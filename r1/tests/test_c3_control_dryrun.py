"""RUNBOOK Track H.9: the desktop control DRYRUN (fake llama-server, fake sidecars, A0-A6 + direct arms,
one interruption and resume, matching_report). About a minute of CPU. DRYRUN; AI-assisted (Claude)."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys

import pytest

from r1.harness import REPO

DESKTOP_ONLY = pytest.mark.skipif(os.environ.get("R1_DRYRUN_CHILD") == "1"
                                  or platform.node().split(".")[0] == "ucrtasl",
                                  reason="desktop DRYRUN only (never on Ada, never nested)")


@DESKTOP_ONLY
def test_control_dryrun_end_to_end(tmp_path):
    work, out = tmp_path / "work", tmp_path / "out"
    work.mkdir()
    env = {**os.environ, "PYTHONPATH": str(REPO), "PATH": os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]}
    done = subprocess.run([sys.executable, "r1/scripts/c3_control_dryrun.py", "--stage", "all", "--work", str(work),
                           "--out", str(out), "--interrupt-after", "3"], cwd=REPO, env=env, capture_output=True,
                          text=True, timeout=170)
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    summary = json.loads((out / "summary.json").read_text())
    assert summary["pass"] and not summary["problems"]
    assert all(summary["checks"].values())
    assert summary["state"]["interruption"]["in_progress"] == "A3__digits_mlp"
    assert summary["matching_report"]["matched"] and len(summary["campaigns"]) == 20
