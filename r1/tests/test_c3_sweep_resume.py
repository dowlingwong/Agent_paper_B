"""RUNBOOK A.5 (resume per campaign root) and A.8 (Ollama runner watchdog) in the C3 sweep runner.

No GPU, no LLM: stub instances, synthetic sweep trees and the HTTP-only fake
server.  The end-to-end checks (SIGKILL mid-sweep; server SIGTERM mid-request)
are the ``interrupt`` and ``watchdog`` scenarios in ``test_c3_sweep_dryrun.py``.
AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from r1.scripts import c3_label_sweep as sweep
from r1.scripts import ollama_instance as oi

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_ollama.py"


@pytest.fixture(autouse=True)
def _no_dryrun(monkeypatch):
    monkeypatch.delenv("R1_DRYRUN", raising=False)


def _runner(tmp_path, **config_overrides):
    config = sweep.load_config(None)
    config["allowed_hosts"] = [platform.node().split(".")[0]]
    config.update(config_overrides)
    batch = tmp_path / "batch"
    batch.mkdir(exist_ok=True)
    return sweep.SweepRunner(config, batch=batch, paper=tmp_path, harness=tmp_path, python="py")


def test_resume_and_watchdog_config_defaults_and_validation(tmp_path):
    config = sweep.load_config(None)
    assert config["resume"] == {"sweeps": True, "max_restarts": 5}
    assert config["watchdog"]["enabled"] is False  # opt-in
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"watchdog": {"enabled": True, "poll_seconds": 1}}))
    assert sweep.load_config(path)["watchdog"]["poll_seconds"] == 1
    for bad in ({"resume": {"sweeps": "yes"}}, {"resume": {"max_restarts": -1}}, {"resume": {"bogus": 1}},
                {"watchdog": {"enabled": 1}}, {"watchdog": {"poll_seconds": 0}}, {"watchdog": {"x": 1}},
                {"watchdog": {"unresponsive_checks": 0}}, {"watchdog": {"health_timeout": "10"}}):
        path.write_text(json.dumps(bad))
        with pytest.raises(sweep.Stop):
            sweep.load_config(path)


def test_interrupted_sweep_phase_resumes_other_phases_stop(tmp_path):
    runner = _runner(tmp_path)
    calls = []
    runner.state["steps"]["sweep_none"] = {"completed": False, "started_utc": "20261101T000000Z"}
    runner.phase("sweep_none", lambda: calls.append("resumed"))
    assert calls == ["resumed"] and runner.state["steps"]["sweep_none"]["completed"]
    assert runner.state["steps"]["sweep_none"]["resumed_utc"]
    for name in ("liveness", "preconditions", "index"):
        runner.state["steps"][name] = {"completed": False, "started_utc": "20261101T000000Z"}
        with pytest.raises(sweep.PhaseInterrupted):
            runner.phase(name, lambda: calls.append(name))
    off = _runner(tmp_path, resume={"sweeps": False, "max_restarts": 5})
    off.state["steps"]["sweep_none"] = {"completed": False, "started_utc": "20261101T000000Z"}
    with pytest.raises(sweep.PhaseInterrupted):
        off.phase("sweep_none", lambda: calls.append("off"))
    assert calls == ["resumed"]


def _state_after_preconditions(runner, **steps):
    runner.state["steps"] = {"preconditions": {"completed": True}, **steps}
    runner.save()


def test_restart_after_preconditions_needs_a_resumable_phase(tmp_path, monkeypatch):
    message = "belongs to an earlier process"
    off = _runner(tmp_path, resume={"sweeps": False, "max_restarts": 5})
    _state_after_preconditions(off, liveness={"completed": True})
    with pytest.raises(sweep.Stop, match=message):  # historical behaviour when resume is off
        off.main()
    on = _runner(tmp_path)
    _state_after_preconditions(on, liveness={"completed": False, "started_utc": "x"})
    with pytest.raises(sweep.Stop, match=message):  # an interrupted liveness phase stays a STOP
        on.main()
    restarted = []
    monkeypatch.setattr(sweep.SweepRunner, "restart_service",
                        lambda self, reason, phase: restarted.append((reason, phase)) or {"generation": 1})
    monkeypatch.setattr(sweep.SweepRunner, "sweep", lambda self, mode: None)
    monkeypatch.setattr(sweep.SweepRunner, "index", lambda self: None)
    resumed = _runner(tmp_path)
    _state_after_preconditions(resumed, liveness={"completed": True},
                               sweep_append_only_summary={"completed": False, "started_utc": "x"})
    resumed.main()
    assert restarted == [("process_restart", "sweep_append_only_summary")]
    assert all(resumed.state["steps"][p]["completed"] for p in resumed.phases())


def _sweep_tree(tmp_path):
    """A sweep interrupted mid-collection: A complete, B's record truncated, C and E partial, D failed."""
    runner = _runner(tmp_path)
    out = tmp_path / "results/r1/pilot/C3_sweep_none_X"
    work = runner.batch / "c3_none_work"
    (out / "roots").mkdir(parents=True)
    (out / "failures").mkdir()
    for inst in ("A", "B", "C", "D", "E"):
        (work / "roots" / inst).mkdir(parents=True)
        (work / "roots" / inst / "root_trials.jsonl").write_text('{"budget_index": 1}\n')
    (out / "roots/A.json").write_text(json.dumps({"instance": "A"}))
    (out / "roots/B.json").write_text('{"instance": "B", "start_fi')  # killed mid-write
    (out / "failures/root__D.json").write_text(json.dumps({"instance": "D", "error_class": "ValueError"}))
    runner.state["steps"]["sweep_none"] = {"completed": False, "started_utc": "20261101T000000Z"}
    return runner, out, work


