"""Independent AI proof check of T2 Prop. 1, T4 Props. 6, 7 (+ Cor. 7a), 9 (+ Cor. 9a) and 10(b). ENGINEERING_ONLY.

AI-assisted (Claude, subagent, 23 Nov 2026). The independent AI proof check under PLAN R1-PROOF-POLICY (check (a));
the coordinating chat's spot check (b) is separate. Not an author check.

Run:  python3 ai_proof_check_20261123.py > ai_proof_check_20261123_output.txt
Needs SymPy, NumPy, SciPy, mpmath. Fixed seeds (20261123; the second session's checks XS/XN use 20261124). About 2-3
minutes on 2 CPUs; the run time goes to stderr, so the output file is byte-reproducible.

Second session (23 Nov, after the first run was interrupted): the first run's lines are unchanged; added at the end are
XS1-XS4 (Kalman variance identities, Prop. 7 local-form series, Prop. 10(b) with noise), XN1-XN2 (the posterior of the
record error given the full ledger is Gaussian: an independent implementation by explicit Gaussian conditioning, and a
conditional-moment test under the deployed rule t*) and XN3 (Prop. 7 at extreme parameters, 50-digit arithmetic).

Every output line starts with a label (S = symbolic, N = numeric) that AI_PROOF_CHECK_20261123.md cites.
Symbolic lines print the simplified difference between two expressions (0 means the identity holds) or a solution.
Numeric lines are evidence, not proofs.
"""
import time
import numpy as np
import sympy as sp
import mpmath
import scipy
from scipy import integrate, optimize, special, stats
from scipy.stats import norm

T0 = time.time()
SEED = 20261123
rng = np.random.default_rng(SEED)


def out(s=""):
    print(s, flush=True)


# ---------------------------------------------------------------- numeric helpers
def V(t, mu, tau, sigma):
    """T2 Prop. 1 closed form, stable for extreme z (norm.sf / norm.cdf)."""
    s = np.hypot(tau, sigma)
    z = (t - mu) / s
    return mu * norm.sf(z) + tau ** 2 / s * norm.pdf(z)


def tstar(mu, tau, sigma):
    return -mu * sigma ** 2 / tau ** 2


def mills(a):
    """lambda(a) = phi(a) / Phi(-a), stable for large a (erfcx)."""
    a = np.asarray(a, dtype=float)
    return np.sqrt(2 / np.pi) / special.erfcx(a / np.sqrt(2))


def skew_kurt(x):
    x = np.asarray(x)
    m, sd = x.mean(), x.std()
    zz = (x - m) / sd
    return m, sd, (zz ** 3).mean(), (zz ** 4).mean() - 3


# ================================================================ symbolic part
def symbolic():
    out("== S: symbolic checks (SymPy %s) ==" % sp.__version__)
    t, mu, y, u, a, x, c, m, h, me = sp.symbols('t mu y u a x c m h m_e', real=True)
    tau, sig, sc, v, beta, alpha = sp.symbols('tau sigma sigma_c v beta alpha', positive=True)
    rho = sp.symbols('rho', positive=True)
    Phi = lambda q: (1 + sp.erf(q / sp.sqrt(2))) / 2
    phi = lambda q: sp.exp(-q ** 2 / 2) / sp.sqrt(2 * sp.pi)
    S = sp.sqrt(tau ** 2 + sig ** 2)
    f = lambda q: phi((q - mu) / S) / S
    z = (t - mu) / S
    Vs = mu * Phi(-z) + tau ** 2 / S * phi(z)
    post = mu + tau ** 2 / S ** 2 * (y - mu)  # E[Delta | Delta_hat = y] (regression of a bivariate normal)

    # --- T2 Prop. 1
    lem = sp.integrate((y - mu) * f(y), (y, t, sp.oo))
    out("S1.1 lemma E[(Y-mu)1{Y>t}] - s*phi(z): %s" % sp.simplify(lem - S * phi(z)))
    I = sp.integrate(post * f(y), (y, t, sp.oo))
    out("S1.2 V(t) := int_t^oo E[D|Dh=y] f(y) dy  minus  mu Phi(-z) + tau^2/s phi(z): %s" % sp.simplify(I - Vs))
    dV = sp.diff(Vs, t)
    out("S1.3 dV/dt + f(t) E[D|Dh=t]: %s" % sp.simplify(dV + f(t) * post.subs(y, t)))
    ts = sp.solve(sp.Eq(post.subs(y, t), 0), t)
    out("S1.4 root of the posterior mean in t: %s ; at sigma=0: %s" % (ts, [sp.simplify(r.subs(sig, 0)) for r in ts]))
    T = -mu * sig ** 2 / tau ** 2
    out("S1.5 dV/dt + f(t)(tau^2/s^2)(t - t*): %s  (so sign dV/dt = -sign(t - t*) for tau > 0)"
        % sp.simplify(dV + f(t) * tau ** 2 / S ** 2 * (t - T)))
    d2 = sp.diff(Vs, t, 2).subs(t, T)
    out("S1.6 V''(t*) + f(t*) tau^2/s^2: %s" % sp.simplify(d2 + f(T) * tau ** 2 / S ** 2))
    D = sp.symbols('Delta', positive=True)
    fe = lambda q: phi(q / sig) / sig
    err_pos = sp.integrate(fe(x), (x, -sp.oo, -D))      # Delta > 0: P(Delta + e <= 0)
    err_neg = sp.integrate(fe(x), (x, D, sp.oo))        # Delta = -D < 0: P(-D + e > 0)
    out("S1.7 error rate: P(D+e<=0) - Phi(-D/sd): %s ; P(-D+e>0) - Phi(-D/sd): %s"
        % (sp.simplify(err_pos - Phi(-D / sig)), sp.simplify(err_neg - Phi(-D / sig))))
    V0 = sp.integrate(x * phi((x - mu) / tau) / tau, (x, t, sp.oo))  # sigma_d = 0: V(t) = E[D 1{D > t}]
    out("S1.8 sigma_d = 0: dV/dt + t*phi((t-mu)/tau)/tau: %s  (dV/dt = -t f_D(t): unique max at t = 0 for every mu)"
        % sp.simplify(sp.diff(V0, t) + t * phi((t - mu) / tau) / tau))

    # --- T4 Prop. 6 scope paragraph (CRN kernel and shared-component model)
    # Delta ~ N(mu, tau^2), e | F ~ N(m_e, v), xi ~ N(0,1), mutually independent given F;
    # Dh = Delta - (1 - rho) e + sigma_c xi.
    w2 = sc ** 2 + (1 - rho) ** 2 * v
    mean_h = mu - (1 - rho) * me
    var_h = tau ** 2 + w2
    postm = mu + tau ** 2 / var_h * (h - mean_h)
    root = sp.solve(sp.Eq(postm, 0), h)[0]
    tss = -(1 - rho) * me - mu * w2 / tau ** 2
    out("S6.1 kernel: root of E[D|F,Dh] in Dh minus t** = -(1-rho)m_e - mu w^2/tau^2: %s" % sp.simplify(root - tss))
    sgm = sp.symbols('sigma_rec', positive=True)  # per-run sd sigma in T2 Prop. 4 / Cor. 9a
    w2u = w2.subs({sc: sgm * sp.sqrt(1 - rho ** 2), v: sgm ** 2})
    out("S6.2 unselected record (v = sigma^2, sigma_c^2 = sigma^2(1-rho^2)): w^2 - 2 sigma^2 (1-rho): %s"
        % sp.simplify(w2u - 2 * sgm ** 2 * (1 - rho)))
    sn2 = 2 * sgm ** 2 * (1 - rho)
    w2k = w2.subs(sc, sgm * sp.sqrt(1 - rho ** 2))
    out("S6.3 sigma_n^2 - w^2 - (1-rho)^2 (sigma^2 - v): %s  (so w <= sigma_n iff v <= sigma^2, for rho < 1)"
        % sp.simplify(sn2 - w2k - (1 - rho) ** 2 * (sgm ** 2 - v)))
    tsn = -mu * sn2 / tau ** 2
    out("S6.4 t** - t* - [-(1-rho) m_e + mu (1-rho)^2 (sigma^2 - v)/tau^2]: %s"
        % sp.simplify(tss.subs(sc, sgm * sp.sqrt(1 - rho ** 2)) - tsn
                      - (-(1 - rho) * me + mu * (1 - rho) ** 2 * (sgm ** 2 - v) / tau ** 2)))
    # shared component: Dh = Delta + v_new - v_rec, v_new ~ N(0,(1-rho)sigma^2) fresh, v_rec | F ~ N(m_v, V_v)
    mv, Vv = sp.symbols('m_v V_v', real=True)
    w2p = (1 - rho) * sgm ** 2 + Vv
    postm2 = mu + tau ** 2 / (tau ** 2 + w2p) * (h - (mu - mv))
    root2 = sp.solve(sp.Eq(postm2, 0), h)[0]
    out("S6.5 shared component: root minus t** = -m_v - mu w'^2/tau^2: %s ; w'^2 at V_v=(1-rho)sigma^2 minus sigma_n^2: %s"
        % (sp.simplify(root2 - (-mv - mu * w2p / tau ** 2)), sp.simplify(w2p.subs(Vv, (1 - rho) * sgm ** 2) - sn2)))
    # Kalman (conditionally Gaussian) update for the kernel record error, used in N6.4
    # e ~ N(m, v); eps = rho e + sigma_c xi; Dh = Delta - (1-rho) e + sigma_c xi.
    cov_eps_h = rho * (-(1 - rho)) * v + sc ** 2
    cov_e_h = -(1 - rho) * v
    out("S6.6 kernel Kalman moments: Cov(eps, Dh) = %s ; Cov(e, Dh) = %s ; Var(Dh) = %s"
        % (sp.expand(cov_eps_h), cov_e_h, sp.expand(var_h)))

    # --- T4 Prop. 7
    a_ = sp.symbols('tl', real=True)  # the comparison threshold t~
    # D(t~) := V(t*) - V(t~) - (tau^2/s^2) int_{t~}^{t*} f(u)(t* - u) du. D(t*) = 0 and, by the fundamental theorem
    # of calculus, dD/dt~ = -V'(t~) + (tau^2/s^2) f(t~)(t* - t~), which S1.5 makes zero; so D = 0 identically.
    dD = -sp.diff(Vs, t).subs(t, a_) + tau ** 2 / S ** 2 * f(a_) * (T - a_)
    out("S7.1 dD/dt~ for D(t~) = V(t*) - V(t~) - (tau^2/s^2) int_t~^t* f(u)(t* - u) du: %s ; D(t*) = 0 trivially" % sp.simplify(dD))
    anti = (T - mu) * Phi((u - mu) / S) + S * phi((u - mu) / S)  # antiderivative of f(u)(t* - u)
    out("S7.1b d/du[(t*-mu)Phi((u-mu)/s) + s phi((u-mu)/s)] - f(u)(t* - u): %s ; closed-form gap minus V(t*) - V(t~): %s"
        % (sp.simplify(sp.diff(anti, u) - f(u) * (T - u)),
           sp.simplify(tau ** 2 / S ** 2 * (anti.subs(u, T) - anti.subs(u, a_)) - (Vs.subs(t, T) - Vs.subs(t, a_)))))
    out("S7.2 int_tl^b (b - u) du (tl < b): %s ; max of f: %s"
        % (sp.factor(sp.integrate(sp.Symbol('b') - u, (u, a_, sp.Symbol('b')))), sp.simplify(f(mu))))
    out("S7.3 local form: -V''(t*)/2 - f(t*) tau^2/(2 s^2): %s"
        % sp.simplify(-sp.diff(Vs, t, 2).subs(t, T) / 2 - f(T) * tau ** 2 / (2 * S ** 2)))

    # --- T4 Cor. 9a and Prop. 9 helpers
    sigc = sp.symbols('sigma_c', positive=True)
    fx = lambda q: phi((q - m) / sigc) / sigc
    qq = sp.Symbol('q', real=True)
    num = sp.integrate(qq * fx(qq), (qq, c, sp.oo))
    den = sp.integrate(fx(qq), (qq, c, sp.oo))
    aa = (c - m) / sigc
    lam = phi(aa) / Phi(-aa)
    out("S9.1 truncated-normal mean E[X|X>c] - (m + sigma_c lambda((c-m)/sigma_c)): %s" % sp.simplify(num / den - (m + sigc * lam)))
    psi = phi(a) - a * Phi(-a)
    out("S9.2 psi(a) = phi(a) - a Phi(-a): psi'(a) + Phi(-a) = %s ; lim_{a->oo} psi = %s ; lambda(a) - a - psi(a)/Phi(-a) = %s"
        % (sp.simplify(sp.diff(psi, a) + Phi(-a)), sp.limit(psi, a, sp.oo),
           sp.simplify(phi(a) / Phi(-a) - a - psi / Phi(-a))))
    lama = phi(a) / Phi(-a)
    out("S9.3 lambda'(a) - lambda(a)(lambda(a) - a): %s  (lambda increasing since lambda > a)"
        % sp.simplify(sp.diff(lama, a) - lama * (lama - a)))
    # Cor. 9a substitution m = rho e, c = e - Delta
    e_, Dl = sp.symbols('e Delta', real=True)
    out("S9.4 Cor. 9a: (c - m)/sigma_c with m = rho e, c = e - Delta, minus ((1-rho)e - Delta)/sigma_c: %s"
        % sp.simplify(((e_ - Dl) - rho * e_) / sigc - ((1 - rho) * e_ - Dl) / sigc))
    # shared-component partial covariance (review, T4:122): u ~ (0, rho s^2), v_rec, v_j ~ (0,(1-rho)s^2)
    s2 = sp.symbols('s2', positive=True)
    cov_hu, cov_he, cov_ue, var_e = 0, -(1 - rho) * s2, rho * s2, s2
    out("S9.5 shared model: partial Cov(Dh_j, u | e) - rho(1-rho)sigma^2: %s"
        % sp.simplify(cov_hu - cov_he * cov_ue / var_e - rho * (1 - rho) * s2))

    # --- T4 Prop. 10(b)
    Xp = sp.integrate(x * phi((x - beta) / tau) / tau, (x, 0, sp.oo))
    out("S10.1 E[X^+], X ~ N(beta, tau^2), minus beta Phi(beta/tau) + tau phi(beta/tau): %s"
        % sp.simplify((Xp - (beta * Phi(beta / tau) + tau * phi(beta / tau))).rewrite(sp.erf)))
    G = beta * Phi(beta / tau) + tau * phi(beta / tau) - tau * phi(0)
    out("S10.2 G(beta,tau) = beta Phi(beta/tau) + tau phi(beta/tau) - tau phi(0): dG/dbeta - Phi(beta/tau) = %s ; G(0) = %s"
        % (sp.simplify(sp.diff(G, beta) - Phi(beta / tau)), sp.simplify(G.subs(beta, 0))))
    out("S10.3 G(2,1) to 20 digits: %s" % sp.N(G.subs({beta: 2, tau: 1}), 20))


