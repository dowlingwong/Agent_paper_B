"""Pure mocked DRYRUN interrupted-root retirement; no filesystem mutation."""
import ast
import copy
import errno
import os
import pathlib
import stat
import types
import unittest
from contextlib import ExitStack
from unittest import mock

from r1.exam import dryrun_root_preserve as retire


class MemoryFS:
    def __init__(self):
        uid = os.getuid()
        def directory(ino, dev=7, owner=uid, mode=0o700):
            return types.SimpleNamespace(st_mode=stat.S_IFDIR | mode, st_uid=owner, st_dev=dev, st_ino=ino)
        self.dirs = {100: directory(1), 101: directory(2), 102: directory(3),
                     103: directory(4), 104: directory(4), 105: directory(5)}
        self.target = None
        self.old = self.dirs[103]
        self.archive_created = False
        self.fail_rename = False
        self.collision = False
        self.change_source = False
        self.source_stats = 0
        self.fsync_failure = False
        self.operations = []
        self.payload = {'root_trials.jsonl': b'synthetic retained bytes'}

    def open(self, name, flags, *, dir_fd=None):
        self.operations.append(('open', str(name), dir_fd))
        mapping = {(None, '/batch'): 100, (100, 'a'): 101, (101, 'b'): 102,
                   (102, 'root'): 104, (100, '_to_delete'): 105}
        return mapping[(dir_fd, str(name))]

    def stat(self, name, *, dir_fd, follow_symlinks):
        assert follow_symlinks is False
        if dir_fd == 102 and name == 'root':
            self.source_stats += 1
            if self.change_source and self.source_stats > 1:
                return types.SimpleNamespace(st_mode=self.old.st_mode, st_uid=self.old.st_uid,
                                             st_dev=self.old.st_dev, st_ino=999)
            if self.old is None:
                raise FileNotFoundError(name)
            return self.old
        if dir_fd == 105 and name == 'interrupted.' + 'a'*32 and self.target is not None:
            return self.target
        raise FileNotFoundError(name)

    def mkdir(self, name, mode, *, dir_fd):
        self.operations.append(('mkdir', name, dir_fd, mode))
        if self.archive_created:
            raise FileExistsError(name)
        self.archive_created = True

    def rename(self, old_fd, old_name, new_fd, new_name, flags):
        self.operations.append(('rename', old_fd, old_name, new_fd, new_name, flags))
        if self.collision:
            raise FileExistsError(new_name)
        if self.fail_rename:
            raise OSError(errno.EOPNOTSUPP, 'unsupported')
        assert (old_fd, old_name, new_fd, flags) == (102, 'root', 105, retire._NOREPLACE)
        self.target = self.old
        self.old = None

    def fsync(self, fd):
        self.operations.append(('fsync', fd))
        if self.fsync_failure:
            raise OSError(errno.EIO, 'synthetic fsync failure')

    def patches(self):
        stack = ExitStack()
        for name, fn in (('open', self.open), ('stat', self.stat), ('mkdir', self.mkdir),
                         ('fsync', self.fsync), ('fstat', lambda fd: self.dirs[fd]),
                         ('close', lambda fd: self.operations.append(('close', fd)))):
            stack.enter_context(mock.patch.object(retire.os, name, side_effect=fn))
        stack.enter_context(mock.patch.object(retire, '_renameat_dryrun', side_effect=self.rename))
        stack.enter_context(mock.patch.object(retire.uuid, 'uuid4', return_value=types.SimpleNamespace(hex='a'*32)))
        return stack


