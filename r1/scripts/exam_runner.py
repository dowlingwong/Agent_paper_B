#!/usr/bin/env python3
"""Portal-only proposer exam. ENGINEERING_ONLY preparation; B1/B2 require author notes."""
from __future__ import annotations
import argparse
import copy
import json
import math
import os
import platform
import re
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from r1.exam.campaign import write_json
from r1.exam.stage_a import prefill_metadata
from r1.exam.guards import artifact_label, digest_file, paired_instance_bootstrap
from r1.exam.runtime import DEFAULT_CONFIG, ExamRunner, MechanicalFailure, PreparationStop, gpu_sample, load_config, placeholders
from r1.exam.analyze import is_v2, thinking_off_capable
from r1.scripts import llama_server_instance as lsi


def run_fresh_qualification(runner, path, spec, ctx):
    """One fresh attempt only; any worker/infra exception remains STOP."""
    path=Path(path)
    try:
        path.mkdir(parents=True,exist_ok=False)
    except FileExistsError as exc:
        raise PreparationStop('STOP: qualification attempt already exists; preserve it') from exc
    runner.run_job({'out':str(path),'config':runner.cfg,'candidate':spec,'ctx':ctx},'r1.exam.qualify')
    result_path=path/'qualification.json'
    if not result_path.is_file(): raise PreparationStop('STOP: qualification output missing')
    result=json.loads(result_path.read_text())
    if result.get('model_sha256')!=spec['quant_source']['sha256'] or result.get('context')!=ctx:
        raise PreparationStop('STOP: qualification model/context binding mismatch')
    if result.get('status') not in ('PASS','MECHANICAL_FAILURE','TEMPLATE_FAILURE'):
        raise PreparationStop('STOP: qualification failed or has unknown status')
    if result['status']=='TEMPLATE_FAILURE':
        evidence=result.get('template_failure_evidence') or {}
        if evidence.get('kind')!='chat_template_parse_error':
            raise PreparationStop('STOP: qualification template failure lacks retained evidence')
        log=Path(evidence.get('server_log') or '')
        if (not log.is_file() or not log.resolve().is_relative_to(path.resolve()) or
            digest_file(log)!=evidence.get('server_log_sha256')):
            raise PreparationStop('STOP: qualification template server log path or digest mismatch')
    if result['status']=='MECHANICAL_FAILURE':
        allocation=result.get('allocation_failure_evidence') or {}
        if allocation.get('kind')!='cuda_allocation_out_of_memory' or allocation.get('healthy_idle_after_stop') is not True:
            raise PreparationStop('STOP: qualification mechanical failure lacks completed OOM/idle evidence')
        log=Path(allocation.get('server_log') or '')
        if (not log.is_file() or not log.resolve().is_relative_to(path.resolve()) or
            digest_file(log)!=allocation.get('server_log_sha256')):
            raise PreparationStop('STOP: qualification OOM server log path or digest mismatch')
    if not runner.cfg.get('dryrun'):
        raw=Path(result.get('raw_probe') or '')
        if (not raw.is_file() or not raw.resolve().is_relative_to(path.resolve()) or
            digest_file(raw)!=result.get('raw_probe_sha256')):
            raise PreparationStop('STOP: qualification raw probe path or digest mismatch')
    return result


def stage_a(runner, selected, only=None, amendment=None, amendment_reason=None):
    # D3 conditions (explicit false, descriptive cold-true-first, per-call
    # evidence) are enforced inside _stage_a_cooperative and the worker path.
    if runner.cfg.get('cache_prompt') is not False:
        raise PreparationStop('STOP: Stage A cache_prompt must be explicitly false')
    if runner.cfg.get('d3_policy')!='author_same_uid_cooperative_20261031':
        raise PreparationStop('STOP: cooperative D3 policy not explicit')
    return _stage_a_cooperative(runner,selected,only=only,amendment=amendment,
                                amendment_reason=amendment_reason)


GPU_IDLE_ATTEMPTS=12
GPU_IDLE_INTERVAL_SECONDS=5.0


def await_idle_gpu(cfg, *, attempts=GPU_IDLE_ATTEMPTS, interval=GPU_IDLE_INTERVAL_SECONDS,
                   sleep=time.sleep):
    """Wait a bounded time for the GPU to go quiescent before an independent qualification.

    A server that just OOM-ed/exited can linger in nvidia-smi for a few seconds (CUDA
    teardown); treating that instant as "GPU not available" aborts a multi-hour run at a
    retry boundary.  The acceptance criterion is unchanged and fail-closed: the final
    observation must have no compute apps, >=1024 MiB free and <=5% utilisation; foreign
    workloads never become acceptable by waiting.  The last observation is included in the
    STOP message for diagnosis.
    """
    from r1.scripts import llama_server_instance as lsi
    from r1.exam.runtime import gpu_sample
    last=None
    for attempt in range(attempts):
        sample=gpu_sample(cfg);apps=lsi.gpu_compute_apps()
        last={'attempt':attempt+1,'apps':apps,'gpu':sample}
        if apps is None:
            # Unknown census is not a transient state: never wait out an unobservable GPU.
            raise PreparationStop(f'STOP: GPU census unavailable for independent qualification: {last}')
        if apps==[] and sample['free_mib']>=1024 and sample['utilisation_percent']<=5:
            return apps,sample
        if attempt+1<attempts: sleep(interval)
    raise PreparationStop(f'STOP: GPU not available for independent qualification after '
                          f'{attempts} observations: {last}')


