"""Isolated cgroup-v2 guardian; invoked only as an explicit B1 child process.

No files are removed. This process stays outside the guarded subtree and holds
an inherited GPU flock through STOP. It must never send signals to numeric PIDs.
"""
import os
import select
import socket
import sys
import time


def _values(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    values = {}
    for line in os.read(fd, 4096).decode('ascii').splitlines():
        key, value = line.split()
        if key in values:
            raise ValueError('duplicate cgroup.events field')
        values[key] = int(value)
    return values


def _freeze(freeze_fd, events_fd, timeout=10.0):
    os.lseek(freeze_fd, 0, os.SEEK_SET)
    if os.write(freeze_fd, b'1\n') != 2:
        raise OSError('short cgroup.freeze write')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _values(events_fd).get('frozen') == 1:
            return
        time.sleep(.01)
    raise TimeoutError('cgroup frozen state was not observed')


def _retain_lease():
    while True:
        time.sleep(3600)


def _reply(control, payload, freeze_fd, events_fd):
    try:
        control.sendall(payload)
    except OSError:
        # Peer death must never release the inherited lease by causing this
        # guardian to exit; the operator must inspect the held STOP scene.
        try: _freeze(freeze_fd, events_fd)
        except Exception: pass
        _retain_lease()


def main(argv):
    if len(argv) != 6:
        return 2
    control_fd, parent_pidfd, freeze_fd, events_fd, supervisor_pidfd, supervisor_live_fd = map(int, argv)
    control = socket.socket(fileno=control_fd)
    poller = select.poll()
    poller.register(parent_pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
    poller.register(supervisor_pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
    poller.register(supervisor_live_fd, select.POLLIN | select.POLLHUP | select.POLLERR)
    poller.register(control_fd, select.POLLIN | select.POLLHUP | select.POLLERR)
    initial = dict(poller.poll(0))
    if initial.get(parent_pidfd, 0) or initial.get(supervisor_pidfd, 0) or initial.get(supervisor_live_fd, 0):
        try: _freeze(freeze_fd, events_fd)
        except Exception: pass
        _retain_lease()
    try:
        control.sendall(b'READY')
    except OSError:
        try: _freeze(freeze_fd, events_fd)
        except Exception: pass
        _retain_lease()
    frozen = False
    while True:
        try:
            events = dict(poller.poll(1000))
        except InterruptedError:
            continue
        except OSError:
            try: _freeze(freeze_fd, events_fd)
            except Exception: pass
            _retain_lease()
        # A pidfd is an independent parent-death witness: pipe/socket duplicates
        # in children cannot suppress the death event.
        dead = bool(events.get(parent_pidfd, 0) or events.get(supervisor_pidfd, 0) or events.get(supervisor_live_fd, 0))
        control_event = events.get(control_fd, 0)
        if dead or (control_event & (select.POLLHUP | select.POLLERR)):
            try:
                if not frozen:
                    _freeze(freeze_fd, events_fd)
                    frozen = True
            except Exception:
                # Preserve the lease even when freezing failed; operator must
                # treat lack of acknowledgement as NOT CHECKABLE.
                pass
            _retain_lease()
        if not (control_event & select.POLLIN):
            continue
        try:
            msg = control.recv(64)
        except OSError:
            try: _freeze(freeze_fd, events_fd)
            except Exception: pass
            _retain_lease()
        if not msg:
            try:
                if not frozen:
                    _freeze(freeze_fd, events_fd)
                    frozen = True
            except Exception:
                pass
            _retain_lease()
        if msg == b'FREEZE':
            try:
                if not frozen:
                    _freeze(freeze_fd, events_fd)
                    frozen = True
                _reply(control,b'FROZEN',freeze_fd,events_fd)
            except Exception as exc:
                _reply(control,('FAILED:' + type(exc).__name__).encode('ascii'),freeze_fd,events_fd)
        elif msg == b'FINISH':
            # Parent promises no further enrollment; verify own subtree is empty.
            if frozen or _values(events_fd).get('populated') != 0:
                _reply(control,b'NOT_EMPTY_OR_FROZEN',freeze_fd,events_fd)
            else:
                _reply(control,b'FINISHED',freeze_fd,events_fd)
                return 0
        else:
            _reply(control,b'BAD_COMMAND',freeze_fd,events_fd)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
