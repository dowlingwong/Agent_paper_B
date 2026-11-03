"""No real server, model, GPU, or network; Stage A qualification remains STOP."""
from types import SimpleNamespace
import pytest
from r1.exam import qualify
from r1.scripts import llamacpp_probe
from r1.scripts.exam_runner import run_fresh_qualification
from r1.exam.runtime import PreparationStop


def test_direct_qualification_stops_before_job_access_or_output():
    class NoAccess:
        def __getitem__(self,key):raise AssertionError('job accessed')
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        qualify.qualify(NoAccess())


def test_stagea_probe_direct_entry_stops_before_output(tmp_path):
    out=tmp_path/'should-not-exist'
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        llamacpp_probe.main(['--binary','/fake','--model','/fake','--gpu','GPU-FAKE',
                            '--port','12345','--out',str(out),'--exam-stage-a'])
    assert not out.exists()


def test_stagea_qualification_generation_passes_explicit_false():
    calls=[]
    def chat(prompt,*,max_tokens,seed,extra):
        calls.append(extra)
        return {'usage':{'completion_tokens':1}}
    llamacpp_probe.generation(SimpleNamespace(chat=chat),1,exam_stage_a=True)
    assert calls==[{'ignore_eos':True,'cache_prompt':False}]


def test_stagea_qualification_recorder_binds_observed_identity(tmp_path,monkeypatch):
    from r1.exam import cache_runtime,cache_proc,cache_false
    identity={'pid':7,'process_start_ticks':9,'fresh':False}
    monkeypatch.setattr(cache_runtime,'capture_parent_identity',lambda inst,**pins:identity)
    monkeypatch.setattr(cache_proc,'sample_llama_server_processes',lambda i:{'pid':7,'count':1})
    calls=[]
    def make(url,alias,**kwargs):
        calls.append((url,alias,kwargs));return 'synthetic-recorder'
    monkeypatch.setattr(cache_false,'FalseCallRecorder',make)
    inst=SimpleNamespace(url='http://fixture',alias='fixture')
    args=SimpleNamespace(expect_binary_sha256='binary-pin',expect_sha256='model-pin')
    recorder,bound=llamacpp_probe.qualification_recorder(inst,args,tmp_path/'qual.jsonl')
    assert recorder=='synthetic-recorder' and bound is identity
    assert calls[0][2]['identity'] is identity and calls[0][2]['journal_path']==tmp_path/'qual.jsonl'
    assert calls[0][2]['census']()=={'pid':7,'count':1}
    assert not (tmp_path/'qual.jsonl').exists()


def test_qualification_recorder_rejects_missing_pins_before_capture(tmp_path,monkeypatch):
    from r1.exam import cache_runtime
    monkeypatch.setattr(cache_runtime,'capture_parent_identity',lambda *a,**k:pytest.fail('capture called'))
    with pytest.raises(RuntimeError,match='pins required'):
        llamacpp_probe.qualification_recorder(None,SimpleNamespace(expect_binary_sha256=None,expect_sha256='x'),tmp_path/'j')


