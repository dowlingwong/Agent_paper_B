# AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.
"""Numerical checks for the author's proof check of T2 Propositions 1-5 and T4 Proposition 6. ENGINEERING_ONLY.

These checks support the proof check; they do not replace it. Closed forms are re-implemented here from the
statements, independently of r1/theory/acceptance.py, and checked by quadrature or simulation.
Run: python3 check_t2_p6.py   (NumPy and SciPy; fixed seed; a few minutes on 2 CPUs)
"""
import time

import numpy as np
from scipy import integrate, optimize
from scipy.stats import norm

rng = np.random.default_rng(20261122)
PHI0 = norm.pdf(0.0)


# ---------------------------------------------------------------------------
# closed forms, as written in the statements
# ---------------------------------------------------------------------------

def V(t, mu, tau, sigma):
    """T2 Proposition 1 / T4 notation: V(t) = mu Phi(-z) + (tau^2/s) phi(z)."""
    s = np.hypot(tau, sigma)
    z = (t - mu) / s
    return mu * norm.sf(z) + tau ** 2 / s * norm.pdf(z)


def V_quad(t, mu, tau, sigma):
    """Independent route: E[Delta P(Delta + e > t | Delta)] by quadrature over Delta."""
    if sigma == 0:
        f = lambda d: d * norm.pdf(d, mu, tau) * (d > t)
    else:
        f = lambda d: d * norm.pdf(d, mu, tau) * norm.sf((t - d) / sigma)
    val, _ = integrate.quad(f, mu - 12 * tau, mu + 12 * tau, points=[t] if sigma == 0 else None,
                            epsabs=1e-13, epsrel=1e-11, limit=200)
    return val


def psi(z):
    z = np.abs(z)
    return norm.pdf(z) - z * norm.sf(z)


