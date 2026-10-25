"""RUNBOOK A.11 helper: the load probe, against the fake llama-server (no GPU).

Route-(ii) cases (no offload line, CPU control run) are in ``test_llamacpp_offload_routes.py``.
AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from r1.scripts import llamacpp_probe as probe
from r1.scripts.ollama_instance import free_port

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_llama_server.py"


@pytest.fixture
def host(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    for key in ("C3_FAKE_FAULTS", "C3_FAKE_LLAMA_OFFLOAD", "C3_FAKE_LLAMA_GPU_MIB"):
        monkeypatch.delenv(key, raising=False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, run_name in (("llama-server", "__main__"), ("nvidia-smi", "fake_nvidia_smi")):
        exe = bin_dir / name
        exe.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                       f"runpy.run_path({str(FAKE)!r}, run_name={run_name!r})\n")
        exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    model = tmp_path / "m-Q4_K_M.gguf"
    model.write_bytes(b"GGUF fixture")
    return {"binary": str(bin_dir / "llama-server"), "model": str(model), "out": tmp_path / "logs"}


def _run(host, *extra):
    argv = ["--binary", host["binary"], "--model", host["model"], "--gpu", "GPU-DRYRUN",
            "--port", str(free_port()), "--out", str(host["out"]), "--start-timeout", "20", "--gen-tokens", "16",
            *extra]
    rc = probe.main(argv)
    record = json.loads(next(host["out"].glob("probe_*.json")).read_text())
    return rc, record


def test_full_offload_probe_records_pins_footprint_and_stops_the_server(host):
    rc, record = _run(host, "--expect-build", "version: 0 (DRYRUN)")
    assert rc == 0 and record["verdict"] == "FULL_GPU_OFFLOAD" and record["route"] == "log_line", record
    assert record["build"]["version_line"] == "version: 0 (DRYRUN)" and len(record["model_sha256"]) == 64
    assert record["offload"]["offloaded_layers"] == record["offload"]["total_layers"] == 29
    assert record["served_models"] == ["r1-manager"] and record["props"]["model_path"] == host["model"]
    assert record["footprint_mib_to_pin"] == 5560 and record["gpu_generation"]["tokens_per_second"] == 40.0
    assert record["server_stop"]["returncode"] == -15 and Path(record["server_log"]).exists()


@pytest.mark.parametrize("extra,env,reason", [((), {"C3_FAKE_LLAMA_OFFLOAD": "cpu"}, "CPU fallback"),
                                              ((), {"C3_FAKE_LLAMA_OFFLOAD": "12"}, "offloaded 12/29"),
                                              (("--expect-sha256", "0" * 64), {}, "model_sha256 differs")])
def test_cpu_fallback_partial_offload_or_wrong_pin_is_a_stop(host, monkeypatch, extra, env, reason):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    rc, record = _run(host, *extra)
    assert rc == 1 and record["verdict"] == "STOP" and record["route"] is None, record
    assert any(reason in r for r in record["stop_reasons"]), record["stop_reasons"]
    assert record["server_stop"]["returncode"] == -15
