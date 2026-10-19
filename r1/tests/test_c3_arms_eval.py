"""C3 arms and offline evaluation on synthetic proposals. ENGINEERING_ONLY; AI-assisted (Claude)."""
import numpy as np
import pytest

from r1.c3 import offline_eval as OE
from r1.c3.arms import ConstantPrior, LGBMPrior, RulesPrior, prior_moments
from r1.c3.features import FEATURES
from r1.c3.labels import soft_label

NOISE = {n: {"delta_n": 0.002} for n in ("nodeA", "nodeB", "nodeC")}


def synth(n_inst=12, per=20, seed=0):
    """Edit key 1 is harmful (z = -2), key 2 helpful (z = +1), key 3 inert duplicates."""
    rng = np.random.default_rng(seed)
    rows = []
    for node in ("nodeA", "nodeB", "nodeC"):
        sig = 0.01
        for i in range(n_inst):
            for t in range(per):
                key = int(rng.integers(1, 4))
                f = {c: 0.0 for c in FEATURES}
                f["key_code"] = key
                f["node_code"] = ("nodeA", "nodeB", "nodeC").index(node)
                inert = key == 3
                f["active_seen_before"] = float(inert)
                delta = 0.0 if inert else (-2.0 if key == 1 else 1.0) * sig + rng.normal(0, 0.2 * sig)
                dhat = 0.0 if inert else delta + rng.normal(0, sig)
                rows.append({"proposal_id": f"{node}:{i}:{t}", "node": node, "instance": f"{node}__s{i}",
                             "instance_seed": i, "features": f, "inert": inert, "sigma_node": sig, "sigma_cmp": sig,
                             "delta_hat": dhat, "delta_true": delta, "weight": 1.0, "eval_weight": 1.0,
                             "soft": soft_label(None if inert else delta, 0.1 * sig, sig, inert=inert)})
    return rows


def test_rules_prior_override_and_constant_prior():
    rows = synth()
    a1 = ConstantPrior().fit(rows).predict(rows)
    a2 = RulesPrior().fit(rows).predict(rows)
    inert = np.array([r["inert"] for r in rows])
    assert np.allclose(a2[inert, 0], 1.0) and np.allclose(a2[~inert, 0], 0.0)
    nodeA = np.array([r["node"] == "nodeA" for r in rows])
    assert np.allclose(a1[nodeA, 0], a1[nodeA][0, 0]) and 0.2 < a1[0, 0] < 0.45


def test_lgbm_learns_key_signal():
    pytest.importorskip("lightgbm")
    rows = synth()
    P = LGBMPrior().fit(rows).predict(rows)
    _, mu, _ = prior_moments(P, rows)
    keys = np.array([r["features"]["key_code"] for r in rows])
    assert mu[keys == 1].mean() < -0.01 and mu[keys == 2].mean() > 0.005


def test_evaluate_gate_detects_learnable_gain():
    pytest.importorskip("lightgbm")
    rows = synth()
    res = OE.evaluate(rows, "instance", 3, g_grid=(0.0, 0.1), noise=NOISE)
    g0 = res["per_g"]["0.1"]
    for node, gate in g0["gate"].items():
        assert gate["gain_A3_minus_A2_per20"] > 0 and gate["ci95"][0] > 0
    assert g0["gate_pass"]
    # A2 skips all inert proposals at g > 0
    assert g0["arms"]["A2"]["nodeA"]["exec_rate"] < 0.8
    lono = OE.evaluate(rows, "lono", g_grid=(0.0,), noise=NOISE)
    assert set(lono["per_g"]["0.0"]["gate"]) == {"nodeA", "nodeB", "nodeC"}


def test_no_gain_when_nothing_is_learnable():
    pytest.importorskip("lightgbm")
    rows = synth()
    rng = np.random.default_rng(5)
    for r in rows:
        r["features"]["key_code"] = int(rng.integers(1, 4)) if not r["inert"] else 3
        r["features"]["key_code"] = 9 if not r["inert"] else 3
    res = OE.evaluate(rows, "instance", 3, g_grid=(0.0,), noise=NOISE)
    for gate in res["per_g"]["0.0"]["gate"].values():
        assert abs(gate["gain_A3_minus_A2_per20"]) < 0.05


def test_cluster_bootstrap_constant_difference():
    d = np.full(30, 0.5)
    w = np.ones(30)
    cl = [i // 5 for i in range(30)]
    draws = OE.cluster_boot(d, w, cl, n=200)
    assert np.allclose(draws, 0.5)


def test_folds_by_instance_keep_instances_together():
    rows = synth(n_inst=6, per=3)
    f = OE.folds_by_instance(rows, 3)
    by_inst = {}
    for r, k in zip(rows, f):
        by_inst.setdefault(r["instance"], set()).add(int(k))
    assert all(len(v) == 1 for v in by_inst.values())
