#!/usr/bin/env python3
"""Summarise the P7 smoke: per arm/seed times, call latency, and GPU peaks.

Reads only the engineering smoke's own records and the sampler CSV.  Writes a JSON
summary; no label, test or evaluation value is read.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ARMS = ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER")
SEEDS = (6301, 6302)


def campaign_row(campaign: Path) -> dict:
    summary = json.loads((campaign / "summary.json").read_text())
    latencies = []
    for line in (campaign / "runs.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)["record"]
        call = ((rec.get("extra") or {}).get("manager") or {}).get("llm_call") or {}
        if call.get("latency_ms") is not None:
            latencies.append(float(call["latency_ms"]))
    return {
        "arm": summary.get("arm"),
        "instance_seed": summary.get("instance_seed"),
        "status": summary.get("status"),
        "worker_runs": summary.get("worker_runs"),
        "llm_calls": summary.get("llm_calls"),
        "keeps": summary.get("keeps"),
        "wall_seconds": round(float(summary.get("wall_seconds") or 0.0), 3),
        "worker_seconds": round(float(summary.get("worker_seconds") or 0.0), 3),
        "call_latency_s_sum": round(sum(latencies) / 1000.0, 3),
        "call_latency_s_mean": round(sum(latencies) / 1000.0 / len(latencies), 3) if latencies else None,
        "call_latency_s_max": round(max(latencies) / 1000.0, 3) if latencies else None,
        "calls_with_latency": len(latencies),
    }


def gpu_peaks(path: Path) -> dict:
    if not path.is_file():
        return {}
    util = []
    used = []
    free = []
    power = []
    temp = []
    for row in csv.reader(path.read_text().splitlines()):
        if len(row) < 6:
            continue
        try:
            util.append(float(row[1]))
            used.append(float(row[2]))
            free.append(float(row[3]))
            power.append(float(row[4]))
            temp.append(float(row[5]))
        except ValueError:
            continue
    return {
        "samples": len(util),
        "util_pct_max": max(util) if util else None,
        "memory_used_mib_max": max(used) if used else None,
        "memory_free_mib_min": min(free) if free else None,
        "power_w_max": max(power) if power else None,
        "temperature_c_max": max(temp) if temp else None,
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
    latency_values = []
    for seed in SEEDS:
        for arm in ARMS:
            campaign = root / f"run-s{seed}" / "chunks" / arm / "campaigns" / f"openml_climate__s{seed}"
            if not campaign.is_dir():
                continue
            for line in (campaign / "runs.jsonl").read_text().splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)["record"]
                call = ((rec.get("extra") or {}).get("manager") or {}).get("llm_call") or {}
                if call.get("latency_ms") is not None:
                    latency_values.append(float(call["latency_ms"]) / 1000.0)
    campaign_means = [r["call_latency_s_mean"] for r in rows if r.get("call_latency_s_mean") is not None]
    payload = {
        "schema": "r1_d3_p7_summary/v1",
        "engineering_only": True,
        "campaigns": len(rows),
        "rows": rows,
        "gpu_peaks": gpu_peaks(root / "gpu_samples.csv"),
        "call_latency": {
            "calls_with_latency": len(latency_values),
            "mean_s": (sum(latency_values) / len(latency_values)) if latency_values else None,
            "max_s": max(latency_values) if latency_values else None,
            "max_campaign_mean_s": max(campaign_means) if campaign_means else None,
            "llm_calls_total": sum(int(r.get("llm_calls") or 0) for r in rows),
        },
        "totals": {
            "wall_seconds": sum(float(r.get("wall_seconds") or 0.0) for r in rows),
            "worker_seconds": sum(float(r.get("worker_seconds") or 0.0) for r in rows),
        },
    }
    Path(args.out).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"campaigns": len(rows), "gpu_peaks": payload["gpu_peaks"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
