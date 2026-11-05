"""RUNBOOK A.10 (25 Oct 2026): dedicated llama-server per batch, pins, offload, watchdog, orphans.

PLAN §10 R1-INFER-LLAMACPP.  No GPU, no LLM: the HTTP-only fake llama-server
(``r1/scripts/c3_fake_llama_server.py``) behind a shebang wrapper.  The end-to-end
checks are the llama.cpp dry-run scenarios in ``test_c3_sweep_dryrun.py``.
AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from r1.scripts import c3_label_sweep as sweep
from r1.scripts import llama_server_instance as lsi

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_llama_server.py"
FULL_LOG = """load_tensors: offloading 28 repeating layers to GPU
load_tensors: offloaded 29/29 layers to GPU
load_tensors:        CUDA0 model buffer size =  4168.09 MiB
llama_kv_cache_unified:      CUDA0 KV buffer size =   448.00 MiB
"""


@pytest.fixture(autouse=True)
def _no_dryrun(monkeypatch):
    monkeypatch.delenv("R1_DRYRUN", raising=False)


@pytest.fixture
def fake(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    monkeypatch.delenv("C3_FAKE_FAULTS", raising=False)
    binary = tmp_path / "bin" / "llama-server"
    binary.parent.mkdir()
    binary.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                      f"runpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    binary.chmod(0o755)
    model = tmp_path / "models" / "m-Q4_K_M.gguf"
    model.parent.mkdir()
    model.write_bytes(b"GGUF fixture")
    started = []
    pending = []
    if sys.platform == 'darwin':
        # These tests use only child fake servers. Mac has no /proc, so the
        # fixture supplies identity from Popen for those owned children; this
        # does not test real Linux /proc identity or signal foreign processes.
        def owned(pid):
            return next((x for x in started + pending if x.process is not None and x.process.pid == pid), None)
        def fake_cmdline(pid):
            instance = owned(pid)
            if instance is None or instance.process.poll() is not None: raise OSError('not an owned fake server')
            return [sys.executable, *instance.argv]
        def fake_uid(pid):
            if owned(pid) is None: raise OSError('not an owned fake server')
            return os.getuid()
        def fake_alive(pid):
            instance = owned(pid)
            return instance is not None and instance.process.poll() is None
        monkeypatch.setattr(lsi, 'proc_cmdline', fake_cmdline)
        monkeypatch.setattr(lsi, 'proc_uid', fake_uid)
        monkeypatch.setattr(lsi, 'pid_alive', fake_alive)

    def start(faults=(), env=None, **kwargs):
        monkeypatch.setenv("C3_FAKE_FAULTS", json.dumps(list(faults)))
        for key, value in (env or {}).items():
            monkeypatch.setenv(key, value)
        inst = lsi.LlamaServerInstance(tmp_path / "batch", str(binary), model_path=str(model), alias="r1-manager",
                                       label="DRYRUN", start_timeout=20, **kwargs)
        pending.append(inst)
        inst.start(build=lsi.build_info(str(binary)), model_sha256=lsi.sha256_file(model))
        pending.remove(inst)
        started.append(inst)
        return inst
    yield {"start": start, "root": root, "binary": binary, "model": model, "tmp": tmp_path}
    for inst in started:
        inst.stop(timeout=5)


def _chat(inst, timeout=3.0):
    body = json.dumps({"model": "r1-manager", "messages": [{"role": "user", "content": "Budget index"}],
                       "seed": 1}).encode()
    try:
        urlopen(Request(inst.url + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}),
                timeout=timeout).read()
    except OSError:
        pass


# -- pins and parsing ----------------------------------------------------------

def test_build_info_and_sha256(fake, tmp_path):
    info = lsi.build_info(str(fake["binary"]))
    assert info["version_line"] == "version: 0 (DRYRUN)" and info["build_number"] == "0" and info["commit"] == "DRYRUN"
    assert lsi.sha256_file(fake["model"]) == __import__("hashlib").sha256(b"GGUF fixture").hexdigest()
    real = "ggml_cuda_init: found 1 CUDA devices:\n  Device 0: NVIDIA GeForce RTX 4090\nversion: 6873 (0e4a0cf2)\nbuilt with cc"
    assert lsi.VERSION_RE.search(real).group(0) == "version: 6873 (0e4a0cf2)"


def test_offload_report_route_i_needs_every_layer_and_no_cpu_fallback():
    # Review of batch B (25 Oct): route (i) is the N/N line alone (author's acceptance); buffers are recorded.
    assert lsi.offload_report(FULL_LOG)["full"] and lsi.offload_report(FULL_LOG)["line"] == "full"
    partial = lsi.offload_report(FULL_LOG.replace("29/29", "20/29"))
    assert not partial["full"] and partial["reasons"] == ["offloaded 20/29 layers"]
    cpu = lsi.offload_report("warning: no usable GPU found, --gpu-layers option will be ignored\n"
                             "load_tensors: offloaded 0/29 layers to GPU\n")
    assert not cpu["full"] and "CPU fallback reported" in cpu["reasons"]
    line_only = lsi.offload_report("load_tensors: offloaded 29/29 layers to GPU\n")
    assert line_only["full"] and line_only["gpu_model_buffers"] == []
    assert not lsi.offload_report("")["full"] and lsi.offload_report("")["line"] == "absent"


# -- the instance ---------------------------------------------------------------

def test_start_records_argv_cmdline_pins_and_identity(fake, monkeypatch):
    inst = fake["start"](env={"LLAMA_ARG_N_GPU_LAYERS": "0", "LLAMA_API_KEY": "x", "C3_FAKE_LLAMA_LOAD_SECONDS": "0.8"})
    rec = json.loads(inst.record_path.read_text())
    assert rec["argv"] == [str(fake["binary"]), "-m", str(fake["model"]), "--host", "127.0.0.1", "--port",
                           str(inst.port), "-ngl", "999", "-c", "8192", "--alias", "r1-manager", "-np", "1"]
    assert rec["cmdline"][1:] == rec["argv"]  # shebang: <python> <binary> <args>
    assert rec["pgid"] == rec["pid"] and rec["healthy_utc"] and rec["health"] == {"status": "ok"}
    assert rec["build"]["version_line"] == "version: 0 (DRYRUN)" and len(rec["model_sha256"]) == 64
    assert rec["env_removed"] == ["LLAMA_API_KEY", "LLAMA_ARG_N_GPU_LAYERS"]
    serve = [json.loads(l) for l in (fake["root"] / "fake_calls.jsonl").read_text().splitlines()
             if '"serve"' in l][-1]
    assert serve["env_llama_arg"] == []  # never inherited by the server
    assert inst.model_ids() == ["r1-manager"] and inst.props()["model_path"] == str(fake["model"])
    assert inst.offload()["full"] and inst.openai_base_url.endswith("/v1")
    assert inst.chat("Reply OK")["choices"][0]["message"]["content"] == "OK"
    inst.stop()
    assert json.loads(inst.record_path.read_text())["returncode"] == -15


def test_refuses_a_busy_port_and_a_missing_model(fake):
    first = fake["start"]()
    with pytest.raises(RuntimeError, match="in use"):
        fake["start"](port=first.port)
    inst = lsi.LlamaServerInstance(fake["tmp"] / "batch", str(fake["binary"]), model_path="/nonexistent.gguf",
                                   alias="a")
    with pytest.raises(RuntimeError, match="GGUF file not found"):
        inst.start()


def test_restart_generation_reuses_the_port_and_keeps_records(fake):
    first = fake["start"]()
    first.stop()
    again = fake["start"](port=first.port, generation=1)
    assert again.health() and again.record_path.name == f"llama_server_{first.port}_r1.json"
    assert first.record_path.exists() and again.log_path.name == f"llama_server_{first.port}_r1.log"


# -- orphans --------------------------------------------------------------------

def test_cmdline_match_is_strict():
    argv = ["/b/llama-server", "-m", "/m.gguf", "--host", "127.0.0.1", "--port", "8085", "-np", "1"]
    assert lsi.cmdline_matches(argv, argv)[0]
    assert lsi.cmdline_matches(["/usr/bin/python3", *argv], argv)[0]  # a shebang script
    assert lsi.cmdline_matches(["/usr/bin/sh", *argv], argv)[0]
    for cmd, reason in ((["/other/llama-server", *argv[1:]], "binary differs"),
                        (["/usr/bin/perl", *argv], "binary differs"),
                        ([*argv[:6], "8086", *argv[7:]], "port differs"),
                        ([argv[0], "-m", "/other.gguf", *argv[3:]], "model path differs"),
                        ([*argv, "--verbose"], "arguments differ"), ([], "no command line")):
        assert lsi.cmdline_matches(cmd, argv) == (False, reason)


def test_orphan_is_stopped_only_when_provably_ours(fake):
    inst = fake["start"]()
    record = dict(inst.record)
    wrong_argv = list(record["argv"])
    wrong_argv[wrong_argv.index("-c") + 1] = "4096"
    for wrong in ({"port": record["port"] + 1, "argv": [a if a != str(record["port"]) else str(record["port"] + 1)
                                                          for a in record["argv"]]},
                  {"argv": [record["argv"][0], "-m", "/elsewhere.gguf", *record["argv"][3:]]},
                  {"argv": wrong_argv}, {"pgid": record["pgid"] + 1}, {"argv": ["/usr/bin/llama-server"]}):
        ours, reason = lsi.orphan_matches({**record, **wrong})
        assert not ours, (wrong, reason)
        assert lsi.stop_orphan({**record, **wrong})["action"] == "none" and inst.alive()
    assert lsi.orphan_matches(record)[0]
    assert lsi.stop_orphan(record)["action"] in ("SIGTERM", "SIGKILL")
    inst.process.wait(timeout=10)
    assert not inst.alive() and not lsi.orphan_matches(record)[0]


def _uid(proc_dir):
    try:
        return lsi.proc_uid(int(proc_dir.name))
    except (OSError, ValueError):
        return None


def test_another_users_or_unrelated_process_is_never_signalled(tmp_path):
    other = next((int(p.name) for p in Path("/proc").glob("[0-9]*")
                  if (p / "status").exists() and _uid(p) not in (None, os.getuid())), None)
    if other is not None:  # a live process of another user: never ours, whatever the record says
        argv = lsi.proc_cmdline(other) if os.access(f"/proc/{other}/cmdline", os.R_OK) else ["x"]
        ours, reason = lsi.orphan_matches({"pid": other, "pgid": os.getpgid(other), "port": 1, "argv": argv})
        assert not ours and "another user" in reason
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    try:
        time.sleep(0.2)
        record = {"pid": proc.pid, "pgid": proc.pid, "port": 8085,
                  "argv": ["/b/llama-server", "-m", "/m.gguf", "--port", "8085"]}
        assert lsi.stop_orphan(record) ["action"] == "none" and proc.poll() is None  # our user, other command line
    finally:
        proc.kill()
        proc.wait()


# -- the runner on the llama.cpp backend ----------------------------------------------------

def _llama_config(tmp, **llamacpp):
    config = sweep.load_config(None)
    config["backend"] = "llamacpp"
    config["llamacpp"] = dict(config["llamacpp"], binary=str(tmp / "bin/llama-server"),
                              model_path=str(tmp / "models/m-Q4_K_M.gguf"),
                              model_sha256=__import__("hashlib").sha256(b"GGUF fixture").hexdigest(),
                              build="version: 0 (DRYRUN)", footprint_mib=6000, start_timeout=20, **llamacpp)
    config["allowed_hosts"] = [platform.node().split(".")[0]]
    return config


def _runner(tmp, config):
    batch = tmp / "batch"
    batch.mkdir(exist_ok=True)
    return sweep.SweepRunner(config, batch=batch, paper=tmp, harness=tmp, python="py")


def test_backend_config_validation(tmp_path):
    assert sweep.load_config(None)["backend"] == "ollama"  # historical configs keep their meaning
    path = tmp_path / "c.json"
    good = {"backend": "llamacpp", "llamacpp": {"binary": "/opt/llama-server", "model_path": "/m/x.gguf",
                                                "model_sha256": "a" * 64, "build": "version: 6873 (0e4a0cf2)",
                                                "footprint_mib": 6000, "port": 18481}}
    path.write_text(json.dumps(good))
    assert sweep.load_config(path)["llamacpp"]["n_gpu_layers"] == 999
    bad_values = [{"backend": "vllm"}, {"llamacpp": {"bogus": 1}}, {"llamacpp": {"model_sha256": "A" * 64}},
                  {"llamacpp": {"build": "b6873"}}, {"llamacpp": {"binary": "llama-server"}},
                  {"llamacpp": {"model_path": None}}, {"llamacpp": {"footprint_mib": 0}},
                  {"llamacpp": {"port": 80}}, {"llamacpp": {"extra_args": ["--port", "1"]}},
                  {"llamacpp": {"model_alias": "a b"}}, {"llamacpp": {"n_gpu_layers": 0}}]
    for bad in bad_values:
        merged = json.loads(json.dumps(good))
        for key, value in bad.items():
            merged[key] = dict(merged[key], **value) if isinstance(value, dict) else value
        path.write_text(json.dumps(merged))
        with pytest.raises(sweep.Stop):
            sweep.load_config(path)
    draft = {"backend": "llamacpp", "llamacpp": {k: "TODO_VERIFY_ON_HOST" for k in
                                                 ("binary", "model_path", "model_sha256", "build", "port",
                                                  "footprint_mib")}}
    path.write_text(json.dumps(draft))
    with pytest.raises(sweep.Stop, match="unresolved TODO_VERIFY"):
        sweep.load_config(path)
    assert len(sweep.placeholders(sweep.load_config(path, allow_placeholders=True))) == 6


def test_pins_refuse_a_different_build_or_gguf(fake):
    tmp = fake["tmp"]
    runner = _runner(tmp, _llama_config(tmp))
    assert runner.llamacpp_pins()["verdict"] == "pinned"
    assert runner.gpu["MODEL_FOOTPRINT_MIB"] == 6000  # co-tenancy margin uses the llama.cpp footprint
    runner.config["llamacpp"]["build"] = "version: 6873 (0e4a0cf2)"
    with pytest.raises(sweep.Stop, match="build .* differs from the pin"):
        runner.llamacpp_pins()
    runner.config["llamacpp"].update(build="version: 0 (DRYRUN)", model_sha256="0" * 64)
    with pytest.raises(sweep.Stop, match="GGUF sha256 .* differs from the pin"):
        runner.llamacpp_pins()
    assert [c["verdict"] for c in runner.state["llamacpp_pin_checks"]] == \
        ["pinned", "refused: build", "refused: model sha256"]


@pytest.mark.parametrize("offload,reason", [("cpu", "CPU fallback"), ("20", "offloaded 20/29")])
def test_cpu_fallback_or_partial_offload_is_a_stop(fake, offload, reason):
    tmp = fake["tmp"]
    runner = _runner(tmp, _llama_config(tmp))
    runner.service = fake["start"](env={"C3_FAKE_LLAMA_OFFLOAD": offload})
    runner.gpu["check_gpu"] = lambda: pytest.fail("no census after a failed offload check")
    with pytest.raises(sweep.Stop, match=f"not fully offloaded.*{reason}"):
        runner.check_offload("load_probe")
    record = json.loads((runner.batch / "gpu_offload_load_probe.json").read_text())
    assert record["backend"] == "llamacpp" and not record["offload"]["full"]


def test_full_offload_passes_and_census_runs(fake):
    tmp = fake["tmp"]
    runner = _runner(tmp, _llama_config(tmp))
    runner.service = fake["start"]()
    calls = []
    runner.gpu["check_gpu"] = lambda: calls.append(1)
    runner.check_offload("load_probe")
    assert calls == [1]
    runner.config["llamacpp"]["model_alias"] = "other"
    with pytest.raises(sweep.Stop, match="pinned alias"):
        runner.check_offload("after")


def test_collector_env_and_manager_model(fake):
    tmp = fake["tmp"]
    runner = _runner(tmp, _llama_config(tmp))
    runner.state["llama_server"] = {"url": "http://127.0.0.1:18481", "openai_base_url": "http://127.0.0.1:18481/v1"}
    env = runner.service_env()
    assert env["LLAMACPP_BASE_URL"] == "http://127.0.0.1:18481/v1" and "OLLAMA_BASE_URL" not in env
    assert runner.manager_model_args() == ["--manager-model", "llamacpp/r1-manager"]
    ollama = _runner(tmp, sweep.load_config(None))
    ollama.state["ollama"] = {"url": "http://127.0.0.1:11481"}
    assert ollama.service_env()["OLLAMA_BASE_URL"] == "http://127.0.0.1:11481" and ollama.manager_model_args() == []
    assert ollama.service_key == "ollama" and runner.service_key == "llama_server"


@pytest.mark.parametrize("mode,kind", [("sigterm", "server_exited"), ("freeze", "unresponsive"),
                                       ("unload", "model_missing")])
def test_watchdog_on_injected_llama_server_loss(fake, mode, kind):
    inst = fake["start"]([{"chat_call": 1, "mode": mode}])
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
    assert "fault=" + mode in inst.log_path.read_text()  # the request line the loss record quotes


def test_a_matching_process_of_another_user_is_never_signalled(fake, monkeypatch):
    inst = fake["start"]()
    assert lsi.orphan_matches(inst.record)[0]
    monkeypatch.setattr(lsi, "proc_uid", lambda pid: os.getuid() + 1)  # same pid, group and argv; other owner
    ours, reason = lsi.orphan_matches(inst.record)
    assert not ours and reason == "pid belongs to another user"
    assert lsi.stop_orphan(inst.record)["action"] == "none" and inst.alive()


def test_server_exiting_before_ready_finalizes_its_record(tmp_path):
    """Lease completion requires every observed server record to name a stop.

    A failed start (template parser error, 32k OOM, ...) is over; its record must carry
    stopped_utc/returncode even though it was never healthy (so it served no request).
    """
    binary = tmp_path / 'bin' / 'llama-server'
    binary.parent.mkdir()
    binary.write_text('#!/bin/sh\nsleep 0.4\nexit 1\n')
    binary.chmod(0o755)
    model = tmp_path / 'models' / 'm.gguf'
    model.parent.mkdir()
    model.write_bytes(b'GGUF fixture')
    inst = lsi.LlamaServerInstance(tmp_path / 'batch', str(binary), model_path=str(model),
                                   alias='r1-manager', start_timeout=10)
    with pytest.raises(RuntimeError, match='exited during start'):
        inst.start()
    record = json.loads(inst.record_path.read_text())
    assert isinstance(record.get('stopped_utc'), str) and record['stopped_utc']
    assert record.get('returncode') == 1
    assert record.get('exited_early') == 1 and record.get('stopped_before_ready') is True
    assert 'healthy_utc' not in record
    assert inst.alive() is False


def test_failed_start_records_the_lease_inheritance_proof(tmp_path, monkeypatch):
    """A server that exits before readiness must still carry the SAME-OFD proof.

    Lease completion requires an inheritance row on every server record; the proof is
    captured immediately after Popen (the FD is inherited at fork/exec) instead of only
    in the /health branch.
    """
    from r1.exam import cache_runtime

    seen = []
    def fake_verify(pid, lease_fd, **kwargs):
        seen.append((pid, lease_fd, kwargs))
        return {'version': 'trackx_lease_inheritance/v1', 'server_pid': pid,
                'server_start_ticks': 777, 'lease_fd': lease_fd, 'kcmp_rc': 0,
                'kcmp_same_ofd': True, 'method': 'synthetic-fixture'}
    monkeypatch.setattr(cache_runtime, 'verify_server_lease_inheritance', fake_verify)
    binary = tmp_path / 'bin' / 'llama-server'
    binary.parent.mkdir()
    binary.write_text('#!/bin/sh\nsleep 0.6\nexit 1\n')
    binary.chmod(0o755)
    model = tmp_path / 'models' / 'm.gguf'
    model.parent.mkdir()
    model.write_bytes(b'GGUF fixture')
    lease_path = tmp_path / 'lease'
    lease_path.touch()
    lease_fd = os.open(lease_path, os.O_RDWR)
    inst = lsi.LlamaServerInstance(tmp_path / 'batch', str(binary), model_path=str(model),
                                   alias='r1-manager', start_timeout=10)
    try:
        with pytest.raises(RuntimeError, match='exited during start'):
            inst.start(lease_fd=lease_fd)
    finally:
        os.close(lease_fd)
    record = json.loads(inst.record_path.read_text())
    assert record['lease_inheritance']['kcmp_same_ofd'] is True
    assert record['lease_inheritance']['server_pid'] == record['pid']
    assert record['start_ticks'] == 777
    assert isinstance(record.get('stopped_utc'), str) and record['stopped_utc']
    assert record.get('returncode') == 1 and record.get('stopped_before_ready') is True
    assert seen and seen[0][1] == lease_fd