def test_resume_keeps_completed_roots_and_moves_partial_attempts(tmp_path):
    runner, out, work = _sweep_tree(tmp_path)
    a_before = (out / "roots/A.json").read_bytes()
    record = runner.resume_interrupted(out, work, "sweep_none", "process_restart", restart={"generation": 1})
    assert record["roots_completed_kept"] == 1 and (out / "roots/A.json").read_bytes() == a_before
    assert record["root_records_unparseable_moved"] == ["B"]
    assert sorted(record["roots_rerun_whole"]) == ["B", "C", "E"]  # D's failure record stands (never retried)
    assert (work / "roots/A").is_dir() and (work / "roots/D").is_dir()
    for inst in ("B", "C", "E"):
        assert not (work / "roots" / inst).exists()
        assert (work / "interrupted/01/roots" / inst / "root_trials.jsonl").exists()  # kept, never patched
    assert (out / "interrupted/01/roots/B.json").exists() and (out / "failures/root__D.json").exists()
    line = json.dumps(record, default=str)
    assert (runner.batch / "interruptions.jsonl").read_text().strip() == line
    assert (out / "interruptions.jsonl").read_text().strip() == line
    assert (runner.batch / "sweep_none.log").read_text().startswith("INTERRUPTION ")
    assert record["schema"] == sweep.INTERRUPTION_SCHEMA and record["n"] == 1
    assert runner.state["interruptions"][0]["kind"] == "process_restart"


def test_runner_loss_moves_only_transport_failures_of_that_session(tmp_path):
    runner, out, work = _sweep_tree(tmp_path)
    started = time.time() - 1
    os.utime(out / "failures/root__D.json", (started - 100, started - 100))  # older than the session
    lost = {"instance": "C", "transport_attempts": [{"attempt": 3, "error_class": "connection_refused"}]}
    other = {"instance": "E", "transport_attempts": [{"attempt": 1, "error_class": "non_retryable"}]}
    (out / "failures/root__C.json").write_text(json.dumps(lost))
    (out / "failures/root__E.json").write_text(json.dumps(other))
    record = runner.resume_interrupted(out, work, "sweep_none", "runner_lost", event={"kind": "server_exited"},
                                       session_started=started)
    assert record["root_failures_moved"] == ["C"] and (out / "interrupted/01/failures/root__C.json").exists()
    assert (out / "failures/root__D.json").exists() and (out / "failures/root__E.json").exists()
    assert sorted(record["roots_rerun_whole"]) == ["B", "C"]
    assert record["runner_event"] == {"kind": "server_exited"}


