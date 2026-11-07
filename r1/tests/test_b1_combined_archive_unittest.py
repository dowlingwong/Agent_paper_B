"""In-memory composition checks; no filesystem operations or subprocesses."""
import hashlib
import json
import os
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from r1.exam import b1_cgroup as control
from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class CombinedArchiveTests(unittest.TestCase):
    def test_state_publication_then_lock_retirement_reuses_archive(self):
        fs = MemoryFS()
        with fs.patches():
            state = preserve.publish_state(Path('/synthetic/batch/batch_state.json'),
                                           {'phase': 'b1', 'status': 'RUNNING'}, None)
        self.assertTrue(fs.archive_exists)
        self.assertEqual(state, (7, 1001))
        payload = json.dumps({'pid': 55, 'host': 'synthetic'}).encode()
        lock = SimpleNamespace(st_dev=7, st_ino=3, st_uid=fs.uid, st_mode=stat.S_IFREG | 0o600)
        directory = SimpleNamespace(st_dev=7, st_uid=fs.uid, st_mode=stat.S_IFDIR | 0o700)
        def lstat(path):
            return lock if path.name == 'runner.lock' else directory
        def mkdir(path, mode, exist_ok):
            self.assertTrue(fs.archive_exists)
            self.assertTrue(exist_ok)
            self.assertEqual(path, Path('/synthetic/batch/_to_delete'))
        rename = Mock(return_value=0)
        with patch.object(Path, 'lstat', autospec=True, side_effect=lstat), \
             patch.object(Path, 'read_bytes', return_value=payload), \
             patch.object(Path, 'mkdir', autospec=True, side_effect=mkdir), \
             patch.object(control.os, 'getpid', return_value=55), \
             patch.object(control.ctypes, 'CDLL', return_value=Mock(renameat2=rename)):
            control.retire_runner_lock('/synthetic/batch/runner.lock', (7, 3, fs.uid),
                                       hashlib.sha256(payload).hexdigest())
        self.assertEqual(rename.call_args.args[-1].value, 1)
        self.assertEqual(json.loads(fs.contents[103])['status'], 'RUNNING')


if __name__ == '__main__':
    unittest.main()
