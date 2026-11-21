"""Fold analyses (PRE-SECONDARY A): synthetic records only. Gate statistics use gate v3.1's own functions and run
only under the pinned NumPy 2.4.4; the structural tests use a recording stand-in for ``fold_statistics``."""
import copy
import random
import sys
from pathlib import Path

import numpy as np
import pytest

from r1.c3 import fold_analysis as F
from r1.c3 import gate as G
from r1.c3 import gate_input_builder as B

sys.path.insert(0, str(Path(__file__).parent))
import test_gate_input_builder as W  # noqa: E402

SUITE_NODES = {"mlab_cifar10": "MLAgentBench", "mlgym_fmnist": "MLGym", "autoresearch_fixedtokens": "autoresearch"}
PINNED = np.__version__ == G.NUMPY_VERSION


def _world(t1_nodes=SUITE_NODES):
    srcs, preds, noise = W._world()
    ev = {e["proposal_id"]: e for e in srcs[0].evaluations}
    for lab in srcs[0].labels:               # informative labels, so that nodes are IQM-eligible
        if lab["label_kind"] == "audit":
            ev[lab["proposal_id"]]["delta_evaluation"] = lab["delta_label"]
    rows, labels, evals = [], [], []
    for node in t1_nodes:
        for inst, v in W.ASSIGN.items():
            if v["node"] == node:
                seed = int(inst.rsplit("__s", 1)[1])
                rows += [W._row(node, seed, "none", 2, "noop", src="g5")]
                rows += [W._row(node, seed, "none", t, src="g5") for t in range(3, 11)]
    rng = np.random.default_rng(5)
    for r in rows:
        lab = W._label(r)
        if not r["noop"]:
            d = random.Random("T" + r["proposal_id"]).gauss(-0.01, 0.03)
            lab["delta_label"] = lab["soft_parameters"]["delta_label"] = d
            e = W._evaluation(r)
            e["delta_evaluation"] = d
            evals.append(e)
        labels.append(lab)
        for a in ("A3", "A5"):
            preds[a][r["proposal_id"]] = rng.dirichlet(np.ones(12)).tolist()
    srcs.append(B.Source("g5", rows, labels, evals))
    noise.update({n: {"sigma_node": W.SIG, "delta_n": 0.002} for n in t1_nodes})
    t1 = B.Tier1(suites=dict(t1_nodes), modes=("none",))
    primary, _ = B.build(srcs, preds, noise, t0_nodes=B.SEVEN_T0, t1=t1)
    return srcs, preds, noise, t1, primary


@pytest.fixture(scope="module")
def world():
    return _world()


class Recorder:
    def __init__(self):
        self.inputs = []

    def __call__(self, gi):
        self.inputs.append(gi)
        return {"schema": F.SCHEMA, "iqm_undefined": None, "nodes": {}, "ineligible_nodes": {},
                "node_poi": {n["node"]: {"A3": 0.5, "A5": 0.5} for n in gi["nodes"]}}


def _shifted(preds):
    out = copy.deepcopy(preds)
    for a in out:
        for pid in out[a]:
            p = np.array(out[a][pid])[::-1]
            out[a][pid] = (p / p.sum()).tolist()
    return out


def test_a_node_subset_build_equals_the_full_build_with_repeats_across_instances_and_sources(world):
    srcs, preds, noise, t1, _ = copy.deepcopy(world)
    node = "openml_sonar"                     # repeats: a test proposal repeats a sweep-1 train key and a dev key
    test_rows = [r for r in srcs[0].rows if r["node"] == node and W.ASSIGN[r["instance"]]["split"] == "test"]
    dev_row = next(r for r in srcs[0].rows if r["node"] == node and W.ASSIGN[r["instance"]]["split"] == "dev")
    s1_row = next(r for r in srcs[1].rows if r["node"] == node and W.ASSIGN[r["instance"]]["split"] == "train")
    test_rows[4]["incumbent_hash"], test_rows[4]["candidate_hash"] = dev_row["incumbent_hash"], dev_row["candidate_hash"]
    test_rows[5]["incumbent_hash"], test_rows[5]["candidate_hash"] = s1_row["incumbent_hash"], s1_row["candidate_hash"]
    full, rep = B.build(srcs, preds, noise, t0_nodes=B.SEVEN_T0, t1=t1)
    assert rep["nodes"][node]["repeats_dropped_test"] == 2
    for nodes in (["digits_mlp"], [node, "tabular_mlp"], ["mlgym_fmnist"], ["mlab_cifar10", "autoresearch_fixedtokens"]):
        sub, srep = F.fold_input(srcs, preds, noise, nodes=nodes, t1=t1)
        assert sorted(n["node"] for n in sub["nodes"]) == sorted(nodes)
        assert sub["t0_nodes"] == sorted(n for n in nodes if n in G.T0_NODES)
        for n in sub["nodes"]:
            assert n == next(m for m in full["nodes"] if m["node"] == n["node"])
        if node in nodes:
            assert srep["nodes"][node]["repeats_dropped_test"] == 2


