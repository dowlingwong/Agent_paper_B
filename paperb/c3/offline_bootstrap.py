"""M3 trusted bootstrap candidate; not connected to production replay.

Runs in a fresh isolated interpreter that the supervisor's clone3 launcher
(``offline_launcher``) execs inside the private cgroup (entry script
``offline_bootstrap_entry.py``). All errors require immediate exit. Linux
kernel and full-boundary review are mandatory before any real workload.

PID 1 of the private PID namespace is this trusted bootstrap, not the workload.
It installs the seccomp filter, starts the workload as its child, reaps every
process in the namespace and then stays alive, still holding the filter, until
the supervisor has drained the listener for notifications withdrawn before
receipt (``offline_seccomp.drain_withdrawn``). Channel protocol after the
listener hand-off: supervisor ``R`` (monitor ready) -> PID 1 ``W<status>``
(workload tree reaped) -> supervisor ``D`` (drain clean) -> PID 1 exits with
the workload status. Without ``D`` PID 1 exits 125.
"""
from __future__ import annotations
import argparse
import codecs
import ctypes
import hashlib
import json
import os
import errno
from pathlib import Path, PurePosixPath
import signal
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
    require_default_signal_dispositions()
    # Keep the workload (same credentials) out of PID 1's /proc fd table and
    # memory; prctl is filtered once the listener exists, so set it now. exec
    # restores dumpability for the workload itself.
    if ctypes.CDLL(None,use_errno=True).prctl(PR_SET_DUMPABLE,0,0,0,0)!=0:
        raise BootstrapStop('STOP: cannot make PID 1 non-dumpable')
    listener=seccomp.install_listener(channel.fileno())
    try:seccomp.send_listener(channel,listener)
    finally:os.close(listener)
    if os.read(channel.fileno(),1)!=b'R':raise BootstrapStop('STOP: supervisor did not acknowledge monitor readiness')
    status=run_workload_as_sentinel(spec,channel)
    os._exit(status)


PR_SET_DUMPABLE=4


def require_default_signal_dispositions():
    """PID 1 must keep every signal at SIG_DFL/SIG_IGN.

    The kernel then drops signals sent to a namespace init from inside the
    namespace, so the workload cannot kill the sentinel and end the filter's
    last user before the drain. A handler would make PID 1 killable.
    """
    for sig in signal.valid_signals():
        if sig in (signal.SIGKILL,signal.SIGSTOP):continue
        try:action=signal.getsignal(sig)
        except (OSError,ValueError):continue
        if action not in (signal.SIG_DFL,signal.SIG_IGN):
            raise BootstrapStop(f'STOP: PID 1 signal {int(sig)} has a handler')


def _status_byte(status):
    if os.WIFEXITED(status):return min(os.WEXITSTATUS(status),255)
    if os.WIFSIGNALED(status):return min(128+os.WTERMSIG(status),255)
    return 255


def run_workload_as_sentinel(spec,channel,*,fork=None,waitpid=None,execve=None):
    """PID-1 loop: start the workload, reap the namespace, hold the filter.

    Returns the exit status PID 1 must use (125 without the supervisor's ``D``).
    Every call here runs under the installed filter and uses only allowed
    system calls (clone without namespace flags, wait4, read, write, close).
    """
    fork=fork or os.fork;waitpid=waitpid or os.waitpid;execve=execve or os.execve
    channel_fd=channel.fileno()
    pid=fork()
    if pid==0:
        try:
            os.close(channel_fd)
            # No inherited SIG_IGN (wider than subprocess's restore_signals,
            # which resets only SIGPIPE/SIGXFSZ) and an empty mask.
            for sig in signal.valid_signals():
                if sig in (signal.SIGKILL,signal.SIGSTOP):continue
                try:
                    if signal.getsignal(sig)==signal.SIG_IGN:signal.signal(sig,signal.SIG_DFL)
                except (OSError,ValueError):pass
            signal.pthread_sigmask(signal.SIG_SETMASK,set())
            execve(spec['argv'][0],spec['argv'],dict(spec['env']))
        finally:os._exit(127)
    workload=None
    while True:
        try:done,status=waitpid(-1,0)
        except ChildProcessError:break
        if done==pid:workload=_status_byte(status)
    if workload is None:return 125
    if os.write(channel_fd,b'W'+bytes([workload]))!=2:return 125
    if os.read(channel_fd,1)!=b'D':return 125
    return workload


def main(argv=None):
    """Entry for the interpreter exec'd by the clone3 launcher; never returns."""
    try:
        # Nothing inherited across the supervisor's execve may stay blocked
        # (a blocked mask would also reach PID 1 and the workload).
        signal.pthread_sigmask(signal.SIG_SETMASK,set())
        signal.signal(signal.SIGINT,signal.SIG_DFL)   # interpreter default handler
        # After chroot no stdlib file is reachable: load every codec the
        # bootstrap uses now (the forked design inherited them preloaded).
        for codec in ('ascii','utf-8','latin-1','idna'):codecs.lookup(codec)
        parser=argparse.ArgumentParser(add_help=False)
        parser.add_argument('--channel-fd',type=int,required=True)
        parser.add_argument('--spec',required=True)
        parser.add_argument('--spec-sha256',required=True)
        parser.add_argument('--supervisor-pid',type=int,required=True)
        args=parser.parse_args(argv)
        fd=os.open(args.spec,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:
            chunks=[]
            while True:
                chunk=os.read(fd,1<<20)
                if not chunk:break
                chunks.append(chunk)
        finally:os.close(fd)
        raw=b''.join(chunks)
        if hashlib.sha256(raw).hexdigest()!=args.spec_sha256:
            raise BootstrapStop('STOP: bootstrap specification hash mismatch')
        spec=json.loads(raw.decode('utf-8'))
    except BaseException as exc:
        try:os.write(2,('STOP: bootstrap entry '+type(exc).__name__+': '+str(exc)+'\n').encode())
        except OSError:pass
        os._exit(125)
    bootstrap_child(spec,args.channel_fd,args.supervisor_pid)


def bootstrap_child(spec,channel_fd,supervisor_pid):
    """Bootstrap in the child that clone3 created inside the cgroup; never returns."""
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
