"""D3 scaffolding for non-generation endpoints; production remains STOP.

Endpoint classification is a declared hypothesis only: deployed binary source
and behavior have not been independently checked. These requests run after
the descriptive replay, so they are never relied upon to establish coldness.
"""
import base64
import hashlib
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from r1.exam.cache_false import D3EvidenceStop
from r1.exam.cache_io import read_chunks
from r1.exam.cache_proc import validate_census_snapshot


class NonGenerationRecorder:
    ALLOWED=frozenset({'/tokenize','/apply-template'})

    def __init__(self,url,*,census,identity,journal_path):
        from r1.exam.stage_a import require_d3_evidence
        require_d3_evidence()
        self.url=url.rstrip('/');self.census=census;self.identity=identity;self.sequence=0
        fd=os.open(Path(journal_path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        self.journal=os.fdopen(fd,'w',encoding='utf-8')

    def close(self): self.journal.close()

    def _write(self,row):
        self.journal.write(json.dumps({**row,'monotonic_ns':time.monotonic_ns()},sort_keys=True,allow_nan=False)+'\n')
        self.journal.flush();os.fsync(self.journal.fileno())

    def _check(self,sample):
        return validate_census_snapshot(sample,self.identity)

    def _sample_now(self):
        from r1.exam.cache_runtime import reject_unverified_lease
        reject_unverified_lease()
        began=time.monotonic_ns();sample=self.census();ended=time.monotonic_ns()
        return validate_census_snapshot(sample,self.identity,earliest_ns=began,latest_ns=ended)

    def post(self,route,payload):
        self.sequence+=1;seq=self.sequence
        try:
            if route not in self.ALLOWED: raise ValueError('STOP: route not classified as non-generation')
            before=self._sample_now()
            raw=json.dumps(payload).encode('utf-8')
            request=Request(self.url+route,data=raw,headers={'Content-Type':'application/json'})
            self._write({'event':'request_attempt','sequence':seq,'route':route,
                         'route_classification':'declared_non_generation_unverified',
                         'request_body':raw.decode('utf-8'),'request_body_sha256':hashlib.sha256(raw).hexdigest(),
                         'delivery':'unknown','census_before':before})
            try:
                with urlopen(request,timeout=600) as response:
                    status=response.status
                    self._write({'event':'response_headers','sequence':seq,'http_status':status})
                    body=read_chunks(response,self._write,sequence=seq)
            except HTTPError as exc:
                self._write({'event':'response_headers','sequence':seq,'http_status':exc.code})
                body=read_chunks(exc,self._write,sequence=seq)
                self._write({'event':'http_error_response','sequence':seq,'http_status':exc.code,
                             'response_body_b64':base64.b64encode(body).decode('ascii'),
                             'response_body_sha256':hashlib.sha256(body).hexdigest()})
                raise
            self._write({'event':'response','sequence':seq,'http_status':status,
                         'response_body_b64':base64.b64encode(body).decode('ascii'),
                         'response_body_sha256':hashlib.sha256(body).hexdigest()})
            value=json.loads(body)
            after=self._sample_now()
            self._write({'event':'checked','sequence':seq,'census_after':after})
            return value
        except Exception as exc:
            try:self._write({'event':'stop','sequence':seq,'error':f'{type(exc).__name__}: {exc}'})
            except Exception as log_exc:
                raise D3EvidenceStop(f'STOP: D3 non-generation journal unavailable: {type(log_exc).__name__}: {log_exc}') from exc
            raise D3EvidenceStop(f'STOP: D3 non-generation evidence failure: {type(exc).__name__}: {exc}') from exc
