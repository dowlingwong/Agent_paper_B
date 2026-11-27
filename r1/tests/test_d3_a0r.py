"""D.3 arm A0R (pre-declaration revision 4 §5.1b; gap G11). Synthetic campaigns only. AI-assisted (Claude).

A0R = the rule layer of A2 with the default keep rule (Delta_hat > 0), no screen, no forecast, no verify.
"""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from r1.c3 import d3_analysis as D3
from r1.c3 import d3_controllers as DC
from r1.c3.control import RuleController
from r1.c3.prior_model import FixedPrior
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.tests.c3_campaign_fixtures import SequenceBackend, node_context, run_campaign

from autoresearch.control_plane.action_versions import KEEP_RULE_DEFAULT, ActionVersions
from autoresearch.control_plane.controller import ContinueController

SIGMA = 0.005
# A2-like prior that executes every proposal the rule layer lets through (as in test_c3_rule_controller).
GAIN = np.array([0.30, 0.02, 0.03, 0.08, 0.15, 0.17, 0.10, 0.06, 0.05, 0.02, 0.01, 0.01])
DUP_EDITS = [("HIDDEN_UNITS", "32", "64"), ("ALPHA", "1e-4", "1e-3"), ("ALPHA", "1e-4", "1e-3"),
             ("MAX_ITER", "40", "80"), ("ALPHA", "1e-4", "1e-3")]


def _small(ctl, cap=8):
    return ctl.campaign_kwargs(d3=False, W=20, llm_cap=cap)


def test_rule_layer_table_is_the_declared_one():
    # pre-declaration revision 4 §5 table and key block "rule_layer_on" (§13 item 21, as built)
    assert DC.D3_RULE_LAYER == {"A0": False, "A0R": True, "A1": False, "A2": True, "FIXR3": False, "EGATE": False,
                                "LADDER": False, "A3": True, "A5": True, "A6": True}
    assert all(DC.D3_RULE_LAYER[a] == (a in D3.RULE_LAYER_ARMS) for a in DC.D3_ARMS)
    assert (DC.D3_W, DC.D3_LLM_CALL_CAP) == (20, 80)
    with pytest.raises(ValueError, match="differs from the declared"):
        DC.RuleLayerController(node_context(SIGMA), arm="A0R", rule_layer=False)
    with pytest.raises(ValueError, match="differs from the declared"):
        DC.RuleLayerController(node_context(SIGMA), arm="LADDER", rule_layer=True)
    with pytest.raises(ValueError, match="not a D.3 arm"):
        DC.RuleLayerController(node_context(SIGMA), arm="A9", rule_layer=True)


def test_campaign_kwargs_bind_w_and_the_cap_with_the_default_keep_rule():
    ctl = DC.a0r_controller(node_context(SIGMA))
    kw = ctl.campaign_kwargs()
    assert kw["controller"] is ctl and kw["skip_display"] == "one_line/v1"
    assert "keep_prior" not in kw and "verify_runs" not in kw
    av = kw["action_versions"]
    assert av.keep_rule == KEEP_RULE_DEFAULT and av.verify_split_policy == "vary" and not av.needs_prior
    cb = kw["compute_budget"]
    assert (cb.max_worker_runs, cb.max_llm_calls, kw["budget"]) == (20, 80, 80)
    with pytest.raises(ValueError, match="fixed by the arm definition"):
        ctl.campaign_kwargs(keep_rule="bayes_threshold/v1")
    with pytest.raises(ValueError, match="fixed by the arm definition"):
        ctl.campaign_kwargs(verify_split_policy="fixed")
    for bad in ({"W": 10}, {"llm_cap": 40}, {"trials": 90}):
        with pytest.raises(ValueError, match="binds"):
            ctl.campaign_kwargs(**bad)
    assert ctl.campaign_kwargs(W=20, llm_cap=80, trials=80)["budget"] == 80  # the declared values are accepted
    with pytest.raises(ValueError):
        ctl.campaign_kwargs(d3=False, trials=40)  # a trial budget below the cap would bind (c3_budgets, D1)


