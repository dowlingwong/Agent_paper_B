"""Track P P.4 phase-1 runner unit: ``r1/c3/train/p4_phase1.py`` (the env3 freeze rule of R1-TRACKP-V21-FREEZE, the
receipted partition pins, the learning-curve subsets, the instance-cluster bootstrap, the per-arm pin file) and the
HTCondor job package ``r1/scripts/htcondor/trackp_p4/`` (spec, job, seal, assemble, JDL render, two-key switch, launch
binding). Synthetic only: no GPU, no image, no label file of a real audit, no network. AI-assisted (Claude).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from r1.c3.train import p4_phase1 as P
from r1.c3.train import sft as SFT
from r1.c3.train import sft_data as SD
from r1.c3.train import tiny
from r1.tests.test_trackp_sft import _after_test_release, _control_plane_skip, _prompts, sweep  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "r1" / "scripts" / "htcondor" / "trackp_p4"
sys.path.insert(0, str(PKG))
import p4_lib as L  # noqa: E402
import p4_render_jdl as RJ  # noqa: E402
import p4_switch as SW  # noqa: E402

PINNED = (ROOT / L.ENV3_FREEZE).read_text()
SPEC_PATH = PKG / "p4_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())
DIGEST = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:" + "2" * 64


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ============================================================================================ env3 freeze
def _swap(line_from: str, line_to: str | None) -> str:
    lines = [ln for ln in PINNED.splitlines() if ln.strip()]
    assert line_from in lines
    lines = [line_to if ln == line_from else ln for ln in lines]
    return "\n".join(x for x in lines if x is not None) + "\n"


def test_the_pinned_freeze_is_r1_env_pin_and_names_causal_conv1d_1_7_0():
    assert _sha((ROOT / L.ENV3_FREEZE).read_bytes()) == L.ENV3_FREEZE_SHA256
    assert "causal-conv1d==1.7.0" in PINNED.splitlines()


@pytest.mark.parametrize("image_line, status", [
    ("causal-conv1d==1.7.0", "identical"),
    ("causal-conv1d==1.7.0+cu12torch2.6cxx11abiFALSE", "causal_conv1d_only"),          # a prebuilt wheel's label
    ("causal_conv1d==1.7.0", "causal_conv1d_only"),                                    # another spelling, same pin
    ("causal-conv1d @ file:///opt/r1/wheels/causal_conv1d-1.7.0+cu12torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl",
     "causal_conv1d_only"),
    ("causal-conv1d @ https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/"
     "causal_conv1d-1.7.0-cp312-cp312-linux_x86_64.whl", "causal_conv1d_only"),
])
def test_v21_freeze_admits_only_the_causal_conv1d_line_at_the_same_version(image_line, status):
    got = P.check_env3_freeze(_swap("causal-conv1d==1.7.0", image_line), PINNED)
    assert got["status"] == status and got["rule"] == "R1-TRACKP-V21-FREEZE"
    if status != "identical":
        assert got["pinned_line"] == "causal-conv1d==1.7.0" and got["image_line"] == image_line
        assert got["version"] == "1.7.0" and "disclosed" in got["disclosure"]


@pytest.mark.parametrize("got, match", [
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.1"), "not the pinned version"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0.post1"), "not the pinned version"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d @ file:///w/causal_conv1d-1.6.0-cp312-cp312-linux_x86_64.whl"),
     "not the pinned version"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d @ file:///w/some_build"), "cannot read"),
    (_swap("causal-conv1d==1.7.0", None), "one line for one line"),                       # the line removed
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0") + "causal-conv1d==1.7.0+x\n", "one line for one line"),
    (_swap("torch==2.6.0+cu124", "torch==2.6.1+cu124"), "outside the causal_conv1d line"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0+cu12") + "einops==9.9\n", "outside the causal_conv1d line"),
    (PINNED + "causal-conv1d==1.7.0\n", "duplicate line"),
])
def test_v21_freeze_stops_on_any_other_difference(got, match):
    with pytest.raises(P.P4Stop, match=match):
        P.check_env3_freeze(got, PINNED)


# ============================================================================================ labels
def _partition(tmp_path, *, block=P.SOURCE_BLOCK_SHA256, source="sweep1", stage="traindev"):
    d = tmp_path / "release" / "sweep1" / "traindev"
    d.mkdir(parents=True)
    (d / P.PARTITION_NAME).write_text('{"proposal_id": "x"}\n')
    psha = _sha((d / P.PARTITION_NAME).read_bytes())
    (d / P.RECEIPT_NAME).write_text(json.dumps({"source": source, "stage": stage, "release_commit": "c" * 40,
                                                "inputs": {"label_block_sha256": block,
                                                           "proposals_sha256": _sha(b"P\n")},
                                                "outputs": {P.PARTITION_NAME: psha}, "counts": {"released_label_rows": 1}}))
    return d, psha, _sha((d / P.RECEIPT_NAME).read_bytes())


def test_partition_is_bound_to_the_note_and_the_frozen_block(tmp_path):
    d, psha, rsha = _partition(tmp_path)
    got = P.check_partition(d, partition_sha256=psha, receipt_sha256=rsha)
    assert got["source_block_sha256"] == P.SOURCE_BLOCK_SHA256 and got["release_commit"] == "c" * 40
    with pytest.raises(P.P4Stop, match="note's labels"):
        P.check_partition(d, partition_sha256="0" * 64, receipt_sha256=rsha)
    with pytest.raises(P.P4Stop, match="label_receipt"):
        P.check_partition(d, partition_sha256=psha, receipt_sha256="0" * 64)
    for kw, match in (({"block": "0" * 64}, "frozen sweep-1 block"), ({"source": "sweep2"}, "sweep-1 train/dev"),
                      ({"stage": "test"}, "sweep-1 train/dev")):
        sub = tmp_path / str(len(kw)) / kw.get("source", kw.get("stage", "b"))
        d2, p2, r2 = _partition(sub, **kw)
        with pytest.raises(P.P4Stop, match=match):
            P.check_partition(d2, partition_sha256=p2, receipt_sha256=r2)
    (d / P.PARTITION_NAME).rename(d / "moved")
    (d / P.PARTITION_NAME).symlink_to(d / "moved")
    with pytest.raises(P.P4Stop, match="missing"):
        P.check_partition(d, partition_sha256=psha, receipt_sha256=rsha)


# ============================================================================================ data, LC, bootstrap
@pytest.fixture
def data_dir(sweep, tmp_path):
    out = tmp_path / "data"
    SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"], shift_z=1.5), _prompts(sweep), out)
    return out


def test_lc_points_are_below_the_training_set_plus_full():
    assert P.lc_points(590) == [250, 500, "full"] and P.lc_points(400) == [250, "full"]
    assert P.lc_points(250) == ["full"] and P.lc_points(251) == [250, "full"]
    with pytest.raises(P.P4Stop):
        P.lc_points(0)


def test_lc_subset_is_a_loadable_derived_data_directory(data_dir, tmp_path):
    train, val, val_seen, man = SD.load_sft_data(data_dir, secondary=True)
    n = len(train) // 2
    m = P.lc_subset(data_dir, n, tmp_path / "lc")
    t2, v2, vs2, man2 = SD.load_sft_data(tmp_path / "lc", secondary=True)
    assert len(t2) == n and [r["proposal_id"] for r in v2] == [r["proposal_id"] for r in val]
    assert len(vs2) == len(val_seen) and {r["proposal_id"] for r in t2} <= {r["proposal_id"] for r in train}
    assert m["lc_subset"]["seed"] == P.LC_SEED + n and m["counts"]["train"] == n
    assert m["lc_subset"]["parent_sft_data_sha256"] == P._sha_file(data_dir / "sft_data.json")
    again = P.lc_subset(data_dir, n, tmp_path / "lc_again")                       # the fixed seed: the same draw
    assert again["lc_subset"]["train_ids_sha256"] == m["lc_subset"]["train_ids_sha256"]
    other = P.lc_subset(data_dir, n, tmp_path / "lc_other", seed=7)
    assert other["lc_subset"]["train_ids_sha256"] != m["lc_subset"]["train_ids_sha256"]
    for args, match in (((data_dir, len(train), tmp_path / "x1"), "below the training-set size"),
                        ((data_dir, n, tmp_path / "lc"), "exists"),
                        ((tmp_path / "lc", 1, tmp_path / "x2"), "full data directory only")):
        with pytest.raises(P.P4Stop, match=match):
            P.lc_subset(*args)
    (data_dir / "rows.jsonl").write_text((data_dir / "rows.jsonl").read_text() + "\n")
    with pytest.raises(P.P4Stop, match="differs from its sft_data.json"):
        P.lc_subset(data_dir, n, tmp_path / "x3")


def _stage_s_runs(data_dir, tmp_path, seeds=(0, 1, 2), lr=1e-4):
    train, val, val_seen, man = SD.load_sft_data(data_dir, secondary=True)
    from r1.c3.train.model import new_head_parameters
    runs = []
    for s in seeds:
        model = tiny.build_hashbag(seed=s)
        run = tmp_path / "runs" / L.run_name(lr, s)
        SFT.run_stage_s(model, train, val, run / "stage_s", {**SFT.DEFAULT_PROTOCOL, "micro_batch": 8}, lr=lr, seed=s,
                        head_params=new_head_parameters(model), max_steps=6, eval_every_steps=3, log=lambda x: None,
                        data_sha256=P._sha_file(data_dir / "sft_data.json"), label_status=man["label_status"],
                        val_secondary=val_seen, duplicate_policy=man["cross_split_duplicates"])
        runs.append(run)
    return runs


def test_bootstrap_is_instance_clustered_on_primary_val(data_dir, tmp_path):
    runs = _stage_s_runs(data_dir, tmp_path)
    boot = P.rps_skill_bootstrap(data_dir, [r / "stage_s" for r in runs], resamples=200)
    rows = [json.loads(x) for x in (data_dir / "rows.jsonl").read_text().splitlines()]
    assert boot["n_val_rows"] == sum(r["split"] == "val" for r in rows)
    assert boot["n_val_instances"] == len({r["instance"] for r in rows if r["split"] == "val"})
    for kind in ("raw", "temperature_scaled"):
        lo, hi = boot[kind]["ci95"]
        assert lo <= boot[kind]["rps_skill_seed_mean"] <= hi or np.isclose(lo, hi)
    reports = [json.loads((r / "stage_s" / "sft_report.json").read_text()) for r in runs]
    assert np.isclose(boot["raw"]["rps_skill_seed_mean"],
                      np.mean([rep["selected"]["val_rps_skill"] for rep in reports]))
    assert boot == P.rps_skill_bootstrap(data_dir, [r / "stage_s" for r in runs], resamples=200)   # seeded
    other = tmp_path / "other_data"
    P.lc_subset(data_dir, 5, other)
    with pytest.raises(P.P4Stop, match="another data directory"):
        P.rps_skill_bootstrap(other, [runs[0] / "stage_s"])


def _pin(data_dir, runs):
    return P.arm_pin(arm="kev-0.8b", base_record={"base_revision": "r"}, staged={"kev-0.8b/a": "1" * 64},
                     data_dir=data_dir, select_report={"selected_lr": 1e-4, "mean_best_val_rps": {}}, grid_runs=runs,
                     lc_runs={"full": runs}, micro_batch=8, host_config_sha256="h" * 64)


def test_arm_pin_records_every_run(data_dir, tmp_path):
    runs = _stage_s_runs(data_dir, tmp_path, seeds=(0,))
    pin = _pin(data_dir, runs)
    assert pin["schema"] == P.PIN_SCHEMA and pin["selected_lr"] == 1e-4 and pin["micro_batch"] == 8
    g = pin["grid"][0]
    assert g["best_json_sha256"] and g["best_tree_sha256"] and g["temperature_sha256"] and g["sft_report_sha256"]
    assert g["best_manifest"]["name"] == "record.json"                  # the CPU stand-in's checkpoint record
    assert pin["learning_curve"]["full"][0]["run_dir"] == runs[0].name


def test_arm_pin_binds_a_real_wrapper_checkpoint_and_stops_without_one(data_dir, tmp_path):
    """Review round 1, M1: the real wrappers write best/manifest.json (model.py), the trainer stage_s/best.json."""
    runs = _stage_s_runs(data_dir, tmp_path, seeds=(0,))
    best = runs[0] / "stage_s" / "best"
    (best / "record.json").rename(best / "manifest.json")
    (best / "adapter").mkdir()
    (best / "adapter" / "adapter_model.safetensors").write_bytes(b"weights")
    g = _pin(data_dir, runs)["grid"][0]
    assert g["best_manifest"]["name"] == "manifest.json" and g["best_manifest"]["sha256"] == P._sha_file(
        best / "manifest.json")
    tree_before = g["best_tree_sha256"]
    (best / "adapter" / "adapter_model.safetensors").write_bytes(b"other weights")
    assert _pin(data_dir, runs)["grid"][0]["best_tree_sha256"] != tree_before        # the weights are in the pin
    for remove, match in ((runs[0] / "stage_s" / "best.json", "best.json"), (best / "manifest.json", "manifest"),
                          (best / "temperature.json", "temperature")):
        moved = remove.with_name(remove.name + ".x")
        remove.rename(moved)
        with pytest.raises(P.P4Stop, match=match):
            _pin(data_dir, runs)
        moved.rename(remove)


# ============================================================================================ spec
def filled() -> dict:
    s = copy.deepcopy(SPEC)
    s["paper"]["commit"] = "3" * 40
    s["image"].update(digest=DIGEST, versions_sha256="4" * 64)
    s["host_config"]["sha256"] = "5" * 64
    s["labels"].update(partition_sha256="6" * 64, receipt_sha256="7" * 64,
                       freeze_record={"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md",
                                      "sha256": "8" * 64})
    s["estimate"]["source"] = "h200_sft_probe: docs/r1/reports/x.md"
    return s


def test_shipped_spec_validates_and_refuses_launch_until_filled():
    loaded = L.validate_spec(copy.deepcopy(SPEC))
    p = loaded["projection"]
    assert p["within_cap"] and p["total_gpu_hours"] == round(2 * (0.83 + 0.5) + 2 * (6.64 + 0.5), 3)
    assert p["per_arm"]["kev-4b"]["walltime_s"] == int(np.ceil(6.64 * 3600 * 1.5 + 1800))
    with pytest.raises(L.Stop, match="paper.commit"):
        L.validate_spec(copy.deepcopy(SPEC), launch=True)
    assert L.validate_spec(filled(), launch=True)["run_id"] == SPEC["run_id"]
    for path, value, match in ((("estimate", "source"), "assumed", "h200_sft_probe"),
                               (("estimate", "source"), "h200_sft_probe:", "h200_sft_probe"),
                               (("image", "digest"), "TODO", "image.digest"),
                               (("labels", "receipt_sha256"), "TODO", "labels.receipt_sha256"),
                               (("host_config", "sha256"), "TODO", "host_config.sha256")):
        s = filled()
        s[path[0]][path[1]] = value
        with pytest.raises(L.Stop, match=match):
            L.validate_spec(s, launch=True)


def _set(*path_value):
    *path, value = path_value

    def edit(s):
        t = s
        for k in path[:-1]:
            t = t[k]
        t[path[-1]] = value
    return edit


@pytest.mark.parametrize("edit, match", [
    (_set("image", "digest", L.IMAGE_V2), "image v2 and v2.1 are not the P.4 image"),
    (_set("image", "digest", L.IMAGE_V21), "image v2 and v2.1 are not the P.4 image"),
    (_set("image", "row", "R1-QTORCH-AMEND"), "image.row"),
    (_set("image", "row", "R1-TRACKP-IMAGE-V21"), "image.row must be R1-TRACKP-IMAGE-V22-B"),
    (_set("gpu_model", "NVIDIA RTX 4090"), "gpu_model"),
    (_set("env3", "freeze_sha256", "0" * 64), "env3 must be"),
    (_set("env3", "rule", "R1-HTC-QTORCH"), "env3 must be"),
    (_set("sft_config", "sha256", "TODO"), "sft_config.sha256"),
    (_set("split_file", "sha256", "0" * 64), "signed P3 split file"),
    (_set("table", "pin", "sweep2_v3"), "table must be"),
    (_set("labels", "source", "sweep2"), "receipted sweep-1"),
    (_set("labels", "source_block_sha256", "0" * 64), "frozen block"),
    (_set("labels", "freeze_record", {"path": "docs/r1/x.md", "sha256": "8" * 64}), "LABEL_FREEZE"),
    (_set("arms", ["kev-0.8b", "kev-4b"]), "controls"),
    (_set("arms", ["kev-0.8b", "laya", "qwen3.5-0.8b-base", "qwen3.5-4b-base"]), "distinct members"),
    (_set("first_arm", "laya"), "first_arm"),
    (_set("protocol", "micro_batch", 16), "micro_batch"),
    (_set("protocol", "lr_grid", [1e-5, 3e-5]), "lr_grid"),
    (_set("protocol", "lc_points", [250, 500, 1000]), "lc_points"),
    (_set("protocol", "real_label_test_read", "phase1"), "real_label_test_read"),
    (_set("caps", "gpu_hours", 60.0), "caps"),
    (_set("estimate", "hours", {"kev-0.8b": 0.83}), "every arm"),
    (_set("estimate", "hours", {"kev-0.8b": 18.0, "kev-4b": 18.0, "qwen3.5-0.8b-base": 0.8,
                                "qwen3.5-4b-base": 6.6}), "over 86400 s|exceeds P4-CAP"),
    (_set("estimate", "hours", {"kev-0.8b": 10.0, "kev-4b": 10.0, "qwen3.5-0.8b-base": 10.0,
                                "qwen3.5-4b-base": 10.0}), "exceeds P4-CAP"),
    (_set("layout", "wall_factor", 1.0), "wall_factor"),
])
def test_spec_refusals(edit, match):
    s = filled()
    edit(s)
    with pytest.raises(L.Stop, match=match):
        L.validate_spec(s, launch=True)


# ============================================================================================ host steps
def _res(rc=0, out="", err=""):
    return subprocess.CompletedProcess([], rc, out, err)


def test_gpu_identity_and_root():
    assert L.gpu_identity(lambda a, **k: _res(0, "NVIDIA H200, GPU-1, 570, 143771 MiB, 9.0\n"))["name"] == L.GPU_MODEL
    for out, match in (("NVIDIA H200, a, b, c, 9.0\nNVIDIA H200, a, b, c, 9.0\n", "one GPU"),
                       ("NVIDIA L40S, a, b, c, 8.9\n", "not NVIDIA H200")):
        with pytest.raises(L.Stop, match=match):
            L.gpu_identity(lambda a, **k: _res(0, out))


def test_image_identity_binds_versions(tmp_path, monkeypatch):
    v = tmp_path / "VERSIONS.txt"
    v.write_text("v2.2\n")
    s = filled()
    s["image"]["versions_sha256"] = _sha(b"v2.2\n")
    monkeypatch.setattr(L, "ENV3_PYTHON", sys.executable)
    monkeypatch.setattr(L, "UV", str(tmp_path / "no-uv"))
    with pytest.raises(L.Stop, match="no-uv missing"):
        L.image_identity(s, v)
    monkeypatch.setattr(L, "UV", sys.executable)
    assert L.image_identity(s, v)["versions_sha256"] == _sha(b"v2.2\n")
    s["image"]["versions_sha256"] = "0" * 64
    with pytest.raises(L.Stop, match="differs from the image v2.2 pin"):
        L.image_identity(s, v)


def test_env3_freeze_step_records_the_v21_difference(monkeypatch):
    image = _swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0+cu12torch2.6cxx11abiFALSE")
    seen = []
    got = L.env3_freeze(filled(), ROOT, lambda a, **k: seen.append(a) or _res(0, image))
    assert seen == [[L.UV, "pip", "freeze", "--python", L.ENV3_PYTHON]]       # env3 is a uv venv without pip (B2)
    assert L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, PINNED))["status"] == "identical"
    assert got["status"] == "causal_conv1d_only" and got["pinned_sha256"] == L.ENV3_FREEZE_SHA256
    with pytest.raises(L.Stop, match="outside the causal_conv1d line"):
        L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, _swap("torch==2.6.0+cu124", "torch==2.7.0")))
    with pytest.raises(L.Stop, match="pip freeze of env3 failed"):
        L.env3_freeze(filled(), ROOT, lambda a, **k: _res(1, "", "boom"))


def test_env3_freeze_step_passes_image_v22s_recorded_freeze():
    """Image v2.2 (V22_BUILD_20261124.md): causal-conv1d 1.7.0 built from source and installed by name, so the freeze
    line stays ``causal-conv1d==1.7.0`` and the sorted freeze diff is empty. The current rule records that as
    ``identical`` (in any line order); it does not need the R1-TRACKP-V21-FREEZE allowance. The reading of
    R1-TRACKP-P4-RUNNER-DECISIONS (1) is pending and not implemented here."""
    v22 = "\n".join(reversed([ln for ln in PINNED.splitlines() if ln.strip()])) + "\n"     # uv's own order
    assert "causal-conv1d==1.7.0" in v22.splitlines()
    got = L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, v22))
    assert got["status"] == "identical" and got["rule"] == "R1-TRACKP-V21-FREEZE"
    assert got["sha256_sorted"] == _sha("\n".join(sorted(x.strip() for x in PINNED.splitlines() if x.strip())).encode())


def test_clone_must_be_full_published_and_clean(tmp_path):
    state = {"shallow": "false", "ancestor": 0, "dirty": ""}

    def git(repo, *args, **kw):
        if args[0] == "rev-parse" and args[1] == "HEAD":
            return _res(0, "3" * 40)
        if args[:2] == ("rev-parse", "--is-shallow-repository"):
            return _res(0, state["shallow"])
        if args[0] == "merge-base":
            return _res(state["ancestor"])
        if args[0] == "status":
            return _res(0, state["dirty"])
        if args[:2] == ("rev-parse", "origin/main"):
            return _res(0, "9" * 40)
        return _res(0)
    sh = lambda a, **k: _res(0)  # noqa: E731
    assert L.clone_full("3" * 40, tmp_path / "c", git, sh)["origin_main"] == "9" * 40
    for key, value, match in (("shallow", "true", "shallow"), ("ancestor", 1, "not on published main"),
                              ("dirty", " M x", "not clean")):
        state.update({"shallow": "false", "ancestor": 0, "dirty": ""}, **{key: value})
        with pytest.raises(L.Stop, match=match):
            L.clone_full("3" * 40, tmp_path / "c", git, sh)


def test_configs_bind_both_shas_and_a_clean_check_config(tmp_path):
    clone = tmp_path / "clone"
    for rel in (L.HOST_CONFIG, L.SFT_CONFIG):
        (clone / rel).parent.mkdir(parents=True, exist_ok=True)
        (clone / rel).write_text(rel)
    s = filled()
    s["host_config"]["sha256"], s["sft_config"]["sha256"] = _sha(L.HOST_CONFIG.encode()), _sha(L.SFT_CONFIG.encode())
    ok = lambda a, **k: _res(0, json.dumps({"placeholders": [], "sha256": "x"}))  # noqa: E731
    assert L.configs(s, clone, ok)["check_config"]["placeholders"] == []
    with pytest.raises(L.Stop, match="not clean"):
        L.configs(s, clone, lambda a, **k: _res(1, json.dumps({"placeholders": ["gpu.name"]})))
    s["host_config"]["sha256"] = "0" * 64
    with pytest.raises(L.Stop, match="is not the spec's"):
        L.configs(s, clone, ok)


def _fake_clone(tmp_path, *, freeze_text="signed freeze\n"):
    """A clone stand-in: this repository's code (so p4_phase1 imports), plus a freeze record and an SFT config whose
    table pins match the synthetic table files."""
    clone = tmp_path / "paper"
    clone.mkdir()
    (clone / "r1").symlink_to(ROOT / "r1")
    sft = json.loads((ROOT / L.SFT_CONFIG).read_text())
    sft["tables"][L.TABLE_PIN]["sha256"] = {"proposals.jsonl": _sha(b"P\n"), "configs.json": _sha(b"C\n")}
    return clone, sft, freeze_text


def test_inputs_lay_out_and_check_the_transferred_files(tmp_path, monkeypatch):
    job = tmp_path / "job"
    job.mkdir()
    d, psha, rsha = _partition(tmp_path / "src")
    for name, text in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
        (job / name).write_bytes(text)
    for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
        (job / name).write_bytes((d / name).read_bytes())
    clone = tmp_path / "clone"
    (clone / "r1/scripts/configs").mkdir(parents=True)
    sft = json.loads((ROOT / L.SFT_CONFIG).read_text())
    sft["tables"][L.TABLE_PIN]["sha256"] = {"proposals.jsonl": _sha(b"P\n"), "configs.json": _sha(b"C\n")}
    (clone / L.SFT_CONFIG).write_text(json.dumps(sft))
    fr = clone / "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md"
    fr.parent.mkdir(parents=True)
    ftext = f"approved: true\nblock: {P.SOURCE_BLOCK_SHA256}\n".encode()
    fr.write_bytes(ftext)
    monkeypatch.setattr(L, "_phase1", lambda c: P)
    s = filled()
    s["labels"].update(partition_sha256=psha, receipt_sha256=rsha,
                       freeze_record={"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md",
                                      "sha256": _sha(ftext)})
    got = L.inputs(s, clone, job)
    assert Path(got["partition_dir"]).name == "traindev" and got["table_sha256"]["build.json"] == _sha(b"B\n")
    assert got["receipt_proposals_sha256"] == _sha(b"P\n")
    # review round 1, minor 2: a freeze record that is not signed, or not of the frozen block, is refused
    for text, n in ((b"approved: false\nblock: " + P.SOURCE_BLOCK_SHA256.encode() + b"\n", "u"),
                    (b"approved: true\nblock: other\n", "b")):
        fr.write_bytes(text)
        jd = tmp_path / f"job_{n}"
        jd.mkdir()
        for name, t in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
            (jd / name).write_bytes(t)
        for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
            (jd / name).write_bytes((d / name).read_bytes())
        s_n = copy.deepcopy(s)
        s_n["labels"]["freeze_record"]["sha256"] = _sha(text)
        with pytest.raises(L.ProtocolStop, match="not a signed freeze"):
            L.inputs(s_n, clone, jd)
    fr.write_bytes(ftext)
    # minor 4: a receipt of another table is refused
    d_o, psha_o, rsha_o = _partition(tmp_path / "other_table")
    rec = json.loads((d_o / P.RECEIPT_NAME).read_text())
    rec["inputs"]["proposals_sha256"] = "0" * 64
    (d_o / P.RECEIPT_NAME).write_text(json.dumps(rec))
    jo = tmp_path / "job_o"
    jo.mkdir()
    for name, t in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
        (jo / name).write_bytes(t)
    for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
        (jo / name).write_bytes((d_o / name).read_bytes())
    s_o = copy.deepcopy(s)
    s_o["labels"].update(partition_sha256=psha_o, receipt_sha256=_sha((d_o / P.RECEIPT_NAME).read_bytes()))
    with pytest.raises(L.ProtocolStop, match="labels are of another table"):
        L.inputs(s_o, clone, jo)
    job2 = tmp_path / "job2"
    job2.mkdir()
    for name in ("proposals.jsonl", "configs.json", "build.json", P.PARTITION_NAME, P.RECEIPT_NAME):
        (job2 / name).write_bytes((Path(got["table_dir"]) / name).read_bytes() if name.endswith(("jsonl", "json"))
                                  and (Path(got["table_dir"]) / name).exists() else
                                  (Path(got["partition_dir"]) / name).read_bytes())
    s2 = copy.deepcopy(s)
    s2["labels"]["freeze_record"]["sha256"] = "0" * 64
    with pytest.raises(L.ProtocolStop, match="signed label freeze"):
        L.inputs(s2, clone, job2)
    job3 = tmp_path / "job3"
    job3.mkdir()
    for name, text in (("proposals.jsonl", b"other\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
        (job3 / name).write_bytes(text)
    with pytest.raises(L.Stop, match="is not the sweep1_v3 pin"):
        L.inputs(s, clone, job3)


def test_staging_checks_every_file_and_the_local_paths(tmp_path):
    clone = tmp_path / "clone"
    (clone / "r1/c3/train").mkdir(parents=True)
    (clone / "r1/scripts/configs").mkdir(parents=True)
    files = {"kev-0.8b": {"adapter.safetensors": b"A" * 10}, "qwen3.5-0.8b-base": {"model.safetensors": b"M" * 7}}
    reg = {"models": {k: {"repo": f"org/{k}", "revision": "r" * 40,
                          "files": {n: {"sha256": _sha(b), "size": len(b)} for n, b in v.items()}}
                      for k, v in files.items()}}
    import yaml
    (clone / "r1/c3/train/registry.yaml").write_text(yaml.safe_dump(reg))
    job = tmp_path / "job"
    job.mkdir()
    payload = {f"https://huggingface.co/org/{k}/resolve/{'r' * 40}/{n}": b for k, v in files.items() for n, b in v.items()}

    def sh(argv, **kw):
        if argv[0] == "curl":
            Path(argv[argv.index("-o") + 1]).write_bytes(payload[argv[-1]])
            return _res(0)
        assert kw["env"]["HF_HUB_OFFLINE"] == "0"
        return _res(0, "6")
    got = L.stage(filled(), "kev-0.8b", clone, job, sh)
    assert set(got["weights"]) == {"kev-0.8b/adapter.safetensors", "qwen3.5-0.8b-base/model.safetensors"}
    cfg = json.loads((ROOT / L.HOST_CONFIG).read_text())
    cfg["bases"]["kev-0.8b"].update(local_path="models/qwen3.5-0.8b-base", adapter_local_path="models/kev-0.8b")
    (clone / L.HOST_CONFIG).write_text(json.dumps(cfg))
    assert L.check_local_paths("kev-0.8b", clone, job)["adapter_local_path"].endswith("models/kev-0.8b")
    cfg["bases"]["kev-0.8b"]["adapter_local_path"] = "models/elsewhere"
    (clone / L.HOST_CONFIG).write_text(json.dumps(cfg))
    with pytest.raises(L.Stop, match="is not the staged"):
        L.check_local_paths("kev-0.8b", clone, job)
    payload[next(iter(payload))] = b"tampered"
    with pytest.raises(L.Stop, match="size or sha256 mismatch"):
        L.stage(filled(), "kev-0.8b", clone, tmp_path / "job_b", sh)


@pytest.mark.parametrize("rc, err, cls", [(1, "torch.OutOfMemoryError: CUDA out of memory", L.ArmStop),
                                          (2, "STOP: sft-dev refused", L.ProtocolStop), (139, "segfault", L.Stop),
                                          (2, "python: can't open file '/j/r1/scripts/trackp.py': [Errno 2]", L.Stop),
                                          (2, "usage: trackp.py\ntrackp.py: error: unrecognized arguments: --x",
                                           L.Stop)])
def test_trackp_failures_are_classified(tmp_path, rc, err, cls):
    with pytest.raises(cls) as e:
        L.trackp(tmp_path, tmp_path, ["sft-dev", "--lr", "1e-4"], lambda a, **k: _res(rc, "", err))
    assert type(e.value) is cls and (tmp_path / "out" / "logs").is_dir()


# ============================================================================================ the job, end to end
@pytest.fixture
def job_world(sweep, tmp_path, monkeypatch):
    """Every host step faked; trackp.py replaced by the real data builder (synthetic labels) and the real Stage S loop
    on the CPU hash-bag stand-in, so the grid, selection, learning curve, bootstrap and pin file run for real."""
    monkeypatch.setattr(L, "LC_POINTS", (5, 500))       # the synthetic table has few training rows
    s = filled()
    s["protocol"]["lc_points"] = [5, 500]
    spec_path = tmp_path / "p4_spec.json"
    spec_path.write_text(json.dumps(s))
    job = tmp_path / "job"
    job.mkdir()
    monkeypatch.setattr(L, "image_identity", lambda spec: {"digest": spec["image"]["digest"], "versions_sha256": "4" * 64})
    monkeypatch.setattr(L, "gpu_identity", lambda sh: {"name": L.GPU_MODEL, "uuid": "GPU-1"})
    monkeypatch.setattr(L, "host_identity", lambda: {"uid": 1000})

    def clone_full(commit, dest, git, sh):
        dest.symlink_to(ROOT)
        return {"commit": commit}
    monkeypatch.setattr(L, "clone_full", clone_full)
    monkeypatch.setattr(L, "env3_freeze", lambda spec, clone, sh: {"status": "identical"})
    monkeypatch.setattr(L, "configs", lambda spec, clone, sh: {"host_config": {"sha256": "5" * 64},
                                                              "sft_config": {"sha256": "s"}})
    monkeypatch.setattr(L, "inputs", lambda spec, clone, job_dir: {
        "table_dir": "t", "partition_dir": str(job_dir / "release/sweep1/traindev"),
        "labels": {"partition": str(job_dir / "release/sweep1/traindev/label_block.traindev.jsonl"),
                   "partition_sha256": "6" * 64},
        "label_freeze": {"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md", "sha256": "8" * 64}})
    monkeypatch.setattr(L, "stage", lambda spec, arm, clone, job_dir, sh: {"weights": {"kev-0.8b/a": "1" * 64}})
    monkeypatch.setattr(L, "check_local_paths", lambda arm, clone, job_dir: {})
    monkeypatch.setattr(L, "test_path", lambda clone, job_dir, arm, ins, sh: {"labels": "synthetic"})
    calls = []
    state = {"oom_at": None}

    def trackp(clone, job_dir, args, sh=None, timeout=0):
        calls.append(args)
        a = {args[k]: args[k + 1] for k in range(1, len(args) - 1) if str(args[k]).startswith("--")}
        if args[0] == "sft-data":
            out = Path(a["--run-dir"]) / "data"
            SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"], shift_z=1.5), _prompts(sweep), out,
                              table_record={"path": str(job_dir / "table"), "sha256": {"proposals.jsonl": "p"}},
                              prompt_record={"sweep_index": {"path": str(clone / "idx.json"), "sha256": "i"}})
        elif args[0] == "sft-dev":
            if state["oom_at"] and len([c for c in calls if c[0] == "sft-dev"]) == state["oom_at"]:
                raise L.ArmStop("STOP: CUDA OOM in sft-dev at micro-batch 8")
            data = Path(a["--data"])
            train, val, vs, man = SD.load_sft_data(data, secondary=True)
            from r1.c3.train.model import new_head_parameters
            model = tiny.build_hashbag(seed=int(a["--seed"]))
            SFT.run_stage_s(model, train, val, Path(a["--run-dir"]) / "stage_s",
                            {**SFT.DEFAULT_PROTOCOL, "micro_batch": 8}, lr=float(a["--lr"]), seed=int(a["--seed"]),
                            head_params=new_head_parameters(model), log=lambda x: None,
                            data_sha256=P._sha_file(data / "sft_data.json"), label_status=man["label_status"],
                            val_secondary=vs, duplicate_policy=man["cross_split_duplicates"])
        elif args[0] == "sft-select":
            runs = args[args.index("--runs") + 1: args.index("--run-dir")]
            rep = SFT.select_lr([Path(r) / "stage_s" for r in runs])
            Path(a["--run-dir"]).mkdir(parents=True)
            (Path(a["--run-dir"]) / "report.json").write_text(json.dumps(rep))
        return {"argv": list(map(str, args))}
    monkeypatch.setattr(L, "trackp", trackp)
    return s, spec_path, job, calls, state


def test_job_runs_grid_select_learning_curve_bootstrap_pin_and_seals(job_world, tmp_path):
    s, spec_path, job, calls, state = job_world
    rec = L.run_job(spec_path, "kev-0.8b", job)
    assert rec["stop"] is None and rec["steps"][-1] == "test_path"
    devs = [c for c in calls if c[0] == "sft-dev"]
    grid = [c for c in devs if "lc_data" not in " ".join(map(str, c))]
    assert len(grid) == 9 and {float(c[c.index("--lr") + 1]) for c in grid} == set(L.LR_GRID)
    lc = [c for c in devs if "lc_data" in " ".join(map(str, c))]
    assert len(lc) == 3 and {float(c[c.index("--lr") + 1]) for c in lc} == {rec["select"]["selected_lr"]}
    assert rec["learning_curve"]["5"] and len(rec["learning_curve"]["full"]) == 3 and "500" not in rec["learning_curve"]
    assert -1 <= rec["bootstrap"]["raw"]["rps_skill_seed_mean"] <= 1
    pin = json.loads((job / "out" / "arm_pin.json").read_text())
    assert pin["selected_lr"] == rec["select"]["selected_lr"] and len(pin["grid"]) == 9
    assert rec["arm_pin_sha256"] == P._sha_file(job / "out" / "arm_pin.json")
    assert subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=job, capture_output=True).returncode == 0
    sealed = tmp_path / "sealed"
    receipt = L.seal(job, s, "kev-0.8b", sealed)
    assert receipt["attempt"] == 1 and Path(receipt["sealed_path"]).name == "attempt-1"
    assert L.seal(job, s, "kev-0.8b", sealed)["attempt"] == 2              # a repeat is a new attempt, never a resume
    with pytest.raises(L.Stop, match="does not match the run/arm"):
        L.seal(job, s, "kev-4b", sealed)


def test_job_records_an_arm_stop_and_still_writes_the_sums(job_world):
    s, spec_path, job, calls, state = job_world
    state["oom_at"] = 4
    with pytest.raises(L.Stop, match="CUDA OOM"):
        L.run_job(spec_path, "kev-0.8b", job)
    rec = json.loads((job / "job_record.json").read_text())
    assert rec["stop_class"] == "arm" and rec["steps"][-1] == "data"
    assert subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=job, capture_output=True).returncode == 0


def _sealed_attempt(sealed_root: Path, s: dict, arm: str, spec_sha: str, n: int = 1, receipt_over=None,
                    **over) -> Path:
    d = sealed_root / s["run_id"] / arm / f"attempt-{n}"
    d.mkdir(parents=True)
    rec = {"label": "ENGINEERING_ONLY", "run_id": s["run_id"], "arm": arm, "spec_sha256": spec_sha, "stop": None,
           "paper_commit": "3" * 40, "image": {"digest": DIGEST}, "configs": {"host_config": 1, "sft_config": 2},
           "data": {"sft_data_sha256": "d" * 64, "identity": {"sha256": "i" * 64}},
           "inputs": {"labels": {"partition": f"/var/lib/condor/execute/dir_{arm}/p", "x": 1}},
           "env3_freeze": {"status": "identical"}, "select": {"selected_lr": 3e-5}, "gpu_hours": 2.0,
           "protocol": {"micro_batch": 8}, **over}
    (d / "job_record.json").write_text(json.dumps(rec))
    receipt = {"job_record_sha256": P._sha_file(d / "job_record.json"), "identity_verified": True,
               "stop": rec["stop"], "charged_gpu_hours": rec["gpu_hours"], **(receipt_over or {})}
    (d / "SEAL_RECEIPT.json").write_text(json.dumps(receipt))
    (d / "SHA256SUMS").write_text(f"{P._sha_file(d / 'job_record.json')}  job_record.json\n")
    return d


def test_assemble_needs_every_arm_one_table_and_the_cap(tmp_path):
    s = filled()
    root = tmp_path / "a"
    dirs = [_sealed_attempt(root, s, arm, "f" * 64) for arm in s["arms"]]
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["gpu_hours_consumed"] == 8.0 and asm["data_identity"] == {"sha256": "i" * 64}
    with pytest.raises(L.Stop, match="needs every arm"):
        L.assemble(dirs[:3], s, "f" * 64, root)
    root_b = tmp_path / "b"
    dirs_b = [_sealed_attempt(root_b, s, arm, "f" * 64, **({"data": {"identity": {"sha256": "e" * 64}}}
                                                           if arm == "kev-4b" else {})) for arm in s["arms"]]
    with pytest.raises(L.Stop, match=r"differ in \['data'\]"):
        L.assemble(dirs_b, s, "f" * 64, root_b)
    big_root = tmp_path / "c"
    big = [_sealed_attempt(big_root, s, arm, "f" * 64, gpu_hours=11.0) for arm in s["arms"]]
    with pytest.raises(L.Stop, match="exceeds P4-CAP"):
        L.assemble(big, s, "f" * 64, big_root)
    # round 2, minor 2: the given attempts must lie in the sealed tree the cap counts
    with pytest.raises(L.Stop, match="not a sealed attempt under"):
        L.assemble(dirs, s, "f" * 64, tmp_path / "wrong_root")
    stopped = _sealed_attempt(root, s, "kev-0.8b", "f" * 64, n=2, stop="STOP: x")
    with pytest.raises(L.Stop, match="STOP-free"):
        L.assemble([stopped, *dirs[1:]], s, "f" * 64, root)
    unverified = _sealed_attempt(root, s, "kev-0.8b", "f" * 64, n=3, receipt_over={"identity_verified": False})
    with pytest.raises(L.Stop, match="verified"):
        L.assemble([unverified, *dirs[1:]], s, "f" * 64, root)


def test_repeats_are_kept_counted_and_never_chosen(tmp_path):
    """Review round 1, M2: every attempt is sealed and charged to the cap; no second STOP-free attempt of an arm."""
    s = filled()
    root = tmp_path / "sealed"
    dirs = [_sealed_attempt(root, s, arm, "f" * 64, n=2) for arm in s["arms"]]
    _sealed_attempt(root, s, "kev-4b", "f" * 64, n=1, stop="STOP: late", gpu_hours=7.0)
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["gpu_hours_consumed"] == 15.0 and len(asm["gpu_hours_by_attempt"]) == 5
    _sealed_attempt(root, s, "kev-4b", "f" * 64, n=3, gpu_hours=2.0)
    with pytest.raises(L.Stop, match="another STOP-free attempt"):
        L.assemble(dirs, s, "f" * 64, root)
    # a killed job: exactly the files p4_job.sh pre-creates (all empty) are still sealed, charged at the walltime
    job = tmp_path / "killed"
    job.mkdir()
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "p4_run.log"):
        (job / name).write_text("")
    r = L.seal(job, s, "kev-0.8b", tmp_path / "s2")
    assert r["record_readable"] is False and r["sums"] == "absent" and r["identity_verified"] is False
    assert r["charged_gpu_hours"] == round(L.arm_walltime_s(s, "kev-0.8b") / 3600, 4) and r["stop"].startswith("STOP")
    # a STOP at identity (no H200 / image in the record) is sealed, unverified, at its own hours
    job2 = tmp_path / "noid"
    job2.mkdir()
    (job2 / "job_record.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "run_id": s["run_id"],
                                                      "arm": "kev-0.8b", "stop": "STOP: landed on L40S",
                                                      "stop_class": "infrastructure", "gpu_hours": 0.01}))
    r2 = L.seal(job2, s, "kev-0.8b", tmp_path / "s2")
    assert r2["attempt"] == 2 and r2["identity_verified"] is False and r2["charged_gpu_hours"] == 0.01
    assert L.charged_hours(s, tmp_path / "s2")["total"] == round(r["charged_gpu_hours"] + 0.01, 4)
    (tmp_path / "s2" / s["run_id"] / "kev-0.8b" / "attempt-3").mkdir()
    with pytest.raises(L.Stop, match="no SEAL_RECEIPT"):
        L.charged_hours(s, tmp_path / "s2")
    (tmp_path / "s2" / s["run_id"] / "kev-0.8b" / "attempt-3").rmdir()
    with pytest.raises(L.Stop, match="does not match the run/arm"):
        L.seal(job2, s, "kev-4b", tmp_path / "s3")
    job3 = tmp_path / "badsums"
    job3.mkdir()
    (job3 / "job_record.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "run_id": s["run_id"],
                                                      "arm": "kev-0.8b"}))
    (job3 / "SHA256SUMS").write_text("0" * 64 + "  job_record.json\n")
    with pytest.raises(L.Stop, match="SHA256SUMS verification failed"):     # non-empty sums must verify
        L.seal(job3, s, "kev-0.8b", tmp_path / "s4")
    # round 2, minor 3: a submission recorded in the run ledger and not yet sealed counts at its walltime
    ledger = tmp_path / "s2" / s["run_id"] / L.SUBMISSION_LEDGER
    ledger.write_text(json.dumps({"arm": "kev-4b"}) + "\n")
    got = L.charged_hours(s, tmp_path / "s2")
    assert got["pending"][0]["arm"] == "kev-4b" and got["total"] == round(
        r["charged_gpu_hours"] + 0.01 + L.arm_walltime_s(s, "kev-4b") / 3600, 4)


def test_two_job_directories_give_one_comparable_record(job_world, tmp_path):
    """Review round 1, B3: the data and label identities the assembly compares carry no job-local path."""
    s, spec_path, job, calls, state = job_world
    job_b = tmp_path / "var" / "lib" / "condor" / "execute" / "dir_42"
    job_b.mkdir(parents=True)
    rec_a = L.run_job(spec_path, "kev-0.8b", job)
    rec_b = L.run_job(spec_path, "kev-4b", job_b)
    assert rec_a["data"]["sft_data_sha256"] != rec_b["data"]["sft_data_sha256"]      # the manifests hold paths
    assert L.comparable(rec_a) == L.comparable(rec_b)
    assert rec_a["data"]["identity"]["rows_sha256"] == rec_b["data"]["identity"]["rows_sha256"]
    assert rec_a["inputs"]["labels"]["partition"] != rec_b["inputs"]["labels"]["partition"]


def test_trackp_runs_the_clone_script_from_the_job_directory(tmp_path, monkeypatch):
    """Review round 1, B1: the real ``_sh`` from the job directory reaches the clone's trackp.py (a refusal is a
    protocol STOP); a clone without the script is an infrastructure STOP, not a protocol one."""
    monkeypatch.setattr(L, "ENV3_PYTHON", sys.executable)
    job = tmp_path / "job"
    job.mkdir()
    with pytest.raises(L.ProtocolStop) as e:
        L.trackp(ROOT, job, ["sft-select", "--runs", str(tmp_path / "missing"), "--run-dir", str(job / "sel")])
    assert "can't open file" not in str(e.value)
    empty = tmp_path / "empty_clone"
    (empty / "r1/scripts/configs").mkdir(parents=True)
    with pytest.raises(L.Stop) as e2:
        L.trackp(empty, job, ["sft-select", "--runs", "x", "--run-dir", str(job / "sel2")])
    assert type(e2.value) is L.Stop and e2.value.stop_class == "infrastructure"


class _Parsed(Exception):
    pass


def test_the_job_argument_lists_parse_with_the_real_cli(monkeypatch, tmp_path):
    """Review round 1, M3: every trackp.py argument list the job builds is accepted by trackp.py's own parser."""
    import argparse
    from r1.scripts import trackp as TP
    orig = argparse.ArgumentParser.parse_args

    def spy(self, args=None, namespace=None):
        ns = orig(self, args, namespace)
        raise _Parsed(ns)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", spy)
    clone, job = tmp_path / "paper", tmp_path / "job"
    ins = {"table_dir": str(job / "table"), "partition_dir": str(job / "release/sweep1/traindev"),
           "label_freeze": {"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md"}}
    lists = [L.data_argv(clone, job, ins), L.data_argv(clone, job, ins, synthetic=True),
             L.sft_dev_argv("kev-0.8b", job / "d", 3e-5, 1, job / "r"),
             L.sft_dev_argv("kev-0.8b", job / "d", L.LR_GRID[0], 0, job / "t", extra=("--steps", "2", "--eval-every", "1")),
             L.select_argv([job / "a", job / "b"], job / "sel")]
    for argv in lists:
        with pytest.raises(_Parsed) as e:
            TP.main(["--config", str(ROOT / L.HOST_CONFIG), *argv])
        ns = e.value.args[0]
        assert ns.cmd == argv[0] and ns.run_dir == argv[argv.index("--run-dir") + 1]
    assert e.value.args[0].runs == [str(job / "a"), str(job / "b")]


