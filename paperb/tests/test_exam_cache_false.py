"""Mocked HTTP only; no model or live service."""
import json
import base64
import hashlib
from types import SimpleNamespace
import pytest
from r1.exam import cache_false
from r1.tests.exam_census_fixture import fake_census


@pytest.fixture
def recorder(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    identity={'pid':5,'process_start_ticks':6,'binary':'/fixture/llama-server'}
    census=lambda:fake_census(identity)
    obj=cache_false.FalseCallRecorder('http://fixture','fixture',census=census,identity=identity,journal_path=tmp_path/'log')
    yield obj,tmp_path/'log'
    obj.close()


def test_direct_construction_remains_blocked(tmp_path):
    with pytest.raises(RuntimeError,match='cooperative Stage A context not authorized'):
        cache_false.FalseCallRecorder('http://fixture','fixture',census=None,identity={},journal_path=tmp_path/'log')
    assert not (tmp_path/'log').exists()


@pytest.mark.parametrize('native', [True,False])
def test_records_wire_body_and_response(recorder,monkeypatch,native):
    obj,path=recorder;requests=[]
    data=({'tokens_evaluated':10,'timings':{'prompt_n':10,'cache_n':0}} if native else
          {'timings':{'prompt_n':10,'cache_n':0},'usage':{'prompt_tokens':10,'prompt_tokens_details':{'cached_tokens':0}}})
    raw=json.dumps(data).encode()
    class Reply:
        status=200
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    def transport(req,timeout): requests.append(req.data);return Reply()
    monkeypatch.setattr(cache_false,'urlopen',transport)
    if native: obj.completion({'prompt':[1,2],'cache_prompt':False})
    else: obj.chat('synthetic',max_tokens=1,seed=1,extra={'cache_prompt':False})
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert json.loads(requests[0])['cache_prompt'] is False
    response=next(r for r in rows if r['event']=='response')
    assert rows[0]['request_body']==requests[0].decode() and response['response_body']==raw.decode()
    assert rows[-1]['event']=='checked' and path.stat().st_mode&0o777==0o600


def test_missing_or_true_setting_stops_before_transport(recorder,monkeypatch):
    obj,path=recorder
    monkeypatch.setattr(cache_false,'urlopen',lambda *a,**k:pytest.fail('must not call'))
    with pytest.raises(cache_false.D3EvidenceStop,match='false required'):
        obj.chat('synthetic',max_tokens=1,seed=1)
    assert json.loads(path.read_text())['event']=='stop'


def test_invalid_utf8_response_retained_byte_exact_before_stop(recorder,monkeypatch):
    obj,path=recorder;raw=b'\xffsynthetic\x80'
    class Reply:
        status=200
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    monkeypatch.setattr(cache_false,'urlopen',lambda *a,**k:Reply())
    with pytest.raises(cache_false.D3EvidenceStop):
        obj.chat('synthetic',max_tokens=1,seed=1,extra={'cache_prompt':False})
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['request_attempt','response_headers','response_chunk','response','stop']
    assert base64.b64decode(rows[3]['response_body_b64'])==raw
    assert rows[3]['response_body_sha256']==hashlib.sha256(raw).hexdigest()


def test_partial_response_chunks_survive_read_error(recorder,monkeypatch):
    obj,path=recorder
    class Reply:
        status=200
        def __init__(self):self.count=0
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            self.count+=1
            if self.count==1:return b'partial\xff'
            raise OSError('synthetic interrupted read')
    monkeypatch.setattr(cache_false,'urlopen',lambda *a,**k:Reply())
    with pytest.raises(cache_false.D3EvidenceStop,match='interrupted read'):
        obj.chat('synthetic',max_tokens=1,seed=1,extra={'cache_prompt':False})
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['request_attempt','response_headers','response_chunk','stop']
    assert base64.b64decode(rows[2]['chunk_b64'])==b'partial\xff'


def test_incomplete_read_partial_survives_in_journal(recorder,monkeypatch):
    from http.client import IncompleteRead
    obj,path=recorder
    class Reply:
        status=200
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):raise IncompleteRead(b'0123456789abcdef',32)
    monkeypatch.setattr(cache_false,'urlopen',lambda *a,**k:Reply())
    with pytest.raises(cache_false.D3EvidenceStop):
        obj.chat('synthetic',max_tokens=1,seed=1,extra={'cache_prompt':False})
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    chunk=next(r for r in rows if r['event']=='response_chunk')
    assert base64.b64decode(chunk['chunk_b64'])==b'0123456789abcdef'
    assert chunk['from_incomplete_read'] and rows[-1]['event']=='stop'


def test_journal_full_and_stop_write_full_propagates_evidence_stop(recorder,monkeypatch):
    obj,_=recorder
    monkeypatch.setattr(obj,'_write',lambda row:(_ for _ in ()).throw(OSError(28,'synthetic full disk')))
    monkeypatch.setattr(cache_false,'urlopen',lambda *a,**k:pytest.fail('network called'))
    with pytest.raises(cache_false.D3EvidenceStop,match='journal unavailable'):
        obj.chat('synthetic',max_tokens=1,seed=1,extra={'cache_prompt':False})


@pytest.fixture(autouse=True)
def synthetic_lease_only(monkeypatch):
    """This module exercises fake HTTP; lease behavior has separate tests."""
    monkeypatch.setattr("r1.exam.cache_runtime.reject_unverified_lease",lambda: None)
