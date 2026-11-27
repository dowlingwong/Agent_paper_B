"""Track P P.4 phase 1 on any admitted host class (R1-HOST-FREE: NEMO2 H200 by HTCondor, Ada RTX 6000 by a direct
launch; image v2.2): the job of P4-JOB A, one job per base. ENGINEERING_ONLY; AI-assisted (Claude).

**R1-HOST-FREE** (card local/20261126-06 unit 1). The spec admits host classes (``hosts``; ``HOST_CLASSES``): each
with its launch kind, GPU name, compute capability, its own host config and its own SFT probe estimate. Each job is
told its class (``--host-class``, the third argument of ``p4_job.sh`` / ``p4_probe.sh``); identity admits exactly one
GPU of that class (name and compute capability), and a direct job's GPU must be the card its launcher leased
(``lease_binding``). The record names the class, host, GPU model, UUID, driver and env3 freeze, and the card's other
compute processes at the start and the end (count and memory, R1-CARD-SHARE (4)); an arm STOP (a CUDA OOM) beside
another compute process is reclassified as an infrastructure failure, repeated in a new attempt directory
(R1-CARD-SHARE (3); ``shared_card_loss``). One arm's run stays on one card: one job, one card; ``assemble`` records
each arm's class and card and refuses an arm whose record does not carry its class's GPU or its leased card.
``seal`` accepts a direct attempt with its launcher record (``direct_launch.json``) and charges GPU-hours on any card
(R1-HOST-FREE (5)); ``charged_hours``, the probe charges and the charge files sum both kinds. **R1-NO-TIMEOUT (3)**:
the 40 GPU-h and 64 slot-hour figures of P4-CAP A are reporting thresholds (``threshold_report``): launch validation,
the switch's check before every submission, ``probe_records`` and ``assemble`` report usage against them and flag
``report_to_author``; none refuses for them. No wall-clock limit decides anything: HTCondor's ``+RequestWalltime``
is a scheduler request only (a walltime kill is sealed as an infrastructure failure), and a direct launch has none.
The step list below is unchanged except where it says "the H200": read "the job's class".

Authority: the P.4 phase-1 authorization draft (`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`,
revision 4.2; P3 of its §7 is this unit), R1-TRACKP-P4-DECISIONS (P4-PHASE1-TEST A, P4-P1SPLIT A, P4-LABELS A,
P4-ARMS A, P4-MB A, P4-JOB A, P4-LC A, P4-CAP A), R1-TRACKP-P4-RUNNER-DECISIONS ((1) the env3 freeze reading, (2)
tokenizers through the hub into ``HF_HOME``, (3) ``kev-0.8b`` the first, solo arm), R1-T1-HOST-TASL (P.4 on NEMO2
H200), R1-TRACKP-IMAGE-V21,
R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B (image v2.2: causal_conv1d 1.7.0 built from source in env3),
R1-TRACKP-V21-FREEZE and R1-HTC-QTORCH (the env3 freeze), R1-S2-LABELS-TRAINDEV-RELEASE (the receipted
partition), R1-TRACKP-SFT-DEV (``sft-dev``, ENGINEERING_ONLY).

**One job = one base** (``arm``), in this order, every step a STOP on failure (``stop_class``: "infrastructure"
for host, image, staging and transfer failures; "protocol" for a refusal of the SFT pipeline; "arm" for a
training failure of the arm, such as a CUDA OOM at the chosen micro-batch):

1. **Identity.** ``/opt/r1/VERSIONS.txt`` sha256 equal to the spec's (the image v2.2 pin), exactly one GPU and it
   is the GPU of the job's host class (``nvidia-smi``; an NVIDIA H200 for ``nemo2_h200``), for a direct class the
   leased card, a non-root uid.
2. **Paper clone.** A full clone at the spec's paper commit with ``origin/main`` fetched, the commit an ancestor of
   ``origin/main``, the tree clean (every partition open runs ``git`` at HEAD and checks the release commit on
   ``origin/main``; a shallow clone would STOP every label read).
3. **env3 freeze** (R1-TRACKP-V21-FREEZE): ``uv pip freeze`` of ``/opt/r1/envs/trackp`` (env3 is a uv venv without
   pip; the image build checks the same freeze) against R1-ENV-PIN's ``pip_freeze_trackp-gpu.txt`` in the clone
   (sha256 pinned): equal, or different only in the ``causal_conv1d`` line at the same version
   (``r1.c3.train.p4_phase1.check_env3_freeze``). The difference is recorded in the job record (``env3_freeze``); any
   other difference is a STOP. R1-TRACKP-P4-RUNNER-DECISIONS (1): "the same version number" reads as version 1.7.0,
   any local build label admitted and recorded, and the env3 causal_conv1d line is checked against 1.7.0 (also when
   the freeze is identical). Image v2.2's build records the sorted freeze identical to the pin (its causal_conv1d
   wheel, built from source, is installed by name: ``causal-conv1d==1.7.0``), which this step records as
   ``identical`` with that line.
4. **Configs.** The host config and the SFT config at the clone have the spec's sha256 and the host config has no
   ``TODO_VERIFY_ON_HOST`` left (``trackp.py --check-config``).
5. **Inputs.** The transferred table files (``proposals.jsonl``, ``configs.json`` at the SFT config's pins; the
   ``build.json`` recorded), and the receipted sweep-1 train/dev partition and its receipt at the note's sha256,
   with the frozen source block (``check_partition``); **P4-F2 A** (R1-P4-TESTPLAN-DECISIONS): the receipt's
   ``inputs.proposals_sha256`` must be the sealed v2 table (``arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256``; any
   other value is a STOP), A3's FEAT-ONE A identity check (``arms_freeze.require_feat_one`` on the committed identity
   result A3 consumed) binds it to the transferred ``sweep1_v3`` table, and the released labels are joined to that
   table by proposal id as A3 joins them (``p4_phase1.join_labels``: a missing or extra id is a STOP); the signed
   label-freeze record present in the clone at its sha256.
6. **Staging** (the one network step, as the staged E0 job): the arm's registry weights from Hugging Face at their
   pinned revisions, each file's size and sha256 against the clone's ``registry.yaml``; the pool tokenizers (prompt
   replay) into the job's ``HF_HOME``. The host config's ``local_path`` / ``adapter_local_path`` must name the
   staged directories. Every later step runs with ``HF_HUB_OFFLINE=1`` and ``TRANSFORMERS_OFFLINE=1``.
7. **Data.** ``trackp.py sft-data`` on the pinned table (``sweep1_v3``), the sweep-1 index and classification of
   the clone, the labels from the receipted partition (``LabelBlockSource`` re-checks every receipt binding), the
   decided policy and the signed P3 split file (the SFT config's ``splits.split_file``), and the signed label
   freeze record (``--label-freeze``). The data directory's ``sft_data.json`` sha256 is recorded, and its path-free
   identity (``data_identity``: the manifest with every ``path`` removed, which carries the rows, splits, table, sweep
   index, classification and label sha256s); ``assemble`` requires the identity equal across the four jobs (the
   absolute job directories differ).
8. **Grid → select → learning curve** (P4-JOB A): ``sft-dev`` for 3 lr × 3 seeds (R1-LR-GRID), ``sft-select``,
   then the learning-curve points below the training-set size at the selected lr × 3 seeds (P4-LC A,
   ``lc_subset``); the full-set point is the selected-lr grid runs. Every run's ``sft_report.json`` must carry the
   fixed protocol (``check_run_protocol``: micro-batch 8, effective batch 16, the SFT config's epochs, patience and
   loss, its lr and seed).
9. **Readiness numbers.** The instance-cluster bootstrap on primary val (``rps_skill_bootstrap``, §3); no gate
   decision.
10. **Per-arm pin file** (``arm_pin``) and the **synthetic test path** (P4-PHASE1-TEST A): a synthetic-label data
    build of the same table, a 2-step ``sft-dev`` on it, and the test evaluator's prompt replay, prediction and
    report with its one-read ledger (``<out>/ledgers/sweep1_v3/<LEDGER_NAME>``). No real-label test is read. The
    ledger lives in each job's ``out/``, so "one read per arm" holds within a job; across repeats of a job each
    attempt has its own ledger (harmless: the labels are synthetic).
11. **Outputs.** ``out/`` (run directories, manifests, reports, the pin file, the logs) in ``out.tar``,
    ``job_record.json`` (schema ``trackp_p4_job_record/1``) and ``SHA256SUMS``; ``seal`` copies every attempt (a
    STOP-free one, a STOP, one without the H200/image identity, one whose record is empty or missing after a
    walltime kill) under ``/ceph/srv/dwong/paperb/trackp_p4/<run_id>/<arm>/attempt-N/`` without overwrite and writes
    a receipt binding the record and the wrapper log, with the GPU-hours it charges to the cap.

**Cap** (P4-CAP A, a reporting threshold under R1-NO-TIMEOUT (3)): the projection (per arm: its largest estimate over
the admitted classes, each of which must come from that class's SFT probe at launch, × the wall factor + startup) is
reported against 40 GPU-h and 64 slot-hours; an HTCondor job's requested walltime stays within 86,400 s (a scheduler
request). The GPU-hours consumed are summed over **every** sealed attempt of the run (``charged_hours``: the receipt's
charge: the record's ``gpu_hours``, or the arm's requested walltime when the record has none; for a direct attempt the
launcher's wall clock or the record's hours, whichever is larger): ``assemble`` and the switch report a total that
reaches the figure to the author, and do not refuse. **P4-PROBECAP A**: the H200 SFT probe's
GPU-hours count against the same 40 GPU-h. The spec carries them as ``caps.probe_gpu_hours`` (filled from the probe
record's ``p4_probe_gpu_hours:`` line, which ``probe_records`` computes over every sealed probe attempt of every probe
run); launch validation requires it, and the projection, ``charged_hours`` (hence ``assemble`` and the switch's
``check_cap``) add it.

**Probe mode** (F1 of the cluster test plan, its §4.2; P4-PROBE A: at most 50 steps of ``sft-dev`` on synthetic
labels, one job per base, nothing kept as an arm). ``probe`` runs the job's own steps 1-4 and 6 unchanged, moves the
transferred table files into place (no label file, receipt or freeze record is transferred or read; ``inputs`` is not
called), builds a synthetic-label data directory, and runs one ``sft-dev --steps 50`` (lr 1e-05, seed 0) with the
assigned GPU's device memory sampled from outside by ``nvidia-smi --id=<uuid>`` and wall-clock stamps around it. No
test path, selection, learning curve, bootstrap or pin file. ``out.tar`` holds an allow-list (logs, the run's reports
and metrics, the data manifest, the memory samples), never a checkpoint. The probe spec (``p4_probe_spec.json``, a
template with three host fields) is validated at probe strength (``validate_probe_spec``) before submission and in the
job; its run id keeps every probe attempt out of the P.4 run's tree. ``probe_records`` builds the §4.4 record and the
§4.5 hours from the sealed probe attempts.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "trackp_p4_job/v1"
RECORD_SCHEMA = "trackp_p4_job_record/1"
RECEIPT_SCHEMA = "trackp_p4_seal_receipt/1"
ASSEMBLY_SCHEMA = "trackp_p4_assembly/1"
ENGINEERING_ONLY = "ENGINEERING_ONLY"
GPU_MODEL = "NVIDIA H200"
PAPER_REPO = "https://github.com/dowlingwong/Agent_paper_B.git"
ENV3_PYTHON = "/opt/r1/envs/trackp/bin/python"
UV = "/opt/uv/uv"                                # uv 0.13.6 in the image (UV_INSTALL_DIR=/opt/uv); env3 has no pip
VERSIONS = Path("/opt/r1/VERSIONS.txt")
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/trackp_p4")
ENV3_FREEZE = "docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt"
ENV3_FREEZE_SHA256 = "50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08"
ENV3_FREEZE_SORTED_SHA256 = "e607c1d87221999015c1cd988c38dbc2e8deb51938403e2ca2c0c2832755419b"
VENV_LEASE_FD_ENV = "P4_VENV_LEASE_FD"
HOST_CONFIG = "r1/scripts/configs/trackp_htcondor_v2.json"   # the nemo2_h200 class's host config
ADA_HOST_CONFIG = "r1/scripts/configs/trackp_ada_v1.json"      # the ada_rtx6000 class's host config
# R1-HOST-FREE (1): the admitted host classes. A job is told its class (``--host-class``); the landed GPU must be that
# class's model and compute capability, exactly one GPU visible; the record names host, GPU model, uuid, driver and the
# env3 freeze. ``launch`` is how a job of the class starts: "htcondor" (p4_render_jdl + p4_switch, condor_submit) or
# "direct" (p4_direct.py over SSH under a GPU lease). ``probe_label`` is the key of the class's SFT probe record in the
# spec's estimate.source and in the note (the H200 one keeps its name, h200_sft_probe). ``smoke_label`` is the note key
# that names the class's Track P smoke and E0 equivalence records (R1-QTORCH-AMEND: one smoke and one E0 check per GPU
# model actually used; the switch requires the line, with records on origin/main, for every admitted class).
HOST_CLASSES = {
    "nemo2_h200": {"launch": "htcondor", "gpu_name": "NVIDIA H200", "compute_capability": "9.0",
                   "host_config_path": HOST_CONFIG, "probe_label": "h200_sft_probe",
                   "smoke_label": "h200_smoke_e0"},
    "ada_rtx6000": {"launch": "direct", "gpu_name": "NVIDIA RTX 6000 Ada Generation", "compute_capability": "8.9",
                    "host_config_path": ADA_HOST_CONFIG, "probe_label": "ada_sft_probe",
                    "smoke_label": "ada_smoke_e0"},
}
HOST_FIXED = ("launch", "gpu_name", "compute_capability")       # a spec's hosts.<class> carries these values as above
DIRECT_LAUNCH_FILE = "direct_launch.json"        # the direct launcher's record beside the job outputs (p4_direct.py)
DIRECT_LAUNCH_SCHEMA = "trackp_p4_direct_launch/1"
TRACKP_SCRIPT = "r1/scripts/trackp.py"
SFT_CONFIG = "r1/scripts/configs/trackp_sft.json"
SPLIT_FILE = {"path": "r1/c3/splits/c3_p3_split_v1.json",
              "sha256": "b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569"}
SOURCE_BLOCK_SHA256 = "cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca"
TABLE_PIN = "sweep1_v3"
SWEEP_INDEX = "results/r1/pilot/C3_sweep_index_20261028T033315Z.json"
CLASSIFICATION = "results/r1/evidence/C3_sweep_classification_20261028.json"
ARMS = {                                        # P4-ARMS A: the Kev bases and both Qwen controls (R1-C3-CONTROL)
    "kev-0.8b": ("kev-0.8b", "qwen3.5-0.8b-base"),            # (adapter registry key, base registry key)
    "kev-4b": ("kev-4b", "qwen3.5-4b-base"),
    "qwen3.5-0.8b-base": (None, "qwen3.5-0.8b-base"),
    "qwen3.5-4b-base": (None, "qwen3.5-4b-base"),
}
CONTROLS = ("qwen3.5-0.8b-base", "qwen3.5-4b-base")
FIRST_ARM = "kev-0.8b"                          # R1-TRACKP-P4-RUNNER-DECISIONS (3): the first, solo arm
CHECKPOINT_ARMS = {"kev-4b": True, "qwen3.5-4b-base": True}
LR_GRID = (1e-05, 3e-05, 0.0001)                # R1-LR-GRID
SEEDS = (0, 1, 2)
LC_POINTS = (250, 500)                          # P4-LC A
MICRO_BATCH = 8                                 # P4-MB A
CAP_GPU_HOURS = 40.0                            # P4-CAP A
CAP_SLOT_HOURS = 64.0                           # 1.6 x the cap
MAX_WALLTIME_S = 86400
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-TRACKP-P4-DECISIONS", "R1-TRACKP-P4-RUNNER-DECISIONS", "R1-TRACKP-IMAGE-V21",
             "R1-TRACKP-IMAGE-V22", "R1-TRACKP-IMAGE-V22-B", "R1-TRACKP-V21-FREEZE", "R1-HTC-QTORCH",
             "R1-S2-LABELS-TRAINDEV-RELEASE", "R1-TRACKP-SFT-DEV", "R1-SWEEP2-PREREG", "R1-HOST-FREE",
             "R1-P4-4B-CHECKPOINT")
TRANSFER_INPUTS = ("p4_job.sh", "p4_lib.py", "p4_spec.json", "proposals.jsonl", "configs.json", "build.json",
                   "label_block.traindev.jsonl", "RECEIPT.json")
TRANSFER_OUTPUTS = "out.tar,job_record.json,SHA256SUMS,p4_run.log"
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
DIGEST = re.compile(r"^ghcr\.io/dowlingwong/r1-htc-gpu@sha256:[0-9a-f]{64}$")
IMAGE_V2 = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd"
# image v2.1 (R1-TRACKP-IMAGE-V21, V21_IMAGE_006FC315.md): its prebuilt causal_conv1d fails to import (smoke 759983 STOP,
# R1-TRACKP-IMAGE-V22), so it is not the P.4 image either
IMAGE_V21 = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:31478d990c8aeb9fdeb11ddf96055049180c2f45e4a8c2c9f050acd41e663831"
IMAGE_ROW = "R1-TRACKP-IMAGE-V22-B"             # the row image v2.2 was built under (option B: source build)
PLACEHOLDER = re.compile(r"^(TODO|PENDING|PLACEHOLDER|TBD|FILL)", re.IGNORECASE)
IMAGE_V22 = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949"
P4_RUN_ID = "trackp-p4-p1-20261122-a"           # the P.4 phase-1 run (the note's run_id)
PKG_REL = "r1/scripts/htcondor/trackp_p4"
# P4-F2 A, for the note's label_table_binding: line (the job itself uses arms_freeze's and p4_phase1's values; a test
# checks these copies equal them)
SEALED_V2_PROPOSALS_SHA256 = "b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4"
V3_PROPOSALS_SHA256 = "d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5"
FEAT_ONE_IDENTITY = {"path": "docs/r1/reports/arms_a3_20261123/feat_one_identity.json",
                     "sha256": "039b8360e293f44632e6a55bff79d32f2b4769045c112cfa4d54a596564853df"}
# --- probe mode (cluster test plan §4.2; P4-PROBE A, P4-PROBECAP A)
PROBE_RUN_ID = re.compile(r"^trackp-p4-probe-\d{8}-[a-z]$")
PROBE_SPEC_FILE = "p4_probe_spec.json"           # the committed template in this package
ADA_REPROBE = {
    "run_id": "trackp-p4-probe-20261127-b",
    "prior_run_id": "trackp-p4-probe-20261125-a",
    "prior_spec_sha256": "540bd9798017260ca391612351706189712221c269482a7d47385695160a50a2",
    "prior_paper_commit": "91cfd48a67f8d62d4e20826976cbdbdbcfcaf505",
}
PROBE_RECORD_SCHEMA = "trackp_p4_probe_record/1"
PROBE_TABLE_SCHEMA = "trackp_p4_h200_sft_probe/1"
PROBE = {"steps": 50, "lr": 1e-05, "seed": 0, "sample_ms": 500, "walltime_s": 7200, "labels": "synthetic"}
PROBE_FILLED = (("paper", "commit"), ("image", "versions_sha256"), ("host_class",),
                *(("hosts", c, "host_config", "sha256") for c in HOST_CLASSES))
PROBE_TRANSFER_INPUTS = ("p4_probe.sh", "p4_lib.py", "p4_probe_spec.json", "proposals.jsonl", "configs.json",
                         "build.json")
PROBE_KEEP = ("out/logs", "out/gpu_lease_log.jsonl", "out/probe/wall.json", "out/probe/{arm}.gpu_mem.csv",
              "out/probe/{arm}/report.json", "out/probe/{arm}/manifest.json",
              "out/probe/{arm}/stage_s/sft_report.json", "out/probe/{arm}/stage_s/metrics.jsonl",
              "out/probe/{arm}/stage_s/best.json", "out/sft_data_synthetic/data/sft_data.json")
PROBE_MIN_STEP = 6                               # §4.4: per-step statistics over steps 6 ... stopped_at


class Stop(Exception):
    stop_class = "infrastructure"


class ProtocolStop(Stop):
    stop_class = "protocol"


class ArmStop(Stop):
    stop_class = "arm"


# =============================================================================================== spec
def load_spec(path: Path) -> dict:
    return json.loads(_read_utf8(Path(path)))


def _placeholder(v) -> bool:
    return isinstance(v, str) and bool(PLACEHOLDER.match(v))


def _pin(value, name: str, pattern=SHA, *, allow: bool) -> None:
    if allow and _placeholder(value):
        return
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise Stop(f"STOP: {name} must be filled ({pattern.pattern})")


def arm_hours(spec: dict, arm: str, host_class: str | None = None) -> float:
    """The arm's estimated training hours on ``host_class`` (its ``hosts.<class>.estimate.hours``), or, with no class,
    the largest over the spec's admitted classes: an arm may land on any of them, so the projection and the walltime
    bound take the slowest (R1-HOST-FREE (5); with one admitted class this is that class's value). The largest is used
    only for the projection, a pending submission's charge and an incomplete launcher record's bound; an HTCondor JDL
    requests its own class's value (``p4_render_jdl.render``), the value ``validate_spec`` checks against 86,400 s."""
    classes = [host_class] if host_class is not None else sorted(spec["hosts"])
    return max(float(spec["hosts"][c]["estimate"]["hours"][arm]) for c in classes)


def arm_walltime_s(spec: dict, arm: str, host_class: str | None = None) -> int:
    lay = spec["layout"]
    return int(math.ceil(arm_hours(spec, arm, host_class) * 3600 * float(lay["wall_factor"]) + float(lay["startup_s"])))


def host_class_of(spec: dict, host_class: str, *, launch: str | None = None) -> dict:
    """The admitted class ``host_class`` of the spec (its fixed values with the spec's host config and estimate), or a
    STOP when the spec does not admit it or (``launch`` given) it does not start that way."""
    hosts = spec.get("hosts") if isinstance(spec.get("hosts"), dict) else {}
    if host_class not in HOST_CLASSES or host_class not in hosts:
        raise Stop(f"STOP: host class {host_class!r} is not admitted by the spec (hosts: {sorted(hosts)}; R1-HOST-FREE)")
    if launch is not None and HOST_CLASSES[host_class]["launch"] != launch:
        raise Stop(f"STOP: host class {host_class} starts by {HOST_CLASSES[host_class]['launch']}, not {launch}")
    return {"host_class": host_class, **HOST_CLASSES[host_class], "host_config": dict(hosts[host_class]["host_config"]),
            "estimate": hosts[host_class].get("estimate")}


def probe_gpu_hours(spec: dict) -> float | None:
    """P4-PROBECAP A: the GPU-hours the H200 SFT probe already charged to the cap (``caps.probe_gpu_hours``), or None
    while it is a placeholder (launch validation requires the number)."""
    v = (spec.get("caps") or {}).get("probe_gpu_hours")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def projection(spec: dict) -> dict:
    """The four jobs' projected GPU-hours and slot-hours; ``within_cap`` adds the probe's charged GPU-hours
    (P4-PROBECAP A; 0 while ``caps.probe_gpu_hours`` is a placeholder, which only default-strength validation admits).
    Each arm is projected at its largest estimate over the admitted host classes (``arm_hours``), wherever it lands;
    GPU-hours count on any card (R1-HOST-FREE (5))."""
    per = {a: {"gpu_hours": round(arm_hours(spec, a) + spec["layout"]["startup_s"] / 3600, 3),
               "walltime_s": arm_walltime_s(spec, a)} for a in spec["arms"]}
    gpu = round(sum(v["gpu_hours"] for v in per.values()), 3)
    slot = round(sum(v["walltime_s"] for v in per.values()) / 3600, 3)
    probe = probe_gpu_hours(spec)
    with_probe = round(gpu + (probe or 0.0), 3)
    return {"per_arm": per, "total_gpu_hours": gpu, "probe_gpu_hours": probe,
            "total_with_probe_gpu_hours": with_probe, "total_slot_hours": slot,
            "cap_gpu_hours": spec["caps"]["gpu_hours"], "cap_slot_hours": spec["caps"]["slot_hours"],
            "within_cap": with_probe <= spec["caps"]["gpu_hours"] and slot <= spec["caps"]["slot_hours"]}


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """Fail-closed; ``launch=True`` refuses every placeholder (the image VERSIONS sha256, each admitted class's host
    config sha256 after its fill, the partition, receipt and freeze-record sha256, each admitted class's probe-based
    estimate, the probe's charged GPU-hours ``caps.probe_gpu_hours``) and refuses a probe spec (one with a ``probe``
    block). R1-HOST-FREE: ``hosts`` admits one or more classes of ``HOST_CLASSES`` with their fixed launch, GPU name and
    compute capability, each with its own ``host_config`` {path, sha256} and ``estimate`` {hours, source}; the old fixed
    ``gpu_model`` and the top-level ``host_config`` / ``estimate`` are refused. At launch every admitted class needs
    its own SFT probe estimate (``<probe_label>: docs/r1/reports/<record>.md``), so no arm can be staged on a class
    without one."""
    allow = not launch
    if spec.get("schema") != SCHEMA or spec.get("label") != ENGINEERING_ONLY or spec.get("phase") != 1:
        raise Stop(f"STOP: spec must be {SCHEMA}, ENGINEERING_ONLY, phase 1")
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not SAFE.fullmatch(run_id) or run_id in (".", ".."):
        raise Stop("STOP: run_id must be a safe path component")
    paper = spec.get("paper") or {}
    if paper.get("repo") != PAPER_REPO:
        raise Stop(f"STOP: paper.repo must be {PAPER_REPO}")
    _pin(paper.get("commit"), "paper.commit", COMMIT, allow=allow)
    image = spec.get("image") or {}
    _pin(image.get("digest"), "image.digest", DIGEST, allow=allow)
    if image.get("digest") in (IMAGE_V2, IMAGE_V21):
        raise Stop("STOP: image v2 and v2.1 are not the P.4 image: v2.2 by digest (R1-TRACKP-IMAGE-V22-B)")
    _pin(image.get("versions_sha256"), "image.versions_sha256", allow=allow)
    if image.get("row") != IMAGE_ROW:
        raise Stop(f"STOP: image.row must be {IMAGE_ROW}")
    if "gpu_model" in spec:
        raise Stop("STOP: gpu_model is replaced by the admitted host classes (hosts); the GPU model is recorded per job, "
                   "not fixed (R1-HOST-FREE (1))")
    for key in ("host_config", "estimate"):
        if key in spec:
            raise Stop(f"STOP: {key} is per host class (hosts.<class>.{key}; R1-HOST-FREE)")
    hosts = spec.get("hosts")
    if not isinstance(hosts, dict) or not hosts or set(hosts) - set(HOST_CLASSES):
        raise Stop(f"STOP: hosts must admit one or more of the host classes {sorted(HOST_CLASSES)} (R1-HOST-FREE (1))")
    env3 = spec.get("env3") or {}
    want_env3 = {"python": ENV3_PYTHON, "freeze": ENV3_FREEZE, "freeze_sha256": ENV3_FREEZE_SHA256,
                 "rule": "R1-TRACKP-V21-FREEZE"}
    if {k: env3.get(k) for k in want_env3} != want_env3:
        raise Stop(f"STOP: env3 must be {want_env3} (R1-ENV-PIN, R1-HTC-QTORCH, R1-TRACKP-V21-FREEZE)")
    block = spec.get("sft_config") or {}
    if block.get("path") != SFT_CONFIG:
        raise Stop(f"STOP: sft_config.path must be {SFT_CONFIG}")
    _pin(block.get("sha256"), "sft_config.sha256", allow=False)
    for cls in sorted(hosts):                       # the fixed values and the host config of each admitted class
        h = hosts[cls]
        if not isinstance(h, dict) or set(h) - {*HOST_FIXED, "host_config", "estimate", "comment"}:
            raise Stop(f"STOP: hosts.{cls} holds only {list(HOST_FIXED)}, host_config, estimate (and a comment)")
        want = {k: HOST_CLASSES[cls][k] for k in HOST_FIXED}
        if {k: h.get(k) for k in HOST_FIXED} != want:
            raise Stop(f"STOP: hosts.{cls} must be {want} (R1-HOST-FREE (1))")
        hc = h.get("host_config") or {}
        if hc.get("path") != HOST_CLASSES[cls]["host_config_path"]:
            raise Stop(f"STOP: hosts.{cls}.host_config.path must be {HOST_CLASSES[cls]['host_config_path']}")
        _pin(hc.get("sha256"), f"hosts.{cls}.host_config.sha256", allow=allow)
    hc_class = spec.get("host_class")
    if launch and hc_class is not None:
        raise Stop("STOP: a P.4 launch spec admits host classes; each job is told its class (--host-class), the spec "
                   "names none (host_class is a probe-spec field)")
    if hc_class is not None and not (allow and _placeholder(hc_class)) and hc_class not in hosts:
        raise Stop(f"STOP: host_class must be one of the admitted classes {sorted(hosts)}")
    if spec.get("split_file") != SPLIT_FILE:
        raise Stop(f"STOP: split_file must be the signed P3 split file {SPLIT_FILE} (P4-P1SPLIT A)")
    table = spec.get("table") or {}
    if table.get("pin") != TABLE_PIN or table.get("sweep_index") != SWEEP_INDEX or \
            table.get("classification") != CLASSIFICATION:
        raise Stop(f"STOP: table must be the pin {TABLE_PIN} with its sweep index and classification")
    labels = spec.get("labels") or {}
    if labels.get("source") != "sweep1" or labels.get("stage") != "traindev":
        raise Stop("STOP: labels must be the receipted sweep-1 train/dev partition (P4-LABELS A)")
    if labels.get("source_block_sha256") != SOURCE_BLOCK_SHA256:
        raise Stop(f"STOP: labels.source_block_sha256 must be the frozen block {SOURCE_BLOCK_SHA256}")
    for key in ("partition_sha256", "receipt_sha256"):
        _pin(labels.get(key), f"labels.{key}", allow=allow)
    freeze = labels.get("freeze_record") or {}
    if not isinstance(freeze.get("path"), str) or not (_placeholder(freeze["path"]) and allow or
                                                        re.fullmatch(r"docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md",
                                                                     freeze["path"])):
        raise Stop("STOP: labels.freeze_record.path must be docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md")
    _pin(freeze.get("sha256"), "labels.freeze_record.sha256", allow=allow)
    arms = spec.get("arms")
    if not isinstance(arms, list) or not arms or len(set(arms)) != len(arms) or set(arms) - set(ARMS):
        raise Stop(f"STOP: arms must be distinct members of {sorted(ARMS)} (P4-ARMS A)")
    missing = [c for c in CONTROLS if c not in arms]
    if missing:
        raise Stop(f"STOP: the controls {missing} are always carried (R1-C3-CONTROL; P4-ARMS A)")
    if spec.get("first_arm") != FIRST_ARM or FIRST_ARM not in arms:
        raise Stop(f"STOP: first_arm must be {FIRST_ARM}, one of the arms, submitted alone first "
                   "(R1-TRACKP-P4-RUNNER-DECISIONS (3))")
    proto = spec.get("protocol") or {}
    want = {"lr_grid": list(LR_GRID), "seeds": list(SEEDS), "lc_points": list(LC_POINTS), "micro_batch": MICRO_BATCH,
            "effective_batch": 16, "duplicate_policy": "heldout_excludes_seen", "real_label_test_read": "none",
            "bootstrap": {"resamples": 2000, "seed": 20261108}, "lc_seed": 20261122}
    for key, value in want.items():
        if proto.get(key) != value:
            raise Stop(f"STOP: protocol.{key} must be {value!r} (fixed)")
    if launch or "gradient_checkpointing" in proto:
        checkpointing = proto.get("gradient_checkpointing")
        if not isinstance(checkpointing, dict) or set(checkpointing) != set(CHECKPOINT_ARMS) or \
                any(v is not True for v in checkpointing.values()):
            raise Stop(f"STOP: protocol.gradient_checkpointing must be {CHECKPOINT_ARMS} (R1-P4-4B-CHECKPOINT)")
    caps = spec.get("caps") or {}
    if caps.get("gpu_hours") != CAP_GPU_HOURS or caps.get("slot_hours") != CAP_SLOT_HOURS:
        raise Stop(f"STOP: caps must be {CAP_GPU_HOURS} GPU-h and {CAP_SLOT_HOURS} slot-hours (P4-CAP A)")
    pg = caps.get("probe_gpu_hours")
    number = isinstance(pg, (int, float)) and not isinstance(pg, bool)
    if launch and not (number and 0 < pg and round(pg, 2) == pg):
        raise Stop("STOP: caps.probe_gpu_hours must be the SFT probes' charged GPU-hours (the probe record's "
                   "p4_probe_gpu_hours: line), positive with at most two decimals, before launch (P4-PROBECAP A; "
                   "R1-NO-TIMEOUT (3): 40 GPU-h is a reporting threshold, not a bound)")
    if not launch and not (_placeholder(pg) or (number and 0 <= pg)):
        raise Stop("STOP: caps.probe_gpu_hours must be a placeholder or non-negative GPU-hours (P4-PROBECAP A)")
    pcf = caps.get("probe_charge_files")
    pcf_ok = isinstance(pcf, dict) and all(isinstance(r, str) and PROBE_RUN_ID.fullmatch(r) and isinstance(v, list)
                                           and v and all(isinstance(x, str) and SHA.fullmatch(x) for x in v)
                                           for r, v in pcf.items())
    if launch and not pcf_ok:
        raise Stop("STOP: caps.probe_charge_files must list the probe charge files ({<probe run>: [<sha256>, ...]}, the "
                   "probe record's p4_probe_charge_file: lines) before launch (P4-PROBECAP A)")
    if not launch and not (_placeholder(pcf) or pcf_ok):
        raise Stop("STOP: caps.probe_charge_files must be a placeholder or {<probe run>: [<sha256>, ...]}")
    if launch and spec.get("probe") is not None:
        raise Stop("STOP: a probe spec is never a P.4 launch spec (P4-PROBE A)")
    lay = spec.get("layout") or {}
    for key, lo, hi in (("wall_factor", 1.2, 3.0), ("startup_s", 600, 3600), ("request_cpus", 4, 32),
                        ("request_memory_mb", 32768, 262144), ("request_disk_kb", 50_000_000, 500_000_000)):
        v = lay.get(key)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
            raise Stop(f"STOP: layout.{key} must be in [{lo}, {hi}]")
    for cls in sorted(hosts):                       # per class: its probe-based estimate (P5; P4-CAP A)
        est = hosts[cls].get("estimate") or {}
        hours = est.get("hours") or {}
        if set(hours) != set(arms) or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v <= 20
                                          for v in hours.values()):
            raise Stop(f"STOP: hosts.{cls}.estimate.hours must give (0, 20] GPU-hours of training for every arm")
        source, label = str(est.get("source", "")), HOST_CLASSES[cls]["probe_label"]
        if launch and not re.fullmatch(rf"{label}: docs/r1/reports/\S+\.md", source):
            raise Stop(f"STOP: hosts.{cls}.estimate.source must be '{label}: docs/r1/reports/<record>.md' before launch: "
                       f"no arm runs on a class without its own SFT probe estimate (P5; P4-CAP A; R1-HOST-FREE)")
    proj = projection(spec)
    for cls in sorted(c for c in hosts if HOST_CLASSES[c]["launch"] == "htcondor"):   # one HTCondor job's request
        for arm in arms:
            w = arm_walltime_s(spec, arm, cls)
            if w > MAX_WALLTIME_S:
                raise Stop(f"STOP: {arm} would request {w} s on {cls}, over {MAX_WALLTIME_S} s (one HTCondor job: a "
                           "scheduler request, not a limit on the run)")
    return {"spec": spec, "run_id": run_id, "projection": proj, "threshold": threshold_report(proj)}


