"""Whole-gate STOP probability of the D8 gate with and without the dev-z eligibility rule (Q2).

Synthetic Monte Carlo only; no label, table or seed of the project is read. AI-assisted.

Model (declared; docs/r1/reports/M11_D8_GATE_V2_20261114.md):

* each node has paired per-instance differences d = oracle - A2 with true mean mu and
  standard deviation sigma = 1, drawn independently on the dev split (n_dev instances) and on
  the test split (n_test instances); "true test z" is mu * sqrt(n_test) / sigma;
* distributions: normal, or left-skewed (d = mu - (L - E L) / sd L with L lognormal(0, 1));
* eligibility: delta_n is assumed non-binding (every node clears it), so the old rule makes every
  node eligible; the new rule adds dev_z = mean(d_dev) / (sd(d_dev, ddof=1) / sqrt(n_dev)) >= 6;
* an eligible node STOPs the gate if its point test denominator mean(d_test) <= 0 or any of
  2,000 within-node bootstrap means of d_test is <= 0 (as in r1/c3/gate.py); the gate also
  STOPs when no node is eligible.

Dev and test samples are independent and nodes are independent, so with per-node eligibility
probability e(z) and per-node test-STOP probability s(z):
    P(no eligible node)   = prod_j (1 - e_j)
    P(gate reads)         = prod_j (1 - e_j s_j) - P(no eligible node)
    P(whole-gate STOP)    = 1 - P(gate reads)
    E[eligible nodes]     = sum_j e_j
e and s are Monte Carlo estimates on a grid of true test z; the scenarios combine them exactly.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

SEED = 20261114
DEV_Z_MIN = 6.0
N_BOOT = 2000


def draw(rng, dist, mu, size):
    if dist == 'normal':
        return mu + rng.standard_normal(size)
    if dist == 'left_skewed':
        mean, sd = math.exp(0.5), math.sqrt((math.e - 1.0) * math.e)
        return mu - (rng.lognormal(0.0, 1.0, size) - mean) / sd
    raise ValueError(dist)


def eligibility(rng, dist, z_test, n_test, n_dev, reps):
    """P(dev_z >= 6) for a node with true test z ``z_test``."""
    mu = z_test / math.sqrt(n_test)
    d = draw(rng, dist, mu, (reps, n_dev))
    z = d.mean(axis=1) / (d.std(axis=1, ddof=1) / math.sqrt(n_dev))
    return float(np.mean(z >= DEV_Z_MIN))


def test_stop(rng, dist, z_test, n_test, reps):
    """P(point test mean <= 0 or any of N_BOOT resampled means <= 0)."""
    mu = z_test / math.sqrt(n_test)
    stops = 0
    for _ in range(reps):
        d = draw(rng, dist, mu, n_test)
        if not d.mean() > 0:
            stops += 1
            continue
        idx = rng.integers(0, n_test, size=(N_BOOT, n_test))
        if np.any(~(d[idx].mean(axis=1) > 0)):
            stops += 1
    return stops / reps


def combine(e, s, m_weights):
    """Scenario summary from per-node probabilities; m_weights: list of (e_j, s_j)."""
    no_elig = math.prod(1.0 - ej for ej, _ in m_weights)
    reads = math.prod(1.0 - ej * sj for ej, sj in m_weights) - no_elig
    return {'p_stop': 1.0 - reads, 'p_no_eligible': no_elig, 'expected_eligible': sum(ej for ej, _ in m_weights)}


def run(n_test, n_devs, z_grid, dists, ms, reps_e, reps_s, seed=SEED):
    rng = np.random.Generator(np.random.PCG64(seed))
    per_node = {}
    for dist in dists:
        for z in z_grid:
            s = test_stop(rng, dist, z, n_test, reps_s)
            per_node[(dist, z, 'test_stop')] = s
            for n_dev in n_devs:
                per_node[(dist, z, n_dev)] = eligibility(rng, dist, z, n_test, n_dev, reps_e)
    rows = []
    for dist in dists:
        for m in ms:
            scenarios = [(f'all nodes z = {z:g}', [z] * m) for z in z_grid if z >= 3]
            mixed = [z for z in z_grid if 3 <= z <= 8]
            scenarios.append((f'z spread over the grid points {mixed[0]:g}..{mixed[-1]:g}',
                              [mixed[round(i * (len(mixed) - 1) / (m - 1))] for i in range(m)]))
            for label, zs in scenarios:
                old = combine(None, None, [(1.0, per_node[(dist, z, 'test_stop')]) for z in zs])
                row = {'dist': dist, 'm': m, 'scenario': label, 'old_rule': old, 'new_rule': {}}
                for n_dev in n_devs:
                    row['new_rule'][n_dev] = combine(None, None, [(per_node[(dist, z, n_dev)],
                                                                    per_node[(dist, z, 'test_stop')]) for z in zs])
                rows.append(row)
    table = {f'{d}|z={z:g}|{k}': v for (d, z, k), v in per_node.items()}
    return {'seed': seed, 'n_test': n_test, 'n_devs': list(n_devs), 'reps_eligibility': reps_e,
            'reps_test_stop': reps_s, 'n_boot': N_BOOT, 'dev_z_min': DEV_Z_MIN,
            'per_node': table, 'scenarios': rows}


def markdown(res):
    out = [f"Per-node probabilities (n_test = {res['n_test']}; test STOP from {res['reps_test_stop']} nodes, "
           f"eligibility from {res['reps_eligibility']} nodes):", '',
           '| d | true test z | P(test STOP) | ' + ' | '.join(f'P(eligible), n_dev = {n}' for n in res['n_devs']) + ' |',
           '|---' * (3 + len(res['n_devs'])) + '|']
    keys = sorted({(k.split('|')[0], float(k.split('|')[1][2:])) for k in res['per_node']})
    for d, z in keys:
        cells = [f"{res['per_node'][f'{d}|z={z:g}|test_stop']:.3f}"] + \
                [f"{res['per_node'][f'{d}|z={z:g}|{n}']:.3f}" for n in res['n_devs']]
        out.append(f'| {d} | {z:g} | ' + ' | '.join(cells) + ' |')
    out += ['', 'Scenarios (P(STOP) / P(no eligible node) / E[eligible]):', '',
            '| d | nodes | scenario | old rule (delta_n only) | ' +
            ' | '.join(f'new rule, n_dev = {n}' for n in res['n_devs']) + ' |',
            '|---' * (4 + len(res['n_devs'])) + '|']
    fmt = lambda r: f"{r['p_stop']:.2f} / {r['p_no_eligible']:.2f} / {r['expected_eligible']:.1f}"
    for row in res['scenarios']:
        out.append(f"| {row['dist']} | {row['m']} | {row['scenario']} | {fmt(row['old_rule'])} | " +
                   ' | '.join(fmt(row['new_rule'][n]) for n in res['n_devs']) + ' |')
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--n-test', type=int, default=20)
    ap.add_argument('--n-dev', type=int, nargs='+', default=[10, 20, 60])
    ap.add_argument('--reps-eligibility', type=int, default=20000)
    ap.add_argument('--reps-test-stop', type=int, default=4000)
    ap.add_argument('--json', default=None)
    a = ap.parse_args(argv)
    z_grid = [3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 10.0]
    res = run(a.n_test, a.n_dev, z_grid, ['normal', 'left_skewed'], [10, 15], a.reps_eligibility, a.reps_test_stop)
    print(markdown(res))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
