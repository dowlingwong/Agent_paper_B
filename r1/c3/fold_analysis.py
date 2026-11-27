"""Fold analyses of the sweep-2 C3 analysis (PRE-SECONDARY A of the signed preregistration): descriptive only.

AI-assisted (Claude). Every analysis here reads test values, so it runs only after the test release row and the gate
runs (§4 step 7), with arms frozen in the arms-frozen record; none has a verdict.

* **Leave-one-suite-out** (``leave_one_suite_out``): per held-out suite of ``gate.SUITES``, the IQM and PoI over that
  suite's T1 nodes, with the fold arms trained without that suite (their predictions are supplied per fold). It STOPs
  as a whole, before any statistic, if a suite has no labelled T1 node (R1-BX-D8-CONFIRM, R1-B7-PARTIAL-T1). The
  labelled T1 nodes are the T1 nodes of the §4 step-6 **primary gate input** (the gate's own
  ``t1_suites_without_labelled_node`` notion), which every function here takes as ``primary_input``.
* **Leave-one-node-out within T0** (``leave_one_node_out``): per held-out node of the primary input's declared T0 set,
  its gap closed and PoI with the fold arms trained without it.
* **Secondary recomputes** (``secondary_runs``): the statistics at g = 0.05 and 0.2 σ_node and per memory mode.

How (PRE-SECONDARY A: "calls the gate's statistics with a declared node subset (v3.1)"):

* Each fold's input is built by the accepted gate-input builder (``gate_input_builder.build``) on the records of the
  fold's nodes only, with the fold arms' predictions as A3 and A5 and the subset's declared T0 set (empty for a suite
  fold). Every quantity the builder computes for a node depends only on that node's records (A2's per-node constants,
  the oracle, PRE-DUP keys, which carry the node), so a fold node's instance ids, A2 and oracle blocks must equal those
  of ``primary_input``; this is checked for every fold node (it binds each fold to the step-6 input and to the full
  build's validation).
* All fold inputs are built and checked before any statistic is computed.
* ``fold_statistics`` computes the gate's statistics with gate v3.1's own functions after its D8 check and pins
  (``analysis_guard.require_d8_confirmation``, ``gate._require_pins``): ``gate._validate`` (eligibility),
  ``gate._point`` (gap closed per node, IQM, PoI), ``gate._bootstrap`` (the node-stratified resamples, seed and draws
  of the gate) and the gate's bound functions ``_lower_iqm`` / ``_lower_poi``. **No Holm step and no verdict:** both
  arms' lower bounds are reported at both declared levels (97.5 % and 95 %), so neither the level nor any field
  encodes a ranking. If the IQM is undefined (no IQM-eligible node, or a nonpositive test denominator on an eligible
  node: the gate's STOPs), the fold reports that STOP and the PoI of the fold's nodes (``gate._node_poi`` over all
  nodes; the gate's PoI never depends on eligibility).

Readings (stated, for the coordinating chat; see the report): A2 and the oracle are not fold arms; folds use the
PRE-DUP primary test population and g = 0.1 σ_node; leave-one-node-out runs over the primary input's T0 set; fold arms
are selected by PRE-SELECT on the fold's dev instances by the arms pipeline. Two author decisions are proposed in the
report with options: the PoI when a fold's IQM is undefined (FOLD-POI) and the interval levels (FOLD-LEVELS).
"""
from __future__ import annotations

from r1.c3 import analysis_guard
from r1.c3 import gate as G
from r1.c3 import gate_input_builder as B

SCHEMA = "r1_c3_fold_statistics/v1"


class FoldStop(RuntimeError):
    """The predeclared leave-one-suite-out STOP (R1-BX-D8-CONFIRM): no statistic is computed."""


class FoldInputError(ValueError):
    """An input refusal before any statistic (§4: fixed and the run repeated, both recorded)."""


def node_subset(sources: list, nodes) -> list:
    """The sources restricted to the records of ``nodes`` (rows, label rows, evaluation rows); source names kept."""
    nodes = set(nodes)
    out = []
    for s in sources:
        rows = [r for r in s.rows if r["node"] in nodes]
        pids = {r["proposal_id"] for r in rows}
        out.append(B.Source(s.name, rows, [x for x in s.labels if x["proposal_id"] in pids],
                            [x for x in s.evaluations if x["proposal_id"] in pids],
                            split_sha256=s.split_sha256,
                            tail_laws={node: law for node, law in s.tail_laws.items() if node in nodes}))
    return out


