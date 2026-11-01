"""Synthetic worker-journal checks do not prove host-wide isolation."""
import hashlib
import base64
import json
import pytest
from r1.exam.cache_order import validate_local_order
from r1.exam.cache_proc import CENSUS_METHOD,CENSUS_SCOPE,census_digest

IDENTITY={'pid':7,'process_start_ticks':9,'fresh':True,'binary':'/fixture/llama-server'}


def sample(time):
    result={'method':CENSUS_METHOD,'scope':CENSUS_SCOPE,'count':1,'pid':7,'process_start_ticks':9,
            'observed':[{'pid':7,'process_start_ticks':9,'executable':'/fixture/llama-server'}],'monotonic_ns':time,
            'inaccessible_executable_links':0,'missing_executable_links':0,
            'unreadable_executable_links':0,'unreadable_executable_errnos':[],'unreadable_executable_samples':[],
            'unobserved_same_uid_calls':'assumed absent by author decision, not measured',
            'host_global_single_server':'NOT_CHECKABLE'}
    result['snapshot_sha256']=census_digest(result)
    return result


def retime_census(rows):
    for row in rows:
        if row['event']=='request_attempt':row['census_before']=sample(row['monotonic_ns']-1)
        elif row['event']=='checked':row['census_after']=sample(row['monotonic_ns']-1)


def records():
    prompts=[{'trial_id':f't{i}','prompt':f'synthetic{i}','seed':i} for i in range(50)]
    true=[{'event':'startup','identity':IDENTITY,'monotonic_ns':1}];clock=10;seq=0
    def response(seq,clock):
        raw=json.dumps({'tokens':[1,2,3],'tokens_evaluated':10,'choices':[{'message':{'content':'synthetic'}}],
                        'timings':{'prompt_n':10,'cache_n':0},
                        'usage':{'prompt_tokens':10,'prompt_tokens_details':{'cached_tokens':0}}}).encode()
        return {'event':'response','sequence':seq,'http_status':200,'response_body_b64':base64.b64encode(raw).decode(),
                'response_body_sha256':hashlib.sha256(raw).hexdigest(),'monotonic_ns':clock}
    for row in prompts:
        for structured in (False,True):
            for repeat in (0,1):
                seq+=1
                request={'messages':[{'role':'user','content':row['prompt']}],'seed':row['seed'],'cache_prompt':True,
                         'model':'fixture','temperature':.2,'max_tokens':4096}
                if structured:request['response_format']={'fixture':True}
                body=json.dumps(request)
                true.append({'event':'request_attempt','sequence':seq,'route':'/v1/chat/completions','prompt_id':row['trial_id'],
                             'structured':structured,'repeat':repeat,'request_body':body,
                             'request_body_sha256':hashlib.sha256(body.encode()).hexdigest(),'monotonic_ns':clock})
                clock+=10;true.append(response(seq,clock));clock+=10
                true.append({'event':'checked','sequence':seq,'monotonic_ns':clock,
                             'cache_counts':{'prompt_tokens_processed':10,'prompt_tokens_cached':0,'usage_prompt_tokens':10,
                                             'first_call':seq==1,'cache_prompt':True}});clock+=10
    true.append({'event':'true_replay_complete','calls':200,'prompt_count':50,'selection_criterion':False,
                 'first_prompt_calls':50,'first_prompt_cache_hits':0,'matching':{'free':50,'schema':50},'monotonic_ns':clock});clock+=10
    def prim(payloads):
        nonlocal clock
        rows=[]
        for seq,(route,payload) in enumerate(payloads,1):
            body=json.dumps(payload)
            rows.append({'event':'request_attempt','sequence':seq,'route':route,'request_body':body,
                         'request_body_sha256':hashlib.sha256(body.encode()).hexdigest(),'monotonic_ns':clock})
            clock+=10;rows.append(response(seq,clock));clock+=10
            check={'event':'checked','sequence':seq,'monotonic_ns':clock}
            if route=='/completion':check['counts']={'prompt_tokens_processed':10,'prompt_tokens_cached':0,'tokens_evaluated_total':10}
            elif route=='/v1/chat/completions':check['counts']={'prompt_tokens_processed':10,'prompt_tokens_cached':0,'usage_prompt_tokens':10,'first_call':False,'cache_prompt':False}
            rows.append(check);clock+=10
        return rows
    false=[('/completion',{'prompt':[1,2,3],'n_predict':1,'seed':0,'temperature':.2,'cache_prompt':False})]
    for row in prompts:
        for structured in (False,True):
            for repeat in (0,1):
                request={'messages':[{'role':'user','content':row['prompt']}],'seed':row['seed'],'cache_prompt':False,
                         'model':'fixture','temperature':.2,'max_tokens':4096}
                if structured:request['response_format']={'fixture':True}
                false.append(('/v1/chat/completions',request))
    nongen=[('/tokenize',{'content':'a ','add_special':True})]
    for i in range(5):
        messages=[{'role':'user','content':f'Fixed template check {i}: JSON, whitespace, Unicode α, newline\nend.'}]
        nongen.append(('/apply-template',{'messages':messages,'add_generation_prompt':True,
                                          'chat_template_kwargs':{'enable_thinking':False}}))
    false_rows=prim(false);nongen_rows=prim(nongen)
    t=true[-1]['monotonic_ns']+10
    for row in nongen_rows[:3]+false_rows[:3]+nongen_rows[3:]+false_rows[3:]:
        row['monotonic_ns']=t;t+=10
    for rows in (true,false_rows,nongen_rows):retime_census(rows)
    return true,false_rows,nongen_rows,prompts


