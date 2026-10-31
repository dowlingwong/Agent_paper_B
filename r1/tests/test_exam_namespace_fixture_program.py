"""Static and local synthetic checks; never execute unshare or mount."""
import importlib.util
import json
from pathlib import Path
import pytest


def program():
    path=Path(__file__).resolve().parents[2]/'D3_NAMESPACE_CPU_FIXTURE_DRAFT.py'
    spec=importlib.util.spec_from_file_location('d3_fixture_draft',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_shared_host_mount_namespace_stops_before_mount(tmp_path,monkeypatch):
    m=program();host={'user':1,'net':2,'mnt':3,'pid':4}
    (tmp_path/'manifest.json').write_text(json.dumps({'host_namespaces':host,'tools':{'mount':'/fake/mount','ip':'/fake/ip'}}))
    monkeypatch.setattr(m,'ns',lambda:host)
    monkeypatch.setattr(m,'command',lambda *a,**k:pytest.fail('mount command attempted'))
    with pytest.raises(RuntimeError,match='not distinct'):
        m.role_inner(tmp_path,3,'/fake/mount','/fake/ip',12345)


def test_exclusive_fixture_file_never_overwrites(tmp_path):
    m=program();path=tmp_path/'fixture'
    m.exclusive(path,b'first')
    with pytest.raises(FileExistsError):m.exclusive(path,b'second')
    assert path.read_bytes()==b'first'


def test_explicit_flag_and_direct_tmp_path_are_required(tmp_path,monkeypatch):
    m=program()
    monkeypatch.setattr(m.sys,'argv',['fixture','--out',str(tmp_path/'new')])
    with pytest.raises(RuntimeError,match='explicit synthetic-only flag'):
        m.main()
    assert not (tmp_path/'new').exists()
    monkeypatch.setattr(m.sys,'argv',['fixture','--out','/not-tmp/new','--execute-synthetic-only'])
    with pytest.raises(RuntimeError,match='direct child of /tmp'):
        m.main()


def test_proc_start_ticks_parses_synthetic_stat(tmp_path,monkeypatch):
    # Verify parsing without reading any real process or using procfs.
    m=program()
    raw='123 (synthetic) S '+' '.join(str(i) for i in range(4,24))
    class FakePath:
        def __init__(self,path):pass
        def read_text(self):return raw
    monkeypatch.setattr(m,'Path',FakePath)
    assert m.proc_start_ticks(123)==22


def test_shared_propagation_stops_before_proc_mount(tmp_path,monkeypatch):
    from types import SimpleNamespace
    m=program();host={'user':1,'net':2,'mnt':3,'pid':4}
    (tmp_path/'manifest.json').write_text(json.dumps({'host_namespaces':host,'tools':{'mount':'/fake/mount','ip':'/fake/ip'}}))
    monkeypatch.setattr(m,'ns',lambda:{'user':11,'net':12,'mnt':13,'pid':14})
    monkeypatch.setattr(m.os,'getpid',lambda:1)
    class FakePath:
        def __init__(self,path):pass
        def read_bytes(self):return b'1 2 0:1 / / rw shared:5 - tmpfs tmpfs rw\n'
    monkeypatch.setattr(m,'Path',FakePath)
    commands=[]
    def command(out,label,argv):commands.append(label);return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m,'command',command)
    with pytest.raises(RuntimeError,match='shared mount propagation'):
        m.role_inner(tmp_path,3,'/fake/mount','/fake/ip',12345)
    assert commands==['make_rprivate']


def test_fixture_command_timeout_never_signals_child(tmp_path,monkeypatch):
    m=program()
    class Fake:
        pid=123
        def wait(self,timeout):raise m.subprocess.TimeoutExpired('fixture',timeout)
        def kill(self):pytest.fail('kill called')
        def terminate(self):pytest.fail('terminate called')
    monkeypatch.setattr(m.subprocess,'Popen',lambda *a,**k:Fake())
    with pytest.raises(RuntimeError,match='process preserved'):
        m.command(tmp_path,'synthetic-command',['fixture'])
    saved=json.loads((tmp_path/'synthetic-command.json').read_text())
    assert saved['status']=='STOP_TIMEOUT_PROCESS_PRESERVED' and saved['pid']==123


