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
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import re

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
import p4_fill_host_config as FH  # noqa: E402
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


@pytest.mark.parametrize("image_line, status, label", [
    ("causal-conv1d==1.7.0", "identical", None),                                     # image v2.2 (source build)
    ("causal-conv1d==1.7.0+cu12torch2.6cxx11abiFALSE", "causal_conv1d_only", "cu12torch2.6cxx11abiFALSE"),
    ("causal-conv1d==1.7.0+local", "causal_conv1d_only", "local"),
    ("causal-conv1d==1.7.0+cu124.src.1", "causal_conv1d_only", "cu124.src.1"),
])
def test_freeze_admits_1_7_0_with_any_local_build_label_and_records_it(image_line, status, label):
    """R1-TRACKP-P4-RUNNER-DECISIONS (1): "the same version number" reads as version 1.7.0, any local build label
    admitted and recorded; the env3 line is checked against 1.7.0 (also when the freeze is identical)."""
    got = P.check_env3_freeze(_swap("causal-conv1d==1.7.0", image_line), PINNED)
    assert got["status"] == status and got["rule"] == "R1-TRACKP-V21-FREEZE"
    assert got["decision"] == "R1-TRACKP-P4-RUNNER-DECISIONS (1)"
    assert got["image_line"] == image_line and got["version"] == "1.7.0" and got["local_label"] == label
    if status != "identical":
        assert got["pinned_line"] == "causal-conv1d==1.7.0" and "disclosed" in got["disclosure"]
        assert label in got["disclosure"]
    else:
        assert "pinned_line" not in got and "disclosure" not in got


@pytest.mark.parametrize("got, match", [
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.1"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0.post1"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.1+local"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0+"), "is not causal-conv1d==1.7.0"),        # empty label
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0+a..b"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal_conv1d==1.7.0"), "is not causal-conv1d==1.7.0"),        # other spelling
    (_swap("causal-conv1d==1.7.0", "causal-conv1d>=1.7.0"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0",                                                                  # a direct reference
           "causal-conv1d @ file:///opt/r1/wheels/causal_conv1d-1.7.0+cu12-cp312-cp312-linux_x86_64.whl"),
     "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d @ https://github.com/Dao-AILab/causal-conv1d/releases/download/"
           "v1.7.0/causal_conv1d-1.7.0-cp312-cp312-linux_x86_64.whl"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", "causal-conv1d @ file:///w/some_build"), "is not causal-conv1d==1.7.0"),
    (_swap("causal-conv1d==1.7.0", None), "one line for one line"),                       # the line removed
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0") + "causal-conv1d==1.7.0+x\n", "one line for one line"),
    (_swap("torch==2.6.0+cu124", "torch==2.6.1+cu124"), "outside the causal_conv1d line"),
    (_swap("torch==2.6.0+cu124", "torch==2.6.0+cu126"), "outside the causal_conv1d line"),  # labels only on causal
    (_swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.0+cu12") + "einops==9.9\n", "outside the causal_conv1d line"),
    (PINNED + "causal-conv1d==1.7.0\n", "duplicate line"),
])
def test_v21_freeze_stops_on_any_other_difference(got, match):
    with pytest.raises(P.P4Stop, match=match):
        P.check_env3_freeze(got, PINNED)


def test_freeze_needs_the_pinned_causal_line_at_1_7_0():
    """The pin itself must hold causal-conv1d==1.7.0 (the line is checked against 1.7.0, not against whatever the
    pinned file says)."""
    other_pin = _swap("causal-conv1d==1.7.0", "causal-conv1d==1.6.0")
    with pytest.raises(P.P4Stop, match="does not hold causal-conv1d==1.7.0"):
        P.check_env3_freeze(other_pin, other_pin)


# ============================================================================================ labels
# P4-F2 A in synthetic form: the sealed v2 table, the v3 table (b"P\n") and its configs (b"C\n") stand in for the real
# B.2 / sweep1_v3 tables through arms_freeze's own constants; the identity result is a synthetic passing one.
SEALED_SYN = _sha(b"SEALED v2 table\n")


def _identity(sealed=SEALED_SYN, arms=None, configs=None, **over) -> dict:
    from r1.c3 import arms_freeze as AF
    return {"schema": AF.IDENTITY_SCHEMA, "featurizer": AF.FEATURIZER, "pass": True,
            "sealed_proposals_sha256": sealed, "arms_proposals_sha256": arms or _sha(b"P\n"),
            "configs_sha256": {"sealed": configs or _sha(b"C\n"), "arms": configs or _sha(b"C\n")},
            "n_budget_frac_left_differ": 3, "n_other_differences": 0, **over}


def _write_identity(root: Path, identity: dict, monkeypatch) -> str:
    path = Path(root) / P.FEAT_ONE_IDENTITY["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(identity, indent=1, sort_keys=True) + "\n")
    sha = _sha(path.read_bytes())
    monkeypatch.setattr(P, "FEAT_ONE_IDENTITY", {"path": P.FEAT_ONE_IDENTITY["path"], "sha256": sha})
    return sha


@pytest.fixture
def f2(monkeypatch):
    """arms_freeze's sweep-1 constants pointed at the synthetic tables (require_feat_one reads them at call time)."""
    from r1.c3 import arms_freeze as AF
    monkeypatch.setattr(AF, "SWEEP1_SEALED_PROPOSALS_SHA256", SEALED_SYN)
    monkeypatch.setattr(AF, "SWEEP1_V3_PROPOSALS_SHA256", _sha(b"P\n"))
    monkeypatch.setattr(AF, "SWEEP1_V3_CONFIGS_SHA256", _sha(b"C\n"))
    return lambda root: _write_identity(root, _identity(), monkeypatch)


def _partition(tmp_path, *, block=P.SOURCE_BLOCK_SHA256, source="sweep1", stage="traindev", props=SEALED_SYN):
    d = tmp_path / "release" / "sweep1" / "traindev"
    d.mkdir(parents=True)
    (d / P.PARTITION_NAME).write_text('{"proposal_id": "x"}\n')
    psha = _sha((d / P.PARTITION_NAME).read_bytes())
    (d / P.RECEIPT_NAME).write_text(json.dumps({"source": source, "stage": stage, "release_commit": "c" * 40,
                                                "inputs": {"label_block_sha256": block, "proposals_sha256": props},
                                                "outputs": {P.PARTITION_NAME: psha}, "counts": {"released_label_rows": 1}}))
    return d, psha, _sha((d / P.RECEIPT_NAME).read_bytes())


def test_partition_is_bound_to_the_note_and_the_frozen_block(tmp_path, f2):
    f2(tmp_path)
    kw0 = {"table_proposals_sha256": _sha(b"P\n"), "identity_root": tmp_path}
    d, psha, rsha = _partition(tmp_path)
    got = P.check_partition(d, partition_sha256=psha, receipt_sha256=rsha, **kw0)
    assert got["source_block_sha256"] == P.SOURCE_BLOCK_SHA256 and got["release_commit"] == "c" * 40
    assert got["table_binding"]["receipt_proposals_sha256"] == SEALED_SYN
    with pytest.raises(P.P4Stop, match="note's labels"):
        P.check_partition(d, partition_sha256="0" * 64, receipt_sha256=rsha, **kw0)
    with pytest.raises(P.P4Stop, match="label_receipt"):
        P.check_partition(d, partition_sha256=psha, receipt_sha256="0" * 64, **kw0)
    for kw, match in (({"block": "0" * 64}, "frozen sweep-1 block"), ({"source": "sweep2"}, "sweep-1 train/dev"),
                      ({"stage": "test"}, "sweep-1 train/dev")):
        sub = tmp_path / str(len(kw)) / kw.get("source", kw.get("stage", "b"))
        d2, p2, r2 = _partition(sub, **kw)
        with pytest.raises(P.P4Stop, match=match):
            P.check_partition(d2, partition_sha256=p2, receipt_sha256=r2, **kw0)
    (d / P.PARTITION_NAME).rename(d / "moved")
    (d / P.PARTITION_NAME).symlink_to(d / "moved")
    with pytest.raises(P.P4Stop, match="missing"):
        P.check_partition(d, partition_sha256=psha, receipt_sha256=rsha, **kw0)


def test_f2_the_receipt_must_release_the_sealed_v2_table_bound_by_feat_one(tmp_path, f2, monkeypatch):
    """P4-F2 A: the sealed v2 receipt table is accepted after A3's FEAT-ONE check against the sweep1_v3 table; the v3
    pin itself, any other table, a missing, altered or failing identity result, or another arms table is a STOP."""
    f2(tmp_path)
    ok = {"inputs": {"proposals_sha256": SEALED_SYN}}
    got = P.check_receipt_table(ok, table_proposals_sha256=_sha(b"P\n"), root=tmp_path)
    assert got["identity"]["sha256"] == P.FEAT_ONE_IDENTITY["sha256"] and got["rule"].startswith("P4-F2 A")
    for props in (_sha(b"P\n"), "0" * 64, None):                 # the v3 pin (the accepted runner's old rule), others
        with pytest.raises(P.P4Stop, match="not the sealed v2 table"):
            P.check_receipt_table({"inputs": {"proposals_sha256": props}}, table_proposals_sha256=_sha(b"P\n"),
                                  root=tmp_path)
    with pytest.raises(P.P4Stop, match="FEAT-ONE: the sweep-1 arms table is not the pinned v3 table"):
        P.check_receipt_table(ok, table_proposals_sha256=_sha(b"other\n"), root=tmp_path)
    with pytest.raises(P.P4Stop, match="identity result .* is missing"):
        P.check_receipt_table(ok, table_proposals_sha256=_sha(b"P\n"), root=tmp_path / "nowhere")
    path = tmp_path / P.FEAT_ONE_IDENTITY["path"]
    path.write_text(path.read_text() + " ")                      # altered after pinning
    with pytest.raises(P.P4Stop, match="not the identity result A3 consumed"):
        P.check_receipt_table(ok, table_proposals_sha256=_sha(b"P\n"), root=tmp_path)
    for over, match in (({"pass": False}, "not a passing"), ({"n_budget_frac_left_differ": 0}, "no budget_frac_left"),
                        ({"sealed_proposals_sha256": "0" * 64}, "does not bind the released sealed table"),
                        ({"configs_sha256": {"arms": "0" * 64}}, "configs.json is not the pinned one")):
        _write_identity(tmp_path, _identity(**over), monkeypatch)
        with pytest.raises(P.P4Stop, match=match):
            P.check_receipt_table(ok, table_proposals_sha256=_sha(b"P\n"), root=tmp_path)


def test_f2_the_published_receipt_and_the_committed_identity_pass_with_the_real_pins():
    """The real constants: the published sweep-1 train/dev receipt (its committed copy; only inputs.proposals_sha256 is
    used) releases the sealed v2 table, and A3's committed identity result binds it to the sweep1_v3 pin. The copies of
    the constants in p4_lib (for the note's label_table_binding line) equal arms_freeze's and p4_phase1's."""
    from r1.c3 import arms_freeze as AF
    receipt = ROOT / "docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json"
    assert _sha(receipt.read_bytes()) == "f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1"
    rec = json.loads(receipt.read_text())
    v3 = json.loads((ROOT / L.SFT_CONFIG).read_text())["tables"][L.TABLE_PIN]["sha256"]["proposals.jsonl"]
    assert v3 == AF.SWEEP1_V3_PROPOSALS_SHA256 == L.V3_PROPOSALS_SHA256
    assert AF.SWEEP1_SEALED_PROPOSALS_SHA256 == L.SEALED_V2_PROPOSALS_SHA256 == rec["inputs"]["proposals_sha256"]
    assert L.FEAT_ONE_IDENTITY == P.FEAT_ONE_IDENTITY
    assert _sha((ROOT / P.FEAT_ONE_IDENTITY["path"]).read_bytes()) == P.FEAT_ONE_IDENTITY["sha256"]
    got = P.check_receipt_table(rec, table_proposals_sha256=v3, root=ROOT)
    assert got["receipt_proposals_sha256"] == AF.SWEEP1_SEALED_PROPOSALS_SHA256 and \
        got["identity"]["n_other_differences"] == 0
    with pytest.raises(P.P4Stop, match="not the sealed v2 table"):          # the accepted runner's rule, now refused
        P.check_receipt_table({"inputs": {"proposals_sha256": v3}}, table_proposals_sha256=v3, root=ROOT)


def test_f2_labels_join_the_v3_table_by_proposal_id_as_a3_joins_them(tmp_path, monkeypatch):
    """A3's join (arms_freeze.load_traindev + training_rows) on a synthetic sweep-1 world: the complete population
    joins; a missing label, a label outside the table, a label on a test row or a duplicate label row is a STOP."""
    from r1.c3 import release
    from r1.tests.test_c3_arms_freeze import ASSIGN, _label, _world
    world = _world(nodes=("digits_mlp",))
    rows, labels = world["tables"]["sweep1"], world["labels"]["sweep1"]
    table = tmp_path / "table"
    table.mkdir()
    (table / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    good = {"stage": "traindev", "source": "sweep1", "counts": {"evaluation_rows": 0}}
    seen = []

    def serve(labs):
        def fake(root, source, receipt_sha256=None):
            seen.append((Path(root), source, receipt_sha256))
            return copy.deepcopy(labs), dict(good)
        monkeypatch.setattr(release, "traindev_labels", fake)
    serve(labels)
    got = P.join_labels(tmp_path / "release", receipt_sha256="a" * 64, table_dir=table)
    assert seen[-1] == (tmp_path / "release", "sweep1", "a" * 64)
    assert got["n_table_rows"] == len(rows) and got["n_label_rows"] == len(labels) == got["n_labelled"]
    assert got["n_traindev_rows"] + got["n_test_rows_skipped"] == len(rows) and got["n_test_rows_skipped"] > 0
    assert set(got) >= {"n_rule_noop", "n_audit", "n_without_label"} and "delta" not in json.dumps(got)
    victim = next(lab for lab in labels if lab["label_kind"] == "audit")
    test_row = next(r for r in rows if ASSIGN[r["instance"]]["split"] == "test" and not r["noop"])
    stray = {**victim, "proposal_id": victim["proposal_id"].replace(":t", ":x")}
    for labs, match in (([lab for lab in labels if lab is not victim], "complete population"),
                        (labels + [stray], "outside the table|not source:instance:trial"),
                        (labels + [_label(test_row)], "test label"),
                        (labels + [victim], "duplicate label row")):
        serve(labs)
        with pytest.raises(P.P4Stop, match=match):
            P.join_labels(tmp_path / "release", receipt_sha256="a" * 64, table_dir=table)


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
    s["caps"]["probe_gpu_hours"] = 0.5
    s["caps"]["probe_charge_files"] = {SYN_PROBE_RUN: [SYN_CHARGE_SHA]}
    return s


# A synthetic recorded probe run matching filled(): one sealed attempt (receipt 0.4 h, wall clock 0.45 h) and its
# charge file, which also holds T1's charge (P4-T1CHARGE A; one synthetic T1 job of 180 s, 0.05 h): 0.5 h in all.
# Review round 2, r2-m2: T1's charge rests on a committed condor_history.txt (SYN_T1_HISTORY, written by _probe_tree).
SYN_PROBE_RUN = "trackp-p4-probe-20261125-a"
SYN_T1_HISTORY = "760065 0 4 180.0\n"
SYN_T1 = {"jobs": [{"cluster_id": "760065", "remote_wallclock_s": 180.0, "charged_gpu_hours": 0.05}],
          "record": {"dir": L.T1_RECORD_DIR, "cluster_ids": ["760065"],
                     "history": {"file": L.T1_HISTORY, "sha256": hashlib.sha256(SYN_T1_HISTORY.encode()).hexdigest(),
                                 "jobs": [{"cluster_id": "760065", "remote_wallclock_s": 180.0}]}},
          "cluster_check": "match", "wallclock_source": "input"}
SYN_CHARGE = (json.dumps({"schema": "trackp_p4_probe_charges/1", "run_id": SYN_PROBE_RUN, "label": "ENGINEERING_ONLY",
                          "supplement": 0, "t1_gpu_hours": 0.05, "t1": SYN_T1,
                          "attempts": {"kev-0.8b/attempt-1": {"receipt_gpu_hours": 0.4, "remote_wallclock_s": 1620.0,
                                                              "cluster_id": "1", "charged_gpu_hours": 0.45}}},
                         indent=1, sort_keys=True) + "\n").encode()
SYN_CHARGE_SHA = hashlib.sha256(SYN_CHARGE).hexdigest()


def _probe_tree(root: Path) -> Path:
    """The recorded probe run of filled() under a sealed root (charge 0.5 h = filled()'s caps.probe_gpu_hours)."""
    d = Path(root) / SYN_PROBE_RUN / "kev-0.8b" / "attempt-1"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": 0.4, "stop": None}))
    (Path(root) / SYN_PROBE_RUN / "_wallclock.json").write_bytes(SYN_CHARGE)
    assert L.T1_REPO_ROOT is not None                                  # the synthetic repository, never the checkout
    (Path(L.T1_REPO_ROOT) / L.T1_RECORD_DIR / L.T1_HISTORY).write_text(SYN_T1_HISTORY)
    return Path(root)


# The spec fields the cluster and the chat fill (cluster test plan §5.1), in validate_spec's order, with the pattern a
# filled value must match. F5: the shipped-spec tests hold both before and after the spec-fill commit.
SPEC_FILL_FIELDS = ((("paper", "commit"), L.COMMIT), (("image", "versions_sha256"), L.SHA),
                    (("host_config", "sha256"), L.SHA), (("labels", "partition_sha256"), L.SHA),
                    (("labels", "receipt_sha256"), L.SHA), (("labels", "freeze_record", "path"),
                                                             re.compile(r"docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md")),
                    (("labels", "freeze_record", "sha256"), L.SHA))


def _spec_value(s, path):
    for k in path:
        s = s[k]
    return s


def test_shipped_spec_validates_and_refuses_launch_until_filled():
    """F5: holds for today's placeholder spec and for the spec after the spec-fill commit (§6 step 9). Each fill
    field is a placeholder or a valid value; launch validation passes exactly when none is left (and the probe-based
    estimate and the probe's charge are filled); a synthetic filled copy always passes."""
    loaded = L.validate_spec(copy.deepcopy(SPEC))
    p = loaded["projection"]
    hours = SPEC["estimate"]["hours"]
    assert p["within_cap"] and p["total_gpu_hours"] == round(sum(h + 0.5 for h in hours.values()), 3)
    assert p["per_arm"]["kev-4b"]["walltime_s"] == int(np.ceil(hours["kev-4b"] * 3600 * 1.5 + 1800))
    open_ = [".".join(path) for path, pat in SPEC_FILL_FIELDS if L._placeholder(_spec_value(SPEC, path))]
    for path, pat in SPEC_FILL_FIELDS:
        v = _spec_value(SPEC, path)
        assert L._placeholder(v) or pat.fullmatch(v), path
    probe_open = L._placeholder(SPEC["estimate"]["source"]) or L.probe_gpu_hours(SPEC) is None
    assert L._placeholder(SPEC["estimate"]["source"]) == (L.probe_gpu_hours(SPEC) is None) == \
        L._placeholder(SPEC["caps"]["probe_charge_files"])                                        # filled together
    if open_ or probe_open:
        with pytest.raises(L.Stop, match=open_[0] if open_ else "estimate.source|probe_gpu_hours|probe_charge_files"):
            L.validate_spec(copy.deepcopy(SPEC), launch=True)
    else:
        assert L.validate_spec(copy.deepcopy(SPEC), launch=True)["projection"]["within_cap"]
    assert L.validate_spec(filled(), launch=True)["run_id"] == SPEC["run_id"]
    for path, value, match in ((("estimate", "source"), "assumed", "h200_sft_probe"),
                               (("estimate", "source"), "h200_sft_probe:", "h200_sft_probe"),
                               (("image", "digest"), "TODO", "image.digest"),
                               (("labels", "receipt_sha256"), "TODO", "labels.receipt_sha256"),
                               (("host_config", "sha256"), "TODO", "host_config.sha256"),
                               (("caps", "probe_gpu_hours"), "TODO: the probe", "caps.probe_gpu_hours"),
                               (("caps", "probe_gpu_hours"), 0.0, "caps.probe_gpu_hours"),
                               (("caps", "probe_gpu_hours"), 0.555, "caps.probe_gpu_hours"),
                               (("caps", "probe_gpu_hours"), True, "caps.probe_gpu_hours")):
        s = filled()
        s[path[0]][path[1]] = value
        with pytest.raises(L.Stop, match=match):
            L.validate_spec(s, launch=True)


def test_the_probe_charge_counts_against_the_cap():
    """P4-PROBECAP A: caps.probe_gpu_hours is added to the projection's cap check, to charged_hours (so to assemble and
    the switch's check_cap); a placeholder counts 0 at default strength only; a probe spec is never a launch spec."""
    s = filled()
    p = L.projection(s)
    assert p["probe_gpu_hours"] == 0.5 and p["total_with_probe_gpu_hours"] == round(p["total_gpu_hours"] + 0.5, 3)
    s["caps"]["probe_gpu_hours"] = round(40.0 - p["total_gpu_hours"] + 0.01, 2)      # the four jobs fit, with it not
    with pytest.raises(L.Stop, match="exceeds P4-CAP"):
        L.validate_spec(s, launch=True)
    s["caps"]["probe_gpu_hours"] = round(40.0 - p["total_gpu_hours"], 2)
    assert L.validate_spec(s, launch=True)["projection"]["within_cap"]
    d = copy.deepcopy(SPEC)
    d["caps"]["probe_gpu_hours"] = "TODO"
    assert L.validate_spec(d)["projection"]["probe_gpu_hours"] is None
    d["caps"]["probe_gpu_hours"] = 41.0
    with pytest.raises(L.Stop, match="caps.probe_gpu_hours"):
        L.validate_spec(d)
    with pytest.raises(L.Stop, match="a probe spec is never a P.4 launch spec"):
        L.validate_spec({**filled(), "probe": dict(L.PROBE)}, launch=True)


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
    (_set("first_arm", "qwen3.5-0.8b-base"), "first_arm must be kev-0.8b"),          # R1-TRACKP-P4-RUNNER-DECISIONS (3)
    (_set("arms", ["kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base"]), "first_arm must be kev-0.8b"),
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
    assert got["local_label"] == "cu12torch2.6cxx11abiFALSE"                  # recorded (R1-TRACKP-P4-RUNNER-DECISIONS)
    assert got["decision"] == "R1-TRACKP-P4-RUNNER-DECISIONS (1)"
    with pytest.raises(L.Stop, match="is not causal-conv1d==1.7.0"):
        L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, _swap("causal-conv1d==1.7.0", "causal-conv1d==1.7.1")))
    with pytest.raises(L.Stop, match="outside the causal_conv1d line"):
        L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, _swap("torch==2.6.0+cu124", "torch==2.7.0")))
    with pytest.raises(L.Stop, match="pip freeze of env3 failed"):
        L.env3_freeze(filled(), ROOT, lambda a, **k: _res(1, "", "boom"))


