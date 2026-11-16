#!/usr/bin/env python3
"""Stage the S2-C2 job files and render its HTCondor JDL (fixed requirements template; ENGINEERING).

The container job writes only into its HTCondor sandbox; the listed output files are transferred back to the
submit host and the reviewed `seal` step copies them into the sealed /ceph path (NEMO2 slots do not advertise
ProvidesEtpCeph). The authorization note, when the spec pins one, is staged and added to transfer_input_files.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402

OUTPUTS = "out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log"


def requirements() -> str:
    return " && ".join(f"({c})" for c in (
        f'TARGET.CloudSite =?= "{lib.CLOUD_SITE}"',
        f'TARGET.GPUs_DeviceName =?= "{lib.GPU_MODEL}"',
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {lib.MIN_CPUS}",
        f"TARGET.CpuFamily =?= {lib.CPU_FAMILY}",
        f"TARGET.CpuModelNumber =?= {lib.CPU_MODEL_NUMBER}",
    ))


def render(spec: dict, name: str, inputs: list[str]) -> str:
    lines = [
        f"# S2-C2 sweep-2 chunk job (ENGINEERING; reviewed dry-run) — {spec['run_id']}/{spec['chunk_id']}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        "executable = s2_c2_job.sh",
        "arguments = s2_c2_spec.json",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {lib.MIN_CPUS}",
        "request_memory = 128000",
        "request_disk = 50000000",
        "request_GPUs = 1",
        f"+RequestWalltime = {spec['walltime_s']}",
        "+RemoteJob = True",
        f"requirements = {requirements()}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "transfer_input_files = " + ",".join(inputs),
        "transfer_output_files = " + OUTPUTS,
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text or "ProvidesEtpCeph" in text:
        raise lib.Stop("STOP: rendered JDL must not use docker_image, request a GPU share, or require ProvidesEtpCeph")
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--name", default="s2_c2_job")
    ap.add_argument("--auth-note", default=None, help="source authorization note to stage (required for EVIDENCE)")
    a = ap.parse_args(argv)
    spec = lib.load_spec(Path(a.spec))
    stage = Path(a.stage_dir).resolve()
    out_path = Path(a.out).resolve()
    if stage.exists():
        raise lib.Stop(f"STOP: stage dir {stage} already exists (fresh staging required)")
    stage.mkdir(parents=True, mode=0o700)
    for name in ("s2_c2_job.sh", "s2_c2_lib.py"):
        shutil.copy2(HERE / name, stage / name)
    src = spec.get("label_source") or {}
    auth = src.get("authorization")
    if auth is not None:
        if Path(auth).name != auth or "/" in auth or "\\" in auth:
            raise lib.Stop("STOP: label_source.authorization must be a bare basename")
        if a.auth_note is None:
            raise lib.Stop("STOP: spec pins an authorization note; --auth-note is required to stage it")
        note = Path(a.auth_note)
        if not note.is_file():
            raise lib.Stop(f"STOP: authorization note {note} missing")
        shutil.copy2(note, stage / Path(auth).name)
        src["authorization"] = Path(auth).name
        spec["label_source"] = src
    (stage / "s2_c2_spec.json").write_text(json_dumps(spec))
    cwd = os.getcwd()
    try:
        os.chdir(stage)
        lib.validate_spec(lib.load_spec(stage / "s2_c2_spec.json"))
    finally:
        os.chdir(cwd)
    inputs = sorted(p.name for p in stage.iterdir() if p.is_file())
    if "s2_c2_spec.json" not in inputs or "s2_c2_job.sh" not in inputs:
        raise lib.Stop("STOP: staged inputs incomplete")
    out_path.write_text(render(spec, a.name, inputs))
    print(out_path)
    return 0


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, indent=1) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
