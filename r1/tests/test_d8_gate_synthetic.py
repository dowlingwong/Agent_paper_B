"""Synthetic known-answer tests for the R1-BX-D8 aggregate gate, version 3 (no real data).

Every table that reaches ``gate.evaluate`` has the real layout: the eight pinned T0 CPU nodes, which belong to no
suite, plus T1 nodes from each pinned suite. Node utilities are synthetic; no real label, audit value or table is
read. Version 3 implements R1-BX-D8-V3-A items 1-3 (V1n test side, train + dev z >= 3, the P3 split) and
R1-BX-D8-V3-B items 4-5 (the studentized (b2) bound, the per-tier test floor).
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

    The NumPy pin itself is tested separately (``test_numpy_pin_*``); here it is set to the running version so that
    the statistics can be tested.
    """
    calls = []
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: calls.append(1))
    monkeypatch.setattr(gate, 'NUMPY_VERSION', np.__version__)
    return calls


def block(name, split, a2, oracle, **arms):
    ids = [f'{name}-{split}{i:03d}' for i in range(len(a2))]
    return {'instance_ids': ids, 'A2': list(a2), 'oracle': list(oracle), **{k: list(v) for k, v in arms.items()}}


def node(name, suite=MLGYM, tier='T1', *, a2, oracle, a3, a5, train_a2=None, train_oracle=None,
         dev_a2=None, dev_oracle=None, delta=0.05, ids=None):
    """Defaults: train and dev with oracle - A2 = 1 everywhere (z = +inf, eligible; dev denominator 1)."""
    out = {'node': name, 'suite': suite, 'tier': tier, 'delta_n': delta,
           'train': block(name, 'r', train_a2 if train_a2 is not None else [0.0] * 4,
                          train_oracle if train_oracle is not None else [1.0] * 4),
           'dev': block(name, 'd', dev_a2 if dev_a2 is not None else [0.0] * 2,
                        dev_oracle if dev_oracle is not None else [1.0] * 2),
           'test': block(name, 't', a2, oracle, A3=a3, A5=a5)}
    if ids is not None:
        out['test']['instance_ids'] = list(ids)
    return out


def constant_node(name, gap3, gap5, n=9, **kw):
    """A2 = 0, oracle = 1 on every test instance: gap closed equals the arm utility; zero variance."""
    return node(name, a2=[0.0] * n, oracle=[1.0] * n, a3=[gap3] * n, a5=[gap5] * n, **kw)


def t0_node(i, gap3, gap5, **kw):
    """The i-th pinned T0 node (sorted order), no suite."""
    return constant_node(T0[i], gap3, gap5, tier='T0', suite=None, **kw)


def t1_nodes(gap3, gap5, **kw):
    """One constant T1 node per pinned suite, named after the suite."""
    return [constant_node(f'{s.lower()}_t1', gap3, gap5, suite=s, **kw) for s in gate.SUITES]


def table(*nodes, t0_nodes=None):
    """v3.1 input; the declared T0 set defaults to all eight (gate v3's full layout)."""
    return {'schema': gate.INPUT_SCHEMA, 'split': dict(gate.SPLIT),
            't0_nodes': sorted(gate.T0_NODES) if t0_nodes is None else list(t0_nodes), 'nodes': list(nodes)}


def layout(t1, t0=None, t0_gap=(0.5, 0.5)):
    """The real shape: the 8 pinned T0 nodes (``t0`` overrides by index) plus ``t1``."""
    t0 = dict(t0 or {})
    return table(*[t0.get(i) or t0_node(i, *t0_gap) for i in range(len(T0))], *t1)


# --------------------------------------------------------------- known answers

def test_degenerate_bootstrap_known_iqm_poi_and_pass(confirmed):
    # Zero within-node variance up to rounding: se is ~0, so the (b2) bound is the point IQM.
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
    assert a3['se_iqm_gap_closed'] == pytest.approx(0.0, abs=1e-12)
    assert a3['probability_of_improvement'] == 1.0
    assert a3['lower_iqm_gap_closed'] == pytest.approx(0.325)
    assert a3['lower_probability_of_improvement'] == 1.0
    assert r['first_ranked_arm'] == 'A3' and a3['level'] == 0.975 and a3['passed']
    assert a3['meets_practical_size']
    # A5 equals A2 everywhere: IQM 0 and PoI 0.5 fail the strict bounds.
    a5 = r['arms']['A5']
    assert a5['iqm_gap_closed'] == 0.0 and a5['probability_of_improvement'] == 0.5
    assert a5['rank'] == 2 and a5['level'] == 0.95 and a5['tested'] and not a5['passed']
    assert r['verdict'] == 'PASS' and r['gate_version'] == '3.1'
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
                    dev_a2=[0.0] * 2, dev_oracle=[0.01] * 2)
    gaps = [0.1 * (k + 1) for k in range(10)]
    t0 = {i: t0_node(i, gaps[i], 0.1) for i in range(8)}
    t1 = [constant_node('ar1', gaps[8], 0.1, suite=AR), constant_node('mlab1', gaps[9], 0.1, suite=MLAB), excluded]
    r = gate.evaluate(layout(t1, t0))
    assert r['excluded_from_iqm'] == ['mlgym_x']
    assert r['ineligible_nodes'] == {'mlgym_x': ['delta_n']}
    assert r['nodes']['mlgym_x']['included_in_iqm'] is False
    assert r['nodes']['mlgym_x']['gap_closed_A3'] is None
    # IQM of 0.1..1.0 (10 values): weights 2,4,4,4,4,4,2 quarters on ranks 3..9 / 20.
    assert r['arms']['A3']['iqm_gap_closed'] == pytest.approx(node_iqm(gaps)) == pytest.approx(0.55)
    assert r['arms']['A3']['probability_of_improvement'] == pytest.approx(10 / 11)
    assert r['arms']['A5']['probability_of_improvement'] == pytest.approx((10 + 0.5) / 11)
    # A suite whose only T1 node is IQM-excluded still counts as labelled.
    assert r['node_counts']['t1_by_suite'][MLGYM] == 1


