"""Validate B1 observer wire evidence against pinned-harness events."""
import base64
import hashlib
import json
from pathlib import Path


def validate_observer_journal(path, events):
    """Validate every observer request and response; no claim of delivery."""
    calls=[e['payload'] for e in events if e.get('event_type')=='llm_call' and e.get('payload',{}).get('purpose')=='self_forecast']
    path=Path(path)
    if not calls:
        if path.exists() and path.stat().st_size:
            raise RuntimeError('STOP: observer journal without harness calls')
        return {'calls':0,'sha256':None}
    if not path.is_file(): raise RuntimeError('STOP: observer journal missing')
    raw=path.read_bytes()
    rows=[json.loads(line) for line in raw.decode('utf-8').splitlines() if line]
    sequence=[row.get('sequence') for row in rows]
    if any(type(seq) is not int or seq<1 for seq in sequence) or sequence!=sorted(sequence):
        raise RuntimeError('STOP: observer journal calls are not serial')
    by_seq={}
    for row in rows:
        seq=row.get('sequence')
        if type(seq) is not int or seq<1: raise RuntimeError('STOP: invalid observer sequence')
        by_seq.setdefault(seq,[]).append(row)
    if sorted(by_seq)!=list(range(1,len(calls)+1)):
        raise RuntimeError('STOP: observer sequence/count mismatch')
    for i,call in enumerate(calls,1):
        entries=by_seq[i]
        if any(e.get('event')=='stop' for e in entries): raise RuntimeError('STOP: observer journal contains STOP')
        attempts=[e for e in entries if e.get('event')=='request_attempt']
        headers=[e for e in entries if e.get('event')=='response_headers']
        chunks=[e for e in entries if e.get('event')=='response_chunk']
        complete=[e for e in entries if e.get('event')=='response_complete']
        kinds=[e.get('event') for e in entries]
        if len(kinds)<4 or kinds[:2]!=['request_attempt','response_headers'] or kinds[-1]!='response_complete' or any(k!='response_chunk' for k in kinds[2:-1]):
            raise RuntimeError('STOP: observer event order invalid')
        if len(attempts)!=1 or len(headers)!=1 or len(complete)!=1 or headers[0].get('http_status')!=200:
            raise RuntimeError('STOP: incomplete observer request/response')
        attempt=attempts[0]; body=attempt['request_body']; evidence=call.get('request_evidence') or {}
        if hashlib.sha256(body.encode()).hexdigest()!=attempt.get('request_body_sha256'):
            raise RuntimeError('STOP: observer request digest mismatch')
        if json.loads(body).get('cache_prompt') is not False or call.get('cache_prompt') is not False:
            raise RuntimeError('STOP: observer request cache_prompt not false')
        if evidence.get('request_body_sha256')!=attempt['request_body_sha256'] or evidence.get('request_body')!=body:
            raise RuntimeError('STOP: observer event and journal mismatch')
        response=b''
        for k,chunk in enumerate(chunks,1):
            part=base64.b64decode(chunk['chunk_b64'],validate=True)
            if chunk.get('chunk_index')!=k or chunk.get('chunk_bytes')!=len(part) or chunk.get('chunk_sha256')!=hashlib.sha256(part).hexdigest():
                raise RuntimeError('STOP: observer response chunk mismatch')
            response+=part
        if not response or hashlib.sha256(response).hexdigest()!=complete[0].get('response_body_sha256') or evidence.get('response_body_sha256')!=complete[0]['response_body_sha256']:
            raise RuntimeError('STOP: observer response digest mismatch')
    return {'calls':len(calls),'sha256':hashlib.sha256(raw).hexdigest()}