class DryrunRootRetireTests(unittest.TestCase):
    def test_moves_exact_root_to_private_archive_with_payload_retained(self):
        fs = MemoryFS(); original = fs.old; payload = dict(fs.payload)
        with fs.patches():
            target = retire.retire_dryrun_root('/batch', '/batch/a/b/root')
        self.assertEqual(str(target), '/batch/_to_delete/interrupted.' + 'a'*32)
        self.assertIs(fs.target, original)
        self.assertIsNone(fs.old)
        self.assertEqual(fs.payload, payload)
        self.assertEqual(len([x for x in fs.operations if x[0] == 'close']), 6)

    def test_collision_or_unsupported_rename_keeps_source(self):
        for collision in (True, False):
            fs = MemoryFS(); original = fs.old
            fs.collision = collision; fs.fail_rename = not collision
            with fs.patches(), self.assertRaises(OSError):
                retire.retire_dryrun_root('/batch', '/batch/a/b/root')
            self.assertIs(fs.old, original)
            self.assertIsNone(fs.target)
            self.assertEqual(fs.payload['root_trials.jsonl'], b'synthetic retained bytes')

    def test_source_replacement_and_bad_archive_are_refused(self):
        for changed in (True, False):
            fs = MemoryFS(); original = fs.old; fs.change_source = changed
            if not changed:
                fs.dirs[105] = types.SimpleNamespace(st_mode=stat.S_IFDIR | 0o777,
                                                     st_uid=os.getuid(), st_dev=7, st_ino=5)
            with fs.patches(), self.assertRaises(RuntimeError):
                retire.retire_dryrun_root('/batch', '/batch/a/b/root')
            self.assertIs(fs.old, original)
            self.assertIsNone(fs.target)
            self.assertFalse(any(op[0] == 'rename' for op in fs.operations))

    def test_symlink_and_cross_device_source_are_refused(self):
        for symlink in (True, False):
            fs = MemoryFS(); original = fs.old
            original.st_mode = (stat.S_IFLNK | 0o777) if symlink else (stat.S_IFDIR | 0o700)
            original.st_dev = 7 if symlink else 8
            with fs.patches(), self.assertRaises(RuntimeError):
                retire.retire_dryrun_root('/batch', '/batch/a/b/root')
            self.assertIs(fs.old, original)
            self.assertIsNone(fs.target)

    def test_post_rename_fsync_error_leaves_archive(self):
        fs = MemoryFS(); original = fs.old; fs.fsync_failure = True
        with fs.patches(), self.assertRaises(OSError):
            retire.retire_dryrun_root('/batch', '/batch/a/b/root')
        self.assertIs(fs.target, original)
        self.assertIsNone(fs.old)
        self.assertEqual(fs.payload['root_trials.jsonl'], b'synthetic retained bytes')

    def test_invalid_paths_refuse_before_open(self):
        for batch, source in (('/batch', '/elsewhere/root'), ('/batch', '/batch'),
                              ('/batch', '/batch/../escape'), ('/batch', '/batch/_to_delete/root'),
                              ('batch', '/batch/a'), ('/batch', 'batch/a')):
            fs = MemoryFS()
            with fs.patches(), self.assertRaises(RuntimeError):
                retire.retire_dryrun_root(batch, source)
            self.assertFalse(fs.operations)

    def test_actual_root_branch_selects_dryrun_and_legacy_paths(self):
        tree = ast.parse(pathlib.Path('r1/exam/runtime.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ExamRunner')
        root = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'root')
        branch = next(n for n in ast.walk(root) if isinstance(n, ast.If) and any(
            isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'retire_dryrun_root'
            for x in ast.walk(n)))
        branch = copy.deepcopy(branch)
        scope = {'time': types.SimpleNamespace(time_ns=lambda: 123),
                 'spec': {'id':'candidate'}, 'node':'node', 'seed':9001}
        class FakePath:
            def __init__(self, text, trace): self.text = text; self.trace = trace
            def __truediv__(self, name): return FakePath(self.text + '/' + name, self.trace)
            @property
            def parent(self): return FakePath(self.text.rsplit('/', 1)[0], self.trace)
            def mkdir(self, **kwargs): self.trace.append(('mkdir', self.text, kwargs))
            def rename(self, dest): self.trace.append(('rename', self.text, dest.text))
        trace = []; rootpath = FakePath('/batch', trace); path = FakePath('/batch/a/b/root', trace)
        scope.update({'self': types.SimpleNamespace(cfg={'dryrun':True}, out=rootpath), 'path':path})
        program = compile(ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])), '<actual-root-branch>', 'exec')
        with mock.patch.object(retire, 'retire_dryrun_root') as actual:
            exec(program, scope)
        actual.assert_called_once_with(rootpath, path)
        self.assertFalse(trace)
        scope['self'].cfg['dryrun'] = False
        exec(program, scope)
        self.assertEqual(trace[0][0], 'mkdir')
        self.assertEqual(trace[1], ('rename', '/batch/a/b/root', '/batch/interrupted/123_candidate_node_s9001'))


if __name__ == '__main__':
    unittest.main()
