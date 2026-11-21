"""G.1b on the TASL pair (sweep2/t1_tasl/g1b_tasl.py): spec, projection and cap, host checks, the node job with fake
host tools, the timing STOP, the lease, seal, assemble and summarise, and the launch note.

Synthetic only: no GPU, no host, no run (the engine, nvidia-smi and the setup are replaced).
"""
from __future__ import annotations

import copy
import hashlib
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


def host_report(h: str, verdict="PASS", items="1-7 PASS", commit=None) -> str:
    return (f"# host check {h}\nhost_check_host: host-{h}\nhost_check_harness_commit: {commit or SPEC['harness']['commit']}\n"
            f"host_check_items: {items}\nhost_check_verdict: {verdict}\n")


def launch_spec(tmp_path: Path, **over) -> dict:
    spec = copy.deepcopy(SPEC)
    spec["paper"]["commit"] = "2" * 40
    for h, uuid in (("TASL-2", UUID2), ("TASL-7", UUID7)):
        host = spec["hosts"][h]
        host.update(hostname=f"host-{h}", gpu_uuid=uuid)
        for key in ("base", "harness_dir", "runs_root", "sealed_root"):
            host[key] = str(tmp_path / h / key)
        host["data_root"] = host["base"] + "/data"
        host["isolation_host_check"] = {"record": f"docs/r1/reports/{h}_check.md",
                                        "sha256": hashlib.sha256(host_report(h).encode()).hexdigest()}
        host.pop("extra_env", None)
    spec["edit_count"]["authority"] = "R1-G1B-EDITS (21 Nov)"
    spec["timeout_decision"]["authority"] = "R1-G1B-TIMEOUT (21 Nov)"
    spec["host_decision"]["authority"] = "R1-T1-TASL-ENV (21 Nov)"
    spec.update(over)
    return spec


def test_shipped_spec_validates_and_a_todo_still_refuses_launch(tmp_path):
    """The shipped spec is filled, so it must pass launch validation; a copy with one TODO field reset must still
    refuse, and launch must still refuse without the signed note on origin/main (the filled values stay unchanged)."""
    loaded = T.validate_spec(copy.deepcopy(SPEC), launch=True)
    p = loaded["projection"]
    assert p["within_cap"] and p["estimate"]["total_gpu_hours"] < 100
    assert set(p["estimate"]["per_node"]) == set(T.T1_NODES)
    assert p["estimate"]["per_node"]["mlgym_houseprice"]["device"] == "cpu"

    todo = copy.deepcopy(SPEC)
    todo["hosts"]["TASL-2"]["hostname"] = "TODO: hostname of TASL-2"
    with pytest.raises(T.Stop, match="hostname"):
        T.validate_spec(todo, launch=True)

    note = tmp_path / "docs" / "r1" / "authorizations" / "g1b_t1_tasl_20261121.md"
    note.parent.mkdir(parents=True)
    note.write_text("approved: true\n")
    with pytest.raises(T.Stop, match="not committed byte-identically on origin/main"):
        T.launch(SPEC_PATH, note, "mlab_imdb", enable=True,
                 on_main=lambda rel, raw: False)


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
    (lambda s: [n.update(cpus="6-9") for n in s["nodes"] if n["node"] == "mlgym_houseprice"], "overlaps"),
    (lambda s: s["nodes"][0].update(cpus="20-21"), "only the CPU-only node"),
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
    hp_chunk = T.chunk_file(spec, hp, lib.PARTS[1], interpreter="/x", cgroup_parent="/c", deadline=1e12)
    assert hp_chunk["device"] == "cpu" and hp_chunk["stop_on_timeout"] is True


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