def threshold_report(proj: dict, charged: float | None = None) -> dict:
    """R1-NO-TIMEOUT (3): the 40 GPU-h and 64 slot-hour figures of P4-CAP A are reporting thresholds for P.4 phase 1
    (work not yet under a signed note): usage (``charged``, when given, else the projection with the probes' charge)
    is reported against them, and reaching one is reported to the author at once (``report_to_author``). It never
    refuses a spec, a submission, a launch or an assembly."""
    gpu = proj["total_with_probe_gpu_hours"] if charged is None else charged
    reached = [k for k, have, cap in (("gpu_hours", gpu, proj["cap_gpu_hours"]),
                                     ("slot_hours", proj["total_slot_hours"], proj["cap_slot_hours"])) if have >= cap]
    return {"rule": "R1-NO-TIMEOUT (3): a reporting threshold, not a refusal", "reached": reached,
            "report_to_author": bool(reached), "gpu_hours": gpu, "gpu_hours_threshold": proj["cap_gpu_hours"],
            "slot_hours_projected": proj["total_slot_hours"], "slot_hours_threshold": proj["cap_slot_hours"]}


# =============================================================================================== helpers
def _sh(argv, *, cwd=None, env=None, timeout=3600) -> subprocess.CompletedProcess:
    opts = {}
    if os.environ.get("P4_VENV_PYTHON"):
        # A native training subprocess retains the launcher flock if its parents exit first.
        opts["pass_fds"] = (venv_lease_fd(),)
    return subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, **opts)


def _git(repo: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=False,
                          timeout=timeout)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_utf8(path: Path, stop=None) -> str:
    """A text file the job reads, decoded as UTF-8 whatever the locale (an ASCII ``LC_ALL=C`` included); a file that
    is not UTF-8 is a STOP of class ``stop`` (default: infrastructure), never a ``UnicodeDecodeError``."""
    try:
        return Path(path).read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise (stop or Stop)(f"STOP: {path} is not UTF-8 text ({exc.reason} at byte {exc.start})") from None


def _utc(t: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


# The running job's host class and its host config (set by ``run_job`` / ``run_probe`` for the class the job was told,
# restored afterwards). Outside a job (the desk, the tests) it is the HTCondor class, so every helper keeps its earlier
# behaviour there. The job steps read the class's host config through ``job_host_config`` (trackp.py --config, the local
# paths, the arm pin), and ``gpu_identity`` / ``configs`` take the class from here unless given one.
_JOB_HOST = {"host_class": "nemo2_h200", "host_config": HOST_CONFIG}


def job_host_class() -> str:
    return _JOB_HOST["host_class"]


def job_host_config() -> str:
    return _JOB_HOST["host_config"]


class _job_host:
    """Context manager: the job runs as ``host_class`` (its host config path from ``HOST_CLASSES``)."""

    def __init__(self, host_class: str):
        if host_class not in HOST_CLASSES:
            raise Stop(f"STOP: unknown host class {host_class!r} (R1-HOST-FREE: {sorted(HOST_CLASSES)})")
        self.new = {"host_class": host_class, "host_config": HOST_CLASSES[host_class]["host_config_path"]}

    def __enter__(self):
        self.old = dict(_JOB_HOST)
        _JOB_HOST.update(self.new)
        return self

    def __exit__(self, *exc):
        _JOB_HOST.clear()
        _JOB_HOST.update(self.old)
        return False


def _phase1(clone: Path):
    """``r1.c3.train.p4_phase1`` from the paper clone (the reviewed code at the paper commit)."""
    if str(clone) not in sys.path:
        sys.path.insert(0, str(clone))
    from r1.c3.train import p4_phase1  # noqa: PLC0415
    return p4_phase1


def _write_sums(root: Path, names) -> None:
    lines = []
    for name in names:
        path = root / name
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []
        lines += [f"{_sha_file(f)}  {f.relative_to(root)}" for f in files]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


# =============================================================================================== host checks
def ada_venv_config(block: dict | None) -> dict:
    """Read the reviewed native runtime from the Ada host configuration."""
    venv = (block or {}).get("venv") or {}
    python = venv.get("python")
    if not isinstance(python, str) or not Path(python).is_absolute() or ".." in Path(python).parts or \
            not python.endswith("/bin/python") or venv.get("version") != "3.12.10":
        raise Stop("STOP: the Ada venv needs its reviewed absolute Python 3.12.10 interpreter")
    return {"python": python, "version": venv["version"]}


def job_python() -> str:
    return os.environ.get("P4_VENV_PYTHON") or ENV3_PYTHON


def venv_lease_fd() -> int:
    try:
        fd = int(os.environ[VENV_LEASE_FD_ENV])
        if fd < 3:
            raise ValueError("reserved standard descriptor")
        os.fstat(fd)
    except (KeyError, ValueError, OSError):
        raise Stop("STOP: the Ada venv job did not inherit the launcher lease descriptor") from None
    return fd


def verify_ada_venv(spec: dict, clone: Path) -> dict:
    """Bind this process and its subprocesses to the venv in the pinned Ada host config."""
    host = host_class_of(spec, "ada_rtx6000", launch="direct")["host_config"]
    path = clone / host["path"]
    if _sha_file(path) != host["sha256"]:
        raise Stop("STOP: the Ada host configuration differs from the spec")
    block = json.loads(_read_utf8(path)).get("direct") or {}
    want = ada_venv_config(block)
    actual = {"python": sys.executable, "version": ".".join(map(str, sys.version_info[:3]))}
    if job_host_class() != "ada_rtx6000" or block.get("container_runtime") != "venv" or actual != want or \
            job_python() != want["python"] or sys.prefix == sys.base_prefix or \
            Path(sys.prefix) != Path(want["python"]).parent.parent:
        raise Stop("STOP: this job is not running the venv named in the pinned Ada host configuration")
    return actual


def image_identity(spec: dict, versions: Path = VERSIONS) -> dict:
    if not versions.is_file():
        raise Stop(f"STOP: {versions} missing: not the pinned image")
    got = _sha_file(versions)
    if got != spec["image"]["versions_sha256"]:
        raise Stop(f"STOP: {versions} sha256 {got} differs from the image v2.2 pin")
    for tool in (ENV3_PYTHON, UV):
        if not Path(tool).exists():
            raise Stop(f"STOP: {tool} missing from the image")
    return {"digest": spec["image"]["digest"], "versions_sha256": got}


def gpu_identity(sh=_sh, host_class: str | None = None) -> dict:
    """Exactly one GPU visible (unscoped ``nvidia-smi``), and it is the GPU of the job's declared host class (name and
    compute capability; ``host_class`` defaults to the running job's class): R1-HOST-FREE (1). A job never moves to
    another class: a GPU of another model is a STOP, whatever class it would fit."""
    cls = host_class or job_host_class()
    want = HOST_CLASSES[cls]
    argv = ["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,compute_cap", "--format=csv,noheader"]
    if os.environ.get("P4_VENV_PYTHON"):
        leased = os.environ.get(LEASED_GPU_ENV, "")
        if cls != "ada_rtx6000" or not re.fullmatch(r"GPU-[0-9a-fA-F-]+", leased) or \
                os.environ.get("CUDA_VISIBLE_DEVICES") != leased:
            raise Stop("STOP: an Ada venv job must bind CUDA visibility to exactly the leased GPU UUID")
        argv.insert(1, f"--id={leased}")
    res = sh(argv, timeout=120)
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi failed: {res.stderr.strip()[:200]}")
    gpus = [[x.strip() for x in line.split(",")] for line in res.stdout.strip().splitlines() if line.strip()]
    if len(gpus) != 1:
        raise Stop(f"STOP: one GPU per P.4 job, nvidia-smi lists {len(gpus)}")
    if len(gpus[0]) != 5:
        raise Stop(f"STOP: nvidia-smi printed {gpus[0]!r}, not name, uuid, driver, memory, compute capability")
    name, uuid, driver, memory, cap = gpus[0]
    if name != want["gpu_name"] or cap != want["compute_capability"]:
        raise Stop(f"STOP: landed on {name} (compute capability {cap}), not {want['gpu_name']} "
                   f"({want['compute_capability']}) of the job's host class {cls} (no run moves to another GPU model)")
    return {"name": name, "uuid": uuid, "driver": driver, "memory_total": memory, "compute_capability": cap,
            "host_class": cls}


LEASED_GPU_ENV = "P4_LEASED_GPU_UUID"            # set by p4_direct.py: the card the launcher leased, by UUID


def card_processes(sh=_sh, uuid: str | None = None) -> dict:
    """R1-CARD-SHARE (4): the compute processes on the job's card as ``nvidia-smi --query-compute-apps`` shows them
    from inside the job (count and memory only; rows of another card's UUID are not counted). A query that fails is
    recorded, never a STOP. (Inside a container another user's processes may not be visible; for a direct job the
    launcher's host-side count, sealed with the attempt, is the record that decides R1-CARD-SHARE (3).)"""
    try:
        res = sh(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv,noheader,nounits"],
                 timeout=120)
        if res.returncode != 0:
            return {"error": f"nvidia-smi rc={res.returncode}: {(res.stderr or '').strip()[:160]}"}
        count, mem = 0, 0.0
        for line in (res.stdout or "").splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) < 3 or (uuid and parts[0] != uuid):
                continue
            count += 1
            try:
                mem += float(parts[2])
            except ValueError:
                pass
        return {"count": count, "memory_mib": mem}
    except Exception as exc:  # noqa: BLE001 - a record, never a STOP
        return {"error": f"{type(exc).__name__}: {exc}"[:200]}


def shared_card_loss(record: dict, *others: dict | None) -> bool:
    """R1-CARD-SHARE (3): an arm STOP (a CUDA OOM) of an attempt whose card had another compute process at its start
    or end (the job's own counts, and any host-side counts given in ``others``) is an infrastructure failure: it is
    sealed and the same run is attempted again in a new attempt directory; never an outcome, never the author's STOP.
    Reclassifies ``record`` in place and returns whether it did."""
    counts = [record.get("card_processes_start"), record.get("card_processes_end"), *others]
    shared = any(isinstance(c, dict) and isinstance(c.get("count"), int) and c["count"] > 0 for c in counts)
    if record.get("stop_class") != "arm" or not shared:
        return False
    record["stop_class"] = "infrastructure"
    record["stop"] = f"{record['stop']} [lost beside another compute process on the card: an infrastructure failure, " \
                     "repeated in a new attempt directory (R1-CARD-SHARE (3))]"
    record["lost_beside_another_process"] = True
    return True


def lease_binding(gpu: dict, environ=None, host_class: str | None = None) -> dict | None:
    """A direct-launch class (R1-HOST-FREE): the one GPU the job sees must be the card the host launcher leased
    (``P4_LEASED_GPU_UUID``, which p4_direct.py sets to the leased card's UUID); a missing or other UUID is a STOP.
    An HTCondor class returns None (the slot is the lease)."""
    cls = host_class or job_host_class()
    if HOST_CLASSES[cls]["launch"] != "direct":
        return None
    environ = os.environ if environ is None else environ
    leased = environ.get(LEASED_GPU_ENV)
    if not leased or leased != gpu.get("uuid"):
        raise Stop(f"STOP: {LEASED_GPU_ENV}={leased!r} is not the one GPU the job sees ({gpu.get('uuid')}): a direct job "
                   "runs on its leased card only (p4_direct.py)")
    return {"leased_uuid": leased, "env": LEASED_GPU_ENV}


def host_identity() -> dict:
    import socket
    if os.geteuid() == 0:
        raise Stop("STOP: the job runs as root")
    return {"hostname": socket.gethostname(), "uid": os.getuid(), "euid": os.geteuid(),
            "logical_cpus": os.cpu_count(), "kernel": os.uname().release}


def env3_freeze(spec: dict, clone: Path, sh=_sh) -> dict:
    """Step 3 (R1-TRACKP-V21-FREEZE): ``uv pip freeze`` of env3 against the clone's committed R1-ENV-PIN freeze."""
    pinned = clone / ENV3_FREEZE
    if not pinned.is_file() or _sha_file(pinned) != ENV3_FREEZE_SHA256:
        raise Stop(f"STOP: {ENV3_FREEZE} at the clone is not the R1-ENV-PIN freeze {ENV3_FREEZE_SHA256}")
    native = bool(os.environ.get("P4_VENV_PYTHON"))
    res = sh(["uv" if native else UV, "pip", "freeze", "--python", job_python()], timeout=600)
    if res.returncode != 0:
        raise Stop(f"STOP: uv pip freeze of env3 failed: {res.stderr.strip()[:200]}")
    try:
        record = _phase1(clone).check_env3_freeze(res.stdout, _read_utf8(pinned))
        if native and (record["status"] != "identical" or record["sha256_sorted"] != ENV3_FREEZE_SORTED_SHA256):
            raise Stop("STOP: the Ada venv freeze must equal the pinned package lock")
        freeze_key = "venv_freeze_sha256" if native else "image_freeze_sha256"
        return {**record, "pinned_sha256": ENV3_FREEZE_SHA256,
                freeze_key: hashlib.sha256(res.stdout.encode()).hexdigest()}
    except Exception as exc:         # P4Stop of the clone's module
        if str(exc).startswith("STOP"):
            raise Stop(str(exc)) from None
        raise


def check_venv_gpu(gpu: dict, sh=_sh) -> None:
    """Check actual CUDA visibility after the venv freeze has passed."""
    code = ("import torch\n"
            "if torch.cuda.device_count() != 1: raise SystemExit(2)\n"
            "print(f'GPU-{torch.cuda.get_device_properties(0).uuid}')")
    result = sh([job_python(), "-B", "-c", code], timeout=120)
    if result.returncode != 0 or result.stdout.strip() != gpu["uuid"]:
        raise Stop("STOP: the Ada venv does not see exactly the leased GPU through CUDA")


