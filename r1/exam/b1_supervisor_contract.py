"""Cooperative inherited supervisor/lease contract for production B1."""
import os
from pathlib import Path
import select

from r1.exam.b1_lease import adopt_inherited
from r1.exam.cache_proc import process_start_ticks


class SupervisorStop(RuntimeError):
    pass


def require_supervisor(environ=None):
    env=os.environ if environ is None else environ
    names=('R1_B1_SUPERVISOR_PID','R1_B1_SUPERVISOR_TICKS','R1_B1_SUPERVISOR_PIDFD',
           'R1_B1_SUPERVISOR_LIVE_FD','R1_B1_LEASE_FD','R1_B1_GUARDIAN_HANDOFF_FD')
    try:
        values=[]
        for name in names:
            raw=env[name]
            if not isinstance(raw,str) or not raw.isdecimal() or str(int(raw))!=raw:
                raise ValueError('noncanonical decimal')
            values.append(int(raw))
        pid,ticks,pidfd,live_fd,lease_fd,handoff_fd=values
        if pid<=0 or ticks<=0 or min(pidfd,live_fd,lease_fd,handoff_fd)<3 or len({pidfd,live_fd,lease_fd,handoff_fd})!=4:
            raise ValueError('invalid supervisor fields')
        if os.getppid()!=pid or process_start_ticks(pid)!=ticks:
            raise ValueError('parent identity differs')
        info=Path('/proc/self/fdinfo')/str(pidfd)
        pids=[line.split(':',1)[1].strip() for line in info.read_text().splitlines() if line.startswith('Pid:')]
        if pids != [str(pid)]:
            raise ValueError('pidfd does not identify supervisor')
        poll=select.poll()
        for fd in (pidfd,live_fd): poll.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR)
        if poll.poll(0):
            raise ValueError('supervisor died or requested STOP')
        adopt_inherited(lease_fd,Path.home()/'r1_locks'/'gpu0.lock')
    except (KeyError,TypeError,ValueError,OSError) as exc:
        raise SupervisorStop('STOP: inherited supervisor/lease contract unavailable') from exc
    return {'pid':pid,'start_ticks':ticks,'pidfd':pidfd,'live_fd':live_fd,'lease_fd':lease_fd,'handoff_fd':handoff_fd}
