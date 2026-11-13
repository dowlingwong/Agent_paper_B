"""R1-EXAM-B1-MODEL-OUTPUT-INVALID (13 Nov 2026): every B1 STOP or uncaught exception that a model output can
trigger is an invalid trial instead (not executed, charged), and every proposal is journalled before execution.

Regression for B1 run 4b31_20261112_c, a STOP at the worker guard when the objective's directive and the structured
edit differed. One test, or a named existing test, per item of the inventory in
``reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md`` §3 (M1–M18).

End-to-end tests drive an exam-shaped root through the pinned harness against the stand-in llama-server of
``exam_truncation_driver.py``. They need harness a3fedbb (``AR_HARNESS_B1_ROOT``) and skip without it unless
``R1_REQUIRE_B1_HARNESS=1``. ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from r1.tests.test_exam_b1_truncation import _drive, _manager, _stable, CAP
from r1.tests.test_exam_b1_truncation import _harness as _pinned_harness

PRECHECK = [  # (stand-in kind, node, expected check)
    ('no_directive', 'digits_mlp', 'directive_missing'),                         # M5
    ('sym_not_editable', 'digits_mlp', 'directive_symbol_not_editable'),         # M6 (the 4b31 trial-020 class)
    ('sym_not_editable', 'openml_credit_approval', 'directive_symbol_not_editable'),
    ('sym_differs', 'digits_mlp', 'directive_symbol_differs'),                   # M6
    ('old_differs', 'digits_mlp', 'directive_old_differs'),                      # M7
    ('new_differs', 'openml_credit_approval', 'directive_new_differs'),          # M7
    ('backslash', 'openml_credit_approval', 'replacement_escape'),               # M8
    ('py_long', 'digits_mlp', 'python_value_too_long'),                          # M9
    ('py_nonliteral', 'digits_mlp', 'python_value_not_literal'),                 # M9
    ('py_nonfinite', 'digits_mlp', 'python_value_not_finite_number'),            # M9
    ('py_bool', 'digits_mlp', 'python_value_not_finite_number'),                 # M9
]


def _trial(r, n):
    return [rec for rec in r['records'] if rec['trial_id'].endswith(f'trial-{n:03d}')][0]


@pytest.mark.parametrize('kind,node,check', PRECHECK, ids=[f'{k}-{n}' for k, n, _ in PRECHECK])
def test_model_output_fault_is_an_invalid_trial_not_executed_and_charged(tmp_path, kind, node, check):
    # trial 2 carries the fault (the stand-in's D25 inactive proposal on openml nodes is at trial 3)
    r = _drive(tmp_path, ['stop', kind, 'stop', 'stop', 'stop', 'stop'], TRUNC_NODE=node, TRUNC_ASSERT_JOURNAL=1)
    assert r['error'] is None, r['error']
    assert sum(e['event_type'] == 'campaign_completed' for e in r['events']) == 1
    bad = _trial(r, 2)
    m = _manager(bad)
    assert bad['decision'] == 'failed_invalid' and bad['failure_category'] == 'proposal_precondition_failed'
    assert (bad['extra'].get('worker') or {}).get('worker_skipped') is True             # not executed
    assert m['proposal_precondition_failed'] is True and 'structured_edit' not in m
    rej = m['b1_model_output_rejected']
    assert rej['check'] == check and rej['policy'] == 'b1_model_output_invalid/v1' and isinstance(rej['structured_edit'], dict)
    assert m['llm_call']['max_completion_tokens'] == CAP                              # one LLM call, charged
    calls = [e for e in r['events'] if e['event_type'] == 'llm_call' and e['trial_id'] == bad['trial_id']]
    assert len(calls) == 1
    # the journal holds the proposal before execution, with the same verdict
    rows = [j for j in r['journal'] if j['trial_id'] == bad['trial_id']]
    assert len(rows) == 1 and rows[0]['check'] == 'rejected' and rows[0]['rejection']['check'] == check
    assert rows[0]['structured_edit'] == rej['structured_edit'] and rows[0]['final_structured_edit'] is None
    assert isinstance(rows[0]['objective'], str) and rows[0]['raw_reply']
    ev = r['journal_evidence']
    assert ev['rejected_by_check'] == {check: 1} and ev['rows'] == len(r['requests'])
    # no other proposal was rejected here
    assert not any('b1_model_output_rejected' in _manager(rec) for rec in r['records'] if rec is not bad)


def test_the_4b31_trial_020_shape(tmp_path):
    """openml_credit_approval, structured edit on model_type, objective naming the non-editable alpha."""
    _harness()
    from r1.exam.b1_proposal_precheck import check_model_output
    spec = type('Spec', (), {'editable_symbols': ('C', 'class_weight', 'imputer', 'learning_rate', 'max_depth',
                                                  'max_iter', 'model_type', 'n_estimators', 'scaler')})()
    edit = {'type': 'config_value', 'symbol': 'model_type', 'old': 'logistic_regression', 'new': 'ridge', 'path': 'config.yaml'}
    out = check_model_output('Change alpha from 1.0 to 0.1 after switching to ridge.', edit, spec)
    assert out['check'] == 'directive_symbol_not_editable' and out['directive'] == ['alpha', '1.0', '0.1']
    assert check_model_output('Change model_type from logistic_regression to ridge', edit, spec) is None


def test_rejection_is_final_even_when_the_objective_names_an_inactive_key(tmp_path):
    """Review round 1, finding 1: structured edit on the active C, objective naming the D25-inactive max_depth. The
    rejection must not be turned into a D25 revision (the harness would read the key from the objective)."""
    r = _drive(tmp_path, ['stop', 'mismatch_inactive_objective', 'stop', 'stop'], TRUNC_NODE='openml_credit_approval')
    assert r['error'] is None
    bad = _trial(r, 2)
    m = _manager(bad)
    assert bad['decision'] == 'failed_invalid' and m['b1_model_output_rejected']['check'] == 'directive_symbol_differs'
    assert m['named_param'] == 'C' and (bad['extra'].get('worker') or {}).get('worker_skipped') is True
    rows = [j for j in r['journal'] if j['trial_id'] == bad['trial_id']]
    assert [j['check'] for j in rows] == ['rejected']                                  # no revision
    assert not any(e['event_type'] == 'proposal_rejected_inactive_key' and e['trial_id'] == bad['trial_id']
                   for e in r['events'])
    assert len([e for e in r['events'] if e['event_type'] == 'llm_call' and e['trial_id'] == bad['trial_id']]) == 1


def test_unencodable_reply_is_an_invalid_trial_and_later_prompts_still_work(tmp_path):
    """M20 (review round 1, finding 2): a lone surrogate in a reply field would enter every later prompt via the
    memory summary and make the next request unencodable. It is an invalid trial; the campaign continues."""
    r = _drive(tmp_path, ['stop', 'surrogate', 'stop', 'stop', 'stop'], TRUNC_NODE='digits_mlp')
    assert r['error'] is None and sum(e['event_type'] == 'campaign_completed' for e in r['events']) == 1
    bad = _trial(r, 2)
    call = _manager(bad)['llm_call']
    assert bad['decision'] == 'failed_invalid' and call['unencodable_reply'] is True
    assert call['unencodable_reply_policy'] == 'b1_model_output_invalid/v1' and call['completion_tokens'] == 5
    assert [j['unencodable_reply'] for j in r['journal'] if j['trial_id'] == bad['trial_id']] == [True]
    assert len(r['requests']) >= 3                                                      # later requests were sent


def test_rejected_proposal_makes_no_observer_call(tmp_path):
    """With an A4-shaped observer: the rejected trial has no observer query and the budget balances."""
    r = _drive(tmp_path, ['stop', 'sym_differs', 'stop', 'stop', 'stop'], TRUNC_NODE='digits_mlp', TRUNC_OBSERVER=1)
    assert r['error'] is None
    bad = _trial(r, 2)
    assert 'b1_model_output_rejected' in _manager(bad)
    assert not any(e['event_type'] == 'exam_self_forecast' and e['trial_id'] == bad['trial_id'] for e in r['events'])
    budget = [e['payload'] for e in r['events'] if e['event_type'] == 'campaign_completed'][0]['compute_budget']
    assert budget['llm_calls'] == sum(e['event_type'] == 'llm_call' for e in r['events'])
    assert budget['worker_runs'] == sum(not ((x['extra'].get('worker') or {}).get('worker_skipped')) for x in r['records'])


def test_harness_rejections_are_left_exactly_as_before(tmp_path):
    """A proposal the harness rejects by itself (stale old value) is not touched, even with a bad directive."""
    r = _drive(tmp_path, ['stop', 'stale_and_mismatch', 'stop'], TRUNC_NODE='digits_mlp')
    pin = _drive(tmp_path, ['stop', 'stale_and_mismatch', 'stop'], TRUNC_NODE='digits_mlp', manager='pin', name='pin')
    bad = _trial(r, 2)
    assert bad['decision'] == 'failed_invalid' and 'b1_model_output_rejected' not in _manager(bad)
    assert _manager(bad)['structured_edit']                       # the harness's own precondition failure
    assert [j['check'] for j in r['journal'] if j['trial_id'] == bad['trial_id']] == ['harness_precondition']
    assert [_stable(x) for x in r['records']] == [_stable(x) for x in pin['records']]


def test_d25_inactive_key_is_left_to_the_harness(tmp_path):
    """openml: an inactive key with a bad directive is revised by the harness (D25), not rejected here."""
    r = _drive(tmp_path, ['stop', 'inactive_and_mismatch', 'stop', 'stop', 'stop', 'stop'], TRUNC_NODE='openml_credit_approval')
    assert r['error'] is None
    t2 = [j for j in r['journal'] if j['trial_id'].endswith('trial-002')]
    assert t2[0]['check'] == 'd25_inactive_key' and len(t2) >= 2                    # revised
    assert all(j['revision_attempt'] == i for i, j in enumerate(t2))
    assert 'b1_model_output_rejected' not in _manager(_trial(r, 2))


def test_valid_campaigns_are_unchanged_apart_from_the_journal(tmp_path):
    fix = _drive(tmp_path, [], name='fix', TRUNC_NODE='openml_credit_approval')
    pin = _drive(tmp_path, [], manager='pin', name='pin', TRUNC_NODE='openml_credit_approval')
    assert fix['error'] is None and pin['error'] is None
    assert [_stable(r) for r in fix['records']] == [_stable(r) for r in pin['records']]
    assert not any('b1_model_output_rejected' in _manager(r) for r in fix['records'])
    assert fix['journal_evidence']['outcomes']['rejected'] == 0


def test_parse_failure_and_truncation_stay_invalid(tmp_path):
    """M1 (unparseable reply) and M2 (truncation): harness invalid path, journalled as not_applicable."""
    r = _drive(tmp_path, ['stop', 'length_partial', 'stop'], TRUNC_NODE='digits_mlp')
    assert r['error'] is None and _trial(r, 2)['decision'] == 'failed_invalid'
    assert [j['check'] for j in r['journal'] if j['trial_id'].endswith('002')] == ['not_applicable']
    assert r['journal_evidence']['outcomes']['not_applicable'] == 1


def test_unresolvable_param_stays_a_harness_precondition_failure(tmp_path):
    """M3: a reply naming no editable constant has no structured edit; the harness rejects it as before."""
    r = _drive(tmp_path, ['stop', 'unknown_param', 'stop'], TRUNC_NODE='digits_mlp')
    bad = _trial(r, 2)
    assert r['error'] is None and bad['decision'] == 'failed_invalid'
    assert bad['failure_category'] == 'proposal_precondition_failed' and 'b1_model_output_rejected' not in _manager(bad)
    assert [j['check'] for j in r['journal'] if j['trial_id'] == bad['trial_id']] == ['not_applicable']


def test_prompt_beyond_the_context_is_an_invalid_trial_after_trial_1(tmp_path):
    """M19: the memory summary repeats model text, so the prompt can outgrow the context. After trial 1 that is an
    invalid trial, charged; at trial 1 (no model text in the prompt) it stays a STOP."""
    r = _drive(tmp_path, ['stop', 'ctx_overflow', 'stop', 'stop'], TRUNC_NODE='digits_mlp')
    assert r['error'] is None
    bad = _trial(r, 2)
    call = _manager(bad)['llm_call']
    assert bad['decision'] == 'failed_invalid' and call['context_overflow'] is True and call['truncated'] is False
    assert call['context_overflow_prompt_tokens'] == 40000 and call['context_overflow_policy'] == 'b1_model_output_invalid/v1'
    assert [j['context_overflow'] for j in r['journal'] if j['trial_id'] == bad['trial_id']] == [True]
    first = _drive(tmp_path, ['ctx_overflow'], TRUNC_NODE='digits_mlp', name='first')
    assert first['error'] is not None and 'exceeds the context' in first['error']['message']


def test_other_llm_failures_still_stop(tmp_path):
    """M18: transport failures are not model output; the root still stops."""
    r = _drive(tmp_path, ['stop', 'http500'], TRUNC_NODE='digits_mlp')
    assert r['error'] is not None and not any(e['event_type'] == 'campaign_completed' for e in r['events'])


# ------------------------------------------------------------------ unit level
def _harness():
    """The pinned harness a3fedbb; skips without it unless R1_REQUIRE_B1_HARNESS=1 (then fails)."""
    _pinned_harness()
    from r1.harness import import_harness
    return import_harness()


def _proposal(objective, edit, spec):
    from autoresearch.manager.base import ManagerProposal
    return ManagerProposal(manager_mode='t', proposal_summary='s', proposal_rationale='', target_files=spec.editable_paths,
                           objective=objective, extra={'structured_edit': edit} if edit is not None else {})


UNIT = [  # (objective, edit new, expected check, guard STOP text)
    ('Increase MAX_ITER.', '80', 'directive_missing', None),
    ('Change momentum from 40 to 80', '80', 'directive_symbol_not_editable', 'directive and structured edit differ'),
    ('Change BATCH_SIZE from 40 to 80', '80', 'directive_symbol_differs', 'directive and structured edit differ'),
    ('Change MAX_ITER from 41 to 80', '80', 'directive_old_differs', 'directive and structured edit differ'),
    ('Change MAX_ITER from 40 to 81', '80', 'directive_new_differs', 'directive and structured edit differ'),
    ('Change MAX_ITER from 40 to 8\\1', '8\\1', 'replacement_escape', 'regex escape syntax'),
    ('Change MAX_ITER from 40 to ' + '1' * 300, '1' * 300, 'python_value_too_long', 'bounded numeric literal'),
    ('Change MAX_ITER from 40 to 2*40', '2*40', 'python_value_not_literal', 'not a numeric literal'),
    ('Change MAX_ITER from 40 to 1e999', '1e999', 'python_value_not_finite_number', 'finite numeric literal'),
    ("Change MAX_ITER from 40 to 'x'", "'x'", 'python_value_not_finite_number', 'finite numeric literal'),
]


@pytest.mark.parametrize('objective,new,check,stop', UNIT, ids=[u[2] + str(i) for i, u in enumerate(UNIT)])
def test_precheck_and_worker_guard_agree(objective, new, check, stop):
    """The worker guard keeps its STOP for any proposal that bypasses the pre-check (internal inconsistency)."""
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_proposal_guard import verify_proposal, B1ProposalIntegrityStop
    from r1.exam.b1_proposal_precheck import check_model_output
    spec = load_registered_node('digits_mlp', repo_root=h)
    edit = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': '40', 'new': new, 'path': 'train.py'}
    assert check_model_output(objective, edit, spec)['check'] == check
    with pytest.raises(B1ProposalIntegrityStop) as info:
        verify_proposal(_proposal(objective, edit, spec), spec)
    assert info.value.code.startswith('STOP: B1') and (stop is None or stop in info.value.code)
    good = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': '40', 'new': '80', 'path': 'train.py'}
    assert check_model_output('Change max_iter from 40 to 80', good, spec) is None
    verify_proposal(_proposal('Change max_iter from 40 to 80', good, spec), spec)


def test_typeerror_value_stays_on_the_worker_path_as_before():
    """A .py value that makes ast.literal_eval raise TypeError (``{[]: 1}``) is not rejected by the pre-check: the
    unchanged worker guard lets the TypeError through, which the harness records as an invalid trial (as under _c)."""
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_proposal_guard import verify_proposal
    from r1.exam.b1_proposal_precheck import check_model_output
    spec = load_registered_node('digits_mlp', repo_root=h)
    edit = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': '40', 'new': '{[]:1}', 'path': 'train.py'}
    assert check_model_output('Change MAX_ITER from 40 to {[]:1}', edit, spec) is None
    with pytest.raises(TypeError):
        verify_proposal(_proposal('Change MAX_ITER from 40 to {[]:1}', edit, spec), spec)


def test_worker_guard_path_mismatch_still_stops():
    """M10: the edit path comes from the harness, not the model; a mismatch stays an internal STOP."""
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_proposal_guard import verify_proposal, B1ProposalIntegrityStop
    spec = load_registered_node('digits_mlp', repo_root=h)
    edit = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': '40', 'new': '80', 'path': 'benchmark.py'}
    with pytest.raises(B1ProposalIntegrityStop, match='path differs'):
        verify_proposal(_proposal('Change MAX_ITER from 40 to 80', edit, spec), spec)


def test_real_worker_turns_node_rejections_into_invalid_trials():
    """M11/M12 (and the 4b31 trials 018/019): the pinned worker runs an edit the node rejects; result invalid."""
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_proposal_guard import B1IntegrityWorker
    spec = load_registered_node('digits_mlp', repo_root=h)
    tmp = Path(tempfile.mkdtemp(prefix='b1mo_'))
    try:
        root = tmp / 'node'
        shutil.copytree(h / 'nodes' / 'digits_mlp', root)
        worker = B1IntegrityWorker(node_root=root, artifact_dir=tmp / 'art', train_seed=9001, split_seed=9001)
        cases = [('Change MAX_ITER from 40 to 0', '40', '0'),       # node rejects the value (M12)
                 ('Change MAX_ITER from 39 to 20', '39', '20')]     # stale old value (M11)
        for b, (objective, old, new) in enumerate(cases, 1):
            edit = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': old, 'new': new, 'path': 'train.py'}
            result = worker.run_trial(_proposal(objective, edit, spec), spec, b)
            assert result.success is False
            assert (root / 'train.py').read_text() == (h / 'nodes' / 'digits_mlp' / 'train.py').read_text()
    finally:
        saved = Path('/tmp') / '_to_delete'
        saved.mkdir(exist_ok=True)
        tmp.rename(saved / tmp.name)


def test_missing_worker_reference_stops_at_the_first_checked_proposal(tmp_path):
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_llm_truncation import B1CappedLangGraphManager
    spec = load_registered_node('digits_mlp', repo_root=h)
    mgr = B1CappedLangGraphManager(model='llamacpp/x', proposal_schema='manager_proposal/v1', transport_retry=None)
    edit = {'type': 'python_constant', 'symbol': 'MAX_ITER', 'old': '40', 'new': '80', 'path': 'train.py'}
    status = type('S', (), {'current_constants': {'MAX_ITER': '40'}})()
    with pytest.raises(RuntimeError, match='no worker'):
        mgr._b1_model_output_check(_proposal('Change MAX_ITER from 40 to 80', edit, spec), status, spec)


def _journal_case(tmp_path):
    r = _drive(tmp_path, ['stop', 'sym_not_editable', 'stop'], TRUNC_NODE='digits_mlp', name='jc')
    out = tmp_path / 'jc'
    return out, [json.loads(s) for s in (out / 'root_trials.jsonl').read_text().splitlines()], \
        [json.loads(s) for s in (out / 'root_events.jsonl').read_text().splitlines()]


def test_journal_validation_detects_tampering(tmp_path):
    from r1.exam.b1_proposal_journal import validate_proposal_journal
    out, records, events = _journal_case(tmp_path)
    path = out / 'b1_proposals.jsonl'
    good = path.read_text()
    assert validate_proposal_journal(path, records, events)['outcomes']['rejected'] == 1
    rows = [json.loads(s) for s in good.splitlines()]
    tampered = [
        rows[:-1],                                                                     # a row missing
        [dict(rows[0], raw_proposal_sha256='0' * 64)] + rows[1:],                      # not the recorded proposal
        [rows[0], dict(rows[1], check='passed', rejection=None)] + rows[2:],           # rejection dropped
        [rows[0], dict(rows[1], structured_edit={'symbol': 'X'})] + rows[2:],          # edit differs
        [dict(rows[0], schema='other')] + rows[1:],
    ]
    # a rejected row followed by another call for the same trial (rejections are final)
    extra_row = dict(rows[1], check='passed', rejection=None, revision_attempt=1)
    tampered.append(rows[:2] + [extra_row] + rows[2:])
    for case in tampered:
        path.write_text(''.join(json.dumps(x) + '\n' for x in case))
        with pytest.raises(RuntimeError, match='STOP: B1 proposal journal'):
            validate_proposal_journal(path, records, events)
    path.write_text(good)
    (out / '_to_delete').mkdir()
    path.rename(out / '_to_delete' / path.name)
    with pytest.raises(RuntimeError, match='missing'):
        validate_proposal_journal(path, records, events)


def _real_worker_run(objective, symbol, old, new, *, timeout=None, b=1):
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from r1.exam.b1_proposal_guard import B1IntegrityWorker
    spec = load_registered_node('digits_mlp', repo_root=h)
    tmp = Path(tempfile.mkdtemp(prefix='b1mo_'))
    try:
        root = tmp / 'node'
        shutil.copytree(h / 'nodes' / 'digits_mlp', root)
        kw = {'timeout_seconds': timeout} if timeout is not None else {}
        worker = B1IntegrityWorker(node_root=root, artifact_dir=tmp / 'art', train_seed=9001, split_seed=9001, **kw)
        edit = {'type': 'python_constant', 'symbol': symbol, 'old': old, 'new': new, 'path': 'train.py'}
        return worker.run_trial(_proposal(objective, edit, spec), spec, b)
    finally:
        saved = Path('/tmp') / '_to_delete'
        saved.mkdir(exist_ok=True)
        tmp.rename(saved / tmp.name)


def test_worker_timeout_is_an_invalid_trial():
    """M13: a run past the worker's timeout returns a failure (invalid trial), not an exception."""
    result = _real_worker_run('Change MAX_ITER from 40 to 300', 'MAX_ITER', '40', '300', timeout=0.05)
    assert result.success is False and 'timed out' in (result.failure_message or '')


