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
    return s


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
    assert L._placeholder(SPEC["estimate"]["source"]) == (L.probe_gpu_hours(SPEC) is None)   # filled together
    if open_ or probe_open:
        with pytest.raises(L.Stop, match=open_[0] if open_ else "estimate.source|probe_gpu_hours"):
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
        return _res(0, "6")
    got = L.stage(filled(), "kev-0.8b", clone, job, sh)
    assert set(got["weights"]) == {"kev-0.8b/adapter.safetensors", "qwen3.5-0.8b-base/model.safetensors"}
    assert len(hub_calls) == 1 and hub_calls[0][1] == str(job / "hf") and got["tokenizers"] == "6"
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
    assert asm["gpu_hours_consumed"] == 8.5 and asm["gpu_hours_probe"] == 0.5        # P4-PROBECAP A: 4 x 2.0 + 0.5
    assert asm["data_identity"] == {"sha256": "i" * 64}
    with pytest.raises(L.Stop, match="needs every arm"):
        L.assemble(dirs[:3], s, "f" * 64, root)
    root_b = tmp_path / "b"
    dirs_b = [_sealed_attempt(root_b, s, arm, "f" * 64, **({"data": {"identity": {"sha256": "e" * 64}}}
                                                           if arm == "kev-4b" else {})) for arm in s["arms"]]
    with pytest.raises(L.Stop, match=r"differ in \['data'\]"):
        L.assemble(dirs_b, s, "f" * 64, root_b)
    big_root = tmp_path / "c"
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
    root = tmp_path / "sealed"
    dirs = [_sealed_attempt(root, s, arm, "f" * 64, n=2) for arm in s["arms"]]
    _sealed_attempt(root, s, "kev-4b", "f" * 64, n=1, stop="STOP: late", gpu_hours=7.0)
    asm = L.assemble(dirs, s, "f" * 64, root)
    assert asm["gpu_hours_consumed"] == 15.5 and len(asm["gpu_hours_by_attempt"]) == 5     # 15.0 + the probe's 0.5
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
    # review m2: a record that is not UTF-8 is unreadable, not a refusal: the attempt is sealed and charged the walltime
    jobu = tmp_path / "not_utf8"
    jobu.mkdir()
    (jobu / "job_record.json").write_bytes(b'{"label": "ENGINEERING_ONLY", "stop": "\x97"}')
    assert L._read_record(jobu / "job_record.json") is None
    ru = L.seal(jobu, s, "kev-0.8b", tmp_path / "s_u")
    assert ru["record_readable"] is False and ru["identity_verified"] is False and ru["stop"].startswith("STOP")
    assert ru["charged_gpu_hours"] == round(L.arm_walltime_s(s, "kev-0.8b") / 3600, 4)
    assert (tmp_path / "s_u" / s["run_id"] / "kev-0.8b" / "attempt-1" / "job_record.json").read_bytes() == \
        (jobu / "job_record.json").read_bytes()
    # a STOP at identity (no H200 / image in the record) is sealed, unverified, at its own hours
    job2 = tmp_path / "noid"
    job2.mkdir()
    (job2 / "job_record.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "run_id": s["run_id"],
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
         "gpu_hours_cap": f"40 (P4-CAP A; P4-PROBECAP A: probe_gpu_hours: {s['caps']['probe_gpu_hours']:.2f} GPU-h); "
                          "slot_hours_cap: 64",
         "label_table_binding": f"P4-F2 A: {L.SEALED_V2_PROPOSALS_SHA256} to {L.V3_PROPOSALS_SHA256} by "
                                f"{L.FEAT_ONE_IDENTITY['path']} sha256 {L.FEAT_ONE_IDENTITY['sha256']}",
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
        + f"p4_probe_gpu_hours: {s['caps']['probe_gpu_hours']:.2f}\n"


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
    no_probe = copy.deepcopy(s)
    no_probe["caps"]["probe_gpu_hours"] = "TODO"
    assert SW.check_cap(no_probe, ["kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base"], tmp_path / "sealed")
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
             "gpu_hours_cap": "40 (P4-CAP A; P4-PROBECAP A: probe_gpu_hours: 0.50 GPU-h; projection 16.94 GPU-h); "
                              "slot_hours_cap: 64"}
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