def _write_part(out: Path, node: str, part: tuple, *, timeout_config=None, nondet=False, stop_on_timeout=False):
    """What the engine writes; with stop_on_timeout it stops right after the first timeout row (harness c025f89a)."""
    out.mkdir(parents=True)
    rows, stop = [], {"stop": None}
    for run in lib.expected_runs(4, part[1], part[2]):
        k = int(run["config"][1:])
        failure = "divergent:timeout" if run["config"] == timeout_config else None
        metric = None if failure else 0.5 + 0.004 * k + (1e-6 if nondet and run["condition"] == "default_repeat" else 0)
        rows.append({"node": node, **run, "metric": metric, "success": metric is not None, "failure": failure,
                     "wall_seconds": 6.0, "run_id": f"{run['config']}_{run['condition']}_"
                     f"{run['train_seed']}_{run['split_seed']}", "isolation": dict(GATE)})
        if failure and stop_on_timeout:
            stop = {"stop": "NoiseFloorStop: STOP: x reached the declared timeout", "stop_kind": "timeout"}
            break
    (out / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (out / "edits.json").write_text(json.dumps({node: []}))
    (out / "chunk_record.json").write_text(json.dumps({"expected_runs": len(lib.expected_runs(4, part[1], part[2])),
                                                        "written_rows": len(rows), "successful_rows": len(rows),
                                                        **stop}))
    return stop


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
    monkeypatch.setattr(T, "check_affinity", lambda s, n, affinity=None: T.cpu_list(T.node_cpus(s, n)))
    monkeypatch.setattr(os, "environ", dict(os.environ))
    state = {"timeout_part": None, "timeout_config": None, "nondet": False}

    def engine(argv, **kw):
        calls.append(argv)
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        part = next(p for p in lib.PARTS if p[0] == Path(argv[argv.index("--out") + 1]).name)
        stop = _write_part(Path(argv[argv.index("--out") + 1]), chunk["node"], part,
                           timeout_config=state["timeout_config"] if part[0] == state["timeout_part"] else None,
                           nondet=state["nondet"], stop_on_timeout=chunk.get("stop_on_timeout", False))
        return subprocess.CompletedProcess(argv, 3 if stop["stop"] else 0, "", "")

    def smi(argv, **kw):
        uuid = UUID2 if "TASL-2" in str(tmp_path) else UUID2
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 1, 2\n"
                                                    f"{UUID7}, NVIDIA GeForce RTX 4090, 1, 2\n", "")
    setup = lambda harness, node, base, out: {"data_root": str(base / "data"), "setup": "x"}  # noqa: E731
    return spec, spec_path, calls, state, engine, smi, setup


def _attempt(spec, node, n=1):
    host = T.node_entry(spec, node)["host"]
    return Path(spec["hosts"][host]["runs_root"]) / spec["run_id"] / node / f"attempt-{n}"


def test_node_job_end_to_end(job, tmp_path):
    spec, spec_path, calls, state, engine, smi, setup = job
    rec = T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    assert rec["runs"]["written"] == 460 and rec["stop"] is None and rec["host"]["host"] == "TASL-2"
    assert rec["attempt"] == 1 and all(c[-2:] == ["--gpu-uuid", UUID2] for c in calls)
    assert rec["timeout_basis"] == {"decision": "census_slowest_x3", "seconds": 65.156, "timeout_s": 3 * 65.156}
    assert len(rec["foreign_checks"]) == 9 and rec["lease"]["lease"].endswith("gpu0.lock")   # job start, before/after each part
    assert json.loads((_attempt(spec, "mlab_imdb") / "attempt.json").read_text())["pid"] == os.getpid()
    assert subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=_attempt(spec, "mlab_imdb"),
                          capture_output=True).returncode == 0
    with pytest.raises(T.Stop, match="no new attempt"):          # a complete node is never run again
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    calls.clear()
    rec = T.run_node_job(spec_path, "mlgym_houseprice", smi=smi, engine=engine, setup=setup)
    assert rec["gpu"] == {"device": "cpu"} and all("--gpu-uuid" not in c for c in calls)
    assert rec["lease"] == {"lease": None} and rec["affinity"] == list(range(8, 16))


def test_refusals_before_the_run_use_up_nothing_and_infrastructure_stops_may_be_retried(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job

    def busy(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, f"{UUID2}, 424242, 9 MiB\n", "")
        return smi(argv)
    with pytest.raises(T.Stop, match="foreign compute processes"):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=busy, engine=engine, setup=setup)
    run_root = Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"]
    assert not (run_root / "mlab_ogbn_arxiv").exists() and len(list((run_root / "_refusals").iterdir())) == 1
    lease = os.path.expanduser(spec["hosts"]["TASL-2"]["lease"])
    with T.gpu_lease(lease):                                       # a busy lease is a refusal too
        with pytest.raises(T.Stop, match="held by another job"):
            T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=engine, setup=setup)
    monkeypatch.setattr(T, "ptrace_scope", lambda: (_ for _ in ()).throw(TypeError("boom")))
    with pytest.raises(T.Stop, match="unexpected TypeError before the run"):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=engine, setup=setup)
    assert len(list((run_root / "_refusals").iterdir())) == 3 and not (run_root / "mlab_ogbn_arxiv").exists()
    monkeypatch.setattr(T, "ptrace_scope", lambda: 1)
    # an infrastructure STOP inside the attempt: the next attempt is allowed
    failing = {"n": 0}

    def flaky(argv, **kw):
        failing["n"] += 1
        if failing["n"] == 1:
            raise OSError("disk full")
        return engine(argv, **kw)
    with pytest.raises(T.Stop, match="unexpected OSError"):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=flaky, setup=setup)
    assert json.loads((_attempt(spec, "mlab_ogbn_arxiv") / "job_record.json").read_text())["stop_class"] == \
        "infrastructure"
    rec = T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=flaky, setup=setup)
    assert rec["attempt"] == 2 and rec["stop"] is None


