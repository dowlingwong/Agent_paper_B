"""Numerical checks for the author's proof check of T4 Propositions 7 and 9. ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 22 Nov 2026). These checks support the proof check; they do not replace it.
Run: python3 check_p07_p09.py   (NumPy and SciPy; about 20 s plus about 20 s for the R1-THEORY-RHO check; fixed seeds)
"""
import numpy as np
from scipy import integrate
from scipy.stats import norm

rng = np.random.default_rng(20261122)


def V(t, mu, tau, sigma):
    s = np.hypot(tau, sigma)
    z = (t - mu) / s
    return mu * norm.sf(z) + tau ** 2 / s * norm.pdf(z)


def prop7(cases=2000):
    """Identity and both bounds of Proposition 7 (per unit of 1 - pi), on random parameters."""
    worst_identity, lower_fail, upper_fail = 0.0, 0, 0
    for _ in range(cases):
        mu, tau, sigma = rng.normal(0, 1), rng.uniform(0.2, 2), rng.uniform(0.2, 2)
        s = np.hypot(tau, sigma)
        t_star = -mu * sigma ** 2 / tau ** 2
        t_tilde = t_star + rng.normal(0, 2)
        gap = V(t_star, mu, tau, sigma) - V(t_tilde, mu, tau, sigma)
        f = lambda u: norm.pdf(u, mu, s)
        oriented, _ = integrate.quad(lambda u: f(u) * (t_star - u), t_tilde, t_star, epsabs=1e-13, epsrel=1e-12)
        identity = tau ** 2 / s ** 2 * oriented
        worst_identity = max(worst_identity, abs(gap - identity))
        lo, hi = sorted((t_tilde, t_star))
        f_min = min(f(lo), f(hi))  # a normal density on an interval is smallest at an endpoint
        lower = tau ** 2 / (2 * s ** 2) * f_min * (t_star - t_tilde) ** 2
        upper = tau ** 2 * (t_star - t_tilde) ** 2 / (2 * np.sqrt(2 * np.pi) * s ** 3)
        lower_fail += gap < lower - 1e-12
        upper_fail += gap > upper + 1e-12
    return worst_identity, lower_fail, upper_fail


def prop7_value_formula(n=4_000_000):
    """T2 Proposition 1's closed form for V(t), which Proposition 7 differentiates, against simulation."""
    mu, tau, sigma, t = -0.4, 0.7, 1.1, 0.3
    delta = rng.normal(mu, tau, n)
    hat = delta + rng.normal(0, sigma, n)
    x = delta * (hat > t)
    return V(t, mu, tau, sigma), x.mean(), x.std() / np.sqrt(n)


def mills(a):
    return norm.pdf(a) / norm.sf(a)


def prop9_formula(n=4_000_000):
    """Proposition 9's conditional mean under its own kernel, for fixed (e, Delta, rho)."""
    rows = []
    for e, delta, rho, sigma in ((0.5, 0.0, 0.3, 1.0), (0.0, 0.4, 0.0, 1.0), (-0.8, -0.2, 0.6, 1.5), (1.2, 0.0, 0.9, 1.0)):
        sc = sigma * np.sqrt(1 - rho ** 2)
        eps = rho * e + sc * rng.normal(size=n)
        keep = delta + eps - e > 0
        a = ((1 - rho) * e - delta) / sc
        formula = rho * e + sc * mills(a)
        se = eps[keep].std() / np.sqrt(keep.sum())
        rows.append((e, delta, rho, formula, eps[keep].mean(), se, formula > max(e - delta, rho * e)))
    return rows


def prop9_second_keep(n=20_000_000, rho=0.5, sigma=1.0):
    """Does the kernel eps | e ~ N(rho e, sigma_c^2) still hold when e is itself a kept (selected) error?

    Model: a component u shared by all runs of the campaign, plus independent run noise v, with
    Var u = rho sigma^2 and Var v = (1 - rho) sigma^2, so that two unselected errors have correlation rho.
    Null proposals (Delta = 0). e0 is unselected; e1 is the error kept at the first keep; the question is the
    law of a fresh candidate's error given e1.
    """
    u = rng.normal(0, np.sqrt(rho) * sigma, n)
    v0, v1, v2 = (rng.normal(0, np.sqrt(1 - rho) * sigma, n) for _ in range(3))
    e0, e1, cand = u + v0, u + v1, u + v2
    first_keep = e1 > e0
    rows = []
    for lo, hi in ((-1.0, -0.8), (-0.1, 0.1), (0.8, 1.0), (1.8, 2.0)):
        unsel = (e0 > lo) & (e0 < hi)
        sel = first_keep & (e1 > lo) & (e1 < hi)
        mid = (lo + hi) / 2
        rows.append((mid, rho * mid, cand[unsel].mean(),
                     cand[sel].mean(), cand[sel].std() / np.sqrt(sel.sum())))
    # pathwise part: on every keep with Delta = 0 the new record error exceeds the old one
    second_keep = first_keep & (cand > e1)
    return rows, bool(np.all(e1[first_keep] > e0[first_keep])), bool(np.all(cand[second_keep] > e1[second_keep]))


