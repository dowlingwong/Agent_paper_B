"""Enforced worker network denial for the R1-E1-OPENML-AMEND offline mechanism.

ENGINEERING_ONLY; AI-assisted. Requirement (b) of the amended row is that worker
subprocesses have **no network** -- enforced, not assumed, and that they cannot
download. This module implements that for the e1 replay with an irreversible
Linux x86-64 seccomp filter installed in the replay driver before any case runs:

* every socket-creating and socket-using syscall returns ``ENETUNREACH``; the
  filter is inherited by every descendant (the ``LocalWorker`` starts the node
  with ``subprocess.run(..., shell=True)``), and ``PR_SET_NO_NEW_PRIVS`` makes
  it impossible to gain privileges that could remove it;
* non-x86-64 and x32-ABI syscalls are killed, so the filter cannot be bypassed
  through the 32-bit ABI; ``io_uring`` setup is blocked because an io_uring
  could otherwise perform socket operations without the listed syscalls;
* after installation the driver proves the denial in itself and in a fresh
  worker-representative child process (``socket(AF_INET)``, ``socket(AF_INET6)``
  and ``create_connection`` must fail with ``ENETUNREACH`` and the child must
  report ``Seccomp: 2``). Any failure -- including a non-Linux host or an
  unavailable ``seccomp``/``NO_NEW_PRIVS`` -- is a STOP: the mechanism never
  assumes that an offline-looking host is offline.

Scope and residual risk: this constrains the replay driver and its descendants
only. A separate, already-running same-uid process on the host is outside it
(operator discipline; stated in the amended report). It is deliberately
conservative: it denies *all* sockets, including loopback and AF_UNIX, so a
case that unexpectedly needs a local socket fails as a STOP instead of passing.
"""
from __future__ import annotations

import ctypes
import errno
import json
import os
import platform
import subprocess
import sys

SCHEMA = 'r1.e1_offline_network/1'
DENIED_ERRNO = 101  # Linux x86-64 ENETUNREACH; fixed, because the filter is Linux-only
DENIED_ERRNAME = 'ENETUNREACH'
MARKER = 'R1_E1_NETWORK_PROBE '

AUDIT_ARCH_X86_64 = 0xC000003E
X32_SYSCALL_BIT = 0x40000000
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_USER_NOTIF = 0x7FC00000  # deliberately not used: no listener required
SECCOMP_RET_ALLOW = 0x7FFF0000

# x86-64 syscall numbers; not portable to another architecture (the installer refuses those).
BLOCKED_SYSCALLS = {
    'socket': 41, 'connect': 42, 'accept': 43, 'sendto': 44, 'recvfrom': 45, 'sendmsg': 46,
    'recvmsg': 47, 'shutdown': 48, 'bind': 49, 'listen': 50, 'getsockname': 51, 'getpeername': 52,
    'socketpair': 53, 'setsockopt': 54, 'getsockopt': 55, 'accept4': 288, 'recvmmsg': 299,
    'sendmmsg': 307, 'io_uring_setup': 425, 'io_uring_enter': 426, 'io_uring_register': 427,
}

# classic-BPF opcodes
_LD_W_ABS = 0x20
_JMP_JEQ_K = 0x15
_JMP_JGE_K = 0x35
_RET_K = 0x06

PR_SET_NO_NEW_PRIVS = 38
SECCOMP_SET_MODE_FILTER = 1
SECCOMP_MODE_FILTER = 2
SYS_SECCOMP = 317


class NetworkDenialStop(RuntimeError):
    """Requirement (b) cannot be enforced or verified: a protocol STOP."""


class SockFilter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte),
                ('k', ctypes.c_uint32)]