def test_node_job_author_stops_end_the_node(job, tmp_path):
    spec, spec_path, calls, state, engine, smi, setup = job
    state.update(timeout_part="train", timeout_config="c3")
    with pytest.raises(T.Stop, match="declared timeout"):
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    rec = json.loads((_attempt(spec, "mlab_imdb") / "job_record.json").read_text())
    assert rec["stop_class"] == "timing" and [p["part"] for p in rec["parts"]] == ["default", "train"]
    assert rec["parts"][1]["written_rows"] == 4 and rec["parts"][1]["stop_kind"] == "timeout"   # stopped at once
    with pytest.raises(T.Stop, match="no new attempt"):
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    state.update(timeout_part=None, timeout_config=None, nondet=True)
    with pytest.raises(T.Stop, match="determinism"):
        T.run_node_job(spec_path, "mlgym_fmnist", smi=smi, engine=engine, setup=setup)
    assert json.loads((_attempt(spec, "mlgym_fmnist") / "job_record.json").read_text())["stop_class"] == "node"
    state.update(nondet=False)
    with pytest.raises(T.Stop, match="no new attempt"):
        T.run_node_job(spec_path, "mlgym_fmnist", smi=smi, engine=engine, setup=setup)


def test_seal_assemble_summarise(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    sealed = []
    for node in spec["nodes"]:
        host = spec["hosts"][node["host"]]
        log = Path(host["runs_root"]) / spec["run_id"] / "_logs" / f"{node['node']}-x.node.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("NODE_EXIT=0\n")
        T.run_node_job(spec_path, node["node"], smi=smi, engine=engine, setup=setup, node_log=str(log))
        receipt = T.seal(_attempt(spec, node["node"]), spec, node["node"])
        assert receipt["node_log_sha256"] and receipt["host"] == node["host"] and receipt["attempt"] == 1
        sealed.append(Path(receipt["sealed_path"]))
    with pytest.raises(T.Stop, match="exists"):
        T.seal(_attempt(spec, "mlab_imdb"), spec, "mlab_imdb")
    manifest = T.assemble(sealed, spec, tmp_path / "run", lib._sha_file(spec_path))
    assert {j["host"] for j in manifest["jobs"]} == {"TASL-2", "TASL-7"}
    called = {}
    monkeypatch.setattr(T.L, "summarise", lambda run_dir, s, root: called.update(n=len(s["nodes"])) or
                        {"schema": "x", "verdicts": {}})
    summary = T.summarise(tmp_path / "run", spec, ROOT)
    assert called["n"] == 7 and summary["schema"] == T.SUMMARY_SCHEMA and summary["gpu_model"] == T.GPU_MODEL
    assert summary["hosts"]["mlgym_breakout_minatar"] == "TASL-7" and summary["devices"]["mlgym_houseprice"] == "cpu"
    bad = copy.deepcopy(spec)
    for n in bad["nodes"]:
        if n["node"] == "mlab_imdb":
            n["host"] = "TASL-7"
    with pytest.raises(T.Stop, match="does not match the table"):
        T.assemble(sealed, bad, tmp_path / "run2", lib._sha_file(spec_path))
    # a second sealed attempt that is not an infrastructure STOP cannot sit beside the chosen one
    other = sealed[0].parent / "attempt-2"
    other.mkdir()
    (other / "job_record.json").write_text(json.dumps({"stop_class": None}))
    with pytest.raises(T.Stop, match="one attempt per node"):
        T.assemble(sealed, spec, tmp_path / "run3", lib._sha_file(spec_path))


def test_close_attempt_for_a_crash_without_record(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    node_root = Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "mlab_ogbn_arxiv"
    n, attempt = T.next_attempt(node_root)                       # as if the host rebooted mid-run
    with pytest.raises(T.Stop, match="no job record"):
        T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=engine, setup=setup)
    lease = spec["hosts"]["TASL-2"]["lease"]
    with pytest.raises(T.Stop, match="still alive"):
        T.close_attempt(attempt, "host rebooted during the train part", lease=lease)        # our own pid is alive
    with pytest.raises(T.Stop, match="reason"):
        T.close_attempt(attempt, "x", lease=lease, alive=lambda pid: False)
    with T.gpu_lease(lease):
        with pytest.raises(T.Stop, match="held by another job"):
            T.close_attempt(attempt, "host rebooted during the train part", lease=lease, alive=lambda pid: False)
    with pytest.raises(T.Stop, match="still name"):
        T.close_attempt(attempt, "host rebooted during the train part", lease=lease, alive=lambda pid: False,
                        scan=lambda path: [4242])
    rec = T.close_attempt(attempt, "host rebooted during the train part", lease=lease, alive=lambda pid: False)
    assert rec["stop_class"] == "infrastructure"
    with pytest.raises(T.Stop, match="without a job record"):
        T.close_attempt(attempt, "host rebooted during the train part", lease=lease, alive=lambda pid: False)
    assert T.run_node_job(spec_path, "mlab_ogbn_arxiv", smi=smi, engine=engine, setup=setup)["attempt"] == 2


def test_close_attempt_without_attempt_json_and_the_process_scan(tmp_path):
    proc = tmp_path / "proc"
    (proc / "123").mkdir(parents=True)
    attempt = tmp_path / "node" / "attempt-1"
    attempt.mkdir(parents=True)
    (proc / "123" / "cmdline").write_bytes(b"python\0-m\0noise_floor\0--chunk\0" + str(attempt / "out/c.json").encode())
    (proc / "self").mkdir()
    assert T.processes_mentioning(attempt, proc) == [123]
    real = tmp_path / "real"
    (real / "attempt-1").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    (proc / "123" / "cmdline").write_bytes(b"python\0--chunk\0" + str(link / "attempt-1" / "out/c.json").encode())
    assert T.processes_mentioning(link / "attempt-1", proc) == [123]          # unresolved path under a symlink
    (proc / "123" / "cmdline").write_bytes(b"bash\0")
    assert T.processes_mentioning(attempt, proc) == []
    rec = T.close_attempt(attempt, "crash between mkdir and attempt.json", lease=None, scan=lambda p: [])
    assert rec["owner"]["pid"] is None and rec["stop_class"] == "infrastructure"


def test_lease_and_refusal_failures_still_stop(job, tmp_path, monkeypatch, capsys):
    spec, spec_path, calls, state, engine, smi, setup = job
    import contextlib

    @contextlib.contextmanager
    def broken(path):
        raise PermissionError("no ~/r1_locks")
        yield
    monkeypatch.setattr(T, "gpu_lease", broken)
    with pytest.raises(T.Stop, match="unexpected PermissionError taking the lease"):
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    monkeypatch.setattr(T, "_write_refusal", lambda *a: (_ for _ in ()).throw(OSError("read-only")))
    with pytest.raises(T.Stop, match="taking the lease"):
        T.run_node_job(spec_path, "mlab_imdb", smi=smi, engine=engine, setup=setup)
    assert "refusal record not written" in capsys.readouterr().err


def test_host_check_record_is_verified_on_main(tmp_path):
    spec = launch_spec(tmp_path)
    host = spec["hosts"]["TASL-2"]
    commit = spec["harness"]["commit"]
    good = host_report("TASL-2").encode()
    assert T.check_host_record(host, commit, lambda rel: good)["record"] == host["isolation_host_check"]["record"]
    with pytest.raises(T.Stop, match="not on published main"):
        T.check_host_record(host, commit, lambda rel: None)
    with pytest.raises(T.Stop, match="declared sha256"):
        T.check_host_record(host, commit, lambda rel: good + b"x")
    for text, match in ((host_report("TASL-2", verdict="FAIL"), "host_check_verdict"),
                        (host_report("TASL-2", items="1-6 PASS"), "host_check_items"),
                        (host_report("TASL-2", commit="0" * 40), "host_check_harness_commit"),
                        (host_report("TASL-7"), "host_check_host")):
        h = copy.deepcopy(host)
        h["isolation_host_check"]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        with pytest.raises(T.Stop, match=match):
            T.check_host_record(h, commit, lambda rel, t=text: t.encode())
    h = copy.deepcopy(host)
    h["isolation_host_check"]["record"] = "TODO: x"
    with pytest.raises(T.Stop, match="no placeholder"):
        T.check_host_record(h, commit, lambda rel: good)


def test_affinity_must_equal_the_declared_cpus(tmp_path):
    spec = launch_spec(tmp_path)
    node = T.node_entry(spec, "mlab_imdb")
    assert T.check_affinity(spec, node, affinity={0, 1, 2, 3, 4, 5, 6, 7}) == list(range(8))
    with pytest.raises(T.Stop, match="CPU affinity"):
        T.check_affinity(spec, node, affinity=set(range(16)))


# ---------------------------------------------------------------------------------------------- launch
def _note(tmp_path, spec_path, commit, **over):
    spec = json.loads(Path(spec_path).read_text())
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none", "paper_commit": commit,
              "spec_sha256": lib._sha_file(spec_path), "run_id": spec["run_id"],
              "harness_commit": spec["harness"]["commit"], "host_row": "R1-T1-TASL-ENV (21 Nov)",
              "P1": "PASS — R1-T1-HOST-TASL", "P2": "PASS — TASL-2 host check docs/r1/reports/TASL-2_check.md",
              "P3": "PASS — TASL-7 host check docs/r1/reports/TASL-7_check.md",
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
    reports = {f"docs/r1/reports/{h}_check.md": host_report(h).encode() for h in T.HOSTS}
    seen = []
    out = T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=yes, read_main=reports.get,
                   launch_binding=lambda repo, s, rows: seen.append(rows) or {"bound": True},
                   runner=lambda sp, n: {"runs": {"written": 460}})
    with pytest.raises(T.Stop, match="not on published main"):
        T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=yes, read_main=lambda rel: None,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    assert out["launch"] == {"bound": True} and "R1-T1-TASL-ENV" in seen[0] and "R1-T1-HOST-TASL" in seen[0]
    for key, value, match in (("P5", "PASS — something", "R1-G1B-EDITS"), ("approved", "false", "approved"),
                              ("spec_sha256", "0" * 64, "spec_sha256"), ("host_row", "R1-X", "host_row"),
                              ("P3", "FAIL", "P3 is not PASS"), ("run_id", "other", "run_id"),
                              ("harness_commit", SPEC["harness"]["commit"][:8], "harness_commit"),
                              ("P2", "PASS — TASL-2 host check, see the report", "P2 must cite")):
        bad = _note(tmp_path, spec_path, spec["paper"]["commit"], **{key: value})
        with pytest.raises(T.Stop, match=match):
            T.launch(spec_path, bad, "mlab_imdb", enable=True, on_main=yes, read_main=reports.get,
                     launch_binding=lambda *a: {}, runner=lambda sp, n: {})


