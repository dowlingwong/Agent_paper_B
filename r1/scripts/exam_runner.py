#!/usr/bin/env python3
"""Portal-only proposer exam. ENGINEERING_ONLY preparation; B1/B2 require author notes."""
from __future__ import annotations
import argparse
import copy
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from r1.exam.campaign import write_json
from r1.exam.stage_a import prefill_metadata
from r1.exam.guards import artifact_label, digest_file, paired_instance_bootstrap
from r1.exam.runtime import DEFAULT_CONFIG, ExamRunner, MechanicalFailure, PreparationStop, gpu_sample, load_config, placeholders
from r1.scripts import llama_server_instance as lsi


def stage_a(runner, selected):
    out=[]
    for candidate in runner.spec_order(selected):
        if candidate.get('kind') not in ('random_valid','scripted'): runner.validate_spec(candidate,allow_pending_footprint=True)
    for spec in runner.spec_order(selected):
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
                try:
                    if not runner.cfg.get('dryrun') or placeholders(spec['runtime'].get('footprint_mib')) or spec['runtime'].get('footprint_mib') is None:
                        if not runner.cfg.get('dryrun'):
                            sample=gpu_sample(runner.cfg);apps=lsi.gpu_compute_apps()
                            if apps is None or apps or sample['free_mib']<1024 or sample['utilisation_percent']>5:
                                raise PreparationStop('STOP: GPU not available for independent qualification')
                        qual_dir=path.parent/'qualification'
                        try: runner.run_job({'out':str(qual_dir),'config':runner.cfg,'candidate':spec,'ctx':ctx},'r1.exam.qualify')
                        except RuntimeError:
                            if not (qual_dir/'qualification.json').exists(): raise
                        qualification=json.loads((qual_dir/'qualification.json').read_text())
                        if qualification['status']=='PREPARATION_STOP': raise PreparationStop('STOP: offload qualification lacks required telemetry')
                        if qualification['status']!='PASS': raise MechanicalFailure('independent exact-path offload qualification failed')
                        spec['runtime']['footprint_mib']=qualification['footprint_mib']
                    else: qualification={'status':'PINNED','footprint_mib':spec['runtime']['footprint_mib']}
                    inst=runner.server(spec,mode,ctx)
                    runner.run_job({'out':str(path.parent),'config':runner.cfg,'candidate':spec,'port':inst.port,'ctx':ctx},'r1.exam.stage_a')
                    result=json.loads(path.read_text())
                    result.update(qualification=qualification,proposal_schema='manager_proposal/v1',model_sha256=spec['quant_source']['sha256'],
                                  build=runner.cfg['server']['build'],thinking_policy=spec['thinking_policy'],
                                  server_record=str(inst.record_path),ctx_size=ctx,cache_type='q8_0',n_gpu_layers=999)
                    write_json(path,result)
                except MechanicalFailure as exc:
                    result={'candidate':spec['id'],'label':'EXAM','phase':'stage-a','passed':False,'failure_classes':['offload'],
                            'error':repr(exc),'prompts':0,'cpu_pool_only':ctx==16384,
                            **prefill_metadata(ctx),'prefill_not_attempted_reason':'qualification/load failure'}
                    write_json(path,result)
                finally:
                    if runner.service: runner.stop_service()
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


