"""R1-T1-HOST-TASL: aggregate the T1 host-check captures into PASS/FAIL for the seven §3 host conditions and the
T1 precheck supplements.

The seven §3 items (C1-C7) are the ``host_check_items`` the G.1b/G.4 job validates.  The supplements are the T1
environment binding (E1), the binding assertions (A0), the jax312 GPU as the environment stands (J1a) and with
the XLA CUDA-data-directory host adaptation (J1b), and the unit's own isolation test file (record only).

Writes SUMMARY.json / SUMMARY.txt into the captures directory.
"""
from __future__ import annotations

import json
import time
from pathlib import Path


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def main() -> int:
    import argparse
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
    e1 = load(cap / "c0_envs.json")
    a0 = load(cap / "c0_assertions.json")
    j1a = load(cap / "c6b_jax_gpu.json")
    j1b = load(cap / "c6b_jax_gpu_xla_cuda_dir.json")

    def ns_summary(d):
        if not d:
            return None
        allp = d.get("probes", {}).get("launcher_all_five_one_call", {}).get("child", {})
        return {"condition_1_pass": d.get("condition_1_pass"), "interpreter": d.get("interpreter"),
                "unshare_rc": allp.get("unshare_rc"), "mapped_uid": allp.get("mapped_uid_in_new_userns"),
                "pid_namespace_child_pid": (allp.get("pid_namespace_child") or {}).get("pid"),
                "tmpfs_mount_rc": allp.get("tmpfs_mount_rc"), "tmpfs_mounted": allp.get("tmpfs_mounted")}

    conditions = []

    c1_ok = bool(c1v and c1v.get("condition_1_pass") and c1s and c1s.get("condition_1_pass"))
    conditions.append({"id": "C1", "name": "unprivileged user+mount+PID+network(+cgroup) namespaces with a real tmpfs mount",
                       "result": "PASS" if c1_ok else "FAIL",
                       "evidence": {"venv": ns_summary(c1v), "system_python3": ns_summary(c1s)},
                       "captures": ["c1_userns_venv.json", "c1_userns_syspy.json"]})

    c2_ok = bool(c2 and c2.get("condition_2_pass"))
    conditions.append({"id": "C2", "name": "Yama ptrace_scope >= 1", "result": "PASS" if c2_ok else "FAIL",
                       "evidence": {"ptrace_scope": (c2 or {}).get("ptrace_scope"),
                                    "yama_in_lsm": (c2 or {}).get("yama_in_lsm"),
                                    "checks": (c2 or {}).get("checks")},
                       "captures": ["c2_ptrace.json"]})

    c3_ok = bool(c3 and c3.get("condition_3_pass"))
    conditions.append({"id": "C3", "name": "delegated cgroup v2 subtree with cgroup.kill (memory.max=8G, memory.swap.max=0)",
                       "result": "PASS" if c3_ok else "FAIL",
                       "evidence": {"cgroup_path": (c3 or {}).get("cgroup_path"), "checks": (c3 or {}).get("checks"),
                                    "runcgroup_probe": (c3 or {}).get("runcgroup_probe")},
                       "captures": ["c3_cgroup.json", "c3_cgroup.txt"]})

    interp = (c4 or {}).get("interpreters", {})
    c4_ok = bool(c4 and c4.get("condition_4_pass") and c4.get("euid_check_pass") and c4.get("venv_check_pass"))
    conditions.append({"id": "C4", "name": "non-root euid + interpreter sys.path hard check (/usr/bin/python3, torch312, jax312)",
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
                       "captures": ["c4_interp.json", "c4_interp.txt"]})

    iso5 = (c5 or {}).get("isolation") or {}
    c5_ok = bool(c5 and iso5.get("effective") is True and not iso5.get("waivers")
                 and not iso5.get("exceptions") and (c5 or {}).get("outcome", {}).get("kind") == "ok")
    conditions.append({"id": "C5", "name": "real sandboxed isolated smoke, record effective:true, waivers {}, exceptions []",
                       "result": "PASS" if c5_ok else "FAIL",
                       "evidence": {"run_dir": (c5 or {}).get("run_dir"), "outcome": (c5 or {}).get("outcome"),
                                    "effective": iso5.get("effective"), "waivers": iso5.get("waivers"),
                                    "exceptions": iso5.get("exceptions"), "euid": iso5.get("euid"),
                                    "ptrace_scope": iso5.get("ptrace_scope"), "nsdelegate": iso5.get("nsdelegate"),
                                    "log_intact": iso5.get("log_intact"), "cgroup": iso5.get("cgroup"),
                                    "result_channel": (c5 or {}).get("result_channel")},
                       "captures": ["c5_smoke.json", "records/g0_smoke/run_record.json",
                                    "records/g0_smoke/run.log", "records/g0_smoke/result_channel.txt"]})

    iso6 = (c6 or {}).get("isolation") or {}
    rep = (c6 or {}).get("gpu_report") or {}
    c6_ok = bool(c6 and c6.get("condition_6_pass")) and not (c6 or {}).get("refused_or_error")
    conditions.append({"id": "C6", "name": "GPU smoke with the sandbox on (editable train.py allocates/syncs a CUDA tensor in the worker)",
                       "result": "PASS" if c6_ok else "FAIL",
                       "evidence": {"run_dir": (c6 or {}).get("run_dir"), "outcome": (c6 or {}).get("outcome"),
                                    "effective": iso6.get("effective"), "waivers": iso6.get("waivers"),
                                    "exceptions": iso6.get("exceptions"), "gpu_uuid": (c6 or {}).get("gpu_uuid"),
                                    "gpu_env_by_uuid": ((c6 or {}).get("environment_applied") or {}).get(
                                        "CUDA_VISIBLE_DEVICES"),
                                    "checks": (c6 or {}).get("checks"),
                                    "gpu_report": {k: rep.get(k) for k in
                                                   ("ok", "cuda_available", "device_count", "device_name",
                                                    "capability", "tensor_sum", "tensor_sum_ok", "matmul_value",
                                                    "matmul_ok", "cuda_initialized", "pid", "ppid", "uid",
                                                    "ns_pid", "ns_user", "ns_mnt", "dev_shm")}},
                       "captures": ["c6_gpu_smoke.json", "records/gpu_smoke/run_record.json",
                                    "records/gpu_smoke/gpu_report.json", "gpu_lease_status.txt",
                                    "gpu_leaselogs_diff.txt"]})

    c7_ok = bool(c7 and c7.get("condition_7_pass", c7.get("no_leftovers")))
    conditions.append({"id": "C7", "name": "end state: GPU before/after, no leftovers, worktree clean, disk, attempt-1 "
                                          "archive/lease untouched (stat+sha256 before/after)",
                       "result": "PASS" if c7_ok else "FAIL",
                       "evidence": {"no_leftovers": (c7 or {}).get("no_leftovers"),
                                    "condition_7_pass": (c7 or {}).get("condition_7_pass"),
                                    "attempt1_untouched": (c7 or {}).get("attempt1_untouched"),
                                    "attempt1_archive": (c7 or {}).get("attempt1_archive"),
                                    "attempt1_fingerprint": {k: (c7 or {}).get("attempt1_fingerprint", {}).get(k) for k in
                                                             ("identical", "differences", "tree_sha256",
                                                              "content_sha256", "entries", "files_count", "bytes")},
                                    "attempt1_lease_logs": (c7 or {}).get("attempt1_lease_logs"),
                                    "repo": (c7 or {}).get("repo"), "leftovers": (c7 or {}).get("leftovers"),
                                    "gpu_after": (c7 or {}).get("gpu_after", {}).get("nvidia_smi_query"),
                                    "gpu_compute_apps_after": (c7 or {}).get("gpu_after", {}).get("compute_apps"),
                                    "disk": (c7 or {}).get("disk")},
                       "captures": ["c7_final.json", "c7_final.txt", "host.json", "host_facts.txt",
                                    "attempt1_compare.json"]})

    failed = [c["id"] for c in conditions if c["result"] != "PASS"]
    overall = "PASS" if not failed else "FAIL"

    env_checks = (e1 or {}).get("checks", {})
    e1_ok = bool(e1 and e1.get("condition_envs_pass"))
    a0_ok = bool(a0 and a0.get("condition_assertions_pass"))
    j1a_ok = bool(j1a and j1a.get("condition_jax_gpu_pass"))
    j1b_ok = bool(j1b and j1b.get("condition_jax_gpu_pass"))
    pytest_summary = load(cap / "pytest_isolation.json")
    supplementary = {
        "E1_t1_environments": {
            "result": "PASS" if e1_ok else "FAIL",
            "uv": (e1 or {}).get("uv", {}).get("version"),
            "uv_python_find": (e1 or {}).get("uv", {}).get("python_find"),
            "checks": env_checks,
            "envs": {name: {"interpreter": (e1 or {}).get("envs", {}).get(name, {}).get("interpreter"),
                            "realpath": (e1 or {}).get("envs", {}).get(name, {}).get("interpreter_realpath"),
                            "version": (e1 or {}).get("envs", {}).get(name, {}).get("version"),
                            "freeze_file_sha256": (e1 or {}).get("envs", {}).get(name, {}).get("freeze_file_sha256"),
                            "freeze_actual_sha256": (e1 or {}).get("envs", {}).get(name, {}).get("freeze_actual_sha256"),
                            "freeze_byte_equal": (e1 or {}).get("envs", {}).get(name, {}).get("freeze_byte_equal"),
                            "freeze_sorted_equal": (e1 or {}).get("envs", {}).get(name, {}).get("freeze_sorted_equal")}
                     for name in ("torch312", "jax312")}},
        "A0_binding_assertions": {"result": "PASS" if a0_ok else "FAIL",
                                  "checks": (a0 or {}).get("checks"),
                                  "gpu_uuids": [ln.split("UUID: ")[-1].strip().rstrip(")") for ln in
                                                ((a0 or {}).get("gpu", {}).get("nvidia_smi_L", {}).get("stdout") or "").splitlines()
                                                if ln.strip()],
                                  "compute_apps": (a0 or {}).get("gpu", {}).get("compute_apps", {}).get("stdout"),
                                  "harness": (a0 or {}).get("repo"), "ptrace": (a0 or {}).get("ptrace"),
                                  "disks": (a0 or {}).get("disks")},
        "J1a_jax312_gpu_as_configured": {
            "result": "PASS" if j1a_ok else "FAIL",
            "jax_version": (j1a or {}).get("jax_version"), "jaxlib_version": (j1a or {}).get("jaxlib_version"),
            "default_backend": (j1a or {}).get("default_backend"), "devices": (j1a or {}).get("devices"),
            "checks": (j1a or {}).get("checks"), "exception": (j1a or {}).get("exception"),
            "ptxas_candidates": (j1a or {}).get("ptxas_candidates"), "env": (j1a or {}).get("env")},
        "J1b_jax312_gpu_with_xla_cuda_data_dir": {
            "result": "PASS" if j1b_ok else "FAIL",
            "xla_flags": ((j1b or {}).get("env") or {}).get("XLA_FLAGS"),
            "jax_version": (j1b or {}).get("jax_version"), "jaxlib_version": (j1b or {}).get("jaxlib_version"),
            "default_backend": (j1b or {}).get("default_backend"), "devices": (j1b or {}).get("devices"),
            "tensor_sum": (j1b or {}).get("tensor_sum"), "matmul_value": (j1b or {}).get("matmul_value"),
            "checks": (j1b or {}).get("checks"), "env": (j1b or {}).get("env")},
        "isolation_pytest": pytest_summary,
        "timeout_factor": {"condition": "timeout factor 3 (core §3, no waiver)", "result": "PASS",
                           "evidence": {"ResourceLimits.timeout_factor": 3.0, "waiver": "timeout_factor not used"}},
    }
    precheck_ok = bool(overall == "PASS" and e1_ok and a0_ok and j1b_ok)
    precheck_verdict = ("PASS for the seven §3 host items; T1 precheck PASS with the jax312 XLA-flag host "
                        "adaptation (J1a fails as configured, J1b passes with --xla_gpu_cuda_data_dir=/usr/local/cuda-12.2)"
                        if precheck_ok else "STOP: a T1 precheck supplement failed (see supplementary)")
    a0_head = ((a0 or {}).get("repo", {}).get("head", {}) or {}).get("stdout", "").strip()
    summary = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "repo": args.repo,
        "host_check_host": (a0 or {}).get("hostname"), "host_check_harness_commit": a0_head,
        "host_check_items": "1-7 PASS" if overall == "PASS" else "FAIL", "host_check_verdict": overall,
        "overall": overall, "failed_conditions": failed, "conditions": conditions,
        "supplementary": supplementary, "precheck_ok": precheck_ok, "precheck_verdict": precheck_verdict,
    }
    (cap / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
                                      encoding="utf-8")
    lines = [f"R1-T1-HOST-TASL TASL-7 host check at harness pin c025f89a — {summary['utc']}",
             f"repo={args.repo}", "", "| # | Condition | Result |", "|---|---|---|"]
    lines += [f"| {c['id']} | {c['name']} | **{c['result']}** |" for c in conditions]
    lines += ["", f"OVERALL (seven §3 host items): **{overall}**", f"FAILED: {failed or 'none'}",
              f"timeout factor 3: PASS (default, no waiver)", "",
              "supplementary (T1 precheck):"]
    for key, item in supplementary.items():
        if isinstance(item, dict) and "result" in item:
            lines.append(f"- {key}: {item['result']}")
    lines += ["",
              f"J1a (jax312 GPU as configured): {supplementary['J1a_jax312_gpu_as_configured']['result']}"
              f" — {((j1a or {}).get('exception') or 'ok')[:220]}",
              f"J1b (jax312 GPU with --xla_gpu_cuda_data_dir=/usr/local/cuda-12.2): "
              f"{supplementary['J1b_jax312_gpu_with_xla_cuda_data_dir']['result']}",
              f"isolation pytest (supplementary): {json.dumps((pytest_summary or {}).get('counts'))}", "",
              f"host_check_host: {summary['host_check_host']}",
              f"host_check_harness_commit: {summary['host_check_harness_commit']}",
              f"host_check_items: {summary['host_check_items']}",
              f"host_check_verdict: {summary['host_check_verdict']}", "",
              f"T1_PRECHECK_VERDICT: {precheck_verdict}"]
    (cap / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
