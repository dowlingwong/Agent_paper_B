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


def handle_ready_audit_channel(fd, mark_stopping, freeze):
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