def _stage_a_cooperative(runner, selected, only=None, amendment=None, amendment_reason=None):
    """Reviewed implementation only; guarded public entry is still STOP.

    ``only`` is the declared A1 amendment-measurement subset: it must be an explicit
    registry-known id list accompanied by an amendment declaration, it is recorded in
    ``batch_state.amendment_measurement`` and it never changes any check; normal Stage A
    runs pass None and carry no amendment record.
    """
    from r1.exam.stage_a import require_d3_evidence
    try: require_d3_evidence()
    except RuntimeError as exc: raise PreparationStop(str(exc)) from exc
    # Defense in depth if the outer D3 gate is ever replaced after review.
    from r1.exam.cache_runtime import reject_unverified_lease
    reject_unverified_lease()
    out=[]
    every_spec=runner.spec_order(selected)
    only_set=None
    if only:
        if amendment!='A1' or not amendment_reason:
            raise PreparationStop('STOP: --only requires an A1 amendment declaration')
        only_set=set(only)
        known={spec['id'] for spec in every_spec}
        unknown=sorted(only_set-known)
        if unknown: raise PreparationStop(f'STOP: --only names unknown ids {unknown}')
        if not only_set: raise PreparationStop('STOP: --only must name at least one id')
        repairs={spec['id']: (spec.get('template_repair') or {}).get('sha256')
                 for spec in every_spec if spec['id'] in only_set and spec.get('template_repair')}
        runner.state['amendment_measurement']={
            'schema':'r1.exam.amendment_measurement/v1','amendment':'A1',
            'attempt':str(getattr(runner,'out','')),'host':platform.node(),
            'reason':amendment_reason,'models':sorted(only_set),
            'build':(runner.cfg.get('server') or {}).get('build'),
            'prompts_sha256':runner.cfg.get('prompts_sha256'),
            'code_commit':runner.cfg.get('paper_commit'),
            'manifest_sha256':os.environ.get('TRACKX_MANIFEST_SHA256'),
            'repairs':dict(sorted(repairs.items())),
            'scope':'separate amendment measurement; never spliced into the Stage A table'}
        runner.save()
    for candidate in every_spec:
        if candidate.get('kind') not in ('random_valid','scripted'): runner.validate_spec(candidate,allow_pending_footprint=True)
    for spec in every_spec:
        if only_set is not None and spec['id'] not in only_set: continue
        key=spec['id']+'/stage-a'
        if key in runner.state['completed']:
            out.append(json.loads(Path(runner.state['completed'][key]['path']).read_text()));continue
        if spec.get('kind') in ('random_valid','scripted'):
            result={'candidate':spec['id'],'label':'EXAM','phase':'stage-a','passed':True,'software_anchor':True,
                    'prompts':0,'failure_classes':[],'mechanical_model_checks':'not_applicable'}
            path=runner.out/spec['id']/'stage-a'/'stage_a.json';write_json(path,result)
        else:
            runner.validate_spec(spec,allow_pending_footprint=True)
            candidate_source=copy.deepcopy(spec)
            result=None
            for ctx in (32768,16384):
                spec=copy.deepcopy(candidate_source);mode=spec['thinking_policy']['mode']
                path=runner.out/spec['id']/'stage-a'/str(ctx)/'stage_a.json'
                completed_normally=False
                try:
                    if not runner.cfg.get('dryrun') or placeholders(spec['runtime'].get('footprint_mib')) or spec['runtime'].get('footprint_mib') is None:
                        if not runner.cfg.get('dryrun'):
                            await_idle_gpu(runner.cfg)
                        qual_dir=path.parent/'qualification'
                        qualification=run_fresh_qualification(runner,qual_dir,spec,ctx)
                        if qualification['status']=='PREPARATION_STOP': raise PreparationStop('STOP: offload qualification lacks required telemetry')
                        if qualification['status']=='TEMPLATE_FAILURE':
                            # Candidate-level template failure (runbook failure class
                            # "template"): record the row and continue with the next
                            # candidate; a context fallback cannot fix a parser error.
                            result={'candidate':spec['id'],'label':'EXAM','phase':'stage-a','passed':False,
                                    'failure_classes':['template'],'prompts':0,'cpu_pool_only':False,
                                    'error':'pinned llama.cpp build cannot parse the model chat template',
                                    'template_failure_evidence':qualification.get('template_failure_evidence'),
                                    **prefill_metadata(ctx),
                                    'prefill_not_attempted_reason':'chat template parser generation failed at startup'}
                            write_json(path,result);completed_normally=True;break
                        if qualification['status']!='PASS': raise MechanicalFailure('independent exact-path offload qualification failed')
                        spec['runtime']['footprint_mib']=qualification['footprint_mib']
                    else: qualification={'status':'PINNED','footprint_mib':spec['runtime']['footprint_mib']}
                    inst=runner.server(spec,mode,ctx)
                    # This wiring captures observed identity only. It explicitly
                    # rejects dispatch: freshness is not derivable from a PID or
                    # a sampled server census. Outer D3 STOP remains in force.
                    from r1.exam.cache_runtime import capture_parent_identity, reject_unverified_cold
                    identity=capture_parent_identity(inst,binary_sha256=runner.cfg['server']['binary_sha256'],
                                                     model_sha256=spec['quant_source']['sha256'])
                    reject_unverified_cold(identity)
                    runner.run_job({'out':str(path.parent),'config':runner.cfg,'candidate':spec,'port':inst.port,
                                    'ctx':ctx,'cache_identity':identity},'r1.exam.stage_a')
                    result=json.loads(path.read_text())
                    result.update(qualification=qualification,proposal_schema='manager_proposal/v1',model_sha256=spec['quant_source']['sha256'],
                                  build=runner.cfg['server']['build'],thinking_policy=spec['thinking_policy'],
                                  server_record=str(inst.record_path),ctx_size=ctx,cpu_pool_only=(ctx==16384),cache_type='q8_0',n_gpu_layers=999)
                    write_json(path,result)
                    completed_normally=True
                except MechanicalFailure as exc:
                    if runner.service:
                        raise PreparationStop('STOP: preserve Stage A server after failure') from exc
                    result={'candidate':spec['id'],'label':'EXAM','phase':'stage-a','passed':False,'failure_classes':['offload'],
                            'error':repr(exc),'prompts':0,'cpu_pool_only':ctx==16384,
                            **prefill_metadata(ctx),'prefill_not_attempted_reason':'qualification/load failure'}
                    write_json(path,result)
                finally:
                    if runner.service and completed_normally: runner.stop_service()
                if result['passed'] or not set(result['failure_classes']).intersection({'offload','fit_estimate'}): break
        result['source_label']=artifact_label(spec);write_json(path,result)
        runner.state['completed'][key]={'path':str(path),'sha256':digest_file(path)};runner.save();out.append(result)
    write_json(runner.out/'stage_a_table.json',{'label':'ENGINEERING_ONLY','rows':out})


