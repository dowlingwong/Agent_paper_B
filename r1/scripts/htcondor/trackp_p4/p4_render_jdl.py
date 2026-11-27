#!/usr/bin/env python3
"""Stage the Track P P.4 phase-1 job files and render one HTCondor JDL (or one direct descriptor) per base (no
submission here). ENGINEERING_ONLY; AI-assisted (Claude).

**R1-HOST-FREE.** A P.4 stage is for one admitted host class (``--host-class``, required): the same canonical stage
(``p4_job.sh``, ``p4_lib.py``, the spec, the table, the partition: ``p4_lib.TRANSFER_INPUTS``) for both launch kinds,
then for an HTCondor class (``nemo2_h200``) one JDL per arm as below, whose ``arguments`` tell the job its class, and
for a direct class (``ada_rtx6000``) ``p4_direct.py`` and one descriptor ``p4direct_<arm>.json`` per arm
(``render_direct``: the class's filled host config's direct values in this checkout, which must be the spec's sha256).
The manifest names ``host_class`` and ``launch``. A probe stage takes its class from the probe spec's ``host_class``;
a direct probe stage writes the descriptor in place of the JDL, ``p4_direct.py``, a unique manifest (``stage_dir``,
``staged_utc``) and a ledger entry with the manifest's sha256; one probe run holds stages of one class only. Below,
"the H200 requirement" is the HTCondor class's GPU requirement.

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
(``condor_submit``), after the pre-submit check: **exactly one ``condor_submit`` per stage directory**, because staging
appends one entry to ``<sealed_root>/<probe run id>/_submissions.jsonl`` (review round 1, M2), which the probe charge
prices at the probe's ``walltime_s`` until its attempt is sealed. A staged base that will not be submitted is still
charged; a base is staged again only after its earlier attempt is sealed as a STOP (no pending submission and no
sealed STOP-free attempt of it in the run: one probe run per base, P4-PROBE A; review round 4, M1); staging into a
probe run that already has a charge file (its probe record was made) is refused: a
re-probe needs a new run id in the template ``p4_probe_spec.json``, a reviewed commit; a job that never ran is sealed
from its stage directory (``p4_lib.py seal <stage dir> <probe spec> --arm
<arm>``: its ``STAGE_MANIFEST.json`` marks it a probe attempt, charged the probe's ``walltime_s``).

Before staging, ``check_probe_binding`` (review round 1, minor 4) checks at the desk what the job would otherwise
refuse only after it has started: ``origin/main`` freshly fetched (``ls-remote`` equals the local ref), the probe
spec's ``paper.commit`` on it, this checkout's ``p4_lib.py``, ``p4_probe.sh`` and probe template equal to those files
at ``paper.commit``, and ``host_config.sha256`` equal to the host config at ``paper.commit``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]          # data read from the checkout (the SFT config, the FEAT-ONE identity result)
CODE_ROOT = HERE.parents[3]          # code imported from the checkout (r1.c3.train.p4_phase1)
sys.path.insert(0, str(HERE))
import p4_lib as lib  # noqa: E402

STAGED = ("p4_job.sh", "p4_lib.py")
TABLE_FILES = ("proposals.jsonl", "configs.json", "build.json")
PARTITION_FILES = ("label_block.traindev.jsonl", "RECEIPT.json")


HTCONDOR_CLASS = "nemo2_h200"        # the one HTCondor host class (lib.HOST_CLASSES)
DIRECT_KEYS = ("ssh_alias", "hostname", "container_runtime", "work_root", "lock_dir", "shm_size", "min_free_mib")
DIRECT_SCHEMA = "trackp_p4_direct_job/1"
DIRECT_LAUNCHER = "p4_direct.py"


def requirements(spec: dict, host_class: str = HTCONDOR_CLASS) -> str:
    gpu = lib.HOST_CLASSES[host_class]["gpu_name"]
    return " && ".join(f"({c})" for c in (
        "TARGET.GPUs >= 1",
        f'TARGET.GPUs_DeviceName =?= "{gpu}"',
        'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"',
        f"TARGET.Cpus >= {spec['layout']['request_cpus']}",
    ))


def render(spec: dict, arm: str, *, preview: bool = False, host_class: str = HTCONDOR_CLASS) -> str:
    lib.host_class_of(spec, host_class, launch="htcondor")
    name = f"p4_{arm}"
    executable = "PREVIEW_NOT_SUBMITTABLE_p4_job.sh" if preview else "p4_job.sh"
    lines = [
        f"# Track P P.4 phase 1 on {lib.HOST_CLASSES[host_class]['gpu_name']} ({host_class}), image v2.2 "
        f"(ENGINEERING_ONLY) — {spec['run_id']}/{arm}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        f"executable = {executable}",
        f"arguments = p4_spec.json {arm} {host_class}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['layout']['request_cpus']}",
        f"request_memory = {spec['layout']['request_memory_mb']}",
        f"request_disk = {spec['layout']['request_disk_kb']}",
        "request_GPUs = 1",
        f"+RequestWalltime = {lib.arm_walltime_s(spec, arm, host_class)}",   # the class's own (B2)
        "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42",
        f"requirements = {requirements(spec, host_class)}",
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


def direct_host_values(spec: dict, host_class: str, *, preview: bool = False, repo: Path | None = None) -> dict:
    """The direct-launch values of the class's host config in this checkout (its ``direct`` block: ``DIRECT_KEYS``)
    with the file's path and sha256. Unless a preview, the file must be the spec's (``hosts.<class>.host_config``
    sha256) and every value filled (no ``TODO_VERIFY_ON_HOST``)."""
    host = lib.host_class_of(spec, host_class, launch="direct")
    rel = host["host_config"]["path"]
    raw = (Path(repo or REPO_ROOT) / rel).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not preview and sha != host["host_config"]["sha256"]:
        raise lib.Stop(f"STOP: {rel} in this checkout (sha256 {sha}) is not hosts.{host_class}.host_config of the spec")
    block = json.loads(raw).get("direct")
    vals = {k: (block or {}).get(k) for k in DIRECT_KEYS}
    open_ = sorted(k for k, v in vals.items() if not isinstance(v, str) or v.startswith("TODO_VERIFY") or
                   lib._placeholder(v))
    if open_ and not preview:
        raise lib.Stop(f"STOP: {rel} direct.{open_} not filled (p4_fill_host_config.py --host-class {host_class})")
    return {"values": vals, "host_config": {"path": rel, "sha256": sha}}


def render_direct(spec: dict, arm: str, host_class: str, *, mode: str, preview: bool = False,
                  repo: Path | None = None) -> str:
    """The descriptor ``p4direct_<arm>.json`` of a direct stage (``trackp_p4_direct_job/1``), the direct path's
    counterpart of a JDL: run, arm, mode (``job`` or ``probe``), the class and its GPU, the image digest, the entry
    script, the spec file and the transferred inputs (the HTCondor lists), the outputs to copy back, the host values of
    the class's host config, the walltime bound (recorded only: the charge of an attempt whose launcher record is
    incomplete; no limit, R1-NO-TIMEOUT) and, for a P.4 job, the switch marker the launcher requires. Deterministic, so
    the switch re-renders and compares it."""
    if mode not in ("job", "probe"):
        raise lib.Stop(f"STOP: unknown direct mode {mode!r}")
    hv = direct_host_values(spec, host_class, preview=preview, repo=repo)
    cls = lib.HOST_CLASSES[host_class]
    job = mode == "job"
    doc = {"schema": DIRECT_SCHEMA, "label": lib.ENGINEERING_ONLY, "preview": preview, "mode": mode,
           "run_id": spec["run_id"], "arm": arm, "host_class": host_class, "gpu_name": cls["gpu_name"],
           "compute_capability": cls["compute_capability"], "image_digest": spec["image"]["digest"],
           "entry": "p4_job.sh" if job else "p4_probe.sh", "spec_file": "p4_spec.json" if job else lib.PROBE_SPEC_FILE,
           "inputs": list(lib.TRANSFER_INPUTS if job else lib.PROBE_TRANSFER_INPUTS),
           "outputs": [*lib.TRANSFER_OUTPUTS.split(","), lib.DIRECT_LAUNCH_FILE],
           "host": hv["values"], "host_config": hv["host_config"],
           "walltime_bound_s": lib._requested_walltime_s(spec, arm),
           "walltime_rule": "recorded only (R1-NO-TIMEOUT): the charge bound of an attempt whose launcher record is "
                            "incomplete; nothing stops the job on time",
           "submit_marker": f"P4_SUBMIT_STARTED_{arm}.json" if job else None,
           "launch_command": f"python3 {DIRECT_LAUNCHER} launch --stage <this stage copied to "
                             f"{hv['values'].get('ssh_alias')}> --arm {arm} --gpu <free card index>"}
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


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


def stage(spec_path: Path, stage_dir: Path, *, table: Path, partition: Path, host_class: str,
          preview: bool = False) -> dict:
    """The canonical P.4 stage for the arms' jobs on ``host_class`` (one class per stage; the spec must admit it): the
    same transferred inputs for both launch kinds, then one JDL per arm (an HTCondor class) or one direct descriptor
    per arm and ``p4_direct.py`` (a direct class)."""
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_spec(spec, launch=not preview)
    host = lib.host_class_of(spec, host_class)
    direct = host["launch"] == "direct"
    stage_dir = Path(stage_dir)
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise lib.Stop(f"STOP: stage directory {stage_dir} is not empty (no overwrite)")
    inputs = check_inputs(spec, table, partition, preview=preview)
    staged = (*STAGED, DIRECT_LAUNCHER) if direct else STAGED
    descriptors = {arm: render_direct(spec, arm, host_class, mode="job", preview=preview) for arm in spec["arms"]} \
        if direct else {}
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in staged:
        shutil.copy2(HERE / name, stage_dir / name)
    shutil.copy2(spec_path, stage_dir / "p4_spec.json")
    for name in TABLE_FILES:
        shutil.copy2(Path(table) / name, stage_dir / name)
    for name in PARTITION_FILES:
        shutil.copy2(Path(partition) / name, stage_dir / name)
    files = {}
    for arm in spec["arms"]:
        path = stage_dir / (f"p4direct_{arm}.json" if direct else f"p4_{arm}.jdl")
        path.write_text(descriptors[arm] if direct else render(spec, arm, preview=preview, host_class=host_class))
        files[path.name] = _sha(path)
    for name in (*staged, "p4_spec.json", *TABLE_FILES, *PARTITION_FILES):
        files[name] = _sha(stage_dir / name)
    manifest = {"schema": "trackp_p4_stage/1", "run_id": loaded["run_id"], "preview": preview,
                "host_class": host_class, "launch": host["launch"],
                "projection": loaded["projection"], "inputs": inputs, "files": files}
    (stage_dir / "STAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


PROBE_STAGED = ("p4_probe.sh", "p4_lib.py")


def render_probe(spec: dict, arm: str) -> str:
    """One probe JDL (the probe spec's ``host_class`` must be an HTCondor class): ``render``'s fixed lines with the
    probe's executable, arguments, transfer lists and walltime."""
    host_class = spec.get("host_class")
    lib.host_class_of(spec, host_class, launch="htcondor")
    name = f"p4probe_{arm}"
    lines = [
        f"# Track P P.4 phase-1 SFT probe on {lib.HOST_CLASSES[host_class]['gpu_name']} ({host_class}), image v2.2 "
        f"(ENGINEERING_ONLY; P4-PROBE A) — {spec['run_id']}/{arm}",
        "universe = container",
        f"container_image = docker://{spec['image']['digest']}",
        "executable = p4_probe.sh",
        f"arguments = {lib.PROBE_SPEC_FILE} {arm} {host_class}",
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
        f"requirements = {requirements(spec, host_class)}",
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


def _show(repo: Path, commit: str, rel: str) -> bytes | None:
    try:
        res = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"], capture_output=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise lib.Stop(f"STOP: git show {commit[:12]}:{rel} timed out") from None
    return res.stdout if res.returncode == 0 else None


def check_probe_binding(spec: dict, repo: Path | None = None, git=lib._git) -> dict:
    """The desk-side pre-submit binding of a probe stage (module docstring)."""
    try:
        return _check_probe_binding(spec, Path(repo or REPO_ROOT), git)
    except subprocess.TimeoutExpired as exc:
        raise lib.Stop(f"STOP: a git command of the probe binding timed out: {exc.cmd}") from None


def _check_probe_binding(spec: dict, repo: Path, git) -> dict:
    commit = spec["paper"]["commit"]
    remote, local = git(repo, "ls-remote", "origin", "refs/heads/main"), git(repo, "rev-parse", "origin/main")
    if remote.returncode or local.returncode or remote.stdout.split() != [local.stdout.strip(), "refs/heads/main"]:
        raise lib.Stop("STOP: fetch published main before staging the probe; local origin/main differs or could not "
                       "be verified")
    if git(repo, "merge-base", "--is-ancestor", commit, "origin/main").returncode:
        raise lib.Stop(f"STOP: the probe spec's paper.commit {commit} is not on published main")
    cls = spec["host_class"]
    names = ("p4_lib.py", "p4_probe.sh", lib.PROBE_SPEC_FILE) + \
        ((DIRECT_LAUNCHER,) if lib.HOST_CLASSES[cls]["launch"] == "direct" else ())
    for name in names:
        if _show(repo, commit, f"{lib.PKG_REL}/{name}") != (HERE / name).read_bytes():
            raise lib.Stop(f"STOP: this checkout's {name} is not the one at paper.commit {commit[:12]} (the job "
                           "would refuse it)")
    rel = spec["hosts"][cls]["host_config"]["path"]
    host = _show(repo, commit, rel)
    if host is None or hashlib.sha256(host).hexdigest() != spec["hosts"][cls]["host_config"]["sha256"]:
        raise lib.Stop(f"STOP: hosts.{cls}.host_config.sha256 is not the sha256 of {rel} at paper.commit {commit[:12]}")
    return {"paper_commit": commit, "origin_main": local.stdout.strip(), "host_class": cls,
            "host_config_sha256": hashlib.sha256(host).hexdigest()}


def stage_probe(spec_path: Path, stage_dir: Path, *, table: Path, arm: str, first_record: Path | None = None,
                sealed_root: Path = lib.SEALED_ROOT, binding=None) -> dict:
    """The probe stage of one base (module docstring)."""
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_probe_spec(spec)
    lib.check_probe_template(spec, lib.load_spec(HERE / lib.PROBE_SPEC_FILE))
    bound = (binding or check_probe_binding)(spec)
    if arm not in spec["arms"]:
        raise lib.Stop(f"STOP: {arm} is not an arm of the probe spec")
    spec_sha = _sha(spec_path)
    gate = None
    if arm != spec["first_arm"]:
        gate = lib.check_first_probe_record(first_record, spec, spec_sha, sealed_root)
    stage_dir = Path(stage_dir)
    if stage_dir.is_symlink():
        raise lib.Stop(f"STOP: stage directory {stage_dir} is a symlink")
    if stage_dir.exists() and (not stage_dir.is_dir() or any(stage_dir.iterdir())):
        raise lib.Stop(f"STOP: stage directory {stage_dir} is not empty (no overwrite)")
    run_dir = Path(sealed_root) / spec["run_id"]
    if run_dir.is_dir() and any(run_dir.glob("_wallclock*")):
        raise lib.Stop(f"STOP: the probe run {spec['run_id']} is already recorded (it has a charge file): a re-probe "
                       "needs a new run id in p4_probe_spec.json, a reviewed commit (review round 3, M1)")
    host_class = loaded["host_class"]
    direct = lib.HOST_CLASSES[host_class]["launch"] == "direct"
    staged_classes = {e.get("host_class") for e in lib.read_ledger(run_dir / lib.SUBMISSION_LEDGER)}
    other = sorted(map(str, staged_classes - {host_class}))
    if other:
        raise lib.Stop(f"STOP: the probe run {spec['run_id']} already holds stages of {other}: one probe run measures "
                       f"one host class (its estimate is per class); a probe on {host_class} needs a new run id")
    sofar = lib.charged_hours({"run_id": spec["run_id"], "probe": lib.PROBE, "caps": {}}, sealed_root)
    if any(x["arm"] == arm for x in sofar["pending"]):          # review round 4, M1: one run per base (P4-PROBE A)
        raise lib.Stop(f"STOP: {arm} already has a probe submission that is not sealed; seal it before staging again")
    if any(a["arm"] == arm and not a["stop"] for a in sofar["attempts"]):
        raise lib.Stop(f"STOP: {arm} already has a sealed STOP-free probe attempt in {spec['run_id']}: one probe run per "
                       "base (P4-PROBE A); a repeat follows only a STOP")
    inputs = check_table(table)
    ledger = run_dir / lib.SUBMISSION_LEDGER
    created, written = not stage_dir.exists(), []

    def put(name: str, src: Path | None = None, text: str | None = None) -> Path:
        dest = stage_dir / name
        written.append(dest)
        if src is not None:
            shutil.copy2(src, dest)
        else:
            dest.write_text(text)
        return dest

    try:        # the stage, then (last) its ledger entry; on any failure the files this call wrote are removed
        stage_dir.mkdir(parents=True, exist_ok=True)
        staged = (*PROBE_STAGED, DIRECT_LAUNCHER) if direct else PROBE_STAGED
        for name in staged:
            put(name, HERE / name)
        put(lib.PROBE_SPEC_FILE, spec_path)
        for name in TABLE_FILES:
            put(name, Path(table) / name)
        if direct:          # R1-HOST-FREE: the descriptor the host launcher runs, in place of the JDL
            launcher = put(f"p4direct_{arm}.json", text=render_direct(spec, arm, host_class, mode="probe"))
        else:
            launcher = put(f"p4probe_{arm}.jdl", text=render_probe(spec, arm))
        files = {launcher.name: _sha(launcher)}
        for name in (*staged, lib.PROBE_SPEC_FILE, *TABLE_FILES):
            files[name] = _sha(stage_dir / name)
        manifest = {"schema": "trackp_p4_probe_stage/1", "run_id": loaded["run_id"], "arm": arm, "mode": "probe",
                    "host_class": host_class, "launch": lib.HOST_CLASSES[host_class]["launch"],
                    "probe": loaded["probe"], "spec_sha256": spec_sha, "first_probe_record": gate, "binding": bound,
                    "inputs": inputs, "files": files, "submission_ledger": str(ledger),
                    "submit": ("exactly one launch of this stage on the host: python3 p4_direct.py launch --stage "
                               f"<this stage> --arm {arm} --gpu <index>") if direct else
                    "exactly one condor_submit of this stage directory"}
        if direct:          # unique per stage, so the ledger entry names this stage by the manifest's sha256
            manifest.update(stage_dir=str(stage_dir.resolve()),
                            staged_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        put("STAGE_MANIFEST.json", text=json.dumps(manifest, indent=1) + "\n")
        ledger.parent.mkdir(parents=True, exist_ok=True)   # M2: the probe charge counts this stage from now on
        entry = {"arm": arm, "kind": "probe", "stage": str(stage_dir.resolve()), "spec_sha256": spec_sha,
                 "host_class": host_class,
                 "intended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if direct:
            entry.update(launch="direct", stage_manifest_sha256=_sha(stage_dir / "STAGE_MANIFEST.json"))
        with ledger.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:  # noqa: BLE001 - no stage may remain without its ledger entry
        try:
            for f in reversed(written):
                if f.is_file() and not f.is_symlink():
                    f.unlink()
            if created and stage_dir.is_dir() and not any(stage_dir.iterdir()):
                stage_dir.rmdir()
        except Exception as cleanup:  # noqa: BLE001
            raise lib.Stop(f"STOP: staging failed ({exc}) and its cleanup failed too ({cleanup}): remove "
                           f"{stage_dir} by hand before any submission") from None
        raise lib.Stop(f"STOP: staging the probe failed ({exc}); nothing staged and no submission recorded") from None
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("stage_dir", type=Path)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--partition", type=Path, help="the receipted partition (not with --probe)")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--probe", action="store_true", help="stage the SFT probe of one base (P4-PROBE A) on the probe "
                                                         "spec's host_class")
    ap.add_argument("--arm", help="--probe: the base")
    ap.add_argument("--first-record", type=Path, help="--probe, another base: the first arm's sealed probe record")
    ap.add_argument("--host-class", choices=sorted(lib.HOST_CLASSES),
                    help="a P.4 stage: the admitted host class the arms' jobs run on (R1-HOST-FREE); required")
    a = ap.parse_args(argv)
    try:
        if a.probe:
            if a.partition is not None or a.preview or not a.arm or a.host_class:
                raise lib.Stop("STOP: --probe takes --arm, no --partition, no --preview (the probe reads no label) and "
                               "no --host-class (the probe spec names its host_class)")
            print(json.dumps(stage_probe(a.spec, a.stage_dir, table=a.table, arm=a.arm, first_record=a.first_record),
                             indent=1))
            return 0
        if a.partition is None or a.arm or a.first_record or not a.host_class:
            raise lib.Stop("STOP: a P.4 stage needs --partition and --host-class and takes no --arm or --first-record")
        print(json.dumps(stage(a.spec, a.stage_dir, table=a.table, partition=a.partition, host_class=a.host_class,
                               preview=a.preview), indent=1))
    except lib.Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
