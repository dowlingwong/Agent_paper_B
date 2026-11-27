"""D.3 arm FIXR3 (pre-declaration revision 4 §5.4; gap G3). Synthetic runs only. AI-assisted (Claude)."""
from __future__ import annotations

import json

import pytest
from scipy import stats

from r1.c3 import accounting as A
from r1.c3 import d3_replicate as R
from r1.c3.d3_controllers import D3_RULE_LAYER


class Script:
    """A deterministic run function: metric(config, seed) from a table; failures by (config, j)."""

    def __init__(self, metrics, fail=()):
        self.metrics, self.fail, self.calls = metrics, set(fail), []

    def __call__(self, *, role, config_sha256, seed, j):
        self.calls.append((role, config_sha256, seed, j))
        if (config_sha256, j) in self.fail:
            return R.RunOutcome(False)
        m = self.metrics[config_sha256]
        return R.RunOutcome(True, m[j] if isinstance(m, (list, tuple)) else m + 0.001 * j)


def test_declared_constants_and_rule_layer():
    assert (R.FIXR3_R, R.FIXR3_ALPHA) == (3, 0.05)
    assert D3_RULE_LAYER["FIXR3"] is False
    with pytest.raises(ValueError, match="declared"):
        R.Fixr3Engine(6201, r=4)
    with pytest.raises(ValueError, match="declared"):
        R.Fixr3Engine(6201, alpha=0.1)


def test_replicate_seeds_follow_section_4_1():
    assert [R.replicate_seed(6201, j) for j in range(3)] == [6201, 6501, 6502]
    assert R.replicate_seed(6218, 2) == 6672 and R.replicate_seed(6218, 9) == 6679
    assert [R.replicate_seed(6301, j) for j in (0, 1, 9)] == [6301, 6311, 6319]
    assert R.replicate_seed(6302, 1) == 6321
    for bad in ((6200, 0), (6200, 1), (6201, 10), (6201, -1)):
        with pytest.raises(ValueError):
            R.replicate_seed(*bad)


@pytest.mark.parametrize("cand,inc", [([0.91, 0.93, 0.92], [0.90, 0.905, 0.899]),
                                      ([0.5, 0.6, 0.7], [0.55, 0.55, 0.56]),
                                      ([0.80, 0.80, 0.80], [0.70, 0.75, 0.72])])
@pytest.mark.filterwarnings("ignore:Precision loss occurred:RuntimeWarning")  # scipy, on the zero-variance side
def test_welch_equals_scipy(cand, inc):
    got = R.welch_one_sided(cand, inc)
    ref = stats.ttest_ind(cand, inc, equal_var=False, alternative="greater")
    assert got["p"] == pytest.approx(ref.pvalue, rel=1e-12) and got["t"] == pytest.approx(ref.statistic, rel=1e-12)


def test_first_trial_is_run_three_times_and_kept_without_a_test():
    run = Script({"c1": 0.9})
    c = A.ChargedRunCounter(W=20)
    s = R.Fixr3Engine(6203).step("c1", run, c)
    assert s.decision == "kept" and s.detail["test"] is None and s.detail["first_trial"]
    assert run.calls == [("candidate", "c1", 6203, 0), ("candidate", "c1", 6521, 1), ("candidate", "c1", 6522, 2)]
    assert c.used == 3 and [r.kind for r in c.runs] == ["trial", "replicate", "replicate"]
    assert [e["j"] for e in s.replicates] == [1, 2] and all(e["charged"] for e in s.replicates)
    assert s.display_metric == pytest.approx((0.9 + 0.901 + 0.902) / 3)


def test_keep_iff_welch_rejects_and_the_incumbent_is_never_rerun():
    run = Script({"c0": [0.90, 0.905, 0.899], "up": [0.95, 0.96, 0.955], "flat": [0.90, 0.91, 0.895]})
    c = A.ChargedRunCounter(W=20)
    e = R.Fixr3Engine(6201)
    e.step("c0", run, c)
    s_flat = e.step("flat", run, c)
    assert s_flat.decision == "discarded" and s_flat.detail["test"]["p"] > 0.05
    s_up = e.step("up", run, c)
    assert s_up.decision == "kept" and s_up.detail["test"]["p"] <= 0.05 and e.incumbent == "up"
    assert all(role == "candidate" for role, *_ in run.calls)  # FIXR3 never runs an incumbent replicate
    assert c.used == 9


