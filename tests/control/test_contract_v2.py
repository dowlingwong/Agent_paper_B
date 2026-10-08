"""Synthetic bound artifacts for phase validation, never real authorization."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('validator_v2',ROOT/'protocols/paper_b/launch_validator.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class PhaseContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'fixture.py').write_text('# Closed test stub')
        self.c=v.load_contract()
        for lane in v.LANES:
            self.c['lanes'][lane].update(engineering_fixture='fixture.py',engineering_fixture_sha256=hashlib.sha256((self.root/'fixture.py').read_bytes()).hexdigest())

    def artifact(self,name,data):
        path=self.root/name;path.write_text(json.dumps(data,sort_keys=True))
        return {'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

    def qualified_fixture(self,lane='one_step'):
        c=copy.deepcopy(self.c);c['status']='frozen';c['freeze_commit']='a'*40
        c['population'].update(task_law='closed temporary fixture',checkpoint_rule='one fixture checkpoint',condition_mixture={'fixture':1.})
        c['runtime'].update(model_revision='synthetic stub, no model',model_artifact_hash='b'*64,
                            harness_commit='a'*40,task_generator_hash='c'*64,evaluator_revision='stub-v1',
                            tool_versions={'stub':'1'},continuation_revision='stub-v1',verifier_revision='stub-v1',response_rule='identity')
        c['outcomes'].update(primary='U',utility_definition={'range':[0.,1.],'direction':'larger is better'})
        c['resources'].update(runtime_ceiling=1,storage_ceiling=1024,monetary_ceiling=0)
        c['replay_allowance'].update(p=None,R=2,provenance=self.artifact('plan.json',{'kind':'measurement_plan','method':'synthetic fixture only; measure p during qualification'}))
        families=['fixture-0','fixture-1']
        c['statistics']['split_manifest']=self.artifact('splits.json',{'protocol_version':'b_v2','lane':lane,'partitions':{'qualification':families,'test':[]}})
        pool=self.artifact('pool.json',{'protocol_version':'b_v2','lane':lane,'split':'qualification','template_families':families})
        c['qualification'][lane].update(pool=pool,checks=['state','mask','outcome'],units=2)
        self.bind(c,lane)
        return c

    def bind(self,c,lane):
        for phase,field in [('engineering','engineering_report'),('qualification','authorization')]:
            data={'protocol_version':'b_v2','lane':lane,'phase':phase,
                  'design_sha256':v.binding_digest(c,phase,lane),'banner':'ENGINEERING_ONLY',
                  'passed':True,'authorized':True,'authorized_by':'UNIT TEST FIXTURE ONLY'}
            c['qualification'][lane][field]=self.artifact(field+'.json',data)

    def test_budget_caps_are_enforced(self):
        caps=self.c['resources']['budget_caps']
        usage={name:caps[name] for name in v.BUDGET_CAP_FIELDS}
        self.assertEqual(v.budget_cap_errors(self.c,usage),[])
        over=dict(usage);over['max_terminal_leaves']=caps['max_terminal_leaves']+1
        self.assertTrue(any('budget cap exceeded' in e for e in v.budget_cap_errors(self.c,over)))
        missing=dict(usage);missing['max_generated_tokens_all_calls']=None
        self.assertTrue(any('missing usage' in e for e in v.budget_cap_errors(self.c,missing)))
        without=copy.deepcopy(self.c);del without['resources']['budget_caps']
        self.assertEqual(v.budget_cap_errors(without,usage),['budget_caps missing'])

    def test_engineering_passes_without_future_live_bindings(self):
        self.assertEqual(v.validate_for_phase(self.c,'engineering','one_step',base_dir=self.root),[])
        self.c['engineering']['model_calls']=True
        self.assertTrue(v.validate_for_phase(self.c,'engineering','one_step',base_dir=self.root))

    def test_qualification_is_not_circular(self):
        c=self.qualified_fixture()
        self.assertIsNone(c['qualification_report'])
        self.assertIsNone(c['statistics']['independent_unit_count'])
        self.assertIsNone(c['replay_allowance']['p'])
        self.assertEqual(v.validate_for_phase(c,'qualification','one_step',base_dir=self.root),[])

    def test_missing_provenance_and_missing_runtime_refused(self):
        for kind in ('provenance','runtime','authorization'):
            c=self.qualified_fixture()
            if kind=='provenance':c['replay_allowance']['provenance']=None
            if kind=='runtime':c['runtime']['model_revision']=None
            if kind=='authorization':c['qualification']['one_step']['authorization']=None
            with self.subTest(kind=kind):self.assertTrue(v.validate_for_phase(c,'qualification','one_step',base_dir=self.root))

    def test_stale_artifact_and_stale_design_refused(self):
        c=self.qualified_fixture();(self.root/'engineering_report.json').write_text('{}')
        self.assertTrue(any('stale artifact' in e for e in v.validate_for_phase(c,'qualification','one_step',base_dir=self.root)))
        c=self.qualified_fixture();c['runtime']['response_rule']='changed'
        self.assertTrue(any('stale design' in e for e in v.validate_for_phase(c,'qualification','one_step',base_dir=self.root)))

    def test_cross_lane_and_cross_phase_refused(self):
        for field,value,reason in [('lane','sequential','cross-lane'),('phase','qualification','cross-phase'),('protocol_version','b_v1','unknown-version')]:
            c=self.qualified_fixture();path=self.root/'engineering_report.json';r=json.loads(path.read_text());r[field]=value
            c['qualification']['one_step']['engineering_report']=self.artifact(path.name,r)
            with self.subTest(field=field):self.assertTrue(any(reason in e for e in v.validate_for_phase(c,'qualification','one_step',base_dir=self.root)))

    def test_unknown_contract_versions_and_later_phases_refused(self):
        for version in ('b_v1','b_v4',None):
            c=copy.deepcopy(self.c);c['protocol_version']=version
            self.assertTrue(any('unknown protocol_version' in e for e in v.validate_for_phase(c,'engineering','one_step',base_dir=self.root)))
        c=copy.deepcopy(self.c);c['record_schema']='unknown'
        self.assertTrue(v.validate_for_phase(c,'engineering','one_step',base_dir=self.root))
        for phase in ('pilot','main_collection','final_evaluation'):
            self.assertEqual(v.validate_for_phase(self.c,phase,'one_step'),['phase not yet implemented'])
        with self.assertRaises(ValueError):v.load_contract(ROOT/'protocols/paper_b/contract_v1.yaml')

    def test_draft_launch_cli_is_refused(self):
        run=subprocess.run([sys.executable,str(ROOT/'protocols/paper_b/launch_validator.py'),'--for-launch'],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('draft launches refused',run.stdout)

    def test_changed_fixture_and_split_leakage_refused(self):
        c=self.qualified_fixture();(self.root/'fixture.py').write_text('# Changed fixture')
        self.assertTrue(any('stale engineering fixture' in e for e in v.validate_for_phase(c,'engineering','one_step',base_dir=self.root)))
        (self.root/'fixture.py').write_text('# Closed test stub')
        c=self.qualified_fixture();splits=json.loads((self.root/'splits.json').read_text());splits['partitions']['test']=['fixture-0']
        c['statistics']['split_manifest']=self.artifact('splits.json',splits)
        self.bind(c,'one_step')
        self.assertTrue(any('split descendant leakage' in e for e in v.validate_for_phase(c,'qualification','one_step',base_dir=self.root)))

    def test_smoke_consumes_active_contract_and_stamps_binding(self):
        output=self.root/'smoke'
        run=subprocess.run([sys.executable,str(ROOT/'experiments/paper_b/smoke_b.py'),'--output',str(output)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads((output/'smoke_summary.json').read_text())
        self.assertEqual(report['protocol_version'],'b_v2')
        self.assertEqual(report['design_sha256'],v.binding_digest(v.load_contract(),'engineering','one_step'))
        self.assertTrue(report['passed'])
        self.assertEqual(report['banner'],'ENGINEERING_ONLY')

    def test_missing_structure_and_malformed_sections_refused(self):
        c=copy.deepcopy(self.c);del c['replay_allowance']
        self.assertTrue(any('structural gap' in e for e in v.validate_for_phase(c,'engineering','one_step',base_dir=self.root)))
        c=copy.deepcopy(self.c);c['lanes']=None
        self.assertTrue(v.validate_for_phase(c,'engineering','one_step',base_dir=self.root))
