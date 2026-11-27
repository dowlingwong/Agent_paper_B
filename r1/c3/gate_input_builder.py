"""Gate-input builder of the sweep-2 C3 analysis (signed preregistration §3, PRE-MEM C, PRE-DUP A, PRE-DIV A, P3).

AI-assisted (Claude). It emits ``r1_d8_gate_input/v3.1`` (gate v3.1, PRE-WDBC B) from records handed to it; it opens
no file except the pinned P3 split file (``p3_split.load``). The records come from the receipted partitions of the
release step (PRE-STAGE A), after the test release row (§4 step 5); this module neither reads tables nor checks
receipts, and the partition reader enforces the lock. Its sha256 is the preregistration's
``gate_input_builder_sha256``.

**Sources.** ``sweep2`` (the T0 gate source: its instances fill the T0 blocks; PRE-MEM "the gate's test population is
sweep 2 only"), ``g5`` (the T1 gate source) and ``sweep1`` (T0 repeat keys only, PRE-DUP "either source"; required
whenever T0 nodes are built). Any other source name, a source carrying rows of the other tier, or label or
evaluation rows on ``sweep1`` is refused.

What it computes (preregistration §3; every rule cited is quoted there):

* **Population and weights.** The evidence population is complete (every non-inert, non-duplicate proposal of a gate
  source is audited, inclusion probability 1), so ``offline_eval``'s weights (no-ops and within-campaign duplicates
  1; audited non-inert N_noninert / N_audited of the stratum; DI-selected 0) are all 1. A gate-source non-inert,
  non-duplicate row without its label row or its evaluation row is refused, as is a label row with an
  ``audit_reason`` (no DI-selected audits in evidence), so the weights cannot silently differ from 1.
* **Utility.** Per series, instance and memory mode, U = 20 × sum(w r) / sum(w) with r = Δ_true × keep − g × execute
  (``skip_credited_at_g``), decisions by ``offline_eval.decisions`` with the rule layer (within-campaign duplicates
  are never executed), g = ``g_units`` × σ_node (0.1 primary; 0.05 and 0.2 for the descriptive recomputes).
* **Series.** A2 (PRE-A2 C): ``arms.RulesPrior`` fitted per node on the **dev** instances' label block of the gate
  sources (the full dev population), no other data; a supplied node without a labelled non-inert dev proposal has no
  A1 constant and is refused (no pooled fallback). A3, A5: the frozen arms' predictions (12 bins per proposal id),
  used as given except the rule layer of §3: a no-op gets the inert belief (``arms.rule_skip``; duplicates are
  skipped in ``decisions``). Oracle: the soft label of the same proposal's label block, N(Δ_label, s²) with
  s = σ_node / √k_label (``labels.soft_label``, ``pooled_node``); a divergent label row (``label_kind: divergent``)
  has no belief and is never executed by the oracle.
* **Δ_true** from the evaluation block for every split (no-ops 0). PRE-DIV A: an evaluation row that admits
  divergence carries ``divergent_seeds`` and ``k_evaluation`` = number of seeds − number divergent (both or
  neither; neither = complete); at most half divergent → partial (``delta_evaluation`` over the rest, counted); more
  than half → divergent, r = −g × execute, counted per series. Label rows: k_label < K is a partial label (counted);
  ``divergent`` labels are counted.
* **PRE-DUP A.** A repeat key is ``sft_data.dup_key`` (node | incumbent hash | candidate hash). ``population =
  "primary"`` leaves out of the **test** block every test proposal (no-ops and within-campaign duplicates included,
  as the text reads) whose key occurs on a train or dev instance of any source supplied; the remaining weights are
  kept and renormalised. ``"full"`` (the PRE-DUP secondary run) keeps everything. Train and dev blocks are the full
  populations in both.
* **PRE-MEM C.** U per instance = the mean over the tier's declared modes of the per-mode U. Only in the test block of
  the PRE-DUP primary run may a mode lose every positive-weight proposal: U is then the other mode's U (reported), and
  an instance with none left in any mode is left out (reported). Anywhere else a design instance with rows but a
  declared mode without rows is refused. ``modes`` restricts the modes for the per-mode secondary runs (rows of other
  modes are excluded and counted); without it, rows of an undeclared mode are refused.
* **Blocks.** Instances and their split come from the P3 split file; a row outside it is refused. Train and dev blocks
  carry A2 and oracle, test also A3 and A5; instance ids sorted. A design instance without rows is missing (dropped
  without reassignment, reported). A declared T0 node without a train, dev or test instance is refused (if PRE-DUP
  empties a T0 test block, the refusal cannot be fixed: an author matter). A frozen T1 node without rows, without a
  train or dev instance (PRE-T1) or without a test instance left is not supplied and is reported.
* **T0 node set.** ``t0_nodes`` is required: the primary set comes from the arms-frozen record (the C3b nodes: the seven
  without openml_wdbc, or all eight if the C3b rerun gives 8/8; PRE-WDBC B); the sensitivity run uses all eight.
* **Seeds.** Label rows must name the tier's label seeds, evaluation rows its evaluation seeds (T0: 7001–7005 /
  7006–7010; T1 under the R1-BX-D3 row: 7001–7003 / 7006–7008); anything else is refused (§6).

The output is ``(gate_input, report)``; the gate input is checked with the gate's own input validation before it is
returned. ``report`` holds the counts §5 and §7 ask for (PRE-DUP left-outs and repeat-key sources, mode fallbacks,
partial and divergent counts, unsupplied T1 nodes); it holds no utility or label value.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from r1.c3 import gate as G
from r1.c3 import p3_split
from r1.c3.arms import RulesPrior, is_duplicate, is_noop
from r1.c3.labels import G5_GAUSSIAN_NODES, G5_STUDENT_T_NU, INERT, N_BINS, label_tail_options, soft_label
from r1.c3.offline_eval import CAMPAIGN_RUNS, G_PRIMARY, decisions

BUILDER_VERSION = "2"
SCHEMA = G.INPUT_SCHEMA                      # r1_d8_gate_input/v3.1
T0_MODES = ("append_only_summary", "none")    # R1-MAIN-PROPOSER (b); PRE-MEM C
T0_LABEL_SEEDS = (7001, 7002, 7003, 7004, 7005)
T0_EVALUATION_SEEDS = (7006, 7007, 7008, 7009, 7010)
D3_LABEL_SEEDS = (7001, 7002, 7003)           # T1 under the R1-BX-D3 row (K = 6)
D3_EVALUATION_SEEDS = (7006, 7007, 7008)
SEVEN_T0 = tuple(n for n in G.T0_NODES if n != "openml_wdbc")   # R1-S2C3B-WDBC: the seven C3b nodes at launch
ALL_T0 = G.T0_NODES                                              # PRE-WDBC B sensitivity: all eight
PRIMARY_T0_CHOICES = (SEVEN_T0, ALL_T0)                          # seven, or eight if the C3b rerun gives 8/8
GATE_SOURCES = {"sweep2": "T0", "g5": "T1"}
KEY_SOURCES = {"sweep1": "T0"}
POPULATIONS = ("primary", "full")
TRAIN_DEV_SERIES = ("A2", "oracle")
TEST_SERIES = ("A2", "oracle", "A3", "A5")


class BuilderError(ValueError):
    """An input refusal (§4): raised before any statistic; fixed and the run repeated, both recorded."""


@dataclass
class Source:
    """One source's released records: ``sweep2`` / ``g5`` (gate sources) or ``sweep1`` (repeat keys only)."""
    name: str
    rows: list                       # table rows (proposals.jsonl)
    labels: list = field(default_factory=list)        # label-block rows (label_block.jsonl format)
    evaluations: list = field(default_factory=list)   # evaluation-block rows (evaluation_block.jsonl format)
    split_sha256: str | None = None                   # G.5 release receipt's exact split binding
    tail_laws: dict[str, tuple[str, float | None]] = field(default_factory=dict)  # receipted G.5 build

    @property
    def gate(self) -> bool:
        return self.name in GATE_SOURCES


