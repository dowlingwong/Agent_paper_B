"""Supervisor event-loop protocol: sentinel drain and HUP handling.

Real pipes and a socketpair stand in for the listener, the pidfd and the
sentinel channel (pipe readable = POLLIN, pipe writer closed = POLLHUP); the
drain, the pidfd wait, ``monitor_one`` and the cgroup are fakes. No process,
seccomp filter or cgroup is created.
"""
import os
import socket
import time
from types import SimpleNamespace

import pytest

from r1.c3 import offline_supervisor as sup


class Fds:
    def __init__(self, tmp_path):
        self.lr, self.lw = os.pipe()          # listener
        self.pr, self.pw = os.pipe()          # pidfd
        self.parent, self.child = socket.socketpair()
        self.audit = os.open(tmp_path / 'audit.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.audit_path = tmp_path / 'audit.jsonl'
        self.group = SimpleNamespace(kill_fd=None)

    def listener_hup(self):
        if self.lw is not None:
            os.close(self.lw)
            self.lw = None

    def listener_pollin(self):
        os.write(self.lw, b'x')

    def pid_exit(self):
        os.write(self.pw, b'x')

    def close(self):
        for fd in (self.lr, self.lw, self.pr, self.pw, self.audit):
            if fd is not None:
                os.close(fd)
        self.parent.close()
        self.child.close()


@pytest.fixture
def fds(tmp_path, monkeypatch):
    f = Fds(tmp_path)
    monkeypatch.setattr(sup, '_wait_empty', lambda group: None)
    yield f
    f.close()


def exited(status=0):
    return SimpleNamespace(si_code=os.CLD_EXITED, si_status=status)


def run(fds, *, drain, wait=None, seconds=5, hup_grace=0.3):
    state = {}
    try:
        return sup.monitor(fds.lr, fds.pr, fds.parent, fds.group, fds.audit,
                           time.monotonic() + seconds, state=state, drain=drain,
                           wait=wait or (lambda fd: exited()), hup_grace=hup_grace), state
    except sup.SupervisorStop as exc:
        exc.state = state
        raise


def test_clean_protocol_completes_only_after_drain_hup_and_exit(fds):
    calls = []

    def drain(listener, **k):
        calls.append('drain')
        return {'withdrawn': 0, 'pending': []}

    def wait(fd):
        calls.append('wait')
        return exited(0)
    fds.child.sendall(b'W\x00')
    # Simulate PID 1 exiting (filter released, bootstrap exits) once it gets D.
    real_sendall = fds.parent.sendall

    class Chan:
        def fileno(self):
            return fds.parent.fileno()

        def recv(self, n):
            return fds.parent.recv(n)

        def sendall(self, data):
            calls.append(('send', data))
            real_sendall(data)
            fds.listener_hup()
            fds.pid_exit()
    state = {}
    result = sup.monitor(fds.lr, fds.pr, Chan(), fds.group, fds.audit, time.monotonic() + 5,
                         state=state, drain=drain, wait=wait, hup_grace=0.3)
    assert result['status'] == 'COMPLETE_UNQUALIFIED' and state['waited'] is True
    assert calls == ['drain', ('send', b'D'), 'wait']
    assert fds.child.recv(1) == b'D'
    text = fds.audit_path.read_text()
    assert '"event": "withdrawn_drain"' in text and '"withdrawn": 0' in text
    assert text.index('withdrawn_drain') < text.index('process_tree_exited')


def test_hup_before_drain_is_stop(fds):
    fds.listener_hup()
    with pytest.raises(sup.SupervisorStop, match='hangup before sentinel drain'):
        run(fds, drain=lambda l, **k: pytest.fail('no drain after HUP'))


def test_pidfd_exit_before_drain_is_stop(fds):
    fds.pid_exit()
    with pytest.raises(sup.SupervisorStop, match='exited before sentinel drain'):
        run(fds, drain=lambda l, **k: pytest.fail('no drain'))


@pytest.mark.parametrize('result,pattern', [
    ({'withdrawn': 2, 'pending': []}, r'withdrawn before receipt \(withdrawn=2, pending=0\)'),
    ({'withdrawn': 0, 'pending': [{'syscall': 41}]}, r'withdrawn=0, pending=1'),
])
def test_drain_residue_or_pending_is_stop_without_release(fds, result, pattern):
    fds.child.sendall(b'W\x00')
    with pytest.raises(sup.SupervisorStop, match=pattern):
        run(fds, drain=lambda l, **k: result)
    fds.child.setblocking(False)
    with pytest.raises(BlockingIOError):
        fds.child.recv(1)          # 'D' was never sent: PID 1 stays and is killed
    assert '"event": "withdrawn_drain"' in fds.audit_path.read_text()


def test_received_notification_is_stop_before_anything_else(fds, monkeypatch):
    fds.listener_pollin()
    fds.child.sendall(b'W\x00')
    monkeypatch.setattr(sup.seccomp, 'monitor_one', lambda *a: {'syscall': 42})
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall 42'):
        run(fds, drain=lambda l, **k: pytest.fail('POLLIN wins over drain'))


def test_exit_without_hup_after_drain_is_stop(fds):
    fds.child.sendall(b'W\x00')

    def drain(listener, **k):
        fds.pid_exit()          # bootstrap exits, but the filter still has users
        return {'withdrawn': 0, 'pending': []}
    with pytest.raises(sup.SupervisorStop, match='filter users remain'):
        run(fds, drain=drain)


def test_notification_after_drain_is_stop(fds, monkeypatch):
    fds.child.sendall(b'W\x00')
    monkeypatch.setattr(sup.seccomp, 'monitor_one', lambda *a: {'syscall': 41})

    def drain(listener, **k):
        fds.listener_pollin()
        return {'withdrawn': 0, 'pending': []}
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall 41'):
        run(fds, drain=drain)


@pytest.mark.parametrize('message,status,pattern', [
    (b'W\x03', 0, 'workload failed'),
    (b'W\x00', 1, 'workload failed'),
])
def test_nonzero_status_is_stop_after_clean_drain(fds, message, status, pattern):
    fds.child.sendall(message)

    def drain(listener, **k):
        fds.listener_hup()
        fds.pid_exit()
        return {'withdrawn': 0, 'pending': []}
    with pytest.raises(sup.SupervisorStop, match=pattern) as info:
        run(fds, drain=drain, wait=lambda fd: exited(status))
    assert info.value.state['waited'] is True


def test_signalled_bootstrap_is_stop(fds):
    fds.child.sendall(b'W\x00')

    def drain(listener, **k):
        fds.listener_hup()
        fds.pid_exit()
        return {'withdrawn': 0, 'pending': []}
    with pytest.raises(sup.SupervisorStop, match='workload failed'):
        run(fds, drain=drain, wait=lambda fd: SimpleNamespace(si_code=os.CLD_KILLED, si_status=9))


def test_channel_eof_before_drain_is_stop(fds):
    fds.child.close()
    with pytest.raises(sup.SupervisorStop, match='channel'):
        run(fds, drain=lambda l, **k: pytest.fail('no drain'))


def test_invalid_sentinel_message_is_stop(fds):
    fds.child.sendall(b'X\x00')
    with pytest.raises(sup.SupervisorStop, match='invalid sentinel message'):
        run(fds, drain=lambda l, **k: pytest.fail('no drain'))


def test_pidfd_ready_without_reap_is_stop(fds):
    fds.child.sendall(b'W\x00')

    def drain(listener, **k):
        fds.listener_hup()
        fds.pid_exit()
        return {'withdrawn': 0, 'pending': []}
    with pytest.raises(sup.SupervisorStop, match='did not yield'):
        run(fds, drain=drain, wait=lambda fd: None)


def test_timeout_is_stop(fds):
    with pytest.raises(sup.SupervisorStop, match='workload timeout'):
        run(fds, drain=lambda l, **k: pytest.fail('no drain'), seconds=0.2)


# ---- poll-event branches, with a scripted poller (each was asserted by a removed
# fork-era parametrization; deleting the branch makes these tests fail)

class ScriptedPoll:
    def __init__(self, script):
        self.script = list(script)

    def register(self, *a):
        pass

    def unregister(self, *a):
        pass

    def poll(self, *a):
        return self.script.pop(0) if self.script else []


def run_scripted(fds, monkeypatch, batches, **kw):
    monkeypatch.setattr(sup.select, 'poll', lambda: ScriptedPoll(batches))
    return run(fds, drain=kw.pop('drain', lambda l, **k: pytest.fail('no drain')), seconds=0.5, **kw)


@pytest.mark.parametrize('mask', [sup.select.POLLERR, sup.select.POLLNVAL])
def test_listener_error_or_invalid_is_stop(fds, monkeypatch, mask):
    with pytest.raises(sup.SupervisorStop, match='listener error'):
        run_scripted(fds, monkeypatch, [[(fds.lr, mask)]])


@pytest.mark.parametrize('mask', [sup.select.POLLHUP, sup.select.POLLERR, sup.select.POLLNVAL,
                                  sup.select.POLLERR | sup.select.POLLIN])
def test_pidfd_error_hangup_or_invalid_is_stop(fds, monkeypatch, mask):
    with pytest.raises(sup.SupervisorStop, match='pidfd error or hangup'):
        run_scripted(fds, monkeypatch, [[(fds.pr, mask)]], wait=lambda fd: pytest.fail('no reap'))


def test_pending_notification_with_hangup_in_one_batch_goes_through_monitor_one(fds, monkeypatch):
    seen = []
    monkeypatch.setattr(sup.seccomp, 'monitor_one', lambda *a: seen.append(a) or {'syscall': 41})
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall 41'):
        run_scripted(fds, monkeypatch, [[(fds.lr, sup.select.POLLIN | sup.select.POLLHUP),
                                         (fds.pr, sup.select.POLLIN)]])
    assert len(seen) == 1
