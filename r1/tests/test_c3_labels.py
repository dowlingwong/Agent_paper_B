"""C3 labels: bins, soft labels, moments. ENGINEERING_ONLY; AI-assisted (Claude)."""
import numpy as np
import pytest

from r1.c3 import labels as L


def test_bins_layout():
    assert L.N_BINS == 12 and len(L.EDGES) == 12 and len(L.MIDPOINTS) == 11
    assert L.hard_bin(0.0) == 6 and L.hard_bin(-10) == 1 and L.hard_bin(10) == 11
    assert L.hard_bin(0.15) == 6 and L.hard_bin(0.16) == 7 and L.hard_bin(-3.5) == 1


def test_soft_label_is_normal_mass_over_bins():
    p = L.soft_label(0.004, 0.001, 0.004, sigma_mode="se_audit")  # z = 1, sd 0.25
    assert p.sum() == pytest.approx(1.0) and p[0] == 0
    assert p[8] + p[9] > 0.95  # mass around z = 1 (bins (0.5,1] and (1,2])
    hard = L.soft_label(0.004, 0.0, 0.004, sigma_mode="se_audit")
    assert hard[L.hard_bin(1.0)] == 1.0
    inert = L.soft_label(None, None, 0.004, inert=True)
    assert inert[0] == 1.0 and inert.sum() == 1.0
    with pytest.raises(ValueError):
        L.soft_label(None, 0.1, 1.0, sigma_mode="se_audit")


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
    p = L.soft_label(0.0, 1.0, 1.0, sigma_mode="se_audit")
    _, mu, tau = L.moments(p, 1.0)
    assert abs(mu) < 1e-9 and 0.8 < tau < 1.3


def test_prob_positive_and_log_score():
    p = L.soft_label(1.0, 0.01, 1.0, sigma_mode="se_audit")
    assert L.prob_positive(p) == pytest.approx(1.0)
    assert L.log_score(p, p) <= L.log_score(p, np.full(12, 1 / 12))


# ---------------------------------------------------------------------------------- tail law (E5, R1-G5-TAILS)
def _gaussian_reference(zm, zs):
    """The Gaussian path exactly as on main before the Student-t unit (``_gaussian_bins`` at 6684e840)."""
    from scipy.stats import norm
    p = np.zeros(L.N_BINS)
    if zs <= 0:
        p[L.hard_bin(zm)] = 1.0
        return p
    p[1:] = np.diff(norm.cdf((L.EDGES - zm) / zs))
    p = np.clip(p, 0.0, None)
    return p / p.sum()


def test_gaussian_soft_label_unchanged_bit_for_bit():
    """The default (and explicit ``tails="gaussian"``) path returns the very bytes of the pre-unit Gaussian code, over
    both sigma modes, partial K, zero width and the inert label."""
    for d in np.linspace(-0.05, 0.05, 41):
        for sig in (0.003, 0.01, 0.0217):
            for k in (1, 2, 3, 5, 6):
                want = _gaussian_reference(float(d) / sig, sig / np.sqrt(k) / sig)
                for kw in ({}, {"tails": "gaussian"}, {"tails": "gaussian", "nu": None}):
                    got = L.soft_label(float(d), None, sig, sigma_mode="pooled_node", k_label=k, **kw)
                    assert got.tobytes() == want.tobytes()
            for se in (0.0, 0.001, 0.004):
                want = _gaussian_reference(float(d) / sig, se / sig)
                assert L.soft_label(float(d), se, sig, sigma_mode="se_audit").tobytes() == want.tobytes()
    assert L.soft_label(None, None, 0.01, inert=True).tobytes() == L.soft_label(
        None, None, 0.01, inert=True, tails="student_t", nu=5).tobytes()


def test_student_t_soft_label_against_scipy_reference():
    """Student-t of location Δ/σ and sd s (scale s·sqrt((ν−2)/ν)), integrated over the bins: checked against
    scipy.stats.t directly and against fixed reference values (ν = 5, Δ = 0, k = 1: s = 1 in z units)."""
    from scipy.stats import norm, t
    nu = 5
    p = L.soft_label(0.0, None, 0.01, sigma_mode="pooled_node", k_label=1, tails="student_t", nu=nu)
    scale = np.sqrt((nu - 2) / nu)
    assert t.std(nu, scale=scale) == pytest.approx(1.0, abs=1e-15)             # σ̂ keeps its sd meaning
    assert p[6] == pytest.approx(2 * t.cdf(0.15 / scale, nu) - 1, abs=1e-15)
    assert p[6] == pytest.approx(0.1459282170706906, abs=1e-12)                 # central bin (−0.15, 0.15]
    assert p[11] == pytest.approx(t.sf(3 / scale, nu), abs=1e-15)
    assert p[11] == pytest.approx(0.0058624055019772525, abs=1e-12)             # z > 3
    assert p[11] > 1 - norm.cdf(3)                                               # heavier than the Gaussian at equal sd
    assert p[0] == 0 and p.sum() == pytest.approx(1.0, abs=1e-15)
    assert np.allclose(p[1:], p[1:][::-1], atol=1e-15)                          # symmetric about Δ = 0
    for d, sig, k, v in ((0.012, 0.01, 3, 5), (-0.004, 0.0217, 6, 3.5), (0.0, 0.003, 2, 30)):
        zm, zs = d / sig, (sig / np.sqrt(k)) / sig
        sc = zs * np.sqrt((v - 2) / v)
        ref = np.diff(t.cdf(L.EDGES, v, loc=zm, scale=sc))
        got = L.soft_label(d, None, sig, sigma_mode="pooled_node", k_label=k, tails="student_t", nu=v)
        assert np.allclose(got[1:], ref / ref.sum(), atol=1e-14, rtol=0)
        assert L.student_t_scale(zs, v) == pytest.approx(sc, rel=1e-15)
    big = L.soft_label(0.012, None, 0.01, sigma_mode="pooled_node", k_label=3, tails="student_t", nu=1e7)
    assert np.allclose(big, L.soft_label(0.012, None, 0.01, sigma_mode="pooled_node", k_label=3), atol=1e-6)
    hard = L.soft_label(0.004, 0.0, 0.004, sigma_mode="se_audit", tails="student_t", nu=5)
    assert hard[L.hard_bin(1.0)] == 1.0                                          # zero width: the hard bin, as Gaussian


@pytest.mark.parametrize("tails, nu", [("student_t", None), ("student_t", 2), ("student_t", 1.5),
                                       ("student_t", True), ("student_t", "5"), ("student_t", float("nan")),
                                       ("student_t", float("inf")), ("gaussian", 5), ("laplace", None)])
def test_tail_law_refusals(tails, nu):
    with pytest.raises(ValueError):
        L.soft_label(0.01, None, 0.01, sigma_mode="pooled_node", k_label=3, tails=tails, nu=nu)
    with pytest.raises(ValueError):
        L.check_tail_law(tails, nu)