@dataclass
class Tier1:
    """The frozen T1 setting (arms-frozen record; PRE-T1, G5-MEM, R1-BX-D3)."""
    suites: dict                     # {node: suite}, suite in gate.SUITES: the frozen T1 node set
    modes: tuple                     # the declared memory mode(s) under G5-MEM
    d3_k6: bool = False              # the R1-BX-D3 row exists: K = 6
    # Verified from the completion or addendum, never inferred from a label row.
    tail_laws: dict[str, tuple[str, float | None]] = field(default_factory=dict)

    @property
    def needs_tail_binding(self) -> bool:
        return bool(self.suites.keys() - (G5_STUDENT_T_NU.keys() | G5_GAUSSIAN_NODES))


def bind_g5_tail_laws(t1: Tier1, table_dir, receipt: dict) -> Tier1:
    """Bind the frozen node context to already verified G.5 build metadata."""
    from r1.c3.release import g5_tail_laws

    laws = g5_tail_laws(table_dir, receipt)
    return replace(t1, tail_laws={node: laws[node] for node in t1.suites if node in laws})


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


def _declared_modes(tier: str, t1: Tier1 | None) -> tuple:
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


def _tail_options(lab: dict, tier: str, t1: Tier1 | None = None) -> dict:
    expected = t1.tail_laws.get(lab.get("node")) if tier == "T1" and t1 is not None else None
    try:
        return label_tail_options(lab, tier=tier, expected=expected)
    except ValueError as exc:
        raise BuilderError(f"{lab['proposal_id']}: {exc}") from exc


