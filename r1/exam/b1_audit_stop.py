"""Unwired B1 audit failure notification component; requires reviewed runner channel.

No process, file, or cgroup is created here. The caller must establish that the
nonblocking pipe is owned by the B1 runner, pass the write FD through the worker
contract, and freeze the owned cgroup upon receipt. This helper by itself does
not stop a pool or qualify a production execution path.
"""
from __future__ import annotations

import fcntl
import os
import stat
import threading


class AuditNotificationStop(RuntimeError):
    """The audit failure channel is missing, invalid, or cannot report STOP."""


def require_notify_fd(fd):
    """Refuse before work unless fd is a nonblocking pipe write end."""
    if type(fd) is not int or fd < 3:
        raise AuditNotificationStop('STOP: invalid audit failure descriptor')
    try:
        mode = os.fstat(fd).st_mode
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    except OSError as exc:
        raise AuditNotificationStop('STOP: audit failure descriptor unavailable') from exc
    if (not stat.S_ISFIFO(mode) or (flags & os.O_ACCMODE) != os.O_WRONLY
            or not flags & os.O_NONBLOCK):
        raise AuditNotificationStop('STOP: audit failure descriptor is not a nonblocking pipe writer')


def run_notifying_audit(fd, run_config, *args):
    """Notify the owning runner before returning an audit exception to its pool.

    ``run_config`` is the real, picklable top-level audit function supplied by
    the future integration. A one-byte write is atomic for a real POSIX pipe.
    The byte means STOP, not proof that the receiver or freeze succeeded.
    """
    require_notify_fd(fd)
    try:
        return run_config(*args)
    except BaseException as original:
        try:
            written = os.write(fd, b'S')
            if written != 1:
                raise OSError('short audit failure notification')
        except BaseException as notification_error:
            raise AuditNotificationStop(
                f'STOP: audit failure notification failed ({type(notification_error).__name__})'
            ) from original
        raise


def send_audit_complete(fd):
    """Collector announces normal completion; runner still verifies exit and cgroup."""
    require_notify_fd(fd)
    try:
        if os.write(fd, b'D') != 1:
            raise OSError('short audit completion notification')
    except OSError as exc:
        raise AuditNotificationStop('STOP: audit completion notification failed') from exc


def handle_ready_audit_channel(fd, mark_stopping, freeze, expected_alive=lambda: True,
                               complete_seen=lambda: False, mark_complete=lambda: None):
    """Runner-side step; only call while the audited child is expected alive.

    The integration must retain the reported exception and never publish
    success. EOF or any unreadable signal is a STOP while work is live. The
    callback should be the owned B1Containment.freeze; a successful return is
    not a substitute for the independent site cgroup qualification.
    """
    read_error = None
    try:
        token = os.read(fd, 1)
    except BlockingIOError:
        return False
    except OSError as exc:
        token = None
        read_error = exc
    if token == b'D' and read_error is None:
        mark_complete()
        return False
    if token == b'' and read_error is None and (complete_seen() or not expected_alive()):
        return False
    try:
        try:
            mark_stopping()
        finally:
            freeze()
    except BaseException as exc:
        raise AuditNotificationStop('STOP: audit notification marking or freeze failed') from exc
    if read_error is not None:
        raise AuditNotificationStop('STOP: audit failure channel unreadable') from read_error
    if token == b'S':
        raise AuditNotificationStop('STOP: audit worker reported failure')
    raise AuditNotificationStop('STOP: audit failure channel closed or malformed')


class AuditStopMonitor:
    """Runner-owned monitor; the integration must pass its own containment."""
    def __init__(self, read_fd, process, containment):
        self.fd = read_fd
        self.process = process
        self.containment = containment
        self.stopping = threading.Event()
        self.completed = threading.Event()
        self.shutdown_requested = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def _run(self):
        try:
            while not self.shutdown_requested.is_set():
                handle_ready_audit_channel(self.fd, self.stopping.set,
                                           self.containment.freeze,
                                           lambda: self.process.poll() is None,
                                           self.completed.is_set, self.completed.set)
                if self.process.poll() is not None:
                    return
                self.shutdown_requested.wait(.05)
        except BaseException as exc:
            self.error = exc
            self.stopping.set()
            if not isinstance(exc, AuditNotificationStop):
                try:
                    self.containment.freeze()
                except BaseException as freeze_error:
                    self.error = AuditNotificationStop(
                        f'STOP: audit monitor failed and freeze failed ({type(freeze_error).__name__})'
                    )

    def check(self):
        if self.stopping.is_set():
            raise AuditNotificationStop('STOP: owned audit failure or monitor failure') from self.error

    def finish(self):
        self.thread.join(timeout=15)
        if self.thread.is_alive():
            raise AuditNotificationStop('STOP: audit failure monitor did not finish')
        self.check()
        if not self.completed.is_set():
            raise AuditNotificationStop('STOP: audit completion notification is missing')

    def shutdown(self):
        self.shutdown_requested.set()
        self.thread.join(timeout=15)
        if self.thread.is_alive():
            raise AuditNotificationStop('STOP: audit failure monitor did not shut down')
