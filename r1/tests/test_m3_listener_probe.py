"""Synthetic-only unit tests: never fork, install seccomp or contact a host."""
import json
import os
from pathlib import Path
import select

import pytest

from r1.c3 import offline_listener_probe as probe


def private(tmp_path):
    path = tmp_path.resolve() / 'private'
    path.mkdir(mode=0o700)
    return path


def test_event_names_preserve_combined_bits():
    assert probe.event_names(select.POLLIN | select.POLLHUP) == ['POLLIN', 'POLLHUP']
    assert probe.event_names(0) == []


def test_non_linux_refuses_before_fork(monkeypatch):
    monkeypatch.setattr(probe.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(probe.os, 'fork', lambda: pytest.fail('must not fork'))
    with pytest.raises(RuntimeError, match='Linux x86-64'):
        probe.observe('normal_exit')


def test_unknown_scenario_refused_before_platform_or_fork(monkeypatch):
    monkeypatch.setattr(probe.os, 'fork', lambda: pytest.fail('must not fork'))
    with pytest.raises(ValueError, match='fixed scenario'):
        probe.observe('arbitrary-command')


def test_main_records_only_fixed_synthetic_results(tmp_path, monkeypatch):
    out = private(tmp_path) / 'result.json'
    calls = []
    monkeypatch.setattr(probe, 'observe', lambda s: calls.append(s) or {'scenario': s, 'events': []})
    assert probe.main(['--out', str(out)]) == 0
    data = json.loads(out.read_text())
    assert calls == list(probe.SCENARIOS)
    assert data['status'] == 'COMPLETE' and data['label'] == 'ENGINEERING_ONLY'
    assert data['scope'] == 'synthetic_listener_observation_not_replay_qualification'


def test_main_records_failure_and_stops_remaining_scenarios(tmp_path, monkeypatch):
    out = private(tmp_path) / 'result.json'
    calls = []
    def fail(s):
        calls.append(s)
        raise TimeoutError('synthetic fixture')
    monkeypatch.setattr(probe, 'observe', fail)
    assert probe.main(['--out', str(out)]) == 2
    data = json.loads(out.read_text())
    assert calls == ['normal_exit'] and data['status'] == 'STOP'
    assert data['failure'] == {'scenario': 'normal_exit', 'type': 'TimeoutError', 'message': 'synthetic fixture'}


def test_main_never_overwrites_and_refuses_shared_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, 'observe', lambda _: pytest.fail('must not run'))
    root = private(tmp_path)
    existing = root / 'old'; existing.write_text('preserve')
    with pytest.raises(SystemExit):
        probe.main(['--out', str(existing)])
    assert existing.read_text() == 'preserve'
    root.chmod(0o755)
    with pytest.raises(SystemExit):
        probe.main(['--out', str(root / 'new')])
    assert not (root / 'new').exists()


def test_main_refuses_symlinked_output_parent(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, 'observe', lambda _: pytest.fail('must not run'))
    root = private(tmp_path)
    link = tmp_path.resolve() / 'alias'
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(SystemExit):
        probe.main(['--out', str(link / 'new')])
    assert not (root / 'new').exists()
