"""Draft D3 true replay; real runner remains blocked pending proof and review."""
import json
import os
import hashlib
import base64
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from r1.exam.cache_evidence import validate_chat_cache_evidence
from r1.exam.cache_io import read_chunks
from r1.exam.cache_proc import validate_census_snapshot


def verify_frozen_binding(prompts, binding):
    from r1.exam.stage_a import load_prompts
    if not isinstance(binding,dict) or not binding.get('path') or not binding.get('sha256'):
        raise ValueError('STOP: missing frozen prompt digest binding')
    verified=load_prompts(binding['path'],binding['sha256'],historical_seeds=True)
    if verified != prompts:
        raise ValueError('STOP: prompts or D26 seeds differ from verified frozen source')


def true_replay(instance, prompts, schema_format, *, census, identity, journal_path, frozen_binding=None):
    """Capture serial descriptive calls; census is observational, not continuous.

    The caller must prove the freshly started server is the intended process and
    this is its first generation call. The caller must not claim a census sample
    proves what occurred between observations. Production gate remains closed.
    """
    from r1.exam.stage_a import require_d3_evidence
    require_d3_evidence()
    verify_frozen_binding(prompts,frozen_binding)
    # The recovered, digest-bound bundle identifies records by trial_id; it
    # has no id field. Do not mutate frozen rows to manufacture an ID.
    ids=[r.get('trial_id') for r in prompts]
    if len(prompts)!=50 or any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=50:
        raise ValueError('STOP: 50 unique prompt trial IDs required')
    if (type(identity.get('pid')) is not int or identity['pid']<=0 or
        type(identity.get('process_start_ticks')) is not int or identity['process_start_ticks']<=0 or
        identity.get('fresh') is not True):
        raise ValueError('STOP: missing fresh server identity')
    path=Path(journal_path)
    # Exclusive creation preserves incomplete attempts; caller decides recovery.
    fd=os.open(path,os.O_WRONLY | os.O_CREAT | os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as journal:
        def append(record):
            try:
                journal.write(json.dumps({**record,'monotonic_ns':time.monotonic_ns()},allow_nan=False,sort_keys=True)+'\n')
                journal.flush();os.fsync(journal.fileno())
            except Exception as exc:
                from r1.exam.cache_false import D3EvidenceStop
                raise D3EvidenceStop(f'STOP: D3 true-call journal unavailable: {type(exc).__name__}: {exc}') from exc
        append({'event':'startup','identity':identity,'scope':'samples immediately before and after each call; gaps unobserved'})
        def sample_now():
            from r1.exam.cache_runtime import reject_unverified_lease
            reject_unverified_lease()
            began=time.monotonic_ns();sample=census();ended=time.monotonic_ns()
            return validate_census_snapshot(sample,identity,earliest_ns=began,latest_ns=ended)
        sequence=0;matched={'free':0,'schema':0};first_prompt_hits=0
        for row in prompts:
            for structured in (False,True):
                messages=[]
                for rep in range(2):
                    sequence+=1
                    try:
                        before=sample_now()
                    except Exception as exc:
                        append({'event':'stop','sequence':sequence,'stage':'census_before',
                                'error':f'{type(exc).__name__}: {exc}'})
                        raise
                    request={'model':instance.alias,'messages':[{'role':'user','content':row['prompt']}],
                             'max_tokens':4096,'temperature':.2,'seed':row['seed'],'cache_prompt':True}
                    if structured: request['response_format']=schema_format
                    try:
                        # Store the exact bytes supplied to urllib, without claiming
                        # they reached the server. A response is recorded separately.
                        wire=json.dumps(request).encode('utf-8')
                        req=Request(instance.url.rstrip('/')+'/v1/chat/completions',data=wire,
                                    headers={'Content-Type':'application/json'})
                        append({'event':'request_attempt','sequence':sequence,'route':'/v1/chat/completions','prompt_id':row['trial_id'],
                                'repeat':rep,'structured':structured,'request_body':wire.decode('utf-8'),
                                'request_body_sha256':hashlib.sha256(wire).hexdigest(),
                                'census_before':before,'delivery':'unknown'})
                        try:
                            with urlopen(req,timeout=600) as response:
                                status=response.status
                                append({'event':'response_headers','sequence':sequence,'http_status':status})
                                raw=read_chunks(response,append,sequence=sequence)
                        except HTTPError as exc:
                            append({'event':'response_headers','sequence':sequence,'http_status':exc.code})
                            raw=read_chunks(exc,append,sequence=sequence)
                            append({'event':'http_error_response','sequence':sequence,'http_status':exc.code,
                                    'response_body':raw.decode('utf-8',errors='replace'),
                                    'response_body_b64':base64.b64encode(raw).decode('ascii'),
                                    'response_body_sha256':hashlib.sha256(raw).hexdigest()})
                            raise
                        append({'event':'response','sequence':sequence,'http_status':status,
                                'response_body':raw.decode('utf-8',errors='replace'),
                                'response_body_b64':base64.b64encode(raw).decode('ascii'),
                                'response_body_sha256':hashlib.sha256(raw).hexdigest()})
                        reply=json.loads(raw)
                        counts=validate_chat_cache_evidence(reply,first_call=sequence==1,cache_prompt=True)
                        # First generation for each distinct prompt, as distinct
                        # from the single first request on the cold server.
                        if not structured and rep==0 and counts['prompt_tokens_cached']>0:
                            first_prompt_hits+=1
                        after=sample_now()
                        append({'event':'checked','sequence':sequence,'cache_counts':counts,'census_after':after})
                        messages.append(reply['choices'][0]['message'])
                    except Exception as exc:
                        append({'event':'stop','sequence':sequence,'error':f'{type(exc).__name__}: {exc}'})
                        raise
                matched['schema' if structured else 'free']+=messages[0]==messages[1]
        result={'event':'true_replay_complete','prompt_count':50,'calls':sequence,'matching':matched,
                'first_prompt_calls':50,'first_prompt_cache_hits':first_prompt_hits,
                'selection_criterion':False}
        append(result)
        return result
