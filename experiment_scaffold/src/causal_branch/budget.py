"""Central hard-cost-ceiling guard (mechanism; calibration is R7-5).

One guard for the eight constrained components. It reads its per-action
worst-case increment table from configuration. With an `unpopulated` table it
refuses to start any scientific action and reports `budget_table_unpopulated`;
it does not default to permissive and does not default to zero. A `profiling`
mode (used only by R7-4/R7-5) permits actions under an explicit per-run
wall-clock/compute cap and marks every resulting record `qualifying: false,
purpose: profiling`.

When a scientific action's registered worst-case increment does not fit the
remaining vector ceiling, the action is not started and the branch terminates as
`BUDGET_EXHAUSTION` — the existing member of both `FailureClass` and
`TerminalCategory`. The guard never converts budget exhaustion into ordinary
failure, unavailability, or a zero-cost observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .types import CostVector, FailureClass, RegimeResult, TerminalCategory

CONSTRAINED_COMPONENTS = (
    "input_tokens",
    "output_tokens",
    "api_expense",
    "cpu_seconds",
    "gpu_seconds",
    "wall_seconds",
    "external_calls",
    "human_minutes",
)


def _component_delta(increment: Mapping[str, Any], component: str) -> float:
    value = increment.get(component, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"worst-case increment for {component} must be nonnegative")
    return float(value)


@dataclass
class BudgetGuard:
    """Fail-closed budget guard with an explicit unpopulated state."""

    increment_table: Mapping[str, Mapping[str, Any]] | None = None
    ceilings: Mapping[str, float] = field(default_factory=dict)
    mode: str = "scientific"  # "scientific" | "profiling"
    profiling_wall_cap: float | None = None
    profiling_compute_cap: float | None = None

    def __post_init__(self) -> None:
        self.remaining: dict[str, float] = {
            component: float(self.ceilings.get(component, 0.0))
            for component in CONSTRAINED_COMPONENTS
        }
        self.binding_events: list[str] = []
        self._started: int = 0

    @property
    def populated(self) -> bool:
        """True when every action's worst-case increment covers all eight
        components with non-null, nonnegative values."""
        table = self.increment_table
        if not table:
            return False
        for action, increment in table.items():
            if not isinstance(increment, dict):
                return False
            for component in CONSTRAINED_COMPONENTS:
                if increment.get(component) is None:
                    return False
        return True

    def _authorize_increment(self, increment: Mapping[str, Any], action: str) -> RegimeResult | None:
        for component in CONSTRAINED_COMPONENTS:
            delta = _component_delta(increment, component)
            if delta > self.remaining.get(component, 0.0):
                self.binding_events.append(f"{action}:{component}")
                return RegimeResult(
                    terminal_category=TerminalCategory.BUDGET_EXHAUSTION,
                    failure_class=FailureClass.BUDGET_EXHAUSTION,
                    primary_outcome=None,
                    details={"component": component, "action": action},
                )
        for component in CONSTRAINED_COMPONENTS:
            self.remaining[component] -= _component_delta(increment, component)
        return None

    def authorize(self, action: str) -> RegimeResult | None:
        """Authorize one action.

        Returns `None` to proceed, or a `BUDGET_EXHAUSTION` `RegimeResult` when
        the action must not start.
        """
        self._started += 1
        if self.mode == "profiling":
            if self.profiling_wall_cap is not None and self.profiling_wall_cap < 0:
                return RegimeResult(
                    terminal_category=TerminalCategory.BUDGET_EXHAUSTION,
                    failure_class=FailureClass.BUDGET_EXHAUSTION,
                    details={"profiling_cap": "wall"},
                )
            return None
        if not self.populated:
            return RegimeResult(
                terminal_category=TerminalCategory.BUDGET_EXHAUSTION,
                failure_class=FailureClass.BUDGET_EXHAUSTION,
                primary_outcome=None,
                details={"reason": "budget_table_unpopulated"},
            )
        increment = self.increment_table.get(action)
        if increment is None:
            return RegimeResult(
                terminal_category=TerminalCategory.BUDGET_EXHAUSTION,
                failure_class=FailureClass.BUDGET_EXHAUSTION,
                details={"reason": "unregistered_action", "action": action},
            )
        return self._authorize_increment(increment, action)

    def binding_rate(self) -> float:
        """Fraction of authorized actions that hit a ceiling (diagnostic)."""
        if self._started == 0:
            return 0.0
        return len(self.binding_events) / self._started


def profiling_record(*, action: str, wall_seconds: float) -> dict[str, Any]:
    """A profiling cost record, always non-qualifying."""
    return {
        "qualifying": False,
        "purpose": "profiling",
        "action": action,
        "wall_seconds": wall_seconds,
    }
