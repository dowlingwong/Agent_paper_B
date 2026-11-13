"""Synthetic tests for r1/scripts/b1_completion_usage.py (R1-EXAM-B1-TRUNCATION-INVALID). AI-assisted (Claude).

The event shapes follow harness a3fedbb: a proposer ``llm_call`` per first proposal and per D25 revision, the
record keeping the last one; a D25-skipped record without ``llm_call``; after each observation an
``exam_self_forecast`` event plus an ``llm_call`` event with ``purpose: self_forecast``."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from r1.scripts import b1_completion_usage as u

HOST = '/home/dowling/exam-x/work/b1_x'


def _write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))


def _call(c, i, **extra):
    return {'completion_tokens': c, 'prompt_tokens': 1000 + i, 'latency_ms': 100.0 * c / 44.0 if c else 1.0,
            'cache_prompt': False, **extra}


def _root(tree: Path, rel: str, trials, *, failed=None, manifest=True):
    """trials: list of dicts {calls: [completion...], skip: bool, observer: (completion, ms) | None}."""
    d = tree / rel
    events, records = [], []
    for i, t in enumerate(trials, 1):
        tid = f'{rel.split("/")[-1]}-trial-{i:03d}'
        calls = [_call(c, i, **({'truncated': True} if c == 16384 else {})) for c in t['calls']]
        for n, call in enumerate(calls):
            events.append({'event_type': 'llm_call', 'trial_id': tid, 'payload': call})
            if n < len(calls) - 1:
                events.append({'event_type': 'proposal_rejected_inactive_key', 'trial_id': tid, 'payload': {'revision': n}})
        manager = {} if t.get('skip') else {'llm_call': dict(calls[-1])}
        records.append({'trial_id': tid, 'budget_index': i, 'decision': 'skipped' if t.get('skip') else 'kept',
                        'extra': {'manager': manager}})
        if t.get('observer'):
            c, ms = t['observer']
            body = base64.b64encode(json.dumps({'usage': {'completion_tokens': c}, 'timings': {'predicted_ms': ms}}).encode()).decode()
            answer = {'status': 'ok', 'llm_calls': 1, 'request_evidence': {'response_body_b64': body}}
            events.append({'event_type': 'exam_self_forecast', 'trial_id': tid, 'payload': answer})
            events.append({'event_type': 'llm_call', 'trial_id': tid,
                           'payload': {'purpose': 'self_forecast', 'llm_calls': 1, 'schema_version': 'exam_self_forecast/v1', **answer}})
    if failed:
        events.append({'event_type': 'llm_call_failed', 'trial_id': 'tX', 'payload': {
            'error_type': 'LengthFinishReasonError',
            'error': f'... CompletionUsage(completion_tokens={failed}, prompt_tokens=1217, total_tokens={failed + 1217}, ...'}})
    _write_rows(d / 'root_events.jsonl', events)
    _write_rows(d / 'root_trials.jsonl', records)
    if manifest:
        (d / 'campaign_manifest.json').write_text(json.dumps({'root': rel}))
    return d


def _tree(tmp_path, *, peak=9000):
    tree = tmp_path / 'roots'
    a = _root(tree, 'qwen38_27b/b1/on/digits_mlp__s9001',
              [{'calls': [300], 'observer': (200, 4100.0)}, {'calls': [peak], 'observer': (900, 20500.0)}, {'calls': [500]}])
    c = _root(tree, 'qwen25_coder_7b/b1/off/openml_credit_approval__s9001',
              [{'calls': [120]}, {'calls': [110, 130]},                 # D25 revision: the record keeps 130
               {'calls': [100, 90, 95], 'skip': True}])                 # D25 skip: no ledger llm_call
    b = _root(tree, 'scripted/b1/off/digits_mlp__s9001', [])
    _root(tree, 'qwen36_27b/b1/on/openml_credit_approval__s9001', [{'calls': [400]}, {'calls': [31550]}],
          failed=31551, manifest=False)
    completed = {}
    for d in (a, b, c):
        rel = d.relative_to(tree).as_posix()
        completed[rel] = {'path': f'{HOST}/{rel}/campaign_manifest.json',
                          'sha256': hashlib.sha256((d / 'campaign_manifest.json').read_bytes()).hexdigest()}
    (tree / 'batch_state.json').write_text(json.dumps({'completed': completed}))
    return tree


def test_table_and_cap_check(tmp_path, capsys):
    tree = _tree(tmp_path)
    assert u.main(['--roots', str(tree)]) == 0
    out = capsys.readouterr().out.splitlines()
    res = json.loads(out[-1])
    assert res['cap'] == 16384 and res['completed_roots'] == 3 and res['completed_llm_roots'] == 2
    assert res['max_completion_tokens_completed'] == 9000 and res['cap_check'] == 'PASS' and res['margin_tokens'] == 16384 - 9000
    rows = {r['root']: r for r in res['roots']}
    a = rows['qwen38_27b/b1/on/digits_mlp__s9001']
    assert (a['llm_calls'], a['max_prompt_tokens'], a['calls_over_thinking_budget'], a['truncated']) == (3, 1003, 1, 0)
    assert (a['observer_calls'], a['observer_bodies'], a['observer_max_completion_tokens'], a['observer_max_predicted_s']) == (2, 2, 900, 20.5)
    c = rows['qwen25_coder_7b/b1/off/openml_credit_approval__s9001']
    assert (c['llm_calls'], c['max_completion_tokens'], c['trials']) == (6, 130, 3)   # revisions and skip counted
    f = rows['qwen36_27b/b1/on/openml_credit_approval__s9001']
    assert f['completed'] is False and f['failed_calls'][0]['completion_tokens'] == 31551   # not in the cap check
    assert rows['scripted/b1/off/digits_mlp__s9001']['software_anchor'] is True
    modes = {(m['candidate'], m['mode']): m for m in res['candidate_modes']}
    q = modes[('qwen38_27b', 'on')]
    assert abs(q['tokens_per_s'] - 440.0) < 1e-6                        # 100 ms per 44 tokens in the fixture
    assert abs(q['all_capped_root_hours_at_80_calls'] - 80 * 16384 / 440.0 / 3600) < 1e-9
    assert abs(q['observer_timeout_tokens'] - u.OBSERVER_TIMEOUT_S * 440.0) < 1e-6 and u.OBSERVER_TIMEOUT_S == 180.0
    assert ('scripted', 'off') not in modes


def test_truncated_calls_are_counted(tmp_path, capsys):
    tree = tmp_path / 'roots'
    d = _root(tree, 'qwen36_27b/b1/on/openml_credit_approval__s9002', [{'calls': [400]}, {'calls': [16384]}, {'calls': [120, 16384]}])
    rel = d.relative_to(tree).as_posix()
    (tree / 'batch_state.json').write_text(json.dumps({'completed': {'k': {
        'path': f'{HOST}/{rel}/campaign_manifest.json',
        'sha256': hashlib.sha256((d / 'campaign_manifest.json').read_bytes()).hexdigest()}}}))
    assert u.main(['--roots', str(tree)]) == 1                          # in a capped run a FAIL is expected
    res = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert res['roots'][0]['truncated'] == 2 and res['candidate_modes'][0]['truncated'] == 2


def test_cap_check_fails_at_or_above_the_cap(tmp_path, capsys):
    assert u.main(['--roots', str(_tree(tmp_path, peak=16384))]) == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1])['cap_check'] == 'FAIL'


def test_refuses_inconsistent_inputs(tmp_path):
    tree = _tree(tmp_path)
    (tree / 'scripted/b1/off/digits_mlp__s9001/campaign_manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='batch-state SHA-256'):
        u.analyse(tree, 16384)
    tree = _tree(tmp_path / 'b')
    p = tree / 'qwen38_27b/b1/on/digits_mlp__s9001/root_trials.jsonl'
    p.write_text(p.read_text().replace('"completion_tokens": 300', '"completion_tokens": 301'))
    with pytest.raises(ValueError, match='last proposer event'):
        u.analyse(tree, 16384)
    tree = _tree(tmp_path / 'c')
    state = json.loads((tree / 'batch_state.json').read_text())
    state['completed']['k'] = {'path': f'{HOST}/qwen25_coder_7b/b1/off/digits_mlp__s9002/campaign_manifest.json', 'sha256': 'x'}
    (tree / 'batch_state.json').write_text(json.dumps(state))
    with pytest.raises(ValueError, match='without events'):
        u.analyse(tree, 16384)
    tree = _tree(tmp_path / 'd')
    p = tree / 'qwen38_27b/b1/on/digits_mlp__s9001/root_events.jsonl'
    rows = [json.loads(s) for s in p.read_text().splitlines()]
    rows = [r for r in rows if not (r['event_type'] == 'llm_call' and r['payload'].get('purpose'))][:]  # drop observer llm_call
    p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    with pytest.raises(ValueError, match='observer forecasts'):
        u.analyse(tree, 16384)
    tree = _tree(tmp_path / 'e')
    p = tree / 'qwen38_27b/b1/on/digits_mlp__s9001/root_events.jsonl'
    p.write_text(p.read_text() + json.dumps({'event_type': 'llm_call', 'trial_id': 'ghost', 'payload': _call(5, 9)}) + '\n')
    with pytest.raises(ValueError, match='not in the ledger'):
        u.analyse(tree, 16384)


def test_default_cap_matches_the_proposer_constant():
    from r1.harness import import_harness
    try:
        import_harness()
    except RuntimeError:
        pytest.skip('harness not importable; set AR_HARNESS_ROOT')
    from r1.exam.b1_llm_truncation import B1_MAX_COMPLETION_TOKENS
    assert u.DEFAULT_CAP == B1_MAX_COMPLETION_TOKENS


def test_context_overflow_calls_have_no_usage_and_are_counted(tmp_path, capsys):
    """R1-EXAM-B1-MODEL-OUTPUT-INVALID: an overflow call records no completion_tokens; it is counted, not refused."""
    tree = tmp_path / 'roots'
    rel = 'olmo31_32b/b1/off/openml_credit_approval__s9002'
    d = _root(tree, rel, [{'calls': [120]}, {'calls': [130]}])
    p = d / 'root_events.jsonl'
    rows = [json.loads(s) for s in p.read_text().splitlines()]
    overflow = {'completion_tokens': None, 'prompt_tokens': None, 'latency_ms': 5.0, 'cache_prompt': False,
                'context_overflow': True, 'truncated': False}
    rows.append({'event_type': 'llm_call', 'trial_id': f'{rel.split("/")[-1]}-trial-003', 'payload': overflow})
    p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    trials = d / 'root_trials.jsonl'
    trials.write_text(trials.read_text() + json.dumps({'trial_id': f'{rel.split("/")[-1]}-trial-003', 'budget_index': 3,
                                                        'decision': 'failed_invalid',
                                                        'extra': {'manager': {'llm_call': overflow}}}) + '\n')
    (tree / 'batch_state.json').write_text(json.dumps({'completed': {'k': {
        'path': f'{HOST}/{rel}/campaign_manifest.json',
        'sha256': hashlib.sha256((d / 'campaign_manifest.json').read_bytes()).hexdigest()}}}))
    assert u.main(['--roots', str(tree)]) == 0
    row = json.loads(capsys.readouterr().out.splitlines()[-1])['roots'][0]
    assert row['context_overflow'] == 1 and row['llm_calls'] == 3 and row['llm_calls_without_usage'] == 0


def test_report_header_names_the_observer_timeout(tmp_path, capsys):
    """R1-EXAM-B1-OBSERVER-TIMEOUT review S1: the per-candidate table names the timeout it is computed for."""
    tree = tmp_path / 'roots'
    rel = 'qwen38_27b/b1/on/digits_mlp__s9001'
    d = _root(tree, rel, [{'calls': [120]}])
    (tree / 'batch_state.json').write_text(json.dumps({'completed': {'k': {
        'path': f'{HOST}/{rel}/campaign_manifest.json',
        'sha256': hashlib.sha256((d / 'campaign_manifest.json').read_bytes()).hexdigest()}}}))
    assert u.main(['--roots', str(tree)]) == 0
    text = capsys.readouterr().out
    assert 'observer reply tokens at 180 s' in text and 'at 60 s' not in text
