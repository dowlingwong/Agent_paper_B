"""Fold analyses of the sweep-2 C3 analysis (PRE-SECONDARY A of the signed preregistration): descriptive only.

AI-assisted (Claude). Every analysis here reads test values, so it runs only after the test release row and the gate
runs (§4 step 7), with arms frozen in the arms-frozen record; none has a verdict.

* **Leave-one-suite-out** (``leave_one_suite_out``): per held-out suite of ``gate.SUITES``, the IQM and PoI over that
  suite's T1 nodes, with the fold arms trained without that suite (their predictions are supplied per fold). It STOPs
  as a whole, before any statistic, if a suite has no labelled T1 node (R1-BX-D8-CONFIRM, R1-B7-PARTIAL-T1): a
  labelled T1 node is a node of the frozen T1 set that the gate-input builder supplies.
* **Leave-one-node-out within T0** (``leave_one_node_out``): per held-out node of the declared T0 set, its gap closed
  with the fold arms trained without it.
* **Secondary recomputes** (``secondary_runs``): the gate statistics at g = 0.05 and 0.2 σ_node and per memory mode.

How (PRE-SECONDARY A: "calls the gate's statistics with a declared node subset (v3.1)"): each fold's input is built
by the accepted gate-input builder (``gate_input_builder.build``) on the records of the fold's nodes only — every
quantity the builder computes for a node (A2's per-node constants, the oracle, PRE-DUP keys, which carry the node)
depends only on that node's records, so a node's values equal those of the full build with the same predictions
(tested) — with the fold arms' predictions as A3 and A5 and the declared T0 node set of the subset (empty for a suite
fold). It is then evaluated by ``gate.evaluate`` (gate v3.1, its pins and the D8 check included). Eligibility applies
as in the gate; a gate STOP inside a fold (for example no IQM-eligible node) is reported for that fold. The output
keeps the gate's statistics and drops its decision fields (verdict, first-ranked arm, Holm rank and pass flags,
practical-size flag): ``descriptive: true``.

Readings (stated, for the coordinating chat): A2 and the oracle are not fold arms — A2 keeps PRE-A2 C's constants from
the node's own dev label block and the oracle its label-block belief, so a fold changes only A3 and A5; folds use the
PRE-DUP primary test population and g = 0.1 σ_node; leave-one-node-out runs over the primary T0 set of the
arms-frozen record; fold arms are selected by PRE-SELECT on the fold's dev instances by the arms pipeline, not here.
"""
from __future__ import annotations

from r1.c3 import gate as G
from r1.c3 import gate_input_builder as B

DECISION_KEYS = ("verdict", "first_ranked_arm")
ARM_DECISION_KEYS = ("rank", "tested", "passed", "meets_practical_size")


class FoldStop(RuntimeError):
    """A predeclared STOP of a fold analysis (no statistic is computed)."""


def node_subset(sources: list, nodes) -> list:
    """The sources restricted to the records of ``nodes`` (rows, label rows, evaluation rows); source names kept."""
    nodes = set(nodes)
    out = []
    for s in sources:
        rows = [r for r in s.rows if r["node"] in nodes]
        pids = {r["proposal_id"] for r in rows}
        out.append(B.Source(s.name, rows, [x for x in s.labels if x["proposal_id"] in pids],
                            [x for x in s.evaluations if x["proposal_id"] in pids]))
    return out


def fold_input(sources, predictions, noise, *, nodes, t1=None, g_units=B.G_PRIMARY, modes=None):
    """(gate input, builder report) for a node subset: the declared T0 set is the subset's T0 nodes."""
    nodes = sorted(set(nodes))
    t0 = [n for n in nodes if n in G.T0_NODES]
    t1_sub = None
    if t1 is not None:
        t1_sub = B.Tier1(suites={n: s for n, s in t1.suites.items() if n in nodes}, modes=t1.modes, d3_k6=t1.d3_k6)
    subset = node_subset(sources, nodes)
    if not t0:                                   # no T0 node: the sweep1 key source carries nothing for the fold
        subset = [s for s in subset if s.name != "sweep1"]
    return B.build(subset, predictions, noise, t0_nodes=t0, t1=t1_sub, population="primary",
                   g_units=g_units, modes=modes)


def _has_train_and_dev(sources, node) -> bool:
    """PRE-T1's supply rule on the gate sources' rows: at least one train and one dev instance of the node."""
    assign = B.p3_split.assignment(B.p3_split.load())
    splits = {assign.get(B.p3_split.instance_id(r["node"], r["instance_seed"]), {}).get("split")
              for s in sources if s.name in B.GATE_SOURCES for r in s.rows if r["node"] == node}
    return {"train", "dev"} <= splits