def test_env3_freeze_step_passes_image_v22s_recorded_freeze():
    """Image v2.2 (V22_BUILD_20261124.md): causal-conv1d 1.7.0 built from source and installed by name, so the freeze
    line stays ``causal-conv1d==1.7.0`` and the sorted freeze diff is empty. The rule records that as ``identical``
    (in any line order), with the causal_conv1d line checked against 1.7.0 and no local label
    (R1-TRACKP-P4-RUNNER-DECISIONS (1))."""
    v22 = "\n".join(reversed([ln for ln in PINNED.splitlines() if ln.strip()])) + "\n"     # uv's own order
    assert "causal-conv1d==1.7.0" in v22.splitlines()
    got = L.env3_freeze(filled(), ROOT, lambda a, **k: _res(0, v22))
    assert got["status"] == "identical" and got["rule"] == "R1-TRACKP-V21-FREEZE"
    assert got["image_line"] == "causal-conv1d==1.7.0" and got["version"] == "1.7.0" and got["local_label"] is None
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


def test_inputs_lay_out_and_check_the_transferred_files(tmp_path, monkeypatch, f2):
    job = tmp_path / "job"
    job.mkdir()
    d, psha, rsha = _partition(tmp_path / "src")
    joins = []

    def join(release_root, *, receipt_sha256, table_dir):      # A3's join itself: test_f2_labels_join_...
        joins.append((Path(release_root), receipt_sha256, Path(table_dir)))
        return {"n_label_rows": 1}
    monkeypatch.setattr(P, "join_labels", join)
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
    f2(clone)                                                  # the identity result in the clone at the paper commit
    monkeypatch.setattr(L, "_phase1", lambda c: P)
    s = filled()
    s["labels"].update(partition_sha256=psha, receipt_sha256=rsha,
                       freeze_record={"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md",
                                      "sha256": _sha(ftext)})
    got = L.inputs(s, clone, job)
    assert Path(got["partition_dir"]).name == "traindev" and got["table_sha256"]["build.json"] == _sha(b"B\n")
    assert got["receipt_proposals_sha256"] == SEALED_SYN and got["labels"]["table_binding"]["rule"].startswith("P4-F2")
    assert joins == [(job / "release", rsha, job / "table")] and got["label_join"] == {"n_label_rows": 1}
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
    # a signed record in UTF-8 with dashes is read whatever the locale; a record that is not UTF-8 is a STOP
    for text, n, ok in ((f"approved: true\nblock \u2014 {P.SOURCE_BLOCK_SHA256} \u2014 signed\n".encode(), "d", True),
                        (b"approved: true\nblock \x97 " + P.SOURCE_BLOCK_SHA256.encode() + b"\n", "x", False)):
        fr.write_bytes(text)
        jd = tmp_path / f"job_{n}"
        jd.mkdir()
        for name, t in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
            (jd / name).write_bytes(t)
        for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
            (jd / name).write_bytes((d / name).read_bytes())
        s_n = copy.deepcopy(s)
        s_n["labels"]["freeze_record"]["sha256"] = _sha(text)
        if ok:
            assert L.inputs(s_n, clone, jd)["label_freeze"]["sha256"] == _sha(text)
        else:
            with pytest.raises(L.ProtocolStop, match="is not UTF-8 text"):
                L.inputs(s_n, clone, jd)
    fr.write_bytes(ftext)
    # minor 4, as P4-F2 A reads it: a receipt of any table but the sealed v2 one is refused (the v3 pin included)
    for n, props in (("o", "0" * 64), ("v3", _sha(b"P\n"))):
        d_o, psha_o, rsha_o = _partition(tmp_path / f"other_table_{n}", props=props)
        jo = tmp_path / f"job_{n}o"
        jo.mkdir()
        for name, t in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
            (jo / name).write_bytes(t)
        for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
            (jo / name).write_bytes((d_o / name).read_bytes())
        s_o = copy.deepcopy(s)
        s_o["labels"].update(partition_sha256=psha_o, receipt_sha256=rsha_o)
        with pytest.raises(L.ProtocolStop, match="not the sealed v2 table"):
            L.inputs(s_o, clone, jo)
    # P4-F2 A: a failing join (a missing or extra proposal id) is a protocol STOP after the identity check
    jj = tmp_path / "job_join"
    jj.mkdir()
    for name, t in (("proposals.jsonl", b"P\n"), ("configs.json", b"C\n"), ("build.json", b"B\n")):
        (jj / name).write_bytes(t)
    for name in (P.PARTITION_NAME, P.RECEIPT_NAME):
        (jj / name).write_bytes((d / name).read_bytes())

    def bad_join(release_root, **kw):
        raise P.P4Stop("STOP: the labels do not join the sweep1_v3 table by proposal id: x")
    monkeypatch.setattr(P, "join_labels", bad_join)
    with pytest.raises(L.ProtocolStop, match="do not join the sweep1_v3 table"):
        L.inputs(s, clone, jj)
    monkeypatch.setattr(P, "join_labels", join)
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


def test_job_reads_text_as_utf8_under_an_ascii_locale(tmp_path):
    """Review note on the sweep-1 freeze record: under ``LC_ALL=C`` with ``PYTHONCOERCECLOCALE=0`` and
    ``PYTHONUTF8=0`` the job's text reads (``_read_utf8``) and its subprocess output (``_sh``, ``_git``) are still
    UTF-8; a file that is not UTF-8 is a STOP, not a ``UnicodeDecodeError``."""
    rec = tmp_path / "C3_SWEEP1_LABEL_FREEZE_20991231.md"
    rec.write_bytes("approved: true\nsigned \u2014 the author \u2013 24 Nov 2026\n".encode())
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"approved: true \x97\n")
    child = tmp_path / "child.py"                     # writes UTF-8 bytes, then a non-UTF-8 byte, to stdout
    child.write_text("import sys\n"
                     "sys.stdout.buffer.write(('STOP: ' + chr(0x2014) + ' x').encode('utf-8') if sys.argv[1] == 'u' "
                     "else bytes([0x97]))\n")
    script = tmp_path / "probe.py"
    script.write_text(f"""import locale, sys
from pathlib import Path
sys.path.insert(0, {str(PKG)!r})
import p4_lib as L
print(getattr(locale, "getencoding", lambda: locale.getpreferredencoding(False))(), sys.flags.utf8_mode)
try:
    Path({str(rec)!r}).read_text()
    print("plain-ok")
except UnicodeDecodeError:
    print("plain-fails")
assert (chr(0x2014) + " the author") in L._read_utf8(Path({str(rec)!r}), L.ProtocolStop)
try:
    L._read_utf8(Path({str(bad)!r}), L.ProtocolStop)
except L.ProtocolStop as e:
    assert "is not UTF-8 text" in str(e)
    print("bad-stops")
r = L._sh([sys.executable, {str(child)!r}, "u"])
assert r.returncode == 0 and r.stdout == "STOP: " + chr(0x2014) + " x", (r.stdout, r.stderr)
print("sh-ok")
r = L._sh([sys.executable, {str(child)!r}, "x"])
assert r.returncode == 0 and r.stdout == chr(0xFFFD), (r.stdout, r.stderr)
print("sh-replace-ok")
""")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHONUTF8", "PYTHONIOENCODING"))}
    env.update(LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONUTF8="0")
    res = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True,   # no -I: it would
                         cwd=tmp_path,                                         # drop PYTHONUTF8=0 (UTF-8 mode on)
                         encoding="utf-8", errors="replace")
    assert res.returncode == 0, res.stderr
    out = res.stdout.split()
    assert out[-3:] == ["bad-stops", "sh-ok", "sh-replace-ok"]
    if out[0].lower().replace("-", "") not in ("ansi_x3.41968", "ascii", "usascii") or out[1] != "0":
        pytest.skip(f"this platform does not give an ASCII locale without UTF-8 mode ({out[:2]})")
    assert out[2] == "plain-fails"                     # the locale really is ASCII: a plain read_text() raises


REAL_STAGE = L.stage                                  # probe_world replaces it; the n3 test restores it


def _fake_hub(hf: Path, pool=None, drop=None) -> str:
    """What the env3 tokenizer step leaves in HF_HOME and prints (TOKENIZER_STAGE): a hub snapshot per POOL entry at its
    pinned revision (files as symlinks to blobs, as huggingface_hub lays them out), and the JSON line. Synthetic."""
    from r1.c3.train import serialize as S
    pool = {n: list(v) for n, v in (pool or S.POOL).items()}
    cache = hf / "hub"
    for name, (repo, rev, sub) in pool.items():
        if name == drop:
            continue
        top = cache / f"models--{repo.replace('/', '--')}"
        snap = top / "snapshots" / rev
        for rel in ([f"{sub}/tokenizer.json", f"{sub}/tokenizer_config.json"] if sub else
                    ["tokenizer.json", "tokenizer_config.json", "config.json"]):
            body = f"{name}:{rel}".encode()
            blob = top / "blobs" / _sha(body)
            blob.parent.mkdir(parents=True, exist_ok=True)
            blob.write_bytes(body)
            (snap / rel).parent.mkdir(parents=True, exist_ok=True)
            if not (snap / rel).exists():
                (snap / rel).symlink_to(os.path.relpath(blob, (snap / rel).parent))
    return json.dumps({"hub_cache": str(cache), "pool": pool}) + "\n"


def test_tokenizers_are_staged_in_the_gpu_job_and_recorded_with_their_sha256(tmp_path):
    """26 Nov 2026 (T4 STOP: no CPU route): the job's own staging step loads every POOL tokenizer by env3 at its pinned
    revision and records each snapshot file with size and sha256; every failure is a STOP (fail closed)."""
    from r1.c3.train import serialize as S
    job = tmp_path / "job"
    got = L.tokenizer_record(job, "loading\n" + _fake_hub(job / "hf"))
    assert got["count"] == len(S.POOL) == 6 and set(got["pool"]) == set(S.POOL)
    laya = got["pool"]["laya-typed-decisions"]
    assert laya["revision"] == S.POOL["laya-typed-decisions"][1] and laya["subfolder"] == "tokenizer"
    body = b"laya-typed-decisions:tokenizer/tokenizer.json"
    assert laya["files"]["tokenizer/tokenizer.json"] == {"size": len(body), "sha256": _sha(body)}
    assert "load_tokenizer" in L.TOKENIZER_STAGE and "HF_HUB_CACHE" in L.TOKENIZER_STAGE
    other = tmp_path / "elsewhere"
    for bad, match in ((lambda j: "6\n", "printed no pool record"),
                       (lambda j: "", "printed no pool record"),
                       (lambda j: _fake_hub(other), "not the job's HF_HOME"),
                       (lambda j: _fake_hub(j / "hf", drop="qwen3.5-4b-base"), "no hub snapshot at its pinned revision"),
                       (lambda j: _fake_hub(j / "hf", pool={"x": ("org/x", "main", None)}), "not \\(repo, pinned"),
                       (lambda j: _fake_hub(j / "hf", pool={"x": ("org/x", "a" * 40, "sub")}).replace(
                           '"sub"', '"other"'), "no tokenizer file")):
        j = tmp_path / f"j{len(list(tmp_path.glob('j*')))}"
        j.mkdir()
        with pytest.raises(L.Stop, match=match):
            L.tokenizer_record(j, bad(j))
    j = tmp_path / "notok"                                     # a snapshot without a tokenizer file
    out = _fake_hub(j / "hf", pool={"x": ("org/x", "b" * 40, None)})
    for f in (j / "hf/hub/models--org--x/snapshots" / ("b" * 40)).glob("tokenizer*"):
        f.unlink()
    with pytest.raises(L.Stop, match="no tokenizer file"):
        L.tokenizer_record(j, out)
    j = tmp_path / "escape"                                    # a snapshot file resolving outside the cache
    out = _fake_hub(j / "hf", pool={"x": ("org/x", "c" * 40, None)})
    link = j / "hf/hub/models--org--x/snapshots" / ("c" * 40) / "config.json"
    link.unlink()
    (tmp_path / "outside.json").write_text("{}")
    link.symlink_to(tmp_path / "outside.json")
    with pytest.raises(L.Stop, match="resolves outside the hub cache"):
        L.tokenizer_record(j, out)
    j = tmp_path / "broken"                                    # review round 1, m3: a broken link is a STOP
    out = _fake_hub(j / "hf", pool={"x": ("org/x", "d" * 40, None)})
    blob = (j / "hf/hub/models--org--x/snapshots" / ("d" * 40) / "config.json").resolve()
    blob.unlink()
    with pytest.raises(L.Stop, match="is a broken link"):
        L.tokenizer_record(j, out)


def test_a_tokenizer_staging_stop_ends_the_probe_before_any_gpu_work(probe_world, tmp_path, monkeypatch):
    """Fail closed, through the real ``stage`` (review round 1, n3): the T4 case (env3 missing, rc 127) and a staged
    snapshot with a broken link (m3) each end the probe with its record written, and no sampler, data build or sft-dev
    runs."""
    spec_path, calls, state = probe_world
    arm = "kev-0.8b"
    payload = {k: f"{k}-weights".encode() for k in L.ARMS[arm] if k}
    reg = {"models": {k: {"repo": f"org/{k}", "revision": "r" * 40,
                          "files": {"w.safetensors": {"sha256": _sha(b), "size": len(b)}}} for k, b in payload.items()}}

    def clone_full(commit, dest, git, sh):                   # a clone with the reviewed probe code, a small registry
        import yaml
        (dest / L.PKG_REL).mkdir(parents=True)
        for name in ("p4_lib.py", "p4_probe.sh", L.PROBE_SPEC_FILE):
            (dest / L.PKG_REL / name).symlink_to(PKG / name)
        (dest / "r1/c3/train").mkdir(parents=True)
        (dest / "r1/c3/train/registry.yaml").write_text(yaml.safe_dump(reg))
        return {"commit": commit}
    monkeypatch.setattr(L, "clone_full", clone_full)
    monkeypatch.setattr(L, "stage", REAL_STAGE)
    for case in ("rc127", "broken_link"):
        def sh(argv, **kw):
            if argv[0] == "curl":
                Path(argv[argv.index("-o") + 1]).write_bytes(payload[argv[-1].split("/")[4]])
                return _res(0)
            assert argv[0] == L.ENV3_PYTHON and "load_tokenizer" in argv[-1]
            if case == "rc127":
                return _res(127, "", "/opt/r1/envs/trackp/bin/python: No such file or directory")
            hf = Path(kw["env"]["HF_HOME"])
            out = _fake_hub(hf)
            snap = next((hf / "hub").glob("models--*/snapshots/*"))
            (snap / "dangling.json").symlink_to(snap / "no_such_blob")
            return _res(0, out)
        job = tmp_path / f"job_{case}"
        sampler = _Sampler((1000,))
        with pytest.raises(L.Stop, match="pool tokenizers failed: /opt/r1|is a broken link"):
            L.run_probe(spec_path, arm, job, sh=sh, popen=sampler, environ={"CUDA_VISIBLE_DEVICES": "GPU-1"})
        rec = json.loads((job / "job_record.json").read_text())
        assert rec["steps"] == ["identity", "clone", "env3_freeze", "configs"] and rec["stop"]
        assert (job / "models" / L.ARMS[arm][1] / "w.safetensors").is_file()      # the real weight step ran first
        assert calls == [] and sampler.argv is None


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

    hub_calls = []

    def sh(argv, **kw):
        if argv[0] == "curl":                          # only the registry weights go by curl
            Path(argv[argv.index("-o") + 1]).write_bytes(payload[argv[-1]])
            return _res(0)
        # R1-TRACKP-P4-RUNNER-DECISIONS (2): the tokenizers are staged through the hub into the job's HF_HOME
        assert kw["env"]["HF_HUB_OFFLINE"] == "0" and kw["env"]["TRANSFORMERS_OFFLINE"] == "0"
        hub_calls.append((argv, kw["env"]["HF_HOME"]))
        return _res(0, _fake_hub(Path(kw["env"]["HF_HOME"])))
    got = L.stage(filled(), "kev-0.8b", clone, job, sh)
    assert set(got["weights"]) == {"kev-0.8b/adapter.safetensors", "qwen3.5-0.8b-base/model.safetensors"}
    assert len(hub_calls) == 1 and hub_calls[0][1] == str(job / "hf") and got["tokenizers"]["count"] == 6
    assert hub_calls[0][0][0] == L.ENV3_PYTHON and "load_tokenizer" in hub_calls[0][0][-1]
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
    with pytest.raises(L.Stop, match="already sealed as attempt-1"):      # round 5 nit: the same output sealed once
        L.seal(job, s, "kev-0.8b", sealed)
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
    root = _probe_tree(tmp_path / "a")
    dirs = [_sealed_attempt(root, s, arm, "f" * 64) for arm in s["arms"]]
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["gpu_hours_consumed"] == 8.5 and asm["gpu_hours_probe"] == 0.5        # P4-PROBECAP A: 4 x 2.0 + 0.5
    assert asm["data_identity"] == {"sha256": "i" * 64}
    with pytest.raises(L.Stop, match="needs every arm"):
        L.assemble(dirs[:3], s, "f" * 64, root)
    root_b = _probe_tree(tmp_path / "b")
    dirs_b = [_sealed_attempt(root_b, s, arm, "f" * 64, **({"data": {"identity": {"sha256": "e" * 64}}}
                                                           if arm == "kev-4b" else {})) for arm in s["arms"]]
    with pytest.raises(L.Stop, match=r"differ in \['data'\]"):
        L.assemble(dirs_b, s, "f" * 64, root_b)
    big_root = _probe_tree(tmp_path / "c")
    big = [_sealed_attempt(big_root, s, arm, "f" * 64, gpu_hours=9.9) for arm in s["arms"]]   # 39.6 + the probe's 0.5
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
    root = _probe_tree(tmp_path / "sealed")
    dirs = [_sealed_attempt(root, s, arm, "f" * 64, n=2) for arm in s["arms"]]
    _sealed_attempt(root, s, "kev-4b", "f" * 64, n=1, stop="STOP: late", gpu_hours=7.0)
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["gpu_hours_consumed"] == 15.5 and len(asm["gpu_hours_by_attempt"]) == 5     # 15.0 + the probe's 0.5
    _sealed_attempt(root, s, "kev-4b", "f" * 64, n=3, gpu_hours=2.0)
    with pytest.raises(L.Stop, match="another STOP-free attempt"):
        L.assemble(dirs, s, "f" * 64, root)
    # a killed job: the files p4_job.sh pre-creates (all empty) and the wrapper's first log line are still sealed,
    # charged at the walltime
    job = tmp_path / "killed"
    job.mkdir()
    for name in ("out.tar", "job_record.json", "SHA256SUMS"):
        (job / name).write_text("")
    (job / "p4_run.log").write_text("P4 container job start 2026-11-25T00:00:00Z host=n1 arm=kev-0.8b uid=1000\n")
    r = L.seal(job, s, "kev-0.8b", tmp_path / "s2")
    assert r["record_readable"] is False and r["sums"] == "absent" and r["identity_verified"] is False
    assert r["charged_gpu_hours"] == round(L.arm_walltime_s(s, "kev-0.8b") / 3600, 4) and r["stop"].startswith("STOP")
    # review m2: a record that is not UTF-8 is unreadable, not a refusal: the attempt is sealed and charged the walltime
    jobu = tmp_path / "not_utf8"
    jobu.mkdir()
    (jobu / "job_record.json").write_bytes(b'{"label": "ENGINEERING_ONLY", "stop": "\x97"}')
    assert L._read_record(jobu / "job_record.json") is None
    (jobu / "p4_run.log").write_text("P4 container job start 2026-11-25T00:00:00Z\n")
    ru = L.seal(jobu, s, "kev-0.8b", tmp_path / "s_u")
    assert ru["record_readable"] is False and ru["identity_verified"] is False and ru["stop"].startswith("STOP")
    assert ru["charged_gpu_hours"] == round(L.arm_walltime_s(s, "kev-0.8b") / 3600, 4)
    assert (tmp_path / "s_u" / s["run_id"] / "kev-0.8b" / "attempt-1" / "job_record.json").read_bytes() == \
        (jobu / "job_record.json").read_bytes()
    # a STOP at identity (no H200 / image in the record) is sealed, unverified, at its own hours
    job2 = tmp_path / "noid"
    job2.mkdir()
    (job2 / "job_record.json").write_text(json.dumps({"schema": L.RECORD_SCHEMA, "label": "ENGINEERING_ONLY",
                                                      "run_id": s["run_id"],
                                                      "arm": "kev-0.8b", "stop": "STOP: landed on L40S",
                                                      "stop_class": "infrastructure", "gpu_hours": 0.01}))
    r2 = L.seal(job2, s, "kev-0.8b", tmp_path / "s2")
    assert r2["attempt"] == 2 and r2["identity_verified"] is False and r2["charged_gpu_hours"] == 0.01
    assert L.charged_hours(s, tmp_path / "s2")["total"] == round(r["charged_gpu_hours"] + 0.01 + 0.5, 4)   # + probe
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
        r["charged_gpu_hours"] + 0.01 + L.arm_walltime_s(s, "kev-4b") / 3600 + 0.5, 4) and got["probe"] == 0.5


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
def stage_world(tmp_path, monkeypatch, f2):
    """A stage directory from a filled spec, with transferred inputs whose pins match a stand-in SFT config (and the
    synthetic FEAT-ONE identity result in the stand-in checkout, P4-F2 A)."""
    repo = tmp_path / "repo"
    (repo / "r1/scripts/configs").mkdir(parents=True)
    f2(repo)
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
    assert man["inputs"]["receipt_table_binding"]["receipt_proposals_sha256"] == SEALED_SYN


