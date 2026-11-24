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
   with the frozen source block (``check_partition``); the signed label-freeze record present in the clone at its
   sha256.
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
the cap, and the switch refuses a repeat whose projection would pass it.
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


def projection(spec: dict) -> dict:
    per = {a: {"gpu_hours": round(arm_hours(spec, a) + spec["layout"]["startup_s"] / 3600, 3),
               "walltime_s": arm_walltime_s(spec, a)} for a in spec["arms"]}
    gpu = round(sum(v["gpu_hours"] for v in per.values()), 3)
    slot = round(sum(v["walltime_s"] for v in per.values()) / 3600, 3)
    return {"per_arm": per, "total_gpu_hours": gpu, "total_slot_hours": slot,
            "cap_gpu_hours": spec["caps"]["gpu_hours"], "cap_slot_hours": spec["caps"]["slot_hours"],
            "within_cap": gpu <= spec["caps"]["gpu_hours"] and slot <= spec["caps"]["slot_hours"]}


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """Fail-closed; ``launch=True`` refuses every placeholder (the image VERSIONS sha256, the host
    config sha256 after its fill, the partition, receipt and freeze-record sha256, the probe-based estimate)."""
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
        raise Stop(f"STOP: the projection {proj['total_gpu_hours']} GPU-h / {proj['total_slot_hours']} slot-h "
                   "exceeds P4-CAP: author STOP")
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


def inputs(spec: dict, clone: Path, job_dir: Path) -> dict:
    """Step 5: the transferred table files and the receipted partition (laid out as ``release/sweep1/traindev/``)."""
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
    part = job_dir / "release" / "sweep1" / "traindev"
    part.mkdir(parents=True)
    for name in ("label_block.traindev.jsonl", "RECEIPT.json"):
        src = job_dir / name
        if src.is_symlink() or not src.is_file():
            raise Stop(f"STOP: transferred {name} missing")
        shutil.move(str(src), part / name)
    try:
        labels = _phase1(clone).check_partition(part, partition_sha256=spec["labels"]["partition_sha256"],
                                                receipt_sha256=spec["labels"]["receipt_sha256"],
                                                source_block_sha256=SOURCE_BLOCK_SHA256)
    except Exception as exc:
        if str(exc).startswith("STOP"):
            raise ProtocolStop(str(exc)) from None
        raise
    receipt = json.loads(_read_utf8(part / "RECEIPT.json"))
    got_props = (receipt.get("inputs") or {}).get("proposals_sha256")
    if got_props != pins.get("proposals.jsonl"):
        raise ProtocolStop(f"STOP: the receipt's proposals sha256 {got_props} is not the {TABLE_PIN} table pin "
                           f"{pins.get('proposals.jsonl')} (the labels are of another table)")
    freeze = spec["labels"]["freeze_record"]
    fpath = clone / freeze["path"]
    if not fpath.is_file() or _sha_file(fpath) != freeze["sha256"]:
        raise ProtocolStop(f"STOP: the signed label freeze {freeze['path']} is not in the clone at its sha256 (P1)")
    ftext = _read_utf8(fpath, ProtocolStop)
    if not re.search(r"^approved: true$", ftext, re.M) or SOURCE_BLOCK_SHA256 not in ftext:
        raise ProtocolStop(f"STOP: {freeze['path']} is not a signed freeze of the block {SOURCE_BLOCK_SHA256} (P1)")
    return {"table_dir": str(table), "table_sha256": rec, "partition_dir": str(part), "labels": labels,
            "label_freeze": {"path": freeze["path"], "sha256": freeze["sha256"]},
            "receipt_proposals_sha256": got_props}


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


# =============================================================================================== seal / assemble
def _read_record(path: Path):
    """The job record, or None when it is missing, empty or not JSON (a walltime kill)."""
    try:
        rec = json.loads(_read_utf8(Path(path)))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