def test_dev_denominator_equal_to_delta_is_included(confirmed):
    edge = constant_node('mlgym1', 0.3, 0.3, dev_oracle=[0.05] * 2, delta=0.05)
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), edge]))
    assert r['excluded_from_iqm'] == []


def test_ratio_of_means_gap_closed_and_delta_method_se(confirmed):
    n = node('mlgym1', a2=[0.0, 2.0, 0.0, 2.0], oracle=[2.0, 4.0, 2.0, 4.0], a3=[1.0, 2.0, 1.0, 2.0],
             a5=[0.0, 2.0, 0.0, 2.0])
    r = gate.evaluate(layout([constant_node('ar1', 0.5, 0.5, suite=AR),
                              constant_node('mlab1', 0.5, 0.5, suite=MLAB), n]))
    # (mean A3 - mean A2) / (mean oracle - mean A2) = (1.5 - 1) / (3 - 1)
    row = r['nodes']['mlgym1']
    assert row['gap_closed_A3'] == pytest.approx(0.25)
    assert row['poi_A3'] == pytest.approx(0.75)    # win, tie, win, tie
    # a = (1, 0, 1, 0), d = (2, 2, 2, 2): var(a) = 1/3, var(d) = 0, cov = 0 -> se^2 = (1/3) / (4 * 4)
    assert row['se_gap_closed_A3'] == pytest.approx(math.sqrt((1 / 3) / 16))


def test_inlined_point_statistics_equal_the_accepted_core():
    rng = np.random.default_rng(3)
    for n in range(1, 30):
        v = rng.normal(0, 1, n).round(2).tolist()
        assert gate._node_iqm(v) == node_iqm(v)
        assert float(np.sort(v) @ gate._iqm_weights(n)) == pytest.approx(node_iqm(v), abs=1e-12)
        pairs = [(rng.integers(0, 3, k).astype(float).tolist(), rng.integers(0, 3, k).astype(float).tolist())
                 for k in rng.integers(1, 9, n)]
        assert gate._node_poi(pairs) == node_equal_probability_of_improvement(pairs)


# ------------------------------------- (b2) against the simulation's own code

NEG = -1e12
BIG = 1e12


