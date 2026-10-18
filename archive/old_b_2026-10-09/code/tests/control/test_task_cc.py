"""B6: candidate-consistency task, its frozen law and its executable witnesses."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(ROOT / "experiments/paper_b/task_cc"))

from law import SCREEN_LAW, law_hash  # noqa: E402
from pilot_law import pilot_law_hash  # noqa: E402
from task import CandidateConsistencyTask, fit_tool, ordinary_refit, verifier  # noqa: E402
from witnesses import run_screen  # noqa: E402


class TestTaskSemantics(unittest.TestCase):
    def test_fit_tool_returns_the_evaluated_candidate(self):
        self.assertEqual(fit_tool([0, 0, 1]), 0)
        self.assertEqual(fit_tool([2, 1, 2]), 2)

    def test_verifier_replaces_only_on_strict_improvement(self):
        # tie: diagnostic candidate equals the candidate; leave unchanged
        self.assertEqual(verifier(1, [1, 1, 0]), 1)
        # strict improvement on the diagnostic replaces the candidate
        self.assertEqual(verifier(0, [1, 1, 0]), 1)

    def test_witnesses_run_through_the_real_fork_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_screen(Path(tmp))
        self.assertTrue(report["all_orderings_ok"])
        self.assertEqual(report["verdict"], "WITNESSES_OK")
        self.assertFalse(report["stop_verifier_redundant"])
        self.assertTrue(report["later_information_exists"])
        # each family produced a tree from execution
        self.assertEqual(len(report["families"]), 8)
        for row in report["families"]:
            self.assertIn("now", row["tree"])

    def test_hidden_truth_is_never_written_to_the_workspace(self):
        spec = SCREEN_LAW["now_best"][0]
        task = CandidateConsistencyTask(spec)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            task.prepare(ws, template_id="t", root_id="r", seed=1)
            task.verify_and_respond(ws)
            task.continue_to_checkpoint2(ws)
            blob = "".join(p.read_text() for p in ws.rglob("*.json"))
        self.assertNotIn("true_param", blob)
        # the true parameter value is not recoverable from the visible surface
        self.assertNotIn("hidden", blob)

    def test_checkpoint2_is_legitimate_new_information(self):
        spec = SCREEN_LAW["later_best"][0]
        task = CandidateConsistencyTask(spec)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            task.prepare(ws, template_id="t", root_id="r", seed=1)
            before = set(p.name for p in ws.glob("*.json"))
            task.continue_to_checkpoint2(ws)
            after = set(p.name for p in ws.glob("*.json"))
        self.assertIn("fit_dev2.json", after - before)
        self.assertNotEqual(ordinary_refit(spec, 1), ordinary_refit(spec, 2))

    def test_law_hash_is_stable_and_pilot_law_is_separate(self):
        self.assertEqual(law_hash(), law_hash(SCREEN_LAW))
        self.assertNotEqual(law_hash(), pilot_law_hash())


if __name__ == "__main__":
    unittest.main()
