"""The node-expansion G.1b spec on TASL-2 (sweep2/t1_tasl/g1b_tasl.py, schema g1b_tasl_x_job/v1; R1-T1-NODE-EXPANSION):
its validation, the per-node harness pins and CPU sets, the census values it binds (against the census records on
main), the CPU-set lease, the engine's CPU-only override, the pip-freeze environment, its own assembly and summary,
the note (draft and strict, the per-node gates, the publication row) and its launch; the seven-node and autoresearch
specs unchanged beside it. R1-TASL2-CPU: no CPU set containing TASL-2 CPUs 8-11, the replacement sets of Titanic and
Forest Cover, and the gate on each replacement set's fixed-seed determinism check record.

Synthetic only: no host, no run, no label, no evaluation value (the engine, nvidia-smi and the setup are replaced; the
census records are read for their pins and wall times only). AI-assisted.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT / "sweep2" / "g1b"))
import g1b_tasl as T  # noqa: E402
import g1b_lib as lib  # noqa: E402
from test_t1_tasl_g1b import _write_part  # noqa: E402

X_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_x_spec.json"
X_SHIPPED = json.loads(X_PATH.read_text())
SEVEN_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_spec.json"
AR_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_ar_spec.json"
# the specs the signed G.1b notes bind: unchanged by the node-expansion kind
SEVEN_SIGNED_SHA = "7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7"
AR_SIGNED_SHA = hashlib.sha256(AR_PATH.read_bytes()).hexdigest()
REP = ROOT / "docs" / "r1" / "reports" / "tasl_chain_20261122"
NOTE_DRAFT = ROOT / "docs" / "r1" / "proposals" / "G1B_X_T1_TASL_NOTE_DRAFT_20261126.md"
ENV_ROW = "R1-EXP-ENV-TEST"
REVIEW = T.X_REVIEW_RECORD
CAPTURES = {"mlgym_titanic": "TITANIC_U2_RESULT_20261125_RETRY_captures",
            "mlgym_metamaze": "METAMAZE_U2_RESULT_20261125_captures",
            "gc7rc_etth1": "ETTH1_U2_RESULT_20261125_captures",
            "gc7rc_forestcover": "FORESTCOVER_U2_RESULT_20261125_captures"}
RECORD_KEYS = {"B1": "s000_baseline", "B2": "B2", "E1": "E1", "E2": "E2", "E3": "E3", "E4": "E4"}


def filled(tmp_path: Path | None = None) -> dict:
    """The shipped spec with paper.commit filled; with tmp_path, the host paths and checkouts moved there."""
    spec = copy.deepcopy(X_SHIPPED)
    spec["paper"]["commit"] = "3" * 40
    if tmp_path is not None:
        host = spec["hosts"]["TASL-2"]
        for key in ("base", "runs_root", "sealed_root"):
            host[key] = str(tmp_path / key)
        host["data_root"] = host["base"] + "/data"
        for node in spec["nodes"]:
            node["harness"]["dir"] = str(tmp_path / "checkouts" / node["node"])
    return spec


def node(spec: dict, name: str) -> dict:
    return next(n for n in spec["nodes"] if n["node"] == name)


# ============================================================================================ the other kinds
def test_the_signed_seven_node_and_ar_specs_are_unchanged_and_validate():
    assert hashlib.sha256(SEVEN_PATH.read_bytes()).hexdigest() == SEVEN_SIGNED_SHA
    seven = T.load_spec(SEVEN_PATH)
    assert T.validate_spec(copy.deepcopy(seven), launch=True)["run_id"] == "g1b-tasl-20261121-b"
    note = T._note_fields((ROOT / "docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md").read_bytes())
    assert note["spec_sha256"] == AR_SIGNED_SHA
    T.validate_spec(T.load_spec(AR_PATH), launch=True)
    assert not T.is_x(seven) and T.spec_hosts(seven) == T.HOSTS


def test_the_seven_node_projection_is_unchanged_by_the_expansion_fields():
    proj = T.projection(T.load_spec(SEVEN_PATH))
    assert proj["estimate"]["total_gpu_hours"] == 28.262 and proj["estimate"]["cpu_core_hours"] == 7.168
    assert "hours_by_record" not in proj["estimate"]["per_node"]["mlgym_houseprice"]


# ============================================================================================ the shipped spec
def test_shipped_spec_validates_and_its_launch_needs_the_paper_commit():
    if X_SHIPPED["paper"]["commit"].startswith("PENDING"):
        with pytest.raises(T.Stop, match="paper.commit"):
            T.validate_spec(copy.deepcopy(X_SHIPPED), launch=True)
        T.validate_spec(copy.deepcopy(X_SHIPPED))
    loaded = T.validate_spec(filled(), launch=True)
    proj = loaded["projection"]
    assert loaded["run_id"].startswith(T.X_RUN_PREFIX) and set(proj["estimate"]["per_node"]) == set(T.X_NODES)
    assert proj["estimate"]["total_gpu_hours"] == 0 and proj["within_cap"] and proj["cap_total_gpu_hours"] == 40
    assert all(v["device"] == "cpu" and v["runs"] == 460 for v in proj["estimate"]["per_node"].values())
    assert proj["estimate"]["cpu_node_hours_by_record"] == pytest.approx(43.584, abs=0.01)


def test_shipped_spec_pins_are_the_census_records_on_main():
    """Each node's pins equal its U2 census capture's pins.json, its census times equal the census run records'
    wall fields (B1 = s000_baseline), and the census record and capture sums are the files on main."""
    for n in X_SHIPPED["nodes"]:
        caps = REP / CAPTURES[n["node"]]
        pins = json.loads((caps / "pins.json").read_text())
        for key in ("node_spec_sha256", "committed_pin_sha256", "edits_manifest_sha256", "data_manifest_sha256",
                    "spec_path"):
            assert n[key] == pins[key], (n["node"], key)
        assert pins.get("node_dir", n["node_dir"]) == n["node_dir"]
        for key, rec in RECORD_KEYS.items():
            run = json.loads((caps / "run_records" / f"{rec}.json").read_text())
            assert run["limits"]["cpu_list"] == T.cpu_list(T.node_census_cpus(n)), n["node"]
            assert n["census_seconds"][key] == run["elapsed_seconds_info_only"], (n["node"], key)
        if n.get("cpu_replacement"):     # the census baseline's result channel, which the determinism check reproduces
            want = n["cpu_replacement"]["determinism_check"]["census_baseline_result_channel_sha256"]
            for rec in ("s000_baseline", "B2"):
                assert lib._sha_file(caps / "result_channels" / f"{rec}.txt") == want, (n["node"], rec)
                run = json.loads((caps / "run_records" / f"{rec}.json").read_text())
                assert run["isolation"]["result_channel_sha256"] == want
                assert run["environment_applied"]["AR_TRAIN_SEED"] == run["environment_applied"]["AR_SPLIT_SEED"] \
                    == "8001"
        assert lib._sha_file(ROOT / n["census_record"]) == n["census_record_sha256"]
        assert lib._sha_file(ROOT / n["census_captures_sha256sums"]["path"]) == n["census_captures_sha256sums"]["sha256"]
        for ref in ("kit_record", "kit_review"):
            assert lib._sha_file(ROOT / n[ref]["path"]) == n[ref]["sha256"]
    freeze = ROOT / "sweep2" / "g1b" / X_SHIPPED["envs"]["venv_jax"]["freeze"]
    assert freeze.read_bytes() == (REP / CAPTURES["mlgym_metamaze"] / "venv_jax.freeze.txt").read_bytes()
    assert lib._sha_file(freeze) == X_SHIPPED["envs"]["venv_jax"]["sha256"]


def test_shipped_spec_cpu_sets_engine_admission_and_gates():
    spec = filled()
    assert {n["node"]: n["cpus"] for n in spec["nodes"]} == {
        "mlgym_titanic": "12-15", "mlgym_metamaze": "0-3", "gc7rc_etth1": "16-31", "gc7rc_forestcover": "4-7"}
    assert {n["node"]: T.node_census_cpus(n) for n in spec["nodes"]} == {
        "mlgym_titanic": "8-11", "mlgym_metamaze": "0-3", "gc7rc_etth1": "16-31", "gc7rc_forestcover": "8-11"}
    sets = [set(T.cpu_list(n["cpus"])) for n in spec["nodes"]]
    assert all(not (s & T.X_EXCLUDED_CPUS) for s in sets)                     # R1-TASL2-CPU
    assert all(not (a & b) for i, a in enumerate(sets) for b in sets[i + 1:])   # disjoint: all four can run at once
    for name in ("mlgym_titanic", "gc7rc_forestcover"):
        rep = node(spec, name)["cpu_replacement"]
        assert rep["authority"] == "R1-TASL2-CPU" and rep["census_cpus"] == "8-11" and "max_attempts" not in node(spec, name)
        assert len(T.cpu_list(node(spec, name)["cpus"])) == len(T.cpu_list(rep["census_cpus"])) == 4
        assert rep["stability_record"] == {"path": T.X_STABILITY_RECORD, "sha256": lib._sha_file(ROOT / T.X_STABILITY_RECORD)}
    assert {n["node"]: n["cpu_only"] for n in spec["nodes"]} == {
        "mlgym_titanic": "harness_list", "mlgym_metamaze": "census_override", "gc7rc_etth1": "census_override",
        "gc7rc_forestcover": "census_override"}
    assert {n["node"]: n["gate_requires"] for n in spec["nodes"]} == {
        "mlgym_titanic": ["host_check", "cpu_determinism"], "mlgym_metamaze": ["host_check", "env_row"],
        "gc7rc_etth1": ["host_check", "review"], "gc7rc_forestcover": ["host_check", "review", "cpu_determinism"]}
    assert sorted(T.cpu_lease_path(spec, n) for n in spec["nodes"]) == [
        "~/r1_locks/cpus-0-3.lock", "~/r1_locks/cpus-12-15.lock", "~/r1_locks/cpus-16-31.lock", "~/r1_locks/cpus-4-7.lock"]
    for n in spec["nodes"]:
        assert T.node_lease(spec, n) == T.cpu_lease_path(spec, n)
        assert 3 * n["slowest_census_seconds"] <= 3 * lib.RUN_SECONDS_CEILING


def _set(path, value):
    def edit(spec):
        cur = spec
        keys = path.split(".")
        for k in keys[:-1]:
            cur = cur[int(k)] if isinstance(cur, list) else cur[k]
        if value is _DEL:
            del cur[keys[-1]]
        else:
            cur[keys[-1]] = value
    return edit


_DEL = object()


@pytest.mark.parametrize("edit, match", [
    (_set("run_id", "g1b-tasl-20261121-b"), "expansion spec's own"),
    (_set("run_id", "g1b-tasl-x"), "expansion spec's own"),
    (_set("harness.commit", "c025f89aeafc2199bf3487b4bcaa16678273c702"), "per node"),
    (_set("caps.max_total_gpu_hours", 41), "at most 40"),
    (_set("caps.authority", "R1-G1B-CAP"), "R1-T1-NODE-EXPANSION"),
    (_set("note_rule", "R1-G1B-NOTE2-DECISIONS"), "note_rule"),
    (_set("estimate.census_host", "TASL-7"), "census_host"),
    (_set("envs.jax312", {"freeze": "env/jax312.freeze.txt", "python": "3.12.16", "freeze_tool": "uv",
                          "sha256": "80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1"}), "among"),
    (_set("envs.venv_jax.freeze_tool", "uv"), "freeze_tool must be pip"),
    (_set("envs.venv_jax.sha256", "0" * 64), "committed census freeze"),
    (_set("hosts.TASL-2.harness_dir", "/x/harness"), "one checkout per node"),
    (_set("hosts.TASL-2.isolation_host_check", {"record": "x", "sha256": "0" * 64}), "gate in the note"),
    (_set("nodes.0.node", "mlab_imdb"), "not R1-T1-NODE-EXPANSION candidates"),
    (_set("nodes.0.harness.commit", "abc"), "harness.commit"),
    (_set("nodes.0.harness.dir", "rel/dir"), "absolute"),
    (_set("nodes.0.harness.branch", ""), "branch"),
    (_set("nodes.1.harness.dir", "/home/dowling/r1_tracks/t1_tasl_x/harness_titanic"), "two harness pins"),
    (_set("nodes.1.harness.dir", "/home/dowling/r1_tracks/t1_tasl_x/harness_titanic/sub"), "lies inside"),
    (_set("nodes.0.harness.dir", "/home/dowling/r1_tracks/t1_tasl_x/runs/h"), "overlap"),
    (_set("nodes.0.run_seconds", 137.714), "census B1"),
    (_set("nodes.0.slowest_census_seconds", 147.81), "census B1|slowest"),
    (_set("nodes.0.census_seconds.E3", 301.0), r"\(0, 300"),
    (_set("nodes.0.census_seconds.E5", 1.0), "exactly the census records"),
    (_set("nodes.0.census_record_sha256", "x"), "census_record_sha256"),
    (_set("nodes.0.census_record", "/abs/record.md"), "docs/r1/reports/"),
    (_set("nodes.0.cpu_only", "maybe"), "cpu_only"),
    (_set("nodes.1.cpus", "2-5"), "overlap without being equal"),
    (_set("nodes.1.device", "tpu"), "cpu or gpu"),
    (_set("nodes.0.gate_requires", ["review"]), "host_check"),
    (_set("nodes.0.gate_requires", ["host_check", "vote"]), "host_check and only"),
    (_set("nodes.1.gate_requires", ["host_check"]), "needs env_row"),
    (_set("nodes.0.n_edits", 5), "uniform"),
    (_set("timeout_decision.basis", "census_baseline_x3"), "census_slowest_x3"),
    (_set("census.commit", "47d2a39d"), "census.commit"),
    (_set("review_record", "docs/r1/reviews/TITANIC_KIT_REVIEW_20261125.md"), "review_record"),
    (_set("cpu_preflight.max_busy", 0.9), "cpu_preflight"),
    (_set("cpu_preflight.seconds", 1), "cpu_preflight"),
    (_set("cpu_preflight", _DEL), "cpu_preflight"),
    # R1-TASL2-CPU: no set containing CPUs 8-11, the replacement sets and their determinism check
    (_set("nodes.0.cpus", "8-11"), r"contains TASL-2 CPUs \[8, 9, 10, 11\].*R1-TASL2-CPU"),
    (_set("nodes.1.cpus", "8-11"), r"contains TASL-2 CPUs \[8, 9, 10, 11\]"),
    (_set("nodes.2.cpus", "11-26"), r"contains TASL-2 CPUs \[11\]"),
    (_set("nodes.3.cpus", "4-8"), r"contains TASL-2 CPUs \[8\]"),
    (_set("hosts.TASL-2.cpus", "8-15"), r"hosts.TASL-2.cpus 8-15 contains CPUs 8-11"),
    (_set("nodes.0.max_attempts", 2), "no attempt cap"),
    (_set("nodes.1.max_attempts", 2), "no attempt cap"),
    (_set("nodes.0.cpus", "0-7"), "census set's size"),
    (_set("nodes.0.cpus", "16-19"), "one of the CPU groups the TASL-2 CPU stability record passed"),
    (_set("nodes.0.cpu_replacement", _DEL), "cpu_determinism gate belongs to a replacement CPU set"),
    (_set("nodes.0.gate_requires", ["host_check"]), "its gate needs cpu_determinism"),
    (_set("nodes.3.gate_requires", ["host_check", "review"]), "its gate needs cpu_determinism"),
    (_set("nodes.1.gate_requires", ["host_check", "env_row", "cpu_determinism"]), "belongs to a replacement CPU set"),
    (_set("nodes.0.cpu_replacement.authority", "R1-T1-NODE-EXPANSION"), "authority must be R1-TASL2-CPU"),
    (_set("nodes.0.cpu_replacement.census_cpus", "12-15"), "only a census set containing CPUs 8-11 is replaced"),
    (_set("nodes.0.cpu_replacement.census_cpus", "8-15"), "census set's size"),
    (_set("nodes.0.cpu_replacement.extra", 1), "must hold exactly"),
    (_set("nodes.0.cpu_replacement.stability_record.path", "docs/r1/reports/x.md"), "stability_record.path"),
    (_set("nodes.0.cpu_replacement.stability_record.sha256", "0" * 64), "not the sha256 of"),
    (_set("nodes.3.cpu_replacement.determinism_check.runs", 1), "runs must be 2"),
    (_set("nodes.3.cpu_replacement.determinism_check.record", "docs/r1/reports/x_12-15.md"), r"ends in _4-7\.md"),
    (_set("nodes.3.cpu_replacement.determinism_check.record", "/abs/x_4-7.md"), "under docs/r1/reports/"),
    (_set("nodes.3.cpu_replacement.determinism_check.census_baseline_result_channel_sha256", "x"),
     "census_baseline_result_channel_sha256"),
    (_set("nodes.3.cpu_replacement.determinism_check.extra", 1), "determinism_check must hold exactly"),
    (_set("nodes.2.cpu_census_conditions", []), "cpu_census_conditions"),
])
def test_x_spec_refusals(edit, match):
    spec = filled()
    edit(spec)
    with pytest.raises(T.Stop, match=match):
        T.validate_spec(spec, launch=True)


def test_two_replacement_sets_cannot_share_a_determinism_record():
    spec = filled()
    fc, ti = node(spec, "gc7rc_forestcover"), node(spec, "mlgym_titanic")
    fc["cpus"] = "12-15"                                  # an equal set is allowed (the lease runs them in turn) ...
    fc["cpu_replacement"]["determinism_check"]["record"] = ti["cpu_replacement"]["determinism_check"]["record"]
    with pytest.raises(T.Stop, match="two replacement CPU sets name one determinism check record"):
        T.validate_spec(spec, launch=True)
    fc["cpu_replacement"]["determinism_check"]["record"] = "docs/r1/reports/x/FC_12-15.md"
    T.validate_spec(spec, launch=True)                    # ... with its own record


def test_the_replacement_sets_are_the_stability_record_passing_groups_and_the_row_is_on_main():
    """R1-TASL2-CPU on this checkout's PLAN; the record passed 0-3, 4-7 and 12-15 (3 of 3) and failed 8-11 (3 of 3)."""
    plan = (ROOT / "docs/r1/PLAN.md").read_text()
    row = [ln for ln in plan.splitlines() if ln.startswith("| R1-TASL2-CPU |")]
    assert len(row) == 1 and "no R1 job on TASL-2 uses CPUs 8-11" in row[0] and "same size" in row[0]
    assert "fixed-seed determinism check before its first use" in row[0] and "R1-TASL2-CPU" in T.X_PLAN_ROWS
    text = (ROOT / T.X_STABILITY_RECORD).read_text()
    for group in T.X_STABLE_SETS:
        a, b = group.split("-")
        assert f"| **CPUs {a}–{b}** | **PASS 3/3**" in text, group
    assert "| **CPUs 8–11** | **FAIL 3/3**" in text
    assert "6,100,000 kHz for cores 4–5 (CPUs 8–11)" in text and "5,800,000 kHz for cores 0–3, 6, 7" in text