def _primary(primary_input: dict, primary_t0) -> tuple[list, dict, dict]:
    """(declared T0 set, {T1 node: suite}, {node: node entry}) of the step-6 primary gate input, whose T0 set must be
    ``primary_t0``, the arms-frozen record's (so the PRE-WDBC sensitivity input cannot stand in for it)."""
    if not isinstance(primary_input, dict) or primary_input.get("schema") != G.INPUT_SCHEMA:
        raise FoldInputError("primary_input must be the §4 step-6 primary gate input (r1_d8_gate_input/v3.1)")
    try:
        G._validate(primary_input)
    except (ValueError, G.GateStop) as exc:
        raise FoldInputError(f"primary_input is not a valid gate input: {exc}") from exc
    t0 = sorted(primary_input["t0_nodes"])
    want = sorted(primary_t0)
    if tuple(want) not in {tuple(sorted(c)) for c in B.PRIMARY_T0_CHOICES}:
        raise FoldInputError("primary_t0 must be the arms-frozen record's T0 set (seven C3b nodes or all eight)")
    if t0 != want:
        raise FoldInputError(f"the primary input declares T0 {t0}, not the arms-frozen record's {want}")
    nodes = {n["node"]: n for n in primary_input["nodes"]}
    t1 = {k: n["suite"] for k, n in nodes.items() if n["tier"] == "T1"}
    return t0, t1, nodes


def fold_input(sources, predictions, noise, *, nodes, t1=None, g_units=B.G_PRIMARY, modes=None):
    """(gate input, builder report) for a node subset: the declared T0 set is the subset's T0 nodes."""
    nodes = sorted(set(nodes))
    t0 = [n for n in nodes if n in G.T0_NODES]
    t1_sub = None
    if t1 is not None:
        t1_sub = B.Tier1(suites={n: s for n, s in t1.suites.items() if n in nodes}, modes=t1.modes,
                         d3_k6=t1.d3_k6, tail_laws={n: law for n, law in t1.tail_laws.items() if n in nodes})
    subset = node_subset(sources, nodes)
    if not t0:                                   # no T0 node: the sweep1 key source carries nothing for the fold
        subset = [s for s in subset if s.name != "sweep1"]
    gi, rep = B.build(subset, predictions, noise, t0_nodes=t0, t1=t1_sub, population="primary",
                      g_units=g_units, modes=modes)
    got = sorted(n["node"] for n in gi["nodes"])
    if got != nodes:
        raise FoldInputError(f"the fold supplies {got}, not the requested {nodes}")
    return gi, rep


def _bind(gi: dict, primary_nodes: dict) -> None:
    """A fold node's instances, A2 and oracle equal the primary input's (same records, same validation)."""
    for n in gi["nodes"]:
        p = primary_nodes.get(n["node"])
        if p is None:
            raise FoldInputError(f"fold node {n['node']} is not in the primary input")
        for key in ("delta_n", "suite", "tier"):
            if n[key] != p[key]:
                raise FoldInputError(f"fold node {n['node']} {key} differs from the primary input")
        for split in ("train", "dev", "test"):
            for key in ("instance_ids", "A2", "oracle"):
                if n[split][key] != p[split][key]:
                    raise FoldInputError(f"fold node {n['node']} {split} {key} differs from the primary input")


def fold_statistics(gate_input: dict) -> dict:
    """The gate's statistics on a (fold) input, without Holm or verdict (module docstring)."""
    analysis_guard.require_d8_confirmation()
    G._require_pins()
    nodes = G._validate(gate_input)
    poi = {arm: G._node_poi([(n["test"][arm].tolist(), n["test"]["A2"].tolist()) for n in nodes.values()])
           for arm in G.ARMS}
    out = {"schema": SCHEMA, "gate_schema": G.OUTPUT_SCHEMA, "gate_version": G.GATE_VERSION,
           "gate_sha256": G.gate_file_sha256(), "descriptive": True,
           "note": "PRE-SECONDARY A: descriptive, no verdict, no Holm ranking",
           "declared_t0_nodes": sorted(gate_input["t0_nodes"]), "levels": list(G.LEVELS),
           "probability_of_improvement": poi,
           "node_poi": {k: {arm: float(G._wins(n["test"][arm], n["test"]["A2"]).mean()) for arm in G.ARMS}
                        for k, n in nodes.items()},
           "ineligible_nodes": {k: list(n["ineligible_reasons"]) for k, n in nodes.items()
                                if n["ineligible_reasons"]},
           "node_fields": {k: {f: n[f] for f in ("suite", "tier", "delta_n", "dev_denominator", "train_dev_z",
                                                 "z_sd_zero", "n_train", "n_dev", "n_test", "n_total")}
                           for k, n in nodes.items()},
           "node_counts": {"total": len(nodes),
                           "by_tier": {t: sum(n["tier"] == t for n in nodes.values()) for t in G.TIERS},
                           "t1_by_suite": {s: sum(n["tier"] == "T1" and n["suite"] == s for n in nodes.values())
                                           for s in G.SUITES}}}
    try:
        eligible, table, summary = G._point(nodes)
    except G.GateStop as exc:
        out.update(iqm_undefined=str(exc), arms=None, nodes=None, tier_descriptive=None)
        return out
    boot, nonpositive = G._bootstrap(nodes, eligible, summary)
    arms = {}
    for arm in G.ARMS:
        b = boot[arm]
        arms[arm] = {**summary[arm],
                     "lower_bounds": {f"{lv:g}": {"lower_iqm_gap_closed": float(G._lower_iqm(b, lv)),
                                                  "lower_probability_of_improvement": float(G._lower_poi(b["poi"], lv))}
                                      for lv in G.LEVELS},
                     "resamples_with_infinite_tstar": int(b["infinite_tstar"])}
    for name in eligible:
        table[name]["resamples_nonpositive_denominator"] = nonpositive[name]
    out.update(iqm_undefined=None, arms=arms, nodes=table, eligible_nodes=list(eligible),
               tier_descriptive=G._tier_descriptive(nodes, table, eligible))
    return out


