"""Synthetic Stage A -> B1 process-loss recovery, never a lease/host test.

Stage A's Mac-unavailable D3 and process identity are explicitly monkeypatched
inside this test only; the Stage A orchestrator and probe calculations still
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


def _preserve_prepare_config(config_path, archive_dir, cfg):
    """Retain prepare's config before installing this test's synthetic config.

    ``archive_dir`` is a fresh private test-owned directory outside the run
    root. Path.rename does not provide kernel no-replace semantics: this
    helper assumes the new directory and its parent remain cooperative and
    stable throughout this operation. Any failure leaves the scene in place.
    """
    archive_dir.mkdir(mode=0o700)
    config_path.rename(archive_dir / config_path.name)
    with config_path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(cfg))


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
    server, independent qualification, or worker subprocess. Those remain site
    checks and are not represented by the resulting DRYRUN fixture.
    """
    from r1.exam import cache_runtime, stage_a
    from r1.scripts import exam_runner
    from r1.scripts.c3_fake_ollama import proposal_for
    from r1.exam.campaign import write_json
    from autoresearch.llm.providers import manager_response_format

    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr(cache_runtime,'reject_unverified_lease',lambda:None)
    monkeypatch.setattr(cache_runtime,'capture_parent_identity',lambda *a,**k:{'scope':'SYNTHETIC'})
    monkeypatch.setattr(cache_runtime,'reject_unverified_cold',lambda *a:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *a,**k:{'synthetic':True})
    prompts=stage_a.load_prompts(cfg['prompts'],cfg['prompts_sha256'],dryrun=True)
    registry=yaml.safe_load(Path(cfg['registry']).read_text())
    selected={'random_valid','scripted','qwen25_coder_7b','qwen38_27b','gemma4_31b'}
    specs=registry['software_anchors']+[x for x in registry['candidates'] if x['role']=='anchor']+\
          [x for x in registry['candidates'] if x['role']=='candidate']
    specs=[copy.deepcopy(x) for x in specs if x['id'] in selected]
    for spec in specs:
        if spec.get('runtime'): spec['runtime']['footprint_mib']=1
    class Recorder:
        def completion(self,payload):
            return {'tokens_evaluated':len(payload['prompt']),'tokens_predicted':1}
        def chat(self,prompt,*,seed,**kwargs):
            text=json.dumps(proposal_for(prompt,seed))
            return {'choices':[{'message':{'content':text,'reasoning_content':'DRYRUN'}}],
                    'usage':{'completion_tokens_details':{'reasoning_tokens':1}}}
    def render(messages):
        return ''.join(f"{m['role']}: {m['content']}\n" for m in messages)+'assistant: '
    class NonGeneration:
        def post(self,route,payload):
            if route=='/tokenize': return {'tokens':[1]}
            if route=='/apply-template': return {'prompt':render(payload['messages'])}
            raise AssertionError(route)
    class Runner:
        def __init__(self):
            self.cfg=cfg;self.out=root/'stage-a';self.state={'completed':{}};self.service=None
        def spec_order(self,selected=None): return specs
        def validate_spec(self,*args,**kwargs): return None
        def save(self): return None
        def server(self,spec,mode,ctx):
            self.service=SimpleNamespace(port=1,ctx_size=ctx,record_path=root/'SYNTHETIC_SERVER.json')
            return self.service
        def stop_service(self): self.service=None
        def run_job(self,job,module):
            assert module=='r1.exam.stage_a'
            rec=Recorder();nongen=NonGeneration()
            result=stage_a.run_stage_a(self.service,job['candidate'],prompts,
                gpu_sample=lambda:{'free_mib':20000,'used_mib':1000},
                schema_format=manager_response_format(),dryrun=True,template_renderer=render,
                cache_context={'false_recorder':rec,'non_generation_recorder':nongen})
            assert result['passed'],result
            write_json(Path(job['out'])/'stage_a.json',result)
    runner=Runner();exam_runner.stage_a(runner,list(selected))
    table=json.loads((runner.out/'stage_a_table.json').read_text())
    assert len(table['rows'])==5 and {x['candidate'] for x in table['rows']}==selected
    assert all(x['passed'] for x in table['rows'])
    for row in table['rows']:
        if not row.get('software_anchor'):
            assert row['prefill_tokens']==32767 and row['prefill_generated_tokens']==1
            assert len(row['template_checks'])==5 and len(row['template_checks_frozen'])==50
            assert row['schema_parse_successes']==50 and row['free_parse_successes']==50
    return runner.out/'stage_a_table.json'


def test_stagea_to_b1_owned_parent_crash_and_recovery(tmp_path,monkeypatch):
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
    amendment=root/'SYNTHETIC_amendment.json'
    with amendment.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps({'label':'ENGINEERING_ONLY','rows':[]}))
    acceptance=root/'SYNTHETIC_acceptance.txt'
    with acceptance.open('x',encoding='utf-8') as stream:
        stream.write('DRYRUN ONLY\n'+digest_file(table)+'\n'+digest_file(amendment)+'\n')
    cfg.update(stage_a_table=str(table),stage_a_table_sha256=digest_file(table),
               stage_a_amendment_table=str(amendment),stage_a_amendment_table_sha256=digest_file(amendment),
               stage_a_amendment_acceptance=str(acceptance),stage_a_amendment_acceptance_sha256=digest_file(acceptance))
    _preserve_prepare_config(config_path,tmp_path/'_to_delete',cfg)
    env={**os.environ,'AR_HARNESS_ROOT':harness,'R1_FAKE_OLLAMA_ROOT':str(root),
         'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1','C3_FAKE_EXIT_IF_ORPHANED':'1'}
    env.pop('LLAMACPP_CACHE_PROMPT',None)
    out=root/'b1';selected=['random_valid','scripted','qwen25_coder_7b','qwen38_27b','gemma4_31b']
    args=[sys.executable,'-m','r1.scripts.exam_runner','b1','--config',str(config_path),
          '--out',str(out)]+[arg for name in selected for arg in ('--candidate',name)]
    log=root/'SYNTHETIC_parent_first.log'
    with log.open('x',encoding='utf-8') as output:
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


@pytest.mark.parametrize('state',[{'status':'STOPPED','stop_reason':'synthetic STOP'}, {'status':'RUNNING','stop_reason':'synthetic STOP'}])
def test_recorded_stop_is_never_a_crash_recovery_candidate(state):
    from r1.exam.runtime import PreparationStop,reject_stopped_batch
    with pytest.raises(PreparationStop,match='must not be resumed'): reject_stopped_batch(state)