def validate(*args):
    return validate_local_order(*args,alias='fixture',ctx_size=4,schema_format={'fixture':True},expect_grammar=False,thinking_enabled=False,identity=IDENTITY)


def test_complete_local_trace_is_explicitly_not_host_wide_proof():
    result=validate(*records())
    assert result['true_calls']==200 and 'continuity and coldness not established' in result['scope']


def test_primary_before_complete_true_is_stop():
    true,false,nongen,prompts=records();false[0]['monotonic_ns']=true[-1]['monotonic_ns']-1
    false[0]['census_before']=sample(false[0]['monotonic_ns']-1)
    with pytest.raises(ValueError,match='precedes complete true'):validate(true,false,nongen,prompts)


def test_missing_true_check_and_wrong_seed_are_stop():
    true,false,nongen,prompts=records()
    with pytest.raises(ValueError,match='true run incomplete'):validate(true[:-2]+true[-1:],false,nongen,prompts)
    prompts[0]['seed']+=1
    with pytest.raises(ValueError,match='binding invalid'):validate(true,false,nongen,prompts)


def test_incomplete_primary_and_journal_stop_are_stop():
    true,false,nongen,prompts=records()
    with pytest.raises(ValueError,match='coverage incomplete'):validate(true,false[:-3],nongen,prompts)
    false[-1]['event']='stop'
    with pytest.raises(ValueError,match='contains STOP'):validate(true,false,nongen,prompts)


def change_request(row,updates):
    body=json.loads(row['request_body']);body.update(updates);text=json.dumps(body)
    row['request_body']=text;row['request_body_sha256']=hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.parametrize('update',[{'model':'other'}, {'seed':999}, {'seed':False}, {'temperature':0},
                                   {'max_tokens':1}, {'max_tokens':4096.0}, {'response_format':{'bad':'schema'}}])
def test_false_request_wrong_identity_or_settings_stop(update):
    true,false,nongen,prompts=records();change_request(false[3],update)
    with pytest.raises(ValueError,match='binding invalid'):validate(true,false,nongen,prompts)


def test_all_completion_primary_bypass_is_rejected():
    true,false,nongen,prompts=records()
    for row in false:
        if row.get('event')=='request_attempt':row['route']='/completion'
        if row.get('event')=='checked':row['counts']={'prompt_tokens_processed':10,'prompt_tokens_cached':0,'tokens_evaluated_total':10}
    with pytest.raises(ValueError,match='route/messages invalid'):validate(true,false,nongen,prompts)


@pytest.mark.parametrize('update',[{'model':'other'}, {'temperature':0}, {'max_tokens':1}])
def test_true_request_wrong_settings_stop(update):
    true,false,nongen,prompts=records();change_request(true[1],update)
    with pytest.raises(ValueError,match='true request binding invalid'):validate(true,false,nongen,prompts)


def test_true_schema_must_match_exactly():
    true,false,nongen,prompts=records()
    structured=next(r for r in true if r.get('event')=='request_attempt' and r.get('structured'))
    change_request(structured,{'response_format':{'bad':'schema'}})
    with pytest.raises(ValueError,match='structured request binding invalid'):validate(true,false,nongen,prompts)


