"""D.3 G1 job-side hardware probe — the observed record a chunk validates.

ENGINEERING code (design revision 6b §3).  The probe runs at the start of a chunk, inside the
job's lease (SSH) or its scheduler assignment (HTCondor), and writes
``observed.json``: host, card model/UUID/driver, memory, the other compute processes (count
and memory only), the proposer identity and the launcher's request/scope.  The chunk then
refuses a model/proposer/lease/memory mismatch before a campaign directory exists.

The probe is the only producer of ``observed.json`` in a real launch.  A unit test injects a
runner; no GPU job, server, label or evaluation value is read here.
"""
from __future__ import annotations

import argparse
import os
import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from r1.c3.d3.launch import (
    LaunchStop, observed_record, parse_other_processes, read_json, utc_now, write_json,
)


def _run(argv: Sequence[str], **kwargs: Any) -> Any:
    return subprocess.run(list(argv), **kwargs)


def _csv_lines(text: str) -> list[list[str]]:
    rows = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append([p.strip() for p in line.split(",")])
    return rows


def parse_gpu(text: str) -> dict[str, Any]:
    """Parse ``name, uuid, driver_version, memory.total, memory.free`` (nounits)."""
    rows = _csv_lines(text)
    if not rows or len(rows[0]) < 5:
        raise LaunchStop(f"cannot read the GPU identity from {text!r}")
    name, uuid, driver, total, free = rows[0][:5]
    try:
        return {"model": name, "uuid": uuid, "driver": driver,
                "memory_total_mib": int(float(total)), "memory_free_mib": int(float(free))}
    except ValueError as exc:
        raise LaunchStop(f"cannot read GPU memory from {text!r}") from exc


def gpu_index_from_lease(lease_path: str | None) -> int:
    """Read the card index from a ``gpu<index>.lock`` lease; 0 when there is no indexed lease."""
    if not lease_path:
        return 0
    import re

    match = re.search(r"gpu(\d+)\.lock$", str(lease_path))
    return int(match.group(1)) if match else 0


def assigned_cuda_uuid() -> str:
    """Resolve the single CUDA-visible HTCondor assignment to the NVML device UUID."""
    import ctypes
    from uuid import UUID

    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if not visible or "," in visible:
        raise LaunchStop("the HTCondor job needs one CUDA_VISIBLE_DEVICES entry")
    try:
        driver = ctypes.CDLL("libcuda.so.1")
        count, device = ctypes.c_int(), ctypes.c_int()
        if driver.cuInit(0) != 0 or driver.cuDeviceGetCount(ctypes.byref(count)) != 0 or count.value != 1:
            raise LaunchStop("CUDA cannot confirm exactly one assigned proposer device")
        uuid_bytes = ctypes.create_string_buffer(16)
        if driver.cuDeviceGet(ctypes.byref(device), 0) != 0 or driver.cuDeviceGetUuid(uuid_bytes, device) != 0:
            raise LaunchStop("CUDA cannot resolve the assigned proposer device UUID")
    except (OSError, AttributeError) as exc:
        raise LaunchStop("the HTCondor job cannot load the CUDA device identity") from exc
    return f"GPU-{UUID(bytes=uuid_bytes.raw)}"


