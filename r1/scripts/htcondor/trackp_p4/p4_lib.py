"""Track P P.4 phase 1 on NEMO2 H200 (HTCondor, image v2.2): the job of P4-JOB A, one job per base. ENGINEERING_ONLY;
AI-assisted (Claude).

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
   is an NVIDIA H200 (``nvidia-smi``), a non-root uid.
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

**Cap** (P4-CAP A): the projection (per arm: the spec's estimate, which must come from the H200 SFT probe at
launch, × the wall factor + startup) must stay within 40 GPU-h, and the requested walltime within 64 slot-hours and
86,400 s per job. The GPU-hours consumed are summed over **every** sealed attempt of the run (``charged_hours``: the
record's ``gpu_hours``, or the arm's requested walltime when the record has none): ``assemble`` refuses a total over
the cap, and the switch refuses a repeat whose projection would pass it. **P4-PROBECAP A**: the H200 SFT probe's
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
HOST_CONFIG = "r1/scripts/configs/trackp_htcondor_v2.json"
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
LR_GRID = (1e-05, 3e-05, 0.0001)                # R1-LR-GRID
SEEDS = (0, 1, 2)
LC_POINTS = (250, 500)                          # P4-LC A
MICRO_BATCH = 8                                 # P4-MB A
CAP_GPU_HOURS = 40.0                            # P4-CAP A
CAP_SLOT_HOURS = 64.0                           # 1.6 x the cap
MAX_WALLTIME_S = 86400
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-TRACKP-P4-DECISIONS", "R1-TRACKP-P4-RUNNER-DECISIONS", "R1-TRACKP-IMAGE-V21",
             "R1-TRACKP-IMAGE-V22", "R1-TRACKP-IMAGE-V22-B", "R1-TRACKP-V21-FREEZE", "R1-HTC-QTORCH",
             "R1-S2-LABELS-TRAINDEV-RELEASE", "R1-TRACKP-SFT-DEV", "R1-SWEEP2-PREREG")
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
PROBE_RECORD_SCHEMA = "trackp_p4_probe_record/1"
PROBE_TABLE_SCHEMA = "trackp_p4_h200_sft_probe/1"
PROBE = {"steps": 50, "lr": 1e-05, "seed": 0, "sample_ms": 500, "walltime_s": 7200, "labels": "synthetic"}
PROBE_FILLED = (("paper", "commit"), ("image", "versions_sha256"), ("host_config", "sha256"))
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


def arm_hours(spec: dict, arm: str) -> float:
    return float(spec["estimate"]["hours"][arm])


def arm_walltime_s(spec: dict, arm: str) -> int:
    lay = spec["layout"]
    return int(math.ceil(arm_hours(spec, arm) * 3600 * float(lay["wall_factor"]) + float(lay["startup_s"])))


def probe_gpu_hours(spec: dict) -> float | None:
    """P4-PROBECAP A: the GPU-hours the H200 SFT probe already charged to the cap (``caps.probe_gpu_hours``), or None
    while it is a placeholder (launch validation requires the number)."""
    v = (spec.get("caps") or {}).get("probe_gpu_hours")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def projection(spec: dict) -> dict:
    """The four jobs' projected GPU-hours and slot-hours; ``within_cap`` adds the probe's charged GPU-hours
    (P4-PROBECAP A; 0 while ``caps.probe_gpu_hours`` is a placeholder, which only default-strength validation admits)."""
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
    """Fail-closed; ``launch=True`` refuses every placeholder (the image VERSIONS sha256, the host
    config sha256 after its fill, the partition, receipt and freeze-record sha256, the probe-based estimate, the
    probe's charged GPU-hours ``caps.probe_gpu_hours``) and refuses a probe spec (one with a ``probe`` block)."""
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
    if spec.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: gpu_model must be {GPU_MODEL} (R1-T1-HOST-TASL)")
    env3 = spec.get("env3") or {}
    want_env3 = {"python": ENV3_PYTHON, "freeze": ENV3_FREEZE, "freeze_sha256": ENV3_FREEZE_SHA256,
                 "rule": "R1-TRACKP-V21-FREEZE"}
    if {k: env3.get(k) for k in want_env3} != want_env3:
        raise Stop(f"STOP: env3 must be {want_env3} (R1-ENV-PIN, R1-HTC-QTORCH, R1-TRACKP-V21-FREEZE)")
    for key, path in (("host_config", HOST_CONFIG), ("sft_config", SFT_CONFIG)):
        block = spec.get(key) or {}
        if block.get("path") != path:
            raise Stop(f"STOP: {key}.path must be {path}")
        _pin(block.get("sha256"), f"{key}.sha256", allow=allow and key == "host_config")
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
    caps = spec.get("caps") or {}
    if caps.get("gpu_hours") != CAP_GPU_HOURS or caps.get("slot_hours") != CAP_SLOT_HOURS:
        raise Stop(f"STOP: caps must be {CAP_GPU_HOURS} GPU-h and {CAP_SLOT_HOURS} slot-hours (P4-CAP A)")
    pg = caps.get("probe_gpu_hours")
    number = isinstance(pg, (int, float)) and not isinstance(pg, bool)
    if launch and not (number and 0 < pg <= CAP_GPU_HOURS and round(pg, 2) == pg):
        raise Stop("STOP: caps.probe_gpu_hours must be the H200 SFT probe's charged GPU-hours (the probe record's "
                   "p4_probe_gpu_hours: line), in (0, 40] with at most two decimals, before launch (P4-PROBECAP A)")
    if not launch and not (_placeholder(pg) or (number and 0 <= pg <= CAP_GPU_HOURS)):
        raise Stop("STOP: caps.probe_gpu_hours must be a placeholder or GPU-hours in [0, 40] (P4-PROBECAP A)")
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
    est = spec.get("estimate") or {}
    hours = est.get("hours") or {}
    if set(hours) != set(arms) or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v <= 20
                                      for v in hours.values()):
        raise Stop("STOP: estimate.hours must give (0, 20] GPU-hours of training for every arm")
    source = str(est.get("source", ""))
    if launch and not re.fullmatch(r"h200_sft_probe: docs/r1/reports/\S+\.md", source):
        raise Stop("STOP: estimate.source must be 'h200_sft_probe: docs/r1/reports/<record>.md' before launch (P5; "
                   "P4-CAP A)")
    proj = projection(spec)
    for arm, v in proj["per_arm"].items():
        if v["walltime_s"] > MAX_WALLTIME_S:
            raise Stop(f"STOP: {arm} would request {v['walltime_s']} s, over {MAX_WALLTIME_S} s (one HTCondor job)")
    if not proj["within_cap"]:
        raise Stop(f"STOP: the projection {proj['total_gpu_hours']} GPU-h (with the probe's charged "
                   f"{proj['probe_gpu_hours'] or 0.0}: {proj['total_with_probe_gpu_hours']}) / "
                   f"{proj['total_slot_hours']} slot-h exceeds P4-CAP: author STOP")
    return {"spec": spec, "run_id": run_id, "projection": proj}


