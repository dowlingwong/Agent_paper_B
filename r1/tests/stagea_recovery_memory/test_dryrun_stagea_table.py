"""Pure mocked DRYRUN Stage A table preservation; no filesystem mutation."""
import ast
import copy
import hashlib
import json
import pathlib
import sys
import types
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class StageATableTests(unittest.TestCase):
    path = pathlib.Path('/synthetic/stage-a/stage_a_table.json')

    def publish(self, fs, value):
        def identity(path):
            self.assertEqual(path, self.path)
            return None if fs.current is None else (fs.current.st_dev, fs.current.st_ino)
        with fs.patches(), mock.patch.object(pathlib.Path, 'mkdir') as mkdir, \
             mock.patch.object(preserve, 'existing_identity', side_effect=identity), \
             mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
            result = preserve.publish_dryrun_stage_a_table(self.path, value)
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        return result

    def test_two_tables_preserve_previous_inode_and_reader_bytes(self):
        fs = MemoryFS()
        first_value = {'label': 'ENGINEERING_ONLY', 'rows': [{'candidate': 'a', 'passed': True}]}
        second_value = {'label': 'ENGINEERING_ONLY', 'rows': [{'candidate': 'a', 'passed': False}]}
        first = self.publish(fs, first_value)
        first_bytes = fs.contents[103]
        second = self.publish(fs, second_value)
        retired = fs.files[fs.names[-1]]
        self.assertEqual((retired.st_dev, retired.st_ino), first)
        self.assertEqual((fs.current.st_dev, fs.current.st_ino), second)
        self.assertEqual(json.loads(first_bytes), first_value)
        self.assertEqual(json.loads(fs.contents[103]), second_value)
        # Legacy write_json serialized the same indent, no NaN, and newline.
        legacy_bytes = (json.dumps(second_value, indent=2, allow_nan=False) + '\n').encode()
        self.assertEqual(fs.contents[103], legacy_bytes)
        self.assertEqual(hashlib.sha256(fs.contents[103]).hexdigest(), hashlib.sha256(legacy_bytes).hexdigest())

    def test_identity_race_and_unsupported_rename_preserve_old(self):
        for race in (True, False):
            fs = MemoryFS(); original = fs.info(0o100600, 44); fs.current = original
            fs.change_before_rename = race; fs.fail_rename = not race
            with self.assertRaises((RuntimeError, OSError)):
                self.publish(fs, {'rows': []})
            self.assertIs(fs.current, original)
            self.assertEqual(len(fs.files), 1)

    def test_bad_target_refuses_before_directory_creation(self):
        with mock.patch.object(pathlib.Path, 'mkdir') as mkdir:
            for target in ('relative/stage_a_table.json', '/synthetic/wrong.json'):
                with self.assertRaises(RuntimeError):
                    preserve.publish_dryrun_stage_a_table(target, {})
        mkdir.assert_not_called()

    def test_actual_dispatch_keeps_production_writer(self):
        tree = ast.parse(pathlib.Path('r1/exam/stage_a.py').read_text())
        helper = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'write_stage_a_table'))
        scope = {}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[])), '<stage-a-table-dispatch>', 'exec'), scope)
        campaign = types.ModuleType('r1.exam.campaign'); campaign.write_json = mock.Mock(return_value='legacy')
        with mock.patch.object(preserve, 'publish_dryrun_stage_a_table', return_value='retained') as retained, \
             mock.patch.dict(sys.modules, {'r1.exam.campaign': campaign}):
            self.assertEqual(scope['write_stage_a_table'](self.path, {'rows': []}, dryrun=True), 'retained')
            self.assertEqual(scope['write_stage_a_table'](self.path, {'rows': []}, dryrun=False), 'legacy')
        retained.assert_called_once_with(self.path, {'rows': []})
        campaign.write_json.assert_called_once_with(self.path, {'rows': []})

    def test_actual_table_call_and_canonical_readers(self):
        tree = ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_stage_a_cooperative')
        calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'write_stage_a_table']
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertTrue(any(k.arg == 'dryrun' for k in call.keywords))
        self.assertIn('stage_a_table.json', ast.unparse(call.args[0]))
        fixture_source = pathlib.Path('r1/tests/test_exam_stagea_b1_crash_recovery.py').read_text()
        self.assertIn("runner.out/'stage_a_table.json'", fixture_source)


if __name__ == '__main__':
    unittest.main()
