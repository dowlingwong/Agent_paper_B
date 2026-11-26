# AI-assisted (Claude, chat session, 22 Nov 2026; subagent). Revision 4: AI-assisted (Claude, local worker,
# 27 Nov 2026). DRAFT; not signed.
"""D.3 closed-loop analysis on T0 (R1-D3-MIN, R1-MINSUB-CHOICES (4)): every pre-declared contrast of both stages.

Tier E (R1-PROCESS-TIERS: "the analysis scripts of D.3"): this file's sha256 is bound by the D.3 pre-declaration
(``docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`` §9) and must not change after it is signed. Revised
after the independent review ``docs/r1/reviews/D3_PREDECLARATION_REVIEW_20261122.md``.

Revision 4 (rows of PLAN §10 "26 November 2026 (d)" and R1-HOST-FREE (2)(c)): arm A0R in D.3a with the contrasts
A0R - A0 and A2 - A0R (R1-D3-DECOMP); D.3b always runs and its family gains A5 - A3 (R1-D3B-UNCONDITIONAL); the
secondary outcomes (a)-(e) of R1-D3-OUTCOMES2, descriptive; the reference rows RS and SMAC3 (R1-D3-HPO-REF),
descriptive; one GPU model per instance across its arms (R1-HOST-FREE (2)(c)); the declared readings ("A2 > A0",
"A3 or A5 > A2", the rule-layer-alone qualifier) and the design's detectable difference (task local/20261126-16).

What it reads, and nothing else
-------------------------------
* Up to three **per-campaign outcome tables** in schema ``r1_d3_outcome/v2`` (pre-declaration §8): the D.3a table
  (required), the D.3b table (once D.3b ran) and the HPO-REF table (once the reference rows ran). A table that is not
  exactly this schema, or does not cover exactly the declared design, is refused before any statistic is computed.
  The path is screened, and the file's size and suffix checked, before it is opened.
* The pre-declaration file (only its sha256 is compared with the tables' header).
* For D.3b only, the signed D.3b authorization note (at most 1 MiB): exactly one line ``approved: true`` and exactly
  one key line ``a6_entered: true|false`` are read from it, so that the D.3b family is fixed before launch
  (pre-declaration §6); its sha256 is recorded in the report.
* The pinned noise summary ``results/r1/noise/D28_REPAIR_20261027/summary.json`` (sha256-checked), only to check that
  the tables' ``sigma_node`` values equal ``r1.c3.dataset.noise_table``'s. It holds noise-floor constants, no label.

It opens no label block, test partition, evaluation block, sweep table or ``r1_sealed`` path: ``refuse_input_path``
refuses such paths by name before anything is opened. Refusal messages name the row index and the rule, never a value
or key taken from the table.

Statistics (pre-declaration §7)
-------------------------------
Per instance (node n, instance seed s) and arm a: Y = y_raw / sigma_node(n), the mean over the declared repetitions
(``REPETITIONS``). For a contrast a - b: D_{n,s} = Y_{n,s}(a) - Y_{n,s}(b) on the same instance.
* Estimate: the node-equal-weighted mean D = (1/N) sum_n mean_s D_{n,s}.
* Standard error: (1/N) sqrt(sum_n s_n^2 / m_n), s_n the within-node sd of D (ddof 1), m_n its instance count.
* Test: two-sided Student t with df = sum_n (m_n - 1); Holm step-down within each stage's family at alpha 0.05
  (D.3a: eight contrasts; D.3b: five, six with A6). Degenerate rule: if the standard error is 0, p = 1 when the
  estimate is 0 and p = 0 otherwise.
* Interval: 95 % t interval (unadjusted), and a node-stratified percentile bootstrap interval (instances resampled
  within node; 10,000 resamples; PCG64 seed 20261122) reported beside it (descriptive).
* A table with more repetitions than declared is analysed on the declared ones; the mean over all its repetitions is
  reported as a separate, descriptive family with no verdict.
* Per-node means and descriptive per-arm usage (worker runs, LLM calls, what ended the campaign).
* Declared readings (pre-declaration §7.4): "A2 > A0" is the Holm rejection of A2 - A0 in the D.3a family with a
  positive estimate; "A3 or A5 > A2" is the Holm rejection of A3 - A2 or of A5 - A2 in the D.3b family with a positive
  estimate; the rule-layer-alone qualifier applies when A2 > A0 and A0R - A0 is rejected favourably while A2 - A0R is
  not.
* Secondary outcomes (R1-D3-OUTCOMES2 (a)-(e); descriptive, no p-value, no verdict) and the reference rows RS and
  SMAC3 (R1-D3-HPO-REF; descriptive differences against A0 and A2, outside the Holm families).

Usage::

    python -m r1.c3.d3_analysis analyse --d3a T.json [--d3b T.json --d3b-note NOTE.md | --d3b-not-run REASON] \
        [--hpo-ref T.json] --predeclaration docs/r1/authorizations/<signed pre-declaration>.md --out report.json
    python -m r1.c3.d3_analysis namespaces      # the seed-namespace disjointness check (§4 of the pre-declaration)
    python -m r1.c3.d3_analysis design          # the detectable difference at the declared design (§7.3)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy import stats

SCHEMA = "r1_d3_outcome/v2"          # revision 4: v1 + the R1-D3-OUTCOMES2 fields, gpu_model, infra_attempts
REPORT_SCHEMA = "r1_d3_report/v2"
STAGES = ("D.3a", "D.3b", "HPO-REF")

# PRE-WDBC B primary T0 set: the seven nodes that passed S2-C3b at the sweep-2 launch commit (R1-S2C3B-WDBC); the
# eight T0 nodes are gate.T0_NODES, openml_wdbc is the one left out.
NODES = ("digits_mlp", "openml_breast_w", "openml_climate", "openml_credit_approval", "openml_ionosphere",
         "openml_sonar", "tabular_mlp")
MEMORY_MODE = "append_only_summary"   # R1-MINSUB-CHOICES (4)
W = 20                                # R1-MINSUB-CHOICES (4): as in sweep 2
LLM_CALL_CAP = 80                     # PROPOSED in the pre-declaration §3 (no value on main); fixed by signing
REPETITIONS = 1                       # PROPOSED in the pre-declaration §1/§13 item 3; fixed by signing
K_AUDIT = 10                          # R1-MINSUB-CHOICES (4)

# R1-D3-MIN + R1-MINSUB-CHOICES (4): six rule arms; R1-D3-DECOMP adds A0R (the default keep rule with the rule layer).
ARMS_D3A = ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER")
ARMS_D3B = ("A3", "A5")                                      # R1-D3-MIN; R1-D3B-UNCONDITIONAL; A6 only under P.5
ARMS_D3B_WITH_A6 = ("A3", "A5", "A6")
ARMS_HPO = ("RS", "SMAC3")                                   # R1-D3-HPO-REF: random search with de-duplication, SMAC3
REPLICATE_ARMS = ("FIXR3", "EGATE")                          # the only arms that may end on no_fundable_candidate
# Arms whose rule layer may skip a proposal (rule_skips > 0). The rule layer is OFF for FIXR3, EGATE and LADDER
# (pre-declaration §5, revision 4: conservative option, as revision 3). RS skips duplicate draws (R1-D3-HPO-REF).
RULE_LAYER_ARMS = ("A0R", "A2", "A3", "A5", "A6", "RS")
SCREEN_ARMS = ("A1", "A2", "A3", "A5", "A6")                 # arms whose E1 screen may skip on value (value_skips > 0)
# The D.3a family (R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-D3-DECOMP), in the declared order of the claim sheet §6.
CONTRASTS_D3A = (("A0R", "A0"), ("A2", "A0R"), ("A1", "A0"), ("A2", "A0"), ("FIXR3", "A0"), ("EGATE", "A0"),
                 ("LADDER", "A0"), ("LADDER", "A2"))
# The D.3b family (R1-D3-MIN; R1-D3B-UNCONDITIONAL adds A5 - A3); A6 - A5 only if the D.3b note declares A6.
CONTRASTS_D3B = (("A3", "A2"), ("A5", "A2"), ("A3", "A0"), ("A5", "A0"), ("A5", "A3"))
CONTRAST_A6 = ("A6", "A5")
# Descriptive reference rows (R1-D3-HPO-REF): differences only, no p-value, outside every Holm family.
CONTRASTS_HPO = (("RS", "A0"), ("SMAC3", "A0"), ("RS", "A2"), ("SMAC3", "A2"))
HPO_PROPOSAL_CAP = 80                 # PROPOSED: draws (RS) or asks (SMAC3) per campaign, = the LLM-call cap
HPO_MEMORY_MODE = "not_applicable"
BUDGET_POINTS = (5, 10, 15, 20)       # R1-D3-OUTCOMES2 (a): Y(w)
POWER = 0.8                           # the stated design power of the detectable-difference figure (§7.3)
ALPHA = 0.05
BOOT = 10_000
BOOT_SEED = 20261122
CI_LEVEL = 0.95
MAX_TABLE_BYTES = 64 * 1024 * 1024

# ---- seeds (pre-declaration §4). Proposed blocks; disjointness is checked by ``check_namespaces``. ------------------
INSTANCE_SEEDS = tuple(range(6201, 6219))       # 18 deployment instances per node, the same seeds on every node
SMOKE_SEEDS = (6301, 6302)                       # the per-arm ENGINEERING smoke (2 instances); never in an outcome table
SMOKE_REPLICATE_SEED_BASE = 6300                 # smoke replicate j (1..9) of smoke seed s: 6300 + 10 (s - 6300) + j
REPLICATE_SEED_BASE = 6500                       # replicate j (1..9) of instance index i: 6500 + 10 i + j
AUDIT_SEED_BASE = 6700                           # audit seed k (1..10) of instance index i: 6700 + 10 i + k
MAX_REPLICATE_J = 9


class D3InputError(ValueError):
    """An input refusal: raised before any statistic is computed (pre-declaration §7, §10)."""


def instance_index(seed: int) -> int:
    if seed not in INSTANCE_SEEDS:
        raise D3InputError("not a declared D.3 instance seed")
    return INSTANCE_SEEDS.index(seed)


def replicate_seeds(seed: int) -> tuple[int, ...]:
    """Seeds of replicate runs j = 1..9 (j = 0 is the instance seed itself) for FIXR3 and EGATE.

    Defined for the D.3 instance seeds (6501-6679) and, ENGINEERING_ONLY, for the smoke seeds (6311-6319, 6321-6329).
    """
    if seed in SMOKE_SEEDS:
        return tuple(SMOKE_REPLICATE_SEED_BASE + 10 * (seed - SMOKE_REPLICATE_SEED_BASE) + j
                     for j in range(1, MAX_REPLICATE_J + 1))
    i = instance_index(seed)
    return tuple(REPLICATE_SEED_BASE + 10 * i + j for j in range(1, MAX_REPLICATE_J + 1))


def audit_seeds(seed: int) -> tuple[int, ...]:
    """The K = 10 fresh audit seeds of one instance, shared by every arm and repetition on it."""
    i = instance_index(seed)
    return tuple(AUDIT_SEED_BASE + 10 * i + k for k in range(1, K_AUDIT + 1))


def instance_id(node: str, seed: int) -> str:
    return f"{node}__s{int(seed)}"


def campaign_id(stage: str, arm: str, node: str, seed: int, repetition: int) -> str:
    """The D.3 record name; it encodes the arm. (The harness campaign_id is the instance id, pre-declaration §4.1.)"""
    return f"{stage}__{arm}__{instance_id(node, seed)}__r{int(repetition)}"


# Every seed namespace already used in the repository, with its source (pre-declaration §4.2). Closed intervals.
# The tests cross-check each interval that has a module constant against that constant.
RESERVED_SEED_NAMESPACES = {
    "sweep 1 and sweep 2 instance seeds = P3 T0 split universe (e1b_collect._instance_seed, k = 0..17)": None,
    "T1 G.5 instance seeds = P3 T1 split universe (r1/c3/p3_split.py T1_SEEDS)": (5101, 5112),
    "B.2 audit seeds, label 7001-7005 and evaluation 7006-7010 (r1/c3/audit.py DEFAULT_SEEDS)": (7001, 7010),
    "exam instance and audit seeds (r1/exam/namespace.py; sweep2/s2_c3b_lib.py EXAM_SEED_BLOCK 9001-9303)": (9001, 9303),
    "G.1b proposed training-seed block (RUNBOOK G.1b; sweep2/s2_c3b_lib.py G1B_SEED_BLOCK)": (8001, 8010),
    "D21 noise floors, train seeds (r1/noise/e1_noise_floor.py SEED_BASE; g1b note: 30 seeds)": (1001, 1030),
    "D21 noise floors, split seeds": (2001, 2030),
    "D21 noise floors, joint seeds": (3001, 3030),
    "G.4 pilot instance seeds (authorizations/g4_t1_tasl_20261122.md)": (4001, 4003),
    "E1b audit seeds (r1/headroom/e1b_collect.py AUDIT_SEED_BASE; R1-E1B-RERUN2)": (5001, 5006),
    "S2-C3b prompt-measurement seeds (sweep2/s2_c3b_lib.py PROMPT_MEASUREMENT_SEEDS)": (6101, 6108),
    "Track S instance blocks (r1/tracks/collect.py INSTANCE_SEED_BLOCKS on trackS-ops-20261030)": (30000, 39999),
    "Track S audit blocks (r1/tracks/collect.py AUDIT_SEED_BASES)": (100000, 799999),
    "engineering smoke seeds (r1/e2e.py 999)": (999, 999),
    # Added 23 Nov 2026 (PLAN R1-SCREEN-MEASURE-CHOICES (6)); AI-assisted (Claude, coordinating chat).
    "supplementary screening measurement (R1-SCREEN-MEASURE; r1/noise/screen_design.py on mac-screen-measure-20261123)": (3301, 3420),
}


def sweep_instance_seed_universe() -> set[int]:
    """The 8 T0 nodes x 18 sweep instance seeds, by ``r1.c3.p3_split.t0_instance_seed`` (a tested copy of the law)."""
    from r1.c3.p3_split import T0_INSTANCES_PER_NODE, T0_NODES, t0_instance_seed
    return {t0_instance_seed(node, k) for node in T0_NODES for k in range(T0_INSTANCES_PER_NODE)}


def declared_d3_seeds() -> dict[str, set[int]]:
    return {"instance": set(INSTANCE_SEEDS), "smoke": set(SMOKE_SEEDS),
            "smoke_replicate": {s for seed in SMOKE_SEEDS for s in replicate_seeds(seed)},
            "replicate": {s for seed in INSTANCE_SEEDS for s in replicate_seeds(seed)},
            "audit": {s for seed in INSTANCE_SEEDS for s in audit_seeds(seed)}}


def check_namespaces() -> dict:
    """Raise D3InputError if a declared D.3 seed block meets another block or any reserved namespace."""
    blocks = declared_d3_seeds()
    names = sorted(blocks)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            if blocks[names[a]] & blocks[names[b]]:
                raise D3InputError(f"D.3 {names[a]} and {names[b]} seeds overlap")
    report = {"d3_blocks": {k: [min(v), max(v), len(v)] for k, v in blocks.items()}, "reserved": {}}
    sweep = sweep_instance_seed_universe()
    for label, interval in RESERVED_SEED_NAMESPACES.items():
        used = sweep if interval is None else set(range(interval[0], interval[1] + 1))
        for name, block in blocks.items():
            if block & used:
                raise D3InputError(f"D.3 {name} seeds meet reserved namespace {label!r}")
        report["reserved"][label] = [min(used), max(used), len(used)]
    return report


# ---- schema ---------------------------------------------------------------------------------------------------------
NOISE_SOURCE_PATH = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SOURCE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
HEADER_KEYS = frozenset({"schema", "stage", "predeclaration_sha256", "noise_source_sha256", "sigma_node", "arms",
                         "a6_entered", "repetitions", "rows"})
ROW_KEYS_V1 = frozenset({"campaign_id", "stage", "arm", "node", "instance_id", "instance_seed", "repetition",
                         "memory_mode", "status", "y_raw", "worker_runs", "llm_calls", "ended_on", "audit_seeds",
                         "start_config_hash", "final_config_hash"})
# Revision 4 fields. R1-HOST-FREE (2)(c): gpu_model. R1-CARD-SHARE (3): infra_attempts (descriptive; >= 1).
# R1-D3-OUTCOMES2: (a) y_raw_w; (b) the compute fields; (d) the mechanism counts.
COMPUTE_INT_KEYS = ("proposals", "llm_tokens_prompt", "llm_tokens_completion")
COMPUTE_SECONDS_KEYS = ("worker_seconds", "proposer_gpu_seconds", "controller_seconds", "wall_seconds")
MECHANISM_KEYS = ("duplicates_proposed", "duplicates_executed", "rule_skips", "value_skips", "keeps",
                  "distinct_configs_executed")
ROW_KEYS = ROW_KEYS_V1 | frozenset({"gpu_model", "infra_attempts", "y_raw_w", "last_keep_run", "last_improving_run",
                                    *COMPUTE_INT_KEYS, *COMPUTE_SECONDS_KEYS, *MECHANISM_KEYS})
ENDED_ON = ("worker_runs", "llm_call_cap", "no_fundable_candidate")
ENDED_ON_HPO = ("worker_runs", "proposal_cap")
_HEX64 = re.compile(r"[0-9a-f]{64}")
# Names of files this script must never open (labels, test or evaluation values, sweep tables, sealed trees).
_FORBIDDEN_NAME = re.compile(r"(label|evaluation|eval_block|runs\.jsonl|proposals\.jsonl|test_block|_test\.|"
                             r"split|audits?\.jsonl|sealed)", re.I)
_A6_LINE = re.compile(r"^a6_entered: (true|false)$")
_APPROVED_LINE = re.compile(r"^approved: (true|false)$")
MAX_NOTE_BYTES = 1024 * 1024


def refuse_input_path(path) -> Path:
    path = Path(path)
    from r1.c3.analysis_guard import refuse_sealed
    try:
        refuse_sealed(path)
    except RuntimeError:
        raise D3InputError("r1_sealed paths are never inputs of this analysis") from None
    if _FORBIDDEN_NAME.search(path.name):
        raise D3InputError("not a D.3 outcome table (label, test, evaluation, split or sweep files are never inputs)")
    return path


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _check_ended_on(where: str, row: dict, stage: str) -> None:
    runs, calls, ended = row["worker_runs"], row["llm_calls"], row["ended_on"]
    if stage == "HPO-REF":
        if ended not in ENDED_ON_HPO:
            raise D3InputError(f"{where}: ended_on must be one of {ENDED_ON_HPO}")
        if (runs == W) != (ended == "worker_runs"):
            raise D3InputError(f"{where}: ended_on 'worker_runs' if and only if worker_runs = {W}")
        if ended == "proposal_cap" and (row["arm"] != "RS" or row["proposals"] != HPO_PROPOSAL_CAP):
            raise D3InputError(f"{where}: ended_on 'proposal_cap' only for RS at {HPO_PROPOSAL_CAP} proposals")
        return
    if ended not in ENDED_ON:
        raise D3InputError(f"{where}: ended_on must be one of {ENDED_ON}")
    if (runs == W) != (ended == "worker_runs"):
        raise D3InputError(f"{where}: ended_on 'worker_runs' if and only if worker_runs = {W}")
    if ended == "llm_call_cap" and calls != LLM_CALL_CAP:
        raise D3InputError(f"{where}: ended_on 'llm_call_cap' needs llm_calls = {LLM_CALL_CAP}")
    if ended == "no_fundable_candidate" and (row["arm"] not in REPLICATE_ARMS or calls == LLM_CALL_CAP):
        raise D3InputError(f"{where}: ended_on 'no_fundable_candidate' only for {REPLICATE_ARMS} below the cap")
    if ended != "worker_runs" and calls == LLM_CALL_CAP and ended != "llm_call_cap":
        raise D3InputError(f"{where}: a campaign below W at the cap ended on 'llm_call_cap'")


def _check_secondary(where: str, row: dict, stage: str) -> None:
    """Revision 4 fields: GPU model, attempts, Y(w), compute and mechanism counts (pre-declaration §8)."""
    runs = row["worker_runs"]
    if stage == "HPO-REF":
        if row["gpu_model"] is not None:
            raise D3InputError(f"{where}: gpu_model must be null for a reference row (no proposer GPU)")
        if row["llm_calls"] != 0 or row["llm_tokens_prompt"] != 0 or row["llm_tokens_completion"] != 0:
            raise D3InputError(f"{where}: a reference row makes no LLM call")
    elif not isinstance(row["gpu_model"], str) or not row["gpu_model"].strip() or len(row["gpu_model"]) > 128:
        raise D3InputError(f"{where}: gpu_model must be a non-empty string of at most 128 characters")
    if not _is_int(row["infra_attempts"]) or row["infra_attempts"] < 1:
        raise D3InputError(f"{where}: infra_attempts must be an integer >= 1")
    for key in COMPUTE_INT_KEYS + MECHANISM_KEYS:
        if not _is_int(row[key]) or row[key] < 0:
            raise D3InputError(f"{where}: {key} must be a non-negative integer")
    for key in COMPUTE_SECONDS_KEYS:
        if not _is_num(row[key]) or row[key] < 0:
            raise D3InputError(f"{where}: {key} must be a finite non-negative number")
    if stage == "HPO-REF":
        if row["proposals"] > HPO_PROPOSAL_CAP:
            raise D3InputError(f"{where}: proposals above the reference-row cap {HPO_PROPOSAL_CAP}")
        if row["proposer_gpu_seconds"] != 0:
            raise D3InputError(f"{where}: a reference row uses no proposer GPU")
    elif row["proposals"] > row["llm_calls"]:
        raise D3InputError(f"{where}: proposals cannot exceed llm_calls")
    if row["duplicates_executed"] > row["duplicates_proposed"] or row["duplicates_executed"] > runs:
        raise D3InputError(f"{where}: duplicates_executed exceeds duplicates_proposed or worker_runs")
    if row["keeps"] > runs or row["distinct_configs_executed"] > runs:
        raise D3InputError(f"{where}: keeps and distinct_configs_executed cannot exceed worker_runs")
    if row["arm"] not in RULE_LAYER_ARMS and row["rule_skips"] != 0:
        raise D3InputError(f"{where}: rule_skips must be 0 for an arm without the rule layer")
    if row["arm"] not in SCREEN_ARMS and row["value_skips"] != 0:
        raise D3InputError(f"{where}: value_skips must be 0 for an arm without the E1 screen")
    last_keep, last_imp = row["last_keep_run"], row["last_improving_run"]
    if last_keep is None:
        if row["keeps"] != 0:
            raise D3InputError(f"{where}: last_keep_run is null but keeps > 0")
    elif not _is_int(last_keep) or not 1 <= last_keep <= runs or row["keeps"] == 0:
        raise D3InputError(f"{where}: last_keep_run must be null (no keep) or an integer in 1..worker_runs")
    if last_imp is not None and (not _is_int(last_imp) or last_keep is None or not 1 <= last_imp <= last_keep):
        raise D3InputError(f"{where}: last_improving_run must be null or an integer in 1..last_keep_run")
    yw = row["y_raw_w"]
    if not isinstance(yw, dict) or set(yw) != {str(w) for w in BUDGET_POINTS}:
        raise D3InputError(f"{where}: y_raw_w must map exactly {[str(w) for w in BUDGET_POINTS]}")
    for w in BUDGET_POINTS:
        v = yw[str(w)]
        if runs < w:
            if v is not None:
                raise D3InputError(f"{where}: y_raw_w at w = {w} must be null (missing_w) when worker_runs < {w}")
        elif not _is_num(v):
            raise D3InputError(f"{where}: y_raw_w at w = {w} must be a finite number when worker_runs >= {w}")
    if runs == W and yw[str(W)] != row["y_raw"]:
        raise D3InputError(f"{where}: y_raw_w at w = {W} must equal y_raw when the campaign reached W")


def validate_table(obj, stage: str) -> dict:
    """Return the table if it is exactly ``r1_d3_outcome/v2`` for ``stage`` and covers the full design; else refuse."""
    if not isinstance(obj, dict) or set(obj) != HEADER_KEYS:
        raise D3InputError(f"header keys must be exactly {sorted(HEADER_KEYS)}")
    if obj["schema"] != SCHEMA:
        raise D3InputError(f"schema must be {SCHEMA!r}")
    if stage not in STAGES or obj["stage"] != stage:
        raise D3InputError(f"stage must be {stage!r}")
    for key in ("predeclaration_sha256", "noise_source_sha256"):
        if not isinstance(obj[key], str) or not _HEX64.fullmatch(obj[key]):
            raise D3InputError(f"{key} must be 64 lowercase hex digits")
    if obj["noise_source_sha256"] != NOISE_SOURCE_SHA256:
        raise D3InputError("noise_source_sha256 differs from the pinned noise source")
    sig = obj["sigma_node"]
    if not isinstance(sig, dict) or set(sig) != set(NODES) or not all(_is_num(v) and v > 0 for v in sig.values()):
        raise D3InputError(f"sigma_node must map exactly {list(NODES)} to positive finite numbers")
    arms, a6 = obj["arms"], obj["a6_entered"]
    if stage in ("D.3a", "HPO-REF"):
        expected = ARMS_D3A if stage == "D.3a" else ARMS_HPO
        if arms != list(expected) or a6 is not None:
            raise D3InputError(f"{stage} arms must be {list(expected)} and a6_entered null")
    else:
        if a6 not in (True, False) or arms != list(ARMS_D3B_WITH_A6 if a6 else ARMS_D3B):
            raise D3InputError("D.3b a6_entered must be true or false and the arms must follow it")
    reps = obj["repetitions"]
    if not _is_int(reps) or not REPETITIONS <= reps <= 2:
        raise D3InputError(f"repetitions must be an integer in {REPETITIONS}..2 (declared: {REPETITIONS})")
    rows = obj["rows"]
    if not isinstance(rows, list) or not rows:
        raise D3InputError("rows must be a non-empty list")
    seen, ids = set(), set()
    for n, row in enumerate(rows):
        where = f"row {n}"
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise D3InputError(f"{where}: keys must be exactly {sorted(ROW_KEYS)}")
        if row["stage"] != stage:
            raise D3InputError(f"{where}: stage differs from the table's")
        if row["arm"] not in arms:
            raise D3InputError(f"{where}: arm not declared")
        if row["node"] not in NODES:
            raise D3InputError(f"{where}: node not in the D.3 T0 node set")
        seed = row["instance_seed"]
        if not _is_int(seed) or seed not in INSTANCE_SEEDS:
            raise D3InputError(f"{where}: not a declared D.3 instance seed")
        if row["instance_id"] != instance_id(row["node"], seed):
            raise D3InputError(f"{where}: instance_id does not match node and seed")
        rep = row["repetition"]
        if not _is_int(rep) or not 0 <= rep < reps:
            raise D3InputError(f"{where}: repetition outside 0..{reps - 1}")
        if row["campaign_id"] != campaign_id(stage, row["arm"], row["node"], seed, rep):
            raise D3InputError(f"{where}: campaign_id is not the declared name")
        mode = HPO_MEMORY_MODE if stage == "HPO-REF" else MEMORY_MODE
        if row["memory_mode"] != mode:
            raise D3InputError(f"{where}: memory mode must be {mode!r}")
        if row["status"] != "complete":
            raise D3InputError(f"{where}: status is not 'complete': a stage with a campaign that is not complete is "
                               "reported as a STOP, not analysed (pre-declaration §10)")
        if not _is_num(row["y_raw"]):
            raise D3InputError(f"{where}: y_raw must be a finite number")
        runs, calls = row["worker_runs"], row["llm_calls"]
        if not _is_int(runs) or not 0 <= runs <= W:
            raise D3InputError(f"{where}: worker_runs must be an integer in 0..{W}")
        if not _is_int(calls) or not 0 <= calls <= LLM_CALL_CAP:
            raise D3InputError(f"{where}: llm_calls must be an integer in 0..{LLM_CALL_CAP}")
        _check_ended_on(where, row, stage)
        _check_secondary(where, row, stage)
        if row["audit_seeds"] != list(audit_seeds(seed)):
            raise D3InputError(f"{where}: audit seeds differ from the declared seeds of the instance")
        for key in ("start_config_hash", "final_config_hash"):
            if not isinstance(row[key], str) or not _HEX64.fullmatch(row[key]):
                raise D3InputError(f"{where}: {key} must be 64 lowercase hex digits")
        if row["final_config_hash"] == row["start_config_hash"] and row["y_raw"] != 0:
            raise D3InputError(f"{where}: final configuration equals the start configuration, so y_raw must be 0")
        if row["campaign_id"] in ids:
            raise D3InputError(f"{where}: duplicate campaign_id")
        ids.add(row["campaign_id"])
        seen.add((row["arm"], row["node"], seed, rep))
    starts, gpus = {}, {}
    for row in rows:
        if starts.setdefault(row["node"], row["start_config_hash"]) != row["start_config_hash"]:
            raise D3InputError("a node has more than one start configuration")
        # R1-HOST-FREE (2)(c): all arms (and repetitions) of one instance are served by one GPU model.
        if gpus.setdefault(row["instance_id"], row["gpu_model"]) != row["gpu_model"]:
            raise D3InputError("the arms of one instance were served by more than one GPU model (R1-HOST-FREE (2)(c))")
    design = {(a, n, s, r) for a in arms for n in NODES for s in INSTANCE_SEEDS for r in range(reps)}
    if seen != design:
        raise D3InputError(f"the table does not cover the declared design: {len(design - seen)} campaigns missing")
    return obj


def load_table(path, stage: str) -> dict:
    path = refuse_input_path(path)
    if path.suffix != ".json":
        raise D3InputError("an outcome table is a .json file")
    try:
        size = path.stat().st_size
    except OSError:
        raise D3InputError("cannot stat the outcome table") from None
    if size > MAX_TABLE_BYTES:
        raise D3InputError(f"outcome table larger than {MAX_TABLE_BYTES} bytes")
    try:
        obj = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise D3InputError("cannot read a JSON outcome table") from None
    return validate_table(obj, stage)


def read_a6_declaration(note_path) -> bool:
    """The D.3b note's single key line ``a6_entered: true|false`` (fixed before D.3b launches)."""
    path = Path(note_path)
    from r1.c3.analysis_guard import refuse_sealed
    try:
        refuse_sealed(path)
    except RuntimeError:
        raise D3InputError("r1_sealed paths are never inputs of this analysis") from None
    if path.suffix != ".md":
        raise D3InputError("the D.3b note is a .md file")
    try:
        if path.stat().st_size > MAX_NOTE_BYTES:
            raise D3InputError(f"the D.3b note is larger than {MAX_NOTE_BYTES} bytes")
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeDecodeError):
        raise D3InputError("cannot read the D.3b note") from None
    approved = [m.group(1) for line in lines if (m := _APPROVED_LINE.match(line))]
    if approved != ["true"]:
        raise D3InputError("the D.3b note must hold exactly one line 'approved: true' (a signed note)")
    hits = [m.group(1) for line in lines if (m := _A6_LINE.match(line))]
    if len(hits) != 1:
        raise D3InputError("the D.3b note must hold exactly one line 'a6_entered: true|false'")
    return hits[0] == "true"


