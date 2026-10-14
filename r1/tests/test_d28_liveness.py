"""D28/P4: the liveness criteria on the committed DT4 ledgers and edge cases.

The DT4 LLM rerun (memory_mode none) is degenerate on openml_ionosphere: every
trial after trial 1 repeats the incumbent metric exactly, and no keep happened
after trial 1.  digits_mlp is live.  AI-assisted (BUILD_BATCH3, P4).
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.liveness import evaluate_ledger_paths, evaluate_records, write_reports

DT4_ROOTS = (
    Path(__file__).resolve().parents[2]
    / "results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots"
)


def test_dt4_ionosphere_fails_for_the_right_reasons():
    report = evaluate_ledger_paths([DT4_ROOTS])
    ionosphere = report["nodes"]["openml_ionosphere"]
    assert ionosphere["pass"] is False
    assert set(ionosphere["failed_criteria"]) == {"keep_after_trial_1", "metric_diff_fraction"}
    assert ionosphere["criteria"]["keep_after_trial_1"]["observed"] == 0
    assert ionosphere["criteria"]["metric_diff_fraction"]["observed"] == 0.0
    assert ionosphere["criteria"]["metric_diff_fraction"]["metric_comparable_trials"] == 114
    assert ionosphere["criteria"]["invalid_rate"]["observed"] == 0.0
    assert ionosphere["n_trials"] == 120


def test_dt4_digits_passes():
    report = evaluate_ledger_paths([DT4_ROOTS])
    digits = report["nodes"]["digits_mlp"]
    assert digits["pass"] is True
    assert digits["failed_criteria"] == []
    assert digits["criteria"]["keep_after_trial_1"]["observed"] == 11
    assert digits["criteria"]["metric_diff_fraction"]["observed"] > 0.80
    assert digits["criteria"]["invalid_rate"]["observed"] == 0.0


def test_report_and_markdown_files_are_written_per_node(tmp_path):
    report = evaluate_ledger_paths([DT4_ROOTS])
    out = write_reports(report, tmp_path / "reports")
    payload = json.loads((out / "liveness.json").read_text())
    assert set(payload["nodes"]) == {"digits_mlp", "openml_ionosphere"}
    for node in ("digits_mlp", "openml_ionosphere"):
        assert (out / f"{node}.json").exists()
        markdown = (out / f"{node}.md").read_text()
        assert ("PASS" if payload["nodes"][node]["pass"] else "FAIL") in markdown
    assert "ENGINEERING_ONLY" in (out / "liveness.md").read_text()


def _record(index, decision, metric=None, incumbent=None, node="openml_ionosphere"):
    return {
        "node_id": node, "budget_index": index, "decision": decision,
        "parsed_metrics": {} if metric is None else {"val_auc": metric},
        "current_best_before": incumbent,
    }


def _invalid_rate_entry(n_discarded):
    records = [_record(1, "kept", 0.9)]
    records += [_record(i, "failed_invalid") for i in range(2, 6)]  # 4 invalid
    records += [_record(i, "discarded", 0.9 - 0.001 * i, 0.9) for i in range(6, 6 + n_discarded)]
    entry = evaluate_records(records)["openml_ionosphere"]
    return entry


def test_invalid_rate_boundary_is_strictly_below_30_percent():
    # 4/13 = 0.3077 fails the criterion; 4/15 = 0.2667 passes it.
    failed = _invalid_rate_entry(8)
    assert failed.invalid_rate >= 0.30
    assert "invalid_rate" in failed.verdict()["failed_criteria"]
    passed = _invalid_rate_entry(10)
    assert passed.invalid_rate < 0.30
    assert "invalid_rate" not in passed.verdict()["failed_criteria"]


def test_metric_diff_fraction_needs_comparable_trials():
    records = [_record(1, "kept", 0.9), _record(2, "discarded", 0.9, 0.9)]
    entry = evaluate_records(records)["openml_ionosphere"]
    assert entry.metric_comparable == 1
    assert entry.metric_diff_fraction == 0.0
    assert "metric_diff_fraction" in entry.verdict()["failed_criteria"]


def test_keeps_at_or_before_trial_1_do_not_count():
    records = [_record(1, "kept", 0.9)]
    entry = evaluate_records(records)["openml_ionosphere"]
    assert entry.keeps_after_trial_1 == 0
    assert "keep_after_trial_1" in entry.verdict()["failed_criteria"]
