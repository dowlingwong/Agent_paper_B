"""Cooperative B1 GPU lease; no model or server operations here."""
import fcntl
import os
import stat
from pathlib import Path


class B1LeaseStop(RuntimeError):
    pass


def acquire(path):
    """Take the existing shared flock (or create its regular file) nonblocking."""
    path=Path(path)
    flags=os.O_RDWR | os.O_CREAT | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_CLOEXEC',0)
    try:
        fd=os.open(path,flags,0o600)
    except OSError as exc:
        raise B1LeaseStop('STOP: cannot open B1 GPU lock') from exc
    try:
        info=os.fstat(fd); named=os.stat(path,follow_symlinks=False)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid() or
                (info.st_dev,info.st_ino)!=(named.st_dev,named.st_ino)):
            raise B1LeaseStop('STOP: B1 GPU lock identity invalid')
        try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc: raise B1LeaseStop('STOP: B1 GPU lock is held') from exc
        return fd
    except BaseException:
        os.close(fd)
        raise


def verify_server_fd(fd, pid, proc_root='/proc'):
    """Require the spawned server still to hold the inherited lock descriptor."""
    try:
        ours=os.fstat(fd);child=os.stat(Path(proc_root)/str(pid)/'fd'/str(fd))
    except OSError as exc:
        raise B1LeaseStop('STOP: B1 server lock descriptor is unobservable') from exc
    if (ours.st_dev,ours.st_ino)!=(child.st_dev,child.st_ino):
        raise B1LeaseStop('STOP: B1 server lock descriptor identity differs')