# =============================================================================================== helpers
def _sh(argv, *, cwd=None, env=None, timeout=3600) -> subprocess.CompletedProcess:
    return subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)       # UTF-8 whatever the locale; never a decode error


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


def gpu_identity(sh=_sh) -> dict:
    res = sh(["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,compute_cap",
              "--format=csv,noheader"], timeout=120)
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi failed: {res.stderr.strip()[:200]}")
    gpus = [[x.strip() for x in line.split(",")] for line in res.stdout.strip().splitlines() if line.strip()]
    if len(gpus) != 1:
        raise Stop(f"STOP: one GPU per P.4 job, nvidia-smi lists {len(gpus)}")
    name, uuid, driver, memory, cap = gpus[0]
    if name != GPU_MODEL:
        raise Stop(f"STOP: landed on {name}, not {GPU_MODEL} (no run moves to another GPU model)")
    return {"name": name, "uuid": uuid, "driver": driver, "memory_total": memory, "compute_capability": cap}


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
    res = sh([UV, "pip", "freeze", "--python", ENV3_PYTHON], timeout=600)
    if res.returncode != 0:
        raise Stop(f"STOP: uv pip freeze of env3 failed: {res.stderr.strip()[:200]}")
    try:
        return {**_phase1(clone).check_env3_freeze(res.stdout, _read_utf8(pinned)), "pinned_sha256": ENV3_FREEZE_SHA256,
                "image_freeze_sha256": hashlib.sha256(res.stdout.encode()).hexdigest()}
    except Exception as exc:         # P4Stop of the clone's module
        if str(exc).startswith("STOP"):
            raise Stop(str(exc)) from None
        raise


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


def configs(spec: dict, clone: Path, sh=_sh) -> dict:
    """Step 4."""
    out = {}
    for key in ("host_config", "sft_config"):
        path = clone / spec[key]["path"]
        got = _sha_file(path)
        if got != spec[key]["sha256"]:
            raise Stop(f"STOP: {spec[key]['path']} sha256 {got} is not the spec's {spec[key]['sha256']}")
        out[key] = {"path": spec[key]["path"], "sha256": got}
    res = sh([ENV3_PYTHON, "-B", str(clone / TRACKP_SCRIPT), "--config", str(clone / HOST_CONFIG), "--check-config"],
             cwd=clone, timeout=600)
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
    """Step 6 (the one network step): the arm's registry weights, checked by size and sha256 against the clone's
    ``registry.yaml``, and the pool tokenizers into ``HF_HOME``."""
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
    res = sh([ENV3_PYTHON, "-B", "-c", "from r1.c3.train import serialize as S\n"
              "for n in S.POOL: S.load_tokenizer(n)\nprint(len(S.POOL))"], cwd=clone, env=env, timeout=3600)
    if res.returncode != 0:
        raise Stop(f"STOP: staging the pool tokenizers failed: {res.stderr.strip()[-300:]}")
    return {"weights": staged, "tokenizers": res.stdout.strip()}


def check_local_paths(arm: str, clone: Path, job_dir: Path) -> dict:
    """The host config must point the arm at the staged directories (paths relative to the job directory)."""
    cfg = json.loads(_read_utf8(clone / HOST_CONFIG))
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
    argv = [ENV3_PYTHON, "-B", str(clone / TRACKP_SCRIPT), "--config", str(clone / HOST_CONFIG), *map(str, args)]
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


def check_run_protocol(run_dir: Path, sft_cfg: dict, *, lr: float, seed: int, data_sha256: str | None = None) -> dict:
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
    return {k: proto.get(k) for k in want}


def sft_dev_argv(arm: str, data: Path, lr: float, seed: int, run_dir: Path, extra=()) -> list:
    return ["sft-dev", "--data", str(data), "--base", arm, "--lr", repr(float(lr)), "--seed", str(seed),
            "--run-dir", str(run_dir), *extra]


def select_argv(runs, run_dir: Path) -> list:
    return ["sft-select", "--runs", *map(str, runs), "--run-dir", str(run_dir)]


