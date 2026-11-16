#!/usr/bin/env python3
"""S2-C3b — (g)4 D28 liveness of the pick on NEMO2 L40S + prompt-length re-measurement.

ENGINEERING_ONLY. Authority: PLAN `R1-SWEEP2-SETTINGS` (4) on `author-decisions-20261116` @ `4da73306`
("pick on NEMO2 L40S, D28 liveness on the eight nodes, re-measure prompt lengths with the pick's tokenizer;
the sweep-2 wrapper restores `min_live_nodes 8`; no exemption"), `R1-SWEEP-HOST-HTC`, and
`R1-MAIN-PROPOSER` (g)4. Run plan: `docs/runbooks-16nov` @ `b3289232` §3 S2-C3b, context 32,768 (R1-SWEEP2-SETTINGS (1)).

One job == one owned llama-server at the exam setting (ctx 32,768, `-ngl 999`, `-np 1`, `--jinja`,
`{"enable_thinking":false}`, q8_0 K/V, `cache_prompt` false) that (1) runs the sweep-1 D28 liveness protocol through
`python -m r1.liveness` on all eight sweep-1 nodes (2 instances, W = 10, memory `append_only_summary`) and requires
all eight nodes to pass (`min_live_nodes 8`; a shortfall STOPs with the evidence persisted), then (2) re-measures the
sweep-2 manager prompt lengths with the **pick's tokenizer** through the server's `/apply-template` + `/tokenize`
endpoints for the three prompt classes (trial-1, declared 11-record memory-on, and the **W = 20 / 19-record longest
class**) and compares them with the sweep-1 prompt-length record that is pinned in the paper checkout (the sweep-1
D28 liveness ledgers' per-call `usage.prompt_tokens`, the recorded budget-12 1,345-token figure and the **true
recorded W = 20 maximum 1,886 tokens** over the 54 rerun-2 root ledgers).  The 1,345 figure belongs to the 14 Oct
rerun-2 prompt set and is explicitly *not* claimed to be the sweep-2 prompt text (openml_breast_w's trial-1 text
differs: rerun-2 `d31c77a3…`/483 tokens vs the 27 Oct liveness/sweep-2 text `61aa9226…`/482 tokens).

Pins/image/host/GPU/CPU/model/server/tar/seal are reused from the reviewed S2-C2 wrapper (`s2_c2_lib.py`); this
module imports it rather than re-implementing them. The paper commit is the reviewed main `9ae6d877` (the sweep-1
records and the `r1.liveness` path are unchanged between it and the unit branch — checked). No B.2 audit runs, no
seed 7001-7010 is touched, no label is read, and nothing here is evidence.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import s2_c2_lib as c2  # noqa: E402

SCHEMA = "s2_c3b/v1"
RECORD_SCHEMA = "s2_c3b_job_record/1"
SEAL_RECEIPT_SCHEMA = "s2_c3b_seal_receipt/1"
CHUNK_ID = "liveness-prompt"

# --- frozen deployment pins (S2-C1 v1 gpu image; R1-SWEEP2-SETTINGS (1); R1-MAIN-PROPOSER (b)/(g)4) -----------
V1_GPU_DIGEST_PREFIX = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35"
FROZEN_LLAMA_SERVER_SHA256 = "f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0"
HARNESS_COMMIT = c2.B2_HARNESS  # a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 (B2 harness, cache_prompt false)
PAPER_COMMIT = "9ae6d87783f53f9da27200869085c9ed0e7697e2"  # reviewed main (S2-M2); r1.liveness unchanged
ALLOWED_PAPER_COMMITS = (PAPER_COMMIT,)
PICK_GGUF_SHA256_PREFIX = "2959c1b0"
PICK_GGUF_SHA256 = "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75"
PICK_ALIAS = "gemma4_31b"

# --- exam server setting (R1-SWEEP2-SETTINGS (1); validated by the S2-C2 validator via _c2_view) --------------
CTX = c2.CTX  # 32,768
NGL = c2.NGL  # 999
NP = c2.NP  # 1

# --- D28 liveness protocol (sweep 1 frozen; R1-SWEEP2-SETTINGS (4)) ------------------------------------------
LIVENESS_NODES = c2.LIVENESS_NODES
MIN_LIVE_NODES = c2.MIN_LIVE_NODES  # 8 - all eight sweep-1 nodes, no exemption
MAX_PARSE_FAILURE_RATE = c2.MAX_PARSE_FAILURE_RATE
LIVENESS_INSTANCES = 2
LIVENESS_RUNS = 10
LIVENESS_MEMORY_MODE = "append_only_summary"
TRANSPORT_MAX_ATTEMPTS = 3  # sweep-1 D28 liveness manifest (results/r1/engineering/liveness_c3_20261027T152425Z)
LIVENESS_REPORT_SCHEMA = "r1.liveness/2"  # pinned `r1/liveness/check.py` output schema

# --- seeds --------------------------------------------------------------------------------------------------
# The sweep-1/2 instance seed law is pinned twice: in the paper repo (`r1/headroom/e1b_collect._instance_seed`) and,
# for the offline checks here, mirrored in `instance_seed`.  R1-MAIN-PROPOSER (b) fixes sweep-2's instance seeds to
# sweep 1's ("the same instance seeds as sweep 1 ... fixed per (node, k)"), so the sweep-2 universe is derived, not
# stored as a list; its SHA-256 is pinned in the spec and recomputed here.
SWEEP_INSTANCE_K = 18  # 18 instances per node (sweep 1 and sweep 2)
RESERVED_AUDIT_SEEDS = tuple(range(7001, 7011))  # B.2 audit label+evaluation seeds; never touched here
G1B_SEED_BLOCK = (8001, 8010)  # RUNBOOK G.1b training-seed block (also kept clear)
# The exam seed block is 9001-9303 (Stage A/B 9001+, B1 9101+, B2 9201+); it is an interval, not "9001+" as an
# unbounded claim.  The collision guard below is nevertheless open-ended (any declared seed >= 9001 STOPs), so a
# future exam-block extension is covered even though the recorded block ends at 9303.
EXAM_SEED_BLOCK = (9001, 9303)
PROMPT_MEASUREMENT_SEEDS = {node: 6100 + i + 1 for i, node in enumerate(LIVENESS_NODES)}
LIVENESS_SEED_POLICY = "sweep1_d28_reuse"
SWEEP2_INSTANCE_SEED_UNIVERSE_SHA256 = \
    "0d7f0e599ecc88f1da6c3724067e319f5714df4d2b0f415833a2b8fafaa7843d"
SWEEP1_INDEX_PATH = "results/r1/pilot/C3_sweep_index_20261028T033315Z.json"
SWEEP1_INDEX_SHA256 = "812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab"
SWEEP1_INSTANCE_SEED_SOURCE_PATH = "r1/headroom/e1b_collect.py"
SWEEP1_INSTANCE_SEED_SOURCE_SHA256 = "0001260442f9647461fd867a53fb74867a2b0e65810d9547eeb093a39e4b3271"

# --- sweep-1 records the re-measurement compares against (pinned paths + SHA-256, all in the paper checkout) --
SWEEP1_LIVENESS_PATH = "results/r1/engineering/liveness_c3_20261027T152425Z"
SWEEP1_LIVENESS_SHA256 = "3f64604e925082e8d639c0f95a9955ebf825cbd7be2f70fbb2aebbf4ab14b6f5"
SWEEP1_MANIFEST_SHA256 = "154f5f4832eaf2b673f475baa931f62b03ef37e330b0707013666d50ab76bd15"
# Per node: the k = 0 liveness campaign ledger, its SHA-256, the recorded trial-1 `usage.prompt_tokens` (the exact
# manager prompt text every campaign of that node sends at trial 1; both liveness instances of a node recorded the
# same value) and the recorded maximum over that instance's 10 memory-on calls.
SWEEP1_LEDGERS = {
    "digits_mlp": {"instance": "digits_mlp__s104", "seed": 104,
                   "ledger_sha256": "ed3b55eee0a24130526651feedbef2069322452ad009cb37cfba0f08eca5d61d",
                   "trial1_prompt_tokens": 514, "max_prompt_tokens": 1162, "n_trials": 10},
    "tabular_mlp": {"instance": "tabular_mlp__s102", "seed": 102,
                    "ledger_sha256": "62679bbb0bd122ce33cab9738945b77c30381caa14ad6e9c254bbaa07a43b80f",
                    "trial1_prompt_tokens": 520, "max_prompt_tokens": 1179, "n_trials": 10},
    "openml_breast_w": {"instance": "openml_breast_w__s105", "seed": 105,
                        "ledger_sha256": "89f266477bc90c06773a246ea37a4b8439c9f1951aad34d78951b952f4c95d28",
                        "trial1_prompt_tokens": 482, "max_prompt_tokens": 1052, "n_trials": 10},
    "openml_ionosphere": {"instance": "openml_ionosphere__s103", "seed": 103,
                          "ledger_sha256": "4beba65a99d7e568e00985f7066b280900bbd2cc657d5454d8d6f2db0447dd8b",
                          "trial1_prompt_tokens": 481, "max_prompt_tokens": 1029, "n_trials": 10},
    "openml_wdbc": {"instance": "openml_wdbc__s100", "seed": 100,
                    "ledger_sha256": "635c0d11dc5be18e48ea9ba83645ba7a7d28baf5d712d4ff1050d585eb6edac3",
                    "trial1_prompt_tokens": 484, "max_prompt_tokens": 1083, "n_trials": 10},
    "openml_credit_approval": {"instance": "openml_credit_approval__s100", "seed": 100,
                               "ledger_sha256": "10a6db2df964d3f81deb736733dc2e8dcaeba5a88b30d83f35be9098b8ef1b9b",
                               "trial1_prompt_tokens": 489, "max_prompt_tokens": 1064, "n_trials": 10},
    "openml_sonar": {"instance": "openml_sonar__s105", "seed": 105,
                     "ledger_sha256": "5857abe356256f54a013aa0f0ea7aa941bdd3639c139a85aa5cd50b87a002d67",
                     "trial1_prompt_tokens": 497, "max_prompt_tokens": 1079, "n_trials": 10},
    "openml_climate": {"instance": "openml_climate__s104", "seed": 104,
                       "ledger_sha256": "b3663eee9e91e0bcc79ef4573e295be38da4ecc35b597d17d00abcdb38a733f5",
                       "trial1_prompt_tokens": 513, "max_prompt_tokens": 1077, "n_trials": 10},
}
# --- the 1,345-token figure: the 14 OCT rerun-2 prompt set, budget 12, NOT a maximum and NOT the sweep-2 text -----
# The RUNBOOK's "manager prompts ... at most 1,345 tokens (memory on, W = 20, rerun-2)" sentence is the value of the
# BUDGET-12 proposal of the 14 Oct rerun-2 pilot (the snapshot below); the same pilot's W = 20 calls are longer (see
# the W = 20 root ledgers below).  The 14 Oct prompt set also differs from the 27 Oct liveness/sweep-2 text for at
# least openml_breast_w (rerun-2 `d31c77a3…` / 483 tokens vs sweep-2 `61aa9226…` / 482 tokens), so 1,345 is a b012
# scale reference, never "the recorded maximum" and never the sweep-2 text.
SWEEP1_PROMPT_B012_PATH = ("results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/snapshots/"
                           "tabular_mlp__s142/E2_b012/manifest.json")
SWEEP1_PROMPT_B012_SHA256 = "5e269d4cee24e263ee36f25cd087df6f489bbec5b8a5db51f5236b438310e605"
SWEEP1_PROMPT_B012_TOKENS = 1345
RERUN2_PROMPT_SET = "E1b rerun-2 A PARTIAL memory-on, 14 Oct 2026 prompt set"
RERUN2_BREAST_W_TRIAL1_SHA256 = "d31c77a387b4a100b58ac5c755b2ed760cdbe4b839d5956af75d4e08df9802b8"
RERUN2_BREAST_W_TRIAL1_TOKENS = 483
SWEEP1_LIVENESS_BREAST_W_TRIAL1_SHA256 = "61aa9226834f39beb862581b321cbfb068712cb2cb6d78d9e52b6d3ef2045134"
SWEEP1_LIVENESS_BREAST_W_TRIAL1_TOKENS = 482

# --- the true recorded W = 20 maximum, from the 54 rerun-2 ROOT ledgers (7B tokenizer) -------------------------
# `tabular_mlp__s142` records the 7B `usage.prompt_tokens` growth on that root: budget 12 -> 1,345, budget 20 ->
# 1,878.  Across all 54 rerun-2 root ledgers the maximum is 1,886 (`tabular_mlp__s112`, budget 20), which is the
# pinned W = 20 baseline this unit reports.  The aggregate SHA-256 pins the whole 54-ledger (instance, .gz sha256)
# list (sorted compact JSON), so the maximum cannot drift silently.
SWEEP1_W20_ROOTS_PATH = ("results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/ledgers/roots")
SWEEP1_W20_ROOT_COUNT = 54
SWEEP1_W20_ROOTS_SHA256 = "04d4ccd9d2a0be3d531240451b4871763356c85589ad16c1f0ebcc9b8b96720d"
SWEEP1_W20_LEDGER_PATH = SWEEP1_W20_ROOTS_PATH + "/tabular_mlp__s142/root_trials.jsonl.gz"
SWEEP1_W20_LEDGER_SHA256 = "bd0408a0df8dd47cf629fcbb4439e59072f54858f497097d0ad38a80266860a7"
SWEEP1_W20_LEDGER_BUDGET12_TOKENS = 1345
SWEEP1_W20_LEDGER_BUDGET20_TOKENS = 1878
SWEEP1_W20_MAX_TOKENS = 1886
SWEEP1_W20_MAX_INSTANCE = "tabular_mlp__s112"
SWEEP1_W20_MAX_BUDGET_INDEX = 20

# --- accepted 32k measured layout (R1-SWEEP2-LAYOUT @ author-decisions-20261116b 025bfc16; replaces S2-C4 16k) ---
# Measured by the accepted S2-C2 32k smoke (clusters 759728/759729, sweep2-main f172d299): 16 chunks, 9,387 s/chunk,
# 41.72 GPU-h, request_walltime 12,203 s, request_disk 42,460,977 kB, request_memory 32,000 MB.
ACCEPTED_LEVEL_LAYOUT = {"request_walltime_s": 12203, "request_disk_kb": 42460977, "request_memory_mb": 32000}

# --- prompt set ---------------------------------------------------------------------------------------------
# Three prompt classes: the trial-1 call, the 11-record memory-on class (budget 12) and the LONGEST class
# (W = 20, budget 20, 19 prior records).  The 11-record fixture is a middle class, not the longest.
PROMPT_VARIANTS = ("trial_1", "memory_on_declared_12", "memory_on_budget_20")
PROMPT_BUILDER_SOURCE = "src/autoresearch/manager/langgraph_manager.py:_prepare_context"
DECLARED_MEMORY_ON_BUDGET_INDEX = 12  # trial 12 in the W = 20 campaign: 11 prior trial lines in the memory block
DECLARED_MEMORY_ON_RECORDS = 11
W20_BUDGET_INDEX = 20  # the longest sweep-2 prompt class (W = 20 campaign): 19 prior trial lines in the memory
W20_RECORDS = 19
DECLARED_PRIOR_SUMMARIES = ("reduce-lr-1e-4", "increase-max-iter", "increase-C-0.5", "decrease-batch-32",
                            "increase-hidden-units", "reduce-alpha-1e-5", "decrease-max-iter",
                            "increase-batch-128", "reduce-hidden-units", "increase-alpha-1e-3",
                            "reduce-learning-rate-5e-4")
# variant -> (budget_index, declared memory records, declared current-best metric)
PROMPT_VARIANT_PLAN = {
    "trial_1": (1, 0, None),
    "memory_on_declared_12": (DECLARED_MEMORY_ON_BUDGET_INDEX, DECLARED_MEMORY_ON_RECORDS, 0.744),
    "memory_on_budget_20": (W20_BUDGET_INDEX, W20_RECORDS, 0.744),
}
TRANSFER_OUTPUTS = ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log")
PROMPT_OUTPUTS = ("s2_c3b_prompt_lengths.json", "s2_c3b_sweep1_comparison.json", "S2_C3B_PROMPT_REPORT.md")


class Stop(c2.Stop):
    """S2-C3b STOP: subclasses the S2-C2 STOP so the shared wrapper helpers raise the same catchable type."""


# ------------------------------------------------------------------ seeds
def instance_seed(node: str, k: int) -> int:
    """Mirror of `r1/headroom/e1b_collect._instance_seed` (pinned paper commit): 100 + 10k + len-sum(node) % 7."""
    return 100 + 10 * int(k) + (sum(map(ord, node)) % 7)


def sweep2_instance_seed_universe() -> list[int]:
    return sorted({instance_seed(node, k) for node in LIVENESS_NODES for k in range(SWEEP_INSTANCE_K)})


def liveness_instance_seeds() -> dict[str, list[int]]:
    """The per-node instance seeds `r1.liveness --instances 2` derives (k = 0, 1) - the sweep-1 D28 seeds."""
    return {node: [instance_seed(node, 0), instance_seed(node, 1)] for node in LIVENESS_NODES}


def _json_list_sha256(values: list[int]) -> str:
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def _flat(mapping: dict[str, list[int]]) -> list[int]:
    return sorted({int(seed) for seeds in mapping.values() for seed in seeds})


def check_seed_disjointness(spec: dict, sweep1_manifest: dict | None = None) -> dict:
    """Verify the declared seed plan.  Raises Stop for a false claim; returns the full, auditable check.

    The pinned `r1.liveness` CLI has no seed argument: it calls `e1b_collect.run_root(node, k)` for k = 0 .. 1, so the
    liveness instance seeds ARE the first two sweep instance seeds, exactly as in sweep 1's D28 run.  A
    "disjoint from the sweep-2 instance seeds" liveness seed set is therefore not implementable without changing the
    pinned harness.  This unit refuses to pretend otherwise: the spec must declare the D28 reuse, and the check
    proves that (a) the reuse equals the sweep-1 D28 record, (b) no audit seed (7001-7010) or exam/G.1b seed is used,
    and (c) the prompt-measurement seeds, which the template text does not depend on at trial 1, are disjoint.
    """
    seeds = c2._get(spec, "seeds")
    policy = seeds.get("liveness_seed_policy")
    if policy == "strict_disjoint":
        raise Stop("STOP: a disjoint liveness instance-seed set is not implementable with the pinned r1.liveness "
                   "CLI (it derives k = 0,1 = the first two sweep instance seeds); declare "
                   f"{LIVENESS_SEED_POLICY!r} and disclose the reuse")
    if policy != LIVENESS_SEED_POLICY:
        raise Stop(f"STOP: seeds.liveness_seed_policy must be {LIVENESS_SEED_POLICY!r} (D28 reuse; see docstring)")

    universe = sweep2_instance_seed_universe()
    if seeds.get("sweep2_instance_seed_count") != len(universe):
        raise Stop(f"STOP: sweep-2 instance seed universe must have {len(universe)} seeds "
                   "(8 nodes x 18 instances; R1-MAIN-PROPOSER (b))")
    if seeds.get("sweep2_instance_seed_universe_sha256") != _json_list_sha256(universe):
        raise Stop("STOP: sweep-2 instance seed universe sha256 mismatch (the pinned seed law changed)")

    live = liveness_instance_seeds()
    declared_live = c2._get(seeds, "liveness_instance_seeds")
    if not isinstance(declared_live, dict) or set(declared_live) != set(LIVENESS_NODES):
        raise Stop("STOP: seeds.liveness_instance_seeds must map exactly the eight sweep-1 nodes")
    for node in LIVENESS_NODES:
        got = [int(x) for x in declared_live[node]]
        if got != live[node]:
            raise Stop(f"STOP: declared liveness instance seeds for {node} {got} != the pinned D28 seeds {live[node]}")

    if c2._get(seeds, "reserved_audit_seeds") != list(RESERVED_AUDIT_SEEDS):
        raise Stop(f"STOP: seeds.reserved_audit_seeds must be exactly {list(RESERVED_AUDIT_SEEDS)}")
    declared_prompt = c2._get(seeds, "prompt_measurement_seeds")
    if not isinstance(declared_prompt, dict) or set(declared_prompt) != set(LIVENESS_NODES):
        raise Stop("STOP: seeds.prompt_measurement_seeds must map exactly the eight sweep-1 nodes")
    for node in LIVENESS_NODES:
        if int(declared_prompt[node]) != PROMPT_MEASUREMENT_SEEDS[node]:
            raise Stop(f"STOP: prompt-measurement seed for {node} must be {PROMPT_MEASUREMENT_SEEDS[node]}")

    prompt_values = sorted(int(v) for v in declared_prompt.values())
    exam_floor_collisions = sorted(value for value in prompt_values if value >= EXAM_SEED_BLOCK[0])
    blocked = set(universe) | set(RESERVED_AUDIT_SEEDS) | set(range(EXAM_SEED_BLOCK[0], EXAM_SEED_BLOCK[1] + 1)) \
        | set(range(G1B_SEED_BLOCK[0], G1B_SEED_BLOCK[1] + 1))
    if len(set(prompt_values)) != len(prompt_values):
        raise Stop("STOP: prompt-measurement seeds must be distinct")
    collisions = sorted(set(prompt_values) & blocked)
    if collisions or exam_floor_collisions:
        raise Stop(f"STOP: prompt-measurement seeds collide with reserved seeds: "
                   f"{sorted(set(collisions) | set(exam_floor_collisions))}; the exam block is "
                   f"{EXAM_SEED_BLOCK[0]}-{EXAM_SEED_BLOCK[1]} and the guard is open-ended (>= {EXAM_SEED_BLOCK[0]})")
    all_declared = set(_flat(live)) | set(prompt_values)
    audit_collisions = sorted(all_declared & set(RESERVED_AUDIT_SEEDS))
    if audit_collisions:
        raise Stop(f"STOP: a declared seed touches the B.2 audit seed block: {audit_collisions}")

    overlap = sorted(set(_flat(live)) & set(universe))
    expected_overlap = sorted({instance_seed(node, 0) for node in LIVENESS_NODES}
                              | {instance_seed(node, 1) for node in LIVENESS_NODES})
    if overlap != expected_overlap:
        raise Stop(f"STOP: unexpected liveness/sweep seed overlap {overlap} != {expected_overlap}")
    manifest_status = None
    if sweep1_manifest is not None:
        campaigns = sweep1_manifest.get("campaigns") or []
        by_node: dict[str, list[int]] = {}
        for campaign in campaigns:
            by_node.setdefault(str(campaign.get("node")), []).append(int(campaign.get("seed")))
        for node in LIVENESS_NODES:
            if sorted(by_node.get(node) or []) != live[node]:
                raise Stop(f"STOP: sweep-1 D28 liveness manifest seeds for {node} "
                           f"{sorted(by_node.get(node) or [])} != the pinned seeds {live[node]}")
        manifest_status = True
    return {
        "schema": "s2_c3b_seed_check/1",
        "policy": policy,
        "note": ("D28 liveness reuses the first two sweep instance seeds by construction (pinned r1.liveness k=0,1), "
                 "exactly as sweep 1 did; it is ENGINEERING_ONLY and never enters a label table. The prompt-"
                 "measurement seeds are disjoint from the sweep instance seeds, the audit block 7001-7010, the exam "
                 "block 9001-9303 and the G.1b block 8001-8010."),
        "liveness_disjoint_from_sweep2_instance_seeds": False,
        "liveness_overlap_with_sweep2_instance_seeds": overlap,
        "liveness_overlap_is_the_frozen_d28_reuse": True,
        "liveness_disjoint_from_audit_seeds": not audit_collisions,
        "prompt_measurement_disjoint": True,
        "sweep2_instance_seed_source": {
            "paper_path": SWEEP1_INSTANCE_SEED_SOURCE_PATH,
            "paper_sha256": SWEEP1_INSTANCE_SEED_SOURCE_SHA256,
            "function": "_instance_seed(node, k) = 100 + 10*k + sum(ord(node)) % 7",
            "instances_per_node": SWEEP_INSTANCE_K,
            "sweep1_index_path": SWEEP1_INDEX_PATH,
            "sweep1_index_sha256": SWEEP1_INDEX_SHA256,
            "sweep1_liveness_path": SWEEP1_LIVENESS_PATH,
            "sweep1_liveness_sha256": SWEEP1_LIVENESS_SHA256,
            "sweep1_manifest_sha256": SWEEP1_MANIFEST_SHA256,
        },
        "sweep2_instance_seed_count": len(universe),
        "sweep2_instance_seed_universe_sha256": _json_list_sha256(universe),
        "sweep2_instance_seeds": universe,
        "liveness_instance_seeds": live,
        "liveness_instance_seed_pairs": [[node, live[node]] for node in LIVENESS_NODES],
        "prompt_measurement_seeds": {node: PROMPT_MEASUREMENT_SEEDS[node] for node in LIVENESS_NODES},
        "prompt_measurement_seed_values": prompt_values,
        "reserved_audit_seeds": list(RESERVED_AUDIT_SEEDS),
        "exam_seed_block": list(EXAM_SEED_BLOCK),
        "exam_seed_guard": (f"the exam seed block is {EXAM_SEED_BLOCK[0]}-{EXAM_SEED_BLOCK[1]} (not an unbounded "
                            f"'9001+' claim); the collision guard is open-ended: any seed >= {EXAM_SEED_BLOCK[0]} STOPs"),
        "g1b_seed_block": list(G1B_SEED_BLOCK),
        "sweep1_liveness_manifest_matches": manifest_status,
    }


# ------------------------------------------------------------------ spec
def load_spec(path: Path) -> dict:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise Stop(f"STOP: spec schema must be {SCHEMA}")
    return data


def _c2_view(spec: dict) -> dict:
    """A C2-shaped copy used only to run the accepted S2-C2 validator (single source for image/model/server pins).

    The C2 validator is applied to a `liveness`-kind view: the collector block below is required by its schema but is
    not used by S2-C3b (this unit runs `r1.liveness`, never a chunk collector).  The C2 liveness block and every
    image/model/server/requirements pin are the spec's own values, so the exam-setting checks are reused verbatim.
    """
    view = json.loads(json.dumps(spec))
    view["schema"] = c2.SCHEMA
    view["kind"] = "liveness"
    view["collector"] = {
        "node": "digits_mlp", "memory_mode": LIVENESS_MEMORY_MODE, "instances": 18, "runs": 20,
        "workers": c2.MIN_CPUS, "transport_max_attempts": TRANSPORT_MAX_ATTEMPTS,
        "proposal_schema": "manager_proposal/v1", "verify_split_policy": "vary", "split": "c3_labels",
    }
    view.setdefault("pilot", False)
    return view


def validate_spec(spec: dict) -> dict:
    if spec.get("kind") != "liveness":
        raise Stop("STOP: kind must be liveness (S2-C3b runs the D28 liveness job)")
    if spec.get("label") != "ENGINEERING_ONLY":
        raise Stop("STOP: S2-C3b is ENGINEERING_ONLY (no EVIDENCE path in this unit)")
    if spec.get("b2_audits") != "none":
        raise Stop("STOP: b2_audits must be 'none' (R1-SWEEP2-SETTINGS (2): no B.2 audit in this unit)")
    try:
        validated_c2 = c2.validate_spec(_c2_view(spec))  # all image/model/server/requirements/liveness pins
    except c2.Stop as exc:
        raise Stop(str(exc)) from None
    if validated_c2["label"] != "ENGINEERING_ONLY":
        raise Stop("STOP: S2-C3b must not resolve an EVIDENCE label")

    run_id = c2._text(c2._get(spec, "run_id"), "run_id", c2.SAFE)
    chunk_id = c2._text(c2._get(spec, "chunk_id"), "chunk_id", c2.SAFE)
    if chunk_id != CHUNK_ID:
        raise Stop(f"STOP: chunk_id must be {CHUNK_ID!r} (one sealed S2-C3b attempt)")

    image = c2._get(spec, "image")
    if not str(image["digest"]).startswith(V1_GPU_DIGEST_PREFIX):
        raise Stop(f"STOP: S2-C3b runs the frozen v1 gpu image {V1_GPU_DIGEST_PREFIX}...; got {image['digest']}")
    if image["llama_server_sha256"] != FROZEN_LLAMA_SERVER_SHA256:
        raise Stop("STOP: llama-server sha256 differs from the frozen v1 image pin")

    model = c2._get(spec, "model")
    if not str(model["sha256"]).startswith(PICK_GGUF_SHA256_PREFIX):
        raise Stop(f"STOP: model must be the pick GGUF {PICK_GGUF_SHA256_PREFIX}...; got {model['sha256']}")
    if model["alias"] != PICK_ALIAS:
        raise Stop(f"STOP: model.alias must be {PICK_ALIAS!r} (R1-EXAM-X7 pick)")

    paper = c2._get(spec, "paper")
    if paper["commit"] not in ALLOWED_PAPER_COMMITS:
        raise Stop(f"STOP: paper.commit must be the reviewed main {PAPER_COMMIT} (the unit documents this pin)")
    if paper["evidence_ready"] is not False:
        raise Stop("STOP: paper.evidence_ready must be false (ENGINEERING_ONLY; not the EVIDENCE path)")

    live = c2._get(spec, "liveness")
    if c2._get(live, "memory_mode") != LIVENESS_MEMORY_MODE:
        raise Stop(f"STOP: liveness memory_mode must be {LIVENESS_MEMORY_MODE}")
    if c2._get(live, "transport_max_attempts") != TRANSPORT_MAX_ATTEMPTS:
        raise Stop(f"STOP: liveness transport_max_attempts must be {TRANSPORT_MAX_ATTEMPTS} (sweep-1 D28)")

    seed_check = check_seed_disjointness(spec)

    pm = c2._get(spec, "prompt_measurement")
    if list(pm.get("variants") or []) != list(PROMPT_VARIANTS):
        raise Stop(f"STOP: prompt_measurement.variants must be {list(PROMPT_VARIANTS)}")
    if pm.get("max_prompt_tokens_stop") != CTX:
        raise Stop(f"STOP: prompt_measurement.max_prompt_tokens_stop must be ctx {CTX}")
    sweep1 = c2._get(pm, "sweep1")
    for key, value in (("liveness_path", SWEEP1_LIVENESS_PATH),
                       ("liveness_sha256", SWEEP1_LIVENESS_SHA256),
                       ("manifest_sha256", SWEEP1_MANIFEST_SHA256),
                       ("b012_path", SWEEP1_PROMPT_B012_PATH),
                       ("b012_sha256", SWEEP1_PROMPT_B012_SHA256),
                       ("b012_tokens", SWEEP1_PROMPT_B012_TOKENS),
                       ("rerun2_prompt_set", RERUN2_PROMPT_SET),
                       ("rerun2_breast_w_trial1_sha256", RERUN2_BREAST_W_TRIAL1_SHA256),
                       ("rerun2_breast_w_trial1_tokens", RERUN2_BREAST_W_TRIAL1_TOKENS),
                       ("sweep2_breast_w_trial1_sha256", SWEEP1_LIVENESS_BREAST_W_TRIAL1_SHA256),
                       ("sweep2_breast_w_trial1_tokens", SWEEP1_LIVENESS_BREAST_W_TRIAL1_TOKENS),
                       ("w20_roots_path", SWEEP1_W20_ROOTS_PATH),
                       ("w20_roots_count", SWEEP1_W20_ROOT_COUNT),
                       ("w20_roots_sha256", SWEEP1_W20_ROOTS_SHA256),
                       ("w20_ledger_path", SWEEP1_W20_LEDGER_PATH),
                       ("w20_ledger_sha256", SWEEP1_W20_LEDGER_SHA256),
                       ("w20_ledger_budget12_tokens", SWEEP1_W20_LEDGER_BUDGET12_TOKENS),
                       ("w20_ledger_budget20_tokens", SWEEP1_W20_LEDGER_BUDGET20_TOKENS),
                       ("w20_max_tokens", SWEEP1_W20_MAX_TOKENS),
                       ("w20_max_instance", SWEEP1_W20_MAX_INSTANCE),
                       ("w20_max_budget_index", SWEEP1_W20_MAX_BUDGET_INDEX)):
        if sweep1.get(key) != value:
            raise Stop(f"STOP: prompt_measurement.sweep1.{key} must be the pinned sweep-1 record value")

    for key in ("walltime_s", "request_disk_kb", "request_memory_mb"):
        value = spec.get(key)
        if type(value) is not int or value <= 0:
            raise Stop(f"STOP: {key} must be a positive integer")
    # M1 (review round 2): the only accepted layout is R1-SWEEP2-LAYOUT's measured 32k layout.  The C2 validator
    # above already rejects anything below the measured S2-C4 floors and non-exact `--chat-template-kwargs`; this
    # check pins the C3b spec to the accepted 32k values (the superseded S2-C4 16k values are refused).
    if level_layout(spec) != ACCEPTED_LEVEL_LAYOUT:
        raise Stop(f"STOP: layout must be the accepted R1-SWEEP2-LAYOUT 32k layout {ACCEPTED_LEVEL_LAYOUT}; "
                   f"got {level_layout(spec)} (the S2-C4 16k layout is superseded)")
    if spec.get("transfer_outputs") != list(TRANSFER_OUTPUTS):
        raise Stop(f"STOP: transfer_outputs must be {list(TRANSFER_OUTPUTS)}")
    return {"run_id": run_id, "chunk_id": chunk_id, "kind": "liveness", "label": "ENGINEERING_ONLY",
            "seed_check": seed_check, "level_layout": level_layout(spec), "spec": spec}


def level_layout(spec: dict) -> dict:
    """The layout the spec requests, in the same shape as the accepted layout (and the C2 chunk record's)."""
    return {"request_walltime_s": spec.get("walltime_s"), "request_disk_kb": spec.get("request_disk_kb"),
            "request_memory_mb": spec.get("request_memory_mb")}


# ------------------------------------------------------------------ liveness
def liveness_argv(spec: dict) -> list[str]:
    """The exact `r1.liveness` invocation (no `--deadline`: the CLI has no such flag)."""
    c = spec["liveness"]
    return ["/opt/r1/envs/harness/bin/python", "-B", "-m", "r1.liveness", "--run", "--manager", "langgraph",
            "--memory-mode", c["memory_mode"], "--nodes", *LIVENESS_NODES,
            "--instances", str(c["instances"]), "--runs", str(c["runs"]),
            "--transport-max-attempts", str(c["transport_max_attempts"]),
            "--manager-model", "llamacpp/" + spec["model"]["alias"],
            "--proposal-schema", "manager_proposal/v1",
            "--out", str(Path("out").resolve()), "--work", str(Path("work").resolve())]


def evaluate_liveness(report: dict, min_live_nodes: int = MIN_LIVE_NODES,
                      nodes: tuple[str, ...] = LIVENESS_NODES) -> dict:
    """Read the D28 verdict.  Malformed/foreign reports are a STOP; a node shortfall is returned, not hidden."""
    if not isinstance(report, dict):
        raise Stop("STOP: liveness.json is not an object")
    if report.get("schema") != LIVENESS_REPORT_SCHEMA:
        raise Stop(f"STOP: liveness report schema {report.get('schema')!r} is not {LIVENESS_REPORT_SCHEMA!r}")
    if report.get("label") != "ENGINEERING_ONLY":
        raise Stop(f"STOP: liveness report label {report.get('label')!r} is not ENGINEERING_ONLY")
    if report.get("manager_kind") != "langgraph":
        raise Stop("STOP: liveness report is not LLM-backed (manager_kind != langgraph)")
    if report.get("memory_mode") != LIVENESS_MEMORY_MODE:
        raise Stop(f"STOP: liveness report memory_mode {report.get('memory_mode')!r} is not {LIVENESS_MEMORY_MODE}")
    nodes_map = report.get("nodes")
    if not isinstance(nodes_map, dict):
        raise Stop("STOP: liveness.json has no nodes object")
    missing = [node for node in nodes if node not in nodes_map]
    if missing:
        raise Stop(f"STOP: liveness report is missing nodes: {missing}")
    unexpected = sorted(set(nodes_map) - set(nodes))
    if unexpected:
        raise Stop(f"STOP: liveness report contains unexpected nodes not in the pinned eight: {unexpected}")
    verdicts = {}
    for node in nodes:
        entry = nodes_map[node]
        if not isinstance(entry, dict) or not isinstance(entry.get("pass"), bool):
            raise Stop(f"STOP: liveness report node {node} has no boolean pass verdict")
        verdicts[node] = {"pass": bool(entry["pass"]), "failed_criteria": list(entry.get("failed_criteria") or []),
                          "n_trials": entry.get("n_trials"),
                          "criteria": entry.get("criteria")}
    passed = [node for node in nodes if verdicts[node]["pass"]]
    failed = [node for node in nodes if not verdicts[node]["pass"]]
    return {"nodes": verdicts, "live_nodes": len(passed), "failed_nodes": failed,
            "min_live_nodes": min_live_nodes, "pass": len(passed) >= min_live_nodes,
            "report_schema": report.get("schema"), "generated_utc": report.get("generated_utc")}


# ------------------------------------------------------------------ prompt measurement
def _harness_import(harness_dir: Path):
    src = Path(harness_dir) / "src"
    if not src.is_dir():
        raise Stop(f"STOP: harness src missing at {src}")
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from autoresearch.manager.hyperparam_edits import parse_train_constants  # noqa: F401
        from autoresearch.manager.langgraph_manager import _prepare_context
        from autoresearch.manager.base import ManagerStatus
        from autoresearch.memory.schemas import (TrialDecision, TrialProvenance, TrialRecord, ExecutionStatus,
                                                  ValidityStatus)
        from autoresearch.memory.summarizer import build_memory_context
        from autoresearch.nodes.registry import load_registered_node
    except Exception as exc:  # noqa: BLE001 - the pinned harness must be importable
        raise Stop(f"STOP: cannot import the pinned harness prompt builder from {harness_dir}: "
                   f"{type(exc).__name__}: {exc}") from None
    return {"parse_train_constants": parse_train_constants, "_prepare_context": _prepare_context,
            "ManagerStatus": ManagerStatus, "build_memory_context": build_memory_context,
            "load_registered_node": load_registered_node, "TrialRecord": TrialRecord,
            "ExecutionStatus": ExecutionStatus, "ValidityStatus": ValidityStatus,
            "TrialDecision": TrialDecision, "TrialProvenance": TrialProvenance}


def _declared_prior_records(node: str, harness, count: int = DECLARED_MEMORY_ON_RECORDS) -> list:
    """A declared, deterministic memory-on history (11 prior trials) for the longest-prompt class.

    Only the harness's own `build_memory_context` and `TrialRecord` types are used; the values are this unit's
    declared fixture, so the resulting prompt text is exact for the declared state and reproducible.
    """
    records = []
    for j in range(1, count + 1):
        summary = DECLARED_PRIOR_SUMMARIES[(j - 1) % len(DECLARED_PRIOR_SUMMARIES)]
        provenance = harness["TrialProvenance"](proposal_id=f"declared-{j}", patch_id=f"declared-{j}",
                                                run_id=f"declared-{j}", metric_id=f"declared-{j}",
                                                decision_id=f"declared-{j}")
        records.append(harness["TrialRecord"](
            trial_id=f"{node}__s{PROMPT_MEASUREMENT_SEEDS[node]}-trial-{j:03d}",
            campaign_id=f"{node}__s{PROMPT_MEASUREMENT_SEEDS[node]}", node_id=node, budget_index=j,
            timestamp_start="2026-11-16T00:00:00Z", timestamp_end="2026-11-16T00:00:02Z",
            manager_mode="langgraph_manager", worker_mode="local", memory_mode=LIVENESS_MEMORY_MODE,
            proposal_summary=summary, proposal_rationale="declared fixture for the prompt-length re-measurement",
            targeted_files=("train.py",), patch_ref=f"declared/trial-{j:03d}/patch.diff",
            git_commit_before="declared-before", git_commit_after="declared-after",
            execution_status=harness["ExecutionStatus"].SUCCESS,
            validity_status=harness["ValidityStatus"].VALID, failure_category=None,
            raw_log_ref=f"declared/trial-{j:03d}/run.log",
            parsed_metrics={"train_loss": 1.2 - 0.01 * j, "val_score": 0.70 + 0.004 * j},
            current_best_before=(0.70 + 0.004 * (j - 1)) if j > 1 else None,
            delta_vs_best=(0.004 if j > 1 and j % 2 == 0 else None),
            decision=(harness["TrialDecision"].KEPT if j % 2 == 0 else harness["TrialDecision"].DISCARDED),
            decision_rationale="declared fixture", wall_clock_seconds=2.0, cumulative_budget_consumed=j,
            provenance=provenance, repeated_bad_count=0))
    return records


def build_prompt_texts(harness_dir: Path, spec: dict) -> dict:
    """Exact sweep-2 manager prompt texts from the pinned harness (`_prepare_context`), plus their SHA-256.

    The manager sends one user message (`context_text`) per call; there is no separate system message in this stack -
    the server chat template renders the system/user scaffolding around it (`/apply-template`, measured later).
    """
    harness = _harness_import(Path(harness_dir))
    harness_root = Path(harness_dir)
    manager_py = harness_root / "src/autoresearch/manager/langgraph_manager.py"
    prompts = []
    for node in LIVENESS_NODES:
        try:
            node_spec = harness["load_registered_node"](node, repo_root=harness_root)
        except Exception as exc:  # noqa: BLE001
            raise Stop(f"STOP: cannot load the pinned harness node spec for {node}: "
                       f"{type(exc).__name__}: {exc}") from None
        constants: dict[str, str] = {}
        node_files = {}
        for rel_path in node_spec.editable_paths:
            path = harness_root / "nodes" / node / rel_path
            if not path.is_file():
                raise Stop(f"STOP: pinned harness node file missing: nodes/{node}/{rel_path}")
            node_files[rel_path] = hashlib.sha256(path.read_bytes()).hexdigest()
            constants.update(harness["parse_train_constants"](path))
        editable = tuple(getattr(node_spec, "editable_symbols", ()) or ())
        if editable:
            allowed = set(editable)
            constants = {key: value for key, value in constants.items() if key in allowed}
        if not constants:
            raise Stop(f"STOP: no editable constants parsed for {node} at the pinned harness commit")
        config_path = harness_root / "configs" / "nodes" / f"{node}.yaml"
        config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest() if config_path.is_file() else None
        for variant in PROMPT_VARIANTS:
            budget_index, record_count, best = PROMPT_VARIANT_PLAN[variant]
            records = [] if record_count == 0 else _declared_prior_records(node, harness, count=record_count)
            memory_context = harness["build_memory_context"](
                records, LIVENESS_MEMORY_MODE, node_spec, budget_index)
            status = harness["ManagerStatus"](
                campaign_id=f"{node}__s{PROMPT_MEASUREMENT_SEEDS[node]}", budget_index=budget_index,
                current_best_metric=best, metric_name=node_spec.metric_name,
                metric_direction=node_spec.metric_direction, current_constants=dict(constants),
                effective_config={})
            state = {"status": status, "memory_context": memory_context, "node_spec": node_spec,
                     "revision_feedback": None, "proposal_schema": None, "llm_meta": None, "llm_seed": None,
                     "llm": None, "llm_seed_as_kwarg": False, "transport_retry": None}
            try:
                text = harness["_prepare_context"](state)["context_text"]
            except Exception as exc:  # noqa: BLE001
                raise Stop(f"STOP: pinned harness prompt builder failed for {node}/{variant}: "
                           f"{type(exc).__name__}: {exc}") from None
            if not isinstance(text, str) or len(text) < 100:
                raise Stop(f"STOP: pinned harness produced an empty/short prompt for {node}/{variant}")
            prompts.append({
                "node": node, "variant": variant, "budget_index": budget_index,
                "prompt_seed": PROMPT_MEASUREMENT_SEEDS[node],
                "campaign_id": f"{node}__s{PROMPT_MEASUREMENT_SEEDS[node]}",
                "memory_mode": LIVENESS_MEMORY_MODE, "memory_records": len(records),
                "current_best_metric": best, "editable_constants": dict(constants),
                "node_file_sha256": node_files, "node_config_sha256": config_sha,
                "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "chars": len(text),
            })
    set_sha = hashlib.sha256(json.dumps(
        [{"node": p["node"], "variant": p["variant"], "text_sha256": p["text_sha256"]} for p in prompts],
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema": "s2_c3b_prompt_texts/1", "builder": PROMPT_BUILDER_SOURCE,
            "harness_commit": spec["harness"]["commit"],
            "builder_file_sha256": hashlib.sha256(manager_py.read_bytes()).hexdigest(),
            "prompt_set_sha256": set_sha, "prompts": prompts}


def _post_json(url: str, payload: dict, timeout: float = 120.0) -> dict:
    data = json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode())
    except Exception as exc:  # noqa: BLE001 - a missing endpoint is a STOP, never a guess
        raise Stop(f"STOP: POST {url} failed: {type(exc).__name__}: {exc}") from None
    if not isinstance(body, dict):
        raise Stop(f"STOP: POST {url} returned no JSON object")
    return body


def root_url(server_base_url: str) -> str:
    """`http://127.0.0.1:<port>/v1` -> `http://127.0.0.1:<port>` (the tokenizer routes are root-level)."""
    base = str(server_base_url)
    return base[:-3] if base.endswith("/v1") else base


def apply_template(base: str, text: str) -> str:
    body = _post_json(root_url(base) + "/apply-template",
                      {"messages": [{"role": "user", "content": text}], "add_generation_prompt": True,
                       "chat_template_kwargs": {"enable_thinking": False}})
    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise Stop("STOP: /apply-template returned no prompt string")
    return prompt


def tokenize_text(base: str, text: str, add_special: bool) -> list[int]:
    body = _post_json(root_url(base) + "/tokenize", {"content": text, "add_special": bool(add_special)})
    tokens = body.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise Stop("STOP: /tokenize returned no tokens")
    try:
        return [int(token) for token in tokens]
    except (TypeError, ValueError):
        raise Stop("STOP: /tokenize returned non-integer tokens") from None


def measure_prompts(base: str, spec: dict, prompt_set: dict) -> dict:
    """Tokenize the exact prompt texts with the pick's tokenizer (server `/apply-template` + `/tokenize`)."""
    rows = []
    for prompt in prompt_set["prompts"]:
        text = prompt["text"]
        user_tokens = tokenize_text(base, text, add_special=False)
        rendered = apply_template(base, text)
        rendered_tokens = tokenize_text(base, rendered, add_special=True)
        position = rendered.find(text)
        if position < 0:
            # M2 (review round 2): a template that mangles/normalises the user text would otherwise still produce a
            # "measurement" that is not the sweep-2 prompt.  That is a STOP, not a recorded flag.
            raise Stop(f"STOP: the rendered prompt for {prompt['node']}/{prompt['variant']} does not contain the "
                       "user text verbatim; the server chat template mangled or whitespace-normalised it, so the "
                       "tokenizer count is not a measurement of the sweep-2 prompt")
        prefix = rendered[:position]
        suffix = rendered[position + len(text):]
        prefix_tokens = tokenize_text(base, prefix, add_special=True) if prefix else []
        row = {
            "node": prompt["node"], "variant": prompt["variant"], "budget_index": prompt["budget_index"],
            "prompt_seed": prompt["prompt_seed"], "campaign_id": prompt["campaign_id"],
            "memory_mode": prompt["memory_mode"], "memory_records": prompt["memory_records"],
            "user_text": text, "user_text_sha256": prompt["text_sha256"], "user_text_chars": prompt["chars"],
            "user_text_tokens": len(user_tokens),
            "rendered_prompt": rendered,
            "rendered_prompt_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
            "rendered_prompt_tokens": len(rendered_tokens),
            "rendered_prompt_chars": len(rendered),
            "template_prefix": prefix, "template_prefix_tokens": len(prefix_tokens),
            "template_prefix_empty": not bool(prefix),
            "template_suffix_chars": len(suffix),
            "user_text_present_in_rendered": True,
            "fits_ctx": len(rendered_tokens) < CTX,
        }
        rows.append(row)
    return {"schema": "s2_c3b_prompt_measurement/1", "ctx": CTX,
            "tokenizer": "pick GGUF tokenizer via the owned llama-server /apply-template + /tokenize",
            "prompt_set_sha256": prompt_set["prompt_set_sha256"],
            "builder_file_sha256": prompt_set["builder_file_sha256"],
            "measured_utc": _utc(), "prompts": rows,
            "max_tokens": max((row["rendered_prompt_tokens"] for row in rows), default=0),
            "all_fit_ctx": all(row["fits_ctx"] for row in rows)}


def _read_json_pinned(path: Path, sha256: str, what: str) -> dict:
    if not path.is_file():
        raise Stop(f"STOP: {what} missing: {path} (expected in the pinned paper checkout)")
    data = path.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != sha256:
        raise Stop(f"STOP: {what} sha256 mismatch: {got} != pinned {sha256} ({path})")
    try:
        return json.loads(data.decode())
    except json.JSONDecodeError:
        raise Stop(f"STOP: {what} is not valid JSON: {path}") from None


def verify_sweep1_record(paper_dir: Path) -> dict:
    """Load and pin the sweep-1 D28 liveness record (all eight nodes passed; ENGINEERING_ONLY)."""
    base = Path(paper_dir) / SWEEP1_LIVENESS_PATH
    liveness = _read_json_pinned(base / "liveness.json", SWEEP1_LIVENESS_SHA256, "sweep-1 liveness.json")
    manifest = _read_json_pinned(base / "manifest.json", SWEEP1_MANIFEST_SHA256, "sweep-1 liveness manifest")
    if liveness.get("label") != "ENGINEERING_ONLY":
        raise Stop("STOP: sweep-1 liveness record label is not ENGINEERING_ONLY")
    if liveness.get("memory_mode") != LIVENESS_MEMORY_MODE:
        raise Stop("STOP: sweep-1 liveness record memory_mode differs")
    if liveness.get("manager_kind") != "langgraph":
        raise Stop("STOP: sweep-1 liveness record is not LLM-backed")
    nodes = liveness.get("nodes") or {}
    failed = [node for node in LIVENESS_NODES if not (nodes.get(node) or {}).get("pass")]
    if failed:
        raise Stop(f"STOP: the pinned sweep-1 liveness record did not pass these nodes: {failed}")
    if manifest.get("harness", {}).get("commit") is None:
        raise Stop("STOP: sweep-1 liveness manifest has no harness commit")
    return {"path": SWEEP1_LIVENESS_PATH, "liveness_sha256": SWEEP1_LIVENESS_SHA256,
            "manifest_sha256": SWEEP1_MANIFEST_SHA256, "liveness": liveness, "manifest": manifest}


def _read_gzip_jsonl_pinned(path: Path, sha256: str | None, what: str) -> list[dict]:
    """Read a pinned `.jsonl.gz` record; a missing file / changed sha / bad JSON is a STOP."""
    if not path.is_file():
        raise Stop(f"STOP: {what} missing: {path} (expected in the pinned paper checkout)")
    raw = path.read_bytes()
    if sha256 is not None:
        got = hashlib.sha256(raw).hexdigest()
        if got != sha256:
            raise Stop(f"STOP: {what} sha256 mismatch: {got} != pinned {sha256} ({path})")
    try:
        lines = gzip.decompress(raw).decode().splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Stop(f"STOP: {what} is not a readable .jsonl.gz record: {type(exc).__name__}: {exc}") from None


def _manager_call(trial: dict) -> dict:
    return ((trial.get("extra") or {}).get("manager", {}) or {}).get("llm_call", {}) or {}


def _verify_w20_root_ledgers(roots: Path) -> dict:
    """Verify the 54 rerun-2 ROOT ledgers and return the true recorded W = 20 maximum (7B tokenizer).

    The 14 Oct rerun-2 pilot roots each record 20 trials of `usage.prompt_tokens`, growing with the memory block:
    `tabular_mlp__s142` is 1,345 at budget 12 and 1,878 at budget 20; the maximum over all 54 roots is 1,886
    (`tabular_mlp__s112`, budget 20).  Both the per-file .gz sha256 list and the maximum are pinned.
    """
    if not roots.is_dir():
        raise Stop(f"STOP: rerun-2 root-ledger directory missing: {roots}")
    files = sorted(roots.glob("*/root_trials.jsonl.gz"))
    if len(files) != SWEEP1_W20_ROOT_COUNT:
        raise Stop(f"STOP: expected {SWEEP1_W20_ROOT_COUNT} rerun-2 root ledgers, found {len(files)} ({roots})")
    entries, maxima = [], []
    ledger_b012 = ledger_b020 = None
    for path in files:
        instance = path.parent.name
        raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"instance": instance, "sha256": raw_sha})
        trials = _read_gzip_jsonl_pinned(path, None, f"rerun-2 root ledger {instance}")
        for trial in trials:
            tokens = _manager_call(trial).get("prompt_tokens")
            if isinstance(tokens, int):
                maxima.append((tokens, instance, trial.get("budget_index")))
        if instance == "tabular_mlp__s142":
            if raw_sha != SWEEP1_W20_LEDGER_SHA256:
                raise Stop(f"STOP: rerun-2 root ledger {instance} sha256 {raw_sha} != pinned "
                           f"{SWEEP1_W20_LEDGER_SHA256} ({path})")
            by_budget = {trial.get("budget_index"): _manager_call(trial).get("prompt_tokens") for trial in trials}
            ledger_b012, ledger_b020 = by_budget.get(12), by_budget.get(20)
    aggregate = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if aggregate != SWEEP1_W20_ROOTS_SHA256:
        raise Stop(f"STOP: rerun-2 root-ledger set sha256 {aggregate} != pinned {SWEEP1_W20_ROOTS_SHA256} "
                   "(a rerun-2 root ledger changed)")
    if ledger_b012 != SWEEP1_W20_LEDGER_BUDGET12_TOKENS or ledger_b020 != SWEEP1_W20_LEDGER_BUDGET20_TOKENS:
        raise Stop(f"STOP: tabular_mlp__s142 rerun-2 budget 12/20 prompt_tokens {ledger_b012}/{ledger_b020} != "
                   f"the pinned {SWEEP1_W20_LEDGER_BUDGET12_TOKENS}/{SWEEP1_W20_LEDGER_BUDGET20_TOKENS}")
    tokens, instance, budget_index = max(maxima)
    if tokens != SWEEP1_W20_MAX_TOKENS or instance != SWEEP1_W20_MAX_INSTANCE \
            or budget_index != SWEEP1_W20_MAX_BUDGET_INDEX:
        raise Stop(f"STOP: the rerun-2 W=20 maximum is {tokens} ({instance}, budget {budget_index}) != the pinned "
                   f"{SWEEP1_W20_MAX_TOKENS} ({SWEEP1_W20_MAX_INSTANCE}, budget {SWEEP1_W20_MAX_BUDGET_INDEX})")
    return {
        "roots_path": SWEEP1_W20_ROOTS_PATH,
        "root_count": len(entries),
        "roots_sha256": aggregate,
        "ledger_path": SWEEP1_W20_LEDGER_PATH,
        "ledger_sha256": SWEEP1_W20_LEDGER_SHA256,
        "ledger_budget12_tokens": ledger_b012,
        "ledger_budget20_tokens": ledger_b020,
        "max_tokens": tokens,
        "max_instance": instance,
        "max_budget_index": budget_index,
        "tokenizer_note": "7B sweep-1 manager tokenizer, recorded as usage.prompt_tokens in the pinned rerun-2 roots",
    }


