"""Collect the R1-TRACKG-AR-U2-TASL2 smoke facts for the result report.

Usage: python3 facts_tasl2.py <evidence_dir>   (writes <evidence_dir>/facts.json and prints a summary)

References: accepted Ada G.0 U2 baseline (17 Nov 2026) smoke wall 564 s, B1 67.901 s, B2 64.096 s, baseline
peak VRAM 5,211.3 MB; the option-A code-unit report's estimate: ~644 logits requests/run, ~640 GiB one-way
volume, ~97-161 s transfer/run, ~2.4-3.4x B1.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

OLD = {"smoke_wall_s": 564.0, "B1_s": 67.901, "B2_s": 64.096, "peak_vram_mb": 5211.3,
       "user_s": 662.47, "sys_s": 42.78, "max_rss_kb": 2110468}
REQUESTS = 644
EXPECTED_RUNS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def text(p: Path) -> str:
    return p.read_text(errors="replace") if p.exists() else ""


def main() -> int:
    ev = Path(sys.argv[1]).resolve()
    facts = {"evidence_dir": str(ev), "reference_17nov_ada": OLD, "requests_per_run": REQUESTS}

    # flat captures
    for name in ("RESULT_STATUS.txt", "RESULT_STATUS.initial_false_stop.txt", "host.txt", "host_at_smoke.txt",
                 "kit.txt", "env.txt", "env_freeze.txt", "data_manifest.txt", "pins.txt", "cgroup_probe.txt",
                 "prechecks.txt", "memory_cgroup.txt", "time_v.txt", "executed_unit_bytes.txt", "runs_du.txt",
                 "smoke_stdout_extract.txt", "record_hashes.txt", "disk_before.txt", "disk_after.txt",
                 "smoke_start_utc.txt", "smoke_end_utc.txt", "DONE"):
        p = ev / name
        if p.exists():
            facts[name] = text(p)
    for name in ("prep/env.txt", "prep/env_freeze.txt", "prep/setup_time_v.txt", "prep/hf_revision_precheck.txt",
                 "prep/pins_committed_recheck.txt", "prep/pins_deployed_recheck.txt", "prep/setup_data.log"):
        p = ev / name
        if p.exists():
            facts[name] = text(p)

    # runs
    rows = {}
    for rp in sorted((ev / "runs").rglob("run_record.json")):
        d = json.loads(rp.read_text())
        rid = d.get("run_id")
        log = rp.parent / "run.log"
        log_text = text(log)
        ar = {}
        for key, pat in (("eval_rows", r"AR_INFO eval_rows=(\d+)"),
                         ("eval_batch_size", r"AR_INFO eval_batch_size=(\d+)"),
                         ("peak_vram_mb", r"AR_INFO peak_vram_mb=([0-9.]+)"),
                         ("causal_probe_max_change", r"AR_INFO causal_probe_max_change=([0-9.eE+-]+)"),
                         ("num_workers", r"AR_INFO num_workers=(\d+)"),
                         ("device", r"AR_INFO device=(\S+)")):
            m = re.search(pat, log_text)
            if m:
                ar[key] = m.group(1)
        iso = d.get("isolation") or {}
        ws = iso.get("worker_sandbox") or {}
        cg = iso.get("cgroup") or {}
        rows[rid] = {
            "executed": d.get("executed"),
            "outcome": d.get("outcome"),
            "elapsed_seconds": d.get("elapsed_seconds_info_only"),
            "run_budget": d.get("run_budget"),
            "process": d.get("process"),
            "node_spec_sha256": d.get("node_spec_sha256"),
            "frozen_pin_sha256": d.get("frozen_pin_sha256"),
            "limits": d.get("limits"),
            "determinism": {"not_forced": (d.get("determinism") or {}).get("not_forced"),
                            "shim_loaded": (d.get("determinism") or {}).get("shim_loaded")},
            "isolation": {"effective": iso.get("effective"), "waivers": iso.get("waivers"),
                          "exceptions": iso.get("exceptions"), "log_intact": iso.get("log_intact"),
                          "result_channel_overflow": iso.get("result_channel_overflow"),
                          "result_channel_sha256": iso.get("result_channel_sha256"),
                          "worker_sandbox": {"shared_dev_shm": ws.get("shared_dev_shm"),
                                             "root": ws.get("root"), "ro_flat": ws.get("ro_flat")},
                          "cgroup": {"kill": cg.get("kill"), "removed": cg.get("removed")}},
            "ar_info": ar,
            "record_sha256": sha(rp),
            "log_sha256": sha(log) if log.exists() else None,
            "result_channel_sha256": sha(rp.parent / "result_channel.txt") if (rp.parent / "result_channel.txt").exists() else None,
        }
    facts["runs"] = rows
    executed = {k: v for k, v in rows.items() if v.get("executed") is True and v.get("elapsed_seconds") is not None}
    facts["run_summary"] = {
        "records": len(rows), "executed": len([r for r in rows.values() if r.get("executed") is True]),
        "refused": [k for k, r in rows.items() if r.get("executed") is False],
        "missing": [r for r in EXPECTED_RUNS if r not in rows],
        "extra": [r for r in rows if r not in EXPECTED_RUNS],
        "B1_val_bpb": (rows.get("s000_baseline", {}).get("outcome") or {}).get("value"),
        "B2_val_bpb": (rows.get("B2", {}).get("outcome") or {}).get("value"),
        "peak_vram_by_run_mb": {k: v["ar_info"].get("peak_vram_mb") for k, v in rows.items() if v["ar_info"].get("peak_vram_mb")},
        "max_peak_vram_mb": max((float(v["ar_info"]["peak_vram_mb"]) for v in rows.values() if v["ar_info"].get("peak_vram_mb")), default=None),
    }

    for name in ("slowdown.json", "verify_full.json", "sampler/sampler_max.json", "gate/gate_not_applicable.txt"):
        p = ev / name
        if p.exists():
            try:
                facts[name] = json.loads(p.read_text())
            except json.JSONDecodeError:
                facts[name] = p.read_text(errors="replace")

    # GPU captures / monitor / lease
    gpu = {}
    for name in ("gpu/gpu_before.txt", "gpu/gpu_qualify.txt", "gpu/gpu_mid.txt", "gpu/gpu_after.txt",
                 "gpu/gpu_lease_status.txt", "gpu/CONTENTION_ABORT.txt"):
        p = ev / name
        gpu[name] = text(p) if p.exists() else None
    mon = text(ev / "gpu/co_tenant_monitor.log")
    mon_lines = [ln for ln in mon.splitlines() if re.match(r"^\d{4}-", ln)]
    foreign = [ln for ln in mon_lines if "foreign=[]" not in ln]
    facts["gpu"] = {
        "captures": gpu,
        "monitor_ticks": len(mon_lines),
        "monitor_ticks_with_foreign_app": len(foreign),
        "foreign_ticks_sample": foreign[:5],
        "monitor_log_sha256": sha(ev / "gpu/co_tenant_monitor.log") if (ev / "gpu/co_tenant_monitor.log").exists() else None,
    }
    cg_rows = text(ev / "sampler/cgroup_sampler.csv").splitlines()
    facts["cgroup_sampler"] = {"rows": len(cg_rows), "sha256": sha(ev / "sampler/cgroup_sampler.csv") if (ev / "sampler/cgroup_sampler.csv").exists() else None}
    facts["script_sha256"] = {p.name: sha(p) for p in sorted((ev / "scripts").glob("*")) if p.is_file()}
    (ev / "facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True, default=str) + "\n")
    brief = {"run_summary": facts["run_summary"],
             "measured": (facts.get("slowdown.json") or {}).get("measured"),
             "cgroup_sampler": facts["cgroup_sampler"],
             "monitor_ticks": facts["gpu"]["monitor_ticks"],
             "monitor_ticks_with_foreign_app": facts["gpu"]["monitor_ticks_with_foreign_app"]}
    print(json.dumps(brief, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
