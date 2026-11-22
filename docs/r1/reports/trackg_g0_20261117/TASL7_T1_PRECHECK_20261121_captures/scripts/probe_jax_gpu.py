"""R1-T1-HOST-TASL: the jax312 environment's GPU on TASL-7 (G.1b's ``mlgym_breakout_minatar`` node runs jax here).

Read-only.  Run by ``run_jax_gpu.sh`` inside a delegated per-command cgroup
(``systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0``) holding the host's
documented exclusive GPU lease, with ``CUDA_VISIBLE_DEVICES`` set to the **full GPU UUID** (the unit names a
GPU by UUID; an index is refused).  It imports the census ``jax312`` environment and runs two small device
operations, forcing synchronisation with ``block_until_ready``, and records the device the backend chose.

The condition is: the default JAX backend is GPU, exactly one device is visible (by UUID), and both results are
numerically correct.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

GPU_UUID = "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1"


def run(cmd: list[str], timeout: float = 60.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout.strip()[:8000],
                "stderr": out.stderr.strip()[:4000]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--gpu-uuid", default=GPU_UUID)
    ap.add_argument("--tag", default="jax_gpu_smoke")
    args = ap.parse_args()
    report: dict = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "tag": args.tag, "python": sys.executable, "cwd": os.getcwd(),
                    "env": {k: os.environ.get(k) for k in
                            ("CUDA_VISIBLE_DEVICES", "XLA_FLAGS", "XLA_PYTHON_CLIENT_PREALLOCATE",
                             "XLA_PYTHON_CLIENT_MEM_FRACTION", "LD_LIBRARY_PATH", "LD_PRELOAD")},
                    "ptxas_candidates": {path: os.path.exists(path) for path in
                                         ("/usr/local/cuda/bin/ptxas", "/usr/local/cuda-12.2/bin/ptxas",
                                          "/usr/bin/ptxas")},
                    "gpu_uuid": args.gpu_uuid,
                    "cgroup_self": Path("/proc/self/cgroup").read_text().strip(),
                    "nvidia_smi_L": run(["nvidia-smi", "-L"]),
                    "compute_apps_before": run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,"
                                                "process_name,used_memory", "--format=csv,noheader"])}
    try:
        import jax
        import jaxlib
        import jax.numpy as jnp
        report["jax_version"] = jax.__version__
        report["jaxlib_version"] = jaxlib.__version__
        report["python_version"] = sys.version.split()[0]
        report["default_backend"] = jax.default_backend()
        devices = jax.devices()
        report["devices"] = [{"id": getattr(d, "id", None), "platform": getattr(d, "platform", None),
                              "device_kind": getattr(d, "device_kind", None),
                              "repr": repr(d)} for d in devices]
        report["device_count"] = len(devices)
        gpu_devices = [d for d in devices if getattr(d, "platform", "") == "gpu"]
        report["gpu_device_count"] = len(gpu_devices)
        if not gpu_devices:
            raise RuntimeError("JAX sees no GPU device: " + repr(report["devices"]))
        device = gpu_devices[0]
        report["chosen_device"] = {"id": getattr(device, "id", None),
                                   "device_kind": getattr(device, "device_kind", None),
                                   "repr": repr(device)}
        x = jnp.arange(1024, dtype=jnp.float32)
        total = float((x * 2.0 + 1.0).sum())          # sum(2i+1, i=0..1023) == 1024**2
        report["tensor_sum"] = total
        report["expected_sum"] = float(1024 * 1024)
        report["tensor_sum_ok"] = abs(total - 1024.0 * 1024.0) < 1e-3
        a = jnp.ones((32, 32), dtype=jnp.float32)
        b = a @ a                                      # every element == 32
        value = float(b[0, 0])
        report["matmul_value"] = value
        report["matmul_ok"] = abs(value - 32.0) < 1e-5
        report["jax_initialized"] = True
        report["ok"] = bool(report["tensor_sum_ok"] and report["matmul_ok"]
                            and report["default_backend"] == "gpu")
    except Exception as error:  # noqa: BLE001
        report["ok"] = False
        report["exception"] = repr(error)
        report["traceback"] = traceback.format_exc()[-6000:]
    report["compute_apps_after"] = run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,"
                                        "process_name,used_memory", "--format=csv,noheader"])
    report["checks"] = {
        "jax_imported": bool(report.get("jax_version")),
        "default_backend_gpu": report.get("default_backend") == "gpu",
        "one_gpu_device": report.get("gpu_device_count") == 1,
        "gpu_env_by_uuid": (report["env"].get("CUDA_VISIBLE_DEVICES") == args.gpu_uuid),
        "tensor_sum_ok": bool(report.get("tensor_sum_ok")),
        "matmul_ok": bool(report.get("matmul_ok")),
        "no_ld_library_path": not report["env"].get("LD_LIBRARY_PATH"),
        "no_ld_preload": not report["env"].get("LD_PRELOAD"),
    }
    report["condition_jax_gpu_pass"] = all(report["checks"].values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({k: report.get(k) for k in
                                  ("jax_version", "jaxlib_version", "default_backend", "device_count",
                                   "gpu_device_count", "chosen_device", "tensor_sum", "matmul_value",
                                   "ok", "checks", "condition_jax_gpu_pass", "exception")},
                                 default=str))
    return 0 if report["condition_jax_gpu_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