def anchor_gate(manifests, cfg):
    anchors={m['candidate']:m for m in manifests}
    if not {'random_valid','scripted','qwen25_coder_7b'}<=set(anchors): raise RuntimeError('STOP: all anchors must complete first')
    def values(m): return [{'instance_id':r['instance_id'],'value':r['delta_audit']} for r in m['audited_proposals']]
    comparison=paired_instance_bootstrap(values(anchors['scripted']),values(anchors['random_valid']))
    if comparison['difference_lower']<=0 and not cfg.get('dryrun'):
        raise RuntimeError('STOP: random-valid < scripted cannot be shown; no discriminating power')
    reference=cfg['anchor_duplicate_reference'];m=anchors['qwen25_coder_7b'];d=m['diagnostics']
    rate=d['duplicates']/d['evaluated'] if d['evaluated'] else None
    if not cfg.get('dryrun') and (rate is None or not reference['lower']<=rate<=reference['upper']):
        raise RuntimeError('STOP: 7B duplicate rate is outside the pinned pilot interval')
    return {'scripted_minus_random':comparison,'anchor_duplicate_rate':rate,'reference':reference,
            'DRYRUN_gate_override':bool(cfg.get('dryrun'))}


def verify_anchor_reference(cfg):
    """Check the author-specified reference identity and interval before B1 starts."""
    ref=cfg.get('anchor_duplicate_reference')
    if not isinstance(ref,dict): raise PreparationStop('STOP: anchor reference is missing')
    try:
        sha=ref['sha256'];source=Path(ref['source']);lower=ref['lower'];upper=ref['upper']
        valid_bounds=(type(lower) in (int,float) and type(upper) in (int,float) and
                      math.isfinite(lower) and math.isfinite(upper) and 0<=lower<=upper<=1)
        if not valid_bounds or not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):
            raise ValueError('invalid digest or interval')
        if not source.is_file() or digest_file(source)!=sha:
            raise ValueError('reference source digest mismatch')
        documented=json.loads(source.read_text())
        if not isinstance(documented,dict) or documented.get('lower')!=lower or documented.get('upper')!=upper:
            raise ValueError('reference interval differs from the source')
    except (KeyError,TypeError,ValueError,OSError) as exc:
        raise PreparationStop('STOP: invalid anchor duplicate reference') from exc


