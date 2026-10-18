"""F6: proposed continuation-value rule, comparators and matching."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from causal_branch.control.timing import (  # noqa: E402
    BavarInspiredVOI,
    ConstantReserveAblation,
    FixedRegimeController,
    ProposedTiming,
    RepeatedMyopicComparator,
    TimingError,
    _fold_of,
    cross_fitted_scores,
    decision_views,
    fit_global,
    matching_report,
)


def _row(root, family, x, w, u_now, u_later, u_never, reached2=True):
    return dict(root_id=root, family=family, h1={"x": float(x)}, h2={"x": float(x), "w": float(w)},
                u_now=float(u_now), u_later=float(u_later), u_never=float(u_never),
                reached2=bool(reached2))


def _fixture(seed=0, n=200, slope=0.0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        family = f"f{i % 5}"
        x = rng.uniform(0, 1)
        w = rng.uniform(0, 1)
        noise = rng.normal(0, 0.1)
        rows.append(_row(f"r{i}", family, x, w,
                         u_now=0.5 + 0.6 * (x - 0.5),
                         u_later=0.5 + slope * x + noise,
                         u_never=0.5))
    return rows


def _null_fixture(seed=0, n=30, n_families=5):
    """True continuation mean is zero; only noisy leaf realisations differ."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        family = f"f{i % n_families}"
        x = rng.uniform(0, 1)
        w = rng.uniform(0, 1)
        rows.append(_row(f"r{i}", family, x, w,
                         u_now=0.5 + 0.6 * (x - 0.5),
                         u_later=0.5 + rng.normal(0, 2.0),
                         u_never=0.5))
    return rows


class TestProposedRule(unittest.TestCase):
    def test_explicit_cutoff_changes_continuation_policy_fit(self):
        # A bounded constant-gain world: verifying later gains .05. The two
        # existing grid cutoffs admit all or no second-stage verifications,
        # so a reused median-cutoff fit cannot represent both policies.
        rows = [_row(f"r{i}", f"f{i % 5}", i / 30, (i % 3) / 3,
                     u_now=0.5, u_later=0.55, u_never=0.5)
                for i in range(30)]
        controller = ProposedTiming()
        views = decision_views(rows)
        admit = controller.fit(rows, c2=0.0)
        deny = controller.fit(rows, c2=0.1)
        self.assertEqual(admit["c2"], 0.0)
        self.assertEqual(deny["c2"], 0.1)
        admit_scores = controller.score(admit, views)
        deny_scores = controller.score(deny, views)
        for rid in views:
            self.assertGreater(admit_scores[rid]["vwait"], 0.04)
            self.assertEqual(deny_scores[rid]["vwait"], 0.0)
            self.assertEqual(admit_scores[rid]["a1"], deny_scores[rid]["a1"])
            self.assertEqual(admit_scores[rid]["a2"], deny_scores[rid]["a2"])
        # Omitting c2 keeps the established default rather than choosing a
        # calibration-grid value behind the caller's back.
        default = controller.fit(rows)
        previous_default = fit_global(rows, l2=controller.l2, n_folds=controller.n_folds)
        self.assertEqual(default["c2"], previous_default["c2"])
        np.testing.assert_array_equal(default["w_wait"], previous_default["w_wait"])

    def test_max_bias_correction(self):
        """M1/M2: the corrected target is centred on zero *and* clearly below naive.

        True continuation mean is zero.  An in-sample second-stage decision makes
        the fitted V_wait track the naive positive part max(A2, 0) (the review
        measured +0.118 vs +0.119 at noise 2), so an absolute threshold cannot
        tell them apart.  This test compares them paired across repetitions.
        """
        vwait_means, gaps = [], []
        for seed in range(40):
            rows = _null_fixture(seed=seed, n=100, n_families=10)
            fit = cross_fitted_scores(rows, c2=0.0).scores
            vwait = np.array([fit[r["root_id"]]["vwait"] for r in rows])
            naive = np.array([max(fit[r["root_id"]]["a2"], 0.0) for r in rows])
            vwait_means.append(float(vwait.mean()))
            gaps.append(float(naive.mean() - vwait.mean()))
        vwait_means, gaps = np.array(vwait_means), np.array(gaps)
        se_v = vwait_means.std(ddof=1) / np.sqrt(len(vwait_means))
        se_g = gaps.std(ddof=1) / np.sqrt(len(gaps))
        # centred on zero within sampling error
        self.assertLess(abs(float(vwait_means.mean())), 3.0 * se_v + 0.01)
        # and far below the naive positive part, paired across repetitions
        self.assertGreater(float(gaps.mean()) - 3.0 * se_g, 0.08)

    def test_fold_leakage_is_absent(self):
        rows = _fixture(seed=2, n=100)
        before = cross_fitted_scores(rows).scores
        target_family = rows[0]["family"]
        perturbed = [dict(r) for r in rows]
        for r in perturbed:
            if r["family"] == target_family:
                r["u_now"] += 10.0
                r["u_later"] += 10.0
        after = cross_fitted_scores(perturbed).scores
        for r in rows:
            if r["family"] == target_family:
                # held out of its own fold: scores do not move with its labels
                self.assertEqual(before[r["root_id"]], after[r["root_id"]])

    def test_folds_keep_families_whole(self):
        rows = _fixture(seed=3, n=60)
        by_family = {}
        for r in rows:
            by_family.setdefault(r["family"], set()).add(_fold_of(r["family"], 5))
        self.assertTrue(all(len(f) == 1 for f in by_family.values()))


