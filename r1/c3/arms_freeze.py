"""T0 arms freeze: A3 training, PRE-SELECT, dev calibration, fold A3s, the FEAT-ONE identity check and the arms-frozen
record (sweep-2 analysis preregistration §3, §4 steps 3-4, PRE-POOL, PRE-JOINT A, PRE-SELECT A, PRE-DUP A,
PRE-SECONDARY A). ENGINEERING_ONLY; AI-assisted (Claude).

What this module reads: table rows (``proposals.jsonl``, features only) and the **receipted train/dev label blocks**
(``release.traindev_labels``). It never opens an evaluation block or a test label: a label row of a P3 test instance,
a row carrying an evaluation field or evaluation seeds, a table row carrying a label or evaluation value, and an input
path named like a raw, test or evaluation block are refused (``ArmsFreezeError``).

* **Training rows** (``training_rows``): built exactly as ``gate_input_builder._prepare`` builds its rows, using the
  builder's own validation (``_instance``, ``_label_ok``, ``_seeds``) and ``labels.soft_label``: a no-op gets the inert
  soft label; a within-campaign duplicate gets no label (and must have no label row); an ``audit`` label gets
  ``soft_label(delta_label, None, sigma_node, sigma_mode="pooled_node", k_label)``; a ``divergent`` label gets no
  belief bin. Every non-inert, non-duplicate train/dev proposal needs its label row (complete population). Weights
  are 1 (the evidence population is complete). Only P3 train and dev instances give training rows.
* **Base rates** (``base_rates``): per node, ``metrics.base_rate`` of the soft labels of that node's own P3 train label
  block of the gate source (sweep 2 for T0, G.5 for T1), PRE-SELECT A.
* **PRE-SELECT A** (``preselect_score``, ``choose``): the mean over nodes, each weighted equally, of the dev RPS skill
  against that node's base rate, on the PRE-DUP primary dev population (``gate_input_builder.primary_dev_population``),
  label block only (labelled rows: no-ops and audit labels). Ties to 1e-9: sweep-2-only, then the smaller base.
  A node with no scored dev row, or whose base-rate RPS is 0, is left out of the mean for every candidate and reported.
* **A3 PRE-POOL** (``freeze_a3``): ``arms.LGBMPrior`` with its fixed defaults (ARMS-HP's recommended option) trained on
  the train rows of the gate sources (``sweep2_only``) or of sweep 1 plus the gate sources (``pooled``), selected by
  PRE-SELECT on **uncalibrated** predictions, then calibrated on the same dev population (§4 step 3's order).
  ARMS-TWIN (required switch ``twin_weight``): ``"mode_group"`` groups pooled train rows by (instance, memory mode,
  incumbent hash, candidate hash), the way twin campaigns pair (R1-MAIN-PROPOSER (e)(3)); a group spanning two
  sources is weighted to the total one source contributes alone (``twin_weighted``); ``"none"`` keeps weight 1.
* **Calibration** (ARMS-CAL, required switch ``calibration``): ``"temperature"`` fits one temperature on the
  non-inert conditional bins of the labelled non-inert dev rows (``metrics.fit_temperature``, the family of A5's
  temperature) and applies it to every non-no-op prediction; ``"none"`` leaves predictions as fitted.
* **Predictions**: proposal id -> 12 bins for every proposal of the gate sources' tables (test proposals included,
  features only), checked with ``gate_input_builder._rule_layer``.
* **Fold A3s** (``fold_plan``, ``freeze_a3(..., held_out=...)``): leave-one-node-out per node of the primary T0 set,
  leave-one-suite-out per suite of the frozen T1 set; each trained without the held-out nodes, selected and calibrated
  on the fold's dev (the remaining nodes), predicting the held-out nodes' proposals.
* **FEAT-ONE identity check** (``identity_compare``, ``identity_check``): between a sealed table and the v3 arms table
  re-derived from the same ledgers: the same (node, proposal_id) keys, byte-identical ``configs.json``, and no field
  other than ``features.budget_frac_left`` differing (NaN-aware). ``require_feat_one`` additionally requires the pinned
  v3 table (``SWEEP1_V3_PROPOSALS_SHA256``), at least one differing record and two distinct tables, so a table
  compared with itself cannot pass.
* **Arms-frozen record** (``render_record``, ``check_record``): a Markdown file under ``docs/r1/`` (the form
  ``release.row_text`` cites) with one fenced JSON block; the strict checker covers every item of §4 step 4.
* **Post-freeze reads fields** (post-freeze reads amendment A§8 unit 2, A§9; AI-assisted, Claude, subagent,
  23 Nov 2026): the record also carries ``amendments`` (the signed amendment's path, sha256 and PLAN row
  R1-POSTFREEZE-READS, looked up in PLAN §10 as the ``decisions`` rows are) and ``rule_arms`` (A0's rule id; A1's and
  A2's per-node vectors for the eight T0 nodes and the frozen T1 nodes, written by the constants fitter
  ``r1/c3/arms_constants.py``, with its path, sha256, code commit, the constants file's pin, the receipts it read and
  the fit population; the D.3 constants file's pin or null). ``postfreeze_fields`` (CLI ``postfreeze-fields``) writes
  both fields from the constants file. ``check_record`` checks their structure always; with ``constants_root`` it
  re-hashes the constants file (and the D.3 constants file) and requires the record's vectors to equal them bitwise
  and the fit's receipts and tables to be the record's ``label_tables``; with ``verify_committed`` it re-hashes the
  amendment as a committed file and requires its final block to be frozen and signed (``signed_utc <= frozen_utc``),
  to name R1-POSTFREEZE-READS and the preregistration, and to bind the committed copy of this file and the fitter
  (A§13), and checks the fitter's sha256 at its code commit. These two are keyword options of the Python API (the
  existing tests' fixture carries no files); the CLI ``check`` and ``render`` always run both and refuse a record
  without them (``require_file_checks``), so they never report a pass that skipped either. ``arms`` is unchanged: A0
  and A1 are not arms of the record (they have nothing to train), so ``required_arms`` does not list them.

Nothing here trains on real data by itself: the CLI (``python -m r1.c3.arms_freeze ...``) is run by the cluster agent
under the runbook ``docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md``.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np

from r1.c3 import gate as G
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split
from r1.c3.arms import LGBMPrior, is_duplicate, is_noop
from r1.c3.features import FEATURES
from r1.c3.labels import INERT, N_BINS, soft_label
from r1.c3.train import metrics as M

RECORD_SCHEMA = "r1_c3_arms_frozen/v1"
PRED_SCHEMA = "r1_c3_arm_predictions/v1"
IDENTITY_SCHEMA = "r1_c3_feat_one_identity/v1"
PREREG_PATH = "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md"
PREREG_SHA256 = "aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5"
NOISE_PATH = "results/r1/noise/D28_REPAIR_20261027/summary.json"     # sweep2/s2_c2_lib.py NOISE_PATH / NOISE_SHA
NOISE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
FEATURIZER = "c3_features/v3"
# FEAT-ONE: the v3 sweep-1 arms table, copied from r1/scripts/configs/trackp_sft.json tables.sweep1_v3 (the diagnosis
# replay at main and the W2.3 rebuild give these bytes); the sealed v2 table is SWEEP1_SEALED_PROPOSALS_SHA256.
SWEEP1_V3_PROPOSALS_SHA256 = "d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5"
SWEEP1_V3_CONFIGS_SHA256 = "b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df"
SWEEP1_SEALED_PROPOSALS_SHA256 = "b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4"  # B.2 table;
# copied from docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md (table/proposals.jsonl) on main
TWIN_WEIGHTS = ("mode_group", "none")
ALLOWED_DIFF = "features.budget_frac_left"
SOURCE_TIER = {"sweep1": "T0", "sweep2": "T0", "g5": "T1"}           # release.SOURCES
VARIANTS = {"sweep2_only": ("sweep2", "g5"), "pooled": ("sweep1", "sweep2", "g5")}
CALIBRATIONS = ("temperature", "none")
TIE = 1e-9
EVAL_KEYS = frozenset({"delta_evaluation", "se_evaluation", "k_evaluation", "divergent_seeds"})
TABLE_VALUE_KEYS = frozenset({"delta_true", "delta_audit", "delta_label", "se_label", "delta_evaluation", "soft",
                              "y_eval", "y_train", "label_kind"})
REFUSED_NAMES = frozenset({"label_block.jsonl", "evaluation_block.jsonl", "evaluation_block.all.jsonl",
                           "label_block.test.jsonl", "runs.jsonl"})
RECORD_PATH_RE = r"docs/r1/[A-Za-z0-9_./-]+\.md"                     # release.row_pattern's arms_path
_HEX = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")


class ArmsFreezeError(ValueError):
    """A refusal: nothing is trained, written or accepted."""


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_file(p) -> str:
    return _sha(Path(p).read_bytes())


# ============================================================================================== input refusals

def refuse_input_path(*paths) -> None:
    """A name check only: refuse a path named like a raw label block, an evaluation block, a test partition or a run
    log. The lock itself is ``release.open_partition`` (receipts, row texts, P3 membership); this is a second guard."""
    for p in paths:
        if p is None:
            continue
        p = Path(p)
        names = {p.name, p.resolve().name}
        if names & REFUSED_NAMES or "test" in (p.name, p.parent.name):
            raise ArmsFreezeError(f"{p}: raw, test or evaluation blocks are not arms inputs (PRE-STAGE A)")


def _label_seed_divergence(lab) -> bool:
    """A G.5 label row (``g5_assemble.group_label``, kinds ``audit`` and ``divergent``) records the **label** seeds
    where the candidate or the parent diverged as ``divergent_seeds``: a list of its own ``seeds``, which are label
    seeds (checked below). That is label-block content, not an evaluation field."""
    div, seeds = lab.get("divergent_seeds"), lab.get("seeds")
    return lab.get("label_kind") in ("audit", "divergent") and isinstance(div, list) and isinstance(seeds, list) \
        and all(isinstance(s, int) and not isinstance(s, bool) for s in div) and set(div) <= set(seeds)


def check_label_rows(labels, assign) -> None:
    """Released train/dev label rows only: no evaluation field, no evaluation seed, no P3 test instance. A G.5 label
    row's ``divergent_seeds`` is admitted only as a subset of its own label seeds (``_label_seed_divergence``)."""
    for lab in labels:
        pid = str(lab.get("proposal_id"))
        bad = EVAL_KEYS & set(lab)
        if bad == {"divergent_seeds"} and _label_seed_divergence(lab):
            bad = set()
        if bad:
            raise ArmsFreezeError(f"{pid}: a label row carries an evaluation field (§6)")
        seeds = set(lab.get("seeds") or ())
        if seeds & (set(B.T0_EVALUATION_SEEDS) | set(B.D3_EVALUATION_SEEDS)):
            raise ArmsFreezeError(f"{pid}: a label row names evaluation seeds (§6)")
        parts = pid.split(":")
        if len(parts) != 3 or parts[1] not in assign:
            raise ArmsFreezeError(f"{pid}: not source:instance:trial with an instance of the P3 split file")
        if assign[parts[1]]["split"] == "test":
            raise ArmsFreezeError(f"{pid}: a test label is not read before the test release row (§6)")


