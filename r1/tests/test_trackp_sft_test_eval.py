"""Track P P.4 test evaluator (r1/c3/train/sft_test_eval.py): the primary test number of R1-TRACKP-SFT-DUP.

CPU only, synthetic sweep (the fixtures of test_trackp_sft.py); the real-label path uses a synthetic label block in
the audit format with evaluation files beside it, which must never be opened.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from r1.c3.train import metrics as M  # noqa: E402
from r1.c3.train import sft_data as SD  # noqa: E402
from r1.c3.train import sft_test_eval as TE  # noqa: E402
from r1.c3.train import tiny  # noqa: E402
from test_trackp_sft import (TOKS, _after_test_release, _control_plane_skip, _label_block, _prompts,  # noqa: E402,F401
                             opened, p3_gate_bypassed, sweep)

# As in test_trackp_sft.py: the raw-block readers as they behave once the T0 test release row exists (the PRE-STAGE A
# lock is tested in test_c3_release.py), and the P3 split-file gate bypassed for the synthetic sweep, whose instances
# are not the design's (the gate is tested in test_trackp_p3.py).
pytestmark = pytest.mark.usefixtures("p3_gate_bypassed")

EPS = 1e-300


def _table(rows, tmp_path: Path) -> tuple[Path, dict]:
    d = tmp_path / "table"
    d.mkdir()
    (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    _, files = SD.load_table(d)
    return d, files


def _build(sweep, tmp_path, source, *, policy=None, name="data", rows=None, prompt_record=None):
    rows = sweep["rows"] if rows is None else rows
    table_dir, files = _table(rows, tmp_path) if not (tmp_path / "table").exists() else \
        (tmp_path / "table", SD.load_table(tmp_path / "table")[1])
    cfg = {} if policy is None else {"cross_split_duplicates": policy}
    out = tmp_path / name
    SD.build_sft_data(rows, source, _prompts(sweep), out, split_cfg=cfg,
                      table_record={"path": str(table_dir), "sha256": files}, prompt_record=prompt_record)
    return out, table_dir


def _labelled_test(data_dir, rows, source):
    data = TE.read_data_dir(data_dir)
    return TE.heldout_populations(rows, data["splits"], source.label_records()), data


def _run_dir(tmp_path, data, *, T=1.0, name="run", weights=b"w0"):
    d = tmp_path / name
    (d / "best").mkdir(parents=True)
    (d / "best" / "adapter.bin").write_bytes(weights)
    (d / "best" / "temperature.json").write_text(json.dumps({"temperature": T, "fitted_on": "val"}))
    (d / "best.json").write_text(json.dumps({"step": 10, "value": 0.1, "bad": 0}))
    (d / "sft_report.json").write_text(json.dumps({"data_sha256": data["manifest_sha256"], "lr": 3e-5, "seed": 0}))
    return d


def _replay(table_files, ids, index_sha=None):
    return {"table_sha256": dict(table_files), "sweep_index_sha256": index_sha, "n": len(ids),
            "ids_sha256": TE._ids_sha(list(ids))}


def _write_logits(path, data, run_dir, table_files, logits: dict, *, arm="arm", index_sha=None, **over):
    doc = {"schema": TE.PREDICTIONS_SCHEMA, "sft_data_sha256": data["manifest_sha256"], "arm": arm, "model": {},
           "run": TE.run_record(run_dir, data), "replay": _replay(table_files, logits, index_sha),
           "logits": {k: [float(x) for x in v] for k, v in logits.items()}}
    doc.update(over)
    path.write_text(json.dumps(doc))
    return path


def _oracle(pops, rows, source):
    by_id = {r["proposal_id"]: r for r in rows}
    rec = {r["proposal_id"]: r for r in source.label_records()}
    return {p: SD.soft_target(rec[p], by_id[p]) for p in pops["secondary"]}


def _as_logits(probs: dict) -> dict:
    return {k: np.log(np.asarray(v, dtype=float) + EPS) for k, v in probs.items()}


def _setup(sweep, tmp_path, src=None, *, T=1.0, **build):
    src = src or SD.SyntheticLabelSource(sweep["rows"])
    data_dir, table_dir = _build(sweep, tmp_path, src, **build)
    rows = build.get("rows") or sweep["rows"]
    pops, data = _labelled_test(data_dir, rows, src)
    table_files = SD.load_table(table_dir)[1]
    run = _run_dir(tmp_path, data, T=T)
    return src, data_dir, table_dir, pops, data, table_files, run, rows


def _eval(data_dir, table_dir, src, path, run, out, ledger, **kw):
    return TE.evaluate_test(data_dir, table_dir, src, path, run, out, arm=kw.pop("arm", "arm"), ledger=ledger, **kw)


# ---------------------------------------------------------------------------------------------- populations

def test_primary_population_applies_the_exclusion_list(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    pops, data = _labelled_test(data_dir, sweep["rows"], src)
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
    assert pops["counts"]["secondary_rule_noops"] >= pops["counts"]["primary_rule_noops"]


@pytest.mark.parametrize("tamper, match", [
    (lambda sp: sp["test_proposals_seen_in_train_or_val"].pop(), "exclusion list differs"),
    (lambda sp: sp["test_proposals_seen_in_train_or_val"].append("x"), "exclusion list differs"),
    (lambda sp: sp.update(test_proposals_seen_in_train_or_val=None), "exclusion list differs"),
    (lambda sp: sp["instances"]["train"].append(sp["instances"]["test"][0]), "two splits"),
    (lambda sp: sp["instances"]["test"].pop(), "outside the recorded split"),
    # a consistently swapped assignment (train <-> test instance): the recorded split is not the recomputed one
    (lambda sp: (sp["instances"]["train"].append(sp["instances"]["test"].pop(0)),
                 sp["instances"]["test"].append(sp["instances"]["train"].pop(0))), "differs from its recomputation"),
    (lambda sp: sp["config"].update(salt="other/v1"), "differs from its recomputation"),
    (lambda sp: sp["universe"].update(n=sp["universe"]["n"] + 1), "universe"),
])
def test_split_and_exclusion_list_are_recomputed(sweep, tmp_path, tamper, match):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    splits = json.loads((data_dir / "splits.json").read_text())
    tamper(splits)
    with pytest.raises(TE.TestEvalError, match=match):
        TE.heldout_populations(sweep["rows"], splits, src.label_records())


def test_duplicate_table_ids_are_refused(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    data_dir, _ = _build(sweep, tmp_path, src)
    splits = json.loads((data_dir / "splits.json").read_text())
    with pytest.raises(TE.TestEvalError, match="duplicate proposal id"):
        TE.heldout_populations(sweep["rows"] + [sweep["rows"][0]], splits, src.label_records())


def _rows_with_unlabelled_train_duplicate(sweep):
    """The sweep's rows plus one unlabelled (``duplicate``) row on a train instance whose key equals a primary test
    proposal's key, so that proposal is excluded only through an unlabelled row."""
    rows = copy.deepcopy(sweep["rows"])
    split_of = SD.assign_splits({r["instance"] for r in rows})
    keys = {s: {SD.dup_key(r) for r in rows if split_of[r["instance"]] == s} for s in ("train", "val")}
    target = next(r for r in rows if split_of[r["instance"]] == "test" and not r["noop"] and not r["duplicate"]
                  and SD.dup_key(r) not in keys["train"] | keys["val"])
    host = next(r for r in rows if split_of[r["instance"]] == "train")
    extra = {**copy.deepcopy(host), "proposal_id": host["proposal_id"] + "_dupx", "duplicate": True, "noop": False,
             "incumbent_hash": target["incumbent_hash"], "candidate_hash": target["candidate_hash"]}
    return rows + [extra], target["proposal_id"]


