"""Synthetic Stage A -> B1 process-loss recovery, never a lease/host test.

Stage A's Mac-unavailable D3 and process identity are explicitly monkeypatched
inside this test only; real Stage A worker subprocesses and probe calculations
run over fabricated replies. B1 uses its actual parent/child code and local fake
llama-server. The deliberately killed parent and its children are test-owned.
No STOPPED batch is resumed, no real model or GPU is used.
"""
import copy
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT=Path(__file__).resolve().parents[2]


def _tree_contents(root):
    """Snapshot directory paths and regular-file bytes in the synthetic root."""
    files={};directories=[]
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink(), f'unexpected synthetic symlink: {path}'
        if path.is_dir():
            directories.append(str(path.relative_to(root)))
            continue
        assert path.is_file(), f'unexpected synthetic special file: {path}'
        files[str(path.relative_to(root))]=path.read_bytes()
    assert files
    return {'directories':directories,'files':files}


def _stage_a_with_fabricated_transport(root, cfg, monkeypatch):
    """Generate five Stage A rows through the real Stage A calculations.

    This deliberately does not exercise the lease, cold-cache identity, native
    server, or independent qualification. A real Stage A worker subprocess is
    entered via actual ExamRunner.run_job with substituted lease, recorder journals,
    identity, and telemetry and a real localhost fake server. Those remain site checks and are not represented by the resulting DRYRUN fixture.
    """
    from r1.exam import cache_runtime, stage_a, runtime
    from r1.scripts import exam_runner
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr(cache_runtime,'reject_unverified_lease',lambda:None)
    monkeypatch.setattr(cache_runtime,'capture_parent_identity',lambda *a,**k:{'scope':'SYNTHETIC'})
    monkeypatch.setattr(cache_runtime,'reject_unverified_cold',lambda *a:None)
    registry=yaml.safe_load(Path(cfg['registry']).read_text())
    selected={'random_valid','scripted','qwen25_coder_7b','qwen38_27b','gemma4_31b'}
    specs=registry['software_anchors']+[x for x in registry['candidates'] if x['role']=='anchor']+\
          [x for x in registry['candidates'] if x['role']=='candidate']
    specs=[copy.deepcopy(x) for x in specs if x['id'] in selected]
    for spec in specs:
        if spec.get('runtime'): spec['runtime']['footprint_mib']=1
    # Stage A worker output is rewritten by its real orchestrator; retire each
    # existing test-owned version before the ordinary write, preserving bytes.
    original_write=exam_runner.write_json
    versions=[0]
    def preserve_then_write(path,data):
        path=Path(path)
        if path.exists():
            archive=path.parent/'_to_delete'
            archive.mkdir(mode=0o700,exist_ok=True)
            versions[0]+=1
            destination=archive/f'{path.name}.{versions[0]:06d}'
            if destination.exists() or destination.is_symlink(): raise RuntimeError('STOP: synthetic version collision')
            path.rename(destination)
        return original_write(path,data)
    monkeypatch.setattr(exam_runner,'write_json',preserve_then_write)
    runner=runtime.ExamRunner(cfg,root/'stage-a')
    runner.state={'phase':'stage-a','completed':{},'interruptions':[],'execution_label':'DRYRUN'}
    monkeypatch.setattr(runner,'spec_order',lambda selected=None:specs)
    monkeypatch.setattr(runner,'validate_spec',lambda *a,**k:None)
    monkeypatch.setattr(runner,'save',lambda:None)
    from r1.scripts.llama_server_instance import LlamaServerInstance
    def fake_server(spec,mode,ctx):
        inst=LlamaServerInstance(root/'stage-a'/'servers'/spec['id'],cfg['server']['binary'],
            model_path=spec['runtime']['model_path'],alias=spec['id'],ctx_size=ctx,
            gpu_uuid='GPU-DRYRUN',label='DRYRUN',start_timeout=10)
        inst.b1_preserve_records=True
        runner.service=inst
        inst.start(build={'version_line':'version: 0 (DRYRUN)'},model_sha256=spec['quant_source']['sha256'])
        return inst
    def stop_fake_server():
        if runner.service is not None:
            runner.service.stop()
            runner.service=None
    monkeypatch.setattr(runner,'server',fake_server)
    monkeypatch.setattr(runner,'stop_service',stop_fake_server)
    monkeypatch.setenv('R1_FAKE_OLLAMA_ROOT',str(root))
    read_fd,write_fd=os.pipe()
    monkeypatch.setattr(cache_runtime,'verified_lease_fd',lambda:read_fd)
    original_popen=subprocess.Popen
    spawned=[]
    def synthetic_stagea_popen(args,*a,**kw):
        if len(args)>=3 and args[1:3]==['-m','r1.exam.stage_a']:
            assert kw.get('pass_fds')==(read_fd,)
            args=list(args);args[2]='r1.tests.stagea_fabricated_worker_20261108'
            kw['env']={**kw['env'],'SYNTHETIC_LEASE_FD':str(read_fd)}
            child=original_popen(args,*a,**kw);spawned.append(child.pid);return child
        return original_popen(args,*a,**kw)
    monkeypatch.setattr(runtime.subprocess,'Popen',synthetic_stagea_popen)
    try:
        exam_runner.stage_a(runner,list(selected))
    finally:
        os.close(read_fd);os.close(write_fd)
    assert len(spawned)==3 and len(set(spawned))==3
    logs=sorted((root/'stage-a').glob('*/stage-a/32768/runner.log'))
    assert len(logs)==3
    recorded=[]
    for path in logs:
        first=path.read_text().splitlines()[0]
        assert 'SYNTHETIC_STAGE_A_WORKER pid=' in first and 'lease_fd_open=True' in first
        recorded.append(int(first.split('pid=')[1].split()[0]))
    assert sorted(recorded)==sorted(spawned)
    table=json.loads((runner.out/'stage_a_table.json').read_text())
    assert len(table['rows'])==5 and {x['candidate'] for x in table['rows']}==selected
    assert all(x['passed'] for x in table['rows'])
    for row in table['rows']:
        if not row.get('software_anchor'):
            assert row['prefill_tokens']==32767 and row['prefill_generated_tokens']==1
            assert len(row['template_checks'])==5 and len(row['template_checks_frozen'])==50
            assert row['schema_parse_successes']==50 and row['free_parse_successes']==50
    return runner.out/'stage_a_table.json'


