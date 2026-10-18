"""Runbook step 1: the agent tree executor on the scripted backend."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(ROOT / "experiments/paper_b/task_cc_live"))

from causal_branch.control.branch_tree import TreeError, records_to_tree  # noqa: E402
from causal_branch.control.configurator.serialiser import (  # noqa: E402
    check_prefix, history_from_json, history_to_json, serialise,
)
from causal_branch.control.executor import (  # noqa: E402
    BRANCH_SLOTS, ExecutorError, PiBackend, PiBinding, ToolHandlers, assert_no_regime_names,
    execute_agent_tree, fork_session, history_from_session, read_session, session_dir,
)
from cc_live_agent import CandidateTaskTools, ScriptedCandidateAgent  # noqa: E402
from cc_live_generator import generate_family  # noqa: E402


def _run(tmp: Path, behaviour: str = "typical", seed: int = 7):
    family = generate_family(0, seed)
    task = CandidateTaskTools(family)
    backend = ScriptedCandidateAgent(behaviour=behaviour)
    return execute_agent_tree(
        task, backend, root_id="fam00-r0", template_family_id="fam00", split="development",
        seed=seed, branch_root=tmp / "tree", prepare=task.prepare, repetitions=2)


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_tree_records_and_outcomes_come_from_execution(self):
        records, tree, histories = _run(self.root)
        self.assertEqual({r.branch_id for r in records}, set(BRANCH_SLOTS))
        self.assertTrue(tree["reached2"])
        for regime in ("now", "later", "never"):
            self.assertTrue(0.0 <= tree[regime] <= 1.0)
        self.assertEqual(records_to_tree(records)["now"], tree["now"])
        now = [r for r in records if r.branch_id == "b0"][0]
        never = [r for r in records if r.branch_id == "b3"][0]
        self.assertEqual(now.verifier_calls, 1)
        self.assertEqual(never.verifier_calls, 0)
        self.assertEqual(histories["refusals"], 0)

    def test_chained_fork_reproduces_parent_prefix_at_both_checkpoints(self):
        _run(self.root)
        tree = self.root / "tree"
        prefix_session = next(session_dir(tree / "prefix/workspace").glob("*.jsonl"))
        prefix_doc = read_session(prefix_session)
        c1 = [e for e in prefix_doc.entries if e.get("type") == "checkpoint"][0]["id"]
        cont_sessions = sorted(session_dir(tree / "b1/workspace").glob("*.jsonl"))
        self.assertEqual(len(cont_sessions), 2)  # inherited parent copy + child
        child = [p for p in cont_sessions if read_session(p).header.get("parentSession")][0]
        child_doc = read_session(child)
        self.assertEqual(child_doc.prefix_digest(c1), prefix_doc.prefix_digest(c1))
        c2 = [e for e in child_doc.entries if e.get("type") == "checkpoint"
              and e.get("checkpoint_id") == "c2"][0]["id"]
        for slot in ("b2_r0", "b2_r1", "b3_r0", "b3_r1"):
            leaf_sessions = session_dir(tree / slot / "workspace").glob("*.jsonl")
            grandchild = [p for p in leaf_sessions
                          if read_session(p).header.get("parentSession") == child.name][0]
            self.assertEqual(read_session(grandchild).prefix_digest(c2), child_doc.prefix_digest(c2))

    def test_later_and_never_share_the_checkpoint2_history(self):
        records, _, histories = _run(self.root)
        d2 = [r for r in records if r.decision_index == 2]
        self.assertEqual(len({r.history_hash_at_decision for r in d2}), 1)
        h1, h2 = histories["h1"], histories["h2"]
        check_prefix(h1, h2)
        self.assertEqual(h1.phase, 1)
        self.assertEqual(h2.phase, 2)
        self.assertTrue(h1.session_prefix_sha256 and h2.session_prefix_sha256)
        self.assertNotEqual(h1.session_prefix_sha256, h2.session_prefix_sha256)
        self.assertEqual(h1.root_id, "fam00-r0")
        roundtrip = history_from_json(history_to_json(h2))
        self.assertEqual(roundtrip, h2)
        # the arrival observation is part of H2 and not of H1
        kinds2 = [e.kind for e in h2.events]
        self.assertIn("observation", kinds2)
        self.assertNotIn("observation", [e.kind for e in h1.events])

    def test_histories_carry_no_outcome_or_identifier(self):
        _, tree, histories = _run(self.root)
        for h in (histories["h1"], histories["h2"]):
            text = serialise(h).text
            self.assertNotIn("fam00", text)
            self.assertNotIn("hidden", text.lower())
            for value in (tree["now"], tree["later"], tree["never"]):
                self.assertNotIn(f"{value:.4f}", text)

    def test_guard_refuses_a_second_verification(self):
        records, tree, histories = _run(self.root, behaviour="greedy")
        self.assertGreaterEqual(histories["refusals"], 1)
        for r in records:
            self.assertLessEqual(r.verifier_calls, 1)
        records_to_tree(records)
        # the refusal is visible in the session as a tool result
        sessions = list((self.root / "tree").rglob("*.jsonl"))
        refused = sum("refused" in p.read_text() for p in sessions)
        self.assertGreater(refused, 0)

    def test_verify_branch_must_verify(self):
        with self.assertRaises(ExecutorError):
            _run(self.root, behaviour="careless")

    def test_no_regime_name_reaches_sessions_or_paths(self):
        _run(self.root)
        assert_no_regime_names(self.root / "tree")
        for path in (self.root / "tree").rglob("*.jsonl"):
            text = path.read_text()
            self.assertNotIn(str(self.root), text)

    def test_transplanted_checkpoint2_session_is_rejected(self):
        _run(self.root)
        tree = self.root / "tree"
        prefix_session = next(session_dir(tree / "prefix/workspace").glob("*.jsonl"))
        with self.assertRaises(ExecutorError):
            history_from_session(prefix_session, phase=2, checkpoint_id="c2")
        doc = read_session(prefix_session)
        with self.assertRaises(ExecutorError):
            fork_session(prefix_session, child_id=doc.header["id"], checkpoint_entry_id=doc.entries[-1]["id"])

    def test_tool_handler_rejects_unknown_tool(self):
        family = generate_family(0, 3)
        task = CandidateTaskTools(family)
        ws = self.root / "ws"
        task.prepare(ws)
        tools = ToolHandlers(task=task, workspace=ws, verify_allowed=False)
        self.assertTrue(tools.call("unknown", {})["refused"])
        self.assertTrue(tools.call("verify_candidate", {"candidate": {}})["refused"])
        self.assertEqual(tools.verifier_calls, 0)

    def test_pi_backend_refuses_unbound(self):
        backend = PiBackend(PiBinding())
        with self.assertRaises(ExecutorError) as ctx:
            backend.run_turn(workspace=self.root, session=self.root / "s.jsonl", tools=None,
                             prompt="", stop="finish", seed=0)
        self.assertIn("not bound", str(ctx.exception))
        bound = PiBackend(PiBinding(endpoint_path="e.json", pi_entry="pi", system_prompt="p",
                                    extension="x", allowed_tools=("fit_candidate",)))
        with self.assertRaises(ExecutorError) as ctx:
            bound.run_turn(workspace=self.root, session=self.root / "s.jsonl", tools=None,
                           prompt="", stop="finish", seed=0)
        self.assertIn("allow_live", str(ctx.exception))

    def test_records_json_roundtrip(self):
        records, _, _ = _run(self.root)
        from dataclasses import asdict
        from causal_branch.control.branch_tree import TreeRecord
        again = [TreeRecord(**json.loads(json.dumps(asdict(r)))) for r in records]
        self.assertEqual(records_to_tree(again), records_to_tree(records))


if __name__ == "__main__":
    unittest.main()
