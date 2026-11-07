"""Pure mocked B1 DRYRUN entry checks; no host, process, or temporary files."""
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from r1.exam import campaign


class DryrunEntryTests(unittest.TestCase):
    def setUp(self):
        self.job={'phase':'b1','dryrun':True,'out':'/tmp/b1-fixture/root',
                  'authority_config':{'dryrun':True,'dryrun_root':'/tmp/b1-fixture'},
                  'node':'digits_mlp','seed':9001}

    def patches(self, host='devbox', marker=True):
        stack=ExitStack()
        stack.enter_context(mock.patch('platform.node',return_value=host))
        stack.enter_context(mock.patch('tempfile.gettempdir',return_value='/tmp'))
        stack.enter_context(mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p))
        stack.enter_context(mock.patch.object(Path,'is_file',return_value=marker))
        return stack

    def test_non_boolean_dryrun_refused_before_mkdir_or_copy(self):
        for value in (1,0,'false','true',None,[]):
            with self.subTest(value=value), mock.patch.object(Path,'mkdir') as mkdir, \
                 mock.patch.object(campaign.shutil,'copytree') as copy:
                with self.assertRaisesRegex(RuntimeError,'must be a boolean'):
                    campaign._collect_b1_review({**self.job,'dryrun':value})
                mkdir.assert_not_called();copy.assert_not_called()

    def test_exam_hosts_refused_before_mkdir_or_copy(self):
        for host in ('TASL-7','tasl-2.example','ucrtasl'):
            with self.subTest(host=host), self.patches(host), mock.patch.object(Path,'mkdir') as mkdir, \
                 mock.patch.object(campaign.shutil,'copytree') as copy:
                with self.assertRaisesRegex(RuntimeError,'development host'):
                    campaign._collect_b1_review(self.job)
                mkdir.assert_not_called();copy.assert_not_called()

    def test_missing_marker_and_escape_refused_before_mkdir_or_copy(self):
        for job,marker in ((self.job,False),({**self.job,'out':'/tmp/elsewhere/out'},True),
                           ({**self.job,'authority_config':{'dryrun':'true','dryrun_root':'/tmp/b1-fixture'}},True)):
            with self.subTest(job=job,marker=marker), self.patches(marker=marker), \
                 mock.patch.object(Path,'mkdir') as mkdir, mock.patch.object(campaign.shutil,'copytree') as copy:
                with self.assertRaises(RuntimeError): campaign._collect_b1_review(job)
                mkdir.assert_not_called();copy.assert_not_called()

    def test_marked_development_host_reaches_original_copy_path(self):
        class ReachedCopy(Exception): pass
        with self.patches(), mock.patch.object(Path,'mkdir') as mkdir, \
             mock.patch.object(campaign,'load_registered_node',return_value=object()), \
             mock.patch.object(campaign.shutil,'copytree',side_effect=ReachedCopy) as copy:
            with self.assertRaises(ReachedCopy): campaign._collect_b1_review(self.job)
            mkdir.assert_called_once();copy.assert_called_once()

    def test_production_false_still_requires_worker_contract(self):
        job={**self.job,'dryrun':False}
        with mock.patch.dict(os.environ,{},clear=True), mock.patch.object(Path,'mkdir') as mkdir, \
             mock.patch.object(campaign.shutil,'copytree') as copy:
            with self.assertRaisesRegex(RuntimeError,'worker contract'): campaign._collect_b1_review(job)
            mkdir.assert_not_called();copy.assert_not_called()


if __name__ == '__main__': unittest.main()