def probe(*, gpu_index: int | str = 0, required_memory_mib: int,
          proposer_model: str = "gemma4_31b", host: str | None = None,
          lease: bool = True, lease_path: str | None = None, lease_kind: str = "ssh",
          request: Mapping[str, Any] | None = None, scope: str | None = None,
          environment_freeze: Mapping[str, Any] | None = None,
          runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Sample the host and return the ``r1_d3_observed/v1`` record."""
    run = runner or _run
    host = host or socket.gethostname()
    gpu = run(["nvidia-smi", "-i", str(gpu_index),
               "--query-gpu=name,uuid,driver_version,memory.total,memory.free",
               "--format=csv,noheader,nounits"], capture_output=True, text=True)
    if int(getattr(gpu, "returncode", 1)) != 0:
        raise LaunchStop(f"nvidia-smi GPU query failed: {getattr(gpu, 'stderr', '').strip()}")
    gpu_info = parse_gpu(gpu.stdout)
    apps = run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
                "--format=csv,noheader,nounits"], capture_output=True, text=True)
    if int(getattr(apps, "returncode", 1)) != 0:
        raise LaunchStop(f"nvidia-smi compute-apps query failed: {getattr(apps, 'stderr', '').strip()}")
    other = parse_other_processes(apps.stdout, gpu_uuid=gpu_info["uuid"])
    return observed_record(
        host=host, model=gpu_info["model"], uuid=gpu_info["uuid"], driver=gpu_info["driver"],
        memory_total_mib=gpu_info["memory_total_mib"], memory_free_mib=gpu_info["memory_free_mib"],
        required_memory_mib=required_memory_mib, lease=lease, lease_path=lease_path,
        proposer_model=proposer_model, other_processes=other, request=request, scope=scope,
        environment_freeze=environment_freeze, chunk_start_utc=utc_now(),
        host_class=None,
    ) | {"lease_kind": lease_kind}


def probe_from_records(launch: Mapping[str, Any], manifest: Mapping[str, Any], *,
                       lease_path: str | None = None, runner: Callable[..., Any] | None = None,
                       gpu_index: int | None = None) -> dict[str, Any]:
    """Build the probe from a launch record and a campaign manifest.

    ``launch["hardware"]`` may carry ``required_memory_mib``; the manifest names the proposer.
    HTCondor has no lock file: its assignment is the reservation, so ``lease`` is true and
    ``lease_path`` is null (``lease_kind = "htcondor"``).
    """
    launcher = str(launch.get("launcher") or "")
    if launcher not in ("htcondor", "ssh", "direct"):
        raise LaunchStop(f"unknown launcher {launcher!r}")
    hardware = launch.get("hardware") or {}
    if hardware.get("required_memory_mib") is None:
        raise LaunchStop("the launch record must declare hardware.required_memory_mib")
    required = int(hardware["required_memory_mib"])
    proposer = str(manifest.get("proposer_model")
                   or (manifest.get("proposer") or {}).get("model")
                   or hardware.get("proposer_model") or "")
    if not proposer:
        raise LaunchStop("the manifest must name its proposer model")
    # Record the host the probe actually runs on, for every launcher; HTCondor chooses it and
    # SSH/direct target one host, which check_hardware then compares with the launch record.
    lease_kind = "htcondor" if launcher == "htcondor" else "lease"
    selector: int | str = gpu_index if gpu_index is not None else gpu_index_from_lease(lease_path)
    if launcher == "htcondor" and "retry_ledger" in launch:
        if gpu_index is not None:
            raise LaunchStop("deployment HTCondor probes the assigned card without an index override")
        selector = assigned_cuda_uuid()
    record = probe(gpu_index=selector, required_memory_mib=required, proposer_model=proposer,
                   host=None, lease=True, lease_path=lease_path, lease_kind=lease_kind,
                   request=launch.get("request"), scope=launch.get("scope"),
                   environment_freeze=hardware.get("environment_freeze"), runner=runner)
    if isinstance(selector, str) and record["gpu_uuid"] != selector:
        raise LaunchStop("the assigned CUDA device and observed GPU UUID differ")
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D.3 G1 job-side hardware probe (ENGINEERING)")
    ap.add_argument("--launch", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lease-path", default=None)
    ap.add_argument("--gpu-index", type=int, default=None,
                    help="card index; derived from a gpu<index>.lock lease when omitted")
    args = ap.parse_args(argv)
    launch = read_json(args.launch)
    manifest = read_json(args.manifest)
    record = probe_from_records(launch, manifest, lease_path=args.lease_path, gpu_index=args.gpu_index)
    write_json(args.out, record)
    print(json.dumps({key: record[key] for key in
                      ("host", "model", "gpu_uuid", "driver", "memory_check", "lease", "lease_kind")},
                     sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
