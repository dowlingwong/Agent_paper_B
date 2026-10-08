"""F7: end-to-end evaluation harness, N1 wiring, displacement and coverage."""
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from causal_branch.control import (  # noqa: E402
    allocator,
    evaluate_tree,
    timing,
)
from causal_branch.control import replay_validity  # noqa: E402
from causal_branch.control.evaluate_tree import (  # noqa: E402
    DERIVED_M,
    EvaluationError,
    displacement_check,
    evaluate_tree as run_evaluation,
)

READINGS = {"supported", "practically_large", "equivalence",
            "not_practically_useful", "inconclusive"}


def _rows(prefix, n, seed, slope=-0.3, noise=0.2, reached_rate=0.8):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        x = rng.uniform(0, 1)
        reached = bool(rng.uniform() < reached_rate)
        out.append(dict(
            root_id=f"{prefix}{i}", family=f"{prefix}f{i % 6}", split="test",
            h1={"x": x}, h2={"x": x, "w": rng.uniform(0, 1)},
            u_now=0.5 + 0.6 * (x - 0.5),
            u_later=0.5 + slope * x + rng.normal(0, noise),
            u_never=0.5, reached2=reached, terminated=not reached,
        ))
    return out


def _context_rows(prefix, n, seed, n_families=12, noise=0.1):
    """Waiting value depends on z, immediate value on x (two H1 features)."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        x, z, w = rng.uniform(0, 1, size=3)
        reached = bool(rng.uniform() < 0.8)
        later = 0.5 + 0.8 * (z - 0.4) + rng.normal(0, noise)
        out.append(dict(
            root_id=f"{prefix}{i}", family=f"{prefix}f{i % n_families}", split="test",
            h1={"x": x, "z": z}, h2={"x": x, "z": z, "w": w},
            u_now=0.5 + 0.6 * (x - 0.5) + rng.normal(0, noise),
            u_later=later if reached else 0.5, u_never=0.5,
            reached2=reached, terminated=not reached,
        ))
    return out


class TestEvaluatedPathGuards(unittest.TestCase):
    """C1/C4/E2: guards on the regimes the allocator actually returns."""

    def test_identical_policies_never_read_as_equivalence(self):
        # one H1 feature: every linear score ranks roots alike, so the
        # proposed and myopic regimes coincide; that is not evidence
        report = run_evaluation(_rows("d", 120, 1), _rows("t", 120, 2), n_bootstrap=40, seed=3)
        row = report.contrasts["proposed-myopic"]
        self.assertFalse(row["policies_distinct"])
        self.assertFalse(row["reading_precondition_met"])
        self.assertEqual(report.readings["proposed-myopic"], "inconclusive")
        self.assertNotEqual(report.readings["proposed-myopic"], "equivalence")

    def test_proposed_differs_from_myopic_where_waiting_value_has_its_own_context(self):
        report = run_evaluation(_context_rows("d", 240, 10), _context_rows("t", 240, 11),
                                n_bootstrap=40, seed=1)
        prop, myop = report.regimes["proposed"], report.regimes["myopic"]
        # aliasing the proposed path to myopic gives disagreement 0 and an
        # identical-draw fraction of 1; distinct policies give neither
        disagree = np.mean([prop[k] != myop[k] for k in prop])
        self.assertGreater(disagree, 0.0)
        row = report.contrasts["proposed-myopic"]
        self.assertTrue(row["policies_distinct"])
        self.assertLess(row["identical_draw_fraction"], 0.5)
        self.assertTrue(row["reading_precondition_met"])

    def test_calibrated_params_follow_each_controllers_grid(self):
        report = run_evaluation(_context_rows("d", 240, 20), _context_rows("t", 240, 21),
                                n_bootstrap=20, seed=2)
        # proposed and myopic declare no constant reserve
        self.assertEqual(report.params["proposed"][2], 0)
        self.assertEqual(report.params["myopic"][2], 0)
        for name in ("proposed", "myopic", "bavar", "constant_reserve"):
            self.assertEqual(set(report.regimes[name]), {r["root_id"] for r in
                                                         _context_rows("t", 240, 21)})


class TestHarness(unittest.TestCase):
    def setUp(self):
        self.dev = _rows("d", 120, 1)
        self.test = _rows("t", 120, 2)

    def test_end_to_end_report(self):
        report = run_evaluation(self.dev, self.test, n_bootstrap=60, seed=3)
        for key, reading in report.readings.items():
            self.assertIn(reading, READINGS, key)
        self.assertEqual(report.budget, 30)  # floor(.25*120)
        self.assertEqual(set(report.contrasts), {"proposed-myopic", "proposed-bavar"})
        self.assertTrue(report.matching["matched_decision_class"])
        for diag in ("oof_corr_a1_immediate", "oof_corr_a2_continuation",
                     "vwait_sd", "vwait_heterogeneity_ci", "a2_ranking_quality"):
            self.assertIn(diag, report.diagnostics)

    def test_n1_wired_into_evaluation(self):
        report = run_evaluation(self.dev, self.test, n_bootstrap=40, seed=4)
        n1 = report.n1
        self.assertEqual(n1["derived_m"], DERIVED_M)
        self.assertIn("interference", n1["interference_scope"])
        self.assertIn("proposed-myopic", n1["p_grid_report"])
        self.assertAlmostEqual(n1["population_tax_2mp"], 2.0 * DERIVED_M * n1["p_path"])
        self.assertEqual(n1["audit_arithmetic"]["audits_for_0.02"], 149)

    def test_out_of_fold_calibration_diagnostics(self):
        # E3: calibration (slope, intercept, reliability) for A1, A2 and V_wait
        report = run_evaluation(_context_rows("d", 240, 30), _context_rows("t", 240, 31),
                                n_bootstrap=20, seed=5)
        cal = report.diagnostics["oof_calibration"]
        self.assertEqual(set(cal), {"a1", "a2", "vwait"})
        for name, row in cal.items():
            self.assertEqual(set(row), {"n", "slope", "intercept", "r2"}, name)
            self.assertGreater(row["n"], 0)
        # the immediate and second-stage models are well specified here
        self.assertAlmostEqual(cal["a1"]["slope"], 1.0, delta=0.25)
        self.assertAlmostEqual(cal["a2"]["slope"], 1.0, delta=0.25)
        self.assertGreater(cal["a2"]["r2"], 0.5)

    def test_one_p_mapping_for_grid_tax_and_bound(self):
        # N2/N3: p_path comes from checkpoint allowances, and the tax and the
        # reported bound use the same p_path and m
        report = run_evaluation(self.dev, self.test, n_bootstrap=40, seed=4)
        n1 = report.n1
        self.assertAlmostEqual(n1["p_path"], min(1.0, 2 * n1["working_p"]))
        self.assertAlmostEqual(n1["population_tax_2mp"], 2 * DERIVED_M * n1["p_path"])
        for key, row in report.contrasts.items():
            expected = max(-1.0, min(1.0, row["adjusted_lcb"] - n1["population_tax_2mp"]))
            self.assertAlmostEqual(n1["population_bound_at_working_p"][key], expected)

    def test_bound_uses_working_p_even_when_no_grid_value_survives(self):
        # N3: an empty grid used to give p_path = 0 yet a bound taxed by 0.04
        report = run_evaluation(self.dev, self.test, n_bootstrap=40, seed=4, p_grid=(0.10,))
        n1 = report.n1
        self.assertEqual(set(n1["p_grid_report"].values()), {None})
        self.assertGreater(n1["p_path"], 0.0)
        for key, row in report.contrasts.items():
            self.assertAlmostEqual(
                row["adjusted_lcb"] - n1["population_bound_at_working_p"][key],
                min(n1["population_tax_2mp"], row["adjusted_lcb"] + 1.0))

    def test_development_test_family_leakage_rejected(self):
        leaked = list(self.test) + [dict(self.dev[0], root_id="x", family=self.dev[0]["family"])]
        with self.assertRaisesRegex(EvaluationError, "disjoint"):
            run_evaluation(self.dev, leaked)

    def test_displacement_within_derived_bound(self):
        result = displacement_check(n_batches=100, n_roots=20, seed=5)
        self.assertLessEqual(result["max_changed_roots"], DERIVED_M)
        self.assertTrue(result["within_bound"])


class TestCoverage(unittest.TestCase):
    def test_entrypoint_executes_public_functions(self):
        modules = (replay_validity, allocator, timing, evaluate_tree)
        names = {m.__name__ for m in modules}
        covered = set()

        def tracer(frame, event, arg):
            if event == "call" and frame.f_globals.get("__name__") in names:
                covered.add((frame.f_globals["__name__"], frame.f_code.co_qualname))
            return tracer

        # evaluate + displacement so both entrypoints run
        dev, test = _rows("d", 80, 11), _rows("t", 80, 12)
        old = sys.gettrace()
        sys.settrace(tracer)
        try:
            run_evaluation(dev, test, n_bootstrap=30, seed=13)
            displacement_check(n_batches=20, n_roots=12, seed=14)
        finally:
            sys.settrace(old)
        public = set()
        for m in modules:
            for n, o in vars(m).items():
                if n.startswith("_") or getattr(o, "__module__", None) != m.__name__:
                    continue
                if inspect.isfunction(o):
                    public.add((m.__name__, o.__qualname__))
                elif inspect.isclass(o):
                    # U2: class methods and properties count; a duplicate
                    # implementation the entrypoint never runs must fail here
                    for mn, mo in vars(o).items():
                        if mn.startswith("_"):
                            continue
                        fn = mo.fget if isinstance(mo, property) else mo
                        fn = getattr(fn, "__func__", fn)
                        if inspect.isfunction(fn):
                            public.add((m.__name__, fn.__qualname__))
        uncovered = sorted(public - covered)
        # every public function must be executed by the entrypoints
        self.assertEqual(uncovered, [], f"uncovered public functions: {uncovered}")


if __name__ == "__main__":
    unittest.main()
