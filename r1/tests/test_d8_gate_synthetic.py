"""Synthetic known-answer tests for the R1-BX-D8 aggregate gate (no real data).

Every table that reaches ``gate.evaluate`` has the real layout: the eight pinned
T0 CPU nodes, which belong to no suite, plus T1 nodes from each pinned suite.
Node utilities are synthetic; no real label, audit value or table is read.
"""
import copy
import json
import math

import numpy as np
import pytest

from r1.c3 import gate
from r1.c3.d8_point_statistics import node_iqm, node_equal_probability_of_improvement
from r1.c3.d8_inference_primitives import holm_two

T0 = sorted(gate.T0_NODES)
AR, MLAB, MLGYM = 'autoresearch', 'MLAgentBench', 'MLGym'


@pytest.fixture
def confirmed(monkeypatch):
    """Replace only the D8 authority check and accept this environment's NumPy.

    The NumPy pin itself is tested separately (``test_numpy_pin_*``); here it is
    set to the running version so that the statistics can be tested.
    """
    calls = []
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: calls.append(1))
    monkeypatch.setattr(gate, 'NUMPY_VERSION', np.__version__)
    return calls


def node(name, suite=MLGYM, tier='T1', *, a2, oracle, a3, a5, dev_a2=None, dev_oracle=None,
         delta=0.05, ids=None):
    n = len(a2)
    return {'node': name, 'suite': suite, 'tier': tier, 'delta_n': delta,
            'dev': {'A2': list(dev_a2 if dev_a2 is not None else [0.0] * 4),
                    'oracle': list(dev_oracle if dev_oracle is not None else [1.0] * 4)},
            'test': {'instance_ids': ids or [f'{name}-i{i:03d}' for i in range(n)],
                     'A2': list(a2), 'oracle': list(oracle), 'A3': list(a3), 'A5': list(a5)}}


def constant_node(name, gap3, gap5, n=5, **kw):
    """A2 = 0, oracle = 1 on every instance: gap closed equals the arm utility."""
    return node(name, a2=[0.0] * n, oracle=[1.0] * n, a3=[gap3] * n, a5=[gap5] * n, **kw)


def t0_node(i, gap3, gap5, **kw):
    """The i-th pinned T0 node (sorted order), no suite."""
    return constant_node(T0[i], gap3, gap5, tier='T0', suite=None, **kw)


def t1_nodes(gap3, gap5, **kw):
    """One constant T1 node per pinned suite, named after the suite."""
    return [constant_node(f'{s.lower()}_t1', gap3, gap5, suite=s, **kw) for s in gate.SUITES]


def table(*nodes):
    return {'schema': gate.INPUT_SCHEMA, 'nodes': list(nodes)}


def layout(t1, t0=None, t0_gap=(0.5, 0.5)):
    """The real shape: the 8 pinned T0 nodes (``t0`` overrides by index) plus ``t1``."""
    t0 = dict(t0 or {})
    return table(*[t0.get(i) or t0_node(i, *t0_gap) for i in range(len(T0))], *t1)


# --------------------------------------------------------------- known answers