def _label_ok(lab: dict, row: dict, label_seeds: tuple) -> str:
    """Validate a label row against its table row; returns its kind (rule_noop, audit, divergent)."""
    kind = lab.get("label_kind")
    if lab.get("node") != row["node"]:
        raise BuilderError(f"{row['proposal_id']}: label row node differs")
    if "audit_reason" in lab:
        raise BuilderError(f"{row['proposal_id']}: an evidence label row carries no audit_reason (no DI selection)")
    if is_noop(row):
        if kind != "rule_noop":
            raise BuilderError(f"{row['proposal_id']}: a no-op needs a rule_noop label row")
        _tail_options(lab, _tier_of(row["node"]))
        return kind
    if kind not in ("audit", "divergent"):
        raise BuilderError(f"{row['proposal_id']}: label kind {kind!r} is not audit/divergent")
    if tuple(lab.get("seeds") or ()) != label_seeds:
        raise BuilderError(f"{row['proposal_id']}: label seeds {lab.get('seeds')} are not {list(label_seeds)} (§6)")
    if kind == "audit":
        sp = lab.get("soft_parameters") or {}
        k, n = sp.get("k_label"), len(label_seeds)
        if not isinstance(k, int) or isinstance(k, bool) or k > n or n - k > n / 2:
            raise BuilderError(f"{row['proposal_id']}: k_label {k!r} is not a complete or partial label")
        if not _finite(lab.get("delta_label")) or sp.get("delta_label") != lab.get("delta_label"):
            raise BuilderError(f"{row['proposal_id']}: label value missing or inconsistent")
        if sp.get("sigma_node") != row["sigma_node"]:
            raise BuilderError(f"{row['proposal_id']}: soft-label sigma_node differs from the table's")
    else:
        _tail_options(lab, _tier_of(row["node"]))
    return kind


