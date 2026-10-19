"""C3 dataset on the committed pilot ledgers (file-only). ENGINEERING_ONLY; AI-assisted (Claude)."""
import json

import pytest

from r1.c3 import dataset as D
from r1.harness import REPO


def test_noise_table_matches_d18_examples():
    nt = D.noise_table()
    assert nt["digits_mlp"]["delta_n"] == pytest.approx(0.002)
    assert nt["openml_ionosphere"]["delta_n"] == pytest.approx(0.004, abs=5e-4)  # PLAN D18 "~0.004"
    assert nt["tabular_mlp"]["sigma_node"] == pytest.approx(0.004569527692588516)
    assert nt["openml_breast_w"]["sigma_local"] < nt["openml_breast_w"]["sigma_structural"]


@pytest.mark.skipif(not (REPO / D.SOURCES["rerun2A"]["dir"]).exists(), reason="pilot data not present")
def test_build_replays_without_violations_and_di_candidates(tmp_path):
    meta = D.build(tmp_path)
    tot = meta["replay_checks_total"]
    assert tot["zero_delta_violations"] == 0 and tot["repeat_metric_violations"] == 0
    rows = D.load_table(tmp_path)
    assert len(rows) == meta["n_proposals"] > 1000
    assert all(r["budget_index"] >= 2 for r in rows)
    di = D.di_candidates(rows)
    assert len(di) == 19
    plan = D.plan(tmp_path, {("dt4", "digits_mlp"): 5}, include_di=True)
    assert sum("di" in p["reason"] for p in plan) == 19
    assert plan == D.plan(tmp_path, {("dt4", "digits_mlp"): 5}, include_di=True)  # seeded
