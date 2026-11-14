"""M4 step 4: the DTQ tool against the fake llama-server and a fake nvidia-smi (no GPU, no LLM).

AI-assisted (Claude); ENGINEERING_ONLY / DRYRUN. Needs the harness (``AR_HARNESS_ROOT``) because the request body
is the harness's own (``r1.tracks.probes.determinism.chat_payload``).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from r1.scripts import dt_dualcard_qualify as dtq
from r1.scripts import llama_server_instance as lsi

REPO = Path(__file__).resolve().parents[2]
FAKE = REPO / "r1/scripts/c3_fake_llama_server.py"
U1, U2 = "GPU-11111111-aaaa", "GPU-22222222-bbbb"


def _harness_or_skip():
    try:
        from r1.harness import import_harness
        import_harness()
        import langchain_core  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"harness not importable: {exc}")


def write_prompts(path: Path, n: int, start: int = 0) -> Path:
    rows = [{"prompt": f"Node: digits_mlp\nBudget index (trial number): {i + 2}\nEditable constants:\n"
                       f"  MAX_ITER = {200 + i}\n", "seed": 1000 + i, "source": f"sweep1/fixture/{i}",
             "ledger_sha256": f"{i % 3:064x}", "trial_id": f"t{i}", "instance_seed": 100 + i}
            for i in range(start, start + n)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


@pytest.fixture
def host(tmp_path, monkeypatch):
    root = tmp_path / "dry"
    root.mkdir()
    (root / ".dryrun").write_text("DRYRUN\n")
    monkeypatch.setenv("R1_FAKE_OLLAMA_ROOT", str(root))
    for var in ("C3_FAKE_FAULTS", "C3_FAKE_LLAMA_OFFLOAD", "C3_FAKE_LLAMA_GPU_MIB", "R1_DRYRUN"):
        monkeypatch.delenv(var, raising=False)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, run_name in (("llama-server", "__main__"), ("nvidia-smi", "fake_nvidia_smi")):
        script = bindir / name
        script.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n"
                          f"runpy.run_path({str(FAKE)!r}, run_name={run_name!r})\n")
        script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    model = tmp_path / "models" / "m-Q4_K_M.gguf"
    model.parent.mkdir()
    model.write_bytes(b"GGUF fixture")
    return {"root": root, "binary": bindir / "llama-server", "model": model, "tmp": tmp_path,
            "sha": lsi.sha256_file(model)}


def args(host, out, prompts, *extra):
    return ["--gguf", str(host["model"]), "--gguf-sha256", host["sha"], "--llama-server-bin", str(host["binary"]),
            "--gpu-uuid", U1, "--gpu-uuid", U2, "--prompts", str(prompts), "--calls-per-campaign", "40",
            "--host-label", "DRYRUN", "--out-dir", str(out), "--dry-run", "--start-timeout", "30",
            "--sample-seconds", "0.05", "--runs-per-campaign", "20", "--cpu-seconds-per-run", "30",
            "--workers", "16", *extra]


def test_dry_run_qualifies_on_two_fake_cards(host):
    _harness_or_skip()
    out = host["tmp"] / "out"
    prompts = write_prompts(host["tmp"] / "p.jsonl", 6)
    assert dtq.main(args(host, out, prompts, "--n", "6")) == 0
    rep = json.loads((out / "dtq_report.json").read_text())
    assert rep["status"] == "complete" and rep["label"] == "DRYRUN" and rep["informational"] is True
    srv = rep["server"]
    assert srv["gpu_uuids"] == [U1, U2] and srv["ctx_size"] == 16384
    argv = srv["argv"]
    assert argv[argv.index("--tensor-split") + 1] == "1,1" and "--jinja" in argv and "-lv" in argv
    assert argv[argv.index("--cache-type-k") + 1] == "q8_0" and argv[argv.index("--cache-type-v") + 1] == "q8_0"
    assert json.loads(argv[argv.index("--chat-template-kwargs") + 1]) == {"enable_thinking": False}
    assert rep["offload"]["full"] and rep["offload"]["route"] == "log_line"
    r = rep["replay"]
    assert r["calls"] == 18 and r["errors"] == 0 and r["identity_rate"] == 1.0
    assert r["request_example"]["cache_prompt"] is False and rep["cache_prompt"] is False
    assert r["request_example"]["response_format"]  # manager_proposal/v1
    assert r["completion_tokens"]["n"] == 18
    assert rep["peak_mib_per_card"] == {U1: 5560, U2: 5560}
    days = rep["projection_days"]
    assert days == pytest.approx(288 * 40 * r["latency"]["mean_s"] / 86400 + 288 * 20 * 30 / 16 / 86400)
    assert rep["dtq"]["pass"] is True and rep["prompts"]["overlap"] == 0
    calls = [json.loads(l) for l in (host["root"] / "fake_calls.jsonl").read_text().splitlines()]
    seeds = sorted({c["seed"] for c in calls if c.get("chat_call")})
    assert seeds == list(range(1000, 1006))  # the D26 seeds of the prompt file


def test_overlap_with_an_exam_prompt_set_is_refused(host):
    prompts = write_prompts(host["tmp"] / "p.jsonl", 4)
    exam = host["tmp"] / "exam.jsonl"
    row = json.loads(prompts.read_text().splitlines()[2])
    exam.write_text(json.dumps({"messages": [{"role": "user", "content": "  " + row["prompt"].replace("\n", " \n")}],
                                "ledger_sha256": "f" * 64}) + "\n")
    with pytest.raises(SystemExit, match=r"replay prompts \[2\] occur in an excluded"):
        dtq.load_prompts(str(prompts), 4, [str(exam)])
    # the same ledger (campaign instance) as an exam prompt, with different text, is refused too
    exam.write_text(json.dumps({"prompt": "another context", "ledger_sha256": f"{1:064x}", "trial_id": "x"}) + "\n")
    with pytest.raises(SystemExit, match=r"replay prompts \[1\] come from a ledger"):
        dtq.load_prompts(str(prompts), 4, [str(exam)])
    # an exclude file that cannot be checked is a STOP, not an empty pass
    exam.write_text(json.dumps({"node": "x"}) + "\n")
    with pytest.raises(SystemExit, match="no prompt text"):
        dtq.load_prompts(str(prompts), 4, [str(exam)])
    exam.write_text(json.dumps({"prompt": "unrelated"}) + "\n")
    with pytest.raises(SystemExit, match="no ledger_sha256"):
        dtq.load_prompts(str(prompts), 4, [str(exam)])
    rows, rec = dtq.load_prompts(str(prompts), 3, [])
    assert len(rows) == 3 and rec["overlap"] == 0


@pytest.mark.parametrize("bad,msg", [({"prompt": "x", "seed": 1}, "no source"), ({"prompt": "x", "source": "s"}, "seed"),
                                     ({"prompt": "", "seed": 1, "source": "s"}, "no prompt text"),
                                     ({"prompt": "x", "seed": 1, "source": "s", "trial_id": "t"}, "ledger_sha256"),
                                     ({"prompt": "x", "seed": 1, "source": "s", "trial_id": "t",
                                       "ledger_sha256": "a" * 64}, "instance_seed")])
def test_prompt_rows_need_text_seed_and_source(tmp_path, bad, msg):
    p = tmp_path / "p.jsonl"
    p.write_text(json.dumps(bad) + "\n")
    with pytest.raises(SystemExit, match=msg):
        dtq.load_prompts(str(p), 1, [])


def test_too_few_and_duplicate_prompts_are_refused(tmp_path):
    p = write_prompts(tmp_path / "p.jsonl", 2)
    with pytest.raises(SystemExit, match="3 are needed"):
        dtq.load_prompts(str(p), 3, [])
    lines = p.read_text().splitlines()
    p.write_text(lines[0] + "\n" + lines[0] + "\n")
    with pytest.raises(SystemExit, match="duplicate"):
        dtq.load_prompts(str(p), 2, [])


def test_co_tenant_at_start_stops_before_any_server(host):
    other = host["root"] / "gpu_apps"
    other.mkdir()
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        (other / f"{sleeper.pid}.csv").write_text(f"{sleeper.pid}, {U2}, 900\n")
        out = host["tmp"] / "out"
        assert dtq.main(args(host, out, write_prompts(host["tmp"] / "p.jsonl", 3), "--n", "3")) == 2
        rep = json.loads((out / "dtq_report.json").read_text())
        assert rep["status"] == "STOP_co_tenant_at_start" and rep["co_tenants"][0]["pid"] == sleeper.pid
        assert "server" not in rep and not (out / "server").exists()
    finally:
        sleeper.kill()
        sleeper.wait()


def test_partial_offload_is_a_recorded_result(host, monkeypatch):
    _harness_or_skip()
    monkeypatch.setenv("C3_FAKE_LLAMA_OFFLOAD", "20")
    out = host["tmp"] / "out"
    assert dtq.main(args(host, out, write_prompts(host["tmp"] / "p.jsonl", 3), "--n", "3")) == 0
    rep = json.loads((out / "dtq_report.json").read_text())
    assert rep["status"] == "offload_not_full" and rep["dtq"]["pass"] is False and "replay" not in rep
    assert rep["server_stop"] is not None


def test_server_start_failure_is_a_recorded_result(host, tmp_path):
    bad = tmp_path / "bin" / "llama-server-oom"
    bad.write_text("#!/bin/sh\n[ \"$1\" = --version ] && { echo 'version: 0 (DRYRUN)' >&2; exit 0; }\n"
                   "echo 'ggml_backend_cuda_buffer_type_alloc_buffer: allocating 9000.00 MiB on device 1: "
                   "cudaMalloc failed: out of memory'\nexit 1\n")
    bad.chmod(0o755)
    out = tmp_path / "out"
    argv = args(host, out, write_prompts(tmp_path / "p.jsonl", 3), "--n", "3")
    argv[argv.index("--llama-server-bin") + 1] = str(bad)
    assert dtq.main(argv) == 0
    rep = json.loads((out / "dtq_report.json").read_text())
    assert rep["status"] == "server_start_failed" and "out of memory" in "\n".join(rep["server_log_tail"])
    assert rep["dtq"]["pass"] is False


def test_sha_mismatch_and_existing_out_dir_are_refused(host):
    prompts = write_prompts(host["tmp"] / "p.jsonl", 3)
    argv = args(host, host["tmp"] / "o1", prompts, "--n", "3")
    argv[argv.index("--gguf-sha256") + 1] = "0" * 64
    with pytest.raises(SystemExit, match="differs from the registry"):
        dtq.main(argv)
    (host["tmp"] / "o2").mkdir()
    with pytest.raises(SystemExit, match="exists"):
        dtq.main(args(host, host["tmp"] / "o2", prompts, "--n", "3"))


def test_exclude_prompts_required_outside_dry_run(host):
    argv = [a for a in args(host, host["tmp"] / "o", write_prompts(host["tmp"] / "p.jsonl", 3)) if a != "--dry-run"]
    with pytest.raises(SystemExit):
        dtq.main(argv)


def test_evaluate_and_projection():
    pr = dtq.projection(3.0, 288, 40, 20, 30.0, 16)
    assert pr["llm_days"] == pytest.approx(0.4) and pr["cpu_days"] == pytest.approx(288 * 20 * 30 / 16 / 86400)
    assert pr["days"] == pytest.approx(pr["llm_days"] + pr["cpu_days"])
    assert dtq.projection(3.0, 288, 40, None, 30.0, 16)["days"] is None      # CPU term unknown: unevaluated
    assert dtq.projection(None, 288, 40, 20, 30.0, 16)["days"] is None
    full = {"full": True}
    assert dtq.evaluate(full, 1.0, 4.0)["pass"] is True
    assert dtq.evaluate(full, 1.0, None)["pass"] is None                      # never judged on the LLM term alone
    assert dtq.evaluate(full, 0.98, None)["pass"] is False
    assert dtq.evaluate(full, 0.98, 1.0)["pass"] is False
    assert dtq.evaluate(full, 1.0, 4.01)["pass"] is False
    assert dtq.evaluate({"full": False}, 1.0, 1.0)["pass"] is False
    assert dtq.evaluate(full, 1.0, 1.0, stop=True)["pass"] is False


def test_memory_sampler_tracks_the_peak_and_flags_intruders():
    seq = iter([[{"pid": 7, "gpu_uuid": U1, "used_mib": 100}, {"pid": 7, "gpu_uuid": U2, "used_mib": 90}],
                None,
                [{"pid": 7, "gpu_uuid": U1, "used_mib": 300}, {"pid": 9, "gpu_uuid": U2, "used_mib": 5}]])
    s = dtq.MemorySampler([U1, U2], 7, apps_fn=lambda: next(seq))
    for _ in range(3):
        s.sample()
    assert s.peak == {U1: 300, U2: 90} and s.samples == 2 and s.unread == 1
    assert s.intruders == [{"pid": 9, "gpu_uuid": U2, "used_mib": 5}] and s.abort.is_set()


def test_intruder_during_the_run_aborts_the_replay_and_never_passes(host, monkeypatch):
    _harness_or_skip()
    apps = host["root"] / "gpu_apps"
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    real_post = dtq.post
    n = {"calls": 0}

    def post(url, payload, timeout):
        n["calls"] += 1
        if n["calls"] == 2:   # a co-tenant appears on card 2 after the second call
            (apps / f"{sleeper.pid}.csv").write_text(f"{sleeper.pid}, {U2}, 900\n")
            import time
            time.sleep(0.3)   # several sampler intervals
        return real_post(url, payload, timeout)

    monkeypatch.setattr(dtq, "post", post)
    try:
        out = host["tmp"] / "out"
        assert dtq.main(args(host, out, write_prompts(host["tmp"] / "p.jsonl", 6), "--n", "6")) == 2
        rep = json.loads((out / "dtq_report.json").read_text())
        assert rep["status"] == "STOP_co_tenant_during_run" and rep["dtq"]["pass"] is False and rep["dtq"]["stop"]
        assert rep["replay"]["aborted_at_call"] is not None and rep["replay"]["calls"] < 18
        assert any(c["pid"] == sleeper.pid for c in rep["co_tenants"])
        assert "projection" not in rep
    finally:
        sleeper.kill()
        sleeper.wait()


def test_unknown_cpu_term_leaves_the_criterion_unevaluated(host):
    _harness_or_skip()
    out = host["tmp"] / "out"
    argv = args(host, out, write_prompts(host["tmp"] / "p.jsonl", 3), "--n", "3")
    i = argv.index("--workers")
    del argv[i:i + 2]
    assert dtq.main(argv) == 0
    rep = json.loads((out / "dtq_report.json").read_text())
    assert rep["status"] == "complete" and rep["projection"]["days"] is None and rep["dtq"]["pass"] is None
    assert rep["projection"]["llm_days"] > 0


def test_real_run_holds_n_and_repeats_at_50_and_3(host):
    argv = [a for a in args(host, host["tmp"] / "o", write_prompts(host["tmp"] / "p.jsonl", 50), "--n", "6")
            if a != "--dry-run"] + ["--exclude-prompts", str(host["tmp"] / "p.jsonl")]
    with pytest.raises(SystemExit):
        dtq.main(argv)


def test_probe_file_is_byte_identical_to_d10b05b7():
    try:
        blob = subprocess.run(["git", "-C", str(REPO), "rev-parse", "d10b05b7:r1/tracks/probes/determinism.py"],
                              capture_output=True, text=True, check=True).stdout.strip()
        here = subprocess.run(["git", "-C", str(REPO), "hash-object", "r1/tracks/probes/determinism.py"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pytest.fail("d10b05b7 not available for the byte-identity check")
    assert here == blob


@pytest.mark.parametrize("field,value", [("seed", 9001), ("seed", 9210), ("instance_seed", 9104), ("audit_seed", 9205)])
def test_seeds_in_the_exam_range_are_refused(tmp_path, field, value):
    p = write_prompts(tmp_path / "p.jsonl", 3)
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    rows[1][field] = value
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(SystemExit, match=r"prompt row 1 has .*exam seed range 9001-9210"):
        dtq.load_prompts(str(p), 3, [])


@pytest.mark.parametrize("value", [9000, 9211])
def test_seeds_just_outside_the_exam_range_pass(tmp_path, value):
    p = write_prompts(tmp_path / "p.jsonl", 2)
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    rows[0]["seed"] = value
    rows[1]["instance_seed"] = value
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert len(dtq.load_prompts(str(p), 2, [])[0]) == 2
