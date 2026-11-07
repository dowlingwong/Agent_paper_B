import os
import sys

forbidden = {'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.chmod',
             'os.chown', 'os.link', 'os.symlink', 'os.truncate', 'os.utime',
             'os.system', 'os.posix_spawn', 'os.fork', 'subprocess.Popen',
             'socket.connect', 'socket.bind', 'socket.getaddrinfo'}
def audit(event, args):
    if event in forbidden:
        raise PermissionError('test runner blocked operation: ' + event)
    if event == 'open' and len(args) >= 3 and isinstance(args[2], int):
        mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if args[2] & mask:
            raise PermissionError('test runner blocked writable open')
sys.addaudithook(audit)
sys.path.insert(0, os.getcwd())
import importlib.util
import unittest
from pathlib import Path

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

root = Path(os.getcwd())
notification = load('test_notify_pure', root / 'r1/tests/b1_audit_stop_memory/test_notifying_audit.py')
executor = load('test_executor_pure', root / 'r1/tests/b1_audit_stop_memory/test_audit_executor_order.py')
from r1.tests import test_b1_worker_contract_unittest as worker
suite = unittest.TestSuite()
for cls in (notification.Tests, executor.Tests, worker.ListenerTests, worker.ParentSpawnTests, worker.ParentIdentityTests):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
for name in unittest.defaultTestLoader.getTestCaseNames(worker.ContractTests):
    if name != 'test_direct_entry_without_contract_refuses_before_output':
        suite.addTest(worker.ContractTests(name))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print('PURE_TEST_RESULT tests_run=%d failures=%d errors=%d skipped=%d' %
      (result.testsRun, len(result.failures), len(result.errors), len(result.skipped)))
sys.exit(0 if result.wasSuccessful() else 1)