def reference_b2(t, eligible, level):
    """The (b2) bound per arm, written as in ``r1/scripts/d8_skew_sim.py`` @ ``dc899aad`` (lines 69, 136-180).

    The data and the index draws are the gate's (same seed and draw order); the arithmetic, the sentinels and the
    sort calls are the simulation's. Returns {arm: (bound, t*)}.
    """
    nodes = sorted(t['nodes'], key=lambda n: n['node'])
    rng = np.random.Generator(np.random.PCG64(gate.SEED))
    draws = {}
    for n in nodes:
        order = sorted(range(len(n['test']['instance_ids'])), key=n['test']['instance_ids'].__getitem__)
        size = len(order)
        draws[n['node']] = (rng.integers(0, size, size=(gate.N_RESAMPLES, size)), order)
    elig = [n for n in nodes if n['node'] in eligible]
    k = len(elig)
    w = np.array([max(0, min(4 * (i + 1), 3 * k) - max(4 * i, k)) for i in range(k)], float) / (2 * k)

    def iqm_sorted(x):
        return np.sort(x, axis=-1) @ w

    def node_se(av, dv, Gv):
        n = av.shape[-1]
        va = av.var(axis=-1, ddof=1)
        vd = dv.var(axis=-1, ddof=1)
        cv = ((av - av.mean(axis=-1, keepdims=True)) * (dv - dv.mean(axis=-1, keepdims=True))).sum(axis=-1) / (n - 1)
        num = np.maximum(va + Gv ** 2 * vd - 2 * Gv * cv, 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.sqrt(num / (n * dv.mean(axis=-1) ** 2))

    data = []
    for n in elig:
        idx, order = draws[n['node']]
        v = {s: np.array([n['test'][s][i] for i in order]) for s in gate.SERIES}
        data.append((v, idx))
    d = [v['oracle'] - v['A2'] for v, _ in data]
    dmean = np.array([x.mean() for x in d])
    d_b = np.stack([x[idx].mean(axis=1) for x, (_, idx) in zip(d, data)], axis=1)
    out = {}
    for arm in gate.ARMS:
        a = [v[arm] - v['A2'] for v, _ in data]
        amean = np.array([x.mean() for x in a])
        a_b = np.stack([x[idx].mean(axis=1) for x, (_, idx) in zip(a, data)], axis=1)
        G = amean / dmean
        theta = float(iqm_sorted(G))
        bad = d_b <= 0
        with np.errstate(divide="ignore", invalid="ignore"):
            G_b = np.where(bad, NEG, a_b / d_b)
        iq_b = iqm_sorted(G_b)
        se_pt = np.array([node_se(a[j], d[j], G[j]) for j in range(k)])
        order = np.argsort(G)
        se_hat = float(np.sqrt(np.sum((w * se_pt[order]) ** 2)))
        se_b = np.empty_like(G_b)
        for j in range(k):
            idx = data[j][1]
            ab = a[j][idx]
            db = d[j][idx]
            with np.errstate(divide="ignore", invalid="ignore"):
                gb = np.where(db.mean(axis=1) > 0, ab.mean(axis=1) / db.mean(axis=1), 0.0)
            se_b[:, j] = node_se(ab, db, gb)
        ordb = np.argsort(G_b, axis=1)
        se_sorted = np.take_along_axis(se_b, ordb, axis=1)
        se_iq_b = np.sqrt(np.sum((w * se_sorted) ** 2, axis=1))
        with np.errstate(divide="ignore", invalid="ignore"):
            tstar = (iq_b - theta) / se_iq_b
        tstar = np.where(bad.any(axis=1) | ~(se_iq_b > 0) | ~np.isfinite(tstar), BIG, tstar)
        qt = float(np.quantile(tstar, level, method="linear"))
        out[arm] = ((theta - qt * se_hat) if se_hat > 0 else theta, tstar)
    return out


def sim_table(seed, dist='normal', mu=1.0, g=(0.3, 0.0), t1_per_suite=(4, 3, 3), het=True):
    """Utilities generated as in the D8-SKEW model (P3 sizes; T0 18, T1 12 instances per node)."""
    rng = np.random.default_rng(seed)

    def noise(size):
        if dist == 'normal':
            return rng.standard_normal(size)
        if dist == 'left_skewed':
            mean, sd = math.exp(0.5), math.sqrt((math.e - 1.0) * math.e)
            return -(rng.lognormal(0.0, 1.0, size) - mean) / sd
        return rng.standard_t(3, size) / math.sqrt(3.0)

    names = [(k, 'T0', None) for k in T0]
    for suite, count in zip(gate.SUITES, t1_per_suite):
        names += [(f'{suite.lower()}_{j}', 'T1', suite) for j in range(count)]
    rows = []
    for name, tier, suite in names:
        n_tr, n_dev, n_te = (6, 3, 9) if tier == 'T0' else (4, 2, 6)
        mu_j = mu * (rng.uniform(0.5, 1.5) if het else 1.0)
        a2 = rng.normal(0, 0.3, n_tr + n_dev + n_te)
        d = mu_j + noise(n_tr + n_dev + n_te)
        c = noise(n_te)
        arms = [g_k * mu_j + math.sqrt(0.5) * c + math.sqrt(0.5) * noise(n_te) for g_k in g]
        rows.append(node(name, suite=suite, tier=tier,
                         train_a2=a2[:n_tr].tolist(), train_oracle=(a2 + d)[:n_tr].tolist(),
                         dev_a2=a2[n_tr:n_tr + n_dev].tolist(), dev_oracle=(a2 + d)[n_tr:n_tr + n_dev].tolist(),
                         a2=a2[n_tr + n_dev:].tolist(), oracle=(a2 + d)[n_tr + n_dev:].tolist(),
                         a3=(a2[n_tr + n_dev:] + arms[0]).tolist(), a5=(a2[n_tr + n_dev:] + arms[1]).tolist(),
                         delta=1e-6))
    return table(*rows)


@pytest.mark.parametrize('seed,dist,mu,g', [(1, 'normal', 1.0, (0.3, 0.0)), (3, 'left_skewed', 1.0, (0.3, 0.0)),
                                            (3, 't3', 1.5, (0.3, 0.0)), (4, 'left_skewed', 0.5, (0.3, 0.0)),
                                            (2, 'normal', 2.0, (0.3, 0.0)), (1, 't3', 0.5, (0.3, 0.0)),
                                            (6, 'left_skewed', 0.5, (0.3, 0.0)),
                                            (21, 'normal', 6.0, (0.8, 0.5)), (22, 'normal', 6.0, (0.8, 0.5))])
def test_b2_bound_equals_the_simulation_code(confirmed, seed, dist, mu, g):
    t = sim_table(seed, dist, mu, g)
    nodes = gate._validate(t)
    eligible, _, summary = gate._point(nodes)
    boot, _ = gate._bootstrap(nodes, eligible, summary)
    for level in gate.LEVELS:
        ref = reference_b2(t, set(eligible), level)
        for arm in gate.ARMS:
            got = gate._lower_iqm(boot[arm], level)
            want, tstar_ref = ref[arm]
            tstar = boot[arm]['tstar']
            assert np.array_equal(tstar == gate.TSTAR_INF, tstar_ref == BIG)
            np.testing.assert_allclose(tstar, tstar_ref, rtol=1e-9, atol=1e-9)
            assert got == pytest.approx(want, rel=1e-9, abs=1e-9)
            assert (got > 0) == (want > 0)
            if seed in (21, 22):
                # high-signal tables: a positive bound not dominated by the 1e12 sentinel
                assert 0 < got < boot[arm]['theta'] and boot[arm]['infinite_tstar'] == 0


def test_point_se_matches_the_declared_formula(confirmed):
    t = sim_table(3, 'left_skewed', 1.0)
    nodes = gate._validate(t)
    eligible, table_, summary = gate._point(nodes)
    for arm in gate.ARMS:
        g, se = [], []
        for k in eligible:
            tt = nodes[k]['test']
            a = tt[arm] - tt['A2']; d = tt['oracle'] - tt['A2']; n = len(a)
            gk = a.mean() / d.mean()
            var = (np.var(a, ddof=1) + gk ** 2 * np.var(d, ddof=1)
                   - 2 * gk * np.cov(a, d, ddof=1)[0, 1]) / (n * d.mean() ** 2)
            g.append(gk); se.append(math.sqrt(max(var, 0.0)))
            assert table_[k][f'se_gap_closed_{arm}'] == pytest.approx(se[-1], rel=1e-12)
        order = np.argsort(g, kind='stable')
        w = gate._iqm_weights(len(g))
        want = math.sqrt(sum((w[i] * se[order[i]]) ** 2 for i in range(len(g))))
        assert summary[arm]['se_iqm_gap_closed'] == pytest.approx(want, rel=1e-12)


def test_poi_bootstrap_matches_an_independent_loop(confirmed):
    t = sim_table(11)
    nodes = gate._validate(t)
    eligible, _, summary = gate._point(nodes)
    boot, _ = gate._bootstrap(nodes, eligible, summary)
    ordered = sorted(t['nodes'], key=lambda n: n['node'])
    rng = np.random.Generator(np.random.PCG64(gate.SEED))
    rates = {arm: np.zeros(gate.N_RESAMPLES) for arm in gate.ARMS}
    for n in ordered:
        order = sorted(range(len(n['test']['instance_ids'])), key=n['test']['instance_ids'].__getitem__)
        idx = rng.integers(0, len(order), size=(gate.N_RESAMPLES, len(order)))
        for arm in gate.ARMS:
            for b in range(gate.N_RESAMPLES):
                pick = [order[i] for i in idx[b]]
                rates[arm][b] += sum(1.0 if n['test'][arm][i] > n['test']['A2'][i] else
                                     0.5 if n['test'][arm][i] == n['test']['A2'][i] else 0.0
                                     for i in pick) / len(pick)
    for arm in gate.ARMS:
        np.testing.assert_allclose(boot[arm]['poi'], rates[arm] / len(ordered), rtol=0, atol=1e-12)


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
    t = sim_table(5, 'left_skewed')
    r1 = gate.evaluate(t)
    shuffled = copy.deepcopy(t)
    shuffled['nodes'].reverse()
    for n in shuffled['nodes']:
        for split, keys in (('train', ('A2', 'oracle')), ('dev', ('A2', 'oracle')), ('test', gate.SERIES)):
            perm = list(reversed(range(len(n[split]['instance_ids']))))
            for k in ('instance_ids', *keys):
                n[split][k] = [n[split][k][i] for i in perm]
    r2 = gate.evaluate(shuffled)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
    assert r1['protocol']['seed'] == 20261108 and r1['protocol']['resamples'] == 2000
    assert r1['protocol']['gate_sha256'] == gate.gate_file_sha256()


def test_result_is_strict_json_with_screened_resamples(confirmed):
    r = gate.evaluate(noisy_with_risky())
    text = json.dumps(r, allow_nan=False, sort_keys=True)
    assert json.loads(text)['arms']['A3']['lower_iqm_gap_closed'] < -1e6


# ------------------------------------------------------------ Holm decisions

def grid(lo, hi):
    """2000 evenly spaced values: the linear quantiles are known."""
    return np.linspace(lo, hi, gate.N_RESAMPLES)


def arm_boot(tstar, poi, theta=1.0, se=1.0):
    return {'theta': theta, 'se_hat': se, 'tstar': np.asarray(tstar, dtype=float),
            'poi': np.asarray(poi, dtype=float), 'infinite_tstar': int(np.count_nonzero(np.asarray(tstar) == BIG))}


def q(lo, hi, level):
    return lo + (hi - lo) * level


def test_screened_resamples_use_the_simulation_sentinel():
    assert gate.TSTAR_INF == BIG
    t = np.r_[grid(-1, 1)[:1950], np.full(50, gate.TSTAR_INF)]
    assert gate._upper_quantile(t, 0.975) == float(np.quantile(t, 0.975, method='linear')) > 1e9
    assert gate._upper_quantile(t, 0.95) == float(np.quantile(t, 0.95, method='linear')) < 1
    b = arm_boot(t, grid(0.6, 0.9), theta=0.5, se=0.1)
    assert gate._lower_iqm(b, 0.975) < -1e8 and gate._lower_iqm(b, 0.95) > 0


def test_lower_bound_formula_and_se_zero():
    b = arm_boot(grid(-2, 2), grid(0.6, 0.9), theta=0.5, se=0.1)
    assert gate._lower_iqm(b, 0.975) == pytest.approx(0.5 - q(-2, 2, 0.975) * 0.1)
    assert gate._lower_iqm(arm_boot(grid(-2, 2), grid(0.6, 0.9), theta=0.3, se=0.0), 0.975) == 0.3
    assert gate._lower_iqm(arm_boot(np.full(2000, BIG), grid(0.6, 0.9), theta=0.3, se=0.1), 0.975) < -1e10


def test_holm_ranks_by_composite_p_and_uses_975_then_95():
    # theta = 1, se = 1: the bound is 1 - q_L(t*). A5's t* is lower, so it ranks first.
    b = {'A3': arm_boot(grid(-1.0, 1.02), grid(0.6, 0.9)), 'A5': arm_boot(grid(-1.0, 0.5), grid(0.6, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert first == 'A5' and arms['A5']['level'] == 0.975 and passed
    assert arms['A5']['lower_iqm_gap_closed'] == pytest.approx(1 - q(-1.0, 0.5, 0.975))
    assert arms['A3']['level'] == 0.95 and arms['A3']['tested']
    assert arms['A3']['lower_iqm_gap_closed'] == pytest.approx(1 - q(-1.0, 1.02, 0.95))
    assert arms['A3']['passed'] == (1 - q(-1.0, 1.02, 0.95) > 0)


def test_first_arm_passing_only_at_95_fails_the_gate():
    lo, hi = -1.0, 1.08
    assert 1 - q(lo, hi, 0.975) < 0 < 1 - q(lo, hi, 0.95)
    b = {'A3': arm_boot(grid(lo, hi), grid(0.6, 0.9)), 'A5': arm_boot(grid(2, 3), grid(0.4, 0.45))}
    arms, first, passed = gate._holm_decision(b)
    assert first == 'A3' and not passed
    assert not arms['A5']['tested'] and not arms['A5']['passed']


def test_both_criteria_required():
    b = {'A3': arm_boot(grid(-1, 0.5), grid(0.45, 0.9)), 'A5': arm_boot(grid(-1, 0.5), grid(0.45, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert arms[first]['lower_iqm_gap_closed'] > 0 and arms[first]['lower_probability_of_improvement'] < 0.5
    assert not passed


def test_second_arm_passes_at_95_after_first_passes():
    b = {'A3': arm_boot(grid(-1, 0.5), grid(0.6, 0.9)), 'A5': arm_boot(grid(-1, 0.9), grid(0.6, 0.9))}
    arms, first, passed = gate._holm_decision(b)
    assert passed and first == 'A3'
    assert arms['A5']['level'] == 0.95 and arms['A5']['tested'] and arms['A5']['passed']


def test_ranking_tie_uses_fixed_arm_order():
    same = arm_boot(grid(-1, 0.5), grid(0.7, 0.9))
    arms, first, _ = gate._holm_decision({'A3': same, 'A5': same})
    assert first == 'A3' and arms['A5']['rank'] == 2


def swapped(b):
    return {'A3': b['A5'], 'A5': b['A3']}


def test_label_swap_never_changes_the_verdict_or_pass_set():
    rng = np.random.default_rng(17)
    for _ in range(400):
        b = {}
        for arm in gate.ARMS:
            k = int(rng.choice([0, 50, 100, int(rng.integers(30, 120))]))
            tstar = np.r_[np.full(k, BIG), rng.normal(rng.uniform(-0.5, 1.5), 1, 2000 - k)]
            poi = rng.uniform(0.45, 0.9, 2000)
            b[arm] = arm_boot(rng.permutation(tstar), poi, theta=float(rng.uniform(0.5, 3)),
                              se=float(rng.choice([0.0, 1.0, 0.5])))
        arms, _, passed = gate._holm_decision(b)
        arms_s, _, passed_s = gate._holm_decision(swapped(b))
        assert passed == passed_s
        assert {a for a in gate.ARMS if arms[a]['passed']} == \
            {('A5' if a == 'A3' else 'A3') for a in gate.ARMS if arms_s[a]['passed']}
        assert passed == any(gate._passes(b[a], 0.975) for a in gate.ARMS)


def test_verdict_agrees_with_accepted_holm_two_away_from_the_boundary():
    """Away from the quantile boundaries, the verdict is min(Holm-adjusted composite tail share) <= 0.05."""
    rng = np.random.default_rng(23)
    checked = 0
    for _ in range(300):
        b = {arm: arm_boot(rng.normal(0, 1, 2000), rng.normal(rng.uniform(0.45, 0.75), 0.08, 2000),
                           theta=float(rng.uniform(0.5, 3.5)), se=1.0) for arm in gate.ARMS}
        p = {a: max(gate._tail_iqm(b[a]), float(np.mean(b[a]['poi'] <= 0.5))) for a in gate.ARMS}
        if any(abs(v - t) < 0.003 for v in p.values() for t in (0.025, 0.05)):
            continue
        _, _, passed = gate._holm_decision(b)
        assert passed == (min(holm_two(p['A3'], p['A5']).values()) <= 0.05)
        checked += 1
    assert checked > 200


# --------------------------------------------- test side (V1n) and STOP cases

def risky_node(name='mlgym_r', **kw):
    # Point denominator 0.1/3 > 0, but 11 of the 27 equally likely resample patterns have mean(d) <= 0.
    return node(name, a2=[0.0, 0.0, 0.0], oracle=[-0.9, 1.0, 0.0], a3=[0.1, 0.1, 0.1], a5=[0, 0, 0], **kw)


def noisy_with_risky(**kw):
    t = sim_table(1, 'normal', 2.0)
    t['nodes'].append(risky_node(**kw))
    return t


def test_resampled_nonpositive_denominator_does_not_stop_and_is_counted(confirmed):
    r = gate.evaluate(noisy_with_risky())
    count = r['nodes']['mlgym_r']['resamples_nonpositive_denominator']
    assert 0.3 * 2000 < count < 0.52 * 2000          # about 11/27 of 2000
    for arm in gate.ARMS:
        assert r['arms'][arm]['resamples_with_infinite_tstar'] >= count
    # More than 2.5% of t* are +inf (the 1e12 sentinel), so the IQM bound is far below 0: no arm passes.
    assert r['arms']['A3']['lower_iqm_gap_closed'] < -1e6 and r['verdict'] == 'FAIL'
    assert r['nodes'][T0[0]]['resamples_nonpositive_denominator'] == 0
    # The risky node adds its screened resamples to those of the base table.
    base = gate.evaluate(sim_table(1, 'normal', 2.0))['arms']['A3']['resamples_with_infinite_tstar']
    assert base < r['arms']['A3']['resamples_with_infinite_tstar']


def test_se_zero_ignores_screened_resamples_as_in_the_simulation(confirmed):
    # The simulation's rule: with se_hat(IQM) = 0 the bound is IQM_hat, whatever t* holds. Here the risky node is
    # trimmed (its gap 3 is the largest of 12) and every other node has zero variance, so se_hat = 0.
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5) + [risky_node()]))
    a3 = r['arms']['A3']
    assert a3['se_iqm_gap_closed'] == 0.0 and r['nodes']['mlgym_r']['resamples_nonpositive_denominator'] > 600
    assert a3['lower_iqm_gap_closed'] == a3['iqm_gap_closed'] == 0.5 and r['verdict'] == 'PASS'


def test_risky_denominator_on_excluded_node_has_no_effect(confirmed):
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5) + [risky_node(dev_oracle=[0.0] * 2)]))
    assert r['excluded_from_iqm'] == ['mlgym_r']
    assert 'resamples_nonpositive_denominator' not in r['nodes']['mlgym_r']
    assert r['verdict'] == 'PASS'


def test_nonpositive_point_test_denominator_stops(confirmed):
    bad = node('mlgym_b', a2=[1.0] * 3, oracle=[1.0] * 3, a3=[1.0] * 3, a5=[1.0] * 3)
    with pytest.raises(gate.GateStop, match=r"nonpositive test oracle-A2 denominator on IQM nodes \['mlgym_b'\]"):
        gate.evaluate(layout(t1_nodes(0.5, 0.5) + [bad]))


def test_no_eligible_node_stops_and_names_the_reasons(confirmed):
    noisy = dict(train_a2=[0.0] * 2, train_oracle=[-2.0, 1.0], dev_a2=[0.0] * 2, dev_oracle=[3.0, 6.0])
    t = layout(t1_nodes(0.5, 0.5, **noisy), t0={i: t0_node(i, 0.5, 0.5, **noisy) for i in range(8)})
    with pytest.raises(gate.GateStop, match=r"train \+ dev z >= 3\.0.*IQM is undefined.*'z'"):
        gate.evaluate(t)


# ------------------------------------------------------------- node layout

def test_real_layout_t0_without_suite_plus_three_t1_suites_runs(confirmed):
    t = sim_table(7, t1_per_suite=(2, 2, 2))
    r = gate.evaluate(t)
    assert r['node_counts'] == {'total': 14, 'by_tier': {'T0': 8, 'T1': 6},
                                't1_by_suite': {AR: 2, MLAB: 2, MLGYM: 2}}
    assert r['verdict'] in ('PASS', 'FAIL')
    assert r['protocol']['t0_nodes'] == list(gate.T0_NODES) and r['protocol']['suites'] == list(gate.SUITES)


@pytest.mark.parametrize('suite', [AR, MLAB, MLGYM])
def test_suite_without_t1_node_is_reported_not_a_stop(confirmed, suite):
    t = sim_table(8, t1_per_suite=tuple(0 if s == suite else 2 for s in gate.SUITES))
    r = gate.evaluate(t)
    assert r['t1_suites_without_labelled_node'] == [suite]
    assert r['node_counts']['t1_by_suite'][suite] == 0


def test_t0_only_runs_and_reports_every_suite_missing(confirmed):
    r = gate.evaluate(layout([]))
    assert r['t1_suites_without_labelled_node'] == list(gate.SUITES)
    assert r['node_counts']['by_tier'] == {'T0': 8, 'T1': 0}


def test_full_layout_reports_no_missing_suite(confirmed):
    assert gate.evaluate(layout(t1_nodes(0.5, 0.5)))['t1_suites_without_labelled_node'] == []


# ------------------------------------------------ train + dev z eligibility (V3-A item 2)

def _z(d):
    d = np.asarray(d, dtype=float)
    return d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))


