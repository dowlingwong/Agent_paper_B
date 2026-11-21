"""Fold analyses (PRE-SECONDARY A): synthetic records only. Gate runs use the real gate v3.1 and are skipped unless
NumPy is the pinned 2.4.4; the structural tests use a recording stand-in for ``gate.evaluate``."""
import copy
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
                rows += [W._row(node, seed, "none", t, src="g5") for t in range(3, 7)]
    rng = np.random.default_rng(5)
    for r in rows:
        labels.append(W._label(r))
        if not r["noop"]:
            e = W._evaluation(r)
            e["delta_evaluation"] = labels[-1]["delta_label"]
            evals.append(e)
        for a in ("A3", "A5"):
            preds[a][r["proposal_id"]] = rng.dirichlet(np.ones(12)).tolist()
    srcs.append(B.Source("g5", rows, labels, evals))
    noise.update({n: {"sigma_node": W.SIG, "delta_n": 0.002} for n in t1_nodes})
    t1 = B.Tier1(suites=dict(SUITE_NODES), modes=("none",))
    return srcs, preds, noise, t1


@pytest.fixture(scope="module")
def world():
    return _world()


class Recorder:
    def __init__(self, stop=None):
        self.inputs, self.stop = [], stop

    def __call__(self, gi):
        self.inputs.append(gi)
        if self.stop:
            raise G.GateStop(self.stop)
        return {"verdict": "PASS", "first_ranked_arm": "A3", "nodes": {n["node"]: {"gap_closed_A3": 0.0}
                                                                          for n in gi["nodes"]},
                "arms": {a: {"rank": 1, "tested": True, "passed": True, "meets_practical_size": True,
                             "iqm_gap_closed": 0.0, "lower_iqm_gap_closed": -1.0} for a in G.ARMS}}


def _shifted(preds):
    out = copy.deepcopy(preds)
    for a in out:
        for pid in out[a]:
            p = np.array(out[a][pid])[::-1]
            out[a][pid] = (p / p.sum()).tolist()
    return out


def test_a_node_subset_build_equals_the_full_build_for_its_nodes(world):
    srcs, preds, noise, t1 = world
    full, _ = B.build(srcs, preds, noise, t0_nodes=B.SEVEN_T0, t1=t1)
    for nodes in (["digits_mlp"], ["openml_sonar", "tabular_mlp"], ["mlgym_fmnist"], ["mlab_cifar10"]):
        sub, _ = F.fold_input(srcs, preds, noise, nodes=nodes, t1=t1)
        assert sub["t0_nodes"] == sorted(n for n in nodes if n in G.T0_NODES)
        for n in sub["nodes"]:
            assert n == next(m for m in full["nodes"] if m["node"] == n["node"])


def test_leave_one_suite_out_uses_each_folds_arms_on_its_suite_only(world):
    srcs, preds, noise, t1 = world
    folds = {s: preds for s in G.SUITES}
    folds["MLGym"] = _shifted(preds)
    rec = Recorder()
    out = F.leave_one_suite_out(srcs, noise, folds, t1=t1, evaluate=rec)
    assert [sorted(n["node"] for n in gi["nodes"]) for gi in rec.inputs] == [
        sorted(n for n, s in SUITE_NODES.items() if s == suite) for suite in G.SUITES]
    assert all(gi["t0_nodes"] == [] for gi in rec.inputs)
    base, _ = F.fold_input(srcs, preds, noise, nodes=["mlgym_fmnist"], t1=t1)
    mlgym = rec.inputs[list(G.SUITES).index("MLGym")]["nodes"][0]
    assert mlgym["test"]["A3"] != base["nodes"][0]["test"]["A3"]          # the fold's own arms
    assert mlgym["test"]["A2"] == base["nodes"][0]["test"]["A2"]          # A2 and oracle are not fold arms
    assert mlgym["test"]["oracle"] == base["nodes"][0]["test"]["oracle"]
    for f in out["folds"].values():
        st = f["statistics"]
        assert st["descriptive"] is True and "verdict" not in st and "first_ranked_arm" not in st
        assert all(not ({"rank", "tested", "passed", "meets_practical_size"} & set(d)) for d in st["arms"].values())