def test_render_refuses_a_receipt_of_another_table_preview_or_not(stage_world, tmp_path):
    """P4-F2 A at the render (T5, T8): a receipt whose table is not the sealed v2 one (the v3 pin included) is refused
    before anything is staged, so the stage cannot pass while every job would STOP at step 5."""
    s, spec_path, stage, man, table, part = stage_world
    for n, props in (("v3", _sha(b"P\n")), ("other", "0" * 64)):
        d, psha, rsha = _partition(tmp_path / f"rel_{n}", props=props)
        bad = copy.deepcopy(s)
        bad["labels"].update(partition_sha256=psha, receipt_sha256=rsha)
        bad_path = tmp_path / f"bad_{n}.json"
        bad_path.write_text(json.dumps(bad))
        for preview, spec_file in ((False, bad_path), (True, SPEC_PATH)):
            out = tmp_path / f"stage_{n}_{preview}"
            with pytest.raises(L.Stop, match="not the sealed v2 table"):
                RJ.stage(spec_file, out, table=table, partition=d, preview=preview)
            assert not out.exists()


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
         "env3_freeze": f"{L.ENV3_FREEZE} (R1-ENV-PIN; R1-TRACKP-V21-FREEZE read per R1-TRACKP-P4-RUNNER-DECISIONS (1))",
         "h200_smoke_e0": "docs/r1/reports/a.md",
         "h200_sft_probe": "docs/r1/reports/x.md",
         "gpu_hours_cap": f"40 (P4-CAP A; P4-PROBECAP A: probe_gpu_hours: {s['caps']['probe_gpu_hours']:.2f} GPU-h, "
                          "T1 included, P4-T1CHARGE A); slot_hours_cap: 64",
         "label_table_binding": f"P4-F2 A: {L.SEALED_V2_PROPOSALS_SHA256} to {L.V3_PROPOSALS_SHA256} by "
                                f"{L.FEAT_ONE_IDENTITY['path']} sha256 {L.FEAT_ONE_IDENTITY['sha256']}",
         "probe_charge_files": "; ".join(f"{run} " + ", ".join(shas)
                                         for run, shas in s["caps"]["probe_charge_files"].items()),
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


def _probe_text(s) -> str:
    return "# H200 SFT probe\n" + "".join(f"p4_estimate_hours: {a} {s['estimate']['hours'][a]}\n" for a in s["arms"]) \
        + f"p4_probe_gpu_hours: {s['caps']['probe_gpu_hours']:.2f}\n" \
        + "".join(f"p4_probe_charge_file: {run} " + ("_wallclock.json" if k == 0 else f"_wallclock.{k}.json") +
                  f" {sha}\n" for run, shas in s["caps"]["probe_charge_files"].items() for k, sha in enumerate(shas))


def test_switch_check_binds_the_note_to_the_stage(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    monkeypatch.setattr(SW, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SW, "_blob_text", lambda rel: _probe_text(s) if rel == "docs/r1/reports/x.md" else "")
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
                              ("env3_freeze", f"{L.ENV3_FREEZE} (R1-TRACKP-V21-FREEZE)", "R1-TRACKP-P4-RUNNER-DECISIONS"),
                              ("gpu_hours_cap", "40.5 (P4-CAP A); slot_hours_cap: 64", "40"),
                              ("table_pin", "sweep1_v2", "table_pin must contain"),
                              ("duplicate_policy", "drop_from_train", "duplicate_policy"),
                              ("h200_sft_probe", "docs/r1/reports/other.md", "h200_sft_probe must contain"),
                              ("harness_commit", "c025f89a", "harness_commit"),
                              ("gpu_hours_cap", "40 (P4-CAP A); slot_hours_cap: 64", "P4-PROBECAP A"),
                              ("gpu_hours_cap", "40 (P4-PROBECAP A: probe_gpu_hours: 0.51); slot_hours_cap: 64",
                               "probe_gpu_hours"),
                              ("gpu_hours_cap", "40 (P4-PROBECAP A: probe_gpu_hours: 0.500); slot_hours_cap: 64",
                               "probe_gpu_hours"),
                              ("label_table_binding", f"P4-F2 A: {L.SEALED_V2_PROPOSALS_SHA256}",
                               "label_table_binding must contain"),
                              ("label_table_binding", "", "lacks 'label_table_binding'")):
        bad = _note(tmp_path, _note_fields(s, spec_sha, **{key: value}), name="trackp_p4_20991230.md")
        with pytest.raises(SW.Stop, match=match):
            SW.check(stage, bad, on_main=yes)
    (stage / "p4_kev-4b.jdl").write_text((stage / "p4_kev-4b.jdl").read_text() + "# edited\n")
    with pytest.raises(SW.Stop, match="changed after staging"):
        SW.check(stage, note, on_main=yes)


def test_switch_check_needs_the_probe_hours_in_the_spec(stage_world, monkeypatch, tmp_path):
    """Review m3: at launch, estimate.hours must be the H200 SFT probe's (one 'p4_estimate_hours: <arm> <hours>' line
    per arm in the record on main), so the draft's 8x placeholder hours cannot be launched."""
    s, spec_path, stage, man, table, part = stage_world
    monkeypatch.setattr(SW, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SW, "_blob_on_main", lambda rel: True)
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    note = _note(tmp_path, _note_fields(s, spec_sha))
    yes = lambda rel, raw: True  # noqa: E731
    good = _probe_text(s)
    assert SW.check(stage, note, on_main=yes, blob_text=lambda rel: good)["arms"] == s["arms"]
    assert SW.check_probe_hours(good, s) == {a: s["estimate"]["hours"][a] for a in s["arms"]}
    first = s["arms"][0]
    pg = f"p4_probe_gpu_hours: {s['caps']['probe_gpu_hours']:.2f}"
    assert SW.check_probe_charge(good, s) == s["caps"]["probe_gpu_hours"]
    for text, match in (("", "one 'p4_estimate_hours"),
                        (good.replace(pg + "\n", ""), "one 'p4_probe_gpu_hours"),          # P4-PROBECAP A
                        (good + pg + "\n", "p4_probe_gpu_hours: <hours>' line \\(found 2"),
                        (good.replace(pg, "p4_probe_gpu_hours: 0.49"), "is not the probe's 0.49"),
                        (good.replace(f"p4_estimate_hours: {first} ", f"p4_estimate_hours: {first} 9"),
                         "is not the probe's"),
                        (good + f"p4_estimate_hours: {first} 1.0\n", "found 2"),
                        ("\n".join(x for x in good.splitlines() if not x.endswith(f" {first} "
                                                                             f"{s['estimate']['hours'][first]}")),
                         "found 0")):
        with pytest.raises(SW.Stop, match=match):
            SW.check(stage, note, on_main=yes, blob_text=lambda rel, t=text: t)


def test_switch_submit_needs_both_keys_the_binding_and_the_first_arm(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    monkeypatch.setattr(SW, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SW, "_blob_on_main", lambda rel: True)
    monkeypatch.setattr(SW, "_blob_text", lambda rel: _probe_text(s))
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
    _probe_tree(tmp_path / "sealed")
    _probe_tree(tmp_path / "other_root")
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
    # P4-PROBECAP A: 22.5 sealed + 1.745 pending (kev-0.8b, submitted above) + 15.61 projected = 39.855 fits; with
    # the probe's 0.5 it is 40.355 > 40
    for n, h in ((1, 22.0), (2, 0.5)):
        _sealed_attempt(tmp_path / "sealed", s, "kev-4b", "f" * 64, n=n, gpu_hours=h, stop="STOP: x")
    assert round(22.5 + 1.745 + 15.61, 3) <= 40.0 < round(22.5 + 1.745 + 15.61 + 0.5, 3)
    # the executed counterfactual (round 4, nit): the same sealed attempts and pending submission with a probe tree that
    # charges 0.01 h, matching caps.probe_gpu_hours, pass check_cap
    cf = tmp_path / "counterfactual"
    for n, h in ((1, 22.0), (2, 0.5)):
        _sealed_attempt(cf, s, "kev-4b", "f" * 64, n=n, gpu_hours=h, stop="STOP: x")
    (cf / s["run_id"] / L.SUBMISSION_LEDGER).write_text(json.dumps({"arm": "kev-0.8b"}) + "\n")
    _probe_attempt(cf, "kev-0.8b", 1, 0.01)
    _record_charges(cf, _wc(cf, {SYN_PROBE_RUN: {"kev-0.8b/attempt-1": 0.0}}))
    s_cf = copy.deepcopy(s)
    s_cf["caps"].update(probe_gpu_hours=0.01, probe_charge_files=L.spec_charge_files(L.charge_file_listing(cf)))
    got = SW.check_cap(s_cf, ["kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base"], cf)
    assert got["charged_gpu_hours"] == round(22.5 + 1.745 + 0.01, 4) and got["projected_gpu_hours"] == 15.61
    (L.T1_REPO_ROOT / L.T1_RECORD_DIR / L.T1_HISTORY).write_text(SYN_T1_HISTORY)   # the sealed tree's T1 (r2-m2)
    with pytest.raises(SW.Stop, match="exceeds P4-CAP"):
        SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    import shutil as _sh
    _sh.rmtree(tmp_path / "sealed")
    _probe_tree(tmp_path / "sealed")
    _sealed_attempt(tmp_path / "sealed", s, "kev-4b", "f" * 64, n=1, gpu_hours=1.0)          # STOP-free: done
    with pytest.raises(SW.Stop, match="already have a sealed STOP-free attempt"):
        SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    _sh.rmtree(tmp_path / "sealed")
    _probe_tree(tmp_path / "sealed")
    out = SW.submit(stage, note, enable=True, first_record=tmp_path / "rec.json", **kw)
    assert submitted == ["p4_kev-0.8b.jdl", "p4_kev-4b.jdl", "p4_qwen3.5-0.8b-base.jdl", "p4_qwen3.5-4b-base.jdl"]
    assert seen[-1] == tmp_path / "rec.json" and all(e["first_record_sha256"] == "r" for e in out["submitted"])
    assert out["submitted"][0]["cap"]["charged_gpu_hours"] == 0.5 == out["submitted"][0]["cap"]["probe_gpu_hours"]
    assert out["submitted"][0]["stage_manifest_sha256"]
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
             "gpu_hours_cap": "40 (P4-CAP A; P4-PROBECAP A and P4-T1CHARGE A: probe_gpu_hours: 0.50 GPU-h, T1 "
                              "included; projection 16.94 GPU-h); slot_hours_cap: 64",
             "probe_charge_files": f"{SYN_PROBE_RUN} _wallclock.json {SYN_CHARGE_SHA}"}
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


# The committed host config before its fill (cluster test plan: 18f18cfc… at 4315ab295 and on main 912a7e02) and the
# exact placeholder text of venv.causal_conv1d; every other placeholder reads TODO_VERIFY_ON_HOST.
HOST_CONFIG_PLACEHOLDER_SHA256 = "18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140"
CAUSAL_PLACEHOLDER = "TODO_VERIFY_ON_HOST (the portal build is for sm_89; H200 is sm_90 \u2014 record the image v2 build)"


def _restore_placeholders(cfg: dict) -> dict:
    """The host config with its 19 values put back to the committed placeholders (review round 1, minor 3)."""
    out = json.loads(json.dumps(cfg))
    keys = FH._paths(out)
    for path in FH.EXPECTED:
        *parent, leaf = keys[path]
        _spec_value(out, parent)[leaf] = CAUSAL_PLACEHOLDER if path == "venv.causal_conv1d" else "TODO_VERIFY_ON_HOST"
    return out


def _layout(cfg: dict) -> bytes:
    return (json.dumps(cfg, indent=1, ensure_ascii=True) + "\n").encode()


def _host_config_state(host: dict) -> str:
    """F5: "placeholders" (exactly the 19 known TODO_VERIFY_ON_HOST values) or "filled" (none, and every one of the 19
    values valid under the fill hook's rules); in both states, the file with the 19 placeholders restored is byte for
    byte the committed pre-fill file (sha256 18f18cfc…), so a fill that changes anything else fails."""
    from r1.c3.train import run as R
    left = R.placeholders(host)
    if left:
        assert set(left) == FH.EXPECTED and len(left) == 19, left
        state = "placeholders"
    else:
        keys = FH._paths(host)
        for path in FH.EXPECTED:
            FH.check_value(path, _spec_value(host, keys[path]))
        state = "filled"
    assert _sha(_layout(_restore_placeholders(host))) == HOST_CONFIG_PLACEHOLDER_SHA256
    return state


def test_the_shipped_spec_host_config_and_note_draft_name_image_v22():
    """Image v2.2 in the spec, the host config (image fields) and the note draft; v2 and v2.1 appear nowhere as the
    image; the image rows are PLAN rows of this checkout and of ``PLAN_ROWS``. F5: the cluster fields of the spec and
    the 19 host-config values may be placeholders (today) or filled (after the host-config fill commit and the
    spec-fill commit); the filled forms are checked, so the fill commits need no test change."""
    assert SPEC["image"]["digest"] == "ghcr.io/dowlingwong/r1-htc-gpu@" + V22_GPU
    assert SPEC["image"]["row"] == L.IMAGE_ROW == "R1-TRACKP-IMAGE-V22-B"
    assert SPEC["image"]["tag"] == "20261124-v2.2-667bb9c2"
    v = SPEC["image"]["versions_sha256"]
    assert v.startswith("TODO_VERIFY_ON_HOST") or L.SHA.fullmatch(v)
    for path, pat in SPEC_FILL_FIELDS:
        assert L._placeholder(_spec_value(SPEC, path)) or pat.fullmatch(_spec_value(SPEC, path)), path
    src = SPEC["estimate"]["source"]
    assert src.startswith("TODO") or re.fullmatch(r"h200_sft_probe: docs/r1/reports/\S+\.md", src)
    host = json.loads((ROOT / L.HOST_CONFIG).read_text())
    assert host["image"] == {"gpu": V22_GPU, "cpu": V22_CPU, "tag": "20261124-v2.2-667bb9c2"}
    assert host["host"] == "HTCondor GPU (image v2.2)"
    if _host_config_state(host) == "filled":
        for arm in L.ARMS:                                     # the job's staged directories (T3)
            L.check_local_paths(arm, ROOT, Path("/nonexistent/condor/execute/dir_0"))
        assert L._placeholder(SPEC["host_config"]["sha256"]) or \
            SPEC["host_config"]["sha256"] == _sha((ROOT / L.HOST_CONFIG).read_bytes())
    else:
        assert L._placeholder(SPEC["host_config"]["sha256"])
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
    env3 = re.search(r"^env3_freeze: (.*)$", text, re.M).group(1)
    assert "R1-TRACKP-P4-RUNNER-DECISIONS (1)" in env3 and "<" not in env3 and ">" not in env3   # signable as is
    assert "causal-conv1d==1.7.0, or causal-conv1d==1.7.0+LABEL" in env3
    assert "Every other line must match the pin exactly" in env3
    # review M1: the note admits no wheel or direct reference, and names both STOP forms the code enforces
    assert not re.search(r"wheel[^.;]*admitted", env3, re.I) and "wheel" not in env3.lower()
    assert "causal-conv1d @ file://" in env3 and "causal-conv1d @ https://" in env3
    assert "causal_conv1d spelling (causal_conv1d==1.7.0)" in env3 and "STOP forms" in env3
    for form in ("causal-conv1d @ file:///w/causal_conv1d-1.7.0-cp312-cp312-linux_x86_64.whl", "causal_conv1d==1.7.0"):
        with pytest.raises(P.P4Stop, match="is not causal-conv1d==1.7.0"):           # the code agrees with the note
            P.check_env3_freeze(_swap("causal-conv1d==1.7.0", form), PINNED)
    assert "R1-TRACKP-P4-RUNNER-DECISIONS (2)" in re.search(r"^job_layout: (.*)$", text, re.M).group(1)
    assert "R1-TRACKP-P4-RUNNER-DECISIONS (3)" in text and SPEC["first_arm"] == L.FIRST_ARM == "kev-0.8b"
    assert "R1-TRACKP-P4-RUNNER-DECISIONS" in L.PLAN_ROWS
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


def test_probe_job_script_syntax_and_mode():
    assert subprocess.run(["bash", "-n", str(PKG / "p4_probe.sh")]).returncode == 0
    text = (PKG / "p4_probe.sh").read_text()
    assert 'p4_lib.py" probe "$1" --arm "$2"' in text and "p4_run.log" in text and 'p4_lib.py" job' not in text


# ============================================================================================ probe mode (F1, §4.2)
PROBE_TEMPLATE_PATH = PKG / L.PROBE_SPEC_FILE
PROBE_TEMPLATE = json.loads(PROBE_TEMPLATE_PATH.read_text())


def probe_filled() -> dict:
    s = copy.deepcopy(PROBE_TEMPLATE)
    s["paper"]["commit"] = "3" * 40
    s["image"]["versions_sha256"] = "4" * 64
    s["host_config"]["sha256"] = "5" * 64
    return s


def test_the_probe_template_is_the_p4_spec_with_a_probe_run_id_and_block():
    """§4.2 item 11: the same image, env3, host config, SFT config, table, layout, arms and protocol as p4_spec.json;
    another run id (F10); the fixed probe block; exactly the three host fields left as placeholders."""
    for key in ("gpu_model", "env3", "sft_config", "split_file", "table", "layout", "arms", "first_arm", "protocol"):
        assert PROBE_TEMPLATE[key] == SPEC[key], key
    for key in ("digest", "row", "tag"):
        assert PROBE_TEMPLATE["image"][key] == SPEC["image"][key]
    assert PROBE_TEMPLATE["image"]["digest"] == L.IMAGE_V22 and PROBE_TEMPLATE["host_config"]["path"] == L.HOST_CONFIG
    assert {k: v for k, v in PROBE_TEMPLATE["caps"].items() if k in ("gpu_hours", "slot_hours")} == \
        {"gpu_hours": 40.0, "slot_hours": 64.0}
    assert L.PROBE_RUN_ID.fullmatch(PROBE_TEMPLATE["run_id"]) and PROBE_TEMPLATE["run_id"] != L.P4_RUN_ID
    assert {k: PROBE_TEMPLATE["probe"][k] for k in L.PROBE} == L.PROBE and L.PROBE["steps"] <= 50
    for path in L.PROBE_FILLED:
        assert L._placeholder(_spec_value(PROBE_TEMPLATE, path)), path
    L.validate_spec(copy.deepcopy(PROBE_TEMPLATE))                          # default strength passes
    with pytest.raises(L.Stop, match="paper.commit"):                       # probe strength needs the host fields
        L.validate_probe_spec(copy.deepcopy(PROBE_TEMPLATE))


def test_probe_strength_needs_the_host_fields_but_not_the_probe_record():
    """§4.2 item 12 / F1: probe strength passes with the label fields, estimate.source and caps.probe_gpu_hours still
    placeholders (no h200_sft_probe needed), and refuses an unfilled host field, another image, the P.4 run id, a
    probe block other than the fixed one; launch strength refuses any probe spec."""
    s = probe_filled()
    got = L.validate_probe_spec(s)
    assert got["probe"]["steps"] == 50 and L._placeholder(s["estimate"]["source"])
    assert L._placeholder(s["labels"]["receipt_sha256"]) and L._placeholder(s["caps"]["probe_gpu_hours"])
    L.check_probe_template(s, PROBE_TEMPLATE)
    for edit, match in ((_set("paper", "commit", "TODO"), "paper.commit"),
                        (_set("image", "versions_sha256", "TODO_VERIFY_ON_HOST: x"), "image.versions_sha256"),
                        (_set("host_config", "sha256", "TODO"), "host_config.sha256"),
                        (_set("image", "digest", DIGEST), "image v2.2 by digest"),
                        (_set("run_id", L.P4_RUN_ID), "never the P.4 run"),
                        (_set("run_id", "trackp-p4-p1-20261125-b"), "trackp-p4-probe"),
                        (_set("probe", "steps", 51), "probe must be"),
                        (_set("probe", "lr", 1e-4), "probe must be"),
                        (_set("probe", "labels", "sweep1"), "probe must be"),
                        (_set("probe", "extra", 1), "probe must be"),
                        (_set("arms", ["kev-0.8b", "kev-4b"]), "controls")):
        bad = probe_filled()
        edit(bad)
        with pytest.raises(L.Stop, match=match):
            L.validate_probe_spec(bad)
    with pytest.raises(L.Stop):
        L.validate_spec(probe_filled(), launch=True)
    for edit in (_set("layout", "request_cpus", 4), _set("protocol", "micro_batch", 8),        # the second: no change
                 _set("labels", "partition_sha256", "6" * 64)):
        other = probe_filled()
        edit(other)
        if other == probe_filled():
            continue
        with pytest.raises(L.Stop, match="differs from the committed template"):
            L.check_probe_template(other, PROBE_TEMPLATE)
    with pytest.raises(L.Stop, match="must hold a placeholder"):
        L.check_probe_template(probe_filled(), probe_filled())


