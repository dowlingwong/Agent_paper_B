"""Synthetic parent-to-worker B1 authority propagation; no model or server."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.exam.runtime import ExamRunner, PreparationStop


def runner(tmp_path, *, dryrun=False, head='a'*40):
    r=ExamRunner.__new__(ExamRunner)
    r.cfg={'workers':20,'host':'TASL-7','dryrun':dryrun,'W':20,'llm_call_cap':80,
           'audit_seeds':[9101,9102,9103,9104],'value_grids':'fixture','rule_sha256':'fixture'}
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


@pytest.mark.parametrize('saved_head,allowed',[('a'*40,True),('b'*40,False)])
def test_recovered_root_checks_authorized_head(tmp_path,monkeypatch,saved_head,allowed):
    import r1.exam.runtime as runtime
    r=runner(tmp_path)
    root=tmp_path/'fixture'/'b1'/'off'/'digits_mlp__s9001';root.mkdir(parents=True)
    manifest=root/'campaign_manifest.json';manifest.write_text('{}')
    (root/'job.json').write_text(json.dumps({'authorization_checkout_head':saved_head}))
    (root/'post_check.json').write_text('{}')
    r.state['in_progress']={'path':str(root)}
    monkeypatch.setattr(runtime,'verify_campaign',lambda path,binding:{'status':'COMPLETE'})
    if allowed:
        assert r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')['status']=='COMPLETE'
    else:
        with pytest.raises(PreparationStop,match='HEAD mismatch'):
            r.root({'id':'fixture'},'b1','digits_mlp',9001,'off')


@pytest.mark.parametrize('in_progress',[False,True])
def test_start_rejects_old_authority_before_resume_side_effects(tmp_path,monkeypatch,in_progress):
    import r1.exam.runtime as runtime
    r=runner(tmp_path);r.rule_sha='rule';r.registry_path=tmp_path/'registry';r.registry_path.write_text('{}')
    old=tmp_path/'old';old.mkdir();manifest=old/'campaign_manifest.json';manifest.write_text('{}')
    (old/'job.json').write_text(json.dumps({'authorization_checkout_head':'b'*40}))
    (old/'post_check.json').write_text('{}')
    state={'binding':r.binding,'phase':'b1','completed':{},'status':'RUNNING'}
    if in_progress: state['in_progress']={'path':str(old)}
    else:
        state['completed']['old']={'path':str(manifest),'sha256':runtime.digest_file(manifest),
                                   'post_check_sha256':runtime.digest_file(old/'post_check.json')}
    (tmp_path/'batch_state.json').write_text(json.dumps(state))
    monkeypatch.setattr(runtime,'author_gate',lambda *a:'a'*40)
    monkeypatch.setattr(runtime,'verify_campaign',lambda *a:{'status':'COMPLETE'})
    with pytest.raises(PreparationStop,match='HEAD mismatch'): r.start('b1')
    assert not (tmp_path/'runner.lock').exists()
