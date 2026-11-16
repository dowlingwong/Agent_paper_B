"""Synthetic parent-to-worker B1 authority propagation; no model or server."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.exam.runtime import ExamRunner, PreparationStop


@pytest.fixture(autouse=True)
def fake_harness_sources(monkeypatch):
    monkeypatch.setattr('r1.exam.runtime.b1_harness_sources',lambda node,commit:{'train.py':'synthetic-sha'})


def runner(tmp_path, *, dryrun=False, head='a'*40):
    r=ExamRunner.__new__(ExamRunner)
    r.cfg={'workers':20,'host':'TASL-7','dryrun':dryrun,'W':20,'llm_call_cap':80,
           'audit_seeds':[9101,9102,9103,9104],'value_grids':'fixture','rule_sha256':'fixture','harness_commit':'fixture',
           'nodes':['digits_mlp']}
    r.author_head=head;r.rule={'version':'x5_rule/v2'};r.binding='fixture-binding'
    r.state={'completed':{}};r.out=tmp_path;r.service=None
    r.space=lambda:None;r.save=lambda:None;r.seen=[]
    def run_job(job,module,interrupt=False):
        r.seen.append(job)
        out=Path(job['out']);out.mkdir(parents=True)
        (out/'campaign_manifest.json').write_text(json.dumps({'status':'COMPLETE'}))
    r.run_job=run_job
    return r


def test_parent_passes_authorized_configuration_and_head(tmp_path):
    r=runner(tmp_path)
    r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')
    assert r.seen[0]['authority_config']==r.cfg
    assert r.seen[0]['authority_config'] is not r.cfg
    assert r.seen[0]['authorization_checkout_head']=='a'*40
    assert r.seen[0]['node_source_sha256']=={'train.py':'synthetic-sha'}


def test_worker_command_uses_runner_python_environment(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    (tmp_path/'python').write_text('fixture');(tmp_path/'python').chmod(0o700);(tmp_path/'python3').symlink_to(tmp_path/'python')
    monkeypatch.setattr(runtime.sys,'executable',str(tmp_path/'python'))
    env=runtime.worker_environment({'PATH':'/usr/bin','TOKEN':'fixture'})
    assert env['PATH']==str(tmp_path)+':/usr/bin'
    assert env['TOKEN']=='fixture' and env['OMP_NUM_THREADS']=='1'


def test_worker_refuses_a_different_or_absent_python3(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    (tmp_path/'python').write_text('fixture')
    monkeypatch.setattr(runtime.sys,'executable',str(tmp_path/'python'))
    with pytest.raises(PreparationStop,match='worker python3'): runtime.worker_environment({'PATH':'/usr/bin'})
    (tmp_path/'python3').write_text('different')
    with pytest.raises(PreparationStop,match='worker python3'): runtime.worker_environment({'PATH':'/usr/bin'})


def test_worker_refuses_non_executable_python_even_when_same_file(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    venv=tmp_path/'venv';venv.mkdir();fallback=tmp_path/'fallback';fallback.mkdir()
    (venv/'python').write_text('fixture');(venv/'python').chmod(0o600)
    (venv/'python3').symlink_to(venv/'python')
    marker=tmp_path/'fallback-executed'
    (fallback/'python3').write_text('#!/bin/sh\nprintf wrong > "$1"\n');(fallback/'python3').chmod(0o700)
    monkeypatch.setattr(runtime.sys,'executable',str(venv/'python'))
    with pytest.raises(PreparationStop,match='worker python3'):
        env=runtime.worker_environment({'PATH':str(fallback)})
        runtime.subprocess.run(['python3',str(marker)],env=env,check=True)
    assert not marker.exists()


def test_parent_refuses_missing_head_before_worker(tmp_path):
    r=runner(tmp_path,head=None)
    with pytest.raises(PreparationStop,match='authorized checkout HEAD'):
        r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')
    assert not r.seen


def test_completed_root_cannot_be_reused_under_different_head(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    r=runner(tmp_path)
    path=tmp_path/'saved'/'campaign_manifest.json';path.parent.mkdir()
    path.write_text('{}')
    (path.parent/'job.json').write_text(json.dumps({'authorization_checkout_head':'b'*40}))
    r.state['completed']['fixture/b1/off/digits_mlp__s9001']={'path':str(path)}
    monkeypatch.setattr(runtime,'verify_campaign',lambda path,binding:{'status':'COMPLETE'})
    with pytest.raises(PreparationStop,match='HEAD mismatch'):
        r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')


def test_completed_root_same_head_is_reused(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    r=runner(tmp_path)
    path=tmp_path/'saved'/'campaign_manifest.json';path.parent.mkdir()
    path.write_text('{}');(path.parent/'job.json').write_text(json.dumps({'authorization_checkout_head':'a'*40}))
    r.state['completed']['fixture/b1/off/digits_mlp__s9001']={'path':str(path)}
    monkeypatch.setattr(runtime,'verify_campaign',lambda path,binding:{'status':'COMPLETE'})
    assert r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')['status']=='COMPLETE'
    assert not r.seen


@pytest.mark.parametrize('saved_head',['a'*40,'b'*40])
def test_existing_production_root_stops_without_recovery_or_mutation(tmp_path,monkeypatch,saved_head):
    import r1.exam.runtime as runtime
    r=runner(tmp_path)
    root=tmp_path/'fixture'/'b1'/'off'/'digits_mlp__s9001';root.mkdir(parents=True)
    manifest=root/'campaign_manifest.json';manifest.write_text('{}')
    job=root/'job.json';job.write_text(json.dumps({'authorization_checkout_head':saved_head}))
    post=root/'post_check.json';post.write_text('{}')
    before={path:path.read_bytes() for path in (manifest,job,post)}
    r.state['in_progress']={'path':str(root)}
    def fail_verification(*args,**kwargs):
        pytest.fail('existing production root must not be recovered')
    monkeypatch.setattr(runtime,'verify_campaign',fail_verification)
    with pytest.raises(PreparationStop,match='existing B1 root is preserved; no automatic recovery'):
        r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')
    assert {path:path.read_bytes() for path in before}==before
    assert r.state['in_progress']=={'path':str(root)} and not r.state['completed']
    assert not r.seen and not (tmp_path/'interrupted').exists()


@pytest.mark.parametrize('in_progress',[False,True])
def test_start_refuses_existing_batch_before_resume_side_effects(tmp_path,monkeypatch,in_progress):
    import r1.exam.runtime as runtime
    import r1.exam.b1_lease as lease
    r=runner(tmp_path);r.cfg['work_dir']=str(tmp_path.parent)
    r.rule_sha='rule';r.registry_path=tmp_path/'registry';r.registry_path.write_text('{}')
    old=tmp_path/'old';old.mkdir();manifest=old/'campaign_manifest.json';manifest.write_text('{}')
    job=old/'job.json';job.write_text(json.dumps({'authorization_checkout_head':'b'*40}))
    post=old/'post_check.json';post.write_text('{}')
    state={'binding':r.binding,'phase':'b1','completed':{},'status':'RUNNING'}
    if in_progress: state['in_progress']={'path':str(old)}
    else:
        state['completed']['old']={'path':str(manifest),'sha256':runtime.digest_file(manifest),
                                   'post_check_sha256':runtime.digest_file(post)}
    state_file=tmp_path/'batch_state.json';state_file.write_text(json.dumps(state))
    before={path:path.read_bytes() for path in (r.registry_path,manifest,job,post,state_file)}
    r.b1_config_head='a'*40;r.registry={}
    monkeypatch.setattr(runtime,'require_committed_b1_config',lambda *a:'a'*40)
    monkeypatch.setattr(runtime,'require_committed_b1_registry',lambda *a,**k:None)
    monkeypatch.setattr(runtime,'author_gate',lambda *a:'a'*40)
    monkeypatch.setattr(runtime,'worker_environment',lambda *a:{})
    def fail_side_effect(*args,**kwargs):
        pytest.fail('must stop before recovery, lease or runner lock')
    monkeypatch.setattr(runtime,'verify_campaign',fail_side_effect)
    monkeypatch.setattr(runtime,'claim_runner_lock',fail_side_effect)
    monkeypatch.setattr(lease,'acquire',fail_side_effect)
    with pytest.raises(PreparationStop,match='B1 batch already exists; no automatic resume'):
        r.start('b1')
    assert {path:path.read_bytes() for path in before}==before
    assert not (tmp_path/'runner.lock').exists() and not (tmp_path/'registry_snapshot.yaml').exists()
    assert not r.seen


def test_stopped_b1_state_is_preserved_without_resuming(tmp_path,monkeypatch):
    import r1.exam.runtime as runtime
    r=runner(tmp_path,dryrun=True);r.rule_sha='rule'
    state=tmp_path/'batch_state.json';original=b'{"status":"STOPPED","stop_reason":"synthetic interruption"}\n'
    state.write_bytes(original)
    monkeypatch.setattr(runtime,'author_gate',lambda *a:None)
    with pytest.raises(PreparationStop,match='stopped batch must not be resumed'):
        r.start('b1')
    assert state.read_bytes()==original and not (tmp_path/'runner.lock').exists()
