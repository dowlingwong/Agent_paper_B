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


if __name__ == "__main__" and "--symbolic-only" in sys.argv:
    symbolic()