def test_stagea_real_worker_to_b1_owned_parent_crash_and_recovery(tmp_path,monkeypatch):
    harness=os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        if os.environ.get('R1_REQUIRE_B1_HARNESS')=='1': pytest.fail('pinned harness required')
        pytest.skip('set AR_HARNESS_B1_ROOT to pinned local harness')
    assert subprocess.check_output(['git','-C',harness,'rev-parse','HEAD'],text=True).strip()=='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    monkeypatch.setenv('AR_HARNESS_ROOT',harness)
    from r1.scripts.exam_dryrun import prepare
    from r1.exam.guards import digest_file
    root=tmp_path/'stagea_b1_synthetic';config_path=prepare(root)
    cfg=json.loads(config_path.read_text());registry=yaml.safe_load(Path(cfg['registry']).read_text())
    specs=registry['software_anchors']+registry['candidates']+registry.get('sensitivities',[])
    cfg.update(rule=str(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               rule_sha256=digest_file(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               nodes=['digits_mlp','openml_credit_approval'],instance_seeds=[9001],W=4,llm_call_cap=24,
               cache_prompt=False,d3_policy='author_same_uid_cooperative_20261031',harness_commit='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2',
               authorizations={'b1':str(root/'SYNTHETIC_UNUSED_NOTE')},
               template_repairs={s['id']:s['template_repair']['sha256'] for s in specs if s.get('template_repair')})
    table=_stage_a_with_fabricated_transport(root,cfg,monkeypatch)
    amendment=root/'SYNTHETIC_amendment.json';amendment.write_text(json.dumps({'label':'ENGINEERING_ONLY','rows':[]}))
    acceptance=root/'SYNTHETIC_acceptance.txt';acceptance.write_text('DRYRUN ONLY\n'+digest_file(table)+'\n'+digest_file(amendment)+'\n')
    cfg.update(stage_a_table=str(table),stage_a_table_sha256=digest_file(table),
               stage_a_amendment_table=str(amendment),stage_a_amendment_table_sha256=digest_file(amendment),
               stage_a_amendment_acceptance=str(acceptance),stage_a_amendment_acceptance_sha256=digest_file(acceptance))
    config_path.write_text(json.dumps(cfg))
    env={**os.environ,'AR_HARNESS_ROOT':harness,'R1_FAKE_OLLAMA_ROOT':str(root),
         'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1','C3_FAKE_EXIT_IF_ORPHANED':'1'}
    env.pop('LLAMACPP_CACHE_PROMPT',None)
    out=root/'b1';selected=['random_valid','scripted','qwen25_coder_7b','qwen38_27b','gemma4_31b']
    args=[sys.executable,'-m','r1.tests.b1_synthetic_trace_runner_20261108','b1','--config',str(config_path),
          '--out',str(out)]+[arg for name in selected for arg in ('--candidate',name)]
    log=root/'SYNTHETIC_parent_first.log'
    with log.open('w') as output:
        parent=subprocess.Popen(args,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        try:
            until=time.monotonic()+90;state=None;partial=None
            while time.monotonic()<until:
                if parent.poll() is not None: pytest.fail('synthetic parent exited before crash: '+log.read_text())
                state_path=out/'batch_state.json'
                if state_path.exists():
                    state=json.loads(state_path.read_text())
                    progress=state.get('in_progress') or {};partial=Path(progress.get('path','/nonexistent'))
                    ledger=partial/'root_trials.jsonl'
                    if (len(state.get('completed',{}))>=4 and '/qwen25_coder_7b/' in str(partial) and
                            ledger.is_file() and ledger.stat().st_size and not (partial/'campaign_manifest.json').exists()): break
                time.sleep(.01)
            else: pytest.fail('synthetic crash point not reached: '+log.read_text())
            assert state['status']=='RUNNING' and not state.get('stop_reason')
            completed={k:(v['path'],digest_file(v['path']),v['post_check_sha256']) for k,v in state['completed'].items()}
            partial_prefix=(partial/'root_trials.jsonl').read_bytes()
            child_pid=(state['in_progress'] or {})['pid']
            job=json.loads((partial/'job.json').read_text())
            records=list((out/'servers'/'qwen25_coder_7b').glob('llama_server_*.json'))
            assert len(records)==1
            server_record=json.loads(records[0].read_text())
            server_pid=server_record['pid']
            assert type(server_pid) is int and server_pid>1 and len({server_pid,child_pid,parent.pid})==3
            assert (server_record['label']=='DRYRUN' and server_record['alias']=='qwen25_coder_7b' and
                    server_record['binary']==str(root/'fake_llama_server') and
                    server_record['model_path']==str(root/'models'/'qwen25_coder_7b.gguf') and
                    server_record.get('stopped_utc') is None and
                    job['base_url']==server_record['openai_base_url'] and job['candidate']['id']=='qwen25_coder_7b')
            before_calls=[json.loads(x) for x in (root/'fake_calls.jsonl').read_text().splitlines()]
            serve=[e for e in before_calls if e.get('event')=='serve' and e.get('pid')==server_pid and
                   e.get('server')=='llama-server' and e.get('alias')=='qwen25_coder_7b' and
                   e.get('port')==server_record['port'] and e.get('model')==server_record['model_path']]
            assert len(serve)==1 and serve[0]['label']=='DRYRUN'
            os.kill(child_pid,0);os.kill(server_pid,0)  # observation only; no signal
            # Kill only this freshly created, test-owned synthetic parent; no
            # runner STOP is written and no real job or unknown PID is signalled.
            parent.send_signal(signal.SIGKILL);parent.wait(timeout=10)
        finally:
            if parent.poll() is None: parent.kill();parent.wait(timeout=10)
    assert parent.returncode==-signal.SIGKILL
    # Observe disappearance of this recorded synthetic worker and server. The
    # server additionally logs its parent-loss self-exit; worker exit cause is
    # not independently recorded here. No unknown process is ever signalled.
    def alive(pid):
        try: os.kill(pid,0);return True
        except ProcessLookupError: return False
    calls=root/'fake_calls.jsonl'
    until=time.monotonic()+20
    while time.monotonic()<until and (alive(child_pid) or alive(server_pid)): time.sleep(.05)
    assert not alive(child_pid) and not alive(server_pid), 'STOP: preserve live synthetic child/server for inspection'
    events=[json.loads(x) for x in calls.read_text().splitlines()]
    assert any(e.get('event')=='parent_lost_self_exit' and e.get('pid')==server_pid for e in events)
    partial_bytes=(partial/'root_trials.jsonl').read_bytes()
    assert partial_bytes.startswith(partial_prefix) and partial_bytes
    partial_tree=_tree_contents(partial)
    crashed=json.loads((out/'batch_state.json').read_text())
    assert crashed['status']=='RUNNING' and not crashed.get('stop_reason')
    resumed=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
    assert resumed.returncode==0,resumed.stdout+resumed.stderr
    result=json.loads((out/'batch_state.json').read_text())
    assert result['status']=='COMPLETE' and len(result['completed'])==11
    for key,(path,sha,check_sha) in completed.items():
        assert result['completed'][key]['path']==path and digest_file(path)==sha
        assert result['completed'][key]['post_check_sha256']==check_sha
        assert digest_file(Path(path).parent/'post_check.json')==check_sha
    archived=list((out/'interrupted').glob('*'))
    assert len(archived)==1 and _tree_contents(archived[0])==partial_tree
    assert all(json.loads(Path(v['path']).read_text())['execution_label']=='DRYRUN' for v in result['completed'].values())
