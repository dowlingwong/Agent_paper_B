"""T5 simulator checks (ENGINEERING_ONLY): closed forms, T4 identities at small scale, branch study."""
from __future__ import annotations

import math

import numpy as np
import pytest

from r1.theory.simulate_t4 import (BranchStudy, Node, Policy, PType, Scenario, branch_stats, branch_study,
                                   fit_constants, gap_bounds, gap_exact, mills, paired, prop10b_loss,
                                   record_bias_formula, reweight, simulate, t_star, type_summary, value)
from r1.theory.t5_report import TYPES, Ctx, di_types, part_calibration, scenario

NODE = Node("test", sigma=0.0125, rho_local=0.82, rho_struct=0.55, split_share=0.6)
TYPES_T = (PType("dup", 0.45, 0.0, 0.0, pi=1.0), PType("bad", 0.20, -0.012, 0.008),
           PType("good", 0.15, 0.003, 0.005), PType("struct", 0.20, -0.006, 0.014, kind="structural", bold=True))


def test_gap_identity_and_bounds():
    rng = np.random.default_rng(0)
    for _ in range(200):
        mu, tau, sig = rng.normal(0, 0.01), rng.uniform(0.002, 0.02), rng.uniform(0.002, 0.02)
        tt = rng.normal(0, 0.01)
        g = float(gap_exact(tt, mu, tau, sig))
        direct = float(value(t_star(mu, tau, sig), mu, tau, sig) - value(tt, mu, tau, sig))
        lo, hi = gap_bounds(tt, mu, tau, sig)
        assert g == pytest.approx(direct, abs=1e-12)
        assert -1e-15 <= float(lo) <= g + 1e-15 and g <= float(hi) + 1e-15


def test_value_matches_monte_carlo():
    rng = np.random.default_rng(1)
    mu, tau, sig, t = -0.004, 0.009, 0.0075, 0.002
    d = rng.normal(mu, tau, 2_000_000)
    mc = np.mean(d * ((d + rng.normal(0, sig, d.size)) > t))
    assert float(value(t, mu, tau, sig)) == pytest.approx(mc, abs=3e-5)


def test_record_bias_formula_matches_truncated_normal():
    rng = np.random.default_rng(2)
    e, delta, rho, sigma, t = 0.006, 0.001, 0.8, 0.0125, 0.0
    sc = sigma * math.sqrt(1 - rho ** 2)
    eps = rho * e + sc * rng.standard_normal(4_000_000)
    kept = eps[delta + eps - e > t]
    assert float(record_bias_formula(e, delta, rho, sc, t)) == pytest.approx(kept.mean(), abs=2e-5)
    assert float(mills(-40.0)) >= 0 and np.isfinite(mills(40.0))


def test_prop10b_example():
    assert prop10b_loss(0.0, 2.0) == pytest.approx(1.61, abs=0.01)
    assert prop10b_loss(0.5, 2.0) == pytest.approx(prop10b_loss(0.0, 2.0) - 0.5)


def test_reweight_and_summary():
    ts = reweight(TYPES_T, inert_share=0.3, dispersion=2.0)
    s0, s1 = type_summary(TYPES_T), type_summary(ts)
    assert s1["inert_share"] == pytest.approx(0.3)
    assert s1["mu_bar"] == pytest.approx(s0["mu_bar"])
    assert s1["sd_type_means"] == pytest.approx(2 * s0["sd_type_means"])


def test_common_random_numbers_are_deterministic():
    scn = Scenario("t", NODE, TYPES_T)
    a = simulate(scn, Policy("o", prior="oracle"), 20, 40, 500, 11)
    b = simulate(scn, Policy("o", prior="oracle"), 20, 40, 500, 11)
    assert np.array_equal(a["_J"], b["_J"])