def test_train_dev_z_known_answer_and_threshold_boundary(confirmed):
    """z = mean(d) / (sd(d, ddof=1)/sqrt(n)), d = oracle - A2 over train + dev together; z = 3 is eligible."""
    # d = (-2, 1, 3, 6): z = 1.188 < 3 (ineligible on z only; dev denominator 4.5 >= delta).
    low = constant_node('mlgym_low', 0.3, 0.3, train_a2=[0.0] * 2, train_oracle=[-2.0, 1.0],
                        dev_a2=[0.0] * 2, dev_oracle=[3.0, 6.0])
    # d = (2, 4): mean 3, sd sqrt(2), n 2 -> z exactly 3.
    edge = constant_node('mlgym_edge', 0.3, 0.3, train_a2=[0.0], train_oracle=[2.0], dev_a2=[0.0], dev_oracle=[4.0])
    assert _z([-2, 1, 3, 6]) == pytest.approx(1.1881770515720091)
    assert _z([2.0, 4.0]) == 3.0
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), low, edge]))
    assert r['nodes']['mlgym_low']['train_dev_z'] == pytest.approx(_z([-2, 1, 3, 6]))
    assert r['ineligible_nodes'] == {'mlgym_low': ['z']}
    assert r['nodes']['mlgym_edge']['train_dev_z'] == 3.0 and r['nodes']['mlgym_edge']['included_in_iqm'] is True
    assert r['protocol']['elig_z_min'] == 3.0


