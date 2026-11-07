"""Owned fake-server preflight paths; never invoke a model, GPU or remote host."""
import fcntl
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from r1.scripts import b1_host_preflight as pre


@pytest.mark.parametrize('failure', ['none', 'start', 'descriptor', 'cleanup'])
def test_owned_server_stopped_and_lease_closed(tmp_path, monkeypatch, failure, capsys):
    home=tmp_path/'home'; lock_dir=home/'r1_locks'; lock_dir.mkdir(parents=True)
    lock=lock_dir/'gpu0.lock';lock.touch()
    monkeypatch.setattr(Path,'home',classmethod(lambda cls: home))
    cfg={'ctx_size':32768,'n_gpu_layers':999,'gpu_uuid':'GPU-fixture',
         'server':{'binary':'fake','start_timeout':1}}
    spec={'id':'qwen25_coder_7b','runtime':{'model_path':'fake.gguf','footprint_mib':1},
          'quant_source':{'sha256':'a'*64},'thinking_policy':{}}
    monkeypatch.setattr(pre,'check_inputs',lambda *a:(cfg,spec,{'fake':True}))
    monkeypatch.setattr(pre,'idle_gpu',lambda cfg:{'free_mib':2000,'utilisation_percent':0})
    monkeypatch.setattr(pre,'gpu_sample',lambda cfg:{'free_mib':2000,'utilisation_percent':0})
    monkeypatch.setattr(pre,'gpu_compute_apps',lambda:[{'pid':1234}])
    monkeypatch.setattr(pre,'template_repair_args',lambda spec:[])
    calls=[]
    class FakeServer:
        def __init__(self,*args,**kwargs):
            self.record={'start_ticks':7,'pgid':1234};self.process=None
        def start(self,**kwargs):
            calls.append(('start',kwargs['b1_lease_fd']))
            self.process=SimpleNamespace(pid=1234,poll=lambda:None if 'stop' not in calls else 0)
            if failure=='start': raise RuntimeError('start failed')
        def stop(self):
            calls.append('stop')
            if failure=='cleanup': raise RuntimeError('stop failed')
        def offload(self,**kwargs): return {'full':True}
        def model_ids(self): return ['qwen25_coder_7b']
        def props(self): return {'model_path':'fake.gguf'}
    monkeypatch.setattr(pre,'LlamaServerInstance',FakeServer)
    def verify(fd,pid):
        calls.append(('verify',pid))
        if failure=='descriptor': raise RuntimeError('descriptor failed')
    monkeypatch.setattr(pre,'verify_server_fd',verify)
    out=tmp_path/'owned'
    if failure=='none':
        pre.run('a'*40,out)
        assert 'PREFLIGHT_PASS' in capsys.readouterr().out
    else:
        with pytest.raises(RuntimeError,match=failure if failure!='cleanup' else 'stop failed'):
            pre.run('a'*40,out)
    assert calls.count('stop')==1
    with lock.open('r+') as probe:
        fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert out.is_dir()


def test_gate_refusal_has_no_directory_lease_or_server(tmp_path,monkeypatch):
    out=tmp_path/'not-created'
    monkeypatch.setattr(pre,'check_inputs',lambda *a: (_ for _ in ()).throw(RuntimeError('gate refused')))
    monkeypatch.setattr(pre,'acquire',lambda *a: pytest.fail('must not acquire'))
    monkeypatch.setattr(pre,'LlamaServerInstance',lambda *a,**k: pytest.fail('must not start'))
    with pytest.raises(RuntimeError,match='gate refused'): pre.run('a'*40,out)
    assert not out.exists()


def test_original_error_survives_server_stop_failure(tmp_path,monkeypatch,capsys):
    home=tmp_path/'home';(home/'r1_locks').mkdir(parents=True);(home/'r1_locks/gpu0.lock').touch()
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:home))
    cfg={'ctx_size':32768,'n_gpu_layers':999,'gpu_uuid':'gpu','server':{'binary':'x','start_timeout':1}}
    spec={'id':'qwen25_coder_7b','runtime':{'model_path':'fake'},'quant_source':{'sha256':'a'*64},'thinking_policy':{}}
    monkeypatch.setattr(pre,'check_inputs',lambda *a:(cfg,spec,{}))
    monkeypatch.setattr(pre,'idle_gpu',lambda *a:{'free_mib':2000})
    monkeypatch.setattr(pre,'template_repair_args',lambda *a:[])
    class FailedServer:
        def __init__(self,*a,**kw): self.process=SimpleNamespace(pid=1234,poll=lambda:None);self.record={'pgid':1234}
        def start(self,**kw): raise RuntimeError('original start failure')
        def stop(self): raise RuntimeError('stop failure')
    monkeypatch.setattr(pre,'LlamaServerInstance',FailedServer)
    with pytest.raises(RuntimeError,match='original start failure'):
        pre.run('a'*40,tmp_path/'own')
    assert 'stop failure' in capsys.readouterr().err


