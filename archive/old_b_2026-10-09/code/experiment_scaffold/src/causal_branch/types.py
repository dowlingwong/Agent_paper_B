from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class FailureClass(StrEnum):
    NONE = "none"
    CHECKPOINT_INSTRUMENTATION = "checkpoint_instrumentation_failure"
    REGIME_UNAVAILABLE_PRETREATMENT = "regime_unavailable_pretreatment"
    REGIME_INDUCED_EXECUTION = "regime_induced_execution_failure"
    POSTTREATMENT_MISSINGNESS = "posttreatment_missingness"
    INFRASTRUCTURE_TIMEOUT = "infrastructure_timeout"
    BUDGET_EXHAUSTION = "budget_exhaustion"


class TerminalCategory(StrEnum):
    NOT_TERMINAL = "not_terminal"
    VALIDATED_COMPLETION = "validated_completion"
    INVALID_SCIENTIFIC_OUTPUT = "invalid_scientific_output"
    RESPONSIBLE_ESCALATION = "responsible_escalation"
    ABSTENTION = "abstention"
    INFRASTRUCTURE_TIMEOUT = "infrastructure_timeout"
    UNRESOLVED_TERMINATION = "unresolved_termination"
    BUDGET_EXHAUSTION = "budget_exhaustion"


class ModelSeedClaim(StrEnum):
    NOT_REQUESTED = "not_requested"
    REQUESTED_UNVERIFIED = "requested_unverified"
    VERIFIED_DETERMINISTIC = "verified_deterministic"


# Disjoint external-call attribution rule. A single external event must be
# counted in exactly one of these three counters and never in two: a verifier
# call is `verifier_calls`, a tool/toolchain call is `tool_calls`, and a
# controller/monitor external call (availability evaluation, gate arithmetic
# model/tool calls made by the decision procedure) is `controller_external_calls`.
# `registered_components()` collapses them into the single constrained
# `external_calls` component exactly once; double counting a single event would
# inflate that component and is a logging defect, not a measurement.
EXTERNAL_CALL_COUNTERS = ("verifier_calls", "tool_calls", "controller_external_calls")

# Count (integer) fields versus continuous resource fields. Counts must be
# nonnegative integers; continuous fields must be finite and nonnegative.
_COUNT_FIELDS = (
    "input_tokens",
    "output_tokens",
    "verifier_calls",
    "tool_calls",
    "controller_external_calls",
    "storage_bytes",
    "network_bytes",
    "artifact_rewrites",
)
_CONTINUOUS_FIELDS = (
    "api_expense",
    "cpu_seconds",
    "gpu_seconds",
    "wall_seconds",
    "human_minutes",
)


@dataclass(frozen=True)
class CostVector:
    input_tokens: int = 0
    output_tokens: int = 0
    api_expense: float = 0.0
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    wall_seconds: float = 0.0
    verifier_calls: int = 0
    tool_calls: int = 0
    controller_external_calls: int = 0
    storage_bytes: int = 0
    network_bytes: int = 0
    human_minutes: float = 0.0
    artifact_rewrites: int = 0

    def __post_init__(self) -> None:
        for field_name in _COUNT_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"cost count field {field_name} must be a nonnegative integer"
                )
        for field_name in _CONTINUOUS_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"cost continuous field {field_name} must be numeric"
                )
            if not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(
                    f"cost continuous field {field_name} must be finite and nonnegative"
                )

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)

    def registered_components(self) -> dict[str, int | float]:
        """Return the eight components priced by the frozen certification math.

        The raw vector deliberately keeps finer audit counters.  Combining the
        three disjoint external-call counters here prevents those counters from
        silently changing K in the simultaneous certification family and makes
        double counting a single event visible as an inflated total.
        """

        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "api_expense": self.api_expense,
            "cpu_seconds": self.cpu_seconds,
            "gpu_seconds": self.gpu_seconds,
            "wall_seconds": self.wall_seconds,
            "external_calls": (
                self.verifier_calls + self.tool_calls + self.controller_external_calls
            ),
            "human_minutes": self.human_minutes,
        }


@dataclass(frozen=True)
class CostBreakdown:
    regime_body: CostVector = field(default_factory=CostVector)
    controller_overhead: CostVector = field(default_factory=CostVector)

    def total(self) -> CostVector:
        values: dict[str, int | float] = {}
        for name in CostVector.__dataclass_fields__:
            values[name] = getattr(self.regime_body, name) + getattr(
                self.controller_overhead, name
            )
        return CostVector(**values)

    def to_dict(self) -> dict[str, Any]:
        total = self.total()
        return {
            "regime_body": self.regime_body.to_dict(),
            "controller_overhead": self.controller_overhead.to_dict(),
            "total_raw": total.to_dict(),
            "registered_K8": total.registered_components(),
        }


@dataclass(frozen=True)
class BranchContext:
    experiment_id: str
    root_id: str
    template_id: str
    checkpoint_id: str
    branch_id: str
    regime_id: str
    repetition_id: int
    workspace: Path
    workload_seed: int
    model_seed_claim: ModelSeedClaim = ModelSeedClaim.NOT_REQUESTED
    parent_branch_id: str | None = None


@dataclass(frozen=True)
class RegimeResult:
    terminal_category: TerminalCategory
    failure_class: FailureClass = FailureClass.NONE
    primary_outcome: float | None = None
    verifier_result: str | None = None
    cost: CostVector = field(default_factory=CostVector)
    controller_cost: CostVector = field(default_factory=CostVector)
    details: dict[str, Any] = field(default_factory=dict)

    def cost_breakdown(self) -> CostBreakdown:
        return CostBreakdown(self.cost, self.controller_cost)