class SockFprog(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filter', ctypes.POINTER(SockFilter))]


def compile_filter() -> list:
    """Classic-BPF program: arch/x32 guards, then ENETUNREACH for every network syscall."""
    if not BLOCKED_SYSCALLS:
        raise ValueError('no syscalls to block')
    program = [
        (_LD_W_ABS, 0, 0, 4),                      # A = seccomp_data.arch
        (_JMP_JEQ_K, 1, 0, AUDIT_ARCH_X86_64),     # equal -> skip the kill
        (_RET_K, 0, 0, SECCOMP_RET_KILL_PROCESS),
        (_LD_W_ABS, 0, 0, 0),                      # A = seccomp_data.nr
        (_JMP_JGE_K, 0, 1, X32_SYSCALL_BIT),       # x32 ABI -> kill
        (_RET_K, 0, 0, SECCOMP_RET_KILL_PROCESS),
    ]
    for _name, number in sorted(BLOCKED_SYSCALLS.items(), key=lambda pair: pair[1]):
        program.extend([(_JMP_JEQ_K, 0, 1, number),                 # equal -> the next instruction
                        (_RET_K, 0, 0, SECCOMP_RET_ERRNO | DENIED_ERRNO)])
    program.append((_RET_K, 0, 0, SECCOMP_RET_ALLOW))
    return program


def _supported_host() -> bool:
    return platform.system() == 'Linux' and platform.machine() in ('x86_64', 'amd64')


def _thread_count():
    try:
        return len(os.listdir('/proc/self/task'))
    except OSError:
        return None


def install() -> None:
    """Irreversibly deny network syscalls in this process and all future descendants."""
    if not _supported_host():
        raise NetworkDenialStop(f'STOP: worker network denial can only be enforced on Linux x86-64, '
                                f'not {platform.system()} {platform.machine()}')
    threads = _thread_count()
    if threads != 1:
        raise NetworkDenialStop(f'STOP: the replay driver is not single-threaded ({threads} threads); '
                                f'cannot prove the seccomp filter covers every thread')
    instructions = compile_filter()
    code = (SockFilter * len(instructions))(*(SockFilter(*instruction) for instruction in instructions))
    program = SockFprog(len(instructions), code)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        error = ctypes.get_errno()
        raise NetworkDenialStop(f'STOP: PR_SET_NO_NEW_PRIVS failed: errno {error} '
                                f'({errno.errorcode.get(error, "?")})')
    result = libc.syscall(SYS_SECCOMP, SECCOMP_SET_MODE_FILTER, 0, ctypes.byref(program))
    if result != 0:
        error = ctypes.get_errno()
        raise NetworkDenialStop(f'STOP: seccomp filter installation failed: errno {error} '
                                f'({errno.errorcode.get(error, "?")})')


def _seccomp_mode():
    try:
        with open('/proc/self/status') as handle:
            for line in handle:
                if line.startswith('Seccomp:'):
                    return int(line.split(':', 1)[1].strip())
    except (OSError, ValueError):
        pass
    return None


def _attempt(domain) -> dict:
    import socket
    try:
        sock = socket.socket(domain, socket.SOCK_STREAM)
    except OSError as exc:
        return {'errno': exc.errno, 'error': errno.errorcode.get(exc.errno), 'type': type(exc).__name__}
    else:
        sock.close()
        return {'created': True}


def in_process_probe() -> dict:
    """Prove the installed filter denies sockets in the calling process."""
    import socket
    result = {'seccomp_mode': _seccomp_mode(), 'af_inet': _attempt(socket.AF_INET),
              'af_inet6': _attempt(socket.AF_INET6)}
    try:
        socket.create_connection(('192.0.2.1', 9), timeout=2.0)
    except OSError as exc:
        result['connect'] = {'errno': exc.errno, 'error': errno.errorcode.get(exc.errno),
                             'type': type(exc).__name__}
    else:
        result['connect'] = {'connected': True}
    result['denied'] = all(isinstance(result[name], dict) and result[name].get('errno') == DENIED_ERRNO
                           for name in ('af_inet', 'af_inet6', 'connect')) and \
        result['seccomp_mode'] == SECCOMP_MODE_FILTER
    return result


PROBE = r'''
import errno, json, socket, sys
out = {'python': sys.version.split()[0]}
def attempt(name, family):
    try:
        s = socket.socket(family, socket.SOCK_STREAM)
    except OSError as exc:
        out[name] = {'errno': exc.errno, 'error': errno.errorcode.get(exc.errno), 'type': type(exc).__name__}
    else:
        s.close(); out[name] = {'created': True}
attempt('af_inet', socket.AF_INET)
attempt('af_inet6', socket.AF_INET6)
try:
    socket.create_connection(('192.0.2.1', 9), timeout=2.0)
except OSError as exc:
    out['connect'] = {'errno': exc.errno, 'error': errno.errorcode.get(exc.errno), 'type': type(exc).__name__}
else:
    out['connect'] = {'connected': True}
try:
    with open('/proc/self/status') as handle:
        mode = [line.split(':', 1)[1].strip() for line in handle if line.startswith('Seccomp:')]
    out['seccomp_mode'] = int(mode[0]) if mode else None
except (OSError, ValueError):
    out['seccomp_mode'] = None
out['denied'] = all(isinstance(out[name], dict) and out[name].get('errno') == 101
                    for name in ('af_inet', 'af_inet6', 'connect')) and out['seccomp_mode'] == 2
print('R1_E1_NETWORK_PROBE ' + json.dumps(out, sort_keys=True))
'''


def child_probe(python=None) -> dict:
    """Prove the filter is inherited by a fresh worker-representative child process."""
    python = python or sys.executable
    try:
        completed = subprocess.run([python, '-B', '-c', PROBE], capture_output=True, text=True, timeout=120,
                                   env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    except (OSError, subprocess.SubprocessError) as exc:
        raise NetworkDenialStop(f'STOP: network-denial probe child failed to start: '
                                f'{type(exc).__name__}: {exc}') from exc
    for line in completed.stdout.splitlines():
        if line.startswith(MARKER):
            try:
                return json.loads(line[len(MARKER):])
            except ValueError as exc:
                raise NetworkDenialStop('STOP: network-denial probe child returned invalid JSON') from exc
    raise NetworkDenialStop(f'STOP: network-denial probe child returned no report '
                            f'(exit {completed.returncode}; stdout {completed.stdout[-400:]!r}; '
                            f'stderr {completed.stderr[-400:]!r})')


def verify_denial(report: dict, where: str) -> None:
    if not isinstance(report, dict) or report.get('denied') is not True:
        raise NetworkDenialStop(f'STOP: worker network denial is not proven in the {where}: {report!r}')
    if report.get('seccomp_mode') != SECCOMP_MODE_FILTER:
        raise NetworkDenialStop(f'STOP: the {where} is not running under a seccomp filter '
                                f'(mode {report.get("seccomp_mode")!r})')
    for name in ('af_inet', 'af_inet6', 'connect'):
        entry = report.get(name)
        if not isinstance(entry, dict) or entry.get('errno') != DENIED_ERRNO:
            raise NetworkDenialStop(f'STOP: worker network denial is not proven in the {where} '
                                    f'for {name}: {entry!r}')


def enforce(*, installer=None, in_process=None, child=None) -> dict:
    """Install and prove requirement (b); STOP if any step cannot be enforced or verified."""
    installer = installer or install
    in_process = in_process or in_process_probe
    child = child or child_probe
    if not _supported_host() and installer is install:
        raise NetworkDenialStop(f'STOP: worker network denial can only be enforced on Linux x86-64, '
                                f'not {platform.system()} {platform.machine()}')
    try:
        installer()
    except NetworkDenialStop:
        raise
    except Exception as exc:  # noqa: BLE001 - fail closed
        raise NetworkDenialStop(f'STOP: worker network denial could not be installed: '
                                f'{type(exc).__name__}: {exc}') from exc
    local = in_process()
    verify_denial(local, 'replay process')
    worker = child()
    verify_denial(worker, 'worker subprocess')
    return {'schema': SCHEMA, 'enforced': True,
            'mechanism': 'seccomp filter, PR_SET_NO_NEW_PRIVS, inherited by descendants',
            'host': f'{platform.system()} {platform.machine()}',
            'denied_errno': DENIED_ERRNO, 'denied_errname': DENIED_ERRNAME,
            'seccomp_mode': SECCOMP_MODE_FILTER,
            'blocked_syscalls': sorted(BLOCKED_SYSCALLS),
            'in_process': local, 'worker_subprocess': worker}


def reverify(*, child=None) -> dict:
    """Re-prove requirement (b) after the last case (the filter cannot be removed)."""
    report = (child or child_probe)()
    verify_denial(report, 'worker subprocess (post-run)')
    return report
