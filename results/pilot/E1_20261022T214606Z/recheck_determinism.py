#!/usr/bin/env python3
"""Determinism re-check for the common 30-seed E1 run (PILOT; AI-assisted, Claude).

Re-runs, for every node and configuration, one training-seed, one split-seed and one
joint-seed run of runs.jsonl (seed indices 14, 22 and 29), through the same
r1.noise.e1_noise_floor.run_one, and compares the metric bit-for-bit.
Writes recheck_determinism.json into the run directory.

Usage (paper repo root, harness venv first on PATH, AR_HARNESS_ROOT set):
  python results/r1/pilot/E1_<UTC>/recheck_determinism.py results/r1/pilot/E1_<UTC>
"""
from __future__ import annotations

import json
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from r1.noise.e1_noise_floor import run_one  # noqa: E402

PICK = {("train", 1001 + 14, None), ("split", None, 2001 + 22), ("joint", 3001 + 29, 3001 + 29)}


def main() -> int:
    run_dir = Path(sys.argv[1])
    edits = json.loads((run_dir / "edits.json").read_text())
    rows = [json.loads(l) for l in (run_dir / "runs.jsonl").read_text().splitlines() if l.strip()]
    target = [r for r in rows if (r["condition"], r["train_seed"], r["split_seed"]) in PICK]
    jobs = []
    for r in target:
        k = int(r["config"][1:])
        edit = None if k == 0 else edits[r["node"]][k - 1]
        jobs.append((r["node"], r["config"], edit, r["condition"], r["train_seed"], r["split_seed"]))
    with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor(max_workers=4) as pool:
        new = list(pool.map(run_one, *zip(*jobs), [tmp] * len(jobs)))
    diffs = [{"node": a["node"], "config": a["config"], "condition": a["condition"], "old": a["metric"], "new": b["metric"]}
             for a, b in zip(target, new) if a["metric"] != b["metric"] or not b["success"]]
    out = {"label": "PILOT", "n_rechecked": len(jobs), "n_identical": len(jobs) - len(diffs), "differences": diffs}
    (run_dir / "recheck_determinism.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "differences"}), len(diffs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
