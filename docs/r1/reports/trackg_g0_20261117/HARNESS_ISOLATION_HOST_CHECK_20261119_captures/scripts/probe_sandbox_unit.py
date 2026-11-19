"""G0: call the unit's own isolation.worker_sandbox_available() directly (outside any systemd scope) and
report the exact refusal, to separate a host userns/mount condition from the cgroup-delegation condition.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path("/home/dowling/r1_trackg_20261117/harness_iso_core")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "trackg"))

from autoresearch.trackg import isolation  # noqa: E402
from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
from autoresearch.trackg.runner import WorkingCopyRunner  # noqa: E402

BASE = Path("/home/dowling/r1_trackg_20261117/host_check_g0_20261119")
interp = sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/python3"
stamp = __import__("time").strftime("%Y%m%dT%H%M%SZ", __import__("time").gmtime())
base = BASE / "work" / f"sandbox_unit_{stamp}"
base.mkdir(parents=True)
node = make_isolated_node(base, "ok")
spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
runner = WorkingCopyRunner(spec, node, BASE / "records")
run_dir = base / "run"
run_dir.mkdir()
work = run_dir / "work"
work.mkdir()
cfg = runner._sandbox_config(run_dir, work, interp)
ok, why = isolation.worker_sandbox_available(interp, cfg, run_dir / "_sandbox_probe")
out = {"interpreter": interp, "euid": os.geteuid(), "ok": ok, "why": why, "ro": cfg["ro"],
       "ro_flat": cfg["ro_flat"], "rw": cfg["rw"], "dev": cfg["dev"], "shared_dev_shm": cfg["shared_dev_shm"]}
print(json.dumps(out, indent=2, sort_keys=True, default=str))
sys.exit(0 if ok else 1)
