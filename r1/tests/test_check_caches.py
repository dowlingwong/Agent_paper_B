"""Offline cache readiness check (r1/noise/check_caches.py). ENGINEERING_ONLY; AI-assisted (Claude)."""
import json
from pathlib import Path

from r1.noise import check_caches as CC
from r1.noise import e1_noise_floor as E1


def _fake_harness(tmp_path, monkeypatch):
    root = tmp_path / "harness"
    cfg = {"dataset": {"dataset_id": 1}, "active_keys": {"dataset_excluded": ["imputer"]}}
    for node, cache in (("openml_a", "empty"), ("openml_b", "none"), ("openml_c", "pilot"), ("openml_d", "own")):
        (root / "nodes" / node).mkdir(parents=True)
        (root / "configs" / "nodes").mkdir(parents=True, exist_ok=True)
        (root / "configs" / "nodes" / f"{node}.yaml").write_text(json.dumps(cfg))
        if cache in ("empty", "own"):
            (root / "nodes" / node / "data_cache").mkdir()
            (root / "nodes" / node / "data_cache" / ".gitkeep").write_text("\n")
        if cache == "own":
            (root / "nodes" / node / "data_cache" / "openml").mkdir()
            (root / "nodes" / node / "data_cache" / "openml" / "x.gz").write_text("x")
        if cache == "pilot":
            pilot = root / E1.PILOT_DATA_CACHE.format(node=node)
            pilot.mkdir(parents=True)
            (pilot / "x.gz").write_text("x")
    monkeypatch.setattr(CC, "HARNESS", root)
    return root


def test_cache_source_mirrors_prepare_node(tmp_path, monkeypatch):
    _fake_harness(tmp_path, monkeypatch)
    # an existing but empty data_cache blocks the pilot fallback in E1._prepare_node
    assert CC.cache_source("openml_a")[0].startswith("cache missing (node data_cache is empty)")
    assert CC.cache_source("openml_b")[0].startswith("cache missing (no node data_cache")
    assert CC.cache_source("openml_c")[0] == "L8 pilot fallback"
    assert CC.cache_source("openml_d")[0] == "node data_cache"


def test_check_node_reports_missing_and_skips_non_openml(tmp_path, monkeypatch):
    _fake_harness(tmp_path, monkeypatch)
    assert CC.check_node("digits_mlp", tmp_path)["status"] == "skipped"
    assert CC.check_node("openml_a", tmp_path)["status"] == "cache missing"
    assert CC.check_node("openml_zzz", tmp_path)["status"] == "not in harness"


def test_common_node_list_and_e1_defaults():
    assert len(CC.COMMON_NODES) == 10
    for node in ("openml_credit_g", "openml_sonar", "openml_blood_transfusion", "openml_qsar_biodeg"):
        assert node in CC.COMMON_NODES and node in E1.DEFAULT_NODES