def test_gates_count_final_roots_only_and_report_interrupted_attempts(tmp_path):
    runner, out, work = _sweep_tree(tmp_path)
    event = {"event_type": "llm_call", "payload": {"parse_ok": True}}
    (work / "roots/A/root_events.jsonl").write_text(json.dumps(event) + "\n")
    (work / "interrupted/01/roots/C").mkdir(parents=True)
    (work / "interrupted/01/roots/C/root_events.jsonl").write_text((json.dumps(event) + "\n") * 3)
    (out / "manifest.json").write_text(json.dumps({"label": "DRYRUN", "manager": {"kind": "langgraph"}}))
    for p in (out / "failures").glob("*.json"):
        p.unlink()
    (out / "roots/B.json").unlink()
    runner.config["instances"] = 1
    gates = runner.collection_gates(out, work, ["A"], "none")
    assert gates["roots"] == 1 and gates["interrupted_attempts"]["root_attempts"] == 1
    checks = json.loads((out / "collection_checks.json").read_text())
    assert checks["llm_calls"] == 1  # the interrupted attempt's 3 calls are not in the final-root counts
    assert checks["interrupted_attempts"] == {"root_attempts": 1, "llm_calls": 3, "interruptions": 0}


class _Stub:
    def __init__(self):
        self.up, self.healthy, self.rc, self.url, self.record = True, True, None, "http://127.0.0.1:9", {"pid": 7}

    def alive(self):
        return self.up

    def health(self, timeout=2.0):
        return {"version": "x"} if self.healthy else None

    def returncode_info(self):
        return oi.OllamaInstance.returncode_info(self)

    @property
    def process(self):
        return type("P", (), {"poll": lambda _: self.rc})()


def test_watchdog_detects_exit_unresponsive_and_lost_model(monkeypatch):
    spec = dict(sweep.DEFAULTS["watchdog"], unresponsive_checks=2, model_checks=2)
    stub = _Stub()
    dog = sweep.RunnerWatchdog(stub, spec)
    loaded = {"value": True}
    monkeypatch.setattr(dog, "model_loaded", lambda: loaded["value"])
    assert dog.check() is None
    stub.healthy = False
    assert dog.check() is None  # one failed poll is not yet a loss
    event = dog.check()
    assert event["kind"] == "unresponsive" and event["consecutive_failed_health_checks"] == 2
    stub.healthy, dog.health_misses = True, 0
    loaded["value"] = False
    assert dog.check() is None and dog.check()["kind"] == "model_unloaded"
    loaded["value"], dog.model_misses = True, 0
    assert dog.check() is None and dog.model_misses == 0
    stub.up, stub.rc = False, -15
    event = dog.check()
    assert event["kind"] == "server_exited" and event["signal"] == "SIGTERM" and event["returncode"] == -15
    assert event["instance"]["pid"] == 7 and event["last_healthy_utc"] <= event["detected_utc"]


@pytest.fixture
def fake_server(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    binary = tmp_path / "ollama"
    binary.write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE} \"$@\"\n")
    binary.chmod(0o755)

    def start(faults, **kwargs):
        monkeypatch.setenv("C3_FAKE_FAULTS", json.dumps(faults))
        inst = oi.OllamaInstance(tmp_path / "batch", str(binary), label="DRYRUN", start_timeout=20, **kwargs)
        inst.start()
        started.append(inst)
        return inst
    started = []
    yield start, root
    for inst in started:
        inst.stop(timeout=5)


def _chat(inst, timeout=3):
    body = json.dumps({"model": "qwen2.5-coder:7b", "messages": [], "options": {"seed": 1}}).encode()
    try:
        urlopen(Request(inst.url + "/api/chat", data=body, headers={"Content-Type": "application/json"}),
                timeout=timeout).read()
    except OSError:
        pass


@pytest.mark.parametrize("mode,kind", [("sigterm", "server_exited"), ("freeze", "unresponsive"),
                                       ("unload", "model_unloaded")])
