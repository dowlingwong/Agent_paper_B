"""clone3 launcher and PID-1 sentinel bootstrap tests.

Unit tests fake the raw system call, /proc and process calls. The kernel test
(opt-in: AR_M3_KERNEL_TESTS=1 and AR_M3_DELEGATED_CGROUP) really clones a
``/bin/sh`` child into a fresh private cgroup on the local kernel; it is not a
target-host qualification.
"""
import ctypes
import errno
import hashlib
import os
from pathlib import Path
import platform
import select
import signal
import socket
from types import SimpleNamespace

import pytest

from r1.c3 import offline_bootstrap as boot
from r1.c3 import offline_cgroup as groups
from r1.c3 import offline_launcher as launcher


@pytest.fixture
def linux(monkeypatch):
    monkeypatch.setattr(launcher.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(launcher.platform, 'machine', lambda: 'x86_64')
    original = Path.iterdir
    monkeypatch.setattr(Path, 'iterdir', lambda p: iter([Path('/t/1')]) if str(p) == '/proc/self/task' else original(p))
    monkeypatch.setattr(launcher.identity, '_kernel_sigchld_action', lambda: (0, 0))


def test_clone_args_layout_matches_uapi_ver2():
    assert ctypes.sizeof(launcher.CloneArgs) == 88
    offsets = {name: getattr(launcher.CloneArgs, name).offset for name, _ in launcher.CloneArgs._fields_}
    assert offsets == {'flags': 0, 'pidfd': 8, 'child_tid': 16, 'parent_tid': 24, 'exit_signal': 32,
                       'stack': 40, 'stack_size': 48, 'tls': 56, 'set_tid': 64, 'set_tid_size': 72,
                       'cgroup': 80}


def test_clone_args_request_only_pidfd_and_cgroup():
    out = ctypes.c_int(-1)
    args = launcher.build_clone_args(7, out)
    assert args.flags == launcher.CLONE_PIDFD | launcher.CLONE_INTO_CGROUP == 0x200001000
    assert args.pidfd == ctypes.addressof(out) and args.cgroup == 7
    assert args.exit_signal == signal.SIGCHLD
    assert (args.stack, args.stack_size, args.tls, args.set_tid, args.set_tid_size,
            args.child_tid, args.parent_tid) == (0,) * 7
    with pytest.raises(launcher.LauncherStop, match='cgroup directory'):
        launcher.build_clone_args(-1, out)


def test_refuses_non_linux_before_any_clone(monkeypatch):
    monkeypatch.setattr(launcher.platform, 'system', lambda: 'Darwin')
    with pytest.raises(launcher.LauncherStop, match='Linux x86-64'):
        launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                   clone=lambda a: pytest.fail('no clone'))


def test_refuses_multithreaded_supervisor(linux, monkeypatch):
    monkeypatch.setattr(Path, 'iterdir', lambda p: iter([Path('/t/1'), Path('/t/2')]))
    with pytest.raises(launcher.LauncherStop, match='single-threaded'):
        launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                   clone=lambda a: pytest.fail('no clone'))


@pytest.mark.parametrize('action', [(1, 0), (0, launcher.identity.SA_NOCLDWAIT)])
def test_refuses_auto_reaping_sigchld(linux, monkeypatch, action):
    monkeypatch.setattr(launcher.identity, '_kernel_sigchld_action', lambda: action)
    with pytest.raises(launcher.LauncherStop, match='auto-reap'):
        launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                   clone=lambda a: pytest.fail('no clone'))


@pytest.mark.parametrize('exe,argv,env,stdio,pass_fds,pattern', [
    ('bin/true', ['x'], {}, (0, 1, 2), (), 'absolute'),
    ('/bin/true', [], {}, (0, 1, 2), (), 'argv'),
    ('/bin/true', ['a\x00'], {}, (0, 1, 2), (), 'argv'),
    ('/bin/true', ['x'], {'A=B': 'c'}, (0, 1, 2), (), 'environment'),
    ('/bin/true', ['x'], {}, (0, 1), (), 'stdio'),
    ('/bin/true', ['x'], {}, (0, 1, 2), (2,), 'passed descriptors'),
])
def test_exec_validation(linux, exe, argv, env, stdio, pass_fds, pattern):
    with pytest.raises(launcher.LauncherStop, match=pattern):
        launcher.spawn_into_cgroup(3, exe, argv, env, stdio=stdio, pass_fds=pass_fds,
                                   clone=lambda a: pytest.fail('no clone'))


def test_clone_failure_is_stop_with_errno(linux):
    with pytest.raises(launcher.LauncherStop, match=r'errno 1 \(EPERM\)'):
        launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                   clone=lambda a: (-1, errno.EPERM))


