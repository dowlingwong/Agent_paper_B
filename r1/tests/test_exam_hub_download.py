"""Receiving and child-stop regressions; fake bytes only, no network."""
import hashlib
import json
from pathlib import Path
import pytest
from r1.exam import hub_download as hub


def spec(root):
    data=b'pinned fixture';target=root/'x/model.gguf';target.parent.mkdir();target.write_bytes(data)
    return {'id':'x','base_repo':'vendor/x','vendor_q4_available':True,'runtime':{'model_path':str(target)},
            'quant_source':{'kind':'vendor','repo':'vendor/x-GGUF','file':'model.gguf','revision':'0'*40,
                            'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'quantization':'Q4_K_M'}}


def test_hub_receiving_checks_reused_bytes_and_preserves_bad_data(tmp_path,monkeypatch):
    monkeypatch.setattr(hub,'ROOT',tmp_path);s=spec(tmp_path)
    result=hub.receive_one(s,tmp_path/'reports',check_space=lambda p:{'available_bytes':100_000_000_000})
    assert result['result']['reused'] and result['result']['sha256']==s['quant_source']['sha256']
    target=Path(s['runtime']['model_path']);target.write_bytes(b'changed bytes!')
    with pytest.raises(RuntimeError,match='mismatch'):hub.receive_one(s,tmp_path/'reports',check_space=lambda p:{})
    assert target.read_bytes()==b'changed bytes!'


def test_hub_disk_stop_signals_only_owned_child_group(tmp_path,monkeypatch):
    monkeypatch.setattr(hub,'ROOT',tmp_path);s=spec(tmp_path);Path(s['runtime']['model_path']).unlink()
    class Child:
        pid=123456
        def poll(self):return None
        def wait(self,timeout=None):return 0
    monkeypatch.setattr(hub.subprocess,'Popen',lambda *a,**k:Child())
    signals=[];monkeypatch.setattr(hub.os,'killpg',lambda pid,sig:signals.append((pid,sig)))
    calls=[]
    def space(p):
        calls.append(p)
        if len(calls)>1:raise RuntimeError('STOP: below 100 GB')
        return {}
    with pytest.raises(RuntimeError,match='100 GB'):hub.receive_one(s,tmp_path/'reports',check_space=space)
    assert signals==[(123456,hub.signal.SIGTERM)]
    assert not Path(s['runtime']['model_path']).exists()


def test_cohort_stop_prevents_queued_artifact_launch(tmp_path,monkeypatch):
    started=[]
    def receive(s,out,*,check_space,cancel):
        started.append(s['id'])
        assert cancel is not None
        raise RuntimeError('STOP: pinned source mismatch')
    monkeypatch.setattr(hub,'receive_one',receive)
    with pytest.raises(RuntimeError,match='source mismatch'):
        hub.run_downloads([{'id':str(i)} for i in range(8)],tmp_path)
    assert started==['0']
    assert json.loads((tmp_path/'transport_stop.json').read_text())['status']=='STOPPED'


def test_shared_cancellation_terminates_active_owned_child(tmp_path,monkeypatch):
    import threading
    monkeypatch.setattr(hub,'ROOT',tmp_path);s=spec(tmp_path);Path(s['runtime']['model_path']).unlink()
    cancel=threading.Event()
    class Child:
        pid=123456
        def poll(self):cancel.set();return None
        def wait(self,timeout=None):return 0
    monkeypatch.setattr(hub.subprocess,'Popen',lambda *a,**k:Child())
    signals=[];monkeypatch.setattr(hub.os,'killpg',lambda pid,sig:signals.append((pid,sig)))
    with pytest.raises(InterruptedError,match='cancelled'):
        hub.receive_one(s,tmp_path/'reports',check_space=lambda p:{},cancel=cancel)
    assert signals==[(123456,hub.signal.SIGTERM)]