def check_table_rows(rows) -> None:
    for r in rows:
        bad = TABLE_VALUE_KEYS & set(r)
        if bad:
            raise ArmsFreezeError(f"{r.get('proposal_id')}: a table row carries label/evaluation values {sorted(bad)}")


def load_traindev(release_root, source: str, receipt_sha256: str):
    """The receipted train/dev label rows of ``source`` (``release.traindev_labels``, receipt pinned) and the receipt."""
    from r1.c3 import release
    if source not in SOURCE_TIER:
        raise ArmsFreezeError(f"unknown source {source}")
    if not _HEX.fullmatch(str(receipt_sha256 or "")):
        raise ArmsFreezeError(f"{source}: the receipt sha256 is required (pinned)")
    refuse_input_path(release_root)
    labels, receipt = release.traindev_labels(release_root, source, receipt_sha256=receipt_sha256)
    if receipt.get("stage") != "traindev" or receipt.get("source") != source or \
            receipt.get("counts", {}).get("evaluation_rows") != 0:
        raise ArmsFreezeError(f"{source}: not a train/dev receipt without evaluation rows")
    check_label_rows(labels, p3_split.assignment(p3_split.load()))
    return labels, receipt


def load_table_rows(table_dir):
    from r1.c3.dataset import load_table
    refuse_input_path(table_dir, Path(table_dir) / "proposals.jsonl")
    rows = load_table(Path(table_dir))
    check_table_rows(rows)
    return rows


# ============================================================================================== training rows

def training_rows(source: str, rows, labels, *, assign=None, t1: B.Tier1 | None = None) -> list[dict]:
    """Training rows of one source's P3 train and dev instances, constructed as ``gate_input_builder._prepare``."""
    if source not in SOURCE_TIER:
        raise ArmsFreezeError(f"unknown source {source}")
    assign = assign if assign is not None else p3_split.assignment(p3_split.load())
    check_label_rows(labels, assign)
    check_table_rows(rows)
    tier = SOURCE_TIER[source]
    label_seeds, _ = B._seeds(tier, t1)
    by_pid = {}
    for lab in labels:
        if lab["proposal_id"] in by_pid:
            raise ArmsFreezeError(f"{source}: duplicate label row {lab['proposal_id']}")
        by_pid[lab["proposal_id"]] = lab
    out, used, seen = [], set(), set()
    for row in sorted(rows, key=lambda r: r["proposal_id"]):
        pid = row["proposal_id"]
        if pid in seen:
            raise ArmsFreezeError(f"duplicate proposal id {pid}")
        seen.add(pid)
        if B._tier_of(row["node"]) != tier:
            raise ArmsFreezeError(f"{source}: row {pid} of node {row['node']} is not a {tier} node")
        missing = [c for c in FEATURES if c not in (row.get("features") or {})]
        if missing:
            raise ArmsFreezeError(f"{pid}: no featurizer value for {missing[:3]} (one featurizer, FEAT-ONE)")
        try:
            inst, split = B._instance(row, assign)
        except B.BuilderError as exc:
            raise ArmsFreezeError(str(exc)) from exc
        lab = by_pid.get(pid)
        if split == "test":
            if lab is not None:
                raise ArmsFreezeError(f"{pid}: a test label is not read before the test release row (§6)")
            continue
        r = {"proposal_id": pid, "source": source, "tier": tier, "node": row["node"], "instance": inst,
             "split": split, "memory_mode": row.get("memory_mode"), "features": row["features"],
             "noop": is_noop(row), "duplicate": is_duplicate(row), "sigma_node": row["sigma_node"],
             "key": B.repeat_key(row), "weight": 1.0, "label_kind": None, "soft": None}
        try:
            if is_noop(row):
                if lab is None:
                    raise ArmsFreezeError(f"{pid}: a no-op without its rule_noop label row")
                r["label_kind"] = B._label_ok(lab, row, label_seeds)
                r["soft"] = soft_label(None, None, row["sigma_node"], inert=True)
                used.add(pid)
            elif is_duplicate(row):
                if lab is not None:
                    raise ArmsFreezeError(f"{pid}: a within-campaign duplicate carries a label row")
            else:
                if lab is None:
                    raise ArmsFreezeError(f"{pid}: non-inert proposal without its label row (complete population)")
                kind = B._label_ok(lab, row, label_seeds)
                if kind == "audit":
                    tails = B._tail_options(lab, tier, t1)
                    r["soft"] = soft_label(lab["delta_label"], None, row["sigma_node"], sigma_mode="pooled_node",
                                           k_label=lab["soft_parameters"]["k_label"], **tails)
                    r.update(tails)
                r["label_kind"] = kind
                used.add(pid)
        except B.BuilderError as exc:
            raise ArmsFreezeError(str(exc)) from exc
        out.append(r)
    unused = set(by_pid) - used
    if unused:
        raise ArmsFreezeError(f"{source}: label rows for proposals outside the table: {sorted(unused)[:5]}")
    return out


def base_rates(rows) -> dict:
    """{node: base-rate 12-vector} from the labelled P3 train rows of the gate sources (PRE-SELECT A)."""
    out = {}
    for node in sorted({r["node"] for r in rows}):
        ys = [r["soft"] for r in rows if r["node"] == node and r["split"] == "train" and r["soft"] is not None
              and r["source"] in B.GATE_SOURCES]
        if ys:
            out[node] = M.base_rate(np.array(ys))
    return out


# ============================================================================================== PRE-SELECT A

def preselect_score(predict, dev_rows, bases) -> dict:
    """PRE-SELECT A on labelled dev rows: {score, per_node, left_out}. ``predict``: rows -> (n, 12) array."""
    per_node, left_out = {}, {}
    for node in sorted({r["node"] for r in dev_rows}):
        rows = [r for r in dev_rows if r["node"] == node and r["soft"] is not None]
        if not rows:
            left_out[node] = "no labelled dev row"
            continue
        if node not in bases:
            left_out[node] = "no train base rate"
            continue
        y = np.array([r["soft"] for r in rows])
        if M.mean_rps(np.broadcast_to(bases[node], y.shape), y) <= 0:
            left_out[node] = "base-rate RPS is 0"
            continue
        per_node[node] = float(M.rps_skill(predict(rows), y, bases[node]))
    if not per_node:
        raise ArmsFreezeError("PRE-SELECT: no node with a scored dev row")
    return {"score": float(np.mean([per_node[n] for n in sorted(per_node)])), "per_node": per_node,
            "left_out": left_out}


def choose(candidates: dict) -> str:
    """PRE-SELECT A's choice: the highest score; ties to 1e-9 go to sweep-2-only, then to the smaller base.
    ``candidates``: {name: {"score", "pool": "sweep2_only"|"pooled", "base_params": float (0 if none)}}."""
    if not candidates:
        raise ArmsFreezeError("no candidates")
    best = max(c["score"] for c in candidates.values())
    tied = [n for n, c in candidates.items() if best - c["score"] <= TIE]
    return min(tied, key=lambda n: (candidates[n]["pool"] != "sweep2_only", candidates[n].get("base_params", 0.0), n))


# ============================================================================================== calibration

def _cond_logits(P) -> np.ndarray:
    return np.log(np.clip(np.asarray(P, float)[:, 1:], 1e-12, None))


def fit_calibration(P_dev, y_dev, mode: str = "temperature") -> dict:
    """ARMS-CAL: one temperature on the non-inert conditional bins (labelled non-inert dev rows), or none."""
    if mode not in CALIBRATIONS:
        raise ArmsFreezeError(f"calibration must be one of {CALIBRATIONS}")
    if mode == "none":
        return {"mode": "none"}
    P_dev, y_dev = np.asarray(P_dev, float), np.asarray(y_dev, float)
    if len(P_dev) == 0:
        raise ArmsFreezeError("no labelled non-inert dev row to fit the temperature on")
    y = y_dev[:, 1:] / np.maximum(y_dev[:, 1:].sum(1, keepdims=True), 1e-12)
    return {"mode": "temperature", "temperature": M.fit_temperature(_cond_logits(P_dev), y),
            "fit_rows": int(len(P_dev)), "family": "metrics.fit_temperature on the 11 non-inert bins"}


def apply_calibration(P, rows, cal: dict) -> np.ndarray:
    P = np.array(P, float)
    if cal["mode"] == "none":
        return P
    T = float(cal["temperature"])
    if not (T > 0 and math.isfinite(T)):
        raise ArmsFreezeError("invalid temperature")
    out = P.copy()
    live = np.array([not is_noop(r) for r in rows], bool)
    if live.any():
        out[live, 1:] = M.apply_temperature(_cond_logits(P[live]), T)
        out[live, INERT] = 0.0
    return out


# ============================================================================================== A3 freeze

def _nodes_of(rows) -> set:
    return {r["node"] for r in rows}


def twin_weighted(rows) -> list[dict]:
    """ARMS-TWIN "mode_group": rows are grouped by (instance, memory mode, key), the way twin campaigns pair (same
    instance seed, same memory mode). A group spanning k > 1 sources gets the total weight T one source contributes
    alone (T = the largest per-source row count, 1 in practice since a key repeats within a campaign only as an
    unlabelled duplicate); each row of source s gets T / (k * n_s). Single-source groups keep their weights, so a
    key's total weight in the pooled variant equals its sweep-2-only total. Returns copies; inputs are not changed."""
    groups = {}
    for r in rows:
        groups.setdefault((r["instance"], r["memory_mode"], r["key"]), []).append(r)
    out = []
    for r in rows:
        g = groups[(r["instance"], r["memory_mode"], r["key"])]
        per_source = {}
        for x in g:
            per_source[x["source"]] = per_source.get(x["source"], 0) + 1
        k = len(per_source)
        w = r["weight"] if k == 1 else r["weight"] * max(per_source.values()) / (k * per_source[r["source"]])
        out.append({**r, "weight": w})
    return out


