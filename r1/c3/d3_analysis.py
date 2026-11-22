# AI-assisted (Claude, chat session, 22 Nov 2026; subagent). DRAFT; not signed; not reviewed.
"""D.3 closed-loop analysis on T0 (R1-D3-MIN, R1-MINSUB-CHOICES (4)): every pre-declared contrast of both stages.

AI-assisted (Claude, chat session, 22 Nov 2026; written by a subagent). DRAFT; not signed; not reviewed. Tier E
(R1-PROCESS-TIERS: "the analysis scripts of D.3"): this file's sha256 is bound by the D.3 pre-declaration
(``docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`` §9) and must not change after it is signed.

What it reads, and nothing else
-------------------------------
* One or two **per-campaign outcome tables** in schema ``r1_d3_outcome/v1`` (pre-declaration §8): the D.3a table
  (required) and the D.3b table (only if D.3b ran). Each row is one closed-loop campaign with its fresh-seed audited
  outcome ``y_raw``. A table that is not exactly this schema, or does not cover exactly the declared design, is
  refused before any statistic is computed.
* The pre-declaration file itself (only to compare its sha256 with the tables' header).
* The pinned noise summary ``results/r1/noise/D28_REPAIR_20261027/summary.json`` (sha256-checked), only to check that
  the tables' ``sigma_node`` values equal ``r1.c3.dataset.noise_table``'s. It holds noise-floor constants, no label.

It opens no label block, test partition, evaluation block, sweep table or ``r1_sealed`` path: ``refuse_input_path``
refuses such paths by name before anything is opened, and no code path here reads any other file.

Statistics (pre-declaration §7)
-------------------------------
Per instance (node n, instance seed s) and arm a: Y = y_raw / sigma_node(n) (the mean over repetitions if the
pre-declaration declares two). For a contrast a - b: D_{n,s} = Y_{n,s}(a) - Y_{n,s}(b) on the same instance.
* Estimate: the node-equal-weighted mean D = (1/N) sum_n mean_s D_{n,s}.
* Standard error: (1/N) sqrt(sum_n s_n^2 / m_n), s_n the within-node sd of D (ddof 1), m_n its instance count.
* Test: two-sided Student t with df = sum_n (m_n - 1); Holm step-down within each stage's family at alpha 0.05.
* Interval: 95 % t interval (unadjusted), and a node-stratified percentile bootstrap interval (instances resampled
  within node; 10,000 resamples; PCG64 seed 20261122) reported beside it (descriptive).
* Per-node means and descriptive per-arm usage (worker runs, LLM calls, what ended the campaign).

Usage::

    python -m r1.c3.d3_analysis analyse --d3a T.json [--d3b T.json | --d3b-not-run REASON] \
        --predeclaration docs/r1/authorizations/<signed pre-declaration>.md --out report.json
    python -m r1.c3.d3_analysis namespaces      # the seed-namespace disjointness check (§4 of the pre-declaration)
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

SCHEMA = "r1_d3_outcome/v1"
REPORT_SCHEMA = "r1_d3_report/v1"
STAGES = ("D.3a", "D.3b")

# PRE-WDBC B primary T0 set: the seven nodes that passed S2-C3b at the sweep-2 launch commit (R1-S2C3B-WDBC); the
# eight T0 nodes are gate.T0_NODES, openml_wdbc is the one left out.
NODES = ("digits_mlp", "openml_breast_w", "openml_climate", "openml_credit_approval", "openml_ionosphere",
         "openml_sonar", "tabular_mlp")
MEMORY_MODE = "append_only_summary"   # R1-MINSUB-CHOICES (4)
W = 20                                # R1-MINSUB-CHOICES (4): as in sweep 2
LLM_CALL_CAP = 80                     # PROPOSED in the pre-declaration §3 (no value on main); fixed by signing
K_AUDIT = 10                          # R1-MINSUB-CHOICES (4)

ARMS_D3A = ("A0", "A1", "A2", "FIXR3", "EGATE", "LADDER")   # R1-D3-MIN + R1-MINSUB-CHOICES (4): six rule arms
ARMS_D3B = ("A3", "A5")                                      # R1-D3-MIN; A6 only under RUNBOOK P.5
ARMS_D3B_WITH_A6 = ("A3", "A5", "A6")
CONTRASTS_D3A = (("A1", "A0"), ("A2", "A0"), ("FIXR3", "A0"), ("EGATE", "A0"), ("LADDER", "A0"), ("LADDER", "A2"))
CONTRASTS_D3B = (("A3", "A2"), ("A5", "A2"), ("A3", "A0"), ("A5", "A0"))
CONTRAST_A6 = ("A6", "A5")
ALPHA = 0.05
BOOT = 10_000
BOOT_SEED = 20261122
CI_LEVEL = 0.95

# ---- seeds (pre-declaration §4). Proposed blocks; disjointness is checked by ``check_namespaces``. ------------------
INSTANCE_SEEDS = tuple(range(6201, 6219))       # 18 deployment instances per node, the same seeds on every node
REPLICATE_SEED_BASE = 6500                       # replicate j (1..9) of instance index i: 6500 + 10 i + j
AUDIT_SEED_BASE = 6700                           # audit seed k (1..10) of instance index i: 6700 + 10 i + k
MAX_REPLICATE_J = 9


def instance_index(seed: int) -> int:
    if seed not in INSTANCE_SEEDS:
        raise D3InputError(f"instance seed {seed!r} is not a declared D.3 instance seed")
    return INSTANCE_SEEDS.index(seed)


def replicate_seeds(seed: int) -> tuple[int, ...]:
    """Seeds of replicate runs j = 1..9 (j = 0 is the instance seed itself) for FIXR3 and EGATE."""
    i = instance_index(seed)
    return tuple(REPLICATE_SEED_BASE + 10 * i + j for j in range(1, MAX_REPLICATE_J + 1))


def audit_seeds(seed: int) -> tuple[int, ...]:
    """The K = 10 fresh audit seeds of one instance, shared by every arm and repetition on it."""
    i = instance_index(seed)
    return tuple(AUDIT_SEED_BASE + 10 * i + k for k in range(1, K_AUDIT + 1))


def instance_id(node: str, seed: int) -> str:
    return f"{node}__s{int(seed)}"


def campaign_id(stage: str, arm: str, node: str, seed: int, repetition: int) -> str:
    return f"{stage}__{arm}__{instance_id(node, seed)}__r{int(repetition)}"


# Every seed namespace already used in the repository, with its source (pre-declaration §4.2). Closed intervals.
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
}


def sweep_instance_seed_universe() -> set[int]:
    """The 8 T0 nodes x 18 sweep instance seeds, by ``r1.c3.p3_split.t0_instance_seed`` (a tested copy of the law)."""
    from r1.c3.p3_split import T0_INSTANCES_PER_NODE, T0_NODES, t0_instance_seed
    return {t0_instance_seed(node, k) for node in T0_NODES for k in range(T0_INSTANCES_PER_NODE)}


def declared_d3_seeds() -> dict[str, set[int]]:
    return {"instance": set(INSTANCE_SEEDS),
            "replicate": {s for seed in INSTANCE_SEEDS for s in replicate_seeds(seed)},
            "audit": {s for seed in INSTANCE_SEEDS for s in audit_seeds(seed)}}


def check_namespaces() -> dict:
    """Raise D3InputError if a declared D.3 seed block meets another block or any reserved namespace."""
    blocks = declared_d3_seeds()
    names = sorted(blocks)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            both = blocks[names[a]] & blocks[names[b]]
            if both:
                raise D3InputError(f"D.3 {names[a]} and {names[b]} seeds overlap: {sorted(both)[:5]}")
    report = {"d3_blocks": {k: [min(v), max(v), len(v)] for k, v in blocks.items()}, "reserved": {}}
    sweep = sweep_instance_seed_universe()
    for label, interval in RESERVED_SEED_NAMESPACES.items():
        used = sweep if interval is None else set(range(interval[0], interval[1] + 1))
        for name, block in blocks.items():
            both = block & used
            if both:
                raise D3InputError(f"D.3 {name} seeds meet reserved namespace {label!r}: {sorted(both)[:5]}")
        report["reserved"][label] = [min(used), max(used), len(used)]
    return report


# ---- schema ---------------------------------------------------------------------------------------------------------
NOISE_SOURCE_PATH = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SOURCE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
HEADER_KEYS = frozenset({"schema", "stage", "predeclaration_sha256", "noise_source_sha256", "sigma_node", "arms",
                         "repetitions", "rows"})
ROW_KEYS = frozenset({"campaign_id", "stage", "arm", "node", "instance_id", "instance_seed", "repetition",
                      "memory_mode", "status", "y_raw", "worker_runs", "llm_calls", "ended_on", "audit_seeds",
                      "start_config_hash", "final_config_hash"})
ENDED_ON = ("worker_runs", "llm_call_cap", "no_fundable_candidate")
_HEX64 = re.compile(r"[0-9a-f]{64}")
# Names of files this script must never open (labels, test or evaluation values, sweep tables, sealed trees).
_FORBIDDEN_NAME = re.compile(r"(label|evaluation|eval_block|runs\.jsonl|proposals\.jsonl|test_block|_test\.|"
                             r"split|audits?\.jsonl|sealed)", re.I)


class D3InputError(ValueError):
    """An input refusal: raised before any statistic is computed (pre-declaration §7, §10)."""


def refuse_input_path(path) -> Path:
    path = Path(path)
    from r1.c3.analysis_guard import refuse_sealed
    try:
        refuse_sealed(path)
    except RuntimeError as exc:
        raise D3InputError(str(exc)) from None
    if _FORBIDDEN_NAME.search(path.name):
        raise D3InputError(f"{path.name}: not a D.3 outcome table (label, test, evaluation, split or sweep files "
                           "are never inputs of this analysis)")
    return path


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def validate_table(obj, stage: str) -> dict:
    """Return the table if it is exactly ``r1_d3_outcome/v1`` for ``stage`` and covers the full design; else refuse."""
    if not isinstance(obj, dict) or set(obj) != HEADER_KEYS:
        got = sorted(obj) if isinstance(obj, dict) else type(obj).__name__
        raise D3InputError(f"header keys must be exactly {sorted(HEADER_KEYS)}, got {got}")
    if obj["schema"] != SCHEMA:
        raise D3InputError(f"schema must be {SCHEMA!r}, got {obj['schema']!r}")
    if stage not in STAGES or obj["stage"] != stage:
        raise D3InputError(f"stage must be {stage!r}, got {obj['stage']!r}")
    for key in ("predeclaration_sha256", "noise_source_sha256"):
        if not isinstance(obj[key], str) or not _HEX64.fullmatch(obj[key]):
            raise D3InputError(f"{key} must be 64 lowercase hex digits")
    if obj["noise_source_sha256"] != NOISE_SOURCE_SHA256:
        raise D3InputError("noise_source_sha256 differs from the pinned noise source")
    sig = obj["sigma_node"]
    if not isinstance(sig, dict) or set(sig) != set(NODES) or not all(_is_num(v) and v > 0 for v in sig.values()):
        raise D3InputError(f"sigma_node must map exactly {list(NODES)} to positive finite numbers")
    arms = obj["arms"]
    allowed = (list(ARMS_D3A),) if stage == "D.3a" else (list(ARMS_D3B), list(ARMS_D3B_WITH_A6))
    if arms not in allowed:
        raise D3InputError(f"{stage} arms must be one of {allowed}, got {arms!r}")
    reps = obj["repetitions"]
    if not _is_int(reps) or reps not in (1, 2):
        raise D3InputError("repetitions must be 1 or 2")
    rows = obj["rows"]
    if not isinstance(rows, list) or not rows:
        raise D3InputError("rows must be a non-empty list")
    seen, ids = set(), set()
    for n, row in enumerate(rows):
        where = f"row {n}"
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            got = sorted(row) if isinstance(row, dict) else type(row).__name__
            raise D3InputError(f"{where}: keys must be exactly {sorted(ROW_KEYS)}, got {got}")
        if row["stage"] != stage:
            raise D3InputError(f"{where}: stage {row['stage']!r} in a {stage} table")
        if row["arm"] not in arms:
            raise D3InputError(f"{where}: arm {row['arm']!r} not declared")
        if row["node"] not in NODES:
            raise D3InputError(f"{where}: node {row['node']!r} is not in the D.3 T0 node set")
        seed = row["instance_seed"]
        if not _is_int(seed) or seed not in INSTANCE_SEEDS:
            raise D3InputError(f"{where}: instance seed {seed!r} is not a declared D.3 instance seed")
        if row["instance_id"] != instance_id(row["node"], seed):
            raise D3InputError(f"{where}: instance_id {row['instance_id']!r} does not match node and seed")
        rep = row["repetition"]
        if not _is_int(rep) or not 0 <= rep < reps:
            raise D3InputError(f"{where}: repetition {rep!r} outside 0..{reps - 1}")
        if row["campaign_id"] != campaign_id(stage, row["arm"], row["node"], seed, rep):
            raise D3InputError(f"{where}: campaign_id {row['campaign_id']!r} is not the declared name")
        if row["memory_mode"] != MEMORY_MODE:
            raise D3InputError(f"{where}: memory mode {row['memory_mode']!r}, declared {MEMORY_MODE!r}")
        if row["status"] != "complete":
            raise D3InputError(f"{where}: status {row['status']!r}: a stage with a campaign that is not complete is "
                               "reported as a STOP, not analysed (pre-declaration §10)")
        if not _is_num(row["y_raw"]):
            raise D3InputError(f"{where}: y_raw must be a finite number")
        if not _is_int(row["worker_runs"]) or not 0 <= row["worker_runs"] <= W:
            raise D3InputError(f"{where}: worker_runs must be an integer in 0..{W}")
        if not _is_int(row["llm_calls"]) or not 0 <= row["llm_calls"] <= LLM_CALL_CAP:
            raise D3InputError(f"{where}: llm_calls must be an integer in 0..{LLM_CALL_CAP}")
        if row["ended_on"] not in ENDED_ON:
            raise D3InputError(f"{where}: ended_on must be one of {ENDED_ON}")
        if row["audit_seeds"] != list(audit_seeds(seed)):
            raise D3InputError(f"{where}: audit seeds differ from the declared seeds of instance {seed}")
        for key in ("start_config_hash", "final_config_hash"):
            if not isinstance(row[key], str) or not _HEX64.fullmatch(row[key]):
                raise D3InputError(f"{where}: {key} must be 64 lowercase hex digits")
        if row["final_config_hash"] == row["start_config_hash"] and row["y_raw"] != 0:
            raise D3InputError(f"{where}: final configuration equals the start configuration, so y_raw must be 0")
        if row["campaign_id"] in ids:
            raise D3InputError(f"{where}: duplicate campaign_id {row['campaign_id']!r}")
        ids.add(row["campaign_id"])
        seen.add((row["arm"], row["node"], seed, rep))
    design = {(a, n, s, r) for a in arms for n in NODES for s in INSTANCE_SEEDS for r in range(reps)}
    if seen != design:
        missing = sorted(design - seen)
        raise D3InputError(f"the table does not cover the declared design: {len(missing)} campaigns missing "
                           f"(e.g. {missing[:3]})")
    return obj


def load_table(path, stage: str) -> dict:
    path = refuse_input_path(path)
    try:
        obj = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise D3InputError(f"{path}: cannot read a JSON outcome table: {exc}") from None
    return validate_table(obj, stage)


def check_pair(d3a: dict, d3b: dict) -> None:
    """D.3b is paired on D.3a's instances and seeds (R1-D3-MIN): same pre-declaration, noise, sigma, repetitions."""
    for key in ("predeclaration_sha256", "noise_source_sha256", "sigma_node", "repetitions"):
        if d3a[key] != d3b[key]:
            raise D3InputError(f"D.3a and D.3b tables differ in {key}")
    for table in (d3a, d3b):
        starts = {}
        for row in table["rows"]:
            if starts.setdefault(row["node"], row["start_config_hash"]) != row["start_config_hash"]:
                raise D3InputError(f"{row['node']}: more than one start configuration")
    a_starts = {r["node"]: r["start_config_hash"] for r in d3a["rows"]}
    b_starts = {r["node"]: r["start_config_hash"] for r in d3b["rows"]}
    if a_starts != b_starts:
        raise D3InputError("D.3a and D.3b start configurations differ")


