"""D.3 arm EGATE (pre-declaration revision 4 §5.5; gap G4). Synthetic runs only. AI-assisted (Claude)."""
from __future__ import annotations

import dataclasses
import json

import pytest

from r1.baselines.responses import PaceStyleGate
from r1.c3 import accounting as A
from r1.c3 import d3_replicate as R
from r1.c3.d3_controllers import D3_RULE_LAYER

BASE = 0.90


class Script:
    """metric(config, j) = base(config) + small seed effect; failures by (role, config, j)."""

    def __init__(self, level, fail=()):
        self.level, self.fail, self.calls = level, set(fail), []

    def __call__(self, *, role, config_sha256, seed, j):
        self.calls.append((role, config_sha256, seed, j))
        if (role, config_sha256, j) in self.fail:
            return R.RunOutcome(False)
        return R.RunOutcome(True, self.level[config_sha256] + 1e-4 * ((j * 7) % 3))


def _engine():
    return R.EgateEngine(6201)


def _after_first(level, fail=(), W=20):
    run, c, e = Script(level, fail), A.ChargedRunCounter(W=W), _engine()
    assert e.step("c0", run, c).decision == "kept"
    return run, c, e


def test_declared_gate_and_rule_layer():
    assert D3_RULE_LAYER["EGATE"] is False
    e = _engine()
    assert (e.gate.alpha, e.gate.clip, e.gate.max_pairs) == (0.1, 0.05, 8) and e.action_version == "verify:pace"
    assert e.seeds == (6201, 6501, 6502, 6503, 6504, 6505, 6506, 6507)
    with pytest.raises(ValueError, match="as on main"):
        R.EgateEngine(6201, gate=PaceStyleGate(clip=0.02))


def test_first_valid_trial_is_kept_after_one_run():
    run, c, e = _after_first({"c0": BASE})
    assert c.used == 1 and run.calls == [("candidate", "c0", 6201, 0)] and e.incumbent == "c0"


def test_commit_at_seven_pairs_needs_d_at_least_0_0468_and_costs_14_runs_with_the_first_trial():
    run, c, e = _after_first({"c0": BASE, "up": BASE + 0.0469})
    s = e.step("up", run, c)
    assert s.decision == "kept" and s.detail["pairs"] == 7 and s.detail["reason"] == "commit"
    assert c.used == 14 and e.incumbent == "up"
    # pair j >= 1 ran the incumbent too (it had only its j = 0 run); j = 0 was reused, not charged
    inc = [x for x in s.replicates if x["role"] == "incumbent"]
    assert [(x["j"], x["charged"]) for x in inc] == [(0, False)] + [(j, True) for j in range(1, 7)]


@pytest.mark.parametrize("d,decision,pairs", [(0.0391, "kept", 8), (0.038, "discarded", 8)])
def test_eight_pair_threshold_matches_the_declared_computation(d, decision, pairs):
    run, c, e = _after_first({"c0": BASE, "x": BASE + d})
    s = e.step("x", run, c)
    assert s.decision == decision and s.detail["pairs"] == pairs
    assert s.detail["reason"] == ("commit" if decision == "kept" else "max_pairs")
    assert c.used == 1 + 8 + 7


def test_decisions_equal_pace_style_gate_on_the_recorded_differences():
    run, c, e = _after_first({"c0": BASE, "x": BASE + 0.045})
    s = e.step("x", run, c)
    gate = PaceStyleGate().decide(s.detail["diffs"])
    assert gate[0] == ("commit" if s.decision == "kept" else "reject") and gate[2] == s.detail["pairs"]


def test_after_one_full_test_the_rest_cannot_commit_and_the_campaign_ends_at_w():
    configs = ["c0", "flat", "flat2", "flat3"]
    run = Script({"c0": BASE, "flat": BASE + 0.001, "flat2": BASE + 0.002, "flat3": BASE})
    out = R.run_replicate_campaign(_engine(), configs, run)
    steps = out["steps"]
    assert [s.decision for s in steps] == ["kept", "discarded", "discarded"]
    assert steps[1].detail["reason"] == "max_pairs" and steps[1].runs_charged == 15
    # the incumbent now has runs at j = 0..7: each later pair costs one run; 4 runs fund 4 pairs, then discard
    assert steps[2].detail["reason"] == "unfundable_pair" and steps[2].detail["pairs"] == 4
    assert steps[2].runs_charged == 4 and all(not x["charged"] for x in steps[2].replicates if x["role"] == "incumbent")
    assert out["counter"].used == 20 and out["ended_on"] == "worker_runs"


def test_a_step_that_cannot_fund_its_first_pair_is_refused_before_it_starts():
    run, c, e = _after_first({"c0": BASE, "x": BASE}, W=1)
    with pytest.raises(A.UnfundableStep):
        e.step("x", run, c)
    assert c.used == 1


def test_failed_candidate_is_failed_invalid_charged_for_the_runs_used():
    run, c, e = _after_first({"c0": BASE, "bad": BASE + 0.1}, fail={("candidate", "bad", 3)})
    s = e.step("bad", run, c)
    assert s.decision == "failed_invalid" and s.detail["failed_at_j"] == 3
    assert s.runs_charged == 4 + 2 and c.used == 1 + 6  # candidates j = 0..3, incumbents j = 1..2
    assert e.incumbent == "c0"


