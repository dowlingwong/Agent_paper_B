"""B3: population-scoped replay allowance — no pointwise gate, union bound, audit.

Engineering counterexamples for RUNBOOK §12.2.  Each test fails if the
population allowance is weakened into a per-checkpoint gate or if a fixed
policy's bound is not shifted by exactly 2p.
"""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

import math  # noqa: E402

from causal_branch.control import bounds as bnds  # noqa: E402
from causal_branch.control.allocation import ConservativeSelector  # noqa: E402
from causal_branch.control.replay_validity import (  # noqa: E402
    PROVENANCE_KINDS,
    CheckpointAllowance,
    ReplayValidityError,
    audit_upper_confidence_bound,
    audits_needed_for_bound,
    p_grid_report,
    path_allowance,
    population_lower_bound,
    simultaneous_family_bounds,
)

GRID = [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]


class TestPopulationBound(unittest.TestCase):
    def test_p_zero_reproduces_sampling_bound(self):
        self.assertEqual(population_lower_bound(0.37, 0.0), 0.37)
        self.assertEqual(population_lower_bound(-0.2, 0.0), -0.2)

    def test_shift_is_exactly_two_p_and_monotone(self):
        lcb = 0.5
        self.assertAlmostEqual(population_lower_bound(lcb, 0.02), 0.5 - 0.04)
        values = [population_lower_bound(lcb, p) for p in GRID]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_bound_is_clipped_to_contrast_range(self):
        self.assertEqual(population_lower_bound(-0.5, 0.5), -1.0)
        self.assertEqual(population_lower_bound(0.9, 0.0), 0.9)

    def test_probability_range_enforced(self):
        for bad in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ReplayValidityError):
                population_lower_bound(0.1, bad)


class TestPointwiseGateRefused(unittest.TestCase):
    def test_array_valued_lcb_is_refused(self):
        with self.assertRaisesRegex(ReplayValidityError, "pointwise"):
            population_lower_bound(np.array([0.1, 0.2, 0.3]), 0.02)

    def test_list_valued_lcb_is_refused(self):
        with self.assertRaisesRegex(ReplayValidityError, "pointwise"):
            population_lower_bound([0.1, 0.2], 0.02)


class TestPlantedDefectWorld(unittest.TestCase):
    def setUp(self):
        # A fixed policy with a positive sampling bound but a planted
        # discrepancy mass large enough to make the intended gain negative.
        # Width-2 radius at alpha=.05, n=1000 is ~.0774, so a mean of .1 gives
        # a sampling LCB ~.0226 > 0 while 2p=.04 pushes it below zero.
        self.family = {"policy": np.full(1000, 0.1)}

    def test_sampling_only_certifies_but_intended_gain_is_negative(self):
        p = 0.02
        sampling, _ = simultaneous_family_bounds(self.family, 0.05, 0.0)
        self.assertIn("policy", sampling)
        self.assertGreater(sampling["policy"], 0.0)
        # The planted discrepancy shifts the intended population gain below 0.
        self.assertLess(sampling["policy"] - 2.0 * p, 0.0)

    def test_two_p_bound_abstains(self):
        qualifying, bounds = simultaneous_family_bounds(self.family, 0.05, 0.02)
        self.assertEqual(qualifying, {})
        self.assertLessEqual(bounds["policy"], 0.0)

    def test_largest_surviving_p_is_adjusted_and_finite(self):
        report = p_grid_report(self.family, GRID, alpha=0.05)
        # sampling bound ~0.0226 > 0; 2p kills it at p=0.02.
        self.assertEqual(report["policy"], 0.01)


class TestPathAllowanceUnionBound(unittest.TestCase):
    def test_union_bound(self):
        a = CheckpointAllowance(0.01, "sensitivity_assumption")
        b = CheckpointAllowance(0.02, "sensitivity_assumption")
        self.assertAlmostEqual(path_allowance(a, b), 0.03)

    def test_union_bound_saturates_at_one(self):
        a = CheckpointAllowance(0.6, "sensitivity_assumption")
        b = CheckpointAllowance(0.6, "sensitivity_assumption")
        self.assertEqual(path_allowance(a, b), 1.0)

    def test_refuses_missing_provenance_or_value(self):
        good = CheckpointAllowance(0.01, "validated_evidence")
        with self.assertRaisesRegex(ReplayValidityError, "provenance"):
            path_allowance(CheckpointAllowance(0.01, None), good)
        with self.assertRaisesRegex(ReplayValidityError, "provenance"):
            path_allowance(CheckpointAllowance(0.01, "guessed"), good)
        with self.assertRaisesRegex(ReplayValidityError, "no declared p"):
            path_allowance(CheckpointAllowance(None, "validated_evidence"), good)


