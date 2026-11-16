"""C3 arms and offline evaluation on synthetic proposals. ENGINEERING_ONLY; AI-assisted (Claude)."""
import numpy as np
import pytest

from r1.c3 import offline_eval as OE
from r1.c3.arms import ConstantPrior, LGBMPrior, RulesPrior, prior_moments
from r1.c3.features import FEATURES
from r1.c3.labels import soft_label

NOISE = {n: {"delta_n": 0.002} for n in ("nodeA", "nodeB", "nodeC")}


def synth(n_inst=12, per=20, seed=0):
    """Edit key 1 is harmful (z = -2), key 2 helpful (z = +1), key 3 no-ops (Delta = 0)."""
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
                f["active_equals_incumbent"] = float(inert)
                delta = 0.0 if inert else (-2.0 if key == 1 else 1.0) * sig + rng.normal(0, 0.2 * sig)
                dhat = 0.0 if inert else delta + rng.normal(0, sig)
                rows.append({"proposal_id": f"{node}:{i}:{t}", "node": node, "instance": f"{node}__s{i}",
                             "instance_seed": i, "features": f, "inert": inert, "sigma_node": sig, "sigma_cmp": sig,
                             "delta_hat": dhat, "delta_true": delta, "weight": 1.0, "eval_weight": 1.0,
                             "soft": soft_label(None if inert else delta, 0.1 * sig, sig, inert=inert, sigma_mode="se_audit")})
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
    res = OE.evaluate(rows, "instance", 3, g_values=(OE.G_PRIMARY,), noise=NOISE)
    gate = OE.gate_verdict(res)
    assert gate["verdict"] == "NOT_AVAILABLE" and "pass" not in gate
    for x in res["values"]["0.1"]["A3_minus_A2"].values():
        assert x["gain_per20"] > 0 and x["ci95"][0] > 0
    # A2 skips all inert proposals at g > 0
    assert res["values"]["0.1"]["arms"]["A2"]["nodeA"]["exec_rate"] < 0.8
    lono = OE.evaluate(rows, "lono", g_values=(OE.G_PRIMARY,), noise=NOISE)
    assert set(lono["values"]["0.1"]["A3_minus_A2"]) == {"nodeA", "nodeB", "nodeC"}


def test_no_gain_when_nothing_is_learnable():
    pytest.importorskip("lightgbm")
    rows = synth()
    rng = np.random.default_rng(5)
    for r in rows:
        r["features"]["key_code"] = int(rng.integers(1, 4)) if not r["inert"] else 3
        r["features"]["key_code"] = 9 if not r["inert"] else 3
    res = OE.evaluate(rows, "instance", 3, g_values=(OE.G_PRIMARY,), noise=NOISE)
    for x in res["values"]["0.1"]["A3_minus_A2"].values():
        assert abs(x["gain_per20"]) < 0.05
    assert OE.gate_verdict(res)["verdict"] == "NOT_AVAILABLE"


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_declared_g_values_only_and_single_gate():
    """Declared g values remain; the superseded per-node gate is unavailable."""
    pytest.importorskip("lightgbm")
    assert OE.G_PRIMARY == 0.1 and OE.G_SENSITIVITY == (0.05, 0.2) and OE.G_EVAL == (0.1, 0.05, 0.2)
    rows = synth(n_inst=6, per=10)
    with pytest.raises(ValueError, match="not a declared value"):
        OE.evaluate(rows, "instance", 3, g_values=(0.0,), noise=NOISE)
    with pytest.raises(ValueError, match="not a declared value"):
        OE.evaluate(rows, "instance", 3, g_values=(0.3,), noise=NOISE)
    res = OE.evaluate(rows, "instance", 3, noise=NOISE)
    assert sorted(res["values"]) == ["0.05", "0.1", "0.2"]
    assert {v["role"] for k, v in res["values"].items()} == {"primary", "sensitivity"}
    assert res["values"]["0.1"]["role"] == "primary"
    # no verdict anywhere in the evaluation itself
    assert not {"pass", "gate_pass", "verdict", "meets_node_criterion"} & set(_keys(res))
    sens = OE.sensitivity_view(res)
    assert not {"pass", "gate_pass", "verdict", "meets_node_criterion"} & set(_keys(sens))
    # theory checks may use g = 0, labelled; they carry no verdict either
    assert "g = 0" in res["theory_checks"]["note"]
    assert OE.gate_verdict(OE.evaluate(rows, "instance", 3, g_values=(0.05,), noise=NOISE))["verdict"] == "NOT_AVAILABLE"
    assert res["run_accounting"]["primary"]["name"] == "skip_credited_at_g"


