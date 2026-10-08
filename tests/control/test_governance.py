"""Runbook step 2: history provenance, copied schema, deterministic ledger."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(ROOT / "experiments/paper_b/task_cc_live"))

from causal_branch.control import reliability_schema as rs  # noqa: E402
from causal_branch.control.executor import execute_agent_tree  # noqa: E402
from causal_branch.control.governance import (  # noqa: E402
    LEDGER_SCHEMA, Ledger, LedgerError, events_for_tree, export_tree, validate_stream, write_tree,
)
from cc_live_agent import CandidateTaskTools, ScriptedCandidateAgent  # noqa: E402
from cc_live_generator import generate_family  # noqa: E402


def _tree(tmp: Path, seed: int = 11):
    family = generate_family(1, seed)
    task = CandidateTaskTools(family)
    return execute_agent_tree(task, ScriptedCandidateAgent(), root_id="fam01-r0",
                              template_family_id="fam01", split="development", seed=seed,
                              branch_root=tmp / "tree", prepare=task.prepare, repetitions=2)


class SchemaCopyTests(unittest.TestCase):
    def test_pinned_schema_and_vocabulary(self):
        self.assertEqual(rs.SCHEMA_VERSION, "1.0")
        self.assertEqual(LEDGER_SCHEMA, "reliability-1.0")
        self.assertEqual(len(rs.UPSTREAM_COMMIT), 40)
        self.assertIn("sealed_test_outcome", {v.value for v in rs.EventVisibility})
        self.assertEqual({s.value for s in rs.AdjudicationStatus},
                         {"accepted", "rejected", "ambiguous", "insufficient_evidence", "verifier_failure"})
        for name in ("proposal", "action_request", "state_snapshot", "verifier_request",
                     "verifier_result", "terminal_outcome", "adjudication", "evidence"):
            self.assertIn(name, {t.value for t in rs.ReliabilityEventType})

    def test_copied_files_carry_provenance_header(self):
        here = ROOT / "experiment_scaffold/src/causal_branch/control/reliability_schema"
        for name in ("events.py", "adjudication.py"):
            head = (here / name).read_text().splitlines()[:3]
            self.assertIn("autoresearch_harness", head[0])
            self.assertIn(rs.UPSTREAM_COMMIT, head[2])


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_two_runs_with_different_wall_times_give_identical_ledgers(self):
        records, tree, histories = _tree(self.root)
        digests = []
        for i, when in enumerate(("2026-10-05T10:00:00Z", "2026-10-06T23:59:59Z")):
            ledger = Ledger(self.root / f"run{i}", run_id="dry-0001")
            write_tree(ledger, records, histories, wall_time_utc=when)
            digests.append(ledger.digest())
            self.assertTrue(ledger.timing_path.is_file())
        self.assertEqual(digests[0], digests[1])
        self.assertNotIn("2026-10-05", (self.root / "run0/ledger/events.jsonl").read_text())

    def test_export_reproduces_records_and_histories(self):
        records, tree, histories = _tree(self.root)
        ledger = Ledger(self.root / "run", run_id="dry-0002")
        write_tree(ledger, records, histories)
        self.assertEqual(validate_stream(ledger.rows()), [])
        exported = export_tree(ledger.events())["fam01-r0"]
        self.assertEqual(sorted(exported["records"], key=lambda r: r.branch_id),
                         sorted(records, key=lambda r: r.branch_id))
        self.assertEqual(exported["tree"], {k: v for k, v in tree.items() if k != "n_repetitions"})
        self.assertEqual(exported["histories"]["h1"], histories["h1"])
        self.assertEqual(exported["histories"]["h2"], histories["h2"])

    def test_histories_in_ledger_carry_no_outcome(self):
        records, tree, histories = _tree(self.root)
        events = events_for_tree(run_id="dry-0003", records=records, histories=histories)
        for event in events:
            for key in ("h1", "h2"):
                if key in event.payload:
                    text = json.dumps(event.payload[key])
                    self.assertNotIn('"U"', text)
                    self.assertNotIn("outcome", text)
        sealed = [e for e in events if e.event_type == rs.ReliabilityEventType.TERMINAL_OUTCOME]
        self.assertTrue(sealed)
        self.assertTrue(all(e.visibility_class == rs.EventVisibility.SEALED_TEST_OUTCOME for e in sealed))

    def test_tampered_row_fails_validation(self):
        records, _, histories = _tree(self.root)
        ledger = Ledger(self.root / "run", run_id="dry-0004")
        write_tree(ledger, records, histories)
        rows = ledger.rows()
        rows[3]["payload"]["U"] = 0.999 if "U" in rows[3]["payload"] else 1
        rows[3]["payload"]["tampered"] = True
        self.assertTrue(any("row_sha256 mismatch" in e for e in validate_stream(rows)))
        rows = ledger.rows()
        rows.append(rows[0])
        self.assertTrue(any("duplicate" in e for e in validate_stream(rows)))

    def test_append_refuses_unknown_parent_and_duplicates(self):
        records, _, histories = _tree(self.root)
        events = events_for_tree(run_id="dry-0005", records=records, histories=histories)
        ledger = Ledger(self.root / "run", run_id="dry-0005")
        with self.assertRaises(LedgerError):
            ledger.append(events[1])  # parent (the proposal) not yet appended
        ledger.append(events[0])
        with self.assertRaises(LedgerError):
            ledger.append(events[0])

    def test_reopened_ledger_continues_the_stream(self):
        records, _, histories = _tree(self.root)
        ledger = Ledger(self.root / "run", run_id="dry-0006")
        write_tree(ledger, records, histories)
        n = len(ledger.rows())
        again = Ledger(self.root / "run", run_id="dry-0006")
        self.assertEqual(len(again.rows()), n)
        with self.assertRaises(LedgerError):
            again.append(events_for_tree(run_id="dry-0006", records=records, histories=histories)[0])


if __name__ == "__main__":
    unittest.main()
