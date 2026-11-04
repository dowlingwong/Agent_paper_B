"""Synthetic M11 tests; no evidence table or model is loaded."""
import pytest
import subprocess
from r1.c3 import gate


class ForbiddenRows:
    def __iter__(self):
        raise AssertionError('must not iterate')


def test_gate_cannot_be_enabled_by_caller_plan(tmp_path):
    fake = tmp_path / 'PLAN.md'
    fake.write_text('## 10. Open decisions\n| R1-BX-D8-CONFIRM | ' + gate.gate_sha256() + ' |\n')
    with pytest.raises(TypeError):
        gate.aggregate_gate(ForbiddenRows(), {}, {}, plan=fake)
    with pytest.raises(RuntimeError, match='trusted committed author PLAN'):
        gate.aggregate_gate(ForbiddenRows(), {}, {})
    with pytest.raises(TypeError):
        gate.require_gate_confirmation(fake)


def test_fabricated_committed_plan_and_remote_ref_cannot_enable_gate(tmp_path, monkeypatch):
    repo = tmp_path / 'fake_repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    plan = repo / 'docs' / 'r1' / 'PLAN.md'
    plan.parent.mkdir(parents=True)
    plan.write_text('## 10. Open decisions\n| R1-BX-D8-CONFIRM | ' + gate.gate_sha256() + ' |\n')
    subprocess.run(['git', '-C', str(repo), 'add', 'docs/r1/PLAN.md'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Dowling Wong',
                    '-c', 'user.email=wangdowling@gmail.com', 'commit', '-q', '-m', 'fixture'], check=True)
    subprocess.run(['git', '-C', str(repo), 'update-ref', 'refs/remotes/origin/mac-int-20261104', 'HEAD'], check=True)
    monkeypatch.chdir(repo)
    with pytest.raises(RuntimeError, match='trusted committed author PLAN'):
        gate.aggregate_gate(ForbiddenRows(), {}, {})


def test_iqm_fractional_boundaries():
    assert gate._iqm([0, 1, 2, 3]) == pytest.approx(1.5)
    assert gate._iqm([0, 1, 2]) == pytest.approx(1.)


def test_provisional_node_summaries_exclude_low_dev_gap_keep_ties():
    groups = {'a': [{'A2': 0., 'A3': .4, 'oracle': 1.}],
              'b': [{'A2': 0., 'A3': 0., 'oracle': 1.}]}
    summary = gate._summaries(groups, {'a': 1., 'b': .01}, {'a': .1, 'b': .1}, 'A3')
    assert summary['iqm_gap_closed'] == pytest.approx(.4)
    assert summary['nodes']['b']['gap_closed'] is None
    assert summary['nodes']['b']['probability_improvement'] == .5
    assert summary['probability_improvement'] == .75


def test_provisional_nonpositive_oracle_denominator_fails_closed():
    groups = {'a': [{'A2': 1., 'A3': 2., 'oracle': 1.}]}
    with pytest.raises(ValueError, match='nonpositive'):
        gate._summaries(groups, {'a': 1.}, {'a': .1}, 'A3')