def test_visible_devices_must_name_the_one_listed_gpu():
    gpu = {"uuid": "GPU-1"}
    assert L.visible_devices(gpu, {"CUDA_VISIBLE_DEVICES": "GPU-1", "_CONDOR_AssignedGPUs": "GPU-1"})[
        "CUDA_VISIBLE_DEVICES"] == "GPU-1"
    assert L.visible_devices(gpu, {"CUDA_VISIBLE_DEVICES": "0"})["NVIDIA_VISIBLE_DEVICES"] is None
    for env in ({"CUDA_VISIBLE_DEVICES": "GPU-2"}, {"NVIDIA_VISIBLE_DEVICES": "GPU-1,GPU-2"}):
        with pytest.raises(L.Stop, match="F3"):
            L.visible_devices(gpu, env)


def test_estimate_hours_reproduce_the_plans_worked_example():
    """§4.5: n = 593 at 1.26 s per step gives S = 9 x 190 + 3 x (80 + 160) = 2,430 steps and H = 0.8505 -> 0.86 h."""
    proto = {"micro_batch": 8, "effective_batch": 16, "max_epochs": 5}
    assert L.full_steps(593, epochs=5, micro=8, accum=2) == 190 and L.full_steps(250, epochs=5, micro=8, accum=2) == 80
    got = L.estimate_hours(593, 1.26, SPEC, proto)
    assert got["steps"] == 2430 and got["hours"] == 0.86
    assert L.estimate_hours(400, 1.0, SPEC, proto)["steps"] == 9 * 125 + 3 * 80           # 500 is not below 400
    assert L.ceil_hundredth(0.86) == 0.86 and L.ceil_hundredth(0.8601) == 0.87 and L.ceil_hundredth(1e-4) == 0.01


class _Sampler:
    """A stand-in for the nvidia-smi sampler: writes ``samples`` lines at once."""

    def __init__(self, samples):
        self.samples, self.argv = samples, None

    def __call__(self, argv, stdout=None, stderr=None):
        self.argv = argv
        stdout.write("".join(f"2026/11/25 10:00:0{k}.000, {u}, 143771\n" for k, u in enumerate(self.samples)))
        stdout.flush()
        return SimpleNamespace(terminate=lambda: None, wait=lambda timeout=None: 0, kill=lambda: None)


@pytest.fixture
def probe_world(sweep, tmp_path, monkeypatch):
    """Every host step faked as in job_world; trackp.py replaced by the real synthetic data builder and the real Stage S
    loop (hash-bag stand-in) honouring --steps; the sampler faked."""
    spec_path = tmp_path / "p4_probe_spec.json"
    spec_path.write_text(json.dumps(probe_filled()))
    monkeypatch.setattr(L, "image_identity", lambda spec: {"digest": spec["image"]["digest"], "versions_sha256": "4" * 64})
    monkeypatch.setattr(L, "gpu_identity", lambda sh: {"name": L.GPU_MODEL, "uuid": "GPU-1", "memory_total": "143771 MiB"})
    monkeypatch.setattr(L, "host_identity", lambda: {"uid": 1000, "hostname": "n1"})
    monkeypatch.setattr(L, "clone_full", lambda commit, dest, git, sh: dest.symlink_to(ROOT) or {"commit": commit})
    monkeypatch.setattr(L, "env3_freeze", lambda spec, clone, sh: {"status": "identical", "image_line": "x",
                                                                   "local_label": None})
    monkeypatch.setattr(L, "configs", lambda spec, clone, sh: {"host_config": {"sha256": "5" * 64},
                                                              "sft_config": {"sha256": "s"}})

    def stage(spec, arm, clone, job_dir, sh):
        (job_dir / "models" / arm).mkdir(parents=True)
        (job_dir / "models" / arm / "w.safetensors").write_bytes(b"w" * 10)
        return {"weights": {f"{arm}/w": "1" * 64}}
    monkeypatch.setattr(L, "stage", stage)
    monkeypatch.setattr(L, "check_local_paths", lambda arm, clone, job_dir: {})
    monkeypatch.setattr(L, "table_inputs", lambda clone, job_dir: {"table_dir": str(job_dir / "table"),
                                                                  "table_sha256": {"proposals.jsonl": "p"}})
    monkeypatch.setattr(L, "inputs", lambda *a: pytest.fail("the probe must not call inputs"))
    monkeypatch.setattr(L, "test_path", lambda *a: pytest.fail("the probe must not run the test path"))
    calls, state = [], {"oom": False, "labels": "synthetic"}

    def trackp(clone, job_dir, args, sh=None, timeout=0):
        calls.append(args)
        a = {args[k]: args[k + 1] for k in range(1, len(args) - 1) if str(args[k]).startswith("--")}
        if args[0] == "sft-data":
            assert a["--labels"] == "synthetic" and "--label-freeze" not in args
            out = Path(a["--run-dir"]) / "data"
            src = SD.SyntheticLabelSource(sweep["rows"], shift_z=1.5)
            SD.build_sft_data(sweep["rows"], src, _prompts(sweep), out,
                              table_record={"path": str(job_dir / "table"), "sha256": {"proposals.jsonl": "p"}})
            if state["labels"] != "synthetic":
                man = json.loads((out / "sft_data.json").read_text())
                man["labels"]["kind"] = state["labels"]
                (out / "sft_data.json").write_text(json.dumps(man))
        elif args[0] == "sft-dev":
            if state["oom"]:
                raise L.ArmStop("STOP: CUDA OOM in sft-dev at micro-batch 8 (P4-MB; the author decides)")
            data = Path(a["--data"])
            train, val, vs, man = SD.load_sft_data(data, secondary=True)
            from r1.c3.train.model import new_head_parameters
            model = tiny.build_hashbag(seed=int(a["--seed"]))
            run = Path(a["--run-dir"])
            SFT.run_stage_s(model, train, val, run / "stage_s", {**SFT.DEFAULT_PROTOCOL, "micro_batch": 8},
                            lr=float(a["--lr"]), seed=int(a["--seed"]), head_params=new_head_parameters(model),
                            log=lambda x: None, max_steps=int(a["--steps"]),
                            data_sha256=P._sha_file(data / "sft_data.json"), label_status=man["label_status"],
                            val_secondary=vs, duplicate_policy=man["cross_split_duplicates"])
            (run / "report.json").write_text("{}\n")
            (run / "manifest.json").write_text("{}\n")
            (job_dir / "out" / "logs").mkdir(parents=True, exist_ok=True)
            (job_dir / "out" / "logs" / "000_sft-dev.log").write_text("log\n")
        else:
            pytest.fail(f"the probe ran {args[0]}")
        return {"argv": list(map(str, args))}
    monkeypatch.setattr(L, "trackp", trackp)
    return spec_path, calls, state


def _run_probe(spec_path, arm, job, samples=(1000, 52000, 51000), env=None, cluster=None):
    job.mkdir(parents=True)
    sampler = _Sampler(samples)
    env = dict(env if env is not None else {"CUDA_VISIBLE_DEVICES": "GPU-1"})
    if cluster is not None:                      # the HTCondor job ad of a submitted job (its ClusterId)
        ad = job.parent / f"{job.name}.job.ad"
        ad.write_text(f'ClusterId = {cluster}\nProcId = 0\nGlobalJobId = "schedd.nemo#{cluster}.0#1764000000"\n')
        env["_CONDOR_JOB_AD"] = str(ad)
    try:
        return L.run_probe(spec_path, arm, job, popen=sampler, environ=env), sampler
    finally:
        assert subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=job, capture_output=True).returncode == 0


def test_probe_runs_one_short_synthetic_sft_dev_and_keeps_no_checkpoint(probe_world, tmp_path):
    """§4.2 items 1-10: one sft-dev --steps 50 at lr 1e-05, seed 0 on a synthetic-label build; device memory sampled
    by UUID; the record carries the §4.4 fields; out.tar holds only the allow-list (no ckpt/, no best/, no rows)."""
    spec_path, calls, state = probe_world
    job = tmp_path / "job"
    rec, sampler = _run_probe(spec_path, "kev-0.8b", job)
    assert rec["stop"] is None and rec["steps"] == ["identity", "clone", "env3_freeze", "configs", "staging", "table",
                                                    "data", "probe"]
    assert [c[0] for c in calls] == ["sft-data", "sft-dev"]
    dev = calls[1]
    assert dev[dev.index("--steps") + 1] == "50" and dev[dev.index("--lr") + 1] == "1e-05" and \
        dev[dev.index("--seed") + 1] == "0" and "--eval-every" not in dev
    assert sampler.argv[:2] == ["nvidia-smi", "--id=GPU-1"] and sampler.argv[-2:] == ["-lms", "500"]
    assert rec["memory"]["peak_memory_used_mib"] == 52000 and rec["memory"]["memory_total_mib"] == 143771
    assert rec["memory"]["headroom_frac"] == round(1 - 52000 / 143771, 4)
    run = rec["run"]
    assert run["protocol_deviation"] == {"max_steps": 50} and run["protocol"]["micro_batch"] == 8
    assert run["protocol"]["effective_batch"] == 16 and run["max_tokens"] == 1024 and 0 < run["stopped_at"] <= 50
    assert run["s_per_step_wall"] == round(rec["wall"]["wall_s"] / run["stopped_at"], 4)
    assert rec["data"]["labels"] == "synthetic" and rec["data"]["n_train"] > 0 and rec["oom"] is False
    assert rec["staging"]["bytes"] == 10 and rec["code"]["template_sha256"] == _sha(PROBE_TEMPLATE_PATH.read_bytes())
    assert rec["visible_devices"]["CUDA_VISIBLE_DEVICES"] == "GPU-1" and rec["schema"] == L.PROBE_RECORD_SCHEMA
    names = subprocess.run(["tar", "-tf", "out.tar"], cwd=job, capture_output=True, text=True).stdout.split()
    allowed = [k.format(arm="kev-0.8b") for k in L.PROBE_KEEP]
    assert names and all(any(n == a or n.startswith(a + "/") for a in allowed) for n in names), names
    assert not any("ckpt" in n or "/best/" in n or n.endswith(("rows.jsonl", ".npy", "splits.json")) for n in names)
    assert (job / "out/probe/kev-0.8b/stage_s/best").is_dir()                   # weights stayed in the job scratch
    assert json.loads((job / "out/probe/wall.json").read_text())["ok"] is True
    # nothing it writes can count as a P.4 arm (§4.6): the protocol deviation is refused
    sft_cfg = json.loads((ROOT / L.SFT_CONFIG).read_text())
    with pytest.raises(L.ProtocolStop, match="protocol deviation"):
        L.check_run_protocol(job / "out/probe/kev-0.8b", sft_cfg, lr=1e-05, seed=0)


def test_probe_stops_on_oom_mismatch_or_non_synthetic_data_and_still_writes_the_record(probe_world, tmp_path):
    spec_path, calls, state = probe_world
    state["oom"] = True
    with pytest.raises(L.ArmStop, match="CUDA OOM"):
        _run_probe(spec_path, "kev-0.8b", tmp_path / "oom")
    rec = json.loads((tmp_path / "oom" / "job_record.json").read_text())
    assert rec["oom"] is True and rec["stop_class"] == "arm" and rec["memory"]["samples"] == 3
    assert rec["wall"]["ok"] is False and rec["steps"][-1] == "data"
    state["oom"] = False
    with pytest.raises(L.Stop, match="no device-memory sample"):
        _run_probe(spec_path, "kev-0.8b", tmp_path / "nomem", samples=())
    with pytest.raises(L.Stop, match="F3"):
        _run_probe(spec_path, "kev-0.8b", tmp_path / "gpu2", env={"CUDA_VISIBLE_DEVICES": "GPU-2"})
    state["labels"] = "label_block_partition"
    with pytest.raises(L.ProtocolStop, match="not a synthetic-label build"):
        _run_probe(spec_path, "kev-0.8b", tmp_path / "real")
    state["labels"] = "synthetic"
    bad = probe_filled()
    bad["layout"]["request_cpus"] = 4
    bad_path = tmp_path / "bad_probe_spec.json"
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(L.Stop, match="differs from the committed template"):
        _run_probe(bad_path, "kev-0.8b", tmp_path / "tpl")
    other_lib = tmp_path / "p4_lib.py"
    other_lib.write_text("# not the reviewed file\n")
    (tmp_path / "lib").mkdir()
    with pytest.raises(L.Stop, match="transferred p4_lib.py is not the one at the paper commit"):
        L.run_probe(spec_path, "kev-0.8b", tmp_path / "lib", popen=_Sampler((1,)), environ={}, lib_file=other_lib)


