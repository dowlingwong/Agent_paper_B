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
            self.record={'start_ticks':7};self.process=None
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
        def __init__(self,*a,**kw): self.process=SimpleNamespace(pid=1234,poll=lambda:None)
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
         'models_dir':str(tmp_path),'dryrun':False}
    anchor={'id':'qwen25_coder_7b','role':'anchor','thinking_policy':{},'runtime':{}}
    registry={'candidates':[anchor],'software_anchors':[]}
    monkeypatch.setattr(pre,'REPO',tmp_path)
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
