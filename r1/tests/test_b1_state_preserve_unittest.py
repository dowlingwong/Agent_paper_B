"""In-memory tests for preservation logic; no filesystem or kernel operations."""
import errno
import io
import json
import os
import stat
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from r1.exam import b1_state_preserve as preserve


class MemoryFS:
    def __init__(self, current=None):
        self.uid = os.getuid()
        self.parent = self.info(stat.S_IFDIR | 0o700, 1)
        self.archive = self.info(stat.S_IFDIR | 0o700, 2)
        self.current = current
        self.archive_exists = False
        self.files = {}
        self.contents = {}
        self.names = []
        self.fail_rename = False
        self.change_before_rename = False
        self.target_stats = 0
        self.fail_dir_fsync = False
        self.race_at_initial_rename = False

    def info(self, mode, ino):
        return SimpleNamespace(st_mode=mode, st_uid=self.uid, st_dev=7, st_ino=ino)

    def open(self, path, flags, mode=0o777, *, dir_fd=None):
        if dir_fd is None:
            return 101
        if dir_fd == 101 and path == '_to_delete':
            return 102
        if dir_fd == 102:
            if path in self.files:
                raise FileExistsError(path)
            self.names.append(path)
            self.files[path] = self.info(stat.S_IFREG | 0o600, 1000 + len(self.names))
            self.contents[103] = b''
            return 103
        raise AssertionError((path, dir_fd))

    def mkdir(self, path, mode, *, dir_fd):
        if self.archive_exists:
            raise FileExistsError(path)
        self.archive_exists = True

    def fstat(self, fd):
        if fd == 101:
            return self.parent
        if fd == 102:
            return self.archive
        if fd == 103:
            return self.files[self.names[-1]]
        raise AssertionError(fd)

    def stat(self, path, *, dir_fd, follow_symlinks):
        if dir_fd == 101:
            self.target_stats += 1
            if self.change_before_rename and self.target_stats > 1:
                return self.info(stat.S_IFREG | 0o600, 999)
            if self.current is None:
                raise FileNotFoundError(path)
            return self.current
        if dir_fd == 102:
            return self.files[path]
        raise AssertionError(dir_fd)

    def write(self, fd, data):
        # Simulate short writes to ensure publication waits for all bytes.
        chunk = bytes(data[:7])
        self.contents[fd] += chunk
        return len(chunk)

    def rename(self, old_fd, old_name, new_fd, new_name, flags):
        if self.fail_rename:
            raise OSError(errno.EOPNOTSUPP, 'synthetic unsupported filesystem')
        new = self.files[old_name]
        if flags == preserve._NOREPLACE:
            if self.race_at_initial_rename:
                self.current = self.info(stat.S_IFREG | 0o600, 777)
            if self.current is not None:
                raise FileExistsError(new_name)
            self.current = new
            del self.files[old_name]
        elif flags == preserve._EXCHANGE:
            old = self.current
            self.current = new
            self.files[old_name] = old
        else:
            raise AssertionError(flags)

    def fsync(self, fd):
        if self.fail_dir_fsync and fd == 102:
            raise OSError(errno.EIO, 'synthetic directory fsync failure')

    def patches(self):
        stack = ExitStack()
        for name in ('open', 'mkdir', 'fstat', 'stat', 'write'):
            stack.enter_context(mock.patch.object(preserve.os, name, getattr(self, name)))
        stack.enter_context(mock.patch.object(preserve.os, 'close', lambda *args: None))
        stack.enter_context(mock.patch.object(preserve.os, 'fsync', self.fsync))
        stack.enter_context(mock.patch.object(preserve, '_renameat2', self.rename))
        stack.enter_context(mock.patch.object(preserve.uuid, 'uuid4',
                                             side_effect=lambda: SimpleNamespace(hex=f'{len(self.names):032x}')))
        return stack