def test_z_pools_train_and_dev(confirmed):
    # The dev pair alone, d = (0.5, 2.5), has z < 3; pooled with train it is far above 3.
    node_ = constant_node('mlgym_pool', 0.3, 0.3, train_a2=[0.0] * 4, train_oracle=[1.4, 1.5, 1.5, 1.6],
                          dev_a2=[0.0] * 2, dev_oracle=[0.5, 2.5])
    assert _z([0.5, 2.5]) < 3 < _z([1.4, 1.5, 1.5, 1.6, 0.5, 2.5])
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), node_]))
    assert r['nodes']['mlgym_pool']['included_in_iqm'] is True
    assert r['nodes']['mlgym_pool']['train_dev_z'] == pytest.approx(_z([1.4, 1.5, 1.5, 1.6, 0.5, 2.5]))


def test_z_and_delta_n_are_both_required_and_both_reported(confirmed):
    small = constant_node('mlgym_small', 0.3, 0.3, dev_a2=[0.0] * 2, dev_oracle=[0.0099, 0.0101],
                          train_a2=[0.0] * 2, train_oracle=[0.01, 0.01])
    noisy = constant_node('mlgym_noisy', 0.3, 0.3, train_a2=[0.0] * 2, train_oracle=[-2.0, 1.0],
                          dev_a2=[0.0] * 2, dev_oracle=[3.0, 6.0])
    both = constant_node('mlgym_both', 0.3, 0.3, train_a2=[0.0] * 2, train_oracle=[-0.02, 0.0],
                         dev_a2=[0.0] * 2, dev_oracle=[0.02, 0.04])
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), small, noisy, both]))
    assert r['ineligible_nodes'] == {'mlgym_both': ['delta_n', 'z'], 'mlgym_noisy': ['z'],
                                     'mlgym_small': ['delta_n']}
    for k in ('mlgym_small', 'mlgym_noisy', 'mlgym_both'):
        assert r['nodes'][k]['gap_closed_A3'] is None and r['nodes'][k]['poi_A3'] == 1.0   # kept in PoI