STUB_SYSTEMD_RUN = """#!/bin/bash
# stub: record the arguments, then run the command after "--" in a fake scope
echo "$@" > "$STUB_DIR/systemd_run_args"
while [ "$1" != "--" ]; do shift; done; shift
exec "$@"
"""
STUB_TASKSET = """#!/bin/bash
echo "$2" > "$STUB_DIR/taskset_cpus"; shift 2; exec "$@"
"""


def _stub_env(tmp_path, run_root: Path, rc: int):
    stub = tmp_path / "stub"
    stub.mkdir(exist_ok=True)
    for name, text in (("systemd-run", STUB_SYSTEMD_RUN), ("taskset", STUB_TASKSET)):
        (stub / name).write_text(text)
        (stub / name).chmod(0o755)
    orch = stub / "orch.py"           # stands in for the orchestrator Python: cpus, logdir, run-node
    orch.write_text(f"""import os, sys
cmd = sys.argv[2]
if cmd == "cpus": print("0-7")
elif cmd == "logdir": print({str(run_root / "_logs")!r})
else:
    open(os.environ["STUB_DIR"] + "/run_node_argv", "w").write(" ".join(sys.argv[2:]) + "\\n" +
        os.environ.get("AR_TEST_CGROUP_PARENT", "") + "\\n" + os.environ.get("G1B_TASL_NODE_LOG", ""))
    sys.exit({rc})
""")
    wrapper_py = stub / "python"
    wrapper_py.write_text(f"#!/bin/bash\nexec {sys.executable} {orch} \"$@\"\n")
    wrapper_py.chmod(0o755)
    return dict(os.environ, PATH=f"{stub}:{os.environ['PATH']}", STUB_DIR=str(stub),
                T1_TASL_ORCHESTRATOR_PYTHON=str(wrapper_py))


