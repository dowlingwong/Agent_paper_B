from common import *
import importlib.util, unittest
spec=importlib.util.spec_from_file_location('reviewed_test',ROOT/'tests/control/test_timing.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
result={}
for mode in ['current','reconstructed_old']:
    orig=t._oof_second_stage
    try:
        if mode=='reconstructed_old':t._oof_second_stage=old_oof
        case=mod.TestProposedRule('test_max_bias_correction'); res=unittest.TestResult(); case.run(res)
        result[mode]=dict(testsRun=res.testsRun,failures=len(res.failures),errors=len(res.errors),details=[x[1] for x in res.failures+res.errors])
    finally:t._oof_second_stage=orig
emit(result)
