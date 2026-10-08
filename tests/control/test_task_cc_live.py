"""F8: live candidate-consistency task (generator, fit/verifier, fork path)."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(ROOT / "experiments/paper_b/task_cc_live"))

from cc_live_candidate import Stump, accuracy, fit_stump, verifier  # noqa: E402
from causal_branch.control.branch_tree import execute_tree_v2  # noqa: E402
from cc_live_generator import generate_family  # noqa: E402
from cc_live_run_task import run as run_live  # noqa: E402
from cc_live_task import LiveCandidateTask  # noqa: E402
from cc_live_tools import CANDIDATE_SCHEMA, tool_names  # noqa: E402


class TestGeneratorAndVerifier(unittest.TestCase):
    def test_splits_are_disjoint(self):
        family = generate_family(0, 1)
        rows = [tuple(np.round(row, 6)) for row in
                np.vstack([family["X_train"], family["X_dev1"], family["X_dev2"], family["X_hidden"]])]
        self.assertEqual(len(rows), len(set(rows)))

    def test_fit_returns_executable_candidate(self):
        family = generate_family(0, 2)
        candidate = fit_stump(family["X_train"], family["y_train"])
        self.assertIsInstance(candidate, Stump)
        predictions = candidate.predict(family["X_dev1"])
        self.assertEqual(len(predictions), len(family["y_dev1"]))

    def test_verifier_ties_leave_candidate_unchanged(self):
        family = generate_family(0, 3)
        candidate = fit_stump(family["X_train"], family["y_train"])
        # the candidate is already the best stump on this diagnostic set
        self.assertEqual(verifier(candidate, family["X_train"], family["y_train"]), candidate)

    def test_verifier_can_replace_on_strict_improvement(self):
        family = generate_family(0, 4)
        bad = Stump(feature=0, threshold=1e9, direction=1)  # predicts all 0
        repaired = verifier(bad, family["X_train"], family["y_train"])
        self.assertGreater(accuracy(repaired, family["X_train"], family["y_train"]),
                           accuracy(bad, family["X_train"], family["y_train"]))


class TestTaskForkPath(unittest.TestCase):
    def test_hidden_evaluation_is_not_in_the_workspace(self):
        family = generate_family(0, 5)
        task = LiveCandidateTask(family)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            task.prepare(ws, template_id="t", root_id="r", seed=1)
            task.continue_to_checkpoint2(ws)
            task.verify_and_respond(ws)
            names = {p.name for p in ws.iterdir()}
            self.assertEqual(names, {"dev1.csv", "dev2.csv", "candidate.json", "features.json"})
            blob = "".join(p.read_text() for p in ws.iterdir())
            self.assertNotIn("hidden", blob)
            self.assertTrue(0.0 <= task.grade(ws) <= 1.0)

    def test_driver_produces_a_tree_through_the_fork_path(self):
        family = generate_family(1, 6)
        with tempfile.TemporaryDirectory() as tmp:
            records, tree = execute_tree_v2(
                LiveCandidateTask(family), root_id="r", template_family_id="f",
                split="engineering", seed=6, branch_root=Path(tmp) / "b", repetitions=2,
            )
        self.assertIn("now", tree)
        self.assertIn("later", tree)
        self.assertIn("never", tree)
        later = next(r for r in records if r.decision_index == 2 and r.action == "verify")
        never = next(r for r in records if r.decision_index == 2 and r.action == "continue")
        self.assertEqual(later.history_hash_at_decision, never.history_hash_at_decision)


class TestToolsAndRun(unittest.TestCase):
    def test_tool_definitions_and_submission_format(self):
        self.assertEqual(tool_names(), ["fit_candidate", "verify_candidate", "submit_candidate"])
        self.assertIn("feature", CANDIDATE_SCHEMA["properties"])
        from cc_live_prompts import TASK_PROMPT
        self.assertIn("submit_candidate", TASK_PROMPT)

    def test_end_to_end_report(self):
        report = run_live(2, 7)
        self.assertEqual(report["banner"], "ENGINEERING_ONLY")
        self.assertEqual(len(report["families"]), 2)
        self.assertIn("pi_path_note", report)


if __name__ == "__main__":
    unittest.main()