def test_a_test_key_seen_only_on_an_unlabelled_train_row_is_excluded_by_the_evaluator(sweep, tmp_path):
    rows, target = _rows_with_unlabelled_train_duplicate(sweep)
    src = SD.SyntheticLabelSource(rows)
    assert target in {r["proposal_id"] for r in src.label_records()}
    data_dir, _ = _build(sweep, tmp_path, src, rows=rows)
    pops, data = _labelled_test(data_dir, rows, src)
    assert target in data["splits"]["test_proposals_seen_in_train_or_val"]
    assert target in pops["excluded"] and target in pops["secondary"] and target not in pops["primary"]


# ---------------------------------------------------------------------------------------------- evaluation

def test_oracle_and_independent_training_base_rate(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"], shift_z=1.0)
    _, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path, src)
    oracle = _oracle(pops, rows, src)
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    rep = _eval(data_dir, table_dir, src, _write_logits(tmp_path / "o.json", data, run, files, _as_logits(oracle)),
                run, tmp_path / "rep_o", led, suite_of={"digits_mlp": "T0"})
    p, s = rep["metrics_primary"], rep["metrics_secondary"]
    assert p["test_n"] == len(pops["primary"]) and s["test_full_n"] == len(pops["secondary"])
    assert p["test_rps"] == pytest.approx(0.0, abs=1e-10) and s["test_full_rps"] == pytest.approx(0.0, abs=1e-10)
    assert p["test_rps_skill"] == pytest.approx(1.0)
    assert rep["populations"]["exclusion_list_matches_recomputation"] is True
    assert rep["evaluation_seeds_read"] is False and rep["label_seeds"] == [7001, 7002, 7003, 7004, 7005]
    assert "phase-1 / ENGINEERING target" in rep["test_target"]
    assert rep["by_suite"]["T0"]["test_n"] == len(pops["primary"])
    assert rep["by_suite"]["T0"]["test_full_n"] == len(pops["secondary"])
    assert "ENGINEERING_ONLY" in rep["label_status"] and rep["data"]["cross_split_duplicates"] == "heldout_excludes_seen"
    on_disk = json.loads((tmp_path / "rep_o" / "test_report.json").read_text())
    assert on_disk["populations"]["primary_ids_sha256"] == TE._ids_sha(pops["primary"])
    # the base rate computed here from the training rows alone (not through the evaluator)
    train_y = [json.loads(x)["y"] for x in (data_dir / "rows.jsonl").read_text().splitlines()
               if x.strip() and json.loads(x)["split"] == "train"]
    base = M.base_rate(np.asarray(train_y, dtype=float))
    val_y = [json.loads(x)["y"] for x in (data_dir / "rows.jsonl").read_text().splitlines()
             if x.strip() and json.loads(x)["split"] != "train"]
    assert not np.allclose(base, M.base_rate(np.asarray(train_y + val_y, dtype=float)))
    run_b = _run_dir(tmp_path, data, name="run_b", weights=b"wb")
    path = _write_logits(tmp_path / "b.json", data, run_b, files, _as_logits({k: base for k in oracle}), arm="base")
    rep = _eval(data_dir, table_dir, src, path, run_b, tmp_path / "rep_b", led, arm="base")
    assert rep["metrics_primary"]["test_rps_skill"] == pytest.approx(0.0, abs=1e-10)
    assert rep["metrics_secondary"]["test_full_rps_skill"] == pytest.approx(0.0, abs=1e-10)
    assert rep["by_suite"]["unassigned"]["test_n"] == len(pops["primary"])
    run_u = _run_dir(tmp_path, data, name="run_u", weights=b"wu")
    path = _write_logits(tmp_path / "u.json", data, run_u, files, {k: np.zeros(TE.N_BINS) for k in oracle}, arm="u")
    rep = _eval(data_dir, table_dir, src, path, run_u, tmp_path / "rep_u", led, arm="u")
    assert abs(rep["metrics_primary"]["test_rps_skill"]) > 1e-3   # uniform is not the base rate


