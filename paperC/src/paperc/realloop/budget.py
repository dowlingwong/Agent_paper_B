"""Budget enforcement against adversarial edits (design note §5, RL-BUDGET). ENGINEERING_ONLY.

In the isolated harness the worker "computes the training itself, so the budget accounting and the loss lines stay in
the editable process" (``isolation.py`` limits); only the wall time (the measured timeout) is enforced outside it.

* ``ExampleServer`` — RL-BUDGET A: the parent holds the training split and serves example **contents** (rows) on
  request through the result channel, in a fixed order (one permutation per epoch), and counts them; the worker root
  holds no training data (RL-LAYOUT ``served``). A request beyond ``n_examples x epochs`` is refused and the run is a
  proposal failure (``divergent`` / ``budget_exceeded``), whatever metric the worker reports. What this bounds: the
  data the worker can obtain (at most the served rows, in the parent's order). What it does not bound: the worker can
  keep rows it received and train on them again; **compute is bounded only by the measured timeout and, as a
  complement, a cgroup CPU/GPU-time limit** (design §8).
* ``classify_run`` — folds the parent-side budget record into the harness outcome.
* ``CampaignBudget`` — the campaign's run budget W and call cap N, owned by the controller: a policy can ask, the
  controller charges, and exhausting either ends the episode as terminated (addendum 19 Nov §C).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


class BudgetExceeded(RuntimeError):
    """A request beyond a budget."""


@dataclass
class ExampleServer:
    rows: Sequence            # the training split, held by the parent
    epochs: int
    seed: int
    served: int = 0
    refused: int = 0
    _order: np.ndarray | None = field(default=None, repr=False)

    def __post_init__(self):
        if len(self.rows) == 0 or self.epochs <= 0:
            raise ValueError("rows must be non-empty and epochs positive")

    @property
    def limit(self) -> int:
        return len(self.rows) * self.epochs

    def order(self) -> np.ndarray:
        if self._order is None:
            rng = np.random.default_rng(self.seed)
            n = len(self.rows)
            self._order = np.concatenate([rng.permutation(n) for _ in range(self.epochs)])
        return self._order

    def serve(self, k: int) -> list:
        """The contents of the next ``k`` examples of the parent's fixed order."""
        if k <= 0:
            raise ValueError("k must be positive")
        if self.served + k > self.limit:
            self.refused += 1
            raise BudgetExceeded(f"{self.served} + {k} examples exceed the budget {self.limit}")
        idx = self.order()[self.served:self.served + k]
        self.served += k
        return [self.rows[int(i)] for i in idx]

    def record(self) -> dict:
        return {"limit": self.limit, "served": self.served, "refused_requests": self.refused}


def classify_run(kind: str, reason: str, budget_record: dict) -> tuple[str, str]:
    """The harness outcome with the parent's budget record folded in. A refused request makes the run
    ``divergent`` / ``budget_exceeded`` (a proposal failure) — deliberately also when the run later fails with host
    evidence (the request was the proposal's) — except a launch error (nothing ran) and a provisional timeout (a
    STOP keeps priority)."""
    over = budget_record.get("refused_requests", 0) > 0 or budget_record.get("served", 0) > budget_record.get("limit", 0)
    if not over:
        return kind, reason
    if kind == "infrastructure_failure" and reason in ("launch_error", "timeout"):
        return kind, reason
    return "divergent", "budget_exceeded"


@dataclass
class CampaignBudget:
    W: int                 # worker runs
    N: int                 # manager (LLM) calls
    runs_used: int = 0
    calls_used: int = 0

    def __post_init__(self):
        if self.W < 1 or self.N < 1:
            raise ValueError("W and N must be at least 1")

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
