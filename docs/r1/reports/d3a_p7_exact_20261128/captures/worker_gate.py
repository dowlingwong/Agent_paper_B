#!/usr/bin/env python3
"""Derive the P7 worker gate from the smoke run trees.

Reads only the engineering smoke's own `runs.jsonl` and `summary.json`.  A charged worker
run is a record with `worker_mode=local_worker`: it either succeeded or failed.  Skips
(`control_plane`) and precheck rejections (`local_worker_precheck`) are not worker runs.

The gate follows the sweep-2 `gates.worker` shape: trials, successful, failures, runtime
errors, failures by category, and the pooled charged failure rate against the D.3
pre-declaration §10 limit of 12.99 %.  The two pre-admitted runtime-error classes (a YAML
ParserError from a truncated mapping value; a TypeError from `max_depth: null`) are
admitted and counted as `invalid_config`; any other runtime_error is unadmitted and fails
the gate.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

ARMS = ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER")
SEEDS = (6301, 6302)
FAILURE_RATE_LIMIT = 0.1299


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def admitted_runtime_error(message: str) -> bool:
    text = str(message or "")
    return text.startswith("ParserError") or ("TypeError" in text and "max_depth" in text)


def trial_log_message(campaign: Path, trial_id: str) -> str:
    """Return the ``FAILURE_MESSAGE`` block of a trial's own ``art/trial-N/run.log``."""
    match = re.search(r"trial-(\d+)", str(trial_id or ""))
    if not match:
        return ""
    path = campaign / "art" / f"trial-{match.group(1)}" / "run.log"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = "FAILURE_MESSAGE="
    index = text.find(marker)
    return text[index + len(marker):] if index >= 0 else ""


def campaign_row(campaign: Path) -> dict:
    summary = json.loads((campaign / "summary.json").read_text())
    successful = 0
    finite_metrics = 0
    failed = 0
    prechecks = 0
    skips = 0
    runtime_errors = 0
    admitted = 0
    unadmitted = 0
    runtime_error_trials: list[dict] = []
    categories: dict[str, int] = {}
    for line in (campaign / "runs.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)["record"]
        mode = str(rec.get("worker_mode") or "")
        if mode == "control_plane":
            skips += 1
            continue
        if mode == "local_worker_precheck":
            prechecks += 1
            continue
        if mode != "local_worker" and "success" not in rec:
            continue
        if "success" in rec:
            # Replicate campaign (FIXR3/EGATE): one RunAttempt per line.
            if rec.get("success") is True:
                successful += 1
                if finite(rec.get("metric")):
                    finite_metrics += 1
            else:
                failed += 1
                categories["runtime_error"] = categories.get("runtime_error", 0) + 1
            continue
        if rec.get("execution_status") == "success":
            successful += 1
            metrics = rec.get("parsed_metrics") or {}
            if metrics and all(finite(v) for v in metrics.values()):
                finite_metrics += 1
            continue
        failed += 1
        category = str(rec.get("failure_category") or "unknown")
        categories[category] = categories.get(category, 0) + 1
        if category == "runtime_error":
            runtime_errors += 1
            trial_id = str(rec.get("trial_id") or "")
            message = trial_log_message(campaign, trial_id)
            short = str(((rec.get("extra") or {}).get("worker_failure_message"))
                        or rec.get("worker_failure_message") or "")
            kind = "admitted_truncated_mapping_parsererror" if message.startswith("ParserError") \
                else ("admitted_max_depth_typeerror" if admitted_runtime_error(message)
                      else "unadmitted")
            runtime_error_trials.append({"trial": trial_id, "worker_exit": short, "class": kind,
                                         "message_head": message.splitlines()[0] if message else ""})
            if kind.startswith("admitted"):
                admitted += 1
                categories["invalid_config"] = categories.get("invalid_config", 0) + 1
                categories["runtime_error"] = categories.pop("runtime_error", 0) - 1
                if categories["runtime_error"] == 0:
                    categories.pop("runtime_error")
            else:
                unadmitted += 1
    trials = successful + failed
    ok = (
        trials >= 1
        and successful >= 1
        and finite_metrics >= 1
        and summary.get("status") == "complete"
        and unadmitted == 0
    )
    return {
        "campaign": campaign.name,
        "arm": summary.get("arm"),
        "instance_seed": summary.get("instance_seed"),
        "status": summary.get("status"),
        "trials": trials,
        "successful": successful,
        "successful_with_finite_metrics": finite_metrics,
        "failed": failed,
        "prechecks": prechecks,
        "skips": skips,
        "runtime_errors": runtime_errors,
        "admitted_diagnosed_runtime_errors": admitted,
        "unadmitted_runtime_errors": unadmitted,
        "runtime_error_trials": runtime_error_trials,
        "failures_by_category": dict(sorted(categories.items())),
        "worker_runs_summary": summary.get("worker_runs"),
        "llm_calls": summary.get("llm_calls"),
        "keeps": summary.get("keeps"),
        "wall_seconds": summary.get("wall_seconds"),
        "worker_seconds": summary.get("worker_seconds"),
        "worker_gate": "PASS" if ok else "FAIL",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    rows = []
    for seed in SEEDS:
        for arm in ARMS:
            campaign = root / f"run-s{seed}" / "chunks" / arm / "campaigns" / f"openml_climate__s{seed}"
            if campaign.is_dir():
                rows.append(campaign_row(campaign))
    trials = sum(r["trials"] for r in rows)
    successful = sum(r["successful"] for r in rows)
    failed = sum(r["failed"] for r in rows)
    categories: dict[str, int] = {}
    for r in rows:
        for key, value in r["failures_by_category"].items():
            categories[key] = categories.get(key, 0) + value
    rate = (failed / trials) if trials else None
    harness_rows = [r for r in rows if r["arm"] not in ("FIXR3", "EGATE")]
    h_trials = sum(r["trials"] for r in harness_rows)
    h_failed = sum(r["failed"] for r in harness_rows)
    h_rate = (h_failed / h_trials) if h_trials else None
    unadmitted = sum(r["unadmitted_runtime_errors"] for r in rows)
    all_complete = bool(rows) and all(
        r["status"] == "complete" and r["successful_with_finite_metrics"] >= 1
        and r["worker_gate"] == "PASS" for r in rows
    )
    status = (
        "PASS"
        if all_complete and rate is not None and rate <= FAILURE_RATE_LIMIT and unadmitted == 0
        else "FAIL"
    )
    payload = {
        "schema": "r1_d3_p7_worker_gate/v1",
        "engineering_only": True,
        "gate": status,
        "campaigns": len(rows),
        "expected_campaigns": 14,
        "worker": {
            "trials": trials,
            "successful": successful,
            "failures": failed,
            "failure_rate": rate,
            "failure_rate_limit": FAILURE_RATE_LIMIT,
            "runtime_errors": sum(r["runtime_errors"] for r in rows),
            "admitted_diagnosed_runtime_errors": sum(
                r["admitted_diagnosed_runtime_errors"] for r in rows),
            "unadmitted_runtime_errors": unadmitted,
            "failures_by_category": dict(sorted(categories.items())),
            "prechecks": sum(r["prechecks"] for r in rows),
            "skips": sum(r["skips"] for r in rows),
            "harness_only": {
                "trials": h_trials,
                "failures": h_failed,
                "failure_rate": h_rate,
                "above_limit": bool(h_rate is not None and h_rate > FAILURE_RATE_LIMIT),
                "note": "Sensitivity only; the declared stage denominator pools replicate runs.",
            },
        },
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"gate": status, "trials": trials, "failures": failed,
                      "rate": rate, "harness_only_rate": h_rate}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