def test_freed_run_accounting():
    """Freed runs credited with the arm's mean reward per executed proposal (exchangeability)."""
    r = np.array([0.5, -0.1, 0.0, 0.0])
    ex = np.array([True, True, False, False])
    w = np.ones(4)
    assert OE.freed_run_value(r, ex, w) == pytest.approx(0.2)
    # an arm that executes everything: freed-run value equals the primary mean
    assert OE.freed_run_value(r, np.ones(4, bool), w) == pytest.approx(r.mean())
    # an arm that executes nothing frees runs it cannot spend: value 0
    assert OE.freed_run_value(r, np.zeros(4, bool), w) == 0.0
    # weighted
    assert OE.freed_run_value(np.array([1.0, 0.0]), np.array([True, True]), np.array([3.0, 1.0])) == pytest.approx(0.75)
    # call-cap value: c = 1 is the primary (W x mean reward per logged proposal), c = inf is W x m
    sr, se, sw = float((w * ex * r).sum()), float((w * ex).sum()), float(w.sum())
    assert OE.capped_value(sr, se, sw, 1.0) == pytest.approx(20 * r.mean())
    assert OE.capped_value(sr, se, sw, float("inf")) == pytest.approx(20 * 0.2)
    # e = 0.5, c = 2: min(W, 0.5 * 2 * W) = W runs at m = 0.2
    assert OE.capped_value(sr, se, sw, 2.0) == pytest.approx(20 * 0.2)
    # e = 0.25, c = 2: min(W, 0.5 W) = 10 runs at m = 0.5
    ex1 = np.array([True, False, False, False])
    assert OE.capped_value(0.5, 1.0, 4.0, 2.0) == pytest.approx(10 * 0.5)
    assert OE.capped_value(0.0, 0.0, 4.0, 2.0) == 0.0
    # capped bootstrap is exact for identical clusters
    r2, ex2 = np.tile(r, 2), np.tile(ex, 2).astype(float)
    cl = np.array([0] * 4 + [1] * 4)
    for c in (1.0, 2.0, float("inf")):
        d = OE.cluster_boot_capped_diff(r2, ex2, r2, np.ones(8), np.ones(8), cl, c, n=50)
        exp = OE.capped_value(0.8, 4.0, 8.0, c) - OE.capped_value(0.8, 8.0, 8.0, c)
        assert np.allclose(d, exp)


def test_freed_run_sensitivity_reported_next_to_primary():
    pytest.importorskip("lightgbm")
    rows = synth(n_inst=6, per=10)
    res = OE.evaluate(rows, "instance", 3, g_values=(OE.G_PRIMARY,), noise=NOISE)
    v = res["values"]["0.1"]
    assert set(OE.RUN_ACCOUNTING["sensitivity"]["call_caps_reported"]) == {"2", "inf"}
    for node, fr in v["freed_run_sensitivity"]["A3_minus_A2"].items():
        a3 = v["freed_run_sensitivity"]["arms"]["A3"][node]["mean_per_executed"]
        a2 = v["freed_run_sensitivity"]["arms"]["A2"][node]["mean_per_executed"]
        assert fr["by_call_cap"]["inf"]["gain_per20"] == pytest.approx(20 * (a3 - a2))
        assert fr["primary_gain_per20"] == pytest.approx(v["A3_minus_A2"][node]["gain_per20"])
        for cap in ("2", "inf"):
            x = fr["by_call_cap"][cap]
            assert x["ci95"][0] - 1e-12 <= x["gain_per20"] <= x["ci95"][1] + 1e-12
        # per-arm call-cap values are consistent with the node-level difference
        for cap in ("2", "inf"):
            d = (v["freed_run_sensitivity"]["arms"]["A3"][node]["per_campaign_by_call_cap"][cap]
                 - v["freed_run_sensitivity"]["arms"]["A2"][node]["per_campaign_by_call_cap"][cap])
            assert fr["by_call_cap"][cap]["gain_per20"] == pytest.approx(d)
    # A0 executes everything: its freed-run value equals its primary per-proposal mean
    for node, x in v["arms"]["A0"].items():
        assert v["freed_run_sensitivity"]["arms"]["A0"][node]["mean_per_executed"] == pytest.approx(x["mean_per_proposal"])


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


def test_duplicates_are_skipped_by_rules_not_labelled_zero():
    """A duplicate (known, negative result) gets no label; A2+ skip it; A1 may run it."""
    rows = synth()
    rng = np.random.default_rng(7)
    extra = []
    for r in rows[:60]:
        d = dict(r, features=dict(r["features"]))
        d["proposal_id"] = r["proposal_id"] + ":dup"
        d["features"]["active_equals_incumbent"] = 0.0
        d["features"]["active_seen_before"] = 1.0
        d.update(noop=False, duplicate=True, inert=False, soft=None, weight=0.0,
                 delta_hat=-abs(rng.normal(0.01, 0.003)), delta_true=-0.01)
        extra.append(d)
    rows2 = rows + extra
    a2 = RulesPrior().fit(rows2)
    assert np.allclose(a2.predict(rows)[:5].sum(1), 1.0)
    ex, kp, _ = OE.decisions(a2.predict(rows2), rows2, 0.0, rule_layer=True)
    dup = np.array([r.get("duplicate", False) for r in rows2])
    assert not ex[dup].any() and not kp[dup].any()
    p1 = ConstantPrior().fit(rows2).predict(rows2)
    assert np.allclose(p1[:len(rows)], ConstantPrior().fit(rows).predict(rows))  # duplicates excluded from fitting
