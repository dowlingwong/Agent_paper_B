import unittest
from r1.scripts.hk2.hk2_audit_shards import ShardError, merge_shards, select_shard


class AuditShardsTest(unittest.TestCase):
    def setUp(self):
        self.seeds = [7001, 7002]
        self.plan = [{'proposal_id': 'p'+str(i), 'node': 'digits',
                      'candidate_hash': 'c'+str(i), 'incumbent_hash': 'anchor'} for i in range(5)]
        self.shards = {i: [dict(p, seeds=self.seeds[:], candidate_metrics=[1.0, 2.0],
                                     incumbent_metrics=[0.5, 1.0])
                           for p in select_shard(self.plan, self.seeds, 3, i)] for i in range(3)}

    def test_partition_and_merge_original_order(self):
        self.assertEqual([x['proposal_id'] for x in merge_shards(self.plan, self.seeds, 3, self.shards)],
                         [x['proposal_id'] for x in self.plan])
        self.assertEqual(select_shard(self.plan, self.seeds, 7, 6), [])

    def test_missing_duplicate_wrong_shard_and_wrong_identity_stop(self):
        for bad in ({0: self.shards[0], 1: self.shards[1]},
                    {0: self.shards[0]+self.shards[0][:1], 1: self.shards[1], 2: self.shards[2]},
                    {0: self.shards[1], 1: self.shards[0], 2: self.shards[2]},
                    {0: [dict(self.shards[0][0], node='other')]+self.shards[0][1:], 1: self.shards[1], 2: self.shards[2]}):
            with self.subTest(bad=bad), self.assertRaises(ShardError): merge_shards(self.plan, self.seeds, 3, bad)
        bad = {i: list(rows) for i, rows in self.shards.items()}; bad[0].pop()
        with self.assertRaises(ShardError): merge_shards(self.plan, self.seeds, 3, bad)

    def test_wrong_seeds_and_invalid_measurement_stop(self):
        for change in ({'seeds': [7002, 7001]}, {'seeds': [7001, 7003]},
                       {'candidate_metrics': [float('nan'), 1]}, {'incumbent_metrics': [True, 1]},
                       {'candidate_metrics': [1]}):
            bad = {i: list(rows) for i, rows in self.shards.items()}; bad[0][0] = dict(bad[0][0], **change)
            with self.subTest(change=change), self.assertRaises(ShardError): merge_shards(self.plan, self.seeds, 3, bad)

    def test_invalid_plan_and_indices(self):
        for args in ((self.plan, [7001, 7001], 3, 0), (self.plan, self.seeds, 3, True),
                     (self.plan+[self.plan[0]], self.seeds, 3, 0), (self.plan, self.seeds, 0, 0)):
            with self.subTest(args=args), self.assertRaises(ShardError): select_shard(*args)
        with self.assertRaises(ShardError): merge_shards(self.plan, self.seeds, 3, {False: [], 1: [], 2: []})


if __name__ == '__main__': unittest.main()
