"""CPU-only tests of GPU-lease accounting and supervisor-death behavior."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import pytest
from r1.scripts import trackp_p3a_guarded as G


def test_completed_fake_gpu_unit_accounts_lease_seconds(tmp_path, monkeypatch):
    fake=tmp_path/"fake.py"; lease=tmp_path/"lease"
    fake.write_text(r"""
import json,os,pathlib,sys,time
a=sys.argv; out=pathlib.Path(a[a.index('--run-dir')+1]); out.mkdir()
lease=pathlib.Path(a[a.index('--lease')+1]); start=time.monotonic()
events=[{'pid':os.getpid(),'event':'start','monotonic_s':start,'tasl7_driver':{'boot_id':'boot'}}]
with lease.open('a') as f: f.write(json.dumps(events[0])+'\n')
time.sleep(.25); end=time.monotonic()
events.append({'pid':os.getpid(),'event':'end','monotonic_s':end,'tasl7_driver':{'boot_id':'boot'}})
with lease.open('a') as f: f.write(json.dumps(events[1])+'\n')
(out/'report.json').write_text('{"score":0.5}')
(out/'manifest.json').write_text(json.dumps({'evidence_label':'DRYRUN','tasl7_driver':{'boot_id':'boot'},'gpu_lease':events}))
""")
    monkeypatch.setattr(G,"SCRIPT",fake); monkeypatch.setattr(G,"verify_live_pins",lambda journal: None)
    monkeypatch.setattr(G.R,"tasl7_driver_snapshot",lambda: {"boot_id":"boot"})
    root=tmp_path/"campaign"; root.mkdir(); budget=G.GPUBudget(limit=10,lease_log=lease)
    G.run_unit(root,root/"journal","boot",budget,"DRYRUN","kev","gpu",["--lease",str(lease)])
    assert .2 <= budget.used < 2


def test_supervisor_death_kills_worker_and_descendant(tmp_path):
    fake=tmp_path/"worker.py"; outer=tmp_path/"supervisor.py"
    worker_pid=tmp_path/"worker.pid"; child_pid=tmp_path/"child.pid"; lease=tmp_path/"lease"
    fake.write_text(r"""
import json,os,pathlib,subprocess,sys,time
a=sys.argv
pathlib.Path(a[a.index('--worker-pid')+1]).write_text(str(os.getpid()))
p=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'])
pathlib.Path(a[a.index('--child-pid')+1]).write_text(str(p.pid))
with pathlib.Path(a[a.index('--lease')+1]).open('a') as f:
 f.write(json.dumps({'pid':os.getpid(),'event':'start','monotonic_s':time.monotonic()})+'\n')
time.sleep(60)
""")
    outer.write_text(r"""
from pathlib import Path
import sys
from r1.scripts import trackp_p3a_guarded as G
root=Path(sys.argv[1]); root.mkdir()
G.SCRIPT=Path(sys.argv[2]); G.verify_live_pins=lambda j: None
G.R.tasl7_driver_snapshot=lambda: {'boot_id':'boot'}
lease=Path(sys.argv[3]); budget=G.GPUBudget(limit=20,lease_log=lease)
G.run_unit(root,root/'journal','boot',budget,'DRYRUN','kev','job',
           ['--lease',str(lease),'--worker-pid',sys.argv[4],'--child-pid',sys.argv[5]])