def clone_full(commit: str, dest: Path, git=_git, sh=_sh) -> dict:
    """Step 2: a full clone (not shallow) at the commit, ``origin/main`` fetched, the commit published, clean."""
    res = sh(["git", "clone", "--quiet", "--no-checkout", PAPER_REPO, str(dest)], timeout=3600)
    if res.returncode != 0:
        raise Stop(f"STOP: git clone failed: {res.stderr.strip()[:300]}")
    if git(dest, "fetch", "--quiet", "origin", "+refs/heads/main:refs/remotes/origin/main").returncode:
        raise Stop("STOP: cannot fetch origin/main into the clone")
    if git(dest, "checkout", "--quiet", "--detach", commit).returncode or \
            git(dest, "rev-parse", "HEAD").stdout.strip() != commit:
        raise Stop(f"STOP: the clone cannot be checked out at {commit}")
    if git(dest, "rev-parse", "--is-shallow-repository").stdout.strip() != "false":
        raise Stop("STOP: the clone is shallow; every partition open needs the full history (P4-JOB A)")
    if git(dest, "merge-base", "--is-ancestor", commit, "origin/main").returncode:
        raise Stop("STOP: the paper commit is not on published main")
    if git(dest, "status", "--porcelain").stdout:
        raise Stop("STOP: the clone is not clean at the pin")
    return {"repo": PAPER_REPO, "commit": commit, "origin_main": git(dest, "rev-parse", "origin/main").stdout.strip()}


def configs(spec: dict, clone: Path, sh=_sh, host_class: str | None = None) -> dict:
    """Step 4: the host config of the job's class (``hosts.<class>.host_config``) and the SFT config at the spec's
    sha256, and ``trackp.py --check-config`` clean on that host config."""
    cls = host_class or job_host_class()
    blocks = {"host_config": host_class_of(spec, cls)["host_config"], "sft_config": spec["sft_config"]}
    out = {}
    for key, block in blocks.items():
        path = clone / block["path"]
        got = _sha_file(path)
        if got != block["sha256"]:
            raise Stop(f"STOP: {block['path']} sha256 {got} is not the spec's {block['sha256']}")
        out[key] = {"path": block["path"], "sha256": got}
    res = sh([job_python(), "-B", str(clone / TRACKP_SCRIPT), "--config", str(clone / blocks["host_config"]["path"]),
              "--check-config"], cwd=clone, timeout=600)
    if res.returncode != 0:
        raise Stop(f"STOP: trackp.py --check-config is not clean on the host config: {res.stdout.strip()[:400]}")
    out["check_config"] = json.loads(res.stdout)
    if out["check_config"].get("placeholders"):
        raise Stop("STOP: the host config still holds TODO_VERIFY_ON_HOST values (P7)")
    return out


def table_inputs(clone: Path, job_dir: Path) -> dict:
    """The transferred table files moved to ``job_dir/table`` and checked against the SFT config's ``sweep1_v3`` pins
    (``build.json`` recorded): the table half of step 5, which the probe also runs."""
    sft = json.loads(_read_utf8(clone / SFT_CONFIG))
    pins = sft["tables"][TABLE_PIN]["sha256"]
    table = job_dir / "table"
    table.mkdir()
    rec = {}
    for name in ("proposals.jsonl", "configs.json", "build.json"):
        src = job_dir / name
        if src.is_symlink() or not src.is_file():
            raise Stop(f"STOP: transferred {name} missing")
        shutil.move(str(src), table / name)
        rec[name] = _sha_file(table / name)
        if name in pins and rec[name] != pins[name]:
            raise Stop(f"STOP: {name} sha256 {rec[name]} is not the {TABLE_PIN} pin {pins[name]}")
    return {"table_dir": str(table), "table_sha256": rec}


def inputs(spec: dict, clone: Path, job_dir: Path) -> dict:
    """Step 5: the transferred table files and the receipted partition (laid out as ``release/sweep1/traindev/``),
    the receipt's table under P4-F2 A and A3's join by proposal id (module docstring)."""
    tab = table_inputs(clone, job_dir)
    table, rec = Path(tab["table_dir"]), tab["table_sha256"]
    part = job_dir / "release" / "sweep1" / "traindev"
    part.mkdir(parents=True)
    for name in ("label_block.traindev.jsonl", "RECEIPT.json"):
        src = job_dir / name
        if src.is_symlink() or not src.is_file():
            raise Stop(f"STOP: transferred {name} missing")
        shutil.move(str(src), part / name)
    P = _phase1(clone)
    try:        # the pins, the source block, then P4-F2 A: the sealed v2 receipt table and A3's FEAT-ONE check
        labels = P.check_partition(part, partition_sha256=spec["labels"]["partition_sha256"],
                                   receipt_sha256=spec["labels"]["receipt_sha256"],
                                   table_proposals_sha256=rec["proposals.jsonl"], identity_root=clone,
                                   source_block_sha256=SOURCE_BLOCK_SHA256)
    except Exception as exc:
        if str(exc).startswith("STOP"):
            raise ProtocolStop(str(exc)) from None
        raise
    freeze = spec["labels"]["freeze_record"]
    fpath = clone / freeze["path"]
    if not fpath.is_file() or _sha_file(fpath) != freeze["sha256"]:
        raise ProtocolStop(f"STOP: the signed label freeze {freeze['path']} is not in the clone at its sha256 (P1)")
    ftext = _read_utf8(fpath, ProtocolStop)
    if not re.search(r"^approved: true$", ftext, re.M) or SOURCE_BLOCK_SHA256 not in ftext:
        raise ProtocolStop(f"STOP: {freeze['path']} is not a signed freeze of the block {SOURCE_BLOCK_SHA256} (P1)")
    try:        # P4-F2 A: after the identity check, A3's join of the labels to sweep1_v3 by proposal id
        join = P.join_labels(job_dir / "release", receipt_sha256=spec["labels"]["receipt_sha256"], table_dir=table)
    except Exception as exc:
        if str(exc).startswith("STOP"):
            raise ProtocolStop(str(exc)) from None
        raise
    return {"table_dir": str(table), "table_sha256": rec, "partition_dir": str(part), "labels": labels,
            "label_freeze": {"path": freeze["path"], "sha256": freeze["sha256"]},
            "receipt_proposals_sha256": labels["table_binding"]["receipt_proposals_sha256"], "label_join": join}


# =============================================================================================== staging
def stage(spec: dict, arm: str, clone: Path, job_dir: Path, sh=_sh) -> dict:
    """Step 6 (the one network step), in the GPU job before any GPU work: the arm's registry weights, checked by size
    and sha256 against the clone's ``registry.yaml``, and the pool tokenizers into ``HF_HOME`` by env3 at their pinned
    revisions, each file recorded with its sha256 (``tokenizer_record``). Any failure is a STOP."""
    import yaml
    registry = yaml.safe_load((clone / "r1/c3/train/registry.yaml").read_bytes())["models"]
    staged = {}
    for key in (k for k in ARMS[arm] if k):
        item = registry[key]
        target = job_dir / "models" / key
        target.mkdir(parents=True)
        for name, pin in sorted(item["files"].items()):
            if Path(name).name != name or name in (".", ".."):
                raise Stop(f"STOP: unexpected registry file name {name}")
            url = f"https://huggingface.co/{item['repo']}/resolve/{item['revision']}/{name}"
            res = sh(["curl", "--fail", "--silent", "--show-error", "--location", "--retry", "2", "--max-time", "3600",
                      "-o", str(target / name), url], timeout=3700)
            dest = target / name
            if res.returncode != 0 or not dest.is_file():
                raise Stop(f"STOP: staging {key}/{name} failed: {res.stderr.strip()[:200]}")
            if dest.stat().st_size != pin["size"] or _sha_file(dest) != pin["sha256"]:
                raise Stop(f"STOP: registry size or sha256 mismatch for {key}/{name}")
            staged[f"{key}/{name}"] = pin["sha256"]
    env = dict(os.environ, HF_HOME=str(job_dir / "hf"), HF_HUB_OFFLINE="0", TRANSFORMERS_OFFLINE="0")
    res = sh([job_python(), "-B", "-c", TOKENIZER_STAGE], cwd=clone, env=env, timeout=3600)
    if res.returncode != 0:
        raise Stop(f"STOP: staging the pool tokenizers failed: {res.stderr.strip()[-300:]}")
    return {"weights": staged, "tokenizers": tokenizer_record(job_dir, res.stdout)}


# The pool tokenizers are staged here, in the GPU job (the probe and the P.4 job), by env3 in the v2.2 GPU image, before
# any GPU work (26 Nov 2026): the desk-side T4 could not run this step on CPU (deepthought: transformers' lazy import asks
# torch for an accelerator; the v2.2 CPU image, job 760071: no env3, rc 127). The script loads every POOL tokenizer at
# its pinned revision (serialize.load_tokenizer, as before) and prints the hub cache and the pool it used.
TOKENIZER_STAGE = ("import json\n"
                   "from huggingface_hub import constants as C\n"
                   "from r1.c3.train import serialize as S\n"
                   "for n in S.POOL: S.load_tokenizer(n)\n"
                   "print(json.dumps({'hub_cache': C.HF_HUB_CACHE, 'pool': {n: list(S.POOL[n]) for n in S.POOL}}))")


def tokenizer_record(job_dir: Path, stdout: str) -> dict:
    """The staged pool tokenizers for the job record: per POOL entry its repo, pinned revision and subfolder, and every
    file of its hub snapshot at that revision with size and sha256. Fail closed (each a STOP, before any GPU work): no
    pool record printed, a hub cache outside the job's ``HF_HOME`` (R1-TRACKP-P4-RUNNER-DECISIONS (2)), a revision that
    is not a 40-hex commit, no snapshot at the pinned revision, a snapshot file resolving outside the cache, or no
    ``tokenizer*`` file in the snapshot (in its subfolder, when the pool names one), or a broken link in it."""
    try:
        out = json.loads(stdout.strip().splitlines()[-1])
        pool, cache = out["pool"], Path(out["hub_cache"])
        if not isinstance(pool, dict) or not pool:
            raise ValueError
    except (IndexError, KeyError, TypeError, ValueError):
        raise Stop("STOP: the tokenizer staging step printed no pool record (hub_cache, pool)") from None
    hf = (Path(job_dir) / "hf").resolve()
    root = cache.resolve()
    if hf != root and hf not in root.parents:
        raise Stop(f"STOP: the tokenizers were staged into {cache}, not the job's HF_HOME {hf} "
                   "(R1-TRACKP-P4-RUNNER-DECISIONS (2))")
    rec = {}
    for name, entry in sorted(pool.items()):
        if not (isinstance(entry, list) and len(entry) == 3 and isinstance(entry[0], str) and "/" in entry[0]
                and isinstance(entry[1], str) and re.fullmatch(r"[0-9a-f]{40}", entry[1])
                and (entry[2] is None or isinstance(entry[2], str))):
            raise Stop(f"STOP: pool tokenizer {name}: {entry!r} is not (repo, pinned 40-hex revision, subfolder)")
        repo, rev, sub = entry
        snap = root / f"models--{repo.replace('/', '--')}" / "snapshots" / rev
        if not snap.is_dir():
            raise Stop(f"STOP: pool tokenizer {name}: no hub snapshot at its pinned revision {rev}")
        files = {}
        for f in sorted(snap.rglob("*")):
            if f.is_dir():
                continue
            try:                                         # review round 1, m3: a broken symlink is a STOP, not skipped
                real = f.resolve(strict=True)
            except (OSError, RuntimeError):
                raise Stop(f"STOP: pool tokenizer {name}: {f} is a broken link") from None
            if root not in real.parents or not real.is_file():
                raise Stop(f"STOP: pool tokenizer {name}: {f} resolves outside the hub cache or not to a file")
            files[f.relative_to(snap).as_posix()] = {"size": real.stat().st_size, "sha256": _sha_file(real)}
        prefix = f"{sub}/" if sub else ""
        if not any(k.startswith(prefix) and "/" not in k[len(prefix):] and k[len(prefix):].startswith("tokenizer")
                   for k in files):
            raise Stop(f"STOP: pool tokenizer {name}: no tokenizer file in its snapshot at {rev}")
        rec[name] = {"repo": repo, "revision": rev, "subfolder": sub, "files": files}
    return {"count": len(rec), "hub_cache": str(cache), "pool": rec}


def check_local_paths(arm: str, clone: Path, job_dir: Path, host_config: str | None = None) -> dict:
    """The host config (of the job's class, unless ``host_config`` names one) must point the arm at the staged
    directories (paths relative to the job directory)."""
    cfg = json.loads(_read_utf8(clone / (host_config or job_host_config())))
    base = cfg["bases"][arm]
    adapter_key, base_key = ARMS[arm]
    want = {"local_path": job_dir / "models" / base_key}
    if adapter_key:
        want["adapter_local_path"] = job_dir / "models" / adapter_key
    for key, path in want.items():
        given = Path(os.path.expanduser(str(base.get(key, ""))))
        got = (job_dir / given) if not given.is_absolute() else given
        if got.resolve() != path.resolve():
            raise Stop(f"STOP: host config bases.{arm}.{key} = {base.get(key)!r} is not the staged {path}")
    return {k: str(v) for k, v in want.items()}


# =============================================================================================== the SFT steps
def offline_env(job_dir: Path) -> dict:
    env = dict(os.environ, HF_HOME=str(job_dir / "hf"), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               PYTHONDONTWRITEBYTECODE="1", PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    return env


def trackp(clone: Path, job_dir: Path, args: list, sh=_sh, timeout: int = 86400) -> dict:
    """One ``trackp.py`` call (the clone's script, by absolute path; the job directory is the working directory)
    with the host config, offline. A refusal of the SFT pipeline (``trackp.py`` prints ``STOP: …`` and exits 2) is a
    protocol STOP, a CUDA OOM an arm STOP, anything else (a missing script, an argument error, a crash) an
    infrastructure STOP. The log is kept under ``out/logs/``."""
    argv = [job_python(), "-B", str(clone / TRACKP_SCRIPT), "--config", str(clone / job_host_config()),
            *map(str, args)]
    res = sh(argv, cwd=job_dir, env={**offline_env(job_dir), "PYTHONPATH": str(clone)}, timeout=timeout)
    logs = job_dir / "out" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{len(list(logs.iterdir())):03d}_{args[0]}.log"
    log.write_text(" ".join(map(str, argv)) + "\n" + (res.stdout or "") + "\n--- stderr ---\n" + (res.stderr or ""),
                   encoding="utf-8")
    if res.returncode == 0:
        return {"argv": [str(a) for a in args], "log": log.name}
    text = (res.stderr or "") + (res.stdout or "")
    if "CUDA out of memory" in text or "OutOfMemoryError" in text:
        raise ArmStop(f"STOP: CUDA OOM in {args[0]} at micro-batch {MICRO_BATCH} (P4-MB; the author decides); see {log.name}")
    if res.returncode == 2 and re.search(r"^STOP: ", res.stderr or "", re.M):
        raise ProtocolStop(f"STOP: trackp.py {args[0]} refused: {text.strip()[-300:]}")
    raise Stop(f"STOP: trackp.py {args[0]} failed rc={res.returncode}; see {log.name}")


def data_argv(clone: Path, job_dir: Path, ins: dict, *, synthetic: bool = False) -> list:
    run = job_dir / "out" / ("sft_data_synthetic" if synthetic else "sft_data")
    argv = ["sft-data", "--table", ins["table_dir"], "--table-pin", TABLE_PIN,
            "--sweep", str(clone / SWEEP_INDEX), "--paper-root", str(clone),
            "--classification", str(clone / CLASSIFICATION),
            "--labels", "synthetic" if synthetic else str(Path(ins["partition_dir"]) / "label_block.traindev.jsonl"),
            "--label-sweep", "sweep1", "--run-dir", str(run)]
    if not synthetic:
        argv += ["--label-freeze", str(clone / ins["label_freeze"]["path"])]
    return argv


def data_build(clone: Path, job_dir: Path, ins: dict, sh=_sh, *, synthetic: bool = False) -> Path:
    """Step 7 (and the synthetic build of step 10)."""
    argv = data_argv(clone, job_dir, ins, synthetic=synthetic)
    trackp(clone, job_dir, argv, sh)
    return Path(argv[argv.index("--run-dir") + 1]) / "data"


def path_free(obj):
    """``obj`` with every ``path`` key removed (recursively): the job directory differs per job."""
    if isinstance(obj, dict):
        return {k: path_free(v) for k, v in obj.items() if k != "path"}
    if isinstance(obj, list):
        return [path_free(v) for v in obj]
    return obj


def data_identity(data: Path) -> dict:
    """The path-free identity of an ``sft-data`` directory: its ``sft_data.json`` without paths (rows, splits, table,
    sweep-index, classification and label sha256s, counts and versions all stay), hashed canonically."""
    manifest = json.loads(_read_utf8(Path(data) / "sft_data.json"))
    free = path_free(manifest)
    return {"sha256": hashlib.sha256(json.dumps(free, sort_keys=True).encode()).hexdigest(),
            "rows_sha256": manifest.get("rows_sha256"), "splits_sha256": manifest.get("splits_sha256")}


def check_run_protocol(run_dir: Path, sft_cfg: dict, *, lr: float, seed: int, data_sha256: str | None = None,
                       checkpointing: bool = False) -> dict:
    """The protocol a run actually used (its ``stage_s/sft_report.json``) is the fixed one: micro-batch 8 (P4-MB A)
    and every other Stage S key of the SFT config's ``train`` block (effective batch 16, loss, epochs, patience, the
    lr grid, ...), with the run's lr and seed; a difference is a protocol STOP."""
    rep = json.loads(_read_utf8(Path(run_dir) / "stage_s" / "sft_report.json"))
    proto = rep.get("protocol") or {}
    keys = ("loss", "effective_batch", "max_epochs", "warmup_frac", "eval_every_frac", "patience", "lr_grid",
            "head_lr", "token_lr", "temperature_scaling")
    want = {k: sft_cfg["train"][k] for k in keys} | {"micro_batch": MICRO_BATCH}
    bad = {k: (proto.get(k), v) for k, v in want.items() if proto.get(k) != v}
    if bad or float(rep.get("lr")) != float(lr) or int(rep.get("seed")) != int(seed):
        raise ProtocolStop(f"STOP: {Path(run_dir).name} ran another protocol than the fixed one: {bad or 'lr/seed'}")
    if rep.get("protocol_deviation") is not None:
        raise ProtocolStop(f"STOP: {Path(run_dir).name} records a protocol deviation: {rep['protocol_deviation']}")
    if data_sha256 is not None and rep.get("data_sha256") != data_sha256:
        raise ProtocolStop(f"STOP: {Path(run_dir).name} was trained on another data directory")
    check_checkpointing(proto, checkpointing)
    return {k: proto.get(k) for k in want}


def check_checkpointing(protocol: dict, enabled: bool) -> None:
    if protocol.get("gradient_checkpointing", False) is not enabled:
        raise ProtocolStop(f"STOP: the Stage S run must have gradient_checkpointing={enabled} (R1-P4-4B-CHECKPOINT)")


def sft_dev_argv(arm: str, data: Path, lr: float, seed: int, run_dir: Path, extra=(), *, checkpointing=False) -> list:
    return ["sft-dev", "--data", str(data), "--base", arm, "--lr", repr(float(lr)), "--seed", str(seed),
            "--run-dir", str(run_dir), *extra, *(("--p4-gradient-checkpointing",) if checkpointing else ())]


def select_argv(runs, run_dir: Path) -> list:
    return ["sft-select", "--runs", *map(str, runs), "--run-dir", str(run_dir)]


def sft_dev(clone: Path, job_dir: Path, arm: str, data: Path, lr: float, seed: int, run_dir: Path, sh=_sh,
            extra=(), *, checkpointing=False) -> Path:
    trackp(clone, job_dir, sft_dev_argv(arm, data, lr, seed, run_dir, extra, checkpointing=checkpointing), sh)
    return run_dir


def run_name(lr: float, seed: int, n: int | str = "full") -> str:
    return f"lr{float(lr):g}_s{seed}" + ("" if n == "full" else f"_n{n}")


# =============================================================================================== the job
def run_job(spec_path: Path, arm: str, job_dir: Path | None = None, *, host_class: str, started: float | None = None,
            sh=_sh, git=_git) -> dict:
    """The job of one arm (module docstring) on the host class it was told (``host_class``, which the spec must
    admit; the job's GPU must be that class's, R1-HOST-FREE). Writes ``out/``, ``out.tar``, ``job_record.json`` and
    ``SHA256SUMS`` in ``job_dir`` (the job's scratch, the current directory by default) and raises Stop on a STOP."""
    with _job_host(host_class):
        return _run_job(spec_path, arm, job_dir, host_class=host_class, started=started, sh=sh, git=git)


def _run_job(spec_path: Path, arm: str, job_dir: Path | None, *, host_class: str, started: float | None, sh,
             git) -> dict:
    started = started or time.time()
    job_dir = Path(job_dir or Path.cwd()).resolve()
    spec = load_spec(spec_path)
    loaded = validate_spec(spec, launch=True)
    if arm not in spec["arms"]:
        raise Stop(f"STOP: {arm} is not an arm of the spec")
    host = host_class_of(spec, host_class)
    checkpointing = spec["protocol"]["gradient_checkpointing"].get(arm, False)
    record: dict = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "arm": arm,
                    "phase": 1, "spec_sha256": _sha_file(spec_path), "paper_commit": spec["paper"]["commit"],
                    "gradient_checkpointing": checkpointing,
                    "host_class": host_class, "launch": host["launch"],
                    "started_utc": _utc(started), "stop": None, "stop_class": None, "steps": [],
                    "projection": loaded["projection"]["per_arm"][arm],
                    "output_use": "ENGINEERING_ONLY P.4 phase 1 (R1-TRACKP-P4-DECISIONS): readiness only; no "
                                  "real-label test read; no evaluation seed read"}
    out = job_dir / "out"
    out.mkdir(exist_ok=True)
    clone = job_dir / "paper"
    try:
        native = bool(os.environ.get("P4_VENV_PYTHON"))
        record["image"] = None if native else image_identity(spec)
        record["gpu"] = gpu_identity(sh)
        record["lease"] = lease_binding(record["gpu"])
        record["card_processes_start"] = card_processes(sh, record["gpu"].get("uuid"))   # R1-CARD-SHARE (4)
        record["host"] = host_identity()
        record["steps"].append("identity")
        record["clone"] = clone_full(spec["paper"]["commit"], clone, git, sh)
        record["steps"].append("clone")
        if native:
            record["venv"] = verify_ada_venv(spec, clone)
        record["env3_freeze"] = env3_freeze(spec, clone, sh)
        if native:
            check_venv_gpu(record["gpu"], sh)
        record["steps"].append("env3_freeze")
        record["configs"] = configs(spec, clone, sh)
        record["steps"].append("configs")
        ins = inputs(spec, clone, job_dir)
        record["inputs"] = ins
        record["steps"].append("inputs")
        record["staging"] = stage(spec, arm, clone, job_dir, sh)
        record["local_paths"] = check_local_paths(arm, clone, job_dir)
        record["steps"].append("staging")
        P = _phase1(clone)
        data = data_build(clone, job_dir, ins, sh)
        record["data"] = {"dir": str(data.relative_to(job_dir)), "sft_data_sha256": _sha_file(data / "sft_data.json"),
                          "identity": data_identity(data)}
        record["steps"].append("data")
        sft_cfg = json.loads(_read_utf8(clone / SFT_CONFIG))
        runs = out / "runs"
        grid = []
        for lr in LR_GRID:
            for s in SEEDS:
                grid.append(sft_dev(clone, job_dir, arm, data, lr, s, runs / run_name(lr, s), sh,
                                    checkpointing=checkpointing))
                check_run_protocol(grid[-1], sft_cfg, lr=lr, seed=s, data_sha256=record["data"]["sft_data_sha256"],
                                   checkpointing=checkpointing)
        record["protocol"] = check_run_protocol(grid[0], sft_cfg, lr=LR_GRID[0], seed=SEEDS[0],
                                                checkpointing=checkpointing)
        record["steps"].append("grid")
        trackp(clone, job_dir, select_argv(grid, out / "select"), sh)
        select = json.loads(_read_utf8(out / "select" / "report.json"))
        lr_sel = float(select["selected_lr"])
        record["select"] = {"selected_lr": lr_sel, "mean_best_val_rps": select.get("mean_best_val_rps")}
        record["steps"].append("select")
        n_train = int(json.loads(_read_utf8(data / "sft_data.json"))["counts"]["train"])
        lc_runs = {}
        for point in P.lc_points(n_train, spec["protocol"]["lc_points"]):
            if point == "full":
                lc_runs["full"] = [runs / run_name(lr_sel, s) for s in SEEDS]
                continue
            sub = out / "lc_data" / f"n{point}"
            P.lc_subset(data, point, sub)
            lc_runs[str(point)] = [sft_dev(clone, job_dir, arm, sub, lr_sel, s, runs / run_name(lr_sel, s, point), sh,
                                          checkpointing=checkpointing)
                                   for s in SEEDS]
            for s, d in zip(SEEDS, lc_runs[str(point)]):
                check_run_protocol(d, sft_cfg, lr=lr_sel, seed=s, data_sha256=_sha_file(sub / "sft_data.json"),
                                   checkpointing=checkpointing)
        record["learning_curve"] = {k: [p.name for p in v] for k, v in lc_runs.items()}
        record["steps"].append("learning_curve")
        boot = P.rps_skill_bootstrap(data, [runs / run_name(lr_sel, s) / "stage_s" for s in SEEDS])
        (out / "bootstrap.json").write_text(json.dumps(boot, indent=1, sort_keys=True) + "\n")
        record["bootstrap"] = {"raw": boot["raw"], "temperature_scaled": boot["temperature_scaled"]}
        record["steps"].append("bootstrap")
        cfg = json.loads(_read_utf8(clone / job_host_config()))
        base = {k: cfg["bases"][arm].get(k) for k in ("family", "base_repo", "base_revision", "adapter_repo",
                                                       "adapter_revision")}
        pin = P.arm_pin(arm=arm, base_record=base, staged=record["staging"]["weights"], data_dir=data,
                        select_report=select, grid_runs=grid, lc_runs=lc_runs,
                        micro_batch=record["protocol"]["micro_batch"],
                        host_config_sha256=record["configs"]["host_config"]["sha256"])
        (out / "arm_pin.json").write_text(json.dumps(pin, indent=1, sort_keys=True) + "\n")
        record["arm_pin_sha256"] = _sha_file(out / "arm_pin.json")
        record["steps"].append("arm_pin")
        record["test_path"] = test_path(clone, job_dir, arm, ins, sh, checkpointing=checkpointing)
        record["steps"].append("test_path")
    except Stop as exc:
        record["stop"], record["stop_class"] = str(exc), exc.stop_class
    except Exception as exc:  # noqa: BLE001 - every failure writes the record and the sums
        record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
    if (record.get("gpu") or {}).get("uuid"):            # R1-CARD-SHARE (4), then (3)
        record["card_processes_end"] = card_processes(sh, record["gpu"]["uuid"])
    shared_card_loss(record)
    finished = time.time()
    record["finished_utc"] = _utc(finished)
    record["gpu_hours"] = round((finished - started) / 3600, 4)
    (job_dir / "job_record.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=job_dir, check=False)
    _write_sums(job_dir, ("out.tar", "job_record.json"))
    if record["stop"]:
        raise Stop(record["stop"])
    return record


def test_path(clone: Path, job_dir: Path, arm: str, ins: dict, sh=_sh, *, checkpointing=False) -> dict:
    """Step 10 (P4-PHASE1-TEST A): the evaluator's path on synthetic labels; the real-label test is never read."""
    syn = data_build(clone, job_dir, ins, sh, synthetic=True)
    run = sft_dev(clone, job_dir, arm, syn, LR_GRID[0], 0, job_dir / "out" / "test_path" / "run", sh,
                  extra=("--steps", "2", "--eval-every", "1"), checkpointing=checkpointing)
    ledger = job_dir / "out" / "ledgers" / TABLE_PIN
    env = {**offline_env(job_dir), "PYTHONPATH": str(clone)}
    code = ("import json, sys\nfrom pathlib import Path\n"
            "from r1.scripts import trackp_p4_test_path as T\n"
            "print(json.dumps(T.main(sys.argv[1:])))\n")
    res = sh([job_python(), "-B", "-c", code, "--data", str(syn), "--table", ins["table_dir"], "--run", str(run),
              "--arm", arm, "--sweep", str(clone / SWEEP_INDEX), "--paper-root", str(clone),
              "--classification", str(clone / CLASSIFICATION), "--host-config", str(clone / job_host_config()),
              "--ledger-dir", str(ledger), "--out", str(job_dir / "out" / "test_path" / "report")],
             cwd=job_dir, env=env, timeout=7200)
    (job_dir / "out" / "logs" / "test_path.log").write_text((res.stdout or "") + "\n--- stderr ---\n" + (res.stderr or ""),
                                                           encoding="utf-8")
    if res.returncode != 0:
        raise Stop(f"STOP: the synthetic test path failed rc={res.returncode}: {(res.stderr or '').strip()[-300:]}")
    rep = json.loads(res.stdout.strip().splitlines()[-1])
    if rep.get("labels") != "synthetic":
        raise ProtocolStop("STOP: the test path read non-synthetic labels (P4-PHASE1-TEST A)")
    return rep


# =============================================================================================== probe mode
def _at(obj: dict, path: tuple):
    for key in path:
        obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def validate_probe_spec(spec: dict) -> dict:
    """Probe strength (cluster test plan §4.2 item 12). Neither existing strength fits: launch strength needs the probe
    record and the label fields, and default strength admits placeholders that ``image_identity`` would refuse only
    inside the job. So: the default ``validate_spec``, then the probe run id (``trackp-p4-probe-<YYYYMMDD>-<letter>``,
    never the P.4 run's: F10), the fixed ``probe`` block (``PROBE``), and these filled with the patterns of
    ``_pin(..., allow=False)``: ``paper.commit`` (the host-config fill commit), ``image.digest`` (the v2.2 digest),
    ``image.versions_sha256`` (T1), ``host_class`` (R1-HOST-FREE: the one admitted class the probe run measures; its
    estimate is per class) and that class's ``hosts.<class>.host_config.sha256`` (T3; the other classes' may stay
    placeholders). The arms and ``first_arm`` are those of the default
    check (both controls, ``kev-0.8b`` first). The Ada re-probe uses a new run id and reuses that first-arm seal, with
    execution limited to the two 4B arms. The label fields, ``estimate.*`` and ``caps.probe_gpu_hours`` may stay
    placeholders: the probe reads none of them. It does not require ``h200_sft_probe`` (F1)."""
    loaded = validate_spec(spec)
    run_id = loaded["run_id"]
    if run_id == P4_RUN_ID or not PROBE_RUN_ID.fullmatch(run_id):
        raise Stop(f"STOP: a probe spec's run_id must be trackp-p4-probe-<YYYYMMDD>-<letter>, never the P.4 run "
                   f"{P4_RUN_ID} (F10)")
    probe = spec.get("probe")
    if not isinstance(probe, dict) or {k: probe.get(k) for k in PROBE} != PROBE or \
            set(probe) - set(PROBE) - {"rule", "comment"}:
        raise Stop(f"STOP: probe must be {PROBE} (P4-PROBE A: at most 50 steps of sft-dev, synthetic labels)")
    _pin(spec["paper"].get("commit"), "paper.commit", COMMIT, allow=False)
    if spec["image"].get("digest") != IMAGE_V22:
        raise Stop("STOP: the probe runs in image v2.2 by digest (R1-TRACKP-IMAGE-V22-B)")
    _pin(spec["image"].get("versions_sha256"), "image.versions_sha256", allow=False)
    cls = spec.get("host_class")
    if not isinstance(cls, str) or cls not in spec["hosts"]:
        raise Stop(f"STOP: a probe spec names the one host class its run uses (host_class, one of the admitted "
                   f"{sorted(spec['hosts'])}): a probe run measures one class (R1-HOST-FREE; P4-PROBE A)")
    _pin(spec["hosts"][cls]["host_config"].get("sha256"), f"hosts.{cls}.host_config.sha256", allow=False)
    reprobe = run_id == ADA_REPROBE["run_id"]
    if "ada_4b_reprobe" in spec and spec["ada_4b_reprobe"] != ADA_REPROBE:
        raise Stop("STOP: the Ada 4B re-probe binding differs from R1-P4-4B-CHECKPOINT")
    if cls == "ada_rtx6000" and run_id == ADA_REPROBE["prior_run_id"] and "ada_4b_reprobe" in spec:
        raise Stop("STOP: the prior Ada run is sealed; use the new Ada 4B re-probe run id")
    if reprobe and (cls != "ada_rtx6000" or spec.get("ada_4b_reprobe") != ADA_REPROBE
                    or spec["protocol"].get("gradient_checkpointing") != CHECKPOINT_ARMS
                    or not CHECKPOINT_ARMS.keys() <= set(spec["arms"])):
        raise Stop("STOP: the Ada 4B re-probe requires the published binding and both checkpointed 4B arms on Ada")
    return {"spec": spec, "run_id": run_id, "probe": dict(probe), "host_class": cls,
            "probe_arms": tuple(CHECKPOINT_ARMS) if reprobe else tuple(spec["arms"])}


def check_probe_template(spec: dict, template: dict) -> None:
    """Check the filled fields and the exact alternate run id bound by the committed probe template."""
    a, b = json.loads(json.dumps(spec)), json.loads(json.dumps(template))
    if a["run_id"] == ADA_REPROBE["run_id"] and b.get("ada_4b_reprobe") == ADA_REPROBE:
        a["run_id"] = b["run_id"]
    for path in PROBE_FILLED:
        if not _placeholder(_at(template, path)):
            raise Stop(f"STOP: the committed probe template must hold a placeholder at {'.'.join(path)}")
        for d in (a, b):
            parent = _at(d, path[:-1])
            if isinstance(parent, dict):
                parent[path[-1]] = None
    if a != b:
        raise Stop("STOP: the probe spec differs from the committed template p4_probe_spec.json outside "
                   + ", ".join(".".join(p) for p in PROBE_FILLED))


def visible_devices(gpu: dict, environ=None) -> dict:
    """F3 inside the probe: the HTCondor GPU assignment as the job sees it. A ``CUDA_VISIBLE_DEVICES`` or
    ``NVIDIA_VISIBLE_DEVICES`` that names GPU UUIDs must name exactly the one GPU ``gpu_identity`` lists; other forms
    (indices, unset) are recorded only."""
    environ = os.environ if environ is None else environ
    env = {k: environ.get(k) for k in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "_CONDOR_AssignedGPUs")}
    for key in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES"):
        value = env[key]
        if value and value.startswith("GPU-") and value != gpu["uuid"]:
            raise Stop(f"STOP: {key}={value} is not the one GPU nvidia-smi lists ({gpu['uuid']}) (F3)")
    return env


