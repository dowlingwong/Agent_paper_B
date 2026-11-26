#!/usr/bin/env python3
"""Sample the smoke scope: descendant RSS high-water marks per run and cgroup memory peaks.

Read-only over /proc and the scope's cgroup tree (the sampler itself runs inside the delegated
scope, in its ``driver`` sub-cgroup, so it is charged with the smoke but excluded from the run
cgroups).  Writes JSON on SIGTERM/SIGINT or when ``--seconds`` elapses.
"""
from __future__ import annotations

import json
import os
import re
import signal
import sys
import time
from pathlib import Path

SCOPE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SECONDS = float(sys.argv[3]) if len(sys.argv) > 3 else 100000.0
RUN_IDS = ["s000_baseline", "s001", "s002", "s003", "B2", "E1", "E2", "E3", "E4"]
CMD_RE = re.compile(r"/runs_(?:smoke|edits)/([^/]+)/")
peak_rss: dict[str, int] = {}
peak_cg: dict[str, int] = {}
peak_scope = 0
samples = 0
started = time.monotonic()
stop = False


def on_signal(signum, frame):  # noqa: ARG001
    global stop
    stop = True


signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)


def run_of(path_name: str) -> str | None:
    name = path_name
    if not name.startswith("ar_"):
        return None
    rest = name[3:]
    for rid in RUN_IDS:
        if rest.startswith(rid + "_"):
            return rid
    return None


def dump() -> None:
    payload = {
        "schema": "u2_scope_monitor/v1",
        "scope": str(SCOPE),
        "utc_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "samples": samples,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "scope_cgroup_memory_peak_bytes": peak_scope,
        "per_run_vmhwm_bytes": peak_rss,
        "per_run_cgroup_memory_peak_bytes": peak_cg,
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(OUT)


while not stop and time.monotonic() - started < SECONDS:
    dirs = [SCOPE]
    try:
        dirs += [p for p in SCOPE.rglob("*") if p.is_dir()]
    except OSError:
        pass
    for d in dirs:
        try:
            mp = d / "memory.peak"
            if mp.is_file():
                val = int(mp.read_text().strip())
                peak_scope = max(peak_scope, val)
                rid = run_of(d.name)
                if rid is not None:
                    peak_cg[rid] = max(peak_cg.get(rid, 0), val)
        except (OSError, ValueError):
            pass
        try:
            pids = (d / "cgroup.procs").read_text().split()
        except OSError:
            continue
        for pid in pids:
            try:
                cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            except OSError:
                continue
            m = CMD_RE.search(cmd)
            if not m:
                continue
            rid = m.group(1)
            try:
                status = Path(f"/proc/{pid}/status").read_text()
            except OSError:
                continue
            for line in status.splitlines():
                if line.startswith("VmHWM:"):
                    try:
                        value = int(line.split()[1]) * 1024
                    except (ValueError, IndexError):
                        break
                    peak_rss[rid] = max(peak_rss.get(rid, 0), value)
                    break
    samples += 1
    if samples % 50 == 0:
        dump()
    time.sleep(0.1)

dump()