@pytest.mark.parametrize("rc, want", [(0, 0), (2, 4)])
def test_wrapper_runs_the_job_in_a_scope_with_a_fresh_log(tmp_path, rc, want):
    script = ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh"
    run_root = tmp_path / "runs" / "rid"
    env = _stub_env(tmp_path, run_root, rc)
    res = subprocess.run(["bash", str(script), "g1b", "spec.json", "mlab_imdb", "note.md", "--enable"], env=env,
                         capture_output=True, text=True)
    assert res.returncode == want, res.stderr
    stub = Path(env["STUB_DIR"])
    assert "--user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0" in (stub / "systemd_run_args").read_text()
    assert (stub / "taskset_cpus").read_text().strip() == "0-7"
    argv, cgroup, log = (stub / "run_node_argv").read_text().split("\n")
    assert argv == "run-node spec.json --node mlab_imdb --note note.md --enable" and cgroup.startswith("/sys/fs/cgroup")
    assert "\n" not in cgroup
    logs = list((run_root / "_logs").iterdir())
    assert len(logs) == 1 and str(logs[0]) == log and f"NODE_EXIT={rc}" in logs[0].read_text()
    res2 = subprocess.run(["bash", str(script), "g1b", "spec.json", "mlab_imdb", "note.md"], env=env,
                          capture_output=True, text=True)
    assert res2.returncode == want and len(list((run_root / "_logs").iterdir())) == 2     # a new log, nothing reused
    bad = subprocess.run(["bash", str(script), "g1b", "spec.json", "mlab_imdb", "note.md", "--yes"], env=env,
                         capture_output=True, text=True)
    assert bad.returncode == 2


