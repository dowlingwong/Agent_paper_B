"""The synthetic close path must retain its runner lock, including on STOP."""
import unittest
from unittest.mock import Mock

from r1.exam.runtime import ExamRunner


class DryrunLockRetention(unittest.TestCase):
    def runner(self, phase):
        runner = ExamRunner.__new__(ExamRunner)
        runner.cfg = {'dryrun': True}
        runner.state = {'phase': phase}
        runner.stop_service = Mock()
        runner.lock = Mock()
        return runner

    def test_normal_close_never_deletes_lock(self):
        for phase in ('stage-a', 'b1'):
            with self.subTest(phase=phase):
                runner = self.runner(phase)
                lock = runner.lock
                runner.close()
                lock.unlink.assert_not_called()
                runner.stop_service.assert_called_once_with()
                self.assertIsNone(runner.lock)

    def test_stop_preservation_does_not_change_lock_or_service(self):
        runner = self.runner('b1')
        lock = runner.lock
        runner.close(preserve_running=True)
        self.assertIs(runner.lock, lock)
        lock.unlink.assert_not_called()
        runner.stop_service.assert_not_called()
