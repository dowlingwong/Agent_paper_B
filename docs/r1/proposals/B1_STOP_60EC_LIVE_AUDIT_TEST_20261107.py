"""60ec audit STOP test with evidence-safe cleanup; engineering only."""
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock
import pytest
from r1.exam import runtime
from r1.scripts import llama_server_instance

def test_audit_stop_notifies_parent_and_stops_owned_processes(tmp_path, monkeypatch):
    module = tmp_path / 'synthetic_b1_child.py'
    module.write_text('''import json, os, time\nfrom pathlib import Path\nfrom r1.exam import campaign\nimport multiprocessing\nmultiprocessing.set_start_method('fork')\ndef fake(node, files, seeds, out, **kwargs):\n    Path(out, "pid_"+files["kind"]).write_text(str(os.getpid()))\n    if files["kind"] == "long":\n        Path(out, "active_worker").write_text(str(os.getpid()))\n        time.sleep(60)\n        return [{"success": True, "metric": 0}]\n    deadline=time.monotonic()+10\n    while not Path(out, "active_worker").exists():\n        if time.monotonic()>deadline: raise RuntimeError("active worker missing")\n        time.sleep(.02)\n    raise RuntimeError("synthetic audit failure")\ncampaign.run_config=fake\njob=json.loads(Path(os.sys.argv[2]).read_text())\ncampaign.run_b1_audits("digits_mlp", {"one":{"files":{"kind":"fail"}}, "two":{"files":{"kind":"long"}}}, {"workers":2,"audit_seeds":[1]}, job["out"], {}, lambda:None)\n''')
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join((str(tmp_path), str(runtime.REPO), str(Path(os.environ['AR_HARNESS_ROOT']) / 'src')))
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
        # Preserve failures and never signal a reaped/reused group ID.
        # The test-owned synthetic processes have a 60-second self-expiry.
        # A failure is STOP; do not retry the production shutdown here.