def test_probe_attempts_are_sealed_gated_recorded_and_charged(probe_world, tmp_path):
    """Seal (the probe run's own tree, F10), the first-arm gate (S10), the §4.4 record and §4.5 hours from one sealed
    STOP-free attempt per arm, and P4-PROBECAP A: every probe attempt, a killed one at the probe walltime, charged."""
    spec_path, calls, state = probe_world
    s = json.loads(spec_path.read_text())
    sealed = tmp_path / "sealed"
    spec_sha = _sha(spec_path.read_bytes())
    receipts = {}
    for arm in s["arms"]:
        job = tmp_path / f"job_{arm}"
        _run_probe(spec_path, arm, job)
        receipts[arm] = L.seal(job, s, arm, sealed)
        assert Path(receipts[arm]["sealed_path"]).parent.parent.name == s["run_id"] != L.P4_RUN_ID
        assert receipts[arm]["identity_verified"] is True
    killed = tmp_path / "killed"
    killed.mkdir()
    for name in ("out.tar", "job_record.json", "SHA256SUMS"):
        (killed / name).write_text("")
    (killed / "p4_run.log").write_text("P4 probe container job start 2026-11-25T00:00:00Z host=n1 arm=kev-4b\n")
    p4s = filled()
    with pytest.raises(L.Stop, match="this is a probe attempt; it is not sealed with a p4 spec"):   # minor 2
        L.seal(killed, p4s, "kev-4b", tmp_path / "p4_sealed")
    p4k = tmp_path / "p4k"                                     # a killed P.4 job is not sealed into a probe tree
    p4k.mkdir()
    (p4k / "p4_run.log").write_text("P4 container job start 2026-11-25T00:00:00Z host=n1 arm=kev-4b\n")
    with pytest.raises(L.Stop, match="this is a p4 attempt; it is not sealed with a probe spec"):
        L.seal(p4k, s, "kev-4b", tmp_path / "x_sealed")
    rk = L.seal(killed, s, "kev-4b", sealed)
    assert rk["charged_gpu_hours"] == 2.0 and rk["attempt"] == 2 and rk["kind"] == "probe"     # walltime_s, 7200 s
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    with pytest.raises(L.Stop, match="unknown-kind-confirmed"):
        L.seal(unknown, p4s, "kev-0.8b", tmp_path / "u_sealed")
    ru = L.seal(unknown, p4s, "kev-0.8b", tmp_path / "u_sealed", unknown_kind_confirmed=True)
    assert ru["charged_gpu_hours"] == 2.0 and ru["kind"] == "unknown (confirmed)"     # max(probe 2 h, arm 1.745 h)
    first = Path(receipts["kev-0.8b"]["sealed_path"]) / "job_record.json"
    assert L.check_first_probe_record(first, s, spec_sha, sealed)["first_probe_record_sha256"]
    with pytest.raises(L.Stop, match="alone first"):
        L.check_first_probe_record(None, s, spec_sha, sealed)
    with pytest.raises(L.Stop, match="spec_sha256"):
        L.check_first_probe_record(first, s, "0" * 64, sealed)
    p4 = copy.deepcopy(SPEC)                                                      # the P.4 spec the probe measures
    p4["caps"]["probe_gpu_hours"] = "TODO"
    dirs = [Path(receipts[a]["sealed_path"]) for a in s["arms"]]
    t1 = _t1(1800.0)                        # P4-T1CHARGE A: a synthetic T1 job of 0.5 h
    with pytest.raises(L.Stop, match="T1's RemoteWallClockTime is required"):
        L.probe_records(s, spec_sha, p4, dirs, sealed)
    table = L.probe_records(s, spec_sha, p4, dirs, sealed, t1_wallclock=t1)
    assert table["schema"] == L.PROBE_TABLE_SCHEMA and [e["arm"] for e in table["entries"]] == s["arms"]
    # minor 1: condor_history wall clocks, the larger per attempt; every sealed attempt needs its entry
    att = {f"{a}/{Path(receipts[a]['sealed_path']).name}": {"cluster_id": "7", "remote_wallclock_s": 900.0}
           for a in s["arms"]}
    att["kev-4b/attempt-2"] = {"cluster_id": "8", "remote_wallclock_s": 9000.0}
    wc = {"schema": L.WALLCLOCK_SCHEMA, "runs": {s["run_id"]: att}}
    t_wc = L.probe_records(s, spec_sha, p4, dirs, sealed, wallclock=wc, t1_wallclock=t1)
    want = round(sum(max(r["charged_gpu_hours"], 0.25) for r in receipts.values()) + 2.5 + 0.5, 4)   # T1 included
    assert t_wc["probe_gpu_hours_charged"] == want and t_wc["wallclock_input"] is True
    assert t_wc["t1_charged"] is True and t_wc["t1_gpu_hours"] == 0.5 == t_wc["probe_charges"]["t1_gpu_hours"]
    for bad, match in (({**wc, "schema": "x"}, "wall-clock input must be"),
                       ({**wc, "runs": {s["run_id"]: {k: v for k, v in att.items() if k != "kev-4b/attempt-2"}}},
                        "missing \\['kev-4b/attempt-2'\\]"),
                       ({**wc, "runs": {s["run_id"]: {**att, "kev-4b/attempt-9": {"remote_wallclock_s": 1}}}},
                        "extra"),
                       ({**wc, "runs": {**wc["runs"], "trackp-p4-probe-20991231-z": {}}}, "runs without sealed"),
                       ({**wc, "runs": {s["run_id"]: {**att, "kev-4b/attempt-2": {"remote_wallclock_s": -1}}}},
                        "RemoteWallClockTime")):
        with pytest.raises(L.Stop, match=match):
            L.probe_records(s, spec_sha, p4, dirs, sealed, wallclock=bad, t1_wallclock=t1)
    # M2: a recorded submission that is not sealed is priced at the walltime and blocks the record
    ledger = sealed / s["run_id"] / L.SUBMISSION_LEDGER
    ledger.write_text("".join(json.dumps({"arm": a, "kind": "probe"}) + "\n" for a in s["arms"]) +
                      json.dumps({"arm": "kev-4b", "kind": "probe"}) + "\n" + json.dumps({"arm": "kev-0.8b"}) + "\n")
    assert L.probe_charges(sealed)["pending"][0]["arm"] == "kev-0.8b"
    with pytest.raises(L.Stop, match="recorded but not sealed"):
        L.probe_records(s, spec_sha, p4, dirs, sealed, t1_wallclock=t1)
    ledger.unlink()
    # round 2, M1: probe-record writes the wall clocks it used once into the sealed tree; probe_charges applies them
    docs = t_wc["charge_file_docs"]
    assert set(docs) == {s["run_id"]} and docs[s["run_id"]]["attempts"]["kev-4b/attempt-2"]["charged_gpu_hours"] == 2.5
    assert docs[s["run_id"]]["t1_gpu_hours"] == 0.5 and docs[s["run_id"]]["t1"]["jobs"][0]["cluster_id"] == "760065"
    L.write_charge_files(docs, sealed)
    t_file = L.probe_records(s, spec_sha, p4, dirs, sealed)              # no input: the charge file applies, T1 too
    assert t_file["probe_gpu_hours_charged"] == want and t_file["charge_file_docs"] == {}
    assert t_file["probe_charges"]["unrecorded"] == [] and t_file["t1"]["source"] == f"{s['run_id']}/_wallclock.json"
    with pytest.raises(L.Stop, match="already has its charge file"):
        L.probe_records(s, spec_sha, p4, dirs, sealed, wallclock=wc)
    with pytest.raises(L.Stop, match="T1 is already charged"):          # T1 given again once a charge file holds it
        L.probe_records(s, spec_sha, p4, dirs, sealed, t1_wallclock=t1)
    charged = sum(r["charged_gpu_hours"] for r in receipts.values()) + 2.0 + 0.5
    assert table["probe_gpu_hours_charged"] == round(charged, 4)
    # the flag follows the hours; the receipts' wall time is real elapsed time, so on a fast run the total can be
    # exactly 2.0 h and the flag False (local/20261126-05 item 2; G5_PILOT_BASIS_HARNESS_REVIEW_20261126.md)
    assert table["p4_probe_gpu_hours"] == L.ceil_hundredth(charged)
    assert table["probe_over_2_gpu_h"] is (L.ceil_hundredth(charged) > 2.0)
    e0 = table["entries"][0]
    assert e0["estimate_hours"] == L.estimate_hours(e0["n_train"], e0["s_per_step_wall"], p4,
                                                    {"micro_batch": 8, "effective_batch": 16, "max_epochs": 5})["hours"]
    assert e0["labels"] == "synthetic" and e0["protocol_deviation"] == {"max_steps": 50} and e0["oom"] is False
    lines = table["lines"]
    assert lines[-1] == f"p4_probe_gpu_hours: {table['p4_probe_gpu_hours']:.2f}" and len(lines) == 5
    filled_p4 = copy.deepcopy(p4)                         # the lines bind the spec through the switch's checks
    filled_p4["estimate"]["hours"] = table["estimate_hours"]
    filled_p4["caps"]["probe_gpu_hours"] = table["p4_probe_gpu_hours"]
    text = "# record\n" + "\n".join(lines) + "\n"
    assert SW.check_probe_hours(text, filled_p4) and SW.check_probe_charge(text, filled_p4)
    assert table["projection"]["probe_gpu_hours"] == table["p4_probe_gpu_hours"]
    with pytest.raises(L.Stop, match="needs every arm"):
        L.probe_records(s, spec_sha, p4, dirs[:3], sealed)
    with pytest.raises(L.Stop, match="differ in"):
        other = copy.deepcopy(p4)
        other["layout"]["request_cpus"] = 4
        L.probe_records(s, spec_sha, other, dirs, sealed)
    with pytest.raises(L.Stop, match="STOP-free probe attempt of this probe spec"):
        L.probe_records(s, "0" * 64, p4, dirs, sealed)
    # S12: a probe charge that pushes the projection over 40 GPU-h is a STOP
    for n in range(3, 25):
        ledger_dir = sealed / s["run_id"] / "kev-4b" / f"attempt-{n}"
        ledger_dir.mkdir()
        (ledger_dir / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": 2.0, "stop": "STOP: x"}))
    with pytest.raises(L.Stop, match="exceeds P4-CAP|caps.probe_gpu_hours"):
        L.probe_records(s, spec_sha, p4, dirs, sealed)


def test_probe_charges_sum_every_probe_run_and_ignore_the_p4_run(tmp_path):
    root = tmp_path / "sealed"
    for run, arm, n, h in (("trackp-p4-probe-20261125-a", "kev-0.8b", 1, 0.2),
                           ("trackp-p4-probe-20261125-a", "kev-0.8b", 2, 2.0),
                           ("trackp-p4-probe-20261201-b", "kev-4b", 1, 0.3),
                           (L.P4_RUN_ID, "kev-0.8b", 1, 5.0), ("trackp-p4-probe-x", "kev-0.8b", 1, 9.0)):
        d = root / run / arm / f"attempt-{n}"
        d.mkdir(parents=True)
        (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": h, "stop": None}))
    got = L.probe_charges(root)
    assert got["total"] == 2.5 and sorted(got["runs"]) == ["trackp-p4-probe-20261125-a", "trackp-p4-probe-20261201-b"]


@pytest.fixture
def probe_stage_world(tmp_path, monkeypatch):
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
    spec_path = tmp_path / "probe_spec.json"
    spec_path.write_text(json.dumps(probe_filled()))
    return spec_path, table


def test_probe_stage_renders_one_base_with_no_label_transfer(probe_stage_world, tmp_path):
    """§4.2: the probe JDL keeps render()'s fixed lines and the layout request, with its own executable, arguments,
    transfer lists (no label file, no receipt) and +RequestWalltime 7200; kev-0.8b alone first."""
    spec_path, table = probe_stage_world
    kw = {"sealed_root": tmp_path / "sealed", "binding": lambda spec: {"desk": "stub"}}
    man = RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", **kw)
    jdl = (tmp_path / "st" / "p4probe_kev-0.8b.jdl").read_text()
    for line in ("universe = container", f"container_image = docker://{L.IMAGE_V22}", "executable = p4_probe.sh",
                 "arguments = p4_probe_spec.json kev-0.8b", "request_GPUs = 1", "request_cpus = 8",
                 "request_memory = 131072", "request_disk = 150000000", "+RequestWalltime = 7200",
                 "periodic_hold = (NumJobStarts > 1)", "transfer_input_files = " + ",".join(L.PROBE_TRANSFER_INPUTS),
                 "transfer_output_files = out.tar,job_record.json,SHA256SUMS,p4_run.log"):
        assert line in jdl.splitlines(), line
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA H200"' in jdl and "label_block" not in jdl and "RECEIPT" not in jdl
    assert sorted(p.name for p in (tmp_path / "st").iterdir()) == sorted(
        ["STAGE_MANIFEST.json", "p4probe_kev-0.8b.jdl", "p4_probe.sh", "p4_lib.py", "p4_probe_spec.json",
         "proposals.jsonl", "configs.json", "build.json"])
    assert man["mode"] == "probe" and man["spec_sha256"] == _sha(spec_path.read_bytes())
    assert man["binding"] == {"desk": "stub"} and "one condor_submit" in man["submit"]
    assert (tmp_path / "st" / "p4_lib.py").read_bytes() == (PKG / "p4_lib.py").read_bytes()
    # M2 of review round 1: staging records one submission, priced at the probe walltime until sealed
    s = json.loads(spec_path.read_text())
    ledger = tmp_path / "sealed" / s["run_id"] / L.SUBMISSION_LEDGER
    assert [json.loads(x)["arm"] for x in ledger.read_text().splitlines()] == ["kev-0.8b"]
    charges = L.probe_charges(tmp_path / "sealed")
    assert charges["total"] == 2.0 and charges["pending"][0]["arm"] == "kev-0.8b"
    with pytest.raises(L.Stop, match="alone first"):
        RJ.stage_probe(spec_path, tmp_path / "st2", table=table, arm="kev-4b", **kw)
    with pytest.raises(L.Stop, match="already has a probe submission that is not sealed"):   # round 4, M1
        RJ.stage_probe(spec_path, tmp_path / "st_again", table=table, arm="kev-0.8b", **kw)
    with pytest.raises(L.Stop, match="not empty"):
        RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", **kw)
    bad = probe_filled()
    bad["probe"]["walltime_s"] = 9000
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(L.Stop, match="probe must be"):
        RJ.stage_probe(tmp_path / "bad.json", tmp_path / "st3", table=table, arm="kev-0.8b", **kw)
    (table / "proposals.jsonl").write_bytes(b"other\n")
    with pytest.raises(L.Stop, match="sweep1_v3 pin"):
        RJ.stage_probe(spec_path, tmp_path / "st4", table=table, arm="kev-0.8b", **{**kw, "sealed_root": tmp_path / "b"})

    def refuse(spec):
        raise L.Stop("STOP: this checkout's p4_lib.py is not the one at paper.commit")
    with pytest.raises(L.Stop, match="not the one at paper.commit"):
        RJ.stage_probe(spec_path, tmp_path / "st6", table=table, arm="kev-0.8b", **{**kw, "binding": refuse})
    assert not (tmp_path / "st6").exists()
    assert len(ledger.read_text().splitlines()) == 1                      # a refused stage records no submission
    for argv in (["--probe", "--arm", "kev-0.8b", "--partition", str(tmp_path)], ["--probe"],
                 ["--probe", "--arm", "kev-0.8b", "--preview"], ["--arm", "kev-0.8b"]):
        assert RJ.main([str(spec_path), str(tmp_path / "st5"), "--table", str(table), *argv]) == 2


def test_probe_stage_of_another_base_needs_the_sealed_first_probe_record(probe_stage_world, tmp_path):
    spec_path, table = probe_stage_world
    s = json.loads(spec_path.read_text())
    sealed = tmp_path / "sealed"
    d = sealed / s["run_id"] / "kev-0.8b" / "attempt-1"
    d.mkdir(parents=True)

    def write(**over):
        rec = {"schema": L.PROBE_RECORD_SCHEMA, "run_id": s["run_id"], "arm": "kev-0.8b",
               "spec_sha256": _sha(spec_path.read_bytes()), "stop": None, "steps": ["identity", "probe"], **over}
        (d / "job_record.json").write_text(json.dumps(rec))
        (d / "SEAL_RECEIPT.json").write_text(json.dumps({"job_record_sha256": _sha((d / "job_record.json").read_bytes()),
                                                         "identity_verified": True}))
        (d / "SHA256SUMS").write_text(f"{_sha((d / 'job_record.json').read_bytes())}  job_record.json\n")
    write()
    man = RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-4b", first_record=d / "job_record.json",
                         sealed_root=sealed, binding=lambda spec: {})
    assert man["first_probe_record"]["first_probe_record_sha256"]
    for over, match in (({"stop": "STOP: OOM"}, "stop"), ({"schema": L.RECORD_SCHEMA}, "schema"),
                        ({"steps": ["identity", "data"]}, "stop")):
        write(**over)
        with pytest.raises(L.Stop, match=match):
            RJ.stage_probe(spec_path, tmp_path / f"st_{len(over)}_{match}", table=table, arm="kev-4b",
                           first_record=d / "job_record.json", sealed_root=sealed, binding=lambda spec: {})


# ============================================================================================ host-config fill (F7)
def _fill_values(**over) -> dict:
    vals = {p: FH.FIXED.get(p) for p in FH.EXPECTED}
    vals.update({"work_dir": ".", "gpu.lock_path": "gpu0.lock",
                 "venv.causal_conv1d": "1.7.0 built from source in image v2.2 (R1-TRACKP-IMAGE-V22-B; synthetic)"})
    vals.update({f"bases.{b}.local_path": f"models/{b}" for b in FH.UNUSED_BASES})
    vals.update(over)
    return {"schema": FH.SCHEMA, "values": vals}


def _placeholder_host_config(tmp_path) -> Path:
    """A copy of the host config with the 19 placeholders: the committed file itself before the fill commit, or the
    committed file with the 19 values put back to TODO_VERIFY_ON_HOST after it (so this test needs no change)."""
    cfg = _restore_placeholders(json.loads((ROOT / L.HOST_CONFIG).read_text()))
    out = tmp_path / "trackp_htcondor_v2.json"
    out.write_bytes(_layout(cfg))
    assert _sha(out.read_bytes()) == HOST_CONFIG_PLACEHOLDER_SHA256
    return out


def test_fill_hook_writes_exactly_the_19_values_and_prints_the_new_sha256(tmp_path):
    """F7 / T3: a synthetic filled copy: exactly 19 values change, --check-config's rule finds no placeholder, every P.4
    arm's local paths are the staged directories, and the printed sha256 is the file's (sha256sum)."""
    from r1.c3.train import run as R
    cfg_path = _placeholder_host_config(tmp_path)
    before = cfg_path.read_bytes()
    values = tmp_path / "host_fill.json"
    values.write_text(json.dumps(_fill_values()))
    dry = FH.fill(values, cfg_path, dry_run=True)
    assert cfg_path.read_bytes() == before and dry["written"] is False
    got = FH.fill(values, cfg_path)
    after = cfg_path.read_bytes()
    assert got["sha256"] == _sha(after) == dry["sha256"] and got["previous_sha256"] == _sha(before)
    assert got["filled"] == 19 and got["placeholders_left"] == [] and R.placeholders(json.loads(after)) == []
    changed = [a for a, b in zip(before.decode().splitlines(), after.decode().splitlines()) if a != b]
    assert len(changed) == 19 and len(before.splitlines()) == len(after.splitlines())
    assert got["local_paths"]["kev-0.8b"]["adapter_local_path"].endswith("/models/kev-0.8b")
    assert _host_config_state(json.loads(after)) == "filled"
    tampered = json.loads(after)                         # minor 3: a fill that also changes another key is caught
    tampered["lease"] = "other"
    with pytest.raises(AssertionError):
        _host_config_state(tampered)
    with pytest.raises(L.Stop, match="exactly the 19 known"):                 # already filled: no second fill
        FH.fill(values, cfg_path)
    assert FH.main(["--template"]) == 0


@pytest.mark.parametrize("edit, match", [
    (lambda v: v["values"].pop("work_dir"), "missing \\['work_dir'\\]"),                       # a partial fill
    (lambda v: v["values"].update({"gpu.extra": "x"}), "unknown \\['gpu.extra'\\]"),
    (lambda v: v["values"].update({"gpu.name": "NVIDIA L40S"}), "gpu.name must be 'NVIDIA H200'"),
    (lambda v: v["values"].update({"bases.kev-4b.local_path": "models/kev-4b"}), "must be 'models/qwen3.5-4b-base'"),
    (lambda v: v["values"].update({"hf_home": "/home/x/hf"}), "hf_home must be 'hf'"),
    (lambda v: v["values"].update({"bases.laya.local_path": "/abs/laya"}), "not a relative path"),
    (lambda v: v["values"].update({"gpu.lock_path": "../gpu0.lock"}), "not a relative path"),
    (lambda v: v["values"].update({"bases.startlux-2b.local_path": "FILL: x"}), "still a placeholder"),
    (lambda v: v["values"].update({"work_dir": "TODO_VERIFY_ON_HOST"}), "still a placeholder"),
    (lambda v: v["values"].update({"venv.causal_conv1d": "1.7.0 from somewhere"}), "R1-TRACKP-IMAGE-V22-B"),
    (lambda v: v["values"].update({"work_dir": ""}), "non-empty string"),
    (lambda v: v.update({"schema": "other"}), "trackp_p4_host_fill/1"),
])
def test_fill_hook_refuses_partial_unknown_or_invalid_values(tmp_path, edit, match):
    cfg_path = _placeholder_host_config(tmp_path)
    before = cfg_path.read_bytes()
    v = _fill_values()
    edit(v)
    values = tmp_path / "host_fill.json"
    values.write_text(json.dumps(v))
    with pytest.raises(L.Stop, match=match):
        FH.fill(values, cfg_path)
    assert cfg_path.read_bytes() == before                                    # nothing written
    assert FH.main([str(values), "--config", str(cfg_path)]) == 2


def test_fill_hook_refuses_a_config_with_another_placeholder_set(tmp_path):
    cfg_path = _placeholder_host_config(tmp_path)
    cfg = json.loads(cfg_path.read_text())
    cfg["work_dir"] = "."                                                     # partly filled by hand
    cfg_path.write_text(json.dumps(cfg, indent=1) + "\n")
    values = tmp_path / "host_fill.json"
    values.write_text(json.dumps(_fill_values()))
    with pytest.raises(L.Stop, match="missing \\['work_dir'\\]"):
        FH.fill(values, cfg_path)


# ============================================================================================ review round 1
def _probe_attempt(root: Path, arm: str, n: int, h: float, run="trackp-p4-probe-20261125-a") -> Path:
    d = root / run / arm / f"attempt-{n}"
    d.mkdir(parents=True)
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": h, "stop": None}))
    return d


T1_COMMITTED = ROOT / L.T1_RECORD_DIR          # the cluster's T1 record on main (merge 7556c1173)


def _make_t1_repo(root: Path, clusters=("760065",), history=None) -> Path:
    """A synthetic repository holding T1's pinned record: the committed (reviewed) versions.jdl and versions.sh, one
    condor_submit output per submission (versions.submit, versions.2.submit, ...) and optionally condor_history.txt.
    Rewrites the submit files and condor_history.txt of an existing one (no history given: none left)."""
    d = Path(root) / L.T1_RECORD_DIR
    d.mkdir(parents=True, exist_ok=True)
    for name in L.T1_RECORD_SHA256:
        shutil.copyfile(T1_COMMITTED / name, d / name)
    for old in d.glob("*.submit"):
        old.unlink()
    for k, c in enumerate(clusters):
        (d / ("versions.submit" if k == 0 else f"versions.{k + 1}.submit")).write_text(
            f"Submitting job(s).\n1 job(s) submitted to cluster {c}.\n")
    if history is not None:
        (d / L.T1_HISTORY).write_text(history)
    elif (d / L.T1_HISTORY).exists():
        (d / L.T1_HISTORY).unlink()
    return Path(root)


@pytest.fixture(autouse=True)
def t1_repo(tmp_path, monkeypatch):
    """Every test reads T1's pinned record from a synthetic repository (T1 job 760065 only), so that later cluster
    commits to the real record cannot change these tests; test_t1charge_the_committed_record_* reads the real one."""
    root = _make_t1_repo(tmp_path / "t1repo")
    monkeypatch.setattr(L, "T1_REPO_ROOT", root)
    return root


def _t1(seconds=0.0, clusters=("760065",), history=True) -> dict:
    """A T1 wall-clock input (trackp_p4_t1_wallclock/1) for the pinned record, one entry per ClusterId; ``seconds`` is
    one value for every job or a list. Synthetic values. With ``history`` (review round 2, r2-m2: the JSON must agree
    with a committed condor_history.txt) the matching condor_history.txt is written into the synthetic repository
    (never into the real checkout)."""
    secs = seconds if isinstance(seconds, (list, tuple)) else [seconds] * len(clusters)
    if history:
        assert L.T1_REPO_ROOT is not None, "_t1 writes condor_history.txt only into the synthetic repository"
        (Path(L.T1_REPO_ROOT) / L.T1_RECORD_DIR / L.T1_HISTORY).write_text(
            "".join(f"{c} 0 4 {float(v)}\n" for c, v in zip(clusters, secs)))
    return {"schema": L.T1_WALLCLOCK_SCHEMA, "jobs": [{"cluster_id": c, "remote_wallclock_s": v}
                                                      for c, v in zip(clusters, secs)]}


def _record_charges(root: Path, wallclock: dict | None = None, t1: float | None = 0.0, run=None) -> dict:
    """What probe-record does to the sealed tree: the wall clocks used, written once per run (round 2, M1), with T1's
    charge (P4-T1CHARGE A; a synthetic T1 job of ``t1`` seconds, 0 by default) in the record run's base file."""
    t1_in = _t1(t1) if t1 is not None else None
    charges = L.probe_charges(root, wallclock=wallclock, t1_wallclock=t1_in)
    return L.write_charge_files(L.charge_file_docs(charges, run or next(iter(charges["runs"]))), root)


def _wc(root: Path, seconds: dict) -> dict:
    """A wall-clock input: {run: {"<arm>/attempt-N": seconds or (seconds, cluster_id)}} -> the
    trackp_p4_condor_wallclock/1 form (cluster_id "1" when not given)."""
    def entry(v):
        s, c = v if isinstance(v, tuple) else (v, "1")
        return {"cluster_id": c, "remote_wallclock_s": s}
    return {"schema": L.WALLCLOCK_SCHEMA, "runs": {run: {k: entry(v) for k, v in att.items()}
                                                   for run, att in seconds.items()}}


def test_m1_the_sealed_probe_tree_must_not_charge_more_than_the_spec(tmp_path):
    """M1 (rounds 1 and 2): assemble and the switch's check_cap re-derive the probe charge from the sealed tree with the
    charge files probe-record wrote, and STOP on a probe attempt sealed after the record, a pending submission, or a
    spec value below the re-derived charge."""
    s = filled()                                                       # caps.probe_gpu_hours 0.5
    root, only_probe = tmp_path / "sealed", tmp_path / "probe_only"
    for r in (root, only_probe):
        _probe_attempt(r, "kev-0.8b", 1, 0.3)
        _probe_attempt(r, "kev-4b", 1, 0.2, run="trackp-p4-probe-20261126-b")
        _record_charges(r, _wc(r, {"trackp-p4-probe-20261125-a": {"kev-0.8b/attempt-1": 0.0},
                                   "trackp-p4-probe-20261126-b": {"kev-4b/attempt-1": 0.0}}))
    s["caps"]["probe_charge_files"] = L.spec_charge_files(L.charge_file_listing(root))
    assert s["caps"]["probe_charge_files"] == L.spec_charge_files(L.charge_file_listing(only_probe))
    dirs = [_sealed_attempt(root, s, arm, "f" * 64) for arm in s["arms"]]
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["probe_ledger"]["probe_gpu_hours_sealed_tree"] == 0.5 == asm["probe_ledger"]["probe_gpu_hours_spec"]
    assert SW.check_cap(s, ["kev-0.8b"], only_probe)["probe_ledger"]["probe_gpu_hours_sealed_tree"] == 0.5
    s_lo = copy.deepcopy(s)
    s_lo["caps"]["probe_gpu_hours"] = 0.49                             # a value typed lower
    with pytest.raises(L.Stop, match="more than caps.probe_gpu_hours 0.49"):
        SW.check_cap(s_lo, ["kev-0.8b"], only_probe)
    for r in (root, only_probe):                                       # sealed after the probe record
        _probe_attempt(r, "qwen3.5-4b-base", 1, 0.0001)
    with pytest.raises(L.Stop, match="sealed after the probe record"):
        L.assemble(dirs, s, "f" * 64, root)
    with pytest.raises(L.Stop, match="sealed after the probe record"):
        SW.check_cap(s, ["kev-0.8b"], only_probe)
    clean = tmp_path / "clean"
    _probe_attempt(clean, "kev-0.8b", 1, 0.3)
    _record_charges(clean, _wc(clean, {"trackp-p4-probe-20261125-a": {"kev-0.8b/attempt-1": 0.0}}))
    s["caps"]["probe_charge_files"] = L.spec_charge_files(L.charge_file_listing(clean))
    ledger = clean / "trackp-p4-probe-20261125-a" / L.SUBMISSION_LEDGER   # a staged probe not yet sealed
    ledger.write_text(json.dumps({"arm": "kev-0.8b"}) + "\n" + json.dumps({"arm": "kev-4b", "kind": "probe"}) + "\n")
    assert L.probe_charges(clean)["total"] == round(0.3 + 2.0, 4)
    with pytest.raises(L.Stop, match="recorded but not sealed"):
        SW.check_cap(s, ["kev-0.8b"], clean)


def test_r2_m1_the_reviewers_case_a_later_small_attempt_in_the_wallclock_gap(tmp_path):
    """Round 2, M1, exactly the reviewer's case: P = 0.60 from a 0.30 h receipt and a 0.60 h wall clock; a 0.25 h
    attempt sealed later re-derived from receipts alone would give 0.55 <= 0.60 and pass. With the charge file the
    re-derivation equals P for the recorded attempt and the later attempt is a STOP."""
    root = tmp_path / "sealed"
    run = "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.30)
    charges = L.probe_charges(root, wallclock=_wc(root, {run: {"kev-0.8b/attempt-1": 2160.0}}),
                              t1_wallclock=_t1(0.0))      # T1 required (P4-T1CHARGE A); 0 s here
    assert charges["total"] == 0.6
    files = L.write_charge_files(L.charge_file_docs(charges, run), root)
    assert files[run]["sha256"] == _sha((root / run / L.CHARGE_FILE).read_bytes())
    s = filled()
    s["caps"]["probe_gpu_hours"] = L.ceil_hundredth(charges["total"])   # P = 0.60, as the record gives it
    s["caps"]["probe_charge_files"] = {run: [files[run]["sha256"]]}
    got = L.check_probe_ledger(s, root)
    assert got["probe_gpu_hours_sealed_tree"] == 0.6 == got["probe_gpu_hours_spec"]
    assert L.probe_charges(root)["charge_files"][run][0]["sha256"] == files[run]["sha256"]
    _probe_attempt(root, "kev-0.8b", 2, 0.25)
    receipts_only = 0.30 + 0.25
    assert L.ceil_hundredth(receipts_only) <= 0.60                      # the gap the reviewer found
    assert L.probe_charges(root)["total"] == 0.85                       # the file applies; the new attempt >= receipt
    with pytest.raises(L.Stop, match="sealed after the probe record"):
        L.check_probe_ledger(s, root)
    with pytest.raises(FileExistsError):                                # written once
        L.write_charge_files(L.charge_file_docs(charges, run), root)
    with pytest.raises(L.Stop, match="already has its charge file"):    # the input may not re-time a recorded run
        L.probe_charges(root, wallclock=_wc(root, {run: {"kev-0.8b/attempt-1": 1.0, "kev-0.8b/attempt-2": 1.0}}))


def test_r2_m1_t1_is_kept_in_the_charge_file_and_never_counted_twice(tmp_path):
    root = tmp_path / "sealed"
    run = "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.30)
    _record_charges(root, _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}}), t1=1800.0, run=run)
    got = L.probe_charges(root)
    assert got["t1_gpu_hours"] == 0.5 and got["total"] == 0.8
    with pytest.raises(L.Stop, match="T1 is already charged"):
        L.probe_charges(root, t1_wallclock=_t1(60.0))
    (root / run / L.CHARGE_FILE).write_text(json.dumps({"schema": "other"}))
    with pytest.raises(L.Stop, match="is not charge file 0 \\(trackp_p4_probe_charges/1\\)"):
        L.probe_charges(root)


