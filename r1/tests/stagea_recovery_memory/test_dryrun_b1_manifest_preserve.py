"""Pure mock checks for synthetic B1 candidate-manifest preservation."""
import ast
import copy
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class DryrunB1ManifestTests(unittest.TestCase):
    path = pathlib.Path('/synthetic/batch/candidate/b1_manifest.json')

    def publish(self, fs, value):
        def identity(path):
            self.assertEqual(path, self.path)
            return None if fs.current is None else (fs.current.st_dev, fs.current.st_ino)
        with fs.patches(), mock.patch.object(pathlib.Path,'mkdir') as mkdir, \
             mock.patch.object(preserve,'existing_identity',side_effect=identity), \
             mock.patch.object(preserve,'_renameat_dryrun',side_effect=fs.rename):
            result=preserve.publish_dryrun_b1_manifest(self.path,value)
        mkdir.assert_called_once_with(parents=True,exist_ok=True)
        return result

    def test_two_versions_preserve_prior_inode_and_legacy_reader_bytes(self):
        fs=MemoryFS()
        first_value={'phase':'b1','status':'COMPLETE','candidate':'fixture','metrics':[1,2]}
        second_value={'phase':'b1','status':'COMPLETE','candidate':'fixture','metrics':[1,2,3]}
        first=self.publish(fs,first_value);first_bytes=fs.contents[103]
        second=self.publish(fs,second_value)
        self.assertEqual((fs.files[fs.names[-1]].st_dev,fs.files[fs.names[-1]].st_ino),first)
        self.assertEqual((fs.current.st_dev,fs.current.st_ino),second)
        self.assertEqual(json.loads(first_bytes),first_value)
        self.assertEqual(json.loads(fs.contents[103]),second_value)
        legacy=(json.dumps(second_value,indent=2,allow_nan=False)+'\n').encode()
        self.assertEqual(fs.contents[103],legacy)
        self.assertEqual(hashlib.sha256(fs.contents[103]).hexdigest(),hashlib.sha256(legacy).hexdigest())

    def test_identity_race_and_unsupported_rename_keep_old(self):
        for race in (True,False):
            fs=MemoryFS();old=fs.info(0o100600,44);fs.current=old
            fs.change_before_rename=race;fs.fail_rename=not race
            with self.assertRaises((RuntimeError,OSError)):
                self.publish(fs,{'phase':'b1'})
            self.assertIs(fs.current,old);self.assertEqual(len(fs.files),1)

    def test_bad_name_or_relative_path_refuses_before_mkdir(self):
        with mock.patch.object(pathlib.Path,'mkdir') as mkdir:
            for target in ('relative/b1_manifest.json','/synthetic/b2_manifest.json'):
                with self.assertRaises(RuntimeError):preserve.publish_dryrun_b1_manifest(target,{})
        mkdir.assert_not_called()

    def test_actual_dispatch_changes_only_dryrun_b1(self):
        tree=ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        helper=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_write_candidate_manifest'))
        legacy=mock.Mock(return_value='legacy');scope={'write_json':legacy}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[helper],type_ignores=[])),'<candidate-manifest-dispatch>','exec'),scope)
        with mock.patch.object(preserve,'publish_dryrun_b1_manifest',return_value='retained') as retained:
            self.assertEqual(scope['_write_candidate_manifest'](self.path,{'x':1},phase='b1',dryrun=True),'retained')
            self.assertEqual(scope['_write_candidate_manifest'](self.path,{'x':1},phase='b1',dryrun=False),'legacy')
            self.assertEqual(scope['_write_candidate_manifest'](self.path,{'x':1},phase='b2',dryrun=True),'legacy')
        retained.assert_called_once_with(self.path,{'x':1});self.assertEqual(legacy.call_count,2)

    def test_actual_call_and_row_append_remain_present(self):
        tree=ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_evidence_unreviewed')
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_write_candidate_manifest']
        self.assertEqual(len(calls),1)
        self.assertEqual({k.arg for k in calls[0].keywords},{'phase','dryrun'})
        self.assertIn("f'{phase}_manifest.json'",ast.unparse(fn))
        self.assertIn('rows.append(manifest)',ast.unparse(fn))


if __name__=='__main__':unittest.main()
