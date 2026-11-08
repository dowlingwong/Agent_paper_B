import json
import subprocess
import sys
import unittest

from r1.scripts.hk2.hk2_synthetic_cli import LABEL, evaluate


class SyntheticCliTest(unittest.TestCase):
    def setUp(self):
        self.plan = [dict(proposal_id='p'+str(i), node='digits', candidate_hash='c'+str(i),
                          incumbent_hash='base') for i in range(3)]
        self.base = dict(label=LABEL, plan=self.plan, seeds=[7001, 7002], count=2)

    def test_end_to_end_select_merge_and_identity_binding(self):
        shards = []
        for index in range(2):
            result = evaluate('select', dict(self.base, index=index))
            self.assertFalse(result['execution_authorized'])
            output = result['result']
            rows = [dict(p, seeds=[7001, 7002], candidate_metrics=[1., 2.],
                         incumbent_metrics=[0., 1.]) for p in output['pairs']]
            shards.append(dict(index=index, plan_sha256=output['plan_sha256'], rows=rows))
        merged = evaluate('merge', dict(self.base, shards=shards))['result']
        self.assertEqual([x['proposal_id'] for x in merged['rows']], ['p0', 'p1', 'p2'])
        bad = [dict(x) for x in shards]; bad[0]['plan_sha256'] = 'other'
        with self.assertRaises(ValueError): evaluate('merge', dict(self.base, shards=bad))
        with self.assertRaises(ValueError): evaluate('merge', dict(self.base, shards=shards[:1]))
        with self.assertRaises(ValueError): evaluate('merge', dict(self.base, shards=shards + shards[:1]))
        bad = [dict(x) for x in shards]; bad[0]['rows'] = [dict(bad[0]['rows'][0], seeds=[7002, 7001])]
        with self.assertRaises(ValueError): evaluate('merge', dict(self.base, shards=bad))

    def test_cut_twice_and_labels(self):
        obj = dict(label=LABEL, unit_id='a', attempts=[dict(unit_id='a', attempt=i, outcome='interrupted')
                                                       for i in (1, 2)])
        self.assertEqual(evaluate('history', obj)['result']['state'], 'STOP_CUT_TWICE')
        with self.assertRaises(ValueError): evaluate('history', dict(obj, label='EVIDENCE'))

    def test_real_cli_stdin_json_and_duplicate_key_stop(self):
        cmd = [sys.executable, '-m', 'r1.scripts.hk2.hk2_synthetic_cli', 'history']
        raw = json.dumps(dict(label=LABEL, unit_id='a', attempts=[])).encode()
        result = subprocess.run(cmd, input=raw, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)['execution_authorized'])
        cut = json.dumps(dict(label=LABEL, unit_id='a', attempts=[dict(unit_id='a', attempt=i, outcome='interrupted') for i in (1, 2)])).encode()
        stopped = subprocess.run(cmd, input=cut, capture_output=True, check=False)
        self.assertEqual(stopped.returncode, 2)
        self.assertEqual(json.loads(stopped.stdout)['result']['state'], 'STOP_CUT_TWICE')
        duplicate = b'{"label":"SYNTHETIC_ONLY","unit_id":"a","unit_id":"b","attempts":[]}'
        result = subprocess.run(cmd, input=duplicate, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')


if __name__ == '__main__': unittest.main()
