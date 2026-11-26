"""Declared per-candidate template repairs (A1): SHA-pinned registry entries; runtime and
launcher pinning. No model/GPU/network."""
import hashlib
import pytest
from pathlib import Path
from r1.exam.runtime import template_repair_args, TEMPLATE_REPAIR_SCHEMA


def _decl(path, sha):
    return {'schema': TEMPLATE_REPAIR_SCHEMA, 'file': str(path), 'sha256': sha}


def test_no_repair_yields_no_args():
    assert template_repair_args({}) == []
    assert template_repair_args({'template_repair': None}) == []


def test_valid_repair_returns_template_file_flag(tmp_path):
    tpl = tmp_path / 'x.jinja'; tpl.write_text('{{ messages }}')
    sha = hashlib.sha256(tpl.read_bytes()).hexdigest()
    args = template_repair_args({'template_repair': _decl(tpl, sha)})
    assert args == ['--chat-template-file', str(tpl.resolve())]


def test_missing_file_or_digest_mismatch_stops(tmp_path):
    tpl = tmp_path / 'x.jinja'; tpl.write_text('{{ messages }}')
    sha = hashlib.sha256(tpl.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match='file missing'):
        template_repair_args({'template_repair': _decl(tmp_path / 'nope.jinja', sha)})
    with pytest.raises(RuntimeError, match='digest mismatch'):
        template_repair_args({'template_repair': _decl(tpl, '0' * 64)})


def test_malformed_declaration_stops(tmp_path):
    with pytest.raises(RuntimeError, match='declaration malformed'):
        template_repair_args({'template_repair': {'file': 'x', 'sha256': '0' * 64}})


def test_launcher_pins_repair_template_files(tmp_path):
    from r1.scripts import trackx_stagea_launch as launch
    repo = tmp_path / 'repo'
    (repo / 'r1/scripts').mkdir(parents=True)
    (repo / 'r1/x.py').write_text('pass\n')
    (repo / 'r1/scripts/trackx_lease_guardian.py').write_text('pass\n')
    (repo / 'r1/exam/templates/repairs').mkdir(parents=True)
    tpl = repo / 'r1/exam/templates/repairs/x.jinja'
    tpl.write_text('{{ messages }}')
    config = tmp_path / 'cfg.json'; config.write_text('{}')
    prompts = tmp_path / 'prompts.jsonl'; prompts.write_text('\n')
    rows = launch.pinned_files(repo, config, prompts, [])
    paths = [row['path'] for row in rows]
    assert str(tpl.resolve()) in paths
