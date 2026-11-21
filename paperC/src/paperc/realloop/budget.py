"""Budget enforcement against adversarial edits (design note §5, RL-BUDGET). ENGINEERING_ONLY.

In the isolated harness the worker "computes the training itself, so the budget accounting and the loss lines stay in
the editable process" (``isolation.py`` limits); only the wall time (the measured timeout) is enforced outside it. An
edit could then train on more examples or more epochs within the time limit. Under RL that is a gain the policy can
learn to buy for free.

* ``ExampleBudget`` — RL-BUDGET A: the parent serves training example indices on request (through the result
  channel) and counts them; a request beyond ``examples x epochs`` is refused and the run is a proposal failure
  (``divergent`` with reason ``budget_exceeded``). The worker can still reuse examples it already received within the
  budget (it keeps them in memory); the budget bounds data, the wall time bounds compute.
* ``classify_run`` — folds the parent-side budget record into the harness outcome.
* ``CampaignBudget`` — the campaign's run budget W and call cap N, owned by the controller: a policy can ask, the
  controller charges, and exhausting either ends the episode as terminated (addendum 19 Nov §C).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class BudgetExceeded(RuntimeError):
    """A request beyond a budget."""


@dataclass
class ExampleBudget:
    n_examples: int
    epochs: int
    seed: int
    served: int = 0
    refused: int = 0
    _order: np.ndarray | None = field(default=None, repr=False)

    def __post_init__(self):
        if self.n_examples <= 0 or self.epochs <= 0:
            raise ValueError("n_examples and epochs must be positive")

    @property
    def limit(self) -> int:
        return self.n_examples * self.epochs

    def serve(self, k: int) -> np.ndarray:
        """The next ``k`` example indices of the parent's fixed order (one permutation per epoch)."""
        if k <= 0:
            raise ValueError("k must be positive")
        if self.served + k > self.limit:
            self.refused += 1
            raise BudgetExceeded(f"{self.served} + {k} examples exceed the budget {self.limit}")
        if self._order is None:
            rng = np.random.default_rng(self.seed)
            self._order = np.concatenate([rng.permutation(self.n_examples) for _ in range(self.epochs)])
        out = self._order[self.served:self.served + k]
        self.served += k
        return out

    def record(self) -> dict:
        return {"limit": self.limit, "served": self.served, "refused_requests": self.refused}


def classify_run(kind: str, reason: str, budget_record: dict) -> tuple[str, str]:
    """The harness outcome with the parent's budget record folded in: any refused request makes the run
    ``divergent`` / ``budget_exceeded`` (a proposal failure), whatever the worker reported."""
    if budget_record.get("refused_requests", 0) > 0 or budget_record.get("served", 0) > budget_record.get("limit", 0):
        if kind == "infrastructure_failure" and reason == "launch_error":
            return kind, reason
        return "divergent", "budget_exceeded"
    return kind, reason


@dataclass
class CampaignBudget:
    W: int                 # worker runs
    N: int                 # manager (LLM) calls
    runs_used: int = 0
    calls_used: int = 0

    def charge_call(self) -> None:
        if self.calls_used >= self.N:
            raise BudgetExceeded("call cap reached")
        self.calls_used += 1

    def can_run(self, k: int = 1) -> bool:
        return self.runs_used + k <= self.W

    def charge_runs(self, k: int) -> None:
        if not self.can_run(k):
            raise BudgetExceeded(f"{self.runs_used} + {k} runs exceed W = {self.W}")
        self.runs_used += k

    def end_reason(self) -> str | None:
        """'W' or 'llm_cap' when the episode is over (terminated), else None."""
        if self.runs_used >= self.W:
            return "W"
        if self.calls_used >= self.N:
            return "llm_cap"
        return None
