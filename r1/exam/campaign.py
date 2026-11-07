"""One isolated exam campaign or Stage A worker. Parent monitors server and disk; no C3 export."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
import yaml
from r1.harness import import_harness
HARNESS=import_harness()
from autoresearch.control_plane.action_versions import ActionVersions
from autoresearch.control_plane.budget import ComputeBudget
from autoresearch.control_plane.campaign import run_real_campaign
from autoresearch.manager.langgraph_manager import LangGraphManager
from autoresearch.manager.random_valid import RandomValidManager
from autoresearch.memory.event_store import CampaignEventStore
from autoresearch.nodes.registry import load_registered_node
from autoresearch.worker.local_worker import LocalWorker
from autoresearch.worker.base import WorkerResult
from r1.c3.audit import run_config, paired
from r1.exam.b1_proposal_guard import B1IntegrityWorker
from r1.c3.features import apply_edit, files_hash, replay_campaign
from r1.exam.observer import SelfForecastObserver, B1ObserverAdapter, authorized_b1_observer
from r1.exam.b1_observer_journal import validate_observer_journal
from r1.exam.guards import artifact_label, digest_file
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.liveness.check import evaluate_ledger_paths


def write_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(data,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def run_b1_audits(node, configs, job, out, cache, save_cache):
    """Bound queued work and notify the owning runner on audit failure."""
    from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
    # A dedicated inherited pipe asks the parent to use its existing stop_tree path.
    stop_fd=int(os.environ['R1_B1_STOP_FD'])
    entries=iter(configs.items())
    with ProcessPoolExecutor(max_workers=job['workers']) as pool:
        active={}
        def submit_one():
            try: h,value=next(entries)
            except StopIteration: return False
            active[pool.submit(run_config,node,value['files'],job['audit_seeds'],str(out),preserve_node_outputs=True,stop_on_invalid=True)]=h
            return True
        try:
            for _ in range(job['workers']):
                if not submit_one(): break
            while active:
                done,_=wait(active,return_when=FIRST_COMPLETED)
                # Observe every already-complete result before dispatching more work.
                done |= {f for f in active if f.done()}
                for future in done:
                    h=active.pop(future);runs=future.result()
                    import math
                    if (len(runs)!=len(job['audit_seeds']) or any(
                            not r.get('success') or isinstance(r.get('metric'),bool) or
                            not isinstance(r.get('metric'),(int,float)) or not math.isfinite(r['metric'])
                            for r in runs)):
                        raise RuntimeError('STOP: invalid B1 audit results')
                    cache[h]=[r['metric'] if r['success'] else None for r in runs]
                    save_cache()
                for _ in done: submit_one()
        except BaseException as exc:
            import sys
            for future in active: future.cancel()
            try: print(f'STOP: audit failure: {type(exc).__name__}: {exc}',file=sys.stderr,flush=True)
            except Exception: pass
            try: os.write(stop_fd,b'1')
            except OSError:
                # A broken notification pipe falls back to an exclusive marker.
                # If both channels fail, the parent enforces its campaign deadline.
                try:
                    with (Path(out)/'audit_stop_notification').open('x') as marker:
                        marker.write('STOP: audit failure; see runner.log\n')
                except OSError: pass
            raise


def read_rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def fixture_metric(files, seed):
    h=int(hashlib.sha256((json.dumps(files,sort_keys=True)+str(seed)).encode()).hexdigest()[:8],16)
    return .5+(h%10000)/100000


class FixtureWorker:
    """Deterministic synthetic CPU fixture only; never a scientific measurement."""
    mode='EXAM_DRYRUN_fixture'
    def __init__(self, root, seed): self.node_root=Path(root);self.seed=seed
    def run_trial(self, proposal, node_spec, budget_index):
        time.sleep(.2)  # give the DRYRUN parent an observable kill point
        files={p:(self.node_root/p).read_text() for p in node_spec.editable_paths}
        edit=proposal.extra.get('structured_edit')
        if edit:
            files=apply_edit(files,edit)
            for p,text in files.items(): (self.node_root/p).write_text(text)
        return WorkerResult(self.mode,node_spec.editable_paths,True,{node_spec.metric_name:fixture_metric(files,self.seed)},
                            'DRYRUN.log','DRYRUN.diff','DRYRUN-before','DRYRUN-after')


def observer_for_campaign(job, out):
    """Bind the observer journal to this root without opening it in advance."""
    candidate=job['candidate']
    if candidate.get('kind','llm')!='llm': return None
    return SelfForecastObserver(job['base_url'],candidate['id'],journal_path=Path(out)/'a4_observer_requests.jsonl')


def exam_manager(candidate, proposal_schema):
    """The LLM proposer of an exam campaign, exactly as ``collect`` builds it.

    The llamacpp provider of the pinned harness decides the wire value of ``cache_prompt``: at the
    B1/B2 pin ``a3fedbb`` (R1-EXAM-B1-HARNESS-PIN) it is sent explicitly, default false, and recorded
    in every ``llm_call`` record (R1-EXAM-CACHE-REV)."""
    return LangGraphManager(model='llamacpp/'+candidate['id'],proposal_schema=proposal_schema,transport_retry=None)


def cache_prompt_evidence(records, events):
    """Fail closed unless every LLM call of the root recorded ``cache_prompt`` false.

    Reads the ``llm_call`` events and the per-trial ``extra.manager.llm_call`` records.  A call
    without the field (an older harness pin that does not send it) or with any other value is a STOP."""
    calls=[e['payload'] for e in events if e.get('event_type')=='llm_call']
    failed=[e['payload'] for e in events if e.get('event_type')=='llm_call_failed']
    trial=[((r.get('extra') or {}).get('manager') or {}).get('llm_call') for r in records]
    trial=[t for t in trial if t]
    values=[c.get('cache_prompt','MISSING') for c in calls+failed+trial]
    if not calls: raise RuntimeError('STOP: no llm_call records; cache_prompt unproven')
    if any(v is not False for v in values):
        raise RuntimeError(f'STOP: llm_call cache_prompt not explicitly false: {sorted(set(map(str,values)))}')
    return {'cache_prompt':False,'llm_call_events':len(calls),'llm_call_failed_events':len(failed),
            'trial_llm_call_records':len(trial),'all_false':True}


def require_worker_host(job, node=None):
    """B1/B2 campaign workers run only on the configured exam host (R1-EXAM-HOST-B1B2-TASL7, author 4 Nov 18:10).

    Replaces the hard-coded TASL-2 check: the job's ``host`` (``cfg.host``, set by ``ExamRunner.root``)
    must be one of ``runtime.APPROVED_EXAM_HOSTS`` and must equal this node's short hostname.  DRYRUN jobs
    never call this (their marked temporary root is checked instead)."""
    import platform
    from r1.exam.runtime import APPROVED_EXAM_HOSTS
    host=job.get('host')
    if host not in APPROVED_EXAM_HOSTS:
        raise RuntimeError(f'STOP: EXAM worker host {host!r} is not an approved exam host {sorted(APPROVED_EXAM_HOSTS)}')
    node=(node if node is not None else platform.node()).split('.')[0]
    if node!=host: raise RuntimeError(f'STOP: EXAM worker on {node!r} but the configured exam host is {host!r}')
    return host


def collect(job):
    if job.get('phase') != 'b1':
        raise RuntimeError('STOP: B2 observer integration is not implemented')
    return _collect_b1_review(job)


def _verify_b1_worker_input(job):
    """Recheck the committed authority at the separate B1 worker entry.

    This is a cooperative point-in-time check; it does not lock the checkout
    or establish that a direct caller is the reviewed runner process.
    """
    from r1.exam.runtime import (REPO, B1_CONFIG_REL, require_committed_b1_config,
                                 require_committed_b1_registry, author_gate)
    cfg=job.get('authority_config')
    if not isinstance(cfg,dict) or cfg.get('dryrun'):
        raise RuntimeError('STOP: production B1 worker requires production authority configuration')
    head=require_committed_b1_config(REPO/B1_CONFIG_REL,cfg)
    if head!=job.get('authorization_checkout_head'):
        raise RuntimeError('STOP: B1 worker configuration HEAD differs from job')
    require_committed_b1_registry(cfg,head)
    if author_gate(cfg,'b1',cfg['rule_sha256'])!=head:
        raise RuntimeError('STOP: B1 worker author HEAD differs from configuration HEAD')
    for key in ('workers','W','llm_call_cap','audit_seeds','value_grids'):
        if job.get(key)!=cfg.get(key):
            raise RuntimeError(f'STOP: B1 worker job {key} differs from committed configuration')
    if job.get('host')!=cfg.get('host') or job.get('node') not in cfg.get('nodes',[]):
        raise RuntimeError('STOP: B1 worker host/node differs from committed configuration')
    if job.get('seed') not in cfg.get('instance_seeds',[]) or job.get('mode') not in ('off','on'):
        raise RuntimeError('STOP: B1 worker seed/mode differs from committed configuration')
    if job.get('proposal_schema')!=cfg.get('proposal_schema'):
        raise RuntimeError('STOP: B1 worker proposal schema differs from committed configuration')
    return head


def _collect_b1_review(job):
    """Collect a B1 campaign with the authorized observer and cache evidence."""
    if job.get('phase') != 'b1': raise RuntimeError('STOP: B1 candidate refuses other phases')
    out=Path(job['out'])
    if not job['dryrun']:
        _verify_b1_worker_input(job)
        # A direct campaign invocation has no parent runner to enforce the
        # approved work-tree boundary. This check does not prove ownership of
        # an existing path inside that tree; the reviewed parent procedure is
        # still required and same-UID processes are cooperative.
        from r1.exam.runtime import host_check
        host_check(job.get('authority_config',{}),out)
        require_worker_host(job)
    if job['dryrun'] and not any((p/'.dryrun').is_file() for p in out.resolve().parents): raise RuntimeError('STOP: unmarked DRYRUN child')
    if not job['dryrun']:
        from r1.exam.runtime import b1_harness_sources
        if job.get('harness_commit')!=job.get('authority_config',{}).get('harness_commit') or \
                job.get('node_source_sha256')!=b1_harness_sources(job['node'],job['harness_commit']):
            raise RuntimeError('STOP: B1 worker harness or initial node sources differ from parent')
    out.mkdir(parents=True,exist_ok=True)
    node=job['node'];seed=job['seed'];spec=load_registered_node(node,repo_root=HARNESS)
    node_root=out/'node'
    shutil.copytree(HARNESS/'nodes'/node,node_root,ignore=shutil.ignore_patterns('__pycache__','.autoresearch_artifacts'))
    if node.startswith('openml_') and not (node_root/'data_cache').exists() and not job['dryrun']:
        cache=HARNESS/f'experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache'
        if not cache.exists(): raise RuntimeError(f'STOP: missing verified OpenML cache for {node}')
        shutil.copytree(cache,node_root/'data_cache')
    start={p:(node_root/p).read_text() for p in spec.editable_paths}
    candidate=job['candidate'];kind=candidate.get('kind','llm')
    if kind=='random_valid':
        manager=RandomValidManager(yaml.safe_load(Path(job['value_grids']).read_text())['nodes'][node])
    elif kind=='scripted': manager=ScriptedRandomManager(node,seed=seed,repetition=0)
    else: manager=exam_manager(candidate,job['proposal_schema'])
    worker=FixtureWorker(node_root,seed) if job['dryrun'] else B1IntegrityWorker(node_root=node_root,artifact_dir=out/'art',train_seed=seed,split_seed=seed)
    raw_observer=observer_for_campaign(job,out)
    observer=B1ObserverAdapter(raw_observer) if raw_observer is not None else None
    try:
        with authorized_b1_observer(job):
            run_real_campaign(node_spec=spec,campaign_id=f'{node}__s{seed}',budget=job['llm_call_cap'] if kind=='llm' else 1_000_000,
                              manager_mode='baseline_manager',memory_mode='append_only_summary',records_path=out/'root_trials.jsonl',worker=worker,
                              proposal_backend=manager,compute_budget=ComputeBudget(max_worker_runs=job['W'],max_llm_calls=job['llm_call_cap']),
                              action_versions=ActionVersions.new_campaign(),verify_split_policy='vary',
                              event_store=CampaignEventStore(out/'root_events.jsonl'),proposal_observer=observer)
    finally:
        if observer is not None: observer.close()
    records=read_rows(out/'root_trials.jsonl');events=read_rows(out/'root_events.jsonl')
    props,checks=replay_campaign(records,start,node,f'{node}__s{seed}','EXAM','append_only_summary',job['W'],1.)
    forecasts={e['trial_id']:e['payload'] for e in events if e['event_type']=='exam_self_forecast'}
    cache={};audits=[];configs={};cache_identity=None
    def save_cache():
        nonlocal cache_identity
        if job['dryrun']:
            write_json(out/'audit_cache.json',cache)
        else:
            from r1.exam.b1_state_preserve import publish_audit_cache
            cache_identity=publish_audit_cache(out/'audit_cache.json',cache,cache_identity)
    audited=[p for p in props if not p.features.get('active_equals_incumbent') and not p.features.get('active_seen_before')]
    for p in audited:
        for files in (p.candidate_files,p.incumbent_files): configs[files_hash(files)]={'node':node,'files':files}
    write_json(out/'audit_configs.json',configs)
    if not job['dryrun']:
        run_b1_audits(node,configs,job,out,cache,save_cache)
    for p in props:
        if p.features.get('active_equals_incumbent') or p.features.get('active_seen_before'): continue
        arrays=[]
        for files in (p.candidate_files,p.incumbent_files):
            h=files_hash(files)
            if h not in cache:
                if job['dryrun']: cache[h]=[fixture_metric(files,s) for s in job['audit_seeds']]
                else:
                    runs=run_config(node,files,job['audit_seeds'],str(out),preserve_node_outputs=True,stop_on_invalid=True)
                    cache[h]=[r['metric'] if r['success'] else None for r in runs]
                save_cache()
            arrays.append(cache[h])
        result=paired(*arrays)
        if result['k']!=len(job['audit_seeds']): raise RuntimeError('STOP: missing/failed paired audit seeds')
        trial=f'{node}__s{seed}-trial-{p.budget_index:03d}'
        audits.append({'proposal_id':p.proposal_id,'instance_id':f'{node}__s{seed}','node':node,'mode':job['mode'],
                       'audit_seeds':job['audit_seeds'],'candidate_hash':p.candidate_hash,'incumbent_hash':p.incumbent_hash,'candidate_metrics':arrays[0],'incumbent_metrics':arrays[1],
                       **result,**{k:v for k,v in forecasts.get(trial,{}).items() if k in ('p_delta_positive','p_no_effect')}})
    cache_prompt=cache_prompt_evidence(records,events) if kind=='llm' else None
    observer_evidence=validate_observer_journal(out/'a4_observer_requests.jsonl',events) if kind=='llm' else None
    live=evaluate_ledger_paths([out/'root_trials.jsonl'],manager_kind='scripted' if kind!='llm' else 'langgraph',memory_mode='append_only_summary')
    novelty=[e['payload'] for e in events if e['event_type']=='edit_novelty']
    evaluated=len(novelty)
    diagnostics={'trials':len(records),'evaluated':evaluated,
                 'invalid':sum(r['decision']=='failed_invalid' for r in records),
                 'duplicates':sum(bool(p.get('active_config_seen_before')) for p in novelty),
                 'noops':sum(bool(p.get('active_config_equals_incumbent')) for p in novelty),
                 'parse_failed':sum(bool(((r.get('extra') or {}).get('manager') or {}).get('parse_failed')) or ((((r.get('extra') or {}).get('manager') or {}).get('llm_call')) or {}).get('parse_ok') is False for r in records)}
    diagnostics.update(forecast_queries=len(forecasts),forecast_query_failed=sum(r.get('status')=='query_failed' for r in forecasts.values()))
    final=[]
    if job['phase']=='b2':
        files={p:(node_root/p).read_text() for p in spec.editable_paths}
        vals=[fixture_metric(files,s) for s in job['audit_seeds']] if job['dryrun'] else [r['metric'] for r in run_config(node,files,job['audit_seeds'],str(out),preserve_node_outputs=True,stop_on_invalid=True)]
        if any(v is None for v in vals): raise RuntimeError('STOP: incomplete final Y audit')
        final=[{'instance_id':f'{node}__s{seed}','node':node,'seeds':job['audit_seeds'],'metrics':vals,'final_y':sum(vals)/len(vals)}]
    completed=next(e['payload'] for e in reversed(events) if e['event_type']=='campaign_completed')
    budget=completed.get('compute_budget') or {'worker_runs':sum(not ((r.get('extra') or {}).get('worker') or {}).get('worker_skipped',False) and r['decision']!='skipped' for r in records),'llm_calls':0}
    result={'label':'EXAM','execution_label':'DRYRUN' if job['dryrun'] else 'EVIDENCE','status':'COMPLETE',
            'phase':job['phase'],'candidate':candidate['id'],'source_label':artifact_label(candidate),'mode':job['mode'],'instance_seed':seed,'node':node,
            'proposal_schema':job['proposal_schema'] if kind=='llm' else None,'observer':'exam_self_forecast/v1' if observer else None,
            'compute_budget':budget,'termination':'worker_cap' if budget['worker_runs']>=job['W'] else 'llm_cap_or_reserved_observer_pair',
            'job_binding':job['binding'],'job_sha256':digest_file(out/'job.json'),
            'evidence_hashes':{name:digest_file(out/name) if (out/name).exists() else None for name in ('root_trials.jsonl','root_events.jsonl','audit_cache.json','audit_configs.json','a4_observer_requests.jsonl')},
            'cache_prompt':cache_prompt,'observer_evidence':observer_evidence,'diagnostics':diagnostics,'audited_proposals':audits,'replay_checks':checks,'d28':live,'final_audits':final}
    write_json(out/'campaign_manifest.json',result)
    return result


def _start_synthetic_parent_watch(expected, on_loss=None):
    """Let a test-owned DRYRUN worker exit itself if its runner disappears."""
    import threading
    import time
    if type(expected) is not int or expected<=1 or os.getppid()!=expected:
        raise RuntimeError('STOP: synthetic worker has lost its original parent')
    def watch():
        while os.getppid()==expected:
            time.sleep(.05)
        if on_loss is not None:
            try: on_loss()
            except OSError: pass
        os._exit(0)
    threading.Thread(target=watch,daemon=True).start()


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
    job=json.loads(Path(a.job).read_text())
    if job.get('dryrun') and os.environ.get('C3_FAKE_EXIT_IF_ORPHANED')=='1':
        try: expected=int(os.environ.get('R1_SYNTHETIC_PARENT_PID',''))
        except ValueError as exc: raise RuntimeError('STOP: synthetic parent identity missing') from exc
        _start_synthetic_parent_watch(expected)
    collect(job)

if __name__=='__main__': main()
