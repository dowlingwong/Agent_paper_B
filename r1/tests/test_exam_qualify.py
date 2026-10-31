"""Known CUDA allocation failure vs unknown qualification state; no GPU/model calls."""
import json
from pathlib import Path
import pytest
from r1.exam import qualify as q
from r1.exam import runtime


@pytest.mark.parametrize('mode,expected',[('oom','MECHANICAL_FAILURE'),('unknown','PREPARATION_STOP'),
                                          ('foreign','PREPARATION_STOP'),('no_census','PREPARATION_STOP'),
                                          ('wrong_pin','PREPARATION_STOP')])
def test_load_failure_classification(tmp_path,monkeypatch,mode,expected):
    log=tmp_path/'server.log'
    log.write_text('ggml_backend_cuda_buffer_type_alloc_buffer: allocating 26000.00 MiB on device 0: cudaMalloc failed: out of memory\n' if mode!='unknown' else 'unclassified startup error\n')
    raw={'footprint_mib_to_pin':None,'gpu_uuid':'GPU-test','server_log':str(log),'server_stop':{'returncode':1},
         'pins_match':{'build':mode!='wrong_pin','model_sha256':True},'stop_reasons':['server failed before ready']}
    def probe(args):(tmp_path/'probe_fixture.json').write_text(json.dumps(raw));return 1
    monkeypatch.setattr(q.llamacpp_probe,'main',probe)
    monkeypatch.setattr(q,'free_port',lambda:18481)
    monkeypatch.setattr(q.lsi,'gpu_compute_apps',lambda:None if mode=='no_census' else ([{'pid':123}] if mode=='foreign' else []))
    monkeypatch.setattr(runtime,'gpu_sample',lambda cfg:{'free_mib':23000})
    job={'config':{'server':{'binary':'fixture','build':'fixture','binary_sha256':'00'*32},'gpu_uuid':'GPU-test'},'candidate':{'id':'fixture',
          'thinking_policy':{'mode':'off'},'runtime':{'model_path':'fixture.gguf'},'quant_source':{'size_bytes':100,'sha256':'0'*64}},
         'out':str(tmp_path),'ctx':32768}
    from r1.exam import cache_runtime
    token=cache_runtime._authorized.set(True)
    try: result=q.qualify(job)
    finally: cache_runtime._authorized.reset(token)
    assert result['status']==expected and result['footprint_mib'] is None
    if mode=='oom':assert result['allocation_failure_evidence']['healthy_idle_after_stop']
