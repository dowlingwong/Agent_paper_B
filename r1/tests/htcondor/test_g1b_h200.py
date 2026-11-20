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
import render_jdl  # noqa: E402

SPEC = json.loads((G1B / "g1b_spec.json").read_text())


def launch_spec() -> dict:
    spec = copy.deepcopy(SPEC)
    spec["image"]["versions_sha256"] = "1" * 64
    spec["paper"]["commit"] = "2" * 40
    spec["edit_count"]["authority"] = "G1B-EDITS (test)"
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
    spec["edit_count"]["authority"] = "TODO_AUTHOR_DECISION"
    with pytest.raises(lib.Stop, match="author's decision"):
        lib.validate_spec(spec, launch=True)


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
    (lambda s: s["nodes"][0].update(deployed_pin_sha256="x"), "deployed_pin_sha256"),
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


def test_spec_pins_match_the_census_values():
    by = {n["node"]: n for n in SPEC["nodes"]}
    assert by["mlab_cifar10"]["deployed_pin_sha256"].startswith("a459b3d8")
    assert by["mlab_cifar10"]["committed_pin_sha256"].startswith("1f047ad7")
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
    assert chunk["frozen_pin_sha256"] == node["deployed_pin_sha256"] and chunk["isolation_waivers"] == {}
    assert chunk["runs"][0] == {"config": "c0", "condition": "joint", "train_seed": 3001, "split_seed": 3001}
    assert chunk["runs"][-1] == {"config": "c4", "condition": "joint", "train_seed": 3030, "split_seed": 3030}
    seeds = {r["train_seed"] for p in lib.PARTS for r in lib.expected_runs(4, p[1], p[2])} - {None}
    assert not seeds & set(range(7001, 7011)) and not seeds & set(range(9001, 10000))


# ---------------------------------------------------------------------------------------------- D21 + summary
def _row(node, config, condition, t, s, metric, **iso):
    gate = {"effective": True, "waivers": {}, "exceptions": []}
    gate.update(iso)
    return {"node": node, "config": config, "condition": condition, "train_seed": t, "split_seed": s,
            "metric": metric, "success": metric is not None, "wall_seconds": 1.0, "run_id": f"{config}_{condition}_{t}_{s}",
            "isolation": gate}


