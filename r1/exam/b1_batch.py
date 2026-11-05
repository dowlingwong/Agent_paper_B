"""Verify a complete authorized B1 batch before producing v2 finalists."""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

from r1.exam.analyze import thinking_off_capable
from r1.exam.guards import digest_file


def _stop(message):
    raise ValueError('STOP: B1 batch '+message)


def _read(path):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError) as exc: raise ValueError('STOP: B1 batch file unavailable or malformed') from exc


def _inside(root, path):
    if not Path(path).resolve().is_relative_to(Path(root).resolve()):
        _stop('constituent path escapes its batch root')


def verify_batch(batch, cfg, rule_sha):
    """Return verified candidate manifests; no inference, server, or mutation.

    The clean committed author note and PLAN are the process authority; this
    does not claim cryptographic authorship or resist a malicious same-UID writer.
    """
    from r1.exam.runtime import author_gate, read_registry, verify_campaign, _verify_b1_root_authority, b1_harness_sources
    from r1.scripts.exam_runner import stage_a_pass_set, anchor_gate, verify_anchor_reference
    from r1.exam.campaign import cache_prompt_evidence, read_rows
    from r1.exam.b1_observer_journal import validate_observer_journal
    from r1.liveness.check import evaluate_ledger_paths
    from r1.harness import harness_root
    from autoresearch.nodes.registry import load_registered_node
    from r1.c3.features import replay_campaign, files_hash
    from r1.c3.audit import paired
    from r1.exam.observer import _authorized_candidate
    if cfg.get('dryrun'): _stop('production verification refuses DRYRUN')
    head=author_gate(cfg,'b1',rule_sha)
    if not isinstance(head,str) or len(head)!=40: _stop('authorized HEAD absent')
    harness=Path(harness_root()).resolve()
    try:
        pinned=subprocess.check_output(['git','-C',str(harness),'rev-parse','HEAD'],text=True).strip()
        changed=subprocess.check_output(['git','-C',str(harness),'status','--porcelain','--untracked-files=no'],text=True).strip()
    except (OSError,subprocess.SubprocessError) as exc: raise ValueError('STOP: B1 harness pin unavailable') from exc
    if pinned!=cfg.get('harness_commit') or changed: _stop('harness differs from the clean pin')
    nodes=set(cfg['nodes'])|{'openml_credit_approval'}
    node_sources={node:b1_harness_sources(node,cfg['harness_commit']) for node in nodes}
    batch=Path(batch).resolve(strict=True)
    _inside(batch,batch/'batch_state.json');_inside(batch,batch/'b1_manifests.json')
    state=_read(batch/'batch_state.json')
    if state.get('status')!='COMPLETE' or state.get('phase')!='b1' or state.get('execution_label')!='EVIDENCE':
        _stop('is not a completed evidence batch')
    registry_path=batch/'registry_snapshot.yaml'
    if registry_path.resolve().parent!=batch or digest_file(registry_path)!=digest_file(cfg['registry']):
        _stop('registry snapshot differs from configured registry')
    registry=read_registry(registry_path)
    expected_binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(registry_path),
        'rule_sha256':rule_sha,'value_grids_sha256':digest_file(cfg['value_grids'])},sort_keys=True).encode()).hexdigest()
    if state.get('binding')!=expected_binding or state.get('rule_sha256')!=rule_sha:
        _stop('configuration binding mismatch')
    candidates={r['id'] for r in registry['candidates'] if r.get('role')=='candidate'}
    eligible=stage_a_pass_set(cfg,candidates,v2=True)
    specs=registry['software_anchors']+[r for r in registry['candidates'] if r['role']=='anchor']+\
          [r for r in registry['candidates'] if r['role']=='candidate']+registry.get('sensitivities',[])
    expected=[]
    for spec in specs:
        if spec['id'] not in eligible: continue
        if spec.get('role') in ('candidate','sensitivity') and not thinking_off_capable(spec.get('thinking_policy')): continue
        expected.append(spec)
    ids=[s['id'] for s in expected]
    if not ids or len(set(ids))!=len(ids): _stop('empty or duplicate eligible set')
    if not {'random_valid','scripted','qwen25_coder_7b'}<=set(ids): _stop('required anchors are missing')
    data=_read(batch/'b1_manifests.json')
    manifests=data.get('manifests') if isinstance(data,dict) and data.get('label')=='EXAM' else None
    if not isinstance(manifests,list) or [m.get('candidate') for m in manifests]!=ids:
        _stop('candidate set or registry order differs from Stage A passes')
    state_roots=state.get('completed')
    if not isinstance(state_roots,dict): _stop('completed root index missing')
    expected_keys=set()
    for spec,m in zip(expected,manifests):
        cid=spec['id']; candidate_path=batch/cid/'b1_manifest.json'
        if not candidate_path.resolve().is_relative_to(batch) or _read(candidate_path)!=m:
            _stop('candidate manifest differs from aggregate')
        if (m.get('execution_label')!='EVIDENCE' or m.get('authorization_checkout_head')!=head or
            m.get('stage_a_table_sha256')!=cfg['stage_a_table_sha256'] or
            m.get('stage_a_amendment_table_sha256')!=cfg['stage_a_amendment_table_sha256'] or
            m.get('stage_a_amendment_acceptance_sha256')!=cfg['stage_a_amendment_acceptance_sha256']):
            _stop('candidate authority or Stage A inputs differ')
        if m.get('stage_a_pass') is not True or m.get('stage_a_pass_source')!=eligible[cid].get('stage_a_pass_source'):
            _stop('candidate Stage A pass provenance differs')
        if (Path(str(m.get('registry_path') or '')).resolve()!=registry_path.resolve() or
                m.get('registry_sha256')!=digest_file(registry_path)):
            _stop('candidate registry does not bind the verified batch snapshot')
        modes=[(spec.get('thinking_policy') or {}).get('mode','off')]
        if (spec.get('thinking_policy') or {}).get('switchable') is True:
            if eligible[cid].get('thinking_disabled_due_grammar'): _stop('required sensitivity disabled')
            modes.append('on')
        grids=[]
        for index,mode in enumerate(modes):
            nodes=cfg['nodes'] if index==0 else ['openml_credit_approval']
            grids.extend((mode,node,seed) for node in nodes for seed in cfg['instance_seeds'])
        expected_paths=[str(batch/cid/'b1'/mode/f'{node}__s{seed}'/'campaign_manifest.json') for mode,node,seed in grids]
        if m.get('root_manifests')!=expected_paths: _stop('candidate root grid differs from authorized design')
        roots=[]
        for (mode,node,seed),path in zip(grids,expected_paths):
            key=f'{cid}/b1/{mode}/{node}__s{seed}';expected_keys.add(key)
            entry=state_roots.get(key)
            if not Path(path).resolve().is_relative_to(batch): _stop('root path escapes batch')
            root_dir=Path(path).parent
            for name in ('job.json','post_check.json','root_trials.jsonl','root_events.jsonl',
                         'audit_cache.json','audit_configs.json','a4_observer_requests.jsonl'):
                _inside(root_dir,root_dir/name)
            if not isinstance(entry,dict) or entry.get('path')!=path or digest_file(path)!=entry.get('sha256'):
                _stop('root missing or changed')
            root=verify_campaign(path,expected_binding);_verify_b1_root_authority(path,head)
            job=_read(Path(path).parent/'job.json')
            for field in ('workers','host','W','llm_call_cap','audit_seeds','proposal_schema'):
                if job.get(field)!=cfg.get(field): _stop('root job parameters differ from authorization')
            if (job.get('authority_config')!=cfg or job.get('phase')!='b1' or job.get('node')!=node or
                job.get('seed')!=seed or job.get('mode')!=mode or job.get('dryrun') is not False or
                job.get('harness_commit')!=cfg['harness_commit'] or job.get('node_source_sha256')!=node_sources[node] or
                job.get('out')!=str(Path(path).parent) or job.get('binding')!=expected_binding or
                job.get('value_grids')!=cfg['value_grids'] or
                not _authorized_candidate(job,cfg,registry)):
                _stop('root job authority, candidate or source binding differs')
            if (root.get('execution_label')!='EVIDENCE' or root.get('phase')!='b1' or root.get('candidate')!=cid or
                root.get('mode')!=mode or root.get('node')!=node or root.get('instance_seed')!=seed):
                _stop('root identity differs from grid')
            names={'root_trials.jsonl','root_events.jsonl','audit_cache.json','audit_configs.json','a4_observer_requests.jsonl'}
            hashes=root.get('evidence_hashes')
            if not isinstance(hashes,dict) or set(hashes)!=names or any(hashes[k] is None for k in ('root_trials.jsonl','root_events.jsonl','audit_configs.json')):
                _stop('root evidence index incomplete')
            records=read_rows(Path(path).parent/'root_trials.jsonl');events=read_rows(Path(path).parent/'root_events.jsonl')
            novelty=[e['payload'] for e in events if e.get('event_type')=='edit_novelty']
            forecasts={e['trial_id']:e['payload'] for e in events if e.get('event_type')=='exam_self_forecast'}
            diagnostics={'trials':len(records),'evaluated':len(novelty),
                'invalid':sum(r['decision']=='failed_invalid' for r in records),
                'duplicates':sum(bool(p.get('active_config_seen_before')) for p in novelty),
                'noops':sum(bool(p.get('active_config_equals_incumbent')) for p in novelty),
                'parse_failed':sum(bool(((r.get('extra') or {}).get('manager') or {}).get('parse_failed')) or
                    ((((r.get('extra') or {}).get('manager') or {}).get('llm_call')) or {}).get('parse_ok') is False for r in records),
                'forecast_queries':len(forecasts),'forecast_query_failed':sum(r.get('status')=='query_failed' for r in forecasts.values())}
            if root.get('diagnostics')!=diagnostics: _stop('root diagnostics differ from ledger and events')
            completed=[e.get('payload') or {} for e in events if e.get('event_type')=='campaign_completed']
            if len(completed)!=1: _stop('root completion event missing or duplicated')
            budget=completed[0].get('compute_budget')
            if not isinstance(budget,dict) or root.get('compute_budget')!=budget:
                _stop('root budget differs from completion event')
            if (budget.get('max_worker_runs')!=cfg['W'] or budget.get('max_llm_calls')!=cfg['llm_call_cap'] or
                type(budget.get('worker_runs')) is not int or not 0<=budget['worker_runs']<=cfg['W'] or
                type(budget.get('llm_calls')) is not int or not 0<=budget['llm_calls']<=cfg['llm_call_cap']):
                _stop('root budget exceeds or differs from authorized caps')
            worker_count=sum(not ((r.get('extra') or {}).get('worker') or {}).get('worker_skipped',False) and r.get('decision')!='skipped' for r in records)
            if budget['worker_runs']!=worker_count: _stop('worker count differs from trial ledger')
            call_events=[e.get('payload') or {} for e in events if e.get('event_type') in ('llm_call','llm_call_failed')]
            if any(type(e.get('llm_calls',1)) is not int or e.get('llm_calls',1)<1 for e in call_events) or \
                    budget['llm_calls']!=sum(e.get('llm_calls',1) for e in call_events):
                _stop('LLM call count differs from events')
            if root.get('termination')!=('worker_cap' if budget['worker_runs']>=cfg['W'] else 'llm_cap_or_reserved_observer_pair'):
                _stop('termination label differs from budget')
            if spec.get('kind') not in ('random_valid','scripted'):
                if root.get('cache_prompt')!=cache_prompt_evidence(records,events): _stop('cache evidence differs from events')
                if root.get('observer_evidence')!=validate_observer_journal(Path(path).parent/'a4_observer_requests.jsonl',events):
                    _stop('observer evidence differs from journal')
            if digest_file(Path(path).parent/'post_check.json')!=entry.get('post_check_sha256'):
                _stop('root receiving certificate changed')
            recorded=root.get('d28') or {}
            recomputed=evaluate_ledger_paths([Path(path).parent/'root_trials.jsonl'],
                generated_utc=recorded.get('generated_utc'),
                manager_kind='scripted' if spec.get('kind') in ('random_valid','scripted') else 'langgraph',
                memory_mode='append_only_summary')
            if recorded!=recomputed or node not in recomputed['nodes']:
                _stop('root D28 differs from verified ledger')
            node_spec=load_registered_node(node,repo_root=harness)
            start={p:(harness/'nodes'/node/p).read_text() for p in node_spec.editable_paths}
            proposals,checks=replay_campaign(records,start,node,f'{node}__s{seed}','EXAM',
                                             'append_only_summary',cfg['W'],1.)
            if root.get('replay_checks')!=checks: _stop('root replay checks differ')
            audited=[p for p in proposals if not p.features.get('active_equals_incumbent') and not p.features.get('active_seen_before')]
            expected_configs={}
            for proposal in audited:
                for files in (proposal.candidate_files,proposal.incumbent_files):
                    expected_configs[files_hash(files)]={'node':node,'files':files}
            if _read(Path(path).parent/'audit_configs.json')!=expected_configs: _stop('audit configs differ from replay')
            cache_path=Path(path).parent/'audit_cache.json'
            cache=_read(cache_path) if cache_path.exists() else {}
            if set(cache)!=set(expected_configs): _stop('audit cache keys differ from replay')
            reconstructed=[]
            for proposal in audited:
                arrays=[cache[files_hash(files)] for files in (proposal.candidate_files,proposal.incumbent_files)]
                result=paired(*arrays)
                if result['k']!=len(cfg['audit_seeds']): _stop('audit cache has incomplete paired seeds')
                trial=f'{node}__s{seed}-trial-{proposal.budget_index:03d}'
                reconstructed.append({'proposal_id':proposal.proposal_id,'instance_id':f'{node}__s{seed}',
                    'node':node,'mode':mode,'audit_seeds':cfg['audit_seeds'],'candidate_hash':proposal.candidate_hash,
                    'incumbent_hash':proposal.incumbent_hash,'candidate_metrics':arrays[0],'incumbent_metrics':arrays[1],
                    **result,**{k:v for k,v in forecasts.get(trial,{}).items() if k in ('p_delta_positive','p_no_effect')}})
            if root.get('audited_proposals')!=reconstructed: _stop('root audits differ from replay and cache')
            roots.append(root)
        if m.get('audited_proposals')!=[p for r in roots for p in r['audited_proposals']]:
            _stop('candidate audits differ from verified roots')
        primary=[r for r in roots if r['mode']==m.get('primary_mode')]
        if not primary or m.get('d28_pass')!=all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in primary):
            _stop('candidate D28 differs from verified primary roots')
        if m.get('cache_prompt_by_root')!=[r.get('cache_prompt') for r in roots]:
            _stop('candidate cache evidence differs from roots')
        diagnostic_keys=('trials','evaluated','invalid','duplicates','noops','parse_failed','forecast_queries','forecast_query_failed')
        if m.get('diagnostics')!={k:sum(r['diagnostics'].get(k,0) for r in roots) for k in diagnostic_keys}:
            _stop('candidate diagnostics differ from verified roots')
        descriptive=[r for r in roots if r['mode']!=m.get('primary_mode')]
        expected_d28={'pass':all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in descriptive),
                      'roots':len(descriptive),'role':'descriptive_never_changes_eligibility'} if descriptive else None
        if m.get('thinking_on_d28')!=expected_d28: _stop('descriptive D28 differs from verified roots')
        if spec.get('kind') not in ('random_valid','scripted') and not all((r.get('cache_prompt') or {}).get('all_false') is True for r in roots):
            _stop('root lacks cache-false evidence')
    if set(state_roots)!=expected_keys: _stop('batch has extra or missing completed roots')
    verify_anchor_reference(cfg)
    if state.get('anchor_gate')!=anchor_gate([m for m in manifests if m['candidate'] in ('random_valid','scripted','qwen25_coder_7b')],cfg):
        _stop('anchor gate does not match verified anchor results')
    return manifests, {'batch_state_sha256':digest_file(batch/'batch_state.json'),
                       'batch_manifests_sha256':digest_file(batch/'b1_manifests.json'),
                       'authorization_checkout_head':head,'eligible_candidates':ids}
