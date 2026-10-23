"""C3 dataset on the committed pilot ledgers (file-only). ENGINEERING_ONLY; AI-assisted (Claude)."""
import json

import pytest

from r1.c3 import dataset as D
from r1.harness import REPO


E1_12OCT = REPO / "results/r1/pilot/E1_20261012T145353Z/summary.json"


def test_noise_table_matches_d18_examples():
    # PLAN D18's examples were computed from the 12 Oct E1 (10 seeds); the formula must reproduce them.
    nt = D.noise_table(E1_12OCT)
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


def test_noise_table_omits_nodes_without_e1_data():
    # 22 Oct pool extension: nodes known to the C3 pipeline but absent from the
    # E1 summary get no (invented) noise constants.
    nt = D.noise_table(E1_12OCT)
    for node in ("openml_credit_g", "openml_sonar", "openml_blood_transfusion", "openml_qsar_biodeg"):
        assert node not in nt
    assert {"digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
            "openml_credit_approval"} <= set(nt)


def test_default_noise_table_is_the_common_30_seed_run():
    """22 Oct: the default E1 source is the common 30-seed run (the C1 noise-floor table) over ten nodes."""
    assert D.E1_SUMMARY.startswith("results/r1/pilot/E1_20261022T214606Z/")
    nt = D.noise_table()
    assert set(nt) == set(D.NODE_INFO) - {"openml_climate"}  # reserve node: not in the common run
    assert nt["openml_ionosphere"]["delta_n"] == pytest.approx(0.004, abs=5e-4)
    assert nt["openml_sonar"]["delta_n"] == pytest.approx(0.0032, abs=1e-4)
    for node in ("digits_mlp", "tabular_mlp", "openml_breast_w", "openml_wdbc", "openml_credit_approval",
                 "openml_blood_transfusion"):
        assert nt[node]["delta_n"] == pytest.approx(0.002)