# ================================================================ T2 Prop. 1 numerics
def n_prop1():
    out("== N1: T2 Proposition 1 ==")
    # N1.1 closed form vs independent quadrature E[Delta Phi((Delta - t)/sigma_d)] (integration over Delta)
    worst_abs, worst_rel, n = 0.0, 0.0, 0
    for _ in range(600):
        mu = rng.normal(0, 1) * 10 ** rng.uniform(-2, 1)
        tau = 10 ** rng.uniform(-2, 1)
        sd = 10 ** rng.uniform(-3, 1)
        s = np.hypot(tau, sd)
        t = tstar(mu, tau, sd) + s * rng.choice([rng.normal(0, 1), rng.normal(0, 4), 30.0, -30.0])
        # standardized variable x: Delta = mu + tau x; integrand has a kink/step at x0 = (t - mu)/tau
        g = lambda xx: (mu + tau * xx) * norm.cdf((mu + tau * xx - t) / sd) * norm.pdf(xx)
        x0 = (t - mu) / tau
        cand = {float(x0 + k * sd / tau) for k in (-10, -6, -3, -1, 0, 1, 3, 6, 10)}
        brk = sorted({-12.0, 12.0} | {p_ for p_ in cand if -12 < p_ < 12})
        q = 0.0
        for lo_, hi_ in zip(brk[:-1], brk[1:]):
            qq_, _ = integrate.quad(g, lo_, hi_, limit=500, epsabs=1e-15, epsrel=1e-12)
            q += qq_
        cf = V(t, mu, tau, sd)
        worst_abs = max(worst_abs, abs(q - cf))
        worst_rel = max(worst_rel, abs(q - cf) / max(abs(cf), 1e-300) if abs(cf) > 1e-12 else 0.0)
        n += 1
    out(f"N1.1 V closed form vs quadrature over Delta, {n} random sets (mu of both signs, tau in [1e-2,10], "
        f"sigma_d in [1e-3,10], t up to +-30 s from t*): max abs diff {worst_abs:.1e}, max rel diff (|V|>1e-12) {worst_rel:.1e}")
    # N1.2 t* is the unique maximiser (bounded optimiser + random comparison points)
    bad_opt, bad_cmp, n = 0, 0, 2000
    worst_loc = 0.0
    for _ in range(n):
        mu = rng.normal(0, 1) * 10 ** rng.uniform(-2, 1)
        tau = 10 ** rng.uniform(-2, 1)
        sd = 10 ** rng.uniform(-3, 1)
        s = np.hypot(tau, sd)
        ts = tstar(mu, tau, sd)
        if abs(ts - mu) > 3 * s:  # optimiser unreliable where V is flat to machine precision
            continue
        r = optimize.minimize_scalar(lambda tt: -V(tt, mu, tau, sd) / s, bounds=(ts - 6 * s, ts + 6 * s),
                                     method='bounded', options={'xatol': 1e-10 * s})
        worst_loc = max(worst_loc, abs(r.x - ts) / s)
        if abs(r.x - ts) / s > 1e-4:
            bad_opt += 1
        tt = ts + s * rng.normal(0, 3, 200)
        if np.any(V(tt, mu, tau, sd) > V(ts, mu, tau, sd) + 1e-15 * (abs(mu) + tau)):
            bad_cmp += 1
    out(f"N1.2 argmax: bounded optimiser |t_opt - t*|/s max {worst_loc:.1e} (failures >1e-4: {bad_opt}); "
        f"sets where one of 200 random t beats V(t*): {bad_cmp}")
    # N1.3 sign of dV/dt by central differences
    bad = 0
    for _ in range(1000):
        mu, tau, sd = rng.normal(0, 1), 10 ** rng.uniform(-1, 0.5), 10 ** rng.uniform(-1, 0.5)
        s, ts = np.hypot(tau, sd), tstar(mu, tau, sd)
        if abs(ts - mu) > 3 * s:
            continue
        for k in (0.05, 0.3, 1.0):
            hh = 1e-6 * s
            dl = (V(ts - k * s + hh, mu, tau, sd) - V(ts - k * s - hh, mu, tau, sd))
            dr = (V(ts + k * s + hh, mu, tau, sd) - V(ts + k * s - hh, mu, tau, sd))
            if not (dl > 0 and dr < 0):
                bad += 1
    out(f"N1.3 finite-difference sign of dV/dt (+ below t*, - above, at 0.05, 0.3, 1 s): violations {bad}")
    # N1.4 edge sigma_d = 0
    res = []
    for mu in (-2.0, -0.5, 0.0, 0.5, 2.0):
        grid = np.linspace(-3, 3, 60001)
        res.append(f"mu={mu:+.1f}: argmax t={grid[np.argmax(V(grid, mu, 1.0, 0.0))]:+.4f}")
    out("N1.4 sigma_d = 0, tau = 1 (T2 says 'every t <= 0 is optimal'): " + "; ".join(res)
        + f"; V(0)-V(-0.5) at mu=0: {V(0,0,1,0)-V(-0.5,0,1,0):.5f} > 0")
    # N1.5 edge tau -> 0: V(t*) -> mu^+ (known-mean rule); sigma_d -> 0: V(t*) -> E[Delta^+]
    vals = []
    for mu in (-0.5, 0.5):
        for tau in (1e-1, 1e-3, 1e-6):
            vals.append(f"mu={mu:+.1f},tau={tau:.0e}: {V(tstar(mu, tau, 1.0), mu, tau, 1.0):+.6f}")
    out("N1.5 tau -> 0 with sigma_d = 1: V(t*) = " + "; ".join(vals) + " (limit mu^+)")
    vals = []
    for sd in (1e-1, 1e-3, 1e-6):
        mu, tau = -0.3, 0.7
        lim = mu * norm.cdf(mu / tau) + tau * norm.pdf(mu / tau)
        vals.append(f"sd={sd:.0e}: t*={tstar(mu,tau,sd):+.2e}, V(t*)-E[D^+]={V(tstar(mu,tau,sd),mu,tau,sd)-lim:+.1e}")
    out("N1.6 sigma_d -> 0 (mu=-0.3, tau=0.7; equivalently rho -> 1 in sigma_d^2 = 2 sigma^2 (1-rho)): " + "; ".join(vals))
    mu, tau, sd = -0.4, 0.7, 1.1
    s = np.hypot(tau, sd)
    out(f"N1.7 extreme thresholds (mu=-0.4): V(t*-40s) = {V(tstar(mu,tau,sd)-40*s,mu,tau,sd):+.6f} (-> mu), "
        f"V(t*+40s) = {V(tstar(mu,tau,sd)+40*s,mu,tau,sd):+.1e} (-> 0)")
    # N1.8 error rate incl. Delta = 0 convention, MC
    sd, M = 0.8, 4_000_000
    e = rng.normal(0, sd, M)
    parts = []
    for d in (-0.5, 0.0, 0.2, 1.0):
        sim = np.mean(d + e > 0) if d <= 0 else np.mean(d + e <= 0)
        parts.append(f"Delta={d:+.1f}: Phi(-|D|/sd)={norm.cdf(-abs(d)/sd):.5f}, sim={sim:.5f}")
    out(f"N1.8 error rate under rho (error = keep if Delta<=0, discard if Delta>0), 4e6 draws, s.e.<=0.00025: " + "; ".join(parts))
    # N1.9 measurable-rule optimality: Bayes rule vs non-threshold rules on common draws
    mu, tau, sd, M = -0.3, 0.8, 0.9, 2_000_000
    d = rng.normal(mu, tau, M)
    hh = d + rng.normal(0, sd, M)
    ts = tstar(mu, tau, sd)
    bayes = d * (hh > ts)
    rules = {"two intervals": (hh > ts) & ~((hh > ts + 0.5) & (hh < ts + 1.0)),
             "random 50% above t*": (hh > ts) & (rng.random(M) < 0.5) | (hh > ts + 1),
             "keep |Dh| > 1": np.abs(hh) > 1}
    parts = []
    for k, r in rules.items():
        diff = bayes - d * r
        parts.append(f"{k}: {diff.mean():+.5f} (s.e. {diff.std()/np.sqrt(M):.5f})")
    out("N1.9 E[D k_Bayes] - E[D k] for non-threshold rules (common draws): " + "; ".join(parts))


