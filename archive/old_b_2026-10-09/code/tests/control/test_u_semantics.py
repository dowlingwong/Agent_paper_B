"""B2: U is primary; invalid, collection failure and unavailable stay distinct.

These are engineering counterexamples: each test fails if the code lets an
invalid outcome, a collection failure or an unavailable action be read as a
utility value.
"""
from dataclasses import replace
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from causal_branch.control.evaluate import (  # noqa: E402
    assert_single_outcome_channel,
    checkpoint_rows,
    evaluate_policies,
)
from causal_branch.control.schema import BranchRecordError, validate_record  # noqa: E402
from test_b_contract import _record  # noqa: E402


def _with_outcome(root, action, utility, *, invalid=0, reason=None,
                  integrity="ok", mask=None):
    return _record(
        template_id=f"t-{root}",
        template_family_id=f"t-{root}",
        root_id=root,
        checkpoint_id=f"c-{root}",
        action_id=action,
        pre_treatment_mask=mask or {"g0": True, "gv": True},
        outcome_success=None if utility is None else int(utility >= 0.5),
        outcome_utility=utility,
        outcome_invalid=invalid if utility is not None else None,
        invalid_reason=reason if utility is not None else None,
        integrity_status=integrity,
        execution_status="completed" if integrity == "ok" else "collection_failure",
    )


def _scores(records):
    keys = sorted({(r.root_id, r.checkpoint_id) for r in records})
    return {"a": {k: float(i) for i, k in enumerate(keys)},
            "b": {k: float(-i) for i, k in enumerate(keys)}}


class TestInvalidIsZeroWithReason(unittest.TestCase):
    def test_invalid_is_exactly_zero_with_reason_retained(self):
        record = _with_outcome("r0", "gv", 0.0, invalid=1, reason="no_valid_candidate")
        validate_record(record)  # U=0 with the reason kept is valid

    def test_invalid_with_nonzero_utility_is_rejected(self):
        record = _with_outcome("r0", "gv", 0.2, invalid=1, reason="no_valid_candidate")
        with self.assertRaisesRegex(BranchRecordError, "exactly outcome_utility=0"):
            validate_record(record)

    def test_invalid_without_reason_is_rejected(self):
        record = _with_outcome("r0", "gv", 0.0, invalid=1, reason=None)
        with self.assertRaisesRegex(BranchRecordError, "retained invalid_reason"):
            validate_record(record)

    def test_invalid_reason_on_valid_outcome_is_rejected(self):
        record = _with_outcome("r0", "gv", 0.5, invalid=0, reason="stray")
        with self.assertRaisesRegex(BranchRecordError, "only meaningful for an invalid"):
            validate_record(record)


class TestCollectionFailureIsNotZero(unittest.TestCase):
    def test_collection_failure_carries_no_outcome(self):
        record = _with_outcome("r0", "g0", None, integrity="collection_failure")
        validate_record(record)

    def test_collection_failure_with_outcome_is_rejected(self):
        record = _with_outcome("r0", "g0", 0.0, integrity="collection_failure")
        with self.assertRaises(BranchRecordError):
            validate_record(record)
        # With a terminal failure status the specific integrity rule fires.
        terminal = replace(record, execution_status="error")
        with self.assertRaisesRegex(BranchRecordError, "non-ok integrity status"):
            validate_record(terminal)

    def test_evaluator_refuses_collection_failure_as_zero(self):
        records = [_with_outcome("r0", "g0", 0.5),
                   _with_outcome("r0", "gv", 0.8),
                   _with_outcome("r1", "g0", None, integrity="collection_failure")]
        with self.assertRaisesRegex(ValueError, "refusing to analyse integrity status"):
            checkpoint_rows(records, ("U",))


class TestUnavailableStaysInOriginalRootAnalysis(unittest.TestCase):
    def test_unavailable_root_falls_back_and_stays_in_denominator(self):
        records = [
            _with_outcome("r0", "g0", 0.5),
            _with_outcome("r0", "gv", 0.5),
            _record(
                template_id="t-r1", template_family_id="t-r1", root_id="r1",
                checkpoint_id="c-r1", action_id="gv",
                pre_treatment_mask={"g0": True, "gv": False},
                execution_status="unavailable", failure_reason="verifier_input_absent",
            ),
            _with_outcome("r1", "g0", 0.4, mask={"g0": True, "gv": False}),
        ]
        rows = checkpoint_rows(records, ("U",))
        self.assertEqual(len(rows), 2)  # both original roots are present
        comparison = evaluate_policies(
            records, scores_by_policy=_scores(records),
            primary_policy="a", primary_comparator="b", capacities=(1.0,),
            outcome="U", n_bootstrap=20,
        )[0]
        evaluation = comparison.evaluations["a"]
        # r1 has no gv outcome and contributes zero through its continue
        # fallback, but it is still an eligible original root.
        self.assertEqual(evaluation.n_eligible_checkpoints, 2)
        self.assertEqual(evaluation.n_feasible_checkpoints, 1)
        self.assertAlmostEqual(evaluation.gain_full_population, 0.0)


class TestOutcomeChannelsDoNotMix(unittest.TestCase):
    def test_mixing_s_and_u_in_one_contrast_is_refused(self):
        with self.assertRaisesRegex(ValueError, "mixing S and U is refused"):
            assert_single_outcome_channel(("S", "U"))

    def test_single_channel_is_accepted(self):
        assert_single_outcome_channel(("U",))
        assert_single_outcome_channel(["S"])

    def test_evaluate_policies_uses_one_channel(self):
        records = [_with_outcome("r0", "g0", 0.5), _with_outcome("r0", "gv", 0.8)]
        comparison = evaluate_policies(
            records, scores_by_policy=_scores(records),
            primary_policy="a", primary_comparator="b",
            capacities=(1.0,), outcome="U", n_bootstrap=10,
        )[0]
        self.assertEqual(comparison.outcome, "U")


if __name__ == "__main__":
    unittest.main()