def condor_ad(environ=None) -> dict | None:
    """ClusterId, ProcId and GlobalJobId from the job ad HTCondor names in ``_CONDOR_JOB_AD`` (None outside a job)."""
    environ = os.environ if environ is None else environ
    path = environ.get("_CONDOR_JOB_AD")
    if not path or not Path(path).is_file():
        return None
    out = {}
    for line in Path(path).read_bytes().decode("utf-8", "replace").splitlines():
        key, _, value = line.partition("=")
        if key.strip() in ("ClusterId", "ProcId", "GlobalJobId"):
            out[key.strip()] = value.strip().strip('"')
    return out


def start_sampler(uuid: str, csv_path: Path, sample_ms: int, popen=subprocess.Popen):
    """F4: the assigned GPU's device memory sampled from outside every ``sample_ms`` ms, scoped to its UUID (as the
    reviewed smoke and E0 stages scoped their queries). Returns a function that stops the sampler."""
    fh = open(csv_path, "w", encoding="utf-8")
    try:
        proc = popen(["nvidia-smi", f"--id={uuid}", "--query-gpu=timestamp,memory.used,memory.total",
                      "--format=csv,noheader,nounits", "-lms", str(int(sample_ms))], stdout=fh,
                     stderr=subprocess.STDOUT)
    except OSError as exc:
        fh.close()
        raise Stop(f"STOP: the nvidia-smi memory sampler did not start: {exc}") from None

    def stop() -> None:
        try:
            proc.terminate()
            proc.wait(timeout=30)
        except Exception:  # noqa: BLE001 - a sampler that will not stop is killed; the samples so far are kept
            proc.kill()
        finally:
            fh.close()
    return stop


def memory_summary(csv_path: Path) -> dict:
    """Peak and total device memory (MiB) of the sampler's lines ``<timestamp>, <used>, <total>``."""
    used, total, bad = [], None, 0
    text = Path(csv_path).read_bytes().decode("utf-8", "replace") if Path(csv_path).is_file() else ""
    for line in text.splitlines():
        parts = [x.strip() for x in line.split(",")]
        try:
            u, t = float(parts[1]), float(parts[2])
        except (IndexError, ValueError):
            bad += line.strip() != ""
            continue
        used.append(u)
        total = t
    if not used:
        return {"samples": 0, "peak_memory_used_mib": None, "memory_total_mib": total, "headroom_frac": None,
                "unparsed_lines": bad}
    peak = max(used)
    return {"samples": len(used), "peak_memory_used_mib": peak, "memory_total_mib": total,
            "headroom_frac": round(1 - peak / total, 4) if total else None, "unparsed_lines": bad}


def step_summary(metrics: Path, first: int = PROBE_MIN_STEP) -> dict:
    """``step_s`` over the optimizer steps ``first`` ... ``stopped_at`` of ``metrics.jsonl`` (median, p90 by nearest
    rank, max)."""
    rows = [json.loads(x) for x in _read_utf8(metrics).splitlines() if x.strip()] if Path(metrics).is_file() else []
    s = sorted(float(r["step_s"]) for r in rows if r.get("kind") == "step" and int(r.get("step", 0)) >= first)
    if not s:
        return {"n": 0, "first_step": first, "step_s_median": None, "step_s_p90": None, "step_s_max": None}
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    return {"n": len(s), "first_step": first, "step_s_median": median,
            "step_s_p90": s[max(0, math.ceil(0.9 * len(s)) - 1)], "step_s_max": s[-1]}


def _tree_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in Path(root).rglob("*") if p.is_file()) if Path(root).is_dir() else 0


def probe_code_binding(spec: dict, clone: Path, lib_file: Path | None = None) -> dict:
    """The probe ran the reviewed code of the commit it cloned: the transferred ``p4_lib.py`` equals the clone's, and
    the transferred probe spec differs from the clone's committed template only in the filled fields."""
    lib_file = Path(lib_file or __file__)
    clone_lib = clone / PKG_REL / "p4_lib.py"
    if not clone_lib.is_file() or _sha_file(clone_lib) != _sha_file(lib_file):
        raise Stop(f"STOP: the transferred p4_lib.py is not the one at the paper commit ({PKG_REL}/p4_lib.py)")
    wrapper = lib_file.parent / "p4_probe.sh"           # the transferred entry point, when it is beside p4_lib.py
    if wrapper.is_file() and (not (clone / PKG_REL / "p4_probe.sh").is_file() or
                              _sha_file(clone / PKG_REL / "p4_probe.sh") != _sha_file(wrapper)):
        raise Stop(f"STOP: the transferred p4_probe.sh is not the one at the paper commit ({PKG_REL}/p4_probe.sh)")
    template = clone / PKG_REL / PROBE_SPEC_FILE
    if not template.is_file():
        raise Stop(f"STOP: the paper commit has no {PKG_REL}/{PROBE_SPEC_FILE} (the probe mode is not on it)")
    check_probe_template(spec, load_spec(template))
    return {"p4_lib_sha256": _sha_file(lib_file), "template_sha256": _sha_file(template)}


def probe_run_summary(run_dir: Path, data: dict, sft_cfg: dict, probe: dict, wall: dict, *, checkpointing=False) -> dict:
    """The probe run's protocol and timings from its ``stage_s`` (cluster test plan §4.4); S10's refusals: another
    micro-batch or effective batch, a protocol deviation other than ``{"max_steps": 50}``, another data directory."""
    stage_s = Path(run_dir) / "stage_s"
    rep = json.loads(_read_utf8(stage_s / "sft_report.json"))
    proto = rep.get("protocol") or {}
    check_checkpointing(proto, checkpointing)
    if proto.get("micro_batch") != MICRO_BATCH or proto.get("effective_batch") != 16:
        raise ProtocolStop(f"STOP: the probe ran micro-batch {proto.get('micro_batch')} / effective batch "
                           f"{proto.get('effective_batch')}, not 8 / 16 (P4-MB A)")
    if rep.get("protocol_deviation") != {"max_steps": probe["steps"]}:
        raise ProtocolStop(f"STOP: the probe's protocol deviation is {rep.get('protocol_deviation')}, not "
                           f"{{'max_steps': {probe['steps']}}}")
    if rep.get("data_sha256") != data["sft_data_sha256"]:
        raise ProtocolStop("STOP: the probe trained on another data directory than its synthetic build")
    if float(rep.get("lr", -1)) != float(probe["lr"]) or rep.get("seed") != probe["seed"]:
        raise ProtocolStop(f"STOP: the probe ran lr {rep.get('lr')} seed {rep.get('seed')}, not {probe['lr']} / "
                           f"{probe['seed']}")
    train = rep.get("train") or {}
    missing = [k for k in ("stopped_at", "completed", "early_stopped") if k not in train]
    if missing or train.get("completed") is not True:
        raise ProtocolStop(f"STOP: the probe's training record is incomplete ({missing or 'completed is not true'})")
    stopped = int(train.get("stopped_at") or 0)
    if not 0 < stopped <= probe["steps"]:
        raise ProtocolStop(f"STOP: the probe stopped at step {stopped}, outside 1 ... {probe['steps']}")
    return {"lr": rep.get("lr"), "seed": rep.get("seed"), "n_train": rep.get("n_train"), "n_val": rep.get("n_val"),
            "protocol": {k: proto.get(k) for k in ("micro_batch", "effective_batch", "max_epochs", "patience",
                                                   "eval_every_frac", "loss")},
            "max_tokens": int(sft_cfg["prompt"]["max_tokens"]), "gradient_checkpointing": checkpointing,
            "protocol_deviation": rep.get("protocol_deviation"), "steps_per_epoch": rep.get("steps_per_epoch"),
            "total_steps": rep.get("total_steps"), "stopped_at": stopped,
            "early_stopped": train.get("early_stopped"),
            "s_per_step_wall": round(wall["wall_s"] / stopped, 4),
            "step_s": step_summary(stage_s / "metrics.jsonl")}


def run_probe(spec_path: Path, arm: str, job_dir: Path | None = None, *, host_class: str | None = None,
              started: float | None = None, sh=_sh, git=_git, popen=subprocess.Popen, environ=None,
              lib_file: Path | None = None) -> dict:
    """The SFT fit and timing probe of one base on the probe spec's host class (module docstring; cluster test plan
    §4.2 items 1-10; R1-HOST-FREE: the class the job was told, ``host_class``, must be the probe spec's). Writes
    ``out/``, ``out.tar`` (the allow-list ``PROBE_KEEP`` only), ``job_record.json`` (``trackp_p4_probe_record/1``) and
    ``SHA256SUMS`` in ``job_dir`` and raises Stop on a STOP."""
    spec = load_spec(spec_path)
    loaded = validate_probe_spec(spec)
    if host_class is not None and host_class != loaded["host_class"]:
        raise Stop(f"STOP: the job was told host class {host_class}, the probe spec measures {loaded['host_class']}")
    with _job_host(loaded["host_class"]):
        return _run_probe(spec_path, spec, loaded, arm, job_dir, started=started, sh=sh, git=git, popen=popen,
                          environ=environ, lib_file=lib_file)


def _run_probe(spec_path: Path, spec: dict, loaded: dict, arm: str, job_dir: Path | None, *, started, sh, git, popen,
               environ, lib_file) -> dict:
    started = started or time.time()
    job_dir = Path(job_dir or Path.cwd()).resolve()
    if arm not in loaded["probe_arms"]:
        raise Stop(f"STOP: {arm} is not an arm of the probe spec")
    probe = loaded["probe"]
    cls = loaded["host_class"]
    checkpointing = spec["protocol"].get("gradient_checkpointing", {}).get(arm, False)
    record: dict = {"schema": PROBE_RECORD_SCHEMA, "label": ENGINEERING_ONLY, "mode": "probe", "run_id": spec["run_id"],
                    "arm": arm, "phase": 1, "spec_sha256": _sha_file(spec_path), "paper_commit": spec["paper"]["commit"],
                    "gradient_checkpointing": checkpointing,
                    "host_class": cls, "launch": HOST_CLASSES[cls]["launch"],
                    "started_utc": _utc(started), "stop": None, "stop_class": None, "steps": [], "probe": probe,
                    "output_use": "ENGINEERING_ONLY SFT fit and timing probe (P4-PROBE A): synthetic labels, at "
                                  "most 50 steps, one base; nothing kept as an arm; no label file, receipt or freeze "
                                  "record read; its GPU-hours count against P4-CAP (P4-PROBECAP A)"}
    out = job_dir / "out"
    pdir = out / "probe"
    pdir.mkdir(parents=True, exist_ok=True)
    clone = job_dir / "paper"
    try:
        native = bool(os.environ.get("P4_VENV_PYTHON"))
        record["image"] = None if native else image_identity(spec)
        record["gpu"] = gpu_identity(sh)                 # unscoped, as the P.4 job runs it (F3; T7)
        record["lease"] = lease_binding(record["gpu"], environ)
        record["card_processes_start"] = card_processes(sh, record["gpu"].get("uuid"))   # R1-CARD-SHARE (4)
        if spec["run_id"] == ADA_REPROBE["run_id"] and record["card_processes_start"].get("count") != 0:
            raise Stop("STOP: the Ada 4B re-probe requires an empty card (R1-P4-4B-CHECKPOINT)")
        record["host"] = host_identity()
        record["visible_devices"] = visible_devices(record["gpu"], environ)
        record["condor"] = condor_ad(environ)
        record["steps"].append("identity")
        record["clone"] = clone_full(spec["paper"]["commit"], clone, git, sh)
        record["code"] = probe_code_binding(spec, clone, lib_file)
        record["steps"].append("clone")
        if native:
            record["venv"] = verify_ada_venv(spec, clone)
        record["env3_freeze"] = env3_freeze(spec, clone, sh)
        if native:
            check_venv_gpu(record["gpu"], sh)
        record["steps"].append("env3_freeze")
        record["configs"] = configs(spec, clone, sh)
        record["steps"].append("configs")
        t0 = time.time()
        record["staging"] = stage(spec, arm, clone, job_dir, sh)
        record["staging"].update(seconds=round(time.time() - t0, 1), bytes=_tree_bytes(job_dir / "models"))
        record["local_paths"] = check_local_paths(arm, clone, job_dir)
        record["steps"].append("staging")
        record["table"] = table_inputs(clone, job_dir)       # no label file, receipt or freeze record; no inputs()
        record["steps"].append("table")
        data = data_build(clone, job_dir, {"table_dir": record["table"]["table_dir"]}, sh, synthetic=True)
        manifest = json.loads(_read_utf8(data / "sft_data.json"))
        if (manifest.get("labels") or {}).get("kind") != "synthetic":
            raise ProtocolStop("STOP: the probe's data directory is not a synthetic-label build (P4-PROBE A)")
        record["data"] = {"dir": str(data.relative_to(job_dir)), "sft_data_sha256": _sha_file(data / "sft_data.json"),
                          "identity": data_identity(data), "labels": "synthetic",
                          "n_train": int((manifest.get("counts") or {}).get("train", 0)),
                          "counts": manifest.get("counts")}
        record["steps"].append("data")
        run_dir = pdir / arm
        csv_path = pdir / f"{arm}.gpu_mem.csv"
        stop_sampler = start_sampler(record["gpu"]["uuid"], csv_path, probe["sample_ms"], popen)
        t_start, failure = time.time(), None
        try:
            sft_dev(clone, job_dir, arm, data, probe["lr"], probe["seed"], run_dir, sh,
                    extra=("--steps", str(probe["steps"])), checkpointing=checkpointing)
        except Stop as exc:
            failure = str(exc)
            raise
        finally:
            t_end = time.time()
            stop_sampler()
            record["wall"] = {"arm": arm, "t_start": t_start, "t_end": t_end, "wall_s": round(t_end - t_start, 3),
                              "ok": failure is None, "stop": failure}
            (pdir / "wall.json").write_text(json.dumps(record["wall"], indent=1, sort_keys=True) + "\n")
            record["memory"] = memory_summary(csv_path)
        if not record["memory"]["samples"]:
            raise Stop("STOP: the probe has no device-memory sample (S10)")
        record["run"] = probe_run_summary(run_dir, record["data"], json.loads(_read_utf8(clone / SFT_CONFIG)), probe,
                                          record["wall"], checkpointing=checkpointing)
        record["steps"].append("probe")
    except Stop as exc:
        record["stop"], record["stop_class"] = str(exc), exc.stop_class
    except Exception as exc:  # noqa: BLE001 - every failure writes the record and the sums
        record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
    record["oom"] = record["stop_class"] == "arm" and "OOM" in str(record["stop"])
    if (record.get("gpu") or {}).get("uuid"):            # R1-CARD-SHARE (4), then (3)
        record["card_processes_end"] = card_processes(sh, record["gpu"]["uuid"])
    shared_card_loss(record)
    if spec["run_id"] == ADA_REPROBE["run_id"] and record.get("card_processes_end", {}).get("count") != 0 \
            and record["stop_class"] in (None, "arm"):
        record.update(stop="STOP: the Ada 4B re-probe could not verify an empty card at exit",
                      stop_class="infrastructure")
    finished = time.time()
    record["finished_utc"] = _utc(finished)
    record["gpu_hours"] = round((finished - started) / 3600, 4)
    keep = [k.format(arm=arm) for k in PROBE_KEEP if (job_dir / k.format(arm=arm)).exists()]
    record["kept"] = keep
    (job_dir / "job_record.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    subprocess.run(["tar", "-cf", "out.tar", *keep] if keep else ["tar", "-cf", "out.tar", "--files-from", "/dev/null"],
                   cwd=job_dir, check=False)
    _write_sums(job_dir, ("out.tar", "job_record.json"))
    if record["stop"]:
        raise {"arm": ArmStop, "protocol": ProtocolStop}.get(record["stop_class"], Stop)(record["stop"])
    return record