def voi(m, q):
    """T2 Proposition 2: q psi(|m|/q); 0 at q = 0."""
    q = np.asarray(q, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(q > 0, q * psi(np.abs(m) / np.where(q > 0, q, 1.0)), 0.0)
    return out


def joint_cov(tau2, st2, ss2, r, policy):
    """Covariance of (Delta, Delta_hat, Dbar) in T2 section 1 (Delta, e_t, e_s, xi_i independent)."""
    if policy == "vary":
        vd, chd = tau2 + (st2 + ss2) / r, tau2
    else:  # fixed: Dbar = Delta + e_s + mean(xi), xi_i ~ N(0, st2)
        vd, chd = tau2 + ss2 + st2 / r, tau2 + ss2
    return np.array([[tau2, tau2, tau2], [tau2, tau2 + st2 + ss2, chd], [tau2, chd, vd]])


def post_var_and_q2(tau2, st2, ss2, r, policy):
    """v = Var(Delta | Delta_hat) and q^2 = v - Var(Delta | Delta_hat, Dbar), by Gaussian conditioning."""
    C = joint_cov(tau2, st2, ss2, r, policy)
    v = C[0, 0] - C[0, 1] ** 2 / C[1, 1]
    S = C[1:, 1:]
    c = C[0, 1:]
    v2 = C[0, 0] - c @ np.linalg.solve(S, c)
    return v, max(v - v2, 0.0)


def q2_fixed_explicit(tau2, st2, ss2, r):
    """Audit's explicit fixed-policy formula: q^2 = Cov(Delta, Dbar | H)^2 / Var(Dbar | H)."""
    A, u = tau2 + ss2, st2
    cov = tau2 * u / (A + u)
    var = u * (1 + 1 / r - u / (A + u))
    return cov ** 2 / var


def q2_vary_explicit(tau2, sd2, r):
    v = tau2 * sd2 / (tau2 + sd2)
    return v - 1.0 / (1.0 / v + r / sd2), v


def mills(a):
    return norm.pdf(a) / norm.sf(a)


def expected_max(n):
    """E[max of n iid N(0,1)] by quadrature."""
    f = lambda x: x * n * norm.cdf(x) ** (n - 1) * norm.pdf(x)
    val, _ = integrate.quad(f, -10, 10, limit=400)
    return val


def table_sigma_d(tau=0.009, g=0.0026):
    """Reconstruction for T2 section 6: the sigma_d at which g = V(t*) = 0.0026 when mu0 = 0, tau = 0.009."""
    return optimize.brentq(lambda x: V(0.0, 0.0, tau, x) - g, 1e-4, 0.1)


def line(s=""):
    print(s, flush=True)


# ---------------------------------------------------------------------------
# P01: T2 Proposition 1
# ---------------------------------------------------------------------------

def p01():
    line("== P01  T2 Proposition 1 ==")
    worst_q, beaten, sign_fail, n_sign = 0.0, 0, 0, 0
    for _ in range(1000):
        mu, tau, sig = rng.normal(0, 1), rng.uniform(0.2, 2), rng.uniform(0.05, 2)
        t = mu + rng.normal(0, 2)
        worst_q = max(worst_q, abs(V(t, mu, tau, sig) - V_quad(t, mu, tau, sig)))
        t_star = -mu * sig ** 2 / tau ** 2
        s = np.hypot(tau, sig)
        grid = np.linspace(min(t_star, mu) - 10 * s, max(t_star, mu) + 10 * s, 20001)
        beaten += int(np.max(V(grid, mu, tau, sig)) > V(t_star, mu, tau, sig) + 1e-15)
        # dV/dt = -f(t)(tau^2/s^2)(t - t*): positive below t*, negative above (finite differences, within 3 s)
        if abs(t_star - mu) < 2 * s:   # where the density is not negligible, so finite differences are reliable
            n_sign += 1
            pts = t_star + s * np.array([-1, -0.3, -0.1, 0.1, 0.3, 1])
            dv = (V(pts + 1e-5 * s, mu, tau, sig) - V(pts - 1e-5 * s, mu, tau, sig)) / (2e-5 * s)
            sign_fail += int(not (np.all(dv[:3] > 0) and np.all(dv[3:] < 0)))
    line(f"P01 value formula vs quadrature over Delta, 1000 random sets: max abs diff {worst_q:.1e}")
    line(f"P01 t* = -mu sigma_d^2/tau^2 is the maximiser: sets where a grid point (20001 points) beats V(t*): {beaten}/1000; "
         f"dV/dt not + below and - above t* (at t* +- 0.1, 0.3, 1 s; sets with |t* - mu| < 2 s): {sign_fail}/{n_sign}")
    n = 4_000_000
    mu, tau, sig, t = -0.4, 0.7, 1.1, 0.3
    d = rng.normal(mu, tau, n)
    x = d * (d + rng.normal(0, sig, n) > t)
    line(f"P01 value formula vs simulation (mu=-0.4, tau=0.7, sigma_d=1.1, t=0.3; 4e6 draws): "
         f"{V(t, mu, tau, sig):.5f} vs {x.mean():.5f} (s.e. {x.std() / np.sqrt(n):.5f})")
    # posterior-mean form of the rule: keep iff E[Delta | Delta_hat] > 0  <=>  Delta_hat > t*
    h = rng.normal(mu, np.hypot(tau, sig), 200000)
    pm = mu + tau ** 2 / (tau ** 2 + sig ** 2) * (h - mu)
    agree = np.mean((pm > 0) == (h > -mu * sig ** 2 / tau ** 2))
    line(f"P01 'keep iff posterior mean > 0' equals 'Delta_hat > t*' on 2e5 draws: agreement {agree:.6f}")
    # error rate of the default rule on a fixed Delta
    rows = []
    for delta in (-0.5, 0.2, 1.0):
        e = rng.normal(0, 0.8, n)
        err = np.mean(np.sign(delta + e) != np.sign(delta))
        rows.append(f"Delta={delta:+.1f}: {norm.cdf(-abs(delta) / 0.8):.5f} vs {err:.5f}")
    line("P01 error rate Phi(-|Delta|/sigma_d), sigma_d=0.8, formula vs simulation (4e6): " + "; ".join(rows))
    # edge case sigma_d = 0 (audit: t = 0 is the unique optimum, not every t <= 0)
    line(f"P01 edge sigma_d=0, mu=0, tau=1: V(0) = {V_quad(0.0, 0.0, 1.0, 0.0):.5f}, V(-1) = {V_quad(-1.0, 0.0, 1.0, 0.0):.5f}, "
         f"V(-0.1) = {V_quad(-0.1, 0.0, 1.0, 0.0):.5f}  (T2 text says every t <= 0 is optimal)")
    grid = np.linspace(-2, 2, 401)
    for mu0 in (-0.5, 0.0, 0.5):
        vals = np.array([V_quad(t, mu0, 1.0, 0.0) for t in grid])
        line(f"P01 edge sigma_d=0, tau=1, mu={mu0:+.1f}: grid argmax t = {grid[vals.argmax()]:+.3f} "
             f"(so t = 0 is optimal for every mu: 'default optimal only if mu = 0' needs sigma_d > 0)")


# ---------------------------------------------------------------------------
# P06: T4 Proposition 6
# ---------------------------------------------------------------------------

def p06():
    line("== P06  T4 Proposition 6 ==")
    n = 4_000_000
    pi, mu, tau, sig = 0.4, -0.3, 0.6, 0.8
    t_star = -mu * sig ** 2 / tau ** 2
    noop = rng.random(n) < pi
    d = np.where(noop, 0.0, rng.normal(mu, tau, n))
    eta = rng.normal(0, sig, n)
    h_exact = np.where(noop, 0.0, d + eta)          # bit-exact node: H = 0 on a no-op
    vstar = (1 - pi) * V(t_star, mu, tau, sig)
    x = d * (h_exact > t_star)
    line(f"P06 value of the threshold rule, bit-exact node (pi=0.4, mu=-0.3, tau=0.6, sigma=0.8; 4e6): "
         f"(1-pi)V(t*) = {vstar:.5f} vs simulation {x.mean():.5f} (s.e. {x.std() / np.sqrt(n):.5f})")
    grid = t_star + np.linspace(-1.5, 1.5, 61)
    vals = [(d * (h_exact > t)).mean() for t in grid]
    line(f"P06 grid search over thresholds on the same draws: best t = {grid[int(np.argmax(vals))]:+.3f}, t* = {t_star:+.3f} "
         f"(grid step 0.05)")
    # non-bit-exact node: on a no-op H = eta (not 0). Bayes posterior mean of the mixture vs the threshold rule.
    h_noisy = d + eta
    f1 = norm.pdf(h_noisy, mu, np.hypot(tau, sig))
    f0 = norm.pdf(h_noisy, 0.0, sig)
    m1 = mu + tau ** 2 / (tau ** 2 + sig ** 2) * (h_noisy - mu)
    m_mix = (1 - pi) * f1 * m1 / ((1 - pi) * f1 + pi * f0)
    agree = np.mean((m_mix > 0) == (h_noisy > t_star))
    x_bayes = d * (m_mix > 0)
    line(f"P06 non-bit-exact node (H = eta on a no-op): mixture Bayes rule agrees with H > t* on {agree:.6f} of draws; "
         f"its value {x_bayes.mean():.5f} (s.e. {x_bayes.std() / np.sqrt(n):.5f}) vs (1-pi)V(t*) = {vstar:.5f}")
    # sigma = 0: t* = 0 for every mu, so 'default rule optimal iff mu_n = 0' needs sigma > 0
    line(f"P06 sigma=0, mu=-0.7, tau=0.5: t* = -mu sigma^2/tau^2 = 0; V(0) = {V_quad(0.0, -0.7, 0.5, 0.0):.5f} "
         f">= V(0.2) = {V_quad(0.2, -0.7, 0.5, 0.0):.5f}, V(-0.2) = {V_quad(-0.2, -0.7, 0.5, 0.0):.5f}")
    # R1 option (ii): shared incumbent error e with posterior N(m_e, v_e) given O_n, candidate error rho e + sigma_c xi
    sigma, rho = 0.0125, 0.82                      # digits_mlp scale (T5 setup table)
    mu, tau = -0.004, 0.009                        # T2 section 6 table, second row
    sc = sigma * np.sqrt(1 - rho ** 2)
    sd_pair = sigma * np.sqrt(2 * (1 - rho))
    # consistency: at an unselected incumbent (m_e = 0, v_e = sigma^2) the corrected noise variance is sigma_d^2
    w2_fresh = (1 - rho) ** 2 * sigma ** 2 + sc ** 2
    line(f"P06/R1(ii) unselected incumbent: (1-rho)^2 sigma^2 + sigma_c^2 = {w2_fresh:.4e}, 2 sigma^2 (1-rho) = {sd_pair ** 2:.4e}")
    for m_e, v_e in ((0.0, sigma ** 2), (sigma, 0.25 * sigma ** 2), (2 * sigma, 0.25 * sigma ** 2)):
        e = rng.normal(m_e, np.sqrt(v_e), n)
        dd = rng.normal(mu, tau, n)
        hh = dd + (rho - 1) * e + sc * rng.normal(size=n)
        w2 = (1 - rho) ** 2 * v_e + sc ** 2
        t_plain = -mu * sd_pair ** 2 / tau ** 2
        t_corr = -(1 - rho) * m_e - mu * w2 / tau ** 2
        v_plain, v_corr = (dd * (hh > t_plain)).mean(), (dd * (hh > t_corr)).mean()
        se_v = (dd * (hh > t_corr)).std() / np.sqrt(n)
        se = (dd * ((hh > t_corr).astype(float) - (hh > t_plain))).std() / np.sqrt(n)
        grid = t_corr + sd_pair * np.linspace(-1, 1, 41)
        best = grid[int(np.argmax([(dd * (hh > t)).mean() for t in grid]))]
        line(f"P06/R1(ii) m_e={m_e / sigma:.0f} sigma, sd(e|O)={np.sqrt(v_e) / sigma:.1f} sigma: t* (Prop 6, sigma_d) = {t_plain * 1e3:+.3f}e-3, "
             f"corrected = {t_corr * 1e3:+.3f}e-3, grid best = {best * 1e3:+.3f}e-3; value 1e-3 x: plain {v_plain * 1e3:.4f}, "
             f"corrected {v_corr * 1e3:.4f} (s.e. {se_v * 1e3:.4f}), closed form corrected {V(t_corr + (1 - rho) * m_e, mu, tau, np.sqrt(w2)) * 1e3:.4f} "
             f"(paired s.e. of the difference {se * 1e3:.4f})")


# ---------------------------------------------------------------------------
# P02: T2 Proposition 2
# ---------------------------------------------------------------------------

def p02():
    line("== P02  T2 Proposition 2 ==")
    # pointwise VoI against simulation, using the true Delta (not the max formula)
    n = 6_000_000
    for policy, (mu, tau, st, ss, r, h0) in (("vary", (-0.3, 0.8, 0.5, 0.6, 2, 0.1)),
                                             ("fixed", (-0.3, 0.8, 0.5, 0.6, 2, 0.1)),
                                             ("vary", (0.0, 1.0, 0.7, 0.7, 3, 1.0))):
        tau2, st2, ss2 = tau ** 2, st ** 2, ss ** 2
        d = rng.normal(mu, tau, n)
        et, es = rng.normal(0, st, n), rng.normal(0, ss, n)
        h = d + et + es
        if policy == "vary":
            dbar = d + rng.normal(0, np.sqrt((st2 + ss2) / r), n)
        else:
            dbar = d + es + rng.normal(0, np.sqrt(st2 / r), n)
        C = joint_cov(tau2, st2, ss2, r, policy)
        beta = np.linalg.solve(C[1:, 1:], C[0, 1:])
        m_prime = mu + beta[0] * (h - mu) + beta[1] * (dbar - mu)
        m = mu + C[0, 1] / C[1, 1] * (h - mu)
        w = np.abs(h - h0) < 0.02
        gain = d[w] * ((m_prime[w] > 0).astype(float) - (m[w] > 0))
        v, q2 = post_var_and_q2(tau2, st2, ss2, r, policy)
        formula = voi(m[w], np.sqrt(q2)).mean()
        line(f"P02 VoI {policy:5s} (mu={mu}, tau={tau}, sd_t={st}, sd_s={ss}, r={r}, Delta_hat~{h0}): "
             f"formula {formula:.5f} vs simulation {gain.mean():.5f} (s.e. {gain.std() / np.sqrt(w.sum()):.5f}, n={w.sum()})")
    # explicit q^2 formulas vs covariance conditioning; monotonicity in r; concavity of q^2 (vary)
    worst_f, worst_v, mono_fail, conc_fail_vary, conc_fail_fixed = 0.0, 0.0, 0, 0, 0
    for _ in range(2000):
        tau, st, ss = rng.uniform(0.1, 2, 3)
        q2v = [post_var_and_q2(tau ** 2, st ** 2, ss ** 2, r, "vary")[1] for r in range(1, 31)]
        q2f = [post_var_and_q2(tau ** 2, st ** 2, ss ** 2, r, "fixed")[1] for r in range(1, 31)]
        worst_f = max(worst_f, max(abs(q2f[r - 1] - q2_fixed_explicit(tau ** 2, st ** 2, ss ** 2, r)) for r in (1, 5, 30)))
        worst_v = max(worst_v, max(abs(q2v[r - 1] - q2_vary_explicit(tau ** 2, st ** 2 + ss ** 2, r)[0]) for r in (1, 5, 30)))
        mono_fail += int(np.any(np.diff(q2v) < -1e-14) or np.any(np.diff(q2f) < -1e-14))
        conc_fail_vary += int(np.any(np.diff(q2v, 2) > 1e-14))
        conc_fail_fixed += int(np.any(np.diff(q2f, 2) > 1e-14))
    line(f"P02 q^2 explicit vs covariance conditioning (2000 sets): max diff fixed {worst_f:.1e}, vary {worst_v:.1e}")
    line(f"P02 q (hence VoI at fixed m) non-decreasing in r=1..30: failures {mono_fail}/2000; "
         f"q^2 concave in r: failures vary {conc_fail_vary}/2000, fixed {conc_fail_fixed}/2000")
    # VoI peaks at m = 0 and decreases in |m|
    ms = np.linspace(0, 5, 501)
    line(f"P02 VoI(m, q=1) decreasing in |m| on [0,5]: {bool(np.all(np.diff(voi(ms, 1.0)) < 0))}; max at m = {ms[np.argmax(voi(ms, 1.0))]:.2f}")
    # audit counterexample (v = 1, sigma_d = 1, m = 3)
    vals = [voi(3.0, np.sqrt(1 - 1 / (1 + r))) for r in (1, 2, 3)]
    line(f"P02 audit counterexample v=1, sigma_d=1, m=3: VoI r=1,2,3 = {vals[0]:.10f}, {vals[1]:.10f}, {vals[2]:.10f}; "
         f"increments {vals[1] - vals[0]:.10f}, {vals[2] - vals[1]:.10f}")
    sd2 = 1.0
    vs = [q2_vary_explicit(t2, sd2, 1)[1] for t2 in (0.5, 2.0, 100.0, 1e6)]
    line(f"P02 realisability: under vary, v = tau^2 sd^2/(tau^2+sd^2) < sd^2; at sd^2 = 1, tau^2 = 0.5, 2, 100, 1e6: v = "
         + ", ".join(f"{x:.6f}" for x in vs) + "  (so v = 1 with sigma_d = 1 is not attainable)")
    tau2 = 2.0
    v = tau2 * sd2 / (tau2 + sd2)
    vals = [voi(3.0, np.sqrt(q2_vary_explicit(tau2, sd2, r)[0])) for r in (1, 2, 3, 4)]
    line(f"P02 attainable counterexample tau^2=2, sigma_d^2=1 (v={v:.4f}), mu=0, Delta_hat=4.5 (m=3), vary: VoI r=1..4 = "
         + ", ".join(f"{x:.3e}" for x in vals) + "; increments " + ", ".join(f"{b - a:.3e}" for a, b in zip(vals, vals[1:])))
    # the same in fixed policy
    vals = [voi(3.0, np.sqrt(post_var_and_q2(2.0, 0.5, 0.5, r, "fixed")[1])) for r in (1, 2, 3, 4)]
    line(f"P02 fixed policy, tau^2=2, sd_t^2=sd_s^2=0.5, m=3: VoI r=1..4 = " + ", ".join(f"{x:.3e}" for x in vals)
         + "; increments " + ", ".join(f"{b - a:.3e}" for a, b in zip(vals, vals[1:])))
    # at m = 0 VoI = q phi(0) is concave in r (vary)
    vals = [voi(0.0, np.sqrt(q2_vary_explicit(tau2, sd2, r)[0])) for r in range(1, 7)]
    line("P02 at m=0 (same parameters, vary): increments in r " + ", ".join(f"{b - a:.4f}" for a, b in zip(vals, vals[1:])))


# ---------------------------------------------------------------------------
# P03: T2 Proposition 3
# ---------------------------------------------------------------------------

def p03():
    line("== P03  T2 Proposition 3 ==")
    mu, tau, ss, r = -0.3, 0.8, 0.6, 2
    tau2, ss2 = tau ** 2, ss ** 2
    A = tau2 + ss2
    rows = []
    for st in (0.5, 1e-1, 1e-2, 1e-3, 1e-4):
        st2 = st ** 2
        vf, q2f = post_var_and_q2(tau2, st2, ss2, r, "fixed")
        vv, q2v = post_var_and_q2(tau2, st2, ss2, r, "vary")
        h = 0.0
        m = mu + tau2 / (A + st2) * (h - mu)
        rows.append(f"sd_t={st:.0e}: VoI fixed {float(voi(m, np.sqrt(q2f))):.3e}, at m=0 {float(voi(0.0, np.sqrt(q2f))):.3e} "
                    f"(q^2/sd_t^2 = {q2f / st2:.4f}), "
                    f"VoI vary {float(voi(m, np.sqrt(q2v))):.4e}")
    line("P03 (mu=-0.3, tau=0.8, sd_s=0.6, r=2, Delta_hat=0): " + "; ".join(rows))
    line(f"P03 fixed: limit of q^2/sd_t^2 from the explicit formula tau^4/(A^2 (1/r + 1)) = {tau2 ** 2 / (A ** 2 * (1 / r + 1)):.4f}")
    v_lim = tau2 * ss2 / A
    q2_lim = v_lim ** 2 / (v_lim + ss2 / r)
    vv, q2v = post_var_and_q2(tau2, 1e-12, ss2, r, "vary")
    line(f"P03 vary: limit q^2 = v^2/(v + sd_s^2/r) = {q2_lim:.6f}; computed at sd_t=1e-6: {q2v:.6f}")
    hs = (0.0, 2.0, 5.0, 10.0)
    vals = [float(voi(mu + tau2 / A * (h - mu), np.sqrt(q2_lim))) for h in hs]
    line("P03 vary limit is pointwise, not uniform: VoI at Delta_hat = " + ", ".join(f"{h:g}: {v:.2e}" for h, v in zip(hs, vals)))
    # PLAN 'Verify split policy' row says vary is never less informative than fixed: compare q (same r)
    worse = 0
    for _ in range(2000):
        tau, st, ss = rng.uniform(0.05, 3, 3)
        for r in range(1, 6):
            worse += int(post_var_and_q2(tau ** 2, st ** 2, ss ** 2, r, "fixed")[1]
                         > post_var_and_q2(tau ** 2, st ** 2, ss ** 2, r, "vary")[1] + 1e-15)
    line(f"P03 cases with q_fixed > q_vary (2000 random sets x r=1..5): {worse}/10000")
    # T2 section 4: fraction of vary's max VoI that fixed recovers, at the sd_train/sd_joint ratios quoted for the MLP nodes
    tau, sd = 0.009, table_sigma_d()
    for ratio in (0.06, 0.39, 0.56, 0.65):
        st2 = (ratio * sd) ** 2
        ss2b = sd ** 2 - st2
        qf = np.sqrt(post_var_and_q2(tau ** 2, st2, ss2b, 2, "fixed")[1])
        qv = np.sqrt(post_var_and_q2(tau ** 2, st2, ss2b, 2, "vary")[1])
        line(f"P03 max-VoI ratio fixed/vary at r=2, tau=0.009, sigma_d={sd:.5f} (see P05), sd_train/sd_joint={ratio:.2f}: {qf / qv:.3f}")


# ---------------------------------------------------------------------------
# P04: T2 Proposition 4
# ---------------------------------------------------------------------------

def p04():
    line("== P04  T2 Proposition 4 ==")
    n = 8_000_000
    sigma, rho, delta = 1.0, 0.6, 0.3
    e = rng.normal(0, sigma, n)
    eps = rho * e + sigma * np.sqrt(1 - rho ** 2) * rng.normal(size=n)
    keep = delta + eps > e
    rows = []
    for lo, hi in ((-1.05, -0.95), (-0.05, 0.05), (0.95, 1.05), (1.95, 2.05)):
        w = (e > lo) & (e < hi)
        mid = (lo + hi) / 2
        f = norm.cdf((delta - (1 - rho) * mid) / (sigma * np.sqrt(1 - rho ** 2)))
        rows.append(f"e~{mid:+.0f}: {f:.4f} vs {keep[w].mean():.4f}")
    line("P04(a) P(keep | e), unselected bivariate-normal record, sigma=1, rho=0.6, delta=0.3 (formula vs simulation, 8e6): "
         + "; ".join(rows))
    # T2 section 5 digits reading
    s, r, d = 0.0125, 0.8, 0.005
    sc = s * np.sqrt(1 - r ** 2)
    line(f"P04 digits reading: sigma sqrt(1-rho^2) = {sc:.5f}; Phi(0.005/{sc:.4f}) = {norm.cdf(d / sc):.4f}; "
         f"Phi((0.005 - 0.2*0.0125)/{sc:.4f}) = {norm.cdf((d - (1 - r) * s) / sc):.4f}")
    # kernel after a keep: three generative models, digits scale; condition on the record's error after one null keep
    n = 20_000_000
    out = {}
    for model in ("kernel", "shared", "fresh"):
        rr = 0.0 if model == "fresh" else r
        if model == "shared":
            u = rng.normal(0, np.sqrt(rr) * s, n)
            v0, v1, v2 = (rng.normal(0, np.sqrt(1 - rr) * s, n) for _ in range(3))
            e0, e1 = u + v0, u + v1
            kept = e1 > e0                                    # null proposal kept
            # test edit of size d against record e (unselected e0, or kept e1)
            acc_unsel = d + (u + v2) > e0
            acc_kept = d + (u + v2) > e1
        else:
            scm = s * np.sqrt(1 - rr ** 2)
            e0 = rng.normal(0, s, n)
            e1 = rr * e0 + scm * rng.normal(size=n)
            kept = e1 > e0
            acc_unsel = d + rr * e0 + scm * rng.normal(size=n) > e0
            acc_kept = d + rr * e1 + scm * rng.normal(size=n) > e1
        res = []
        for target in (0.0, s):
            w0 = np.abs(e0 - target) < 0.05 * s
            w1 = kept & (np.abs(e1 - target) < 0.05 * s)
            f = norm.cdf((d - (1 - rr) * target) / (s * np.sqrt(1 - rr ** 2)))
            res.append((target, f, acc_unsel[w0].mean(), acc_kept[w1].mean(), np.sqrt(0.25 / w1.sum())))
        out[model] = res
    for model, res in out.items():
        line(f"P04 P(keep delta=0.005 | record e), sigma=0.0125, rho={'0' if model == 'fresh' else '0.8'}, model '{model}' "
             "(e | formula | unselected record | record kept once by a null keep | s.e. <=): "
             + "; ".join(f"e={t / s:.0f}sigma | {f:.4f} | {a:.4f} | {b:.4f} | {se:.4f}" for t, f, a, b, se in res))
    # (b) expected running maximum vs sigma sqrt(2 ln n)
    rows = []
    for k in (10, 40, 1000, 100000):
        em = expected_max(k + 1)                    # initial record + k fresh draws
        rows.append(f"n={k}: E[max of n+1] = {em:.3f}, sqrt(2 ln n) = {np.sqrt(2 * np.log(k)):.3f}, ratio {em / np.sqrt(2 * np.log(k)):.3f}")
    line("P04(b) record after n null fresh-draw trials (sigma=1): " + "; ".join(rows))
    # (b) and the shared-component analogue: acceptance of a fixed delta after n null trials
    M = 400_000
    s, rho, d = 0.0125, 0.8, 0.005
    for n_null in (5, 20, 40, 200):
        res = {}
        # fresh draws (rho = 0)
        e = rng.normal(0, s, M)
        for _ in range(n_null):
            c = rng.normal(0, s, M)
            e = np.where(c > e, c, e)
        res["fresh"] = norm.cdf((d - e) / s).mean()
        # kernel (AR(1) parent) model
        sck = s * np.sqrt(1 - rho ** 2)
        e = rng.normal(0, s, M)
        for _ in range(n_null):
            c = rho * e + sck * rng.normal(size=M)
            e = np.where(c > e, c, e)
        res["kernel"] = norm.cdf((d - (1 - rho) * e) / sck).mean()
        # shared component model: only the record's own part v matters
        sv = s * np.sqrt(1 - rho)
        v = rng.normal(0, sv, M)
        for _ in range(n_null):
            c = rng.normal(0, sv, M)
            v = np.where(c > v, c, v)
        res["shared"] = norm.cdf((d - v) / sv).mean()
        # closed form for the shared model: E Phi(delta/sv - M_{n+1})
        k = n_null + 1
        cf = integrate.quad(lambda x: norm.cdf(d / sv - x) * k * norm.cdf(x) ** (k - 1) * norm.pdf(x), -10, 10, limit=400)[0]
        line(f"P04 acceptance of delta=0.005 after {n_null:3d} null trials (sigma=0.0125; 4e5 campaigns): fresh rho=0 {res['fresh']:.3f}; "
             f"kernel rho=0.8 {res['kernel']:.3f}; shared rho=0.8 {res['shared']:.3f} (closed form {cf:.3f})")


# ---------------------------------------------------------------------------
# P05: T2 Proposition 5
# ---------------------------------------------------------------------------

def p05():
    line("== P05  T2 Proposition 5 ==")
    fails, worst_ratio = 0, 0.0
    for _ in range(2000):
        mu = rng.normal(0, 1)
        tau, st, ss = rng.uniform(0.05, 3, 3)
        r = int(rng.integers(1, 6))
        for pol in ("vary", "fixed"):
            v, q2 = post_var_and_q2(tau ** 2, st ** 2, ss ** 2, r, pol)
            hs = rng.normal(mu, 3, 50)
            m = mu + tau ** 2 / (tau ** 2 + st ** 2 + ss ** 2) * (hs - mu)
            vo = voi(m, np.sqrt(q2))
            fails += int(np.any(vo > np.sqrt(q2) * PHI0 + 1e-15) or np.sqrt(q2) > np.sqrt(v) + 1e-15)
            if r == 2:
                worst_ratio = max(worst_ratio, np.sqrt(q2) * PHI0 / np.hypot(st, ss))
    line(f"P05 VoI <= q phi(0) <= sqrt(v) phi(0): violations {fails} of 4000 parameter sets x 50 Delta_hat")
    line(f"P05 q and v do not involve Delta_hat or mu0 (they are built from the covariance only; see post_var_and_q2)")
    sups = []
    for r in (1, 2, 3):
        q2, v = q2_vary_explicit(1e8, 1.0, r)
        sups.append(f"r={r}: {np.sqrt(q2) * PHI0:.4f} (2r x 0.1 = {0.2 * r:.1f})")
    line("P05 sup over tau of max VoI / sigma_d (vary, tau -> infinity): " + "; ".join(sups))
    line(f"P05 largest max-VoI / sigma_d seen at r=2 over random sets (both policies): {worst_ratio:.4f}")
    # T2 section 6 table: back-solve sigma_d from g = V(t*) = 0.0026 at mu0 = 0, tau = 0.009, then recompute the rest
    tau = 0.009
    sd = table_sigma_d()
    v = tau ** 2 * sd ** 2 / (tau ** 2 + sd ** 2)
    q2v = q2_vary_explicit(tau ** 2, sd ** 2, 2)[0]
    g2 = V(-(-0.004) * sd ** 2 / tau ** 2, -0.004, tau, sd)
    line(f"P05 table reconstruction (assumption: the table's sigma_d is the one giving g = 0.0026 in row 1): sigma_d = {sd:.5f}; "
         f"row 2 g = V(t*) = {g2:.5f}; max VoI vary r=2 = {np.sqrt(q2v) * PHI0:.5f}; 4g threshold for verify: g < {np.sqrt(q2v) * PHI0 / 4:.5f}; "
         f"sqrt(v) phi(0) = {np.sqrt(v) * PHI0:.5f}")
    for share in (0.5, 0.36, 0.25):
        st2 = share * sd ** 2
        q2f = post_var_and_q2(tau ** 2, st2, sd ** 2 - st2, 2, "fixed")[1]
        line(f"P05 same sigma_d, training share of the paired variance {share:.2f}: max VoI fixed r=2 = {np.sqrt(q2f) * PHI0:.5f}")


# ---------------------------------------------------------------------------
# T4 Proposition 10(b) (summary file only)
# ---------------------------------------------------------------------------

def p10b():
    line("== T4 Proposition 10(b) ==")
    n = 4_000_000
    tau, beta = 1.0, 2.0
    myopic = tau * PHI0
    keep_part = beta * norm.cdf(beta / tau) + tau * norm.pdf(beta / tau)
    z = rng.normal(0, tau, n)                       # common random numbers for the two branches
    diff = np.maximum(beta + z, 0) - np.maximum(z, 0)
    line(f"P10(b) tau=1, beta=2: keep-branch gain minus myopic = {keep_part - myopic:.5f}; "
         f"simulation (common random numbers, 4e6) {diff.mean():.5f} (s.e. {diff.std() / np.sqrt(n):.5f})")


if __name__ == "__main__":
    t0 = time.time()
    line("AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.")
    line("Output of check_t2_p6.py (seed 20261122).")
    p01()
    p06()
    p02()
    p03()
    p04()
    p05()
    p10b()
    line(f"total run time {time.time() - t0:.0f} s")
