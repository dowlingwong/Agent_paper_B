#!/usr/bin/env python3
"""Stage the S2-C2 / S2-C3b job files and render the HTCondor JDL (fixed requirements template; ENGINEERING).

The container job writes only into its HTCondor sandbox; the listed output files are transferred back to the
submit host and the reviewed `seal` step copies them into the sealed /ceph path (NEMO2 slots do not advertise
ProvidesEtpCeph). The authorization note, when the spec pins one, is staged and added to transfer_input_files.

`--kind c2` (default) stages the accepted S2-C2 sweep-2 chunk/liveness wrapper; `--kind c3b` stages the S2-C3b
(g)4 D28-liveness + prompt-length wrapper (which also needs `s2_c2_lib.py`, imported for the shared pins/seal).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402

OUTPUTS = "out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log"

KINDS = {
    "c2": {"title": "S2-C2 sweep-2 chunk job (ENGINEERING; reviewed dry-run)",
           "executable": "s2_c2_job.sh", "spec_name": "s2_c2_spec.json", "name": "s2_c2_job",
           "files": ("s2_c2_job.sh", "s2_c2_lib.py")},
    "c3b": {"title": "S2-C3b (g)4 D28 liveness + prompt re-measurement (ENGINEERING_ONLY; reviewed dry-run)",
            "executable": "s2_c3b_job.sh", "spec_name": "s2_c3b_spec.json", "name": "s2_c3b_job",
            "files": ("s2_c3b_job.sh", "s2_c3b_lib.py", "s2_c2_lib.py")},
}


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


def render(spec: dict, name: str, inputs: list[str], kind: str = "c2") -> str:
    layout = KINDS[kind]
    lines = [
        f"# {layout['title']} — {spec['run_id']}/{spec['chunk_id']}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        f"executable = {layout['executable']}",
        f"arguments = {layout['spec_name']}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {lib.MIN_CPUS}",
        f"request_memory = {spec['request_memory_mb']}",
        f"request_disk = {spec['request_disk_kb']}",
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
    if kind == "c3b" and "s2_c3b_lib.py" not in inputs:
        raise lib.Stop("STOP: the c3b JDL must stage s2_c3b_lib.py")
    return text


def _c3b_validate(spec_path: Path) -> None:
    import s2_c3b_lib as c3b  # local import: the C2 path must not depend on the c3b module
    c3b.validate_spec(c3b.load_spec(spec_path))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--kind", choices=sorted(KINDS), default="c2")
    ap.add_argument("--auth-note", default=None, help="source authorization note to stage (required for EVIDENCE)")
    a = ap.parse_args(argv)
    layout = KINDS[a.kind]
    name = a.name or layout["name"]
    spec = lib.load_spec(Path(a.spec)) if a.kind == "c2" else None
    if a.kind == "c3b":
        import s2_c3b_lib as c3b
        spec = c3b.load_spec(Path(a.spec))
    stage = Path(a.stage_dir).resolve()
    out_path = Path(a.out).resolve()
    if stage.exists():
        raise lib.Stop(f"STOP: stage dir {stage} already exists (fresh staging required)")
    stage.mkdir(parents=True, mode=0o700)
    for filename in layout["files"]:
        shutil.copy2(HERE / filename, stage / filename)
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
    (stage / layout["spec_name"]).write_text(json.dumps(spec, indent=1) + "\n")
    cwd = os.getcwd()
    try:
        os.chdir(stage)
        if a.kind == "c3b":
            _c3b_validate(stage / layout["spec_name"])
        else:
            lib.validate_spec(lib.load_spec(stage / layout["spec_name"]))
    finally:
        os.chdir(cwd)
    inputs = sorted(p.name for p in stage.iterdir() if p.is_file())
    if layout["spec_name"] not in inputs:
        raise lib.Stop("STOP: staged inputs incomplete")
    for filename in layout["files"]:
        if filename not in inputs:
            raise lib.Stop(f"STOP: staged inputs incomplete: {filename} missing")
    out_path.write_text(render(spec, name, inputs, a.kind))
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