# ================================================================ T4 Prop. 6 numerics
def n_prop6():
    out("== N6: T4 Proposition 6 and its scope paragraph ==")
    M = 3_000_000
    sets = [(0.4, -0.3, 0.6, 0.8), (0.2, 0.3, 0.8, 0.6), (0.0, -1.0, 1.5, 0.3), (0.7, 0.1, 0.9, 0.0)]
    for (pi, mu, tau, sd) in sets:
        noop = rng.random(M) < pi
        d = np.where(noop, 0.0, rng.normal(mu, tau, M))
        eta = rng.normal(0, max(sd, 1e-300), M) if sd > 0 else np.zeros(M)
        h_bit = np.where(noop, 0.0, d + eta)            # bit-exact: Dh = 0 on a no-op
        h_nb = np.where(noop, rng.normal(0, 1.0, M), d + eta)  # non-bit-exact: arbitrary law on a no-op
        ts = tstar(mu, tau, sd)
        grid = ts + np.linspace(-1.5, 1.5, 61) * np.hypot(tau, sd)
        best_bit = grid[np.argmax([np.mean(d * (h_bit > g)) for g in grid])]
        best_nb = grid[np.argmax([np.mean(d * (h_nb > g)) for g in grid])]
        val_cf = (1 - pi) * V(ts, mu, tau, sd)
        vb, vn = d * (h_bit > ts), d * (h_nb > ts)
        out(f"N6.1 pi={pi}, mu={mu:+.1f}, tau={tau}, sigma={sd}: t*={ts:+.4f}; grid-best (step 0.05 s) bit-exact {best_bit:+.4f}, "
            f"non-bit-exact {best_nb:+.4f}; (1-pi)V(t*)={val_cf:.5f}, sim bit-exact {vb.mean():.5f}, non-bit-exact {vn.mean():.5f} "
            f"(s.e. {vb.std()/np.sqrt(M):.5f})")
    # N6.2 direction claims of the scope paragraph, kernel form (pure algebra, random stress)
    K = 1_000_000
    sgm = 10 ** rng.uniform(-3, 0, K)
    rho = rng.uniform(0, 0.999, K)
    tau = 10 ** rng.uniform(-3, 0, K)
    mu = rng.normal(0, 1, K) * tau * 3
    me = rng.normal(0, 1, K) * sgm * 2
    v = sgm ** 2 * 10 ** rng.uniform(-3, 0.7, K)
    sc2 = sgm ** 2 * (1 - rho ** 2)
    w2 = sc2 + (1 - rho) ** 2 * v
    sn2 = 2 * sgm ** 2 * (1 - rho)
    tss = -(1 - rho) * me - mu * w2 / tau ** 2
    ts = -mu * sn2 / tau ** 2
    cond = (me >= 0) & (mu <= 0) & (v <= sgm ** 2)
    tol = 1e-12 * (np.abs(ts) + np.abs(tss) + sgm)
    out(f"N6.2 scope (kernel): sets meeting E[e|F]>=0, mu<=0, Var(e|F)<=sigma^2: {cond.sum()}; t** > t* among them: "
        f"{np.sum(cond & (tss > ts + tol))}")
    for name, cnd in [("E[e|F] < 0 (mu<=0, Var<=s^2)", (me < 0) & (mu <= 0) & (v <= sgm ** 2)),
                      ("Var(e|F) > s^2 (E>=0, mu<0)", (me >= 0) & (mu < 0) & (v > sgm ** 2)),
                      ("mu > 0 (E>=0, Var<=s^2)", (me >= 0) & (mu > 0) & (v <= sgm ** 2))]:
        out(f"N6.2 dropping one condition, {name}: share with t** > t*: {np.mean(tss[cnd] > ts[cnd]):.3f} of {cnd.sum()}")
    # shared-component form
    mv = rng.normal(0, 1, K) * sgm
    Vv = (1 - rho) * sgm ** 2 * 10 ** rng.uniform(-3, 0.7, K)
    w2p = (1 - rho) * sgm ** 2 + Vv
    tss2 = -mv - mu * w2p / tau ** 2
    cond2 = (mv >= 0) & (mu <= 0) & (Vv <= (1 - rho) * sgm ** 2)
    out(f"N6.3 scope (shared component): sets meeting the three conditions: {cond2.sum()}; t** > t* among them: "
        f"{np.sum(cond2 & (tss2 > ts + tol))}")


def kalman_campaigns(model, M=1_000_000, N=4, sgm=0.0125, rho=0.82, tau=0.009):
    """Campaigns under the kernel ('kernel') or shared-component ('shared') record-error model.
    The policy keeps iff Dh > t** with the Kalman moments of the latent record error (kernel: e; shared: v_rec).
    The proposal mean mu_n depends on the last recorded comparison (a ledger-reading proposer)."""
    sc = sgm * np.sqrt(1 - rho ** 2)
    sv2 = (1 - rho) * sgm ** 2
    sd2 = 2 * sgm ** 2 * (1 - rho)
    if model == "kernel":
        lat = rng.normal(0, sgm, M)        # e (record error), unselected
        m, v = np.zeros(M), np.full(M, sgm ** 2)
    else:
        lat = rng.normal(0, np.sqrt(sv2), M)  # v_rec (fresh component of the record), unselected; u cancels
        m, v = np.zeros(M), np.full(M, sv2)
    last_h = np.zeros(M)
    pattern = np.zeros(M, dtype=int)
    for n in range(N):
        mu = -0.004 + 0.5 * np.clip(last_h, -0.01, 0.01)
        if n == N - 1:
            z = (lat - m) / np.sqrt(v)
            raw = lat.copy()
            stash = (mu.copy(), m.copy(), v.copy())
        d = rng.normal(mu, tau, M)
        xi = rng.normal(0, 1, M)
        if model == "kernel":
            eps = rho * lat + sc * xi
            hh = d + eps - lat
            w2 = sc ** 2 + (1 - rho) ** 2 * v
            tss = -(1 - rho) * m - mu * w2 / tau ** 2
            mean_h = mu - (1 - rho) * m
            var_h = tau ** 2 + w2
            c_eps = -rho * (1 - rho) * v + sc ** 2
            c_lat = -(1 - rho) * v
            m_keep = rho * m + c_eps / var_h * (hh - mean_h)
            v_keep = rho ** 2 * v + sc ** 2 - c_eps ** 2 / var_h
            new = eps
        else:
            vnew = rng.normal(0, np.sqrt(sv2), M)
            hh = d + vnew - lat
            w2 = sv2 + v
            tss = -m - mu * w2 / tau ** 2
            mean_h = mu - m
            var_h = tau ** 2 + w2
            c_new, c_lat = sv2, -v
            m_keep = c_new / var_h * (hh - mean_h)
            v_keep = sv2 - c_new ** 2 / var_h
            new = vnew
        if n == N - 1:
            return dict(z=z, raw=raw, pattern=pattern, d=d, h=hh, tss=tss, mu=stash[0],
                        tplain=-stash[0] * sd2 / tau ** 2, sd=np.sqrt(sd2))
        keep = hh > tss
        m_disc = m + c_lat / var_h * (hh - mean_h)
        v_disc = v - c_lat ** 2 / var_h
        m = np.where(keep, m_keep, m_disc)
        v = np.where(keep, v_keep, v_disc)
        lat = np.where(keep, new, lat)
        last_h = hh
        pattern = pattern * 2 + keep


