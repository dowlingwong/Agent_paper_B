"""D.3 G1 direct SSH launcher — one process per chunk on the leased host.

ENGINEERING code (design revision 6b §2).  It starts the same
``r1.c3.d3.campaign_chunk`` entry as the HTCondor launcher, inside the host's delegated user
scope, after taking the card's lease with ``flock -n``.  The lease is held for the whole
chunk; a busy lease is a placement refusal, not a STOP.  The launcher writes the same
``launch.json``/``observed.json`` records the chunk validates and stages them with the chunk
invocation, so the remote directory is self-contained.

The card may be shared when the chunk's memory fits (R1-CARD-SHARE); the observed record's
``memory_check`` is required to be ``pass`` and its ``lease`` true.  The remote script
re-checks the lease, so a stale observed record cannot bypass it.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3.d3.launch import (
    LaunchStop, check_pin, chunk_argv, read_json, shell_join, utc_now, validate_launch, write_json,
)

DEFAULT_SCOPE = ("systemd-run --user --scope -p Delegate=yes -p MemoryMax=16G "
                 "-p MemorySwapMax=0")


def _heredoc(name: str, text: str) -> str:
    return f"cat > {shell_join([name])} <<'D3_FILE_EOF'\n{text.rstrip()}\nD3_FILE_EOF\n"


def render_remote_script(launch: Mapping[str, Any], *,
                         launch_text: str | None = None,
                         manifest_text: str | None = None,
                         observed_text: str | None = None,
                         probe: bool = False,
                         out_dir: str = "out",
                         lease_path: str | None = None,
                         scope: str = DEFAULT_SCOPE,
                         python: str = "python3") -> str:
    """The script ``ssh host bash -s`` runs; it is the only place the lease is taken."""
    launch = validate_launch(launch)
    if launch["launcher"] != "ssh":
        raise LaunchStop(f"this launcher writes ssh records, not {launch['launcher']!r}")
    lease = lease_path or launch.get("lease_path")
    if not lease:
        raise LaunchStop("an SSH launch needs a lease path (the card's gpu<index>.lock)")
    argv = chunk_argv("launch.json", out_dir, manifest_path="manifest.json",
                      observed_path="observed.json", python=python)
    parts = ["#!/bin/bash", "set -euo pipefail"]
    for name, text in (("launch.json", launch_text), ("manifest.json", manifest_text),
                       ("observed.json", observed_text)):
        if text is not None:
            parts.append(_heredoc(name, text))
    parts += [
        f"lease={shell_join([str(lease)])}",
        "if [ ! -e \"$lease\" ]; then echo 'STOP: the declared lease does not exist' >&2; exit 3; fi",
        "exec 9>\"$lease\"",
        "flock -n 9 || { echo 'STOP: the card lease is held by another job' >&2; exit 4; }",
        f"if [ -e {shell_join([str(out_dir)])} ]; then echo 'STOP: the chunk output exists' >&2; exit 5; fi",
    ]
    if probe:
        parts.append(f"python3 -m r1.c3.d3.probe --launch launch.json --manifest manifest.json "
                     f"--out observed.json --lease-path \"$lease\"")
    parts += [
        f"exec {scope} {shell_join(argv)}",
        "",
    ]
    return "\n".join(parts)


def check_observed(observed: Mapping[str, Any], *, lease_path: str | None) -> None:
    if observed.get("memory_check") != "pass":
        raise LaunchStop(f"the observed memory check is {observed.get('memory_check')!r}, not 'pass'")
    if observed.get("lease") is not True:
        raise LaunchStop("the observed record says the lease is not held")
    if lease_path and observed.get("lease_path") not in (None, lease_path):
        raise LaunchStop(f"observed lease {observed.get('lease_path')!r} differs from {lease_path!r}")


def launch(launch_path: str | Path, out_dir: str | Path, *, manifest_path: str | Path | None = None,
           observed_path: str | Path | None = None, host: str | None = None,
           lease_path: str | None = None, scope: str = DEFAULT_SCOPE,
           ssh: str = "ssh", dry_run: bool = False,
           runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Write the launch record and start the chunk on the host, unless ``dry_run``."""
    launch_record = read_json(launch_path)
    launch_record["launcher"] = "ssh"
    launch_record["scope"] = scope
    launch_record["request"] = None
    manifest = launch_record.get("manifest") or {}
    observed_pin = launch_record.get("observed") or {}
    manifest_path = manifest_path or manifest.get("path")
    probe = observed_pin.get("probe") is True
    observed_path = observed_path or observed_pin.get("path") or "observed.json"
    if not manifest_path:
        raise LaunchStop("the launch record must name its manifest")
    check_pin(manifest_path, manifest, "manifest")
    if not probe:
        check_pin(observed_path, observed_pin, "observed")
    host = host or str(launch_record.get("host") or "")
    if not host:
        raise LaunchStop("an SSH launch needs a host")
    lease = lease_path or launch_record.get("lease_path")
    if not lease:
        raise LaunchStop("an SSH launch needs a lease path")
    launch_record["lease_path"] = lease
    if not probe:
        observed = read_json(observed_path)
        check_observed(observed, lease_path=lease)
    out = Path(out_dir)
    if out.exists():
        raise LaunchStop(f"refusing an existing chunk directory {out}")
    write_json(out.parent / "launch.json", launch_record)
    remote_dir = str(launch_record.get("remote_dir") or out.parent)
    manifest_text = Path(manifest_path).read_text(encoding="utf-8")
    observed_text = None if probe else Path(observed_path).read_text(encoding="utf-8")
    script = render_remote_script(
        launch_record, launch_text=json.dumps(launch_record, indent=1, sort_keys=True) + "\n",
        manifest_text=manifest_text, observed_text=observed_text, probe=probe, out_dir=str(out),
        lease_path=lease, scope=scope)
    record = {
        "schema": "r1_d3_launch_submit/v1",
        "launcher": "ssh",
        "host": host,
        "lease_path": lease,
        "scope": scope,
        "request": None,
        "remote_dir": remote_dir,
        "dry_run": bool(dry_run),
        "created_utc": utc_now(),
    }
    write_json(out.parent / "ssh_launch_record.json", record)
    if dry_run:
        record["script"] = script
        return record
    run = runner or subprocess.run
    proc = run([ssh, host, f"mkdir -p {remote_dir} && cd {remote_dir} && bash -s"], input=script,
               capture_output=True, text=True)
    record["ssh_rc"] = int(getattr(proc, "returncode", 1))
    record["ssh_stdout"] = str(getattr(proc, "stdout", ""))
    record["ssh_stderr"] = str(getattr(proc, "stderr", ""))
    write_json(out.parent / "ssh_launch_record.json", record)
    if record["ssh_rc"] != 0:
        raise LaunchStop(f"the SSH chunk exited {record['ssh_rc']}: {record['ssh_stderr'].strip()}")
    return record