def _evaluation(ev: dict | None, row: dict, eval_seeds: tuple) -> tuple[float | None, str]:
    """(Δ_true, status) with status complete / partial / divergent (PRE-DIV A)."""
    if ev is None:
        raise BuilderError(f"{row['proposal_id']}: audited proposal without its evaluation row (complete population)")
    if ev.get("node") != row["node"] or tuple(ev.get("seeds") or ()) != eval_seeds:
        raise BuilderError(f"{row['proposal_id']}: evaluation row node or seeds differ (§6)")
    has_div, has_k = "divergent_seeds" in ev, "k_evaluation" in ev
    if has_div != has_k:
        raise BuilderError(f"{row['proposal_id']}: divergent_seeds and k_evaluation come together")
    div = list(ev.get("divergent_seeds") or [])
    if len(set(div)) != len(div) or not set(div) <= set(eval_seeds):
        raise BuilderError(f"{row['proposal_id']}: divergent_seeds are not evaluation seeds")
    if has_k and ev["k_evaluation"] != len(eval_seeds) - len(div):
        raise BuilderError(f"{row['proposal_id']}: k_evaluation does not match divergent_seeds")
    if len(div) > len(eval_seeds) / 2:
        if ev.get("delta_evaluation") is not None:
            raise BuilderError(f"{row['proposal_id']}: a divergent proposal carries an evaluation value")
        return None, "divergent"
    if not _finite(ev.get("delta_evaluation")):
        raise BuilderError(f"{row['proposal_id']}: evaluation value missing or non-finite")
    return float(ev["delta_evaluation"]), ("partial" if div else "complete")


def _check_sources(sources: list[Source], need_sweep1: bool) -> None:
    """Distinct known source names; the sweep1 repeat-key source whenever T0 is built (PRE-DUP A: either source)."""
    names = [s.name for s in sources]
    if len(set(names)) != len(names) or not set(names) <= set(GATE_SOURCES) | set(KEY_SOURCES):
        raise BuilderError(f"sources must be distinct members of {sorted(GATE_SOURCES) + sorted(KEY_SOURCES)}")
    if need_sweep1 and "sweep1" not in names:
        raise BuilderError("T0 needs the sweep1 repeat-key source (PRE-DUP A: either source)")


def _source_row_ok(src: Source, row: dict) -> None:
    tier = GATE_SOURCES.get(src.name) or KEY_SOURCES[src.name]
    if row["node"] in p3_split.T1_EXTRA_TASKS:
        raise BuilderError(f"{row['node']}: a 1GC extra task is never supplied to the gate (R1-G5-S9)")
    if _tier_of(row["node"]) != tier:
        raise BuilderError(f"{src.name}: row {row['proposal_id']} of node {row['node']} is not a {tier} node")


