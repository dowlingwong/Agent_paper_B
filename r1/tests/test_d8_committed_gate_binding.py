"""Synthetic D8 authority tests: no data files, models, or repositories are read."""
import hashlib
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from r1.c3 import analysis_guard as guard

HEAD = 'a' * 40
CODE = 'c' * 40
GATE = b'synthetic gate\n'
SHA = hashlib.sha256(GATE).hexdigest()
DECISION = (f'Gate code `r1/c3/gate.py` @ `{CODE}`, sha256 `{SHA}`, '
            'implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); '
            'T0 and T1 pooled with tier as a stratum. '
            'If only some T1 nodes have labels by B.7, read the gate on T0 plus the available '
            'labelled T1 nodes and disclose the node count. '
            'For leave-one-suite-out, each suite must have at least one labelled T1 node, '
            'otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. '
            'Existing preregistration and analysis gates remain in force. '
            'Sweep-2 label tables may be analysed from this row on.')
PLAN = (f'## 10. Author decisions\n### 5 November 2026 (author)\n'
        f'| ID | Decision |\n|---|---|\n'
        f'| R1-BX-D8-CONFIRM | {DECISION} |\n').encode()


def invoke(*, committed_gate=GATE, work_gate=GATE, committed_plan=PLAN,
           work_plan=PLAN, missing_gate=False, head_after=HEAD,
           gate_mode=b'100644', plan_mode=b'100644', symlink=None,
           code_gate=GATE, code_mode=b'100644', ancestor=True):
    calls = []

    def git(argv, **kwargs):
        action = argv[3:]
        calls.append(action)
        if action == ['rev-parse', '--verify', 'HEAD']:
            if sum(x[0] == 'rev-parse' for x in calls) == 2:
                assert ['read', '/synthetic/docs/r1/PLAN.md'] in calls
                assert ['read', '/synthetic/r1/c3/gate.py'] in calls
                return head_after.encode() + b'\n'
            return HEAD.encode() + b'\n'
        if action == ['ls-tree', '-z', HEAD, '--', 'docs/r1/PLAN.md', 'r1/c3/gate.py']:
            oid = b'c' * 40
            return (plan_mode+b' blob '+oid+b'\tdocs/r1/PLAN.md\0' +
                    gate_mode+b' blob '+oid+b'\tr1/c3/gate.py\0')
        if action == ['merge-base', '--is-ancestor', CODE, HEAD]:
            if not ancestor:
                raise subprocess.CalledProcessError(1, argv)
            return b''
        if action == ['ls-tree', '-z', CODE, '--', 'r1/c3/gate.py']:
            return code_mode+b' blob '+b'c'*40+b'\tr1/c3/gate.py\0'
        if action == ['show', CODE + ':r1/c3/gate.py']:
            return code_gate
        if action == ['show', HEAD + ':docs/r1/PLAN.md']:
            return committed_plan
        if action == ['show', HEAD + ':r1/c3/gate.py']:
            if missing_gate:
                raise subprocess.CalledProcessError(128, argv)
            return committed_gate
        raise AssertionError(argv)

    def read_bytes(path):
        calls.append(['read', str(path)])
        if path == Path('/synthetic/r1/c3/gate.py'):
            return work_gate
        if path == Path('/synthetic/docs/r1/PLAN.md'):
            return work_plan
        raise AssertionError(path)

    with patch.object(guard, 'REPO', Path('/synthetic')), \
         patch.object(guard, 'refuse_sealed'), \
         patch.object(Path, 'is_file', return_value=True), \
         patch.object(Path, 'is_symlink', lambda path: str(path) == symlink), \
         patch.object(Path, 'read_bytes', read_bytes), \
         patch.object(guard.subprocess, 'check_output', side_effect=git):
        return guard.require_d8_confirmation()


def test_exact_committed_gate_and_affirmative_plan_succeed():
    assert invoke() is None


def test_untracked_gate_is_rejected_even_if_decision_names_its_hash():
    with pytest.raises(RuntimeError, match='committed PLAN or regular gate code unavailable'):
        invoke(missing_gate=True)


def test_uncommitted_gate_matching_decision_is_rejected():
    with pytest.raises(RuntimeError, match='gate SHA source differs from committed HEAD'):
        invoke(committed_gate=b'older committed gate\n')


def test_uncommitted_plan_is_rejected():
    with pytest.raises(RuntimeError, match='PLAN differs from committed HEAD'):
        invoke(work_plan=PLAN+b'changed\n')


def test_head_change_is_rejected():
    with pytest.raises(RuntimeError, match='HEAD changed'):
        invoke(head_after='b'*40)


@pytest.mark.parametrize('which', ['gate', 'plan'])
def test_committed_symlink_mode_is_rejected(which):
    args = {'gate_mode': b'120000'} if which == 'gate' else {'plan_mode': b'120000'}
    with pytest.raises(RuntimeError, match='committed PLAN or regular gate code unavailable'):
        invoke(**args)


@pytest.mark.parametrize('path', ['/synthetic/r1/c3/gate.py', '/synthetic/docs/r1/PLAN.md'])
def test_checkout_symlink_is_rejected(path):
    with pytest.raises(RuntimeError, match='symlink or alias'):
        invoke(symlink=path)


def test_negative_decision_cannot_open_guard_even_if_hash_matches():
    negative = PLAN.replace(b'Gate code ', b'NOT APPROVED: Gate code ')
    with pytest.raises(RuntimeError, match='exact affirmative'):
        invoke(committed_plan=negative, work_plan=negative)


@pytest.mark.parametrize('mutation', [
    lambda value: value + b' not approved',
    lambda value: value.replace(b'analysed from this row on.', b'not analysed from this row on.'),
    lambda value: value.replace(SHA.encode(), b'f'*64),
    lambda value: value.replace(b'r1/c3/gate.py', b'r1/c3/other.py'),
    lambda value: value.replace(b' and disclose the node count', b''),
    lambda value: value.replace(b'For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. ', b''),
    lambda value: value.replace(b'Existing preregistration and analysis gates remain in force. ', b''),
    lambda value: value.replace(b'T0 plus the available labelled T1 nodes', b'T0 only'),
])
def test_inexact_negative_extra_prose_or_wrong_hash_cannot_authorize(mutation):
    altered = PLAN.replace(DECISION.encode(), mutation(DECISION.encode()))
    with pytest.raises(RuntimeError, match='exact affirmative'):
        invoke(committed_plan=altered, work_plan=altered)


def test_declared_code_commit_must_be_ancestor_and_match():
    with pytest.raises(RuntimeError, match='committed PLAN or regular gate code unavailable'):
        invoke(ancestor=False)
    with pytest.raises(RuntimeError, match='declared gate commit does not match'):
        invoke(code_gate=b'different gate')
    with pytest.raises(RuntimeError, match='committed PLAN or regular gate code unavailable'):
        invoke(code_mode=b'120000')


def test_duplicate_decision_rows_refused_including_later_revocation():
    for extra in (DECISION, 'not approved '+SHA):
        plan = PLAN + f'| R1-BX-D8-CONFIRM | {extra} |\n'.encode()
        with pytest.raises(RuntimeError, match='exact affirmative'):
            invoke(committed_plan=plan, work_plan=plan)