class StatePreservationTests(unittest.TestCase):
    path = Path('/synthetic/batch/batch_state.json')

    def test_publish_then_exchange_retains_old_inode(self):
        fs = MemoryFS()
        with fs.patches():
            first = preserve.publish_state(self.path, {'phase': 'b1', 'status': 'RUNNING'}, None)
            first_payload = json.loads(fs.contents[103])
            second = preserve.publish_state(self.path, {'phase': 'b1', 'status': 'COMPLETE'}, first)
        self.assertNotEqual(first, second)
        self.assertEqual((fs.current.st_dev, fs.current.st_ino), second)
        retired = fs.files[fs.names[-1]]
        self.assertEqual((retired.st_dev, retired.st_ino), first)
        self.assertEqual(first_payload['status'], 'RUNNING')
        self.assertEqual(json.loads(fs.contents[103])['status'], 'COMPLETE')

    def test_unsupported_exchange_preserves_current_and_candidate(self):
        original = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=os.getuid(), st_dev=7, st_ino=44)
        fs = MemoryFS(original)
        fs.fail_rename = True
        with fs.patches():
            with self.assertRaises(OSError):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, (7, 44))
        self.assertIs(fs.current, original)
        self.assertEqual(len(fs.files), 1)
        self.assertEqual(json.loads(fs.contents[103])['status'], 'RUNNING')

    def test_unexpected_existing_state_stops_before_archive_creation(self):
        original = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=os.getuid(), st_dev=7, st_ino=44)
        fs = MemoryFS(original)
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'identity changed'):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, None)
        self.assertFalse(fs.archive_exists)
        self.assertIs(fs.current, original)

    def test_symlink_state_is_refused(self):
        symlink = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_uid=os.getuid(), st_dev=7, st_ino=55)
        fs = MemoryFS(symlink)
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'owned regular'):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, (7, 55))
        self.assertFalse(fs.archive_exists)

    def test_group_writable_prior_state_is_refused(self):
        unsafe = SimpleNamespace(st_mode=stat.S_IFREG | 0o660, st_uid=os.getuid(), st_dev=7, st_ino=55)
        fs = MemoryFS(unsafe)
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'owned regular'):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, (7, 55))
        self.assertFalse(fs.archive_exists)

    def test_change_before_exchange_preserves_both_names(self):
        original = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=os.getuid(), st_dev=7, st_ino=44)
        fs = MemoryFS(original)
        fs.change_before_rename = True
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'changed before publication'):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, (7, 44))
        self.assertIs(fs.current, original)
        self.assertEqual(len(fs.files), 1)

    def test_failure_after_exchange_retains_both_inodes(self):
        original = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=os.getuid(), st_dev=7, st_ino=44)
        fs = MemoryFS(original)
        fs.fail_dir_fsync = True
        with fs.patches():
            with self.assertRaises(OSError):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, (7, 44))
        self.assertEqual(fs.files[fs.names[-1]].st_ino, 44)
        self.assertNotEqual(fs.current.st_ino, 44)

    def test_insecure_batch_directory_is_refused(self):
        fs = MemoryFS()
        fs.parent.st_mode = stat.S_IFDIR | 0o777
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'directory is not owned'):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, None)
        self.assertFalse(fs.archive_exists)

    def test_initial_collision_does_not_replace_existing_state(self):
        fs = MemoryFS()
        fs.race_at_initial_rename = True
        with fs.patches():
            with self.assertRaises(FileExistsError):
                preserve.publish_state(self.path, {'status': 'RUNNING'}, None)
        self.assertEqual(fs.current.st_ino, 777)
        self.assertEqual(len(fs.files), 1)

    def test_nonfinite_state_fails_before_filesystem_access(self):
        fs = MemoryFS()
        with fs.patches():
            with self.assertRaises(ValueError):
                preserve.publish_state(self.path, {'value': float('nan')}, None)
        self.assertFalse(fs.archive_exists)

    def test_runtime_selects_preserving_writer_only_for_production_b1(self):
        from r1.exam import runtime
        runner = SimpleNamespace(out=Path('/synthetic/batch'), state={'phase': 'b1'},
                                 cfg={'dryrun': False}, b1_state_identity=(7, 44))
        with mock.patch.object(preserve, 'publish_state', return_value=(7, 45)) as writer, \
                mock.patch.object(runtime, 'write_json') as legacy:
            runtime.ExamRunner.save(runner)
            self.assertEqual(runner.b1_state_identity, (7, 45))
            writer.assert_called_once()
            legacy.assert_not_called()
            runner.cfg['dryrun'] = True
            runtime.ExamRunner.save(runner)
            legacy.assert_called_once()

    def test_post_exchange_failure_stop_save_failure_has_no_waited_receipt(self):
        from r1.exam import runtime, b1_exit_receipt
        for attempted_status in ('RUNNING', 'COMPLETE'):
            with self.subTest(attempted_status=attempted_status):
                original = SimpleNamespace(st_mode=stat.S_IFREG | 0o600,
                                           st_uid=os.getuid(), st_dev=7, st_ino=44)
                fs = MemoryFS(original)
                fs.fail_dir_fsync = True
                runner = SimpleNamespace(out=Path('/synthetic/batch'),
                                         cfg={'dryrun':False},
                                         state={'phase':'b1','status':attempted_status},
                                         b1_state_identity=(7,44))
                runner.save = lambda: runtime.ExamRunner.save(runner)
                stderr = io.StringIO()
                with fs.patches(), mock.patch.object(runtime.sys, 'stderr', stderr), \
                        mock.patch.object(b1_exit_receipt, 'write_exclusive_json') as write:
                    with self.assertRaises(OSError):
                        runner.save()
                    self.assertNotEqual(fs.current.st_ino, 44)
                    self.assertEqual(runner.b1_state_identity, (7,44))
                    runner.state['status'] = 'STOPPED'
                    runtime.report_b1_stop_and_save(runner, OSError('post-exchange failure'))
                    self.assertIn('state save failed', stderr.getvalue())
                    child = SimpleNamespace(pid=99, wait=lambda: 1)
                    with self.assertRaisesRegex(RuntimeError, 'did not exit successfully'):
                        b1_exit_receipt.publish_after_wait(child, '/synthetic/batch', 'a'*40)
                    write.assert_not_called()
                    with mock.patch.object(b1_exit_receipt, '_require_local_filesystem'), \
                            mock.patch.object(b1_exit_receipt, 'read_owned_regular', side_effect=FileNotFoundError):
                        with self.assertRaises(FileNotFoundError):
                            b1_exit_receipt.verify_waited_success('/synthetic/batch', 'a'*40)


if __name__ == '__main__':
    unittest.main()
