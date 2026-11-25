#!/usr/bin/env python3
"""U2 postflight: read the one smoke's records, check every required field, derive the census
measured run time / timeout, resource numbers and the capture set (with SHA256SUMS).

Read-only over the runs root; writes only under ``$BASE/captures`` (outside the repository).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
H = Path("/home/dowling/r1_trackp/wt/titanic-20261125")
NODE = "mlgym_titanic"
BASE = Path(os.environ.get("U2_BASE",
                          "/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125"))
RAW = BASE / "raw"
RUNS = BASE / "runs"
CAP = BASE / "captures"
DATA_ROOT = Path("/home/dowling/r1_engineering/titanic_20261125/data")
PIN = "3a67042ba7e4211feb9681524f3879643c8cf635"
BRANCH = "mac-trackg-titanic-20261125"
DEPLOYED_PIN = "4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107"
DATA_MANIFEST = "c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4"
RUN_IDS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]
CENSUS_ROWS = ["s000_baseline", "B2", "E1", "E2", "E3", "E4"]  # c2 basis (smoke records excluded)
def _cpu_list(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out
EXPECTED_CPUS = _cpu_list(os.environ.get("U2_CPUS", "16-31"))
KIT_VALUES = {  # accepted kit checklist-E smoke (val_accuracy, sealed test_accuracy), seeds 8001/8001
    "s000_baseline": (0.775281, 0.763158),
    "B2": (0.775281, 0.763158),
    "s003": (0.803371, 0.772727),
    "E1": (0.803371, 0.772727),
    "E2": (0.775281, 0.751196),
    "E3": (0.792135, 0.784689),
    "E4": (0.792135, 0.746411),
}
LOSS_LINES = 15000
PROVISIONAL = 1800.0


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, cwd=cwd)


def git(*args: str) -> str:
    res = run(["git", *args], cwd=str(H))
    assert res.returncode == 0, f"git {' '.join(args)}: {res.stderr[-400:]}"
    return res.stdout.strip()


def read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def collect_rows() -> list[dict]:
    rows = []
    for path in sorted(RUNS.glob("runs_smoke/*/run_record.json")) + sorted(RUNS.glob("runs_edits/*/run_record.json")):
        run_dir = path.parent
        record = json.loads(path.read_text())
        iso = record.get("isolation") or {}
        diffusion = record.get("diff") or {}
        limits = record.get("limits") or {}
        channel_path = run_dir / "result_channel.txt"
        log_path = run_dir / "run.log"
        channel = channel_path.read_text(errors="replace") if channel_path.is_file() else ""
        log = log_path.read_text(errors="replace") if log_path.is_file() else ""
        rows.append({
            "run": run_dir.name,
            "executed": record.get("executed"),
            "diff_status": diffusion.get("status"),
            "diff_refusal": diffusion.get("refusal"),
            "outcome": record.get("outcome"),
            "sealed": record.get("sealed"),
            "elapsed_seconds_info_only": record.get("elapsed_seconds_info_only"),
            "isolation_effective": iso.get("effective"),
            "isolation_waivers": iso.get("waivers"),
            "isolation_exceptions": iso.get("exceptions"),
            "isolation_argv": iso.get("argv"),
            "frozen_files_checked": iso.get("frozen_files_checked"),
            "frozen_files_changed": iso.get("frozen_files_changed"),
            "log_intact": iso.get("log_intact"),
            "cgroup_path": (iso.get("cgroup") or {}).get("path"),
            "cgroup_kill_empty_after": (iso.get("cgroup") or {}).get("kill", {}).get("empty_after"),
            "ptrace_scope": iso.get("ptrace_scope"),
            "worker_sandbox": iso.get("worker_sandbox"),
            "determinism_not_forced": (record.get("determinism") or {}).get("not_forced"),
            "determinism_shim_loaded": (record.get("determinism") or {}).get("shim_loaded"),
            "determinism_torch": (record.get("determinism") or {}).get("torch_version"),
            "process_killed_with": (record.get("process") or {}).get("killed_with"),
            "timed_out": (record.get("process") or {}).get("timed_out"),
            "run_budget": record.get("run_budget"),
            "frozen_pin_sha256": record.get("frozen_pin_sha256"),
            "cuda_visible_devices": (record.get("environment_applied") or {}).get("CUDA_VISIBLE_DEVICES"),
            "timeout_recorded": (record.get("environment_applied") or {}).get("timeout_seconds"),
            "limits": limits,
            "code_state_sha256": record.get("code_state_sha256"),
            "log_sha256": record.get("log_sha256"),
            "log_file_sha256": sha256_file(log_path) if log_path.is_file() else None,
            "result_channel_sha256": iso.get("result_channel_sha256"),
            "result_channel_file_sha256": sha256_file(channel_path) if channel_path.is_file() else None,
            "result_channel_text": channel,
            "metric_lines": len(re.findall(r"^AR_METRIC val_accuracy=(\S+)$", channel, re.M)),
            "test_lines": len(re.findall(r"^AR_TEST test_accuracy=(\S+)$", channel, re.M)),
            "metric_in_log": len(re.findall(r"^AR_METRIC ", log, re.M)),
            "test_in_log": len(re.findall(r"^AR_TEST ", log, re.M)),
            "loss_lines": len(re.findall(r"^step \d+ loss \S+$", log, re.M)),
            "carriage_returns": "\r" in log,
            "run_record_sha256": sha256_file(path),
        })
    return rows


def main() -> int:
    pre = json.loads((RAW / "preflight.json").read_text())
    checks: dict[str, bool] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = bool(ok)
        if not ok:
            print(f"CHECK_FAILED {name}: {detail!r}")

    launch_rc = (BASE / "launch.rc")
    launch_rc_text = launch_rc.read_text().strip() if launch_rc.is_file() else "<missing>"
    smoke_stdout = (RAW / "smoke_stdout.txt").read_text(errors="replace") if (RAW / "smoke_stdout.txt").is_file() else ""
    launch_out = (RAW / "launch.out").read_text(errors="replace") if (RAW / "launch.out").is_file() else ""
    smoke_jsonl = []
    for line in smoke_stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                smoke_jsonl.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    check("launch_rc_zero", launch_rc_text == "0", launch_rc_text)
    check("checklist_e_passed", f"CHECKLIST_E_PASSED {NODE}" in smoke_stdout)
    check("single_scope_invocation", launch_out.count("Running scope as unit") == 1, launch_out.count("Running scope as unit"))

    # ---- run set and decisions
    expected = {"runs_smoke": {"s000_baseline", "s001", "s002", "s003"}, "runs_edits": {"E1", "E2", "E3", "E4", "B2"}}
    for family, ids in expected.items():
        fam = RUNS / family
        got = {p.name for p in fam.iterdir() if p.is_dir()} if fam.is_dir() else set()
        check(f"run_set_{family}", got == ids, sorted(got))
    rows = collect_rows()
    by_run = {r["run"]: r for r in rows}
    check("all_runs_present", set(by_run) == set(RUN_IDS), sorted(by_run))
    executed = [r for r in rows if r["executed"]]
    check("executed_count_8", len(executed) == 8, [r["run"] for r in executed])

    decisions = {}
    ledger = RUNS / "runs_smoke" / "smoke_ledger.jsonl"
    if ledger.is_file():
        for line in ledger.read_text().splitlines():
            entry = json.loads(line)
            decisions[entry["run_id"]] = entry["decision"]
    check("ledger_decisions",
          decisions == {"s000_baseline": "baseline", "s001": "not_run_refused",
                        "s002": "discarded_divergent", "s003": "kept"}, decisions)
    check("frozen_diff_refused",
          by_run.get("s001", {}).get("diff_refusal") == "scope_violation"
          and by_run.get("s001", {}).get("executed") is False, by_run.get("s001", {}).get("diff_refusal"))
    check("broken_divergent",
          (by_run.get("s002", {}).get("outcome") or {}).get("kind") == "divergent"
          and (by_run.get("s002", {}).get("outcome") or {}).get("reason") in ("non_finite_loss", "non_finite_metric"),
          by_run.get("s002", {}).get("outcome"))
    check("baseline_ok", (by_run.get("s000_baseline", {}).get("outcome") or {}).get("kind") == "ok")
    for name in ("E1", "E2", "E3", "E4", "B2"):
        check(f"edit_{name}_ok", (by_run.get(name, {}).get("outcome") or {}).get("kind") == "ok",
              by_run.get(name, {}).get("outcome"))
    for name in ("E1", "E2", "E3", "E4"):
        check(f"edit_{name}_applied", by_run.get(name, {}).get("diff_status") == "applied",
              by_run.get(name, {}).get("diff_status"))
    check("baseline_repeat_has_no_diff", by_run.get("B2", {}).get("diff_status") is None,
          by_run.get("B2", {}).get("diff_status"))

    # ---- isolation / determinism / no GPU / budget / timeout, every executed row
    iso_bad = [r["run"] for r in executed
               if not (r["isolation_effective"] is True and r["isolation_waivers"] == {}
                       and r["isolation_exceptions"] == [])]
    check("isolation_effective_all_executed", not iso_bad, iso_bad)
    check("frozen_files_checked_16", all(r["frozen_files_checked"] == 16 for r in executed),
          {r["run"]: r["frozen_files_checked"] for r in executed})
    check("isolation_no_frozen_change", all(r["frozen_files_changed"] == [] for r in executed))
    check("isolation_log_intact", all(r["log_intact"] is True for r in executed))
    check("isolation_ptrace_scope_1", all(r["ptrace_scope"] == 1 for r in executed),
          {r["run"]: r["ptrace_scope"] for r in executed})
    check("isolation_cgroup_kill_empty", all(r["cgroup_kill_empty_after"] is True for r in executed))
    check("isolation_worker_sandbox_present",
          all(isinstance(r["worker_sandbox"], dict) and r["worker_sandbox"] for r in executed))
    det_bad = [r["run"] for r in executed
               if r["determinism_not_forced"] != ["dataloader_workers"] or not r["determinism_shim_loaded"]]
    check("determinism_settings_forced", not det_bad, det_bad)
    check("determinism_torch_2_6_pinned_env",
          all((r["determinism_torch"] or "").startswith("2.6.0") for r in executed),
          {r["run"]: r["determinism_torch"] for r in executed})
    check("no_gpu_in_every_run", all(r["cuda_visible_devices"] == "" for r in executed),
          {r["run"]: r["cuda_visible_devices"] for r in executed})
    check("gpu_uuids_empty", all((r["limits"].get("gpu_uuids") or []) == [] for r in executed))
    check("deployed_pin_every_run", all(r["frozen_pin_sha256"] == DEPLOYED_PIN for r in executed))
    check("cgroup_parent_scope", all((r["limits"].get("cgroup_parent") or "").startswith("/sys/fs/cgroup")
                                     and ".scope" in (r["limits"].get("cgroup_parent") or "") for r in executed))
    check("cpu_list_expected", all(r["limits"].get("cpu_list") == EXPECTED_CPUS for r in executed),
          {r["run"]: r["limits"].get("cpu_list") for r in executed})
    check("full_budget_150000", all(r["run_budget"] == {"kind": "steps", "value": 150000} for r in executed),
          {r["run"]: r["run_budget"] for r in executed})
    check("provisional_timeout_recorded",
          all(r["limits"].get("provisional_timeout_seconds") == PROVISIONAL
              and r["limits"].get("measured_run_seconds") is None for r in executed),
          {r["run"]: (r["limits"].get("provisional_timeout_seconds"),
                      r["limits"].get("measured_run_seconds")) for r in executed})
    check("timeout_text_recorded",
          all((r["timeout_recorded"] or "").startswith("1800") for r in executed),
          {r["run"]: r["timeout_recorded"] for r in executed})
    check("no_timeout_no_kill",
          all(r["process_killed_with"] is None and r["timed_out"] is False for r in executed),
          {r["run"]: (r["process_killed_with"], r["timed_out"]) for r in executed})
    check("result_channel_one_line_each",
          all(r["metric_lines"] == 1 and r["test_lines"] == 1 for r in executed),
          {r["run"]: (r["metric_lines"], r["test_lines"]) for r in executed})
    check("result_channel_matches_record",
          all(r["result_channel_file_sha256"] == r["result_channel_sha256"] for r in executed))
    check("log_intact_sha",
          all(r["log_file_sha256"] == r["log_sha256"] for r in executed))
    check("no_metric_in_log", all(r["metric_in_log"] == 0 and r["test_in_log"] == 0 for r in executed))
    check("loss_lines_15000", all(r["loss_lines"] == LOSS_LINES for r in executed),
          {r["run"]: r["loss_lines"] for r in executed})
    check("no_carriage_returns", all(r["carriage_returns"] is False for r in executed))
    manager_sealed = []
    if ledger.is_file():
        for line in ledger.read_text().splitlines():
            entry = json.loads(line)
            if "sealed" in json.dumps(entry.get("record", {})):
                manager_sealed.append(entry["run_id"])
    check("manager_view_no_sealed", not manager_sealed, manager_sealed)

    # ---- determinism and reproduction of the accepted checklist-E values
    b1 = by_run.get("s000_baseline", {})
    b2 = by_run.get("B2", {})
    s003 = by_run.get("s003", {})
    e1 = by_run.get("E1", {})
    b1_val = (b1.get("outcome") or {}).get("value")
    b2_val = (b2.get("outcome") or {}).get("value")
    b1_test = (b1.get("sealed") or {}).get("test_accuracy")
    b2_test = (b2.get("sealed") or {}).get("test_accuracy")
    check("determinism_b2_equals_b1", b2_val == b1_val and b2_test == b1_test, {"B1": (b1_val, b1_test), "B2": (b2_val, b2_test)})
    check("determinism_s003_equals_E1",
          (s003.get("outcome") or {}).get("value") == (e1.get("outcome") or {}).get("value")
          and (s003.get("sealed") or {}).get("test_accuracy") == (e1.get("sealed") or {}).get("test_accuracy"))

    kit_ok, kit_detail = {}, {}
    for rid, (val, test) in KIT_VALUES.items():
        got = ((by_run.get(rid, {}).get("outcome") or {}).get("value"),
               (by_run.get(rid, {}).get("sealed") or {}).get("test_accuracy"))
        kit_ok[rid] = got == (val, test)
        kit_detail[rid] = {"now": got, "kit": (val, test)}
    check("reproduces_kit_checklist_e_values", all(kit_ok.values()), kit_detail)

    # ---- c2: measured run time from this census and the 3x timeout (chunk schema (0, 300])
    census_elapsed = {r["run"]: r["elapsed_seconds_info_only"] for r in rows if r["run"] in CENSUS_ROWS}
    check("census_elapsed_present", all(isinstance(v, (int, float)) for v in census_elapsed.values()), census_elapsed)
    slowest = max(census_elapsed.values())
    slowest_run = max(census_elapsed, key=census_elapsed.get)
    measured_run_seconds = int(math.ceil(slowest))
    timeout_seconds = 3.0 * measured_run_seconds
    check("measured_run_seconds_in_chunk_schema", 0 < measured_run_seconds <= 300,
          {"measured_run_seconds": measured_run_seconds, "slowest": slowest})
    check("measured_timeout_factor_3", True)

    # ---- resources, disk, GPU, worktree
    scope_peak = read_int(RAW / "scope_memory_peak.txt")
    monitor = json.loads((RAW / "monitor.json").read_text()) if (RAW / "monitor.json").is_file() else {}
    check("scope_memory_peak_present", isinstance(scope_peak, int) and scope_peak > 0, scope_peak)
    memory_events = (RAW / "scope_memory_events.txt").read_text() if (RAW / "scope_memory_events.txt").is_file() else ""
    oom = re.search(r"^oom_kill (\d+)$", memory_events, re.M)
    oom_count = int(oom.group(1)) if oom else 0
    check("no_oom_kill", oom_count == 0, memory_events)
    du = run(["du", "-sb", str(RUNS)])
    per_run_work = {}
    for family in ("runs_smoke", "runs_edits"):
        for d in sorted((RUNS / family).iterdir()):
            if d.is_dir() and (d / "work").is_dir():
                per_run_work[d.name] = int(run(["du", "-sb", str(d / "work")]).stdout.split()[0])
    resources = {
        "scope_cgroup": (RAW / "scope_inner.log").read_text().splitlines()[:20],
        "scope_memory_peak_bytes": scope_peak,
        "scope_memory_max_bytes": read_int(RAW / "scope_memory_max.txt"),
        "scope_memory_swap_max_bytes": read_int(RAW / "scope_memory_swap_max.txt"),
        "scope_subtree_memory_enabled": "+memory" in (
            (RAW / "scope_subtree_control_after.txt").read_text() if (RAW / "scope_subtree_control_after.txt").is_file() else ""),
        "monitor": monitor,
        "runs_root_bytes": int(du.stdout.split()[0]) if du.returncode == 0 else None,
        "per_run_work_bytes": per_run_work,
        "data_root_bytes": int(run(["du", "-sb", str(DATA_ROOT / "mlgym_titanic")]).stdout.split()[0]),
        "home_avail_bytes_after": int(run(["df", "-B1", "--output=avail", str(HOME)]).stdout.strip().splitlines()[-1]),
        "runs_root": str(RUNS),
    }
    check("memory_cap_8g_swap0",
          resources["scope_memory_max_bytes"] == 8589934592 and resources["scope_memory_swap_max_bytes"] == 0,
          (resources["scope_memory_max_bytes"], resources["scope_memory_swap_max_bytes"]))

    gpu = run(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu",
               "--format=csv,noheader"])
    apps = run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"])
    lease = HOME / "r1_locks/gpu0.lock"
    locks = run(["lslocks"]).stdout
    gpu_post = {
        "utc": now(),
        "gpus": gpu.stdout.strip().splitlines(),
        "compute_apps": apps.stdout.strip().splitlines() if apps.returncode == 0 else None,
        "lease_lock_stat": {"bytes": lease.stat().st_size, "mtime": lease.stat().st_mtime} if lease.exists() else None,
        "lease_held": any("gpu0.lock" in ln for ln in locks.splitlines()),
    }
    check("no_gpu_lease_taken", gpu_post["lease_held"] is False)
    check("lease_lock_untouched", pre["gpu"]["lease_lock_stat"] == gpu_post["lease_lock_stat"],
          {"before": pre["gpu"]["lease_lock_stat"], "after": gpu_post["lease_lock_stat"]})
    (RAW / "gpu_state_post.txt").write_text(
        f"utc: {gpu_post['utc']}\nnvidia-smi:\n" + ("\n".join(gpu_post["gpus"]) if gpu_post["gpus"] else "") +
        f"\ncompute apps:\n{apps.stdout.strip()}\nlease gpu0.lock: {gpu_post['lease_lock_stat']} "
        f"held={gpu_post['lease_held']}\n")

    status = git("status", "--porcelain").splitlines()
    check("worktree_unchanged", status == pre["git"]["status_porcelain"], status)
    check("pin_unchanged", git("rev-parse", "HEAD") == PIN)
    check("no_new_files_in_repo",
          all(ln in {"?? third_party/mlgym/nodes/mlgym_titanic/data",
                     "?? third_party/mlgym/nodes/mlgym_titanic/data/"} for ln in status), status)
    data_manifest_now = sha256_file(DATA_ROOT / "mlgym_titanic/data_manifest.json")
    check("data_manifest_unchanged", data_manifest_now == DATA_MANIFEST, data_manifest_now)
    check("data_root_still_read_only",
          not any(os.stat(p).st_mode & 0o222
                  for p in [DATA_ROOT / "mlgym_titanic",
                            *[DATA_ROOT / "mlgym_titanic" / n for n in ("train.csv", "test.csv", "ground_truth.csv")]]))
    check("runs_root_outside_repository", str(RUNS.resolve()).startswith(str(DATA_ROOT.parent)) and
          not str(RUNS.resolve()).startswith(str(H)))
    check("data_out_of_repository", pre["data"]["outside_repo"])

    verdict = "PASS" if all(checks.values()) else "STOP"
    summary = {
        "schema": "u2_census_smoke_result/v1",
        "utc": now(),
        "verdict": verdict,
        "node": NODE,
        "host": platform.node(),
        "launch_rc": launch_rc_text,
        "smoke_stdout_tail": smoke_stdout.strip().splitlines()[-3:],
        "smoke_jsonl": smoke_jsonl,
        "rows": rows,
        "checks": checks,
        "failed_checks": [k for k, v in checks.items() if not v],
        "b1": {"val_accuracy": b1_val, "test_accuracy": b1_test},
        "b2": {"val_accuracy": b2_val, "test_accuracy": b2_test},
        "census_timing": {
            "basis_runs": CENSUS_ROWS,
            "per_run_elapsed_seconds": census_elapsed,
            "slowest_run": slowest_run,
            "slowest_elapsed_seconds": slowest,
            "measured_run_seconds": measured_run_seconds,
            "timeout_factor": 3.0,
            "timeout_seconds": timeout_seconds,
            "chunk_schema_measured_run_seconds_range": [">0", "<=300"],
            "smoke_records_excluded": ["s002", "s003"],
            "smoke_provisional_timeout_seconds": PROVISIONAL,
            "stop_on_timeout": True,
        },
        "pins": pre["pins"],
        "data": pre["data"],
        "env": pre["env"],
        "smoke_entry": pre["smoke_entry"],
        "host_facts": {k: pre[k] for k in ("host", "kernel", "machine", "uid", "ptrace_scope", "systemd_version",
                                           "affinity", "cgroup", "cgroup_limits", "loadavg")},
        "git": pre["git"],
        "resources": resources,
        "gpu": {"pre": pre["gpu"], "post": gpu_post},
        "commands": {
            "setup": "AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/titanic_20261125/data PATH=<torch312>/bin:$PATH python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlgym_titanic",
            "preflight": "<torch312>/bin/python $BASE/scripts/pins_preflight.py",
            "launch": "systemd-run --user --scope --unit=u2-titanic-census-20261125T<HHMM>Z --collect -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 env PATH=<torch312>/bin:$PATH VIRTUAL_ENV=<torch312> CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 AR_TRACKG_DATA_ROOT=... taskset -c 8-11 bash $BASE/scripts/scope_inner.sh",
            "smoke": "<torch312>/bin/python -m tests.trackg.port_smoke_gpu --node mlgym_titanic --cpus 8-11 --memory-limit <external 8G scope> --runs-root $BASE/runs --provisional-timeout 1800",
            "postflight": "<torch312>/bin/python $BASE/scripts/postflight.py",
        },
    }
    infra = [r["run"] for r in rows
             if (r.get("outcome") or {}).get("kind") == "infrastructure_failure"]
    _scope_log_lines = (RAW / "scope_inner.log").read_text(errors="replace").splitlines()
    _scope_line = next((ln for ln in _scope_log_lines if ln.startswith("SCOPE=")), "")
    RETRY_UNIT = _scope_line.split("=", 1)[1].rsplit("/", 1)[-1] if _scope_line else "<unknown>"
    _launch_line = next((ln for ln in _scope_log_lines if ln.startswith("scope_inner_start_utc=")), "")
    RETRY_UTC_LAUNCH = _launch_line.split("=", 1)[1] if _launch_line else "<unknown>"
    summary["attempts"] = {
        "A": {"status": "aborted_by_lead_authorization", "valid_for_census": False,
              "preserved_root": "/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted",
              "utc_launch": "2026-11-25T12:55:25Z", "utc_abort": "2026-11-25T13:03:05Z",
              "unit": "u2-titanic-census-20261125T1256Z.scope", "cpus": "16-31 (E-cores on the i9-14900KF)",
              "reason": "CPU-set/schema risk: baseline reached step 97440/150000 in 458 s; projected >300 s per "
                        "census run, above the chunk schema cap measured_run_seconds in (0, 300]. Aborted by "
                        "lead authorization; preserved unmodified, excluded from the U2 record."},
        "B": {"status": "STOP", "valid_for_census": False,
              "preserved_root": "/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B",
              "utc_launch": "2026-11-25T13:04:10Z", "utc_end": "2026-11-25T13:16:01Z",
              "unit": "u2-titanic-census-20261125T1304Z.scope",
              "cpus": "8-11 (P-cores, the kit-accepted CPU set)",
              "smoke_main_rc": "1", "checklist_e_passed": False,
              "infrastructure_failures": ["E1", "E2"],
              "reason": "prior U2 attempt STOP with sporadic native signals: E1 killed signal 11 (0.532 s), "
                        "E2 killed signal 4 (0.660 s), B2 divergent nonzero_exit rc 1 (1.563 s); the five "
                        "completed runs reproduced the kit-accepted values; one launch, no retry; preserved "
                        "unmodified and excluded from the retry record."},
        "R": {"status": verdict, "valid_for_census": verdict == "PASS",
              "utc_launch": RETRY_UTC_LAUNCH, "unit": RETRY_UNIT,
              "cpus": "8-11 (P-cores, the kit-accepted CPU set)",
              "smoke_main_rc": launch_rc_text,
              "checklist_e_passed": f"CHECKLIST_E_PASSED {NODE}" in smoke_stdout,
              "infrastructure_failures": infra,
              "reason": "authorised single clean retry on an idle host after the clean Forest Cover U2 on the "
                        "same CPUs; one launch, no further retry."},
    }
    (RAW / "postflight.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    # ---- assemble the capture set
    if CAP.exists():
        shutil.rmtree(CAP)
    CAP.mkdir(parents=True)
    for src in sorted(RAW.iterdir()):
        if src.is_file():
            shutil.copy2(src, CAP / src.name)
    for name in ("run_records", "run_logs", "result_channels"):
        (CAP / name).mkdir()
    for family in ("runs_smoke", "runs_edits"):
        for d in sorted((RUNS / family).iterdir()):
            if not d.is_dir():
                continue
            run_name = d.name
            shutil.copy2(d / "run_record.json", CAP / "run_records" / f"{run_name}.json")
            if (d / "run.log").is_file():
                shutil.copy2(d / "run.log", CAP / "run_logs" / f"{run_name}.log")
            if (d / "result_channel.txt").is_file():
                shutil.copy2(d / "result_channel.txt", CAP / "result_channels" / f"{run_name}.txt")
    (CAP / "scripts").mkdir()
    for script in ("pins_preflight.py", "scope_inner.sh", "launch.sh", "monitor.py", "postflight.py"):
        shutil.copy2(BASE / "scripts" / script, CAP / "scripts" / script)
    (CAP / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        f"U2 CPU-only census smoke — {NODE} (MLGym Titanic), TASL-2, no GPU, no GPU lease",
        f"utc: {summary['utc']}",
        f"verdict: {verdict}",
        f"smoke: launch_rc={launch_rc_text} CHECKLIST_E_PASSED={'CHECKLIST_E_PASSED ' + NODE in smoke_stdout}",
        f"B1 val_accuracy={b1_val} sealed test_accuracy={b1_test}",
        f"B2 val_accuracy={b2_val} sealed test_accuracy={b2_test} (determinism B2==B1: {checks.get('determinism_b2_equals_b1')})",
        f"measured_run_seconds={measured_run_seconds} (slowest census {slowest_run} {slowest:.3f} s) "
        f"timeout={timeout_seconds:.1f} s (3 x measured, factor 3.0; schema (0, 300])",
        f"scope memory.peak={scope_peak} bytes memory.max={resources['scope_memory_max_bytes']} "
        f"memory.swap.max={resources['scope_memory_swap_max_bytes']}",
        f"runs_root={RUNS} bytes={resources['runs_root_bytes']}",
        "", "run executed diff_status kind value sealed_test elapsed_s iso_effective iso_waivers "
            "iso_exceptions det_not_forced killed frozen_files_checked",
    ]
    for r in rows:
        out = r["outcome"] or {}
        lines.append(f"{r['run']} {r['executed']} {r['diff_status']} {out.get('kind')} {out.get('value')} "
                     f"{(r['sealed'] or {}).get('test_accuracy')} {r['elapsed_seconds_info_only']} "
                     f"{r['isolation_effective']} {r['isolation_waivers']} {r['isolation_exceptions']} "
                     f"{r['determinism_not_forced']} {r['process_killed_with']} {r['frozen_files_checked']}")
    lines.append("")
    lines.append("checks: " + json.dumps(summary["checks"], sort_keys=True))
    summary_txt = "\n".join(lines) + "\n"
    (CAP / "summary.txt").write_text(summary_txt)
    (CAP / "ATTEMPT_LOG.txt").write_text(
        "Attempts on the reviewed MLGym Titanic kit (mlgym_titanic), 25 Nov 2026\n"
        "== pre-review kit-development attempts (preserved on the host, excluded from the U2 record) ==\n"
        "attempt 1 (25 Nov 03:41-03:43 PST): cpu_smoke_runs_attempt1_module_not_found/ - PATH interpreter\n"
        "  without pandas and a chmod-through-the-data-link PermissionError.\n"
        "attempt 2 (25 Nov 03:49 PST): cpu_smoke_runs_attempt2_e4_nonfinite/ - E4 draft non-finite feature.\n"
        "accepted kit smoke (25 Nov 04:11 PST): cpu_smoke_runs/ - CHECKLIST_E_PASSED mlgym_titanic (CPUs 8-11).\n"
        "== U2 attempt A (aborted by lead authorization, 12:55:25Z-13:03:05Z) ==\n"
        "  one launch on CPUs 16-31 (the 16 E-cores of the i9-14900KF); aborted on CPU-set/schema risk.\n"
        "  Preserved unmodified at /home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted\n"
        "== U2 attempt B (one launch, 13:04:10Z-13:16:01Z, CPUs 8-11) - PRIOR FAILED ATTEMPT, KEPT ==\n"
        "  preflight PASS, but the smoke STOPped with sporadic native crashes: E1 killed signal 11 (0.532 s),\n"
        "  E2 killed signal 4 (0.660 s), B2 divergent nonzero_exit rc 1 (worker connection closed); the five\n"
        "  completed runs reproduced the kit-accepted values. One launch, no retry; preserved unmodified at\n"
        "  /home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B\n"
        "== U2 RETRY R (this evidence root; one launch) ==\n"
        "  Authorised clean retry: the sibling U2 smokes that had been sharing CPUs 8-11 were stopped and the\n"
        "  same host then passed a clean Forest Cover U2 smoke on CPUs 8-11 (13:41-13:56Z). This retry ran\n"
        "  with no other smoke on the host, CPUs 8-11 P-cores, delegated 8G/swap0 scope, no GPU, no GPU lease,\n"
        "  no deletion, no push. One launch only; if it had STOPped again the evidence would have been\n"
        "  preserved with no further retry.\n"
        f"verdict: {verdict}; failed_checks={summary['failed_checks']}\n"
        f"B1 val_accuracy={b1_val} sealed test_accuracy={b1_test}; "
        f"B2 val_accuracy={b2_val} sealed test_accuracy={b2_test}; "
        f"determinism B2==B1: {checks.get('determinism_b2_equals_b1')}\n"
        f"scope memory.peak={scope_peak} bytes; runs_root={RUNS}\n"
        "Prior attempts A and B remain preserved unmodified and are excluded from the retry record.\n")
    attempt_a = os.environ.get("U2_ATTEMPT_A", "<preserved attempt-A root>")
    (CAP / "commands.txt").write_text(
        "# U2 census CPU smoke - authorised clean RETRY R (TASL-2, 25 Nov 2026)\n"
        f"# retry evidence root (outside the repository): {BASE}\n"
        "# prior failed attempt B preserved at /home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B\n"
        "# prior aborted attempt A preserved at /home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted\n"
        "# worktree: /home/dowling/r1_trackp/wt/titanic-20261125 "
        "(branch mac-trackg-titanic-20261125 @ 3a67042ba7e4211feb9681524f3879643c8cf635)\n"
        "export AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/titanic_20261125/data\n"
        "export PATH=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin:$PATH\n"
        "export VIRTUAL_ENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312\n"
        "export PYTHONDONTWRITEBYTECODE=1\n"
        "# preflight (no smoke)\n"
        f"$VIRTUAL_ENV/bin/python {BASE}/scripts/pins_preflight.py\n"
        "# the one retry smoke, inside the delegated 8G/swap0 scope, CPUs 8-11 P-cores, no GPU:\n"
        "systemd-run --user --scope --unit=<retry unit, see raw/scope_inner.log> --collect \\\n"
        "  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \\\n"
        "  env PATH=$VIRTUAL_ENV/bin:$PATH VIRTUAL_ENV=$VIRTUAL_ENV CUDA_VISIBLE_DEVICES= \\\n"
        "      PYTHONDONTWRITEBYTECODE=1 AR_TRACKG_DATA_ROOT=$AR_TRACKG_DATA_ROOT \\\n"
        f"      U2_BASE={BASE} U2_CPUS=8-11 \\\n"
        f"  taskset -c 8-11 bash {BASE}/scripts/scope_inner.sh\n"
        "# inside the scope (scope_inner.sh): AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)\n"
        "taskset -c 8-11 $VIRTUAL_ENV/bin/python -m tests.trackg.port_smoke_gpu \\\n"
        "  --node mlgym_titanic --cpus 8-11 \\\n"
        '  --memory-limit "external: systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G '
        '-p MemorySwapMax=0 (enforced cgroup)" \\\n'
        f"  --runs-root {BASE}/runs \\\n"
        "  --provisional-timeout 1800\n"
        "# actual timestamps and the launch console are preserved verbatim in raw/launch_env.txt,\n"
        "# raw/launch.out and raw/scope_inner.log. No retry was made after this one.\n"
        "# repo unchanged by the smoke; runs root outside the repository; no data copied into any repo/capture.\n")
    attempt_a = os.environ.get("U2_ATTEMPT_A")
    if attempt_a and Path(attempt_a).is_dir():
        a_root = Path(attempt_a)
        dst = CAP / "attempt_A_ecores_aborted"
        dst.mkdir(exist_ok=True)
        if (a_root / "ATTEMPT_A_ABORTED.txt").is_file():
            shutil.copy2(a_root / "ATTEMPT_A_ABORTED.txt", dst / "ATTEMPT_A_ABORTED.txt")
        for name in ("launch_env.txt", "launch.out", "scope_inner.log", "scope_probe.log", "preflight.json",
                     "pins.json", "env.txt", "setup.log", "monitor.json", "scope_memory_max.txt",
                     "scope_memory_swap_max.txt", "scope_subtree_control_after.txt", "gpu_state_pre.txt",
                     "data_manifest.json", "edits_manifest.json", "torch312.freeze.txt", "mlgym_titanic.yaml",
                     "git_head.txt", "git_status.txt", "git_diffstat_vs_base.txt", "preflight.log",
                     "preflight_attempt0_overstrict.log"):
            src = a_root / "raw" / name
            if src.is_file():
                shutil.copy2(src, dst / name)
        partial = a_root / "runs" / "runs_smoke" / "s000_baseline" / "run.log"
        if partial.is_file():
            shutil.copy2(partial, dst / "s000_baseline_partial_run.log")
        (dst / "README.txt").write_text(
            "Attempt A (preserved unmodified on TASL-2 at " + str(a_root) + "): one aborted launch on CPUs\n"
            "16-31 (E-cores). Only this curated subset is copied here; its scripts/ and the partial run tree\n"
            "remain on the host. Attempt A is excluded from the U2 record. See the paper-side report and\n"
            "ATTEMPT_A_ABORTED.txt for the abort reason and the lead authorization.\n")
    rows_out = []
    for path in sorted(CAP.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rows_out.append(f"{sha256_file(path)}  {path.relative_to(CAP)}")
    (CAP / "SHA256SUMS").write_text("\n".join(rows_out) + "\n")
    verify = run(["sha256sum", "-c", "SHA256SUMS"], cwd=str(CAP))
    sums_sha = sha256_file(CAP / "SHA256SUMS")
    print(f"SHA256SUMS files={len(rows_out)} verify_rc={verify.returncode} sha256={sums_sha}")
    if verify.returncode != 0:
        print(verify.stdout[-1200:], verify.stderr[-1200:])
    print(json.dumps({"verdict": verdict, "failed_checks": summary["failed_checks"],
                      "b1": summary["b1"], "b2": summary["b2"],
                      "measured_run_seconds": measured_run_seconds, "timeout_seconds": timeout_seconds,
                      "slowest": (slowest_run, slowest),
                      "captures_files": len(rows_out), "SHA256SUMS_sha256": sums_sha,
                      "captures_bytes": int(run(["du", "-sb", str(CAP)]).stdout.split()[0])}, sort_keys=True))
    print(f"U2_CPU_CENSUS_SMOKE_{verdict} node={NODE}")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"POSTFLIGHT_STOP: {exc}")
        sys.exit(3)