def sft_dev(clone: Path, job_dir: Path, arm: str, data: Path, lr: float, seed: int, run_dir: Path, sh=_sh,
            extra=()) -> Path:
    trackp(clone, job_dir, sft_dev_argv(arm, data, lr, seed, run_dir, extra), sh)
    return run_dir


def run_name(lr: float, seed: int, n: int | str = "full") -> str:
    return f"lr{float(lr):g}_s{seed}" + ("" if n == "full" else f"_n{n}")


# =============================================================================================== the job
def run_job(spec_path: Path, arm: str, job_dir: Path | None = None, *, started: float | None = None,
            sh=_sh, git=_git) -> dict:
    """The job of one arm (module docstring). Writes ``out/``, ``out.tar``, ``job_record.json`` and ``SHA256SUMS`` in
    ``job_dir`` (the job's scratch, the current directory by default) and raises Stop on a STOP."""
    started = started or time.time()
    job_dir = Path(job_dir or Path.cwd()).resolve()
    spec = load_spec(spec_path)
    loaded = validate_spec(spec, launch=True)
    if arm not in spec["arms"]:
        raise Stop(f"STOP: {arm} is not an arm of the spec")
    record: dict = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "arm": arm,
                    "phase": 1, "spec_sha256": _sha_file(spec_path), "paper_commit": spec["paper"]["commit"],
                    "started_utc": _utc(started), "stop": None, "stop_class": None, "steps": [],
                    "projection": loaded["projection"]["per_arm"][arm],
                    "output_use": "ENGINEERING_ONLY P.4 phase 1 (R1-TRACKP-P4-DECISIONS): readiness only; no "
                                  "real-label test read; no evaluation seed read"}
    out = job_dir / "out"
    out.mkdir(exist_ok=True)
    clone = job_dir / "paper"
    try:
        record["image"] = image_identity(spec)
        record["gpu"] = gpu_identity(sh)
        record["host"] = host_identity()
        record["steps"].append("identity")
        record["clone"] = clone_full(spec["paper"]["commit"], clone, git, sh)
        record["steps"].append("clone")
        record["env3_freeze"] = env3_freeze(spec, clone, sh)
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
                grid.append(sft_dev(clone, job_dir, arm, data, lr, s, runs / run_name(lr, s), sh))
                check_run_protocol(grid[-1], sft_cfg, lr=lr, seed=s, data_sha256=record["data"]["sft_data_sha256"])
        record["protocol"] = check_run_protocol(grid[0], sft_cfg, lr=LR_GRID[0], seed=SEEDS[0])
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
            lc_runs[str(point)] = [sft_dev(clone, job_dir, arm, sub, lr_sel, s, runs / run_name(lr_sel, s, point), sh)
                                   for s in SEEDS]
            for s, d in zip(SEEDS, lc_runs[str(point)]):
                check_run_protocol(d, sft_cfg, lr=lr_sel, seed=s, data_sha256=_sha_file(sub / "sft_data.json"))
        record["learning_curve"] = {k: [p.name for p in v] for k, v in lc_runs.items()}
        record["steps"].append("learning_curve")
        boot = P.rps_skill_bootstrap(data, [runs / run_name(lr_sel, s) / "stage_s" for s in SEEDS])
        (out / "bootstrap.json").write_text(json.dumps(boot, indent=1, sort_keys=True) + "\n")
        record["bootstrap"] = {"raw": boot["raw"], "temperature_scaled": boot["temperature_scaled"]}
        record["steps"].append("bootstrap")
        cfg = json.loads(_read_utf8(clone / HOST_CONFIG))
        base = {k: cfg["bases"][arm].get(k) for k in ("family", "base_repo", "base_revision", "adapter_repo",
                                                       "adapter_revision")}
        pin = P.arm_pin(arm=arm, base_record=base, staged=record["staging"]["weights"], data_dir=data,
                        select_report=select, grid_runs=grid, lc_runs=lc_runs,
                        micro_batch=record["protocol"]["micro_batch"],
                        host_config_sha256=record["configs"]["host_config"]["sha256"])
        (out / "arm_pin.json").write_text(json.dumps(pin, indent=1, sort_keys=True) + "\n")
        record["arm_pin_sha256"] = _sha_file(out / "arm_pin.json")
        record["steps"].append("arm_pin")
        record["test_path"] = test_path(clone, job_dir, arm, ins, sh)
        record["steps"].append("test_path")
    except Stop as exc:
        record["stop"], record["stop_class"] = str(exc), exc.stop_class
    except Exception as exc:  # noqa: BLE001 - every failure writes the record and the sums
        record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
    finished = time.time()
    record["finished_utc"] = _utc(finished)
    record["gpu_hours"] = round((finished - started) / 3600, 4)
    (job_dir / "job_record.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=job_dir, check=False)
    _write_sums(job_dir, ("out.tar", "job_record.json"))
    if record["stop"]:
        raise Stop(record["stop"])
    return record


def test_path(clone: Path, job_dir: Path, arm: str, ins: dict, sh=_sh) -> dict:
    """Step 10 (P4-PHASE1-TEST A): the evaluator's path on synthetic labels; the real-label test is never read."""
    syn = data_build(clone, job_dir, ins, sh, synthetic=True)
    run = sft_dev(clone, job_dir, arm, syn, LR_GRID[0], 0, job_dir / "out" / "test_path" / "run", sh,
                  extra=("--steps", "2", "--eval-every", "1"))
    ledger = job_dir / "out" / "ledgers" / TABLE_PIN
    env = {**offline_env(job_dir), "PYTHONPATH": str(clone)}
    code = ("import json, sys\nfrom pathlib import Path\n"
            "from r1.scripts import trackp_p4_test_path as T\n"
            "print(json.dumps(T.main(sys.argv[1:])))\n")
    res = sh([ENV3_PYTHON, "-B", "-c", code, "--data", str(syn), "--table", ins["table_dir"], "--run", str(run),
              "--arm", arm, "--sweep", str(clone / SWEEP_INDEX), "--paper-root", str(clone),
              "--classification", str(clone / CLASSIFICATION), "--host-config", str(clone / HOST_CONFIG),
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
    ``image.versions_sha256`` (T1) and ``host_config.sha256`` (T3). The arms and ``first_arm`` are those of the default
    check (both controls, ``kev-0.8b`` first). The label fields, ``estimate.*`` and ``caps.probe_gpu_hours`` may stay
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
    _pin(spec["host_config"].get("sha256"), "host_config.sha256", allow=False)
    return {"spec": spec, "run_id": run_id, "probe": dict(probe)}


def check_probe_template(spec: dict, template: dict) -> None:
    """A filled probe spec differs from the committed template (``p4_probe_spec.json``) only in ``PROBE_FILLED``,
    which the template holds as placeholders."""
    a, b = json.loads(json.dumps(spec)), json.loads(json.dumps(template))
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


def probe_run_summary(run_dir: Path, data: dict, sft_cfg: dict, probe: dict, wall: dict) -> dict:
    """The probe run's protocol and timings from its ``stage_s`` (cluster test plan §4.4); S10's refusals: another
    micro-batch or effective batch, a protocol deviation other than ``{"max_steps": 50}``, another data directory."""
    stage_s = Path(run_dir) / "stage_s"
    rep = json.loads(_read_utf8(stage_s / "sft_report.json"))
    proto = rep.get("protocol") or {}
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
            "max_tokens": int(sft_cfg["prompt"]["max_tokens"]), "gradient_checkpointing": "off (SFT path)",
            "protocol_deviation": rep.get("protocol_deviation"), "steps_per_epoch": rep.get("steps_per_epoch"),
            "total_steps": rep.get("total_steps"), "stopped_at": stopped,
            "early_stopped": train.get("early_stopped"),
            "s_per_step_wall": round(wall["wall_s"] / stopped, 4),
            "step_s": step_summary(stage_s / "metrics.jsonl")}


def run_probe(spec_path: Path, arm: str, job_dir: Path | None = None, *, started: float | None = None, sh=_sh,
              git=_git, popen=subprocess.Popen, environ=None, lib_file: Path | None = None) -> dict:
    """The H200 SFT fit and timing probe of one base (module docstring; cluster test plan §4.2 items 1-10). Writes
    ``out/``, ``out.tar`` (the allow-list ``PROBE_KEEP`` only), ``job_record.json`` (``trackp_p4_probe_record/1``) and
    ``SHA256SUMS`` in ``job_dir`` and raises Stop on a STOP."""
    started = started or time.time()
    job_dir = Path(job_dir or Path.cwd()).resolve()
    spec = load_spec(spec_path)
    loaded = validate_probe_spec(spec)
    if arm not in spec["arms"]:
        raise Stop(f"STOP: {arm} is not an arm of the probe spec")
    probe = loaded["probe"]
    record: dict = {"schema": PROBE_RECORD_SCHEMA, "label": ENGINEERING_ONLY, "mode": "probe", "run_id": spec["run_id"],
                    "arm": arm, "phase": 1, "spec_sha256": _sha_file(spec_path), "paper_commit": spec["paper"]["commit"],
                    "started_utc": _utc(started), "stop": None, "stop_class": None, "steps": [], "probe": probe,
                    "output_use": "ENGINEERING_ONLY H200 SFT fit and timing probe (P4-PROBE A): synthetic labels, at "
                                  "most 50 steps, one base; nothing kept as an arm; no label file, receipt or freeze "
                                  "record read; its GPU-hours count against P4-CAP (P4-PROBECAP A)"}
    out = job_dir / "out"
    pdir = out / "probe"
    pdir.mkdir(parents=True, exist_ok=True)
    clone = job_dir / "paper"
    try:
        record["image"] = image_identity(spec)
        record["gpu"] = gpu_identity(sh)                 # unscoped, as the P.4 job runs it (F3; T7)
        record["host"] = host_identity()
        record["visible_devices"] = visible_devices(record["gpu"], environ)
        record["condor"] = condor_ad(environ)
        record["steps"].append("identity")
        record["clone"] = clone_full(spec["paper"]["commit"], clone, git, sh)
        record["code"] = probe_code_binding(spec, clone, lib_file)
        record["steps"].append("clone")
        record["env3_freeze"] = env3_freeze(spec, clone, sh)
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
                    extra=("--steps", str(probe["steps"])))
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
                                          record["wall"])
        record["steps"].append("probe")
    except Stop as exc:
        record["stop"], record["stop_class"] = str(exc), exc.stop_class
    except Exception as exc:  # noqa: BLE001 - every failure writes the record and the sums
        record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
    record["oom"] = record["stop_class"] == "arm" and "OOM" in str(record["stop"])
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
    """S10 / §4.1: a probe of another base is staged only after the first arm's probe record is sealed and STOP-free
    (same probe spec)."""
    first = spec["first_arm"]
    if path is None:
        raise Stop(f"STOP: probe {first} alone first; another base needs --first-record (its sealed, STOP-free probe "
                   "record)")
    path = Path(path).resolve()
    arm_root = (Path(sealed_root) / spec["run_id"] / first).resolve()
    if path.parent.parent != arm_root or path.name != "job_record.json" or \
            not (path.parent / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: --first-record must be {arm_root}/attempt-N/job_record.json with its SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=path.parent, capture_output=True).returncode != 0:
        raise Stop("STOP: the first arm's sealed probe outputs do not verify against SHA256SUMS")
    record = json.loads(_read_utf8(path))
    receipt = json.loads(_read_utf8(path.parent / "SEAL_RECEIPT.json"))
    checks = {"schema": record.get("schema") == PROBE_RECORD_SCHEMA, "run_id": record.get("run_id") == spec["run_id"],
              "arm": record.get("arm") == first, "spec_sha256": record.get("spec_sha256") == spec_sha256,
              "receipt": receipt.get("job_record_sha256") == _sha_file(path),
              "identity_verified": receipt.get("identity_verified") is True,
              "stop": record.get("stop") is None and record.get("steps", [])[-1:] == ["probe"]}
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
            (n and doc.get("t1_gpu_hours") is not None):
        raise Stop(f"STOP: {path} is not charge file {n} ({CHARGE_SCHEMA}) of {run}")
    return doc


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
                  t1_wallclock_s: float | None = None) -> dict:
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

    ``t1_wallclock_s`` (decision P4-T1CHARGE, option A): T1's ``RemoteWallClockTime``, added when given; a T1 charge
    already in a charge file is added by default, and giving it twice is a STOP."""
    runs, total, unrecorded = {}, 0.0, []
    root = Path(sealed_root)
    if wallclock is not None and (not isinstance(wallclock, dict) or wallclock.get("schema") != WALLCLOCK_SCHEMA
                                  or not isinstance(wallclock.get("runs"), dict)):
        raise Stop(f"STOP: the wall-clock input must be {{'schema': '{WALLCLOCK_SCHEMA}', 'runs': {{...}}}}")
    seen_runs, t1_files = set(), 0.0
    files = charge_file_listing(sealed_root)
    for d in sorted(p for p in root.iterdir() if p.is_dir() and PROBE_RUN_ID.fullmatch(p.name)) if root.is_dir() else []:
        c = charged_hours({"run_id": d.name, "probe": PROBE, "caps": {}}, sealed_root)
        recorded = {}
        for n, f in enumerate(files.get(d.name, [])):
            doc = _charge_doc(Path(f["path"]), d.name, n)
            t1_files += float(doc.get("t1_gpu_hours") or 0.0)
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
        if given is not None:
            seen_runs.add(d.name)
            if set(given) != keys:
                raise Stop(f"STOP: the wall-clock input for {d.name} must give exactly its sealed attempts; missing "
                           f"{sorted(keys - set(given))}, extra {sorted(set(given) - keys)}")
        attempts = []
        for a in c["attempts"]:
            a, key = dict(a), f"{a['arm']}/{a['attempt']}"
            receipt = a["charged_gpu_hours"]
            att_dir = d / a["arm"] / a["attempt"]
            if given is not None:
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
    if t1_wallclock_s is not None and t1_files:
        raise Stop("STOP: T1 is already charged in a probe charge file (P4-T1CHARGE)")
    t1 = round(_wallclock_s(t1_wallclock_s, "T1") / 3600, 4) if t1_wallclock_s is not None else (t1_files or None)
    total += t1 or 0.0
    return {"runs": runs, "pending": [p for r in runs.values() for p in r["pending"]], "t1_gpu_hours": t1,
            "unrecorded": unrecorded, "charge_files": files, "total": round(total, 4)}


def charge_file_docs(charges: dict, record_run: str, t1_charged: bool) -> dict:
    """The charge files ``probe-record`` writes: one per run whose wall clocks came from the input, with the charge it
    used per attempt; T1's charge (if charged) in the file of the record's own run."""
    out = {}
    for run, r in charges["runs"].items():
        if r["charge_files"] or not r["attempts"]:
            continue
        out[run] = {"schema": CHARGE_SCHEMA, "run_id": run, "label": ENGINEERING_ONLY, "supplement": 0,
                    "rule": "P4-PROBECAP A; review round 2, M1: written once by probe-record; probe_charges applies it",
                    "attempts": {f"{a['arm']}/{a['attempt']}": {
                        "receipt_gpu_hours": a["receipt_gpu_hours"], "remote_wallclock_s": a.get("remote_wallclock_s"),
                        "cluster_id": a.get("cluster_id"), "charged_gpu_hours": a["charged_gpu_hours"]}
                        for a in r["attempts"]},
                    "t1_gpu_hours": charges["t1_gpu_hours"] if (t1_charged and run == record_run) else None}
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
                   "probe record; probe_charges applies it", "attempts": attempts, "t1_gpu_hours": None}
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
    (``probe_charges``). A probe attempt no charge file names, a pending probe submission, or a re-derived charge above
    the spec's value is a STOP. For the attempts the record charged, the re-derived value equals the record's
    ``p4_probe_gpu_hours``."""
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
    derived = ceil_hundredth(charges["total"])
    have = probe_gpu_hours(spec) or 0.0
    if derived > have + 1e-9:
        raise Stop(f"STOP: the sealed tree charges {derived} GPU-h to the probe, more than caps.probe_gpu_hours {have}: "
                   "rebuild the probe record and the spec (P4-PROBECAP A)")
    return {"probe_gpu_hours_spec": have, "probe_gpu_hours_sealed_tree": derived, "charge_files": on_disk}


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
    stages = [str(Path(e["stage"]).resolve()) if e.get("stage") else None for e in read_ledger(ledger)
              if e["arm"] == Path(arm_dir).name]
    pos = {}
    for name, receipt, _ in free:
        src = receipt.get("source_dir")
        hits = [k for k, s in enumerate(stages) if src and s == str(Path(src).resolve()) and k not in pos.values()]
        if not hits:
            raise Stop(f"STOP: the STOP-free probe attempts of {Path(arm_dir).name} cannot be ordered by submission "
                       f"(no ClusterId from one schedd, no ledger entry for {name}): the author decides")
        pos[name] = hits[0]
    ranked = sorted(free, key=lambda f: pos[f[0]])
    return {"first": ranked[0][0], "extra": [{"attempt": f[0], "ledger_position": pos[f[0]]} for f in ranked[1:]],
            "basis": "ledger order"}


