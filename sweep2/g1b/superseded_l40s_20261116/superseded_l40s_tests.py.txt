"""Synthetic tests for the G.1b T1 GPU-node noise-floor job (no job, no network, no GPU, no submission).

Covers: template validation, the G.0 placeholder refusal (empty census / placeholder nodes / placeholder run times
and edit sets), the D21 qualification math (2 material edits, mean plug-in P(wrong) >= 0.10, sigma_joint > 0,
30 seeds fixed), the 60 GPU-h / 48 h and chunk-wall STOPs, chunk expansion, determinism pairing, and the rendered
JDL requirements. All node ids used here are synthetic fixtures (`synthetic_t1_node_*`), never G.0 names.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
G1B = ROOT / "sweep2" / "g1b"
sys.path.insert(0, str(G1B))
import g1b_lib as lib  # noqa: E402
import render_jdl  # noqa: E402

TEMPLATE = json.loads((G1B / "g1b_spec.template.json").read_text())


def complete_spec(run_seconds=90.0, node_count=4) -> dict:
    """A synthetic complete spec (G.0 census filled) for validation/D21/JDL tests."""
    spec = copy.deepcopy(TEMPLATE)
    letters = "abcdefghij"[:node_count]
    nodes = [f"synthetic_t1_node_{c}" for c in letters]
    spec["run_id"] = "g1b-test-a"
    spec["g0_census"] = {"status": "complete", "report_path": "docs/r1/reports/synthetic/G0_CENSUS_TEST.md",
                         "report_sha256": "1" * 64, "host_platform": "ada-rtx6000-ada", "nodes": nodes}
    spec["plan"]["candidate_nodes"] = [
        {"node_id": node, "run_seconds": run_seconds, "metric": "val_score", "direction": "higher",
         "request_memory_mb": lib.MEMORY_FLOOR_MB, "request_disk_kb": lib.DISK_FLOOR_KB,
         "edit_set": [{"edit_id": f"edit_{k}", "kind": "code_diff", "patch_sha256": f"{k:064x}"}
                      for k in range(1, 6)],
         "runner": {"module": "r1.noise.t1_noise_runner", "entrypoint": "run_one",
                    "module_sha256": "2" * 64}}
        for node in nodes]
    spec["paper"]["commit"] = "3" * 40
    spec["harness"]["commit"] = "4" * 40
    spec["harness"]["pin_evidence"] = "docs/r1/reviews/T1_PORT_REVIEW_TEST.md"
    spec["env"]["libraries"] = {"python": "3.13.16", "numpy": "2.4.4", "scikit-learn": "1.8.0", "torch": "2.9.0"}
    chunk = max(lib.chunk_plan(spec["plan"]), key=lambda c: c["walltime_s"])
    spec["chunk"] = {k: chunk[k] for k in ("chunk_id", "node", "condition", "seed_start", "seed_count")}
    return spec


# --------------------------------------------------------------------------- template + G.0 placeholder refusal
def test_template_is_refused_until_the_g0_census_is_complete():
    with pytest.raises(lib.Stop, match="G.0 census incomplete"):
        lib.validate_spec(copy.deepcopy(TEMPLATE))


def test_g0_empty_or_placeholder_nodes_are_refused():
    spec = complete_spec()
    spec["g0_census"]["nodes"] = []
    spec["plan"]["candidate_nodes"] = []
    with pytest.raises(lib.Stop, match="named no candidate nodes"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["g0_census"]["nodes"][0] = "G0_PENDING_NODE_01"
    spec["plan"]["candidate_nodes"][0]["node_id"] = "G0_PENDING_NODE_01"
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"].append(copy.deepcopy(spec["plan"]["candidate_nodes"][0]))
    spec["plan"]["candidate_nodes"][-1]["node_id"] = "synthetic_extra_node"
    with pytest.raises(lib.Stop, match="exactly the nodes"):
        lib.validate_spec(spec)


def test_placeholder_census_report_and_run_time_are_refused():
    spec = complete_spec()
    spec["g0_census"]["report_sha256"] = "0" * 64
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["g0_census"]["report_path"] = "G0_CENSUS_PENDING"
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["run_seconds"] = None
    with pytest.raises(lib.Stop, match="run_seconds"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["run_seconds"] = lib.RUN_SECONDS_CEILING + 1
    with pytest.raises(lib.Stop, match="run_seconds"):
        lib.validate_spec(spec)


def test_placeholder_edit_set_and_runner_are_refused():
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["edit_set"] = spec["plan"]["candidate_nodes"][0]["edit_set"][:4]
    with pytest.raises(lib.Stop, match="edit_set"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["edit_set"][2]["edit_id"] = "G0_PENDING_EDIT_03"
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["edit_set"][2]["patch_sha256"] = "0" * 64
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["plan"]["candidate_nodes"][0]["runner"]["module"] = "G0_PENDING_RUNNER_MODULE"
    with pytest.raises(lib.Stop, match="placeholder"):
        lib.validate_spec(spec)


def test_engineering_only_and_no_authorization_note():
    spec = complete_spec()
    assert lib.validate_spec(spec)["label"] == lib.ENGINEERING_ONLY
    for change in (lambda s: s.__setitem__("label", "EVIDENCE"),
                   lambda s: s.__setitem__("label_source", {"authorization": "x.md"})):
        bad = complete_spec()
        change(bad)
        with pytest.raises(lib.Stop, match="ENGINEERING_ONLY|authorization"):
            lib.validate_spec(bad)


def test_seed_count_split_policy_and_server_setting_are_fail_closed():
    for mutate in (lambda s: s["plan"].__setitem__("seeds_per_condition", 10),
                   lambda s: s["plan"].__setitem__("split_policy", "fixed"),
                   lambda s: s["plan"].__setitem__("conditions", ["train", "split"]),
                   lambda s: s["plan"].__setitem__("configs", 5),
                   lambda s: s["measurement"].__setitem__("workers", 16),
                   lambda s: s["measurement"]["seed_bases"].__setitem__("joint", 7001),
                   lambda s: s["proposer_environment"]["server"].__setitem__("ctx", 16384),
                   lambda s: s["proposer_environment"]["model"].__setitem__("use", "fetch"),
                   lambda s: s["requirements"].__setitem__("gpu_device_name", "NVIDIA H100"),
                   lambda s: s["requirements"].__setitem__("cpu_model_number", 1),
                   lambda s: s["requirements"].__setitem__("machine_regex", "^g36")):
        spec = complete_spec()
        mutate(spec)
        with pytest.raises(lib.Stop):
            lib.validate_spec(spec)


def test_chunk_must_be_in_the_pre_declared_plan():
    spec = complete_spec()
    spec["chunk"]["chunk_id"] = "synthetic_t1_node_a-train-s00-30"
    with pytest.raises(lib.Stop, match="not in the pre-declared chunk plan"):
        lib.validate_spec(spec)
    spec = complete_spec()
    spec["chunk"]["node"] = "synthetic_t1_node_b"
    with pytest.raises(lib.Stop, match="does not match the pre-declared chunk"):
        lib.validate_spec(spec)


# --------------------------------------------------------------------------- projection / caps / chunking
def test_projection_uses_552_runs_per_node_and_the_measured_caps():
    spec = complete_spec(run_seconds=90.0, node_count=4)
    loaded = lib.validate_spec(spec)
    proj = loaded["projection"]
    assert lib.runs_per_node(spec["plan"]) == 552
    assert proj["total_runs"] == 4 * 552
    assert proj["total_gpu_hours"] == pytest.approx(4 * 552 * 90 / 3600, abs=1e-3)
    assert proj["total_gpu_hours"] <= lib.CAP_TOTAL_GPU_HOURS
    assert proj["max_chunk_wall_seconds"] <= lib.MAX_CHUNK_WALL_SECONDS
    assert proj["chunks"] == 4 * 10  # three conditions x 3 seed parts + one determinism chunk per node
    assert proj["serial_wall_hours"] == proj["total_gpu_hours"]  # workers = 1: GPU-hours are one-slot wall hours
    assert proj["per_node_wall_hours"] == pytest.approx(552 * 90 / 3600, abs=1e-3)
    assert proj["slots_required_for_48h_wall"] == 2  # 55.2 GPU-h needs two concurrent slots for a <48 h wall


def test_gpu_hour_cap_stops_the_job_at_60_gpu_hours():
    # 4 nodes x 120 s/run and 8 nodes x 60 s/run both project 73.6 GPU-h: author STOP (R1-SWEEP2-SETTINGS (5)).
    for run_seconds, node_count, expected in ((120.0, 4, 73.6), (60.0, 8, 73.6)):
        spec = complete_spec(run_seconds=run_seconds, node_count=node_count)
        with pytest.raises(lib.Stop, match="author STOP|GPU-h cap"):
            lib.validate_spec(spec)
        assert lib.projection(spec["plan"])["total_gpu_hours"] == pytest.approx(expected, abs=0.05)
    # 4 nodes x 90 s fits the cap; 5 nodes x 90 s does not.
    assert lib.validate_spec(complete_spec(90.0, 4))["projection"]["total_gpu_hours"] == pytest.approx(55.2)
    with pytest.raises(lib.Stop, match="GPU-h cap"):
        lib.validate_spec(complete_spec(90.0, 5))


def test_caps_may_not_be_raised_and_chunk_wall_is_capped():
    for key, value in (("max_total_gpu_hours", 120.0), ("max_chunk_wall_hours", 100.0),
                       ("max_chunk_wall_seconds", 30000)):
        spec = complete_spec()
        spec["caps"][key] = value
        with pytest.raises(lib.Stop, match="raises the pre-declared"):
            lib.validate_spec(spec)
    # a lowered cap is allowed but the projection is still checked against it
    spec = complete_spec()
    spec["caps"]["max_total_gpu_hours"] = 10.0
    with pytest.raises(lib.Stop, match="GPU-h cap"):
        lib.validate_spec(spec)


def test_chunk_plan_keeps_every_chunk_inside_the_measured_wall():
    for run_seconds in (30.0, 60.0, 90.0, 120.0):
        plan = complete_spec(run_seconds=run_seconds, node_count=1)["plan"]
        chunks = lib.chunk_plan(plan)
        assert all(c["walltime_s"] <= lib.MAX_CHUNK_WALL_SECONDS for c in chunks)
        assert all(c["runs"] > 0 for c in chunks)
        for condition in lib.CONDITIONS:
            covered = sum(c["seed_count"] for c in chunks if c["condition"] == condition)
            assert covered == lib.SEEDS_PER_CONDITION
        defaults = [c for c in chunks if c["condition"] == "default"]
        assert len(defaults) == 1 and defaults[0]["runs"] == 12


def test_chunk_runs_expand_to_the_e1_run_schema():
    spec = complete_spec(run_seconds=90.0, node_count=1)
    plan = spec["plan"]
    train = next(c for c in lib.chunk_plan(plan) if c["condition"] == "train")
    runs = lib.chunk_runs(plan, train)
    assert len(runs) == train["seed_count"] * 6
    assert {r["config"] for r in runs} == {f"c{k}" for k in range(6)}
    # config is the outer loop: the first seed_count rows are c0 at seed_start, seed_start+1, ...
    assert [r["train_seed"] for r in runs[:train["seed_count"]]] == [
        lib.SEED_BASES["train"] + train["seed_start"] + i for i in range(train["seed_count"])]
    assert all(r["split_seed"] is None for r in runs)
    joint = next(c for c in lib.chunk_plan(plan) if c["condition"] == "joint")
    jruns = lib.chunk_runs(plan, joint)
    assert all(r["train_seed"] == r["split_seed"] - 1000 for r in jruns)
    default = next(c for c in lib.chunk_plan(plan) if c["condition"] == "default")
    druns = lib.chunk_runs(plan, default)
    assert len(druns) == 12 and {r["condition"] for r in druns} == {"default", "default_repeat"}


def test_determinism_check_pairs_default_runs():
    rows = [{"node": "n", "config": "c0", "condition": "default", "metric": 0.5, "success": True},
            {"node": "n", "config": "c0", "condition": "default_repeat", "metric": 0.5, "success": True}]
    assert lib.determinism_check(rows)["deterministic"] is True
    rows[1]["metric"] = 0.5001
    check = lib.determinism_check(rows)
    assert check["deterministic"] is False and check["configs"]["c0"]["bit_identical"] is False


# --------------------------------------------------------------------------- D21 rule math
def _deltas(mean, sd, n=30):
    """Symmetric synthetic joint deltas with a fixed mean and (ddof=1) sd."""
    half = n // 2
    return [mean + sd, mean - sd] * half


def _material_edit(mean=0.003, sd=0.006):
    stats = lib.edit_stats(_deltas(mean, sd))
    assert stats["material"] is True
    return stats


def test_d21_edit_statistics_resolved_material_and_p_wrong():
    material = _material_edit()
    assert material["delta_hat_J"] == pytest.approx(0.003)
    assert material["sd_joint"] == pytest.approx(0.006 * (30 / 29) ** 0.5)
    assert material["resolved"] is True and material["material"] is True
    # |delta| < 0.002: resolved but not material (D21's effect floor)
    small = lib.edit_stats(_deltas(0.001, 0.0002))
    assert small["resolved"] is True and small["material"] is False
    # |delta| below 2 se: not resolved, hence not material
    unresolved = lib.edit_stats(_deltas(0.001, 0.01))
    assert unresolved["resolved"] is False and unresolved["material"] is False
    assert material["p_wrong"] == pytest.approx(lib._phi(-abs(0.003) / material["sd_joint"]))


def test_d21_requires_two_material_edits():
    good = lib.d21_qualify([_material_edit()], sigma_joint=0.01, seeds_per_condition=30)
    assert good["checks"]["material_edits_ge_2"] is False and good["qualifies_D21"] is False
    two = lib.d21_qualify([_material_edit(), _material_edit(mean=0.004, sd=0.008)],
                          sigma_joint=0.01, seeds_per_condition=30)
    assert two["n_material"] == 2 and two["qualifies_D21"] is True


def test_d21_requires_mean_plug_in_p_wrong_at_least_0_10():
    # |delta|/sd = 1.7 gives P(wrong) ~ 0.045: material, but the mean over material edits is below 0.10.
    low = [_material_edit(mean=0.0102, sd=0.006), _material_edit(mean=0.0102, sd=0.006)]
    out = lib.d21_qualify(low, sigma_joint=0.01, seeds_per_condition=30)
    assert out["n_material"] == 2
    assert out["mean_p_wrong_material"] == pytest.approx(0.045, abs=0.005)
    assert out["checks"]["mean_p_wrong_ge_0.10"] is False and out["qualifies_D21"] is False
    out = lib.d21_qualify([_material_edit(), _material_edit(mean=0.004, sd=0.008)],
                          sigma_joint=0.01, seeds_per_condition=30)
    assert out["mean_p_wrong_material"] >= lib.D21_MIN_MEAN_P_WRONG and out["qualifies_D21"] is True


def test_d21_requires_positive_sigma_joint():
    edits = [_material_edit(), _material_edit(mean=0.004, sd=0.008)]
    assert lib.d21_qualify(edits, 0.01, 30)["qualifies_D21"] is True
    out = lib.d21_qualify(edits, 0.0, 30)
    assert out["checks"]["sigma_joint_gt_0"] is False and out["qualifies_D21"] is False


def test_d21_seed_count_is_fixed_at_30():
    edits = [_material_edit(), _material_edit(mean=0.004, sd=0.008)]
    for seeds in (10, 29, 31):
        out = lib.d21_qualify(edits, 0.01, seeds)
        assert out["checks"]["seeds_per_condition_is_30"] is False and out["qualifies_D21"] is False
    assert lib.d21_qualify(edits, 0.01, 30)["qualifies_D21"] is True


# --------------------------------------------------------------------------- JDL requirements
def test_renderer_pins_the_l40s_cpu_class_and_transfers_the_measured_layout(tmp_path):
    spec = complete_spec(run_seconds=90.0, node_count=4)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out = tmp_path / "g1b_job.jdl"
    render_jdl.main([str(spec_path), "--out", str(out), "--stage-dir", str(tmp_path / "stage")])
    jdl = out.read_text()
    assert "universe = container" in jdl
    assert f"container_image = docker://{lib.IMAGE_DIGEST}" in jdl
    assert 'TARGET.CloudSite =?= "BwForCluster-Nemo2"' in jdl
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"' in jdl
    assert 'TARGET.Arch == "X86_64"' in jdl and 'TARGET.OpSys == "LINUX"' in jdl
    assert f"TARGET.Cpus >= {lib.MIN_CPUS}" in jdl
    assert f"TARGET.CpuFamily =?= {lib.CPU_FAMILY}" in jdl
    assert f"TARGET.CpuModelNumber =?= {lib.CPU_MODEL_NUMBER}" in jdl
    assert "regexp(" not in jdl and "machine_regex" not in jdl and "ProvidesEtpCeph" not in jdl
    assert "docker_image" not in jdl and "RequestGPUMemory" not in jdl
    assert f"request_memory = {lib.MEMORY_FLOOR_MB}" in jdl and f"request_disk = {lib.DISK_FLOOR_KB}" in jdl
    assert "request_GPUs = 1" in jdl and "+RemoteJob = True" in jdl and "+G1BPreview" not in jdl
    assert "transfer_input_files = g1b_job.sh,g1b_lib.py,g1b_spec.json" in jdl
    assert f"transfer_output_files = {lib.TRANSFER_OUTPUTS}" in jdl
    walltime = int(jdl.split("+RequestWalltime = ")[1].splitlines()[0])
    assert 0 < walltime <= lib.MAX_CHUNK_WALL_SECONDS


def test_renderer_refuses_the_template_and_the_preview_outside_its_dir(tmp_path, monkeypatch):
    with pytest.raises(lib.Stop, match="G.0 census incomplete"):
        render_jdl.main([str(G1B / "g1b_spec.template.json"), "--out", str(tmp_path / "x.jdl"),
                         "--stage-dir", str(tmp_path / "stage")])
    with pytest.raises(lib.Stop, match="layout-preview"):
        render_jdl.main([str(G1B / "g1b_spec.template.json"), "--out", str(tmp_path / "x.jdl"),
                         "--stage-dir", str(tmp_path / "stage2"), "--layout-preview"])


def test_layout_preview_is_marked_not_submittable(tmp_path, monkeypatch):
    monkeypatch.setattr(render_jdl, "PREVIEW_DIR", tmp_path)
    out = tmp_path / "g1b_layout_preview.jdl"
    render_jdl.main([str(G1B / "g1b_spec.template.json"), "--out", str(out),
                     "--stage-dir", str(tmp_path / "stage"), "--layout-preview"])
    jdl = out.read_text()
    assert "+G1BPreview = True" in jdl and "LAYOUT PREVIEW ONLY" in jdl and "NOT FOR SUBMISSION" in jdl
    assert f"container_image = docker://{lib.IMAGE_DIGEST}" in jdl
    staged = json.loads((tmp_path / "stage" / "g1b_spec.json").read_text())
    with pytest.raises(lib.Stop):
        lib.validate_spec(staged)


def test_job_entry_is_engineering_only_and_never_submits():
    script = (G1B / "g1b_job.sh").read_text()
    assert "ENGINEERING_ONLY" in script
    assert "/opt/r1/envs/trackp/bin/python" in script
    assert "condor_submit" not in script
    assert "STOP" in script and "out.tar" in script


def test_schema_and_constants_agree():
    schema = json.loads((G1B / "g1b_spec.schema.json").read_text())
    caps = schema["properties"]["caps"]["properties"]
    assert caps["max_total_gpu_hours"]["maximum"] == lib.CAP_TOTAL_GPU_HOURS
    assert caps["max_chunk_wall_hours"]["maximum"] == lib.CAP_CHUNK_WALL_HOURS
    assert caps["max_chunk_wall_seconds"]["maximum"] == lib.MAX_CHUNK_WALL_SECONDS
    req = schema["properties"]["requirements"]["properties"]
    assert req["cloud_site"]["const"] == lib.CLOUD_SITE
    assert req["gpu_device_name"]["const"] == lib.GPU_MODEL
    assert req["cpu_family"]["const"] == lib.CPU_FAMILY
    assert req["cpu_model_number"]["const"] == lib.CPU_MODEL_NUMBER
    assert schema["properties"]["plan"]["properties"]["seeds_per_condition"]["const"] == lib.SEEDS_PER_CONDITION
    assert schema["properties"]["plan"]["properties"]["split_policy"]["const"] == lib.SPLIT_POLICY
    assert schema["properties"]["measurement"]["properties"]["workers"]["const"] == lib.WORKERS
    for key in ("schema", "kind", "label", "run_id", "chunk", "g0_census", "plan", "image", "paper", "harness",
                "env", "proposer_environment", "measurement", "caps", "requirements"):
        assert key in TEMPLATE
