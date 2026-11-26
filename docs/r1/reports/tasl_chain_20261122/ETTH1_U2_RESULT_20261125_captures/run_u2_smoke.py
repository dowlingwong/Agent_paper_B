#!/usr/bin/env python3
"""U2 CPU-only census smoke driver for the reviewed Track G kit ``gc7rc_etth1`` (ETTh1).

Ran on TASL-2 with no GPU and no GPU lease, inside a ``systemd-run --user --scope`` delegated scope
(``Delegate=yes``, ``MemoryMax=8G``, ``MemorySwapMax=0``), affinity 16-31, ``CUDA_VISIBLE_DEVICES=""``,
``PYTHONDONTWRITEBYTECODE=1``.

It executes the kit's standard GPU stub-manager smoke (``tests/trackg/port_smoke_gpu.py``, the checklist-E
census smoke) at the node's full 2,000-step budget on the real data.  The reviewed module's CLI refuses a
run without ``--gpu-uuid`` for every node that is not in ``CPU_ONLY_NODES``; ``gc7rc_etth1`` is a
GPU-capable torch node and is not in that set, so this driver overrides **only** that guard in memory
(``port_smoke_gpu.CPU_ONLY_NODES``) and calls the module's own ``main()`` with the kit's documented flags
(``--cpus``, ``--memory-limit``, ``--runs-root``, ``--provisional-timeout``).  No repository file is
changed; the run set, the run code, the full budget and the checks are the reviewed module's own.

Writes preflight/pins/data/env captures, every ``run_record.json``, run logs, result channels, a resource
summary (peak cgroup memory, disk) and ``SHA256SUMS`` into ``captures/``.  ENGINEERING_ONLY: no GPU, no
census measurement beyond this smoke, no evidence, no deletion, no push.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

HOME = Path.home()
H = HOME / "r1_trackg_20261125/harness_etth1"
BASE = Path(os.environ.get("U2_BASE") or
            (HOME / "r1_engineering/etth1_port_20261125/u2_census_smoke_20261125"))
RAW = BASE / "raw"
RUNS = BASE / "runs"
CAP = BASE / "captures"

PIN = "3a06d86721b0c1826b165b68a9781a561e4993f4"
BASE_COMMIT = "c025f89aeafc2199bf3487b4bcaa16678273c702"
EQ = {
    "node_spec_sha256": "8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c",
    "spec_raw_sha256": "9391f718bd7669438189f45b48a920786a6ca5a51854bd861b0f945ea3d00c22",
    "committed_pin_sha256": "818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27",
    "deployed_pin_sha256": "e314858234bb378dce4cad5cf0492cfa1ee76561c231e756b90f301672ddec93",
    "edits_manifest_sha256": "ba31fed3bb67c0d78825a0d026058cbeb3a0261971fe8a4766f138687b232306",
    "data_manifest_sha256": "eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b",
    "node_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
    "master_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
}
FREEZE_SHA = "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"
SERIES_SHA = "32a0ad070e7536e7099725098b24b74c775bc897d58f3c5868399a6f86c8d850"
SRC_CSV_SHA = "f18de3ad269cef59bb07b5438d79bb3042d3be49bdeecf01c1cd6d29695ee066"
RUN_IDS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_argv(argv: list[str], stdin_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, input=stdin_text)


def git(*args: str) -> str:
    res = run_argv(["git", *args], )
    assert res.returncode == 0, f"git {' '.join(args)} rc={res.returncode}: {res.stderr[-500:]}"
    return res.stdout.strip()


def cgroup_dir() -> Path:
    text = Path("/proc/self/cgroup").read_text().strip()
    assert text.startswith("0::"), f"not a unified cgroup v2 hierarchy: {text}"
    return Path("/sys/fs/cgroup") / text.split("::", 1)[1].lstrip("/")


def read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


class Monitor(threading.Thread):
    """Poll the smoke scope's child run cgroups for peak memory (and a little CPU accounting)."""

    def __init__(self, scope: Path):
        super().__init__(daemon=True)
        self.scope = scope
        self.stop = threading.Event()
        self.peak_memory: dict[str, int] = {}
        self.peak_anon: dict[str, int] = {}
        self.samples = 0

    def _cgroup_memory(self, path: Path) -> tuple[int | None, int | None]:
        current = read_int(path / "memory.current")
        anon = None
        try:
            for line in (path / "memory.stat").read_text().splitlines():
                key, _, value = line.partition(" ")
                if key == "anon":
                    anon = int(value)
                    break
        except OSError:
            pass
        peak = read_int(path / "memory.peak")
        return (max(current or 0, peak or 0) if current is not None or peak is not None else None,
                max(anon or 0, 0) if anon is not None else None)

    def run(self) -> None:
        while not self.stop.is_set():
            try:
                for entry in self.scope.iterdir():
                    if not entry.is_dir() or not entry.name.startswith("ar_"):
                        continue
                    mem, anon = self._cgroup_memory(entry)
                    if mem is not None:
                        self.peak_memory[entry.name] = max(self.peak_memory.get(entry.name, 0), mem)
                    if anon is not None:
                        self.peak_anon[entry.name] = max(self.peak_anon.get(entry.name, 0), anon)
                    self.samples += 1
            except OSError:
                pass
            self.stop.wait(0.1)


