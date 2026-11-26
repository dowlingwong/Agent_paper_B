"""AI-assisted (Claude, coordinating chat, 23 Nov 2026).

Spot check (b) of PLAN row R1-PROOF-POLICY. Written independently of
ai_proof_check_20261123.py: no code or numbers are imported from it. Each block
re-derives one key identity or inequality, or one edge case, of a statement
rated in AI_PROOF_CHECK_20261123.md. Record: SPOT_CHECK_COORDINATOR_20261123.md.

Run: python3 spot_check_coordinator_20261123.py > spot_check_coordinator_20261123_output.txt
Fixed seeds; the output is reproducible.
"""

import numpy as np
import sympy as sp
from scipy import integrate, stats

PHI = stats.norm.cdf
phi = stats.norm.pdf


def line(tag, msg):
    print(f"{tag}: {msg}")


# ---------------------------------------------------------------- T2 Prop. 1
def V_closed(t, mu0, tau, sd):
    s = np.sqrt(tau**2 + sd**2)
    z = (t - mu0) / s
    return mu0 * PHI(-z) + tau**2 / s * phi(z)


def t2_prop1():
    # Key 1: V(t) closed form, symbolic route via the posterior-mean decomposition.
    t, mu0 = sp.symbols("t mu0", real=True)
    tau, sd = sp.symbols("tau sd", positive=True)
    s = sp.sqrt(tau**2 + sd**2)
    z = (t - mu0) / s
    Phi = lambda x: (1 + sp.erf(x / sp.sqrt(2))) / 2
    ph = lambda x: sp.exp(-x**2 / 2) / sp.sqrt(2 * sp.pi)
    V = mu0 * Phi(-z) + tau**2 / s * ph(z)
    tstar = -mu0 * sd**2 / tau**2
    f = ph(z) / s
    d = sp.simplify(sp.diff(V, t) + tau**2 / s**2 * f * (t - tstar))
    line("SC-T2-1", f"V'(t) + (tau^2/s^2) f(t) (t - t*) simplifies to {d}")
    # Monte Carlo of V at one point (independent check of the closed form).
    rng = np.random.default_rng(20261123)
    m0, ta, sdv, tt = -0.4, 0.7, 0.5, 0.1
    D = rng.normal(m0, ta, 4_000_000)
    Dh = D + rng.normal(0, sdv, D.size)
    x = D * (Dh > tt)
    line("SC-T2-2", f"V closed {V_closed(tt, m0, ta, sdv):.5f}; MC {x.mean():.5f} (s.e. {x.std()/np.sqrt(x.size):.5f})")
    # Edge: sigma_d = 0. V(t) = E[D 1{D > t}], so V' = -t f_D(t): unique optimum t = 0.
    for m in (-1.0, 0.0, 1.0):
        grid = np.linspace(-3, 3, 60001)
        Vg = V_closed(grid, m, 1.0, 0.0)
        line("SC-T2-3", f"sigma_d=0, mu0={m:+.1f}: argmax t = {grid[np.argmax(Vg)]:+.4f}; V(0)-V(-1) = {V_closed(0, m, 1, 0) - V_closed(-1, m, 1, 0):+.5f}")


# ---------------------------------------------------------------- T4 Prop. 6 scope and Lemma K
def scope_tstarstar():
    rho, sig, m, v, mu = sp.symbols("rho sigma m v mu", real=True)
    tau = sp.symbols("tau", positive=True)
    sc2 = sig**2 * (1 - rho**2)
    w2 = sc2 + (1 - rho) ** 2 * v
    # Bayes threshold from first principles: E[D | Dh] = mu + tau^2/(tau^2+w2) (Dh - M), M = mu - (1-rho) m.
    h = sp.symbols("h", real=True)
    post = mu + tau**2 / (tau**2 + w2) * (h - (mu - (1 - rho) * m))
    thr = sp.solve(sp.Eq(post, 0), h)[0]
    target = -(1 - rho) * m - mu * w2 / tau**2
    line("SC-T4-6a", f"threshold solving E[D|Dh]=0 minus stated t** = {sp.simplify(thr - target)}")
    line("SC-T4-6b", f"w^2 at m=0, v=sigma^2 minus 2 sigma^2 (1-rho) = {sp.simplify(w2.subs(v, sig**2) - 2*sig**2*(1-rho))}")
    tstar = -mu * 2 * sig**2 * (1 - rho) / tau**2
    diff = sp.simplify(target - tstar - (-(1 - rho) * m + mu * (1 - rho) ** 2 * (sig**2 - v) / tau**2))
    line("SC-T4-6c", f"t** - t* minus stated expression = {diff}")