def test_failed_first_trial_makes_the_next_proposal_the_first_trial():
    run, c, e = Script({"bad": BASE, "c1": BASE}, fail={("candidate", "bad", 0)}), A.ChargedRunCounter(W=20), _engine()
    assert e.step("bad", run, c).decision == "failed_invalid" and e.incumbent is None
    assert e.step("c1", run, c).decision == "kept" and c.used == 2


def test_failed_incumbent_run_discards_is_charged_and_never_rerun():
    run, c, e = _after_first({"c0": BASE, "x": BASE + 0.1, "y": BASE + 0.1}, fail={("incumbent", "c0", 2)})
    s = e.step("x", run, c)
    assert s.decision == "discarded" and s.detail["reason"] == "incumbent_failed"
    assert c.used == 1 + 3 + 2 and c.lookup("c0", 6502).success is False
    s2 = e.step("y", run, c)  # reaches pair j = 2 again: ends there, the failed run is not repeated
    assert s2.decision == "discarded" and s2.detail["reason"] == "incumbent_failed_earlier"
    assert [x for x in run.calls if x[0] == "incumbent" and x[3] == 2] == [("incumbent", "c0", 6502, 2)]
    assert ("candidate", "y", 6502, 2) not in run.calls
    assert s2.runs_charged == 2  # candidates j = 0, 1; incumbent runs reused


def test_a_kept_candidate_brings_its_own_runs_as_the_new_incumbent():
    run, c, e = _after_first({"c0": BASE, "up": BASE + 0.0469, "next": BASE + 0.0469 + 0.06,
                              "next8": BASE + 0.0469 + 0.06 + 0.0391}, W=60)
    e.step("up", run, c)  # kept at 7 pairs: "up" has runs at j = 0..6
    used = c.used
    s = e.step("next", run, c)  # d > clip on every pair: commits at exactly 7 pairs, all incumbent runs reused
    assert s.decision == "kept" and s.detail["pairs"] == 7
    assert [x["j"] for x in s.replicates if x["role"] == "incumbent" and x["charged"]] == []
    assert c.used - used == s.runs_charged == 7
    s8 = e.step("next8", run, c)  # "next" has runs at j = 0..6: an 8-pair test charges the incumbent at j = 7 only
    assert s8.decision == "kept" and s8.detail["pairs"] == 8
    assert [x["j"] for x in s8.replicates if x["role"] == "incumbent" and x["charged"]] == [7]


class Flat:
    """metric(config) with no seed effect, so paired differences are exact."""

    def __init__(self, level):
        self.level, self.calls = level, []

    def __call__(self, *, role, config_sha256, seed, j):
        self.calls.append((role, config_sha256, seed, j))
        return R.RunOutcome(True, self.level[config_sha256])


@pytest.mark.parametrize("d,decision,pairs", [(0.0468, "kept", 7), (0.0467, "kept", 8), (0.039, "kept", 8),
                                              (0.0389, "discarded", 8)])
def test_declared_boundaries_exactly(d, decision, pairs):
    run, c, e = Flat({"c0": 0.0, "x": d}), A.ChargedRunCounter(W=20), _engine()
    e.step("c0", run, c)
    s = e.step("x", run, c)
    assert s.detail["diffs"] == [d] * pairs and s.decision == decision and s.detail["pairs"] == pairs


def test_a_candidate_identical_to_the_incumbent_reuses_its_own_runs():
    run, c, e = Flat({"c0": 0.9}), A.ChargedRunCounter(W=20), _engine()
    e.step("c0", run, c)
    s = e.step("c0", run, c)
    assert s.decision == "discarded" and s.detail["reason"] == "max_pairs" and s.runs_charged == 8
    assert not [x for x in run.calls if x[0] == "incumbent"]
    assert all(not x["charged"] for x in s.replicates if x["role"] == "incumbent") and c.used == 9


def test_only_the_repository_gate_is_accepted():
    @dataclasses.dataclass(frozen=True)
    class Imitation(PaceStyleGate):
        pass
    with pytest.raises(ValueError, match="as on main"):
        R.EgateEngine(6201, gate=Imitation())


def test_minimised_metrics_are_oriented():
    run, c = Script({"c0": 0.5, "lower": 0.5 - 0.05}), A.ChargedRunCounter(W=20)
    e = R.EgateEngine(6201, maximize=False)
    e.step("c0", run, c)
    assert e.step("lower", run, c).decision == "kept"


def test_replicate_entries_feed_campaign_usage(tmp_path):
    configs = ["c0", "x", "y"]
    run = Script({"c0": BASE, "x": BASE + 0.001, "y": BASE + 0.1}, fail={("incumbent", "c0", 5)})
    out = R.run_replicate_campaign(_engine(), configs, run)
    rows = [{"budget_index": b + 1, "worker_mode": "w", "extra": {"control": {"replicates": s.replicates}}}
            for b, s in enumerate(out["steps"])]
    (tmp_path / "t.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp_path / "e.jsonl").write_text("")
    u = A.campaign_usage(tmp_path / "t.jsonl", tmp_path / "e.jsonl", arm="EGATE", instance="i", information_set="s",
                         worker_run_cap=20, llm_call_cap=80, manager_deterministic=True)
    assert u.worker_runs == out["counter"].used
    assert u.replicate_runs_reused == sum(1 for s in out["steps"] for x in s.replicates if not x["charged"])
