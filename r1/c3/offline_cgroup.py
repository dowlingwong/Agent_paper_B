"""Linux cgroup-v2 primitives for the M3 offline supervisor candidate.

This component creates and retains an empty uniquely named delegated cgroup;
it has no replay caller and does not establish namespace, mount, seccomp,
process-tree, or supervisor crash-safety guarantees. Production STOP stays.
"""
from __future__ import annotations
import ctypes
import os
from pathlib import Path
import platform
import select
import signal
import uuid

CGROUP2_SUPER_MAGIC=0x63677270


class CgroupStop(RuntimeError):
    pass


def _require_cgroup_v2(path):
    if platform.system()!='Linux': raise CgroupStop('STOP: cgroup-v2 requires Linux')
    libc=ctypes.CDLL(None,use_errno=True)
    # Oversized native buffer: the first long of Linux struct statfs is f_type.
    data=(ctypes.c_long*64)()
    if libc.statfs(os.fsencode(path),ctypes.byref(data))!=0:
        raise CgroupStop('STOP: cannot inspect cgroup filesystem')
    if data[0] != CGROUP2_SUPER_MAGIC: raise CgroupStop('STOP: not a cgroup-v2 filesystem')


def _open_control(directory_fd,name,flags):
    return os.open(name,flags|os.O_CLOEXEC|os.O_NOFOLLOW,dir_fd=directory_fd)


class PrivateCgroup:
    """Own a new cgroup and its opened descriptors; it is never removed here."""
    def __init__(self, path, directory_fd, procs_fd, kill_fd, events_fd=None):
        self.path=Path(path);self.directory_fd=directory_fd
        self.procs_fd=procs_fd;self.kill_fd=kill_fd;self.events_fd=events_fd

    @classmethod
    def create(cls, delegated):
        delegated=Path(delegated)
        _require_cgroup_v2(delegated)
        flags=os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC|os.O_NOFOLLOW
        root_fd=os.open(delegated,flags)
        child_fd=procs_fd=kill_fd=events_fd=None
        try:
            root_stat=os.fstat(root_fd)
            if root_stat.st_uid!=os.geteuid(): raise CgroupStop('STOP: delegated cgroup is not owned by this user')
            name='paper-b-m3-'+uuid.uuid4().hex
            os.mkdir(name,0o700,dir_fd=root_fd)
            child_fd=os.open(name,flags,dir_fd=root_fd)
            type_fd=_open_control(child_fd,'cgroup.type',os.O_RDONLY)
            try: cgroup_type=os.read(type_fd,100).decode().strip()
            finally: os.close(type_fd)
            if cgroup_type!='domain': raise CgroupStop('STOP: cgroup is not a domain')
            procs_fd=_open_control(child_fd,'cgroup.procs',os.O_WRONLY)
            kill_fd=_open_control(child_fd,'cgroup.kill',os.O_WRONLY)
            events_fd=_open_control(child_fd,'cgroup.events',os.O_RDONLY)
            result=cls(delegated/name,child_fd,procs_fd,kill_fd,events_fd)
            child_fd=procs_fd=kill_fd=events_fd=None
            return result
        finally:
            os.close(root_fd)
            for fd in (child_fd,procs_fd,kill_fd,events_fd):
                if fd is not None: os.close(fd)

    def add_own_child(self,pid):
        """Move only a live child of this supervisor, retaining a pidfd.

        Caller keeps the child blocked on a private bootstrap handshake before
        this call and must retain the returned pidfd through teardown. A held
        pidfd retains the process identity; failed verification is STOP.
        """
        if type(pid) is not int or pid<=0: raise CgroupStop('STOP: invalid child pid')
        if (not all(hasattr(os,name) for name in ('pidfd_open','P_PIDFD','waitid','WEXITED','WNOHANG','WNOWAIT'))
                or not hasattr(signal,'pidfd_send_signal')):
            raise CgroupStop('STOP: pidfd support required')
        try:
            pidfd=os.pidfd_open(pid,0)
        except OSError as exc: raise CgroupStop('STOP: cannot acquire child pidfd') from exc
        assignment_attempted=False;success=False
        try:
            # P_PIDFD + WNOWAIT confirms parent-child relationship without reaping.
            exited=os.waitid(os.P_PIDFD,pidfd,os.WEXITED|os.WNOHANG|os.WNOWAIT)
            if exited is not None: raise CgroupStop('STOP: child already exited')
            poller=select.poll();poller.register(pidfd,select.POLLIN)
            if poller.poll(0): raise CgroupStop('STOP: child exited before cgroup assignment')
            data=f'{pid}\n'.encode('ascii')
            assignment_attempted=True
            if os.write(self.procs_fd,data)!=len(data): raise CgroupStop('STOP: cgroup assignment failed')
            if poller.poll(0): raise CgroupStop('STOP: child exited during cgroup assignment')
            text=Path(f'/proc/{pid}/cgroup').read_text()
            matches=[line.split('::',1)[1] for line in text.splitlines() if line.startswith('0::')]
            if len(matches)!=1 or Path(matches[0]).name!=self.path.name:
                raise CgroupStop('STOP: child cgroup membership not verified')
            result=pidfd;pidfd=None;success=True
            return result
        except (OSError,ChildProcessError) as exc:
            raise CgroupStop('STOP: child ownership or cgroup membership unavailable') from exc
        finally:
            try:
                if assignment_attempted and not success:
                    try: self.kill()
                    finally: signal.pidfd_send_signal(pidfd,signal.SIGKILL)
            finally:
                if pidfd is not None: os.close(pidfd)

    def kill(self):
        """Kill only descendants of this fresh cgroup, on a supervisor STOP."""
        if os.write(self.kill_fd,b'1\n')!=2: raise CgroupStop('STOP: cgroup kill failed')

    def close(self):
        for name in ('procs_fd','kill_fd','events_fd','directory_fd'):
            fd=getattr(self,name,None)
            if fd is not None:
                os.close(fd);setattr(self,name,None)