# R1-EXAM-B1-HARNESS-PIN (author, 4 Nov): Track X B1/B2 run on harness cacheprompt-20261031 @ a3fedbb,
# which sends explicit cache_prompt (default false) on every llama-server request (R1-EXAM-CACHE-REV).
B1_HARNESS_PIN='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
STAGE_A_AMENDMENT_KEYS=('stage_a_amendment_table','stage_a_amendment_table_sha256',
                        'stage_a_amendment_acceptance','stage_a_amendment_acceptance_sha256')


def stage_a_pass_set(cfg, registry_candidates, *, v2):
    """The Stage A pass set B1/B2 read: candidate id -> accepted Stage A row.

    v1: the rows of the sha-bound ``stage_a_table`` with ``passed`` (unchanged).
    v2 (R1-TRACKX-HANDOVER-RULING, packet (d); DRAFT until the author commits R1-EXAM-RULE-X5V2): the
    ``t7h8`` PASS rows of ``stage_a_table`` UNION the PASS rows of the declared A1 amendment measurement
    (``t7j10``) table, which is an explicit sha-bound input and is refused unless both the table and the
    operator's acceptance record are supplied with their sha256.  Only registry ``candidate`` rows enter
    from the amendment table; anchors keep their ``stage_a_table`` rows and run as anchors.  The D28 and
    thinking-off conditions are applied later (B1 manifests / ``analyze``), never here.
    """
    if digest_file(cfg['stage_a_table'])!=cfg['stage_a_table_sha256']: raise PreparationStop('STOP: Stage A table digest mismatch')
    stages=json.loads(Path(cfg['stage_a_table']).read_text())['rows']
    if not v2: return {r['candidate']:r for r in stages if r['passed']}
    eligible={r['candidate']:{**r,'stage_a_pass_source':'stage_a_table'} for r in stages if r['passed']}
    missing=[k for k in STAGE_A_AMENDMENT_KEYS if not cfg.get(k) or placeholders(cfg[k])]
    if missing: raise PreparationStop(f'STOP: x5_rule/v2 needs the operator-accepted A1 amendment table bound by sha256: {missing}')
    table,acceptance=_repo_path(cfg['stage_a_amendment_table']),_repo_path(cfg['stage_a_amendment_acceptance'])
    if not table.is_file() or digest_file(table)!=cfg['stage_a_amendment_table_sha256']:
        raise PreparationStop('STOP: A1 amendment table digest mismatch')
    if not acceptance.is_file() or digest_file(acceptance)!=cfg['stage_a_amendment_acceptance_sha256']:
        raise PreparationStop('STOP: operator acceptance of the A1 amendment table missing or digest mismatch')
    # The acceptance record must name the very tables it accepts (OPS_O1 names both full shas).
    text=acceptance.read_text(errors='replace')
    if cfg['stage_a_amendment_table_sha256'] not in text or cfg['stage_a_table_sha256'] not in text:
        raise PreparationStop('STOP: acceptance record does not name the amendment and Stage A table sha256')
    try: data=json.loads(table.read_text())
    except ValueError as exc: raise PreparationStop('STOP: A1 amendment table is not JSON') from exc
    if not isinstance(data,dict) or data.get('label')!='ENGINEERING_ONLY' or not isinstance(data.get('rows'),list):
        raise PreparationStop('STOP: A1 amendment table malformed')
    for r in data['rows']:
        if not isinstance(r,dict) or not isinstance(r.get('candidate'),str) or not isinstance(r.get('passed'),bool):
            raise PreparationStop(f'STOP: A1 amendment table row malformed: {str(r)[:120]}')
        if r['passed'] and r['candidate'] in registry_candidates and r['candidate'] not in eligible:
            eligible[r['candidate']]={**r,'stage_a_pass_source':'a1_amendment_measurement'}
    return eligible


def _repo_path(value):
    """Absolute paths as given; relative ones (e.g. a committed acceptance report) from the repo root."""
    path=Path(value)
    return path if path.is_absolute() else Path(__file__).resolve().parents[2]/path


_FALSE_ENV=('','0','false','no','off')


def refuse_cache_prompt_override(environ=None):
    """Pre-flight (review F6): the a3fedbb harness reads LLAMACPP_CACHE_PROMPT; B1/B2 refuse any true value."""
    value=(environ if environ is not None else os.environ).get('LLAMACPP_CACHE_PROMPT','')
    if value.strip().lower() not in _FALSE_ENV:
        raise PreparationStop(f'STOP: LLAMACPP_CACHE_PROMPT={value!r} would override cache_prompt false (R1-EXAM-CACHE-REV)')


def template_repair_record(spec):
    """The SHA-pinned repair template a model is served with (R1-EXAM-A1-M1-REQUIREMENTS (1)), or None."""
    repair=spec.get('template_repair')
    return {'file':repair.get('file'),'sha256':repair.get('sha256')} if repair else None


