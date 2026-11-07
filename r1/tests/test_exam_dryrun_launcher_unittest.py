"""Read-only mocked launcher checks; no temporary files or processes."""
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from r1.exam import runtime
from r1.scripts import exam_dryrun


class DryrunLauncherTests(unittest.TestCase):
    def patches(self, host='devbox', tmp='/tmp'):
        stack=ExitStack()
        stack.enter_context(mock.patch('platform.node',return_value=host))
        stack.enter_context(mock.patch.object(runtime.tempfile,'tempdir',None))
        stack.enter_context(mock.patch.object(runtime.tempfile,'gettempdir',side_effect=AssertionError('deleting probe forbidden')))
        stack.enter_context(mock.patch.dict(os.environ,{'TMPDIR':tmp},clear=True))
        stack.enter_context(mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p))
        stack.enter_context(mock.patch.object(Path,'is_dir',return_value=True))
        stack.enter_context(mock.patch.object(os,'access',return_value=True))
        return stack

    def test_prepare_and_run_refuse_exam_hosts_before_temp_selection(self):
        for host in ('TASL-7','tasl-2.example','ucrtasl'):
            for entry in (exam_dryrun.prepare,exam_dryrun.run):
                with self.subTest(host=host,entry=entry.__name__), \
                     mock.patch('platform.node',return_value=host), \
                     mock.patch.object(exam_dryrun,'_dryrun_temp_roots',side_effect=AssertionError('temp discovery forbidden')) as roots, \
                     mock.patch.object(Path,'mkdir') as mkdir, mock.patch.object(exam_dryrun.subprocess,'run') as execute:
                    with self.assertRaisesRegex(RuntimeError,'development host only'): entry('/tmp/b1-fixture')
                    roots.assert_not_called();mkdir.assert_not_called();execute.assert_not_called()

    def test_valid_development_temp_root_reaches_creation_without_temp_probe(self):
        class ReachedMkdir(Exception): pass
        for temp in ('/tmp','/private/var/folders/xy/example/T'):
            root=temp+'/fixture'
            with self.subTest(root=root), self.patches(tmp=temp), mock.patch.object(Path,'exists',return_value=False), \
                 mock.patch.object(Path,'mkdir',side_effect=ReachedMkdir) as mkdir:
                with self.assertRaises(ReachedMkdir): exam_dryrun.prepare(root)
                mkdir.assert_called_once()

    def test_fresh_root_writes_existing_dryrun_marker_before_other_work(self):
        class ReachedMarker(Exception): pass
        with self.patches(), mock.patch.object(Path,'exists',return_value=False), \
             mock.patch.object(Path,'mkdir') as mkdir, \
             mock.patch.object(Path,'write_text',autospec=True,side_effect=ReachedMarker) as write, \
             mock.patch.object(exam_dryrun.subprocess,'run') as execute:
            with self.assertRaises(ReachedMarker): exam_dryrun.prepare('/tmp/fixture')
            mkdir.assert_called_once()
            self.assertEqual(write.call_args.args[0],Path('/tmp/fixture/.dryrun'))
            self.assertIn('EXAM DRYRUN',write.call_args.args[1])
            execute.assert_not_called()

    def test_outside_temp_root_is_refused_before_creation(self):
        with self.patches(), mock.patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(RuntimeError,'temporary child directory'): exam_dryrun.prepare('/elsewhere/fixture')
            mkdir.assert_not_called()

    def test_nonempty_existing_root_is_preserved(self):
        with self.patches(), mock.patch.object(Path,'exists',return_value=True), \
             mock.patch.object(Path,'iterdir',return_value=iter([Path('/tmp/fixture/old')])), \
             mock.patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(RuntimeError,'preserve the earlier DRYRUN'): exam_dryrun.prepare('/tmp/fixture')
            mkdir.assert_not_called()


if __name__=='__main__': unittest.main()
