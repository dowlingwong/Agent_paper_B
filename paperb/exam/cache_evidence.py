"""D3 response validation only. This module cannot authorize a Stage A run.

The caller must separately establish cold startup, request order and resident
server census. Missing or contradictory response fields are not evidence.
"""
from __future__ import annotations


def validate_chat_cache_evidence(reply, *, first_call, cache_prompt):
    if not isinstance(reply, dict) or type(first_call) is not bool or type(cache_prompt) is not bool:
        raise ValueError('STOP: malformed response, first-call indicator, or cache setting')
    timing = reply.get('timings')
    usage = reply.get('usage')
    if not isinstance(timing, dict) or not isinstance(usage, dict):
        raise ValueError('STOP: missing per-call timings or usage')
    details = usage.get('prompt_tokens_details')
    if not isinstance(details, dict):
        raise ValueError('STOP: missing prompt token cache details')
    processed, cached = timing.get('prompt_n'), timing.get('cache_n')
    total, usage_cached = usage.get('prompt_tokens'), details.get('cached_tokens')
    for value in (processed, cached, total, usage_cached):
        if type(value) is not int or value < 0:
            raise ValueError('STOP: missing or invalid per-call cache counts')
    # Stage A calls contain non-empty manager prompts. Zero total tokens or a
    # cold first call with no processing cannot certify such a call.
    if total == 0 or (first_call and processed == 0):
        raise ValueError('STOP: non-empty prompt has zero tokens or first-call processing')
    if processed + cached != total or cached != usage_cached:
        raise ValueError('STOP: inconsistent prompt/cache token counts')
    if not cache_prompt and cached != 0:
        raise ValueError('STOP: cache_prompt false reports a cache hit')
    if first_call and cached != 0:
        raise ValueError('STOP: first call reports a cache hit')
    return {'prompt_tokens_processed': processed, 'prompt_tokens_cached': cached,
            'usage_prompt_tokens': total, 'first_call': first_call,
            'cache_prompt': cache_prompt}