def test_host_probe_bind_failure_stops_before_any_connection(monkeypatch):
    m=program();calls=[]
    class FakeSocket:
        def settimeout(self,value):pass
        def bind(self,address):calls.append('bind');raise OSError('busy')
        def listen(self,*a):pytest.fail('listen after failed bind')
        def close(self):calls.append('close')
    monkeypatch.setattr(m.socket,'socket',lambda:FakeSocket())
    monkeypatch.setattr(m.socket,'create_connection',lambda *a,**k:pytest.fail('unknown service contacted'))
    with pytest.raises(RuntimeError,match='exclusively bind'):
        m.own_host_listener(12345)
    assert calls==['bind','close']


def test_inner_failure_waits_for_natural_child_exit_without_signal(tmp_path,monkeypatch):
    m=program()
    monkeypatch.setattr(m,'role_inner',lambda *a:(_ for _ in ()).throw(RuntimeError('synthetic stop')))
    calls=[]
    def waitpid(pid,options):
        calls.append((pid,options))
        if len(calls)==1:return (99,0)
        raise ChildProcessError()
    monkeypatch.setattr(m.os,'waitpid',waitpid)
    monkeypatch.setattr(m.os,'kill',lambda *a:pytest.fail('signal attempted'))
    assert m.inner_preserving(tmp_path,3,'/fake/mount','/fake/ip',4)==1
    assert len(calls)==2 and json.loads((tmp_path/'inner_STOP.json').read_text())['waiting_for_children_without_signal']


def test_setns_stage_must_be_denied_not_command_failure():
    from types import SimpleNamespace
    m=program()
    good={'mode':'net','stages':[{'stage':'open_net','rc':0,'errno':0},
                                 {'stage':'setns_net','rc':-1,'errno':1}]}
    assert m.require_denied_setns('net',SimpleNamespace(returncode=0,stdout=json.dumps(good).encode()))==good
    # A command failing after namespace entry is never a setns denial.
    after_entry={'mode':'net','stages':[{'stage':'open_net','rc':0,'errno':0},
                                        {'stage':'setns_net','rc':0,'errno':0}]}
    with pytest.raises(RuntimeError,match='not proven denied'):
        m.require_denied_setns('net',SimpleNamespace(returncode=0,stdout=json.dumps(after_entry).encode()))
    with pytest.raises(RuntimeError,match='could not report'):
        m.require_denied_setns('net',SimpleNamespace(returncode=1,stdout=json.dumps(good).encode()))


def test_user_namespace_entry_success_cannot_be_counted_as_denial():
    from types import SimpleNamespace
    m=program()
    report={'mode':'user-net','stages':[{'stage':'open_user','rc':0,'errno':0},{'stage':'open_net','rc':0,'errno':0},
              {'stage':'setns_user','rc':0,'errno':0},{'stage':'setns_net','rc':-1,'errno':1}]}
    with pytest.raises(RuntimeError,match='not proven denied'):
        m.require_denied_setns('user-net',SimpleNamespace(returncode=0,stdout=json.dumps(report).encode()))


def test_dependency_manifest_digest_and_complete_set_are_required(tmp_path):
    import hashlib
    m=program();path=tmp_path/'deps.json'
    value={'schema':'D3_NAMESPACE_CPU_DEPENDENCIES/v1','fixture_sha256':m.file_digest(m.HERE),'files':{}}
    raw=json.dumps(value).encode();path.write_bytes(raw)
    with pytest.raises(RuntimeError,match='manifest digest mismatch'):
        m.verified_dependencies(path,'0'*64)
    with pytest.raises(RuntimeError,match='dependency set incomplete'):
        m.verified_dependencies(path,hashlib.sha256(raw).hexdigest())


