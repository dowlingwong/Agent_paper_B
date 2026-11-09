"""RUNBOOK Track H.2: one featurizer for the online controller and the offline table.

``features_from_view`` is called by ``dataset.build`` (through ``replay_campaign``)
and by the online controller on the harness ``ControlView``.  Acceptance:
replaying every pilot campaign whose ledgers are in this checkout, the features
computed from a real harness ``ControlView`` at each E1 hash-equal the dataset
rows; and audit, sibling and future data are unreachable.
ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import dataclasses
import glob
import json
import math
from pathlib import Path

import pytest

from r1.c3 import dataset as D
from r1.c3.features import (FEATURES, FeatureLeakError, NodeContext, ReplayProposal, ReplayView, features_from_view,
                            features_hash, read_jsonl)
from r1.harness import REPO, import_harness

HARNESS = import_harness()

from autoresearch.control_plane.controller import ControlViewLeakError, build_control_view  # noqa: E402
from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.memory.schemas import TrialRecord  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

PILOT = [s for s in D.SOURCES if (REPO / D.SOURCES[s]["dir"]).exists()]
needs_pilot = pytest.mark.skipif(len(PILOT) < 3, reason="pilot ledgers not present")


def _online_view(rows, i, spec, epoch="E1", provisional=None):
    row = rows[i]
    manager = (row.get("extra") or {}).get("manager") or {}
    proposal = ManagerProposal(manager_mode=row.get("manager_mode", "x"), proposal_summary=row.get("proposal_summary", ""),
                               proposal_rationale="", target_files=tuple(spec.editable_paths), objective="",
                               extra=dict(manager))
    return build_control_view(epoch=epoch, budget_index=int(row["budget_index"]),
                              ledger_prefix=[TrialRecord.from_mapping(r) for r in rows[:i]],
                              current_best=row.get("current_best_before"), proposal=proposal,
                              provisional=provisional, budget={"worker_runs_remaining": 1}, node=spec)


@needs_pilot
def test_online_features_hash_equal_the_dataset_rows(tmp_path):
    D.build(tmp_path, tuple(PILOT))
    table = {r["proposal_id"]: r for r in D.load_table(tmp_path)}
    noise = D.noise_table()
    checked, campaigns = 0, 0
    for name in PILOT:
        src, d = D.SOURCES[name], REPO / D.SOURCES[name]["dir"]
        for f in sorted(glob.glob(str(d / src["ledgers"]))):
            inst = Path(f).parent.name
            node = inst.split("__s")[0]
            spec = load_registered_node(node, repo_root=HARNESS)
            ctx = NodeContext(node=node, start_files=D._start_files(d, inst, node), sigma_node=noise[node]["sigma_node"],
                              runs_total=src["runs"], memory_mode=src["memory_mode"])
            rows = read_jsonl(Path(f))
            campaigns += 1
            for i, row in enumerate(rows):
                pid = f"{name}:{inst}:t{int(row['budget_index']):03d}"
                online = features_from_view(_online_view(rows, i, spec), ctx)
                if pid not in table:  # no dataset row: the trial has no features or no valid metric
                    assert online is None or row["decision"] == "skipped" or not (row.get("parsed_metrics") or {})
                    continue
                assert online is not None, pid
                assert list(online) == list(FEATURES)
                assert features_hash(online) == features_hash(table[pid]["features"]), pid
                checked += 1
    assert checked == len(table) > 1000 and campaigns >= 50


def _ledger():
    def row(b, key, old, new, decision, metric, best):
        return {"budget_index": b, "decision": decision, "parsed_metrics": {"val_score": metric},
                "current_best_before": best, "delta_vs_best": None if best is None else metric - best,
                "extra": {"manager": {"structured_edit": {"symbol": key, "old": old, "new": new, "path": "train.py"}}}}
    return [row(1, "HIDDEN_UNITS", "32", "64", "kept", 0.90, None),
            row(2, "ALPHA", "1e-4", "1e-3", "discarded", 0.89, 0.90),
            row(3, "MAX_ITER", "40", "80", "kept", 0.93, 0.90),
            row(4, "ALPHA", "1e-4", "1e-3", "discarded", 0.91, 0.93)]


CTX = NodeContext(node="digits_mlp", start_files={"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"},
                  sigma_node=0.0075, runs_total=20, memory_mode="none")


def _replay_view(rows, i):
    edit = rows[i]["extra"]["manager"]["structured_edit"]
    return ReplayView(budget_index=rows[i]["budget_index"], ledger_prefix=tuple(rows[:i]),
                      current_best=rows[i]["current_best_before"], proposal=ReplayProposal(extra={"structured_edit": edit}))


def test_node_context_has_only_campaign_constants():
    assert [f.name for f in dataclasses.fields(NodeContext)] == [
        "node", "start_files", "sigma_node", "runs_total", "memory_mode"]
    with pytest.raises(TypeError):
        NodeContext(node="digits_mlp", start_files={}, sigma_node=1.0, runs_total=20, memory_mode="none",
                    audit={"delta": 1.0})  # type: ignore[call-arg]


class _Spy:
    """A view proxy that records which attributes the featurizer reads."""

    def __init__(self, view):
        object.__setattr__(self, "_view", view)
        object.__setattr__(self, "read", set())

    def __getattr__(self, name):
        self.read.add(name)
        return getattr(self._view, name)


def test_featurizer_reads_only_the_prefix_the_incumbent_metric_and_the_edit():
    spec = load_registered_node("digits_mlp", repo_root=HARNESS)
    rows = _ledger()
    prov = TrialRecord.from_mapping(_full(rows[3]))
    spy = _Spy(_online_view([_full(r) for r in rows], 3, spec, epoch="E2", provisional=prov))
    features_from_view(spy, CTX)
    assert spy.read == {"budget_index", "ledger_prefix", "current_best", "proposal"}
    # the current trial's outcome (E2 provisional) does not change the features
    e1 = features_from_view(_online_view([_full(r) for r in rows], 3, spec), CTX)
    e2 = features_from_view(_online_view([_full(r) for r in rows], 3, spec, epoch="E2", provisional=prov), CTX)
    assert features_hash(e1) == features_hash(e2)


def test_future_and_own_outcomes_are_unreachable():
    rows = _ledger()
    base = features_from_view(_replay_view(rows, 3), CTX)
    # a record at or after the current trial in the prefix is refused
    with pytest.raises(FeatureLeakError):
        features_from_view(ReplayView(budget_index=3, ledger_prefix=tuple(rows), current_best=0.93,
                                      proposal=ReplayProposal(extra={})), CTX)
    # changing the current trial's own outcome or later trials changes nothing
    alt = [dict(r) for r in rows]
    alt[3] = {**alt[3], "decision": "kept", "parsed_metrics": {"val_score": 0.99}, "delta_vs_best": 0.06}
    alt.append({**alt[1], "budget_index": 5})
    assert features_hash(features_from_view(_replay_view(alt, 3), CTX)) == features_hash(base)


def test_the_harness_refuses_audit_sibling_and_future_inputs():
    spec = load_registered_node("digits_mlp", repo_root=HARNESS)
    for kwargs in ({"audit_metrics": {"delta_audit": 0.01}}, {"sibling_outcomes": [0.9]},
                   {"future_records": [object()]}):
        with pytest.raises(ControlViewLeakError):
            build_control_view(epoch="E1", budget_index=3, node=spec, **kwargs)


def test_first_trial_and_missing_incumbent_have_no_features():
    rows = _ledger()
    assert features_from_view(_replay_view(rows, 0), CTX) is None
    v = _replay_view(rows, 1)
    assert features_from_view(dataclasses.replace(v, current_best=None), CTX) is None
    assert not math.isnan(features_from_view(v, CTX)["recorded_gain_z"])


def _full(row):
    """A ledger row with every TrialRecord field (for TrialRecord.from_mapping)."""
    b = row["budget_index"]
    return {"trial_id": f"c-trial-{b:03d}", "campaign_id": "c", "node_id": "digits_mlp", "budget_index": b,
            "timestamp_start": "2026-10-25T00:00:00Z", "timestamp_end": "2026-10-25T00:00:01Z",
            "manager_mode": "x", "worker_mode": "local", "memory_mode": "none", "proposal_summary": "s",
            "proposal_rationale": "r", "targeted_files": ["train.py"], "patch_ref": "", "git_commit_before": "",
            "git_commit_after": "", "execution_status": "success", "validity_status": "valid",
            "failure_category": None, "raw_log_ref": "", "parsed_metrics": row["parsed_metrics"],
            "current_best_before": row["current_best_before"], "delta_vs_best": row["delta_vs_best"],
            "decision": row["decision"], "decision_rationale": "", "wall_clock_seconds": 1.0,
            "cumulative_budget_consumed": b,
            "provenance": {k: f"c-trial-{b:03d}" for k in ("proposal_id", "patch_id", "run_id", "metric_id",
                                                             "decision_id")}, "extra": row["extra"]}


def _skip_row(b, control):
    return {"budget_index": b, "decision": "skipped", "parsed_metrics": {}, "current_best_before": 0.93,
            "delta_vs_best": None, "extra": {"control": control}}


@pytest.mark.parametrize("control,counted", [
    ({"epoch": "E1", "action": "skip", "skip_reason": "prior_no_gain"}, False),   # control-plane skip
    ({"epoch": "E1", "action": "skip"}, False),                                    # controller skip, no reason
    ({"epoch": "E1", "action": "skip", "reason": "inactive_key", "key": "x", "revisions": 2}, True),  # D25
])
def test_control_plane_skips_do_not_count_as_invalid(control, counted):
    """Review F2: an online control-plane skip leaves invalid_so_far unchanged (train/deploy parity)."""
    rows = _ledger()[:3] + [_skip_row(4, control)]
    nxt = {"budget_index": 5, "decision": "discarded", "parsed_metrics": {"val_score": 0.91}, "current_best_before": 0.93,
           "delta_vs_best": -0.02,
           "extra": {"manager": {"structured_edit": {"symbol": "ALPHA", "old": "1e-4", "new": "1e-3", "path": "train.py"}}}}
    rows.append(nxt)
    f = features_from_view(_replay_view(rows, 4), CTX)
    assert f["invalid_so_far"] == (1.0 if counted else 0.0)
    # the online path (harness TrialRecords) agrees
    spec = load_registered_node("digits_mlp", repo_root=HARNESS)
    # W2 (R1-SEQ-BUDGET-FIELDS): the harness writes E1 and inactive-key skips with worker_mode "control_plane"
    # (campaign._skipped_record); the fixture now does too, so the worker-run count agrees online and offline.
    full = [_full(r) for r in rows[:3]] + [{**_full({**rows[3], "extra": rows[3]["extra"]}), "parsed_metrics": {},
                                           "worker_mode": "control_plane"}] + \
        [_full(rows[4])]
    online = features_from_view(_online_view(full, 4, spec), CTX)
    assert features_hash(online) == features_hash(f)