def leave_one_suite_out(sources, noise, fold_predictions: dict, *, primary_input: dict, primary_t0, t1,
                        statistics=None) -> dict:
    """Per held-out suite: the IQM and PoI over its labelled T1 nodes with that fold's arms. ``fold_predictions``:
    {suite: {"A3": {pid: bins}, "A5": {...}}} for every suite of ``gate.SUITES``."""
    statistics = statistics or fold_statistics
    _, labelled, primary_nodes = _primary(primary_input, primary_t0)
    without = [s for s in G.SUITES if s not in labelled.values()]
    if without:          # before any statistic: R1-BX-D8-CONFIRM's leave-one-suite-out STOP
        raise FoldStop(f"STOP: leave-one-suite-out needs a labelled T1 node in every suite; none in {without}")
    if t1 is None or any(t1.suites.get(n) != s for n, s in labelled.items()):
        raise FoldInputError("the frozen T1 setting does not match the primary input's T1 nodes and suites")
    missing = [s for s in G.SUITES if s not in fold_predictions]
    if missing:
        raise FoldInputError(f"no fold arms for suites {missing}")
    inputs = {}
    for suite in G.SUITES:
        nodes = sorted(n for n, s in labelled.items() if s == suite)
        inputs[suite] = fold_input(sources, fold_predictions[suite], noise, nodes=nodes, t1=t1)
        _bind(inputs[suite][0], primary_nodes)
    return {"analysis": "leave_one_suite_out", "schema": SCHEMA, "descriptive": True,
            "folds": {s: {"nodes": [n["node"] for n in inputs[s][0]["nodes"]], "builder_report": inputs[s][1],
                          "statistics": statistics(inputs[s][0])} for s in G.SUITES}}


def leave_one_node_out(sources, noise, fold_predictions: dict, *, primary_input: dict, primary_t0,
                       statistics=None) -> dict:
    """Per held-out T0 node of the primary input's T0 set: its gap closed and PoI with that fold's arms.
    ``fold_predictions``: {node: {"A3": ..., "A5": ...}}."""
    statistics = statistics or fold_statistics
    t0, _, primary_nodes = _primary(primary_input, primary_t0)
    missing = [n for n in t0 if n not in fold_predictions]
    if missing:
        raise FoldInputError(f"no fold arms for nodes {missing}")
    inputs = {}
    for node in t0:                                      # every input built and bound before any statistic
        inputs[node] = fold_input(sources, fold_predictions[node], noise, nodes=[node])
        _bind(inputs[node][0], primary_nodes)
    folds = {}
    for node in t0:
        st = statistics(inputs[node][0])
        row = (st.get("nodes") or {}).get(node) or {}
        folds[node] = {"builder_report": inputs[node][1], "statistics": st,
                       "held_out": {"gap_closed_A3": row.get("gap_closed_A3"),
                                    "gap_closed_A5": row.get("gap_closed_A5"),
                                    "poi_A3": st["node_poi"][node]["A3"], "poi_A5": st["node_poi"][node]["A5"],
                                    "ineligible_reasons": st["ineligible_nodes"].get(node, []),
                                    "iqm_undefined": st["iqm_undefined"]}}
    return {"analysis": "leave_one_node_out", "schema": SCHEMA, "descriptive": True, "folds": folds}


def secondary_runs(sources, predictions, noise, *, primary_input: dict, primary_t0, t1=None,
                   statistics=None) -> dict:
    """The statistics at g = 0.05 and 0.2 σ_node and per memory mode (PRE-DUP primary, the primary T0 set), with the
    primary arms' predictions."""
    statistics = statistics or fold_statistics
    t0, labelled, _ = _primary(primary_input, primary_t0)
    if labelled and (t1 is None or any(t1.suites.get(n) != s for n, s in labelled.items())):
        raise FoldInputError("the frozen T1 setting does not match the primary input's T1 nodes and suites")
    inputs = {}
    for g in (0.05, 0.2):
        inputs[f"g_{g}"] = B.build(sources, predictions, noise, t0_nodes=t0, t1=t1, g_units=g)
    for mode in B.T0_MODES:
        t1_mode, srcs = t1, sources
        if t1 is not None and mode not in t1.modes:    # T1 nodes run in their declared mode(s) only (G5-MEM)
            t1_mode, srcs = None, [s for s in sources if s.name != "g5"]
        inputs[f"mode_{mode}"] = B.build(srcs, predictions, noise, t0_nodes=t0, t1=t1_mode, modes=(mode,))
    return {"analysis": "secondary_runs", "schema": SCHEMA, "descriptive": True,
            "runs": {k: {"builder_report": rep, "statistics": statistics(gi)} for k, (gi, rep) in inputs.items()}}