def test_r2_minors_unknown_kind_and_never_submitted_probe_stage(probe_stage_world, tmp_path):
    """Round 2, minor 1: an unknown kind with a readable record of neither schema is charged at least the larger
    walltime. Minor 2: a never-submitted probe stage directory is a probe attempt (its STAGE_MANIFEST.json), 2 h."""
    p4s = filled()
    odd = tmp_path / "odd"
    odd.mkdir()
    for h, want in ((0.01, 2.0), (5.0, 5.0)):
        (odd / "job_record.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "run_id": p4s["run_id"],
                                                         "arm": "kev-0.8b", "gpu_hours": h}))
        r = L.seal(odd, p4s, "kev-0.8b", tmp_path / f"s_{h}", unknown_kind_confirmed=True)
        assert r["charged_gpu_hours"] == want and r["kind"] == "unknown (confirmed)"
    spec_path, table = probe_stage_world
    s = json.loads(spec_path.read_text())
    sealed = tmp_path / "sealed"
    RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", sealed_root=sealed,
                   binding=lambda spec: {})
    assert L.attempt_kind(tmp_path / "st", None) == "probe" and L.probe_charges(sealed)["pending"]
    with pytest.raises(L.Stop, match="this is a probe attempt"):
        L.seal(tmp_path / "st", p4s, "kev-0.8b", tmp_path / "p4_sealed")
    r = L.seal(tmp_path / "st", s, "kev-0.8b", sealed)                   # never submitted: no confirmation needed
    assert r["kind"] == "probe" and r["charged_gpu_hours"] == 2.0 and r["record_readable"] is False
    assert not L.probe_charges(sealed)["pending"] and L.probe_charges(sealed)["total"] == 2.0


def test_r2_nits_ledger_failure_leaves_no_stage_and_git_timeouts_stop(probe_stage_world, tmp_path):
    spec_path, table = probe_stage_world
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")                                             # the sealed root cannot hold a ledger
    with pytest.raises(L.Stop, match="nothing staged and no submission recorded"):
        RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", sealed_root=blocker,
                       binding=lambda spec: {})
    assert not (tmp_path / "st").exists()

    def slow(repo, *args, **kw):
        raise subprocess.TimeoutExpired(["git", *args], 600)
    with pytest.raises(L.Stop, match="timed out"):
        RJ.check_probe_binding(probe_filled(), tmp_path, git=slow)


def test_minor5_the_probe_jdl_shares_renders_fixed_lines():
    """Minor 5: every line of render() that is not job-specific appears unchanged in render_probe()."""
    s, ps = filled(), probe_filled()
    s["image"]["digest"] = ps["image"]["digest"]
    own = ("#", "executable =", "arguments =", "log =", "output =", "error =", "+RequestWalltime =",
           "transfer_input_files =")
    fixed = [ln for ln in RJ.render(s, "kev-4b").splitlines() if not ln.startswith(own)]
    probe = RJ.render_probe(ps, "kev-4b").splitlines()
    assert fixed and all(ln in probe for ln in fixed)
    assert len([ln for ln in probe if not ln.startswith(own)]) == len(fixed)


