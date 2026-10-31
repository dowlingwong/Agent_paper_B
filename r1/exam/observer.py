"""A4 exam observer, never a controller. One charged query after execution, no outcome input."""
import hashlib
import base64
import os
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from r1.c3.prior_model import parse_typed_answer
from r1.exam.cache_io import read_chunks
from r1.exam.cache_false import D3EvidenceStop


class SelfForecastObserver:
    version = 'exam_self_forecast/v1'
    llm_calls_per_observation = 1

    def __init__(self, base_url=None, model=None, *, llm=None, journal_path=None):
        self.base_url = base_url
        self.model = model
        self.client = llm
        self.journal_path=journal_path
        self._journal=None
        self._sequence=0

    def close(self):
        if self._journal is not None:
            self._journal.close();self._journal=None

    def _append(self,row):
        self._journal.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
        self._journal.flush();os.fsync(self._journal.fileno())

    def _request(self, prompt):
        # Direct invocation cannot bypass the still-unreviewed D3 production gate.
        from r1.exam.stage_a import require_d3_evidence
        require_d3_evidence()
        if not self.journal_path:
            raise D3EvidenceStop('STOP: observer durable journal path required')
        if self._journal is None:
            try:
                fd=os.open(self.journal_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                self._journal=os.fdopen(fd,'w',encoding='utf-8')
            except Exception as exc:
                raise D3EvidenceStop('STOP: observer durable journal unavailable') from exc
        self._sequence+=1
        sequence=self._sequence
        # These fields describe local observations; attempting urlopen does not
        # prove bytes arrived at the server, including when an exception occurs.
        evidence = {'request_constructed': False, 'request_attempted': False,
                    'response_received': False}
        try:
            url = self.base_url.rstrip('/') + '/chat/completions'
            payload = {'model': self.model, 'messages': [{'role': 'user', 'content': prompt}],
                       'max_tokens': 4096, 'temperature': 0.0, 'seed': 0,
                       'cache_prompt': False}
            raw_request = json.dumps(payload).encode()
            request = Request(url, data=raw_request, headers={'Content-Type': 'application/json'})
            evidence.update(request_constructed=True, cache_prompt=False,
                            request_body=raw_request.decode(),
                            request_body_sha256=hashlib.sha256(raw_request).hexdigest())
            self._append({'event':'request_attempt','sequence':sequence,'request_body':raw_request.decode(),
                          'request_body_sha256':hashlib.sha256(raw_request).hexdigest(),'delivery':'unknown'})
            evidence['request_attempted'] = True
            with urlopen(request, timeout=60.0) as response:
                evidence['response_received'] = True
                evidence['http_status'] = response.status
                evidence['response_chunks']=[]
                self._append({'event':'response_headers','sequence':sequence,'http_status':response.status})
                def retain(chunk):
                    self._append({**chunk,'sequence':sequence})
                    evidence['response_chunks'].append(chunk)
                raw_response = read_chunks(response,retain,sequence=sequence)
                evidence['response_body_sha256'] = hashlib.sha256(raw_response).hexdigest()
                evidence['response_body_b64']=base64.b64encode(raw_response).decode('ascii')
                self._append({'event':'response_complete','sequence':sequence,
                              'response_body_sha256':evidence['response_body_sha256']})
            reply = json.loads(raw_response.decode())
            return str(reply['choices'][0]['message']['content']), evidence, None
        except HTTPError as exc:
            evidence.update(response_received=True, http_status=exc.code)
            evidence['response_chunks']=[]
            try:
                self._append({'event':'response_headers','sequence':sequence,'http_status':exc.code})
                def retain(chunk):
                    self._append({**chunk,'sequence':sequence})
                    evidence['response_chunks'].append(chunk)
                raw_error=read_chunks(exc,retain,sequence=sequence)
                evidence['response_body_sha256']=hashlib.sha256(raw_error).hexdigest()
                evidence['response_body_b64']=base64.b64encode(raw_error).decode('ascii')
                self._append({'event':'response_complete','sequence':sequence,
                              'response_body_sha256':evidence['response_body_sha256']})
            except Exception as read_exc:
                evidence['response_read_error']=f'{type(read_exc).__name__}: {read_exc}'
            try:self._append({'event':'stop','sequence':sequence,'error':f'{type(exc).__name__}: {exc}'})
            except Exception as log_exc:
                raise D3EvidenceStop(f'STOP: observer journal unavailable: {type(log_exc).__name__}: {log_exc}') from exc
            failure=D3EvidenceStop(f'STOP: observer HTTP or response evidence failure: {type(exc).__name__}: {exc}')
            failure.evidence=evidence
            raise failure from exc
        except Exception as exc:
            try:self._append({'event':'stop','sequence':sequence,'error':f'{type(exc).__name__}: {exc}'})
            except Exception as log_exc:
                raise D3EvidenceStop(f'STOP: observer journal unavailable: {type(log_exc).__name__}: {log_exc}') from exc
            failure=D3EvidenceStop(f'STOP: observer transport or response evidence failure: {type(exc).__name__}: {exc}')
            failure.evidence=evidence
            raise failure from exc

    def observe(self, proposal, status, node_spec):
        from r1.exam.stage_a import require_d3_evidence
        require_d3_evidence()
        edit=proposal.extra.get('structured_edit') or {'objective':proposal.objective}
        prompt=('You proposed the edit below. Predict its effect without observing its outcome.\n'
                f'Node: {node_spec.name}. Edit: {json.dumps(edit,sort_keys=True)}.\n'
                'Return JSON with "p_no_effect": probability of no effect, "p_positive": probability '
                'of a metric improvement conditional on some effect, and "size": tiny, small, medium, large.\n'
                'No metric outcome is supplied.')
        prompt_sha=hashlib.sha256(prompt.encode()).hexdigest()
        if self.client is not None:
            raise D3EvidenceStop('STOP: injected observer transport is not verified')
        else:
            raw,evidence,error=self._request(prompt)
            if error is not None:
                return {'status':'query_failed','error':error,'prompt_sha256':prompt_sha,
                        'llm_calls':1,'request_evidence':evidence}
        try:
            answer=parse_typed_answer(re.sub(r'<think>.*?</think>\s*','',raw,flags=re.S))
        except Exception as exc:
            return {'status':'query_failed','error':f'{type(exc).__name__}: {exc}',
                    'prompt_sha256':prompt_sha,'llm_calls':1,'request_evidence':evidence}
        return {'status':'ok', 'p_no_effect':answer['p_no_effect'],
                'p_delta_positive':(1-answer['p_no_effect'])*answer['p_positive'],
                'p_positive_given_effect':answer['p_positive'], 'size':answer['size'],
                'raw_answer':raw, 'prompt_sha256':prompt_sha,
                'llm_calls':1,'request_evidence':evidence}
