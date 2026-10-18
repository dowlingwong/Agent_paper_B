"""B5: b_branch_v2 records, the real fork path, tree converter and estimators."""
from dataclasses import replace
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from causal_branch.adapters.toy import MockModelProvider  # noqa: E402
from causal_branch.control.evaluate import evaluate_policies  # noqa: E402
from test_b_contract import _record  # noqa: E402
from causal_branch.control.branch_tree import (  # noqa: E402
    DecisionView,
    TreeError,
    execute_tree_v2,
    original_root_values,
    paired_contrast,
    records_to_tree,
    theta_difference,
    value_of_regimes,
)


class SumTask:
    """A tiny scripted task executed through the real fork path.

    The initial candidate is wrong; only a verification fixes it.  Outcomes are
    computed by grading the files, never supplied as constants.
    """

    def __init__(self):
        self.provider = MockModelProvider()

    def prepare(self, workspace, *, template_id, root_id, seed):
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "candidate.json").write_text(json.dumps({"values": [1, 2, 30]}) + "\n")
        (workspace / "dev_batch1.json").write_text(json.dumps({"expected": 6}) + "\n")
        (workspace / "task.json").write_text(json.dumps({"template_id": template_id, "seed": seed}) + "\n")

    def continue_to_checkpoint2(self, workspace):
        (workspace / "dev_batch2.json").write_text(json.dumps({"expected": 6}) + "\n")
        return True

    def verify_and_respond(self, workspace):
        expected = json.loads((workspace / "dev_batch1.json").read_text())["expected"]
        candidate = json.loads((workspace / "candidate.json").read_text())
        if sum(candidate["values"]) != expected:
            # The verifier uses the mock provider and replaces the candidate on
            # a strict visible improvement.
            self.provider.complete("repair")
            (workspace / "candidate.json").write_text(json.dumps({"values": [1, 2, 3]}) + "\n")

    def grade(self, workspace):
        expected = json.loads((workspace / "dev_batch1.json").read_text())["expected"]
        candidate = json.loads((workspace / "candidate.json").read_text())
        return 1.0 if sum(candidate["values"]) == expected else 0.0


class TestTreeDriver(unittest.TestCase):
    def _run(self, task):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        branch_root = Path(tmp.name) / "branches"
        records, tree = execute_tree_v2(
            task, root_id="r0", template_family_id="family-0", split="engineering",
            seed=7, branch_root=branch_root,
        )
        return records, tree

    def test_driver_executes_all_three_regimes(self):
        records, tree = self._run(SumTask())
        decisions = {(r.decision_index, r.action) for r in records}
        self.assertEqual(decisions, {(1, "verify"), (1, "continue"), (2, "verify"), (2, "continue")})
        self.assertTrue(tree["reached2"])
        self.assertEqual(tree["now"], 1.0)   # verify repairs the candidate
        self.assertEqual(tree["never"], 0.0)  # never leaves it wrong
        self.assertEqual(tree["later"], 1.0)

    def test_reached_only_denominator_rejected(self):
        records, _ = self._run(SumTask())
        broken = [replace(r, reached=False, terminated_before_decision=True)
                  if r.decision_index == 1 and r.action == "continue" else r
                  for r in records]
        with self.assertRaisesRegex(TreeError, "reached-only"):
            records_to_tree(broken)

    def test_transplanted_checkpoint2_rejected(self):
        records, _ = self._run(SumTask())
        broken = [replace(r, history_hash_at_decision="transplanted")
                  if r.decision_index == 2 and r.action == "verify" else r
                  for r in records]
        with self.assertRaisesRegex(TreeError, "siblings disagree"):
            records_to_tree(broken)

    def test_second_verification_rejected(self):
        records, _ = self._run(SumTask())
        broken = [replace(r, verifier_calls=2) if r.action == "verify" else r
                  for r in records]
        with self.assertRaisesRegex(TreeError, "at most one verification"):
            records_to_tree(broken)

    def test_checkpoint2_fork_parented_to_verify_now_is_rejected(self):
        records, _ = self._run(SumTask())
        now_id = next(r.branch_id for r in records
                      if r.decision_index == 1 and r.action == "verify")
        broken = [replace(r, parent_branch_id=now_id) if r.decision_index == 2 else r
                  for r in records]
        with self.assertRaisesRegex(TreeError, "transplanted"):
            records_to_tree(broken)

    def test_lineage_leakage_rejected(self):
        records, _ = self._run(SumTask())
        broken = [replace(r, split="test") if r.branch_id.endswith("__now") else r
                  for r in records]
        with self.assertRaisesRegex(TreeError, "lineage or split leakage"):
            records_to_tree(broken)


def _trees():
    rows = [
        ("f1", "r1", 1.0, 0.5, 0.0),
        ("f1", "r2", 0.8, 0.9, 0.1),
        ("f2", "r3", 0.2, 0.7, 0.3),
        ("f2", "r4", 0.6, 0.4, 0.2),
        ("f3", "r5", 0.5, 0.5, 0.5),
    ]
    return [
        {"root_id": root, "template_family_id": family, "split": "test",
         "now": now, "later": later, "never": never}
        for family, root, now, later, never in rows
    ]


def _regimes(trees, regime):
    return {t["root_id"]: regime for t in trees}


