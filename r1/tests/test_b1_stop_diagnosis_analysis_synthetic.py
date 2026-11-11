"""Synthetic known-answer tests for the B1 STOP diagnosis analysis (no host, real data or model).

Every class and every rule disjunct has its own fixture with one exact expected class."""
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


def write(tmp_path, doc, name='ssh.log', tail='\nDIAGNOSIS_CAPTURE_COMPLETE\n\nSSH_EXIT=0\n'):
    path = tmp_path / name
    path.write_text('PRIVATE_CAPTURE=x\n' + json.dumps(doc) + tail)
    return path


def capture(tmp_path, diag, fixtures, **kw):
    return write(tmp_path, diag.inspect(str(fixtures.build(tmp_path / 'b1', diag, **kw))))


def run(tmp_path, env, delta=None, monkeypatch=None, **kw):
    diag, fx, an = env
    if delta is not None: monkeypatch.setattr(fx, '_delta', delta)
    return an.verdicts(an.load_capture(capture(tmp_path, diag, fx, **kw)))


def scripted_zero(a, n, s, b):
    return 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003)


def two_node_gap(a, n, s, b):
    """Scripted ahead on two nodes, behind on ionosphere; random_valid 0. D1 point
    (8 x 0.0158 - 4 x 0.025) / 12 > 0 with lower <= 0; mean z about 0.5; two positive nodes:
    neither H1 nor H3 fires."""
    if a == 'scripted': return -0.025 if n == 'openml_ionosphere' else 0.0158
    return 0.0 if a == 'random_valid' else 0.003


def test_h1_by_point_is_design_class_and_r4_applies(env, tmp_path, monkeypatch):
    v = run(tmp_path, env, scripted_zero, monkeypatch)
    assert v['H1'] == 'SUPPORTED' and v['H2'] == 'NOT SUPPORTED' and v['H4'] == 'NOT SUPPORTED' and v['class'] == 'D'
    assert v['evidence']['h1_reasons'][0] == 'D1 point <= 0'
    assert v['r4_applicable_under_A1'] is True and v['needs_author'] == [] and v['D7'] == 'PASS'
    assert v['rules_fixed_before_diagnosis_capture'] is True and v['descriptive_capture_known'].startswith('ranges only')


def test_h1_second_disjunct_small_standardised_gap(env, tmp_path, monkeypatch):
    # Raw point > 0, lower <= 0, mean z < Z_SMALL, two positive nodes.
    def delta(a, n, s, b):
        if a == 'scripted':
            if n == 'digits_mlp': return 0.002 if s != 9004 else -0.0055
            if n == 'openml_credit_approval': return 0.004 if s != 9004 else -0.011
            return -0.0001
        return 0.0 if a == 'random_valid' else 0.003
    v = run(tmp_path, env, delta, monkeypatch)
    ev = v['evidence']
    assert ev['d1_point'] > 0 and ev['d1_lower'] <= 0 and ev['positive_nodes'] == 2 and ev['mean_z_difference'] < 0.10
    assert v['H1'] == 'SUPPORTED' and len(ev['h1_reasons']) == 1 and ev['h1_reasons'][0].startswith('mean z')
    assert v['H3'] == 'NOT SUPPORTED' and v['H4'] == 'NOT SUPPORTED' and v['class'] == 'D' and v['r4_applicable_under_A1'] is True


def test_d_via_h2_increment_drop_alone_is_not_r4(env, tmp_path, monkeypatch):
    def delta(a, n, s, b):
        if a == 'scripted':
            if n == 'openml_ionosphere': return -0.025
            return 0.0285 if b <= 11 else 0.0  # root mean 0.0285 x 10 / 19 = 0.015
        return 0.0 if a == 'random_valid' else 0.003
    v = run(tmp_path, env, delta, monkeypatch)
    ev = v['evidence']
    assert ev['d1_point'] > 0 and ev['d1_lower'] <= 0 and ev['positive_nodes'] == 2 and ev['mean_z_difference'] >= 0.10
    assert v['H1'] == 'NOT SUPPORTED' and v['H3'] == 'NOT SUPPORTED' and v['H4'] == 'NOT SUPPORTED'
    assert v['H2'] == 'SUPPORTED' and [r['kind'] for r in ev['h2_reasons']] == ['increment_drop']
    assert v['class'] == 'D' and v['r4_applicable_under_A1'] is False
    assert v['needs_author'] == ['class D rests on H2 alone; not covered by line A1 (PLAN R1-EXAM-B1-ANCHOR-R4)']