def test_a0r_skips_duplicates_without_a_run_and_keeps_on_positive_delta(tmp_path):
    ctl = DC.a0r_controller(node_context(SIGMA))
    _, events, rows, worker = run_campaign(tmp_path, SequenceBackend(DUP_EDITS), **_small(ctl))
    skipped = [r for r in rows if r["decision"] == "skipped"]
    assert skipped, "the scripted sequence proposes duplicates"
    assert all(r["extra"]["control"]["skip_reason"] == "rule_duplicate" and r["worker_mode"] == "control_plane"
               for r in skipped)
    executed = [r for r in rows if r["worker_mode"] == "config_metric_worker"]
    assert worker.runs == len(executed)  # a skip costs no run
    for r in executed[1:]:
        assert (r["decision"] == "kept") == (r["delta_vs_best"] > 0)  # keep rule default/v1
        assert "keep_rule" not in r["extra"] or r["extra"]["keep_rule"].get("version") != "bayes_threshold/v1"
    e1 = [e["payload"] for e in events if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"]
    assert all(d["llm_calls"] == 0 for d in e1)  # no forecast, no controller call
    assert not [e for e in events if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E2"
                and e["payload"]["action"] != "continue"]  # no verify


class _Twin:
    """Delegates to A0R and asks A2's RuleController the same question on the same view and mask."""

    deterministic = True

    def __init__(self, ctx):
        self.a0r = DC.a0r_controller(ctx)
        self.a2 = RuleController(FixedPrior(GAIN, "A2"), ctx, verify=False)
        self.version, self.pairs = self.a0r.version, []

    def decide(self, view, mask):
        mine = self.a0r.decide(view, mask)
        if view.epoch == "E1" and view.proposal is not None:
            ref = self.a2.decide(view, mask)
            self.pairs.append((mine, ref))
        return mine


def _backend(name):
    return SequenceBackend(DUP_EDITS) if name == "dup" else ScriptedRandomManager("digits_mlp", seed=name,
                                                                                 repetition=0)


@pytest.mark.parametrize("backend", ["dup", 3, 11, 29])
def test_a0r_rule_layer_decides_exactly_as_a2s(tmp_path, backend):
    ctx = node_context(SIGMA)
    twin = _Twin(ctx)
    kw = _small(twin.a0r, cap=16)
    kw["controller"] = twin
    run_campaign(tmp_path, _backend(backend), **kw)
    assert twin.pairs
    if backend == "dup":
        assert any(mine.action == "skip" for mine, _ in twin.pairs)  # the rule layer was exercised
    for mine, ref in twin.pairs:
        ref_rule_skip = ref.action == "skip" and ref.detail.get("skip_reason") in ("rule_noop", "rule_duplicate")
        if ref_rule_skip:
            assert mine.action == "skip" and mine.detail["skip_reason"] == ref.detail["skip_reason"]
        else:
            assert mine.action == "continue"  # GAIN executes everything else; A0R has no screen
        if "rule" in ref.detail:
            assert mine.detail["rule"] == ref.detail["rule"] and mine.detail["features_hash"] == ref.detail[
                "features_hash"]


def _strip(rows):
    return [(r["budget_index"], r["decision"], r["parsed_metrics"], r["delta_vs_best"]) for r in rows]


@pytest.mark.parametrize("backend", ["dup", 5])
def test_a0r_equals_a0_until_its_first_rule_skip(tmp_path, backend):
    ctx = node_context(SIGMA)
    ctl = DC.a0r_controller(ctx)
    _, _, a_rows, _ = run_campaign(tmp_path / "a", _backend(backend), **_small(ctl, 16))
    kw = _small(ctl, 16)
    kw["controller"] = ContinueController()
    kw["action_versions"] = ActionVersions.new_campaign(keep_rule=KEEP_RULE_DEFAULT)
    _, _, b_rows, _ = run_campaign(tmp_path / "b", _backend(backend), **kw)
    first_skip = next((i for i, r in enumerate(a_rows) if r["decision"] == "skipped"), len(a_rows))
    assert first_skip >= 2 and _strip(a_rows[:first_skip]) == _strip(b_rows[:first_skip])
    if first_skip < len(a_rows):  # A0 executes what A0R skipped
        assert b_rows[first_skip]["decision"] != "skipped"


def test_rule_layer_off_never_skips_and_still_logs_the_flags(tmp_path):
    ctl = DC.RuleLayerController(node_context(SIGMA), arm="A0", rule_layer=False)
    _, _, rows, worker = run_campaign(tmp_path, SequenceBackend(DUP_EDITS), **_small(ctl))
    assert "skipped" not in [r["decision"] for r in rows]
    assert any(e.get("rule", {}).get("duplicate") for e in ctl.log)  # the duplicate was seen, and executed


def _view(epoch="E1", proposal=True):
    return SimpleNamespace(epoch=epoch, budget_index=4, proposal={} if proposal else None,
                           input_hash=lambda: "h")


@pytest.mark.parametrize("noop,dup,reason", [(True, False, "rule_noop"), (False, True, "rule_duplicate"),
                                             (True, True, "rule_noop")])
def test_noop_is_checked_before_duplicate_and_an_infeasible_skip_runs(monkeypatch, noop, dup, reason):
    fake = SimpleNamespace(noop=noop, duplicate=dup, features={"x": 1.0})
    monkeypatch.setattr(DC, "featurize_view", lambda view, ctx: fake)
    ctl = DC.a0r_controller(node_context(SIGMA))
    d = ctl.decide(_view(), {"skip": True})
    assert d.action == "skip" and d.detail["skip_reason"] == reason and d.llm_calls == 0
    d = ctl.decide(_view(), {"skip": False})
    assert d.action == "continue" and d.detail["skip_infeasible"] and d.detail["rule_decision"] == reason
    assert ctl.decide(_view("E2"), {"verify": True}).action == "continue"
    assert ctl.decide(_view("E0", proposal=False), {"stop": True}).action == "continue"


def test_unfeaturisable_proposal_runs(monkeypatch):
    def boom(view, ctx):
        raise RuntimeError("bad edit")
    monkeypatch.setattr(DC, "featurize_view", boom)
    d = DC.a0r_controller(node_context(SIGMA)).decide(_view(), {"skip": True})
    assert d.action == "continue" and d.detail["reason"].startswith("featurize_failed")