def preflight() -> dict:
    os.chdir(H)
    sys.path.insert(0, str(H))
    sys.path.insert(0, str(H / "src"))
    pre: dict = {"utc": now(), "host": socket.gethostname()}
    pre["kernel"] = platform.release()
    pre["machine"] = platform.machine()
    pre["python"] = sys.version
    pre["python_executable"] = sys.executable
    pre["uid"] = os.geteuid()
    pre["loadavg"] = os.getloadavg()
    pre["affinity"] = sorted(os.sched_getaffinity(0))
    pre["cgroup"] = str(cgroup_dir())
    pre["ptrace_scope"] = Path("/proc/sys/kernel/yama/ptrace_scope").read_text().strip()
    pre["systemd_version"] = run_argv(["systemd-run", "--version"]).stdout.splitlines()[0]
    pre["memory_max"] = (cgroup_dir() / "memory.max").read_text().strip()
    pre["memory_swap_max"] = (cgroup_dir() / "memory.swap.max").read_text().strip()
    pre["cuda_visible_devices_env"] = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    pre["ar_test_cgroup_parent_env"] = os.environ.get("AR_TEST_CGROUP_PARENT", "<unset>")
    pre["pythonhashseed"] = os.environ.get("PYTHONHASHSEED", "<unset>")
    pre["launch_env"] = {"PATH": os.environ.get("PATH"), "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
                         "PYTHONPATH": os.environ.get("PYTHONPATH"),
                         "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
                         "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE")}
    pre["python3_resolved"] = shutil.which("python3")
    assert pre["python3_resolved"] is not None, "STOP: python3 is not on PATH"
    assert Path(pre["python3_resolved"]).resolve() == Path(sys.executable).resolve(), (
        "STOP: python3 on PATH resolves to " + str(Path(pre["python3_resolved"]).resolve())
        + " not the pinned interpreter " + str(Path(sys.executable).resolve()))
    pre["py_dont_write_bytecode"] = os.environ.get("PYTHONDONTWRITEBYTECODE", "<unset>")

    import numpy
    import torch

    pre["torch"] = {
        "version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }
    pre["numpy"] = numpy.__version__

    # git and branch binding
    pre["git"] = {
        "head": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "status_porcelain": git("status", "--porcelain").splitlines(),
        "base_commit_is_ancestor": run_argv(["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"]).returncode == 0,
        "diff_name_status_vs_base": git("diff", "--name-status", BASE_COMMIT, "HEAD").splitlines(),
        "diffstat_vs_base": git("diff", "--stat", BASE_COMMIT, "HEAD").splitlines()[-1],
    }
    assert pre["git"]["head"] == PIN, f"STOP: HEAD {pre['git']['head']} != reviewed pin {PIN}"
    assert pre["git"]["branch"] == "mac-trackg-etth1-20261125", pre["git"]["branch"]
    assert pre["git"]["status_porcelain"] in ([], ["?? nodes/gc7rc_etth1/data"]), \
        f"STOP: worktree not clean at the pin: {pre['git']['status_porcelain']}"

    # pins, recomputed from the committed tree with the kit's own frozen-pin helpers
    from autoresearch.trackg import isolation
    from autoresearch.trackg.node_template import load_trackg_node_spec
    from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file as nf_sha
    spec_path = H / "configs/trackg/nodes/gc7rc_etth1.yaml"
    spec = load_trackg_node_spec(spec_path)
    node_dir = H / "nodes/gc7rc_etth1"
    pin = isolation.frozen_file_hashes(node_dir, spec.frozen_paths)
    committed = committed_view(pin)
    master = H / "src/autoresearch/trackg/node_lib/ar_isolated.py"
    pins = {
        "node": spec.name,
        "spec_path": str(spec_path.relative_to(H)),
        "run_budget": {"kind": spec.run_budget.kind, "value": spec.run_budget.value},
        "node_spec_sha256": spec.raw_sha256,
        "spec_raw_sha256": nf_sha(spec_path),
        "committed_pin_sha256": frozen_pin_sha256(committed),
        "deployed_pin_sha256": frozen_pin_sha256(pin),
        "edits_manifest_sha256": nf_sha(node_dir / "representative_edits/manifest.json"),
        "data_manifest_sha256": nf_sha(node_dir / "data/data_manifest.json"),
        "node_ar_isolated_sha256": nf_sha(node_dir / "ar_isolated.py"),
        "master_ar_isolated_sha256": nf_sha(master),
        "frozen_files": committed,
        "data_link": os.readlink(node_dir / "data"),
    }
    pre["pins"] = pins
    for key, expected in EQ.items():
        assert pins[key] == expected, f"STOP: {key} {pins[key]} != accepted {expected}"
    assert pins["run_budget"] == {"kind": "steps", "value": 2000}

    # data: pinned, read-only, outside the repository
    data_root = node_dir / "data"
    assert data_root.is_symlink() and not str(data_root.resolve()).startswith(str(H)), data_root
    manifest = json.loads((data_root / "data_manifest.json").read_text())
    series = data_root / "series.npy"
    raw_csv = data_root / manifest["source"]["csv"]
    pre["data"] = {
        "root": str(data_root.resolve()),
        "root_mode": oct(data_root.resolve().stat().st_mode),
        "manifest_schema": manifest.get("schema"),
        "source_url": manifest["source"]["url"],
        "source_sha256_pinned": manifest["source"]["sha256"],
        "source_sha256_recomputed": sha256_file(raw_csv),
        "source_bytes": raw_csv.stat().st_size,
        "series_sha256_manifest": manifest["files"]["series.npy"]["sha256"],
        "series_sha256_recomputed": sha256_file(series),
        "series_bytes": series.stat().st_size,
        "series_mode": oct(series.stat().st_mode),
        "read_only": all(not p.stat().st_mode & 0o222 for p in (data_root.resolve(), series, raw_csv)),
    }
    assert pre["data"]["source_sha256_recomputed"] == SRC_CSV_SHA, "STOP: pinned source CSV changed"
    assert pre["data"]["series_sha256_recomputed"] == SERIES_SHA, "STOP: pinned series.npy changed"
    assert pre["data"]["source_bytes"] == 2589657
    assert pre["data"]["read_only"], "STOP: data root is writable"
    assert pre["data"]["series_sha256_manifest"] == SERIES_SHA

    # environment freeze (pinned torch312)
    uv = HOME / ".local/bin/uv"
    freeze = run_argv([str(uv), "pip", "freeze", "--python", sys.executable])
    assert freeze.returncode == 0, freeze.stderr[-800:]
    freeze_text = freeze.stdout
    pre["env"] = {
        "freeze_packages": len([ln for ln in freeze_text.splitlines() if "==" in ln]),
        "freeze_sha256": hashlib.sha256(freeze_text.encode()).hexdigest(),
        "freeze_expected_sha256": FREEZE_SHA,
        "uv": run_argv([str(uv), "--version"]).stdout.strip(),
        "hostname": socket.gethostname(),
        "kernel": platform.release(),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "numpy": numpy.__version__,
    }
    assert pre["env"]["freeze_sha256"] == FREEZE_SHA, "STOP: torch312 freeze differs from the accepted freeze"
    (RAW / "torch312.freeze.txt").write_text(freeze_text)
    (RAW / "env.txt").write_text(
        f"=== {pre['utc']}\nhostname: {socket.gethostname()}\nplatform: {platform.platform()}\n"
        f"python: {sys.version} ({sys.executable})\ntorch: {torch.__version__} numpy: {numpy.__version__}\n"
        f"cuda_available: {torch.cuda.is_available()} cuda_device_count: {torch.cuda.device_count()}\n"
        f"CUDA_VISIBLE_DEVICES: {pre['cuda_visible_devices_env']!r}\n"
        f"freeze_sha256: {pre['env']['freeze_sha256']} ({pre['env']['freeze_packages']} packages)\n"
        f"cgroup: {pre['cgroup']} memory.max={pre['memory_max']} memory.swap.max={pre['memory_swap_max']}\n"
        f"affinity: {pre['affinity']}\nptrace_scope: {pre['ptrace_scope']}\n"
        f"systemd: {pre['systemd_version']}\n"
        f"branch: {pre['git']['branch']} head: {pre['git']['head']}\n"
        f"git status: {pre['git']['status_porcelain']}\n"
    )
    (RAW / "pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    (RAW / "data_manifest.json").write_text((data_root / "data_manifest.json").read_text())
    (RAW / "edits_manifest.json").write_text((node_dir / "representative_edits/manifest.json").read_text())
    (RAW / "gc7rc_etth1.yaml").write_text(spec_path.read_text())
    (RAW / "git_head.txt").write_text(f"branch: {pre['git']['branch']}\nhead: {pre['git']['head']}\n"
                                      f"base: {BASE_COMMIT}\n")
    (RAW / "git_status.txt").write_text("\n".join(pre["git"]["status_porcelain"]) + "\n")
    (RAW / "git_diffstat_vs_base.txt").write_text("\n".join(pre["git"]["diff_name_status_vs_base"]) + "\n"
                                                  + pre["git"]["diffstat_vs_base"] + "\n")

    # GPU state and lease: record, assert no GPU is visible to this run
    gpu = run_argv(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu",
                    "--format=csv,noheader"])
    apps = run_argv(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"])
    lease = HOME / "r1_locks/gpu0.lock"
    locks = run_argv(["lslocks"]).stdout if run_argv(["lslocks"]).returncode == 0 else ""
    pre["gpu"] = {
        "nvidia_smi_rc": gpu.returncode,
        "gpus": gpu.stdout.strip().splitlines(),
        "compute_apps": apps.stdout.strip().splitlines() if apps.returncode == 0 else None,
        "lease_lock_file": str(lease) if lease.exists() else None,
        "lease_lock_stat": {"bytes": lease.stat().st_size, "mtime": lease.stat().st_mtime} if lease.exists() else None,
        "lease_held": any("gpu0.lock" in line for line in locks.splitlines()),
    }
    assert pre["cuda_visible_devices_env"] == "", "STOP: CUDA_VISIBLE_DEVICES is not hidden"
    assert torch.cuda.device_count() == 0, "STOP: a GPU is visible to the smoke driver"
    assert pre["gpu"]["lease_held"] is False, "STOP: a GPU lease is held"
    (RAW / "gpu_state_pre.txt").write_text(
        f"utc: {pre['utc']}\nCUDA_VISIBLE_DEVICES: {pre['cuda_visible_devices_env']!r}\n"
        f"torch.cuda.device_count: {torch.cuda.device_count()} cuda_available: {torch.cuda.is_available()}\n"
        f"nvidia-smi query rc={gpu.returncode}:\n{gpu.stdout.strip()}\n"
        f"compute apps:\n{apps.stdout.strip()}\n"
        f"lease gpu0.lock: {pre['gpu']['lease_lock_stat']} held={pre['gpu']['lease_held']}\n"
    )

    assert set(pre["affinity"]) == set(range(16, 32)), f"STOP: driver affinity {pre['affinity']} != 16-31"
    assert pre["cuda_visible_devices_env"] == ""
    assert pre["ar_test_cgroup_parent_env"] == "<unset>", "AR_TEST_CGROUP_PARENT must be set by this driver"
    assert not RUNS.exists(), f"STOP: runs root {RUNS} already exists (one smoke only, no retry)"
    (BASE / "raw").mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True)
    return pre


def run_smoke() -> dict:
    scope = cgroup_dir()
    assert (scope / "cgroup.controllers").is_file() and os.access(scope / "cgroup.procs", os.W_OK), \
        f"STOP: the delegated scope cgroup {scope} is not writable"
    os.environ["AR_TEST_CGROUP_PARENT"] = str(scope)

    subtree = None
    try:
        ctl = scope / "cgroup.subtree_control"
        before = ctl.read_text().strip()
        ctl.write_text("+memory")
        subtree = {"before": before, "after": ctl.read_text().strip()}
    except OSError as exc:
        subtree = {"error": str(exc)}

    from tests.trackg import port_smoke_gpu

    assert "gc7rc_etth1" not in port_smoke_gpu.CPU_ONLY_NODES
    port_smoke_gpu.CPU_ONLY_NODES = frozenset(set(port_smoke_gpu.CPU_ONLY_NODES) | {"gc7rc_etth1"})
    memory_limit = ("systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 "
                    f"(unit {scope.name}; AR_TEST_CGROUP_PARENT={scope})")
    argv = ["--node", "gc7rc_etth1", "--cpus", "16-31", "--memory-limit", memory_limit,
            "--runs-root", str(RUNS), "--provisional-timeout", "900"]

    monitor = Monitor(scope)
    monitor.start()
    started = now()
    t0 = time.monotonic()
    output = ""
    error = None
    rc: int | None = None
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = port_smoke_gpu.main(argv)
        output = buf.getvalue()
    except BaseException as exc:  # the module's checks assert; keep the evidence and report STOP
        error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        if not output:
            output = ""
    finally:
        elapsed = time.monotonic() - t0
        monitor.stop.set()
        monitor.join(timeout=5)
    smoke_peak = read_int(scope / "memory.peak")
    (RAW / "smoke_stdout.txt").write_text(output)
    if error:
        (RAW / "smoke_error.txt").write_text(error)
    print(output, end="")
    print(f"SMOKE_MAIN_RC={rc} elapsed_seconds={elapsed:.3f} driver_utc={started}..{now()}")
    return {"argv": argv, "cgroup_parent": str(scope), "memory_limit": memory_limit,
            "rc": rc, "stdout": output, "error": error, "elapsed_seconds": round(elapsed, 3),
            "started_utc": started, "finished_utc": now(), "scope_memory_peak_bytes": smoke_peak,
            "python3_resolved": shutil.which("python3"), "subtree_control": subtree,
            "monitor": {"peak_memory_bytes": monitor.peak_memory, "peak_anon_bytes": monitor.peak_anon,
                        "samples": monitor.samples}}


def collect_rows() -> list[dict]:
    rows = []
    record_paths = sorted(RUNS.glob("runs_smoke/*/run_record.json")) + sorted(RUNS.glob("runs_edits/*/run_record.json"))
    by_run: dict[str, Path] = {}
    for path in record_paths:
        run_dir = path.parent
        record = json.loads(path.read_text())
        run = run_dir.name
        iso = record.get("isolation") or {}
        diffusion = record.get("diff") or {}
        row = {
            "run": run,
            "run_dir": str(run_dir),
            "executed": record.get("executed"),
            "diff_status": diffusion.get("status"),
            "diff_refusal": diffusion.get("refusal"),
            "outcome": record.get("outcome"),
            "elapsed_seconds_info_only": record.get("elapsed_seconds_info_only"),
            "isolation_effective": iso.get("effective"),
            "isolation_waivers": iso.get("waivers"),
            "isolation_exceptions": iso.get("exceptions"),
            "frozen_files_checked": iso.get("frozen_files_checked"),
            "frozen_files_changed": iso.get("frozen_files_changed"),
            "sealed": record.get("sealed"),
            "determinism_not_forced": (record.get("determinism") or {}).get("not_forced"),
            "determinism_shim_loaded": (record.get("determinism") or {}).get("shim_loaded"),
            "process_killed_with": (record.get("process") or {}).get("killed_with"),
            "timed_out": (record.get("process") or {}).get("timed_out"),
            "run_budget": record.get("run_budget"),
            "frozen_pin_sha256": record.get("frozen_pin_sha256"),
            "cuda_visible_devices": (record.get("environment_applied") or {}).get("CUDA_VISIBLE_DEVICES"),
            "command": record.get("command"),
            "run_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "log_sha256": sha256_file(run_dir / "run.log") if (run_dir / "run.log").is_file() else None,
            "result_channel_sha256": iso.get("result_channel_sha256"),
        }
        rows.append(row)
        by_run[run] = run_dir
    return rows


def postflight(pre: dict, smoke: dict, rows: list[dict]) -> dict:
    post: dict = {"utc": now(), "rows": rows}
    checks: dict[str, bool] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = bool(ok)
        if not ok:
            print(f"CHECK_FAILED {name}: {detail!r}")

    expected = {"runs_smoke": {"s000_baseline", "s001", "s002", "s003"}, "runs_edits": {"E1", "E2", "E3", "E4", "B2"}}
    for family, ids in expected.items():
        fam = RUNS / family
        got = {p.name for p in fam.iterdir() if p.is_dir()} if fam.is_dir() else set()
        check(f"run_set_{family}", got == ids, sorted(got))
    check("all_runs_present", {r["run"] for r in rows} == set(RUN_IDS), sorted(r["run"] for r in rows))
    check("smoke_rc_zero", smoke["rc"] == 0 and smoke["error"] is None, smoke["error"])
    check("checklist_e_passed", "CHECKLIST_E_PASSED gc7rc_etth1" in smoke["stdout"])

    by_run = {r["run"]: r for r in rows}
    executed = [r for r in rows if r["executed"]]
    check("executed_count_8", len(executed) == 8, [r["run"] for r in executed])
    check("frozen_diff_refused_scope_violation",
          by_run.get("s001", {}).get("diff_refusal") == "scope_violation"
          and by_run.get("s001", {}).get("executed") is False, by_run.get("s001"))
    s000 = by_run.get("s000_baseline", {})
    s002 = by_run.get("s002", {})
    s003 = by_run.get("s003", {})
    e1 = by_run.get("E1", {})
    b2 = by_run.get("B2", {})
    check("baseline_ok", (s000.get("outcome") or {}).get("kind") == "ok", s000.get("outcome"))
    check("broken_divergent",
          (s002.get("outcome") or {}).get("kind") == "divergent" and
          (s002.get("outcome") or {}).get("reason") in ("non_finite_loss", "non_finite_metric"),
          s002.get("outcome"))
    for name in ("E1", "E2", "E3", "E4", "B2"):
        check(f"edit_{name}_ok", (by_run.get(name, {}).get("outcome") or {}).get("kind") == "ok",
              by_run.get(name, {}).get("outcome"))

    isolation_bad = [r["run"] for r in executed
                     if not (r["isolation_effective"] is True and r["isolation_waivers"] == {}
                             and r["isolation_exceptions"] == [])]
    check("isolation_effective_all_executed", not isolation_bad, isolation_bad)
    check("isolation_no_frozen_change", all(r["frozen_files_changed"] == [] for r in executed))
    gpu_rows = [r["run"] for r in executed if r["cuda_visible_devices"] != ""]
    check("no_gpu_in_every_run", not gpu_rows, gpu_rows)
    pin_rows = [r["run"] for r in executed if r["frozen_pin_sha256"] != EQ["deployed_pin_sha256"]]
    check("deployed_pin_every_run", not pin_rows, pin_rows)
    det_rows = [r["run"] for r in executed if r["determinism_not_forced"] != ["dataloader_workers"]
                or not r["determinism_shim_loaded"]]
    check("determinism_settings_forced", not det_rows, det_rows)
    killed = [r["run"] for r in rows if (r.get("process_killed_with") is not None) or r.get("timed_out")]
    check("no_timeout_no_kill", not killed, killed)
    budget_bad = [r["run"] for r in executed if r["run_budget"] != {"kind": "steps", "value": 2000}]
    check("full_budget_2000_every_run", not budget_bad, budget_bad)

    baseline_value = (s000.get("outcome") or {}).get("value")
    repeat_value = (b2.get("outcome") or {}).get("value")
    check("determinism_b2_equals_b1", repeat_value == baseline_value,
          {"B1": baseline_value, "B2": repeat_value})
    sealed_b1 = (s000.get("sealed") or {}).get("test_mse")
    sealed_b2 = (b2.get("sealed") or {}).get("test_mse")
    check("determinism_sealed_test_b2_equals_b1", sealed_b2 == sealed_b1,
          {"B1": sealed_b1, "B2": sealed_b2})
    check("determinism_s003_equals_E1",
          (s003.get("outcome") or {}).get("value") == (e1.get("outcome") or {}).get("value") and
          (s003.get("sealed") or {}).get("test_mse") == (e1.get("sealed") or {}).get("test_mse"),
          {"s003": s003.get("outcome"), "E1": e1.get("outcome")})

    # resource accounting: attribute the monitor's peak cgroups to runs
    peaks: dict[str, dict] = {}
    for name in list(smoke["monitor"]["peak_memory_bytes"]):
        for run in RUN_IDS:
            if name.startswith("ar_" + run + "_"):
                peaks[run] = {
                    "peak_memory_bytes": smoke["monitor"]["peak_memory_bytes"].get(name),
                    "peak_anon_bytes": smoke["monitor"]["peak_anon_bytes"].get(name),
                    "cgroup": name,
                }
    post["resources"] = {
        "scope_memory_peak_bytes": smoke["scope_memory_peak_bytes"],
        "python3_resolved": smoke.get("python3_resolved"),
        "subtree_control": smoke.get("subtree_control"),
        "scope_memory_max_bytes": int((cgroup_dir() / "memory.max").read_text().strip()),
        "per_run_peak": peaks,
        "monitor_samples": smoke["monitor"]["samples"],
        "sample_interval": "0.1 s poll of cgroup memory.current/memory.peak/memory.stat:anon",
    }

    du = run_argv(["du", "-sb", str(RUNS)])
    data_du = run_argv(["du", "-sb", str((H / "nodes/gc7rc_etth1/data").resolve())])
    df = run_argv(["df", "-B1", "--output=avail", str(HOME)])
    work = {}
    for family in ("runs_smoke", "runs_edits"):
        for run_dir in sorted((RUNS / family).iterdir()):
            if run_dir.is_dir() and (run_dir / "work").is_dir():
                out = run_argv(["du", "-sb", str(run_dir / "work")])
                work[run_dir.name] = int(out.stdout.split()[0]) if out.returncode == 0 else None
    post["disk"] = {
        "runs_root_bytes": int(du.stdout.split()[0]) if du.returncode == 0 else None,
        "per_run_work_bytes": work,
        "captures_bytes": None,
        "data_root_bytes": int(data_du.stdout.split()[0]) if data_du.returncode == 0 else None,
        "home_avail_bytes_before_probe": None,
        "home_avail_bytes_after": int(df.stdout.strip().splitlines()[-1]) if df.returncode == 0 else None,
    }

    gpu = run_argv(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu",
                    "--format=csv,noheader"])
    apps = run_argv(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"])
    lease = HOME / "r1_locks/gpu0.lock"
    locks = run_argv(["lslocks"]).stdout if run_argv(["lslocks"]).returncode == 0 else ""
    post["gpu"] = {
        "gpus": gpu.stdout.strip().splitlines(),
        "compute_apps": apps.stdout.strip().splitlines() if apps.returncode == 0 else None,
        "lease_lock_stat": {"bytes": lease.stat().st_size, "mtime": lease.stat().st_mtime} if lease.exists() else None,
        "lease_held": any("gpu0.lock" in line for line in locks.splitlines()),
        "cpu_visible_devices": "",
    }
    check("no_gpu_lease_taken", post["gpu"]["lease_held"] is False, post["gpu"]["lease_held"])
    check("lease_lock_untouched",
          pre["gpu"]["lease_lock_stat"] == post["gpu"]["lease_lock_stat"],
          {"before": pre["gpu"]["lease_lock_stat"], "after": post["gpu"]["lease_lock_stat"]})

    status = git("status", "--porcelain").splitlines()
    check("worktree_unchanged", status == pre["git"]["status_porcelain"], status)
    check("pin_unchanged", git("rev-parse", "HEAD") == PIN)
    check("no_new_files_in_repo", not [ln for ln in status if not ln.endswith("nodes/gc7rc_etth1/data")], status)

    post["checks"] = checks
    post["verdict"] = "PASS" if all(checks.values()) else "STOP"
    post["b1_val_mse"] = baseline_value
    post["b2_val_mse"] = repeat_value
    post["b1_sealed_test_mse"] = sealed_b1
    post["b2_sealed_test_mse"] = sealed_b2
    post["smoke"] = {k: v for k, v in smoke.items() if k != "stdout"}
    post["elapsed_seconds_total"] = smoke["elapsed_seconds"]
    return post


def assemble_captures(pre: dict, smoke: dict, post: dict) -> None:
    CAP.mkdir(parents=True, exist_ok=True)
    for name in ("preflight.json", "summary.json", "summary.txt", "commands.txt", "smoke_stdout.txt",
                 "smoke_error.txt", "torch312.freeze.txt", "env.txt", "pins.json", "data_manifest.json",
                 "edits_manifest.json", "gc7rc_etth1.yaml", "git_head.txt", "git_status.txt",
                 "git_diffstat_vs_base.txt", "gpu_state_pre.txt"):
        src = RAW / name
        if src.is_file():
            shutil.copy2(src, CAP / name)
    (RAW / "preflight.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
    (RAW / "summary.json").write_text(json.dumps(post, indent=2, sort_keys=True) + "\n")
    lines = ["U2 CPU-only census smoke — gc7rc_etth1 (ETTh1), TASL-2, no GPU, no GPU lease",
             f"utc: {post['utc']}", f"verdict: {post['verdict']}",
             f"smoke_main_rc: {smoke['rc']}  elapsed_s: {smoke['elapsed_seconds']}",
             f"B1 val_mse: {post['b1_val_mse']}  B2 val_mse: {post['b2_val_mse']}",
             f"B1 sealed test_mse: {post['b1_sealed_test_mse']}  B2 sealed test_mse: {post['b2_sealed_test_mse']}",
             f"scope memory.peak: {post['resources']['scope_memory_peak_bytes']} bytes  "
             f"scope memory.max: {post['resources']['scope_memory_max_bytes']} bytes",
             f"runs_root: {RUNS}  bytes: {post['disk']['runs_root_bytes']}",
             "", "run executed diff_status kind value val_mse sealed_test_mse elapsed_s "
                 "iso_effective iso_waivers iso_exceptions det_not_forced killed"]
    for row in post["rows"]:
        out = row["outcome"] or {}
        sealed = (row["sealed"] or {}).get("test_mse")
        lines.append(f"{row['run']} {row['executed']} {row['diff_status']} {out.get('kind')} "
                     f"{out.get('value')} {out.get('value')} {sealed} {row['elapsed_seconds_info_only']} "
                     f"{row['isolation_effective']} {row['isolation_waivers']} "
                     f"{row['isolation_exceptions']} {row['determinism_not_forced']} {row['process_killed_with']}")
    lines.append("")
    lines.append("checks: " + json.dumps(post["checks"], sort_keys=True))
    summary_text = "\n".join(lines) + "\n"
    (RAW / "summary.txt").write_text(summary_text)
    (CAP / "preflight.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
    (CAP / "summary.json").write_text(json.dumps(post, indent=2, sort_keys=True) + "\n")
    (CAP / "summary.txt").write_text(summary_text)
    for family in ("runs_smoke", "runs_edits"):
        for run_dir in sorted((RUNS / family).iterdir()):
            if not run_dir.is_dir():
                continue
            run = run_dir.name
            (CAP / "run_records").mkdir(exist_ok=True)
            (CAP / "run_logs").mkdir(exist_ok=True)
            (CAP / "result_channels").mkdir(exist_ok=True)
            shutil.copy2(run_dir / "run_record.json", CAP / "run_records" / f"{run}.json")
            if (run_dir / "run.log").is_file():
                shutil.copy2(run_dir / "run.log", CAP / "run_logs" / f"{run}.log")
            if (run_dir / "result_channel.txt").is_file():
                shutil.copy2(run_dir / "result_channel.txt", CAP / "result_channels" / f"{run}.txt")
    # the driver itself, for auditability
    shutil.copy2(Path(__file__).resolve(), CAP / "run_u2_smoke.py")
    post["disk"]["captures_bytes"] = int(run_argv(["du", "-sb", str(CAP)]).stdout.split()[0])
    post["disk"]["script_bytes"] = os.path.getsize(Path(__file__).resolve())
    (CAP / "summary.json").write_text(json.dumps(post, indent=2, sort_keys=True) + "\n")
    # SHA256SUMS over every capture except itself
    rows = []
    for path in sorted(CAP.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rows.append(f"{sha256_file(path)}  {path.relative_to(CAP)}")
    (CAP / "SHA256SUMS").write_text("\n".join(rows) + "\n")
    verify = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=CAP, capture_output=True, text=True)
    print(f"SHA256SUMS: {len(rows)} files; verify rc={verify.returncode} "
          f"sha256sums_sha256={sha256_file(CAP / 'SHA256SUMS')}")
    if verify.returncode != 0:
        print(verify.stdout[-1500:], verify.stderr[-1500:])


def main() -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"U2 CPU census smoke driver start {now()}")
    pre = preflight()
    print(f"preflight PASS {now()}: head={pre['git']['head']} branch={pre['git']['branch']} "
          f"pins={pre['pins']['committed_pin_sha256'][:12]} data={pre['data']['series_sha256_recomputed'][:12]} "
          f"env_freeze={pre['env']['freeze_sha256'][:12]} gpu_visible={pre['torch']['cuda_device_count']} "
          f"cgroup={pre['cgroup']}")
    smoke = run_smoke()
    rows = collect_rows()
    post = postflight(pre, smoke, rows)
    assemble_captures(pre, smoke, post)
    print(post["verdict"])
    print(f"B1_val_mse={post['b1_val_mse']} B2_val_mse={post['b2_val_mse']} "
          f"B1_sealed_test_mse={post['b1_sealed_test_mse']} B2_sealed_test_mse={post['b2_sealed_test_mse']}")
    print(f"U2_CPU_CENSUS_SMOKE_{post['verdict']} node=gc7rc_etth1")
    return 0 if post["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
