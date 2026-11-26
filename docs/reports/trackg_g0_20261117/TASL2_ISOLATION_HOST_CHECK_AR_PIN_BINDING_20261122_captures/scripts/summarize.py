"""TASL-2 AR-pin host check: build SUMMARY.json / SUMMARY.txt from the capture JSON documents.

Reads only the captures directory and the run root; writes SUMMARY.{json,txt} into the captures directory and
prints the verdict.  The STOP/PASS gates themselves live in run_all.sh; this script records their outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PIN = "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"
SEVEN_PIN = "c025f89aeafc2199bf3487b4bcaa16678273c702"
CONDITION_FILES = {
    "c1_userns_ar_cond7a": "condition_1_pass",
    "c1_userns_syspy": "condition_1_pass",
    "c2_ptrace": "condition_2_pass",
    "c3_cgroup": "condition_3_pass",
    "c4_interp": "condition_4_pass",
    "c5_smoke": "condition_5_pass",
    "c6_gpu_smoke": "condition_6_pass",
    "c7_final": "condition_7_pass",
    "node_pins": "condition_2_pass",
    "env_check": "condition_3_pass",
    "step4_data_check": "condition_4_data_pass",
    "ast_cuda_ipc_scan": "condition_scan_pass",
}


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--captures", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out-dir", default="")
    args = ap.parse_args()
    cap, base = Path(args.captures), Path(args.base)
    out_dir = Path(args.out_dir) if args.out_dir else cap

    def get(name):
        return load(cap / f"{name}.json")

    stop_items = []
    stops_file = cap / "stop_items.txt"
    if stops_file.is_file():
        stop_items = [line for line in stops_file.read_text().splitlines() if line.strip()]

    conditions = {}
    for name, key in CONDITION_FILES.items():
        doc = get(name)
        conditions[name] = None if doc is None else doc.get(key)
    # C1 needs both interpreter probes.
    c1 = bool(conditions.get("c1_userns_ar_cond7a")) and bool(conditions.get("c1_userns_syspy"))
    c2 = bool(conditions.get("c2_ptrace"))
    c3 = bool(conditions.get("c3_cgroup"))
    c4 = bool(conditions.get("c4_interp"))
    c5 = bool(conditions.get("c5_smoke"))
    c6 = bool(conditions.get("c6_gpu_smoke"))
    c7 = bool(conditions.get("c7_final"))
    c1_7 = {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6, "C7": c7}
    checks = {
        "checkout": bool((get("host_facts") or {}).get("repo_pin_matches", {}).get("harness_ar", {})
                         .get("match")),
        "node_pins": bool((get("node_pins") or {}).get("condition_2_pass")),
        "environment": bool((get("env_check") or {}).get("condition_3_pass")),
        "data": bool((get("step4_data_check") or {}).get("condition_4_data_pass")),
        "c1_c7": all(c1_7.values()),
        "ast_scan": bool((get("ast_cuda_ipc_scan") or {}).get("condition_scan_pass")),
    }
    verdict = "PASS" if (all(checks.values()) and not stop_items
                         and c1_7 == {k: True for k in c1_7}) else "FAIL / STOP"

    host = get("host_facts") or {}
    node_pins = get("node_pins") or {}
    env = get("env_check") or {}
    data = get("step4_data_check") or {}
    c6doc = get("c6_gpu_smoke") or {}
    c7doc = get("c7_final") or {}
    venv_before = get("venv_evidence_before") or {}
    venv_after = get("venv_evidence_after") or {}
    pytest_doc = get("pytest_isolation") or {}
    ast_doc = get("ast_cuda_ipc_scan") or {}

    summary = {
        "schema": "tasl2_ar_pin_hostcheck_summary/v2",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": "TASL-2",
        "pin": PIN,
        "seven_node_pin": SEVEN_PIN,
        "engine": "deepseek-harness agent ar-pin-hostcheck-r2",
        "scope": "procedure sections 0-5 (data, C1-C7, supplementary pytest and AST CUDA-IPC scan); "
                 "binding record written only if C1-C7 pass",
        "verdict": verdict,
        "checks": checks,
        "c1_c7": c1_7,
        "stop_items": stop_items,
        "checkout": {
            "head": ((get("host_facts") or {}).get("repos", {}).get("harness_ar", {})
                     .get("head") or {}).get("stdout"),
            "pin_match": checks["checkout"],
            "seven_node_head": ((get("host_facts") or {}).get("repos", {}).get("seven_node", {})
                                .get("head") or {}).get("stdout"),
            "seven_node_match": bool((get("host_facts") or {}).get("repo_pin_matches", {})
                                     .get("seven_node", {}).get("match")),
        },
        "node_pins": {"condition": (get("node_pins") or {}).get("condition_2_pass"),
                      "got": (get("node_pins") or {}).get("got"),
                      "checks": (get("node_pins") or {}).get("checks")},
        "environment": {
            "condition": (get("env_check") or {}).get("condition_3_pass"),
            "uv": (env.get("uv") or {}).get("version"),
            "python": (env.get("python") or {}).get("version"),
            "torch": (env.get("torch") or {}).get("version"),
            "torch_cuda": (env.get("torch") or {}).get("cuda"),
            "freeze_sha256": (env.get("freeze") or {}).get("sha256_raw"),
            "freeze_lines": (env.get("freeze") or {}).get("lines"),
            "readlink_f": env.get("readlink_f_venv"),
            "checks": env.get("checks"),
        },
        "interpreter": {
            "before": {"resolved": (venv_before.get("resolved_interpreter")),
                       "sha256": venv_before.get("interpreter_sha256"),
                       "bytes": venv_before.get("interpreter_bytes"),
                       "python": venv_before.get("python_version"),
                       "freeze_sha256": venv_before.get("freeze_sha256"),
                       "checks": venv_before.get("checks")},
            "after": {"resolved": (venv_after.get("resolved_interpreter")),
                      "sha256": venv_after.get("interpreter_sha256"),
                      "bytes": venv_after.get("interpreter_bytes"),
                      "python": venv_after.get("python_version"),
                      "freeze_sha256": venv_after.get("freeze_sha256"),
                      "checks": venv_after.get("checks")},
        },
        "data": {"condition": (get("step4_data_check") or {}).get("condition_4_data_pass"),
                 "manifest_sha256": (data.get("manifest") or {}).get("sha256"),
                 "file_count": (data.get("manifest") or {}).get("file_count"),
                 "revision": (data.get("manifest") or {}).get("revision"),
                 "link_readlink": (data.get("link") or {}).get("readlink")},
        "gpu_summary": {"gpu_uuid": c6doc.get("gpu_uuid"),
                        "expected_gpu_uuid": c6doc.get("expected_gpu_uuid"),
                        "isolation_effective": (c6doc.get("isolation") or {}).get("effective"),
                        "waivers": (c6doc.get("isolation") or {}).get("waivers"),
                        "exceptions": (c6doc.get("isolation") or {}).get("exceptions"),
                        "checks": c6doc.get("checks")},
        "end_state": {"condition": (get("c7_final") or {}).get("condition_7_pass"),
                      "no_leftovers": c7doc.get("no_leftovers"),
                      "repo_checks": c7doc.get("repo_checks"),
                      "gpu_after_compute_apps": ((c7doc.get("gpu_after") or {})
                                                 .get("compute_apps") or {}).get("stdout")},
        "supplementary_pytest": {"counts": pytest_doc.get("counts"), "rc": pytest_doc.get("rc")},
        "ast_cuda_ipc_scan": {"condition": (get("ast_cuda_ipc_scan") or {}).get("condition_scan_pass"),
                              "primary_call_hit_count": ast_doc.get("primary_call_hit_count"),
                              "primary": {n: {"sha256": i.get("sha256"),
                                              "call_hits": i.get("call_hits")}
                                          for n, i in (ast_doc.get("primary_files") or {}).items()}},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    lines = [
        "TASL-2 AR-pin host check at harness pin " + PIN,
        f"utc={summary['utc']} host=TASL-2",
        f"verdict={verdict}",
        f"checkout_pin_match={checks['checkout']} node_pins={checks['node_pins']} "
        f"environment={checks['environment']} data={checks['data']} c1_c7={checks['c1_c7']} "
        f"ast_scan={checks['ast_scan']}",
        "conditions: " + " ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in c1_7.items()),
        "STOP items:" if stop_items else "STOP items: none",
    ]
    lines += ["  " + s for s in stop_items]
    (out_dir / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