def descriptive(gate_output: dict) -> dict:
    """The gate's statistics without its decision fields."""
    out = {k: v for k, v in gate_output.items() if k not in DECISION_KEYS}
    out["arms"] = {a: {k: v for k, v in d.items() if k not in ARM_DECISION_KEYS}
                   for a, d in gate_output["arms"].items()}
    out["descriptive"] = True
    out["note"] = "PRE-SECONDARY A: descriptive, no verdict"
    return out


def _run(gate_input, evaluate):
    try:
        return {"statistics": descriptive(evaluate(gate_input))}
    except G.GateStop as exc:
        return {"gate_stop": str(exc)}


def leave_one_suite_out(sources, noise, fold_predictions: dict, *, t1, evaluate=None) -> dict:
    """Per held-out suite: the IQM and PoI over its T1 nodes with that fold's arms. ``fold_predictions``:
    {suite: {"A3": {pid: bins}, "A5": {...}}} for every suite of ``gate.SUITES``."""
    evaluate = evaluate or G.evaluate
    if t1 is None:
        raise FoldStop("STOP: leave-one-suite-out needs the frozen T1 setting")
    missing = [s for s in G.SUITES if s not in fold_predictions]
    if missing:
        raise FoldStop(f"STOP: no fold arms for suites {missing}")
    inputs, reports, without, unsupplied = {}, {}, [], {}
    for suite in G.SUITES:
        frozen = sorted(n for n, s in t1.suites.items() if s == suite)
        nodes = [n for n in frozen if _has_train_and_dev(sources, n)]          # PRE-T1, as the builder applies it
        unsupplied.update({n: "no train or dev instance" for n in frozen if n not in nodes})
        if not nodes:
            without.append(suite)
            continue
        gi, rep = fold_input(sources, fold_predictions[suite], noise, nodes=nodes, t1=t1)
        if not gi["nodes"]:
            without.append(suite)
        inputs[suite], reports[suite] = gi, rep
    if without:          # before any statistic: R1-BX-D8-CONFIRM's leave-one-suite-out STOP
        raise FoldStop(f"STOP: leave-one-suite-out needs a labelled T1 node in every suite; none in {without}")
    return {"analysis": "leave_one_suite_out", "descriptive": True, "t1_not_supplied": unsupplied,
            "folds": {s: {"nodes": [n["node"] for n in inputs[s]["nodes"]], "builder_report": reports[s],
                          **_run(inputs[s], evaluate)} for s in G.SUITES}}


def leave_one_node_out(sources, noise, fold_predictions: dict, *, primary_t0, evaluate=None) -> dict:
    """Per held-out T0 node of the primary set: its gap closed (and PoI) with that fold's arms.
    ``fold_predictions``: {node: {"A3": ..., "A5": ...}}."""
    evaluate = evaluate or G.evaluate
    primary_t0 = sorted(primary_t0)
    if tuple(primary_t0) not in {tuple(sorted(c)) for c in B.PRIMARY_T0_CHOICES}:
        raise FoldStop("STOP: primary_t0 must be the arms-frozen record's T0 set (seven C3b nodes or all eight)")
    missing = [n for n in primary_t0 if n not in fold_predictions]
    if missing:
        raise FoldStop(f"STOP: no fold arms for nodes {missing}")
    folds = {}
    for node in primary_t0:
        gi, rep = fold_input(sources, fold_predictions[node], noise, nodes=[node])
        res = _run(gi, evaluate)
        if "statistics" in res:
            row = res["statistics"]["nodes"][node]
            res["held_out"] = {k: row.get(k) for k in ("gap_closed_A3", "gap_closed_A5", "poi_A3", "poi_A5",
                                                       "included_in_iqm", "ineligible_reasons", "n_test")}
        folds[node] = {"builder_report": rep, **res}
    return {"analysis": "leave_one_node_out", "descriptive": True, "folds": folds}


def secondary_runs(sources, predictions, noise, *, primary_t0, t1=None, evaluate=None) -> dict:
    """The gate statistics at g = 0.05 and 0.2 σ_node and per memory mode (PRE-DUP primary, the primary T0 set)."""
    evaluate = evaluate or G.evaluate
    out = {}
    for g in (0.05, 0.2):
        gi, rep = B.build(sources, predictions, noise, t0_nodes=primary_t0, t1=t1, g_units=g)
        out[f"g_{g}"] = {"builder_report": rep, **_run(gi, evaluate)}
    for mode in B.T0_MODES:
        t1_mode = t1
        if t1 is not None and mode not in t1.modes:
            t1_mode = B.Tier1(suites={}, modes=t1.modes, d3_k6=t1.d3_k6)   # T1 nodes run in their declared modes only
        srcs = sources if t1_mode is t1 else [s for s in sources if s.name != "g5"]
        gi, rep = B.build(srcs, predictions, noise, t0_nodes=primary_t0, t1=t1_mode, modes=(mode,))
        out[f"mode_{mode}"] = {"builder_report": rep, **_run(gi, evaluate)}
    return {"analysis": "secondary_runs", "descriptive": True, "runs": out}
