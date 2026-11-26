#!/usr/bin/env python3
"""Per-CPU busy sample for the fixed-seed determinism check (prep report section 9 step 7).

Reads /proc/stat, samples for --seconds (default 5 s), and prints the busy fraction of every logical CPU.
The caller proceeds only if no CPU of the checked set was busier than 0.2 (the spec's cpu_preflight
threshold); exit code 0 means the set is quiet enough.  Read-only.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def cpus_of(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def snap() -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for line in Path("/proc/stat").read_text().splitlines():
        if line.startswith("cpu") and not line.startswith("cpu "):
            parts = line.split()
            out[parts[0][3:]] = [int(x) for x in parts[1:]]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpus", required=True, help="e.g. 12-15")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--max-busy", type=float, default=0.2)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    wanted = cpus_of(args.cpus)
    t0 = time.time()
    a = snap()
    time.sleep(args.seconds)
    b = snap()
    per_cpu = {}
    for cpu in wanted:
        key = str(cpu)
        if key not in a or key not in b:
            per_cpu[key] = None
            continue
        va, vb = a[key], b[key]
        total = sum(vb) - sum(va)
        idle = (vb[3] + vb[4]) - (va[3] + va[4])
        per_cpu[key] = round(0.0 if total <= 0 else 1.0 - idle / total, 4)
    values = [v for v in per_cpu.values() if v is not None]
    result = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cpus": args.cpus,
        "cpu_list": wanted,
        "seconds": args.seconds,
        "max_busy": args.max_busy,
        "per_cpu_busy": per_cpu,
        "set_max_busy": max(values) if values else None,
        "set_mean_busy": round(sum(values) / len(values), 4) if values else None,
        "loadavg": list(__import__("os").getloadavg()),
        "pass": bool(values) and max(values) <= args.max_busy,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("BUSY " + json.dumps({k: result[k] for k in ("cpus", "set_max_busy", "set_mean_busy",
                                                       "pass", "utc")}, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
