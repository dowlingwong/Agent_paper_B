"""M3 Linux supervisor candidate; not connected to production replay.

Unreviewed integration of bootstrap, namespaces, private root, seccomp listener
and cgroup monitoring. NEVER use as evidence of offline isolation until the
full design, exact syscall list, crash safety and Linux/site qualification have
passed independent review. Existing OpenML replay STOP remains unchanged.

9 Nov 2026 revision (MAC_M3_OVERNIGHT_HANDOFF_20261109.md):

* child creation: one raw ``clone3(CLONE_PIDFD | CLONE_INTO_CGROUP)``
  (``offline_launcher``) replaces ``os.fork()`` + numeric ``cgroup.procs``
  write; no at-fork callback runs in the supervisor and the pidfd is the
  kernel's, so the reviewed child-identity sequence cannot occur;
* withdrawn notifications: PID 1 is a trusted sentinel that keeps the filter
  alive after the workload tree is reaped; the supervisor then drains the
  listener (``offline_seccomp.drain_withdrawn``) and STOPs on any residue;
* HUP: a listener hang-up before the drain is a STOP; after a clean drain it
  is the required sign that the filter's last user is gone, and completion
  requires it together with the pidfd exit and an empty cgroup.
"""
from __future__ import annotations
import errno
import json
import os
from pathlib import Path
import platform
import select
import signal
import socket
import time

import hashlib
import sys

from r1.c3 import offline_bootstrap as boot
from r1.c3 import offline_cgroup as groups
from r1.c3 import offline_launcher as launcher
from r1.c3.offline_runtime_closure import closure_digest
from r1.c3 import offline_seccomp as seccomp

BOOTSTRAP_ENTRY=Path(__file__).resolve().with_name('offline_bootstrap_entry.py')
HUP_GRACE_SECONDS=5


class SupervisorStop(RuntimeError): pass


def _write_all(fd,data):
    offset=0
    while offset<len(data):
        n=os.write(fd,data[offset:])
        if n<=0:raise SupervisorStop('STOP: short control/audit write')
        offset+=n


def _record(audit_fd,event):
    _write_all(audit_fd,(json.dumps(event,sort_keys=True)+'\n').encode())
    os.fsync(audit_fd)


def _group_empty(group):
    os.lseek(group.events_fd,0,os.SEEK_SET)
    text=os.read(group.events_fd,4096).decode('ascii')
    values={line.split()[0]:line.split()[1] for line in text.splitlines() if len(line.split())==2}
    if values.get('populated') not in ('0','1'):raise SupervisorStop('STOP: cgroup population unavailable')
    return values['populated']=='0'


def _wait_empty(group,seconds=5):
    end=time.monotonic()+seconds
    while not _group_empty(group):
        if time.monotonic()>=end:raise SupervisorStop('STOP: cgroup did not become empty')
        time.sleep(.05)


def _kill_and_reap(group,pid,pidfd,waited,*,wait=None):
    """Bounded fail-closed teardown; retain an explicit error for every failure.

    Reaping is by pidfd only (never by numeric PID), so it cannot reap or
    misattribute another process.
    """
    wait=wait or launcher.wait_pidfd
    failures=[]
    if group is not None:
        try:group.kill()
        except BaseException as exc:failures.append(f'cgroup kill: {exc}')
    if pidfd is not None:
        try:signal.pidfd_send_signal(pidfd,signal.SIGKILL)
        except OSError as exc:
            if exc.errno!=errno.ESRCH:failures.append(f'pidfd signal: {exc}')
    if pidfd is not None and not waited:
        deadline=time.monotonic()+5
        while True:
            try:result=wait(pidfd)
            except ChildProcessError:
                failures.append('bootstrap is not a waitable child');break
            except OSError as exc:
                failures.append(f'bootstrap wait: {exc}');break
            if result is not None:break
            if time.monotonic()>=deadline:
                failures.append('bootstrap did not exit');break
            time.sleep(.05)
    elif pid is not None and pidfd is None and not waited:
        failures.append('bootstrap identity unavailable for reaping')
    if group is not None:
        try:_wait_empty(group)
        except BaseException as exc:failures.append(f'cgroup drain: {exc}')
    if failures:raise SupervisorStop('STOP: teardown not verified: '+'; '.join(failures))


