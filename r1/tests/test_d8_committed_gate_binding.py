"""Synthetic D8 authority tests: no data files, models, or repositories are read."""
import hashlib
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from r1.c3 import analysis_guard as guard

HEAD = 'a' * 40
GATE = b'synthetic gate\n'
SHA = hashlib.sha256(GATE).hexdigest()
PLAN = (f'## 10. Author decisions\n### 5 November 2026 (author)\n'
        f'| ID | Decision |\n|---|---|\n'
        f'| R1-BX-D8-CONFIRM | approved gate sha256 {SHA} |\n').encode()


def invoke(*, committed_gate=GATE, work_gate=GATE, committed_plan=PLAN,
           work_plan=PLAN, missing_gate=False, head_after=HEAD):
    calls = []

    def git(argv, **kwargs):
        action = argv[3:]
        calls.append(action)
        if action == ['rev-parse', '--verify', 'HEAD']:
            return (HEAD if sum(x[0] == 'rev-parse' for x in calls) == 1 else head_after).encode() + b'\n'
        if action == ['show', HEAD + ':docs/r1/PLAN.md']:
            return committed_plan
        if action == ['show', HEAD + ':r1/c3/gate.py']:
            if missing_gate:
                raise subprocess.CalledProcessError(128, argv)
            return committed_gate
        raise AssertionError(argv)

    def read_bytes(path):
        if path == Path('/synthetic/r1/c3/gate.py'):
            return work_gate
        if path == Path('/synthetic/docs/r1/PLAN.md'):
            return work_plan
        raise AssertionError(path)

    with patch.object(guard, 'REPO', Path('/synthetic')), \
         patch.object(guard, 'refuse_sealed'), \
         patch.object(Path, 'is_file', return_value=True), \
         patch.object(Path, 'read_bytes', read_bytes), \
         patch.object(guard.subprocess, 'check_output', side_effect=git):
        return guard.require_d8_confirmation()


def test_exact_committed_gate_and_plan_succeed():
    assert invoke() is None


def test_untracked_gate_is_rejected_even_if_decision_names_its_hash():
    with pytest.raises(RuntimeError, match='committed PLAN or gate code unavailable'):
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