def test_d_via_h2_count_ratio_alone(env, tmp_path, monkeypatch):
    budgets = lambda a, n, s: range(2, 10) if a == 'scripted' else range(2, 21)  # 32 vs 76 audited per node
    v = run(tmp_path, env, two_node_gap, monkeypatch, budgets=budgets)
    assert v['H1'] == 'NOT SUPPORTED' and v['H3'] == 'NOT SUPPORTED' and v['H4'] == 'NOT SUPPORTED'
    assert v['H2'] == 'SUPPORTED' and [r['kind'] for r in v['evidence']['h2_reasons']] == ['count_ratio']
    assert v['class'] == 'D' and v['r4_applicable_under_A1'] is False


def test_unclassified_when_no_rule_fires(env, tmp_path, monkeypatch):
    v = run(tmp_path, env, two_node_gap, monkeypatch)
    assert (v['H1'], v['H2'], v['H3'], v['H4']) == ('NOT SUPPORTED',) * 4
    assert v['class'] == 'UNCLASSIFIED' and v['r4_applicable_under_A1'] is False
    assert v['needs_author'] == ['no class rule fired (plan section 4)']


def test_consistent_small_gap_with_wide_interval_is_power_class(env, tmp_path, monkeypatch):
    def delta(a, n, s, b):
        if a == 'scripted': return 0.01 if s != 9004 else -0.02
        return 0.0 if a == 'random_valid' else 0.003
    v = run(tmp_path, env, delta, monkeypatch)
    ev = v['evidence']
    assert ev['d1_point'] == pytest.approx(0.0025) and ev['d1_lower'] <= 0 and ev['positive_nodes'] == 3
    assert ev['mean_z_difference'] > 0.10
    assert v['H3'] == 'SUPPORTED' and v['H1'] == 'NOT SUPPORTED' and v['H2'] == 'NOT SUPPORTED' and v['class'] == 'P'
    assert v['r4_applicable_under_A1'] is False and len(v['needs_author']) == 1


def test_gate_not_reproduced_is_engineering_class(env, tmp_path):
    # Default fixture: identical per-instance differences > 0 give a degenerate interval above 0.
    v = run(tmp_path, env)
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E' and v['r4_applicable_under_A1'] is False
    assert any('does not reproduce' in r for r in v['evidence']['h4_reasons']) and v['needs_author'] == []


def test_falling_increments_with_unreproduced_stop_is_engineering(env, tmp_path, monkeypatch):
    # H2 fires, but identical per-instance differences > 0 do not reproduce the STOP: E takes precedence.
    def delta(a, n, s, b):
        if a == 'scripted': return 0.03 if b <= 11 else 0.0
        return -0.01 if a == 'random_valid' else 0.003
    v = run(tmp_path, env, delta, monkeypatch)
    assert v['H2'] == 'SUPPORTED' and v['H4'] == 'SUPPORTED' and v['class'] == 'E'


def test_d0_counter_forces_engineering_class(env, tmp_path, monkeypatch):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', scripted_zero)
    root = fx.build(tmp_path / 'b1', diag)
    fx.rehash_manifest(root, diag, 'scripted/b1/off/digits_mlp__s9001',
                       lambda d: d['audited_proposals'][0].update(delta_audit=0.5))
    v = an.verdicts(an.load_capture(write(tmp_path, diag.inspect(str(root)))))
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E'
    assert any('D0 counter' in r for r in v['evidence']['h4_reasons'])


