"""Pure mocks of synthetic FixtureWorker editable preservation."""
import ast
import copy
import errno
import os
import pathlib
import types
import unittest
from unittest import mock

from r1.exam import b1_state_preserve as preserve
from r1.tests.test_b1_state_preserve_unittest import MemoryFS


class FixtureEditPublisherTests(unittest.TestCase):
    root = pathlib.Path('/synthetic/node')
    path = root / 'config.yaml'

    def test_changed_text_keeps_prior_inode_and_plain_text_bytes(self):
        fs=MemoryFS();old=fs.info(0o100600,44);fs.current=old
        with fs.patches(), mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path), \
             mock.patch.object(preserve,'_renameat_dryrun',side_effect=fs.rename):
            new=preserve.publish_dryrun_fixture_text(self.root,'config.yaml','C: 2.0\n',(7,44))
        self.assertEqual((fs.files[fs.names[-1]].st_dev,fs.files[fs.names[-1]].st_ino),(7,44))
        self.assertEqual((fs.current.st_dev,fs.current.st_ino),new)
        self.assertEqual(fs.contents[103],b'C: 2.0\n')

    def test_identity_change_or_unsupported_rename_keeps_old(self):
        for race in (True,False):
            fs=MemoryFS();old=fs.info(0o100600,44);fs.current=old
            fs.change_before_rename=race;fs.fail_rename=not race
            with fs.patches(),mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path), \
                 mock.patch.object(preserve,'_renameat_dryrun',side_effect=fs.rename):
                with self.assertRaises((RuntimeError,OSError)):
                    preserve.publish_dryrun_fixture_text(self.root,'config.yaml','changed',(7,44))
            self.assertIs(fs.current,old);self.assertEqual(len(fs.files),1)

    def test_invalid_or_alias_paths_refuse_before_write(self):
        with mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path), \
             mock.patch.object(preserve.os,'open') as opened:
            for rel in ('','../escape','/absolute','sub/../escape','sub//file','_to_delete/x','bad\\name'):
                with self.assertRaises(RuntimeError):
                    preserve.publish_dryrun_fixture_text(self.root,rel,'changed',(7,44))
        opened.assert_not_called()

    def test_read_checks_identity_and_does_not_create(self):
        with mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path), \
             mock.patch.object(pathlib.Path,'read_text',return_value='C: 1\n'), \
             mock.patch.object(preserve,'existing_identity',side_effect=[(7,1),(7,1)]):
            text,identity=preserve.read_dryrun_fixture_text(self.root,'config.yaml')
        self.assertEqual((text,identity),('C: 1\n',(7,1)))
        with mock.patch.object(pathlib.Path,'resolve',lambda path,strict=False:path), \
             mock.patch.object(pathlib.Path,'read_text',return_value='C: 1\n'), \
             mock.patch.object(preserve,'existing_identity',side_effect=[(7,1),(7,2)]):
            with self.assertRaises(RuntimeError):preserve.read_dryrun_fixture_text(self.root,'config.yaml')


class FixtureWorkerDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse(pathlib.Path('r1/exam/campaign.py').read_text())
        names=('DryrunFixturePreservationStop','FixtureWorker')
        classes=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names]
        scope={'Path':pathlib.Path,'time':types.SimpleNamespace(sleep=lambda _:None),
               'WorkerResult':mock.Mock(return_value='worker-result'),
               'fixture_metric':lambda files,seed:(tuple(sorted(files.items())),seed),
               'apply_edit':lambda files,edit:{**files,edit['path']:edit['text']}}
        exec(compile(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])),'<fixture-worker>','exec'),scope)
        cls.worker_class=scope['FixtureWorker'];cls.stop_class=scope['DryrunFixturePreservationStop'];cls.scope=scope

    def setUp(self):self.scope['WorkerResult'].reset_mock()

    def test_worker_updates_only_changed_path_and_preserves_metrics(self):
        worker=self.worker_class('/synthetic/node',9001)
        spec=types.SimpleNamespace(editable_paths=('a.py','b.py'),metric_name='value')
        proposal=types.SimpleNamespace(extra={'structured_edit':{'path':'a.py','text':'new'}})
        contents={'a.py':('old',(7,1)),'b.py':('same',(7,2))}
        with mock.patch.object(preserve,'read_dryrun_fixture_text',side_effect=lambda root,p:contents[p]), \
             mock.patch.object(preserve,'publish_dryrun_fixture_text') as write:
            self.assertEqual(worker.run_trial(proposal,spec,1),'worker-result')
        write.assert_called_once_with(worker.node_root,'a.py','new',(7,1))
        args=self.scope['WorkerResult'].call_args.args
        self.assertEqual(args[3],{'value':((('a.py','new'),('b.py','same')),9001)})

    def test_read_and_publish_failures_escape_harness_exception_handler(self):
        worker=self.worker_class('/synthetic/node',9001)
        spec=types.SimpleNamespace(editable_paths=('a.py',),metric_name='value')
        proposal=types.SimpleNamespace(extra={'structured_edit':{'path':'a.py','text':'new'}})
        self.assertTrue(issubclass(self.stop_class,SystemExit));self.assertFalse(issubclass(self.stop_class,Exception))
        with mock.patch.object(preserve,'read_dryrun_fixture_text',side_effect=OSError(errno.EIO,'read failed')):
            with self.assertRaises(self.stop_class):worker.run_trial(proposal,spec,1)
        with mock.patch.object(preserve,'read_dryrun_fixture_text',return_value=('old',(7,1))), \
             mock.patch.object(preserve,'publish_dryrun_fixture_text',side_effect=OSError(errno.EIO,'write failed')):
            with self.assertRaises(self.stop_class):worker.run_trial(proposal,spec,1)
        self.scope['WorkerResult'].assert_not_called()

    def test_changed_editable_set_stops_before_publication(self):
        worker=self.worker_class('/synthetic/node',9001)
        spec=types.SimpleNamespace(editable_paths=('a.py',),metric_name='value')
        proposal=types.SimpleNamespace(extra={'structured_edit':{'path':'other.py','text':'new'}})
        with mock.patch.object(preserve,'read_dryrun_fixture_text',return_value=('old',(7,1))), \
             mock.patch.object(preserve,'publish_dryrun_fixture_text') as write:
            with self.assertRaises(self.stop_class):worker.run_trial(proposal,spec,1)
        write.assert_not_called();self.scope['WorkerResult'].assert_not_called()


if __name__=='__main__':unittest.main()
