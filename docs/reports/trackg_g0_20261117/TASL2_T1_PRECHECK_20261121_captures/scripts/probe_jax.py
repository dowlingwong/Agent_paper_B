"""R1-T1-HOST-TASL TASL-2 pre-launch: jax312 GPU smoke inside the worker sandbox (Breakout node environment).

Same apparatus as ``probe_gpu.py`` (the unit's own ``tests/trackg/isolated_fixture`` node and
``WorkingCopyRunner``, no waivers) with a jax trainer instead of the torch one: the editable ``train.py``
checks the jax backend/devices and runs a jitted GPU matmul inside the sandboxed worker (PID 1 of its own
user/mount/PID namespaces), and tries ``gymnax.make("Breakout-MinAtar")`` (the Breakout node's environment).

Run inside a delegated scope with ``AR_TEST_CGROUP_PARENT`` set and the host's documented exclusive GPU lease
(``flock ~/r1_locks/gpu0.lock``, taken by ``run_jax_smoke.sh``); no compute app before or after. The record
must show ``effective: true``, ``waivers {}`` and ``exceptions []``; the jax report must show the GPU backend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from probe_gpu import gpu_snapshot  # noqa: E402  (same directory as this script)

REPO = Path("/home/dowling/r1_tracks/t1_tasl/harness")
BASE = Path("/home/dowling/r1_engineering/tasl2_t1_precheck_20261121")

TRAIN_PY = r'''"""Editable trainer for the TASL-2 jax312 GPU smoke: jax devices + jitted GPU work inside the sandbox."""
import json
import os
import sys

import numpy as np

MODE = "jax_gpu"


def _read(path):
    try:
        with open(path, "r", errors="replace") as handle:
            return handle.read()[:4000]
    except OSError as error:
        return "<unreadable: %r>" % (error,)


def _env_subset():
    keys = ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "PATH", "LD_LIBRARY_PATH",
            "HOME", "TMPDIR", "XLA_FLAGS", "JAX_PLATFORMS", "AR_RESULT_SOCKET", "RUST_LOG")
    return {k: os.environ.get(k) for k in keys}


def _diag():
    diag = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(), "cwd": os.getcwd(),
            "env": _env_subset(), "dev_nodes": {}, "dev_listing": [],
            "proc_driver_nvidia_version": None,
            "uid_map": _read("/proc/self/uid_map"), "gid_map": _read("/proc/self/gid_map"),
            "sys_module_nvidia_version": _read("/sys/module/nvidia/version")}
    for name in ("nvidiactl", "nvidia0", "nvidia-uvm", "nvidia-uvm-tools", "nvidia-modeset"):
        path = "/dev/" + name
        entry = {"exists": os.path.exists(path)}
        try:
            st = os.stat(path)
            entry.update({"mode": oct(st.st_mode & 0o777), "uid": st.st_uid, "gid": st.st_gid})
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
    if os.path.exists("/proc/driver/nvidia/version"):
        diag["proc_driver_nvidia_version"] = _read("/proc/driver/nvidia/version")
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
        import subprocess
        diag["nvidia_smi"] = {"cmd": "nvidia-smi -L"}
        proc = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=30)
        diag["nvidia_smi"].update({"rc": proc.returncode, "stdout": proc.stdout[-4000:],
                                   "stderr": proc.stderr[-4000:]})
    except Exception as error:  # noqa: BLE001
        diag["nvidia_smi"] = repr(error)
    try:
        import jax
        diag["jax_version"] = jax.__version__
        diag["jax_default_backend"] = jax.default_backend()
        diag["jax_devices"] = [str(d) for d in jax.devices()]
    except Exception as error:  # noqa: BLE001
        import traceback
        diag["jax_import_error"] = repr(error)
        diag["jax_import_traceback"] = traceback.format_exc()[-4000:]
    return diag


def _jax_probe():
    report = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
              "euid": getattr(os, "geteuid", os.getuid)(), "cwd": os.getcwd()}
    try:
        import jax
        import jax.numpy as jnp
        report["jax_version"] = jax.__version__
        report["backend"] = jax.default_backend()
        devices = jax.devices()
        report["devices"] = [str(d) for d in devices]
        report["device_kinds"] = [getattr(d, "device_kind", None) for d in devices]
        report["device_platforms"] = [getattr(d, "platform", None) for d in devices]
        if report["backend"] != "gpu":
            report["diagnostics"] = _diag()
            raise RuntimeError("jax.default_backend() is not gpu inside the sandbox: %r"
                               % (report["backend"],))
        x = jnp.arange(64, dtype=jnp.float32) * 2.0 + 1.0
        total = float(jnp.sum(x))
        a = jnp.ones((16, 16), dtype=jnp.float32)
        matmul = jax.jit(lambda t: t @ t)(a)
        report["tensor_sum"] = total
        report["tensor_sum_ok"] = abs(total - 4096.0) < 1e-3
        report["matmul_value"] = float(matmul[0, 0])
        report["matmul_ok"] = abs(report["matmul_value"] - 16.0) < 1e-4
        try:
            import gymnax
            env, params = gymnax.make("Breakout-MinAtar")
            obs, _state = env.reset(jax.random.PRNGKey(0), params)
            report["gymnax_breakout"] = {"env": type(env).__name__,
                                         "obs_shape": [int(n) for n in obs.shape],
                                         "obs_device": str(getattr(obs, "device", None))}
        except Exception as error:  # noqa: BLE001
            report["gymnax_breakout"] = {"error": repr(error)[:800]}
        report["ns_pid"] = os.readlink("/proc/self/ns/pid")
        report["ns_user"] = os.readlink("/proc/self/ns/user")
        report["ns_mnt"] = os.readlink("/proc/self/ns/mnt")
        report["dev_shm"] = sorted(os.listdir("/dev/shm")) if os.path.isdir("/dev/shm") else None
        report["ok"] = bool(report["tensor_sum_ok"] and report["matmul_ok"])
    except Exception as error:  # noqa: BLE001
        import traceback
        report["ok"] = False
        report["exception"] = repr(error)
        report["traceback"] = traceback.format_exc()
    with open("jax_report.json", "w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
    print("JAX_PROBE " + json.dumps(report, sort_keys=True), flush=True)
    if not report.get("ok"):
        raise RuntimeError("jax GPU probe failed inside the sandbox: " + json.dumps(report)[:1200])


def train(steps):
    _jax_probe()
    for step in range(1, steps + 1):
        print("step %d loss: %s" % (step, 1.0 / step), flush=True)


def predict(x):
    return (np.arange(len(x)) % 2 == 0).astype(np.int64)


def fill():
    return [1.0, 2.0, 3.0, 4.0]
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="jax_gpu_smoke")
    ap.add_argument("--interpreter", default=sys.executable)
    args = ap.parse_args()
    repo, base = Path(args.repo), Path(args.base)
    cg = os.environ.get("AR_TEST_CGROUP_PARENT")
    if not cg:
        print("AR_TEST_CGROUP_PARENT is not set", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo / "tests" / "trackg"))

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
        name="tasl2_jax_gpu_smoke",
        description="TASL-2 T1 precheck: editable train.py runs jax GPU work in the sandbox",
        frozen_paths=["parent.py", "worker.py", "ar_isolated.py"],
        editable_paths=["train.py"],
        isolation=iso_block,
        selection={"test_scored": False, "selection_split": "validation"})
    spec = TrackGNodeSpec.from_mapping(mapping)
    waivers: dict = {}
    gpu_before = gpu_snapshot()
    apps = gpu_before["compute_apps"].get("stdout", "")
    gpu_uuid = None
    try:
        gpu_uuid = [part.strip() for part in
                    gpu_before["nvidia_smi_query"].get("stdout", "").splitlines()[0].split(",")][1]
    except (IndexError, AttributeError):
        gpu_uuid = None
    result: dict = {"utc": stamp, "repo": str(repo), "base": str(base), "tag": args.tag,
                    "interpreter": args.interpreter, "cgroup_parent": cg,
                    "gpu_before": gpu_before, "gpu_uuid": gpu_uuid, "node_hashes": node_hashes,
                    "waivers": waivers, "refused": False}
    if apps.strip() or gpu_before["trackx_marker"] or not gpu_uuid:
        result["refused"] = True
        result["refusal_reason"] = (f"GPU not exclusively free / not identifiable (compute_apps={apps!r}, "
                                    f"trackx_marker={gpu_before['trackx_marker']}, uuid={gpu_uuid!r}); "
                                    f"no run started")
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                                  encoding="utf-8")
        print(json.dumps({"refused": True, "reason": result["refusal_reason"]}))
        return 3
    limits = ResourceLimits(uncapped_reason="TASL-2 T1 precheck: one small jax GPU op, no CPU/memory cap",
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
        jax_report_path = run.run_dir / "work" / "jax_report.json"
        jax_report = json.loads(jax_report_path.read_text()) if jax_report_path.exists() else None
        result_channel = (run.run_dir / "result_channel.txt").read_text(errors="replace")
        result.update({
            "run_dir": str(run.run_dir), "record_path": str(run.run_dir / "run_record.json"),
            "outcome": run.record.get("outcome"), "isolation": iso,
            "result_channel": result_channel, "run_log": run_log,
            "jax_report_path": str(jax_report_path), "jax_report": jax_report,
            "environment_applied": run.record.get("environment_applied"),
            "command": run.record.get("command")})
        checks = {
            "outcome_ok": (run.record.get("outcome") or {}).get("kind") == "ok",
            "effective_true": iso.get("effective") is True,
            "waivers_empty": iso.get("waivers") == {},
            "exceptions_empty": iso.get("exceptions") == [],
            "worker_sandbox_present": iso.get("worker_sandbox") is not None,
            "jax_report_written": jax_report is not None,
            "jax_ran_in_worker": bool(jax_report and jax_report.get("ok")),
            "jax_gpu_backend": bool(jax_report and jax_report.get("backend") == "gpu"),
            "jax_tensor_sum_correct": bool(jax_report and jax_report.get("tensor_sum_ok")),
            "worker_pid1": bool((jax_report or {}).get("pid") == 1),
            "run_log_has_jax_probe": "JAX_PROBE" in run_log,
            "no_jax_error_text": not any(token in run_log for token in
                                         ("CUDA error", "cudaError", "XlaRuntimeError",
                                          "JAX_PROBE_REPORTED_ERROR")),
            "metric_written": "val_accuracy" in result_channel,
            "cgroup_removed": bool((iso.get("cgroup") or {}).get("removed")),
            "gpu_env_by_uuid": ((run.record.get("environment_applied") or {})
                                .get("CUDA_VISIBLE_DEVICES") == gpu_uuid)}
        result["checks"] = checks
        result["condition_jax_gpu_pass"] = all(checks.values())
        records = Path(args.out).parent / "records" / args.tag
        records.mkdir(parents=True, exist_ok=True)
        for name in ("run_record.json", "run.log", "result_channel.txt"):
            if (run.run_dir / name).exists():
                (records / name).write_bytes((run.run_dir / name).read_bytes())
        if jax_report_path.exists():
            (records / "jax_report.json").write_bytes(jax_report_path.read_bytes())
        result["copied_records"] = str(records)
    else:
        result["condition_jax_gpu_pass"] = False
        result["checks"] = {"run_started": False}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
                              encoding="utf-8")
    print("RESULT " + json.dumps({"condition_jax_gpu_pass": result.get("condition_jax_gpu_pass"),
                                  "checks": result.get("checks"),
                                  "refused_or_error": result.get("refused_or_error"),
                                  "jax_report": result.get("jax_report"),
                                  "isolation_effective": (result.get("isolation") or {}).get("effective"),
                                  "waivers": (result.get("isolation") or {}).get("waivers"),
                                  "exceptions": (result.get("isolation") or {}).get("exceptions")},
                                 default=str))
    return 0 if result.get("condition_jax_gpu_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
