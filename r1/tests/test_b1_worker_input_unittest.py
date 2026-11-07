"""In-memory B1 worker authority checks; no files or child processes."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from r1.exam import campaign, runtime


class WorkerInputTest(unittest.TestCase):
    def setUp(self):
        self.head='a'*40
        self.cfg={'dryrun':False,'rule_sha256':'b'*64,'workers':20,'W':20,
                  'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
                  'value_grids':'r1/exam/value_grids.yaml','host':'TASL-7',
                  'nodes':['digits_mlp'],'instance_seeds':[9001],
                  'proposal_schema':'manager_proposal/v1'}
        self.job={'phase':'b1','dryrun':False,'authority_config':copy.deepcopy(self.cfg),
                  'authorization_checkout_head':self.head,'workers':20,'W':20,
                  'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
                  'value_grids':self.cfg['value_grids'],'host':'TASL-7',
                  'node':'digits_mlp','seed':9001,'mode':'off',
                  'proposal_schema':'manager_proposal/v1','out':'/fake-b1-root'}

    def verify(self,job=None,*,config_head=None,author_head=None):
        with patch.object(runtime,'require_committed_b1_config',return_value=config_head or self.head) as config, \
             patch.object(runtime,'require_committed_b1_registry') as registry, \
             patch.object(runtime,'author_gate',return_value=author_head or self.head) as author:
            result=campaign._verify_b1_worker_input(job or self.job)
            config.assert_called_once_with(runtime.REPO/runtime.B1_CONFIG_REL,(job or self.job)['authority_config'])
            registry.assert_called_once_with((job or self.job)['authority_config'],self.head)
            author.assert_called_once()
            return result

    def test_matching_job(self):
        self.assertEqual(self.verify(),self.head)

    def test_config_head_mismatch(self):
        with self.assertRaisesRegex(RuntimeError,'configuration HEAD'): self.verify(config_head='c'*40)

    def test_author_head_mismatch(self):
        with self.assertRaisesRegex(RuntimeError,'author HEAD'): self.verify(author_head='c'*40)

    def test_derived_fields_refuse_mismatch(self):
        for key,value in [('workers',19),('W',21),('llm_call_cap',81),
                          ('audit_seeds',[9101]),('value_grids','/other/grid.yaml'),
                          ('host','different'),('node','other'),('seed',999),
                          ('mode','other'),('proposal_schema','other')]:
            job=copy.deepcopy(self.job);job[key]=value
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError,'STOP:'):
                self.verify(job)

    def test_input_check_precedes_output_and_worker(self):
        with patch.object(campaign,'require_worker_host'), \
             patch.object(campaign,'_verify_b1_worker_input',side_effect=RuntimeError('STOP: test')), \
             patch.object(Path,'mkdir') as mkdir, \
             patch.object(campaign,'B1IntegrityWorker') as worker:
            with self.assertRaisesRegex(RuntimeError,'STOP:'):
                campaign._collect_b1_review(self.job)
            mkdir.assert_not_called();worker.assert_not_called()

    def test_committed_config_refusal_precedes_other_authority(self):
        with patch.object(runtime,'require_committed_b1_config',side_effect=runtime.PreparationStop('STOP: bad config')), \
             patch.object(runtime,'require_committed_b1_registry') as registry, \
             patch.object(runtime,'author_gate') as author:
            with self.assertRaises(runtime.PreparationStop): campaign._verify_b1_worker_input(self.job)
            registry.assert_not_called();author.assert_not_called()


if __name__=='__main__': unittest.main()