def n_kalman():
    out("== N6.4: (new, AI analysis) the posterior of the record error given the full ledger is Gaussian ==")
    for model in ("kernel", "shared"):
        r = kalman_campaigns(model, M=600_000, tau=0.003)
        z, pat = r["z"], r["pattern"]
        mx_m = mx_s = mx_k = 0.0
        min_p = 1.0
        for p in range(8):
            sel = pat == p
            if sel.sum() < 2000:
                continue
            mm, sd, sk, ku = skew_kurt(z[sel])
            mx_m, mx_s, mx_k = max(mx_m, abs(mm) / (1 / np.sqrt(sel.sum()))), max(mx_s, abs(sk)), max(mx_k, abs(ku))
            min_p = min(min_p, stats.kstest(z[sel][:200000], 'norm').pvalue)
        out(f"N6.4s [{model}] stress tau=0.003 (strong selection; 6e5 campaigns): over keep patterns with >=2000 rows, "
            f"max |mean|/s.e. {mx_m:.2f}, max |skew| {mx_s:.3f}, max |excess kurt| {mx_k:.3f}, min KS p {min_p:.3f}")
    for model in ("kernel", "shared"):
        r = kalman_campaigns(model)
        z, raw, pat = r["z"], r["raw"], r["pattern"]
        out(f"N6.4 [{model}] standardized record error (e - E[e|F_4])/sd(e|F_4) at trial 4, by keep pattern of trials 1-3 "
            f"(count | mean, sd, skew, excess kurt | KS p on <=2e5 | skew of the raw record error):")
        for p in range(8):
            sel = pat == p
            if sel.sum() < 2000:
                continue
            mm, sd, sk, ku = skew_kurt(z[sel])
            ks = stats.kstest(z[sel][:200000], 'norm').pvalue
            out(f"N6.4 [{model}]   pattern {p:03b}: {sel.sum():7d} | {mm:+.4f} {sd:.4f} {sk:+.4f} {ku:+.4f} | {ks:.3f} | {skew_kurt(raw[sel])[2]:+.3f}")
        # location of the Bayes threshold: E[Delta | Dh near threshold] over all histories
        d, hh, tss, tpl, sdd = r["d"], r["h"], r["tss"], r["tplain"], r["sd"]
        band = 0.03 * sdd
        for nm, th in (("t** (Kalman moments)", tss), ("t* (Prop. 6, measured sigma_d)", tpl)):
            sel = np.abs(hh - th) < band
            out(f"N6.4 [{model}] mean of Delta_4 over |Dh_4 - threshold| < 0.03 sigma_d, threshold {nm}: "
                f"{d[sel].mean()*1e3:+.4f}e-3 (s.e. {d[sel].std()/np.sqrt(sel.sum())*1e3:.4f}e-3, n={sel.sum()})")
        vals = []
        base = d * (hh > tss)
        for cshift in (-0.3, -0.1, 0.1, 0.3):
            diff = base - d * (hh > tss + cshift * sdd)
            vals.append(f"shift {cshift:+.1f} sd: {diff.mean()*1e6:+.3f} (s.e. {diff.std()/np.sqrt(len(d))*1e6:.3f})")
        diff = base - d * (hh > tpl)
        vals.append(f"plain t*: {diff.mean()*1e6:+.3f} (s.e. {diff.std()/np.sqrt(len(d))*1e6:.3f})")
        out(f"N6.4 [{model}] value at trial 4, (t** rule) - (other rule), units 1e-6: " + "; ".join(vals))


# ================================================================ T4 Prop. 7 numerics
def n_prop7():
    out("== N7: T4 Proposition 7 and Corollary 7a ==")
    worst, lf, uf, minend, n = 0.0, 0, 0, 0, 0
    worst_abs7 = 0.0
    for _ in range(3000):
        mu = rng.normal(0, 1) * 10 ** rng.uniform(-1, 0.7)
        tau = 10 ** rng.uniform(-1.5, 0.7)
        sd = 10 ** rng.uniform(-2, 0.7)
        s = np.hypot(tau, sd)
        ts = tstar(mu, tau, sd)
        if abs(ts - mu) > 10 * s:
            continue
        tt = ts + s * rng.choice([rng.normal(0, 0.3), rng.normal(0, 3), 15.0, -15.0])
        gap = V(ts, mu, tau, sd) - V(tt, mu, tau, sd)
        f = lambda q: norm.pdf(q, mu, s)
        integ, _ = integrate.quad(lambda q: f(q) * (ts - q), tt, ts, epsabs=1e-15, epsrel=1e-12, limit=400)
        ident = tau ** 2 / s ** 2 * integ
        worst = max(worst, abs(gap - ident) / gap if gap > 1e-8 else 0.0)
        worst_abs7 = max(worst_abs7, abs(gap - ident))
        lo_pt, hi_pt = min(ts, tt), max(ts, tt)
        grid = np.linspace(lo_pt, hi_pt, 2001)
        fmin_grid = f(grid).min()
        fmin_end = min(f(ts), f(tt))
        if fmin_grid < fmin_end * (1 - 1e-12):
            minend += 1
        lower = tau ** 2 / (2 * s ** 2) * fmin_end * (ts - tt) ** 2
        upper = tau ** 2 * (ts - tt) ** 2 / (2 * np.sqrt(2 * np.pi) * s ** 3)
        if gap < lower * (1 - 1e-9) - 1e-15:
            lf += 1
        if gap > upper * (1 + 1e-9) + 1e-15:
            uf += 1
        n += 1
    out(f"N7.1 {n} random sets (t~ up to +-15 s from t*): identity max rel diff (gap > 1e-8) {worst:.1e}, max abs diff {worst_abs7:.1e}; lower-bound failures {lf}; "
        f"upper-bound failures {uf}; sets where min f on the interval is not at an endpoint: {minend}")
    # N7.2 local form: ratio approx/gap -> 1
    mu, tau, sd = -0.4, 0.7, 1.1
    s, ts = np.hypot(tau, sd), tstar(mu, tau, sd)
    parts = []
    for hfrac in (1.0, 0.1, 0.01, 0.001):
        for sign in (+1, -1):
            tt = ts + sign * hfrac * s
            gap = V(ts, mu, tau, sd) - V(tt, mu, tau, sd)
            approx = tau ** 2 * norm.pdf(ts, mu, s) * (ts - tt) ** 2 / (2 * s ** 2)
            parts.append(f"{sign*hfrac:+g}s: {approx/gap:.6f}")
    out("N7.2 local form, ratio (approximation / exact gap) at t~ - t* = " + "; ".join(parts) + " (relative error O(|t~ - t*|/s))")
    # N7.3 Cor. 7a under (NF) with (NI) failing: shared latent theta, keep-free execution rule
    M, N = 2_000_000, 5
    mu0 = np.array([-0.3, 0.1, -0.5, 0.0, -0.2])
    b = np.array([0.5, 1.0, -0.7, 1.2, 0.8])
    cc = np.array([0.5, 0.3, 0.6, 0.4, 0.5])
    sg = np.array([0.8, 0.5, 1.0, 0.7, 0.6])
    theta = rng.normal(0, 1, M)
    mpost, vpost = np.zeros(M), np.ones(M)
    gain_sim = np.zeros(M)
    gain_pred = np.zeros(M)
    gain_sim2 = np.zeros(M)
    gain_pred2 = np.zeros(M)
    H1 = np.zeros(M)
    for n in range(N):
        a = np.ones(M, dtype=bool) if n != 2 else (H1 > 0)   # execution reads a past result, never a keep decision
        dlt = mu0[n] + b[n] * theta + cc[n] * rng.normal(0, 1, M)
        Hn = dlt + sg[n] * rng.normal(0, 1, M)
        mun = mu0[n] + b[n] * mpost
        taun = np.sqrt(b[n] ** 2 * vpost + cc[n] ** 2)
        tsn = tstar(mun, taun, sg[n])
        ttil = np.zeros(M)                       # default rule
        ttil2 = 0.3 * H1 if n > 0 else np.zeros(M)  # another O_n-measurable threshold
        gain_sim += a * dlt * ((Hn > tsn).astype(float) - (Hn > ttil))
        gain_pred += a * (V(tsn, mun, taun, sg[n]) - V(ttil, mun, taun, sg[n]))
        gain_sim2 += a * dlt * ((Hn > tsn).astype(float) - (Hn > ttil2))
        gain_pred2 += a * (V(tsn, mun, taun, sg[n]) - V(ttil2, mun, taun, sg[n]))
        # Kalman update of theta on executed trials: Hn - mu0 = b theta + noise (var cc^2 + sg^2)
        nv = cc[n] ** 2 + sg[n] ** 2
        k = vpost * b[n] / (b[n] ** 2 * vpost + nv)
        mpost = np.where(a, mpost + k * (Hn - mu0[n] - b[n] * mpost), mpost)
        vpost = np.where(a, vpost - k * b[n] * vpost, vpost)
        if n == 0:
            H1 = Hn
    for nm, gs, gp in (("t~ = 0", gain_sim, gain_pred), ("t~ = 0.3 H_1", gain_sim2, gain_pred2)):
        dd = gs - gp
        out(f"N7.3 Cor. 7a, (NF) holds, (NI) fails (shared theta), 5 trials, 2e6 campaigns, {nm}: simulated gain {gs.mean():.5f}, "
            f"E[sum a_n gap_n] {gp.mean():.5f}, difference {dd.mean():+.5f} (s.e. {dd.std()/np.sqrt(M):.5f})")


