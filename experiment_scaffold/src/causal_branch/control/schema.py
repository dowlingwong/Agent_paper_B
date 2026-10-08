"""Paper B branch-record schema and the leak-safe learner projection.

The schema is the machine-readable form of the dataset contract in Paper B
§4.  A record is append-only; validation rejects records whose semantics are
incomplete rather than defaulting missing fields to valid values.

The learner projection is deliberately restricted: it exposes only the
pre-treatment features and the mask, never the evaluator-only condition label,
never the outcome table, and never root-identity shortcuts.  The negative tests
in ``tests/control/`` assert that the projection cannot be made to leak those
fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping

B_BRANCH_SCHEMA_VERSION = "b_branch_v1"

SPLITS = frozenset({"qualification", "pilot", "train", "validation", "calibration", "test"})
ACTION_IDS = frozenset({"g0", "gv"})
EXECUTION_STATUS = frozenset(
    {"pending", "completed", "timeout", "error", "unavailable", "collection_failure", "invalid"}
)
#: Data-integrity status.  ``ok`` is the only status that may carry an outcome;
#: a collection or infrastructure failure is never a utility value.
INTEGRITY_STATUS = frozenset({"ok", "collection_failure", "infrastructure_stop"})

REQUIRED_FIELDS = (
    "schema_version",
    "paper",
    "study",
    "protocol_hash",
    "run_id",
    "template_id",
    "root_id",
    "checkpoint_id",
    "checkpoint_rule_version",
    "split",
    "condition_label",
    "runtime_manifest_hash",
    "snapshot_hash",
    "history_hash",
    "feature_registry_version",
    "pre_treatment_features",
    "pre_treatment_mask",
    "availability_evidence_hash",
    "action_id",
    "action_version",
    "continuation_version",
    "repetition_id",
    "seed_coupling_id",
    "branch_order",
    "adjudicator_version",
)

#: Fields that must never be reachable through the learner projection.
EVALUATOR_ONLY_FIELDS = frozenset(
    {"condition_label", "outcome_success", "outcome_utility", "outcome_invalid",
     "invalid_reason", "integrity_status", "artifact_hashes"}
)


class BranchRecordError(ValueError):
    """A branch record violates the Paper B dataset contract."""


@dataclass(frozen=True)
class BranchRecord:
    schema_version: str = B_BRANCH_SCHEMA_VERSION
    paper: str = "B"
    study: str = ""
    protocol_hash: str = ""
    run_id: str = ""
    template_id: str = ""
    template_family_id: str | None = None
    root_id: str = ""
    checkpoint_id: str = ""
    checkpoint_rule_version: str = ""
    split: str = ""
    condition_label: str = "evaluator_only"
    runtime_manifest_hash: str = ""
    snapshot_hash: str = ""
    history_hash: str = ""
    feature_registry_version: str = ""
    pre_treatment_features: Mapping[str, float] = field(default_factory=dict)
    pre_treatment_mask: Mapping[str, bool] = field(default_factory=dict)
    availability_evidence_hash: str = ""
    action_id: str = ""
    action_version: str = ""
    continuation_version: str = ""
    repetition_id: int = 0
    seed_coupling_id: str = ""
    branch_order: int = 0
    outcome_success: int | None = None
    outcome_utility: float | None = None
    outcome_invalid: int | None = None
    invalid_reason: str | None = None
    integrity_status: str = "ok"
    cost_vector: Mapping[str, float] = field(default_factory=dict)
    execution_status: str = "pending"
    failure_reason: str | None = None
    adjudicator_version: str = ""
    artifact_hashes: tuple[str, ...] = ()

    def identity(self) -> tuple[str, str, str, int]:
        return (self.root_id, self.checkpoint_id, self.action_id, self.repetition_id)


def validate_record(record: BranchRecord) -> None:
    """Fail closed on a record that violates the dataset contract."""

    missing = []
    for name in REQUIRED_FIELDS:
        value = getattr(record, name, None)
        if value is None or (isinstance(value, str) and not value) or value == {}:
            missing.append(name)
    if missing:
        raise BranchRecordError(f"missing required fields: {sorted(missing)}")
    if record.schema_version != B_BRANCH_SCHEMA_VERSION:
        raise BranchRecordError(
            f"unknown schema_version {record.schema_version!r}; expected {B_BRANCH_SCHEMA_VERSION}"
        )
    if record.paper != "B":
        raise BranchRecordError("a Paper B record must carry paper='B'")
    if record.split not in SPLITS:
        raise BranchRecordError(f"unknown split {record.split!r}")
    if record.action_id not in ACTION_IDS:
        raise BranchRecordError(f"unknown action_id {record.action_id!r}")
    if record.execution_status not in EXECUTION_STATUS:
        raise BranchRecordError(f"unknown execution_status {record.execution_status!r}")
    if record.repetition_id < 0 or record.branch_order < 0:
        raise BranchRecordError("repetition_id and branch_order must be non-negative")
    if record.action_id == "gv" and record.outcome_success is not None:
        if not record.pre_treatment_mask.get("gv", False):
            raise BranchRecordError("a gv record with an assigned outcome requires a feasible mask")
    if record.action_id == "g0" and not record.pre_treatment_mask.get("g0", False):
        raise BranchRecordError("g0 must be feasible (baseline availability)")
    if set(record.pre_treatment_mask) != ACTION_IDS or any(type(v) is not bool for v in record.pre_treatment_mask.values()):
        raise BranchRecordError("mask must explicitly bind boolean g0 and gv feasibility")
    if any(not math.isfinite(v) for v in record.pre_treatment_features.values()):
        raise BranchRecordError("features must be finite")
    if any(not math.isfinite(v) or v < 0 for v in record.cost_vector.values()):
        raise BranchRecordError("cost channels must be finite and nonnegative")
    unavailable = not record.pre_treatment_mask.get(record.action_id, False)
    assigned = any(v is not None for v in (record.outcome_success, record.outcome_utility, record.outcome_invalid))
    if unavailable != (record.execution_status == "unavailable"):
        raise BranchRecordError("execution status disagrees with pre-treatment feasibility")
    if unavailable and assigned:
        raise BranchRecordError("an unavailable action must not be assigned an outcome")
    if record.execution_status == "unavailable" and assigned:
        raise BranchRecordError("unavailable execution status cannot carry an outcome")
    if assigned and not record.adjudicator_version:
        raise BranchRecordError("an assigned outcome requires an adjudicator version")
    if assigned and record.execution_status not in {"completed", "timeout", "error", "invalid"}:
        raise BranchRecordError(
            "an assigned outcome requires a terminal execution status (completed/timeout/error/invalid)"
        )
    if record.outcome_invalid not in (None, 0, 1):
        raise BranchRecordError("outcome_invalid must be None or binary")
    if record.outcome_success not in (None, 0, 1):
        raise BranchRecordError("outcome_success must be None or binary")
    if record.outcome_utility is not None and not (0.0 <= record.outcome_utility <= 1.0):
        raise BranchRecordError("outcome_utility must lie in [0,1]")
    if record.integrity_status not in INTEGRITY_STATUS:
        raise BranchRecordError(f"unknown integrity_status {record.integrity_status!r}")
    if record.integrity_status != "ok":
        # A collection or infrastructure failure is an integrity outcome, never
        # a utility value, and the evaluator must not read it as U=0.
        if assigned:
            raise BranchRecordError(
                "a non-ok integrity status must not carry an outcome value"
            )
        if record.execution_status not in {"collection_failure", "error"}:
            raise BranchRecordError(
                "a non-ok integrity status requires a terminal failure execution status"
            )
    if record.outcome_invalid == 1:
        # Invalid or no candidate: exactly U=0, with its reason retained.
        if record.outcome_utility is None or record.outcome_utility != 0.0:
            raise BranchRecordError("an invalid outcome is exactly outcome_utility=0")
        if not record.invalid_reason:
            raise BranchRecordError("an invalid outcome requires a retained invalid_reason")
    elif record.invalid_reason:
        raise BranchRecordError("invalid_reason is only meaningful for an invalid outcome")


def feature_projection(record: BranchRecord) -> dict[str, Any]:
    """Return the learner-visible projection of a record.

    Only the pre-treatment features and the feasibility mask are exposed.  The
    evaluator-only condition label, the outcome table and artifact hashes are
    not part of the projection and cannot be requested from it.
    """

    return {
        "features": dict(record.pre_treatment_features),
        "mask": dict(record.pre_treatment_mask),
    }


def assert_projection_is_leak_free(projection: Mapping[str, Any]) -> None:
    """Guard used by tests and by the smoke driver."""

    leaked = EVALUATOR_ONLY_FIELDS.intersection(projection)
    leaked |= (EVALUATOR_ONLY_FIELDS | {"root_id", "template_id", "template_family_id"}).intersection(projection.get("features", {}))
    if leaked:
        raise BranchRecordError(f"learner projection leaks evaluator-only fields: {sorted(leaked)}")


def assert_no_duplicate_units(records: list[BranchRecord]) -> None:
    """Duplicate root/checkpoint/action/repetition units are a data defect."""

    seen: set[tuple[str, str, str, int]] = set()
    for record in records:
        key = record.identity()
        if key in seen:
            raise BranchRecordError(f"duplicate branch unit {key}")
        seen.add(key)


def assert_split_disjoint(records: list[BranchRecord]) -> None:
    """Every template family, template and root (including descendants) has one split.

    Callers must supply a stable family identity across renamed sibling variants;
    when absent, the template itself is the declared family. Names are not guessed.
    """
    owners = {}
    for record in records:
        for kind, identity in (("family", record.template_family_id or record.template_id),
                               ("template", record.template_id), ("root", record.root_id)):
            key = kind, identity
            if key in owners and owners[key] != record.split:
                raise BranchRecordError(f"split leakage for {kind} {identity}: {owners[key]} vs {record.split}")
            owners[key] = record.split