def test_z_sd_zero_follows_the_sign_of_the_mean(confirmed):
    pos = constant_node('mlgym_pos', 0.3, 0.3)          # d = 1 everywhere on train + dev
    zero = constant_node('mlgym_zero', 0.3, 0.3, train_a2=[1.0] * 2, train_oracle=[1.0] * 2,
                         dev_a2=[1.0] * 2, dev_oracle=[1.0] * 2)
    r = gate.evaluate(layout([constant_node('ar1', 0.1, 0.1, suite=AR),
                              constant_node('mlab1', 0.1, 0.1, suite=MLAB), pos, zero]))
    assert r['nodes']['mlgym_pos']['z_sd_zero'] is True and r['nodes']['mlgym_pos']['included_in_iqm'] is True
    assert r['nodes']['mlgym_pos']['train_dev_z'] is None
    assert r['ineligible_nodes'] == {'mlgym_zero': ['delta_n', 'z']}


def test_eligibility_rule_can_spare_a_risky_node(confirmed):
    risky = risky_node(train_a2=[0.0] * 2, train_oracle=[-2.0, 1.0], dev_a2=[0.0] * 2, dev_oracle=[3.0, 6.0])
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5) + [risky]))
    assert r['ineligible_nodes'] == {'mlgym_r': ['z']} and r['verdict'] == 'PASS'