""")
    env={**os.environ,"PYTHONPATH":str(G.R.REPO),"CUDA_VISIBLE_DEVICES":""}
    sup=subprocess.Popen([sys.executable,str(outer),str(tmp_path/"campaign"),str(fake),str(lease),
                          str(worker_pid),str(child_pid)],env=env)
    try:
        deadline=time.monotonic()+15
        while not child_pid.exists() and time.monotonic()<deadline:
            assert sup.poll() is None
            time.sleep(.1)
        assert child_pid.exists()
        os.kill(sup.pid,signal.SIGKILL); sup.wait(timeout=5)
        for pidfile in (worker_pid,child_pid):
            pid=int(pidfile.read_text()); deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                stat=Path(f"/proc/{pid}/stat")
                if not stat.exists() or stat.read_text().split()[2]=="Z": break
                time.sleep(.1)
            else: pytest.fail(f"process {pid} survived supervisor death")
    finally:
        if sup.poll() is None: sup.kill(); sup.wait()


def test_gate_does_not_exec_before_readiness(tmp_path):
    gate=G.R.REPO/"r1/scripts/trackp_p3a_gate.py"
    marker=tmp_path/"executed"
    read_fd,write_fd=os.pipe()
    command=[sys.executable,str(gate),str(read_fd),sys.executable,"-c",
             f"from pathlib import Path; Path({str(marker)!r}).write_text('ok')"]
    proc=subprocess.Popen(command,pass_fds=(read_fd,))
    os.close(read_fd)
    try:
        time.sleep(.3)
        assert not marker.exists() and proc.poll() is None
        os.write(write_fd,b"1"); os.close(write_fd); write_fd=None
        assert proc.wait(timeout=5)==0 and marker.read_text()=="ok"
    finally:
        if write_fd is not None: os.close(write_fd)
        if proc.poll() is None: proc.kill(); proc.wait()


def test_wrong_fork_parent_is_killed_before_worker_exec(tmp_path):
    marker=tmp_path/"executed"
    code=("from r1.scripts.trackp_p3a_guarded import worker_parent_death_guard; "
          "from pathlib import Path; worker_parent_death_guard(-1); "
          f"Path({str(marker)!r}).write_text('bad')")
    result=subprocess.run([sys.executable,"-c",code],cwd=G.R.REPO,
                          env={**os.environ,"PYTHONPATH":str(G.R.REPO),"CUDA_VISIBLE_DEVICES":""},timeout=5)
    assert result.returncode==-signal.SIGKILL and not marker.exists()


def test_watchdog_kills_even_if_stop_log_is_unwritable(tmp_path,monkeypatch):
    from r1.scripts import trackp_p3a_watchdog as W
    calls=[]
    monkeypatch.setattr(W,"process_state",lambda parent: None)
    monkeypatch.setattr(W.os,"killpg",lambda group,sig: calls.append((group,sig)))
    assert W.watch(123,"identity",456,"/proc/nonexistent-forbidden/stop.log",0,tmp_path/"lease",0,1)==2
    assert calls==[(456,signal.SIGKILL)]


def test_stopped_supervisor_does_not_bypass_gpu_budget(tmp_path):
    fake=tmp_path/"worker.py"; outer=tmp_path/"supervisor.py"
    worker_pid=tmp_path/"worker.pid"; lease=tmp_path/"lease"
    fake.write_text(r"""
import json,os,pathlib,sys,time
a=sys.argv
pathlib.Path(a[a.index('--worker-pid')+1]).write_text(str(os.getpid()))
with pathlib.Path(a[a.index('--lease')+1]).open('a') as f:
 f.write(json.dumps({'pid':os.getpid(),'event':'start','monotonic_s':time.monotonic()})+'\n')
time.sleep(60)
""")
    outer.write_text(r"""
from pathlib import Path
import sys
from r1.scripts import trackp_p3a_guarded as G
root=Path(sys.argv[1]); root.mkdir()
G.SCRIPT=Path(sys.argv[2]); G.verify_live_pins=lambda j: None
G.R.tasl7_driver_snapshot=lambda: {'boot_id':'boot'}
lease=Path(sys.argv[3]); budget=G.GPUBudget(limit=1.2,lease_log=lease)
G.run_unit(root,root/'journal','boot',budget,'DRYRUN','kev','job',
           ['--lease',str(lease),'--worker-pid',sys.argv[4]])
""")
    env={**os.environ,"PYTHONPATH":str(G.R.REPO),"CUDA_VISIBLE_DEVICES":""}
    sup=subprocess.Popen([sys.executable,str(outer),str(tmp_path/"campaign"),str(fake),str(lease),str(worker_pid)],env=env)
    try:
        deadline=time.monotonic()+15
        while (not worker_pid.exists() or not lease.exists() or not lease.read_text()) and time.monotonic()<deadline:
            assert sup.poll() is None
            time.sleep(.05)
        assert worker_pid.exists() and lease.read_text()
        os.kill(sup.pid,signal.SIGSTOP)
        pid=int(worker_pid.read_text()); deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            stat=Path(f"/proc/{pid}/stat")
            if not stat.exists() or stat.read_text().split()[2]=="Z": break
            time.sleep(.1)
        else: pytest.fail("independent watchdog did not stop worker while supervisor was stopped")
        log=tmp_path/"campaign"/"DRYRUN"/"kev"/"job.watchdog.log"
        deadline=time.monotonic()+3
        while not log.exists() and time.monotonic()<deadline: time.sleep(.05)
        assert log.exists() and "GPU lease budget exhausted" in log.read_text()
    finally:
        if sup.poll() is None:
            os.kill(sup.pid,signal.SIGCONT)
            try: sup.wait(timeout=5)
            except subprocess.TimeoutExpired: sup.kill(); sup.wait()


def test_blocked_acquired_log_is_killed_and_marked_unobserved(tmp_path,monkeypatch):
    fake=tmp_path/"blocked.py"; lease=tmp_path/"lease"
    fake.write_text(r"""
