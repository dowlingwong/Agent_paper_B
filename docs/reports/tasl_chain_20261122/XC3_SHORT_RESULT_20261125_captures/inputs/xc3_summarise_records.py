#!/usr/bin/env python3
"""Summarise the four XC3 TASL-7 job records (evidence for the result memo)."""
import json
import sys
from pathlib import Path

B = Path("/home/dowling/r1_tracks/t1_tasl")
RUN = "g1b-tasl-20261121-b-xc3-a-TASL-7"
NODES = ["mlab_imdb", "mlab_ogbn_arxiv", "mlgym_fmnist", "mlgym_houseprice"]
out = {}
for n in NODES:
    d = B / "runs" / RUN / n / "attempt-1"
    rec = json.loads((d / "job_record.json").read_text())
    part = (rec.get("parts") or [{}])[0]
    out[n] = {
        "attempt": rec.get("attempt"),
        "device": rec.get("device"),
        "started_utc": rec.get("started_utc"),
        "finished_utc": rec.get("finished_utc"),
        "spec_sha256": rec.get("spec_sha256"),
        "harness_commit": rec.get("harness_commit"),
        "label": rec.get("label"),
        "stop": rec.get("stop"),
        "stop_class": rec.get("stop_class"),
        "deadline_s": rec.get("deadline_s"),
        "parts": rec.get("parts"),
        "timing": rec.get("timing"),
        "determinism": rec.get("determinism"),
        "data": {k: rec.get("data", {}).get(k) for k in ("data_root", "setup")},
        "host": (rec.get("host") or {}).get("host"),
        "gpu": rec.get("gpu"),
        "lease": rec.get("lease"),
        "crosscheck_default_part": rec.get("crosscheck_default_part"),
        "rows_written": part.get("written_rows"),
        "rows_successful": part.get("successful_rows"),
        "rows_expected": part.get("expected_runs"),
        "node_log": rec.get("node_log"),
    }
print(json.dumps(out, indent=1, sort_keys=True))
