"""Independent AI proof check of the appendix statements of Paper B that had not been through R1-PROOF-POLICY.

AI-assisted (Claude, subagent, 23 Nov 2026). Check (a) of PLAN row R1-PROOF-POLICY; the coordinating chat's spot
check (b) is separate. Not an author check. ENGINEERING_ONLY: no data of any sweep, audit or evaluation is read.

Statements (numbering as in AI_PROOF_CHECK_APPENDIX_20261123.md), manuscript papers/r1/sections/appendix.tex @ 5db543bb:
  1 prop:app-voi (T2 Prop. 2)      2 prop:app-split (T2 Prop. 3)     3 prop:app-record (T2 Prop. 4) and its Scope
  4 prop:app-verify (T2 Prop. 5)   5 prop:app-rules (T4 Cor. 8a)     6 edge cases of prop:onestep (revision 8'.4)
  7 "Summed gains need both conditions" (revision R3)                8 "Bias of offline evaluation" (revision R6)
  9 the information example, prop:failures(b), and Table tab:ex-info (revision 10(c))

Run:  python3 ai_proof_check_appendix_20261123.py > ai_proof_check_appendix_20261123_output.txt
Needs SymPy, NumPy, SciPy, mpmath. Fixed seeds (base 20261125, one generator per statement). The run time goes to
stderr, so the output file is byte-reproducible. Written without importing code from the earlier check scripts.

Every output line starts with a label: AS = symbolic, AN = numeric, then the statement number. Symbolic lines print
the simplified difference between two expressions (0 means the identity holds) or a limit. Numeric lines are
evidence, not proofs.
"""
import sys
import time
import numpy as np
import sympy as sp
import mpmath
import scipy
from scipy.stats import norm

T0 = time.time()
SEED = 20261125
PHI0 = norm.pdf(0.0)


def out(s=""):
    print(s, flush=True)


def rng_for(k):
    """One independent generator per statement k, so that adding checks to one section leaves the others unchanged."""
    return np.random.default_rng([SEED, k])


# ---------------------------------------------------------------- numeric helpers (double precision)
def psi(z):
    z = np.asarray(z, dtype=float)
    return norm.pdf(z) - z * norm.sf(z)


