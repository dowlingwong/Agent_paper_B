"""A tiny CPU policy-gradient trainer for ``RealLoopEnv`` (design note §7, RL-ALGO). ENGINEERING_ONLY.

A mechanism check, not a proposed method: a linear-softmax policy per phase (E1: execute/skip; E2: keep/discard),
REINFORCE with a leave-one-out batch baseline (the R-B update's baseline, without clipping), trained only on
training-split instances. Truncated episodes are dropped from the gradient and counted (addendum 19 Nov §C); the
truncation rate is reported. The real methods for Q3 are the offline learners of P8 (R0 FQI, R1 IQL) trained on
logged campaigns with the same reward (``reward``), layout and budget rules.
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
    obs, phase = env.reset()
    trace = []
    done = False
    while not done:
        action, i = policy.act(obs, phase, rng)
        trace.append((obs, phase, i))
        obs, phase, _, done = env.step(action)
    return env.episode, trace


def reinforce(make_env: Callable[[str, int], E.RealLoopEnv], instances: list[str], split_of: dict[str, str], *,
              iterations: int, batch: int, lr: float, seed: int = 0) -> dict:
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
    for it in range(iterations):
        episodes = []
        truncated = 0
        while len(episodes) < batch:
            inst = instances[k % len(instances)]
            ep, trace = rollout(make_env(inst, k), policy, rng)
            k += 1
            if ep.end == "truncated":
                truncated += 1
                if truncated > 10 * batch:
                    raise E.EnvStop("every episode truncates; STOP")
                continue
            episodes.append((ep.ret, trace))
        rets = np.array([r for r, _ in episodes])
        grads = {p: np.zeros_like(w) for p, w in policy.weights.items()}
        for j, (ret, trace) in enumerate(episodes):
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
                    "truncation_rate": truncated / (truncated + len(episodes))})
    return {"policy": policy, "log": log}