def verify_sweep1_prompt_record(paper_dir: Path) -> dict:
    """Pin the 14 Oct rerun-2 prompt-length record: the b012 1,345 figure and the true W = 20 maximum 1,886.

    Three records are verified together, all SHA-256 pinned:
    (1) the b012 snapshot manifest (`tabular_mlp__s142/E2_b012`, 1,345) - the RUNBOOK figure.  It is the **budget-12**
        value of the **14 Oct** rerun-2 prompt set: it is *not* a maximum and *not* the 27 Oct liveness/sweep-2 text.
    (2) the 54 rerun-2 root ledgers, whose maximum is 1,886 (`tabular_mlp__s112`, budget 20) - the true recorded
        W = 20 baseline (`tabular_mlp__s142`: budget 12 = 1,345, budget 20 = 1,878).
    (3) the corrected comparison: openml_breast_w's trial-1 rerun-2 text (`d31c77a3…`, 483 tokens) differs from the
        27 Oct liveness/sweep-2 text (`61aa9226…`, 482 tokens), so the two prompt sets cannot be treated as identical.
    """
    paper = Path(paper_dir)
    b012 = _read_json_pinned(paper / SWEEP1_PROMPT_B012_PATH, SWEEP1_PROMPT_B012_SHA256,
                             "sweep-1 prompt-length b012 snapshot")
    try:
        value = b012["proposal"]["extra"]["llm_call"]["prompt_tokens"]
        provisional = b012["provisional"]["extra"]["manager"]["llm_call"]["prompt_tokens"]
    except (KeyError, TypeError):
        raise Stop("STOP: sweep-1 prompt-length b012 snapshot has no proposal/provisional prompt_tokens") from None
    if int(value) != SWEEP1_PROMPT_B012_TOKENS or int(provisional) != SWEEP1_PROMPT_B012_TOKENS:
        raise Stop(f"STOP: sweep-1 prompt-length b012 snapshot {value}/{provisional} != {SWEEP1_PROMPT_B012_TOKENS}")
    w20 = _verify_w20_root_ledgers(paper / SWEEP1_W20_ROOTS_PATH)
    if w20["ledger_budget12_tokens"] != SWEEP1_PROMPT_B012_TOKENS:
        raise Stop(f"STOP: the rerun-2 root ledger's budget-12 prompt_tokens {w20['ledger_budget12_tokens']} != "
                   f"the b012 snapshot {SWEEP1_PROMPT_B012_TOKENS}; the 1,345 figure is a budget-12 value")
    rerun2_breast = None
    rerun2_path = paper / SWEEP1_W20_ROOTS_PATH / "openml_breast_w__s105/root_trials.jsonl.gz"
    for trial in _read_gzip_jsonl_pinned(rerun2_path, None, "rerun-2 openml_breast_w root ledger"):
        if trial.get("budget_index") == 1:
            rerun2_breast = {
                "context_sha256": ((trial.get("extra") or {}).get("manager", {}) or {}).get("context_sha256"),
                "prompt_tokens": _manager_call(trial).get("prompt_tokens"),
            }
    if not isinstance(rerun2_breast, dict) or rerun2_breast["context_sha256"] is None:
        raise Stop("STOP: the rerun-2 openml_breast_w root ledger has no trial-1 context_sha256")
    liveness_breast_path = (paper / SWEEP1_LIVENESS_PATH / "ledgers"
                            / SWEEP1_LEDGERS["openml_breast_w"]["instance"] / "root_trials.jsonl")
    if not liveness_breast_path.is_file():
        raise Stop(f"STOP: sweep-1 liveness openml_breast_w ledger missing: {liveness_breast_path}")
    liveness_breast = None
    for line in liveness_breast_path.read_text().splitlines():
        if not line.strip():
            continue
        trial = json.loads(line)
        if trial.get("budget_index") == 1:
            liveness_breast = {
                "context_sha256": ((trial.get("extra") or {}).get("manager", {}) or {}).get("context_sha256"),
                "prompt_tokens": _manager_call(trial).get("prompt_tokens"),
            }
    if liveness_breast is None:
        raise Stop("STOP: the sweep-1 liveness openml_breast_w ledger has no trial-1 record")
    if (rerun2_breast["context_sha256"] != RERUN2_BREAST_W_TRIAL1_SHA256
            or rerun2_breast["prompt_tokens"] != RERUN2_BREAST_W_TRIAL1_TOKENS):
        raise Stop(f"STOP: rerun-2 openml_breast_w trial-1 {rerun2_breast} != pinned "
                   f"{RERUN2_BREAST_W_TRIAL1_SHA256}/{RERUN2_BREAST_W_TRIAL1_TOKENS}")
    if (liveness_breast["context_sha256"] != SWEEP1_LIVENESS_BREAST_W_TRIAL1_SHA256
            or liveness_breast["prompt_tokens"] != SWEEP1_LIVENESS_BREAST_W_TRIAL1_TOKENS):
        raise Stop(f"STOP: sweep-1 liveness openml_breast_w trial-1 {liveness_breast} != pinned "
                   f"{SWEEP1_LIVENESS_BREAST_W_TRIAL1_SHA256}/{SWEEP1_LIVENESS_BREAST_W_TRIAL1_TOKENS}")
    if rerun2_breast["context_sha256"] == liveness_breast["context_sha256"]:
        raise Stop("STOP: the rerun-2 and sweep-1 liveness openml_breast_w trial-1 prompt texts are identical; the "
                   "unit's premise that the 14 Oct prompt set is not the sweep-2 text does not hold")
    return {
        "b012": {
            "path": SWEEP1_PROMPT_B012_PATH, "sha256": SWEEP1_PROMPT_B012_SHA256,
            "prompt_tokens": SWEEP1_PROMPT_B012_TOKENS,
            "campaign_id": b012.get("campaign_id"), "node": b012.get("node_name"),
            "budget_index": b012.get("budget_index"), "memory_mode": b012.get("memory_mode"),
            "prompt_set": RERUN2_PROMPT_SET,
            "meaning": ("the RUNBOOK's 1,345 is the 14 Oct rerun-2 prompt set's budget-12 value; it is explicitly "
                       "NOT a maximum (the same pilot reaches 1,878 at budget 20 on that root) and NOT the "
                       "27 Oct liveness/sweep-2 prompt text"),
            "tokenizer_note": "counted with the sweep-1 manager (7B) tokenizer (RUNBOOK Context note)",
        },
        "w20": w20,
        "rerun2_breast_w_trial1": {"path": str(rerun2_path.relative_to(paper)), **rerun2_breast},
        "sweep2_breast_w_trial1": {"path": str(liveness_breast_path.relative_to(paper)), **liveness_breast},
        "prompt_set_note": (f"{RERUN2_PROMPT_SET} is not the 27 Oct liveness/sweep-2 prompt set: openml_breast_w "
                            f"trial-1 differs ({rerun2_breast['context_sha256'][:8]}/"
                            f"{rerun2_breast['prompt_tokens']} vs {liveness_breast['context_sha256'][:8]}/"
                            f"{liveness_breast['prompt_tokens']}); the per-node trial-1 text identity check in this "
                            "unit is made against the pinned 27 Oct liveness ledgers only"),
    }


