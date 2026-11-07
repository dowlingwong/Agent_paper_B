"""A synthetic copied, unrecorded interruption under fully mocked process state."""
import json
import unittest
from r1.tests.stagea_recovery_memory.test_copied_checkpoint import CopiedCheckpointTest


class DeadWorkerCheckpointTest(unittest.TestCase):
    def test_dead_worker_record_checked_and_completed_root_still_skipped(self):
        fixture = CopiedCheckpointTest(methodName='test_copied_unrecorded_checkpoint_loads_and_skips_completed_root')
        fixture.setUp()
        fixture.state['in_progress'] = {'path':'/old/b1/partial', 'pid':77}
        fixture.fs.files['/copy/b1/batch_state.json'] = json.dumps(fixture.state)
        calls = []
        def dead(pid, signal):
            calls.append((pid, signal))
            raise ProcessLookupError('synthetic process absent')
        fixture.runner.start.__globals__['os'].kill = dead
        fixture.runner.start('b1')
        self.assertEqual(calls, [(77, 0)])
        self.assertEqual(fixture.runner.state['in_progress']['path'], '/old/b1/partial')
        self.assertEqual(fixture.runner.root({'id':'random_valid'}, 'b1', 'digits_mlp', 9001, 'off'),
                         {'label':'DRYRUN', 'synthetic':True})
        fixture.old_unchanged()


if __name__ == '__main__':
    unittest.main()
