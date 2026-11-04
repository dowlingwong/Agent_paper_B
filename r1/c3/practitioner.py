"""D7 practitioner baseline building blocks (CPU only, AI-assisted Codex).

A0/rho in offline_eval already implements Karpathy's always-execute,
keep-if-positive rule. The additional Welch test consumes explicit observations
only; scheduling and online controller integration are not implemented here.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import t as student_t

from r1.c3.gate import require_gate_confirmation


def welch_replicates(candidate, incumbent, *, remaining_runs):
    """One-sided Welch r=3, alpha=0.05, all six measurements charged.

    Candidate and incumbent values are direction-normalized so larger is
    better. This is an independent-sample Welch test, not a paired t-test.
    Conservative accounting charges all three runs of each configuration;
    whether pre-existing incumbent measurements may be reused is an open
    operational question. Reject insufficient budgets and invalid observations.
    """
    if type(remaining_runs) is not int or remaining_runs < 6:
        raise ValueError('six worker-run budget units required for independent samples')
    c, i = np.asarray(candidate, dtype=float), np.asarray(incumbent, dtype=float)
    if c.shape != (3,) or i.shape != (3,) or not np.isfinite(c).all() or not np.isfinite(i).all():
        raise ValueError('Welch baseline requires three finite observations per configuration')
    delta = float(c.mean() - i.mean())
    a, b = float(c.var(ddof=1) / 3), float(i.var(ddof=1) / 3)
    variance = a + b
    if variance == 0:
        p = 0.0 if delta > 0 else 1.0
        df = None
    else:
        df = variance * variance / (a * a / 2 + b * b / 2)
        p = float(student_t.sf(delta / np.sqrt(variance), df))
    return {'execute': True, 'keep': bool(p < .05), 'p_value': p,
            'mean_difference': delta, 'degrees_of_freedom': df,
            'worker_runs_charged': 6, 'candidate_runs': 3, 'incumbent_runs': 3,
            'test': 'one-sided Welch', 'alpha': .05}


def offline_welch_values(rows):
    """New evaluation adapter; guard before reading any supplied instance rows.

    This opt-in interface currently always stops. A future implementation must
    verify held-out values, seeds, sample weights and source provenance; legacy
    readers are unchanged.
    """
    require_gate_confirmation()
    raise RuntimeError("STOP: evaluation-row provenance is not implemented")