class TestAuditArithmetic(unittest.TestCase):
    def test_twenty_four_zero_miss_audits_give_point_117(self):
        self.assertAlmostEqual(audit_upper_confidence_bound(24), 0.11735, places=4)

    def test_149_audits_reach_the_point_02_bound(self):
        self.assertEqual(audits_needed_for_bound(0.02), 149)
        self.assertLessEqual(audit_upper_confidence_bound(149), 0.02)
        self.assertGreater(audit_upper_confidence_bound(148), 0.02)

    def test_zero_miss_only(self):
        with self.assertRaises(ReplayValidityError):
            audit_upper_confidence_bound(10, n_misses=1)


class TestSharedConfidenceRadius(unittest.TestCase):
    def test_radius_is_width_two(self):
        n, alpha = 50, 0.05 / 3
        expected = 2.0 * math.sqrt(math.log(1.0 / alpha) / (2.0 * n))
        self.assertAlmostEqual(bnds.hoeffding_radius(n, alpha), expected)
        # a planted width-1 radius is half and must not be the default
        self.assertAlmostEqual(bnds.hoeffding_radius(n, alpha, width=1.0), expected / 2)
        self.assertNotAlmostEqual(bnds.hoeffding_radius(n, alpha, width=1.0),
                                  bnds.hoeffding_radius(n, alpha))

    def test_replay_validity_and_allocation_agree(self):
        values = np.linspace(-1.0, 1.0, 40)
        alpha = 0.05
        n = len(values)
        expected = float(values.mean()) - bnds.hoeffding_radius(n, alpha)
        _, bounds = simultaneous_family_bounds({"a": values}, alpha, 0.0)
        self.assertAlmostEqual(bounds["a"], expected)
        selector = ConservativeSelector(delta=alpha, harm_tolerance=1.0)
        self.assertAlmostEqual(selector.select({"a": values}).bounds["a"], expected)


class TestProvenanceKinds(unittest.TestCase):
    def test_accepted_kinds(self):
        self.assertEqual(
            set(PROVENANCE_KINDS),
            {"sensitivity_assumption", "validated_evidence"},
        )


class TestInterferenceTax(unittest.TestCase):
    """N2/N3: the batch-allocated population tax is 2 * m * p_path."""

    def test_contrast_bound_arithmetic(self):
        from causal_branch.control.replay_validity import population_contrast_lower_bound
        self.assertAlmostEqual(population_contrast_lower_bound(0.30, 0.04, m=3), 0.30 - 0.24)
        self.assertEqual(population_contrast_lower_bound(0.30, 0.0, m=3), 0.30)
        self.assertEqual(population_contrast_lower_bound(-0.9, 0.5, m=3), -1.0)  # clipped
        for bad in (0, -1, 1.5, True):
            with self.assertRaises(ReplayValidityError):
                population_contrast_lower_bound(0.3, 0.02, m=bad)
        with self.assertRaises(ReplayValidityError):
            population_contrast_lower_bound(np.array([0.3, 0.2]), 0.02, m=3)

    def test_grid_with_interference_and_two_checkpoints_is_stricter(self):
        from causal_branch.control.replay_validity import p_grid_report
        gains = {"c": np.full(400, 0.30)}
        grid = (0.0, 0.005, 0.01, 0.02, 0.05, 0.10)
        per_root = p_grid_report(gains, grid, alpha=0.05)["c"]
        batch = p_grid_report(gains, grid, alpha=0.05, m=3, checkpoints=2)["c"]
        self.assertIsNotNone(per_root)
        self.assertLess(batch if batch is not None else -1.0, per_root)
        # p = 0.02 per checkpoint -> p_path 0.04 -> tax 0.24 at m = 3
        self.assertLessEqual(batch, 0.01)
        with self.assertRaises(ReplayValidityError):
            p_grid_report(gains, grid, checkpoints=3)


if __name__ == "__main__":
    unittest.main()
