"""Local synthetic HTTP fake only; no model or GPU."""
import json
import io
import base64
import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest
from r1.exam.cache_descriptive import true_replay
from r1.tests.exam_census_fixture import fake_census


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *args:None)
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append(body)
            answer={'choices':[{'message':{'content':'fixed'}}], 'timings':{'prompt_n':10,'cache_n':0},
                    'usage':{'prompt_tokens':10,'prompt_tokens_details':{'cached_tokens':0}}}
            raw=json.dumps(answer).encode();self.send_response(200);self.end_headers();self.wfile.write(raw)
        def log_message(self,*args): pass
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    class Instance:
        alias='fixture'
        url=f'http://127.0.0.1:{server.server_port}'
        def chat(self,prompt,*,max_tokens,seed,extra):
            body={'model':self.alias,'messages':[{'role':'user','content':prompt}],
                  'max_tokens':max_tokens,'temperature':0,'seed':seed,**extra}
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                                 data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})) as r:
                return json.load(r)
    yield Instance(),calls
    server.shutdown();thread.join();server.server_close()


def inputs():
    prompts=[{'trial_id':str(i),'prompt':f'synthetic-{i}','seed':i} for i in range(50)]
    identity={'pid':111,'process_start_ticks':123,'fresh':True,'binary':'/fixture/llama-server'}
    def census(): return fake_census(identity)
    return prompts,identity,census