def freeze_a3(tables: dict, trows: dict, *, calibration: str, twin_weight: str, held_out=(), primary_dev=None,
              seed: int = 0) -> dict:
    """A3 under PRE-POOL / PRE-SELECT A / ARMS-CAL. ``tables``: {source: table rows}; ``trows``: {source: training rows}
    (``training_rows``). ``held_out``: nodes left out of training and selection (a fold); the predictions then cover
    the held-out nodes' gate-source proposals, otherwise every gate-source proposal. Returns the fitted model, the
    calibration, the selection record and the predictions."""
    if "sweep2" not in tables and "g5" not in tables:
        raise ArmsFreezeError("no gate source")
    if twin_weight not in TWIN_WEIGHTS:
        raise ArmsFreezeError(f"twin_weight must be one of {TWIN_WEIGHTS}")
    held = set(held_out)
    if primary_dev is None:
        try:
            primary_dev = B.primary_dev_population([B.Source(s, rows) for s, rows in sorted(tables.items())])
        except B.BuilderError as exc:
            raise ArmsFreezeError(str(exc)) from exc
    allrows = [r for s in sorted(trows) for r in trows[s] if r["node"] not in held]
    bases = base_rates(allrows)
    dev = [r for r in allrows if r["split"] == "dev" and r["source"] in B.GATE_SOURCES and r["soft"] is not None
           and r["proposal_id"] in primary_dev]
    fits, cands = {}, {}
    for variant, sources in VARIANTS.items():
        train = [r for r in allrows if r["split"] == "train" and r["source"] in sources and r["soft"] is not None]
        if not train:
            raise ArmsFreezeError(f"{variant}: no labelled training row")
        if twin_weight == "mode_group":
            train = twin_weighted(train)
        model = LGBMPrior(seed=seed).fit(train)
        sc = preselect_score(model.predict, dev, bases)
        fits[variant] = (model, train)
        cands[variant] = {"score": sc["score"], "pool": variant, "base_params": 0.0, "per_node": sc["per_node"],
                          "left_out": sc["left_out"], "n_train_rows": len(train),
                          "train_sources": sorted({r["source"] for r in train}),
                          "twin_rows_downweighted": sum(r["weight"] < 1.0 for r in train)}
    choice = choose(cands)
    model, train = fits[choice]
    live = [r for r in dev if not r["noop"] and r["label_kind"] == "audit"]
    cal = fit_calibration(model.predict(live) if live else np.zeros((0, N_BINS)),
                          np.array([r["soft"] for r in live]) if live else np.zeros((0, N_BINS)), calibration)
    targets = [r for s in sorted(tables) if s in B.GATE_SOURCES for r in tables[s]
               if (r["node"] in held if held else True)]
    if held and not targets:
        raise ArmsFreezeError(f"no gate-source proposal of the held-out nodes {sorted(held)}")
    P = apply_calibration(model.predict(targets), targets, cal)
    try:
        B._rule_layer(P, targets)
    except B.BuilderError as exc:
        raise ArmsFreezeError(f"predictions fail the builder's validation: {exc}") from exc
    preds = {r["proposal_id"]: [float(x) for x in p] for r, p in zip(targets, P)}
    selection = {"rule": "PRE-SELECT A (mean over nodes of dev RPS skill vs the node's own P3 train base rate; "
                         "PRE-DUP primary dev population; uncalibrated predictions; ties to 1e-9 -> sweep2_only)",
                 "choice": choice, "candidates": cands, "dev_rows_scored": len(dev),
                 "held_out": sorted(held), "trained_nodes": sorted(_nodes_of(allrows)), "twin_weight": twin_weight,
                 "calibration_rows": sorted(r["proposal_id"] for r in live)}
    return {"model": model, "calibration": cal, "selection": selection, "predictions": preds}


def fold_plan(t0_nodes, t1: B.Tier1 | None) -> dict:
    """{fold name: held-out nodes}: leave-one-node-out per primary T0 node; leave-one-suite-out per suite of the
    frozen T1 set (PRE-SECONDARY A, R1-FOLD-DECISIONS)."""
    plan = {f"lono:{n}": [n] for n in sorted(t0_nodes)}
    if t1 is not None:
        for suite in sorted(set(t1.suites.values())):
            plan[f"loso:{suite}"] = sorted(n for n, s in t1.suites.items() if s == suite)
    return plan


def write_arm(out_dir, name: str, result: dict, *, code_commit: str, role: str, inputs: dict,
              artefact_root=None) -> dict:
    """Write model, calibration, selection and predictions of one A3 arm; returns its record entry, with paths
    relative to ``artefact_root`` (default ``out_dir``'s parent)."""
    out_dir = Path(out_dir)
    root = Path(artefact_root) if artefact_root is not None else out_dir.parent
    out_dir.mkdir(parents=True, exist_ok=False)
    m = result["model"]
    files = {"checkpoint": ("model.txt", m.model.model_to_string().encode()),
             "calibration": ("calibration.json", _dump(result["calibration"])),
             "selection": ("selection.json", _dump(result["selection"])),
             "predictions": ("predictions.json", _dump({"schema": PRED_SCHEMA, "arm": name,
                                                        "predictions": result["predictions"]}))}
    entry = {"arm": name, "role": role, "code_commit": code_commit, "family": "A3 LightGBM (arms.LGBMPrior defaults)",
             "params": {"rounds": m.rounds, "lgbm": m.params, "columns": m.cols},
             "calibration_mode": result["calibration"]["mode"], "inputs": inputs, "toolchain": toolchain(),
             "twin_weight": result["selection"]["twin_weight"],
             "preselect": {"choice": result["selection"]["choice"],
                           "dev_values": {k: v["score"] for k, v in result["selection"]["candidates"].items()}},
             "n_predictions": len(result["predictions"])}
    for key, (fname, data) in files.items():
        (out_dir / fname).write_bytes(data)
        entry[key] = {"path": (out_dir / fname).resolve().relative_to(root.resolve()).as_posix(), "sha256": _sha(data)}
    (out_dir / "arm_entry.json").write_bytes(_dump(entry))
    return entry


def toolchain() -> dict:
    """The versions the model bytes depend on (m3)."""
    import platform
    import lightgbm
    return {"python": platform.python_version(), "numpy": np.__version__, "lightgbm": lightgbm.__version__}


def _dump(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, allow_nan=False) + "\n").encode()


# ============================================================================================== FEAT-ONE identity

def _same(a, b) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return True
        return a == b
    return type(a) is type(b) and a == b


def _diff_paths(a: dict, b: dict, prefix: str = "") -> list[str]:
    out = []
    for k in sorted(set(a) | set(b)):
        p = f"{prefix}{k}"
        if k not in a or k not in b:
            out.append(p)
        elif isinstance(a[k], dict) and isinstance(b[k], dict):
            out += _diff_paths(a[k], b[k], p + ".")
        elif not _same(a[k], b[k]):
            out.append(p)
    return out


def identity_compare(sealed_rows, arms_rows, *, sealed_configs: bytes, arms_configs: bytes) -> dict:
    """FEAT-ONE: the arms table differs from the sealed table only in ``features.budget_frac_left`` (NaN-aware), with
    the same (node, proposal_id) keys and byte-identical configs. Reports ids and field paths only, never values."""
    def keyed(rows, what):
        out = {}
        for r in rows:
            k = (r["node"], r["proposal_id"])
            if k in out:
                raise ArmsFreezeError(f"{what}: duplicate key {k}")
            out[k] = r
        return out
    s, a = keyed(sealed_rows, "sealed table"), keyed(arms_rows, "arms table")
    keys_equal = set(s) == set(a)
    configs_equal = sealed_configs == arms_configs
    allowed, other = [], []
    for k in sorted(set(s) & set(a)):
        for path in _diff_paths(s[k], a[k]):
            (allowed if path == ALLOWED_DIFF else other).append((k[1], path))
    return {"schema": IDENTITY_SCHEMA, "rule": "FEAT-ONE: same (node, proposal_id) keys, byte-identical configs.json, "
                                               "only features.budget_frac_left may differ (NaN-aware)",
            "pass": bool(keys_equal and configs_equal and not other),
            "n_sealed": len(s), "n_arms": len(a), "keys_equal": keys_equal,
            "keys_only_sealed": len(set(s) - set(a)), "keys_only_arms": len(set(a) - set(s)),
            "configs_equal": configs_equal, "configs_sha256": {"sealed": _sha(sealed_configs),
                                                               "arms": _sha(arms_configs)},
            "n_budget_frac_left_differ": len(allowed), "first_budget_frac_left_ids": [p for p, _ in allowed[:5]],
            "n_other_differences": len(other), "other_differences": [list(x) for x in other[:20]]}


def require_feat_one(identity: dict, *, sealed_sha256: str, arms_sha256: str) -> None:
    """FEAT-ONE as enforced (M1): a passing identity result of this schema and featurizer, binding the sealed table the
    receipt released to the pinned v3 arms table, with at least one ``budget_frac_left`` difference (two distinct
    tables: a table compared with itself is refused)."""
    if not isinstance(identity, dict) or identity.get("schema") != IDENTITY_SCHEMA or \
            identity.get("featurizer") != FEATURIZER or identity.get("pass") is not True:
        raise ArmsFreezeError(f"FEAT-ONE: not a passing {IDENTITY_SCHEMA} result for {FEATURIZER}")
    if arms_sha256 != SWEEP1_V3_PROPOSALS_SHA256 or identity.get("arms_proposals_sha256") != arms_sha256:
        raise ArmsFreezeError("FEAT-ONE: the sweep-1 arms table is not the pinned v3 table "
                              f"{SWEEP1_V3_PROPOSALS_SHA256[:12]}…")
    if sealed_sha256 != SWEEP1_SEALED_PROPOSALS_SHA256:
        raise ArmsFreezeError("FEAT-ONE: the sweep-1 table the receipt released is not the sealed B.2 table "
                              f"{SWEEP1_SEALED_PROPOSALS_SHA256[:12]}…")
    if identity.get("sealed_proposals_sha256") != sealed_sha256 or sealed_sha256 == arms_sha256:
        raise ArmsFreezeError("FEAT-ONE: the identity result does not bind the released sealed table to a distinct "
                              "arms table")
    if (identity.get("configs_sha256") or {}).get("arms") != SWEEP1_V3_CONFIGS_SHA256:
        raise ArmsFreezeError("FEAT-ONE: the arms table's configs.json is not the pinned one")
    n = identity.get("n_budget_frac_left_differ")
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ArmsFreezeError("FEAT-ONE: no budget_frac_left difference (a table compared with itself?)")