def test_nit_probe_gpu_hours_given_exactly_once_in_the_note(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    for value in ("40 (P4-PROBECAP A: probe_gpu_hours: 0.50; probe_gpu_hours: 9.99); slot_hours_cap: 64",
                  "40 (P4-PROBECAP A: probe_gpu_hours: 9.99; probe_gpu_hours: 0.50); slot_hours_cap: 64"):
        with pytest.raises(SW.Stop, match="exactly once"):
            SW.check_binding(_note_fields(s, spec_sha, gpu_hours_cap=value), s, spec_sha)


def test_nit_probe_run_summary_checks_lr_seed_and_the_train_record(tmp_path):
    stage_s = tmp_path / "run" / "stage_s"
    stage_s.mkdir(parents=True)
    base = {"lr": 1e-05, "seed": 0, "protocol": {"micro_batch": 8, "effective_batch": 16},
            "protocol_deviation": {"max_steps": 50}, "data_sha256": "d",
            "train": {"stopped_at": 20, "completed": True, "early_stopped": True}}
    args = ({"sft_data_sha256": "d"}, {"prompt": {"max_tokens": 1024}}, dict(L.PROBE), {"wall_s": 40.0})
    (stage_s / "sft_report.json").write_text(json.dumps(base))
    assert L.probe_run_summary(tmp_path / "run", *args)["s_per_step_wall"] == 2.0
    for over, match in (({"lr": 1e-4}, "lr"), ({"seed": 1}, "seed"),
                        ({"train": {"stopped_at": 20, "early_stopped": True}}, "incomplete"),
                        ({"train": {"stopped_at": 20, "completed": False, "early_stopped": False}}, "incomplete"),
                        ({"train": {"stopped_at": 51, "completed": True, "early_stopped": False}}, "outside")):
        (stage_s / "sft_report.json").write_text(json.dumps({**base, **over}))
        with pytest.raises(L.ProtocolStop, match=match):
            L.probe_run_summary(tmp_path / "run", *args)


def test_nit_fill_hook_refuses_ambiguous_dotted_paths():
    with pytest.raises(L.Stop, match="ambiguous"):
        FH._paths({"a.b": {"c": 1}, "a": {"b.c": 2}})
    assert FH._paths({"a": {"b": 1}, "c": 2}) == {"a.b": ("a", "b"), "c": ("c",)}


def test_nit_the_job_binds_the_transferred_p4_probe_sh(probe_world, tmp_path):
    spec_path, calls, state = probe_world
    lib_dir = tmp_path / "transferred"
    lib_dir.mkdir()
    shutil.copy2(PKG / "p4_lib.py", lib_dir / "p4_lib.py")
    (lib_dir / "p4_probe.sh").write_text("#!/bin/bash\necho other\n")
    job = tmp_path / "job"
    job.mkdir()
    with pytest.raises(L.Stop, match="transferred p4_probe.sh is not the one at the paper commit"):
        L.run_probe(spec_path, "kev-0.8b", job, popen=_Sampler((1,)), environ={}, lib_file=lib_dir / "p4_lib.py")
    shutil.copy2(PKG / "p4_probe.sh", lib_dir / "p4_probe.sh")
    (tmp_path / "job2").mkdir()
    rec = L.run_probe(spec_path, "kev-0.8b", tmp_path / "job2", popen=_Sampler((1,)), environ={},
                      lib_file=lib_dir / "p4_lib.py")
    assert rec["stop"] is None and rec["code"]["p4_lib_sha256"] == _sha((PKG / "p4_lib.py").read_bytes())


def test_minor4_probe_stage_desk_binding_against_paper_commit_on_main(tmp_path):
    """Minor 4: before staging, origin/main fresh, paper.commit on it, the checkout's p4_lib.py, p4_probe.sh and probe
    template equal to paper.commit's, and host_config.sha256 equal to the host config at paper.commit."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    _git(work, "checkout", "-q", "-b", "main")
    for name in ("p4_lib.py", "p4_probe.sh", L.PROBE_SPEC_FILE):
        (work / L.PKG_REL).mkdir(parents=True, exist_ok=True)
        shutil.copy2(PKG / name, work / L.PKG_REL / name)
    (work / L.HOST_CONFIG).parent.mkdir(parents=True)
    (work / L.HOST_CONFIG).write_bytes(b'{"filled": true}\n')
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "fill")
    c = _git(work, "rev-parse", "HEAD")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    s = probe_filled()
    s["paper"]["commit"] = c
    s["host_config"]["sha256"] = _sha(b'{"filled": true}\n')
    got = RJ.check_probe_binding(s, work)
    assert got["paper_commit"] == c and got["origin_main"] == c
    with pytest.raises(L.Stop, match="host_config.sha256"):
        RJ.check_probe_binding({**s, "host_config": {**s["host_config"], "sha256": "5" * 64}}, work)
    (work / L.PKG_REL / "p4_lib.py").write_text("# changed after the fill commit\n")
    _git(work, "commit", "-qam", "later")
    later = _git(work, "rev-parse", "HEAD")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "fetch", "-q", "origin")
    with pytest.raises(L.Stop, match="p4_lib.py is not the one at paper.commit"):
        RJ.check_probe_binding({**s, "paper": {**s["paper"], "commit": later}}, work)
    _git(work, "checkout", "-q", "-b", "side", c)
    (work / "x").write_text("x")
    _git(work, "add", "x")
    _git(work, "commit", "-qm", "unpublished")
    with pytest.raises(L.Stop, match="not on published main"):
        RJ.check_probe_binding({**s, "paper": {**s["paper"], "commit": _git(work, "rev-parse", "HEAD")}}, work)
    _git(work, "update-ref", "refs/remotes/origin/main", c)                 # a stale local origin/main
    with pytest.raises(L.Stop, match="fetch published main"):
        RJ.check_probe_binding(s, work)


def test_r2_m1_probe_record_cli_writes_the_charge_file_once_and_binds_its_sha256(probe_world, tmp_path, monkeypatch,
                                                                               capsys):
    spec_path, calls, state = probe_world
    s = json.loads(spec_path.read_text())
    sealed = tmp_path / "sealed"
    monkeypatch.setattr(L, "SEALED_ROOT", sealed)
    dirs = []
    for arm in s["arms"]:
        _run_probe(spec_path, arm, tmp_path / f"job_{arm}")
        dirs.append(Path(L.seal(tmp_path / f"job_{arm}", s, arm, sealed)["sealed_path"]))
    p4_path = tmp_path / "p4_spec.json"
    p4 = copy.deepcopy(SPEC)
    p4["caps"]["probe_gpu_hours"] = "TODO"
    p4_path.write_text(json.dumps(p4))
    wc_path = tmp_path / "wallclock.json"
    wc_path.write_text(json.dumps(_wc(sealed, {s["run_id"]: {f"{d.parent.name}/{d.name}": 600.0 for d in dirs}})))
    t1_path = tmp_path / "t1_wallclock.json"
    t1_path.write_text(json.dumps(_t1(720.0)))          # P4-T1CHARGE A, synthetic 0.2 h
    out = tmp_path / "probe_records.json"
    argv = ["probe-record", str(spec_path), str(p4_path), *map(str, dirs), "--wallclock", str(wc_path),
            "--t1-wallclock", str(t1_path)]
    assert L.main([*argv, "--out", str(out)]) == 0
    table = json.loads(out.read_text())
    charge = sealed / s["run_id"] / L.CHARGE_FILE
    assert table["charge_files"][s["run_id"]][0]["sha256"] == _sha(charge.read_bytes())
    printed = capsys.readouterr().out.splitlines()
    assert "charge_file_docs" not in table and printed[-2].startswith("p4_probe_gpu_hours:")
    assert printed[-1].startswith(f"p4_probe_charge_file: {s['run_id']} _wallclock.json ")
    assert L.ceil_hundredth(L.probe_charges(sealed)["total"]) == table["p4_probe_gpu_hours"]   # launch re-derivation
    assert table["spec_probe_charge_files"] == {s["run_id"]: [_sha(charge.read_bytes())]}
    held = json.loads(charge.read_text())                                # P4-T1CHARGE A: T1 once, in the base file
    assert held["t1_gpu_hours"] == 0.2 == table["t1_gpu_hours"] and held["t1"]["cluster_check"] == "match"
    assert table["probe_gpu_hours_charged"] == round(sum(a["charged_gpu_hours"] for a in held["attempts"].values())
                                                     + 0.2, 4)
    assert f"p4_probe_charge_file: {s['run_id']} _wallclock.json {_sha(charge.read_bytes())}" in table["lines"]
    before = charge.read_bytes()
    assert L.main([*argv, "--out", str(tmp_path / "again.json")]) == 2                     # the file is written once
    assert charge.read_bytes() == before and not (tmp_path / "again.json").exists()


# ============================================================================================ review round 3
def test_r3_m1_reprobe_after_record_end_to_end(probe_world, probe_stage_world, tmp_path, monkeypatch, capsys, t1_repo):
    """R3-M1: (a) staging into a recorded probe run is refused; (b) an attempt that lands in it anyway (the reviewer's
    demonstration: sealed into the recorded run) blocks the launch, cannot be named in a new wall-clock input and is not
    accepted by probe-record, and is recovered by probe-charge (a write-once _wallclock.1.json naming exactly it) and a
    rebuilt probe record, whose P, charge-file lines and spec listing then pass the launch check."""
    spec_path, calls, state = probe_world
    s = json.loads(spec_path.read_text())
    run = s["run_id"]
    sealed = tmp_path / "sealed"
    monkeypatch.setattr(L, "SEALED_ROOT", sealed)
    dirs = []
    for k, arm in enumerate(s["arms"]):
        _run_probe(spec_path, arm, tmp_path / f"job_{arm}", cluster=100 + k)
        dirs.append(Path(L.seal(tmp_path / f"job_{arm}", s, arm, sealed)["sealed_path"]))
    p4_path = tmp_path / "p4_spec.json"
    p4 = copy.deepcopy(SPEC)
    p4["caps"]["probe_gpu_hours"] = "TODO"
    p4_path.write_text(json.dumps(p4))
    wc_path = tmp_path / "wallclock.json"
    cl = {f"{d.parent.name}/{d.name}": str(100 + k) for k, d in enumerate(dirs)}
    wc_path.write_text(json.dumps(_wc(sealed, {run: {f"{d.parent.name}/{d.name}": (600.0, cl[f"{d.parent.name}/{d.name}"])
                                                     for d in dirs}})))
    argv = ["probe-record", str(spec_path), str(p4_path), *map(str, dirs)]
    t1_path = tmp_path / "t1_wallclock.json"
    t1_path.write_text(json.dumps(_t1(360.0, history=False)))  # P4-T1CHARGE A, synthetic 0.1 h
    assert L.main([*argv, "--wallclock", str(wc_path), "--out", str(tmp_path / "r1.json")]) == 2   # T1 required
    assert not (sealed / run / L.CHARGE_FILE).exists() and not (tmp_path / "r1.json").exists()
    assert L.main([*argv, "--wallclock", str(wc_path), "--t1-history", "--out", str(tmp_path / "r1.json")]) == 2
    assert L.main([*argv, "--wallclock", str(wc_path), "--t1-wallclock", str(t1_path),   # r2-m2: no JSON-only route
                   "--out", str(tmp_path / "r1.json")]) == 2
    assert not (sealed / run / L.CHARGE_FILE).exists() and not (tmp_path / "r1.json").exists()
    _make_t1_repo(t1_repo, history="760065 0 4 360.0\n")              # review round 1, m2: built from condor_history
    assert L.main([*argv, "--wallclock", str(wc_path), "--t1-history", "--out", str(tmp_path / "r1.json")]) == 0
    first = json.loads((tmp_path / "r1.json").read_text())
    attempts = first["probe_charges"]["runs"][run]["attempts"]
    assert first["t1_gpu_hours"] == 0.1 and first["t1"]["wallclock_source"].endswith(L.T1_HISTORY) and \
        first["probe_gpu_hours_charged"] == round(sum(a["charged_gpu_hours"] for a in attempts) + 0.1, 4)
    spec1 = filled()
    spec1["caps"].update(probe_gpu_hours=first["p4_probe_gpu_hours"],
                         probe_charge_files=first["spec_probe_charge_files"])
    assert L.check_probe_ledger(spec1, sealed)["probe_gpu_hours_sealed_tree"] == first["p4_probe_gpu_hours"]
    # (a) a new stage into the recorded run is refused
    st_spec, table = probe_stage_world
    with pytest.raises(L.Stop, match="already recorded .* new run id"):
        RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", sealed_root=sealed,
                       binding=lambda sp: {})
    assert not (tmp_path / "st").exists()
    # (b) an attempt lands anyway (sealed by hand into the recorded run): a STOP-free kev-4b attempt-2
    _run_probe(spec_path, "kev-4b", tmp_path / "late", cluster=500)
    late = L.seal(tmp_path / "late", s, "kev-4b", sealed)
    with pytest.raises(L.Stop, match="sealed after the probe record"):
        L.check_probe_ledger(spec1, sealed)
    wc2 = tmp_path / "wc2.json"
    wc2.write_text(json.dumps(_wc(sealed, {run: {k: (600.0, c) for k, c in cl.items()} |
                                            {"kev-4b/attempt-2": (900.0, "500")}})))
    assert L.main([*argv, "--wallclock", str(wc2), "--out", str(tmp_path / "x.json")]) == 2     # names a recorded run
    empty = tmp_path / "empty_wc.json"
    empty.write_text(json.dumps(_wc(sealed, {})))
    assert L.main([*argv, "--wallclock", str(empty), "--out", str(tmp_path / "y.json")]) == 2   # unrecorded attempt
    # the recovery: probe-charge with exactly the unrecorded attempt
    wc3 = tmp_path / "wc3.json"
    for bad in ({run: {}}, {run: {"kev-4b/attempt-2": (900.0, "500"), "kev-4b/attempt-1": (1.0, "101")}},
                {"trackp-p4-probe-20991231-z": {"kev-4b/attempt-2": (900.0, "500")}},
                {run: {"kev-4b/attempt-2": (900.0, "501")}}):                       # round 5: another job's clock
        wc3.write_text(json.dumps(_wc(sealed, bad)))
        assert L.main(["probe-charge", run, "--wallclock", str(wc3)]) == 2
    wc3.write_text(json.dumps(_wc(sealed, {run: {"kev-4b/attempt-2": (9000.0, "500")}})))
    assert L.main(["probe-charge", run, "--wallclock", str(wc3)]) == 0
    sup = sealed / run / "_wallclock.1.json"
    doc = json.loads(sup.read_text())
    assert doc["supplement"] == 1 and set(doc["attempts"]) == {"kev-4b/attempt-2"}
    assert doc["attempts"]["kev-4b/attempt-2"]["charged_gpu_hours"] == 2.5
    assert L.main(["probe-charge", run, "--wallclock", str(wc3)]) == 2                       # nothing unrecorded now
    with pytest.raises(L.Stop, match="not the ones caps.probe_charge_files lists"):          # the old spec is stale
        L.check_probe_ledger(spec1, sealed)
    assert L.main([*argv, "--wallclock", str(empty), "--t1-wallclock", str(t1_path),           # T1 given twice
                   "--out", str(tmp_path / "r2x.json")]) == 2
    capsys.readouterr()
    assert L.main([*argv, "--wallclock", str(empty), "--out", str(tmp_path / "r2.json")]) == 0     # rebuilt record
    second = json.loads((tmp_path / "r2.json").read_text())
    assert second["t1_gpu_hours"] == 0.1 and second["t1"]["source"] == f"{run}/_wallclock.json"   # T1 once, from file
    want = L.ceil_hundredth(first["probe_gpu_hours_charged"] + 2.5)
    assert second["p4_probe_gpu_hours"] == want > first["p4_probe_gpu_hours"]
    assert second["spec_probe_charge_files"] == {run: [_sha((sealed / run / "_wallclock.json").read_bytes()),
                                                       _sha(sup.read_bytes())]}
    assert [e["attempt"] for e in second["entries"]] == ["attempt-1"] * 4                     # the first, never the late
    assert second["extra_stop_free_attempts"] == {"kev-4b": [{"attempt": "attempt-2", "cluster_id": 500}]}
    lines = capsys.readouterr().out.splitlines()
    assert f"p4_probe_charge_file: {run} _wallclock.1.json {_sha(sup.read_bytes())}" in lines
    spec2 = filled()
    spec2["caps"].update(probe_gpu_hours=second["p4_probe_gpu_hours"],
                         probe_charge_files=second["spec_probe_charge_files"])
    assert L.check_probe_ledger(spec2, sealed)["probe_gpu_hours_sealed_tree"] == want
    text = "\n".join(lines) + "\n"
    assert SW.check_probe_charge_files(text, spec2) == second["spec_probe_charge_files"]
    assert late["attempt"] == 2


def test_r3_m1_probe_charge_refusals(tmp_path):
    root = tmp_path / "sealed"
    run = "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    with pytest.raises(L.Stop, match="has no _wallclock.json"):
        L.supplement_charges(run, _wc(root, {run: {"kev-0.8b/attempt-1": 1.0}}), root)
    _record_charges(root, _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}}))
    with pytest.raises(L.Stop, match="no unrecorded attempt"):
        L.supplement_charges(run, _wc(root, {run: {}}), root)
    _probe_attempt(root, "kev-0.8b", 2, 0.2)
    (root / run / L.SUBMISSION_LEDGER).write_text("".join(json.dumps({"arm": "kev-0.8b"}) + "\n" for _ in range(3)))
    with pytest.raises(L.Stop, match="pending submission"):
        L.supplement_charges(run, _wc(root, {run: {"kev-0.8b/attempt-2": 1.0}}), root)
    (root / run / L.SUBMISSION_LEDGER).unlink()
    with pytest.raises(L.Stop, match="not a probe run id"):
        L.supplement_charges(L.P4_RUN_ID, _wc(root, {run: {}}), root)
    got = L.supplement_charges(run, _wc(root, {run: {"kev-0.8b/attempt-2": 1.0}}), root)
    assert got["supplement"] == 1 and L.probe_charges(root)["total"] == 0.5 and not L.probe_charges(root)["unrecorded"]


def test_r3_m1_charge_file_names_order_and_double_naming(tmp_path):
    root = tmp_path / "sealed"
    run = "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    _record_charges(root, _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}}))
    base = json.loads((root / run / L.CHARGE_FILE).read_text())
    (root / run / "_wallclock.2.json").write_text(json.dumps({**base, "supplement": 2}))
    with pytest.raises(L.Stop, match="without gaps"):
        L.probe_charges(root)
    (root / run / "_wallclock.2.json").unlink()
    (root / run / "_wallclock.1.json").write_text(json.dumps({**base, "supplement": 1}))   # carries T1: refused
    with pytest.raises(L.Stop, match="is not charge file 1"):
        L.probe_charges(root)
    (root / run / "_wallclock.1.json").write_text(json.dumps({**base, "supplement": 1, "t1_gpu_hours": None,
                                                               "t1": None}))              # names attempt-1 again
    with pytest.raises(L.Stop, match="named by two charge files"):
        L.probe_charges(root)
    (root / run / "_wallclock.1.json").unlink()
    (root / run / "_wallclock.old.json").write_text("{}")
    with pytest.raises(L.Stop, match="not a probe charge file name"):
        L.probe_charges(root)


def test_r3_minor1_a_changed_missing_or_unlisted_charge_file_stops_the_launch(tmp_path):
    """R3-m1: caps.probe_charge_files carries every charge file's sha256; check_probe_ledger (assemble, check_cap)
    refuses a zeroed (changed), deleted or added charge file."""
    s = filled()
    for name, mutate in (("zeroed", lambda r: (r / SYN_PROBE_RUN / "_wallclock.json").write_text(
                             json.dumps({**json.loads(SYN_CHARGE), "attempts": {"kev-0.8b/attempt-1": {
                                 "charged_gpu_hours": 0.0}}}))),
                         ("deleted", lambda r: (r / SYN_PROBE_RUN / "_wallclock.json").unlink()),
                         ("added", lambda r: _probe_tree(r / "x") and shutil.copytree(
                             r / "x" / SYN_PROBE_RUN, r / "trackp-p4-probe-20261126-b"))):
        root = _probe_tree(tmp_path / name)
        assert L.check_probe_ledger(s, root)["probe_gpu_hours_sealed_tree"] == 0.5
        mutate(root)
        with pytest.raises(L.Stop, match="changed, missing or unlisted"):
            L.check_probe_ledger(s, root)
        with pytest.raises(L.Stop, match="changed, missing or unlisted"):
            SW.check_cap(s, ["kev-0.8b"], root)
    with pytest.raises(L.Stop, match="probe_charge_files"):
        L.validate_spec({**filled(), "caps": {**filled()["caps"], "probe_charge_files": {"x": ["0" * 64]}}},
                        launch=True)
    with pytest.raises(L.Stop, match="probe_charge_files"):
        L.validate_spec({**filled(), "caps": {**filled()["caps"], "probe_charge_files": "TODO"}}, launch=True)


def test_r3_minor1_the_switch_binds_record_spec_and_note_charge_files(stage_world, monkeypatch, tmp_path):
    s, spec_path, stage, man, table, part = stage_world
    good = _probe_text(s)
    line = f"p4_probe_charge_file: {SYN_PROBE_RUN} _wallclock.json {SYN_CHARGE_SHA}"
    assert SW.check_probe_charge_files(good, s) == {SYN_PROBE_RUN: [SYN_CHARGE_SHA]}
    for text, match in ((good.replace(line + "\n", ""), "is not the probe record's"),
                        (good.replace(SYN_CHARGE_SHA, "0" * 64), "is not the probe record's"),
                        (good + line + "\n", "twice"),
                        (good + line.replace("_wallclock.json", "_wallclock.2.json") + "\n", "without gaps")):
        with pytest.raises(SW.Stop, match=match):
            SW.check_probe_charge_files(text, s)
    spec_sha = _sha((stage / "p4_spec.json").read_bytes())
    for value in (f"{SYN_PROBE_RUN} _wallclock.json", f"{SYN_PROBE_RUN} {SYN_CHARGE_SHA} {'1' * 64}",
                  f"other {SYN_CHARGE_SHA}"):
        with pytest.raises(SW.Stop, match="probe_charge_files"):
            SW.check_binding(_note_fields(s, spec_sha, probe_charge_files=value), s, spec_sha)


def test_r3_nits_stage_dir_symlink_and_cleanup_keeps_a_pre_existing_dir(probe_stage_world, tmp_path):
    spec_path, table = probe_stage_world
    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real")
    with pytest.raises(L.Stop, match="is a symlink"):
        RJ.stage_probe(spec_path, tmp_path / "link", table=table, arm="kev-0.8b", sealed_root=tmp_path / "s",
                       binding=lambda sp: {})
    pre = tmp_path / "pre"
    pre.mkdir()                                                         # an empty stage directory that existed before
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")
    with pytest.raises(L.Stop, match="nothing staged and no submission recorded"):
        RJ.stage_probe(spec_path, pre, table=table, arm="kev-0.8b", sealed_root=blocker, binding=lambda sp: {})
    assert pre.is_dir() and not any(pre.iterdir())                      # kept, emptied of this call's files only


def test_r3_nits_a_failing_cleanup_still_ends_as_a_stop(probe_stage_world, tmp_path, monkeypatch):
    spec_path, table = probe_stage_world
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")
    real_unlink = Path.unlink

    def refuse_unlink(self, *a, **k):
        if self.parent.name == "st":
            raise PermissionError(f"cannot remove {self}")
        return real_unlink(self, *a, **k)
    monkeypatch.setattr(Path, "unlink", refuse_unlink)
    with pytest.raises(L.Stop, match="cleanup failed too"):
        RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b", sealed_root=blocker,
                       binding=lambda sp: {})


# ============================================================================================ review round 4
def test_r4_m1_a_base_is_staged_again_only_after_a_stop(probe_stage_world, tmp_path):
    """R4-M1 (a), the two-stage case: while a stage of a base is pending, or once it has a sealed STOP-free attempt,
    staging that base again is refused (one probe run per base, P4-PROBE A); after a STOP it may be staged again."""
    spec_path, table = probe_stage_world
    s = json.loads(spec_path.read_text())
    sealed = tmp_path / "sealed"
    kw = {"table": table, "arm": "kev-0.8b", "sealed_root": sealed, "binding": lambda sp: {}}
    RJ.stage_probe(spec_path, tmp_path / "st1", **kw)
    with pytest.raises(L.Stop, match="not sealed; seal it before staging again"):
        RJ.stage_probe(spec_path, tmp_path / "st2", **kw)
    assert not (tmp_path / "st2").exists()
    assert len(L.read_ledger(sealed / s["run_id"] / L.SUBMISSION_LEDGER)) == 1
    r = L.seal(tmp_path / "st1", s, "kev-0.8b", sealed)                 # never ran: a STOP attempt, 2 h
    assert r["stop"].startswith("STOP")
    RJ.stage_probe(spec_path, tmp_path / "st3", **kw)                   # a repeat after a STOP
    d = sealed / s["run_id"] / "kev-0.8b" / "attempt-2"                 # its attempt sealed STOP-free
    d.mkdir()
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": 0.3, "stop": None}))
    with pytest.raises(L.Stop, match="already has a sealed STOP-free probe attempt"):
        RJ.stage_probe(spec_path, tmp_path / "st4", **kw)


def test_r4_m1_seal_order_cannot_change_which_attempt_the_record_uses(probe_world, tmp_path):
    """R4-M1 (b)-(d): two STOP-free probe runs of kev-0.8b (ClusterId 300 submitted after ClusterId 200). Whichever is
    sealed first, the record uses the one submitted first (200), refuses the other, and lists it as an extra."""
    spec_path, calls, state = probe_world
    s = json.loads(spec_path.read_text())
    spec_sha = _sha(spec_path.read_bytes())
    p4 = copy.deepcopy(SPEC)
    p4["caps"]["probe_gpu_hours"] = "TODO"
    jobs = {"late": ("kev-0.8b", 300), "early": ("kev-0.8b", 200), "k4": ("kev-4b", 201),
            "q08": ("qwen3.5-0.8b-base", 202), "q4": ("qwen3.5-4b-base", 203)}
    for name, (arm, cluster) in jobs.items():
        _run_probe(spec_path, arm, tmp_path / name, cluster=cluster)
    used = {}
    for label, seal_first in (("late_first", ("late", "early")), ("early_first", ("early", "late"))):
        sealed = tmp_path / label
        rec = {n: Path(L.seal(tmp_path / n, s, jobs[n][0], sealed)["sealed_path"]) for n in (*seal_first, "k4", "q08",
                                                                                              "q4")}
        others = [rec["k4"], rec["q08"], rec["q4"]]
        t1 = _t1(60.0)
        with pytest.raises(L.Stop, match="not the first STOP-free probe attempt of kev-0.8b by submission order"):
            L.probe_records(s, spec_sha, p4, [rec["late"], *others], sealed, t1_wallclock=t1)
        table = L.probe_records(s, spec_sha, p4, [rec["early"], *others], sealed, t1_wallclock=t1)
        e0 = next(e for e in table["entries"] if e["arm"] == "kev-0.8b")
        used[label] = (e0["attempt"], e0["condor_job"]["ClusterId"])
        assert table["extra_stop_free_attempts"] == {"kev-0.8b": [{"attempt": rec["late"].name, "cluster_id": 300}]}
    assert {c for _, c in used.values()} == {"200"}                      # the same job, whatever the seal order
    assert {a for a, _ in used.values()} == {"attempt-1", "attempt-2"}   # though its attempt number differs


def test_r4_m1_ledger_order_fallback_and_unorderable_attempts(tmp_path):
    arm_dir = tmp_path / "sealed" / "trackp-p4-probe-20261125-a" / "kev-0.8b"
    ledger = arm_dir.parent / L.SUBMISSION_LEDGER
    for n, src in ((1, tmp_path / "stage_b"), (2, tmp_path / "stage_a")):
        d = arm_dir / f"attempt-{n}"
        d.mkdir(parents=True)
        (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": 0.3, "stop": None,
                                                         "source_dir": str(src)}))
    with pytest.raises(L.Stop, match="cannot be ordered by submission"):
        L.submission_order(arm_dir, ledger)
    ledger.write_text(json.dumps({"arm": "kev-0.8b", "stage": str(tmp_path / "stage_a")}) + "\n" +
                      json.dumps({"arm": "kev-0.8b", "stage": str(tmp_path / "stage_b")}) + "\n")
    got = L.submission_order(arm_dir, ledger)
    assert got["first"] == "attempt-2" and got["basis"] == "ledger order"
    assert got["extra"] == [{"attempt": "attempt-1", "ledger_position": 1}]
    for n, (schedd, cluster) in ((1, ("a", 5)), (2, ("b", 4))):        # two schedds: ClusterIds not comparable
        (arm_dir / f"attempt-{n}" / "job_record.json").write_text(json.dumps(
            {"condor": {"ClusterId": str(cluster), "GlobalJobId": f"{schedd}#{cluster}.0#1"}}))
    assert L.submission_order(arm_dir, ledger)["basis"] == "ledger order"
    (arm_dir / "attempt-2" / "job_record.json").write_text(json.dumps(
        {"condor": {"ClusterId": "4", "GlobalJobId": "a#4.0#1"}}))
    got = L.submission_order(arm_dir, ledger)
    assert got["basis"] == "ClusterId" and got["first"] == "attempt-2"


def test_r4_nit_a_malformed_ledger_line_is_a_stop(tmp_path):
    root = tmp_path / "sealed"
    run_dir = root / "trackp-p4-probe-20261125-a"
    run_dir.mkdir(parents=True)
    for text in ('{"arm": "kev-0.8b"}\n{"arm": "kev', '["kev-0.8b"]\n', '{"stage": "x"}\n'):
        (run_dir / L.SUBMISSION_LEDGER).write_text(text)
        with pytest.raises(L.Stop, match="_submissions.jsonl:"):
            L.probe_charges(root)


# ============================================================================================ review round 5
def test_r5_minor1_wallclock_cluster_id_must_be_the_records(probe_world, tmp_path):
    """Round 5, minor 1: a wall clock whose cluster_id differs from (or omits) the record's condor.ClusterId is a STOP
    in probe_charges (input and charge files) and supplement_charges; a record without a ClusterId cannot be checked
    and is marked unverifiable."""
    spec_path, calls, state = probe_world
    s = json.loads(spec_path.read_text())
    run = s["run_id"]
    sealed = tmp_path / "sealed"
    _run_probe(spec_path, "kev-0.8b", tmp_path / "a", cluster=700)
    L.seal(tmp_path / "a", s, "kev-0.8b", sealed)
    _run_probe(spec_path, "kev-4b", tmp_path / "b")                     # no job ad: no ClusterId in its record
    L.seal(tmp_path / "b", s, "kev-4b", sealed)
    for c, match in (("701", "is not the record's ClusterId 700"), (None, "is not the record's ClusterId 700")):
        with pytest.raises(L.Stop, match=match):
            L.probe_charges(sealed, wallclock=_wc(sealed, {run: {"kev-0.8b/attempt-1": (60.0, c),
                                                                 "kev-4b/attempt-1": (60.0, "9")}}))
    good = _wc(sealed, {run: {"kev-0.8b/attempt-1": (60.0, "700"), "kev-4b/attempt-1": (60.0, "9")}})
    got = {a["arm"]: a["cluster_check"] for a in L.probe_charges(sealed, wallclock=good)["runs"][run]["attempts"]}
    assert got == {"kev-0.8b": "match", "kev-4b": "unverifiable (no ClusterId in the record)"}
    _record_charges(sealed, good, run=run)
    assert L.probe_charges(sealed)["total"] > 0                         # the written file passes the same check
    path = sealed / run / L.CHARGE_FILE
    doc = json.loads(path.read_text())
    doc["attempts"]["kev-0.8b/attempt-1"]["cluster_id"] = "999"         # a charge file edited to another job
    path.write_text(json.dumps(doc))
    with pytest.raises(L.Stop, match="_wallclock.json.*is not the record's ClusterId 700"):
        L.probe_charges(sealed)
    path.write_text(json.dumps({**doc, "attempts": {**doc["attempts"], "kev-0.8b/attempt-1": {
        **doc["attempts"]["kev-0.8b/attempt-1"], "cluster_id": "700"}}}))
    _run_probe(spec_path, "qwen3.5-0.8b-base", tmp_path / "c", cluster=702)
    L.seal(tmp_path / "c", s, "qwen3.5-0.8b-base", sealed)
    with pytest.raises(L.Stop, match="is not the record's ClusterId 702"):
        L.supplement_charges(run, _wc(sealed, {run: {"qwen3.5-0.8b-base/attempt-1": (60.0, "703")}}), sealed)
    assert L.supplement_charges(run, _wc(sealed, {run: {"qwen3.5-0.8b-base/attempt-1": (60.0, "702")}}),
                                sealed)["supplement"] == 1


def test_r5_minor2_a_clean_result_is_never_sealed_as_killed(tmp_path):
    """Round 5, minor 2: an unreadable or missing record with the wrapper's end line rc=0 is refused; a killed job (no
    end line, or a non-zero rc) is still sealed."""
    s, ps = filled(), probe_filled()
    for spec, head, end in ((ps, "P4 probe container job start", "P4 probe container job end"),
                            (s, "P4 container job start", "P4 container job end")):
        for blank in (None, ""):
            job = tmp_path / f"clean_{spec['run_id']}_{blank is None}"
            job.mkdir()
            if blank is not None:
                (job / "job_record.json").write_text(blank)
            (job / "out.tar").write_bytes(b"x" * 10)
            (job / "p4_run.log").write_text(f"{head} 2026-11-25T00:00:00Z host=n1 arm=kev-0.8b\n"
                                            f"{end} 2026-11-25T01:00:00Z rc=0\n")
            with pytest.raises(L.Stop, match="end with rc=0 but the job record is missing or unreadable"):
                L.seal(job, spec, "kev-0.8b", tmp_path / "sealed")
        for tail, n in (("", "killed"), (f"{end} 2026-11-25T01:00:00Z rc=2\n", "stopped")):
            job = tmp_path / f"{n}_{spec['run_id']}"
            job.mkdir()
            (job / "p4_run.log").write_text(f"{head} 2026-11-25T00:00:00Z host=n1 arm=kev-0.8b\n{tail}")
            assert L.seal(job, spec, "kev-0.8b", tmp_path / "sealed")["record_readable"] is False


def test_r5_minor3_clusterid_ordering_needs_a_named_schedd(tmp_path):
    arm_dir = tmp_path / "sealed" / "trackp-p4-probe-20261125-a" / "kev-0.8b"
    ledger = arm_dir.parent / L.SUBMISSION_LEDGER
    for n, (src, cluster) in ((1, (tmp_path / "stage_b", 5)), (2, (tmp_path / "stage_a", 9))):
        d = arm_dir / f"attempt-{n}"
        d.mkdir(parents=True)
        (d / "SEAL_RECEIPT.json").write_text(json.dumps({"charged_gpu_hours": 0.3, "stop": None,
                                                         "source_dir": str(src)}))
        (d / "job_record.json").write_text(json.dumps({"condor": {"ClusterId": str(cluster)}}))   # no GlobalJobId
    assert L._cluster({"condor": {"ClusterId": "5"}}) is None
    assert L._cluster({"condor": {"ClusterId": "5", "GlobalJobId": "#5.0#1"}}) is None
    assert L._cluster({"condor": {"ClusterId": "5", "GlobalJobId": "s#5.0#1"}}) == ("s", 5)
    with pytest.raises(L.Stop, match="cannot be ordered by submission"):
        L.submission_order(arm_dir, ledger)
    ledger.write_text(json.dumps({"arm": "kev-0.8b", "stage": str(tmp_path / "stage_a")}) + "\n" +
                      json.dumps({"arm": "kev-0.8b", "stage": str(tmp_path / "stage_b")}) + "\n")
    got = L.submission_order(arm_dir, ledger)
    assert got["basis"] == "ledger order" and got["first"] == "attempt-2"      # not ClusterId 5 < 9


# ============================================================================================ P4-T1CHARGE A (26 Nov)
def test_t1charge_the_committed_record_is_the_pinned_one(monkeypatch):
    """R1-P4-PROBE-CHARGE, P4-T1CHARGE A; review round 1, M1 points 1-2: the real checkout's pinned record (resolved
    against the repository root, not the cwd) holds the reviewed versions.jdl / versions.sh and names 760065. The wall
    clock is synthetic: T1 has not run, and no condor_history output is committed."""
    monkeypatch.setattr(L, "T1_REPO_ROOT", None)
    monkeypatch.chdir("/")                                             # the cwd plays no part
    rec = L.t1_record()
    assert L._t1_repo() == ROOT and rec["dir"] == L.T1_RECORD_DIR and "760065" in rec["cluster_ids"]
    assert L.T1_RECORD_SHA256 == {"versions.jdl": "fa7ec821ca1fd597184691117f0f846df139c0a40df32db4afb2553d2d33c97d",
                                  "versions.sh": "125342d1cfed4fd435d68bbc0c5e7655845318d7522c7c9bd64536e1b3432025"}
    assert rec["submit_files"]["versions.submit"]
    with pytest.raises(L.Stop, match="not the ClusterIds of T1's committed record"):
        L.t1_charge(_t1(300.0, clusters=("760066",), history=False))
    if rec["history"] is None:                                         # r2-m2: no JSON-only route without the file
        with pytest.raises(L.Stop, match="needs the committed .*condor_history.txt"):
            L.t1_charge(_t1(300.0, clusters=tuple(rec["cluster_ids"]), history=False))   # synthetic seconds


def test_t1charge_m1_the_record_is_pinned_by_path_bytes_submit_and_760065(t1_repo):
    """Review round 1, M1 points 2-4: altered job files, no submit output (no 'unverifiable' any more), a record without
    760065, a record_dir other than the pinned one, and a T1 submit file in another T1_versions* folder are STOPs."""
    d = t1_repo / L.T1_RECORD_DIR
    assert L.t1_record()["cluster_ids"] == ["760065"]
    (d / "versions.sh").write_text("#!/bin/bash\nexit 0\n")             # (M1 c) arbitrary bytes
    with pytest.raises(L.Stop, match="versions.sh is not T1's reviewed file"):
        L.t1_record()
    shutil.copyfile(T1_COMMITTED / "versions.sh", d / "versions.sh")
    (d / "versions.submit").unlink()                                   # (M1 b) no submit output
    with pytest.raises(L.Stop, match="does not name its first job 760065"):
        L.t1_charge(_t1(60.0))
    _make_t1_repo(t1_repo, clusters=("760100",))                       # a record without 760065
    with pytest.raises(L.Stop, match="does not name its first job 760065"):
        L.t1_record()
    _make_t1_repo(t1_repo)
    with pytest.raises(L.Stop, match="T1 wall-clock input must be"):
        L.t1_charge({**_t1(60.0), "record_dir": "docs/r1/reports/trackp_p4_cluster_20261127/T1_versions"})
    other = t1_repo / "docs/r1/reports/trackp_p4_cluster_20261127/T1_versions"   # (M1 a) a resubmission elsewhere
    other.mkdir(parents=True)
    (other / "versions.submit").write_text("1 job(s) submitted to cluster 760200.\n")
    with pytest.raises(L.Stop, match="outside the pinned folder"):
        L.t1_charge(_t1(60.0, clusters=("760200",)))
    (other / "versions.submit").rename(other / "notes.txt")             # r2-m1: its text still records a submission
    with pytest.raises(L.Stop, match="outside the pinned folder"):
        L.t1_charge(_t1(60.0))
    (other / "notes.txt").write_text("T1 notes, no condor_submit output\n")   # no submit record there: not a T1 record
    assert L.t1_charge(_t1(60.0))["cluster_check"] == "match"
    for text, match in (("2 job(s) submitted to cluster 760065.\n", "one job per submission"),
                        ("ERROR: submit failed\n", "holds no condor_submit line")):
        (d / "versions.submit").write_text(text)
        with pytest.raises(L.Stop, match=match):
            L.t1_record()


def test_t1charge_required_charged_once_in_the_base_file_and_rederived_equal_to_p(tmp_path, t1_repo):
    """The charge is required and every T1 job is charged (a resubmission inside the pinned folder: both charged); it
    is stored once, in the record run's base charge file, never in a supplement; the launch check re-derives exactly P
    with it, and STOPs when no charge file holds T1 or when T1's value does not follow from its jobs."""
    _make_t1_repo(t1_repo, clusters=("760065", "760100"))
    root, run = tmp_path / "sealed", "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    t1 = _t1([600.0, 1200.0], clusters=("760065", "760100"))
    charges = L.probe_charges(root, wallclock=_wc(root, {run: {"kev-0.8b/attempt-1": 0.0}}), t1_wallclock=t1)
    assert charges["t1_gpu_hours"] == round(0.1667 + 0.3333, 4) == 0.5 and charges["total"] == 0.8
    assert [j["cluster_id"] for j in charges["t1"]["jobs"]] == ["760065", "760100"]
    docs = L.charge_file_docs(charges, run)
    assert docs[run]["t1_gpu_hours"] == 0.5 and docs[run]["supplement"] == 0
    files = L.write_charge_files(docs, root)
    s = filled()
    s["caps"].update(probe_gpu_hours=L.ceil_hundredth(charges["total"]), probe_charge_files={run: [files[run]["sha256"]]})
    got = L.check_probe_ledger(s, root)
    assert got["probe_gpu_hours_sealed_tree"] == 0.8 == got["probe_gpu_hours_spec"]
    assert L.probe_charges(root)["t1"]["source"] == f"{run}/_wallclock.json"
    _probe_attempt(root, "kev-4b", 1, 0.2)                             # a supplement never carries T1
    L.supplement_charges(run, _wc(root, {run: {"kev-4b/attempt-1": 0.0}}), root)
    assert json.loads((root / run / "_wallclock.1.json").read_text())["t1"] is None
    assert L.probe_charges(root)["total"] == 1.0
    bare = tmp_path / "bare"                                           # no charge file holds T1
    _probe_attempt(bare, "kev-0.8b", 1, 0.3)
    _record_charges(bare, _wc(bare, {run: {"kev-0.8b/attempt-1": 0.0}}), t1=None)
    s_bare = filled()
    s_bare["caps"].update(probe_gpu_hours=0.3, probe_charge_files=L.spec_charge_files(L.charge_file_listing(bare)))
    with pytest.raises(L.Stop, match="no probe charge file holds T1's charge"):
        L.check_probe_ledger(s_bare, bare)
    path = root / run / L.CHARGE_FILE
    path.write_text(json.dumps({**json.loads(path.read_text()), "t1_gpu_hours": 0.0}))
    with pytest.raises(L.Stop, match="T1's charge does not follow from its jobs"):
        L.probe_charges(root)
    path.write_text(json.dumps({**json.loads(path.read_text()), "t1_gpu_hours": None}))
    with pytest.raises(L.Stop, match="T1's charge does not follow from its jobs"):
        L.probe_charges(root)


