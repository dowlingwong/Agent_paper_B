"""Approved native context reserve; request and measured counts, no inference."""
from types import SimpleNamespace
import pytest
from r1.exam import stage_a

@pytest.mark.parametrize('context',[32768,16384])
def test_native_reserve_request_and_evidence(monkeypatch,context):
    calls=[]
    def post(instance,route,payload):
        calls.append((route,payload))
        if route=='/tokenize':return {'tokens':[1,2,3]}
        assert len(payload['prompt'])<instance.ctx_size
        return {'tokens_evaluated':len(payload['prompt']),'tokens_predicted':1}
    monkeypatch.setattr(stage_a,'post',post)
    evidence=stage_a.fit_prefill(SimpleNamespace(ctx_size=context))
    assert calls[1][1]['n_predict']==1
    assert evidence['declared_context_tokens']==context
    assert evidence['prefill_requested_tokens']==evidence['prefill_tokens']==context-1
    assert evidence['prefill_generated_tokens']==evidence['prefill_requested_generated_tokens']==1
    assert evidence['native_api_reserve_tokens']==1

@pytest.mark.parametrize('evaluated,generated',[(32766,1),(32767,0),(32767,None)])
def test_bad_native_counts_retained_and_fail(monkeypatch,evaluated,generated):
    def post(instance,route,payload):
        if route=='/tokenize':return {'tokens':[1,2]}
        return {'tokens_evaluated':evaluated,'tokens_predicted':generated}
    monkeypatch.setattr(stage_a,'post',post)
    result=stage_a.run_stage_a(SimpleNamespace(ctx_size=32768),{'id':'fixture'},[{}],
        gpu_sample=lambda:{'free_mib':22000,'used_mib':1000},schema_format={})
    assert result['passed'] is False and result['failure_classes']==['offload']
    assert result['prefill_tokens']==evaluated and result['prefill_generated_tokens']==generated
