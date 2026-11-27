"""D.3 arm LADDER (pre-declaration revision 4 §5.6; gap G5). Synthetic campaigns only. AI-assisted (Claude)."""
from __future__ import annotations

import pytest

from r1.c3 import d3_controllers as DC
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.tests.c3_campaign_fixtures import SequenceBackend, node_context, run_campaign

from autoresearch.control_plane.action_versions import KEEP_RULE_BAYES, KEEP_RULE_DEFAULT, ActionVersions
from autoresearch.control_plane.controller import ContinueController

SIGMA = 0.005
DUP_EDITS = [("HIDDEN_UNITS", "32", "64"), ("ALPHA", "1e-4", "1e-3"), ("ALPHA", "1e-4", "1e-3"),
             ("MAX_ITER", "40", "80"), ("ALPHA", "1e-4", "1e-3")]


def _rows(tmp, ctl, seed=5, backend=None, cap=16):
    kw = ctl.campaign_kwargs(d3=False, W=20, llm_cap=cap)
    b = backend or ScriptedRandomManager("digits_mlp", seed=seed, repetition=0)
    return run_campaign(tmp, b, **kw)


def test_grid_and_eta():
    assert len(DC.LADDER_GRID) == 121 and DC.LADDER_GRID[0] == -3.0 and DC.LADDER_GRID[-1] == 3.0
    assert 0.0 in DC.LADDER_GRID and 0.05 in DC.LADDER_GRID and -2.95 in DC.LADDER_GRID
    assert DC.ladder_eta(0.5, 0.01) == 0.005
    for bad in (0.07, 3.05, -3.5):
        with pytest.raises(ValueError, match="grid"):
            DC.ladder_eta(bad, 0.01)
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="sigma_node"):
            DC.ladder_eta(0.5, bad)


@pytest.mark.parametrize("c", DC.LADDER_GRID)
def test_keep_threshold_is_exactly_eta_on_the_whole_grid(c):
    for sigma in (0.0036, 0.005, 0.046, 0.0123456789):
        ctl = DC.ladder_controller(node_context(sigma), c=c)
        assert ctl.keep_prior(None).threshold == ctl.eta == c * sigma


def test_rule_layer_off_as_built_and_switch_is_checked():
    assert DC.D3_RULE_LAYER["LADDER"] is False
    assert DC.LadderController(node_context(SIGMA), c=0.2).rule_layer is False
    with pytest.raises(ValueError, match="differs from the declared"):
        DC.LadderController(node_context(SIGMA), c=0.2, rule_layer=True)
    for bad in (float("nan"), 0.07, 3.05):  # eta only from a grid value: an off-grid eta is impossible
        with pytest.raises(ValueError, match="grid"):
            DC.LadderController(node_context(SIGMA), c=bad)
    with pytest.raises(TypeError):
        DC.LadderController(node_context(SIGMA), eta=0.001)


def test_campaign_kwargs():
    ctl = DC.LadderController(node_context(SIGMA), c=0.4)
    kw = ctl.campaign_kwargs()
    assert kw["action_versions"].keep_rule == KEEP_RULE_BAYES and kw["keep_prior"].threshold == ctl.eta == 0.4 * SIGMA
    assert (kw["compute_budget"].max_worker_runs, kw["compute_budget"].max_llm_calls, kw["budget"]) == (20, 80, 80)
    assert "verify_runs" not in kw and kw["skip_display"] == "one_line/v1"
    with pytest.raises(ValueError, match="fixed by the arm definition"):
        ctl.campaign_kwargs(keep_rule=KEEP_RULE_DEFAULT)
    with pytest.raises(ValueError, match="fixed by the arm definition"):
        ctl.campaign_kwargs(verify_split_policy="fixed")
    with pytest.raises(ValueError, match="binds"):
        ctl.campaign_kwargs(W=10)


@pytest.mark.parametrize("c", [0.4, -0.4, 0.1])
def test_keep_iff_delta_hat_above_eta_and_every_proposal_runs(tmp_path, c):
    ctl = DC.LadderController(node_context(SIGMA), c=c)
    eta = ctl.eta
    _, events, rows, worker = _rows(tmp_path, ctl, seed=9)
    assert "skipped" not in [r["decision"] for r in rows]
    for r in rows[1:]:
        if r["delta_vs_best"] is None:
            continue
        rule = r["extra"]["keep_rule"]
        assert rule["applied"] and rule["threshold"] == eta
        assert (r["decision"] == "kept") == (r["delta_vs_best"] > eta)
    assert not [e for e in events if e["event_type"] == "control_decision" and e["payload"]["action"] == "verify"]


@pytest.mark.parametrize("c,seed,bites", [(0.8, 1, "positive_delta_discarded"), (-0.4, 9, "nonpositive_kept")])
def test_the_threshold_bites_where_a0_would_decide_otherwise(tmp_path, c, seed, bites):
    ctl = DC.LadderController(node_context(SIGMA), c=c)
    eta = ctl.eta
    _, _, rows, _ = _rows(tmp_path, ctl, seed=seed)
    compared = [r for r in rows[1:] if r["delta_vs_best"] is not None]
    if bites == "positive_delta_discarded":
        assert any(r["decision"] == "discarded" and 0 < r["delta_vs_best"] <= eta for r in compared)
    else:
        assert any(r["decision"] == "kept" and eta < r["delta_vs_best"] <= 0 for r in compared)


def test_duplicates_are_executed(tmp_path):
    ctl = DC.LadderController(node_context(SIGMA), c=0.0)
    _, _, rows, worker = _rows(tmp_path, ctl, backend=SequenceBackend(DUP_EDITS), cap=8)
    assert "skipped" not in [r["decision"] for r in rows]
    assert any(e.get("rule", {}).get("duplicate") for e in ctl.log)


@pytest.mark.parametrize("seed", [5, 9, 13])
def test_eta_zero_reproduces_a0s_decisions(tmp_path, seed):
    ctl = DC.ladder_controller(node_context(SIGMA), c=0.0)
    _, _, a, _ = _rows(tmp_path / "a", ctl, seed=seed)
    kw = ctl.campaign_kwargs(d3=False, W=20, llm_cap=16)
    kw.pop("keep_prior")
    kw["controller"] = ContinueController()
    kw["action_versions"] = ActionVersions.new_campaign(keep_rule=KEEP_RULE_DEFAULT)
    _, _, b, _ = run_campaign(tmp_path / "b", ScriptedRandomManager("digits_mlp", seed=seed, repetition=0), **kw)
    strip = [(r["budget_index"], r["decision"], r["parsed_metrics"], r["delta_vs_best"]) for r in a]
    assert strip == [(r["budget_index"], r["decision"], r["parsed_metrics"], r["delta_vs_best"]) for r in b]
