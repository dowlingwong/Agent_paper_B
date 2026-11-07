import os
import sys

forbidden = {'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.chmod',
             'os.chown', 'os.link', 'os.symlink', 'os.truncate', 'os.utime',
             'os.system', 'os.posix_spawn', 'subprocess.Popen', 'socket.connect',
             'socket.bind', 'socket.getaddrinfo'}

def audit(event, args):
    if event in forbidden:
        raise PermissionError('test runner blocked operation: ' + event)
    if event == 'open' and len(args) >= 3 and isinstance(args[2], int):
        mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if args[2] & mask:
            raise PermissionError('test runner blocked writable open')

sys.addaudithook(audit)
sys.path.insert(0, os.getcwd())
import unittest
from r1.tests.stagea_recovery_memory.test_dryrun_state_preserve import DryrunStateTests
from r1.tests.stagea_recovery_memory.test_copied_checkpoint import CopiedCheckpointTest
from r1.tests.stagea_recovery_memory.test_dead_worker_checkpoint import DeadWorkerCheckpointTest
from r1.tests.test_b1_state_preserve_unittest import StatePreservationTests
loader = unittest.defaultTestLoader
suite = unittest.TestSuite(loader.loadTestsFromTestCase(c) for c in (DryrunStateTests, CopiedCheckpointTest))
suite.addTest(DeadWorkerCheckpointTest('test_dead_worker_record_checked_and_completed_root_still_skipped'))
excluded = {'test_post_exchange_failure_stop_save_failure_has_no_waited_receipt',
            'test_runtime_selects_preserving_writer_for_b1_and_dryrun'}
for name in loader.getTestCaseNames(StatePreservationTests):
    if name not in excluded:
        suite.addTest(StatePreservationTests(name))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print('PURE_TEST_RESULT tests_run=%d failures=%d errors=%d skipped=%d' %
      (result.testsRun, len(result.failures), len(result.errors), len(result.skipped)))
sys.exit(0 if result.wasSuccessful() else 1)