# ================================================================ T4 Prop. 9 numerics
def n_prop9():
    out("== N9: T4 Proposition 9 (kernel-free) and Corollary 9a ==")

    def laws(e, d):
        """Non-Gaussian conditional laws of eps given G = (e, Delta), parameters nonlinear in (e, Delta)."""
        return [
            ("student-t3", stats.t(3, loc=0.6 * e + 0.3 * d ** 2, scale=0.7)),
            ("skewnorm", stats.skewnorm(5, loc=np.sin(e) - d, scale=1.0)),
            ("lognormal", stats.lognorm(0.8, loc=-1 + e / 2, scale=1.0)),
            ("uniform", stats.uniform(loc=e - 1.5, scale=2.0 + abs(d))),
            ("gauss-mix", None),
            ("discrete", None),
        ]

    def moments(name, dist, e, d, c):
        """p = P(eps > c), E[eps | eps > c], E[eps]; by quadrature (continuous) or exact sums (discrete)."""
        if name == "gauss-mix":
            ws, ms, ss = np.array([0.7, 0.3]), np.array([e - 1.0, e + 2.0 * np.tanh(d)]), np.array([0.5, 1.5])
            p = np.sum(ws * norm.sf((c - ms) / ss))
            num = np.sum(ws * (ms * norm.sf((c - ms) / ss) + ss * norm.pdf((c - ms) / ss)))
            return p, (num / p if p > 0 else np.nan), np.sum(ws * ms)
        if name == "discrete":
            xs = np.array([-2.0, 0.0, 1.0, 3.0]) + 0.5 * e
            ps = np.array([0.2, 0.3 + 0.1 * np.tanh(d), 0.3 - 0.1 * np.tanh(d), 0.2])
            k = xs > c
            p = ps[k].sum()
            return p, ((xs[k] * ps[k]).sum() / p if p > 0 else np.nan), (xs * ps).sum()
        p = dist.sf(c)
        if p <= 0:
            return 0.0, np.nan, dist.mean()
        num = dist.expect(lambda q: q, lb=c, conditional=False)
        return p, num / p, dist.mean()

    n1 = n2 = n3 = 0
    v1 = v2 = v3 = 0
    m1 = m2 = m3 = np.inf
    for e in (-2.0, -0.5, 0.0, 0.3, 1.5, 4.0):
        for d in (-1.0, 0.0, 0.2, 2.0):
            for t in (0.0, -0.5, 0.4):
                c = e - d + t
                for name, dist in laws(e, d):
                    p, ek, emean = moments(name, dist, e, d, c)
                    if p > 1e-12:
                        n1 += 1
                        m1 = min(m1, ek - c)
                        v1 += ek - c <= -1e-10
                    if 1e-12 < p < 1 - 1e-12:
                        n2 += 1
                        m2 = min(m2, ek - emean)
                        v2 += ek - emean <= -1e-10
                        # (iii): recentre the law so that E[eps | G] = 0: eps0 = eps - emean, K0 = {eps > c + emean}
                        p0, ekc, _ = moments(name, dist, e, d, c + emean)
                        if 1e-12 < p0 < 1 - 1e-12:
                            ek0 = ekc - emean
                            n3 += 1
                            m3 = min(m3, ek0)
                            v3 += ek0 <= -1e-10
    out(f"N9.1 discrete G (6 e x 4 Delta x 3 thresholds t, both signs), 6 non-Gaussian laws of eps | G, exact quadrature/sums:")
    out(f"N9.1   (ii.1) E[e'|K,G] > e - Delta + t on p_G > 0: {n1} cells, violations {v1}, min margin {m1:.2e}")
    out(f"N9.1   (ii.2) E[e'|K,G] > E[eps|G] on 0 < p_G < 1: {n2} cells, violations {v2}, min margin {m2:.2e}")
    out(f"N9.1   (iii)  E[e'|K,G] > 0 when E[eps|G] = 0, on 0 < p_G < 1: {n3} cells, violations {v3}, min margin {m3:.2e}")
    # N9.2 necessity of p_G < 1 in (ii.2)
    c = 0.7
    dist = stats.uniform(loc=c + 1, scale=1)
    out(f"N9.2 p_G = 1 (eps ~ U(c+1, c+2)): E[e'|K,G] - E[eps|G] = {dist.mean() - dist.expect(lambda q: q, lb=c):+.1e} "
        f"(equality, so the strict (ii.2) needs p_G < 1)")
    # N9.3 (iv) with coarse G' and an adaptive proposer that reads the displayed record B
    M = 4_000_000
    J = rng.normal(0, 1, M)
    e = 0.8 * rng.standard_t(4, M) + 0.3
    B = J + e
    d = 0.5 * np.tanh(B) + 0.6 * rng.standard_t(5, M)
    eps = 0.4 * e + stats.skewnorm.rvs(-4, loc=0.5, scale=0.9, size=M, random_state=rng)
    K = d + eps - e > 0
    qs = np.quantile(B, np.linspace(0, 1, 11))
    bins = np.clip(np.searchsorted(qs, B, side='right') - 1, 0, 9)
    worst = np.inf
    for k in range(10):
        sel = K & (bins == k)
        diff = eps[sel] - (e[sel] - d[sel])
        worst = min(worst, diff.mean() / (diff.std() / np.sqrt(sel.sum())))
    diff = eps[K] - (e[K] - d[K])
    out(f"N9.3 (iv), G' = sigma(decile of B) and G' trivial, heavy-tailed skewed errors, proposer reads B: min over deciles of "
        f"(E[e'|K,G'] - E[e - Delta|K,G'])/s.e. = {worst:.0f}; trivial G': {diff.mean():+.4f} (s.e. {diff.std()/np.sqrt(K.sum()):.4f})")
    # review's example: without '| K' on the right, (iv) would be false
    pK = 0.5 * 0.5 + 0.5 * norm.sf(10)
    eK = (0.5 * norm.pdf(0) + 0.5 * norm.pdf(10)) / pK
    rhs_cond = (0.5 * 10 * norm.sf(10)) / pK
    out(f"N9.3 review example e in {{0,10}}, eps~N(0,1), null: E[e'|K] = {eK:.4f} < E[e] = 5, but > E[e - Delta | K] = {rhs_cond:.1e}")
    # N9.4 Cor. 9a: formula vs high-precision quadrature (mpmath, independent of the closed form) and the inequality
    # margins sigma_c*lambda(a) (over rho e) and sigma_c*(lambda(a) - a) (over e - Delta), evaluated at 40 digits.
    mpmath.mp.dps = 40
    worst_rel, nv, n, minlog = 0.0, 0, 0, np.inf
    for rho in (0.0, 0.3, 0.82, 0.99, 0.999):
        for e0 in (-1.5, -0.2, 0.0, 0.9, 2.5):
            for D0 in (-0.8, 0.0, 0.4, 3.0):
                sc = mpmath.sqrt(1 - mpmath.mpf(rho) ** 2)
                m, c = mpmath.mpf(rho) * e0, mpmath.mpf(e0) - D0
                a = ((1 - mpmath.mpf(rho)) * e0 - D0) / sc
                lam = mpmath.npdf(a) / mpmath.ncdf(-a)
                formula = m + sc * lam
                # E[X | X > c] = c + sc * int_0^oo y phi(a+y) dy / int_0^oo phi(a+y) dy  (y = (X - c)/sc)
                pk = max(mpmath.mpf(0), -a)  # mode of phi(a + y) on y >= 0
                sca = 1 / (1 + abs(a))  # decay scale of phi(a + y) for large a
                pts = sorted(set([mpmath.mpf(0), pk, pk + sca, pk + 5 * sca, pk + 1, pk + 10])) + [mpmath.inf]
                num = mpmath.quad(lambda y: y * mpmath.npdf(a + y), pts)
                den = mpmath.quad(lambda y: mpmath.npdf(a + y), pts)
                quad = c + sc * num / den
                worst_rel = max(worst_rel, float(abs(quad - formula) / max(abs(formula), mpmath.mpf('1e-30'))))
                marg = min(sc * lam, sc * (lam - a))
                nv += marg <= 0
                minlog = min(minlog, float(mpmath.log10(marg)))
                n += 1
    out(f"N9.4 Cor. 9a formula vs 40-digit quadrature, {n} sets (rho up to 0.999, e and Delta of both signs, P(keep) from "
        f"~1e-72 to ~1): max rel diff {worst_rel:.1e}; inequality margins <= 0: {nv}; smallest margin 10^{minlog:.1f}")
    parts = []
    for (e0, D0, rho) in ((0.5, 0.0, 0.3), (-0.8, -0.2, 0.6), (1.0, 0.0, 0.99), (0.0, 1.5, 0.0)):
        sc = np.sqrt(1 - rho ** 2)
        epsd = rho * e0 + sc * rng.normal(0, 1, 4_000_000)
        k = epsd > e0 - D0
        parts.append(f"e={e0:+.1f},D={D0:+.1f},rho={rho}: {rho*e0+sc*mills(((1-rho)*e0-D0)/sc):+.5f} vs {epsd[k].mean():+.5f} "
                     f"(s.e. {epsd[k].std()/np.sqrt(k.sum()):.5f})")
    out("N9.4 Cor. 9a formula vs simulation (4e6): " + "; ".join(parts))
    # N9.5 shared component, record kept once by a null keep: semi-analytic E[u | e] and the review's M2 example
    rho, s = 0.5, 1.0
    su, sv = np.sqrt(rho) * s, np.sqrt(1 - rho) * s
    fM = lambda q: 2 * norm.pdf(q, 0, sv) * norm.cdf(q, 0, sv)  # law of v1 given v1 > v0 (= max of two)
    parts = []
    for e0 in (-0.9, 0.0, 0.9, 1.9):
        w = lambda q: norm.pdf(e0 - q, 0, su) * fM(q)
        num, _ = integrate.quad(lambda q: (e0 - q) * w(q), -12, 12, limit=400)
        den, _ = integrate.quad(w, -12, 12, limit=400)
        parts.append(f"e={e0:+.1f}: {num/den:+.4f}")
    out("N9.5 shared model, rho=0.5: mean of a fresh error given a record kept once (quadrature; packet MC: -0.7781, -0.2314, "
        "+0.3060, +0.8758): " + "; ".join(parts))
    e0, D0 = 0.0, 3.0
    w = lambda q: norm.pdf(e0 - q, 0, su) * fM(q)
    PK = lambda q: norm.sf((q - D0) / sv)
    num, _ = integrate.quad(lambda q: w(q) * ((e0 - q) * PK(q) + sv * norm.pdf((q - D0) / sv)), -12, 12, limit=400)
    den, _ = integrate.quad(lambda q: w(q) * PK(q), -12, 12, limit=400)
    den0, _ = integrate.quad(w, -12, 12, limit=400)
    out(f"N9.5 review M2 example (shared, kept once, e=0, Delta=3): P(keep|e,Delta) = {den/den0:.4f}, E[e'|keep,e,Delta] = "
        f"{num/den:+.4f} (review MC: 0.9995, -0.229): a zero-mean candidate error is needed in (iii)'s reading")


