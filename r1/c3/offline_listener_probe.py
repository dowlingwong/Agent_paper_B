"""Fixed synthetic Linux seccomp-listener lifecycle probe; not a sandbox.

For separately reviewed site qualification only, after supervisor acceptance.
It never runs a model, reads a dataset or opens a network connection. The child
either exits normally or attempts socket(2), which the filter intercepts before
socket creation. The parent controls only its own newly forked child. Output is
ENGINEERING_ONLY and does not qualify the full supervisor or authorize replay.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import signal
import socket
import stat
import time

from r1.c3 import offline_seccomp as seccomp

SCENARIOS = ('normal_exit', 'blocked_socket_then_exit')


def event_names(mask):
    return [name for name in ('POLLIN', 'POLLHUP', 'POLLERR', 'POLLNVAL')
            if mask & getattr(select, name)]


def _child(channel, scenario):
    """Install the candidate filter, hand off the listener, then fixed behavior."""
    listener = seccomp.install_listener(channel.fileno())
    seccomp.send_listener(channel, listener)
    os.close(listener)
    if os.read(channel.fileno(), 1) != b'R':
        os._exit(122)
    channel.close()
    if scenario == 'blocked_socket_then_exit':
        # The installed filter returns USER_NOTIF for socket(2). It cannot
        # reach the actual socket implementation while the parent holds the
        # listener; the parent kills this test-owned child after observing it.
        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall(seccomp.SYSCALLS['socket'], socket.AF_INET, socket.SOCK_STREAM, 0)
        os._exit(123)  # reaching this line would be an unexpected outcome
    os._exit(0)


def observe(scenario, timeout_seconds=10):
    """Collect raw listener/pidfd readiness and safely reap only our child."""
    if scenario not in SCENARIOS:
        raise ValueError('unknown fixed scenario')
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise RuntimeError('STOP: probe requires Linux x86-64')
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        raise RuntimeError('STOP: pidfd support required')
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 30:
        raise ValueError('bounded timeout required')
    if len(list(Path('/proc/self/task').iterdir())) != 1:
        raise RuntimeError('STOP: probe must be single threaded before fork')
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    listener = pidfd = None
    pid = os.fork()
    if pid == 0:
        parent.close()
        try:
            _child(child, scenario)
        except BaseException:
            os._exit(124)
    child.close()
    waited = False
    events = []
    exit_status = None
    try:
        pidfd = os.pidfd_open(pid, 0)
        parent.settimeout(timeout_seconds)
        listener = seccomp.receive_listener(parent)
        seccomp.verify_listener(listener)
        poller = select.poll()
        poller.register(listener, select.POLLIN | select.POLLHUP | select.POLLERR)
        poller.register(pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
        parent.sendall(b'R')
        parent.close()
        deadline = time.monotonic() + timeout_seconds
        violation_killed = False
        listener_registered = True
        while time.monotonic() < deadline:
            ready = poller.poll(max(1, int((deadline - time.monotonic()) * 1000)))
            if not ready:
                continue
            events.append([{'fd': 'listener' if fd == listener else 'child_pidfd',
                            'mask': mask, 'events': event_names(mask)} for fd, mask in ready])
            if scenario == 'blocked_socket_then_exit' and not violation_killed and any(
                    fd == listener and mask & select.POLLIN for fd, mask in ready):
                # Preserve pending notification while the test-owned child
                # exits, then observe the kernel's terminal listener events.
                signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                violation_killed = True
            child_ready = any(fd == pidfd and mask & select.POLLIN for fd, mask in ready)
            if child_ready:
                _, exit_status = os.waitpid(pid, 0)
                waited = True
                # Record one immediate post-exit poll, including a possible
                # pending notification and HUP in the same event batch.
                if not listener_registered:
                    poller.register(listener, select.POLLIN | select.POLLHUP | select.POLLERR)
                terminal = poller.poll(0)
                events.append([{'fd': 'listener' if fd == listener else 'child_pidfd',
                                'mask': mask, 'events': event_names(mask)} for fd, mask in terminal])
                break
            if listener_registered and any(fd == listener for fd, _ in ready):
                # Level-triggered HUP/POLLIN can otherwise spin indefinitely
                # while waiting for our child to exit; observe it again once
                # the pidfd reports exit.
                poller.unregister(listener)
                listener_registered = False
        if not waited:
            raise TimeoutError('STOP: synthetic listener probe timed out')
        if scenario == 'normal_exit' and (not os.WIFEXITED(exit_status) or os.WEXITSTATUS(exit_status) != 0):
            raise RuntimeError('STOP: normal probe child failed')
        if scenario == 'blocked_socket_then_exit' and not violation_killed:
            raise RuntimeError('STOP: socket attempt did not produce a notification')
        return {'scenario': scenario, 'events': events, 'child_wait_status': exit_status,
                'notification_receive_after_exit': 'NOT_ATTEMPTED'}
    finally:
        parent.close()
        if not waited:
            # Only a child that we just forked, identified by its pidfd, is
            # signalled; no site process is enumerated, signalled or modified.
            if pidfd is not None:
                try:
                    signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                except OSError as exc:
                    if exc.errno != errno.ESRCH:
                        raise
            else:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            os.waitpid(pid, 0)
        if listener is not None:
            os.close(listener)
        if pidfd is not None:
            os.close(pidfd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new output file in an authorized private directory')
    args = parser.parse_args(argv)
    if (not args.out.is_absolute() or args.out.exists() or not args.out.parent.is_dir()
            or args.out.parent.resolve() != args.out.parent):
        parser.error('output must be a new absolute file under an existing private directory')
    st = args.out.parent.stat()
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) & 0o077:
        parser.error('output directory must be owned by the current user and inaccessible to group/other')
    # Create exclusively before the first process, so failures leave evidence.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(args.out, flags, 0o600)
    try:
        data = {'label': 'ENGINEERING_ONLY', 'scope': 'synthetic_listener_observation_not_replay_qualification',
                'kernel': platform.release(), 'machine': platform.machine(), 'scenarios': [],
                'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'filter_sha256': hashlib.sha256(Path(seccomp.__file__).read_bytes()).hexdigest(),
                'started_utc': datetime.now(timezone.utc).isoformat()}
        data['status'] = 'COMPLETE'
        for scenario in SCENARIOS:
            try:
                data['scenarios'].append(observe(scenario))
            except Exception as exc:
                data['status'] = 'STOP'
                data['failure'] = {'scenario': scenario, 'type': type(exc).__name__, 'message': str(exc)}
                break
        data['finished_utc'] = datetime.now(timezone.utc).isoformat()
        encoded = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
        while encoded:
            n = os.write(fd, encoded)
            if n <= 0:
                raise OSError('short output write')
            encoded = encoded[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    return 0 if data['status'] == 'COMPLETE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
