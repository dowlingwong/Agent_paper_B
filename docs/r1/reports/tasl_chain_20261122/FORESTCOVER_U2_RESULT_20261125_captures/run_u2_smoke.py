#!/usr/bin/env python3
"""U2 CPU-only census smoke driver for the reviewed Track G kit ``gc7rc_forestcover`` (1GC-7RC Forest Cover).

Ran on TASL-2 with no GPU and no GPU lease, inside a ``systemd-run --user --scope`` delegated scope
(``Delegate=yes``, ``MemoryMax=8G``, ``MemorySwapMax=0``), affinity **8-11** (P-cores), ``CUDA_VISIBLE_DEVICES=""``,
``PYTHONDONTWRITEBYTECODE=1``, the pinned env's ``bin`` first on ``PATH`` and the absolute pinned interpreter.

It executes the kit's standard stub-manager census smoke (``tests/trackg/port_smoke_gpu.py``, checklist E) at the
node's full 8,000-step budget on the real data.  The reviewed module's CLI refuses a run without ``--gpu-uuid`` for
every node that is not in ``CPU_ONLY_NODES``; ``gc7rc_forestcover`` is a GPU-capable torch node and is not in that
set, so this driver overrides **only** that guard in memory (``port_smoke_gpu.CPU_ONLY_NODES``) and calls the
module's own ``main()`` with the kit's documented flags (``--cpus``, ``--memory-limit``, ``--runs-root``,
``--provisional-timeout``).  No repository file is changed; the run set, the run code, the full budget and the
checks are the reviewed module's own.

Modes:
  * ``U2_PREFLIGHT_ONLY=1`` — run the preflight gate only (pins/data/env/git/GPU/scope/CPU answers written to
    ``BASE/preflight/``), do not create ``runs/`` and do not launch any run;
  * default — preflight, the single smoke launch, postflight checks, captures and ``SHA256SUMS``.

Writes preflight/pins/data/env captures, every ``run_record.json``, run logs, result channels, a resource
summary (peak cgroup memory, disk) and ``SHA256SUMS`` into ``captures/``.  ENGINEERING_ONLY: no GPU, no census
measurement beyond this smoke, no evidence/G.1b file, no deletion, no push.
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
H = HOME / "r1_trackg_20261125/harness_forestcover"
BASE = Path(os.environ.get("U2_BASE") or
            (HOME / "r1_engineering/forestcover_port_20261125/u2_census_smoke_20261125U2"))
RAW = BASE / "raw"
RUNS = BASE / "runs"
CAP = BASE / "captures"
PRE = BASE / "preflight"
NODE = "gc7rc_forestcover"
PIN = "85851664679d10889c5af406843c4a3fc38f7a49"
BASE_COMMIT = "c025f89aeafc2199bf3487b4bcaa16678273c702"
BRANCH = "mac-trackg-forestcover-20261125"
CPU_LIST = (8, 9, 10, 11)
EQ = {
    "node_spec_sha256": "ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb",
    "spec_raw_sha256": "edd1a076aab8b2cc1f45192860b3555a844400c211581888b9edbcc4e5104e02",
    "committed_pin_sha256": "78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33",
    "deployed_pin_sha256": "ec5c779161be56665bf7ae6d45adee140fde6e47cb46cb08bd583f8a0d4d5a5f",
    "edits_manifest_sha256": "0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed",
    "data_manifest_sha256": "2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d",
    "node_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
    "master_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
}
FREEZE_SHA = "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"
X_SHA = "3c9503390b527ce0cc5d1713772db126e754d12f312f3581b3f15fe6f834bfa7"
X_BYTES = 125498720
Y_SHA = "35e11486262e974a249c66474dc624fe29d88f690d9819612239fb4dd34768a7"
Y_BYTES = 581140
ZIP_SHA = "89a975c2457cd48e824238ae43c5a3cb762e42c4b4078d9b44a4514055105f6d"
ZIP_BYTES = 11251206
MEMBER_SHA = "614360d0257557dd1792834a85a1cdebfadc3c4f30b011d56afee7ffb5b15771"
MEMBER_BYTES = 11240707
RUN_BUDGET = {"kind": "steps", "value": 8000}
RUN_IDS = ["s000_baseline", "s001", "s002", "s003", "E1", "E2", "E3", "E4", "B2"]
CLASS_COUNTS = {"class_1": 211840, "class_2": 283301, "class_3": 35754, "class_4": 2747,
                "class_5": 9493, "class_6": 17367, "class_7": 20510}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_argv(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True)


def git(*args: str) -> str:
    res = run_argv(["git", "-C", str(H), *args])
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
    """Poll the smoke scope's per-run child cgroups for memory (scope peak is the authoritative number)."""

    def __init__(self, scope: Path):
        super().__init__(daemon=True)
        self.scope = scope
        self.stop = threading.Event()
        self.peak_memory: dict[str, int] = {}
        self.peak_anon: dict[str, int] = {}
        self.samples = 0

    @staticmethod
    def _cgroup_memory(path: Path) -> tuple[int | None, int | None]:
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
        mem = max(current or 0, peak or 0) if current is not None or peak is not None else None
        return mem, anon

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


