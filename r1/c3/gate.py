"""R1-BX-D8 aggregate C3 gate (M11): statistic on already computed utilities.

Synthetic-tested implementation candidate; AI-assisted. It is not an author
decision and it opens nothing before the D8 confirmation check passes.

What it computes (PLAN R1-BX-D8 and R1-BX-PROPOSED-CONFIRM (D8)):

* per node, gap closed = (mean U_arm - mean U_A2) / (mean U_oracle - mean U_A2)
  on the node's test instances, where U_oracle is the noisy-oracle ceiling;
* nodes whose dev-split denominator mean U_oracle - mean U_A2 is below
  ``delta_n`` are excluded from the IQM, listed, and kept in the probability
  of improvement (PoI);
* IQM of gap closed across the eligible nodes: the 25%-75% empirical trimmed
  mean with fractional boundary weights (``d8_point_statistics.node_iqm``);
* PoI: per node the share of test instances with U_arm > U_A2, ties one half,
  then the plain mean over all nodes;
* node-stratified bootstrap: 2,000 resamples of test instances within each
  node, one shared index draw per node and resample for A2, oracle, A3 and A5;
* decision: Holm over A3 and A5 at family-wise one-sided alpha = 0.05; the
  first-ranked arm is tested with one-sided 97.5% lower bounds, the second
  (only if the first passes) with 95%. An arm passes if the IQM lower bound is
  > 0 and the PoI lower bound is > 0.5 (both strict). The gate passes if the
  first-ranked arm passes. The point IQM is reported against 0.1.

Implementation conventions that the PLAN rows do not fix (preregistration
candidates; see docs/r1/reports/M11_D8_GATE_20261109.md):

* seed 20261108, ``numpy.random.Generator(PCG64)``; nodes in sorted node-id
  order, instances in sorted instance-id order; for each node in that order
  one ``integers(0, n, size=(2000, n))`` draw;
* lower bound at level L = ``numpy.quantile(boot, 1 - L, method='linear')``;
* arm ranking: ascending composite percentile p-value
  max(P*(IQM <= 0), P*(PoI <= 0.5)), ties in the fixed order A3, A5; used only
  to order the two arms, never as the pass criterion;
* a resampled test denominator <= 0 on an IQM-eligible node, a nonpositive
  point test denominator on such a node, or no eligible node is a STOP: no
  resample or node is dropped;
* T0 and T1 are pooled with tier as a stratum: every node lies in one tier and
  resampling is within node; per-tier node counts and descriptive point
  statistics are reported. Partial T1 (R1-B7-PARTIAL-T1): each expected suite
  needs at least one T1 node, otherwise STOP.

Inputs are the caller's responsibility: U is the one-step utility scaled to a
20-run campaign, the oracle utility comes from the label-seed block only, test
utilities from the evaluation block, and the dev arrays from the dev split.
This module does not compute or verify those provenance properties.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

from r1.c3 import analysis_guard
from r1.c3.d8_point_statistics import node_iqm, node_equal_probability_of_improvement

CONFIRM_ID = 'R1-BX-D8-CONFIRM'
INPUT_SCHEMA = 'r1_d8_gate_input/v1'
OUTPUT_SCHEMA = 'r1_d8_gate_result/v1'
N_RESAMPLES = 2000
SEED = 20261108
RNG = 'numpy.random.Generator(PCG64)'
QUANTILE_METHOD = 'linear'
FAMILY_ALPHA = 0.05
LEVELS = (0.975, 0.95)          # Holm: first-ranked arm, second-ranked arm
PRACTICAL_SIZE = 0.1
POI_NULL = 0.5
ARMS = ('A3', 'A5')             # fixed order; also the tie-break for ranking
TIERS = ('T0', 'T1')
SERIES = ('A2', 'oracle', 'A3', 'A5')


class GateStop(RuntimeError):
    """A predeclared STOP: the gate is not read and nothing is dropped."""


def gate_file_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# ----------------------------------------------------------------- validation

def _finite_vector(values, label):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f'{label} must be a nonempty list')
    for v in values:
        if type(v) not in (int, float):
            raise ValueError(f'{label} contains a non-numeric value')
        try:
            ok = math.isfinite(v)
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f'{label} contains a non-finite value')
    return np.asarray(values, dtype=float)


def _text(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'{label} must be a nonempty string without outer spaces')
    return value


def _validate(gate_input):
    if not isinstance(gate_input, dict) or gate_input.get('schema') != INPUT_SCHEMA:
        raise ValueError(f'gate input must be a dict with schema {INPUT_SCHEMA}')
    extra = set(gate_input) - {'schema', 'expected_suites', 'nodes'}
    if extra:
        raise ValueError(f'unknown gate input fields: {sorted(extra)}')
    suites = gate_input.get('expected_suites')
    if not isinstance(suites, list) or not suites:
        raise ValueError('expected_suites must be a nonempty list')
    suites = [_text(s, 'suite') for s in suites]
    if len(set(suites)) != len(suites):
        raise ValueError('expected_suites contains duplicates')
    raw_nodes = gate_input.get('nodes')
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError('nodes must be a nonempty list')
    nodes = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise ValueError('each node must be a dict')
        extra = set(raw) - {'node', 'suite', 'tier', 'delta_n', 'dev', 'test'}
        if extra:
            raise ValueError(f'unknown node fields: {sorted(extra)}')
        name = _text(raw.get('node'), 'node id')
        if name in nodes:
            raise ValueError(f'duplicate node id {name}')
        suite = _text(raw.get('suite'), 'suite')
        if suite not in suites:
            raise ValueError(f'node {name} has a suite outside expected_suites')
        tier = raw.get('tier')
        if tier not in TIERS:
            raise ValueError(f'node {name} tier must be one of {TIERS}')
        delta = raw.get('delta_n')
        if type(delta) not in (int, float) or not math.isfinite(delta) or delta <= 0:
            raise ValueError(f'node {name} delta_n must be a positive finite number')
        dev = raw.get('dev')
        if not isinstance(dev, dict) or set(dev) != {'A2', 'oracle'}:
            raise ValueError(f'node {name} dev must have exactly A2 and oracle')
        dev_a2 = _finite_vector(dev['A2'], f'{name} dev A2')
        dev_or = _finite_vector(dev['oracle'], f'{name} dev oracle')
        if len(dev_a2) != len(dev_or):
            raise ValueError(f'node {name} dev vectors differ in length')
        test = raw.get('test')
        if not isinstance(test, dict) or set(test) != {'instance_ids', *SERIES}:
            raise ValueError(f'node {name} test must have instance_ids, A2, oracle, A3, A5')
        ids = test['instance_ids']
        if not isinstance(ids, list) or not ids:
            raise ValueError(f'node {name} instance_ids must be a nonempty list')
        ids = [_text(i, 'instance id') for i in ids]
        if len(set(ids)) != len(ids):
            raise ValueError(f'node {name} has duplicate instance ids')
        series = {k: _finite_vector(test[k], f'{name} test {k}') for k in SERIES}
        if any(len(v) != len(ids) for v in series.values()):
            raise ValueError(f'node {name} test vectors are not paired with instance_ids')
        order = sorted(range(len(ids)), key=ids.__getitem__)
        nodes[name] = {
            'suite': suite, 'tier': tier, 'delta_n': float(delta),
            'dev_denominator': float(dev_or.mean() - dev_a2.mean()),
            'n_test': len(ids), 'n_dev': len(dev_a2),
            'test': {k: v[order] for k, v in series.items()},
        }
    no_t1 = [s for s in suites if not any(n['suite'] == s and n['tier'] == 'T1' for n in nodes.values())]
    if no_t1:
        raise GateStop(f'STOP: suites without a labelled T1 node: {no_t1} (R1-B7-PARTIAL-T1)')
    return suites, dict(sorted(nodes.items()))


# ---------------------------------------------------------------- statistics

def _wins(arm, a2):
    return (arm > a2).astype(float) + 0.5 * (arm == a2)


def _point(nodes):
    eligible = [k for k, n in nodes.items() if n['dev_denominator'] >= n['delta_n']]
    if not eligible:
        raise GateStop('STOP: no node has a dev denominator at or above delta_n; the IQM is undefined')
    table = {}
    for name, n in nodes.items():
        t = n['test']
        denom = float(t['oracle'].mean() - t['A2'].mean())
        row = {'suite': n['suite'], 'tier': n['tier'], 'n_test': n['n_test'], 'n_dev': n['n_dev'],
               'delta_n': n['delta_n'], 'dev_denominator': n['dev_denominator'],
               'included_in_iqm': name in eligible, 'test_denominator': denom}
        if name in eligible and not denom > 0:
            raise GateStop(f'STOP: nonpositive test oracle-A2 denominator on IQM node {name}')
        for arm in ARMS:
            row[f'gap_closed_{arm}'] = (float(t[arm].mean() - t['A2'].mean()) / denom
                                        if name in eligible else None)
            row[f'poi_{arm}'] = float(_wins(t[arm], t['A2']).mean())
        table[name] = row
    summary = {}
    for arm in ARMS:
        summary[arm] = {
            'iqm_gap_closed': node_iqm([table[k][f'gap_closed_{arm}'] for k in eligible]),
            'probability_of_improvement': node_equal_probability_of_improvement(
                [(nodes[k]['test'][arm].tolist(), nodes[k]['test']['A2'].tolist()) for k in nodes]),
        }
    return eligible, table, summary


def _bootstrap(nodes, eligible):
    """Return {arm: (iqm[B], poi[B])} from shared within-node index draws."""
    rng = np.random.Generator(np.random.PCG64(SEED))
    gaps = {arm: [] for arm in ARMS}
    poi = {arm: np.zeros(N_RESAMPLES) for arm in ARMS}
    for name, n in nodes.items():          # sorted node-id order
        t = n['test']; size = n['n_test']
        idx = rng.integers(0, size, size=(N_RESAMPLES, size))
        a2 = t['A2'][idx].mean(axis=1)
        for arm in ARMS:
            poi[arm] += _wins(t[arm], t['A2'])[idx].mean(axis=1)
        if name in eligible:
            denom = t['oracle'][idx].mean(axis=1) - a2
            bad = int(np.count_nonzero(~(denom > 0)))
            if bad:
                raise GateStop(f'STOP: {bad} of {N_RESAMPLES} resampled oracle-A2 denominators '
                               f'are nonpositive on IQM node {name}; no resample is dropped')
            for arm in ARMS:
                gaps[arm].append((t[arm][idx].mean(axis=1) - a2) / denom)
    out = {}
    for arm in ARMS:
        matrix = np.stack(gaps[arm], axis=1)           # (B, eligible nodes)
        iqm = np.array([node_iqm(row) for row in matrix.tolist()])
        out[arm] = (iqm, poi[arm] / len(nodes))
    return out


def _lower(boot, level):
    return float(np.quantile(boot, 1.0 - level, method=QUANTILE_METHOD))


def _holm_decision(boot):
    """Holm step-down over the two arms with the PLAN's lower-bound criterion.

    ``boot`` maps each arm to (bootstrap IQM array, bootstrap PoI array).
    """
    ranking = []
    for arm in ARMS:
        iqm, poi = boot[arm]
        p_iqm = float(np.mean(iqm <= 0.0)); p_poi = float(np.mean(poi <= POI_NULL))
        ranking.append((max(p_iqm, p_poi), ARMS.index(arm), arm, p_iqm, p_poi))
    ranking.sort()
    arms = {}
    still_testing = True
    for rank, (p_comp, _, arm, p_iqm, p_poi) in enumerate(ranking):
        level = LEVELS[rank]
        iqm, poi = boot[arm]
        lb_iqm, lb_poi = _lower(iqm, level), _lower(poi, level)
        if still_testing:
            passed = lb_iqm > 0.0 and lb_poi > POI_NULL
            tested = True
        else:
            passed, tested = False, False
        arms[arm] = {'rank': rank + 1, 'level': level, 'tested': tested, 'passed': passed,
                     'lower_iqm_gap_closed': lb_iqm, 'lower_probability_of_improvement': lb_poi,
                     'ranking_p_iqm': p_iqm, 'ranking_p_poi': p_poi, 'ranking_p_composite': p_comp}
        still_testing = still_testing and passed
    first = ranking[0][2]
    return arms, first, arms[first]['passed']


def _tier_descriptive(nodes, table, eligible):
    out = {}
    for tier in TIERS:
        names = [k for k in nodes if nodes[k]['tier'] == tier]
        elig = [k for k in names if k in eligible]
        row = {'n_nodes': len(names), 'n_iqm_nodes': len(elig)}
        for arm in ARMS:
            row[f'iqm_gap_closed_{arm}'] = (node_iqm([table[k][f'gap_closed_{arm}'] for k in elig])
                                            if elig else None)
            row[f'poi_{arm}'] = (float(np.mean([table[k][f'poi_{arm}'] for k in names]))
                                 if names else None)
        out[tier] = row
    return out


def _evaluate(gate_input):
    suites, nodes = _validate(gate_input)
    eligible, table, summary = _point(nodes)
    boot = _bootstrap(nodes, eligible)
    arms, first, passed = _holm_decision(boot)
    for arm in ARMS:
        arms[arm].update(summary[arm])
        arms[arm]['meets_practical_size'] = summary[arm]['iqm_gap_closed'] >= PRACTICAL_SIZE
    return {
        'schema': OUTPUT_SCHEMA,
        'verdict': 'PASS' if passed else 'FAIL',
        'first_ranked_arm': first,
        'arms': arms,
        'nodes': table,
        'excluded_from_iqm': [k for k in nodes if k not in eligible],
        'node_counts': {'total': len(nodes),
                        'by_tier': {t: sum(n['tier'] == t for n in nodes.values()) for t in TIERS},
                        'by_suite_and_tier': {s: {t: sum(n['suite'] == s and n['tier'] == t
                                                         for n in nodes.values()) for t in TIERS}
                                              for s in suites}},
        'tier_descriptive': _tier_descriptive(nodes, table, eligible),
        'protocol': {'resamples': N_RESAMPLES, 'seed': SEED, 'rng': RNG,
                     'numpy_version': np.__version__, 'quantile_method': QUANTILE_METHOD,
                     'family_alpha': FAMILY_ALPHA, 'levels': list(LEVELS),
                     'practical_size': PRACTICAL_SIZE, 'arms': list(ARMS),
                     'gate_sha256': gate_file_sha256()},
    }


# --------------------------------------------------------------- entry points

def evaluate(gate_input):
    """Run the gate on an in-memory input after the D8 confirmation check."""
    analysis_guard.require_d8_confirmation()
    return _evaluate(gate_input)


def load_and_evaluate(path):
    """Check D8 confirmation and sealed paths before opening the input file."""
    analysis_guard.require_d8_confirmation()
    analysis_guard.refuse_sealed(path)
    with open(path, encoding='utf-8') as handle:
        gate_input = json.load(handle)
    return _evaluate(gate_input)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print('usage: python -m r1.c3.gate GATE_INPUT.json', file=sys.stderr)
        return 2
    print(json.dumps(load_and_evaluate(argv[0]), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
