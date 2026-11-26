"""D27/P3: the E1 no-op/duplicate skip controller (harness heuristic arm).

AI-assisted (BUILD_BATCH3, P3); ENGINEERING_ONLY.
"""
from __future__ import annotations

from types import SimpleNamespace

from r1.controllers import NOOP_SKIP_ARM_NOTE, NoOpSkipController
from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.controller import build_control_view, compute_mask  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

START = {"LEARNING_RATE": "0.001", "REGULARIZATION": "0.0001", "N_EPOCHS": "80", "BATCH_SIZE": "32"}


def _record(index: int, decision: str) -> SimpleNamespace:
    return SimpleNamespace(budget_index=index, decision=decision, parsed_metrics={})


def _proposal(symbol: str, old: str, new: str) -> SimpleNamespace:
    return SimpleNamespace(
        extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                   "symbol": symbol, "old": old, "new": new}},
        manager_mode="stub",
        proposal_summary=f"{symbol} {old} -> {new}",
        objective=f"Change {symbol} from {old} to {new}.",
    )


def _decide(controller, budget_index, records, proposal, *, skip_feasible=True):
    spec = load_registered_node("lr_synthetic", repo_root=HARNESS)
    view = build_control_view(
        epoch="E1", budget_index=budget_index, ledger_prefix=records, node=spec, proposal=proposal
    )
    mask = compute_mask(view, proposal_passed_precondition=skip_feasible)
    return controller.decide(view, mask), mask


def test_arm_is_marked_as_needing_e1_branch_data():
    assert "E1 branch data" in NOOP_SKIP_ARM_NOTE


def test_noop_edit_is_skipped():
    controller = NoOpSkipController(start_constants=START)
    decision, _ = _decide(controller, 1, [], _proposal("N_EPOCHS", "80", "80"))
    assert decision.action == "skip"
    assert decision.scores["config_equals_incumbent"] == 1.0
    assert decision.controller_version == "noop_skip/v1"


def test_new_edit_continues():
    controller = NoOpSkipController(start_constants=START)
    decision, _ = _decide(controller, 1, [], _proposal("LEARNING_RATE", "0.001", "0.002"))
    assert decision.action == "continue"


def test_duplicate_of_an_evaluated_config_is_skipped():
    controller = NoOpSkipController(start_constants=START)
    first, _ = _decide(controller, 1, [], _proposal("LEARNING_RATE", "0.001", "0.002"))
    assert first.action == "continue"
    second, _ = _decide(
        controller, 2, [_record(1, "discarded")],
        _proposal("LEARNING_RATE", "0.001", "0.002"),
    )
    assert second.action == "skip"
    assert second.scores["config_seen_before"] == 1.0
    assert second.scores["config_equals_incumbent"] == 0.0


def test_after_a_keep_the_new_incumbent_is_the_reference():
    controller = NoOpSkipController(start_constants=START)
    _decide(controller, 1, [], _proposal("LEARNING_RATE", "0.001", "0.002"))
    repeat, _ = _decide(
        controller, 2, [_record(1, "kept")],
        _proposal("LEARNING_RATE", "0.002", "0.002"),
    )
    assert repeat.action == "skip"
    revert, _ = _decide(
        controller, 3, [_record(1, "kept"), _record(2, "skipped")],
        _proposal("LEARNING_RATE", "0.002", "0.001"),
    )
    assert revert.action == "continue"


def test_skipped_trials_evaluate_nothing():
    controller = NoOpSkipController(start_constants=START)
    _decide(controller, 1, [], _proposal("LEARNING_RATE", "0.001", "0.002"))
    later, _ = _decide(
        controller, 2, [_record(1, "skipped")],
        _proposal("LEARNING_RATE", "0.001", "0.002"),
    )
    assert later.action == "continue"


def test_an_unseen_keep_makes_the_controller_conservative():
    controller = NoOpSkipController(start_constants=START)
    decision, _ = _decide(
        controller, 2, [_record(1, "kept")],
        _proposal("N_EPOCHS", "80", "80"),
    )
    assert decision.action == "continue"


def test_infeasible_skip_mask_keeps_continue():
    controller = NoOpSkipController(start_constants=START)
    decision, mask = _decide(
        controller, 1, [], _proposal("N_EPOCHS", "80", "80"), skip_feasible=False
    )
    assert mask["skip"] is False
    assert decision.action == "continue"


def test_non_e1_epochs_continue():
    controller = NoOpSkipController(start_constants=START)
    spec = load_registered_node("lr_synthetic", repo_root=HARNESS)
    view = build_control_view(
        epoch="E2", budget_index=2, ledger_prefix=[_record(1, "discarded")], node=spec,
        proposal=_proposal("N_EPOCHS", "80", "80"),
    )
    assert controller.decide(view, compute_mask(view)).action == "continue"