def seal(job_output: Path, spec: dict, arm: str, sealed_root: Path = SEALED_ROOT) -> dict:
    """Copy one attempt to ``<sealed_root>/<run_id>/<arm>/attempt-N/`` (no overwrite; a new attempt for a repeated job,
    never a resume) with a receipt binding the record and log. Every attempt is sealed, so its outputs are kept and
    its GPU-hours counted (P4-JOB A, P4-CAP A):

    - a readable record must be this run's and arm's and ENGINEERING_ONLY (else STOP: the wrong job);
    - ``SHA256SUMS``, when present and non-empty, must verify (else STOP); a killed or early-stopped job leaves the
      empty files ``p4_job.sh`` pre-creates (``sums: absent``; empty files are kept as they are);
    - ``identity_verified`` is true only for a record carrying the H200 and the spec's image (v2.2) digest;
    - ``charged_gpu_hours`` is the record's ``gpu_hours``, or, with no readable value, the arm's requested walltime
      (the most the slot could have used)."""
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
    for name in (spec["run_id"], arm):
        if not SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    arm_root = Path(sealed_root) / spec["run_id"] / arm
    if any(p.is_symlink() for p in [arm_root, *arm_root.parents] if p.exists()):
        raise Stop(f"STOP: {arm_root} has a symlink component")
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
    charged = float(hours) if isinstance(hours, (int, float)) and not isinstance(hours, bool) and hours >= 0 else \
        round(arm_walltime_s(spec, arm) / 3600, 4)
    receipt = {"schema": RECEIPT_SCHEMA, "run_id": spec["run_id"], "arm": arm, "attempt": n,
               "sealed_path": str(target), "record_readable": record is not None, "sums": sums,
               "identity_verified": verified, "stop": (record or {}).get("stop", "STOP: no readable job record"),
               "stop_class": (record or {}).get("stop_class", "infrastructure"),
               "charged_gpu_hours": charged,
               "charge_basis": "job_record.gpu_hours" if charged == hours else "requested walltime (no readable value)",
               "job_record_sha256": _sha_file(target / "job_record.json") if (target / "job_record.json").is_file()
               else None,
               "run_log_sha256": _sha_file(target / "p4_run.log") if (target / "p4_run.log").is_file() else None,
               "sealed_utc": _utc()}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def charged_hours(spec: dict, sealed_root: Path = SEALED_ROOT) -> dict:
    """GPU-hours charged to P4-CAP by every sealed attempt of the run, per arm and in total (each attempt's receipt;
    an attempt directory without a receipt is a STOP: seal it first)."""
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
    return {"per_arm": per, "total": round(sum(per.values()), 4), "attempts": attempts, "pending": pending}


SUBMISSION_LEDGER = "_submissions.jsonl"


def pending_submissions(spec: dict, sealed_root: Path, attempts: list[dict]) -> list[dict]:
    """Submissions recorded in the run's ledger (``<sealed_root>/<run_id>/_submissions.jsonl``, appended by the switch)
    that have no sealed attempt yet, each charged at the arm's requested walltime (a running or lost job counts)."""
    ledger = Path(sealed_root) / spec["run_id"] / SUBMISSION_LEDGER
    subs = [json.loads(x) for x in _read_utf8(ledger).splitlines() if x.strip()] if ledger.is_file() else []
    out = []
    for arm in sorted({s["arm"] for s in subs}):
        n = sum(1 for s in subs if s["arm"] == arm) - sum(1 for a in attempts if a["arm"] == arm)
        out += [{"arm": arm, "charged_gpu_hours": round(arm_walltime_s(spec, arm) / 3600, 4),
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
    attempt of the run (``charged_hours``) against the cap."""
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
    if charged["total"] > spec["caps"]["gpu_hours"]:
        raise Stop(f"STOP: {charged['total']} GPU-h charged by all attempts exceeds P4-CAP {spec['caps']['gpu_hours']}")
    return {"schema": ASSEMBLY_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "jobs": jobs,
            "gpu_hours_consumed": charged["total"], "gpu_hours_by_attempt": charged["attempts"],
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
    j = sub.add_parser("job"); j.add_argument("spec"); j.add_argument("--arm", required=True)
    z = sub.add_parser("seal"); z.add_argument("job_output"); z.add_argument("spec"); z.add_argument("--arm", required=True)
    a = sub.add_parser("assemble"); a.add_argument("spec"); a.add_argument("sealed", nargs="+")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "validate":
            loaded = validate_spec(load_spec(Path(args.spec)), launch=args.launch)
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"]}, indent=1))
        elif args.cmd == "job":
            rec = run_job(Path(args.spec), args.arm)
            print(json.dumps({"ok": True, "arm": args.arm, "selected_lr": rec["select"]["selected_lr"]}, indent=1))
        elif args.cmd == "seal":
            print(json.dumps(seal(Path(args.job_output), load_spec(Path(args.spec)), args.arm), indent=1))
        else:
            print(json.dumps(assemble([Path(x) for x in args.sealed], load_spec(Path(args.spec)),
                                      _sha_file(Path(args.spec))), indent=1))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
