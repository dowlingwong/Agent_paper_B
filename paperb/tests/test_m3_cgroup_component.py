"""Synthetic cgroup controls: no real cgroup, child, GPU, network or model."""
import os
from pathlib import Path
import pytest
from r1.c3 import offline_cgroup as cg


def test_create_and_kill_only_new_cgroup(tmp_path,monkeypatch):
    monkeypatch.setattr(cg,'_require_cgroup_v2',lambda _:None)
    real_mkdir=os.mkdir
    def fixture_mkdir(name,mode=0o777,*,dir_fd=None):
        real_mkdir(name,mode,dir_fd=dir_fd)
        if str(name).startswith('paper-b-m3-'):
            directory=tmp_path/str(name)
            (directory/'cgroup.type').write_text('domain\n')
            (directory/'cgroup.procs').write_bytes(b'')
            (directory/'cgroup.kill').write_bytes(b'')
            (directory/'cgroup.events').write_bytes(b'populated 0\n')
    monkeypatch.setattr(os,'mkdir',fixture_mkdir)
    group=cg.PrivateCgroup.create(tmp_path)
    try:
        assert group.path.parent==tmp_path and group.path.name.startswith('paper-b-m3-')
        group.kill()
        assert (group.path/'cgroup.kill').read_bytes()==b'1\n'
    finally: group.close()
    assert group.path.exists()  # retained; never removes a cgroup


def test_membership_only_own_live_child_and_pidfd_retained(tmp_path,monkeypatch):
    group=cg.PrivateCgroup(tmp_path/'paper-b-m3-fixture',-1,11,12)
    records=[];closed=[]
    monkeypatch.setattr(cg.identity,'require_assignment_guard',lambda:None)
    monkeypatch.setattr(os,'pidfd_open',lambda pid,flags:13,raising=False)
    monkeypatch.setattr(os,'P_PIDFD',3,raising=False)
    monkeypatch.setattr(os,'waitid',lambda *args:None,raising=False)
    monkeypatch.setattr(os,'WEXITED',4,raising=False)
    monkeypatch.setattr(os,'WNOWAIT',0x1000000,raising=False)
    monkeypatch.setattr(cg.signal,'pidfd_send_signal',lambda *args:None,raising=False)
    monkeypatch.setattr(os,'write',lambda fd,data:records.append((fd,data)) or len(data))
    monkeypatch.setattr(os,'close',lambda fd:closed.append(fd))
    class Poll:
        def register(self,*args):pass
        def poll(self,*args):return []
    monkeypatch.setattr(cg.select,'poll',lambda:Poll())
    original=Path.read_text
    def read_text(path,*args,**kwargs):
        if str(path)=='/proc/123/cgroup': return '0::/delegated/paper-b-m3-fixture\n'
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',read_text)
    assert group.add_own_child(123)==13
    assert records==[(11,b'123\n')] and closed==[]
    def not_child(*args):raise ChildProcessError('not a child')
    monkeypatch.setattr(os,'waitid',not_child)
    with pytest.raises(cg.CgroupStop,match='ownership'): group.add_own_child(123)
    assert records==[(11,b'123\n')] and closed==[13]


def test_cgroup_refuses_mismatched_membership(tmp_path,monkeypatch):
    group=cg.PrivateCgroup(tmp_path/'paper-b-m3-fixture',-1,11,12)
    closed=[]
    monkeypatch.setattr(cg.identity,'require_assignment_guard',lambda:None)
    monkeypatch.setattr(os,'pidfd_open',lambda pid,flags:13,raising=False)
    monkeypatch.setattr(os,'P_PIDFD',3,raising=False)
    monkeypatch.setattr(os,'waitid',lambda *args:None,raising=False)
    monkeypatch.setattr(os,'WEXITED',4,raising=False)
    monkeypatch.setattr(os,'WNOWAIT',0x1000000,raising=False)
    monkeypatch.setattr(cg.signal,'pidfd_send_signal',lambda *args:None,raising=False)
    monkeypatch.setattr(os,'write',lambda fd,data:len(data))
    monkeypatch.setattr(os,'close',lambda fd:closed.append(fd))
    monkeypatch.setattr(Path,'read_text',lambda *args,**kwargs:'0::/different/group\n')
    class Poll:
        def register(self,*args):pass
        def poll(self,*args):return []
    monkeypatch.setattr(cg.select,'poll',lambda:Poll())
    with pytest.raises(cg.CgroupStop,match='membership'):group.add_own_child(123)
    assert closed==[13]


def test_assignment_rechecks_guard_immediately_before_numeric_pid_write(tmp_path,monkeypatch):
    group=cg.PrivateCgroup(tmp_path/'paper-b-m3-fixture',-1,11,12)
    calls=[]
    def guard():
        calls.append('guard')
        if len(calls)==2:raise cg.identity.ChildIdentityStop('STOP: SIGCHLD changed')
    monkeypatch.setattr(cg.identity,'require_assignment_guard',guard)
    monkeypatch.setattr(os,'pidfd_open',lambda *a:13,raising=False)
    monkeypatch.setattr(os,'P_PIDFD',3,raising=False)
    monkeypatch.setattr(os,'waitid',lambda *a:None,raising=False)
    monkeypatch.setattr(os,'WEXITED',4,raising=False)
    monkeypatch.setattr(os,'WNOWAIT',0x1000000,raising=False)
    monkeypatch.setattr(cg.signal,'pidfd_send_signal',lambda *a:pytest.fail('no assignment attempted'),raising=False)
    monkeypatch.setattr(os,'write',lambda *a:pytest.fail('numeric PID must not be written'))
    closed=[];monkeypatch.setattr(os,'close',lambda fd:closed.append(fd))
    class Poll:
        def register(self,*args):pass
        def poll(self,*args):return []
    monkeypatch.setattr(cg.select,'poll',lambda:Poll())
    with pytest.raises(cg.identity.ChildIdentityStop,match='SIGCHLD changed'):
        group.add_own_child(123)
    assert calls==['guard','guard'] and closed==[13]