def identity_check(sealed_dir, arms_dir) -> dict:
    sealed_dir, arms_dir = Path(sealed_dir), Path(arms_dir)
    out = identity_compare(load_table_rows(sealed_dir), load_table_rows(arms_dir),
                           sealed_configs=(sealed_dir / "configs.json").read_bytes(),
                           arms_configs=(arms_dir / "configs.json").read_bytes())
    out.update(sealed_proposals_sha256=_sha_file(sealed_dir / "proposals.jsonl"),
               arms_proposals_sha256=_sha_file(arms_dir / "proposals.jsonl"), featurizer=FEATURIZER)
    return out


# ============================================================================================== arms-frozen record

REQUIRED_TOP = ("schema", "preregistration", "gate", "gate_input_builder", "split_file", "noise_source",
                "g1b_summaries", "t0_nodes", "t1", "label_tables", "feature_tables", "arms", "fold_arms",
                "secondary_arms", "decisions", "disclosures", "a3_settings",
                "amendments", "rule_arms")                       # post-freeze reads amendment A§9
REQUIRED_DECISIONS = ("FEAT-ONE", "ARMS-CAL", "ARMS-HP", "ARMS-LEFTOUT", "ARMS-WDBC", "ARMS-TWIN", "ARMS-T1FEAT",
                      "ARMS-A5CKPT", "ARMS-A5FOLD", "ARMS-SECONDARY")
T1_KEYS = {"suites", "modes", "d3_k6", "instances"}
TOOLCHAIN_KEYS = {"python", "numpy", "lightgbm"}
REQUIRED_DISCLOSURES = ("trackp_sft_v1", "exam_set")
# D7 (A5's T1 input): R1-T1-FEAT-DECISIONS records D7 itself, R1-T1-A5-DECISIONS its options (D7-FORM A and the rest)
D7_ROWS = ("R1-T1-FEAT-DECISIONS", "R1-T1-A5-DECISIONS")
D7_FORM_ROW = "R1-T1-A5-DECISIONS"
ARM_FIELDS = ("role", "code_commit", "checkpoint", "calibration", "predictions", "preselect")
# Post-freeze reads amendment (A§8 unit 2, A§9). The amendment's own sha256 cannot be pinned here (its final block
# A§13 pins this file's), so the record carries it and ``verify_committed`` re-hashes the committed file.
REQUIRED_AMENDMENTS = ("R1-POSTFREEZE-READS",)
AMENDMENT_KEYS = {"path", "sha256", "plan_row"}
AMENDMENT_PATH_RE = r"docs/r1/authorizations/[A-Za-z0-9_./-]+\.md"   # a path naming a DRAFT is refused too
ARMS_FREEZE_PATH = "r1/c3/arms_freeze.py"
UTC_RE = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z"     # release.prereg_frozen's frozen_utc form
A0_RULE = "r1.c3.offline_eval.rho"                      # execute every proposal; keep iff delta_hat > 0
RULE_ARM_KEYS = {"A0", "A1", "A2", "d3_constants"}
RULE_FIT_KEYS = ("vectors", "fitter", "constants", "receipts", "fit_population")


def render_record(record: dict) -> str:
    """The arms-frozen record as Markdown: a short header and one fenced JSON block (sorted keys)."""
    body = json.dumps(record, indent=1, sort_keys=True, allow_nan=False)
    return ("# C3 arms-frozen record (sweep-2 analysis preregistration §4 step 4)\n\n"
            "Written by `r1/c3/arms_freeze.py` (AI-assisted, Claude). Nothing in it changes after it is committed; the "
            "test release row cites its sha256. The JSON block below is the record; `python -m r1.c3.arms_freeze "
            "check --record <this file>` checks it.\n\n```json\n" + body + "\n```\n")


def parse_record(text: str) -> dict:
    blocks = re.findall(r"^```json\n(.*?)\n```\s*$", text, flags=re.S | re.M)
    if len(blocks) != 1 or not text.rstrip().endswith("```"):
        raise ArmsFreezeError("the record needs exactly one fenced json block, at the end of the file")
    try:
        return json.loads(blocks[0])
    except ValueError as exc:
        raise ArmsFreezeError("the record's json block does not parse") from exc


def _prereg_block(repo: Path) -> dict:
    from r1.c3 import release

    data = (repo / PREREG_PATH).read_bytes()
    if _sha(data) != PREREG_SHA256:
        raise ArmsFreezeError("the preregistration is not the frozen one")
    block = dict(line.split(": ", 1) for line in release._final_block(data.decode()))
    if _sha_file(repo / release.BUILDER_PATH) != block["gate_input_builder_sha256"]:
        try:
            active = release.prereg_frozen(root=repo)
        except release.ReleaseStop as exc:
            raise ArmsFreezeError(str(exc)) from exc
        block["gate_input_builder_sha256"] = active["builder_sha256"]
        block["g5_tail_amendment_sha256"] = active["sha256"]
    return block


def _pin(obj, what: str, path: str | None = None, sha: str | None = None) -> None:
    if not isinstance(obj, dict) or not isinstance(obj.get("path"), str) or not _HEX.fullmatch(str(obj.get("sha256"))):
        raise ArmsFreezeError(f"{what}: needs {{path, sha256}}")
    if path is not None and obj["path"] != path:
        raise ArmsFreezeError(f"{what}: path must be {path}")
    if sha is not None and obj["sha256"] != sha:
        raise ArmsFreezeError(f"{what}: sha256 must be {sha}")


def tree_sha256(directory) -> str:
    """The checkpoint-tree sha256 of P.4's ``arm_pin`` (``p4_phase1.arm_pin``): sha256 over the sorted files' lines
    ``<relative posix path>\\0<file sha256>\\n``."""
    d = Path(directory)
    files = sorted(p for p in d.rglob("*") if p.is_file())
    return _sha("".join(f"{p.relative_to(d).as_posix()}\0{_sha_file(p)}\n" for p in files).encode())


def a5_pin_binding(entry: dict, root) -> dict:
    """An A5-family entry is bound to one run of its P.4 arm pin: the pin file's ``grid`` holds a run whose
    ``best_tree_sha256`` is the entry's checkpoint and whose ``temperature_sha256`` is the entry's calibration."""
    pin = json.loads((Path(root) / entry["p4_arm_pin"]["path"]).read_text())
    if not str(pin.get("schema", "")).startswith("trackp_p4_arm_pin/"):
        raise ArmsFreezeError("p4_arm_pin is not a P.4 arm pin file")
    runs = [r for r in pin.get("grid") or [] if r.get("best_tree_sha256") == entry["checkpoint"]["sha256"]
            and r.get("temperature_sha256") == entry["calibration"]["sha256"]]
    if len(runs) != 1:
        raise ArmsFreezeError("the A5 checkpoint and temperature are not exactly one run of its P.4 arm pin")
    return runs[0]


def required_arms(record: dict) -> list[str]:
    """Every arm the record must freeze: A3 and A5 (primary), the declared secondary arms, and the fold arms."""
    t1 = record.get("t1") or {}
    tier1 = B.Tier1(suites=t1.get("suites") or {}, modes=tuple(t1.get("modes") or ()), d3_k6=bool(t1.get("d3_k6")))
    folds = fold_plan(record.get("t0_nodes") or [], tier1 if tier1.suites else None)
    names = ["A3", "A5", *list(record.get("secondary_arms") or [])]
    for arm, status in sorted((record.get("fold_arms") or {}).items()):
        if status == "built":
            names += [f"{arm}@{f}" for f in folds]
    return names


def _check_t1(t1) -> None:
    """PRE-T1 A: the frozen T1 node set and its instances (each in the split file, of a frozen node; every frozen node
    with at least one train and one dev instance)."""
    if not isinstance(t1, dict) or set(t1) != T1_KEYS or not isinstance(t1["suites"], dict) \
            or not isinstance(t1["d3_k6"], bool) or not isinstance(t1["modes"], list) \
            or not isinstance(t1["instances"], list):
        raise ArmsFreezeError(f"t1 must be {sorted(T1_KEYS)} (PRE-T1, G5-MEM, R1-BX-D3)")
    for node, suite in t1["suites"].items():
        if node not in p3_split.T1_NODES or suite not in G.SUITES:
            raise ArmsFreezeError(f"T1 node {node} / suite {suite} not in the split file / gate.SUITES")
    if t1["suites"] and not t1["modes"]:
        raise ArmsFreezeError("a non-empty T1 set needs its declared mode(s)")
    assign = p3_split.assignment(p3_split.load())
    if len(set(t1["instances"])) != len(t1["instances"]):
        raise ArmsFreezeError("t1.instances repeats an instance")
    for inst in t1["instances"]:
        if inst not in assign or assign[inst]["node"] not in t1["suites"]:
            raise ArmsFreezeError(f"t1.instances: {inst} is not a split-file instance of a frozen T1 node")
    for node in t1["suites"]:
        splits = {assign[i]["split"] for i in t1["instances"] if assign[i]["node"] == node}
        if not {"train", "dev"} <= splits:
            raise ArmsFreezeError(f"t1: {node} needs a train and a dev instance (PRE-T1 A)")


