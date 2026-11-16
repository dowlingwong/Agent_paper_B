"""Synthetic known-answer tests for the descriptive B1 first-vs-second-half check (R1-EXAM-B1-ANCHOR-R4-H2)."""
import json
from pathlib import Path

import pytest

from r1.scripts import b1_candidate_halves as H


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def build(work: Path, cand: str, role: str, roots: dict, *, host='/home/dowling/exam-x/work/b1_x', extra_mode=None):
    """roots: {(node, seed): [delta_audit, ...]} for the primary mode 'off'."""
    stored = []
    for (node, seed), deltas in roots.items():
        rel = f'off/{node}__s{seed}/campaign_manifest.json'
        _write(work / cand / 'b1' / rel, {'mode': 'off', 'audited_proposals':
                                          [{'instance_id': f'{node}__s{seed}', 'delta_audit': d,
                                           'proposal_id': f'EXAM:{node}__s{seed}:t{3 * k + 2:03d}'}
                                          for k, d in enumerate(deltas)]})
        stored.append(f'{host}/{cand}/b1/{rel}')
    if extra_mode:
        rel = f'on/digits_mlp__s9001/campaign_manifest.json'
        _write(work / cand / 'b1' / rel, {'mode': 'on', 'audited_proposals':
                                          [{'instance_id': 'digits_mlp__s9001', 'delta_audit': 9.0,
                                           'proposal_id': 'EXAM:digits_mlp__s9001:t001'}]})
        stored.append(f'{host}/{cand}/b1/{rel}')
    _write(work / cand / 'b1_manifest.json', {'candidate': cand, 'role': role, 'phase': 'b1', 'primary_mode': 'off',
                                              'root_manifests': stored})


def test_halves_known_answer_and_other_modes_ignored(tmp_path):
    s = H.SIGMA_JOINT
    build(tmp_path, 'cand_a', 'candidate', {('digits_mlp', 9001): [0.0102, 0.0102, -0.0102],      # z: 1, 1 | -1
                                            ('openml_ionosphere', 9001): [0.0410, -0.0410]},       # z: 1 | -1
          extra_mode=True)
    build(tmp_path, 'scripted', 'anchor', {('openml_credit_approval', 9002): [0.0, 0.0279]})      # z: 0 | 1
    rows = {r['candidate']: r for r in H.candidate_rows(tmp_path)}
    a = rows['cand_a']
    assert (a['roots'], a['n_first'], a['n_second']) == (2, 3, 2)
    assert a['first_half_mean_z'] == pytest.approx(1.0) and a['second_half_mean_z'] == pytest.approx(-1.0)
    assert a['change_z'] == pytest.approx(-2.0)
    assert a['change_z_by_node']['digits_mlp'] == pytest.approx(-2.0)
    assert a['change_z_by_node']['openml_credit_approval'] is None
    b = rows['scripted']
    assert b['change_z'] == pytest.approx(1.0) and b['role'] == 'anchor'
    assert 'not used by x5_rule_v2' in b['role_of_this_check'] and s['digits_mlp'] == 0.0102


def test_main_prints_table_and_json_and_refuses_bad_input(tmp_path, capsys):
    build(tmp_path, 'cand_a', 'candidate', {('digits_mlp', 9001): [0.01, 0.02]})
    assert H.main(['--work', str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert '| cand_a | candidate | 1 |' in out and '"schema": "b1_candidate_halves/v1"' in out
    assert H.main(['--work', str(tmp_path / 'missing')]) == 2
    bad = tmp_path / 'bad'
    build(bad, 'cand_b', 'candidate', {('tabular_mlp', 9001): [0.01]})   # node without sigma_joint
    assert H.main(['--work', str(bad)]) == 2


def test_refuses_audits_out_of_budget_order(tmp_path):
    build(tmp_path, 'cand_a', 'candidate', {('digits_mlp', 9001): [0.01, 0.02, 0.03]})
    path = tmp_path / 'cand_a' / 'b1' / 'off' / 'digits_mlp__s9001' / 'campaign_manifest.json'
    root = json.loads(path.read_text())
    root['audited_proposals'] = root['audited_proposals'][::-1]
    path.write_text(json.dumps(root))
    with pytest.raises(ValueError, match='budget order'):
        H.candidate_rows(tmp_path)
    root['audited_proposals'] = root['audited_proposals'][::-1]
    root['audited_proposals'][0]['proposal_id'] = 'EXAM:digits_mlp__s9002:t002'   # wrong instance
    path.write_text(json.dumps(root))
    with pytest.raises(ValueError, match='proposal_id'):
        H.candidate_rows(tmp_path)
