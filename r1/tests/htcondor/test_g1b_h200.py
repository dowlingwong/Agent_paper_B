"""G.1b on NEMO2 H200: spec validation, projection and cap, chunk plan, D21 math, summary, JDL render, two-key switch.

Synthetic only: no GPU, no network, no submission (condor_submit is never called; the switch tests stop before it
or replace subprocess.run).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
G1B = ROOT / "sweep2" / "g1b"
sys.path.insert(0, str(G1B))
import g1b_lib as lib  # noqa: E402
import g1b_switch as switch  # noqa: E402
import g1b_render_jdl as render_jdl  # noqa: E402  (not sweep2/render_jdl.py)

SPEC = json.loads((G1B / "g1b_spec.json").read_text())


def launch_spec() -> dict:
    spec = copy.deepcopy(SPEC)
    spec["image"]["versions_sha256"] = "1" * 64
    spec["paper"]["commit"] = "2" * 40
    spec["edit_count"]["authority"] = "R1-G1B-EDITS (test)"
    spec["timeout_decision"]["authority"] = "R1-G1B-TIMEOUT (test)"
    return spec


# ---------------------------------------------------------------------------------------------- spec + projection
def test_committed_spec_validates_and_projects_under_the_cap():
    loaded = lib.validate_spec(copy.deepcopy(SPEC))
    proj = loaded["projection"]
    assert proj["jobs"] == 6 and proj["total_runs"] == 6 * 460
    assert proj["total_run_gpu_hours"] == pytest.approx(sum(n["run_seconds"] for n in SPEC["nodes"]) * 460 / 3600, abs=1e-2)
    assert 26 < proj["total_run_gpu_hours"] < 27 and proj["total_gpu_hours"] < lib.CAP_TOTAL_GPU_HOURS
    assert proj["max_walltime_s"] <= lib.MAX_WALLTIME_S
    imdb = proj["per_node"]["mlab_imdb"]
    assert imdb["requested_walltime_s"] == 3600 + math.ceil(460 * 64.142 * 1.5)
    # the 552-run variant (five edits) stays under the cap too: about 32 GPU-h of runs
    assert sum(n["run_seconds"] for n in SPEC["nodes"]) * 552 / 3600 == pytest.approx(32.1, abs=0.1)


def test_launch_validation_refuses_placeholders():
    with pytest.raises(lib.Stop, match="versions_sha256"):
        lib.validate_spec(copy.deepcopy(SPEC), launch=True)
    spec = launch_spec()
    lib.validate_spec(spec, launch=True)
    for bad in ("TODO_AUTHOR_DECISION", "G1B-EDITS row x", "see R1-G1B-EDITS", "R1-G1B-EDITSX"):
        spec["edit_count"]["authority"] = bad
        with pytest.raises(lib.Stop, match="author's decision"):
            lib.validate_spec(spec, launch=True)
    spec = launch_spec()
    for bad in ("TODO_AUTHOR_DECISION", "R1-G1B-TIMEOUTS", "x R1-G1B-TIMEOUT"):
        spec["timeout_decision"]["authority"] = bad
        with pytest.raises(lib.Stop, match="timeout basis needs"):
            lib.validate_spec(spec, launch=True)
    spec = launch_spec()
    spec["timeout_decision"]["basis"] = "slowest_census_record_x3"
    with pytest.raises(lib.Stop, match="reviewed change"):
        lib.validate_spec(spec)


def _mut(fn):
    spec = copy.deepcopy(SPEC)
    fn(spec)
    return spec


@pytest.mark.parametrize("mutate, needle", [
    (lambda s: s["nodes"].pop(0), "six T1 nodes"),
    (lambda s: s["nodes"].append(dict(s["nodes"][0], node="openml_ionosphere")), "not T1 nodes"),
    (lambda s: s["nodes"].append(copy.deepcopy(s["nodes"][0])), "listed twice"),
    (lambda s: s["nodes"][2].update(n_edits=5), "uniform"),
    (lambda s: s["edit_count"].update(runs_per_node=552), "must agree"),
    (lambda s: s["caps"].update(max_total_gpu_hours=150.0), "R1-G1B-CAP"),
    (lambda s: [n.update(run_seconds=290.0) for n in s["nodes"]], "author STOP|walltime"),
    (lambda s: s.update(gpu_model="NVIDIA L40S"), "H200"),
    (lambda s: s["image"].update(digest="ghcr.io/dowlingwong/r1-htc-gpu@sha256:" + "6" * 64), "v2 gpu digest"),
    (lambda s: s["measurement"].update(seeds_per_condition=29), "seeds_per_condition"),
    (lambda s: s["measurement"].update(isolation_gate="effective:true"), "isolation_gate"),
    (lambda s: s["envs"]["torch312"].update(sha256="0" * 64), "freeze sha256"),
    (lambda s: s["nodes"][0].update(committed_pin_sha256="x"), "committed_pin_sha256"),
    (lambda s: s["nodes"][0].pop("data_manifest_sha256"), "data_manifest_sha256"),
    (lambda s: s["nodes"][0].update(data_manifest_sha256="TODO"), "data_manifest_sha256"),
    (lambda s: s["nodes"][0].update(edits_manifest_sha256="0" * 63), "edits_manifest_sha256"),
    (lambda s: s["nodes"][0].update(node_dir="/abs/path"), "relative path"),
    (lambda s: s.update(label="EVIDENCE"), "ENGINEERING_ONLY"),
])
def test_spec_refusals(mutate, needle):
    with pytest.raises(lib.Stop, match=needle):
        lib.validate_spec(_mut(mutate))


def test_cap_stop_projection():
    spec = _mut(lambda s: s["caps"].update(max_total_gpu_hours=20.0))  # a spec may lower the cap, never raise it
    with pytest.raises(lib.Stop, match="exceeds the R1-G1B-CAP"):
        lib.validate_spec(spec)
    proj = lib.validate_spec(copy.deepcopy(SPEC))["projection"]
    # the requested slot-hours bound the table too (kit review N3): a cap between the projection and the slot-hours
    between = (proj["total_gpu_hours"] + proj["requested_slot_hours"]) / 2
    assert proj["total_gpu_hours"] < between < proj["requested_slot_hours"]
    with pytest.raises(lib.Stop, match="slot-h"):
        lib.validate_spec(_mut(lambda s: s["caps"].update(max_total_gpu_hours=round(between, 3))))


def test_spec_pins_match_the_census_values():
    by = {n["node"]: n for n in SPEC["nodes"]}
    assert by["mlab_cifar10"]["committed_pin_sha256"].startswith("1f047ad7")
    assert by["mlab_cifar10"]["data_manifest_sha256"].startswith("43fdf860")
    assert by["mlgym_fmnist"]["data_manifest_sha256"].startswith("8d28287b")
    assert by["mlgym_breakout_minatar"]["data_manifest_sha256"] is None
    assert all("deployed_pin_sha256" not in n for n in SPEC["nodes"])  # host-specific (data link), kit review B1
    assert by["mlgym_breakout_minatar"]["env"] == "jax312" and by["mlab_imdb"]["env"] == "torch312"
    for name, env in SPEC["envs"].items():
        assert hashlib.sha256((G1B / env["freeze"]).read_bytes()).hexdigest() == env["sha256"]
    assert SPEC["envs"]["torch312"]["sha256"].startswith("d2e70fe4") and SPEC["envs"]["jax312"]["sha256"].startswith("80a455c6")


# ---------------------------------------------------------------------------------------------- chunk plan
def test_parts_and_chunk_files():
    node = SPEC["nodes"][0]
    counts = {p[0]: len(lib.expected_runs(4, p[1], p[2])) for p in lib.PARTS}
    assert counts == {"default": 10, "train": 150, "split": 150, "joint": 150} and sum(counts.values()) == 460
    chunk = lib.chunk_file(SPEC, node, lib.PARTS[3], interpreter="/e/bin/python", cgroup_parent="/sys/fs/cgroup/x",
                           deadline=1e12, memory_limit="m")
    assert chunk["committed_pin_sha256"] == node["committed_pin_sha256"] and chunk["isolation_waivers"] == {}
    assert chunk["data_manifest_sha256"] == node["data_manifest_sha256"] and "frozen_pin_sha256" not in chunk
    assert chunk["runs"][0] == {"config": "c0", "condition": "joint", "train_seed": 3001, "split_seed": 3001}
    assert chunk["runs"][-1] == {"config": "c4", "condition": "joint", "train_seed": 3030, "split_seed": 3030}
    seeds = {r["train_seed"] for p in lib.PARTS for r in lib.expected_runs(4, p[1], p[2])} - {None}
    assert not seeds & set(range(7001, 7011)) and not seeds & set(range(9001, 10000))


# ---------------------------------------------------------------------------------------------- D21 + summary
GATE = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True, "parent_traced_by": None,
        "parent_dumpable_at_accept": False}


def _row(node, config, condition, t, s, metric, failure=None, **iso):
    gate = dict(GATE)
    gate.update(iso)
    return {"node": node, "config": config, "condition": condition, "train_seed": t, "split_seed": s,
            "metric": metric, "success": metric is not None, "failure": failure, "wall_seconds": 1.0,
            "run_id": f"{config}_{condition}_{t}_{s}", "isolation": gate}


def synthetic_rows(nodes=None, *, nondet_node=None, parts=lib.PARTS) -> list[dict]:
    import random
    rows = []
    effects = [0.0, 0.004, -0.003, 0.0005, 0.02]  # c0..c4
    for node in nodes or [n["node"] for n in SPEC["nodes"]]:
        for p in parts:
            for run in lib.expected_runs(4, p[1], p[2]):
                k = int(run["config"][1:])
                seed = run["train_seed"] or run["split_seed"] or 0
                noise = random.Random(hash((node, run["condition"], seed)) & 0xFFFF).gauss(0, 0.003) if seed else 0.0
                metric = 0.5 + effects[k] + noise
                if node == nondet_node and run["condition"] == "default_repeat" and k == 0:
                    metric += 1e-6
                rows.append(_row(node, run["config"], run["condition"], run["train_seed"], run["split_seed"],
                                 round(metric, 9)))
    return rows


EDITS = {n["node"]: [{"symbol": f"E{k}", "old": "baseline", "new": f"E{k}.diff"} for k in range(1, 5)]
         for n in SPEC["nodes"]}


def assembled_dir(tmp: Path, rows: list[dict], *, node_stopped=()) -> Path:
    """A run directory in the shape ``assemble`` writes (rows, edits, ASSEMBLY.json)."""
    d = tmp / "run"
    d.mkdir(parents=True)
    (d / "runs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (d / "edits.json").write_text(json.dumps(EDITS))
    jobs = [{"node": n["node"], "stop_class": "node" if n["node"] in node_stopped else None, "spec_sha256": "s"}
            for n in SPEC["nodes"]]
    (d / "ASSEMBLY.json").write_text(json.dumps({"jobs": jobs, "runs_sha256": lib._sha_file(d / "runs.jsonl"),
                                                 "spec_json_sha256": hashlib.sha256(
                                                     json.dumps(SPEC, sort_keys=True).encode()).hexdigest()}))
    return d


def test_summarise_applies_the_pinned_rule_with_the_independent_check(tmp_path):
    summary = lib.summarise(assembled_dir(tmp_path, synthetic_rows()), SPEC, ROOT)
    assert summary["screening_funnel"]["measured"] == 6
    v = summary["verdicts"]["mlab_cifar10"]
    assert v["checks"]["seeds_per_condition_is_30"] and v["n_edits"] == 4
    assert v["checks"]["material_edits_ge_2"] and v["sigma_joint"] > 0
    assert v["paired_joint_n"] == [30, 30, 30, 30] and v["divergent"]["rows"] == 0
    assert v["e1_report_proposed_split"] in ("vary", "fixed")
    assert (tmp_path / "run" / "summary.json").is_file()


def test_summarise_refuses_an_unassembled_or_changed_run_dir(tmp_path):
    d = assembled_dir(tmp_path, synthetic_rows())
    with (d / "runs.jsonl").open("a") as fh:
        fh.write("\n")
    with pytest.raises(lib.Stop, match="assembly manifest"):
        lib.summarise(d, SPEC, ROOT)
    (d / "ASSEMBLY.json").unlink()  # this test's own temporary file
    with pytest.raises(FileNotFoundError):
        lib.summarise(d, SPEC, ROOT)


def test_summarise_stops_on_drift_between_the_two_rule_implementations(tmp_path, monkeypatch):
    d = assembled_dir(tmp_path, synthetic_rows())
    real = lib.paired_joint_stats
    monkeypatch.setattr(lib, "paired_joint_stats", lambda *a: [dict(e, material=not e["material"]) for e in real(*a)])
    with pytest.raises(lib.Stop, match="rule drift"):
        lib.summarise(d, SPEC, ROOT)
    monkeypatch.setattr(lib, "paired_joint_stats", lambda *a: [dict(e, p_wrong=e["p_wrong"] + 1e-6) for e in real(*a)])
    with pytest.raises(lib.Stop, match="rule drift"):
        lib.summarise(d, SPEC, ROOT)
    monkeypatch.setattr(lib, "paired_joint_stats", real)
    monkeypatch.setattr(lib, "d21_qualify", lambda *a: {"qualifies_D21": "x", "checks": {}})
    with pytest.raises(lib.Stop, match="node verdict"):
        lib.summarise(d, SPEC, ROOT)


@pytest.mark.parametrize("damage, needle", [
    ("drop", "coverage"), ("duplicate", "duplicate"), ("waiver", "not effectively isolated"),
    ("log", "not effectively isolated"), ("traced", "not effectively isolated"),
    ("dumpable", "not effectively isolated"), ("exceptions", "not effectively isolated"),
    ("effective", "not effectively isolated"),
])
def test_summarise_stops_on_gaps_and_unisolated_rows(tmp_path, damage, needle):
    rows = synthetic_rows()
    if damage == "drop":
        rows.pop(5)
    elif damage == "duplicate":
        rows.append(dict(rows[5]))
    else:
        key, value = {"waiver": ("waivers", {"root": "x"}), "log": ("log_intact", False),
                      "traced": ("parent_traced_by", 4242), "dumpable": ("parent_dumpable_at_accept", True),
                      "exceptions": ("exceptions", ["x"]), "effective": ("effective", "true")}[damage]
        rows[7]["isolation"][key] = value
    with pytest.raises(lib.Stop, match=needle):
        lib.summarise(assembled_dir(tmp_path, rows), SPEC, ROOT)


def test_summarise_marks_nondeterminism_and_node_stops_as_not_qualifying(tmp_path):
    summary = lib.summarise(assembled_dir(tmp_path / "a", synthetic_rows(nondet_node="mlab_imdb")), SPEC, ROOT)
    assert summary["verdicts"]["mlab_imdb"]["qualifies_D21"] is False
    assert summary["screening_funnel"]["failed_determinism"] == 1
    # a node whose job stopped on determinism carries its default rows only
    rows = [r for r in synthetic_rows(nondet_node="mlgym_fmnist")
            if r["node"] != "mlgym_fmnist" or r["condition"] in ("default", "default_repeat")]
    summary = lib.summarise(assembled_dir(tmp_path / "b", rows, node_stopped=("mlgym_fmnist",)), SPEC, ROOT)
    assert summary["verdicts"]["mlgym_fmnist"]["reason"] == "fixed-seed determinism failed"
    # ... and any other row of that node is an extra row
    with pytest.raises(lib.Stop, match="coverage"):
        lib.summarise(assembled_dir(tmp_path / "c", synthetic_rows(), node_stopped=("mlgym_fmnist",)), SPEC, ROOT)


def test_determinism_compares_outcomes():
    def pair(a, b):
        return [_row("n", "c0", "default", None, None, *a), _row("n", "c0", "default_repeat", None, None, *b)]
    assert lib.determinism_check(pair((0.5,), (0.5,)))["deterministic"] is True
    assert lib.determinism_check(pair((0.5,), (0.5000001,)))["deterministic"] is False
    both_failed = lib.determinism_check(pair((None, "divergent:timeout"), (None, "divergent:timeout")))
    assert both_failed["deterministic"] is True and both_failed["divergent_configs_at_default"] == ["c0"]
    assert lib.determinism_check(pair((None, "divergent:timeout"), (None, "divergent:nan")))["deterministic"] is False
    assert lib.determinism_check(pair((None, "divergent:timeout"), (0.5,)))["deterministic"] is False
    assert lib.determinism_check(pair((0.5,), (None, "x")))["deterministic"] is False
    assert lib.determinism_check(pair((0.5,), (0.5,))[:1])["deterministic"] is False  # an unpaired default
    assert lib.determinism_check([])["deterministic"] is False


def test_paired_joint_stats_follow_e1_report_on_thin_pairs():
    rows = [r for r in synthetic_rows(["mlab_cifar10"]) if not (r["config"] == "c2" and r["condition"] == "joint"
                                                                and r["train_seed"] > 3002)]
    stats = lib.paired_joint_stats(rows, "mlab_cifar10", 4)
    assert stats[1] == {"n_joint": 2, "material": False, "p_wrong": stats[1]["p_wrong"], "resolved": False}
    assert math.isnan(stats[1]["p_wrong"]) and stats[0]["n_joint"] == 30


def test_d21_rule_constants_and_math():
    assert (lib.D21_MIN_MATERIAL_EDITS, lib.D21_MIN_EFFECT, lib.D21_MIN_MEAN_P_WRONG) == (2, 0.002, 0.10)
    e = lib.edit_stats([0.01 + 0.001 * ((i % 3) - 1) for i in range(30)])
    assert e["resolved"] and e["material"]
    q = lib.d21_qualify([{"material": True, "p_wrong": 0.2}, {"material": True, "p_wrong": 0.05}], 0.01, 30)
    assert q["qualifies_D21"] is True and q["mean_p_wrong_material"] == pytest.approx(0.125)
    assert lib.d21_qualify([{"material": True, "p_wrong": 0.2}], 0.01, 30)["qualifies_D21"] is False
    assert lib.d21_qualify([{"material": True, "p_wrong": 0.2}] * 2, 0.0, 30)["qualifies_D21"] is False


# ---------------------------------------------------------------------------------------------- job helpers
def test_setup_command_parser(tmp_path):
    y = tmp_path / "n.yaml"
    y.write_text("name: x\nsetup_command: 'test -n \"$AR_TRACKG_DATA_ROOT\" && python3 prepare_data.py --out x'\n")
    assert lib._node_setup_command(y).startswith("test -n")
    y.write_text("name: x\nsetup_command: >\n  multi\n")
    with pytest.raises(lib.Stop, match="single quoted"):
        lib._node_setup_command(y)
    y.write_text("name: x\n")
    assert lib._node_setup_command(y) is None


def test_job_stops_as_root_and_still_writes_its_outputs(tmp_path, monkeypatch):
    spec = launch_spec()
    path = tmp_path / "g1b_spec.json"
    path.write_text(json.dumps(spec))
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    monkeypatch.setattr(lib, "image_identity", lambda s: {"digest": s["image"]["digest"]})
    monkeypatch.setattr(lib, "host_identity", lambda: {"euid": 0, "fqdn": "x"})
    with pytest.raises(lib.Stop, match="root"):
        lib.run_node_job(path, "mlab_ogbn_arxiv")
    record = json.loads((tmp_path / "job_record.json").read_text())
    assert "root" in record["stop"] and (tmp_path / "out.tar").is_file() and (tmp_path / "SHA256SUMS").is_file()
    assert record["stop_class"] == "infrastructure" and record["spec_sha256"] == lib._sha_file(path)


def test_job_stop_before_validation_still_writes_a_record(tmp_path, monkeypatch):
    path = tmp_path / "g1b_spec.json"
    path.write_text(json.dumps(copy.deepcopy(SPEC)))  # placeholders: refused at launch validation
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    with pytest.raises(lib.Stop, match="versions_sha256"):
        lib.run_node_job(path, "mlab_ogbn_arxiv")
    record = json.loads((tmp_path / "job_record.json").read_text())
    assert record["stop_class"] == "infrastructure" and "versions_sha256" in record["stop"]
    assert (tmp_path / "SHA256SUMS").read_text().count("job_record.json") == 1


def test_merge_parts_and_default_gate(tmp_path):
    out = tmp_path / "out"
    rows = synthetic_rows(["mlab_cifar10"])
    for part in lib.PARTS:
        (out / part[0]).mkdir(parents=True)
        part_rows = [r for r in rows if r["condition"] in {"default": ("default", "default_repeat")}.get(part[0], (part[0],))]
        (out / part[0] / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in part_rows))
    (out / "default" / "edits.json").write_text(json.dumps({"mlab_cifar10": EDITS["mlab_cifar10"]}))
    assert lib.default_gate(out)["deterministic"] is True
    node = lib.node_entry(SPEC, "mlab_cifar10")
    merged = lib.merge_parts(out, node)
    assert merged == {"expected": 460, "written": 460, "successful": 460, "divergent": 0}
    assert len(lib._rows(out / "runs.jsonl")) == 460 and (out / "edits.json").is_file()
    with pytest.raises(FileExistsError):
        lib.merge_parts(out, node)  # no overwrite
    (out / "runs.jsonl").rename(tmp_path / "merged_once.jsonl")
    with (out / "joint" / "runs.jsonl").open("a") as fh:
        fh.write(json.dumps(dict(rows[-1], run_id="extra")) + "\n")
    with pytest.raises(lib.Stop, match="461 rows, expected 460"):
        lib.merge_parts(out, node)
    bad = dict(rows[0], isolation=dict(GATE, log_intact=False))
    (out / "default" / "runs.jsonl").write_text(json.dumps(bad) + "\n")
    with pytest.raises(lib.Stop, match="not effectively isolated"):
        lib.merge_parts(out, node)
    nondet = synthetic_rows(["mlab_cifar10"], nondet_node="mlab_cifar10", parts=lib.PARTS[:1])
    (out / "default" / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in nondet))
    with pytest.raises(lib.NodeStop, match="determinism"):
        lib.default_gate(out)


def test_compare_freeze():
    assert lib.compare_freeze("b==2\na==1\n", "a==1\nb==2\n\n", "torch312") == ["a==1", "b==2"]
    with pytest.raises(lib.Stop, match=r"differs from the census freeze: \['b==2', 'b==3'\]"):
        lib.compare_freeze("a==1\nb==3\n", "a==1\nb==2\n", "torch312")
    with pytest.raises(lib.Stop, match="multiplicity"):
        lib.compare_freeze("a==1\na==1\n", "a==1\n", "torch312")


def test_check_staged_identity(tmp_path):
    (tmp_path / "sweep2" / "g1b").mkdir(parents=True)
    (tmp_path / "sweep2" / "g1b" / "g1b_lib.py").write_bytes((G1B / "g1b_lib.py").read_bytes())
    lib.check_staged_identity(tmp_path, {"g1b_lib.py": "sweep2/g1b/g1b_lib.py"})
    (tmp_path / "sweep2" / "g1b" / "g1b_lib.py").write_bytes(b"# changed\n")
    with pytest.raises(lib.Stop, match="differs from the pinned paper commit"):
        lib.check_staged_identity(tmp_path, {"g1b_lib.py": "sweep2/g1b/g1b_lib.py"})


def test_setup_keeps_its_log_on_timeout_and_failure(tmp_path, monkeypatch):
    harness = tmp_path / "h"
    (harness / "nodes" / "x").mkdir(parents=True)
    (harness / "nodes" / "x" / "node.yaml").write_text("name: x\nsetup_command: 'echo hello; exit 3'\n")
    node = {"node": "x", "node_dir": "nodes/x", "spec_path": "nodes/x/node.yaml"}
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(lib.Stop, match="rc 3"):
        lib.run_setup(harness, node, tmp_path, out)
    assert "hello" in (out / "setup.log").read_text()

    def timeout(*a, **k):
        raise lib.subprocess.TimeoutExpired(a[0], 7200, output="partial", stderr="err")
    monkeypatch.setattr(lib.subprocess, "run", timeout)
    with pytest.raises(lib.Stop, match="timed out"):
        lib.run_setup(harness, node, tmp_path, out)
    assert "partial" in (out / "setup.log").read_text() and "timeout" in (out / "setup.log").read_text()


# ---------------------------------------------------------------------------------------------- launch binding
def _git(cwd, *args):
    import subprocess
    env = dict(__import__("os").environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def launch_repo(tmp_path):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    (work / "docs" / "r1" / "authorizations").mkdir(parents=True)
    (work / "docs" / "r1" / "PLAN.md").write_text("| R1-A | x |\n| R1-B | y |\n")
    (work / "docs" / "r1" / "authorizations" / "n.md").write_text("n\n")
    _git(work, "checkout", "-q", "-b", "main")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "main")
    _git(work, "push", "-q", "origin", "main")
    (work / "job.txt").write_text("launch\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "launch")
    return work, _git(work, "rev-parse", "HEAD")


def test_verify_launch_binds_the_spec_commit_to_published_main(launch_repo):
    work, commit = launch_repo
    spec = {"paper": {"commit": commit}}
    assert lib.verify_launch(work, spec, ("R1-A", "R1-B"))["paper_commit"] == commit
    with pytest.raises(lib.Stop, match="PLAN row R1-C"):
        lib.verify_launch(work, spec, ("R1-A", "R1-C"))
    with pytest.raises(lib.Stop, match="full launch commit"):
        lib.verify_launch(work, {"paper": {"commit": commit[:12]}}, ("R1-A",))
    with pytest.raises(lib.Stop, match="exactly the spec's paper commit"):
        lib.verify_launch(work, {"paper": {"commit": _git(work, "rev-parse", "HEAD~1")}}, ("R1-A",))
    (work / "job.txt").write_text("dirty\n")
    with pytest.raises(lib.Stop, match="tracked-clean"):
        lib.verify_launch(work, spec, ("R1-A",))
    _git(work, "checkout", "-q", "--", "job.txt")
    # an authority file changed on the launch commit
    (work / "docs" / "r1" / "PLAN.md").write_text("| R1-A | x |\n| R1-B | y |\n| R1-Z | forged |\n")
    _git(work, "commit", "-qam", "plan change")
    with pytest.raises(lib.Stop, match="authority files differ"):
        lib.verify_launch(work, {"paper": {"commit": _git(work, "rev-parse", "HEAD")}}, ("R1-A",))
    # main moved on without this checkout fetching it
    other = work.parent / "other"
    _git(work.parent, "clone", "-q", str(work.parent / "origin.git"), str(other))
    (other / "x").write_text("x\n")
    _git(other, "add", "-A")
    _git(other, "commit", "-qm", "moved")
    _git(other, "push", "-q", "origin", "main")
    with pytest.raises(lib.Stop, match="fetch published main"):
        lib.verify_launch(work, spec, ("R1-A",))
    _git(work, "fetch", "-q", "origin")
    _git(work, "checkout", "-q", commit)
    with pytest.raises(lib.Stop, match="descend from published main"):
        lib.verify_launch(work, spec, ("R1-A",))


# ---------------------------------------------------------------------------------------------- assemble
def _sealed_job(root: Path, spec: dict, spec_sha: str, node: str, rows: list[dict], *, stop_class=None,
                **over) -> Path:
    import subprocess
    d = root / node
    (d / "out" / "default").mkdir(parents=True)
    body = "".join(json.dumps(r) + "\n" for r in rows)
    if stop_class == "node":
        (d / "out" / "default" / "runs.jsonl").write_text(body)
        (d / "out" / "default" / "edits.json").write_text(json.dumps({node: EDITS[node]}))
    else:
        (d / "out" / "runs.jsonl").write_text(body)
        (d / "out" / "edits.json").write_text(json.dumps({node: EDITS[node]}))
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=d, check=True)
    (d / "out").rename(root / f"_scratch_{node}")  # keep only what a sealed directory holds
    record = {"run_id": spec["run_id"], "node": node, "spec_sha256": spec_sha, "harness_commit": spec["harness"]["commit"],
              "image": {"digest": lib.IMAGE_DIGEST}, "gpu": {"name": lib.GPU_MODEL, "uuid": "GPU-1"},
              "host": {"fqdn": "h"}, "stop_class": stop_class, "label": lib.ENGINEERING_ONLY}
    record.update(over)
    (d / "job_record.json").write_text(json.dumps(record))
    lib._write_sums(d, ("out.tar", "job_record.json"))
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({"run_id": spec["run_id"], "node": node,
                                                     "job_record_sha256": lib._sha_file(d / "job_record.json")}))
    return d


def _all_sealed(tmp, **per_node):
    spec, spec_sha = copy.deepcopy(SPEC), "a" * 64
    rows = synthetic_rows()
    dirs = []
    for n in SPEC["nodes"]:
        node = n["node"]
        opts = per_node.get(node, {})
        node_rows = [r for r in rows if r["node"] == node]
        if opts.get("stop_class") == "node":
            node_rows = [r for r in node_rows if r["condition"] in ("default", "default_repeat")]
        dirs.append(_sealed_job(tmp / "sealed", spec, spec_sha, node, node_rows, **opts))
    return spec, spec_sha, dirs


def test_assemble_then_summarise(tmp_path):
    spec, spec_sha, dirs = _all_sealed(tmp_path, mlgym_fmnist={"stop_class": "node"})
    manifest = lib.assemble(dirs, spec, tmp_path / "run", spec_sha)
    assert len(manifest["jobs"]) == 6 and manifest["runs_sha256"] == lib._sha_file(tmp_path / "run" / "runs.jsonl")
    summary = lib.summarise(tmp_path / "run", spec, ROOT)
    assert summary["verdicts"]["mlgym_fmnist"]["qualifies_D21"] is False
    assert summary["verdicts"]["mlab_cifar10"]["paired_joint_n"] == [30] * 4
    with pytest.raises(lib.Stop, match="exists"):
        lib.assemble(dirs, spec, tmp_path / "run", spec_sha)


@pytest.mark.parametrize("over, needle", [
    ({"stop_class": "infrastructure"}, "stop_class"), ({"gpu": {"name": "NVIDIA L40S"}}, "gpu"),
    ({"image": {"digest": "x"}}, "image"), ({"harness_commit": "0" * 40}, "harness_commit"),
    ({"run_id": "other"}, "run_id"), ({"spec_sha256": "b" * 64}, "spec_sha256"),
])
def test_assemble_refuses_jobs_that_do_not_match_the_table(tmp_path, over, needle):
    spec, spec_sha, dirs = _all_sealed(tmp_path, mlab_imdb=over)
    with pytest.raises(lib.Stop, match=needle):
        lib.assemble(dirs, spec, tmp_path / "run", spec_sha)


def test_assemble_refuses_tampered_or_unsealed_outputs(tmp_path):
    spec, spec_sha, dirs = _all_sealed(tmp_path)
    with (dirs[1] / "out.tar").open("ab") as fh:
        fh.write(b"\0")
    with pytest.raises(lib.Stop, match="SHA256SUMS"):
        lib.assemble(dirs, spec, tmp_path / "run1", spec_sha)
    spec, spec_sha, dirs = _all_sealed(tmp_path / "b")
    (dirs[2] / "SEAL_RECEIPT.json").rename(tmp_path / "b" / "receipt_moved.json")
    with pytest.raises(lib.Stop, match="SEAL_RECEIPT"):
        lib.assemble(dirs, spec, tmp_path / "run2", spec_sha)
    spec, spec_sha, dirs = _all_sealed(tmp_path / "c")
    (dirs[3] / "SEAL_RECEIPT.json").write_text(json.dumps({"run_id": spec["run_id"], "node": SPEC["nodes"][3]["node"],
                                                            "job_record_sha256": "0" * 64}))
    with pytest.raises(lib.Stop, match="receipt"):
        lib.assemble(dirs, spec, tmp_path / "run3", spec_sha)
    spec, spec_sha, dirs = _all_sealed(tmp_path / "d")
    lib.assemble(dirs[:5], spec, tmp_path / "run4", spec_sha)  # assembling five nodes works; the summary refuses it
    with pytest.raises(lib.Stop, match="every spec node"):
        lib.summarise(tmp_path / "run4", spec, ROOT)


def test_delegated_cgroup_refusals(tmp_path, monkeypatch):
    fake_proc = tmp_path / "cg"
    fake_proc.write_text("0::/nonexistent/job\n")
    real = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: real(fake_proc) if str(self) == "/proc/self/cgroup"
                        else real(self, *a, **k))
    with pytest.raises(lib.Stop, match="not visible"):
        lib.delegated_cgroup()


# ---------------------------------------------------------------------------------------------- JDL + switch
def test_preview_stage_is_not_submittable(tmp_path):
    m = render_jdl.stage(G1B / "g1b_spec.json", tmp_path / "stage", preview=True)
    assert m["preview"] is True and len([f for f in m["files"] if f.endswith(".jdl")]) == 6
    text = (tmp_path / "stage" / "g1b_mlab_imdb.jdl").read_text()
    assert "executable = PREVIEW_NOT_SUBMITTABLE_g1b_job.sh" in text
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA H200"' in text and "+RequestWalltime = 47858" in text
    assert "container_image = docker://" + lib.IMAGE_DIGEST in text
    with pytest.raises(lib.Stop, match="not empty"):
        render_jdl.stage(G1B / "g1b_spec.json", tmp_path / "stage", preview=True)
    with pytest.raises(lib.Stop, match="versions_sha256"):
        render_jdl.stage(G1B / "g1b_spec.json", tmp_path / "stage2")


def _note(spec: dict, **over) -> str:
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "run_id": spec["run_id"], "image": lib.IMAGE_DIGEST,
              "paper_commit": spec["paper"]["commit"], "spec_sha256": hashlib.sha256(
                  (json.dumps(spec, indent=1)).encode()).hexdigest(),
              "versions_sha256": spec["image"]["versions_sha256"], "harness_commit": spec["harness"]["commit"],
              "nodes": ",".join(n["node"] for n in spec["nodes"]), "n_edits_per_node": "4", "runs_per_node": "460",
              "gpu_hours": "35", "P1": "PASS — R1-T1-HOST-H200 host check record x", "P2": "PASS — R1-TRACKG-G3-EARLY",
              "P3": "PASS — R1-G1B-EDITS", "P4": "PASS — reviewed", "P5": "PASS — versions record x",
              "P6": "PASS — R1-T1-IMAGE-V2 (test row)", "P7": "PASS — R1-G1B-TIMEOUT (test)",
              "d8_lock": "true", "labels_read": "none"}
    fields.update(over)
    return "# note\n" + "".join(f"{k}: {v}\n" for k, v in fields.items())


@pytest.fixture
def launch_stage(tmp_path):
    spec = launch_spec()
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec, indent=1))
    render_jdl.stage(path, tmp_path / "stage")
    note_dir = switch.REPO_ROOT / "docs" / "r1" / "authorizations"
    return spec, tmp_path / "stage", note_dir


BOUND = lambda repo, spec, rows: {"paper_commit": spec["paper"]["commit"], "rows": rows}  # noqa: E731


def test_switch_check_and_two_keys(launch_stage, tmp_path, monkeypatch):
    spec, stage, note_dir = launch_stage
    note = note_dir / "g1b_t1_h200_20991231.md"
    assert not note.exists()
    note.write_text(_note(spec))
    yes = lambda rel, raw: True  # noqa: E731
    try:
        ok = switch.check(stage, note, on_main=yes)
        assert ok["run_id"] == spec["run_id"] and ok["projection_gpu_hours"] < 35
        assert ok["spec_sha256"] == lib._sha_file(stage / "g1b_spec.json")
        with pytest.raises(switch.Stop, match="not committed on origin/main"):
            switch.check(stage, note, on_main=lambda rel, raw: False)
        monkeypatch.delenv(switch.ENABLE_ENV, raising=False)
        with pytest.raises(switch.Stop, match="disabled"):
            switch.submit(stage, note, enable=True, on_main=yes, launch_binding=BOUND)
        monkeypatch.setenv(switch.ENABLE_ENV, "1")
        with pytest.raises(switch.Stop, match="disabled"):
            switch.submit(stage, note, enable=False, on_main=yes, launch_binding=BOUND)

        def refuse(repo, spec, rows):
            raise lib.Stop("STOP: fetch published main before launch")
        with pytest.raises(lib.Stop, match="fetch published main"):
            switch.submit(stage, note, enable=True, node="mlab_ogbn_arxiv", on_main=yes, launch_binding=refuse)
        seen = []
        with pytest.raises(switch.Stop, match="first-record"):
            switch.submit(stage, note, enable=True, on_main=yes,
                          launch_binding=lambda r, s, rows: seen.append(rows) or BOUND(r, s, rows))
        assert seen == [switch.PLAN_ROWS] and "R1-G1B-EDITS" in switch.PLAN_ROWS and "R1-G1B-CAP" in switch.PLAN_ROWS
        calls = []
        monkeypatch.setattr(switch.subprocess, "run", lambda argv, **k: calls.append(argv) or
                            type("R", (), {"returncode": 0, "stdout": "1 job(s) submitted", "stderr": ""})())
        out = switch.submit(stage, note, enable=True, node="mlab_ogbn_arxiv", on_main=yes, launch_binding=BOUND)
        assert calls == [["condor_submit", "g1b_mlab_ogbn_arxiv.jdl"]] and len(out["submitted"]) == 1
        assert out["submitted"][0]["launch"]["paper_commit"] == spec["paper"]["commit"]
        with pytest.raises(switch.Stop, match="already submitted"):
            switch.submit(stage, note, enable=True, node="mlab_ogbn_arxiv", on_main=yes, launch_binding=BOUND)
    finally:
        note.unlink()  # this test's own temporary note inside the checkout


def _first_record(spec, spec_sha, **over):
    record = {"run_id": spec["run_id"], "node": switch.FIRST_NODE, "spec_sha256": spec_sha,
              "harness_commit": spec["harness"]["commit"], "image": {"digest": lib.IMAGE_DIGEST},
              "gpu": {"name": lib.GPU_MODEL}, "environment": {"freeze_sha256": spec["envs"]["torch312"]["sha256"]},
              "data": {"setup": "x"}, "cgroup_parent": "/sys/fs/cgroup/job",
              "parts": [{"part": "default", "stop": None, "written_rows": 10, "expected_runs": 10}],
              "runs": {"expected": 460, "written": 460}, "stop": None, "stop_class": None}
    record.update(over)
    return record


def _seal_first(root: Path, spec: dict, record: dict, *, receipt_sha=None) -> Path:
    d = root / spec["run_id"] / switch.FIRST_NODE
    d.mkdir(parents=True)
    (d / "job_record.json").write_text(json.dumps(record))
    (d / "out.tar").write_bytes(b"tar")
    lib._write_sums(d, ("out.tar", "job_record.json"))
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({"job_record_sha256": receipt_sha or
                                                     lib._sha_file(d / "job_record.json"),
                                                     "run_id": spec["run_id"], "node": switch.FIRST_NODE}))
    return d / "job_record.json"


def test_first_record_accepts_a_working_path_and_a_node_stop(tmp_path, monkeypatch):
    spec, sha = launch_spec(), "c" * 64
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "a")
    path = _seal_first(tmp_path / "a", spec, _first_record(spec, sha))
    assert switch.check_first_record(path, spec["run_id"], spec, sha)["first_record_stop_class"] is None
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "b")
    node_stop = _first_record(spec, sha, stop="STOP: fixed-seed determinism failed", stop_class="node", runs=None)
    path = _seal_first(tmp_path / "b", spec, node_stop)
    assert switch.check_first_record(path, spec["run_id"], spec, sha)["first_record_stop_class"] == "node"


@pytest.mark.parametrize("over, needle", [
    ({"stop_class": "infrastructure", "stop": "STOP: x"}, "stop_class"),
    ({"spec_sha256": "d" * 64}, "spec_sha256"), ({"harness_commit": "0" * 40}, "harness"),
    ({"image": {"digest": "x"}}, "image"), ({"gpu": {"name": "NVIDIA L40S"}}, "gpu"),
    ({"gpu": None}, "gpu"), ({"environment": {"freeze_sha256": None}}, "environment"),
    ({"environment": {"freeze_sha256": "e" * 64}}, "environment"), ({"cgroup_parent": None}, "cgroup"),
    ({"data": None}, "data"), ({"parts": []}, "default_part"),
    ({"parts": [{"part": "default", "stop": None, "written_rows": 9, "expected_runs": 10}]}, "default_part"),
    ({"parts": [{"part": "default", "stop": None, "written_rows": None, "expected_runs": None}]}, "default_part"),
    ({"runs": {"expected": 460, "written": 459}}, "rows"), ({"runs": None}, "rows"),
    ({"run_id": "other"}, "run_id"), ({"node": "mlab_imdb"}, "node"),
])
def test_first_record_refusals(tmp_path, monkeypatch, over, needle):
    spec, sha = launch_spec(), "c" * 64
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path)
    path = _seal_first(tmp_path, spec, _first_record(spec, sha, **over))
    with pytest.raises(switch.Stop, match=needle):
        switch.check_first_record(path, spec["run_id"], spec, sha)


def test_first_record_must_be_the_sealed_copy(tmp_path, monkeypatch):
    spec, sha = launch_spec(), "c" * 64
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "sealed")
    elsewhere = tmp_path / "copy" / spec["run_id"] / switch.FIRST_NODE
    elsewhere.mkdir(parents=True)
    (elsewhere / "job_record.json").write_text(json.dumps(_first_record(spec, sha)))
    with pytest.raises(switch.Stop, match="must be"):
        switch.check_first_record(elsewhere / "job_record.json", spec["run_id"], spec, sha)
    path = _seal_first(tmp_path / "sealed", spec, _first_record(spec, sha))
    with pytest.raises(switch.Stop, match="must be"):
        switch.check_first_record(path, "other_run", spec, sha)
    (path.parent / "out.tar").write_bytes(b"changed")
    with pytest.raises(switch.Stop, match="SHA256SUMS"):
        switch.check_first_record(path, spec["run_id"], spec, sha)
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "r")
    path = _seal_first(tmp_path / "r", spec, _first_record(spec, sha), receipt_sha="0" * 64)
    with pytest.raises(switch.Stop, match="receipt"):
        switch.check_first_record(path, spec["run_id"], spec, sha)
    with pytest.raises(switch.Stop, match="alone first"):
        switch.check_first_record(None, spec["run_id"], spec, sha)


@pytest.mark.parametrize("over, needle", [
    ({"approved": "false"}, "not approved"), ({"gpu_hours": "120"}, "R1-G1B-CAP"), ({"P1": "PASS — other"}, "cite"),
    ({"P4": "pending"}, "not recorded as PASS"), ({"label": "EVIDENCE"}, "ENGINEERING_ONLY"),
    ({"labels_read": "some"}, "labels_read"), ({"P3": "PASS — G1B-EDITS"}, "cite"),
    ({"paper_commit": ""}, "paper_commit"), ({"spec_sha256": ""}, "spec_sha256"),
    ({"P6": ""}, "P6"), ({"P6": "pending"}, "not recorded as PASS"), ({"P7": "PASS — other"}, "cite"),
])
def test_note_refusals(over, needle):
    with pytest.raises(switch.Stop, match=needle):
        switch.parse_note(_note(launch_spec(), **over))


def test_switch_refuses_a_changed_stage_or_mismatched_note(launch_stage):
    spec, stage, note_dir = launch_stage
    note = note_dir / "g1b_t1_h200_20991230.md"
    note.write_text(_note(spec, harness_commit="3" * 40))
    try:
        with pytest.raises(switch.Stop, match="harness_commit"):
            switch.check(stage, note, on_main=lambda rel, raw: True)
        for key, bad in (("paper_commit", "4" * 40), ("spec_sha256", "5" * 64)):
            note.write_text(_note(spec, **{key: bad}))
            with pytest.raises(switch.Stop, match=key):
                switch.check(stage, note, on_main=lambda rel, raw: True)
        note.write_text(_note(spec, gpu_hours="10"))
        with pytest.raises(switch.Stop, match="more GPU-hours"):
            switch.check(stage, note, on_main=lambda rel, raw: True)
        note.write_text(_note(spec))
        jdl = stage / "g1b_mlab_imdb.jdl"
        jdl.write_text(jdl.read_text().replace("request_GPUs = 1", "request_GPUs = 2"))
        with pytest.raises(switch.Stop, match="changed after staging"):
            switch.check(stage, note, on_main=lambda rel, raw: True)
    finally:
        note.unlink()


# ---------------------------------------------------------------------------------------------- round-2 notes
def test_assemble_refuses_a_row_of_another_node_and_a_duplicate_node(tmp_path):
    spec, spec_sha = copy.deepcopy(SPEC), "a" * 64
    rows = synthetic_rows()
    dirs = []
    for n in SPEC["nodes"]:
        node_rows = [r for r in rows if r["node"] == n["node"]]
        if n["node"] == "mlab_imdb":
            node_rows[0] = dict(node_rows[0], node="mlab_cifar10")
        dirs.append(_sealed_job(tmp_path / "sealed", spec, spec_sha, n["node"], node_rows))
    with pytest.raises(lib.Stop, match="names node"):
        lib.assemble(dirs, spec, tmp_path / "run", spec_sha)
    spec, spec_sha, dirs = _all_sealed(tmp_path / "b")
    with pytest.raises(lib.Stop, match="two sealed directories"):
        lib.assemble(dirs + dirs[:1], spec, tmp_path / "run2", spec_sha)


def test_summarise_refuses_an_assembly_of_another_spec(tmp_path):
    spec, spec_sha, dirs = _all_sealed(tmp_path)
    lib.assemble(dirs, spec, tmp_path / "run", spec_sha)
    other = copy.deepcopy(spec)
    other["run_id"] = "other_run"
    with pytest.raises(lib.Stop, match="another spec"):
        lib.summarise(tmp_path / "run", other, ROOT)


def test_job_runs_the_staged_identity_check(tmp_path, monkeypatch):
    path = tmp_path / "g1b_spec.json"
    path.write_text(json.dumps(launch_spec()))
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    for name in ("image_identity", "gpu_identity"):
        monkeypatch.setattr(lib, name, lambda *a: {"digest": lib.IMAGE_DIGEST, "name": lib.GPU_MODEL})
    monkeypatch.setattr(lib, "host_identity", lambda: {"euid": 1000})
    monkeypatch.setattr(lib, "clone_at", lambda repo, commit, dest: {"commit": commit})

    def refuse(paper_dir, files):
        assert files == {"g1b_lib.py": "sweep2/g1b/g1b_lib.py"}
        raise lib.Stop("STOP: the staged g1b_lib.py differs from the pinned paper commit")
    monkeypatch.setattr(lib, "check_staged_identity", refuse)
    with pytest.raises(lib.Stop, match="staged g1b_lib.py differs"):
        lib.run_node_job(path, "mlab_ogbn_arxiv")
    assert json.loads((tmp_path / "job_record.json").read_text())["stop_class"] == "infrastructure"


def test_timeout_log_decodes_bytes():
    assert lib._text(b"caf\xc3\xa9") == "caf\u00e9" and lib._text(None) == "" and lib._text("x") == "x"


def test_engine_rows_pass_the_paper_gate_contract():
    """Cross-repo contract (review r2 M2): a row built by the harness engine's row_of passes check_row_gate, and
    dropping any of the six isolation fields makes it fail."""
    import os
    root = Path(os.environ.get("AR_HARNESS_ROOT", "/nonexistent")) / "src"
    if not (root / "autoresearch" / "trackg" / "noise_floor.py").is_file():
        pytest.skip("AR_HARNESS_ROOT does not point at a harness with the noise-floor engine")
    sys.path.insert(0, str(root))
    try:
        nf = __import__("autoresearch.trackg.noise_floor", fromlist=["row_of"])
    finally:
        sys.path.remove(str(root))
    gate = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True, "parent_traced_by": None,
            "parent_dumpable_at_accept": False}
    record = {"outcome": {"kind": "ok", "value": 0.5}, "isolation": dict(gate, extra="ignored"),
              "elapsed_seconds_info_only": 1.0}
    chunk = type("C", (), {"node": "mlab_cifar10"})()
    result = type("R", (), {"record": record, "run_id": "r"})()
    run = {"config": "c0", "condition": "default", "train_seed": None, "split_seed": None}
    row = nf.row_of(chunk, run, result, "f" * 64)
    lib.check_row_gate(row)
    variants = [{k: v for k, v in gate.items() if k != key} for key in ("effective", "waivers", "exceptions",
                                                                        "log_intact")]
    variants += [dict(gate, parent_traced_by=4242), dict(gate, parent_dumpable_at_accept=True)]
    for iso in variants:   # a missing core field, or a traced/dumpable parent, fails the paper gate
        broken = dict(record, isolation=iso)
        with pytest.raises(lib.Stop):
            lib.check_row_gate(nf.row_of(chunk, run, type("R", (), {"record": broken, "run_id": "r"})(), "f" * 64))
