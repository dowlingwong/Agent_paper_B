"""RUNBOOK Track H.3/H.6: the RuleController through the harness decide(). ENGINEERING_ONLY; AI-assisted (Claude).

Acceptance (H.3): A1 through ``RuleController`` equals the index-policy arm on a
scripted campaign (same E1 decisions, same keep threshold and decisions), and
the online decisions equal the offline ``offline_eval.decisions`` of the A1 arm
on the replayed ledger.  E1 and E2 use one forecast; decision events record the
forecast and the rule quantities; rule skips come first and are logged as such.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from r1.c3 import offline_eval as OE
from r1.c3 import rules
from r1.c3.arms import ConstantPrior
from r1.c3.control import RuleController
from r1.c3.features import replay_campaign
from r1.c3.prior_model import FixedPrior, ManagerQuestionPrior, TableArmPrior
from r1.tests.c3_campaign_fixtures import (IndexPolicyReference, SequenceBackend, node_context, run_campaign)

from r1.headroom.scripted_manager import ScriptedRandomManager
from autoresearch.control_plane.action_versions import KEEP_RULE_BAYES, ActionVersions, KeepPrior
from autoresearch.control_plane.budget import ComputeBudget

SIGMA = 0.005
# A1-like constant priors: "gain" executes everything with a positive keep threshold; "nogain" skips.
GAIN = np.array([0.30, 0.02, 0.03, 0.08, 0.15, 0.17, 0.10, 0.06, 0.05, 0.02, 0.01, 0.01])
NOGAIN = np.array([0.30, 0.20, 0.20, 0.15, 0.10, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0])


def a1_prior(p):
    arm = ConstantPrior()
    arm.pooled = np.asarray(p, float) / np.sum(p)
    arm.by_node = {"digits_mlp": arm.pooled}
    return TableArmPrior(arm, "A1")


def _strip(rows):
    """Decision, metric, delta and the keep threshold where the rule applied (trial 1 keeps its first metric)."""
    out = []
    for r in rows:
        rule = r["extra"].get("keep_rule") or {}
        out.append((r["budget_index"], r["decision"], r["parsed_metrics"], r["delta_vs_best"],
                    rule.get("threshold") if rule.get("applied") else None))
    return out


@pytest.mark.parametrize("probs,expect_execute", [(GAIN, True), (NOGAIN, False)])
def test_a1_through_rule_controller_equals_the_index_policy(tmp_path, probs, expect_execute):
    prior = a1_prior(probs)
    ctx = node_context(SIGMA)
    f = prior.forecast({"node": "digits_mlp", "features": {}})
    pi, mu, tau = f.moments(SIGMA)
    assert bool(rules.execute(pi, mu, tau, SIGMA, 0.1 * SIGMA)) is expect_execute
    if expect_execute:
        assert rules.bayes_threshold(mu, tau, SIGMA) > 0  # the keep rule differs from rho
    ctl = RuleController(prior, ctx)
    assert not ctl.rule_layer  # A1 has no rule layer
    budget, seed, scale = 16, 127, 0.004
    a, a_ev, a_rows, _ = run_campaign(tmp_path / "a", ScriptedRandomManager("digits_mlp", seed=seed, repetition=0),
                                      budget=budget, scale=scale, **ctl.campaign_kwargs())
    ref_prior = KeepPrior(mu=mu, tau=tau, sigma=SIGMA, source="constant")
    b, _, b_rows, _ = run_campaign(tmp_path / "b", ScriptedRandomManager("digits_mlp", seed=seed, repetition=0),
                                   budget=budget, scale=scale, controller=IndexPolicyReference(expect_execute),
                                   action_versions=ActionVersions.new_campaign(keep_rule=KEEP_RULE_BAYES),
                                   keep_prior=ref_prior, skip_display="one_line/v1")
    assert _strip(a_rows) == _strip(b_rows)
    decisions = [r["decision"] for r in a_rows]
    if expect_execute:
        assert "skipped" not in decisions and "discarded" in decisions and "kept" in decisions[1:]
        # the threshold actually bites: some positive delta was discarded
        assert any(r["decision"] == "discarded" and (r["delta_vs_best"] or 0) > 0 for r in a_rows)
    else:
        assert decisions[0] == "kept" and set(decisions[1:]) == {"skipped"}
        assert all(r["extra"]["control"]["skip_reason"] == "prior_no_gain" for r in a_rows[1:])
    # offline: the A1 arm's decisions (offline_eval.decisions, no rule layer) on the replayed ledger
    props, _ = replay_campaign(a_rows, ctx.start_files, "digits_mlp", "digits_mlp__s127", "t", "none", 20, SIGMA)
    if props:
        table = [{"node": p.node, "features": p.features, "sigma_node": SIGMA, "sigma_cmp": SIGMA,
                  "delta_hat": p.outcome["delta_hat"]} for p in props]
        P = np.array([prior.forecast(r).probs for r in table])
        ex, kp, _ = OE.decisions(P, table, OE.G_PRIMARY, rule_layer=False)
        assert ex.all()
        assert list(kp) == [p.outcome["decision"] == "kept" for p in props]


def test_one_forecast_serves_e1_and_e2_and_is_recorded(tmp_path):
    calls = []

    class Counting(FixedPrior):
        def forecast(self, row):
            calls.append(row["features"]["budget_index"])
            return super().forecast(row)

    prior = Counting(GAIN, "A5")
    ctl = RuleController(prior, node_context(SIGMA))
    _, events, rows, _ = run_campaign(tmp_path, ScriptedRandomManager("digits_mlp", seed=7, repetition=0),
                                      budget=10, **ctl.campaign_kwargs())
    e1 = {e["trial_id"]: e["payload"] for e in events
          if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"}
    executed = [r for r in rows if r["budget_index"] >= 2]
    assert sorted(calls) == [float(r["budget_index"]) for r in executed]  # one forecast per trial
    for r in executed:
        d = e1[r["trial_id"]]["detail"]
        for key in ("probs", "pi", "mu", "tau", "sigma", "t_star", "V", "g", "execute", "prior_version",
                    "prior_digest", "features_hash", "featurizer"):
            assert key in d, key
        prior_used = r["extra"]["keep_rule"]["prior"]
        assert (prior_used["mu"], prior_used["tau"], prior_used["sigma"]) == (d["mu"], d["tau"], d["sigma"])
        assert prior_used["source"].endswith(":e1_forecast")
        assert math.isclose(r["extra"]["keep_rule"]["threshold"], d["t_star"], rel_tol=0, abs_tol=0)
        assert d["g"] == 0.1 * SIGMA and len(d["probs"]) == 12


def test_rule_skips_come_first_and_are_logged(tmp_path):
    calls = []

    class Counting(FixedPrior):
        def forecast(self, row):
            calls.append(row["features"]["budget_index"])
            return super().forecast(row)

    edits = [("HIDDEN_UNITS", "32", "64"), ("ALPHA", "1e-4", "1e-3"), ("ALPHA", "1e-4", "1e-3"),
             ("MAX_ITER", "40", "80")]
    ctl = RuleController(Counting(GAIN, "A2"), node_context(SIGMA))
    assert ctl.rule_layer
    records, events, rows, worker = run_campaign(tmp_path, SequenceBackend(edits), budget=4, **ctl.campaign_kwargs())
    by_b = {r["budget_index"]: r for r in rows}
    if by_b[2]["decision"] == "discarded":
        assert by_b[3]["decision"] == "skipped"
        assert by_b[3]["extra"]["control"]["skip_reason"] == "rule_duplicate"
        assert 3.0 not in calls  # no forecast for a rule skip
        assert worker.runs == 3
    else:  # trial 2 kept: trial 3 is then stale (precondition) and nothing is asserted about rules
        pytest.skip("scripted metric kept trial 2")
    detail = [e["payload"]["detail"] for e in events if e["event_type"] == "control_decision"
              and e["payload"]["epoch"] == "E1" and e["trial_id"].endswith("003")][0]
    assert detail["rule"] == {"noop": False, "duplicate": True} and "probs" not in detail


def test_a4_queries_are_charged_to_the_llm_cap(tmp_path):
    n_calls = []

    def fake_llm(prompt):
        n_calls.append(1)
        return '{"p_no_effect": 0.1, "p_positive": 0.6, "size": "medium"}'

    fallback = a1_prior(GAIN)
    ctl = RuleController(ManagerQuestionPrior(fake_llm, fallback), node_context(SIGMA), fallback=fallback)
    cap = 3
    _, events, rows, _ = run_campaign(tmp_path, ScriptedRandomManager("digits_mlp", seed=3, repetition=0), budget=8,
                                      compute_budget=ComputeBudget(max_llm_calls=cap), **ctl.campaign_kwargs())
    decisions = [e["payload"] for e in events if e["event_type"] == "control_decision"]
    charged = sum(d["llm_calls"] for d in decisions)
    assert len(n_calls) == charged == cap  # the deterministic proposer is free; A4 spends the cap exactly
    fallbacks = [d["detail"]["fallback"] for d in decisions if d["epoch"] == "E1" and "detail" in d
                 and "fallback" in d["detail"]]
    assert fallbacks.count("llm_cap_exhausted") == len(rows) - 1 - cap


def test_skip_infeasible_and_no_features_continue():
    from types import SimpleNamespace
    ctl = RuleController(FixedPrior(NOGAIN, "A3"), node_context(SIGMA))
    view = SimpleNamespace(epoch="E1", budget_index=1, ledger_prefix=(), current_best=None, budget={},
                           proposal=SimpleNamespace(extra={"structured_edit": {"symbol": "ALPHA", "old": "1e-4",
                                                                               "new": "1e-3", "path": "train.py"}},
                                                    proposal_summary="s"),
                           input_hash=lambda: "h")
    d = ctl.decide(view, {"continue": True, "skip": True})
    assert d.action == "continue" and d.detail["reason"] == "no_features"
    kp = ctl.keep_prior(SimpleNamespace(**{**view.__dict__, "epoch": "E2"}))
    assert kp.source.endswith("no_features")
