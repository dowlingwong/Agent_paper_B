"""R1 branch-record schema (BUILD_RUNBOOK L9).

Ported in spirit from the legacy ``experiment_scaffold/src/causal_branch/control/schema.py``
(old Paper B route, b_branch_v1/v2):
- records are append-only;
- validation refuses incomplete semantics;
- the learner projection is restricted;
- an integrity status is never a utility value;
- duplicate and split checks are kept.

The unit changes from a three-leaf root tree to a **trial-epoch sibling set**:
every feasible action at one restored decision point, each followed by R
continuations under rho.

Keys:
- a decision point is (instance_id, campaign_id, epoch, budget_index);
- a record is one action at a decision point;
- a leaf is one continuation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

R1_BRANCH_SCHEMA = "r1_branch_v1"
EPOCHS = frozenset({"E0", "E1", "E2"})
ACTIONS = frozenset({"continue", "skip", "revise", "verify", "demote", "stop"})
INTEGRITY = frozenset({"ok", "collection_failure", "infrastructure_stop"})
SPLITS = frozenset({"engineering", "pilot", "dev", "calibration", "test"})

#: Keys that may never appear in a learner-visible feature map (the leak test).
FORBIDDEN_FEATURE_KEYS = frozenset({
    "outcome", "outcome_y", "y", "audit", "audit_metrics", "test_metric", "test_score",
    "leaves", "sibling", "sibling_outcomes", "future", "future_records", "instance_id",
    "campaign_id", "split", "integrity",
})
FORBIDDEN_FEATURE_PREFIXES = ("audit_", "test_", "sibling_", "future_", "outcome_", "leaf_")


class BranchRecordError(ValueError):
    """A record or a sibling set violates the R1 branch contract."""


@dataclass(frozen=True)
class Leaf:
    """One continuation after the forced action.

    ``outcome_y`` is the normalised audited improvement of the final incumbent
    (PLAN §4), in [-1, 1].  It exists only when ``integrity == "ok"``.  A
    collection failure is a status, never a utility value.
    """

    repetition: int
    integrity: str
    outcome_y: float | None
    cost_worker_runs: int
    cost_llm_calls: int = 0
    final_incumbent_hash: str = ""
    audit: Mapping[str, Any] = field(default_factory=dict)  # evaluator-only


@dataclass(frozen=True)
class BranchRecord:
    schema_version: str
    instance_id: str
    node: str
    campaign_id: str
    epoch: str
    budget_index: int
    action: str
    split: str
    harness_commit: str
    snapshot_hash: str
    manager_backend: str
    horizon: int
    features: Mapping[str, Any]
    mask: Mapping[str, bool]
    leaves: tuple[Leaf, ...]
    executed_action: str | None = None  # what the harness actually ran (rejections fall back to continue)
    notes: str = ""

    @property
    def decision_point(self) -> tuple[str, str, str, int]:
        return (self.instance_id, self.campaign_id, self.epoch, int(self.budget_index))

    @property
    def identity(self) -> tuple[str, str, str, int, str]:
        return (*self.decision_point, self.action)


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def validate_record(record: BranchRecord) -> None:
    if record.schema_version != R1_BRANCH_SCHEMA:
        raise BranchRecordError(f"unknown schema {record.schema_version!r}")
    for name in ("instance_id", "node", "campaign_id", "harness_commit", "snapshot_hash", "manager_backend"):
        if not getattr(record, name):
            raise BranchRecordError(f"missing {name}")
    if record.epoch not in EPOCHS:
        raise BranchRecordError(f"unknown epoch {record.epoch!r}")
    if record.action not in ACTIONS:
        raise BranchRecordError(f"unknown action {record.action!r}")
    if record.split not in SPLITS:
        raise BranchRecordError(f"unknown split {record.split!r}")
    if not isinstance(record.budget_index, int) or isinstance(record.budget_index, bool) or record.budget_index < 1:
        raise BranchRecordError("budget_index must be a positive int")
    if not isinstance(record.horizon, int) or record.horizon < 0:
        raise BranchRecordError("horizon must be a non-negative int")
    if set(record.mask) - ACTIONS:
        raise BranchRecordError(f"mask names unknown actions {sorted(set(record.mask) - ACTIONS)}")
    if not record.mask.get(record.action, False):
        raise BranchRecordError(f"action {record.action!r} is not feasible under the recorded mask")
    if not record.leaves:
        raise BranchRecordError("a record needs at least one leaf")
    assert_features_leak_free(record.features)
    reps = set()
    for leaf in record.leaves:
        if leaf.repetition in reps:
            raise BranchRecordError(f"duplicate repetition {leaf.repetition}")
        reps.add(leaf.repetition)
        if leaf.integrity not in INTEGRITY:
            raise BranchRecordError(f"unknown integrity status {leaf.integrity!r}")
        if leaf.integrity == "ok":
            if not _finite(leaf.outcome_y) or not -1.0 <= float(leaf.outcome_y) <= 1.0:
                raise BranchRecordError("an ok leaf needs a finite outcome_y in [-1, 1]")
        elif leaf.outcome_y is not None:
            raise BranchRecordError("a failed leaf must not carry a utility value")
        if not isinstance(leaf.cost_worker_runs, int) or leaf.cost_worker_runs < 0:
            raise BranchRecordError("cost_worker_runs must be a non-negative int")


def assert_features_leak_free(features: Mapping[str, Any]) -> None:
    bad = [k for k in features if k.lower() in FORBIDDEN_FEATURE_KEYS
           or k.lower().startswith(FORBIDDEN_FEATURE_PREFIXES)]
    if bad:
        raise BranchRecordError(f"features leak evaluator-only information: {sorted(bad)}")


def learner_projection(record: BranchRecord) -> dict[str, Any]:
    """The only view a learner or controller may see: features, mask, epoch."""
    projection = {"features": dict(record.features), "mask": dict(record.mask), "epoch": record.epoch}
    assert_features_leak_free(projection["features"])
    return projection


def validate_sibling_sets(records: list[BranchRecord]) -> dict[tuple, list[BranchRecord]]:
    """Group by decision point and check the sibling contract.

    Siblings share snapshot, features, mask, split, horizon, backend and harness
    commit; each action appears at most once; every instance has one split.
    """
    groups: dict[tuple, list[BranchRecord]] = {}
    seen: set[tuple] = set()
    split_of: dict[str, str] = {}
    for record in records:
        validate_record(record)
        if record.identity in seen:
            raise BranchRecordError(f"duplicate branch unit {record.identity}")
        seen.add(record.identity)
        if split_of.setdefault(record.instance_id, record.split) != record.split:
            raise BranchRecordError(f"split leakage for instance {record.instance_id}")
        groups.setdefault(record.decision_point, []).append(record)
    for point, sibs in groups.items():
        first = sibs[0]
        for other in sibs[1:]:
            for name in ("snapshot_hash", "split", "horizon", "manager_backend", "harness_commit"):
                if getattr(other, name) != getattr(first, name):
                    raise BranchRecordError(f"siblings at {point} disagree on {name}")
            if dict(other.features) != dict(first.features) or dict(other.mask) != dict(first.mask):
                raise BranchRecordError(f"siblings at {point} disagree on pre-treatment features or mask")
        if "continue" not in {s.action for s in sibs}:
            raise BranchRecordError(f"sibling set at {point} lacks the reference action 'continue'")
    return groups


def record_to_dict(record: BranchRecord) -> dict[str, Any]:
    out = {k: getattr(record, k) for k in record.__dataclass_fields__ if k != "leaves"}
    out["features"], out["mask"] = dict(record.features), dict(record.mask)
    out["leaves"] = [dict(leaf.__dict__, audit=dict(leaf.audit)) for leaf in record.leaves]
    return out


def record_from_dict(payload: Mapping[str, Any]) -> BranchRecord:
    data = dict(payload)
    data["leaves"] = tuple(Leaf(**leaf) for leaf in data.get("leaves", []))
    record = BranchRecord(**data)
    validate_record(record)
    return record
