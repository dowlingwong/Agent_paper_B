#!/usr/bin/env python3
"""Paper B control-side scientific regression checks (negative tests).

Each test catches a concrete failure mode named in the runbook's mandatory
checks.  These are contract/engineering checks: passing them is not evidence
about the world.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from causal_branch.control.allocation import (  # noqa: E402
    ConservativeSelector,
    batch_top_q,
    streaming_threshold,
)
from causal_branch.control.evaluate import evaluate_policies  # noqa: E402
from causal_branch.control.schema import (  # noqa: E402
    BranchRecord,
    BranchRecordError,
    assert_no_duplicate_units,
    feature_projection,
    validate_record,
)
from causal_branch.control.world import generate_world  # noqa: E402


def _record(**overrides) -> BranchRecord:
    base = dict(
        study="B1_pilot",
        protocol_hash="p",
        run_id="r",
        template_id="t",
        root_id="root",
        checkpoint_id="ckpt",
        checkpoint_rule_version="v1",
        split="train",
        condition_label="evaluator_only",
        runtime_manifest_hash="rm",
        snapshot_hash="sn",
        history_hash="hh",
        feature_registry_version="fr",
        pre_treatment_features={"z": 0.5},
        pre_treatment_mask={"g0": True, "gv": True},
        availability_evidence_hash="av",
        action_id="g0",
        action_version="v1",
        continuation_version="rho",
        repetition_id=0,
        seed_coupling_id="s",
        branch_order=0,
        adjudicator_version="adj",
    )
    base.update(overrides)
    return BranchRecord(**base)


class TestUnavailableIsNotZero(unittest.TestCase):
    def test_unavailable_action_cannot_carry_an_outcome(self):
        record = _record(
            action_id="gv",
            pre_treatment_mask={"g0": True, "gv": False},
            execution_status="unavailable",
            outcome_success=0,
            adjudicator_version="adj",
        )
        with self.assertRaises(BranchRecordError):
            validate_record(record)

    def test_unavailable_record_without_outcome_is_valid(self):
        record = _record(
            action_id="gv",
            pre_treatment_mask={"g0": True, "gv": False},
            execution_status="unavailable",
            failure_reason="verifier_input_absent",
        )
        validate_record(record)


class TestFeasibleTimeoutRetained(unittest.TestCase):
    def test_timeout_is_an_outcome_of_the_regime(self):
        record = _record(
            action_id="gv",
            execution_status="timeout",
            outcome_success=0,
            outcome_utility=0.0,
            outcome_invalid=0,
            adjudicator_version="adj",
        )
        validate_record(record)  # must not be dropped or converted to unavailable

    def test_pending_record_cannot_carry_an_outcome(self):
        with self.assertRaises(BranchRecordError):
            validate_record(
                _record(
                    action_id="gv",
                    execution_status="pending",
                    outcome_success=1,
                    adjudicator_version="adj",
                )
            )


class TestDuplicateUnits(unittest.TestCase):
    def test_duplicate_root_checkpoint_action_repetition_rejected(self):
        records = [_record(repetition_id=0), _record(repetition_id=0)]
        with self.assertRaises(BranchRecordError):
            assert_no_duplicate_units(records)

    def test_repetition_is_not_an_independent_unit(self):
        # Two repetitions of one checkpoint are two records but one unit; the
        # duplicate check must not treat repetition as a new independent unit.
        records = [_record(repetition_id=0), _record(repetition_id=1)]
        assert_no_duplicate_units(records)


class TestNoInjectorLabelLeakage(unittest.TestCase):
    def test_projection_excludes_condition_and_outcomes(self):
        record = _record(condition_label="hurt=1", outcome_success=1)
        projection = feature_projection(record)
        self.assertNotIn("condition_label", projection)
        self.assertNotIn("outcome_success", projection)
        self.assertNotIn("outcome_utility", projection)
        self.assertNotIn("outcome_invalid", projection)
        self.assertNotIn("artifact_hashes", projection)

    def test_projection_contains_only_features_and_mask(self):
        projection = feature_projection(_record())
        self.assertEqual(set(projection), {"features", "mask"})


class TestBatchVsStreaming(unittest.TestCase):
    def test_batch_top_q_has_exact_count(self):
        scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        feasible = np.array([True, True, True, True, True])
        selected = batch_top_q(scores, feasible, 0.4)
        self.assertEqual(int(selected.sum()), 2)

    def test_batch_top_q_never_selects_infeasible(self):
        scores = np.array([0.9, 0.8, 0.7])
        feasible = np.array([False, True, True])
        selected = batch_top_q(scores, feasible, 1.0)
        self.assertFalse(selected[0])

    def test_streaming_threshold_does_not_promise_a_count(self):
        scores = np.array([0.9, 0.8, 0.7, 0.6])
        selected = streaming_threshold(scores, 0.75, np.ones(4, dtype=bool))
        self.assertEqual(int(selected.sum()), 2)  # achieved rate, not a fixed budget


class TestConservativeSelectionIsNotACertificate(unittest.TestCase):
    def test_fallback_when_no_member_qualifies(self):
        selector = ConservativeSelector(delta=0.05, harm_tolerance=0.0)
        result = selector.select({"a": np.array([-0.1, -0.2]), "b": np.array([0.0, -0.1])})
        self.assertTrue(result.fallback)
        self.assertIsNone(result.chosen)

    def test_zero_observed_errors_do_not_produce_a_certificate(self):
        # A perfect mean with one template must not qualify: the bound is the
        # object, not the observed mean.
        selector = ConservativeSelector(delta=0.05, harm_tolerance=0.0)
        result = selector.select({"a": np.array([1.0])})
        self.assertTrue(result.fallback)

    def test_selection_requires_a_positive_lower_bound(self):
        selector = ConservativeSelector(delta=0.05, harm_tolerance=0.0, gain_range=1.0)
        gains = np.full(400, 0.5)
        result = selector.select({"a": gains})
        self.assertFalse(result.fallback)
        self.assertLess(result.bounds["a"], 0.5)  # the bound is conservative


class TestUtilityAndSelectionEstimands(unittest.TestCase):
    def test_utility_channel_is_separate_from_binary(self):
        world = generate_world(seed=7, n_templates=6, roots_per_template=2, repetitions=2, split="test")
        records = world.records
        keys = sorted({(r.root_id, r.checkpoint_id) for r in records if r.outcome_success is not None})
        scores = {name: {key: 0.5 for key in keys} for name in ("advantage", "risk")}
        s_eval = evaluate_policies(records, scores_by_policy=scores, primary_policy="advantage", primary_comparator="risk", capacities=(0.5,), outcome="S")
        u_eval = evaluate_policies(records, scores_by_policy=scores, primary_policy="advantage", primary_comparator="risk", capacities=(0.5,), outcome="U")
        self.assertTrue(s_eval and u_eval)
        # The two channels are computed from different outcome fields; they are
        # not silently the same analysis.
        self.assertEqual(s_eval[0].outcome, "S")
        self.assertEqual(u_eval[0].outcome, "U")

    def test_population_gain_and_selected_set_gain_are_distinct_fields(self):
        world = generate_world(seed=8, n_templates=6, roots_per_template=2, repetitions=2, split="test")
        keys = sorted({(r.root_id, r.checkpoint_id) for r in world.records if r.outcome_success is not None})
        scores = {"advantage": {key: 1.0 for key in keys}, "risk": {key: 0.0 for key in keys}}
        comparison = evaluate_policies(world.records, scores_by_policy=scores, primary_policy="advantage", primary_comparator="risk", capacities=(0.5,))[0]
        evaluation = comparison.evaluations["advantage"]
        # The feasible-support gain averages over ALL feasible checkpoints;
        # the full-population gain divides the same selected sum by all eligible
        # checkpoints (unavailable ones fall back to g0 and contribute 0).
        self.assertGreater(evaluation.n_feasible_checkpoints, evaluation.n_selected)
        self.assertAlmostEqual(
            evaluation.gain_full_population,
            evaluation.gain_feasible * evaluation.n_feasible_checkpoints / evaluation.n_eligible_checkpoints
            if evaluation.n_selected
            else 0.0,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
