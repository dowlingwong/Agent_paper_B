"""Withdrawn seccomp notification: drain protocol tests.

Unit tests use a fake receive call. The kernel tests (opt-in,
``AR_M3_KERNEL_TESTS=1``, Linux x86-64, seccomp user notification available)
build the swallowed-interruption counterexample required by
MAC_M3_WITHDRAWN_RECHECK_REVIEW_20261108.md on the *local* kernel: a workload
whose prohibited call is interrupted before the supervisor receives it and who
swallows EINTR. They are not a target-host qualification. No network is used:
the prohibited call is ``socket(AF_UNIX)``, which the filter suspends before
the kernel executes it.
"""
import ctypes
import errno
import os
import platform
import select
import signal
import socket
import struct
import time

import pytest

from r1.c3 import offline_seccomp as seccomp

KERNEL = os.environ.get('AR_M3_KERNEL_TESTS') == '1'
kernel_only = pytest.mark.skipif(
    not KERNEL or platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'),
    reason='set AR_M3_KERNEL_TESTS=1 on Linux x86-64 to run real seccomp tests')


def fake_recv(outcomes):
    calls = []

    def recv(fd, buffer):
        calls.append(fd)
        kind = outcomes.pop(0)
        if kind == 'notif':
            struct.pack_into('=QIIiI', buffer, 0, 7, 99, 0, 41, seccomp.AUDIT_ARCH_X86_64)
            return 0, 0
        return -1, kind
    return recv, calls


def test_drain_counts_each_enoent_as_withdrawn_until_eintr():
    recv, calls = fake_recv([errno.ENOENT, errno.ENOENT, errno.EINTR])
    assert seccomp.drain_withdrawn(5, recv=recv) == {'withdrawn': 2, 'pending': []}
    assert calls == [5, 5, 5]


def test_drain_clean_only_on_eintr():
    recv, _ = fake_recv([errno.EINTR])
    assert seccomp.drain_withdrawn(5, recv=recv) == {'withdrawn': 0, 'pending': []}


def test_drain_reports_pending_notification_as_violation():
    recv, _ = fake_recv(['notif', errno.EINTR])
    result = seccomp.drain_withdrawn(5, recv=recv)
    assert result['withdrawn'] == 0
    assert result['pending'][0]['syscall'] == 41 and result['pending'][0]['decision'] == 'STOP'


@pytest.mark.parametrize('err', [errno.EBADF, errno.ENOTTY, errno.EFAULT, errno.EINVAL])
def test_drain_unexpected_error_is_stop(err):
    recv, _ = fake_recv([err])
    with pytest.raises(seccomp.DrainStop, match='drain failed'):
        seccomp.drain_withdrawn(5, recv=recv)


def test_drain_is_bounded_and_restores_timer_and_handler():
    sentinel = lambda *_: None
    previous = signal.signal(signal.SIGALRM, sentinel)
    try:
        recv, _ = fake_recv([errno.ENOENT] * 3)
        with pytest.raises(seccomp.DrainStop, match='did not terminate'):
            seccomp.drain_withdrawn(5, recv=recv, max_iterations=3)
        assert signal.getsignal(signal.SIGALRM) is sentinel
        assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
    finally:
        signal.signal(signal.SIGALRM, previous)


def test_drain_refuses_invalid_listener():
    with pytest.raises(seccomp.DrainStop, match='invalid listener'):
        seccomp.drain_withdrawn(-1, recv=lambda *a: pytest.fail('no receive'))


# --------------------------------------------------------------- real kernel

def _workload(mode):
    """Grandchild under the inherited filter. Swallows every error."""
    libc = ctypes.CDLL(None, use_errno=True)
    if mode == 'withdraw':
        signal.signal(signal.SIGALRM, lambda *_: None)
        signal.siginterrupt(signal.SIGALRM, True)   # handler without SA_RESTART
        signal.setitimer(signal.ITIMER_REAL, 0.3)
        libc.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)  # suspended, then EINTR
        signal.setitimer(signal.ITIMER_REAL, 0)
    os._exit(0)


def _sentinel(channel, mode):
    """Child: install the real M3 filter, hand off listener, act as PID-1 sentinel."""
    try:
        listener = seccomp.install_listener(channel.fileno())
        seccomp.send_listener(channel, listener)
        os.close(listener)
        pid = os.fork()
        if pid == 0:
            _workload(mode)
        while True:
            try:
                os.waitpid(-1, 0)
            except ChildProcessError:
                break
        os.write(channel.fileno(), b'W')
        os.read(channel.fileno(), 1)   # wait for the supervisor's drain verdict
    finally:
        os._exit(0)


def _run(mode):
    parent, child = socket.socketpair()
    pid = os.fork()
    if pid == 0:
        parent.close()
        _sentinel(child, mode)
    child.close()
    try:
        parent.settimeout(10)
        listener = seccomp.receive_listener(parent)
        assert parent.recv(1) == b'W'           # workload tree reaped, sentinel alive
        poller = select.poll()
        poller.register(listener, select.POLLIN | select.POLLHUP)
        before = poller.poll(0)
        drained = seccomp.drain_withdrawn(listener)
        parent.sendall(b'D')
        os.waitpid(pid, 0)
        after = poller.poll(1000)
        return before, drained, after, listener
    finally:
        parent.close()


@kernel_only
def test_kernel_swallowed_interruption_is_invisible_to_poll_but_found_by_drain():
    before, drained, after, listener = _run('withdraw')
    try:
        # The old monitor only reacts to POLLIN: there is nothing to see.
        assert not any(mask & select.POLLIN for _, mask in before)
        assert drained == {'withdrawn': 1, 'pending': []}
        assert any(mask & select.POLLHUP for _, mask in after)
    finally:
        os.close(listener)


@kernel_only
def test_kernel_clean_workload_drains_to_zero():
    before, drained, after, listener = _run('clean')
    try:
        assert before == []
        assert drained == {'withdrawn': 0, 'pending': []}
        assert any(mask & select.POLLHUP for _, mask in after)
        # Negative control for the sentinel requirement: once the last filter
        # user is gone (HUP), v6.6+ kernels answer ENOENT at once even with no
        # residue, so a drain after HUP cannot tell the two histories apart.
        release = tuple(int(x) for x in platform.release().split('.')[:2])
        if release >= (6, 6):
            rc, err = seccomp._libc_recv(listener, ctypes.create_string_buffer(seccomp.NOTIF_SIZE))
            assert (rc, err) == (-1, errno.ENOENT)
    finally:
        os.close(listener)
