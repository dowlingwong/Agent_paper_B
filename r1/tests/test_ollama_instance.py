"""Dedicated Ollama instance per batch (C3 sweep; 19 Oct 2026). Fake server only.

AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

import pytest

from r1.scripts.ollama_instance import OllamaInstance, port_is_free

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_ollama.py"


@pytest.fixture
def fake(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    monkeypatch.delenv("C3_FAKE_FAULTS", raising=False)
    binary = tmp_path / "ollama"
    binary.write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE} \"$@\"\n")
    binary.chmod(0o755)
    return binary, root


def test_start_health_record_and_stop(tmp_path, fake):
    binary, root = fake
    batch = tmp_path / "batch"
    inst = OllamaInstance(batch, str(binary), label="DRYRUN", start_timeout=20)
    record = inst.start()
    try:
        assert inst.health() == {"version": "DRYRUN"}
        saved = json.loads(inst.record_path.read_text())
        assert saved["pid"] == inst.process.pid and saved["port"] == inst.port
        assert Path(saved["models_dir"]).is_relative_to(batch.resolve())
        assert saved["version"] == {"version": "DRYRUN"}
        serve = [json.loads(l) for l in (root / "fake_calls.jsonl").read_text().splitlines()
                 if json.loads(l).get("event") == "serve"]
        assert serve[0]["port"] == inst.port and serve[0]["models"] == saved["models_dir"]
    finally:
        inst.stop()
    assert not inst.alive() and inst.health() is None
    assert json.loads(inst.record_path.read_text())["stopped_utc"]
    assert record["pgid"] == record["pid"]  # own process group


def test_refuses_a_port_in_use(tmp_path, fake):
    binary, _ = fake
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        port = busy.getsockname()[1]
        assert not port_is_free(port)
        with pytest.raises(RuntimeError, match="in use"):
            OllamaInstance(tmp_path / "b", str(binary), port=port).start()


def test_models_dir_must_live_under_the_batch(tmp_path, fake):
    binary, _ = fake
    with pytest.raises(ValueError):
        OllamaInstance(tmp_path / "b", str(binary), models_dir=tmp_path / "elsewhere")


def test_models_are_seeded_from_a_pinned_directory(tmp_path, fake):
    binary, _ = fake
    pinned = tmp_path / "pinned"
    (pinned / "blobs").mkdir(parents=True)
    (pinned / "blobs" / "sha256-x").write_bytes(b"model")
    with OllamaInstance(tmp_path / "b", str(binary), seed_models_from=pinned, start_timeout=20) as inst:
        copy = inst.models_dir / "blobs" / "sha256-x"
        assert copy.read_bytes() == b"model"
        assert inst.record["models_seeded"] in ("hardlink", "copy")


def test_stopping_one_instance_never_touches_another(tmp_path, fake):
    binary, _ = fake
    a = OllamaInstance(tmp_path / "a", str(binary), start_timeout=20)
    b = OllamaInstance(tmp_path / "b", str(binary), start_timeout=20)
    a.start()
    b.start()
    try:
        a.stop()
        assert a.health() is None
        assert b.health() == {"version": "DRYRUN"} and b.alive()
    finally:
        a.stop()
        b.stop()


def test_a_server_that_exits_during_start_is_a_stop(tmp_path, fake, monkeypatch):
    binary, _ = fake
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(tmp_path / "unmarked"))
    with pytest.raises(RuntimeError, match="exited during start"):
        OllamaInstance(tmp_path / "b", str(binary), start_timeout=20).start()
