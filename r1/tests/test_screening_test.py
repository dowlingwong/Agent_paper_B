"""Synthetic checks of the ancestor-descendant screening test (ENGINEERING_ONLY; AI-assisted, Claude subagent).

Kernel model (s = 0) -> pooled partial near 0; shared-component model -> pooled partial clearly positive and near its
closed form. No repository data is read.
"""
from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from r1.noise import screening_test as st


def _clusters(n_inst, length, k, s, rho, seed):
    rng = np.random.default_rng(seed)
    return {f"i{j}": {"chains": [list(st.simulate_chain(length, k, s, rho, rng, means=rng.normal(0, 5, length)))]}
            for j in range(n_inst)}


class ClosedForms(unittest.TestCase):
    def test_kernel_partial_is_zero(self):
        for r1, r2 in ((0.8, 0.8), (0.3, 0.9), (0.0, 0.5)):
            self.assertAlmostEqual(st.shared_lineage_partial(0.0, r1, r2), 0.0, places=12)

    def test_t5_calibration_values(self):
        # T5_SHARED_NOISE_20261122 §2: at rho = 0.82 the shares 0.7082 / 0.7891 give partial 0.24 / 0.37
        for s, p in ((0.7082, 0.24), (0.7891, 0.37)):
            r = st.link_coefficient(0.82, s)
            self.assertAlmostEqual(st.shared_lineage_partial(s, r, r), p, delta=0.005)

    def test_link_coefficient_reproduces_rho(self):
        for s in (0.0, 0.3, 0.7):
            r = st.link_coefficient(0.82, s)
            self.assertAlmostEqual(s + (1 - s) * r, 0.82, places=12)


class TriplePartial(unittest.TestCase):
    def test_matches_regression_residual_correlation(self):
        rng = np.random.default_rng(1)
        g, p, c = rng.normal(size=(3, 30))
        v, why = st.triple_partial(g, p, c)
        self.assertEqual(why, "ok")
        X = np.column_stack([np.ones(30), p])
        rg = g - X @ np.linalg.lstsq(X, g, rcond=None)[0]
        rc = c - X @ np.linalg.lstsq(X, c, rcond=None)[0]
        self.assertAlmostEqual(v, float(np.corrcoef(rg, rc)[0, 1]), places=10)

    def test_invariant_to_configuration_means_and_scale(self):
        rng = np.random.default_rng(2)
        g, p, c = rng.normal(size=(3, 8))
        a, _ = st.triple_partial(g, p, c)
        b, _ = st.triple_partial(3 * g + 1, 0.5 * p - 2, 7 * c + 0.3)
        self.assertAlmostEqual(a, b, places=10)

    def test_ineligible_triples(self):
        rng = np.random.default_rng(3)
        g, c = rng.normal(size=(2, 6))
        self.assertEqual(st.triple_partial(g, g * 2 + 1, c)[1], "near_singular")
        self.assertEqual(st.triple_partial(g, np.ones(6), c)[1], "zero_spread")
        self.assertEqual(st.triple_partial(g, c, g)[1], "identical_members")
        self.assertEqual(st.triple_partial(g[:3], c[:3], g[:3] + 1)[1], "too_few_seeds")
        self.assertIsNone(st.triple_partial(g, g * 2 + 1, c)[0])


class PooledTest(unittest.TestCase):
    def test_kernel_model_gives_partial_near_zero(self):
        cl = _clusters(400, 4, 10, 0.0, 0.82, seed=10)
        parts, why = st.cluster_partials(cl)
        est, n = st.pooled(parts)
        self.assertEqual(n, 800)
        self.assertLess(abs(est), 0.05)
        lo, hi = st.cluster_bootstrap(parts)
        self.assertLess(lo, 0.0 + 0.05)
        self.assertEqual(st.decide(lo, hi), "NO_SHARED")

    def test_shared_model_gives_positive_partial(self):
        s = 0.7891
        cl = _clusters(400, 4, 30, s, 0.82, seed=11)
        parts, _ = st.cluster_partials(cl)
        est, _ = st.pooled(parts)
        target = st.shared_lineage_partial(s, st.link_coefficient(0.82, s), st.link_coefficient(0.82, s))
        self.assertGreater(est, 0.25)
        self.assertAlmostEqual(est, target, delta=0.06)
        lo, hi = st.cluster_bootstrap(parts)
        self.assertEqual(st.decide(lo, hi), "SHARED")

    def test_shared_model_positive_at_five_seeds(self):
        # the Track S geometry: five seeds per instance; the small-sample partial is attenuated but positive
        cl = _clusters(600, 4, 5, 0.7891, 0.82, seed=12)
        est, _ = st.pooled(st.cluster_partials(cl)[0])
        self.assertGreater(est, 0.15)

    def test_seed_bootstrap_shared_seeds(self):
        rng = np.random.default_rng(13)
        u = rng.normal(0, math.sqrt(0.0), 40)
        triples = []
        for _ in range(30):
            ch = st.simulate_chain(3, 40, 0.0, 0.82, rng, u=u)
            triples.append((ch[0], ch[1], ch[2]))
        lo, hi = st.seed_bootstrap(triples, n_boot=300)
        est = float(np.mean([st.triple_partial(*t)[0] for t in triples]))
        self.assertLessEqual(lo, est)
        self.assertGreaterEqual(hi, est)

    def test_decide(self):
        self.assertEqual(st.decide(0.11, 0.5), "SHARED")
        self.assertEqual(st.decide(-0.3, 0.09), "NO_SHARED")
        self.assertEqual(st.decide(0.05, 0.2), "INCONCLUSIVE")
        self.assertEqual(st.decide(float("nan"), 0.2), "INCONCLUSIVE")


