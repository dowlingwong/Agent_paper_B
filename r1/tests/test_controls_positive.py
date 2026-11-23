"""Synthetic-data tests of r1/noise/controls_positive.py (R1-CONTROLS-ROW positive control). AI-assisted (Claude)."""
from __future__ import annotations

import itertools
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy import stats

from r1.noise import controls_positive as C


def _write_run(root: Path, node_diffs: dict, base_metric: float = 0.9, sd_base: float = 0.01, seed: int = 1,
               drop=None) -> None:
    """A minimal accepted-run directory: runs.jsonl (joint condition), edits.json and an e1_report-style summary."""
    rng = np.random.default_rng(seed)
    rows, edits, summary = [], {}, {"label": "PILOT", "nodes": {}}
    for node, diffs in node_diffs.items():
        base = base_metric + rng.normal(0, sd_base, len(C.JOINT_SEEDS))
        edits[node] = [{"symbol": f"P{i}", "old": "1", "new": str(i + 1)} for i in range(len(diffs))]
        sedits = []
        for i, s in enumerate(C.JOINT_SEEDS):
            rows.append({"node": node, "config": "c0", "condition": "joint", "train_seed": s, "split_seed": s,
                         "metric": float(base[i]), "success": True})
        for k, d in enumerate(diffs, start=1):
            d = np.asarray(d, float)
            for i, s in enumerate(C.JOINT_SEEDS):
                if drop == (node, f"c{k}", s):
                    continue
                rows.append({"node": node, "config": f"c{k}", "condition": "joint", "train_seed": s,
                             "split_seed": s, "metric": float(base[i] + d[i]), "success": True})
            dd = np.array([(base[i] + d[i]) - base[i] for i in range(len(C.JOINT_SEEDS))])
            sedits.append({"edit": f"P{k - 1} 1 -> {k}", "delta_hat_J": float(dd.mean()),
                           "sd_joint": float(dd.std(ddof=1)), "material": True})
        summary["nodes"][node] = {"edits": sedits}
    root.mkdir(parents=True, exist_ok=True)
    (root / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (root / "edits.json").write_text(json.dumps(edits))
    (root / "summary.json").write_text(json.dumps(summary))


class SubsetTests(unittest.TestCase):
    def test_exhaustive_k5_is_every_combination_once(self):
        sub = C.all_subsets(30, 5)
        self.assertEqual(sub.shape, (math.comb(30, 5), 5))
        self.assertEqual(len({tuple(r) for r in sub.tolist()}), math.comb(30, 5))
        self.assertEqual(C.subsets_for(30, 5, 10, 1)[1], "exhaustive")
        self.assertEqual(C.subsets_for(30, 10, 10, 1)[1], "monte_carlo")

    def test_random_subsets_are_without_replacement_and_reproducible(self):
        a = C.random_subsets(30, 10, 5000, 7)
        b = C.random_subsets(30, 10, 5000, 7)
        self.assertTrue(np.array_equal(a, b))
        self.assertTrue(all(len(set(r)) == 10 for r in a.tolist()))
        self.assertTrue(((a >= 0) & (a < 30)).all())
        counts = np.bincount(a.ravel(), minlength=30) / a.shape[0]  # each seed in about 10/30 of subsets
        self.assertLess(np.abs(counts - 1 / 3).max(), 0.03)


class DetectionTests(unittest.TestCase):
    def test_vectorised_readings_equal_a_naive_loop(self):
        rng = np.random.default_rng(3)
        d = rng.normal(0.004, 0.006, 9)
        sub = C.all_subsets(9, 4)
        delta_n = 0.002
        got = C.detection(d, sub, delta_n, 1, "exhaustive")
        hits = {r: 0 for r in C.READINGS}
        tc = stats.t.ppf(0.95, 3)
        for idx in itertools.combinations(range(9), 4):
            x = d[list(idx)]
            m = x.mean()
            t = stats.ttest_1samp(x, 0.0, alternative="greater").statistic
            hits["R0"] += m > 0
            hits["Rdelta"] += m > delta_n
            hits["Rt"] += t > tc
            hits["Rdelta_t"] += (m > delta_n) and (t > tc)
        n = math.comb(9, 4)
        for r in C.READINGS:
            self.assertAlmostEqual(got[r]["p"], hits[r] / n, places=12)
            self.assertEqual(got[r]["mc_error"], 0.0)

    def test_negative_effect_is_read_in_its_own_direction(self):
        rng = np.random.default_rng(4)
        d = rng.normal(0.01, 0.004, 30)
        sub = C.all_subsets(30, 5)
        pos = C.detection(d, sub, 0.002, 1, "exhaustive")
        neg = C.detection(-d, sub, 0.002, -1, "exhaustive")
        for r in C.READINGS:
            self.assertEqual(pos[r]["p"], neg[r]["p"])

    def test_constant_differences(self):
        sub = C.all_subsets(30, 5)
        up = C.detection(np.full(30, 0.01), sub, 0.002, 1, "exhaustive")
        for r in C.READINGS:
            self.assertEqual(up[r]["p"], 1.0)  # sd_K = 0 and mean > 0 counts as a detection
        small = C.detection(np.full(30, 0.001), sub, 0.002, 1, "exhaustive")
        self.assertEqual(small["Rdelta"]["p"], 0.0)
        self.assertEqual(small["Rt"]["p"], 1.0)
        self.assertEqual(small["Rdelta_t"]["p"], 0.0)
        zero = C.detection(np.zeros(30), sub, 0.002, 1, "exhaustive")
        for r in C.READINGS:
            self.assertEqual(zero[r]["p"], 0.0)

    def test_symmetric_null_population_gives_equal_tails(self):
        half = np.linspace(0.001, 0.015, 15)
        d = np.concatenate([half, -half])
        res = C.detection(d, C.all_subsets(30, 5), 0.002, 1, "exhaustive")
        m, _ = C.subset_statistics(d, C.all_subsets(30, 5), 1)
        self.assertEqual(int((m > 1e-15).sum()), int((m < -1e-15).sum()))
        self.assertAlmostEqual(res["R0"]["p"], 0.5, delta=0.05)

    def test_monte_carlo_matches_the_finite_population_normal_approximation(self):
        rng = np.random.default_rng(5)
        d = rng.normal(0.005, 0.008, 30)
        eff = C.effect(d)
        sub = C.random_subsets(30, 10, 40000, 11)
        res = C.detection(d, sub, 0.002, 1, "monte_carlo")
        a = C.analytic(eff, 0.002, 10, 30)
        self.assertLess(abs(res["Rdelta"]["p"] - a["Rdelta_fpc"]), 0.03)
        self.assertGreater(res["Rdelta"]["mc_error"], 0.0)
        self.assertLess(res["Rdelta"]["mc_error"], 0.003)
        # a fresh-seed audit has more variance than the resampling scheme: closer to 1/2 when the effect > delta_n
        self.assertLess(a["Rdelta_super"], a["Rdelta_fpc"])
        self.assertLessEqual(a["Rdelta_super_at_mean_minus_2se"], a["Rdelta_super"])
        self.assertGreaterEqual(a["Rdelta_super_at_mean_plus_2se"], a["Rdelta_super"])

    def test_noncentral_t_power_matches_simulation(self):
        rng = np.random.default_rng(6)
        mu, sd, k = 0.006, 0.008, 10
        eff = {"mean": mu, "sd": sd, "se": sd / math.sqrt(30), "n": 30}
        x = rng.normal(mu, sd, (100000, k))
        t = x.mean(1) / (x.std(1, ddof=1) / math.sqrt(k))
        sim = float((t > stats.t.ppf(0.95, k - 1)).mean())
        self.assertLess(abs(C.analytic(eff, 0.002, k, 30)["Rt_super_nct"] - sim), 0.01)

    def test_monte_carlo_check_against_exhaustive(self):
        rng = np.random.default_rng(9)
        sub = C.all_subsets(30, 5)
        cases = []
        for mu in (0.006, -0.003, 0.0):
            d = rng.normal(mu, 0.006, 30)
            sgn = C.direction_of(d.mean())
            cases.append((d, 0.002, sgn, C.detection(d, sub, 0.002, sgn, "exhaustive")))
        chk = C.monte_carlo_check(cases, 5, 20000, 1)
        self.assertEqual(chk["cells"], 3)
        for r in C.READINGS:
            self.assertLess(chk[r]["max_abs_difference"], 0.02)
            self.assertLess(chk[r]["max_difference_in_mc_errors"], 5.0)
        mc_cases = [(d, dn, s, dict(det, method="monte_carlo")) for d, dn, s, det in cases]
        self.assertIsNone(C.monte_carlo_check(mc_cases, 5, 100, 1))

    def test_classify(self):
        self.assertEqual(C.classify(0.010, 0.001, 0.002), "above")
        self.assertEqual(C.classify(-0.010, 0.001, 0.002), "above")
        self.assertEqual(C.classify(0.0001, 0.0002, 0.002), "below")
        self.assertEqual(C.classify(0.0025, 0.001, 0.002), "near")
        self.assertEqual(C.direction_of(0.0), 1)
        self.assertEqual(C.direction_of(-1e-9), -1)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        rng = np.random.default_rng(8)
        self.diffs = {"digits_mlp": [rng.normal(0.008, 0.006, 30), rng.normal(-0.015, 0.011, 30),
                                     np.zeros(30)],
                      "openml_sonar": [rng.normal(0.0002, 0.0007, 30)]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_end_to_end_on_a_synthetic_run(self):
        run_dir = self.root / "run"
        _write_run(run_dir, self.diffs)
        noise = {"digits_mlp": {"delta_n": 0.002, "sigma_node": 0.0066},
                 "openml_sonar": {"delta_n": 0.0032, "sigma_node": 0.03}}
        orig = C.node_noise
        C.node_noise = lambda path: noise
        try:
            out = self.root / "out"
            res = C.run(run_dir, out, draws=3000, seed=1, expected_sha=None)
            res2 = C.run(run_dir, None, draws=3000, seed=1, expected_sha=None)
        finally:
            C.node_noise = orig
        self.assertEqual(json.loads((out / "controls_positive.json").read_text())["nodes"], res["nodes"])
        self.assertTrue((out / "tables.md").read_text().startswith("# Positive control"))
        self.assertEqual(res["nodes"], res2["nodes"])  # deterministic
        self.assertEqual(sorted(res["nodes"]), ["digits_mlp", "openml_sonar"])
        self.assertIn("openml_climate", res["not_determined"])
        self.assertEqual(res["nodes"]["openml_sonar"]["start_configuration"], "pre_repair")
        self.assertEqual(res["nodes"]["digits_mlp"]["start_configuration"], "current")
        e1, e2, e3 = res["nodes"]["digits_mlp"]["edits"]
        self.assertEqual((e1["kind"], e2["kind"], e3["kind"]), ("improvement", "harm", "zero"))
        self.assertAlmostEqual(e1["mean"], float(np.mean(self.diffs["digits_mlp"][0])), places=10)
        self.assertEqual(e1["vs_delta_n"], "above")
        self.assertEqual(res["nodes"]["openml_sonar"]["edits"][0]["vs_delta_n"], "below")
        self.assertGreater(e1["detection"]["10"]["Rdelta"]["p"], 0.95)
        self.assertGreater(e2["detection"]["10"]["Rdelta"]["p"], 0.95)
        self.assertEqual(e3["detection"]["10"]["Rdelta"]["p"], 0.0)
        self.assertEqual(e1["detection"]["5"]["method"], "exhaustive")
        self.assertEqual(e1["detection"]["10"]["method"], "monte_carlo")
        self.assertIn("monte_carlo_vs_exhaustive_K5", res["checks"])
        self.assertNotIn("monte_carlo_vs_exhaustive_K10", res["checks"])

    def test_sha_mismatch_and_incomplete_seeds_are_refused(self):
        run_dir = self.root / "run"
        _write_run(run_dir, self.diffs)
        with self.assertRaises(ValueError):
            C.check_inputs(run_dir)  # the accepted run's sha256 values
        bad = self.root / "bad"
        _write_run(bad, self.diffs, drop=("digits_mlp", "c2", 3007))
        with self.assertRaises(ValueError):
            C.load_joint(bad, ["digits_mlp"])

    def test_sealed_paths_are_refused(self):
        with self.assertRaises(RuntimeError):
            C.check_inputs(self.root / "r1_sealed" / "run", None)


class ConstantsTests(unittest.TestCase):
    def test_t0_nodes_match_the_gate(self):
        from r1.c3.gate import T0_NODES
        self.assertEqual(C.T0_NODES, T0_NODES)
        self.assertTrue(set(C.REPAIRED) <= set(C.T0_NODES))

    def test_critical_values(self):
        self.assertAlmostEqual(C.t_crit(10), 1.8331129326536335, places=10)
        self.assertAlmostEqual(C.t_crit(5), 2.1318467863266495, places=10)


if __name__ == "__main__":
    unittest.main()
