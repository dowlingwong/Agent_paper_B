"""Tests for T5's shared-component noise model (ENGINEERING_ONLY). AI-assisted (Claude, subagent), 22 Nov 2026.

unittest style; fast (a few seconds). Model: docs/r1/theory/T5_SHARED_NOISE_20261122.md and the comment block
"Shared-component noise model" in r1/theory/simulate_t4.py.
"""
from __future__ import annotations

import math
import unittest

import numpy as np

from r1.theory.simulate_t4 import (Node, Policy, PType, Scenario, effective_rho, shared_correlations, shared_rho_w,
                                   shared_share_for_partial, simulate)

NODE = Node("test", sigma=0.0125, rho_local=0.82, rho_struct=0.55, split_share=0.59)
TYPES = (PType("dup", 0.45, 0.0, 0.0, pi=1.0), PType("bad", 0.20, -0.012, 0.008),
         PType("good", 0.15, 0.003, 0.005), PType("struct", 0.20, -0.006, 0.014, kind="structural", bold=True))
LOCAL = (PType("a", 0.5, -0.002, 0.006), PType("b", 0.5, 0.001, 0.004))


def _partial(par, a, b):
    C = np.corrcoef(np.stack([par, a, b]))
    return C[0, 1], (C[1, 2] - C[0, 1] * C[0, 2]) / math.sqrt((1 - C[0, 1] ** 2) * (1 - C[0, 2] ** 2))


class SharedHelpers(unittest.TestCase):
    def test_closed_form_and_inverse(self):
        for rho in (0.55, 0.7, 0.82, 0.9):
            for p in (0.05, 0.2, 0.37):
                if p > rho / (1 + rho):
                    continue
                s = shared_share_for_partial(p, rho)
                c = shared_correlations(rho, rho, s)
                self.assertAlmostEqual(c["sibling_partial"], p, places=10)
                self.assertAlmostEqual(c["sibling_partial_closed_form"], p, places=10)
                self.assertAlmostEqual(c["marginal_parent_child_a"], rho, places=12)
        with self.assertRaises(ValueError):
            shared_share_for_partial(0.51, 0.82)          # max reachable at rho = 0.82 is 0.82 / 1.82 = 0.4505

    def test_record_limit_and_infeasible_kind(self):
        c = shared_correlations(0.82, 0.55, 0.0)
        self.assertEqual(c["sibling_partial"], 0.0)       # s = 0: the parent screens off its children
        self.assertEqual(float(shared_rho_w(0.55, 0.7)), 0.0)
        self.assertAlmostEqual(float(effective_rho(0.55, 0.7)), 0.7)
        self.assertFalse(shared_correlations(0.82, 0.55, 0.7)["feasible"])

    def test_helper_against_direct_sampling(self):
        """(i) marginal parent-child correlation and (ii) sibling partial correlation, from the generative model
        e = u + w drawn directly (independent of simulate())."""
        rng = np.random.default_rng(1)
        n, s, sig = 400_000, 0.6, 1.0
        for ra_t, rb_t in ((0.82, 0.82), (0.82, 0.65)):
            c = shared_correlations(ra_t, rb_t, s)
            u = rng.normal(0, math.sqrt(s) * sig, n)
            w0 = rng.normal(0, math.sqrt(1 - s) * sig, n)
            wa = c["r_w_a"] * w0 + math.sqrt(1 - c["r_w_a"] ** 2) * rng.normal(0, math.sqrt(1 - s) * sig, n)
            wb = c["r_w_b"] * w0 + math.sqrt(1 - c["r_w_b"] ** 2) * rng.normal(0, math.sqrt(1 - s) * sig, n)
            par, a, b = u + w0, u + wa, u + wb
            ca = np.corrcoef(par, a)[0, 1]
            cb = np.corrcoef(par, b)[0, 1]
            _, part = _partial(par, a, b)
            self.assertAlmostEqual(ca, c["marginal_parent_child_a"], delta=0.004)
            self.assertAlmostEqual(cb, c["marginal_parent_child_b"], delta=0.004)
            self.assertAlmostEqual(part, c["sibling_partial"], delta=0.006)