def test_value_outside_the_declared_range_still_executes():
    """M14 (documented, unchanged): digits_mlp declares allowed_ranges (HIDDEN_UNITS 4-256) but neither the
    harness nor the node enforces them; such a value runs. This pins today's behaviour (author decision)."""
    result = _real_worker_run('Change HIDDEN_UNITS from 32 to 300', 'HIDDEN_UNITS', '32', '300')
    assert result.success is True and 'val_score' in result.parsed_metrics


@pytest.mark.parametrize('path,symbol,old,new', [
    ('train.py', 'MAX_ITER', '40', '80'), ('train.py', 'ALPHA', '1e-4', '5e-4'), ('train.py', 'HIDDEN_UNITS', '32', '64'),
    ('config.yaml', 'C', '0.15', '0.3'), ('config.yaml', 'model_type', 'logistic_regression', 'random_forest'),
    ('config.yaml', 'class_weight', 'balanced', 'None'), ('config.yaml', 'scaler', 'standard', 'minmax')])
def test_worker_and_replay_apply_a_passing_edit_identically(tmp_path, path, symbol, old, new):
    """M16: for an edit that passes the pre-check, the pinned worker's file edit equals the replay's, so the
    post-campaign replay cannot fail on model output; a replay failure stays an internal STOP."""
    h = _harness()
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import _apply_edit
    from r1.c3.features import apply_edit
    from r1.exam.b1_proposal_precheck import check_model_output
    node = 'digits_mlp' if path == 'train.py' else 'openml_credit_approval'
    spec = load_registered_node(node, repo_root=h)
    edit = {'type': 'python_constant' if path == 'train.py' else 'config_value', 'symbol': symbol, 'old': old,
            'new': new, 'path': path}
    assert check_model_output(f'Change {symbol} from {old} to {new}', edit, spec) is None
    source = (h / 'nodes' / node / path).read_text()
    target = tmp_path / path
    target.write_text(source)
    applied = _apply_edit(target, symbol, old, new)
    assert not isinstance(applied, str), applied
    assert target.read_text() == apply_edit({path: source}, edit)[path]