def _check_receipts(lt: dict, release_roots: dict) -> int:
    """Re-hash each named source's traindev receipt and partition against ``label_tables`` (hashes only)."""
    n = 0
    for src, root in sorted(release_roots.items()):
        if src not in lt:
            raise ArmsFreezeError(f"--release-root names {src}, which the record does not")
        d = Path(root) / src / "traindev"
        raw = (d / "RECEIPT.json").read_bytes()
        rec = json.loads(raw)
        part = "label_block.traindev.jsonl"
        if _sha(raw) != lt[src]["receipt_sha256"] or rec.get("source") != src or rec.get("stage") != "traindev" or \
                (rec.get("inputs") or {}).get("label_block_sha256") != lt[src]["label_block_sha256"] or \
                (rec.get("inputs") or {}).get("proposals_sha256") != lt[src]["proposals_sha256"] or \
                (rec.get("outputs") or {}).get(part) != lt[src]["traindev_partition_sha256"] or \
                _sha_file(d / part) != lt[src]["traindev_partition_sha256"]:
            raise ArmsFreezeError(f"label_tables.{src} does not match the receipt and partition under {root}")
        n += 1
    return n


# ---------------------------------------------------------------------- post-freeze reads fields (amendment A§9)

def _relative(path, what: str) -> None:
    """A path relative to a root: not absolute, no '..' and no backslash (so ``root / path`` stays under root)."""
    p = str(path)
    if not p or p.startswith("/") or "\\" in p or ".." in p.split("/"):
        raise ArmsFreezeError(f"{what}: the path must be relative to its root, without '..'")


def _check_amendments(amendments, rows: set) -> None:
    """``amendments``: exactly one entry {path, sha256, plan_row} per required amendment row; each row an author row
    of PLAN §10 (the lookup of the ``decisions`` rows)."""
    if not isinstance(amendments, list) or len(amendments) != len(REQUIRED_AMENDMENTS):
        raise ArmsFreezeError(f"amendments must list exactly {list(REQUIRED_AMENDMENTS)} (post-freeze reads A§9)")
    cited = []
    for e in amendments:
        if not isinstance(e, dict) or set(e) != AMENDMENT_KEYS:
            raise ArmsFreezeError(f"an amendments entry must be {sorted(AMENDMENT_KEYS)}")
        _pin(e, "amendments entry")
        if not re.fullmatch(AMENDMENT_PATH_RE, e["path"]) or "draft" in e["path"].lower():
            raise ArmsFreezeError(f"amendments: the path must match {AMENDMENT_PATH_RE} and not name a draft")
        row = e["plan_row"]
        if not isinstance(row, str) or not re.fullmatch(r"R1-[A-Z0-9-]+", row) or row not in rows:
            raise ArmsFreezeError(f"amendments must cite an author row of PLAN §10 (got {row!r})")
        cited.append(row)
    if sorted(cited) != sorted(REQUIRED_AMENDMENTS):
        raise ArmsFreezeError(f"amendments must cite {list(REQUIRED_AMENDMENTS)}, each once (got {cited})")


def _check_rule_arms(ra, t1: dict) -> dict:
    """Structure of ``rule_arms``: A0 = {rule: A0_RULE, constants: null}; A1 and A2 each with per-node vectors for
    exactly the eight T0 nodes and the frozen T1 nodes (12 finite non-negative bins summing to 1; A2's bin 0 is 0),
    the fitter {path, sha256, code_commit}, the constants file {path, sha256}, the receipts of the gate sources and the
    fit population, the same for both (one fit); A1 with "no rule layer; no verify offline"; ``d3_constants`` null or
    {path, sha256}. Returns the shared provenance."""
    from r1.c3 import arms_constants as AC
    if not isinstance(ra, dict) or set(ra) != RULE_ARM_KEYS:
        raise ArmsFreezeError(f"rule_arms must be {sorted(RULE_ARM_KEYS)} (post-freeze reads A§9)")
    if ra["A0"] != {"rule": A0_RULE, "constants": None}:
        raise ArmsFreezeError(f"rule_arms.A0 must be {{rule: {A0_RULE}, constants: null}}")
    nodes = set(B.ALL_T0) | set(t1["suites"])
    sources = {"sweep2"} | ({"g5"} if t1["suites"] else set())
    prov = None
    for arm in ("A1", "A2"):
        e = ra[arm]
        keys = set(RULE_FIT_KEYS) | ({"offline"} if arm == "A1" else set())
        if not isinstance(e, dict) or set(e) != keys:
            raise ArmsFreezeError(f"rule_arms.{arm} must be {sorted(keys)}")
        if arm == "A1" and e["offline"] != AC.A1_OFFLINE:
            raise ArmsFreezeError(f"rule_arms.A1.offline must read {AC.A1_OFFLINE!r}")
        vec = e["vectors"]
        if not isinstance(vec, dict) or set(vec) != nodes:
            raise ArmsFreezeError(f"rule_arms.{arm}.vectors must cover exactly the eight T0 nodes and the frozen T1 "
                                  "nodes")
        for n in sorted(vec):
            AC.check_vector(vec[n], f"rule_arms.{arm}.vectors.{n}", a2=arm == "A2")
        f = e["fitter"]
        if not isinstance(f, dict) or set(f) != {"path", "sha256", "code_commit"} or \
                not _COMMIT.fullmatch(str(f.get("code_commit"))):
            raise ArmsFreezeError(f"rule_arms.{arm}.fitter must be {{path, sha256, code_commit (40 hex)}}")
        _pin(f, f"rule_arms.{arm}.fitter", AC.FITTER_PATH)
        c = e["constants"]
        if not isinstance(c, dict) or set(c) != {"path", "sha256"}:
            raise ArmsFreezeError(f"rule_arms.{arm}.constants must be {{path, sha256}}")
        _pin(c, f"rule_arms.{arm}.constants")
        _relative(c["path"], f"rule_arms.{arm}.constants")
        rc = e["receipts"]
        if not isinstance(rc, dict) or set(rc) != sources or not all(_HEX.fullmatch(str(v)) for v in rc.values()):
            raise ArmsFreezeError(f"rule_arms.{arm}.receipts must give the receipt sha256 of {sorted(sources)}")
        if e["fit_population"] != AC.FIT_POPULATION:
            raise ArmsFreezeError(f"rule_arms.{arm}.fit_population must read {AC.FIT_POPULATION!r}")
        p = {k: e[k] for k in RULE_FIT_KEYS if k != "vectors"}
        if prov is not None and p != prov:
            raise ArmsFreezeError("rule_arms.A1 and A2 must come from one fit (fitter, constants, receipts, population)")
        prov = p
    d3 = ra["d3_constants"]
    if d3 is not None:
        if not isinstance(d3, dict) or set(d3) != {"path", "sha256"}:
            raise ArmsFreezeError("rule_arms.d3_constants must be null or {path, sha256}")
        _pin(d3, "rule_arms.d3_constants")
        _relative(d3["path"], "rule_arms.d3_constants")
    return prov


def _read_pinned(root, pin: dict, what: str) -> bytes:
    f = Path(root) / pin["path"]
    if not f.is_file():
        raise ArmsFreezeError(f"{what}: {f} is missing")
    data = f.read_bytes()
    if _sha(data) != pin["sha256"]:
        raise ArmsFreezeError(f"{what}: {f} differs from its sha256")
    return data


def _check_constants_files(ra: dict, root, lt: dict, t1: dict, builder_sha256: str) -> int:
    """Under ``root``: the constants file re-hashed and parsed; the record's A1 and A2 vectors equal to it bitwise; its
    fitter, builder pin (the record's ``gate_input_builder``), T1 setting, receipts, partitions and tables equal to the
    record's (``label_tables``); each frozen T1 node's
    dev instances equal to ``t1.instances``'; and, if pinned, the D.3 constants file re-hashed with the seven D.3
    nodes' A1 and A2 vectors equal to the record's bitwise (R1-D3-MIN; D.3 draft §10). Returns the files read."""
    from r1.c3 import arms_constants as AC
    c = AC.parse(_read_pinned(root, ra["A1"]["constants"], "rule_arms constants file"))
    for arm in ("A1", "A2"):
        got, want = c["vectors"][arm], ra[arm]["vectors"]
        diff = sorted(n for n in set(got) | set(want)
                      if n not in got or n not in want or not AC.same_bits(got[n], want[n]))
        if diff:
            raise ArmsFreezeError(f"rule_arms.{arm}: the vectors differ from the constants file for {diff[:4]}")
    if c["fitter"] != ra["A1"]["fitter"]:
        raise ArmsFreezeError("rule_arms: the fitter differs from the constants file's")
    if c["gate_input_builder"]["sha256"] != builder_sha256:
        raise ArmsFreezeError("rule_arms: the constants file's gate_input_builder is not the record's (fit_a2's code)")
    if c["t1"] != {k: t1[k] for k in ("suites", "modes", "d3_k6")}:
        raise ArmsFreezeError("rule_arms: the constants file's T1 setting is not the record's t1")
    if {s: m["receipt_sha256"] for s, m in c["sources"].items()} != ra["A1"]["receipts"]:
        raise ArmsFreezeError("rule_arms: the receipts differ from the constants file's")
    for src, m in sorted(c["sources"].items()):
        L = lt.get(src) or {}
        if any(L.get(k) != m[k] for k in ("receipt_sha256", "traindev_partition_sha256", "label_block_sha256",
                                          "proposals_sha256")):
            raise ArmsFreezeError(f"rule_arms: the constants were fitted on {src} partitions or tables other than "
                                  f"label_tables.{src}")
    assign = p3_split.assignment(p3_split.load())
    for node in sorted(t1["suites"]):
        want = sorted(i for i in t1["instances"] if assign[i]["node"] == node and assign[i]["split"] == "dev")
        if c["nodes"][node]["dev_instances"] != want:
            raise ArmsFreezeError(f"rule_arms: {node}'s dev instances in the constants file differ from t1.instances")
    n = 1
    if ra["d3_constants"] is not None:
        _check_d3_vectors(ra, _read_pinned(root, ra["d3_constants"], "rule_arms.d3_constants"))
        n += 1
    return n


