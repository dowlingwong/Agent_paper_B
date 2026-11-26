"""The current confirmation-row draft (R1-BX-D8-CONFIRM-V31, gate v3.1) matches the guard and the current gate bytes.

The draft lives under docs/r1/proposals and is not authority. This test only
checks that, if the author pasted it after review, the accepted guard would
accept it for the current gate file. It uses a pytest-owned synthetic Git
repository; the real PLAN is never modified.
"""
import hashlib
import os
import re
import subprocess

import pytest

from r1.c3 import analysis_guard as g
from r1.harness import REPO

DRAFT = REPO / 'docs/r1/proposals/R1_BX_D8_CONFIRM_V31_DRAFT_20261121.md'   # gate v3.1 (was the v3 draft)
GATE = REPO / 'r1/c3/gate.py'


def draft_row():
    text = DRAFT.read_text(encoding='utf-8')
    rows = re.findall(r'^\| R1-BX-D8-CONFIRM-V31 \| .* \|$', text, re.M)
    assert len(rows) == 1, 'the draft must contain exactly one candidate row'
    return rows[0]


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def test_draft_names_current_gate_sha_and_a_commit_with_those_bytes():
    row = draft_row()
    sha = re.search(r'sha256 `([0-9a-f]{64})`', row).group(1)
    commit = re.search(r'@ `([0-9a-f]{40}|[0-9a-f]{64})`', row).group(1)
    assert sha == hashlib.sha256(GATE.read_bytes()).hexdigest(), 'draft SHA is stale: redraft the row'
    try:
        at_commit = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{commit}:r1/c3/gate.py'],
                                            stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip('draft commit not present in this checkout')
    assert hashlib.sha256(at_commit).hexdigest() == sha


def test_draft_row_is_accepted_by_the_real_guard_in_a_synthetic_repo(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    for k in ('AUTHOR', 'COMMITTER'):
        monkeypatch.setenv(f'GIT_{k}_NAME', 'Synthetic')
        monkeypatch.setenv(f'GIT_{k}_EMAIL', 'synthetic@example.invalid')
    repo = tmp_path / 'repo'; repo.mkdir()
    template = tmp_path / 'empty-template'; template.mkdir()
    subprocess.run(['git', 'init', '-q', '--template', str(template), str(repo)], check=True)
    (repo / 'r1/c3').mkdir(parents=True)
    (repo / 'r1/c3/gate.py').write_bytes(GATE.read_bytes())
    git(repo, 'add', 'r1/c3/gate.py'); git(repo, 'commit', '-qm', 'synthetic copy of gate')
    synthetic_commit = git(repo, 'rev-parse', 'HEAD')
    row = re.sub(r'@ `[0-9a-f]{40,64}`', f'@ `{synthetic_commit}`', draft_row())
    (repo / 'docs/r1').mkdir(parents=True)
    (repo / 'docs/r1/PLAN.md').write_text('## 10. Author decisions\n### 10 November 2026 (author)\n'
                                          '| ID | Decision |\n|---|---|\n' + row + '\n')
    git(repo, 'add', 'docs/r1/PLAN.md'); git(repo, 'commit', '-qm', 'synthetic PLAN')
    monkeypatch.setattr(g, 'REPO', repo)
    assert g.require_d8_confirmation() is None