def _host_config_state(host: dict) -> str:
    """F5: "placeholders" (exactly the 19 known TODO_VERIFY_ON_HOST values) or "filled" (none, and every one of the 19
    values valid under the fill hook's rules); anything else fails."""
    from r1.c3.train import run as R
    left = R.placeholders(host)
    if left:
        assert set(left) == FH.EXPECTED and len(left) == 19, left
        return "placeholders"
    keys = FH._paths(host)
    for path in FH.EXPECTED:
        FH.check_value(path, _spec_value(host, keys[path]))
    return "filled"


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


def _run_probe(spec_path, arm, job, samples=(1000, 52000, 51000), env=None):
    job.mkdir(parents=True)
    sampler = _Sampler(samples)
    try:
        return L.run_probe(spec_path, arm, job, popen=sampler,
                           environ=env if env is not None else {"CUDA_VISIBLE_DEVICES": "GPU-1"}), sampler
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
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "p4_run.log"):
        (killed / name).write_text("")
    rk = L.seal(killed, s, "kev-4b", sealed)
    assert rk["charged_gpu_hours"] == 2.0 and rk["attempt"] == 2                  # the probe's walltime_s, 7200 s
    first = Path(receipts["kev-0.8b"]["sealed_path"]) / "job_record.json"
    assert L.check_first_probe_record(first, s, spec_sha, sealed)["first_probe_record_sha256"]
    with pytest.raises(L.Stop, match="alone first"):
        L.check_first_probe_record(None, s, spec_sha, sealed)
    with pytest.raises(L.Stop, match="spec_sha256"):
        L.check_first_probe_record(first, s, "0" * 64, sealed)
    p4 = copy.deepcopy(SPEC)                                                      # the P.4 spec the probe measures
    p4["caps"]["probe_gpu_hours"] = "TODO"
    dirs = [Path(receipts[a]["sealed_path"]) for a in s["arms"]]
    table = L.probe_records(s, spec_sha, p4, dirs, sealed)
    assert table["schema"] == L.PROBE_TABLE_SCHEMA and [e["arm"] for e in table["entries"]] == s["arms"]
    charged = sum(r["charged_gpu_hours"] for r in receipts.values()) + 2.0
    assert table["probe_gpu_hours_charged"] == round(charged, 4)
    assert table["p4_probe_gpu_hours"] == L.ceil_hundredth(charged) and table["probe_over_2_gpu_h"] is True
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
    man = RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b")
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
    assert (tmp_path / "st" / "p4_lib.py").read_bytes() == (PKG / "p4_lib.py").read_bytes()
    with pytest.raises(L.Stop, match="alone first"):
        RJ.stage_probe(spec_path, tmp_path / "st2", table=table, arm="kev-4b")
    with pytest.raises(L.Stop, match="not empty"):
        RJ.stage_probe(spec_path, tmp_path / "st", table=table, arm="kev-0.8b")
    bad = probe_filled()
    bad["probe"]["walltime_s"] = 9000
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(L.Stop, match="probe must be"):
        RJ.stage_probe(tmp_path / "bad.json", tmp_path / "st3", table=table, arm="kev-0.8b")
    (table / "proposals.jsonl").write_bytes(b"other\n")
    with pytest.raises(L.Stop, match="sweep1_v3 pin"):
        RJ.stage_probe(spec_path, tmp_path / "st4", table=table, arm="kev-0.8b")
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
                         sealed_root=sealed)
    assert man["first_probe_record"]["first_probe_record_sha256"]
    for over, match in (({"stop": "STOP: OOM"}, "stop"), ({"schema": L.RECORD_SCHEMA}, "schema"),
                        ({"steps": ["identity", "data"]}, "stop")):
        write(**over)
        with pytest.raises(L.Stop, match=match):
            RJ.stage_probe(spec_path, tmp_path / f"st_{len(over)}_{match}", table=table, arm="kev-4b",
                           first_record=d / "job_record.json", sealed_root=sealed)


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
    from r1.c3.train import run as R
    cfg = json.loads((ROOT / L.HOST_CONFIG).read_text())
    if not R.placeholders(cfg):
        keys = FH._paths(cfg)
        for path in FH.EXPECTED:
            *parent, leaf = keys[path]
            _spec_value(cfg, parent)[leaf] = "TODO_VERIFY_ON_HOST"
    out = tmp_path / "trackp_htcondor_v2.json"
    out.write_text(json.dumps(cfg, indent=1, ensure_ascii=True) + "\n")
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