def test_grammar_probe_is_separately_bound_after_replay():
    true,false,nongen,prompts=records();start=false[-1]['monotonic_ns']+10
    attempt=dict(false[9]);response=dict(false[10]);checked=dict(false[11])
    # false[9] is first prompt's first structured replay request.
    for i,row in enumerate((attempt,response,checked)):
        row['sequence']=202;row['monotonic_ns']=start+i*10
    change_request(attempt,{'chat_template_kwargs':{'enable_thinking':True},'reasoning_budget_tokens':2048})
    false.extend((attempt,response,checked))
    retime_census(false)
    result=validate_local_order(true,false,nongen,prompts,alias='fixture',ctx_size=4,
                                schema_format={'fixture':True},expect_grammar=True,thinking_enabled=False,identity=IDENTITY)
    assert result['true_calls']==200
    change_request(attempt,{'seed':999})
    with pytest.raises(ValueError,match='grammar probe binding invalid'):
        validate_local_order(true,false,nongen,prompts,alias='fixture',ctx_size=4,
                             schema_format={'fixture':True},expect_grammar=True,thinking_enabled=False,identity=IDENTITY)


def test_prefill_tokens_must_match_tokenizer_output():
    true,false,nongen,prompts=records();change_request(false[0],{'prompt':[9,9,9]})
    with pytest.raises(ValueError,match='prefill binding invalid'):
        validate(true,false,nongen,prompts)


@pytest.mark.parametrize('which',['true','false','nongen'])
def test_batching_attempts_before_responses_is_rejected(which):
    true,false,nongen,prompts=records()
    rows={'true':true,'false':false,'nongen':nongen}[which]
    prefix=[r for r in rows if r['event']=='startup']
    attempts=[r for r in rows if r['event']=='request_attempt']
    responses=[r for r in rows if r['event']=='response']
    checks=[r for r in rows if r['event']=='checked']
    suffix=[r for r in rows if r['event']=='true_replay_complete']
    reordered=prefix+attempts+responses+checks+suffix
    start=rows[0]['monotonic_ns']
    for i,row in enumerate(reordered):row['monotonic_ns']=start+i*10
    retime_census(reordered)
    if which=='true':true=reordered
    elif which=='false':false=reordered
    else:nongen=reordered
    with pytest.raises(ValueError,match='calls are not serial'):
        validate(true,false,nongen,prompts)


@pytest.mark.parametrize('which',['true','false','nongen'])
@pytest.mark.parametrize('field',['missing','changed'])
def test_missing_or_changed_census_never_qualifies(which,field):
    true,false,nongen,prompts=records()
    rows={'true':true,'false':false,'nongen':nongen}[which]
    attempt=next(r for r in rows if r['event']=='request_attempt')
    if field=='missing':attempt.pop('census_before')
    else:attempt['census_before']['pid']=999
    with pytest.raises(ValueError,match='server census or identity mismatch'):
        validate(true,false,nongen,prompts)


def test_boolean_server_count_is_not_integer_census():
    true,false,nongen,prompts=records()
    attempt=next(r for r in true if r['event']=='request_attempt')
    attempt['census_before']['count']=True
    with pytest.raises(ValueError,match='server census or identity mismatch'):
        validate(true,false,nongen,prompts)


def test_prefill_must_wait_for_tokenize_check():
    true,false,nongen,prompts=records()
    # Preserve order inside the tokenize journal but put its completion after
    # the already-recorded prefill attempt.
    start=false[0]['monotonic_ns']
    for i,row in enumerate(nongen[:3]):row['monotonic_ns']=start+i*10
    retime_census(nongen)
    with pytest.raises(ValueError,match='tokenize/prefill/template/replay cross-journal order'):
        validate(true,false,nongen,prompts)


def test_true_route_must_be_chat_completions():
    true,false,nongen,prompts=records()
    for row in true:
        if row.get('event')=='request_attempt':row['route']='/completion'
    with pytest.raises(ValueError,match='true request route invalid'):
        validate(true,false,nongen,prompts)


def test_made_up_census_or_missing_observations_never_qualify():
    true,false,nongen,prompts=records()
    attempt=next(r for r in true if r['event']=='request_attempt')
    attempt['census_before']['method']='no actual sampling'
    attempt['census_before']['scope']='made up'
    attempt['census_before'].pop('observed')
    with pytest.raises(ValueError,match='server census or identity mismatch'):
        validate(true,false,nongen,prompts)


