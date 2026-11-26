"""D3 must fail closed until cold-server evidence is implemented."""
from types import SimpleNamespace
import pytest
from r1.exam.runtime import PreparationStop
from r1.exam import stage_a as worker
from r1.scripts.exam_runner import stage_a

@pytest.mark.parametrize('setting', [None, True, False])
def test_runner_cannot_start_incomplete_d3(setting):
    runner = SimpleNamespace(cfg={'cache_prompt': setting})
    with pytest.raises(PreparationStop, match='STOP:'):
        stage_a(runner, None)

def test_direct_worker_cannot_bypass_guard():
    with pytest.raises(RuntimeError, match='D3 cold-cache'):
        worker.main([])

@pytest.mark.parametrize('entry', ['fit_prefill', 'run_stage_a'])
def test_direct_generation_entries_cannot_bypass_guard(entry):
    class NoAccess:
        def __getattribute__(self, name):
            raise AssertionError('instance must not be accessed')
    inst = NoAccess()
    with pytest.raises(RuntimeError, match='D3 cold-cache'):
        if entry == 'fit_prefill':
            worker.fit_prefill(inst)
        else:
            worker.run_stage_a(inst, {}, [], gpu_sample=None, schema_format=None)

def test_cli_stops_before_config_or_runner(monkeypatch, tmp_path):
    from r1.scripts import exam_runner
    def unexpected(*args, **kwargs):
        raise AssertionError('must stop before config or runner')
    monkeypatch.setattr(exam_runner, 'load_config', unexpected)
    monkeypatch.setattr(exam_runner, 'ExamRunner', unexpected)
    with pytest.raises(PreparationStop, match='D3 cold-cache'):
        exam_runner.main(['stage-a', '--out', str(tmp_path / 'never-created')])
    assert not (tmp_path / 'never-created').exists()

def test_runner_start_stage_a_requires_authorized_d3_context(tmp_path):
    from r1.exam.runtime import ExamRunner
    runner = object.__new__(ExamRunner)
    runner.out = tmp_path / 'never-created'
    # B1 fix: Stage A dispatch is enabled but refuses an unauthorized context
    # before any output is created.
    with pytest.raises(RuntimeError, match='D3 cold-cache cooperative Stage A context not authorized'):
        runner.start('stage-a')
    assert not runner.out.exists()

def test_b2_cli_refuses_missing_active_note_before_runner(monkeypatch, tmp_path):
    # B2 code unit (14 Nov 2026): B2 is no longer refused outright; like B1 it stops before any runner or output
    # while its committed config or authorization note is unresolved.
    from r1.scripts import exam_runner
    monkeypatch.setattr(exam_runner,'load_config',lambda *a,**k:{'authorizations':{'b2':'TODO_AUTHOR_NOTE'}})
    seen=[]
    monkeypatch.setattr(exam_runner,'require_committed_b1_config',lambda *a,**k:seen.append(k.get('rel')) or 'a'*40)
    monkeypatch.setattr(exam_runner,'ExamRunner',lambda *a,**k:pytest.fail('runner must not start'))
    with pytest.raises(PreparationStop, match='authorization note is unresolved'):
        exam_runner.main(['b2', '--out', str(tmp_path / 'never-created')])
    assert seen==['r1/scripts/configs/exam_b2_v2.json']
    assert not (tmp_path / 'never-created').exists()

def test_b1_cli_refuses_missing_active_note_before_runner(monkeypatch,tmp_path):
    from r1.scripts import exam_runner
    monkeypatch.setattr(exam_runner,'load_config',lambda *a,**k:{'authorizations':{'b1':'TODO_AUTHOR_NOTE'}})
    monkeypatch.setattr(exam_runner,'require_committed_b1_config',lambda *a:'a'*40)
    monkeypatch.setattr(exam_runner,'ExamRunner',lambda *a,**k:pytest.fail('runner must not start'))
    with pytest.raises(PreparationStop,match='authorization note is unresolved'):
        exam_runner.main(['b1','--out',str(tmp_path/'never-created')])
    assert not (tmp_path/'never-created').exists()

def test_b2_start_stops_before_output(tmp_path, monkeypatch):
    # B2 code unit: an unreviewed rule or a refused author gate stops B2 before any output, as for B1.
    from r1.exam import runtime
    runner = object.__new__(runtime.ExamRunner)
    runner.out = tmp_path / 'never-created'
    runner.rule={'version':'x5_rule/v1'};runner.cfg={}
    with pytest.raises(PreparationStop, match='B2 requires the reviewed x5_rule/v2'):
        runner.start('b2')
    runner.rule={'version':'x5_rule/v2'};runner.rule_sha='synthetic'
    runner.b1_config_head='a'*40;runner.registry_path=None;runner.registry=None
    monkeypatch.setattr(runtime,'require_committed_b1_config',lambda *a,**k:'a'*40)
    monkeypatch.setattr(runtime,'require_committed_b1_registry',lambda *a,**k:None)
    def refused(*args): raise runtime.PreparationStop('STOP: synthetic authorization refused')
    monkeypatch.setattr(runtime,'author_gate',refused)
    with pytest.raises(PreparationStop,match='authorization refused'): runner.start('b2')
    assert not runner.out.exists()

def test_b1_unauthorized_start_stops_before_output(tmp_path,monkeypatch):
    from r1.exam import runtime
    runner=object.__new__(runtime.ExamRunner);runner.out=tmp_path/'never-created'
    runner.rule={'version':'x5_rule/v2'};runner.rule_sha='synthetic';runner.cfg={}
    runner.b1_config_head='a'*40;runner.registry_path=None;runner.registry=None
    monkeypatch.setattr(runtime,'require_committed_b1_config',lambda *a:'a'*40)
    monkeypatch.setattr(runtime,'require_committed_b1_registry',lambda *a,**k:None)
    def refused(*args): raise runtime.PreparationStop('STOP: synthetic authorization refused')
    monkeypatch.setattr(runtime,'author_gate',refused)
    with pytest.raises(PreparationStop,match='authorization refused'): runner.start('b1')
    assert not runner.out.exists()

def test_campaign_worker_stops_before_job_access():
    from r1.exam.campaign import collect
    with pytest.raises(RuntimeError, match='only the reviewed B1/B2 collector'):
        collect({})


def test_direct_native_post_stops_before_instance_or_network(monkeypatch):
    class NoAccess:
        def __getattribute__(self,name): raise AssertionError('instance accessed')
    monkeypatch.setattr(worker, 'urlopen',lambda *a,**k:pytest.fail('network used'))
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        worker.post(NoAccess(),'/completion',{'cache_prompt':False})