def check_pair(d3a: dict, other: dict) -> None:
    """D.3b (and the HPO-REF rows) are paired on D.3a's instances and seeds (R1-D3-MIN, R1-D3-HPO-REF): same
    pre-declaration, noise, sigma, repetitions and start configurations; for D.3b also the same GPU model per instance
    as D.3a's arms (R1-HOST-FREE (2)(c): D.3b's contrasts difference its arms with D.3a's A0 and A2)."""
    name = other["stage"]
    for key in ("predeclaration_sha256", "noise_source_sha256", "sigma_node", "repetitions"):
        if d3a[key] != other[key]:
            raise D3InputError(f"D.3a and {name} tables differ in {key}")
    a_starts = {r["node"]: r["start_config_hash"] for r in d3a["rows"]}
    b_starts = {r["node"]: r["start_config_hash"] for r in other["rows"]}
    if a_starts != b_starts:
        raise D3InputError(f"D.3a and {name} start configurations differ")
    if name == "D.3b":
        a_gpu = {r["instance_id"]: r["gpu_model"] for r in d3a["rows"]}
        b_gpu = {r["instance_id"]: r["gpu_model"] for r in other["rows"]}
        if a_gpu != b_gpu:
            raise D3InputError("an instance's D.3b arms were served by a GPU model other than its D.3a arms' "
                               "(R1-HOST-FREE (2)(c))")