# ================================================================ T4 Prop. 10(b) numerics
def n_prop10b():
    out("== N10: T4 Proposition 10(b) ==")
    mpmath.mp.dps = 30
    G = lambda b, t: b * mpmath.ncdf(b / t) + t * mpmath.npdf(b / t) - t * mpmath.npdf(0)
    out(f"N10.1 G(2,1) = 2 Phi(2) + phi(2) - phi(0) = {mpmath.nstr(G(2, 1), 12)}")
    M = 4_000_000
    zz = rng.normal(0, 1, M)
    keep_branch = np.maximum(2 + zz, 0)
    disc_branch = np.maximum(zz, 0)
    dd = keep_branch - disc_branch
    out(f"N10.2 simulation (common random numbers, 4e6, own seed): E[(2+Z)^+] - E[Z^+] = {dd.mean():.5f} (s.e. {dd.std()/np.sqrt(M):.5f})")
    parts = [f"beta={b:g}: G={float(G(b,1)):.5f}, loss at alpha=1: {max(float(G(b,1))-1,0):.5f}" for b in (0.25, 0.5, 1, 2, 5, 10, 100)]
    out("N10.3 tau=1, optimality gap (G - alpha)^+: " + "; ".join(parts))
    tau, sgm = 1.0, 0.5
    s = np.hypot(tau, sgm)
    parts = []
    for b in (2, 10, 100):
        Gs = V(tstar(b, tau, sgm), b, tau, sgm) - V(0.0, 0.0, tau, sgm)
        parts.append(f"beta={b}: G_sigma={Gs:.5f} (>= beta - tau^2 phi(0)/s = {b - tau**2*norm.pdf(0)/s:.5f})")
    dk = rng.normal(2, tau, M)
    hk = dk + rng.normal(0, sgm, M)
    d0 = rng.normal(0, tau, M)
    h0 = d0 + rng.normal(0, sgm, M)
    sim = np.mean(dk * (hk > tstar(2, tau, sgm))) - np.mean(d0 * (h0 > 0))
    out(f"N10.4 noisy version sigma=0.5 at trial 2 (keep-branch value - myopic, before -alpha): " + "; ".join(parts)
        + f"; simulation at beta=2: {sim:.5f} (s.e. ~{np.sqrt(2)*tau/np.sqrt(M):.4f})")


# ================================================================ second session (23 Nov): added checks
# Own generator, run after everything above, so that every earlier output line is unchanged.
rng2 = np.random.default_rng(SEED + 1)


def x_symbolic():
    out("== XS: added symbolic checks (second session) ==")
    rho = sp.symbols('rho', positive=True)
    sg2, v, tau2 = sp.symbols('sigma2 v tau2', positive=True)
    # kernel Kalman step (sigma_c^2 = sigma^2 (1 - rho^2)): e | F ~ N(m, v); eps = rho e + sigma_c xi; h = D - (1-rho) e + sigma_c xi
    sc2k = sg2 * (1 - rho ** 2)
    var_h = tau2 + sc2k + (1 - rho) ** 2 * v
    c_eps = -rho * (1 - rho) * v + sc2k
    c_lat = -(1 - rho) * v
    v_keep = rho ** 2 * v + sc2k - c_eps ** 2 / var_h
    v_disc = v - c_lat ** 2 / var_h
    out("XS1 kernel Kalman step: sigma^2 - v_keep - [rho^2 (sigma^2 - v) + Cov(eps,Dh)^2/Var(Dh)] = %s ; "
        "v - v_disc - Cov(e,Dh)^2/Var(Dh) = %s ; Cov(eps,Dh) - (1-rho)(sigma^2 (1+rho) - rho v) = %s "
        "(so v <= sigma^2 is preserved by keeps and discards, and Cov(eps,Dh) > 0 when v <= sigma^2, rho < 1)"
        % (sp.simplify(sg2 - v_keep - (rho ** 2 * (sg2 - v) + c_eps ** 2 / var_h)),
           sp.simplify(v - v_disc - c_lat ** 2 / var_h), sp.simplify(c_eps - (1 - rho) * (sg2 * (1 + rho) - rho * v))))
    sv2 = (1 - rho) * sg2
    var_hs = tau2 + sv2 + v
    out("XS2 shared-component Kalman step: (1-rho)sigma^2 - v_keep - ((1-rho)sigma^2)^2/Var(Dh) = %s ; v - v_disc - v^2/Var(Dh) = %s"
        % (sp.simplify(sv2 - (sv2 - sv2 ** 2 / var_hs) - sv2 ** 2 / var_hs), sp.simplify(v - (v - v ** 2 / var_hs) - v ** 2 / var_hs)))
    # Prop. 7 local form: I(h) = int_0^h f(t* - r) r dr, h = t* - t~ (oriented)
    T, mu, r, hh = sp.symbols('T mu r h', real=True)
    s = sp.symbols('s', positive=True)
    f = lambda q: sp.exp(-((q - mu) / s) ** 2 / 2) / (s * sp.sqrt(2 * sp.pi))
    ser = sp.series(f(T - r) * r, r, 0, 4).removeO()
    Ih = sp.integrate(ser, (r, 0, hh))
    target = f(T) * (hh ** 2 / 2 + (T - mu) * hh ** 3 / (3 * s ** 2))
    dI = sp.expand(Ih - target)
    out("XS3 Prop. 7 local form: coefficients of h^2 and h^3 in [int_0^h f(t*-r) r dr] - f(t*)(h^2/2 + (t*-mu) h^3/(3 s^2)): "
        "%s, %s (so the local form has relative error (2/3)(t*-mu)(t*-t~)/s^2 + O((t*-t~)^2/s^2 (1 + (t*-mu)^2/s^2)))"
        % (sp.simplify(dI.coeff(hh, 2)), sp.simplify(dI.coeff(hh, 3))))
    # Prop. 10(b) with noise sigma > 0 at trial 2
    t, beta, tau, sig = sp.symbols('t beta tau sigma', positive=True)
    tt = sp.symbols('tt', real=True)
    S2 = sp.sqrt(tau ** 2 + sig ** 2)
    Phi = lambda q: (1 + sp.erf(q / sp.sqrt(2))) / 2
    phi = lambda q: sp.exp(-q ** 2 / 2) / sp.sqrt(2 * sp.pi)
    Vb = lambda tq, m: m * Phi(-(tq - m) / S2) + tau ** 2 / S2 * phi((tq - m) / S2)
    out("XS4 Prop. 10(b), sigma > 0: V(0; 0, tau, sigma) - tau^2 phi(0)/s = %s ; lim_{t -> -oo} V(t; beta, tau, sigma) = %s "
        "(so G_sigma = V(t*; beta) - V(0; 0) >= beta - tau^2 phi(0)/s)"
        % (sp.simplify(Vb(0, 0) - tau ** 2 / S2 * phi(0)), sp.limit(Vb(tt, beta), tt, -sp.oo)))