def probe_records(probe_spec: dict, probe_spec_sha256: str, p4_spec: dict, sealed: list[Path],
                  sealed_root: Path = SEALED_ROOT, *, wallclock: dict | None = None,
                  t1_wallclock_s: float | None = None) -> dict:
    """The §4.4 record (``trackp_p4_h200_sft_probe/1``) from the first sealed, verified, STOP-free probe attempt of each
    arm of the P.4 spec **by submission order** (``submission_order``: HTCondor ``ClusterId``, else ledger order; never
    seal order); later STOP-free attempts of an arm are charged, never used, and listed in
    ``extra_stop_free_attempts`` so that more than one run per base is visible; and the §4.5 hours; ``p4_probe_gpu_hours`` is every probe attempt's charge (``probe_charges``)
    rounded up to 0.01. The P.4 spec with these values must validate within P4-CAP (S12), else a STOP."""
    validate_probe_spec(probe_spec)
    validate_spec(p4_spec)
    same = ("gpu_model", "env3", "sft_config", "split_file", "table", "layout", "arms", "first_arm", "protocol")
    differ = [k for k in same if probe_spec.get(k) != p4_spec.get(k)]
    differ += [f"image.{k}" for k in ("digest", "row") if probe_spec["image"].get(k) != p4_spec["image"].get(k)]
    if probe_spec["host_config"]["path"] != p4_spec["host_config"]["path"] or \
            (not _placeholder(p4_spec["host_config"]["sha256"]) and
             probe_spec["host_config"]["sha256"] != p4_spec["host_config"]["sha256"]):
        differ.append("host_config")
    if differ:
        raise Stop(f"STOP: the probe spec and the P.4 spec differ in {differ}: the probe does not measure these jobs")
    run_root = (Path(sealed_root) / probe_spec["run_id"]).resolve()
    jobs, keys, extras = {}, {}, {}
    for d in map(Path, sealed):
        if d.resolve().parent.parent != run_root or not re.fullmatch(r"attempt-[1-9][0-9]*", d.name):
            raise Stop(f"STOP: {d} is not a sealed probe attempt under {run_root}/<arm>/attempt-N")
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=d, capture_output=True).returncode != 0:
            raise Stop(f"STOP: {d} does not verify against its SHA256SUMS")
        rec = json.loads(_read_utf8(d / "job_record.json"))
        receipt = json.loads(_read_utf8(d / "SEAL_RECEIPT.json"))
        if receipt.get("job_record_sha256") != _sha_file(d / "job_record.json") or rec.get("stop") or \
                rec.get("schema") != PROBE_RECORD_SCHEMA or rec.get("spec_sha256") != probe_spec_sha256 or \
                rec.get("run_id") != probe_spec["run_id"] or receipt.get("identity_verified") is not True or \
                rec.get("steps", [])[-1:] != ["probe"]:
            raise Stop(f"STOP: {d} is not a sealed, verified, STOP-free probe attempt of this probe spec")
        arm = rec["arm"]
        if arm in jobs:
            raise Stop(f"STOP: two probe attempts given for {arm}")
        order = submission_order(d.parent, Path(sealed_root) / probe_spec["run_id"] / SUBMISSION_LEDGER)
        if order["first"] != d.name:
            raise Stop(f"STOP: {d.name} is not the first STOP-free probe attempt of {arm} by submission order "
                       f"({order['first']}, by {order['basis']}): the record uses that one, never one chosen by result")
        extras[arm] = order["extra"]
        jobs[arm] = (d, rec)
        for k, v in {"paper_commit": rec.get("paper_commit"), "image": rec.get("image"),
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
            "hostname": (rec.get("host") or {}).get("hostname"), "gpu": rec.get("gpu"),
            "image_digest": rec["image"]["digest"], "versions_sha256": rec["image"]["versions_sha256"],
            "paper_commit": rec["paper_commit"], "host_config_sha256": rec["configs"]["host_config"]["sha256"],
            "sft_config_sha256": rec["configs"]["sft_config"]["sha256"],
            "env3_freeze": {x: rec["env3_freeze"].get(x) for x in ("status", "image_line", "local_label")},
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
            "estimate_hours": est["hours"], "estimate_steps": est["steps"]})
    charges = probe_charges(sealed_root, wallclock=wallclock, t1_wallclock_s=t1_wallclock_s)
    if probe_spec["run_id"] not in charges["runs"]:
        raise Stop(f"STOP: no sealed attempt of {probe_spec['run_id']} under {sealed_root}")
    if charges["pending"]:
        raise Stop(f"STOP: {len(charges['pending'])} probe submission(s) are recorded but not sealed "
                   f"({sorted({p['arm'] for p in charges['pending']})}): seal every attempt first (P4-PROBECAP A)")
    probe_hours = ceil_hundredth(charges["total"])
    would = json.loads(json.dumps(p4_spec))
    would["estimate"]["hours"] = dict(hours)
    would["caps"]["probe_gpu_hours"] = probe_hours
    proj = validate_spec(would)["projection"]          # S12: within 40 GPU-h with the probe, and 64 slot-hours
    lines = [f"p4_estimate_hours: {arm} {hours[arm]:.2f}" for arm in p4_spec["arms"]] + \
        [f"p4_probe_gpu_hours: {probe_hours:.2f}"]
    return {"schema": PROBE_TABLE_SCHEMA, "label": ENGINEERING_ONLY, "probe_run_id": probe_spec["run_id"],
            "probe_spec_sha256": probe_spec_sha256,
            "rule": "P4-PROBE A, P4-PROBECAP A (R1-P4-TESTPLAN-DECISIONS); cluster test plan §4.4 and §4.5",
            "binding_note": "p4_switch binds the Markdown record's printed lines (p4_estimate_hours, p4_probe_gpu_hours, "
                            "p4_probe_charge_file), not this JSON file; the hours, the probe charge and the charge files "
                            "reach the spec, and are checked against it, only through those lines",
            "entries": entries, "estimate_hours": hours, "probe_gpu_hours_charged": charges["total"],
            "p4_probe_gpu_hours": probe_hours, "probe_charges": charges, "projection": proj,
            "wallclock_input": wallclock is not None, "t1_charged": t1_wallclock_s is not None,
            "charge_file_docs": charge_file_docs(charges, probe_spec["run_id"], t1_wallclock_s is not None),
            "probe_over_2_gpu_h": probe_hours > 2.0,
            "extra_stop_free_attempts": {a: v for a, v in sorted(extras.items()) if v},
            "headroom_below_15pct": sorted(e["arm"] for e in entries if e["headroom_frac"] is not None
                                           and e["headroom_frac"] < 0.15),
            "lines": lines}