def test_degenerate_bootstrap_known_iqm_poi_and_pass(confirmed):
    # Zero within-node variance: every resample equals the point estimate.
    # 12 nodes (8 T0 + 4 T1) with A3 gaps 0.05, 0.10, ..., 0.60: the IQM of 12
    # values is the mean of the middle six, (0.20 + ... + 0.45) / 6 = 0.325.
    gaps = [0.05 * (k + 1) for k in range(12)]
    t0 = {i: t0_node(i, gaps[i], 0.0) for i in range(8)}
    t1 = [constant_node('ar1', gaps[8], 0.0, suite=AR), constant_node('mlab1', gaps[9], 0.0, suite=MLAB),
          constant_node('mlgym1', gaps[10], 0.0, suite=MLGYM), constant_node('mlgym2', gaps[11], 0.0, suite=MLGYM)]
    r = gate.evaluate(layout(t1, t0))
    assert confirmed == [1]
    a3 = r['arms']['A3']
    assert a3['iqm_gap_closed'] == pytest.approx(0.325)
    assert a3['probability_of_improvement'] == 1.0
    assert a3['lower_iqm_gap_closed'] == pytest.approx(0.325)
    assert a3['lower_probability_of_improvement'] == 1.0
    assert r['first_ranked_arm'] == 'A3' and a3['level'] == 0.975 and a3['passed']
    assert a3['meets_practical_size']
    # A5 equals A2 everywhere: IQM 0 and PoI 0.5 fail the strict bounds.
    a5 = r['arms']['A5']
    assert a5['iqm_gap_closed'] == 0.0 and a5['probability_of_improvement'] == 0.5
    assert a5['rank'] == 2 and a5['level'] == 0.95 and a5['tested'] and not a5['passed']
    assert r['verdict'] == 'PASS'
    assert r['node_counts'] == {'total': 12, 'by_tier': {'T0': 8, 'T1': 4},
                                't1_by_suite': {AR: 1, MLAB: 1, MLGYM: 2}}
    assert r['nodes'][T0[0]]['suite'] is None and r['nodes']['ar1']['suite'] == AR
    assert r['tier_descriptive']['T0']['iqm_gap_closed_A3'] == pytest.approx(node_iqm(gaps[:8]))
    assert r['tier_descriptive']['T1']['iqm_gap_closed_A3'] == pytest.approx(node_iqm(gaps[8:]))


def test_strict_bounds_ties_and_zero_gap_fail(confirmed):
    r = gate.evaluate(layout(t1_nodes(0.0, 0.0), t0_gap=(0.0, 0.0)))
    for arm in gate.ARMS:
        assert r['arms'][arm]['lower_iqm_gap_closed'] == 0.0
        assert r['arms'][arm]['lower_probability_of_improvement'] == 0.5
        assert not r['arms'][arm]['passed']
    assert r['verdict'] == 'FAIL'
    # Holm: the second arm is not tested when the first-ranked arm fails.
    second = [a for a in gate.ARMS if r['arms'][a]['rank'] == 2][0]
    assert not r['arms'][second]['tested']


def test_dev_exclusion_drops_node_from_iqm_but_keeps_it_in_poi(confirmed):
    # The MLGym T1 node's dev denominator 0.01 < delta 0.05: its gap (-1) must not
    # enter the IQM; its PoI (A3 below A2 everywhere: 0) must enter the mean.
    excluded = node('mlgym_x', a2=[0.0] * 5, oracle=[1.0] * 5, a3=[-1.0] * 5, a5=[0.0] * 5,
                    dev_a2=[0.0] * 4, dev_oracle=[0.01] * 4)
    gaps = [0.1 * (k + 1) for k in range(10)]
    t0 = {i: t0_node(i, gaps[i], 0.1) for i in range(8)}
    t1 = [constant_node('ar1', gaps[8], 0.1, suite=AR), constant_node('mlab1', gaps[9], 0.1, suite=MLAB), excluded]
    r = gate.evaluate(layout(t1, t0))
    assert r['excluded_from_iqm'] == ['mlgym_x']
    assert r['nodes']['mlgym_x']['included_in_iqm'] is False
    assert r['nodes']['mlgym_x']['gap_closed_A3'] is None
    # IQM of 0.1..1.0 (10 values): weights 2,4,4,4,4,4,2 quarters on ranks 3..9 / 20.
    assert r['arms']['A3']['iqm_gap_closed'] == pytest.approx(node_iqm(gaps)) == pytest.approx(0.55)
    assert r['arms']['A3']['probability_of_improvement'] == pytest.approx(10 / 11)
    assert r['arms']['A5']['probability_of_improvement'] == pytest.approx((10 + 0.5) / 11)
    # A suite whose only T1 node is IQM-excluded still counts as labelled.
    assert r['node_counts']['t1_by_suite'][MLGYM] == 1


def test_dev_denominator_equal_to_delta_is_included(confirmed):
    edge = constant_node('mlgym1', 0.3, 0.3, dev_oracle=[0.05] * 4, delta=0.05)
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), edge]))
    assert r['excluded_from_iqm'] == []