def voi(m, q):
    """Bayes value of information q psi(|m|/q); 0 at q = 0."""
    m = np.asarray(m, dtype=float)
    q = np.asarray(q, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        val = q * psi(np.abs(m) / np.where(q > 0, q, 1.0))
    return np.where(q > 0, val, 0.0)


def cond_moments(policy, mu, tau, st, ss, r, h):
    """Gaussian conditioning on H = h for the paired-replicate model of T2 section 1.

    H = Delta + e_t + e_s.  vary: Dbar = Delta + xi, Var xi = (st^2 + ss^2)/r.
    fixed: Dbar = Delta + e_s + xi, Var xi = st^2/r (the campaign's split error is reused).
    Returns m = E[Delta | H], v = Var(Delta | H), q^2 = Var(E[Delta | H, Dbar] | H), and the conditional mean and
    variance of Dbar and its covariance with Delta given H (for the frozen response D > 0).
    Generic matrix conditioning, independent of the closed forms checked symbolically.
    """
    t2, a, b = tau ** 2, st ** 2, ss ** 2
    if policy == "vary":
        vD = t2 + (a + b) / r
        cHD = t2
    else:
        vD = t2 + b + a / r
        cHD = t2 + b
    vH = t2 + a + b
    S = np.array([[t2, t2, t2], [t2, vH, cHD], [t2, cHD, vD]], dtype=float)
    m = mu + t2 / vH * (h - mu)
    v = t2 - t2 ** 2 / vH
    Sxx = S[1:, 1:]
    c = S[0, 1:]
    v2 = t2 - c @ np.linalg.solve(Sxx, c)
    q2 = max(v - v2, 0.0)
    mD = mu + cHD / vH * (h - mu)
    vDH = vD - cHD ** 2 / vH
    cDeltaD = t2 - t2 * cHD / vH
    return m, v, q2, mD, vDH, cDeltaD


# ================================================================ symbolic part
def symbolic():
    out("== AS: symbolic checks (SymPy %s) ==" % sp.__version__)
    x, e, d, h, me = sp.symbols('x e delta h m_e', real=True)
    q, mp, tau, st, ss, r, v, w, s, c, sig, g, al, be, ka, u, A, a = sp.symbols(
        'q m_p tau sigma_t sigma_s r v w s c sigma g alpha beta kappa u A a', positive=True)
    rho = sp.symbols('rho', real=True)
    Phi = lambda z: (1 + sp.erf(z / sp.sqrt(2))) / 2
    phi = lambda z: sp.exp(-z ** 2 / 2) / sp.sqrt(2 * sp.pi)
    psis = lambda z: phi(z) - z * Phi(-z)

    # ---- 1. prop:app-voi
    for lab, mval, base in (("m > 0", mp, mp), ("m < 0", -mp, 0)):
        Epos = sp.integrate(x * phi((x - mval) / q) / q, (x, 0, sp.oo))
        out("AS1.1 (%s) E[max(M',0)] - max(m,0) - q psi(|m|/q), M' ~ N(m, q^2): %s"
            % (lab, sp.simplify((Epos - base - q * psis(mp / q)).rewrite(sp.erf))))
    z = sp.symbols('z', positive=True)
    out("AS1.2 psi'(z) + Phi(-z): %s ; d/dq[q psi(x/q)] - phi(x/q): %s ; d2/dq2[q psi(x/q)] - (x^2/q^3) phi(x/q): %s"
        % (sp.simplify(sp.diff(psis(z), z) + Phi(-z)),
           sp.simplify(sp.diff(q * psis(mp / q), q) - phi(mp / q)),
           sp.simplify(sp.diff(q * psis(mp / q), q, 2) - mp ** 2 / q ** 3 * phi(mp / q))))
    # general replicate structure: given H, Cov(Delta, L) = [[v, c], [c, w]], Dbar = L + xi, Var xi = s^2/r
    q2g = c ** 2 / (w + s ** 2 / r)
    out("AS1.3 Dbar = L + fresh mean error: q_r^2 = c^2/(w + s^2/r); dq^2/dr - c^2 s^2/(w r + s^2)^2: %s ; "
        "d2q^2/dr2 + 2 c^2 s^2 w/(w r + s^2)^3: %s  (increasing and concave in r, for both split policies)"
        % (sp.simplify(sp.diff(q2g, r) - c ** 2 * s ** 2 / (w * r + s ** 2) ** 2),
           sp.simplify(sp.diff(q2g, r, 2) + 2 * c ** 2 * s ** 2 * w / (w * r + s ** 2) ** 3)))
    # full-model conditioning, both policies
    t2, ua, ub = tau ** 2, st ** 2, ss ** 2
    vH = t2 + ua + ub

    def q2_full(policy):
        if policy == "vary":
            vD, cHD = t2 + (ua + ub) / r, t2
        else:
            vD, cHD = t2 + ub + ua / r, t2 + ub
        Sxx = sp.Matrix([[vH, cHD], [cHD, vD]])
        cc = sp.Matrix([t2, t2])
        var1 = t2 - t2 ** 2 / vH
        var2 = t2 - (cc.T * Sxx.inv() * cc)[0, 0]
        return sp.simplify(var1 - var2), sp.simplify(var1)

    q2v, vv = q2_full("vary")
    sd2 = ua + ub
    vv_cf = t2 * sd2 / (t2 + sd2)
    out("AS1.4 vary: v - tau^2 sigma_d^2/(tau^2+sigma_d^2): %s ; q^2 - v^2/(v + sigma_d^2/r): %s"
        % (sp.simplify(vv - vv_cf), sp.simplify(q2v - vv_cf ** 2 / (vv_cf + sd2 / r))))
    q2f, _ = q2_full("fixed")
    cf = t2 - t2 * (t2 + ub) / vH                # Cov(Delta, Delta + e_s | H)
    wf = (t2 + ub) - (t2 + ub) ** 2 / vH         # Var(Delta + e_s | H)
    out("AS1.5 fixed: q^2 - c^2/(w + sigma_t^2/r) with c = Cov(Delta, Delta+e_s | H), w = Var(Delta+e_s | H): %s"
        % sp.simplify(q2f - cf ** 2 / (wf + ua / r)))

    # ---- 2. prop:app-split
    Aa = t2 + ub
    q2_audit = t2 ** 2 * ua / ((Aa + ua) ** 2 * (1 + 1 / r - ua / (Aa + ua)))
    out("AS2.1 fixed: q^2 - tau^4 u/((A+u)^2 (1 + 1/r - u/(A+u))) [audit's form, A = tau^2+sigma_s^2, u = sigma_t^2]: %s"
        % sp.simplify(q2f - q2_audit))
    lim_f = sp.limit(sp.simplify(q2f / ua).subs(st, sp.sqrt(u)), u, 0)
    out("AS2.2 fixed: lim_{sigma_t -> 0} q^2/sigma_t^2 - tau^4 r/((tau^2+sigma_s^2)^2 (r+1)): %s  (so VoI <= q phi(0) -> 0)"
        % sp.simplify(lim_f - t2 ** 2 * r / (Aa ** 2 * (r + 1))))
    v0 = t2 * ub / Aa
    lim_v = sp.limit(q2v.subs(st, sp.sqrt(u)), u, 0)
    out("AS2.3 vary: lim_{sigma_t -> 0} q^2 - v0^2/(v0 + sigma_s^2/r), v0 = tau^2 sigma_s^2/(tau^2+sigma_s^2): %s  (> 0 for tau, sigma_s > 0)"
        % sp.simplify(lim_v - v0 ** 2 / (v0 + ub / r)))

    # ---- 3. prop:app-record
    sc = sig * sp.sqrt(1 - rho ** 2)
    pk = 1 - Phi((e - d - rho * e) / sc)          # P(eps > e - delta | e), eps | e ~ N(rho e, sigma^2 (1 - rho^2))
    form = Phi((d - (1 - rho) * e) / sc)
    out("AS3.1 P(delta + eps - e > 0 | e) - Phi((delta - (1-rho) e)/(sigma sqrt(1-rho^2))): %s ; "
        "d/de of the formula + (1-rho)/(sigma sqrt(1-rho^2)) phi(.): %s  (< 0 for -1 < rho < 1)"
        % (sp.simplify(pk - form), sp.simplify(sp.diff(form, e) + (1 - rho) / sc * phi((d - (1 - rho) * e) / sc))))
    # kernel model: given the history e ~ N(m_e, v); eps = rho e + sigma_c xi
    var_eps = rho ** 2 * v + sc ** 2
    out("AS3.2 kernel given the history (e ~ N(m_e, v)): Cov(e,eps)/Var(e) - rho: %s ; Var(eps|e) - sigma^2(1-rho^2): %s ; "
        "Var(eps) - sigma^2 - rho^2 (v - sigma^2): %s  (the kernel holds; the centred common-variance joint law needs m_e = 0, v = sigma^2)"
        % (sp.simplify(rho * v / v - rho), sp.simplify(sc ** 2 - sig ** 2 * (1 - rho ** 2)),
           sp.simplify(var_eps - sig ** 2 - rho ** 2 * (v - sig ** 2))))
    # rho = 0, null trial against an unselected record, recorded comparison h = eps1 - e0 > 0 (a keep)
    Sm = sp.Matrix([[sig ** 2, 0], [0, sig ** 2]])     # (e0, eps1)
    lvec = sp.Matrix([-1, 1])
    m_new = (sp.Matrix([0, 1]).T * Sm * lvec)[0, 0] / (lvec.T * Sm * lvec)[0, 0] * h
    v_new = sig ** 2 - ((sp.Matrix([0, 1]).T * Sm * lvec)[0, 0]) ** 2 / (lvec.T * Sm * lvec)[0, 0]
    out("AS3.3 rho = 0, one null keep from an unselected record: E[e_new | h] - h/2: %s ; Var(e_new | h) - sigma^2/2: %s  "
        "(given the ledger the kept record's error is N(h/2, sigma^2/2), not N(0, sigma^2))"
        % (sp.simplify(m_new - h / 2), sp.simplify(v_new - sig ** 2 / 2)))

    # ---- 4. prop:app-verify
    out("AS4.1 psi(0) - phi(0): %s ; v - c^2/(w + s^2/r) - [(v w - c^2) + v s^2/r]/(w + s^2/r): %s  (so q^2 <= v when c^2 <= v w)"
        % (sp.simplify(psis(0) - phi(0)),
           sp.simplify(v - c ** 2 / (w + s ** 2 / r) - ((v * w - c ** 2) + v * s ** 2 / r) / (w + s ** 2 / r))))
    sdd = sp.symbols('sigma_d', positive=True)
    vvd = t2 * sdd ** 2 / (t2 + sdd ** 2)
    q2vd = vvd ** 2 / (vvd + sdd ** 2 / r)
    out("AS4.2 vary: sigma_d^2 - v - sigma_d^4/(tau^2+sigma_d^2): %s ; d/dv[v^2/(v+a)] - v(v+2a)/(v+a)^2: %s ; "
        "lim_{tau->oo} q^2 - sigma_d^2 r/(r+1): %s"
        % (sp.simplify(sdd ** 2 - vvd - sdd ** 4 / (t2 + sdd ** 2)),
           sp.simplify(sp.diff(v ** 2 / (v + a), v) - v * (v + 2 * a) / (v + a) ** 2),
           sp.simplify(sp.limit(q2vd, tau, sp.oo) - sdd ** 2 * r / (r + 1))))
    out("AS4.3 fixed: lim_{tau->oo} q^2 - sigma_t^2 r/(r+1): %s"
        % sp.simplify(sp.limit(q2f, tau, sp.oo) - ua * r / (r + 1)))
    out("AS4.4 phi(0) sqrt(r/(r+1)) at r = 1, 2, 3: %s ; phi(0) = %s"
        % (", ".join(sp.N(phi(0) * sp.sqrt(sp.Rational(k, k + 1)), 6).__str__() for k in (1, 2, 3)), sp.N(phi(0), 8)))

    # ---- 7. summed gains, example of prop:failures(b) at alpha = 1, beta = 10, kappa = 1, g = 1/2
    vals = {al: 1, be: 10, ka: 1, g: sp.Rational(1, 2)}
    J_one = sp.Max(be * phi(0) / sp.sqrt(1 + ka ** 2) - g, 0).subs(vals)
    J_all = (al * phi(0) - g + be * phi(0) - g).subs(vals)
    formula = (sp.Max(g - al * phi(0), 0) + sp.Max(g - be * phi(0) / sp.sqrt(1 + ka ** 2), 0)).subs(vals)
    out("AS7.1 J(one-step) = %s ; J(always execute, Bayes keep) = %s ; difference = %s ; sum (g - V*_n)^+ with the one-step V*_n = %s"
        % (sp.N(J_one, 12), sp.N(J_all, 12), sp.N(J_one - J_all, 12), sp.N(formula, 12)))

    # ---- 9. information example
    out("AS9.1 d/dbeta[beta psi(g/beta)] - phi(g/beta): %s  (so the slope of the difference is phi(g/beta) - phi(0)/sqrt(1+kappa^2), "
        "increasing in beta, not constant)" % sp.simplify(sp.diff(be * psis(g / be), be) - phi(g / be)))
    eps_ = sp.symbols('epsilon', positive=True)
    diff_large = al * phi(0) - g + be * psis(g / be) - (be * phi(0) / sp.sqrt(1 + ka ** 2) - g)
    resid = diff_large - (be * phi(0) * (1 - 1 / sp.sqrt(1 + ka ** 2)) + al * phi(0) - g / 2)
    out("AS9.2 lim_{beta->oo} [difference - beta phi(0)(1 - 1/sqrt(1+kappa^2)) - alpha phi(0) + g/2]: %s"
        % sp.simplify(sp.limit(sp.simplify(resid.subs(be, 1 / eps_)), eps_, 0)))
    diff_k0 = al * phi(0) - g + be * psis(g / be) - (be * phi(0) - g)
    out("AS9.3 kappa = 0: lim_{beta->oo} difference - (alpha phi(0) - g/2): %s  (bounded)"
        % sp.simplify(sp.limit(sp.simplify(diff_k0.subs(be, 1 / eps_)), eps_, 0) - (al * phi(0) - g / 2)))
    diff_small = al * phi(0) - g + be * psis(g / be) - 0
    out("AS9.4 lim_{beta->0} difference (one-step value 0 there) - (alpha phi(0) - g): %s  (< 0 when g > alpha phi(0))"
        % sp.simplify(sp.limit(diff_small, be, 0) - (al * phi(0) - g)))


# ================================================================ 1. prop:app-voi
def mp_psi(z):
    return mpmath.npdf(z) - z * mpmath.ncdf(-z)


def mp_q2(policy, tau2, st2, ss2, r):
    """Closed forms (AS1.4, AS1.5) in mpmath."""
    vH = tau2 + st2 + ss2
    if policy == "vary":
        sd2 = st2 + ss2
        v = tau2 * sd2 / (tau2 + sd2)
        return v ** 2 / (v + sd2 / r)
    cf = tau2 - tau2 * (tau2 + ss2) / vH
    wf = (tau2 + ss2) - (tau2 + ss2) ** 2 / vH
    return cf ** 2 / (wf + st2 / r)


def n1():
    rng = rng_for(1)
    out("== AN1: prop:app-voi (T2 Prop. 2) ==")
    sets = [("vary", -0.3, 0.8, 0.5, 0.6, 2, 0.1), ("fixed", -0.3, 0.8, 0.5, 0.6, 2, 0.1),
            ("vary", 0.0, 1.0, 0.7, 0.7, 3, 1.0), ("fixed", 0.4, 0.5, 0.9, 0.3, 1, -0.6)]
    M = 4_000_000
    for (pol, mu, tau, st, ss, r, h0) in sets:
        m, v, q2, mD, vDH, cDD = cond_moments(pol, mu, tau, st, ss, r, h0)
        # exact conditional sampling of (Delta, Dbar) given H = h0
        L = np.linalg.cholesky(np.array([[v, cDD], [cDD, vDH]]))
        zz = rng.standard_normal((M, 2)) @ L.T
        Dl, Db = m + zz[:, 0], mD + zz[:, 1]
        Mp = m + cDD / vDH * (Db - mD)
        gain = Dl * ((Mp > 0).astype(float) - float(m > 0))
        out(f"AN1.1 {pol:5s} mu={mu:+.1f} tau={tau} sd_t={st} sd_s={ss} r={r} H={h0:+.1f}: q psi(|m|/q) = {float(voi(m, np.sqrt(q2))):.6f}; "
            f"simulated E[Delta(1{{M'>0}} - 1{{m>0}}) | H] = {gain.mean():.6f} (s.e. {gain.std(ddof=1)/np.sqrt(M):.6f}); "
            f"q^2 - Cov^2/Var = {q2 - cDD ** 2 / vDH:.1e}")
    # end-to-end: joint simulation, window around H = h0, posterior from the joint covariance
    M2 = 8_000_000
    for (pol, mu, tau, st, ss, r, h0) in sets[:2]:
        D = mu + tau * rng.standard_normal(M2)
        et, es = st * rng.standard_normal(M2), ss * rng.standard_normal(M2)
        H = D + et + es
        if pol == "vary":
            Db = D + np.sqrt((st ** 2 + ss ** 2) / r) * rng.standard_normal(M2)
        else:
            Db = D + es + st / np.sqrt(r) * rng.standard_normal(M2)
        sH = np.sqrt(tau ** 2 + st ** 2 + ss ** 2)
        sel = np.abs(H - h0) < 0.01 * sH
        Hs, Ds, Dbs = H[sel], D[sel], Db[sel]
        cov = np.cov(np.vstack([D, H, Db]))
        beta = np.linalg.solve(cov[1:, 1:], cov[0, 1:])
        Mp = D.mean() + beta[0] * (Hs - H.mean()) + beta[1] * (Dbs - Db.mean())
        mH = mu + tau ** 2 / sH ** 2 * (Hs - mu)
        gain = Ds * ((Mp > 0).astype(float) - (mH > 0).astype(float))
        m, v, q2, *_ = cond_moments(pol, mu, tau, st, ss, r, h0)
        out(f"AN1.2 end-to-end {pol:5s} (joint draws, |H - {h0:+.1f}| < 0.01 s, posterior from the sample covariance, {sel.sum()} draws): "
            f"simulated {gain.mean():.5f} (s.e. {gain.std(ddof=1)/np.sqrt(sel.sum()):.5f}) against {float(voi(m, np.sqrt(q2))):.5f}")
    # increments in r at attainable parameters (P02 section 4), 50 digits
    mpmath.mp.dps = 50
    tau2, st2, ss2 = mpmath.mpf(2), mpmath.mpf('0.5'), mpmath.mpf('0.5')
    for pol in ("vary", "fixed"):
        for H in (mpmath.mpf('4.5'), mpmath.mpf(0)):
            m = tau2 * H / (tau2 + st2 + ss2)
            vals = [mpmath.sqrt(mp_q2(pol, tau2, st2, ss2, k)) * mp_psi(abs(m) / mpmath.sqrt(mp_q2(pol, tau2, st2, ss2, k))) for k in range(1, 6)]
            inc = [vals[i + 1] - vals[i] for i in range(4)]
            trend = "increasing" if all(inc[i + 1] > inc[i] for i in range(3)) else ("decreasing" if all(inc[i + 1] < inc[i] for i in range(3)) else "mixed")
            out(f"AN1.3 {pol:5s} tau^2=2, sd_t^2=sd_s^2=0.5, mu=0, H={mpmath.nstr(H, 2)} (m={mpmath.nstr(m, 3)}): VoI r=1..5 = "
                + ", ".join(mpmath.nstr(x_, 4) for x_ in vals) + "; increments " + ", ".join(mpmath.nstr(x_, 4) for x_ in inc) + f" ({trend})")
    mpmath.mp.dps = 15
    # generic matrix conditioning against the closed forms; concavity in r; random sets
    worst, nonconc, nonmono = 0.0, 0, 0
    for _ in range(2000):
        mu, tau = rng.normal(0, 1), rng.uniform(0.05, 3)
        st, ss = rng.uniform(0.0, 2), rng.uniform(0.0, 2)
        if st < 1e-3:
            st = 1e-3
        for pol in ("vary", "fixed"):
            q2s = []
            for k in range(1, 31):
                _, _, q2, *_ = cond_moments(pol, mu, tau, st, ss, k, 0.0)
                q2c = float(mp_q2(pol, mpmath.mpf(tau ** 2), mpmath.mpf(st ** 2), mpmath.mpf(ss ** 2), k))
                worst = max(worst, abs(q2 - q2c) / max(q2c, 1e-300))
                q2s.append(q2c)
            dq = np.diff(q2s)
            nonmono += int(np.any(dq < -1e-14))
            nonconc += int(np.any(np.diff(dq) > 1e-14 * max(q2s)))
    out(f"AN1.4 2,000 random sets x 2 policies, r = 1..30: max rel diff generic conditioning vs closed form {worst:.1e}; "
        f"sets with q_r^2 not non-decreasing {nonmono}; not concave {nonconc}")
    # a fixed response (keep iff Dbar > 0) can be worth less than the Bayes response, and less than not verifying
    for (pol, mu, tau, st, ss, r, h0) in [("vary", 0.0, 1.0, 1 / np.sqrt(2), 1 / np.sqrt(2), 1, 3.0),
                                         ("vary", 0.0, 1.0, 1 / np.sqrt(2), 1 / np.sqrt(2), 1, 0.3)]:
        m, v, q2, mD, vDH, cDD = cond_moments(pol, mu, tau, st, ss, r, h0)
        sD = np.sqrt(vDH)
        frozen = m * norm.cdf(mD / sD) + cDD * norm.pdf(mD / sD) / sD - max(m, 0.0)
        out(f"AN1.5 {pol} mu=0 tau=1 sd_d=1 r={r} H={h0}: Bayes-response value {float(voi(m, np.sqrt(q2))):.5f}; "
            f"value of 'keep iff Dbar > 0' relative to the Bayes decision on H alone {frozen:+.5f}")


# ================================================================ 2. prop:app-split
def n2():
    out("== AN2: prop:app-split (T2 Prop. 3) ==")
    mu, tau, ss, r, H = -0.3, 0.8, 0.6, 2, 0.0
    A = tau ** 2 + ss ** 2
    lim = tau ** 4 * r / (A ** 2 * (r + 1))
    for st in (0.5, 0.1, 1e-2, 1e-3, 1e-4):
        mf, _, q2f, *_ = cond_moments("fixed", mu, tau, st, ss, r, H)
        mv, _, q2v, *_ = cond_moments("vary", mu, tau, st, ss, r, H)
        q2fc = float(mp_q2("fixed", mpmath.mpf(tau ** 2), mpmath.mpf(st ** 2), mpmath.mpf(ss ** 2), r))
        out(f"AN2.1 mu=-0.3 tau=0.8 sd_s=0.6 r=2, sd_t={st:g}: fixed: max over H of VoI = q phi(0) = {np.sqrt(q2fc) * PHI0:.4e}, "
            f"VoI at H=0 {float(voi(mf, np.sqrt(q2fc))):.3e} (q^2/sd_t^2 = {q2fc / st ** 2:.6f}, limit {lim:.6f}); vary VoI at H=0 {float(voi(mv, np.sqrt(q2v))):.6f}")
    v0 = tau ** 2 * ss ** 2 / A
    q0 = np.sqrt(v0 ** 2 / (v0 + ss ** 2 / r))
    mpmath.mp.dps = 30
    vals = []
    for Hh in (0.0, 2.0, 5.0, 10.0):
        m0 = mu + tau ** 2 / A * (Hh - mu)
        vals.append(mpmath.mpf(q0) * mp_psi(mpmath.mpf(abs(m0)) / mpmath.mpf(q0)))
    mpmath.mp.dps = 15
    out("AN2.2 vary, limit sd_t -> 0 (q0 = %.6f): VoI at H = 0, 2, 5, 10 = %s  (positive at each H, tends to 0 as |H| grows: "
        "pointwise, not uniform)" % (q0, ", ".join(mpmath.nstr(x_, 4) for x_ in vals)))


# ================================================================ 3. prop:app-record and its Scope
def n3():
    rng = rng_for(3)
    out("== AN3: prop:app-record (T2 Prop. 4) and its Scope paragraph ==")
    sig, rho, dl, M = 1.0, 0.6, 0.3, 8_000_000
    sc = sig * np.sqrt(1 - rho ** 2)
    e = sig * rng.standard_normal(M)
    eps = rho * e + sc * rng.standard_normal(M)
    keep = dl + eps - e > 0
    parts = []
    for e0 in (-1.0, 0.0, 1.0, 2.0):
        sel = np.abs(e - e0) < 0.02
        parts.append(f"e~{e0:+.0f}: {norm.cdf((dl - (1 - rho) * e0) / sc):.4f}/{keep[sel].mean():.4f}")
    out("AN3.1 unselected record, sigma=1 rho=0.6 delta=0.3, formula/simulated P(keep | e): " + "; ".join(parts))
    # kernel model as the generative law: one null trial against an unselected record, then a later fresh candidate
    for rho in (0.0, 0.6):
        sc = sig * np.sqrt(1 - rho ** 2)
        e0 = sig * rng.standard_normal(M)
        eps1 = rho * e0 + sc * rng.standard_normal(M)
        k = eps1 > e0                       # null proposal, default rule
        en = eps1[k]
        eps2 = rho * en + sc * rng.standard_normal(en.size)
        slope = np.cov(en, eps2)[0, 1] / en.var(ddof=1)
        resid = eps2 - slope * en
        corr = np.corrcoef(en, eps2)[0, 1]
        sel = np.abs(en - 1.0) < 0.02
        kk = (0.2 + eps2[sel] - en[sel] > 0)
        pk, pse = kk.mean(), kk.std(ddof=1) / np.sqrt(kk.size)
        out(f"AN3.2 kernel model rho={rho}: after one null keep ({en.size} keeps) mean e = {en.mean():+.4f}, Var e = {en.var():.4f} "
            f"(centred common-variance law needs 0 and {sig ** 2:.1f}); Corr(e, eps_next) = {corr:.4f} (rho = {rho}); "
            f"regression slope {slope:.4f}, residual variance {resid.var():.4f} (kernel: {rho}, {sc ** 2:.4f}); "
            f"P(keep delta=0.2 | e~1) {pk:.4f} (s.e. {pse:.4f}) vs formula {norm.cdf((0.2 - (1 - rho) * 1.0) / sc):.4f}")
    out(f"AN3.3 rho=0 exact: E[e | one null keep] = sigma/sqrt(pi) = {1 / np.sqrt(np.pi):.4f}, Var = sigma^2 (1 - 1/pi) = {1 - 1 / np.pi:.4f}")
    # given the recorded comparison h (the ledger), rho = 0: e_new | h ~ N(h/2, sigma^2/2)
    e0 = rng.standard_normal(M)
    eps1 = rng.standard_normal(M)
    hh = eps1 - e0
    parts = []
    for h0 in (0.5, 1.5):
        sel = np.abs(hh - h0) < 0.01
        parts.append(f"h~{h0}: mean {eps1[sel].mean():.4f} (h/2 = {h0 / 2}), var {eps1[sel].var():.4f} (0.5)")
    out("AN3.4 rho=0, kept record given its recorded comparison h: " + "; ".join(parts))
    # source (b): E[e_n] versus the expected maximum of n draws and sqrt(2 ln n)
    parts = []
    for n in (10, 40, 1000):
        En = mpmath.quad(lambda t: t * n * mpmath.npdf(t) * mpmath.ncdf(t) ** (n - 1), [-mpmath.inf, 0, 3, mpmath.inf])
        En1 = mpmath.quad(lambda t: t * (n + 1) * mpmath.npdf(t) * mpmath.ncdf(t) ** n, [-mpmath.inf, 0, 3, mpmath.inf])
        parts.append(f"n={n}: E max(n draws) {mpmath.nstr(En, 4)}, E max(n+1 draws) {mpmath.nstr(En1, 4)}, sqrt(2 ln n) {np.sqrt(2 * np.log(n)):.3f}")
    out("AN3.5 sigma=1, null stretch, record = max(initial unselected draw, n fresh draws): " + "; ".join(parts))
    # stagnation trend (fresh errors): record level and conditional keep probability of delta = 0.005 at sigma = 0.0125
    C = 200_000
    s_, dl = 0.0125, 0.005
    rec = s_ * rng.standard_normal(C)
    parts = []
    for n in range(1, 201):
        rec = np.maximum(rec, s_ * rng.standard_normal(C))
        if n in (5, 20, 40, 200):
            parts.append(f"n={n}: mean e_n/sigma {rec.mean() / s_:.3f}, mean P(keep | e_n) {norm.cdf((dl - rec) / s_).mean():.3f}")
    out("AN3.6 fresh errors, sigma=0.0125, delta=0.005, 200,000 stretches: " + "; ".join(parts))


# ================================================================ 4. prop:app-verify
def q2_closed(policy, tau2, st2, ss2, r):
    """The closed forms of AS1.4 / AS1.5 in double precision."""
    vH = tau2 + st2 + ss2
    if policy == "vary":
        sd2 = st2 + ss2
        v = tau2 * sd2 / (tau2 + sd2)
        return v ** 2 / (v + sd2 / r), v
    cf = tau2 - tau2 * (tau2 + ss2) / vH
    wf = (tau2 + ss2) - (tau2 + ss2) ** 2 / vH
    return cf ** 2 / (wf + st2 / r), tau2 - tau2 ** 2 / vH


def n4():
    rng = rng_for(4)
    out("== AN4: prop:app-verify (T2 Prop. 5) ==")
    v1 = v2 = ncase = 0
    max_r2, fire_r1, npairs = 0.0, 0, 0
    for _ in range(2000):
        mu, tau = rng.normal(0, 1), rng.uniform(0.05, 3)
        st, ss = max(rng.uniform(0, 2), 1e-3), rng.uniform(0, 2)
        sd = np.hypot(st, ss)
        vH = tau ** 2 + st ** 2 + ss ** 2
        Hs = np.linspace(mu - 5 * np.sqrt(vH), mu + 5 * np.sqrt(vH), 41)
        mvals = mu + tau ** 2 / vH * (Hs - mu)
        for pol in ("vary", "fixed"):
            npairs += 1
            for k in range(1, 6):
                q2, v = q2_closed(pol, tau ** 2, st ** 2, ss ** 2, k)
                q = np.sqrt(q2)
                vo = voi(mvals, q)
                v1 += int(np.sum(vo > q * PHI0 * (1 + 1e-12)))
                v2 += int(q > np.sqrt(v) * (1 + 1e-12))
                ncase += 41
                if k == 2:
                    max_r2 = max(max_r2, q * PHI0 / sd)
                if k == 1 and q * PHI0 > 0.2 * sd:
                    fire_r1 += 1
    out(f"AN4.1 2,000 random sets x 2 policies x r = 1..5 x 41 values of H ({ncase} cases): VoI > q phi(0) in {v1}; q > sqrt(v) in {v2}")
    parts = []
    for k in (1, 2, 3):
        q2v, _ = q2_closed("vary", 1e6, 0.5, 0.5, k)
        q2f, _ = q2_closed("fixed", 1e6, 0.5, 0.5, k)
        parts.append(f"r={k}: vary max VoI/sd_d {np.sqrt(q2v) * PHI0:.5f}, fixed max VoI/sd_t {np.sqrt(q2f / 0.5) * PHI0:.5f}, "
                     f"phi(0) sqrt(r/(r+1)) {PHI0 * np.sqrt(k / (k + 1)):.5f}")
    out("AN4.2 tau = 1000 sd_d (sd_t^2 = sd_s^2 = sd_d^2/2): " + "; ".join(parts))
    out(f"AN4.3 R1-A1-VERIFY (g = 0.1 sd_node, sd_d <= sd_node): over the same random sets, max of max VoI/sd_d at r = 2 is {max_r2:.4f} "
        f"(< phi(0) sqrt(2/3) = {PHI0 * np.sqrt(2 / 3):.4f} < 2rg/sd_d = 0.4; directly: VoI <= sqrt(v) phi(0) < sd_d phi(0) = {PHI0:.5f} sd_d); "
        f"at r = 1 (2rg = 0.2 sd_node) max VoI > 0.2 sd_d in {fire_r1} of {npairs} set-policy pairs")


# ================================================================ 5. prop:app-rules
def n5():
    rng = rng_for(5)
    out("== AN5: prop:app-rules (T4 Cor. 8a) ==")
    mu, tau, sig, h0, g = 1.0, 1.0, 1.0, -0.1, 0.1
    post = mu + tau ** 2 / (tau ** 2 + sig ** 2) * (h0 - mu)
    M = 8_000_000
    D = mu + tau * rng.standard_normal(M)
    H = D + sig * rng.standard_normal(M)
    sel = np.abs(H - h0) < 0.01
    out(f"AN5.1 duplicate of a configuration discarded by the default rule (recorded comparison h = {h0}, same incumbent), "
        f"forecast mu=1 tau=1 sigma=1 at trial n: E[Delta | O_n] = {post:.4f} (simulated {D[sel].mean():.4f}, s.e. "
        f"{D[sel].std(ddof=1) / np.sqrt(sel.sum()):.4f}); a run reveals nothing, so m_n = E[Delta | O_n] and V*_n = {max(post, 0):.4f}; "
        f"at g = {g}: execute-and-keep-by-(i) earns V*_n - g = {max(post, 0) - g:+.4f} > skip 0 > -g = {-g:+.4f}")

    def campaigns(t, C=20_000, N=20, K=12):
        dup_seen = dup_kept = b_down = 0
        max_dup_hat = -np.inf
        for _ in range(C):
            metric = rng.standard_normal(K) + rng.standard_normal(K)   # true value + per-configuration fixed error
            inc, B, evaluated = 0, metric[0], {0}
            for x in rng.integers(0, K, N):
                x = int(x)
                if x == inc:
                    continue                                          # identified no-op
                hat = metric[x] - B
                is_dup = x in evaluated
                evaluated.add(x)
                if is_dup:
                    dup_seen += 1
                    max_dup_hat = max(max_dup_hat, hat)
                if hat > t:
                    dup_kept += int(is_dup)
                    b_down += int(metric[x] < B)
                    inc, B = x, metric[x]
        return dup_seen, dup_kept, b_down, max_dup_hat

    for t in (0.0, -0.5):
        ds, dk, bd, mx = campaigns(t)
        out(f"AN5.2 toy bit-exact node (12 configurations, recorded metric fixed per configuration, 20,000 campaigns of 20 trials), "
            f"keep iff comparison > {t:+.1f}: duplicates {ds}, kept {dk}, record decreases {bd}, max duplicate comparison {mx:+.3e}")


# ================================================================ 6. edge cases of prop:onestep
def n6():
    out("== AN6: edge cases of prop:onestep (revision 8'.4) ==")
    pi, mu = 0.3, 0.02
    for lab, vals, probs in (("atom at -mu (no separation)", [-0.04, -0.02, 0.0, 0.02, 0.04], [0.1, 0.2, 0.4, 0.2, 0.1]),
                             ("no atom at -mu (separation)", [-0.03, -0.01, 0.01, 0.03], [0.2, 0.3, 0.3, 0.2])):
        Hn = np.round(mu + np.array(vals), 12)
        p0 = float(np.sum(np.array(probs)[np.abs(Hn) < 1e-12]))
        pIc0 = (1 - pi) * p0 / (pi + (1 - pi) * p0)
        m0 = pIc0 * mu
        keeps_all = all((1.0 if abs(hh) > 1e-12 else pIc0) * mu > 0 for hh in Hn) and m0 > 0
        val_rule = (1 - pi) * float(np.sum(np.array(probs) * (((np.abs(Hn) > 1e-12) | (m0 > 0)) * mu)))
        val_oracle = (1 - pi) * mu
        out(f"AN6.1 bit-exact node, tau_n = 0, pi = {pi}, mu = {mu}, lattice noise, {lab}: P(non-no-op | H = 0) = {pIc0:.4f}, "
            f"m_n(H=0) = {m0:+.5f}, the m_n-rule keeps every executed proposal: {keeps_all}; its value {val_rule:.4f}, "
            f"(1 - pi) mu^+ = {val_oracle:.4f}")
    pi, mu, tau, sig = 0.3, 0.1, 1.0, 1.0
    s = np.hypot(tau, sig)
    parts = []
    for h in (-3.0, 0.0, 3.0):
        fI = pi * norm.pdf(h / sig) / sig
        fN = (1 - pi) * norm.pdf((h - mu) / s) / s
        pI = fI / (fI + fN)
        m1 = mu + tau ** 2 / s ** 2 * (h - mu)
        parts.append(f"H={h:+.0f}: P(no-op | H) {pI:.4f}, m_n {(1 - pI) * m1:+.4f} ({'keep' if (1 - pI) * m1 > 0 else 'discard'})")
    out(f"AN6.2 node where a no-op is not observed exactly (H = eta on a no-op), tau_n = {tau} > 0, mu_n = {mu} > 0, pi = {pi}, sigma = {sig}: "
        + "; ".join(parts))


# ================================================================ 7. summed gains (example of prop:failures(b))
def n7():
    rng = rng_for(7)
    out("== AN7: 'Summed gains need both conditions' (revision R3) ==")
    al, be, ka, g, M = 1.0, 10.0, 1.0, 0.5, 4_000_000
    th, xi = rng.standard_normal(M), rng.standard_normal(M)
    H2 = be * th + ka * be * xi
    V2 = be * PHI0 / np.sqrt(1 + ka ** 2)
    one = (be * th * (H2 > 0) - g) if V2 >= g else np.zeros(M)       # trial 1 skipped (alpha phi(0) < g); t* = 0 at trial 2
    allx = (al * th * (th > 0) - g) + (be * th * (th > 0) - g)        # execute both; theta known at trial 2
    dd = one - allx
    se = lambda y: y.std(ddof=1) / np.sqrt(M)
    out(f"AN7.1 alpha=1 beta=10 kappa=1 g=0.5, {M} draws with common random numbers: J(one-step) {one.mean():.4f} (s.e. {se(one):.4f}); "
        f"J(always execute, Bayes keep) {allx.mean():.4f} (s.e. {se(allx):.4f}); screening gain {dd.mean():+.4f} (s.e. {se(dd):.4f}); "
        f"manuscript: 2.3209, 3.3884, -1.0674, formula +0.1011")
    jo = V2 - g
    ja = al * PHI0 - g + be * PHI0 - g
    out(f"AN7.2 rounding: closed-form difference {jo - ja:+.6f} rounds to {jo - ja:+.4f}; the difference of the rounded values "
        f"2.3209 - 3.3884 = {2.3209 - 3.3884:+.4f}")


# ================================================================ 8. bias of offline evaluation
def n8():
    rng = rng_for(8)
    out("== AN8: 'Bias of offline evaluation' (revision R6) ==")
    al, be, ka, g, M = 1.0, 10.0, 1.0, 0.5, 4_000_000
    se = lambda y: y.std(ddof=1) / np.sqrt(M)
    # (NF) holds, (NI) fails: the example of prop:failures(b). The sweep executes both trials.
    th, xi = rng.standard_normal(M), rng.standard_normal(M)
    H2 = be * th + ka * be * xi
    V2on = be * PHI0 / np.sqrt(1 + ka ** 2)
    on = (be * th * (H2 > 0) - g) if V2on >= g else np.zeros(M)
    off = np.where(be * th >= g, be * th - g, 0.0)        # offline: H_1 = alpha theta is in the sweep history, so theta is known
    out(f"AN8.1 (NF) holds, (NI) fails (prop:failures(b), beta=10): Bayes one-step controller, online value {on.mean():.4f} "
        f"(closed form {V2on - g:.4f}); offline evaluation on a sweep {off.mean():.4f} (closed form beta psi(g/beta) = {be * float(psi(g / be)):.4f}); "
        f"offline - online {np.mean(off - on):+.4f} (s.e. {se(off - on):.4f}): optimistic")
    # (NF) and (NI): probe and edit independent (theta_1, theta_2)
    th1, th2, xi = rng.standard_normal(M), rng.standard_normal(M), rng.standard_normal(M)
    H2 = be * th2 + ka * be * xi
    on = (be * th2 * (H2 > 0) - g)                         # V2 is the same online and offline: H_1 says nothing on theta_2
    off = on.copy()
    out(f"AN8.2 (NF) and (NI) (theta_1, theta_2 independent): Bayes controller, offline - online {np.mean(off - on):+.4f} "
        f"(identical decisions on every path)")

    # learned (non-Bayes) forecasters under (NF) and (NI): the sign of the offline bias is not determined
    def value(mu_hat):
        """Realised trial-2 utility of a controller that plugs the forecast N(mu_hat, beta^2) into the closed form."""
        s2, tau = (be * ka) ** 2, be
        s = np.sqrt(tau ** 2 + s2)
        tstar = -mu_hat * s2 / tau ** 2
        zz = (tstar - mu_hat) / s
        Vstar = mu_hat * norm.sf(zz) + tau ** 2 / s * norm.pdf(zz)      # forecast value V(t*; mu_hat, tau, sigma)
        return np.where(Vstar >= g, be * th2 * (H2 > tstar) - g, 0.0)
    fa_off, fa_on = value(2.0 * be * th1), value(np.zeros(M))
    fb_off, fb_on = value(np.zeros(M)), value(np.full(M, -3.0 * be))
    out(f"AN8.3 learned forecaster A (offline it reads the uninformative H_1: mu_hat = 2 beta H_1; online mu_hat = 0): "
        f"offline - online {np.mean(fa_off - fa_on):+.4f} (s.e. {se(fa_off - fa_on):.4f}): pessimistic")
    out(f"AN8.4 learned forecaster B (online it reacts to the 'skipped' line: mu_hat = -3 beta; offline mu_hat = 0): "
        f"offline - online {np.mean(fb_off - fb_on):+.4f} (s.e. {se(fb_off - fb_on):.4f}): optimistic")


# ================================================================ 9. information example and Table tab:ex-info
TABLE = {2: ("0.0642", "0.4716", "0.4074"), 10: ("2.3209", "3.6434", "1.3224"),
         100: ("27.7095", "39.5437", "11.8342"), 1000: ("281.5948", "398.5913", "116.9965")}


def n9():
    rng = rng_for(9)
    out("== AN9: information example, prop:failures(b), and Table tab:ex-info (revision 10(c)) ==")
    mpmath.mp.dps = 30
    al, g, ka = mpmath.mpf(1), mpmath.mpf('0.5'), mpmath.mpf(1)
    phi0 = mpmath.npdf(0)
    for b in (2, 10, 100, 1000):
        be = mpmath.mpf(b)
        one = max(be * phi0 / mpmath.sqrt(1 + ka ** 2) - g, 0)
        probe = al * phi0 - g + be * mpmath.npdf(g / be) - g * mpmath.ncdf(-g / be)
        gap = max(probe - one, 0)
        strs = (f"{float(one):.4f}", f"{float(probe):.4f}", f"{float(gap):.4f}")
        ok = all(a_ == b_ for a_, b_ in zip(strs, TABLE[b]))
        # Monte Carlo with common random numbers
        M = 2_000_000
        th, xi = rng.standard_normal(M), rng.standard_normal(M)
        bf = float(be)
        V2 = bf * PHI0 / np.sqrt(2.0)
        mo = (bf * th * (bf * th + bf * xi > 0) - 0.5) if V2 >= 0.5 else np.zeros(M)
        pr = -0.5 + th * (th > 0) + np.where(bf * th > 0.5, bf * th - 0.5, 0.0)
        out(f"AN9.1 beta={b}: one-step {mpmath.nstr(one, 10)}, probe first {mpmath.nstr(probe, 10)}, gap {mpmath.nstr(gap, 10)}; "
            f"rounded {strs} vs table {TABLE[b]}: {'match' if ok else 'MISMATCH'}; MC one-step {mo.mean():.4f} (s.e. "
            f"{mo.std(ddof=1) / np.sqrt(M):.4f}), probe {pr.mean():.4f} ({pr.std(ddof=1) / np.sqrt(M):.4f}), "
            f"difference {np.mean(pr - mo):.4f} ({(pr - mo).std(ddof=1) / np.sqrt(M):.4f})")
    slope_inf = phi0 * (1 - 1 / mpmath.sqrt(2))
    parts = [f"beta={b}: {mpmath.nstr(mpmath.npdf(g / b) - phi0 / mpmath.sqrt(2), 6)}" for b in (2, 10, 100, 1000)]
    out(f"AN9.2 slope d(difference)/dbeta = phi(g/beta) - phi(0)/sqrt(2) (above the kink beta = g sqrt(2)/phi(0) = "
        f"{mpmath.nstr(g * mpmath.sqrt(2) / phi0, 6)}): " + "; ".join(parts) + f"; limit phi(0)(1 - 1/sqrt 2) = {mpmath.nstr(slope_inf, 8)}")
    parts = []
    for b in (10, 100, 1000, 10 ** 6):
        be = mpmath.mpf(b)
        d0 = al * phi0 - g + be * mpmath.npdf(g / be) - g * mpmath.ncdf(-g / be) - max(be * phi0 - g, 0)
        parts.append(f"beta={b}: {mpmath.nstr(d0, 6)}")
    out("AN9.3 kappa = 0: difference " + "; ".join(parts) + f"; limit alpha phi(0) - g/2 = {mpmath.nstr(al * phi0 - g / 2, 6)} (bounded)")
    be = mpmath.mpf('0.1')
    dsm = al * phi0 - g + be * mpmath.npdf(g / be) - g * mpmath.ncdf(-g / be) - max(be * phi0 / mpmath.sqrt(2) - g, 0)
    out(f"AN9.4 beta=0.1: difference {mpmath.nstr(dsm, 6)} (revision 10(c): about -0.1011; negative, so the gap is 0); "
        f"macros: alpha phi(0) = {mpmath.nstr(al * phi0, 6)} (\\ExTenCProbeValue = 0.40), slope {mpmath.nstr(slope_inf, 6)} "
        f"(\\ExTenCSlope = 0.117)")
    mpmath.mp.dps = 15


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    out("AI-assisted (Claude, subagent, 23 Nov 2026). Independent AI proof check of appendix statements under PLAN R1-PROOF-POLICY "
        "(check (a)); not an author check.")
    out(f"Output of ai_proof_check_appendix_20261123.py (seed base {SEED}; numpy {np.__version__}, scipy {scipy.__version__}, "
        f"sympy {sp.__version__}, mpmath {mpmath.__version__}).")
    symbolic()
    n1()
    n2()
    n3()
    n4()
    n5()
    n6()
    n7()
    n8()
    n9()
    print(f"total run time {time.time() - T0:.0f} s", file=sys.stderr)  # stderr, so that the output file is byte-reproducible
