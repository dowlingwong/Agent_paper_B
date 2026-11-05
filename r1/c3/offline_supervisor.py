"""M3 Linux supervisor candidate; not connected to production replay.

Unreviewed integration of bootstrap, namespaces, private root, seccomp listener
and cgroup monitoring. NEVER use as evidence of offline isolation until the
full design, exact syscall list, crash safety and Linux/site qualification have
passed independent review. Existing OpenML replay STOP remains unchanged.
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

from r1.c3 import offline_bootstrap as boot
from r1.c3 import offline_cgroup as groups
from r1.c3 import offline_seccomp as seccomp


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


def _kill_and_reap(group,pid,pidfd,waited):
    """Bounded fail-closed teardown; retain an explicit error for every failure."""
    failures=[]
    if group is not None:
        try:group.kill()
        except BaseException as exc:failures.append(f'cgroup kill: {exc}')
    if pidfd is not None:
        try:signal.pidfd_send_signal(pidfd,signal.SIGKILL)
        except OSError as exc:
            if exc.errno!=errno.ESRCH:failures.append(f'pidfd signal: {exc}')
    if pid is not None and not waited:
        deadline=time.monotonic()+5
        while True:
            try:done,_=os.waitpid(pid,os.WNOHANG)
            except ChildProcessError:done=pid
            if done==pid:break
            if time.monotonic()>=deadline:
                failures.append('bootstrap did not exit');break
            time.sleep(.05)
    if group is not None:
        try:_wait_empty(group)
        except BaseException as exc:failures.append(f'cgroup drain: {exc}')
    if failures:raise SupervisorStop('STOP: teardown not verified: '+'; '.join(failures))


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
            raise SupervisorStop('STOP: supervisor must be single threaded before fork')
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
    parent=child=None;group=None;pidfd=listener=None;pid=None;waited=False
    try:
        group=groups.PrivateCgroup.create(delegated)
        parent,child=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
        supervisor_pid=os.getpid();pid=os.fork()
        if pid==0:
            try:
                parent.close()
                os.dup2(null_fd,0);os.dup2(log_fd,1);os.dup2(log_fd,2)
                boot.bootstrap_child(spec,child.fileno(),supervisor_pid)
            finally:os._exit(125)
        child.close();child=None
        pidfd=group.add_own_child(pid)
        _record(audit_fd,{'event':'group_bound','pid':pid,'cgroup':str(group.path)})
        parent.sendall(b'S');parent.settimeout(bootstrap_seconds)
        listener=seccomp.receive_listener(parent)
        seccomp.verify_listener(listener)
        _record(audit_fd,{'event':'listener_ready','pid':pid})
        parent.sendall(b'R');parent.close();parent=None
        poller=select.poll();poller.register(listener,select.POLLIN|select.POLLERR|select.POLLHUP)
        poller.register(pidfd,select.POLLIN|select.POLLERR|select.POLLHUP)
        deadline=time.monotonic()+timeout_seconds
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise SupervisorStop('STOP: workload timeout')
            events=poller.poll(max(1,int(remaining*1000)))
            if any(fd==listener and mask&select.POLLIN for fd,mask in events):
                observed=seccomp.monitor_one(listener,group.kill_fd,audit_fd)
                raise SupervisorStop(f"STOP: prohibited syscall {observed['syscall']}")
            if any(fd==listener and mask&(select.POLLERR|select.POLLHUP) for fd,mask in events):
                raise SupervisorStop('STOP: listener error or hangup; monitor health is not established')
            if any(fd==pidfd for fd,_ in events):
                _,status=os.waitpid(pid,0);waited=True
                _wait_empty(group)
                if not os.WIFEXITED(status) or os.WEXITSTATUS(status)!=0:
                    raise SupervisorStop('STOP: bootstrap/workload failed')
                _record(audit_fd,{'event':'process_tree_exited','status':0})
                return {'status':'COMPLETE_UNQUALIFIED','audit':str(out/'supervisor.jsonl'),
                        'cgroup':str(group.path),'scope':'candidate_not_replay_authorization'}
            if any(fd==listener for fd,_ in events):
                raise SupervisorStop('STOP: listener failed before process completion')
    except BaseException as original:
        if parent is not None:
            parent.close();parent=None
        try:_kill_and_reap(group,pid,pidfd,waited)
        except SupervisorStop as cleanup:raise cleanup from original
        raise
    finally:
        for s in (parent,child):
            if s is not None:s.close()
        for fd in (listener,pidfd,null_fd,log_fd,audit_fd):
            if fd is not None:os.close(fd)
        if group is not None:group.close()
