"""G.1b on the TASL pair (sweep2/t1_tasl/g1b_tasl.py): spec, projection and cap, host checks, the node job with fake
host tools, the timing STOP, the lease, seal, assemble and summarise, and the launch note.

Synthetic only: no GPU, no host, no run (the engine, nvidia-smi and the setup are replaced).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT / "sweep2" / "g1b"))
import g1b_tasl as T  # noqa: E402
import g1b_lib as lib  # noqa: E402

SPEC_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())
UUID2 = "GPU-11111111-2222-3333-4444-555555555555"
UUID7 = "GPU-77777777-2222-3333-4444-555555555555"


def launch_spec(tmp_path: Path, **over) -> dict:
    spec = copy.deepcopy(SPEC)
    spec["paper"]["commit"] = "2" * 40
    for h, uuid in (("TASL-2", UUID2), ("TASL-7", UUID7)):
        host = spec["hosts"][h]
        host.update(hostname=f"host-{h}", gpu_uuid=uuid)
        for key in ("base", "harness_dir", "runs_root", "sealed_root"):
            host[key] = str(tmp_path / h / key)
        host["data_root"] = host["base"] + "/data"
        host["isolation_host_check"] = {"record": f"docs/r1/reports/{h}_check.md", "sha256": "3" * 64}
        host.pop("extra_env", None)
    spec["edit_count"]["authority"] = "R1-G1B-EDITS (21 Nov)"
    spec["timeout_decision"]["authority"] = "R1-G1B-TIMEOUT (21 Nov)"
    spec["host_decision"]["authority"] = "R1-T1-TASL-ENV (21 Nov)"
    spec.update(over)
    return spec


def test_shipped_spec_validates_and_refuses_launch_until_filled():
    loaded = T.validate_spec(copy.deepcopy(SPEC))
    p = loaded["projection"]
    assert p["within_cap"] and p["estimate"]["total_gpu_hours"] < 100
    assert set(p["estimate"]["per_node"]) == set(T.T1_NODES)
    assert p["estimate"]["per_node"]["mlgym_houseprice"]["device"] == "cpu"
    with pytest.raises(T.Stop):
        T.validate_spec(copy.deepcopy(SPEC), launch=True)


def test_projection_counts_gpu_nodes_in_gpu_hours_and_scales_with_the_ratio(tmp_path):
    spec = launch_spec(tmp_path)
    p = T.projection(spec)
    gpu_nodes = [n for n in spec["nodes"] if n["device"] == "gpu"]
    want = sum(460 * n["run_seconds"] + spec["estimate"]["setup_estimate_s"] for n in gpu_nodes) / 3600
    assert p["estimate"]["total_gpu_hours"] == pytest.approx(want, abs=0.01)
    assert p["sensitivity"]["total_gpu_hours"] > p["estimate"]["total_gpu_hours"]
    big = launch_spec(tmp_path, caps={"max_total_gpu_hours": 10})
    with pytest.raises(T.Stop, match="R1-G1B-CAP"):
        T.validate_spec(big)
    six = copy.deepcopy(spec)
    six["edit_count"].update(n_edits_per_node=5, runs_per_node=552)
    for n in six["nodes"]:
        n["n_edits"] = 5
    assert T.projection(six)["estimate"]["per_node"]["mlab_imdb"]["runs"] == 552


@pytest.mark.parametrize("edit, match", [
    (lambda s: s["nodes"].pop(), "seven passed census nodes"),
    (lambda s: s["nodes"][0].update(host="Ada"), "host must be one of"),
    (lambda s: [n.update(device="gpu") for n in s["nodes"] if n["node"] == "mlgym_houseprice"], "device must be cpu"),
    (lambda s: s["nodes"][0].update(device="cpu"), "device must be gpu"),
    (lambda s: s.update(gpu_model="NVIDIA H200"), "RTX 4090"),
    (lambda s: s["hosts"].pop("TASL-7"), "hosts must be exactly"),
    (lambda s: s["hosts"]["TASL-2"].update(lease="/tmp/x.lock"), "lease"),
    (lambda s: s["timeout_decision"].update(basis="census_median_x3"), "timeout_decision.basis"),
    (lambda s: s["measurement"].update(timeout_on_4090="divergent"), "timeout_on_4090"),
    (lambda s: [n.update(env="jax312") for n in s["nodes"] if n["node"] == "mlab_imdb"], "present on TASL-2"),
    (lambda s: s["nodes"][1].update(slowest_census_seconds=1.0), "below the baseline"),
    (lambda s: s["hosts"]["TASL-2"].update(gpu_uuid="GPU-1234"), "full GPU UUID"),
    (lambda s: s["hosts"]["TASL-2"].update(data_root="/elsewhere/data"), "<base>/data"),
    (lambda s: s["edit_count"].update(authority="TODO"), "R1-G1B-EDITS"),
    (lambda s: s["host_decision"].update(authority="R1-OTHER"), "R1-T1-TASL-ENV"),
])
def test_spec_refusals(tmp_path, edit, match):
    spec = launch_spec(tmp_path)
    edit(spec)
    with pytest.raises(T.Stop, match=match):
        T.validate_spec(spec, launch=True)


def test_chunk_uses_the_declared_timeout_basis_and_the_device(tmp_path):
    spec = launch_spec(tmp_path)
    ogbn = T.node_entry(spec, "mlab_ogbn_arxiv")
    chunk = T.chunk_file(spec, ogbn, lib.PARTS[0], interpreter="/x/python", cgroup_parent="/sys/fs/cgroup/s",
                         deadline=1e12)
    assert chunk["measured_run_seconds"] == 21.8 and chunk["device"] == "gpu"      # census_slowest_x3
    spec["timeout_decision"]["basis"] = "census_baseline_x3"
    assert T.chunk_file(spec, ogbn, lib.PARTS[0], interpreter="/x", cgroup_parent="/c",
                        deadline=1e12)["measured_run_seconds"] == 5.651
    hp = T.node_entry(spec, "mlgym_houseprice")
    assert T.chunk_file(spec, hp, lib.PARTS[1], interpreter="/x", cgroup_parent="/c", deadline=1e12)["device"] == "cpu"


# ---------------------------------------------------------------------------------------------- host checks
class Smi:
    def __init__(self, gpus, apps=""):
        self.gpus, self.apps = gpus, apps

    def __call__(self, argv, **kw):
        out = self.apps if "--query-compute-apps" in " ".join(argv) else self.gpus
        return subprocess.CompletedProcess(argv, 0, out, "")


def test_gpu_and_foreign_process_checks(tmp_path):
    spec = launch_spec(tmp_path)
    ok = Smi(f"{UUID2}, NVIDIA GeForce RTX 4090, 535.309.01, 24564 MiB\n")
    assert T.gpu_check(spec, "TASL-2", ok)["name"] == T.GPU_MODEL
    with pytest.raises(T.Stop, match="not on this host"):
        T.gpu_check(spec, "TASL-7", ok)
    with pytest.raises(T.Stop, match="not NVIDIA GeForce RTX 4090"):
        T.gpu_check(spec, "TASL-2", Smi(f"{UUID2}, NVIDIA RTX 6000 Ada Generation, 1, 2\n"))
    busy = Smi("", f"{UUID2}, 999999, 4000 MiB\n{UUID7}, 5, 10 MiB\n")
    with pytest.raises(T.Stop, match="foreign compute processes"):
        T.check_no_foreign(UUID2, "before default", busy)
    assert T.check_no_foreign(UUID7, "x", Smi("", f"{UUID2}, 999999, 1 MiB\n"))["foreign"] == []
    assert T.check_no_foreign(None, "x", busy)["device"] == "cpu"


def test_ptrace_scope_and_scope_cgroup(tmp_path):
    p = tmp_path / "ptrace"
    p.write_text("0\n")
    with pytest.raises(T.Stop, match="ptrace_scope is 0"):
        T.ptrace_scope(p)
    p.write_text("1\n")
    assert T.ptrace_scope(p) == 1
    cg = tmp_path / "scope"
    cg.mkdir()
    (cg / "memory.max").write_text("8589934592\n")
    (cg / "memory.swap.max").write_text("0\n")
    got = T.scope_cgroup({"AR_TEST_CGROUP_PARENT": str(cg)}, delegated=lambda: str(cg))
    assert got["memory.max"] == "8589934592"
    with pytest.raises(T.Stop, match="not this job's delegated scope"):
        T.scope_cgroup({"AR_TEST_CGROUP_PARENT": "/other"}, delegated=lambda: str(cg))
    (cg / "memory.swap.max").write_text("max\n")
    with pytest.raises(T.Stop, match="memory.swap.max"):
        T.scope_cgroup({"AR_TEST_CGROUP_PARENT": str(cg)}, delegated=lambda: str(cg))


def test_harness_checkout_must_be_at_the_pin_and_clean(tmp_path):
    spec = launch_spec(tmp_path)

    def git(head, status):
        return lambda argv, **kw: subprocess.CompletedProcess(argv, 0, head if "rev-parse" in argv else status, "")
    commit = spec["harness"]["commit"]
    assert T.harness_checkout(spec, "TASL-2", git(commit, "?? nodes/mlab_imdb/data\n"
                                                           "?? third_party/mlgym/nodes/mlgym_fmnist/data\n"))
    with pytest.raises(T.Stop, match="not the pin"):
        T.harness_checkout(spec, "TASL-2", git("0" * 40, ""))
    with pytest.raises(T.Stop, match="not clean"):
        T.harness_checkout(spec, "TASL-2", git(commit, " M src/autoresearch/trackg/runner.py\n"))
    with pytest.raises(T.Stop, match="not clean"):
        T.harness_checkout(spec, "TASL-2", git(commit, "?? src/sitecustomize.py\n"))


def test_environment_must_equal_the_census_freeze(tmp_path):
    spec = launch_spec(tmp_path)
    node = T.node_entry(spec, "mlab_imdb")
    freeze = (ROOT / "sweep2" / "g1b" / spec["envs"]["torch312"]["freeze"]).read_text()

    def sh(freeze_text, version="3.12.16"):
        return lambda argv, **kw: subprocess.CompletedProcess(argv, 0, freeze_text if "freeze" in argv else version, "")
    assert T.environment(spec, "TASL-2", node, sh(freeze))["packages"] > 50
    with pytest.raises(T.Stop, match="differs from the census freeze"):
        T.environment(spec, "TASL-2", node, sh(freeze + "extra==1.0\n"))
    with pytest.raises(T.Stop, match="not 3.12.16"):
        T.environment(spec, "TASL-2", node, sh(freeze, "3.12.3"))


def test_the_gpu_lease_is_exclusive(tmp_path):
    lease = str(tmp_path / "locks" / "gpu0.lock")
    with T.gpu_lease(lease):
        with pytest.raises(T.Stop, match="held by another job"):
            with T.gpu_lease(lease):
                pass
    with T.gpu_lease(lease) as held:
        assert held["lease"].endswith("gpu0.lock")


def test_a_timeout_on_the_4090_is_a_timing_stop():
    node = {"node": "mlab_ogbn_arxiv", "run_seconds": 5.651}
    rows = [{"run_id": "c0_x", "config": "c0", "wall_seconds": 6.2, "failure": None},
            {"run_id": "c4_x", "config": "c4", "wall_seconds": 22.0, "failure": None}]
    got = T.timing_check(rows, node, "default")
    assert got["ratio_4090_over_ada"] == pytest.approx(6.2 / 5.651, abs=1e-4)
    rows.append({"run_id": "c4_y", "config": "c4", "wall_seconds": 65.5, "failure": "divergent:timeout"})
    with pytest.raises(T.TimingStop, match="declared timeout on the 4090"):
        T.timing_check(rows, node, "train")


# ---------------------------------------------------------------------------------------------- the node job
GATE = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True, "parent_traced_by": None,
        "parent_dumpable_at_accept": False}


def _write_part(out: Path, node: str, part: tuple, *, timeout_config=None, nondet=False):
    out.mkdir(parents=True)
    rows = []
    for run in lib.expected_runs(4, part[1], part[2]):
        k = int(run["config"][1:])
        failure = "divergent:timeout" if run["config"] == timeout_config else None
        metric = None if failure else 0.5 + 0.004 * k + (1e-6 if nondet and run["condition"] == "default_repeat" else 0)
        rows.append({"node": node, **run, "metric": metric, "success": metric is not None, "failure": failure,
                     "wall_seconds": 6.0, "run_id": T.L.expected_runs and f"{run['config']}_{run['condition']}_"
                     f"{run['train_seed']}_{run['split_seed']}", "isolation": dict(GATE)})
    (out / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (out / "edits.json").write_text(json.dumps({node: []}))
    (out / "chunk_record.json").write_text(json.dumps({"expected_runs": len(rows), "written_rows": len(rows),
                                                        "successful_rows": len(rows), "stop": None}))


@pytest.fixture
def job(tmp_path, monkeypatch):
    spec = launch_spec(tmp_path)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    calls = []
    monkeypatch.setattr(T, "host_identity", lambda s, h: {"host": h, "hostname": f"host-{h}"})
    monkeypatch.setattr(T, "ptrace_scope", lambda: 1)
    monkeypatch.setattr(T, "scope_cgroup", lambda: {"cgroup_parent": "/sys/fs/cgroup/scope"})
    monkeypatch.setattr(T, "harness_checkout", lambda s, h: {"commit": s["harness"]["commit"]})
    monkeypatch.setattr(T, "environment", lambda s, h, n: {"name": n["env"]})
    monkeypatch.setattr(os, "environ", dict(os.environ))
    state = {"timeout_part": None, "timeout_config": None, "nondet": False}

    def engine(argv, **kw):
        calls.append(argv)
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        part = next(p for p in lib.PARTS if p[0] == Path(argv[argv.index("--out") + 1]).name)
        _write_part(Path(argv[argv.index("--out") + 1]), chunk["node"], part,
                    timeout_config=state["timeout_config"] if part[0] == state["timeout_part"] else None,
                    nondet=state["nondet"])
        return subprocess.CompletedProcess(argv, 0, "", "")

    def smi(argv, **kw):
        uuid = UUID2 if "TASL-2" in str(tmp_path) else UUID2
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 1, 2\n"
                                                    f"{UUID7}, NVIDIA GeForce RTX 4090, 1, 2\n", "")
    setup = lambda harness, node, base, out: {"data_root": str(base / "data"), "setup": "x"}  # noqa: E731
    return spec, spec_path, calls, state, engine, smi, setup


def test_node_job_end_to_end(job, tmp_path):
    spec, spec_path, calls, state, engine, smi, setup = job
    rec = T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    assert rec["runs"]["written"] == 460 and rec["stop"] is None and rec["host"]["host"] == "TASL-2"
    assert all(c[-2:] == ["--gpu-uuid", UUID2] for c in calls)
    assert rec["timeout_basis"] == {"decision": "census_slowest_x3", "seconds": 65.156, "timeout_s": 3 * 65.156}
    assert len(rec["foreign_checks"]) == 8 and rec["lease"]["lease"].endswith("gpu0.lock")
    job_dir = Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "mlab_imdb"
    assert subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=job_dir, capture_output=True).returncode == 0
    calls.clear()
    rec = T.run_node_job(spec_path, "mlgym_houseprice", smi=smi, engine=engine, setup=setup)
    assert rec["gpu"] == {"device": "cpu"} and all("--gpu-uuid" not in c for c in calls)
    assert rec["lease"] == {"lease": None}


def test_node_job_stops(job, tmp_path):
    spec, spec_path, calls, state, engine, smi, setup = job
    state.update(timeout_part="train", timeout_config="c3")
    with pytest.raises(T.Stop, match="declared timeout on the 4090"):
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    rec = json.loads((Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "mlab_imdb" /
                      "job_record.json").read_text())
    assert rec["stop_class"] == "timing" and [p["part"] for p in rec["parts"]] == ["default", "train"]
    state.update(timeout_part=None, nondet=True)
    with pytest.raises(T.Stop, match="determinism"):
        T.run_node_job(spec_path, "mlgym_fmnist", smi=smi, engine=engine, setup=setup)
    rec = json.loads((Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "mlgym_fmnist" /
                      "job_record.json").read_text())
    assert rec["stop_class"] == "node"
    state.update(nondet=False)

    def busy(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, f"{UUID2}, 424242, 9 MiB\n", "")
        return smi(argv)
    with pytest.raises(T.Stop, match="foreign compute processes"):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=busy, engine=engine, setup=setup)
    with pytest.raises(FileExistsError):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=engine, setup=setup)   # no overwrite


def test_seal_assemble_summarise(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    sealed = []
    for node in spec["nodes"]:
        T.run_node_job(spec_path, node["node"], smi=smi, engine=engine, setup=setup)
        host = spec["hosts"][node["host"]]
        job_dir = Path(host["runs_root"]) / spec["run_id"] / node["node"]
        (job_dir.parent / f"{node['node']}.node.log").write_text("NODE_EXIT=0\n")
        receipt = T.seal(job_dir, spec, node["node"])
        assert receipt["node_log_sha256"] and receipt["host"] == node["host"]
        sealed.append(Path(receipt["sealed_path"]))
    with pytest.raises(T.Stop, match="exists"):
        T.seal(Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "mlab_imdb", spec, "mlab_imdb")
    manifest = T.assemble(sealed, spec, tmp_path / "run", lib._sha_file(spec_path))
    assert {j["host"] for j in manifest["jobs"]} == {"TASL-2", "TASL-7"}
    # the D21 summary through g1b_lib.summarise; the synthetic rows have no seed noise, so only the wiring is checked
    called = {}
    monkeypatch.setattr(T.L, "summarise", lambda run_dir, s, root: called.update(n=len(s["nodes"])) or
                        {"schema": "x", "verdicts": {}})
    summary = T.summarise(tmp_path / "run", spec, ROOT)
    assert called["n"] == 7 and summary["schema"] == T.SUMMARY_SCHEMA and summary["gpu_model"] == T.GPU_MODEL
    assert summary["hosts"]["mlgym_breakout_minatar"] == "TASL-7" and summary["devices"]["mlgym_houseprice"] == "cpu"
    # a sealed job from the wrong host or with a timing STOP is refused
    bad = copy.deepcopy(spec)
    for n in bad["nodes"]:
        if n["node"] == "mlab_imdb":
            n["host"] = "TASL-7"
    with pytest.raises(T.Stop, match="does not match the table"):
        T.assemble(sealed, bad, tmp_path / "run2", lib._sha_file(spec_path))


# ---------------------------------------------------------------------------------------------- launch
def _note(tmp_path, spec_path, commit, **over):
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none", "paper_commit": commit,
              "spec_sha256": lib._sha_file(spec_path), "host_row": "R1-T1-TASL-ENV (21 Nov)",
              "P1": "PASS — R1-T1-HOST-TASL", "P2": "PASS — TASL-2 host check x", "P3": "PASS — TASL-7 host check y",
              "P4": "PASS — docs/r1/reviews/T1_TASL_REVIEW.md", "P5": "PASS — R1-G1B-EDITS 4 edits",
              "P6": "PASS — R1-G1B-TIMEOUT census_slowest_x3"}
    fields.update(over)
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "g1b_t1_tasl_20991231.md"
    p.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    return p


def test_launch_needs_the_note_both_keys_and_the_binding(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    yes = lambda rel, raw: True  # noqa: E731
    note = _note(tmp_path, spec_path, spec["paper"]["commit"])
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    with pytest.raises(T.Stop, match="disabled"):
        T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=yes)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    with pytest.raises(T.Stop, match="not committed"):
        T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=lambda rel, raw: False)
    seen = []
    out = T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=yes,
                   launch_binding=lambda repo, s, rows: seen.append(rows) or {"bound": True},
                   runner=lambda sp, n: {"runs": {"written": 460}})
    assert out["launch"] == {"bound": True} and "R1-T1-TASL-ENV" in seen[0] and "R1-T1-HOST-TASL" in seen[0]
    for key, value, match in (("P5", "PASS — something", "R1-G1B-EDITS"), ("approved", "false", "approved"),
                              ("spec_sha256", "0" * 64, "spec_sha256"), ("host_row", "R1-X", "host_row"),
                              ("P3", "FAIL", "P3 is not PASS")):
        bad = _note(tmp_path, spec_path, spec["paper"]["commit"], **{key: value})
        with pytest.raises(T.Stop, match=match):
            T.launch(spec_path, bad, "mlab_imdb", enable=True, on_main=yes, launch_binding=lambda *a: {},
                     runner=lambda sp, n: {})


def test_wrapper_script_runs_in_a_delegated_scope():
    text = (ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_node.sh").read_text()
    for needle in ("systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0",
                   "AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG", 'CUDA_VISIBLE_DEVICES=""', "taskset -c",
                   "unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs", "no overwrite"):
        assert needle in text
