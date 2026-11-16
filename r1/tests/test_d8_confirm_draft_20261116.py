"""The 16 Nov R1-BX-D8-CONFIRM draft (S2-M4) stays compatible with the accepted parser.

Path A must be byte-identical to the 14 Nov row, which test_d8_confirm_draft_matches_parser.py runs through the
real guard. The path-B template must be accepted by the real parser function once its two placeholders are filled.
The draft is not authority; the real PLAN is never read or modified here.
"""
import hashlib
import re

from r1.c3 import analysis_guard as g
from r1.harness import REPO

DRAFT = REPO / 'docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261116.md'
OLD = REPO / 'docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261114.md'
GATE = REPO / 'r1/c3/gate.py'
ROW = re.compile(r'^\| R1-BX-D8-CONFIRM \| .* \|$', re.M)
PLAN_HEAD = '## 10. Author decisions\n### 16 November 2026 (author)\n| ID | Decision |\n|---|---|\n'


def _rows(path):
    return ROW.findall(path.read_text(encoding='utf-8'))


def test_path_a_is_the_14_nov_row():
    new, old = _rows(DRAFT), _rows(OLD)
    assert len(old) == 1 and len(new) == 2
    assert new[0] == old[0]


def test_path_b_template_is_accepted_once_filled():
    template = _rows(DRAFT)[1]
    assert '<commit>' in template and '<sha256 of gate.py>' in template
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    commit = 'a' * 40
    row = template.replace('<commit>', commit).replace('<sha256 of gate.py>', sha)
    assert g._confirmation_commit(PLAN_HEAD + row + '\n', sha) == commit
    # The filled template differs from path A only in the two values.
    path_a = _rows(DRAFT)[0]
    assert re.sub(r'@ `[0-9a-f]{40}`', f'@ `{commit}`', path_a) == row


def test_template_with_placeholders_is_refused():
    template = _rows(DRAFT)[1]
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    assert g._confirmation_commit(PLAN_HEAD + template + '\n', sha) is None


def test_decision_row_draft_is_not_a_confirmation():
    text = DRAFT.read_text(encoding='utf-8')
    assert re.search(r'^\| R1-BX-D8-V3 \| ', text, re.M)
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    # Every candidate row in the draft is inside a fenced block, so the draft text itself confirms nothing.
    assert g._confirmation_commit('## 10. Author decisions\n### 16 November 2026 (author)\n' + text, sha) is None