def test_precheck_binds_registry_path_and_gate_to_reviewed_head(tmp_path,monkeypatch):
    head='a'*40
    cfg={'registry':'r1/exam/registry.yaml','rule':'rule','rule_sha256':'b'*64,
         'nodes':['digits_mlp'],'harness_commit':'c'*40,'work_dir':str(tmp_path),
         'models_dir':str(tmp_path),'dryrun':False,'cache_prompt':False,'template_repairs':{}}
    anchor={'id':'qwen25_coder_7b','role':'anchor','thinking_policy':{},'runtime':{'footprint_mib':1}}
    registry={'candidates':[anchor],'software_anchors':[]}
    monkeypatch.setattr(pre,'REPO',tmp_path)
    monkeypatch.delenv('LLAMACPP_CACHE_PROMPT',raising=False)
    monkeypatch.setattr(pre,'load_config',lambda path:cfg)
    monkeypatch.setattr(pre,'require_committed_b1_config',lambda path,value:head)
    monkeypatch.setattr(pre,'read_registry',lambda path:registry)
    seen=[]
    def registry_check(config,actual_head,*,selected_path,selected_registry):
        seen.append((actual_head,selected_path,selected_registry))
    monkeypatch.setattr(pre,'require_committed_b1_registry',registry_check)
    monkeypatch.setattr(pre,'load_rule',lambda *a:({'version':'x5_rule/v2','thinking_mode':{'always_on_in_b1':'skip'}},'b'*64))
    monkeypatch.setattr(pre,'author_gate',lambda config,phase,sha:head)
    monkeypatch.setattr(pre,'verify_anchor_reference',lambda *a:None)
    monkeypatch.setattr(pre,'worker_environment',lambda:{'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
    monkeypatch.setattr(pre,'b1_harness_sources',lambda *a:{'train.py':'digest'})
    monkeypatch.setattr(pre,'host_check',lambda *a:None)
    monkeypatch.setattr(pre,'space_check',lambda *a:None)
    monkeypatch.setattr(pre,'stage_a_pass_set',lambda *a,**k:{'qwen25_coder_7b':{'passed':True}})
    monkeypatch.setattr(pre,'template_repair_args',lambda *a:[])
    class Runner:
        def __init__(self,*args,**kwargs): assert kwargs['b1_config_head']==head
        def validate_spec(self,item): return {'build':'reviewed'}
    monkeypatch.setattr(pre,'ExamRunner',Runner)
    assert pre.check_inputs(head,tmp_path/'own')==(cfg,anchor,{'build':'reviewed'})
    assert seen==[(head,tmp_path/cfg['registry'],registry)]


@pytest.mark.parametrize('point', ['before_record', 'signal_during_spawn'])
def test_real_owned_server_start_interrupt_stops_only_own_process(tmp_path,monkeypatch,point):
    import subprocess
    import sys
    from unittest.mock import Mock
    binary=tmp_path/'synthetic-server'
    binary.write_text(f'#!{sys.executable}\nimport time\ntime.sleep(30)\n')
    binary.chmod(0o700)
    model=tmp_path/'synthetic.gguf';model.write_text('fixture')
    inst=pre.LlamaServerInstance(tmp_path/'server',str(binary),model_path=model,
                                 alias='fixture',port=12345)
    monkeypatch.setattr(pre.lsi,'port_is_free',lambda port:True)
    monkeypatch.setattr(inst,'_save',Mock())
    other=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
    received=[]
    old_handler=None
    if point=='before_record':
        monkeypatch.setattr(pre.lsi,'process_start_ticks',lambda pid: (_ for _ in ()).throw(InterruptedError('before record')))
    else:
        original=subprocess.Popen
        def interrupted_spawn(*args,**kwargs):
            child=original(*args,**kwargs)
            os.kill(os.getpid(),pre.signal.SIGTERM)
            return child
        old_handler=pre.signal.signal(pre.signal.SIGTERM,lambda sig,frame:received.append(sig))
        monkeypatch.setattr(pre.lsi.subprocess,'Popen',interrupted_spawn)
    try:
        with pytest.raises(InterruptedError): pre.start_owned_server(inst,received=received)
        assert inst.process is not None and inst.record == {}
        pre.stop_owned_server(inst)
        assert inst.process.poll() is not None
        assert other.poll() is None
    finally:
        if inst.process is not None and inst.process.poll() is None:
            inst.process.terminate();inst.process.wait(timeout=3)
        other.terminate();other.wait(timeout=3)
        if old_handler is not None: pre.signal.signal(pre.signal.SIGTERM,old_handler)


def test_missing_record_rejects_nonowned_group_without_signalling(tmp_path,monkeypatch):
    import subprocess
    import sys
    from unittest.mock import Mock
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    inst=SimpleNamespace(process=child,record={},stop=Mock())
    try:
        with pytest.raises(RuntimeError,match='group identity mismatch'):
            pre.stop_owned_server(inst)
        inst.stop.assert_not_called()
        assert child.poll() is None
    finally:
        child.terminate();child.wait(timeout=3)


def test_signals_during_cleanup_are_recorded_without_interrupting_stop(tmp_path,monkeypatch,capsys):
    home=tmp_path/'home';(home/'r1_locks').mkdir(parents=True);lock=home/'r1_locks/gpu0.lock';lock.touch()
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:home))
    cfg={'ctx_size':32768,'n_gpu_layers':999,'gpu_uuid':'gpu','server':{'binary':'x','start_timeout':1}}
    spec={'id':'qwen25_coder_7b','runtime':{'model_path':'fake','footprint_mib':1},'quant_source':{'sha256':'a'*64},'thinking_policy':{}}
    monkeypatch.setattr(pre,'check_inputs',lambda *a:(cfg,spec,{}))
    monkeypatch.setattr(pre,'idle_gpu',lambda *a:{'free_mib':2000})
    monkeypatch.setattr(pre,'gpu_sample',lambda *a:{'free_mib':2000})
    monkeypatch.setattr(pre,'gpu_compute_apps',lambda:[{'pid':1234}])
    monkeypatch.setattr(pre,'template_repair_args',lambda *a:[])
    monkeypatch.setattr(pre,'verify_server_fd',lambda *a:None)
    handlers={}
    def signal_mock(sig,handler):
        old=handlers.get(sig,pre.signal.SIG_DFL);handlers[sig]=handler;return old
    monkeypatch.setattr(pre.signal,'signal',signal_mock)
    stops=[]
    class Server:
        def __init__(self,*a,**k):
            self.done=False;self.record={'pgid':1234,'start_ticks':7}
            self.process=SimpleNamespace(pid=1234,poll=lambda:0 if self.done else None)
        def start(self,**k): pass
        def offload(self,**k): return {'full':True}
        def model_ids(self): return ['qwen25_coder_7b']
        def props(self): return {'model_path':'fake'}
        def stop(self):
            stops.append('stop');handlers[pre.signal.SIGTERM](pre.signal.SIGTERM,None)
            handlers[pre.signal.SIGINT](pre.signal.SIGINT,None);self.done=True
    monkeypatch.setattr(pre,'LlamaServerInstance',Server)
    with pytest.raises(InterruptedError,match='interrupted'):
        pre.run('a'*40,tmp_path/'own')
    assert stops==['stop'] and 'PREFLIGHT_PASS' not in capsys.readouterr().out
    with lock.open('r+') as contender: fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_broken_stderr_does_not_skip_lease_close_or_mask_original(tmp_path,monkeypatch):
    home=tmp_path/'home';(home/'r1_locks').mkdir(parents=True);lock=home/'r1_locks/gpu0.lock';lock.touch()
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:home))
    cfg={'ctx_size':32768,'n_gpu_layers':999,'gpu_uuid':'gpu','server':{'binary':'x','start_timeout':1}}
    spec={'id':'qwen25_coder_7b','runtime':{'model_path':'fake'},'quant_source':{'sha256':'a'*64},'thinking_policy':{}}
    monkeypatch.setattr(pre,'check_inputs',lambda *a:(cfg,spec,{}))
    monkeypatch.setattr(pre,'idle_gpu',lambda *a:{'free_mib':2000})
    monkeypatch.setattr(pre,'template_repair_args',lambda *a:[])
    class FailedServer:
        def __init__(self,*a,**kw): self.process=SimpleNamespace(pid=1234,poll=lambda:None);self.record={'pgid':1234}
        def start(self,**kw): raise RuntimeError('original start failure')
        def stop(self): raise RuntimeError('stop failure')
    class Broken:
        def write(self,*a): raise OSError('stderr unavailable')
        def flush(self): raise OSError('stderr unavailable')
    monkeypatch.setattr(pre,'LlamaServerInstance',FailedServer)
    with monkeypatch.context() as context:
        context.setattr(pre.sys,'stderr',Broken())
        with pytest.raises(RuntimeError,match='original start failure'):
            pre.run('a'*40,tmp_path/'own')
    with lock.open('r+') as contender: fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)