def check_first_probe_record(path: Path | None, spec: dict, spec_sha256: str, sealed_root: Path = SEALED_ROOT) -> dict:
    """Bind the first arm's sealed STOP-free record, from the original Ada spec for the 4B re-probe."""
    first = spec["first_arm"]
    if path is None:
        raise Stop(f"STOP: probe {first} alone first; another base needs --first-record (its sealed, STOP-free probe "
                   "record)")
    path = Path(path).resolve()
    reprobe = spec["run_id"] == ADA_REPROBE["run_id"]
    run_id = ADA_REPROBE["prior_run_id"] if reprobe else spec["run_id"]
    expected_sha = ADA_REPROBE["prior_spec_sha256"] if reprobe else spec_sha256
    arm_root = (Path(sealed_root) / run_id / first).resolve()
    if path.parent.parent != arm_root or path.name != "job_record.json" or \
            not (path.parent / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: --first-record must be {arm_root}/attempt-N/job_record.json with its SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=path.parent, capture_output=True).returncode != 0:
        raise Stop("STOP: the first arm's sealed probe outputs do not verify against SHA256SUMS")
    record = json.loads(_read_utf8(path))
    receipt = json.loads(_read_utf8(path.parent / "SEAL_RECEIPT.json"))
    checks = {"schema": record.get("schema") == PROBE_RECORD_SCHEMA, "run_id": record.get("run_id") == run_id,
              "arm": record.get("arm") == first, "spec_sha256": record.get("spec_sha256") == expected_sha,
              "receipt": receipt.get("job_record_sha256") == _sha_file(path),
              "identity_verified": receipt.get("identity_verified") is True,
              "host_class": record.get("host_class") == spec.get("host_class"),     # one probe run, one class
              "stop": record.get("stop") is None and record.get("steps", [])[-1:] == ["probe"]}
    if reprobe:
        checks["published_prior_commit"] = record.get("paper_commit") == ADA_REPROBE["prior_paper_commit"]
        checks["first_seal"] = receipt.get("stop") is None and bool(re.fullmatch(r"attempt-[1-9][0-9]*",
                                                                                path.parent.name))
    failed = sorted(k for k, ok in checks.items() if not ok)
    if failed:
        raise Stop(f"STOP: the first arm's probe record is not sealed and STOP-free: {failed}")
    return {"first_probe_record_sha256": _sha_file(path)}


def ceil_hundredth(x: float) -> float:
    """``x`` rounded up to 0.01 (a float error below 1e-6 of a hundredth is not rounded up)."""
    return math.ceil(round(float(x) * 100, 6)) / 100


def full_steps(m: int, *, epochs: float, micro: int, accum: int) -> int:
    """Optimizer steps of a full run on ``m`` training rows without early stopping (``Trainer.__init__``)."""
    return int(math.ceil(max(1, math.ceil(math.ceil(m / micro) / accum)) * epochs))


