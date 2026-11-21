"""R1-T1-HOST-TASL TASL-2 G.1b pre-launch host check: aggregate the captures into PASS/FAIL + GO/STOP.

Reads the JSON captures written by the probes (clipped by ``run_checks.sh``) and writes SUMMARY.json /
SUMMARY.txt.  The first table is HARNESS_ISOLATION_20261117 §3 items 1-7 at the harness pin c025f89a (the
``host_check_items: 1-7 PASS`` binding needs exactly these); the second is the G.1b plan §6 host-test items
that are in scope on TASL-2.  Items that need the TASL-7 proposer/host (§6 6-8) are out of this host's scope;
the 4090/Ada baseline ratio (§6 3) is measured by the job's first part, not pre-launch, and is reported as
deferred with the synthetic load proxy recorded.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

PIN = "c025f89aeafc2199bf3487b4bcaa16678273c702"
GPU_UUID = "GPU-4d623e76-7587-ee15-a633-46f60d220d94"


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--captures", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--t1", default="/home/dowling/r1_tracks/t1_tasl")
    args = ap.parse_args()
    cap, repo, t1 = Path(args.captures), Path(args.repo), Path(args.t1)

    c1v, c1s = load(cap / "c1_userns_venv.json"), load(cap / "c1_userns_syspy.json")
    c2 = load(cap / "c2_ptrace.json")
    c3 = load(cap / "c3_cgroup.json")
    c4 = load(cap / "c4_interp.json")
    c5 = load(cap / "c5_smoke.json")
    c6 = load(cap / "c6_gpu_smoke.json")
    c6b = load(cap / "c6b_jax_gpu_smoke.json")
    c6c = load(cap / "c6c_cpu_gpu_coexistence.json")
    c7 = load(cap / "c7_final.json")
    env = load(cap / "env_check.json")
    host = load(cap / "host.json")
    pytest_rec = load(cap / "pytest_isolation.json")
    pin_txt = text(cap / "harness_pin.txt")

    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                                  timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

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
                "tmpfs_mounted": allp.get("tmpfs_mounted")}

    conditions = []

    c1_ok = bool(c1v and c1v.get("condition_1_pass") and c1s and c1s.get("condition_1_pass"))
    conditions.append({
        "id": "C1",
        "name": "§3.1 unprivileged user+mount+PID+network(+cgroup) namespaces with a real tmpfs mount",
        "result": "PASS" if c1_ok else "FAIL",
        "evidence": {"torch312_python": ns_summary(c1v), "system_python3": ns_summary(c1s),
                     "interpreters": [ (c1v or {}).get("interpreter"), (c1s or {}).get("interpreter") ]},
        "captures": ["c1_userns_venv.json", "c1_userns_syspy.json", "logs/c1_userns_venv.log",
                     "logs/c1_userns_syspy.log"]})

    c2_ok = bool(c2 and c2.get("condition_2_pass"))
    conditions.append({
        "id": "C2", "name": "§3.2 Yama ptrace_scope >= 1",
        "result": "PASS" if c2_ok else "FAIL",
        "evidence": {"ptrace_scope_raw": (c2 or {}).get("ptrace_scope_raw"),
                     "lsm": (c2 or {}).get("lsm"),
                     "parent_attach_child": (c2 or {}).get("parent_attach_child"),
                     "unrelated_sibling_attach": (c2 or {}).get("unrelated_sibling_attach")},
        "captures": ["c2_ptrace.json", "logs/c2_ptrace.log"]})

    scope_dir = ((c3 or {}).get("dir") or {})
    checks3 = (c3 or {}).get("checks") or {}
    c3_ok = bool(c3 and c3.get("condition_3_pass"))
    conditions.append({
        "id": "C3", "name": "§3.3 delegated cgroup v2 subtree the uid can write, with cgroup.kill "
                            "(census scope MemoryMax=8G, MemorySwapMax=0)",
        "result": "PASS" if c3_ok else "FAIL",
        "evidence": {"cgroup_path": (c3 or {}).get("cgroup_path"),
                     "memory.max": (scope_dir.get("memory.max") or {}).get("value"),
                     "memory.swap.max": (scope_dir.get("memory.swap.max") or {}).get("value"),
                     "cgroup.kill_exists": (scope_dir.get("cgroup.kill") or {}).get("exists"),
                     "nsdelegate": (c3 or {}).get("nsdelegate"),
                     "checks": checks3},
        "captures": ["c3_cgroup.json", "c3_cgroup.txt", "logs/c3_cgroup.log"]})

    c4_ok = bool(c4 and c4.get("condition_4_pass"))
    interps = (c4 or {}).get("interpreters") or {}
    conditions.append({
        "id": "C4", "name": "§3.4 non-root euid and the run interpreter's sys.path hard check "
                            "(torch312 + jax312 + system python)",
        "result": "PASS" if c4_ok else "FAIL",
        "evidence": {"euid": (c4 or {}).get("euid"), "is_root": (c4 or {}).get("is_root"),
                     "interpreters": {k: {"version": (v.get("facts") or {}).get("version"),
                                          "broad_entries": v.get("broad_entries"),
                                          "sandbox_config_ok": v.get("sandbox_config_ok"),
                                          "sandbox_available": v.get("sandbox_available"),
                                          "hard_check_error": v.get("hard_check_error")}
                                      for k, v in interps.items()}},
        "captures": ["c4_interp.json", "c4_interp.txt", "logs/c4_interp.log"]})

    iso5 = (c5 or {}).get("isolation") or {}
    iso5_for_flag = (c5 or {}).get("isolation") or {}
    c5_ok = bool(c5 and (c5.get("condition_5_pass") if "condition_5_pass" in c5 else
                         (iso5_for_flag.get("effective") is True and not iso5_for_flag.get("waivers")
                          and not iso5_for_flag.get("exceptions")
                          and iso5_for_flag.get("worker_sandbox") is not None
                          and ((c5 or {}).get("outcome") or {}).get("kind") == "ok")))
    conditions.append({
        "id": "C5", "name": "§3.5 a real sandboxed smoke whose record shows effective: true",
        "result": "PASS" if c5_ok else "FAIL",
        "evidence": {"run_dir": (c5 or {}).get("run_dir"), "outcome": (c5 or {}).get("outcome"),
                     "effective": iso5.get("effective"), "waivers": iso5.get("waivers"),
                     "exceptions": iso5.get("exceptions"),
                     "euid": iso5.get("euid"), "ptrace_scope": iso5.get("ptrace_scope"),
                     "nsdelegate": iso5.get("nsdelegate"), "log_intact": iso5.get("log_intact"),
                     "cgroup_removed": (iso5.get("cgroup") or {}).get("removed")},
        "captures": ["c5_smoke.json", "logs/c5_smoke.log", "records/g0_smoke/run_record.json",
                     "records/g0_smoke/run.log"]})

    iso6 = (c6 or {}).get("isolation") or {}
    rep6 = (c6 or {}).get("gpu_report") or {}
    c6_ok = bool(c6 and c6.get("condition_6_pass"))
    conditions.append({
        "id": "C6", "name": "§3.6 GPU smoke with the sandbox on (effective true, no waivers/exceptions, no "
                            "CUDA error)",
        "result": "PASS" if c6_ok else "FAIL",
        "evidence": {"run_dir": (c6 or {}).get("run_dir"), "outcome": (c6 or {}).get("outcome"),
                     "effective": iso6.get("effective"), "waivers": iso6.get("waivers"),
                     "exceptions": iso6.get("exceptions"),
                     "gpu_uuid": (c6 or {}).get("gpu_uuid"),
                     "gpu_env_by_uuid": ((c6 or {}).get("environment_applied") or {}).get(
                         "CUDA_VISIBLE_DEVICES"),
                     "checks": (c6 or {}).get("checks"),
                     "gpu_report": {k: rep6.get(k) for k in
                                    ("ok", "cuda_available", "device_count", "device_name",
                                     "capability", "tensor_sum", "tensor_sum_ok", "matmul_value",
                                     "matmul_ok", "cuda_initialized", "pid", "ppid", "uid",
                                     "ns_pid", "ns_user", "ns_mnt", "dev_shm")},
                     "gpu_before_apps": (c6 or {}).get("gpu_before", {}).get("compute_apps"),
                     "gpu_after_apps": (c6 or {}).get("gpu_after", {}).get("compute_apps")},
        "captures": ["c6_gpu_smoke.json", "logs/c6_gpu_smoke.log",
                     "records/gpu_smoke/run_record.json", "records/gpu_smoke/run.log",
                     "records/gpu_smoke/gpu_report.json", "gpu_lease_status.txt",
                     "gpu_compute_apps_pre_gpu_smoke.txt", "gpu_compute_apps_post_gpu_smoke.txt"]})

    c7_ok = bool(c7 and c7.get("no_leftovers"))
    gpu_uuid_now = ""
    try:
        gpu_uuid_now = (c7 or {}).get("gpu_after", {}).get("nvidia_smi_L", {}).get(
            "stdout", "").split("(UUID: ")[1].split(")")[0]
    except (IndexError, AttributeError):
        gpu_uuid_now = ""
    conditions.append({
        "id": "C7", "name": "§3.7 end state: GPU before/after, no leftovers, disk, host/kernel, tool versions",
        "result": "PASS" if c7_ok else "FAIL",
        "evidence": {"no_leftovers": (c7 or {}).get("no_leftovers"),
                     "leftovers": (c7 or {}).get("leftovers"),
                     "gpu_uuid_after_nvidia_smi_L": gpu_uuid_now,
                     "gpu_before": (c7 or {}).get("gpu_before", {}).get("nvidia_smi_query"),
                     "gpu_after": (c7 or {}).get("gpu_after", {}).get("nvidia_smi_query"),
                     "gpu_compute_apps_after": (c7 or {}).get("gpu_after", {}).get("compute_apps"),
                     "disk": (c7 or {}).get("disk"), "host": (c7 or {}).get("host"),
                     "repo": (c7 or {}).get("repo"),
                     "tools": {k: v.get("stdout") for k, v in ((c7 or {}).get("tools") or {}).items()}},
        "captures": ["c7_final.json", "c7_final.txt", "host.json", "host_facts.txt",
                     "logs/c7_final.log"]})

    # ------------------------------------------------------------------ plan §6 / T1 pre-launch checks
    pre = []

    def pre_item(tid, name, ok, evidence, captures, note=""):
        pre.append({"id": tid, "name": name, "result": "PASS" if ok else ("DEFERRED" if ok is None else "FAIL"),
                    "evidence": evidence, "captures": captures, "note": note})

    h = host or {}
    gpuL = (h.get("gpu") or {}).get("nvidia_smi_L", {}).get("stdout", "")
    apps_before = text(cap / "gpu_compute_apps_before_all.txt").strip()
    pre_item("T1-1", "§6.1 delegated scope 8G/swap0/cgroup.kill and the isolation probes inside it",
             c3_ok and c5_ok and c6_ok,
             {"c3_cgroup": checks3, "c5_effective": iso5.get("effective"),
              "c6_effective": iso6.get("effective")},
             ["c3_cgroup.json", "c5_smoke.json", "c6_gpu_smoke.json"])
    pre_item("T1-2", "§6.2 nvidia-smi -L full UUID and no resident compute process on the card",
             bool(GPU_UUID in gpuL) and not apps_before,
             {"nvidia_smi_L": gpuL, "expected_uuid": GPU_UUID, "compute_apps_before": apps_before,
              "compute_apps_after": text(cap / "gpu_compute_apps_after_all.txt").strip()},
             ["nvidia_smi_L.txt", "gpu_state_before.txt", "gpu_compute_apps_before_all.txt",
              "gpu_compute_apps_after_all.txt"])
    pre_item("T1-3", "§6.2/§3.2 Yama ptrace_scope >= 1", bool((c2 or {}).get("condition_2_pass")),
             {"ptrace_scope": (c2 or {}).get("ptrace_scope_raw")}, ["c2_ptrace.json"])
    pre_item("T1-4", "non-root run uid", bool((h.get("euid") == 1008) and (c4 or {}).get("is_root") is False),
             {"euid": h.get("euid"), "user": (h.get("user") or {}).get("stdout")},
             ["host_facts.txt", "c4_interp.txt"])
    head, porcelain = git("rev-parse", "HEAD"), git("status", "--porcelain")
    pre_item("T1-5", "harness checkout at pin c025f89a, detached and clean",
             head == PIN and porcelain == "",
             {"expected_pin": PIN, "head": head, "dirty": bool(porcelain),
              "detached": git("symbolic-ref", "-q", "HEAD") == "",
              "origin_branch_head": git("rev-parse", "origin/mac-trackg-t1-tasl-20261121")},
             ["harness_pin.txt", "harness_pin_after.txt", "host.json"])
    echecks = (env or {}).get("checks") or {}
    pre_item("T1-6", "§6.5 torch312/jax312 from the census freezes, Python 3.12.16, uv version/interpreter "
                     "source recorded, uv pip freeze byte-equal",
             bool((env or {}).get("condition_env_pass")),
             {"checks": echecks,
              "uv": ((env or {}).get("uv") or {}).get("version", {}).get("stdout"),
              "python_find": ((env or {}).get("python_install") or {}).get(
                  "uv_python_find_3.12.16", {}).get("stdout"),
              "freezes": {n: {"freeze_sha256": (i.get("freeze") or {}).get("freeze_sha256"),
                              "uv_freeze_sha256": (i.get("freeze") or {}).get("uv_freeze_sha256"),
                              "byte_equal_uv_order": (i.get("freeze") or {}).get("byte_equal"),
                              "line_equal_sorted": (i.get("freeze") or {}).get("line_equal_sorted"),
                              "byte_equal_census_collation": (i.get("freeze") or {}).get(
                                  "locale_sorted_byte_equal"),
                              "locale_sorted_sha256": (i.get("freeze") or {}).get("locale_sorted_sha256"),
                              "lines": (i.get("freeze") or {}).get("freeze_lines")}
                          for n, i in ((env or {}).get("envs") or {}).items()},
              "separation": (env or {}).get("separation")},
             ["env_check.json", "env_check.txt", "env_uv.txt", "env_freeze_sha.txt",
              "logs/env_sync.log"])
    pre_item("T1-7", "isolation probes + sandboxed smoke at the pin show effective:true, waivers {}, "
                     "exceptions []",
             c1_ok and c4_ok and c5_ok,
             {"c1": c1_ok, "c4": c4_ok, "c5": c5_ok,
              "c5_effective": iso5.get("effective"), "c5_waivers": iso5.get("waivers"),
              "c5_exceptions": iso5.get("exceptions")},
             ["c1_userns_venv.json", "c1_userns_syspy.json", "c4_interp.json", "c5_smoke.json"])
    cg = c6c or {}
    pre_item("T1-8", "§6.4 CPU-only houseprice affinity 8-15 with no GPU variable, GPU node beside it not "
                     "slowed past timeout (short synthetic load check)",
             bool(cg.get("condition_cpu_gpu_pass")),
             {"cpu_cpus": cg.get("cpu_cpus"), "gpu_cpus": cg.get("gpu_cpus"),
              "checks": cg.get("checks"), "measurements": cg.get("measurements"),
              "gpu_apps_before": cg.get("gpu_apps_before"),
              "gpu_apps_during_coexistence": cg.get("gpu_apps_during_coexistence")},
             ["c6c_cpu_gpu_coexistence.json", "c6c_cpu_gpu_coexistence.txt",
              "cpu_gpu_lease_status.txt", "logs/c6c_cpu_gpu.log"])
    jaxrep = (c6b or {}).get("jax_report") or {}
    pre_item("T1-9", "§6.5 jax312 GPU availability (Breakout node environment; direct and sandboxed)",
             bool((c6b or {}).get("condition_jax_gpu_pass"))
             and bool(((env or {}).get("envs") or {}).get("jax312", {}).get("jax", {}).get("ok")),
             {"sandbox": {"effective": ((c6b or {}).get("isolation") or {}).get("effective"),
                          "waivers": ((c6b or {}).get("isolation") or {}).get("waivers"),
                          "exceptions": ((c6b or {}).get("isolation") or {}).get("exceptions"),
                          "checks": (c6b or {}).get("checks"),
                          "backend": jaxrep.get("backend"), "devices": jaxrep.get("devices"),
                          "device_kinds": jaxrep.get("device_kinds"),
                          "tensor_sum": jaxrep.get("tensor_sum"),
                          "matmul_ok": jaxrep.get("matmul_ok"),
                          "gymnax_breakout": jaxrep.get("gymnax_breakout"),
                          "pid": jaxrep.get("pid"), "ppid": jaxrep.get("ppid"),
                          "ns_pid": jaxrep.get("ns_pid"), "ns_user": jaxrep.get("ns_user")},
              "direct": ((env or {}).get("envs") or {}).get("jax312", {}).get("jax")},
             ["c6b_jax_gpu_smoke.json", "logs/c6b_jax_gpu_smoke.log",
              "records/jax_gpu_smoke/run_record.json", "records/jax_gpu_smoke/jax_report.json",
              "jax_lease_status.txt", "env_check.json"])
    disk = (c7 or {}).get("disk") or (h.get("disk") or {})
    disk_ok = bool(disk and any(d.get("free_gib", 0) >= 20 for d in disk.values() if isinstance(d, dict)))
    pre_item("T1-10", "disk headroom on TASL-2 (>= 20 GiB free floor)", disk_ok,
             {"disk": disk}, ["host_facts.txt", "c7_final.txt"])
    pre_item("T1-11", "§6.3 4090/Ada ratio on each node's baseline (first part)", None,
             {"deferred": "measured by the G.1b job's first part on the 4090, not pre-launch",
              "synthetic_proxy": cg.get("measurements")},
             ["c6c_cpu_gpu_coexistence.json"], note="DEFERRED to the job, per the plan")

    failed = [c["id"] for c in conditions if c["result"] != "PASS"]
    failed_pre = [c["id"] for c in pre if c["result"] == "FAIL"]
    overall = "PASS" if not failed and not failed_pre else "FAIL"
    verdict = ("GO: TASL-2 host-condition gate for the G.1b pre-launch (HARNESS_ISOLATION §3 items 1-7 PASS "
               "at harness pin c025f89a; T1 plan §6 items in scope PASS). Not a launch authorization; the "
               "author's signed note and both keys are still required." if overall == "PASS" else
               "STOP: a host condition failed; do not start G.1b on TASL-2.")
    summary = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "authority": "R1-T1-HOST-TASL / T1_TASL_PLAN §6 (pre-launch host test)",
               "host": "TASL-2", "harness_pin": PIN, "repo": str(repo), "t1_root": str(t1),
               "gpu_uuid": GPU_UUID,
               "overall": overall, "failed_conditions": failed, "failed_prelaunch": failed_pre,
               "conditions": conditions, "prelaunch": pre,
               "supplementary": {"isolation_pytest": pytest_rec,
                                 "host_check_binding": {
                                     "host_check_host": "TASL-2",
                                     "host_check_harness_commit": PIN,
                                     "host_check_items": "1-7 PASS" if not failed else "FAIL",
                                     "host_check_verdict": "PASS" if not failed else "FAIL"}},
               "verdict": verdict}
    (cap / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
                                      encoding="utf-8")
    lines = [f"R1-T1-HOST-TASL TASL-2 G.1b pre-launch host check — {summary['utc']}",
             f"host={summary['host']} pin={PIN} repo={repo}", "",
             "## HARNESS_ISOLATION §3 items 1-7 (binding table)", "",
             "| # | Condition | Result |", "|---|---|---|"]
    for c in conditions:
        lines.append(f"| {c['id']} | {c['name']} | **{c['result']}** |")
    lines += ["", "## T1_TASL_PLAN §6 pre-launch items in scope on TASL-2", "",
              "| # | Check | Result |", "|---|---|---|"]
    for c in pre:
        lines.append(f"| {c['id']} | {c['name']} | **{c['result']}** |")
    lines += ["", f"OVERALL: **{overall}**", f"FAILED (§3): {failed or 'none'}",
              f"FAILED (§6 in scope): {failed_pre or 'none'}"]
    if pytest_rec:
        lines.append(f"isolation pytest (supplementary): {json.dumps(pytest_rec.get('counts', pytest_rec))}")
    lines += ["", f"VERDICT: {verdict}"]
    (cap / "SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
