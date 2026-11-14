"""Pure capability bootstrap tests; no kernel capabilities are changed."""
import builtins
import io
import pytest
from r1.c3 import offline_capabilities as cap


def test_capability_drop_order_and_verification(monkeypatch):
    calls=[]
    monkeypatch.setattr(cap.platform,'system',lambda:'Linux')
    monkeypatch.setattr(cap.platform,'machine',lambda:'x86_64')
    monkeypatch.setattr(builtins,'open',lambda *a,**k:io.StringIO('2\n'))
    class Lib:
        def prctl(self,*args):calls.append(('prctl',args));return 0
        def syscall(self,*args):calls.append(('syscall',args[0]));return 0
    monkeypatch.setattr(cap.ctypes,'CDLL',lambda *a,**k:Lib())
    cap.drop_and_verify()
    assert [c[1] for c in calls if c[0]=='syscall']==[126,125]
    drops=[c[1][1] for c in calls if c[0]=='prctl' and c[1][0]==cap.PR_CAPBSET_DROP]
    reads=[c[1][1] for c in calls if c[0]=='prctl' and c[1][0]==cap.PR_CAPBSET_READ]
    assert drops==reads==[0,1,2]


def test_capability_drop_refuses_failure_and_non_linux(monkeypatch):
    monkeypatch.setattr(cap.platform,'system',lambda:'Linux')
    monkeypatch.setattr(cap.platform,'machine',lambda:'x86_64')
    monkeypatch.setattr(builtins,'open',lambda *a,**k:io.StringIO('0'))
    class Lib:
        def prctl(self,*args):return -1
    monkeypatch.setattr(cap.ctypes,'CDLL',lambda *a,**k:Lib())
    with pytest.raises(cap.CapabilityStop,match='ambient'):cap.drop_and_verify()
    monkeypatch.setattr(cap.platform,'system',lambda:'Darwin')
    with pytest.raises(cap.CapabilityStop,match='Linux x86-64'):cap.drop_and_verify()
