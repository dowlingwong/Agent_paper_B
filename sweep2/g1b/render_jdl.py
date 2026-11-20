#!/usr/bin/env python3
"""Stage the G.1b H200 job files and render one HTCondor JDL per T1 node (no submission here).

``render_jdl.py <spec> <stage_dir>`` validates the spec at launch strength (no placeholder), copies
``g1b_job.sh``, ``g1b_lib.py`` and the spec into an empty stage directory and writes ``g1b_<node>.jdl`` plus
``STAGE_MANIFEST.json`` (sha256 of every staged file and JDL).  ``--preview`` renders from a spec that still
holds launch placeholders; the preview JDLs carry ``PREVIEW_NOT_SUBMITTABLE`` in their executable line, so
``condor_submit`` refuses them, and the manifest says ``preview: true``.  The submission itself goes through
the two-key switch ``g1b_switch.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_lib as lib  # noqa: E402

STAGED = ("g1b_job.sh", "g1b_lib.py")


def requirements(spec: dict) -> str:
    return " && ".join(f"({c})" for c in (
        "TARGET.GPUs >= 1",
        f'TARGET.GPUs_DeviceName =?= "{lib.GPU_MODEL}"',
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {spec['layout']['request_cpus']}",
    ))


def render(spec: dict, node: dict, *, preview: bool = False) -> str:
    name = f"g1b_{node['node']}"
    executable = "PREVIEW_NOT_SUBMITTABLE_g1b_job.sh" if preview else "g1b_job.sh"
    lines = [
        f"# G.1b T1 noise floor on {lib.GPU_MODEL} (ENGINEERING_ONLY) — {spec['run_id']}/{node['node']}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        f"executable = {executable}",
        f"arguments = g1b_spec.json {node['node']}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['layout']['request_cpus']}",
        f"request_memory = {spec['layout']['request_memory_mb']}",
        f"request_disk = {spec['layout']['request_disk_kb']}",
        "request_GPUs = 1",
        f"+RequestWalltime = {lib.node_walltime(node, spec['layout'])}",
        "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42",
        f"requirements = {requirements(spec)}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT_OR_EVICT",
        "transfer_input_files = g1b_job.sh,g1b_lib.py,g1b_spec.json",
        f"transfer_output_files = {lib.TRANSFER_OUTPUTS}",
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text or "ProvidesEtpCeph" in text:
        raise lib.Stop("STOP: the JDL must not use docker_image, a GPU share or ProvidesEtpCeph")
    return text


def stage(spec_path: Path, stage_dir: Path, *, preview: bool = False) -> dict:
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_spec(spec, launch=not preview)
    stage_dir = Path(stage_dir)
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise lib.Stop(f"STOP: stage directory {stage_dir} is not empty (no overwrite)")
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in STAGED:
        shutil.copy2(HERE / name, stage_dir / name)
    shutil.copy2(spec_path, stage_dir / "g1b_spec.json")
    files = {}
    for node in spec["nodes"]:
        path = stage_dir / f"g1b_{node['node']}.jdl"
        path.write_text(render(spec, node, preview=preview))
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in (*STAGED, "g1b_spec.json"):
        files[name] = hashlib.sha256((stage_dir / name).read_bytes()).hexdigest()
    manifest = {"schema": "g1b_h200_stage/1", "run_id": loaded["run_id"], "preview": preview,
                "projection": loaded["projection"], "files": files}
    (stage_dir / "STAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("stage_dir", type=Path)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(stage(a.spec, a.stage_dir, preview=a.preview), indent=1))
    except lib.Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