def prop9_kernel_free(n=2_000_000, trials=12, rho=0.5, sigma=1.0, tau=0.5):
    """Kernel-free Proposition 9 (restated 22 Nov 2026, R1-THEORY-RHO) under the shared-component model.

    Added 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked. Uses its own generator, so the
    output lines above are unchanged.
    Model: every run's error is u + v, u shared by the campaign (Var rho sigma^2), v fresh per run
    (Var (1 - rho) sigma^2). The proposer reads the displayed record B = J(inc) + e: mu_n = +0.2 if
    B <= 0.5, else -0.3; Delta_n ~ N(mu_n, tau^2). Default rule: keep iff Delta_n + eps_n - e > 0.
    Checks, on trials whose record was itself kept at least once (a selected error):
      (i)   e' > e - Delta_n on every keep (pathwise);
      (ii)  in bins of (e, Delta_n): E[e' | keep] > mean of (e - Delta_n) over the bin's keeps, and
            E[e' | keep] > E[eps_n] over the bin (truncation from below raises the mean);
      and the kernel formula rho e + sigma_c lambda(a), which this model does not satisfy after a keep.
    """
    g = np.random.default_rng(2026112202)
    u = g.normal(0, np.sqrt(rho) * sigma, n)
    sv = np.sqrt(1 - rho) * sigma
    e = u + g.normal(0, sv, n)          # unselected initial record
    J = np.zeros(n)
    kept_before = np.zeros(n, dtype=bool)
    rows = {k: [] for k in ("e", "d", "eps", "keep")}
    path_ok, n_keep = True, 0
    for _ in range(trials):
        mu = np.where(J + e <= 0.5, 0.2, -0.3)
        d = mu + tau * g.normal(size=n)
        eps = u + g.normal(0, sv, n)
        keep = d + eps - e > 0
        path_ok &= bool(np.all(eps[keep] > (e - d)[keep]))
        n_keep += int(keep.sum())
        sel = kept_before
        for k, x in (("e", e), ("d", d), ("eps", eps), ("keep", keep)):
            rows[k].append(x[sel])
        J = np.where(keep, J + d, J)
        e = np.where(keep, eps, e)
        kept_before = kept_before | keep
    E, D, EPS, K = (np.concatenate(rows[k]) for k in ("e", "d", "eps", "keep"))
    sc = sigma * np.sqrt(1 - rho ** 2)
    out = []
    for em, dm in ((0.0, 0.0), (0.5, 0.0), (1.0, -0.3), (0.5, 0.4), (-0.5, 0.2)):
        b = (np.abs(E - em) < 0.05) & (np.abs(D - dm) < 0.05)
        bk = b & K
        kept_mean = EPS[bk].mean()
        se = EPS[bk].std() / np.sqrt(bk.sum())
        thr = (E - D)[bk].mean()
        all_mean = EPS[b].mean()
        kernel = rho * em + sc * mills(((1 - rho) * em - dm) / sc)
        out.append((em, dm, int(b.sum()), K[b].mean(), kept_mean, se, thr, all_mean, kernel,
                    kept_mean > max(thr, all_mean)))
    return path_ok, n_keep, out


if __name__ == "__main__":
    ident, lf, uf = prop7()
    print(f"P7 identity: max |gap - integral| = {ident:.2e}; lower-bound failures {lf}; upper-bound failures {uf}")
    closed, sim, se = prop7_value_formula()
    print(f"P7 / T2 P1 value formula: closed form {closed:.5f}, simulation {sim:.5f} (s.e. {se:.5f})")
    print("P9 formula under its own kernel (e, Delta, rho | formula, simulation, s.e., inequality holds):")
    for e, d, r, formula, sim, se, ok in prop9_formula():
        print(f"  e={e:+.1f} Delta={d:+.1f} rho={r:.1f} | {formula:+.5f} {sim:+.5f} {se:.5f} {ok}")
    rows, path1, path2 = prop9_second_keep()
    print("P9 kernel after one keep, shared-component model, rho = 0.5 (e | rho*e, mean of a fresh error given an "
          "UNSELECTED record e, mean given a KEPT record e, s.e.):")
    for mid, target, unsel, sel, se in rows:
        print(f"  e={mid:+.1f} | {target:+.4f} {unsel:+.4f} {sel:+.4f} {se:.4f}")
    print(f"P9 pathwise: e' > e on every null keep: first keep {path1}, second keep {path2}")
    path_ok, n_keep, out = prop9_kernel_free()
    print(f"P9 kernel-free (R1-THEORY-RHO), shared-component model, rho = 0.5, ledger-reading proposer: "
          f"e' > e - Delta on every keep: {path_ok} ({n_keep} keeps)")
    print("  on records kept at least once; bins |e - e0| < 0.05, |Delta - D0| < 0.05 (e0, D0 | rows, P(keep), "
          "E[e'|keep], s.e., mean (e - Delta) over keeps, E[eps] over bin, kernel formula, kernel-free inequality holds):")
    for em, dm, nb, pk, km, se, thr, am, kf, ok in out:
        print(f"  e0={em:+.1f} D0={dm:+.1f} | {nb} {pk:.3f} {km:+.4f} {se:.4f} {thr:+.4f} {am:+.4f} {kf:+.4f} {ok}")
