"""Internal journal ordering checks; cannot prove host-wide request exclusion.

These checks only audit records produced by this worker. They cannot observe
other processes, prove freshness, or establish a GPU flock. Production remains
behind the independent cold/lease STOP gates.
"""
import hashlib
import base64
import json
from r1.exam.cache_evidence import validate_chat_cache_evidence
from r1.exam.cache_proc import validate_census_snapshot


def _nongen_expected_rows(thinking_enabled,nongen_expected=None):
    rows=[('/tokenize',{'content':'a ','add_special':True})]
    if nongen_expected is None:
        for i in range(5):
            messages=[{'role':'user','content':f'Fixed template check {i}: JSON, whitespace, Unicode α, newline\nend.'}]
            rows.append(('/apply-template',{'messages':messages,'add_generation_prompt':True,
                                            'chat_template_kwargs':{'enable_thinking':thinking_enabled}}))
    else:
        for route,payload in nongen_expected:
            rows.append((str(route),payload))
    return rows


def validate_local_order(true_rows,false_rows,nongen_rows,prompts,*,alias,ctx_size,schema_format,expect_grammar,thinking_enabled,identity,nongen_expected=None):
    def fail(reason):raise ValueError('STOP: D3 local journal '+reason)
    expected_non_generation=_nongen_expected_rows(thinking_enabled,nongen_expected)
    nongen_required=len(expected_non_generation)
    def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    def timestamps(rows):
        times=[r.get('monotonic_ns') for r in rows]
        if any(type(t) is not int or t<0 for t in times) or any(b<=a for a,b in zip(times,times[1:])):
            fail('missing or nonmonotonic timestamps')
        if any(r.get('event')=='stop' for r in rows):fail('contains STOP')
        return times
    for rows in (true_rows,false_rows,nongen_rows):timestamps(rows)
    expected={r.get('trial_id'):r for r in prompts}
    if len(prompts)!=50 or len(expected)!=50 or any(not isinstance(x,str) or not x for x in expected):
        fail('prompt IDs invalid')
    if not isinstance(alias,str) or not alias or type(ctx_size) is not int or ctx_size<2 or not isinstance(schema_format,dict) or type(expect_grammar) is not bool or type(thinking_enabled) is not bool:
        fail('frozen replay settings invalid')
    if (not isinstance(identity,dict) or type(identity.get('pid')) is not int or identity['pid']<=0 or
        type(identity.get('process_start_ticks')) is not int or identity['process_start_ticks']<=0 or
        not isinstance(identity.get('binary'),str) or not identity['binary']):
        fail('server identity invalid')
    def verify_census(sample):
        try:validate_census_snapshot(sample,identity)
        except RuntimeError:fail('server census or identity mismatch')
    startup=[r for r in true_rows if r.get('event')=='startup']
    if len(startup)!=1 or canonical(startup[0].get('identity'))!=canonical(identity):fail('startup identity mismatch')
    by_prompt={r.get('prompt'):r for r in prompts}
    if len(by_prompt)!=50 or any(not isinstance(p,str) or not p for p in by_prompt):
        fail('prompt text identities invalid')
    attempts=[r for r in true_rows if r.get('event')=='request_attempt']
    checks=[r for r in true_rows if r.get('event')=='checked']
    responses=[r for r in true_rows if r.get('event')=='response']
    completed=[r for r in true_rows if r.get('event')=='true_replay_complete']
    if len(attempts)!=200 or len(checks)!=200 or len(responses)!=200 or len(completed)!=1:
        fail('true run incomplete')
    if completed[0].get('calls')!=200 or completed[0].get('prompt_count')!=50 or completed[0].get('selection_criterion') is not False:
        fail('true completion summary invalid')
    seq=[r.get('sequence') for r in attempts]
    if seq!=list(range(1,201)) or [r.get('sequence') for r in checks]!=seq or [r.get('sequence') for r in responses]!=seq:
        fail('true request/check sequence invalid')
    schedule=[(row['trial_id'],structured,repeat) for row in prompts for structured in (False,True) for repeat in (0,1)]
    if [(r.get('prompt_id'),r.get('structured'),r.get('repeat')) for r in attempts]!=schedule:
        fail('true prompt/mode/repeat schedule invalid')
    def response_bytes(row):
        try:raw=base64.b64decode(row['response_body_b64'],validate=True)
        except (KeyError,ValueError,TypeError):fail('response bytes missing or malformed')
        if hashlib.sha256(raw).hexdigest()!=row.get('response_body_sha256') or row.get('http_status')!=200:
            fail('response digest or HTTP status invalid')
        return raw
    first_prompt_hits=0;messages_by_key={}
    for i,(request,response,check) in enumerate(zip(attempts,responses,checks)):
        if i and request['monotonic_ns']<=checks[i-1]['monotonic_ns']:
            fail('true calls are not serial')
        verify_census(request.get('census_before'));verify_census(check.get('census_after'))
        if (request['census_before']['monotonic_ns']>request['monotonic_ns'] or
            check['census_after']['monotonic_ns']<=response['monotonic_ns'] or
            check['census_after']['monotonic_ns']>check['monotonic_ns']):
            fail('true census timestamp invalid')
        if not request['monotonic_ns']<response['monotonic_ns']<check['monotonic_ns']:
            fail('true request/response/check order invalid')
        try:reply=json.loads(response_bytes(response))
        except (ValueError,UnicodeDecodeError):fail('true response JSON invalid')
        counts=validate_chat_cache_evidence(reply,first_call=request['sequence']==1,cache_prompt=True)
        if check.get('cache_counts')!=counts:fail('true recorded cache counts disagree with response')
        try:
            choices=reply['choices']
            if not isinstance(choices,list) or not choices or not isinstance(choices[0],dict):raise ValueError('invalid choices')
            message=choices[0]['message']
            if not isinstance(message,dict) or not isinstance(message.get('content'),str):raise ValueError('invalid message')
            key=(request.get('prompt_id'),request.get('structured'),request.get('repeat'))
            if key in messages_by_key:raise ValueError('duplicate response key')
            messages_by_key[key]=canonical(message)
        except (KeyError,TypeError,ValueError):fail('true response message missing or invalid')
        if request.get('structured') is False and request.get('repeat')==0 and counts['prompt_tokens_cached']>0:
            first_prompt_hits+=1
    if completed[0].get('first_prompt_calls')!=50 or completed[0].get('first_prompt_cache_hits')!=first_prompt_hits:
        fail('true first-prompt cache-hit summary mismatch')
    seen=set();true_templates={}
    for row in attempts:
        if row.get('route')!='/v1/chat/completions':fail('true request route invalid')
        key=(row.get('prompt_id'),row.get('structured'),row.get('repeat'))
        if (key in seen or key[0] not in expected or type(key[1]) is not bool or
            type(key[2]) is not int or key[2] not in (0,1)):
            fail('true prompt/mode/repeat invalid')
        seen.add(key)
        body=row.get('request_body')
        if not isinstance(body,str) or hashlib.sha256(body.encode()).hexdigest()!=row.get('request_body_sha256'):
            fail('true request digest invalid')
        try:request=json.loads(body)
        except (ValueError,TypeError):fail('true request JSON invalid')
        source=expected[key[0]]
        if (request.get('cache_prompt') is not True or type(request.get('seed')) is not int or request.get('seed')!=source.get('seed') or
            request.get('model')!=alias or type(request.get('temperature')) not in (int,float) or request.get('temperature')!=.2 or
            type(request.get('max_tokens')) is not int or request.get('max_tokens')!=4096 or
            request.get('messages')!=[{'role':'user','content':source.get('prompt')}]):
            fail('true request binding invalid')
        if (canonical(request.get('response_format'))!=canonical(schema_format) if key[1] else 'response_format' in request):
            fail('true structured request binding invalid')
        # Canonical JSON preserves JSON types, array order, nested fields and
        # every extra setting. Only the cache flag is allowed to differ later.
        without_cache={k:v for k,v in request.items() if k!='cache_prompt'}
        canonical_request=canonical(without_cache)
        template_key=(key[0],key[1])
        if template_key in true_templates and true_templates[template_key]!=canonical_request:
            fail('true repeats differ in non-cache request parameters')
        true_templates[template_key]=canonical_request
    if len(seen)!=200:fail('true coverage invalid')
    matching={}
    for structured,label in ((False,'free'),(True,'schema')):
        matching[label]=sum(messages_by_key[(trial_id,structured,0)]==messages_by_key[(trial_id,structured,1)]
                            for trial_id in expected)
    declared=completed[0].get('matching')
    if (not isinstance(declared,dict) or set(declared)!={'free','schema'} or
        any(type(declared[k]) is not int or declared[k]!=matching[k] for k in matching)):
        fail('true matching summary disagrees with response messages')
    completion=completed[0]['monotonic_ns']
    if completion<=max(r['monotonic_ns'] for r in checks):fail('completion precedes last true check')
    non_gen_responses=[r for r in nongen_rows if r.get('event')=='response']
    if not non_gen_responses:fail('tokenize response missing')
    try:token_reply=json.loads(response_bytes(non_gen_responses[0]));tokens=token_reply['tokens']
    except (ValueError,TypeError,KeyError,UnicodeDecodeError):fail('tokenize response invalid')
    if not isinstance(tokens,list) or not tokens or any(type(x) is not int for x in tokens):
        fail('tokenize response tokens invalid')
    expected_tokens=(tokens*((ctx_size-1+len(tokens)-1)//len(tokens)))[:ctx_size-1]
    attempt_by_kind={};check_by_kind={}
    for label,rows in (('false',false_rows),('non-generation',nongen_rows)):
        attempts=[r for r in rows if r.get('event')=='request_attempt']
        checks=[r for r in rows if r.get('event')=='checked']
        attempt_by_kind[label]=attempts;check_by_kind[label]=checks
        responses=[r for r in rows if r.get('event')=='response']
        required=(201+int(expect_grammar)) if label=='false' else nongen_required
        if len(attempts)!=required or len(checks)!=len(attempts) or len(responses)!=len(attempts):
            fail(label+' request/check coverage incomplete')
        seq=list(range(1,len(attempts)+1))
        if [r.get('sequence') for r in attempts]!=seq or [r.get('sequence') for r in checks]!=seq or [r.get('sequence') for r in responses]!=seq:
            fail(label+' request/check sequence invalid')
        for i,(request,response,check) in enumerate(zip(attempts,responses,checks)):
            if i and request['monotonic_ns']<=checks[i-1]['monotonic_ns']:
                fail(label+' calls are not serial')
            verify_census(request.get('census_before'));verify_census(check.get('census_after'))
            if (request['census_before']['monotonic_ns']>request['monotonic_ns'] or
                check['census_after']['monotonic_ns']<=response['monotonic_ns'] or
                check['census_after']['monotonic_ns']>check['monotonic_ns']):
                fail(label+' census timestamp invalid')
            if not request['monotonic_ns']<response['monotonic_ns']<check['monotonic_ns']:
                fail(label+' request/response/check order invalid')
            raw=response_bytes(response)
            if label=='false':
                try:reply=json.loads(raw)
                except (ValueError,UnicodeDecodeError):fail('false response JSON invalid')
                if request.get('route')=='/v1/chat/completions':
                    counts=validate_chat_cache_evidence(reply,first_call=False,cache_prompt=False)
                elif request.get('route')=='/completion':
                    timing=reply.get('timings') or {};cached=timing.get('cache_n');processed=timing.get('prompt_n');total=reply.get('tokens_evaluated')
                    if any(type(x) is not int or x<0 for x in (cached,processed,total)) or cached!=0 or processed!=total or total==0:
                        fail('false prefill response cache counts invalid')
                    counts={'prompt_tokens_processed':processed,'prompt_tokens_cached':cached,'tokens_evaluated_total':total}
                else:fail('false response route invalid')
                if check.get('counts')!=counts:fail('false recorded cache counts disagree with response')
        parsed=[]
        for row in rows:
            if row.get('event')!='request_attempt':continue
            if row['monotonic_ns']<=completion:fail(label+' request precedes complete true run')
            body=row.get('request_body')
            if not isinstance(body,str) or hashlib.sha256(body.encode()).hexdigest()!=row.get('request_body_sha256'):
                fail(label+' request digest invalid')
            if label=='false':
                try:request=json.loads(body)
                except (TypeError,ValueError):fail('false request JSON invalid')
                if request.get('cache_prompt') is not False:fail('false request cache flag invalid')
                parsed.append((row.get('route'),request))
            else:
                if row.get('route') not in ('/tokenize','/apply-template'):
                    fail('non-generation route invalid')
                try:request=json.loads(body)
                except (TypeError,ValueError):fail('non-generation request JSON invalid')
                parsed.append((row.get('route'),request))
        if label=='false':
            route,prefill=parsed[0]
            if (route!='/completion' or type(prefill.get('prompt')) is not list or
                prefill['prompt']!=expected_tokens or any(type(x) is not int for x in prefill['prompt']) or
                type(prefill.get('n_predict')) is not int or prefill.get('n_predict')!=1 or
                type(prefill.get('seed')) is not int or prefill.get('seed')!=0 or
                type(prefill.get('temperature')) not in (int,float) or prefill.get('temperature')!=.2):
                fail('false prefill binding invalid')
            replay=parsed[1:201];counts={}
            for route,request in replay:
                messages=request.get('messages')
                if route!='/v1/chat/completions' or not isinstance(messages,list) or len(messages)!=1 or not isinstance(messages[0],dict):
                    fail('false replay route/messages invalid')
                prompt=messages[0].get('content');source=by_prompt.get(prompt)
                if (source is None or messages!=[{'role':'user','content':prompt}] or
                    request.get('model')!=alias or type(request.get('seed')) is not int or request.get('seed')!=source.get('seed') or
                    type(request.get('temperature')) not in (int,float) or request.get('temperature')!=.2 or
                    type(request.get('max_tokens')) is not int or request.get('max_tokens')!=4096):
                    fail('false replay request binding invalid')
                structured='response_format' in request
                if structured and canonical(request['response_format'])!=canonical(schema_format):fail('false replay schema binding invalid')
                key=(source['trial_id'],structured);counts[key]=counts.get(key,0)+1
                without_cache={k:v for k,v in request.items() if k!='cache_prompt'}
                canonical_request=canonical(without_cache)
                if canonical_request!=true_templates.get(key):fail('true/false non-cache request parameters differ')
            if set(counts)!={(i,s) for i in expected for s in (False,True)} or any(n!=2 for n in counts.values()):
                fail('false replay prompt/mode/repeat coverage invalid')
            if expect_grammar:
                route,request=parsed[201]
                first=prompts[0]
                if (route!='/v1/chat/completions' or request.get('model')!=alias or
                    type(request.get('seed')) is not int or request.get('seed')!=first.get('seed') or
                    type(request.get('temperature')) not in (int,float) or request.get('temperature')!=.2 or
                    type(request.get('max_tokens')) is not int or request.get('max_tokens')!=4096 or
                    canonical(request.get('response_format'))!=canonical(schema_format) or
                    request.get('messages')!=[{'role':'user','content':first['prompt']}] or
                    canonical(request.get('chat_template_kwargs'))!=canonical({'enable_thinking':True}) or
                    type(request.get('reasoning_budget_tokens')) is not int or request.get('reasoning_budget_tokens')!=2048):
                    fail('false grammar probe binding invalid')
        else:
            if canonical(parsed)!=canonical(expected_non_generation):
                fail('non-generation tokenize/template binding invalid')
    tokenize_check=check_by_kind['non-generation'][0]['monotonic_ns']
    prefill_attempt=attempt_by_kind['false'][0]['monotonic_ns']
    prefill_check=check_by_kind['false'][0]['monotonic_ns']
    template_attempts=attempt_by_kind['non-generation'][1:]
    template_checks=check_by_kind['non-generation'][1:]
    replay_attempt=attempt_by_kind['false'][1]['monotonic_ns']
    if not (tokenize_check<prefill_attempt and prefill_check<min(r['monotonic_ns'] for r in template_attempts)
            and max(r['monotonic_ns'] for r in template_checks)<replay_attempt):
        fail('tokenize/prefill/template/replay cross-journal order invalid')
    return {'scope':'worker journals and discrete census samples only; host-wide exclusion, continuity and coldness not established',
            'true_calls':200,'true_prompts':50,'true_completed_before_recorded_primary':True}
