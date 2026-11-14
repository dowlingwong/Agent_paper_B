"""B2 code unit (14 Nov 2026): the B2_HANDOFF_DRAFT §6 classes fire in phase ``b2`` through ``campaign.collect``.

Each case runs one B2-phase root (seed 9011, audit seeds 9201–9210) through the reviewed B1/B2 collector against a
loopback stand-in (``exam_b2_collect_driver.py``), under the B1/B2 harness pin a3fedbb (``AR_HARNESS_B1_ROOT``).
DRYRUN fixture worker and audits.  The invalid-trial classes are those of R1-EXAM-B1-TRUNCATION-INVALID and
R1-EXAM-B1-MODEL-OUTPUT-INVALID as proposed for B2 (row R1-EXAM-B2-INVALID-TRIALS); the STOP classes stop the root.
STOP classes enforced in the parent runner, the author gate or the worker integrity guard (pins, shas, authority,
host, existing roots, GPU lease, deadline) are covered in ``test_exam_b2_code_unit.py`` and by the phase-agnostic
B1 guard tests.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / 'r1/tests/exam_b2_collect_driver.py'


def run(tmp_path, name, **env):
    harness = os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        if os.environ.get('R1_REQUIRE_B1_HARNESS') == '1': pytest.fail('pinned B1/B2 harness required')
        pytest.skip('set AR_HARNESS_B1_ROOT to the pinned harness')
    head = subprocess.check_output(['git', '-C', harness, 'rev-parse', 'HEAD'], text=True).strip()
    assert head == 'a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    out = tmp_path / name
    full = {**os.environ, 'AR_HARNESS_ROOT': harness, 'PYTHONDONTWRITEBYTECODE': '1',
            **{k: (json.dumps(v) if not isinstance(v, str) else v) for k, v in env.items()}}
    proc = subprocess.run([sys.executable, str(DRIVER), str(out)], env=full, text=True, capture_output=True, timeout=240)
    assert proc.returncode == 0, proc.stderr[-3000:]
    return json.loads((out / 'driver_result.json').read_text())


def test_b2_root_completes_with_the_final_y_audit_and_b1_evidence(tmp_path):
    r = run(tmp_path, 'ok')
    assert r['status'] == 'complete', r['error']
    m = r['manifest']
    assert m['phase'] == 'b2' and m['instance_seed'] == 9011 and m['mode'] == 'off'
    [final] = m['final_audits']
    assert final['seeds'] == list(range(9201, 9211)) and len(final['metrics']) == 10
    assert abs(final['final_y'] - sum(final['metrics']) / 10) < 1e-12
    assert all(a['audit_seeds'] == list(range(9201, 9211)) for a in m['audited_proposals'])
    assert m['cache_prompt']['all_false'] is True and m['observer_evidence']['calls'] > 0
    assert m['proposal_journal']['schema'] == 'b1_proposal_journal/v1'
    assert all(q['body'].get('cache_prompt') is False for q in r['requests'])
    assert all(q['body'].get('max_completion_tokens') == 16384 for q in r['requests'] if not q['observer'])


def test_b2_invalid_trial_classes_are_invalid_trials_charged_and_journalled(tmp_path):
    plan = ['stop', 'length_partial', 'sym_differs', 'no_directive', 'backslash', 'py_long', 'surrogate', 'ctx_overflow']
    r = run(tmp_path, 'invalid', B2_PLAN=plan, B2_TRIALS='16', B2_W='3')
    assert r['status'] == 'complete', r['error']
    decisions = [x['decision'] for x in r['records']]
    assert decisions[1:8] == ['failed_invalid'] * 7          # M2, M7, M5, M8, M9, M20, M19 after trial 1
    rows = {j['budget_index']: j for j in r['journal']}
    assert rows[2]['truncated'] is True                        # M2 under the 16,384 cap
    assert {rows[i]['rejection']['check'] for i in (3, 4, 5, 6)} == \
        {'directive_symbol_differs', 'directive_missing', 'replacement_escape', 'python_value_too_long'}
    assert rows[7]['unencodable_reply'] is True and rows[8]['context_overflow'] is True
    m = r['manifest']
    assert m['proposal_journal']['rejected_by_check'] == {'directive_missing': 1, 'directive_symbol_differs': 1,
                                                          'python_value_too_long': 1, 'replacement_escape': 1}
    # every invalid trial was charged against the LLM budget (one proposer call each, plus observer calls)
    assert m['compute_budget']['llm_calls'] >= len(r['records'])
    assert len(r['journal']) == len(r['records'])


@pytest.mark.parametrize('name,env,status,match', [
    ('m19_trial1', {'B2_PLAN': ['ctx_overflow']}, 'stop', 'first proposer prompt exceeds the context'),
    ('m18_transport', {'B2_PLAN': ['stop', 'http500']}, 'stop', 'Error code: 500'),
    ('observer', {'B2_OBSERVER': 'fail'}, 'observer_stop', 'observer evidence failed'),
    ('m17_audit', {'B2_FAULT': 'audit_none'}, 'stop', 'missing/failed paired audit seeds'),
    ('final_y', {'B2_FAULT': 'final_none'}, 'stop', 'incomplete final Y audit'),
])
def test_b2_stop_classes_stop_the_root(tmp_path, name, env, status, match):
    r = run(tmp_path, name, **env)
    assert r['status'] == status and match in r['error']
    assert r['manifest'] is None                               # nothing is published for a stopped root