def test_a_gpu_node_runs_on_the_host_cpus_away_from_the_cpu_sets():
    spec = filled()
    n = node(spec, "gc7rc_etth1")
    n["device"] = "gpu"
    del n["cpus"], n["cpu_only"]
    with pytest.raises(T.Stop, match="overlaps the cpus of the host's GPU jobs"):      # MetaMaze on 0-3, host 0-7
        T.validate_spec(copy.deepcopy(spec), launch=True)
    spec["hosts"]["TASL-2"]["cpus"] = "4-7"                                      # Forest Cover's set
    with pytest.raises(T.Stop, match="overlaps the cpus of the host's GPU jobs"):
        T.validate_spec(copy.deepcopy(spec), launch=True)
    spec["hosts"]["TASL-2"]["cpus"] = "16-23"                                    # ETTh1's E-cores, now free
    loaded = T.validate_spec(copy.deepcopy(spec), launch=True)
    assert loaded["projection"]["estimate"]["total_gpu_hours"] > 0
    assert T.node_lease(spec, n) == "~/r1_locks/gpu0.lock"
    n["cpus"] = "16-23"
    with pytest.raises(T.Stop, match="no cpus, no cpu_only"):
        T.validate_spec(spec, launch=True)


def test_the_seven_node_and_ar_kinds_refuse_the_expansion_fields():
    seven = T.load_spec(SEVEN_PATH)
    bad = copy.deepcopy(seven)
    bad["nodes"].append(copy.deepcopy(node(filled(), "mlgym_titanic")))
    with pytest.raises(T.Stop, match="not T1 nodes"):
        T.validate_spec(bad)
    with pytest.raises(T.Stop, match="must be gpu|must be cpu"):
        b2 = copy.deepcopy(seven)
        b2["nodes"][0]["device"] = "cpu"
        T.validate_spec(b2)