def context_fixture(seed=0, n=200, n_families=10, noise=0.1, reached_rate=0.8):
    """Immediate value depends on x; waiting value depends on a different
    feature z, so a timing rule has something a one-step rule cannot see."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        x, z, w = rng.uniform(0, 1, size=3)
        reached = bool(rng.uniform() < reached_rate)
        later = 0.5 + 0.8 * (z - 0.4) + rng.normal(0, noise)
        rows.append(dict(root_id=f"r{i}", family=f"f{i % n_families}",
                         h1={"x": float(x), "z": float(z)},
                         h2={"x": float(x), "z": float(z), "w": float(w)},
                         u_now=0.5 + 0.6 * (x - 0.5) + rng.normal(0, noise),
                         u_later=later if reached else 0.5, u_never=0.5,
                         reached2=reached, terminated=not reached))
    return rows


def _ranks(values):
    return np.argsort(np.argsort(np.asarray(values)))


class TestControllerImplementations(unittest.TestCase):
    def setUp(self):
        self.rows = context_fixture(seed=4, n=200)
        self.views = decision_views(self.rows)
        self.controllers = {
            "proposed": ProposedTiming(), "myopic": RepeatedMyopicComparator(),
            "bavar": BavarInspiredVOI(), "constant": ConstantReserveAblation(),
        }
        self.models = {k: c.fit(self.rows) for k, c in self.controllers.items()}
        self.scores = {k: c.score(self.models[k], self.views)
                       for k, c in self.controllers.items()}

    def test_scoring_refuses_raw_rows(self):
        # L1: a controller receives decision views, never rows with outcomes
        for name, c in self.controllers.items():
            with self.assertRaisesRegex(TimingError, "DecisionView"):
                c.score(self.models[name], {r["root_id"]: r for r in self.rows})

    def test_scores_do_not_move_when_outcomes_are_poisoned(self):
        # L1: scoring reads no outcome field; NaN outcomes change nothing
        poisoned = [dict(r, u_now=float("nan"), u_later=float("nan"),
                         u_never=float("nan"), h2_hidden=1.0) for r in self.rows]
        views = decision_views(poisoned)
        for name, c in self.controllers.items():
            self.assertEqual(c.score(self.models[name], views), self.scores[name], name)

    def test_checkpoint1_view_has_no_later_information(self):
        v1, v2 = self.views[self.rows[0]["root_id"]]
        self.assertEqual(set(v1.history), {"x", "z"})
        unreached = next(r for r in self.rows if not r["reached2"])
        self.assertIsNone(self.views[unreached["root_id"]][1])

    def test_proposed_s1_reorders_relative_to_myopic(self):
        prop = [self.scores["proposed"][r["root_id"]]["s1"] for r in self.rows]
        myop = [self.scores["myopic"][r["root_id"]]["s1"] for r in self.rows]
        corr = np.corrcoef(_ranks(prop), _ranks(myop))[0, 1]
        self.assertLess(corr, 0.95)

    def test_myopic_cannot_reserve_and_the_ablation_can(self):
        # C2: the constant-reserve ablation differs from myopic by its reserve
        self.assertTrue(all(p.reserve == 0 for p in self.controllers["myopic"].grid()))
        self.assertTrue(any(p.reserve > 0 for p in self.controllers["constant"].grid()))
        # proposed and myopic share one grid, so their contrast isolates s1
        self.assertEqual(self.controllers["proposed"].grid(), self.controllers["myopic"].grid())
        counts = {k: c.tuning_configs for k, c in self.controllers.items()}
        self.assertEqual(len(set(counts.values())), 1, counts)

    def test_bavar_scores_checkpoint2_from_h2(self):
        # C3: the comparator's checkpoint-2 score is a real H2 scorer
        reached = [r["root_id"] for r in self.rows if r["reached2"]]
        unreached = [r["root_id"] for r in self.rows if not r["reached2"]]
        s2 = np.array([self.scores["bavar"][rid]["s2"] for rid in reached])
        a2 = np.array([self.scores["bavar"][rid]["a2"] for rid in reached])
        self.assertGreater(len(set(np.round(s2, 12))), len(reached) // 2)
        self.assertFalse(np.allclose(s2, a2))
        self.assertTrue(all(self.scores["bavar"][rid]["s2"] == 0.0 for rid in unreached))
        # and it ranks the true continuation gain
        truth = np.array([next(r for r in self.rows if r["root_id"] == rid)["u_later"] - 0.5
                          for rid in reached])
        self.assertGreater(np.corrcoef(s2, truth)[0, 1], 0.5)

    def test_fixed_regimes(self):
        for regime in ("now", "later", "never"):
            got = FixedRegimeController(regime).regimes(self.rows)
            self.assertEqual(set(got.values()), {regime})
        with self.assertRaisesRegex(TimingError, "unknown"):
            FixedRegimeController("sometimes").regimes(self.rows)


class TestMatchingReport(unittest.TestCase):
    def test_matched_controllers_pass(self):
        report = matching_report([ProposedTiming(), RepeatedMyopicComparator(), BavarInspiredVOI()])
        self.assertTrue(report["matched_decision_class"])

    def test_mismatched_capacity_fails(self):
        with self.assertRaisesRegex(TimingError, "matching failed"):
            matching_report([ProposedTiming(l2=0.01), RepeatedMyopicComparator(l2=0.5)])

    def test_mismatched_folds_fails(self):
        with self.assertRaisesRegex(TimingError, "matching failed"):
            matching_report([ProposedTiming(n_folds=5), BavarInspiredVOI(n_folds=3)])


if __name__ == "__main__":
    unittest.main()