def test_run_protocol_is_checked_per_run(data_dir, tmp_path):
    runs = _stage_s_runs(data_dir, tmp_path, seeds=(0,), lr=1e-4)
    cfg = json.loads((ROOT / L.SFT_CONFIG).read_text())
    with pytest.raises(L.ProtocolStop, match="protocol deviation"):     # these short runs set max_steps (round 2, 5)
        L.check_run_protocol(runs[0], cfg, lr=1e-4, seed=0)
    rp = runs[0] / "stage_s" / "sft_report.json"
    rp.write_text(json.dumps({**json.loads(rp.read_text()), "protocol_deviation": None}))
    data_sha = P._sha_file(data_dir / "sft_data.json")
    assert L.check_run_protocol(runs[0], cfg, lr=1e-4, seed=0, data_sha256=data_sha)["micro_batch"] == 8
    with pytest.raises(L.ProtocolStop, match="another data directory"):
        L.check_run_protocol(runs[0], cfg, lr=1e-4, seed=0, data_sha256="0" * 64)
    with pytest.raises(L.ProtocolStop, match="lr/seed"):
        L.check_run_protocol(runs[0], cfg, lr=3e-5, seed=0)
    rep_path = runs[0] / "stage_s" / "sft_report.json"
    rep = json.loads(rep_path.read_text())
    rep["protocol"]["micro_batch"] = 4
    rep_path.write_text(json.dumps(rep))
    with pytest.raises(L.ProtocolStop, match="micro_batch"):
        L.check_run_protocol(runs[0], cfg, lr=1e-4, seed=0)