def test_zero_audited_proposals_is_engineering_class(env, tmp_path, monkeypatch):
    budgets = lambda a, n, s: range(0) if (a, n, s) == ('scripted', 'digits_mlp', 9001) else range(2, 21)
    v = run(tmp_path, env, scripted_zero, monkeypatch, budgets=budgets)
    reasons = v['evidence']['h4_reasons']
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E' and v['evidence']['d1_point'] is None
    assert 'no audited proposal in scripted/digits_mlp__s9001' in reasons
    assert any(r.startswith('D1 cannot be recomputed') for r in reasons)


def test_software_root_short_of_worker_cap_is_engineering_class(env, tmp_path, monkeypatch):
    runs = lambda a, n, s: (18, 'llm_cap_or_reserved_observer_pair') if (a, n, s) == ('random_valid', 'openml_ionosphere', 9003) else (20, 'worker_cap')
    v = run(tmp_path, env, scripted_zero, monkeypatch, worker_runs=runs)
    assert v['H4'] == 'SUPPORTED' and v['class'] == 'E'
    assert v['evidence']['h4_reasons'] == ['software anchor ended llm_cap_or_reserved_observer_pair with worker_runs=18 '
                                           '(expected worker_cap, 20) in random_valid/openml_ionosphere__s9003']


def test_qwen_root_short_of_worker_cap_is_not_an_anomaly(env, tmp_path, monkeypatch):
    runs = lambda a, n, s: (12, 'llm_cap_or_reserved_observer_pair') if a == 'qwen25_coder_7b' else (20, 'worker_cap')
    v = run(tmp_path, env, scripted_zero, monkeypatch, worker_runs=runs)
    assert v['H4'] == 'NOT SUPPORTED' and v['class'] == 'D'


def test_h4_undetermined_goes_to_author_not_r4(env, tmp_path, monkeypatch):
    v = run(tmp_path, env, scripted_zero, monkeypatch, invalid=15)  # 15 / 20 invalid in every root
    assert v['H1'] == 'SUPPORTED' and v['H4'] == 'UNDETERMINED' and v['class'] == 'REVIEW'
    assert v['r4_applicable_under_A1'] is False
    assert v['needs_author'] == ['H4 UNDETERMINED: possible engineering defect flagged, not shown']


def test_d7_fail_blocks_r4_and_goes_to_author(env, tmp_path, monkeypatch):
    v = run(tmp_path, env, scripted_zero, monkeypatch, qwen_dup=2, qwen_eval=20)
    assert v['D7'] == 'FAIL' and v['class'] == 'D' and v['H1'] == 'SUPPORTED'
    assert v['r4_applicable_under_A1'] is False and v['needs_author'][0].startswith('D7 FAIL')


def test_d7_zero_evaluated_is_fail_as_in_the_gate(env, tmp_path, monkeypatch):
    v = run(tmp_path, env, scripted_zero, monkeypatch, qwen_dup=0, qwen_eval=0)
    assert v['D7'] == 'FAIL' and 'undefined' in v['needs_author'][0] and v['r4_applicable_under_A1'] is False


def test_tables_render_with_new_columns(env, tmp_path, monkeypatch, capsys):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', scripted_zero)
    path = capture(tmp_path, diag, fx)
    assert an.main(['x', str(path)]) == 0
    out = capsys.readouterr().out
    assert '### D1' in out and '### D7' in out and '"class": "D"' in out and 'candidate_metrics' not in out
    assert 'in-run gain after first keep' in out and '| skipped |' in out and 'median / sigma_joint' in out
    assert '[0.42386590667728663, 0.5800007633587785]' in out


def _refused(an, path, capsys, match):
    assert an.main(['x', str(path)]) == 1
    out = capsys.readouterr()
    assert out.out == '' and out.err.startswith('analysis refused') and match in out.err, out.err


