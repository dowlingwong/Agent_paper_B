"""D28 liveness criteria over campaign ledgers (P4).

Criteria (PLAN §10 D28), aggregated per node over every ledger given:

- ``keep_after_trial_1``: at least one kept trial with ``budget_index > 1``;
- ``metric_diff_fraction``: at least 50 % of trials have a metric different
  from the incumbent's.  A trial counts when it carries the node metric and an
  incumbent exists (``current_best_before`` is not None); the comparison is
  bit-exact (``!=`` on floats).  If no trial is comparable the criterion fails;
- ``invalid_rate``: failed-invalid trials below 30 % of all trials.

A node passes only when all three hold.  Output is JSON and Markdown per node.

AI-assisted (BUILD_BATCH3, P4); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.nodes.registry import load_registered_node  # noqa: E402

KEEP_AFTER_TRIAL_1 = "keep_after_trial_1"
METRIC_DIFF_FRACTION = "metric_diff_fraction"
INVALID_RATE = "invalid_rate"
CRITERIA = (KEEP_AFTER_TRIAL_1, METRIC_DIFF_FRACTION, INVALID_RATE)

METRIC_DIFF_MIN = 0.50
INVALID_RATE_MAX = 0.30


def _decision(record: dict) -> str:
    return str(record.get("decision") or "")


def _metric_name(node: str) -> str:
    try:
        return load_registered_node(node, repo_root=HARNESS).metric_name
    except Exception:  # noqa: BLE001 - an unregistered node is still checkable
        return "val_score"


@dataclass
class NodeLiveness:
    node: str
    ledgers: list[str] = field(default_factory=list)
    n_trials: int = 0
    keeps_after_trial_1: int = 0
    metric_comparable: int = 0
    metric_different: int = 0
    invalid: int = 0

    @property
    def metric_diff_fraction(self) -> float:
        return (self.metric_different / self.metric_comparable) if self.metric_comparable else 0.0

    @property
    def invalid_rate(self) -> float:
        return (self.invalid / self.n_trials) if self.n_trials else 0.0

    def verdict(self) -> dict:
        failed = []
        if self.keeps_after_trial_1 < 1:
            failed.append(KEEP_AFTER_TRIAL_1)
        if not (self.metric_comparable and self.metric_diff_fraction >= METRIC_DIFF_MIN):
            failed.append(METRIC_DIFF_FRACTION)
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
                "metric_diff_fraction": {
                    "required": f">= {METRIC_DIFF_MIN}",
                    "observed": self.metric_diff_fraction,
                    "metric_comparable_trials": self.metric_comparable,
                    "metric_different_trials": self.metric_different,
                },
                "invalid_rate": {
                    "required": f"< {INVALID_RATE_MAX}",
                    "observed": self.invalid_rate,
                },
            },
            "n_trials": self.n_trials,
            "ledgers": list(self.ledgers),
        }


def evaluate_records(records: Iterable[dict], node: str | None = None) -> dict[str, NodeLiveness]:
    """Aggregate trial records per node into :class:`NodeLiveness`."""
    grouped: dict[str, NodeLiveness] = {}
    for record in records:
        node_id = str(node or record.get("node_id") or "unknown")
        entry = grouped.setdefault(node_id, NodeLiveness(node=node_id))
        entry.n_trials += 1
        index = record.get("budget_index")
        decision = _decision(record)
        if decision == "failed_invalid":
            entry.invalid += 1
        elif decision == "kept" and isinstance(index, int) and index > 1:
            entry.keeps_after_trial_1 += 1
        metric_name = _metric_name(node_id)
        incumbent = record.get("current_best_before")
        value = (record.get("parsed_metrics") or {}).get(metric_name)
        if value is not None and incumbent is not None:
            entry.metric_comparable += 1
            if float(value) != float(incumbent):
                entry.metric_different += 1
    return grouped


def _read_ledger(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _ledger_paths(target: str | Path) -> list[Path]:
    path = Path(target)
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.jsonl") if p.is_file())


def evaluate_ledger_paths(targets: Iterable[str | Path], *, generated_utc: str | None = None) -> dict:
    """Evaluate every ledger below *targets*; one JSON-able report."""
    paths: list[Path] = []
    for target in targets:
        paths.extend(_ledger_paths(target))
    grouped: dict[str, NodeLiveness] = {}
    for path in paths:
        records = _read_ledger(path)
        for node, entry in evaluate_records(records).items():
            existing = grouped.setdefault(node, NodeLiveness(node=node))
            existing.ledgers.append(str(path))
            existing.n_trials += entry.n_trials
            existing.keeps_after_trial_1 += entry.keeps_after_trial_1
            existing.metric_comparable += entry.metric_comparable
            existing.metric_different += entry.metric_different
            existing.invalid += entry.invalid
    return {
        "schema": "r1.liveness/1",
        "label": "ENGINEERING_ONLY",
        "generated_utc": generated_utc or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "criteria": {
            "keep_after_trial_1": "at least one keep after trial 1",
            "metric_diff_fraction": f">= {METRIC_DIFF_MIN} of comparable trials",
            "invalid_rate": f"< {INVALID_RATE_MAX}",
        },
        "nodes": {node: entry.verdict() for node, entry in sorted(grouped.items())},
    }


def _markdown(node: str, verdict: dict) -> str:
    criteria = verdict["criteria"]
    status = "PASS" if verdict["pass"] else "FAIL"
    lines = [
        f"# Liveness: {node} — {status}",
        "",
        "ENGINEERING_ONLY (D28). Thresholds: keep after trial 1 ≥ 1; "
        f"metric-different fraction ≥ {METRIC_DIFF_MIN}; invalid rate < {INVALID_RATE_MAX}.",
        "",
        "| criterion | required | observed |",
        "|---|---|---|",
        f"| keep_after_trial_1 | {criteria['keep_after_trial_1']['required']} | "
        f"{criteria['keep_after_trial_1']['observed']} |",
        f"| metric_diff_fraction | {criteria['metric_diff_fraction']['required']} | "
        f"{criteria['metric_diff_fraction']['observed']:.4f} "
        f"({criteria['metric_diff_fraction']['metric_different_trials']}/"
        f"{criteria['metric_diff_fraction']['metric_comparable_trials']}) |",
        f"| invalid_rate | {criteria['invalid_rate']['required']} | "
        f"{criteria['invalid_rate']['observed']:.4f} |",
        "",
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
               "| node | pass | failed criteria | trials |", "|---|---|---|---|"]
    for node, verdict in report["nodes"].items():
        summary.append(
            f"| {node} | {'PASS' if verdict['pass'] else 'FAIL'} | "
            f"{', '.join(verdict['failed_criteria']) or '—'} | {verdict['n_trials']} |"
        )
    (out / "liveness.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    for node, verdict in report["nodes"].items():
        (out / f"{node}.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / f"{node}.md").write_text(_markdown(node, verdict), encoding="utf-8")
    return out
