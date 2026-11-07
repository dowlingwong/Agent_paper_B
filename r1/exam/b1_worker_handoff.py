"""B1 worker start handoff under the same-UID cooperative host assumption.

A one-way inherited pipe prevents this worker from entering the campaign until
its spawning runner has recorded it and checked the runner's selected lease,
server and newly created root. It is not a trust boundary against a same-UID
process that forges an entire parent, nor a kernel socket-to-PID proof.
"""
import hashlib
import json
import os
import select
import stat
from pathlib import Path

from r1.exam.cache_proc import process_start_ticks
from r1.exam.cache_runtime import _proc_ppid

HANDOFF_FD_ENV = 'R1_B1_HANDOFF_FD'
LEASE_FD_ENV = 'R1_B1_LEASE_FD'
_MAX_RECORD = 4096


def _digest_job(job):
    return hashlib.sha256(json.dumps(job,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _identity(path):
    info=os.stat(path,follow_symlinks=False)
    return info.st_dev,info.st_ino,info.st_uid,info.st_mode


def make_record(job, child_pid, lease_fd, root, service):
    """Called by the parent after Popen and before releasing the child."""
    from r1.exam.b1_lease import verify_server_fd
    if type(child_pid) is not int or child_pid<=0 or type(lease_fd) is not int or lease_fd<3:
        raise RuntimeError('STOP: B1 handoff child/lease descriptor invalid')
    own=os.fstat(lease_fd)
    lock=Path.home()/'r1_locks'/'gpu0.lock'
    named=os.stat(lock,follow_symlinks=False)
    if (own.st_dev,own.st_ino,own.st_uid)!=(named.st_dev,named.st_ino,named.st_uid) or \
       not stat.S_ISREG(named.st_mode) or named.st_nlink!=1 or named.st_uid!=os.getuid():
        raise RuntimeError('STOP: B1 handoff lease identity mismatch')
    verify_server_fd(lease_fd,child_pid)
    out=Path(root)
    if not out.is_absolute() or out.resolve()!=out or str(out)!=job.get('out'):
        raise RuntimeError('STOP: B1 handoff root path mismatch')
    dev,ino,uid,mode=_identity(out)
    if not stat.S_ISDIR(mode) or uid!=os.getuid():
        raise RuntimeError('STOP: B1 handoff root is not an owned directory')
    record={'version':'b1-worker-handoff/v1','job_sha256':_digest_job(job),
            'parent_pid':os.getpid(),'parent_start_ticks':process_start_ticks(os.getpid()),
            'child_pid':child_pid,'child_start_ticks':process_start_ticks(child_pid),
            'lease_fd':lease_fd,'lease_dev':own.st_dev,'lease_ino':own.st_ino,'lease_uid':own.st_uid,
            'root':str(out),'root_dev':dev,'root_ino':ino,'root_uid':uid,'server':None}
    if service is None:
        if job.get('base_url') is not None:
            raise RuntimeError('STOP: B1 software anchor has unexpected endpoint')
    else:
        server_pid=service.process.pid
        if service.process.poll() is not None or job.get('base_url')!=service.openai_base_url:
            raise RuntimeError('STOP: B1 handoff endpoint differs from current server')
        verify_server_fd(lease_fd,server_pid)
        record['server']={'pid':server_pid,'start_ticks':process_start_ticks(server_pid),
                          'base_url':service.openai_base_url}
    return record


def release(write_fd,record):
    payload=(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    if len(payload)>_MAX_RECORD:
        raise RuntimeError('STOP: B1 handoff record too large')
    if os.write(write_fd,payload)!=len(payload):
        raise RuntimeError('STOP: B1 handoff short write')


def await_parent(job, *, timeout=30):
    """Require parent release and re-observe its finite identity snapshot."""
    raw=os.environ.get(HANDOFF_FD_ENV,'');raw_lease=os.environ.get(LEASE_FD_ENV,'')
    if not raw.isdecimal() or not raw_lease.isdecimal():
        raise RuntimeError('STOP: B1 worker has no inherited handoff or lease')
    fd=int(raw);lease_fd=int(raw_lease)
    if fd<3 or lease_fd<3 or fd==lease_fd:
        raise RuntimeError('STOP: B1 worker handoff descriptors invalid')
    try:
        if not select.select([fd],[],[],timeout)[0]:
            raise RuntimeError('STOP: B1 worker handoff timed out')
        payload=os.read(fd,_MAX_RECORD+1)
    finally:
        os.close(fd)
    try:
        if len(payload)>_MAX_RECORD or not payload.endswith(b'\n'):
            raise ValueError('truncated or oversized handoff')
        record=json.loads(payload)
        if record.get('version')!='b1-worker-handoff/v1' or record.get('job_sha256')!=_digest_job(job):
            raise ValueError('job binding mismatch')
        parent=os.getppid()
        if record.get('parent_pid')!=parent or record.get('child_pid')!=os.getpid():
            raise ValueError('parent/child pid mismatch')
        if record.get('parent_start_ticks')!=process_start_ticks(parent) or record.get('child_start_ticks')!=process_start_ticks(os.getpid()):
            raise ValueError('parent/child lifetime mismatch')
        if record.get('lease_fd')!=lease_fd:
            raise ValueError('inherited lease descriptor mismatch')
        own=os.fstat(lease_fd)
        lock=os.stat(Path.home()/'r1_locks'/'gpu0.lock',follow_symlinks=False)
        parent_fd=os.stat(Path('/proc')/str(parent)/'fd'/str(lease_fd))
        expected=(record['lease_dev'],record['lease_ino'],record['lease_uid'])
        if any((x.st_dev,x.st_ino,x.st_uid)!=expected for x in (own,lock,parent_fd)) or not stat.S_ISREG(lock.st_mode) or lock.st_nlink!=1 or lock.st_uid!=os.getuid():
            raise ValueError('lease descriptor identity mismatch')
        path=Path(job['out']);dev,ino,uid,mode=_identity(path)
        if not path.is_absolute() or path.resolve()!=path or record.get('root')!=str(path) or \
           (dev,ino,uid)!=(record['root_dev'],record['root_ino'],record['root_uid']) or not stat.S_ISDIR(mode) or uid!=os.getuid():
            raise ValueError('campaign root identity mismatch')
        server=record['server']
        if server is None:
            if job.get('base_url') is not None:
                raise ValueError('software anchor endpoint mismatch')
        else:
            pid=server['pid']
            if server['base_url']!=job.get('base_url') or server['base_url']!=os.environ.get('LLAMACPP_BASE_URL'):
                raise ValueError('server endpoint mismatch')
            if server['start_ticks']!=process_start_ticks(pid) or _proc_ppid(pid)!=parent:
                raise ValueError('server lifetime/parent mismatch')
            server_fd=os.stat(Path('/proc')/str(pid)/'fd'/str(lease_fd))
            if (server_fd.st_dev,server_fd.st_ino,server_fd.st_uid)!=expected:
                raise ValueError('server lease descriptor mismatch')
        if os.getppid()!=parent or process_start_ticks(parent)!=record['parent_start_ticks']:
            raise ValueError('parent changed during handoff')
        return record
    except (KeyError,TypeError,ValueError,OSError,json.JSONDecodeError) as exc:
        raise RuntimeError(f'STOP: invalid B1 worker handoff: {exc}') from exc
