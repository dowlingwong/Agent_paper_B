"""Pure in-memory checks; no real files, subprocesses or kernel operations."""
import hashlib
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS
from r1.scripts.llama_server_instance import LlamaServerInstance


class VersionFS(MemoryFS):
    def __init__(self):
        super().__init__()
        self.by_inode = {}

    def rename(self, old_fd, old_name, new_fd, new_name, flags):
        candidate = self.files[old_name]
        self.by_inode[candidate.st_ino] = self.contents[103]
        super().rename(old_fd, old_name, new_fd, new_name, flags)


class OtherSnapshotTests(unittest.TestCase):
    def test_two_audit_cache_versions_preserve_old_bytes_and_canonical_json(self):
        fs = VersionFS()
        path = Path('/synthetic/root/audit_cache.json')
        with fs.patches():
            first = preserve.publish_audit_cache(path, {'a': [1.0]}, None)
            second = preserve.publish_audit_cache(path, {'a': [1.0], 'b': [2.0]}, first)
        self.assertNotEqual(first, second)
        self.assertEqual(json.loads(fs.by_inode[first[1]]), {'a': [1.0]})
        self.assertEqual(json.loads(fs.by_inode[second[1]]), {'a': [1.0], 'b': [2.0]})
        self.assertEqual(fs.files[fs.names[-1]].st_ino, first[1])
        self.assertTrue(all(name.startswith('audit_cache.') for name in fs.names))

    def test_contained_server_saves_versions_and_guard_wraps_both(self):
        fs = VersionFS()
        inst = LlamaServerInstance.__new__(LlamaServerInstance)
        inst.record_path = Path('/synthetic/server/llama_server_8080.json')
        inst.record = {'pid': 123, 'status': 'starting'}
        inst.b1_record_identity = None
        containment = mock.Mock()
        containment.write_active.side_effect = lambda callback: callback()
        inst.b1_containment = containment
        with fs.patches():
            inst._save()
            first = inst.b1_record_identity
            inst.record['status'] = 'ready'
            inst._save()
            second = inst.b1_record_identity
        self.assertEqual(containment.write_active.call_count, 2)
        self.assertEqual(json.loads(fs.by_inode[first[1]])['status'], 'starting')
        self.assertEqual(json.loads(fs.by_inode[second[1]])['status'], 'ready')
        self.assertEqual(fs.files[fs.names[-1]].st_ino, first[1])
        self.assertTrue(all(name.startswith('server_record.') for name in fs.names))

    def test_unrelated_paths_refused_before_file_operations(self):
        with mock.patch.object(preserve.os, 'open') as opened:
            for function, path in ((preserve.publish_audit_cache, '/synthetic/other.json'),
                                   (preserve.publish_server_record, '/synthetic/llama_server_x.json')):
                with self.assertRaisesRegex(RuntimeError, 'invalid B1 snapshot'):
                    function(path, {}, None)
        opened.assert_not_called()

    def test_existing_foreign_target_refused_without_candidate(self):
        fs = VersionFS()
        fs.current = fs.info(0o100600, 77)
        with fs.patches():
            with self.assertRaisesRegex(RuntimeError, 'identity changed'):
                preserve.publish_audit_cache('/synthetic/root/audit_cache.json', {}, None)
        self.assertFalse(fs.archive_exists)
        self.assertEqual(fs.names, [])


if __name__ == '__main__':
    unittest.main()