def verify_sigma_against_noise_source(sigma_node: dict, summary_path=None, expected_sha256: str = NOISE_SOURCE_SHA256,
                                      tol: float = 1e-12) -> None:
    """The tables' sigma_node must equal ``dataset.noise_table`` on the pinned noise summary (sha256-checked)."""
    from r1.harness import REPO
    path = Path(summary_path) if summary_path is not None else REPO / NOISE_SOURCE_PATH
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise D3InputError(f"{path}: sha256 differs from the pinned noise source")
    from r1.c3.dataset import noise_table
    table = noise_table(path)
    for node in NODES:
        if node not in table or abs(table[node]["sigma_node"] - float(sigma_node[node])) > tol:
            raise D3InputError(f"{node}: sigma_node in the table differs from the noise source")


# ---- statistics -----------------------------------------------------------------------------------------------------
def outcome_matrix(table: dict) -> dict:
    """arm -> node -> Y over INSTANCE_SEEDS (sigma_node units; the mean over repetitions)."""
    reps = table["repetitions"]
    acc: dict = {}
    for row in table["rows"]:
        acc.setdefault(row["arm"], {}).setdefault(row["node"], {}).setdefault(row["instance_seed"], [None] * reps)
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
    else:
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


def _family(name: str, pairs, ys: dict) -> dict:
    results = [dict(paired_contrast(ys[a], ys[b]), contrast=f"{a} - {b}", arm=a, reference=b) for a, b in pairs]
    adjusted, reject = holm([r["p_two_sided"] for r in results])
    for r, adj, rej in zip(results, adjusted, reject):
        r["p_holm"], r["reject_holm"] = adj, rej
    return {"family": name, "status": "analysed", "alpha_familywise": ALPHA, "sided": "two-sided",
            "multiplicity": "Holm step-down within this family", "contrasts": results}