class TestReachabilityRows(unittest.TestCase):
    def test_evaluator_keeps_non_reaching_root_in_full_population(self):
        records = [
            _record(template_id="t0", template_family_id="f0", root_id="r0",
                    checkpoint_id="c0", split="test", action_id="g0", outcome_success=0,
                    outcome_utility=0.5, outcome_invalid=0, execution_status="completed",
                    pre_treatment_mask={"g0": True, "gv": True}),
            _record(template_id="t0", template_family_id="f0", root_id="r0",
                    checkpoint_id="c0", split="test", action_id="gv", outcome_success=0,
                    outcome_utility=0.5, outcome_invalid=0, execution_status="completed",
                    pre_treatment_mask={"g0": True, "gv": True}),
        ]
        scores = {"a": {("r0", "c0"): 1.0, ("r1", "r1/unreached"): 0.0},
                  "b": {("r0", "c0"): 1.0, ("r1", "r1/unreached"): 0.0}}
        comparison = evaluate_policies(
            records, scores_by_policy=scores, primary_policy="a", primary_comparator="b",
            capacities=(1.0,), outcome="U", n_bootstrap=20,
            reachability=[{"root_id": "r1", "template_family_id": "f1",
                           "split": "test", "fallback": 0.2}],
        )[0]
        evaluation = comparison.evaluations["a"]
        self.assertEqual(evaluation.n_eligible_checkpoints, 2)
        self.assertEqual(evaluation.n_feasible_checkpoints, 1)
        self.assertAlmostEqual(evaluation.gain_full_population, 0.0)


class TestEstimators(unittest.TestCase):
    def test_original_root_values_and_difference(self):
        values = original_root_values(_trees())
        self.assertAlmostEqual(values["now"], np.mean([1.0, 0.8, 0.2, 0.6, 0.5]))
        self.assertAlmostEqual(theta_difference(_trees()),
                               values["now"] - values["later"])

    def test_value_of_regimes_and_identical_contrast_is_zero(self):
        trees = _trees()
        never = _regimes(trees, "never")
        self.assertAlmostEqual(value_of_regimes(trees, never), np.mean([0.0, 0.1, 0.3, 0.2, 0.5]))
        contrast = paired_contrast(trees, never, never, n_bootstrap=50, seed=1)
        self.assertEqual(contrast["point"], 0.0)
        self.assertEqual(contrast["ci"], (0.0, 0.0))

    def test_shared_draws_give_a_paired_contrast(self):
        trees = _trees()
        contrast = paired_contrast(trees, _regimes(trees, "now"), _regimes(trees, "never"),
                                   n_bootstrap=200, seed=20260927)
        self.assertGreater(contrast["point"], 0.0)
        self.assertEqual(contrast["n_families"], 3)

    def test_value_of_regimes_rejects_missing_or_unknown(self):
        trees = _trees()
        with self.assertRaisesRegex(TreeError, "missing for roots"):
            value_of_regimes(trees, {"r1": "never"})
        with self.assertRaisesRegex(TreeError, "unknown regime"):
            value_of_regimes(trees, _regimes(trees, "maybe"))


class TestLineageAndDecisionView(unittest.TestCase):
    def test_later_and_never_share_the_checkpoint2_state(self):
        records, tree = execute_tree_v2(
            SumTask(), root_id="r", template_family_id="f", split="engineering",
            seed=3, branch_root=Path(tempfile.mkdtemp()) / "b",
        )
        later = next(r for r in records if r.decision_index == 2 and r.action == "verify")
        never = next(r for r in records if r.decision_index == 2 and r.action == "continue")
        self.assertEqual(later.parent_branch_id, never.parent_branch_id)
        self.assertEqual(later.history_hash_at_decision, never.history_hash_at_decision)

    def test_decision_view_h1_and_h2(self):
        view1 = DecisionView(phase=1, h1={"z": 1.0}, remaining_budget=3, progress=0.1)
        self.assertEqual(view1.history, {"z": 1.0})
        with self.assertRaisesRegex(TreeError, "not available at checkpoint 1"):
            view1.later_state()
        view2 = DecisionView(phase=2, h1={"z": 1.0}, h2={"z": 1.0, "x": 2.0},
                             remaining_budget=2, progress=0.6)
        self.assertEqual(view2.history, {"z": 1.0, "x": 2.0})
        self.assertEqual(view2.later_state(), {"z": 1.0, "x": 2.0})

    def test_decision_view_rejects_h2_missing_h1_without_flag(self):
        with self.assertRaisesRegex(TreeError, "H2 must contain H1"):
            DecisionView(phase=2, h1={"z": 1.0}, h2={"x": 2.0})
        # a declared sufficiency flag permits the drop
        view = DecisionView(phase=2, h1={"z": 1.0}, h2={"x": 2.0}, sufficiency_declared=True)
        self.assertEqual(view.history, {"x": 2.0})

    def test_controller_reading_outcomes_raises(self):
        view = DecisionView(phase=1, h1={"z": 0.0})
        with self.assertRaisesRegex(TreeError, "leaf outcomes"):
            view.outcome("now")
        with self.assertRaisesRegex(TreeError, "hidden"):
            view.hidden()


if __name__ == "__main__":
    unittest.main()
