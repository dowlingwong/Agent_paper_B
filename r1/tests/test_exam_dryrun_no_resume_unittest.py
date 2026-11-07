"""Mocked legacy launcher ordering; no real files, processes or temporary roots."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from r1.scripts import exam_dryrun


class NoRepeatTests(unittest.TestCase):
    def invoke(self, interrupted):
        root=Path('/tmp/synthetic-exam')
        log=mock.MagicMock()
        statuses=[SimpleNamespace(returncode=0),SimpleNamespace(returncode=interrupted)]
        with mock.patch.object(exam_dryrun,'_require_development_host'), \
             mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p), \
             mock.patch.object(exam_dryrun,'prepare',return_value=root/'config.json'), \
             mock.patch.object(Path,'glob',return_value=iter(())), \
             mock.patch.object(Path,'open',return_value=log) as open_log, \
             mock.patch.object(Path,'read_text',autospec=True,return_value=json.dumps({})) as read_text, \
             mock.patch.object(exam_dryrun,'digest_file',return_value='synthetic-sha'), \
             mock.patch.object(exam_dryrun,'write_json') as write_json, \
             mock.patch.object(exam_dryrun.subprocess,'run',side_effect=statuses) as run:
            with self.assertRaisesRegex(RuntimeError,'automatic repeat is forbidden'):
                exam_dryrun.run(root)
        self.assertEqual(run.call_count,2)
        calls=run.call_args_list
        self.assertIn('stage-a',calls[0].args[0])
        self.assertIn('b1',calls[1].args[0]);self.assertIn('--interrupt-root',calls[1].args[0])
        write_json.assert_called_once()  # stage-A config binding, before B1 interruption
        read_text.assert_called_once_with(root/'config.json')  # no stopped batch read
        self.assertEqual(open_log.call_count,2)  # no new log after interrupted command

    def test_recorded_stop_never_starts_second_b1(self): self.invoke(1)

    def test_unexpected_success_does_not_authorize_second_b1(self): self.invoke(0)

    def test_interrupted_command_exception_never_starts_second_b1(self):
        root=Path('/tmp/synthetic-exam');log=mock.MagicMock()
        with mock.patch.object(exam_dryrun,'_require_development_host'), \
             mock.patch.object(Path,'resolve',autospec=True,side_effect=lambda p:p), \
             mock.patch.object(exam_dryrun,'prepare',return_value=root/'config.json'), \
             mock.patch.object(Path,'glob',return_value=iter(())), \
             mock.patch.object(Path,'open',return_value=log), \
             mock.patch.object(Path,'read_text',return_value='{}'), \
             mock.patch.object(exam_dryrun,'digest_file',return_value='synthetic-sha'), \
             mock.patch.object(exam_dryrun,'write_json'), \
             mock.patch.object(exam_dryrun.subprocess,'run',side_effect=[SimpleNamespace(returncode=0),TimeoutError('synthetic')]) as run:
            with self.assertRaises(TimeoutError): exam_dryrun.run(root)
        self.assertEqual(run.call_count,2)


if __name__=='__main__': unittest.main()