def estimate_hours(n: int, s_per_step: float, spec: dict, protocol: dict) -> dict:
    """Cluster test plan §4.5: ``S = |lr| x |seeds| x steps(n) + |seeds| x sum steps(p)`` over the learning-curve points
    ``p < n``, all without early stopping; ``H = S x s_per_step_wall / 3600`` rounded up to 0.01 h."""
    micro, eff = int(protocol["micro_batch"]), int(protocol["effective_batch"])
    kw = {"epochs": float(protocol["max_epochs"]), "micro": micro, "accum": eff // micro}
    proto = spec["protocol"]
    s = len(proto["lr_grid"]) * len(proto["seeds"]) * full_steps(n, **kw) + \
        len(proto["seeds"]) * sum(full_steps(int(p), **kw) for p in proto["lc_points"] if int(p) < n)
    return {"n_train": n, "s_per_step_wall": s_per_step, "steps": s, "hours": ceil_hundredth(s * s_per_step / 3600)}


WALLCLOCK_SCHEMA = "trackp_p4_condor_wallclock/1"


def _wallclock_s(v, what: str) -> float:
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 30 * 86400:
        raise Stop(f"STOP: {what}: RemoteWallClockTime must be seconds in [0, 30 days]")
    return float(v)


CHARGE_FILE = "_wallclock.json"                  # per probe run, written once by probe-record (review round 2, M1)
CHARGE_SCHEMA = "trackp_p4_probe_charges/1"
CHARGE_NAME = re.compile(r"^_wallclock(?:\.([1-9][0-9]*))?\.json$")   # the base file, then probe-charge's supplements


def _charge_paths(run_dir: Path) -> list[Path]:
    """The run's charge files in order: ``_wallclock.json``, then ``_wallclock.1.json``, ``_wallclock.2.json``, …
    (review round 3, M1). A supplement without the base file, a gap in the numbering, or another ``_wallclock*``
    name is a STOP."""
    run_dir = Path(run_dir)
    found = {}
    for p in run_dir.glob("_wallclock*"):
        m = CHARGE_NAME.fullmatch(p.name)
        if m is None or p.is_symlink() or not p.is_file():
            raise Stop(f"STOP: {p} is not a probe charge file name (_wallclock.json or _wallclock.<n>.json)")
        found[int(m.group(1) or 0)] = p
    if found and sorted(found) != list(range(len(found))):
        raise Stop(f"STOP: the charge files of {run_dir.name} are not _wallclock.json, .1, .2, … without gaps: "
                   f"{sorted(found)}")
    return [found[k] for k in sorted(found)]


def _charge_doc(path: Path, run: str, n: int) -> dict:
    doc = json.loads(_read_utf8(path))
    if not isinstance(doc, dict) or doc.get("schema") != CHARGE_SCHEMA or doc.get("run_id") != run or \
            not isinstance(doc.get("attempts"), dict) or not doc["attempts"] or (doc.get("supplement") or 0) != n or \
            (n and (doc.get("t1_gpu_hours") is not None or doc.get("t1") is not None)):
        raise Stop(f"STOP: {path} is not charge file {n} ({CHARGE_SCHEMA}) of {run}")
    if doc.get("t1_gpu_hours") is not None or doc.get("t1") is not None:
        _t1_from_file(doc, path)
    return doc


# ---------------------------------------------------------------------------------------- T1 (P4-T1CHARGE A)
T1_WALLCLOCK_SCHEMA = "trackp_p4_t1_wallclock/1"
# T1's committed record, pinned (review round 1 of P4_T1CHARGE, M1): the folder, resolved against the repository root
# (never the cwd), and the bytes of its job files as accepted in docs/r1/reviews/P4_T1_VERSIONS_JOB_REVIEW_20261125.md.
T1_RECORD_DIR = "docs/r1/reports/trackp_p4_cluster_20261125/T1_versions"
T1_RECORD_SHA256 = {"versions.jdl": "fa7ec821ca1fd597184691117f0f846df139c0a40df32db4afb2553d2d33c97d",
                    "versions.sh": "125342d1cfed4fd435d68bbc0c5e7655845318d7522c7c9bd64536e1b3432025"}
T1_FIRST_CLUSTER = "760065"                         # versions.submit on main (merge 7556c1173)
T1_HISTORY = "condor_history.txt"                   # required: condor_history <C> -af ClusterId ProcId JobStatus RWCT
T1_FROM_HISTORY = "condor_history"                  # probe-record --t1-history: build T1's entry from T1_HISTORY
T1_SUBMIT_LINE = re.compile(r"^\s*([0-9]+) job\(s\) submitted to cluster ([0-9]+)\.\s*$", re.M)   # condor_submit
T1_SUBMIT_GLOB = "versions*.submit"                 # the pinned folder's top-level condor_submit outputs
T1_SUBMIT_TEXT = b"submitted to cluster"            # condor_submit's line; anywhere else in a T1 folder it is a STOP
T1_FOLDER_PREFIX = "t1_versions"                    # stray T1 folders under docs/, matched in any letter case
CLUSTER_ID = re.compile(r"^[0-9]+$")
T1_REPO_ROOT: Path | None = None                    # tests point this at a synthetic repository; None: this checkout


def _t1_repo(repo: Path | None = None) -> Path:
    """The repository root the pinned T1 record is read from: this p4_lib.py's checkout (it is
    ``r1/scripts/htcondor/trackp_p4/p4_lib.py`` under the root), never the cwd. Only the desk calls this
    (probe-record, assemble, check_cap); the job never does."""
    if repo is not None:
        return Path(repo)
    if T1_REPO_ROOT is not None:
        return Path(T1_REPO_ROOT)
    return Path(__file__).resolve().parents[4]


def _cluster_id(v, what: str) -> str:
    """A ClusterId as condor_history gives it (digits; an int or a string)."""
    c = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
    if not CLUSTER_ID.fullmatch(c):
        raise Stop(f"STOP: {what}: cluster_id must be the job's ClusterId from condor_history (digits), not {v!r}")
    return c


def _t1_submit_like_files(folder: Path) -> list[Path]:
    """Every file under ``folder`` (at any depth) that is named ``*.submit`` in any letter case or whose bytes contain
    "submitted to cluster" in any letter case: what could record a T1 submission. An unreadable file is a STOP."""
    out = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames.sort()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if name.lower().endswith(".submit"):
                out.append(p)
                continue
            try:
                data = p.read_bytes()
            except OSError as e:
                raise Stop(f"STOP: {p} in a T1 folder cannot be read ({e}); P4-T1CHARGE A") from None
            if T1_SUBMIT_TEXT in data.lower():
                out.append(p)
    return out


def t1_record(repo: Path | None = None) -> dict:
    """T1's committed record (R1-P4-PROBE-CHARGE, P4-T1CHARGE A), pinned: ``T1_RECORD_DIR`` under the repository root,
    whose ``versions.jdl`` and ``versions.sh`` must be the reviewed bytes (``T1_RECORD_SHA256``). Every T1 submission is
    committed inside this folder as a ``condor_submit`` output (``versions.submit``, then ``versions.<n>.submit``),
    one line ``1 job(s) submitted to cluster <C>.`` each; their ClusterIds are T1's jobs (repeats and STOP attempts
    included), and ``T1_FIRST_CLUSTER`` must be among them. No submit output, another submit count, a ClusterId twice,
    or a T1 submission recorded anywhere else is a STOP (review round 2, r2-m1): inside the pinned folder, searched
    recursively, any file other than its top-level ``versions*.submit`` files that is named ``*.submit`` or contains
    "submitted to cluster" (``rerun/versions.submit``, ``versions.2.submit.txt``); and under the repository's ``docs/``
    tree, any other folder whose name starts with ``T1_versions`` in any letter case (``t1_versions/``), ``_to_delete``
    folders included, holding such a file at any depth. Also reads the ``condor_history.txt`` (``t1_history``)."""
    root = _t1_repo(repo)
    d = root / T1_RECORD_DIR
    for name, want in T1_RECORD_SHA256.items():
        if not (d / name).is_file() or _sha_file(d / name) != want:
            raise Stop(f"STOP: {T1_RECORD_DIR}/{name} is not T1's reviewed file (sha256 {want}); P4-T1CHARGE A")
    top = sorted(p for p in d.glob(T1_SUBMIT_GLOB) if p.is_file())
    inside = [str(p.relative_to(root)) for p in _t1_submit_like_files(d) if p not in top]
    if inside:
        raise Stop(f"STOP: T1 submit records in {T1_RECORD_DIR} outside its top-level {T1_SUBMIT_GLOB} files: "
                   f"{inside}; every T1 submission is committed as versions.submit, versions.<n>.submit "
                   "(P4-T1CHARGE A)")
    strays = []
    for dirpath, dirnames, _ in os.walk(root / "docs"):
        for name in sorted(dirnames):
            p = Path(dirpath) / name
            if name.lower().startswith(T1_FOLDER_PREFIX) and p.resolve() != d.resolve() and _t1_submit_like_files(p):
                strays.append(str(p.relative_to(root)))
    if strays:
        raise Stop(f"STOP: T1 submit records outside the pinned folder {T1_RECORD_DIR}: {sorted(strays)}; every T1 "
                   "submission is committed inside it (P4-T1CHARGE A); a T1 folder moved to _to_delete with its "
                   "submit output also stops the launch")
    ids, submit = [], {}
    for p in top:
        found = T1_SUBMIT_LINE.findall(_read_utf8(p))
        if not found:
            raise Stop(f"STOP: {p} holds no condor_submit line '1 job(s) submitted to cluster <ClusterId>.'")
        for n, c in found:
            if int(n) != 1:
                raise Stop(f"STOP: {p}: T1 queues one job per submission, not {n}")
            if c in ids:
                raise Stop(f"STOP: T1's record names ClusterId {c} twice")
            ids.append(c)
        submit[p.name] = _sha_file(p)
    if T1_FIRST_CLUSTER not in ids:
        raise Stop(f"STOP: T1's record {T1_RECORD_DIR} does not name its first job {T1_FIRST_CLUSTER} in a "
                   "condor_submit output (P4-T1CHARGE A)")
    hist = d / T1_HISTORY
    return {"dir": T1_RECORD_DIR, "files": dict(T1_RECORD_SHA256), "submit_files": submit, "cluster_ids": ids,
            "history": t1_history(hist, ids) if hist.exists() else None}


def t1_history(path: Path, cluster_ids: list[str]) -> dict:
    """T1's committed ``condor_history <ClusterId> -af ClusterId ProcId JobStatus RemoteWallClockTime`` output: one
    line per job, space-separated, the wall clock a float (the ``-af`` form that
    ``docs/r1/reports/htcondor_prep_20261114/probes/parse_queue_times.py`` reads with ``line.split()``). Every line must
    have ProcId 0 and JobStatus 3 (removed) or 4 (completed), i.e. the job has left the queue; its ClusterIds must be
    exactly the pinned submit set, each once."""
    jobs, seen = [], set()
    for k, line in enumerate(_read_utf8(path).splitlines(), 1):
        if not line.strip():
            continue
        p = line.split()
        if len(p) != 4:
            raise Stop(f"STOP: {path}:{k}: expected 'ClusterId ProcId JobStatus RemoteWallClockTime'")
        c = _cluster_id(p[0], f"{path}:{k}")
        if p[1] != "0" or p[2] not in ("3", "4"):
            raise Stop(f"STOP: {path}:{k}: T1 job {c} must have ProcId 0 and JobStatus 3 or 4 (left the queue), not "
                       f"{p[1]} {p[2]}")
        try:
            wc = _wallclock_s(float(p[3]), f"{path}:{k}")
        except ValueError:
            raise Stop(f"STOP: {path}:{k}: RemoteWallClockTime {p[3]!r} is not a number") from None
        if c in seen:
            raise Stop(f"STOP: {path}: ClusterId {c} twice")
        seen.add(c)
        jobs.append({"cluster_id": c, "remote_wallclock_s": wc})
    if seen != set(cluster_ids):
        raise Stop(f"STOP: {path} must give exactly T1's submitted jobs {sorted(cluster_ids)}; missing "
                   f"{sorted(set(cluster_ids) - seen)}, extra {sorted(seen - set(cluster_ids))}")
    return {"file": T1_HISTORY, "sha256": _sha_file(path), "jobs": jobs}


def t1_charge(doc, repo: Path | None = None) -> dict:
    """P4-T1CHARGE A (R1-P4-PROBE-CHARGE): T1's GPU time, charged to the probe against phase 1's 40 GPU-h cap, from the
    same evidence as the probe wall clocks: per T1 job its ClusterId and ``RemoteWallClockTime`` from condor_history.
    ``doc`` is either ``T1_FROM_HISTORY`` (the entry is built from the pinned record's ``condor_history.txt``) or the
    JSON input ``{"schema": "trackp_p4_t1_wallclock/1", "jobs": [{"cluster_id", "remote_wallclock_s"}, ...]}`` (a
    ``record_dir`` key, if present, must be ``T1_RECORD_DIR``), which must agree with ``condor_history.txt``. Either
    way the committed ``condor_history.txt`` is required (review round 2, r2-m2: no JSON-only route). The jobs must be
    exactly the ClusterIds of the pinned record (``t1_record``): one missing, one extra or one given twice is a STOP.

    **Every** T1 job is charged (the conservative reading): each repeat or STOP attempt is its own job and is charged
    its ``RemoteWallClockTime`` (seconds / 3600, rounded to 4 decimals as the probe attempts are), with no walltime
    floor (T1 has no receipt; RemoteWallClockTime is its full measure, accumulated over restarts)."""
    record = t1_record(repo)
    hist = record["history"]
    if doc == T1_FROM_HISTORY:
        if hist is None:
            raise Stop(f"STOP: --t1-history needs {T1_RECORD_DIR}/{T1_HISTORY} (condor_history -af ClusterId ProcId "
                       "JobStatus RemoteWallClockTime)")
        given, source = hist["jobs"], f"{T1_RECORD_DIR}/{T1_HISTORY}"
    else:
        if not isinstance(doc, dict) or doc.get("schema") != T1_WALLCLOCK_SCHEMA or \
                doc.get("record_dir", T1_RECORD_DIR) != T1_RECORD_DIR or not isinstance(doc.get("jobs"), list) or \
                not doc["jobs"]:
            raise Stop(f"STOP: the T1 wall-clock input must be {{'schema': '{T1_WALLCLOCK_SCHEMA}', 'jobs': "
                       f"[{{'cluster_id', 'remote_wallclock_s'}}, ...]}} for {T1_RECORD_DIR} (P4-T1CHARGE A)")
        given, source = doc["jobs"], "input"
    jobs, seen = [], []
    for k, entry in enumerate(given):
        if not isinstance(entry, dict):
            raise Stop(f"STOP: T1 job {k} must be {{'cluster_id', 'remote_wallclock_s'}}")
        c = _cluster_id(entry.get("cluster_id"), f"T1 job {k}")
        if c in seen:
            raise Stop(f"STOP: T1 job ClusterId {c} is given twice (T1 is charged exactly once per job)")
        seen.append(c)
        wc = _wallclock_s(entry.get("remote_wallclock_s"), f"T1 job {c}")
        jobs.append({"cluster_id": c, "remote_wallclock_s": wc, "charged_gpu_hours": round(wc / 3600, 4)})
    if set(seen) != set(record["cluster_ids"]):
        raise Stop(f"STOP: the T1 jobs given are not the ClusterIds of T1's committed record {T1_RECORD_DIR} "
                   f"(missing {sorted(set(record['cluster_ids']) - set(seen))}, extra "
                   f"{sorted(set(seen) - set(record['cluster_ids']))}); every T1 job is charged (P4-T1CHARGE A)")
    if source == "input":
        if hist is None:                                # review round 2, r2-m2: no JSON-only route
            raise Stop(f"STOP: the T1 wall-clock input needs the committed {T1_RECORD_DIR}/{T1_HISTORY} to agree with "
                       "(condor_history <ClusterId> -af ClusterId ProcId JobStatus RemoteWallClockTime); commit it and "
                       "give --t1-history (P4-T1CHARGE A)")
        want = {j["cluster_id"]: j["remote_wallclock_s"] for j in hist["jobs"]}
        bad = sorted(j["cluster_id"] for j in jobs if abs(j["remote_wallclock_s"] - want[j["cluster_id"]]) > 1e-6)
        if bad:
            raise Stop(f"STOP: the T1 wall-clock input disagrees with {T1_RECORD_DIR}/{T1_HISTORY} for {bad}")
    return {"jobs": jobs, "record": record, "cluster_check": "match", "wallclock_source": source,
            "gpu_hours": round(sum(j["charged_gpu_hours"] for j in jobs), 4)}


def check_t1_record_charged(t1: dict, repo: Path | None = None) -> dict:
    """At launch (review round 1, M1 point 5 and m1): the pinned record is read again; a ClusterId in it that the
    stored T1 charge does not name (a T1 job submitted after the probe record), or a ``condor_history.txt`` changed
    since the record, is a STOP (the chat decides). Review round 2, r2-m2: the committed ``condor_history.txt`` must be
    there, and every stored wall clock is compared with it: a job it names that the charge does not hold, or a stored
    ``remote_wallclock_s`` below its RemoteWallClockTime, is a STOP (this also covers a charge stored without the
    file's sha256)."""
    record = t1_record(repo)
    stored_wc = {}
    for j in t1.get("jobs") or []:
        if not isinstance(j, dict):
            raise Stop(f"STOP: the stored T1 charge has a job that is not {{'cluster_id', 'remote_wallclock_s'}}: {j!r}")
        stored_wc[str(j.get("cluster_id"))] = _wallclock_s(j.get("remote_wallclock_s"),
                                                           f"the stored T1 charge, job {j.get('cluster_id')}")
    charged = set(stored_wc)
    missing = sorted(set(record["cluster_ids"]) - charged)
    if missing:
        raise Stop(f"STOP: T1 jobs in {T1_RECORD_DIR} that the probe charge does not hold: {missing} (submitted after "
                   "the probe record?); the chat decides (P4-T1CHARGE A)")
    hist = record["history"]
    if hist is None:
        raise Stop(f"STOP: {T1_RECORD_DIR}/{T1_HISTORY} is missing; T1's charge must rest on the committed "
                   "condor_history output (P4-T1CHARGE A)")
    stored = ((t1.get("record") or {}).get("history") or {}).get("sha256")
    if stored and hist.get("sha256") != stored:
        raise Stop(f"STOP: {T1_RECORD_DIR}/{T1_HISTORY} changed since the probe record (P4-T1CHARGE A)")
    not_held = sorted(j["cluster_id"] for j in hist["jobs"] if j["cluster_id"] not in stored_wc)
    lower = sorted(j["cluster_id"] for j in hist["jobs"]
                   if j["cluster_id"] in stored_wc and stored_wc[j["cluster_id"]] < j["remote_wallclock_s"] - 1e-6)
    if not_held or lower:
        raise Stop(f"STOP: T1's stored charge disagrees with {T1_RECORD_DIR}/{T1_HISTORY}: jobs not held {not_held}, "
                   f"stored wall clock below condor_history's for {lower}; the chat decides (P4-T1CHARGE A)")
    return {"t1_record_cluster_ids": record["cluster_ids"], "t1_charged_cluster_ids": sorted(charged)}


def _t1_from_file(doc: dict, path) -> dict:
    """T1's charge as a base charge file holds it, re-derived from its jobs (a value that does not follow from them, or
    evidence without a value, is a STOP)."""
    t1 = doc.get("t1")
    jobs = t1.get("jobs") if isinstance(t1, dict) else None
    try:
        if not isinstance(jobs, list) or not jobs:
            raise Stop("no jobs")
        ids = [_cluster_id(j.get("cluster_id"), f"{path} T1") for j in jobs]
        derived = [round(_wallclock_s(j.get("remote_wallclock_s"), f"{path} T1") / 3600, 4) for j in jobs]
        ok = len(set(ids)) == len(ids) and all(abs(float(j.get("charged_gpu_hours")) - h) < 1e-9
                                               for j, h in zip(jobs, derived)) and \
            isinstance(doc.get("t1_gpu_hours"), (int, float)) and abs(doc["t1_gpu_hours"] - round(sum(derived), 4)) < 1e-9
    except (Stop, AttributeError, TypeError, ValueError):
        ok = False
    if not ok:
        raise Stop(f"STOP: {path}: T1's charge does not follow from its jobs (t1_gpu_hours, t1.jobs; P4-T1CHARGE A)")
    return {"jobs": jobs, "record": t1.get("record"), "cluster_check": t1.get("cluster_check"),
            "gpu_hours": float(doc["t1_gpu_hours"])}


def charge_file_listing(sealed_root: Path = SEALED_ROOT) -> dict:
    """{probe run: [{"file", "path", "sha256"}, …]} for every probe run that has charge files, in file order (the form
    the probe record's ``p4_probe_charge_file:`` lines and the spec's ``caps.probe_charge_files`` carry)."""
    root, out = Path(sealed_root), {}
    for d in sorted(p for p in root.iterdir() if p.is_dir() and PROBE_RUN_ID.fullmatch(p.name)) if root.is_dir() else []:
        paths = _charge_paths(d)
        if paths:
            out[d.name] = [{"file": p.name, "path": str(p), "sha256": _sha_file(p)} for p in paths]
    return out


def check_cluster(attempt_dir: Path, cluster_id, what: str) -> str:
    """Review round 5, minor 1: a wall-clock entry's ``cluster_id`` against the sealed attempt's own record. When the
    record carries a readable ``condor.ClusterId``, the entry must give the same id (a missing or different id is a
    STOP: the wall clock would belong to another job). When the record has none (a job killed before it wrote its
    record, a stage that never ran), the entry's id cannot be checked; that is recorded as ``unverifiable``."""
    ad = (_read_record(Path(attempt_dir) / "job_record.json") or {}).get("condor") or {}
    have = str(ad.get("ClusterId")).strip() if ad.get("ClusterId") not in (None, "") else None
    if have is None:
        return "unverifiable (no ClusterId in the record)"
    if cluster_id in (None, "") or str(cluster_id).strip() != have:
        raise Stop(f"STOP: {what}: the wall clock's cluster_id {cluster_id!r} is not the record's ClusterId {have}")
    return "match"


def probe_charges(sealed_root: Path = SEALED_ROOT, *, wallclock: dict | None = None,
                  t1_wallclock: dict | None = None) -> dict:
    """P4-PROBECAP A: GPU-hours charged by every sealed attempt of every probe run (``trackp-p4-probe-*``) under the
    sealed root, STOP attempts and repeats included, plus every recorded probe submission not yet sealed (``stage_probe``
    appends to the run's ``_submissions.jsonl``; ``charged_hours`` prices it at the probe's ``walltime_s``).

    Wall clocks (review round 1, minor 1; rounds 2 and 3, M1). An attempt is charged the larger of its receipt's
    ``charged_gpu_hours`` and its ``RemoteWallClockTime``. The wall clocks come from one of two places, never both for
    one run:

    * the run's charge files (``trackp_p4_probe_charges/1``): ``_wallclock.json``, which ``probe-record`` writes once
      with the charge it used per attempt (and T1's, if charged), and ``_wallclock.<n>.json``, which ``probe-charge``
      writes once for attempts sealed into the run after that (``supplement_charges``). They are applied by default;
      an attempt no charge file names is charged at least its receipt and listed in ``unrecorded``; an attempt named
      twice is a STOP;
    * the ``wallclock`` input of ``probe-record`` (``trackp_p4_condor_wallclock/1``: ``{"runs": {<run>:
      {"<arm>/attempt-<N>": {"cluster_id", "remote_wallclock_s"}}}}``), for runs without charge files: it must name
      exactly the run's sealed attempts.

    A **direct** attempt (R1-HOST-FREE (5); its seal receipt says ``launch: direct``) has no HTCondor job: its receipt
    already charges the larger of the launcher record's wall clock (one card) and the job record's ``gpu_hours``
    (``seal``). It is charged that (or a charge file's larger value), is never "unrecorded", and a wall-clock input must
    not name it (it names exactly the run's HTCondor attempts). The charge files list it with ``launch: direct``.

    T1 (P4-T1CHARGE A, R1-P4-PROBE-CHARGE): its charge comes from one of two places, never both: ``t1_wallclock``
    (``t1_charge``: every T1 job's ClusterId and ``RemoteWallClockTime``, bound to T1's pinned committed record, from
    the JSON input or ``T1_FROM_HISTORY``), which only
    ``probe-record`` gives and which goes into the base charge file ``_wallclock.json`` of the record's run; or that
    base file, applied by default. T1 given again while a charge file holds it, T1 in two charge files, or a T1
    ClusterId that is also a probe attempt's is a STOP: T1 is charged exactly once. ``t1`` is None when neither holds
    it; ``probe_records`` and ``check_probe_ledger`` then STOP (the charge is required)."""
    runs, total, unrecorded = {}, 0.0, []
    root = Path(sealed_root)
    if wallclock is not None and (not isinstance(wallclock, dict) or wallclock.get("schema") != WALLCLOCK_SCHEMA
                                  or not isinstance(wallclock.get("runs"), dict)):
        raise Stop(f"STOP: the wall-clock input must be {{'schema': '{WALLCLOCK_SCHEMA}', 'runs': {{...}}}}")
    seen_runs, t1_files = set(), []
    files = charge_file_listing(sealed_root)
    for d in sorted(p for p in root.iterdir() if p.is_dir() and PROBE_RUN_ID.fullmatch(p.name)) if root.is_dir() else []:
        c = charged_hours({"run_id": d.name, "probe": PROBE, "caps": {}}, sealed_root)
        recorded = {}
        for n, f in enumerate(files.get(d.name, [])):
            doc = _charge_doc(Path(f["path"]), d.name, n)
            if doc.get("t1_gpu_hours") is not None:
                t1_files.append({"source": f"{d.name}/{f['file']}", **_t1_from_file(doc, f["path"])})
            for key, entry in doc["attempts"].items():
                if key in recorded:
                    raise Stop(f"STOP: {d.name}/{key} is named by two charge files")
                recorded[key] = (entry or {}, f["file"])
        given = wallclock["runs"].get(d.name) if wallclock is not None and d.name in wallclock["runs"] else None
        if recorded and given is not None:
            raise Stop(f"STOP: {d.name} already has its charge file {CHARGE_FILE}; the wall-clock input must not "
                       "name it again (use probe-charge for attempts sealed after the record)")
        keys = {f"{a['arm']}/{a['attempt']}" for a in c["attempts"]}
        if set(recorded) - keys:
            raise Stop(f"STOP: charge files of {d.name} name attempts that are not sealed: "
                       f"{sorted(set(recorded) - keys)[:5]}")
        condor_keys = {f"{a['arm']}/{a['attempt']}" for a in c["attempts"] if a.get("launch") != "direct"}
        if given is not None:
            seen_runs.add(d.name)
            if set(given) != condor_keys:
                raise Stop(f"STOP: the wall-clock input for {d.name} must give exactly its sealed HTCondor attempts; "
                           f"missing {sorted(condor_keys - set(given))}, extra {sorted(set(given) - condor_keys)} (a "
                           "direct attempt is charged by its launcher record, never by a wall-clock input)")
        attempts = []
        for a in c["attempts"]:
            a, key = dict(a), f"{a['arm']}/{a['attempt']}"
            receipt = a["charged_gpu_hours"]
            att_dir = d / a["arm"] / a["attempt"]
            if key in recorded and (recorded[key][0].get("launch") == "direct") != (a.get("launch") == "direct"):
                raise Stop(f"STOP: {d.name}/{key}: the charge file and the seal receipt disagree on direct launch")
            if a.get("launch") == "direct":     # R1-HOST-FREE (5): its receipt holds the launcher's wall clock already
                entry, fname = recorded.get(key, ({}, None))
                a.update(remote_wallclock_s=None, cluster_id=None, cluster_check="direct launch (no HTCondor job)",
                         charged_gpu_hours=round(max(receipt, float(entry.get("charged_gpu_hours") or 0.0)), 4),
                         charge_basis=fname or "receipt (direct launcher record)")
            elif given is not None:
                entry = given[key] or {}
                wc = _wallclock_s(entry.get("remote_wallclock_s"), f"{d.name}/{key}")
                a.update(remote_wallclock_s=wc, cluster_id=entry.get("cluster_id"),
                         cluster_check=check_cluster(att_dir, entry.get("cluster_id"), f"{d.name}/{key}"),
                         charged_gpu_hours=round(max(receipt, wc / 3600), 4),
                         charge_basis="max(receipt, RemoteWallClockTime)")
            elif key in recorded:
                entry, fname = recorded[key]
                a.update(remote_wallclock_s=entry.get("remote_wallclock_s"), cluster_id=entry.get("cluster_id"),
                         cluster_check=check_cluster(att_dir, entry.get("cluster_id"), f"{d.name}/{key} ({fname})"),
                         charged_gpu_hours=round(max(receipt, float(entry.get("charged_gpu_hours") or 0.0)), 4),
                         charge_basis=fname)
            else:
                a["charge_basis"] = "receipt (no wall clock recorded)"
                unrecorded.append(f"{d.name}/{key}")
            a["receipt_gpu_hours"] = receipt
            attempts.append(a)
        run_total = round(sum(a["charged_gpu_hours"] for a in attempts) +
                          sum(p["charged_gpu_hours"] for p in c["pending"]), 4)
        runs[d.name] = {"total": run_total, "attempts": attempts, "pending": c["pending"],
                        "charge_files": files.get(d.name, [])}
        total += run_total
    if wallclock is not None and set(wallclock["runs"]) - seen_runs:
        raise Stop(f"STOP: the wall-clock input names runs without sealed attempts or with a charge file: "
                   f"{sorted(set(wallclock['runs']) - seen_runs)}")
    if len(t1_files) > 1:
        raise Stop(f"STOP: T1 is charged in more than one charge file ({[t['source'] for t in t1_files]}); T1 is "
                   "charged exactly once (P4-T1CHARGE A)")
    if t1_wallclock is not None and t1_files:
        raise Stop(f"STOP: T1 is already charged in a probe charge file ({t1_files[0]['source']}); it is given once, "
                   "to the first probe record (P4-T1CHARGE A)")
    t1 = {"source": "input", **t1_charge(t1_wallclock)} if t1_wallclock is not None else \
        (t1_files[0] if t1_files else None)
    if t1 is not None:
        probe_ids = {str(a["cluster_id"]).strip() for r in runs.values() for a in r["attempts"]
                     if a.get("cluster_id") not in (None, "")}
        both = sorted(probe_ids & {str(j["cluster_id"]) for j in t1["jobs"]})
        if both:
            raise Stop(f"STOP: ClusterId {both} is charged as T1 and as a probe attempt; each job is charged once "
                       "(P4-T1CHARGE A)")
        total += t1["gpu_hours"]
    return {"runs": runs, "pending": [p for r in runs.values() for p in r["pending"]],
            "t1_gpu_hours": t1["gpu_hours"] if t1 is not None else None, "t1": t1,
            "unrecorded": unrecorded, "charge_files": files, "total": round(total, 4)}


def charge_file_docs(charges: dict, record_run: str) -> dict:
    """The charge files ``probe-record`` writes: one per run whose wall clocks came from the input, with the charge it
    used per attempt. T1's charge, when it came from the input (P4-T1CHARGE A), goes into the base file
    ``_wallclock.json`` of the record's own run, with its jobs and the record they were bound to; never into a
    supplement. If that run already has its base file, T1 cannot be stored and this is a STOP."""
    out = {}
    t1 = charges.get("t1")
    from_input = t1 is not None and t1.get("source") == "input"
    for run, r in charges["runs"].items():
        if r["charge_files"] or not r["attempts"]:
            continue
        mine = from_input and run == record_run
        out[run] = {"schema": CHARGE_SCHEMA, "run_id": run, "label": ENGINEERING_ONLY, "supplement": 0,
                    "rule": "P4-PROBECAP A; review round 2, M1: written once by probe-record; probe_charges applies it"
                            + ("; P4-T1CHARGE A: T1's charge, every T1 job, held here once" if mine else ""),
                    "attempts": {f"{a['arm']}/{a['attempt']}": {
                        "receipt_gpu_hours": a["receipt_gpu_hours"], "remote_wallclock_s": a.get("remote_wallclock_s"),
                        "cluster_id": a.get("cluster_id"), "charged_gpu_hours": a["charged_gpu_hours"],
                        **({"launch": "direct"} if a.get("launch") == "direct" else {})}
                        for a in r["attempts"]},
                    "t1_gpu_hours": t1["gpu_hours"] if mine else None,
                    "t1": {k: t1.get(k) for k in ("jobs", "record", "cluster_check", "wallclock_source")}
                    if mine else None}
    if from_input and record_run not in out:
        raise Stop(f"STOP: T1's charge goes into the base charge file {CHARGE_FILE} this record writes for "
                   f"{record_run}, and {record_run} already has one; T1 is never put in a supplement (P4-T1CHARGE A)")
    return out


def write_charge_files(docs: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """Write each charge file once (an existing file is never overwritten); returns {run: {path, sha256}}."""
    out = {}
    for run, doc in docs.items():
        path = Path(sealed_root) / run / CHARGE_FILE
        with path.open("x", encoding="utf-8") as fh:
            fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        out[run] = {"path": str(path), "sha256": _sha_file(path)}
    return out


def supplement_charges(run_id: str, wallclock: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """Round 3, M1, the recovery path (``p4_lib.py probe-charge``): attempts sealed into a probe run that already has
    its charge file get a supplementary charge file ``_wallclock.<n>.json`` (the next ``n``), written once, naming
    exactly the run's currently unrecorded attempts with their ``RemoteWallClockTime`` (``wallclock`` in the
    ``trackp_p4_condor_wallclock/1`` form, naming only this run). The run must have no pending submission. A rebuilt
    probe record then gives the new ``p4_probe_gpu_hours`` and lists every charge file."""
    if not PROBE_RUN_ID.fullmatch(str(run_id)):
        raise Stop(f"STOP: {run_id} is not a probe run id")
    run_dir = Path(sealed_root) / run_id
    paths = _charge_paths(run_dir) if run_dir.is_dir() else []
    if not paths:
        raise Stop(f"STOP: {run_id} has no {CHARGE_FILE}; its first wall clocks go through probe-record")
    if not isinstance(wallclock, dict) or wallclock.get("schema") != WALLCLOCK_SCHEMA or \
            set((wallclock.get("runs") or {})) != {run_id}:
        raise Stop(f"STOP: the wall-clock input must be {WALLCLOCK_SCHEMA} naming exactly the run {run_id}")
    charges = probe_charges(sealed_root)
    r = charges["runs"][run_id]
    if r["pending"]:
        raise Stop(f"STOP: {run_id} has {len(r['pending'])} pending submission(s); seal every attempt first")
    todo = {u.split("/", 1)[1] for u in charges["unrecorded"] if u.split("/", 1)[0] == run_id}
    if not todo:
        raise Stop(f"STOP: {run_id} has no unrecorded attempt")
    given = wallclock["runs"][run_id]
    if set(given) != todo:
        raise Stop(f"STOP: the wall-clock input must name exactly the unrecorded attempts of {run_id}; missing "
                   f"{sorted(todo - set(given))}, extra {sorted(set(given) - todo)}")
    attempts = {}
    for a in r["attempts"]:
        key = f"{a['arm']}/{a['attempt']}"
        if key in todo:
            entry = given[key] or {}
            wc = _wallclock_s(entry.get("remote_wallclock_s"), f"{run_id}/{key}")
            check = check_cluster(run_dir / a["arm"] / a["attempt"], entry.get("cluster_id"), f"{run_id}/{key}")
            attempts[key] = {"receipt_gpu_hours": a["receipt_gpu_hours"], "remote_wallclock_s": wc,
                             "cluster_id": entry.get("cluster_id"), "cluster_check": check,
                             "charged_gpu_hours": round(max(a["receipt_gpu_hours"], wc / 3600), 4)}
    n = len(paths)
    path = run_dir / f"_wallclock.{n}.json"
    doc = {"schema": CHARGE_SCHEMA, "run_id": run_id, "label": ENGINEERING_ONLY, "supplement": n,
           "rule": "P4-PROBECAP A; review round 3, M1: written once by probe-charge for attempts sealed after the "
                   "probe record; probe_charges applies it", "attempts": attempts, "t1_gpu_hours": None, "t1": None}
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return {"path": str(path), "sha256": _sha_file(path), "supplement": n, "attempts": sorted(attempts)}


def spec_charge_files(listing: dict) -> dict:
    """The ``caps.probe_charge_files`` form of a charge-file listing: {run: [sha256 of each file, in file order]}."""
    return {run: [f["sha256"] for f in files] for run, files in sorted(listing.items())}


def check_probe_ledger(spec: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """M1 of review rounds 1-3 and minor 1 of round 3: the spec's ``caps.probe_gpu_hours`` and
    ``caps.probe_charge_files`` against the sealed tree. The charge files on disk must be exactly those the spec lists,
    with the same sha256 (a changed, missing or unlisted file is a STOP); the probe charge is then re-derived with them
    (``probe_charges``). A probe attempt no charge file names, a pending probe submission, no charge file holding T1's
    charge (P4-T1CHARGE A), or a re-derived charge above the spec's value is a STOP. For the attempts the record charged
    and T1, the re-derived value equals the record's ``p4_probe_gpu_hours``."""
    listed = (spec.get("caps") or {}).get("probe_charge_files")
    if not isinstance(listed, dict):
        raise Stop("STOP: caps.probe_charge_files must list the probe charge files (P4-PROBECAP A)")
    on_disk = spec_charge_files(charge_file_listing(sealed_root))
    if on_disk != listed:
        changed = sorted(r for r in set(on_disk) | set(listed) if on_disk.get(r) != listed.get(r))
        raise Stop(f"STOP: the probe charge files on disk are not the ones caps.probe_charge_files lists (changed, "
                   f"missing or unlisted) for {changed} (P4-PROBECAP A)")
    charges = probe_charges(sealed_root)
    if charges["unrecorded"]:
        raise Stop(f"STOP: probe attempts sealed after the probe record (no charge file names them): "
                   f"{charges['unrecorded'][:5]}; record them with probe-charge, then rebuild the probe record and "
                   "the spec (P4-PROBECAP A)")
    if charges["pending"]:
        raise Stop(f"STOP: {len(charges['pending'])} probe submission(s) are recorded but not sealed (P4-PROBECAP A)")
    if charges["t1"] is None:
        raise Stop("STOP: no probe charge file holds T1's charge; the probe record charges T1 in its base charge file "
                   "(P4-T1CHARGE A)")
    t1_check = check_t1_record_charged(charges["t1"])
    derived = ceil_hundredth(charges["total"])
    have = probe_gpu_hours(spec) or 0.0
    if derived > have + 1e-9:
        raise Stop(f"STOP: the sealed tree charges {derived} GPU-h to the probe, more than caps.probe_gpu_hours {have}: "
                   "rebuild the probe record and the spec (P4-PROBECAP A)")
    return {"probe_gpu_hours_spec": have, "probe_gpu_hours_sealed_tree": derived, "charge_files": on_disk,
            "t1": t1_check}


def _cluster(rec: dict | None) -> tuple[str, int] | None:
    """(schedd, ClusterId) from a probe record's HTCondor job ad, or None (also when the ``GlobalJobId`` gives no
    schedd: ClusterIds are only comparable within one named schedd)."""
    ad = (rec or {}).get("condor") or {}
    try:
        schedd, cluster = str(ad.get("GlobalJobId") or "").split("#")[0], int(ad["ClusterId"])
    except (KeyError, TypeError, ValueError):
        return None
    return (schedd, cluster) if schedd else None      # review round 5, minor 3: no schedd, no ClusterId ordering


def submission_order(arm_dir: Path, ledger: Path) -> dict:
    """Review round 4, M1: the STOP-free sealed probe attempts of one arm in **submission** order (attempt numbers
    follow seal order, which the operator controls). Order by the HTCondor ``ClusterId`` each record carries, when every
    such attempt has one from the same schedd; otherwise by the attempt's position in the submission ledger (its seal
    receipt's ``source_dir`` against the ledger entry's ``stage``, each entry used once); otherwise, with two or more
    STOP-free attempts, a STOP. Returns the first, the extras (ids, never used) and the basis."""
    free = []
    for att in sorted(Path(arm_dir).glob("attempt-*")):
        rp = att / "SEAL_RECEIPT.json"
        receipt = json.loads(_read_utf8(rp)) if rp.is_file() else {}
        if receipt and not receipt.get("stop"):
            free.append((att.name, receipt, _read_record(att / "job_record.json")))
    if len(free) <= 1:
        return {"first": free[0][0] if free else None, "extra": [], "basis": "single"}
    clusters = [_cluster(rec) for _, _, rec in free]
    if all(c is not None for c in clusters) and len({c[0] for c in clusters}) == 1 and \
            len({c[1] for c in clusters}) == len(clusters):
        ranked = sorted(zip(clusters, free), key=lambda x: x[0][1])
        ids = [{"attempt": f[0], "cluster_id": c[1]} for c, f in ranked]
        return {"first": ranked[0][1][0], "extra": ids[1:], "basis": "ClusterId"}
    entries = [e for e in read_ledger(ledger) if e["arm"] == Path(arm_dir).name]
    stages = [str(Path(e["stage"]).resolve()) if e.get("stage") else None for e in entries]
    pos = {}
    for name, receipt, _ in free:
        src = receipt.get("source_dir")
        msha = receipt.get("stage_manifest_sha256")   # a direct attempt: its launcher record names the stage it ran
        hits = [k for k, s in enumerate(stages) if k not in pos.values() and
                ((src and s == str(Path(src).resolve())) or
                 (msha and entries[k].get("stage_manifest_sha256") == msha))]
        if not hits:
            raise Stop(f"STOP: the STOP-free probe attempts of {Path(arm_dir).name} cannot be ordered by submission "
                       f"(no ClusterId from one schedd, no ledger entry for {name}): the author decides")
        pos[name] = hits[0]
    ranked = sorted(free, key=lambda f: pos[f[0]])
    return {"first": ranked[0][0], "extra": [{"attempt": f[0], "ledger_position": pos[f[0]]} for f in ranked[1:]],
            "basis": "ledger order"}


def probe_records(probe_spec: dict, probe_spec_sha256: str, p4_spec: dict, sealed: list[Path],
                  sealed_root: Path = SEALED_ROOT, *, wallclock: dict | None = None,
                  t1_wallclock: dict | None = None) -> dict:
    """The §4.4 record (``trackp_p4_h200_sft_probe/1``) from the first sealed, verified, STOP-free probe attempt of each
    arm of the P.4 spec **by submission order** (``submission_order``: HTCondor ``ClusterId``, else ledger order; never
    seal order); later STOP-free attempts of an arm are charged, never used, and listed in
    ``extra_stop_free_attempts`` so that more than one run per base is visible; and the §4.5 hours; ``p4_probe_gpu_hours`` is every probe attempt's charge (``probe_charges``)
    plus T1's (P4-T1CHARGE A, R1-P4-PROBE-CHARGE: every T1 job's ``RemoteWallClockTime``, from ``t1_wallclock`` for the
    first record, or from the base charge file that record wrote for a rebuilt one), rounded up to 0.01. A record
    without T1's charge is a STOP. The P.4 spec with these values must validate (S12); its projection is reported
    against the P4-CAP figures (``threshold``; R1-NO-TIMEOUT (3): reported, not refused).

    R1-HOST-FREE: the record is of the probe spec's one host class (``host_class``), which the P.4 spec must admit with
    the same fixed values and host config; every attempt's record must name that class. Its estimate is that class's
    (``hosts.<class>.estimate``): the record prints ``p4_probe_host_class: <class>`` with the hours lines, and the S12
    check projects the P.4 spec as launched on that class alone. The schema is ``trackp_p4_<probe_label>/1``
    (``trackp_p4_h200_sft_probe/1`` for the H200 class, as before)."""
    loaded = validate_probe_spec(probe_spec)
    validate_spec(p4_spec)
    cls = loaded["host_class"]
    reprobe = probe_spec["run_id"] == ADA_REPROBE["run_id"]
    same = ("env3", "sft_config", "split_file", "table", "layout", "arms", "first_arm", "protocol")
    differ = [k for k in same if probe_spec.get(k) != p4_spec.get(k)]
    differ += [f"image.{k}" for k in ("digest", "row") if probe_spec["image"].get(k) != p4_spec["image"].get(k)]
    p4_host = (p4_spec.get("hosts") or {}).get(cls)
    probe_host = probe_spec["hosts"][cls]
    if not isinstance(p4_host, dict) or any(p4_host.get(k) != probe_host.get(k) for k in HOST_FIXED) or \
            probe_host["host_config"]["path"] != p4_host["host_config"]["path"] or \
            (not _placeholder(p4_host["host_config"]["sha256"]) and
             probe_host["host_config"]["sha256"] != p4_host["host_config"]["sha256"]):
        differ.append(f"hosts.{cls}")
    if differ:
        raise Stop(f"STOP: the probe spec and the P.4 spec differ in {differ}: the probe does not measure these jobs")
    jobs, keys, extras = {}, {}, {}
    for d in map(Path, sealed):
        arm = d.parent.name
        carried = reprobe and arm not in CHECKPOINT_ARMS
        run_id = ADA_REPROBE["prior_run_id"] if carried else probe_spec["run_id"]
        spec_sha = ADA_REPROBE["prior_spec_sha256"] if carried else probe_spec_sha256
        run_root = (Path(sealed_root) / run_id).resolve()
        if d.resolve().parent.parent != run_root or not re.fullmatch(r"attempt-[1-9][0-9]*", d.name):
            raise Stop(f"STOP: {d} is not a sealed probe attempt under {run_root}/<arm>/attempt-N")
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=d, capture_output=True).returncode != 0:
            raise Stop(f"STOP: {d} does not verify against its SHA256SUMS")
        rec = json.loads(_read_utf8(d / "job_record.json"))
        receipt = json.loads(_read_utf8(d / "SEAL_RECEIPT.json"))
        if receipt.get("job_record_sha256") != _sha_file(d / "job_record.json") or rec.get("stop") or \
                rec.get("schema") != PROBE_RECORD_SCHEMA or rec.get("spec_sha256") != spec_sha or \
                rec.get("run_id") != run_id or rec.get("arm") != arm or receipt.get("identity_verified") is not True or \
                rec.get("steps", [])[-1:] != ["probe"] or rec.get("host_class") != cls:
            raise Stop(f"STOP: {d} is not a sealed, verified, STOP-free probe attempt of this probe spec (on {cls})")
        if reprobe:
            commit = ADA_REPROBE["prior_paper_commit"] if carried else probe_spec["paper"]["commit"]
            if rec.get("paper_commit") != commit or receipt.get("stop") or card_was_shared(rec, receipt):
                raise Stop(f"STOP: {d} does not attest the bound commit and empty Ada card")
            counts = (receipt.get("other_processes_start"), receipt.get("other_processes_end"),
                      rec.get("card_processes_start"), rec.get("card_processes_end"))
            if not carried and any((c or {}).get("count") != 0 for c in counts):
                raise Stop(f"STOP: {d} lacks a complete empty-card observation")
            effective = (rec.get("run") or {}).get("gradient_checkpointing")
            verified = (effective == "off (SFT path)" if carried else
                        (effective is True and rec.get("gradient_checkpointing") is True))
            if not verified:
                raise Stop(f"STOP: {d} does not attest the required checkpointing setting for {arm}")
        if arm in jobs:
            raise Stop(f"STOP: two probe attempts given for {arm}")
        order = submission_order(d.parent, Path(sealed_root) / run_id / SUBMISSION_LEDGER)
        if order["first"] != d.name:
            raise Stop(f"STOP: {d.name} is not the first STOP-free probe attempt of {arm} by submission order "
                       f"({order['first']}, by {order['basis']}): the record uses that one, never one chosen by result")
        extras[arm] = order["extra"]
        jobs[arm] = (d, rec)
        for k, v in {**({} if reprobe else {"paper_commit": rec.get("paper_commit")}),
                     "image": rec.get("image"), "venv": rec.get("venv"),
                     "configs": {x: rec["configs"][x] for x in ("host_config", "sft_config")},
                     "data": rec["data"]["identity"], "n_train": rec["data"]["n_train"],
                     "env3": {x: rec["env3_freeze"].get(x) for x in ("status", "image_line", "local_label")}}.items():
            keys.setdefault(k, set()).add(json.dumps(v, sort_keys=True))
    if set(jobs) != set(p4_spec["arms"]):
        raise Stop(f"STOP: the probe record needs every arm {p4_spec['arms']}; got {sorted(jobs)}")
    differ = sorted(k for k, v in keys.items() if len(v) != 1)
    if differ:
        raise Stop(f"STOP: the probe jobs differ in {differ} (one image, commit, config and synthetic data directory)")
    entries, hours = [], {}
    for arm in p4_spec["arms"]:
        d, rec = jobs[arm]
        run, mem = rec["run"], rec["memory"]
        est = estimate_hours(rec["data"]["n_train"], run["s_per_step_wall"], p4_spec, run["protocol"])
        hours[arm] = est["hours"]
        entries.append({
            "arm": arm, "registry_keys": list(ARMS[arm]), "attempt": d.name, "condor_job": rec.get("condor"),
            **({"probe_run_id": rec["run_id"], "probe_spec_sha256": rec["spec_sha256"]} if reprobe else {}),
            "host_class": rec.get("host_class"), "launch": rec.get("launch"),
            "hostname": (rec.get("host") or {}).get("hostname"), "gpu": rec.get("gpu"),
            "image_digest": (rec.get("image") or {}).get("digest"),
            "versions_sha256": (rec.get("image") or {}).get("versions_sha256"),
            **({"venv": rec["venv"]} if rec.get("venv") else {}),
            "paper_commit": rec["paper_commit"], "host_config_sha256": rec["configs"]["host_config"]["sha256"],
            "sft_config_sha256": rec["configs"]["sft_config"]["sha256"],
            "env3_freeze": {x: rec["env3_freeze"].get(x) for x in ("status", "image_line", "local_label")},
            **({"venv_freeze_sha256": rec["env3_freeze"]["venv_freeze_sha256"]} if rec.get("venv") else {}),
            "staging_seconds": rec["staging"].get("seconds"), "staged_bytes": rec["staging"].get("bytes"),
            "labels": rec["data"]["labels"], "sft_data_sha256": rec["data"]["sft_data_sha256"],
            "n_train": rec["data"]["n_train"], "micro_batch": run["protocol"]["micro_batch"],
            "effective_batch": run["protocol"]["effective_batch"], "max_tokens": run["max_tokens"],
            "gradient_checkpointing": run["gradient_checkpointing"], "protocol_deviation": run["protocol_deviation"],
            "steps_per_epoch": run["steps_per_epoch"], "total_steps": run["total_steps"],
            "stopped_at": run["stopped_at"], "early_stopped": run["early_stopped"],
            "wall_s": rec["wall"]["wall_s"], "s_per_step_wall": run["s_per_step_wall"],
            "step_s_median": run["step_s"]["step_s_median"], "step_s_p90": run["step_s"]["step_s_p90"],
            "step_s_max": run["step_s"]["step_s_max"], "peak_memory_used_mib": mem["peak_memory_used_mib"],
            "memory_total_mib": mem["memory_total_mib"], "headroom_frac": mem["headroom_frac"],
            "memory_samples": mem["samples"], "oom": bool(rec.get("oom")), "rc": 0, "stop": rec.get("stop"),
            "stop_class": rec.get("stop_class"), "gpu_hours_consumed": rec.get("gpu_hours"),
            "estimate_hours": est["hours"], "estimate_steps": est["steps"],
            "card_shared": card_was_shared(rec, json.loads(_read_utf8(d / "SEAL_RECEIPT.json")))})
    charges = probe_charges(sealed_root, wallclock=wallclock, t1_wallclock=t1_wallclock)
    if probe_spec["run_id"] not in charges["runs"]:
        raise Stop(f"STOP: no sealed attempt of {probe_spec['run_id']} under {sealed_root}")
    if charges["pending"]:
        raise Stop(f"STOP: {len(charges['pending'])} probe submission(s) are recorded but not sealed "
                   f"({sorted({p['arm'] for p in charges['pending']})}): seal every attempt first (P4-PROBECAP A)")
    if charges["t1"] is None:
        raise Stop("STOP: T1's RemoteWallClockTime is required in the probe charge (P4-T1CHARGE A): give --t1-history "
                   f"({T1_RECORD_DIR}/{T1_HISTORY}) or --t1-wallclock ({T1_WALLCLOCK_SCHEMA}, agreeing with that "
                   "file); only a rebuilt record takes it from the base charge file")
    if charges["t1"]["source"] != "input":             # a rebuilt record: the pinned record must hold no newer T1 job
        check_t1_record_charged(charges["t1"])
    docs = charge_file_docs(charges, probe_spec["run_id"])
    probe_hours = ceil_hundredth(charges["total"])
    would = json.loads(json.dumps(p4_spec))
    would["hosts"] = {cls: would["hosts"][cls]}        # S12 as launched on the measured class alone
    would["hosts"][cls]["estimate"]["hours"] = dict(hours)
    would["caps"]["probe_gpu_hours"] = probe_hours
    proj = validate_spec(would)["projection"]          # S12; the 40 GPU-h / 64 slot-h figures are reported
    lines = [f"p4_probe_host_class: {cls}"] + \
        [f"p4_estimate_hours: {arm} {hours[arm]:.2f}" for arm in p4_spec["arms"]] + \
        [f"p4_probe_gpu_hours: {probe_hours:.2f}"]
    return {"schema": f"trackp_p4_{HOST_CLASSES[cls]['probe_label']}/1", "label": ENGINEERING_ONLY,
            "probe_run_id": probe_spec["run_id"], "host_class": cls, "gpu_name": HOST_CLASSES[cls]["gpu_name"],
            "probe_spec_sha256": probe_spec_sha256,
            "rule": "P4-PROBE A, P4-PROBECAP A (R1-P4-TESTPLAN-DECISIONS); P4-T1CHARGE A (R1-P4-PROBE-CHARGE): T1's "
                    "RemoteWallClockTime, every T1 job, is in p4_probe_gpu_hours; cluster test plan §4.4 and §4.5",
            "binding_note": "p4_switch binds the Markdown record's printed lines (p4_estimate_hours, p4_probe_gpu_hours, "
                            "p4_probe_charge_file), not this JSON file; the hours, the probe charge and the charge files "
                            "reach the spec, and are checked against it, only through those lines",
            "entries": entries, "estimate_hours": hours, "probe_gpu_hours_charged": charges["total"],
            "p4_probe_gpu_hours": probe_hours, "probe_charges": charges, "projection": proj,
            "threshold": threshold_report(proj),
            "wallclock_input": wallclock is not None, "t1_charged": True, "t1_gpu_hours": charges["t1_gpu_hours"],
            "t1": charges["t1"], "charge_file_docs": docs,
            "probe_over_2_gpu_h": probe_hours > 2.0,
            "extra_stop_free_attempts": {a: v for a, v in sorted(extras.items()) if v},
            "headroom_below_15pct": sorted(e["arm"] for e in entries if e["headroom_frac"] is not None
                                           and e["headroom_frac"] < 0.15),
            "card_shared_arms": sorted(e["arm"] for e in entries if e["card_shared"]),
            "fit_and_timing_reliable": not any(e["card_shared"] for e in entries),
            "lines": lines}


def card_was_shared(record: dict, receipt: dict) -> bool:
    """Review M8: another compute process was on the probe's card at its start or end (the launcher's host-side
    counts in the receipt, or the job's own counts). The fit (peak memory, headroom) and the timing of a shared-card
    probe are descriptive only (R1-CARD-SHARE (2)); the record says so (``card_shared_arms``,
    ``fit_and_timing_reliable``), and the Ada probe is run on an empty card (``p4_direct.py cards``)."""
    counts = [receipt.get("other_processes_start"), receipt.get("other_processes_end"),
              record.get("card_processes_start"), record.get("card_processes_end")]
    return bool(receipt.get("card_shared")) or any(isinstance(c, dict) and isinstance(c.get("count"), int) and
                                                   c["count"] > 0 for c in counts)


# =============================================================================================== seal / assemble
def _read_record(path: Path):
    """The job record, or None when it is missing, empty, not UTF-8 or not JSON (a walltime kill): such an attempt is
    sealed as unreadable, never refused."""
    try:
        rec = json.loads(_read_utf8(Path(path)))
    except (OSError, ValueError, Stop):         # Stop: _read_utf8's refusal of a non-UTF-8 file
        return None
    return rec if isinstance(rec, dict) else None


LOG_HEADER = {"probe": ("P4 probe container job start", "P4 probe venv job start"),
              "p4": ("P4 container job start", "P4 venv job start")}
CLEAN_END = re.compile(r"^P4 (?:probe )?(?:container|venv) job end \S+ rc=0\s*$", re.M)


def logged_host_class(src: Path) -> str | None:
    """The ``host_class=`` the wrapper's start line in ``p4_run.log`` names (``p4_job.sh``, ``p4_probe.sh``), or None."""
    log = Path(src) / "p4_run.log"
    if not log.is_file():
        return None
    for line in log.read_bytes().decode("utf-8", "replace").splitlines():
        if line.startswith(LOG_HEADER["probe"] + LOG_HEADER["p4"]):
            m = re.search(r"\shost_class=(\S+)", line)
            return m.group(1) if m else None
    return None


def clean_exit_logged(src: Path) -> bool:
    """True when ``p4_run.log`` holds a wrapper's end line with ``rc=0`` (a job killed by the walltime or evicted never
    writes it: the wrapper is killed before its last ``echo``)."""
    log = Path(src) / "p4_run.log"
    return log.is_file() and CLEAN_END.search(log.read_bytes().decode("utf-8", "replace")) is not None


STAGE_KIND = {"trackp_p4_probe_stage/1": "probe", "trackp_p4_stage/1": "p4"}   # STAGE_MANIFEST.json schemas


def attempt_kind(src: Path, record: dict | None, launch: dict | None = None) -> str | None:
    """"probe" or "p4" from the record (its schema or mode), else from a direct launcher record's ``mode`` (``probe``
    or ``job``), else from the first line of ``p4_run.log`` that one of
    the two wrappers writes, else (a job that never ran, sealed from its stage directory; review round 2, minor 2)
    from the stage's ``STAGE_MANIFEST.json`` (``trackp_p4_probe_stage/1`` with mode ``probe``, or ``trackp_p4_stage/1``,
    not a preview); None when none of them tells."""
    if record is not None and (record.get("schema") == PROBE_RECORD_SCHEMA or record.get("mode") == "probe"):
        return "probe"
    if record is not None and record.get("schema") == RECORD_SCHEMA:
        return "p4"
    if launch is not None and launch.get("mode") in ("probe", "job"):
        return {"probe": "probe", "job": "p4"}[launch["mode"]]
    log = Path(src) / "p4_run.log"
    if log.is_file():
        for line in log.read_bytes().decode("utf-8", "replace").splitlines():
            if line.startswith(LOG_HEADER["probe"]):
                return "probe"
            if line.startswith(LOG_HEADER["p4"]):
                return "p4"
    man = Path(src) / "STAGE_MANIFEST.json"
    if man.is_file():
        try:
            m = json.loads(_read_utf8(man))
        except (ValueError, Stop):
            return None
        kind = STAGE_KIND.get(m.get("schema")) if isinstance(m, dict) else None
        if kind == "probe" and m.get("mode") == "probe":
            return "probe"
        if kind == "p4" and m.get("preview") is False:
            return "p4"
    return None


def seal(job_output: Path, spec: dict, arm: str, sealed_root: Path = SEALED_ROOT, *,
         unknown_kind_confirmed: bool = False) -> dict:
    """Copy one attempt to ``<sealed_root>/<run_id>/<arm>/attempt-N/`` (no overwrite; a new attempt for a repeated job,
    never a resume) with a receipt binding the record and log. Every attempt is sealed, so its outputs are kept and
    its GPU-hours counted (P4-JOB A, P4-CAP A):

    - a readable record must be this run's and arm's and ENGINEERING_ONLY (else STOP: the wrong job);
    - ``SHA256SUMS``, when present and non-empty, must verify (else STOP); a killed or early-stopped job leaves the
      empty files ``p4_job.sh`` pre-creates (``sums: absent``; empty files are kept as they are);
    - ``identity_verified`` is true only for a record that names a host class the spec admits, of this attempt's
      launch kind, and carries that class's GPU (name and compute capability) and the spec's image (v2.2) digest;
    - the attempt's kind (``attempt_kind``: the record's schema or mode, else the wrapper's first log line, else the
      stage manifest of a job that never ran) must be the spec's (a probe attempt only with a probe spec, a P.4
      attempt only with the P.4 spec); an attempt that shows none of them is sealed only with
      ``unknown_kind_confirmed`` and charged at least the larger of the probe's and the arm's walltime (and the
      record's ``gpu_hours`` if larger);
    - ``charged_gpu_hours`` is the record's ``gpu_hours``, or, with no readable value, the arm's requested walltime
      (the most the slot could have used; for a probe spec, the probe's ``walltime_s``).

    **Direct attempts** (R1-HOST-FREE; the outputs carry the launcher's ``direct_launch.json``, which is copied and
    bound by sha256 in the receipt, ``launch: direct``): the launcher record must be this run's, arm's and kind's, of a
    direct class the spec admits, with the spec's image digest, and the job record (when readable) must name the same
    class and the leased card's UUID (one job, one card), else a STOP. ``identity_verified`` also needs the launcher's
    status ``finished``. The charge counts GPU-hours on any card (R1-HOST-FREE (5)): a complete launcher record
    (``ended_utc``, ``wall_clock_s`` and ``exit_code`` set) charges the larger of its wall clock (the lease span, one
    card) and the record's ``gpu_hours``; an incomplete one (the launcher was killed before its end) charges the
    largest of the time from the launch start to this seal, the requested walltime bound and the record's
    ``gpu_hours`` (fail closed: nothing bounds a direct job's wall clock). Without a launcher record, a record that
    names a direct class is a STOP (no evidence bounds its GPU time), and so is one whose ``p4_run.log`` start line
    names a direct class (review M4); an HTCondor attempt is sealed as before, and ``identity_verified`` needs its
    record to name an admitted HTCondor class whose GPU it carries.

    **The receipt's ``stop`` and ``stop_class`` are authoritative** (review M5): an arm STOP of an attempt that lost its
    card to another compute process is reclassified ``infrastructure`` here (R1-CARD-SHARE (3)) from the launcher's
    host-side counts even when the job record, which saw only what the container showed, still says ``arm``; every
    reader of an attempt's outcome reads the receipt."""
    src = Path(job_output).resolve()
    record = _read_record(src / "job_record.json")
    if record is not None and (record.get("label") != ENGINEERING_ONLY or record.get("run_id") != spec["run_id"]
                               or record.get("arm") != arm):
        raise Stop("STOP: the job record does not match the run/arm or is not ENGINEERING_ONLY")
    launch = read_direct_launch(src)
    rec_class = (record or {}).get("host_class")
    if launch is None and rec_class is None:        # review M4: the wrapper's log names the class the job was told
        rec_class_logged = logged_host_class(src)
        if rec_class_logged in HOST_CLASSES and HOST_CLASSES[rec_class_logged]["launch"] == "direct":
            raise Stop(f"STOP: p4_run.log names the direct class {rec_class_logged} but {DIRECT_LAUNCH_FILE} is "
                       "missing: it is not sealed as an HTCondor attempt (copy the launcher record back)")
    if launch is None and rec_class in HOST_CLASSES and HOST_CLASSES[rec_class]["launch"] == "direct":
        raise Stop(f"STOP: the record names the direct class {rec_class} but {DIRECT_LAUNCH_FILE} is missing: nothing "
                   "bounds its GPU time; copy the launcher record back with the outputs (the author decides otherwise)")
    sums = "absent"
    if (src / "SHA256SUMS").is_file() and (src / "SHA256SUMS").stat().st_size > 0:
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
            raise Stop("STOP: transferred SHA256SUMS verification failed")
        sums = "verified"
    if record is None and clean_exit_logged(src):   # review round 5, minor 2: a clean result is never a "killed" job
        raise Stop("STOP: p4_run.log records the wrapper's end with rc=0 but the job record is missing or unreadable: "
                   "a finished job's record was lost or blanked; it is not sealed as a killed job (the author decides)")
    want = "probe" if spec.get("probe") is not None else "p4"
    kind = attempt_kind(src, record, launch)  # minor 2 of review round 1: a killed probe never enters the P.4 tree
    if kind is not None and kind != want:
        raise Stop(f"STOP: this is a {kind} attempt; it is not sealed with a {want} spec")
    if launch is not None:
        direct_launch_matches(launch, spec, arm, want, record)
    if kind is None and not unknown_kind_confirmed:
        raise Stop("STOP: neither the job record nor p4_run.log shows whether this is a probe or a P.4 attempt; "
                   "seal it with --unknown-kind-confirmed (charged the larger of both walltimes)")
    for name in (spec["run_id"], arm):
        if not SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    arm_root = Path(sealed_root) / spec["run_id"] / arm
    if any(p.is_symlink() for p in [arm_root, *arm_root.parents] if p.exists()):
        raise Stop(f"STOP: {arm_root} has a symlink component")
    if record is not None and arm_root.is_dir():    # review round 5, nit: the same output is sealed once
        mine = _sha_file(src / "job_record.json")
        for att in sorted(arm_root.glob("attempt-*")):
            rp = att / "SEAL_RECEIPT.json"
            if rp.is_file() and (json.loads(_read_utf8(rp)).get("job_record_sha256") == mine):
                raise Stop(f"STOP: this job record is already sealed as {att.name}; the same output is sealed once")
    n = 1 + len([p for p in arm_root.glob("attempt-*")]) if arm_root.exists() else 1
    target = arm_root / f"attempt-{n}"
    if target.exists():
        raise Stop(f"STOP: {target} exists; no overwrite")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "p4_run.log", DIRECT_LAUNCH_FILE):
        if (src / name).exists():
            shutil.copy2(src / name, target / name)
    cls = rec_class if rec_class in (spec.get("hosts") or {}) else None
    verified = record is not None and cls is not None and \
        HOST_CLASSES[cls]["launch"] == ("direct" if launch is not None else "htcondor") and \
        (record.get("gpu") or {}).get("name") == HOST_CLASSES[cls]["gpu_name"] and \
        (record.get("gpu") or {}).get("compute_capability") == HOST_CLASSES[cls]["compute_capability"] and \
        launch_runtime_verified(launch, record, spec) and \
        (launch is None or launch.get("status") == "finished")
    hours = (record or {}).get("gpu_hours")
    wall_h = round(_requested_walltime_s(spec, arm) / 3600, 4)
    readable = isinstance(hours, (int, float)) and not isinstance(hours, bool) and hours >= 0
    direct = {}
    if launch is not None:                  # R1-HOST-FREE (5): GPU-hours of the leased card, whatever its model
        charged, basis, direct = direct_charge(launch, float(hours) if readable else None, wall_h, time.time())
        direct["direct_launch_sha256"] = _sha_file(target / DIRECT_LAUNCH_FILE)
    elif kind is None:                     # unknown kind, confirmed: at least the larger of both walltimes, even with
        wall_h = max(wall_h, round(PROBE["walltime_s"] / 3600, 4), round(arm_walltime_s(spec, arm) / 3600, 4))
        charged = max(float(hours) if readable else 0.0, wall_h)       # a readable record (review round 2, minor 1)
        basis = "job_record.gpu_hours" if charged == hours else \
            "max(job_record.gpu_hours, the larger walltime) (unknown kind, confirmed)"
    else:
        charged = float(hours) if readable else wall_h
        basis = "job_record.gpu_hours" if charged == hours else "requested walltime (no readable value)"
    no_record = (launch or {}).get("refusal") or "STOP: no readable job record"
    outcome = {"stop": (record or {}).get("stop", no_record),
               "stop_class": (record or {}).get("stop_class", "infrastructure"), **{
                   k: (record or {}).get(k) for k in ("card_processes_start", "card_processes_end")}}
    if unfinished_venv_launch(launch):
        outcome.update(stop=(launch.get("refusal") or "STOP: the native launcher did not finish"),
                       stop_class="infrastructure")
    if launch is not None:                  # R1-CARD-SHARE (3), (4): the launcher's host-side counts of the card
        direct.update(other_processes_start=launch.get("other_processes_start"),
                      other_processes_end=launch.get("other_processes_end"), card_shared=launch.get("card_shared"))
        shared_card_loss(outcome, launch.get("other_processes_start"), launch.get("other_processes_end"))
    if spec["run_id"] == ADA_REPROBE["run_id"] and outcome["stop_class"] in (None, "arm") and any(
            (direct.get(key) or {}).get("count") != 0 for key in ("other_processes_start", "other_processes_end")):
        outcome.update(stop="STOP: the Ada 4B re-probe lacks host-side evidence of an empty card",
                       stop_class="infrastructure")
    receipt = {"schema": RECEIPT_SCHEMA, "run_id": spec["run_id"], "arm": arm, "attempt": n,
               "sealed_path": str(target), "record_readable": record is not None, "sums": sums,
               "identity_verified": verified, "stop": outcome["stop"],
               "stop_class": outcome["stop_class"],
               **({"lost_beside_another_process": True}
                  if outcome.get("lost_beside_another_process") or (record or {}).get("lost_beside_another_process")
                  else {}),
               "charged_gpu_hours": charged, "kind": kind or "unknown (confirmed)",
               "charge_basis": basis,
               "launch": "direct" if launch is not None else "htcondor", "host_class": rec_class,
               "job_record_sha256": _sha_file(target / "job_record.json") if (target / "job_record.json").is_file()
               else None,
               "run_log_sha256": _sha_file(target / "p4_run.log") if (target / "p4_run.log").is_file() else None,
               **direct,
               "source_dir": str(src), "sealed_utc": _utc()}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def seal_threshold(spec: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """R1-NO-TIMEOUT (3) at seal: the run's charged GPU-hours after this seal (every sealed attempt, pending
    submissions, the probes' charge) against the 40 GPU-h figure; ``report_to_author`` when reached. Printed by the
    ``seal`` CLI; never a refusal (a run whose tree cannot be counted is reported as such)."""
    try:
        charged = charged_hours(spec, sealed_root)
        out = threshold_report(projection(spec), charged["total"])
    except (Stop, KeyError, TypeError, ValueError) as exc:
        return {"error": f"the charge could not be counted: {exc}"}
    if out["report_to_author"]:
        print(f"REPORT TO THE AUTHOR: {charged['total']} GPU-h charged in {spec['run_id']} reaches the P4-CAP figure "
              f"{spec['caps']['gpu_hours']} GPU-h (R1-NO-TIMEOUT (3): reported, not refused)", file=sys.stderr)
    return out


def read_direct_launch(src: Path) -> dict | None:
    """The direct launcher's record beside the outputs (``direct_launch.json``, ``trackp_p4_direct_launch/1``), or None
    when the attempt has none (an HTCondor attempt). A file that is there but is not such a record (a symlink, not
    UTF-8 JSON, another schema) is a STOP: the launcher writes it atomically, so a broken one is not a kill."""
    p = Path(src) / DIRECT_LAUNCH_FILE
    if not p.exists() and not p.is_symlink():
        return None
    if p.is_symlink() or not p.is_file():
        raise Stop(f"STOP: {p} is not a regular file")
    try:
        doc = json.loads(_read_utf8(p))
    except (ValueError, Stop):
        raise Stop(f"STOP: {p} is not a readable launcher record (the author decides)") from None
    if not isinstance(doc, dict) or doc.get("schema") != DIRECT_LAUNCH_SCHEMA or doc.get("label") != ENGINEERING_ONLY:
        raise Stop(f"STOP: {p} is not a {DIRECT_LAUNCH_SCHEMA} ENGINEERING_ONLY record")
    return doc


def direct_launch_matches(launch: dict, spec: dict, arm: str, kind: str, record: dict | None) -> None:
    """A direct launcher record belongs to this attempt (``seal``): this run, arm and kind (``job`` for a P.4 spec,
    ``probe`` for a probe spec), a direct class the spec admits (for a probe spec, the spec's ``host_class``), the
    spec's image digest; and a readable job record names the same class and runs on the leased card (its GPU UUID is
    the launcher's), else a STOP."""
    cls = launch.get("host_class")
    want_mode = "probe" if kind == "probe" else "job"
    bad = []
    if launch.get("run_id") != spec["run_id"] or launch.get("arm") != arm:
        bad.append("run_id/arm")
    if launch.get("mode") != want_mode:
        bad.append(f"mode (not {want_mode})")
    if cls not in (spec.get("hosts") or {}) or HOST_CLASSES[cls]["launch"] != "direct":
        bad.append(f"host_class {cls!r} (not a direct class the spec admits)")
    elif kind == "probe" and cls != spec.get("host_class"):
        bad.append(f"host_class {cls} (the probe spec measures {spec.get('host_class')})")
    if launch.get("image_digest") != spec["image"]["digest"]:
        bad.append("image_digest")
    uuid = (launch.get("gpu") or {}).get("uuid")
    if not isinstance(uuid, str) or not uuid.startswith("GPU-"):
        bad.append("gpu.uuid")
    if record is not None:
        if record.get("host_class") != cls:
            bad.append(f"job record host_class {record.get('host_class')!r}")
        if record.get("gpu") is not None and (record.get("gpu") or {}).get("uuid") != uuid:
            bad.append("job record GPU uuid is not the leased card's")
        if record.get("venv") and record["venv"] != launch.get("venv"):
            bad.append("job record venv path and version differ from the launcher")
        if launch.get("runtime") == "venv" and not record.get("stop") and \
                not launch_runtime_verified(launch, record, spec):
            bad.append("job record venv identity")
    if bad:
        raise Stop(f"STOP: {DIRECT_LAUNCH_FILE} does not belong to this attempt: {bad}")


def launch_runtime_verified(launch: dict | None, record: dict, spec: dict) -> bool:
    if (launch or {}).get("runtime") != "venv":
        return (record.get("image") or {}).get("digest") == spec["image"]["digest"]
    venv = record.get("venv")
    freeze = record.get("env3_freeze") or {}
    return (record.get("host_class") == "ada_rtx6000" and record.get("image") is None and
            launch.get("image_executed") is False and isinstance(venv, dict) and venv == launch.get("venv") and
            freeze.get("status") == "identical" and freeze.get("pinned_sha256") == ENV3_FREEZE_SHA256 and
            freeze.get("sha256_sorted") == ENV3_FREEZE_SORTED_SHA256 and
            re.fullmatch(r"[0-9a-f]{64}", str(freeze.get("venv_freeze_sha256"))) is not None)


def _utc_epoch(text) -> float | None:
    """Seconds since the epoch of a ``YYYY-MM-DDTHH:MM:SSZ`` stamp (``_utc``'s form), or None."""
    try:
        return float(calendar.timegm(time.strptime(str(text), "%Y-%m-%dT%H:%M:%SZ")))
    except (TypeError, ValueError, OverflowError):
        return None


def unfinished_venv_launch(launch: dict | None) -> bool:
    return bool(launch and launch.get("runtime") == "venv" and launch.get("status") != "finished")


def direct_charge(launch: dict, record_hours: float | None, walltime_h: float, now: float) -> tuple:
    """(charged GPU-hours, basis, receipt fields) of a direct attempt (``seal``; R1-HOST-FREE (5), P4-CAP A,
    P4-PROBECAP A): one card, so GPU-hours = the launcher's ``wall_clock_s`` / 3600 (the lease span), or the record's
    ``gpu_hours`` if larger. An incomplete launcher record (no end, wall clock or exit code: the launcher was killed)
    and an unfinished native launch use the largest of launch start to ``now`` (the seal), ``walltime_h`` and the
    record's hours. A record without
    a readable ``started_utc`` cannot be bounded and is a STOP."""
    wall = launch.get("wall_clock_s")
    complete = not unfinished_venv_launch(launch) and \
        isinstance(wall, (int, float)) and not isinstance(wall, bool) and 0 <= wall <= 30 * 86400 and \
        isinstance(launch.get("exit_code"), int) and not isinstance(launch.get("exit_code"), bool) and \
        _utc_epoch(launch.get("ended_utc")) is not None
    fields = {"direct_launch_sha256": None, "launcher_status": launch.get("status"),
              "launcher_wall_clock_s": wall if complete else None, "launcher_exit_code": launch.get("exit_code"),
              "gpu_uuid": (launch.get("gpu") or {}).get("uuid"),
              "stage_manifest_sha256": (launch.get("stage") or {}).get("manifest_sha256")}
    if complete:
        charged = round(max(float(wall) / 3600, record_hours or 0.0), 4)
        basis = "max(direct launcher wall clock, job_record.gpu_hours)"
    else:
        start = _utc_epoch(launch.get("started_utc"))
        if start is None:
            raise Stop(f"STOP: {DIRECT_LAUNCH_FILE} has no readable started_utc: its GPU time cannot be bounded")
        span = max(0.0, now - start) / 3600
        charged = round(max(span, walltime_h, record_hours or 0.0), 4)
        basis = "incomplete launcher record: max(launch start to seal, requested walltime, job_record.gpu_hours)"
    return charged, basis, fields


def _requested_walltime_s(spec: dict, arm: str) -> int:
    """The walltime a job of ``arm`` requests: the probe's fixed ``probe.walltime_s`` for a probe spec, else the
    arm's projected walltime (``arm_walltime_s``)."""
    if spec.get("probe") is not None:
        return int(spec["probe"]["walltime_s"])
    return arm_walltime_s(spec, arm)


def charged_hours(spec: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """GPU-hours charged to P4-CAP by every sealed attempt of the run, per arm and in total (each attempt's receipt;
    an attempt directory without a receipt is a STOP: seal it first), plus, in ``total``, the probe's charged GPU-hours
    ``caps.probe_gpu_hours`` (P4-PROBECAP A; ``probe``, 0 while a placeholder)."""
    root = Path(sealed_root) / spec["run_id"]
    per, attempts = {}, []
    for arm_dir in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        for att in sorted(arm_dir.glob("attempt-*")):
            rp = att / "SEAL_RECEIPT.json"
            if not rp.is_file():
                raise Stop(f"STOP: {att} has no SEAL_RECEIPT.json; seal every attempt before counting the cap")
            r = json.loads(_read_utf8(rp))
            h = float(r.get("charged_gpu_hours") or 0)
            per[arm_dir.name] = round(per.get(arm_dir.name, 0.0) + h, 4)
            attempts.append({"arm": arm_dir.name, "attempt": att.name, "charged_gpu_hours": h,
                             "stop": r.get("stop"), **({"launch": "direct"} if r.get("launch") == "direct" else {})})
    pending = pending_submissions(spec, sealed_root, attempts)
    for p in pending:
        per[p["arm"]] = round(per.get(p["arm"], 0.0) + p["charged_gpu_hours"], 4)
    probe = probe_gpu_hours(spec) or 0.0
    return {"per_arm": per, "probe": probe, "total": round(sum(per.values()) + probe, 4), "attempts": attempts,
            "pending": pending}


SUBMISSION_LEDGER = "_submissions.jsonl"


def read_ledger(ledger: Path) -> list[dict]:
    """The submission ledger's entries in order; a line that is not a JSON object with a string ``arm`` (for example a
    line cut mid-write) is a STOP (review round 4, nit)."""
    out = []
    if not Path(ledger).is_file():
        return out
    for n, line in enumerate(_read_utf8(ledger).splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            raise Stop(f"STOP: {ledger}:{n} is not a JSON line (cut mid-write?); repair the ledger by hand") from None
        if not isinstance(entry, dict) or not isinstance(entry.get("arm"), str):
            raise Stop(f"STOP: {ledger}:{n} is not a submission entry with an arm")
        out.append(entry)
    return out


def pending_submissions(spec: dict, sealed_root: Path, attempts: list[dict]) -> list[dict]:
    """Submissions recorded in the run's ledger (``<sealed_root>/<run_id>/_submissions.jsonl``, appended by the switch,
    or by ``p4_render_jdl.stage_probe`` for a probe run) that have no sealed attempt yet, each charged at the requested
    walltime (``_requested_walltime_s``: the probe's ``walltime_s`` for a probe run; a running or lost job counts)."""
    subs = read_ledger(Path(sealed_root) / spec["run_id"] / SUBMISSION_LEDGER)
    out = []
    for arm in sorted({s["arm"] for s in subs}):
        n = sum(1 for s in subs if s["arm"] == arm) - sum(1 for a in attempts if a["arm"] == arm)
        out += [{"arm": arm, "charged_gpu_hours": round(_requested_walltime_s(spec, arm) / 3600, 4),
                 "basis": "submitted, not sealed: requested walltime"}] * max(0, n)
    return out


def comparable(rec: dict) -> dict:
    """What every job of the table must share, without job-local paths (the job directory differs per job). The host
    config is shared per host class (``host_config[<class>]``): jobs of one class must agree, jobs of two classes
    carry their own class's config (R1-HOST-FREE; each job checked its class's sha256 against the spec)."""
    return {"paper_commit": rec.get("paper_commit"), "image": rec.get("image"),
            **({"venv": rec["venv"]} if rec.get("venv") else {}),
            "configs": {"sft_config": rec["configs"]["sft_config"]},
            f"host_config[{rec.get('host_class')}]": rec["configs"]["host_config"],
            "data": (rec.get("data") or {}).get("identity"),
            "labels": {k: v for k, v in (rec["inputs"]["labels"]).items() if k != "partition"},
            "env3_status": {k: rec["env3_freeze"].get(k) for k in ("status", "image_line", "pinned_line",
                                                                   "local_label")},
            "protocol": rec.get("protocol"),
            "tokenizers": {n: {f: v["sha256"] for f, v in t["files"].items()}            # review round 1, n4
                           for n, t in (((rec.get("staging") or {}).get("tokenizers") or {}).get("pool")
                                        or {}).items()}}


def assemble(sealed: list[Path], spec: dict, spec_file_sha256: str, sealed_root: Path = SEALED_ROOT) -> dict:
    """One sealed, STOP-free attempt per arm (and no other STOP-free attempt of that arm: no choosing among
    attempts); in every job the same spec, paper commit, image, env3 freeze status, configs, labels (without the
    job-local partition path) and data identity (``data_identity``: path-free); GPU-hours summed over every sealed
    attempt of the run plus the probe's (``charged_hours``) against the cap, HTCondor and direct attempts alike
    (R1-HOST-FREE (5)).

    R1-HOST-FREE: the GPU model is recorded, not fixed. Each arm's job names its host class, and its one card (GPU
    model, UUID, driver) is recorded per arm in ``jobs``; ``gpu_models`` and ``mixed_gpu_models`` show whether the
    arms ran on more than one model. One arm's training run stays on one card: the arm's assembled attempt must name an
    admitted class and carry exactly that class's GPU, and a direct attempt's record must be on the card its launcher
    leased (the receipt's ``gpu_uuid``); anything else is a STOP."""
    jobs, keys = {}, {}
    charged = charged_hours(spec, sealed_root)
    listed = {(a["arm"], a["attempt"]) for a in charged["attempts"]}
    run_root = (Path(sealed_root) / spec["run_id"]).resolve()
    for d in map(Path, sealed):
        if d.resolve().parent.parent != run_root or not re.fullmatch(r"attempt-[1-9][0-9]*", d.name) or \
                (d.parent.name, d.name) not in listed:
            raise Stop(f"STOP: {d} is not a sealed attempt under {run_root}/<arm>/attempt-N (the cap counts that tree)")
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=d, capture_output=True).returncode != 0:
            raise Stop(f"STOP: {d} does not verify against its SHA256SUMS")
        rec = json.loads(_read_utf8(d / "job_record.json"))
        receipt = json.loads(_read_utf8(d / "SEAL_RECEIPT.json"))
        if receipt.get("job_record_sha256") != _sha_file(d / "job_record.json") or rec.get("stop") or \
                rec.get("spec_sha256") != spec_file_sha256 or rec.get("run_id") != spec["run_id"] or \
                receipt.get("identity_verified") is not True:
            raise Stop(f"STOP: {d} is not a sealed, verified, STOP-free attempt of this run and spec")
        if rec["arm"] in jobs:
            raise Stop(f"STOP: two attempts given for {rec['arm']}")
        for other in sorted(d.parent.glob("attempt-*")):
            if other.resolve() == d.resolve():
                continue
            o = json.loads(_read_utf8(other / "SEAL_RECEIPT.json")) if (other / "SEAL_RECEIPT.json").is_file() \
                else {}
            if not o.get("stop"):
                raise Stop(f"STOP: {rec['arm']} has another STOP-free attempt {other.name}: one attempt per arm, "
                           "never chosen by result")
        cls, gpu = rec.get("host_class"), rec.get("gpu") or {}
        if cls not in (spec.get("hosts") or {}) or gpu.get("name") != HOST_CLASSES[cls]["gpu_name"] or \
                not isinstance(gpu.get("uuid"), str) or \
                (receipt.get("launch") == "direct" and receipt.get("gpu_uuid") != gpu.get("uuid")):
            raise Stop(f"STOP: {d}: one arm's run stays on one card of its admitted class; the record names class "
                       f"{cls!r}, GPU {gpu.get('name')!r} ({gpu.get('uuid')!r}), receipt card {receipt.get('gpu_uuid')!r}")
        jobs[rec["arm"]] = {"sealed": str(d), "job_record_sha256": receipt["job_record_sha256"],
                            "selected_lr": (rec.get("select") or {}).get("selected_lr"),
                            "gpu_hours": rec.get("gpu_hours"), "env3_freeze": rec.get("env3_freeze"),
                            "host_class": cls, "launch": receipt.get("launch", "htcondor"),
                            "hostname": (rec.get("host") or {}).get("hostname"),
                            "gpu": {k: gpu.get(k) for k in ("name", "uuid", "driver", "compute_capability")}}
        for k, v in comparable(rec).items():
            keys.setdefault(k, set()).add(json.dumps(v, sort_keys=True))
    if set(jobs) != set(spec["arms"]):
        raise Stop(f"STOP: the assembly needs every arm {spec['arms']}; got {sorted(jobs)}")
    differ = sorted(k for k, v in keys.items() if len(v) != 1)
    if differ:
        raise Stop(f"STOP: the jobs differ in {differ} (one table: one data directory, image and config)")
    if json.loads(next(iter(keys["data"]))) is None:
        raise Stop("STOP: the job records carry no data identity")
    ledger = check_probe_ledger(spec, sealed_root)       # M1: the spec's probe charge and charge files = the sealed tree
    threshold = threshold_report(projection(spec), charged["total"])    # R1-NO-TIMEOUT (3): reported, never refused
    return {"schema": ASSEMBLY_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "jobs": jobs,
            "gpu_hours_consumed": charged["total"], "gpu_hours_probe": charged["probe"], "probe_ledger": ledger,
            "threshold": threshold,
            "gpu_hours_by_attempt": charged["attempts"],
            "gpu_models": {a: j["gpu"]["name"] for a, j in sorted(jobs.items())},
            "mixed_gpu_models": len({j["gpu"]["name"] for j in jobs.values()}) > 1,
            "data_identity": json.loads(next(iter(keys["data"]))),
            "env3_freeze": json.loads(next(iter(keys["env3_status"])))}


# =============================================================================================== launch binding
SYS_PATH_DIRS = ("r1/scripts/htcondor/trackp_p4",)


def _repo_id(url: str) -> str:
    """owner/name of a GitHub remote, however it is spelled (https, ssh, scp form, with or without .git)."""
    u = re.sub(r"\.git$", "", str(url).strip().rstrip("/"))
    u = re.sub(r"^(?:https?://|ssh://git@|git@)github\.com[:/]", "", u)
    return u.lower()
CODE_SUFFIXES = (".py", ".pyc", ".pyo", ".sh", ".pth", ".so")


def verify_launch_p4(repo: Path, spec: dict, rows: tuple[str, ...], *, spec_path: Path, git=_git) -> dict:
    """The launch binding on the submit host (as ``g1b_tasl.verify_launch_tasl``): ``origin`` freshly fetched
    (``ls-remote`` equals the local ``origin/main``); the submit checkout tracked-clean, with no untracked code outside
    ``docs/``, and published (an ancestor of ``origin/main``); the spec file is ``HEAD``'s committed file; the spec's
    paper commit (which the job clones and the note names) is an ancestor of ``HEAD`` whose tree equals ``HEAD``'s
    outside ``docs/`` and that spec file; the PLAN rows on ``origin/main``."""
    commit = (spec.get("paper") or {}).get("commit")
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        raise Stop("STOP: the spec must pin the full paper commit")
    url = git(repo, "remote", "get-url", "origin").stdout.strip()      # as git resolves it (insteadOf applied)
    if _repo_id(url) != _repo_id((spec.get("paper") or {}).get("repo", "")):
        raise Stop(f"STOP: origin ({url or 'unset'}) is not the spec's paper repository")
    remote, local = git(repo, "ls-remote", "origin", "refs/heads/main"), git(repo, "rev-parse", "origin/main")
    if remote.returncode or local.returncode or remote.stdout.split() != [local.stdout.strip(), "refs/heads/main"]:
        raise Stop("STOP: fetch published main before launch; local origin/main differs or could not be verified")
    main = local.stdout.strip()
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    if git(repo, "status", "--porcelain", "-uno").stdout:
        raise Stop("STOP: the launch checkout must be tracked-clean")
    stray = [f for f in git(repo, "ls-files", "--others", "--exclude-standard", "--", ".", ":(exclude)docs/").stdout
             .splitlines() if f.endswith(CODE_SUFFIXES)]
    stray += [f for f in git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "--",
                              *SYS_PATH_DIRS).stdout.splitlines()
              if f.endswith(CODE_SUFFIXES) and "/__pycache__/" not in f]
    if stray:
        raise Stop(f"STOP: untracked code files in the launch checkout: {stray[:5]}")
    if git(repo, "merge-base", "--is-ancestor", head, main).returncode:
        raise Stop("STOP: the launch checkout (HEAD) must be published: an ancestor of the freshly fetched origin/main")
    try:
        rel = Path(spec_path).resolve().relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        raise Stop("STOP: the launch spec must be the spec file committed in the repository") from None
    shown = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{rel}"], capture_output=True)
    if shown.returncode or shown.stdout != Path(spec_path).read_bytes():
        raise Stop(f"STOP: the launch spec is not the committed {rel} of HEAD")
    if git(repo, "merge-base", "--is-ancestor", commit, head).returncode:
        raise Stop("STOP: the paper commit must be an ancestor of the launch checkout")
    if git(repo, "diff", "--quiet", commit, head, "--", ".", ":(exclude)docs/", f":(exclude,literal){rel}").returncode:
        raise Stop(f"STOP: the launch checkout differs from the paper commit outside docs/ and {rel}")
    plan = git(repo, "show", "origin/main:docs/r1/PLAN.md").stdout
    for row in rows:
        if not re.search(rf"^\| {re.escape(row)} \|", plan, re.M):
            raise Stop(f"STOP: the PLAN row {row} is not on published main")
    return {"paper_commit": commit, "head": head, "main": main, "spec": rel}


# =============================================================================================== CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    v.add_argument("--probe", action="store_true", help="probe strength (validate_probe_spec) instead")
    j = sub.add_parser("job"); j.add_argument("spec"); j.add_argument("--arm", required=True)
    j.add_argument("--host-class", required=True, choices=sorted(HOST_CLASSES),
                   help="the host class the job runs under (R1-HOST-FREE); its GPU must be that class's")
    p = sub.add_parser("probe", help="the SFT fit and timing probe of one base on one host class (P4-PROBE A)")
    p.add_argument("spec"); p.add_argument("--arm", required=True)
    p.add_argument("--host-class", required=True, choices=sorted(HOST_CLASSES),
                   help="the host class the job runs under; it must be the probe spec's host_class")
    r = sub.add_parser("probe-record", help="the probe record (§4.4) and hours (§4.5) from sealed probe attempts")
    r.add_argument("probe_spec"); r.add_argument("p4_spec"); r.add_argument("sealed", nargs="+")
    r.add_argument("--out", required=True, help="a new probe_records.json (never overwritten)")
    r.add_argument("--wallclock", required=True, type=Path,
                   help=f"{WALLCLOCK_SCHEMA} JSON: condor_history RemoteWallClockTime of every sealed probe attempt")
    t1g = r.add_mutually_exclusive_group()
    t1g.add_argument("--t1-wallclock", type=Path, default=None,
                     help=f"P4-T1CHARGE A: {T1_WALLCLOCK_SCHEMA} JSON, every T1 job's ClusterId and condor_history "
                          f"RemoteWallClockTime, for the pinned record {T1_RECORD_DIR}; it must agree with the "
                          f"committed {T1_HISTORY} there (no JSON-only route)")
    t1g.add_argument("--t1-history", action="store_true",
                     help=f"P4-T1CHARGE A: build T1's entry from {T1_RECORD_DIR}/{T1_HISTORY}. One of the two is "
                          "required for the first record; a rebuilt record takes T1 from the base charge file, and "
                          "giving it again is a STOP")
    q = sub.add_parser("probe-charge", help="round 3: a write-once supplementary charge file for attempts sealed into "
                                            "a probe run after its record")
    q.add_argument("run_id"); q.add_argument("--wallclock", required=True, type=Path)
    z = sub.add_parser("seal"); z.add_argument("job_output"); z.add_argument("spec"); z.add_argument("--arm", required=True)
    z.add_argument("--unknown-kind-confirmed", action="store_true",
                   help="seal an attempt whose record and log do not show its kind (charged the larger walltime)")
    a = sub.add_parser("assemble"); a.add_argument("spec"); a.add_argument("sealed", nargs="+")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "validate" and args.probe:
            if args.launch:
                raise Stop("STOP: --probe and --launch are two different strengths")
            loaded = validate_probe_spec(load_spec(Path(args.spec)))
            print(json.dumps({"ok": True, "strength": "probe", "run_id": loaded["run_id"], "probe": loaded["probe"]},
                             indent=1))
        elif args.cmd == "validate":
            loaded = validate_spec(load_spec(Path(args.spec)), launch=args.launch)
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"],
                              "threshold": loaded["threshold"]}, indent=1))
        elif args.cmd == "probe":
            rec = run_probe(Path(args.spec), args.arm, host_class=args.host_class)
            print(json.dumps({"ok": True, "arm": args.arm, "memory": rec["memory"],
                              "s_per_step_wall": rec["run"]["s_per_step_wall"]}, indent=1))
        elif args.cmd == "probe-charge":
            print(json.dumps(supplement_charges(args.run_id, json.loads(_read_utf8(args.wallclock)), SEALED_ROOT),
                             indent=1))
        elif args.cmd == "probe-record":
            out = Path(args.out)
            if out.exists():
                raise Stop(f"STOP: {out} exists (written once)")
            table = probe_records(load_spec(Path(args.probe_spec)), _sha_file(Path(args.probe_spec)),
                                  load_spec(Path(args.p4_spec)), [Path(x) for x in args.sealed], SEALED_ROOT,
                                  wallclock=json.loads(_read_utf8(args.wallclock)),
                                  t1_wallclock=T1_FROM_HISTORY if args.t1_history else
                                  json.loads(_read_utf8(args.t1_wallclock)) if args.t1_wallclock else None)
            if table["probe_charges"]["unrecorded"]:
                raise Stop(f"STOP: attempts without a wall clock: {table['probe_charges']['unrecorded'][:5]}")
            docs = table.pop("charge_file_docs")
            write_charge_files(docs, SEALED_ROOT)        # once, before probe_records.json (round 2, M1; see the report)
            listing = charge_file_listing(SEALED_ROOT)
            table["charge_files"] = listing
            table["spec_probe_charge_files"] = spec_charge_files(listing)   # the value of caps.probe_charge_files
            table["lines"] += [f"p4_probe_charge_file: {run} {f['file']} {f['sha256']}"
                               for run, files in listing.items() for f in files]
            out.write_text(json.dumps(table, indent=1, sort_keys=True) + "\n")
            print("\n".join(table["lines"]))
            print(json.dumps({"out": str(out), "sha256": _sha_file(out), "projection": table["projection"],
                              "probe_over_2_gpu_h": table["probe_over_2_gpu_h"],
                              "headroom_below_15pct": table["headroom_below_15pct"]}, indent=1), file=sys.stderr)
        elif args.cmd == "job":
            rec = run_job(Path(args.spec), args.arm, host_class=args.host_class)
            print(json.dumps({"ok": True, "arm": args.arm, "selected_lr": rec["select"]["selected_lr"]}, indent=1))
        elif args.cmd == "seal":
            spec = load_spec(Path(args.spec))
            receipt = seal(Path(args.job_output), spec, args.arm, unknown_kind_confirmed=args.unknown_kind_confirmed)
            print(json.dumps(receipt, indent=1))
            print(json.dumps({"threshold": seal_threshold(spec)}, indent=1), file=sys.stderr)
        else:
            print(json.dumps(assemble([Path(x) for x in args.sealed], load_spec(Path(args.spec)),
                                      _sha_file(Path(args.spec))), indent=1))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except FileExistsError as exc:              # a write-once file (a charge file) exists: never overwritten
        print(f"STOP: {exc.filename} exists (written once)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
