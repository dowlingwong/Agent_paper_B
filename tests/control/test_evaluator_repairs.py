"""Counterexamples for denominator, pairing, missingness, leakage and alignment."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiment_scaffold/src'))
from causal_branch.control.evaluate import evaluate_policies, checkpoint_rows, cluster_draw_indices
from causal_branch.control.schema import assert_split_disjoint, BranchRecordError, validate_record
from causal_branch.control.learners import matching_report
from causal_branch.control.allocation import ConservativeSelector
from test_b_contract import _record
spec=importlib.util.spec_from_file_location('smoke_driver',ROOT/'experiments/paper_b/smoke_b.py')
smoke=importlib.util.module_from_spec(spec);spec.loader.exec_module(smoke)


def world(pairs, costs=None):
    records=[]
    for i,(base,verify) in enumerate(pairs):
        for action,val in [('g0',base),('gv',verify)]:
            records.append(_record(template_id=f't{i}',template_family_id=f't{i}',
                root_id=f'r{i}',checkpoint_id=f'c{i}',split='test',
                pre_treatment_features={'z':float(i)},pre_treatment_mask={'g0':True,'gv':verify is not None},
                action_id=action,execution_status='unavailable' if val is None else 'completed',
                outcome_success=None if val is None else int(val>=.5),outcome_utility=val,
                cost_vector={} if val is None else {'time':1. if action=='g0' else (costs[i] if costs else 2.)}))
    return records


def scores(records, left=None, right=None):
    keys=sorted({(r.root_id,r.checkpoint_id) for r in records})
    n=len(keys)
    return {'left':dict(zip(keys,left if left is not None else range(n))),
            'right':dict(zip(keys,right if right is not None else range(n)))}


def evaluate(records, score=None, **kwargs):
    return evaluate_policies(records,scores_by_policy=score or scores(records),
                             primary_policy=kwargs.pop('primary_policy','left'),
                             primary_comparator=kwargs.pop('primary_comparator','right'),
                             outcome='U',n_bootstrap=50,**kwargs)[0]


class PairedBootstrapRepairs(unittest.TestCase):
    def test_duplicate_draws_preserve_multiplicity_and_reallocate(self):
        np.testing.assert_array_equal(cluster_draw_indices(np.array([0,0,1,2]),np.array([0,0,1])),[0,1,0,1,2])
        records=world([(0.,1.),(1.,0.),(.2,.4)])
        class FixedDraw:
            def choice(self,*args,**kwargs):return np.array([0,0,1])
        with patch('causal_branch.control.evaluate.np.random.default_rng',return_value=FixedDraw()):
            r=evaluate(records,scores(records,[3,2,1],[3,2,1]),capacities=(.5,))
        # Each resample selects TWO occurrences of template zero: 2/3, not 1/2.
        self.assertAlmostEqual(r.evaluations['left'].gain_ci[0],2/3)
        self.assertAlmostEqual(r.evaluations['left'].gain_ci[1],2/3)
        self.assertEqual(r.d_ci,(0.,0.))

    def test_identical_policy_paired_interval_has_zero_width(self):
        r=evaluate(world([(0.,1.),(1.,0.),(.1,.8),(.9,.2)]),capacities=(.5,))
        self.assertEqual(r.d_value,0.)
        self.assertEqual(r.d_ci,(0.,0.))

    def test_role_swap_flips_point_and_interval_sign(self):
        records=world([(0.,1.),(1.,0.),(.2,.8),(.8,.2)])
        s=scores(records,[4,1,3,2],[1,4,2,3])
        a=evaluate(records,s,capacities=(.5,));b=evaluate(records,s,capacities=(.5,),primary_policy='right',primary_comparator='left')
        self.assertAlmostEqual(a.d_value,-b.d_value)
        np.testing.assert_allclose(a.d_ci,[-b.d_ci[1],-b.d_ci[0]])

    def test_all_feasible_denominator_is_not_selected_only(self):
        records=world([(0.,1.),(0.,1.),(0.,1.),(0.,None)])
        r=evaluate(records,scores(records,[4,3,2,1]),capacities=(.25,)).evaluations['left']
        self.assertAlmostEqual(r.gain_feasible,1/3)
        self.assertEqual(r.gain_selected_only,1.)
        self.assertEqual(r.gain_full_population,.25)
        self.assertEqual((r.n_feasible_checkpoints,r.n_selected),(3,1))

    def test_comparator_is_explicit_not_inferred(self):
        records=world([(0.,1.),(1.,0.)])
        with self.assertRaisesRegex(ValueError,'explicit primary'):
            evaluate(records,primary_comparator='risk')

    def test_missing_channel_is_not_zero_or_unavailability(self):
        records=world([(0.,1.),(1.,None)])
        with self.assertRaisesRegex(ValueError,'missing requested outcome U'):
            checkpoint_rows([replace(r,outcome_utility=None) if r.root_id=='r0' and r.action_id=='gv' else r for r in records],('U',))
        with self.assertRaisesRegex(ValueError,'missing feasible gv'):
            checkpoint_rows([r for r in records if not (r.root_id=='r0' and r.action_id=='gv')],('U',))
        # A missing unavailable branch is allowed only because the baseline mask says so.
        self.assertEqual(len(checkpoint_rows([r for r in records if not (r.root_id=='r1' and r.action_id=='gv')],('U',))),2)
        with self.assertRaisesRegex(ValueError,'unknown requested'):
            checkpoint_rows(records,('typo',))

    def test_unavailable_utility_only_outcome_is_rejected(self):
        r=world([(0.,None)])[1]
        with self.assertRaises(BranchRecordError):validate_record(replace(r,outcome_utility=.3))

    def test_context_and_repetition_alignment(self):
        r=world([(0.,1.)])
        with self.assertRaisesRegex(ValueError,'inconsistent checkpoint'):
            checkpoint_rows([r[0],replace(r[1],pre_treatment_features={'z':99.})])
        with self.assertRaisesRegex(ValueError,'unmatched repetitions'):
            checkpoint_rows([r[0],replace(r[1],repetition_id=1)])

    def test_mixed_costs_reported_but_do_not_leak_into_allocation(self):
        r=world([(0.,1.),(0.,1.)],costs=[2.,20.]);s=scores(r,[2,1],[1,2])
        a=evaluate(r,s,capacities=(.5,))
        self.assertEqual(a.evaluations['left'].selected_incremental_cost,{'time':1.})
        self.assertEqual(a.evaluations['right'].selected_incremental_cost,{'time':19.})
        changed=[replace(x,cost_vector={'time':999.}) if x.action_id=='gv' else x for x in r]
        b=evaluate(changed,s,capacities=(.5,))
        self.assertEqual(a.d_value,b.d_value)
        self.assertEqual(a.d_ci,b.d_ci)


class TrainingAndWorldRepairs(unittest.TestCase):
    def test_calibration_test_and_sibling_variant_leakage(self):
        r=world([(0.,1.)])[0]
        for clone in [replace(r,split='calibration'),
                      replace(r,split='calibration',template_id='variant',root_id='newroot',checkpoint_id='newckpt')]:
            with self.subTest(clone=clone.template_id),self.assertRaisesRegex(BranchRecordError,'split leakage'):
                assert_split_disjoint([r,clone])

    def test_action_labels_stay_with_features_when_unavailable(self):
        rows=smoke._checkpoint_rows(world([(.25,None),(.75,1.)]))
        features,actions,labels=smoke.action_training_rows(rows)
        self.assertEqual([f['z'] for f in features],[0.,1.,1.])
        self.assertEqual(actions,['g0','g0','gv'])
        self.assertEqual(labels,[0.,1.,1.])

    def test_fractional_training_means_and_matching_are_substantive(self):
        rows=[dict(features={'z':z},mask={'g0':True,'gv':True},g0_success=p,
                   gv_success=p+.1,g0_utility=p) for z,p in [(0.,.25),(1.,.75)]]
        learners=smoke.fit_all(rows);risk=learners[0]
        x=np.array([[0.,1.],[1.,1.]])
        expected=np.linalg.solve(x.T@x+.01*np.eye(2),x.T@np.array([.25,.75]))
        np.testing.assert_allclose(risk.model.w,expected)
        self.assertTrue(matching_report(learners)['matched_decision_class'])
        learners[2].model.l2=.5
        self.assertFalse(matching_report(learners)['matched_decision_class'])
        learners[2].model.l2=.01;learners[2].features=['future_outcome']
        self.assertFalse(matching_report(learners)['matched_decision_class'])
        learners[2].features=['z'];learners[2].model.w=np.zeros(3)
        self.assertFalse(matching_report(learners)['matched_decision_class'])

    def test_risk_sufficient_insufficient_null_and_negative_worlds(self):
        # Fixed context scores specify policies; labels never select their order.
        sufficient=world([(0.,1.),(1.,1.)])
        r=evaluate(sufficient,scores(sufficient,[2,1],[2,1]),capacities=(.5,))
        self.assertEqual(r.d_value,0.)
        insufficient=world([(0.,0.),(.5,1.)])
        r=evaluate(insufficient,scores(insufficient,[1,2],[2,1]),capacities=(.5,))
        self.assertEqual(r.d_value,.25)
        for pairs in [[(.5,.5),(.2,.2)],[(1.,0.),(1.,0.)]]:
            r=evaluate(world(pairs),capacities=(.5,))
            self.assertLessEqual(r.evaluations['left'].gain_feasible,0.)
            result=ConservativeSelector().select({'p':np.full(100,r.evaluations['left'].gain_feasible)})
            self.assertTrue(result.fallback)
