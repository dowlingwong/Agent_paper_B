"""Mac-safe API tests; real filter behavior needs independent Linux fixtures."""
import sys
import pytest
from r1.scripts import c3_replay_seccomp_candidate as guard


def test_must_fail_closed_on_non_linux(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'darwin')
    with pytest.raises(RuntimeError, match='Linux seccomp required'):
        guard.install()


def test_guard_denies_socket_and_io_uring_entrypoints():
    assert {'socket', 'connect', 'sendto', 'sendmsg', 'socketcall', 'io_uring_setup'} <= set(guard.DENY)
    assert guard.SCMP_ACT_KILL_PROCESS != guard.SCMP_ACT_ALLOW


def test_empty_command_is_rejected():
    with pytest.raises(ValueError, match='empty'):
        guard.exec_guarded([])


@pytest.mark.skipif(sys.platform != 'linux', reason='requires real Linux seccomp')
def test_linux_filter_denies_unix_and_preserves_arithmetic():
    import signal
    import subprocess
    guard_path = guard.__file__
    prefix = [sys.executable, '-I', '-S', guard_path, sys.executable, '-B', '-c']
    arithmetic = subprocess.run(prefix + ['print(sum(i*i for i in range(100)))'], capture_output=True, text=True)
    assert arithmetic.returncode == 0
    assert arithmetic.stdout.strip() == str(sum(i*i for i in range(100)))
    for family in ('AF_UNIX', 'AF_INET', 'AF_INET6'):
        task = subprocess.run(prefix + ['import socket,sys; print("READY",flush=True); socket.socket(getattr(socket,sys.argv[1]))', family], capture_output=True, text=True)
        assert task.returncode == -signal.SIGSYS
        assert task.stdout.strip() == 'READY'
