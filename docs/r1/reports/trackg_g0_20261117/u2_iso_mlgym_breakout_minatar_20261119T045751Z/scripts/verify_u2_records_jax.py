"""Full verification of the JAX node mlgym_breakout_minatar U2 port_smoke_gpu run.

Usage: python3 verify_u2_records_jax.py <runs_root> --node mlgym_breakout_minatar --gpu UUID --cpus CPUS [--smoke-log PATH]
Exit 1 on any issue.

JAX-node differences from the torch verifier:
  * the manager record has no `sealed.test_accuracy`; the sealed value is the runtime record's
    `sealed.test_return` (source: the run's result_channel `AR_TEST test_return=...`), recorded as
    `sealed_key`; it must be present on the baseline/repeat (accept any single numeric key);
  * `determinism.not_forced` is the torch-free JAX list (torch_absent reasons): the verifier records it
    and checks it is a non-empty list of strings and that every not_forced setting carries a
    `torch_absent` reason, but does not require the torch list;
  * this node has no data setup, so the deployed run-record pin must equal the committed-file pin
    cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4 (an inequality is a pin/data anomaly);
  * `process.killed_with` must be null and `timed_out` false.
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
COMMITTED_PIN = "cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4"


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
    sealed_keys = set()
    not_forced_values = set()
    for rid in EXPECTED_RUNS:
        if rid not in recs:
            continue
        rp, d = recs[rid]
        iso = d.get("isolation") or {}
        sealed = d.get("sealed") or {}
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
            "determinism_not_forced": (d.get("determinism") or {}).get("not_forced"),
        }
        pins.add(d.get("frozen_pin_sha256"))
        for k, v in sealed.items():
            sealed_keys.add(k)
        nf = (d.get("determinism") or {}).get("not_forced")
        if isinstance(nf, list):
            not_forced_values.update(nf)
        if rid == "s001":
            if d.get("executed") is not False:
                issues.append({"run_id": rid, "error": "refused frozen diff is not executed:false"})
            if d.get("outcome") is not None:
                issues.append({"run_id": rid, "error": "refused diff has an outcome"})
            if iso:
                issues.append({"run_id": rid, "error": "refused diff carries isolation fields"})
            refusal = (d.get("diff") or {}).get("refusal")
            if refusal != "scope_violation":
                issues.append({"run_id": rid, "error": f"refusal is {refusal}, expected scope_violation"})
            rows.append(row)
            continue
        if d.get("executed") is not True:
            issues.append({"run_id": rid, "error": "executed is not true"})
        det = d.get("determinism") or {}
        nf = det.get("not_forced")
        settings = det.get("settings") or []
        nf_reasons = [s.get("reason", "") for s in settings if s.get("status") == "not_forced"]
        torch_nf_reasons = [s.get("reason", "") for s in settings
                            if s.get("status") == "not_forced" and "torch" in str(s.get("setting", ""))]
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
            "determinism.not_forced is a non-empty list of strings": isinstance(nf, list) and len(nf) > 0
            and all(isinstance(x, str) for x in nf),
            "determinism.not_forced torch settings carry a torch_absent reason": (
                len(torch_nf_reasons) > 0 and all("torch_absent" in str(r) for r in torch_nf_reasons)
            ),
            "determinism.not_forced includes dataloader_workers": "dataloader_workers" in (nf or []),
            "determinism shim_loaded is true": det.get("shim_loaded") is True,
            "node is the unit node": d.get("node") == args.node,
            "limits.external_limit exact": (d.get("limits") or {}).get("external_limit") == EXTERNAL_LIMIT,
            "limits.gpu_uuids == [UUID]": (d.get("limits") or {}).get("gpu_uuids") == [args.gpu],
            "limits.cpu_list == cpus": (d.get("limits") or {}).get("cpu_list") == cpus,
            "limits.memory_method external": (d.get("limits") or {}).get("memory_method") == "external",
            "provisional_timeout 1800": (d.get("limits") or {}).get("provisional_timeout_seconds") == 1800.0,
            "timeout_factor 3.0": (d.get("limits") or {}).get("timeout_factor") == 3.0,
            "process.killed_with is null": (d.get("process") or {}).get("killed_with") is None,
            "process.timed_out is false": (d.get("process") or {}).get("timed_out") is False,
            "process.returncode 0 for ok runs": (
                (d.get("outcome") or {}).get("kind") != "ok"
                or (d.get("process") or {}).get("returncode") == 0
            ),
            "node_spec_sha256 present": bool(d.get("node_spec_sha256")),
            "outcome kind ok": (d.get("outcome") or {}).get("kind") == "ok",
            "outcome.value present": (d.get("outcome") or {}).get("value") is not None,
            "elapsed_seconds_info_only present": d.get("elapsed_seconds_info_only") is not None,
            "sealed value present": bool(sealed),
            "frozen_pin_sha256 full 64-hex": isinstance(d.get("frozen_pin_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", d.get("frozen_pin_sha256")) is not None,
        }
        if rid == "s002":
            checks["outcome divergent/non-finite"] = (
                (d.get("outcome") or {}).get("kind") == "divergent"
                and (d.get("outcome") or {}).get("reason") in ("non_finite_loss", "non_finite_metric")
            )
            checks.pop("outcome kind ok", None)
            checks.pop("outcome.value present", None)
        for name, ok in checks.items():
            if not ok:
                issues.append({"run_id": rid, "error": name})
        row["checks"] = checks
        rows.append(row)
    if len(pins) != 1:
        issues.append({"error": f"deployed pin differs across records: {sorted(map(str, pins))}"})
    deployed_pin = next(iter(pins)) if len(pins) == 1 else None
    if deployed_pin != COMMITTED_PIN:
        issues.append({"error": "deployed pin != committed-file pin (no-data node expects equality)",
                       "deployed": deployed_pin, "committed": COMMITTED_PIN})
    if len(sealed_keys) != 1:
        issues.append({"error": f"sealed keys are not unique across records: {sorted(sealed_keys)}"})
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
        "committed_pin_sha256": COMMITTED_PIN,
        "sealed_key": sealed_key,
        "not_forced_values": sorted(not_forced_values),
        "smoke": smoke,
        "issues": issues,
        "ok": not issues,
        "rows": rows,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
