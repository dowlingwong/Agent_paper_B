"""C3 label sweep runner: config, Paper A coordination, gates, phases (no GPU, no LLM).

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


@pytest.fixture(autouse=True)
def _no_dryrun(monkeypatch):
    monkeypatch.delenv("R1_DRYRUN", raising=False)


def _cmd(payload, rc=0):
    code = f"import sys; print('noise'); print({payload!r}); sys.exit({rc})"
    return [sys.executable, "-c", code]


def test_config_defaults_follow_plan(tmp_path):
    config = sweep.load_config(None)
    assert config["nodes"] == ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
                              "openml_credit_approval", "openml_sonar", "openml_blood_transfusion"]  # D21 pool after the 22 Oct common run
    assert config["instances"] == 18 and config["runs"] == 20
    assert config["memory_modes"] == ["append_only_summary", "none"]
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"instances": 6, "nodes": ["digits_mlp"], "ollama": {"port": 12345}}))
    custom = sweep.load_config(path)
    assert custom["instances"] == 6 and custom["ollama"]["port"] == 12345
    assert custom["ollama"]["binary"] == "/usr/local/bin/ollama"  # nested defaults kept
    for bad in ({"bogus": 1}, {"runs": 10}, {"memory_modes": ["append_only_summary_with_rationale"]}):
        path.write_text(json.dumps(bad))
        with pytest.raises(sweep.Stop):
            sweep.load_config(path)


def test_paper_a_check_clear_and_refusals():
    clear = sweep.paper_a_check({"command": _cmd('{"paper_a_live_waiting_for_card": false}')}, "host")
    assert clear["verdict"] == "clear"
    refusals = [
        {"command": None},
        {"command": _cmd('{"paper_a_live_waiting_for_card": true}')},
        {"command": _cmd('{"status": "computing"}')},
        {"command": _cmd("not json")},
        {"command": _cmd('{"paper_a_live_waiting_for_card": false}', rc=1)},
        {"command": ["/nonexistent/check"]},
    ]
    for spec in refusals:
        with pytest.raises(sweep.Stop) as info:
            sweep.paper_a_check(spec, "host")
        assert info.value.args[1]["verdict"].startswith("refused")


def test_gpu_helpers_are_reused_from_the_shared_script(tmp_path):
    runner = sweep.SweepRunner(sweep.load_config(None), batch=tmp_path, paper=REPO, harness=tmp_path, python="py")
    for name in sweep.GPU_HELPERS | sweep.GPU_CONSTANTS:
        assert name in runner.gpu
    assert runner.gpu["state"] is runner.state


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo_pair(tmp_path):
    paper = tmp_path / "paper"
    (paper / "docs/r1").mkdir(parents=True)
    (paper / "r1/scripts").mkdir(parents=True)
    (paper / "docs/r1/PLAN.md").write_text("\n".join(sweep.ROWS) + "\n")
    harness = tmp_path / "harness"
    harness.mkdir()
    for repo in (paper, harness):
        _git("init", "-q", "-b", "main", cwd=repo)
        _git("config", "user.name", "t", cwd=repo)
        _git("config", "user.email", "t@e", cwd=repo)
    (harness / "x").write_text("x")
    _git("add", ".", cwd=harness)
    _git("commit", "-qm", "h", cwd=harness)
    pin = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=harness, text=True).strip()
    (paper / "r1/scripts/HARNESS_PIN_C3").write_text(pin + "\n")
    _git("add", ".", cwd=paper)
    _git("commit", "-qm", "p", cwd=paper)
    bare = tmp_path / "paper.git"
    _git("clone", "-q", "--bare", str(paper), str(bare), cwd=tmp_path)
    _git("remote", "add", "origin", str(bare), cwd=paper)
    return paper, harness


def test_launch_refuses_before_any_gpu_or_ollama_when_paper_a_waits(tmp_path, monkeypatch):
    paper, harness = _repo_pair(tmp_path)
    batch = tmp_path / "batch"
    batch.mkdir()
    config = sweep.load_config(None)
    config["paper_a_check"] = {"command": _cmd('{"paper_a_live_waiting_for_card": true}')}
    runner = sweep.SweepRunner(config, batch=batch, paper=paper, harness=harness, python="py")
    touched = []
    runner.gpu["gpu_rows"] = lambda: touched.append("gpu") or ([], [])
    with pytest.raises(sweep.Stop, match="Paper A"):
        runner.phase("preconditions", runner.preconditions)
    assert touched == [] and runner.ollama is None
    state = json.loads((batch / "batch_state.json").read_text())
    assert state["paper_a_check"]["verdict"].startswith("refused")
    # the interrupted phase is never retried automatically
    with pytest.raises(sweep.PhaseInterrupted):
        runner.phase("preconditions", runner.preconditions)


def test_preconditions_refuse_a_harness_off_the_pin(tmp_path):
    paper, harness = _repo_pair(tmp_path)
    (paper / "r1/scripts/HARNESS_PIN_C3").write_text("0" * 40 + "\n")
    _git("commit", "-qam", "bad pin", cwd=paper)
    _git("push", "-q", "origin", "HEAD:refs/heads/main", cwd=paper)
    runner = sweep.SweepRunner(sweep.load_config(None), batch=tmp_path, paper=paper, harness=harness, python="py")
    runner.state["steps"]["preconditions"] = {}
    with pytest.raises(sweep.Stop, match="HARNESS_PIN_C3"):
        runner.preconditions()


def _fake_sweep(tmp_path, *, roots=2, failures=0, parse_fail=False):
    out, work = tmp_path / "out", tmp_path / "work"
    (out / "roots").mkdir(parents=True)
    manifest = {"label": "PILOT", "manager": {"kind": "langgraph", "transport_max_attempts": 3},
                "verify_split_policy": "vary", "action_versions": {"verify_split_policy": "vary"}}
    (out / "manifest.json").write_text(json.dumps(manifest))
    for i in range(roots):
        inst = f"digits_mlp__s{i}"
        (out / "roots" / f"{inst}.json").write_text("{}")
        d = work / "roots" / inst
        d.mkdir(parents=True)
        events = [{"event_type": "llm_call", "trial_id": "t1",
                   "payload": {"parse_ok": not parse_fail, "transport_attempts": [
                       {"attempt": 1, "error_class": "server_disconnected"}, {"attempt": 2, "error_class": None}]}}]
        (d / "root_events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
        (d / "root_trials.jsonl").write_text(json.dumps({"proposal_summary": "reduce-lr to 2e-4 please"}) + "\n")
    for i in range(failures):
        (out / "failures").mkdir(exist_ok=True)
        (out / "failures" / f"root__digits_mlp__s{roots + i}.json").write_text(json.dumps(
            {"error_class": "ollama._types.ResponseError", "failed_utc": "2026-10-19T00:00:00.000000Z",
             "traceback": "Traceback ..."}))
    return out, work


def test_gates_pass_and_record_retries(tmp_path):
    config = sweep.load_config(None)
    config["instances"] = 2
    runner = sweep.SweepRunner(config, batch=tmp_path, paper=REPO, harness=tmp_path, python="py")
    out, work = _fake_sweep(tmp_path)
    checks = runner.collection_gates(out, work, ["digits_mlp"], "append_only_summary")
    assert checks["roots"] == 2 and checks["llm_calls"] == 2 and checks["llm_calls_retried"] == 2
    written = json.loads((out / "collection_checks.json").read_text())
    assert written["retried_calls"][0]["attempts"][0]["error_class"] == "server_disconnected"


def test_root_failures_are_written_before_the_gate_raises(tmp_path):
    config = sweep.load_config(None)
    config["instances"] = 3
    runner = sweep.SweepRunner(config, batch=tmp_path, paper=REPO, harness=tmp_path, python="py")
    out, work = _fake_sweep(tmp_path, roots=2, failures=1)
    with pytest.raises(sweep.Stop, match="1 root campaign failures"):
        runner.collection_gates(out, work, ["digits_mlp"], "none")
    assert json.loads((out / "collection_checks.json").read_text())["root_failures"] == 1
    failures = json.loads((out / "collection_failures.json").read_text())
    assert failures["failures"][0]["traceback"] and failures["failures"][0]["failed_utc"]


def test_parse_failure_rate_gate(tmp_path):
    config = sweep.load_config(None)
    config["instances"] = 2
    runner = sweep.SweepRunner(config, batch=tmp_path, paper=REPO, harness=tmp_path, python="py")
    out, work = _fake_sweep(tmp_path, parse_fail=True)
    with pytest.raises(sweep.Stop, match="parse failures"):
        runner.collection_gates(out, work, ["digits_mlp"], "none")
    assert (out / "parse_failure_examples.json").exists()


def test_launcher_refuses_without_identity_and_on_unclean_prepare(tmp_path):
    launcher = REPO / "r1/scripts/c3_label_sweep_launch.sh"
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run(["bash", str(launcher), "--prepare"], env=env, capture_output=True, text=True)
    assert done.returncode != 0 and "R1_GIT_NAME" in done.stdout
    batch = tmp_path / "b"
    batch.mkdir()
    (batch / "env.sh").write_text("")
    (batch / "prepare.json").write_text(json.dumps({"ok": False, "unexpected": ["tests/x::y"]}))
    done = subprocess.run(["bash", str(launcher), "--start", str(batch)], env=env, capture_output=True, text=True)
    assert done.returncode != 0 and "not clean" in done.stdout + done.stderr


def test_prepare_check_accepts_only_the_environmental_set(tmp_path):
    (tmp_path / "harness_tests.log").write_text(
        "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance\n1 failed, 5 passed\n")
    (tmp_path / "paper_tests.log").write_text("5 passed\n")
    script = REPO / "r1/scripts/c3_prepare_check.py"
    subprocess.run([sys.executable, str(script), str(tmp_path), "1", "0", "p", "h", "0"], check=True,
                   capture_output=True)
    assert json.loads((tmp_path / "prepare.json").read_text())["ok"] is True
    (tmp_path / "harness_tests.log").write_text("FAILED tests/stage2/test_new.py::t\n1 failed\n")
    subprocess.run([sys.executable, str(script), str(tmp_path), "1", "0", "p", "h", "0"], check=True,
                   capture_output=True)
    assert json.loads((tmp_path / "prepare.json").read_text())["ok"] is False


# --- 22 Oct: Ada sweep config, audit K = 10, pending-node slot ------------------------------------

ADA_CONFIG = REPO / "r1/scripts/configs/c3_sweep_ada.json"


def test_ada_sweep_config_validates_and_follows_plan():
    config = sweep.load_config(ADA_CONFIG)
    assert config["nodes"] == ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
                              "openml_credit_approval", "openml_sonar", "openml_blood_transfusion"]  # D21 pool after the 22 Oct common run
    assert config["nodes_pending"] == []  # 22 Oct: candidates decided by the common 30-seed run
    assert config["instances"] == 18 and config["runs"] == 20
    assert config["memory_modes"] == ["append_only_summary", "none"]
    assert config["liveness"] == {"instances": 2, "runs": 10, "memory_mode": "append_only_summary"}
    assert config["audit"] == {"seeds": list(range(7001, 7011)), "label_seeds": 5, "evaluation_seeds": 5}
    assert config["allowed_hosts"] == ["ucrtasl"] and config["transport_max_attempts"] == 3
    ollama = config["ollama"]
    assert ollama["port"] and ollama["port"] != 11434 and ollama["seed_models_from"]
    command = config["paper_a_check"]["command"]
    assert (REPO / command[1]).exists() and (REPO / command[command.index("--config") + 1]).exists()
    assert sweep.MODEL == "qwen2.5-coder:7b" and len(sweep.DIGEST) == 64  # digest pin stays in the runner


def test_audit_and_pending_validation(tmp_path):
    path = tmp_path / "c.json"
    for bad in ({"audit": {"seeds": [7001, 7002, 7003], "label_seeds": 1, "evaluation_seeds": 2}},
                {"audit": {"seeds": [7001, 7001], "label_seeds": 1, "evaluation_seeds": 1}},
                {"audit": {"seeds": list(range(7001, 7011)), "label_seeds": 4, "evaluation_seeds": 6}},
                {"nodes": ["digits_mlp"], "nodes_pending": ["digits_mlp"]},
                {"nodes": ["digits_mlp", "digits_mlp"]}):
        path.write_text(json.dumps(bad))
        with pytest.raises(sweep.Stop):
            sweep.load_config(path)
    path.write_text(json.dumps({"audit": {"seeds": list(range(7001, 7007)), "label_seeds": 3,
                                          "evaluation_seeds": 3}}))
    assert sweep.load_config(path)["audit"]["seeds"] == list(range(7001, 7007))  # K = 6 still allowed
    assert sweep.load_config(None)["audit"]["seeds"] == list(range(7001, 7011))  # default K = 10


def test_check_config_cli(tmp_path):
    ok = subprocess.run([sys.executable, str(REPO / "r1/scripts/c3_label_sweep.py"), "--config", str(ADA_CONFIG),
                         "--check-config"], capture_output=True, text=True, cwd=REPO, timeout=60)
    assert ok.returncode == 0 and json.loads(ok.stdout)["nodes"][-1] == "openml_blood_transfusion"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"runs": 10}))
    no = subprocess.run([sys.executable, str(REPO / "r1/scripts/c3_label_sweep.py"), "--config", str(bad),
                         "--check-config"], capture_output=True, text=True, cwd=REPO, timeout=60)
    assert no.returncode == 2 and "STOP" in no.stdout


def test_dryrun_overrides_only_desktop_keys(tmp_path):
    sys.path.insert(0, str(REPO / "r1/scripts"))
    import c3_sweep_dryrun as dry
    base = sweep.load_config(ADA_CONFIG)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    config, overridden = dry.dryrun_config(base, tmp_path, bin_dir)
    assert set(overridden) == {"nodes", "instances", "runs", "workers", "liveness", "min_live_nodes",
                               "gpu_wait_seconds", "max_collect_sessions", "paper_a_check", "ollama"}
    for key in set(base) - set(overridden):
        assert config[key] == base[key], key
    assert config["nodes"] == ["digits_mlp", "openml_breast_w"]
    command = config["paper_a_check"]["command"]
    assert command[:2] == base["paper_a_check"]["command"][:2]
    fake = json.loads(Path(command[command.index("--config") + 1]).read_text())
    assert fake["expected_branch"] == "paper-a-v4-ada"
