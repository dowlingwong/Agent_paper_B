"""Mock-only tests: no audit, worker, temporary files or deletion."""
import ast
import os
import shutil
import stat
import unittest
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from unittest.mock import Mock, patch


def copy_function():
    path = Path(__file__).parents[1] / 'c3' / 'audit.py'
    tree = ast.parse(path.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_copy_audit_node')
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {'Path': Path, 'PurePosixPath': PurePosixPath, 'os': os, 'shutil': shutil, 'stat': stat}
    exec(compile(module, '<isolated-audit-copy>', 'exec'), scope)
    return scope['_copy_audit_node']


class Handle:
    def __init__(self, fail=False):
        self.writes = []
        self.fail = fail
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def fileno(self): return 17
    def write(self, value):
        self.writes.append(value)
        if self.fail: raise OSError('simulated partial write')


class AuditCopyTest(unittest.TestCase):
    def test_nested_copy_excludes_only_selected_and_exclusively_creates(self):
        fn = copy_function()
        handles = [Handle(), Handle()]
        def copytree(source, destination, ignore):
            self.assertEqual(ignore(str(source), ['root.py', 'nested', '__pycache__', 'keep']),
                             {'root.py', '__pycache__'})
            self.assertEqual(ignore(str(source / 'nested'), ['edit.py', 'keep.py']), {'edit.py'})
        with patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'is_dir', return_value=True), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=0o100755)), \
             patch.object(shutil, 'copytree', side_effect=copytree), \
             patch.object(os, 'open', return_value=17) as opened, \
             patch.object(os, 'fdopen', side_effect=handles), \
             patch.object(os, 'fchmod') as chmod:
            fn(Path('/source'), Path('/destination'), {'root.py': 'a', 'nested/edit.py': 'b'},
               ['root.py', 'nested/edit.py'])
            self.assertEqual([h.writes for h in handles], [['a'], ['b']])
            self.assertEqual(opened.call_count, 2)
            self.assertTrue(all(call.args[1] & os.O_EXCL for call in opened.call_args_list))
            self.assertEqual(chmod.call_count, 2)
            with self.assertRaises(ValueError):
                fn(Path('/source'), Path('/destination'), {'../oops': 'x'}, ['../oops'])
            with self.assertRaises(ValueError):
                fn(Path('/source'), Path('/destination'), {'other.py': 'x'}, ['root.py'])

    def test_collision_and_write_failure_do_not_cleanup(self):
        fn = copy_function()
        with patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=0o100644)), \
             patch.object(shutil, 'copytree'), patch.object(Path, 'unlink') as unlink, \
             patch.object(os, 'open', side_effect=FileExistsError('collision')):
            with self.assertRaises(FileExistsError):
                fn(Path('/source'), Path('/destination'), {'root.py': 'x'}, ['root.py'])
            unlink.assert_not_called()
        handle = Handle(fail=True)
        with patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=0o100644)), \
             patch.object(shutil, 'copytree'), patch.object(Path, 'unlink') as unlink, \
             patch.object(os, 'open', return_value=17), patch.object(os, 'fdopen', return_value=handle), \
             patch.object(os, 'fchmod'):
            with self.assertRaises(OSError):
                fn(Path('/source'), Path('/destination'), {'root.py': 'partial'}, ['root.py'])
            self.assertEqual(handle.writes, ['partial'])
            unlink.assert_not_called()


if __name__ == '__main__':
    unittest.main()
