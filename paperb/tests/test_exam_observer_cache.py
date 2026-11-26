"""HTTP is mocked; these tests do not exercise a server or a real model."""
import hashlib
import base64
import json
from types import SimpleNamespace
import pytest
from r1.exam import observer


def invoke(monkeypatch, transport, tmp_path, *, base='http://fixture/v1'):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr(observer, 'urlopen', transport)
    obj=observer.SelfForecastObserver(base, 'fixture',journal_path=tmp_path/'observer.jsonl')
    try: return obj.observe(SimpleNamespace(extra={}, objective='edit'), None, SimpleNamespace(name='node'))
    finally: obj.close()


def test_request_body_false_and_response_evidence(monkeypatch,tmp_path):
    captured=[]
    raw=json.dumps({'choices':[{'message':{'content':'{"p_no_effect":0.2,"p_positive":0.75,"size":"small"}'}}]}).encode()
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self,size):
            if getattr(self,'read_done',False):return b''
            self.read_done=True;return raw
    def transport(req, timeout):
        captured.append(req.data)
        return Response()
    result=invoke(monkeypatch, transport,tmp_path)
    evidence=result['request_evidence']
    assert result['status']=='ok' and json.loads(captured[0])['cache_prompt'] is False
    assert evidence['request_constructed'] and evidence['request_attempted'] and evidence['response_received']
    assert evidence['http_status']==200 and evidence['cache_prompt'] is False
    assert evidence['request_body']==captured[0].decode()
    assert evidence['request_body_sha256']==hashlib.sha256(captured[0]).hexdigest()
    assert evidence['response_body_sha256']==hashlib.sha256(raw).hexdigest()
    assert base64.b64decode(evidence['response_body_b64'])==raw


def test_failure_before_construction_does_not_claim_call(monkeypatch,tmp_path):
    with pytest.raises(observer.D3EvidenceStop) as failure:
        invoke(monkeypatch, lambda *args, **kwargs: pytest.fail('must not call'),tmp_path, base=None)
    assert failure.value.evidence=={'request_constructed':False,'request_attempted':False,'response_received':False}


def test_connection_failure_records_attempt_without_claiming_delivery(monkeypatch,tmp_path):
    def transport(*args, **kwargs): raise OSError('unreachable fixture')
    with pytest.raises(observer.D3EvidenceStop) as failure:invoke(monkeypatch, transport,tmp_path)
    evidence=failure.value.evidence
    assert evidence['request_constructed'] and evidence['request_attempted']
    assert evidence['cache_prompt'] is False and not evidence['response_received']
    assert 'sent' not in evidence and 'response_body_sha256' not in evidence


def test_injected_llm_stops_without_call(monkeypatch):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    client=lambda _: pytest.fail('injected client invoked')
    with pytest.raises(observer.D3EvidenceStop,match='injected observer transport'):
        observer.SelfForecastObserver(llm=client).observe(SimpleNamespace(extra={}, objective='edit'),None,SimpleNamespace(name='node'))


def test_response_read_failure_records_receipt_without_body(monkeypatch,tmp_path):
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self,size): raise OSError('read failure')
    with pytest.raises(observer.D3EvidenceStop) as failure:invoke(monkeypatch, lambda *args, **kwargs: Response(),tmp_path)
    evidence=failure.value.evidence
    assert evidence['request_attempted'] and evidence['response_received']
    assert 'response_body_sha256' not in evidence


def test_observer_partial_response_chunks_survive_read_error(monkeypatch,tmp_path):
    class Response:
        status=200
        def __init__(self):self.count=0
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):
            self.count+=1
            if self.count==1:return b'partial\xff'
            raise OSError('synthetic interrupted read')
    with pytest.raises(observer.D3EvidenceStop) as failure:invoke(monkeypatch,lambda *a,**k:Response(),tmp_path)
    assert base64.b64decode(failure.value.evidence['response_chunks'][0]['chunk_b64'])==b'partial\xff'
    assert 'response_body_sha256' not in failure.value.evidence
    saved=[json.loads(x) for x in (tmp_path/'observer.jsonl').read_text().splitlines()]
    chunk=next(x for x in saved if x['event']=='response_chunk')
    assert base64.b64decode(chunk['chunk_b64'])==b'partial\xff'
    assert saved[-1]['event']=='stop'


def test_observer_incomplete_read_partial_is_durable(monkeypatch,tmp_path):
    from http.client import IncompleteRead
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,size):raise IncompleteRead(b'0123456789abcdef',32)
    with pytest.raises(observer.D3EvidenceStop):invoke(monkeypatch,lambda *a,**k:Response(),tmp_path)
    saved=[json.loads(x) for x in (tmp_path/'observer.jsonl').read_text().splitlines()]
    chunk=next(x for x in saved if x['event']=='response_chunk')
    assert base64.b64decode(chunk['chunk_b64'])==b'0123456789abcdef'
    assert chunk['from_incomplete_read'] and saved[-1]['event']=='stop'


@pytest.mark.parametrize('status', [400, 503])
def test_http_error_records_received_status_and_body(monkeypatch, status,tmp_path):
    from io import BytesIO
    from urllib.error import HTTPError
    body=b'synthetic error'
    def transport(*args, **kwargs):
        raise HTTPError('http://fixture', status, 'failed', {}, BytesIO(body))
    with pytest.raises(observer.D3EvidenceStop) as failure:invoke(monkeypatch, transport,tmp_path)
    evidence=failure.value.evidence
    assert evidence['request_attempted'] and evidence['response_received']
    assert evidence['http_status']==status
    assert evidence['response_body_sha256']==hashlib.sha256(body).hexdigest()
    assert 'sent' not in evidence


def test_injected_llm_stops_before_access_when_gate_closed():
    client=lambda _: pytest.fail('injected client invoked')
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        observer.SelfForecastObserver(llm=client).observe(SimpleNamespace(extra={}, objective='edit'),None,SimpleNamespace(name='node'))


def test_direct_http_observer_stops_before_base_access_or_network(monkeypatch):
    class NoAccess:
        def __getattribute__(self,name): raise AssertionError('observer accessed')
    monkeypatch.setattr(observer, 'urlopen',lambda *a,**k:pytest.fail('network used'))
    with pytest.raises(RuntimeError,match='D3 cold-cache'):
        observer.SelfForecastObserver._request(NoAccess(),'synthetic')


def test_observer_journal_full_and_stop_write_full_propagates_stop(monkeypatch,tmp_path):
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr(observer,'urlopen',lambda *a,**k:pytest.fail('network called'))
    obj=observer.SelfForecastObserver('http://fixture/v1','fixture',journal_path=tmp_path/'observer.jsonl')
    monkeypatch.setattr(obj,'_append',lambda row:(_ for _ in ()).throw(OSError(28,'synthetic full disk')))
    try:
        with pytest.raises(observer.D3EvidenceStop,match='journal unavailable'):
            obj._request('synthetic')
    finally:obj.close()
