"""Every visible sweep-2 table reader refuses without an exact R1-BX-D8-CONFIRM row.

Synthetic only: a pytest-owned Git checkout with a synthetic gate and PLAN, and a
synthetic table directory whose build metadata has unknown (sweep-2-like)
provenance. A Python audit hook records every file opened while a reader runs;
no file inside the table other than ``build.json`` may be opened before the
reader refuses. No real label, audit value, sealed file or author row is used.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from r1.c3 import analysis_guard as g
from r1.c3 import audit, dataset, duplicate_report, gate, ni_masking, offline_eval

_OPENED = []
_RECORDING = [False]


def _hook(event, args):
    if _RECORDING[0] and event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENED.append(os.fsdecode(args[0]))


sys.addaudithook(_hook)


def decision(sha, commit):
    return (f'Gate code `r1/c3/gate.py` @ `{commit}`, sha256 `{sha}`, '
            'implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); '
            'T0 and T1 pooled with tier as a stratum. '
            'If only some T1 nodes have labels by B.7, read the gate on T0 plus the available '
            'labelled T1 nodes and disclose the node count. '
            'Each suite must have at least one labelled T1 node, otherwise STOP. '
            'Existing preregistration and analysis gates remain in force. '
            'Sweep-2 label tables may be analysed from this row on.')


HEAD = '## 10. Author decisions\n### 9 November 2026 (author)\n| ID | Decision |\n|---|---|\n'

# PLAN variants with no table row whose first cell is exactly R1-BX-D8-CONFIRM in a
# dated author decision table of section 10 (each is a near miss of the valid row).
VARIANTS = {
    'absent': lambda row, d: HEAD,
    'd8_row_only': lambda row, d: HEAD + f'| R1-BX-D8 | {d} |\n',
    'confirm_in_second_cell': lambda row, d: HEAD + f'| R1-BX-D8 | R1-BX-D8-CONFIRM {d} |\n',
    'prefix_not_exact': lambda row, d: HEAD + f'| R1-BX-D8-CONFIRM-DRAFT | {d} |\n',
    'prose': lambda row, d: HEAD + f'R1-BX-D8-CONFIRM {d}\n',
    'fenced': lambda row, d: HEAD + '```\n' + row + '```\n',
    'html_comment': lambda row, d: HEAD + '<!--\n' + row + '-->\n',
    'indented_code': lambda row, d: HEAD + '    ' + row,
    'other_section': lambda row, d: '## 9. Notes\n### 9 November 2026 (author)\n| ID | Decision |\n|---|---|\n' + row,
    'undated_heading': lambda row, d: '## 10. Author decisions\n### Author decisions\n| ID | Decision |\n|---|---|\n' + row,
    'proposed_table': lambda row, d: '## 10. Author decisions\n### 9 November 2026 (author)\n| ID | Proposed decision |\n|---|---|\n' + row,
    'wrong_sha': lambda row, d: HEAD + row.replace(d.split('sha256 `')[1][:64], 'a' * 64),
    'negated': lambda row, d: HEAD + row.replace('may be analysed', 'may not be analysed'),
    'duplicate_rows': lambda row, d: HEAD + row + row,
}


def git(repo, *args):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def make_repo(tmp_path, monkeypatch, variant):
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', os.devnull)
    for k in ('AUTHOR', 'COMMITTER'):
        monkeypatch.setenv(f'GIT_{k}_NAME', 'Synthetic')
        monkeypatch.setenv(f'GIT_{k}_EMAIL', 'synthetic@example.invalid')
    repo = tmp_path / 'repo'; repo.mkdir()
    template = tmp_path / 'empty-template'; template.mkdir()
    subprocess.run(['git', 'init', '-q', '--template', str(template), str(repo)], check=True)
    gate_file = repo / 'r1/c3/gate.py'; gate_file.parent.mkdir(parents=True)
    gate_file.write_bytes(b'# SYNTHETIC gate bytes for the refusal matrix\n')
    git(repo, 'add', 'r1/c3/gate.py'); git(repo, 'commit', '-qm', 'synthetic gate')
    code = git(repo, 'rev-parse', 'HEAD')
    d = decision(hashlib.sha256(gate_file.read_bytes()).hexdigest(), code)
    row = f'| R1-BX-D8-CONFIRM | {d} |\n'
    plan = repo / 'docs/r1/PLAN.md'; plan.parent.mkdir(parents=True)
    plan.write_text((HEAD + row if variant == 'valid' else VARIANTS[variant](row, d)) + '## 11. Other\n')
    git(repo, 'add', 'docs/r1/PLAN.md'); git(repo, 'commit', '-qm', 'synthetic PLAN')
    monkeypatch.setattr(g, 'REPO', repo)
    return repo


def make_table(tmp_path):
    table = tmp_path / 'sweep2_table'; table.mkdir()
    (table / 'build.json').write_text(json.dumps({'sweep_index': {'path': 'synthetic', 'sha256': '2' * 64}}))
    for name in ('proposals.jsonl', 'audits.jsonl', 'configs.json', 'gate_input.json'):
        (table / name).write_text('SYNTHETIC LABEL BYTES MUST NOT BE OPENED\n')
    return table


READERS = {
    'dataset.load_table': lambda t, tmp: dataset.load_table(t),
    'offline_eval.assemble': lambda t, tmp: offline_eval.assemble(t),
    'ni_masking.load_audits': lambda t, tmp: ni_masking.load_audits(t),
    'audit.evidence_plan': lambda t, tmp: audit.evidence_plan(t, tmp, tmp / 'missing-index', tmp / 'missing-class'),
    'duplicate_report.main': lambda t, tmp: duplicate_report.main(DUPLICATE_ARGS(t, tmp)),
    'gate.load_and_evaluate': lambda t, tmp: gate.load_and_evaluate(t / 'gate_input.json'),
    'gate.evaluate': lambda t, tmp: gate.evaluate({'schema': gate.INPUT_SCHEMA}),
}


def DUPLICATE_ARGS(table, tmp):
    return ['--table', str(table), '--out', str(tmp / 'duplicate_report_out.json')]


def run_reader(name, table, tmp_path):
    _OPENED.clear(); _RECORDING[0] = True
    try:
        with pytest.raises(RuntimeError, match='STOP'):
            READERS[name](table, tmp_path)
    finally:
        _RECORDING[0] = False
    opened = {Path(p).resolve() for p in _OPENED}
    forbidden = {(table / n).resolve() for n in ('proposals.jsonl', 'audits.jsonl', 'configs.json', 'gate_input.json')}
    assert not opened & forbidden, f'{name} opened label bytes before refusing'


@pytest.mark.parametrize('variant', sorted(VARIANTS))
@pytest.mark.parametrize('reader', sorted(READERS))
def test_reader_refuses_without_exact_confirm_row(tmp_path, monkeypatch, variant, reader):
    make_repo(tmp_path, monkeypatch, variant)
    run_reader(reader, make_table(tmp_path), tmp_path)


def test_valid_synthetic_row_is_what_unlocks_the_guard(tmp_path, monkeypatch):
    """Positive control: the same fixture with the exact row passes the authority check."""
    make_repo(tmp_path, monkeypatch, 'valid')
    assert g.require_d8_confirmation() is None


def test_gate_entry_points_check_authority_before_anything_else(tmp_path, monkeypatch):
    make_repo(tmp_path, monkeypatch, 'absent')
    called = []
    monkeypatch.setattr(gate, '_evaluate', lambda x: called.append(x))
    for call in (lambda: gate.evaluate({}), lambda: gate.load_and_evaluate(tmp_path / 'missing.json'),
                 lambda: gate.main([str(tmp_path / 'missing.json')])):
        with pytest.raises(RuntimeError, match='R1-BX-D8-CONFIRM'):
            call()
    assert called == []