def _write_spec(out,spec):
    raw=json.dumps(spec,sort_keys=True,separators=(',',':')).encode('utf-8')
    path=out/'bootstrap_spec.json'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC|os.O_NOFOLLOW,0o600)
    try:
        _write_all(fd,raw);os.fsync(fd)
    finally:os.close(fd)
    return path,hashlib.sha256(raw).hexdigest()


def bootstrap_argv(spec_path,spec_sha,channel_fd,supervisor_pid):
    exe=sys.executable
    if not exe or not os.path.isabs(exe):raise SupervisorStop('STOP: absolute interpreter path required')
    return exe,[exe,'-I','-S','-B',str(BOOTSTRAP_ENTRY),'--channel-fd',str(channel_fd),
                '--spec',str(spec_path),'--spec-sha256',spec_sha,'--supervisor-pid',str(supervisor_pid)]


def _file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def bootstrap_identity(exe):
    """Interpreter and trusted bootstrap sources the clone3 child execs (audit only)."""
    here=Path(__file__).resolve().parent
    names=('offline_bootstrap_entry.py','offline_bootstrap.py','offline_capabilities.py',
           'offline_mounts.py','offline_namespaces.py','offline_seccomp.py','__init__.py')
    sources={n:_file_sha(here/n) for n in names}
    sources['../__init__.py']=_file_sha(here.parent/'__init__.py')   # r1/__init__.py, run by the entry
    return {'interpreter':os.path.realpath(exe),'interpreter_sha256':_file_sha(os.path.realpath(exe)),
            'sources_sha256':sources}


def spec_content_digest(spec):
    """Digest of what the boundary run executes, independent of host source paths and of
    the per-run private root: closure and working-file targets with their hashes, argv,
    env and tmpfs size."""
    payload={'closure':sorted([i['target'],i['sha256']] for i in spec['closure']),
             'work_files':sorted([i['target'],i['sha256']] for i in spec['work_files']),
             'argv':list(spec['argv']),'env':dict(sorted(spec['env'].items())),
             'tmpfs_bytes':spec['tmpfs_bytes']}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _read_exact(sock,n):
    data=b''
    while len(data)<n:
        chunk=sock.recv(n-len(data))
        if not chunk:raise SupervisorStop('STOP: sentinel channel closed before drain')
        data+=chunk
    return data


def _await_hup(listener,group,audit_fd,seconds):
    """After pidfd exit: the filter's last user must be gone (listener HUP)."""
    poller=select.poll();poller.register(listener,select.POLLIN|select.POLLERR|select.POLLHUP)
    events=poller.poll(int(seconds*1000))
    if any(mask&select.POLLIN for _,mask in events):
        observed=seccomp.monitor_one(listener,group.kill_fd,audit_fd)
        raise SupervisorStop(f"STOP: prohibited syscall {observed['syscall']} after drain")
    if not any(mask&select.POLLHUP for _,mask in events) or any(mask&(select.POLLERR|select.POLLNVAL) for _,mask in events):
        raise SupervisorStop('STOP: filter users remain after bootstrap exit')


