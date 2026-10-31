"""Candidate Linux offline process guard, for independent review only.

Uses unprivileged libseccomp with NO_NEW_PRIVS. A prohibited socket or io_uring
syscall kills the calling process rather than returning an error it could catch.
The candidate executor uses it; neither is independently accepted or authorized for use.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys

# No inherited socket descriptors may be passed to the guarded process.
# Also deny alternate socketcall and io_uring interfaces where available.
DENY = ('socket', 'socketpair', 'socketcall', 'connect', 'bind', 'listen', 'accept',
        'accept4', 'sendto', 'sendmsg', 'sendmmsg', 'recvfrom', 'recvmsg',
        'recvmmsg', 'shutdown', 'setsockopt', 'getsockopt', 'getpeername',
        'getsockname', 'io_uring_setup')
SCMP_ACT_ALLOW = 0x7FFF0000
SCMP_ACT_KILL_PROCESS = 0x80000000
PR_SET_NO_NEW_PRIVS = 38


def install():
    if sys.platform != 'linux':
        raise RuntimeError('STOP: Linux seccomp required')
    name = ctypes.util.find_library('seccomp')
    if not name:
        raise RuntimeError('STOP: libseccomp unavailable')
    lib = ctypes.CDLL(name, use_errno=True)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.restype = None
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise RuntimeError('STOP: NO_NEW_PRIVS unavailable')
    context = lib.seccomp_init(SCMP_ACT_ALLOW)
    if not context:
        raise RuntimeError('STOP: seccomp init failed')
    resolved = set()
    try:
        for syscall in DENY:
            number = lib.seccomp_syscall_resolve_name(syscall.encode('ascii'))
            if number == -1:
                continue
            resolved.add(syscall)
            if lib.seccomp_rule_add(context, SCMP_ACT_KILL_PROCESS, number, 0) != 0:
                raise RuntimeError(f'STOP: seccomp rule rejected for {syscall}')
        if not {'socket', 'connect', 'sendto', 'sendmsg', 'io_uring_setup'} <= resolved:
            raise RuntimeError('STOP: required network syscall names unavailable')
        if lib.seccomp_load(context) != 0:
            raise RuntimeError('STOP: kernel rejected seccomp filter')
    finally:
        lib.seccomp_release(context)


def exec_guarded(argv: list[str]):
    if not argv:
        raise ValueError('STOP: empty target command')
    install()
    os.execvp(argv[0], argv)


if __name__ == '__main__':
    exec_guarded(sys.argv[1:])
