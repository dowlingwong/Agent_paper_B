"""In-memory error ordering checks; no files or processes are created."""
import hashlib
import json
import unittest
from unittest.mock import Mock, patch

from r1.exam import b1_exit_receipt as receipt
from r1.scripts import b1_supervisor as supervisor


class UncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.names=set()
        self.head='a'*40
        self.active=b'active'
        self.state=b'state'
        self.finalized=b'final'
        self.record={'version':'b1_waited_exit/v1','runner_pid':42,'exit_code':0,
                     'authorization_checkout_head':self.head,
                     'active_sha256':hashlib.sha256(self.active).hexdigest(),
                     'batch_state_sha256':hashlib.sha256(self.state).hexdigest(),
                     'finalization_sha256':hashlib.sha256(self.finalized).hexdigest()}

    def lstat(self,path):
        if str(path) not in self.names: raise FileNotFoundError(str(path))
        return Mock()

    def record_uncertainty(self,path,data):
        self.names.add(str(path))

    def reader(self):
        with patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.os,'lstat',side_effect=self.lstat), \
             patch.object(receipt.os.path,'lexists',return_value=False), \
             patch.object(receipt,'read_owned_regular',return_value=json.dumps(self.record).encode()), \
             patch.object(receipt,'active_and_state',return_value=(self.active,self.state)), \
             patch.object(receipt,'_verified_finalization',return_value=self.finalized):
            return receipt.verify_waited_success('/batch',self.head)

    def test_queued_error_confirmed_commit_is_terminal_without_uncertainty(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'verify_waited_success',return_value=self.record), \
             patch.object(supervisor,'_exclusive_json') as stop:
            supervisor._publish_or_reconcile(Mock(),'/batch',self.head)
        stop.assert_not_called()

    def test_transient_reconciliation_failure_persists_reader_block(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'verify_waited_success',side_effect=OSError('transient read')), \
             patch.object(supervisor,'_exclusive_json',side_effect=self.record_uncertainty):
            with self.assertRaises(supervisor.PublicationUncertain):
                supervisor._publish_or_reconcile(Mock(),'/batch',self.head)
        with self.assertRaisesRegex(RuntimeError,'uncertain'):
            self.reader()

    def test_uncertainty_persistence_failure_is_explicit_limit(self):
        with patch.object(receipt,'publish_after_wait',side_effect=RuntimeError('queued callback')), \
             patch.object(receipt,'verify_waited_success',side_effect=OSError('transient read')), \
             patch.object(supervisor,'_exclusive_json',side_effect=OSError('disk unavailable')), \
             patch('builtins.print') as report:
            with self.assertRaisesRegex(supervisor.PublicationUncertain,'could not be persisted'):
                supervisor._publish_or_reconcile(Mock(),'/batch',self.head)
        self.assertIn('NOT CHECKABLE',report.call_args.args[0])
        # Without a persistent name, after reads recover the current reader
        # cannot learn about the uncertainty. This deliberately tests the
        # documented storage-failure limitation; it is not a safety claim.
        self.assertEqual(self.reader(),self.record)

    def test_cannot_stat_uncertainty_path_is_refused(self):
        with patch.object(receipt,'_require_local_filesystem'), \
             patch.object(receipt.os,'lstat',side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                receipt.verify_waited_success('/batch',self.head)
