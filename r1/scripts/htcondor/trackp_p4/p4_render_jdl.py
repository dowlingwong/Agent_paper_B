#!/usr/bin/env python3
"""Stage the Track P P.4 phase-1 job files and render one HTCondor JDL per base (no submission here).
ENGINEERING_ONLY; AI-assisted (Claude).

``p4_render_jdl.py <spec> <stage_dir> --table <table dir> --partition <release>/sweep1/traindev`` validates the spec
at launch strength (no placeholder), copies ``p4_job.sh``, ``p4_lib.py`` and the spec into an empty stage
directory, copies the transferred inputs (the table's ``proposals.jsonl``, ``configs.json`` and ``build.json``, the
receipted partition and its ``RECEIPT.json``), checks them against the spec's pins (the partition and receipt
sha256 and the frozen source block; the table files against the SFT config's ``sweep1_v3`` pins), and writes
``p4_<arm>.jdl`` plus ``STAGE_MANIFEST.json`` (sha256 of every staged file and JDL). ``--preview`` renders from a spec
that still holds launch placeholders; the preview JDLs carry ``PREVIEW_NOT_SUBMITTABLE`` in their executable line
and the manifest says ``preview: true``. The submission goes through the two-key switch ``p4_switch.py``.

P4-F2 A (R1-P4-TESTPLAN-DECISIONS): the render (preview or not) also checks the receipt's table: its
``inputs.proposals_sha256`` must be the sealed v2 table, bound to the staged ``sweep1_v3`` table by A3's FEAT-ONE
identity check (``p4_phase1.check_receipt_table`` with the committed identity result of this checkout), so T5 and T8
refuse what every job would refuse at step 5. No label row is read here; the join by proposal id runs in the job.

**Probe stage** (cluster test plan §4.2; P4-PROBE A): ``p4_render_jdl.py <filled probe spec> <stage_dir> --table
<table dir> --probe --arm <arm> [--first-record <sealed first-arm probe job_record.json>]`` validates the probe spec at
probe strength, requires it to differ from the committed template ``p4_probe_spec.json`` only in its three host fields,
stages ``p4_probe.sh``, ``p4_lib.py``, the spec (as ``p4_probe_spec.json``) and the three table files (no label file,
no receipt), and renders one ``p4probe_<arm>.jdl``: the fixed lines of ``render`` (container universe, the v2.2
digest, one GPU, the H200 requirement, the no-resume hold, the ``layout`` request), its own executable, arguments and
transfer lists, and ``+RequestWalltime`` = the probe's ``walltime_s``. ``kev-0.8b`` is staged alone first; another base
needs the first arm's sealed, STOP-free probe record (``p4_lib.check_first_probe_record``). Submission is by hand
(``condor_submit``), after the pre-submit check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]          # data read from the checkout (the SFT config, the FEAT-ONE identity result)
CODE_ROOT = HERE.parents[3]          # code imported from the checkout (r1.c3.train.p4_phase1)
sys.path.insert(0, str(HERE))
import p4_lib as lib  # noqa: E402

STAGED = ("p4_job.sh", "p4_lib.py")
TABLE_FILES = ("proposals.jsonl", "configs.json", "build.json")
PARTITION_FILES = ("label_block.traindev.jsonl", "RECEIPT.json")


def requirements(spec: dict) -> str:
    return " && ".join(f"({c})" for c in (
        "TARGET.GPUs >= 1",
        f'TARGET.GPUs_DeviceName =?= "{lib.GPU_MODEL}"',
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {spec['layout']['request_cpus']}",
    ))


def render(spec: dict, arm: str, *, preview: bool = False) -> str:
    name = f"p4_{arm}"
    executable = "PREVIEW_NOT_SUBMITTABLE_p4_job.sh" if preview else "p4_job.sh"
    lines = [
        f"# Track P P.4 phase 1 on {lib.GPU_MODEL}, image v2.2 (ENGINEERING_ONLY) — {spec['run_id']}/{arm}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        f"executable = {executable}",
        f"arguments = p4_spec.json {arm}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['layout']['request_cpus']}",
        f"request_memory = {spec['layout']['request_memory_mb']}",
        f"request_disk = {spec['layout']['request_disk_kb']}",
        "request_GPUs = 1",
        f"+RequestWalltime = {lib.arm_walltime_s(spec, arm)}",
        "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42",
        f"requirements = {requirements(spec)}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT_OR_EVICT",
        f"transfer_input_files = {','.join(lib.TRANSFER_INPUTS)}",
        f"transfer_output_files = {lib.TRANSFER_OUTPUTS}",
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text or "ProvidesEtpCeph" in text:
        raise lib.Stop("STOP: the JDL must not use docker_image, a GPU share or ProvidesEtpCeph")
    return text


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_table(table: Path) -> dict:
    """The three table files against the SFT config's ``sweep1_v3`` pins (``build.json`` recorded)."""
    sft = json.loads((REPO_ROOT / lib.SFT_CONFIG).read_text())
    pins = sft["tables"][lib.TABLE_PIN]["sha256"]
    out = {}
    for name in TABLE_FILES:
        p = Path(table) / name
        if p.is_symlink() or not p.is_file():
            raise lib.Stop(f"STOP: {p} missing")
        out[name] = _sha(p)
        if name in pins and out[name] != pins[name]:
            raise lib.Stop(f"STOP: {p} is not the {lib.TABLE_PIN} pin {pins[name]}")
    return out


