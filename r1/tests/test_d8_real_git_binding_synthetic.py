"""Real Git/filesystem checks using synthetic decisions and pytest-owned temp only."""
import hashlib
import os
import subprocess
from pathlib import Path

import pytest
from r1.c3 import analysis_guard as guard


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    monkeypatch.setenv('GIT_AUTHOR_NAME', 'Synthetic')
    monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'synthetic@example.invalid')
    monkeypatch.setenv('GIT_COMMITTER_NAME', 'Synthetic')
    monkeypatch.setenv('GIT_COMMITTER_EMAIL', 'synthetic@example.invalid')
    repo = tmp_path / 'repo'; repo.mkdir()
    template = tmp_path / 'empty-template'; template.mkdir()
    subprocess.run(['git', 'init', '-q', '--template', str(template), str(repo)], check=True)
    gate = repo / 'r1/c3/gate.py'; gate.parent.mkdir(parents=True)
    content = b'# SYNTHETIC gate, not a real analysis gate\n'; gate.write_bytes(content)
    git(repo, 'add', 'r1/c3/gate.py'); git(repo, 'commit', '-qm', 'synthetic gate')
    code = git(repo, 'rev-parse', 'HEAD'); sha = hashlib.sha256(content).hexdigest()
    decision = (f'Gate code `r1/c3/gate.py` @ `{code}`, sha256 `{sha}`, '
                'implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); '
                'T0 and T1 pooled with tier as a stratum. '
                'If only some T1 nodes have labels by B.7, read the gate on T0 plus the available '
                'labelled T1 nodes and disclose the node count. '
                'Each suite must have at least one labelled T1 node, otherwise STOP. '
                'Existing preregistration and analysis gates remain in force. '
                'Sweep-2 label tables may be analysed from this row on.')
    plan = repo / 'docs/r1/PLAN.md'; plan.parent.mkdir(parents=True)
    plan.write_text('## 10. Author decisions\n### 5 November 2026 (author)\n'
                    '| ID | Decision |\n|---|---|\n'
                    f'| R1-BX-D8-CONFIRM | {decision} |\n')
    git(repo, 'add', 'docs/r1/PLAN.md'); git(repo, 'commit', '-qm', 'synthetic decision')
    monkeypatch.setattr(guard, 'REPO', repo)
    return repo, gate, plan


def test_real_clean_synthetic_ancestor_accepts(checkout):
    assert guard.require_d8_confirmation() is None


def test_dirty_gate_refused(checkout):
    _, gate, _ = checkout
    gate.write_bytes(b'# changed synthetic gate\n')
    with pytest.raises(RuntimeError, match='STOP'):
        guard.require_d8_confirmation()


def test_dirty_plan_refused(checkout):
    _, _, plan = checkout
    with plan.open('a') as f: f.write('additional uncommitted synthetic text\n')
    with pytest.raises(RuntimeError, match='STOP'):
        guard.require_d8_confirmation()


def test_committed_gate_change_refused(checkout):
    repo, gate, _ = checkout
    gate.write_bytes(b'# another synthetic committed gate\n')
    git(repo, 'add', 'r1/c3/gate.py'); git(repo, 'commit', '-qm', 'change gate')
    with pytest.raises(RuntimeError, match='STOP'):
        guard.require_d8_confirmation()


def test_committed_negative_decision_refused(checkout):
    repo, _, plan = checkout
    plan.write_text(plan.read_text().replace('Sweep-2 label tables may be analysed',
                                             'Sweep-2 label tables may not be analysed'))
    git(repo, 'add', 'docs/r1/PLAN.md'); git(repo, 'commit', '-qm', 'negative decision')
    with pytest.raises(RuntimeError, match='STOP'):
        guard.require_d8_confirmation()
