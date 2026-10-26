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


def test_check_config_lists_placeholders_and_real_runs_refuse_them(tmp_path):
    res = run("--check-config", check=False)
    assert res.returncode == 1 and "TODO_VERIFY" not in res.stderr
    assert "bases.kev-0.8b.local_path" in json.loads(res.stdout)["placeholders"]
    res = run("spike", "--base", "kev-0.8b", "--run-dir", str(tmp_path / "x"), check=False)
    assert res.returncode == 2 and "TODO_VERIFY" in res.stderr
    res = run("spike", "--base", "kev-0.8b", "--allow-placeholders", "--run-dir", str(tmp_path / "x"), check=False)
    assert res.returncode == 2 and "--tiny dry runs only" in res.stderr


def test_later_phases_refuse(tmp_path):
    for cmd in ("sft", "a6", "rb"):
        res = run(cmd, "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir", str(tmp_path), check=False)
        assert res.returncode == 2 and "STOP" in res.stderr


def test_evidence_runs_need_their_authorization_note(tmp_path):
    res = run("e0", "--tiny", "--family", "kev", "--allow-placeholders", "--run-dir", str(tmp_path), check=False)
    assert res.returncode == 0 or "STOP" not in res.stderr  # --tiny is DRYRUN: no note needed
    from r1.c3.train import run as R
    if R.authorization_note("p3a") is None:
        res = run("e0", "--base", "kev-0.8b", "--evidence", "EVIDENCE", "--run-dir", str(tmp_path / "y"), check=False)
        assert res.returncode == 2


@pytest.mark.parametrize("family", ["kev", "qwen_control"])
def test_toy_batch_e0_and_probes_dry_run(tmp_path, family):
    run("toy", "--tiny", "--family", family, "--allow-placeholders", "--run-dir", str(tmp_path / "toy"),
        "--steps", "6", "--examples", "16")
    rep = json.loads((tmp_path / "toy" / "report.json").read_text())
    man = json.loads((tmp_path / "toy" / "manifest.json").read_text())
    assert rep["reload_identical"] and rep["completed"]
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
    args = ["toy", "--tiny", "--family", "kev", "--allow-placeholders", "--steps", "16", "--examples", "32"]
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
    assert killed_at < 16
    run(*args, "--run-dir", str(part))
    steps = [json.loads(l)["step"] for l in (part / "toy" / "metrics.jsonl").read_text().splitlines()
             if json.loads(l)["kind"] == "step"]
    resumed = steps[steps.index(killed_at) + 1:] if killed_at in steps else steps
    assert resumed[resumed.index(killed_at + 1):] == list(range(killed_at + 1, 17))  # resumed after the checkpoint
    a_full, h_full = _params(tmp_path / "full")
    a_part, h_part = _params(part)
    import torch
    assert all(torch.equal(a_full[k], a_part[k]) for k in a_full)
    assert all(torch.equal(h_full[k], h_part[k]) for k in h_full)
