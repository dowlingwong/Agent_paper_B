"""Synthetic trace tests; no HTTP, real server, model, GPU, or host census."""
import copy
import pytest
from r1.exam.cache_trace_synthetic import validate_synthetic_trace


def fixture():
    prompt_ids=[str(i) for i in range(50)];calls=[]
    for key in prompt_ids:
        for _ in range(2):
            calls.append({'prompt_id':key,'message':'same','cache_prompt':True})
    calls.append({'cache_prompt':False,'prompt_id':'probe','message':'other'})
    for i,call in enumerate(calls):
        call.update(sequence=i+1,pid=112,process_start_ticks=55,
                    census_before={'scope':'fixture_servers','pids':[112]},
                    census_after={'scope':'fixture_servers','pids':[112]},
                    response={'timings':{'prompt_n':10,'cache_n':0},
                              'usage':{'prompt_tokens':10,'prompt_tokens_details':{'cached_tokens':0}}})
    return {'kind':'SYNTHETIC_FIXTURE_ONLY','startup':{'pid':112,'process_start_ticks':55,'fresh_process':True},
            'prompt_ids':prompt_ids,'calls':calls}


def test_complete_trace_and_observation_limit():
    out=validate_synthetic_trace(fixture())
    assert out['true_reproducible']==50 and 'not continuous' in out['count_observation']


@pytest.mark.parametrize('mutation', [
    lambda t: t.update(kind='production'),
    lambda t: t['startup'].update(fresh_process=False),
    lambda t: t['startup'].pop('process_start_ticks'),
    lambda t: t['calls'][0].update(cache_prompt=False),
    lambda t: t['calls'][0]['response']['timings'].update(cache_n=1),
    lambda t: t['calls'][1].update(process_start_ticks=56),
    lambda t: t['calls'][1].pop('census_before'),
    lambda t: t['calls'][1]['census_after'].update(pids=[112,113]),
    lambda t: t['calls'][1].update(sequence=9),
    lambda t: t['calls'].pop(1),
    lambda t: t['calls'][-1].update(cache_prompt=True),
])
def test_missing_or_conflicting_evidence_stops(mutation):
    t=copy.deepcopy(fixture());mutation(t)
    with pytest.raises(ValueError,match='STOP'):
        validate_synthetic_trace(t)