def _prepare(sources: list[Source], assign: dict, t1: Tier1 | None) -> tuple[list[dict], dict, dict]:
    """Population rows of the gate sources (instance, split, weight, label, Δ_true), the repeat keys of train and dev
    instances of every source, and the repeat keys per source (for the report). Sources are checked by the caller."""
    seen_ids, keys, key_sources = set(), {"train": set(), "dev": set()}, {}
    out = []
    for src in sources:
        tier = GATE_SOURCES.get(src.name) or KEY_SOURCES[src.name]
        context = t1
        if src.tail_laws:
            if src.name != "g5" or t1 is None:
                raise BuilderError("the receipted G.5 tail laws require a frozen T1 context")
            if any(law != src.tail_laws[node] for node, law in t1.tail_laws.items() if node in src.tail_laws):
                raise BuilderError("the frozen context and G.5 receipt give different tail laws")
            if any(row["node"] not in src.tail_laws for row in src.rows):
                raise BuilderError("the G.5 receipt lacks a tail law for a source node")
            context = replace(t1, tail_laws=src.tail_laws)
        labels, evals = {}, {}
        for lab in src.labels:
            if lab["proposal_id"] in labels:
                raise BuilderError(f"{src.name}: duplicate label row {lab['proposal_id']}")
            labels[lab["proposal_id"]] = lab
        for ev in src.evaluations:
            if ev["proposal_id"] in evals:
                raise BuilderError(f"{src.name}: duplicate evaluation row {ev['proposal_id']}")
            evals[ev["proposal_id"]] = ev
        if not src.gate and (labels or evals):
            raise BuilderError(f"{src.name}: a repeat-key source carries no label or evaluation rows")
        mine = set()
        prepared = []
        for row in src.rows:
            pid = row["proposal_id"]
            if pid in seen_ids:
                raise BuilderError(f"duplicate proposal id {pid}")
            seen_ids.add(pid)
            _source_row_ok(src, row)
            inst, split = _instance(row, assign)
            if split in keys:
                keys[split].add(repeat_key(row))
                mine.add(repeat_key(row))
            if src.gate:
                prepared.append((row, inst, split))
        key_sources[src.name] = len(mine)
        if not src.gate:
            continue
        if tier == "T1" and t1 is None and prepared:
            raise BuilderError("T1 rows supplied without the frozen T1 setting (PRE-T1, G5-MEM, R1-BX-D3)")
        label_seeds, eval_seeds = _seeds(tier, t1)
        used = set()
        for row, inst, split in sorted(prepared, key=lambda x: x[0]["proposal_id"]):   # canonical order
            pid = row["proposal_id"]
            lab = labels.get(pid)
            r = {"row": row, "instance": inst, "split": split, "tier": tier, "mode": row["memory_mode"],
                 "key": repeat_key(row), "label_kind": None, "label_partial": False, "status": "complete",
                 "weight": 1.0}
            if is_noop(row):
                if lab is None:
                    raise BuilderError(f"{pid}: a no-op without its rule_noop label row")
                if pid in evals:
                    raise BuilderError(f"{pid}: a no-op carries an evaluation row")
                r["label_kind"] = _label_ok(lab, row, label_seeds)
                r.update(delta_true=0.0, soft=soft_label(None, None, row["sigma_node"], inert=True))
                used.add(pid)
            elif is_duplicate(row):
                if lab is not None or pid in evals:
                    raise BuilderError(f"{pid}: a within-campaign duplicate carries a label or evaluation row")
                r.update(delta_true=0.0, soft=None)               # never executed under the rule layer
            else:
                if lab is None:
                    raise BuilderError(f"{pid}: non-inert proposal without its label row (complete population)")
                kind = _label_ok(lab, row, label_seeds)
                dt, status = _evaluation(evals.get(pid), row, eval_seeds)
                soft = None
                if kind == "audit":
                    k = lab["soft_parameters"]["k_label"]
                    soft = soft_label(lab["delta_label"], None, row["sigma_node"], sigma_mode="pooled_node",
                                      k_label=k, **_tail_options(lab, tier, context))
                    r["label_partial"] = k < len(label_seeds)
                r.update(label_kind=kind, delta_true=dt, status=status, soft=soft)
                used.add(pid)
            out.append(r)
        unused = (set(labels) | set(evals)) - used
        if unused:
            raise BuilderError(f"{src.name}: label/evaluation rows for proposals outside the table: "
                               f"{sorted(unused)[:5]}")
    out.sort(key=lambda r: r["row"]["proposal_id"])   # sums and the A2 fit do not depend on input order
    return out, keys, key_sources


def fit_a2(prepared: list[dict]):
    """PRE-A2 C: ``RulesPrior`` fitted on the dev instances' label block of the gate sources (full dev population).
    Training uses only node, flags, soft label and weight."""
    dev = [{"node": r["row"]["node"], "noop": is_noop(r["row"]), "duplicate": is_duplicate(r["row"]),
            "features": r["row"].get("features", {}), "soft": r["soft"], "weight": r["weight"]}
           for r in prepared if r["split"] == "dev" and r["soft"] is not None]
    if not any(not (d["noop"] or d["duplicate"]) for d in dev):
        raise BuilderError("no labelled non-inert dev proposal to fit A2 on")
    return RulesPrior().fit(dev)


def _rule_layer(P, rows):
    """§3's rule layer on a supplied arm's predictions: a no-op gets the inert belief; other rows as given."""
    P = np.array(P, float)
    if P.ndim != 2 or P.shape[1] != N_BINS or not np.isfinite(P).all() or (P < 0).any() or \
            not np.allclose(P.sum(1), 1.0, atol=1e-6):
        raise BuilderError("arm predictions must be finite 12-bin distributions")
    for i, row in enumerate(rows):
        if is_noop(row):
            P[i] = _inert()
    return P


