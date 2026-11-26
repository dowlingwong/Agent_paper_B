"""R1-TRACKG-AR-U2-TASL2 condition 6: GPU smoke with the worker sandbox on (effective true, no exceptions).

Uses the unit's own ``tests/trackg/isolated_fixture`` (frozen parent + frozen worker + editable train.py).  A
temporary copy of the node is made whose **editable** ``train.py`` allocates and synchronises a small CUDA
tensor with torch inside the sandboxed worker (PID 1 of its own user/mount/PID/net/cgroup namespaces); the
*frozen* parent computes the metric from the worker's answers and writes ``val_accuracy`` as usual.

The node does **not** set ``shared_dev_shm`` and no waiver is given: the record must show
``effective: true``, ``waivers {}`` and ``exceptions []``.  The GPU report is written by the worker into its
working copy (``<run_dir>/work/gpu_report.json``) and is also printed to the run log as ``GPU_PROBE {...}``.

If ``torch.cuda.is_available()`` is false inside the sandbox, the worker additionally records deep diagnostics
(device-node open, /proc and /sys facts, libcuda cuInit, NVML init, nvidia-smi, torch.cuda.init traceback) so a
host/driver limitation can be told apart from a sandbox configuration problem.

Run inside a delegated scope (``AR_TEST_CGROUP_PARENT`` set) holding the host's documented exclusive GPU lease
(``flock ~/r1_locks/gpu0.lock``, taken by ``run_gpu_smoke.sh``); no compute app may run before or after.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/dowling/r1_trackp/harness_cond7a_20261121")
BASE = Path("/home/dowling/r1_engineering/tasl2_hostcheck_20261121")
EXPECTED_GPU_UUID = "GPU-4d623e76-7587-ee15-a633-46f60d220d94"

TRAIN_PY = r'''"""Editable trainer for the TASL-2 GPU smoke: allocates and synchronises a CUDA tensor inside the sandbox."""
import json
import os
import sys

import numpy as np

MODE = "gpu"


def _read(path):
    try:
        with open(path, "r", errors="replace") as handle:
            return handle.read()[:4000]
    except OSError as error:
        return "<unreadable: %r>" % (error,)


def _env_subset():
    keys = ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "PATH", "LD_LIBRARY_PATH",
            "HOME", "TMPDIR", "AR_RESULT_SOCKET", "RUST_LOG")
    return {k: os.environ.get(k) for k in keys}


def _diag():
    diag = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(), "cwd": os.getcwd(),
            "env": _env_subset(),
            "dev_nodes": {}, "dev_listing": [], "dev_caps": [],
            "proc_driver_nvidia_version": None, "proc_self_status_cap": {},
            "uid_map": _read("/proc/self/uid_map"), "gid_map": _read("/proc/self/gid_map"),
            "sys_module_nvidia_version": _read("/sys/module/nvidia/version"),
            "sys_devices": _read("/sys/class/misc/nvidia/uevent")}
    for name in ("nvidiactl", "nvidia0", "nvidia-uvm", "nvidia-uvm-tools", "nvidia-modeset"):
        path = "/dev/" + name
        entry = {"exists": os.path.exists(path)}
        try:
            st = os.stat(path)
            entry.update({"mode": oct(st.st_mode & 0o777), "uid": st.st_uid, "gid": st.st_gid,
                          "rdev": [os.major(st.st_rdev), os.minor(st.st_rdev)]})
        except OSError as error:
            entry["stat_error"] = repr(error)
        try:
            fd = os.open(path, os.O_RDWR | os.O_CLOEXEC)
            entry["open"] = "open_ok"
            os.close(fd)
        except OSError as error:
            entry["open"] = repr(error)
        diag["dev_nodes"][name] = entry
    try:
        diag["dev_listing"] = sorted(os.listdir("/dev"))
    except OSError as error:
        diag["dev_listing"] = repr(error)
    try:
        diag["dev_caps"] = sorted(os.listdir("/dev/nvidia-caps"))
    except OSError as error:
        diag["dev_caps"] = repr(error)
    if os.path.exists("/proc/driver/nvidia/version"):
        diag["proc_driver_nvidia_version"] = _read("/proc/driver/nvidia/version")
    status = _read("/proc/self/status")
    for line in status.splitlines():
        if line.split(":")[0] in ("CapEff", "CapBnd", "CapPrm", "NoNewPrivs", "Seccomp"):
            diag["proc_self_status_cap"][line.split(":")[0]] = line.split(":", 1)[1].strip()
    try:
        import ctypes
        libcuda = ctypes.CDLL("libcuda.so.1")
        rc = libcuda.cuInit(0)
        diag["cuInit_rc"] = rc
        if rc != 0:
            err = ctypes.c_char_p()
            libcuda.cuGetErrorString(rc, ctypes.byref(err))
            diag["cuInit_error"] = err.value.decode(errors="replace") if err.value else None
    except Exception as error:  # noqa: BLE001
        diag["libcuda"] = repr(error)
    try:
        import ctypes
        nvml = ctypes.CDLL("libnvidia-ml.so.1")
        rc = nvml.nvmlInit_v2()
        diag["nvmlInit_rc"] = rc
        if rc == 0:
            count = ctypes.c_uint(0)
            rc2 = nvml.nvmlDeviceGetCount_v2(ctypes.byref(count))
            diag["nvml_device_count"] = {"rc": rc2, "count": int(count.value)}
    except Exception as error:  # noqa: BLE001
        diag["nvml"] = repr(error)
    try:
        diag["nvidia_smi"] = {"cmd": "nvidia-smi -L"}
        proc = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=30)
        diag["nvidia_smi"].update({"rc": proc.returncode, "stdout": proc.stdout[-4000:],
                                   "stderr": proc.stderr[-4000:]})
    except Exception as error:  # noqa: BLE001
        diag["nvidia_smi"] = repr(error)
    try:
        import torch
        diag["torch_version"] = torch.__version__
        diag["torch_cuda_version"] = torch.version.cuda
        diag["torch_cuda_is_available"] = bool(torch.cuda.is_available())
        diag["torch_cuda_device_count"] = int(torch.cuda.device_count())
        try:
            torch.cuda.init()
            diag["torch_cuda_init"] = "ok"
            diag["torch_cuda_initialized"] = bool(torch.cuda.is_initialized())
        except Exception as error:  # noqa: BLE001
            import traceback
            diag["torch_cuda_init"] = repr(error)
            diag["torch_cuda_init_traceback"] = traceback.format_exc()[-4000:]
        if diag.get("torch_cuda_initialized"):
            a = torch.ones((8, 8), dtype=torch.float32, device="cuda:0")
            b = a @ a
            torch.cuda.synchronize()
            diag["torch_matmul_value"] = float(b[0, 0].item())
    except Exception as error:  # noqa: BLE001
        import traceback
        diag["torch_import_error"] = repr(error)
        diag["torch_import_traceback"] = traceback.format_exc()[-4000:]
    return diag


def _gpu_probe():
    report = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
              "euid": getattr(os, "geteuid", os.getuid)(), "cwd": os.getcwd()}
    try:
        import torch
        report["torch_version"] = torch.__version__
        report["torch_cuda_version"] = torch.version.cuda
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["device_count"] = int(torch.cuda.device_count())
        if not report["cuda_available"]:
            report["diagnostics"] = _diag()
            raise RuntimeError("torch.cuda.is_available() is False inside the sandbox")
        device = torch.device("cuda:0")
        report["device_name"] = torch.cuda.get_device_name(device)
        report["capability"] = list(torch.cuda.get_device_capability(device))
        tensor = torch.arange(64, dtype=torch.float32, device=device) * 2.0
        tensor = tensor + 1.0                       # elementwise kernel
        total = float(tensor.sum().item())          # device->host copy forces synchronisation
        torch.cuda.synchronize()
        a = torch.ones((16, 16), dtype=torch.float32, device=device)
        b = a @ a                                    # a small matmul on the device
        torch.cuda.synchronize()
        report.update({"tensor_sum": total, "expected_sum": 64.0 * 64.0,   # sum(2*i+1, i=0..63) = 4096
                       "tensor_sum_ok": abs(total - 4096.0) < 1e-3,
                       "matmul_shape": list(b.shape), "matmul_value": float(b[0, 0].item()),
                       "memory_allocated_bytes": int(torch.cuda.memory_allocated(device)),
                       "cuda_initialized": bool(torch.cuda.is_initialized())})
        report["ns_pid"] = os.readlink("/proc/self/ns/pid")
        report["ns_user"] = os.readlink("/proc/self/ns/user")
        report["ns_mnt"] = os.readlink("/proc/self/ns/mnt")
        report["dev_shm"] = sorted(os.listdir("/dev/shm")) if os.path.isdir("/dev/shm") else None
        # ones(16,16) @ ones(16,16) has every element equal to 16
        report["matmul_ok"] = abs(report["matmul_value"] - 16.0) < 1e-6
        report["ok"] = bool(report["tensor_sum_ok"] and report["matmul_ok"]
                            and report["cuda_initialized"])
    except Exception as error:  # noqa: BLE001
        import traceback
        report["ok"] = False
        report["exception"] = repr(error)
        report["traceback"] = traceback.format_exc()
    with open("gpu_report.json", "w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
    print("GPU_PROBE " + json.dumps(report, sort_keys=True), flush=True)
    if not report.get("ok"):
        raise RuntimeError("GPU probe failed inside the sandbox: " + json.dumps(report)[:1200])


def train(steps):
    _gpu_probe()
    for step in range(1, steps + 1):
        print("step %d loss: %s" % (step, 1.0 / step), flush=True)


def predict(x):
    return (np.arange(len(x)) % 2 == 0).astype(np.int64)


def fill():
    return [1.0, 2.0, 3.0, 4.0]
'''


def gpu_snapshot() -> dict:
    def run(cmd):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"rc": out.returncode, "stdout": out.stdout.strip()[:8000],
                    "stderr": out.stderr.strip()[:4000]}
        except (OSError, subprocess.SubprocessError) as error:
            return {"rc": None, "error": f"{type(error).__name__}: {error}"}
    driver = None
    try:
        driver = Path("/proc/driver/nvidia/version").read_text().strip()
    except OSError:
        pass
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nvidia_smi_query": run(["nvidia-smi", "--query-gpu=index,uuid,driver_version,memory.total,"
                                 "memory.used,memory.free,utilization.gpu", "--format=csv,noheader"]),
        "compute_apps": run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                             "--format=csv,noheader"]),
        "nv_driver": driver,
        "trackx_marker": Path("/home/dowling/r1_locks/trackx_evidence.active").exists(),
        "lease_lock_exists": Path("/home/dowling/r1_locks/gpu0.lock").exists(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="gpu_smoke")
    ap.add_argument("--interpreter", default=sys.executable)
    args = ap.parse_args()
    repo, base = Path(args.repo), Path(args.base)
    cg = os.environ.get("AR_TEST_CGROUP_PARENT")
    if not cg:
        print("AR_TEST_CGROUP_PARENT is not set", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo / "tests" / "trackg"))

    import hashlib
    from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
    from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
    from autoresearch.trackg.runner import ResourceLimits, WorkingCopyRunner  # noqa: E402

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = base / "work" / f"{args.tag}_{stamp}"
    work.mkdir(parents=True)
    node = make_isolated_node(work, "ok")
    (node / "train.py").write_text(TRAIN_PY, encoding="utf-8")
    node_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(node.iterdir()) if p.is_file()}

    iso_block = {"entry": "parent.py", "args": ["{budget}"]}
    mapping = isolated_spec_mapping(
        name="tasl2_gpu_smoke",
        description="TASL-2 host check: editable train.py allocates/synchronises a CUDA tensor in the sandbox",
        frozen_paths=["parent.py", "worker.py", "ar_isolated.py"],
        editable_paths=["train.py"],
        isolation=iso_block,
        selection={"test_scored": False, "selection_split": "validation"},
    )
    spec = TrackGNodeSpec.from_mapping(mapping)
    waivers: dict = {}
    gpu_before = gpu_snapshot()
    apps = gpu_before["compute_apps"].get("stdout", "")
    # The unit gives a GPU by UUID (indices are refused): limits.gpu_uuids -> CUDA_VISIBLE_DEVICES=<GPU-...>.
    gpu_uuid = None
    try:
        gpu_uuid = [part.strip() for part in
                    gpu_before["nvidia_smi_query"].get("stdout", "").splitlines()[0].split(",")][1]
    except (IndexError, AttributeError):
        gpu_uuid = None
    result: dict = {"utc": stamp, "repo": str(repo), "base": str(base), "tag": args.tag,
                    "interpreter": args.interpreter, "cgroup_parent": cg,
                    "gpu_before": gpu_before, "gpu_uuid": gpu_uuid,
                    "expected_gpu_uuid": EXPECTED_GPU_UUID, "node_hashes": node_hashes,
                    "waivers": waivers, "refused": False}
    if apps.strip() or gpu_before["trackx_marker"] or gpu_uuid != EXPECTED_GPU_UUID:
        result["refused"] = True
        result["refusal_reason"] = (f"GPU not exclusively free / not identifiable (compute_apps={apps!r}, "
                                    f"trackx_marker={gpu_before['trackx_marker']}, uuid={gpu_uuid!r}); "
                                    f"no run started")
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                                  encoding="utf-8")
        print(json.dumps({"refused": True, "reason": result["refusal_reason"]}))
        return 3

    limits = ResourceLimits(uncapped_reason="TASL-2 GPU host check: one small CUDA tensor, no CPU/memory cap",
                            measured_run_seconds=20.0, kill_grace_seconds=3.0,
                            gpu_uuids=(gpu_uuid,), cgroup_parent=cg, isolation_waivers=waivers)
    runner = WorkingCopyRunner(spec, node, base / "records")
    try:
        run = runner.run(f"{args.tag}_{stamp}", limits, interpreter=args.interpreter)
    except Exception as exc:  # noqa: BLE001
        import traceback
        result["refused_or_error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        run = None

    result["gpu_after"] = gpu_snapshot()
    if run is not None:
        iso = {k: v for k, v in run.record["isolation"].items() if k != "_verified_log"}
        run_log = (run.run_dir / "run.log").read_text(errors="replace")
        gpu_report_path = run.run_dir / "work" / "gpu_report.json"
        gpu_report = json.loads(gpu_report_path.read_text()) if gpu_report_path.exists() else None
        result_channel = (run.run_dir / "result_channel.txt").read_text(errors="replace")
        result.update({
            "run_dir": str(run.run_dir), "record_path": str(run.run_dir / "run_record.json"),
            "outcome": run.record.get("outcome"), "isolation": iso,
            "result_channel": result_channel, "run_log": run_log,
            "gpu_report_path": str(gpu_report_path), "gpu_report": gpu_report,
            "environment_applied": run.record.get("environment_applied"),
            "command": run.record.get("command"),
        })
        cuda_error = any(token in run_log for token in
                         ("CUDA error", "cudaError", "CUDA_ERROR"))
        checks = {
            "outcome_ok": (run.record.get("outcome") or {}).get("kind") == "ok",
            "effective_true": iso.get("effective") is True,
            "waivers_empty": iso.get("waivers") == {},
            "exceptions_empty": iso.get("exceptions") == [],
            "worker_sandbox_present": iso.get("worker_sandbox") is not None,
            "gpu_report_written": gpu_report is not None,
            "gpu_ran_in_worker": bool(gpu_report and gpu_report.get("ok")),
            "gpu_tensor_sum_correct": bool(gpu_report and gpu_report.get("tensor_sum_ok")),
            "worker_pid1": bool((gpu_report or {}).get("pid") == 1),
            "run_log_has_gpu_probe": "GPU_PROBE" in run_log,
            "no_cuda_error_text": not cuda_error,
            "metric_written": "val_accuracy" in result_channel,
            "cgroup_removed": bool((iso.get("cgroup") or {}).get("removed")),
            "gpu_env_by_uuid": ((run.record.get("environment_applied") or {})
                                .get("CUDA_VISIBLE_DEVICES") == gpu_uuid),
            "gpu_uuid_matches_expected": gpu_uuid == EXPECTED_GPU_UUID,
        }
        result["checks"] = checks
        result["condition_6_pass"] = all(checks.values())
        records = Path(args.out).parent / "records" / args.tag
        records.mkdir(parents=True, exist_ok=True)
        for name in ("run_record.json", "run.log", "result_channel.txt"):
            if (run.run_dir / name).exists():
                (records / name).write_bytes((run.run_dir / name).read_bytes())
        if gpu_report_path.exists():
            (records / "gpu_report.json").write_bytes(gpu_report_path.read_bytes())
        result["copied_records"] = str(records)
    else:
        result["condition_6_pass"] = False
        result["checks"] = {"run_started": False}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                              encoding="utf-8")
    print("RESULT " + json.dumps({"condition_6_pass": result.get("condition_6_pass"),
                                  "checks": result.get("checks"),
                                  "refused_or_error": result.get("refused_or_error"),
                                  "gpu_report": result.get("gpu_report"),
                                  "isolation_effective": (result.get("isolation") or {}).get("effective"),
                                  "waivers": (result.get("isolation") or {}).get("waivers"),
                                  "exceptions": (result.get("isolation") or {}).get("exceptions")},
                                 default=str))
    return 0 if result.get("condition_6_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
