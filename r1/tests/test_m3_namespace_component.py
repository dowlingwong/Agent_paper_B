"""Pure namespace setup tests; no real unshare, mount, or child process."""
from pathlib import Path
import pytest
from r1.c3 import offline_namespaces as ns


def fixture(monkeypatch):
    calls=[]
    monkeypatch.setattr(ns.platform,'system',lambda:'Linux')
    monkeypatch.setattr(ns.platform,'machine',lambda:'x86_64')
    monkeypatch.setattr(ns.os,'getuid',lambda:1001)
    monkeypatch.setattr(ns.os,'getgid',lambda:1002)
    monkeypatch.setattr(Path,'iterdir',lambda _:iter([Path('/fixture/thread')]))
    monkeypatch.setattr(ns,'_write_proc',lambda path,data:calls.append(('write',path,data)))
    class Lib:
        def unshare(self,flags): calls.append(('unshare',flags));return 0
        def mount(self,*args): calls.append(('mount',args[3]));return 0
        def prctl(self,*args): calls.append(('prctl',args));return 0
    monkeypatch.setattr(ns,'_libc',lambda:Lib())
    return calls


def test_namespace_setup_sequences_user_mapping_before_other_isolation(monkeypatch):
    calls=fixture(monkeypatch);ns.unshare_bootstrap()
    assert calls==[('unshare',ns.CLONE_NEWUSER),('write','/proc/self/uid_map','0 1001 1\n'),
                   ('write','/proc/self/setgroups','deny\n'),('write','/proc/self/gid_map','0 1002 1\n'),
                   ('unshare',ns.CLONE_NEWNS|ns.CLONE_NEWIPC|ns.CLONE_NEWNET|ns.CLONE_NEWPID),
                   ('mount',ns.MS_REC|ns.MS_PRIVATE)]


def test_mapping_error_stops_before_remaining_namespaces(monkeypatch):
    calls=fixture(monkeypatch)
    def fail(path,data):
        calls.append(('write',path,data))
        if path.endswith('setgroups'):raise PermissionError('fixture')
    monkeypatch.setattr(ns,'_write_proc',fail)
    with pytest.raises(ns.NamespaceStop,match='mappings unavailable'):ns.unshare_bootstrap()
    assert [c[0] for c in calls]==['unshare','write','write']


def test_unshare_refuses_multiple_threads_before_syscalls(monkeypatch):
    calls=fixture(monkeypatch)
    monkeypatch.setattr(Path,'iterdir',lambda _:iter([Path('/a'),Path('/b')]))
    with pytest.raises(ns.NamespaceStop,match='single threaded'):ns.unshare_bootstrap()
    assert calls==[]


def test_parent_death_guard_requires_unchanged_parent(monkeypatch):
    calls=fixture(monkeypatch)
    parents=iter([123,123]);monkeypatch.setattr(ns.os,'getppid',lambda:next(parents))
    ns.parent_death_guard(123);assert calls[0][0]=='prctl'
    parents=iter([123,124])
    with pytest.raises(ns.NamespaceStop,match='changed during setup'):ns.parent_death_guard(123)