# ============================================================================================ the node job
@pytest.fixture
def job(tmp_path, monkeypatch):
    spec = filled(tmp_path)
    spec_path = tmp_path / "x_spec.json"
    spec_path.write_text(json.dumps(spec))
    calls, leases = [], []
    monkeypatch.setattr(T, "host_identity", lambda s, h: {"host": h, "hostname": "TASL-2"})
    monkeypatch.setattr(T, "ptrace_scope", lambda: 1)
    monkeypatch.setattr(T, "scope_cgroup", lambda: {"cgroup_parent": "/sys/fs/cgroup/scope"})
    seen_checkout = []

    def checkout(s, h, git=None, node=None):
        seen_checkout.append(node["node"] if node else None)
        return {"dir": T.node_harness_dir(s, node), "commit": T.node_harness_commit(s, node)}
    monkeypatch.setattr(T, "harness_checkout", checkout)
    monkeypatch.setattr(T, "environment", lambda s, h, n: {"name": n["env"], "python_version": "3.12.16"})
    monkeypatch.setattr(T, "check_affinity", lambda s, n, affinity=None: T.cpu_list(T.node_cpus(s, n)))
    monkeypatch.setattr(os, "environ", dict(os.environ))
    busy = []
    monkeypatch.setattr(T, "cpu_busy_check", lambda s, n, when, **kw: busy.append(when) or {"when": when, "busy": {}})
    real_lease = T.gpu_lease

    def lease(path, *a):
        leases.append(path)
        return real_lease(str(tmp_path / "locks" / Path(path).name), *a)
    monkeypatch.setattr(T, "gpu_lease", lease)

    def engine(argv, **kw):
        calls.append((argv, kw))
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        part = next(p for p in lib.PARTS if p[0] == Path(argv[argv.index("--out") + 1]).name)
        _write_part(Path(argv[argv.index("--out") + 1]), chunk["node"], part)
        return subprocess.CompletedProcess(argv, 0, "", "")

    def smi(argv, **kw):
        raise AssertionError("a CPU node never calls nvidia-smi")
    setup = lambda harness, node, base, out: {"data_root": str(base / "data"), "setup": "x"}  # noqa: E731
    return spec, spec_path, calls, engine, smi, setup, leases, seen_checkout


def _attempt(spec, name, n=1):
    return Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / name / f"attempt-{n}"


@pytest.mark.parametrize("name, admission", [("mlgym_titanic", "harness_list"), ("mlgym_metamaze", "census_override"),
                                             ("gc7rc_forestcover", "census_override")])
