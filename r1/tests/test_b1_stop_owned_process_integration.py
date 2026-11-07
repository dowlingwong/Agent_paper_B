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


def test_audit_stop_notifies_parent_and_stops_owned_processes(tmp_path, monkeypatch):
    module = tmp_path / 'synthetic_b1_child.py'
    module.write_text('''import json, os, time\nfrom pathlib import Path\nfrom r1.exam import campaign\nimport multiprocessing\nmultiprocessing.set_start_method('fork')\ndef fake(node, files, seeds, out):\n    Path(out, "pid_"+files["kind"]).write_text(str(os.getpid()))\n    if files["kind"] == "long":\n        Path(out, "active_worker").write_text(str(os.getpid()))\n        time.sleep(60)\n        return [{"success": True, "metric": 0}]\n    deadline=time.monotonic()+10\n    while not Path(out, "active_worker").exists():\n        if time.monotonic()>deadline: raise RuntimeError("active worker missing")\n        time.sleep(.02)\n    raise RuntimeError("synthetic audit failure")\ncampaign.run_config=fake\njob=json.loads(Path(os.sys.argv[2]).read_text())\ncampaign.run_b1_audits("digits_mlp", {"one":{"files":{"kind":"fail"}}, "two":{"files":{"kind":"long"}}}, {"workers":2,"audit_seeds":[1]}, job["out"], {}, lambda:None)\n''')
    real_stop = c3_label_sweep.stop_tree
    # The Mac sandbox cannot run ps and has no /proc. Synthetic workers
    # record their own PIDs so the existing stop_tree can exercise signaling.
    def ps_table():
        return {int(path.read_text()): (runner.child.pid, '')
                for path in (tmp_path / 'job').glob('pid_*')}
    monkeypatch.setattr(c3_label_sweep, 'proc_table', ps_table)
    stops = []
    def stop(pid):
        result = real_stop(pid, timeout=1)
        stops.append(result)
        return result
    monkeypatch.setattr(runtime, 'stop_tree', stop)
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
        assert len(stops) == 1 and len(stops[0]['pids']) >= 3
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
