"""No-temp, mocked tests of the cooperative waited-exit publication boundary."""
import hashlib
import json
import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from r1.exam import b1_exit_receipt as receipt


HEAD = 'a' * 40
PID = 4321
ACTIVE = json.dumps({'version':'b1_active/v1','runner_pid':PID,
                     'authorization_checkout_head':HEAD}).encode()
COMPLETE = json.dumps({'status':'COMPLETE','phase':'b1','execution_label':'EVIDENCE'}).encode()
FINALIZED = b'synthetic reviewed finalization bytes'


class ReceiptTests(unittest.TestCase):
    def file_info(self, *, inode=9, size=2):
        return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=os.getuid(),
                               st_dev=7, st_ino=inode, st_size=size, st_mtime_ns=1, st_ctime_ns=1)

    def test_read_owned_receipt_checks_stable_identity(self):
        info = self.file_info()
        with mock.patch.object(receipt.os, 'open', return_value=8001), \
                mock.patch.object(receipt.os, 'fstat', return_value=info), \
                mock.patch.object(receipt.os, 'read', side_effect=[b'{}', b'']), \
                mock.patch.object(receipt.os, 'stat', return_value=info), \
                mock.patch.object(receipt.os, 'close'):
            self.assertEqual(receipt.read_owned_regular('/synthetic/receipt'), b'{}')

    def test_replaced_receipt_name_is_refused(self):
        with mock.patch.object(receipt.os, 'open', return_value=8001), \
                mock.patch.object(receipt.os, 'fstat', return_value=self.file_info()), \
                mock.patch.object(receipt.os, 'read', side_effect=[b'{}', b'']), \
                mock.patch.object(receipt.os, 'stat', return_value=self.file_info(inode=10)), \
                mock.patch.object(receipt.os, 'close'):
            with self.assertRaisesRegex(RuntimeError, 'changed while read'):
                receipt.read_owned_regular('/synthetic/receipt')

    def test_oversize_receipt_is_refused_before_content_read(self):
        with mock.patch.object(receipt.os, 'open', return_value=8001), \
                mock.patch.object(receipt.os, 'fstat', return_value=self.file_info(size=receipt.MAX_BYTES+1)), \
                mock.patch.object(receipt.os, 'read') as read, \
                mock.patch.object(receipt.os, 'close'):
            with self.assertRaisesRegex(RuntimeError, 'not an owned regular'):
                receipt.read_owned_regular('/synthetic/receipt')
        read.assert_not_called()

    def test_nonzero_wait_never_writes_receipt_even_if_state_looks_complete(self):
        # Models a COMPLETE exchange followed by fsync failure and STOP-save
        # failure: the externally waited runner exit is nonzero.
        with mock.patch.object(receipt, 'active_and_state') as read, \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaisesRegex(RuntimeError, 'did not exit successfully'):
                receipt.publish_waited_success('/synthetic/batch', HEAD, PID, 1)
        read.assert_not_called()
        write.assert_not_called()

    def test_valid_receipt_binds_waited_pid_head_and_exact_bytes(self):
        with mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED), \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            result = receipt.publish_waited_success('/synthetic/batch', HEAD, PID, 0)
        self.assertEqual(result['runner_pid'], PID)
        self.assertEqual(result['batch_state_sha256'], hashlib.sha256(COMPLETE).hexdigest())
        self.assertEqual(result['active_sha256'], hashlib.sha256(ACTIVE).hexdigest())
        self.assertEqual(result['finalization_sha256'], hashlib.sha256(FINALIZED).hexdigest())
        write.assert_called_once_with(Path('/synthetic/batch') / receipt.EXIT_RECEIPT, result)

    def test_missing_receipt_refuses_verification(self):
        with mock.patch.object(receipt, 'read_owned_regular', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_changed_state_refuses_verification(self):
        data = {'version':'b1_waited_exit/v1','runner_pid':PID,'exit_code':0,
                'authorization_checkout_head':HEAD,'active_sha256':hashlib.sha256(ACTIVE).hexdigest(),
                'batch_state_sha256':hashlib.sha256(COMPLETE).hexdigest(),
                'finalization_sha256':hashlib.sha256(FINALIZED).hexdigest()}
        with mock.patch.object(receipt, 'read_owned_regular', return_value=json.dumps(data).encode()), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, b'changed')), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED):
            with self.assertRaisesRegex(RuntimeError, 'bytes mismatch'):
                receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_matching_bytes_allow_receipt_validation(self):
        data = {'version':'b1_waited_exit/v1','runner_pid':PID,'exit_code':0,
                'authorization_checkout_head':HEAD,'active_sha256':hashlib.sha256(ACTIVE).hexdigest(),
                'batch_state_sha256':hashlib.sha256(COMPLETE).hexdigest(),
                'finalization_sha256':hashlib.sha256(FINALIZED).hexdigest()}
        with mock.patch.object(receipt, 'read_owned_regular', return_value=json.dumps(data).encode()), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED):
            self.assertEqual(receipt.verify_waited_success('/synthetic/batch', HEAD), data)

    def test_changed_finalization_refuses_verification(self):
        data = {'version':'b1_waited_exit/v1','runner_pid':PID,'exit_code':0,
                'authorization_checkout_head':HEAD,'active_sha256':hashlib.sha256(ACTIVE).hexdigest(),
                'batch_state_sha256':hashlib.sha256(COMPLETE).hexdigest(),
                'finalization_sha256':hashlib.sha256(FINALIZED).hexdigest()}
        with mock.patch.object(receipt, 'read_owned_regular', return_value=json.dumps(data).encode()), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', return_value=b'changed'):
            with self.assertRaisesRegex(RuntimeError, 'bytes mismatch'):
                receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_stop_record_even_a_dangling_name_blocks_before_reading(self):
        with mock.patch.object(receipt.os.path, 'lexists', return_value=True), \
                mock.patch.object(receipt, 'read_owned_regular') as read:
            with self.assertRaisesRegex(RuntimeError, 'STOP record'):
                receipt.active_and_state('/synthetic/batch', HEAD, PID)
        read.assert_not_called()

    def test_boolean_exit_result_is_not_success(self):
        with mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaisesRegex(RuntimeError, 'did not exit successfully'):
                receipt.publish_waited_success('/synthetic/batch', HEAD, PID, False)
        write.assert_not_called()

    def test_runner_failure_does_not_create_external_receipt(self):
        child = SimpleNamespace(pid=PID, wait=lambda: 1)
        with mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaisesRegex(RuntimeError, 'did not exit successfully'):
                receipt.publish_after_wait(child, '/synthetic/batch', HEAD)
        write.assert_not_called()

    def test_missing_finalization_refuses_even_after_successful_wait(self):
        child = SimpleNamespace(pid=PID, wait=lambda: 0)
        with mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', side_effect=FileNotFoundError), \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaises(FileNotFoundError):
                receipt.publish_after_wait(child, '/synthetic/batch', HEAD)
        write.assert_not_called()

    def test_production_existing_batch_is_not_automatically_resumed(self):
        from r1.exam import runtime
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.out = Path('/synthetic/existing')
        runner.cfg = {'dryrun':False, 'nodes':[], 'harness_commit':'h', 'work_dir':'/synthetic'}
        runner.rule = {'version':'x5_rule/v2'}
        runner.rule_sha = 'r'
        runner.b1_config_head = HEAD
        runner.registry_path = Path('/synthetic/registry')
        runner.registry = {}
        runner.state = {}
        runner.b1_state_identity = None
        with mock.patch.object(runtime, 'require_committed_b1_config', return_value=HEAD), \
                mock.patch.object(runtime, 'require_committed_b1_registry'), \
                mock.patch.object(runtime, 'author_gate', return_value=HEAD), \
                mock.patch.object(runtime, 'worker_environment'), \
                mock.patch.object(Path, 'mkdir', side_effect=FileExistsError), \
                mock.patch('r1.exam.b1_state_preserve.write_exclusive_json') as sentinel:
            with self.assertRaisesRegex(runtime.PreparationStop, 'cannot be resumed automatically'):
                runner.start('b1')
        sentinel.assert_not_called()


if __name__ == '__main__':
    unittest.main()