def preflight(out: Path) -> dict:
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
                         "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE"),
                         "U2_BASE": os.environ.get("U2_BASE"), "AR_TRACKG_DATA_ROOT":
                         os.environ.get("AR_TRACKG_DATA_ROOT")}
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
    assert pre["git"]["branch"] == BRANCH, pre["git"]["branch"]
    assert pre["git"]["status_porcelain"] in ([], ["?? nodes/gc7rc_forestcover/data"]), \
        f"STOP: worktree not clean at the pin: {pre['git']['status_porcelain']}"

    # pins, recomputed from the committed tree with the kit's own frozen-pin helpers
    from autoresearch.trackg import isolation
    from autoresearch.trackg.node_template import load_trackg_node_spec
    from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file as nf_sha
    spec_path = H / "configs/trackg/nodes/gc7rc_forestcover.yaml"
    spec = load_trackg_node_spec(spec_path)
    node_dir = H / "nodes/gc7rc_forestcover"
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
        "frozen_file_count_with_data_link": len(pin),
        "data_link": os.readlink(node_dir / "data"),
    }
    pre["pins"] = pins
    for key, expected in EQ.items():
        assert pins[key] == expected, f"STOP: {key} {pins[key]} != accepted {expected}"
    assert pins["run_budget"] == RUN_BUDGET

    # data: pinned, read-only, outside the repository
    data_root = node_dir / "data"
    resolved = data_root.resolve()
    assert data_root.is_symlink() and not str(resolved).startswith(str(H)), data_root
    manifest_path = resolved / "data_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    x_path, y_path = resolved / "X.npy", resolved / "y.npy"
    zip_path = resolved / "raw" / "covertype.zip"
    pre["data"] = {
        "root": str(resolved),
        "root_mode": oct(resolved.stat().st_mode),
        "manifest_schema": manifest.get("schema"),
        "manifest_sha256": sha256_file(manifest_path),
        "node": manifest.get("node"),
        "setup_only": manifest.get("setup_only"),
        "files": {
            "X.npy": {"sha256_manifest": manifest["files"]["X.npy"]["sha256"],
                      "bytes_manifest": manifest["files"]["X.npy"]["bytes"],
                      "sha256_recomputed": sha256_file(x_path),
                      "bytes": x_path.stat().st_size,
                      "mode": oct(x_path.stat().st_mode)},
            "y.npy": {"sha256_manifest": manifest["files"]["y.npy"]["sha256"],
                      "bytes_manifest": manifest["files"]["y.npy"]["bytes"],
                      "sha256_recomputed": sha256_file(y_path),
                      "bytes": y_path.stat().st_size,
                      "mode": oct(y_path.stat().st_mode)},
        },
        "source": {
            "url": manifest["source"]["url"],
            "dataset": manifest["source"]["dataset"],
            "doi": manifest["source"]["doi"],
            "license": manifest["source"]["license"],
            "zip_sha256_pinned": manifest["source"]["zip_sha256"],
            "zip_bytes_pinned": manifest["source"]["zip_bytes"],
            "zip_sha256_recomputed": sha256_file(zip_path),
            "zip_bytes": zip_path.stat().st_size,
            "member": manifest["source"]["member"],
            "member_sha256_pinned": manifest["source"]["member_sha256"],
            "member_bytes_pinned": manifest["source"]["member_bytes"],
        },
        "rows": manifest["source"]["rows"],
        "features": manifest["source"]["features"],
        "classes": manifest["source"]["classes"],
        "class_counts": manifest["source"]["class_counts"],
        "read_only": all(not p.stat().st_mode & 0o222
                         for p in (resolved, x_path, y_path, manifest_path, zip_path, resolved / "raw")),
    }
    assert pre["data"]["manifest_sha256"] == EQ["data_manifest_sha256"], "STOP: data manifest changed"
    assert pre["data"]["files"]["X.npy"]["sha256_recomputed"] == X_SHA, "STOP: pinned X.npy changed"
    assert pre["data"]["files"]["y.npy"]["sha256_recomputed"] == Y_SHA, "STOP: pinned y.npy changed"
    assert pre["data"]["files"]["X.npy"]["bytes"] == X_BYTES
    assert pre["data"]["files"]["y.npy"]["bytes"] == Y_BYTES
    assert pre["data"]["source"]["zip_sha256_recomputed"] == ZIP_SHA, "STOP: pinned source zip changed"
    assert pre["data"]["source"]["zip_bytes"] == ZIP_BYTES
    assert pre["data"]["source"]["member_sha256_pinned"] == MEMBER_SHA
    assert pre["data"]["source"]["member_bytes_pinned"] == MEMBER_BYTES
    assert pre["data"]["read_only"], "STOP: data root is writable"
    assert (pre["data"]["rows"], pre["data"]["features"], pre["data"]["classes"]) == (581012, 54, 7)
    assert pre["data"]["class_counts"] == CLASS_COUNTS
    assert sum(pre["data"]["class_counts"].values()) == 581012

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
    (out / "torch312.freeze.txt").write_text(freeze_text)
    (out / "env.txt").write_text(
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
    (out / "pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    (out / "data_manifest.json").write_text(manifest_path.read_text())
    (out / "edits_manifest.json").write_text((node_dir / "representative_edits/manifest.json").read_text())
    (out / "gc7rc_forestcover.yaml").write_text(spec_path.read_text())
    (out / "git_head.txt").write_text(f"branch: {pre['git']['branch']}\nhead: {pre['git']['head']}\n"
                                      f"base: {BASE_COMMIT}\n")
    (out / "git_status.txt").write_text("\n".join(pre["git"]["status_porcelain"]) + "\n")
    (out / "git_diffstat_vs_base.txt").write_text("\n".join(pre["git"]["diff_name_status_vs_base"]) + "\n"
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
    (out / "gpu_state_pre.txt").write_text(
        f"utc: {pre['utc']}\nCUDA_VISIBLE_DEVICES: {pre['cuda_visible_devices_env']!r}\n"
        f"torch.cuda.device_count: {torch.cuda.device_count()} cuda_available: {torch.cuda.is_available()}\n"
        f"nvidia-smi query rc={gpu.returncode}:\n{gpu.stdout.strip()}\n"
        f"compute apps:\n{apps.stdout.strip()}\n"
        f"lease gpu0.lock: {pre['gpu']['lease_lock_stat']} held={pre['gpu']['lease_held']}\n"
    )

    assert pre["affinity"] == list(CPU_LIST), f"STOP: driver affinity {pre['affinity']} != {list(CPU_LIST)}"
    assert pre["cuda_visible_devices_env"] == ""
    assert pre["ar_test_cgroup_parent_env"] == "<unset>", "AR_TEST_CGROUP_PARENT must be set by this driver"
    assert pre["py_dont_write_bytecode"] == "1", "STOP: PYTHONDONTWRITEBYTECODE is not 1"
    assert pre["memory_max"] == str(8 * 1024 ** 3), f"STOP: memory.max {pre['memory_max']} != 8 GiB"
    assert pre["memory_swap_max"] == "0", f"STOP: memory.swap.max {pre['memory_swap_max']} != 0"
    assert not RUNS.exists(), f"STOP: runs root {RUNS} already exists (one smoke only, no retry)"
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

    assert NODE not in port_smoke_gpu.CPU_ONLY_NODES
    port_smoke_gpu.CPU_ONLY_NODES = frozenset(set(port_smoke_gpu.CPU_ONLY_NODES) | {NODE})
    memory_limit = ("systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 "
                    f"(unit {scope.name}; AR_TEST_CGROUP_PARENT={scope})")
    argv = ["--node", NODE, "--cpus", "8-11", "--memory-limit", memory_limit,
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
            "decision": None,
            "diff_status": diffusion.get("status"),
            "diff_refusal": diffusion.get("refusal"),
            "outcome": record.get("outcome"),
            "sealed": record.get("sealed"),
            "value": (record.get("outcome") or {}).get("value"),
            "test_value": (record.get("sealed") or {}).get("test_accuracy"),
            "elapsed_seconds_info_only": record.get("elapsed_seconds_info_only"),
            "isolation_effective": iso.get("effective"),
            "isolation_waivers": iso.get("waivers"),
            "isolation_exceptions": iso.get("exceptions"),
            "frozen_files_checked": iso.get("frozen_files_checked"),
            "frozen_files_changed": iso.get("frozen_files_changed"),
            "iso_cgroup_path": (iso.get("cgroup") or {}).get("path"),
            "cgroup_removed": (iso.get("cgroup") or {}).get("removed"),
            "result_channel_sha256": iso.get("result_channel_sha256"),
            "determinism_not_forced": (record.get("determinism") or {}).get("not_forced"),
            "determinism_shim_loaded": (record.get("determinism") or {}).get("shim_loaded"),
            "process_killed_with": (record.get("process") or {}).get("killed_with"),
            "timed_out": (record.get("process") or {}).get("timed_out"),
            "run_budget": record.get("run_budget"),
            "frozen_pin_sha256": record.get("frozen_pin_sha256"),
            "node_spec_sha256": record.get("node_spec_sha256"),
            "cuda_visible_devices": (record.get("environment_applied") or {}).get("CUDA_VISIBLE_DEVICES"),
            "command": record.get("command"),
            "schema": record.get("schema"),
            "run_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "log_sha256": sha256_file(run_dir / "run.log") if (run_dir / "run.log").is_file() else None,
        }
        rows.append(row)
    return rows


def postflight(pre: dict, smoke: dict, rows: list[dict]) -> dict:
    post: dict = {"utc": now(), "rows": rows}
    checks: dict[str, bool] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = bool(ok)
        if not ok:
            print(f"CHECK_FAILED {name}: {detail!r}")

    expected = {"runs_smoke": {"s000_baseline", "s001", "s002", "s003"},
                "runs_edits": {"E1", "E2", "E3", "E4", "B2"}}
    for family, ids in expected.items():
        fam = RUNS / family
        got = {p.name for p in fam.iterdir() if p.is_dir()} if fam.is_dir() else set()
        check(f"run_set_{family}", got == ids, sorted(got))
    check("all_runs_present", {r["run"] for r in rows} == set(RUN_IDS), sorted(r["run"] for r in rows))
    check("smoke_rc_zero", smoke["rc"] == 0 and smoke["error"] is None, smoke["error"])
    check("checklist_e_passed", "CHECKLIST_E_PASSED gc7rc_forestcover" in smoke["stdout"])

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
    check("frozen_files_checked_16", all(r["frozen_files_checked"] == 16 for r in executed),
          {r["run"]: r["frozen_files_checked"] for r in executed})
    gpu_rows = [r["run"] for r in executed if r["cuda_visible_devices"] != ""]
    check("no_gpu_in_every_run", not gpu_rows, gpu_rows)
    pin_rows = [r["run"] for r in executed if r["frozen_pin_sha256"] != EQ["deployed_pin_sha256"]]
    check("deployed_pin_every_run", not pin_rows, pin_rows)
    spec_rows = [r["run"] for r in executed if r["node_spec_sha256"] != EQ["node_spec_sha256"]]
    check("node_spec_every_run", not spec_rows, spec_rows)
    det_rows = [r["run"] for r in executed if r["determinism_not_forced"] != ["dataloader_workers"]
                or not r["determinism_shim_loaded"]]
    check("determinism_settings_forced", not det_rows, det_rows)
    killed = [r["run"] for r in rows if (r.get("process_killed_with") is not None) or r.get("timed_out")]
    check("no_timeout_no_kill", not killed, killed)
    budget_bad = [r["run"] for r in executed if r["run_budget"] != RUN_BUDGET]
    check("full_budget_8000_every_run", not budget_bad, budget_bad)

    baseline_value = (s000.get("outcome") or {}).get("value")
    repeat_value = (b2.get("outcome") or {}).get("value")
    check("determinism_b2_equals_b1", repeat_value == baseline_value,
          {"B1": baseline_value, "B2": repeat_value})
    sealed_b1 = (s000.get("sealed") or {}).get("test_accuracy")
    sealed_b2 = (b2.get("sealed") or {}).get("test_accuracy")
    check("determinism_sealed_test_b2_equals_b1", sealed_b2 == sealed_b1,
          {"B1": sealed_b1, "B2": sealed_b2})
    check("determinism_s003_equals_E1",
          (s003.get("outcome") or {}).get("value") == (e1.get("outcome") or {}).get("value") and
          (s003.get("sealed") or {}).get("test_accuracy") == (e1.get("sealed") or {}).get("test_accuracy"),
          {"s003": s003.get("outcome"), "E1": e1.get("outcome")})
    # B2/E1-style run reproducibility also through the log/result-channel hashes
    check("determinism_b2_log_matches_b1",
          s000.get("log_sha256") == b2.get("log_sha256") and
          s000.get("result_channel_sha256") == b2.get("result_channel_sha256"),
          {"B1_log": s000.get("log_sha256"), "B2_log": b2.get("log_sha256")})
    check("determinism_s003_log_matches_E1",
          s003.get("log_sha256") == e1.get("log_sha256") and
          s003.get("result_channel_sha256") == e1.get("result_channel_sha256"),
          {"s003_log": s003.get("log_sha256"), "E1_log": e1.get("log_sha256")})

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
        "scope_memory_swap_max_bytes": int((cgroup_dir() / "memory.swap.max").read_text().strip()),
        "per_run_peak": peaks,
        "monitor_samples": smoke["monitor"]["samples"],
        "sample_interval": "0.1 s poll of cgroup memory.current/memory.peak/memory.stat:anon",
    }

    du = run_argv(["du", "-sb", str(RUNS)])
    data_du = run_argv(["du", "-sb", str((H / "nodes/gc7rc_forestcover/data").resolve())])
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
    check("no_new_files_in_repo", not [ln for ln in status if not ln.endswith("nodes/gc7rc_forestcover/data")],
          status)

    post["checks"] = checks
    post["verdict"] = "PASS" if all(checks.values()) else "STOP"
    post["b1_val_accuracy"] = baseline_value
    post["b2_val_accuracy"] = repeat_value
    post["b1_sealed_test_accuracy"] = sealed_b1
    post["b2_sealed_test_accuracy"] = sealed_b2
    post["smoke"] = {k: v for k, v in smoke.items() if k != "stdout"}
    post["elapsed_seconds_total"] = smoke["elapsed_seconds"]
    return post


def assemble_captures(pre: dict, smoke: dict, post: dict) -> None:
    CAP.mkdir(parents=True, exist_ok=True)
    (RAW / "preflight.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
    (RAW / "summary.json").write_text(json.dumps(post, indent=2, sort_keys=True) + "\n")
    lines = ["U2 CPU-only census smoke — gc7rc_forestcover (1GC-7RC Forest Cover), TASL-2, no GPU, no GPU lease",
             f"utc: {post['utc']}", f"verdict: {post['verdict']}",
             f"smoke_main_rc: {smoke['rc']}  elapsed_s: {smoke['elapsed_seconds']}",
             f"B1 val_accuracy: {post['b1_val_accuracy']}  B2 val_accuracy: {post['b2_val_accuracy']}",
             f"B1 sealed test_accuracy: {post['b1_sealed_test_accuracy']}  "
             f"B2 sealed test_accuracy: {post['b2_sealed_test_accuracy']}",
             f"scope memory.peak: {post['resources']['scope_memory_peak_bytes']} bytes  "
             f"scope memory.max: {post['resources']['scope_memory_max_bytes']} bytes",
             f"runs_root: {RUNS}  bytes: {post['disk']['runs_root_bytes']}",
             "",
             "run executed diff_status kind value val_accuracy sealed_test_accuracy elapsed_s "
             "iso_effective iso_waivers iso_exceptions det_not_forced killed"]
    for row in post["rows"]:
        out = row["outcome"] or {}
        lines.append(f"{row['run']} {row['executed']} {row['diff_status']} {out.get('kind')} "
                     f"{out.get('value')} {out.get('value')} {(row.get('sealed') or {}).get('test_accuracy')} "
                     f"{row['elapsed_seconds_info_only']} {row['isolation_effective']} "
                     f"{row['isolation_waivers']} {row['isolation_exceptions']} "
                     f"{row['determinism_not_forced']} {row['process_killed_with']}")
    lines.append("")
    lines.append("checks: " + json.dumps(post["checks"], sort_keys=True))
    summary_text = "\n".join(lines) + "\n"
    (RAW / "summary.txt").write_text(summary_text)
    for name in ("preflight.json", "summary.json", "summary.txt", "torch312.freeze.txt", "env.txt",
                 "pins.json", "data_manifest.json", "edits_manifest.json", "gc7rc_forestcover.yaml",
                 "git_head.txt", "git_status.txt", "git_diffstat_vs_base.txt", "gpu_state_pre.txt",
                 "smoke_stdout.txt", "smoke_error.txt"):
        src = RAW / name
        if src.is_file():
            shutil.copy2(src, CAP / name)
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
    ledger = RUNS / "runs_smoke" / "smoke_ledger.jsonl"
    if ledger.is_file():
        shutil.copy2(ledger, CAP / "smoke_ledger.jsonl")
    # the driver itself, for auditability
    shutil.copy2(Path(__file__).resolve(), CAP / "run_u2_smoke.py")
    # preflight gate evidence, if it exists
    gate = PRE
    if gate.is_dir() and any(gate.iterdir()):
        (CAP / "preflight_gate").mkdir(exist_ok=True)
        for name in ("console_preflight.log", "preflight.json", "env.txt", "pins.json", "git_head.txt",
                     "git_status.txt", "gpu_state_pre.txt", "torch312.freeze.txt"):
            src = gate / name
            if src.is_file():
                shutil.copy2(src, CAP / "preflight_gate" / name)
    # launch console, if it exists (written by the launcher)
    for name in ("console_smoke.log",):
        src = BASE / name
        if src.is_file():
            shutil.copy2(src, CAP / name)
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
    preflight_only = os.environ.get("U2_PREFLIGHT_ONLY") == "1"
    out = PRE if preflight_only else RAW
    out.mkdir(parents=True, exist_ok=True)
    print(f"U2 CPU census smoke driver start {now()} mode={'preflight-only' if preflight_only else 'smoke'}")
    pre = preflight(out)
    if preflight_only:
        (PRE / "preflight.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
        print(f"PREFLIGHT_PASS {now()}: head={pre['git']['head']} branch={pre['git']['branch']} "
              f"committed_pin={pre['pins']['committed_pin_sha256']} "
              f"deployed_pin={pre['pins']['deployed_pin_sha256']} "
              f"spec={pre['pins']['node_spec_sha256']} "
              f"data_manifest={pre['data']['manifest_sha256']} X={pre['data']['files']['X.npy']['sha256_recomputed']} "
              f"env_freeze={pre['env']['freeze_sha256']} gpu_visible={pre['torch']['cuda_device_count']} "
              f"affinity={pre['affinity']} cgroup={pre['cgroup']} "
              f"memory.max={pre['memory_max']} swap.max={pre['memory_swap_max']}")
        return 0
    print(f"preflight PASS {now()}: head={pre['git']['head']} branch={pre['git']['branch']} "
          f"pins={pre['pins']['committed_pin_sha256'][:12]} data={pre['data']['manifest_sha256'][:12]} "
          f"env_freeze={pre['env']['freeze_sha256'][:12]} gpu_visible={pre['torch']['cuda_device_count']} "
          f"affinity={pre['affinity']} cgroup={pre['cgroup']}")
    smoke = run_smoke()
    rows = collect_rows()
    post = postflight(pre, smoke, rows)
    assemble_captures(pre, smoke, post)
    print(post["verdict"])
    print(f"B1_val_accuracy={post['b1_val_accuracy']} B2_val_accuracy={post['b2_val_accuracy']} "
          f"B1_sealed_test_accuracy={post['b1_sealed_test_accuracy']} "
          f"B2_sealed_test_accuracy={post['b2_sealed_test_accuracy']}")
    print(f"U2_CPU_CENSUS_SMOKE_{post['verdict']} node=gc7rc_forestcover")
    return 0 if post["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