def _series_rewards(items: list[dict], series: str, a2, predictions: dict, g_units: float):
    """Per-row realised r for one series, and the number of executed divergent rows."""
    rows = [it["row"] for it in items]
    if series == "A2":
        P = a2.predict(rows)
    elif series == "oracle":
        P = np.array([it["soft"] if it["soft"] is not None else _inert() for it in items])
    else:
        preds = predictions.get(series) or {}
        missing = [r["proposal_id"] for r in rows if not is_noop(r) and r["proposal_id"] not in preds]
        if missing:
            raise BuilderError(f"{series}: no prediction for {len(missing)} proposals, e.g. {missing[:3]}")
        P = _rule_layer([preds.get(r["proposal_id"], _inert()) for r in rows], rows)
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


def _source_assignment(sources: list[Source], split_path=None) -> dict:
    pin_sha = next((s.split_sha256 for s in sources if s.name == "g5" and s.split_sha256), None)
    try:
        if split_path is not None:
            return p3_split.assignment(p3_split.load(split_path, sha256=pin_sha))
        split = p3_split.load_pinned(p3_split.pin_of_sha(pin_sha)) if pin_sha else p3_split.load()
        return p3_split.assignment(split)
    except p3_split.SplitError as exc:
        raise BuilderError(str(exc)) from exc


