"""The gate-v3 R1-BX-D8-CONFIRM draft: the S2-M4 path-B template with only the commit and SHA filled in.

The draft is not authority; the real PLAN is never read or modified here. The accepted parser is
``analysis_guard._confirmation_commit``.
"""
import hashlib
import re

from r1.c3 import analysis_guard as g
from r1.harness import REPO

DRAFT = REPO / 'docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_V3_20261116.md'
S2M4 = REPO / 'docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261116.md'
GATE = REPO / 'r1/c3/gate.py'
ROW = re.compile(r'^\| R1-BX-D8-CONFIRM \| .* \|$', re.M)
PLAN_HEAD = '## 10. Author decisions\n### 16 November 2026 (author)\n| ID | Decision |\n|---|---|\n'


def _row():
    rows = ROW.findall(DRAFT.read_text(encoding='utf-8'))
    assert len(rows) == 1
    return rows[0]


def test_row_is_the_s2m4_template_with_two_values_filled():
    template = ROW.findall(S2M4.read_text(encoding='utf-8'))[1]
    row = _row()
    commit = re.search(r'@ `([0-9a-f]{40})`', row).group(1)
    sha = re.search(r'sha256 `([0-9a-f]{64})`', row).group(1)
    assert template.replace('<commit>', commit).replace('<sha256 of gate.py>', sha) == row
    assert sha == hashlib.sha256(GATE.read_bytes()).hexdigest()


def test_fenced_row_is_inert_and_unfenced_row_is_accepted():
    row = _row()
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    commit = re.search(r'@ `([0-9a-f]{40})`', row).group(1)
    assert g._confirmation_commit(PLAN_HEAD + '```\n' + row + '\n```\n', sha) is None
    assert g._confirmation_commit(PLAN_HEAD + row + '\n', sha) == commit
    body = '\n'.join(line for line in DRAFT.read_text(encoding='utf-8').splitlines() if not line.startswith('#'))
    assert g._confirmation_commit(PLAN_HEAD + body + '\n', sha) is None
