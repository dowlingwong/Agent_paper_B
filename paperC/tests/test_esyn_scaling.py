"""Design checks for the E-SYN scaling study (ENGINEERING_ONLY; AI-assisted, 22 Nov 2026)."""
import unittest

from paperc import esyn_scaling as es, learner_validation as lv
from paperc.esyn import sim


class ScalingDesignTest(unittest.TestCase):
    def test_roots_are_disjoint_from_held_out_roots_and_within_registry(self):
        es._check_ranges()
        held_out = set(lv.SCREEN) | set(lv.DEV) | set(lv.TEST)
        for n in es.SIZES:
            for draw in range(es.N_DRAWS):
                if es.has_draw(draw, n):
                    roots = es.draw_roots(draw, n)
                    self.assertEqual(len(set(roots)), n)
                    self.assertFalse(set(roots) & held_out)
                    self.assertLess(max(roots), sim.MAX_RECORDED)

    def test_draw_zero_is_nested_and_starts_with_p8_roots(self):
        self.assertEqual(es.draw_roots(0, len(lv.TRAIN)), list(lv.TRAIN))
        for small, large in zip(es.SIZES, es.SIZES[1:]):
            self.assertEqual(es.draw_roots(0, large)[:small], es.draw_roots(0, small))

    def test_draw_counts(self):
        counts = {n: sum(es.has_draw(d, n) for d in range(es.N_DRAWS)) for n in es.SIZES}
        self.assertEqual(counts, {256: 3, 512: 3, 1024: 3, 2048: 3, 4096: 2, 8192: 1})
        with self.assertRaises(ValueError):
            es.draw_roots(2, 4096)

    def test_extended_grids_keep_p8_settings_first(self):
        for method, grid in lv.GRIDS.items():
            self.assertEqual(es.EXTENDED[method][:len(grid)], grid)

    def test_headroom_reads_stored_tables(self):
        table = es.headroom()
        self.assertEqual(len(table["worlds"]), 7)
        null = table["worlds"]["strict_null"]
        self.assertFalse(null["gap_clear"])
        self.assertIsNone(null["one_step"]["share"])
        budget = table["worlds"]["budget"]
        self.assertTrue(budget["gap_clear"])
        self.assertGreater(budget["sequential"]["share"], 0.9)
        self.assertLess(budget["one_step"]["share"], 0.2)



class ScalingReportTest(unittest.TestCase):
    def test_verdicts(self):
        from paperc import esyn_scaling_report as report

        base = {"gap_clear": True, "left_clear": False, "left": 0.0, "left_half_width": 1.0}
        self.assertEqual(report.verdict({**base, "gap_clear": False}), "none: no gap")
        self.assertEqual(report.verdict({**base, "left_clear": True, "left": 3.0}), "yes")
        self.assertTrue(report.verdict(base).startswith("none shown"))
        self.assertEqual(report.verdict({**base, "left": 1.5}), "not resolved")

    def test_stored_result_matches_committed_code_and_reproduces_p8(self):
        import json

        result = json.loads(es.OUT.read_text())
        self.assertEqual(result["code_sha256"], es.code_sha256())
        check = es.reproduction(result)
        self.assertTrue(check["rows_equal"] and check["fork_points_equal"])
        self.assertTrue(all(m["same_setting"] for m in check["methods"].values()))
        self.assertEqual(check["methods"]["R0"]["difference"], 0.0)

    def test_margin_is_grouped_as_sequential_and_committed_report_is_this_modules_output(self):
        import json

        from paperc import esyn_scaling_report as report

        self.assertIn("margin", report.SEQUENTIAL)
        self.assertNotIn("margin", report.ONE_STEP)
        table = report.headroom()["worlds"]
        self.assertEqual(table["keep_feedback"]["one_step"]["rung"], "shrink")
        self.assertEqual(es.ONE_STEP, ("N2", "N2b", "margin", "shrink", "rawkeep"))  # run-time grouping restored
        result = json.loads(es.OUT.read_text())
        self.assertEqual(es.REPORT.read_text(), report.markdown(result))


if __name__ == "__main__":
    unittest.main()