def test_watchdog_on_injected_runner_loss(fake_server, mode, kind):
    start, root = fake_server
    inst = start([{"chat_call": 1, "mode": mode}])
    spec = dict(sweep.DEFAULTS["watchdog"], enabled=True, poll_seconds=0.2, health_timeout=1.0,
                unresponsive_checks=2, model_checks=2)
    dog = sweep.RunnerWatchdog(inst, spec)
    assert dog.check() is None
    _chat(inst, timeout=1.5)
    event, deadline = None, time.monotonic() + 15
    while event is None and time.monotonic() < deadline:
        event = dog.check()
        time.sleep(0.2)
    assert event is not None and event["kind"] == kind, event
    if mode == "sigterm":
        assert event["signal"] == "SIGTERM"
    assert (root / f"fault_1_{mode}.fired").exists()
    assert "fault=" + mode in inst.log_path.read_text()  # the request line the loss record quotes


def test_restarted_instance_reuses_port_and_models_and_keeps_records(fake_server):
    start, _ = fake_server
    first = start([])
    first.stop()
    again = start([], port=first.port, models_dir=first.models_dir, generation=1, reuse_models=True)
    assert again.health() and again.record["models_seeded"] == "reused" and again.record["generation"] == 1
    assert again.record_path.name == f"ollama_instance_{first.port}_r1.json" and first.record_path.exists()


def test_orphaned_instance_is_stopped_only_when_it_is_provably_ours(fake_server):
    start, _ = fake_server
    inst = start([])
    record = dict(inst.record)
    for wrong in ({"port": record["port"] + 1}, {"models_dir": "/elsewhere"}, {"pgid": record["pgid"] + 1}):
        ours, reason = oi.orphan_matches({**record, **wrong})
        assert not ours, reason
        assert oi.stop_orphan({**record, **wrong})["action"] == "none" and inst.alive()
    assert oi.orphan_matches(record)[0]
    stopped = oi.stop_orphan(record)
    assert stopped["action"] in ("SIGTERM", "SIGKILL")
    inst.process.wait(timeout=10)
    assert not inst.alive() and not oi.orphan_matches(record)[0]


def test_port_in_time_wait_is_free_but_a_listener_is_not():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    client = socket.create_connection(("127.0.0.1", port))
    conn, _ = server.accept()
    assert not oi.port_is_free(port)  # a listening server
    conn.close()  # the server side closes first: its port enters TIME_WAIT
    time.sleep(0.2)
    client.close()
    server.close()
    assert oi.port_is_free(port)


def test_resume_refuses_while_an_earlier_runner_process_lives(tmp_path):
    runner = _runner(tmp_path)
    marker = f"{runner.batch}/c3_none_work"
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "-m", "r1.headroom.e1b_collect",
                             "--work", marker])
    try:
        time.sleep(0.3)
        found = runner.earlier_processes()
        assert [p["pid"] for p in found] == [proc.pid]
        with pytest.raises(sweep.Stop, match="still alive"):
            runner.restart_service("process_restart", "sweep_none")
        assert runner.state["service_restarts"][0]["refused"][0]["pid"] == proc.pid
    finally:
        proc.kill()
        proc.wait()
    assert runner.earlier_processes() == []


def test_restart_budget_is_enforced(tmp_path):
    runner = _runner(tmp_path, resume={"sweeps": True, "max_restarts": 0})
    with pytest.raises(sweep.Stop, match="max_restarts"):
        runner.restart_service("process_restart", "sweep_none")
    runner.config["watchdog"] = dict(runner.config["watchdog"], max_restarts=0)
    with pytest.raises(sweep.Stop, match="watchdog.max_restarts"):
        runner.restart_service("runner_lost", "sweep_none")


def test_launcher_appends_to_the_runner_log():
    text = (REPO / "r1/scripts/c3_label_sweep_launch.sh").read_text()
    assert "c3_label_sweep.py >> $B/runner.log" in text and "c3_label_sweep.py > $B/runner.log" not in text
