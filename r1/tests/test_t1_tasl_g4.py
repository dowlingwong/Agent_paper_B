"""G.4 on the TASL pair (sweep2/t1_tasl/g4_tasl.py): spec, the proposer server record, the worker job with fake host
tools and a fake server, the timing STOP, seal and read, the date recompute with one slot, and the note.

Synthetic only: no GPU, no network, no llama-server (Popen, urlopen, nvidia-smi and the engine are replaced).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g4_tasl as T  # noqa: E402
import g1b_tasl as G  # noqa: E402

SPEC_PATH = ROOT / "sweep2" / "t1_tasl" / "g4_tasl_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())
HOST_REPORT = (f"host_check_host: host-TASL-2\nhost_check_harness_commit: {SPEC['harness']['commit']}\n"
               "host_check_items: 1-7 PASS\nhost_check_verdict: PASS\n")
PARAMS = json.loads((ROOT / "sweep2" / "t1_tasl" / "g4_tasl_dates_params.json").read_text())
UUID2 = "GPU-11111111-2222-3333-4444-555555555555"
UUID7 = "GPU-77777777-2222-3333-4444-555555555555"
BUILD = "0.7.0-dev (build 1234, commit abcdef0)"
PROPS_BUILD = "b1234-abcdef0"           # what llama.cpp's /props reports for that --version line
TS = "100.101.102.103"


@pytest.fixture
def g1b_filled(monkeypatch):
    g = json.loads((ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_spec.json").read_text())
    g["hosts"]["TASL-2"].update(hostname="host-TASL-2", gpu_uuid=UUID2)
    monkeypatch.setattr(T, "g1b_spec", lambda: g)
    return g


def launch_spec(tmp_path: Path) -> dict:
    spec = copy.deepcopy(SPEC)
    spec["paper"]["commit"] = "2" * 40
    w = spec["worker"]
    w.update(hostname="host-TASL-2", gpu_uuid=UUID2)
    for key in ("base", "harness_dir", "runs_root", "sealed_root"):
        w[key] = str(tmp_path / "w" / key)
    w["isolation_host_check"] = {"record": "docs/r1/reports/TASL-2_check.md",
                                 "sha256": hashlib.sha256(HOST_REPORT.encode()).hexdigest()}
    p = spec["proposer"]
    p.update(hostname="host-TASL-7", gpu_uuid=UUID7, tailscale_address=TS, server_url=f"http://{TS}:8080",
             binary_sha256="4" * 64, bin_dir_manifest_sha256="5" * 64, expected_build=BUILD,
             run_dir=str(tmp_path / "p" / "run"))
    spec["timeout_decision"]["authority"] = "R1-G1B-TIMEOUT (21 Nov)"
    spec["host_decision"]["authority"] = "R1-T1-TASL-ENV (21 Nov)"
    return spec


def test_shipped_spec_validates_and_refuses_launch(g1b_filled):
    assert T.validate_spec(copy.deepcopy(SPEC) | {"worker": SPEC["worker"] | {"hostname": "host-TASL-2",
                                                                              "gpu_uuid": UUID2}})["projection"]
    with pytest.raises(T.Stop):
        T.validate_spec(copy.deepcopy(SPEC), launch=True)


@pytest.mark.parametrize("edit, match", [
    (lambda s: s["proposer"].update(server_url="http://10.0.0.5:8080"), "Tailscale address"),
    (lambda s: s["proposer"].update(server_url=f"https://{TS}:8080"), "http://"),
    (lambda s: s["proposer"].update(server_url="http://100.64.0.9:8080"), "proposer.tailscale_address"),
    (lambda s: s["proposer"].update(args=s["proposer"]["args"][:-1]), "exam settings"),
    (lambda s: s["proposer"].update(model_path="/x/other.gguf"), "GGUF file name"),
    (lambda s: s["worker"].update(gpu_uuid=UUID7), "RTX 4090 of g1b_tasl_spec.json"),
    (lambda s: s["worker"].update(host="TASL-7"), "worker.host"),
    (lambda s: s["pilot"].update(cache_prompt=True), "cache_prompt false"),
    (lambda s: s["nodes"][2].update(node="mlab_imdb"), "pilot nodes"),
    (lambda s: s["nodes"][0].update(run_seconds=11.0), "differs from g1b_tasl_spec.json"),
    (lambda s: s["timeout_decision"].update(basis="census_baseline_x3"), "equal the G.1b basis"),
    (lambda s: s["worker"]["env_python"].pop("jax312"), "jax312 on TASL-2"),
    (lambda s: s["host_decision"].update(authority="TODO"), "R1-T1-TASL-ENV"),
])
def test_spec_refusals(tmp_path, g1b_filled, edit, match):
    spec = launch_spec(tmp_path)
    T.validate_spec(spec, launch=True)
    edit(spec)
    with pytest.raises(T.Stop, match=match):
        T.validate_spec(spec, launch=True)


def test_pilot_file_uses_the_remote_server_and_the_table_timeout_basis(tmp_path, g1b_filled):
    spec = launch_spec(tmp_path)
    pf = T.pilot_file(spec, T.node_entry(spec, "mlab_cifar10"), interpreter="/py", cgroup_parent="/sys/fs/cgroup/s")
    assert pf["base_url"] == f"http://{TS}:8080" and pf["extra_payload"] == {"cache_prompt": False}
    assert pf["measured_run_seconds"] == 13.347 and pf["isolation_waivers"] == {}


# ---------------------------------------------------------------------------------------------- proposer
class Proc:
    pid = 4242

    def wait(self):
        return 0

    def terminate(self):
        pass


def test_serve_checks_binary_model_build_and_writes_the_record(tmp_path, g1b_filled, monkeypatch):
    spec = launch_spec(tmp_path)
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec))
    monkeypatch.setattr(T.socket, "gethostname", lambda: "host-TASL-7")
    monkeypatch.setattr(T.os.path, "expanduser", lambda p: str(tmp_path / "home" / p.lstrip("~/")))

    def smi(argv, **kw):
        if argv[-1] == "--version":
            assert "LD_LIBRARY_PATH" not in kw["env"]
            return subprocess.CompletedProcess(argv, 0, "", f"ggml_cuda_init: ...\nversion: {BUILD}\nbuilt with x\n")
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[0] == "ldd":
            assert "LD_LIBRARY_PATH" not in kw["env"] and "LD_PRELOAD" not in kw["env"]
            lib_dir = Path(spec["proposer"]["binary"]).parent
            return subprocess.CompletedProcess(argv, 0, f"\tlibggml-cuda.so.0 => {lib_dir}/libggml-cuda.so.0 (0x1)\n"
                                                        "\tlibcudart.so.12 => /usr/lib/libcudart.so.12 (0x2)\n", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID7}, NVIDIA GeForce RTX 4090, 1, 2\n", "")
    manifest = lambda d: ("abc  llama-server\n", "5" * 64)  # noqa: E731
    shas = {spec["proposer"]["binary"]: "4" * 64, spec["proposer"]["model_path"]: T.MODEL["sha256"]}
    seen = {}
    monkeypatch.setenv("LD_LIBRARY_PATH", "/stray/lib")
    rec = T.serve(sp, smi=smi, popen=lambda argv, **kw: seen.update(argv=argv, env=kw["env"]) or Proc(),
                  sha=lambda p: shas[str(p)], manifest=manifest, wait=False)
    assert rec["ldd"] and rec["bin_dir_manifest_sha256"] == "5" * 64 and "LD_LIBRARY_PATH" not in seen["env"]
    assert rec["server_env"]["LD_LIBRARY_PATH"] is None
    assert seen["argv"][-4:] == ["--host", TS, "--port", "8080"] and "-np" in seen["argv"]
    assert rec["build"] == f"version: {BUILD}" and rec["pid"] == 4242
    raw = (Path(spec["proposer"]["run_dir"]) / spec["run_id"] / "server-1" / "server_record.json").read_bytes()
    assert rec["server_dir"].endswith("/server-1")
    assert T.check_server_record(spec, raw, G.L._sha_file(sp))["pid"] == 4242
    with pytest.raises(T.Stop, match="does not match"):
        T.check_server_record(spec, raw, "0" * 64)
    shas[spec["proposer"]["model_path"]] = "9" * 64
    spec["run_id"] = "g4-tasl-other"
    sp.write_text(json.dumps(spec))
    with pytest.raises(T.Stop, match="GGUF sha256"):
        T.serve(sp, smi=smi, popen=lambda argv, **kw: Proc(), sha=lambda p: shas[str(p)], manifest=manifest,
                wait=False)
    spec["run_id"] = "g4-tasl-other2"
    sp.write_text(json.dumps(spec))
    with pytest.raises(T.Stop, match="build directory differs"):
        T.serve(sp, smi=smi, popen=lambda argv, **kw: Proc(), sha=lambda p: shas[str(p)],
                manifest=lambda d: ("x\n", "6" * 64), wait=False)
    # B1 (G.4 review): a refused serve writes only a refusal; once the cause is gone, serve starts (a new server-N)
    import fcntl
    shas[spec["proposer"]["model_path"]] = T.MODEL["sha256"]
    run_root = Path(spec["proposer"]["run_dir"]) / spec["run_id"]
    assert not list(run_root.glob("server-*")) and len(list((run_root / "_refusals").iterdir())) == 1
    lease = Path(T.os.path.expanduser(spec["proposer"]["lease"]))
    holder = lease.open("a+")
    fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with pytest.raises(T.Stop, match="held by another job"):
        T.serve(sp, smi=smi, popen=lambda argv, **kw: Proc(), sha=lambda p: shas[str(p)], manifest=manifest,
                wait=False)
    fcntl.flock(holder, fcntl.LOCK_UN)
    holder.close()
    assert not list(run_root.glob("server-*")) and len(list((run_root / "_refusals").iterdir())) == 2
    first = T.serve(sp, smi=smi, popen=lambda argv, **kw: Proc(), sha=lambda p: shas[str(p)], manifest=manifest,
                    wait=False)
    again = T.serve(sp, smi=smi, popen=lambda argv, **kw: Proc(), sha=lambda p: shas[str(p)], manifest=manifest,
                    wait=False)
    assert first["server_dir"].endswith("/server-1") and again["server_dir"].endswith("/server-2")


def test_bin_manifest_covers_files_and_links(tmp_path):
    d = tmp_path / "bin"
    d.mkdir()
    (d / "llama-server").write_bytes(b"exe")
    (d / "libggml-cuda.so.0").write_bytes(b"lib")
    (d / "libggml-cuda.so").symlink_to("libggml-cuda.so.0")
    text, digest = T.bin_manifest(d)
    assert "link  libggml-cuda.so -> libggml-cuda.so.0" in text and digest == hashlib.sha256(text.encode()).hexdigest()
    (d / "libggml-cuda.so.0").write_bytes(b"other")
    assert T.bin_manifest(d)[1] != digest
    (d / "sub").mkdir()
    with pytest.raises(T.Stop, match="not a regular file"):
        T.bin_manifest(d)


def test_llama_libraries_must_resolve_inside_the_build_directory(tmp_path):
    lines = [f"\tlibllama.so => {tmp_path}/libllama.so (0x1)", "\tlibggml-cuda.so => /usr/local/lib/libggml-cuda.so (0x2)",
             "\tlibcudart.so.12 => /usr/lib/libcudart.so.12 (0x3)", "\tlinux-vdso.so.1 (0x4)"]
    assert T.ldd_outside(lines, tmp_path) == ["libggml-cuda.so => /usr/local/lib/libggml-cuda.so"]


def test_props_build_is_the_llama_cpp_form():
    assert T.props_build("0.7.0-dev (build 1, commit 620d222)") == "b1-620d222"
    assert T.props_build("0.7.0-dev (build 11669, commit 620d2225c)") == "b11669-620d2225c"
    with pytest.raises(T.Stop):
        T.props_build("1234 (abcdef0)")


# ---------------------------------------------------------------------------------------------- worker
class Server:
    def __init__(self, props=None, status=200):
        self.props = props or {"default_generation_settings": {"n_ctx": 32768}, "total_slots": 1, "build_info": PROPS_BUILD,
                               "model_path": "/m/google_gemma-4-31B-it-Q4_K_M.gguf"}
        self.status = status

    def __call__(self, url, timeout=10.0):
        if url.endswith("/health"):
            return self.status, b'{"status":"ok"}'
        return self.status, json.dumps(self.props).encode()


def test_server_identity_and_latency(tmp_path, g1b_filled):
    spec = launch_spec(tmp_path)
    assert T.server_identity(spec, Server())["n_ctx"] == 32768
    for change, match in (({"total_slots": 4}, "total_slots"), ({"build_info": "other"}, "build_info"),
                          ({"default_generation_settings": {"n_ctx": 8192}}, "n_ctx")):
        with pytest.raises(T.Stop, match=match):
            T.server_identity(spec, Server(Server().props | change))
    ticks = iter(x * 0.01 for x in range(100))
    probe = T.latency_probe(spec, n=5, get=Server(), clock=lambda: next(ticks))
    assert probe["n"] == 5 and probe["median_ms"] == pytest.approx(10.0)


def _ledgers(out: Path, n_calls=20, run_s=10.0):
    for i in (1, 2, 3):
        d = out / f"instance_{i}"
        d.mkdir(parents=True)
        lines = [json.dumps({"step": k, "decision": "kept", "manager_call": {"usage": {"wall_seconds": 30.0 + k}}})
                 for k in range(1, n_calls + 1)]
        (d / "campaign_ledger.jsonl").write_text("\n".join(lines) + "\n")
    summary = {"node": None, "proposals": 60, "seconds": {"llm_median": 40.0, "run_median": run_s,
                                                          "campaign_wall_total": 3600.0},
               "rates": {"ran_of_proposals": 0.6, "kept_of_ran": 0.2},
               "fit": {"cache_prompt_false_on_every_call": True, "all_fit_ctx": True},
               "diff_liveness": {"ran_of_valid": 0.7}, "cross_instance_duplicates": {"groups": 0,
                                                                                      "ran_proposals_in_groups": 0}}
    return summary


@pytest.fixture
def worker(tmp_path, g1b_filled, monkeypatch):
    spec = launch_spec(tmp_path)
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec))
    monkeypatch.setattr(T.os.path, "expanduser", lambda p: str(tmp_path / "home" / p.lstrip("~/")))
    monkeypatch.setattr(G, "host_identity", lambda s, h: {"host": h})
    monkeypatch.setattr(G, "ptrace_scope", lambda: 1)
    monkeypatch.setattr(G, "scope_cgroup", lambda: {"cgroup_parent": "/sys/fs/cgroup/scope"})
    monkeypatch.setattr(G, "harness_checkout", lambda s, h: {"commit": s["harness"]["commit"]})
    monkeypatch.setattr(G, "environment", lambda s, h, n: {"name": n["env"]})
    monkeypatch.setattr(G, "check_affinity", lambda s, n, affinity=None: list(range(8)))
    monkeypatch.setattr(os, "environ", dict(os.environ))
    # a server record as serve() writes it
    rec = {"schema": T.SERVER_RECORD_SCHEMA, "run_id": spec["run_id"], "host": "TASL-7", "hostname": "host-TASL-7",
           "server_url": spec["proposer"]["server_url"], "spec_sha256": G.L._sha_file(sp),
           "binary_sha256": "4" * 64, "bin_dir_manifest_sha256": "5" * 64, "model_sha256": T.MODEL["sha256"],
           "build": f"version: {BUILD}",
           "argv": T.server_argv(spec, 8080), "gpu": {"uuid": UUID7, "name": T.GPU_MODEL}, "pid": 7}
    srv = tmp_path / "server_record.json"
    srv.write_text(json.dumps(rec))
    state = {"run_s": 10.0, "calls": []}

    def engine(argv, **kw):
        state["calls"].append(argv)
        out = Path(argv[argv.index("--out") + 1])
        summary = _ledgers(out, run_s=state["run_s"])
        summary["node"] = json.loads(Path(argv[argv.index("--pilot") + 1]).read_text())["node"]
        (out / "pilot_summary.json").write_text(json.dumps(summary))
        return subprocess.CompletedProcess(argv, 0, "", "")

    def smi(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 1, 2\n", "")
    setup = lambda h, n, base, out: {"data_root": str(base / "data")}  # noqa: E731
    return spec, sp, srv, state, engine, smi, setup


def test_worker_job_end_to_end_seal_and_dates(worker, tmp_path):
    spec, sp, srv, state, engine, smi, setup = worker
    sealed = []
    for name in ("mlab_cifar10", "mlgym_fmnist", "mlgym_breakout_minatar"):
        rec = T.run_node_job(sp, name, srv, smi=smi, engine=engine, setup=setup, get=Server())
        assert rec["stop"] is None and rec["call_latency"]["n"] == 60 and rec["latency_probe_before"]["n"] == 20
        assert state["calls"][-1][-2:] == ["--gpu-uuid", UUID2]
        job = Path(spec["worker"]["runs_root"]) / spec["run_id"] / name / "attempt-1"
        receipt = T.seal(job, spec, name)
        assert receipt["server_record_json_sha256"]
        sealed.append(Path(receipt["sealed_path"]))
    summaries = {s["node"]: s for s in (T.read_sealed_summary(p, spec, G.L._sha_file(sp)) for p in sealed)}
    params = PARAMS | {"pilot_nodes": list(summaries)}
    got = T.recompute_dates(summaries, params, today=date(2026, 11, 21))
    assert got["concurrent_worker_slots"] == 1 and got["gpu_model"] == T.GPU_MODEL
    assert "rtx4090_over_census_run_ratio" in got and "h200_over_census_run_ratio" not in got
    assert "mlgym_houseprice" in got["g5_by_K"]["10"]["per_node"]
    with pytest.raises(T.Stop, match="one concurrent"):
        T.recompute_dates(summaries, params | {"concurrent_h200_slots": 4}, today=date(2026, 11, 21))


def test_worker_stops(worker, tmp_path):
    spec, sp, srv, state, engine, smi, setup = worker
    state["run_s"] = 20.0                         # above the cifar10 basis 13.347 s
    with pytest.raises(T.Stop, match="exceeds the declared timeout basis"):
        T.run_node_job(sp, "mlab_cifar10", srv, smi=smi, engine=engine, setup=setup, get=Server())
    rec = json.loads((Path(spec["worker"]["runs_root"]) / spec["run_id"] / "mlab_cifar10" / "attempt-1" /
                      "job_record.json").read_text())
    assert rec["stop_class"] == "timing"
    with pytest.raises(T.Stop, match="no new attempt"):
        T.run_node_job(sp, "mlab_cifar10", srv, smi=smi, engine=engine, setup=setup, get=Server())
    state["run_s"] = 10.0
    with pytest.raises(T.Stop, match="/props differ"):
        T.run_node_job(sp, "mlgym_fmnist", srv, smi=smi, engine=engine, setup=setup,
                       get=Server(Server().props | {"total_slots": 2}))
    run_root = Path(spec["worker"]["runs_root"]) / spec["run_id"]
    assert not (run_root / "mlgym_fmnist").exists() and list((run_root / "_refusals").iterdir())   # refused before
    rec = T.run_node_job(sp, "mlgym_fmnist", srv, smi=smi, engine=engine, setup=setup, get=Server())
    assert rec["attempt"] == 1
    flip = {"n": 0}

    def changing(url, timeout=10.0):
        if url.endswith("/props"):
            flip["n"] += 1
            if flip["n"] > 1:
                return 200, json.dumps(Server().props | {"build_info": "x"}).encode()
        return Server()(url)
    with pytest.raises(T.Stop, match="differ from the declared server"):
        T.run_node_job(sp, "mlgym_breakout_minatar", srv, smi=smi, engine=engine, setup=setup, get=changing)


def test_launch_and_note(worker, tmp_path, monkeypatch):
    spec, sp, srv, state, engine, smi, setup = worker
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True)
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none",
              "paper_commit": spec["paper"]["commit"], "spec_sha256": G.L._sha_file(sp),
              "P1": "PASS — R1-T1-HOST-TASL; docs/r1/reports/TASL-2_check.md", "P2": "PASS — R1-TRACKG-G3-EARLY",
              "P3": "PASS — docs/r1/authorizations/g1b_t1_tasl_20261121.md; TASL-7 jobs sealed",
              "P4": "PASS — docs/r1/reviews/x.md", "P5": "PASS — R1-T1-TASL-ENV",
              "run_id": spec["run_id"], "harness_commit": spec["harness"]["commit"]}
    note = d / "g4_t1_tasl_20991231.md"
    note.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    yes = lambda rel, raw: True  # noqa: E731
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    review = {"docs/r1/reviews/x.md": b"review"}.get
    with pytest.raises(T.Stop, match="disabled"):
        T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main=review)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    rows = []
    reports = {"docs/r1/reports/TASL-2_check.md": HOST_REPORT.encode(), "docs/r1/reviews/x.md": b"review"}
    out = T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main=reports.get,
                   launch_binding=lambda r, s, rw: rows.append(rw) or {"ok": 1}, runner=lambda *a: {"x": 1})
    with pytest.raises(T.Stop, match="not on published main"):
        T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main=review,
                 launch_binding=lambda *a: {}, runner=lambda *a: {})          # the review is there, the host check not
    assert out["launch"] == {"ok": 1} and "R1-T1-HOST-TASL" in rows[0]
    good = note.read_text()
    with pytest.raises(T.Stop, match="P4 must name review files on origin/main"):
        T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main={**reports,
                 "docs/r1/reviews/x.md": None}.get, launch_binding=lambda *a: {}, runner=lambda *a: {})
    for old, new, match in (("P5: PASS — R1-T1-TASL-ENV", "P5: PASS — none", "P5"),
                            ("P4: PASS — docs/r1/reviews/x.md", "P4: PASS — docs/r1/reviews/<the review>.md",
                             "placeholder"),
                            ("P3: PASS — docs/r1/authorizations/g1b_t1_tasl_20261121.md", "P3: PASS — G1B", "P3"),
                            (f"run_id: {spec['run_id']}", "run_id: g4-tasl-x", "run_id"),
                            (f"harness_commit: {spec['harness']['commit']}", "harness_commit: " + "0" * 40,
                             "harness_commit")):
        note.write_text(good.replace(old, new))
        with pytest.raises(T.Stop, match=match):
            T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes)
    note.write_text(good)
    # the default binding is the TASL one (verify_launch_tasl with the spec path), never g1b_lib.verify_launch
    seen = {}
    monkeypatch.setattr(G, "verify_launch_tasl", lambda repo, s, r, *, spec_path: seen.update(
        rows=r, spec_path=spec_path, run_id=s["run_id"]) or {"tasl": 1})
    monkeypatch.setattr(G.L, "verify_launch", lambda *a, **k: pytest.fail("g1b_lib.verify_launch must not be used"))
    out = T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main=reports.get,
                   runner=lambda *a: {"x": 1})
    assert out["launch"]["tasl"] == 1 and seen == {"rows": T.PLAN_ROWS, "spec_path": sp, "run_id": spec["run_id"]}
    assert out["launch"]["imports"]["g1b_tasl"] == "sweep2/t1_tasl/g1b_tasl.py"
    # the keys are checked before the binding: no binding call without both keys
    monkeypatch.delenv(T.ENABLE_ENV)
    calls = []
    with pytest.raises(T.Stop, match="disabled"):
        T.launch(sp, note, "mlab_cifar10", srv, enable=True, on_main=yes, read_main=reports.get,
                 launch_binding=lambda *a: calls.append(a) or {}, runner=lambda *a: {})
    assert calls == []


def test_serve_is_gated_like_run_node(worker, tmp_path, monkeypatch):
    """``serve`` needs the same signed note (run_id, harness commit), both keys and the TASL launch binding before
    the GPU lease is taken; nothing is served when any of them fails."""
    spec, sp, srv, *_ = worker
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none",
              "paper_commit": spec["paper"]["commit"], "spec_sha256": G.L._sha_file(sp),
              "P1": "PASS — R1-T1-HOST-TASL; docs/r1/reports/TASL-2_check.md", "P2": "PASS — R1-TRACKG-G3-EARLY",
              "P3": "PASS — docs/r1/authorizations/g1b_t1_tasl_20261121.md", "P4": "PASS — docs/r1/reviews/x.md",
              "P5": "PASS — R1-T1-TASL-ENV", "run_id": spec["run_id"], "harness_commit": spec["harness"]["commit"]}
    note = d / "g4_t1_tasl_20991230.md"
    note.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    yes = lambda rel, raw: True  # noqa: E731
    served = []
    server = lambda path: served.append(path) or {"pid": 1}  # noqa: E731
    main = {"docs/r1/reviews/x.md": b"review"}.get
    import functools
    T_serve_launch = T.serve_launch
    monkeypatch.setattr(T, "serve_launch", functools.partial(T_serve_launch, read_main=main))
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    with pytest.raises(T.Stop, match="disabled"):
        T.serve_launch(sp, note, enable=True, on_main=yes, server=server,
                       launch_binding=lambda *a: pytest.fail("binding before the keys"))
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    with pytest.raises(T.Stop, match="disabled"):
        T.serve_launch(sp, note, enable=False, on_main=yes, server=server, launch_binding=lambda *a: {})
    with pytest.raises(T.Stop, match="not committed byte-identically"):
        T.serve_launch(sp, note, enable=True, on_main=lambda rel, raw: False, server=server,
                       launch_binding=lambda *a: {})

    def refuse(*a):
        raise T.Stop("STOP: fetch published main before launch")
    with pytest.raises(T.Stop, match="fetch published main"):
        T.serve_launch(sp, note, enable=True, on_main=yes, server=server, launch_binding=refuse)
    note.write_text(note.read_text().replace(f"run_id: {spec['run_id']}", "run_id: other"))
    with pytest.raises(T.Stop, match="run_id"):
        T.serve_launch(sp, note, enable=True, on_main=yes, server=server, launch_binding=lambda *a: {})
    assert served == []
    note.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    seen = {}
    monkeypatch.setattr(G, "verify_launch_tasl", lambda repo, s, r, *, spec_path: seen.update(
        rows=r, spec_path=spec_path) or {"tasl": 1})
    out = T.serve_launch(sp, note, enable=True, on_main=yes, server=server)
    assert out["pid"] == 1 and out["launch"]["tasl"] == 1 and served == [sp]
    assert seen == {"rows": T.PLAN_ROWS, "spec_path": sp}
    bad = dict(spec)
    bad["proposer"] = {**spec["proposer"], "binary_sha256": "TODO"}
    bad_path = tmp_path / "bad_spec.json"
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(T.Stop):
        T.serve_launch(bad_path, note, enable=True, on_main=yes, server=server, launch_binding=lambda *a: {})
    assert served == [sp]


def test_import_sources_refuse_a_shadow(monkeypatch, tmp_path):
    """M2 (G.4 review): a module imported from elsewhere than its reviewed source (e.g. a sourceless .pyc earlier on
    sys.path) is refused at launch."""
    assert T.check_import_sources()["g1b_tasl"] == "sweep2/t1_tasl/g1b_tasl.py"
    fake = type(sys)("g1b_tasl")
    fake.__file__ = str(T.REPO_ROOT / "sweep2" / "g4" / "g1b_tasl.pyc")
    monkeypatch.setitem(sys.modules, "g1b_tasl", fake)
    with pytest.raises(T.Stop, match="imported from .*g4/g1b_tasl.pyc"):
        T.check_import_sources()


def test_serve_cli_goes_through_the_gate(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(T, "serve_launch", lambda spec, note, *, enable: calls.append((spec, note, enable)) or {"ok": 1})
    monkeypatch.setattr(T, "serve", lambda *a, **k: pytest.fail("the CLI must not call serve directly"))
    assert T.main(["serve", str(tmp_path / "s.json"), "--note", str(tmp_path / "n.md"), "--enable"]) == 0
    assert calls == [(tmp_path / "s.json", tmp_path / "n.md", True)]


def test_g5_projection_table_and_pre_pilot_dates_for_seven_nodes():
    import g5_projection_tasl as P
    t = P.table()
    row = t["W=manager_calls MEM=one_mode share=0.6 K=10"]
    assert row["gpu_hours"] == pytest.approx(166.9, abs=0.05) and row["audited_per_node"] == 144
    got = T.recompute_dates({}, PARAMS, today=date(2026, 11, 21))
    assert "g5_requested_slot_hours" not in got and got["B7"] == "2026-12-07"
    assert "slot" not in json.dumps(got["g5_by_K"])
    assert len(got["g5_by_K"]["10"]["per_node"]) == 7


DRAFT = ROOT / "docs" / "r1" / "proposals" / "G4_T1_TASL_NOTE_DRAFT_20261121.md"


def test_note_draft_parses_as_check_note_reads_it(tmp_path):
    """Dry check of the G.4 note draft: as drafted it STOPs (unfilled, unsigned); with the launch fills (approved, the
    paper commit, the spec sha256, P3 and P4 completed) it passes ``check_note`` with the shipped spec's run_id and
    harness commit, and P1 cites TASL-2's host check record as ``launch`` requires."""
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True)
    note = d / "g4_t1_tasl_20261122.md"
    draft = DRAFT.read_text()
    note.write_text(draft)
    yes = lambda rel, raw: True  # noqa: E731
    with pytest.raises(T.Stop, match="not filled"):
        T.check_note(note, SPEC_PATH, SPEC["paper"]["commit"], on_main=yes, spec=SPEC)
    import re as _re
    signed = _re.sub(r"^approved: false$", "approved: true", draft, flags=_re.M)
    signed = _re.sub(r"^paper_commit: <FILL[^\n]*$", f"paper_commit: {SPEC['paper']['commit']}", signed, flags=_re.M)
    signed = _re.sub(r"^spec_sha256: <FILL[^\n]*$", f"spec_sha256: {G.L._sha_file(SPEC_PATH)}", signed, flags=_re.M)
    signed = _re.sub(r"^P3: PASS — <FILL[^\n]*$", "P3: PASS — the signed G.1b note docs/r1/authorizations/"
                     "g1b_t1_tasl_20261121.md; no G.1b job on either card during the pilot (G4-ORDER B)", signed,
                     flags=_re.M)
    note.write_text(signed)                    # P4 still names "<the G.4 launch-binding review>": refused
    with pytest.raises(T.Stop, match=r"placeholder\): \['P4'\]"):
        T.check_note(note, SPEC_PATH, SPEC["paper"]["commit"], on_main=yes, spec=SPEC)
    signed = signed.replace("docs/r1/reviews/<the G.4 launch-binding review>.md", "docs/r1/reviews/G4_REVIEW.md")
    assert "<FILL" not in signed and "<the" not in "".join(l for l in signed.splitlines() if _re.match(r"^\w+:", l))
    note.write_text(signed)
    fields = T.check_note(note, SPEC_PATH, SPEC["paper"]["commit"], on_main=yes, spec=SPEC)
    assert fields["run_id"] == SPEC["run_id"] and fields["harness_commit"] == SPEC["harness"]["commit"]
    assert SPEC["worker"]["isolation_host_check"]["record"] in fields["P1"]
    assert "breakout" in fields["P2"] and [n["node"] for n in SPEC["nodes"]][2] == "mlgym_breakout_minatar"