def test_prop7_identity_stationary_iid():
    scn = Scenario("t", NODE, TYPES_T)
    const = fit_constants(scn, 20, 40, 2000, 5)
    o = simulate(scn, Policy("o", prior="oracle"), 20, 40, 6000, 6, ref=(const.mu_r, const.tau_r, 0.0))
    a = simulate(scn, Policy("a2", prior="rules"), 20, 40, 6000, 6, const)
    d, se = paired(o, a)
    assert abs(d - o["gap"][0]) < 4 * se + 1e-5
    assert o["gap_lo"][0] <= o["gap"][0] <= o["gap_hi"][0]


def test_prop8_lagrangian_identity():
    scn = Scenario("t", NODE, TYPES_T)
    g = 0.0012
    a = simulate(scn, Policy("x", prior="oracle", rules=False), 30, 30, 6000, 7, g_eval=g)
    b = simulate(scn, Policy("s", prior="oracle", rules=False, screen=True, g=g), 30, 30, 6000, 7)
    d, se = paired(b, a, "_lag")
    assert abs(d - a["pos_part"][0]) < 4 * se + 1e-5


@pytest.mark.parametrize("prop", ["stationary", "memory"])
def test_prop9_formula_holds_for_every_proposer(prop):
    scn = scenario("digits_on", "record", prop)
    r = simulate(scn, Policy("rho", prior="zero", rules=False), 30, 60, 3000, 8)
    p = r["p9_summary"]
    assert abs(p["mean_residual"]) < 4 * p["se_residual"] + 1e-6
    assert p["null_mean_rise"] > 0


def test_calibrated_predictor_limits():
    scn = Scenario("t", NODE, TYPES_T)
    const = fit_constants(scn, 20, 40, 3000, 9)
    o = simulate(scn, Policy("o", prior="oracle"), 20, 40, 2000, 10, const)
    c0 = simulate(scn, Policy("c", prior="calibrated", noise_sd=0.0), 20, 40, 2000, 10, const)
    assert np.allclose(o["_J"], c0["_J"])
    a2 = simulate(scn, Policy("a2", prior="rules"), 20, 40, 2000, 10, const)
    cinf = simulate(scn, Policy("c", prior="calibrated", noise_sd=10.0), 20, 40, 2000, 10, const)
    d, se = paired(cinf, a2)
    assert abs(d) < 4 * se + 2e-4


def test_branch_study_record_reference_and_proxy_bias():
    bs = BranchStudy("t", di_types("tabular", "hom"), 0.0027, 0.0037, rho=0.0, split="vary")
    br = branch_study(bs, 6000, 12)
    st = branch_stats(br)
    assert st["changed"] > 50
    # verify promotions replace an upward-biased record: the reference drops
    assert st["signed_rec0_promotion"] < 0
    # next-trial identity: Delta_hat shift = absolute-metric shift - record shift
    assert st["signed_dh1_changed"] == pytest.approx(st["signed_ab1_changed"] - st["signed_rec0_changed"], abs=1e-12)
    # the incumbent-relative contrast is inflated relative to the true-value contrast
    assert st["signed_dh1_changed"] > st["signed_tv1_changed"] + 0.0005
    # selection: E[proxy] exceeds the true immediate value, so the residual is negative under DI
    assert st["proxy_bias"] > 0.0005
    assert st["residual"] < -0.0005
    assert abs(st["residual_oracle_immediate"]) < 0.5 * st["proxy_bias"]


def test_branch_study_detects_a_real_shift_in_true_value():
    base = BranchStudy("t", di_types("tabular", "hom"), 0.0027, 0.0037, rho=0.5)
    fb = BranchStudy("t", di_types("tabular", "hom"), 0.0027, 0.0037, rho=0.5, feedback_shift=0.003)
    s0 = branch_stats(branch_study(base, 6000, 13))
    s1 = branch_stats(branch_study(fb, 6000, 13))
    assert s1["signed_tv3_promotion"] > s0["signed_tv3_promotion"] + 0.001


def test_calibration_part_runs():
    out = part_calibration(Ctx(quick=True), "calibration")
    for k in TYPES:
        r = out["scenarios"][k]
        assert 0.2 <= r["p_improve_informative"] <= 0.5
        assert 0.4 <= r["inert_share"] <= 0.77