def verify_sigma_against_noise_source(sigma_node: dict, summary_path=None, expected_sha256: str = NOISE_SOURCE_SHA256,
                                      tol: float = 1e-12) -> None:
    """The tables' sigma_node must equal ``dataset.noise_table`` on the pinned noise summary (sha256-checked)."""
    from r1.harness import REPO
    path = Path(summary_path) if summary_path is not None else REPO / NOISE_SOURCE_PATH
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise D3InputError("the noise summary's sha256 differs from the pinned noise source")
    from r1.c3.dataset import noise_table
    table = noise_table(path)
    for node in NODES:
        if node not in table or abs(table[node]["sigma_node"] - float(sigma_node[node])) > tol:
            raise D3InputError(f"{node}: sigma_node in the table differs from the noise source")


# ---- statistics -----------------------------------------------------------------------------------------------------
def outcome_matrix(table: dict, reps_used: int) -> dict:
    """arm -> node -> Y over INSTANCE_SEEDS (sigma_node units; the mean over repetitions 0..reps_used-1)."""
    acc: dict = {}
    for row in table["rows"]:
        if row["repetition"] >= reps_used:
            continue
        acc.setdefault(row["arm"], {}).setdefault(row["node"], {}).setdefault(row["instance_seed"], [None] * reps_used)
        acc[row["arm"]][row["node"]][row["instance_seed"]][row["repetition"]] = \
            float(row["y_raw"]) / float(table["sigma_node"][row["node"]])
    return {arm: {node: np.array([float(np.mean(by_seed[s])) for s in INSTANCE_SEEDS]) for node, by_seed in nodes.items()}
            for arm, nodes in acc.items()}