def test_full_fake_http_replay(fake,tmp_path):
    instance,calls=fake;prompts,identity,census=inputs();path=tmp_path/'journal.jsonl'
    result=true_replay(instance,prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert result['calls']==len(calls)==200 and all(x['cache_prompt'] is True for x in calls)
    assert result['matching']=={'free':50,'schema':50}
    assert result['first_prompt_calls']==50 and result['first_prompt_cache_hits']==0
    assert sum(r['event']=='checked' for r in rows)==200
    assert all(r['delivery']=='unknown' and len(r['request_body_sha256'])==64
               for r in rows if r['event']=='request_attempt')
    assert path.stat().st_mode & 0o777 == 0o600
    assert rows[-1]['selection_criterion'] is False and 'gaps unobserved' in rows[0]['scope']


def test_missing_census_stops_before_request(fake,tmp_path):
    instance,calls=fake;prompts,identity,_=inputs()
    with pytest.raises(RuntimeError,match='STOP'):
        true_replay(instance,prompts,{},census=lambda:None,identity=identity,journal_path=tmp_path/'journal')
    assert calls==[]
    rows=[json.loads(x) for x in (tmp_path/'journal').read_text().splitlines()]
    assert rows[-1]['event']=='stop' and rows[-1]['stage']=='census_before'


def test_invalid_response_retained_before_stop(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *args:None)
    class BadInstance:
        alias='fixture'
        url='http://fixture.invalid'
    class FakeResponse:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return b'{"choices":[{"message":{"content":"x"}}],"usage":{}}'
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',lambda *args,**kwargs:FakeResponse())
    prompts,identity,census=inputs();path=tmp_path/'journal'
    with pytest.raises(ValueError,match='STOP'):
        true_replay(BadInstance(),prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['startup','request_attempt','response_headers','response_chunk','response','stop']


def test_direct_true_replay_is_blocked_before_touching_instance(tmp_path):
    class NoAccess:
        def __getattribute__(self, name): raise AssertionError('instance accessed')
    prompts,identity,census=inputs()
    with pytest.raises(RuntimeError,match='cooperative Stage A context not authorized'):
        true_replay(NoAccess(),prompts,{},census=census,identity=identity,journal_path=tmp_path/'journal')
    assert not (tmp_path/'journal').exists()


def test_duplicate_trial_id_stops_before_network(fake,tmp_path):
    instance,calls=fake;prompts,identity,census=inputs()
    prompts[-1]['trial_id']=prompts[0]['trial_id']
    with pytest.raises(ValueError,match='unique prompt trial IDs'):
        true_replay(instance,prompts,{},census=census,identity=identity,journal_path=tmp_path/'journal')
    assert calls==[] and not (tmp_path/'journal').exists()


def test_http_error_response_is_recorded_before_stop(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *args:None)
    class Instance:
        alias='fixture'
        url='http://fixture.invalid'
    def fail(request,**kwargs):
        raise HTTPError(request.full_url,429,'fake',{},io.BytesIO(b'{"error":"synthetic"}'))
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',fail)
    prompts,identity,census=inputs();path=tmp_path/'journal'
    with pytest.raises(HTTPError):
        true_replay(Instance(),prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['startup','request_attempt','response_headers','response_chunk','http_error_response','stop']
    assert rows[4]['http_status']==429 and len(rows[4]['response_body_sha256'])==64


def test_true_invalid_utf8_response_retained_byte_exact_before_stop(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *args:None)
    class Instance:
        alias='fixture';url='http://fixture.invalid'
    raw=b'\xffsynthetic\x80'
    class Reply:
        status=200
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',lambda *a,**k:Reply())
    prompts,identity,census=inputs();path=tmp_path/'journal'
    with pytest.raises(UnicodeDecodeError):
        true_replay(Instance(),prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['startup','request_attempt','response_headers','response_chunk','response','stop']
    assert base64.b64decode(rows[4]['response_body_b64'])==raw
    assert rows[4]['response_body_sha256']==hashlib.sha256(raw).hexdigest()


def test_true_partial_response_chunks_survive_read_error(tmp_path,monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *args:None)
    class Instance:alias='fixture';url='http://fixture.invalid'
    class Reply:
        status=200
        def __init__(self):self.count=0
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            self.count+=1
            if self.count==1:return b'partial\xff'
            raise OSError('synthetic interrupted read')
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',lambda *a,**k:Reply())
    prompts,identity,census=inputs();path=tmp_path/'journal'
    with pytest.raises(OSError,match='interrupted read'):
        true_replay(Instance(),prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert [r['event'] for r in rows]==['startup','request_attempt','response_headers','response_chunk','stop']
    assert base64.b64decode(rows[3]['chunk_b64'])==b'partial\xff'


def test_true_incomplete_read_partial_survives(tmp_path,monkeypatch):
    from http.client import IncompleteRead
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *a,**k:None)
    class Instance:alias='fixture';url='http://fixture.invalid'
    class Reply:
        status=200
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):raise IncompleteRead(b'0123456789abcdef',32)
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',lambda *a,**k:Reply())
    prompts,identity,census=inputs();path=tmp_path/'journal'
    with pytest.raises(IncompleteRead):
        true_replay(Instance(),prompts,{},census=census,identity=identity,journal_path=path)
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    chunk=next(r for r in rows if r['event']=='response_chunk')
    assert base64.b64decode(chunk['chunk_b64'])==b'0123456789abcdef'
    assert chunk['from_incomplete_read'] and rows[-1]['event']=='stop'


def test_true_journal_full_is_evidence_stop_before_network(tmp_path,monkeypatch):
    from r1.exam.cache_false import D3EvidenceStop
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.verify_frozen_binding',lambda *a,**k:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.os.fsync',lambda *a:(_ for _ in ()).throw(OSError(28,'synthetic full disk')))
    monkeypatch.setattr('r1.exam.cache_descriptive.urlopen',lambda *a,**k:pytest.fail('network called'))
    class Instance:alias='fixture';url='http://fixture.invalid'
    prompts,identity,census=inputs()
    with pytest.raises(D3EvidenceStop,match='journal unavailable'):
        true_replay(Instance(),prompts,{},census=census,identity=identity,journal_path=tmp_path/'journal')


def test_verified_binding_rejects_modified_prompt_or_seed(monkeypatch):
    from r1.exam.cache_descriptive import verify_frozen_binding
    prompts,_,_=inputs()
    monkeypatch.setattr('r1.exam.stage_a.load_prompts',lambda *args,**kwargs:prompts)
    different=[dict(x) for x in prompts];different[0]['seed']+=1
    with pytest.raises(ValueError,match='D26 seeds differ'):
        verify_frozen_binding(different,{'path':'fixture','sha256':'fixture'})
    with pytest.raises(ValueError,match='digest binding'):
        verify_frozen_binding(prompts,None)


@pytest.fixture(autouse=True)
def synthetic_lease_only(monkeypatch):
    """This module exercises fake HTTP; lease behavior has separate tests."""
    monkeypatch.setattr("r1.exam.cache_runtime.reject_unverified_lease",lambda: None)
