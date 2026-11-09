"""Supervisor validation tests. No fork, clone, mount, cgroup, model, or network."""
import errno
import json
import os
from pathlib import Path
import pytest
from r1.c3 import offline_bootstrap as boot
from r1.c3 import offline_seccomp as seccomp
from r1.c3 import offline_supervisor as sup


def valid_spec():
    return {'root':'/tmp/private-root','tmpfs_bytes':1048576,
            'closure':[{'source':'/tmp/tool','target':'/runtime/tool','sha256':'0'*64}],
            'work_files':[],'argv':['/runtime/tool'],
            'env':{'HOME':'/work','TMPDIR':'/work','PYTHONDONTWRITEBYTECODE':'1'}}


def test_bootstrap_requires_explicit_closure_and_scrubbed_environment():
    spec=valid_spec();boot.validate_spec(spec)
    with pytest.raises(boot.BootstrapStop,match='unsafe environment'):
        boot.validate_spec({**spec,'env':{**spec['env'],'LD_PRELOAD':'/work/unsafe'}})
    with pytest.raises(boot.BootstrapStop,match='executable missing'):
        boot.validate_spec({**spec,'argv':['/runtime/other']})
    with pytest.raises(boot.BootstrapStop,match='private HOME'):
        boot.validate_spec({**spec,'env':{**spec['env'],'HOME':'/'}})


def test_listener_validation_only_accepts_enoent_for_zero_id():
    def expected(fd,request,payload):raise OSError(errno.ENOENT,'invalid zero ID')
    seccomp.verify_listener(3,ioctl=expected)
    def wrong(fd,request,payload):raise OSError(errno.ENOTTY,'wrong descriptor')
    with pytest.raises(RuntimeError,match='listener verification failed'):seccomp.verify_listener(3,ioctl=wrong)
    with pytest.raises(RuntimeError,match='unexpectedly accepted'):seccomp.verify_listener(3,ioctl=lambda *args:0)


def test_supervisor_refuses_non_linux_before_any_output(tmp_path,monkeypatch):
    monkeypatch.setattr(sup.platform,'system',lambda:'Darwin')
    out=tmp_path/'new'
    with pytest.raises(sup.SupervisorStop,match='Linux x86-64'):
        sup.supervise(valid_spec(),'/not-used',out,protected_roots=[tmp_path])
    assert not out.exists()


def test_durable_record_and_group_population(tmp_path):
    audit=tmp_path/'audit';fd=os.open(audit,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:sup._record(fd,{'event':'fixture'})
    finally:os.close(fd)
    assert '"fixture"' in audit.read_text()
    events=tmp_path/'events';events.write_text('populated 0\n')
    fd=os.open(events,os.O_RDONLY)
    try:
        class Group:events_fd=fd
        assert sup._group_empty(Group())
    finally:os.close(fd)


class _Group:
    def __init__(self,tmp_path,events):
        self.path=tmp_path/'paper-b-m3-fixture';self.kill_fd=91;self.events_fd=92;self.directory_fd=93
        self.events=events
    def kill(self):self.events.append(('killed',))
    def close(self):self.events.append(('group_closed',))


def _mock_supervisor(tmp_path,monkeypatch,events,*,spawn=None,monitor=None):
    """Simulated clone3 flow: no clone, socket, cgroup or kernel call occurs."""
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    original_iterdir=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p: iter([Path('/fake/thread')]) if str(p)=='/proc/self/task' else original_iterdir(p))
    protected=tmp_path/'protected';protected.mkdir()
    monkeypatch.setattr(sup.groups.PrivateCgroup,'create',lambda _:_Group(tmp_path,events))
    class Channel:
        def __init__(self,label):self.label=label
        def close(self):events.append(('closed',self.label))
        def sendall(self,data):events.append(('send',bytes(data)))
        def settimeout(self,t):events.append(('timeout',t))
        def fileno(self):return 17 if self.label=='child' else 16
    monkeypatch.setattr(sup.socket,'socketpair',lambda *a:(Channel('parent'),Channel('child')))
    monkeypatch.setattr(sup.os,'fork',lambda:pytest.fail('the supervisor must never fork'))
    def fake_spawn(cgroup_fd,exe,argv,env,*,stdio,pass_fds):
        events.append(('spawn',cgroup_fd,tuple(pass_fds)))
        assert argv[1:4]==['-I','-S','-B'] and argv[4]==str(sup.BOOTSTRAP_ENTRY)
        assert env=={}
        return 55,81
    monkeypatch.setattr(sup.launcher,'spawn_into_cgroup',spawn or fake_spawn)
    monkeypatch.setattr(sup.launcher,'verify_membership',lambda pid,fd,name:events.append(('membership',pid,fd,name)))
    monkeypatch.setattr(sup.seccomp,'receive_listener',lambda _:events.append(('received',)) or 80)
    monkeypatch.setattr(sup.seccomp,'verify_listener',lambda fd:events.append(('verified',fd)))
    monkeypatch.setattr(sup,'monitor',monitor or (lambda *a,**k:events.append(('monitor',)+a[:3]) or {'status':'COMPLETE_UNQUALIFIED'}))
    monkeypatch.setattr(sup,'_kill_and_reap',lambda *a:events.append(('teardown',)+a))
    real_close=os.close
    monkeypatch.setattr(sup.os,'close',lambda fd:events.append(('closed_fd',fd)) if fd in (80,81) else real_close(fd))
    return protected


