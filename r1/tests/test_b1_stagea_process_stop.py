"""B1 STOP uses the existing owned-process path and retains shutdown notes."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from r1.exam import analyze, runtime
from r1.scripts import exam_runner


def test_b1_stop_stops_owned_server_and_records_shutdown(monkeypatch, capsys):
    cfg = {'dryrun': False, 'authorizations': {'b1': 'approved.json'},
           'stage_a_table': 'table', 'stage_a_table_sha256': 'digest',
           'nodes': ['digits_mlp'], 'llm_call_cap': 80,
           'anchor_duplicate_reference': {'source': 'ref'}, 'rule': 'rule', 'rule_sha256': 'sha'}
    runner = SimpleNamespace(state={}, service=object(), lock=object(), b1_shutdown_attempted=False)
    runner.start = lambda phase: runner.state.update(phase=phase, status='RUNNING')
    def stop():
        runner.b1_shutdown_attempted = True
        runner.service = None
    runner.stop_service = Mock(side_effect=stop)
    runner.save = Mock()
    runner.close = Mock()
    monkeypatch.setattr(exam_runner, 'load_config', lambda *a, **k: cfg)
    monkeypatch.setattr(exam_runner, 'require_committed_b1_config', lambda *a: 'a'*40)
    monkeypatch.setattr(exam_runner, 'placeholders', lambda *a: [])
    monkeypatch.setattr(analyze, 'load_rule', lambda *a: ({'version': 'x5_rule/v1'}, 'sha'))
    monkeypatch.setattr(exam_runner, 'is_v2', lambda *a: False)
    monkeypatch.setattr(exam_runner, 'verify_anchor_reference', lambda *a: None)
    monkeypatch.setattr(exam_runner, 'ExamRunner', lambda *a, **k: runner)
    monkeypatch.setattr(exam_runner, 'evidence', Mock(side_effect=RuntimeError('original failure')))
    assert exam_runner.main(['b1','--out','/synthetic']) == 1
    runner.stop_service.assert_called_once()
    runner.close.assert_called_once_with(skip_service=True)
    assert runner.state['status'] == 'STOPPED'
    assert 'original failure' in runner.state['stop_reason']
    assert 'shutdown' in runner.state['shutdown_writes'].lower() or 'stopping' in runner.state['shutdown_writes'].lower()
    assert 'runner/server logs' in capsys.readouterr().err


def test_existing_production_batch_is_not_reused(tmp_path, monkeypatch):
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': False, 'work_dir': str(tmp_path), 'nodes': []}
    runner.out = tmp_path / 'existing'
    runner.out.mkdir()
    runner.rule = {'version': 'x5_rule/v2'}
    runner.rule_sha = 'sha'
    runner.registry_path = tmp_path / 'registry'
    runner.registry = {}
    runner.b1_config_head = 'a'*40
    monkeypatch.setattr(runtime, 'require_committed_b1_config', lambda *a: 'a'*40)
    monkeypatch.setattr(runtime, 'require_committed_b1_registry', lambda *a, **k: None)
    monkeypatch.setattr(runtime, 'author_gate', lambda *a: 'a'*40)
    monkeypatch.setattr(runtime, 'worker_environment', lambda *a: {})
    with pytest.raises(runtime.PreparationStop, match='no automatic resume'):
        runner.start('b1')


def test_post_spawn_save_failure_stops_owned_child(tmp_path, monkeypatch):
    child = Mock(pid=1234, returncode=None)
    child.poll.side_effect = [None]
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': False, 'watchdog': {}}
    runner.state = {'phase': 'b1', 'interruptions': []}
    runner.service = None
    runner.b1_lease_fd = 8
    runner.space = Mock()
    runner.save = Mock(side_effect=RuntimeError('state save failed'))
    monkeypatch.setattr(runtime, 'worker_environment', lambda: {})
    monkeypatch.setattr(runtime, 'write_json', lambda *a: None)
    monkeypatch.setattr(runtime.subprocess, 'Popen', lambda *a, **k: child)
    stop = Mock()
    monkeypatch.setattr(runtime, 'stop_tree', stop)
    monkeypatch.setattr(runtime, 'report_b1_stop_and_save', Mock())
    with pytest.raises(RuntimeError, match='state save failed'):
        runner.run_job({'out': str(tmp_path / 'job')}, 'r1.exam.campaign')
    stop.assert_called_once_with(1234)
    child.wait.assert_called_once_with(timeout=30)
    assert 'state save failed' in runner.state['interruptions'][0]['error']


def test_audit_notification_uses_existing_owned_process_stop(tmp_path, monkeypatch):
    child = Mock(pid=1234, returncode=None)
    child.poll.return_value = None
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': False, 'watchdog': {}}
    runner.state = {'phase': 'b1', 'interruptions': []}
    runner.service = None
    runner.b1_lease_fd = 8
    runner.space = Mock()
    runner.save = Mock()
    monkeypatch.setattr(runtime, 'worker_environment', lambda: {})
    monkeypatch.setattr(runtime, 'write_json', lambda *a: None)
    monkeypatch.setattr(runtime.subprocess, 'Popen', lambda *a, **k: child)
    monkeypatch.setattr(runtime.os, 'read', lambda fd, count: b'1')
    stop = Mock()
    monkeypatch.setattr(runtime, 'stop_tree', stop)
    monkeypatch.setattr(runtime, 'report_b1_stop_and_save', Mock())
    with pytest.raises(RuntimeError, match='audit worker failure'):
        runner.run_job({'out': str(tmp_path / 'job')}, 'r1.exam.campaign')
    stop.assert_called_once_with(1234)
    child.wait.assert_called_once_with(timeout=30)
