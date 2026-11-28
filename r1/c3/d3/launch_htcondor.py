"""D.3 G1 HTCondor launcher — one job per (stage, node, arm, repetition) chunk.

ENGINEERING code (design revision 6b §2).  The job runs the same
``r1.c3.d3.campaign_chunk`` entry as the direct SSH launcher.  The scheduler request is the
reviewed one and is compared, never edited; a mismatch is a refusal before submission.

The job needs the paper code.  ``launch["staging"]["repo_tarball"]`` pins the tarball it
transfers; ``d3_chunk.sh`` unpacks it and sets ``PYTHONPATH``.  No sealed file, label or
evaluation value is transferred by this module.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from r1.c3.d3.launch import (
    D3_IMAGE, D3_REQUEST, LaunchStop, check_pin, check_request, chunk_argv, read_json,
    sha256_file, shell_join, utc_now, validate_deployment_launch, validate_launch, write_json,
)

SUBMIT_NAME = "d3_chunk.sub"
WRAPPER_NAME = "d3_chunk.sh"


def _check_staging(launch: Mapping[str, Any]) -> Mapping[str, Any]:
    staging = launch.get("staging")
    if not isinstance(staging, Mapping):
        raise LaunchStop("an HTCondor launch needs staging.repo_tarball")
    pin = staging.get("repo_tarball")
    if not isinstance(pin, Mapping) or not pin.get("path") or not pin.get("sha256"):
        raise LaunchStop("staging.repo_tarball must be {path, sha256}")
    path = Path(str(pin["path"]))
    if not path.is_file():
        raise LaunchStop(f"repo tarball not found: {path}")
    digest = sha256_file(path)
    if digest != str(pin["sha256"]):
        raise LaunchStop(f"repo tarball sha256 mismatch: {digest} != {pin['sha256']}")
    return staging


def wrapper_script(*, probe: bool = True) -> str:
    """The job-side wrapper: stage the repo, probe the assigned card, then run the chunk."""
    probe_line = (
        "python3 -m r1.c3.d3.probe --launch launch.json --manifest manifest.json "
        "--out observed.json\n" if probe else ""
    )
    return (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "mkdir -p repo\n"
        "tar -xzf repo.tar -C repo\n"
        "export PYTHONPATH=\"$PWD/repo${PYTHONPATH:+:$PYTHONPATH}\"\n"
        + probe_line +
        "exec python3 -m r1.c3.d3.campaign_chunk \"$@\"\n"
    )


def render_submit(launch: Mapping[str, Any], *, submit_dir: str | Path,
                  request: Mapping[str, Any] | None = None,
                  image: str = D3_IMAGE) -> str:
    """Render the submit description; the request and the chunk argv are fixed here."""
    launch = validate_launch(launch)
    if launch["launcher"] != "htcondor":
        raise LaunchStop(f"this launcher writes htcondor records, not {launch['launcher']!r}")
    _check_staging(launch)
    req = check_request(request or D3_REQUEST)
    submit_dir = Path(submit_dir)
    argv = chunk_argv("launch.json", "out", manifest_path="manifest.json",
                      observed_path="observed.json", python="python3")
    model = str(launch.get("campaign_model_source", {}).get("model") or "").strip()
    lines = [
        f"# D.3 G1 chunk {launch['stage']}/{launch['node']}/{launch['arm']}/r{launch['repetition']}",
        f"# written {utc_now()} by r1/c3/d3/launch_htcondor.py",
        "universe = container",
        f"container_image = docker://{image}",
        f"executable = {WRAPPER_NAME}",
        f"arguments = {shell_join(argv[1:])}",
    ]
    if model:
        lines.append(f'requirements = (TARGET.GPUs_DeviceName =?= "{model}")')
    lines += [
        "+RemoteJob = True",
        f"request_GPUs = {req['request_GPUs']}",
        f"request_cpus = {req['request_cpus']}",
        f"request_memory = {req['request_memory_mb']}",
        f"request_disk = {req['request_disk_kb']}",
        f"+RequestWalltime = {req['request_walltime_s']}",
        "periodic_hold = (NumJobStarts > 1)",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "output = d3_chunk.out",
        "error = d3_chunk.err",
        "log = d3_chunk.log",
        "transfer_input_files = " + ",".join(
            [WRAPPER_NAME, "launch.json", "manifest.json", "repo.tar"]
            + ([] if (launch.get("observed") or {}).get("probe") is True else ["observed.json"])),
        "transfer_output_files = out",
        "queue 1",
        "",
    ]
    return "\n".join(lines)


def parse_cluster_id(text: str) -> str:
    match = re.search(r"(\d+) job\(s\) submitted to cluster (\d+)", str(text))
    if not match:
        raise LaunchStop(f"cannot read a cluster id from condor_submit output: {text!r}")
    return match.group(2)


def submit(launch_path: str | Path, out_dir: str | Path, *, submit_dir: str | Path | None = None,
           manifest_path: str | Path | None = None, observed_path: str | Path | None = None,
           request: Mapping[str, Any] | None = None, image: str = D3_IMAGE,
           condor_submit: str = "condor_submit", dry_run: bool = False,
           runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Write the launch/submit records and submit, unless ``dry_run``."""
    launch = read_json(launch_path)
    launch["launcher"] = "htcondor"
    launch["request"] = check_request(request or D3_REQUEST)
    launch["scope"] = None
    if "lease_path" not in launch:
        launch["lease_path"] = None
    manifest = launch.get("manifest") or {}
    observed = launch.get("observed") or {}
    manifest_path = manifest_path or manifest.get("path")
    observed_path = observed_path or observed.get("path")
    if not manifest_path or not observed_path:
        raise LaunchStop("the launch record must name its manifest and observed files")
    check_pin(manifest_path, manifest, "manifest")
    probe = observed.get("probe") is True
    if not dry_run or "retry_ledger" in launch:
        launch = validate_deployment_launch(launch, source_dir=Path(launch_path).parent)
    if not probe:
        check_pin(observed_path, observed, "observed")
    out = Path(out_dir)
    if out.exists():
        raise LaunchStop(f"refusing an existing chunk directory {out}")
    submit_dir = Path(submit_dir) if submit_dir is not None else out.parent / "submit"
    try:
        submit_dir.mkdir(parents=True)
    except FileExistsError as exc:
        raise LaunchStop(f"the attempt submit directory already exists: {submit_dir}") from exc
    # The job sees these at its own relative names; the launch record's pins stay intact.
    (submit_dir / "manifest.json").write_bytes(Path(manifest_path).read_bytes())
    if not probe:
        (submit_dir / "observed.json").write_bytes(Path(observed_path).read_bytes())
    launch_file = submit_dir / "launch.json"
    write_json(launch_file, launch)
    (submit_dir / WRAPPER_NAME).write_text(wrapper_script(probe=probe), encoding="utf-8")
    staging = _check_staging(launch)
    repo = Path(str(staging["repo_tarball"]["path"]))
    (submit_dir / "repo.tar").write_bytes(repo.read_bytes())
    text = render_submit(launch, submit_dir=submit_dir, request=launch["request"], image=image)
    submit_file = submit_dir / SUBMIT_NAME
    submit_file.write_text(text, encoding="utf-8")
    result: dict[str, Any] = {
        "schema": "r1_d3_launch_submit/v1",
        "launcher": "htcondor",
        "submit_file": str(submit_file),
        "submit_sha256": sha256_file(submit_file),
        "request": dict(launch["request"]),
        "dry_run": bool(dry_run),
        "created_utc": utc_now(),
    }
    if dry_run:
        return result
    run = runner or subprocess.run
    proc = run([condor_submit, submit_file.name], capture_output=True, text=True, cwd=submit_dir)
    result["condor_submit_rc"] = int(getattr(proc, "returncode", 1))
    result["condor_submit_stdout"] = str(getattr(proc, "stdout", ""))
    result["condor_submit_stderr"] = str(getattr(proc, "stderr", ""))
    if result["condor_submit_rc"] != 0:
        raise LaunchStop(f"condor_submit failed: {result['condor_submit_stderr'].strip()}")
    result["cluster_id"] = parse_cluster_id(result["condor_submit_stdout"])
    write_json(submit_dir / "submit_record.json", result)
    return result
