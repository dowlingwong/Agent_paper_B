"""C3 labels: bins, soft labels, moments. ENGINEERING_ONLY; AI-assisted (Claude)."""
import numpy as np
import pytest

from r1.c3 import labels as L


def test_bins_layout():
    assert L.N_BINS == 12 and len(L.EDGES) == 12 and len(L.MIDPOINTS) == 11
    assert L.hard_bin(0.0) == 6 and L.hard_bin(-10) == 1 and L.hard_bin(10) == 11
    assert L.hard_bin(0.15) == 6 and L.hard_bin(0.16) == 7 and L.hard_bin(-3.5) == 1


def test_soft_label_is_normal_mass_over_bins():
    p = L.soft_label(0.004, 0.001, 0.004)  # z = 1, sd 0.25
    assert p.sum() == pytest.approx(1.0) and p[0] == 0
    assert p[8] + p[9] > 0.95  # mass around z = 1 (bins (0.5,1] and (1,2])
    hard = L.soft_label(0.004, 0.0, 0.004)
    assert hard[L.hard_bin(1.0)] == 1.0
    inert = L.soft_label(None, None, 0.004, inert=True)
    assert inert[0] == 1.0 and inert.sum() == 1.0
    with pytest.raises(ValueError):
        L.soft_label(None, 0.1, 1.0)


def test_moments_from_bins():
    p = np.zeros(12)
    p[0], p[11] = 0.5, 0.5
    pi, mu, tau = L.moments(p, 0.01)
    assert pi == 0.5 and mu == pytest.approx(0.04) and tau == pytest.approx(0.0)
    _, _, tau_f = L.moments(p, 0.01, tau_floor_z=0.15)
    assert tau_f == pytest.approx(0.0015)
    q = np.zeros(12)
    q[1], q[11] = 0.5, 0.5
    _, mu2, tau2 = L.moments(q, 1.0)
    assert mu2 == pytest.approx(0.0) and tau2 == pytest.approx(4.0)


def test_soft_label_moments_recover_gaussian():
    p = L.soft_label(0.0, 1.0, 1.0)
    _, mu, tau = L.moments(p, 1.0)
    assert abs(mu) < 1e-9 and 0.8 < tau < 1.3


def test_prob_positive_and_log_score():
    p = L.soft_label(1.0, 0.01, 1.0)
    assert L.prob_positive(p) == pytest.approx(1.0)
    assert L.log_score(p, p) <= L.log_score(p, np.full(12, 1 / 12))