def footprint_fixture(tmp_path, *, model_sha='c'*64, build='build', footprint=1234):
    import hashlib
    import json
    anchor={'id':'qwen25_coder_7b','role':'anchor','quant_source':{'sha256':'a'*64},
            'runtime':{'footprint_mib':'TODO_VERIFY_ON_HOST'}}
    candidate={'id':'candidate','role':'candidate','quant_source':{'sha256':'c'*64},
               'runtime':{'footprint_mib':'TODO_VERIFY_ON_HOST'}}
    registry={'candidates':[anchor,candidate],'software_anchors':[]}
    first=tmp_path/'stagea.json'; amendment=tmp_path/'amendment.json'; acceptance=tmp_path/'acceptance.md'
    first.write_text(json.dumps({'rows':[{'candidate':anchor['id'],'passed':True,'model_sha256':'a'*64,
                                         'build':'build','qualification':{'footprint_mib':5678}}]}))
    amendment.write_text(json.dumps({'label':'ENGINEERING_ONLY','rows':[{'candidate':'candidate','passed':True,
                  'model_sha256':model_sha,'build':build,'qualification':{'footprint_mib':footprint}}]}))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    acceptance.write_text(digest(first)+'\n'+digest(amendment)+'\n')
    cfg={'stage_a_table':str(first),'stage_a_table_sha256':digest(first),
         'stage_a_amendment_table':str(amendment),'stage_a_amendment_table_sha256':digest(amendment),
         'stage_a_amendment_acceptance':str(acceptance),'stage_a_amendment_acceptance_sha256':digest(acceptance),
         'server':{'build':'build'}}
    eligible=pre.stage_a_pass_set(cfg,{'candidate'},v2=True)
    return cfg,registry,eligible,anchor,candidate,first


