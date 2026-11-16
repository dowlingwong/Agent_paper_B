"""Trusted clone3 launcher for the M3 supervisor candidate (Linux x86-64).

Replaces the earlier ``os.fork()`` + numeric ``cgroup.procs`` write. The child
is created by one raw ``clone3`` system call with ``CLONE_PIDFD`` and
``CLONE_INTO_CGROUP``:

* the kernel places the child in the private cgroup before it runs a single
  instruction, so no numeric PID is ever written to ``cgroup.procs``;
* the kernel returns a pidfd for exactly that child atomically, so no later
  lookup by PID (``pidfd_open``) can bind a recycled PID;
* the raw system call bypasses ``os.register_at_fork`` callbacks and libc
  ``pthread_atfork`` handlers in the parent, which closes the reviewed
  "at-fork callback reaps the child before assignment" sequence by
  construction (MAC_M3_SIGCHLD_ASSIGNMENT_REVIEW_20261107.md).

The child does not run the bootstrap in the cloned interpreter image. Between
the ``clone3`` return and ``execve`` it executes only the bounded Python path in
:func:`_child_exec` (three ``dup2`` calls and one ``execve`` of a fresh,
isolated interpreter running the trusted bootstrap entry script). That is why
the caller must be single-threaded: no other thread can hold an interpreter or
allocator lock in the cloned image.

NOT a qualification. Kernel >= 5.7, a cgroup-v2 default hierarchy, delegation
write access to the target ``cgroup.procs`` and the common ancestor, and
``clone3`` not being filtered for the supervisor all need the separate on-site
qualification. Production replay STOP is unchanged.
"""
from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import platform
import select
import signal

from r1.c3 import offline_child_identity as identity

SYS_CLONE3 = 435              # x86-64 only
CLONE_PIDFD = 0x00001000
CLONE_INTO_CGROUP = 0x200000000
CLONE_ARGS_SIZE_VER2 = 88     # struct clone_args up to and including .cgroup


class LauncherStop(RuntimeError):
    pass


class CloneArgs(ctypes.Structure):
    """``struct clone_args`` (include/uapi/linux/sched.h), all ``__aligned_u64``."""
    _fields_ = [('flags', ctypes.c_uint64), ('pidfd', ctypes.c_uint64),
                ('child_tid', ctypes.c_uint64), ('parent_tid', ctypes.c_uint64),
                ('exit_signal', ctypes.c_uint64), ('stack', ctypes.c_uint64),
                ('stack_size', ctypes.c_uint64), ('tls', ctypes.c_uint64),
                ('set_tid', ctypes.c_uint64), ('set_tid_size', ctypes.c_uint64),
                ('cgroup', ctypes.c_uint64)]


def build_clone_args(cgroup_fd, pidfd_out):
    """Return the exact clone_args used by :func:`spawn_into_cgroup`.

    Only ``CLONE_PIDFD | CLONE_INTO_CGROUP`` and ``exit_signal = SIGCHLD``;
    ``stack = 0`` gives fork-like semantics on a copy of the caller's stack.
    No namespace, VM, file-table or signal-handler sharing flag is set.
    """
    if type(cgroup_fd) is not int or cgroup_fd < 0:
        raise LauncherStop('STOP: cgroup directory descriptor required')
    args = CloneArgs()
    args.flags = CLONE_PIDFD | CLONE_INTO_CGROUP
    args.pidfd = ctypes.addressof(pidfd_out)
    args.exit_signal = int(signal.SIGCHLD)
    args.cgroup = cgroup_fd
    return args


def _require_platform():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise LauncherStop('STOP: clone3 launcher supports Linux x86-64 only')
    if ctypes.sizeof(CloneArgs) != CLONE_ARGS_SIZE_VER2:
        raise LauncherStop('STOP: unexpected struct clone_args layout')


def require_launch_preconditions():
    """Single thread (cloned image safety) and exit-status retention.

    SIGCHLD must not auto-reap (SIG_IGN or SA_NOCLDWAIT): the supervisor needs
    the child's exit status. Identity no longer depends on this check: a pidfd
    from CLONE_PIDFD can never refer to another process, so a lost status is a
    fail-closed STOP, not a misattribution.
    """
    _require_platform()
    try:
        if len(list(Path('/proc/self/task').iterdir())) != 1:
            raise LauncherStop('STOP: launcher requires a single-threaded supervisor')
    except OSError as exc:
        raise LauncherStop('STOP: supervisor thread count unavailable') from exc
    try:
        handler, flags = identity._kernel_sigchld_action()
    except identity.ChildIdentityStop as exc:
        raise LauncherStop(str(exc)) from exc
    if handler == 1 or flags & identity.SA_NOCLDWAIT:
        raise LauncherStop('STOP: SIGCHLD disposition would auto-reap the child')


def _raw_clone3(args):
    """Issue clone3 while holding the GIL (PyDLL), so the child image has it."""
    libc = ctypes.PyDLL(None, use_errno=True)
    fn = libc.syscall
    fn.restype = ctypes.c_long
    fn.argtypes = [ctypes.c_long, ctypes.c_void_p, ctypes.c_size_t]
    rc = fn(SYS_CLONE3, ctypes.addressof(args), ctypes.sizeof(args))
    return rc, (ctypes.get_errno() if rc < 0 else 0)


