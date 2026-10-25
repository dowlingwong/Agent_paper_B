"""RUNBOOK Track H.6/H.7: direct-action arms through the same decide(), the hybrid (proposal), and the
extended matching report (instances, W, LLM cap, information set). ENGINEERING_ONLY; AI-assisted (Claude)."""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from r1.branch.matching import ArmDescriptor, CampaignUsage, MatchingError, matching_report
from r1.c3.accounting import campaign_usage
from r1.c3.control import AWRDirectController, RuleController, fit_awr_direct
from r1.c3.features import FEATURES
from r1.c3.prior_model import FixedPrior
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.llm_control import LLMSelfController
from r1.tests.c3_campaign_fixtures import node_context, run_campaign

from autoresearch.control_plane.budget import ComputeBudget

SIGMA = 0.005
NOGAIN = np.array([0.30, 0.20, 0.20, 0.15, 0.10, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0])
INFO = "control_view/v1+node_context/v1"


class RevisingManager(ScriptedRandomManager):
    """A non-deterministic stand-in that accepts revision feedback (so the harness offers ``revise``)."""

    deterministic = False

    def propose_next_trial(self, status, memory_context, node_spec, revision_feedback=None, revision_attempt=None):
        if revision_feedback is None:
            return super().propose_next_trial(status, memory_context, node_spec)
        saved, self.repetition = self.repetition, 1000 + int(revision_attempt or 1)
        try:
            return super().propose_next_trial(status, memory_context, node_spec)
        finally:
            self.repetition = saved


class SecondForecastGains(FixedPrior):
    """No gain for the first forecast of a trial, gain for a second one (the revised proposal)."""

    GAIN = np.array([0.05, 0.0, 0.02, 0.05, 0.1, 0.18, 0.2, 0.2, 0.12, 0.05, 0.02, 0.01])

    def __init__(self):
        super().__init__(NOGAIN, "A3")
        self.seen = {}

    def forecast(self, row):
        b = row["features"]["budget_index"]
        self.seen[b] = self.seen.get(b, 0) + 1
        f = super().forecast(row)
        if self.seen[b] >= 2:
            return dataclasses.replace(f, probs=tuple(self.GAIN / self.GAIN.sum()))
        return f


