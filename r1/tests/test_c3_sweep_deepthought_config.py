"""RUNBOOK A.6 and A.10: the deepthought and zhixu portal sweep configs on the llama.cpp backend,
and unresolved-value handling. No host access.

A.10 (25 Oct 2026, PLAN §10 R1-INFER-LLAMACPP): both configs use ``backend: llamacpp``; the
author's answers to batch A's open questions apply (watchdog on, restart limits 5 / 3,
min_live_nodes 8, Paper A check "not applicable" on these hosts).

A.6 completed on the host (26 Oct 2026, PLAN §10 R1-DT-PIN / R1-SCHEMA): the deepthought config is
no longer a draft - every host value is read on deepthought and ``proposal_schema`` is on - so it
must carry no placeholder and ``--check-config`` must pass on it. The zhixu portal config is still
a draft and keeps the placeholder behaviour.

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
PORTAL = REPO / "r1/scripts/configs/c3_sweep_portal.json"
HOST_VALUES = {"workers", "gpu_uuid", "llamacpp.binary", "llamacpp.model_path", "llamacpp.model_sha256",
               "llamacpp.build", "llamacpp.port", "llamacpp.footprint_mib", "allowed_hosts[0]"}


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


@pytest.mark.parametrize("path,host,open_values", [(DEEPTHOUGHT, "deepthought", set()),
                                                   (PORTAL, "zhixu portal", HOST_VALUES)])
def test_host_configs_keep_the_ada_design_on_llamacpp_and_mark_only_host_values(path, host, open_values):
    ada = sweep.load_config(ADA)
    draft = sweep.load_config(path, allow_placeholders=True)
    assert set(sweep.placeholders(draft)) == open_values
    for key in ("nodes", "nodes_pending", "instances", "runs", "memory_modes", "transport_max_attempts",
                "liveness", "max_parse_failure_rate", "max_collect_sessions", "audit"):
        assert draft[key] == ada[key], key
    assert draft["nodes"] == sweep.D21_NODES and len(draft["nodes"]) == 8
    assert ada["backend"] == "ollama" and draft["backend"] == "llamacpp"  # the Ada config stays historical
    # Author's answers to batch A (25 Oct): watchdog on, limits 5 / 3, min_live_nodes 8, Paper A n/a here.
    assert draft["resume"] == {"sweeps": True, "max_restarts": 5}
    assert draft["watchdog"]["enabled"] and draft["watchdog"]["max_restarts"] == 3
    assert draft["min_live_nodes"] == 8
    command = draft["paper_a_check"]["command"]
    assert command[:3] == ["python3", "r1/scripts/paper_a_status.py", "--not-applicable"]
    assert "zhixu experiment" in command[3] and host in command[3]
    spec = draft["llamacpp"]
    assert spec["model_alias"] == "r1-manager" and spec["n_gpu_layers"] == 999 and spec["extra_args"] == []
    assert host.split()[-1] in draft["comment"] and "llama.cpp" in draft["comment"]


def test_paper_a_not_applicable_command_clears_off_the_paper_a_host():
    command = sweep.load_config(DEEPTHOUGHT, allow_placeholders=True)["paper_a_check"]
    record = sweep.paper_a_check(command, "deepthought")  # runs the real command from the repo root
    assert record["verdict"] == "clear" and record["report"]["verdict"] == "not_applicable"
    on_ada = dict(command, command=[*command["command"], "--host", "ucrtasl"])
    with pytest.raises(sweep.Stop, match="Paper A"):
        sweep.paper_a_check(on_ada, "ucrtasl")


def test_check_config_cli_on_the_portal_draft():
    base = [sys.executable, str(REPO / "r1/scripts/c3_label_sweep.py"), "--config", str(PORTAL), "--check-config"]
    refused = subprocess.run(base, capture_output=True, text=True, cwd=REPO, timeout=60)
    assert refused.returncode == 2 and "unresolved TODO_VERIFY" in refused.stdout
    draft = subprocess.run([*base, "--allow-placeholders"], capture_output=True, text=True, cwd=REPO, timeout=60)
    assert draft.returncode == 0 and json.loads(draft.stdout)["nodes"][-1] == "openml_blood_transfusion"
    assert draft.stderr.startswith("UNRESOLVED (9): ")
    assert set(draft.stderr.split(": ", 1)[1].strip().split(", ")) == HOST_VALUES


def test_check_config_cli_passes_on_the_completed_deepthought_config():
    """A.6 completed on the host (26 Oct): no placeholder is left and the schema is on (R1-SCHEMA)."""
    base = [sys.executable, str(REPO / "r1/scripts/c3_label_sweep.py"), "--config", str(DEEPTHOUGHT),
            "--check-config"]
    done = subprocess.run(base, capture_output=True, text=True, cwd=REPO, timeout=60)
    assert done.returncode == 0, done.stdout[-2000:] + done.stderr[-2000:]
    config = json.loads(done.stdout)
    assert sweep.placeholders(config) == []
    assert config["backend"] == "llamacpp" and config["proposal_schema"] == "manager_proposal/v1"
    assert config["allowed_hosts"] == ["deepthought"]
    spec = config["llamacpp"]
    assert spec["binary"].startswith("/") and spec["model_path"].endswith(".gguf")
    assert sweep.lsi.VERSION_RE.fullmatch(spec["build"])
    assert len(spec["model_sha256"]) == 64 and spec["footprint_mib"] >= 1 and spec["port"] >= 1024
    assert spec["ctx_size"] == 8192 and spec["n_gpu_layers"] == 999