def _check_d3_vectors(ra: dict, data: bytes) -> None:
    """The seven D.3 nodes' A1 and A2 vectors of the D.3 constants file (a document of the constants schema family:
    per node ``A1`` and ``A2``) equal the record's bitwise (R1-D3-MIN; D.3 draft §5.0, §10)."""
    from r1.c3 import arms_constants as AC
    dv = AC.vectors_of(AC.load_json(data, "D.3 constants file"), "D.3 constants file")
    missing = [x for x in AC.D3_NODES if x not in dv["A1"] or x not in dv["A2"]]
    if missing:
        raise ArmsFreezeError(f"rule_arms.d3_constants: the D.3 constants file lacks the D.3 nodes {missing}")
    for arm in ("A1", "A2"):
        diff = [x for x in AC.D3_NODES if not AC.same_bits(dv[arm][x], ra[arm]["vectors"][x])]
        if diff:
            raise ArmsFreezeError(f"rule_arms.{arm}: the D.3 nodes {diff} differ from the D.3 constants file "
                                  "(R1-D3-MIN; D.3 draft §10)")


def _amendment_block(data: bytes, path: str) -> dict:
    from r1.c3.release import ReleaseStop, _final_block
    try:
        lines = _final_block(data.decode("utf-8"))
    except (ReleaseStop, UnicodeError) as exc:
        raise ArmsFreezeError(f"amendments: {path} has no final fenced block with a frozen: line") from exc
    block = {}
    for line in lines:
        m = re.fullmatch(r"([a-z_0-9]+): (.*)", line)
        if not m or m.group(1) in block:
            raise ArmsFreezeError(f"amendments: {path}'s final block has a line that is not a unique 'key: value'")
        block[m.group(1)] = m.group(2).strip()
    return block


def _utc(value) -> datetime | None:
    """A ``YYYY-MM-DDTHH:MM[:SS]Z`` time (no offset, no fraction; the preregistration's ``frozen_utc`` form), or None."""
    v = str(value or "")
    if not re.fullmatch(UTC_RE, v):
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ" if v.count(":") == 2 else "%Y-%m-%dT%H:%MZ")
    except ValueError:
        return None


def _check_amendment_files(amendments: list, repo: Path, fitter_sha256: str) -> int:
    """Each amendment re-hashed as a committed file of the checkout (``release._committed``); its final block must be
    frozen and signed (R1-POSTFREEZE-READS: signed before the record): ``frozen: true``, ``signed_by`` filled,
    ``signed_utc`` and ``frozen_utc`` in the ``YYYY-MM-DDTHH:MM[:SS]Z`` form with ``signed_utc <= frozen_utc``; it must
    name the entry's PLAN row and the frozen preregistration, and bind the fitter the record names
    (``constants_fitter_sha256``) and the **committed** ``r1/c3/arms_freeze.py`` of this checkout
    (``arms_freeze_sha256``; A§13, A§12 item 22). Because of that binding the record can be re-checked only at a commit
    whose ``arms_freeze.py`` is the bound one. Returns the files read."""
    from r1.c3.release import ReleaseStop, _committed
    n = 0
    try:
        arms_freeze_sha256 = _sha(_committed(ARMS_FREEZE_PATH, repo))
    except ReleaseStop as exc:
        raise ArmsFreezeError(f"amendments: {exc}") from exc
    for e in amendments:
        try:
            data = _committed(e["path"], repo)
        except ReleaseStop as exc:
            raise ArmsFreezeError(f"amendments: {exc}") from exc
        if _sha(data) != e["sha256"]:
            raise ArmsFreezeError(f"amendments: the committed {e['path']} differs from its sha256")
        block = _amendment_block(data, e["path"])
        want = {"frozen": "true", "plan_row": e["plan_row"], "amends": f"{PREREG_PATH} sha256 {PREREG_SHA256}",
                "constants_fitter_sha256": fitter_sha256, "arms_freeze_sha256": arms_freeze_sha256}
        bad = sorted(k for k, v in want.items() if block.get(k) != v)
        if bad:
            raise ArmsFreezeError(f"amendments: {e['path']}'s final block does not give the values the record needs "
                                  f"for {bad} (frozen, its PLAN row, the preregistration, units 1 and 2 bound)")
        signed, frozen = _utc(block.get("signed_utc")), _utc(block.get("frozen_utc"))
        if not block.get("signed_by") or block["signed_by"].startswith("<") or signed is None or frozen is None \
                or signed > frozen:
            raise ArmsFreezeError(f"amendments: {e['path']} is not signed and frozen as the record needs (signed_by; "
                                  "signed_utc and frozen_utc as YYYY-MM-DDTHH:MM[:SS]Z, signed_utc <= frozen_utc)")
        n += 1
    return n


def _check_fitter_commit(fitter: dict, repo: Path) -> None:
    """The fitter's sha256 is the sha256 of ``r1/c3/arms_constants.py`` at its code commit (``git show``)."""
    from r1.c3 import arms_constants as AC
    from r1.c3.release import _GIT_ERRORS, _git
    try:
        data = _git("show", f"{fitter['code_commit']}:{AC.FITTER_PATH}", root=repo)
    except _GIT_ERRORS as exc:
        raise ArmsFreezeError(f"rule_arms: {AC.FITTER_PATH} is not in the fitter's code commit "
                              f"{fitter['code_commit'][:12]}") from exc
    if _sha(data) != fitter["sha256"]:
        raise ArmsFreezeError(f"rule_arms: the fitter's sha256 is not that of {AC.FITTER_PATH} at its code commit")


def postfreeze_fields(constants: bytes, *, constants_path: str, amendment_path: str, amendment_sha256: str,
                      d3: tuple[str, bytes] | None = None) -> dict:
    """The record's ``amendments`` and ``rule_arms`` fields (post-freeze reads A§9) from the constants file's bytes
    (``r1/c3/arms_constants.py``; ``constants_path`` relative to the root the record's checker is given) and the
    signed amendment's path and sha256. ``d3``: (path, bytes) of the D.3 constants file if the D.3 pre-declaration
    pins one, else the field is null. Nothing is read here; the vectors are copied from the file."""
    from r1.c3 import arms_constants as AC
    c = AC.parse(constants)
    _relative(constants_path, "constants path")
    prov = {"fitter": dict(c["fitter"]), "constants": {"path": constants_path, "sha256": _sha(constants)},
            "receipts": {s: m["receipt_sha256"] for s, m in sorted(c["sources"].items())},
            "fit_population": c["fit_population"]}
    ra = {"A0": {"rule": A0_RULE, "constants": None},
          "A1": {"vectors": {n: list(v) for n, v in sorted(c["vectors"]["A1"].items())}, **json.loads(json.dumps(prov)),
                 "offline": AC.A1_OFFLINE},
          "A2": {"vectors": {n: list(v) for n, v in sorted(c["vectors"]["A2"].items())}, **json.loads(json.dumps(prov))},
          "d3_constants": None}
    if d3 is not None:
        _relative(d3[0], "D.3 constants path")
        ra["d3_constants"] = {"path": d3[0], "sha256": _sha(d3[1])}
        _check_d3_vectors(ra, d3[1])
    fields = {"amendments": [{"path": amendment_path, "sha256": amendment_sha256, "plan_row": REQUIRED_AMENDMENTS[0]}],
              "rule_arms": ra}
    _check_rule_arms(ra, c["t1"] | {"instances": []})
    return fields


