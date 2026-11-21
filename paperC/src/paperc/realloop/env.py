"""A multi-step real-loop environment over an injected runner (design note §6). ENGINEERING_ONLY.

One episode is one campaign on one instance. At each proposal the policy chooses E1 (``execute`` or ``skip``); after
an ``ok`` run it chooses E2 (``keep`` or ``discard``). The controller, not the policy, charges the campaign budget
(``CampaignBudget``), attributes each run (``reward.attribute`` under the declared RL-INFRA policy), folds the
parent's example budget into the outcome (``budget.classify_run``), and ends the episode:

* terminated when W or the call cap is exhausted; the terminal reward is the audited increment of the final
  incumbent (the runner's ``audit``), so a policy is paid only for what an audit confirms;
* truncated on a ``truncate`` attribution (no terminal reward; the episode is dropped from training and counted);
* STOP on a ``stop`` attribution (``EnvStop``).

``mode="train"`` refuses an instance outside the training split (``split_of``), so learning never touches dev or
test campaigns. The runner protocol (``Runner``) is what the B11 real-loop runner implements against the pinned
harness; the tests use a fake one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from paperc.realloop import budget as B
from paperc.realloop import reward as R

N_FEATURES = 6


class EnvStop(RuntimeError):
    """A protocol STOP inside an episode."""


@dataclass(frozen=True)
class Proposal:
    hash: str
    forecast_mean: float = 0.0     # a belief model's predicted increment, sigma units (state, not outcome)
    duplicate: bool = False


class Runner(Protocol):
    def propose(self) -> Proposal: ...

    def run(self, proposal: Proposal, budget: B.ExampleBudget) -> R.RunRecord: ...

    def control_rerun(self) -> R.RunRecord: ...

    def audit(self, incumbent_hash: str | None) -> tuple[float, float]: ...   # (y_terminal, y_start)


@dataclass
class Step:
    obs: np.ndarray
    phase: str            # "E1" | "E2"
    action: str
    reward: float


@dataclass
class Episode:
    instance: str
    steps: list[Step] = field(default_factory=list)
    end: str | None = None            # "terminated" | "truncated"
    end_reason: str | None = None
    attributions: dict[str, int] = field(default_factory=dict)

    @property
    def ret(self) -> float:
        return float(sum(s.reward for s in self.steps))


class RealLoopEnv:
    def __init__(self, runner: Runner, *, instance: str, split_of: dict[str, str], W: int, N: int,
                 reward: R.RewardSpec, infra_policy: str, example_budget: tuple[int, int], mode: str = "train",
                 seed: int = 0):
        if mode not in ("train", "eval"):
            raise ValueError(f"mode {mode!r}")
        if mode == "train" and split_of.get(instance) != "train":
            raise EnvStop(f"{instance} is not a training instance ({split_of.get(instance)!r}); RL trains on the "
                          f"training split only")
        if infra_policy not in R.INFRA_POLICIES:
            raise R.RewardError(f"RL-INFRA policy {infra_policy!r} is not allowed")
        self.runner, self.instance, self.reward, self.infra_policy = runner, instance, reward, infra_policy
        self.budget = B.CampaignBudget(W, N)
        self.example_budget, self.seed = example_budget, seed
        self.incumbent: str | None = None
        self.incumbent_value: float | None = None
        self.keeps = 0
        self.episode = Episode(instance)
        self._pending: tuple[Proposal, R.RunRecord] | None = None
        self._proposal: Proposal | None = None

    # ------------------------------------------------------------------ observations
    def _obs(self, phase: str, proposal: Proposal | None, delta: float | None) -> np.ndarray:
        b = self.budget
        return np.array([1.0 if phase == "E2" else 0.0, (b.W - b.runs_used) / b.W, (b.N - b.calls_used) / b.N,
                         0.0 if proposal is None else proposal.forecast_mean, 0.0 if delta is None else delta,
                         self.keeps / max(1, b.W)], dtype=float)

    def reset(self) -> tuple[np.ndarray, str]:
        return self._next_proposal()

    def _next_proposal(self) -> tuple[np.ndarray, str]:
        self.budget.charge_call()
        self._proposal = self.runner.propose()
        return self._obs("E1", self._proposal, None), "E1"

    # ------------------------------------------------------------------ transitions
    def _count(self, attribution: str) -> None:
        self.episode.attributions[attribution] = self.episode.attributions.get(attribution, 0) + 1

    def _finish(self, kind: str, reason: str) -> None:
        self.episode.end, self.episode.end_reason = kind, reason

    def step(self, action: str):
        """Apply ``action`` to the current decision; returns (obs, phase, reward, done)."""
        if self.episode.end is not None:
            raise EnvStop("the episode has ended")
        if self._pending is None:
            obs_before = self._obs("E1", self._proposal, None)
            if action not in ("execute", "skip"):
                raise ValueError(f"E1 action {action!r}")
            reward = 0.0
            if action == "execute" and not self.budget.can_run(1):
                action = "skip"            # the controller refuses a run beyond W; the policy cannot override
            if action == "execute":
                ex = B.ExampleBudget(*self.example_budget, seed=self.seed + self.budget.runs_used)
                run = self.runner.run(self._proposal, ex)
                kind, reason = B.classify_run(run.kind, run.reason, ex.record())
                run = R.RunRecord(kind, reason, run.value if kind == R.OK else None, run.runs_consumed, run.edited,
                                  run.host)
                control = self.runner.control_rerun() if (
                    self.infra_policy == "control_rerun" and run.kind == R.INFRA and run.edited
                    and run.reason in R.WORKER_PRODUCIBLE and not run.host.any()) else None
                att = R.attribute(run, policy=self.infra_policy, control=control)
                self._count(att)
                if att == "stop":
                    raise EnvStop(f"protocol STOP: {run.kind}/{run.reason}")
                if att == "truncate":
                    self.episode.steps.append(Step(obs_before, "E1", action, 0.0))
                    self._finish("truncated", "infrastructure")
                    return None, None, 0.0, True
                self.budget.charge_runs(run.runs_consumed)
                reward = self.reward.step(att, run.runs_consumed)
                self.episode.steps.append(Step(obs_before, "E1", action, reward))
                if att == "ok":
                    delta = None if self.incumbent_value is None else run.value - self.incumbent_value
                    self._pending = (self._proposal, run)
                    return self._obs("E2", self._proposal, delta), "E2", reward, False
            else:
                self.episode.steps.append(Step(obs_before, "E1", action, reward))
            return self._advance(reward)
        proposal, run = self._pending
        delta = None if self.incumbent_value is None else run.value - self.incumbent_value
        obs_before = self._obs("E2", proposal, delta)
        if action not in ("keep", "discard"):
            raise ValueError(f"E2 action {action!r}")
        if action == "keep":
            self.incumbent, self.incumbent_value, self.keeps = proposal.hash, run.value, self.keeps + 1
        self.episode.steps.append(Step(obs_before, "E2", action, 0.0))
        self._pending = None
        return self._advance(0.0)

    def _advance(self, reward: float):
        reason = self.budget.end_reason()
        if reason is None:
            obs, phase = self._next_proposal()
            return obs, phase, reward, False
        y_terminal, y_start = self.runner.audit(self.incumbent)
        terminal = self.reward.terminal(y_terminal, y_start)
        self.episode.steps[-1].reward += terminal
        self._finish("terminated", reason)
        return None, None, reward + terminal, True
