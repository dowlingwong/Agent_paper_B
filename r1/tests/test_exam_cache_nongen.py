"""Synthetic-only checks; route labels are not deployed binary evidence."""
import base64
import hashlib
import json
import pytest
from r1.exam import cache_nongen
from r1.exam.cache_false import D3EvidenceStop
from r1.tests.exam_census_fixture import fake_census


@pytest.fixture
def rec(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    ident={'pid':1,'process_start_ticks':2,'binary':'/fixture/llama-server'}
    census=lambda:fake_census(ident)
    path=tmp_path/'non-generation.jsonl'
    recorder=cache_nongen.NonGenerationRecorder('http://fixture',census=census,identity=ident,journal_path=path)
    yield recorder,path
    recorder.close()


def test_direct_entry_remains_stop(tmp_path):
    with pytest.raises(RuntimeError,match='cooperative Stage A context not authorized'):
        cache_nongen.NonGenerationRecorder('http://fixture',census=None,identity={},journal_path=tmp_path/'log')
    assert not (tmp_path/'log').exists()


@pytest.mark.parametrize('route',['/tokenize','/apply-template'])
def test_records_non_generation_route_as_unverified(rec,monkeypatch,route):
    recorder,path=rec;requests=[];raw=b'{"tokens":[1]}'
    class Reply:
        status=200
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    def transport(request,timeout):requests.append(request);return Reply()
    monkeypatch.setattr(cache_nongen,'urlopen',transport)
    assert recorder.post(route,{'content':'synthetic'})=={'tokens':[1]}
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert rows[0]['route_classification']=='declared_non_generation_unverified'
    assert rows[0]['delivery']=='unknown' and rows[0]['request_body'].encode()==requests[0].data
    response=next(r for r in rows if r['event']=='response')
    assert base64.b64decode(response['response_body_b64'])==raw
    assert response['response_body_sha256']==hashlib.sha256(raw).hexdigest()


def test_non_generation_rejects_generation_route_before_network(rec,monkeypatch):
    recorder,path=rec;monkeypatch.setattr(cache_nongen,'urlopen',lambda *a,**k:pytest.fail('network'))
    with pytest.raises(D3EvidenceStop,match='route not classified'):
        recorder.post('/completion',{'prompt':'synthetic'})
    assert json.loads(path.read_text())['event']=='stop'


def test_invalid_response_preserved_before_stop(rec,monkeypatch):
    recorder,path=rec;raw=b'\xffsynthetic\x80'
    class Reply:
        status=200
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    monkeypatch.setattr(cache_nongen,'urlopen',lambda *a,**k:Reply())
    with pytest.raises(D3EvidenceStop):recorder.post('/tokenize',{'content':'synthetic'})
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['request_attempt','response_headers','response_chunk','response','stop']
    assert base64.b64decode(rows[3]['response_body_b64'])==raw


def test_journal_full_and_stop_write_full_propagates_evidence_stop(rec,monkeypatch):
    recorder,_=rec
    monkeypatch.setattr(recorder,'_write',lambda row:(_ for _ in ()).throw(OSError(28,'synthetic full disk')))
    monkeypatch.setattr(cache_nongen,'urlopen',lambda *a,**k:pytest.fail('network called'))
    with pytest.raises(D3EvidenceStop,match='journal unavailable'):
        recorder.post('/tokenize',{'content':'synthetic'})


@pytest.fixture(autouse=True)
def synthetic_lease_only(monkeypatch):
    """This module exercises fake HTTP; lease behavior has separate tests."""
    monkeypatch.setattr("r1.exam.cache_runtime.reject_unverified_lease",lambda: None)