def paired_contrast(ya: dict, yb: dict, *, boot: int = BOOT, seed: int = BOOT_SEED) -> dict:
    """Node-equal-weighted mean paired difference, stratified t test (two-sided) and intervals."""
    diffs = {node: np.asarray(ya[node], float) - np.asarray(yb[node], float) for node in NODES}
    m = {node: len(d) for node, d in diffs.items()}
    if any(v < 2 for v in m.values()):
        raise D3InputError("every node needs at least two paired instances")
    n_nodes = len(NODES)
    node_means = {node: float(np.mean(d)) for node, d in diffs.items()}
    est = float(np.mean([node_means[node] for node in NODES]))
    var = sum(float(np.var(diffs[node], ddof=1)) / m[node] for node in NODES) / n_nodes ** 2
    se = math.sqrt(var)
    df = sum(v - 1 for v in m.values())
    tq = float(stats.t.ppf(0.5 + CI_LEVEL / 2, df))
    if se > 0:
        t = est / se
        p = float(2 * stats.t.sf(abs(t), df))
    else:  # degenerate rule (pre-declaration §7.3)
        t = 0.0 if est == 0 else math.copysign(math.inf, est)
        p = 1.0 if est == 0 else 0.0
    # Draw order (declared): one generator; per node in NODES order, a (boot x m_n) array of instance indices.
    rng = np.random.Generator(np.random.PCG64(seed))
    draws = np.mean([diffs[node][rng.integers(0, m[node], size=(boot, m[node]))].mean(axis=1) for node in NODES],
                    axis=0)
    lo, hi = np.quantile(draws, [(1 - CI_LEVEL) / 2, 0.5 + CI_LEVEL / 2], method="linear")
    return {"estimate": est, "se": se, "t": t, "df": df, "p_two_sided": p,
            "ci95_t": [est - tq * se, est + tq * se], "ci95_bootstrap": [float(lo), float(hi)],
            "n_instances": sum(m.values()), "n_nodes": n_nodes,
            "per_node": {node: {"mean": node_means[node], "sd": float(np.std(diffs[node], ddof=1)), "n": m[node]}
                         for node in NODES},
            "degenerate_se": se == 0}