def _post_moments(model, rho, k1, k2, h1, h2, mu1, tau1, mu2, tau2):
    """Independent implementation (explicit Gaussian conditioning on (Dh_1, Dh_2), not the Kalman recursion).
    sigma = 1. kernel: latents (e0, D1, xi1, D2, xi2); shared: (v0, D1, vn1, D2, vn2).
    Returns the posterior mean and variance of the record error before trial 3 (kernel: e_2; shared: v_rec,2)."""
    M = len(h1)
    if model == "kernel":
        sc = np.sqrt(1 - rho ** 2)
        s0, sxi = np.ones(M), np.ones(M)
        a1 = np.array([-(1 - rho), 1, sc, 0, 0], float)
        bk, bd = np.array([rho, 0, sc, 0, 0], float), np.array([1, 0, 0, 0, 0], float)
    else:
        sv2 = 1 - rho
        s0, sxi = np.full(M, sv2), np.full(M, sv2)
        a1 = np.array([-1, 1, 1, 0, 0], float)
        bk, bd = np.array([0, 0, 1, 0, 0], float), np.array([1, 0, 0, 0, 0], float)
    b1 = np.where(k1[:, None], bk, bd)
    if model == "kernel":
        a2 = np.array([0, 0, 0, 1, sc])[None, :] - (1 - rho) * b1
        ck = rho * b1 + np.array([0, 0, 0, 0, sc])[None, :]
    else:
        a2 = np.array([0, 0, 0, 1, 1.0])[None, :] - b1
        ck = np.tile(np.array([0, 0, 0, 0, 1.0]), (M, 1))
    c = np.where(k2[:, None], ck, b1)
    m0 = np.stack([np.zeros(M), mu1, np.zeros(M), mu2, np.zeros(M)], 1)
    S = np.stack([s0, tau1 ** 2, sxi, tau2 ** 2, sxi], 1)
    A = np.stack([np.tile(a1, (M, 1)), a2], 1)
    y = np.stack([h1, h2], 1)
    SAt = S[:, :, None] * np.transpose(A, (0, 2, 1))
    Gm = np.einsum('mij,mjk->mik', A, SAt)
    det = Gm[:, 0, 0] * Gm[:, 1, 1] - Gm[:, 0, 1] * Gm[:, 1, 0]
    Gi = np.stack([np.stack([Gm[:, 1, 1], -Gm[:, 0, 1]], 1), np.stack([-Gm[:, 1, 0], Gm[:, 0, 0]], 1)], 1) / det[:, None, None]
    res = y - np.einsum('mij,mj->mi', A, m0)
    cSAt = np.einsum('mj,mjk->mk', c, SAt)
    mean = np.einsum('mj,mj->m', c, m0) + np.einsum('mk,mkl,ml->m', cSAt, Gi, res)
    var = np.einsum('mj,mj->m', c * S, c) - np.einsum('mk,mkl,ml->m', cSAt, Gi, cSAt)
    return mean, var


def x_posterior_bins():
    out("== XN1: (AI analysis) e | F_n is Gaussian given the full ledger; narrow-bin check, independent implementation ==")
    out("XN1 two trials, sigma = 1, deployed rule t*_n = -mu_n sigma_d^2/tau_n^2 (sigma_d^2 = 2(1-rho)), ledger-reading proposer "
        "mu_2 = -0.2 + 0.3 tanh(Dh_1/sigma_d), tau_2 = 0.35 + 0.3/(1 + (Dh_1/sigma_d)^2); target: record error before trial 3, "
        "standardized by the exact Gaussian posterior given (Dh_1, Dh_2); 4e7 campaigns per model; bins of half-width 0.1 s")
    mu1, tau1 = -0.3, 0.5
    for model, rho in (("kernel", 0.0), ("kernel", 0.82), ("shared", 0.82)):
        sd2 = 2 * (1 - rho)
        sd = np.sqrt(sd2)
        s1 = np.sqrt(tau1 ** 2 + sd2)
        t1 = -mu1 * sd2 / tau1 ** 2
        mu2f = lambda h: -0.2 + 0.3 * np.tanh(h / sd)
        tau2f = lambda h: 0.35 + 0.3 / (1 + (h / sd) ** 2)
        centers = []
        for k1 in (0, 1):
            h1c = t1 + (0.4 if k1 else -0.4) * s1
            m2c, ta2c = mu2f(h1c), tau2f(h1c)
            t2c = -m2c * sd2 / ta2c ** 2
            s2 = np.sqrt(ta2c ** 2 + sd2)
            for k2 in (0, 1):
                centers.append((k1, k2, h1c, t2c + (0.4 if k2 else -0.4) * s2, 0.1 * s1, 0.1 * s2))
        acc = {i: [] for i in range(len(centers))}
        raw_by_pat = {p: [] for p in range(4)}
        zpat = {p: [] for p in range(4)}
        glob = []
        for chunk in range(40):
            M = 1_000_000
            if model == "kernel":
                sc = np.sqrt(1 - rho ** 2)
                e0 = rng2.normal(0, 1, M)
                d1 = rng2.normal(mu1, tau1, M)
                x1 = rng2.normal(0, 1, M)
                h1 = d1 - (1 - rho) * e0 + sc * x1
                k1 = h1 > t1
                e1 = np.where(k1, rho * e0 + sc * x1, e0)
                m2, ta2 = mu2f(h1), tau2f(h1)
                d2 = rng2.normal(m2, ta2)
                x2 = rng2.normal(0, 1, M)
                h2 = d2 - (1 - rho) * e1 + sc * x2
                k2 = h2 > -m2 * sd2 / ta2 ** 2
                tgt = np.where(k2, rho * e1 + sc * x2, e1)
            else:
                sv = np.sqrt(1 - rho)
                v0 = rng2.normal(0, sv, M)
                d1 = rng2.normal(mu1, tau1, M)
                vn1 = rng2.normal(0, sv, M)
                h1 = d1 + vn1 - v0
                k1 = h1 > t1
                r1 = np.where(k1, vn1, v0)
                m2, ta2 = mu2f(h1), tau2f(h1)
                d2 = rng2.normal(m2, ta2)
                vn2 = rng2.normal(0, sv, M)
                h2 = d2 + vn2 - r1
                k2 = h2 > -m2 * sd2 / ta2 ** 2
                tgt = np.where(k2, vn2, r1)
            pat = 2 * k1 + k2
            for p in range(4):
                ip = np.flatnonzero(pat == p)[:25000]
                raw_by_pat[p].append(tgt[ip])
                mm, vv = _post_moments(model, rho, k1[ip], k2[ip], h1[ip], h2[ip], np.full(len(ip), mu1),
                                       np.full(len(ip), tau1), m2[ip], ta2[ip])
                zpat[p].append((tgt[ip] - mm) / np.sqrt(vv))
            for i, (c1, c2, h1c, h2c, w1, w2) in enumerate(centers):
                sel = (np.abs(h1 - h1c) < w1) & (np.abs(h2 - h2c) < w2)
                if sel.any():
                    mm, vv = _post_moments(model, rho, k1[sel], k2[sel], h1[sel], h2[sel], np.full(sel.sum(), mu1),
                                           np.full(sel.sum(), tau1), m2[sel], ta2[sel])
                    acc[i].append(np.column_stack([(tgt[sel] - mm) / np.sqrt(vv), k1[sel], k2[sel]]))
            if chunk < 2:
                idx = np.arange(100_000)
                mm, vv = _post_moments(model, rho, k1[idx], k2[idx], h1[idx], h2[idx], np.full(len(idx), mu1),
                                       np.full(len(idx), tau1), m2[idx], ta2[idx])
                glob.append((tgt[idx] - mm) / np.sqrt(vv))
        g = np.concatenate(glob)
        gm, gs, gk, gku = skew_kurt(g)
        rs = [skew_kurt(np.concatenate(raw_by_pat[p]))[2] for p in range(4)]
        out(f"XN1 [{model}, rho={rho}] all histories (2e5): standardized mean {gm:+.4f}, sd {gs:.4f}, skew {gk:+.4f}, "
            f"excess kurt {gku:+.4f}, KS p {stats.kstest(g, 'norm').pvalue:.3f}; skew of the raw record error by keep pattern "
            f"00/01/10/11: {rs[0]:+.3f} {rs[1]:+.3f} {rs[2]:+.3f} {rs[3]:+.3f}")
        parts = []
        for p in range(4):
            zp = np.concatenate(zpat[p])
            a_, b_, c_, d_ = skew_kurt(zp)
            parts.append(f"{p >> 1}{p & 1}: n={len(zp)}, {a_:+.4f} {b_:.4f} {c_:+.4f} {d_:+.4f}")
        out(f"XN1 [{model}, rho={rho}] by keep pattern (up to 1e6 rows each; mean, sd, skew, excess kurt; s.e. of skew "
            f"<= {np.sqrt(6 / min(len(np.concatenate(zpat[p])) for p in range(4))):.4f}): " + "; ".join(parts))
        for i, (c1, c2, h1c, h2c, w1, w2) in enumerate(centers):
            a = np.concatenate(acc[i])
            zz = a[:, 0]
            purity = np.mean((a[:, 1] == c1) & (a[:, 2] == c2))
            mm, ss, sk, ku = skew_kurt(zz)
            out(f"XN1 [{model}, rho={rho}]   bin Dh_1 = {h1c:+.3f}, Dh_2 = {h2c:+.3f} (keep pattern {c1}{c2}, share {purity:.3f}): "
                f"n = {len(zz)}, mean {mm:+.4f} (s.e. {1/np.sqrt(len(zz)):.4f}), sd {ss:.4f}, skew {sk:+.4f} "
                f"(s.e. {np.sqrt(6/len(zz)):.4f}), excess kurt {ku:+.4f} (s.e. {np.sqrt(24/len(zz)):.4f})")