def test_setns_namespace_fd_open_failure_is_not_denial():
    from types import SimpleNamespace
    m=program()
    report={'mode':'net','stages':[{'stage':'open_net','rc':-1,'errno':13}]}
    with pytest.raises(RuntimeError,match='could not report'):
        m.require_denied_setns('net',SimpleNamespace(returncode=2,stdout=json.dumps(report).encode()))


def test_fixture_event_retries_short_writes_and_fails_on_enospc(tmp_path,monkeypatch):
    m=program();written=bytearray()
    def short(fd,data):written.extend(data[:1]);return 1
    monkeypatch.setattr(m.os,'write',short);monkeypatch.setattr(m.os,'fsync',lambda fd:None)
    m.event(tmp_path,'synthetic',payload='ok')
    assert json.loads(bytes(written))['event']=='synthetic'
    calls=[]
    def full(fd,data):
        calls.append(1)
        if len(calls)==1:return 1
        raise OSError(28,'synthetic full disk')
    monkeypatch.setattr(m.os,'write',full)
    with pytest.raises(OSError,match='full disk'):m.event(tmp_path,'fail')
    assert len(calls)==2


def test_final_event_verifier_rejects_truncation_and_out_of_order(tmp_path):
    m=program();path=tmp_path/'events.jsonl'
    events=[{'event':'spawn','monotonic_ns':1,'label':'fake','argv':['fixture']},
            {'event':'spawn_started','monotonic_ns':2,'label':'fake','pid':5},
            {'event':'spawn_finished','monotonic_ns':3,'label':'fake','pid':5,'returncode':0}]
    path.write_text(''.join(json.dumps(x)+'\n' for x in events))
    expected={'spawns':{'fake':{'argv':['fixture'],'pid':5}},'commands':{},'waited':{'fake'}}
    assert m.verify_events(path,**expected)['events']==3
    path.write_text('{"event":"a","monotonic_ns":1}\n{"event":')
    with pytest.raises(RuntimeError,match='incomplete'):m.verify_events(path,**expected)
    events[1]['monotonic_ns']=0;path.write_text(''.join(json.dumps(x)+'\n' for x in events))
    with pytest.raises(RuntimeError,match='order invalid'):m.verify_events(path,**expected)


def test_made_up_or_missing_fixture_events_do_not_qualify(tmp_path):
    m=program();path=tmp_path/'events.jsonl'
    path.write_text('{"event":"made_up","monotonic_ns":1}\n')
    expected={'spawns':{'fake':{'argv':['fixture'],'pid':5}},'commands':{},'waited':{'fake'}}
    with pytest.raises(RuntimeError,match='unexpected fixture event kind'):m.verify_events(path,**expected)
    path.write_text('{"event":"spawn","label":"fake","argv":["fixture"],"monotonic_ns":1}\n')
    with pytest.raises(RuntimeError,match='phases incomplete'):m.verify_events(path,**expected)


def test_fixture_event_wrong_argv_or_pid_is_rejected(tmp_path):
    m=program();path=tmp_path/'events.jsonl'
    events=[{'event':'spawn','monotonic_ns':1,'label':'fake','argv':['other']},
            {'event':'spawn_started','monotonic_ns':2,'label':'fake','pid':6},
            {'event':'spawn_finished','monotonic_ns':3,'label':'fake','pid':6,'returncode':0}]
    expected={'spawns':{'fake':{'argv':['fixture'],'pid':5}},'commands':{},'waited':{'fake'}}
    path.write_text(''.join(json.dumps(x)+'\n' for x in events))
    with pytest.raises(RuntimeError,match='argv mismatch'):m.verify_events(path,**expected)
    events[0]['argv']=['fixture'];path.write_text(''.join(json.dumps(x)+'\n' for x in events))
    with pytest.raises(RuntimeError,match='PID mismatch'):m.verify_events(path,**expected)