def _child_exec(stdio, executable, argv, env):
    """Only code run in the clone3 child before execve; never returns."""
    try:
        os.dup2(stdio[0], 0, inheritable=True)
        os.dup2(stdio[1], 1, inheritable=True)
        os.dup2(stdio[2], 2, inheritable=True)
        os.execve(executable, argv, env)
    finally:
        os._exit(127)


def validate_exec(executable, argv, env, pass_fds, stdio):
    if not isinstance(executable, str) or not executable.startswith('/'):
        raise LauncherStop('STOP: absolute bootstrap interpreter required')
    if (not isinstance(argv, list) or not argv
            or any(not isinstance(a, str) or '\x00' in a for a in argv)):
        raise LauncherStop('STOP: invalid bootstrap argv')
    if not isinstance(env, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                        or '\x00' in k + v or '=' in k for k, v in env.items()):
        raise LauncherStop('STOP: invalid bootstrap environment')
    if (not isinstance(stdio, tuple) or len(stdio) != 3
            or any(type(fd) is not int or fd < 0 for fd in stdio)):
        raise LauncherStop('STOP: three stdio descriptors required')
    if any(type(fd) is not int or fd < 3 for fd in pass_fds):
        raise LauncherStop('STOP: passed descriptors must be >= 3')


def spawn_into_cgroup(cgroup_fd, executable, argv, env, *, stdio, pass_fds=(),
                      clone=None):
    """Create the bootstrap child inside ``cgroup_fd``; return ``(pid, pidfd)``.

    ``pass_fds`` are made inheritable for the child (the caller closes its own
    copies afterwards); every other descriptor of the supervisor should be
    ``O_CLOEXEC`` and the bootstrap closes any survivor itself. On any failure
    no child exists (clone3 failed) or the child is SIGKILLed via its pidfd.
    ``clone`` is a test seam for the raw system call only.
    """
    require_launch_preconditions()
    validate_exec(executable, argv, env, pass_fds, stdio)
    # Pre-encode everything so the child does as little as possible.
    env = dict(env)
    argv = list(argv)
    for fd in pass_fds:
        os.set_inheritable(fd, True)
    pidfd_out = ctypes.c_int(-1)
    args = build_clone_args(cgroup_fd, pidfd_out)
    rc, err = (clone or _raw_clone3)(args)
    if rc == 0:
        _child_exec(stdio, executable, argv, env)
    if rc < 0:
        raise LauncherStop(f'STOP: clone3 into private cgroup failed: errno {err} '
                           f'({errno.errorcode.get(err, "?")})')
    pid, pidfd = int(rc), int(pidfd_out.value)
    if pidfd < 0:
        # Kernel contract violated; no stable identity. pid is a child of ours,
        # but we refuse to signal it by number.
        raise LauncherStop('STOP: clone3 returned no pidfd')
    try:
        os.set_inheritable(pidfd, False)
    except OSError as exc:
        _kill_quiet(pidfd)
        os.close(pidfd)
        raise LauncherStop('STOP: pidfd flags unavailable') from exc
    return pid, pidfd


def _kill_quiet(pidfd):
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
    except OSError:
        pass


def verify_membership(pid, pidfd, cgroup_name, *, full_path=None):
    """Check /proc/<pid>/cgroup, then prove the PID still named the pidfd child.

    The child is unreaped (only the supervisor reaps, via its pidfd), so while
    the pidfd is not readable the numeric PID cannot have been recycled.
    """
    poller = select.poll()
    poller.register(pidfd, select.POLLIN)
    if poller.poll(0):
        raise LauncherStop('STOP: bootstrap exited before membership check')
    try:
        text = Path(f'/proc/{pid}/cgroup').read_text()
    except OSError as exc:
        raise LauncherStop('STOP: bootstrap cgroup membership unavailable') from exc
    if poller.poll(0):
        raise LauncherStop('STOP: bootstrap exited during membership check')
    matches = [line.split('::', 1)[1] for line in text.splitlines() if line.startswith('0::')]
    if len(matches) != 1 or Path(matches[0]).name != cgroup_name:
        raise LauncherStop('STOP: bootstrap cgroup membership not verified')
    # Exact check: the /proc path (relative to the cgroup-v2 mount as seen from
    # this cgroup namespace) must be a full trailing component path of the
    # private cgroup's filesystem path.
    if full_path is not None:
        rel = matches[0].rstrip('/')
        if not rel.startswith('/') or not (str(full_path).rstrip('/') == rel
                                           or str(full_path).rstrip('/').endswith(rel)):
            raise LauncherStop('STOP: bootstrap cgroup path not verified')


def wait_pidfd(pidfd):
    """Reap exactly the pidfd child without blocking; ``None`` if still running."""
    result = os.waitid(os.P_PIDFD, pidfd, os.WEXITED | os.WNOHANG)
    if result is None or result.si_pid == 0:
        return None
    return result