def compare_with_sweep1(paper_dir: Path, measured: dict, cross_check: dict | None = None) -> dict:
    """Compare the pick-tokenizer prompt lengths with the pinned sweep-1 records.  Missing/mismatched records STOP."""
    record = verify_sweep1_record(paper_dir)
    prompt_record = verify_sweep1_prompt_record(paper_dir)
    b012_tokens = prompt_record["b012"]["prompt_tokens"]
    w20_max = prompt_record["w20"]["max_tokens"]
    base = Path(paper_dir) / SWEEP1_LIVENESS_PATH
    by_node = {}
    for row in measured["prompts"]:
        by_node.setdefault(row["node"], {})[row["variant"]] = row
    rows, ratios = [], []
    for node in LIVENESS_NODES:
        pinned = SWEEP1_LEDGERS[node]
        for variant in PROMPT_VARIANTS:
            if variant not in by_node.get(node, {}):
                raise Stop(f"STOP: the measurement has no {variant} prompt for {node} "
                           "(the W=20 / 19-record longest class must be measured, not only the 11-record fixture)")
        ledger_path = base / "ledgers" / pinned["instance"] / "root_trials.jsonl"
        if not ledger_path.is_file():
            raise Stop(f"STOP: sweep-1 liveness ledger missing: {ledger_path}")
        got_sha = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        if got_sha != pinned["ledger_sha256"]:
            raise Stop(f"STOP: sweep-1 liveness ledger sha256 mismatch for {node}")
        trials = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
        if not trials:
            raise Stop(f"STOP: sweep-1 liveness ledger for {node} is empty")
        recorded = [(trial.get("extra") or {}).get("manager", {}).get("llm_call", {}) or {} for trial in trials]
        trial1 = [call.get("prompt_tokens") for call, trial in zip(recorded, trials)
                  if trial.get("budget_index") == 1]
        if len(trial1) != 1 or trial1[0] != pinned["trial1_prompt_tokens"]:
            raise Stop(f"STOP: sweep-1 liveness trial-1 prompt_tokens for {node} != {pinned['trial1_prompt_tokens']}")
        maxima = [call.get("prompt_tokens") for call in recorded if isinstance(call.get("prompt_tokens"), int)]
        if not maxima or max(maxima) != pinned["max_prompt_tokens"]:
            raise Stop(f"STOP: sweep-1 liveness max prompt_tokens for {node} != {pinned['max_prompt_tokens']}")
        trial1_row = by_node[node]["trial_1"]
        middle_row = by_node[node]["memory_on_declared_12"]
        longest_row = by_node[node]["memory_on_budget_20"]
        # The trial-1 manager prompt text must be byte-identical to the text the sweep-1 liveness run actually sent:
        # the ledger records its SHA-256 (`extra.manager.context_sha256`), so the tokenizer comparison below is on
        # identical text (not on a re-derived approximation).
        sweep1_context_sha = [((trial.get("extra") or {}).get("manager", {}) or {}).get("context_sha256")
                              for trial in trials if trial.get("budget_index") == 1]
        if len(sweep1_context_sha) != 1 or not isinstance(sweep1_context_sha[0], str):
            raise Stop(f"STOP: sweep-1 liveness ledger for {node} has no trial-1 context_sha256")
        if sweep1_context_sha[0] != trial1_row["user_text_sha256"]:
            raise Stop(f"STOP: the pinned prompt builder does not reproduce the sweep-1 liveness trial-1 prompt "
                       f"text for {node} ({trial1_row['user_text_sha256']} != {sweep1_context_sha[0]}); the "
                       "prompt template/node files changed and the tokenizer comparison cannot be made")
        ratio = trial1_row["rendered_prompt_tokens"] / pinned["trial1_prompt_tokens"]
        ratios.append(ratio)
        rows.append({
            "node": node, "sweep1_instance": pinned["instance"],
            "sweep1_trial1_prompt_tokens": pinned["trial1_prompt_tokens"],
            "pick_trial1_rendered_prompt_tokens": trial1_row["rendered_prompt_tokens"],
            "pick_trial1_user_text_tokens": trial1_row["user_text_tokens"],
            "sweep1_trial1_prompt_sha256": sweep1_context_sha[0],
            "pick_trial1_prompt_sha256": trial1_row["user_text_sha256"],
            "prompt_texts_identical": True,
            "trial1_delta_tokens": trial1_row["rendered_prompt_tokens"] - pinned["trial1_prompt_tokens"],
            "trial1_tokenizer_ratio": round(ratio, 4),
            "sweep1_max_prompt_tokens": pinned["max_prompt_tokens"],
            "pick_memory_on_declared_12_tokens": middle_row["rendered_prompt_tokens"],
            "memory_on_declared_12_delta_vs_b012": middle_row["rendered_prompt_tokens"] - b012_tokens,
            "pick_memory_on_budget_20_tokens": longest_row["rendered_prompt_tokens"],
            "pick_memory_on_budget_20_vs_w20_max_ratio": round(longest_row["rendered_prompt_tokens"] / w20_max, 4),
            "memory_on_budget_20_delta_vs_sweep1_recorded_max": longest_row["rendered_prompt_tokens"] - w20_max,
            "pick_fits_ctx": trial1_row["fits_ctx"] and middle_row["fits_ctx"] and longest_row["fits_ctx"],
        })
    max_pick = max(row["rendered_prompt_tokens"] for row in measured["prompts"])
    max_trial1 = max(by_node[node]["trial_1"]["rendered_prompt_tokens"] for node in LIVENESS_NODES)
    max_middle = max(by_node[node]["memory_on_declared_12"]["rendered_prompt_tokens"] for node in LIVENESS_NODES)
    max_longest = max(by_node[node]["memory_on_budget_20"]["rendered_prompt_tokens"] for node in LIVENESS_NODES)
    summary = {
        "max_pick_prompt_tokens": max_pick,
        "max_pick_trial1_tokens": max_trial1,
        "max_pick_memory_on_declared_12_tokens": max_middle,
        "max_pick_memory_on_budget_20_tokens": max_longest,
        "max_pick_memory_on_tokens": max_longest,
        "trial1_tokenizer_ratio_mean": round(sum(ratios) / len(ratios), 4),
        "trial1_tokenizer_ratio_min": round(min(ratios), 4),
        "trial1_tokenizer_ratio_max": round(max(ratios), 4),
        "sweep1_b012_tokens": b012_tokens,
        "ratio_vs_sweep1_b012": round(max_middle / b012_tokens, 4),
        "sweep1_w20_max_tokens": w20_max,
        "sweep1_w20_max_instance": prompt_record["w20"]["max_instance"],
        "ratio_vs_sweep1_w20_max": round(max_longest / w20_max, 4),
        "ctx_headroom_tokens": CTX - max_pick,
        "ctx_headroom_ratio": round(CTX / max_pick, 2) if max_pick else None,
        "all_pick_prompts_fit_ctx": measured["all_fit_ctx"],
        "prompt_texts_identical_to_sweep1": all(row["prompt_texts_identical"] for row in rows),
        "longest_prompt_class_measured": "memory_on_budget_20" in PROMPT_VARIANTS,
        "interpretation": (
            "the trial-1 pick/prompt comparison is on identical prompt text (SHA-256-equal, 27 Oct liveness ledgers); "
            "the memory-on classes are this unit's declared fixtures (11 records = budget 12, a middle class; 19 "
            "records = budget 20 = the longest W=20 class). The 1,345 figure is the 14 Oct rerun-2 budget-12 value, "
            "not a maximum; the true recorded W=20 maximum is 1,886. The W=20 fit conclusion is the headroom line, "
            "not a claim that the fixture text equals the 14 Oct rerun-2 text."),
    }
    result = {
        "schema": "s2_c3b_sweep1_comparison/1",
        "compared_utc": _utc(),
        "method": ("the trial-1 manager prompt text is rebuilt from the pinned harness and must be byte-identical to "
                   "the sweep-1 liveness record (the ledger's `extra.manager.context_sha256` is compared, 27 Oct "
                   "prompt set); the pick-tokenizer counts come from the owned server's /apply-template + /tokenize; "
                   "the sweep-1 counts are the recorded per-call usage.prompt_tokens of the pinned sweep-1 D28 "
                   "liveness ledgers (r1-manager tokenizer). The memory-on prompts are this unit's declared fixtures: "
                   "the 11-record (budget 12) middle class and the 19-record (budget 20) longest W=20 class. The "
                   "recorded 1,345 is the 14 Oct rerun-2 budget-12 value, not a maximum; the true W=20 maximum is "
                   "1,886 over the pinned 54 rerun-2 root ledgers."),
        "sweep1_record": {"liveness_path": record["path"], "liveness_sha256": record["liveness_sha256"],
                          "manifest_sha256": record["manifest_sha256"],
                          "b012": prompt_record["b012"], "w20": prompt_record["w20"],
                          "prompt_set_note": prompt_record["prompt_set_note"]},
        "ctx": CTX,
        "prompt_variants": list(PROMPT_VARIANTS),
        "per_node": rows,
        "summary": summary,
    }
    if cross_check is not None:
        result["liveness_usage_cross_check"] = cross_check
    return result


