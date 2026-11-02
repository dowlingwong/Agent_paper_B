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


FIXTURES = Path(__file__).parent / 'fixtures'


def _run_real_template_probe(tmp_path, monkeypatch, *, probe_overrides=None, log_text=None):
    from r1.exam import cache_runtime
    pristine = json.loads((FIXTURES / 'stop4_olmo_probe.json').read_text())
    real = json.loads(json.dumps(pristine))
    attempt = tmp_path / 'attempt'; attempt.mkdir()
    log = attempt / 'llama_server_fixture.log'
    log.write_text(log_text if log_text is not None else (FIXTURES / 'stop4_olmo_server.log').read_text())
    if probe_overrides:
        for dotted, value in probe_overrides.items():
            target = real
            parts = dotted.split('.')
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = value
    real['server_log'] = str(log)
    probe_path = attempt / 'probe_20261102T035958Z.json'
    probe_path.write_text(json.dumps(real))
    monkeypatch.setattr(q.llamacpp_probe, 'main',
                        lambda args: (probe_path.write_text(json.dumps(real)), 1)[1])
    monkeypatch.setattr(q, 'free_port', lambda: 18481)
    job = {'config': {'server': {'binary': 'fixture', 'build': pristine['build']['version_line'],
                                 'binary_sha256': pristine['binary_sha256']},
                      'gpu_uuid': pristine['gpu_uuid']},
           'candidate': {'id': 'olmo31_32b', 'thinking_policy': {'mode': 'off'},
                         'runtime': {'model_path': 'fixture.gguf'},
                         'quant_source': {'size_bytes': 100, 'sha256': pristine['model_sha256']}},
           'out': str(attempt), 'ctx': 32768}
    token = cache_runtime._authorized.set(True)
    try:
        return q.qualify(job)
    finally:
        cache_runtime._authorized.reset(token)


def test_real_stop4_probe_is_classified_as_a_candidate_template_failure(tmp_path, monkeypatch):
    from r1.exam.qualify import qualification_exit_code
    result = _run_real_template_probe(tmp_path, monkeypatch)
    assert result['status'] == 'TEMPLATE_FAILURE'
    evidence = result['template_failure_evidence']
    assert evidence['kind'] == 'chat_template_parse_error'
    assert evidence['failure_class'] == 'template' and evidence['retry_at_16k'] is False
    assert Path(evidence['server_log']).name == 'llama_server_fixture.log'
    assert evidence['exit_evidence']['stop_reason'].endswith('(rc=1)')
    assert qualification_exit_code(result) == 0


@pytest.mark.parametrize('overrides,log_text,expected', [
    ({'binary_sha256': '0' * 64}, None, 'PREPARATION_STOP'),
    ({'model_sha256': '0' * 64}, None, 'PREPARATION_STOP'),
    ({'build.version_line': 'version: wrong'}, None, 'PREPARATION_STOP'),
    ({}, 'llama_server: exiting due to model loading error\n', 'PREPARATION_STOP'),
    ({}, 'chat template parsing error: x\n', 'PREPARATION_STOP'),
    ({'stop_reasons': []}, None, 'PREPARATION_STOP'),
])
def test_real_stop4_probe_negatives_remain_preparation_stop(tmp_path, monkeypatch, overrides, log_text, expected):
    result = _run_real_template_probe(tmp_path, monkeypatch, probe_overrides=overrides, log_text=log_text)
    assert result['status'] == expected


def test_template_failure_log_outside_attempt_dir_remains_preparation_stop(tmp_path, monkeypatch):
    from r1.exam import cache_runtime
    real = json.loads((FIXTURES / 'stop4_olmo_probe.json').read_text())
    outside = tmp_path / 'outside.log'
    outside.write_text((FIXTURES / 'stop4_olmo_server.log').read_text())
    attempt = tmp_path / 'attempt'; attempt.mkdir()
    real['server_log'] = str(outside)
    probe_path = attempt / 'probe_20261102T035958Z.json'
    probe_path.write_text(json.dumps(real))
    monkeypatch.setattr(q.llamacpp_probe, 'main', lambda args: (probe_path.write_text(json.dumps(real)), 1)[1])
    monkeypatch.setattr(q, 'free_port', lambda: 18481)
    job = {'config': {'server': {'binary': 'fixture', 'build': real['build']['version_line'],
                                 'binary_sha256': real['binary_sha256']},
                      'gpu_uuid': real['gpu_uuid']},
           'candidate': {'id': 'olmo31_32b', 'thinking_policy': {'mode': 'off'},
                         'runtime': {'model_path': 'fixture.gguf'},
                         'quant_source': {'size_bytes': 100, 'sha256': real['model_sha256']}},
           'out': str(attempt), 'ctx': 32768}
    token = cache_runtime._authorized.set(True)
    try:
        result = q.qualify(job)
    finally:
        cache_runtime._authorized.reset(token)
    assert result['status'] == 'PREPARATION_STOP'
