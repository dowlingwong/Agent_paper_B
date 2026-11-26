"""R1-T1-HOST-TASL TASL-2 pre-launch: CPU-only node affinity and CPU/GPU coexistence (G.1b plan §6.4).

``mlgym_houseprice`` runs CPU-only on cpus 8-15 with no GPU variable while a GPU node runs on the same host
(TASL-2's 4090, the plan's GPU nodes on cpus 0-7).  A full node run is out of scope pre-launch (the plan's
job does it), so this uses a **short synthetic load check**: a houseprice-like CPU MLP training loop pinned to
8-15 with ``CUDA_VISIBLE_DEVICES=""`` (no GPU visible), and a GPU node-like torch training loop by UUID pinned
to 0-7.  It measures each workload alone and together and refuses if the GPU job is slowed past its declared
timeout factor (3x) or by more than 1.5x, or if the CPU job is slowed by more than 1.5x.

Run inside a delegated scope (the orchestrator does) so the CPU job's cgroup is the census scope (8G/swap 0);
the workloads are small on purpose.  Read-only apart from ``--out``/``--text`` and the two workload scripts it
writes under ``<base>/work/cpu_gpu_workloads/`` (copied into the captures).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CPU_SCRIPT = r'''"""Synthetic houseprice-like CPU node: a small tabular MLP trained on 8 cores, no GPU."""
import json
import os
import time

import torch

torch.set_num_threads(int(os.environ.get("T1_CPU_THREADS", "8")))
torch.manual_seed(0)
generator = torch.Generator().manual_seed(1234)
n, d = 4000, 10
x = torch.randn(n, d, generator=generator)
true_w = torch.randn(d, 1, generator=generator)
y = x @ true_w + 0.1 * torch.randn(n, 1, generator=generator)
model = torch.nn.Sequential(torch.nn.Linear(d, 64), torch.nn.ReLU(),
                            torch.nn.Linear(64, 64), torch.nn.ReLU(),
                            torch.nn.Linear(64, 1))
opt = torch.optim.Adam(model.parameters(), lr=1e-2)
loss_fn = torch.nn.MSELoss()
target = float(os.environ.get("T1_TARGET_S", "12"))
steps = 0
loss = None
start = time.monotonic()
while time.monotonic() - start < target:
    opt.zero_grad()
    loss = loss_fn(model(x), y)
    loss.backward()
    opt.step()
    steps += 1
wall = time.monotonic() - start
print(json.dumps({"role": "cpu_houseprice_like", "affinity": sorted(os.sched_getaffinity(0)),
                  "wall_s": round(wall, 3), "steps": steps, "target_s": target,
                  "threads": torch.get_num_threads(), "torch": torch.__version__,
                  "cpu_count": os.cpu_count(),
                  "cuda_available": bool(torch.cuda.is_available()),
                  "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                  "nvidia_visible_devices": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
                  "condor_assigned_gpus": os.environ.get("_CONDOR_AssignedGPUs"),
                  "final_loss": float(loss.item()) if loss is not None else None}))
'''

GPU_SCRIPT = r'''"""Synthetic GPU node: a small torch MLP training loop on the 4090 by full UUID."""
import json
import os
import time

import torch

torch.manual_seed(0)
if not torch.cuda.is_available():
    print(json.dumps({"role": "gpu_node_like", "cuda_available": False,
                      "error": "torch.cuda.is_available() is False"}))
    raise SystemExit(3)
device = torch.device("cuda:0")
model = torch.nn.Sequential(torch.nn.Linear(256, 512), torch.nn.ReLU(),
                            torch.nn.Linear(512, 512), torch.nn.ReLU(),
                            torch.nn.Linear(512, 10)).to(device)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
generator = torch.Generator(device=device).manual_seed(1234)
x = torch.randn(512, 256, generator=generator, device=device)
y = torch.randint(0, 10, (512,), generator=generator, device=device)
loss_fn = torch.nn.CrossEntropyLoss()
target = float(os.environ.get("T1_TARGET_S", "20"))
torch.cuda.synchronize()
start = time.monotonic()
steps = 0
loss = None
while time.monotonic() - start < target:
    opt.zero_grad()
    loss = loss_fn(model(x), y)
    loss.backward()
    opt.step()
    steps += 1
    if steps % 10 == 0:
        torch.cuda.synchronize()
torch.cuda.synchronize()
wall = time.monotonic() - start
print(json.dumps({"role": "gpu_node_like", "affinity": sorted(os.sched_getaffinity(0)),
                  "wall_s": round(wall, 3), "steps": steps, "target_s": target,
                  "torch": torch.__version__, "cuda_available": bool(torch.cuda.is_available()),
                  "device_name": torch.cuda.get_device_name(device),
                  "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                  "memory_allocated_bytes": int(torch.cuda.memory_allocated(device)),
                  "final_loss": float(loss.item()) if loss is not None else None}))
'''


def parse_cpus(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(part))
    return out


def run(cmd: list[str], env: dict, timeout: float = 600.0) -> dict:
    started = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    return {"cmd": cmd, "rc": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr[-8000:],
            "driver_wall_s": round(time.monotonic() - started, 3)}


def parse_json(stdout: str) -> dict:
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return {}


def nvidia_apps() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=60)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        return f"<error {error!r}>"


def base_env(cuda: str) -> dict:
    env = dict(os.environ)
    for name in ("LD_PRELOAD",):
        env.pop(name, None)
    env["CUDA_VISIBLE_DEVICES"] = cuda
    env.pop("NVIDIA_VISIBLE_DEVICES", None)
    env.pop("_CONDOR_AssignedGPUs", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--python", default="/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python")
    ap.add_argument("--cuda-visible-devices", default="GPU-4d623e76-7587-ee15-a633-46f60d220d94")
    ap.add_argument("--cpu-cpus", default="8-15")
    ap.add_argument("--gpu-cpus", default="0-7")
    ap.add_argument("--gpu-lease-seconds", type=float, default=20.0)
    ap.add_argument("--cpu-lease-seconds", type=float, default=12.0)
    args = ap.parse_args()
    base, python = Path(args.base), args.python
    cpu_cpus, gpu_cpus = parse_cpus(args.cpu_cpus), parse_cpus(args.gpu_cpus)
    work = base / "work" / "cpu_gpu_workloads"
    work.mkdir(parents=True, exist_ok=True)
    cpu_path, gpu_path = work / "cpu_houseprice_like.py", work / "gpu_node_like.py"
    cpu_path.write_text(CPU_SCRIPT, encoding="utf-8")
    gpu_path.write_text(GPU_SCRIPT, encoding="utf-8")

    result: dict = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "python": python, "cpu_cpus": cpu_cpus, "gpu_cpus": gpu_cpus,
                    "gpu_uuid": args.cuda_visible_devices,
                    "gpu_lease_seconds": args.gpu_lease_seconds,
                    "cpu_lease_seconds": args.cpu_lease_seconds,
                    "gpu_apps_before": nvidia_apps(), "workloads": {}}
    env_cpu = base_env("")                      # CPU-only node: no GPU named, no scheduler variable
    env_cpu["T1_CPU_THREADS"] = "8"
    env_cpu["T1_TARGET_S"] = str(args.cpu_lease_seconds)
    env_gpu = base_env(args.cuda_visible_devices)
    env_gpu["T1_TARGET_S"] = str(args.gpu_lease_seconds)

    cpu_solo = run(["taskset", "-c", args.cpu_cpus, python, str(cpu_path)], env_cpu)
    result["workloads"]["cpu_solo"] = {"scale": parse_json(cpu_solo["stdout"]),
                                       "rc": cpu_solo["rc"], "stderr": cpu_solo["stderr"][-2000:]}
    gpu_solo = run(["taskset", "-c", args.gpu_cpus, python, str(gpu_path)], env_gpu)
    result["workloads"]["gpu_solo"] = {"scale": parse_json(gpu_solo["stdout"]),
                                       "rc": gpu_solo["rc"], "stderr": gpu_solo["stderr"][-2000:],
                                       "apps_during": nvidia_apps()}

    # together: the GPU job runs; after 3 s the CPU job starts beside it on the disjoint cpus
    gpu_proc = subprocess.Popen(["taskset", "-c", args.gpu_cpus, python, str(gpu_path)],
                                env=env_gpu, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(3.0)
    cpu_proc = subprocess.Popen(["taskset", "-c", args.cpu_cpus, python, str(cpu_path)],
                                env=env_cpu, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    apps_during = nvidia_apps()
    cpu_out, cpu_err = cpu_proc.communicate(timeout=600)
    gpu_out, gpu_err = gpu_proc.communicate(timeout=600)
    result["gpu_apps_during_coexistence"] = apps_during
    result["workloads"]["cpu_concurrent"] = {"scale": parse_json(cpu_out), "rc": cpu_proc.returncode,
                                             "stderr": cpu_err[-2000:]}
    result["workloads"]["gpu_concurrent"] = {"scale": parse_json(gpu_out), "rc": gpu_proc.returncode,
                                             "stderr": gpu_err[-2000:]}
    result["gpu_apps_after"] = nvidia_apps()

    cpu_scale = result["workloads"]["cpu_concurrent"]["scale"]
    gpu_solo_s = (result["workloads"]["gpu_solo"]["scale"].get("wall_s") or 0.0)
    gpu_conc_s = (result["workloads"]["gpu_concurrent"]["scale"].get("wall_s") or 0.0)
    cpu_solo_s = (result["workloads"]["cpu_solo"]["scale"].get("wall_s") or 0.0)
    cpu_conc_s = (result["workloads"]["cpu_concurrent"]["scale"].get("wall_s") or 0.0)
    gpu_ratio = gpu_conc_s / gpu_solo_s if gpu_solo_s else None
    cpu_ratio = cpu_conc_s / cpu_solo_s if cpu_solo_s else None
    checks = {
        "cpu_affinity_8_15": sorted(cpu_scale.get("affinity") or []) == sorted(cpu_cpus),
        "gpu_affinity_0_7": sorted((result["workloads"]["gpu_concurrent"]["scale"].get("affinity") or []))
        == sorted(gpu_cpus),
        "cpu_no_gpu_variable": (cpu_scale.get("cuda_visible_devices") == ""
                                and cpu_scale.get("nvidia_visible_devices") is None
                                and cpu_scale.get("condor_assigned_gpus") is None),
        "cpu_cannot_see_gpu": cpu_scale.get("cuda_available") is False,
        "gpu_ran_in_coexistence": bool(result["workloads"]["gpu_concurrent"]["scale"].get("cuda_available")),
        "gpu_not_slowed_1.5x": bool(gpu_ratio is not None and gpu_ratio <= 1.5),
        "gpu_within_timeout_3x": bool(gpu_ratio is not None and gpu_ratio < 3.0),
        "cpu_not_slowed_1.5x": bool(cpu_ratio is not None and cpu_ratio <= 1.5),
        "gpu_idle_before": not result["gpu_apps_before"].strip(),
    }
    result["measurements"] = {"gpu_solo_wall_s": gpu_solo_s, "gpu_concurrent_wall_s": gpu_conc_s,
                              "gpu_ratio_concurrent_over_solo": gpu_ratio,
                              "declared_timeout_3x_s": 3.0 * gpu_solo_s,
                              "cpu_solo_wall_s": cpu_solo_s, "cpu_concurrent_wall_s": cpu_conc_s,
                              "cpu_ratio_concurrent_over_solo": cpu_ratio}
    result["checks"] = checks
    result["condition_cpu_gpu_pass"] = all(checks.values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"utc={result['utc']} cpu_cpus={cpu_cpus} gpu_cpus={gpu_cpus} "
                 f"gpu_uuid={args.cuda_visible_devices}",
                 f"gpu_solo_wall_s={gpu_solo_s} gpu_concurrent_wall_s={gpu_conc_s} "
                 f"gpu_ratio={gpu_ratio} (timeout 3x={3.0 * gpu_solo_s:.3f} s)",
                 f"cpu_solo_wall_s={cpu_solo_s} cpu_concurrent_wall_s={cpu_conc_s} cpu_ratio={cpu_ratio}",
                 f"cpu_child_affinity={cpu_scale.get('affinity')} cuda_visible_devices="
                 f"{cpu_scale.get('cuda_visible_devices')!r} cuda_available={cpu_scale.get('cuda_available')}",
                 f"gpu_child_affinity={result['workloads']['gpu_concurrent']['scale'].get('affinity')} "
                 f"gpu_device={result['workloads']['gpu_concurrent']['scale'].get('device_name')}",
                 f"gpu_apps: before={result['gpu_apps_before']!r} during={apps_during!r} "
                 f"after={result['gpu_apps_after']!r}",
                 f"checks={json.dumps(checks)}",
                 f"condition_cpu_gpu_pass={result['condition_cpu_gpu_pass']}"]
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_cpu_gpu_pass": result["condition_cpu_gpu_pass"],
                                  "checks": checks, "measurements": result["measurements"]},
                                 default=str))
    return 0 if result["condition_cpu_gpu_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
