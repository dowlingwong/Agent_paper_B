"""Draft false-call wire recorder. Direct use stays behind the D3 STOP gate."""
import hashlib
import base64
import time
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from r1.exam.cache_evidence import validate_chat_cache_evidence
from r1.exam.cache_io import read_chunks
from r1.exam.cache_proc import validate_census_snapshot


class D3EvidenceStop(RuntimeError):
    """Infrastructure evidence failure: never classify it as model parse failure."""


class FalseCallRecorder:
    def __init__(self, url, model, *, census, identity, journal_path):
        from r1.exam.stage_a import require_d3_evidence
        require_d3_evidence()
        self.url=url.rstrip('/');self.model=model;self.census=census;self.identity=identity
        fd=os.open(Path(journal_path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        self.journal=os.fdopen(fd,'w',encoding='utf-8');self.sequence=0

    def close(self): self.journal.close()

    def _write(self, row):
        self.journal.write(json.dumps({**row,'monotonic_ns':time.monotonic_ns()},sort_keys=True,allow_nan=False)+'\n')
        self.journal.flush();os.fsync(self.journal.fileno())

    def _check(self, sample):
        return validate_census_snapshot(sample,self.identity)

    def _sample_now(self):
        from r1.exam.cache_runtime import reject_unverified_lease
        reject_unverified_lease()
        began=time.monotonic_ns();sample=self.census();ended=time.monotonic_ns()
        return validate_census_snapshot(sample,self.identity,earliest_ns=began,latest_ns=ended)

    def _send(self, route, payload):
        self.sequence+=1;seq=self.sequence
        try:
            if payload.get('cache_prompt') is not False: raise ValueError('STOP: false required')
            before=self._sample_now()
            body=json.dumps(payload).encode('utf-8')
            req=Request(self.url+route,data=body,headers={'Content-Type':'application/json'})
            self._write({'event':'request_attempt','sequence':seq,'route':route,'request_body':body.decode(),
                         'request_body_sha256':hashlib.sha256(body).hexdigest(),'census_before':before,
                         'delivery':'unknown'})
            try:
                with urlopen(req,timeout=600) as response:
                    status=response.status
                    self._write({'event':'response_headers','sequence':seq,'http_status':status})
                    raw=read_chunks(response,self._write,sequence=seq)
            except HTTPError as exc:
                self._write({'event':'response_headers','sequence':seq,'http_status':exc.code})
                raw=read_chunks(exc,self._write,sequence=seq)
                self._write({'event':'http_error_response','sequence':seq,'http_status':exc.code,
                             'response_body':raw.decode('utf-8',errors='replace'),
                             'response_body_b64':base64.b64encode(raw).decode('ascii'),
                             'response_body_sha256':hashlib.sha256(raw).hexdigest()})
                raise
            self._write({'event':'response','sequence':seq,'http_status':status,
                         'response_body':raw.decode('utf-8',errors='replace'),
                         'response_body_b64':base64.b64encode(raw).decode('ascii'),
                         'response_body_sha256':hashlib.sha256(raw).hexdigest()})
            reply=json.loads(raw)
            if route=='/v1/chat/completions':
                counts=validate_chat_cache_evidence(reply,first_call=False,cache_prompt=False)
            else:
                timing=reply.get('timings') or {};cached=timing.get('cache_n');processed=timing.get('prompt_n')
                total=reply.get('tokens_evaluated')
                if any(type(x) is not int or x<0 for x in (cached,processed,total)) or cached!=0 or processed!=total or total==0:
                    raise ValueError('STOP: invalid native false cache counts')
                counts={'prompt_tokens_processed':processed,'prompt_tokens_cached':cached,'tokens_evaluated_total':total}
            after=self._sample_now()
            self._write({'event':'checked','sequence':seq,'counts':counts,'census_after':after})
            return reply
        except Exception as exc:
            try:self._write({'event':'stop','sequence':seq,'error':f'{type(exc).__name__}: {exc}'})
            except Exception as log_exc:
                raise D3EvidenceStop(f'STOP: D3 false-call journal unavailable: {type(log_exc).__name__}: {log_exc}') from exc
            raise D3EvidenceStop(f'STOP: D3 false-call evidence failure: {type(exc).__name__}: {exc}') from exc

    def chat(self, prompt, *, max_tokens, seed, extra=None):
        payload={'model':self.model,'messages':[{'role':'user','content':prompt}],
                 'max_tokens':max_tokens,'temperature':0,'seed':seed,**(extra or {})}
        return self._send('/v1/chat/completions',payload)

    def completion(self, payload): return self._send('/completion',payload)
