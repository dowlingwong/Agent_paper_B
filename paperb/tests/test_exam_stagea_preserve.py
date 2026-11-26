"""Stage A STOP preserves synthetic running processes and lock marker."""
from types import SimpleNamespace
import pytest
from r1.exam import runtime
from r1.scripts import llama_server_instance as lsi


def test_close_after_stagea_stop_preserves_service_and_marker(tmp_path):
    runner=runtime.ExamRunner.__new__(runtime.ExamRunner);calls=[]
    marker=tmp_path/'runner.lock';marker.write_text('synthetic')
    runner.service=SimpleNamespace(stop=lambda:calls.append('signal'))
    runner.lock=marker
    runner.close(preserve_running=True)
    assert calls==[] and marker.read_text()=='synthetic' and runner.service is not None


def test_stagea_child_is_not_signalled_on_supervision_stop(tmp_path,monkeypatch):
    runner=runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.state={'phase':'stage-a','interruptions':[]};runner.service=None
    runner.cfg={'root_timeout_seconds':1,'watchdog':{'poll_seconds':0.1},'dryrun':False}
    steps=[]
    def space():
        steps.append('space')
        if len(steps)>1:raise RuntimeError('synthetic disk STOP')
    runner.space=space;runner.save=lambda:None
    child=SimpleNamespace(pid=999,returncode=None,poll=lambda:None,wait=lambda **k:pytest.fail('must not wait'))
    monkeypatch.setattr(runtime.subprocess,'Popen',lambda *a,**k:child)
    monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd',lambda:3)
    monkeypatch.setattr('r1.exam.cache_runtime.reject_unverified_lease',lambda:None)
    monkeypatch.setattr(runtime,'stop_tree',lambda *a:pytest.fail('must not signal'))
    with pytest.raises(RuntimeError,match='synthetic disk STOP'):
        runner.run_job({'out':str(tmp_path/'job')},'fixture')
    assert runner.state['in_progress']['pid']==999 and runner.state['interruptions'][-1]['returncode'] is None


def test_stagea_interrupt_option_stops_before_worker_is_started(tmp_path,monkeypatch):
    runner=runtime.ExamRunner.__new__(runtime.ExamRunner);runner.state={'phase':'stage-a'}
    monkeypatch.setattr(runtime.subprocess,'Popen',lambda *a,**k:pytest.fail('worker started'))
    with pytest.raises(runtime.PreparationStop,match='must not be signalled'):
        runner.run_job({'out':str(tmp_path/'never')},'fixture',interrupt=True)
    assert not (tmp_path/'never').exists()


@pytest.mark.parametrize('preserve,expected_stops',[(True,0),(False,1)])
def test_server_start_timeout_preservation_is_explicit(tmp_path,monkeypatch,preserve,expected_stops):
    model=tmp_path/'model';model.write_bytes(b'synthetic')
    inst=lsi.LlamaServerInstance(tmp_path/'out','/synthetic/binary',model_path=model,
                                 alias='synthetic',port=4242,start_timeout=0)
    proc=SimpleNamespace(pid=999,returncode=None,poll=lambda:None)
    monkeypatch.setattr(lsi,'port_is_free',lambda p:True)
    monkeypatch.setattr(lsi.subprocess,'Popen',lambda *a,**k:proc)
    monkeypatch.setattr(lsi.os,'getpgid',lambda p:999)
    monkeypatch.setattr(lsi,'proc_cmdline',lambda p:['synthetic'])
    signals=[];monkeypatch.setattr(inst,'stop',lambda:signals.append('stop'))
    with pytest.raises(RuntimeError,match='did not become healthy'):
        inst.start(preserve_on_failure=preserve)
    assert len(signals)==expected_stops


@pytest.mark.parametrize('state',[{'status':'STOPPED'},{'status':'STOP'},
                                  {'status':'FAILED'},{'status':'RUNNING','stop_reason':'failure'}])
def test_stopped_batch_never_resumes_or_mutates_state(state):
    before=dict(state)
    with pytest.raises(runtime.PreparationStop,match='must not be resumed'):
        runtime.reject_stopped_batch(state)
    assert state==before


def test_live_stagea_orphan_is_never_signalled(monkeypatch):
    monkeypatch.setattr(runtime.lsi,'orphan_matches',lambda *a:pytest.fail('no takeover'))
    monkeypatch.setattr(runtime.lsi,'stop_orphan',lambda *a:pytest.fail('no signalling'))
    with pytest.raises(runtime.PreparationStop,match='preserve without signalling'):
        runtime.handle_live_orphan({'pid':123},'stage-a')


@pytest.mark.parametrize('name,content',[('batch_state.json','{"status":"RUNNING"}'),
                                         ('runner.lock','{"pid":999}'),('partial.log','partial')])
def test_any_existing_stagea_evidence_is_not_reused_or_modified(tmp_path,name,content):
    out=tmp_path/'attempt';out.mkdir();record=out/name;record.write_text(content)
    with pytest.raises(runtime.PreparationStop,match='cannot be resumed or overwritten'):
        runtime.refuse_existing_stage_a_output(out)
    assert record.read_text()==content and sorted(x.name for x in out.iterdir())==[name]


def test_empty_or_absent_stagea_output_is_acceptable(tmp_path):
    runtime.refuse_existing_stage_a_output(tmp_path/'absent')
    empty=tmp_path/'empty';empty.mkdir();runtime.refuse_existing_stage_a_output(empty)