def evidence(runner, phase, selected, interrupt):
    cfg=runner.cfg;rows=[]
    if digest_file(cfg['stage_a_table'])!=cfg['stage_a_table_sha256']: raise PreparationStop('STOP: Stage A table digest mismatch')
    if phase=='b2' and digest_file(cfg['b1_analysis'])!=cfg['b1_analysis_sha256']: raise PreparationStop('STOP: B1 analysis digest mismatch')
    stages=json.loads(Path(cfg['stage_a_table']).read_text())['rows'];eligible={r['candidate']:r for r in stages if r['passed']}
    specs=runner.spec_order(selected)
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
        if phase=='b2':
            row=next(r for r in screen['rows'] if r['candidate']==spec['id']);mode=row['b2_thinking_mode'];modes=[mode]
            if mode=='on' and eligible[spec['id']].get('thinking_disabled_due_grammar'): raise PreparationStop('STOP: B1 chose thinking-on disabled by Stage A')
            rank=screen['finalists'].index(spec['id']) if spec['id'] in screen['finalists'] else 99
            if not cfg.get('free_sensitivity') and rank<3 and spec.get('thinking_policy',{}).get('switchable') is True and not eligible[spec['id']].get('thinking_disabled_due_grammar'): modes.append('on' if mode=='off' else 'off')
        root_results=[];began=time.monotonic()
        try:
            for mode_index,current_mode in enumerate(modes):
                nodes=([cfg['schema_sensitivity_node']] if cfg.get('free_sensitivity') else (cfg['nodes'] if mode_index==0 or phase=='b2' else ['openml_credit_approval']))
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
        d28=all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in root_results)
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
        uncertain=any(x.get('cost_is_upper_bound') for x in runner.state.get('server_intervals',[]) if x['candidate']==spec['id'] and x['phase']==phase)
        manifest['gpu_hours_upper_bound']=manifest['gpu_hours']
        manifest['gpu_hours_status']='upper_bound_after_interruption' if uncertain else 'recorded_dedicated_intervals'
        if uncertain: manifest['gpu_hours']=None
        path=runner.out/spec['id']/f'{phase}_manifest.json';write_json(path,manifest);rows.append(manifest)
    write_json(runner.out/f'{phase}_manifests.json',{'label':'EXAM','manifests':rows})


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['stage-a','b1','b2'],nargs='?')
    p.add_argument('--config',default=str(DEFAULT_CONFIG));p.add_argument('--out');p.add_argument('--candidate',action='append')
    p.add_argument('--free-sensitivity',action='store_true',help='B2 only: one-node free-generation sensitivity for 7B and the author-recorded D22 pick')
    p.add_argument('--check-config',action='store_true');p.add_argument('--allow-placeholders',action='store_true')
    p.add_argument('--interrupt-root',action='store_true',help='DRYRUN only: kill first root worker after one ledger append')
    a=p.parse_args(argv)
    if a.allow_placeholders and not a.check_config: p.error('--allow-placeholders is only for --check-config')
    cfg=load_config(a.config,allow_placeholders=a.allow_placeholders)
    if a.free_sensitivity:
        if a.phase!='b2': p.error('--free-sensitivity requires b2')
        cfg['free_sensitivity']=True
        if not cfg.get('d22_pick') or placeholders(cfg['d22_pick']): raise RuntimeError('STOP: author D22 pick required')
    if a.check_config: print(json.dumps({'valid':True,'unresolved':placeholders(cfg)}));return 0
    if not a.phase or not a.out: p.error('phase and --out required')
    if a.interrupt_root and not cfg.get('dryrun'): p.error('--interrupt-root is DRYRUN only')
    required=['prompts','prompts_sha256'] if a.phase=='stage-a' else ['stage_a_table','stage_a_table_sha256','nodes','llm_call_cap','anchor_duplicate_reference']
    if a.phase=='b2': required += ['b1_analysis','b1_analysis_sha256','b2_instances_per_node']
    unresolved=placeholders({k:cfg[k] for k in required})
    if unresolved: raise RuntimeError(f'STOP: unresolved phase settings: {unresolved}')
    runner=ExamRunner(cfg,a.out)
    try:
        runner.start(a.phase)
        if a.phase=='stage-a': stage_a(runner,a.candidate)
        else: evidence(runner,a.phase,a.candidate,a.interrupt_root)
        runner.state['status']='COMPLETE';runner.save()
    except BaseException as exc:
        runner.state.update(status='STOPPED',stop_reason=f'{type(exc).__name__}: {exc}')
        if runner.lock is not None: runner.save()
        print(runner.state['stop_reason'],file=sys.stderr);return 1
    finally: runner.close()
    return 0

if __name__=='__main__': raise SystemExit(main())
