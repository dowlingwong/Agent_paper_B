"""Full verification of the CPU node mlgym_houseprice U2 port_smoke_gpu run.

Usage: python3 verify_u2_records_cpu.py <runs_root> --node mlgym_houseprice --cpus "95,94,..." \
          --smoke-log PATH --committed-pin PIN --deployed-expected PIN --node-spec-sha SHA

Checks: 9 records / 8 executed / s001 refused; isolation effective/waivers/exceptions/log/result-channel/cgroup
kill; CPU-node limits (gpu_uuids [], cpu_list, memory_method external, exact one-line external_limit,
provisional 1800 s, timeout_factor 3.0); run_budget steps 1 (one fit); outcome val_rmse for ok runs,
s002 divergent non-finite; sealed test_rmse; determinism not_forced list + shim_loaded; process killed_with
null, timed_out false, ok returncode 0; the run's AR_DATA line records the author csv sha256/md5; node-spec
sha; full-hex deployed pin (separate from the committed pin) and full-hex committed pin; CHECKLIST_E_PASSED,
one JSON line per run, no synthetic marker. Exit 1 on any issue.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED_RUNS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]
EXECUTED = [r for r in EXPECTED_RUNS if r != "s001"]
EXTERNAL_LIMIT = ("external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                  "(enforced cgroup)")
CSV_SHA = "1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41"
CSV_MD5 = "80ccab65fb115cbad143dbbd2bcd5577"


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
    ap.add_argument("--cpus", required=True)
    ap.add_argument("--smoke-log", default=None)
    ap.add_argument("--committed-pin", default="")
    ap.add_argument("--deployed-expected", default="")
    ap.add_argument("--node-spec-sha", default="")
    args = ap.parse_args()
    root = args.runs_root.resolve()
    cpus = [int(x) for x in args.cpus.replace("-", ",").split(",") if x.strip()]
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
    ar_data = None
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
        row = {
            "run_id": rid,
            "executed": d.get("executed"),
            "record": str(rp),
            "record_sha256": sha(rp),
            "log": str(rp.parent / "run.log"),
            "log_sha256": sha(rp.parent / "run.log") if (rp.parent / "run.log").exists() else None,
            "outcome": d.get("outcome"),
            "elapsed_seconds_info_only": d.get("elapsed_seconds_info_only"),
            "sealed": sealed,
            "frozen_pin_sha256": d.get("frozen_pin_sha256"),
            "node_spec_sha256": d.get("node_spec_sha256"),
            "run_budget": d.get("run_budget"),
            "determinism": {"not_forced": nf, "shim_loaded": det.get("shim_loaded")},
            "process": d.get("process"),
        }
        pins.add(d.get("frozen_pin_sha256"))
        for k in sealed:
            sealed_keys.add(k)
        if ar_data is None and (rp.parent / "run.log").exists():
            m = re.search(r"AR_DATA houseprice_sha256=(\S+) md5=(\S+) same_as_mlgym_copy=(\S+)",
                          (rp.parent / "run.log").read_text(errors="replace"))
            if m:
                ar_data = {"houseprice_sha256": m.group(1), "md5": m.group(2), "same_as_mlgym_copy": m.group(3)}
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
        checks = {
            "isolation.effective is true": iso.get("effective") is True,
            "isolation.waivers == {}": iso.get("waivers") == {},
            "isolation.exceptions == []": iso.get("exceptions") == [],
            "isolation.log_intact is true": iso.get("log_intact") is True,
            "result_channel_overflow is false": iso.get("result_channel_overflow") is False,
            "result_channel_sha256 present": bool(iso.get("result_channel_sha256")),
            "cgroup.kill method cgroup.kill": ((iso.get("cgroup") or {}).get("kill") or {}).get("method") == "cgroup.kill",
            "cgroup.kill empty_after true": ((iso.get("cgroup") or {}).get("kill") or {}).get("empty_after") is True,
            "cgroup removed true": (iso.get("cgroup") or {}).get("removed") is True,
            "determinism.not_forced is a non-empty list": isinstance(nf, list) and len(nf) > 0,
            "determinism.shim_loaded is a bool": isinstance(det.get("shim_loaded"), bool),
            "limits.external_limit exact": limits.get("external_limit") == EXTERNAL_LIMIT,
            "limits.gpu_uuids == [] (CPU node)": limits.get("gpu_uuids") == [],
            "limits.cpu_list == selected cpus": limits.get("cpu_list") == cpus,
            "limits.memory_method external": limits.get("memory_method") == "external",
            "provisional_timeout 1800": limits.get("provisional_timeout_seconds") == 1800.0,
            "timeout_factor 3.0": limits.get("timeout_factor") == 3.0,
            "run_budget steps 1 (one fit)": d.get("run_budget") == {"kind": "steps", "value": 1},
            "process.killed_with is null": proc.get("killed_with") is None,
            "process.timed_out is false": proc.get("timed_out") is False,
            "process.returncode 0": proc.get("returncode") == 0,
            "node is the unit node": d.get("node") == args.node,
            "node_spec_sha256 full 64-hex (kit canonical hash)": isinstance(d.get("node_spec_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", d.get("node_spec_sha256")) is not None,
            "outcome kind ok": (d.get("outcome") or {}).get("kind") == "ok",
            "outcome.value (val_rmse) present": (d.get("outcome") or {}).get("value") is not None,
            "elapsed_seconds_info_only present": d.get("elapsed_seconds_info_only") is not None,
            "sealed value present": bool(sealed),
            "frozen_pin_sha256 full 64-hex": isinstance(d.get("frozen_pin_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", d.get("frozen_pin_sha256")) is not None,
        }
        if rid == "s002":
            checks.pop("outcome kind ok", None)
            checks.pop("outcome.value (val_rmse) present", None)
            checks["outcome divergent/non-finite"] = (
                (d.get("outcome") or {}).get("kind") == "divergent"
                and (d.get("outcome") or {}).get("reason") in ("non_finite_loss", "non_finite_metric")
            )
        for name, ok in checks.items():
            if not ok:
                issues.append({"run_id": rid, "error": name})
        row["checks"] = checks
        rows.append(row)
    if len(pins) != 1:
        issues.append({"error": f"deployed pin differs across records: {sorted(map(str, pins))}"})
    deployed_pin = next(iter(pins)) if len(pins) == 1 else None
    if not (isinstance(deployed_pin, str) and re.fullmatch(r"[0-9a-f]{64}", deployed_pin)):
        issues.append({"error": "deployed pin is not a full 64-hex value", "deployed": deployed_pin})
    if args.committed_pin and not re.fullmatch(r"[0-9a-f]{64}", args.committed_pin):
        issues.append({"error": "committed pin argument is not full 64-hex", "committed": args.committed_pin})
    if ar_data is None:
        issues.append({"error": "AR_DATA houseprice_sha256/md5 line missing from the run logs"})
    else:
        if ar_data["houseprice_sha256"] != CSV_SHA:
            issues.append({"error": "AR_DATA houseprice_sha256 != author csv sha256", "ar_data": ar_data})
        if ar_data["md5"] != CSV_MD5:
            issues.append({"error": "AR_DATA md5 != author csv md5", "ar_data": ar_data})
    if len(sealed_keys) != 1:
        issues.append({"error": f"sealed keys are not unique: {sorted(sealed_keys)}"})
    sealed_key = next(iter(sealed_keys)) if len(sealed_keys) == 1 else None

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
        "deployed_pin_expected_match": (deployed_pin == args.deployed_expected) if args.deployed_expected else None,
        "sealed_key": sealed_key,
        "not_forced_values": sorted(not_forced_values),
        "cpu_node": True,
        "cpus": cpus,
        "ar_data_line": ar_data,
        "smoke": smoke,
        "issues": issues,
        "ok": not issues,
        "rows": rows,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
