"""Track P P.4 test evaluator (r1/c3/train/sft_test_eval.py): the primary test number of R1-TRACKP-SFT-DUP.

CPU only, synthetic sweep (the fixtures of test_trackp_sft.py); the real-label path uses a synthetic label block in
the audit format with evaluation files beside it, which must never be opened.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from r1.c3.train import sft_data as SD  # noqa: E402
from r1.c3.train import sft_test_eval as TE  # noqa: E402
from r1.c3.train import tiny  # noqa: E402
from test_trackp_sft import (TOKS, _control_plane_skip, _label_block, _prompts, opened,  # noqa: E402,F401
                             sweep)


def _table(sweep, tmp_path: Path) -> tuple[Path, dict]:
    d = tmp_path / "table"
    d.mkdir()
    (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sweep["rows"]))
    _, files = SD.load_table(d)
    return d, files


def _build(sweep, tmp_path, source, *, policy=None, name="data"):
    table_dir, files = _table(sweep, tmp_path) if not (tmp_path / "table").exists() else \
        (tmp_path / "table", SD.load_table(tmp_path / "table")[1])
    cfg = {} if policy is None else {"cross_split_duplicates": policy}
    out = tmp_path / name
    SD.build_sft_data(sweep["rows"], source, _prompts(sweep), out, split_cfg=cfg,
                      table_record={"path": str(table_dir), "sha256": files})
    return out, table_dir


def _labelled_test(data_dir, sweep, source):
    data = TE.read_data_dir(data_dir)
    return TE.heldout_populations(sweep["rows"], data["splits"], source.label_records()), data


def _write_predictions(path, data, probs: dict, **over):
    doc = {"schema": TE.PREDICTIONS_SCHEMA, "sft_data_sha256": data["manifest_sha256"], "arm": "test",
           "model": {}, "temperature": 1.0, "predictions": {k: [float(x) for x in v] for k, v in probs.items()}}
    doc.update(over)
    path.write_text(json.dumps(doc))
    return path


def _oracle(pops, sweep, source):
    by_id = {r["proposal_id"]: r for r in sweep["rows"]}
    rec = {r["proposal_id"]: r for r in source.label_records()}
    return {p: SD.soft_target(rec[p], by_id[p]) for p in pops["secondary"]}


# ---------------------------------------------------------------------------------------------- populations

def test_primary_population_applies_the_exclusion_list(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    listed = set(data["splits"]["test_proposals_seen_in_train_or_val"])
    assert listed, "the synthetic sweep must have cross-split duplicates for this test to mean anything"
    assert set(pops["excluded"]) == listed
    assert set(pops["primary"]) == set(pops["secondary"]) - listed and set(pops["primary"]) < set(pops["secondary"])
    test_insts = set(data["splits"]["instances"]["test"])
    by_id = {r["proposal_id"]: r for r in sweep["rows"]}
    assert all(by_id[p]["instance"] in test_insts for p in pops["secondary"])
    m = data["manifest"]["counts"]
    assert pops["counts"]["labelled_test"] == m["labelled_test_proposals"]
    assert pops["counts"]["labelled_test_seen_in_train_or_val"] == m["labelled_test_seen_in_train_or_val"]
    assert pops["counts"]["test_rows_seen_in_train_or_val"] == m["test_rows_seen_in_train_or_val"]


@pytest.mark.parametrize("tamper, match", [
    (lambda sp: sp["test_proposals_seen_in_train_or_val"].pop(), "exclusion list differs"),
    (lambda sp: sp["test_proposals_seen_in_train_or_val"].append("x"), "exclusion list differs"),
    (lambda sp: sp.update(test_proposals_seen_in_train_or_val=None), "exclusion list differs"),
    (lambda sp: sp["instances"]["train"].append(sp["instances"]["test"][0]), "two splits"),
    (lambda sp: sp["instances"]["test"].pop(), "outside the recorded split"),
])
def test_exclusion_list_is_recomputed(sweep, tmp_path, tamper, match):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    splits = json.loads((data_dir / "splits.json").read_text())
    tamper(splits)
    with pytest.raises(TE.TestEvalError, match=match):
        TE.heldout_populations(sweep["rows"], splits, src.label_records())


def test_a_test_key_seen_only_on_an_unlabelled_train_row_is_still_excluded(sweep, tmp_path):
    """'Seen' uses every table row of a train or val instance, labelled or not (as the builder)."""
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    data = TE.read_data_dir(data_dir)
    split = {i: s for s in ("train", "val", "test") for i in data["splits"]["instances"][s]}
    dup_rows = [r for r in sweep["rows"] if r["duplicate"] and split[r["instance"]] in ("train", "val")]
    keys = {SD.dup_key(r) for r in dup_rows}
    hit = [r["proposal_id"] for r in sweep["rows"] if split[r["instance"]] == "test" and SD.dup_key(r) in keys]
    assert set(hit) <= set(data["splits"]["test_proposals_seen_in_train_or_val"])


# ---------------------------------------------------------------------------------------------- evaluation

def test_evaluate_oracle_and_base_rate_predictions(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"], shift_z=1.0)
    data_dir, table_dir = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    oracle = _oracle(pops, sweep, src)
    rep = TE.evaluate_test(data_dir, table_dir, src, _write_predictions(tmp_path / "o.json", data, oracle),
                           tmp_path / "rep_o", suite_of={"digits_mlp": "T0"})
    p, s = rep["metrics_primary"], rep["metrics_secondary"]
    assert p["test_n"] == len(pops["primary"]) and s["test_full_n"] == len(pops["secondary"])
    assert p["test_rps"] == pytest.approx(0.0, abs=1e-12) and s["test_full_rps"] == pytest.approx(0.0, abs=1e-12)
    assert p["test_rps_skill"] == pytest.approx(1.0) and rep["headline"] == "primary"
    assert rep["populations"]["exclusion_list_matches_recomputation"] is True
    assert rep["evaluation_seeds_read"] is False and rep["label_seeds"] == [7001, 7002, 7003, 7004, 7005]
    assert rep["by_suite"]["T0"]["test_n"] == len(pops["primary"])
    assert rep["by_suite"]["T0"]["test_full_n"] == len(pops["secondary"])
    assert rep["by_node"]["digits_mlp"]["test_rps"] == pytest.approx(0.0, abs=1e-12)
    assert "ENGINEERING_ONLY" in rep["label_status"] and rep["data"]["cross_split_duplicates"] == "heldout_excludes_seen"
    on_disk = json.loads((tmp_path / "rep_o" / "test_report.json").read_text())
    assert on_disk["populations"]["primary_ids_sha256"] == TE._ids_sha(pops["primary"])
    # the training base rate as the forecast: skill 0 on both populations
    base = {k: data["base"] for k in oracle}
    rep = TE.evaluate_test(data_dir, table_dir, src, _write_predictions(tmp_path / "b.json", data, base),
                           tmp_path / "rep_b")
    assert rep["metrics_primary"]["test_rps_skill"] == pytest.approx(0.0, abs=1e-12)
    assert rep["metrics_secondary"]["test_full_rps_skill"] == pytest.approx(0.0, abs=1e-12)
    assert rep["by_suite"]["unassigned"]["test_n"] == len(pops["primary"])


def test_primary_and_secondary_differ_exactly_by_the_excluded_proposals(sweep, tmp_path):
    """Perfect predictions on the excluded proposals, uniform elsewhere: the primary RPS is the uniform RPS of the
    unseen proposals; the secondary mixes in the zeros."""
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, table_dir = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    oracle = _oracle(pops, sweep, src)
    excl = set(pops["excluded"])
    preds = {k: (v if k in excl else np.full(TE.N_BINS, 1.0 / TE.N_BINS)) for k, v in oracle.items()}
    rep = TE.evaluate_test(data_dir, table_dir, src, _write_predictions(tmp_path / "p.json", data, preds),
                           tmp_path / "rep")
    from r1.c3.train import metrics as M
    u = np.full((len(pops["primary"]), TE.N_BINS), 1.0 / TE.N_BINS)
    y = np.stack([oracle[k] for k in pops["primary"]])
    assert rep["metrics_primary"]["test_rps"] == pytest.approx(M.mean_rps(u, y))
    n_p, n_s = len(pops["primary"]), len(pops["secondary"])
    assert rep["metrics_secondary"]["test_full_rps"] == pytest.approx(M.mean_rps(u, y) * n_p / n_s)


@pytest.mark.parametrize("edit, match", [
    (lambda preds, d: preds.popitem(), "exactly the labelled test proposals"),
    (lambda preds, d: preds.update({"not_a_test_id": [1 / 12] * 12}), "exactly the labelled test proposals"),
    (lambda preds, d: preds.update({next(iter(preds)): [0.5] * 12}), "probability vector"),
    (lambda preds, d: preds.update({next(iter(preds)): [1.0] + [0.0] * 10}), "probability vector"),
    (lambda preds, d: preds.update({next(iter(preds)): [float("nan")] * 12}), "probability vector"),
    (lambda preds, d: preds.update({next(iter(preds)): [-0.1, 1.1] + [0.0] * 10}), "probability vector"),
    (lambda preds, d: d.update(sft_data_sha256="0" * 64), "another data directory"),
    (lambda preds, d: d.update(schema="x"), "schema"),
])
def test_prediction_refusals(sweep, tmp_path, edit, match):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, table_dir = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    preds = {k: [float(x) for x in v] for k, v in _oracle(pops, sweep, src).items()}
    header = {}
    edit(preds, header)
    path = _write_predictions(tmp_path / "p.json", data, preds, **header)
    with pytest.raises(TE.TestEvalError, match=match):
        TE.evaluate_test(data_dir, table_dir, src, path, tmp_path / "rep")
    assert not (tmp_path / "rep" / "test_report.json").exists()


def test_bindings_and_one_read(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, table_dir = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    path = _write_predictions(tmp_path / "p.json", data, _oracle(pops, sweep, src))
    # another synthetic seed is another label source
    with pytest.raises(TE.TestEvalError, match="seed"):
        TE.evaluate_test(data_dir, table_dir, SD.SyntheticLabelSource(sweep["rows"], seed=1), path, tmp_path / "r1")
    TE.evaluate_test(data_dir, table_dir, src, path, tmp_path / "r2")
    with pytest.raises(TE.TestEvalError, match="one test read per arm"):
        TE.evaluate_test(data_dir, table_dir, src, path, tmp_path / "r2")
    # a changed table
    rows = (table_dir / "proposals.jsonl").read_text().splitlines()
    (table_dir / "proposals.jsonl").write_text("\n".join(rows[:-1]) + "\n")
    with pytest.raises(SD.SFTDataError, match="pinned"):
        TE.evaluate_test(data_dir, table_dir, src, path, tmp_path / "r3")
    # a changed splits.json
    sp = data_dir / "splits.json"
    sp.write_text(sp.read_text().replace('"test"', '"test" ', 1))
    with pytest.raises(TE.TestEvalError, match="sha256"):
        TE.read_data_dir(data_dir)


def test_data_without_a_table_hash_or_exclusion_list_is_refused(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    out = tmp_path / "nopin"
    SD.build_sft_data(sweep["rows"], src, _prompts(sweep), out)
    table_dir, _ = _table(sweep, tmp_path)
    pops, data = _labelled_test(out, sweep, src)
    path = _write_predictions(tmp_path / "p.json", data, _oracle(pops, sweep, src))
    with pytest.raises(TE.TestEvalError, match="no table hash"):
        TE.evaluate_test(out, table_dir, src, path, tmp_path / "rep")
    old, _ = _build(sweep, tmp_path, src, policy="drop_from_train", name="old")
    with pytest.raises(TE.TestEvalError, match="no exclusion list"):
        TE.read_data_dir(old)


def test_real_label_block_path_never_opens_evaluation_seed_files(sweep, tmp_path, opened):
    audit = tmp_path / "audit"
    block = _label_block(sweep, audit)
    src = SD.LabelBlockSource(block)
    data_dir, table_dir = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep, src)
    path = _write_predictions(tmp_path / "p.json", data, _oracle(pops, sweep, src))
    opened.clear()
    rep = TE.evaluate_test(data_dir, table_dir, SD.LabelBlockSource(block), path, tmp_path / "rep")
    assert rep["labels"]["kind"] == "label_block" and rep["metrics_primary"]["test_rps"] == pytest.approx(0.0, abs=1e-12)
    names = {Path(p).name for p in opened}
    assert "label_block.jsonl" in names
    assert not names & {"evaluation_block.jsonl", "runs.jsonl"}
    # a label block whose bytes differ from the one the data was built on
    other = _label_block(sweep, tmp_path / "audit2", mutate=lambda labels: labels[-1].update(
        delta_label=labels[-1]["delta_label"] + 1e-6,
        soft_parameters={**labels[-1]["soft_parameters"], "delta_label": labels[-1]["delta_label"] + 1e-6})
        if labels[-1]["label_kind"] == "audit" else None)
    with pytest.raises(TE.TestEvalError, match="sha256"):
        TE.evaluate_test(data_dir, table_dir, SD.LabelBlockSource(other), path, tmp_path / "rep2")
    with pytest.raises(SD.SFTDataError, match="evaluation"):
        TE.read_predictions(audit / "evaluation_block.jsonl", data, pops["secondary"])


def test_predict_test_writes_a_bound_predictions_file(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, table_dir = _build(sweep, tmp_path, src)
    prompts = TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=data_dir,
                                     table_rows=sweep["rows"], label_source=src)
    pops, _ = _labelled_test(data_dir, sweep, src)
    assert sorted(prompts) == pops["secondary"]
    model = tiny.build_hashbag(seed=0)
    out = tmp_path / "preds.json"
    doc = TE.predict_test(model, prompts, 1.3, data_dir, out, arm="hashbag", model_record={"seed": 0})
    assert doc["temperature"] == 1.3 and set(doc["predictions"]) == set(pops["secondary"])
    rep = TE.evaluate_test(data_dir, table_dir, src, out, tmp_path / "rep")
    assert rep["predictions"]["arm"] == "hashbag" and np.isfinite(rep["metrics_primary"]["test_rps"])
    with pytest.raises(TE.TestEvalError, match="exists"):
        TE.predict_test(model, prompts, 1.3, data_dir, out)
    with pytest.raises(TE.TestEvalError, match="temperature"):
        TE.predict_test(model, prompts, 0.0, data_dir, tmp_path / "p2.json")