def holm(pvalues: list[float], alpha: float = ALPHA) -> tuple[list[float], list[bool]]:
    """Holm step-down: adjusted p-values (monotone, capped at 1) and rejections at family-wise alpha."""
    k = len(pvalues)
    order = sorted(range(k), key=lambda i: (pvalues[i], i))
    adjusted = [0.0] * k
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (k - rank) * pvalues[i]))
        adjusted[i] = running
    reject = [adjusted[i] <= alpha for i in range(k)]
    return adjusted, reject


_DESCRIPTIVE_DROP = ("t", "p_two_sided")


def _family(name: str, pairs, ys: dict, *, primary: bool = True, status: str | None = None) -> dict:
    results = [dict(paired_contrast(ys[a], ys[b]), contrast=f"{a} - {b}", arm=a, reference=b) for a, b in pairs]
    if primary:
        adjusted, reject = holm([r["p_two_sided"] for r in results])
        for r, adj, rej in zip(results, adjusted, reject):
            r["p_holm"], r["reject_holm"] = adj, rej
            # The declared reading (§7.4): a rejection counts in the direction of its estimate.
            r["holm_direction"] = ("favourable" if r["estimate"] > 0 else "unfavourable") if rej else "none"
        return {"family": name, "status": "analysed", "alpha_familywise": ALPHA, "sided": "two-sided",
                "multiplicity": f"Holm step-down within this family ({len(results)} contrasts)",
                "contrasts": results}
    for r in results:   # descriptive: no test statistic, no p-value, no verdict
        for key in _DESCRIPTIVE_DROP:
            r.pop(key, None)
    return {"family": name, "status": status or "descriptive (repetitions beyond the declared count; no verdict)",
            "contrasts": results}


