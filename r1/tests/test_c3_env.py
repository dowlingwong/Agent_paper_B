"""RUNBOOK Track H.8: OfflineBanditEnv reproduces offline_eval's one-step values. ENGINEERING_ONLY; AI-assisted (Claude)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from r1.c3 import offline_eval as OE
from r1.c3.arms import LGBMPrior
from r1.c3.env import OfflineBanditEnv, evaluate_policy, label_rows, onehot
from r1.c3.labels import N_BINS
from r1.harness import REPO

PILOT_TABLE = REPO / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
needs_table = pytest.mark.skipif(not (PILOT_TABLE / "audits.jsonl").exists(), reason="19 Oct pilot table not present")


def _const(b):
    class Const:
        def fit(self, rows):
            return self

        def predict(self, rows):
            return np.tile(onehot(b), (len(rows), 1))
    return Const


class GreedyLGBM:
    """A3 cross-fitted, deployed as its mode bin (a non-constant fixed policy)."""

    def fit(self, rows):
        self.m = LGBMPrior().fit(rows)
        return self

    def predict(self, rows):
        return np.array([onehot(int(np.argmax(p))) for p in self.m.predict(rows)])


@pytest.fixture(scope="module")
def rows():
    if not (PILOT_TABLE / "audits.jsonl").exists():
        pytest.skip("19 Oct pilot table not present")
    return label_rows(PILOT_TABLE)


@needs_table
@pytest.mark.parametrize("b", [0, 3, 6, 8, 11])
@pytest.mark.parametrize("gu", OE.G_EVAL)
def test_constant_bin_policies_reproduce_offline_eval(rows, b, gu):
    res = OE.evaluate(rows, "instance", 3, g_values=(gu,), arms={a: _const(b) for a in ("A1", "A2", "A3")})
    for arm, rule_layer in (("A1", False), ("A2", True)):
        env = OfflineBanditEnv(rows, version="bin/v0", split="eval", g_units=gu, rule_layer=rule_layer, plugin="onehot_moments")
        got = evaluate_policy(env, lambda obs, info: b)
        ref = res["values"][str(gu)]["arms"][arm]
        assert set(got) == set(ref)
        for node in ref:
            assert got[node]["mean_per_proposal"] == pytest.approx(ref[node]["mean_per_proposal"], rel=1e-12, abs=1e-15)
            assert got[node]["exec_rate"] == pytest.approx(ref[node]["exec_rate"], rel=1e-12)


@needs_table
def test_a_learned_fixed_policy_reproduces_offline_eval(rows):
    pytest.importorskip("lightgbm")
    arms = {"A1": GreedyLGBM, "A2": GreedyLGBM, "A3": GreedyLGBM}
    res = OE.evaluate(rows, "instance", 3, g_values=(OE.G_PRIMARY,), arms=arms)
    preds = OE.crossfit(rows, "instance", 3, {"A3": GreedyLGBM})["A3"]
    index = {r["proposal_id"]: i for i, r in enumerate(rows)}
    env = OfflineBanditEnv(rows, version="bin/v0", split="eval", plugin="onehot_moments")
    got = evaluate_policy(env, lambda obs, info: int(np.argmax(preds[index[info["proposal_id"]]])))
    for node, ref in res["values"][str(OE.G_PRIMARY)]["arms"]["A3"].items():
        assert got[node]["mean_per_proposal"] == pytest.approx(ref["mean_per_proposal"], rel=1e-12, abs=1e-15)


@needs_table
def test_training_rewards_use_label_seeds_only(rows):
    env = OfflineBanditEnv(rows, version="bin/v0", split="label", plugin="greedy", tau_node={n: 1.0 for n in {r["node"] for r in rows}})
    assert all(r.get("delta_label") is not None for r in env.rows)
    assert not any(r.get("duplicate") for r in env.rows)  # duplicates carry no training label
    before = evaluate_policy(env, lambda obs, info: 8)
    scrambled = [dict(r, delta_true=r["delta_true"] + 1.0) for r in rows]  # evaluation seeds changed
    env2 = OfflineBanditEnv(scrambled, version="bin/v0", split="label", plugin="greedy", tau_node={n: 1.0 for n in {r["node"] for r in rows}})
    assert evaluate_policy(env2, lambda obs, info: 8) == before
    ev = OfflineBanditEnv(scrambled, version="bin/v0", split="eval", plugin="greedy", tau_node={n: 1.0 for n in {r["node"] for r in rows}})
    assert evaluate_policy(ev, lambda obs, info: 8) != evaluate_policy(
        OfflineBanditEnv(rows, version="bin/v0", split="eval", plugin="greedy", tau_node={n: 1.0 for n in {r["node"] for r in rows}}),
        lambda obs, info: 8)
    # label and evaluation halves differ on audited rows
    audited = [r for r in rows if r.get("delta_label") is not None and not r.get("noop")]
    assert any(r["delta_label"] != r["delta_true"] for r in audited)


def test_gym_api_shapes():
    f = {c: 0.0 for c in __import__("r1.c3.features", fromlist=["FEATURES"]).FEATURES}
    row = {"proposal_id": "p", "node": "n", "features": f, "sigma_node": 0.01, "sigma_cmp": 0.01, "delta_hat": 0.02,
           "delta_true": 0.01, "delta_label": 0.015, "weight": 1.0, "eval_weight": 1.0, "noop": False,
           "duplicate": False}
    env = OfflineBanditEnv([row], version="bin/v0", plugin="greedy", tau_node={"n": 1.0})
    obs, info = env.reset(seed=0)
    assert obs.shape == (len(f),) and info["proposal_id"] == "p"
    obs2, r, term, trunc, step_info = env.step(9)  # bin (1, 2]: mu = 1.5 sigma, executes, keeps Delta_hat = 2 sigma
    assert term and not trunc and step_info["execute"] and step_info["keep"]
    assert math.isclose(r, 0.015 - 0.1 * 0.01)
    env.reset()
    _, r0, *_ = env.step(0)  # the no-op bin: pi = 1, never executed
    assert r0 == 0.0
    with pytest.raises(RuntimeError):
        env.step(0)
    with pytest.raises(ValueError):
        OfflineBanditEnv([row], version="bin/v0", plugin="greedy", tau_node={"n": 1.0}, g_units=0.3)  # undeclared g
    with pytest.raises(ValueError):
        env.reset()
        env.step(N_BINS)