def check_inputs(spec: dict, table: Path, partition: Path, *, preview: bool = False) -> dict:
    out = check_table(table)
    for name in PARTITION_FILES:
        p = Path(partition) / name
        if p.is_symlink() or not p.is_file():
            raise lib.Stop(f"STOP: {p} missing")
        out[name] = _sha(p)
    labels = spec["labels"]
    if not preview:
        if out["label_block.traindev.jsonl"] != labels["partition_sha256"] or \
                out["RECEIPT.json"] != labels["receipt_sha256"]:
            raise lib.Stop("STOP: the partition or its receipt is not the one the spec pins (labels:, label_receipt:)")
    receipt = json.loads((Path(partition) / "RECEIPT.json").read_text())
    if (receipt.get("inputs") or {}).get("label_block_sha256") != lib.SOURCE_BLOCK_SHA256 or \
            receipt.get("source") != "sweep1" or receipt.get("stage") != "traindev":
        raise lib.Stop("STOP: the receipt is not the sweep-1 train/dev release of the frozen block")
    try:                # P4-F2 A: the sealed v2 receipt table, bound to the staged sweep1_v3 table by FEAT-ONE A
        binding = lib._phase1(CODE_ROOT).check_receipt_table(receipt, table_proposals_sha256=out["proposals.jsonl"],
                                                             root=REPO_ROOT)
    except Exception as exc:
        if str(exc).startswith("STOP"):
            raise lib.Stop(str(exc)) from None
        raise
    out["receipt_table_binding"] = binding
    return out