def test_mocked_supervisor_clone3_sequence_binds_then_acknowledges(tmp_path,monkeypatch):
    events=[]
    protected=_mock_supervisor(tmp_path,monkeypatch,events)
    result=sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    assert result['status']=='COMPLETE_UNQUALIFIED' and result['withdrawn_drain']=='clean'
    assert ('spawn',93,(17,)) in events
    order=[events.index(e) for e in [('spawn',93,(17,)),('closed','child'),
           ('membership',55,81,'paper-b-m3-fixture'),('send',b'S'),('received',),('verified',80),('send',b'R')]]
    assert order==sorted(order)
    assert events.index(('send',b'R')) < [i for i,e in enumerate(events) if e[0]=='monitor'][0]
    audit=(tmp_path/'output'/'supervisor.jsonl').read_text()
    assert '"creation": "clone3_pidfd_into_cgroup"' in audit and 'spec_sha256' in audit
    bound=json.loads(audit.splitlines()[0])
    assert bound['bootstrap']['interpreter_sha256'] and len(bound['bootstrap']['sources_sha256'])==6
    spec_file=tmp_path/'output'/'bootstrap_spec.json'
    import hashlib
    assert hashlib.sha256(spec_file.read_bytes()).hexdigest() in audit
    assert json.loads(spec_file.read_text())['root']==str(tmp_path/'output'/'root')
    assert ('closed_fd',80) in events and ('closed_fd',81) in events and ('group_closed',) in events


@pytest.mark.parametrize('stage',['spawn','membership','monitor'])
def test_mocked_supervisor_failure_tears_down_by_pidfd(tmp_path,monkeypatch,stage):
    events=[]
    def boom(*a,**k):raise sup.SupervisorStop(f'STOP: fixture {stage}')
    kwargs={'spawn':boom} if stage=='spawn' else {'monitor':boom} if stage=='monitor' else {}
    protected=_mock_supervisor(tmp_path,monkeypatch,events,**kwargs)
    if stage=='membership':
        monkeypatch.setattr(sup.launcher,'verify_membership',boom)
    with pytest.raises(sup.SupervisorStop,match=f'fixture {stage}'):
        sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    teardown=[e for e in events if e[0]=='teardown']
    assert len(teardown)==1
    group,pid,pidfd,waited=teardown[0][1:]
    assert isinstance(group,_Group) and waited is False
    assert (pid,pidfd)==((None,None) if stage=='spawn' else (55,81))
    assert (('send',b'S') in events)==(stage=='monitor')
    assert ('group_closed',) in events


def test_teardown_attempts_pidfd_even_if_cgroup_kill_fails(monkeypatch):
    events=[]
    class Group:
        def kill(self):events.append('group');raise OSError('fixture')
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:events.append('pidfd'),raising=False)
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append('empty'))
    with pytest.raises(sup.SupervisorStop,match='teardown not verified: cgroup kill'):
        sup._kill_and_reap(Group(),55,81,False,wait=lambda fd:events.append(('reaped',fd)) or object())
    assert events==['group','pidfd',('reaped',81),'empty']