def lemma_k_symbolic():
    rho, sig, m, v, mu, h = sp.symbols("rho sigma m v mu h", real=True)
    tau = sp.symbols("tau", positive=True)
    sc2 = sig**2 * (1 - rho**2)
    # Linear model given F_n: e ~ N(m, v), D ~ N(mu, tau^2), xi ~ N(0,1) independent.
    # eps = rho e + sc xi ; Dh = D + eps - e.
    S2 = tau**2 + sc2 + (1 - rho) ** 2 * v
    C = sc2 - rho * (1 - rho) * v                 # Cov(eps, Dh), derived by hand
    covED = -(1 - rho) * v                        # Cov(e, Dh)
    M = mu - (1 - rho) * m
    v_keep = rho**2 * v + sc2 - C**2 / S2
    v_disc = v - covED**2 / S2
    line("SC-K-1", f"sigma^2 - v_keep - [rho^2 (sigma^2 - v) + C^2/S^2] = {sp.simplify(sig**2 - v_keep - (rho**2*(sig**2 - v) + C**2/S2))}")
    line("SC-K-2", f"v - v_disc - (1-rho)^2 v^2/S^2 = {sp.simplify(v - v_disc - (1-rho)**2*v**2/S2)}")
    # Cross-check C with an explicit covariance-matrix computation.
    A = sp.Matrix([[1, 0, 0], [rho, 0, sp.sqrt(sc2)], [-(1 - rho), 1, sp.sqrt(sc2)]])  # rows: e, eps, Dh in terms of (e, D, xi)
    Sig = sp.diag(v, tau**2, 1)
    Cov = A * Sig * A.T
    line("SC-K-3", f"Cov(eps,Dh) - C = {sp.simplify(Cov[1, 2] - C)}; Var(Dh) - S^2 = {sp.simplify(Cov[2, 2] - S2)}; Cov(e,Dh) + (1-rho) v = {sp.simplify(Cov[0, 2] - covED)}")


def kalman_step(m, v, h, keep, mu, tau, rho, sig):
    sc2 = sig**2 * (1 - rho**2)
    S2 = tau**2 + sc2 + (1 - rho) ** 2 * v
    M = mu - (1 - rho) * m
    C = sc2 - rho * (1 - rho) * v
    m_k = rho * m + C * (h - M) / S2
    v_k = rho**2 * v + sc2 - C**2 / S2
    m_d = m - (1 - rho) * v * (h - M) / S2
    v_d = v - (1 - rho) ** 2 * v**2 / S2
    return np.where(keep, m_k, m_d), np.where(keep, v_k, v_d)


def lemma_k_numeric(rho, label, n=3_000_000, seed=7):
    """Simulate 3-trial campaigns under the kernel as the generative model and the
    deployed rule (t*_n with sigma_n^2 = 2 sigma^2 (1-rho)). If Lemma K holds, the
    residual r = (e_4 - m_4)/sqrt(v_4) is N(0,1) and independent of every function
    of the ledger; in particular within each keep pattern."""
    rng = np.random.default_rng(seed)
    sig = 1.0
    mus = np.array([-0.30, -0.05, 0.20])
    taus = np.array([0.50, 0.80, 0.40])
    sc = sig * np.sqrt(1 - rho**2)
    sn2 = 2 * sig**2 * (1 - rho)
    e = rng.normal(0, sig, n)
    m = np.zeros(n)
    v = np.full(n, sig**2)
    hs, ks = [], []
    for j in range(3):
        D = rng.normal(mus[j], taus[j], n)
        eps = rho * e + sc * rng.normal(0, 1, n)
        h = D + eps - e
        keep = h > -mus[j] * sn2 / taus[j] ** 2
        m, v = kalman_step(m, v, h, keep, mus[j], taus[j], rho, sig)
        e = np.where(keep, eps, e)
        hs.append(h)
        ks.append(keep)
    r = (e - m) / np.sqrt(v)
    H = np.column_stack(hs)
    pattern = ks[0].astype(int) * 4 + ks[1].astype(int) * 2 + ks[2].astype(int)
    line(f"SC-K-4[{label}]", f"all: mean r {r.mean():+.4f}, var r {r.var():.4f}, skew {stats.skew(r):+.4f}, ex.kurt {stats.kurtosis(r):+.4f}; max v_4/sigma^2 {v.max():.4f}")
    worst_t = 0.0
    for p in range(8):
        sel = pattern == p
        if sel.sum() < 20000:
            continue
        rp, ep = r[sel], e[sel]
        line(f"SC-K-5[{label}]", f"pattern {p:03b} (n={sel.sum()}): r mean {rp.mean():+.4f} var {rp.var():.4f} skew {stats.skew(rp):+.4f} | raw e mean {ep.mean():+.4f} skew {stats.skew(ep):+.4f}")
    # Orthogonality of r and r^2-1 to nonlinear ledger functions (t-statistics).
    tests = {
        "h1^2": H[:, 0] ** 2,
        "h1*h2": H[:, 0] * H[:, 1],
        "sign(h3)": np.sign(H[:, 2]),
        "h2^3": H[:, 1] ** 3,
        "keep3*h3": ks[2] * H[:, 2],
        "max(h)": H.max(axis=1),
    }
    out = []
    for name, g in tests.items():
        g = (g - g.mean()) / g.std()
        for lab, y in (("r", r), ("r2-1", r**2 - 1)):
            prod = g * y
            tstat = prod.mean() / (prod.std() / np.sqrt(n))
            worst_t = max(worst_t, abs(tstat))
            out.append(f"{lab}~{name} {tstat:+.2f}")
    line(f"SC-K-6[{label}]", "t-stats: " + "; ".join(out))
    # Contrast: standardising with moments given the keep pattern only (the coarser information
    # the T4:48 sentence has in mind) leaves dependence on the ledger values.
    rr = np.empty(n)
    for p in range(8):
        sel = pattern == p
        rr[sel] = (e[sel] - e[sel].mean()) / e[sel].std()
    g = (H[:, 2] - H[:, 2].mean()) / H[:, 2].std()
    tc = (g * rr).mean() / ((g * rr).std() / np.sqrt(n))
    line(f"SC-K-7[{label}]", f"max |t| above {worst_t:.2f}; pattern-only standardisation, t-stat against h3: {tc:+.1f}")
    # Share of histories with E[e | F] < 0 at trial 4 (S9: possible after a keep below the prior mean).
    line(f"SC-K-8[{label}]", f"share with E[e_4 | F_4] < 0: {(m < 0).mean():.4f}; share with at least one keep: {(pattern > 0).mean():.4f}")