def test_primary_and_secondary_differ_exactly_by_the_excluded_proposals(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    oracle = _oracle(pops, rows, src)
    excl = set(pops["excluded"])
    probs = {k: (v if k in excl else np.full(TE.N_BINS, 1.0 / TE.N_BINS)) for k, v in oracle.items()}
    rep = _eval(data_dir, table_dir, src, _write_logits(tmp_path / "p.json", data, run, files, _as_logits(probs)),
                run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)
    u = np.full((len(pops["primary"]), TE.N_BINS), 1.0 / TE.N_BINS)
    y = np.stack([oracle[k] for k in pops["primary"]])
    assert rep["metrics_primary"]["test_rps"] == pytest.approx(M.mean_rps(u, y))
    n_p, n_s = len(pops["primary"]), len(pops["secondary"])
    assert rep["metrics_secondary"]["test_full_rps"] == pytest.approx(M.mean_rps(u, y) * n_p / n_s, abs=1e-10)


def test_temperature_comes_from_the_run_and_both_scalings_are_reported(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path, T=2.5)
    rng = np.random.default_rng(0)
    logits = {k: rng.normal(size=TE.N_BINS) for k in pops["secondary"]}
    rep = _eval(data_dir, table_dir, src, _write_logits(tmp_path / "p.json", data, run, files, logits),
                run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)
    oracle = _oracle(pops, rows, src)
    y = np.stack([oracle[k] for k in pops["primary"]])
    z = np.stack([logits[k] for k in pops["primary"]])
    assert rep["run"]["temperature"] == 2.5
    assert rep["metrics_primary"]["test_rps"] == pytest.approx(M.mean_rps(TE._softmax(z / 2.5), y))
    assert rep["metrics_primary_raw"]["test_rps"] == pytest.approx(M.mean_rps(TE._softmax(z), y))
    assert rep["metrics_primary"]["test_rps"] != pytest.approx(rep["metrics_primary_raw"]["test_rps"])


@pytest.mark.parametrize("edit, match", [
    (lambda lg, d: lg.popitem(), "exactly the labelled test proposals"),
    (lambda lg, d: lg.update({"not_a_test_id": [0.0] * 12}), "exactly the labelled test proposals"),
    (lambda lg, d: lg.update({next(iter(lg)): [0.0] * 11}), "logit vector"),
    (lambda lg, d: lg.update({next(iter(lg)): [float("nan")] * 12}), "logit vector"),
    (lambda lg, d: lg.update({next(iter(lg)): ["a"] * 12}), "numeric"),
    (lambda lg, d: d.update(sft_data_sha256="0" * 64), "another data directory"),
    (lambda lg, d: d.update(schema="trackp_sft_test_predictions/v1"), "schema"),
    (lambda lg, d: d.update(arm="other"), "arm"),
    (lambda lg, d: d["run"].update(temperature=1.7), "temperature"),
    (lambda lg, d: d["run"].update(best_tree_sha256="0" * 64), "best_tree_sha256"),
    (lambda lg, d: d["replay"].update(table_sha256={"proposals.jsonl": "0" * 64}), "another table"),
])
def test_logits_file_refusals(sweep, tmp_path, edit, match):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    logits = {k: [0.0] * 12 for k in pops["secondary"]}
    path = _write_logits(tmp_path / "p.json", data, run, files, logits)
    doc = json.loads(path.read_text())
    edit(doc["logits"], doc)
    if "not_a_test_id" in doc["logits"] or len(doc["logits"]) != len(logits):
        doc["replay"] = _replay(files, doc["logits"])
    path.write_text(json.dumps(doc))
    with pytest.raises(TE.TestEvalError, match=match):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)
    assert not (tmp_path / "rep" / "test_report.json").exists()
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    assert not led.exists() or led.read_text() == ""


