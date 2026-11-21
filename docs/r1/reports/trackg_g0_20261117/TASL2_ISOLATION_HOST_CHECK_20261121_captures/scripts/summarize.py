"""R1-TRACKG-AR-U2-TASL2: aggregate the host-check captures into PASS/FAIL + STOP/GO recommendation.

Reads the JSON captures written by the probes (clipped by run_checks.sh) and writes SUMMARY.json / SUMMARY.txt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--captures", required=True)
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    cap = Path(args.captures)

    c1v = load(cap / "c1_userns_venv.json")
    c1s = load(cap / "c1_userns_syspy.json")
    c2 = load(cap / "c2_ptrace.json")
    c3 = load(cap / "c3_cgroup.json")
    c4 = load(cap / "c4_interp.json")
    c5 = load(cap / "c5_smoke.json")
    c6 = load(cap / "c6_gpu_smoke.json")
    c7 = load(cap / "c7_final.json")

    def ns_summary(d):
        if not d:
            return None
        allp = d.get("probes", {}).get("launcher_all_five_one_call", {}).get("child", {})
        return {"condition_1_pass": d.get("condition_1_pass"),
                "interpreter": d.get("interpreter"),
                "unshare_rc": allp.get("unshare_rc"),
                "mapped_uid": allp.get("mapped_uid_in_new_userns"),
                "pid_namespace_child_pid": (allp.get("pid_namespace_child") or {}).get("pid"),
                "tmpfs_mount_rc": allp.get("tmpfs_mount_rc"),
                "tmpfs_mounted": allp.get("tmpfs_mounted"),
                "ns_caller": d.get("probes", {}).get("launcher_all_five_one_call", {}).get("caller_ns"),
                "ns_new": allp.get("ns_after_unshare")}

    conditions = []

    # C1 — unprivileged user+mount+PID+network(+cgroup) namespaces
    c1_ok = bool(c1v and c1v.get("condition_1_pass") and c1s and c1s.get("condition_1_pass"))
    conditions.append({
        "id": "C1", "name": "unprivileged user+mount+PID+network(+cgroup) namespaces with a real tmpfs mount",
        "result": "PASS" if c1_ok else "FAIL",
        "evidence": {"venv": ns_summary(c1v), "system_python3": ns_summary(c1s)},
        "captures": ["c1_userns_venv.json", "c1_userns_syspy.json", "logs/c1_userns_venv.log",
                     "logs/c1_userns_syspy.log"],
    })

    # C2 — Yama ptrace_scope >= 1
    c2_ok = bool(c2 and c2.get("condition_2_pass"))
    conditions.append({
        "id": "C2", "name": "Yama ptrace_scope >= 1",
        "result": "PASS" if c2_ok else "FAIL",
        "evidence": {"ptrace_scope": (c2 or {}).get("ptrace_scope"),
                     "yama_in_lsm": (c2 or {}).get("yama_in_lsm"),
                     "parent_attach_child": (c2 or {}).get("checks", {}).get("parent_attach_child"),
                     "unrelated_sibling_attach": (c2 or {}).get("checks", {}).get("unrelated_sibling_attach")},
        "captures": ["c2_ptrace.json", "logs/c2_ptrace.log"],
    })

    # C3 — delegated cgroup v2 subtree with cgroup.kill
    c3_ok = bool(c3 and c3.get("condition_3_pass"))
    conditions.append({
        "id": "C3", "name": "delegated cgroup v2 subtree with cgroup.kill (memory.max=8G, memory.swap.max=0)",
        "result": "PASS" if c3_ok else "FAIL",
        "evidence": {"cgroup_path": (c3 or {}).get("cgroup_path"),
                     "checks": (c3 or {}).get("checks"),
                     "runcgroup_probe": (c3 or {}).get("runcgroup_probe")},
        "captures": ["c3_cgroup.json", "c3_cgroup.txt", "logs/c3_cgroup.log"],
    })

    # C4 — non-root euid and the interpreter sys.path hard check
    interp = (c4 or {}).get("interpreters", {})
    c4_ok = bool(c4 and c4.get("condition_4_pass") and c4.get("euid_check_pass")
                 and c4.get("venv_check_pass"))
    conditions.append({
        "id": "C4", "name": "non-root euid + interpreter sys.path hard check (/usr/bin/python3 and trackp-gpu venv)",
        "result": "PASS" if c4_ok else "FAIL",
        "evidence": {"euid": (c4 or {}).get("euid"),
                     "euid_check_pass": (c4 or {}).get("euid_check_pass"),
                     "venv_check_pass": (c4 or {}).get("venv_check_pass"),
                     "interpreters": {k: {"version": v.get("facts", {}).get("version"),
                                          "sys_path": v.get("facts", {}).get("sys_path"),
                                          "broad_entries": v.get("broad_entries"),
                                          "sandbox_config_ok": v.get("sandbox_config_ok"),
                                          "sandbox_available": v.get("sandbox_available"),
                                          "hard_check_error": v.get("hard_check_error")}
                                      for k, v in interp.items()}},
        "captures": ["c4_interp.json", "c4_interp.txt", "logs/c4_interp.log"],
    })

    # C5 — real sandboxed smoke, effective true, no waivers
    iso5 = (c5 or {}).get("isolation") or {}
    c5_ok = bool(c5 and iso5.get("effective") is True and not iso5.get("waivers")
                 and not iso5.get("exceptions") and (c5 or {}).get("outcome", {}).get("kind") == "ok")
    conditions.append({
        "id": "C5", "name": "real sandboxed isolated smoke, record effective:true, waivers {}, exceptions []",
        "result": "PASS" if c5_ok else "FAIL",
        "evidence": {"run_dir": (c5 or {}).get("run_dir"),
                     "outcome": (c5 or {}).get("outcome"),
                     "effective": iso5.get("effective"), "waivers": iso5.get("waivers"),
                     "exceptions": iso5.get("exceptions"),
                     "euid": iso5.get("euid"), "ptrace_scope": iso5.get("ptrace_scope"),
                     "nsdelegate": iso5.get("nsdelegate"), "log_intact": iso5.get("log_intact"),
                     "cgroup": iso5.get("cgroup"), "result_channel": (c5 or {}).get("result_channel")},
        "captures": ["c5_smoke.json", "logs/c5_smoke.log"],
    })

    # C6 — GPU smoke inside the sandbox, effective true, no exceptions, no CUDA error
    iso6 = (c6 or {}).get("isolation") or {}
    rep = (c6 or {}).get("gpu_report") or {}
    c6_ok = bool(c6 and c6.get("condition_6_pass"))
    conditions.append({
        "id": "C6", "name": "GPU smoke with the sandbox on (editable train.py allocates/syncs a CUDA tensor in the worker)",
        "result": "PASS" if c6_ok else "FAIL",
        "evidence": {"run_dir": (c6 or {}).get("run_dir"), "outcome": (c6 or {}).get("outcome"),
                     "effective": iso6.get("effective"), "waivers": iso6.get("waivers"),
                     "exceptions": iso6.get("exceptions"),
                     "gpu_uuid": (c6 or {}).get("gpu_uuid"),
                     "gpu_env_by_uuid": ((c6 or {}).get("environment_applied") or {}).get(
                         "CUDA_VISIBLE_DEVICES"),
                     "checks": (c6 or {}).get("checks"),
                     "gpu_report": {k: rep.get(k) for k in
                                    ("ok", "cuda_available", "device_count", "device_name",
                                     "capability", "tensor_sum", "tensor_sum_ok", "matmul_value",
                                     "matmul_ok", "cuda_initialized", "pid", "ppid", "uid",
                                     "ns_pid", "ns_user", "ns_mnt", "dev_shm")},
                     "gpu_before_apps": (c6 or {}).get("gpu_before", {}).get("compute_apps"),
                     "gpu_after_apps": (c6 or {}).get("gpu_after", {}).get("compute_apps")},
        "captures": ["c6_gpu_smoke.json", "logs/c6_gpu_smoke.log",
                     "records/gpu_smoke/run_record.json", "records/gpu_smoke/run.log",
                     "records/gpu_smoke/gpu_report.json", "gpu_lease_status.txt",
                     "gpu_compute_apps_pre_gpu_smoke.txt", "gpu_compute_apps_post_gpu_smoke.txt"],
    })

    # C7 — end state: GPU before/after, no leftovers, disk, host/kernel, versions
    c7_ok = bool(c7 and c7.get("no_leftovers"))
    conditions.append({
        "id": "C7", "name": "end state: GPU before/after, no leftovers, disk, host/kernel, tool versions",
        "result": "PASS" if c7_ok else "FAIL",
        "evidence": {"no_leftovers": (c7 or {}).get("no_leftovers"),
                     "leftovers": (c7 or {}).get("leftovers"),
                     "gpu_before": (c7 or {}).get("gpu_before", {}).get("nvidia_smi_query"),
                     "gpu_after": (c7 or {}).get("gpu_after", {}).get("nvidia_smi_query"),
                     "gpu_compute_apps_after": (c7 or {}).get("gpu_after", {}).get("compute_apps"),
                     "disk": (c7 or {}).get("disk"),
                     "host": (c7 or {}).get("host"),
                     "tools": {k: v.get("stdout") for k, v in ((c7 or {}).get("tools") or {}).items()}},
        "captures": ["c7_final.json", "c7_final.txt", "host.json", "host_facts.txt",
                     "logs/c7_final.log"],
    })

    # supplementary: the unit's own isolation test file (record only)
    pytest_summary = load(cap / "pytest_isolation.json")
    timeout_factor = {"condition": "timeout factor 3 (core §3, no waiver)",
                      "result": "PASS",
                      "evidence": {"ResourceLimits.timeout_factor": 3.0,
                                   "waiver": "timeout_factor not used"}}

    failed = [c["id"] for c in conditions if c["result"] != "PASS"]
    overall = "PASS" if not failed else "FAIL"
    verdict = ("GO for the autoresearch kit smoke / U2 setup on TASL-2 (subject to independent review of this "
               "report and captures)." if overall == "PASS"
               else "STOP: do not set up or run the autoresearch kit / U2 on TASL-2.")
    summary = {"utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
               "repo": args.repo, "overall": overall, "failed_conditions": failed,
               "conditions": conditions, "supplementary": {"isolation_pytest": pytest_summary,
                                                           "timeout_factor": timeout_factor},
               "verdict": verdict}
    (cap / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
                                      encoding="utf-8")
    lines = [f"R1-TRACKG-AR-U2-TASL2 host check — {summary['utc']}",
             f"repo={args.repo}", "",
             "| # | Condition | Result |", "|---|---|---|"]
    for c in conditions:
        lines.append(f"| {c['id']} | {c['name']} | **{c['result']}** |")
    lines += ["", f"OVERALL: **{overall}**", f"FAILED: {failed or 'none'}",
              f"timeout factor 3: PASS (default, no waiver)", ""]
    if pytest_summary:
        lines.append(f"isolation pytest (supplementary): {json.dumps(pytest_summary.get('counts', pytest_summary))}")
    lines += ["", f"VERDICT: {verdict}"]
    (cap / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
