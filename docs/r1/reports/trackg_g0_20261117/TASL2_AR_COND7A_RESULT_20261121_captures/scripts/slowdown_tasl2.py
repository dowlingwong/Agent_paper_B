"""Measured slowdown / peak-resource facts for the one R1-TRACKG-AR-U2-TASL2 isolated smoke (TASL-2).

Usage: python3 slowdown_tasl2.py <evidence_dir>

Reads the run records under <evidence_dir>/runs, the smoke start/end stamps, /usr/bin/time -v output, the
1 s nvidia-smi compute-app sampler maximum, the 2 s cgroup v2 memory sampler and the per-run AR_INFO
peak_vram_mb lines; writes <evidence_dir>/slowdown.json and prints it.

Reference (accepted 17 Nov 2026 Ada G.0 U2 B1/B2, TRACKG_U2_AR_RESULT_20261117.md): smoke wall 564 s, B1
67.901 s, B2 64.096 s, baseline peak VRAM 5,211.3 MB; whole-smoke /usr/bin/time -v user 662.47 s, sys 42.78 s,
max RSS 2,110,468 kB.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

OLD = {"smoke_wall_s": 564.0, "B1_s": 67.901, "B2_s": 64.096, "peak_vram_mb": 5211.3,
       "user_s": 662.47, "sys_s": 42.78, "max_rss_kb": 2110468}
REQUESTS = 644  # 640 validation + 3 causality probe + 1 repeat per run (cond7a code-unit report sec 8)


def parse_dt(text):
    text = text.strip()
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def parse_time_v(text):
    out = {}
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)", text)
    if m:
        raw = m.group(1)
        secs = 0.0
        for part in raw.split(":"):
            secs = secs * 60 + float(part)
        out["elapsed_wall"] = raw
        out["elapsed_wall_seconds"] = round(secs, 2)
    for key, pat in (
        ("user_seconds", r"User time \(seconds\):\s*([0-9.]+)"),
        ("system_seconds", r"System time \(seconds\):\s*([0-9.]+)"),
        ("max_rss_kbytes", r"Maximum resident set size \(kbytes\):\s*([0-9]+)"),
        ("minor_page_faults", r"Minor \(reclaiming\) page faults:\s*([0-9]+)"),
        ("major_page_faults", r"Major \(requiring I/O\) page faults:\s*([0-9]+)"),
        ("file_system_outputs", r"File system outputs:\s*([0-9]+)"),
        ("socket_messages_sent", r"Socket messages sent:\s*([0-9]+)"),
        ("socket_messages_received", r"Socket messages received:\s*([0-9]+)"),
    ):
        m = re.search(pat, text)
        if m:
            value = m.group(1)
            out[key] = float(value) if "." in value else int(value)
    return out


def parse_cgroup_sampler(text):
    peak = 0
    cur = 0
    rows = 0
    for line in text.splitlines():
        rows += 1
        m = re.search(r"current_bytes=(\d+)", line)
        if m:
            cur = max(cur, int(m.group(1)))
        m = re.search(r"peak_bytes=(\d+)", line)
        if m:
            peak = max(peak, int(m.group(1)))
    return {"rows": rows, "max_memory_current_bytes": cur or None, "max_memory_peak_bytes": peak or None}


def main() -> int:
    ev = Path(sys.argv[1]).resolve()
    rows = {}
    for rp in sorted((ev / "runs").rglob("run_record.json")):
        d = json.loads(rp.read_text())
        rid = d.get("run_id")
        log = rp.parent / "run.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        ar = {}
        for key, pat in (("eval_rows", r"AR_INFO eval_rows=(\d+)"),
                         ("eval_batch_size", r"AR_INFO eval_batch_size=(\d+)"),
                         ("peak_vram_mb", r"AR_INFO peak_vram_mb=([0-9.]+)"),
                         ("causal_probe_max_change", r"AR_INFO causal_probe_max_change=([0-9.eE+-]+)"),
                         ("num_workers", r"AR_INFO num_workers=(\d+)"),
                         ("device", r"AR_INFO device=(\S+)")):
            m = re.search(pat, text)
            if m:
                ar[key] = m.group(1)
        rows[rid] = {
            "executed": d.get("executed"),
            "outcome": d.get("outcome"),
            "elapsed_seconds": d.get("elapsed_seconds_info_only"),
            "peak_vram_mb_worker": float(ar["peak_vram_mb"]) if "peak_vram_mb" in ar else None,
            "ar_info": ar,
        }
    executed = {k: v for k, v in rows.items() if v.get("executed") is True and v.get("elapsed_seconds") is not None}
    skipped = [k for k in executed if k == "s001"]
    timing = {k: v["elapsed_seconds"] for k, v in executed.items() if k not in skipped}
    vals = sorted(timing.values())
    b1 = rows.get("s000_baseline", {}).get("elapsed_seconds")
    b2 = rows.get("B2", {}).get("elapsed_seconds")

    wall = None
    try:
        t0 = parse_dt((ev / "smoke_start_utc.txt").read_text())
        t1 = parse_dt((ev / "smoke_end_utc.txt").read_text())
        wall = round((t1 - t0).total_seconds(), 1)
    except Exception:  # noqa: BLE001
        pass

    time_v_text = (ev / "time_v.txt").read_text(errors="replace") if (ev / "time_v.txt").exists() else ""
    time_v = parse_time_v(time_v_text)
    sampler_text = (ev / "sampler/cgroup_sampler.csv").read_text(errors="replace") if (ev / "sampler/cgroup_sampler.csv").exists() else ""
    cg = parse_cgroup_sampler(sampler_text)
    sampler_max = {}
    sm = ev / "sampler/sampler_max.json"
    if sm.exists():
        sampler_max = json.loads(sm.read_text())

    out = {
        "host": "TASL-2",
        "smoke": {
            "nodes": "autoresearch_fixedtokens",
            "runs_records": len(rows),
            "executed_records": len([r for r in rows.values() if r.get("executed") is True]),
            "refused_records": [k for k, r in rows.items() if r.get("executed") is False],
            "executed_elapsed_seconds": timing,
            "mean_executed_run_seconds": round(sum(vals) / len(vals), 3) if vals else None,
            "median_executed_run_seconds": vals[len(vals) // 2] if vals else None,
            "requests_per_run": REQUESTS,
            "smoke_wall_seconds": wall,
        },
        "reference_17nov_ada": OLD,
        "measured": {
            "B1_seconds": b1,
            "B2_seconds": b2,
            "B1_val_bpb": (rows.get("s000_baseline", {}).get("outcome") or {}).get("value"),
            "B2_val_bpb": (rows.get("B2", {}).get("outcome") or {}).get("value"),
            "B1_minus_17nov_seconds": round(b1 - OLD["B1_s"], 3) if b1 else None,
            "B1_vs_17nov_ratio": round(b1 / OLD["B1_s"], 3) if b1 else None,
            "smoke_wall_minus_17nov_seconds": round(wall - OLD["smoke_wall_s"], 1) if wall else None,
            "smoke_wall_vs_17nov_ratio": round(wall / OLD["smoke_wall_s"], 3) if wall else None,
            "transfer_surrogate_seconds_per_request": round((b1 - OLD["B1_s"]) / REQUESTS, 4) if b1 else None,
            "transfer_surrogate_note": (
                "derived as (measured B1 - 67.901 s)/644 logits requests; the node prints no per-request "
                "transfer timer, so this is a wall-clock surrogate, not an instrumented transfer measurement"
            ),
            "volume_one_way_gib_per_run": 640,
            "volume_moved_gib_per_run": 640 * 3,
            "B2_minus_B1_seconds": round(b2 - b1, 3) if (b1 is not None and b2 is not None) else None,
        },
        "peak_resources": {
            "per_run_peak_vram_mb_worker": {k: v["peak_vram_mb_worker"] for k, v in rows.items() if v.get("peak_vram_mb_worker") is not None},
            "max_per_run_peak_vram_mb": max((v["peak_vram_mb_worker"] for v in rows.values() if v.get("peak_vram_mb_worker") is not None), default=None),
            "reference_17nov_peak_vram_mb": OLD["peak_vram_mb"],
            "whole_smoke_gpu_upper_bound_mib": sampler_max.get("whole_smoke_upper_bound_mib"),
            "whole_smoke_gpu_upper_bound_label": sampler_max.get("whole_smoke_upper_bound_label"),
            "sampler_max": sampler_max or None,
            "whole_smoke_time_v": time_v,
            "cgroup_memory": cg,
            "cgroup_memory_peak_after": (ev / "memory_cgroup.txt").read_text(errors="replace") if (ev / "memory_cgroup.txt").exists() else None,
        },
        "rows": rows,
    }
    (ev / "slowdown.json").write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("smoke", "measured", "peak_resources")}, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