class SharedSimulator(unittest.TestCase):
    def test_s_zero_reproduces_record_bit_for_bit(self):
        scn = Scenario("t", NODE, TYPES, noise="record")
        for pol in (Policy("rho", prior="zero", rules=False), Policy("o", prior="oracle", screen=True, g=0.0005)):
            a = simulate(scn, pol, 15, 30, 1500, 4)
            b = simulate(scn.with_(noise="shared", shared_share=0.0), pol, 15, 30, 1500, 4)
            self.assertTrue(np.array_equal(a["_J"], b["_J"]))
            self.assertEqual(a["p9"], b["p9"])
            self.assertEqual(a["record_bias_end"], b["record_bias_end"])

    def test_simulator_correlations_match_helper(self):
        """No keeps (threshold far up): the incumbent stays the initial configuration, and the candidates of
        calls 1 and 2 are siblings. Check (i) and (ii) on the simulator's own draws."""
        s = shared_share_for_partial(0.37, 0.82)
        scn = Scenario("t", NODE, LOCAL, noise="shared", shared_share=s)
        r = simulate(scn, Policy("nokeep", prior="zero", rules=False, theta0=1e6), 3, 3, 150_000, 9, trace=2)
        tr = r["_trace"]
        self.assertEqual(r["keeps"], 0.0)
        self.assertTrue(np.array_equal(tr[0, 0], tr[1, 0]))
        c01, part = _partial(tr[0, 0], tr[0, 1], tr[1, 1])
        self.assertAlmostEqual(c01, 0.82, delta=0.005)
        self.assertAlmostEqual(part, 0.37, delta=0.01)
        sd = np.std(tr[0, 0])
        self.assertAlmostEqual(sd, NODE.sigma, delta=0.0002)        # per-run sd unchanged
        self.assertAlmostEqual(np.std(tr[0, 1] - tr[0, 0]), NODE.sigma_d("local"), delta=0.0001)  # paired sd unchanged

    def test_kernel_free_inequality_every_model(self):
        for noise, s in (("iid", 0.0), ("record", 0.0), ("shared", 0.55), ("shared", 0.79)):
            scn = Scenario("t", NODE, TYPES, noise=noise, shared_share=s)
            for pol in (Policy("rho", prior="zero", rules=False), Policy("o", prior="oracle")):
                k = simulate(scn, pol, 20, 40, 1500, 6)["kfree"]
                self.assertGreater(k["keeps"], 0)
                self.assertEqual(k["viol_general"], 0)
                self.assertEqual(k["viol_p09"], 0)
                self.assertEqual(k["null_viol_rise"], 0)
                if pol.prior == "zero":
                    self.assertEqual(k["keeps_t_neg"], 0)

    def test_prop9_formula_fails_after_keeps_under_shared(self):
        """Under ``record`` T4 Proposition 9's formula holds by construction; under ``shared`` it does not after a
        keep (the later-keep residual is clearly non-zero)."""
        rec = simulate(Scenario("t", NODE, LOCAL, noise="record"), Policy("rho", prior="zero", rules=False),
                       30, 30, 4000, 7)["p9_by_keep"]
        sh = simulate(Scenario("t", NODE, LOCAL, noise="shared", shared_share=0.79),
                      Policy("rho", prior="zero", rules=False), 30, 30, 4000, 7)["p9_by_keep"]
        self.assertLess(abs(rec["later"]["mean_residual"]), 4 * rec["later"]["se_residual"] + 1e-6)
        self.assertGreater(abs(sh["later"]["mean_residual"]), 10 * sh["later"]["se_residual"])

    def test_threshold_correction_runs_and_is_noop_for_iid(self):
        scn = Scenario("t", NODE, TYPES, noise="iid")
        a = simulate(scn, Policy("o", prior="oracle"), 15, 30, 1000, 3)
        b = simulate(scn, Policy("o", prior="oracle", ecorr="known"), 15, 30, 1000, 3)
        self.assertTrue(np.array_equal(a["_J"], b["_J"]))
        scn = Scenario("t", NODE, TYPES, noise="shared", shared_share=0.79)
        a = simulate(scn, Policy("o", prior="oracle"), 15, 30, 3000, 3)
        b = simulate(scn, Policy("o", prior="oracle", ecorr="known"), 15, 30, 3000, 3)
        t = simulate(scn, Policy("o", prior="oracle", ecorr="table", ecorr_m=(0.0,) * 4, ecorr_v=(0.0,) * 4),
                     15, 30, 3000, 3)
        # a zero table with zero variance uses the fresh sd s_f < paired sd, so it differs from t*; both run
        self.assertTrue(np.isfinite(t["gain"][0]))
        # knowing the incumbent's error lowers the mean threshold (the record is selected high) and adds keeps
        self.assertLess(b["mean_threshold_executed"], a["mean_threshold_executed"])
        self.assertGreater(b["keeps"], a["keeps"])


if __name__ == "__main__":
    unittest.main()