# ---------------------------------------------------------------- T4 Prop. 7
def prop7():
    # Identity and both bounds at 50 digits (double precision loses V's difference when t* sits
    # far in a tail, e.g. tau = 0.05, sigma = 3).
    import mpmath as mp
    mp.mp.dps = 50
    rng = np.random.default_rng(11)
    fails = 0
    worst = mp.mpf(0)
    for _ in range(200):
        mu = mp.mpf(rng.normal(0, 1))
        tau = mp.mpf(np.exp(rng.uniform(np.log(0.05), np.log(3))))
        sd = mp.mpf(np.exp(rng.uniform(np.log(0.05), np.log(3))))
        s = mp.sqrt(tau**2 + sd**2)
        ts = -mu * sd**2 / tau**2
        tt = ts + mp.mpf(rng.uniform(-6, 6)) * s
        f = lambda u: mp.npdf(u, mu, s)
        z1, z0 = (ts - mu) / s, (tt - mu) / s
        # V(t*) - V(t~) with mu * [Phi(-z1) - Phi(-z0)] written as -mu * [Phi(z1) - Phi(z0)]
        # in the left tail, so that the constant mu cancels exactly instead of in floating point.
        dPhi = mp.ncdf(-z1) - mp.ncdf(-z0) if z1 + z0 > 0 else -(mp.ncdf(z1) - mp.ncdf(z0))
        gap = mu * dPhi + tau**2 / s * (mp.npdf(z1) - mp.npdf(z0))
        rhs = tau**2 / s**2 * mp.quad(lambda u: f(u) * (ts - u), mp.linspace(tt, ts, 401), maxdegree=8)
        worst = max(worst, abs(gap - rhs) / abs(gap))
        lo = tau**2 / (2 * s**2) * min(f(tt), f(ts)) * (ts - tt) ** 2
        hi = tau**2 * (ts - tt) ** 2 / (2 * mp.sqrt(2 * mp.pi) * s**3)
        fails += (not (lo <= gap <= hi)) or gap <= 0
    line("SC-T4-7a", f"200 random sets at 50 digits: max rel |gap - integral| {mp.nstr(worst, 3)}; bound or sign failures {fails}")
    # Local form: relative error (2/3)(t*-mu)(t*-t~)/s^2 at small h, both signs.
    mu, tau, sd = -0.6, 0.5, 0.8
    s = np.hypot(tau, sd)
    ts = -mu * sd**2 / tau**2
    for hrel in (1e-3, -1e-3):
        h = hrel * s
        tt = ts - h
        gap = V_closed(ts, mu, tau, sd) - V_closed(tt, mu, tau, sd)
        lead = tau**2 * phi((ts - mu) / s) / s * h**2 / (2 * s**2)
        pred = 1 + 2 / 3 * (ts - mu) * h / s**2
        line("SC-T4-7b", f"h/s={hrel:+.0e}: gap/lead {gap/lead:.7f}; predicted 1 + (2/3)(t*-mu)h/s^2 = {pred:.7f}")


