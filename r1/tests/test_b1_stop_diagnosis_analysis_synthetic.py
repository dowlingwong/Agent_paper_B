"""Synthetic known-answer tests for the B1 STOP diagnosis analysis (no host, real data or model)."""
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.fixture
def env(monkeypatch):
    diag = _load('b1_diag_for_analysis', 'docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py')
    if not hasattr(diag.os, 'O_NOATIME'): monkeypatch.setattr(diag.os, 'O_NOATIME', 0, raising=False)
    fixtures = _load('b1_diag_fixtures', 'r1/tests/test_b1_stop_diagnosis_synthetic.py')
    analysis = _load('b1_diag_analysis', 'docs/r1/proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py')
    return diag, fixtures, analysis


def capture(tmp_path, diag, fixtures, **kw):
    doc = diag.inspect(str(fixtures.build(tmp_path / 'b1', diag, **kw)))
    path = tmp_path / 'ssh.log'
    path.write_text('PRIVATE_CAPTURE=x\n' + json.dumps(doc) + '\nDIAGNOSIS_CAPTURE_COMPLETE\n\nSSH_EXIT=0\n')
    return path


def test_scripted_worse_than_random_is_design_class_and_r4_applies(env, tmp_path, monkeypatch):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', lambda a, n, s, b: 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003))
    v = an.verdicts(an.load_capture(capture(tmp_path, diag, fx)))
    assert v['H1'] == 'SUPPORTED' and v['H4'] == 'NOT SUPPORTED' and v['class'] == 'D'
    assert v['r4_applicable_under_A1'] is True and v['D7'] == 'PASS' and v['rules_fixed_before_capture'] is True


def test_gate_not_reproduced_is_engineering_class(env, tmp_path):
    diag, fx, an = env
    # Default fixture: scripted 0.001 vs random_valid 0.018/19 per instance -> degenerate interval above 0,
    # so the recomputed gate would have passed: the recorded STOP is not reproduced.
    v = an.verdicts(an.load_capture(capture(tmp_path, diag, fx)))
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E' and v['r4_applicable_under_A1'] is False
    assert any('does not reproduce' in r for r in v['evidence']['h4_reasons'])


def test_consistent_small_gap_with_wide_interval_is_power_class(env, tmp_path, monkeypatch):
    diag, fx, an = env
    def delta(a, n, s, b):
        if a == 'scripted': return 0.01 if s != 9004 else -0.02
        return 0.0 if a == 'random_valid' else 0.003
    monkeypatch.setattr(fx, '_delta', delta)
    v = an.verdicts(an.load_capture(capture(tmp_path, diag, fx)))
    ev = v['evidence']
    assert ev['d1_point'] == pytest.approx(0.0025) and ev['d1_lower'] <= 0 and ev['positive_nodes'] == 3
    assert ev['mean_z_difference'] > an.Z_SMALL
    assert v['H3'] == 'SUPPORTED' and v['H1'] == 'NOT SUPPORTED' and v['H2'] == 'NOT SUPPORTED' and v['class'] == 'P'


def test_d0_counter_forces_engineering_class(env, tmp_path, monkeypatch):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', lambda a, n, s, b: 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003))
    path = capture(tmp_path, diag, fx)
    doc = an.load_capture(path)
    doc['summary']['D2']['scripted/digits_mlp']['d0']['delta_mismatch'] = 1
    v = an.verdicts(doc)
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E'


def test_falling_increments_support_h2(env, tmp_path, monkeypatch):
    diag, fx, an = env
    # Scripted beats random_valid on every node (so H1 and H3 do not fire), but scripted's
    # increments fall from +0.03 to 0 within each root: a > 0.25 sigma_joint drop on every node.
    def delta(a, n, s, b):
        if a == 'scripted': return 0.03 if b <= 11 else 0.0
        return -0.01 if a == 'random_valid' else 0.003
    monkeypatch.setattr(fx, '_delta', delta)
    v = an.verdicts(an.load_capture(capture(tmp_path, diag, fx)))
    assert v['H2'] == 'SUPPORTED' and v['class'] in ('D', 'E')


def test_duplicate_rate_outside_interval_reported_separately(env, tmp_path, monkeypatch):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', lambda a, n, s, b: 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003))
    v = an.verdicts(an.load_capture(capture(tmp_path, diag, fx, qwen_dup=2, qwen_eval=20)))
    assert v['D7'] == 'FAIL' and v['class'] == 'D'


def test_tables_render_and_capture_without_marker_is_refused(env, tmp_path, monkeypatch, capsys):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', lambda a, n, s, b: 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003))
    path = capture(tmp_path, diag, fx)
    assert an.main(['x', str(path)]) == 0
    out = capsys.readouterr().out
    assert '### D1' in out and '### D7' in out and '"class": "D"' in out and 'candidate_metrics' not in out
    bad = tmp_path / 'bad.log'; bad.write_text(path.read_text().replace('DIAGNOSIS_CAPTURE_COMPLETE', ''))
    assert an.main(['x', str(bad)]) == 1
