"""R1-BX-D8 aggregate C3 gate (M11): statistic on already computed utilities.

Synthetic-tested implementation candidate; AI-assisted. It is not an author
decision and it opens nothing before the D8 confirmation check passes.

What it computes (PLAN R1-BX-D8 and R1-BX-PROPOSED-CONFIRM (D8)):

* per node, gap closed = (mean U_arm - mean U_A2) / (mean U_oracle - mean U_A2)
  on the node's test instances, where U_oracle is the noisy-oracle ceiling
  (ratio of means: a convention, the row writes the ratio without "mean");
* nodes whose dev-split denominator mean U_oracle - mean U_A2 is below
  ``delta_n`` are excluded from the IQM, listed, and kept in the probability
  of improvement (PoI);
* IQM of gap closed across the eligible nodes: the 25%-75% empirical trimmed
  mean with fractional boundary weights (``_node_iqm``, inlined here so that
  the gate SHA binds it; identical to the accepted
  ``d8_point_statistics.node_iqm``);
* PoI: per node the share of test instances with U_arm > U_A2, ties (exact
  floating-point equality) one half, then the plain mean over all nodes;
* node-stratified bootstrap: 2,000 resamples of test instances within each
  node, one shared index draw per node and resample for A2, oracle, A3 and A5;
  nodes are fixed, so the bounds cover instance noise for these nodes only;
* decision: Holm over A3 and A5 at family-wise one-sided alpha = 0.05; the
  first-ranked arm is tested with one-sided 97.5% lower bounds, the second
  (only if the first passes) with 95%. An arm passes if the IQM lower bound is
  > 0 and the PoI lower bound is > 0.5 (both strict). The gate passes if the
  first-ranked arm passes. The point IQM is reported against 0.1.

Node layout (pinned here, so the gate SHA binds it):

* tier T0 is exactly the eight CPU nodes of ``T0_NODES``: the authorized
  sweep-1 node set (R1-DT-PIN-SWEEP1; docs/r1/authorizations/c3_sweep1_20261027.md),
  in which openml_climate substitutes for openml_blood_transfusion, which failed
  D21 (R1-D28-REPAIR; DT_SWEEP1_READINESS_20261027.md). Sweep 2 runs on the same
  instances (RUNBOOK B.1b). T0 nodes belong to no suite (``"suite": null``). A
  missing, extra or renamed T0 node is a STOP;
* tier T1 nodes carry a suite from ``SUITES`` (R1-BX-D2 as amended by
  R1-1GC-FALLBACK). A T1 node without a suite or with another suite is a STOP.
  The T1 node list itself cannot be pinned (partial T1, R1-B7-PARTIAL-T1);
* partial T1: each suite in ``SUITES`` needs at least one labelled T1 node,
  otherwise the whole gate STOPs. The R1-B7-PARTIAL-T1 consequence ties this
  condition to leave-one-suite-out; the CONFIRM row text the parser requires
  states it without that qualifier. The whole-gate STOP is the conservative
  reading (a preregistration candidate).

Implementation conventions that the PLAN rows do not fix (preregistration
candidates; see docs/r1/reports/M11_D8_GATE_20261109.md):

* seed 20261108, ``numpy.random.Generator(PCG64)``; NumPy must be exactly
  ``NUMPY_VERSION`` (STOP otherwise); nodes in sorted node-id order, instances
  in sorted instance-id order; for each node in that order one
  ``integers(0, n, size=(2000, n))`` draw;
* lower bound at level L = ``numpy.quantile(boot, 1 - L, method='linear')``;
* arm ranking for Holm: an arm that passes at the first level (97.5%) ranks
  before one that does not; then ascending composite percentile p-value
  max(P*(IQM <= 0), P*(PoI <= 0.5)); then the fixed order A3, A5. The first key
  is the pass test itself, so the verdict does not depend on arm labels;
* a resampled test denominator <= 0 on an IQM-eligible node, a nonpositive
  point test denominator on such a node, or no eligible node is a STOP: no
  resample or node is dropped; every offending node is listed;
* T0 and T1 are pooled with tier as a stratum: every node lies in one tier and
  resampling is within node; per-tier node counts and descriptive point
  statistics are reported.

Inputs are the caller's responsibility: U is the one-step utility scaled to a
20-run campaign; ``delta_n`` is the node's D18 delta_n in the same 20-run-scaled
utility units as U (D18: "also the unit of the C3 gate, scaled to a 20-run
campaign"); the oracle utility comes from the label-seed block only, test
utilities from the evaluation block, and the dev arrays from the dev split.
This module does not compute or verify those provenance properties or units.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

from r1.c3 import analysis_guard

CONFIRM_ID = 'R1-BX-D8-CONFIRM'
INPUT_SCHEMA = 'r1_d8_gate_input/v2'
OUTPUT_SCHEMA = 'r1_d8_gate_result/v2'
NUMPY_VERSION = '2.4.4'         # harness uv.lock pin; STOP on any other version
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
# Tier T0: the 8 CPU nodes of the authorized sweep 1 (R1-DT-PIN-SWEEP1, 27 Oct;
# docs/r1/authorizations/c3_sweep1_20261027.md; R1-BX-D2 "the 8 CPU nodes stay as
# tier T0"). openml_climate substitutes for openml_blood_transfusion (failed D21;
# R1-D28-REPAIR). Same set as the evidence classifier and the deepthought config.
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval',
            'openml_ionosphere', 'openml_sonar', 'openml_wdbc', 'tabular_mlp')
# T1 suites: R1-BX-D2 as amended by R1-1GC-FALLBACK (MLAgentBench replaces 1GC-7RC).
SUITES = ('autoresearch', 'MLAgentBench', 'MLGym')


class GateStop(RuntimeError):
    """A predeclared STOP: the gate is not read and nothing is dropped."""


def gate_file_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _require_pins():
    """STOP unless this file is the gate the D8 check bound and NumPy is pinned."""
    bound = Path(analysis_guard.REPO) / 'r1/c3/gate.py'
    here = Path(__file__)
    try:
        same = here.resolve() == bound.resolve() and here.read_bytes() == bound.read_bytes()
    except OSError:
        same = False
    if not same:
        raise GateStop('STOP: the executing gate file is not r1/c3/gate.py of the checked repository')
    if np.__version__ != NUMPY_VERSION:
        raise GateStop(f'STOP: NumPy {np.__version__} is not the pinned NumPy {NUMPY_VERSION}')


# ------------------------------------------- point statistics (inlined, bound)

def _node_iqm(gap_closed):
    """25%-trimmed mean with fractional weights at empirical quantile edges.

    Same arithmetic as the accepted ``d8_point_statistics.node_iqm``; inlined
    so that the confirmed gate SHA covers it.
    """
    values = sorted(_finite_list(gap_closed, 'node gap closed'))
    n = len(values)
    # Work in quarter-observation units to avoid floating cut-point rounding.
    lower, upper = n, 3 * n
    total = 0.0
    for i, value in enumerate(values):
        weight = max(0, min(4 * (i + 1), upper) - max(4 * i, lower))
        total += value * weight
    result = total / (2 * n)
    if not math.isfinite(result):
        raise ValueError('IQM overflow')
    return result


def _node_poi(nodes):
    """Average node-level win rates; ties count one half, nodes equally.

    Same arithmetic as the accepted
    ``d8_point_statistics.node_equal_probability_of_improvement``; inlined.
    """
    if not isinstance(nodes, (list, tuple)) or not nodes:
        raise ValueError('nodes must be a nonempty sequence')
    node_rates = []
    for pair in nodes:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError('each node needs arm and baseline values')
        arm = _finite_list(pair[0], 'arm utility')
        baseline = _finite_list(pair[1], 'baseline utility')
        if len(arm) != len(baseline):
            raise ValueError('paired node observations differ in length')
        score = sum(1.0 if a > b else 0.5 if a == b else 0.0
                    for a, b in zip(arm, baseline))
        node_rates.append(score / len(arm))
    return sum(node_rates) / len(node_rates)


# ----------------------------------------------------------------- validation

def _finite_list(values, label):
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
    return list(values)


def _finite_vector(values, label):
    array = np.asarray(_finite_list(values, label), dtype=float)
    # Bound every resampled sum and every difference of two means: 4 n max|v|
    # finite means no mean, resampled mean or mean difference can overflow.
    if not math.isfinite(4.0 * len(array) * float(np.max(np.abs(array)))):
        raise ValueError(f'{label} is too large in magnitude for finite means')
    return array


def _text(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'{label} must be a nonempty string without outer spaces')
    return value


def _validate(gate_input):
    if not isinstance(gate_input, dict) or gate_input.get('schema') != INPUT_SCHEMA:
        raise ValueError(f'gate input must be a dict with schema {INPUT_SCHEMA}')
    extra = set(gate_input) - {'schema', 'nodes'}
    if extra:
        raise ValueError(f'unknown gate input fields: {sorted(extra)}')
    raw_nodes = gate_input.get('nodes')
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError('nodes must be a nonempty list')
    nodes = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise ValueError('each node must be a dict')
        if set(raw) != {'node', 'suite', 'tier', 'delta_n', 'dev', 'test'}:
            raise ValueError(f'node fields must be exactly node, suite, tier, delta_n, dev, test; '
                             f'got {sorted(raw)}')
        name = _text(raw.get('node'), 'node id')
        if name in nodes:
            raise ValueError(f'duplicate node id {name}')
        suite = raw.get('suite')
        if suite is not None:
            suite = _text(suite, 'suite')
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
        dev_denominator = float(dev_or.mean() - dev_a2.mean())
        if not math.isfinite(dev_denominator):
            raise ValueError(f'node {name} dev denominator is not finite')
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
            'dev_denominator': dev_denominator,
            'n_test': len(ids), 'n_dev': len(dev_a2),
            'test': {k: v[order] for k, v in series.items()},
        }
    _check_layout(nodes)
    return dict(sorted(nodes.items()))


def _check_layout(nodes):
    """STOP unless the node set matches the pinned layout (nothing dropped silently)."""
    t0 = sorted(k for k, n in nodes.items() if n['tier'] == 'T0')
    if t0 != sorted(T0_NODES):
        raise GateStop(f'STOP: T0 nodes must be exactly {sorted(T0_NODES)}; missing '
                       f'{sorted(set(T0_NODES) - set(t0))}, unexpected {sorted(set(t0) - set(T0_NODES))}')
    t0_with_suite = sorted(k for k in t0 if nodes[k]['suite'] is not None)
    if t0_with_suite:
        raise GateStop(f'STOP: T0 nodes belong to no suite; suite given for {t0_with_suite}')
    t1 = [k for k, n in nodes.items() if n['tier'] == 'T1']
    bad = sorted(k for k in t1 if nodes[k]['suite'] not in SUITES)
    if bad:
        raise GateStop(f'STOP: T1 nodes without a suite in {list(SUITES)}: {bad}')
    no_t1 = [s for s in SUITES if not any(nodes[k]['suite'] == s for k in t1)]
    if no_t1:
        raise GateStop(f'STOP: suites without a labelled T1 node: {no_t1} (R1-B7-PARTIAL-T1)')


# ---------------------------------------------------------------- statistics

def _wins(arm, a2):
    return (arm > a2).astype(float) + 0.5 * (arm == a2)


def _point(nodes):
    eligible = [k for k, n in nodes.items() if n['dev_denominator'] >= n['delta_n']]
    if not eligible:
        raise GateStop('STOP: no node has a dev denominator at or above delta_n; the IQM is undefined')
    table = {}
    nonpositive = []
    for name, n in nodes.items():
        t = n['test']
        denom = float(t['oracle'].mean() - t['A2'].mean())
        row = {'suite': n['suite'], 'tier': n['tier'], 'n_test': n['n_test'], 'n_dev': n['n_dev'],
               'delta_n': n['delta_n'], 'dev_denominator': n['dev_denominator'],
               'included_in_iqm': name in eligible, 'test_denominator': denom}
        if name in eligible and not denom > 0:
            nonpositive.append(name)
            continue
        for arm in ARMS:
            row[f'gap_closed_{arm}'] = (float(t[arm].mean() - t['A2'].mean()) / denom
                                        if name in eligible else None)
            row[f'poi_{arm}'] = float(_wins(t[arm], t['A2']).mean())
        table[name] = row
    if nonpositive:
        raise GateStop(f'STOP: nonpositive test oracle-A2 denominator on IQM nodes {nonpositive}')
    summary = {}
    for arm in ARMS:
        summary[arm] = {
            'iqm_gap_closed': _node_iqm([table[k][f'gap_closed_{arm}'] for k in eligible]),
            'probability_of_improvement': _node_poi(
                [(nodes[k]['test'][arm].tolist(), nodes[k]['test']['A2'].tolist()) for k in nodes]),
        }
    return eligible, table, summary


def _bootstrap(nodes, eligible):
    """Return {arm: (iqm[B], poi[B])} from shared within-node index draws."""
    rng = np.random.Generator(np.random.PCG64(SEED))
    gaps = {arm: [] for arm in ARMS}
    poi = {arm: np.zeros(N_RESAMPLES) for arm in ARMS}
    nonpositive = {}
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
                nonpositive[name] = bad
                continue
            for arm in ARMS:
                gaps[arm].append((t[arm][idx].mean(axis=1) - a2) / denom)
    if nonpositive:
        raise GateStop(f'STOP: nonpositive resampled oracle-A2 denominators (of {N_RESAMPLES}) on IQM '
                       f'nodes {nonpositive}; no resample or node is dropped')
    out = {}
    for arm in ARMS:
        matrix = np.stack(gaps[arm], axis=1)           # (B, eligible nodes)
        iqm = np.array([_node_iqm(row) for row in matrix.tolist()])
        out[arm] = (iqm, poi[arm] / len(nodes))
    return out


def _lower(boot, level):
    return float(np.quantile(boot, 1.0 - level, method=QUANTILE_METHOD))


def _passes(boot_arm, level):
    """The PLAN's pass test for one arm at one level (both bounds, strict)."""
    iqm, poi = boot_arm
    return _lower(iqm, level) > 0.0 and _lower(poi, level) > POI_NULL