def test_parent_gets_kernel_pidfd_and_passes_fds(linux, monkeypatch):
    r, w = os.pipe()
    try:
        os.set_inheritable(r, False)
        seen = {}

        def clone(args):
            seen['flags'] = args.flags
            assert os.get_inheritable(r)      # made inheritable before clone
            ctypes.c_int.from_address(args.pidfd).value = w
            return 4242, 0
        pid, pidfd = launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                                pass_fds=(r,), clone=clone)
        assert (pid, pidfd) == (4242, w) and not os.get_inheritable(w)
        assert seen['flags'] == 0x200001000
    finally:
        os.close(r)
        os.close(w)


def test_missing_pidfd_is_stop(linux):
    with pytest.raises(launcher.LauncherStop, match='no pidfd'):
        launcher.spawn_into_cgroup(3, '/bin/true', ['/bin/true'], {}, stdio=(0, 1, 2),
                                   clone=lambda a: (4242, 0))


def test_child_branch_only_dups_and_execs(linux, monkeypatch):
    calls = []
    monkeypatch.setattr(launcher.os, 'dup2', lambda a, b, inheritable=True: calls.append(('dup2', a, b)))

    class Exec(BaseException):
        pass
    monkeypatch.setattr(launcher.os, 'execve', lambda *a: calls.append(('execve',) + a) or (_ for _ in ()).throw(Exec()))
    monkeypatch.setattr(launcher.os, '_exit', lambda code: calls.append(('_exit', code)))
    with pytest.raises(Exec):
        launcher.spawn_into_cgroup(3, '/usr/bin/python3', ['/usr/bin/python3', '-I'], {'A': 'b'},
                                   stdio=(10, 11, 12), clone=lambda a: (0, 0))
    assert calls == [('dup2', 10, 0), ('dup2', 11, 1), ('dup2', 12, 2),
                     ('execve', '/usr/bin/python3', ['/usr/bin/python3', '-I'], {'A': 'b'}), ('_exit', 127)]


def test_membership_check_reads_proc_only_while_pidfd_unready(monkeypatch):
    r, w = os.pipe()
    try:
        monkeypatch.setattr(Path, 'read_text', lambda self: '0::/delegated/paper-b-m3-abc\n')
        launcher.verify_membership(55, r, 'paper-b-m3-abc')
        with pytest.raises(launcher.LauncherStop, match='membership not verified'):
            launcher.verify_membership(55, r, 'paper-b-m3-other')
        os.write(w, b'x')                      # pidfd readable = child exited
        with pytest.raises(launcher.LauncherStop, match='exited before'):
            launcher.verify_membership(55, r, 'paper-b-m3-abc')
    finally:
        os.close(r)
        os.close(w)


@pytest.mark.skipif(not hasattr(os, 'P_PIDFD'), reason='Linux pidfd constants')
def test_wait_pidfd_uses_pidfd_not_pid(monkeypatch):
    seen = []
    monkeypatch.setattr(launcher.os, 'waitid', lambda idtype, ident, flags: seen.append((idtype, ident, flags)))
    assert launcher.wait_pidfd(9) is None
    assert seen == [(os.P_PIDFD, 9, os.WEXITED | os.WNOHANG)]


# ---------------------------------------------------------------- bootstrap

def test_sentinel_reaps_namespace_reports_and_waits_for_drain():
    a, b = socket.socketpair()
    try:
        statuses = [(100, 0), (101, 9), (102, 0)]

        def waitpid(pid, flags):
            assert (pid, flags) == (-1, 0)
            if statuses:
                return statuses.pop(0)
            raise ChildProcessError()
        b.sendall(b'D')
        assert boot.run_workload_as_sentinel({'argv': ['/w'], 'env': {}}, a,
                                             fork=lambda: 100, waitpid=waitpid) == 0
        assert b.recv(2) == b'W\x00'
    finally:
        a.close()
        b.close()


@pytest.mark.parametrize('reply,expected', [(b'X', 125), (b'', 125)])
def test_sentinel_without_drain_ack_exits_125(reply, expected):
    a, b = socket.socketpair()
    try:
        waits = [(100, 3 << 8)]
        if reply:
            b.sendall(reply)
        else:
            b.shutdown(socket.SHUT_WR)
        status = boot.run_workload_as_sentinel(
            {'argv': ['/w'], 'env': {}}, a, fork=lambda: 100,
            waitpid=lambda *x: waits.pop(0) if waits else (_ for _ in ()).throw(ChildProcessError()))
        assert status == expected
        assert b.recv(2) == b'W\x03'
    finally:
        a.close()
        b.close()


def test_sentinel_never_reports_without_reaping_workload():
    a, b = socket.socketpair()
    try:
        assert boot.run_workload_as_sentinel(
            {'argv': ['/w'], 'env': {}}, a, fork=lambda: 100,
            waitpid=lambda *x: (_ for _ in ()).throw(ChildProcessError())) == 125
        b.setblocking(False)
        with pytest.raises(BlockingIOError):
            b.recv(2)
    finally:
        a.close()
        b.close()