@pytest.mark.parametrize("prior_kind,budget_n", [("nogain", 1), ("second_gains", 1), ("nogain", 0)])
def test_hybrid_revises_then_rescreens_once(tmp_path, prior_kind, budget_n):
    prior = FixedPrior(NOGAIN, "A3") if prior_kind == "nogain" else SecondForecastGains()
    ctl = RuleController(prior, node_context(SIGMA), hybrid_revise=True, revision_budget=budget_n)
    assert ctl.version.startswith("rule_controller_hybrid/v1") and ctl.rescreen_after_revise
    _, events, rows, _ = run_campaign(tmp_path, RevisingManager("digits_mlp", seed=9, repetition=0), budget=4,
                                      compute_budget=ComputeBudget(max_llm_calls=20), **ctl.campaign_kwargs())
    controls = [r["extra"].get("control") or {} for r in rows]
    e1 = [e for e in events if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"]
    t2 = [e["payload"] for e in e1 if e["trial_id"] == rows[1]["trial_id"]]
    if budget_n == 0:
        assert [r["decision"] for r in rows[1:]] == ["skipped"] * 3
        assert all("revision" not in c for c in controls)
        assert len(t2) == 1
    elif prior_kind == "nogain":
        # trial 2: revise, the revision is re-screened, still no gain -> skipped without a worker run
        assert rows[1]["decision"] == "skipped" and controls[1]["action"] == "skip"
        assert controls[1]["rescreened_after_revise"] and controls[1]["skip_reason"] == "prior_no_gain"
        assert "revision" in controls[1] and rows[1]["proposal_summary"] != controls[1]["revision"]["original"][
            "proposal_summary"]
        assert [p["action"] for p in t2] == ["revise", "skip"]
        assert t2[0]["detail"]["hybrid"] == "revise_instead_of_skip" and t2[1]["mask"]["revise"] is False
        assert [r["decision"] for r in rows[2:]] == ["skipped", "skipped"]  # revision budget spent
    else:
        # the revision is predicted to gain: it runs, and its E1 forecast serves the keep rule
        assert controls[1]["action"] == "revise" and rows[1]["decision"] in ("kept", "discarded")
        assert [p["action"] for p in t2] == ["revise", "continue"]
        assert rows[1]["extra"]["keep_rule"]["prior"]["source"].endswith(":e1_forecast")
    usage = campaign_usage(tmp_path / "trials.jsonl", tmp_path / "events.jsonl", arm="hybrid", instance="i",
                           information_set=INFO, worker_run_cap=None, llm_call_cap=20, manager_deterministic=False)
    assert usage.llm_calls == 4 + budget_n
    assert usage.worker_runs == 1 + (prior_kind == "second_gains")


def _awr_rows(n=200, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        f = {c: 0.0 for c in FEATURES}
        harmful = bool(rng.random() < 0.5)
        f["key_code"] = 1.0 if harmful else 2.0
        rows.append({"features": f, "sigma_node": SIGMA, "delta_hat": rng.normal(-0.01 if harmful else 0.01, 0.003),
                     "delta_label": -0.01 if harmful else 0.01})
    return rows


def test_awr_direct_arm_learns_to_skip_harmful_edits():
    model = fit_awr_direct(_awr_rows())
    from types import SimpleNamespace
    from r1.c3.control import feature_vector
    harm = {c: 0.0 for c in FEATURES} | {"key_code": 1.0}
    good = {c: 0.0 for c in FEATURES} | {"key_code": 2.0}
    p_h, p_g = model.proba(np.array([feature_vector(harm), feature_vector(good)]))
    assert p_h[1] > 0.5 > p_g[1]


def test_awr_training_never_reads_the_evaluation_half():
    rows = _awr_rows()
    base = fit_awr_direct(rows)
    poisoned = [dict(r, delta_true=(1.0 if r["delta_label"] < 0 else -1.0)) for r in rows]  # eval half, inverted
    fitted = fit_awr_direct(poisoned)
    for key in base.params:
        assert np.array_equal(base.params[key], fitted.params[key])
    with pytest.raises(ValueError, match="evaluation half"):
        fit_awr_direct(poisoned, value_key="delta_true")
    with pytest.raises(ValueError, match="without a finite"):
        fit_awr_direct([{k: v for k, v in r.items() if k != "delta_label"} for r in poisoned])
    with pytest.raises(ValueError, match="without a finite"):
        fit_awr_direct(rows + [dict(rows[0], delta_label=None)])


def test_awr_direct_and_llm_self_control_run_through_decide(tmp_path):
    rows = _awr_rows()
    for r in rows:  # make every edit look harmful so the arm skips
        r["delta_label"] = -0.01
    ctl = AWRDirectController(fit_awr_direct(rows), node_context(SIGMA))
    _, _, ledger, _ = run_campaign(tmp_path / "awr", ScriptedRandomManager("digits_mlp", seed=4, repetition=0),
                                   budget=3, controller=ctl)
    assert [r["decision"] for r in ledger] == ["kept", "skipped", "skipped"]
    assert ledger[1]["extra"]["control"]["skip_reason"] == "awr_direct"

    calls = []

    def fake_llm(prompt):
        calls.append(prompt)
        return '{"action": "skip", "scores": {"skip": 1.0}}' if "E1" in prompt.split("Decision epoch:")[1][:4] \
            else '{"action": "continue"}'

    llm = LLMSelfController(fake_llm)
    _, events, ledger, _ = run_campaign(tmp_path / "llm", ScriptedRandomManager("digits_mlp", seed=4, repetition=0),
                                        budget=3, controller=llm, compute_budget=ComputeBudget(max_llm_calls=4))
    usage = campaign_usage(tmp_path / "llm" / "trials.jsonl", tmp_path / "llm" / "events.jsonl", arm="llm_self",
                           instance="i", information_set=INFO, worker_run_cap=None, llm_call_cap=4,
                           manager_deterministic=True)
    assert usage.controller_llm_calls == len(calls) <= 4 and usage.llm_calls == usage.controller_llm_calls
    assert "skipped" in [r["decision"] for r in ledger]


def _desc(name, **kw):
    base = dict(name=name, family=name, information_set=INFO, spending_rule="c3_rules/v1", intervention_cap=None,
                compute_budget=20, llm_call_cap=40, tuning_budget=0, dev_instances="dev", instances="eval")
    base.update(kw)
    return ArmDescriptor(**base)


def _use(arm, inst, **kw):
    base = dict(arm=arm, instance=inst, information_set=INFO, worker_run_cap=20, llm_call_cap=40, worker_runs=20,
                llm_calls=30)
    base.update(kw)
    return CampaignUsage(**base)


def test_matching_report_checks_instances_w_llm_cap_and_information_set():
    arms = [_desc("A1"), _desc("A4"), _desc("hybrid")]
    usage = [_use(a, i) for a in ("A1", "A4", "hybrid") for i in ("s1", "s2")]
    rep = matching_report(arms, usage)
    assert rep["matched"] and rep["campaigns"]["arms"]["A4"]["W"] == 20 and "instances" in rep["matched_fields"]
    bad_cases = [
        [u if (u.arm, u.instance) != ("A4", "s2") else dataclasses.replace(u, instance="s3") for u in usage],
        [u if u.arm != "A4" else dataclasses.replace(u, worker_run_cap=21) for u in usage],
        [u if u.arm != "A4" else dataclasses.replace(u, llm_call_cap=41) for u in usage],
        [u if u.arm != "hybrid" else dataclasses.replace(u, information_set="other") for u in usage],
        [u if u.arm != "A4" else dataclasses.replace(u, llm_calls=41) for u in usage],
    ]
    for bad in bad_cases:
        with pytest.raises(MatchingError):
            matching_report(arms, bad)
    with pytest.raises(MatchingError):
        matching_report([_desc("A1"), _desc("A4", instances="other")])


def test_matching_report_without_new_fields_is_unchanged():
    a = ArmDescriptor("x", "rule", "Z", "r", None, None, None, 80, "dev")
    rep = matching_report([a, dataclasses.replace(a, name="y")])
    assert rep["matched_fields"] == ["information_set", "spending_rule", "intervention_cap", "compute_budget",
                                     "llm_call_cap", "tuning_budget", "dev_instances"]
    assert all("instances" not in r for r in rep["arms"]) and "campaigns" not in rep