class Chains(unittest.TestCase):
    def test_dedupe_and_triples(self):
        a, b, c = np.arange(5.0), np.arange(5.0) ** 2, np.arange(5.0) ** 3
        self.assertEqual(len(st.dedupe_consecutive([a, a, b, b, c])), 3)
        self.assertEqual(st.chain_triples(5), [(0, 1, 2), (1, 2, 3), (2, 3, 4)])
        self.assertEqual(len(st.chain_triples(5, "all")), 10)
        self.assertEqual(st.chain_triples(2), [])

    def test_tracks_loader_on_synthetic_directory(self):
        rng = np.random.default_rng(20)
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            roots, trunc, runs = [], [], []
            c0_vals = {}
            for i in range(3):
                inst = f"node__s{30500 + i}"
                seeds = [200000 + 20 * i + k for k in range(5)]
                ch = st.simulate_chain(4, 5, 0.0, 0.8, rng)
                # calibration order: the first audited proposal's candidate, then its incumbent c0
                for s, v in zip(seeds, ch[1]):
                    runs.append({"node": "node", "salt": 0, "config_hash": f"X{i}", "seed": s, "metric": float(v)})
                for s, v in zip(seeds, ch[0]):
                    runs.append({"node": "node", "salt": 0, "config_hash": "C0", "seed": s, "metric": float(v)})
                c0_vals[inst] = ch[0]
                decisions = [{"index": 3, "action": "keep"}, {"index": 9, "action": "keep"}, {"index": 15, "action": "keep"}]
                for pol, rep in (("a2u", 0), ("static:1,0", 0), ("static:1,0", 1)):
                    rid = f"{inst}__{pol}__r{rep}"
                    roots.append({"root_id": rid, "instance_id": inst, "status": "ok", "policy": pol, "rep": rep,
                                  "decisions": decisions})
                    for W, t, j in ((8, 8, 1), (10, 10, 2), (12, 12, 2), (20, 40, 3)):
                        trunc.append({"root_id": rid, "instance_id": inst, "W": W, "trials": t, "audit_seeds": seeds,
                                      "y_terminal_per_seed": [float(x) for x in ch[j]], "policy": pol, "rep": rep})
            for name, rows in (("roots.jsonl", roots), ("s05b_truncated.jsonl", trunc), ("audit_runs.jsonl", runs)):
                (d / name).write_text("".join(json.dumps(r) + "\n" for r in rows))
            self.assertEqual(st.identify_c0(d), "C0")
            lengths = st.tracks_chain_lengths_meta(d, True)
            self.assertEqual(set(lengths.values()), {4})          # c0, I_8, I_10 (= I_12), I_20
            cl = st.load_tracks(d, "C0")
            self.assertEqual(len(cl), 3)
            for inst, item in cl.items():
                self.assertEqual(len(item["chains"]), 1)
                self.assertEqual(len(item["chains"][0]), 4)
                np.testing.assert_allclose(item["chains"][0][0], c0_vals[inst])
            both = st.load_tracks(d, "C0", roots_filter=lambda r: r["rep"] in (0, 1))
            self.assertTrue(all(len(v["chains"]) == 1 for v in both.values()))   # identical trajectories count once
            # an instance whose second hash differs makes c0 unidentified (fail closed)
            runs.insert(0, {"node": "node", "salt": 0, "config_hash": "Y", "seed": 200000, "metric": 0.5})
            (d / "audit_runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))
            self.assertIsNone(st.identify_c0(d))


if __name__ == "__main__":
    unittest.main()
