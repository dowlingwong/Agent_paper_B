"""AI-assisted (Claude, coordinating chat, 23 Nov 2026).

Spot check (b) of PLAN row R1-PROOF-POLICY for the appendix statements. Written independently of
ai_proof_check_appendix_20261123.py (no code or numbers imported). Record: SPOT_CHECK_APPENDIX_COORDINATOR_20261123.md.
Run: python3 spot_check_appendix_coordinator_20261123.py > spot_check_appendix_coordinator_20261123_output.txt
"""
import numpy as np
from scipy import integrate, stats

phi, PHI = stats.norm.pdf, stats.norm.cdf


def line(tag, msg):
    print(f"{tag}: {msg}")


def psi(z):
    return phi(z) - z * PHI(-z)


def voi(m, q):
    return q * psi(abs(m) / q) if q > 0 else 0.0


# 1. app-voi: closed form E[M'+] - m+ = q psi(|m|/q) by quadrature; diminishing returns fail.
for m, q in ((0.7, 0.4), (-1.2, 0.9), (0.0, 0.5)):
    num = integrate.quad(lambda x: max(x, 0) * stats.norm.pdf(x, m, q), m - 12 * q, m + 12 * q, points=[0])[0] - max(m, 0)
    line("SC-A1a", f"m={m:+.1f}, q={q}: quadrature {num:.10f}; q psi(|m|/q) {voi(m, q):.10f}")
tau2, sd2, H = 2.0, 1.0, 4.5                          # vary policy: D_i = Delta + xi_i, xi_i ~ N(0, sd2)
v = tau2 * sd2 / (tau2 + sd2)
m = tau2 / (tau2 + sd2) * H
vals = [0.0] + [voi(m, np.sqrt(v**2 / (v + sd2 / r))) for r in range(1, 6)]
inc = np.diff(vals)
line("SC-A1b", f"tau2=2, sd2=1, H=4.5 (m={m}): VoI increments r=1..5 {', '.join(f'{x:.4e}' for x in inc)}; increasing: {bool(np.all(np.diff(inc) > 0))}")
vals0 = [0.0] + [voi(0.0, np.sqrt(v**2 / (v + sd2 / r))) for r in range(1, 6)]
line("SC-A1c", f"same at m=0: increments {', '.join(f'{x:.4e}' for x in np.diff(vals0))} (decreasing)")


# 2. app-split: fixed policy VoI -> 0 as sigma_t -> 0; vary policy keeps a positive limit at fixed H.
def split_q2(tau2, st2, ss2, r, policy):
    # Delta, e_t, e_s, xi independent; H = Delta + e_t + e_s.
    # fixed: D_i = Delta + e_s + xi_i, xi ~ N(0, st2); vary: D_i = Delta + xi_i, xi ~ N(0, st2 + ss2).
    varH = tau2 + st2 + ss2
    if policy == "fixed":
        covDH, covDdelta, varD = tau2 + ss2, tau2, tau2 + ss2 + st2 / r
    else:
        covDH, covDdelta, varD = tau2, tau2, tau2 + (st2 + ss2) / r
    # conditional on H: Var(D|H), Cov(Delta, D|H)
    vD = varD - covDH**2 / varH
    cDd = covDdelta - covDH * tau2 / varH
    return cDd**2 / vD if vD > 0 else 0.0


for st2 in (1e-1, 1e-3, 1e-6):
    qf = np.sqrt(split_q2(1.0, st2, 0.5, 2, "fixed"))
    qv = np.sqrt(split_q2(1.0, st2, 0.5, 2, "vary"))
    line("SC-A2", f"sigma_t^2={st2:g}: max_H VoI fixed <= q phi(0) = {qf*phi(0):.3e}; vary q = {qv:.4f}, VoI at H=0 {voi(0.0, qv):.4f}")


# 3. app-record: after one null keep from an unselected record (rho = 0), e is not N(0, sigma^2) given the history,
#    but the kernel (fresh candidate independent of e) still gives the keep probability.
rng = np.random.default_rng(23)
n = 4_000_000
e0, eps = rng.normal(0, 1, n), rng.normal(0, 1, n)
keep = eps - e0 > 0
e1 = eps[keep]
line("SC-A3a", f"rho=0, sigma=1, one null keep: E[e | keep] {e1.mean():.4f} (1/sqrt(pi) = {1/np.sqrt(np.pi):.4f}); Var {e1.var():.4f} (1 - 1/pi = {1-1/np.pi:.4f})")
h = (eps - e0)[keep]
sel = np.abs(h - 1.0) < 0.02
line("SC-A3b", f"given h ~ 1.0: E[e | h] {e1[sel].mean():.4f} (h/2 = 0.5), Var {e1[sel].var():.4f} (1/2)")
# Keep probability of a later fixed-delta proposal given e: kernel formula vs simulation at rho = 0.6.
rho, delta, sig = 0.6, 0.3, 1.0
for e in (-0.5, 0.0, 0.8):
    sim = (delta + rho * e + sig * np.sqrt(1 - rho**2) * rng.normal(0, 1, 2_000_000) - e > 0).mean()
    line("SC-A3c", f"rho=0.6, delta=0.3, e={e:+.1f}: Phi formula {PHI((delta-(1-rho)*e)/(sig*np.sqrt(1-rho**2))):.4f}; MC {sim:.4f}")


