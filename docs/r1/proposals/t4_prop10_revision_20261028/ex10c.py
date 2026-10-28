# Proposition 10(c) example (T4_PROP10_REVISION_20261028.md, section 4).
# Latent theta ~ N(0,1) shared by two fixed, non-interacting edits:
#   trial 1: Delta_1 = alpha*theta, observed without noise if executed;
#   trial 2: Delta_2 = beta*theta, observed with noise sd sigma_2 = kappa*beta.
# Policies: myopic (Proposition 8'), probe-first, always-execute with Bayes keep.
# Closed forms plus a Monte Carlo check with common random numbers (CRN).
import numpy as np
from scipy.stats import norm

PHI0 = norm.pdf(0.0)


def ex_pos(c):
    """E[(theta - c)^+] for theta ~ N(0,1)."""
    return norm.pdf(c) - c * norm.sf(c)


def closed_form(alpha, beta, kappa, g):
    v1 = alpha * PHI0                                  # V*_1 = E[(alpha theta)^+]
    assert v1 < g, "the example needs g > alpha*phi(0), so the myopic rule skips trial 1"
    v2 = beta * PHI0 / np.sqrt(1.0 + kappa ** 2)       # V*_2 with t* = 0 (uninformed)
    myopic = max(v2 - g, 0.0)
    probe = v1 - g + beta * ex_pos(g / beta)           # learn theta, then execute/keep iff beta*theta > g
    always = (v1 - g) + (beta * PHI0 - g)              # execute both; trial 2 keep uses theta known from trial 1
    return myopic, probe, always


def monte_carlo(alpha, beta, kappa, g, n=2_000_000, seed=0):
    rng = np.random.default_rng(seed)
    th = rng.standard_normal(n)
    h2 = beta * th + kappa * beta * rng.standard_normal(n)
    v2 = beta * PHI0 / np.sqrt(1.0 + kappa ** 2)
    my = (beta * th * (h2 > 0) - g) if v2 >= g else np.zeros(n)   # t* = 0 at trial 2
    pr = -g + alpha * th * (th > 0) + np.where(beta * th > g, beta * th - g, 0.0)
    al = (-g + alpha * th * (th > 0)) + (-g + beta * th * (th > 0))
    se = lambda x: x.std(ddof=1) / np.sqrt(n)
    return {"myopic": (my.mean(), se(my)), "probe": (pr.mean(), se(pr)),
            "always": (al.mean(), se(al)), "loss": ((pr - my).mean(), se(pr - my)),
            "screen_gain": ((my - al).mean(), se(my - al))}


if __name__ == "__main__":
    alpha, g, kappa = 1.0, 0.5, 1.0
    print(f"alpha={alpha} g={g} kappa={kappa}; MC n=2e6 with common random numbers; values: closed form (MC mean +- se)")
    for beta in (2.0, 10.0, 100.0, 1000.0):
        my, pr, al = closed_form(alpha, beta, kappa, g)
        mc = monte_carlo(alpha, beta, kappa, g)
        print(f"beta={beta:g}: myopic={my:.4f} ({mc['myopic'][0]:.4f}+-{mc['myopic'][1]:.4f})  "
              f"probe={pr:.4f} ({mc['probe'][0]:.4f}+-{mc['probe'][1]:.4f})  "
              f"loss={pr - my:.4f} ({mc['loss'][0]:.4f}+-{mc['loss'][1]:.4f})  "
              f"always={al:.4f}  screening gain={my - al:.4f} ({mc['screen_gain'][0]:.4f}+-{mc['screen_gain'][1]:.4f})")
    print("asymptotic loss slope in beta (kappa=1):", PHI0 * (1 - 1 / np.sqrt(2.0)))
    my, pr, al = closed_form(alpha, 10.0, kappa, g)
    v1, v2 = alpha * PHI0, 10.0 * PHI0 / np.sqrt(2.0)
    print("R3 check (beta=10): actual screening gain J(myopic)-J(always) =", round(my - al, 4),
          "; formula sum (g - V*)^+ with myopic V*'s =", round(max(g - v1, 0) + max(g - v2, 0), 4))
