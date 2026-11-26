"""D28 liveness criteria over campaign ledgers (P4; criterion 2 revised 14 Oct).

Criteria (PLAN §10 rows D28 and D28 (revised criterion 2)):

- ``keep_after_trial_1``: at least one kept trial with ``budget_index > 1``;
- ``active_novelty_fraction``: at least 50 % of *evaluated* trials have an
  active-key configuration that differs from the incumbent's and from every
  configuration evaluated earlier in the campaign, including before a resume.
  A trial is evaluated when a worker run happened; skipped trials, including
  ``inactive_key`` skips, are not evaluated.  Ledgers without ``edit_novelty``
  events (DT4 and older) are scored by replaying their structured edits
  (:mod:`r1.liveness.novelty`), and the report states
  ``novelty_source: events | replayed``;
- ``invalid_rate``: failed-invalid trials below 30 % of all trials.

The inactive-key rejections are reported as a separate count.  A node passes
only when all three criteria hold.  Output is JSON and Markdown per node.

AI-assisted (BUILD_BATCH3 P4; revised in BUILD_BATCH4, P6); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from r1.liveness.novelty import (
    INACTIVE_KEY_EVENT,
    SOURCE_EVENTS,
    SOURCE_REPLAYED,
    NoveltyTally,
    decision_of,
    load_segments,
    replay_tally,
    tally_segments,
)

KEEP_AFTER_TRIAL_1 = "keep_after_trial_1"
ACTIVE_NOVELTY_FRACTION = "active_novelty_fraction"
INVALID_RATE = "invalid_rate"
CRITERIA = (KEEP_AFTER_TRIAL_1, ACTIVE_NOVELTY_FRACTION, INVALID_RATE)

NOVELTY_MIN = 0.50
INVALID_RATE_MAX = 0.30


@dataclass
class NodeLiveness:
    node: str
    ledgers: list[str] = field(default_factory=list)
    n_trials: int = 0
    keeps_after_trial_1: int = 0
    invalid: int = 0
    evaluated: int = 0
    novel: int = 0
    equals_incumbent: int = 0
    seen_before: int = 0
    inactive_key_rejections: int = 0
    novelty_sources: set[str] = field(default_factory=set)

    @property
    def novelty_fraction(self) -> float:
        return (self.novel / self.evaluated) if self.evaluated else 0.0

    @property
    def invalid_rate(self) -> float:
        return (self.invalid / self.n_trials) if self.n_trials else 0.0

    @property
    def novelty_source(self) -> str:
        if self.novelty_sources == {SOURCE_EVENTS}:
            return SOURCE_EVENTS
        if self.novelty_sources == {SOURCE_REPLAYED}:
            return SOURCE_REPLAYED
        return "+".join(sorted(self.novelty_sources)) or SOURCE_REPLAYED

    def verdict(self) -> dict:
        failed = []
        if self.keeps_after_trial_1 < 1:
            failed.append(KEEP_AFTER_TRIAL_1)
        if not (self.evaluated and self.novelty_fraction >= NOVELTY_MIN):
            failed.append(ACTIVE_NOVELTY_FRACTION)
        if not (self.invalid_rate < INVALID_RATE_MAX):
            failed.append(INVALID_RATE)
        return {
            "node": self.node,
            "pass": not failed,
            "failed_criteria": failed,
            "criteria": {
                "keep_after_trial_1": {
                    "required": "at least 1 keep with budget_index > 1",
                    "observed": self.keeps_after_trial_1,
                },
                "active_novelty_fraction": {
                    "required": f">= {NOVELTY_MIN}",
                    "observed": self.novelty_fraction,
                    "novel_trials": self.novel,
                    "evaluated_trials": self.evaluated,
                    "equals_incumbent_trials": self.equals_incumbent,
                    "seen_before_trials": self.seen_before,
                    "novelty_source": self.novelty_source,
                },
                "invalid_rate": {
                    "required": f"< {INVALID_RATE_MAX}",
                    "observed": self.invalid_rate,
                },
            },
            "inactive_key_rejections": self.inactive_key_rejections,
            "novelty_source": self.novelty_source,
            "n_trials": self.n_trials,
            "ledgers": list(self.ledgers),
        }


def _add_segment(entry: NodeLiveness, records: list[dict], tally: NoveltyTally, labels: list[str]) -> None:
    for label in labels:
        if label not in entry.ledgers:
            entry.ledgers.append(label)
    for record in records:
        entry.n_trials += 1
        index = record.get("budget_index")
        decision = decision_of(record)
        if decision == "failed_invalid":
            entry.invalid += 1
        elif decision == "kept" and isinstance(index, int) and index > 1:
            entry.keeps_after_trial_1 += 1
    entry.evaluated += tally.evaluated
    entry.novel += tally.novel
    entry.equals_incumbent += tally.equals_incumbent
    entry.seen_before += tally.seen_before
    entry.inactive_key_rejections += tally.inactive_key_rejections
    entry.novelty_sources.add(tally.source)


def evaluate_segments(segments) -> dict[str, NodeLiveness]:
    grouped: dict[str, NodeLiveness] = {}
    for segment in segments:
        entry = grouped.setdefault(segment.node, NodeLiveness(node=segment.node))
        _add_segment(entry, segment.records, segment.tally(), segment.labels)
    return grouped


def evaluate_records(records: Iterable[dict], node: str | None = None) -> dict[str, NodeLiveness]:
    """Aggregate bare trial records per node, scoring novelty by replay."""
    grouped: dict[str, NodeLiveness] = {}
    by_node: dict[str, list[dict]] = {}
    for record in records:
        node_id = str(node or record.get("node_id") or "unknown")
        by_node.setdefault(node_id, []).append(record)
        grouped.setdefault(node_id, NodeLiveness(node=node_id))
    for node_id, node_records in by_node.items():
        _add_segment(grouped[node_id], node_records, replay_tally(node_records, node_id), [])
    return grouped


def evaluate_ledger_paths(
    targets: Iterable[str | Path],
    *,
    generated_utc: str | None = None,
    manager_kind: str | None = None,
    memory_mode: str | None = None,
) -> dict:
    """Evaluate every ledger below *targets*; one JSON-able report.

    ``manager_kind`` records which proposer produced the ledgers
    (``"scripted"`` or ``"langgraph"``); ``memory_mode`` records the mode they
    ran with.  The D28 gate only accepts an LLM-backed, memory-on manifest
    (review F5 and the revised D28 row).
    """
    segments = load_segments(targets)
    grouped: dict[str, NodeLiveness] = evaluate_segments(segments)
    return {
        "schema": "r1.liveness/2",
        "label": "ENGINEERING_ONLY",
        "generated_utc": generated_utc or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "manager_kind": manager_kind,
        "memory_mode": memory_mode,
        "criteria": {
            "keep_after_trial_1": "at least one keep after trial 1",
            "active_novelty_fraction": (
                f">= {NOVELTY_MIN} of evaluated trials; novelty_source events or replayed"
            ),
            "invalid_rate": f"< {INVALID_RATE_MAX}",
        },
        "nodes": {node: entry.verdict() for node, entry in sorted(grouped.items())},
    }


def _markdown(node: str, verdict: dict, label: str = "ENGINEERING_ONLY") -> str:
    criteria = verdict["criteria"]
    novelty = criteria["active_novelty_fraction"]
    status = "PASS" if verdict["pass"] else "FAIL"
    lines = [
        f"# Liveness: {node} — {status}",
        "",
        f"{label} (D28, revised criterion 2). Thresholds: keep after trial 1 ≥ 1; "
        f"active-key novelty ≥ {NOVELTY_MIN} of evaluated trials; invalid rate < {INVALID_RATE_MAX}.",
        "",
        "| criterion | required | observed |",
        "|---|---|---|",
        f"| keep_after_trial_1 | {criteria['keep_after_trial_1']['required']} | "
        f"{criteria['keep_after_trial_1']['observed']} |",
        f"| active_novelty_fraction | {novelty['required']} | {novelty['observed']:.4f} "
        f"({novelty['novel_trials']}/{novelty['evaluated_trials']}, {novelty['novelty_source']}) |",
        f"| invalid_rate | {criteria['invalid_rate']['required']} | "
        f"{criteria['invalid_rate']['observed']:.4f} |",
        "",
        f"Evaluated trials: {novelty['evaluated_trials']} "
        f"(equals incumbent {novelty['equals_incumbent_trials']}, seen before {novelty['seen_before_trials']}).",
        f"Inactive-key rejections (separate count): {verdict['inactive_key_rejections']}.",
        f"Trials: {verdict['n_trials']}. Failed criteria: "
        f"{', '.join(verdict['failed_criteria']) or 'none'}.",
        "",
        "Ledgers:",
    ]
    lines += [f"- `{path}`" for path in verdict["ledgers"]]
    return "\n".join(lines) + "\n"


def write_reports(report: dict, out_dir: str | Path) -> Path:
    """Write ``liveness.json``, ``liveness.md`` and per-node files."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "liveness.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [f"# Liveness report ({report['label']})", "", f"Generated: {report['generated_utc']}", "",
               "| node | pass | failed criteria | evaluated | novel | source |", "|---|---|---|---|---|---|"]
    for node, verdict in report["nodes"].items():
        novelty = verdict["criteria"]["active_novelty_fraction"]
        summary.append(
            f"| {node} | {'PASS' if verdict['pass'] else 'FAIL'} | "
            f"{', '.join(verdict['failed_criteria']) or '—'} | {novelty['evaluated_trials']} | "
            f"{novelty['novel_trials']} | {novelty['novelty_source']} |"
        )
    (out / "liveness.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    for node, verdict in report["nodes"].items():
        (out / f"{node}.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / f"{node}.md").write_text(_markdown(node, verdict, report["label"]), encoding="utf-8")
    return out