# =============================================================================================== seal / assemble
def _read_record(path: Path):
    """The job record, or None when it is missing, empty, not UTF-8 or not JSON (a walltime kill): such an attempt is
    sealed as unreadable, never refused."""
    try:
        rec = json.loads(_read_utf8(Path(path)))
    except (OSError, ValueError, Stop):         # Stop: _read_utf8's refusal of a non-UTF-8 file
        return None
    return rec if isinstance(rec, dict) else None


LOG_HEADER = {"probe": "P4 probe container job start", "p4": "P4 container job start"}   # p4_probe.sh, p4_job.sh
CLEAN_END = re.compile(r"^P4 (?:probe )?container job end \S+ rc=0\s*$", re.M)   # the wrappers' last line on rc 0


def clean_exit_logged(src: Path) -> bool:
    """True when ``p4_run.log`` holds a wrapper's end line with ``rc=0`` (a job killed by the walltime or evicted never
    writes it: the wrapper is killed before its last ``echo``)."""
    log = Path(src) / "p4_run.log"
    return log.is_file() and CLEAN_END.search(log.read_bytes().decode("utf-8", "replace")) is not None


STAGE_KIND = {"trackp_p4_probe_stage/1": "probe", "trackp_p4_stage/1": "p4"}   # STAGE_MANIFEST.json schemas