def check_record(record: dict, *, repo=None, plan_text: str | None = None, artefact_root=None,
                 verify_git: bool = False, record_path: str | None = None, release_roots: dict | None = None,
                 constants_root=None, verify_committed: bool = False, require_file_checks: bool = False) -> dict:
    """Strict check of §4 step 4. ``repo``: the checkout holding the preregistration, gate, builder and G.1b summaries
    (default ``r1.harness.REPO``). ``plan_text``: PLAN to look up the decision rows (default the repo's).
    ``artefact_root``: if given, every arm artefact {path, sha256} is re-hashed under it. ``verify_git``: every code
    commit must be an ancestor of ``origin/main``. ``release_roots``: {source: release root} whose traindev receipts
    and partitions are re-hashed. Post-freeze reads fields (A§9): ``amendments`` and ``rule_arms`` are always checked
    in structure, and the amendment's PLAN row like the ``decisions`` rows; ``constants_root``: if given, the
    constants file and the D.3 constants file are re-hashed under it and compared with the record (bitwise);
    ``verify_committed``: the amendment is re-hashed as a committed file of ``repo`` and its final block checked, and
    the fitter's sha256 is checked against its code commit. ``require_file_checks``: a record carrying either field is
    refused unless both file checks run; the CLI sets it, so ``check`` and ``render`` never report a pass without them
    (``check``: a constants root from ``--constants-root`` or ``--artefact-root``; ``render``: ``--constants-root``;
    the committed-amendment check has no CLI opt-out). Returns a summary; raises ``ArmsFreezeError`` on the first
    failure."""
    from r1.harness import REPO
    from r1.c3.release import author_rows
    repo = Path(repo or REPO)
    if record_path is not None and not re.fullmatch(RECORD_PATH_RE, record_path):
        raise ArmsFreezeError(f"the record path must match {RECORD_PATH_RE} (release.row_text cites it)")
    if require_file_checks and {"amendments", "rule_arms"} & set(record) and \
            (constants_root is None or not verify_committed):
        raise ArmsFreezeError("the record's amendments/rule_arms need both file checks: a constants root "
                              "(--constants-root, or --artefact-root for check) and the committed-amendment check; "
                              "no pass is reported without them")
    missing = [k for k in REQUIRED_TOP if k not in record]
    if missing:
        raise ArmsFreezeError(f"the record lacks {missing}")
    if record["schema"] != RECORD_SCHEMA:
        raise ArmsFreezeError(f"schema must be {RECORD_SCHEMA}")
    pre = _prereg_block(repo)
    _pin(record["preregistration"], "preregistration", PREREG_PATH, PREREG_SHA256)
    if "g5_tail_amendment_sha256" in pre:
        from r1.c3.release import G5_TAILS_AMENDMENT_PATH

        _pin(record.get("g5_tail_amendment"), "g5_tail_amendment", G5_TAILS_AMENDMENT_PATH,
             pre["g5_tail_amendment_sha256"])
    gate_sha, builder_sha = _sha_file(repo / "r1/c3/gate.py"), _sha_file(repo / "r1/c3/gate_input_builder.py")
    if pre["gate_sha256"] != gate_sha or pre["gate_input_builder_sha256"] != builder_sha:
        raise ArmsFreezeError("the checkout's gate or builder is not the one the preregistration binds")
    _pin(record["gate"], "gate", "r1/c3/gate.py", pre["gate_sha256"])
    _pin(record["gate_input_builder"], "gate_input_builder", "r1/c3/gate_input_builder.py",
         pre["gate_input_builder_sha256"])
    _pin(record["split_file"], "split_file", "r1/c3/splits/c3_p3_split_v1.json", p3_split.P3_SPLIT_SHA256)
    _pin(record["noise_source"], "noise_source", NOISE_PATH, NOISE_SHA256)
    t0 = record["t0_nodes"]
    if not isinstance(t0, list) or tuple(sorted(t0)) not in {tuple(sorted(c)) for c in B.PRIMARY_T0_CHOICES}:
        raise ArmsFreezeError("t0_nodes must be the seven C3b nodes or all eight (PRE-WDBC B)")
    t1 = record["t1"]
    _check_t1(t1)
    g1b = record["g1b_summaries"]
    if not isinstance(g1b, dict) or set(g1b) != set(t1["suites"]):
        raise ArmsFreezeError("g1b_summaries must cover exactly the T1 node set")
    from r1.c3.release import ReleaseStop, _committed
    for node, pin in g1b.items():      # committed repo files, re-hashed as release_row does (m2)
        _pin(pin, f"g1b_summaries.{node}")
        try:
            data = _committed(pin["path"], repo)
        except ReleaseStop as exc:
            raise ArmsFreezeError(f"g1b_summaries.{node}: {exc}") from exc
        if _sha(data) != pin["sha256"]:
            raise ArmsFreezeError(f"g1b_summaries.{node}: the committed file differs from its sha256")
    lt = record["label_tables"]
    need = {"sweep1", "sweep2"} | ({"g5"} if t1["suites"] else set())
    if not isinstance(lt, dict) or set(lt) != need:
        raise ArmsFreezeError(f"label_tables must name exactly {sorted(need)}")
    for src, v in lt.items():
        for k in ("label_block_sha256", "traindev_partition_sha256", "receipt_sha256", "proposals_sha256"):
            if not _HEX.fullmatch(str((v or {}).get(k))):
                raise ArmsFreezeError(f"label_tables.{src}.{k} must be a sha256")
    ft = record["feature_tables"]
    if not isinstance(ft, dict) or ft.get("featurizer") != FEATURIZER:
        raise ArmsFreezeError(f"feature_tables.featurizer must be {FEATURIZER} (FEAT-ONE)")
    s1 = ft.get("sweep1") or {}
    if s1.get("sealed_proposals_sha256") != lt["sweep1"]["proposals_sha256"]:
        raise ArmsFreezeError("feature_tables.sweep1.sealed_proposals_sha256 must be the released sealed table")
    require_feat_one(s1.get("identity_check"), sealed_sha256=lt["sweep1"]["proposals_sha256"],
                     arms_sha256=s1.get("arms_proposals_sha256"))
    feature_sha = {src: (s1["arms_proposals_sha256"] if src == "sweep1" else lt[src]["proposals_sha256"])
                   for src in need}
    for src in sorted(need - {"sweep1"}):
        if (ft.get(src) or {}).get("proposals_sha256") != lt[src]["proposals_sha256"]:
            raise ArmsFreezeError(f"feature_tables.{src} must be the released table ({src} is built with v3)")
    row_text = dict(author_rows(plan_text if plan_text is not None
                                else (repo / "docs/r1/PLAN.md").read_text(encoding="utf-8")))
    rows = set(row_text)
    st = record["a3_settings"]
    if not isinstance(st, dict) or set(st) != {"calibration", "twin_weight"} or \
            st["calibration"] not in CALIBRATIONS or st["twin_weight"] not in TWIN_WEIGHTS:
        raise ArmsFreezeError(f"a3_settings must give calibration in {CALIBRATIONS} and twin_weight in {TWIN_WEIGHTS} "
                              "(ARMS-CAL, ARMS-TWIN)")
    dec = record["decisions"]
    for d in REQUIRED_DECISIONS:
        row = (dec or {}).get(d)
        if not isinstance(row, str) or not re.fullmatch(r"R1-[A-Z0-9-]+", row) or row not in rows:
            raise ArmsFreezeError(f"decision {d} must cite an author row of PLAN §10 (got {row!r})")
    if t1["suites"]:                    # A5's T1 input (D7 of the ARMS-T1FEAT A report) must be signed
        if dec["ARMS-T1FEAT"] not in D7_ROWS:
            raise ArmsFreezeError("a non-empty T1 set needs A5's T1 input (D7 of the ARMS-T1FEAT A report) signed: the "
                                  f"row ARMS-T1FEAT cites must be one of the rows recording D7, {list(D7_ROWS)} (got "
                                  f"{dec['ARMS-T1FEAT']})")
        if not re.search(r"(?<![\w-])D7-FORM A\b", row_text.get(D7_FORM_ROW, "")):
            raise ArmsFreezeError(f"a non-empty T1 set needs the PLAN row {D7_FORM_ROW} adopting D7-FORM A "
                                  "(trackp_prompt_t1/1 as A5's T1 input)")
    disc = record["disclosures"]
    if not isinstance(disc, dict) or any(not isinstance(disc.get(k), str) or not disc[k].strip()
                                         for k in REQUIRED_DISCLOSURES):
        raise ArmsFreezeError(f"disclosures must state {list(REQUIRED_DISCLOSURES)} (§4 step 4)")
    fa = record["fold_arms"]
    if not isinstance(fa, dict) or set(fa) != {"A3", "A5"} or \
            any(v != "built" and not re.fullmatch(r"not_built:R1-[A-Z0-9-]+", str(v)) for v in fa.values()):
        raise ArmsFreezeError("fold_arms must be {A3, A5}: 'built' or 'not_built:<author row>'")
    for v in fa.values():
        if v != "built" and v.split(":", 1)[1] not in rows:
            raise ArmsFreezeError(f"fold_arms cites an absent author row: {v}")
    if not isinstance(record["secondary_arms"], list):
        raise ArmsFreezeError("secondary_arms must be a list (ARMS-SECONDARY)")
    arms = record["arms"]
    want = required_arms(record)
    absent = [a for a in want if a not in (arms or {})]
    extra = sorted(set(arms or {}) - set(want))
    if absent or extra:
        raise ArmsFreezeError(f"arms missing {absent[:6]} or undeclared {extra[:6]}")
    commits = set()
    for name, e in arms.items():
        miss = [k for k in ARM_FIELDS if k not in e]
        if miss:
            raise ArmsFreezeError(f"arm {name} lacks {miss}")
        role = "fold" if "@" in name else "primary" if name in ("A3", "A5") else "secondary"
        if e["role"] != role:
            raise ArmsFreezeError(f"arm {name}: role must be {role}")
        if not _COMMIT.fullmatch(str(e["code_commit"])):
            raise ArmsFreezeError(f"arm {name}: code_commit must be a 40-hex commit")
        commits.add(e["code_commit"])
        for k in ("checkpoint", "calibration", "predictions"):
            _pin(e[k], f"arm {name}.{k}")
        ps = e["preselect"]
        vals = (ps or {}).get("dev_values")
        if not isinstance(vals, dict) or ps.get("choice") not in vals or \
                not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vals.values()):
            raise ArmsFreezeError(f"arm {name}: preselect needs the choice and finite dev values of every candidate")
        if name.split("@")[0].startswith("A5"):
            _pin(e.get("p4_arm_pin"), f"arm {name}.p4_arm_pin")
        if name.split("@")[0] == "A3":      # M4: the tables A3 was trained on are the record's tables
            inputs = e.get("inputs")
            if not isinstance(inputs, dict) or set(inputs) != need:
                raise ArmsFreezeError(f"arm {name}: inputs must name exactly {sorted(need)}")
            for src in sorted(need):
                got = inputs[src] or {}
                if got.get("receipt_sha256") != lt[src]["receipt_sha256"] or \
                        got.get("traindev_partition_sha256") != lt[src]["traindev_partition_sha256"] or \
                        got.get("table_proposals_sha256") != feature_sha[src]:
                    raise ArmsFreezeError(f"arm {name}: inputs.{src} differ from label_tables/feature_tables")
            if e.get("calibration_mode") != st["calibration"] or e.get("twin_weight") != st["twin_weight"]:
                raise ArmsFreezeError(f"arm {name}: calibration_mode/twin_weight differ from a3_settings")
            tc = e.get("toolchain")
            if not isinstance(tc, dict) or set(tc) != TOOLCHAIN_KEYS or not all(isinstance(v, str) for v in tc.values()):
                raise ArmsFreezeError(f"arm {name}: toolchain must give {sorted(TOOLCHAIN_KEYS)} versions")
    _check_amendments(record["amendments"], rows)                     # post-freeze reads A§9 (unit 2)
    prov = _check_rule_arms(record["rule_arms"], t1)
    commits.add(prov["fitter"]["code_commit"])
    constants_read = 0 if constants_root is None else _check_constants_files(
        record["rule_arms"], constants_root, lt, t1, record["gate_input_builder"]["sha256"])
    amendments_read = 0
    if verify_committed:
        _check_fitter_commit(prov["fitter"], repo)
        amendments_read = _check_amendment_files(record["amendments"], repo, prov["fitter"]["sha256"])
    checked = 0
    if artefact_root is not None:
        root = Path(artefact_root)
        pins = [(f"{n}.{k}", e[k]) for n, e in arms.items() for k in ("checkpoint", "calibration", "predictions",
                                                                         "p4_arm_pin") if k in e]
        for what, pin in pins:
            f = root / pin["path"]
            got = tree_sha256(f) if f.is_dir() else _sha_file(f) if f.is_file() else None
            if got != pin["sha256"]:
                raise ArmsFreezeError(f"{what}: {f} is missing or differs from its sha256")
            checked += 1
        for name, e in arms.items():
            if name.split("@")[0].startswith("A5"):
                a5_pin_binding(e, root)
    if verify_git:
        for c in sorted(commits):
            if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", c, "refs/remotes/origin/main"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
                raise ArmsFreezeError(f"code commit {c} is not an ancestor of origin/main")
    receipts = _check_receipts(lt, release_roots or {})
    return {"pass": True, "arms": sorted(arms), "artefacts_rehashed": checked, "receipts_rehashed": receipts,
            "code_commits": sorted(commits), "constants_files_rehashed": constants_read,
            "amendments_rehashed": amendments_read}


