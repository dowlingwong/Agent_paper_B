"""Pure mocked Stage A result preservation checks; no filesystem mutations."""
import ast
import copy
import json
import pathlib
import sys
import types
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class StageAResultTests(unittest.TestCase):
    path = pathlib.Path('/synthetic/stage-a/32768/stage_a.json')

    def publish(self, fs, value):
        def identity(path):
            self.assertEqual(path, self.path)
            return None if fs.current is None else (fs.current.st_dev, fs.current.st_ino)
        with fs.patches(), mock.patch.object(pathlib.Path, 'mkdir') as mkdir, \
             mock.patch.object(preserve, 'existing_identity', side_effect=identity), \
             mock.patch.object(preserve, '_renameat_dryrun', side_effect=fs.rename):
            result = preserve.publish_dryrun_stage_a_result(self.path, value)
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        return result

    def test_child_and_two_parent_versions_retain_prior_inodes(self):
        fs = MemoryFS()
        child = self.publish(fs, {'child': 1})
        child_bytes = fs.contents[103]
        parent = self.publish(fs, {'child': 1, 'qualification': 'PINNED'})
        parent_bytes = fs.contents[103]
        final = self.publish(fs, {'child': 1, 'qualification': 'PINNED', 'source_label': 'fixture'})
        self.assertEqual(json.loads(child_bytes), {'child': 1})
        self.assertEqual(json.loads(parent_bytes), {'child': 1, 'qualification': 'PINNED'})
        self.assertEqual((fs.files[fs.names[1]].st_dev, fs.files[fs.names[1]].st_ino), child)
        self.assertEqual((fs.files[fs.names[2]].st_dev, fs.files[fs.names[2]].st_ino), parent)
        self.assertEqual((fs.current.st_dev, fs.current.st_ino), final)
        self.assertEqual(json.loads(fs.contents[103])['source_label'], 'fixture')

    def test_existing_identity_change_and_unsupported_rename_preserve_current(self):
        for race in (True, False):
            fs = MemoryFS(); original = fs.info(0o100600, 44); fs.current = original
            fs.change_before_rename = race; fs.fail_rename = not race
            with self.assertRaises((RuntimeError, OSError)):
                self.publish(fs, {'new': True})
            self.assertIs(fs.current, original)
            self.assertEqual(len(fs.files), 1)

    def test_bad_target_refuses_before_mkdir(self):
        with mock.patch.object(pathlib.Path, 'mkdir') as mkdir:
            for target in ('relative/stage_a.json', '/synthetic/wrong.json'):
                with self.assertRaises(RuntimeError):
                    preserve.publish_dryrun_stage_a_result(target, {})
        mkdir.assert_not_called()

    def test_actual_dispatch_preserves_production_call(self):
        tree = ast.parse(pathlib.Path('r1/exam/stage_a.py').read_text())
        helper = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'write_stage_a_result'))
        module = ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[]))
        scope = {}
        exec(compile(module, '<stage-a-result-dispatch>', 'exec'), scope)
        fake_campaign = types.ModuleType('r1.exam.campaign'); fake_campaign.write_json = mock.Mock(return_value='legacy')
        with mock.patch.object(preserve, 'publish_dryrun_stage_a_result', return_value='retained') as retained, \
             mock.patch.dict(sys.modules, {'r1.exam.campaign': fake_campaign}):
            self.assertEqual(scope['write_stage_a_result'](self.path, {'x': 1}, dryrun=True), 'retained')
            self.assertEqual(scope['write_stage_a_result'](self.path, {'x': 1}, dryrun=False), 'legacy')
        retained.assert_called_once_with(self.path, {'x': 1})
        fake_campaign.write_json.assert_called_once_with(self.path, {'x': 1})

    def test_real_call_sites_use_dispatch(self):
        runner = ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        worker = ast.parse(pathlib.Path('r1/exam/stage_a.py').read_text())
        fixture = ast.parse(pathlib.Path('r1/tests/test_exam_stagea_b1_crash_recovery.py').read_text())
        function = next(n for n in runner.body if isinstance(n, ast.FunctionDef) and n.name == '_stage_a_cooperative')
        calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'write_stage_a_result']
        self.assertEqual(len(calls), 5)
        for call in calls:
            self.assertTrue(any(k.arg == 'dryrun' for k in call.keywords))
        for tree in (worker, fixture):
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'write_stage_a_result' for n in ast.walk(tree)))


if __name__ == '__main__':
    unittest.main()
