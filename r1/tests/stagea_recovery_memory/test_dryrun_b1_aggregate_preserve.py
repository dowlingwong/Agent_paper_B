"""Pure mock checks for synthetic B1 aggregate-manifest preservation."""
import ast
import copy
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class DryrunB1AggregateTests(unittest.TestCase):
    aggregate = pathlib.Path('/synthetic/batch/b1_manifests.json')
    candidate = pathlib.Path('/synthetic/batch/a/b1_manifest.json')

    def publish(self, fs, path, value, function):
        def identity(actual):
            self.assertEqual(actual, path)
            return None if fs.current is None else (fs.current.st_dev, fs.current.st_ino)
        with fs.patches(), mock.patch.object(pathlib.Path,'mkdir') as mkdir, \
             mock.patch.object(preserve,'existing_identity',side_effect=identity), \
             mock.patch.object(preserve,'_renameat_dryrun',side_effect=fs.rename):
            result=function(path,value)
        mkdir.assert_called_once_with(parents=True,exist_ok=True)
        return result

    def test_two_versions_preserve_inode_and_candidate_reader_equality(self):
        aggregate_fs=MemoryFS();candidate_fs=MemoryFS()
        first={'candidate':'a','phase':'b1','status':'COMPLETE','metric':1}
        second={'candidate':'a','phase':'b1','status':'COMPLETE','metric':2}
        self.publish(candidate_fs,self.candidate,first,preserve.publish_dryrun_b1_manifest)
        old=self.publish(aggregate_fs,self.aggregate,{'label':'EXAM','manifests':[first]},preserve.publish_dryrun_b1_aggregate)
        first_bytes=aggregate_fs.contents[103]
        self.publish(candidate_fs,self.candidate,second,preserve.publish_dryrun_b1_manifest)
        new=self.publish(aggregate_fs,self.aggregate,{'label':'EXAM','manifests':[second]},preserve.publish_dryrun_b1_aggregate)
        self.assertEqual((aggregate_fs.files[aggregate_fs.names[-1]].st_dev,aggregate_fs.files[aggregate_fs.names[-1]].st_ino),old)
        self.assertEqual((aggregate_fs.current.st_dev,aggregate_fs.current.st_ino),new)
        self.assertEqual(json.loads(first_bytes)['manifests'],[first])
        self.assertEqual(json.loads(aggregate_fs.contents[103])['manifests'][0],json.loads(candidate_fs.contents[103]))
        expected=(json.dumps({'label':'EXAM','manifests':[second]},indent=2,allow_nan=False)+'\n').encode()
        self.assertEqual(aggregate_fs.contents[103],expected)
        self.assertEqual(hashlib.sha256(aggregate_fs.contents[103]).hexdigest(),hashlib.sha256(expected).hexdigest())

    def test_identity_race_and_unsupported_rename_keep_old(self):
        for race in (True,False):
            fs=MemoryFS();old=fs.info(0o100600,44);fs.current=old
            fs.change_before_rename=race;fs.fail_rename=not race
            with self.assertRaises((RuntimeError,OSError)):
                self.publish(fs,self.aggregate,{'label':'EXAM','manifests':[]},preserve.publish_dryrun_b1_aggregate)
            self.assertIs(fs.current,old);self.assertEqual(len(fs.files),1)

    def test_bad_name_or_relative_path_refuses_before_mkdir(self):
        with mock.patch.object(pathlib.Path,'mkdir') as mkdir:
            for target in ('relative/b1_manifests.json','/synthetic/b1_manifest.json','/synthetic/b2_manifests.json'):
                with self.assertRaises(RuntimeError):preserve.publish_dryrun_b1_aggregate(target,{})
        mkdir.assert_not_called()

    def test_actual_dispatch_changes_only_dryrun_b1(self):
        tree=ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        helper=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_write_aggregate_manifest'))
        legacy=mock.Mock(return_value='legacy');scope={'write_json':legacy}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[helper],type_ignores=[])),'<aggregate-manifest-dispatch>','exec'),scope)
        with mock.patch.object(preserve,'publish_dryrun_b1_aggregate',return_value='retained') as retained:
            self.assertEqual(scope['_write_aggregate_manifest'](self.aggregate,{'x':1},phase='b1',dryrun=True),'retained')
            self.assertEqual(scope['_write_aggregate_manifest'](self.aggregate,{'x':1},phase='b1',dryrun=False),'legacy')
            self.assertEqual(scope['_write_aggregate_manifest'](self.aggregate,{'x':1},phase='b2',dryrun=True),'legacy')
        retained.assert_called_once_with(self.aggregate,{'x':1});self.assertEqual(legacy.call_count,2)

    def test_actual_producer_and_batch_reader_contract(self):
        runner=ast.parse(pathlib.Path('r1/scripts/exam_runner.py').read_text())
        fn=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='_evidence_unreviewed')
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_write_aggregate_manifest']
        self.assertEqual(len(calls),1)
        self.assertEqual({k.arg for k in calls[0].keywords},{'phase','dryrun'})
        self.assertIn("f'{phase}_manifests.json'",ast.unparse(calls[0]))
        batch=ast.parse(pathlib.Path('r1/exam/b1_batch.py').read_text())
        verify=next(n for n in batch.body if isinstance(n,ast.FunctionDef) and n.name=='verify_batch')
        source=ast.unparse(verify)
        self.assertIn("_read(batch / 'b1_manifests.json')",source)
        self.assertIn('_read(candidate_path) != m',source)
        self.assertIn("'batch_manifests_sha256': digest_file(batch / 'b1_manifests.json')",source)
        self.assertIn("m.get('execution_label') != 'EVIDENCE'",source)
        receipt=pathlib.Path('r1/exam/b1_exit_receipt.py').read_text()
        finalization=pathlib.Path('r1/exam/b1_finalization.py').read_text()
        self.assertNotIn('b1_manifests.json',receipt)
        self.assertNotIn('b1_manifests.json',finalization)


if __name__=='__main__':unittest.main()
