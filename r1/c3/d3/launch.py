"""D.3 G1 launch records and the two launchers' common helpers (design revision 6b).

ENGINEERING code.  The chunk lives in one place, :mod:`r1.c3.d3.campaign_chunk`; HTCondor and
direct SSH are only two ways to start it.  This module owns what both launchers must agree on:

* the ``r1_d3_launch/v1`` record and its validation (the signed W, LLM cap and 18 instance
  seeds are already enforced by :meth:`ChunkSpec.from_launch`; this module adds the launcher
  fields and refuses contradictory values);
* the exact argv both launchers pass to the chunk (parity, not duplication);
* the reviewed HTCondor request, which is compared, never rewritten;
* the card's other compute processes (count and memory only, R1-CARD-SHARE / revision 6b §3);
* the free-memory check and lease helpers used by the direct launcher.

No campaign, server, GPU job, label or evaluation value is read here.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

LAUNCH_SCHEMA = "r1_d3_launch/v1"
OBSERVED_SCHEMA = "r1_d3_observed/v1"
SUBMIT_SCHEMA = "r1_d3_htcondor_submit/v1"

#: The reviewed single-GPU preflight request (D3_HTCONDOR_PREFLIGHT_20261127).  A launcher may
#: not edit a value to obtain a slot; ``check_request`` refuses any difference.
D3_REQUEST: dict[str, Any] = {
    "universe": "container",
    "request_GPUs": 1,
    "request_cpus": 8,
    "request_memory_mb": 131072,
    "request_disk_kb": 150000000,
    "request_walltime_s": 3600,
}
D3_IMAGE = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949"

LAUNCHERS = ("htcondor", "ssh", "direct")
_REQUIRED = ("schema", "stage", "arm", "node", "repetition", "instance_seeds", "W",
             "llm_cap", "launcher", "host", "campaign_model_source", "manifest", "observed")


class LaunchStop(RuntimeError):
    """A refusal before execution: placement, lease, request or record problem."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LaunchStop(f"{path} is not a JSON object")
    return payload


def write_json(path: str | Path, payload: Mapping[str, Any]) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False, default=str) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_launch(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one launch record; returns a shallow copy with the launcher fields checked."""
    missing = [key for key in _REQUIRED if key not in record]
    if missing:
        raise LaunchStop(f"launch record misses {missing}")
    if record["schema"] != LAUNCH_SCHEMA:
        raise LaunchStop(f"unknown launch schema {record['schema']!r}; expected {LAUNCH_SCHEMA!r}")
    if record["launcher"] not in LAUNCHERS:
        raise LaunchStop(f"unknown launcher {record['launcher']!r}")
    pin = record.get("manifest")
    if not isinstance(pin, Mapping) or not pin.get("path") or not pin.get("sha256"):
        raise LaunchStop("launch record manifest must be {path, sha256}")
    observed = record.get("observed")
    if not isinstance(observed, Mapping) or not observed.get("path"):
        raise LaunchStop("launch record observed must be {path, sha256} or {path, probe: true}")
    if observed.get("probe") is not True and not observed.get("sha256"):
        raise LaunchStop("launch record observed must carry sha256 or probe: true")
    source = record.get("campaign_model_source")
    if not isinstance(source, Mapping) or not source.get("sha256"):
        raise LaunchStop("campaign_model_source must carry path and sha256")
    # The signed values live in one place: ChunkSpec.from_launch.  Import locally so the
    # launcher's record checks stay usable without a harness checkout.
    from r1.c3.d3.campaign_chunk import ChunkSpec, ChunkStop

    try:
        ChunkSpec.from_launch(record)
    except ChunkStop as exc:
        raise LaunchStop(str(exc)) from exc
    return dict(record)


def validate_deployment_launch(record: Mapping[str, Any]) -> dict[str, Any]:
    """Require the live reservation and retry ledger on the deployment path."""
    from r1.c3.d3.evidence_accounting import AccountingStop, check_retry_ledger

    launch = validate_launch(record)
    if launch["launcher"] not in ("htcondor", "ssh") or launch["observed"].get("probe") is not True:
        raise LaunchStop("deployment accounting needs the live HTCondor or SSH reservation probe")
    try:
        check_retry_ledger(launch)
    except AccountingStop as exc:
        raise LaunchStop(str(exc)) from exc
    return launch


def check_pin(path: str | Path, pin: Mapping[str, Any], what: str) -> str:
    """Hash a launch input and refuse a mismatch with its recorded pin."""
    if not isinstance(pin, Mapping) or not pin.get("sha256"):
        raise LaunchStop(f"{what} has no sha256 pin")
    got = sha256_file(path)
    if got != str(pin["sha256"]):
        raise LaunchStop(f"{what} sha256 mismatch: {got} != {pin['sha256']}")
    return got


def check_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Refuse any scheduler request other than the reviewed one (no request edited for a slot)."""
    got = dict(request or {})
    if set(got) != set(D3_REQUEST):
        extra = sorted(set(got) - set(D3_REQUEST))
        missing = sorted(set(D3_REQUEST) - set(got))
        raise LaunchStop(f"the HTCondor request must carry exactly {sorted(D3_REQUEST)}; extra={extra} missing={missing}")
    wrong = {key: (got[key], D3_REQUEST[key]) for key in D3_REQUEST if got[key] != D3_REQUEST[key]}
    if wrong:
        raise LaunchStop(f"the HTCondor request differs from the reviewed one: {wrong}")
    return got


def chunk_argv(launch_path: str | Path, out_dir: str | Path, *,
               manifest_path: str | Path, observed_path: str | Path,
               python: str | None = None) -> list[str]:
    """The one argv both launchers pass to the chunk script (design revision 6b §2)."""
    return [python or sys.executable, "-m", "r1.c3.d3.campaign_chunk",
            "--launch", str(launch_path), "--out", str(out_dir),
            "--manifest", str(manifest_path), "--observed", str(observed_path)]


def shell_join(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(a)) for a in argv)