import pathlib,sys,time
from r1.c3.train import run as R
a=sys.argv
R._log_lease=lambda *args: time.sleep(60)
with R.gpu_lease('blocked',lock_path=pathlib.Path(a[a.index('--lock')+1]),
                 log_path=pathlib.Path(a[a.index('--lease')+1]),check_processes=False):
 pass
""")
    monkeypatch.setattr(G,"SCRIPT",fake); monkeypatch.setattr(G,"verify_live_pins",lambda journal: None)
    monkeypatch.setattr(G.R,"tasl7_driver_snapshot",lambda: {"boot_id":"boot"})
    monkeypatch.setenv("PYTHONPATH",str(G.R.REPO))
    root=tmp_path/"campaign"; root.mkdir(); budget=G.GPUBudget(limit=.8,lease_log=lease)
    with pytest.raises(G.R.TrackPStop,match="watchdog"):
        G.run_unit(root,root/"journal","boot",budget,"DRYRUN","kev","blocked",
                   ["--lease",str(lease),"--lock",str(tmp_path/"gpu.lock")])
    assert budget.unobserved_lease_upper_s > 0
    assert "unit_complete" not in (root/"journal").read_text()


def test_missing_lease_end_is_upper_bound_not_measured(tmp_path,monkeypatch):
    fake=tmp_path/"fake.py"; lease=tmp_path/"lease"
    fake.write_text(r"""
import json,os,pathlib,sys,time
a=sys.argv
with pathlib.Path(a[a.index('--lease')+1]).open('a') as f:
 f.write(json.dumps({'pid':os.getpid(),'event':'start','monotonic_s':time.monotonic()})+'\n')
time.sleep(.1)
""")
    monkeypatch.setattr(G,"SCRIPT",fake); monkeypatch.setattr(G,"verify_live_pins",lambda journal: None)
    monkeypatch.setattr(G.R,"tasl7_driver_snapshot",lambda: {"boot_id":"boot"})
    root=tmp_path/"campaign"; root.mkdir(); budget=G.GPUBudget(limit=10,lease_log=lease)
    with pytest.raises(G.R.TrackPStop,match="missing end"):
        G.run_unit(root,root/"journal","boot",budget,"DRYRUN","kev","partial",["--lease",str(lease)])
    assert budget.used == 0 and budget.unobserved_lease_upper_s > 0


def test_watchdog_nonzero_after_worker_exit_records_unobserved_upper_bound(tmp_path,monkeypatch):
    fake=tmp_path/"exit.py"; lease=tmp_path/"lease"
    fake.write_text(r"""
import json,os,pathlib,sys,time
a=sys.argv
with pathlib.Path(a[a.index('--lease')+1]).open('a') as f:
 f.write(json.dumps({'pid':os.getpid(),'event':'acquired','monotonic_s':time.monotonic()})+'\n')
time.sleep(.1)
""")
    class FailedWatchdog:
        def poll(self): return None
        def wait(self,timeout=None): return 3
    monkeypatch.setattr(G,"start_watchdog",lambda *args: FailedWatchdog())
    monkeypatch.setattr(G,"SCRIPT",fake)
    monkeypatch.setattr(G,"verify_live_pins",lambda journal: None)
    monkeypatch.setattr(G.R,"tasl7_driver_snapshot",lambda: {"boot_id":"boot"})
    root=tmp_path/"campaign"; root.mkdir(); budget=G.GPUBudget(limit=10,lease_log=lease)
    with pytest.raises(G.R.TrackPStop,match="watchdog STOP"):
        G.run_unit(root,root/"journal","boot",budget,"DRYRUN","kev","job",["--lease",str(lease)])
    assert budget.used==0 and 0 < budget.unobserved_lease_upper_s < 5