def test_a_changed_checkpoint_or_temperature_after_prediction_is_refused(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    (run / "best" / "adapter.bin").write_bytes(b"other weights")
    with pytest.raises(TE.TestEvalError, match="best_tree_sha256"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)
    (run / "best" / "adapter.bin").write_bytes(b"w0")
    (run / "best" / "temperature.json").write_text(json.dumps({"temperature": 1.5}))
    with pytest.raises(TE.TestEvalError, match="temperature"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)
    other = _run_dir(tmp_path, {"manifest_sha256": "0" * 64}, name="foreign")
    with pytest.raises(TE.TestEvalError, match="another data directory"):
        TE.run_record(other, data)


def test_one_test_read_per_arm_and_per_checkpoint(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    _eval(data_dir, table_dir, src, path, run, tmp_path / "r1", led)
    entry = json.loads(led.read_text())
    assert entry["arm"] == "arm" and entry["best_tree_sha256"] == TE.run_record(run, data)["best_tree_sha256"]
    with pytest.raises(TE.TestEvalError, match="one test read per arm"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "r1", led)          # same output directory
    with pytest.raises(TE.TestEvalError, match="one test read per arm"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "r2", led)          # another directory, same arm
    path2 = _write_logits(tmp_path / "p2.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]},
                          arm="renamed")
    with pytest.raises(TE.TestEvalError, match="one test read per arm"):
        _eval(data_dir, table_dir, src, path2, run, tmp_path / "r3", led, arm="renamed")   # same checkpoint
    assert len(led.read_text().splitlines()) == 1
    # the same arm id with another checkpoint (best/ changed and re-predicted): still one read per arm
    (run / "best" / "adapter.bin").write_bytes(b"another checkpoint")
    path3 = _write_logits(tmp_path / "p3.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    with pytest.raises(TE.TestEvalError, match="one test read per arm"):
        _eval(data_dir, table_dir, src, path3, run, tmp_path / "r4", led)
    # another arm on another checkpoint reads once
    run_o = _run_dir(tmp_path, data, name="run_other", weights=b"other arm weights")
    path4 = _write_logits(tmp_path / "p4.json", data, run_o, files, {k: [0.0] * 12 for k in pops["secondary"]},
                          arm="other_arm")
    _eval(data_dir, table_dir, src, path4, run_o, tmp_path / "r5", led, arm="other_arm")
    assert len(led.read_text().splitlines()) == 2


def test_data_bindings(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    with pytest.raises(TE.TestEvalError, match="seed"):
        _eval(data_dir, table_dir, SD.SyntheticLabelSource(sweep["rows"], seed=1), path, run, tmp_path / "a", led)
    with pytest.raises(TE.TestEvalError, match="shift_z"):
        _eval(data_dir, table_dir, SD.SyntheticLabelSource(sweep["rows"], shift_z=0.5), path, run, tmp_path / "b",
              led)
    rows_t = (table_dir / "proposals.jsonl").read_text().splitlines()
    (table_dir / "proposals.jsonl").write_text("\n".join(rows_t[:-1]) + "\n")
    with pytest.raises(SD.SFTDataError, match="pinned"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "c", led)
    (table_dir / "proposals.jsonl").write_text("\n".join(rows_t) + "\n")
    sp = data_dir / "splits.json"
    sp.write_text(sp.read_text().replace('"test"', '"test" ', 1))
    with pytest.raises(TE.TestEvalError, match="sha256"):
        TE.read_data_dir(data_dir)


def _rehash(data_dir: Path, *, splits=None, manifest_edit=None):
    """Rewrite splits.json and/or the manifest consistently (hashes updated), as a careless rebuild would."""
    if splits is not None:
        (data_dir / "splits.json").write_text(json.dumps(splits, indent=1, sort_keys=True) + "\n")
    m = json.loads((data_dir / "sft_data.json").read_text())
    m["splits_sha256"] = SD.sha256_file(data_dir / "splits.json")
    if manifest_edit:
        manifest_edit(m)
    (data_dir / "sft_data.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def test_policy_version_sweep_and_completion_refusals(sweep, tmp_path):
    # the policy, with a consistent manifest and real labels
    audit = tmp_path / "audit"
    block = _label_block(sweep, audit)
    data_dir, table_dir = _build(sweep, tmp_path, SD.LabelBlockSource(block))
    sp = json.loads((data_dir / "splits.json").read_text())
    sp["config"]["cross_split_duplicates"] = "exclude_from_heldout"
    _rehash(data_dir, splits=sp)
    with pytest.raises(TE.TestEvalError, match="R1-TRACKP-SFT-DUP decides"):
        TE.read_data_dir(data_dir)
    # the featurizer / prompt version
    d2, _ = _build(sweep, tmp_path, SD.SyntheticLabelSource(sweep["rows"]), name="d2")
    _rehash(d2, manifest_edit=lambda m: m.update(prompt_version="trackp_prompt/v1"))
    with pytest.raises(TE.TestEvalError, match="this code is"):
        TE.read_data_dir(d2)
    # the label sweep and the completion record
    d3, _ = _build(sweep, tmp_path, SD.LabelBlockSource(block), name="d3")
    m3 = json.loads((d3 / "sft_data.json").read_text())
    for edit, match in ((lambda m: m["labels"].update(sweep="sweep2"), "sweep"),
                        (lambda m: m["labels"]["completion"].update(sha256="0" * 64), "completion")):
        m = copy.deepcopy(m3)
        edit(m)
        with pytest.raises(TE.TestEvalError, match=match):
            TE.check_label_source(m, SD.LabelBlockSource(block))


def test_phase1_refuses_a_real_label_test_read_and_the_real_path_opens_no_evaluation_file(sweep, tmp_path, opened):
    audit = tmp_path / "audit"
    block = _label_block(sweep, audit)
    src = SD.LabelBlockSource(block)
    index_sha = SD.sha256_file(sweep["inputs"]["index_path"])
    data_dir, table_dir = _build(sweep, tmp_path, src, prompt_record={"sweep_index": {"sha256": index_sha}})
    pops, data = _labelled_test(data_dir, sweep["rows"], src)
    files = SD.load_table(table_dir)[1]
    run = _run_dir(tmp_path, data)
    path = _write_logits(tmp_path / "p.json", data, run, files, _as_logits(_oracle(pops, sweep["rows"], src)),
                         index_sha=index_sha)
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    with pytest.raises(TE.TestEvalError, match="refused in phase 1"):
        _eval(data_dir, table_dir, SD.LabelBlockSource(block), path, run, tmp_path / "rep0", led)
    opened.clear()
    rep = _eval(data_dir, table_dir, SD.LabelBlockSource(block), path, run, tmp_path / "rep", led,
                allow_engineering_real_label_read=True)
    assert rep["labels"]["kind"] == "label_block" and rep["metrics_primary"]["test_rps"] == pytest.approx(0, abs=1e-10)
    names = {Path(p).name for p in opened}
    assert "label_block.jsonl" in names and not names & {"evaluation_block.jsonl", "runs.jsonl"}
    # a logits file replayed from another sweep index
    run2 = _run_dir(tmp_path, data, name="run2", weights=b"w2")
    bad = _write_logits(tmp_path / "q.json", data, run2, files, {k: [0.0] * 12 for k in pops["secondary"]},
                        arm="a2", index_sha="0" * 64)
    with pytest.raises(TE.TestEvalError, match="sweep index"):
        _eval(data_dir, table_dir, SD.LabelBlockSource(block), bad, run2, tmp_path / "rep2", led, arm="a2",
              allow_engineering_real_label_read=True)
    with pytest.raises(SD.SFTDataError, match="evaluation"):
        TE.read_predictions(audit / "evaluation_block.jsonl", data, pops["secondary"])


def test_data_without_a_table_hash_or_exclusion_list_is_refused(sweep, tmp_path):
    src = SD.SyntheticLabelSource(sweep["rows"])
    out = tmp_path / "nopin"
    SD.build_sft_data(sweep["rows"], src, _prompts(sweep), out)
    table_dir, _ = _table(sweep["rows"], tmp_path)
    data = TE.read_data_dir(out)
    with pytest.raises(TE.TestEvalError, match="no table hash"):
        TE._pinned_table(data, table_dir)
    old, _ = _build(sweep, tmp_path, src, policy="drop_from_train", name="old")
    with pytest.raises(TE.TestEvalError, match="no exclusion list"):
        TE.read_data_dir(old)


def test_breakdown_reports_groups_only_among_the_excluded_and_refuses_unmapped_nodes():
    probs = {p: np.full(TE.N_BINS, 1.0 / TE.N_BINS) for p in ("a1", "a2", "b1")}
    targets = {p: np.eye(TE.N_BINS)[3] for p in probs}
    base = np.full(TE.N_BINS, 1.0 / TE.N_BINS)
    node_of = {"a1": "node_a", "a2": "node_a", "b1": "node_b"}
    out = TE.breakdown(["a1"], ["a1", "a2", "b1"], node_of, TE.suite_function({"node_a": "S1", "node_b": "S2"}),
                       probs, targets, base)
    assert out["node"]["node_a"]["test_n"] == 1 and out["node"]["node_a"]["test_full_n"] == 2
    assert out["node"]["node_b"] == {"test_n": 0, "test_full_n": 1}
    assert out["suite"]["S2"] == {"test_n": 0, "test_full_n": 1}
    with pytest.raises(TE.TestEvalError, match="no suite"):
        TE.breakdown(["a1"], ["a1", "b1"], node_of, TE.suite_function({"node_a": "S1"}), probs, targets, base)


def test_nan_metrics_are_written_as_null():
    assert TE._json_safe({"a": float("nan"), "b": [1.0, float("inf")], "c": np.float32(2.0)}) == \
        {"a": None, "b": [1.0, None], "c": 2.0}


def test_replay_and_predict_write_a_bound_logits_file(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path, T=1.3)
    prompts, replay = TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=data_dir,
                                             table_dir=table_dir, label_source=src)
    assert sorted(prompts) == pops["secondary"] and replay["table_sha256"] == files
    model = tiny.build_hashbag(seed=0)
    loaded = []
    loader = lambda best: loaded.append(best) or model  # noqa: E731
    out = tmp_path / "logits.json"
    doc = TE.predict_test(loader, prompts, replay, run, data_dir, out, arm="hashbag", model_record={"seed": 0})
    assert loaded == [run / "best"]
    assert doc["run"]["temperature"] == 1.3 and set(doc["logits"]) == set(pops["secondary"])
    from r1.c3.train.sft import predict_logits
    ids = sorted(prompts)
    assert np.allclose(np.asarray([doc["logits"][i] for i in ids]), predict_logits(model, [prompts[i] for i in ids]))
    rep = _eval(data_dir, table_dir, src, out, run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME, arm="hashbag")
    assert rep["logits"]["arm"] == "hashbag" and np.isfinite(rep["metrics_primary"]["test_rps"])
    with pytest.raises(TE.TestEvalError, match="exists"):
        TE.predict_test(loader, prompts, replay, run, data_dir, out, arm="hashbag")
    with pytest.raises(TE.TestEvalError, match="replayed set"):
        TE.predict_test(loader, dict(list(prompts.items())[1:]), replay, run, data_dir, tmp_path / "p2.json", arm="h")

    def changing_loader(best):
        (best / "adapter.bin").write_bytes(b"changed during load")
        return model
    with pytest.raises(TE.TestEvalError, match="changed while the model was loaded"):
        TE.predict_test(changing_loader, prompts, replay, run, data_dir, tmp_path / "p3.json", arm="h")


def test_replay_refuses_a_feature_that_differs_from_the_table_row(sweep, tmp_path, monkeypatch):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    real = SD.sweep_prompts

    def tampered(*a, **k):
        out = real(*a, **k)
        pid = pops["secondary"][0]
        prompt, feats = out[pid]
        out[pid] = (prompt, {**feats, "tampered": 1.0})
        return out
    monkeypatch.setattr(SD, "sweep_prompts", tampered)
    with pytest.raises(TE.TestEvalError, match="replayed features differ"):
        TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=data_dir, table_dir=table_dir,
                               label_source=src)


# ---------------------------------------------------------------------------------------------- round-2 additions

def test_the_p3_assignment_is_the_preregistration_formula():
    """PRE-SPLIT A (sweep-2 analysis preregistration @ 95da769e): per node, order by
    sha256("c3_p3_split/v1:" + "<node>__s<seed>"); first 9 test, next 3 dev, last 6 train. Recomputed here
    independently and compared with the builder's assignment under P4-P1SPLIT A's config."""
    import hashlib
    nodes = ["digits_mlp", "openml_breast_w", "openml_climate", "openml_credit_approval", "openml_ionosphere",
             "openml_sonar", "openml_wdbc", "tabular_mlp"]
    uni = SD.instance_universe(nodes, 18)
    got = SD.assign_splits(uni, {"salt": "c3_p3_split/v1", "test_instances_per_node": 9,
                                 "val_instances_per_node": 3}, universe=uni)
    for node in nodes:
        insts = [i for i in uni if i.split("__s")[0] == node]
        assert len(insts) == 18 and all(i == f"{node}__s{int(i.rsplit('__s', 1)[1])}" for i in insts)
        order = sorted(insts, key=lambda i: hashlib.sha256(f"c3_p3_split/v1:{i}".encode()).hexdigest())
        want = {i: "test" if k < 9 else "val" if k < 12 else "train" for k, i in enumerate(order)}
        assert {i: got[i] for i in insts} == want


def test_ledger_binds_the_test_material_not_the_data_directory(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    led = tmp_path / "ledgers" / TE.LEDGER_NAME
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    _eval(data_dir, table_dir, src, path, run, tmp_path / "r1", led)
    # a rebuilt data directory over the same table, labels and split: another sft_data sha256, same material
    m = json.loads((data_dir / "sft_data.json").read_text())
    rebuilt = tmp_path / "rebuilt"
    rebuilt.mkdir()
    for name in ("rows.jsonl", "splits.json"):
        (rebuilt / name).write_bytes((data_dir / name).read_bytes())
    m["counts"] = {**m["counts"], "rebuilt": 1}
    (rebuilt / "sft_data.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    data2 = TE.read_data_dir(rebuilt)
    assert data2["manifest_sha256"] != data["manifest_sha256"]
    run2 = _run_dir(tmp_path, data2, name="run_rebuilt")      # same weights: the same best checkpoint
    path2 = _write_logits(tmp_path / "p2.json", data2, run2, files, {k: [0.0] * 12 for k in pops["secondary"]},
                          arm="other_id")
    with pytest.raises(TE.TestEvalError, match="already read on this test material"):
        _eval(rebuilt, table_dir, src, path2, run2, tmp_path / "r2", led, arm="other_id")
    with pytest.raises(TE.TestEvalError, match="must be named"):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "r3", tmp_path / "other.jsonl")


@pytest.mark.parametrize("edit, match", [
    (lambda d: d["run"].update(sft_report_sha256="0" * 64), "sft_report_sha256"),
    (lambda d: d["run"].update(best_json_sha256="0" * 64), "best_json_sha256"),
    (lambda d: d["run"].update(temperature_json_sha256="0" * 64), "temperature_json_sha256"),
])
def test_every_run_hash_is_checked(sweep, tmp_path, edit, match):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    doc = json.loads(path.read_text())
    edit(doc)
    path.write_text(json.dumps(doc))
    with pytest.raises(TE.TestEvalError, match=match):
        _eval(data_dir, table_dir, src, path, run, tmp_path / "rep", tmp_path / "ledgers" / TE.LEDGER_NAME)


@pytest.mark.parametrize("T", [0.0, -1.0, float("nan"), "1.0", True])
def test_a_non_positive_or_non_numeric_temperature_is_refused(sweep, tmp_path, T):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    (run / "best" / "temperature.json").write_text(json.dumps({"temperature": T}))
    with pytest.raises(TE.TestEvalError, match="positive number"):
        TE.run_record(run, data)


def test_real_labels_need_a_recorded_sweep_index(sweep, tmp_path):
    block = _label_block(sweep, tmp_path / "audit")
    src = SD.LabelBlockSource(block)
    data_dir, table_dir = _build(sweep, tmp_path, src)                       # no prompt record
    pops, data = _labelled_test(data_dir, sweep["rows"], src)
    files = SD.load_table(table_dir)[1]
    run = _run_dir(tmp_path, data)
    path = _write_logits(tmp_path / "p.json", data, run, files, {k: [0.0] * 12 for k in pops["secondary"]})
    with pytest.raises(TE.TestEvalError, match="records no sweep index"):
        _eval(data_dir, table_dir, SD.LabelBlockSource(block), path, run, tmp_path / "rep",
              tmp_path / "ledgers" / TE.LEDGER_NAME, allow_engineering_real_label_read=True)


def test_replay_checks_the_pinned_table_the_label_source_and_the_sweep_index(sweep, tmp_path):
    src, data_dir, table_dir, pops, data, files, run, rows = _setup(sweep, tmp_path)
    with pytest.raises(TE.TestEvalError, match="seed"):
        TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=data_dir, table_dir=table_dir,
                               label_source=SD.SyntheticLabelSource(sweep["rows"], seed=3))
    index_sha = SD.sha256_file(sweep["inputs"]["index_path"])
    d2, _ = _build(sweep, tmp_path, src, name="d2", prompt_record={"sweep_index": {"sha256": "0" * 64}})
    with pytest.raises(TE.TestEvalError, match="sweep index differs"):
        TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=d2, table_dir=table_dir, label_source=src)
    d3, _ = _build(sweep, tmp_path, src, name="d3", prompt_record={"sweep_index": {"sha256": index_sha}})
    TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=d3, table_dir=table_dir, label_source=src)
    lines = (table_dir / "proposals.jsonl").read_text().splitlines()
    (tmp_path / "proposals_backup.jsonl").write_text("\n".join(lines) + "\n")
    (table_dir / "proposals.jsonl").write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(SD.SFTDataError, match="pinned"):
        TE.replay_test_prompts(sweep["inputs"], tokenizers=TOKS, data_dir=data_dir, table_dir=table_dir,
                               label_source=src)


def test_an_unlabelled_test_row_seen_on_train_is_on_the_list_but_in_no_population(sweep, tmp_path):
    """An unlabelled (duplicate) test row whose key occurs on a train instance is listed (the builder lists table
    rows) but is in neither population; the recomputation must list it too."""
    rows = copy.deepcopy(sweep["rows"])
    split_of = SD.assign_splits({r["instance"] for r in rows})
    train_row = next(r for r in rows if split_of[r["instance"]] == "train" and not r["noop"] and not r["duplicate"])
    host = next(r for r in rows if split_of[r["instance"]] == "test")
    extra = {**copy.deepcopy(host), "proposal_id": host["proposal_id"] + "_tdup", "duplicate": True, "noop": False,
             "incumbent_hash": train_row["incumbent_hash"], "candidate_hash": train_row["candidate_hash"]}
    rows = rows + [extra]
    src = SD.SyntheticLabelSource(rows)
    data_dir, _ = _build(sweep, tmp_path, src, rows=rows)
    pops, data = _labelled_test(data_dir, rows, src)
    assert extra["proposal_id"] in pops["excluded"]
    assert extra["proposal_id"] not in pops["secondary"] and extra["proposal_id"] not in pops["primary"]