def _usage(table: dict) -> dict:
    ended_values = ENDED_ON_HPO if table["stage"] == "HPO-REF" else ENDED_ON
    out = {}
    for arm in table["arms"]:
        rows = [r for r in table["rows"] if r["arm"] == arm and r["repetition"] < REPETITIONS]
        out[arm] = {"campaigns": len(rows),
                    "mean_worker_runs": float(np.mean([r["worker_runs"] for r in rows])),
                    "mean_llm_calls": float(np.mean([r["llm_calls"] for r in rows])),
                    "ended_on": {k: sum(r["ended_on"] == k for r in rows) for k in ended_values},
                    "mean_y_sigma_units": float(np.mean([r["y_raw"] / table["sigma_node"][r["node"]] for r in rows])),
                    "infra_attempts_above_one": sum(r["infra_attempts"] > 1 for r in rows),
                    "gpu_models": sorted({str(r["gpu_model"]) for r in rows})}
    return out


# ---- secondary outcomes (R1-D3-OUTCOMES2; descriptive, no verdict) ------------------------------------------------
def budget_curve(table: dict) -> dict:
    """(a) Y(w) for w in BUDGET_POINTS: per arm and node, the mean of y_raw_w / sigma_node over the campaigns that
    reached w (repetitions < REPETITIONS), with the count; a missing w is never imputed (``missing_w``)."""
    out = {}
    for arm in table["arms"]:
        out[arm] = {}
        for node in NODES:
            rows = [r for r in table["rows"] if r["arm"] == arm and r["node"] == node and r["repetition"] < REPETITIONS]
            cell = {}
            for w in BUDGET_POINTS:
                vals = [r["y_raw_w"][str(w)] / table["sigma_node"][node] for r in rows
                        if r["y_raw_w"][str(w)] is not None]
                cell[str(w)] = {"mean": float(np.mean(vals)) if vals else None, "n": len(vals),
                                "missing_w": len(rows) - len(vals)}
            out[arm][node] = cell
    return out


def runs_to_match(curves: dict, reference: str = "A0") -> dict:
    """(c) Per node, the smallest w at which an arm's mean Y(w) reaches the reference's mean Y(20); ``None`` if it
    does not within BUDGET_POINTS or the reference has no Y(20). ``complete`` is False when a mean used rests on
    fewer campaigns than the node's instances (some campaigns ended before w)."""
    ref = curves.get(reference)
    out = {}
    for arm, nodes in curves.items():
        out[arm] = {}
        for node in NODES:
            target = ref[node][str(W)] if ref else None
            hit, complete = None, True
            if target is None or target["mean"] is None:
                out[arm][node] = {"w": None, "reference_mean_y20": None, "complete": False}
                continue
            complete = target["missing_w"] == 0
            for w in BUDGET_POINTS:
                cell = nodes[node][str(w)]
                complete = complete and cell["missing_w"] == 0
                if cell["mean"] is not None and cell["mean"] >= target["mean"]:
                    hit = w
                    break
            out[arm][node] = {"w": hit, "reference_mean_y20": target["mean"], "complete": complete}
    return out


def compute_and_mechanisms(table: dict) -> dict:
    """(b) compute per campaign and (d) mechanism counts per campaign: per arm, means over campaigns (declared
    repetitions), plus the share of campaigns with an improving keep and the mean of the last improving run."""
    out = {}
    for arm in table["arms"]:
        rows = [r for r in table["rows"] if r["arm"] == arm and r["repetition"] < REPETITIONS]
        cell = {f"mean_{k}": float(np.mean([r[k] for r in rows]))
                for k in ("worker_runs", "llm_calls") + COMPUTE_INT_KEYS + COMPUTE_SECONDS_KEYS + MECHANISM_KEYS}
        imp = [r["last_improving_run"] for r in rows if r["last_improving_run"] is not None]
        keep = [r["last_keep_run"] for r in rows if r["last_keep_run"] is not None]
        cell.update(campaigns=len(rows), campaigns_with_improving_keep=len(imp),
                    mean_last_improving_run=float(np.mean(imp)) if imp else None,
                    mean_last_keep_run=float(np.mean(keep)) if keep else None)
        out[arm] = cell
    return out


def node_arm_means(table: dict) -> dict:
    """arm -> node -> mean primary Y (sigma_node units, declared repetitions)."""
    ys = outcome_matrix(table, REPETITIONS)
    return {arm: {node: float(np.mean(v)) for node, v in nodes.items()} for arm, nodes in ys.items()}