def check_template_repairs(cfg, specs):
    """v2 configs bind each repaired model's template sha; the registry must agree byte for byte."""
    declared=cfg.get('template_repairs')
    if not isinstance(declared,dict): raise PreparationStop('STOP: x5_rule/v2 config must bind template_repairs')
    actual={s['id']:s['template_repair']['sha256'] for s in specs if s.get('template_repair')}
    if declared!=actual: raise PreparationStop(f'STOP: config template_repairs {declared} differ from registry {actual}')
    return actual


def evidence(runner, phase, selected, interrupt):
    if phase != 'b1' or not is_v2(getattr(runner,'rule',None)):
        raise PreparationStop('STOP: only x5_rule/v2 B1 evidence is implemented')
    if selected and not runner.cfg.get('dryrun'):
        raise PreparationStop('STOP: production B1 requires the full eligible candidate set')
    return _evidence_unreviewed(runner, phase, selected, interrupt)


def _evidence_unreviewed(runner, phase, selected, interrupt):
    """Evidence collection body; the public entry admits reviewed B1 only."""
    cfg=runner.cfg;rows=[]
    v2=is_v2(getattr(runner,'rule',None))
    if digest_file(cfg['stage_a_table'])!=cfg['stage_a_table_sha256']: raise PreparationStop('STOP: Stage A table digest mismatch')
    if phase=='b2' and digest_file(cfg['b1_analysis'])!=cfg['b1_analysis_sha256']: raise PreparationStop('STOP: B1 analysis digest mismatch')
    if v2:
        if cfg.get('cache_prompt') is not False: raise PreparationStop('STOP: B1/B2 cache_prompt must be explicitly false (R1-EXAM-CACHE-REV)')
        if not cfg.get('dryrun') and cfg.get('harness_commit')!=B1_HARNESS_PIN: raise PreparationStop('STOP: B1/B2 harness pin must be a3fedbb (R1-EXAM-B1-HARNESS-PIN)')
        refuse_cache_prompt_override()
        check_template_repairs(cfg,runner.spec_order())
    registry_candidates={s['id'] for s in runner.spec_order() if s.get('role')=='candidate'}
    eligible=stage_a_pass_set(cfg,registry_candidates,v2=v2)
    specs=runner.spec_order(selected)
    if v2 and phase=='b1':
        unavailable=[s['id'] for s in specs if s['id'] in eligible and
                     (s.get('thinking_policy') or {}).get('switchable') is True and
                     eligible[s['id']].get('thinking_disabled_due_grammar')]
        if unavailable:
            raise PreparationStop('STOP: required thinking-on sensitivity disabled by Stage A grammar: '+', '.join(unavailable))
    if phase=='b2':
        screen=json.loads(Path(cfg['b1_analysis']).read_text())
        if screen['rule_sha256']!=runner.rule_sha: raise RuntimeError('STOP: B1 rule identity mismatch')
        final={cfg['d22_pick'],'qwen25_coder_7b'} if cfg.get('free_sensitivity') else set(screen['finalists'])
        specs=[s for s in runner.spec_order() if s['id'] in final]
        if cfg.get('free_sensitivity'):
            plan=(Path(__file__).resolve().parents[2]/'docs/r1/PLAN.md').read_text()
            if not any('D22' in line and cfg['d22_pick'] in line for line in plan.splitlines()): raise RuntimeError('STOP: D22 pick must be author-recorded before its free sensitivity')
        if not specs: raise RuntimeError('STOP: B2 needs frozen B1 finalists')
    for spec in specs:
        if spec['id'] not in eligible: continue
        if (v2 and phase=='b1' and spec.get('role') in ('candidate','sensitivity') and runner.rule['thinking_mode']['always_on_in_b1']=='skip'
                and not thinking_off_capable(spec.get('thinking_policy'))):
            # R1-EXAM-ALWAYS-ON-SKIP: always-thinking models do not run B1; the appendix reports them from Stage A.
            runner.state.setdefault('b1_skipped_always_on',[])
            if spec['id'] not in runner.state['b1_skipped_always_on']: runner.state['b1_skipped_always_on'].append(spec['id'])
            runner.save();continue
        if phase=='b1' and spec['role']=='candidate' and not runner.state.get('anchor_gate'):
            runner.state['anchor_gate']=anchor_gate(rows,cfg);runner.save()
        spec=copy.deepcopy(spec)
        if spec.get('runtime') and placeholders(spec['runtime'].get('footprint_mib')):
            accepted=eligible[spec['id']]
            if accepted.get('model_sha256')!=spec['quant_source']['sha256'] or accepted.get('build')!=cfg['server']['build']:
                raise RuntimeError('STOP: accepted Stage A model/build does not match B1 pins')
            spec['runtime']['footprint_mib']=accepted['qualification']['footprint_mib']
        mode=spec.get('thinking_policy',{}).get('mode','off')
        modes=[mode]
        if phase=='b1' and spec.get('thinking_policy',{}).get('switchable') is True and not eligible[spec['id']].get('thinking_disabled_due_grammar'):
            modes.append('on')
        if phase=='b2' and not v2:
            row=next(r for r in screen['rows'] if r['candidate']==spec['id']);mode=row['b2_thinking_mode'];modes=[mode]
            if mode=='on' and eligible[spec['id']].get('thinking_disabled_due_grammar'): raise PreparationStop('STOP: B1 chose thinking-on disabled by Stage A')
            rank=screen['finalists'].index(spec['id']) if spec['id'] in screen['finalists'] else 99
            if not cfg.get('free_sensitivity') and rank<3 and spec.get('thinking_policy',{}).get('switchable') is True and not eligible[spec['id']].get('thinking_disabled_due_grammar'): modes.append('on' if mode=='off' else 'off')
        if phase=='b2' and v2:
            # x5_rule/v2: B2 runs thinking off for every finalist; the top-3 rerun is thinking-on and descriptive only.
            row=next((r for r in screen['rows'] if r['candidate']==spec['id']),None)
            if row is None and not cfg.get('free_sensitivity'): raise PreparationStop('STOP: x5_rule/v2 B2 finalist has no B1 analysis row')
            if row is not None and row.get('b2_thinking_mode')!='off': raise PreparationStop('STOP: x5_rule/v2 B1 analysis must assign B2 mode off')
            if spec.get('kind') not in ('random_valid','scripted') and not thinking_off_capable(spec.get('thinking_policy')):
                raise PreparationStop('STOP: x5_rule/v2 B2 finalist cannot run thinking off')
            mode='off';modes=['off']
            rank=screen['finalists'].index(spec['id']) if spec['id'] in screen['finalists'] else 99
            if not cfg.get('free_sensitivity') and rank<3 and spec.get('thinking_policy',{}).get('switchable') is True and not eligible[spec['id']].get('thinking_disabled_due_grammar'): modes.append('on')
        root_results=[];began=time.monotonic()
        try:
            for mode_index,current_mode in enumerate(modes):
                sensitivity_node=runner.rule['thinking_mode']['b1_sensitivity']['node'] if v2 else 'openml_credit_approval'
                nodes=([cfg['schema_sensitivity_node']] if cfg.get('free_sensitivity') else (cfg['nodes'] if mode_index==0 or phase=='b2' else [sensitivity_node]))
                seeds=cfg['instance_seeds'] if phase=='b1' else list(range(9011,9011+cfg['b2_instances_per_node']))
                needs_run=any(f'{spec["id"]}/{phase}/{current_mode}/{n}__s{s}' not in runner.state['completed'] for n in nodes for s in seeds)
                if needs_run and spec.get('kind') not in ('random_valid','scripted'): runner.server(spec,current_mode,16384 if eligible[spec['id']].get('cpu_pool_only') else 32768)
                for node in nodes:
                    for seed in seeds:
                        root_results.append(runner.root(spec,phase,node,seed,current_mode,interrupt=interrupt and len(runner.state['completed'])>=1 and not runner.state.get('interruptions')))
                if runner.service: runner.stop_service()
        finally:
            if runner.service: runner.stop_service()
        audits=[r for root in root_results for r in root['audited_proposals']]
        diag={k:sum(r['diagnostics'].get(k,0) for r in root_results) for k in ('trials','evaluated','invalid','duplicates','noops','parse_failed','forecast_queries','forecast_query_failed')}
        def d28_of(roots): return all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in roots)
        # v2 (review F2): the D28 eligibility gate reads the thinking-off (primary-mode) roots only; the
        # descriptive thinking-on roots get their own D28 record and never change eligibility.
        d28=d28_of([r for r in root_results if r['mode']==modes[0]]) if v2 else d28_of(root_results)
        d28_descriptive=[r for r in root_results if r['mode']!=modes[0]] if v2 else []
        manifest={'label':'EXAM','phase':phase,'status':'COMPLETE','candidate':spec['id'],'family':spec['family'],'role':spec['role'],
                  'source_label':artifact_label(spec),'rule_sha256':runner.rule_sha,'registry_sha256':digest_file(runner.registry_path),'registry_path':str(runner.out/'registry_snapshot.yaml'),'registry_order':[s['id'] for s in runner.spec_order()].index(spec['id']),
                  'model_sha256':(spec.get('quant_source') or {}).get('sha256'),'llamacpp_build':cfg['server']['build'] if not spec.get('kind') else None,
                  'purpose':'schema_free_sensitivity' if cfg.get('free_sensitivity') else 'primary','schema_mode':'free' if cfg.get('free_sensitivity') else 'manager_proposal/v1',
                  'thinking_sensitivity_omitted_reason':'Stage A grammar disabled thinking-on' if eligible[spec['id']].get('thinking_disabled_due_grammar') else None,
                  'stage_a_table_sha256':cfg['stage_a_table_sha256'],'b1_analysis_sha256':cfg.get('b1_analysis_sha256') if phase=='b2' else None,
                  'primary_mode':modes[0],'mode':modes[0],'stage_a_pass':True,'d28_pass':d28,'audited_proposals':audits,
                  'diagnostics':diag,'thinking_policy':spec.get('thinking_policy'),'proposal_schema':None if spec.get('kind') or cfg.get('free_sensitivity') else 'manager_proposal/v1',
                  'final_audits':[r for root in root_results if root['mode']==modes[0] for r in root['final_audits']],
                  'sensitivity_final_audits':[r for root in root_results if root['mode']!=modes[0] for r in root['final_audits']],
                  'gpu_hours':sum((x['end']-x['start'])/3600 for x in runner.state.get('server_intervals',[]) if x['candidate']==spec['id'] and x['phase']==phase and x['mode']==modes[0] and x['end'] is not None),
                  'total_gpu_hours':sum((x['end']-x['start'])/3600 for x in runner.state.get('server_intervals',[]) if x['candidate']==spec['id'] and x['phase']==phase and x['end'] is not None),
                  'gpu_hours_method':'dedicated_server_wall_intervals_including_load_and_audit',
                  'execution_label':'DRYRUN' if cfg.get('dryrun') else 'EVIDENCE','root_manifests':[str(runner.out/f'{spec["id"]}/{phase}/{r["mode"]}/{r["node"]}__s{r["instance_seed"]}/campaign_manifest.json') for r in root_results]}
        if v2:
            if phase=='b1' and not cfg.get('dryrun') and not re.fullmatch(r'[0-9a-f]{40}',str(getattr(runner,'author_head',''))):
                raise PreparationStop('STOP: B1 manifest requires the authorized checkout HEAD')
            manifest.update(rule_version='x5_rule/v2',cache_prompt=cfg['cache_prompt'],harness_commit=cfg.get('harness_commit'),
                            authorization_checkout_head=getattr(runner,'author_head',None),
                            template_repair=template_repair_record(spec),
                            stage_a_pass_source=eligible[spec['id']].get('stage_a_pass_source'),
                            stage_a_amendment_table_sha256=cfg['stage_a_amendment_table_sha256'],
                            stage_a_amendment_acceptance_sha256=cfg['stage_a_amendment_acceptance_sha256'],
                            cache_prompt_by_root=[root.get('cache_prompt') for root in root_results],
                            d28_scope='thinking_off_roots_only',
                            thinking_on_d28={'pass':d28_of(d28_descriptive),'roots':len(d28_descriptive),'role':'descriptive_never_changes_eligibility'} if d28_descriptive else None)
            if spec.get('kind') not in ('random_valid','scripted') and not all((root.get('cache_prompt') or {}).get('all_false') is True for root in root_results):
                raise PreparationStop('STOP: a B1/B2 root lacks llm_call evidence of cache_prompt false')
            if len(modes)>1:
                manifest['thinking_on_rerun' if phase=='b2' else 'thinking_on_sensitivity']='descriptive'
        uncertain=any(x.get('cost_is_upper_bound') for x in runner.state.get('server_intervals',[]) if x['candidate']==spec['id'] and x['phase']==phase)
        manifest['gpu_hours_upper_bound']=manifest['gpu_hours']
        manifest['gpu_hours_status']='upper_bound_after_interruption' if uncertain else 'recorded_dedicated_intervals'
        if uncertain: manifest['gpu_hours']=None
        path=runner.out/spec['id']/f'{phase}_manifest.json';write_json(path,manifest);rows.append(manifest)
    write_json(runner.out/f'{phase}_manifests.json',{'label':'EXAM','manifests':rows})