def build(sources: list[Source], predictions: dict, noise: dict, *, t0_nodes, t1: Tier1 | None = None,
          population: str = "primary", g_units: float = G_PRIMARY, modes=None, split_path=None) -> tuple[dict, dict]:
    """The v3.1 gate input and its report. ``t0_nodes``: the declared T0 node set (required). ``noise``: {node:
    {"delta_n", "sigma_node"}} (PRE-DELTA: D18 δ_n unscaled; T0 from the pinned noise source, T1 from the G.1b
    summaries). ``predictions``: {"A3": {pid: 12 bins}, "A5": {...}} from the frozen arms."""
    if population not in POPULATIONS:
        raise BuilderError(f"population must be one of {POPULATIONS}")
    if not _finite(g_units) or g_units <= 0:
        raise BuilderError("g_units must be positive")
    t0_nodes = list(t0_nodes)
    if len(set(t0_nodes)) != len(t0_nodes) or not set(t0_nodes) <= set(G.T0_NODES):
        raise BuilderError(f"t0_nodes must be distinct members of {G.T0_NODES}")
    _check_sources(sources, need_sweep1=bool(t0_nodes))
    if t1 is not None:
        for node, suite in t1.suites.items():
            if node in p3_split.T1_EXTRA_TASKS:
                raise BuilderError(f"{node}: a 1GC extra task is never supplied to the gate (R1-G5-S9)")
            if node in p3_split.T1_EXPANSION_MLGYM and suite != "MLGym":
                raise BuilderError(f"{node}: the expansion node is supplied as MLGym (R1-G5-S9)")
    assign = _source_assignment(sources, split_path)
    prepared, keys, key_sources = _prepare(sources, assign, t1)
    seen_traindev = keys["train"] | keys["dev"]
    by_node = {}
    for it in prepared:
        by_node.setdefault(it["row"]["node"], []).append(it)
    t1_nodes = set(t1.suites) if t1 is not None else set()
    stray = sorted(n for n in by_node if _tier_of(n) == "T1" and n not in t1_nodes)
    if stray:
        raise BuilderError(f"T1 nodes without a frozen suite (PRE-T1): {stray}")
    a2 = fit_a2(prepared)
    report = {"builder_version": BUILDER_VERSION, "population": population, "g_units": g_units,
              "t0_nodes": sorted(t0_nodes), "modes_override": list(modes) if modes is not None else None,
              "repeat_key_sources": key_sources, "nodes": {}, "t1_not_supplied": {}, "skipped_nodes": []}
    out_nodes = []
    for node in sorted(set(by_node) | t1_nodes | set(t0_nodes)):
        tier = _tier_of(node)
        if tier == "T0" and node not in t0_nodes:
            report["skipped_nodes"].append(node)
            continue
        if node not in by_node:
            if tier == "T0":
                raise BuilderError(f"declared T0 node {node} has no rows")
            report["t1_not_supplied"][node] = ["no rows"]
            continue
        if tier == "T1":                    # PRE-T1: a node needs a train and a dev instance to be supplied
            lacking = [sp for sp in ("train", "dev") if not any(it["split"] == sp for it in by_node[node])]
            if lacking:
                report["t1_not_supplied"][node] = lacking
                continue
        if node not in a2.by_node:
            raise BuilderError(f"{node}: no labelled non-inert dev proposal, so no A1 constant (PRE-A2 C)")
        if node not in noise or not _finite(noise[node].get("delta_n")) or noise[node]["delta_n"] <= 0:
            raise BuilderError(f"no positive δ_n for {node}")
        if any(it["row"]["sigma_node"] != noise[node]["sigma_node"] for it in by_node[node]):
            raise BuilderError(f"{node}: table sigma_node differs from the noise source")
        declared = _declared_modes(tier, t1)
        if modes is None:
            bad = sorted({it["mode"] for it in by_node[node]} - set(declared))
            if bad:
                raise BuilderError(f"{node}: rows of undeclared memory modes {bad}")
            node_modes = declared
        else:
            node_modes = tuple(modes)
            if not node_modes or not set(node_modes) <= set(declared):
                raise BuilderError(f"{node}: modes {node_modes} are not among the declared {declared}")
        nrep = {"left_out_instances": {}, "mode_fallbacks": {}, "repeats_dropped_test": 0,
                "rows_outside_modes": 0, "evaluation_partial": 0, "evaluation_divergent": 0,
                "label_partial": 0, "label_divergent": 0, "divergent_executed": {}, "missing_instances": {}}
        blocks = {}
        for split in p3_split.SPLITS:
            series = TEST_SERIES if split == "test" else TRAIN_DEV_SERIES
            items = [it for it in by_node[node] if it["split"] == split]
            present = {it["instance"] for it in items}
            inside = [it for it in items if it["mode"] in node_modes]
            nrep["rows_outside_modes"] += len(items) - len(inside)
            items = inside
            for inst in sorted(present):        # before PRE-DUP every declared mode of an instance has rows
                lacking = [m for m in node_modes if not any(it["instance"] == inst and it["mode"] == m
                                                            for it in items)]
                if lacking:
                    raise BuilderError(f"{node} {split} {inst}: no rows for mode(s) {lacking} (PRE-MEM C's fallback "
                                       "applies only to proposals left out under PRE-DUP A)")
            may_fall_back = split == "test" and population == "primary"
            if may_fall_back:
                kept = [it for it in items if it["key"] not in seen_traindev]
                nrep["repeats_dropped_test"] = len(items) - len(kept)
                items = kept
            for it in items:
                nrep["evaluation_partial"] += it["status"] == "partial"
                nrep["evaluation_divergent"] += it["status"] == "divergent"
                nrep["label_partial"] += it["label_partial"]
                nrep["label_divergent"] += it["label_kind"] == "divergent"
            design = [i for i, v in assign.items() if v["node"] == node and v["split"] == split]
            vals = {s: {} for s in series}
            w = np.array([it["weight"] for it in items])
            by_inst_mode = {}
            for i, it in enumerate(items):
                by_inst_mode.setdefault((it["instance"], it["mode"]), []).append(i)
            fallbacks, left_out = [], []
            for inst in sorted(present):
                empty = [m for m in node_modes if not (w[by_inst_mode.get((inst, m), [])].sum() > 0)]
                if empty and not may_fall_back:
                    raise BuilderError(f"{node} {split} {inst}: mode(s) {empty} without proposals (PRE-MEM C's "
                                       "fallback applies only under PRE-DUP A)")
                if len(empty) == len(node_modes):
                    left_out.append(inst)
                else:
                    fallbacks += [f"{inst}:{m}" for m in empty]
            if fallbacks:
                nrep["mode_fallbacks"][split] = fallbacks
            nrep["left_out_instances"][split] = left_out
            nrep["missing_instances"][split] = sorted(set(design) - present)
            ids = sorted(present - set(left_out))
            if items:
                for s in series:
                    r, n_div = _series_rewards(items, s, a2, predictions, g_units)
                    nrep["divergent_executed"][s] = nrep["divergent_executed"].get(s, 0) + n_div
                    for inst in ids:
                        per_mode = []
                        for m in node_modes:
                            idx = by_inst_mode.get((inst, m), [])
                            sw = float(w[idx].sum())
                            if sw > 0:
                                per_mode.append(CAMPAIGN_RUNS * float((w[idx] * r[idx]).sum()) / sw)
                        vals[s][inst] = float(np.mean(per_mode))
            blocks[split] = {"instance_ids": ids, **{s: [vals[s][i] for i in ids] for s in series}}
        empty_splits = [s for s in p3_split.SPLITS if not blocks[s]["instance_ids"]]
        report["nodes"][node] = {**nrep, "tier": tier, "counts": {s: len(blocks[s]["instance_ids"])
                                                                  for s in p3_split.SPLITS}}
        if empty_splits:
            if tier == "T0":
                raise BuilderError(f"declared T0 node {node} has no instance in {empty_splits}")
            report["t1_not_supplied"][node] = empty_splits
            continue
        out_nodes.append({"node": node, "suite": t1.suites[node] if tier == "T1" else None, "tier": tier,
                          "delta_n": float(noise[node]["delta_n"]),
                          "train": blocks["train"], "dev": blocks["dev"], "test": blocks["test"]})
    gate_input = {"schema": SCHEMA, "split": dict(G.SPLIT), "t0_nodes": sorted(t0_nodes), "nodes": out_nodes}
    for n in out_nodes:
        for split in p3_split.SPLITS:
            for k, v in n[split].items():
                if k != "instance_ids" and not all(math.isfinite(x) for x in v):
                    raise BuilderError(f"{n['node']} {split} {k}: non-finite utility")
    G._validate(gate_input)          # the gate's own input validation (an input refusal, before any statistic)
    return gate_input, report


