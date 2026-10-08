"""B4: matched controllers, total-work accounting, ridge equivalence, RF witness."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from causal_branch.control.controllers import (  # noqa: E402
    Budget,
    BudgetError,
    BudgetReport,
    FixedRegime,
    FrozenReserveVOI,
    LeafCost,
    RepeatedMyopic,
    RFWitness,
    allowed_tree_budget,
    assert_matched_allowed_budgets,
    assert_ridge_equivalence,
)
from causal_branch.control.learners import AdvantageLearner, ActionValueLearner  # noqa: E402
from causal_branch.control.tree import Root, build_tree  # noqa: E402

TREE_REGIME = {"now": "verify_now", "later": "verify_later", "never": "never"}


def _root(**delta):
    base = dict(root_id="r", template_family_id="f", split="engineering",
                budget=1.0, cost_now=1.0, cost_later=1.0,
                reaches_after_continue=True, reaches_after_verify=False,
                terminated_after_continue=False, available_now=True,
                available_later=True, never=0.0, now=0.2, later=1.0,
                immediate_gain=0.0)
    base.update(delta)
    return Root(**base)


def _outcome(root, controller, adv1, adv2):
    regime = controller.choose(
        adv1, adv2,
        reached2=root.reaches_after_continue and not root.terminated_after_continue,
        budget_remaining=1 if root.budget >= 1 else 0,
    )
    return next(leaf["outcome"] for leaf in build_tree(root)["leaves"]
                if leaf["regime"] == TREE_REGIME[regime])


class TestControllerOrdering(unittest.TestCase):
    def test_early_use_optimal(self):
        root = _root(now=1.0, later=0.5, immediate_gain=1.0)
        frozen = FrozenReserveVOI(reserve_threshold=0.2)
        self.assertEqual(frozen.choose(1.0, 0.0, reached2=True), "now")
        self.assertEqual(_outcome(root, frozen, 1.0, 0.0), 1.0)

    def test_save_for_later(self):
        root = _root(now=0.2, later=1.0, immediate_gain=0.05)
        frozen = FrozenReserveVOI(reserve_threshold=0.2)
        self.assertEqual(frozen.choose(0.05, 1.0, reached2=True), "later")
        self.assertEqual(_outcome(root, frozen, 0.05, 1.0), 1.0)

    def test_repeated_myopic_fails_in_the_greedy_world(self):
        root = _root(now=0.2, later=1.0, immediate_gain=0.1)
        myopic = RepeatedMyopic()
        frozen = FrozenReserveVOI(reserve_threshold=0.2)
        self.assertEqual(myopic.choose(0.1, 1.0, reached2=True), "now")
        self.assertEqual(frozen.choose(0.1, 1.0, reached2=True), "later")
        self.assertLess(_outcome(root, myopic, 0.1, 1.0),
                        _outcome(root, frozen, 0.1, 1.0))

    def test_unreachable_checkpoint2_falls_back(self):
        root = _root(reaches_after_continue=False, immediate_gain=0.05)
        frozen = FrozenReserveVOI(reserve_threshold=0.2)
        self.assertEqual(frozen.choose(0.05, 1.0, reached2=False), "never")
        self.assertEqual(_outcome(root, frozen, 0.05, 1.0), 0.0)

    def test_checkpoint2_requires_a_positive_score(self):
        # The constant-reserve bug: reaching checkpoint 2 was enough to verify.
        # A negative checkpoint-2 score must now leave the verification unused.
        frozen = FrozenReserveVOI(reserve_threshold=0.2)
        self.assertEqual(frozen.choose(0.05, -0.3, reached2=True), "never")
        self.assertEqual(frozen.choose(0.05, 0.3, reached2=True), "later")
        myopic = RepeatedMyopic()
        self.assertEqual(myopic.choose(0.0, -0.1, reached2=True), "never")

    def test_fixed_regimes(self):
        self.assertEqual(FixedRegime("never").choose(1.0, 1.0, reached2=True), "never")
        self.assertEqual(FixedRegime("now").choose(0.0, 0.0, reached2=True), "now")
        self.assertEqual(FixedRegime("later").choose(0.0, 0.0, reached2=True), "later")
        self.assertEqual(FixedRegime("later").choose(0.0, 0.0, reached2=False), "never")


class TestBudgetMatching(unittest.TestCase):
    def test_tree_budget_is_floor_not_ceil(self):
        self.assertEqual(allowed_tree_budget(10, 0.25, 2.0), Budget(2, 4.0))
        self.assertEqual(allowed_tree_budget(3, 0.25, 1.0), Budget(0, 0.0))

    def test_matching_refuses_unequal_allowed_budgets(self):
        assert_matched_allowed_budgets({"a": Budget(5, 10.0), "b": Budget(5, 10.0)})
        with self.assertRaisesRegex(BudgetError, "equal allowed"):
            assert_matched_allowed_budgets({"a": Budget(5, 10.0), "b": Budget(4, 10.0)})
        with self.assertRaisesRegex(BudgetError, "equal allowed"):
            assert_matched_allowed_budgets({"a": Budget(5, 10.0), "b": Budget(5, 9.0)})

    def test_realized_use_reported_separately_and_bounded(self):
        report = BudgetReport(Budget(3, 6.0), realized_calls=2, realized_work=4.0)
        self.assertEqual(report.unspent_calls, 1)
        self.assertEqual(report.unspent_work, 2.0)
        with self.assertRaisesRegex(BudgetError, "allowed budget"):
            BudgetReport(Budget(1, 2.0), realized_calls=2, realized_work=2.0)
        with self.assertRaisesRegex(BudgetError, "allowed budget"):
            BudgetReport(Budget(1, 2.0), realized_calls=1, realized_work=2.5)


class TestCostLedger(unittest.TestCase):
    def test_ledger_total_and_channels(self):
        cost = LeafCost(prefix=1.0, continuation_ckpt2=2.0, verifier_overhead=3.0,
                        failed_attempts=1.0, storage=0.5)
        self.assertEqual(cost.total(), 7.5)
        self.assertEqual(set(cost.channels()), {
            "prefix", "continuation_ckpt2", "verifier_overhead",
            "failed_attempts", "storage"})


class TestRidgeEquivalence(unittest.TestCase):
    def test_advantage_and_action_value_agree(self):
        feats = [{"z": 0.0}, {"z": 0.5}]
        flat = [feats[0], feats[0], feats[1], feats[1]]
        actions = ["g0", "gv", "g0", "gv"]
        labels = [0.1, 0.4, 0.6, 0.9]
        value = ActionValueLearner().fit(flat, actions, labels)
        adv = AdvantageLearner().fit(feats, [0.3, 0.3])

        def q(feature, action):
            return float(value.predict([feature], [action])[0])

        value_diff = np.array([q(feats[0], "gv") - q(feats[0], "g0"),
                               q(feats[1], "gv") - q(feats[1], "g0")])
        gap = assert_ridge_equivalence(adv.predict(feats), value_diff)
        self.assertLessEqual(gap, 1e-12)

    def test_equivalence_check_detects_a_wrong_gap(self):
        with self.assertRaisesRegex(BudgetError, "equivalence violated"):
            assert_ridge_equivalence([0.1, 0.2], [0.1, 0.3])


class TestRFWitness(unittest.TestCase):
    def test_configuration_and_penalty(self):
        rng = np.random.default_rng(0)
        rows = [{"z": float(z)} for z in rng.uniform(0, 1, 60)]
        labels = [int(r["z"] > 0.5) for r in rows]
        witness = RFWitness(penalty_multiplier=1.0)
        witness.fit(rows, labels)
        self.assertEqual(witness.n_estimators, 200)
        self.assertEqual(witness.max_depth, 6)
        scores = witness.predict(rows)
        self.assertEqual(scores.shape, (60,))
        plain = RFWitness(penalty_multiplier=0.0)
        plain.fit(rows, labels)
        self.assertTrue(np.all(witness.predict(rows) <= plain.predict(rows) + 1e-12))


if __name__ == "__main__":
    unittest.main()
