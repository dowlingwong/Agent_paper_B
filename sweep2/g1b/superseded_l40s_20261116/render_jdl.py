#!/usr/bin/env python3
"""Render the G.1b noise-floor chunk JDL (fixed HTCondor template; ENGINEERING_ONLY) and stage its inputs.

The reviewed S2-C2 pattern is reused: `universe = container`, the frozen v1 GPU image digest, `+RemoteJob = True`,
NEMO2 L40S + CPU-class requirements (CpuFamily 6 / CpuModelNumber 207 / model-name string), outputs transferred as
`out.tar` + `job_record.json` + `SHA256SUMS` + `g1b_run.log` (NEMO2 slots do not advertise ProvidesEtpCeph, so the
container writes only its sandbox and the operator seals later), and no `machine_regex` requirement.

Two modes:
  --layout-preview   render the NOT-RUNNABLE layout-preview JDL from the placeholder template into g1b_dryrun/ only;
                     used for the committed `condor_submit -dry-run` evidence while G.0 has not named the nodes.
  (default)          require a complete, valid chunk spec (G.0 census filled, no placeholders) and render a real JDL.

A preview JDL is deliberately not submittable: its spec is the placeholder template, so the container entry STOPs at
spec validation before it touches the GPU. The renderer refuses to write a preview JDL outside `g1b_dryrun/`.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_lib as lib  # noqa: E402

TEMPLATE = HERE / "g1b_spec.template.json"
PREVIEW_DIR = HERE / "g1b_dryrun"
PREVIEW_RUN_SECONDS = 120.0  # R1-BX-D5 label-run upper bound, used ONLY for the layout preview
OUTPUTS = lib.TRANSFER_OUTPUTS


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


def render(spec: dict, node: dict, chunk: dict, name: str, inputs: list[str], *, preview: bool) -> str:
    header = ("# G.1b T1 GPU-node noise-floor chunk (ENGINEERING_ONLY; prepared, NOT RUN) — "
              f"{spec.get('run_id')}/{chunk['chunk_id']}")
    if preview:
        header += "\n# LAYOUT PREVIEW ONLY — the G.0 census has not named the candidate nodes yet. NOT FOR SUBMISSION:" \
                  "\n# the staged spec is the placeholder template and the container entry STOPs at spec validation."
    lines = [
        header,
        "universe = container",
        f"container_image = docker://{lib.IMAGE_DIGEST}",
        "executable = g1b_job.sh",
        "arguments = g1b_spec.json",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {lib.MIN_CPUS}",
        f"request_memory = {int(node['request_memory_mb'])}",
        f"request_disk = {int(node['request_disk_kb'])}",
        "request_GPUs = 1",
        f"+RequestWalltime = {int(chunk['walltime_s'])}",
        "+RemoteJob = True",
        f"requirements = {requirements()}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "transfer_input_files = " + ",".join(inputs),
        "transfer_output_files = " + OUTPUTS,
        "queue 1",
    ]
    if preview:
        lines.insert(lines.index("+RemoteJob = True") + 1, "+G1BPreview = True")
    text = "\n".join(lines) + "\n"
    for banned in ("docker_image", "RequestGPUMemory", "ProvidesEtpCeph", "machine_regex"):
        if banned in text:
            raise lib.Stop(f"STOP: rendered JDL must not contain {banned!r}")
    return text


def render_from_template() -> tuple[dict, dict, dict]:
    """Build the layout-preview chunk from the placeholder template (no validation: the template is a placeholder)."""
    spec = json.loads(TEMPLATE.read_text())
    spec = copy.deepcopy(spec)
    for node in spec["plan"]["candidate_nodes"]:
        node["run_seconds"] = PREVIEW_RUN_SECONDS
        node["request_memory_mb"] = lib.MEMORY_FLOOR_MB
        node["request_disk_kb"] = lib.DISK_FLOOR_KB
    chunks = lib.chunk_plan(spec["plan"])
    chunk = max(chunks, key=lambda c: c["walltime_s"])
    node = next(n for n in spec["plan"]["candidate_nodes"] if n["node_id"] == chunk["node"])
    return spec, node, chunk


def _stage(stage: Path, spec: dict) -> list[str]:
    if stage.exists():
        raise lib.Stop(f"STOP: stage dir {stage} already exists (fresh staging required)")
    stage.mkdir(parents=True, mode=0o700)
    for name in ("g1b_job.sh", "g1b_lib.py"):
        shutil.copy2(HERE / name, stage / name)
    (stage / "g1b_spec.json").write_text(json.dumps(spec, indent=1) + "\n")
    return sorted(p.name for p in stage.iterdir() if p.is_file())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--name", default="g1b_job")
    ap.add_argument("--layout-preview", action="store_true",
                    help="render the placeholder layout preview into g1b_dryrun/ (not submittable)")
    a = ap.parse_args(argv)
    out_path = Path(a.out).resolve()
    stage = Path(a.stage_dir).resolve()
    if a.layout_preview:
        if out_path.parent != PREVIEW_DIR.resolve():
            raise lib.Stop(f"STOP: a layout-preview JDL may only be written under {PREVIEW_DIR}")
        if stage.exists() and any(stage.iterdir()):
            raise lib.Stop("STOP: preview stage dir must be fresh")
        spec, node, chunk = render_from_template()
        inputs = _stage(stage, spec)
        out_path.write_text(render(spec, node, chunk, a.name, inputs, preview=True))
        print(out_path)
        return 0
    loaded = lib.validate_spec(lib.load_spec(Path(a.spec)))
    spec, node, chunk = loaded["spec"], next(
        n for n in loaded["plan"]["candidate_nodes"] if n["node_id"] == loaded["chunk"]["node"]
    ), loaded["chunk"]
    inputs = _stage(stage, spec)
    if "g1b_spec.json" not in inputs or "g1b_job.sh" not in inputs or "g1b_lib.py" not in inputs:
        raise lib.Stop("STOP: staged inputs incomplete")
    out_path.write_text(render(spec, node, chunk, a.name, inputs, preview=False))
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