def test_x_node_job_end_to_end(job, name, admission):
    spec, spec_path, calls, engine, smi, setup, leases, seen_checkout = job
    n = node(spec, name)
    rec = T.run_node_job(spec_path, name, smi=smi, engine=engine, setup=setup)
    assert rec["runs"]["written"] == 460 and rec["stop"] is None and rec["attempt"] == 1
    assert rec["spec_schema"] == T.X_SCHEMA and rec["harness_commit"] == n["harness"]["commit"]
    assert rec["cpu_only"] == admission and rec["cpus"] == n["cpus"] and rec["device"] == "cpu"
    assert rec["census_cpus"] == T.node_census_cpus(n) == ("8-11" if "cpu_replacement" in n else n["cpus"])
    assert rec["cpu_replacement"] == ("R1-TASL2-CPU" if "cpu_replacement" in n else None)
    assert rec["timeout_basis"] == {"decision": "census_slowest_x3", "seconds": n["slowest_census_seconds"],
                                    "timeout_s": 3 * n["slowest_census_seconds"]}
    assert leases == [f"~/r1_locks/cpus-{n['cpus']}.lock"] and seen_checkout == [name]
    assert rec["gpu"] == {"device": "cpu"} and rec["lease"]["lease"].endswith(f"cpus-{n['cpus']}.lock")
    assert [r["when"] for r in rec["cpu_preflight"]] == ["before the attempt"] + [f"before {p[0]}" for p in lib.PARTS]
    for argv, kw in calls:
        assert argv[0] == spec["hosts"]["TASL-2"]["env_python"][n["env"]] and "--gpu-uuid" not in argv
        assert kw["cwd"] == Path(n["harness"]["dir"]) and kw["env"]["CUDA_VISIBLE_DEVICES"] == ""
        if admission == "census_override":
            assert argv[1:4] == ["-c", T.X_ENGINE_OVERRIDE, name]
        else:
            assert argv[1:3] == ["-m", "autoresearch.trackg.noise_floor"]
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        assert chunk["device"] == "cpu" and chunk["measured_run_seconds"] == n["slowest_census_seconds"]
        assert chunk["committed_pin_sha256"] == n["committed_pin_sha256"] and chunk["stop_on_timeout"] is True


