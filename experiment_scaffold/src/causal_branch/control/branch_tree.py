"""B5: ``b_branch_v2`` records and the original-root tree.

The tree driver executes the three complete regimes on one original root through
the real filesystem fork path (:class:`FileSnapshotManager` /
:class:`FileBranchIsolationManager`) with a task adapter and a scripted/mock
policy on CPU.  Outcomes come from executing the task, never from supplied leaf
constants.

The converter ``records_to_tree`` recomputes the regimes and rejects a
checkpoint-2 state transplanted from another branch, a denominator conditioned
on both policies reaching checkpoint 2, lineage or split leakage, and a second
verification in one root.

All estimands are over the original-root population; unreachable checkpoint 2
and unavailable verification stay in under their registered fallback.  Nothing
here is scientific evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Protocol

import numpy as np

from causal_branch.branching import FileBranchIsolationManager
from causal_branch.checkpoint import FileSnapshotManager

B_BRANCH_V2_SCHEMA = "b_branch_v2"
REGIMES = ("now", "later", "never")


class TreeError(ValueError):
    """A tree violates the original-root contract."""


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TreeRecord:
    schema_version: str = B_BRANCH_V2_SCHEMA
    root_id: str = ""
    template_family_id: str = ""
    split: str = ""
    decision_index: int = 1
    branch_id: str = ""
    parent_branch_id: str | None = None
    action: str = "continue"
    history_hash_at_decision: str = ""
    history_hash_after: str = ""
    reached: bool = True
    terminated_before_decision: bool = False
    verifier_calls: int = 0
    outcome: float | None = None
    integrity_status: str = "ok"
    condition_label: str = "evaluator_only"

    def __post_init__(self) -> None:
        if self.schema_version != B_BRANCH_V2_SCHEMA:
            raise TreeError(f"unknown schema {self.schema_version!r}")
        if self.action not in {"continue", "verify"}:
            raise TreeError(f"unknown action {self.action!r}")
        if self.decision_index not in (1, 2):
            raise TreeError("decision_index must be 1 or 2")
        if self.integrity_status != "ok" and self.outcome is not None:
            raise TreeError("a non-ok integrity status must not carry an outcome")
        if self.outcome is not None and not (0.0 <= float(self.outcome) <= 1.0):
            raise TreeError("outcome must lie in [0,1]")


def record_allowed_actions(records: list[TreeRecord]) -> None:
    """Each trajectory branch makes at most one verification.

    The three regimes are alternative trajectories on one root, so verify-now
    and verify-later may each consume one call on their own branch.  A single
    branch with two calls, or a checkpoint-2 fork parented to the verify-now
    branch, would be a second verification in one trajectory and is rejected.
    """

    for record in records:
        if record.verifier_calls not in (0, 1):
            raise TreeError(
                f"a branch must make at most one verification, got {record.verifier_calls}"
            )


def records_to_tree(records: list[TreeRecord]) -> dict:
    """Recompute the three regimes for one original root from its records.

    Rejects transplanted checkpoint-2 state, a reached-only denominator, lineage
    or split leakage and a second verification.
    """

    if not records:
        raise TreeError("empty record set")
    roots = {r.root_id for r in records}
    if len(roots) != 1:
        raise TreeError("records_to_tree expects exactly one root")
    record_allowed_actions(records)
    families = {r.template_family_id for r in records}
    splits = {r.split for r in records}
    if len(families) != 1 or len(splits) != 1:
        raise TreeError("lineage or split leakage across records")
    d1 = [r for r in records if r.decision_index == 1]
    d2 = [r for r in records if r.decision_index == 2]
    now_records = [r for r in d1 if r.action == "verify"]
    cont_records = [r for r in d1 if r.action == "continue"]
    if len(now_records) != 1 or len(cont_records) != 1:
        raise TreeError("a root must have one verify-now and one continue decision-1 record")
    cont = cont_records[0]
    if cont.integrity_status != "ok" or now_records[0].integrity_status != "ok":
        raise TreeError("integrity failure blocks a causal tree")
    if not cont.reached:
        if d2:
            raise TreeError("reached-only denominator: later regimes exist though checkpoint 2 was not reached")
        if not cont.terminated_before_decision:
            raise TreeError("a non-reaching root must record terminated_before_decision")
        fallback = cont.outcome
        if fallback is None:
            raise TreeError("a non-reaching fallback must carry an outcome")
        return {
            "schema": B_BRANCH_V2_SCHEMA, "root_id": cont.root_id,
            "template_family_id": cont.template_family_id, "split": cont.split,
            "reached2": False, "now": now_records[0].outcome,
            "later": float(fallback), "never": float(fallback),
        }
    if len(d2) != 2:
        raise TreeError("a reaching root must have both checkpoint-2 records")
    later_records = [r for r in d2 if r.action == "verify"]
    never_records = [r for r in d2 if r.action == "continue"]
    if len(later_records) != 1 or len(never_records) != 1:
        raise TreeError("checkpoint 2 must fork into exactly one verify and one continue")
    expected_parent = cont.branch_id
    h2 = None
    for record in d2:
        if record.parent_branch_id != expected_parent:
            raise TreeError("checkpoint-2 state transplanted from another branch")
        if h2 is None:
            h2 = record.history_hash_at_decision
        elif record.history_hash_at_decision != h2:
            raise TreeError("checkpoint-2 siblings disagree on their decision history")
    if cont.history_hash_after != h2:
        raise TreeError("checkpoint-2 decision history is not the continue branch's state")
    return {
        "schema": B_BRANCH_V2_SCHEMA, "root_id": cont.root_id,
        "template_family_id": cont.template_family_id, "split": cont.split,
        "reached2": True, "now": now_records[0].outcome,
        "later": later_records[0].outcome, "never": never_records[0].outcome,
    }


# --------------------------------------------------------------------------
# Estimators over original roots
# --------------------------------------------------------------------------


def original_root_values(trees: list[dict]) -> dict[str, float]:
    if not trees:
        raise TreeError("empty original-root population")
    return {regime: float(np.mean([t[regime] for t in trees])) for regime in REGIMES}


def theta_difference(trees: list[dict]) -> float:
    values = original_root_values(trees)
    return values["now"] - values["later"]


def value_of_regimes(trees: list[dict], regimes: dict[str, str]) -> float:
    """Mean original-root U for a frozen root -> regime assignment.

    Evaluation takes a precomputed regime map (from the F4 allocator), never an
    arbitrary callable that could read leaf outcomes.
    """

    if not trees:
        raise TreeError("empty original-root population")
    missing = [t["root_id"] for t in trees if t["root_id"] not in regimes]
    if missing:
        raise TreeError(f"regimes missing for roots: {missing[:3]}")
    bad = [r for r in regimes.values() if r not in REGIMES]
    if bad:
        raise TreeError(f"unknown regime(s): {sorted(set(bad))}")
    return float(np.mean([t[regimes[t["root_id"]]] for t in trees]))


def paired_contrast(trees: list[dict], regimes_a: dict[str, str], regimes_b: dict[str, str], *,
                    n_bootstrap: int = 200, seed: int = 20260927) -> dict:
    """Template-family cluster bootstrap with shared draws across two regimes maps.

    Families are the resampling unit; each draw is shared by both maps, so the
    contrast is paired.  No per-root i.i.d. certificate is claimed.
    """

    if not trees:
        raise TreeError("empty original-root population")
    families = sorted({t["template_family_id"] for t in trees})
    index = np.array([families.index(t["template_family_id"]) for t in trees])
    point = value_of_regimes(trees, regimes_a) - value_of_regimes(trees, regimes_b)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_bootstrap):
        drawn = rng.choice(len(families), size=len(families), replace=True)
        idx = np.concatenate([np.flatnonzero(index == t) for t in drawn]).astype(int)
        resampled = [trees[i] for i in idx]
        diffs.append(value_of_regimes(resampled, regimes_a) - value_of_regimes(resampled, regimes_b))
    diffs = np.asarray(diffs)
    return {
        "point": float(point),
        "ci": (float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))),
        "n_bootstrap": n_bootstrap,
        "n_families": len(families),
        "note": "template-family cluster bootstrap with shared draws; batch coupling must be declared",
    }


# --------------------------------------------------------------------------
# The decision view: the only object a controller receives
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DecisionView:
    """What a controller may see at a decision point.

    At checkpoint 1 it exposes ``H1`` (``history``) and no later information.  At
    checkpoint 2 it exposes ``H2`` (which must contain ``H1`` unless a sufficiency
    flag is declared).  Reading leaf outcomes or hidden data raises.
    """

    phase: int
    h1: dict
    h2: dict | None = None
    remaining_budget: int = 0
    progress: float = 0.0
    sufficiency_declared: bool = False

    def __post_init__(self) -> None:
        if self.phase not in (1, 2):
            raise TreeError("decision phase must be 1 or 2")
        if self.phase == 2:
            if self.h2 is None:
                raise TreeError("checkpoint-2 view requires H2")
            if not set(self.h1) <= set(self.h2) and not self.sufficiency_declared:
                raise TreeError(
                    "H2 must contain H1 unless a sufficiency flag is declared"
                )

    @property
    def history(self) -> dict:
        return dict(self.h2) if self.phase == 2 else dict(self.h1)

    def later_state(self) -> dict:
        if self.phase == 1:
            raise TreeError("later-decision information is not available at checkpoint 1")
        return dict(self.h2 or {})

    def outcome(self, *args, **kwargs):
        raise TreeError("a controller must not read leaf outcomes")

    def hidden(self, *args, **kwargs):
        raise TreeError("a controller must not read hidden data")


# --------------------------------------------------------------------------
# The tree driver
# --------------------------------------------------------------------------


class TreeTask(Protocol):
    """A task adapter executed through the real fork path."""

    def prepare(self, workspace: Path, *, template_id: str, root_id: str, seed: int) -> None: ...
    def continue_to_checkpoint2(self, workspace: Path) -> bool: ...
    def verify_and_respond(self, workspace: Path) -> None: ...
    def grade(self, workspace: Path) -> float: ...


def _digest_workspace(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(workspace.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(workspace)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def execute_tree_v2(task: TreeTask, *, root_id: str, template_family_id: str,
                    split: str, seed: int, branch_root: Path,
                    repetitions: int = 2) -> tuple[list[TreeRecord], dict]:
    """Execute the three regimes on one root through the real fork path.

    Each leaf is executed ``repetitions`` (>=2) times and averaged; leaf outcomes
    are treated as noisy samples.  Later and never fork from the same
    checkpoint-2 state.  All outcomes come from executing ``task``; no leaf
    constant is supplied.
    """

    if repetitions < 2:
        raise TreeError("at least two stochastic repetitions per leaf are required")
    snapshots = FileSnapshotManager()
    branches = FileBranchIsolationManager(branch_root, snapshots)
    prefix_ws = branch_root / "prefix" / "workspace"
    prefix_ws.parent.mkdir(parents=True, exist_ok=True)
    task.prepare(prefix_ws, template_id=template_family_id, root_id=root_id, seed=seed)
    snap_dir = branch_root / "snap_c1"
    manifest = snapshots.capture(
        prefix_ws, snap_dir, checkpoint_id="c1", root_id=root_id,
        parent_checkpoint_id=None, budget_remaining={"verifier_calls": 1},
        feasible_regimes=["g0", "gv"],
    )
    h1 = manifest.tree_hash
    records: list[TreeRecord] = []

    def _run(base_id: str, snap_dir: Path, parent: str | None, verify: bool) -> float:
        outcomes = []
        for rep in range(repetitions):
            ws = branches.fork(snap_dir, branch_id=f"{base_id}__r{rep}", parent_branch_id=parent)
            if verify:
                task.verify_and_respond(ws)
            outcomes.append(float(task.grade(ws)))
        return float(np.mean(outcomes))

    now_id = f"{root_id}__now"
    now_outcome = _run(now_id, snap_dir, None, verify=True)
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=1, branch_id=now_id, parent_branch_id=None, action="verify",
        history_hash_at_decision=h1, history_hash_after=h1, reached=True,
        verifier_calls=1, outcome=now_outcome,
    ))

    cont_id = f"{root_id}__cont"
    cont_ws = branches.fork(snap_dir, branch_id=f"{cont_id}__probe", parent_branch_id=None)
    reached2 = bool(task.continue_to_checkpoint2(cont_ws))
    if not reached2:
        fallback = float(task.grade(cont_ws))
        records.append(TreeRecord(
            root_id=root_id, template_family_id=template_family_id, split=split,
            decision_index=1, branch_id=cont_id, parent_branch_id=None, action="continue",
            history_hash_at_decision=h1, history_hash_after=h1, reached=False,
            terminated_before_decision=True, verifier_calls=0, outcome=fallback,
        ))
        return records, records_to_tree(records)

    snap2_dir = branch_root / "snap_c2"
    manifest2 = snapshots.capture(
        cont_ws, snap2_dir, checkpoint_id="c2", root_id=root_id,
        parent_checkpoint_id="c1", budget_remaining={"verifier_calls": 1},
        feasible_regimes=["g0", "gv"],
    )
    h2 = manifest2.tree_hash
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=1, branch_id=cont_id, parent_branch_id=None, action="continue",
        history_hash_at_decision=h1, history_hash_after=h2, reached=True,
        terminated_before_decision=False, verifier_calls=0, outcome=None,
    ))
    later_id = f"{root_id}__later"
    later_outcome = _run(later_id, snap2_dir, cont_id, verify=True)
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=2, branch_id=later_id, parent_branch_id=cont_id, action="verify",
        history_hash_at_decision=h2, history_hash_after=h2, reached=True,
        verifier_calls=1, outcome=later_outcome,
    ))
    never_id = f"{root_id}__never"
    never_outcome = _run(never_id, snap2_dir, cont_id, verify=False)
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=2, branch_id=never_id, parent_branch_id=cont_id, action="continue",
        history_hash_at_decision=h2, history_hash_after=h2, reached=True,
        verifier_calls=0, outcome=never_outcome,
    ))
    tree = records_to_tree(records)
    tree["n_repetitions"] = repetitions
    return records, tree
