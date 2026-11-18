#!/usr/bin/env python3
"""Stage the sweep-2 job files and render the fixed HTCondor JDL (ENGINEERING).

The reviewed C2, C3 and C3b spec schemas are supported:

* ``s2_c2_job/v1``     - the sweep-2 chunk/liveness job (S2-C2): executable ``s2_c2_job.sh``;
* ``s2_c3_replay/v1``  - the B2 root replay deployment check (S2-C3): executable ``s2_c3_replay_job.sh``, with the
  24 flattened pinned B2 root inputs, the reviewed label patch + TASL-only preflight shim, the declared-inputs
  manifest and every declared file input (Stage A tables, Stage A prompts, OpenML cache archive) staged as transfer
  inputs.
* The C3b schema stages D28 liveness and prompt re-measurement via `--kind c3b`.

The container job writes only into its HTCondor sandbox; the listed output files are transferred back to the submit
host and the reviewed `seal` step copies them into the sealed /ceph path (NEMO2 slots do not advertise
ProvidesEtpCeph).  The authorization note, when the C2 spec pins one, is staged and added to transfer_input_files.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402
import s2_c3_replay as replay  # noqa: E402
import s2_c3b_lib as c3b  # noqa: E402

C2_OUTPUTS = "out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log"
C3_OUTPUTS = C2_OUTPUTS
C3_EXECUTABLE = "s2_c3_replay_job.sh"
CRITERIA_STAGED = "S2_C3_CRITERIA.md"
L40S_RANK = 'rank = ifThenElse(TARGET.GPUs_DeviceName =?= "NVIDIA L40S", 1, 0)'


def requirements(spec: dict) -> str:
    return " && ".join(f"({c})" for c in (
        "TARGET.GPUs >= 1",
        "TARGET.GPUs_GlobalMemoryMb >= 24576",
        "TARGET.GPUs_Capability >= 7.0",
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {lib.MIN_CPUS}",
        *([f'TARGET.GPUs_DeviceName =?= "{spec["diagnostic_gpu_model"]}"'] if spec.get("diagnostic_gpu_model") else []),
        *([f'TARGET.CloudSite =?= "{lib.CLOUD_SITE}"'] if spec.get("diagnostic_gpu_model") == "NVIDIA L40S" else []),
    ))


def _layout(spec: dict, key: str) -> int:
    value = spec.get(key)
    if type(value) is not int or value <= 0:
        raise lib.Stop(f"STOP: spec must declare the author-accepted 32k layout field {key} (integer); got {value!r}")
    return value


def render(spec: dict, name: str, inputs: list[str], *, executable: str = "s2_c2_job.sh",
           arguments: str = "s2_c2_spec.json", outputs: str = C2_OUTPUTS,
           banner: str = "S2-C2 sweep-2 chunk job (ENGINEERING; reviewed dry-run)") -> str:
    lines = [
        f"# {banner} — {spec['run_id']}/{spec['chunk_id']}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        f"executable = {executable}",
        f"arguments = {arguments}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {lib.MIN_CPUS}",
        # The author-accepted 32k sweep-2 layout is spec-declared (R1-SWEEP2-LAYOUT); never hard-coded here, so a
        # stale 16k default cannot leak into a rendered JDL.  A spec without the fields is a STOP.
        f"request_memory = {_layout(spec, 'request_memory_mb')}",
        f"request_disk = {_layout(spec, 'request_disk_kb')}",
        "request_GPUs = 1",
        f"+RequestWalltime = {_layout(spec, 'walltime_s')}",
        "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42",
        f"requirements = {requirements(spec)}",
        *([L40S_RANK] if executable == "s2_c2_job.sh" else []),
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        "transfer_input_files = " + ",".join(inputs),
        "transfer_output_files = " + outputs,
        "queue 1",
    ]
    text = "\n".join(lines) + "\n"
    if "docker_image" in text or "RequestGPUMemory" in text or "ProvidesEtpCeph" in text:
        raise lib.Stop("STOP: rendered JDL must not use docker_image, request a GPU share, or require ProvidesEtpCeph")
    return text


def _write_spec(stage: Path, spec: dict) -> None:
    (stage / "s2_c2_spec.json").write_text(json.dumps(spec, indent=1) + "\n")


def stage_c2(spec: dict, stage: Path, a) -> str:
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
    _write_spec(stage, spec)
    cwd = os.getcwd()
    try:
        os.chdir(stage)
        lib.validate_spec(lib.load_spec(stage / "s2_c2_spec.json"))
    finally:
        os.chdir(cwd)
    return json.dumps(spec, indent=1) + "\n"


def stage_c3(spec: dict, stage: Path) -> None:
    """Stage the replay job, the pinned B2 roots, the reviewed patches and every declared input (flat), then verify."""
    for name in ("s2_c3_replay.py", "s2_c2_lib.py", "s2_c3_replay_job.sh"):
        shutil.copy2(HERE / name, stage / name)
    criteria = ROOT / replay.CRITERIA_PATH
    if not criteria.is_file() or replay._sha_file(criteria) != replay.CRITERIA_SHA256:
        raise replay.Stop("STOP: criteria file missing or its sha256 does not match the pre-declared pin")
    shutil.copy2(criteria, stage / CRITERIA_STAGED)
    inputs_dir = ROOT / spec["replay_inputs"]["dir"]
    if not inputs_dir.is_dir():
        raise replay.Stop(f"STOP: pinned replay inputs directory {inputs_dir} missing")
    shutil.copy2(inputs_dir / "SHA256SUMS", stage / replay.STAGED_SHA256SUMS)
    for root in replay.ROOTS:
        for kind, staged in (("job.json", replay.STAGED_JOB.format(root=root)),
                             ("campaign_manifest.json", replay.STAGED_MANIFEST.format(root=root))):
            source = inputs_dir / root / kind
            if not source.is_file():
                raise replay.Stop(f"STOP: pinned replay input {root}/{kind} missing")
            shutil.copy2(source, stage / staged)
    # The declared-inputs manifest is staged unchanged, and every declared ``file`` item is staged under its flat
    # transfer name.  The job verifies the same sha256 values again (and the git blobs after its pinned clones).
    manifest = ROOT / spec["declared_inputs"]["path"]
    if not manifest.is_file() or replay._sha_file(manifest) != spec["declared_inputs"]["sha256"]:
        raise replay.Stop("STOP: declared-inputs manifest missing or its sha256 does not match the spec pin")
    shutil.copy2(manifest, stage / replay.DECLARED_STAGED)
    declared = json.loads(manifest.read_text())
    for item in declared.get("items") or []:
        if item.get("kind") != "file":
            continue
        source = ROOT / item["path"]
        if not source.is_file():
            raise replay.Stop(f"STOP: declared input {item['id']} is missing ({source})")
        if replay._sha_file(source) != item["sha256"]:
            raise replay.Stop(f"STOP: declared input {item['id']} sha256 does not match the declaration")
        shutil.copy2(source, stage / item["staged"])
    for rel, sha, kind in ((replay.PATCH_PATH, replay.PATCH_SHA256, "label"),
                           (replay.SHIM_PATH, replay.SHIM_SHA256, "shim")):
        source = HERE / Path(rel).name
        if not source.is_file() or replay._sha_file(source) != sha:
            raise replay.Stop(f"STOP: {kind} patch missing or its sha256 does not match the reviewed pin")
        if (stage / source.name).is_file() and replay._sha_file(stage / source.name) != sha:
            raise replay.Stop(f"STOP: staged {kind} patch differs from the reviewed pin")
    (stage / "s2_c3_spec.json").write_text(json.dumps(spec, indent=1) + "\n")
    cwd = os.getcwd()
    try:
        os.chdir(stage)
        replay.validate_spec(replay.load_spec(stage / "s2_c3_spec.json"))
        replay.verify_pinned_inputs(stage, spec)
        staged_declared = replay.load_declared_inputs(stage, spec)
        replay.verify_declared_inputs(stage, spec, staged_declared,
                                      cfg=replay.verify_pinned_inputs(stage, spec)["jobs"][replay.ROOTS[0]][
                                          "authority_config"])
    finally:
        os.chdir(cwd)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--kind", choices=("c2", "c3b"), default=None)
    ap.add_argument("--auth-note", default=None, help="C2 only: source authorization note to stage (EVIDENCE)")
    a = ap.parse_args(argv)
    raw = json.loads(Path(a.spec).read_text())
    schema = raw.get("schema") if isinstance(raw, dict) else None
    stage = Path(a.stage_dir).resolve()
    if stage.exists():
        raise lib.Stop(f"STOP: stage dir {stage} already exists (fresh staging required)")
    stage.mkdir(parents=True, mode=0o700)
    if a.kind == "c3b" or schema == c3b.SCHEMA:
        spec = c3b.load_spec(Path(a.spec))
        files = ["s2_c3b_job.sh", "s2_c3b_lib.py", "s2_c2_lib.py"]
        for filename in files:
            shutil.copy2(HERE / filename, stage / filename)
        spec_name = "s2_c3b_spec.json"
        (stage / spec_name).write_text(json.dumps(spec, indent=1) + "\n")
        cwd = os.getcwd()
        try:
            os.chdir(stage)
            c3b.validate_spec(c3b.load_spec(stage / spec_name))
        finally:
            os.chdir(cwd)
        out_path = Path(a.out).resolve()
        out_path.write_text(render(spec, a.name or "s2_c3b_job", sorted(files + [spec_name]),
                                   executable="s2_c3b_job.sh", arguments=spec_name,
                                   banner="S2-C3b D28 liveness and prompt re-measurement (ENGINEERING_ONLY)"))
        print(out_path)
        return 0
    if schema == replay.SCHEMA:
        validated = replay.validate_spec(raw)
        spec = validated["spec"]
        stage_c3(spec, stage)
        inputs = sorted(p.name for p in stage.iterdir() if p.is_file())
        if "s2_c3_spec.json" not in inputs or "s2_c3_replay_job.sh" not in inputs:
            raise lib.Stop("STOP: staged replay inputs incomplete")
        out_path = Path(a.out).resolve()
        out_path.write_text(render(spec, a.name or "s2_c3_replay_job", inputs, executable=C3_EXECUTABLE,
                                   arguments="s2_c3_spec.json", outputs=C3_OUTPUTS,
                                   banner="S2-C3 B2-root replay / L40S deployment check (ENGINEERING; reviewed dry-run)"))
        print(out_path)
        return 0
    if schema != lib.SCHEMA:
        raise lib.Stop(f"STOP: unsupported spec schema {schema!r}")
    spec = lib.load_spec(Path(a.spec))
    imported = stage_c2(spec, stage, a)
    spec = json.loads(imported)
    inputs = sorted(p.name for p in stage.iterdir() if p.is_file())
    if "s2_c2_spec.json" not in inputs or "s2_c2_job.sh" not in inputs:
        raise lib.Stop("STOP: staged inputs incomplete")
    out_path = Path(a.out).resolve()
    out_path.write_text(render(spec, a.name or "s2_c2_job", inputs))
    print(out_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (lib.Stop, replay.Stop) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
