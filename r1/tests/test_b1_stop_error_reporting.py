"""Synthetic B1 STOP reporting; no processes, files or experiments."""
from types import SimpleNamespace
import pytest

from r1.exam import runtime
from r1.scripts import exam_runner


def test_failure_to_save_does_not_replace_original_stop(capsys):
    original = RuntimeError('GPU census lost')

    def fail_save():
        raise OSError(28, 'no space')

    runtime.report_b1_stop_and_save(SimpleNamespace(save=fail_save), original)
    err = capsys.readouterr().err
    assert 'RuntimeError: GPU census lost' in err
    assert 'state save failed: OSError: [Errno 28] no space' in err
    assert err.index('GPU census lost') < err.index('state save failed')


def test_b1_entry_reports_original_before_state_save_failure(monkeypatch, capsys):
    cfg = {'dryrun': False, 'authorizations': {'b1': 'synthetic'}, 'rule': 'synthetic',
           'rule_sha256': 'synthetic', 'stage_a_table': 'synthetic',
           'stage_a_table_sha256': 'synthetic', 'nodes': ['synthetic'],
           'llm_call_cap': 1, 'anchor_duplicate_reference': 'synthetic'}
    monkeypatch.setattr(exam_runner, 'load_config', lambda *a, **k: cfg)
    # Exercise STOP reporting after the separately tested committed-config gate.
    monkeypatch.setattr(exam_runner, 'require_committed_b1_config', lambda *a: 'a'*40)
    monkeypatch.setattr(exam_runner, 'placeholders', lambda *a: False)
    monkeypatch.setattr('r1.exam.analyze.load_rule', lambda *a: ({}, None))
    monkeypatch.setattr(exam_runner, 'is_v2', lambda *a: False)
    monkeypatch.setattr(exam_runner, 'verify_anchor_reference', lambda *a: None)
    class FakeRunner:
        def __init__(self, *args, **kwargs):
            self.state = {}; self.lock = object(); self.closed = False
        def start(self, phase):
            raise RuntimeError('original preflight failure')
        def save(self):
            raise OSError(28, 'no space')
        def close(self, *, preserve_running=False):
            self.closed = True
    monkeypatch.setattr(exam_runner, 'ExamRunner', FakeRunner)
    assert exam_runner.main(['b1', '--out', '/synthetic']) == 1
    err = capsys.readouterr().err
    assert 'RuntimeError: original preflight failure' in err
    assert 'state save failed: OSError: [Errno 28] no space' in err


def test_unavailable_stderr_and_state_do_not_escape(monkeypatch):
    class BrokenStderr:
        def write(self, value):
            raise OSError('stderr unavailable')
        def flush(self):
            raise OSError('stderr unavailable')
    def fail_save():
        raise OSError('state unavailable')
    monkeypatch.setattr(runtime.sys, 'stderr', BrokenStderr())
    runtime.report_b1_stop_and_save(SimpleNamespace(save=fail_save), RuntimeError('original'))


@pytest.mark.parametrize("has_lock", [False, True])
def test_b1_entry_with_broken_stderr_still_returns_failure(monkeypatch, has_lock):
    cfg = {'dryrun': False, 'authorizations': {'b1': 'synthetic'}, 'rule': 'synthetic',
           'rule_sha256': 'synthetic', 'stage_a_table': 'synthetic',
           'stage_a_table_sha256': 'synthetic', 'nodes': ['synthetic'],
           'llm_call_cap': 1, 'anchor_duplicate_reference': 'synthetic'}
    monkeypatch.setattr(exam_runner, 'load_config', lambda *a, **k: cfg)
    # Exercise STOP reporting after the separately tested committed-config gate.
    monkeypatch.setattr(exam_runner, 'require_committed_b1_config', lambda *a: 'a'*40)
    monkeypatch.setattr(exam_runner, 'placeholders', lambda *a: False)
    monkeypatch.setattr('r1.exam.analyze.load_rule', lambda *a: ({}, None))
    monkeypatch.setattr(exam_runner, 'is_v2', lambda *a: False)
    monkeypatch.setattr(exam_runner, 'verify_anchor_reference', lambda *a: None)
    class BrokenStderr:
        def write(self, value):
            raise OSError('stderr unavailable')
        def flush(self):
            raise OSError('stderr unavailable')
    class FakeRunner:
        def __init__(self, *args, **kwargs):
            self.state = {}; self.lock = object() if has_lock else None
        def start(self, phase):
            raise RuntimeError('original preflight failure')
        def save(self):
            if not has_lock:
                raise AssertionError('must not save without a lock')
            raise OSError('state unavailable')
        def close(self, *, preserve_running=False):
            pass
    monkeypatch.setattr(exam_runner, 'ExamRunner', FakeRunner)
    with monkeypatch.context() as ctx:
        ctx.setattr(runtime.sys, 'stderr', BrokenStderr())
        assert exam_runner.main(['b1', '--out', '/synthetic']) == 1


def test_base_exception_from_save_is_not_swallowed(capsys):
    def exit_save():
        raise SystemExit('save requested exit')
    with pytest.raises(SystemExit, match='save requested exit'):
        runtime.report_b1_stop_and_save(SimpleNamespace(save=exit_save), RuntimeError('original'))
    assert 'RuntimeError: original' in capsys.readouterr().err
