"""D28/P4: the liveness criteria on the committed DT4 ledgers and edge cases.

Criterion 2 was revised on 14 Oct 2026 to active-key novelty (PLAN §10).  The
DT4 LLM rerun (memory_mode none, no edit_novelty events) is degenerate on both
nodes under the new criterion: openml_ionosphere never leaves its incumbent's
active configuration (its edits name n_estimators, inert under the committed
logistic_regression model_type), and digits_mlp repeats configurations with
memory off.  Its ledgers are therefore scored by the replay path.  AI-assisted
(BUILD_BATCH3 P4; revised in BUILD_BATCH4, P6).
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.harness import harness_root
from r1.liveness import evaluate_ledger_paths, evaluate_records, write_reports
from r1.liveness.novelty import load_segments, replay_tally

HARNESS = harness_root()

DT4_ROOTS = (
    Path(__file__).resolve().parents[2]
    / "results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots"
)
SMOKE_LEDGERS = (
    Path(__file__).resolve().parents[2]
    / "results/r1/engineering/liveness_scripted_20261014T075806Z/ledgers"
)


def test_dt4_ionosphere_fails_for_the_right_reasons():
    report = evaluate_ledger_paths([DT4_ROOTS])
    ionosphere = report["nodes"]["openml_ionosphere"]
    assert ionosphere["pass"] is False
    assert set(ionosphere["failed_criteria"]) == {"keep_after_trial_1", "active_novelty_fraction"}
    assert ionosphere["criteria"]["keep_after_trial_1"]["observed"] == 0
    novelty = ionosphere["criteria"]["active_novelty_fraction"]
    assert novelty["observed"] == 0.0
    assert (novelty["novel_trials"], novelty["evaluated_trials"]) == (0, 120)
    assert novelty["novelty_source"] == "replayed"
    assert ionosphere["criteria"]["invalid_rate"]["observed"] == 0.0
    assert ionosphere["inactive_key_rejections"] == 0
    assert ionosphere["n_trials"] == 120


def _independent_digits_recomputation() -> tuple[int, int, int]:
    """Second, simple recomputation of the DT4 digits numbers (no liveness code).

    digits_mlp has no active-key declaration, so the active configuration is
    the full effective configuration; this tracks it with plain tuples and a
    hand-rolled keep/restore replay.
    """
    from autoresearch.manager.hyperparam_edits import build_effective_config, parse_train_constants
    from autoresearch.nodes.registry import load_registered_node

    spec = load_registered_node("digits_mlp", repo_root=HARNESS)
    start: dict[str, str] = {}
    for rel in spec.editable_paths:
        start.update(parse_train_constants(HARNESS / "nodes" / "digits_mlp" / rel))
    evaluated = novel = keeps_after_trial_1 = 0
    for ledger in sorted(DT4_ROOTS.glob("digits_mlp__*/root_trials.jsonl")):
        current = dict(start)
        incumbent = dict(start)
        seen: set[tuple] = set()
        for line in ledger.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("decision") == "skipped":
                continue
            evaluated += 1
            edit = ((record.get("extra") or {}).get("manager") or {}).get("structured_edit")
            candidate = dict(current)
            if isinstance(edit, dict) and edit.get("symbol") in candidate:
                candidate[edit["symbol"]] = str(edit["new"])
            key = tuple(sorted(build_effective_config(candidate).items()))
            incumbent_key = tuple(sorted(build_effective_config(incumbent).items()))
            if key != incumbent_key and key not in seen:
                novel += 1
            seen.add(key)
            if record.get("decision") == "kept":
                if record.get("budget_index", 0) > 1:
                    keeps_after_trial_1 += 1
                current = candidate
                incumbent = candidate
    return evaluated, novel, keeps_after_trial_1


def test_dt4_digits_is_pinned_after_an_independent_recomputation():
    # DT4 ran with memory off, so a novelty FAIL here is the honest outcome;
    # PASS is never forced.  The numbers are pinned.
    report = evaluate_ledger_paths([DT4_ROOTS])
    digits = report["nodes"]["digits_mlp"]
    novelty = digits["criteria"]["active_novelty_fraction"]
    assert novelty["novelty_source"] == "replayed"
    assert (
        novelty["novel_trials"], novelty["evaluated_trials"],
        digits["criteria"]["keep_after_trial_1"]["observed"],
    ) == (8, 120, 11)
    assert digits["criteria"]["invalid_rate"]["observed"] == 0.0
    assert digits["pass"] is False
    assert digits["failed_criteria"] == ["active_novelty_fraction"]
    assert (novelty["evaluated_trials"], novelty["novel_trials"],
            digits["criteria"]["keep_after_trial_1"]["observed"]) == _independent_digits_recomputation()


def test_report_and_markdown_files_are_written_per_node(tmp_path):
    report = evaluate_ledger_paths([DT4_ROOTS])
    out = write_reports(report, tmp_path / "reports")
    payload = json.loads((out / "liveness.json").read_text())
    assert set(payload["nodes"]) == {"digits_mlp", "openml_ionosphere"}
    for node in ("digits_mlp", "openml_ionosphere"):
        assert (out / f"{node}.json").exists()
        markdown = (out / f"{node}.md").read_text()
        assert ("PASS" if payload["nodes"][node]["pass"] else "FAIL") in markdown
        assert payload["nodes"][node]["novelty_source"] in markdown
    assert "ENGINEERING_ONLY" in (out / "liveness.md").read_text()


def _record(index, decision, edit=None, node="openml_ionosphere", budget_consumed=None):
    record = {
        "node_id": node, "budget_index": index, "decision": decision,
        "trial_id": f"{node}-trial-{index:03d}",
        "parsed_metrics": {"val_auc": 0.9}, "current_best_before": 0.9,
        "extra": {"manager": {"structured_edit": edit}} if edit else {},
        "cumulative_budget_consumed": budget_consumed or index,
    }
    return record


def test_skipped_trials_are_not_evaluated_and_rejections_are_separate():
    # T1 changes C (active under logistic_regression): novel.
    # T2 is skipped with an edit that would have been novel: never evaluated.
    # T3 changes n_estimators (inert under logistic_regression): equals the
    # incumbent's active configuration, so not novel.
    records = [
        _record(1, "kept", {"symbol": "C", "old": "0.15", "new": "0.9", "path": "config.yaml"}),
        _record(2, "skipped", {"symbol": "model_type", "old": "logistic_regression",
                               "new": "gradient_boosting", "path": "config.yaml"}),
        _record(3, "discarded", {"symbol": "n_estimators", "old": "100", "new": "200",
                                 "path": "config.yaml"}),
    ]
    entry = evaluate_records(records)["openml_ionosphere"]
    assert entry.evaluated == 2  # the skipped trial is excluded
    assert entry.novel == 1
    assert entry.novelty_fraction == 0.5
    verdict = entry.verdict()
    assert verdict["criteria"]["active_novelty_fraction"]["evaluated_trials"] == 2
    assert "active_novelty_fraction" not in verdict["failed_criteria"]  # 1/2 >= 0.5


def test_novelty_fraction_boundary_requires_evaluated_trials():
    one_of_three = [
        _record(1, "kept", {"symbol": "C", "old": "0.15", "new": "0.9", "path": "config.yaml"}),
        _record(2, "discarded", {"symbol": "n_estimators", "old": "100", "new": "200", "path": "config.yaml"}),
        _record(3, "discarded", {"symbol": "n_estimators", "old": "100", "new": "300", "path": "config.yaml"}),
    ]
    entry = evaluate_records(one_of_three)["openml_ionosphere"]
    assert entry.novel == 1 and entry.evaluated == 3
    assert "active_novelty_fraction" in entry.verdict()["failed_criteria"]
    empty = evaluate_records([_record(1, "skipped")])["openml_ionosphere"]
    assert empty.evaluated == 0
    assert "active_novelty_fraction" in empty.verdict()["failed_criteria"]  # never a vacuous pass


def test_events_are_preferred_and_inactive_rejections_counted(tmp_path):
    directory = tmp_path / "ledgers" / "openml_ionosphere__s103"
    directory.mkdir(parents=True)
    records = [_record(1, "kept"), _record(2, "discarded")]
    (directory / "root_trials.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n"
    )
    events = [
        {"event_type": "edit_novelty", "trial_id": "openml_ionosphere-trial-001",
         "payload": {"active_config_equals_incumbent": False, "active_config_seen_before": False}},
        {"event_type": "edit_novelty", "trial_id": "openml_ionosphere-trial-002",
         "payload": {"active_config_equals_incumbent": True, "active_config_seen_before": True}},
        {"event_type": "proposal_rejected_inactive_key", "trial_id": "openml_ionosphere-trial-002",
         "payload": {"key": "imputer", "revision": 0}},
        {"event_type": "proposal_rejected_inactive_key", "trial_id": "openml_ionosphere-trial-002",
         "payload": {"key": "imputer", "revision": 1, "skipped": True}},
        {"event_type": "decision_made", "trial_id": "openml_ionosphere-trial-002",
         "payload": {"decision": "kept"}},
    ]
    (directory / "root_events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    report = evaluate_ledger_paths([tmp_path / "ledgers"])
    verdict = report["nodes"]["openml_ionosphere"]
    novelty = verdict["criteria"]["active_novelty_fraction"]
    assert novelty["novelty_source"] == "events"
    assert (novelty["evaluated_trials"], novelty["novel_trials"]) == (2, 1)
    assert verdict["inactive_key_rejections"] == 2


def test_events_without_active_flags_fall_back_to_replay(tmp_path):
    directory = tmp_path / "ledgers" / "openml_ionosphere__s103"
    directory.mkdir(parents=True)
    records = [_record(1, "kept", {"symbol": "C", "old": "0.15", "new": "0.9", "path": "config.yaml"})]
    (directory / "root_trials.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    old_event = {"event_type": "edit_novelty", "trial_id": "openml_ionosphere-trial-001",
                 "payload": {"config_equals_incumbent": False, "config_seen_before": False,
                             "metric_identical_to_incumbent": False}}
    (directory / "root_events.jsonl").write_text(json.dumps(old_event) + "\n")
    verdict = evaluate_ledger_paths([tmp_path / "ledgers"])["nodes"]["openml_ionosphere"]
    novelty = verdict["criteria"]["active_novelty_fraction"]
    assert novelty["novelty_source"] == "replayed"
    assert (novelty["evaluated_trials"], novelty["novel_trials"]) == (1, 1)


def test_scripted_smoke_wdbc_passes_under_the_revised_criterion():
    # PLAN §10 D28 revision: the old metric-different criterion failed wdbc
    # (7/18) although the scripted proposer kept proposing novel configurations;
    # the active-key novelty criterion passes it.
    report = evaluate_ledger_paths([SMOKE_LEDGERS])
    wdbc = report["nodes"]["openml_wdbc"]
    novelty = wdbc["criteria"]["active_novelty_fraction"]
    assert novelty["novelty_source"] == "events"
    assert wdbc["pass"] is True
    assert (novelty["novel_trials"], novelty["evaluated_trials"]) == (19, 20)
    digits = report["nodes"]["digits_mlp"]
    assert digits["pass"] is False
    assert digits["failed_criteria"] == ["active_novelty_fraction"]
    assert (digits["criteria"]["active_novelty_fraction"]["novel_trials"],
            digits["criteria"]["active_novelty_fraction"]["evaluated_trials"]) == (7, 20)


def test_smoke_events_and_replay_agree_per_segment():
    for segment in load_segments([SMOKE_LEDGERS]):
        events = segment.tally()
        replayed = replay_tally(segment.records, segment.node)
        assert (events.evaluated, events.novel) == (replayed.evaluated, replayed.novel), segment.node
