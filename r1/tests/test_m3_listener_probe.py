"""Synthetic-only unit tests: never fork, install seccomp or contact a host."""
import json
import os
from pathlib import Path
import select
import signal

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


def _mock_parent_probe(monkeypatch):
    """Simulate the parent after fork; no process, socket or kernel operation."""
    actions = []
    monkeypatch.setattr(probe.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(probe.platform, 'machine', lambda: 'x86_64')
    original_iterdir = Path.iterdir
    monkeypatch.setattr(Path, 'iterdir', lambda p: iter([Path('/fake/thread')])
                        if str(p) == '/proc/self/task' else original_iterdir(p))
    monkeypatch.setattr(probe.signal, 'getsignal', lambda _: signal.SIG_DFL)
    class Channel:
        def __init__(self, name): self.name = name
        def close(self): actions.append(('channel_close', self.name))
        def settimeout(self, value): actions.append(('timeout', value))
    monkeypatch.setattr(probe.socket, 'socketpair', lambda *a: (Channel('parent'), Channel('child')))
    monkeypatch.setattr(probe.os, 'fork', lambda: 77)
    monkeypatch.setattr(probe.os, 'pidfd_open', lambda *a: 88, raising=False)
    monkeypatch.setattr(probe.os, 'P_PIDFD', 3, raising=False)
    monkeypatch.setattr(probe.os, 'WNOWAIT', 0x01000000, raising=False)
    monkeypatch.setattr(probe.os, 'waitid', lambda *a: None, raising=False)
    monkeypatch.setattr(probe.os, 'kill', lambda *a: pytest.fail('numeric PID signal is forbidden'))
    monkeypatch.setattr(probe.signal, 'pidfd_send_signal', lambda *a: actions.append(('pidfd_signal', a[0])), raising=False)
    monkeypatch.setattr(probe.os, 'waitpid', lambda pid, flags: actions.append(('waitpid', pid, flags)) or (pid, 0))
    real_close = os.close
    monkeypatch.setattr(probe.os, 'close', lambda fd: actions.append(('close_fd', fd)) if fd in (88, 99) else real_close(fd))
    return actions


def test_ignored_sigchld_refused_before_fork(monkeypatch):
    _mock_parent_probe(monkeypatch)
    monkeypatch.setattr(probe.signal, 'getsignal', lambda _: signal.SIG_IGN)
    monkeypatch.setattr(probe.os, 'fork', lambda: pytest.fail('must not fork'))
    with pytest.raises(RuntimeError, match='default SIGCHLD'):
        probe.observe('normal_exit')


def test_pidfd_acquisition_failure_never_signals_numeric_pid(monkeypatch):
    actions = _mock_parent_probe(monkeypatch)
    monkeypatch.setattr(probe.os, 'pidfd_open', lambda *a: (_ for _ in ()).throw(OSError('fixture')))
    with pytest.raises(probe.ProbeCleanupError, match='identity not verified; no signal'):
        probe.observe('normal_exit')
    assert ('waitpid', 77, os.WNOHANG) in actions
    assert not any(a[0] == 'pidfd_signal' for a in actions)


def test_unverified_pidfd_never_signals_and_still_closes(monkeypatch):
    actions = _mock_parent_probe(monkeypatch)
    monkeypatch.setattr(probe.os, 'waitid', lambda *a: (_ for _ in ()).throw(ChildProcessError()), raising=False)
    with pytest.raises(probe.ProbeCleanupError, match='identity not verified; no signal'):
        probe.observe('normal_exit')
    assert ('close_fd', 88) in actions and ('waitpid', 77, os.WNOHANG) in actions
    assert not any(a[0] == 'pidfd_signal' for a in actions)


def test_signal_error_still_reaps_and_closes_all_descriptors(monkeypatch):
    actions = _mock_parent_probe(monkeypatch)
    monkeypatch.setattr(probe.seccomp, 'receive_listener', lambda _: 99)
    monkeypatch.setattr(probe.seccomp, 'verify_listener', lambda _: (_ for _ in ()).throw(RuntimeError('handoff')))
    monkeypatch.setattr(probe.signal, 'pidfd_send_signal',
                        lambda *a: (_ for _ in ()).throw(PermissionError('denied')), raising=False)
    with pytest.raises(probe.ProbeCleanupError, match='pidfd signal'):
        probe.observe('normal_exit')
    assert ('waitpid', 77, os.WNOHANG) in actions
    assert ('close_fd', 88) in actions and ('close_fd', 99) in actions


def test_reap_uses_nonblocking_wait_and_has_deadline(monkeypatch):
    values = iter([0, 1, 3])
    calls = []
    monkeypatch.setattr(probe.time, 'monotonic', lambda: next(values))
    monkeypatch.setattr(probe.time, 'sleep', lambda _: None)
    monkeypatch.setattr(probe.os, 'waitpid', lambda pid, flags: calls.append((pid, flags)) or (0, 0))
    assert probe._reap_bounded(77) == ('not_reaped_before_deadline', None)
    assert calls and all(flags == os.WNOHANG for _, flags in calls)


def test_unreaped_child_is_explicit_and_descriptors_close(monkeypatch):
    actions = _mock_parent_probe(monkeypatch)
    monkeypatch.setattr(probe.seccomp, 'receive_listener', lambda _: 99)
    monkeypatch.setattr(probe.seccomp, 'verify_listener', lambda _: (_ for _ in ()).throw(RuntimeError('handoff')))
    monkeypatch.setattr(probe, '_reap_bounded', lambda _: ('not_reaped_before_deadline', None))
    with pytest.raises(probe.ProbeCleanupError, match='pid=77.*not_reaped_before_deadline'):
        probe.observe('normal_exit')
    assert ('pidfd_signal', 88) in actions
    assert ('close_fd', 88) in actions and ('close_fd', 99) in actions