# ============================================================================================== CLI

def _code_commit() -> str:
    """HEAD of a clean checkout whose arms_freeze.py is the committed file (``release._committed``)."""
    from r1.c3 import release
    release._committed("r1/c3/arms_freeze.py")
    dirty = release._git("status", "--porcelain", "--untracked-files=no").decode().strip()
    if dirty:
        raise ArmsFreezeError("the arms run needs a clean checkout (tracked changes present)")
    return release._head()


def _kv(items) -> dict:
    out = {}
    for it in items or ():
        k, _, v = it.partition("=")
        if not k or not v or k in out:
            raise ArmsFreezeError(f"expected unique SOURCE=VALUE, got {it!r}")
        out[k] = v
    return out


def _tier1(path) -> B.Tier1 | None:
    if not path:
        return None
    d = json.loads(Path(path).read_text())
    return B.Tier1(suites=d["suites"], modes=tuple(d["modes"]), d3_k6=bool(d["d3_k6"])) if d.get("suites") else None


def _train_cmd(a) -> dict:
    tables_dirs, receipts, roots = _kv(a.table), _kv(a.receipt), _kv(a.release_root)
    if not (set(tables_dirs) == set(receipts) == set(roots)) or not {"sweep1", "sweep2"} <= set(tables_dirs):
        raise ArmsFreezeError("--table, --receipt and --release-root must name the same sources, sweep1 and sweep2 "
                              "included")
    out, artefact_root = Path(a.out), Path(a.artefact_root)
    if artefact_root.resolve() not in out.resolve().parents:
        raise ArmsFreezeError("--out must lie inside --artefact-root (record paths are relative to it)")
    identity = json.loads(Path(a.identity).read_text())
    t1 = _tier1(a.t1)
    if t1 is not None and "g5" not in tables_dirs:
        raise ArmsFreezeError("a frozen T1 set needs the g5 table and receipt")
    commit = _code_commit()
    assign = p3_split.assignment(p3_split.load())
    tables, trows, inputs = {}, {}, {}
    for src in sorted(tables_dirs):
        labels, receipt = load_traindev(roots[src], src, receipts[src])
        rows = load_table_rows(tables_dirs[src])
        table_sha = _sha_file(Path(tables_dirs[src]) / "proposals.jsonl")
        if src == "sweep1":     # FEAT-ONE: the pinned v3 arms table, bound to the released sealed table
            require_feat_one(identity, sealed_sha256=receipt["inputs"]["proposals_sha256"], arms_sha256=table_sha)
        elif table_sha != receipt["inputs"]["proposals_sha256"]:
            raise ArmsFreezeError(f"{src}: the table is not the one the receipt released")
        if src == "g5" and t1 is not None and t1.needs_tail_binding:
            t1 = B.bind_g5_tail_laws(t1, tables_dirs[src], receipt)
        tables[src] = rows
        trows[src] = training_rows(src, rows, labels, assign=assign, t1=t1)
        inputs[src] = {"table_proposals_sha256": table_sha, "receipt_sha256": receipts[src],
                       "traindev_partition_sha256": receipt["outputs"]["label_block.traindev.jsonl"]}
    out.mkdir(parents=True, exist_ok=False)
    primary_dev = B.primary_dev_population([B.Source(s, rows) for s, rows in sorted(tables.items())])
    entries = {"A3": write_arm(out / "A3", "A3", freeze_a3(tables, trows, calibration=a.calibration,
                                                            primary_dev=primary_dev, twin_weight=a.twin_weight),
                               code_commit=commit, role="primary", inputs=inputs, artefact_root=artefact_root)}
    if a.folds:
        t0 = B.ALL_T0 if a.primary_t0 == "eight" else B.SEVEN_T0
        for fold, held in fold_plan(t0, t1).items():
            name = f"A3@{fold}"
            res = freeze_a3(tables, trows, calibration=a.calibration, held_out=held, primary_dev=primary_dev,
                            twin_weight=a.twin_weight)
            entries[name] = write_arm(out / name.replace("@", "__").replace(":", "__"), name, res,
                                      code_commit=commit, role="fold", inputs=inputs, artefact_root=artefact_root)
    (out / "entries.json").write_bytes(_dump(entries))
    return {k: {"choice": v["preselect"]["choice"], "n_predictions": v["n_predictions"]} for k, v in entries.items()}


def _postfreeze_cmd(a) -> dict:
    """``postfreeze-fields``: the two fields from the constants file under ``--constants-root`` and the committed
    signed amendment (checked as the record checker checks it), written once to ``--out``."""
    from r1.c3.release import ReleaseStop, _committed, author_rows
    from r1.harness import REPO
    out = Path(a.out)
    if out.exists():
        raise ArmsFreezeError(f"{out} exists; written once")
    root = Path(a.constants_root)
    _relative(a.constants, "--constants")
    constants = (root / a.constants).read_bytes()
    d3 = None
    if a.d3_constants:
        _relative(a.d3_constants, "--d3-constants")
        d3 = (a.d3_constants, (root / a.d3_constants).read_bytes())
    try:
        amendment = _committed(a.amendment, REPO)
    except ReleaseStop as exc:
        raise ArmsFreezeError(f"--amendment: {exc}") from exc
    fields = postfreeze_fields(constants, constants_path=a.constants, amendment_path=a.amendment,
                               amendment_sha256=_sha(amendment), d3=d3)
    rows = {i for i, _ in author_rows((REPO / "docs/r1/PLAN.md").read_text(encoding="utf-8"))}
    _check_amendments(fields["amendments"], rows)
    _check_fitter_commit(fields["rule_arms"]["A1"]["fitter"], REPO)
    _check_amendment_files(fields["amendments"], REPO, fields["rule_arms"]["A1"]["fitter"]["sha256"])
    out.write_bytes(_dump(fields))
    return {"out": str(out), "sha256": _sha_file(out), "amendment_sha256": fields["amendments"][0]["sha256"],
            "constants_sha256": fields["rule_arms"]["A1"]["constants"]["sha256"],
            "nodes": sorted(fields["rule_arms"]["A1"]["vectors"]), "d3_constants": fields["rule_arms"]["d3_constants"]}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="T0 arms freeze (ENGINEERING_ONLY; train/dev labels only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("identity", help="FEAT-ONE identity check: sealed table vs v3 arms table")
    i.add_argument("--sealed", required=True)
    i.add_argument("--arms-table", required=True)
    i.add_argument("--out", required=True)
    t = sub.add_parser("train-a3", help="A3 (and fold A3s): train, PRE-SELECT, calibrate, predict")
    t.add_argument("--release-root", action="append", required=True, help="SOURCE=DIR holding SOURCE/traindev")
    t.add_argument("--table", action="append", required=True, help="SOURCE=DIR (sweep1 = the v3 arms table)")
    t.add_argument("--receipt", action="append", required=True, help="SOURCE=sha256 of its traindev RECEIPT.json")
    t.add_argument("--identity", required=True, help="the passing FEAT-ONE identity JSON for sweep1")
    t.add_argument("--t1", help="JSON {suites, modes, d3_k6} of the frozen T1 set (omit for T0 only)")
    t.add_argument("--calibration", choices=CALIBRATIONS, required=True, help="ARMS-CAL, as the author row decides")
    t.add_argument("--twin-weight", choices=TWIN_WEIGHTS, required=True, help="ARMS-TWIN, as the author row decides")
    t.add_argument("--folds", action="store_true")
    t.add_argument("--primary-t0", choices=("seven", "eight"), default="seven")
    t.add_argument("--artefact-root", required=True, help="the root the record's artefact paths are relative to")
    t.add_argument("--out", required=True, help="a new directory inside --artefact-root")
    c = sub.add_parser("check", help="strict check of an arms-frozen record")
    c.add_argument("--record", required=True)
    c.add_argument("--artefact-root")
    c.add_argument("--constants-root", help="root of rule_arms' constants files (default: --artefact-root; one of the "
                                            "two is required for a record with rule_arms)")
    c.add_argument("--no-git", action="store_true", help="skip the commit-ancestry check (the committed-amendment "
                                                         "check always runs)")
    c.add_argument("--release-root", action="append", help="SOURCE=DIR: re-hash its traindev receipt and partition")
    w = sub.add_parser("render", help="render a record JSON into the Markdown record and check it")
    w.add_argument("--json", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--constants-root", help="root of rule_arms' constants files (required for a record with rule_arms)")
    p = sub.add_parser("postfreeze-fields", help="write the record's amendments and rule_arms fields (A§9)")
    p.add_argument("--constants", required=True, help="the constants file, relative to --constants-root")
    p.add_argument("--constants-root", required=True, help="the root the record's constants paths are relative to")
    p.add_argument("--d3-constants", help="the D.3 constants file, relative to --constants-root, if one is pinned")
    p.add_argument("--amendment", required=True, help="the signed amendment's repository path (committed)")
    p.add_argument("--out", required=True, help="a new JSON file holding the two fields")
    a = ap.parse_args(argv)
    if a.cmd == "postfreeze-fields":
        print(json.dumps(_postfreeze_cmd(a), indent=1))
        return 0
    if a.cmd == "identity":
        res = identity_check(a.sealed, a.arms_table)
        Path(a.out).write_bytes(_dump(res))
        print(json.dumps({k: res[k] for k in ("pass", "n_sealed", "n_budget_frac_left_differ",
                                               "n_other_differences", "keys_equal", "configs_equal")}))
        return 0 if res["pass"] else 3
    if a.cmd == "train-a3":
        print(json.dumps(_train_cmd(a), indent=1))
        return 0
    if a.cmd == "render":
        record = json.loads(Path(a.json).read_text())
        check_record(record, record_path=a.out, constants_root=a.constants_root, verify_committed=True,
                     require_file_checks=True)
        if Path(a.out).exists():
            raise ArmsFreezeError(f"{a.out} exists; the record is written once")
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(render_record(record))
        print(_sha_file(a.out))
        return 0
    rec = parse_record(Path(a.record).read_text())
    print(json.dumps(check_record(rec, artefact_root=a.artefact_root, verify_git=not a.no_git,
                                  record_path=a.record, release_roots=_kv(a.release_root),
                                  constants_root=a.constants_root or a.artefact_root,
                                  verify_committed=True, require_file_checks=True), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
