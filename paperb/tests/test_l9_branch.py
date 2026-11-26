"""L9 tests: branch-record contract, leak-safe projection, sibling table, cluster bootstrap, matching."""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from r1.branch.bootstrap import cluster_bootstrap, hoeffding_radius
from r1.branch.matching import ArmDescriptor, MatchingError, matching_report
from r1.branch.schema import (
    R1_BRANCH_SCHEMA,
    BranchRecord,
    BranchRecordError,
    Leaf,
    learner_projection,
    record_from_dict,
    record_to_dict,
    validate_record,
    validate_sibling_sets,
)
from r1.branch.table import build_table, evaluate_choices, run_policy

MASK = {"continue": True, "verify": True, "skip": False}


def rec(instance="i1", budget_index=3, action="continue", ys=(0.1, 0.2), split="dev", features=None,
        mask=None, integrity=None, **kw) -> BranchRecord:
    leaves = tuple(
        Leaf(repetition=k, integrity=(integrity or "ok"), outcome_y=(None if integrity and integrity != "ok" else y),
             cost_worker_runs=5 + (4 if action == "verify" else 0))
        for k, y in enumerate(ys))
    base = dict(schema_version=R1_BRANCH_SCHEMA, instance_id=instance, node="digits_mlp", campaign_id="c1",
                epoch="E2", budget_index=budget_index, action=action, split=split, harness_commit="423addd",
                snapshot_hash="s" + instance + str(budget_index), manager_backend="scripted",
                horizon=3, features=features or {"delta_hat": 0.01, "remaining_runs": 12}, mask=mask or MASK,
                leaves=leaves)
    base.update(kw)
    return BranchRecord(**base)


# -- schema ------------------------------------------------------------------

def test_valid_record_round_trips():
    r = rec()
    validate_record(r)
    assert record_from_dict(record_to_dict(r)) == r


@pytest.mark.parametrize("bad_key", ["outcome_y", "audit_metrics", "test_score", "sibling_outcomes",
                                     "future_records", "instance_id", "leaf_y", "Y"])
def test_leaky_features_are_refused(bad_key):
    with pytest.raises(BranchRecordError):
        validate_record(rec(features={"delta_hat": 0.0, bad_key: 1.0}))


def test_projection_exposes_only_features_mask_epoch():
    proj = learner_projection(rec())
    assert set(proj) == {"features", "mask", "epoch"}
    assert "leaves" not in proj and "instance_id" not in proj["features"]


def test_failed_leaf_cannot_carry_utility():
    bad = dataclasses.replace(rec(), leaves=(Leaf(0, "collection_failure", 0.0, 5),))
    with pytest.raises(BranchRecordError):
        validate_record(bad)
    validate_record(rec(integrity="collection_failure"))  # None outcome is fine


def test_infeasible_action_and_out_of_range_y_are_refused():
    with pytest.raises(BranchRecordError):
        validate_record(rec(action="skip"))
    with pytest.raises(BranchRecordError):
        validate_record(rec(ys=(1.5,)))


def test_sibling_contract():
    ok = [rec(action="continue"), rec(action="verify")]
    assert len(validate_sibling_sets(ok)) == 1
    with pytest.raises(BranchRecordError):  # duplicate unit
        validate_sibling_sets([rec(), rec()])
    with pytest.raises(BranchRecordError):  # siblings disagree on features
        validate_sibling_sets([rec(), rec(action="verify", features={"delta_hat": 0.5, "remaining_runs": 12})])
    with pytest.raises(BranchRecordError):  # instance in two splits
        validate_sibling_sets([rec(budget_index=3), rec(budget_index=4, split="test")])
    with pytest.raises(BranchRecordError):  # no reference action
        validate_sibling_sets([rec(action="verify")])


# -- table -------------------------------------------------------------------

def _table():
    records = []
    for i in range(4):
        for b in (2, 5):
            records.append(rec(instance=f"i{i}", budget_index=b, action="continue", ys=(0.10,)))
            records.append(rec(instance=f"i{i}", budget_index=b, action="verify", ys=(0.15, 0.05)))
    return build_table(records)


