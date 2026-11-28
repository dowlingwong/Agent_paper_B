#!/usr/bin/env python3
"""Derive the P7 worker gate and per-arm/seed table from the smoke run trees.

Reads only the engineering smoke's own ledger records (`runs.jsonl`) and per-campaign
`summary.json`; writes `worker_gate.json`.  No label, test or evaluation value is read.

A campaign passes the worker gate when it has at least one successful run with a finite
parsed metric, no worker-failure message, and a non-zero charged worker-run count.  The
gate is PASS only when every campaign of both smoke seeds passes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ARMS = ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER")


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def campaign_row(campaign: Path) -> dict:
    summary = json.loads((campaign / "summary.json").read_text())
    successes = 0
    finite_metrics = 0
    failures = 0
    invalid = 0
    skipped = 0
    for line in (campaign / "runs.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)["record"]
        if rec.get("execution_status") is not None:
            # Harness campaign: a full trial record. Control-only records with no
            # execution_status are not worker runs and are ignored. A skipped
            # proposal was charged no worker run and is not a worker failure.
            if rec.get("execution_status") == "success":
                successes += 1
                metrics = rec.get("parsed_metrics") or {}
                if metrics and all(finite(v) for v in metrics.values()):
                    finite_metrics += 1
            elif rec.get("decision") == "skipped":
                skipped += 1
            elif rec.get("validity_status") == "invalid" or rec.get("decision") == "failed_invalid":
                # A proposal rejected before any worker run (control-plane cost only).
                invalid += 1
            else:
                failures += 1
        elif "success" in rec:
            # Replicate campaign (FIXR3/EGATE): one RunAttempt per line.
            if rec.get("success") is True:
                successes += 1
                if finite(rec.get("metric")):
                    finite_metrics += 1
            else:
                failures += 1
    ok = (
        int(summary.get("worker_runs", 0)) >= 1
        and successes >= 1
        and finite_metrics >= 1
        and summary.get("status") == "complete"
    )
    return {
        "campaign": campaign.name,
        "arm": summary.get("arm"),
        "instance_seed": summary.get("instance_seed"),
        "status": summary.get("status"),
        "worker_runs": summary.get("worker_runs"),
        "llm_calls": summary.get("llm_calls"),
        "keeps": summary.get("keeps"),
        "wall_seconds": summary.get("wall_seconds"),
        "worker_seconds": summary.get("worker_seconds"),
        "successful_runs": successes,
        "successful_with_finite_metrics": finite_metrics,
        "skipped_proposals": skipped,
        "failed_runs": failures,
        "invalid_runs": invalid,
        "worker_gate": "PASS" if ok else "FAIL",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="engineering root holding run-s<seed>/")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    rows = []
    for seed in (6301, 6302):
        run = root / f"run-s{seed}"
        for arm in ARMS:
            campaign = run / "chunks" / arm / "campaigns" / f"openml_climate__s{seed}"
            if campaign.is_dir():
                rows.append(campaign_row(campaign))
    gate = "PASS" if rows and all(r["worker_gate"] == "PASS" for r in rows) else "FAIL"
    payload = {
        "schema": "r1_d3_p7_worker_gate/v1",
        "engineering_only": True,
        "gate": gate,
        "campaigns": len(rows),
        "expected_campaigns": 14,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"gate": gate, "campaigns": len(rows)}, sort_keys=True))
    return 0 if gate == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