def test_tampered_census_detail_or_digest_is_rejected():
    true,false,nongen,prompts=records()
    attempt=next(r for r in false if r['event']=='request_attempt')
    attempt['census_before']['observed'][0]['executable']='/other/llama-server'
    with pytest.raises(ValueError,match='server census or identity mismatch'):
        validate(true,false,nongen,prompts)


def test_true_matching_summary_must_match_actual_messages():
    true,false,nongen,prompts=records()
    true[-1]['matching']={'free':0,'schema':50}
    with pytest.raises(ValueError,match='matching summary disagrees'):
        validate(true,false,nongen,prompts)
    true[-1]['matching']={'free':50,'schema':50}
    response=next(r for r in true if r.get('event')=='response')
    raw=json.loads(base64.b64decode(response['response_body_b64']))
    raw['choices'][0]['message']['content']='different synthetic'
    wire=json.dumps(raw).encode();response['response_body_b64']=base64.b64encode(wire).decode()
    response['response_body_sha256']=hashlib.sha256(wire).hexdigest()
    with pytest.raises(ValueError,match='matching summary disagrees'):
        validate(true,false,nongen,prompts)


def test_true_response_missing_message_never_qualifies():
    true,false,nongen,prompts=records()
    response=next(r for r in true if r.get('event')=='response')
    raw=json.loads(base64.b64decode(response['response_body_b64']));raw.pop('choices')
    wire=json.dumps(raw).encode();response['response_body_b64']=base64.b64encode(wire).decode()
    response['response_body_sha256']=hashlib.sha256(wire).hexdigest()
    with pytest.raises(ValueError,match='response message missing or invalid'):
        validate(true,false,nongen,prompts)


def test_swapped_repeat_labels_cannot_redefine_first_call():
    true,false,nongen,prompts=records()
    first=next(r for r in true if r.get('event')=='request_attempt' and r.get('prompt_id')=='t0' and r.get('structured') is False and r.get('repeat')==0)
    second=next(r for r in true if r.get('event')=='request_attempt' and r.get('prompt_id')=='t0' and r.get('structured') is False and r.get('repeat')==1)
    first['repeat'],second['repeat']=second['repeat'],first['repeat']
    with pytest.raises(ValueError,match='schedule invalid'):
        validate(true,false,nongen,prompts)


def test_all_tokenize_non_generation_bypass_is_rejected():
    true,false,nongen,prompts=records()
    for row in nongen:
        if row.get('event')=='request_attempt':row['route']='/tokenize'
    with pytest.raises(ValueError,match='tokenize/template binding invalid'):
        validate(true,false,nongen,prompts)


def test_template_content_or_thinking_mode_mismatch_is_rejected():
    true,false,nongen,prompts=records();change_request(nongen[3],{'messages':[{'role':'user','content':'wrong'}]})
    with pytest.raises(ValueError,match='tokenize/template binding invalid'):
        validate(true,false,nongen,prompts)


def test_cache_hit_summary_and_recorded_counts_must_match_raw_response():
    true,false,nongen,prompts=records()
    true[-1]['first_prompt_cache_hits']=1
    with pytest.raises(ValueError,match='first-prompt cache-hit summary mismatch'):
        validate(true,false,nongen,prompts)
    true[-1]['first_prompt_cache_hits']=0
    false[2]['counts']['prompt_tokens_cached']=1
    with pytest.raises(ValueError,match='false recorded cache counts disagree'):
        validate(true,false,nongen,prompts)


@pytest.mark.parametrize('extra',[{'top_p':.01},{'chat_template_kwargs':{'enable_thinking':True}},
                                  {'stream':False},{'temperature':True},{'unexpected_nested':{'x':[1,2]}}])
def test_false_extra_or_changed_non_cache_parameters_cannot_pass(extra):
    true,false,nongen,prompts=records();change_request(false[3],extra)
    with pytest.raises(ValueError,match='binding invalid|parameters differ'):
        validate(true,false,nongen,prompts)


def test_true_repeat_non_cache_difference_cannot_pass():
    true,false,nongen,prompts=records()
    second=next(r for r in true if r.get('event')=='request_attempt' and r.get('prompt_id')=='t0' and r.get('structured') is False and r.get('repeat')==1)
    change_request(second,{'top_p':.01})
    with pytest.raises(ValueError,match='true repeats differ'):
        validate(true,false,nongen,prompts)
