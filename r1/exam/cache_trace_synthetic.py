"""Synthetic-only D3 transcript checker; never authorizes real inference.

The caller-supplied records are test fixtures, not proof of server identity,
request ordering or server residency. A real mechanism is not implemented.
"""
from r1.exam.cache_evidence import validate_chat_cache_evidence


def validate_synthetic_trace(trace):
    if trace.get('kind') != 'SYNTHETIC_FIXTURE_ONLY':
        raise ValueError('STOP: synthetic fixtures only')
    startup=trace.get('startup') or {}
    pid=startup.get('pid'); start=startup.get('process_start_ticks')
    if (type(pid) is not int or pid <= 0 or type(start) is not int or start <= 0
            or startup.get('fresh_process') is not True):
        raise ValueError('STOP: missing synthetic fresh process identity')
    expected=trace.get('prompt_ids')
    if (not isinstance(expected,list) or len(expected)!=50 or
            any(not isinstance(x,str) or not x for x in expected) or len(set(expected))!=50):
        raise ValueError('STOP: expected 50 unique prompt ids')
    calls=trace.get('calls')
    if not isinstance(calls,list) or not calls:
        raise ValueError('STOP: missing call trace')
    seen={key:[] for key in expected}; switched=False
    for i,call in enumerate(calls):
        if not isinstance(call,dict) or call.get('sequence')!=i+1:
            raise ValueError('STOP: missing call sequence')
        if call.get('pid')!=pid or call.get('process_start_ticks')!=start:
            raise ValueError('STOP: server identity changed')
        for when in ('census_before','census_after'):
            census=call.get(when)
            if not isinstance(census,dict) or census.get('scope')!='fixture_servers' or census.get('pids')!=[pid]:
                raise ValueError('STOP: server census unavailable or not one')
        setting=call.get('cache_prompt')
        if type(setting) is not bool:
            raise ValueError('STOP: absent cache setting')
        if i==0 and setting is not True:
            raise ValueError('STOP: first inference is not true')
        if not setting:
            switched=True
        elif switched:
            raise ValueError('STOP: true call after false')
        validate_chat_cache_evidence(call.get('response'),first_call=(i==0),cache_prompt=setting)
        if setting:
            key=call.get('prompt_id')
            if key not in seen or 'message' not in call or call['message'] is None:
                raise ValueError('STOP: missing prompt identity or output')
            seen[key].append(call['message'])
    if not switched or any(len(x)!=2 for x in seen.values()):
        raise ValueError('STOP: incomplete descriptive replay or false stage')
    return {'label':'SYNTHETIC_FIXTURE_ONLY','true_reproducible':sum(x[0]==x[1] for x in seen.values()),
            'prompt_count':50,'count_scope':'fixture_servers',
            'count_observation':'before and after calls only; not continuous'}
