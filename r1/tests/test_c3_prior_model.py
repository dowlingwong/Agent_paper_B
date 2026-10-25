"""RUNBOOK Track H.1: the ``PriorModel`` protocol and the wrapped arms. ENGINEERING_ONLY; AI-assisted (Claude).

Acceptance: A1-A3 wrapped as ``PriorModel`` reproduce the ``offline_eval``
numbers on the 19 Oct pilot table exactly (every value of ``evaluate`` and the
gate, instance and leave-one-node-out splits).  The committed
``offline_eval.json`` of that table predates the 22 Oct g / run-accounting
schema, so the comparison is against today's ``offline_eval`` run on the same
proposals and audits.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from r1.c3 import offline_eval as OE
from r1.c3.arms import ConstantPrior, LGBMPrior, RulesPrior, prior_moments
from r1.c3.labels import N_BINS
from r1.c3.prior_model import (FixedPrior, Forecast, IsotonicMap, ManagerQuestionPrior, TableArmPrior, offline_arm,
                               parse_typed_answer, typed_to_bins)
from r1.harness import REPO

PILOT_TABLE = REPO / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
needs_table = pytest.mark.skipif(not (PILOT_TABLE / "audits.jsonl").exists(), reason="19 Oct pilot table not present")
WRAPPED = {a: offline_arm(a) for a in ("A1", "A2", "A3")}


def _dump(x):
    return json.dumps(x, sort_keys=True, default=str)


@needs_table
@pytest.mark.parametrize("mode", ["instance", "lono"])
def test_wrapped_arms_reproduce_offline_eval_exactly(mode):
    pytest.importorskip("lightgbm")
    rows = OE.assemble(PILOT_TABLE)
    assert len(rows) > 600
    ref = OE.evaluate(rows, mode, 3)
    new = OE.evaluate(rows, mode, 3, arms=WRAPPED)
    assert _dump(new) == _dump(ref)
    if mode == "instance":
        assert _dump(OE.gate_verdict(new)) == _dump(OE.gate_verdict(ref))
    # and the held-out distributions themselves are bit-identical
    p_ref = OE.crossfit(rows, mode, 3)
    p_new = OE.crossfit(rows, mode, 3, WRAPPED)
    for a in p_ref:
        assert np.array_equal(p_ref[a], p_new[a])


@needs_table
def test_forecast_moments_equal_the_offline_moments():
    pytest.importorskip("lightgbm")
    rows = OE.assemble(PILOT_TABLE)
    for name, cls in (("A1", ConstantPrior), ("A2", RulesPrior), ("A3", LGBMPrior)):
        arm = cls().fit(rows)
        prior = TableArmPrior(arm, name)
        P = arm.predict(rows)
        pi, mu, tau = prior_moments(P, rows)
        for i in range(0, len(rows), 37):
            f = prior.forecast(rows[i])
            assert f.probs == tuple(P[i]) and f.version.startswith(name) and len(f.digest) == 64
            assert f.moments(rows[i]["sigma_node"]) == (pi[i], mu[i], tau[i])
        assert prior.rule_layer == (name != "A1")


def test_forecast_validation():
    Forecast(probs=(1.0,) + (0.0,) * 11, version="v", digest="d", latency_s=0.0)
    for bad in ((0.5,) * 12, (1.0,) * 3, (float("nan"),) + (0.0,) * 11, (-0.1, 1.1) + (0.0,) * 10):
        with pytest.raises(ValueError):
            Forecast(probs=bad, version="v", digest="d", latency_s=0.0)


def test_typed_answers_map_to_bins():
    p = typed_to_bins(0.25, 1.0, "large")
    assert math.isclose(p[0], 0.25) and math.isclose(sum(p), 1.0) and sum(p[1:6]) == 0.0
    assert p[9] > p[8] > 0 and p[11] > 0
    q = typed_to_bins(0.0, 0.0, "small")
    assert math.isclose(q[5], 0.8 * 1.0) and math.isclose(q[6], 0.2)  # (-0.5,-0.15] and the central bin
    assert parse_typed_answer('ok {"p_no_effect": 0.1, "p_positive": 0.7, "size": "Medium"}')["size"] == "medium"
    for bad in ("no json", '{"p_no_effect": 2, "p_positive": 0.5, "size": "small"}',
                '{"p_no_effect": 0.1, "p_positive": 0.5, "size": "huge"}'):
        with pytest.raises(ValueError):
            parse_typed_answer(bad)


def test_a4_calls_the_injected_client_once_and_calibrates():
    prompts = []

    def fake_llm(prompt):
        prompts.append(prompt)
        return '{"p_no_effect": 0.6, "p_positive": 0.9, "size": "small"}'

    fallback = FixedPrior(np.ones(N_BINS), "A1")
    row = {"node": "digits_mlp", "features": {"key_code": 3}, "edit": {"symbol": "ALPHA", "old": "1e-4", "new": "1e-3"}}
    a4 = ManagerQuestionPrior(fake_llm, fallback)
    f = a4.forecast(row)
    assert f.llm_calls == 1 and f.fallback is None and len(prompts) == 1 and "ALPHA" in prompts[0]
    assert math.isclose(f.probs[0], 0.6)
    cal = IsotonicMap().fit({"p_no_effect": [0.0, 0.6, 1.0], "p_positive": [0.0, 1.0]},
                            {"p_no_effect": [0.0, 0.1, 0.2], "p_positive": [0.0, 1.0]})
    g = ManagerQuestionPrior(fake_llm, fallback, cal).forecast(row)
    assert math.isclose(g.probs[0], 0.1) and g.digest != f.digest
    broken = ManagerQuestionPrior(lambda p: "I think it helps", fallback).forecast(row)
    assert broken.llm_calls == 1 and broken.fallback.startswith("a4_answer_failed")
    assert broken.probs == fallback.forecast(row).probs