def parse_other_processes(text: str, *, gpu_uuid: str | None = None) -> dict[str, Any]:
    """Parse ``nvidia-smi --query-compute-apps`` output.

    The record keeps only the count and total memory (revision 6b §3; R1-CARD-SHARE): no
    other user's pid, command line or identity is stored.  With ``gpu_uuid`` a three-column
    ``gpu_uuid,pid,used_memory`` query is filtered to that card.
    """
    count = 0
    total = 0
    unknown = 0
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.lower().startswith("pid") or line.lower().startswith("gpu_uuid"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        if gpu_uuid and len(parts) >= 3 and parts[0] != gpu_uuid:
            continue
        value = parts[-1].replace("MiB", "").strip()
        if value in ("", "N/A", "[N/A]", "Not Supported"):
            count += 1
            unknown += 1
            continue
        try:
            total += int(float(value))
        except ValueError as exc:
            raise LaunchStop(f"cannot read a compute-process memory value from {line!r}") from exc
        count += 1
    return {"count": count, "used_memory_mib": total, "unknown_memory_count": unknown}


def memory_fit(required_mib: int, free_mib: int) -> str:
    """The revision-6b memory check: a shared card is allowed when the memory fits."""
    if int(required_mib) <= 0:
        raise LaunchStop("required_memory_mib must be positive")
    return "pass" if int(free_mib) >= int(required_mib) else "fail"


def lease_held(path: str | Path, *, runner: Callable[..., Any] | None = None) -> bool:
    """True when the lease can be taken now; the probe releases it immediately.

    ``runner`` may supply an OS command (the hosts have ``flock``); the default uses
    ``fcntl`` so the helper also works on the Mac.  A missing directory is a refusal.
    """
    path = Path(path)
    if not path.parent.is_dir():
        raise LaunchStop(f"lease directory does not exist: {path.parent}")
    if runner is not None:
        proc = runner(["flock", "-n", str(path), "true"], capture_output=True, text=True)
        return int(getattr(proc, "returncode", 1)) == 0
    import fcntl

    path.touch(exist_ok=True)
    with path.open("r+") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    return True


def observed_record(*, host: str, model: str, uuid: str, driver: str,
                    memory_total_mib: int, memory_free_mib: int, required_memory_mib: int,
                    lease: bool, lease_path: str | None, proposer_model: str,
                    other_processes: Mapping[str, Any], host_class: str | None = None,
                    request: Mapping[str, Any] | None = None,
                    scope: str | None = None,
                    environment_freeze: Mapping[str, Any] | None = None,
                    chunk_start_utc: str | None = None) -> dict[str, Any]:
    """Build the observed hardware record the chunk validates before a campaign."""
    check = memory_fit(required_memory_mib, memory_free_mib)
    return {
        "schema": OBSERVED_SCHEMA,
        "host": host,
        "host_class": host_class,
        "model": model,
        "gpu_uuid": uuid,
        "driver": driver,
        "memory_total": int(memory_total_mib),
        "memory_free": int(memory_free_mib),
        "required_memory_mib": int(required_memory_mib),
        "memory_check": check,
        "lease": bool(lease),
        "lease_path": lease_path,
        "proposer_model": proposer_model,
        "other_processes_start": dict(other_processes or {"count": 0, "used_memory_mib": 0}),
        "other_processes_end": None,
        "request": dict(request) if request is not None else None,
        "scope": scope,
        "environment_freeze": dict(environment_freeze or {}),
        "chunk_start_utc": chunk_start_utc,
    }


def write_launch(path: str | Path, record: Mapping[str, Any]) -> str:
    """Validate and write a launch record; refuses a launcher field that contradicts its file."""
    payload = validate_launch(record)
    return write_json(path, payload)


def _run(argv: Sequence[str], **kwargs: Any) -> Any:
    import subprocess

    return subprocess.run(list(argv), **kwargs)
