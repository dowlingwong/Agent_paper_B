"""Alternative verify *responses* (they need their own harness action version under D4).

The harness's frozen verify response keeps iff the mean paired difference is
positive.  A PACE-style gate and a racing rule are different responses, so
under D4 each would be a separately declared action version
(``verify:pace``, ``verify:race``).  They cannot be scored on a table that
branched only the frozen response; their decision logic lives here, tested on
its own, so the harness can adopt them as action versions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PaceStyleGate:
    """Anytime-valid paired test by betting (PACE-style; after arXiv 2606.08106, not a reproduction).

    Paired differences d_i are clipped to [-c, c] and scaled to [-1, 1]. The
    wealth process K_n = prod(1 + lambda_i * d_i / c), with a predictable
    lambda_i in [0, 1/2] (the running-mean plug-in, truncated), is a test
    supermartingale under H0: E[clip(d)] <= 0 (Waudby-Smith & Ramdas, JRSS-B 2024).
    Note: that is the null for the *clipped* difference; a skewed null with
    E[d] <= 0 can have a positive clipped mean (L14 finding 15).
    Commit iff K_n >= 1/alpha within the run cap. Ville's inequality bounds the
    false-commit probability by alpha under optional stopping.
    """

    alpha: float = 0.1
    clip: float = 0.05     # metric units; paired differences beyond this are clipped
    max_pairs: int = 8

    def decide(self, diffs: list[float]) -> tuple[str, float, int]:
        wealth, seen = 1.0, []
        for i, d in enumerate(diffs[: self.max_pairs]):
            x = float(np.clip(d, -self.clip, self.clip)) / self.clip
            lam = 0.0 if not seen else float(np.clip(np.mean(seen), 0.0, 0.5))
            wealth *= 1.0 + lam * x
            seen.append(x)
            if wealth >= 1.0 / self.alpha:
                return "commit", wealth, i + 1
        return "reject", wealth, min(len(diffs), self.max_pairs)


@dataclass(frozen=True)
class RacingRule:
    """Racing-style paired rule (after Hoeffding races / F-Race): sample pairs until a
    one-sided t-interval excludes zero or the cap is reached; ties keep the incumbent."""

    min_pairs: int = 2
    max_pairs: int = 8
    z: float = 1.645

    def decide(self, diffs: list[float]) -> tuple[str, int]:
        for n in range(self.min_pairs, min(len(diffs), self.max_pairs) + 1):
            d = np.asarray(diffs[:n], dtype=float)
            sd = float(np.std(d, ddof=1)) if n > 1 else math.inf
            half = self.z * sd / math.sqrt(n) if sd > 0 else 0.0
            if d.mean() - half > 0:
                return "commit", n
            if d.mean() + half < 0:
                return "reject", n
        return "reject", min(len(diffs), self.max_pairs)
