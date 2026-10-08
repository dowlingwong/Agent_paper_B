"""Scripted two-checkpoint trees with text histories for the configurator scaffold.

ENGINEERING ONLY.  No model is called and nothing here is evidence.  The
generator writes rows in the ``timing.py`` row format (``root_id``, ``family``,
``h1``, ``h2``, ``u_now``, ``u_later``, ``u_never``, ``reached2``) plus
matching decision histories in the serialiser's event format, so the
configurator path (serialise -> encode -> project -> shared ridge heads ->
``evaluate_tree``) can be exercised end to end on CPU.

Scripted law (declared so tests can reason about it):

- each root has a fit quality ``q`` in [0, 1] and a latent ``drift`` flag;
- telemetry ``h1`` carries ``q`` with noise and nothing about ``drift``;
- the checkpoint-1 text names a coarse ``q`` bucket and, with probability
  ``cue_rate``, a drift warning;
- the checkpoint-2 text (continue branch) reveals whether batch 2 shifted;
- verifying now helps low-``q`` roots and is wasted on drifting roots;
  verifying later helps drifting roots.

Outcomes never enter the text: the event kinds allowed by the serialiser cannot
carry a grade, and the generator only writes visible agent/tool messages.
"""

from __future__ import annotations

import numpy as np

from causal_branch.control.configurator.serialiser import DecisionHistory, HistoryEvent

TOOLS = ("fit_candidate", "inspect_features", "summarise_dev", "plot_residuals")


def _bucket(q: float) -> str:
    return "low" if q < 0.4 else ("medium" if q < 0.7 else "high")


def _clip(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def scripted_population(n_families: int = 16, roots_per_family: int = 4, *,
                        seed: int = 20261004, cue_rate: float = 0.8,
                        reach_rate: float = 0.85, noise: float = 0.03):
    """Return ``(rows, histories)`` for a scripted population."""

    rng = np.random.default_rng(seed)
    rows, histories = [], {}
    for f in range(n_families):
        family = f"sfam{f:02d}"
        family_shift = rng.normal(0, 0.05)
        for j in range(roots_per_family):
            rid = f"{family}-r{j}"
            q = float(rng.uniform(0, 1))
            drift = bool(rng.uniform() < 0.4)
            cue = drift and rng.uniform() < cue_rate
            reached2 = bool(rng.uniform() < reach_rate)

            u_never = _clip(0.6 + 0.2 * q - 0.15 * drift + family_shift + rng.normal(0, noise))
            u_now = _clip(u_never + 0.10 * (1 - q) - 0.06 * drift + rng.normal(0, noise))
            u_later = (_clip(u_never + 0.04 * (1 - q) + 0.14 * drift + rng.normal(0, noise))
                       if reached2 else u_never)

            tools = rng.choice(TOOLS, size=3, replace=True)
            ev = [HistoryEvent(0, "task", f"Fit a classifier for template {family}; "
                                          f"submit the candidate with best dev accuracy. root {rid}."),
                  HistoryEvent(1, "tool_call", "fit on dev batch 1", name=str(tools[0])),
                  HistoryEvent(2, "tool_result",
                               f"dev accuracy is {_bucket(q)}; candidate stored", name=str(tools[0])),
                  HistoryEvent(3, "assistant",
                               ("feature distribution warning: drift suspected in incoming data"
                                if cue else "feature distributions look stable so far")),
                  HistoryEvent(4, "tool_call", "inspect current candidate", name=str(tools[1])),
                  HistoryEvent(5, "checkpoint", "checkpoint 1 reached")]
            h1 = DecisionHistory(phase=1, checkpoint_step=5, events=tuple(ev),
                                 redact=(rid, family))
            h2 = None
            if reached2:
                ev2 = ev + [
                    HistoryEvent(6, "observation", "dev batch 2 arrived"),
                    HistoryEvent(7, "tool_call", "evaluate candidate on batch 2", name=str(tools[2])),
                    HistoryEvent(8, "tool_result",
                                 ("batch 2 accuracy dropped sharply: distribution shift confirmed"
                                  if drift else "batch 2 accuracy consistent with batch 1"),
                                 name=str(tools[2])),
                    HistoryEvent(9, "checkpoint", "checkpoint 2 reached")]
                h2 = DecisionHistory(phase=2, checkpoint_step=9, events=tuple(ev2),
                                     redact=(rid, family))
            histories[rid] = (h1, h2)
            tel_q = q + rng.normal(0, 0.2)
            rows.append(dict(
                root_id=rid, family=family,
                h1={"tel_q": float(tel_q), "tel_steps": 5.0},
                h2={"tel_q": float(tel_q), "tel_steps": 5.0, "tel_steps2": 9.0 if reached2 else 0.0},
                u_now=u_now, u_later=u_later, u_never=u_never, reached2=reached2))
    return rows, histories


def split_by_family(rows, n_dev_families: int):
    families = sorted({r["family"] for r in rows})
    dev = set(families[:n_dev_families])
    return ([r for r in rows if r["family"] in dev], [r for r in rows if r["family"] not in dev])
