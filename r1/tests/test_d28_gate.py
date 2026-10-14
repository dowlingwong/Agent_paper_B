"""D28/P5: the require_live gate and its wiring into the batch runner.

AI-assisted (BUILD_BATCH3, P5); ENGINEERING_ONLY.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from r1.harness import harness_root
from r1.liveness import load_liveness_manifest, require_live

HARNESS = harness_root()
SCRIPT_MODULE = "r1.scripts.deepthought_batch1_resume"


def _manifest(*verdicts):
    return {"nodes": {node: verdict for node, verdict in verdicts}}


def test_gate_passes_when_every_node_is_live():
    manifest = _manifest(
        ("digits_mlp", {"pass": True, "failed_criteria": []}),
        ("openml_ionosphere", {"pass": True, "failed_criteria": []}),
    )
    assert require_live(["digits_mlp", "openml_ionosphere"], manifest) is manifest


def test_gate_raises_stop_for_a_failed_node():
    manifest = _manifest(("openml_ionosphere", {"pass": False, "failed_criteria": ["keep_after_trial_1"]}))
    with pytest.raises(RuntimeError, match=r"^STOP: .*openml_ionosphere"):
        require_live(["openml_ionosphere"], manifest)


def test_gate_raises_stop_for_a_missing_node():
    manifest = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}))
    with pytest.raises(RuntimeError, match=r"^STOP: no liveness verdict"):
        require_live(["digits_mlp", "openml_wdbc"], manifest)


def test_gate_accepts_a_bare_verdict_mapping():
    manifest = {"digits_mlp": {"pass": True, "failed_criteria": []}}
    assert require_live(["digits_mlp"], manifest) is manifest


def test_load_manifest_rejects_non_reports(tmp_path):
    path = tmp_path / "not.json"
    path.write_text(json.dumps({"nodes": {}}))
    assert load_liveness_manifest(path)["nodes"] == {}
    path.write_text(json.dumps([1, 2, 3]))
    with pytest.raises(ValueError):
        load_liveness_manifest(path)


def _load_script(tmp_path, monkeypatch):
    batch = tmp_path / "batch"
    paper = tmp_path / "paper"
    batch.mkdir()
    paper.mkdir()
    monkeypatch.setenv("R1_BATCH_DIRECTORY", str(batch))
    monkeypatch.setenv("R1_PAPER_ROOT", str(paper))
    monkeypatch.setenv("AR_HARNESS_ROOT", str(HARNESS))
    sys.modules.pop(SCRIPT_MODULE, None)
    return importlib.import_module(SCRIPT_MODULE)


def test_script_stops_without_a_liveness_manifest(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    with pytest.raises(RuntimeError, match=r"^STOP: no D28 liveness manifest"):
        script.require_liveness(["digits_mlp"])


def test_script_reads_the_manifest_from_the_environment(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_manifest(("digits_mlp", {"pass": True, "failed_criteria": []}))))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(good))
    assert script.require_liveness(["digits_mlp"])["nodes"]["digits_mlp"]["pass"] is True

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_manifest(("digits_mlp", {"pass": False, "failed_criteria": ["metric_diff_fraction"]}))))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(bad))
    with pytest.raises(RuntimeError, match=r"^STOP: failed D28 liveness: digits_mlp"):
        script.require_liveness(["digits_mlp"])


def test_script_finds_the_newest_engineering_liveness_report(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    older = Path(script.PAPER) / "results/r1/engineering/liveness_scripted_20260101T000000Z"
    newer = Path(script.PAPER) / "results/r1/engineering/liveness_scripted_20260102T000000Z"
    for directory, passed in ((older, False), (newer, True)):
        directory.mkdir(parents=True)
        (directory / "liveness.json").write_text(
            json.dumps(_manifest(("digits_mlp", {"pass": passed, "failed_criteria": []})))
        )
    assert script.require_liveness(["digits_mlp"])["nodes"]["digits_mlp"]["pass"] is True


def test_collect_is_gated_before_any_collector_call(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    calls = []
    monkeypatch.setattr(script, "cmd", lambda *a, **k: calls.append(a))
    with pytest.raises(RuntimeError, match=r"^STOP:"):
        script.collect(tmp_path / "out", tmp_path / "work", ["--nodes", "digits_mlp"], ["digits_mlp"])
    assert calls == []  # the collector was never invoked
