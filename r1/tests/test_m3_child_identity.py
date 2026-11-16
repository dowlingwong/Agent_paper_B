"""Mocks only: no fork, signal mask change, kernel call or remote access."""
import ctypes
from pathlib import Path
import signal

import pytest

from r1.c3 import offline_child_identity as identity


def _mock_guard(monkeypatch, *, handler=0, flags=0, blocked=frozenset({1,2}), threads=1):
    monkeypatch.setattr(identity.platform,'system',lambda:'Linux')
    monkeypatch.setattr(identity.platform,'machine',lambda:'x86_64')
    original=Path.iterdir
    monkeypatch.setattr(Path,'iterdir',lambda p:iter([Path('/fake/thread')]*threads)
                        if str(p)=='/proc/self/task' else original(p))
    monkeypatch.setattr(identity,'blockable_signals',lambda:{1,2})
    monkeypatch.setattr(identity.signal,'pthread_sigmask',lambda action,mask:set(blocked))
    monkeypatch.setattr(identity.signal,'getsignal',lambda sig:signal.SIG_DFL)
    monkeypatch.setattr(identity,'_kernel_sigchld_action',lambda:(handler,flags))


def test_assignment_guard_accepts_explicit_mocked_reapable_case(monkeypatch):
    _mock_guard(monkeypatch)
    identity.require_assignment_guard()


@pytest.mark.parametrize('kwargs,pattern',[
    ({'handler':1},'auto-reap'),
    ({'handler':123456},'handler'),
    ({'flags':identity.SA_NOCLDWAIT},'auto-reap'),
    ({'blocked':{1}},'blocked signal handlers'),
    ({'threads':2},'one supervisor thread'),
])
def test_assignment_guard_refuses_unproved_child_retention(monkeypatch,kwargs,pattern):
    _mock_guard(monkeypatch,**kwargs)
    with pytest.raises(identity.ChildIdentityStop,match=pattern):
        identity.require_assignment_guard()


def test_raw_sigaction_query_layout_and_failure_are_mocked(monkeypatch):
    monkeypatch.setattr(identity.platform,'system',lambda:'Linux')
    monkeypatch.setattr(identity.platform,'machine',lambda:'x86_64')
    calls=[]
    class FakeLibc:
        def syscall(self,nr,signum,new,old,size):
            calls.append((nr,signum,new,size))
            action=ctypes.cast(old,ctypes.POINTER(identity._KernelSigaction)).contents
            action.handler=0;action.flags=identity.SA_NOCLDWAIT
            return 0
    monkeypatch.setattr(identity.ctypes,'CDLL',lambda *a,**k:FakeLibc())
    assert identity._kernel_sigchld_action()==(0,identity.SA_NOCLDWAIT)
    assert calls==[(13,int(signal.SIGCHLD),0,8)]
    monkeypatch.setattr(identity.ctypes,'CDLL',lambda *a,**k:type('Fail',(),{'syscall':lambda *a:-1})())
    with pytest.raises(identity.ChildIdentityStop,match='action unavailable'):
        identity._kernel_sigchld_action()


@pytest.mark.parametrize('action',[lambda *_:None,None])
def test_previously_queued_or_unknown_python_signal_callback_refused(monkeypatch,action):
    _mock_guard(monkeypatch)
    monkeypatch.setattr(identity.signal,'getsignal',lambda _:action)
    with pytest.raises(identity.ChildIdentityStop,match='Python signal callback'):
        identity.require_assignment_guard()
