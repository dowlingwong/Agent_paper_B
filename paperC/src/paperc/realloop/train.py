"""A tiny CPU policy-gradient trainer for ``RealLoopEnv`` (design note §7, RL-ALGO). ENGINEERING_ONLY.

A mechanism check, not a proposed method: a linear-softmax policy per phase (E1: execute/skip; E2: keep/discard),
REINFORCE with a leave-one-out batch baseline (the R-B update's baseline, without clipping), trained only on
training-split instances. The environment asks the policy only at feasible decisions (an ``execute`` that would not
fit in W is a rule-forced row there), so every sampled action is credited; a mismatch between the sampled and the
taken action is a STOP.

Truncated episodes: this is a Monte Carlo method, so a truncated episode is left out of the gradient (plan §3.1:
"Monte Carlo targets drop it, and the drop is reported per arm") and counted. Because dropping is only safe if
truncation does not depend on the outcome, the trainer enforces the declared truncation level: a STOP when the
cumulative truncation rate exceeds ``trunc_level`` (once ``min_episodes`` episodes were drawn) or when more than half
of one iteration's draws truncate. The rate is reported with every iteration's return. The real methods for Q3 are
P8's offline learners (R0 FQI, R1 IQL), which bootstrap at a truncated episode's last observed state (plan §3.1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from paperc.realloop import env as E

ACTIONS = {"E1": ("execute", "skip"), "E2": ("keep", "discard")}


@dataclass
class LinearPolicy:
    weights: dict[str, np.ndarray] = field(default_factory=lambda: {p: np.zeros((2, E.N_FEATURES + 1))
                                                                    for p in ACTIONS})

    def probs(self, obs: np.ndarray, phase: str) -> np.ndarray:
        z = self.weights[phase] @ np.append(obs, 1.0)
        z = z - z.max()
        e = np.exp(z)
        return e / e.sum()

    def act(self, obs, phase, rng) -> tuple[str, int]:
        p = self.probs(obs, phase)
        i = int(rng.choice(2, p=p))
        return ACTIONS[phase][i], i


def rollout(env: E.RealLoopEnv, policy: LinearPolicy, rng) -> tuple[E.Episode, list[tuple[np.ndarray, str, int]]]:
    """One episode and the trace of the policy's decisions."""
    obs, phase = env.reset()
    trace = []
    done = obs is None
    while not done:
        action, i = policy.act(obs, phase, rng)
        next_obs, next_phase, _, done, taken = env.step(action)
        if taken != action:
            raise E.EnvStop(f"the environment took {taken!r} for the sampled {action!r}")
        trace.append((obs, phase, i))
        obs, phase = next_obs, next_phase
    return env.episode, trace


def reinforce(make_env: Callable[[str, int], E.RealLoopEnv], instances: list[str], split_of: dict[str, str], *,
              iterations: int, batch: int, lr: float, seed: int = 0, trunc_level: float = 0.05,
              min_episodes: int = 20) -> dict:
    """Train on ``instances`` (all must be in the training split); returns the policy and a log."""
    outside = sorted(i for i in instances if split_of.get(i) != "train")
    if outside:
        raise E.EnvStop(f"non-training instances given to the trainer: {outside[:3]}")
    if batch < 2:
        raise ValueError("the leave-one-out baseline needs batch >= 2")
    rng = np.random.default_rng(seed)
    policy = LinearPolicy()
    log = []
    k = 0
    drawn = truncated_total = 0
    for it in range(iterations):
        episodes = []
        truncated = 0
        while len(episodes) < batch:
            inst = instances[k % len(instances)]
            ep, trace = rollout(make_env(inst, k), policy, rng)
            k += 1
            drawn += 1
            if ep.end == "truncated":
                truncated += 1
                truncated_total += 1
                if truncated > batch:
                    raise E.EnvStop(f"STOP: more than half of iteration {it}'s draws truncate")
                if drawn >= min_episodes and truncated_total / drawn > trunc_level:
                    raise E.EnvStop(f"STOP: cumulative truncation rate {truncated_total / drawn:.3f} > {trunc_level}")
                continue
            episodes.append((ep.ret, trace))
        if drawn >= min_episodes and truncated_total / drawn > trunc_level:
            raise E.EnvStop(f"STOP: cumulative truncation rate {truncated_total / drawn:.3f} > {trunc_level}")
        rets = np.array([r for r, _ in episodes])
        grads = {p: np.zeros_like(w) for p, w in policy.weights.items()}
        for ret, trace in episodes:
            adv = ret - (rets.sum() - ret) / (len(rets) - 1)
            for obs, phase, i in trace:
                x = np.append(obs, 1.0)
                p = policy.probs(obs, phase)
                g = -np.outer(p, x)
                g[i] += x
                grads[phase] += adv * g
        for p in policy.weights:
            policy.weights[p] += lr * grads[p] / len(episodes)
        log.append({"iteration": it, "mean_return": float(rets.mean()), "truncated": truncated,
                    "truncation_rate": truncated / (truncated + len(episodes)),
                    "cumulative_truncation_rate": truncated_total / drawn})
    return {"policy": policy, "log": log}
