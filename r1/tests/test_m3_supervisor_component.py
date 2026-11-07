"""Supervisor validation tests. No fork, mount, cgroup, model, or network."""
import errno
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


@pytest.mark.parametrize('listener_error',['none','error','pending_hup','pidfd_error','pidfd_hup',
                                           'pidfd_invalid','pidfd_premature','listener_invalid'])
def test_mocked_supervisor_sequences_listener_before_workload_ack(tmp_path,monkeypatch,listener_error):
    # Entire child/cgroup/kernel behavior is simulated; no fork or sockets occur.
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    monkeypatch.setattr(sup.identity,'blockable_signals',lambda:{1,2})
    monkeypatch.setattr(sup.identity,'require_assignment_guard',lambda:None)
    original_iterdir=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p: iter([Path('/fake/thread')]) if str(p)=='/proc/self/task' else original_iterdir(p))
    protected=tmp_path/'protected';protected.mkdir()
    events=[]
    monkeypatch.setattr(sup.signal,'pthread_sigmask',
                        lambda action,mask: events.append(('mask',action,set(mask))) or {2})
    class Group:
        path=tmp_path/'group';kill_fd=91;events_fd=92
        def add_own_child(self,pid):events.append(('bound',pid));return 81
        def kill(self):events.append(('killed',))
        def close(self):events.append(('group_closed',))
    monkeypatch.setattr(sup.groups.PrivateCgroup,'create',lambda _:Group())
    class Channel:
        def __init__(self,label):self.label=label
        def close(self):events.append(('closed',self.label))
        def sendall(self,data):events.append(('send',bytes(data)))
        def settimeout(self,t):events.append(('timeout',t))
    monkeypatch.setattr(sup.socket,'socketpair',lambda *a:(Channel('parent'),Channel('child')))
    monkeypatch.setattr(sup.os,'fork',lambda:55)
    monkeypatch.setattr(sup.seccomp,'receive_listener',lambda _:events.append(('received',)) or 80)
    monkeypatch.setattr(sup.seccomp,'verify_listener',lambda fd:events.append(('verified',fd)))
    waits=[]
    def fake_waitpid(pid,flags):
        waits.append(flags)
        if listener_error=='pidfd_premature' and len(waits)==1:return (0,0)
        return (55,0)
    monkeypatch.setattr(sup.os,'waitpid',fake_waitpid)
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append(('empty',)))
    class Poll:
        def register(self,*args):pass
        def poll(self,*args):
            if listener_error=='error':return [(80,sup.select.POLLERR),(81,sup.select.POLLIN)]
            if listener_error=='pending_hup':return [(80,sup.select.POLLIN|sup.select.POLLHUP),(81,sup.select.POLLIN)]
            if listener_error=='pidfd_error':return [(81,sup.select.POLLERR|sup.select.POLLIN)]
            if listener_error=='pidfd_hup':return [(81,sup.select.POLLHUP)]
            if listener_error=='pidfd_invalid':return [(81,sup.select.POLLNVAL)]
            if listener_error=='listener_invalid':return [(80,sup.select.POLLNVAL),(81,sup.select.POLLIN)]
            return [(81,sup.select.POLLIN)]
    monkeypatch.setattr(sup.select,'poll',lambda:Poll())
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:events.append(('pidfd_signal',)),raising=False)
    monkeypatch.setattr(sup.seccomp,'monitor_one',lambda *a:events.append(('durable_violation',)) or {'syscall':42})
    real_close=os.close
    monkeypatch.setattr(sup.os,'close',lambda fd:events.append(('closed_fd',fd)) if fd in (80,81) else real_close(fd))
    if listener_error!='none':
        if listener_error=='pending_hup':expected='prohibited syscall'
        elif listener_error=='pidfd_premature':expected='pidfd readiness did not yield'
        elif listener_error.startswith('pidfd_'):expected='pidfd error or hangup'
        else:expected='listener error or hangup'
        with pytest.raises(sup.SupervisorStop,match=expected):
            sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
        assert ('killed',) in events
        assert (('durable_violation',) in events)==(listener_error=='pending_hup')
    else:
        result=sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
        assert result['status']=='COMPLETE_UNQUALIFIED'
    assert events.index(('bound',55)) < events.index(('send',b'S'))
    assert events.index(('mask',sup.signal.SIG_BLOCK,{1,2})) < events.index(('bound',55))
    assert events.index(('bound',55)) < events.index(('mask',sup.signal.SIG_SETMASK,{2})) < events.index(('send',b'S'))
    assert events.index(('verified',80)) < events.index(('send',b'R'))
    assert ('empty',) in events
    assert all(flags==sup.os.WNOHANG for flags in waits)


def test_teardown_attempts_pidfd_even_if_cgroup_kill_fails(monkeypatch):
    events=[]
    class Group:
        def kill(self):events.append('group');raise OSError('fixture')
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:events.append('pidfd'),raising=False)
    monkeypatch.setattr(sup.os,'waitpid',lambda *a:(55,0))
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append('empty'))
    with pytest.raises(sup.SupervisorStop,match='teardown not verified'):
        sup._kill_and_reap(Group(),55,81,False)
    assert events==['group','pidfd','empty']


def test_teardown_does_not_claim_reap_when_child_identity_is_lost(monkeypatch):
    events=[]
    class Group:
        def kill(self):events.append('group')
    monkeypatch.setattr(sup.signal,'pidfd_send_signal',lambda *a:events.append('pidfd'),raising=False)
    monkeypatch.setattr(sup.os,'waitpid',lambda *a:(_ for _ in ()).throw(ChildProcessError()))
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append('empty'))
    with pytest.raises(sup.SupervisorStop,match='not a waitable child'):
        sup._kill_and_reap(Group(),55,81,False)
    assert events==['group','pidfd','empty']