def test_leave_one_suite_out_stops_before_any_statistic_without_a_labelled_node_per_suite():
    srcs, preds, noise, t1 = _world({k: v for k, v in SUITE_NODES.items() if v != "autoresearch"})
    rec = Recorder()
    with pytest.raises(F.FoldStop, match="autoresearch"):
        F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, t1=t1, evaluate=rec)
    assert rec.inputs == []
    srcs2, preds2, noise2, t1b = _world()
    srcs2[2].rows = [r for r in srcs2[2].rows if not (r["node"] == "mlgym_fmnist"
                                                     and W.ASSIGN[r["instance"]]["split"] == "dev")]
    keep = {r["proposal_id"] for r in srcs2[2].rows}
    srcs2[2].labels = [x for x in srcs2[2].labels if x["proposal_id"] in keep]
    srcs2[2].evaluations = [x for x in srcs2[2].evaluations if x["proposal_id"] in keep]
    with pytest.raises(F.FoldStop, match="MLGym"):               # frozen but not supplied (no dev instance)
        F.leave_one_suite_out(srcs2, noise2, {s: preds2 for s in G.SUITES}, t1=t1b, evaluate=rec)
    assert rec.inputs == []
    with pytest.raises(F.FoldStop, match="no fold arms"):
        F.leave_one_suite_out(srcs, noise, {"MLGym": preds}, t1=t1, evaluate=rec)


def test_leave_one_node_out_reports_gate_stops_per_fold(world):
    srcs, preds, noise, t1 = world
    rec = Recorder(stop="STOP: no node is IQM-eligible")
    out = F.leave_one_node_out(srcs, noise, {n: preds for n in B.SEVEN_T0}, primary_t0=B.SEVEN_T0, evaluate=rec)
    assert sorted(out["folds"]) == sorted(B.SEVEN_T0)
    assert all(f["gate_stop"].startswith("STOP") for f in out["folds"].values())
    assert [gi["t0_nodes"] for gi in rec.inputs] == [[n] for n in sorted(B.SEVEN_T0)]
    with pytest.raises(F.FoldStop, match="primary_t0"):
        F.leave_one_node_out(srcs, noise, {}, primary_t0=["digits_mlp"], evaluate=rec)
    with pytest.raises(F.FoldStop, match="no fold arms"):
        F.leave_one_node_out(srcs, noise, {}, primary_t0=B.SEVEN_T0, evaluate=rec)


def test_secondary_runs(world):
    srcs, preds, noise, t1 = world
    rec = Recorder()
    out = F.secondary_runs(srcs, preds, noise, primary_t0=B.SEVEN_T0, t1=t1, evaluate=rec)
    assert sorted(out["runs"]) == ["g_0.05", "g_0.2", "mode_append_only_summary", "mode_none"]
    assert [r["builder_report"]["g_units"] for r in out["runs"].values()][:2] == [0.05, 0.2]
    nodes = {k: sorted(n["node"] for n in gi["nodes"]) for k, gi in zip(out["runs"], rec.inputs)}
    assert "mlab_cifar10" in nodes["mode_none"] and "mlab_cifar10" not in nodes["mode_append_only_summary"]


@pytest.mark.skipif(not PINNED, reason="gate v3.1 runs only under NumPy 2.4.4")
def test_real_gate_folds_are_descriptive_and_match_the_gate_formula(world):
    srcs, preds, noise, t1 = world
    out = F.leave_one_node_out(srcs, noise, {n: preds for n in B.SEVEN_T0}, primary_t0=B.SEVEN_T0)
    for node, f in out["folds"].items():
        gi, _ = F.fold_input(srcs, preds, noise, nodes=[node])
        t = gi["nodes"][0]["test"]
        a, d = np.array(t["A3"]) - np.array(t["A2"]), np.array(t["oracle"]) - np.array(t["A2"])
        if "statistics" in f:
            assert f["held_out"]["gap_closed_A3"] == pytest.approx(a.mean() / d.mean(), abs=1e-12)
            assert "verdict" not in f["statistics"]
        else:
            assert "STOP" in f["gate_stop"]
    loso = F.leave_one_suite_out(srcs, noise, {s: preds for s in G.SUITES}, t1=t1)
    assert set(loso["folds"]) == set(G.SUITES)
    for f in loso["folds"].values():
        assert ("statistics" in f and f["statistics"]["protocol"]["declared_t0_nodes"] == []) or "gate_stop" in f
