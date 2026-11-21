"""Gate-input builder of the sweep-2 C3 analysis (signed preregistration §3, PRE-MEM C, PRE-DUP A, PRE-DIV A, P3).

AI-assisted (Claude). It emits ``r1_d8_gate_input/v3.1`` (gate v3.1, PRE-WDBC B) from records handed to it; it opens
no file except the pinned P3 split file (``p3_split.load``). The records come from the receipted partitions of the
release step (PRE-STAGE A), after the test release row (§4 step 5); this module neither reads tables nor checks
receipts, and the partition reader enforces the lock. Its sha256 is the preregistration's
``gate_input_builder_sha256``.

What it computes (preregistration §3; every rule cited is quoted there):

* **Population and weights** (``offline_eval``'s, per (source, node) stratum over the whole table): no-ops and
  within-campaign duplicates weight 1; an audited non-inert proposal N_noninert / N_audited of its stratum; a
  non-inert proposal without a label row is not in the population (as ``offline_eval.assemble``); a label row whose
  ``audit_reason`` does not contain ``random`` is DI-selected and weighs 0 (evidence label blocks carry no reason).
* **Utility.** Per series, instance and memory mode, U = 20 × sum(w r) / sum(w) with r = Δ_true × keep − g × execute
  (``skip_credited_at_g``), decisions by ``offline_eval.decisions`` with the rule layer (no-ops have an inert belief,
  within-campaign duplicates are never executed), g = ``g_units`` × σ_node (0.1 primary).
* **Series.** A2 (PRE-A2 C): ``arms.RulesPrior`` fitted per node on the **dev** instances' label block of the gate
  sources (sweep 2 for T0, G.5 for T1; the full dev population), no other data. A3, A5: the frozen arms'
  predictions, supplied per proposal id (12 bins), with the A2/A3 rule override applied (no-op → inert; else inert
  mass 0, renormalised; idempotent on A3's output). Oracle: the soft label of the same proposal's label block,
  N(Δ_label, s²) with s = σ_node / √k_label (``labels.soft_label``, ``pooled_node``); a divergent label row
  (``label_kind: divergent``) has no belief and is never executed by the oracle.
* **Δ_true** from the evaluation block for every split (no-ops 0). PRE-DIV A: an evaluation row lists its
  ``divergent_seeds`` (absent = none); at most half divergent → partial (``delta_evaluation`` is the mean over the
  rest, counted); more than half → divergent, r = −g × execute, counted per series.
* **PRE-DUP A.** A repeat key is ``sft_data.dup_key`` (node | incumbent hash | candidate hash). ``population =
  "primary"`` leaves out of the **test** block every test proposal whose key occurs on a train or dev instance of
  any source supplied (sweep 1 and sweep 2 for T0); remaining weights are kept and renormalised.
  ``"full"`` (the PRE-DUP secondary run) keeps everything. Train and dev blocks are the full populations in both.
* **PRE-MEM C.** U per instance = the mean over the tier's declared modes of the per-mode U; a mode with no
  positive-weight proposal in the block's population contributes nothing and U is the other mode's (reported as a
  fallback); an instance with none in any mode is left out (reported). ``modes`` overrides the declared modes for the
  per-mode secondary runs.
* **Blocks.** Instances and their split come from the P3 split file (``p3_split``); a row outside it is refused.
  Train and dev blocks carry A2 and oracle, test also A3 and A5; instance ids sorted. A declared T0 node without a
  train, dev or test instance is a refusal; a T1 node without a train or dev instance (PRE-T1) or without a test
  instance left is not supplied and is reported.
* **Seeds.** Label rows must name the tier's label seeds, evaluation rows its evaluation seeds (T0: 7001–7005 /
  7006–7010; T1 under the R1-BX-D3 row: 7001–7003 / 7006–7008); anything else is refused (§6).

The output is ``(gate_input, report)``; the gate input is checked with the gate's own input validation before it is
returned. ``report`` holds the counts §5 and §7 ask for (PRE-DUP left-outs, mode fallbacks, partial and divergent
counts, unsupplied T1 nodes); it never holds a value of an unreleased block, because the builder runs only after
step 5.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from r1.c3 import gate as G
from r1.c3 import p3_split
from r1.c3.arms import RulesPrior, is_duplicate, is_noop
from r1.c3.labels import INERT, N_BINS, soft_label
from r1.c3.offline_eval import CAMPAIGN_RUNS, G_PRIMARY, decisions

BUILDER_VERSION = "1"
SCHEMA = G.INPUT_SCHEMA                      # r1_d8_gate_input/v3.1
T0_MODES = ("append_only_summary", "none")    # R1-MAIN-PROPOSER (b); PRE-MEM C
T0_LABEL_SEEDS = (7001, 7002, 7003, 7004, 7005)
T0_EVALUATION_SEEDS = (7006, 7007, 7008, 7009, 7010)
D3_LABEL_SEEDS = (7001, 7002, 7003)           # T1 under the R1-BX-D3 row (K = 6)
D3_EVALUATION_SEEDS = (7006, 7007, 7008)
PRIMARY_T0 = tuple(n for n in G.T0_NODES if n != "openml_wdbc")   # R1-S2C3B-WDBC: the seven C3b nodes
SENSITIVITY_T0 = G.T0_NODES                                       # PRE-WDBC B: all eight
POPULATIONS = ("primary", "full")
TRAIN_DEV_SERIES = ("A2", "oracle")
TEST_SERIES = ("A2", "oracle", "A3", "A5")
SUPPLIED_ARMS = ("A3", "A5")


class BuilderError(ValueError):
    """An input refusal (§4): raised before any statistic; fixed and the run repeated, both recorded."""


@dataclass
class Source:
    """One source's released records. ``gate``: True for the gate sources (sweep 2 for T0, G.5 for T1), whose
    instances fill the blocks; False for a source that only contributes repeat keys (sweep 1)."""
    name: str
    rows: list                       # table rows (proposals.jsonl)
    labels: list = field(default_factory=list)        # label-block rows (label_block.jsonl format)
    evaluations: list = field(default_factory=list)   # evaluation-block rows (evaluation_block.jsonl format)
    gate: bool = True


@dataclass
class Tier1:
    """The frozen T1 setting (arms-frozen record; PRE-T1, G5-MEM, R1-BX-D3)."""
    suites: dict                     # {node: suite}, suite in gate.SUITES
    modes: tuple                     # the declared memory mode(s) under G5-MEM
    d3_k6: bool = False              # the R1-BX-D3 row exists: K = 6


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def repeat_key(row: dict) -> str:
    """``sft_data.dup_key`` (copied: that module imports the harness); a test checks equality."""
    return f"{row['node']}|{row['incumbent_hash']}|{row['candidate_hash']}"


def _tier_of(node: str) -> str:
    return "T0" if node in G.T0_NODES else "T1"


def _seeds(tier: str, t1: Tier1 | None) -> tuple[tuple, tuple]:
    if tier == "T1" and t1 is not None and t1.d3_k6:
        return D3_LABEL_SEEDS, D3_EVALUATION_SEEDS
    return T0_LABEL_SEEDS, T0_EVALUATION_SEEDS


def _modes(tier: str, t1: Tier1 | None, override) -> tuple:
    if override is not None:
        return tuple(override)
    if tier == "T0":
        return T0_MODES
    if t1 is None or not t1.modes:
        raise BuilderError("T1 rows supplied without the frozen T1 setting (modes under G5-MEM)")
    return tuple(t1.modes)


def _instance(row: dict, assign: dict) -> tuple[str, str]:
    inst = p3_split.instance_id(row["node"], row["instance_seed"])
    if row.get("instance") not in (None, inst):
        raise BuilderError(f"{row['proposal_id']}: instance {row.get('instance')!r} is not {inst!r}")
    if inst not in assign:
        raise BuilderError(f"{row['proposal_id']}: instance {inst} is not in the P3 split file (§6)")
    if assign[inst]["node"] != row["node"]:
        raise BuilderError(f"{row['proposal_id']}: instance {inst} belongs to another node")
    return inst, assign[inst]["split"]


def _label_ok(lab: dict, row: dict, label_seeds: tuple) -> str:
    """Validate a label row against its table row; returns its kind (rule_noop, audit, divergent)."""
    kind = lab.get("label_kind")
    if lab.get("node") != row["node"]:
        raise BuilderError(f"{row['proposal_id']}: label row node differs")
    if is_noop(row):
        if kind != "rule_noop":
            raise BuilderError(f"{row['proposal_id']}: a no-op needs a rule_noop label row")
        return kind
    if kind not in ("audit", "divergent"):
        raise BuilderError(f"{row['proposal_id']}: label kind {kind!r} is not audit/divergent")
    if tuple(lab.get("seeds") or ()) != label_seeds:
        raise BuilderError(f"{row['proposal_id']}: label seeds {lab.get('seeds')} are not {list(label_seeds)} (§6)")
    if kind == "audit":
        sp = lab.get("soft_parameters") or {}
        k = sp.get("k_label")
        if not isinstance(k, int) or isinstance(k, bool) or not (len(label_seeds) - k <= len(label_seeds) / 2) \
                or k > len(label_seeds):
            raise BuilderError(f"{row['proposal_id']}: k_label {k!r} is not a complete or partial label")
        if not _finite(lab.get("delta_label")) or sp.get("delta_label") != lab.get("delta_label"):
            raise BuilderError(f"{row['proposal_id']}: label value missing or inconsistent")
        if sp.get("sigma_node") != row["sigma_node"]:
            raise BuilderError(f"{row['proposal_id']}: soft-label sigma_node differs from the table's")
    return kind


def _evaluation(ev: dict | None, row: dict, eval_seeds: tuple) -> tuple[float | None, str]:
    """(Δ_true, status) with status complete / partial / divergent (PRE-DIV A)."""
    if ev is None:
        raise BuilderError(f"{row['proposal_id']}: audited proposal without an evaluation row")
    if ev.get("node") != row["node"] or tuple(ev.get("seeds") or ()) != eval_seeds:
        raise BuilderError(f"{row['proposal_id']}: evaluation row node or seeds differ (§6)")
    div = ev.get("divergent_seeds") or []
    if len(set(div)) != len(div) or not set(div) <= set(eval_seeds):
        raise BuilderError(f"{row['proposal_id']}: divergent_seeds are not evaluation seeds")
    if len(div) > len(eval_seeds) / 2:
        if ev.get("delta_evaluation") is not None:
            raise BuilderError(f"{row['proposal_id']}: a divergent proposal carries an evaluation value")
        return None, "divergent"
    if not _finite(ev.get("delta_evaluation")):
        raise BuilderError(f"{row['proposal_id']}: evaluation value missing or non-finite")
    return float(ev["delta_evaluation"]), ("partial" if div else "complete")


def _prepare(sources: list[Source], assign: dict, t1: Tier1 | None) -> tuple[list[dict], dict]:
    """Population rows of the gate sources (with instance, split, weight, label, Δ_true) and the repeat keys of
    train and dev instances of every source."""
    seen_ids, keys = set(), {"train": set(), "dev": set()}
    out = []
    for src in sources:
        labels = {}
        for lab in src.labels:
            if lab["proposal_id"] in labels:
                raise BuilderError(f"{src.name}: duplicate label row {lab['proposal_id']}")
            labels[lab["proposal_id"]] = lab
        evals = {}
        for ev in src.evaluations:
            if ev["proposal_id"] in evals:
                raise BuilderError(f"{src.name}: duplicate evaluation row {ev['proposal_id']}")
            evals[ev["proposal_id"]] = ev
        if not src.gate:
            if labels or evals:
                raise BuilderError(f"{src.name}: a repeat-key source carries no label or evaluation rows")
        prepared = []
        for row in src.rows:
            pid = row["proposal_id"]
            if pid in seen_ids:
                raise BuilderError(f"duplicate proposal id {pid}")
            seen_ids.add(pid)
            inst, split = _instance(row, assign)
            if split in keys:
                keys[split].add(repeat_key(row))
            if src.gate:
                prepared.append((row, inst, split))
        if not src.gate:
            continue
        used = set()
        n_non, n_aud = {}, {}
        for row, _, _ in prepared:
            if not (is_noop(row) or is_duplicate(row)):
                k = (row["source"], row["node"])
                n_non[k] = n_non.get(k, 0) + 1
                if row["proposal_id"] in labels:
                    n_aud[k] = n_aud.get(k, 0) + 1
        for row, inst, split in sorted(prepared, key=lambda x: x[0]["proposal_id"]):   # canonical order
            tier = _tier_of(row["node"])
            if tier == "T1" and t1 is None:
                raise BuilderError("T1 rows supplied without the frozen T1 setting (PRE-T1, G5-MEM, R1-BX-D3)")
            label_seeds, eval_seeds = _seeds(tier, t1)
            pid = row["proposal_id"]
            lab = labels.get(pid)
            r = {"row": row, "instance": inst, "split": split, "tier": tier, "mode": row["memory_mode"],
                 "key": repeat_key(row), "label_kind": None, "status": "complete"}
            if is_noop(row):
                if lab is None:
                    raise BuilderError(f"{pid}: a no-op without its rule_noop label row")
                r["label_kind"] = _label_ok(lab, row, label_seeds)
                r.update(weight=1.0, delta_true=0.0, soft=soft_label(None, None, row["sigma_node"], inert=True))
                used.add(pid)
                if pid in evals:
                    raise BuilderError(f"{pid}: a no-op carries an evaluation row")
            elif is_duplicate(row):
                if lab is not None or pid in evals:
                    raise BuilderError(f"{pid}: a within-campaign duplicate carries a label or evaluation row")
                r.update(weight=1.0, delta_true=0.0, soft=None)   # never executed under the rule layer
            else:
                if lab is None:
                    if pid in evals:
                        raise BuilderError(f"{pid}: evaluation row without a label row")
                    continue                                       # not in the population (offline_eval)
                kind = _label_ok(lab, row, label_seeds)
                k = (row["source"], row["node"])
                ratio = n_non[k] / n_aud[k]
                reason = lab.get("audit_reason")
                dt, status = _evaluation(evals.get(pid), row, eval_seeds)
                soft = None
                if kind == "audit":
                    soft = soft_label(lab["delta_label"], None, row["sigma_node"], sigma_mode="pooled_node",
                                      k_label=lab["soft_parameters"]["k_label"])
                r.update(label_kind=kind, delta_true=dt, status=status, soft=soft,
                         weight=0.0 if (reason is not None and "random" not in str(reason)) else ratio)
                used.add(pid)
            out.append(r)
        unused = (set(labels) | set(evals)) - used
        if unused:
            raise BuilderError(f"{src.name}: label/evaluation rows for proposals outside the table: "
                               f"{sorted(unused)[:5]}")
    out.sort(key=lambda r: r["row"]["proposal_id"])   # sums and the A2 fit do not depend on input order
    return out, keys


def fit_a2(prepared: list[dict]):
    """PRE-A2 C: ``RulesPrior`` fitted on the dev instances' label block of the gate sources (full dev population).
    Training uses only node, flags, soft label and weight."""
    dev = [{"node": r["row"]["node"], "noop": is_noop(r["row"]), "duplicate": is_duplicate(r["row"]),
            "features": r["row"].get("features", {}), "soft": r["soft"], "weight": r["weight"]}
           for r in prepared if r["split"] == "dev" and r["soft"] is not None and r["weight"] > 0]
    if not any(not (d["noop"] or d["duplicate"]) for d in dev):
        raise BuilderError("no labelled non-inert dev proposal to fit A2 on")
    return RulesPrior().fit(dev)


def _override(P, rows):
    """The A2/A3 rule override: a no-op is inert; otherwise inert mass 0, renormalised."""
    P = np.array(P, float)
    if P.ndim != 2 or P.shape[1] != N_BINS or not np.isfinite(P).all() or (P < 0).any():
        raise BuilderError("arm predictions must be finite nonnegative 12-bin rows")
    out = np.zeros_like(P)
    for i, row in enumerate(rows):
        if is_noop(row):
            out[i, INERT] = 1.0
        else:
            q = P[i].copy()
            q[INERT] = 0.0
            if not q.sum() > 0:
                raise BuilderError(f"{row['proposal_id']}: prediction has no non-inert mass")
            out[i] = q / q.sum()
    return out


def _series_rewards(items: list[dict], series: str, a2, predictions: dict, g_units: float):
    """Per-row realised r for one series, and the indices of executed divergent rows."""
    rows = [it["row"] for it in items]
    if series == "A2":
        P = a2.predict(rows)
    elif series == "oracle":
        P = np.array([it["soft"] if it["soft"] is not None else _inert() for it in items])
    else:
        preds = predictions.get(series) or {}
        need = [r["proposal_id"] for r in rows if not is_noop(r)]
        missing = [p for p in need if p not in preds]
        if missing:
            raise BuilderError(f"{series}: no prediction for {len(missing)} proposals, e.g. {missing[:3]}")
        P = _override([preds.get(r["proposal_id"], _inert()) for r in rows], rows)
    ex, kp, (_, _, _, _, g) = decisions(P, rows, g_units, rule_layer=True)
    if series == "oracle":
        nobelief = np.array([it["label_kind"] == "divergent" for it in items], bool)
        ex, kp = ex & ~nobelief, kp & ~nobelief
    divergent = np.array([it["status"] == "divergent" for it in items], bool)
    d = np.array([0.0 if it["delta_true"] is None else it["delta_true"] for it in items])
    r = np.where(divergent, -g * ex, d * kp - g * ex)
    return r, int((divergent & ex).sum())


def _inert():
    p = np.zeros(N_BINS)
    p[INERT] = 1.0
    return p


def build(sources: list[Source], predictions: dict, noise: dict, *, t0_nodes=PRIMARY_T0, t1: Tier1 | None = None,
          population: str = "primary", g_units: float = G_PRIMARY, modes=None, split_path=None) -> tuple[dict, dict]:
    """The v3.1 gate input and its report. ``noise``: {node: {"delta_n", "sigma_node"}} (PRE-DELTA: D18 δ_n
    unscaled; T0 from the pinned noise source, T1 from the G.1b summaries). ``predictions``: {"A3": {pid: 12
    bins}, "A5": {...}} from the frozen arms."""
    if population not in POPULATIONS:
        raise BuilderError(f"population must be one of {POPULATIONS}")
    if not _finite(g_units) or g_units <= 0:
        raise BuilderError("g_units must be positive")
    t0_nodes = list(t0_nodes)
    if len(set(t0_nodes)) != len(t0_nodes) or not set(t0_nodes) <= set(G.T0_NODES):
        raise BuilderError(f"t0_nodes must be distinct members of {G.T0_NODES}")
    assign = p3_split.assignment(p3_split.load(split_path) if split_path else p3_split.load())
    prepared, keys = _prepare(sources, assign, t1)
    a2 = fit_a2(prepared)
    seen_traindev = keys["train"] | keys["dev"]
    by_node = {}
    for it in prepared:
        by_node.setdefault(it["row"]["node"], []).append(it)
    report = {"builder_version": BUILDER_VERSION, "population": population, "g_units": g_units,
              "t0_nodes": sorted(t0_nodes), "modes_override": list(modes) if modes is not None else None,
              "nodes": {}, "t1_not_supplied": {}, "skipped_nodes": [],
              "a2_fit_nodes": sorted(a2.by_node), "a2_pooled_fallback": sorted(set(by_node) - set(a2.by_node))}
    out_nodes = []
    for node in sorted(by_node):
        tier = _tier_of(node)
        if tier == "T0" and node not in t0_nodes:
            report["skipped_nodes"].append(node)
            continue
        if tier == "T1" and (t1 is None or node not in t1.suites):
            raise BuilderError(f"T1 node {node} has no frozen suite (PRE-T1)")
        if node not in noise or not _finite(noise[node].get("delta_n")) or noise[node]["delta_n"] <= 0:
            raise BuilderError(f"no positive δ_n for {node}")
        if any(it["row"]["sigma_node"] != noise[node]["sigma_node"] for it in by_node[node]):
            raise BuilderError(f"{node}: table sigma_node differs from the noise source")
        node_modes = _modes(tier, t1, modes)
        nrep = {"left_out_instances": {}, "mode_fallbacks": {}, "repeats_dropped_test": 0,
                "partial": 0, "divergent": 0, "divergent_executed": {}, "missing_instances": {}}
        blocks = {}
        for split in p3_split.SPLITS:
            series = TEST_SERIES if split == "test" else TRAIN_DEV_SERIES
            items = [it for it in by_node[node] if it["split"] == split]
            present = {it["instance"] for it in items}
            if split == "test" and population == "primary":
                kept = [it for it in items if it["key"] not in seen_traindev]
                nrep["repeats_dropped_test"] = len(items) - len(kept)
                items = kept
            nrep["partial"] += sum(it["status"] == "partial" for it in items)
            nrep["divergent"] += sum(it["status"] == "divergent" for it in items)
            design = [i for i, v in assign.items() if v["node"] == node and v["split"] == split]
            vals = {s: {} for s in series}
            if items:
                w = np.array([it["weight"] for it in items])
                for s in series:
                    r, n_div = _series_rewards(items, s, a2, predictions, g_units)
                    nrep["divergent_executed"][s] = nrep["divergent_executed"].get(s, 0) + n_div
                    for inst in sorted({it["instance"] for it in items}):
                        per_mode = []
                        for m in node_modes:
                            idx = [i for i, it in enumerate(items) if it["instance"] == inst and it["mode"] == m]
                            sw = float(w[idx].sum()) if idx else 0.0
                            if sw > 0:
                                per_mode.append(CAMPAIGN_RUNS * float((w[idx] * r[idx]).sum()) / sw)
                            elif s == series[0]:
                                nrep["mode_fallbacks"].setdefault(split, []).append(f"{inst}:{m}")
                        if per_mode:
                            vals[s][inst] = float(np.mean(per_mode))
            ids = sorted(vals[series[0]])
            if any(sorted(vals[s]) != ids for s in series):
                raise BuilderError(f"{node} {split}: series cover different instances")
            nrep["missing_instances"][split] = sorted(set(design) - present)
            nrep["left_out_instances"][split] = sorted(present - set(ids))
            blocks[split] = {"instance_ids": ids, **{s: [vals[s][i] for i in ids] for s in series}}
        empty = [s for s in p3_split.SPLITS if not blocks[s]["instance_ids"]]
        report["nodes"][node] = {**nrep, "tier": tier, "counts": {s: len(blocks[s]["instance_ids"])
                                                                  for s in p3_split.SPLITS}}
        if empty:
            if tier == "T0":
                raise BuilderError(f"declared T0 node {node} has no instance in {empty}")
            report["t1_not_supplied"][node] = empty
            continue
        out_nodes.append({"node": node, "suite": t1.suites[node] if tier == "T1" else None, "tier": tier,
                          "delta_n": float(noise[node]["delta_n"]),
                          "train": blocks["train"], "dev": blocks["dev"], "test": blocks["test"]})
    missing_t0 = sorted(set(t0_nodes) - {n["node"] for n in out_nodes})
    if missing_t0:
        raise BuilderError(f"declared T0 nodes without rows: {missing_t0}")
    gate_input = {"schema": SCHEMA, "split": dict(G.SPLIT), "t0_nodes": sorted(t0_nodes), "nodes": out_nodes}
    for n in out_nodes:
        for split in p3_split.SPLITS:
            for k, v in n[split].items():
                if k != "instance_ids" and not all(math.isfinite(x) for x in v):
                    raise BuilderError(f"{n['node']} {split} {k}: non-finite utility")
    G._validate(gate_input)          # the gate's own input validation (an input refusal, before any statistic)
    return gate_input, report


def runs(sources, predictions, noise, *, t1=None, split_path=None) -> dict:
    """The three gate inputs of §4 step 6: primary (seven T0 nodes, PRE-DUP primary), PRE-DUP secondary (seven,
    full test population) and PRE-WDBC sensitivity (eight, PRE-DUP primary)."""
    kw = {"t1": t1, "split_path": split_path}
    return {"primary": build(sources, predictions, noise, t0_nodes=PRIMARY_T0, population="primary", **kw),
            "dup_secondary": build(sources, predictions, noise, t0_nodes=PRIMARY_T0, population="full", **kw),
            "wdbc_sensitivity": build(sources, predictions, noise, t0_nodes=SENSITIVITY_T0, population="primary",
                                      **kw)}


def primary_dev_population(sources: list[Source], *, split_path=None) -> set:
    """PRE-DUP A for selection (PRE-SELECT): the proposal ids of dev proposals of the gate sources whose repeat key
    does not occur on any train instance of any source supplied."""
    assign = p3_split.assignment(p3_split.load(split_path) if split_path else p3_split.load())
    train_keys = set()
    dev = []
    for src in sources:
        for row in src.rows:
            inst, split = _instance(row, assign)
            if split == "train":
                train_keys.add(repeat_key(row))
            elif split == "dev" and src.gate:
                dev.append(row)
    return {r["proposal_id"] for r in dev if repeat_key(r) not in train_keys}
