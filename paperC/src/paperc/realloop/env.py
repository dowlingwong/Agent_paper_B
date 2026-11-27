"""A multi-step real-loop environment over an injected runner (design note §6). ENGINEERING_ONLY.

One episode is one campaign on one instance. Each manager call yields a proposal. A proposal the harness does not run
(diff refused for scope, inert, a duplicate of an evaluated code state, an invalid proposal) is rule-forced: it
charges the call and no run, and the policy makes no decision on it. Otherwise the policy chooses E1 (``execute`` or
``skip``); after an ``ok`` run it chooses E2 (``keep`` or ``discard``); after a proposal failure the E2 row is a forced
``discard`` (the schema's row rule). The controller, not the policy:

* does not ask the policy about a proposal whose declared run cost (``Proposal.max_runs``) does not fit in what is
  left of W: it is a rule-forced ``skip`` (``over_budget``), so no action is credited at an infeasible state; a run
  that consumes more than it declared is a protocol STOP;
* attributes the whole ``execute`` (``reward.attribute_attempts``: the first attempt decides, every attempt is
  charged, an attempt after an ``ok`` is a STOP, the parent's example record applied to the deciding attempt);
* registers the start configuration and every executed code state as evaluated (a later proposal of one is a
  duplicate: not run);
* ends the episode: terminated when W or the call cap is exhausted, with the audited increment of the final incumbent
  as the terminal reward; truncated with reason ``host`` on host-evidenced faults or ``infrastructure`` on a launch
  error or a failure of trusted code (no terminal reward; a truncated episode's ``ret`` is 0 and meaningless);
  truncated with reason ``protocol_stop`` on a STOP, recorded before ``EnvStop`` is raised.

``step`` returns the action actually taken, so a learner credits what happened. ``mode="train"`` refuses an instance
outside the training split. The ``Runner`` protocol is what the B11 real-loop runner implements against the pinned
harness with ``max_infra_reruns = 0`` (design §8); the tests use a fake one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from paperc.realloop import budget as B
from paperc.realloop import reward as R

N_FEATURES = 6
NOT_RUN = ("not_run_scope", "not_run_inert", "not_run_duplicate", "invalid_proposal")
FORCED_SKIPS = NOT_RUN + ("over_budget",)


class EnvStop(RuntimeError):
    """A protocol STOP inside an episode (the episode is recorded as truncated / protocol_stop first)."""


@dataclass(frozen=True)
class Proposal:
    hash: str                      # the code state the proposal would produce
    forecast_mean: float = 0.0     # a belief model's predicted increment, sigma units (state, not outcome)
    status: str = "ok"             # "ok" or one of NOT_RUN (the harness does not run it)
    max_runs: int = 1              # the run cost declared before running


class Runner(Protocol):
    def propose(self) -> Proposal: ...

    def run(self, proposal: Proposal, server: B.ExampleServer) -> R.RunRecord: ...

    def control_rerun(self) -> R.RunRecord: ...          # the trusted start configuration (RL-INFRA B)

    def start_hash(self) -> str: ...                      # the start configuration's code-state hash

    def training_rows(self) -> list: ...                  # the training split, held by the parent

    def audit(self, incumbent_hash: str | None) -> tuple[float, float]: ...   # (y_terminal, y_start)


@dataclass
class Step:
    obs: np.ndarray
    phase: str            # "E1" | "E2"
    action: str
    reward: float
    forced: bool = False  # True: the controller or a rule chose the action, not the policy


@dataclass
class Episode:
    instance: str
    steps: list[Step] = field(default_factory=list)
    end: str | None = None            # "terminated" | "truncated"
    end_reason: str | None = None     # W | llm_cap | host | protocol_stop
    attributions: dict[str, int] = field(default_factory=dict)
    forced: dict[str, int] = field(default_factory=dict)

    @property
    def ret(self) -> float:
        return 0.0 if self.end == "truncated" else float(sum(s.reward for s in self.steps))


class RealLoopEnv:
    def __init__(self, runner: Runner, *, instance: str, split_of: dict[str, str], W: int, N: int,
                 reward: R.RewardSpec, infra_policy: str, epochs: int, mode: str = "train", seed: int = 0):
        if mode not in ("train", "eval"):
            raise ValueError(f"mode {mode!r}")
        if mode == "train" and split_of.get(instance) != "train":
            raise EnvStop(f"{instance} is not a training instance ({split_of.get(instance)!r}); RL trains on the "
                          f"training split only")
        if infra_policy not in R.INFRA_POLICIES:
            raise R.RewardError(f"RL-INFRA policy {infra_policy!r} is not allowed")
        self.runner, self.instance, self.reward, self.infra_policy = runner, instance, reward, infra_policy
        self.budget = B.CampaignBudget(W, N)
        self.epochs, self.seed = epochs, seed
        self.incumbent: str | None = None
        self.incumbent_value: float | None = None
        self.keeps = 0
        self.evaluated: set[str] = {runner.start_hash()}
        self.episode = Episode(instance)
        self._pending: tuple[Proposal, R.RunRecord] | None = None
        self._proposal: Proposal | None = None
        self._last_terminal = 0.0

    # ------------------------------------------------------------------ observations
    def _obs(self, phase: str, proposal: Proposal | None, delta: float | None) -> np.ndarray:
        b = self.budget
        return np.array([1.0 if phase == "E2" else 0.0, (b.W - b.runs_used) / b.W, (b.N - b.calls_used) / b.N,
                         0.0 if proposal is None else proposal.forecast_mean, 0.0 if delta is None else delta,
                         self.keeps / b.W], dtype=float)

    def reset(self):
        """(obs, "E1") for the first decision, or (None, None) if the episode terminated before any decision (every
        proposal rule-forced until the call cap)."""
        out = self._next_decision()
        return (None, None) if out is None else out

    def _count(self, table: dict, key: str) -> None:
        table[key] = table.get(key, 0) + 1

    def _finish(self, kind: str, reason: str) -> None:
        self.episode.end, self.episode.end_reason = kind, reason

    def _stop(self, message: str):
        self._finish("truncated", "protocol_stop")
        raise EnvStop(message)

    def _next_decision(self):
        """Draw proposals until one needs a policy decision (returns (obs, "E1")) or the episode terminates
        (returns None)."""
        while True:
            if self.budget.end_reason() is not None:
                self._terminate(self.budget.end_reason())
                return None
            self.budget.charge_call()
            proposal = self.runner.propose()
            if proposal.status != "ok" or proposal.hash in self.evaluated or \
                    not self.budget.can_run(proposal.max_runs):
                if proposal.status != "ok":
                    status = proposal.status
                elif proposal.hash in self.evaluated:
                    status = "not_run_duplicate"
                else:
                    status = "over_budget"            # infeasible: the policy is not asked
                if status not in FORCED_SKIPS:
                    self._stop(f"unknown proposal status {proposal.status!r}")
                self._count(self.episode.forced, status)
                self.episode.steps.append(Step(self._obs("E1", proposal, None), "E1", "skip", 0.0, forced=True))
                continue
            self._proposal = proposal
            return self._obs("E1", proposal, None), "E1"

    def _terminate(self, reason: str) -> None:
        y_terminal, y_start = self.runner.audit(self.incumbent)
        terminal = self.reward.terminal(y_terminal, y_start)
        self._last_terminal = terminal
        if self.episode.steps:
            self.episode.steps[-1].reward += terminal
        else:
            self.episode.steps.append(Step(np.zeros(N_FEATURES), "E1", "skip", terminal, forced=True))
        self._finish("terminated", reason)

    # ------------------------------------------------------------------ transitions
    def step(self, action: str):
        """Apply ``action`` to the current decision; returns (obs, phase, reward, done, action_taken)."""
        if self.episode.end is not None:
            raise EnvStop("the episode has ended")
        if self._pending is not None:
            return self._step_e2(action)
        proposal = self._proposal
        obs_before = self._obs("E1", proposal, None)
        if action not in ("execute", "skip"):
            raise ValueError(f"E1 action {action!r}")
        if action == "skip":
            self.episode.steps.append(Step(obs_before, "E1", "skip", 0.0))
            return self._advance(0.0, "skip")
        if not self.budget.can_run(proposal.max_runs):
            self._stop("an infeasible execute reached the policy")       # _next_decision forces these
        server = B.ExampleServer(self.runner.training_rows(), self.epochs, seed=self.seed + self.budget.runs_used)
        run = self.runner.run(proposal, server)
        over = B.over_budget(server.record())
        first = run.prior_attempts[0] if run.prior_attempts else run
        control = None
        if self.infra_policy == "control_rerun" and not over and first.kind == R.INFRA and not first.trusted_code \
                and first.reason in R.WORKER_PRODUCIBLE and not first.host.any():
            control = self.runner.control_rerun()
        att, runs, first = R.attribute_attempts(run, policy=self.infra_policy, control=control, budget_over=over)
        self._count(self.episode.attributions, att)
        self.evaluated.add(proposal.hash)
        if att == "stop":
            self.episode.steps.append(Step(obs_before, "E1", "execute", 0.0))
            self._stop(f"protocol STOP: {first.kind}/{first.reason}")
        if runs > proposal.max_runs:
            self.episode.steps.append(Step(obs_before, "E1", "execute", 0.0))
            self._stop(f"the execute consumed {runs} runs, more than its declared {proposal.max_runs}")
        if att in ("truncate_host", "truncate_infrastructure"):
            self.episode.steps.append(Step(obs_before, "E1", "execute", 0.0))
            self._finish("truncated", "host" if att == "truncate_host" else "infrastructure")
            return None, None, 0.0, True, "execute"
        self.budget.charge_runs(runs)
        reward = self.reward.step(att, runs)
        self.episode.steps.append(Step(obs_before, "E1", "execute", reward))
        delta = None if (att != "ok" or self.incumbent_value is None) else first.value - self.incumbent_value
        if att == "ok":
            self._pending = (proposal, first)
            return self._obs("E2", proposal, delta), "E2", reward, False, "execute"
        self.episode.steps.append(Step(self._obs("E2", proposal, None), "E2", "discard", 0.0, forced=True))
        return self._advance(reward, "execute")

    def _step_e2(self, action: str):
        proposal, run = self._pending
        delta = None if self.incumbent_value is None else run.value - self.incumbent_value
        obs_before = self._obs("E2", proposal, delta)
        if action not in ("keep", "discard"):
            raise ValueError(f"E2 action {action!r}")
        if action == "keep":
            self.incumbent, self.incumbent_value, self.keeps = proposal.hash, run.value, self.keeps + 1
        self.episode.steps.append(Step(obs_before, "E2", action, 0.0))
        self._pending = None
        return self._advance(0.0, action)

    def _advance(self, reward: float, taken: str):
        """Move to the next decision; the returned reward is the decision's own plus the terminal reward if the
        episode terminates now (forced rows carry no reward)."""
        self._last_terminal = 0.0
        nxt = self._next_decision()
        if nxt is None:
            return None, None, reward + self._last_terminal, True, taken
        obs, phase = nxt
        return obs, phase, reward, False, taken
