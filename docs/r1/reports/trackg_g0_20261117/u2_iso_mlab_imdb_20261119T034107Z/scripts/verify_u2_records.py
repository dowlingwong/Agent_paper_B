"""Full verification of one U2 isolated-node port_smoke_gpu run (the unit's record + checklist gate).

Usage: python3 verify_u2_records.py <runs_root> --node NODE --gpu UUID --cpus CPUS [--smoke-log PATH]

Checks, for the expected 9 records (s000_baseline, s001 refused frozen diff, s002 broken diff,
s003 first edit, E1-E4 declared edits, B2 repeat baseline):
  * 9 run_record.json, 8 executed, s001 executed:false with outcome null and no isolation fields;
  * every executed record: isolation.effective true, waivers {}, exceptions [], log_intact true,
    result_channel_overflow false + result_channel_sha256 present, cgroup.kill method cgroup.kill
    with empty_after true and removed true, determinism.not_forced == ["dataloader_workers"],
    limits.external_limit the exact unit string, limits.gpu_uuids [UUID], cpu_list CPUS,
    memory_method external, provisional_timeout 1800, timeout_factor 3.0;
  * outcome kinds: baseline/edits/repeat ok, s002 divergent/non_finite_loss;
  * baseline and B2 carry elapsed_seconds_info_only and outcome.value, sealed.test_accuracy present;
  * frozen_pin_sha256 constant across records;
  * when --smoke-log is given: CHECKLIST_E_PASSED <node>, one JSON line per run (9), no 'synthetic'.

Writes JSON to stdout; exit 1 on any issue.
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

    pins = set()
    for rid in EXPECTED_RUNS:
        if rid not in recs:
            continue
        rp, d = recs[rid]
        iso = d.get("isolation") or {}
        row = {
            "run_id": rid,
            "executed": d.get("executed"),
            "record": str(rp),
            "record_sha256": sha(rp),
            "log": str(rp.parent / "run.log"),
            "log_sha256": sha(rp.parent / "run.log") if (rp.parent / "run.log").exists() else None,
            "outcome": d.get("outcome"),
            "elapsed_seconds_info_only": d.get("elapsed_seconds_info_only"),
            "sealed_test_accuracy": (d.get("sealed") or {}).get("test_accuracy"),
            "frozen_pin_sha256": d.get("frozen_pin_sha256"),
        }
        pins.add(d.get("frozen_pin_sha256"))
        if rid == "s001":
            if d.get("executed") is not False:
                issues.append({"run_id": rid, "error": "refused frozen diff is not executed:false"})
            if d.get("outcome") is not None:
                issues.append({"run_id": rid, "error": "refused diff has an outcome"})
            if iso:
                issues.append({"run_id": rid, "error": "refused diff carries isolation fields"})
            refusal = ((d.get("diff") or {}).get("refusal"))
            if refusal != "scope_violation":
                issues.append({"run_id": rid, "error": f"refusal is {refusal}, expected scope_violation"})
            rows.append(row)
            continue
        if d.get("executed") is not True:
            issues.append({"run_id": rid, "error": "executed is not true"})
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
            "determinism.not_forced == [dataloader_workers]": (d.get("determinism") or {}).get("not_forced") == ["dataloader_workers"],
            "node is the unit node": d.get("node") == args.node,
            "limits.external_limit exact": (d.get("limits") or {}).get("external_limit") == EXTERNAL_LIMIT,
            "limits.gpu_uuids == [UUID]": (d.get("limits") or {}).get("gpu_uuids") == [args.gpu],
            "limits.cpu_list == cpus": (d.get("limits") or {}).get("cpu_list") == cpus,
            "memory_method external": (d.get("limits") or {}).get("memory_method") == "external",
            "provisional_timeout 1800": (d.get("limits") or {}).get("provisional_timeout_seconds") == 1800.0,
            "timeout_factor 3.0": (d.get("limits") or {}).get("timeout_factor") == 3.0,
            "outcome kind ok": (d.get("outcome") or {}).get("kind") == "ok",
            "outcome.value present": (d.get("outcome") or {}).get("value") is not None,
            "elapsed_seconds_info_only present": d.get("elapsed_seconds_info_only") is not None,
            "sealed.test_accuracy present": (d.get("sealed") or {}).get("test_accuracy") is not None,
            "frozen_pin_sha256 full 64-hex": isinstance(d.get("frozen_pin_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", d.get("frozen_pin_sha256")) is not None,
        }
        if rid == "s002":
            # s002 is the deliberately broken diff: divergent/non_finite_loss, no value
            checks.pop("outcome kind ok", None)
            checks.pop("outcome.value present", None)
            checks["outcome divergent/non_finite_loss"] = (
                (d.get("outcome") or {}).get("kind") == "divergent"
                and (d.get("outcome") or {}).get("reason") == "non_finite_loss"
            )
        for name, ok in checks.items():
            if not ok:
                issues.append({"run_id": rid, "error": name})
        row["checks"] = checks
        rows.append(row)
    if len(pins) > 1:
        issues.append({"error": f"deployed pin differs across records: {sorted(map(str, pins))}"})

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
        "deployed_pin_sha256": next(iter(pins)) if len(pins) == 1 else sorted(map(str, pins)),
        "smoke": smoke,
        "issues": issues,
        "ok": not issues,
        "rows": rows,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