def stage(spec_path: Path, stage_dir: Path, *, table: Path, partition: Path, preview: bool = False) -> dict:
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_spec(spec, launch=not preview)
    stage_dir = Path(stage_dir)
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise lib.Stop(f"STOP: stage directory {stage_dir} is not empty (no overwrite)")
    inputs = check_inputs(spec, table, partition, preview=preview)
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in STAGED:
        shutil.copy2(HERE / name, stage_dir / name)
    shutil.copy2(spec_path, stage_dir / "p4_spec.json")
    for name in TABLE_FILES:
        shutil.copy2(Path(table) / name, stage_dir / name)
    for name in PARTITION_FILES:
        shutil.copy2(Path(partition) / name, stage_dir / name)
    files = {}
    for arm in spec["arms"]:
        path = stage_dir / f"p4_{arm}.jdl"
        path.write_text(render(spec, arm, preview=preview))
        files[path.name] = _sha(path)
    for name in (*STAGED, "p4_spec.json", *TABLE_FILES, *PARTITION_FILES):
        files[name] = _sha(stage_dir / name)
    manifest = {"schema": "trackp_p4_stage/1", "run_id": loaded["run_id"], "preview": preview,
                "projection": loaded["projection"], "inputs": inputs, "files": files}
    (stage_dir / "STAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


PROBE_STAGED = ("p4_probe.sh", "p4_lib.py")


def render_probe(spec: dict, arm: str) -> str:
    """One probe JDL: ``render``'s fixed lines with the probe's executable, arguments, transfer lists and walltime."""
    name = f"p4probe_{arm}"
    lines = [
        f"# Track P P.4 phase-1 H200 SFT probe on {lib.GPU_MODEL}, image v2.2 (ENGINEERING_ONLY; P4-PROBE A) — "
        f"{spec['run_id']}/{arm}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        "executable = p4_probe.sh",
        f"arguments = {lib.PROBE_SPEC_FILE} {arm}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['layout']['request_cpus']}",
        f"request_memory = {spec['layout']['request_memory_mb']}",
        f"request_disk = {spec['layout']['request_disk_kb']}",
        "request_GPUs = 1",
        f"+RequestWalltime = {int(spec['probe']['walltime_s'])}",
        "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42",
        f"requirements = {requirements(spec)}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT_OR_EVICT",
        f"transfer_input_files = {','.join(lib.PROBE_TRANSFER_INPUTS)}",
        f"transfer_output_files = {lib.TRANSFER_OUTPUTS}",
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text or "ProvidesEtpCeph" in text or "label_block" in text \
            or "RECEIPT" in text:
        raise lib.Stop("STOP: the probe JDL must not use docker_image, a GPU share or ProvidesEtpCeph, nor transfer labels")
    return text


def stage_probe(spec_path: Path, stage_dir: Path, *, table: Path, arm: str, first_record: Path | None = None,
                sealed_root: Path = lib.SEALED_ROOT) -> dict:
    """The probe stage of one base (module docstring)."""
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_probe_spec(spec)
    lib.check_probe_template(spec, lib.load_spec(HERE / lib.PROBE_SPEC_FILE))
    if arm not in spec["arms"]:
        raise lib.Stop(f"STOP: {arm} is not an arm of the probe spec")
    spec_sha = _sha(spec_path)
    gate = None
    if arm != spec["first_arm"]:
        gate = lib.check_first_probe_record(first_record, spec, spec_sha, sealed_root)
    stage_dir = Path(stage_dir)
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise lib.Stop(f"STOP: stage directory {stage_dir} is not empty (no overwrite)")
    inputs = check_table(table)
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in PROBE_STAGED:
        shutil.copy2(HERE / name, stage_dir / name)
    shutil.copy2(spec_path, stage_dir / lib.PROBE_SPEC_FILE)
    for name in TABLE_FILES:
        shutil.copy2(Path(table) / name, stage_dir / name)
    jdl = stage_dir / f"p4probe_{arm}.jdl"
    jdl.write_text(render_probe(spec, arm))
    files = {jdl.name: _sha(jdl)}
    for name in (*PROBE_STAGED, lib.PROBE_SPEC_FILE, *TABLE_FILES):
        files[name] = _sha(stage_dir / name)
    manifest = {"schema": "trackp_p4_probe_stage/1", "run_id": loaded["run_id"], "arm": arm, "mode": "probe",
                "probe": loaded["probe"], "spec_sha256": spec_sha, "first_probe_record": gate, "inputs": inputs,
                "files": files}
    (stage_dir / "STAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("stage_dir", type=Path)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--partition", type=Path, help="the receipted partition (not with --probe)")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--probe", action="store_true", help="stage the H200 SFT probe of one base (P4-PROBE A)")
    ap.add_argument("--arm", help="--probe: the base")
    ap.add_argument("--first-record", type=Path, help="--probe, another base: the first arm's sealed probe record")
    a = ap.parse_args(argv)
    try:
        if a.probe:
            if a.partition is not None or a.preview or not a.arm:
                raise lib.Stop("STOP: --probe takes --arm, no --partition and no --preview (the probe reads no label)")
            print(json.dumps(stage_probe(a.spec, a.stage_dir, table=a.table, arm=a.arm, first_record=a.first_record),
                             indent=1))
            return 0
        if a.partition is None or a.arm or a.first_record:
            raise lib.Stop("STOP: a P.4 stage needs --partition and takes no --arm or --first-record")
        print(json.dumps(stage(a.spec, a.stage_dir, table=a.table, partition=a.partition, preview=a.preview),
                         indent=1))
    except lib.Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
