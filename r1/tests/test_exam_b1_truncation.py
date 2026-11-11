"""R1-EXAM-B1-TRUNCATION-INVALID (11 Nov 2026): a truncated proposer reply is an invalid trial, and every
proposer call carries the completion cap.  Regression for B1 run fffa_20261111_b (STOP: an uncaught
``openai.LengthFinishReasonError`` from a qwen36_27b thinking-on reply that filled the context).

The end-to-end tests drive one exam-shaped campaign root through the pinned harness ``run_real_campaign``
with the proposer from ``r1.exam.campaign.exam_manager`` against a stand-in llama-server
(``exam_truncation_driver.py``).  They need the B1/B2 harness pin a3fedbb (``AR_HARNESS_B1_ROOT``, as in
``test_exam_x5_rule_v2``) and skip without it unless ``R1_REQUIRE_B1_HARNESS=1``.
ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
A3FEDBB = 'a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
CAP = 16384
ADDED_KEYS = {'max_completion_tokens', 'finish_reason', 'truncated', 'truncation_policy', 'truncation_error_type',
              'discarded_content_chars', 'discarded_reasoning_chars'}


def _harness():
    for cand in (os.environ.get('AR_HARNESS_B1_ROOT'), '/home/claude/wt/harness-a3fedbb',
                 str(REPO.parent / 'autoresearch_harness_a3fedbb')):
        if cand and (Path(cand) / 'src').is_dir():
            head = subprocess.check_output(['git', '-C', cand, 'rev-parse', 'HEAD'], text=True).strip()
            assert head == A3FEDBB, f'B1/B2 harness pin must be {A3FEDBB}, found {head}'
            return Path(cand)
    if os.environ.get('R1_REQUIRE_B1_HARNESS') == '1':
        pytest.fail('R1_REQUIRE_B1_HARNESS=1 but no a3fedbb checkout found; set AR_HARNESS_B1_ROOT')
    pytest.skip('harness a3fedbb checkout not found; set AR_HARNESS_B1_ROOT (R1_REQUIRE_B1_HARNESS=1 makes this fail)')


def _drive(tmp_path, plan, manager='fix', name='root', **extra):
    harness = _harness()
    out = tmp_path / name
    env = {k: v for k, v in os.environ.items() if k != 'LLAMACPP_CACHE_PROMPT'}
    env.update(AR_HARNESS_ROOT=str(harness), PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE='1',
               TRUNC_PLAN=json.dumps(plan), TRUNC_MANAGER=manager, **{k: str(v) for k, v in extra.items()})
    done = subprocess.run([sys.executable, str(REPO / 'r1/tests/exam_truncation_driver.py'), str(out)],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stdout + done.stderr
    result = json.loads((out / 'result.json').read_text())
    assert result['harness']['commit'] == A3FEDBB
    return result


def _manager(record):
    return ((record.get('extra') or {}).get('manager')) or {}


def _cap_sent(body):
    """The cap as the pinned client sends it: ``max_completion_tokens`` (or the legacy ``max_tokens``)."""
    return body.get('max_completion_tokens', body.get('max_tokens'))


TRUNCATING = ('length_partial', 'length_full', 'length_empty', 'content_filter')


def test_pin_proposer_crashes_on_a_length_truncated_reply(tmp_path):
    """Reproduces the STOP shape at the old ``exam_manager`` (plain harness proposer, no cap)."""
    r = _drive(tmp_path, ['stop', 'length_partial'], manager='pin')
    assert r['error'] is not None and r['error']['type'] == 'LengthFinishReasonError' and r['error']['module'] == 'openai'
    failed = [e['payload'] for e in r['events'] if e['event_type'] == 'llm_call_failed']
    assert len(failed) == 1 and failed[0]['error_type'] == 'LengthFinishReasonError'
    assert failed[0]['transport_attempts'][0]['error_class'] == 'non_retryable'
    assert not any(e['event_type'] == 'campaign_completed' for e in r['events'])
    assert all(_cap_sent(q['body']) is None for q in r['requests'])      # the pin sent no cap


def test_truncated_replies_are_invalid_trials_and_the_campaign_continues(tmp_path):
    plan = ['stop', 'length_partial', 'length_full', 'stop', 'content_filter', 'length_empty']
    r = _drive(tmp_path, plan)
    assert r['error'] is None
    assert sum(e['event_type'] == 'campaign_completed' for e in r['events']) == 1
    assert not any(e['event_type'] == 'llm_call_failed' for e in r['events'])
    # every request carries the cap and cache_prompt false
    assert r['requests'] and all(_cap_sent(q['body']) == CAP for q in r['requests'])
    assert all(q['body']['cache_prompt'] is False for q in r['requests'])
    assert r['cache_stop'] is None and r['manifest_cache_prompt']['all_false'] is True
    # one trial per request, in order; each charged one LLM call
    records = r['records']
    assert len(records) == len(r['requests'])
    llm_events = [e['payload'] for e in r['events'] if e['event_type'] == 'llm_call']
    assert len(llm_events) == len(r['requests'])
    for q, rec, event in zip(r['requests'], records, llm_events):
        call = _manager(rec)['llm_call']
        assert call['max_completion_tokens'] == CAP and event['max_completion_tokens'] == CAP
        assert call == event                                              # the event copies the record
        if q['kind'] in TRUNCATING:
            assert rec['decision'] == 'failed_invalid'
            assert rec['failure_category'] == 'proposal_precondition_failed'
            assert _manager(rec)['parse_failed'] is True and not _manager(rec).get('structured_edit')
            assert call['truncated'] is True and call['parse_ok'] is False
            assert call['truncation_policy'] == 'b1_truncated_output_invalid/v1'
            assert call['finish_reason'] == ('content_filter' if q['kind'] == 'content_filter' else 'length')
            assert call['truncation_error_type'] == ('ContentFilterFinishReasonError' if q['kind'] == 'content_filter'
                                                     else 'LengthFinishReasonError')
            assert call['completion_tokens'] == (9 if q['kind'] == 'content_filter' else CAP)
            assert call['prompt_tokens'] == 7 and call['response_chars'] == 0
            assert ((rec.get('extra') or {}).get('worker') or {}).get('worker_skipped') is True   # no worker run
        else:
            assert rec['decision'] != 'failed_invalid'
            assert call['truncated'] is False and call['finish_reason'] == 'stop' and call['parse_ok'] is True
            assert not (set(call) & (ADDED_KEYS - {'max_completion_tokens', 'finish_reason', 'truncated'}))
    # a complete proposal that was cut short is still discarded
    full = records[plan.index('length_full')]
    assert _manager(full)['llm_call']['discarded_content_chars'] > 0


def test_truncated_calls_are_charged_to_the_llm_budget(tmp_path):
    """Every reply truncated, trial budget 20 > LLM cap 5: the root ends normally after exactly 5 calls."""
    r = _drive(tmp_path, ['length_empty'] * 30, TRUNC_TRIALS=20, TRUNC_LLM_CAP=5)
    assert r['error'] is None and sum(e['event_type'] == 'campaign_completed' for e in r['events']) == 1
    assert len(r['requests']) == 5 and len(r['records']) == 5
    assert all(rec['decision'] == 'failed_invalid' for rec in r['records'])
    assert all(_manager(rec)['llm_call']['truncated'] is True for rec in r['records'])
    assert all(((rec.get('extra') or {}).get('worker') or {}).get('worker_skipped') is True for rec in r['records'])


def test_with_an_observer_truncated_trials_make_no_observer_call_and_the_budget_balances(tmp_path):
    """With an A4-shaped observer the harness reports compute_budget: every charge has its llm_call event."""
    r = _drive(tmp_path, ['stop', 'length_partial', 'stop', 'length_empty'], TRUNC_OBSERVER=1)
    assert r['error'] is None
    budget = [e['payload'] for e in r['events'] if e['event_type'] == 'campaign_completed'][0]['compute_budget']
    llm_events = [e for e in r['events'] if e['event_type'] == 'llm_call']
    assert budget['llm_calls'] == len(llm_events) == budget['max_llm_calls'] == 8
    assert budget['worker_runs'] == 3
    observed = {e['trial_id'] for e in r['events'] if e['event_type'] == 'exam_self_forecast'}
    truncated = {rec['trial_id'] for rec in r['records'] if _manager(rec)['llm_call'].get('truncated')}
    assert len(truncated) == 2 and not (observed & truncated)
    proposer = [e for e in llm_events if 'purpose' not in e['payload']]
    assert len(proposer) == len(r['requests']) and all(e['payload']['max_completion_tokens'] == CAP for e in proposer)


def test_a_truncated_d25_revision_is_the_invalid_final_proposal(tmp_path):
    """openml_credit_approval has D25 active keys; the stand-in names an inactive key at trial 3 and the
    revision request is cut short: the revision goes through the guard and the trial is invalid."""
    r = _drive(tmp_path, ['stop', 'stop', 'stop', 'length_empty'], TRUNC_NODE='openml_credit_approval')
    assert r['error'] is None
    rejected = [e for e in r['events'] if e['event_type'] == 'proposal_rejected_inactive_key']
    assert rejected and rejected[0]['trial_id'].endswith('trial-003')
    t3 = [rec for rec in r['records'] if rec['trial_id'].endswith('trial-003')][0]
    calls = [e['payload'] for e in r['events'] if e['event_type'] == 'llm_call' and e['trial_id'] == t3['trial_id']]
    assert len(calls) == 2 and calls[0]['truncated'] is False and calls[1]['truncated'] is True
    assert _manager(t3)['llm_call'] == calls[1] and t3['decision'] == 'failed_invalid'
    assert r['requests'][3]['kind'] == 'length_empty' and _cap_sent(r['requests'][3]['body']) == CAP


def test_usage_script_reads_harness_shaped_roots(tmp_path):
    """r1/scripts/b1_completion_usage.py on real harness output (observer and D25 events included)."""
    import hashlib
    from r1.scripts import b1_completion_usage as u
    tree = tmp_path / 'tree'
    completed, requests = {}, {}
    for name, node, extra, plan in (('obs', 'digits_mlp', {'TRUNC_OBSERVER': 1}, ['stop', 'length_partial']),
                                    ('d25', 'openml_credit_approval', {}, ['stop', 'stop', 'stop', 'length_empty'])):
        r = _drive(tmp_path, plan, name=name, TRUNC_NODE=node, **extra)
        requests[name] = len(r['requests'])
        rel = f'cand_{name}/b1/on/{node}__s9001'
        d = tree / rel
        d.mkdir(parents=True)
        for fname in ('root_events.jsonl', 'root_trials.jsonl'):
            (d / fname).write_bytes((tmp_path / name / fname).read_bytes())
        (d / 'campaign_manifest.json').write_text('{}')
        completed[rel] = {'path': f'/w/{rel}/campaign_manifest.json',
                          'sha256': hashlib.sha256(b'{}').hexdigest()}
    (tree / 'batch_state.json').write_text(json.dumps({'completed': completed}))
    res = u.analyse(tree, CAP)
    rows = {r['root'].split('/')[0]: r for r in res['roots']}
    assert rows['cand_obs']['observer_calls'] == 3 and rows['cand_obs']['truncated'] == 1
    assert rows['cand_obs']['llm_calls'] == requests['obs'] and rows['cand_d25']['llm_calls'] == requests['d25']
    assert rows['cand_d25']['truncated'] == 1 and res['cap_check'] == 'FAIL'   # truncated calls sit at the cap


def test_other_failures_still_stop_the_root(tmp_path):
    r = _drive(tmp_path, ['stop', 'http500'])
    assert r['error'] is not None and r['error']['type'] != 'LengthFinishReasonError'
    failed = [e['payload'] for e in r['events'] if e['event_type'] == 'llm_call_failed']
    assert len(failed) == 1 and not any(e['event_type'] == 'campaign_completed' for e in r['events'])


def _stable(record):
    m = _manager(record)
    call = {k: v for k, v in (m.get('llm_call') or {}).items() if k not in ADDED_KEYS | {'latency_ms'}}
    return (record['budget_index'], record['decision'], record['failure_category'], record['delta_vs_best'],
            json.dumps(record['parsed_metrics'], sort_keys=True), m.get('context_sha256'),
            m.get('raw_proposal_sha256'), json.dumps(m.get('structured_edit'), sort_keys=True),
            json.dumps(call, sort_keys=True))


def test_valid_replies_are_unchanged_apart_from_the_cap(tmp_path):
    """Without truncation the fix changes only the cap in the request and the added record fields."""
    fix = _drive(tmp_path, [], manager='fix', name='fix')
    pin = _drive(tmp_path, [], manager='pin', name='pin')
    assert fix['error'] is None and pin['error'] is None
    strip = lambda q: {k: v for k, v in q['body'].items() if k not in ('max_completion_tokens', 'max_tokens')}
    assert [strip(q) for q in fix['requests']] == [strip(q) for q in pin['requests']]
    assert [_stable(r) for r in fix['records']] == [_stable(r) for r in pin['records']]
    assert len(fix['records']) == len(pin['records']) > 0


# ------------------------------------------------------------------ unit level (no harness pin needed beyond import)
class _Model:
    def __init__(self, reply=None, exc=None):
        self.reply, self.exc, self.seen = reply, exc, []

    def invoke(self, messages, *args, **kwargs):
        self.seen.append((messages, args, kwargs))
        if self.exc is not None:
            raise self.exc
        return self.reply


def _module():
    from r1.harness import import_harness
    try:
        import_harness()
    except RuntimeError:
        pytest.skip('harness not importable; set AR_HARNESS_ROOT')
    from r1.exam import b1_llm_truncation
    return b1_llm_truncation


def test_guard_turns_a_returned_length_reply_into_an_empty_reply():
    """The non-parsing path: a reply with finish_reason length is returned, not raised."""
    t = _module()
    from langchain_core.messages import AIMessage
    reply = AIMessage(content='{"summary": "x"', response_metadata={'finish_reason': 'length'},
                      usage_metadata={'input_tokens': 3, 'output_tokens': 11, 'total_tokens': 14})
    guard = t.TruncationGuard(_Model(reply), 99)
    out = guard.invoke(['m'], seed=5)
    assert out.content == '' and out.usage_metadata['output_tokens'] == 11
    assert guard.outcome == {'finish_reason': 'length', 'truncated': True, 'truncation_error_type': None,
                             'discarded_content_chars': len(reply.content), 'discarded_reasoning_chars': 0}
    assert guard.model.seen == [(['m'], (), {'seed': 5})]


def test_guard_passes_a_complete_reply_through_unchanged():
    t = _module()
    from langchain_core.messages import AIMessage
    reply = AIMessage(content='{}', response_metadata={'finish_reason': 'stop'})
    guard = t.TruncationGuard(_Model(reply), 99)
    assert guard.invoke(['m']) is reply and guard.outcome == {'finish_reason': 'stop', 'truncated': False}


def test_guard_does_not_swallow_other_errors():
    t = _module()
    guard = t.TruncationGuard(_Model(exc=ValueError('boom')), 99)
    with pytest.raises(ValueError):
        guard.invoke(['m'])


def test_cap_constant_and_validation():
    t = _module()
    assert t.B1_MAX_COMPLETION_TOKENS == CAP
    for bad in (0, -1, True, 1.5, '16384'):
        with pytest.raises(ValueError):
            t.B1CappedLangGraphManager(model='llamacpp/x', proposal_schema='manager_proposal/v1',
                                       transport_retry=None, max_completion_tokens=bad)
