"""C1 duplicate-rate report (PLAN §10, Duplicates 22 Oct). ENGINEERING_ONLY; AI-assisted (Claude)."""
import json
from pathlib import Path

import pytest

from r1.c3 import duplicate_report as DR
from r1.c3.arms import noop_kind
from r1.c3.features import replay_campaign

REPO = Path(__file__).resolve().parents[2]


def _row(source, inst, mode, noop=False, dup=False, active_key=1.0, same_cfg=0.0, symbol="ALPHA", kind=None):
    r = {"source": source, "instance": inst, "node": inst.split("__s")[0], "memory_mode": mode,
         "noop": noop, "duplicate": dup, "edit": {"symbol": symbol} if symbol else {},
         "features": {"active_key": active_key, "cfg_equals_incumbent": same_cfg,
                      "active_equals_incumbent": float(noop), "active_seen_before": float(dup or noop)}}
    if kind:
        r["noop_kind"] = kind
    return r


def test_kinds_counts_fractions_and_wasted_runs():
    rows = [_row("s", "n__s1", "none", noop=True, active_key=0.0),             # inactive edit
            _row("s", "n__s1", "none", noop=True, same_cfg=1.0),               # incumbent repeat (literal)
            _row("s", "n__s1", "none", noop=True),                             # incumbent repeat
            _row("s", "n__s2", "none", dup=True),
            _row("s", "n__s2", "none"), _row("s", "n__s2", "none"),
            _row("s", "n__s3", "append_only_summary", dup=True),
            _row("s", "n__s3", "append_only_summary")]
    rep = DR.report(rows)
    g = {(x["node"], x["memory_mode"]): x for x in rep["groups"]}
    off = g[("n", "none")]
    assert off["proposals"] == 6 and off["campaigns"] == 2
    assert (off["noop_inactive_edit"], off["noop_incumbent_repeat"], off["duplicate"], off["other"]) == (1, 2, 1, 2)
    assert off["noop_literal_no_change"] == 1 and off["noops"] == 3
    assert off["wasted_runs_rho"] == 4 and off["wasted_run_fraction_rho"] == pytest.approx(4 / 6)
    assert off["wasted_runs_rho_per_campaign"] == pytest.approx(2.0)
    assert off["fractions"]["duplicate"] == pytest.approx(1 / 6)
    assert rep["total"]["proposals"] == 8 and rep["total"]["wasted_runs_rho"] == 5
    assert rep["by_memory_mode"]["append_only_summary"]["duplicate"] == 1
    md = DR.markdown(rep)
    assert md.count("\n") == 2 + len(rep["groups"]) + len(rep["by_memory_mode"]) + 1


def test_noop_kind_prefers_table_field_and_derives_otherwise():
    assert noop_kind(_row("s", "n__s1", "none")) is None
    assert noop_kind(_row("s", "n__s1", "none", noop=True, active_key=0.0)) == "inactive_edit"
    assert noop_kind(_row("s", "n__s1", "none", noop=True, active_key=0.0, same_cfg=1.0)) == "incumbent_repeat"
    assert noop_kind(_row("s", "n__s1", "none", noop=True, symbol=None, active_key=0.0)) == "incumbent_repeat"
    assert noop_kind(_row("s", "n__s1", "none", noop=True, kind="inactive_edit")) == "inactive_edit"


def _trial(b, key, old, new, decision, metric, best_before, delta):
    return {"budget_index": b, "decision": decision, "parsed_metrics": {"val_auc": metric},
            "current_best_before": best_before, "delta_vs_best": delta,
            "extra": {"manager": {"structured_edit": {"path": "config.yaml", "symbol": key,
                                                      "old": str(old), "new": str(new)}}}}


def test_replay_emits_noop_kind_for_inactive_and_repeat():
    start = {"config.yaml": "model_type: logistic_regression\nC: 1.0\nn_estimators: 100\nscaler: standard\n"
                            "max_iter: 200\nclass_weight: none\nmax_depth: 3\nlearning_rate: 0.1\n"}
    rows = [_trial(1, "C", 1.0, 2.0, "kept", 0.90, None, None),
            _trial(2, "n_estimators", 100, 200, "discarded", 0.90, 0.90, 0.0),      # inactive under LR
            _trial(3, "C", 2.0, 4.0, "discarded", 0.89, 0.90, -0.01),
            _trial(4, "C", 2.0, 4.0, "discarded", 0.89, 0.90, -0.01)]                # duplicate of trial 3
    props, checks = replay_campaign(rows, start, "openml_breast_w", "openml_breast_w__s1", "src", "none", 20, 0.01)
    kinds = [(p.outcome["noop_kind"], p.outcome["duplicate"]) for p in props]
    assert kinds == [("inactive_edit", False), (None, False), (None, True)]
    assert checks["zero_delta_violations"] == 0


def test_committed_pilot_table_derivation():
    """The committed 19 Oct pilot table (no noop_kind field): DT4 ionosphere no-ops are all inactive edits."""
    table = REPO / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines() if x.strip()]
    rep = DR.report(rows)
    g = {(x["source"], x["node"]): x for x in rep["groups"]}
    assert g[("dt4", "openml_ionosphere")]["noop_inactive_edit"] == 114
    assert rep["total"]["proposals"] == 1323
    assert rep["total"]["noops"] + rep["total"]["duplicate"] == rep["total"]["wasted_runs_rho"]
