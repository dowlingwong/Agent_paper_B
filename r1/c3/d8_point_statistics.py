"""Pure synthetic-ready D8 point statistics; not a gate or data reader.

This module computes only the declared node-level IQM and node-equal
probability of improvement. It does not perform normalization, exclusion,
bootstrap, hypothesis testing, authorization or evidence provenance checks.
"""
import math


def _values(items, label):
    if not isinstance(items, (list, tuple)) or not items:
        raise ValueError(f'{label} must be a nonempty sequence')
    values = []
    for value in items:
        if type(value) not in (int, float):
            raise ValueError(f'{label} contains a non-numeric value')
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f'{label} contains a non-finite value')
        values.append(value)
    return values


def node_iqm(gap_closed):
    """25%-trimmed mean with fractional weights at empirical quantile edges."""
    values = sorted(_values(gap_closed, 'node gap closed'))
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


def node_equal_probability_of_improvement(nodes):
    """Average node-level win rates; ties count one half, nodes equally."""
    if not isinstance(nodes, (list, tuple)) or not nodes:
        raise ValueError('nodes must be a nonempty sequence')
    node_rates = []
    for pair in nodes:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError('each node needs arm and baseline values')
        arm = _values(pair[0], 'arm utility')
        baseline = _values(pair[1], 'baseline utility')
        if len(arm) != len(baseline):
            raise ValueError('paired node observations differ in length')
        score = sum(1.0 if a > b else 0.5 if a == b else 0.0
                    for a, b in zip(arm, baseline))
        node_rates.append(score / len(arm))
    return sum(node_rates) / len(node_rates)
