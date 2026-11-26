"""T3: Monte-Carlo simulator of the governed loop under the T2 Gaussian model (ENGINEERING_ONLY).

It checks T2's statements at campaign level, where the one-trial algebra does
not reach:
- Proposition 4: in the fresh-draw regime, a noise-inflated incumbent record
  stalls later true improvements; CRN damps the effect by (1 - rho);
- Proposition 5 / H4: under a fixed run budget, verify pays off only when
  fresh proposals are poor (diminishing returns) or the stagnation
  externality is large.

Model per campaign:
- true value J(c); proposals Delta ~ N(mu0 - kappa * gain_so_far, tau^2), where
  kappa > 0 gives diminishing returns;
- regime "fresh": every run draws e ~ N(0, sigma^2), so the incumbent's record
  is a stale draw;
- regime "crn": a config's error is e_c = rho * e_inc + sigma * sqrt(1 - rho^2) * u,
  fixed per config (a local edit of the incumbent), so it is reproduced on re-run;
- verify(r): r paired fresh differences, D_i = Delta + N(0, 2 sigma^2 (1 - rho)),
  keep iff mean(D) > 0. In the fresh regime the incumbent's record is then
  re-measured: B is set to the verified candidate's mean fresh metric.

Policies at E2: ``rho`` (never verify), ``always`` (verify every feasible
trial), ``margin`` (verify iff |Delta_hat| < z * sigma_d) and ``kg`` (the T2
index with the true parameters and the stationary price g).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r1.theory.acceptance import NodeNoise, run_price, verify_voi


@dataclass(frozen=True)
class SimConfig:
    regime: str = "crn"          # "crn" or "fresh"
    sigma: float = 0.0125         # per-run noise sd
    rho: float = 0.8              # CRN correlation of a local edit with its incumbent
    mu0: float = 0.0
    tau: float = 0.009
    kappa: float = 0.0            # diminishing returns: mu0 falls by kappa per unit of true gain
    runs: int = 40
    r: int = 2
    policy: str = "rho"
    z: float = 0.5
    seed: int = 0


def _sigma_d(cfg: SimConfig) -> float:
    return cfg.sigma * math.sqrt(2.0 * (1.0 - cfg.rho)) if cfg.regime == "crn" else cfg.sigma * math.sqrt(2.0)


def simulate(cfg: SimConfig, n_campaigns: int = 2000) -> dict:
    rng = np.random.default_rng(cfg.seed)
    sd = _sigma_d(cfg)
    nn = NodeNoise(mu0=cfg.mu0, tau=cfg.tau, sigma_t=sd / math.sqrt(2), sigma_s=sd / math.sqrt(2))
    g = run_price(nn)
    finals, verifies, keeps, false_keeps, bias_end = [], [], [], [], []
    accept_by_t = np.zeros(cfg.runs)
    seen_by_t = np.zeros(cfg.runs)
    for _ in range(n_campaigns):
        J, gain, runs, t = 0.0, 0.0, 0, 0
        e_inc = rng.normal(0, cfg.sigma)          # record error of the start config
        B = J + e_inc
        n_ver = n_keep = n_false = 0
        while runs < cfg.runs:
            delta = rng.normal(cfg.mu0 - cfg.kappa * gain, cfg.tau)
            if cfg.regime == "crn":
                e_c = cfg.rho * e_inc + cfg.sigma * math.sqrt(1 - cfg.rho ** 2) * rng.normal()
            else:
                e_c = rng.normal(0, cfg.sigma)
            m = J + delta + e_c
            runs += 1
            dhat = m - B
            if delta > 0:
                accept_by_t[min(t, cfg.runs - 1)] += dhat > 0
                seen_by_t[min(t, cfg.runs - 1)] += 1
            remaining = cfg.runs - runs
            do_verify = False
            if remaining >= 2 * cfg.r:
                if cfg.policy == "always":
                    do_verify = True
                elif cfg.policy == "margin":
                    do_verify = abs(dhat) < cfg.z * sd
                elif cfg.policy == "kg":
                    do_verify = verify_voi(dhat, nn, cfg.r, "vary") > 2 * cfg.r * g
            if do_verify:
                runs += 2 * cfg.r
                n_ver += 1
                dbar = delta + rng.normal(0, sd / math.sqrt(cfg.r))
                keep = dbar > 0
            else:
                keep = dhat > 0
            if keep:
                n_keep += 1
                n_false += delta <= 0
                J += delta
                gain += delta
                e_inc = e_c
                if do_verify and cfg.regime == "fresh":
                    e_inc = rng.normal(0, cfg.sigma / math.sqrt(cfg.r))  # re-measured incumbent
                B = J + e_inc
            t += 1
        finals.append(J)
        verifies.append(n_ver)
        keeps.append(n_keep)
        false_keeps.append(n_false)
        bias_end.append(B - J)
    finals = np.array(finals)
    with np.errstate(invalid="ignore", divide="ignore"):
        acc = np.where(seen_by_t > 0, accept_by_t / seen_by_t, np.nan)
    return {"mean_final": float(finals.mean()), "se_final": float(finals.std(ddof=1) / math.sqrt(len(finals))),
            "mean_verifies": float(np.mean(verifies)), "mean_keeps": float(np.mean(keeps)),
            "false_keep_rate": float(np.sum(false_keeps) / max(np.sum(keeps), 1)),
            "mean_record_bias_end": float(np.mean(bias_end)), "acceptance_of_true_improvements_by_trial": acc.tolist(),
            "g": g, "sigma_d": sd}