def monitor(listener,pidfd,channel,group,audit_fd,deadline,*,state=None,drain=None,wait=None,
            hup_grace=HUP_GRACE_SECONDS):
    """Event loop after the monitor is ready; returns the completion record.

    Order of checks per poll batch: listener readable (a received prohibited
    call: STOP), listener error, sentinel message (drain), listener HUP, pidfd.
    """
    drain=drain or seccomp.drain_withdrawn;wait=wait or launcher.wait_pidfd
    state=state if state is not None else {}
    state['waited']=False
    poller=select.poll()
    poller.register(listener,select.POLLIN|select.POLLERR|select.POLLHUP)
    poller.register(pidfd,select.POLLIN|select.POLLERR|select.POLLHUP)
    poller.register(channel.fileno(),select.POLLIN|select.POLLERR|select.POLLHUP)
    chan=channel.fileno()
    drained=None;hup_seen=False;workload_status=None;listener_registered=True;channel_registered=True
    while True:
        remaining=deadline-time.monotonic()
        if remaining<=0:raise SupervisorStop('STOP: workload timeout')
        events=poller.poll(max(1,int(remaining*1000)))
        masks={}
        for fd,mask in events:masks[fd]=masks.get(fd,0)|mask
        lmask=masks.get(listener,0) if listener_registered else 0
        cmask=masks.get(chan,0) if channel_registered else 0
        pmask=masks.get(pidfd,0)
        if lmask&select.POLLIN:
            observed=seccomp.monitor_one(listener,group.kill_fd,audit_fd)
            raise SupervisorStop(f"STOP: prohibited syscall {observed['syscall']}")
        if lmask&(select.POLLERR|select.POLLNVAL):
            raise SupervisorStop('STOP: listener error; monitor health is not established')
        if cmask:
            if drained is not None:raise SupervisorStop('STOP: unexpected sentinel message after drain')
            if not cmask&select.POLLIN:raise SupervisorStop('STOP: sentinel channel error before drain')
            message=_read_exact(channel,2)
            if message[:1]!=b'W':raise SupervisorStop('STOP: invalid sentinel message')
            workload_status=message[1]
            drained=drain(listener,deadline=deadline)
            _record(audit_fd,{'event':'withdrawn_drain','withdrawn':drained['withdrawn'],
                              'pending':drained['pending'],'workload_status':workload_status})
            if drained['withdrawn'] or drained['pending']:
                raise SupervisorStop(f"STOP: prohibited syscall attempt withdrawn before receipt "
                                     f"(withdrawn={drained['withdrawn']}, pending={len(drained['pending'])})")
            channel.sendall(b'D')
            poller.unregister(chan);channel_registered=False
            continue
        if lmask&select.POLLHUP:
            if drained is None:
                raise SupervisorStop('STOP: listener hangup before sentinel drain; withdrawn attempts unobservable')
            hup_seen=True
            poller.unregister(listener);listener_registered=False
        if pmask&(select.POLLERR|select.POLLHUP|select.POLLNVAL):
            raise SupervisorStop('STOP: bootstrap pidfd error or hangup')
        if pmask&select.POLLIN:
            if drained is None:raise SupervisorStop('STOP: bootstrap exited before sentinel drain')
            result=wait(pidfd)
            if result is None:raise SupervisorStop('STOP: pidfd readiness did not yield the bootstrap child')
            state['waited']=True
            _wait_empty(group)
            if not hup_seen:_await_hup(listener,group,audit_fd,hup_grace)
            exited=result.si_code==os.CLD_EXITED
            if not exited or result.si_status!=0 or workload_status!=0:
                raise SupervisorStop('STOP: bootstrap/workload failed')
            _record(audit_fd,{'event':'process_tree_exited','status':0,'withdrawn':0})
            return {'status':'COMPLETE_UNQUALIFIED','waited':True}
        if not events:continue
        if not (lmask or cmask or pmask):
            raise SupervisorStop('STOP: unexpected poll event')


