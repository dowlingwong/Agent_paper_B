"""Synthetic JSON fixtures; these do not demonstrate a real server contract."""
import copy
import pytest
from r1.exam.cache_evidence import validate_chat_cache_evidence


def response(processed=10, cached=0):
    return {'timings': {'prompt_n': processed, 'cache_n': cached},
            'usage': {'prompt_tokens': processed + cached,
                      'prompt_tokens_details': {'cached_tokens': cached}}}


def test_cold_first_and_warm_followup():
    assert validate_chat_cache_evidence(response(), first_call=True, cache_prompt=True)['prompt_tokens_cached'] == 0
    assert validate_chat_cache_evidence(response(6, 4), first_call=False, cache_prompt=True)['prompt_tokens_processed'] == 6


def test_first_hit_refused():
    with pytest.raises(ValueError, match='first call'):
        validate_chat_cache_evidence(response(6, 4), first_call=True, cache_prompt=True)


@pytest.mark.parametrize('path,value', [
    (('timings',), None), (('usage',), None),
    (('timings', 'prompt_n'), None), (('timings', 'cache_n'), True),
    (('usage', 'prompt_tokens'), -1),
    (('usage', 'prompt_tokens_details', 'cached_tokens'), 1),
    (('usage', 'prompt_tokens'), 11),
])
def test_missing_invalid_or_inconsistent_counts_stop(path, value):
    obj = copy.deepcopy(response())
    parent = obj
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError, match='STOP'):
        validate_chat_cache_evidence(obj, first_call=False, cache_prompt=True)


def test_nonempty_prompt_zero_token_response_stops():
    for first_call in (True, False):
        with pytest.raises(ValueError, match='non-empty prompt'):
            validate_chat_cache_evidence(response(0, 0), first_call=first_call, cache_prompt=True)


def test_first_call_zero_processing_stops_even_with_cached_tokens():
    with pytest.raises(ValueError, match='first-call processing'):
        validate_chat_cache_evidence(response(0, 5), first_call=True, cache_prompt=True)


def test_disabled_cache_rejects_hit():
    with pytest.raises(ValueError, match='cache_prompt false'):
        validate_chat_cache_evidence(response(6, 4), first_call=False, cache_prompt=False)
    result = validate_chat_cache_evidence(response(10, 0), first_call=False, cache_prompt=False)
    assert result['cache_prompt'] is False


@pytest.mark.parametrize('value', [None, 0, 1, 'false'])
def test_cache_setting_must_be_explicit_boolean(value):
    with pytest.raises(ValueError, match='cache setting'):
        validate_chat_cache_evidence(response(), first_call=False, cache_prompt=value)
