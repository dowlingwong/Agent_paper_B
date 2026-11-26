"""D28 (revised criterion 2), PLAN §10 row of 14 Oct 2026: active-key novelty.

A trial is *evaluated* when a worker run happened; skipped trials (including
``inactive_key`` skips) are never evaluated.  An evaluated trial is *novel*
when its active-key configuration differs from the incumbent's **and** from
every configuration evaluated earlier in the campaign, including before a
resume.  The criterion is the share of novel trials among evaluated trials.

The tally comes from one of two sources, decided per campaign ledger:

- ``events``: the control plane's ``edit_novelty`` events carry
  ``active_config_equals_incumbent`` and ``active_config_seen_before`` (and the
  config hashes, D27 F3 fix).  A ledger is scored from events only when every
  evaluated trial has such an event;
- ``replayed``: DT4 and older ledgers have no events.  Each trial's active-key
  configuration is reconstructed by replaying its recorded ``structured_edit``
  from the node's start configuration, applying keeps and restores (a kept
  trial moves the incumbent; any other decision restores it), and projecting
  with the node's *current* declaration.

The replay reuses the control plane's own projection helper so that the two
sources cannot drift.

ENGINEERING_ONLY.  AI-assisted (BUILD_BATCH4, P6).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.campaign import (  # noqa: E402
    _novelty_config,
    _project_active_config,
)
from autoresearch.manager.hyperparam_edits import parse_train_constants  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

EDIT_NOVELTY_EVENT = "edit_novelty"
INACTIVE_KEY_EVENT = "proposal_rejected_inactive_key"

SOURCE_EVENTS = "events"
SOURCE_REPLAYED = "replayed"


@dataclass
class NoveltyTally:
    node: str
    source: str = SOURCE_REPLAYED
    evaluated: int = 0
    novel: int = 0
    equals_incumbent: int = 0
    seen_before: int = 0
    inactive_key_rejections: int = 0

    @property
    def fraction(self) -> float:
        return (self.novel / self.evaluated) if self.evaluated else 0.0

    def merge(self, other: "NoveltyTally") -> None:
        self.evaluated += other.evaluated
        self.novel += other.novel
        self.equals_incumbent += other.equals_incumbent
        self.seen_before += other.seen_before
        self.inactive_key_rejections += other.inactive_key_rejections
        if other.source != self.source:
            self.source = "events+replayed"


def decision_of(record: dict) -> str:
    return str(record.get("decision") or "")


def structured_edit(record: dict) -> dict | None:
    """The recorded structured edit of a trial, wherever the manager stored it."""
    extra = record.get("extra") or {}
    manager = extra.get("manager") or {}
    edit = manager.get("structured_edit") or extra.get("structured_edit")
    return edit if isinstance(edit, dict) else None


def active_projection(effective_config: dict[str, str], node_spec) -> tuple[tuple[str, str], ...]:
    """Hashable active-key projection of an effective config."""
    return tuple(sorted(_project_active_config(effective_config, node_spec).items()))


def replay_tally(records: Iterable[dict], node: str) -> NoveltyTally:
    """Score a legacy ledger by replaying its structured edits (rows 14 Oct).

    The configuration replayed is the same one the ``edit_novelty`` events use:
    the effective config extended with every editable symbol (review F7), so
    the two sources agree trial by trial.
    """
    spec = load_registered_node(node, repo_root=HARNESS)
    constants: dict[str, str] = {}
    for rel in spec.editable_paths:
        constants.update(parse_train_constants(HARNESS / "nodes" / node / rel))
    current = dict(constants)
    incumbent = active_projection(_novelty_config(current, spec), spec)
    seen: set[tuple[tuple[str, str], ...]] = set()
    tally = NoveltyTally(node=node, source=SOURCE_REPLAYED)
    for record in records:
        if decision_of(record) == "skipped":
            continue  # no worker run: never evaluated (D28 revision)
        tally.evaluated += 1
        candidate = dict(current)
        edit = structured_edit(record)
        symbol = str((edit or {}).get("symbol") or "")
        if symbol and symbol in candidate:
            candidate[symbol] = str(edit.get("new"))
        active = active_projection(_novelty_config(candidate, spec), spec)
        equals = active == incumbent
        seen_before = active in seen
        if equals:
            tally.equals_incumbent += 1
        if seen_before:
            tally.seen_before += 1
        if not equals and not seen_before:
            tally.novel += 1
        seen.add(active)
        if decision_of(record) == "kept":
            current = candidate
            incumbent = active
    return tally


def event_is_usable(payload: dict) -> bool:
    return (
        "active_config_equals_incumbent" in payload
        and "active_config_seen_before" in payload
    )


def events_tally(payloads: Iterable[dict], node: str) -> NoveltyTally:
    """Score trials from ``edit_novelty`` events (new runs, resume-aware)."""
    tally = NoveltyTally(node=node, source=SOURCE_EVENTS)
    for payload in payloads:
        tally.evaluated += 1
        equals = bool(payload.get("active_config_equals_incumbent"))
        seen_before = bool(payload.get("active_config_seen_before"))
        if equals:
            tally.equals_incumbent += 1
        if seen_before:
            tally.seen_before += 1
        if not equals and not seen_before:
            tally.novel += 1
    return tally


class Segment:
    """One campaign ledger plus the event stream stored beside it."""

    def __init__(self, node: str, records: list[dict], events_by_trial: dict[str, dict],
                 inactive_key_rejections: int, labels: list[str] | None = None) -> None:
        self.node = node
        self.records = records
        self.events_by_trial = events_by_trial
        self.inactive_key_rejections = inactive_key_rejections
        self.labels = list(labels or [])

    def tally(self) -> NoveltyTally:
        evaluated = [r for r in self.records if decision_of(r) != "skipped"]
        matched = [self.events_by_trial.get(str(r.get("trial_id"))) for r in evaluated]
        if evaluated and all(payload is not None and event_is_usable(payload) for payload in matched):
            result = events_tally(matched, self.node)
        else:
            result = replay_tally(self.records, self.node)
        result.inactive_key_rejections = self.inactive_key_rejections
        return result


def _jsonl_paths(target: str | Path) -> list[Path]:
    path = Path(target)
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.jsonl") if p.is_file())


def _read_lines(path: Path) -> list[dict]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def load_segments(targets: Iterable[str | Path]) -> list[Segment]:
    """Split every jsonl input into trial records and events, one segment per directory.

    A directory holds one campaign ledger (one instance) and, for new runs, its
    event stream beside it.  Event lines are attached to trial records by
    ``trial_id``; event-only files without any trial records are ignored.
    """
    directories: dict[Path, dict] = {}
    for target in targets:
        for path in _jsonl_paths(target):
            bucket = directories.setdefault(
                path.parent, {"records": [], "by_trial": {}, "rejections": 0, "labels": []}
            )
            for item in _read_lines(path):
                event_type = item.get("event_type")
                if event_type == EDIT_NOVELTY_EVENT:
                    bucket["by_trial"][str(item.get("trial_id"))] = dict(item.get("payload") or {})
                elif event_type == INACTIVE_KEY_EVENT:
                    bucket["rejections"] += 1
                elif event_type:
                    continue  # another campaign event: not a trial record
                else:
                    bucket["records"].append(item)
                    if str(path) not in bucket["labels"]:
                        bucket["labels"].append(str(path))
    segments = []
    for _, bucket in sorted(directories.items(), key=lambda item: str(item[0])):
        records = bucket["records"]
        if not records:
            continue
        node = str(records[0].get("node_id") or "unknown")
        segments.append(Segment(node, records, bucket["by_trial"], bucket["rejections"], bucket["labels"]))
    return segments


def tally_segments(segments: Iterable[Segment]) -> dict[str, NoveltyTally]:
    """Aggregate per-node novelty tallies over segments."""
    grouped: dict[str, NoveltyTally] = {}
    for segment in segments:
        entry = grouped.get(segment.node)
        tally = segment.tally()
        if entry is None:
            grouped[segment.node] = tally
        else:
            entry.merge(tally)
    return grouped
