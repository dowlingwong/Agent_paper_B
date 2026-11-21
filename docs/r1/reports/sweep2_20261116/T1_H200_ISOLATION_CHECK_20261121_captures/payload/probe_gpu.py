"""R1-T1-HOST-H200 host condition §5.5 (experiment-agent item 7): the GPU smoke with the worker sandbox on.

A tiny isolated node: the frozen parent makes an 8-float CUDA tensor, shares it with
``ar_isolated.cuda_share()``; the sandboxed worker (PID 1 of its own user/mount/PID/net/cgroup namespaces) opens
it with ``ar_isolated.cuda_open()`` and sends a CPU copy back.  The node sets ``shared_dev_shm: true`` (torch
keeps the CUDA IPC reference counters there -- the autoresearch node's declared exception), so the record has
``exceptions: ["shared_dev_shm"]`` and ``effective: false`` by design, never a waiver.

Also runs the same CUDA IPC hand-off in a plain process (no namespaces) as a control, so a failure can be
attributed to the namespace architecture or to the host GPU/driver.  The run itself is one 8-float tensor; the
HTCondor slot is a single exclusively-allocated H200.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
import traceback
from pathlib import Path

import lib_iso

PARENT_PY = textwrap.dedent('''\
    """Frozen parent: shares one small CUDA tensor with the sandboxed worker over CUDA IPC."""
    import ar_isolated as iso
    chan = iso.parent_start()
    import json
    import sys

    import torch

    ok = False
    report = {}
    try:
        worker = iso.Worker("cuda_worker.py")
        try:
            tensor = torch.arange(8, dtype=torch.float32, device="cuda:0") * 1.5
            desc = iso.cuda_share(tensor)
            meta, arrays = worker.call("open", {"desc": desc})
            values = arrays.get("y")
            expected = (torch.arange(8, dtype=torch.float32) * 1.5).numpy()
            same = values is not None and values.shape == expected.shape and bool((abs(values - expected) < 1e-6).all())
            ok = bool(same) and meta.get("pid") == 1
            report = {"ipc_ok": bool(same), "worker": meta, "device": str(tensor.device),
                      "parent_cuda_init": torch.cuda.is_initialized(),
                      "values": [float(v) for v in values] if values is not None else None}
        finally:
            worker.close()
    except iso.IsolationProtocolError as error:
        report = {"ipc_ok": False, "error": str(error)[:2000]}
    print("cuda ipc report:", json.dumps(report), flush=True)
    if not ok:
        print("AR_ERROR CUDA IPC across the PID namespace failed", flush=True)
        sys.exit(4)
    chan.write("val_accuracy: 1.0000")
    chan.close()
    ''')

WORKER_PY = textwrap.dedent('''\
    """Frozen worker entry (PID 1 of the worker namespaces): opens the parent's CUDA IPC tensor and copies it."""
    import ar_isolated as iso
    conn = iso.worker_connect()
    import os

    import torch

    torch.cuda.init()   # latent cuda_open init requirement (iso-fix report, residual risk 2); diagnostics only


    def h_open(meta, arrays, fds):
        tensor = iso.cuda_open(meta["desc"])
        host = tensor.detach().cpu().numpy()
        return {"pid": os.getpid(), "device": str(tensor.device), "sum": float(host.sum())}, {"y": host}


    iso.serve({"open": h_open}, conn)
    ''')

TRAIN_PY = '"""Editable placeholder: this probe only exercises frozen code."""\n'

CONTROL_CODE = textwrap.dedent('''\
    import json, sys
    sys.path.insert(0, sys.argv[1])
    import torch
    import ar_isolated as iso
    torch.cuda.init()
    desc = json.loads(sys.argv[2])
    tensor = iso.cuda_open(desc)
    host = tensor.detach().cpu().numpy()
    expected = (torch.arange(8, dtype=torch.float32) * 1.5).numpy()
    print(json.dumps({"ipc_ok": bool((abs(host - expected) < 1e-6).all()), "values": [float(v) for v in host],
                      "device": str(tensor.device), "cuda_init": torch.cuda.is_initialized()}))
    ''')


def gpu_facts() -> dict:
    out: dict = {"torch_importable": False}
    try:
        import torch
        out.update({"torch_importable": True, "torch_version": torch.__version__,
                    "torch_cuda_version": torch.version.cuda,
                    "cuda_available": torch.cuda.is_available(),
                    "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES")})
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            free, total = torch.cuda.mem_get_info(device)
            props = torch.cuda.get_device_properties(device)
            out.update({"device_count": torch.cuda.device_count(), "device": device,
                        "name": torch.cuda.get_device_name(device),
                        "capability": [props.major, props.minor],
                        "memory_total_mib": round(total / 2**20, 1), "memory_free_mib": round(free / 2**20, 1),
                        "memory_used_mib": round((total - free) / 2**20, 1),
                        "driver_version_host": lib_iso.read_text("/proc/driver/nvidia/version").strip()
                        if os.path.exists("/proc/driver/nvidia/version") else None})
    except Exception:  # noqa: BLE001
        out["error"] = traceback.format_exc()
    out["nvidia_smi"] = lib_iso.run(["nvidia-smi", "-L"], timeout=30)
    out["nvidia_smi_apps"] = lib_iso.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader,nounits"],
        timeout=30)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--interpreter", default=sys.executable)
    parser.add_argument("--revision", default="unknown")
    parser.add_argument("--tag", default="gpu_smoke")
    parser.add_argument("--base", required=True)
    parser.add_argument("--cgroup-parent", default=os.environ.get("AR_TEST_CGROUP_PARENT", ""))
    parser.add_argument("--diag-waivers", default="",
                        help="diagnostic only: comma list among no_cgroup,ptrace_scope,root")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    result: dict = {
        "utc": stamp, "revision": args.revision, "repo": args.repo, "interpreter": args.interpreter,
        "euid": os.geteuid(), "cgroup_parent": args.cgroup_parent or None,
        "diagnostic_waivers": [x.strip() for x in args.diag_waivers.split(",") if x.strip()],
        "gpu_before": gpu_facts(),
    }
    gpu = result["gpu_before"]
    # Safety gate: only ever touch a GPU that the batch system allocated to THIS job.  A CPU-only allocation
    # (CUDA_VISIBLE_DEVICES unset) must never pick up a GPU another job is using.
    allocated = bool(str(os.environ.get("CUDA_VISIBLE_DEVICES") or "").strip())
    result["gpu_allocated_to_this_job"] = allocated
    if not gpu.get("torch_importable") or not gpu.get("cuda_available") or not allocated:
        result["condition_pass"] = False
        result["refused"] = True
        result["refusal_reason"] = (f"no CUDA device allocated to this job (CUDA_VISIBLE_DEVICES="
                                    f"{os.environ.get('CUDA_VISIBLE_DEVICES')!r}; torch_importable="
                                    f"{gpu.get('torch_importable')}, cuda_available={gpu.get('cuda_available')})")
        lib_iso.write_json(args.out, result)
        print(json.dumps({"tag": args.tag, "refused": True, "reason": result["refusal_reason"]}))
        return 3
    if gpu.get("memory_used_mib", 1e9) > 2 * 1024:
        result["condition_pass"] = False
        result["refused"] = True
        result["refusal_reason"] = (f"the allocated GPU is already in use ({gpu.get('memory_used_mib')} MiB used); "
                                    f"refusing to touch another job's card")
        lib_iso.write_json(args.out, result)
        print(json.dumps({"tag": args.tag, "refused": True, "reason": result["refusal_reason"]}))
        return 3
    if gpu.get("memory_free_mib", 0) < 40 * 1024:
        result["condition_pass"] = False
        result["refused"] = True
        result["refusal_reason"] = f"GPU has less than 40 GiB free ({gpu.get('memory_free_mib')} MiB); no run started"
        lib_iso.write_json(args.out, result)
        print(json.dumps({"tag": args.tag, "refused": True, "reason": result["refusal_reason"]}))
        return 3

    # Plain-process control: the same CUDA IPC hand-off without any namespace.
    node_lib = Path(args.repo) / "src" / "autoresearch" / "trackg" / "node_lib"
    control: dict = {"node_lib": str(node_lib)}
    try:
        sys.path.insert(0, str(node_lib))
        import ar_isolated as driver_iso  # noqa: E402  (node_lib has no __init__.py; imported by path)
        import torch  # noqa: E402
        control["driver_cuda_init_before"] = torch.cuda.is_initialized()
        tensor = torch.arange(8, dtype=torch.float32, device="cuda:0") * 1.5
        desc = driver_iso.cuda_share(tensor)
        control["desc"] = desc
        proc = subprocess.run([args.interpreter, "-c", CONTROL_CODE, str(node_lib), json.dumps(desc)],
                              capture_output=True, text=True, timeout=180)
        control["plain_process"] = {"rc": proc.returncode, "stdout": proc.stdout[-8000:],
                                    "stderr": proc.stderr[-8000:]}
        try:
            control["plain_ipc_ok"] = bool(json.loads(proc.stdout.strip().splitlines()[-1]).get("ipc_ok"))
        except (json.JSONDecodeError, IndexError):
            control["plain_ipc_ok"] = False
    except Exception:  # noqa: BLE001
        control["error"] = traceback.format_exc()
        control["plain_ipc_ok"] = False
    result["plain_control"] = control

    diag = [x.strip() for x in args.diag_waivers.split(",") if x.strip()]
    if not args.cgroup_parent and "no_cgroup" not in diag:
        result["refused"] = True
        result["refusal_reason"] = ("no writable delegated cgroup v2 parent (condition C1 FAIL); a no-waiver run "
                                    "needs limits.cgroup_parent")
        result["condition_pass"] = False
        lib_iso.write_json(args.out, result)
        print(json.dumps({"tag": args.tag, "refused": True, "reason": result["refusal_reason"]}))
        return 2

    base = Path(args.base) / f"gpu_{args.tag}_{stamp}_{os.getpid()}"
    base.mkdir(parents=True)
    try:
        sys.path.insert(0, os.path.join(args.repo, "src"))
        sys.path.insert(0, os.path.join(args.repo, "tests", "trackg"))
        from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
        from autoresearch.trackg.runner import RunnerError, ResourceLimits, WorkingCopyRunner  # noqa: E402
        from isolated_fixture import isolated_spec_mapping  # noqa: E402

        node = base / "node"
        node.mkdir()
        (node / "parent.py").write_text(PARENT_PY, encoding="utf-8")
        (node / "cuda_worker.py").write_text(WORKER_PY, encoding="utf-8")
        (node / "train.py").write_text(TRAIN_PY, encoding="utf-8")
        (node / "ar_isolated.py").write_bytes((node_lib / "ar_isolated.py").read_bytes())
        mapping = isolated_spec_mapping(
            name="h200_gpu_cuda_ipc_probe",
            description="tiny CUDA IPC across the worker PID namespace (H200 host check, §5.5)",
            frozen_paths=["parent.py", "cuda_worker.py", "ar_isolated.py"],
            editable_paths=["train.py"],
            isolation={"entry": "parent.py", "args": [], "shared_dev_shm": True},
            selection={"test_scored": False, "selection_split": "validation"},
        )
        spec = TrackGNodeSpec.from_mapping(mapping)
        waivers = {}
        reasons = {
            "no_cgroup": "diagnostic-only host check: no writable delegated cgroup v2 subtree in this HTCondor "
                         "container (condition C1 FAIL); the run is NOT effective",
            "ptrace_scope": "diagnostic-only host check: Yama ptrace_scope < 1 in this HTCondor container "
                            "(condition C4 FAIL); the run is NOT effective",
            "root": "diagnostic-only host check: the container job runs as root (condition C2 FAIL); the run is "
                    "NOT effective",
        }
        for name in diag:
            if name in reasons:
                waivers[name] = reasons[name]
        limits = ResourceLimits(
            uncapped_reason="host-check GPU probe: one 8-float tensor; CPU/memory are bounded by the HTCondor "
                            "container job (request_cpus=4, request_memory=16000 MB)",
            provisional_timeout_seconds=300.0, kill_grace_seconds=10.0,
            cgroup_parent=args.cgroup_parent or None, isolation_waivers=waivers)
        runner = WorkingCopyRunner(spec, node, base / "runs")
        try:
            run = runner.run(f"h200_gpu_{stamp}", limits, interpreter=args.interpreter)
        except RunnerError as error:
            result["refused"] = True
            result["refusal_reason"] = str(error)
            lib_iso.write_json(args.out, result)
            print(json.dumps({"tag": args.tag, "refused": True, "reason": str(error)}))
            return 2
        result["refused"] = False
        isolation = {k: v for k, v in run.record["isolation"].items() if k != "_verified_log"}
        log = (run.run_dir / "run.log").read_text(errors="replace") if (run.run_dir / "run.log").exists() else ""
        result.update({
            "run_dir": str(run.run_dir), "record": run.record, "isolation": isolation,
            "outcome": run.record.get("outcome"), "run_log": log,
            "result_channel": (run.run_dir / "result_channel.txt").read_text(errors="replace")
            if (run.run_dir / "result_channel.txt").exists() else None,
        })
        target = Path(args.out).parent / "records" / args.tag
        target.mkdir(parents=True, exist_ok=True)
        for name in ("run_record.json", "run.log", "result_channel.txt"):
            if (run.run_dir / name).exists():
                (target / name).write_bytes((run.run_dir / name).read_bytes())
        result["artifacts"] = [str(target / name) for name in ("run_record.json", "run.log", "result_channel.txt")
                               if (target / name).exists()]
        ipc_in_log = '"ipc_ok": true' in log
        result["condition_pass"] = bool((run.record.get("outcome") or {}).get("kind") == "ok"
                                        and isolation.get("worker_sandbox") is not None
                                        and isolation.get("exceptions") == ["shared_dev_shm"]
                                        and (isolation.get("waivers") == {} or bool(diag))
                                        and ipc_in_log)
    except Exception:  # noqa: BLE001
        result["error"] = traceback.format_exc()
        result["condition_pass"] = False
    result["gpu_after"] = gpu_facts()
    result["gpu_returned_idle"] = (result["gpu_after"].get("memory_used_mib", 1e9)
                                   <= (result["gpu_before"].get("memory_used_mib") or 0) + 64)
    lib_iso.write_json(args.out, result)
    print(json.dumps({"tag": args.tag, "refused": result.get("refused", False),
                      "plain_ipc_ok": control.get("plain_ipc_ok"),
                      "outcome": result.get("outcome"),
                      "exceptions": (result.get("isolation") or {}).get("exceptions"),
                      "waivers": (result.get("isolation") or {}).get("waivers"),
                      "condition_pass": result.get("condition_pass")}, default=str))
    if result.get("refused"):
        return 2
    return 0 if result.get("condition_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