def test_sentinel_child_closes_channel_restores_signals_and_execs(monkeypatch):
    calls = []
    a, b = socket.socketpair()
    try:
        monkeypatch.setattr(boot.os, 'close', lambda fd: calls.append(('close', fd)))
        monkeypatch.setattr(boot.signal, 'signal', lambda sig, h: calls.append(('signal', sig, h)))

        class Exit(BaseException):
            pass
        monkeypatch.setattr(boot.os, '_exit', lambda code: (_ for _ in ()).throw(Exit(code)))
        with pytest.raises(Exit):
            boot.run_workload_as_sentinel({'argv': ['/w', 'x'], 'env': {'HOME': '/work'}}, a,
                                          fork=lambda: 0,
                                          execve=lambda *x: calls.append(('execve',) + x))
        assert calls[0] == ('close', a.fileno())
        assert ('signal', signal.SIGPIPE, signal.SIG_DFL) in calls
        assert calls[-1] == ('execve', '/w', ['/w', 'x'], {'HOME': '/work'})
    finally:
        a.close()
        b.close()


def test_status_byte_mapping():
    assert boot._status_byte(0) == 0
    assert boot._status_byte(3 << 8) == 3
    assert boot._status_byte(9) == 137


def test_pid1_refuses_signal_handlers():
    previous = signal.signal(signal.SIGUSR1, lambda *a: None)
    try:
        with pytest.raises(boot.BootstrapStop, match='has a handler'):
            boot.require_default_signal_dispositions()
    finally:
        signal.signal(signal.SIGUSR1, previous)


def test_entry_refuses_spec_hash_mismatch(tmp_path, monkeypatch):
    spec = tmp_path / 'spec.json'
    spec.write_bytes(b'{}')
    writes = []

    class Exit(BaseException):
        pass
    monkeypatch.setattr(boot.os, 'write', lambda fd, data: writes.append(data) or len(data))
    monkeypatch.setattr(boot.os, '_exit', lambda code: (_ for _ in ()).throw(Exit(code)))
    monkeypatch.setattr(boot, 'bootstrap_child', lambda *a: pytest.fail('no bootstrap'))
    previous = signal.getsignal(signal.SIGINT)
    try:
        with pytest.raises(Exit) as info:
            boot.main(['--channel-fd', '5', '--spec', str(spec), '--spec-sha256', '0' * 64,
                       '--supervisor-pid', '2'])
    finally:
        signal.signal(signal.SIGINT, previous)
    assert info.value.args == (125,) and b'hash mismatch' in writes[0]


def test_entry_passes_verified_spec(tmp_path, monkeypatch):
    raw = b'{"argv":["/w"]}'
    spec = tmp_path / 'spec.json'
    spec.write_bytes(raw)
    seen = []
    monkeypatch.setattr(boot, 'bootstrap_child', lambda *a: seen.append(a))
    previous = signal.getsignal(signal.SIGINT)
    try:
        boot.main(['--channel-fd', '5', '--spec', str(spec), '--spec-sha256',
                   hashlib.sha256(raw).hexdigest(), '--supervisor-pid', '2'])
        assert signal.getsignal(signal.SIGINT) == signal.SIG_DFL
    finally:
        signal.signal(signal.SIGINT, previous)
    assert seen == [({'argv': ['/w']}, 5, 2)]


# -------------------------------------------------------------- real kernel

@pytest.mark.skipif(os.environ.get('AR_M3_KERNEL_TESTS') != '1' or not os.environ.get('AR_M3_DELEGATED_CGROUP')
                    or platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'),
                    reason='set AR_M3_KERNEL_TESTS=1 and AR_M3_DELEGATED_CGROUP')
def test_kernel_child_is_born_in_cgroup_with_atomic_pidfd():
    hooks = []
    os.register_at_fork(after_in_parent=lambda: hooks.append('parent'))
    group = groups.PrivateCgroup.create(os.environ['AR_M3_DELEGATED_CGROUP'])
    r, w = os.pipe()
    null = os.open(os.devnull, os.O_RDONLY | os.O_CLOEXEC)
    try:
        pid, pidfd = launcher.spawn_into_cgroup(
            group.directory_fd, '/bin/sh', ['/bin/sh', '-c', 'cat /proc/self/cgroup; exec sleep 30'],
            {'PATH': '/usr/bin:/bin'}, stdio=(null, w, w), pass_fds=())
        try:
            launcher.verify_membership(pid, pidfd, group.path.name)
            signal.pidfd_send_signal(pidfd, 0)
            assert hooks == []
            line = [x for x in os.read(r, 4096).decode().splitlines() if x.startswith('0::')]
            assert line and line[0].endswith('/' + group.path.name)
        finally:
            signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            select.select([pidfd], [], [], 5)
            result = launcher.wait_pidfd(pidfd)
            os.close(pidfd)
        assert result is not None and result.si_pid == pid
    finally:
        os.close(r)
        os.close(w)
        os.close(null)
        group.close()