def test_table_values_costs_and_fallback():
    t = _table()
    assert len(t) == 8 and set(t.instances) == {"i0", "i1", "i2", "i3"}
    pv = evaluate_choices(t, "verify", ["verify"] * 8)
    assert pv.value == pytest.approx(0.10) and pv.mean_cost == pytest.approx(9)
    sk = evaluate_choices(t, "skip", ["skip"] * 8)  # infeasible -> continue
    assert sk.n_fallback == 8 and sk.value == pytest.approx(0.10)


def test_undefined_values_are_counted_not_imputed():
    records = [rec(instance="a", action="continue", ys=(0.2,)),
               rec(instance="a", action="verify", ys=(0.0,), integrity="collection_failure"),
               rec(instance="b", action="continue", ys=(0.4,)),
               rec(instance="b", action="verify", ys=(0.6,))]
    t = build_table(records)
    pv = evaluate_choices(t, "v", ["verify", "verify"])
    assert pv.n_undefined == 1 and pv.value == pytest.approx(0.6)


def test_policies_see_only_projections():
    t = _table()
    seen = []
    run_policy(t, lambda p: seen.append(p) or "continue")
    assert all(set(p) == {"features", "mask", "epoch"} for p in seen)


# -- bootstrap ---------------------------------------------------------------

def test_bootstrap_known_constant_contrast():
    t = _table()
    cont = np.full(len(t), t.col("continue"))
    ver = np.full(len(t), t.col("verify"))
    res = cluster_bootstrap(t, {"continue": cont, "verify": ver}, contrasts=[("verify", "continue")], n_boot=300)
    assert res.contrasts["verify - continue"] == pytest.approx(0.0, abs=1e-12)
    assert res.contrast_ci["verify - continue"] == pytest.approx((0.0, 0.0), abs=1e-12)
    assert res.n_instances == 4


def test_bootstrap_resamples_instances_not_points():
    # one instance has a huge effect on many points; point-level resampling would understate the spread
    records = []
    for i in range(10):
        n_pts = 10 if i == 0 else 1
        for b in range(1, n_pts + 1):
            records.append(rec(instance=f"i{i}", budget_index=b, action="continue", ys=(0.0,)))
            records.append(rec(instance=f"i{i}", budget_index=b, action="verify", ys=(0.9 if i == 0 else 0.0,)))
    t = build_table(records)
    cols = {"c": np.full(len(t), t.col("continue")), "v": np.full(len(t), t.col("verify"))}
    res = cluster_bootstrap(t, cols, contrasts=[("v", "c")], n_boot=2000, seed=1)
    lo, hi = res.contrast_ci["v - c"]
    assert lo < 0.05  # instance i0 is absent from about a third of draws
    assert hi > 0.6


def test_hoeffding_radius():
    assert hoeffding_radius(100, 0.05) == pytest.approx(2 * np.sqrt(np.log(20) / 200))
    with pytest.raises(ValueError):
        hoeffding_radius(0, 0.05)


# -- matching ----------------------------------------------------------------

def test_matching_report_passes_and_fails():
    a = ArmDescriptor("rho", "rule", "Z_v1", "spend_v1", 6, 40, 40, 27, "dev_v1")
    b = dataclasses.replace(a, name="kg", family="kg_index")
    assert matching_report([a, b])["matched"]
    with pytest.raises(MatchingError):
        matching_report([a, dataclasses.replace(b, tuning_budget=81)])
    with pytest.raises(MatchingError):
        matching_report([a, dataclasses.replace(b, information_set="Z_with_llm_text")])


def test_rejected_forced_action_is_not_scored_as_that_action():
    records = [rec(instance="a", action="continue", ys=(0.2,)),
               rec(instance="a", action="verify", ys=(0.9,), executed_action="continue")]
    t = build_table(records)
    assert not t.feasible[0, t.col("verify")]
    assert evaluate_choices(t, "v", ["verify"]).n_fallback == 1