def synthetic_run_dir(tmp: Path, *, nondet_node=None, drop=False, bad_gate=False) -> Path:
    import random
    rows = []
    rnd = random.Random(1)
    effects = [0.0, 0.004, -0.003, 0.0005, 0.02]  # c0..c4
    for node in [n["node"] for n in SPEC["nodes"]]:
        for p in lib.PARTS:
            for run in lib.expected_runs(4, p[1], p[2]):
                k = int(run["config"][1:])
                seed = run["train_seed"] or run["split_seed"] or 0
                noise = random.Random(hash((node, run["condition"], seed)) & 0xFFFF).gauss(0, 0.003) if seed else 0.0
                metric = 0.5 + effects[k] + noise
                if node == nondet_node and run["condition"] == "default_repeat" and k == 0:
                    metric += 1e-6
                rows.append(_row(node, run["config"], run["condition"], run["train_seed"], run["split_seed"],
                                 round(metric, 9)))
    if drop:
        rows.pop(5)
    if bad_gate:
        rows[7]["isolation"]["waivers"] = {"root": "x"}
    d = tmp / "run"
    d.mkdir()
    (d / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    edits = {n["node"]: [{"symbol": f"E{k}", "old": "baseline", "new": f"E{k}.diff"} for k in range(1, 5)]
             for n in SPEC["nodes"]}
    (d / "edits.json").write_text(json.dumps(edits))
    return d


def test_summarise_applies_the_pinned_rule_with_the_double_check(tmp_path):
    summary = lib.summarise(synthetic_run_dir(tmp_path), SPEC, ROOT)
    assert summary["screening_funnel"]["measured"] == 6
    v = summary["verdicts"]["mlab_cifar10"]
    assert v["checks"]["seeds_per_condition_is_30"] and v["n_edits"] == 4
    assert v["checks"]["material_edits_ge_2"] and v["sigma_joint"] > 0
    assert (tmp_path / "run" / "summary.json").is_file()


def test_summarise_stops_on_gaps_and_unisolated_rows_and_flags_nondeterminism(tmp_path):
    with pytest.raises(lib.Stop, match="coverage"):
        lib.summarise(synthetic_run_dir(tmp_path / "a", drop=True), SPEC, ROOT) if (tmp_path / "a").mkdir() is None else None
    with pytest.raises(lib.Stop, match="not effectively isolated"):
        lib.summarise(synthetic_run_dir(tmp_path / "b", bad_gate=True), SPEC, ROOT) if (tmp_path / "b").mkdir() is None else None
    (tmp_path / "c").mkdir()
    summary = lib.summarise(synthetic_run_dir(tmp_path / "c", nondet_node="mlab_imdb"), SPEC, ROOT)
    assert summary["verdicts"]["mlab_imdb"]["qualifies_D21"] is False
    assert summary["screening_funnel"]["failed_determinism"] == 1


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
              "versions_sha256": spec["image"]["versions_sha256"], "harness_commit": spec["harness"]["commit"],
              "nodes": ",".join(n["node"] for n in spec["nodes"]), "n_edits_per_node": "4", "runs_per_node": "460",
              "gpu_hours": "35", "P1": "PASS — R1-T1-HOST-H200 host check record x", "P2": "PASS — R1-TRACKG-G3-EARLY",
              "P3": "PASS — G1B-EDITS row x", "P4": "PASS — reviewed", "P5": "PASS — versions record x",
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


def test_switch_check_and_two_keys(launch_stage, tmp_path, monkeypatch):
    spec, stage, note_dir = launch_stage
    note = note_dir / "g1b_t1_h200_20991231.md"
    assert not note.exists()
    note.write_text(_note(spec))
    try:
        ok = switch.check(stage, note, on_main=lambda rel, raw: True)
        assert ok["run_id"] == spec["run_id"] and ok["projection_gpu_hours"] < 35
        with pytest.raises(switch.Stop, match="not committed on origin/main"):
            switch.check(stage, note, on_main=lambda rel, raw: False)
        monkeypatch.delenv(switch.ENABLE_ENV, raising=False)
        with pytest.raises(switch.Stop, match="disabled"):
            switch.submit(stage, note, enable=True, on_main=lambda rel, raw: True)
        monkeypatch.setenv(switch.ENABLE_ENV, "1")
        with pytest.raises(switch.Stop, match="disabled"):
            switch.submit(stage, note, enable=False, on_main=lambda rel, raw: True)
        with pytest.raises(switch.Stop, match="first-record"):
            switch.submit(stage, note, enable=True, on_main=lambda rel, raw: True)
        calls = []
        monkeypatch.setattr(switch.subprocess, "run", lambda argv, **k: calls.append(argv) or
                            type("R", (), {"returncode": 0, "stdout": "1 job(s) submitted", "stderr": ""})())
        out = switch.submit(stage, note, enable=True, node="mlab_ogbn_arxiv", on_main=lambda rel, raw: True)
        assert calls == [["condor_submit", "g1b_mlab_ogbn_arxiv.jdl"]] and len(out["submitted"]) == 1
        with pytest.raises(switch.Stop, match="already submitted"):
            switch.submit(stage, note, enable=True, node="mlab_ogbn_arxiv", on_main=lambda rel, raw: True)
    finally:
        note.unlink()  # this test's own temporary note inside the checkout


@pytest.mark.parametrize("over, needle", [
    ({"approved": "false"}, "not approved"), ({"gpu_hours": "120"}, "R1-G1B-CAP"), ({"P1": "PASS — other"}, "cite"),
    ({"P4": "pending"}, "not recorded as PASS"), ({"label": "EVIDENCE"}, "ENGINEERING_ONLY"),
    ({"labels_read": "some"}, "labels_read"),
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