def test_two_nodes_on_one_cpu_set_cannot_run_at_once(job, tmp_path):
    spec, spec_path, calls, engine, smi, setup, leases, _ = job
    import fcntl
    lock = tmp_path / "locks" / "cpus-4-7.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(T.Stop, match="CPU-set lease .* is held by another job \\(one expansion node per CPU set"):
            T.run_node_job(spec_path, "gc7rc_forestcover", smi=smi, engine=engine, setup=setup)
        rec = T.run_node_job(spec_path, "mlgym_titanic", smi=smi, engine=engine, setup=setup)    # another set
        assert rec["stop"] is None
    refusals = list((Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "_refusals").iterdir())
    assert len(refusals) == 1 and refusals[0].name.startswith("gc7rc_forestcover-")


def _fake_engine(tmp_path: Path) -> Path:
    """A stand-in harness whose engine guard is the one of autoresearch.trackg.noise_floor at c025f89a."""
    pkg = tmp_path / "fake_harness" / "src" / "autoresearch" / "trackg"
    pkg.mkdir(parents=True)
    for d in (pkg.parent, pkg):
        (d / "__init__.py").write_text("")
    (pkg / "noise_floor.py").write_text(
        "import json, sys\n"
        "CPU_ONLY_NODES = frozenset({'mlgym_houseprice'})\n"
        "def main(argv=None):\n"
        "    a = list(sys.argv[1:] if argv is None else argv)\n"
        "    data = json.load(open(a[a.index('--chunk') + 1]))\n"
        "    if data.get('device') == 'cpu' and data['node'] not in CPU_ONLY_NODES:\n"
        "        print('STOP: not a CPU-only node'); return 2\n"
        "    print('admitted', data['node'], sorted(CPU_ONLY_NODES), a[-1]); return 0\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n")
    return tmp_path / "fake_harness"


def test_the_engine_override_widens_the_list_for_its_own_node_only(tmp_path):
    harness = _fake_engine(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1")

    def run(argv_head, chunk_node):
        chunk = tmp_path / f"chunk_{chunk_node}.json"
        chunk.write_text(json.dumps({"node": chunk_node, "device": "cpu"}))
        return subprocess.run([sys.executable, *argv_head, "--chunk", str(chunk), "--out", "OUT"], cwd=harness,
                              env=env, capture_output=True, text=True)
    plain = run(["-m", "autoresearch.trackg.noise_floor"], "mlgym_metamaze")
    assert plain.returncode == 2 and "not a CPU-only node" in plain.stdout       # the pin's guard, unchanged
    ok = run(["-c", T.X_ENGINE_OVERRIDE, "mlgym_metamaze"], "mlgym_metamaze")
    assert ok.returncode == 0 and ok.stdout.split() == ["admitted", "mlgym_metamaze", "['mlgym_houseprice',",
                                                        "'mlgym_metamaze']", "OUT"]
    other = run(["-c", T.X_ENGINE_OVERRIDE, "mlgym_metamaze"], "gc7rc_etth1")
    assert other.returncode == 1 and "another node" in other.stderr


def test_the_pip_freeze_environment(tmp_path, monkeypatch):
    spec = filled(tmp_path)
    n = node(spec, "mlgym_metamaze")
    freeze = (ROOT / "sweep2" / "g1b" / "env" / "venv_jax.freeze.txt").read_text()
    seen = []

    def sh(argv, **kw):
        seen.append(argv)
        if argv[1:] == ["-c", "import sys; print(sys.version.split()[0])"]:
            return subprocess.CompletedProcess(argv, 0, "3.12.16\n", "")
        return subprocess.CompletedProcess(argv, 0, freeze, "")
    out = T.environment(spec, "TASL-2", n, sh=sh)
    assert seen[0] == [spec["hosts"]["TASL-2"]["env_python"]["venv_jax"], "-m", "pip", "--disable-pip-version-check",
                       "freeze"]
    assert out["packages"] == 56 and out["freeze_sha256"] == spec["envs"]["venv_jax"]["sha256"]
    seen.clear()
    T.environment(spec, "TASL-2", node(spec, "mlgym_titanic"),
                  sh=lambda argv, **kw: (seen.append(argv), subprocess.CompletedProcess(
                      argv, 0, "3.12.16\n" if "-c" in argv else
                      (ROOT / "sweep2/g1b/env/torch312.freeze.txt").read_text(), ""))[1])
    assert seen[0][:3] == [spec["hosts"]["TASL-2"]["uv"], "pip", "freeze"]
    with pytest.raises(T.Stop, match="differs from the census freeze"):
        T.environment(spec, "TASL-2", n, sh=lambda argv, **kw: subprocess.CompletedProcess(
            argv, 0, "3.12.16\n" if "-c" in argv else freeze.replace("jax==0.4.35", "jax==0.4.36"), ""))


def test_harness_checkout_is_the_node_own(tmp_path):
    spec = filled(tmp_path)
    n = node(spec, "gc7rc_etth1")

    def git(argv, **kw):
        if argv[-2:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, n["harness"]["commit"] + "\n", "")
        return subprocess.CompletedProcess(argv, 0, "?? nodes/gc7rc_etth1/data\n", "")
    out = T.harness_checkout(spec, "TASL-2", git=git, node=n)
    assert out == {"dir": n["harness"]["dir"], "commit": n["harness"]["commit"]}
    with pytest.raises(T.Stop, match="not the pin"):
        T.harness_checkout(spec, "TASL-2", git=git, node=node(spec, "mlgym_titanic"))


def test_x_seal_assemble_summarise_are_its_own(job, tmp_path, monkeypatch):
    spec, spec_path, calls, engine, smi, setup, *_ = job
    receipts = []
    for name in ("mlgym_titanic", "gc7rc_etth1"):
        T.run_node_job(spec_path, name, smi=smi, engine=engine, setup=setup)
        receipts.append(T.seal(_attempt(spec, name), spec, name))
    manifest = T.assemble([Path(r["sealed_path"]) for r in receipts], spec, tmp_path / "run", lib._sha_file(spec_path))
    assert manifest["schema"] == T.X_ASSEMBLY_SCHEMA and [j["device"] for j in manifest["jobs"]] == ["cpu", "cpu"]
    monkeypatch.setattr(T.L, "summarise", lambda run_dir, s, root: {"schema": "x", "verdicts": {}})
    summary = T.summarise(tmp_path / "run", spec, ROOT)
    assert summary["schema"] == T.X_SUMMARY_SCHEMA and summary["note_rule"].startswith(T.X_RULE)
    assert summary["harness_commits"]["gc7rc_etth1"] == node(spec, "gc7rc_etth1")["harness"]["commit"]
    # a job record at another pin than the node's is refused by the assembly
    other = copy.deepcopy(spec)
    node(other, "mlgym_titanic")["harness"]["commit"] = "4" * 40
    with pytest.raises(T.Stop, match="harness_commit"):
        T.assemble([Path(receipts[0]["sealed_path"])], other, tmp_path / "run2", lib._sha_file(spec_path))
    asm = json.loads((tmp_path / "run" / "ASSEMBLY.json").read_text())
    asm["schema"] = T.ASSEMBLY_SCHEMA
    (tmp_path / "run" / "ASSEMBLY.json").write_text(json.dumps(asm))
    with pytest.raises(T.Stop, match="other spec kind"):
        T.summarise(tmp_path / "run", spec, ROOT)


# ============================================================================================ the note and launch
def host_report(pin: str, verdict="PASS", host="TASL-2") -> str:
    return (f"# host check\nhost_check_host: {host}\nhost_check_harness_commit: {pin}\nhost_check_items: 1-7 PASS\n"
            f"host_check_verdict: {verdict}\n")


def rep_path(name: str) -> str:
    return f"docs/r1/reports/x_hostchecks/HOST_CHECK_{name}.md"


def det_record(spec: dict, name: str, **over) -> str:
    """A determinism check record of a replacement CPU set (R1-TASL2-CPU) with its column-0 lines."""
    n = node(spec, name)
    lines = {"host": "TASL-2", "node": name, "cpus": n["cpus"], "harness_commit": n["harness"]["commit"], "runs": "2",
             "result_channel_sha256": n["cpu_replacement"]["determinism_check"]["census_baseline_result_channel_sha256"],
             "baseline_seconds": f"{n['run_seconds'] * 1.04:.3f} {n['run_seconds'] * 1.05:.3f}", "verdict": "PASS"}
    lines.update(over)
    return "# determinism check\n\n**Verdict: PASS** (prose is not read)\n\n" + "".join(
        f"determinism_check_{k}: {v}\n" for k, v in lines.items() if v is not None)


def det_path(spec: dict, name: str) -> str:
    return node(spec, name)["cpu_replacement"]["determinism_check"]["record"]


def gate_pass(spec: dict, name: str, det: str | None = None) -> str:
    n = node(spec, name)
    sha = hashlib.sha256(host_report(n["harness"]["commit"]).encode()).hexdigest()
    text = f"PASS — host check {rep_path(name)} sha256 {sha}"
    if "env_row" in n["gate_requires"]:
        text += f"; env row {ENV_ROW}"
    if "review" in n["gate_requires"]:
        text += f"; review {REVIEW}"
    if "cpu_determinism" in n["gate_requires"]:
        rec = det if det is not None else det_record(spec, name)
        text += f"; determinism check {det_path(spec, name)} sha256 {hashlib.sha256(rec.encode()).hexdigest()}"
    return text


def note_fields(spec, spec_path, *, draft=False, gates=None, **over) -> dict:
    fields = {"approved": "false" if draft else "true", "label": "ENGINEERING_ONLY", "labels_read": "none",
              "run_id": spec["run_id"], "paper_commit": spec["paper"]["commit"],
              "spec_sha256": lib._sha_file(spec_path), "publication_row": "R1-T1-NODE-EXPANSION: coordinating chat",
              "note_rule": "R1-T1-NODE-EXPANSION (x)", "host_row": "R1-T1-TASL-ENV (hosts), with R1-T1-HOST-TASL",
              "P1": "PASS — R1-T1-HOST-TASL: TASL-2", "P2": "PASS — kit reviews docs/r1/reviews/K.md",
              "P3": "PASS — census docs/r1/reports/C.md", "P4": f"PASS — review record {REVIEW}",
              "P5": "PASS — R1-G1B-EDITS: 4", "P6": "PASS — R1-G1B-TIMEOUT: slowest x3",
              "P7": "PASS — R1-T1-NODE-EXPANSION: 0 GPU-h of 40",
              "funnel": "MountainCarContinuous rejected; mlgym_metamaze, mlgym_titanic, gc7rc_etth1, gc7rc_forestcover; "
                        "AG News reserve",
              "cutoff": "finished_utc at or before 2 Dec 2026 00:00 CET -> G.5 addendum; later -> T2"}
    for n in spec["nodes"]:
        fields[f"node_{n['node']}"] = (f"harness {n['harness']['commit']}; committed_pin_sha256 "
                                       f"{n['committed_pin_sha256']}; edits {n['edits_manifest_sha256']}")
        fields[f"gate_{n['node']}"] = (gates or {}).get(n["node"], "PENDING — needs: host check")
        if n.get("cpu_replacement"):
            chk = n["cpu_replacement"]["determinism_check"]
            fields[f"determinism_check_{n['node']}"] = (f"R1-TASL2-CPU: cpus {n['cpus']}; record {chk['record']}; "
                                                        f"channel {chk['census_baseline_result_channel_sha256']}")
    fields.update(over)
    return fields


def write_note(tmp_path, fields, name="g1b_x_t1_tasl_20991231.md") -> Path:
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("# note\n\n" + "".join(f"{k}: {v}\n" for k, v in fields.items()))
    return p


def test_check_note_x_needs_the_determinism_line_of_each_replacement_set(job, tmp_path):
    spec, spec_path, *_ = job
    f = note_fields(spec, spec_path)
    del f["determinism_check_gc7rc_forestcover"]
    with pytest.raises(T.Stop, match="determinism_check_gc7rc_forestcover must name 'R1-TASL2-CPU'"):
        T.check_note_x(write_note(tmp_path, f), spec_path, spec=spec, on_main=lambda rel, raw: True,
                       read_main=_main_files(spec, spec_path).get)


def test_check_note_x_strict_and_draft(job, tmp_path):
    spec, spec_path, *_ = job
    yes = lambda rel, raw: True  # noqa: E731
    main = _main_files(spec, spec_path).get
    fields = T.check_note_x(write_note(tmp_path, note_fields(spec, spec_path)), spec_path, spec=spec, on_main=yes,
                            read_main=main)
    assert fields["_p4_review"]["verdict"] == "ACCEPTED"
    assert fields["gate_mlgym_titanic"].startswith("PENDING")       # a PENDING gate does not stop publication
    with pytest.raises(T.Stop, match="byte-identically"):
        T.check_note_x(write_note(tmp_path, note_fields(spec, spec_path)), spec_path, spec=spec,
                       on_main=lambda rel, raw: False)
    draft = note_fields(spec, spec_path, draft=True, P2="PENDING — docs/r1/reviews/K.md c1",
                        P4="PENDING — docs/r1/reviews/ at publication")
    T.check_note_x(write_note(tmp_path, draft, name="g1b_x_t1_tasl_20991230.md"), spec_path, spec=spec, draft=True)
    signed_open = note_fields(spec, spec_path, P4="PENDING — docs/r1/reviews/ at publication")
    with pytest.raises(T.Stop, match="not filled"):        # P2/P4 may be PENDING in the draft only
        T.check_note_x(write_note(tmp_path, signed_open, name="g1b_x_t1_tasl_20991229.md"), spec_path, spec=spec,
                       on_main=yes, read_main=main)
    other_p4 = note_fields(spec, spec_path, P4="PASS — review docs/r1/reviews/TITANIC_KIT_REVIEW_20261125.md")
    with pytest.raises(T.Stop, match="P4 must cite this unit's review record"):
        T.check_note_x(write_note(tmp_path, other_p4, name="g1b_x_t1_tasl_20991228.md"), spec_path, spec=spec,
                       on_main=yes, read_main=main)
    for record, match in ((None, "not on published main"), (review_record("0" * 64), "exactly one line 'spec_sha256"),
                          (review_record(lib._sha_file(spec_path), verdict="NOT ACCEPTED"), "verdict: ACCEPTED"),
                          (review_record(lib._sha_file(spec_path), extra="verdict: ACCEPTED\n"), "verdict: ACCEPTED")):
        with pytest.raises(T.Stop, match=match):         # P4 looks its file up on main and reads the bound lines
            T.check_note_x(write_note(tmp_path, note_fields(spec, spec_path)), spec_path, spec=spec, on_main=yes,
                           read_main={REVIEW: record}.get)


@pytest.mark.parametrize("over, match", [
    ({"approved": "false"}, "approved"),
    ({"labels_read": "train"}, "labels_read"),
    ({"paper_commit": "4" * 40}, "paper_commit"),
    ({"spec_sha256": "0" * 64}, "spec_sha256"),
    ({"run_id": "g1b-x-other"}, "run_id"),
    ({"publication_row": "R1-T1-D21-SCOPE"}, "publication_row"),
    ({"note_rule": "R1-T1-NODE-EXPANSIONS"}, "note_rule"),
    ({"host_row": "R1-T1-HOST-TASL"}, "host_row"),
    ({"P3": "PASS — census records elsewhere"}, "P3 must cite"),
    ({"P7": "PASS — R1-G1B-CAP"}, "P7 must cite"),
    ({"P5": "FAIL — R1-G1B-EDITS"}, "P5 is not PASS"),
    ({"funnel": "mlgym_titanic only"}, "funnel"),
    ({"cutoff": "by 3 Dec 2026"}, "cutoff"),
    ({"cutoff": "finished_utc by 2 Dec 2026 -> G.5; later T2"}, "cutoff"),
    ({"node_mlgym_titanic": "harness 3a67042b"}, "node_mlgym_titanic must name"),
    ({"gate_gc7rc_etth1": "maybe"}, "gate_gc7rc_etth1 must read PASS or PENDING"),
    ({"gate_mlab_imdb": "PASS — x"}, "not in the spec"),
    ({"keys": "<FILL>"}, "not filled"),
    ({"seal": "PENDING later"}, "not filled"),
    ({"determinism_check_mlgym_titanic": "R1-TASL2-CPU: cpus 12-15, the record at publication"},
     "determinism_check_mlgym_titanic must name 'docs/r1/reports/"),
    ({"determinism_check_gc7rc_forestcover": "cpus 4-7 docs/r1/reports/tasl_chain_20261122/"
                                            "TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md bcfc9b5d"},
     "determinism_check_gc7rc_forestcover must name 'R1-TASL2-CPU'"),
    ({"determinism_check_mlgym_metamaze": "R1-TASL2-CPU: none"}, "not on a replacement CPU set"),
])
def test_check_note_x_refusals(job, tmp_path, over, match):
    spec, spec_path, *_ = job
    with pytest.raises(T.Stop, match=match):
        T.check_note_x(write_note(tmp_path, note_fields(spec, spec_path, **over)), spec_path, spec=spec,
                       on_main=lambda rel, raw: True, read_main=_main_files(spec, spec_path).get)


def test_check_note_x_needs_its_name_and_kind(job, tmp_path):
    spec, spec_path, *_ = job
    f = note_fields(spec, spec_path)
    with pytest.raises(T.Stop, match="g1b_x_t1_tasl_"):
        T.check_note_x(write_note(tmp_path, f, name="g1b_t1_tasl_20991231.md"), spec_path, spec=spec,
                       on_main=lambda rel, raw: True)
    with pytest.raises(T.Stop, match="check_note_x"):           # the seven-node note check refuses this kind
        T.check_note(write_note(tmp_path, f, name="g1b_t1_tasl_20991231.md"), spec_path, spec["paper"]["commit"],
                     on_main=lambda rel, raw: True, spec=spec)
    with pytest.raises(T.Stop, match="node-expansion spec"):
        T.check_note_x(write_note(tmp_path, f), SEVEN_PATH, spec=T.load_spec(SEVEN_PATH))
    with pytest.raises(T.Stop, match="exactly one line 'approved: false'"):
        T.check_note_x(write_note(tmp_path, f), spec_path, spec=spec, draft=True)


def review_record(sha: str, verdict="ACCEPTED", disp=("gc7rc_etth1", "gc7rc_forestcover"), extra="") -> bytes:
    return (f"# review\n\n**Verdict: ACCEPTED** (prose is not read)\n\nspec_sha256: {sha}\nverdict: {verdict}\n"
            + "".join(f"cpu_census_disposition: {n} ACCEPTED\n" for n in disp) + extra).encode()


def _main_files(spec, spec_path) -> dict:
    plan = (ROOT / "docs/r1/PLAN.md").read_bytes() + \
        f"| {ENV_ROW} | EXP-ENV A: {T.X_ENV_ROW_TEXT}, in place, read-only. |\n".encode()
    files = {"docs/r1/PLAN.md": plan, REVIEW: review_record(lib._sha_file(spec_path))}
    for n in spec["nodes"]:
        files[rep_path(n["node"])] = host_report(n["harness"]["commit"]).encode()
        if n.get("cpu_replacement"):
            files[det_path(spec, n["node"])] = det_record(spec, n["node"]).encode()
    return files


def test_x_launch_runs_only_gated_nodes(job, tmp_path, monkeypatch):
    spec, spec_path, *_ = job
    yes = lambda rel, raw: True  # noqa: E731
    files = _main_files(spec, spec_path)
    gates = {"mlgym_titanic": gate_pass(spec, "mlgym_titanic"), "mlgym_metamaze": gate_pass(spec, "mlgym_metamaze")}
    note = write_note(tmp_path, note_fields(spec, spec_path, gates=gates))
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    with pytest.raises(T.Stop, match="disabled"):
        T.launch(spec_path, note, "mlgym_titanic", enable=True, on_main=yes, read_main=files.get)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    seen = []
    for name in ("mlgym_titanic", "mlgym_metamaze"):
        out = T.launch(spec_path, note, name, enable=True, on_main=yes, read_main=files.get,
                       launch_binding=lambda repo, s, rows: seen.append(rows) or {"bound": True},
                       runner=lambda sp, n: {"runs": {"written": 460}})
        assert out["launch"] == {"bound": True} and out["gate"]["host_check"]["record"] == rep_path(name)
    assert set(T.X_PLAN_ROWS) <= set(seen[0]) and "R1-T1-NODE-EXPANSION" in seen[0]
    titanic = T.launch(spec_path, note, "mlgym_titanic", enable=True, on_main=yes, read_main=files.get,
                       launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    assert titanic["gate"]["cpu_determinism"]["cpus"] == "12-15" and titanic["gate"]["cpu_determinism"]["verdict"] == \
        "PASS" and titanic["gate"]["cpu_determinism"]["record"] == det_path(spec, "mlgym_titanic")
    with pytest.raises(T.Stop, match="gate_gc7rc_etth1 is not PASS"):        # PENDING: this node does not launch
        T.launch(spec_path, note, "gc7rc_etth1", enable=True, on_main=yes, read_main=files.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})


@pytest.mark.parametrize("name, mutate, match", [
    ("mlgym_titanic", lambda g, f, s: (g.replace("sha256 ", "sha256 0", 1)[:-1], f), "sha256|cite its host check"),
    ("mlgym_titanic", lambda g, f, s: (g, {**f, rep_path("mlgym_titanic"):
                                           host_report(node(s, "gc7rc_etth1")["harness"]["commit"]).encode()}),
     "differs from its declared sha256"),
    ("mlgym_titanic", lambda g, f, s: (g.split(" sha256")[0], f), "must cite its host check"),
    ("mlgym_metamaze", lambda g, f, s: (g.split("; env row")[0], f), "must cite its env row"),
    ("mlgym_metamaze", lambda g, f, s: (g, {**f, "docs/r1/PLAN.md": (ROOT / "docs/r1/PLAN.md").read_bytes()}),
     "must exist once and contain, verbatim"),
    ("mlgym_metamaze", lambda g, f, s: (g, {**f, "docs/r1/PLAN.md": (ROOT / "docs/r1/PLAN.md").read_bytes() + (
        f"| {ENV_ROW} | EXP-ENV refused: venv_jax is not admitted for mlgym_metamaze |\n").encode()}),
     "must exist once and contain, verbatim"),                    # a mere mention (here a refusal) does not pass
    ("gc7rc_etth1", lambda g, f, s: (g.replace(REVIEW, "docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md"),
                                     {**f, "docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md": b"# kit review\n"}),
     "must be this unit's review record"),                        # the kit review that asked for the GPU census
    ("gc7rc_etth1", lambda g, f, s: (g, {**f, REVIEW: f[REVIEW].replace(b"cpu_census_disposition: gc7rc_etth1 "
                                                                         b"ACCEPTED\n", b"")}),
     "cpu_census_disposition: gc7rc_etth1 ACCEPTED"),
    ("gc7rc_forestcover", lambda g, f, s: (g, {**f, REVIEW: f[REVIEW].replace(
        b"cpu_census_disposition: gc7rc_forestcover ACCEPTED", b"cpu_census_disposition: gc7rc_forestcover REFUSED")}),
     "cpu_census_disposition: gc7rc_forestcover ACCEPTED"),
    ("gc7rc_forestcover", lambda g, f, s: (g.split("; review")[0], f), "must cite its review"),
    ("gc7rc_forestcover", lambda g, f, s: (g, {k: v for k, v in f.items() if "reviews" not in k}),
     "not on published main"),
    # R1-TASL2-CPU: the replacement set's fixed-seed determinism check record
    ("mlgym_titanic", lambda g, f, s: (g.split("; determinism check")[0], f), "must cite its cpu determinism"),
    ("gc7rc_forestcover", lambda g, f, s: (g.split("; determinism check")[0], f), "must cite its cpu determinism"),
    ("mlgym_titanic", lambda g, f, s: (g, {k: v for k, v in f.items() if "DETERMINISM" not in k}),
     "determinism check record .* is not on published main"),
    ("mlgym_titanic", lambda g, f, s: (g.replace(det_path(s, "mlgym_titanic"), "docs/r1/reports/other_12-15.md"),
                                       {**f, "docs/r1/reports/other_12-15.md": f[det_path(s, "mlgym_titanic")]}),
     "must be the record its spec names"),
    ("mlgym_titanic", lambda g, f, s: (g, {**f, det_path(s, "mlgym_titanic"):
                                           det_record(s, "mlgym_titanic", verdict="FAIL").encode()}),
     "differs from the sha256 its gate cites"),
] + [
    ("mlgym_titanic", (lambda over: lambda g, f, s: (
        gate_pass(s, "mlgym_titanic", det_record(s, "mlgym_titanic", **over)),
        {**f, det_path(s, "mlgym_titanic"): det_record(s, "mlgym_titanic", **over).encode()}))(over), match)
    for over, match in (
        ({"verdict": "FAIL"}, r"does not show a PASS.*'verdict': 'FAIL'"),
        ({"cpus": "8-11"}, r"does not show a PASS.*'cpus': '8-11'"),
        ({"node": "gc7rc_forestcover"}, r"does not show a PASS.*'node'"),
        ({"host": "TASL-7"}, r"does not show a PASS.*'host'"),
        ({"harness_commit": "c025f89aeafc2199bf3487b4bcaa16678273c702"}, r"does not show a PASS.*'harness_commit'"),
        ({"runs": "3"}, r"does not show a PASS.*'runs'"),
        ({"result_channel_sha256": "0" * 64}, r"does not show a PASS.*'result_channel_sha256'"),
        ({"result_channel_sha256": None}, "exactly one line 'determinism_check_result_channel_sha256"),
        ({"verdict": "PASS\n**determinism_check_verdict: FAIL**"}, "exactly one line 'determinism_check_verdict"),
        ({"verdict": "PASS\nDETERMINISM_CHECK_VERDICT: FAIL"}, "exactly one line 'determinism_check_verdict"),
        ({"verdict": "PASS "}, r"does not show a PASS.*'verdict': 'PASS '"),
        ({"baseline_seconds": "140.0"}, "must give 2 baseline wall times"),
        ({"baseline_seconds": "140.0 207.275"}, r"each in \(0, 207.274"),
        ({"baseline_seconds": "140.0 fast"}, "must give 2 baseline wall times"),
    )
] + [
    ("gc7rc_forestcover", lambda g, f, s: (
        gate_pass(s, "gc7rc_forestcover", det_record(s, "gc7rc_forestcover", baseline_seconds="93.5 140.11")),
        {**f, det_path(s, "gc7rc_forestcover"):
         det_record(s, "gc7rc_forestcover", baseline_seconds="93.5 140.11").encode()}), r"each in \(0, 140.109\]"),
])
def test_x_gate_refusals(job, tmp_path, monkeypatch, name, mutate, match):
    spec, spec_path, *_ = job
    files = _main_files(spec, spec_path)
    gate, files = mutate(gate_pass(spec, name), files, spec)
    note = write_note(tmp_path, note_fields(spec, spec_path, gates={name: gate}))
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    with pytest.raises(T.Stop, match=match):
        T.launch(spec_path, note, name, enable=True, on_main=lambda rel, raw: True, read_main=files.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})


def test_a_host_check_at_another_pin_is_refused_even_when_the_gate_binds_it(job, tmp_path, monkeypatch):
    spec, spec_path, *_ = job
    files = _main_files(spec, spec_path)
    stale = host_report("c025f89aeafc2199bf3487b4bcaa16678273c702")
    files[rep_path("mlgym_titanic")] = stale.encode()
    gate = f"PASS — host check {rep_path('mlgym_titanic')} sha256 {hashlib.sha256(stale.encode()).hexdigest()}"
    note = write_note(tmp_path, note_fields(spec, spec_path, gates={"mlgym_titanic": gate}))
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    with pytest.raises(T.Stop, match="does not show a PASS for this host and pin.*host_check_harness_commit"):
        T.launch(spec_path, note, "mlgym_titanic", enable=True, on_main=lambda rel, raw: True, read_main=files.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})


