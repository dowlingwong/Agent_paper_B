#!/usr/bin/env python3
"""Render the S2-C2 HTCondor JDL from a validated job spec (fixed requirements template; ENGINEERING)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2_c2_lib as lib  # noqa: E402


def requirements(spec: dict) -> str:
    r = spec["requirements"]
    return " && ".join(f"({c})" for c in (
        'TARGET.CloudSite =?= "BwForCluster-Nemo2"',
        'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"',
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {r['min_cpus']}",
        f'regexp("{r["machine_regex"]}", TARGET.Machine)',
        "TARGET.ProvidesEtpCeph =?= True",
    ))


def render(spec: dict, name: str) -> str:
    img = spec["image"]["digest"]
    lines = [
        f"# S2-C2 sweep-2 chunk job (ENGINEERING; reviewed dry-run) — {spec['run_id']}/{spec['chunk_id']}",
        "universe = container",
        f"container_image = docker://{img}",
        "executable = s2_c2_job.sh",
        "arguments = s2_c2_spec.json",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['requirements']['min_cpus']}",
        "request_memory = 64000",
        "request_disk = 30000000",
        "request_GPUs = 1",
        f"+RequestWalltime = {spec.get('walltime_s', 7200)}",
        "+RemoteJob = True",
        f"requirements = {requirements(spec)}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "transfer_input_files = s2_c2_job.sh,s2_c2_lib.py,s2_c2_spec.json",
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text:
        raise lib.Stop("STOP: rendered JDL must not use docker_image or request a GPU share")
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="s2_c2_job")
    a = ap.parse_args(argv)
    spec = lib.validate_spec(lib.load_spec(Path(a.spec)))["spec"]
    Path(a.out).write_text(render(spec, a.name))
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
