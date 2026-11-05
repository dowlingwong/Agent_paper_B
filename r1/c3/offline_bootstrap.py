"""M3 trusted bootstrap candidate; not connected to production replay.

Only call in a dedicated forked child after the supervisor has placed it in a
fresh private cgroup. All errors require immediate child exit. Linux kernel and
full-boundary review are mandatory before any real workload is considered.
"""
from __future__ import annotations
import os
import errno
from pathlib import Path, PurePosixPath
import socket
import sys

from r1.c3 import offline_capabilities as caps
from r1.c3 import offline_mounts as mounts
from r1.c3 import offline_namespaces as ns
from r1.c3 import offline_seccomp as seccomp

ALLOWED_ENV={'PATH','PYTHONPATH','HOME','TMPDIR','PYTHONDONTWRITEBYTECODE',
             'OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS','AR_TRAIN_SEED','AR_SPLIT_SEED'}


class BootstrapStop(RuntimeError): pass


def validate_spec(spec):
    if not isinstance(spec,dict) or set(spec)!={'root','tmpfs_bytes','closure','work_files','argv','env'}:
        raise BootstrapStop('STOP: malformed sandbox specification')
    root=spec['root'];argv=spec['argv'];env=spec['env']
    if not isinstance(root,str) or not Path(root).is_absolute():
        raise BootstrapStop('STOP: private root must be absolute')
    if (not isinstance(argv,list) or not argv or any(not isinstance(a,str) or '\x00' in a for a in argv)
            or not argv[0].startswith('/') or '..' in PurePosixPath(argv[0]).parts):
        raise BootstrapStop('STOP: invalid command')
    if not isinstance(env,dict) or set(env)-ALLOWED_ENV or any(not isinstance(k,str) or not isinstance(v,str) or '\x00' in v for k,v in env.items()):
        raise BootstrapStop('STOP: invalid or unsafe environment')
    if env.get('HOME')!='/work' or env.get('TMPDIR')!='/work' or env.get('PYTHONDONTWRITEBYTECODE')!='1':
        raise BootstrapStop('STOP: private HOME, TMPDIR, and bytecode policy required')
    if not isinstance(spec['closure'],list) or not isinstance(spec['work_files'],list):
        raise BootstrapStop('STOP: explicit closure and working files required')
    if argv[0] not in {entry.get('target') for entry in spec['closure'] if isinstance(entry,dict)}:
        raise BootstrapStop('STOP: executable missing from pinned closure')


def close_extra_fds(keep):
    """Close all descriptors except controlled stdio and bootstrap channel."""
    keep=set(keep)|{0,1,2}
    try: fds=[int(p.name) for p in Path('/proc/self/fd').iterdir() if p.name.isdigit()]
    except OSError as exc:raise BootstrapStop('STOP: cannot enumerate descriptors') from exc
    for fd in fds:
        if fd not in keep:
            try:os.close(fd)
            except OSError as exc:
                if exc.errno!=errno.EBADF:raise BootstrapStop('STOP: cannot close inherited descriptor') from exc


def _pid1(spec,channel,parent_pidfd):
    ns.pid_init_parent_guard(parent_pidfd)
    if os.getpid()!=1:raise BootstrapStop('STOP: child is not PID 1 in its namespace')
    root=spec['root']
    mounts.create_root(root,spec['tmpfs_bytes'])
    mounts.mount_closure(root,spec['closure'])
    mounts.populate_work(root,spec['work_files'])
    mounts.mount_pid_proc(root)
    # Ensure proc is the new PID namespace, not the host proc mount.
    status=(Path(root)/'proc/self/status').read_text()
    if not any(line.split()==['NSpid:','1'] for line in status.splitlines()):
        raise BootstrapStop('STOP: private proc does not report PID namespace init')
    os.chroot(root);os.chdir('/work')
    close_extra_fds({channel.fileno(),parent_pidfd})
    caps.drop_and_verify()
    # Recheck after credential/capability setup before dropping the parent
    # descriptor and before any untrusted instruction can execute.
    ns.pid_init_parent_guard(parent_pidfd)
    os.close(parent_pidfd)
    listener=seccomp.install_listener(channel.fileno())
    try:seccomp.send_listener(channel,listener)
    finally:os.close(listener)
    if os.read(channel.fileno(),1)!=b'R':raise BootstrapStop('STOP: supervisor did not acknowledge monitor readiness')
    channel.close()
    os.execve(spec['argv'][0],spec['argv'],dict(spec['env']))


def bootstrap_child(spec,channel_fd,supervisor_pid):
    """Bootstrap entry in the already-cgrouped child; never returns."""
    try:
        validate_spec(spec)
        channel=socket.socket(fileno=channel_fd)
        if not hasattr(os,'pidfd_open'):raise BootstrapStop('STOP: pidfd support required')
        supervisor_pidfd=os.pidfd_open(supervisor_pid,0)
        ns.parent_death_guard(supervisor_pid)
        if os.read(channel_fd,1)!=b'S':raise BootstrapStop('STOP: cgroup handoff failed')
        ns.unshare_bootstrap()
        # User-namespace credential changes may clear PDEATHSIG. Re-arm it
        # against the stable supervisor pidfd after the transition and before
        # opening the pidfd used by the child PID-1 process.
        ns.pid_init_parent_guard(supervisor_pidfd)
        os.close(supervisor_pidfd)
        # Open stable identity before the PID namespace fork; PID-1 inherits it.
        parent_pidfd=os.pidfd_open(os.getpid(),0)
        pid=os.fork()
        if pid==0:
            _pid1(spec,channel,parent_pidfd)
        os.close(parent_pidfd);channel.close()
        _,status=os.waitpid(pid,0)
        os._exit(os.waitstatus_to_exitcode(status) if os.WIFEXITED(status) else 128+os.WTERMSIG(status))
    except BaseException as exc:
        try:os.write(2,('STOP: bootstrap '+type(exc).__name__+': '+str(exc)+'\n').encode())
        except OSError:pass
        os._exit(125)
