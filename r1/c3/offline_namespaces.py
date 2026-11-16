"""Linux namespace bootstrap primitives for the M3 supervisor candidate.

Only a dedicated trusted, single-threaded bootstrap process may call these
irreversible primitives. An error after unshare requires immediate process exit.
They do not create the filesystem closure, mount /proc, drop capabilities,
install seccomp, or launch a workload. Production replay remains STOP.
"""
from __future__ import annotations
import ctypes
import os
from pathlib import Path
import platform
import select
import signal

CLONE_NEWNS=0x00020000
CLONE_NEWUSER=0x10000000
CLONE_NEWIPC=0x08000000
CLONE_NEWNET=0x40000000
CLONE_NEWPID=0x20000000
MS_REC=16384
MS_PRIVATE=1<<18
PR_SET_PDEATHSIG=1


class NamespaceStop(RuntimeError):
    pass


def _libc(): return ctypes.CDLL(None,use_errno=True)


def _check(rc,description):
    if rc!=0:
        error=ctypes.get_errno()
        raise NamespaceStop(f'STOP: {description}: errno {error}')


def _write_proc(path, data):
    fd=os.open(path,os.O_WRONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    try:
        encoded=data.encode('ascii')
        if os.write(fd,encoded)!=len(encoded): raise NamespaceStop(f'STOP: short write to {path}')
    finally: os.close(fd)


def parent_death_guard(expected_parent):
    """Ensure this bootstrap dies if its actual supervisor parent exits.

    Must be called before unsharing the PID namespace; if the process sees a
    different parent before or immediately after prctl, stop. This alone does
    not establish descendant cleanup or readiness/monitor crash safety.
    """
    if platform.system()!='Linux': raise NamespaceStop('STOP: Linux required')
    if type(expected_parent) is not int or expected_parent<=1 or os.getppid()!=expected_parent:
        raise NamespaceStop('STOP: bootstrap parent mismatch')
    libc=_libc();_check(libc.prctl(PR_SET_PDEATHSIG,signal.SIGKILL,0,0,0),'PR_SET_PDEATHSIG')
    if os.getppid()!=expected_parent: raise NamespaceStop('STOP: supervisor changed during setup')


def pid_init_parent_guard(parent_pidfd):
    """PID-1 child guards its trusted outer parent using an inherited pidfd.

    The outer bootstrap opens a pidfd for itself before forking the PID-1
    child. The child sets PDEATHSIG and polls that same stable identity, closing
    the race in which the parent exits before prctl; callers close the pidfd
    before untrusted exec. This still needs Linux kernel qualification.
    """
    if platform.system()!='Linux' or type(parent_pidfd) is not int or parent_pidfd<0:
        raise NamespaceStop('STOP: Linux parent pidfd required')
    libc=_libc();_check(libc.prctl(PR_SET_PDEATHSIG,signal.SIGKILL,0,0,0),'PID-1 PR_SET_PDEATHSIG')
    poller=select.poll();poller.register(parent_pidfd,select.POLLIN)
    if poller.poll(0):raise NamespaceStop('STOP: outer bootstrap parent exited')


def unshare_bootstrap():
    """Create isolated user, mount, IPC, network, and child PID namespaces.

    NEWPID affects only subsequent children, so the caller must fork a PID-1
    init and safely supervise it. This function is not itself a containment
    verdict and never execs untrusted code.
    """
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):
        raise NamespaceStop('STOP: supported Linux x86-64 required')
    try:
        if len(list(Path('/proc/self/task').iterdir()))!=1:
            raise NamespaceStop('STOP: bootstrap must be single threaded')
    except OSError as exc: raise NamespaceStop('STOP: cannot verify bootstrap thread count') from exc
    uid=os.getuid();gid=os.getgid();libc=_libc()
    _check(libc.unshare(CLONE_NEWUSER),'user namespace')
    try:
        _write_proc('/proc/self/uid_map',f'0 {uid} 1\n')
        _write_proc('/proc/self/setgroups','deny\n')
        _write_proc('/proc/self/gid_map',f'0 {gid} 1\n')
    except OSError as exc:
        raise NamespaceStop('STOP: user namespace mappings unavailable') from exc
    flags=CLONE_NEWNS|CLONE_NEWIPC|CLONE_NEWNET|CLONE_NEWPID
    _check(libc.unshare(flags),'mount, IPC, network and child PID namespaces')
    # Prevent propagation of later mounts to the host mount namespace.
    _check(libc.mount(None,ctypes.c_char_p(b'/'),None,MS_REC|MS_PRIVATE,None),'private mount propagation')