OFFLINE_ONLINE_ARMS = ("A2", "A3", "A5")   # claim sheet §5 item 7: arms with an offline per-node utility


def offline_online_agreement(gate_node_utility: dict, loop_means: dict, arms=OFFLINE_ONLINE_ARMS) -> dict:
    """(e) Per node and arm, the gate's per-node utility beside the arm's closed-loop mean Y, and the rank agreement
    of the arms per node (Kendall tau-b; ``None`` when undefined), with its mean over the nodes where it is defined.

    Its input is the per-node utility the preregistered analysis already writes; this function is pure and is not
    wired to read any gate file (the source file and its key are an open field of the pre-declaration, §7.5)."""
    per_node, taus = {}, []
    for node in NODES:
        off = [float(gate_node_utility[a][node]) for a in arms]
        on = [float(loop_means[a][node]) for a in arms]
        tau = None
        if len(set(off)) > 1 and len(set(on)) > 1:
            tau = float(stats.kendalltau(off, on).statistic)
            taus.append(tau)
        per_node[node] = {"offline_utility": dict(zip(arms, off)), "closed_loop_mean_y": dict(zip(arms, on)),
                          "kendall_tau": tau}
    return {"arms": list(arms), "per_node": per_node, "mean_kendall_tau": float(np.mean(taus)) if taus else None,
            "nodes_with_tau": len(taus), "status": "descriptive (no test, no verdict)"}


def secondary(table: dict) -> dict:
    curves = budget_curve(table)
    return {"status": "descriptive (R1-D3-OUTCOMES2; no p-value, no verdict)", "budget_curve": curves,
            "compute_and_mechanisms": compute_and_mechanisms(table), "node_arm_mean_y": node_arm_means(table)}


# ---- design figure and declared readings --------------------------------------------------------------------------
def detectable_difference(k: int, *, alpha: float = ALPHA, power: float = POWER, n_nodes: int = len(NODES),
                          m: int = len(INSTANCE_SEEDS)) -> dict:
    """The smallest true paired difference, in units of sd(D) (the within-node sd of the paired difference, assumed
    equal across nodes), that a two-sided test at Holm's first step (alpha / k) detects with the stated power, for the
    declared design (n_nodes x m paired instances). A design figure, not a claim: sd(D) has no source before D.3."""
    n = n_nodes * m
    df = n_nodes * (m - 1)
    a = alpha / k
    z = (stats.norm.ppf(1 - a / 2) + stats.norm.ppf(power)) / math.sqrt(n)
    t = (stats.t.ppf(1 - a / 2, df) + stats.t.ppf(power, df)) / math.sqrt(n)
    z_last = (stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)) / math.sqrt(n)
    t_last = (stats.t.ppf(1 - alpha / 2, df) + stats.t.ppf(power, df)) / math.sqrt(n)
    return {"contrasts": k, "alpha_first_step": a, "power": power, "n_paired_instances": n, "df": df,
            "mde_first_step_sd_units_normal": float(z), "mde_first_step_sd_units_t": float(t),
            "mde_last_step_sd_units_normal": float(z_last), "mde_last_step_sd_units_t": float(t_last)}


READING_TEXT = {   # GOAL_METRIC_ALIGNMENT_PROPOSAL §6, adopted by R1-ALIGN-OUTCOME; row 5 without its last sentence
    1: "learned control raises audited gain at matched budget; the decomposition says how much each part buys",
    2: "learned control raises audited gain at matched budget (from the closed loop); the gate result is reported as "
       "measured, with its power; the offline-online disagreement is a finding",
    3: "one-step gains do not carry into the loop; where they are lost is reported",
    4: "noise-aware rule control is enough at this task complexity; effect sizes and intervals bound what learning "
       "could add; the tier table says whether that changes with code-level edits",
    5: "the measured negative: C1 and the theory stand, and the loop is shown not to be limited by its keep and "
       "screen decisions on these tasks",
}
RULE_LAYER_ALONE_TEXT = "de-duplication raises the audited gain; the one-step rule adds no demonstrated gain"


def _by_name(family: dict) -> dict:
    return {c["contrast"]: c for c in family.get("contrasts", []) if isinstance(c, dict)}


def declared_readings(families: dict) -> dict:
    """The declared readings (pre-declaration §7.4), set by rule from the two Holm families.

    rule_gain: 'gain' iff A2 - A0 is Holm-rejected in D.3a with a positive estimate; 'harm' iff rejected with a
    negative estimate; else 'none'. learned_gain: 'gain' iff A3 - A2 or A5 - A2 is Holm-rejected in D.3b with a
    positive estimate; 'harm' iff neither is favourable and at least one is rejected unfavourably; else 'none';
    'not_run' if the D.3b family is not analysed. gain_source (only when rule_gain = 'gain'): 'rule_layer_alone' iff
    A0R - A0 is rejected favourably and A2 - A0R is not; 'one_step_rule_adds' iff A2 - A0R is rejected favourably;
    else 'not_separated'. The headline row is given for each gate verdict; the gate itself is not read here."""
    a = _by_name(families["D.3a"])
    direction = lambda c: c["holm_direction"]   # noqa: E731
    rule_gain = {"favourable": "gain", "unfavourable": "harm", "none": "none"}[direction(a["A2 - A0"])]
    gain_source = None
    if rule_gain == "gain":
        if direction(a["A2 - A0R"]) == "favourable":
            gain_source = "one_step_rule_adds"
        elif direction(a["A0R - A0"]) == "favourable":
            gain_source = "rule_layer_alone"
        else:
            gain_source = "not_separated"
    b = families.get("D.3b", {})
    if b.get("status") != "analysed":
        learned_gain = "not_run"
    else:
        bn = _by_name(b)
        dirs = [direction(bn["A3 - A2"]), direction(bn["A5 - A2"])]
        learned_gain = "gain" if "favourable" in dirs else ("harm" if "unfavourable" in dirs else "none")
    rows = {}
    for gate in ("pass", "fail", "stop"):
        if rule_gain != "gain":
            row = 5
        elif learned_gain == "not_run":
            row = None
        elif learned_gain == "gain":
            row = {"pass": 1, "fail": 2, "stop": 1}[gate]
        else:
            row = {"pass": 3, "fail": 4, "stop": None}[gate]
        text = READING_TEXT.get(row) if row is not None else None
        if gain_source == "rule_layer_alone" and row in (3, 4):
            text = RULE_LAYER_ALONE_TEXT
        rows[gate] = {"row": row, "headline": text}
    rows["stop"]["note"] = ("gate STOP: the gate is reported as a STOP with no verdict; the closed-loop reading stands "
                            "on its own (pre-declaration §7.4; author item)")
    notes = []
    if rule_gain == "harm":
        notes.append("A2 - A0 is rejected in the unfavourable direction: A2 lowers the audited gain against A0; "
                     "reported as such under row 5")
    if learned_gain == "harm":
        notes.append("A3 - A2 or A5 - A2 is rejected in the unfavourable direction and neither favourably: a learned "
                     "forecast lowers the audited gain against A2; reported as such under 'no gain over A2'")
    return {"rule_gain": rule_gain, "learned_gain": learned_gain, "gain_source": gain_source, "notes": notes,
            "qualifier": RULE_LAYER_ALONE_TEXT if gain_source == "rule_layer_alone" else None,
            "headline_by_gate_verdict": rows,
            "definition": "Holm rejection within the family, counted in the direction of its estimate"}


