"""Append-only, deterministic ledger for Paper B runs (runbook step 2).

The ledger mirrors every tree event as a ``ReliabilityEvent`` from the copied
harness schema (``control.reliability_schema``).  Three rules make it
reproducible, which the upstream factories are not:

- **deterministic ids**: ``event_id = sha256(run|root|branch|step|type)[:16]``;
- **timing out of the hashed row**: wall-clock times go to a sidecar file,
  never into the event payload or its hashes;
- **full row hash**: every ledger row carries ``row_sha256`` over the canonical
  event JSON, and ``validate_stream`` recomputes it, checks that parent ids
  resolve to earlier rows and that ``monotonic_step`` never decreases.

The ledger is the record of what ran.  ``export_tree`` rebuilds the
``TreeRecord`` set and the decision-time histories from it, so the analysis
can be reproduced from the ledger alone.  Outcomes are written with visibility
``sealed_test_outcome``; histories carry no outcome field (the serialiser
rejects such kinds).  Nothing here is evidence.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from causal_branch.control.branch_tree import TreeRecord, records_to_tree
from causal_branch.control.configurator.serialiser import (
    DecisionHistory, history_from_json, history_to_json,
)
from causal_branch.control.reliability_schema import (
    SCHEMA_VERSION, AdjudicationRecord, AdjudicationStatus, EventVisibility,
    ReliabilityEvent, ReliabilityEventType,
)

LEDGER_SCHEMA = f"reliability-{SCHEMA_VERSION}"
EVENTS_FILE = "events.jsonl"
TIMING_FILE = "timing.jsonl"


class LedgerError(ValueError):
    """The ledger was tampered with, is out of order, or cannot be exported."""


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def event_id(run_id: str, root_id: str, branch_id: str, step: int, event_type: str) -> str:
    return hashlib.sha256(f"{run_id}|{root_id}|{branch_id}|{step}|{event_type}".encode()).hexdigest()[:16]


def make_event(*, run_id: str, root_id: str, branch_id: str, step: int,
               event_type: ReliabilityEventType, payload: dict, parents: Iterable[str] = (),
               actor_type: str = "executor", actor_id: str = "b_tree_executor",
               visibility: EventVisibility = EventVisibility.POLICY_VISIBLE,
               artifact_refs: Iterable[str] = ()) -> ReliabilityEvent:
    """Construct an event directly: deterministic id, no wall-clock time."""

    payload = {"root_id": root_id, "branch_id": branch_id, **payload}
    return ReliabilityEvent(
        event_id=event_id(run_id, root_id, branch_id, step, event_type.value),
        run_id=run_id, parent_event_ids=tuple(parents), event_type=event_type,
        actor_type=actor_type, actor_id=actor_id, monotonic_step=step,
        wall_time_utc="-", payload=payload, artifact_refs=tuple(artifact_refs),
        visibility_class=visibility,
    )


def row_for(event: ReliabilityEvent) -> dict:
    body = event.to_dict()
    body["wall_time_utc"] = "-"  # timing lives in the sidecar
    return {**body, "row_sha256": hashlib.sha256(_canonical(body)).hexdigest()}


class Ledger:
    """Append-only JSONL under ``<run_dir>/ledger/``."""

    def __init__(self, run_dir: Path, run_id: str) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.dir = self.run_dir / "ledger"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.dir / EVENTS_FILE
        self.timing_path = self.dir / TIMING_FILE
        self._ids: set[str] = {r["event_id"] for r in self.rows()}
        self._last_step = max((r["monotonic_step"] for r in self.rows()), default=-1)

    # -- writing ----------------------------------------------------------
    def append(self, event: ReliabilityEvent, *, wall_time_utc: str = "") -> dict:
        if event.event_id in self._ids:
            raise LedgerError(f"duplicate event id {event.event_id}")
        for parent in event.parent_event_ids:
            if parent not in self._ids:
                raise LedgerError(f"parent event {parent} is not in the ledger")
        if event.monotonic_step < self._last_step:
            raise LedgerError("monotonic_step decreased")
        row = row_for(event)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        if wall_time_utc:
            with self.timing_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event_id": event.event_id, "wall_time_utc": wall_time_utc},
                                        sort_keys=True) + "\n")
        self._ids.add(event.event_id)
        self._last_step = event.monotonic_step
        return row

    # -- reading ----------------------------------------------------------
    def rows(self) -> list[dict]:
        if not self.events_path.is_file():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def events(self) -> list[ReliabilityEvent]:
        return [ReliabilityEvent.from_dict({k: v for k, v in r.items() if k != "row_sha256"})
                for r in self.rows()]

    def digest(self) -> str:
        return hashlib.sha256(self.events_path.read_bytes()).hexdigest() if self.events_path.is_file() else ""


def validate_stream(rows: list[dict]) -> list[str]:
    """Recompute row hashes, resolve parents, check step order.  Returns errors."""

    errors: list[str] = []
    seen: set[str] = set()
    last = -1
    for n, row in enumerate(rows):
        body = {k: v for k, v in row.items() if k != "row_sha256"}
        if hashlib.sha256(_canonical(body)).hexdigest() != row.get("row_sha256"):
            errors.append(f"row {n}: row_sha256 mismatch")
        event = ReliabilityEvent.from_dict(body)
        if event.event_id in seen:
            errors.append(f"row {n}: duplicate event id")
        for parent in event.parent_event_ids:
            if parent not in seen:
                errors.append(f"row {n}: parent {parent} not earlier in the stream")
        if event.monotonic_step < last:
            errors.append(f"row {n}: monotonic_step decreased")
        if body.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"row {n}: schema version {body.get('schema_version')}")
        seen.add(event.event_id)
        last = event.monotonic_step
    return errors


# --------------------------------------------------------------------------
# Tree -> events
# --------------------------------------------------------------------------


def events_for_tree(*, run_id: str, records: list[TreeRecord], histories: dict,
                    adjudicator_version: str = "cc_live_evaluator") -> list[ReliabilityEvent]:
    """The event stream for one executed root.

    Per root: a proposal; per record: action_request, state_snapshot,
    verifier_request/result when a verification was executed, terminal_outcome
    (sealed) and an adjudication.  H1 and H2 are attached to the proposal and to
    the continue branch's snapshot respectively.
    """

    if not records:
        raise LedgerError("no records")
    root_id = records[0].root_id
    family = records[0].template_family_id
    h1: DecisionHistory = histories["h1"]
    h2: DecisionHistory | None = histories.get("h2")
    step = 0
    out: list[ReliabilityEvent] = []

    proposal = make_event(run_id=run_id, root_id=root_id, branch_id="prefix", step=step,
                          event_type=ReliabilityEventType.PROPOSAL,
                          payload={"template_family_id": family, "split": records[0].split,
                                   "proposed_action": "grow_three_regime_tree",
                                   "declared_objective": "paired verification-timing contrast",
                                   "h1": history_to_json(h1)})
    out.append(proposal)
    step += 1
    for record in sorted(records, key=lambda r: (r.decision_index, r.branch_id)):
        parents = (proposal.event_id,)
        request = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                             event_type=ReliabilityEventType.ACTION_REQUEST, parents=parents,
                             payload={"action_type": record.action,
                                      "decision_index": record.decision_index,
                                      "parent_branch_id": record.parent_branch_id,
                                      "history_hash_at_decision": record.history_hash_at_decision})
        out.append(request)
        step += 1
        snap_payload = {"history_hash_after": record.history_hash_after,
                        "reached": record.reached,
                        "terminated_before_decision": record.terminated_before_decision}
        if record.decision_index == 1 and record.action == "continue" and record.reached and h2 is not None:
            snap_payload["h2"] = history_to_json(h2)
        snapshot = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                              event_type=ReliabilityEventType.STATE_SNAPSHOT,
                              parents=(request.event_id,), payload=snap_payload)
        out.append(snapshot)
        step += 1
        last = snapshot
        if record.verifier_calls:
            vreq = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                              event_type=ReliabilityEventType.VERIFIER_REQUEST,
                              parents=(last.event_id,), payload={"verifier_calls": record.verifier_calls})
            out.append(vreq)
            step += 1
            vres = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                              event_type=ReliabilityEventType.VERIFIER_RESULT,
                              parents=(vreq.event_id,), payload={"executed": True})
            out.append(vres)
            step += 1
            last = vres
        if record.outcome is not None:
            outcome = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                                 event_type=ReliabilityEventType.TERMINAL_OUTCOME,
                                 parents=(last.event_id,),
                                 payload={"U": float(record.outcome),
                                          "integrity_status": record.integrity_status},
                                 visibility=EventVisibility.SEALED_TEST_OUTCOME)
            out.append(outcome)
            step += 1
            adjudication = AdjudicationRecord(
                adjudication_id=event_id(run_id, root_id, record.branch_id, step, "adjudication"),
                run_id=run_id, step_index=step, execution_success=record.integrity_status == "ok",
                scientific_validity=record.outcome is not None,
                deterministic_checks=["candidate.json present", "outcome in [0,1]"],
                verifier_versions=[adjudicator_version],
                final_status=(AdjudicationStatus.ACCEPTED if record.integrity_status == "ok"
                              else AdjudicationStatus.INSUFFICIENT_EVIDENCE))
            adj = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                             event_type=ReliabilityEventType.ADJUDICATION, parents=(outcome.event_id,),
                             payload={"adjudication": {**asdict(adjudication),
                                                       "final_status": adjudication.final_status.value}},
                             visibility=EventVisibility.ADJUDICATION_ONLY,
                             actor_type="adjudicator", actor_id=adjudicator_version)
            out.append(adj)
            step += 1
        else:
            integrity = make_event(run_id=run_id, root_id=root_id, branch_id=record.branch_id, step=step,
                                   event_type=ReliabilityEventType.EVIDENCE, parents=(last.event_id,),
                                   payload={"integrity_status": record.integrity_status,
                                            "outcome": None})
            out.append(integrity)
            step += 1
    return out


def write_tree(ledger: Ledger, records: list[TreeRecord], histories: dict, *,
               wall_time_utc: str = "") -> list[dict]:
    rows = []
    for event in events_for_tree(run_id=ledger.run_id, records=records, histories=histories):
        rows.append(ledger.append(event, wall_time_utc=wall_time_utc))
    return rows


# --------------------------------------------------------------------------
# Events -> tree
# --------------------------------------------------------------------------


def export_tree(events: list[ReliabilityEvent]) -> dict[str, dict]:
    """Rebuild ``{root_id: {"records": [...], "tree": {...}, "histories": {...}}}``."""

    by_root: dict[str, dict] = {}
    pending: dict[str, dict] = {}
    for event in events:
        p = event.payload
        root = p.get("root_id")
        branch = p.get("branch_id")
        entry = by_root.setdefault(root, {"records": {}, "h1": None, "h2": None,
                                          "family": None, "split": None})
        if event.event_type == ReliabilityEventType.PROPOSAL:
            entry["h1"] = history_from_json(p["h1"])
            entry["family"], entry["split"] = p["template_family_id"], p["split"]
        elif event.event_type == ReliabilityEventType.ACTION_REQUEST:
            pending[(root, branch)] = {"action": p["action_type"], "decision_index": p["decision_index"],
                                       "parent_branch_id": p["parent_branch_id"],
                                       "history_hash_at_decision": p["history_hash_at_decision"],
                                       "verifier_calls": 0, "outcome": None, "integrity_status": "ok"}
        elif event.event_type == ReliabilityEventType.STATE_SNAPSHOT:
            rec = pending[(root, branch)]
            rec.update(history_hash_after=p["history_hash_after"], reached=p["reached"],
                       terminated_before_decision=p["terminated_before_decision"])
            if "h2" in p:
                entry["h2"] = history_from_json(p["h2"])
        elif event.event_type == ReliabilityEventType.VERIFIER_REQUEST:
            pending[(root, branch)]["verifier_calls"] = int(p["verifier_calls"])
        elif event.event_type == ReliabilityEventType.TERMINAL_OUTCOME:
            pending[(root, branch)]["outcome"] = float(p["U"])
            pending[(root, branch)]["integrity_status"] = p["integrity_status"]
        elif event.event_type == ReliabilityEventType.EVIDENCE:
            pending[(root, branch)]["integrity_status"] = p["integrity_status"]
    for (root, branch), rec in pending.items():
        entry = by_root[root]
        entry["records"][branch] = TreeRecord(
            root_id=root, template_family_id=entry["family"], split=entry["split"], branch_id=branch,
            **rec)
    out = {}
    for root, entry in by_root.items():
        records = [entry["records"][b] for b in sorted(entry["records"])]
        out[root] = {"records": records, "tree": records_to_tree(records),
                     "histories": {"h1": entry["h1"], "h2": entry["h2"]}}
    return out