def test_signal_mask_restored_when_guard_rejects_before_fork(tmp_path,monkeypatch):
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    original=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p:iter([Path('/fake/thread')])
                        if str(p)=='/proc/self/task' else original(p))
    protected=tmp_path/'protected';protected.mkdir()
    calls=[]
    class Group:
        def close(self):calls.append('group_closed')
    class Channel:
        def close(self):calls.append('channel_closed')
    monkeypatch.setattr(sup.groups.PrivateCgroup,'create',lambda _:Group())
    monkeypatch.setattr(sup.socket,'socketpair',lambda *a:(Channel(),Channel()))
    monkeypatch.setattr(sup.identity,'blockable_signals',lambda:{1,2})
    monkeypatch.setattr(sup.identity,'require_assignment_guard',
                        lambda:(_ for _ in ()).throw(sup.identity.ChildIdentityStop('guard refused')))
    monkeypatch.setattr(sup.signal,'pthread_sigmask',lambda op,mask:calls.append((op,set(mask))) or {2})
    monkeypatch.setattr(sup.os,'fork',lambda:pytest.fail('guard must precede fork'))
    monkeypatch.setattr(sup,'_kill_and_reap',lambda *a:calls.append('cleanup'))
    with pytest.raises(sup.identity.ChildIdentityStop,match='guard refused'):
        sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    assert calls.index((sup.signal.SIG_BLOCK,{1,2})) < calls.index('cleanup')
    assert calls.index('cleanup') < calls.index((sup.signal.SIG_SETMASK,{2}))
    assert 'group_closed' in calls


def test_restore_failure_stops_before_bootstrap_ack_and_closes(tmp_path,monkeypatch):
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    original=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p:iter([Path('/fake/thread')])
                        if str(p)=='/proc/self/task' else original(p))
    protected=tmp_path/'protected';protected.mkdir();calls=[]
    class Group:
        def add_own_child(self,pid):calls.append('assigned');return 81
        def close(self):calls.append('group_closed')
    class Channel:
        def close(self):calls.append('channel_closed')
        def sendall(self,data):pytest.fail('no bootstrap acknowledgement on restore failure')
    monkeypatch.setattr(sup.groups.PrivateCgroup,'create',lambda _:Group())
    monkeypatch.setattr(sup.socket,'socketpair',lambda *a:(Channel(),Channel()))
    monkeypatch.setattr(sup.identity,'blockable_signals',lambda:{1,2})
    monkeypatch.setattr(sup.identity,'require_assignment_guard',lambda:None)
    def mask(op,value):
        calls.append((op,set(value)))
        if op==sup.signal.SIG_SETMASK:raise OSError('fixture restore')
        return {2}
    monkeypatch.setattr(sup.signal,'pthread_sigmask',mask)
    monkeypatch.setattr(sup.os,'fork',lambda:55)
    monkeypatch.setattr(sup,'_kill_and_reap',lambda *a:calls.append('cleanup'))
    real_close=os.close
    monkeypatch.setattr(sup.os,'close',lambda fd:calls.append(('closed_fd',fd)) if fd==81 else real_close(fd))
    with pytest.raises(sup.SupervisorStop,match='mask restoration failed'):
        sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    assert 'assigned' in calls and 'cleanup' in calls and 'group_closed' in calls
    assert ('closed_fd',81) in calls


def test_mocked_child_restores_original_mask_before_bootstrap(tmp_path,monkeypatch):
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    original=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p:iter([Path('/fake/thread')])
                        if str(p)=='/proc/self/task' else original(p))
    protected=tmp_path/'protected';protected.mkdir();calls=[]
    class Group:
        def close(self):calls.append('group_closed')
    class Channel:
        def close(self):calls.append('channel_closed')
        def fileno(self):return 17
    monkeypatch.setattr(sup.groups.PrivateCgroup,'create',lambda _:Group())
    monkeypatch.setattr(sup.socket,'socketpair',lambda *a:(Channel(),Channel()))
    monkeypatch.setattr(sup.identity,'blockable_signals',lambda:{1,2})
    monkeypatch.setattr(sup.identity,'require_assignment_guard',lambda:None)
    monkeypatch.setattr(sup.signal,'pthread_sigmask',lambda op,mask:calls.append((op,set(mask))) or {2})
    monkeypatch.setattr(sup.os,'fork',lambda:0)
    monkeypatch.setattr(sup.os,'dup2',lambda *a:None)
    monkeypatch.setattr(sup.boot,'bootstrap_child',lambda *a:calls.append('bootstrap'))
    class FakeChildExit(BaseException):pass
    monkeypatch.setattr(sup.os,'_exit',lambda _:(_ for _ in ()).throw(FakeChildExit()))
    monkeypatch.setattr(sup,'_kill_and_reap',lambda *a:None)
    with pytest.raises(FakeChildExit):
        sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    assert calls.index((sup.signal.SIG_SETMASK,{2})) < calls.index('bootstrap')


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
    class StopExec(Exception):pass
    monkeypatch.setattr(boot.os,'execve',lambda *a:(_ for _ in ()).throw(StopExec()))
    with pytest.raises(StopExec):boot._pid1(spec,Channel(),18)
    assert calls.count(('guard',18))==2
    assert calls.index('caps_dropped') < max(i for i,v in enumerate(calls) if v==('guard',18)) < calls.index('filter')
    assert calls.index(('closed',18)) < calls.index('filter')
