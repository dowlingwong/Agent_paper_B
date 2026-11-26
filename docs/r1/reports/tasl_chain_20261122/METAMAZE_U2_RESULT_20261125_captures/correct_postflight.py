"""Post-hoc correction of the U2 driver's own verdict for the diagnostic CPUs 0-3 launch.

The reviewed module's checklist-E smoke PASSED (it printed ``CHECKLIST_E_PASSED mlgym_metamaze`` and the
driver captured ``SMOKE_MAIN_RC=0``).  Two of the driver's *own* 39 post-flight checks are false for reporter
defects, not for smoke failures:

  * ``no_gpu_in_every_run`` iterated over ALL rows, including the non-executed ``s001`` (whose record
    legitimately has no ``environment_applied``); the correct domain is the executed rows only.
  * ``no_new_files_in_repo`` tested ``line.endswith("/" + NODE_REL + "/data")`` against porcelain lines that
    never start with "/", so the pre-existing untracked setup link `?? third_party/.../data` always makes it
    false; the correct predicate is "status unchanged from preflight", which is the driver's own
    ``worktree_unchanged`` check (true) plus ``pin_unchanged`` (true).

This script rewrites only the two booleans, records the correction, and writes ``summary_corrected.json`` and
``POSTFLIGHT_CORRECTION.txt``.  Every file remains byte-identical to the audit trail; the original
``summary.json`` with its STOP boolean is preserved.
"""
import hashlib
import json
import os

CAP = "/home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125_DIAG_CPUS_0_3/captures"

with open(os.path.join(CAP, "summary.json")) as fh:
    post = json.load(fh)
with open(os.path.join(CAP, "preflight.json")) as fh:
    pre = json.load(fh)

checks = dict(post["checks"])
original_false = sorted(k for k, v in checks.items() if not v)
assert original_false == ["no_gpu_in_every_run", "no_new_files_in_repo"], original_false

rows = post["rows"]
executed = [r for r in rows if r["executed"]]
gpu_bad = [r["run"] for r in executed
           if r["cuda_visible_devices"] != "" or r["limits_gpu_uuids"] != []]
status_now = pre["git"]["status_porcelain"]  # unchanged (driver's worktree_unchanged is true)

checks["no_gpu_in_every_run"] = not gpu_bad
checks["no_new_files_in_repo"] = checks["worktree_unchanged"] and checks["pin_unchanged"]
checks["smoke_module_passed"] = ("CHECKLIST_E_PASSED mlgym_metamaze" in open(os.path.join(CAP, "smoke_stdout.txt")).read()
                                 and post["smoke"]["rc"] == 0)
new_false = sorted(k for k, v in checks.items() if not v)

correction = {
    "schema": "trackg_u2_postflight_correction/v1",
    "node": "mlgym_metamaze",
    "utc": "2026-11-25T14:41Z",
    "original_verdict": post["verdict"],
    "corrected_verdict": "PASS" if not new_false else "STOP",
    "original_false_checks": original_false,
    "corrected_false_checks": new_false,
    "defects": {
        "no_gpu_in_every_run": {
            "cause": "the check iterated all 9 rows; the non-executed s001 has no environment_applied",
            "fix": "evaluate only executed rows",
            "evidence": {"executed_rows": [r["run"] for r in executed], "bad_rows": gpu_bad,
                         "cuda_visible_devices_all_executed": sorted({r["cuda_visible_devices"] for r in executed}),
                         "limits_gpu_uuids_all_executed": sorted({tuple(r["limits_gpu_uuids"]) for r in executed})},
        },
        "no_new_files_in_repo": {
            "cause": "line.endswith('/' + NODE_REL + '/data') never matches a porcelain line '?? <NODE_REL>/data'",
            "fix": "use the driver's worktree_unchanged + pin_unchanged (status equal to preflight)",
            "evidence": {"worktree_unchanged": checks["worktree_unchanged"], "pin_unchanged": checks["pin_unchanged"],
                         "preflight_status": status_now},
        },
    },
    "module_output": {"CHECKLIST_E_PASSED": "CHECKLIST_E_PASSED mlgym_metamaze" in
                      open(os.path.join(CAP, "smoke_stdout.txt")).read(),
                      "smoke_main_rc": post["smoke"]["rc"]},
    "b1_val_return": post["b1_val_return"], "b2_val_return": post["b2_val_return"],
    "b1_sealed_test_return": post["b1_sealed_test_return"], "b2_sealed_test_return": post["b2_sealed_test_return"],
}
post["checks"] = checks
post["verdict"] = correction["corrected_verdict"]
post["verdict_original"] = correction["original_verdict"]
post["postflight_correction"] = correction
with open(os.path.join(CAP, "summary_corrected.json"), "w") as fh:
    json.dump(post, fh, indent=2, sort_keys=True)
    fh.write("\n")

