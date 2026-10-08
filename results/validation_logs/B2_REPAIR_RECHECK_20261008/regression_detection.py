import sys,importlib.util,unittest,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'B2_REREVIEW_20261008'))
from common import *
# Import common first to bind code to B2_REVIEW_ROOT; read repaired tests from B only.
testroot=Path(os.environ.get('B2_TEST_ROOT', ROOT / 'tests/control'))
checks={
 'test_timing.py':['TestProposedRule.test_explicit_cutoff_changes_continuation_policy_fit'],
 'test_evaluate_tree.py':['TestHarness.test_selected_continuation_cutoff_matches_scored_model_and_diagnostics','TestHarness.test_masks_survive_evaluation_and_bootstrap_with_all_roots_in_denominator','TestHarness.test_phase_specific_masks_and_resource_accounting','TestHarness.test_nonqualifying_family_bounds_are_preserved']}
out={}
for filename,names in checks.items():
    spec=importlib.util.spec_from_file_location(filename.replace('.py',''),testroot/filename);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for name in names:
        cls,method=name.split('.');res=unittest.TestResult();getattr(mod,cls)(method).run(res)
        out[name]=dict(testsRun=res.testsRun,failures=len(res.failures),errors=len(res.errors),details=[x[1] for x in res.failures+res.errors])
emit(dict(code_root=str(ROOT),results=out))
