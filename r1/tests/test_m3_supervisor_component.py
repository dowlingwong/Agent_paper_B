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


def test_mocked_supervisor_sequences_listener_before_workload_ack(tmp_path,monkeypatch):
    # Entire child/cgroup/kernel behavior is simulated; no fork or sockets occur.
    monkeypatch.setattr(sup.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sup.platform,'machine',lambda:'x86_64')
    original_iterdir=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p: iter([Path('/fake/thread')]) if str(p)=='/proc/self/task' else original_iterdir(p))
    protected=tmp_path/'protected';protected.mkdir()
    events=[]
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
    monkeypatch.setattr(sup.os,'waitpid',lambda pid,flags:(55,0))
    monkeypatch.setattr(sup,'_wait_empty',lambda _:events.append(('empty',)))
    class Poll:
        def register(self,*args):pass
        def poll(self,*args):return [(81,sup.select.POLLIN)]
    monkeypatch.setattr(sup.select,'poll',lambda:Poll())
    real_close=os.close
    monkeypatch.setattr(sup.os,'close',lambda fd:events.append(('closed_fd',fd)) if fd in (80,81) else real_close(fd))
    result=sup.supervise(valid_spec(),'/delegated',tmp_path/'output',protected_roots=[protected])
    assert result['status']=='COMPLETE_UNQUALIFIED'
    assert events.index(('bound',55)) < events.index(('send',b'S'))
    assert events.index(('verified',80)) < events.index(('send',b'R'))
    assert ('empty',) in events and ('killed',) not in events


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
