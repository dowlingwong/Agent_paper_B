#!/usr/bin/env python3
"""Helper run inside a second, sibling delegated scope (the 'old job' for the orphan rule).

It creates one populated ``ar_*`` child cgroup in its own scope cgroup and
sleeps, so that the next job's start-of-job scan sees an orphaned run cgroup
in a sibling unit under the same ``user@<uid>.service/app.slice``.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ready = Path(sys.argv[1])
cg = Path("/sys/fs/cgroup" + Path("/proc/self/cgroup").read_text().strip().split(":", 2)[2])
ar = cg / f"ar_orphan_smoke_{os.getpid()}_1"
ar.mkdir()
child = subprocess.Popen(["/bin/sleep", "300"])
(ar / "cgroup.procs").write_text(f"{child.pid}\n")
ready.write_text(json.dumps({"scope_cgroup": str(cg), "unit": cg.name, "ar": str(ar),
                             "sleep_pid": child.pid, "pid": os.getpid()}))
time.sleep(300)
