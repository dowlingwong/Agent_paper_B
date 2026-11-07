"""In-memory operator classification checks; no files or processes created."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from r1.exam import b1_operator_exit as operator


class OperatorExitTests(unittest.TestCase):
    def setUp(self):
        self.head='a'*40
        self.binding=json.dumps({'head':self.head,'out':'/work/batch','pid':42,'start_ticks':77}).encode()

    def classify(self, observed_exit, *, stop_paths=(), binding=None, verify_error=None):
        stop_paths=set(stop_paths)
        with patch.object(operator.Path,'resolve',lambda path,**kw:path), \
             patch.object(operator,'read_owned_regular',return_value=self.binding if binding is None else binding), \
             patch.object(operator,'_exists_checked',side_effect=lambda p:str(p) in stop_paths), \
             patch.object(operator,'verify_waited_success',side_effect=verify_error) as verify:
            value=operator.classify_supervisor_exit('/work/batch','/work/supervisor',self.head,observed_exit)
        return value,verify

    def test_finally_failure_after_terminal_commit_is_operational_issue(self):
        # Model a callback interrupting the supervisor after terminal commit,
        # overriding its intended return 0. No STOP is inferred from exit alone.
        def supervisor_return():
            try: return 0
            finally: raise RuntimeError('queued callback after commit')
        try: supervisor_return()
        except RuntimeError: observed_exit=1
        result,verify=self.classify(observed_exit)
        self.assertEqual(result['classification'],'COMMITTED_NONZERO_EXIT_OPERATIONAL_ISSUE')
        self.assertTrue(result['operator_must_check_logs_for_stop'])
        self.assertTrue(result['requires_handover_restoration'])
        self.assertTrue(result['requires_complete_batch_verifier'])
        verify.assert_called_once()

    def test_zero_exit_still_requires_receipt_and_independent_verification(self):
        result,verify=self.classify(0)
        self.assertEqual(result['classification'],'COMMITTED_NORMAL_EXIT')
        self.assertTrue(result['requires_complete_batch_verifier'])
        verify.assert_called_once()

    def test_any_recorded_stop_wins_even_if_receipt_exists(self):
        for path in ('/work/supervisor/SUPERVISOR_STOP.json','/work/batch/STOP.json',
                     '/work/batch/B1_COMMIT_UNCERTAIN.json'):
            with self.subTest(path=path):
                result,verify=self.classify(1,stop_paths=[path])
                self.assertEqual(result['classification'],'STOP_OR_UNCERTAIN')
                verify.assert_not_called()

    def test_unverifiable_receipt_cannot_classify_success(self):
        with self.assertRaises(OSError): self.classify(1,verify_error=OSError('unavailable'))

    def test_supervisor_binding_mismatch_refused(self):
        bad=json.dumps({'head':self.head,'out':'/work/other','pid':42,'start_ticks':77}).encode()
        with self.assertRaisesRegex(ValueError,'does not bind'):
            self.classify(1,binding=bad)