def _alive(pid):
    try: os.kill(int(pid),0)
    except ProcessLookupError: return False
    except PermissionError as exc:
        raise PreparationStop('STOP: server liveness unobservable') from exc
    return True


def _write_lease_completion(runner):
    """Fail-closed natural-completion evidence; the guardian alone releases the lock."""
    evidence=os.environ.get('TRACKX_LEASE_EVIDENCE_DIR')
    if not evidence or not Path(evidence).is_dir():
        raise PreparationStop('STOP: lease evidence directory absent')
    from r1.exam.cache_proc import process_start_ticks
    from r1.exam.cooperative_lease import write_completion
    records=[]
    for path in sorted(runner.out.rglob('llama_server_*.json')):
        row=json.loads(path.read_text())
        pid=row.get('pid');ticks=row.get('start_ticks');stopped=row.get('stopped_utc')
        if type(pid) is not int or type(ticks) is not int or not isinstance(stopped,str) or not stopped:
            raise PreparationStop('STOP: server record incomplete for lease completion')
        if _alive(pid) and process_start_ticks(pid)==ticks:
            raise PreparationStop('STOP: server still alive; natural completion unproven')
        records.append({'pid':pid,'start_ticks':ticks,'stopped_utc':stopped,
                        'record_sha256':digest_file(path),'record_path':str(path.resolve())})
    if not records:
        raise PreparationStop('STOP: no server records; natural completion unproven')
    return write_completion(evidence,batch_state_path=str(runner.out/'batch_state.json'),
                            servers=records,runner_pid=os.getpid(),
                            runner_start_ticks=process_start_ticks(os.getpid()))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['stage-a','b1','b2'],nargs='?')
    p.add_argument('--config',default=str(DEFAULT_CONFIG));p.add_argument('--out');p.add_argument('--candidate',action='append')
    p.add_argument('--free-sensitivity',action='store_true',help='B2 only: one-node free-generation sensitivity for 7B and the author-recorded D22 pick')
    p.add_argument('--check-config',action='store_true');p.add_argument('--allow-placeholders',action='store_true')
    p.add_argument('--interrupt-root',action='store_true',help='DRYRUN only: kill first root worker after one ledger append')
    p.add_argument('--only',help='A1 amendment measurement only: comma-separated registry ids (requires --amendment A1)')
    p.add_argument('--amendment',choices=['A1'],help='declared template-check amendment for a measurement run')
    p.add_argument('--amendment-reason',help='declared reason for the amendment measurement')
    a=p.parse_args(argv)
    if not a.check_config and a.phase=='b2':
        raise PreparationStop('STOP: B2 reviewed observer integration is not implemented')
    if not a.check_config and a.phase=='stage-a' and not os.environ.get('TRACKX_GPU_LEASE_FD'):
        raise PreparationStop('STOP: D3 cold-cache cooperative lease FD absent')
    if a.allow_placeholders and not a.check_config: p.error('--allow-placeholders is only for --check-config')
    cfg=load_config(a.config,allow_placeholders=a.allow_placeholders)
    if not a.check_config and a.phase=='stage-a':
        from r1.exam.cache_runtime import authorize_cooperative_stagea
        authorize_cooperative_stagea(cfg)
    if a.free_sensitivity:
        if a.phase!='b2': p.error('--free-sensitivity requires b2')
        cfg['free_sensitivity']=True
        if not cfg.get('d22_pick') or placeholders(cfg['d22_pick']): raise RuntimeError('STOP: author D22 pick required')
    if a.check_config: print(json.dumps({'valid':True,'unresolved':placeholders(cfg)}));return 0
    if not a.phase or not a.out: p.error('phase and --out required')
    if a.interrupt_root and not cfg.get('dryrun'): p.error('--interrupt-root is DRYRUN only')
    if a.phase=='b1' and a.candidate and not cfg.get('dryrun'):
        raise PreparationStop('STOP: production B1 requires the full eligible candidate set')
    if a.phase in ('b1','b2') and (not cfg.get('authorizations',{}).get(a.phase) or
                                  placeholders(cfg['authorizations'][a.phase])):
        raise PreparationStop('STOP: active phase authorization note is unresolved')
    required=['prompts','prompts_sha256'] if a.phase=='stage-a' else ['stage_a_table','stage_a_table_sha256','nodes','llm_call_cap','anchor_duplicate_reference']
    if a.phase=='b2': required += ['b1_analysis','b1_analysis_sha256','b2_instances_per_node']
    if a.phase in ('b1','b2'):
        from r1.exam.analyze import load_rule
        if is_v2(load_rule(cfg['rule'],cfg['rule_sha256'])[0]): required += list(STAGE_A_AMENDMENT_KEYS)
    unresolved=placeholders({k:cfg[k] for k in required})
    if unresolved: raise RuntimeError(f'STOP: unresolved phase settings: {unresolved}')
    if a.phase=='b1' and not cfg.get('dryrun'): verify_anchor_reference(cfg)
    runner=ExamRunner(cfg,a.out)
    preserve_running=False
    try:
        runner.start(a.phase)
        if a.phase=='stage-a':
            only=[x.strip() for x in a.only.split(',')] if a.only else None
            if only is not None and (a.amendment!='A1' or not a.amendment_reason):
                raise PreparationStop('STOP: --only requires --amendment A1 and --amendment-reason')
            if only is None and (a.amendment or a.amendment_reason):
                raise PreparationStop('STOP: amendment flags require --only')
            stage_a(runner,a.candidate,only=only,amendment=a.amendment,
                    amendment_reason=a.amendment_reason)
        else: evidence(runner,a.phase,a.candidate,a.interrupt_root)
        runner.state['status']='COMPLETE';runner.save()
    except BaseException as exc:
        preserve_running=a.phase=='stage-a'
        runner.state.update(status='STOPPED',stop_reason=f'{type(exc).__name__}: {exc}')
        if preserve_running:
            runner.state['gpu_lease_after_stop']='NOT_CHECKABLE: runner marker is not evidence of held flock'
        if runner.lock is not None: runner.save()
        print(runner.state['stop_reason'],file=sys.stderr);return 1
    finally: runner.close(preserve_running=preserve_running)
    # Only after close() so no later write can invalidate the batch_state digest
    # the guardian validates before releasing the lock.
    if a.phase=='stage-a' and not cfg.get('dryrun'): _write_lease_completion(runner)
    return 0

if __name__=='__main__': raise SystemExit(main())