def _usage(table: dict) -> dict:
    out = {}
    for arm in table["arms"]:
        rows = [r for r in table["rows"] if r["arm"] == arm]
        out[arm] = {"campaigns": len(rows),
                    "mean_worker_runs": float(np.mean([r["worker_runs"] for r in rows])),
                    "mean_llm_calls": float(np.mean([r["llm_calls"] for r in rows])),
                    "ended_on": {k: sum(r["ended_on"] == k for r in rows) for k in ENDED_ON},
                    "mean_y_sigma_units": float(np.mean([r["y_raw"] / table["sigma_node"][r["node"]] for r in rows]))}
    return out


D3B_NOT_RUN_REASONS = ("gate_not_passed", "stopped", "not_started")


def analyse(d3a: dict, d3b: dict | None = None, d3b_not_run: str | None = None) -> dict:
    """Every pre-declared contrast. ``d3a`` and ``d3b`` must already be validated tables."""
    validate_table(d3a, "D.3a")
    ys = outcome_matrix(d3a)
    report = {"schema": REPORT_SCHEMA, "predeclaration_sha256": d3a["predeclaration_sha256"],
              "repetitions": d3a["repetitions"], "nodes": list(NODES), "instance_seeds": list(INSTANCE_SEEDS),
              "W": W, "llm_call_cap": LLM_CALL_CAP, "outcome_units": "sigma_node",
              "families": {"D.3a": _family("D.3a", CONTRASTS_D3A, ys)}, "usage": {"D.3a": _usage(d3a)}}
    if d3b is None:
        if d3b_not_run not in D3B_NOT_RUN_REASONS:
            raise D3InputError(f"without a D.3b table, state why: one of {D3B_NOT_RUN_REASONS}")
        report["families"]["D.3b"] = {"family": "D.3b", "status": "not_run", "reason": d3b_not_run,
                                      "contrasts": [f"{a} - {b}" for a, b in CONTRASTS_D3B]}
        return report
    if d3b_not_run is not None:
        raise D3InputError("a D.3b table and a not-run reason are mutually exclusive")
    validate_table(d3b, "D.3b")
    check_pair(d3a, d3b)
    ys = {**ys, **outcome_matrix(d3b)}
    pairs = CONTRASTS_D3B + ((CONTRAST_A6,) if "A6" in d3b["arms"] else ())
    report["families"]["D.3b"] = _family("D.3b", pairs, ys)
    report["families"]["D.3b"]["a6_entered"] = "A6" in d3b["arms"]
    report["usage"]["D.3b"] = _usage(d3b)
    return report


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
    a.add_argument("--predeclaration", required=True)
    a.add_argument("--out", required=True)
    sub.add_parser("namespaces")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "namespaces":
            print(json.dumps(check_namespaces(), indent=1, sort_keys=True))
            return 0
        out = Path(args.out)
        if out.exists():
            raise D3InputError(f"{out} exists; an analysis output is never overwritten")
        d3a = load_table(args.d3a, "D.3a")
        d3b = load_table(args.d3b, "D.3b") if args.d3b else None
        predecl = Path(args.predeclaration)
        if _sha256(predecl) != d3a["predeclaration_sha256"]:
            raise D3InputError("the pre-declaration file's sha256 differs from the tables' header")
        verify_sigma_against_noise_source(d3a["sigma_node"])
        report = analyse(d3a, d3b, args.d3b_not_run)
        report["inputs"] = {"d3a_sha256": _sha256(Path(args.d3a)),
                            "d3b_sha256": _sha256(Path(args.d3b)) if args.d3b else None,
                            "predeclaration": str(predecl), "analysis_sha256": _sha256(Path(__file__))}
        out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    except D3InputError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
