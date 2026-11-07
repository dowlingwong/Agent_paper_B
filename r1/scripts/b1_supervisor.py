#!/usr/bin/env python3
"""Cooperative, lease-owning B1 supervisor. Never auto-retries a STOP.

Invoke only after the author gate, host ownership, site qualification and the
reviewed Track S/P handover. This launcher does not prove those external facts.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import uuid

REPO=Path(__file__).resolve().parents[2]
ENTRY=REPO/'r1/exam/b1_supervised_entry.py'


def _exclusive_json(path, value):
    data=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        view=memoryview(data)
        while view:
            n=os.write(fd,view)
            if n<=0: raise OSError('short exclusive JSON write')
            view=view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _retain_on_stop(live_fd, directory, original):
    """Request guardian freeze, record best effort and retain inherited lease."""
    try: os.write(live_fd,b'S')
    except OSError: pass
    try:
        _exclusive_json(directory/'SUPERVISOR_STOP.json',{
            'status':'STOPPED','error':f'{type(original).__name__}: {original}'})
    except Exception as record_error:
        try: print(f'STOP: supervisor receipt failed: {record_error}',file=sys.stderr,flush=True)
        except Exception: pass
    # Do not close the lease or signal the child. Author/operator reviews the
    # STOP scene. The guardian monitors this live FD and the supervisor pidfd.
    while True:
        try: time.sleep(3600)
        except BaseException: pass


def _same_inherited_fd(child_pid, fd, label):
    from r1.exam.cooperative_lease import kcmp_file_result
    ours=os.fstat(fd);child=os.stat(Path('/proc')/str(child_pid)/'fd'/str(fd))
    if (ours.st_dev,ours.st_ino)!=(child.st_dev,child.st_ino):
        raise RuntimeError(f'STOP: runner inherited {label} inode differs')
    rc,err=kcmp_file_result(os.getpid(),child_pid,fd,fd)
    if rc!=0: raise RuntimeError(f'STOP: runner inherited {label} OFD unproved (rc={rc}, errno={err})')


def _publish_or_reconcile(child, out, head):
    """Treat a verified retirement as the completion point after a callback.

    Both readers and this reconciliation require the same committed sentinel
    and receipt. This is not proof under arbitrary storage or concurrent STOP
    failures; an independent review must establish the allowed fault model.
    """
    from r1.exam.b1_exit_receipt import publish_after_wait, verify_waited_success
    try:
        publish_after_wait(child,out,head)
    except BaseException:
        verify_waited_success(out,head)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    from r1.exam.runtime import load_config,require_committed_b1_config,host_check,author_gate
    from r1.exam.analyze import load_rule
    from r1.exam.b1_lease import acquire
    from r1.exam.cache_proc import process_start_ticks
    cfg=load_config(args.config)
    if cfg.get('dryrun'): raise RuntimeError('STOP: supervisor is production B1 only')
    head=require_committed_b1_config(args.config,cfg)
    rule,rule_sha=load_rule(cfg['rule'],cfg['rule_sha256'])
    if rule.get('version')!='x5_rule/v2' or author_gate(cfg,'b1',rule_sha)!=head:
        raise RuntimeError('STOP: B1 supervisor author/config HEAD differs')
    out=Path(args.out)
    if not out.is_absolute() or out!=out.resolve() or out.parent!=Path(cfg['work_dir']) or os.path.lexists(out):
        raise RuntimeError('STOP: B1 output must be a fresh unaliased direct work child')
    host_check(cfg,out)
    # The requested batch does not exist yet; check its actual containing
    # work directory before acquiring the GPU lease or starting the runner.
    # The runner must recheck the new batch itself before starting workload.
    from r1.exam.b1_exit_receipt import _require_local_filesystem
    _require_local_filesystem(out.parent)
    # Handover and site qualification are external reviewed prerequisites;
    # this code does not infer them from an output path or a lock.
    supervisor_dir=out.parent/('b1-supervisor-'+time.strftime('%Y%m%d')+'-'+uuid.uuid4().hex)
    supervisor_dir.mkdir(mode=0o700,exist_ok=False)
    _exclusive_json(supervisor_dir/'SUPERVISOR.json',{'head':head,'out':str(out),'pid':os.getpid(),
                    'start_ticks':process_start_ticks(os.getpid())})
    lease_fd=acquire(Path.home()/'r1_locks'/'gpu0.lock')
    supervisor_pidfd=os.pidfd_open(os.getpid(),0)
    live_r,live_w=os.pipe();grant_r,grant_w=os.pipe();exec_r,exec_w=os.pipe()
    log=(supervisor_dir/'runner.log').open('xb',buffering=0)
    env=dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1',R1_B1_SUPERVISOR_PID=str(os.getpid()),
               R1_B1_SUPERVISOR_TICKS=str(process_start_ticks(os.getpid())),
               R1_B1_SUPERVISOR_PIDFD=str(supervisor_pidfd),R1_B1_SUPERVISOR_LIVE_FD=str(live_r),
               R1_B1_LEASE_FD=str(lease_fd))
    command=[sys.executable,'-B',str(REPO/'r1/scripts/exam_runner.py'),'b1',
             '--config',str(Path(args.config)),'--out',str(out)]
    child=None
    try:
        argv=[sys.executable,'-I','-S','-B',str(ENTRY),str(grant_r),str(log.fileno()),str(exec_w),*command]
        child=subprocess.Popen(argv,env=env,cwd=REPO,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True,
                               pass_fds=(grant_r,log.fileno(),exec_w,lease_fd,supervisor_pidfd,live_r))
        os.close(grant_r);grant_r=None;os.close(exec_w);exec_w=None
        for fd,label in ((lease_fd,'lease'),(supervisor_pidfd,'supervisor pidfd'),(live_r,'STOP channel')):
            _same_inherited_fd(child.pid,fd,label)
        _exclusive_json(supervisor_dir/'RUNNER.json',{'pid':child.pid,'start_ticks':process_start_ticks(child.pid),'head':head})
        if os.write(grant_w,b'G')!=1: raise RuntimeError('STOP: supervisor grant incomplete')
        os.close(grant_w);grant_w=None
        readable,_,_=select.select([exec_r],[],[],10)
        if not readable or os.read(exec_r,1)!=b'': raise RuntimeError('STOP: runner exec not observed')
        status=child.wait()
        if status!=0: raise RuntimeError(f'STOP: B1 runner exited {status}')
        from r1.exam.b1_finalization import verify_finalization
        verify_finalization(out,head)
        # This independently supervised receipt is a separate implementation;
        # absence or any failure must STOP before the lease is released.
        # The receipt helper's last operation atomically retires ACTIVE. Once
        # that happens this process must not turn a published success into a
        # STOP. Suppress asynchronous Python signal handlers across that point;
        # SIGKILL remains subject to the documented atomic-rename fault model.
        signal.pthread_sigmask(signal.SIG_BLOCK, signal.valid_signals() - {signal.SIGKILL, signal.SIGSTOP})
        _publish_or_reconcile(child,out,head)
        # No fallible success step follows. Process exit releases the lease.
        return 0
    except BaseException as exc:
        _retain_on_stop(live_w,supervisor_dir,exc)
    finally:
        for fd in (live_r,grant_r,grant_w,exec_r,exec_w,supervisor_pidfd):
            if fd is not None:
                try: os.close(fd)
                except BaseException: pass
        try: log.close()
        except BaseException: pass


if __name__=='__main__':
    raise SystemExit(main())
