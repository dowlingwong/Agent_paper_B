"""Pure mocked DRYRUN state preservation checks; no filesystem mutation."""
import ast
import copy
import errno
import json
import pathlib
import types
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class DryrunStateTests(unittest.TestCase):
    def test_two_publications_keep_prior_inode_and_bytes(self):
        fs = MemoryFS()
        with fs.patches(), mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
            first = preserve.publish_dryrun_state('/synthetic/batch/batch_state.json', {'n': 1}, None)
            first_bytes = fs.contents[103]
            second = preserve.publish_dryrun_state('/synthetic/batch/batch_state.json', {'n': 2}, first)
        self.assertNotEqual(first, second)
        self.assertEqual(json.loads(first_bytes), {'n': 1})
        retired = fs.files[fs.names[-1]]
        self.assertEqual((retired.st_dev, retired.st_ino), first)
        self.assertEqual(json.loads(fs.contents[103]), {'n': 2})

    def test_unsupported_rename_leaves_old_and_candidate(self):
        fs = MemoryFS()
        original = fs.info(0o100600, 44)
        fs.current = original
        fs.fail_rename = True
        with fs.patches(), mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
            with self.assertRaises(OSError):
                preserve.publish_dryrun_state('/synthetic/batch/batch_state.json', {'n': 2}, (7, 44))
        self.assertIs(fs.current, original)
        self.assertEqual(len(fs.files), 1)
        self.assertEqual(json.loads(fs.contents[103]), {'n': 2})

    def test_darwin_flag_mapping_and_failure(self):
        libc = types.SimpleNamespace(renameatx_np=mock.Mock(return_value=0))
        with mock.patch.object(preserve.sys, 'platform', 'darwin'), \
             mock.patch.object(preserve.ctypes, 'CDLL', return_value=libc):
            preserve._renameat_dryrun(1, 'old', 2, 'new', preserve._NOREPLACE)
            self.assertEqual(libc.renameatx_np.call_args.args[-1], 0x4)
            preserve._renameat_dryrun(1, 'old', 2, 'new', preserve._EXCHANGE)
            self.assertEqual(libc.renameatx_np.call_args.args[-1], 0x2)
            libc.renameatx_np.return_value = -1
            with mock.patch.object(preserve.ctypes, 'get_errno', return_value=errno.EEXIST):
                with self.assertRaises(OSError) as error:
                    preserve._renameat_dryrun(1, 'old', 2, 'new', preserve._NOREPLACE)
            self.assertEqual(error.exception.errno, errno.EEXIST)

    def test_other_platform_refuses_before_libc(self):
        with mock.patch.object(preserve.sys, 'platform', 'win32'), \
             mock.patch.object(preserve.ctypes, 'CDLL') as libc:
            with self.assertRaises(OSError):
                preserve._renameat_dryrun(1, 'old', 2, 'new', preserve._NOREPLACE)
        libc.assert_not_called()

    def test_actual_save_dispatch_and_identity_update(self):
        source = pathlib.Path('r1/exam/runtime.py').read_text()
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'ExamRunner')
        method = copy.deepcopy(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'save'))
        module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
        legacy = mock.Mock()
        scope = {'write_json': legacy}
        exec(compile(module, '<actual-save>', 'exec'), scope)
        obj = types.SimpleNamespace(cfg={'dryrun': True}, state={'phase': 'b1'},
                                    out=pathlib.Path('/synthetic/batch'), dryrun_state_identity=(7, 1))
        with mock.patch.object(preserve, 'publish_dryrun_state', return_value=(7, 2)) as publish:
            scope['save'](obj)
        publish.assert_called_once_with(obj.out/'batch_state.json', obj.state, (7, 1))
        self.assertEqual(obj.dryrun_state_identity, (7, 2))
        legacy.assert_not_called()
        obj.cfg['dryrun'] = False
        obj.b1_state_identity = (7, 3)
        with mock.patch.object(preserve, 'publish_state', return_value=(7, 4)) as publish:
            scope['save'](obj)
        publish.assert_called_once_with(obj.out/'batch_state.json', obj.state, (7, 3))
        self.assertEqual(obj.b1_state_identity, (7, 4))
        obj.state['phase'] = 'stage-a'
        scope['save'](obj)
        legacy.assert_called_once_with(obj.out/'batch_state.json', obj.state)


if __name__ == '__main__':
    unittest.main()
