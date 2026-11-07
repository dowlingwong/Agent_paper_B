"""No-temp, mocked tests of the cooperative waited-exit publication boundary."""
import hashlib
import json
import os
import stat
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from r1.exam import b1_exit_receipt as receipt


HEAD = 'a' * 40
PID = 4321
MOUNT = ('24','/','8:1','ext4')
ACTIVE = json.dumps({'version':'b1_active/v1','runner_pid':PID,
                     'authorization_checkout_head':HEAD,'mount_identity':list(MOUNT)}).encode()
COMPLETE = json.dumps({'status':'COMPLETE','phase':'b1','execution_label':'EVIDENCE'}).encode()
FINALIZED = b'synthetic reviewed finalization bytes'
REAL_LOCAL_CHECK = receipt._require_local_filesystem


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(receipt, '_require_local_filesystem', return_value=MOUNT)
        patcher.start()
        self.addCleanup(patcher.stop)
        lock_patcher = mock.patch.object(receipt, '_reader_publication_lock', side_effect=lambda batch: nullcontext())
        lock_patcher.start()
        self.addCleanup(lock_patcher.stop)
        binding_patcher = mock.patch.object(receipt, '_supervisor_binding', return_value='b'*64)
        binding_patcher.start()
        self.addCleanup(binding_patcher.stop)

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

    def test_mount_parser_selects_most_specific_and_decodes_space(self):
        table = ('24 22 8:1 / / rw - ext4 /dev/a rw\n'
                 '25 24 8:2 / /synthetic\\040space rw - xfs /dev/b rw\n')
        self.assertEqual(receipt._mount_for('/synthetic space/batch', table)[1:],
                         ('/synthetic space', '8:2', 'xfs', '25'))

    def test_mount_parser_rejects_equal_specificity(self):
        table = ('24 22 8:1 / / rw - ext4 /dev/a rw\n'
                 '25 22 8:2 / / rw - xfs /dev/b rw\n')
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
            receipt._mount_for('/batch', table)

    def test_local_filesystem_check_refuses_nfs_and_device_mismatch(self):
        info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_dev=os.makedev(8,1))
        for table in ('24 22 8:1 / / rw - nfs server:/ rw\n',
                      '24 22 8:2 / / rw - ext4 /dev/a rw\n'):
            with self.subTest(table=table), \
                    mock.patch.object(receipt.os, 'stat', return_value=info), \
                    mock.patch.object(Path, 'read_text', return_value=table):
                with self.assertRaisesRegex(RuntimeError, 'site-qualified ext4/xfs'):
                    REAL_LOCAL_CHECK('/synthetic/batch')

    def test_local_filesystem_check_accepts_matching_ext4_type_only(self):
        info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_dev=os.makedev(8,1))
        table = '24 22 8:1 / / rw - ext4 /dev/a rw\n'
        with mock.patch.object(receipt.os, 'stat', return_value=info), \
                mock.patch.object(Path, 'read_text', return_value=table):
            self.assertEqual(REAL_LOCAL_CHECK('/synthetic/batch'), MOUNT)

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
        with mock.patch.object(receipt, '_require_publication_signal_mask'), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED), \
                mock.patch.object(receipt, '_retire_active_last') as retire, \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            result = receipt.publish_waited_success('/synthetic/batch', HEAD, PID, 0)
        self.assertEqual(result['runner_pid'], PID)
        self.assertEqual(result['batch_state_sha256'], hashlib.sha256(COMPLETE).hexdigest())
        self.assertEqual(result['active_sha256'], hashlib.sha256(ACTIVE).hexdigest())
        self.assertEqual(result['finalization_sha256'], hashlib.sha256(FINALIZED).hexdigest())
        write.assert_called_once_with(Path('/synthetic/batch') / receipt.EXIT_RECEIPT, result)
        retire.assert_called_once_with('/synthetic/batch', ACTIVE)

    def test_missing_receipt_refuses_verification(self):
        with mock.patch.object(receipt, 'read_owned_regular', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_changed_state_refuses_verification(self):
        data = {'version':'b1_waited_exit/v2','runner_pid':PID,'exit_code':0,
                'supervisor_dir':'/supervisor','supervisor_sha256':'b'*64,
                'authorization_checkout_head':HEAD,'active_sha256':hashlib.sha256(ACTIVE).hexdigest(),
                'batch_state_sha256':hashlib.sha256(COMPLETE).hexdigest(),
                'finalization_sha256':hashlib.sha256(FINALIZED).hexdigest()}
        with mock.patch.object(receipt, 'read_owned_regular', return_value=json.dumps(data).encode()), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, b'changed')), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED):
            with self.assertRaisesRegex(RuntimeError, 'bytes mismatch'):
                receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_matching_bytes_allow_receipt_validation(self):
        data = {'version':'b1_waited_exit/v2','runner_pid':PID,'exit_code':0,
                'supervisor_dir':'/supervisor','supervisor_sha256':'b'*64,
                'authorization_checkout_head':HEAD,'active_sha256':hashlib.sha256(ACTIVE).hexdigest(),
                'batch_state_sha256':hashlib.sha256(COMPLETE).hexdigest(),
                'finalization_sha256':hashlib.sha256(FINALIZED).hexdigest()}
        with mock.patch.object(receipt, 'read_owned_regular', return_value=json.dumps(data).encode()), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED):
            self.assertEqual(receipt.verify_waited_success('/synthetic/batch', HEAD), data)

    def test_changed_finalization_refuses_verification(self):
        data = {'version':'b1_waited_exit/v2','runner_pid':PID,'exit_code':0,
                'supervisor_dir':'/supervisor','supervisor_sha256':'b'*64,
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
        with mock.patch.object(receipt, '_require_publication_signal_mask'), \
                mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                mock.patch.object(receipt, '_verified_finalization', side_effect=FileNotFoundError), \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaises(FileNotFoundError):
                receipt.publish_after_wait(child, '/synthetic/batch', HEAD)
        write.assert_not_called()

    def test_visible_complete_receipt_after_fsync_failure_is_blocked_by_active(self):
        child = SimpleNamespace(pid=PID, wait=lambda: 0)
        for failure in ('file fsync', 'directory fsync'):
            with self.subTest(failure=failure):
                visible = {'receipt': None, 'active': True}
                def failed_publish(path, value):
                    visible['receipt'] = value  # full bytes visible, then fsync failed
                    raise OSError(failure)
                def exists(path):
                    return Path(path).name == receipt.ACTIVE and visible['active']
                with mock.patch.object(receipt, '_require_publication_signal_mask'), \
                        mock.patch.object(receipt, 'active_and_state', return_value=(ACTIVE, COMPLETE)), \
                        mock.patch.object(receipt, '_verified_finalization', return_value=FINALIZED), \
                        mock.patch.object(receipt, 'write_exclusive_json', side_effect=failed_publish), \
                        mock.patch.object(receipt, '_retire_active_last') as retire, \
                        mock.patch.object(receipt.os.path, 'lexists', side_effect=exists):
                    with self.assertRaises(OSError):
                        receipt.publish_after_wait(child, '/synthetic/batch', HEAD)
                    self.assertIsNotNone(visible['receipt'])
                    retire.assert_not_called()
                    with self.assertRaisesRegex(RuntimeError, 'active sentinel has not been retired'):
                        receipt.verify_waited_success('/synthetic/batch', HEAD)

    def test_missing_signal_mask_refuses_before_any_receipt_write(self):
        with mock.patch.object(receipt.signal, 'valid_signals', return_value={1, 2, receipt.signal.SIGKILL, receipt.signal.SIGSTOP}), \
                mock.patch.object(receipt.signal, 'pthread_sigmask', return_value={1}), \
                mock.patch.object(receipt, 'write_exclusive_json') as write:
            with self.assertRaisesRegex(RuntimeError, 'blocked catchable signals'):
                receipt.publish_waited_success('/synthetic/batch', HEAD, PID, 0)
        write.assert_not_called()

    def test_retirement_is_last_fallible_publication_step(self):
        events = []
        directory = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=os.getuid(), st_dev=7)
        def note_fsync(fd):
            events.append(('fsync',fd))
        def note_rename(*args):
            events.append(('rename',args[-1]))
        def note_close(fd):
            events.append(('close',fd))
            raise OSError('synthetic close failure after commit')
        with mock.patch.object(receipt, 'read_owned_regular', return_value=ACTIVE), \
                mock.patch.object(receipt.os.path, 'lexists', return_value=False), \
                mock.patch.object(receipt.os, 'open', side_effect=[101,102]), \
                mock.patch.object(receipt.os, 'fstat', return_value=directory), \
                mock.patch.object(receipt.os, 'fsync', side_effect=note_fsync), \
                mock.patch.object(receipt.os, 'close', side_effect=note_close), \
                mock.patch.object(receipt, '_renameat2', side_effect=note_rename):
            receipt._retire_active_last('/synthetic/batch', ACTIVE)
        self.assertEqual(events[:3], [('fsync',102),('fsync',101),('rename',receipt._NOREPLACE)])
        self.assertEqual(events[3:], [('close',102),('close',101)])

    def test_retirement_precommit_fsync_failure_does_not_rename(self):
        directory = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=os.getuid(), st_dev=7)
        with mock.patch.object(receipt, 'read_owned_regular', return_value=ACTIVE), \
                mock.patch.object(receipt.os.path, 'lexists', return_value=False), \
                mock.patch.object(receipt.os, 'open', side_effect=[101,102]), \
                mock.patch.object(receipt.os, 'fstat', return_value=directory), \
                mock.patch.object(receipt.os, 'fsync', side_effect=OSError('synthetic fsync failure')), \
                mock.patch.object(receipt.os, 'close'), \
                mock.patch.object(receipt, '_renameat2') as rename:
            with self.assertRaisesRegex(OSError, 'fsync failure'):
                receipt._retire_active_last('/synthetic/batch', ACTIVE)
        rename.assert_not_called()

    def test_mount_replacement_refuses_retirement_before_open(self):
        different = ('25','/synthetic/batch','8:1','ext4')
        with mock.patch.object(receipt, '_require_local_filesystem', return_value=different), \
                mock.patch.object(receipt.os, 'open') as opened, \
                mock.patch.object(receipt, '_renameat2') as rename:
            with self.assertRaisesRegex(RuntimeError, 'mount changed'):
                receipt._retire_active_last('/synthetic/batch', ACTIVE)
        opened.assert_not_called()
        rename.assert_not_called()

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
                mock.patch.object(receipt, '_require_local_filesystem'), \
                mock.patch.object(Path, 'mkdir', side_effect=FileExistsError), \
                mock.patch('r1.exam.b1_state_preserve.write_exclusive_json') as sentinel:
            with self.assertRaisesRegex(runtime.PreparationStop, 'cannot be resumed automatically'):
                runner.start('b1')
        sentinel.assert_not_called()

    def test_unsupported_parent_mount_stops_before_output_or_sentinel(self):
        from r1.exam import runtime
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.out = Path('/synthetic/new')
        runner.cfg = {'dryrun':False, 'nodes':[], 'harness_commit':'h', 'work_dir':'/synthetic'}
        runner.rule = {'version':'x5_rule/v2'}
        runner.rule_sha = 'r'; runner.b1_config_head = HEAD
        runner.registry_path = Path('/synthetic/registry'); runner.registry = {}
        runner.state = {}; runner.b1_state_identity = None
        with mock.patch.object(runtime, 'require_committed_b1_config', return_value=HEAD), \
                mock.patch.object(runtime, 'require_committed_b1_registry'), \
                mock.patch.object(runtime, 'author_gate', return_value=HEAD), \
                mock.patch.object(runtime, 'worker_environment'), \
                mock.patch.object(receipt, '_require_local_filesystem', side_effect=RuntimeError('unsupported mount')), \
                mock.patch.object(Path, 'mkdir') as mkdir, \
                mock.patch('r1.exam.b1_state_preserve.write_exclusive_json') as sentinel:
            with self.assertRaisesRegex(RuntimeError, 'unsupported mount'):
                runner.start('b1')
        mkdir.assert_not_called()
        sentinel.assert_not_called()

    def test_same_device_distinct_bind_mount_stops_before_sentinel(self):
        from r1.exam import runtime
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.out = Path('/synthetic/new')
        runner.cfg = {'dryrun':False, 'nodes':[], 'harness_commit':'h', 'work_dir':'/synthetic'}
        runner.rule = {'version':'x5_rule/v2'}
        runner.rule_sha = 'r'; runner.b1_config_head = HEAD
        runner.registry_path = Path('/synthetic/registry'); runner.registry = {}
        runner.state = {}; runner.b1_state_identity = None
        mounted_child = ('25','/synthetic/new','8:1','ext4')
        with mock.patch.object(runtime, 'require_committed_b1_config', return_value=HEAD), \
                mock.patch.object(runtime, 'require_committed_b1_registry'), \
                mock.patch.object(runtime, 'author_gate', return_value=HEAD), \
                mock.patch.object(runtime, 'worker_environment'), \
                mock.patch.object(receipt, '_require_local_filesystem', side_effect=[MOUNT, mounted_child]), \
                mock.patch.object(Path, 'mkdir') as mkdir, \
                mock.patch('r1.exam.b1_state_preserve.write_exclusive_json') as sentinel:
            with self.assertRaisesRegex(runtime.PreparationStop, 'mount differs'):
                runner.start('b1')
        mkdir.assert_called_once()
        sentinel.assert_not_called()

    def test_active_sentinel_refuses_changed_mount_identity(self):
        wrong_mount = ('25','/synthetic/batch','8:1','ext4')
        with mock.patch.object(receipt.os.path, 'lexists', return_value=False), \
                mock.patch.object(receipt, 'read_owned_regular', side_effect=[ACTIVE, COMPLETE]), \
                mock.patch.object(receipt, '_require_local_filesystem', return_value=wrong_mount):
            with self.assertRaisesRegex(RuntimeError, 'sentinel does not bind'):
                receipt.active_and_state('/synthetic/batch', HEAD, PID)

    def test_active_sentinel_accepts_matching_mount_identity(self):
        with mock.patch.object(receipt.os.path, 'lexists', return_value=False), \
                mock.patch.object(receipt, 'read_owned_regular', side_effect=[ACTIVE, COMPLETE]):
            self.assertEqual(receipt.active_and_state('/synthetic/batch', HEAD, PID),
                             (ACTIVE, COMPLETE))


if __name__ == '__main__':
    unittest.main()