def test_the_publication_row_must_be_on_main(job, tmp_path, monkeypatch):
    spec, spec_path, *_ = job
    files = _main_files(spec, spec_path)
    note = write_note(tmp_path, note_fields(spec, spec_path, gates={"mlgym_titanic": gate_pass(spec, "mlgym_titanic")}))
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    plan = files["docs/r1/PLAN.md"].decode()
    for text in ("", plan.replace("The coordinating chat publishes the new G.1b spec and note", "The author signs")):
        with pytest.raises(T.Stop, match="coordinating chat publishes"):
            T.launch(spec_path, note, "mlgym_titanic", enable=True, on_main=lambda rel, raw: True,
                     read_main={**files, "docs/r1/PLAN.md": text.encode()}.get,
                     launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    assert T.check_publication_row(lambda rel: (ROOT / rel).read_bytes()) == T.X_RULE   # the row on this checkout


def test_cli_check_note_x(job, tmp_path, capsys):
    spec, spec_path, *_ = job
    draft = note_fields(spec, spec_path, draft=True, P4="PENDING — docs/r1/reviews/ at publication")
    note = write_note(tmp_path, draft)
    assert T.main(["check-note-x", str(spec_path), "--note", str(note), "--draft"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "draft" and set(out["gates"].values()) == {"PENDING"}
    assert T.main(["check-note-x", str(spec_path), "--note", str(note)]) == 2


def test_the_shipped_draft_renders_the_spec_and_passes_its_draft_check(tmp_path):
    """The shipped draft: its rendered lines are the spec's (build_g1bx_launch.render); at the base it carries the
    template's PENDING paper_commit/spec_sha256 and refuses; at the launch commit it passes check-note-x --draft."""
    import build_g1bx_launch as BX
    spec = T.load_spec(X_PATH)
    fields = T._note_fields(NOTE_DRAFT.read_bytes())
    proj = T.validate_spec(copy.deepcopy(spec) | {"paper": {**spec["paper"], "commit": "0" * 40}})["projection"]
    for key, value in BX.render(spec, proj).items():
        assert fields[key] == value, key
    target = tmp_path / "docs/r1/authorizations/g1b_x_t1_tasl_20991231.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(NOTE_DRAFT.read_bytes())
    if spec["paper"]["commit"] == BX.TEMPLATE_PAPER:
        assert fields["paper_commit"].startswith("PENDING") and fields["spec_sha256"].startswith("PENDING")
        with pytest.raises(T.Stop):
            T.check_note_x(target, X_PATH, spec=spec, draft=True)
    else:
        out = T.check_note_x(target, X_PATH, spec=spec, draft=True)
        assert out["spec_sha256"] == lib._sha_file(X_PATH) and out["approved"] == "false"
    assert all(fields[f"gate_{n}"].startswith("PENDING") for n in T.X_NODES)
    assert "8-11" in fields["disclosure_metamaze_cpus"] and "stability record" in fields["disclosure_metamaze_cpus"]
    disc = fields["disclosure_metamaze_cpus"]
    assert T.X_STABILITY_RECORD in disc and lib._sha_file(ROOT / T.X_STABILITY_RECORD) in disc and "R1-TASL2-CPU" in disc
    assert "pending" not in disc
    for n in X_SHIPPED["nodes"]:                          # the note names each replacement set's determinism check
        if n.get("cpu_replacement"):
            line = fields[f"determinism_check_{n['node']}"]
            assert n["cpu_replacement"]["determinism_check"]["record"] in line and "pass:" in line
            assert "procedure:" in line and "supporting evidence, not the check" in line
    assert "12-15" in fields["cpu_sets"] and "4-7" in fields["cpu_sets"] and "30 Nov 20:33" in fields["latest_starts"]


# ============================================================================================ round-1 additions
def _stat(path: Path, rows: dict[int, tuple[int, int]]) -> None:
    """A /proc/stat with per-CPU (busy, idle) jiffies (user = busy, idle = idle, the rest 0)."""
    path.write_text("cpu  0 0 0 0 0 0 0 0 0 0\n" + "".join(f"cpu{c} {b} 0 0 {i} 0 0 0 0 0 0\n"
                                                           for c, (b, i) in sorted(rows.items())))


def test_cpu_busy_check_reads_proc_stat_and_fails_closed(tmp_path):
    spec = filled()
    n = node(spec, "mlgym_metamaze")                     # cpus 0-3
    stat = tmp_path / "stat"
    before = {c: (100, 1000) for c in range(32)}
    after = {c: (110, 1090) for c in range(32)}           # 10 busy of 100 jiffies: 0.1
    after[17] = (200, 1000)                               # another set fully busy: not this node's concern
    _stat(stat, before)
    slept = []

    def sleep(sec):
        slept.append(sec)
        _stat(stat, after)
    out = T.cpu_busy_check(spec, n, "before default", stat=stat, sleep=sleep)
    assert slept == [5] and out["busy"] == {"0": 0.1, "1": 0.1, "2": 0.1, "3": 0.1} and out["max_busy"] == 0.2
    after[2] = (150, 1140)                                # cpu 2: 50 of 100 busy
    _stat(stat, before)
    with pytest.raises(T.Stop, match=r"CPUs \[2\] of mlgym_metamaze's CPU set were busy"):
        T.cpu_busy_check(spec, n, "before the attempt", stat=stat, sleep=sleep)
    _stat(stat, {c: v for c, v in before.items() if c != 3})
    with pytest.raises(T.Stop, match="cpu 3 of mlgym_metamaze's set is not in"):
        T.cpu_busy_check(spec, n, "x", stat=stat, sleep=lambda s: None)
    _stat(stat, before)                                   # no jiffies elapsed: counted as busy (fail closed)
    with pytest.raises(T.Stop, match="were busy"):
        T.cpu_busy_check(spec, n, "x", stat=stat, sleep=lambda s: None)


def test_a_busy_set_refuses_before_the_attempt_and_stops_a_later_part(job, monkeypatch):
    spec, spec_path, calls, engine, smi, setup, *_ = job

    def busy(s, n, when, **kw):
        raise T.Stop(f"STOP: CPUs [8] busy {when}")
    monkeypatch.setattr(T, "cpu_busy_check", busy)
    with pytest.raises(T.Stop, match="busy before the attempt"):
        T.run_node_job(spec_path, "mlgym_titanic", smi=smi, engine=engine, setup=setup)
    root = Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"]
    assert not (root / "mlgym_titanic").exists() and len(list((root / "_refusals").iterdir())) == 1   # nothing used
    seen = []

    def busy_at_split(s, n, when, **kw):
        seen.append(when)
        if when == "before split":
            raise T.Stop("STOP: CPUs [9] busy before split")
        return {"when": when}
    monkeypatch.setattr(T, "cpu_busy_check", busy_at_split)
    with pytest.raises(T.Stop, match="busy before split"):
        T.run_node_job(spec_path, "mlgym_titanic", smi=smi, engine=engine, setup=setup)
    rec = json.loads((_attempt(spec, "mlgym_titanic") / "job_record.json").read_text())
    assert rec["stop_class"] == "infrastructure" and [r["when"] for r in rec["cpu_preflight"]] == \
        ["before the attempt", "before default", "before train"]
    assert seen == ["before the attempt", "before default", "before train", "before split"]


def test_no_attempt_cap_now_that_no_node_runs_on_cpus_8_11(job, monkeypatch):
    """R1-TASL2-CPU dropped the two-attempt rule of CPUs 8-11: the replacement sets follow the existing rule (a new
    attempt after an infrastructure STOP, none after a node or timing STOP)."""
    spec, spec_path, calls, engine, smi, setup, *_ = job

    def crashing(argv, **kw):                            # an engine STOP (as a native-signal infrastructure failure)
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True)
        (out / "chunk_record.json").write_text(json.dumps({"stop": "NoiseFloorStop: infrastructure failure (-11)"}))
        return subprocess.CompletedProcess(argv, 3, "", "")
    for _ in range(3):
        with pytest.raises(T.Stop, match="infrastructure failure"):
            T.run_node_job(spec_path, "gc7rc_forestcover", smi=smi, engine=crashing, setup=setup)
    rec = T.run_node_job(spec_path, "gc7rc_forestcover", smi=smi, engine=engine, setup=setup)
    assert rec["attempt"] == 4 and rec["stop"] is None
    import inspect
    assert list(inspect.signature(T.next_attempt).parameters) == ["node_root"]
    assert not hasattr(T, "X_FAVOURED_MAX_ATTEMPTS") and not hasattr(T, "X_FAVOURED_CPUS")


def test_timing_stop_names_the_cpu_set_not_the_4090():
    spec = filled()
    rows = [{"run_id": "r", "failure": "divergent:timeout", "config": "c0", "wall_seconds": 1.0}]
    with pytest.raises(T.TimingStop, match=r"its CPU set \(cpus 12-15\)"):
        T.timing_check(rows, node(spec, "mlgym_titanic"), "default")
    seven = T.load_spec(SEVEN_PATH)
    with pytest.raises(T.TimingStop, match="on the 4090"):
        T.timing_check(rows, seven["nodes"][0], "default")


def test_shipped_spec_carries_the_review_conditions():
    for name in ("gc7rc_etth1", "gc7rc_forestcover"):
        cond = " ".join(node(X_SHIPPED, name)["cpu_census_conditions"])
        for needle in ("stays on the CPU", "G.5 addendum", "c2/c4", "re-issued spec", "CPU-measured", "c1"):
            assert needle in cond, (name, needle)
    fields = T._note_fields(NOTE_DRAFT.read_bytes())
    for needle in ("stays on the CPU", "G.5 addendum", "re-issued spec", "CPU-measured", "P2"):
        assert needle in fields["cpu_census_conditions"]
    assert "CPU-measured" in fields["funnel"] and "retry_8_11" not in fields and "max_attempts" not in \
        NOTE_DRAFT.read_text()
    assert "4-7, the R1-TASL2-CPU replacement" in fields["cpu_census_conditions"]
    assert "4-7" in " ".join(node(X_SHIPPED, "gc7rc_forestcover")["cpu_census_conditions"])
    assert "2026-12-01T23:00:00Z" in fields["cutoff"] and "independently reviewed" in NOTE_DRAFT.read_text()
    for needle in ("Kaggle", "CC BY-ND 4.0", "not a suite"):
        assert needle in fields["disclosure_data"]
    assert "tests.trackg.port_smoke_gpu.CPU_ONLY_NODES" in fields["disclosure_override"]
    assert "cards only, not on\n  CPU sets" in NOTE_DRAFT.read_text()
