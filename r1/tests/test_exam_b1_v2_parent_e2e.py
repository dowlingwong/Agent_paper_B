"""B1 v2 synthetic parent/child integration; no real model, Stage A or GPU."""
import json
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
import pytest
import yaml

ROOT=Path(__file__).resolve().parents[2]


def test_b1_v2_parent_to_child_synthetic_receipts(tmp_path, monkeypatch):
    harness=os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        if os.environ.get('R1_REQUIRE_B1_HARNESS')=='1': pytest.fail('pinned B1 harness required')
        pytest.skip('set AR_HARNESS_B1_ROOT to the pinned local harness')
    head=subprocess.check_output(['git','-C',harness,'rev-parse','HEAD'],text=True).strip()
    assert head=='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    monkeypatch.setenv('AR_HARNESS_ROOT',harness)
    from r1.scripts.exam_dryrun import prepare
    from r1.exam.guards import digest_file
    root=tmp_path/'synthetic_b1';config_path=prepare(root)
    cfg=json.loads(config_path.read_text())
    registry=yaml.safe_load(Path(cfg['registry']).read_text())
    rows=registry['software_anchors']+registry['candidates']+registry.get('sensitivities',[])
    cfg.update(rule=str(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               rule_sha256=digest_file(ROOT/'r1/exam/rules/x5_rule_v2.yaml'),
               nodes=['digits_mlp'], instance_seeds=[9001], W=2, llm_call_cap=8,
               cache_prompt=False, harness_commit=head,
               authorizations={'b1':str(root/'SYNTHETIC_UNUSED_NOTE')},
               template_repairs={s['id']:s['template_repair']['sha256'] for s in rows if s.get('template_repair')})
    table=root/'SYNTHETIC_stage_a.json';table.write_text(json.dumps({'label':'DRYRUN','rows':[{'candidate':'qwen25_coder_7b','passed':True}]}))
    amendment=root/'SYNTHETIC_amendment.json';amendment.write_text(json.dumps({'label':'ENGINEERING_ONLY','rows':[]}))
    accept=root/'SYNTHETIC_acceptance.txt';accept.write_text('DRYRUN, not author evidence\n'+digest_file(table)+'\n'+digest_file(amendment)+'\n')
    cfg.update(stage_a_table=str(table),stage_a_table_sha256=digest_file(table),
               stage_a_amendment_table=str(amendment),stage_a_amendment_table_sha256=digest_file(amendment),
               stage_a_amendment_acceptance=str(accept),stage_a_amendment_acceptance_sha256=digest_file(accept))
    config_path.write_text(json.dumps(cfg))
    env={**os.environ,'AR_HARNESS_ROOT':harness,'R1_FAKE_OLLAMA_ROOT':str(root),
         'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1','C3_FAKE_EXIT_IF_ORPHANED':'1'}
    env.pop('LLAMACPP_CACHE_PROMPT',None)
    out=root/'b1'
    try:
        proc=subprocess.run([sys.executable,'-m','r1.scripts.exam_runner','b1','--config',str(config_path),
                             '--out',str(out),'--candidate','qwen25_coder_7b'],cwd=ROOT,env=env,
                            capture_output=True,text=True,timeout=180)
    finally:
        # Observe only test-owned recorded PIDs; never signal an unknown process.
        pids=set();calls=root/'fake_calls.jsonl'
        if calls.exists():
            for line in calls.read_text().splitlines():
                row=json.loads(line)
                if row.get('event')=='serve' and row.get('server')=='llama-server': pids.add(row['pid'])
        state_path=out/'batch_state.json'
        if state_path.exists():
            running=(json.loads(state_path.read_text()).get('in_progress') or {}).get('pid')
            if running: pids.add(running)
        def alive(pid):
            try: os.kill(pid,0);return True
            except ProcessLookupError: return False
        deadline=time.monotonic()+15
        while any(alive(pid) for pid in pids) and time.monotonic()<deadline: time.sleep(.1)
        remaining=[pid for pid in pids if alive(pid)]
        assert not remaining, f'STOP: preserve still-live synthetic test processes for review: {remaining}'
    assert proc.returncode==0,proc.stdout+proc.stderr+'\n'+'\n'.join(p.read_text()[-3000:] for p in out.rglob('runner.log'))
    state=json.loads((out/'batch_state.json').read_text())
    assert state['status']=='COMPLETE' and len(state['completed'])==1
    manifest=json.loads((out/'qwen25_coder_7b/b1_manifest.json').read_text())
    assert manifest['execution_label']=='DRYRUN' and manifest['d28_scope']=='thinking_off_roots_only'
    root_manifest=json.loads(Path(next(iter(state['completed'].values()))['path']).read_text())
    assert root_manifest['observer_evidence']['calls']>0
    assert root_manifest['cache_prompt']['all_false'] is True
    journal=Path(next(iter(state['completed'].values()))['path']).parent/'a4_observer_requests.jsonl'
    assert root_manifest['evidence_hashes']['a4_observer_requests.jsonl']==hashlib.sha256(journal.read_bytes()).hexdigest()
    assert root_manifest['observer_evidence']['sha256']==hashlib.sha256(journal.read_bytes()).hexdigest()


def test_fake_server_exits_when_its_test_parent_disappears(tmp_path):
    """An orphaned fake server exits itself; this test never signals it."""
    root=tmp_path/'fake_parent_loss';root.mkdir();(root/'.dryrun').write_text('synthetic')
    model=root/'fixture.gguf';model.write_bytes(b'fake, no tensors')
    env={**os.environ,'R1_FAKE_OLLAMA_ROOT':str(root),'C3_FAKE_EXIT_IF_ORPHANED':'1'}
    controller='''import json, os, subprocess, sys, time
from pathlib import Path
root=Path(sys.argv[1]); fake=sys.argv[2]; model=sys.argv[3]
env={**os.environ,"R1_SYNTHETIC_PARENT_PID":str(os.getpid())}
p=subprocess.Popen([sys.executable,fake,"-m",model,"--host","127.0.0.1","--port","0","-ngl","0","--alias","fixture"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
deadline=time.monotonic()+10
while time.monotonic()<deadline:
    log=root/"fake_calls.jsonl"
    if log.exists() and any(json.loads(line).get("event")=="serve" for line in log.read_text().splitlines()):
        print(p.pid,flush=True);sys.exit(0)
    if p.poll() is not None: sys.exit(3)
    time.sleep(.05)
sys.exit(4)
'''
    parent=subprocess.run([sys.executable,'-c',controller,str(root),str(ROOT/'r1/scripts/c3_fake_llama_server.py'),str(model)],
                          env=env,cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert parent.returncode==0,parent.stderr
    pid=int(parent.stdout.strip());calls=root/'fake_calls.jsonl';deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        events=[json.loads(x) for x in calls.read_text().splitlines()]
        if any(x.get('pid')==pid and x.get('event')=='parent_lost_self_exit' for x in events): break
        time.sleep(.05)
    else: pytest.fail(f'STOP: fake server {pid} did not record self-exit; preserve for inspection')


def test_synthetic_worker_exits_when_parent_disappears(tmp_path):
    """The synthetic worker notices its original parent even before PID journaling."""
    ready=tmp_path/'worker-ready';gone=tmp_path/'worker-self-exit'
    child='''import os,sys,time
from pathlib import Path
from r1.exam.campaign import _start_synthetic_parent_watch
ready=Path(sys.argv[1]);gone=Path(sys.argv[2]);expected=int(sys.argv[3])
_start_synthetic_parent_watch(expected,lambda:gone.write_text("self-exit"))
ready.write_text("started")
while True: time.sleep(.05)
'''
    controller='''import os,subprocess,sys,time
from pathlib import Path
ready=Path(sys.argv[1]);gone=Path(sys.argv[2]);child=sys.argv[3]
p=subprocess.Popen([sys.executable,"-c",child,str(ready),str(gone),str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
deadline=time.monotonic()+10
while time.monotonic()<deadline:
    if ready.exists(): print(p.pid,flush=True);sys.exit(0)
    if p.poll() is not None: sys.exit(3)
    time.sleep(.05)
sys.exit(4)
'''
    parent=subprocess.run([sys.executable,'-c',controller,str(ready),str(gone),child],cwd=ROOT,
                          env={**os.environ,'PYTHONPATH':str(ROOT)},capture_output=True,text=True,timeout=20)
    assert parent.returncode==0,parent.stderr
    deadline=time.monotonic()+10
    while not gone.exists() and time.monotonic()<deadline: time.sleep(.05)
    assert gone.read_text()=='self-exit'


def test_synthetic_worker_refuses_already_lost_parent(monkeypatch):
    from r1.exam import campaign
    monkeypatch.setattr(campaign.os,'getppid',lambda:999)
    with pytest.raises(RuntimeError,match='lost its original parent'):
        campaign._start_synthetic_parent_watch(123)