# ------------------------------------------------ test floor (V3-B item 5)

@pytest.mark.parametrize('tier,n,ok', [('T0', 8, False), ('T0', 9, True), ('T1', 2, False), ('T1', 3, True)])
def test_test_floor_per_tier(confirmed, tier, n, ok):
    if tier == 'T0':
        t = layout(t1_nodes(0.5, 0.5), t0={0: t0_node(0, -1.0, 0.0, n=n)})
        name = T0[0]
    else:
        t = layout(t1_nodes(0.5, 0.5) + [constant_node('mlgym_f', -1.0, 0.0, n=n)])
        name = 'mlgym_f'
    r = gate.evaluate(t)
    assert r['nodes'][name]['test_floor'] == gate.TEST_FLOOR[tier]
    assert r['nodes'][name]['included_in_iqm'] is ok
    if not ok:
        assert r['ineligible_nodes'][name] == ['test_floor'] and r['below_test_floor'] == [name]
        assert r['nodes'][name]['poi_A3'] == 0.0          # kept in the PoI and reported
    else:
        assert name not in r['ineligible_nodes'] and r['below_test_floor'] == []


def test_floor_reason_is_listed_with_the_others(confirmed):
    n = constant_node('mlgym_all', 0.3, 0.3, n=2, train_a2=[0.0] * 2, train_oracle=[-2.0, 1.0],
                      dev_a2=[0.0] * 2, dev_oracle=[0.0, 0.0])
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5) + [n]))
    assert r['ineligible_nodes'] == {'mlgym_all': ['delta_n', 'z', 'test_floor']}


# ---------------------------------------------------- split (V3-A item 3)