def runs(sources, predictions, noise, *, primary_t0, t1=None, split_path=None) -> dict:
    """The three gate inputs of §4 step 6: primary (the arms-frozen record's T0 set, PRE-DUP primary), PRE-DUP
    secondary (the same T0 set, full test population) and PRE-WDBC sensitivity (all eight, PRE-DUP primary).
    ``primary_t0``: the seven C3b nodes, or all eight if the C3b rerun gave 8/8 (then the sensitivity run equals the
    primary, reported)."""
    primary_t0 = tuple(sorted(primary_t0))
    if primary_t0 not in {tuple(sorted(c)) for c in PRIMARY_T0_CHOICES}:
        raise BuilderError("primary_t0 must be the seven C3b nodes or all eight (PRE-WDBC B, arms-frozen record)")
    kw = {"t1": t1, "split_path": split_path}
    out = {"primary": build(sources, predictions, noise, t0_nodes=primary_t0, population="primary", **kw),
           "dup_secondary": build(sources, predictions, noise, t0_nodes=primary_t0, population="full", **kw),
           "wdbc_sensitivity": build(sources, predictions, noise, t0_nodes=ALL_T0, population="primary", **kw)}
    out["wdbc_sensitivity"][1]["equals_primary"] = primary_t0 == tuple(sorted(ALL_T0))
    return out


def primary_dev_population(sources: list[Source], *, split_path=None) -> set:
    """PRE-DUP A for selection (PRE-SELECT): the proposal ids of dev proposals of the gate sources whose repeat key
    does not occur on any train instance of any source supplied."""
    assign = _source_assignment(sources, split_path)
    _check_sources(sources, need_sweep1=any(_tier_of(r["node"]) == "T0" for s in sources for r in s.rows))
    train_keys = set()
    dev = []
    for src in sources:
        for row in src.rows:
            _source_row_ok(src, row)
            inst, split = _instance(row, assign)
            if split == "train":
                train_keys.add(repeat_key(row))
            elif split == "dev" and src.gate:
                dev.append(row)
    return {r["proposal_id"] for r in dev if repeat_key(r) not in train_keys}