def attempt_kind(src: Path, record: dict | None) -> str | None:
    """"probe" or "p4" from the record (its schema or mode), else from the first line of ``p4_run.log`` that one of
    the two wrappers writes, else (a job that never ran, sealed from its stage directory; review round 2, minor 2)
    from the stage's ``STAGE_MANIFEST.json`` (``trackp_p4_probe_stage/1`` with mode ``probe``, or ``trackp_p4_stage/1``,
    not a preview); None when none of them tells."""
    if record is not None and (record.get("schema") == PROBE_RECORD_SCHEMA or record.get("mode") == "probe"):
        return "probe"
    if record is not None and record.get("schema") == RECORD_SCHEMA:
        return "p4"
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
    - ``identity_verified`` is true only for a record carrying the H200 and the spec's image (v2.2) digest;
    - the attempt's kind (``attempt_kind``: the record's schema or mode, else the wrapper's first log line, else the
      stage manifest of a job that never ran) must be the spec's (a probe attempt only with a probe spec, a P.4
      attempt only with the P.4 spec); an attempt that shows none of them is sealed only with
      ``unknown_kind_confirmed`` and charged at least the larger of the probe's and the arm's walltime (and the
      record's ``gpu_hours`` if larger);
    - ``charged_gpu_hours`` is the record's ``gpu_hours``, or, with no readable value, the arm's requested walltime
      (the most the slot could have used; for a probe spec, the probe's ``walltime_s``)."""
    src = Path(job_output).resolve()
    record = _read_record(src / "job_record.json")
    if record is not None and (record.get("label") != ENGINEERING_ONLY or record.get("run_id") != spec["run_id"]
                               or record.get("arm") != arm):
        raise Stop("STOP: the job record does not match the run/arm or is not ENGINEERING_ONLY")
    sums = "absent"
    if (src / "SHA256SUMS").is_file() and (src / "SHA256SUMS").stat().st_size > 0:
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
            raise Stop("STOP: transferred SHA256SUMS verification failed")
        sums = "verified"
    if record is None and clean_exit_logged(src):   # review round 5, minor 2: a clean result is never a "killed" job
        raise Stop("STOP: p4_run.log records the wrapper's end with rc=0 but the job record is missing or unreadable: "
                   "a finished job's record was lost or blanked; it is not sealed as a killed job (the author decides)")
    want = "probe" if spec.get("probe") is not None else "p4"
    kind = attempt_kind(src, record)        # minor 2 of review round 1: a killed probe never enters the P.4 tree
    if kind is not None and kind != want:
        raise Stop(f"STOP: this is a {kind} attempt; it is not sealed with a {want} spec")
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
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "p4_run.log"):
        if (src / name).exists():
            shutil.copy2(src / name, target / name)
    verified = record is not None and (record.get("gpu") or {}).get("name") == GPU_MODEL and \
        (record.get("image") or {}).get("digest") == spec["image"]["digest"]
    hours = (record or {}).get("gpu_hours")
    wall_h = round(_requested_walltime_s(spec, arm) / 3600, 4)
    readable = isinstance(hours, (int, float)) and not isinstance(hours, bool) and hours >= 0
    if kind is None:                        # unknown kind, confirmed: at least the larger of both walltimes, even with
        wall_h = max(wall_h, round(PROBE["walltime_s"] / 3600, 4), round(arm_walltime_s(spec, arm) / 3600, 4))
        charged = max(float(hours) if readable else 0.0, wall_h)       # a readable record (review round 2, minor 1)
    else:
        charged = float(hours) if readable else wall_h
    receipt = {"schema": RECEIPT_SCHEMA, "run_id": spec["run_id"], "arm": arm, "attempt": n,
               "sealed_path": str(target), "record_readable": record is not None, "sums": sums,
               "identity_verified": verified, "stop": (record or {}).get("stop", "STOP: no readable job record"),
               "stop_class": (record or {}).get("stop_class", "infrastructure"),
               "charged_gpu_hours": charged, "kind": kind or "unknown (confirmed)",
               "charge_basis": ("job_record.gpu_hours" if charged == hours else
                                "requested walltime (no readable value)" if kind is not None else
                                "max(job_record.gpu_hours, the larger walltime) (unknown kind, confirmed)"),
               "job_record_sha256": _sha_file(target / "job_record.json") if (target / "job_record.json").is_file()
               else None,
               "run_log_sha256": _sha_file(target / "p4_run.log") if (target / "p4_run.log").is_file() else None,
               "source_dir": str(src), "sealed_utc": _utc()}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


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
                             "stop": r.get("stop")})
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
    """What every job of the table must share, without job-local paths (the job directory differs per job)."""
    return {"paper_commit": rec.get("paper_commit"), "image": rec.get("image"),
            "configs": {x: rec["configs"][x] for x in ("host_config", "sft_config")},
            "data": (rec.get("data") or {}).get("identity"),
            "labels": {k: v for k, v in (rec["inputs"]["labels"]).items() if k != "partition"},
            "env3_status": {k: rec["env3_freeze"].get(k) for k in ("status", "image_line", "pinned_line",
                                                                   "local_label")},
            "protocol": rec.get("protocol")}


