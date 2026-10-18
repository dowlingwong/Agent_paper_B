import copy
import unittest
from causal_branch.control.tree import fixtures, summarize, validate_trees

class TreeTests(unittest.TestCase):
    def setUp(self): self.trees=fixtures();self.by={t['root']['root_id']:t for t in self.trees}
    def leaf(self,name,regime): return next(l for l in self.by[name]['leaves'] if l['regime']==regime)
    def test_early_and_late_optima(self):
        self.assertEqual(self.leaf('early_use_optimal','verify_now')['outcome'],1)
        self.assertEqual(self.leaf('save_for_later','verify_later')['outcome'],1)
        self.assertEqual(self.leaf('no_useful_later','verify_later')['outcome'],0)
    def test_fallbacks_and_budget(self):
        for name in ('early_termination','unreachable_checkpoint2','exhausted_budget','unavailable_later'):
            self.assertEqual(self.leaf(name,'verify_later')['action2'],'continue')
            self.assertEqual(self.leaf(name,'verify_later')['outcome'],0)
        self.assertEqual(self.leaf('save_for_later','verify_later')['budget_after1'],1)
        self.assertEqual(self.leaf('save_for_later','verify_later')['budget_final'],0)
        self.assertFalse(self.leaf('early_use_optimal','verify_now')['reached2'])
        self.assertTrue(self.leaf('early_use_optimal','never')['reached2'])
    def test_original_root_denominator(self):
        pair=[self.by['save_for_later'],self.by['unreachable_checkpoint2']]
        self.assertEqual(summarize(pair)['means']['verify_later'],.5)
        with self.assertRaisesRegex(ValueError,'original-root denominator'): summarize(pair,denominator=1)
    def test_leakage_plants(self):
        bad=copy.deepcopy(self.trees);bad[0]['leaves'][0]['split']='test'
        with self.assertRaisesRegex(ValueError,'descendant leakage'):validate_trees(bad)
        bad=copy.deepcopy(self.trees);bad[1]['root']['split']='test'
        for l in bad[1]['leaves']:l['split']='test'
        with self.assertRaisesRegex(ValueError,'family leakage'):validate_trees(bad)
    def test_budget_and_missing_leaf_plants(self):
        for field,value in [('budget_final',-1),('reached2',True)]:
            bad=copy.deepcopy(self.trees);bad[0]['leaves'][0][field]=value
            with self.assertRaisesRegex(ValueError,'invalid reachability'):validate_trees(bad)
        bad=copy.deepcopy(self.trees);bad[0]['leaves'].pop()
        with self.assertRaises(ValueError):validate_trees(bad)
    def test_repeated_one_step_greedy_fails(self):
        t=self.by['greedy_fails'];self.assertGreater(t['root']['immediate_gain'],0)
        # A positive immediate gain spends the only token at checkpoint 1;
        # even when re-evaluated at checkpoint 2, that greedy rule cannot verify.
        early=self.leaf('greedy_fails','verify_now');later=self.leaf('greedy_fails','verify_later')
        self.assertEqual(early['budget_final'],0)
        self.assertLess(early['outcome'],later['outcome'])
