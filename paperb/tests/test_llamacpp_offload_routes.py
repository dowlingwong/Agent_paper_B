"""Full-offload acceptance on llama.cpp: two routes (review of batch B, 25 Oct 2026).

Real-host evidence (deepthought, llama.cpp v0.7.0, commit 620d222; report
``docs/r1/reports/LLAMACPP_PROBE_DT_20261025.md`` on ``dt-sweep1-20261025``): at
default verbosity the server log has **no** ``offloaded N/N layers`` line and no
``CUDA<k> model buffer`` line, so a log-only check STOPs every real start.  The
author's revised acceptance (runbook, 25 Oct):

(i)  the log line ``offloaded N/N layers`` (N/M with M != N is a STOP even if the
     memory looks fine); or, when the build does not print it,
(ii) the recorded server pid on the configured GPU uuid in ``nvidia-smi
     --query-compute-apps`` with used memory >= the pinned ``footprint_mib``
     (measured by the probe; refused if unset), and no CPU-fallback line.

The probe proves (ii) with a ``-ngl 0`` CPU control run that must be >= 2x slower
in generation tokens/s, records loaded-state telemetry before any assertion and
reports the footprint to pin.  No GPU: the fake llama-server (``C3_FAKE_LLAMA_OFFLOAD
=silent`` mimics v0.7.0) and a fake ``nvidia-smi`` that lists the fake server's
simulated GPU memory.  AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

import pytest

from r1.scripts import c3_label_sweep as sweep
from r1.scripts import llama_server_instance as lsi
from r1.scripts import llamacpp_probe as probe
from r1.scripts.ollama_instance import free_port

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_llama_server.py"
UUID = "GPU-11111111-2222-3333-4444-555555555555"
V070_LOG = """common_params_print_info: verbosity = 3 (adjust with the `-lv N` CLI arg)
load_model: initializing, n_slots = 1, n_ctx_slot = 8192, kv_unified = 'true'
llama_server: model loaded
llama_server: listening on http://127.0.0.1:18081
"""
LINE_LOG = "load_tensors: offloaded 29/29 layers to GPU\nload_tensors:        CUDA0 model buffer size =  4168.09 MiB\n"
REAL_BUILD = "version: 0.7.0-dev (build 1, commit 620d222)"


def _apps(pid, mib, uuid=UUID):
    return [{"pid": pid, "gpu_uuid": uuid, "used_mib": mib}]


# -- the decision (pure) -------------------------------------------------------------------

def test_route_i_log_line_passes_without_memory_evidence():
    check = lsi.offload_check(LINE_LOG, pid=7, gpu_uuid=UUID, footprint_mib=5000, apps=[])
    assert check["full"] and check["route"] == "log_line" and check["offloaded_layers"] == 29


def test_route_i_partial_line_stops_even_with_enough_memory():
    log = LINE_LOG.replace("29/29", "20/29")
    check = lsi.offload_check(log, pid=7, gpu_uuid=UUID, footprint_mib=5000, apps=_apps(7, 9000))
    assert not check["full"] and check["route"] is None and "offloaded 20/29 layers" in check["reasons"][0]


def test_route_ii_memory_on_the_target_card_passes_when_the_build_prints_no_line():
    check = lsi.offload_check(V070_LOG, pid=7, gpu_uuid=UUID, footprint_mib=5304,
                              apps=[{"pid": 99, "gpu_uuid": UUID, "used_mib": 100}, *_apps(7, 5560)])
    assert check["full"] and check["route"] == "gpu_memory"
    assert check["gpu_memory"]["used_mib"] == 5560 and check["gpu_memory"]["footprint_mib"] == 5304


@pytest.mark.parametrize("apps,footprint,reason", [
    (_apps(7, 5000), 5304, "below the pinned footprint"),          # footprint too low
    (_apps(8, 9000), 5304, "not listed on"),                       # pid not on the card
    (_apps(7, 9000, uuid="GPU-other"), 5304, "not listed on"),     # pid on another card
    (None, 5304, "nvidia-smi"),                                    # no telemetry
    (_apps(7, 9000), None, "footprint_mib is not set"),            # nothing pinned: refused
])
def test_route_ii_failures_stop(apps, footprint, reason):
    check = lsi.offload_check(V070_LOG, pid=7, gpu_uuid=UUID, footprint_mib=footprint, apps=apps)
    assert not check["full"] and check["route"] is None
    assert any(reason in r for r in check["reasons"]), check["reasons"]


def test_cpu_fallback_line_stops_both_routes():
    fallback = "warning: no usable GPU found, --gpu-layers option will be ignored\n"
    for log in (fallback + V070_LOG, fallback + LINE_LOG):
        check = lsi.offload_check(log, pid=7, gpu_uuid=UUID, footprint_mib=5304, apps=_apps(7, 9000))
        assert not check["full"] and "CPU fallback reported" in check["reasons"]


def test_compute_apps_parsing():
    out = f"3546902, {UUID}, 5560\n  12, GPU-x, [N/A]\n"
    assert lsi.parse_compute_apps(out) == [{"pid": 3546902, "gpu_uuid": UUID, "used_mib": 5560},
                                           {"pid": 12, "gpu_uuid": "GPU-x", "used_mib": None}]
    assert lsi.parse_compute_apps("No running processes found\n") == []


def test_real_v070_build_line_is_parsed_and_accepted_as_a_pin(tmp_path):
    found = lsi.parse_version(REAL_BUILD + "\nbuilt with GNU 13.3.1 for Linux x86_64\n")
    assert found == {"version_line": REAL_BUILD, "build_number": "0.7.0-dev", "commit": "620d222"}
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"backend": "llamacpp", "llamacpp": {
        "binary": "/ceph/dwong/opt/llama.cpp/build-gcc13/bin/llama-server",
        "model_path": "/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "model_sha256": "509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c",
        "build": REAL_BUILD, "footprint_mib": 5304}}))
    assert sweep.load_config(path)["llamacpp"]["build"] == REAL_BUILD


# -- the fake host: llama-server + nvidia-smi listing its simulated GPU memory --------------

@pytest.fixture
def host(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    monkeypatch.delenv("C3_FAKE_FAULTS", raising=False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "llama-server"
    binary.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                      f"runpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    binary.chmod(0o755)
    smi = bin_dir / "nvidia-smi"
    smi.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                   f"runpy.run_path({str(FAKE)!r}, run_name='fake_nvidia_smi')\n")
    smi.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    model = tmp_path / "m-Q4_K_M.gguf"
    model.write_bytes(b"GGUF fixture")
    started = []

    def start(offload="line", gpu_mib=None, **kwargs):
        monkeypatch.setenv("C3_FAKE_LLAMA_OFFLOAD", offload)
        if gpu_mib is not None:
            monkeypatch.setenv("C3_FAKE_LLAMA_GPU_MIB", str(gpu_mib))
        inst = lsi.LlamaServerInstance(tmp_path / "batch", str(binary), model_path=str(model), alias="r1-manager",
                                       gpu_uuid=UUID, label="DRYRUN", start_timeout=20, **kwargs)
        inst.start()
        started.append(inst)
        return inst
    yield {"start": start, "binary": str(binary), "model": str(model), "tmp": tmp_path, "root": root}
    for inst in started:
        inst.stop(timeout=5)


def test_fake_v070_log_has_no_offload_line_and_fake_nvidia_smi_lists_the_server(host):
    inst = host["start"]("silent", gpu_mib=5560)
    text = inst.log_text()
    assert "offloaded" not in text and "model buffer" not in text and "llama_server: model loaded" in text
    assert {"pid": inst.record["pid"], "gpu_uuid": UUID, "used_mib": 5560} in lsi.gpu_compute_apps()


def _runner(tmp, footprint):
    config = sweep.load_config(None)
    config["backend"] = "llamacpp"
    config["llamacpp"] = dict(config["llamacpp"], binary=str(tmp / "bin/llama-server"),
                              model_path=str(tmp / "m-Q4_K_M.gguf"), model_sha256="0" * 64,
                              build="version: 0 (DRYRUN)", footprint_mib=footprint)
    config["allowed_hosts"] = [platform.node().split(".")[0]]
    (tmp / "batch").mkdir(exist_ok=True)
    runner = sweep.SweepRunner(config, batch=tmp / "batch", paper=tmp, harness=tmp, python="py")
    runner.gpu["check_gpu"] = lambda: None
    return runner


@pytest.mark.parametrize("offload,gpu_mib,route", [("line", 5560, "log_line"), ("silent", 5560, "gpu_memory")])
def test_runner_check_passes_by_either_route_and_records_it(host, offload, gpu_mib, route):
    runner = _runner(host["tmp"], 5304)
    runner.service = host["start"](offload, gpu_mib=gpu_mib)
    runner.check_offload("load_probe")
    record = json.loads((runner.batch / "gpu_offload_load_probe.json").read_text())
    assert record["offload"]["full"] and record["offload"]["route"] == route


@pytest.mark.parametrize("offload,gpu_mib,reason", [("silent", 4000, "below the pinned footprint"),
                                                    ("20", 9000, "offloaded 20/29 layers"),
                                                    ("cpu", 9000, "CPU fallback")])
def test_runner_check_stops_on_low_memory_partial_line_or_fallback(host, offload, gpu_mib, reason):
    runner = _runner(host["tmp"], 5304)
    runner.service = host["start"](offload, gpu_mib=gpu_mib)
    with pytest.raises(sweep.Stop, match=reason):
        runner.check_offload("load_probe")
    record = json.loads((runner.batch / "gpu_offload_load_probe.json").read_text())
    assert not record["offload"]["full"] and record["offload"]["route"] is None


def test_runner_check_stops_when_the_server_pid_is_not_on_the_card(host):
    runner = _runner(host["tmp"], 5304)
    runner.service = host["start"]("silent", gpu_mib=0)  # 0: the fake lists nothing (a CPU-only server)
    with pytest.raises(sweep.Stop, match="not listed on"):
        runner.check_offload("after")


# -- the probe ---------------------------------------------------------------------------------

def _probe(host, *extra, env=None, monkeypatch=None):
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    out = host["tmp"] / "logs"
    argv = ["--binary", host["binary"], "--model", host["model"], "--gpu", UUID, "--port", str(free_port()),
            "--out", str(out), "--start-timeout", "20", "--gen-tokens", "16", *extra]
    rc = probe.main(argv)
    return rc, json.loads(next(out.glob("probe_*.json")).read_text())


def test_probe_route_i(host, monkeypatch):
    rc, record = _probe(host, env={"C3_FAKE_LLAMA_OFFLOAD": "line", "C3_FAKE_LLAMA_GPU_MIB": "5560"},
                        monkeypatch=monkeypatch)
    assert rc == 0 and record["verdict"] == "FULL_GPU_OFFLOAD" and record["route"] == "log_line"
    assert record["footprint_mib_to_pin"] == 5560 and record["cpu_control"] is None


def test_probe_route_ii_with_cpu_control(host, monkeypatch):
    rc, record = _probe(host, env={"C3_FAKE_LLAMA_OFFLOAD": "silent", "C3_FAKE_LLAMA_GPU_MIB": "5560",
                                   "C3_FAKE_LLAMA_TPS_GPU": "40", "C3_FAKE_LLAMA_TPS_CPU": "8"},
                        monkeypatch=monkeypatch)
    assert rc == 0 and record["verdict"] == "FULL_GPU_OFFLOAD" and record["route"] == "gpu_memory", record
    assert record["footprint_mib_to_pin"] == 5560
    control = record["cpu_control"]
    assert control["argv_ngl"] == "0" and control["passed"] and control["speedup"] == pytest.approx(5.0)
    assert record["loaded"]["compute_apps"] and record["loaded"]["utc"]  # telemetry recorded


@pytest.mark.parametrize("env,extra,reason", [
    ({"C3_FAKE_LLAMA_TPS_GPU": "40", "C3_FAKE_LLAMA_TPS_CPU": "30"}, (), "speedup"),   # CPU control too fast
    ({"C3_FAKE_LLAMA_GPU_MIB": "0"}, (), "not listed on"),                              # server not on the card
    ({"C3_FAKE_LLAMA_GPU_MIB": "100"}, ("--min-gpu-mib", "4000"), "below"),             # far too little memory
    ({}, ("--expect-footprint-mib", "6000"), "below"),                                  # below a pinned footprint
])
def test_probe_route_ii_failures_exit_nonzero_with_telemetry(host, monkeypatch, env, extra, reason):
    rc, record = _probe(host, *extra, env={"C3_FAKE_LLAMA_OFFLOAD": "silent", "C3_FAKE_LLAMA_GPU_MIB": "5560", **env},
                        monkeypatch=monkeypatch)
    assert rc == 1 and record["verdict"] == "STOP", record
    assert any(reason in r for r in record["stop_reasons"]), record["stop_reasons"]
    assert "loaded" in record and record["server_stop"]["returncode"] == -15


def test_probe_partial_line_is_a_stop(host, monkeypatch):
    rc, record = _probe(host, env={"C3_FAKE_LLAMA_OFFLOAD": "20", "C3_FAKE_LLAMA_GPU_MIB": "9000"},
                        monkeypatch=monkeypatch)
    assert rc == 1 and record["verdict"] == "STOP" and record["route"] is None
    assert any("offloaded 20/29" in r for r in record["stop_reasons"])