def cross_check_liveness_usage(out_dir: Path, measured: dict) -> dict:
    """Cross-check `/tokenize(add_special=True)` against the job's own liveness-ledger `usage.prompt_tokens`.

    The liveness run that precedes the prompt measurement sends the same trial-1 manager prompt text, and its
    `out/ledgers/<instance>/root_trials.jsonl` records the server's own `usage.prompt_tokens` for that call.  Both
    numbers are recorded so the BOS / add_special question is settled by the run itself instead of being guessed.
    (m3 of review round 2.)
    """
    ledger_dir = Path(out_dir) / "ledgers"
    paths = sorted(ledger_dir.glob("*/root_trials.jsonl")) if ledger_dir.is_dir() else []
    trial1 = {row["node"]: row["rendered_prompt_tokens"] for row in measured["prompts"]
              if row["variant"] == "trial_1"}
    per_node: dict[str, dict] = {}
    for path in paths:
        instance = path.parent.name
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                trial = json.loads(line)
            except json.JSONDecodeError:
                raise Stop(f"STOP: liveness ledger {path} is not valid JSONL") from None
            if trial.get("budget_index") != 1:
                continue
            node = str(trial.get("campaign_id") or instance).split("__")[0]
            usage = _manager_call(trial).get("prompt_tokens")
            if node in trial1 and isinstance(usage, int):
                entry = per_node.setdefault(node, {"node": node, "liveness_usage_prompt_tokens": usage,
                                                   "pick_rendered_prompt_tokens": trial1[node],
                                                   "instances": []})
                entry["instances"].append(instance)
                entry["liveness_usage_prompt_tokens"] = usage
    for entry in per_node.values():
        entry["delta_tokens"] = entry["pick_rendered_prompt_tokens"] - entry["liveness_usage_prompt_tokens"]
        entry["abs_delta_tokens"] = abs(entry["delta_tokens"])
        entry["bos_consistent"] = entry["abs_delta_tokens"] <= 1
    deltas = [entry["abs_delta_tokens"] for entry in per_node.values()]
    return {
        "schema": "s2_c3b_liveness_usage_cross_check/1",
        "available": bool(per_node),
        "source": "out/ledgers/*/root_trials.jsonl -> extra.manager.llm_call.prompt_tokens (the job's own liveness run)",
        "per_node": {node: per_node[node] for node in LIVENESS_NODES if node in per_node},
        "nodes_checked": len(per_node),
        "max_abs_delta_tokens": max(deltas) if deltas else None,
        "all_bos_consistent_within_1_token": all(entry["bos_consistent"] for entry in per_node.values()) if per_node
                                              else None,
        "note": ("`/tokenize(add_special=True)` should match the server's own `usage.prompt_tokens` for the same "
                 "trial-1 text (delta 0, or 1 if add_special double-counts a BOS that the chat template already "
                 "emitted); both numbers are recorded and the flag is REPORTED, not used to invent a pass"),
    }