def test_qualification_bad_pins_stop_before_server_launch(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr(llamacpp_probe,'port_is_free',lambda p:True)
    monkeypatch.setattr(llamacpp_probe.lsi,'build_info',lambda p:{'version_line':'actual-build'})
    monkeypatch.setattr(llamacpp_probe.lsi,'sha256_file',lambda p:'actual-sha')
    monkeypatch.setattr(llamacpp_probe.lsi,'LlamaServerInstance',lambda *a,**k:pytest.fail('server launched'))
    rc=llamacpp_probe.main(['--binary','/fake','--model','/fake','--gpu','GPU-FAKE','--port','12345',
                            '--out',str(tmp_path/'probe'),'--exam-stage-a','--expect-sha256','expected-model',
                            '--expect-binary-sha256','expected-binary','--expect-build','expected-build'])
    assert rc==1


def test_qualification_existing_directory_never_reused(tmp_path):
    existing=tmp_path/'attempt';existing.mkdir();old=existing/'qualification.json';old.write_text('old')
    runner=SimpleNamespace(cfg={},run_job=lambda *a,**k:pytest.fail('old attempt reused'))
    with pytest.raises(PreparationStop,match='already exists'):
        run_fresh_qualification(runner,existing,{'quant_source':{'sha256':'pin'}},32768)
    assert old.read_text()=='old'


def test_qualification_worker_stop_not_swallowed_even_if_output_exists(tmp_path):
    def run(job,module):
        (tmp_path/'attempt'/'qualification.json').write_text('{"status":"PASS"}')
        raise RuntimeError('synthetic watchdog STOP')
    runner=SimpleNamespace(cfg={'dryrun':True},run_job=run)
    with pytest.raises(RuntimeError,match='watchdog STOP'):
        run_fresh_qualification(runner,tmp_path/'attempt',{'quant_source':{'sha256':'pin'}},32768)
    assert (tmp_path/'attempt'/'qualification.json').exists()


def test_fresh_qualification_rejects_wrong_context(tmp_path):
    import json
    def run(job,module):
        (tmp_path/'attempt'/'qualification.json').write_text(json.dumps({'status':'PASS','model_sha256':'pin','context':16384}))
    runner=SimpleNamespace(cfg={'dryrun':True},run_job=run)
    with pytest.raises(PreparationStop,match='model/context binding'):
        run_fresh_qualification(runner,tmp_path/'attempt',{'quant_source':{'sha256':'pin'}},32768)


def test_qualification_exit_protocol_allows_only_bound_oom_fallback():
    from r1.exam.qualify import qualification_exit_code
    oom={'status':'MECHANICAL_FAILURE','allocation_failure_evidence':{
        'kind':'cuda_allocation_out_of_memory','healthy_idle_after_stop':True}}
    assert qualification_exit_code(oom)==0
    assert qualification_exit_code({'status':'PASS'})==0
    for bad in ({'status':'MECHANICAL_FAILURE'}, {'status':'PREPARATION_STOP'},
                {'status':'MECHANICAL_FAILURE','allocation_failure_evidence':{
                    'kind':'cuda_allocation_out_of_memory','healthy_idle_after_stop':False}}):
        assert qualification_exit_code(bad)==1


def test_fake_32k_oom_falls_back_to_16k_only_after_bound_receipt(tmp_path,monkeypatch):
    import json
    from r1.scripts import exam_runner
    from r1.exam import cache_runtime,stage_a as worker
    monkeypatch.setattr(worker,'require_d3_evidence',lambda:None)
    monkeypatch.setattr(cache_runtime,'reject_unverified_lease',lambda:None)
    monkeypatch.setattr(cache_runtime,'capture_parent_identity',lambda *a,**k:{'synthetic':True})
    monkeypatch.setattr(cache_runtime,'reject_unverified_cold',lambda *a:None)
    spec={'id':'fixture','role':'candidate','runtime':{'footprint_mib':None},
          'quant_source':{'sha256':'pin'},'thinking_policy':{'mode':'off'}}
    class Runner:
        cfg={'dryrun':True,'server':{'binary_sha256':'bin','build':'fake'}}
        out=tmp_path
        state={'completed':{}}
        service=None
        contexts=[]
        def spec_order(self,selected=None):return [spec]
        def validate_spec(self,*args,**kwargs):pass
        def save(self):pass
        def server(self,spec,mode,ctx):
            self.contexts.append(ctx);self.service=SimpleNamespace(record_path='synthetic',port=18482);return self.service
        def stop_service(self):self.service=None
        def run_job(self,job,module):
            out=Path(job['out']);out.mkdir(parents=True,exist_ok=True)
            if module=='r1.exam.qualify':
                ctx=job['ctx']
                if ctx==32768:
                    from r1.exam.guards import digest_file
                    log=out/'oom_server.log'
                    log.write_text('0.03.957.863 E ggml_backend_cuda_buffer_type_alloc_buffer: allocating 102.00 MiB on device 0: cudaMalloc failed: out of memory\n')
                    result={'status':'MECHANICAL_FAILURE','context':ctx,'model_sha256':'pin',
                            'allocation_failure_evidence':{'kind':'cuda_allocation_out_of_memory',
                                                           'healthy_idle_after_stop':True,
                                                           'server_log':str(log),
                                                           'server_log_sha256':digest_file(log)}}
                else:result={'status':'PASS','context':ctx,'model_sha256':'pin','footprint_mib':50}
                from r1.exam.qualify import qualification_exit_code
                if qualification_exit_code(result):raise RuntimeError('worker failed')
                (out/'qualification.json').write_text(json.dumps(result))
            else:
                (out/'stage_a.json').write_text(json.dumps({'passed':True,'failure_classes':[]}))
    from pathlib import Path
    r=Runner()
    exam_runner._stage_a_cooperative(r,None)
    assert r.contexts==[16384]
    table=json.loads((tmp_path/'stage_a_table.json').read_text())
    row=table['rows'][0]
    assert row['ctx_size']==16384 and row['cpu_pool_only'] is True
    assert (tmp_path/'fixture/stage-a/32768/qualification/qualification.json').exists()
    assert (tmp_path/'fixture/stage-a/16384/qualification/qualification.json').exists()


def test_unverified_mechanical_failure_cannot_fallback(tmp_path):
    import json
    def run(job,module):
        (Path(job['out'])/'qualification.json').write_text(json.dumps({
            'status':'MECHANICAL_FAILURE','context':32768,'model_sha256':'pin'}))
    from pathlib import Path
    runner=SimpleNamespace(cfg={'dryrun':True},run_job=run)
    with pytest.raises(PreparationStop,match='lacks completed OOM/idle evidence'):
        run_fresh_qualification(runner,tmp_path/'attempt',{'quant_source':{'sha256':'pin'}},32768)


def test_template_failure_candidate_row_continues_to_next_candidate(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    from r1.scripts import exam_runner
    from r1.exam import cache_runtime, stage_a as worker
    from r1.exam.guards import digest_file
    monkeypatch.setattr(worker, 'require_d3_evidence', lambda: None)
    monkeypatch.setattr(cache_runtime, 'reject_unverified_lease', lambda: None)
    monkeypatch.setattr(cache_runtime, 'capture_parent_identity', lambda *a, **k: {'synthetic': True})
    monkeypatch.setattr(cache_runtime, 'reject_unverified_cold', lambda *a: None)

    def make_spec(cid):
        return {'id': cid, 'role': 'candidate', 'runtime': {'footprint_mib': None},
                'quant_source': {'sha256': 'pin-' + cid}, 'thinking_policy': {'mode': 'off'}}

    specs = [make_spec('tmpl_bad'), make_spec('tmpl_good')]

    class Runner:
        cfg = {'dryrun': True, 'server': {'binary_sha256': 'bin', 'build': 'fake'}}
        out = tmp_path
        state = {'completed': {}}
        service = None
        def __init__(self):
            self.served = []
        def spec_order(self, selected=None): return [dict(s) for s in specs]
        def validate_spec(self, *a, **k): pass
        def save(self): pass
        def server(self, spec, mode, ctx):
            self.served.append(spec['id'])
            self.service = SimpleNamespace(record_path='synthetic', port=18482)
            return self.service
        def stop_service(self): self.service = None
        def run_job(self, job, module):
            out = Path(job['out']); out.mkdir(parents=True, exist_ok=True)
            if module == 'r1.exam.qualify':
                cid = job['candidate']['id']
                if cid == 'tmpl_bad':
                    log = out / 'server.log'
                    log.write_text('init: chat template parsing error: Unable to generate parser\n'
                                   'llama_server: exiting due to model loading error\n')
                    result = {'status': 'TEMPLATE_FAILURE', 'context': job['ctx'],
                              'model_sha256': job['candidate']['quant_source']['sha256'],
                              'template_failure_evidence': {
                                  'kind': 'chat_template_parse_error', 'failure_class': 'template',
                                  'retry_at_16k': False, 'server_log': str(log),
                                  'server_log_sha256': digest_file(log)}}
                else:
                    result = {'status': 'PASS', 'context': job['ctx'],
                              'model_sha256': job['candidate']['quant_source']['sha256'],
                              'footprint_mib': 50}
                (out / 'qualification.json').write_text(json.dumps(result))
            else:
                (out / 'stage_a.json').write_text(json.dumps({
                    'candidate': job['candidate']['id'], 'passed': True, 'failure_classes': []}))

    token = cache_runtime._authorized.set(True)
    try:
        r = Runner()
        exam_runner._stage_a_cooperative(r, None)
    finally:
        cache_runtime._authorized.reset(token)
    table = json.loads((tmp_path / 'stage_a_table.json').read_text())
    rows = {row['candidate']: row for row in table['rows']}
    assert rows['tmpl_bad']['passed'] is False and rows['tmpl_bad']['failure_classes'] == ['template']
    assert rows['tmpl_good']['passed'] is True
    assert r.served == ['tmpl_good']  # the template-failed candidate never started a server


def test_lease_completion_accepts_a_failed_start_record(tmp_path, monkeypatch):
    """The runner's completion writer must accept a finalized pre-readiness failure."""
    import json, os
    from pathlib import Path
    from r1.scripts import exam_runner
    from r1.exam import cache_proc
    out = tmp_path / 'out'
    rec_dir = out / 'servers' / 'cand'
    rec_dir.mkdir(parents=True)
    record = {'pid': 999999, 'start_ticks': 555, 'stopped_utc': '2026-11-03T00:00:00Z',
              'returncode': 1, 'exited_early': 1, 'stopped_before_ready': True,
              'lease_inheritance': {'version': 'trackx_lease_inheritance/v1',
                                    'server_pid': 999999, 'server_start_ticks': 555,
                                    'kcmp_rc': 0, 'kcmp_same_ofd': True}}
    (rec_dir / 'llama_server_9000.json').write_text(json.dumps(record) + '\n')
    (out / 'batch_state.json').write_text(json.dumps({'status': 'COMPLETE'}) + '\n')
    evidence = tmp_path / 'evidence'; evidence.mkdir()
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(evidence))
    monkeypatch.setattr(cache_proc, 'process_start_ticks', lambda pid: 4242)
    exam_runner._write_lease_completion(SimpleNamespace(out=out))
    completion = json.loads((evidence / 'lease_completion.json').read_text())
    assert completion['servers'] == [{'pid': 999999, 'start_ticks': 555,
                                      'stopped_utc': '2026-11-03T00:00:00Z',
                                      'record_sha256': completion['servers'][0]['record_sha256'],
                                      'record_path': completion['servers'][0]['record_path']}]
    assert completion['runner_start_ticks'] == 4242


def test_await_idle_gpu_retries_a_transient_teardown(monkeypatch):
    """A just-exited server may linger in nvidia-smi; a bounded wait must absorb it."""
    from r1.scripts import exam_runner
    from r1.exam import runtime
    from r1.scripts import llama_server_instance as lsi
    samples = iter([{'free_mib': 100, 'utilisation_percent': 99},
                    {'free_mib': 200, 'utilisation_percent': 40},
                    {'free_mib': 20000, 'utilisation_percent': 0}])
    apps = iter([[], [], []])
    monkeypatch.setattr(runtime, 'gpu_sample', lambda cfg: next(samples))
    monkeypatch.setattr(lsi, 'gpu_compute_apps', lambda: next(apps))
    slept = []
    observed, sample = exam_runner.await_idle_gpu({}, attempts=5, interval=0, sleep=slept.append)
    assert observed == [] and sample['free_mib'] == 20000 and len(slept) == 2


def test_await_idle_gpu_still_stops_for_a_foreign_app(monkeypatch):
    from r1.scripts import exam_runner
    from r1.exam import runtime
    from r1.scripts import llama_server_instance as lsi
    monkeypatch.setattr(runtime, 'gpu_sample', lambda cfg: {'free_mib': 20000, 'utilisation_percent': 0})
    monkeypatch.setattr(lsi, 'gpu_compute_apps', lambda: [{'pid': 123, 'used_memory': '1 MiB'}])
    slept = []
    with pytest.raises(PreparationStop, match='after 3 observations'):
        exam_runner.await_idle_gpu({}, attempts=3, interval=0, sleep=slept.append)
    assert len(slept) == 2  # waits only between attempts


def test_await_idle_gpu_stops_immediately_when_the_census_is_unknown(monkeypatch):
    from r1.scripts import exam_runner
    from r1.exam import runtime
    from r1.scripts import llama_server_instance as lsi
    monkeypatch.setattr(runtime, 'gpu_sample', lambda cfg: {'free_mib': 20000, 'utilisation_percent': 0})
    monkeypatch.setattr(lsi, 'gpu_compute_apps', lambda: None)
    slept = []
    with pytest.raises(PreparationStop, match='GPU census unavailable'):
        exam_runner.await_idle_gpu({}, attempts=5, interval=0, sleep=slept.append)
    assert slept == []
