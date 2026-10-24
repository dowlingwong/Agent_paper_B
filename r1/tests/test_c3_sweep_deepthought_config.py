"""RUNBOOK A.6 (draft): the deepthought sweep config and unresolved-value handling. No host access.

AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from r1.scripts import c3_label_sweep as sweep

REPO = Path(__file__).resolve().parents[2]
ADA = REPO / "r1/scripts/configs/c3_sweep_ada.json"
DEEPTHOUGHT = REPO / "r1/scripts/configs/c3_sweep_deepthought.json"
HOST_VALUES = {"workers", "paper_a_check.command", "gpu_uuid", "ollama.binary", "ollama.seed_models_from",
               "ollama.port", "allowed_hosts[0]"}


@pytest.fixture(autouse=True)
def _no_dryrun(monkeypatch):
    monkeypatch.delenv("R1_DRYRUN", raising=False)


def test_placeholders_are_refused_unless_explicitly_allowed(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"comment": "TODO_VERIFY in free text is fine",
                                "ollama": {"port": "TODO_VERIFY_ON_DEEPTHOUGHT"},
                                "allowed_hosts": ["TODO_VERIFY_ON_DEEPTHOUGHT"]}))
    with pytest.raises(sweep.Stop, match=r"ollama\.port.*allowed_hosts\[0\]"):
        sweep.load_config(path)  # a launch builds its config this way
    config = sweep.load_config(path, allow_placeholders=True)
    assert sweep.placeholders(config) == ["ollama.port", "allowed_hosts[0]"]
    assert sweep.placeholders(sweep.load_config(ADA)) == []


def test_deepthought_draft_keeps_the_ada_design_and_marks_only_host_values():
    ada = sweep.load_config(ADA)
    draft = sweep.load_config(DEEPTHOUGHT, allow_placeholders=True)
    assert set(sweep.placeholders(draft)) == HOST_VALUES
    for key in ("nodes", "nodes_pending", "instances", "runs", "memory_modes", "transport_max_attempts",
                "liveness", "min_live_nodes", "max_parse_failure_rate", "max_collect_sessions", "audit"):
        assert draft[key] == ada[key], key
    assert draft["nodes"] == sweep.D21_NODES and len(draft["nodes"]) == 8
    assert draft["resume"]["sweeps"] and draft["watchdog"]["enabled"]
    assert draft["ollama"]["start_timeout"] == ada["ollama"]["start_timeout"]
    assert "deepthought" in draft["comment"] and "TITAN" in draft["comment"]


def test_check_config_cli_on_the_draft():
    base = [sys.executable, str(REPO / "r1/scripts/c3_label_sweep.py"), "--config", str(DEEPTHOUGHT), "--check-config"]
    refused = subprocess.run(base, capture_output=True, text=True, cwd=REPO, timeout=60)
    assert refused.returncode == 2 and "unresolved TODO_VERIFY" in refused.stdout
    draft = subprocess.run([*base, "--allow-placeholders"], capture_output=True, text=True, cwd=REPO, timeout=60)
    assert draft.returncode == 0 and json.loads(draft.stdout)["nodes"][-1] == "openml_blood_transfusion"
    assert draft.stderr.startswith("UNRESOLVED (7): ")
    assert set(draft.stderr.split(": ", 1)[1].strip().split(", ")) == HOST_VALUES