def assemble(sealed: list[Path], spec: dict, spec_file_sha256: str, sealed_root: Path = SEALED_ROOT) -> dict:
    """One sealed, STOP-free attempt per arm (and no other STOP-free attempt of that arm: no choosing among
    attempts); in every job the same spec, paper commit, image, env3 freeze status, configs, labels (without the
    job-local partition path) and data identity (``data_identity``: path-free); GPU-hours summed over every sealed
    attempt of the run plus the probe's (``charged_hours``) against the cap."""
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
        jobs[rec["arm"]] = {"sealed": str(d), "job_record_sha256": receipt["job_record_sha256"],
                            "selected_lr": (rec.get("select") or {}).get("selected_lr"),
                            "gpu_hours": rec.get("gpu_hours"), "env3_freeze": rec.get("env3_freeze")}
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
    if charged["total"] > spec["caps"]["gpu_hours"]:
        raise Stop(f"STOP: {charged['total']} GPU-h charged by all attempts and the probe exceeds P4-CAP "
                   f"{spec['caps']['gpu_hours']}")
    return {"schema": ASSEMBLY_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "jobs": jobs,
            "gpu_hours_consumed": charged["total"], "gpu_hours_probe": charged["probe"], "probe_ledger": ledger,
            "gpu_hours_by_attempt": charged["attempts"],
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
    p = sub.add_parser("probe", help="the H200 SFT fit and timing probe of one base (P4-PROBE A)")
    p.add_argument("spec"); p.add_argument("--arm", required=True)
    r = sub.add_parser("probe-record", help="the probe record (§4.4) and hours (§4.5) from sealed probe attempts")
    r.add_argument("probe_spec"); r.add_argument("p4_spec"); r.add_argument("sealed", nargs="+")
    r.add_argument("--out", required=True, help="a new probe_records.json (never overwritten)")
    r.add_argument("--wallclock", required=True, type=Path,
                   help=f"{WALLCLOCK_SCHEMA} JSON: condor_history RemoteWallClockTime of every sealed probe attempt")
    r.add_argument("--t1-wallclock", type=float, default=None,
                   help="decision P4-T1CHARGE option A: T1's RemoteWallClockTime in seconds, added to the probe charge")
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
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"]}, indent=1))
        elif args.cmd == "probe":
            rec = run_probe(Path(args.spec), args.arm)
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
                                  wallclock=json.loads(_read_utf8(args.wallclock)), t1_wallclock_s=args.t1_wallclock)
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
            rec = run_job(Path(args.spec), args.arm)
            print(json.dumps({"ok": True, "arm": args.arm, "selected_lr": rec["select"]["selected_lr"]}, indent=1))
        elif args.cmd == "seal":
            print(json.dumps(seal(Path(args.job_output), load_spec(Path(args.spec)), args.arm,
                                  unknown_kind_confirmed=args.unknown_kind_confirmed), indent=1))
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
