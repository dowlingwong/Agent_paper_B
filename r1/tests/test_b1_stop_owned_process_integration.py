"""Synthetic Mac test of the owned-worker STOP path, with no model or GPU."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from r1.exam import runtime
from r1.scripts import c3_label_sweep, llama_server_instance


def test_stop_after_root_exit_kills_owned_group_not_unrelated(tmp_path, monkeypatch):
    module = tmp_path / 'synthetic_exited_root.py'
    module.write_text('''import os, subprocess, sys, time\nfrom pathlib import Path\njob = Path(sys.argv[2]).parent\np = subprocess.Popen([sys.executable, "-c", "import signal,time,sys; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text('ready'); time.sleep(60)", str(job / "ready")])\n(job / "child_pid").write_text(str(p.pid))\nwhile not (job / "ready").exists(): time.sleep(.01)\nraise SystemExit(7)\n''')
    env = dict(os.environ)
    env['PYTHONPATH'] = str(tmp_path) + os.pathsep + str(runtime.REPO)
    monkeypatch.setattr(runtime, 'worker_environment', lambda: env)
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': False, 'watchdog': {'poll_seconds': 0.05}, 'root_timeout_seconds': 10}
    runner.state = {'phase': 'b1', 'interruptions': []}
    runner.service = None
    runner.b1_lease_fd = os.open(os.devnull, os.O_RDONLY)
    runner.space = Mock()
    runner.save = Mock()
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    jobdir = tmp_path / 'job'
    try:
        with pytest.raises(RuntimeError, match='root worker exit 7'):
            runner.run_job({'out': str(jobdir)}, 'synthetic_exited_root')
        pid = int((jobdir / 'child_pid').read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.05)
        else:
            pytest.fail('owned descendant still exists after STOP')
        assert unrelated.poll() is None
        assert runner.child.returncode == 7
    finally:
        os.close(runner.b1_lease_fd)
        unrelated.terminate()
        unrelated.wait(timeout=3)


def test_audit_stop_notifies_parent_and_stops_owned_processes(tmp_path, monkeypatch):
    module = tmp_path / 'synthetic_b1_child.py'
    module.write_text('''import json, os, time\nfrom pathlib import Path\nfrom r1.exam import campaign\nimport multiprocessing\nmultiprocessing.set_start_method('fork')\ndef fake(node, files, seeds, out, **kwargs):\n    Path(out, "pid_"+files["kind"]).write_text(str(os.getpid()))\n    if files["kind"] == "long":\n        Path(out, "active_worker").write_text(str(os.getpid()))\n        time.sleep(60)\n        return [{"success": True, "metric": 0}]\n    deadline=time.monotonic()+10\n    while not Path(out, "active_worker").exists():\n        if time.monotonic()>deadline: raise RuntimeError("active worker missing")\n        time.sleep(.02)\n    raise RuntimeError("synthetic audit failure")\ncampaign.run_config=fake\njob=json.loads(Path(os.sys.argv[2]).read_text())\ncampaign.run_b1_audits("digits_mlp", {"one":{"files":{"kind":"fail"}}, "two":{"files":{"kind":"long"}}}, {"workers":2,"audit_seeds":[1]}, job["out"], {}, lambda:None)\n''')
    env = dict(os.environ)
    env['PYTHONPATH'] = str(tmp_path) + os.pathsep + str(runtime.REPO)
    monkeypatch.setattr(runtime, 'worker_environment', lambda: env)
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': False, 'watchdog': {'poll_seconds': 0.05}, 'root_timeout_seconds': 15}
    runner.state = {'phase': 'b1', 'interruptions': [], 'server_intervals': []}
    runner.service = None
    runner.b1_lease_fd = os.open(os.devnull, os.O_RDONLY)
    runner.space = Mock()
    runner.save = Mock()
    server = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    inst = llama_server_instance.LlamaServerInstance.__new__(llama_server_instance.LlamaServerInstance)
    inst.process = server
    inst.record = {'pgid': server.pid}
    inst._save = Mock()
    jobdir = tmp_path / 'job'
    started = time.monotonic()
    try:
        with pytest.raises(RuntimeError, match='audit worker failure'):
            runner.run_job({'out': str(jobdir)}, 'synthetic_b1_child')
        runner.service = inst
        runner.stop_service()
        assert time.monotonic() - started < 15
        assert runner.child.poll() is not None and server.poll() is not None
        assert (jobdir / 'active_worker').exists()
        assert 'synthetic audit failure' in (jobdir / 'runner.log').read_text()
    finally:
        os.close(runner.b1_lease_fd)
        for proc in (runner.child, server):
            if proc is not None:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: pass
