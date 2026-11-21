"""Collect the R1-TRACKG-AR-COND7A smoke facts for the result report.

Usage: python3 analyze_cond7a.py <capture_dir>   (prints and writes facts.json)
References (accepted 17 Nov AR U2 result): smoke wall 564 s, B1 67.901 s, worker peak VRAM 5,211.3 MB,
/usr/bin/time user 662.47 s, sys 42.78 s, max RSS 2,110,468 kB (old CUDA-IPC path).
"""
import json
import math
import re
import sys
from pathlib import Path

OLD = {"smoke_wall_s": 564.0, "B1_s": 67.901, "peak_vram_mb": 5211.3,
       "user_s": 662.47, "sys_s": 42.78, "max_rss_kb": 2110468}
REQUESTS = 644  # 640 validation + 3 causality probe + 1 repeat (cond7a report §8)
RUNS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]
SHAS = {}


def sha(p):
    import hashlib
    h = hashlib.sha256()
    with Path(p).open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    cap = Path(sys.argv[1]).resolve()
    ev = cap  # captures are the EV copy
    facts = {"capture": str(cap), "old_reference": OLD, "requests_per_run": REQUESTS}
    # timing / recorded values
    rows = {}
    for rp in sorted((ev / "runs").rglob("run_record.json")):
        d = json.loads(rp.read_text())
        rid = d.get("run_id")
        log = rp.parent / "run.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        info = {}
        for key, pat in (("eval_rows", r"AR_INFO eval_rows=(\d+)"),
                         ("eval_batch_size", r"AR_INFO eval_batch_size=(\d+)"),
                         ("peak_vram_mb", r"AR_INFO peak_vram_mb=([0-9.]+)"),
                         ("causal_probe_max_change", r"AR_INFO causal_probe_max_change=([0-9.eE+-]+)")):
            m = re.search(pat, text)
            if m:
                info[key] = m.group(1)
        rows[rid] = {
            "executed": d.get("executed"),
            "outcome": d.get("outcome"),
            "elapsed_seconds": d.get("elapsed_seconds_info_only"),
            "run_budget": d.get("run_budget"),
            "sealed": d.get("sealed"),
            "record_sha256": sha(rp),
            "log_sha256": sha(log) if log.exists() else None,
            "ar_info": info,
            "process": d.get("process"),
        }
    facts["runs"] = rows
    tags = []
    for f in ("time_v.txt", "memory_cgroup.txt"):
        p = ev / f
        tags.append((f, p.read_text(errors="replace") if p.exists() else ""))
    facts["time_v"] = tags[0][1]
    facts["memory_cgroup"] = tags[1][1]
    # smoke wall from log start/end markers
    log = (ev / "logs/run_node.log").read_text(errors="replace")
    st = re.search(r"start=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", log)
    en = re.search(r"# finished status=", log)
    end_m = re.search(r"end_utc=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", (ev / "RESULT_STATUS.txt").read_text(errors="replace"))
    wall = None
    if st and end_m:
        from datetime import datetime, timezone
        t0 = datetime.strptime(st.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        t1 = datetime.strptime(end_m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        wall = round((t1 - t0).total_seconds(), 1)
    facts["smoke_wall_seconds"] = wall
    b1 = rows.get("s000_baseline", {}).get("elapsed_seconds")
    b2 = rows.get("B2", {}).get("elapsed_seconds")
    executed = {k: v for k, v in rows.items() if v.get("executed") and v.get("elapsed_seconds") is not None}
    vals = [v["elapsed_seconds"] for v in executed.values()]
    facts["slowdown"] = {
        "B1_seconds": b1, "B2_seconds": b2,
        "B1_vs_17nov": round(b1 / OLD["B1_s"], 3) if b1 else None,
        "B1_slowdown_seconds": round(b1 - OLD["B1_s"], 3) if b1 else None,
        "smoke_wall_seconds": wall,
        "smoke_vs_17nov": round(wall / OLD["smoke_wall_s"], 3) if wall else None,
        "smoke_slowdown_seconds": round(wall - OLD["smoke_wall_s"], 1) if wall else None,
        "per_run_elapsed": {k: v["elapsed_seconds"] for k, v in executed.items()},
        "per_run_vs_67_901": {k: round(v["elapsed_seconds"] / OLD["B1_s"], 3) for k, v in executed.items()},
        "mean_executed_run_seconds": round(sum(vals) / len(vals), 3) if vals else None,
        "per_request_transfer_surrogate_seconds": round((b1 - OLD["B1_s"]) / REQUESTS, 4) if b1 else None,
        "per_request_transfer_surrogate_note": (
            "derived from (measured B1 - 67.901 s)/644 requests; the code prints no per-request transfer "
            "timer, so this is a wall-clock surrogate, not an instrumented transfer measurement"),
        "volume_one_way_gib_per_run": 640,
        "volume_moved_gib_per_run": round(640 * 3, 1),
    }
    # peaks
    peak_vram_list = []
    for r in rows.values():
        pv = r.get("ar_info", {}).get("peak_vram_mb")
        if pv:
            peak_vram_list.append(float(pv))
    facts["peak_vram_worker_mb"] = {
        "per_run": {rid: r.get("ar_info", {}).get("peak_vram_mb") for rid, r in rows.items() if r.get("ar_info", {}).get("peak_vram_mb")},
        "max": max(peak_vram_list) if peak_vram_list else None,
        "old_reference_mb": OLD["peak_vram_mb"],
    }
    for f in ("sampler/sampler_max.json", "verify_full.json", "summary.json", "gate/gate_check.txt",
              "data_manifest.txt", "pins.txt", "kit.txt", "slowdown.json"):
        p = ev / f
        if p.exists():
            try:
                facts[f] = json.loads(p.read_text())
            except json.JSONDecodeError:
                facts[f] = p.read_text(errors="replace")
    out = cap / "facts.json"
    out.write_text(json.dumps(facts, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: facts[k] for k in ("smoke_wall_seconds", "slowdown", "peak_vram_worker_mb")},
                     indent=2, sort_keys=True, default=str))
    print("wrote", out)


if __name__ == "__main__":
    main()
