"""P7: e1b_compare on the committed fixtures and the paired-bootstrap path.

Fixtures: the DT4 LLM rerun (memory off) as B and the 12 Oct scripted run as C
on their two shared nodes; a copied scripted manifest supplies an A for the
three-arm readings path.  AI-assisted (BUILD_BATCH4, P7); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
import pytest

from r1.baselines.evaluate import evaluate_arms
from r1.branch.table import build_table
from r1.headroom.e1b_compare import (
    _pair_deltas,
    compare,
    load_arm,
    markdown,
    paired_memory_effect,
)

PILOT = Path(__file__).resolve().parents[2] / "results/r1/pilot"
DT4 = PILOT / "E1b_20261013T151857Z"
SCRIPTED = PILOT / "E1b_20261012T161034Z"
N_BOOT = 200


def test_two_arm_report_reproduces_the_committed_analysis():
    result = compare([("B", DT4), ("C", SCRIPTED)], n_boot=N_BOOT)
    assert result["nodes"] == ["digits_mlp", "openml_ionosphere"]
    committed = json.loads((DT4 / "analysis.json").read_text())
    for node in result["nodes"] + ["ALL"]:
        expected = committed["per_node"][node]["contrasts"]["always_verify - rho"]
        observed = result["per_node"][node]["arms"]["B"]["contrasts"]["always_verify - rho"]["point"]
        assert observed == pytest.approx(expected, abs=1e-12)
        # the full per-node contrast family is present for both arms
        for label in ("B", "C"):
            for name in ("always_verify - rho", "kg_index - rho", "margin_threshold - rho"):
                assert name in result["per_node"][node]["arms"][label]["contrasts"]
    assert result["per_node"]["digits_mlp"]["memory_effect"] is None
    assert "note" in result["readings"]
    json.dumps(result, default=str)  # serialisable
    text = markdown(result)
    assert "PILOT" in text
    # no A: the readings are explicitly not computed (never silently skipped)
    assert "Readings (template only)" in text
    assert "not computed" in text


def test_paired_memory_effect_uses_shared_instance_draws():
    arm_a = load_arm("A", SCRIPTED)
    arm_b = load_arm("B", DT4)
    table_a = build_table([r for r in arm_a.records if r.node == "digits_mlp"])
    table_b = build_table([r for r in arm_b.records if r.node == "digits_mlp"])
    rep_a = evaluate_arms(table_a, n_boot=20, seed=20261012)
    rep_b = evaluate_arms(table_b, n_boot=20, seed=20261012)
    effect = paired_memory_effect(table_a, rep_a.choices, table_b, rep_b.choices, n_boot=173, seed=11)
    assert effect["instances_matched"] is True
    assert effect["n_instances"] == 6
    assert effect["n_boot"] == 173
    assert math.isfinite(effect["point_estimate"])
    assert effect["ci"][0] <= effect["ci"][1]

    # one shared resample feeds both arms: reproduce the first draw by hand
    deltas = _pair_deltas(table_a, rep_a.choices, table_b, rep_b.choices, n_boot=173, seed=11)
    assert len(deltas) == effect["n_boot"] - effect["n_degenerate_draws"]
    assert deltas
    instances = sorted(set(table_a.instances.tolist()))
    rng = np.random.default_rng(11)
    picked = rng.choice(len(instances), size=len(instances), replace=True)
    rows_a = np.concatenate([np.flatnonzero(table_a.instances == instances[k]) for k in picked])
    rows_b = np.concatenate([np.flatnonzero(table_b.instances == instances[k]) for k in picked])
    value_a = (np.nanmean(table_a.value[rows_a, rep_a.choices["always_verify"][rows_a]])
               - np.nanmean(table_a.value[rows_a, rep_a.choices["rho"][rows_a]]))
    value_b = (np.nanmean(table_b.value[rows_b, rep_b.choices["always_verify"][rows_b]])
               - np.nanmean(table_b.value[rows_b, rep_b.choices["rho"][rows_b]]))
    assert deltas[0] == pytest.approx(value_b - value_a)


def test_three_arm_readings_are_bonferroni_adjusted(tmp_path):
    arm_a = tmp_path / "arm_a"
    arm_a.mkdir()
    shutil.copy2(SCRIPTED / "records.jsonl", arm_a / "records.jsonl")
    shutil.copy2(SCRIPTED / "manifest.json", arm_a / "manifest.json")
    result = compare([("A", arm_a), ("B", DT4), ("C", SCRIPTED)], n_boot=N_BOOT)
    readings = result["readings"]
    assert readings["bonferroni_m"] == 2  # one primary contrast per shared node
    assert readings["adjusted_level"] == pytest.approx(1 - 0.05 / 2)
    for node in ("digits_mlp", "openml_ionosphere"):
        entry = readings["per_node"][node]
        assert entry["reading"] in {"supported", "inconclusive", "opposite"}
        assert entry["adjusted_ci"][0] <= entry["adjusted_ci"][1]
    assert result["per_node"]["ALL"]["memory_effect"] is not None
    assert "note" not in readings
    text = markdown(result)
    assert "Bonferroni over m = 2" in text
    assert "supported if the adjusted lower bound is > 0" in text
    assert "inconclusive" in text or "supported" in text or "opposite" in text