def test_anchor_and_amendment_candidate_use_real_sha_bound_rows(tmp_path):
    cfg,registry,eligible,anchor,candidate,_=footprint_fixture(tmp_path)
    assert pre.resolve_stage_a_spec(anchor,cfg,registry,eligible)['runtime']['footprint_mib']==5678
    assert pre.resolve_stage_a_spec(candidate,cfg,registry,eligible)['runtime']['footprint_mib']==1234
    assert anchor['runtime']['footprint_mib']=='TODO_VERIFY_ON_HOST'
    assert candidate['runtime']['footprint_mib']=='TODO_VERIFY_ON_HOST'


@pytest.mark.parametrize('changes',[
    {'model_sha':'d'*64}, {'build':'wrong'}, {'footprint':0}, {'footprint':-1},
    {'footprint':float('nan')}, {'footprint':True}, {'footprint':None},
])
def test_stagea_footprint_rejects_wrong_binding_and_invalid_value(tmp_path,changes):
    cfg,registry,eligible,_,candidate,_=footprint_fixture(tmp_path,**changes)
    with pytest.raises(RuntimeError,match='STOP: Stage A'):
        pre.resolve_stage_a_spec(candidate,cfg,registry,eligible)


def test_changed_table_stops_at_observer_recheck(tmp_path):
    cfg,registry,eligible,anchor,_,first=footprint_fixture(tmp_path)
    first.write_text('{"rows": []}')
    with pytest.raises(RuntimeError,match='table digest mismatch'):
        pre.resolve_stage_a_spec(anchor,cfg,registry,eligible)


def test_preflight_rejects_cache_override_and_requires_explicit_false(monkeypatch):
    cfg={'cache_prompt':False,'template_repairs':{}}
    monkeypatch.setenv('LLAMACPP_CACHE_PROMPT','true')
    with pytest.raises(RuntimeError,match='LLAMACPP_CACHE_PROMPT'):
        pre.check_b1_protocol(cfg,[],{})
    monkeypatch.delenv('LLAMACPP_CACHE_PROMPT')
    with pytest.raises(RuntimeError,match='explicitly false'):
        pre.check_b1_protocol({'cache_prompt':None,'template_repairs':{}},[],{})


def test_preflight_applies_actual_template_repair_mapping(monkeypatch):
    monkeypatch.delenv('LLAMACPP_CACHE_PROMPT',raising=False)
    rows=[{'id':'model','template_repair':{'sha256':'a'*64}}]
    with pytest.raises(RuntimeError,match='template_repairs'):
        pre.check_b1_protocol({'cache_prompt':False,'template_repairs':{'model':'b'*64}},rows,{})
    pre.check_b1_protocol({'cache_prompt':False,'template_repairs':{'model':'a'*64}},rows,{})


def test_preflight_stops_batch_for_eligible_switchable_grammar_failure(monkeypatch):
    monkeypatch.delenv('LLAMACPP_CACHE_PROMPT',raising=False)
    rows=[{'id':'model','thinking_policy':{'switchable':True}}]
    cfg={'cache_prompt':False,'template_repairs':{}}
    with pytest.raises(RuntimeError,match='thinking-on sensitivity disabled'):
        pre.check_b1_protocol(cfg,rows,{'model':{'thinking_disabled_due_grammar':True}})
    pre.check_b1_protocol(cfg,rows,{'model':{'thinking_disabled_due_grammar':False}})
    pre.check_b1_protocol(cfg,rows,{})
