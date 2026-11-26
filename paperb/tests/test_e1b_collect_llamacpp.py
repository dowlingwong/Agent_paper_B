"""RUNBOOK A.10 (25 Oct 2026): the collector and liveness on the llama.cpp manager model.

* ``--manager-model llamacpp/<alias>`` is recorded in the manifest's manager block
  (resume reads it from there) with a ``llamacpp_seed`` seed policy;
* a root campaign that fails with an OpenAI-client exception (the llama.cpp
  provider) is recorded and then re-raised as an exception that survives the
  process pool's pickling; before, ``openai.APIConnectionError`` could not be
  unpickled in the parent and turned one failed root into ``BrokenProcessPool``
  for the whole collector (seen in the llama.cpp ``permanent`` dry run).

AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import pickle
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from r1.headroom import e1b_collect as collect

REPO = Path(__file__).resolve().parents[2]


def _connection_error():
    httpx = pytest.importorskip("httpx")
    openai = pytest.importorskip("openai")
    exc = openai.APIConnectionError(request=httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions"))
    exc.llm_call_attempts = [{"attempt": 1, "error_class": "connection_refused"}]
    return exc


def test_manager_model_ids_and_seed_policy():
    assert collect.check_manager_model("llamacpp/r1-manager") == "llamacpp/r1-manager"
    assert collect.check_manager_model("ollama/qwen2.5-coder:7b")
    for bad in ("r1-manager", "openai/gpt-4.1", "llamacpp/", "vllm/x"):
        with pytest.raises(ValueError):
            collect.check_manager_model(bad)
    assert collect.seed_policy("langgraph", "llamacpp/r1-manager")["kind"] == "llamacpp_seed"
    assert collect.seed_policy("langgraph")["kind"] == "ollama_seed"  # historical default unchanged
    assert collect.seed_policy("langgraph", "ollama/qwen2.5-coder:7b")["kind"] == "ollama_seed"
    assert collect.seed_policy("scripted")["kind"] == "numpy_pcg64"
    assert "llama.cpp" in collect.manager_backend_text("langgraph", "llamacpp/r1-manager")
    assert collect.manager_backend_text("langgraph") == "langgraph qwen2.5-coder:7b (Ollama; pinned digest dae161e2...)"


def _boom(exc):
    raise exc


def _failing_root(tmp: str):
    """In a pool worker: run_root whose campaign raises the llama.cpp client's connection error."""
    collect._run_root = lambda *a, **k: _boom(_connection_error())
    return collect.run_root("digits_mlp", 0, tmp + "/work", 6, [], out_dir=tmp + "/out")


def test_failed_root_with_an_openai_error_is_recorded_and_survives_the_pool(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "_run_root", lambda *a, **k: _boom(_connection_error()))
    with pytest.raises(Exception) as caught:
        collect.run_root("digits_mlp", 0, str(tmp_path / "work"), 6, [], out_dir=str(tmp_path / "out"))
    record = json.loads(next((tmp_path / "out/failures").glob("root__*.json")).read_text())
    assert record["error_class"] == "openai.APIConnectionError"  # the original class is what is recorded
    assert record["transport_attempts"][0]["error_class"] == "connection_refused"
    again = pickle.loads(pickle.dumps(caught.value))  # what the process pool does with it
    assert "APIConnectionError" in str(again) and "failures/root__digits_mlp__" in str(again)
    with ProcessPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_failing_root, str(tmp_path / "pool"))
        returned = future.exception(timeout=120)
    assert type(returned).__name__ == "RootCampaignFailed", repr(returned)  # not BrokenProcessPool
    assert list((tmp_path / "pool/out/failures").glob("root__*.json"))


def test_picklable_exceptions_are_reraised_unchanged(tmp_path, monkeypatch):
    original = ConnectionResetError(104, "reset")
    monkeypatch.setattr(collect, "_run_root", lambda *a, **k: _boom(original))
    with pytest.raises(ConnectionResetError) as caught:
        collect.run_root("digits_mlp", 0, str(tmp_path / "work"), 6, [], out_dir=str(tmp_path / "out"))
    assert caught.value is original


def test_manager_model_flag_needs_langgraph(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(REPO))
    done = subprocess.run([sys.executable, "-m", "r1.headroom.e1b_collect", "--manager", "scripted",
                           "--manager-model", "llamacpp/r1-manager", "--out", str(tmp_path / "o")],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 2 and "--manager-model needs --manager langgraph" in done.stderr
    assert not (tmp_path / "o").exists()