def test_split_must_be_declared_as_p3(confirmed):
    for bad in (None, {'name': 'P2', 'train': '1/2', 'dev': '1/6', 'test': '1/3'},
                {'name': 'P3', 'train': '1/3', 'dev': '1/6'}, 'P3'):
        t = layout(t1_nodes(0.5, 0.5))
        if bad is None:
            del t['split']
        else:
            t['split'] = bad
        with pytest.raises(gate.GateStop, match='declared split must be exactly'):
            gate.evaluate(t)


def test_train_dev_test_ids_must_be_disjoint(confirmed):
    t = layout(t1_nodes(0.5, 0.5))
    t['nodes'][-1]['dev']['instance_ids'][0] = t['nodes'][-1]['test']['instance_ids'][0]
    with pytest.raises(ValueError, match='must be disjoint'):
        gate.evaluate(t)


def test_counts_and_design_size_are_reported_not_enforced(confirmed):
    r = gate.evaluate(layout(t1_nodes(0.5, 0.5)))
    # constant nodes: 4 train + 2 dev + 9 test = 15 instances, against 18 (T0) and 12 (T1)
    row = r['nodes'][T0[0]]
    assert (row['n_train'], row['n_dev'], row['n_test'], row['n_total']) == (4, 2, 9, 15)
    assert r['off_design_size'][T0[0]] == {'n_total': 15, 'design': 18}
    assert r['off_design_size']['mlgym_t1'] == {'n_total': 15, 'design': 12}
    sim = gate.evaluate(sim_table(12))
    assert sim['off_design_size'] == {} and sim['off_split'] == {}
    assert r['off_split'] == {}                       # off-size nodes are listed under off_design_size only
    assert r['protocol']['split'] == gate.SPLIT and r['protocol']['design_instances'] == {'T0': 18, 'T1': 12}
    assert gate.DESIGN_SPLIT == {'T0': (6, 3, 9), 'T1': (4, 2, 6)}


def test_a_p2_split_labelled_p3_is_reported_as_off_split(confirmed):
    t = sim_table(12)
    tt = next(n for n in t['nodes'] if n['tier'] == 'T1')
    # move two test instances (6 -> 4) to train (4 -> 6): the P2 counts 6 : 2 : 4 at the design size 12
    for k in ('instance_ids', 'A2', 'oracle'):
        tt['train'][k] = tt['train'][k] + tt['test'][k][:2]
    for k in ('instance_ids', *gate.SERIES):
        tt['test'][k] = tt['test'][k][2:]
    r = gate.evaluate(t)
    assert r['off_split'] == {tt['node']: {'counts': [6, 2, 4], 'p3': [4, 2, 6]}}
    assert r['off_design_size'] == {}


# ------------------------------------------------------- layout STOPs

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
    (('schema',), 'r1_d8_gate_input/v2'),
    (('schema',), 'r1_d8_gate_input/v3'),
    (('t0_nodes',), 'digits_mlp'),
    (('t0_nodes',), [T0[0], T0[0]]),
    (('t0_nodes',), [1]),
    (('nodes', 0, 'node'), T0[1]),
    (('nodes', 0, 'tier'), 'T2'),
    (('nodes', 0, 'suite'), ''),
    (('nodes', 0, 'suite'), 3),
    (('nodes', 0, 'test', 'A3'), [1e308] * 9),
    (('nodes', 0, 'dev', 'oracle'), [1e308] * 2),
    (('nodes', 0, 'train', 'oracle'), [1e308] * 4),
    (('nodes', 0, 'delta_n'), 0.0),
    (('nodes', 0, 'delta_n'), True),
    (('nodes', 0, 'test', 'A3'), [0.5] * 4),
    (('nodes', 0, 'test', 'A3'), [True] * 9),
    (('nodes', 0, 'test', 'A2'), [float('nan')] * 9),
    (('nodes', 0, 'test', 'oracle'), [float('inf')] * 9),
    (('nodes', 0, 'test', 'instance_ids'), ['x'] * 9),
    (('nodes', 0, 'dev', 'A2'), []),
    (('nodes', 0, 'dev', 'A2'), [0.0] * 3),
    (('nodes', 0, 'dev', 'instance_ids'), ['d0', ' d1']),
    (('nodes', 0, 'train', 'A3'), [0.0] * 4),
    (('nodes', 0, 'train'), {'A2': [0.0], 'oracle': [1.0]}),
    (('nodes', 0, 'extra'), 1),
    (('extra',), 1),
])
def test_malformed_inputs_refused(confirmed, path, value):
    with pytest.raises(ValueError):
        gate.evaluate(mutate(path, value))


def test_missing_train_or_suite_field_refused(confirmed):
    for field in ('suite', 'train'):
        t = layout(t1_nodes(0.5, 0.5))
        del t['nodes'][0][field]
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
    assert gate.NUMPY_VERSION == '2.4.4' and gate.ELIG_Z_MIN == 3.0 and gate.GATE_VERSION == '3.1'
    assert gate.TEST_FLOOR == {'T0': 9, 'T1': 3}
    assert gate.SPLIT == {'name': 'P3', 'train': '1/3', 'dev': '1/6', 'test': '1/2'}
    assert gate.DESIGN_INSTANCES == {'T0': 18, 'T1': 12}
    assert gate.INPUT_SCHEMA == 'r1_d8_gate_input/v3.1' and gate.OUTPUT_SCHEMA == 'r1_d8_gate_result/v3.1'
    assert gate.ENVIRONMENT == 'harness uv.lock environment at a3fedbb (Python 3.13, NumPy 2.4.4)'
    assert not hasattr(gate, 'DEV_Z_MIN')
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