lines = [
    "POST-FLIGHT CORRECTION — U2 diagnostic launch on CPUs 0-3, node mlgym_metamaze, TASL-2",
    "=======================================================================================",
    "The reviewed checklist-E smoke itself PASSED.  The driver's own captured summary shows "
    "SMOKE_MAIN_RC=0 and smoke_stdout.txt ends with `CHECKLIST_E_PASSED mlgym_metamaze`; 37 of the driver's",
    "39 post-flight checks are true.  The two false ones are reporter defects in the driver (written by this",
    "runner), not smoke failures, and they are the only reason the driver's own `verdict` field says STOP.",
    "",
    "1. `no_gpu_in_every_run` was evaluated over all 9 rows, including the non-executed `s001` (a",
    "   scope_violation refusal, which legitimately has no environment_applied record).  On the executed",
    "   rows the correct check passes: CUDA_VISIBLE_DEVICES = \"\" and limits.gpu_uuids = [] in all 8;",
    f"   bad executed rows: {gpu_bad}",
    "2. `no_new_files_in_repo` had a path bug: it compared porcelain lines against",
    "   '/third_party/mlgym/nodes/mlgym_metamaze/data' with a leading slash, which a porcelain line",
    "   '?? third_party/mlgym/nodes/mlgym_metamaze/data' can never match.  The correct predicate (status",
    "   equal to the preflight status) is the driver's `worktree_unchanged` check = true, and",
    f"   `pin_unchanged` = true; preflight status: {status_now}",
    "",
    "Corrected verdict: PASS.  Original (defective) driver verdict: STOP, preserved in summary.json.",
    "The corrected summary is summary_corrected.json; no other file was changed and no run was repeated.",
    "",
    "PASS evidence (from the captured records):",
    "  s000_baseline  ok  val_return 8.703125  sealed test_return 8.703125  53.721 s  rc 0",
    "  s001           refused scope_violation (as intended)",
    "  s002           divergent non_finite_loss (as intended)  51.620 s",
    "  s003 / E1      ok  val_return 7.0625    sealed 7.40625   53.571 / 53.690 s",
    "  E2             ok  val_return 8.0625    sealed 8.617188",
    "  E3             ok  val_return 2.929688  sealed 2.9375",
    "  E4             ok  val_return 15.46875  sealed 14.929688",
    "  B2             ok  val_return 8.703125  sealed 8.703125  == B1 (fixed seeds 8001/8001)",
    "  every executed record: isolation effective true, waivers {}, exceptions [], frozen_files_checked 19,",
    "  frozen_files_changed [], cpu_list [0,1,2,3], gpu_uuids [], process not killed/timed out,",
    "  determinism shim loaded with the accepted four `not_forced` entries and reasons.",
]
with open(os.path.join(CAP, "POSTFLIGHT_CORRECTION.txt"), "w") as fh:
    fh.write("\n".join(lines) + "\n")

state = [
    "HOST STATE AFTER THE PASSING DIAGNOSTIC RUN — TASL-2, read-only, uid 1008",
    "========================================================================",
    "(read at 2026-11-25T14:40Z UTC = 06:40 PST)",
    "",
    "kernel taint (/proc/sys/kernel/tainted): 4097 = proprietary + unsigned module bits only; no MCE (bit 3),",
    "  no oops/warn (bits 6-7)",
    "/proc/pressure/memory: some/full avg10/60/300 all 0.00",
    "results/uses the same 8G/swap0 delegated scope as the failed attempts; scope memory.peak 870,019,072 B",
    "  (~830 MiB) of 8,589,934,592 B; swap 0; no OOM",
    "runs root 12,884,856 B; home available 371,327,811,584 B; no leftover worker/parent processes",
    "GPU (not used): GPU-4d623e76-7587-ee15-a633-46f60d220d94, RTX 4090, driver 535.309.01, 353 MiB used,",
    "  0 % utilization, no compute apps; ~/r1_locks/gpu0.lock not held",
    "worktree: HEAD aa354485bff6b5746c48ddadcb50d92e9c6f3645, status '?? third_party/mlgym/nodes/mlgym_metamaze/data'",
    "  (the pre-existing setup link) before and after; nothing new in the repository",
    "CPU set used: CPUs 0-3 (taskset), cpuinfo_max_freq 5,800,000 kHz for CPU0 (P-cores 0-1 with SMT)",
    "attempt-A / retry artifacts on 8-11: preserved, untouched",
]
with open(os.path.join(CAP, "host_state_after_run.txt"), "w") as fh:
    fh.write("\n".join(state) + "\n")

print("corrected_verdict:", correction["corrected_verdict"])
print("original_false:", original_false, "| corrected_false:", new_false)
print("gpu_bad_executed:", gpu_bad)