def _holm_decision(boot):
    """Holm step-down over the two arms with the PLAN's lower-bound criterion.

    ``boot`` maps each arm to (bootstrap IQM array, bootstrap PoI array). The
    ranking key starts with the first-level pass test itself, so an arm that
    passes at 97.5% always ranks first: the verdict is "some arm passes at
    97.5%" and cannot depend on arm labels. The composite tail share and the
    fixed order only order arms that agree on that test.
    """
    ranking = []
    for arm in ARMS:
        iqm, poi = boot[arm]
        p_iqm = float(np.mean(iqm <= 0.0)); p_poi = float(np.mean(poi <= POI_NULL))
        first_level_pass = _passes(boot[arm], LEVELS[0])
        ranking.append((not first_level_pass, max(p_iqm, p_poi), ARMS.index(arm), arm, p_iqm, p_poi))
    ranking.sort()
    arms = {}
    still_testing = True
    for rank, (_, p_comp, _, arm, p_iqm, p_poi) in enumerate(ranking):
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
    first = ranking[0][3]
    return arms, first, arms[first]['passed']


def _tier_descriptive(nodes, table, eligible):
    out = {}
    for tier in TIERS:
        names = [k for k in nodes if nodes[k]['tier'] == tier]
        elig = [k for k in names if k in eligible]
        row = {'n_nodes': len(names), 'n_iqm_nodes': len(elig)}
        for arm in ARMS:
            row[f'iqm_gap_closed_{arm}'] = (_node_iqm([table[k][f'gap_closed_{arm}'] for k in elig])
                                            if elig else None)
            row[f'poi_{arm}'] = (float(np.mean([table[k][f'poi_{arm}'] for k in names]))
                                 if names else None)
        out[tier] = row
    return out