@pytest.mark.parametrize('case,match', [
    ('no_marker', 'DIAGNOSIS_CAPTURE_COMPLETE'),
    ('ssh_exit_nonzero', 'SSH_EXIT=0'),
    ('missing_d1', 'D1'),
    ('d7_inside_missing', 'D7 rate/inside'),
    ('none_difference', 'D1_per_instance'),
    ('truncated_rows', 'rows (exactly 36)'),
    ('missing_d3', 'D3 (6 keys)'),
    ('d1_point_differs', 'D1 point differs from rows'),
    ('d2_audited_differs', 'audited differs from rows'),
    ('d3_median_missing', 'D3/D8 scripted/digits_mlp'),
    # Review B1_DIAG_REVIEW_20261109 round 2, note N1: recomputed, not trusted.
    ('z_differs', 'z differs from rows / sigma_joint'),
    ('d3_mean_differs', 'D3/D8 scripted/digits_mlp.mean differs from rows'),
    ('d8_share_differs', 'D3/D8 qwen25_coder_7b/openml_ionosphere.share_harmful differs from rows'),
    ('d4_median_differs', 'D4 random_valid/openml_credit_approval.second_half_of_audited.median differs from rows'),
    ('d4_n_differs', 'budget_index_gt_10.n differs from rows'),
    ('d7_rounded_bound', 'D7 reference differs from the pinned constant'),
    ('d7_wrong_source_sha', 'D7 reference differs from the pinned constant'),
    ('proposals_out_of_order', 'row proposals in budget-index order'),
])
def test_partial_or_inconsistent_capture_is_refused(env, tmp_path, monkeypatch, capsys, case, match):
    diag, fx, an = env
    monkeypatch.setattr(fx, '_delta', scripted_zero)
    doc = diag.inspect(str(fx.build(tmp_path / 'b1', diag))); s = doc['summary']; tail = None
    if case == 'no_marker': tail = '\n\nSSH_EXIT=0\n'
    elif case == 'ssh_exit_nonzero': tail = '\nDIAGNOSIS_CAPTURE_COMPLETE\n\nSSH_EXIT=255\n'
    elif case == 'missing_d1': del s['D1_gate_recomputed']
    elif case == 'd7_inside_missing': del s['D7']['inside']
    elif case == 'none_difference': s['D1_per_instance'][3]['difference'] = None
    elif case == 'truncated_rows': doc['rows'] = doc['rows'][:5]
    elif case == 'missing_d3': del s['D3']
    elif case == 'd1_point_differs': s['D1_gate_recomputed']['difference_point'] += 1e-6
    elif case == 'd2_audited_differs': s['D2']['scripted/digits_mlp']['audited'] += 1
    elif case == 'd3_median_missing': del s['D3']['scripted/digits_mlp']['median_over_sigma_joint']
    elif case == 'z_differs': s['D1_per_instance'][5]['difference_over_sigma_joint'] += 1e-6
    elif case == 'd3_mean_differs': s['D3']['scripted/digits_mlp']['mean'] += 1e-6
    elif case == 'd8_share_differs':
        d = s['D8_information_only']['qwen25_coder_7b/openml_ionosphere']; d['share_harmful'] = 1.0 - d['share_harmful'] + 0.01
    elif case == 'd4_median_differs':
        s['D4']['random_valid/openml_credit_approval']['second_half_of_audited']['median'] += 1e-6
    elif case == 'd4_n_differs': s['D4']['scripted/openml_ionosphere']['budget_index_gt_10']['n'] += 1
    elif case == 'd7_rounded_bound':
        s['D7']['reference']['lower'] = 0.4239; s['D7']['inside'] = s['D7']['reference']['lower'] <= s['D7']['rate'] <= s['D7']['reference']['upper']
    elif case == 'd7_wrong_source_sha': s['D7']['reference']['sha256'] = '0' * 64
    elif case == 'proposals_out_of_order':
        r = next(r for r in doc['rows'] if len(r['proposals']) >= 2); r['proposals'] = r['proposals'][::-1]
    path = write(tmp_path, doc, **({'tail': tail} if tail else {}))
    _refused(an, path, capsys, match)