def supervise(spec,delegated,out,*,protected_roots,timeout_seconds=300,bootstrap_seconds=30):
    """Run a future qualified workload under the candidate boundary.

    Code remains unused by replay and must not be treated as qualified. `out`
    must be new and outside the explicitly supplied preserved input roots.
    Synthetic-only qualification is a separate
    authorization, and Linux host capabilities remain independently verified.
    """
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):
        raise SupervisorStop('STOP: Linux x86-64 required')
    if type(timeout_seconds) not in (int,float) or not 0<timeout_seconds<=86400:
        raise SupervisorStop('STOP: finite bounded timeout required')
    if type(bootstrap_seconds) not in (int,float) or not 0<bootstrap_seconds<=300:
        raise SupervisorStop('STOP: finite bootstrap timeout required')
    try:
        if len(list(Path('/proc/self/task').iterdir()))!=1:
            raise SupervisorStop('STOP: supervisor must be single threaded before clone3')
    except OSError as exc:raise SupervisorStop('STOP: supervisor thread count unavailable') from exc
    out=Path(out)
    if not out.is_absolute() or out.exists():raise SupervisorStop('STOP: output must be a new absolute path')
    if not isinstance(protected_roots,(list,tuple)) or not protected_roots:
        raise SupervisorStop('STOP: preserved input roots must be explicit')
    for raw in protected_roots:
        root_path=Path(raw)
        if not root_path.is_absolute() or not root_path.exists():
            raise SupervisorStop('STOP: invalid preserved input root')
        if out.resolve().is_relative_to(root_path.resolve()):
            raise SupervisorStop('STOP: output inside preserved input root')
    out.mkdir(mode=0o700)
    root=out/'root';root.mkdir(mode=0o700)
    spec={**spec,'root':str(root)};boot.validate_spec(spec)
    open_flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC|os.O_NOFOLLOW
    log_fd=os.open(out/'bootstrap.log',open_flags,0o600)
    audit_fd=os.open(out/'supervisor.jsonl',open_flags,0o600)
    null_fd=os.open(os.devnull,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    parent=child=None;group=None;pidfd=listener=None;pid=None;state={'waited':False}
    try:
        spec_path,spec_sha=_write_spec(out,spec)
        group=groups.PrivateCgroup.create(delegated)
        parent,child=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
        exe,argv=bootstrap_argv(spec_path,spec_sha,child.fileno(),os.getpid())
        identity_before=bootstrap_identity(exe)   # hashed before the child can exec them
        pid,pidfd=launcher.spawn_into_cgroup(group.directory_fd,exe,argv,{},
                                             stdio=(null_fd,log_fd,log_fd),pass_fds=(child.fileno(),))
        child.close();child=None
        launcher.verify_membership(pid,pidfd,group.path.name,full_path=str(group.path))
        _record(audit_fd,{'event':'group_bound','pid':pid,'cgroup':str(group.path),
                          'creation':'clone3_pidfd_into_cgroup','spec_sha256':spec_sha,
                          'bootstrap':identity_before})
        parent.sendall(b'S');parent.settimeout(bootstrap_seconds)
        listener=seccomp.receive_listener(parent)
        seccomp.verify_listener(listener)
        _record(audit_fd,{'event':'listener_ready','pid':pid})
        parent.sendall(b'R');parent.settimeout(bootstrap_seconds)
        deadline=time.monotonic()+timeout_seconds
        monitor(listener,pidfd,parent,group,audit_fd,deadline,state=state)
        return {'status':'COMPLETE_UNQUALIFIED','audit':str(out/'supervisor.jsonl'),
                'cgroup':str(group.path),'withdrawn_drain':'clean',
                'spec_sha256':spec_sha,'spec_content_sha256':spec_content_digest(spec),
                'runtime_closure_sha256':closure_digest(spec['closure']),
                'scope':'candidate_not_replay_authorization'}
    except BaseException as original:
        if parent is not None:
            parent.close();parent=None
        try:_kill_and_reap(group,pid,pidfd,state['waited'])
        except SupervisorStop as cleanup:raise cleanup from original
        raise
    finally:
        for s in (parent,child):
            if s is not None:s.close()
        for fd in (listener,pidfd,null_fd,log_fd,audit_fd):
            if fd is not None:os.close(fd)
        if group is not None:group.close()
