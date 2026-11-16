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


def _fenced_blocks(text):
    return re.findall(r'^```\n(.*?)\n```$', text, re.M | re.S)


def test_fences_are_what_keep_the_draft_rows_inert():
    text = DRAFT.read_text(encoding='utf-8')
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    blocks = [b for b in _fenced_blocks(text) if b.startswith('| R1-BX-D8-CONFIRM | ')]
    assert len(blocks) == 2
    path_a = blocks[0]
    commit = re.search(r'@ `([0-9a-f]{40})`', path_a).group(1)
    # Fenced exactly as in the draft, directly under a valid author table header: refused.
    assert g._confirmation_commit(PLAN_HEAD + '```\n' + path_a + '\n```\n', sha) is None
    # The same block without its fence: accepted, so the fence (not a wording slip) is what keeps it inert.
    assert g._confirmation_commit(PLAN_HEAD + path_a + '\n', sha) == commit
    # The whole draft under the header, with its own headings stripped so that it stays in section 10: refused.
    body = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))
    assert g._confirmation_commit(PLAN_HEAD + body + '\n', sha) is None


def test_decision_row_draft_is_present_and_not_a_confirmation_row():
    text = DRAFT.read_text(encoding='utf-8')
    rows = re.findall(r'^\| R1-BX-D8-V3 \| .* \|$', text, re.M)
    assert len(rows) == 1
    sha = hashlib.sha256(GATE.read_bytes()).hexdigest()
    assert g._confirmation_commit(PLAN_HEAD + rows[0] + '\n', sha) is None
