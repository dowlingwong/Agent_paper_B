"""Paired campaign inference for P9 and Paper C plan §11. ENGINEERING_ONLY.

The campaign instance, not an audit or manager repetition, is the unit. Use
one frozen artifact per arm. Holm is applied across the declared nodes to
superiority p-values and, separately, to the TOST intersection-union p-values.
There is no extra correction between TOST's two sides.

See Holm (1979), https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf,
and Schuirmann (1987), https://doi.org/10.1007/BF01068419.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math

import numpy as np
from scipy.stats import norm, t

ALPHA = 0.025
EQUIVALENCE_POWER_FLOOR = 0.80


@dataclass(frozen=True, order=True)
class CampaignKey:
    node: str
    instance_seed: int
    start_configuration: str


@dataclass(frozen=True)
class CampaignOutcome:
    key: CampaignKey
    value: float | None     # None records an attempted but incomplete campaign.
    manager_rep: int = 0
    audit_seed: int | None = None   # None represents a supplied audit mean.
    fit_seed: int | None = None     # A single frozen fit per arm.


@dataclass(frozen=True)
class PairedCampaigns:
    keys: tuple[CampaignKey, ...]
    differences: tuple[float, ...]
    attempted: int
    left_incomplete: int
    right_incomplete: int

    @property
    def excluded(self):
        return self.attempted - len(self.keys)


def _campaigns(rows):
    data = defaultdict(lambda: defaultdict(dict))
    seeds = set()
    for row in rows:
        audits = data[row.key][row.manager_rep]
        if row.audit_seed in audits:
            raise ValueError(f"duplicate campaign measurement: {row.key}")
        if row.value is not None and not math.isfinite(row.value):
            raise ValueError(f"nonfinite campaign outcome: {row.key}")
        audits[row.audit_seed] = row.value
        seeds.add(row.fit_seed)
    if len(seeds) > 1:
        raise ValueError("pass one frozen fit per arm; fit seeds are not independent campaigns")
    return data


def pair_campaigns(left, right) -> PairedCampaigns:
    """Match attempts and nested measurement IDs, then average within campaigns."""
    a, b = _campaigns(left), _campaigns(right)
    if not a or a.keys() != b.keys():
        raise ValueError("arms need the same nonempty set of attempted campaign keys")
    if len({key.node for key in a}) != 1:
        raise ValueError("paired inference uses one node's raw metric at a time")
    keys, differences = [], []
    missing_a = missing_b = 0
    for key in sorted(a):
        pa, pb = a[key], b[key]
        if pa.keys() != pb.keys():
            raise ValueError(f"manager repetitions differ between arms: {key}")
        incomplete_a = incomplete_b = False
        repetition_means = []
        for rep in sorted(pa):
            ra, rb = pa[rep], pb[rep]
            if ra.keys() != rb.keys() or (None in ra and len(ra) > 1):
                raise ValueError(f"audit IDs must match and a supplied audit mean stands alone: {key}")
            miss_a = any(value is None for value in ra.values())
            miss_b = any(value is None for value in rb.values())
            incomplete_a |= miss_a
            incomplete_b |= miss_b
            if not miss_a and not miss_b:
                repetition_means.append(math.fsum(ra[seed] - rb[seed] for seed in sorted(ra)) / len(ra))
        missing_a += incomplete_a
        missing_b += incomplete_b
        if not incomplete_a and not incomplete_b:
            keys.append(key)
            differences.append(math.fsum(repetition_means) / len(repetition_means))
    return PairedCampaigns(tuple(keys), tuple(differences), len(a), missing_a, missing_b)


def et0_margin(frozen_edit_sd: float) -> float:
    if not math.isfinite(frozen_edit_sd) or frozen_edit_sd < 0:
        raise ValueError("the frozen node scale must be finite and nonnegative")
    return max(0.002, 0.25 * frozen_edit_sd)


def esyn_margin(dp_value: float, best_myopic_value: float) -> float:
    gap = dp_value - best_myopic_value
    if not math.isfinite(gap) or gap < -1e-14:
        raise ValueError("invalid E-SYN DP-minus-myopic gap")
    return 0.1 * max(0.0, gap)


def _validate_alpha(alpha):
    if not 0 < alpha < 0.5:
        raise ValueError("one-sided alpha must lie in (0, 0.5)")


@dataclass(frozen=True)
class PairedTest:
    n: int
    mean: float | None
    se: float | None
    ci: tuple[float, float] | None
    delta: float
    alpha: float
    p_superiority: float
    p_lower: float
    p_upper: float
    p_tost: float
    status: str


def paired_test(differences, delta: float, *, alpha=ALPHA, known_sd=None) -> PairedTest:
    """One-sided paired t and TOST. Known positive SD is for the Normal control."""
    _validate_alpha(alpha)
    if not math.isfinite(delta) or delta < 0:
        raise ValueError("equivalence margin must be finite and nonnegative")
    if known_sd is not None and (not math.isfinite(known_sd) or known_sd <= 0):
        raise ValueError("known SD must be finite and positive")
    x = np.asarray(differences, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("paired differences must be a finite one-dimensional sample")
    n = len(x)
    mean = float(x.mean()) if n else None
    if n < 2:
        return PairedTest(n, mean, None, None, delta, alpha, 1.0, 1.0, 1.0, 1.0, "insufficient pairs")
    sd = float(x.std(ddof=1)) if known_sd is None else known_sd
    if not math.isfinite(mean) or not math.isfinite(sd):
        raise ValueError("nonfinite paired mean or standard deviation")
    if sd == 0:
        return PairedTest(n, mean, 0.0, None, delta, alpha, 1.0, 1.0, 1.0, 1.0, "unresolved variance")
    se = sd / math.sqrt(n)
    law = t(df=n - 1) if known_sd is None else norm
    half = float(law.isf(alpha)) * se
    p_superiority = float(law.sf(mean / se))
    p_lower = float(law.sf((mean + delta) / se))
    p_upper = float(law.sf((delta - mean) / se))
    return PairedTest(n, mean, se, (mean - half, mean + half), delta, alpha,
                      p_superiority, p_lower, p_upper, max(p_lower, p_upper), "tested")


def holm(p_values):
    """Adjusted p-values in input order using Holm's cumulative step-down rule."""
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("Holm requires a vector of finite p-values in [0, 1]")
    order = np.argsort(p, kind="stable")
    result = np.empty_like(p)
    result[order] = np.minimum(1.0, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return result


def family_decisions(tests, *, alpha=ALPHA, go_no_go=None, equivalence_power_at_zero=None):
    """One Q-family; include every declared node, with None for unavailable data."""
    _validate_alpha(alpha)
    go = {} if go_no_go is None else go_no_go
    power = {} if equivalence_power_at_zero is None else equivalence_power_at_zero
    if set(go) - set(tests) or set(power) - set(tests):
        raise ValueError("gates must refer to declared family nodes")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in power.values()):
        raise ValueError("predeclared power must lie in [0, 1]")
    available = [test is not None and test.status == "tested" and go.get(node, True)
                 for node, test in tests.items()]
    p_sup = holm([test.p_superiority if keep else 1.0 for test, keep in zip(tests.values(), available)])
    p_eq = holm([test.p_tost if keep and test.delta > 0 else 1.0
                 for test, keep in zip(tests.values(), available)])
    result = {}
    for i, (node, test) in enumerate(tests.items()):
        superiority = bool(p_sup[i] <= alpha)
        rejects_equivalence_null = bool(p_eq[i] <= alpha)
        equivalence_testable = bool(available[i] and test.delta > 0
                                   and power.get(node, 0.0) >= EQUIVALENCE_POWER_FLOOR)
        equivalence = rejects_equivalence_null and equivalence_testable
        if not available[i]:
            decision = "not testable at this budget"
        elif superiority and equivalence:
            decision = "superiority and equivalence"
        elif superiority:
            decision = "superiority"
        elif equivalence:
            decision = "equivalence"
        else:
            decision = "inconclusive"
        result[node] = {"superiority_p_holm": float(p_sup[i]), "tost_p_holm": float(p_eq[i]),
                        "superiority": superiority, "tost_rejects": rejects_equivalence_null,
                        "equivalence_testable": equivalence_testable, "equivalence": equivalence,
                        "decision": decision}
    return result


def normal_power(n: int, effect: float, sd: float, delta: float, *, alpha=ALPHA) -> dict:
    """Closed-form power for known-variance Gaussian paired differences."""
    _validate_alpha(alpha)
    if (n < 2 or not math.isfinite(effect) or not math.isfinite(sd) or sd <= 0
            or not math.isfinite(delta) or delta < 0):
        raise ValueError("invalid Normal power design")
    se = sd / math.sqrt(n)
    z = norm.isf(alpha)
    lower, upper = -delta / se + z, delta / se - z
    return {"superiority": float(norm.cdf(effect / se - z)),
            "tost_rejects": float(max(0.0, norm.cdf(upper - effect / se) - norm.cdf(lower - effect / se)))}