def test_teardown_does_not_claim_reap_when_child_identity_is_lost(monkeypatch):
    events=[]
    class Group:
        def kill(self):events.append('group')
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:events.append('pidfd'),raising=False)
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append('empty'))
    monkeypatch.setattr(sup.os,'waitpid',lambda *a:pytest.fail('teardown must never reap by numeric PID'))
    with pytest.raises(sup.SupervisorStop,match='not a waitable child'):
        sup._kill_and_reap(Group(),55,81,False,wait=lambda fd:(_ for _ in ()).throw(ChildProcessError()))
    assert events==['group','pidfd','empty']


def test_teardown_without_pidfd_never_signals_or_reaps_by_number(monkeypatch):
    events=[]
    class Group:
        def kill(self):events.append('group')
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:pytest.fail('no pidfd'),raising=False)
    monkeypatch.setattr(sup.os,'waitpid',lambda *a:pytest.fail('no numeric reap'))
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append('empty'))
    with pytest.raises(sup.SupervisorStop,match='identity unavailable'):
        sup._kill_and_reap(Group(),55,None,False)
    assert events==['group','empty']


def test_pid1_rearms_death_guard_after_capability_drop_before_exec(tmp_path,monkeypatch):
    calls=[];root=tmp_path/'root';root.mkdir();spec=valid_spec();spec['root']=str(root)
    class Channel:
        def fileno(self):return 17
        def close(self):calls.append('channel_close')
    monkeypatch.setattr(boot.ns,'pid_init_parent_guard',lambda fd:calls.append(('guard',fd)))
    monkeypatch.setattr(boot.os,'getpid',lambda:1)
    monkeypatch.setattr(boot.mounts,'create_root',lambda *a:None)
    monkeypatch.setattr(boot.mounts,'mount_closure',lambda *a:None)
    monkeypatch.setattr(boot.mounts,'populate_work',lambda *a:None)
    monkeypatch.setattr(boot.mounts,'mount_pid_proc',lambda *a:None)
    monkeypatch.setattr(Path,'read_text',lambda *a,**k:'NSpid:\t1\n')
    monkeypatch.setattr(boot.os,'chroot',lambda *a:None)
    monkeypatch.setattr(boot.os,'chdir',lambda *a:None)
    monkeypatch.setattr(boot,'close_extra_fds',lambda keep:calls.append(('close_extra',keep)))
    monkeypatch.setattr(boot.caps,'drop_and_verify',lambda:calls.append('caps_dropped'))
    monkeypatch.setattr(boot.seccomp,'install_listener',lambda fd:calls.append('filter') or 19)
    monkeypatch.setattr(boot.seccomp,'send_listener',lambda *a:calls.append('listener_sent'))
    monkeypatch.setattr(boot.os,'close',lambda fd:calls.append(('closed',fd)))
    monkeypatch.setattr(boot.os,'read',lambda *a:b'R')
    monkeypatch.setattr(boot,'require_default_signal_dispositions',lambda:calls.append('signals_checked'))
    class Libc:
        def prctl(self,option,*a):calls.append(('prctl',option));return 0
    monkeypatch.setattr(boot.ctypes,'CDLL',lambda *a,**k:Libc())
    monkeypatch.setattr(boot,'run_workload_as_sentinel',lambda spec,ch:calls.append('sentinel') or 0)
    class StopExit(Exception):pass
    monkeypatch.setattr(boot.os,'_exit',lambda code:(_ for _ in ()).throw(StopExit(code)))
    with pytest.raises(StopExit):boot._pid1(spec,Channel(),18)
    assert calls.count(('guard',18))==2
    assert calls.index('caps_dropped') < max(i for i,v in enumerate(calls) if v==('guard',18)) < calls.index('filter')
    assert calls.index(('closed',18)) < calls.index('filter')
    # PID 1 is non-dumpable and handler-free before the filter, and only then
    # becomes the sentinel that starts the workload.
    assert calls.index('signals_checked') < calls.index(('prctl',boot.PR_SET_DUMPABLE)) < calls.index('filter')
    assert calls.index('listener_sent') < calls.index('sentinel')