def test_zero_variance_on_both_sides_is_no_keep_and_counted():
    run = Script({"c0": [0.9, 0.9, 0.9], "c1": [0.95, 0.95, 0.95]})
    c = A.ChargedRunCounter(W=20)
    e = R.Fixr3Engine(6201)
    e.step("c0", run, c)
    s = e.step("c1", run, c)
    assert s.decision == "discarded" and s.detail["test"]["zero_variance"] and e.zero_variance_cases == 1


@pytest.mark.parametrize("j", [0, 1, 2])
def test_any_failed_replicate_is_failed_invalid_charged_for_the_runs_used(j):
    run = Script({"c0": [0.9, 0.91, 0.89], "bad": 0.99}, fail={("bad", j)})
    c = A.ChargedRunCounter(W=20)
    e = R.Fixr3Engine(6201)
    e.step("c0", run, c)
    s = e.step("bad", run, c)
    assert s.decision == "failed_invalid" and s.runs_charged == j + 1 and c.used == 3 + j + 1
    assert len([x for x in run.calls if x[1] == "bad"]) == j + 1  # the remaining replicates are not run
    assert e.incumbent == "c0"


def test_a_failed_first_trial_makes_the_next_proposal_the_first_trial():
    run = Script({"bad": 0.9, "c1": 0.5}, fail={("bad", 2)})
    c = A.ChargedRunCounter(W=20)
    e = R.Fixr3Engine(6201)
    assert e.step("bad", run, c).decision == "failed_invalid" and e.incumbent is None
    s = e.step("c1", run, c)
    assert s.decision == "kept" and s.detail["first_trial"] and s.detail["test"] is None


def test_at_most_six_full_proposals_then_no_fundable_candidate():
    configs = [f"c{k}" for k in range(10)]
    run = Script({k: 0.9 for k in configs})
    out = R.run_replicate_campaign(R.Fixr3Engine(6201), configs, run)
    assert len(out["steps"]) == 6 and out["counter"].used == 18 and out["ended_on"] == "no_fundable_candidate"
    assert A.table_ended_on(worker_runs=18, llm_calls=10, arm="FIXR3", unfundable=True) == "no_fundable_candidate"


def test_failures_let_a_campaign_execute_more_proposals_and_end_at_w():
    configs = [f"c{k}" for k in range(12)]
    # two candidates fail at j = 0 (one run each): 2 + 6 x 3 = 20 runs, eight proposals executed
    run = Script({k: 0.9 for k in configs}, fail={("c1", 0), ("c3", 0)})
    out = R.run_replicate_campaign(R.Fixr3Engine(6201), configs, run)
    assert len(out["steps"]) == 8 and out["counter"].used == 20 and out["ended_on"] == "worker_runs"


def test_unfundable_step_charges_nothing():
    run = Script({"c0": 0.9})
    c = A.ChargedRunCounter(W=2)
    with pytest.raises(A.UnfundableStep):
        R.Fixr3Engine(6201).step("c0", run, c)
    assert c.used == 0 and run.calls == []


def test_minimised_metrics_are_oriented():
    run = Script({"c0": [0.30, 0.31, 0.29], "lower": [0.10, 0.11, 0.105]})
    c = A.ChargedRunCounter(W=20)
    e = R.Fixr3Engine(6201, maximize=False)
    e.step("c0", run, c)
    assert e.step("lower", run, c).decision == "kept"


def test_replicate_entries_feed_campaign_usage(tmp_path):
    configs = ["c0", "c1", "c2"]
    run = Script({"c0": 0.9, "c1": 0.91, "c2": 0.5}, fail={("c2", 1)})
    out = R.run_replicate_campaign(R.Fixr3Engine(6201), configs, run)
    rows = [{"budget_index": b + 1, "worker_mode": "w", "extra": {"control": {"replicates": s.replicates}}}
            for b, s in enumerate(out["steps"])]
    (tmp_path / "t.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp_path / "e.jsonl").write_text("")
    u = A.campaign_usage(tmp_path / "t.jsonl", tmp_path / "e.jsonl", arm="FIXR3", instance="i", information_set="s",
                         worker_run_cap=20, llm_call_cap=80, manager_deterministic=True)
    assert u.worker_runs == out["counter"].used == 3 + 3 + 2