def test_ratio_of_means_gap_closed(confirmed):
    n = node('mlgym1', a2=[0.0, 2.0], oracle=[2.0, 4.0], a3=[1.0, 2.0], a5=[0.0, 2.0])
    r = gate.evaluate(layout([constant_node('ar1', 0.5, 0.5, suite=AR),
                              constant_node('mlab1', 0.5, 0.5, suite=MLAB), n]))
    # (mean A3 - mean A2) / (mean oracle - mean A2) = (1.5 - 1) / (3 - 1)
    assert r['nodes']['mlgym1']['gap_closed_A3'] == pytest.approx(0.25)
    assert r['nodes']['mlgym1']['poi_A3'] == pytest.approx(0.75)    # win, tie


def test_inlined_point_statistics_equal_the_accepted_core():
    rng = np.random.default_rng(3)
    for n in range(1, 30):
        v = rng.normal(0, 1, n).round(2).tolist()
        assert gate._node_iqm(v) == node_iqm(v)
        pairs = [(rng.integers(0, 3, k).astype(float).tolist(), rng.integers(0, 3, k).astype(float).tolist())
                 for k in rng.integers(1, 9, n)]
        assert gate._node_poi(pairs) == node_equal_probability_of_improvement(pairs)


# ------------------------------------------------- bootstrap against a reference

def reference_bootstrap(t):
    """Independent slow loop with the same documented draw order and seed."""
    nodes = sorted(t['nodes'], key=lambda n: n['node'])
    rng = np.random.Generator(np.random.PCG64(gate.SEED))
    draws = {}
    for n in nodes:
        order = sorted(range(len(n['test']['instance_ids'])), key=n['test']['instance_ids'].__getitem__)
        size = len(order)
        draws[n['node']] = (rng.integers(0, size, size=(gate.N_RESAMPLES, size)), order)
    out = {}
    for arm in gate.ARMS:
        iqms, pois = [], []
        for b in range(gate.N_RESAMPLES):
            gaps, rates = [], []
            for n in nodes:
                idx, order = draws[n['node']]
                pick = [order[i] for i in idx[b]]
                v = {k: [n['test'][k][i] for i in pick] for k in gate.SERIES}
                rates.append(sum(1.0 if x > y else 0.5 if x == y else 0.0
                                 for x, y in zip(v[arm], v['A2'])) / len(pick))
                dev = (sum(n['dev']['oracle']) / len(n['dev']['oracle'])
                       - sum(n['dev']['A2']) / len(n['dev']['A2']))
                if dev >= n['delta_n']:
                    m = {k: sum(v[k]) / len(pick) for k in gate.SERIES}
                    gaps.append((m[arm] - m['A2']) / (m['oracle'] - m['A2']))
            iqms.append(node_iqm(gaps)); pois.append(sum(rates) / len(rates))
        out[arm] = (np.array(iqms), np.array(pois))
    return out


def noisy_table(seed=5, n=12, lift=(0.3, 0.1), t1_per_suite=(1, 2, 1)):
    """Real layout: 8 T0 nodes (no suite) and T1 nodes per suite, noisy utilities."""
    rng = np.random.default_rng(seed)
    names = [(k, 'T0', None) for k in T0]
    for suite, count in zip(gate.SUITES, t1_per_suite):
        names += [(f'{suite.lower()}_{j}', 'T1', suite) for j in range(count)]
    rows = []
    for name, tier, suite in names:
        a2 = rng.normal(0, 0.2, n); oracle = a2 + 1 + rng.normal(0, 0.05, n)
        rows.append(node(name, suite=suite, tier=tier,
                         a2=a2.round(3).tolist(), oracle=oracle.round(3).tolist(),
                         a3=(a2 + lift[0] + rng.normal(0, 0.3, n)).round(3).tolist(),
                         a5=(a2 + lift[1] + rng.normal(0, 0.3, n)).round(3).tolist()))
    return table(*rows)


