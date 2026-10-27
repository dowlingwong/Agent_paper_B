import json

import pytest

from r1.analysis.pilot_figures import PILOT, waste_counts


def test_waste_counts_preserves_strata_and_categories():
    rows = [
        {"source": "a", "node": "n", "memory_mode": "none", "inert": True, "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "none", "inert": True, "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "on", "inert": False, "inert_kind": None},
    ]
    assert waste_counts(rows) == [("a", "n", "none", "duplicate", 2, 2, 1.0), ("a", "n", "on", "non-inert", 1, 1, 1.0)]


def test_rejects_missing_and_contradictory_inert_labels():
    base = {"source": "a", "node": "n", "memory_mode": "none"}
    with pytest.raises(ValueError):
        waste_counts([base])
    with pytest.raises(ValueError):
        waste_counts([{**base, "inert": True, "inert_kind": None}])
    with pytest.raises(ValueError):
        waste_counts([{**base, "inert": False, "inert_kind": "duplicate"}])
    with pytest.raises(ValueError):
        waste_counts([{**base, "inert": True, "inert_kind": "non-inert"}])


def test_committed_pilot_categories_preserve_source_rows():
    with (PILOT / "proposals.jsonl").open() as handle:
        counts = waste_counts(json.loads(line) for line in handle if line.strip())
    assert sum(row[4] for row in counts) == 1323
    assert sum(row[4] for row in counts if row[3] == "duplicate") == 727
    assert all(row[5] > 0 and 0 <= row[6] <= 1 for row in counts)


def test_committed_noise_and_pilot_tables_match_sources_and_labels():
    import csv
    import hashlib

    from r1.analysis.pilot_figures import NOISE, OUT, ROOT

    noise = json.loads(NOISE.read_text())["summaries"]["common_30"]["nodes"]
    with (OUT / "noise_floor.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert {row["node"] for row in rows} == set(noise)
    for row in rows:
        assert row["provisional_status"] == "PILOT; pending author acceptance"
        for column in ("sigma_train", "sigma_split", "sigma_joint"):
            assert float(row[column]) == noise[row["node"]][column]
    gate = json.loads((PILOT / "offline_eval.json").read_text())["instance"]["per_g"]["0.1"]["gate"]
    with (OUT / "offline_pilot.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert {row["node"] for row in rows} == set(gate)
    for row in rows:
        assert row["provisional_status"] == "ENGINEERING_ONLY; historical pilot; not current C3 gate"
        source = gate[row["node"]]
        assert float(row["gain_A3_minus_A2_per20"]) == source["gain_A3_minus_A2_per20"]
        assert [float(row["ci_lower"]), float(row["ci_upper"])] == source["ci95"]
        assert float(row["delta_n"]) == source["delta_n"]
    manifest = json.loads((OUT / "provenance.json").read_text())
    for name, digest in manifest["inputs"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


def test_all_historical_gate_rows_match_each_mode_and_price():
    import csv
    from r1.analysis.pilot_figures import OUT

    result = json.loads((PILOT / "offline_eval.json").read_text())
    with (OUT / "offline_all_gates.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    expected = sum(len(entry["gate"]) for mode in ("instance", "lono") for entry in result[mode]["per_g"].values())
    assert len(rows) == expected
    assert len({(r["mode"], r["g_over_sigma"], r["node"]) for r in rows}) == expected
    for row in rows:
        value = result[row["mode"]]["per_g"][row["g_over_sigma"]]["gate"][row["node"]]
        assert row["provisional_status"] == "ENGINEERING_ONLY; historical pilot; not current C3 gate"
        assert float(row["gain_A3_minus_A2_per20"]) == value["gain_A3_minus_A2_per20"]
        assert [float(row["ci_lower"]), float(row["ci_upper"])] == value["ci95"]
        assert (row["historical_pass"] == "True") is value["pass"]
        assert float(row["delta_n"]) == value["delta_n"]
        assert int(row["instances"]) == value["n_instances"]
        assert int(row["eval_rows"]) == value["n_eval_rows"]
    with (OUT / "offline_all_arms.csv").open() as handle:
        arms = list(csv.DictReader(handle))
    expected_arms = sum(len(node_values) for mode in ("instance", "lono") for entry in result[mode]["per_g"].values() for node_values in entry["arms"].values())
    assert len(arms) == expected_arms
    assert len({(r["mode"], r["g_over_sigma"], r["arm"], r["node"]) for r in arms}) == expected_arms
    for row in arms:
        value = result[row["mode"]]["per_g"][row["g_over_sigma"]]["arms"][row["arm"]][row["node"]]
        assert row["provisional_status"] == "ENGINEERING_ONLY; historical pilot; not current C3 gate"
        for key in ("mean_per_proposal", "per_campaign", "exec_rate"):
            assert float(row[key]) == value[key]


def test_duplicate_figure_includes_zero_duplicate_strata():
    from r1.analysis.pilot_figures import duplicate_shares
    counts = waste_counts([
        {"source": "a", "node": "n", "memory_mode": "off", "inert": True, "inert_kind": "equals_incumbent"},
        {"source": "a", "node": "m", "memory_mode": "on", "inert": True, "inert_kind": "duplicate"},
    ])
    shares = dict(duplicate_shares(counts))
    assert shares == {("a", "m", "on"): 1.0, ("a", "n", "off"): 0.0}
    with (PILOT / "proposals.jsonl").open() as handle:
        counts = waste_counts(json.loads(line) for line in handle if line.strip())
    shares = dict(duplicate_shares(counts))
    assert set(shares) == {tuple(row[:3]) for row in counts}
    assert shares[("dt4", "openml_ionosphere", "none")] == 0.0


def test_rejects_unlabelled_or_non_split_pilot_inputs():
    from r1.analysis.pilot_figures import validate_pilot_inputs
    noise = {'label': 'PILOT', 'summaries': {'common_30': {'label': 'PILOT'}}}
    evaluation = {'label': 'ENGINEERING_ONLY', 'seed_split': True}
    validate_pilot_inputs(noise, evaluation)
    with pytest.raises(ValueError, match='PILOT'):
        validate_pilot_inputs({'label': 'UNKNOWN'}, evaluation)
    with pytest.raises(ValueError, match='seed-split'):
        validate_pilot_inputs(noise, {'label': 'ENGINEERING_ONLY', 'seed_split': False})
