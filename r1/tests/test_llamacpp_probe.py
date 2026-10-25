"""RUNBOOK A.11 helper: the one-token load probe, against the fake llama-server (no GPU).

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
    monkeypatch.delenv("C3_FAKE_FAULTS", raising=False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "llama-server"
    binary.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                      f"runpy.run_path({str(FAKE)!r}, run_name='__main__')\n")
    binary.chmod(0o755)
    smi = bin_dir / "nvidia-smi"  # lists every live fake server as a 4500 MiB compute app
    smi.write_text("#!/bin/sh\ncase \"$*\" in *compute-apps*) for p in $(pgrep -f c3_fake_llama_server -d ' ') "
                   "$(pgrep -f 'bin/llama-server' -d ' '); do echo \"$p, 4500\"; done;; *) echo 'fake gpu';; esac\n")
    smi.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    model = tmp_path / "m-Q4_K_M.gguf"
    model.write_bytes(b"GGUF fixture")
    return {"binary": str(binary), "model": str(model), "out": tmp_path / "logs"}


def _run(host, *extra):
    argv = ["--binary", host["binary"], "--model", host["model"], "--gpu", "GPU-DRYRUN",
            "--port", str(free_port()), "--out", str(host["out"]), "--start-timeout", "20", *extra]
    rc = probe.main(argv)
    record = json.loads(next(host["out"].glob("probe_*.json")).read_text())
    return rc, record


def test_full_offload_probe_records_pins_footprint_and_stops_the_server(host):
    rc, record = _run(host, "--expect-build", "version: 0 (DRYRUN)")
    assert rc == 0 and record["verdict"] == "FULL_GPU_OFFLOAD", record
    assert record["build"]["version_line"] == "version: 0 (DRYRUN)" and len(record["model_sha256"]) == 64
    assert record["offload"]["offloaded_layers"] == record["offload"]["total_layers"] == 29
    assert record["served_models"] == ["r1-manager"] and record["props"]["model_path"] == host["model"]
    assert record["server_gpu_mib"] == 4500 and record["probe"]["content"] == "OK"
    assert record["server_stop"]["returncode"] == -15 and Path(record["server_log"]).exists()


@pytest.mark.parametrize("extra,env", [((), {"C3_FAKE_LLAMA_OFFLOAD": "cpu"}), ((), {"C3_FAKE_LLAMA_OFFLOAD": "12"}),
                                       (("--expect-sha256", "0" * 64), {})])
def test_cpu_fallback_partial_offload_or_wrong_pin_is_not_accepted(host, monkeypatch, extra, env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    rc, record = _run(host, *extra)
    assert rc == 1 and record["verdict"] == "NOT_ACCEPTED", record
    assert record["server_stop"]["returncode"] == -15