# 4. app-verify: VoI <= q phi(0) <= sqrt(v) phi(0); supremum phi(0) sigma_d sqrt(r/(r+1)) under vary.
for r in (1, 2, 3):
    sups = []
    for tau2 in (1.0, 10.0, 1e4):
        v = tau2 * 1.0 / (tau2 + 1.0)
        q = np.sqrt(v**2 / (v + 1.0 / r))
        sups.append(q * phi(0))
    line("SC-A4", f"r={r}: max_m VoI = q phi(0) at tau2 = 1, 10, 1e4: {', '.join(f'{x:.4f}' for x in sups)}; limit phi(0) sqrt(r/(r+1)) = {phi(0)*np.sqrt(r/(r+1)):.4f}")


# 5. app-rules (ii): a duplicate under the Bayes keep rule can be worth E[Delta | O]+ - g > 0.
mu, t2, s2, hprev, g = 1.0, 1.0, 1.0, -0.1, 0.1
post = mu + t2 / (t2 + s2) * (hprev - mu)
line("SC-A5a", f"duplicate with recorded comparison {hprev}, forecast mu=1, tau=sigma=1: E[Delta|O] = {post:.3f}; value of executing under Bayes keep {max(post,0)-g:+.3f} (claimed -g = {-g})")
# (iii) default rule: the record never decreases, so a duplicate's metric is <= the current record and its comparison
#       is <= 0. Toy bit-exact ledger: a configuration's metric is fixed at its first evaluation.
rng2 = np.random.default_rng(5)
B, ledger, dups, viol, viol_loose = -np.inf, {}, 0, 0, 0
for k in range(200_000):
    cfg = int(rng2.integers(0, 300))
    if cfg in ledger:
        dups += 1
        viol += ledger[cfg] > B
        continue
    ledger[cfg] = rng2.normal(0, 1)
    if ledger[cfg] > B:
        B = ledger[cfg]
# A looser rule (keep iff comparison > -0.5) lets the record fall, after which duplicates can beat it.
rng3 = np.random.default_rng(5)
B2, ledger2 = -np.inf, {}
for k in range(200_000):
    cfg = int(rng3.integers(0, 300))
    first = cfg not in ledger2
    val = ledger2.setdefault(cfg, rng3.normal(0, 1))
    if not first:
        viol_loose += val > B2
    if val - B2 > -0.5:
        B2 = val
line("SC-A5b", f"duplicates proposed {dups}; with comparison > 0 under the default rule: {viol}; under keep iff comparison > -0.5: {viol_loose}")


# 6. Edge cases of prop:onestep: without exact no-op observation, separation fails and the rule can discard.
pi, mu, tau, sig = 0.3, 0.1, 1.0, 1.0
for hh in (-3.0, 0.0, 2.0):
    f1 = stats.norm.pdf(hh, mu, np.hypot(tau, sig))
    f0 = stats.norm.pdf(hh, 0, sig)
    p1 = (1 - pi) * f1 / ((1 - pi) * f1 + pi * f0)
    m1 = mu + tau**2 / (tau**2 + sig**2) * (hh - mu)
    line("SC-A6", f"pi=0.3, mu=0.1, tau=sigma=1, no-op observed as N(0,1): H={hh:+.1f}: P(non-no-op|H) {p1:.4f}, m_n {p1*m1:+.4f}")


# 7. Summed gains (alpha = 1, beta = 10, kappa = 1, g = 0.5).
a, b, k, g = 1.0, 10.0, 1.0, 0.5
J1 = max(b * phi(0) / np.sqrt(1 + k**2) - g, 0)
Jall = a * phi(0) + b * phi(0) - 2 * g
line("SC-A7", f"one-step {J1:.4f}; always execute + Bayes keep {Jall:.4f}; difference {J1-Jall:.6f}; sum (g - V*)+ = {g - a*phi(0):.4f}")


# 9. Information example: table row beta = 10 and the slope phi(g/beta) - phi(0)/sqrt(2).
probe = a * phi(0) - g + b * phi(g / b) - g * PHI(-g / b)
line("SC-A9a", f"beta=10: one-step {J1:.4f}, probe-first {probe:.4f}, gap {probe-J1:.4f}")
for bb in (2.0, 10.0, 100.0, 1e4):
    line("SC-A9b", f"beta={bb:g}: slope of the gap {phi(g/bb) - phi(0)/np.sqrt(2):.5f} (limit {phi(0)*(1-1/np.sqrt(2)):.5f})")
# Numeric derivative check of d/dbeta [beta psi(g/beta)] = phi(g/beta) at beta = 3.
f = lambda bb: bb * psi(g / bb)
line("SC-A9c", f"beta=3: numeric derivative {(f(3+1e-6)-f(3-1e-6))/2e-6:.8f}; phi(g/beta) {phi(g/3):.8f}")
