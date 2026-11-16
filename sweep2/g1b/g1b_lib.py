#!/usr/bin/env python3
"""G.1b — T1 GPU-node noise-floor job on NEMO2 L40S (HTCondor; ENGINEERING_ONLY; PREPARED, NOT RUNNABLE).

Authority: PLAN row R1-TRACKG-G1B-HOST (`author-decisions-20261116` @ 4da73306), which moves the G.1b part of
R1-ADA-CENSUS to NEMO2 L40S while the G.0 census stays on Ada; PLAN rows R1-BX-D5 (fixed step/token budget, one GPU
model per table), R1-BX-REVISIONS (e) census / (f) cost, R1-SWEEP2-SETTINGS (1) 32,768 context and (5) the 60 GPU-h /
48 h STOP, and the 22 Oct D21 rule. Work plan: `docs/r1/prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`
(`docs/runbooks-16nov` @ b3289232), later-sweep pattern S2-C8.

One job == one chunk of the D21 30-seed measurement for ONE G.0-named T1 candidate node: one seed condition (train,
split or joint) over a contiguous seed part, or the two default runs per configuration (determinism check). The job
never reads labels, never starts the proposer and never downloads the 19.6 GB pick GGUF: the proposer/server/GGUF
pins are carried so the whole G.1b family (this noise floor and the later D28-liveness sub-unit) shares one pinned
environment, but this chunk makes no LLM calls.

The wrapper validates the spec fail-closed. It refuses to run while the G.0 census has not named the candidate
nodes: the spec carries a validated placeholder list, and every chunk job STOPs on a placeholder node id, an empty
census, a placeholder run time or a placeholder edit set. Do not run: preparation only (see G1B_PLAN.md).

Subcommands:
  validate <spec>                 validate a complete chunk spec and print its projection (no side effects)
  plan-chunks <spec>              print the pre-declared chunk plan for the spec's candidate nodes
  run <spec>                      container entry: validate, measure this chunk, write out/ + job_record.json
  summarise <run-dir>             offline: verify coverage, apply the pinned D21 report rule, write the verdict
  seal <job-output> --run-id --chunk-id   operator: verify a transferred chunk and copy it to the sealed /ceph path

Outputs are ENGINEERING_ONLY: they are a noise-floor measurement, not a label table and not evidence. They enter no
training, selection or gate path; using a measured sigma-hat in a label table needs the separate T1 label
authorization and the R1-BX-D8 rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# --------------------------------------------------------------------------- frozen pins and pre-declared constants
SCHEMA = "g1b_job/v1"
KIND = "noise_floor_chunk"
RECORD_SCHEMA = "g1b_job_record/1"
RUN_SCHEMA = "r1.e1_noise_floor/2"
ENGINEERING_ONLY = "ENGINEERING_ONLY"
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/g1b")

# HTCondor host class (S2-C4 measured class: NEMO2 L40S, CpuFamily 6 / CpuModelNumber 207)
CLOUD_SITE = "BwForCluster-Nemo2"
GPU_MODEL = "NVIDIA L40S"
GPU_MIN_TOTAL_MEMORY_BYTES = 40 * 1024 ** 3  # L40S is 48 GB; a smaller card is an off-class landing
CPU_FAMILY = 6
CPU_MODEL_NUMBER = 207
CPU_MODEL_CONTAINS = "INTEL(R) XEON(R) PLATINUM 8562Y+"
MIN_CPUS = 16

# Frozen v1 GPU image (S2-C1 freeze proposal / S2-C4 measured layout); one digest for this table.
IMAGE_DIGEST = ("ghcr.io/dowlingwong/r1-htc-gpu@sha256:"
                "69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296")
LLAMA_SERVER_SHA256 = "f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0"
LLAMA_CPP_COMMIT = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
IMAGE_MARKERS = {"image": "r1-htc-gpu", "build_utc": "2026-11-14T23:10:24Z",
                 "llama_server_sha256": LLAMA_SERVER_SHA256, "llama_cpp_commit": LLAMA_CPP_COMMIT}

# Shared G.1b-family proposer/server pin (R1-SWEEP2-SETTINGS (1) and the pick of R1-EXAM-X7/R1-MAIN-PROPOSER).
# This noise-floor chunk declares it and records it; it starts no server and downloads no GGUF.
SERVER_SETTING = {
    "binary": "/opt/r1/llama/bin/llama-server",
    "ctx": 32768,
    "n_gpu_layers": 999,
    "n_parallel": 1,
    "cache_prompt": False,
    "expected_build": "0.7.0-dev (build 11669, commit 620d2225c)",
    "extra_args": ["--jinja", "--chat-template-kwargs", '{"enable_thinking": false}',
                   "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--no-webui"],
}
PICK_GGUF = {
    "url": ("https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/"
            "619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf"),
    "sha256": "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75",
    "size": 19598489952,
    "alias": "gemma4_31b",
    "provenance": {"registry_doc": "docs/r1/reports/exam_phase2_20261026/gemma4_31b.json",
                   "registry_sha256": "a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61",
                   "revision": "619aca7589c72be65dd968de8602ad23d68b5c14",
                   "file": "google_gemma-4-31B-it-Q4_K_M.gguf",
                   "source_label": "bartowski imatrix Q4_K_M"},
}
MODEL_USE = "declared-only-no-download"  # this chunk is a training-run measurement: no proposer, no GGUF egress
PAPER_REPO = "https://github.com/dowlingwong/Agent_paper_B.git"
HARNESS_REPO = "https://github.com/dowlingwong/autoresearch_harness.git"
HARNESS_EXAM_PIN = "897d83c8efa364ec2fdd37288241cc42e01d7274"  # EXAM pin; refused for the T1 table family

# D21 rule (PLAN row "D21 rule (22 Oct)"); executed by the pinned `r1.noise.e1_report` code.
SEEDS_PER_CONDITION = 30
CONDITIONS = ("train", "split", "joint")
SEED_BASES = {"train": 1001, "split": 2001, "joint": 3001}
SPLIT_POLICY = "vary"  # R1-SWEEP2-SETTINGS / D21: the noise floor is measured with the "vary" split
CONFIG_COUNT = 6  # baseline c0 + the five standard E1 edits
E1_EDIT_COUNT = 5
DEFAULT_RUNS_PER_CONFIG = 2  # `default` + `default_repeat`, the fixed-seed determinism check
D21_MIN_MATERIAL_EDITS = 2
D21_MIN_EFFECT = 0.002
D21_MIN_MEAN_P_WRONG = 0.10
WORKERS = 1  # one GPU training run at a time: the determinism premise of the D21 fixed-seed check

# Pre-declared caps / job layout (R1-SWEEP2-SETTINGS (5) and the S2-C4 measured layout).
CAP_TOTAL_GPU_HOURS = 60.0
CAP_CHUNK_WALL_HOURS = 48.0
MAX_CHUNK_WALL_SECONDS = 10776  # S2-C4 measured full-chunk wall (the reviewed S2-C2 +RequestWalltime)
MAX_CONCURRENT_SLOTS = 8  # pre-declared parallel node-job budget for the 48 h wall cap (checked before submit)
RESERVED_SECONDS = 900  # image/pin checks, staging, tars, per-chunk bookkeeping
CHUNK_OVERHEAD_FACTOR = 1.35  # per-run node copy + startup, declared (not measured for T1 nodes yet)
RUN_SECONDS_CEILING = 300.0  # R1-BX-D5: label runs 1-2 min, closed-loop up to about 5 min
MEMORY_FLOOR_MB = 32000  # S2-C4 measured floor, reused as the G.1b scheduling floor
DISK_FLOOR_KB = 42439718  # S2-C4 measured peak x1.4, reused as the G.1b scheduling floor
TRANSFER_OUTPUTS = "out.tar,job_record.json,SHA256SUMS,g1b_run.log"
TRANSFER_INPUTS = "g1b_job.sh,g1b_lib.py,g1b_spec.json"

# String / shape guards
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
NODE_ID = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
VERSION = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[A-Za-z0-9.+-]*)$")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
PLACEHOLDER = re.compile(r"^(?:G0_PENDING|PENDING|PLACEHOLDER|TBD|TODO|FILL)", re.IGNORECASE)
PLACEHOLDER_SHA = "0" * 64

ALLOWED_TOP = {"schema", "kind", "label", "run_id", "chunk", "g0_census", "plan", "image", "paper", "harness",
               "env", "proposer_environment", "measurement", "caps", "requirements"}


class Stop(RuntimeError):
    """Fail-closed STOP: the evidence is preserved, nothing is retried, nothing is deleted."""


# --------------------------------------------------------------------------- spec loading and small guards
def load_spec(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise Stop(f"STOP: cannot read spec: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise Stop(f"STOP: spec schema must be {SCHEMA}")
    return data


def _get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            raise Stop(f"STOP: spec missing {'.'.join(keys)}")
        cur = cur[k]
    return cur


def _text(v, name, pattern=None) -> str:
    if not isinstance(v, str) or not v or CONTROL.search(v):
        raise Stop(f"STOP: {name} must be a nonempty single-line string")
    if pattern is not None and not pattern.fullmatch(v):
        raise Stop(f"STOP: {name} has the wrong form")
    return v


def _number(v, name, *, minimum=None, maximum=None) -> float:
    if type(v) not in (int, float) or not math.isfinite(float(v)):
        raise Stop(f"STOP: {name} must be a finite number")
    if minimum is not None and v < minimum:
        raise Stop(f"STOP: {name} must be >= {minimum}")
    if maximum is not None and v > maximum:
        raise Stop(f"STOP: {name} must be <= {maximum}")
    return float(v)


def is_placeholder(value) -> bool:
    if not isinstance(value, str):
        return False
    s = value.strip()
    return bool(PLACEHOLDER.match(s)) or "PENDING" in s.upper() or s.startswith("<") or s.endswith(">")


def _no_placeholder(value, name: str) -> str:
    text = _text(value, name)
    if is_placeholder(text):
        raise Stop(f"STOP: {name} is still a placeholder ({text!r}); the G.0 census must fill it")
    return text


# --------------------------------------------------------------------------- projection and chunking
def runs_per_node(plan: dict) -> int:
    """552 = 6 configurations (baseline + 5 standard E1 edits) x (30 train + 30 split + 30 joint + 2 default)."""
    seeds = int(plan["seeds_per_condition"])
    return int(plan["configs"]) * (len(CONDITIONS) * seeds + int(plan["default_runs_per_config"]))


def _seed_parts(run_seconds: float) -> list[tuple[int, int]]:
    """Split the fixed 30-seed block so every chunk fits the measured 10,776 s scheduling ceiling."""
    per_seed_runs = CONFIG_COUNT
    per_run = run_seconds * CHUNK_OVERHEAD_FACTOR
    room = MAX_CHUNK_WALL_SECONDS - RESERVED_SECONDS
    max_runs = int(room // per_run) if per_run > 0 else 0
    max_seeds = max_runs // per_seed_runs
    if max_seeds < 1:
        raise Stop(f"STOP: one seed block ({per_seed_runs} runs at {run_seconds:g} s/run) does not fit the "
                   f"{MAX_CHUNK_WALL_SECONDS} s chunk ceiling; a larger run time is an author decision")
    parts, start = [], 0
    while start < SEEDS_PER_CONDITION:
        take = min(max_seeds, SEEDS_PER_CONDITION - start)
        parts.append((start, take))
        start += take
    return parts


def _chunk(node_id: str, condition: str, start: int, count: int, runs: int, run_seconds: float) -> dict:
    model_seconds = runs * run_seconds * CHUNK_OVERHEAD_FACTOR
    walltime = int(math.ceil(RESERVED_SECONDS + model_seconds))
    suffix = f"{condition}-s{start:02d}-{count:02d}" if condition != "default" else "default"
    return {"chunk_id": f"{node_id}-{suffix}", "node": node_id, "condition": condition,
            "seed_start": start, "seed_count": count, "runs": runs, "run_seconds": run_seconds,
            "model_seconds": round(model_seconds, 1), "walltime_s": walltime}


def chunk_plan(plan: dict) -> list[dict]:
    """Pre-declared chunking: one chunk per (node, condition, seed part) plus one determinism chunk per node."""
    chunks = []
    for node in plan["candidate_nodes"]:
        node_id = node["node_id"]
        run_seconds = float(node["run_seconds"])
        for condition in CONDITIONS:
            for start, count in _seed_parts(run_seconds):
                runs = count * int(plan["configs"])
                chunks.append(_chunk(node_id, condition, start, count, runs, run_seconds))
        default_runs = int(plan["configs"]) * int(plan["default_runs_per_config"])
        chunks.append(_chunk(node_id, "default", 0, 0, default_runs, run_seconds))
    return chunks


def projection(plan: dict) -> dict:
    """Pre-declared projection: GPU-hours are engaged-GPU upper bounds (workers = 1, so wall == GPU time)."""
    per_node = []
    total_runs = 0
    total_gpu_hours = 0.0
    for node in plan["candidate_nodes"]:
        runs = runs_per_node(plan)
        gpu_hours = runs * float(node["run_seconds"]) / 3600.0
        total_runs += runs
        total_gpu_hours += gpu_hours
        per_node.append({"node_id": node["node_id"], "runs": runs,
                         "run_seconds": float(node["run_seconds"]), "gpu_hours": round(gpu_hours, 3)})
    chunks = chunk_plan(plan)
    per_node_wall = max(n["gpu_hours"] for n in per_node) if per_node else 0.0
    return {"per_node": per_node, "candidate_nodes": len(plan["candidate_nodes"]),
            "runs_per_node": runs_per_node(plan), "total_runs": total_runs,
            "total_gpu_hours": round(total_gpu_hours, 3),
            "serial_wall_hours": round(total_gpu_hours, 3),  # workers = 1: GPU-hours equal one-slot wall hours
            "per_node_wall_hours": round(per_node_wall, 3),
            # slots needed for the whole unit to finish inside the 48 h wall cap (pre-submit condor_status check)
            "slots_required_for_48h_wall": max(1, int(math.ceil(total_gpu_hours / CAP_CHUNK_WALL_HOURS))),
            "chunks": len(chunks),
            "max_chunk_wall_seconds": max(c["walltime_s"] for c in chunks)}

def chunk_runs(plan: dict, chunk: dict) -> list[dict]:
    """Expand a pre-declared chunk into the exact run list (E1 schema: condition + paired seed roles)."""
    node = next(n for n in plan["candidate_nodes"] if n["node_id"] == chunk["node"])
    configs = [("c0", None)] + [(f"c{k}", edit) for k, edit in enumerate(node["edit_set"], start=1)]
    runs = []
    if chunk["condition"] == "default":
        for config_id, edit in configs:
            for condition in ("default", "default_repeat"):
                runs.append({"node": node["node_id"], "config": config_id, "edit": edit,
                             "condition": condition, "train_seed": None, "split_seed": None})
        return runs
    for condition in (chunk["condition"],):
        for config_id, edit in configs:
            for offset in range(chunk["seed_start"], chunk["seed_start"] + chunk["seed_count"]):
                train_seed = SEED_BASES["train"] + offset if condition in ("train", "joint") else None
                split_seed = SEED_BASES["split"] + offset if condition in ("split", "joint") else None
                runs.append({"node": node["node_id"], "config": config_id, "edit": edit,
                             "condition": condition, "train_seed": train_seed, "split_seed": split_seed})
    return runs


# --------------------------------------------------------------------------- D21 rule (unit-testable, frozen)
def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _sd(values) -> float:
    xs = [float(v) for v in values]
    if len(xs) < 2:
        return float("nan")
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))


def edit_stats(deltas_joint) -> dict:
    """Per-edit D21 quantities from the 30 paired joint deltas d_s = m(c_k, s) - m(c0, s)."""
    dj = [float(x) for x in deltas_joint]
    if len(dj) < 2:
        raise Stop("STOP: a D21 edit needs the 30 paired joint deltas")
    delta = sum(dj) / len(dj)
    sd = _sd(dj)
    se = sd / math.sqrt(len(dj))
    resolved = (abs(delta) > 2 * se) if se > 0 else (delta != 0)
    if sd > 0:
        p_wrong = _phi(-abs(delta) / sd)
    else:
        p_wrong = 0.0 if delta != 0 else float("nan")
    material = bool(resolved and abs(delta) >= D21_MIN_EFFECT)
    return {"n_joint": len(dj), "delta_hat_J": delta, "sd_joint": sd, "se": se,
            "resolved": bool(resolved), "material": material, "p_wrong": p_wrong}


def d21_qualify(edits: list[dict], sigma_joint: float, seeds_per_condition: int) -> dict:
    """Apply the 22 Oct D21 rule exactly: >=2 material edits, mean plug-in P(wrong) >= 0.10, sigma_joint > 0.

    The seed count is fixed at 30 (D21 "D21 rule (22 Oct)" / "D21 uniform application"); it is checked, not
    adjustable. `edits` entries carry the `edit_stats` fields; `sigma_joint` is the sd of the baseline's joint
    metrics. The seed-bootstrap probability of qualifying is a reported diagnostic, never part of the decision.
    """
    material = [e for e in edits if e.get("material")]
    p_vals = [float(e["p_wrong"]) for e in material if not math.isnan(float(e["p_wrong"]))]
    mean_p = sum(p_vals) / len(p_vals) if p_vals else float("nan")
    checks = {
        "seeds_per_condition_is_30": int(seeds_per_condition) == SEEDS_PER_CONDITION,
        "material_edits_ge_2": len(material) >= D21_MIN_MATERIAL_EDITS,
        "mean_p_wrong_ge_0.10": bool(p_vals) and mean_p >= D21_MIN_MEAN_P_WRONG,
        "sigma_joint_gt_0": float(sigma_joint) > 0,
    }
    return {"qualifies_D21": all(checks.values()), "checks": checks, "n_edits": len(edits),
            "n_material": len(material), "mean_p_wrong_material": mean_p, "sigma_joint": float(sigma_joint),
            "rule": {"min_material_edits": D21_MIN_MATERIAL_EDITS, "min_effect": D21_MIN_EFFECT,
                     "min_mean_p_wrong": D21_MIN_MEAN_P_WRONG, "seeds_per_condition": SEEDS_PER_CONDITION,
                     "source": "PLAN D21 rule (22 Oct); r1.noise.e1_report"}}


def determinism_check(rows: list[dict]) -> dict:
    """Pair `default` with `default_repeat` per configuration; a mismatch fails the fixed-seed premise."""
    pairs = {}
    for row in rows:
        if row.get("condition") not in ("default", "default_repeat"):
            continue
        pairs.setdefault(row["config"], {})[row["condition"]] = (
            row.get("metric") if row.get("success") else None)
    per_config, ok = {}, True
    for config_id, got in sorted(pairs.items()):
        a, b = got.get("default"), got.get("default_repeat")
        same = a is not None and a == b
        per_config[config_id] = {"default": a, "default_repeat": b, "bit_identical": same}
        ok = ok and same
    return {"deterministic": bool(ok and per_config), "configs": per_config}


# --------------------------------------------------------------------------- spec validation (fail-closed)
def validate_spec(spec: dict) -> dict:
    if not isinstance(spec, dict):
        raise Stop(f"STOP: spec must be an object with schema {SCHEMA}")
    if "label_source" in spec:
        raise Stop("STOP: the noise-floor chunk takes no authorization note; it is ENGINEERING_ONLY")
    extra = set(spec) - ALLOWED_TOP
    if extra:
        raise Stop(f"STOP: unknown spec keys {sorted(extra)}")
    if spec.get("schema") != SCHEMA:
        raise Stop(f"STOP: spec schema must be {SCHEMA}")
    if spec.get("kind") != KIND:
        raise Stop(f"STOP: spec kind must be {KIND}")
    if spec.get("label") != ENGINEERING_ONLY:
        raise Stop("STOP: the G.1b noise-floor chunk is ENGINEERING_ONLY; a label table is a separate "
                   "authorized unit (no EVIDENCE path here)")
    run_id = _text(_get(spec, "run_id"), "run_id", SAFE)

    # G.0 census: the candidate node list does not exist before the experiment agent's Ada census.
    census = _get(spec, "g0_census")
    status = _text(_get(census, "status"), "g0_census.status")
    if status != "complete":
        raise Stop("STOP: G.0 census incomplete (status != 'complete'). The candidate T1 node list comes only "
                   "from the experiment agent's G.0 census on Ada (R1-ADA-CENSUS; R1-TRACKG-G1B-HOST keeps the "
                   "census on Ada and moves only G.1b to NEMO2 L40S)")
    report = _no_placeholder(_get(census, "report_path"), "g0_census.report_path")
    if not report.startswith("docs/r1/reports/"):
        raise Stop("STOP: g0_census.report_path must be the committed G.0 census report under docs/r1/reports/")
    report_sha = _text(_get(census, "report_sha256"), "g0_census.report_sha256", SHA)
    if report_sha == PLACEHOLDER_SHA:
        raise Stop("STOP: g0_census.report_sha256 is a placeholder; pin the real census report sha256")
    _text(_get(census, "host_platform"), "g0_census.host_platform")
    census_nodes = _get(census, "nodes")
    if not isinstance(census_nodes, list) or not census_nodes:
        raise Stop("STOP: the G.0 census named no candidate nodes; refuses G.0-empty node lists")
    for i, node in enumerate(census_nodes):
        node = _no_placeholder(node, f"g0_census.nodes[{i}]")
        if not NODE_ID.fullmatch(node):
            raise Stop(f"STOP: g0_census.nodes[{i}]={node!r} is not a harness node id")
    if len(set(census_nodes)) != len(census_nodes):
        raise Stop("STOP: g0_census.nodes contains duplicates")

    # Pre-declared plan over those nodes.
    plan = _get(spec, "plan")
    if _number(_get(plan, "seeds_per_condition"), "plan.seeds_per_condition") != SEEDS_PER_CONDITION:
        raise Stop(f"STOP: seeds per condition is fixed at {SEEDS_PER_CONDITION} (D21 rule, 22 Oct); it may "
                   "not be reduced or raised per node")
    if list(_get(plan, "conditions")) != list(CONDITIONS):
        raise Stop(f"STOP: plan.conditions must be exactly {list(CONDITIONS)}")
    if _text(_get(plan, "split_policy"), "plan.split_policy") != SPLIT_POLICY:
        raise Stop(f"STOP: plan.split_policy must be {SPLIT_POLICY!r} (D21 measurement uses the vary split)")
    if int(_number(_get(plan, "configs"), "plan.configs")) != CONFIG_COUNT:
        raise Stop(f"STOP: plan.configs must be {CONFIG_COUNT} (baseline + the five standard E1 edits)")
    if int(_number(_get(plan, "default_runs_per_config"), "plan.default_runs_per_config")) != DEFAULT_RUNS_PER_CONFIG:
        raise Stop(f"STOP: plan.default_runs_per_config must be {DEFAULT_RUNS_PER_CONFIG} (determinism check)")
    candidates = _get(plan, "candidate_nodes")
    if not isinstance(candidates, list) or not candidates:
        raise Stop("STOP: plan.candidate_nodes is empty; refuses G.0-empty node lists")
    candidate_ids = []
    for i, node in enumerate(candidates):
        node_id = _no_placeholder(_get(node, "node_id"), f"plan.candidate_nodes[{i}].node_id")
        if not NODE_ID.fullmatch(node_id):
            raise Stop(f"STOP: plan.candidate_nodes[{i}].node_id={node_id!r} is not a harness node id")
        candidate_ids.append(node_id)
        _number(_get(node, "run_seconds"), f"{node_id}.run_seconds", minimum=1.0, maximum=RUN_SECONDS_CEILING)
        _no_placeholder(_get(node, "metric"), f"{node_id}.metric")
        if _text(_get(node, "direction"), f"{node_id}.direction") not in ("higher", "lower"):
            raise Stop(f"STOP: {node_id}.direction must be 'higher' or 'lower'")
        for key, floor in (("request_memory_mb", MEMORY_FLOOR_MB), ("request_disk_kb", DISK_FLOOR_KB)):
            value = int(_number(_get(node, key), f"{node_id}.{key}", minimum=1))
            if value < floor:
                raise Stop(f"STOP: {node_id}.{key}={value} is below the pre-declared floor {floor} "
                           f"(S2-C4 measured layout)")
        edits = _get(node, "edit_set")
        if not isinstance(edits, list) or len(edits) != E1_EDIT_COUNT:
            raise Stop(f"STOP: {node_id}.edit_set must carry the {E1_EDIT_COUNT} declared standard E1 edits "
                       "(D21 standard edit set); fewer is an author STOP, not a silently reduced set")
        seen = set()
        for j, edit in enumerate(edits):
            edit_id = _no_placeholder(_get(edit, "edit_id"), f"{node_id}.edit_set[{j}].edit_id")
            if edit_id in seen:
                raise Stop(f"STOP: {node_id}.edit_set has duplicate edit id {edit_id!r}")
            seen.add(edit_id)
            if _text(_get(edit, "kind"), f"{node_id}.edit_set[{j}].kind") not in ("code_diff", "hyperparameter"):
                raise Stop(f"STOP: {node_id}.edit_set[{j}].kind must be 'code_diff' or 'hyperparameter'")
            patch = _text(_get(edit, "patch_sha256"), f"{node_id}.edit_set[{j}].patch_sha256", SHA)
            if patch == PLACEHOLDER_SHA:
                raise Stop(f"STOP: {node_id}.edit_set[{j}].patch_sha256 is a placeholder")
        runner = _get(node, "runner")
        _no_placeholder(_get(runner, "module"), f"{node_id}.runner.module")
        _no_placeholder(_get(runner, "entrypoint"), f"{node_id}.runner.entrypoint")
        module_sha = _text(_get(runner, "module_sha256"), f"{node_id}.runner.module_sha256", SHA)
        if module_sha == PLACEHOLDER_SHA:
            raise Stop(f"STOP: {node_id}.runner.module_sha256 is a placeholder")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise Stop("STOP: plan.candidate_nodes contains duplicates")
    if set(candidate_ids) != set(census_nodes):
        raise Stop("STOP: plan.candidate_nodes must be exactly the nodes the G.0 census named; a node may be "
                   "neither added nor dropped silently (D21 uniform application)")

    # The chunk must be one of the pre-declared chunks for this plan.
    chunk = _get(spec, "chunk")
    chunk_id = _text(_get(chunk, "chunk_id"), "chunk.chunk_id", SAFE)
    node = _no_placeholder(_get(chunk, "node"), "chunk.node")
    condition = _text(_get(chunk, "condition"), "chunk.condition")
    seed_start = int(_number(_get(chunk, "seed_start"), "chunk.seed_start", minimum=0))
    seed_count = int(_number(_get(chunk, "seed_count"), "chunk.seed_count", minimum=0))
    plan_chunks = chunk_plan(plan)
    match = [c for c in plan_chunks if c["chunk_id"] == chunk_id]
    if not match:
        raise Stop(f"STOP: chunk {chunk_id!r} is not in the pre-declared chunk plan for these nodes")
    if (node, condition, seed_start, seed_count) != (match[0]["node"], match[0]["condition"],
                                                     match[0]["seed_start"], match[0]["seed_count"]):
        raise Stop(f"STOP: chunk {chunk_id!r} does not match the pre-declared chunk fields")
    selected = match[0]

    # Frozen environment pins.
    image = _get(spec, "image")
    if _text(_get(image, "digest"), "image.digest") != IMAGE_DIGEST:
        raise Stop("STOP: image.digest must be the frozen v1 gpu digest (one image per table)")
    if _get(image, "versions_markers") != IMAGE_MARKERS:
        raise Stop("STOP: image.versions_markers must equal the frozen image markers")
    paper = _get(spec, "paper")
    if _text(_get(paper, "repo"), "paper.repo") != PAPER_REPO:
        raise Stop("STOP: paper.repo must be the Agent_paper_B repository")
    _no_placeholder(_get(paper, "commit"), "paper.commit")
    _text(_get(paper, "commit"), "paper.commit", COMMIT)
    harness = _get(spec, "harness")
    if _text(_get(harness, "repo"), "harness.repo") != HARNESS_REPO:
        raise Stop("STOP: harness.repo must be the autoresearch_harness repository")
    harness_commit = _text(_no_placeholder(_get(harness, "commit"), "harness.commit"),
                           "harness.commit", COMMIT)
    if harness_commit == HARNESS_EXAM_PIN:
        raise Stop("STOP: the EXAM harness pin cannot serve the T1 table family; pin the T1 label-table harness")
    _no_placeholder(_get(harness, "pin_evidence"), "harness.pin_evidence")
    env = _get(spec, "env")
    if _text(_get(env, "python"), "env.python") != "/opt/r1/envs/trackp/bin/python":
        raise Stop("STOP: env.python must be the frozen image's torch environment")
    libraries = _get(env, "libraries")
    if not isinstance(libraries, dict) or not libraries:
        raise Stop("STOP: env.libraries must be a nonempty object (D21 records the library versions)")
    for key in ("python", "numpy", "scikit-learn", "torch"):
        if key not in libraries:
            raise Stop(f"STOP: env.libraries must pin {key} (D21 manifest requirement)")
    for key, value in libraries.items():
        _text(key, "env.libraries key")
        if not VERSION.fullmatch(_no_placeholder(value, f"env.libraries[{key}]")):
            raise Stop(f"STOP: env.libraries[{key}] is not an exact version string")

    # Shared G.1b-family proposer pins (declared, not exercised by this training-run chunk).
    proposer = _get(spec, "proposer_environment")
    if _get(proposer, "server") != SERVER_SETTING:
        raise Stop("STOP: proposer_environment.server must equal the frozen 32,768-context exam server setting "
                   "(R1-SWEEP2-SETTINGS (1))")
    model = _get(proposer, "model")
    want_model = dict(PICK_GGUF, use=MODEL_USE)
    if model != want_model:
        raise Stop("STOP: proposer_environment.model must be the pinned pick GGUF, declared only "
                   "(use='declared-only-no-download')")
    if scope_of_server(proposer["server"]) != "32k-exam":
        raise Stop("STOP: proposer server setting is not the 32,768-context exam setting")

    measurement = _get(spec, "measurement")
    if int(_number(_get(measurement, "workers"), "measurement.workers")) != WORKERS:
        raise Stop("STOP: measurement.workers must be 1 (serialised GPU runs are the D21 determinism premise)")
    if _get(measurement, "seed_bases") != SEED_BASES:
        raise Stop(f"STOP: measurement.seed_bases must be {SEED_BASES} (E1/D21 seed convention, disjoint from "
                   "the audit seeds 7001-7010 and the exam seeds 9001+)")
    for key, const in (("chunk_overhead_factor", CHUNK_OVERHEAD_FACTOR), ("reserved_seconds", RESERVED_SECONDS)):
        if _number(_get(measurement, key), f"measurement.{key}") != const:
            raise Stop(f"STOP: measurement.{key} must be the pre-declared {const}")

    requirements = _get(spec, "requirements")
    for key, want in (("cloud_site", CLOUD_SITE), ("gpu_device_name", GPU_MODEL), ("arch", "X86_64"),
                      ("opsys", "LINUX"), ("min_cpus", MIN_CPUS), ("cpu_family", CPU_FAMILY),
                      ("cpu_model_number", CPU_MODEL_NUMBER), ("cpu_model_contains", CPU_MODEL_CONTAINS)):
        got = _get(requirements, key)
        if got != want:
            raise Stop(f"STOP: requirements.{key} must be {want!r} (one pinned GPU and CPU class per table)")
    if "requires_etp_ceph" in requirements:
        raise Stop("STOP: NEMO2 slots do not advertise ProvidesEtpCeph; outputs transfer and are sealed later")
    if "machine_regex" in requirements:
        raise Stop("STOP: pin the CPU class, not a machine regex (S2-C2 reviewed pattern)")

    # Caps: pre-declared, may be lowered, never raised; the projection is checked against them.
    caps = _get(spec, "caps")
    for key, const in (("max_total_gpu_hours", CAP_TOTAL_GPU_HOURS),
                       ("max_chunk_wall_hours", CAP_CHUNK_WALL_HOURS),
                       ("max_chunk_wall_seconds", MAX_CHUNK_WALL_SECONDS)):
        value = _number(_get(caps, key), f"caps.{key}", minimum=1)
        if value > const:
            raise Stop(f"STOP: caps.{key}={value:g} raises the pre-declared {const:g}; a raise needs a new "
                       "author row amending R1-SWEEP2-SETTINGS (5)")
    proj = projection(plan)
    if proj["total_gpu_hours"] > caps["max_total_gpu_hours"]:
        raise Stop(f"STOP: projected {proj['total_gpu_hours']:.2f} GPU-h over {proj['candidate_nodes']} candidate "
                   f"nodes exceeds the pre-declared {caps['max_total_gpu_hours']:g} GPU-h cap. This is the author "
                   "STOP of R1-SWEEP2-SETTINGS (5): do not trim the 30 seeds (D21), do not drop nodes silently; "
                   "report the per-node projection and stop")
    if proj["max_chunk_wall_seconds"] > caps["max_chunk_wall_seconds"]:
        raise Stop(f"STOP: a chunk projects {proj['max_chunk_wall_seconds']} s wall, above the pre-declared "
                   f"{caps['max_chunk_wall_seconds']} s cap")
    if proj["max_chunk_wall_seconds"] > int(CAP_CHUNK_WALL_HOURS * 3600):
        raise Stop(f"STOP: a chunk projects above the {CAP_CHUNK_WALL_HOURS:g} h wall cap "
                   "(R1-SWEEP2-SETTINGS (5))")
    if proj["per_node_wall_hours"] > CAP_CHUNK_WALL_HOURS:
        raise Stop(f"STOP: one node projects {proj['per_node_wall_hours']:.2f} h of chunks, above the "
                   f"{CAP_CHUNK_WALL_HOURS:g} h wall cap (R1-SWEEP2-SETTINGS (5))")
    if proj["slots_required_for_48h_wall"] > MAX_CONCURRENT_SLOTS:
        raise Stop(f"STOP: the unit needs {proj['slots_required_for_48h_wall']} concurrent L40S slots to finish "
                   f"inside the 48 h cap, above the pre-declared {MAX_CONCURRENT_SLOTS}")
    return {"run_id": run_id, "label": ENGINEERING_ONLY, "spec": spec, "plan": plan,
            "chunk": selected, "projection": proj}


def scope_of_server(server: dict) -> str:
    """The declared context must be the 32,768-context exam setting; returns a short tag used by the validator."""
    if server.get("ctx") == 32768 and server.get("n_gpu_layers") == 999 and server.get("n_parallel") == 1:
        return "32k-exam"
    return "off-setting"


# --------------------------------------------------------------------------- container-side identity/run helpers
def _env_python(spec: dict) -> str:
    path = spec["env"]["python"]
    if not Path(path).is_file():
        raise Stop(f"STOP: pinned environment python missing: {path}")
    return path


def _run_python(python: str, code: str, *, env: dict | None = None, timeout: int = 180) -> str:
    res = subprocess.run([python, "-B", "-c", code], capture_output=True, text=True, timeout=timeout,
                         env=env or dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if res.returncode != 0:
        raise Stop(f"STOP: python probe failed: {res.stderr.strip()[:400]}")
    return res.stdout.strip()


def image_identity(spec: dict) -> dict:
    versions = Path("/opt/r1/VERSIONS.txt")
    if not versions.is_file():
        raise Stop("STOP: /opt/r1/VERSIONS.txt missing (not the frozen v1 gpu image)")
    text = versions.read_text()
    for key, value in spec["image"]["versions_markers"].items():
        if not re.search(rf"^{re.escape(key)}={re.escape(value)}$", text, re.M):
            raise Stop(f"STOP: image identity marker {key}={value} missing")
    binary = Path(spec["proposer_environment"]["server"]["binary"])
    if not binary.is_file():
        raise Stop(f"STOP: llama-server binary {binary} missing (not the frozen image)")
    got = hashlib.sha256(binary.read_bytes()).hexdigest()
    if got != LLAMA_SERVER_SHA256:
        raise Stop("STOP: llama-server binary sha256 differs from the frozen image pin")
    return {"digest": spec["image"]["digest"], "versions_sha256": hashlib.sha256(versions.read_bytes()).hexdigest(),
            "llama_server_sha256": got, "markers": spec["image"]["versions_markers"]}


def host_identity() -> dict:
    name = socket.gethostname()
    try:
        fqdn = socket.getfqdn(name)
    except OSError:
        fqdn = name
    cpus = os.cpu_count() or 0
    if cpus < MIN_CPUS:
        raise Stop(f"STOP: landed with {cpus} CPUs, below the pinned class {MIN_CPUS}")
    return {"hostname": name, "fqdn": fqdn, "logical_cpus": cpus}


def gpu_identity(spec: dict) -> dict:
    code = ("import json,torch\nok=torch.cuda.is_available()\nout={'cuda_available':ok}\n"
            "if ok:\n p=torch.cuda.get_device_properties(0)\n"
            " out.update(name=p.name,uuid=str(getattr(p,'uuid',None)),total_memory=p.total_memory,"
            "major=p.major,minor=p.minor,count=torch.cuda.device_count())\nprint(json.dumps(out))\n")
    info = json.loads(_run_python(_env_python(spec), code, timeout=300).splitlines()[-1])
    if not info.get("cuda_available"):
        raise Stop("STOP: CUDA unavailable in the job")
    if GPU_MODEL not in str(info.get("name", "")):
        raise Stop(f"STOP: GPU {info.get('name')!r} is not the pinned model {GPU_MODEL!r}")
    if int(info.get("total_memory") or 0) < GPU_MIN_TOTAL_MEMORY_BYTES:
        raise Stop(f"STOP: GPU reports {info.get('total_memory')} bytes, below the pinned class")
    return {"name": info["name"], "uuid": info.get("uuid") or _proc_gpu_uuid(), "driver": _driver_version(),
            "total_memory": info.get("total_memory"),
            "compute_capability": [info.get("major"), info.get("minor")], "device_count": info.get("count")}


def _proc_gpu_uuid() -> str | None:
    for path in sorted(Path("/proc/driver/nvidia/gpus").glob("*/information")):
        match = re.search(r"^GPU UUID:\s*(\S+)$", path.read_text(errors="replace"), re.M)
        if match:
            return match.group(1)
    return None


def _driver_version() -> str | None:
    path = Path("/proc/driver/nvidia/version")
    if not path.is_file():
        return None
    match = re.search(r"Kernel Module\s+(\d+\.\d+(?:\.\d+)?)", path.read_text(errors="replace"))
    return match.group(1) if match else None


def cpu_identity(spec: dict) -> dict:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        raise Stop("STOP: /proc/cpuinfo missing (not a batch Linux host)")
    text = cpuinfo.read_text(errors="replace")
    name = re.search(r"^model name\s*:\s*(.+)$", text, re.M)
    model = name.group(1).strip() if name else "unknown"
    family = re.search(r"^cpu family\s*:\s*(\d+)$", text, re.M)
    number = re.search(r"^model\s*:\s*(\d+)$", text, re.M)
    cores = len(re.findall(r"^processor\s*:", text, re.M))
    got = (int(family.group(1)) if family else None, int(number.group(1)) if number else None)
    if got != (CPU_FAMILY, CPU_MODEL_NUMBER) or CPU_MODEL_CONTAINS not in model:
        raise Stop(f"STOP: CPU {model!r} family/model {got} is not the pinned class "
                   f"{CPU_FAMILY}/{CPU_MODEL_NUMBER} {CPU_MODEL_CONTAINS!r}")
    requirements = spec["requirements"]
    if cores < int(requirements["min_cpus"]):
        raise Stop(f"STOP: landed with {cores} CPUs, below the pinned class {requirements['min_cpus']}")
    return {"model": model, "family": got[0], "model_number": got[1], "logical_cpus": cores}


def library_versions(spec: dict) -> dict:
    keys = sorted(spec["env"]["libraries"])
    code = ("import json,sys\nfrom importlib import metadata\nout={'python':sys.version.split()[0]}\n"
            f"for name in {keys!r}:\n"
            " if name=='python': continue\n"
            " try: out[name]=metadata.version(name)\n"
            " except metadata.PackageNotFoundError: out[name]=None\n"
            "print(json.dumps(out))\n")
    got = json.loads(_run_python(_env_python(spec), code, timeout=180).splitlines()[-1])
    for key, want in spec["env"]["libraries"].items():
        if got.get(key) != want:
            raise Stop(f"STOP: pinned library {key}={want} but the job environment has {got.get(key)!r}")
    return got


def clone_at(repo: str, commit: str, dest: Path) -> dict:
    if dest.exists():
        raise Stop(f"STOP: scratch checkout {dest} already exists (fresh scratch required)")
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", repo], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", "origin", commit], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)
    got = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if got != commit:
        raise Stop(f"STOP: retrieved commit {got} != pinned {commit}")
    status = subprocess.check_output(["git", "-C", str(dest), "status", "--porcelain"], text=True).strip()
    return {"repo": repo, "commit": got, "dirty": bool(status)}


def verify_wrapper_identity(paper_dir: Path) -> dict:
    """The transferred wrapper must be byte-identical to the one in the pinned paper commit."""
    pinned = paper_dir / "sweep2" / "g1b" / "g1b_lib.py"
    if not pinned.is_file():
        raise Stop("STOP: pinned paper commit does not carry sweep2/g1b/g1b_lib.py")
    want = hashlib.sha256(pinned.read_bytes()).hexdigest()
    got = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if got != want:
        raise Stop("STOP: transferred g1b_lib.py differs from the pinned paper commit (code identity)")
    return {"paper_g1b_lib_sha256": got}


def load_runner(spec: dict, node: dict, paper_dir: Path, harness_dir: Path) -> tuple[object, dict]:
    """Import the reviewed T1 measurement runner from the pinned paper commit and verify its sha256."""
    import importlib
    import importlib.util
    module = node["runner"]["module"]
    entrypoint = node["runner"]["entrypoint"]
    sys.path.insert(0, str(paper_dir))
    os.environ["PYTHONPATH"] = str(paper_dir)
    os.environ["AR_HARNESS_ROOT"] = str(harness_dir)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        found = importlib.util.find_spec(module)
    except (ImportError, ValueError) as exc:
        raise Stop(f"STOP: runner module {module!r} is not importable from the pinned paper commit: {exc}") from exc
    if found is None or not found.origin:
        raise Stop(f"STOP: runner module {module!r} is not present in the pinned paper commit")
    origin = Path(found.origin).resolve()
    if paper_dir.resolve() not in origin.parents and origin != paper_dir.resolve():
        raise Stop(f"STOP: runner module resolves outside the pinned paper commit: {origin}")
    got = hashlib.sha256(origin.read_bytes()).hexdigest()
    if got != node["runner"]["module_sha256"]:
        raise Stop("STOP: runner module sha256 differs from the spec pin")
    mod = importlib.import_module(module)
    fn = getattr(mod, entrypoint, None)
    if not callable(fn):
        raise Stop(f"STOP: runner module has no callable {entrypoint!r}")
    return fn, {"module": module, "entrypoint": entrypoint, "sha256": got, "origin": str(origin)}


def _check_rule_constants(paper_dir: Path) -> dict:
    """The pinned measurement report code must still execute the 22 Oct D21 rule (no silent drift)."""
    sys.path.insert(0, str(paper_dir))
    try:
        from r1.noise import e1_report  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise Stop(f"STOP: cannot import r1.noise.e1_report from the pinned paper commit: {exc}") from exc
    pairs = {"minimum material edits": (e1_report.MIN_EDITS, D21_MIN_MATERIAL_EDITS),
             "minimum mean P(wrong)": (e1_report.QUALIFY_P, D21_MIN_MEAN_P_WRONG),
             "minimum effect": (e1_report.MIN_EFFECT, D21_MIN_EFFECT)}
    mismatched = {k: {"pinned": v[0], "declared": v[1]} for k, v in pairs.items() if v[0] != v[1]}
    if mismatched:
        raise Stop(f"STOP: the pinned r1.noise.e1_report no longer implements the declared D21 rule: {mismatched}")
    return {"constants": {k: v[0] for k, v in pairs.items()}}


def _write_sums(root: Path, names) -> None:
    lines = []
    for name in names:
        path = root / name
        if not path.exists():
            continue
        files = [path] if path.is_file() else [p for p in sorted(path.rglob("*")) if p.is_file()]
        for file in files:
            lines.append(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(root)}")
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def _tar_dir(src: Path, dest: Path) -> None:
    if not src.exists():
        dest.write_bytes(b"")
        return
    subprocess.run(["tar", "-cf", str(dest), src.name], cwd=str(src.parent), check=True)


def run_job(spec_path: Path) -> dict:
    loaded = validate_spec(load_spec(spec_path))
    spec, plan, chunk, proj = loaded["spec"], loaded["plan"], loaded["chunk"], loaded["projection"]
    node = next(n for n in plan["candidate_nodes"] if n["node_id"] == chunk["node"])
    out = Path("out")
    out.mkdir(parents=True, exist_ok=True)
    record_path = Path("job_record.json")
    if record_path.is_file() and record_path.stat().st_size:
        raise Stop("STOP: job_record.json already exists; this measurement chunk is not resumable in place")
    started = time.time()
    record = {"schema": RECORD_SCHEMA, "run_id": loaded["run_id"], "chunk": chunk, "label": ENGINEERING_ONLY,
              "output_use": "ENGINEERING_ONLY G.1b noise-floor measurement; no labels read; not evidence; not a "
                            "label table",
              "spec_sha256": hashlib.sha256(Path(spec_path).read_bytes()).hexdigest(),
              "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
              "projection": proj, "caps": spec["caps"],
              "pins": {"paper": {"repo": spec["paper"]["repo"], "commit": spec["paper"]["commit"]},
                       "harness": {"repo": spec["harness"]["repo"], "commit": spec["harness"]["commit"],
                                   "pin_evidence": spec["harness"]["pin_evidence"]},
                       "proposer_environment": spec["proposer_environment"],
                       "measurement": spec["measurement"], "requirements": spec["requirements"]},
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    record["image"] = image_identity(spec)
    record["host"] = host_identity()
    record["gpu"] = gpu_identity(spec)
    record["cpu"] = cpu_identity(spec)
    record["libraries"] = library_versions(spec)
    paper_dir, harness_dir = Path("paper"), Path("harness")
    record["paper_at_pin"] = clone_at(spec["paper"]["repo"], spec["paper"]["commit"], paper_dir)
    record["harness_at_pin"] = clone_at(spec["harness"]["repo"], spec["harness"]["commit"], harness_dir)
    record["wrapper_identity"] = verify_wrapper_identity(paper_dir)
    record["d21_rule"] = _check_rule_constants(paper_dir)
    runner, runner_info = load_runner(spec, node, paper_dir, harness_dir)
    record["runner"] = runner_info

    runs = chunk_runs(plan, chunk)
    deadline = started + int(chunk["walltime_s"]) - 120
    per_run_timeout = max(60, int(round(3 * float(node["run_seconds"]))))  # runbook G.1: 3 x measured run time
    out_tmp = Path("scratch")
    out_tmp.mkdir(exist_ok=True)
    runs_path = out / "runs.jsonl"
    completed, failed = 0, []
    for run in runs:
        if time.time() > deadline:
            failed.append({"reason": "chunk deadline reached before the run started", "run": run})
            break
        try:
            row = runner(node=node["node_id"], config_id=run["config"], edit=run["edit"],
                         condition=run["condition"], train_seed=run["train_seed"],
                         split_seed=run["split_seed"], node_root=str(harness_dir / "nodes" / node["node_id"]),
                         artifact_dir=str(out_tmp / "artifacts"), step_budget=node.get("step_budget"),
                         timeout_seconds=per_run_timeout)
        except Exception as exc:  # noqa: BLE001 - a failed run is recorded, not hidden
            row = {"node": node["node_id"], "config": run["config"], "condition": run["condition"],
                   "train_seed": run["train_seed"], "split_seed": run["split_seed"], "metric": None,
                   "success": False, "failure": f"runner exception: {exc}", "edit_applied": None,
                   "wall_seconds": None}
        if not isinstance(row, dict) or not {"node", "config", "condition", "metric", "success"} <= set(row):
            raise Stop("STOP: the runner returned a row that is not E1-schema (keep the outputs)")
        with runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        completed += row.get("success") is True
    record["runs"] = {"expected": len(runs), "written": len(runs) - len(failed), "successful": completed,
                      "failures": failed, "per_run_timeout_seconds": per_run_timeout}
    (out / "edits.json").write_text(json.dumps({node["node_id"]: [
        {"symbol": e["edit_id"], "old": "baseline", "new": e.get("description", e["edit_id"]),
         "kind": e["kind"], "patch_sha256": e["patch_sha256"]} for e in node["edit_set"]]}, indent=1) + "\n")
    determinism = determinism_check([json.loads(line) for line in runs_path.read_text().splitlines()]) \
        if runs_path.is_file() else {"deterministic": False, "configs": {}}
    record["determinism"] = determinism
    manifest = {"schema": RUN_SCHEMA, "label": ENGINEERING_ONLY, "run_id": loaded["run_id"], "chunk": chunk,
                "seed_bases": spec["measurement"]["seed_bases"], "seeds_per_condition": plan["seeds_per_condition"],
                "split_policy": plan["split_policy"], "nodes": [node["node_id"]],
                "edits": {node["node_id"]: [e["edit_id"] for e in node["edit_set"]]},
                "host": {**record["host"], "gpu": record["gpu"], "cpu": record["cpu"],
                         "libraries": record["libraries"], "image": record["image"]["digest"],
                         "image_versions_sha256": record["image"]["versions_sha256"],
                         "paper_commit": spec["paper"]["commit"], "harness_commit": spec["harness"]["commit"],
                         "runner_sha256": runner_info["sha256"]},
                "projection": proj, "caps": spec["caps"],
                "note": "ENGINEERING_ONLY G.1b noise floor; no labels; D21 rule applied offline by the pinned "
                        "r1.noise.e1_report"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record["seconds"] = round(time.time() - started, 1)
    if failed:
        record["stop"] = f"{len(failed)} run(s) did not complete within the chunk; outputs preserved"
        record_path.write_text(json.dumps(record, indent=1) + "\n")
        _tar_dir(out, Path("out.tar"))
        _write_sums(Path("."), ("out", "out.tar", "job_record.json"))
        raise Stop(f"STOP: {record['stop']} (no retry; keep the chunk for diagnosis)")
    if chunk["condition"] == "default" and not determinism["deterministic"]:
        record["stop"] = "fixed-seed determinism failed; D21 verdict cannot be published for this node"
        record_path.write_text(json.dumps(record, indent=1) + "\n")
        _tar_dir(out, Path("out.tar"))
        _write_sums(Path("."), ("out", "out.tar", "job_record.json"))
        raise Stop(f"STOP: {record['stop']}")
    record_path.write_text(json.dumps(record, indent=1) + "\n")
    _tar_dir(out, Path("out.tar"))
    _write_sums(Path("."), ("out", "out.tar", "job_record.json"))
    return record


# --------------------------------------------------------------------------- offline summary + seal
def summarise(run_dir: Path, plan: dict, paper_dir: Path | None = None) -> dict:
    """Verify full coverage, then apply the pinned r1.noise.e1_report rule; double-check with d21_qualify."""
    run_dir = Path(run_dir)
    rows = [json.loads(line) for line in (run_dir / "runs.jsonl").read_text().splitlines() if line.strip()]
    edits = json.loads((run_dir / "edits.json").read_text())
    nodes = [n["node_id"] for n in plan["candidate_nodes"]]
    seeds = int(plan["seeds_per_condition"])
    keys = {(n, c, cond, ts, ss) for n in nodes for c in [f"c{k}" for k in range(CONFIG_COUNT)]
            for cond in CONDITIONS for ts, ss in
            [((SEED_BASES["train"] + i) if cond in ("train", "joint") else None,
              (SEED_BASES["split"] + i) if cond in ("split", "joint") else None) for i in range(seeds)]}
    default_keys = {(n, c, cond, None, None) for n in nodes for c in [f"c{k}" for k in range(CONFIG_COUNT)]
                    for cond in ("default", "default_repeat")}
    seen = {}
    for row in rows:
        key = (row.get("node"), row.get("config"), row.get("condition"), row.get("train_seed"),
               row.get("split_seed"))
        if key in seen:
            raise Stop(f"STOP: duplicate run {key}; coverage must be exact")
        seen[key] = row
    missing = (keys | default_keys) - set(seen)
    extra = set(seen) - (keys | default_keys)
    if missing or extra:
        raise Stop(f"STOP: run coverage is not exact: {len(missing)} missing, {len(extra)} extra")
    det = determinism_check(rows)
    if not det["deterministic"]:
        return {"schema": "g1b_summary/1", "label": ENGINEERING_ONLY, "determinism": det,
                "verdicts": {n: {"qualifies_D21": False, "reason": "fixed-seed determinism failed"}
                             for n in nodes}}
    if paper_dir is None:
        paper_dir = Path(os.environ.get("G1B_PAPER_ROOT", ".")).resolve()
    _check_rule_constants(paper_dir)
    sys.path.insert(0, str(paper_dir))
    from r1.noise import e1_report  # noqa: PLC0415
    pinned = e1_report.summarise(run_dir)
    verdicts = {}
    for node in nodes:
        info = pinned["nodes"].get(node, {})
        edit_stats_list = [{"material": bool(e.get("material")), "p_wrong": e.get("p_model", float("nan")),
                            "delta_hat_J": e.get("delta_hat_J")} for e in info.get("edits", [])]
        ours = d21_qualify(edit_stats_list, info.get("sigma_joint", float("nan")), seeds)
        if bool(info.get("proposal", {}).get("qualifies_D21")) != ours["qualifies_D21"]:
            raise Stop(f"STOP: D21 rule drift on node {node}: pinned report says "
                       f"{info.get('proposal', {}).get('qualifies_D21')}, the declared rule says "
                       f"{ours['qualifies_D21']}")
        verdicts[node] = dict(ours, e1_report_proposed_split=info.get("proposal", {}).get("split_policy"),
                              n_edits=info.get("summary", {}).get("n_edits"),
                              n_resolved=info.get("summary", {}).get("n_resolved"),
                              median_wall_seconds=info.get("median_wall_seconds"))
    summary = {"schema": "g1b_summary/1", "label": ENGINEERING_ONLY, "run_dir": str(run_dir),
               "run_id": None, "split_policy": SPLIT_POLICY,
               "rule": d21_qualify([], 0.0, seeds)["rule"], "determinism": det, "verdicts": verdicts,
               "screening_funnel": {"measured": len(nodes),
                                    "qualified": sum(1 for v in verdicts.values() if v["qualifies_D21"]),
                                    "failed_determinism": 0}}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (run_dir / "tables.md").write_text(e1_report.markdown(pinned, {}) + "\n")
    return summary


def _sealed_target(run_id: str, chunk_id: str) -> Path:
    for name in (run_id, chunk_id):
        if not SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    base = (SEALED_ROOT / run_id / chunk_id).resolve()
    want = SEALED_ROOT / run_id / chunk_id
    if not (base == want or want in base.parents):
        raise Stop(f"STOP: sealed target {base} is outside {SEALED_ROOT}/<run_id>/<chunk_id>")
    probe = base
    while probe != Path("/"):
        if probe.exists() and probe.is_symlink():
            raise Stop(f"STOP: sealed path component is a symlink: {probe}")
        probe = probe.parent
    return base


def seal(job_output: Path, run_id: str, chunk_id: str) -> dict:
    src = Path(job_output).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("label") != ENGINEERING_ONLY:
        raise Stop("STOP: only ENGINEERING_ONLY G.1b chunks may be sealed")
    if record.get("run_id") != run_id or record.get("chunk", {}).get("chunk_id") != chunk_id:
        raise Stop("STOP: job record does not match the requested run/chunk")
    if not str(record.get("image", {}).get("digest", "")).startswith("ghcr.io/"):
        raise Stop("STOP: job record has no pinned image digest")
    if not record.get("host", {}).get("fqdn") or not record.get("gpu", {}).get("name"):
        raise Stop("STOP: job record has no host/GPU identity")
    sums = src / "SHA256SUMS"
    if not sums.is_file():
        raise Stop("STOP: job output has no SHA256SUMS")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=str(src), capture_output=True).returncode != 0:
        raise Stop("STOP: transferred SHA256SUMS verification failed")
    target = _sealed_target(run_id, chunk_id)
    if target.exists():
        raise Stop(f"STOP: sealed target exists; no overwrite ({target})")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out", "job_record.json", "SHA256SUMS", "g1b_run.log", "out.tar"):
        path = src / name
        if path.exists():
            (shutil.copytree if path.is_dir() else shutil.copy2)(path, target / name)
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(target)}"
             for p in sorted(target.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    (target / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    receipt = {"schema": "g1b_seal_receipt/1", "run_id": run_id, "chunk_id": chunk_id,
               "sealed_path": str(target), "label": record["label"],
               "image_digest": record["image"]["digest"], "paper_commit": record["pins"]["paper"]["commit"],
               "harness_commit": record["pins"]["harness"]["commit"],
               "host": record["host"]["fqdn"], "gpu": record["gpu"]["name"],
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec")
    p = sub.add_parser("plan-chunks"); p.add_argument("spec")
    r = sub.add_parser("run"); r.add_argument("spec")
    s = sub.add_parser("summarise"); s.add_argument("run_dir"); s.add_argument("spec")
    s.add_argument("--paper-root", default=None)
    z = sub.add_parser("seal"); z.add_argument("job_output"); z.add_argument("--run-id", required=True)
    z.add_argument("--chunk-id", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        loaded = validate_spec(load_spec(Path(a.spec)))
        print(json.dumps({"ok": True, "run_id": loaded["run_id"], "label": loaded["label"],
                          "chunk": loaded["chunk"], "projection": loaded["projection"]}, indent=1))
        return 0
    if a.cmd == "plan-chunks":
        plan = _get(load_spec(Path(a.spec)), "plan")
        print(json.dumps({"chunks": chunk_plan(plan), "projection": projection(plan)}, indent=1))
        return 0
    if a.cmd == "run":
        record = run_job(Path(a.spec))
        print(json.dumps({"ok": True, "chunk": record["chunk"], "host": record["host"]["fqdn"],
                          "gpu": record["gpu"]["name"], "runs": record["runs"]}, indent=1))
        return 0
    if a.cmd == "summarise":
        plan = _get(load_spec(Path(a.spec)), "plan")
        print(json.dumps(summarise(Path(a.run_dir), plan, Path(a.paper_root) if a.paper_root else None), indent=1))
        return 0
    print(json.dumps(seal(Path(a.job_output), a.run_id, a.chunk_id), indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