D3B_NOT_RUN_REASONS = ("stopped", "not_started")   # R1-D3B-UNCONDITIONAL: 'gate_not_passed' is no longer a reason


def analyse(d3a: dict, d3b: dict | None = None, d3b_not_run: str | None = None,
            a6_declared: bool | None = None, hpo: dict | None = None) -> dict:
    """Every pre-declared contrast. ``a6_declared`` comes from the signed D.3b note (``read_a6_declaration``)."""
    validate_table(d3a, "D.3a")
    ys = outcome_matrix(d3a, REPETITIONS)
    report = {"schema": REPORT_SCHEMA, "predeclaration_sha256": d3a["predeclaration_sha256"],
              "repetitions_declared": REPETITIONS, "repetitions_in_tables": d3a["repetitions"],
              "nodes": list(NODES), "instance_seeds": list(INSTANCE_SEEDS),
              "W": W, "llm_call_cap": LLM_CALL_CAP, "outcome_units": "sigma_node",
              "families": {"D.3a": _family("D.3a", CONTRASTS_D3A, ys)}, "usage": {"D.3a": _usage(d3a)},
              "secondary": {"D.3a": secondary(d3a)}}
    extra = d3a["repetitions"] > REPETITIONS
    if extra:
        report["families"]["D.3a_all_repetitions"] = _family("D.3a_all_repetitions", CONTRASTS_D3A,
                                                             outcome_matrix(d3a, d3a["repetitions"]), primary=False)
    if hpo is not None:
        validate_table(hpo, "HPO-REF")
        check_pair(d3a, hpo)
        report["reference_rows"] = _family("HPO-REF", CONTRASTS_HPO, {**ys, **outcome_matrix(hpo, REPETITIONS)},
                                           primary=False,
                                           status="descriptive (R1-D3-HPO-REF; outside the Holm families; no verdict)")
        report["usage"]["HPO-REF"] = _usage(hpo)
        report["secondary"]["HPO-REF"] = secondary(hpo)
    else:
        report["reference_rows"] = {"family": "HPO-REF", "status": "not_run",
                                    "contrasts": [f"{a} - {b}" for a, b in CONTRASTS_HPO]}
    if d3b is None:
        if d3b_not_run not in D3B_NOT_RUN_REASONS or a6_declared is not None:
            raise D3InputError(f"without a D.3b table, state why: one of {D3B_NOT_RUN_REASONS}")
        report["families"]["D.3b"] = {"family": "D.3b", "status": "not_run", "reason": d3b_not_run,
                                      "contrasts": [f"{a} - {b}" for a, b in CONTRASTS_D3B]}
        return _finish(report, a6_declared)
    if d3b_not_run is not None:
        raise D3InputError("a D.3b table and a not-run reason are mutually exclusive")
    if a6_declared not in (True, False):
        raise D3InputError("a D.3b analysis needs the signed D.3b note's a6_entered declaration")
    validate_table(d3b, "D.3b")
    if d3b["a6_entered"] is not a6_declared:
        raise D3InputError("the D.3b table's a6_entered differs from the D.3b note")
    check_pair(d3a, d3b)
    pairs = CONTRASTS_D3B + ((CONTRAST_A6,) if a6_declared else ())
    report["families"]["D.3b"] = _family("D.3b", pairs, {**ys, **outcome_matrix(d3b, REPETITIONS)})
    report["families"]["D.3b"]["a6_entered"] = a6_declared
    report["usage"]["D.3b"] = _usage(d3b)
    report["secondary"]["D.3b"] = secondary(d3b)
    if extra:
        all_ys = {**outcome_matrix(d3a, d3a["repetitions"]), **outcome_matrix(d3b, d3b["repetitions"])}
        report["families"]["D.3b_all_repetitions"] = _family("D.3b_all_repetitions", pairs, all_ys, primary=False)
    return _finish(report, a6_declared)


def _finish(report: dict, a6_declared) -> dict:
    """Runs-to-match over every analysed table's budget curve, the design figure and the declared readings."""
    curves = {}
    for stage in ("D.3a", "D.3b", "HPO-REF"):
        if stage in report["secondary"]:
            curves.update(report["secondary"][stage]["budget_curve"])
    report["secondary"]["runs_to_match"] = runs_to_match(curves)
    report["design"] = _design(a6_declared)
    report["readings"] = declared_readings(report["families"])
    return report


def _design(a6_declared) -> dict:
    k_b = len(CONTRASTS_D3B) + (1 if a6_declared else 0)
    return {"status": "design figure at the declared design, not a claim (pre-declaration §7.3)",
            "D.3a": detectable_difference(len(CONTRASTS_D3A)), "D.3b": detectable_difference(k_b)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyse")
    a.add_argument("--d3a", required=True)
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--d3b")
    g.add_argument("--d3b-not-run", choices=D3B_NOT_RUN_REASONS)
    a.add_argument("--d3b-note", help="the signed D.3b authorization note (required with --d3b)")
    a.add_argument("--hpo-ref", help="the HPO-REF outcome table (R1-D3-HPO-REF; descriptive), if it exists")
    a.add_argument("--predeclaration", required=True)
    a.add_argument("--out", required=True)
    sub.add_parser("namespaces")
    sub.add_parser("design")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "namespaces":
            print(json.dumps(check_namespaces(), indent=1, sort_keys=True))
            return 0
        if args.cmd == "design":   # the detectable-difference figure of §7.3 (no input)
            print(json.dumps({"without_A6": _design(False), "with_A6": _design(True)}, indent=1, sort_keys=True))
            return 0
        if bool(args.d3b) != bool(args.d3b_note):
            raise D3InputError("--d3b and --d3b-note go together")
        d3a = load_table(args.d3a, "D.3a")
        d3b = load_table(args.d3b, "D.3b") if args.d3b else None
        a6 = read_a6_declaration(args.d3b_note) if args.d3b_note else None
        hpo = load_table(args.hpo_ref, "HPO-REF") if args.hpo_ref else None
        predecl = Path(args.predeclaration)
        if _sha256(predecl) != d3a["predeclaration_sha256"]:
            raise D3InputError("the pre-declaration file's sha256 differs from the tables' header")
        verify_sigma_against_noise_source(d3a["sigma_node"])
        report = analyse(d3a, d3b, args.d3b_not_run, a6, hpo)
        report["inputs"] = {"d3a_sha256": _sha256(Path(args.d3a)),
                            "d3b_sha256": _sha256(Path(args.d3b)) if args.d3b else None,
                            "hpo_ref_sha256": _sha256(Path(args.hpo_ref)) if args.hpo_ref else None,
                            "d3b_note_sha256": _sha256(Path(args.d3b_note)) if args.d3b_note else None,
                            "predeclaration": str(predecl), "analysis_sha256": _sha256(Path(__file__))}
        try:
            with open(args.out, "x") as fh:   # never overwrite an analysis output
                fh.write(json.dumps(report, indent=1, sort_keys=True) + "\n")
        except FileExistsError:
            raise D3InputError("the output file exists; an analysis output is never overwritten") from None
    except D3InputError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