def _hermite_tests(z, F):
    """max |t| of E[He_k(z) g] = 0 over k = 1..4 and the columns g of F (plus the constant)."""
    He = [z, z ** 2 - 1, z ** 3 - 3 * z, z ** 4 - 6 * z ** 2 + 3]
    G = np.column_stack([np.ones(len(z))] + [(F[:, j] - F[:, j].mean()) / (F[:, j].std() + 1e-300) for j in range(F.shape[1])])
    worst, ntest = 0.0, 0
    for hk in He:
        prod = hk[:, None] * G
        tt = prod.mean(0) / (prod.std(0) / np.sqrt(len(z)) + 1e-300)
        worst = max(worst, np.max(np.abs(tt)))
        ntest += G.shape[1]
    return worst, ntest


def x_campaigns(model, policy, M, N, sgm, rho, tau, mu_base, gen, react=0.5):
    """N-trial campaigns; the latent record error follows the exact Kalman recursion given the recorded comparisons.
    policy 'plain' = deployed t*_n with the measured sigma_d; 'bayes' = t**_n with the Kalman moments."""
    sd2 = 2 * sgm ** 2 * (1 - rho)
    sd = np.sqrt(sd2)
    if model == "kernel":
        sc = sgm * np.sqrt(1 - rho ** 2)
        vref = sgm ** 2
    else:
        sv2 = (1 - rho) * sgm ** 2
        vref = sv2
    lat = gen.normal(0, np.sqrt(vref), M)
    m, v = np.zeros(M), np.full(M, vref)
    last_h = np.zeros(M)
    feats, vmax = [], 0.0
    for n in range(N):
        mu = mu_base + react * np.clip(last_h, -0.8 * sd, 0.8 * sd)
        if model == "kernel":
            w2 = sc ** 2 + (1 - rho) ** 2 * v
            tss = -(1 - rho) * m - mu * w2 / tau ** 2
        else:
            w2 = sv2 + v
            tss = -m - mu * w2 / tau ** 2
        tpl = -mu * sd2 / tau ** 2
        if n == N - 1:
            z = (lat - m) / np.sqrt(v)
            F = np.column_stack(feats + [m / np.sqrt(vref), v / vref, mu / tau])
            return dict(z=z, F=F, raw=lat, m=m, v=v, mu=mu, tss=tss, tpl=tpl, vmax=vmax, vref=vref, naive=lat / np.sqrt(vref))
        d = gen.normal(mu, tau, M)
        if model == "kernel":
            xi = gen.normal(0, 1, M)
            new = rho * lat + sc * xi
            hh = d + new - lat
            mean_h, var_h = mu - (1 - rho) * m, tau ** 2 + w2
            c_new, c_lat = sc ** 2 - rho * (1 - rho) * v, -(1 - rho) * v
            m_keep = rho * m + c_new / var_h * (hh - mean_h)
            v_keep = rho ** 2 * v + sc ** 2 - c_new ** 2 / var_h
        else:
            new = gen.normal(0, np.sqrt(sv2), M)
            hh = d + new - lat
            mean_h, var_h = mu - m, tau ** 2 + w2
            c_new, c_lat = sv2, -v
            m_keep = c_new / var_h * (hh - mean_h)
            v_keep = sv2 - c_new ** 2 / var_h
        keep = hh > (tpl if policy == "plain" else tss)
        m_disc = m + c_lat / var_h * (hh - mean_h)
        v_disc = v - c_lat ** 2 / var_h
        m, v = np.where(keep, m_keep, m_disc), np.where(keep, v_keep, v_disc)
        lat = np.where(keep, new, lat)
        vmax = max(vmax, float(np.max(v / vref)))
        feats += [hh / sd, (hh / sd) ** 2, keep.astype(float), keep * hh / sd]
        last_h = hh


def x_kalman_moments():
    out("== XN2: (AI analysis) conditional-moment test of the Gaussian posterior over full histories, deployed rule t* ==")
    out("XN2 under H0 (e | F_n ~ N(m_n, v_n) exactly) every Hermite moment E[He_k(z) g(F_n)] = 0 (k = 1..4); features g: each "
        "recorded Dh_j, its square, keep_j, keep_j*Dh_j, and m_n, v_n, mu_n; the naive standardization (unselected record, "
        "z = e/sd) is tested the same way as a power check")
    cases = (("kernel", 0.0125, 0.82, 0.009, -0.004, 0.5, "digits-like"),
             ("kernel", 0.0125, 0.0, 0.002, 0.0, 0.05, "rho = 0, near-null proposals, strong selection"),
             ("shared", 0.0125, 0.82, 0.009, -0.004, 0.5, "digits-like"))
    for model, sgm, rho, tau, mub, react, nm in cases:
        r = x_campaigns(model, "plain", 1_000_000, 6, sgm, rho, tau, mub, rng2, react)
        w, nt = _hermite_tests(r["z"], r["F"])
        wn, _ = _hermite_tests(r["naive"], r["F"])
        mm, ss, sk, ku = skew_kurt(r["z"])
        sk_raw = skew_kurt(r["raw"])[2]
        cond = (r["mu"] <= 0) & (r["m"] >= 0)
        viol = np.sum(cond & (r["tss"] > r["tpl"] + 1e-12 * np.abs(r["tpl"])))
        out(f"XN2 [{model}, rho={rho}, tau={tau}, mu = {mub} + {react} clip(last Dh), {nm}] trial 6 of 1e6 campaigns: max |t| over {nt} Hermite tests "
            f"{w:.2f} (naive standardization: {wn:.1f}); z mean {mm:+.4f}, sd {ss:.4f}, skew {sk:+.4f}, excess kurt {ku:+.4f}; "
            f"raw record error skew {sk_raw:+.3f}; max over trials of Var(e|F)/{'sigma^2' if model == 'kernel' else '(1-rho)sigma^2'} "
            f"{r['vmax']:.6f}; share with E[e|F] < 0: {np.mean(r['m'] < 0):.3f}; among mu <= 0 and E[e|F] >= 0 "
            f"({cond.sum()}), t** > t*: {viol}")


def x_prop7_edges():
    out("== XN3: T4 Prop. 7 at extreme parameters, 50-digit arithmetic, closed-form integral (S7.1b) ==")
    mpmath.mp.dps = 50
    mpf = mpmath.mpf

    def Vm(t, mu, tau, sg):
        s = mpmath.sqrt(tau ** 2 + sg ** 2)
        z = (t - mu) / s
        return mu * mpmath.ncdf(-z) + tau ** 2 / s * mpmath.npdf(z)

    n = lf = uf = neg = 0
    worst = mpf(0)
    rmin_lo, rmax_up = mpf('inf'), mpf(0)
    for mu in ('-1', '-1e-3', '0', '1e-3', '1'):
        for tau in ('1e-3', '1e-1', '1'):
            for sg in ('1e-4', '1e-2', '1'):
                mu_, tau_, sg_ = mpf(mu), mpf(tau), mpf(sg)
                s = mpmath.sqrt(tau_ ** 2 + sg_ ** 2)
                ts = -mu_ * sg_ ** 2 / tau_ ** 2
                for k in ('-5', '-0.5', '-1e-3', '1e-3', '0.5', '5', None):
                    tt = mpf(0) if k is None else ts + mpf(k) * s
                    if tt == ts:
                        continue
                    gap = Vm(ts, mu_, tau_, sg_) - Vm(tt, mu_, tau_, sg_)
                    I = (ts - mu_) * (mpmath.ncdf((ts - mu_) / s) - mpmath.ncdf((tt - mu_) / s)) \
                        + s * (mpmath.npdf((ts - mu_) / s) - mpmath.npdf((tt - mu_) / s))
                    ident = tau_ ** 2 / s ** 2 * I
                    fts, ftt = mpmath.npdf((ts - mu_) / s) / s, mpmath.npdf((tt - mu_) / s) / s
                    lower = tau_ ** 2 / (2 * s ** 2) * min(fts, ftt) * (ts - tt) ** 2
                    upper = tau_ ** 2 * (ts - tt) ** 2 / (2 * mpmath.sqrt(2 * mpmath.pi) * s ** 3)
                    tol = mpf('1e-45') * (abs(mu_) + tau_)
                    if gap > mpf('1e-40'):
                        worst = max(worst, abs(gap - ident) / gap)
                    neg += gap < -tol
                    lf += gap < lower - tol
                    uf += gap > upper + tol
                    if lower > mpf('1e-40'):
                        rmin_lo = min(rmin_lo, gap / lower)
                    if upper > mpf('1e-40'):
                        rmax_up = max(rmax_up, gap / upper)
                    n += 1
    out(f"XN3 {n} cases (mu in {{0, +-1e-3, +-1}}, tau in {{1e-3, 0.1, 1}}, sigma in {{1e-4, 0.01, 1}}, t~ = t* +- {{1e-3, 0.5, 5}} s "
        f"and t~ = 0): identity max rel diff (gap > 1e-40) {mpmath.nstr(worst, 3)}; gap < 0: {neg}; lower-bound failures {lf}; "
        f"upper-bound failures {uf}; min gap/lower {mpmath.nstr(rmin_lo, 12)}; max gap/upper {mpmath.nstr(rmax_up, 12)}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    out("AI-assisted (Claude, subagent, 23 Nov 2026). Independent AI proof check under PLAN R1-PROOF-POLICY (check (a)); not an author check.")
    out(f"Output of ai_proof_check_20261123.py (seed {SEED}; numpy {np.__version__}, scipy {scipy.__version__}, "
        f"sympy {sp.__version__}, mpmath {mpmath.__version__}).")
    symbolic()
    n_prop1()
    n_prop6()
    n_kalman()
    n_prop7()
    n_prop9()
    n_prop10b()
    x_symbolic()
    x_posterior_bins()
    x_kalman_moments()
    x_prop7_edges()
    import sys
    print(f"total run time {time.time() - T0:.0f} s", file=sys.stderr)  # stderr, so that the output file is byte-reproducible
