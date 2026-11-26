#!/bin/bash
# Assemble the TASL-7 CPU stability capture set on the evidence root (read-only w.r.t. the runs).
set -eu
E=/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126
C=$E/captures
PY=/home/dowling/r1_trackg_20261125/venv_jax/bin/python
mkdir -p "$C/results" "$C/host" "$C/logs" "$C/runs" "$C/scripts"
cp -a "$E"/results/g*.json "$C/results/"
cp -a "$E"/host/*.txt "$C/host/"
cp -a "$E"/host/*.json "$C/host/" 2>/dev/null || true
cp -a "$E"/logs/ledger.tsv "$E"/logs/launch_console.log "$C/logs/"
cp -a "$E"/logs/precheck.txt "$C/logs/" 2>/dev/null || true
cp -a "$E"/logs/postcheck.txt "$C/logs/" 2>/dev/null || true
mkdir -p "$C/validation"
cp -a "$E"/validation/*.json "$C/validation/" 2>/dev/null || true
cp -a "$E"/validation/runs_validation "$C/validation/" 2>/dev/null || true
cp -a "$E"/logs/g*_r*.console.txt "$E"/logs/g*_r*.stderr.txt "$C/logs/" 2>/dev/null || true
cp -a "$E"/commands.txt "$C/" 2>/dev/null || true
cp -a "$E"/run_baseline_stability.py "$E"/launch_stress.sh "$E"/host_capture_tasl7.sh "$E"/verify_setup.sh \
      "$E"/collect_captures.sh "$E"/precheck_tasl7.sh "$E"/postcheck_tasl7.sh "$C/scripts/" 2>/dev/null || true
cp -a "$E"/freeze.txt "$C/scripts/" 2>/dev/null || true
for d in "$E"/runs/g*_r*; do
  [ -d "$d" ] || continue
  tag=$(basename "$d")
  mkdir -p "$C/runs/$tag"
  cp -a "$d/s000_baseline/run_record.json" "$d/s000_baseline/run.log" \
        "$d/s000_baseline/result_channel.txt" "$d/s000_baseline/determinism_shim.json" "$C/runs/$tag/" 2>/dev/null || true
done

"$PY" - "$E" "$C" <<'PY'
import json, sys, glob
E, C = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob(E + "/results/g*.json")):
    d = json.load(open(f)); r = d.get("run") or {}
    rows.append({
        "group": d["group"], "repeat": d["repeat"], "utc_start": d["utc_start"], "utc_end": d["utc_end"],
        "wall_seconds": d["wall_seconds"], "verdict": d["verdict"],
        "outcome_kind": (r.get("outcome") or {}).get("kind"),
        "outcome_reason": (r.get("outcome") or {}).get("reason"),
        "parent_returncode": (r.get("process") or {}).get("returncode"),
        "signal": r.get("signal"),
        "elapsed_seconds_info_only": r.get("elapsed_seconds_info_only"),
        "val_return": r.get("val_return"), "sealed_test_return": r.get("sealed_test_return"),
        "steps_max": r.get("steps_max"),
        "log_sha256": r.get("log_sha256"), "log_bytes": r.get("log_bytes"),
        "channel_sha256": r.get("channel_sha256"), "channel_bytes": r.get("channel_bytes"),
        "baseline_check_ok": (r.get("baseline_check") or {}).get("ok"),
        "scope_memory_peak_bytes": r.get("scope_memory_peak_bytes"),
        "isolation_effective": (r.get("isolation") or {}).get("effective"),
        "frozen_files_checked": (r.get("isolation") or {}).get("frozen_files_checked"),
        "affinity": (d.get("binding") or {}).get("affinity"),
        "cgroup": (d.get("binding") or {}).get("cgroup"),
        "driver_error": d.get("driver_error"),
    })
groups = []
for x in rows:
    if x["group"] not in groups:
        groups.append(x["group"])
group_verdicts = {}
for g in groups:
    rs = [x for x in rows if x["group"] == g]
    npass = sum(1 for x in rs if x["verdict"] == "PASS")
    group_verdicts[g] = ("PASS %d/%d" % (npass, len(rs))) if npass == len(rs) else ("FAIL %d/%d" % (len(rs) - npass, len(rs)))
passing = [x for x in rows if x["verdict"] == "PASS"]
failing = [x for x in rows if x["verdict"] != "PASS"]
starts = [x["utc_start"] for x in rows if x.get("utc_start")]
ends = [x["utc_end"] for x in rows if x.get("utc_end")]
summary = {
    "schema": "tasl7_cpu_stability_summary/v1",
    "utc_first_start": min(starts) if starts else None, "utc_last_end": max(ends) if ends else None,
    "host": {"hostname": "TASL-7", "cpu": "AMD Ryzen 9 7900X 12-Core Processor", "model": "97", "stepping": "2",
             "family": "25", "microcode_unique": sorted({ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo")
                                                       if ln.startswith("microcode")}),
             "microcode_per_cpu_count": sum(1 for ln in open("/proc/cpuinfo") if ln.startswith("microcode")),
             "governor": open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read().strip(),
             "cpufreq_driver": open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver").read().strip(),
             "epp": open("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference").read().strip(),
             "amd_pstate_status": open("/sys/devices/system/cpu/amd_pstate/status").read().strip(),
             "cpu_max_khz": open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read().strip(),
             "kernel": "6.8.0-149-generic", "os": "Ubuntu 22.04.5 LTS", "logical_cpus": 24, "groups": groups},
    "kit": {"path": "/home/dowling/r1_trackg_20261125/harness_metamaze",
            "head": "aa354485bff6b5746c48ddadcb50d92e9c6f3645", "branch": "mac-trackg-mountaincar-20261125",
            "base": "c025f89aeafc2199bf3487b4bcaa16678273c702"},
    "env": {"path": "/home/dowling/r1_trackg_20261125/venv_jax",
            "freeze_sha256": "630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9"},
    "data_manifest_sha256": "e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000",
    "command": ("the reviewed census baseline run only (tests/trackg/port_smoke_gpu -> "
                "port_support.run_smoke_campaign with an empty proposal list): s000_baseline, full 2,000,000 "
                "steps, seeds 8001/8001"),
    "groups": groups, "repeats": 3, "rows": rows, "group_verdicts": group_verdicts,
    "determinism": {
        "passing_runs": len(passing),
        "passing_runs_log_hashes": sorted({x["log_sha256"] for x in passing}),
        "passing_runs_channel_hashes": sorted({x["channel_sha256"] for x in passing}),
        "passing_runs_identical_logs": len({x["log_sha256"] for x in passing}) == 1 if passing else None,
        "passing_runs_identical_channels": len({x["channel_sha256"] for x in passing}) == 1 if passing else None,
        "passing_vals": sorted({x["val_return"] for x in passing if x["val_return"] is not None}),
        "passing_sealed": sorted({x["sealed_test_return"] for x in passing if x["sealed_test_return"] is not None}),
        "failing_runs": len(failing),
        "failing_runs_log_hashes": sorted({x["log_sha256"] for x in failing}),
        "failing_runs_identical_logs": len({x["log_sha256"] for x in failing}) == 1 if failing else None,
        "failing_runs_channel_hashes": sorted({x["channel_sha256"] for x in failing}),
    },
}
if passing:
    summary["conclusion"] = ("%d/%d runs PASS; passing run.log hashes: %s; passing channel hashes: %s; "
                             "val_return %s; sealed %s." % (
                                 len(passing), len(rows),
                                 ", ".join(h[:16] for h in summary["determinism"]["passing_runs_log_hashes"]),
                                 ", ".join(h[:16] for h in summary["determinism"]["passing_runs_channel_hashes"]),
                                 summary["determinism"]["passing_vals"], summary["determinism"]["passing_sealed"]))
else:
    summary["conclusion"] = "no passing runs"
with open(C + "/summary.json", "w") as fh:
    json.dump(summary, fh, indent=2, sort_keys=True); fh.write("\n")
print("SUMMARY_JSON_WRITTEN")
PY

{
  echo "TASL-7 CPU-set stability check - MetaMaze baseline (reviewed census baseline run), TASL-7, no GPU, no system change"
  echo "utc: $(tail -n +2 "$E/logs/ledger.tsv" | cut -f3 | sort | head -1) -> $(tail -n +2 "$E/logs/ledger.tsv" | cut -f4 | sort | tail -1)"
  echo "host: TASL-7, AMD Ryzen 9 7900X 12-Core (Zen 4, family 25 / model 97 / stepping 2), 24 logical CPUs (0-23),"
  echo "      microcode $(grep -E '^microcode' /proc/cpuinfo | head -1 | cut -d: -f2 | tr -d ' '), kernel $(uname -r), Ubuntu 22.04.5"
  echo "kit: /home/dowling/r1_trackg_20261125/harness_metamaze @ aa354485bff6b5746c48ddadcb50d92e9c6f3645 (mac-trackg-mountaincar-20261125)"
  echo "env: /home/dowling/r1_trackg_20261125/venv_jax freeze 630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9 (jax 0.4.35, CPU)"
  echo "data: /home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze manifest e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000"
  echo "test: the reviewed census baseline run only (s000_baseline), full 2,000,000 steps, seeds 8001/8001, one run per (group,repeat), 6 groups x 3 repeats sequential"
  echo 'scope: each run in its own systemd-run --user --scope (Delegate=yes MemoryMax=8G MemorySwapMax=0); CUDA_VISIBLE_DEVICES=""; taskset -c <group>; PATH=venv_jax/bin first'
  echo
  echo "verdicts:"
  "$PY" - "$C/summary.json" <<'PY2'
import json, sys
s = json.load(open(sys.argv[1]))
for g in s["groups"]:
    print("  CPUs %-6s %s" % (g, s["group_verdicts"][g]))
PY2
  echo
  printf "%-6s %-3s %-8s %-16s %-3s %-6s %-8s %-10s %-9s %s\n" group rep verdict outcome rc signal wall_s val_return sealed log_sha
  "$PY" - "$E" <<'PY3'
import glob, json, sys
E = sys.argv[1]
for f in sorted(glob.glob(E + "/results/g*.json")):
    d = json.load(open(f)); r = d.get("run") or {}
    print("%-6s %-3s %-8s %-16s %-3s %-6s %-8s %-10s %-9s %s" % (
        d["group"], d["repeat"], d["verdict"], (r.get("outcome") or {}).get("kind"),
        (r.get("process") or {}).get("returncode"), r.get("signal") or "-", d["wall_seconds"],
        r.get("val_return") or "-", r.get("sealed_test_return") or "-", (r.get("log_sha256") or "")[:16]))
PY3
  echo
  echo "determinism: see summary.json - passing run.log / result-channel sha256 sets and val/sealed values."
  echo "no system change, no deletion, no GPU lease, no push. ENGINEERING_ONLY."
} > "$C/summary.txt"

cd "$C"
find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS
sha256sum -c SHA256SUMS > /dev/null && echo "REMOTE_SHA256SUMS_OK"
echo "=== capture file count: $(wc -l < SHA256SUMS)"
echo "CAPTURES_SHA=$(sha256sum SHA256SUMS | cut -d' ' -f1)"
cat "$C/summary.txt"