def _prompt_report(measured: dict, comparison: dict, cross_check: dict | None = None) -> str:
    lines = ["# S2-C3b prompt-length re-measurement (ENGINEERING_ONLY)", "",
             f"Generated {_utc()}. Pick tokenizer via the owned llama-server `/apply-template` + `/tokenize`; "
             f"context {CTX}.", "",
             "| node | sweep-1 trial-1 tokens | pick trial-1 tokens | ratio | sweep-1 liveness max (memory on) | "
             "pick 11-record (b012) | pick W=20 19-record (longest) |", "|---|---|---|---|---|---|---|"]
    for row in comparison["per_node"]:
        lines.append(f"| {row['node']} | {row['sweep1_trial1_prompt_tokens']} | "
                     f"{row['pick_trial1_rendered_prompt_tokens']} | {row['trial1_tokenizer_ratio']} | "
                     f"{row['sweep1_max_prompt_tokens']} | {row['pick_memory_on_declared_12_tokens']} | "
                     f"{row['pick_memory_on_budget_20_tokens']} |")
    summary = comparison["summary"]
    lines += ["", f"- max pick prompt: **{summary['max_pick_prompt_tokens']}** tokens "
                  f"(headroom {summary['ctx_headroom_tokens']} of {CTX}, x{summary['ctx_headroom_ratio']}); "
                  f"fits: {summary['all_pick_prompts_fit_ctx']}",
              f"- trial-1 tokenizer ratio (pick/sweep-1): mean {summary['trial1_tokenizer_ratio_mean']}, "
              f"range {summary['trial1_tokenizer_ratio_min']}-{summary['trial1_tokenizer_ratio_max']}",
              f"- pick W=20 19-record class (longest): {summary['max_pick_memory_on_budget_20_tokens']} tokens "
              f"(x{summary['ratio_vs_sweep1_w20_max']} of the pinned 1,886 W=20 maximum)",
              f"- pick 11-record class (b012, middle): {summary['max_pick_memory_on_declared_12_tokens']} tokens "
              f"(x{summary['ratio_vs_sweep1_b012']} of the 1,345 b012 value)",
              "- pinned sweep-1 prompt-length record (7B tokenizer): the recorded **1,345** figure is the **14 Oct** "
              "rerun-2 prompt set's **budget-12** value, NOT a maximum and NOT the 27 Oct/sweep-2 text; the true "
              "recorded **W=20 maximum is 1,886** (`tabular_mlp__s112`, budget 20; that root family grows 1,345 at "
              "budget 12 to 1,878 at budget 20, e.g. `tabular_mlp__s142`, over the pinned 54 rerun-2 root ledgers)",
              "- corrected comparison: `openml_breast_w` trial-1 differs between the 14 Oct rerun-2 set "
              "(`d31c77a3…`, 483 tokens) and the 27 Oct liveness/sweep-2 text (`61aa9226…`, 482 tokens); the "
              "byte-identity check above is against the 27 Oct liveness ledgers only"]
    if cross_check is not None:
        if cross_check.get("available"):
            lines.append(f"- in-run cross-check: `/tokenize(add_special=True)` vs the job's own liveness-ledger "
                         f"`usage.prompt_tokens` over {cross_check['nodes_checked']} nodes: max |delta| = "
                         f"{cross_check['max_abs_delta_tokens']} token(s); BOS-consistent (<=1): "
                         f"{cross_check['all_bos_consistent_within_1_token']}")
        else:
            lines.append("- in-run cross-check: no liveness ledgers were available to compare "
                         "`/tokenize(add_special=True)` against `usage.prompt_tokens`")
    lines += ["", f"Sweep-1 record: `{comparison['sweep1_record']['liveness_path']}` "
                  f"(liveness.json {comparison['sweep1_record']['liveness_sha256'][:12]}...); rerun-2 prompt record "
                  f"`{comparison['sweep1_record']['w20']['roots_path']}` "
                  f"({comparison['sweep1_record']['w20']['root_count']} root ledgers, "
                  f"sha {comparison['sweep1_record']['w20']['roots_sha256'][:12]}...).", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ job persistence / seal
def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _persist(record: dict, record_path: Path) -> None:
    record_path.write_text(json.dumps(record, indent=1) + "\n")
    c2._tar_dir(Path("out"), Path("out.tar"))
    c2._tar_dir(Path("work"), Path("work.tar"))
    c2._write_sums(Path("."))


def _stop_with_evidence(record: dict, record_path: Path, message: str) -> None:
    """Persist the record + out/work tars + SHA256SUMS before raising (S2-C2 round-5 pattern)."""
    record["stop"] = message
    record["finished_utc"] = _utc()
    _persist(record, record_path)
    raise Stop(message)


def _write_prompt_outputs(measured: dict, comparison: dict | None,
                         cross_check: dict | None = None) -> None:
    out = Path("out")
    out.mkdir(parents=True, exist_ok=True)
    (out / "s2_c3b_prompt_lengths.json").write_text(json.dumps(measured, indent=1) + "\n")
    if comparison:
        (out / "s2_c3b_sweep1_comparison.json").write_text(json.dumps(comparison, indent=1) + "\n")
        (out / "S2_C3B_PROMPT_REPORT.md").write_text(_prompt_report(measured, comparison, cross_check))


def audit_worker_logs(bases=("out", "work")) -> dict:
    """Scan worker run.log files under out/ and work/ (r1.liveness copies ledgers to out/ but writes the worker
    logs under work/). STOP if none exist or if every run crashed; otherwise record the counts."""
    logs = []
    for base in bases:
        logs.extend(sorted(Path(base).rglob("run.log")))
    crashed = [p for p in logs if any(m in p.read_text(errors="replace")
                                      for m in ("Traceback (most recent call last)", "ModuleNotFoundError",
                                                "ImportError", "SyntaxError"))]
    audit = {"total_run_logs": len(logs), "crashed": len(crashed), "scanned": list(bases)}
    if not logs:
        raise Stop("STOP: no liveness worker run.log found (work/ and out/ scanned); no training evidence")
    if len(crashed) == len(logs):
        raise Stop("STOP: all liveness worker runs crashed; no training evidence")
    return audit


def run_liveness_job(spec_path: Path) -> dict:
    validated = validate_spec(load_spec(Path(spec_path)))
    s = validated["spec"]
    out, work = Path("out"), Path("work")
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    record_path = Path("job_record.json")
    record = {
        "schema": RECORD_SCHEMA, "kind": "liveness", "run_id": validated["run_id"],
        "chunk_id": validated["chunk_id"], "label": validated["label"],
        "image_digest": s["image"]["digest"], "model_sha256": s["model"]["sha256"],
        "paper_commit": s["paper"]["commit"], "harness_commit": s["harness"]["commit"],
        "b2_audits": "none (no B.2 audits; audit seeds 7001-7010 untouched)",
        "audit_seeds_touched": [],
        "output_use": "ENGINEERING: never enters a label table, training or selection; not evidence",
        "manager_settings": {"ctx": CTX, "np": NP, "ngl": NGL, "thinking": "off", "kv_cache": "q8_0",
                             "cache_prompt": "false (LLAMACPP_CACHE_PROMPT/LLAMACACHE_PROMPT unset)",
                             "temperature": "0.2 (D26 manager seed)"},
        "non_numeric_differences": c2.non_numeric_differences(s["server"]["extra_args"]),
        "level_layout": validated["level_layout"],
        "seed_plan": validated["seed_check"],
        "spec_liveness": s["liveness"],
        "spec_prompt_measurement": {"variants": list(PROMPT_VARIANTS),
                                    "sweep1": s["prompt_measurement"]["sweep1"],
                                    "max_prompt_tokens_stop": s["prompt_measurement"]["max_prompt_tokens_stop"]},
        "started_utc": _utc(),
    }
    record["image"] = c2.image_identity(s)
    record["host"] = c2.host_identity()
    record["gpu"] = c2.gpu_identity(s["requirements"]["gpu_device_name"])
    record["cpu"] = c2.cpu_identity()

    paper_dir, harness_dir = Path("paper"), Path("harness")
    c2.clone_at(s["paper"]["repo"], s["paper"]["commit"], paper_dir)
    c2.clone_at(s["harness"]["repo"], s["harness"]["commit"], harness_dir)
    try:
        sweep1 = verify_sweep1_record(paper_dir)
    except Stop as exc:
        _stop_with_evidence(record, record_path, str(exc))
    record["sweep1_record"] = {"path": sweep1["path"], "liveness_sha256": sweep1["liveness_sha256"],
                               "manifest_sha256": sweep1["manifest_sha256"]}
    try:
        seed_check = check_seed_disjointness(s, sweep1_manifest=sweep1["manifest"])
        verify_sweep1_prompt_record(paper_dir)
    except Stop as exc:
        _stop_with_evidence(record, record_path, str(exc))
    record["seed_plan"] = seed_check

    record["model"] = c2.fetch_model(s["model"], Path("model.gguf"))
    server = c2.start_server(s, Path("model.gguf"), Path("llama-server.log"))

    def stop(message: str) -> None:
        """M4 (review round 2): kill the owned server (None-guarded) BEFORE `_persist` writes `SHA256SUMS`.

        Otherwise `llama-server.log` (a summed transfer output) could still be written by the live server after it
        was hashed, and `seal` would refuse the transferred sums on exactly the shortfall/failure path that promises
        "evidence persists and can be sealed".  The `_kill` guard tolerates an already-cleared handle.
        """
        c2._kill(server["proc"])
        server["proc"] = None
        _stop_with_evidence(record, record_path, message)

    try:
        record["server"] = {key: server[key] for key in
                            ("pid", "base_url", "build", "offloaded_layers", "total_layers", "cuda_lines", "log")}
        argv = liveness_argv(s)
        env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()),
                   AR_HARNESS_ROOT=str(harness_dir.resolve()),
                   PATH="/opt/r1/envs/harness/bin:" + os.environ.get("PATH", ""),
                   LLAMACPP_BASE_URL=server["base_url"], OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
        env.pop("LLAMACPP_CACHE_PROMPT", None)
        env.pop("LLAMACACHE_PROMPT", None)
        started = time.time()
        result = subprocess.run(argv, cwd=str(paper_dir.resolve()), env=env, capture_output=True, text=True)
        record["liveness_run"] = {"argv": argv, "returncode": result.returncode,
                                  "seconds": round(time.time() - started, 1),
                                  "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:]}
        if result.returncode != 0:
            stop(f"STOP: r1.liveness rc={result.returncode}; outputs kept")
        try:
            record["worker_audit"] = audit_worker_logs()
        except Stop as exc:
            stop(str(exc))
        try:
            report = json.loads((out / "liveness.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            stop(f"STOP: cannot read out/liveness.json: {exc}")
        try:
            verdict = evaluate_liveness(report)
        except Stop as exc:
            stop(str(exc))
        record["liveness_results"] = verdict
        if not verdict["pass"]:
            stop(f"STOP: only {verdict['live_nodes']}/{len(LIVENESS_NODES)} nodes passed D28 liveness "
                 f"(< {verdict['min_live_nodes']}): {verdict['failed_nodes']}; the author decides, "
                 "no node is dropped silently")

        try:
            prompt_set = build_prompt_texts(harness_dir, s)
            measured = measure_prompts(server["base_url"], s, prompt_set)
        except Stop as exc:
            stop(str(exc))
        record["prompt_measurement"] = {"prompt_set_sha256": prompt_set["prompt_set_sha256"],
                                        "builder": prompt_set["builder"],
                                        "builder_file_sha256": prompt_set["builder_file_sha256"],
                                        "max_tokens": measured["max_tokens"],
                                        "all_fit_ctx": measured["all_fit_ctx"],
                                        "prompts": [{key: row[key] for key in
                                                     ("node", "variant", "prompt_seed", "user_text_sha256",
                                                      "user_text_tokens", "rendered_prompt_sha256",
                                                      "rendered_prompt_tokens", "template_prefix_tokens",
                                                      "fits_ctx")} for row in measured["prompts"]]}
        if not measured["all_fit_ctx"]:
            _write_prompt_outputs(measured, None)
            stop(f"STOP: a re-measured prompt does not fit ctx {CTX} (max {measured['max_tokens']} tokens)")
        try:
            # m3 (review round 2): settle the BOS/add_special question with the job's own liveness ledgers.
            cross_check = cross_check_liveness_usage(out, measured)
            record["liveness_prompt_token_cross_check"] = cross_check
        except Stop as exc:
            stop(str(exc))
        try:
            comparison = compare_with_sweep1(paper_dir, measured, cross_check=cross_check)
        except Stop as exc:
            stop(str(exc))
        record["sweep1_comparison"] = comparison
        _write_prompt_outputs(measured, comparison, record.get("liveness_prompt_token_cross_check"))
    finally:
        c2._kill(server["proc"])
    record["finished_utc"] = _utc()
    _persist(record, record_path)
    return record


# ------------------------------------------------------------------ seal
def seal(job_output: Path, run_id: str, chunk_id: str) -> dict:
    """Operator-side sealing: C3b record guards, then the reviewed S2-C2 seal step (no overwrite)."""
    src = Path(job_output).resolve()
    record_file = src / "job_record.json"
    if not record_file.is_file():
        raise Stop("STOP: job output has no job_record.json")
    record = json.loads(record_file.read_text())
    if record.get("schema") != RECORD_SCHEMA:
        raise Stop(f"STOP: job record schema must be {RECORD_SCHEMA}")
    if record.get("kind") != "liveness":
        raise Stop("STOP: job record kind must be liveness")
    if record.get("label") != "ENGINEERING_ONLY":
        raise Stop("STOP: S2-C3b seals ENGINEERING_ONLY records only")
    if record.get("audit_seeds_touched"):
        raise Stop("STOP: job record claims touched audit seeds")
    receipt = c2.seal(job_output, run_id, chunk_id)
    receipt.update({"schema": SEAL_RECEIPT_SCHEMA, "unit": "S2-C3b", "record_schema": RECORD_SCHEMA})
    target = Path(receipt["sealed_path"])
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


# ------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    validate = sub.add_parser("validate", help="validate a spec (fail-closed)")
    validate.add_argument("spec")
    seeds = sub.add_parser("seeds", help="print the seed-disjointness check for a spec")
    seeds.add_argument("spec")
    run = sub.add_parser("run", help="run the D28 liveness job + prompt re-measurement (in the HTCondor sandbox)")
    run.add_argument("spec")
    seal_parser = sub.add_parser("seal", help="seal a transferred job output (operator side, /ceph)")
    seal_parser.add_argument("job_output")
    seal_parser.add_argument("--run-id", required=True)
    seal_parser.add_argument("--chunk-id", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        validated = validate_spec(load_spec(Path(args.spec)))
        print(json.dumps({"ok": True, "run_id": validated["run_id"], "chunk_id": validated["chunk_id"],
                          "label": validated["label"],
                          "prompt_measurement_disjoint":
                              validated["seed_check"]["prompt_measurement_disjoint"],
                          "liveness_disjoint_from_sweep2_instance_seeds":
                              validated["seed_check"]["liveness_disjoint_from_sweep2_instance_seeds"]}))
        return 0
    if args.cmd == "seeds":
        validated = validate_spec(load_spec(Path(args.spec)))
        print(json.dumps(validated["seed_check"], indent=1))
        return 0
    if args.cmd == "run":
        record = run_liveness_job(Path(args.spec))
        print(json.dumps({"ok": True, "label": record["label"], "host": record["host"]["fqdn"],
                          "gpu": record["gpu"]["name"], "live_nodes": record["liveness_results"]["live_nodes"],
                          "max_prompt_tokens": record["prompt_measurement"]["max_tokens"]}))
        return 0
    print(json.dumps(seal(Path(args.job_output), args.run_id, args.chunk_id), indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Stop, c2.Stop) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