def test_bootstrap_matches_independent_reference_loop(confirmed):
    t = noisy_table(n=6)
    nodes = gate._validate(t)
    eligible, _, _ = gate._point(nodes)
    got = gate._bootstrap(nodes, eligible)
    ref = reference_bootstrap(t)
    for arm in gate.ARMS:
        np.testing.assert_allclose(got[arm][0], ref[arm][0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(got[arm][1], ref[arm][1], rtol=0, atol=1e-12)


def test_poi_lower_bound_matches_normal_theory_for_large_nodes(confirmed):
    # Four nodes, 400 instances, wins with probability 0.7 and no ties: the PoI
    # bootstrap SE is about sqrt(0.21/400)/2; the 97.5% lower bound sits ~1.96 SE below.
    rng = np.random.default_rng(11)
    rows = []
    for k in range(4):
        win = rng.random(400) < 0.7
        a2 = np.zeros(400); a3 = np.where(win, 0.5, -0.5)
        rows.append(node(T0[k], tier='T0', suite=None, a2=a2.tolist(), oracle=[1.0] * 400,
                         a3=a3.tolist(), a5=a3.tolist()))
    # The remaining 4 T0 and 3 T1 nodes have PoI exactly 1 and zero bootstrap
    # variance; the overall PoI is (sum of four noisy rates + 7) / 11.
    rest = [t0_node(i, 0.5, 0.5) for i in range(4, 8)] + t1_nodes(0.5, 0.5)
    r = gate.evaluate(table(*rows, *rest))
    a3 = r['arms']['A3']
    noisy = (a3['probability_of_improvement'] * 11 - 7) / 4
    se = math.sqrt(noisy * (1 - noisy) / 1600) * 4 / 11
    assert a3['level'] == 0.975          # A5 is identical; the fixed tie-break ranks A3 first
    lb = a3['lower_probability_of_improvement']
    assert lb == pytest.approx(a3['probability_of_improvement'] - 1.96 * se, abs=0.25 * se)
    assert r['excluded_from_iqm'] == []


def test_deterministic_and_order_invariant(confirmed):
    t = noisy_table()
    r1 = gate.evaluate(t)
    shuffled = copy.deepcopy(t)
    shuffled['nodes'].reverse()
    assert r1['node_counts']['total'] == 12
    for n in shuffled['nodes']:
        perm = list(reversed(range(len(n['test']['instance_ids']))))
        for k in ('instance_ids', *gate.SERIES):
            n['test'][k] = [n['test'][k][i] for i in perm]
    r2 = gate.evaluate(shuffled)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    assert r1['protocol']['seed'] == 20261108 and r1['protocol']['resamples'] == 2000
    assert r1['protocol']['gate_sha256'] == gate.gate_file_sha256()


# ------------------------------------------------------------ Holm decisions

def boot(iqm_values, poi_values):
    return np.asarray(iqm_values, dtype=float), np.asarray(poi_values, dtype=float)


def grid(lo, hi):
    """2000 evenly spaced values: the linear 2.5% and 5% quantiles are known."""
    return np.linspace(lo, hi, gate.N_RESAMPLES)


def q(lo, hi, level):
    return lo + (hi - lo) * (1 - level)


def test_holm_ranks_by_composite_p_and_uses_975_then_95():
    # A5 has the smaller composite p-value and is tested first at 97.5%.
    b = {'A3': boot(grid(-0.01, 1.0), grid(0.6, 0.9)), 'A5': boot(grid(0.1, 1.0), grid(0.6, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert first == 'A5' and arms['A5']['level'] == 0.975 and passed
    assert arms['A5']['lower_iqm_gap_closed'] == pytest.approx(q(0.1, 1.0, 0.975))
    assert arms['A3']['level'] == 0.95 and arms['A3']['tested']
    assert arms['A3']['lower_iqm_gap_closed'] == pytest.approx(q(-0.01, 1.0, 0.95))
    assert arms['A3']['passed'] == (q(-0.01, 1.0, 0.95) > 0)


def test_first_arm_passing_only_at_95_fails_the_gate():
    # lower 2.5% quantile < 0 < lower 5% quantile: it would pass only without Holm.
    lo, hi = -0.04, 0.96
    assert q(lo, hi, 0.975) < 0 < q(lo, hi, 0.95)
    b = {'A3': boot(grid(lo, hi), grid(0.6, 0.9)), 'A5': boot(grid(-1, 0), grid(0.4, 0.45))}
    arms, first, passed = gate._holm_decision(b)
    assert first == 'A3' and not passed
    assert not arms['A5']['tested'] and not arms['A5']['passed']


def test_both_criteria_required():
    b = {'A3': boot(grid(0.2, 0.9), grid(0.45, 0.9)), 'A5': boot(grid(0.2, 0.9), grid(0.45, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert arms[first]['lower_iqm_gap_closed'] > 0 and arms[first]['lower_probability_of_improvement'] < 0.5
    assert not passed


def test_second_arm_passes_at_95_after_first_passes():
    lo, hi = -0.04, 0.96
    b = {'A3': boot(grid(0.5, 1.0), grid(0.7, 0.9)), 'A5': boot(grid(lo, hi), grid(0.7, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert first == 'A3' and passed
    assert arms['A5']['rank'] == 2 and arms['A5']['passed']


def test_ranking_tie_uses_fixed_arm_order():
    same = boot(grid(0.2, 0.9), grid(0.7, 0.9))
    arms, first, _ = gate._holm_decision({'A3': same, 'A5': same})
    assert first == 'A3' and arms['A5']['rank'] == 2


def swapped(b):
    return {'A3': b['A5'], 'A5': b['A3']}


def test_reviewer_boundary_tie_verdict_does_not_depend_on_labels():
    # REVIEW_M11_D8_round1 finding 4: both arms have exactly 50 of 2000 draws <= 0
    # (composite p = 0.025), but the interpolated 2.5% quantile is -0.015 for A3
    # and +0.975 for A5. Ranking on p alone tied, and the label order decided
    # the verdict (FAIL as labelled, PASS with the labels swapped).
    a3 = np.r_[np.full(50, -1.0), np.full(1950, 0.01)]
    a5 = np.r_[np.full(50, -0.001), np.full(1950, 1.0)]
    poi = np.full(2000, 0.9)
    b = {'A3': (a3, poi), 'A5': (a5, poi)}
    assert gate._lower(a3, 0.975) < 0 < gate._lower(a5, 0.975)
    arms, first, passed = gate._holm_decision(b)
    arms_s, first_s, passed_s = gate._holm_decision(swapped(b))
    assert arms['A3']['ranking_p_composite'] == arms['A5']['ranking_p_composite'] == 0.025
    assert passed and passed_s
    assert first == 'A5' and first_s == 'A3'          # the arm holding the passing data


def test_label_swap_never_changes_the_verdict_or_pass_set():
    rng = np.random.default_rng(17)
    for _ in range(400):
        b = {}
        for arm in gate.ARMS:
            # exactly 50 or 100 draws at or below the null (tail share 0.025 / 0.05)
            # with varying gaps to the next draw, plus unconstrained cases
            k = int(rng.choice([50, 100, int(rng.integers(30, 120))]))
            low = 0.0005 if rng.random() < 0.7 else -0.05
            iqm = np.r_[np.full(k, rng.choice([-1.0, -0.01, 0.0])), rng.uniform(low, 1, 2000 - k)]
            poi = np.r_[np.full(k, rng.choice([0.4, 0.5])), rng.uniform(0.5 + low, 0.9, 2000 - k)]
            b[arm] = (rng.permutation(iqm), rng.permutation(poi))
        arms, _, passed = gate._holm_decision(b)
        arms_s, _, passed_s = gate._holm_decision(swapped(b))
        assert passed == passed_s
        assert {a for a in gate.ARMS if arms[a]['passed']} == \
            {('A5' if a == 'A3' else 'A3') for a in gate.ARMS if arms_s[a]['passed']}
        assert passed == any(gate._passes(b[a], 0.975) for a in gate.ARMS)


def test_verdict_agrees_with_accepted_holm_two_away_from_the_boundary():
    """The gate verdict is min(Holm-adjusted composite p) <= 0.05 when no draw count is at a boundary."""
    rng = np.random.default_rng(23)
    checked = 0
    for _ in range(300):
        b = {arm: (rng.normal(rng.uniform(-0.1, 0.4), 0.12, 2000), rng.normal(rng.uniform(0.45, 0.75), 0.08, 2000))
             for arm in gate.ARMS}
        p = {a: max(float(np.mean(b[a][0] <= 0)), float(np.mean(b[a][1] <= 0.5))) for a in gate.ARMS}
        if any(abs(v - t) < 0.003 for v in p.values() for t in (0.025, 0.05)):
            continue
        _, _, passed = gate._holm_decision(b)
        assert passed == (min(holm_two(p['A3'], p['A5']).values()) <= 0.05)
        checked += 1
    assert checked > 200


# ---------------------------------------------------------------- STOP cases

def risky_node(name='mlgym_r', **kw):
    # Point denominator 0.1/3 > 0, but resamples of the first instance alone give -0.9.
    return node(name, a2=[0.0, 0.0, 0.0], oracle=[-0.9, 1.0, 0.0], a3=[0.1, 0.1, 0.1], a5=[0, 0, 0], **kw)


def test_resampled_nonpositive_denominator_stops_without_dropping(confirmed):
    with pytest.raises(gate.GateStop, match='resampled oracle-A2 denominators'):
        gate.evaluate(layout(t1_nodes(0.5, 0.5) + [risky_node()]))


def test_every_node_with_nonpositive_resampled_denominators_is_listed(confirmed):
    t = layout(t1_nodes(0.5, 0.5) + [risky_node('mlgym_r1'), risky_node('mlgym_r2', suite=MLGYM)])
    with pytest.raises(gate.GateStop) as stop:
        gate.evaluate(t)
    assert "'mlgym_r1'" in str(stop.value) and "'mlgym_r2'" in str(stop.value)


def test_risky_denominator_on_excluded_node_does_not_stop(confirmed):
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5) + [risky_node(dev_oracle=[0.0] * 4)]))
    assert r['excluded_from_iqm'] == ['mlgym_r']


def test_nonpositive_point_test_denominator_stops(confirmed):
    bad = node('mlgym_b', a2=[1.0] * 3, oracle=[1.0] * 3, a3=[1.0] * 3, a5=[1.0] * 3)
    with pytest.raises(gate.GateStop, match=r"nonpositive test oracle-A2 denominator on IQM nodes \['mlgym_b'\]"):
        gate.evaluate(layout(t1_nodes(0.5, 0.5) + [bad]))


def test_no_eligible_node_stops(confirmed):
    t = layout(t1_nodes(0.5, 0.5, dev_oracle=[0.0] * 4), t0={i: t0_node(i, 0.5, 0.5, dev_oracle=[0.0] * 4)
                                                             for i in range(8)})
    with pytest.raises(gate.GateStop, match='IQM is undefined'):
        gate.evaluate(t)


# ------------------------------------------------------------- node layout

def test_real_layout_t0_without_suite_plus_three_t1_suites_runs(confirmed):
    """The reviewer's shape: 8 T0 nodes with no suite plus 2 T1 nodes per suite."""
    t = noisy_table(t1_per_suite=(2, 2, 2))
    r = gate.evaluate(t)
    assert r['node_counts'] == {'total': 14, 'by_tier': {'T0': 8, 'T1': 6},
                                't1_by_suite': {AR: 2, MLAB: 2, MLGYM: 2}}
    assert r['verdict'] in ('PASS', 'FAIL')
    assert r['protocol']['t0_nodes'] == list(gate.T0_NODES) and r['protocol']['suites'] == list(gate.SUITES)


@pytest.mark.parametrize('suite', [AR, MLAB, MLGYM])
def test_suite_without_t1_node_stops(confirmed, suite):
    t = noisy_table(t1_per_suite=tuple(0 if s == suite else 2 for s in gate.SUITES))
    with pytest.raises(gate.GateStop, match=rf"suites without a labelled T1 node: \['{suite}'\]"):
        gate.evaluate(t)


def test_t0_only_stops(confirmed):
    with pytest.raises(gate.GateStop, match='suites without a labelled T1 node'):
        gate.evaluate(layout([]))


def test_missing_t0_node_stops(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    del t['nodes'][3]
    with pytest.raises(gate.GateStop, match=rf"missing \['{T0[3]}'\]"):
        gate.evaluate(t)


def test_extra_or_renamed_t0_node_stops(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    t['nodes'].append(constant_node('openml_blood_transfusion', 0.5, 0.5, tier='T0', suite=None))
    with pytest.raises(gate.GateStop, match=r"unexpected \['openml_blood_transfusion'\]"):
        gate.evaluate(t)
    t = layout(t1_nodes(0.5, 0.5))
    t['nodes'][0]['node'] = 'digits_mlp_v2'
    with pytest.raises(gate.GateStop, match='T0 nodes must be exactly'):
        gate.evaluate(t)


def test_t0_node_relabelled_as_t1_stops(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    t['nodes'][0].update(tier='T1', suite=MLGYM)
    with pytest.raises(gate.GateStop, match='T0 nodes must be exactly'):
        gate.evaluate(t)


def test_t0_node_with_a_suite_stops(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    t['nodes'][0]['suite'] = MLGYM
    with pytest.raises(gate.GateStop, match='T0 nodes belong to no suite'):
        gate.evaluate(t)


@pytest.mark.parametrize('suite', [None, 'cpu_testbed', '1GC-7RC', 'mlgym'])
def test_t1_node_outside_the_pinned_suites_stops(confirmed, suite):
    t = layout(t1_nodes(0.5, 0.5) + [constant_node('extra_t1', 0.5, 0.5, suite=suite)])
    with pytest.raises(gate.GateStop, match=r"T1 nodes without a suite in .*\['extra_t1'\]"):
        gate.evaluate(t)


def test_caller_supplied_suite_list_is_refused(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    t['expected_suites'] = list(gate.SUITES)
    with pytest.raises(ValueError, match='unknown gate input fields'):
        gate.evaluate(t)


# ------------------------------------------------------- pins and binding

def test_numpy_pin_mismatch_stops_before_the_input_is_read(monkeypatch, tmp_path):
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: None)
    monkeypatch.setattr(gate, 'NUMPY_VERSION', '0.0.0-not-installed')
    with pytest.raises(gate.GateStop, match='is not the pinned NumPy 0.0.0-not-installed'):
        gate.evaluate(layout(t1_nodes(0.5, 0.5)))
    opened = []
    monkeypatch.setattr('builtins.open', lambda *a, **k: opened.append(a) or (_ for _ in ()).throw(AssertionError))
    with pytest.raises(gate.GateStop, match='pinned NumPy'):
        gate.load_and_evaluate(tmp_path / 'gate_input.json')
    assert opened == []
    with pytest.raises(gate.GateStop, match='pinned NumPy'):
        gate._evaluate(layout(t1_nodes(0.5, 0.5)))


def test_numpy_pin_match_runs(monkeypatch):
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: None)
    monkeypatch.setattr(gate.np, '__version__', gate.NUMPY_VERSION)
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5)))
    assert r['protocol']['numpy_pin'] == gate.NUMPY_VERSION == r['protocol']['numpy_version']


def test_executing_file_must_be_the_checked_gate(confirmed, monkeypatch, tmp_path):
    other = tmp_path / 'r1/c3/gate.py'; other.parent.mkdir(parents=True)
    other.write_bytes(gate.Path(gate.__file__).read_bytes())
    monkeypatch.setattr(gate.analysis_guard, 'REPO', tmp_path)      # same bytes, other path
    with pytest.raises(gate.GateStop, match='executing gate file'):
        gate.evaluate(layout(t1_nodes(0.5, 0.5)))
    monkeypatch.setattr(gate.analysis_guard, 'REPO', tmp_path / 'absent')
    with pytest.raises(gate.GateStop, match='executing gate file'):
        gate.evaluate(layout(t1_nodes(0.5, 0.5)))


def test_gate_does_not_import_the_unbound_point_statistics_module():
    import ast
    tree = ast.parse(gate.Path(gate.__file__).read_text())
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {f'{n.module}.{a.name}' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert imported == {'__future__.annotations', 'hashlib', 'json', 'math', 'sys', 'pathlib.Path',
                        'numpy', 'r1.c3.analysis_guard'}


# ---------------------------------------------------------------- validation

def mutate(path, value):
    t = layout(t1_nodes(0.5, 0.5))
    target = t
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return t


@pytest.mark.parametrize('path,value', [
    (('schema',), 'other'),
    (('nodes', 0, 'node'), T0[1]),
    (('nodes', 0, 'tier'), 'T2'),
    (('nodes', 0, 'suite'), ''),
    (('nodes', 0, 'suite'), 3),
    (('nodes', 0, 'test', 'A3'), [1e308] * 5),
    (('nodes', 0, 'dev', 'oracle'), [1e308] * 4),
    (('nodes', 0, 'delta_n'), 0.0),
    (('nodes', 0, 'delta_n'), True),
    (('nodes', 0, 'test', 'A3'), [0.5] * 4),
    (('nodes', 0, 'test', 'A3'), [True] * 5),
    (('nodes', 0, 'test', 'A2'), [float('nan')] * 5),
    (('nodes', 0, 'test', 'oracle'), [float('inf')] * 5),
    (('nodes', 0, 'test', 'instance_ids'), ['x'] * 5),
    (('nodes', 0, 'dev', 'A2'), []),
    (('nodes', 0, 'dev', 'A2'), [0.0] * 3),
    (('nodes', 0, 'extra'), 1),
    (('extra',), 1),
])
def test_malformed_inputs_refused(confirmed, path, value):
    with pytest.raises(ValueError):
        gate.evaluate(mutate(path, value))


def test_missing_suite_field_refused(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    del t['nodes'][0]['suite']
    with pytest.raises(ValueError, match='node fields must be exactly'):
        gate.evaluate(t)


def test_json_duplicate_keys_and_constants_refused(confirmed, tmp_path, monkeypatch):
    monkeypatch.setattr(gate.analysis_guard, 'refuse_sealed', lambda *a: None)
    good = json.dumps(layout(t1_nodes(0.5, 0.5)))
    path = tmp_path / 'gate_input.json'
    path.write_text(good)
    assert gate.load_and_evaluate(path)['node_counts']['total'] == 11
    path.write_text(good[:-1] + ', "nodes": []}')
    with pytest.raises(ValueError, match="duplicate JSON key 'nodes'"):
        gate.load_and_evaluate(path)
    path.write_text(good.replace('"delta_n": 0.05', '"delta_n": NaN', 1))
    with pytest.raises(ValueError, match='non-finite JSON constant NaN'):
        gate.load_and_evaluate(path)


def test_fixed_protocol_constants():
    assert (gate.N_RESAMPLES, gate.SEED, gate.LEVELS, gate.FAMILY_ALPHA) == (2000, 20261108, (0.975, 0.95), 0.05)
    assert gate.ARMS == ('A3', 'A5') and gate.PRACTICAL_SIZE == 0.1 and gate.CONFIRM_ID == 'R1-BX-D8-CONFIRM'
    assert gate.NUMPY_VERSION == '2.4.4'
    # Authorized sweep-1 node set (R1-DT-PIN-SWEEP1) and the three suites (R1-BX-D2, R1-1GC-FALLBACK).
    assert set(gate.T0_NODES) == {'digits_mlp', 'tabular_mlp', 'openml_breast_w', 'openml_ionosphere',
                                  'openml_wdbc', 'openml_credit_approval', 'openml_sonar',
                                  'openml_climate'}
    assert gate.SUITES == ('autoresearch', 'MLAgentBench', 'MLGym')


def _classifier_node_list():
    """The literal node list required by the accepted evidence classifier."""
    import ast
    from r1.c3 import dataset
    tree = ast.parse(gate.Path(dataset.__file__).read_text())
    func = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == 'evidence_classification')
    lists = [ast.literal_eval(a.value) for a in ast.walk(func)
             if isinstance(a, ast.Assign) and [getattr(t, 'id', None) for t in a.targets] == ['nodes']]
    assert len(lists) == 1
    return lists[0]


def test_t0_nodes_equal_the_classifier_and_the_authorized_sweep_config():
    """Drift between the gate's T0 pin and the authorized sweep set breaks this test, not the gate."""
    config = json.loads((gate.analysis_guard.REPO / 'r1/scripts/configs/c3_sweep_deepthought.json').read_text())
    assert set(gate.T0_NODES) == set(_classifier_node_list()) == set(config['nodes'])
    assert len(gate.T0_NODES) == len(set(gate.T0_NODES)) == 8
    assert config['nodes_pending'] == []