# ============================================================================================ JDL and switch
@pytest.fixture
def stage_world(tmp_path, monkeypatch):
    """A stage directory from a filled spec, with transferred inputs whose pins match a stand-in SFT config."""
    repo = tmp_path / "repo"
    (repo / "r1/scripts/configs").mkdir(parents=True)
    sft = json.loads((ROOT / L.SFT_CONFIG).read_text())
    sft["tables"][L.TABLE_PIN]["sha256"] = {"proposals.jsonl": _sha(b"P\n"), "configs.json": _sha(b"C\n")}
    (repo / L.SFT_CONFIG).write_text(json.dumps(sft))
    monkeypatch.setattr(RJ, "REPO_ROOT", repo)
    table = tmp_path / "table"
    table.mkdir()
    for name, text in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
        (table / name).write_bytes(text)
    part, psha, rsha = _partition(tmp_path / "rel")
    s = filled()
    s["labels"].update(partition_sha256=psha, receipt_sha256=rsha)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(s))
    stage = tmp_path / "stage"
    man = RJ.stage(spec_path, stage, table=table, partition=part)
    return s, spec_path, stage, man, table, part


def test_render_stages_one_jdl_per_arm_with_the_inputs(stage_world, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    assert man["preview"] is False and set(s["arms"]) == {n[3:-4] for n in man["files"] if n.endswith(".jdl")}
    jdl = (stage / "p4_kev-4b.jdl").read_text()
    assert f"container_image = docker://{DIGEST}" in jdl and "request_GPUs = 1" in jdl
    assert f"+RequestWalltime = {L.arm_walltime_s(s, 'kev-4b')}" in jdl and "NVIDIA H200" in jdl
    assert "label_block.traindev.jsonl,RECEIPT.json" in jdl and "ProvidesEtpCeph" not in jdl
    with pytest.raises(L.Stop, match="not empty"):
        RJ.stage(spec_path, stage, table=table, partition=part)
    bad = copy.deepcopy(s)
    bad["labels"]["receipt_sha256"] = "0" * 64
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(L.Stop, match="not the one the spec pins"):
        RJ.stage(bad_path, tmp_path / "stage_bad", table=table, partition=part)
    prev = RJ.stage(SPEC_PATH, tmp_path / "stage_preview", table=table, partition=part, preview=True)
    assert prev["preview"] is True and "PREVIEW_NOT_SUBMITTABLE" in (tmp_path / "stage_preview/p4_kev-0.8b.jdl").read_text()


def _note_fields(s, spec_sha, **over):
    f = {"approved": "true", "label": "ENGINEERING_ONLY", "phase": "1", "run_id": s["run_id"], "spec_sha256": spec_sha,
         "code_commit": s["paper"]["commit"],
         "labels": f"<root>/sweep1/traindev/label_block.traindev.jsonl sha256 {s['labels']['partition_sha256']}",
         "label_receipt": f"/r/sweep1/traindev/RECEIPT.json sha256 {s['labels']['receipt_sha256']}",
         "source_label_block": f"docs/r1/reports/b2_audit_20261119/label_block.jsonl sha256 {L.SOURCE_BLOCK_SHA256}",
         "label_freeze": f"{s['labels']['freeze_record']['path']} sha256 {s['labels']['freeze_record']['sha256']}",
         "split_file": f"{L.SPLIT_FILE['path']} sha256 {L.SPLIT_FILE['sha256']}",
         "arms": "kev-0.8b, kev-4b, qwen3.5-0.8b-base, qwen3.5-4b-base (P4-ARMS A)",
         "host_config": f"{L.HOST_CONFIG} {s['host_config']['sha256']}", "micro_batch": "8 (P4-MB A)",
         "image": s["image"]["digest"], "versions_sha256": s["image"]["versions_sha256"],
         "env3_freeze": f"{L.ENV3_FREEZE} (R1-ENV-PIN; R1-TRACKP-V21-FREEZE)", "h200_smoke_e0": "docs/r1/reports/a.md",
         "h200_sft_probe": "docs/r1/reports/x.md", "gpu_hours_cap": "40 (P4-CAP A); slot_hours_cap: 64",
         "job_layout": "one job per base (P4-JOB A)", "real_label_test_read": "none (P4-PHASE1-TEST A)",
         "evaluation_seeds_read": "none", "table_pin": "sweep1_v3 (c3_features/v3)",
         "duplicate_policy": "heldout_excludes_seen (R1-TRACKP-SFT-DUP)",
         "split": "P3 (9 test / 3 dev / 6 train per node), the signed split file (P4-P1SPLIT A)",
         "lr_grid": "1e-5,3e-5,1e-4; seeds per lr: 3; learning curve: 250, 500 and the full set, seed 20261122 + n",
         "host": "NEMO2 H200 (HTCondor), R1-T1-HOST-TASL", "harness_commit": "none (no harness import)",
         "P1": "PASS — docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md and the receipt",
         "P2": "PASS — P.3a records", "P3": "PASS — docs/r1/reviews/TRACKP_P4_RUNNER_REVIEW.md",
         "P4": "PASS — not applicable to phase 1 (T0 is one suite)",
         "P5": "PASS — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22, R1-TRACKP-IMAGE-V22-B: smoke, E0, probe",
         "P6": "PASS — R1-TRACKP-P4-DECISIONS", "P7": "PASS — trackp.py --check-config clean",
         "P8": "PASS — R1-T1-HOST-TASL"}
    f["labels"] = f["labels"].replace("<root>", "/release")
    f.update(over)
    return f


def _note(dirpath: Path, fields: dict, name="trackp_p4_20991231.md") -> Path:
    d = dirpath / "docs/r1/authorizations"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    return p


def test_switch_check_binds_the_note_to_the_stage(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    monkeypatch.setattr(SW, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SW, "_blob_on_main", lambda rel: rel == "docs/r1/reports/x.md")
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    yes = lambda rel, raw: True  # noqa: E731
    note = _note(tmp_path, _note_fields(s, spec_sha))
    got = SW.check(stage, note, on_main=yes)
    with pytest.raises(SW.Stop, match="probe record docs/r1/reports/x.md is not on origin/main"):
        SW.check(stage, note, on_main=yes, blob_on_main=lambda rel: False)
    assert got["arms"] == s["arms"] and got["spec_sha256"] == spec_sha
    with pytest.raises(SW.Stop, match="not committed"):
        SW.check(stage, note, on_main=lambda rel, raw: False)
    for key, value, match in (("approved", "false", "approved"), ("P5", "PASS — smoke", "P5 must cite"),
                              ("P5", "PASS — R1-TRACKP-IMAGE-V22, R1-TRACKP-IMAGE-V22-B", "must cite R1-TRACKP-IMAGE-V21"),
                              ("P5", "PASS — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22-B",          # V22-B is not V22
                               "must cite R1-TRACKP-IMAGE-V22$"),
                              ("P5", "PASS — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22", "must cite R1-TRACKP-IMAGE-V22-B"),
                              ("labels", "/r/label_block.traindev.jsonl sha256 0", "labels must contain"),
                              ("micro_batch", "16", "micro_batch"), ("gpu_hours_cap", "60; slot_hours_cap: 64", "40"),
                              ("arms", "kev-0.8b, qwen3.5-0.8b-base, qwen3.5-4b-base", "arms"),
                              ("real_label_test_read", "phase1", "none"), ("spec_sha256", "0" * 64, "spec_sha256"),
                              ("image", L.IMAGE_V2, "image must contain"), ("h200_sft_probe", "<record>", "placeholder"),
                              ("env3_freeze", L.ENV3_FREEZE, "R1-TRACKP-V21-FREEZE"), ("P2", "FAIL", "P2 is not recorded as PASS"),
                              ("gpu_hours_cap", "40.5 (P4-CAP A); slot_hours_cap: 64", "40"),
                              ("table_pin", "sweep1_v2", "table_pin must contain"),
                              ("duplicate_policy", "drop_from_train", "duplicate_policy"),
                              ("h200_sft_probe", "docs/r1/reports/other.md", "h200_sft_probe must contain"),
                              ("harness_commit", "c025f89a", "harness_commit")):
        bad = _note(tmp_path, _note_fields(s, spec_sha, **{key: value}), name="trackp_p4_20991230.md")
        with pytest.raises(SW.Stop, match=match):
            SW.check(stage, bad, on_main=yes)
    (stage / "p4_kev-4b.jdl").write_text((stage / "p4_kev-4b.jdl").read_text() + "# edited\n")
    with pytest.raises(SW.Stop, match="changed after staging"):
        SW.check(stage, note, on_main=yes)


def test_switch_submit_needs_both_keys_the_binding_and_the_first_arm(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    monkeypatch.setattr(SW, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SW, "_blob_on_main", lambda rel: True)
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    yes = lambda rel, raw: True  # noqa: E731
    note = _note(tmp_path, _note_fields(s, spec_sha))
    submitted = []
    real_run = subprocess.run

    ledger = tmp_path / "sealed" / s["run_id"] / L.SUBMISSION_LEDGER

    def run(argv, **kw):
        if argv[0] == "condor_submit":          # confirmation note: the run ledger already charges this arm
            arm = argv[1][len("p4_"):-len(".jdl")]
            assert arm in [json.loads(x)["arm"] for x in ledger.read_text().splitlines()]
            submitted.append(argv[1])
            return _res(0, "1 job(s) submitted to cluster 7.")
        return real_run(argv, **kw)
    monkeypatch.setattr(SW.subprocess, "run", run)
    monkeypatch.delenv(SW.ENABLE_ENV, raising=False)
    kw = dict(on_main=yes, launch_binding=lambda repo, sp, rows: {"rows": rows}, spec_path=stage / "p4_spec.json",
              sealed_root=tmp_path / "sealed")
    with pytest.raises(SW.Stop, match="disabled"):
        SW.submit(stage, note, enable=True, **kw)
    monkeypatch.setenv(SW.ENABLE_ENV, "1")
    with pytest.raises(SW.Stop, match="disabled"):
        SW.submit(stage, note, enable=False, **kw)
    with pytest.raises(SW.Stop, match="the other arms need --first-record"):
        SW.submit(stage, note, enable=True, **kw)
    out = SW.submit(stage, note, enable=True, arm="kev-0.8b", **kw)
    assert submitted == ["p4_kev-0.8b.jdl"] and set(L.PLAN_ROWS) == set(out["submitted"][0]["launch"]["rows"])
    with pytest.raises(SW.Stop, match="not sealed yet"):                   # its job is pending (the run ledger)
        SW.submit(stage, note, enable=True, arm="kev-0.8b", **kw)
    with pytest.raises(SW.Stop, match="already submitted"):                # and the stage's once-only marker
        SW.submit(stage, note, enable=True, arm="kev-0.8b", **{**kw, "sealed_root": tmp_path / "other_root"})
    with pytest.raises(SW.Stop, match="not the committed spec"):
        SW.submit(stage, note, enable=True, arm="kev-0.8b", **{**kw, "spec_path": SPEC_PATH})
    # with the first arm's record checked (test_first_record_gate), the other arms go, the first not again
    seen = []
    monkeypatch.setattr(SW, "check_first_record",
                        lambda path, spec, sha, root: seen.append(path) or {"first_record_sha256": "r"})
    # review round 1, M2: sealed attempts that already charge the cap block a submission that would pass it
    for n, h in ((1, 30.0), (2, 2.0)):
        _sealed_attempt(tmp_path / "sealed", s, "kev-4b", "f" * 64, n=n, gpu_hours=h, stop="STOP: x")
    with pytest.raises(SW.Stop, match="exceeds P4-CAP"):
        SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    import shutil as _sh
    _sh.rmtree(tmp_path / "sealed")
    _sealed_attempt(tmp_path / "sealed", s, "kev-4b", "f" * 64, n=1, gpu_hours=1.0)          # STOP-free: done
    with pytest.raises(SW.Stop, match="already have a sealed STOP-free attempt"):
        SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    _sh.rmtree(tmp_path / "sealed")
    out = SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    assert submitted == ["p4_kev-0.8b.jdl", "p4_kev-4b.jdl", "p4_qwen3.5-0.8b-base.jdl", "p4_qwen3.5-4b-base.jdl"]
    assert seen[-1] == tmp_path / "rec.json" and all(e["first_record_sha256"] == "r" for e in out["submitted"])
    assert out["submitted"][0]["cap"]["charged_gpu_hours"] == 0 and out["submitted"][0]["stage_manifest_sha256"]
    ledger = (tmp_path / "sealed" / s["run_id"] / L.SUBMISSION_LEDGER).read_text().splitlines()
    assert [json.loads(x)["arm"] for x in ledger] == ["kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base"]
    assert all("intended_utc" in json.loads(x) for x in ledger)          # written before condor_submit
    with pytest.raises(SW.Stop, match="not sealed yet"):                 # round 3, minor 1: one running job per arm
        SW.check_cap(s, ["kev-4b"], tmp_path / "sealed")


def test_first_record_gate(stage_world, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    sealed = tmp_path / "sealed"
    arm_dir = sealed / s["run_id"] / "kev-0.8b" / "attempt-1"
    arm_dir.mkdir(parents=True)

    def write(**over):
        rec = {"run_id": s["run_id"], "arm": "kev-0.8b", "spec_sha256": spec_sha, "image": {"digest": DIGEST},
               "gpu": {"name": L.GPU_MODEL}, "env3_freeze": {"status": "causal_conv1d_only"}, "stop": None,
               "steps": ["identity", "test_path"], **over}
        (arm_dir / "job_record.json").write_text(json.dumps(rec))
        (arm_dir / "SEAL_RECEIPT.json").write_text(
            json.dumps({"job_record_sha256": P._sha_file(arm_dir / "job_record.json")}))
        (arm_dir / "SHA256SUMS").write_text(f"{P._sha_file(arm_dir / 'job_record.json')}  job_record.json\n")
    write()
    assert SW.check_first_record(arm_dir / "job_record.json", s, spec_sha, sealed)["first_record_sha256"]
    with pytest.raises(SW.Stop, match="alone first"):
        SW.check_first_record(None, s, spec_sha, sealed)
    for over, match in (({"stop": "STOP: x"}, "stop"), ({"steps": ["identity", "data"]}, "stop"),
                        ({"env3_freeze": {"status": "other"}}, "env3_freeze"), ({"gpu": {"name": "L40S"}}, "gpu")):
        write(**over)
        with pytest.raises(SW.Stop, match=match):
            SW.check_first_record(arm_dir / "job_record.json", s, spec_sha, sealed)
    write()
    with pytest.raises(SW.Stop, match="must be"):
        SW.check_first_record(tmp_path / "job_record.json", s, spec_sha, sealed)


# ============================================================================================ launch binding
def _git(repo, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def test_launch_binding(tmp_path):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    _git(work, "checkout", "-q", "-b", "main")
    (work / "docs/r1").mkdir(parents=True)
    (work / "docs/r1/PLAN.md").write_text("".join(f"| {r} | x |\n" for r in L.PLAN_ROWS))
    (work / "r1/scripts/htcondor/trackp_p4").mkdir(parents=True)
    (work / "r1/scripts/htcondor/trackp_p4/p4_lib.py").write_text("code = 1\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "C")
    c = _git(work, "rev-parse", "HEAD")
    spec = {"paper": {"repo": str(origin), "commit": c}}
    sp = work / "r1/scripts/htcondor/trackp_p4/p4_spec.json"
    sp.write_text(json.dumps(spec))
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "M")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    out = L.verify_launch_p4(work, spec, L.PLAN_ROWS, spec_path=sp)
    assert out["paper_commit"] == c and out["head"] == out["main"]
    with pytest.raises(L.Stop, match="PLAN row R1-X"):
        L.verify_launch_p4(work, spec, L.PLAN_ROWS + ("R1-X",), spec_path=sp)
    with pytest.raises(L.Stop, match="not the spec's paper repository"):
        L.verify_launch_p4(work, {"paper": {"repo": "https://github.com/x/y.git", "commit": c}}, L.PLAN_ROWS,
                           spec_path=sp)
    (work / "r1/scripts/htcondor/trackp_p4/shadow.py").write_text("x\n")
    with pytest.raises(L.Stop, match="untracked code"):
        L.verify_launch_p4(work, spec, L.PLAN_ROWS, spec_path=sp)
    (work / "r1/scripts/htcondor/trackp_p4/shadow.py").rename(tmp_path / "shadow.py")
    (work / "r1/scripts/htcondor/trackp_p4/p4_lib.py").write_text("code = 2\n")
    _git(work, "commit", "-qam", "code after the paper commit")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(L.Stop, match="differs from the paper commit"):
        L.verify_launch_p4(work, spec, L.PLAN_ROWS, spec_path=sp)
    _git(work, "commit", "-q", "--allow-empty", "-m", "local only")
    with pytest.raises(L.Stop, match="must be published"):
        L.verify_launch_p4(work, spec, L.PLAN_ROWS, spec_path=sp)


# ============================================================================================ the note draft
NOTE_DRAFT = ROOT / "docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md"


def test_the_note_draft_parses_and_its_completion_binds_a_filled_spec(tmp_path):
    """The draft reads approved: false and holds placeholders now; filling only its declared open fields (and
    approved) gives a note that p4_switch.parse_note and check_binding accept against a filled spec."""
    with pytest.raises(SW.Stop, match="placeholder"):
        SW.parse_note(NOTE_DRAFT.read_text())
    s = filled()
    spec_sha = "a" * 64
    fills = {"approved": "true", "spec_sha256": spec_sha, "code_commit": s["paper"]["commit"],
             "labels": f"/release/sweep1/traindev/label_block.traindev.jsonl sha256 {s['labels']['partition_sha256']}",
             "label_receipt": f"/release/sweep1/traindev/RECEIPT.json sha256 {s['labels']['receipt_sha256']}",
             "label_freeze": f"{s['labels']['freeze_record']['path']} sha256 {s['labels']['freeze_record']['sha256']}",
             "host_config": f"{L.HOST_CONFIG} {s['host_config']['sha256']}", "image": s["image"]["digest"],
             "versions_sha256": s["image"]["versions_sha256"], "h200_smoke_e0": "docs/r1/reports/smoke.md",
             "h200_sft_probe": "docs/r1/reports/x.md (per base at micro-batch 8)",
             "P1": "PASS — docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md and the receipt",
             "P2": "PASS — P.3a records", "P3": "PASS — docs/r1/reviews/TRACKP_P4_RUNNER_REVIEW.md",
             "P4": "PASS — the author's tick: not applicable to phase 1 (T0 is one suite)",
             "P5": "PASS — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B: records",
             "P7": "PASS — trackp.py --check-config clean",
             "env3_freeze": f"{L.ENV3_FREEZE} sha256 {L.ENV3_FREEZE_SHA256} (R1-ENV-PIN; R1-HTC-QTORCH); "
                            "under R1-TRACKP-V21-FREEZE"}
    lines = []
    import re
    for line in NOTE_DRAFT.read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:", line)
        lines.append(f"{m.group(1)}: {fills[m.group(1)]}" if m and m.group(1) in fills else line)
    fields = SW.parse_note("\n".join(lines) + "\n")
    SW.check_binding(fields, s, spec_sha)
    assert fields["run_id"] == SPEC["run_id"] == s["run_id"]


V22_GPU = "sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949"        # V22_BUILD_20261124.md
V22_CPU = "sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8"


def test_the_shipped_spec_host_config_and_note_draft_name_image_v22():
    """Image v2.2 in the spec, the host config (image fields; its TODO_VERIFY_ON_HOST values stay) and the note draft;
    the VERSIONS.txt sha256 stays a placeholder (it is not in the cluster records); v2 and v2.1 appear nowhere as the
    image; the image rows are PLAN rows of this checkout and of ``PLAN_ROWS``."""
    assert SPEC["image"]["digest"] == "ghcr.io/dowlingwong/r1-htc-gpu@" + V22_GPU
    assert SPEC["image"]["row"] == L.IMAGE_ROW == "R1-TRACKP-IMAGE-V22-B"
    assert SPEC["image"]["tag"] == "20261124-v2.2-667bb9c2"
    assert SPEC["image"]["versions_sha256"].startswith("TODO_VERIFY_ON_HOST")
    for key in (("paper", "commit"), ("host_config", "sha256"), ("labels", "partition_sha256"),
                ("labels", "receipt_sha256")):
        assert L._placeholder(SPEC[key[0]][key[1]]), key
    assert L._placeholder(SPEC["labels"]["freeze_record"]["sha256"]) and SPEC["estimate"]["source"].startswith("TODO")
    host = json.loads((ROOT / L.HOST_CONFIG).read_text())
    assert host["image"] == {"gpu": V22_GPU, "cpu": V22_CPU, "tag": "20261124-v2.2-667bb9c2"}
    assert host["host"] == "HTCondor GPU (image v2.2)" and "TODO_VERIFY_ON_HOST" in json.dumps(host)
    import re
    text = NOTE_DRAFT.read_text()
    assert re.search(r"^approved: false$", text, re.M) and not re.search(r"^approved: true", text, re.M)
    assert re.search(r"^image: (\S+)", text, re.M).group(1) == SPEC["image"]["digest"]
    assert re.search(r"^versions_sha256: <FILL", text, re.M)
    p5 = re.search(r"^P5: (.*)$", text, re.M).group(1)
    assert p5.startswith("PENDING") and all(SW._cites(p5, r) for r in SW.P_CITES["P5"])
    for needle in ("759993", "759994", "759997", "760000", V22_GPU.split(":")[1], V22_CPU.split(":")[1],
                   "fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312", "V22_BUILD_20261124.md",
                   "TRACKP_V22_IMAGE_REVIEW_20261124.md"):
        assert needle in p5, needle
    assert "R1-TRACKP-P4-RUNNER-DECISIONS (1)" in re.search(r"^env3_freeze: (.*)$", text, re.M).group(1)
    for row in ("R1-TRACKP-IMAGE-V21", "R1-TRACKP-IMAGE-V22", "R1-TRACKP-IMAGE-V22-B"):
        assert row in L.PLAN_ROWS
    plan = (ROOT / "docs/r1/PLAN.md").read_text()
    for row in L.PLAN_ROWS:
        assert re.search(rf"^\| {re.escape(row)} \|", plan, re.M), row
    for old in (L.IMAGE_V2, L.IMAGE_V21):
        assert old.split("@")[1] not in json.dumps(SPEC) and old.split("@")[1] not in json.dumps(host["image"])


def test_the_test_path_refuses_real_labels(tmp_path):
    from r1.scripts import trackp_p4_test_path as TPATH
    d = tmp_path / "data"
    d.mkdir()
    (d / "sft_data.json").write_text(json.dumps({"labels": {"kind": "label_block"}}))
    args = ["--data", str(d)] + sum(([f"--{k}", "x"] for k in ("table", "run", "arm", "sweep", "paper-root",
                                                                "classification", "host-config", "ledger-dir", "out")), [])
    with pytest.raises(SystemExit, match="synthetic labels only"):
        TPATH.main(args)


def test_the_test_path_runs_replay_predict_and_report_on_cpu(sweep, tmp_path):
    """Review round 1, M3: the synthetic test path end to end on CPU (hash-bag stand-in for the arm's model), with the
    labels the real ``trackp.py sft-data --labels synthetic`` would write."""
    from contextlib import contextmanager
    from r1.scripts import trackp_p4_test_path as TPATH
    from r1.tests.test_trackp_sft import TOKS
    table = tmp_path / "table"
    table.mkdir()
    (table / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sweep["rows"]))
    _, files = SD.load_table(table)
    data = tmp_path / "data"
    SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"], seed=0), _prompts(sweep), data,
                      table_record={"path": str(table), "sha256": files})
    runs = _stage_s_runs(data, tmp_path, seeds=(0,), lr=1e-4)
    model = tiny.build_hashbag(seed=0)

    @contextmanager
    def build():
        yield model, {"stand_in": "hashbag"}, ["lease"]
    a = TPATH.parse(["--data", str(data), "--table", str(table), "--run", str(runs[0]), "--arm", "kev-0.8b",
                     "--sweep", "x", "--paper-root", "x", "--classification", "x", "--host-config", "x",
                     "--ledger-dir", str(tmp_path / "ledgers"), "--out", str(tmp_path / "report")])
    out = TPATH.run(a, replay_inputs=sweep["inputs"], tokenizers=TOKS, build=build())
    assert out["labels"] == "synthetic" and out["evaluation_seeds_read"] is False and out["test_n"] > 0
    assert (tmp_path / "report" / "report" / "test_report.json").is_file() and out["lease"] == ["lease"]
    assert out["report_sha256"] == _sha((tmp_path / "report" / "report" / "test_report.json").read_bytes())
    assert len(list((tmp_path / "ledgers").iterdir())) == 1                       # the one-read ledger


def test_job_script_syntax():
    assert subprocess.run(["bash", "-n", str(PKG / "p4_job.sh")]).returncode == 0