def test_wrapper_g4_passes_the_server_record(tmp_path):
    script = ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh"
    run_root = tmp_path / "runs" / "rid"
    env = _stub_env(tmp_path, run_root, 0)
    res = subprocess.run(["bash", str(script), "g4", "spec.json", "mlab_cifar10", "note.md", "srv.json", "--enable"],
                         env=env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    argv = (Path(env["STUB_DIR"]) / "run_node_argv").read_text().split("\n")[0]
    assert argv == "run-node spec.json --node mlab_cifar10 --note note.md --server-record srv.json --enable"
    assert subprocess.run(["bash", str(script), "g4", "spec.json", "mlab_cifar10", "note.md"], env=env,
                          capture_output=True).returncode == 2


def test_a_tasl7_node_needs_p7_the_cross_host_check(job, tmp_path, monkeypatch):
    """R1-T1-TASL-ENV: a node on TASL-7 launches only with P7 PASS citing the row; a TASL-2 node does not need it."""
    spec, spec_path, *_ = job
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    reports = {f"docs/r1/reports/{h}_check.md": host_report(h).encode() for h in T.HOSTS}
    kw = dict(enable=True, on_main=lambda rel, raw: True, read_main=reports.get, launch_binding=lambda *a: {},
              runner=lambda sp, n: {"node": n})
    tasl7 = next(n["node"] for n in spec["nodes"] if n["host"] == "TASL-7")
    tasl2 = next(n["node"] for n in spec["nodes"] if n["host"] == "TASL-2")
    note = _note(tmp_path, spec_path, spec["paper"]["commit"])
    assert T.launch(spec_path, note, tasl2, **kw)["node"] == tasl2
    with pytest.raises(T.Stop, match="P7 PASS citing R1-T1-TASL-ENV"):
        T.launch(spec_path, note, tasl7, **kw)
    for p7 in ("PENDING — R1-T1-TASL-ENV cross-host check not built", "PASS — cross-host check done"):
        with pytest.raises(T.Stop, match="P7"):
            T.launch(spec_path, _note(tmp_path, spec_path, spec["paper"]["commit"], P7=p7), tasl7, **kw)
    ok = _note(tmp_path, spec_path, spec["paper"]["commit"],
               P7="PASS — R1-T1-TASL-ENV cross-host check docs/r1/reports/xc.md")
    assert T.launch(spec_path, ok, tasl7, **kw)["node"] == tasl7


def _git(repo, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def _launch_repo(tmp_path):
    """origin (bare) and a clone: C = code and PLAN; M = C + the spec naming C + the note (published main)."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    _git(work, "checkout", "-q", "-b", "main")
    (work / "docs/r1/authorizations").mkdir(parents=True)
    (work / "docs/r1/PLAN.md").write_text("".join(f"| {r} | x |\n" for r in T.PLAN_ROWS + ("R1-T1-TASL-ENV",)))
    (work / "sweep2/t1_tasl").mkdir(parents=True)
    (work / "sweep2/t1_tasl/g1b_tasl.py").write_text("code = 1\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "C")
    c = _git(work, "rev-parse", "HEAD")
    spec = {"paper": {"commit": c}, "run_id": "r"}
    spec_path = work / "sweep2/t1_tasl/g1b_tasl_spec.json"
    spec_path.write_text(json.dumps(spec))
    (work / "docs/r1/authorizations/g1b_t1_tasl_20991231.md").write_text(f"paper_commit: {c}\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "M")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    return work, spec, spec_path, c


def _publish(work, msg, files):
    for rel, text in files.items():
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_text(text)
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", msg)
    _git(work, "push", "-q", "origin", "HEAD:main")
    _git(work, "fetch", "-q", "origin")
    return _git(work, "rev-parse", "HEAD")


def test_tasl_launch_binding_is_satisfiable_where_the_s2c5_binding_is_not(tmp_path):
    """The S2-C5 binding needs HEAD == the commit the note names and that commit to descend from the main carrying the
    note: unsatisfiable. The TASL binding launches from the published checkout holding the signed spec, with the named
    commit as a code-equal ancestor."""
    work, spec, spec_path, c = _launch_repo(tmp_path)
    rows = T.PLAN_ROWS + ("R1-T1-TASL-ENV",)
    out = T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    assert out["paper_commit"] == c and out["head"] == out["main"] == _git(work, "rev-parse", "HEAD")
    with pytest.raises(lib.Stop, match="exactly the spec's paper commit"):
        lib.verify_launch(work, spec, rows)
    _git(work, "checkout", "-q", c)                    # at the named commit, main (with the note) does not descend
    with pytest.raises(lib.Stop, match="descend from published main"):
        lib.verify_launch(work, spec, rows)
    with pytest.raises(T.Stop, match="not the committed"):            # and the signed spec is not in that tree
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    _git(work, "checkout", "-q", "main")


def test_main_may_move_on_after_the_signature(tmp_path):
    """M1 of the note review: no code freeze. Main gains unrelated code and a second note for the same run; the
    checkout at the signed launch commit still binds, and a checkout at the new main does not (its code differs)."""
    work, spec, spec_path, c = _launch_repo(tmp_path)
    rows = T.PLAN_ROWS + ("R1-T1-TASL-ENV",)
    m2 = _git(work, "rev-parse", "HEAD")
    _publish(work, "unrelated code", {"r1/c3/release.py": "x = 1\n",
                                      "docs/r1/authorizations/g1b_t1_tasl_20991232.md": "second note\n"})
    with pytest.raises(T.Stop, match="differs from the paper commit"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    _git(work, "checkout", "-q", m2)
    out = T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    assert out["head"] == m2 and out["main"] != m2


def test_tasl_launch_binding_refusals(tmp_path):
    work, spec, spec_path, c = _launch_repo(tmp_path)
    rows = T.PLAN_ROWS + ("R1-T1-TASL-ENV",)
    with pytest.raises(T.Stop, match="PLAN row R1-X"):
        T.verify_launch_tasl(work, spec, rows + ("R1-X",), spec_path=spec_path)
    with pytest.raises(T.Stop, match="full paper commit"):
        T.verify_launch_tasl(work, {"paper": {"commit": "abc"}}, rows, spec_path=spec_path)
    with pytest.raises(T.Stop, match="not the spec's paper repository"):
        T.verify_launch_tasl(work, {**spec, "paper": {**spec["paper"], "repo": "https://github.com/x/y.git"}}, rows,
                             spec_path=spec_path)
    # the URL git uses counts, not the configured one: an insteadOf rewrite to another remote is refused
    _git(work, "config", "remote.origin.url", "https://github.com/x/y.git")
    _git(work, "config", f"url.{tmp_path / 'origin.git'}.insteadOf", "https://github.com/x/y.git")
    with pytest.raises(T.Stop, match="not the spec's paper repository"):
        T.verify_launch_tasl(work, {**spec, "paper": {**spec["paper"], "repo": "https://github.com/x/y.git"}}, rows,
                             spec_path=spec_path)
    _git(work, "config", "--unset", f"url.{tmp_path / 'origin.git'}.insteadOf")
    _git(work, "config", "remote.origin.url", str(tmp_path / "origin.git"))
    outside = tmp_path / "spec.json"
    outside.write_bytes(spec_path.read_bytes())
    with pytest.raises(T.Stop, match="committed in the repository"):
        T.verify_launch_tasl(work, spec, rows, spec_path=outside)
    loose = work / "sweep2/t1_tasl/loose_spec.json"                    # untracked, not code: only the spec check
    loose.write_bytes(spec_path.read_bytes())
    with pytest.raises(T.Stop, match="not the committed"):
        T.verify_launch_tasl(work, spec, rows, spec_path=loose)
    (work / "sweep2/t1_tasl/shadow.py").write_text("x = 1\n")
    with pytest.raises(T.Stop, match="untracked code files"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    (work / "sweep2/t1_tasl/shadow.py").rename(tmp_path / "shadow.py")
    (work / ".git" / "info" / "exclude").write_text("*.py[cod]\n__pycache__/\n")   # as the repository's .gitignore
    (work / "sweep2/t1_tasl/json.pyc").write_bytes(b"\0")                         # ignored, sourceless, importable
    with pytest.raises(T.Stop, match="untracked code files"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    (work / "sweep2/t1_tasl/json.pyc").rename(tmp_path / "json.pyc")
    (work / "sweep2/t1_tasl/__pycache__").mkdir()
    (work / "sweep2/t1_tasl/__pycache__/g1b_tasl.cpython-312.pyc").write_bytes(b"\0")    # a normal cache is fine
    assert T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)["head"]
    (work / "sweep2/t1_tasl/g1b_tasl.py").write_text("code = 2\n")       # tracked-dirty
    with pytest.raises(T.Stop, match="tracked-clean"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    _git(work, "checkout", "-q", "--", "sweep2/t1_tasl/g1b_tasl.py")
    _git(work, "commit", "-q", "--allow-empty", "-m", "local, not pushed")
    with pytest.raises(T.Stop, match="must be published"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    _git(work, "reset", "-q", "--hard", "origin/main")
    with pytest.raises(T.Stop, match="ancestor of the launch checkout"):
        T.verify_launch_tasl(work, {"paper": {"commit": "f" * 40}}, rows, spec_path=spec_path)
    # another spec (G.4) is not excluded: a change to it after the paper commit refuses
    _publish(work, "g4 spec change", {"sweep2/t1_tasl/g4_tasl_spec.json": "{}\n"})
    with pytest.raises(T.Stop, match="differs from the paper commit"):
        T.verify_launch_tasl(work, spec, rows, spec_path=spec_path)
    # a docs-only and own-spec-only change after the paper commit is fine; a stale fetch is not
    spec2 = {"paper": {"commit": _git(work, "rev-parse", "HEAD")}, "run_id": "r2"}
    _publish(work, "spec + docs", {"sweep2/t1_tasl/g1b_tasl_spec.json": json.dumps(spec2), "docs/r1/notes.md": "n\n"})
    assert T.verify_launch_tasl(work, spec2, rows, spec_path=spec_path)["paper_commit"] == spec2["paper"]["commit"]
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True, capture_output=True)
    _publish(other, "later", {"docs/r1/later.md": "x\n"})
    with pytest.raises(T.Stop, match="fetch published main"):
        T.verify_launch_tasl(work, spec2, rows, spec_path=spec_path)


def test_the_spec_exclusion_is_literal(tmp_path):
    """A spec path with glob characters excludes only itself, never code (pathspec literal)."""
    work, spec, spec_path, c = _launch_repo(tmp_path)
    odd = work / "sweep2/t1_tasl/g1b_tasl*"
    odd.write_bytes(spec_path.read_bytes())
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "odd spec copy")
    c2 = _git(work, "rev-parse", "HEAD")
    spec2 = {**spec, "paper": {"commit": c2}}
    odd.write_text(json.dumps(spec2))
    (work / "sweep2/t1_tasl/g1b_tasl.py").write_text("code = 99\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "code change hidden by a glob?")
    _git(work, "push", "-q", "origin", "HEAD:main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(T.Stop, match="differs from the paper commit"):
        T.verify_launch_tasl(work, spec2, T.PLAN_ROWS + ("R1-T1-TASL-ENV",), spec_path=odd)


def test_repo_id_normalises_github_remotes():
    want = T._repo_id("https://github.com/dowlingwong/Agent_paper_B.git")
    assert want == "dowlingwong/agent_paper_b"
    for url in ("git@github.com:dowlingwong/Agent_paper_B.git", "ssh://git@github.com/dowlingwong/Agent_paper_B",
                "https://github.com/dowlingwong/Agent_paper_B/"):
        assert T._repo_id(url) == want
    assert T._repo_id("https://github.com/dowlingwong/other.git") != want
