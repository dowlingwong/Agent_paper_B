"""Synthetic known-answer tests for the R1-BX-D8 aggregate gate (no real data)."""
import copy
import json
import math

import numpy as np
import pytest

from r1.c3 import gate
from r1.c3.d8_point_statistics import node_iqm


@pytest.fixture
def confirmed(monkeypatch):
    """Replace only the D8 authority check; every test that uses this records it."""
    calls = []
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: calls.append(1))
    return calls


def node(name, suite='S1', tier='T1', *, a2, oracle, a3, a5, dev_a2=None, dev_oracle=None,
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


def table(*nodes, suites=('S1',)):
    return {'schema': gate.INPUT_SCHEMA, 'expected_suites': list(suites), 'nodes': list(nodes)}


# --------------------------------------------------------------- known answers

def test_degenerate_bootstrap_known_iqm_poi_and_pass(confirmed):
    # Zero within-node variance: every resample equals the point estimate.
    t = table(constant_node('n1', 0.2, 0.0), constant_node('n2', 0.4, 0.0, tier='T0'),
              constant_node('n3', 0.6, 0.0), constant_node('n4', 0.8, 0.0, tier='T0'))
    r = gate.evaluate(t)
    assert confirmed == [1]
    a3 = r['arms']['A3']
    assert a3['iqm_gap_closed'] == pytest.approx(0.5)            # (0.4 + 0.6) / 2
    assert a3['probability_of_improvement'] == 1.0
    assert a3['lower_iqm_gap_closed'] == pytest.approx(0.5)
    assert a3['lower_probability_of_improvement'] == 1.0
    assert r['first_ranked_arm'] == 'A3' and a3['level'] == 0.975 and a3['passed']
    assert a3['meets_practical_size']
    # A5 equals A2 everywhere: IQM 0 and PoI 0.5 fail the strict bounds.
    a5 = r['arms']['A5']
    assert a5['iqm_gap_closed'] == 0.0 and a5['probability_of_improvement'] == 0.5
    assert a5['rank'] == 2 and a5['level'] == 0.95 and a5['tested'] and not a5['passed']
    assert r['verdict'] == 'PASS'
    assert r['node_counts'] == {'total': 4, 'by_tier': {'T0': 2, 'T1': 2},
                                'by_suite_and_tier': {'S1': {'T0': 2, 'T1': 2}}}


def test_strict_bounds_ties_and_zero_gap_fail(confirmed):
    t = table(constant_node('n1', 0.0, 0.0), constant_node('n2', 0.0, 0.0))
    r = gate.evaluate(t)
    for arm in gate.ARMS:
        assert r['arms'][arm]['lower_iqm_gap_closed'] == 0.0
        assert r['arms'][arm]['lower_probability_of_improvement'] == 0.5
        assert not r['arms'][arm]['passed']
    assert r['verdict'] == 'FAIL'
    # Holm: the second arm is not tested when the first-ranked arm fails.
    second = [a for a in gate.ARMS if r['arms'][a]['rank'] == 2][0]
    assert not r['arms'][second]['tested']


def test_dev_exclusion_drops_node_from_iqm_but_keeps_it_in_poi(confirmed):
    # n4's dev denominator 0.01 < delta 0.05: its gap (100) must not enter the IQM;
    # its PoI (A3 below A2 everywhere: 0) must enter the mean.
    excluded = node('n4', a2=[0.0] * 5, oracle=[1.0] * 5, a3=[-1.0] * 5, a5=[0.0] * 5,
                    dev_a2=[0.0] * 4, dev_oracle=[0.01] * 4)
    t = table(constant_node('n1', 0.2, 0.1), constant_node('n2', 0.4, 0.1),
              constant_node('n3', 0.6, 0.1), excluded)
    r = gate.evaluate(t)
    assert r['excluded_from_iqm'] == ['n4']
    assert r['nodes']['n4']['included_in_iqm'] is False
    assert r['nodes']['n4']['gap_closed_A3'] is None
    assert r['arms']['A3']['iqm_gap_closed'] == pytest.approx(node_iqm([0.2, 0.4, 0.6]))
    assert r['arms']['A3']['probability_of_improvement'] == pytest.approx(0.75)
    assert r['arms']['A5']['probability_of_improvement'] == pytest.approx((1 + 1 + 1 + 0.5) / 4)


def test_dev_denominator_equal_to_delta_is_included(confirmed):
    edge = constant_node('n2', 0.3, 0.3, dev_oracle=[0.05] * 4, delta=0.05)
    r = gate.evaluate(table(constant_node('n1', 0.1, 0.1), edge))
    assert r['excluded_from_iqm'] == []


def test_ratio_of_means_gap_closed(confirmed):
    n = node('n1', a2=[0.0, 2.0], oracle=[2.0, 4.0], a3=[1.0, 2.0], a5=[0.0, 2.0])
    r = gate.evaluate(table(n, constant_node('n2', 0.5, 0.5)))
    # (mean A3 - mean A2) / (mean oracle - mean A2) = (1.5 - 1) / (3 - 1)
    assert r['nodes']['n1']['gap_closed_A3'] == pytest.approx(0.25)
    assert r['nodes']['n1']['poi_A3'] == pytest.approx(0.75)    # win, tie


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
                dev = sum(n['dev']['oracle']) / len(n['dev']['oracle']) - sum(n['dev']['A2']) / len(n['dev']['A2'])
                if dev >= n['delta_n']:
                    m = {k: sum(v[k]) / len(pick) for k in gate.SERIES}
                    gaps.append((m[arm] - m['A2']) / (m['oracle'] - m['A2']))
            iqms.append(node_iqm(gaps)); pois.append(sum(rates) / len(rates))
        out[arm] = (np.array(iqms), np.array(pois))
    return out


def noisy_table(seed=5, nodes=6, n=12, lift=(0.3, 0.1)):
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(nodes):
        a2 = rng.normal(0, 0.2, n); oracle = a2 + 1 + rng.normal(0, 0.05, n)
        rows.append(node(f'n{k}', suite=f'S{k % 2}', tier='T1' if k < 2 else 'T0',
                         a2=a2.round(3).tolist(), oracle=oracle.round(3).tolist(),
                         a3=(a2 + lift[0] + rng.normal(0, 0.3, n)).round(3).tolist(),
                         a5=(a2 + lift[1] + rng.normal(0, 0.3, n)).round(3).tolist()))
    return table(*rows, suites=('S0', 'S1'))


def test_bootstrap_matches_independent_reference_loop(confirmed):
    t = noisy_table(nodes=4, n=6)
    _, nodes = gate._validate(t)
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
        rows.append(node(f'n{k}', tier='T1', a2=a2.tolist(), oracle=[1.0] * 400,
                         a3=a3.tolist(), a5=a3.tolist()))
    r = gate.evaluate(table(*rows))
    a3 = r['arms']['A3']
    se = math.sqrt(a3['probability_of_improvement'] * (1 - a3['probability_of_improvement']) / 1600)
    assert a3['level'] == 0.975          # A5 is identical; the fixed tie-break ranks A3 first
    lb = a3['lower_probability_of_improvement']
    assert lb == pytest.approx(a3['probability_of_improvement'] - 1.96 * se, abs=0.25 * se)


def test_deterministic_and_order_invariant(confirmed):
    t = noisy_table()
    r1 = gate.evaluate(t)
    shuffled = copy.deepcopy(t)
    shuffled['nodes'].reverse()
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


# ---------------------------------------------------------------- STOP cases

def test_resampled_nonpositive_denominator_stops_without_dropping(confirmed):
    # Point denominator 0.1/3 > 0, but resamples of the first instance alone give -0.9.
    risky = node('n2', a2=[0.0, 0.0, 0.0], oracle=[-0.9, 1.0, 0.0], a3=[0.1, 0.1, 0.1], a5=[0, 0, 0])
    with pytest.raises(gate.GateStop, match='resampled oracle-A2 denominators'):
        gate.evaluate(table(constant_node('n1', 0.5, 0.5), risky))


def test_risky_denominator_on_excluded_node_does_not_stop(confirmed):
    risky = node('n2', a2=[0.0, 0.0, 0.0], oracle=[-0.9, 1.0, 0.0], a3=[0.1, 0.1, 0.1], a5=[0, 0, 0],
                 dev_oracle=[0.0] * 4)
    r = gate.evaluate(table(constant_node('n1', 0.5, 0.5), risky))
    assert r['excluded_from_iqm'] == ['n2']


def test_nonpositive_point_test_denominator_stops(confirmed):
    bad = node('n2', a2=[1.0] * 3, oracle=[1.0] * 3, a3=[1.0] * 3, a5=[1.0] * 3)
    with pytest.raises(gate.GateStop, match='nonpositive test'):
        gate.evaluate(table(constant_node('n1', 0.5, 0.5), bad))


def test_no_eligible_node_stops(confirmed):
    with pytest.raises(gate.GateStop, match='IQM is undefined'):
        gate.evaluate(table(constant_node('n1', 0.5, 0.5, dev_oracle=[0.0] * 4)))


def test_suite_without_t1_node_stops_and_counts_are_disclosed(confirmed):
    t = table(constant_node('n1', 0.5, 0.5, suite='S1', tier='T1'),
              constant_node('n2', 0.5, 0.5, suite='S2', tier='T0'), suites=('S1', 'S2'))
    with pytest.raises(gate.GateStop, match=r"suites without a labelled T1 node: \['S2'\]"):
        gate.evaluate(t)
    t['nodes'].append(constant_node('n3', 0.5, 0.5, suite='S2', tier='T1'))
    r = gate.evaluate(t)
    assert r['node_counts']['by_suite_and_tier'] == {'S1': {'T0': 0, 'T1': 1}, 'S2': {'T0': 1, 'T1': 1}}
    assert r['tier_descriptive']['T0']['n_nodes'] == 1 and r['tier_descriptive']['T1']['n_nodes'] == 2


def test_expected_suite_with_no_nodes_stops(confirmed):
    with pytest.raises(gate.GateStop, match='S9'):
        gate.evaluate(table(constant_node('n1', 0.5, 0.5), suites=('S1', 'S9')))


# ---------------------------------------------------------------- validation

def mutate(path, value):
    t = table(constant_node('n1', 0.5, 0.5), constant_node('n2', 0.5, 0.5))
    target = t
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return t


@pytest.mark.parametrize('path,value', [
    (('schema',), 'other'),
    (('nodes', 0, 'node'), 'n2'),
    (('nodes', 0, 'tier'), 'T2'),
    (('nodes', 0, 'suite'), 'S9'),
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


def test_fixed_protocol_constants():
    assert (gate.N_RESAMPLES, gate.SEED, gate.LEVELS, gate.FAMILY_ALPHA) == (2000, 20261108, (0.975, 0.95), 0.05)
    assert gate.ARMS == ('A3', 'A5') and gate.PRACTICAL_SIZE == 0.1 and gate.CONFIRM_ID == 'R1-BX-D8-CONFIRM'
