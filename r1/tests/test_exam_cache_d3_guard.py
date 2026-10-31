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

@pytest.mark.parametrize('phase', ['b1', 'b2'])
def test_evidence_cli_stops_before_config_and_runner(phase, monkeypatch, tmp_path):
    from r1.scripts import exam_runner
    def unexpected(*args, **kwargs):
        raise AssertionError('must stop before config or runner')
    monkeypatch.setattr(exam_runner, 'load_config', unexpected)
    monkeypatch.setattr(exam_runner, 'ExamRunner', unexpected)
    with pytest.raises(PreparationStop, match='reviewed harness pin'):
        exam_runner.main([phase, '--out', str(tmp_path / 'never-created')])
    assert not (tmp_path / 'never-created').exists()

@pytest.mark.parametrize('phase', ['b1', 'b2'])
def test_evidence_start_stops_before_output(phase, tmp_path):
    from r1.exam.runtime import ExamRunner
    runner = object.__new__(ExamRunner)
    runner.out = tmp_path / 'never-created'
    with pytest.raises(PreparationStop, match='reviewed harness pin'):
        runner.start(phase)
    assert not runner.out.exists()

def test_campaign_worker_stops_before_job_access():
    from r1.exam.campaign import collect
    with pytest.raises(RuntimeError, match='reviewed harness pin'):
        collect({})


def test_direct_native_post_stops_before_instance_or_network(monkeypatch):
    class NoAccess:
        def __getattribute__(self,name): raise AssertionError('instance accessed')
    monkeypatch.setattr(worker, 'urlopen',lambda *a,**k:pytest.fail('network used'))
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        worker.post(NoAccess(),'/completion',{'cache_prompt':False})