def test_leave_one_suite_out_uses_each_folds_arms_on_its_suite_only(world):
    srcs, preds, noise, t1, primary = world
    folds = {s: preds for s in G.SUITES}
    folds["MLGym"] = _shifted(preds)
    rec = Recorder()
    out = F.leave_one_suite_out(srcs, noise, folds, primary_input=primary, primary_t0=B.SEVEN_T0, t1=t1, statistics=rec)
    assert [sorted(n["node"] for n in gi["nodes"]) for gi in rec.inputs] == [
        sorted(n for n, s in SUITE_NODES.items() if s == suite) for suite in G.SUITES]
    assert all(gi["t0_nodes"] == [] for gi in rec.inputs)
    mlgym = rec.inputs[list(G.SUITES).index("MLGym")]["nodes"][0]
    base = next(n for n in primary["nodes"] if n["node"] == "mlgym_fmnist")
    assert mlgym["test"]["A3"] != base["test"]["A3"]                    # the fold's own arms
    assert mlgym["test"]["A2"] == base["test"]["A2"] and mlgym["test"]["oracle"] == base["test"]["oracle"]
    assert out["schema"] == F.SCHEMA and set(out["folds"]) == set(G.SUITES)


def test_leave_one_suite_out_stops_before_any_statistic_without_a_labelled_node_per_suite():
    rec = Recorder()
    srcs, preds, noise, t1, primary = _world({k: v for k, v in SUITE_NODES.items() if v != "autoresearch"})
    with pytest.raises(F.FoldStop, match="autoresearch"):
        F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, primary_input=primary, primary_t0=B.SEVEN_T0, t1=t1, statistics=rec)
    # a frozen node whose test rows are missing is not in the primary input: its suite has no labelled node
    srcs, preds, noise, t1, _ = _world()
    gone = {r["proposal_id"] for r in srcs[2].rows if r["node"] == "mlgym_fmnist"
            and W.ASSIGN[r["instance"]]["split"] == "test"}
    W._drop(srcs[2], gone)
    primary, rep = B.build(srcs, preds, noise, t0_nodes=B.SEVEN_T0, t1=t1)
    assert rep["t1_not_supplied"] == {"mlgym_fmnist": ["test"]}
    with pytest.raises(F.FoldStop, match="MLGym"):
        F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, primary_input=primary, primary_t0=B.SEVEN_T0, t1=t1, statistics=rec)
    assert rec.inputs == []


def test_folds_are_bound_to_the_primary_input_and_built_before_any_statistic(world):
    srcs, preds, noise, t1, primary = world
    rec = Recorder()
    other = copy.deepcopy(primary)
    other["nodes"][-1]["test"]["A2"][0] += 1.0                          # last T0 node: a different primary input
    with pytest.raises(F.FoldInputError, match="differs from the primary input"):
        F.leave_one_node_out(srcs, noise, {n: preds for n in B.SEVEN_T0}, primary_input=other, primary_t0=B.SEVEN_T0, statistics=rec)
    assert rec.inputs == []                                              # no statistic before the failing fold
    with pytest.raises(F.FoldInputError, match="T0 set"):
        F.leave_one_node_out(srcs, noise, {}, primary_input=primary, primary_t0=["digits_mlp"], statistics=rec)
    with pytest.raises(F.FoldInputError, match="no fold arms"):
        F.leave_one_node_out(srcs, noise, {}, primary_input=primary, primary_t0=B.SEVEN_T0, statistics=rec)
    with pytest.raises(F.FoldInputError, match="primary_input"):
        F.secondary_runs(srcs, preds, noise, primary_input={"schema": "x"}, primary_t0=B.SEVEN_T0, t1=t1, statistics=rec)
    with pytest.raises(F.FoldInputError, match="frozen T1 setting"):
        F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, primary_input=primary, primary_t0=B.SEVEN_T0,
                              t1=B.Tier1(suites={"mlab_cifar10": "MLGym"}, modes=("none",)), statistics=rec)


def test_leave_one_node_out_and_secondary_runs_route_correctly(world):
    srcs, preds, noise, t1, primary = world
    rec = Recorder()
    out = F.leave_one_node_out(srcs, noise, {n: preds for n in B.SEVEN_T0}, primary_input=primary, primary_t0=B.SEVEN_T0, statistics=rec)
    assert sorted(out["folds"]) == sorted(B.SEVEN_T0)
    assert [gi["t0_nodes"] for gi in rec.inputs] == [[n] for n in sorted(B.SEVEN_T0)]
    rec = Recorder()
    out = F.secondary_runs(srcs, preds, noise, primary_input=primary, primary_t0=B.SEVEN_T0, t1=t1, statistics=rec)
    assert list(out["runs"]) == ["g_0.05", "g_0.2", "mode_append_only_summary", "mode_none"]
    assert [out["runs"][k]["builder_report"]["g_units"] for k in ("g_0.05", "g_0.2")] == [0.05, 0.2]
    nodes = {k: sorted(n["node"] for n in gi["nodes"]) for k, gi in zip(out["runs"], rec.inputs)}
    assert "mlab_cifar10" in nodes["mode_none"] and "mlab_cifar10" not in nodes["mode_append_only_summary"]