# ---------------------------------------------------------------- T4 Prop. 9 / Cor. 9a
def lam(a):
    return np.exp(stats.norm.logpdf(a) - stats.norm.logsf(a))


def prop9():
    # (ii.2) edge: at p_G = 1 the strict inequality becomes equality. Example: eps uniform on [0, 1], c = -1.
    rng = np.random.default_rng(3)
    eps = rng.uniform(0, 1, 2_000_000)
    c = -1.0
    K = eps > c
    line("SC-T4-9a", f"p_G = {K.mean():.3f}: E[eps | K] - E[eps] = {eps[K].mean() - eps.mean():+.2e} (equality; strictness needs p_G < 1)")
    # Cor. 9a formula against simulation, and lambda(a) > max(0, a).
    for rho, e0, D in ((0.95, 0.7, -0.2), (0.6, -0.9, 0.1), (0.0, 0.0, 0.3)):
        sc = np.sqrt(1 - rho**2)
        x = rho * e0 + sc * rng.normal(0, 1, 4_000_000)
        keep = x > e0 - D
        a = ((1 - rho) * e0 - D) / sc
        pred = rho * e0 + sc * lam(a)
        line("SC-T4-9b", f"rho={rho}, e={e0:+.1f}, D={D:+.1f}: formula {pred:+.4f}; MC {x[keep].mean():+.4f} (s.e. {x[keep].std()/np.sqrt(keep.sum()):.4f}); exceeds max(e-D, rho e) = {max(e0-D, rho*e0):+.4f}: {pred > max(e0-D, rho*e0)}")
    a = np.linspace(-30, 30, 600001)
    margin = lam(a) - np.maximum(0, a)
    line("SC-T4-9c", f"lambda(a) - max(0, a) on [-30, 30]: min {margin.min():.3e} (> 0: {bool((margin > 0).all())})")
    # Edge rho -> 1: E[e' | K] -> e when D > 0 and -> e - D when D < 0.
    for D in (0.2, -0.2):
        rho, e0 = 0.9999, 0.5
        sc = np.sqrt(1 - rho**2)
        a = ((1 - rho) * e0 - D) / sc
        line("SC-T4-9d", f"rho={rho}, e={e0}, D={D:+.1f}: E[e'|K] = {rho*e0 + sc*lam(a):+.5f}")


# ---------------------------------------------------------------- T4 Prop. 10(b)
def prop10b():
    G = lambda b, t: b * PHI(b / t) + t * phi(b / t) - t * phi(0)
    line("SC-T4-10a", f"G(2,1) = {G(2.0, 1.0):.10f}; loss at alpha=1.6097 is (G-alpha)+ = {max(G(2.0, 1.0) - 1.6097, 0):.5f}, not 1.61-alpha = {1.61 - 1.6097:.5f}")
    rng = np.random.default_rng(5)
    d_keep = rng.normal(2.0, 1.0, 4_000_000)
    d_disc = rng.normal(0.0, 1.0, 4_000_000)
    a, b = np.maximum(d_keep, 0), np.maximum(d_disc, 0)
    se = np.sqrt(a.var() / a.size + b.var() / b.size)
    line("SC-T4-10b", f"simulated E[max(N(2,1),0)] - E[max(N(0,1),0)] = {a.mean() - b.mean():.5f} (s.e. {se:.5f}; G(2,1) = {G(2.0, 1.0):.5f})")
    # Unboundedness and the noisy-trial-2 extension: G_sigma >= beta - tau^2 phi(0)/s.
    for b in (2.0, 10.0, 100.0):
        tau, sd = 1.0, 0.5
        s = np.hypot(tau, sd)
        ts = -b * sd**2 / tau**2
        Gs = V_closed(ts, b, tau, sd) - V_closed(0.0, 0.0, tau, sd)
        line("SC-T4-10c", f"beta={b:g}: G = {G(b, 1.0):.5f} >= beta - phi(0) = {b - phi(0):.5f}; G_sigma(0.5) = {Gs:.5f} >= {b - tau**2*phi(0)/s:.5f}")


if __name__ == "__main__":
    t2_prop1()
    scope_tstarstar()
    lemma_k_symbolic()
    lemma_k_numeric(0.6, "rho=0.6")
    lemma_k_numeric(0.0, "rho=0.0", seed=8)
    lemma_k_numeric(0.9, "rho=0.9", seed=9)
    prop7()
    prop9()
    prop10b()
