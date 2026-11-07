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
from r1.tests import test_b1_publication_uncertainty_unittest as publication
from r1.tests import test_b1_operator_exit_unittest as operator
classes = (publication.UncertaintyTests, publication.PublicationLockTests,
           publication.FullBatchEntryTests, publication.SupervisorBindingTests,
           operator.OperatorExitTests)
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in classes)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print('PURE_TEST_RESULT tests_run=%d failures=%d errors=%d skipped=%d' %
      (result.testsRun, len(result.failures), len(result.errors), len(result.skipped)))
sys.exit(0 if result.wasSuccessful() else 1)
