"""Pure mock check that a preservation import error cannot become an invalid trial."""
import builtins
import types
import unittest
from unittest import mock

from r1.tests.stagea_recovery_memory.test_dryrun_fixture_edit import FixtureWorkerDispatchTests


class FixtureImportFailureTests(unittest.TestCase):
    def test_preservation_import_failure_escapes_harness_exception_handler(self):
        FixtureWorkerDispatchTests.setUpClass()
        worker=FixtureWorkerDispatchTests.worker_class('/synthetic/node',9001)
        stop=FixtureWorkerDispatchTests.stop_class
        proposal=types.SimpleNamespace(extra={'structured_edit':{'path':'a.py','text':'new'}})
        spec=types.SimpleNamespace(editable_paths=('a.py',),metric_name='value')
        real_import=builtins.__import__
        def reject(name,*args,**kwargs):
            if name=='r1.exam.b1_state_preserve':raise ImportError('synthetic import failure')
            return real_import(name,*args,**kwargs)
        with mock.patch.object(builtins,'__import__',side_effect=reject):
            with self.assertRaises(stop):worker.run_trial(proposal,spec,1)
        self.assertTrue(issubclass(stop,SystemExit))
        self.assertFalse(issubclass(stop,Exception))


if __name__=='__main__':unittest.main()