def _evaluate(gate_input):
    _require_pins()
    nodes = _validate(gate_input)
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
                        't1_by_suite': {s: sum(n['tier'] == 'T1' and n['suite'] == s
                                               for n in nodes.values()) for s in SUITES}},
        'tier_descriptive': _tier_descriptive(nodes, table, eligible),
        'protocol': {'resamples': N_RESAMPLES, 'seed': SEED, 'rng': RNG,
                     'numpy_version': np.__version__, 'numpy_pin': NUMPY_VERSION,
                     'quantile_method': QUANTILE_METHOD,
                     't0_nodes': list(T0_NODES), 'suites': list(SUITES),
                     'family_alpha': FAMILY_ALPHA, 'levels': list(LEVELS),
                     'practical_size': PRACTICAL_SIZE, 'arms': list(ARMS),
                     'gate_sha256': gate_file_sha256()},
    }


# --------------------------------------------------------------- entry points

def evaluate(gate_input):
    """Run the gate on an in-memory input after the D8 confirmation check."""
    analysis_guard.require_d8_confirmation()
    _require_pins()
    return _evaluate(gate_input)


def _no_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f'duplicate JSON key {key!r} in gate input')
        out[key] = value
    return out


def _no_constant(name):
    raise ValueError(f'non-finite JSON constant {name} in gate input')


def load_and_evaluate(path):
    """Check D8 confirmation, pins and sealed paths before opening the input file."""
    analysis_guard.require_d8_confirmation()
    _require_pins()
    analysis_guard.refuse_sealed(path)
    with open(path, encoding='utf-8') as handle:
        gate_input = json.load(handle, object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)
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
