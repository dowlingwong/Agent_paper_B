"""B.7 aggregate gate on already computed, paired instance utilities.

ENGINEERING_ONLY; AI-assisted (Codex). No table reader or label loader is here.
The caller must compute the TRACK_P §7.1 noisy-oracle utility using only the
label-seed block, and provide its utility evaluated on the evaluation block.
Inputs must be per-instance, per-20-run utilities with matching A2/A3/A5/oracle
values; dev_denominators are measured on dev, without looking at test data.
No operational verdict is possible: authenticating a committed author PLAN
row, provenance validation, and inferential protocol remain unimplemented.
The production entry point stops before any input is iterated.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

CONFIRM_ID = "R1-BX-D8-CONFIRM"


def gate_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def require_gate_confirmation():
    """Fail closed until the committed, author-owned PLAN is authenticated.

    A caller-supplied PLAN path, local ref or self-declared commit is not
    authority. The future implementation must authenticate the exact published
    decision and its commit before this check can pass. No test-only escape is
    exposed by the production interface.
    """
    raise RuntimeError("STOP: trusted committed author PLAN authentication is not implemented")


def _iqm(values):
    """Mean of the empirical quantile function over its middle half."""
    x = np.sort(np.asarray(values, dtype=float))
    if not len(x) or not np.isfinite(x).all():
        raise ValueError("IQM requires finite values from at least one node")
    n = len(x)
    lo, hi = n * .25, n * .75
    weights = np.maximum(0, np.minimum(np.arange(1, n + 1), hi) - np.maximum(np.arange(n), lo))
    return float(np.dot(x, weights) / (hi - lo))


def _summaries(groups, dev_denominators, deltas, arm, draws=None):
    gaps, improvements, by_node = [], [], {}
    for node, all_rows in groups.items():
        rows = all_rows if draws is None else [all_rows[i] for i in draws[node]]
        a2 = np.asarray([r['A2'] for r in rows]); test = np.asarray([r[arm] for r in rows])
        oracle = np.asarray([r['oracle'] for r in rows])
        denom = float(np.mean(oracle) - np.mean(a2))
        improvement = float(np.mean((test > a2) + .5 * (test == a2)))
        eligible = dev_denominators[node] >= deltas[node]
        gap = None
        if eligible:
            if denom <= 0 or not math.isfinite(denom):
                raise ValueError(f"STOP: nonpositive test oracle gap for {node}")
            gap = float((np.mean(test) - np.mean(a2)) / denom)
            gaps.append(gap)
        improvements.append(improvement)
        by_node[node] = {'gap_closed': gap, 'probability_improvement': improvement,
                         'dev_denominator': dev_denominators[node], 'delta_n': deltas[node],
                         'test_denominator': denom, 'included_in_iqm': eligible}
    return {'iqm_gap_closed': _iqm(gaps), 'probability_improvement': float(np.mean(improvements)), 'nodes': by_node}


def aggregate_gate(rows, dev_denominators, deltas):
    """Unavailable pending author-PLAN, provenance and inference review.

    No input is iterated. Future integration must fix bootstrap to 2000,
    predeclare the null/interval and nonpositive-oracle-denominator treatment,
    validate the noisy oracle and all data partitions, and run an independent
    reference comparison. The older percentile/p-value prototype is removed.
    """
    require_gate_confirmation()
    raise RuntimeError("STOP: aggregate gate provenance and inference are not implemented")
