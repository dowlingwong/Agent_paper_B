"""Pure mocked DRYRUN server record preservation; no filesystem mutation."""
import ast
import copy
import json
import pathlib
import types
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class DryrunServerRecordTests(unittest.TestCase):
    path = pathlib.Path('/synthetic/servers/llama_server_123_r1.json')

    def test_start_and_stop_records_keep_prior_inode(self):
        fs = MemoryFS()
        with fs.patches(), mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
            start = preserve.publish_dryrun_server_record(self.path, {'pid': 7}, None)
            start_bytes = fs.contents[103]
            stopped = preserve.publish_dryrun_server_record(self.path, {'pid': 7, 'stopped_utc': 'fixture'}, start)
        retired = fs.files[fs.names[-1]]
        self.assertEqual((retired.st_dev, retired.st_ino), start)
        self.assertEqual(json.loads(start_bytes), {'pid': 7})
        self.assertEqual(json.loads(fs.contents[103]), {'pid': 7, 'stopped_utc': 'fixture'})
        self.assertEqual((fs.current.st_dev, fs.current.st_ino), stopped)

    def test_existing_and_unsupported_operations_do_not_replace_old(self):
        for collision in (True, False):
            fs = MemoryFS(); original = fs.info(0o100600, 44); fs.current = original
            fs.fail_rename = not collision
            with fs.patches(), mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
                with self.assertRaises((RuntimeError, OSError)):
                    preserve.publish_dryrun_server_record(self.path, {'pid': 7}, None if collision else (7,44))
            self.assertIs(fs.current, original)
            self.assertEqual(len(fs.files), 0 if collision else 1)

    def test_actual_save_dispatches_three_paths(self):
        source = pathlib.Path('r1/scripts/llama_server_instance.py').read_text()
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'LlamaServerInstance')
        method = copy.deepcopy(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_save'))
        scope = {'json': json}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), '<actual-server-save>', 'exec'), scope)
        record = {'pid': 7}; path = mock.Mock()
        obj = types.SimpleNamespace(label='DRYRUN', record_path=path, record=record, dryrun_record_identity=(7,1))
        with mock.patch.object(preserve, 'publish_dryrun_server_record', return_value=(7,2)) as dry:
            scope['_save'](obj)
        dry.assert_called_once_with(path, record, (7,1))
        self.assertEqual(obj.dryrun_record_identity, (7,2)); path.write_text.assert_not_called()
        obj.label = 'ENGINEERING_ONLY'
        scope['_save'](obj)
        path.write_text.assert_called_once_with(json.dumps(record, indent=2)+'\n')
        obj.label = 'DRYRUN'; obj.b1_record_identity = (7,3)
        obj.b1_containment = types.SimpleNamespace(write_active=lambda callback: callback())
        with mock.patch.object(preserve, 'publish_server_record', return_value=(7,4)) as production:
            scope['_save'](obj)
        production.assert_called_once_with(path, record, (7,3))
        self.assertEqual(obj.b1_record_identity, (7,4))

    def test_invalid_name_refuses_before_open(self):
        with mock.patch.object(preserve.os, 'open') as opened:
            with self.assertRaises(RuntimeError):
                preserve.publish_dryrun_server_record('/synthetic/not_a_server.json', {}, None)
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()
