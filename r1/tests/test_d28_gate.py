"""D28/P5: the require_live gate and its wiring into the batch runner.

The gate consumes only LLM-backed, memory-on liveness manifests; the D24
memory-off contrast arm is exempt from the memory-mode match and reuses the
memory-on verdict (PLAN §10 D28 revision, BUILD_BATCH4 P6).  AI-assisted
(BUILD_BATCH3 P5; exemption added in BUILD_BATCH4, P6); ENGINEERING_ONLY.
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
MEMORY_ON = "append_only_summary"


def _manifest(*verdicts, manager_kind="langgraph", memory_mode=MEMORY_ON):
    return {
        "manager_kind": manager_kind,
        "memory_mode": memory_mode,
        "nodes": {node: verdict for node, verdict in verdicts},
    }


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


def test_gate_rejects_a_scripted_manifest():
    manifest = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}), manager_kind="scripted")
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from an LLM-backed run"):
        require_live(["digits_mlp"], manifest)


def test_gate_rejects_a_memory_off_manifest():
    manifest = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}), memory_mode="none")
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from a memory-on run"):
        require_live(["digits_mlp"], manifest)


def test_contrast_exemption_reuses_the_memory_on_verdict():
    memory_on = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}))
    # Arm B: LLM, memory off, declared contrast.  Exempt from the memory-mode
    # match; eligibility still comes from the memory-on verdict.
    assert require_live(["digits_mlp"], memory_on, memory_mode="none", arm_role="contrast") is memory_on
    # A memory-on collection must match the manifest's mode.
    with pytest.raises(RuntimeError, match=r"^STOP: collection memory_mode=.* does not match"):
        require_live(["digits_mlp"], memory_on, memory_mode="append_only_summary_with_rationale",
                     arm_role="primary")
    # The exemption cannot admit a scripted or memory-off manifest.
    scripted = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}), manager_kind="scripted")
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from an LLM-backed run"):
        require_live(["digits_mlp"], scripted, memory_mode="none", arm_role="contrast")
    memory_off = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}), memory_mode="none")
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from a memory-on run"):
        require_live(["digits_mlp"], memory_off, memory_mode="none", arm_role="contrast")
    # A memory-off primary collection is not exempt.
    with pytest.raises(RuntimeError, match=r"^STOP: collection memory_mode=.* does not match"):
        require_live(["digits_mlp"], memory_on, memory_mode="none", arm_role="primary")


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


def _langgraph_manifest(*verdicts):
    return _manifest(*verdicts)


def test_script_reads_the_manifest_from_the_environment(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_langgraph_manifest(("digits_mlp", {"pass": True, "failed_criteria": []}))))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(good))
    assert script.require_liveness(["digits_mlp"])["nodes"]["digits_mlp"]["pass"] is True

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_langgraph_manifest(
        ("digits_mlp", {"pass": False, "failed_criteria": ["active_novelty_fraction"]})
    )))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(bad))
    with pytest.raises(RuntimeError, match=r"^STOP: failed D28 liveness: digits_mlp"):
        script.require_liveness(["digits_mlp"])


def test_script_rejects_a_scripted_liveness_manifest(tmp_path, monkeypatch):
    # Review F5: a scripted smoke pass is not the D28 LLM/memory-on check.
    script = _load_script(tmp_path, monkeypatch)
    scripted = tmp_path / "scripted.json"
    payload = _manifest(("digits_mlp", {"pass": True, "failed_criteria": []}), manager_kind="scripted")
    scripted.write_text(json.dumps(payload))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(scripted))
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from an LLM-backed run"):
        script.require_liveness(["digits_mlp"])

    missing_kind = tmp_path / "missing.json"
    missing_kind.write_text(json.dumps(_manifest(
        ("digits_mlp", {"pass": True, "failed_criteria": []}), manager_kind=None
    )))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(missing_kind))
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from an LLM-backed run"):
        script.require_liveness(["digits_mlp"])


def test_script_rejects_a_memory_off_liveness_manifest(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    memory_off = tmp_path / "memory_off.json"
    memory_off.write_text(json.dumps(_manifest(
        ("digits_mlp", {"pass": True, "failed_criteria": []}), memory_mode="none"
    )))
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(memory_off))
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from a memory-on run"):
        script.require_liveness(["digits_mlp"])


def test_script_finds_the_newest_engineering_liveness_report(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    older = Path(script.PAPER) / "results/r1/engineering/liveness_langgraph_20260101T000000Z"
    newer = Path(script.PAPER) / "results/r1/engineering/liveness_langgraph_20260102T000000Z"
    for directory, passed in ((older, False), (newer, True)):
        directory.mkdir(parents=True)
        (directory / "liveness.json").write_text(json.dumps(_langgraph_manifest(
            ("digits_mlp", {"pass": passed, "failed_criteria": []})
        )))
    assert script.require_liveness(["digits_mlp"])["nodes"]["digits_mlp"]["pass"] is True


def test_script_orders_manifests_by_date_not_by_manager_prefix(tmp_path, monkeypatch):
    # Review F11: paths sort langgraph < llm < scripted regardless of date, so
    # a lexicographic pick would use the older llm manifest and miss the newer
    # failing langgraph one.
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    older = Path(script.PAPER) / "results/r1/engineering/liveness_llm_20260101T000000Z"
    newer = Path(script.PAPER) / "results/r1/engineering/liveness_langgraph_20260201T000000Z"
    for directory, passed in ((older, True), (newer, False)):
        directory.mkdir(parents=True)
        (directory / "liveness.json").write_text(json.dumps(_langgraph_manifest(
            ("digits_mlp", {"pass": passed, "failed_criteria": [] if passed else ["active_novelty_fraction"]})
        )))
    with pytest.raises(RuntimeError, match=r"^STOP: failed D28 liveness: digits_mlp"):
        script.require_liveness(["digits_mlp"])


def test_collect_is_gated_before_any_collector_call(tmp_path, monkeypatch):
    script = _load_script(tmp_path, monkeypatch)
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    calls = []
    monkeypatch.setattr(script, "cmd", lambda *a, **k: calls.append(a))
    with pytest.raises(RuntimeError, match=r"^STOP:"):
        script.collect(tmp_path / "out", tmp_path / "work", ["--nodes", "digits_mlp"], ["digits_mlp"])
    assert calls == []  # the collector was never invoked
