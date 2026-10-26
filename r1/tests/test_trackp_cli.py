"""Track P 1.6: ``r1/scripts/trackp.py`` dry runs on tiny random-weight models (CPU), incl. a SIGKILL-and-resume.

ENGINEERING_ONLY; AI-assisted (Claude). Needs the pool tokenizers in the local HF cache (skips otherwise).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = [sys.executable, str(REPO / "r1" / "scripts" / "trackp.py")]
ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1"}


def _tokenizers_cached() -> bool:
    try:
        from r1.c3.train import tiny
        tiny.tokenizer(*tiny.QWEN)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _tokenizers_cached(), reason="pool tokenizers not in the local HF cache")


def run(*args, check=True):
    res = subprocess.run([*CLI, *args], capture_output=True, text=True, env=ENV, cwd=REPO, timeout=900)
    if check and res.returncode != 0:
        raise AssertionError(f"rc={res.returncode}\n{res.stdout[-2000:]}\n{res.stderr[-4000:]}")
    return res


def _placeholder_config(tmp_path):
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_portal.json").read_text())
    cfg["bases"]["kev-0.8b"]["local_path"] = "TODO_VERIFY_ON_HOST"
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_shipped_config_is_filled():
    res = run("--check-config", check=False)
    assert res.returncode == 0 and json.loads(res.stdout)["placeholders"] == []


def test_check_config_lists_placeholders_and_real_runs_refuse_them(tmp_path):
    cfg = _placeholder_config(tmp_path)
    res = run("--config", cfg, "--check-config", check=False)
    assert res.returncode == 1 and json.loads(res.stdout)["placeholders"] == ["bases.kev-0.8b.local_path"]
    res = run("--config", cfg, "spike", "--base", "kev-0.8b", "--run-dir", str(tmp_path / "x"), check=False)
    assert res.returncode == 2 and "TODO_VERIFY" in res.stderr
    res = run("--config", cfg, "spike", "--base", "kev-0.8b", "--allow-placeholders", "--run-dir", str(tmp_path / "x"),
              check=False)
    assert res.returncode == 2 and "--tiny dry runs only" in res.stderr


def test_later_phases_refuse(tmp_path):
    for cmd in ("sft", "a6", "rb"):
        res = run(cmd, "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir", str(tmp_path), check=False)
        assert res.returncode == 2 and "STOP" in res.stderr


def test_tiny_runs_are_dryrun_and_need_no_note(tmp_path):
    res = run("e0", "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir", str(tmp_path), "--steps", "1",
              "--examples", "8", "--n-test", "8", check=False)
    assert res.returncode == 0, res.stderr[-2000:]
    assert json.loads((tmp_path / "manifest.json").read_text())["evidence_label"] == "DRYRUN"
    # the gate itself (every non-DRYRUN label, with and without a note) is tested in test_trackp_trainer.py


@pytest.mark.parametrize("family", ["kev", "qwen_control"])
def test_toy_batch_e0_and_probes_dry_run(tmp_path, family):
    run("toy", "--tiny", "--family", family, "--allow-placeholders", "--run-dir", str(tmp_path / "toy"),
        "--steps", "6", "--examples", "16")
    rep = json.loads((tmp_path / "toy" / "report.json").read_text())
    man = json.loads((tmp_path / "toy" / "manifest.json").read_text())
    assert rep["reload_identical"] and rep["completed"]
    assert {"total", "belief", "action"} <= set(rep["batch_loss_before"]) and "loss_decreased" in rep
    assert man["evidence_label"] == "DRYRUN" and len(man["git"]["paper"]["commit"]) == 40
    assert man["model_files_sha256"]["heads.safetensors"]
    run("e0", "--tiny", "--family", family, "--allow-placeholders", "--run-dir", str(tmp_path / "e0"),
        "--steps", "3", "--examples", "24", "--n-test", "24", "--with-probes", "--n-probe", "3")
    rep = json.loads((tmp_path / "e0" / "report.json").read_text())
    assert {"head_fit", "lora", "pass", "probes"} <= set(rep)
    assert set(rep["probes"]) >= {"A1", "A2", "A3", "A4", "A5"}
    if family == "qwen_control":
        assert rep["probes"]["A5"]["pass"] is not None


def test_exam_subcommand_runs_the_frozen_rule(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("exam_tests", REPO / "r1/tests/test_trackp_exam_analyze.py")
    T = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(T)                     # reuse its synthetic results builder
    items = T._items()
    base = T._base(items)
    data = T._data(T._model("kev", "kev", 0.30, items, base, seed=1),
                   T._model("qwen-0.8b", "qwen_control", 0.20, items, base, seed=2),
                   T._model("gbdt", "floor", 0.10, items, base, seed=3, e0=None))
    p = tmp_path / "results.json"
    p.write_text(json.dumps(data))
    res = run("exam", "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir", str(tmp_path / "exam"),
              "--results", str(p), check=False)
    assert res.returncode == 0, res.stderr[-2000:]
    rep = json.loads((tmp_path / "exam" / "report.json").read_text())
    assert rep["rule_sha256"] == (REPO / "r1/c3/rules/p3_rule_v1.yaml.sha256").read_text().split()[0]


def _params(run_dir: Path):
    from safetensors.torch import load_file
    return load_file(str(run_dir / "saved" / "adapter" / "adapter_model.safetensors")), \
        load_file(str(run_dir / "saved" / "heads.safetensors"))


def test_toy_kill_and_resume_matches_an_uninterrupted_run(tmp_path):
    args = ["toy", "--tiny", "--family", "kev", "--allow-placeholders", "--steps", "40", "--examples", "32"]
    run(*args, "--run-dir", str(tmp_path / "full"))
    part = tmp_path / "part"
    proc = subprocess.Popen([*CLI, *args, "--run-dir", str(part)], env=ENV, cwd=REPO,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ckpt = part / "toy" / "ckpt"
    deadline = time.time() + 600
    while time.time() < deadline:   # kill once a mid-run checkpoint (not the last) is complete
        done = [p for p in ckpt.glob("step_*") if (p / "COMPLETE").is_file()] if ckpt.is_dir() else []
        if any(int(p.name.split("_")[1]) >= 4 for p in done):
            break
        if proc.poll() is not None:
            pytest.fail("run finished before it could be killed")
        time.sleep(0.05)
    os.kill(proc.pid, signal.SIGKILL)
    proc.wait()
    killed_at = max(int(p.name.split("_")[1]) for p in ckpt.glob("step_*") if (p / "COMPLETE").is_file())
    assert killed_at < 40
    run(*args, "--run-dir", str(part))
    steps = [json.loads(l)["step"] for l in (part / "toy" / "metrics.jsonl").read_text().splitlines()
             if json.loads(l)["kind"] == "step"]
    assert steps == list(range(1, 41))   # each step logged once: steps after the checkpoint were recomputed
    a_full, h_full = _params(tmp_path / "full")
    a_part, h_part = _params(part)
    import torch
    assert all(torch.equal(a_full[k], a_part[k]) for k in a_full)
    assert all(torch.equal(h_full[k], h_part[k]) for k in h_full)


def test_same_seed_in_two_processes_saves_identical_files(tmp_path):
    """STOP 3 review #2: the seed is set before the model is built; saved files reproduce across processes."""
    args = ["toy", "--tiny", "--family", "kev", "--allow-placeholders", "--steps", "2", "--examples", "16", "--seed", "3"]
    run(*args, "--run-dir", str(tmp_path / "a"))
    run(*args, "--run-dir", str(tmp_path / "b"))
    ma = json.loads((tmp_path / "a" / "manifest.json").read_text())["model_files_sha256"]
    mb = json.loads((tmp_path / "b" / "manifest.json").read_text())["model_files_sha256"]
    for f in ("adapter/adapter_model.safetensors", "heads.safetensors"):
        assert ma[f] == mb[f]
    # the tiny stand-in base lives in each run dir, so only its path differs (real runs share one base path)
    ca, cb = (json.loads((tmp_path / x / "saved/adapter/adapter_config.json").read_text()) for x in "ab")
    ca.pop("base_model_name_or_path"), cb.pop("base_model_name_or_path")
    assert ca == cb and ca["target_modules"] == sorted(ca["target_modules"])
