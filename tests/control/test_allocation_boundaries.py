import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment_scaffold/src'))
from causal_branch.control.allocation import ConservativeSelector, streaming_threshold

class AllocationBoundaries(unittest.TestCase):
    def test_streaming_excludes_unavailable_high_score(self):
        np.testing.assert_array_equal(streaming_threshold(np.array([10., 2.]), 1., np.array([False, True])), [False, True])

    def test_paired_contrast_width_and_two_endpoint_allocation(self):
        gains = {'p': np.zeros(20)}
        result = ConservativeSelector(delta=.05).select(gains, {'p': np.zeros(20)})
        self.assertEqual(result.per_endpoint_delta, .025)
        radius = 2 * np.sqrt(np.log(40) / 40)
        self.assertAlmostEqual(result.bounds['p'], -radius)
        self.assertAlmostEqual(result.degradation_upper['p'], radius)

    def test_missing_harm_data_cannot_pass_requested_harm_gate(self):
        result = ConservativeSelector().select({'p': np.ones(10000)}, {})
        self.assertTrue(result.fallback)
        self.assertIsNone(result.chosen)

    def test_identical_gain_with_harm_bound_is_wider(self):
        selector = ConservativeSelector()
        gains = {'p': np.zeros(20)}
        self.assertLess(selector.select(gains, {'p': np.zeros(20)}).bounds['p'], selector.select(gains).bounds['p'])

if __name__ == '__main__':
    unittest.main()
