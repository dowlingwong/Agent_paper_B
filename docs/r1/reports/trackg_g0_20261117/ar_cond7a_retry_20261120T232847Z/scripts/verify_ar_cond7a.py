"""Full verification of the R1-TRACKG-AR-COND7 option A isolated autoresearch smoke.

Usage: python3 verify_ar_cond7a.py <runs_root> --node autoresearch_fixedtokens --gpu UUID --cpus CPUS \
          --smoke-log PATH --committed-pin PIN --deployed-pin PIN --node-spec-sha SHA

Checks: 9 records / 8 executed / s001 refused; isolation effective true, waivers {}, exceptions [], no
shared_dev_shm (private /dev/shm), log/result-channel/cgroup kill; CPU/GPU limits and the one-line external
limit; run_budget tokens 32768000; outcome val_bpb finite for the ok runs; s002 divergent non-finite; B2 repeat
equal to B1; determinism not_forced/shim_loaded; process killed_with null, timed_out false, ok returncode 0;
no CUDA IPC error markers in any run log (and AR_INFO eval_rows/eval_batch_size/peak_vram_mb recorded);
node-spec canonical sha; committed vs deployed pin separately; CHECKLIST_E_PASSED, one JSON line per run, no
synthetic marker. Exit 1 on any issue.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

EXPECTED_RUNS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]
EXECUTED = [r for r in EXPECTED_RUNS if r != "s001"]
EXTERNAL_LIMIT = ("external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                  "(enforced cgroup)")
RUN_BUDGET = {"kind": "tokens", "value": 32768000}
CUDA_IPC_ERROR_MARKERS = ["invalid resource handle", "cuda_open", "bind_cuda", "_share_cuda_",
                          "_new_shared_cuda", "CUDA IPC"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_root", type=Path)
    ap.add_argument("--node", required=True)
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--cpus", required=True)
    ap.add_argument("--smoke-log", default=None)
    ap.add_argument("--committed-pin", default="")
    ap.add_argument("--deployed-pin", default="")
    ap.add_argument("--node-spec-sha", default="")
    args = ap.parse_args()
    root = args.runs_root.resolve()
    cpus = []
    for part in args.cpus.split(","):
        lo, _, hi = part.partition("-")
        cpus += list(range(int(lo), int(hi or lo) + 1))
    issues, rows = [], []
    recs = {}
    for rp in sorted(root.rglob("run_record.json")):
        d = json.loads(rp.read_text())
        rid = d.get("run_id")
        if rid in recs:
            issues.append({"error": f"duplicate run_id {rid}", "record": str(rp)})
        recs[rid] = (rp, d)
    missing = [r for r in EXPECTED_RUNS if r not in recs]
    extra = [r for r in recs if r not in EXPECTED_RUNS]
    if missing:
        issues.append({"error": f"missing run records: {missing}"})
    if extra:
        issues.append({"error": f"unexpected run records: {extra}"})

    pins, sealed_keys, not_forced_values = set(), set(), set()
    ipc_hits, ar_info = [], {}
    b1 = b2 = None
    for rid in EXPECTED_RUNS:
        if rid not in recs:
            continue
        rp, d = recs[rid]
        iso = d.get("isolation") or {}
        sealed = d.get("sealed") or {}
        det = d.get("determinism") or {}
        nf = det.get("not_forced")
        if isinstance(nf, list):
            not_forced_values.update(nf)
        log = rp.parent / "run.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        for marker in CUDA_IPC_ERROR_MARKERS:
            if marker.lower() in text.lower():
                ipc_hits.append({"run_id": rid, "marker": marker})
        info = {}
        for pat in (r"AR_INFO eval_rows=(\d+)", r"AR_INFO eval_batch_size=(\d+)",
                    r"AR_INFO peak_vram_mb=([0-9.]+)", r"AR_INFO causal_probe_max_change=([0-9.eE+-]+)"):
            m = re.search(pat, text)
            if m:
                info[pat.split("=")[0].split()[-1]] = m.group(1)
        if info:
            ar_info[rid] = info
        sealed_keys.update(sealed.keys())
        pins.add(d.get("frozen_pin_sha256"))
        row = {
            "run_id": rid,
            "executed": d.get("executed"),
            "record": str(rp),
            "record_sha256": sha(rp),
            "log": str(log),
            "log_sha256": sha(log) if log.exists() else None,
            "outcome": d.get("outcome"),
            "elapsed_seconds_info_only": d.get("elapsed_seconds_info_only"),
            "run_budget": d.get("run_budget"),
            "sealed": sealed,
            "frozen_pin_sha256": d.get("frozen_pin_sha256"),
            "determinism": {"not_forced": nf, "shim_loaded": det.get("shim_loaded")},
            "process": d.get("process"),
            "ar_info": info,
        }
        if rid == "s001":
            if d.get("executed") is not False:
                issues.append({"run_id": rid, "error": "refused frozen diff is not executed:false"})
            if d.get("outcome") is not None:
                issues.append({"run_id": rid, "error": "refused diff has an outcome"})
            if iso:
                issues.append({"run_id": rid, "error": "refused diff carries isolation fields"})
            if (d.get("diff") or {}).get("refusal") != "scope_violation":
                issues.append({"run_id": rid, "error": "refusal is not scope_violation"})
            rows.append(row)
            continue
        if d.get("executed") is not True:
            issues.append({"run_id": rid, "error": "executed is not true"})
        proc = d.get("process") or {}
        limits = d.get("limits") or {}
        ws = iso.get("worker_sandbox") or {}
        checks = {
            "isolation.effective is true": iso.get("effective") is True,
            "isolation.waivers == {}": iso.get("waivers") == {},
            "isolation.exceptions == [] (no shared_dev_shm)": iso.get("exceptions") == [],
            "isolation.log_intact is true": iso.get("log_intact") is True,
            "result_channel_overflow is false": iso.get("result_channel_overflow") is False,
            "result_channel_sha256 present": bool(iso.get("result_channel_sha256")),
            "cgroup.kill method cgroup.kill": ((iso.get("cgroup") or {}).get("kill") or {}).get("method") == "cgroup.kill",
            "cgroup.kill empty_after true": ((iso.get("cgroup") or {}).get("kill") or {}).get("empty_after") is True,
            "cgroup removed true": (iso.get("cgroup") or {}).get("removed") is True,
            "worker private /dev/shm (shared_dev_shm false)": ws.get("shared_dev_shm") is False,
            "worker sandbox present": bool(ws),
            "determinism.not_forced is a non-empty list": isinstance(nf, list) and len(nf) > 0,
            "determinism.shim_loaded is a bool": isinstance(det.get("shim_loaded"), bool),
            "limits.external_limit exact": limits.get("external_limit") == EXTERNAL_LIMIT,
            "limits.gpu_uuids == [UUID]": limits.get("gpu_uuids") == [args.gpu],
            "limits.cpu_list == cpus": limits.get("cpu_list") == cpus,
            "limits.memory_method external": limits.get("memory_method") == "external",
            "provisional_timeout 1800": limits.get("provisional_timeout_seconds") == 1800.0,
            "timeout_factor 3.0": limits.get("timeout_factor") == 3.0,
            "run_budget tokens 32768000": d.get("run_budget") == RUN_BUDGET,
            "process.killed_with is null": proc.get("killed_with") is None,
            "process.timed_out is false": proc.get("timed_out") is False,
            "process.returncode 0": proc.get("returncode") == 0,
            "node is the unit node": d.get("node") == args.node,
            "node_spec_sha256 expected": (not args.node_spec_sha) or d.get("node_spec_sha256") == args.node_spec_sha,
            "outcome kind ok": (d.get("outcome") or {}).get("kind") == "ok",
            "elapsed_seconds_info_only present": d.get("elapsed_seconds_info_only") is not None,
            "frozen_pin_sha256 full 64-hex": isinstance(d.get("frozen_pin_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", d.get("frozen_pin_sha256")) is not None,
        }
        val = (d.get("outcome") or {}).get("value")
        if rid == "s002":
            checks.pop("outcome kind ok", None)
            checks["outcome divergent/non-finite"] = (
                (d.get("outcome") or {}).get("kind") == "divergent"
                and (d.get("outcome") or {}).get("reason") in ("non_finite_loss", "non_finite_metric")
            )
        else:
            checks["outcome.value val_bpb finite"] = isinstance(val, (int, float)) and math.isfinite(val)
        if rid == "s000_baseline":
            b1 = d.get("elapsed_seconds_info_only")
        if rid == "B2":
            b2 = d.get("elapsed_seconds_info_only")
        for name, ok in checks.items():
            if not ok:
                issues.append({"run_id": rid, "error": name})
        row["checks"] = checks
        rows.append(row)
    # B2 metric repeat equals B1
    try:
        v1 = (recs["s000_baseline"][1].get("outcome") or {}).get("value")
        v2 = (recs["B2"][1].get("outcome") or {}).get("value")
        if v1 is None or v2 is None or v1 != v2:
            issues.append({"error": "B2 metric does not repeat B1 exactly", "B1": v1, "B2": v2})
    except KeyError:
        pass
    if ipc_hits:
        issues.append({"error": "CUDA IPC marker found in run logs", "hits": ipc_hits})
    if len(pins) != 1:
        issues.append({"error": f"deployed pin differs across records: {sorted(map(str, pins))}"})
    deployed_pin = next(iter(pins)) if len(pins) == 1 else None
    if args.deployed_pin and deployed_pin != args.deployed_pin:
        issues.append({"error": "deployed pin != expected recomputed deployed pin",
                       "deployed": deployed_pin, "expected": args.deployed_pin})
    if args.committed_pin and not re.fullmatch(r"[0-9a-f]{64}", args.committed_pin):
        issues.append({"error": "committed pin argument is not full 64-hex"})
    sealed_key = next(iter(sealed_keys)) if len(sealed_keys) == 1 else (None if not sealed_keys else sorted(sealed_keys))

    smoke = None
    if args.smoke_log:
        sp = Path(args.smoke_log)
        text = sp.read_text(errors="replace")
        json_lines = [ln for ln in text.splitlines() if ln.startswith("{")]
        smoke = {
            "smoke_log": str(sp),
            "smoke_log_sha256": sha(sp),
            "checklist_e_passed": f"CHECKLIST_E_PASSED {args.node}" in text,
            "json_run_lines": len(json_lines),
            "synthetic_marker": "synthetic" in text.lower(),
            "systemd_run_rc": next((ln.split("=", 1)[1] for ln in text.splitlines() if ln.startswith("systemd_run_rc=")), None),
        }
        if not smoke["checklist_e_passed"]:
            issues.append({"error": "CHECKLIST_E_PASSED line missing from the smoke log"})
        if smoke["json_run_lines"] != len(EXPECTED_RUNS):
            issues.append({"error": f"{smoke['json_run_lines']} JSON run lines, expected {len(EXPECTED_RUNS)}"})
        if smoke["synthetic_marker"]:
            issues.append({"error": "synthetic marker in the smoke log"})
        if smoke["systemd_run_rc"] != "0":
            issues.append({"error": f"systemd_run_rc is {smoke['systemd_run_rc']}"})

    executed_count = len([r for r in rows if r["executed"] is True])
    peak_vram_list = [float(v["peak_vram_mb"]) for v in ar_info.values() if v.get("peak_vram_mb")]
    out = {
        "node": args.node,
        "runs_root": str(root),
        "expected_runs": EXPECTED_RUNS,
        "records": len(recs),
        "executed_records": executed_count,
        "expected_executed": len(EXECUTED),
        "refused_s001": recs.get("s001", (None, {}))[1].get("executed") is False if "s001" in recs else None,
        "deployed_pin_sha256": deployed_pin,
        "committed_pin_sha256": args.committed_pin or None,
        "sealed_key": sealed_key,
        "not_forced_values": sorted(not_forced_values),
        "no_cuda_ipc_error": not ipc_hits,
        "ipc_hits": ipc_hits,
        "ar_info": ar_info,
        "peak_vram_mb_list": peak_vram_list,
        "B1_seconds": b1,
        "B2_seconds": b2,
        "smoke": smoke,
        "issues": issues,
        "ok": not issues,
        "rows": rows,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
