"""Fail-closed child-PID assignment checks for the unqualified M3 supervisor.

These Linux x86-64 checks are not kernel qualification, adversarial host
isolation, or authorization to replay. The caller must remain single-threaded
and keep catchable signals blocked from the check through numeric cgroup
assignment; process changes by an external tracer are outside this unit.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import platform
import signal


class ChildIdentityStop(RuntimeError):
    pass


class _KernelSigaction(ctypes.Structure):
    # Linux x86-64 kernel ABI (not libc struct sigaction): handler, flags,
    # restorer and one 64-bit kernel sigset. __NR_rt_sigaction = 13.
    _fields_ = [('handler', ctypes.c_ulong), ('flags', ctypes.c_ulong),
                ('restorer', ctypes.c_ulong), ('mask', ctypes.c_ulong)]


SA_NOCLDWAIT = 0x00000002


def _kernel_sigchld_action():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise ChildIdentityStop('STOP: Linux x86-64 required for SIGCHLD inspection')
    if ctypes.sizeof(ctypes.c_ulong) != 8 or ctypes.sizeof(_KernelSigaction) != 32:
        raise ChildIdentityStop('STOP: unsupported kernel sigaction ABI')
    action = _KernelSigaction()
    libc = ctypes.CDLL(None, use_errno=True)
    # Read only. Kernel sigset size on x86-64 is 8 bytes; passing a wrong
    # size fails rather than guessing the libc sigaction layout.
    if libc.syscall(13, int(signal.SIGCHLD), 0, ctypes.byref(action), 8) != 0:
        raise ChildIdentityStop('STOP: kernel SIGCHLD action unavailable')
    return action.handler, action.flags


def blockable_signals():
    if not hasattr(signal, 'pthread_sigmask') or not hasattr(signal, 'valid_signals'):
        raise ChildIdentityStop('STOP: signal-mask inspection unavailable')
    return set(signal.valid_signals()) - {signal.SIGKILL, signal.SIGSTOP}


def require_assignment_guard():
    """Refuse assignment unless zombie retention and mask assumptions hold."""
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise ChildIdentityStop('STOP: Linux x86-64 required')
    try:
        if len(list(Path('/proc/self/task').iterdir())) != 1:
            raise ChildIdentityStop('STOP: child assignment requires one supervisor thread')
        required = blockable_signals()
        current = set(signal.pthread_sigmask(signal.SIG_BLOCK, set()))
        if not required <= current:
            raise ChildIdentityStop('STOP: child assignment requires blocked signal handlers')
        # CPython may already have queued a Python callback before the OS
        # mask was installed; blocking later delivery alone does not prevent
        # that callback from running between the check and cgroup.procs write.
        # This narrow candidate therefore rejects Python callbacks and unknown
        # dispositions rather than attempting to clear a pending callback.
        for sig in required:
            action = signal.getsignal(sig)
            if action not in (signal.SIG_DFL, signal.SIG_IGN):
                raise ChildIdentityStop('STOP: pending or unknown Python signal callback possible')
        handler, flags = _kernel_sigchld_action()
    except (OSError, ValueError) as exc:
        raise ChildIdentityStop('STOP: child assignment guard unavailable') from exc
    # SIG_DFL is the null kernel handler; explicit SIG_IGN is 1 and is not
    # equivalent for child zombie retention. SA_NOCLDWAIT can accompany DFL.
    if handler != 0 or flags & SA_NOCLDWAIT:
        raise ChildIdentityStop('STOP: SIGCHLD can auto-reap or execute a handler')
