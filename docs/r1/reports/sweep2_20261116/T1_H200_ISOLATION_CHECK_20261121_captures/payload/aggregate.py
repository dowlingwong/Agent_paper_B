"""R1-T1-HOST-H200: aggregate the probe JSONs of one HTCondor container job into isolation_check.json.

Per-condition PASS/FAIL follow `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 ("Host conditions and waivers")
plus the experiment-agent list (items 1-7) and §5.5.  The `as-instructed` core revision (68cdd1a) and the
accepted sandbox-fix revision (5403392e) are reported separately so a code defect is never attributed to the host.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

import lib_iso


def load(path: str | Path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def condition(cid: str, name: str, result: bool | None, reason: str, evidence: list[str],
              waiver: str | None = None) -> dict:
    return {"id": cid, "name": name, "waiver": waiver,
            "result": ("PASS" if result else "FAIL") if result is not None else "NOT TESTED",
            "pass": bool(result), "reason": reason, "evidence": evidence}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out_dir)
    host = load(out / "host.json") or {}
    cgroup = load(out / "cgroup.json") or {}
    userns = load(out / "userns.json") or {}
    sandbox = [load(p) or {} for p in sorted(glob.glob(str(out / "sandbox_*.json")))]
    smoke = [load(p) or {} for p in sorted(glob.glob(str(out / "smoke_*.json")))]
    gpu = load(out / "gpu_smoke.json") or {}
    pytest_log = load(out / "pytest_isolation.json") or {}
    cgroup_parent = (out / "cgroup_parent.txt").read_text().strip() if (out / "cgroup_parent.txt").exists() else ""

    by_rev = {}
    for item in sandbox:
        by_rev.setdefault(item.get("revision", "?"), []).append(item)
    smoke_by_tag = {item.get("tag", "?"): item for item in smoke}

    conditions: list[dict] = []

    # C1 -- cgroup v2 parent the run's uid can write, with cgroup.kill (waiver: no_cgroup)
    c1 = bool(cgroup.get("condition_C1_pass"))
    if c1:
        chosen = cgroup.get("chosen") or {}
        rec = chosen.get("record") or {}
        reason = (f"delegated cgroup v2 parent accepted by the unit's own RunCgroup: {chosen.get('parent')}; "
                  f"kill={rec.get('kill')}; migration_possible={rec.get('migration_possible')}")
    else:
        failures = cgroup.get("failure_reasons") or []
        reason = "; ".join(f"{item.get('path')}: {item.get('error')}" for item in failures[:6]) or \
            "no writable cgroup v2 parent (see cgroup.json)"
        mount = cgroup.get("cgroup_mount") or []
        if mount and "ro," in mount[0].split(" - ")[0]:
            reason += f" [/sys/fs/cgroup is mounted read-only inside the container: {mount[0][:200]}]"
    conditions.append(condition("C1", "cgroup v2 parent the run's uid can write, with cgroup.kill",
                                c1, reason, ["cgroup.json", "cgroup_parent.txt"], "no_cgroup"))

    # C2 -- not root (waiver: root)
    euid = host.get("euid", userns.get("euid"))
    c2 = isinstance(euid, int) and euid != 0
    conditions.append(condition("C2", "the run is not root (euid != 0)", c2,
                                f"euid={euid} inside the container job" if c2 else f"euid={euid}: runs as root",
                                ["host.json"], "root"))

    # C3 -- unprivileged user namespaces with mount, PID and network namespaces (waiver: no_worker_sandbox)
    fix_probes = by_rev.get("fix_5403392e", [])
    fix_probe_ok = [item for item in fix_probes if (item.get("sandbox_probe") or {}).get("ok")]
    c3 = bool(userns.get("condition_C3_pass")) and bool(fix_probe_ok)
    tree = userns.get("full_namespace_tree") or {}
    pid1 = tree.get("pid1_child") or {}
    if c3:
        reason = ("real probe: unshare(CLONE_NEWUSER) + uid/gid map, CLONE_NEWNS, CLONE_NEWNET, CLONE_NEWCGROUP, "
                  f"CLONE_NEWPID ok; PID-1 pivot_root={pid1.get('pivot_root')}; write in new root="
                  f"{pid1.get('write_in_new_root')}; usable={pid1.get('proc_self_status_readable')}")
    else:
        reason = f"unshare/pivot_root probe failed; steps={tree.get('userns_steps')}; stopped_after=" \
                 f"{tree.get('stopped_after')}; pid1_child={pid1}"
    unit = {rev: [{"interpreter": item.get("interpreter"),
                   "sandbox_probe": item.get("sandbox_probe"),
                   "sys_path_hard_check": item.get("sys_path_hard_check")} for item in items]
            for rev, items in by_rev.items()}
    conditions.append(condition("C3", "unprivileged user namespaces with mount, PID and network namespaces "
                                      "(the sandbox probe)", c3,
                                reason + f"; unit sandbox probe by revision: {json.dumps(unit, default=str)[:2000]}",
                                ["userns.json", "sandbox_*.json"], "no_worker_sandbox"))

    # C4 -- Yama ptrace_scope >= 1 (waiver: ptrace_scope)
    scope = (host.get("sysctls", {}).get("kernel.yama.ptrace_scope", {}) or {}).get("value")
    try:
        scope_int = int(scope)
    except (TypeError, ValueError):
        scope_int = None
    c4 = scope_int is not None and scope_int >= 1
    conditions.append(condition("C4", "Yama ptrace_scope >= 1", c4,
                                f"/proc/sys/kernel/yama/ptrace_scope = {scope!r}" + ("" if c4 else
                                                                                      " (needs >= 1; waiver not taken)"),
                                ["host.json"], "ptrace_scope"))

    # C5 -- timeout factor 3 (waiver: timeout_factor)
    tf = host.get("timeout_factor_check") or {}
    c5 = bool(tf.get("ok"))
    conditions.append(condition("C5", "timeout factor 3 (R1-TRACKG-PORT-DECISIONS (4))", c5,
                                f"default factor={tf.get('default_timeout_factor')} -> "
                                f"{tf.get('timeout_seconds_at_measured_10s')} s at measured 10 s; "
                                f"factor 2 refused without waiver={tf.get('factor_two_refused')}"
                                + (f"; error={tf.get('error')}" if not c5 else ""),
                                ["host.json"], "timeout_factor"))

    # C6 -- the run interpreter's sys.path holds no home directory / runs tree (hard RunnerError, no waiver)
    hard = []
    for rev, items in by_rev.items():
        for item in items:
            hard.append({"revision": rev, "interpreter": item.get("interpreter"),
                         "check": item.get("sys_path_hard_check"),
                         "sys_path": item.get("interpreter_paths")})
    accepted_rev = [h for h in hard if h["revision"] == "fix_5403392e"]
    c6 = bool(accepted_rev) and all((h.get("check") or {}).get("ok") for h in accepted_rev)
    bad = [h for h in accepted_rev if not (h.get("check") or {}).get("ok")]
    conditions.append(condition("C6", "the run interpreter's sys.path holds no home directory / runs tree "
                                      "(hard RunnerError, no waiver)", c6,
                                ("all accepted-revision interpreters pass the unit's hard check; " if c6 else
                                 f"hard check failed: {json.dumps(bad, default=str)[:1500]}; ")
                                + f"per revision: {json.dumps([{k: v for k, v in h.items() if k != 'sys_path'} for h in hard], default=str)[:2500]}",
                                ["sandbox_*.json"], None))

    # C7 -- a real sandboxed smoke whose record shows effective: true (experiment-agent item 6)
    real = [item for item in smoke if not item.get("diagnostic_waivers")]
    passing = [item for item in real if item.get("condition_pass")]
    c7 = bool(passing)
    if c7:
        first = passing[0]
        iso = first.get("isolation") or {}
        reason = (f"smoke through the unit's own fixture/runner: revision={first.get('revision')}, "
                  f"record effective={iso.get('effective')}, waivers={iso.get('waivers')}, "
                  f"exceptions={iso.get('exceptions')}, outcome={first.get('outcome')}, euid={iso.get('euid')}, "
                  f"ptrace_scope={iso.get('ptrace_scope')}, nsdelegate={iso.get('nsdelegate')}, "
                  f"cgroup={(iso.get('cgroup') or {})}")
    else:
        details = []
        for item in real:
            if item.get("refused"):
                details.append(f"{item.get('tag')}: refused: {item.get('refusal_reason')}")
            elif item.get("error"):
                details.append(f"{item.get('tag')}: error: {item.get('error').splitlines()[-1]}")
            else:
                iso = item.get("isolation") or {}
                details.append(f"{item.get('tag')}: effective={iso.get('effective')} waivers={iso.get('waivers')} "
                               f"outcome={item.get('outcome')}")
        diag = [item for item in smoke if item.get("diagnostic_waivers")]
        for item in diag:
            iso = item.get("isolation") or {}
            details.append(f"[diagnostic {item.get('tag')}] effective={iso.get('effective')} "
                           f"waivers={iso.get('waivers')} outcome={item.get('outcome')} "
                           f"refused={item.get('refused')} reason={item.get('refusal_reason')}")
        reason = "; ".join(details) or "no smoke result"
    conditions.append(condition("C7", "a real sandboxed smoke whose record shows effective: true "
                                      "(no waivers, no exceptions)", c7,
                                reason, ["smoke_*.json", "records/"], "no_cgroup/root/ptrace_scope/"
                                                                     "no_worker_sandbox (none taken)"))

    # C8 -- GPU smoke with the sandbox on, CUDA IPC across the PID namespace (core §5.5)
    gpu_diag = None
    import glob as _glob
    for path in sorted(_glob.glob(str(out / "gpu_smoke_diag.json"))):
        gpu_diag = load(path) or None
    c8 = bool(gpu.get("condition_pass"))
    # NO GPU in this job (CPU-only allocation on an H200 node): the GPU smoke is pending, not failed
    gpu_absent = bool(gpu.get("refused")) and "no CUDA device allocated" in str(gpu.get("refusal_reason"))
    giso = gpu.get("isolation") or {}
    if c8:
        reason = (f"CUDA IPC hand-off passed in the sandboxed worker: outcome={gpu.get('outcome')}, "
                  f"exceptions={giso.get('exceptions')}, waivers={giso.get('waivers')}, "
                  f"plain-process control ipc_ok={(gpu.get('plain_control') or {}).get('plain_ipc_ok')}, "
                  f"gpu={ (gpu.get('gpu_before') or {}).get('name') }")
    else:
        reason = (f"gpu probe: refused={gpu.get('refused')}, refusal={gpu.get('refusal_reason')}, "
                  f"outcome={gpu.get('outcome')}, log_ipc_failure="
                  f"{'cuda ipc report' in (gpu.get('run_log') or '')}, "
                  f"run_log_tail={(gpu.get('run_log') or '')[-1200:]!r}, "
                  f"plain_control_ipc_ok={(gpu.get('plain_control') or {}).get('plain_ipc_ok')}, "
                  f"error={(gpu.get('error') or '').splitlines()[-1:]}; "
                  f"diagnostic_run(diag waivers={(gpu_diag or {}).get('diagnostic_waivers')}): "
                  f"outcome={(gpu_diag or {}).get('outcome')}, refused={(gpu_diag or {}).get('refused')}, "
                  f"refusal={(gpu_diag or {}).get('refusal_reason')}, ipc_in_log="
                  f"{'cuda ipc report' in ((gpu_diag or {}).get('run_log') or '')}, "
                  f"plain_control_ipc_ok={((gpu_diag or {}).get('plain_control') or {}).get('plain_ipc_ok')}"
                  ) if gpu else "no GPU probe result"
    conditions.append(condition("C8", "GPU smoke with the sandbox on: CUDA IPC across the PID namespace (§5.5)",
                                None if gpu_absent else c8,
                                ("NOT TESTED in this job: no GPU was allocated to it (CPU-only allocation on an "
                                 "H200 node); a 1-GPU job with the same payload is submitted separately. "
                                 if gpu_absent else "") + reason,
                                ["gpu_smoke.json", "gpu_smoke_diag.json", "records/"], None))

    # as-instructed vs accepted-fix summary
    old_smoke = smoke_by_tag.get("smoke_old_nowaiver") or {}
    old_sandbox = [item for item in by_rev.get("old_68cdd1a", [])]
    summary_revisions = {
        "as_instructed_68cdd1a": {
            "sandbox_probes": [{"interpreter": item.get("interpreter"),
                                "sandbox_probe": item.get("sandbox_probe")} for item in old_sandbox],
            "no_waiver_smoke": {"refused": old_smoke.get("refused"),
                                "refusal_reason": old_smoke.get("refusal_reason"),
                                "outcome": old_smoke.get("outcome")},
        },
        "accepted_fix_5403392e": {
            "sandbox_probes": [{"interpreter": item.get("interpreter"),
                                "sandbox_probe": item.get("sandbox_probe")}
                               for item in by_rev.get("fix_5403392e", [])],
            "no_waiver_smoke": {"refused": (smoke_by_tag.get("smoke_fix_nowaiver") or {}).get("refused"),
                                "refusal_reason": (smoke_by_tag.get("smoke_fix_nowaiver") or {}).get("refusal_reason"),
                                "outcome": (smoke_by_tag.get("smoke_fix_nowaiver") or {}).get("outcome")},
        },
    }

    failed = [item["id"] for item in conditions if item["result"] == "FAIL"]
    not_tested = [item["id"] for item in conditions if item["result"] == "NOT TESTED"]
    all_pass = all(item["result"] == "PASS" for item in conditions)
    verdict = ("ALL CONDITIONS PASS: T1 label runs on NEMO2 H200 are viable."
               if all_pass else
               f"FAIL ({', '.join(failed)}): the whole T1 table moves to Ada (PLAN row R1-T1-HOST-H200).")
    if not failed and not_tested:
        verdict = (f"INCOMPLETE ({', '.join(not_tested)}): no host condition failed, but the GPU smoke is not "
                   f"exercised in this job; the 1-GPU job with the same payload supplies it.")
    payload = {
        "schema": "r1_t1_h200_isolation_check/v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task": "R1-T1-HOST-H200: harness-isolation host conditions inside the HTCondor container on one NEMO2 H200",
        "authority": "docs/r1/reports/HARNESS_ISOLATION_20261117.md §3, §5.5; PLAN row R1-T1-HOST-H200 (main 4aac5209)",
        "host": {"hostname": host.get("hostname"), "euid": euid, "uname": host.get("uname"),
                 "os_release": (host.get("os_release") or "").splitlines()[:3],
                 "container": host.get("container"), "gpu": host.get("gpu"),
                 "ptrace_scope": (host.get("sysctls", {}).get("kernel.yama.ptrace_scope") or {}),
                 "cgroup_fs": host.get("cgroup_fs")},
        "image": {"expected_digest": "sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd",
                  "expected_tag": "20261115-v2-e1cb6d8e",
                  "VERSIONS_txt": (host.get("image") or {}).get("VERSIONS_txt")},
        "core_revisions": {"as_instructed": "68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e "
                                           "(mac-harness-isolation-20261117; accepted on published main)",
                           "accepted_fix": "5403392e94cb59d732f45d6702fc857531ad8fd5 "
                                           "(mac-harness-isolation-fix-20261119; Ada host-check fix, accepted in "
                                           "docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_FIX_20261119.md)"},
        "conditions": conditions,
        "condition_results": {item["id"]: item["result"] for item in conditions},
        "failed_conditions": failed,
        "not_tested_conditions": not_tested,
        "summary_by_revision": summary_revisions,
        "pytest_isolation": pytest_log,
        "cgroup_parent_used": cgroup_parent or None,
        "overall": "PASS" if all_pass else ("INCOMPLETE" if (not failed and not_tested) else "FAIL"),
        "verdict": verdict,
        "notes": [
            "ENGINEERING_ONLY: no T1 labels, no sweep-2 change, nothing on main.",
            "A condition is PASS only when the accepted unit itself accepts the host with no waiver; "
            "the labelled diagnostic no_cgroup waiver runs (when condition C1 fails) are never effective and "
            "are reported as diagnostics only.",
            "The as-instructed core 68cdd1a carries the pre-fix bind-remount defect (review defect A) and is "
            "expected to refuse the sandbox on any host whose /sys carries locked nodev/noexec; the accepted fix "
            "5403392e is the code whose host conditions decide viability.",
        ],
    }
    lib_iso.write_json(args.out, payload)
    print(json.dumps({"overall": payload["overall"], "failed": failed,
                      "condition_results": payload["condition_results"]}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
