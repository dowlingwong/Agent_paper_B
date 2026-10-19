"""C3 features: replay, inert detection, leakage. ENGINEERING_ONLY; AI-assisted (Claude)."""
import copy
import math

import pytest

from r1.c3.features import FEATURES, ReplayError, apply_edit, replay_campaign

START = {"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"}
YAML = {"config.yaml": "model_type: logistic_regression\nC: 0.15\nmax_depth: 5\nscaler: standard\n"
        "class_weight: balanced\nn_estimators: 100\nlearning_rate: 0.05\nimputer: most_frequent\nmax_iter: 1000\n"}


def row(b, key, old, new, decision, metric, best, path="train.py"):
    return {"budget_index": b, "decision": decision, "parsed_metrics": {"val_score": metric},
            "current_best_before": best, "delta_vs_best": None if best is None else metric - best,
            "extra": {"manager": {"structured_edit": {"symbol": key, "old": old, "new": new, "path": path}}}}


def ledger():
    return [
        row(1, "HIDDEN_UNITS", "32", "64", "kept", 0.90, None),
        row(2, "ALPHA", "1e-4", "1e-3", "discarded", 0.89, 0.90),
        row(3, "ALPHA", "1e-4", "1e-3", "discarded", 0.89, 0.90),     # duplicate of trial 2
        row(4, "MAX_ITER", "40", "80", "kept", 0.93, 0.90),
        row(5, "MAX_ITER", "80", "40", "discarded", 0.90, 0.93),      # back to trial-1 config: seen
        row(6, "HIDDEN_UNITS", "64", "128", "discarded", 0.92, 0.93),
    ]


def test_apply_edit_like_worker():
    out = apply_edit(START, {"symbol": "ALPHA", "old": "1e-4", "new": "1e-3", "path": "train.py"})
    assert "ALPHA = 1e-3\n" in out["train.py"] and START["train.py"] != out["train.py"]
    with pytest.raises(ValueError):
        apply_edit(START, {"symbol": "ALPHA", "old": "5", "new": "1e-3", "path": "train.py"})
    y = apply_edit(YAML, {"symbol": "class_weight", "old": "balanced", "new": "null", "path": "config.yaml"})
    assert "class_weight: null" in y["config.yaml"]


def test_replay_inert_and_flags():
    props, checks = replay_campaign(ledger(), START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075)
    assert [p.budget_index for p in props] == [2, 3, 4, 5, 6]
    inert = {p.budget_index: p.outcome["inert"] for p in props}
    assert inert == {2: False, 3: True, 4: False, 5: True, 6: False}
    p3 = props[1]
    assert p3.features["active_seen_before"] == 1.0 and p3.features["same_edit_count"] == 1.0
    p5 = props[3]
    assert p5.features["reverse_of_last_key_edit"] == 1.0 and p5.features["keeps_so_far"] == 2.0
    p6 = props[4]
    assert "HIDDEN_UNITS = 64" in p6.incumbent_files["train.py"] and "MAX_ITER = 80" in p6.incumbent_files["train.py"]
    assert "HIDDEN_UNITS = 128" in p6.candidate_files["train.py"]
    assert p6.features["key_edit_count"] == 1.0 and p6.features["last_key_kept"] == 1.0
    assert checks["zero_delta_violations"] == 0 and checks["repeat_metric_violations"] == 0
    assert set(FEATURES) == set(p6.features)


def test_no_leakage_from_own_or_future_outcomes():
    base, _ = replay_campaign(ledger(), START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075)
    led = ledger()
    # change the outcome of trial 4 (metric only, same decision) and everything after it
    for r in led[3:]:
        r["parsed_metrics"]["val_score"] += 0.05
        r["delta_vs_best"] = r["parsed_metrics"]["val_score"] - r["current_best_before"]
    alt, _ = replay_campaign(led, START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075, check=False)
    for a, b in zip(base, alt):
        if a.budget_index <= 4:
            assert a.features == b.features or all(
                (math.isnan(x) and math.isnan(y)) or x == y for x, y in zip(a.features.values(), b.features.values()))


def test_repeat_metric_check_detects_bad_replay():
    led = ledger()
    led[2]["parsed_metrics"]["val_score"] = 0.80  # duplicate config with a different metric
    _, checks = replay_campaign(led, START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075)
    assert checks["repeat_metric_violations"] == 1


def test_inactive_key_is_inert_on_openml():
    led = [row(1, "C", "0.15", "0.3", "kept", 0.99, None, "config.yaml"),
           row(2, "max_depth", "5", "7", "discarded", 0.99, 0.99, "config.yaml"),   # inactive for LR
           row(3, "model_type", "logistic_regression", "random_forest", "discarded", 0.98, 0.99, "config.yaml")]
    props, checks = replay_campaign(led, YAML, "openml_breast_w", "openml_breast_w__s105", "t", "x", 20, 0.0039)
    assert props[0].outcome["inert"] and props[0].outcome["inert_kind"] == "equals_incumbent"
    assert props[0].features["active_key"] == 0.0
    assert not props[1].outcome["inert"] and props[1].features["structural"] == 1.0
    assert checks["zero_delta_violations"] == 0


def test_stale_edit_raises():
    led = ledger()
    led[1]["extra"]["manager"]["structured_edit"]["old"] = "9"
    with pytest.raises(ReplayError):
        replay_campaign(led, START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075)
