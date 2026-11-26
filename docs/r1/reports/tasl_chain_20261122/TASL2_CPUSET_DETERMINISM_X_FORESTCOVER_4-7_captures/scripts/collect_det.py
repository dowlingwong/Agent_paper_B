#!/usr/bin/env python3
"""Collect and check the two fixed-seed determinism runs of one node (prep report section 9 step 7).

Reads <evidence>/results/r<n>.json (the adapted driver's result document) and the corresponding
<evidence>/runs/r<n>/s000_baseline/run_record.json, then applies the spec's pass criterion and writes a
sanitized summary: hashes and wall times only, no metric value is copied into the summary.

Pass criterion (all of, both runs): exit 0 with outcome ok; isolation effective true, waivers {},
exceptions []; frozen files changed []; result_channel_sha256 equal to the census baseline's; elapsed at most
the bound (1.5 x census B1); affinity equal to the set; scope memory.max 8 GiB and memory.swap.max 0; the
checkout at its pin, clean apart from the data link.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cpus_of(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--expected-channel", required=True)
    ap.add_argument("--max-elapsed", required=True, type=float)
    ap.add_argument("--pin", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--node-rel", required=True)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    ev = Path(args.evidence)
    want_cpus = cpus_of(args.set)
    rows = []
    for n in range(1, args.repeats + 1):
        res_path = ev / "results" / f"r{n}.json"
        res = load(res_path)
        run = (res or {}).get("run") or {}
        binding = (res or {}).get("binding") or {}
        run_dir = Path(run.get("run_dir") or (ev / "runs" / f"r{n}" / "s000_baseline"))
        record_path = run_dir / "run_record.json"
        record = load(record_path) or {}
        iso = record.get("isolation") or {}
        pipeline = record.get("process") or {}
        row = {
            "repeat": n,
            "results_path": str(res_path),
            "run_record_path": str(record_path),
            "present": res is not None,
            "driver_verdict": (res or {}).get("verdict"),
            "driver_error": (res or {}).get("driver_error"),
            "wall_seconds_driver": (res or {}).get("wall_seconds"),
            "exit_code": run.get("exit_code"),
            "signal": run.get("signal"),
            "outcome_kind": (run.get("outcome") or {}).get("kind"),
            "timed_out": run.get("timed_out"),
            "elapsed_seconds_info_only": run.get("elapsed_seconds_info_only"),
            "result_channel_sha256": iso.get("result_channel_sha256"),
            "channel_sha256_observed": run.get("channel_sha256"),
            "channel_bytes": iso.get("result_channel_bytes") or run.get("channel_bytes"),
            "log_sha256": iso.get("log_sha256") or run.get("log_sha256"),
            "baseline_check_ok": (run.get("baseline_check") or {}).get("ok"),
            "effective": iso.get("effective"),
            "waivers": iso.get("waivers"),
            "exceptions": iso.get("exceptions"),
            "frozen_files_checked": iso.get("frozen_files_checked"),
            "frozen_files_changed": iso.get("frozen_files_changed"),
            "memory_max": record.get("limits", {}).get("memory_max") or binding.get("memory_max"),
            "memory_swap_max": record.get("limits", {}).get("memory_swap_max") or binding.get("memory_swap_max"),
            "affinity": binding.get("affinity"),
            "cpu_affinity_matches_group": binding.get("cpu_affinity_matches_group"),
            "loadavg": binding.get("loadavg"),
            "harness_head": (binding.get("git") or {}).get("head"),
            "harness_branch": (binding.get("git") or {}).get("branch"),
            "harness_status_porcelain": (binding.get("git") or {}).get("status_porcelain"),
            "ar_test_cgroup_parent": binding.get("ar_test_cgroup_parent"),
            "scope_cgroup": binding.get("cgroup"),
            "pins": {k: (binding.get("pins") or {}).get(k) for k in
                     ("node_spec_sha256", "spec_raw_sha256", "committed_pin_sha256",
                      "deployed_pin_sha256", "edits_manifest_sha256", "data_manifest_sha256")},
            "env_freeze_sha256": (binding.get("env") or {}).get("freeze_sha256"),
            "python_executable": binding.get("python_executable"),
            "python": binding.get("python"),
        }
        checks = {
            "present": row["present"],
            "driver_verdict_pass": row["driver_verdict"] == "PASS",
            "exit_code_0": row["exit_code"] == 0,
            "outcome_ok": row["outcome_kind"] == "ok",
            "baseline_check_ok": row["baseline_check_ok"] is True,
            "effective_true": row["effective"] is True,
            "waivers_empty": row["waivers"] == {},
            "exceptions_empty": row["exceptions"] == [],
            "frozen_files_changed_empty": row["frozen_files_changed"] == [],
            "result_channel_sha_matches_census": row["result_channel_sha256"] == args.expected_channel,
            "channel_sha_observed_matches_record":
                row["channel_sha256_observed"] == row["result_channel_sha256"],
            "elapsed_within_bound": (row["elapsed_seconds_info_only"] is not None
                                     and row["elapsed_seconds_info_only"] <= args.max_elapsed),
            "affinity_equals_set": row["affinity"] == want_cpus,
            "memory_max_8g": row["memory_max"] in ("8589934592", 8589934592),
            "memory_swap_max_0": row["memory_swap_max"] == "0",
            "harness_head_pin": row["harness_head"] == args.pin,
            "harness_branch": row["harness_branch"] == args.branch,
            "harness_clean_apart_from_data_link":
                (row["harness_status_porcelain"] in ([], [f"?? {args.node_rel}/data"])),
        }
        row["checks"] = checks
        row["pass"] = all(checks.values())
        rows.append(row)
    verdict = "PASS" if rows and all(r["pass"] for r in rows) else "FAIL"
    result = {
        "schema": "g1bx_cpuset_determinism_summary/v1",
        "node": args.node,
        "cpus": args.set,
        "pin": args.pin,
        "branch": args.branch,
        "expected_result_channel_sha256": args.expected_channel,
        "max_elapsed_seconds": args.max_elapsed,
        "runs": rows,
        "verdict": verdict,
    }
    out = Path(args.out) if args.out else ev / "determinism_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = [f"node={args.node} cpus={args.set} pin={args.pin}",
             f"verdict={verdict} expected_channel={args.expected_channel} "
             f"max_elapsed={args.max_elapsed}"]
    for r in rows:
        lines.append(
            f"run {r['repeat']}: pass={r['pass']} rc={r['exit_code']} outcome={r['outcome_kind']} "
            f"elapsed={r['elapsed_seconds_info_only']} channel={r['result_channel_sha256']} "
            f"effective={r['effective']} waivers={r['waivers']} exceptions={r['exceptions']} "
            f"frozen_changed={r['frozen_files_changed']} affinity={r['affinity']} "
            f"memory_max={r['memory_max']} swap={r['memory_swap_max']} "
            f"failed_checks={[k for k, v in r['checks'].items() if not v]}")
    (ev / "determinism_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("VERDICT " + verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