def test_t1charge_m1_point5_a_t1_job_submitted_after_the_record_stops_the_launch(tmp_path, t1_repo):
    """Review round 1, M1 point 5 and m1: check_probe_ledger (assemble, check_cap) and a rebuilt record read the pinned
    record again; a T1 ClusterId the stored charge does not hold is a STOP (the chat decides)."""
    root, run = tmp_path / "sealed", "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    _record_charges(root, _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}}), t1=360.0, run=run)
    s = filled()
    s["caps"].update(probe_gpu_hours=0.4, probe_charge_files=L.spec_charge_files(L.charge_file_listing(root)))
    assert L.check_probe_ledger(s, root)["t1"]["t1_record_cluster_ids"] == ["760065"]
    _make_t1_repo(t1_repo, clusters=("760065", "760300"))              # T1 resubmitted after the record
    for check in (lambda: L.check_probe_ledger(s, root), lambda: SW.check_cap(s, ["kev-0.8b"], root)):
        with pytest.raises(L.Stop, match=r"does not hold: \['760300'\].*the chat decides"):
            check()
    with pytest.raises(L.Stop, match="does not hold"):
        L.check_t1_record_charged(L.probe_charges(root)["t1"])


def test_t1charge_m2_condor_history_builds_and_checks_the_entry(tmp_path, t1_repo):
    """Review round 1, m2: T1_versions/condor_history.txt (condor_history <C> -af ClusterId ProcId JobStatus
    RemoteWallClockTime, the -af form of htcondor_prep_20261114/probes/parse_queue_times.py) builds T1's entry
    (--t1-history) or must agree with the JSON input; its sha256 is held in the base charge file; it must name exactly
    the submitted jobs, ProcId 0, JobStatus 3 or 4; a changed file stops the launch."""
    root, run = tmp_path / "sealed", "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    wc = _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}})
    with pytest.raises(L.Stop, match="--t1-history needs"):
        L.probe_charges(root, wallclock=wc, t1_wallclock=L.T1_FROM_HISTORY)
    hist = "760065 0 4 723.0\n"
    _make_t1_repo(t1_repo, history=hist)
    got = L.probe_charges(root, wallclock=wc, t1_wallclock=L.T1_FROM_HISTORY)
    assert got["t1_gpu_hours"] == round(723 / 3600, 4) and got["t1"]["wallclock_source"].endswith("condor_history.txt")
    assert got["t1"]["record"]["history"]["sha256"] == _sha(hist.encode())
    assert L.probe_charges(root, wallclock=wc, t1_wallclock=_t1(723.0))["t1_gpu_hours"] == got["t1_gpu_hours"]
    with pytest.raises(L.Stop, match="disagrees with"):
        L.probe_charges(root, wallclock=wc, t1_wallclock=_t1(60.0, history=False))
    for text, match in (("760065 0 2 723.0\n", "JobStatus 3 or 4"), ("760065 1 4 723.0\n", "ProcId 0"),
                        ("760065 0 4\n", "expected 'ClusterId ProcId"), ("760065 0 4 abc\n", "not a number"),
                        ("760065 0 4 1.0\n760065 0 4 1.0\n", "twice"),
                        ("760065 0 4 1.0\n760099 0 3 1.0\n", "extra \\['760099'\\]"), ("\n", "missing")):
        (t1_repo / L.T1_RECORD_DIR / L.T1_HISTORY).write_text(text)
        with pytest.raises(L.Stop, match=match):
            L.probe_charges(root, wallclock=wc, t1_wallclock=L.T1_FROM_HISTORY)
    (t1_repo / L.T1_RECORD_DIR / L.T1_HISTORY).write_text(hist)
    docs = L.charge_file_docs(L.probe_charges(root, wallclock=wc, t1_wallclock=L.T1_FROM_HISTORY), run)
    assert docs[run]["t1"]["record"]["history"]["sha256"] == _sha(hist.encode())
    L.write_charge_files(docs, root)
    s = filled()
    s["caps"].update(probe_gpu_hours=0.51, probe_charge_files=L.spec_charge_files(L.charge_file_listing(root)))
    assert L.check_probe_ledger(s, root)["probe_gpu_hours_sealed_tree"] == L.ceil_hundredth(0.3 + 723 / 3600)
    (t1_repo / L.T1_RECORD_DIR / L.T1_HISTORY).write_text("760065 0 4 724.0\n")
    with pytest.raises(L.Stop, match="changed since the probe record"):
        L.check_probe_ledger(s, root)


def test_t1charge_r2_m1_a_t1_submission_anywhere_but_the_top_level_submit_files_stops(t1_repo):
    """Review round 2, r2-m1, the reviewer's three cases: a resubmission recorded as T1_versions/rerun/versions.submit,
    as T1_versions/versions.2.submit.txt, or in a lower-case t1_versions/ folder elsewhere under docs/ was uncharged;
    each is now a STOP. The pinned folder is searched recursively for any other *.submit file or any file containing
    "submitted to cluster"; stray folders match in any letter case, _to_delete included (r2-n1: by design)."""
    d = t1_repo / L.T1_RECORD_DIR
    assert L.t1_record()["cluster_ids"] == ["760065"]
    (d / "rerun").mkdir()
    (d / "rerun" / "versions.submit").write_text("1 job(s) submitted to cluster 760400.\n")     # case 1
    with pytest.raises(L.Stop, match=r"outside its top-level versions\*\.submit files: .*rerun/versions\.submit"):
        L.t1_record()
    (d / "rerun" / "versions.submit").rename(d / "rerun" / "notes.txt")                          # its text still counts
    with pytest.raises(L.Stop, match=r"rerun/notes\.txt"):
        L.t1_charge(_t1(60.0))
    shutil.rmtree(d / "rerun")
    (d / "versions.2.submit.txt").write_text("Submitting job(s).\n1 job(s) submitted to cluster 760401.\n")  # case 2
    with pytest.raises(L.Stop, match=r"versions\.2\.submit\.txt"):
        L.t1_charge(_t1(60.0))
    (d / "versions.2.submit.txt").unlink()
    (d / "rerun.submit").write_text("ERROR\n")                       # a *.submit not named versions*.submit
    with pytest.raises(L.Stop, match=r"rerun\.submit"):
        L.t1_record()
    (d / "rerun.submit").unlink()
    assert L.t1_charge(_t1(60.0))["cluster_check"] == "match"
    for rel in ("docs/r1/reports/trackp_p4_cluster_20261127/t1_versions",                       # case 3
                "docs/r1/reports/trackp_p4_cluster_20261127/T1_VERSIONS_rerun/sub",
                "docs/r1/reports/_to_delete/T1_versions"):                                       # r2-n1: by design
        other = t1_repo / rel
        other.mkdir(parents=True)
        (other / "versions.submit").write_text("1 job(s) submitted to cluster 760402.\n")
        with pytest.raises(L.Stop, match="outside the pinned folder"):
            L.t1_charge(_t1(60.0))
        (other / "versions.submit").rename(other / "versions.submit.txt")                       # not named *.submit
        with pytest.raises(L.Stop, match="outside the pinned folder"):
            L.t1_record()
        shutil.rmtree(t1_repo / "/".join(rel.split("/")[:4]))
    assert L.t1_record()["cluster_ids"] == ["760065"]


def test_t1charge_r2_m2_the_json_route_needs_condor_history_and_the_launch_compares_it(tmp_path, t1_repo):
    """Review round 2, r2-m2, the reviewer's case: 0 s recorded from the JSON input alone, then a condor_history.txt
    giving 3500 s committed later, passed the launch. Now the JSON input is refused without the committed
    condor_history.txt, and the launch check compares every stored wall clock with the file: a lower stored value, a
    job the charge does not hold, or a missing file is a STOP, also for a charge stored without the file's sha256."""
    root, run = tmp_path / "sealed", "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    wc = _wc(root, {run: {"kev-0.8b/attempt-1": 0.0}})
    with pytest.raises(L.Stop, match="needs the committed .*condor_history.txt"):              # 0 s, JSON only
        L.probe_charges(root, wallclock=wc, t1_wallclock=_t1(0.0, history=False))
    _record_charges(root, wc, t1=0.0, run=run)                         # 0 s, agreeing with condor_history.txt
    path, hist = root / run / L.CHARGE_FILE, t1_repo / L.T1_RECORD_DIR / L.T1_HISTORY
    s = filled()
    s["caps"].update(probe_gpu_hours=0.3, probe_charge_files=L.spec_charge_files(L.charge_file_listing(root)))
    assert L.check_probe_ledger(s, root)["t1"]["t1_record_cluster_ids"] == ["760065"]
    hist.write_text("760065 0 4 3500.0\n")                            # 3500 s committed later
    for check in (lambda: L.check_probe_ledger(s, root), lambda: SW.check_cap(s, ["kev-0.8b"], root)):
        with pytest.raises(L.Stop, match="changed since the probe record"):
            check()
    doc = json.loads(path.read_text())                                 # a charge stored without the file's sha256
    doc["t1"]["record"]["history"] = None
    path.write_text(json.dumps(doc))
    s["caps"]["probe_charge_files"] = L.spec_charge_files(L.charge_file_listing(root))
    with pytest.raises(L.Stop, match=r"stored wall clock below condor_history's for \['760065'\]"):
        L.check_probe_ledger(s, root)
    with pytest.raises(L.Stop, match=r"below condor_history's for \['760065'\]"):
        L.check_t1_record_charged({"jobs": [{"cluster_id": "760065", "remote_wallclock_s": 0.0}]})
    hist.unlink()                                                      # no condor_history.txt behind the charge
    with pytest.raises(L.Stop, match="condor_history.txt is missing"):
        L.check_probe_ledger(s, root)
    hist.write_text("760065 0 4 0.0\n")                               # equal: passes
    assert L.check_probe_ledger(s, root)["probe_gpu_hours_sealed_tree"] == 0.3
    assert L.check_t1_record_charged({"jobs": [{"cluster_id": "760065", "remote_wallclock_s": 0.0}]})
    with pytest.raises(L.Stop, match="does not hold"):
        L.check_t1_record_charged({"jobs": []})
    with pytest.raises(L.Stop, match="stored T1 charge, job 760065: RemoteWallClockTime must be"):
        L.check_t1_record_charged({"jobs": [{"cluster_id": "760065", "remote_wallclock_s": None}]})


def test_t1charge_missing_twice_and_clusterid_refusals(tmp_path, t1_repo):
    """A missing T1, T1 given twice (in the input, again after a charge file holds it, in two charge files, or as a
    probe attempt's job), and a ClusterId that is not the pinned record's are each a STOP."""
    root, run = tmp_path / "sealed", "trackp-p4-probe-20261125-a"
    _probe_attempt(root, "kev-0.8b", 1, 0.3)
    wc = _wc(root, {run: {"kev-0.8b/attempt-1": (0.0, "500")}})
    ok = _t1(60.0)
    assert L.probe_charges(root, wallclock=wc, t1_wallclock=ok)["t1"]["cluster_check"] == "match"
    assert L.probe_charges(root, wallclock=wc)["t1"] is None                       # probe_records/ledger then STOP
    for t1, match in (
            ({**ok, "schema": "x"}, "T1 wall-clock input must be"),
            ({**ok, "jobs": []}, "T1 wall-clock input must be"),
            ({**ok, "jobs": ok["jobs"] * 2}, "given twice"),
            (_t1(1.0, clusters=("9003",), history=False), "not the ClusterIds of T1's committed"),
            (_t1(1.0, clusters=("760065", "9004"), history=False), "extra \\['9004'\\]"),
            (_t1(1.0, clusters=("x9001",), history=False), "cluster_id must be"),
            ({**ok, "jobs": [{"cluster_id": True, "remote_wallclock_s": 1.0}]}, "cluster_id must be"),
            (_t1(-1, clusters=("760065",), history=False), "RemoteWallClockTime")):
        with pytest.raises(L.Stop, match=match):
            L.probe_charges(root, wallclock=wc, t1_wallclock=t1)
    _make_t1_repo(t1_repo, clusters=("760065", "500"))
    with pytest.raises(L.Stop, match="charged as T1 and as a probe attempt"):
        L.probe_charges(root, wallclock=wc, t1_wallclock=_t1(60.0, clusters=("760065", "500")))
    _make_t1_repo(t1_repo, clusters=("760065", "760100"))               # a resubmission: every T1 job is charged
    with pytest.raises(L.Stop, match="missing \\['760100'\\]"):
        L.probe_charges(root, wallclock=wc, t1_wallclock=ok)
    both = L.probe_charges(root, wallclock=wc, t1_wallclock=_t1([360.0, 720.0], clusters=("760065", "760100")))
    assert both["t1_gpu_hours"] == 0.3
    _make_t1_repo(t1_repo)
    _record_charges(root, wc, t1=60.0, run=run)                         # T1 given again once the base file holds it
    with pytest.raises(L.Stop, match="T1 is already charged"):
        L.probe_charges(root, t1_wallclock=ok)
    other = root / "trackp-p4-probe-20261201-b"                         # T1 in two charge files
    shutil.copytree(root / run, other)
    doc = json.loads((other / L.CHARGE_FILE).read_text())
    (other / L.CHARGE_FILE).write_text(json.dumps({**doc, "run_id": other.name}))
    with pytest.raises(L.Stop, match="more than one charge file"):
        L.probe_charges(root)
    legacy = tmp_path / "legacy"                                        # the record's run already has a base file
    _probe_attempt(legacy, "kev-0.8b", 1, 0.3)
    _record_charges(legacy, _wc(legacy, {run: {"kev-0.8b/attempt-1": 0.0}}), t1=None)
    with pytest.raises(L.Stop, match="already has one; T1 is never put in a supplement"):
        L.charge_file_docs(L.probe_charges(legacy, t1_wallclock=ok), run)


def test_t1charge_the_note_must_say_t1_is_included(tmp_path):
    """The note's gpu_hours_cap: must cite P4-T1CHARGE A (the switch), and the draft's line does."""
    s = filled()
    f = _note_fields(s, "a" * 64)
    SW.check_binding(f, s, "a" * 64)
    with pytest.raises(SW.Stop, match="P4-T1CHARGE A"):
        SW.check_binding({**f, "gpu_hours_cap": f["gpu_hours_cap"].replace(", T1 included, P4-T1CHARGE A", "")},
                         s, "a" * 64)
    line = next(x for x in NOTE_DRAFT.read_text().splitlines() if x.startswith("gpu_hours_cap:"))
    assert "P4-T1CHARGE A" in line and "T1" in line.replace("P4-T1CHARGE", "")


def test_n4_assemble_compares_the_staged_tokenizer_files():
    """Review round 1, n4: comparable() carries each staged tokenizer file's sha256, so the four P.4 jobs must have
    staged the same tokenizer bytes."""
    base = {"configs": {"host_config": {}, "sft_config": {}}, "inputs": {"labels": {}}, "env3_freeze": {},
            "staging": {"tokenizers": {"pool": {"x": {"files": {"tokenizer.json": {"size": 1, "sha256": "a" * 64}}}}}}}
    other = copy.deepcopy(base)
    other["staging"]["tokenizers"]["pool"]["x"]["files"]["tokenizer.json"]["sha256"] = "b" * 64
    assert L.comparable(base)["tokenizers"] == {"x": {"tokenizer.json": "a" * 64}}
    assert L.comparable(base) != L.comparable(other)
