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
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr(stage_a,'post',post)
    instance=SimpleNamespace(ctx_size=context)
    recorder=SimpleNamespace(completion=lambda payload:post(instance,'/completion',payload))
    nongen=SimpleNamespace(post=lambda route,payload:post(instance,route,payload))
    evidence=stage_a.fit_prefill(instance,recorder,nongen)
    assert calls[1][1]['n_predict']==1
    assert calls[1][1]['cache_prompt'] is False
    assert evidence['declared_context_tokens']==context
    assert evidence['prefill_requested_tokens']==evidence['prefill_tokens']==context-1
    assert evidence['prefill_generated_tokens']==evidence['prefill_requested_generated_tokens']==1
    assert evidence['native_api_reserve_tokens']==1

@pytest.mark.parametrize('evaluated,generated',[(32766,1),(32767,0),(32767,None)])
def test_bad_native_counts_retained_and_fail(monkeypatch,evaluated,generated):
    def post(instance,route,payload):
        if route=='/tokenize':return {'tokens':[1,2]}
        return {'tokens_evaluated':evaluated,'tokens_predicted':generated}
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr(stage_a,'post',post)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *args,**kwargs:{'synthetic':True})
    instance=SimpleNamespace(ctx_size=32768)
    recorder=SimpleNamespace(completion=lambda payload:post(instance,'/completion',payload))
    nongen=SimpleNamespace(post=lambda route,payload:post(instance,route,payload))
    result=stage_a.run_stage_a(instance,{'id':'fixture'},[{}],
        gpu_sample=lambda:{'free_mib':22000,'used_mib':1000},schema_format={},cache_context={'false_recorder':recorder,'non_generation_recorder':nongen})
    assert result['passed'] is False and result['failure_classes']==['offload']
    assert result['prefill_tokens']==evaluated and result['prefill_generated_tokens']==generated

@pytest.mark.parametrize('context',[32768,16384])
def test_unattempted_prefill_metadata(context):
    evidence=stage_a.prefill_metadata(context)
    assert evidence['declared_context_tokens']==context
    assert evidence['prefill_requested_tokens']==context-1
    assert evidence['prefill_tokens'] is None and evidence['prefill_generated_tokens'] is None
    assert evidence['native_api_reserve_tokens']==1


def test_descriptive_precedes_recorded_false_and_evidence_stop_propagates(monkeypatch):
    from r1.exam.cache_false import D3EvidenceStop
    events=[]
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *a,**k:events.append('true') or {})
    monkeypatch.setattr(stage_a,'post',lambda *a,**k:{'tokens':[1]})
    def completion(payload):
        events.append('false')
        assert payload['cache_prompt'] is False
        raise D3EvidenceStop('synthetic evidence failure')
    instance=SimpleNamespace(ctx_size=32768)
    nongen=SimpleNamespace(post=lambda route,payload:{'tokens':[1]})
    with pytest.raises(D3EvidenceStop,match='synthetic evidence failure'):
        stage_a.run_stage_a(instance,{'id':'fixture'},[{}],gpu_sample=lambda:{'free_mib':22000,'used_mib':1000},
                            schema_format={},cache_context={'false_recorder':SimpleNamespace(completion=completion),'non_generation_recorder':nongen})
    assert events==['true','false']


def test_grammar_uses_false_recorder_and_keeps_seed():
    calls=[]
    schema={'json_schema':{'schema':{'required':['answer']}}}
    def chat(prompt,*,max_tokens,seed,extra):
        calls.append((prompt,seed,extra))
        return {'choices':[{'message':{'content':'{"answer": "ok"}',
                                       'reasoning_content':'synthetic'}}], 'usage':{}}
    row={'prompt':'synthetic','seed':123}
    result=stage_a.thinking_grammar_probe(SimpleNamespace(chat=chat),row,schema)
    assert result['passed'] and calls[0][1]==123 and calls[0][2]['cache_prompt'] is False


def test_grammar_propagates_infrastructure_evidence_stop():
    from r1.exam.cache_false import D3EvidenceStop
    def chat(*a,**k): raise D3EvidenceStop('synthetic evidence failure')
    with pytest.raises(D3EvidenceStop):
        stage_a.thinking_grammar_probe(SimpleNamespace(chat=chat),{'prompt':'synthetic','seed':1},{})


@pytest.mark.parametrize('failure',['no_samples','sample_error','low_free'])
def test_vram_resource_or_census_failures_propagate_stop(monkeypatch,failure):
    from r1.exam.cache_false import D3EvidenceStop
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *a,**k:{})
    # Return immediately from a synthetic prefill after the telemetry thread starts.
    monkeypatch.setattr(stage_a,'fit_prefill',lambda *a,**k:{'prefill_tokens':3,'prefill_generated_tokens':1})
    def gpu():
        if failure=='sample_error':raise OSError('synthetic census failure')
        if failure=='no_samples':raise OSError('synthetic no sample')
        return {'free_mib':512,'used_mib':1}
    with pytest.raises(D3EvidenceStop,match='VRAM'):
        stage_a.run_stage_a(SimpleNamespace(ctx_size=4),{'id':'fixture'},[{}],gpu_sample=gpu,
                            schema_format={},cache_context={'false_recorder':object(),'non_generation_recorder':object()})


@pytest.mark.parametrize('sample',[{}, {'free_mib':2048}, {'free_mib':2048,'used_mib':None},
                                  {'free_mib':True,'used_mib':1}, {'free_mib':float('nan'),'used_mib':1},
                                  {'free_mib':2048,'used_mib':-1},'malformed'])
def test_vram_missing_or_invalid_fields_are_stop_not_candidate_failure(monkeypatch,sample):
    from r1.exam.cache_false import D3EvidenceStop
    monkeypatch.setattr(stage_a,'require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *a,**k:{})
    monkeypatch.setattr(stage_a,'fit_prefill',lambda *a,**k:{'prefill_tokens':3,'prefill_generated_tokens':1})
    with pytest.raises(D3EvidenceStop,match='VRAM'):
        stage_a.run_stage_a(SimpleNamespace(ctx_size=4),{'id':'fixture'},[{}],gpu_sample=lambda:sample,
                            schema_format={},cache_context={'false_recorder':object(),'non_generation_recorder':object()})