@pytest.mark.skipif(not PINNED, reason="gate v3.1 runs only under NumPy 2.4.4")
def test_fold_statistics_are_the_gates_without_holm_and_report_poi_when_the_iqm_is_undefined(world):
    srcs, preds, noise, t1, primary = world
    st = F.fold_statistics(primary)
    gate_out = G.evaluate(primary)
    assert st["schema"] == F.SCHEMA and st["gate_schema"] == G.OUTPUT_SCHEMA and st["descriptive"] is True
    banned = {"verdict", "first_ranked_arm", "rank", "tested", "passed", "level", "meets_practical_size",
              "ranking_p_iqm", "ranking_p_poi", "ranking_p_composite"}

    def keys(x):
        return set(x) | {k for v in x.values() if isinstance(v, dict) for k in keys(v)} if isinstance(x, dict) else set()
    assert not banned & keys(st)
    for arm in G.ARMS:                     # the same point statistics; bounds at both levels, one of them the gate's
        assert st["arms"][arm]["iqm_gap_closed"] == gate_out["arms"][arm]["iqm_gap_closed"]
        assert st["probability_of_improvement"][arm] == gate_out["arms"][arm]["probability_of_improvement"]
        lv = f"{gate_out['arms'][arm]['level']:g}"
        assert st["arms"][arm]["lower_bounds"][lv]["lower_iqm_gap_closed"] == gate_out["arms"][arm]["lower_iqm_gap_closed"]
        assert st["arms"][arm]["lower_bounds"][lv]["lower_probability_of_improvement"] == \
            gate_out["arms"][arm]["lower_probability_of_improvement"]
        assert set(st["arms"][arm]["lower_bounds"]) == {"0.975", "0.95"}
    assert st["tier_descriptive"] == gate_out["tier_descriptive"] and st["node_counts"] == gate_out["node_counts"]
    loso = F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, primary_input=primary, primary_t0=B.SEVEN_T0, t1=t1)
    undefined = {s for s, f in loso["folds"].items() if f["statistics"]["iqm_undefined"]}
    assert undefined == {"MLGym"} and loso["folds"]["MLGym"]["statistics"]["arms"] is None
    assert loso["folds"]["MLGym"]["statistics"]["node_fields"]["mlgym_fmnist"]["n_test"] == 6
    for s, f in loso["folds"].items():
        assert set(f["statistics"]["probability_of_improvement"]) == set(G.ARMS)   # PoI reported in every fold
        assert f["statistics"]["declared_t0_nodes"] == []
    lono = F.leave_one_node_out(srcs, noise, {n: preds for n in B.SEVEN_T0}, primary_input=primary, primary_t0=B.SEVEN_T0)
    for node, f in lono["folds"].items():
        t = next(n for n in primary["nodes"] if n["node"] == node)["test"]
        a, d = np.array(t["A3"]) - np.array(t["A2"]), np.array(t["oracle"]) - np.array(t["A2"])
        assert f["held_out"]["iqm_undefined"] is None
        assert f["held_out"]["gap_closed_A3"] == pytest.approx(a.mean() / d.mean(), abs=1e-12)
        assert f["held_out"]["poi_A3"] == pytest.approx(gate_out["nodes"][node]["poi_A3"], abs=0)


def test_wrong_primary_or_noise_is_an_input_refusal(world):
    srcs, preds, noise, t1, primary = world
    rec = Recorder()
    sens, _ = B.build(srcs, preds, noise, t0_nodes=B.ALL_T0, t1=t1)
    with pytest.raises(F.FoldInputError, match="arms-frozen record"):       # the sensitivity input cannot stand in
        F.leave_one_node_out(srcs, noise, {n: preds for n in B.ALL_T0}, primary_input=sens,
                             primary_t0=B.SEVEN_T0, statistics=rec)
    bad_noise = {**noise, "digits_mlp": {"sigma_node": W.SIG, "delta_n": 99.0}}
    with pytest.raises(F.FoldInputError, match="delta_n differs"):
        F.leave_one_node_out(srcs, bad_noise, {n: preds for n in B.SEVEN_T0}, primary_input=primary,
                             primary_t0=B.SEVEN_T0, statistics=rec)
    with pytest.raises(F.FoldInputError, match="not a valid gate input"):
        F.leave_one_node_out(srcs, noise, {}, primary_input={"schema": G.INPUT_SCHEMA}, primary_t0=B.SEVEN_T0,
                             statistics=rec)
    assert rec.inputs == []
