"""P7: E1b rerun-2 entrypoint tests (stubs; no LLM, no GPU, no Ada).

Phase checkpoints, the liveness eligibility filter, the arm gating and
metadata, the launcher refusals, and the end-to-end commit with the runner's
own whitespace check (the DT4 lesson: every path that commits generated files
is tested in a temporary git repository).  AI-assisted (BUILD_BATCH4, P7).
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from r1.harness import harness_root
from r1.headroom.e1b_analyze import markdown as analyze_markdown
from r1.headroom.e1b_compare import compare, markdown as compare_markdown
from r1.liveness import evaluate_ledger_paths, write_reports

REPO = Path(__file__).resolve().parents[2]
SCRIPT_MODULE = "r1.scripts.ada_e1b_rerun2"
HARNESS = harness_root()
DT4 = REPO / "results/r1/pilot/E1b_20261013T151857Z"
SCRIPTED = REPO / "results/r1/pilot/E1b_20261012T161034Z"
SMOKE_LEDGERS = REPO / "results/r1/engineering/liveness_scripted_20261014T075806Z/ledgers"
LAUNCHER = REPO / "r1/scripts/ada_e1b_rerun2_launch.sh"


def _load_runner(tmp_path: Path, monkeypatch):
    batch = tmp_path / "batch"
    paper = tmp_path / "paper"
    harness = tmp_path / "harness"
    for directory in (batch, paper, harness):
        directory.mkdir(parents=True, exist_ok=True)
    (harness / ".venv/bin").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("R1_BATCH_DIRECTORY", str(batch))
    monkeypatch.setenv("R1_PAPER_ROOT", str(paper))
    monkeypatch.setenv("AR_HARNESS_ROOT", str(harness))
    monkeypatch.setenv("R1_OLLAMA_MODELS", str(tmp_path / "models"))
    monkeypatch.setenv("R1_OLLAMA_BINARY", "/bin/echo")
    monkeypatch.delenv("R1_LIVENESS_MANIFEST", raising=False)
    with mock.patch("platform.node", return_value="ucrtasl"):
        sys.modules.pop(SCRIPT_MODULE, None)
        module = importlib.import_module(SCRIPT_MODULE)
    return module


# ---------------------------------------------------------------------------
# Phase checkpoints
# ---------------------------------------------------------------------------

def test_completed_phases_are_skipped_and_order_is_fixed(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    order = []
    runner.state["steps"] = {}
    runner.phase("preconditions", lambda: order.append("preconditions"))
    runner.phase("liveness", lambda: order.append("liveness"))
    runner.phase("preconditions", lambda: order.append("again"))  # completed: skipped
    assert order == ["preconditions", "liveness"]
    assert runner.state["steps"]["preconditions"]["completed"] is True
    assert runner.state["steps"]["liveness"]["completed"] is True


def test_restart_loads_checkpoints_from_disk_and_stops_on_an_interrupted_phase(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    batch = Path(runner.BATCH)
    (batch / "batch_state.json").write_text(json.dumps({
        "gpu": "0, GPU-x, A100, 40000",
        "steps": {"preconditions": {"completed": True, "started_utc": "t0"}},
    }))
    runner.load_previous_state()
    assert runner.state["gpu"] == "0, GPU-x, A100, 40000"
    calls = []
    runner.phase("preconditions", lambda: calls.append("preconditions"))
    assert calls == []  # never redone

    runner.state["steps"]["arm_A"] = {"completed": False, "started_utc": "t1"}
    with pytest.raises(runner.PhaseInterrupted, match="arm_A"):
        runner.phase("arm_A", lambda: calls.append("arm_A"))
    assert calls == []  # an interrupted phase is never retried


def test_entrypoint_maps_an_interrupted_phase_to_a_stop(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    reasons = []

    def _main():
        raise runner.PhaseInterrupted("phase arm_B was interrupted at t9")

    monkeypatch.setattr(runner, "main", _main)
    monkeypatch.setattr(runner, "finish", lambda reason: reasons.append(reason))
    runner._entrypoint()
    assert reasons and reasons[0].startswith("STOP: phase arm_B was interrupted")
    assert "no automatic retry" in reasons[0]


# ---------------------------------------------------------------------------
# Liveness phase: eligibility and the floor
# ---------------------------------------------------------------------------

def _stub_liveness(monkeypatch, runner, verdicts):
    def _cmd(argv, **kwargs):
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True, exist_ok=True)
        payload = {
            "manager_kind": "langgraph", "memory_mode": "append_only_summary",
            "nodes": {node: {"pass": passed, "criteria": {},
                             "failed_criteria": [] if passed else ["active_novelty_fraction"]}
                      for node, passed in verdicts.items()},
        }
        (out / "liveness.json").write_text(json.dumps(payload))

    monkeypatch.setattr(runner, "cmd", _cmd)
    monkeypatch.setattr(runner, "commit", lambda *a, **k: None)


def test_liveness_eligible_filter_and_exclusions(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    runner.state["steps"] = {"liveness": {"completed": False, "started_utc": "t"}}
    _stub_liveness(monkeypatch, runner, {"digits_mlp": True, "tabular_mlp": True,
                                         "openml_ionosphere": False, "openml_breast_w": True})
    runner.liveness_phase()
    entry = runner.state["steps"]["liveness"]
    assert entry["eligible_nodes"] == ["digits_mlp", "tabular_mlp", "openml_breast_w"]
    assert entry["excluded_nodes"] == ["openml_ionosphere"]
    assert "liveness_llm_" in entry["out"]
    assert set(entry["verdicts"]) == {"digits_mlp", "tabular_mlp", "openml_ionosphere", "openml_breast_w"}


def test_liveness_stops_below_two_eligible_nodes(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    runner.state["steps"] = {"liveness": {"completed": False, "started_utc": "t"}}
    _stub_liveness(monkeypatch, runner, {"digits_mlp": True, "tabular_mlp": False,
                                         "openml_ionosphere": False, "openml_breast_w": False})
    with pytest.raises(RuntimeError, match=r"^STOP: only 1 nodes passed D28 liveness"):
        runner.liveness_phase()
    assert runner.state["steps"]["liveness"]["eligible_nodes"] == ["digits_mlp"]


def test_preconditions_check_the_plan_rows_and_checkouts(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    (Path(runner.PAPER) / "docs/r1").mkdir(parents=True)
    (Path(runner.PAPER) / "docs/r1/PLAN.md").write_text("nothing here\n")
    with pytest.raises(RuntimeError, match=r"^STOP: PLAN §10 lacks the author row"):
        runner.preconditions()


# ---------------------------------------------------------------------------
# Arms: gating, exemption, metadata
# ---------------------------------------------------------------------------

def test_arm_a_collect_is_gated_before_any_collector_call(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(runner, "cmd", lambda *a, **k: calls.append(a))
    with pytest.raises(RuntimeError, match=r"^STOP:"):
        runner.collect(tmp_path / "out", tmp_path / "work", ["--nodes", "digits_mlp"], ["digits_mlp"],
                       manager="langgraph", memory_mode="append_only_summary", arm_role="primary")
    assert calls == []


def _write_liveness_manifest(path: Path, manager_kind: str, memory_mode: str, passed: bool = True):
    path.write_text(json.dumps({
        "manager_kind": manager_kind,
        "memory_mode": memory_mode,
        "nodes": {"digits_mlp": {"pass": passed, "failed_criteria": [] if passed else ["active_novelty_fraction"]}},
    }))


def test_arm_b_exemption_and_arm_a_mode_match(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    manifest = tmp_path / "liveness.json"
    _write_liveness_manifest(manifest, "langgraph", "append_only_summary")
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(manifest))
    # Arm A: gated, memory mode matches the memory-on manifest.
    runner.require_liveness(["digits_mlp"], memory_mode="append_only_summary", arm_role="primary")
    # Arm B: memory-off contrast, exempt from the mode match, same verdict.
    runner.require_liveness(["digits_mlp"], memory_mode="none", arm_role="contrast")
    # The exemption cannot bypass the gate with a scripted or memory-off manifest.
    scripted = tmp_path / "scripted.json"
    _write_liveness_manifest(scripted, "scripted", "none")
    monkeypatch.setenv("R1_LIVENESS_MANIFEST", str(scripted))
    with pytest.raises(RuntimeError, match=r"^STOP: liveness manifest is not from an LLM-backed run"):
        runner.require_liveness(["digits_mlp"], memory_mode="none", arm_role="contrast")


def test_arm_passes_eligible_nodes_and_manifest_metadata(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    runner.state["steps"] = {
        "liveness": {"completed": True, "out": str(tmp_path / "liveness"), "eligible_nodes": ["digits_mlp", "tabular_mlp"]},
    }
    recorded = {}

    def _collect(out, work, extra, nodes, **kwargs):
        recorded.update({"out": out, "extra": extra, "nodes": nodes, **kwargs})
        return {"leaves": 1}

    monkeypatch.setattr(runner, "collect", _collect)
    monkeypatch.setattr(runner, "cmd", lambda *a, **k: None)
    monkeypatch.setattr(runner, "commit", lambda *a, **k: None)
    monkeypatch.setattr(runner, "regeneration_check", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_after_collection", lambda *a, **k: None)
    for label, (memory_mode, arm_role, manager) in runner.ARMS.items():
        runner.state["steps"][f"arm_{label}"] = {"completed": False, "started_utc": "t"}
        recorded.clear()
        runner.arm(label)
        assert recorded["nodes"] == ["digits_mlp", "tabular_mlp"]
        assert recorded["memory_mode"] == memory_mode
        assert recorded["arm_role"] == arm_role
        assert recorded["manager"] == manager
        extra = recorded["extra"]
        assert "--arm" in extra and label in extra
        assert "--arm-role" in extra and arm_role in extra
        # the eligible-node filter reaches the collector argv
        nodes_at = extra.index("--nodes")
        assert extra[nodes_at + 1: nodes_at + 3] == ["digits_mlp", "tabular_mlp"]
        assert "openml_ionosphere" not in extra


def test_collector_manifest_carries_arm_role_and_memory_mode(tmp_path):
    # A real, tiny scripted collection: the manifest fields the harness reads.
    out = tmp_path / "out"
    work = tmp_path / "work"
    command = [sys.executable, "-m", "r1.headroom.e1b_collect",
               "--nodes", "digits_mlp", "--instances", "1", "--runs", "2", "--points", "2",
               "--reps", "1", "--audit-seeds", "1", "--workers", "1", "--manager", "scripted",
               "--memory-mode", "none", "--arm", "C", "--arm-role", "reference",
               "--label", "ENGINEERING_ONLY", "--split", "engineering",
               "--out", str(out), "--work", str(work)]
    environment = dict(os.environ, AR_HARNESS_ROOT=str(HARNESS))
    subprocess.run(command, cwd=REPO, env=environment, check=True, capture_output=True)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["arm"] == "C"
    assert manifest["arm_role"] == "reference"
    assert manifest["memory_mode"] == "none"
    assert (work / "roots/digits_mlp__s104/root_events.jsonl").exists()


# ---------------------------------------------------------------------------
# Launcher refusals (shell, stubbed tmux/hostname)
# ---------------------------------------------------------------------------

def _launcher_env(tmp_path: Path, *, hostname="ucrtasl", has_session=False, ls_output="") -> dict:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "hostname").write_text(f"#!/bin/sh\necho {hostname}\n")
    (bin_dir / "tmux").write_text(
        "#!/bin/sh\n"
        'echo "$@" >> "$STUB_TMUX_LOG"\n'
        'if [ "$1" = "has-session" ]; then exit "${STUB_TMUX_HAS_SESSION:-1}"; fi\n'
        'if [ "$1" = "ls" ]; then cat "${STUB_TMUX_LS:-/dev/null}"; fi\n'
        "exit 0\n"
    )
    for name in ("hostname", "tmux"):
        (bin_dir / name).chmod(0o755)
    log = tmp_path / "tmux.log"
    log.write_text("")
    return dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                STUB_TMUX_LOG=str(log), STUB_TMUX_HAS_SESSION="0" if has_session else "1",
                STUB_TMUX_LS=ls_output)


def _run_launcher(args, env):
    return subprocess.run(["bash", str(LAUNCHER), *args], env=env, capture_output=True, text=True)


def test_launcher_is_ada_only(tmp_path):
    env = _launcher_env(tmp_path, hostname="my-mac")
    result = _run_launcher(["--prepare"], env)
    assert result.returncode == 1
    assert "STOP: run this on Ada" in result.stdout


def test_launcher_refuses_an_existing_session(tmp_path):
    env = _launcher_env(tmp_path, has_session=True)
    result = _run_launcher(["--prepare"], env)
    assert result.returncode == 1
    assert "STOP: tmux session r1_e1b_rerun2 already exists" in result.stdout


def test_launcher_refuses_an_existing_ollama_session(tmp_path):
    ls_file = tmp_path / "tmux_ls.txt"
    ls_file.write_text("r1_ollama_dt4: 1 windows (created today)\n")
    env = _launcher_env(tmp_path, ls_output=str(ls_file))
    result = _run_launcher(["--prepare"], env)
    assert result.returncode == 1
    assert "STOP: one of our r1_ollama_* sessions already exists" in result.stdout


def _prepare_batch(tmp_path: Path, *, ok=True, unexpected=None) -> Path:
    batch = tmp_path / "batch"
    (batch / "autoresearch_harness/.venv/bin").mkdir(parents=True)
    fake_python = batch / "autoresearch_harness/.venv/bin/python"
    fake_python.write_text("#!/bin/sh\nexit 0\n")
    fake_python.chmod(0o755)
    (batch / "env.sh").write_text("export R1_BATCH_DIRECTORY=%s\n" % batch)
    (batch / "prepare.json").write_text(json.dumps({
        "ok": ok,
        "harness_tests": {"unexpected": unexpected or []},
    }))
    return batch


def test_launcher_start_requires_prepare_json(tmp_path):
    env = _launcher_env(tmp_path)
    result = _run_launcher(["--start", str(tmp_path / "missing")], env)
    assert result.returncode == 1
    assert "STOP:" in result.stdout


def test_launcher_start_refuses_unaccepted_failures(tmp_path):
    env = _launcher_env(tmp_path)
    batch = _prepare_batch(tmp_path, ok=False, unexpected=["tests/test_new_thing.py::test_x"])
    result = _run_launcher(["--start", str(batch)], env)
    assert result.returncode == 1
    assert "outside the accepted environmental set" in result.stdout
    assert "tests/test_new_thing.py::test_x" in result.stdout
    # nothing started
    assert "new-session" not in (tmp_path / "tmux.log").read_text()


def test_launcher_start_starts_the_session_when_clean(tmp_path):
    env = _launcher_env(tmp_path)
    batch = _prepare_batch(tmp_path)
    result = _run_launcher(["--start", str(batch)], env)
    assert result.returncode == 0, result.stdout + result.stderr
    log = (tmp_path / "tmux.log").read_text()
    assert "new-session -d -s r1_e1b_rerun2" in log
    assert "ada_e1b_rerun2.py" in log


# ---------------------------------------------------------------------------
# End-to-end commit: every generated Markdown/JSON through the runner's check
# ---------------------------------------------------------------------------

def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_commit_passes_the_whitespace_check_end_to_end(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    _git(["init", "-b", "main"], work)
    _git(["config", "user.email", "t@example.com"], work)
    _git(["config", "user.name", "T"], work)
    (work / "README.md").write_text("x\n")
    _git(["add", "README.md"], work)
    _git(["commit", "-m", "init"], work)
    _git(["remote", "add", "origin", str(origin)], work)
    _git(["push", "-u", "origin", "main"], work)

    # Generate every kind of artifact the runner commits, from the fixtures.
    reports = work / "docs/r1/reports"
    reports.mkdir(parents=True)
    arm_out = work / "results/r1/pilot/E1b_rerun2_B_fixture"
    (arm_out / "provenance/ledgers/roots/digits_mlp__s104").mkdir(parents=True)
    shutil.copy2(DT4 / "analysis.json", arm_out / "analysis.json")
    shutil.copy2(DT4 / "collection_checks.json", arm_out / "collection_checks.json")
    (arm_out / "provenance/ledgers/roots/digits_mlp__s104/root_trials.jsonl").write_text(
        (DT4 / "provenance/ledgers/roots/digits_mlp__s104/root_trials.jsonl").read_text()
    )
    analysis = json.loads((DT4 / "analysis.json").read_text())
    tables = reports / "HEADROOM_RERUN2_B_fixture_tables.md"
    tables.write_text(analyze_markdown(analysis) + "\n")
    comparison = compare([("A", SCRIPTED), ("B", DT4), ("C", SCRIPTED)], n_boot=50)
    compare_md = reports / "HEADROOM_RERUN2_fixture_comparison.md"
    compare_md.write_text(compare_markdown(comparison) + "\n")
    compare_json = reports / "HEADROOM_RERUN2_fixture_comparison.json"
    compare_json.write_text(json.dumps(comparison, indent=1, default=str) + "\n")
    liveness_out = work / "results/r1/engineering/liveness_llm_fixture"
    write_reports(evaluate_ledger_paths([SMOKE_LEDGERS], manager_kind="scripted", memory_mode="none"),
                  liveness_out)
    status = work / "docs/r1/STATUS.md"
    status.write_text("# Status\n\n## 14 October 2026 — R1-E1B-RERUN2 (PILOT): completed\n\n- entry\n")

    runner.state["steps"]["e2e_arm"] = {"completed": False}
    runner.commit(work, "e2e arm artifacts", [arm_out, tables, compare_md, compare_json, liveness_out],
                  "e2e_arm")
    assert runner.state["steps"]["e2e_arm"]["commit"]

    runner.state["steps"]["e2e_status"] = {"completed": False}
    runner.commit(work, "e2e status", [status], "e2e_status")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work, text=True).strip()
    remote = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     cwd=origin, text=True).strip()
    assert head == remote  # pushed
    committed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only",
                                         "-r", "HEAD", "--", "."], cwd=work, text=True)
    assert "docs/r1/STATUS.md" in committed

    # Non-vacuous: a blank line at EOF in a checked path makes the runner's
    # own whitespace check fail before any commit happens.
    bad = reports / "BAD_trailing_blank.md"
    bad.write_text("line\n\n")
    runner.state["steps"]["e2e_bad"] = {"completed": False}
    head_before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work, text=True).strip()
    with pytest.raises(subprocess.CalledProcessError):
        runner.commit(work, "must fail", [bad], "e2e_bad")
    head_after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work, text=True).strip()
    assert head_before == head_after  # nothing was committed
