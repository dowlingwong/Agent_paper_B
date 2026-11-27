import pytest
from pathlib import Path

from paperc import guarded_first_accept as guard


def test_proposed_seeds_need_a_new_worker_reservation():
    registry = Path(__file__).resolve().parents[1] / "seeds" / "registry_v1.json"
    result = guard.check_reservations(registry)
    assert result["instance_extension_published"] is False
    assert result["audit_seed_range"] == [10_901_000, 10_901_119]


def test_guard_seeds_the_harness_before_any_proposals():
    steps = []

    def start():
        steps.append("start")
        return 0.8

    def run(**kwargs):
        steps.append(kwargs)
        return []

    assert guard.run_guarded(measure_start=start, run_campaign=run, budget=20) == (0.8, [])
    assert steps == ["start", {"initial_current_best": 0.8, "budget": 20}]
    with pytest.raises(ValueError, match="finite"):
        guard.run_guarded(measure_start=lambda: float("nan"), run_campaign=run)
    assert len(steps) == 2


@pytest.mark.parametrize("candidate, actual", [(0.7, "discarded"), (0.8, "discarded"), (0.9, "kept")])
def test_first_trial_uses_strict_improvement(candidate, actual):
    row = {"budget_index": 1, "current_best_before": 0.8, "parsed_metrics": {"val_score": candidate},
           "decision": actual}
    assert guard.verify_keeps([row], 0.8) == ([1] if actual == "kept" else [])
    row["decision"] = "discarded" if actual == "kept" else "kept"
    with pytest.raises(ValueError, match="strict improvement"):
        guard.verify_keeps([row], 0.8)


def test_a_discard_or_invalid_trial_preserves_start():
    rows = [{"budget_index": 1, "current_best_before": 0.8, "parsed_metrics": {"val_score": 0.7},
             "decision": "discarded"},
            {"budget_index": 2, "current_best_before": 0.8, "decision": "failed_invalid"},
            {"budget_index": 3, "current_best_before": 0.8, "parsed_metrics": {"val_score": 0.85},
             "decision": "kept"}]
    assert guard.verify_keeps(rows, 0.8) == [3]
    rows[1]["current_best_before"] = 0.7
    with pytest.raises(ValueError, match="another incumbent"):
        guard.verify_keeps(rows, 0.8)


def test_guarded_first_accounts_for_prechecks_and_start_separately():
    rows = [{"worker_mode": "local_worker"}, {"worker_mode": "local_worker_precheck"}]
    events = [{"event_type": "campaign_completed",
               "payload": {"compute_budget": {"worker_runs_used": 1, "llm_calls_used": 2}}}]
    assert guard.accounting(rows, events) == {"candidate_worker_runs": 1, "start_worker_runs": 1,
                                             "llm_calls": 2}
    events[0]["payload"]["compute_budget"]["worker_runs_used"] = 2
    with pytest.raises(ValueError, match="inconsistent"):
        guard.accounting(rows, events)
