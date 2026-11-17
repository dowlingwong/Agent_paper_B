"""Track P Stage S (SFT) pipeline: data builder, label sources, splits, trainer runner, CLI (R1-TRACKP-SFT-DEV).

Tiny CPU dry run on a synthetic sweep (synthetic ledgers -> table rows by the table's own replay -> prompts ->
synthetic or label-block labels -> hash-bag model). ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import builtins
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")  # not in the harness lock; present on the Track P hosts

from r1.c3 import dataset as D
from r1.c3 import features as F
from r1.c3 import labels as LB
from r1.c3.features import NodeContext
from r1.c3.train import sft as SFT
from r1.c3.train import sft_data as SD
from r1.c3.train import tiny
from r1.c3.train.run import TrackPStop
from r1.c3.train.types import PROMPT_VERSION

NODE = "digits_mlp"
SIGMA = 0.0075
START = {"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"}
VALUES = {"HIDDEN_UNITS": ["16", "32", "64", "128"], "ALPHA": ["1e-5", "1e-4", "1e-3", "1e-2"],
          "MAX_ITER": ["20", "40", "80", "160"]}
SOURCE = "c3_synth_none"
INSTANCES = [f"{NODE}__s{100 + k}" for k in range(9)]
NOISE = {NODE: {"sigma_node": SIGMA, "sigma_structural": SIGMA, "sigma_local": SIGMA}}


class _Whitespace:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


TOKS = {"whitespace": _Whitespace()}


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    """As in test_trackp_serialize: stand in for the harness's ``is_control_plane_skip`` when the pin lacks it."""
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def _metric(cfg: dict) -> float:
    h = int(hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8], 16)
    return round(0.85 + (h % 1000) / 10000.0, 4)


def _ledger(inst: str, n: int = 10) -> list[dict]:
    rng = np.random.default_rng(int(inst.rsplit("__s", 1)[1]))
    inc = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}
    best, rows = None, []
    for b in range(1, n + 1):
        key = list(VALUES)[int(rng.integers(3))]
        if b == 4:   # one rule no-op per campaign: the edit sets the incumbent's own value
            new = inc[key]
        else:
            new = str(rng.choice([v for v in VALUES[key] if v != inc[key]]))
        cand = {**inc, key: new}
        m = _metric(cand)
        delta = None if best is None else m - best
        kept = best is None or m > best
        rows.append({"budget_index": b, "decision": "kept" if kept else "discarded",
                     "parsed_metrics": {"val_score": m}, "current_best_before": best, "delta_vs_best": delta,
                     "extra": {"manager": {"structured_edit": {"symbol": key, "old": inc[key], "new": new,
                                                               "path": "train.py"}}}})
        if kept:
            inc, best = cand, m
    return rows


@pytest.fixture()
def sweep(tmp_path):
    """Synthetic sweep directory (roots/<inst>.json start files, ledgers/<inst>/root_trials.jsonl), its table rows
    (built by the table's own replay) and ``sweep_replay_inputs``-shaped inputs."""
    d = tmp_path / "sweep_none"
    rows = []
    for inst in INSTANCES:
        led = _ledger(inst)
        (d / "ledgers" / inst).mkdir(parents=True)
        (d / "ledgers" / inst / "root_trials.jsonl").write_text("".join(json.dumps(r) + "\n" for r in led))
        (d / "roots").mkdir(exist_ok=True)
        (d / "roots" / f"{inst}.json").write_text(json.dumps({"start_files": START}))
        props, checks = F.replay_campaign(led, START, NODE, inst, SOURCE, "none", 20, SIGMA)
        assert checks["zero_delta_violations"] == 0
        rows += [D.row_of(p, NOISE) for p in props]
    spec = {"dir": str(d), "ledgers": "ledgers/*/root_trials.jsonl", "runs": 20, "memory_mode": "none"}
    inputs = {"index_path": tmp_path / "index.json", "specs": {SOURCE: (spec, d)}, "noise": NOISE}
    (tmp_path / "index.json").write_text("{}")
    return {"dir": d, "rows": rows, "inputs": inputs, "tmp": tmp_path}


def _prompts(sweep):
    return SD.sweep_prompts(sweep["inputs"], tokenizers=TOKS)


def _label_block(sweep, audit_dir: Path, *, schema="r1.c3_audit_completion/3", seeds=SD.LABEL_SEEDS, mutate=None,
                 index_sha256=SD.SWEEP1_INDEX_SHA):
    """A label block in audit.evidence_blocks' row format, its completion, and evaluation/run files beside it."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    labels, evals = [], []
    for r in sweep["rows"]:
        if r["noop"]:
            labels.append({"proposal_id": r["proposal_id"], "node": r["node"], "label_kind": "rule_noop",
                           "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}})
        elif not r["duplicate"]:
            d = float(np.sin(hash(r["proposal_id"]) % 97)) * SIGMA
            labels.append({"proposal_id": r["proposal_id"], "node": r["node"], "label_kind": "audit",
                           "seeds": list(seeds), "delta_label": d, "se_label": 0.001,
                           "soft_parameters": {"inert": False, "sigma_node": SIGMA, "k_label": 5,
                                               "delta_label": d, "se_label": 0.001}})
            evals.append({"proposal_id": r["proposal_id"], "node": r["node"], "seeds": [7006, 7007, 7008, 7009, 7010],
                          "delta_evaluation": 123.0, "se_evaluation": 1.0})
    if mutate:
        mutate(labels)
    (audit_dir / "label_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in labels))
    (audit_dir / "evaluation_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in evals))
    (audit_dir / "runs.jsonl").write_text('{"seed": 7006, "metric": 0.5}\n')
    completion = {"schema": schema, "label": "EVIDENCE", "label_seeds": list(seeds), "index_sha256": index_sha256,
                  "classification_sha256": "c" * 64,
                  "evaluation_seeds": [7006, 7007, 7008, 7009, 7010],
                  "label_block_sha256": SD.sha256_file(audit_dir / "label_block.jsonl"),
                  "evaluation_block_sha256": SD.sha256_file(audit_dir / "evaluation_block.jsonl"),
                  "proposals_sha256": "p" * 64, "counts": {"eligible": len(evals)}}
    (audit_dir / "evidence_completion.json").write_text(json.dumps(completion))
    return audit_dir / "label_block.jsonl"


@pytest.fixture()
def opened(monkeypatch):
    """Every path opened through builtins.open / io.open (pathlib's read_text and read_bytes go through io.open)."""
    seen: list[str] = []
    real = builtins.open

    def spy(file, *a, **k):
        seen.append(str(file))
        return real(file, *a, **k)
    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy)
    return seen


# ---------------------------------------------------------------------------------------------- prompts & table

def test_prompts_bind_to_table_rows(sweep):
    prompts = _prompts(sweep)
    ids = {r["proposal_id"] for r in sweep["rows"]}
    assert set(prompts) == ids and len(ids) > 50
    for r in sweep["rows"]:
        p, feats = prompts[r["proposal_id"]]
        assert F.features_hash(feats) == F.features_hash(r["features"])
        assert p.meta["prompt_version"] == PROMPT_VERSION and p.meta["proposal_id"] == r["proposal_id"]
        assert p.group == r["proposal_id"] and f"Node: {NODE}" in p.state
    some = sorted(ids)[0]
    only = SD.sweep_prompts(sweep["inputs"], tokenizers=TOKS, wanted={some})
    assert some in only and all(k.rsplit(":", 1)[0] == some.rsplit(":", 1)[0] for k in only)


def test_feature_mismatch_and_stray_prompts_refused(sweep, tmp_path):
    prompts = _prompts(sweep)
    rows = [dict(r) for r in sweep["rows"]]
    rows[5] = {**rows[5], "features": {**rows[5]["features"], "key_edit_count": 99.0}}
    with pytest.raises(SD.SFTDataError, match="replayed features differ"):
        SD.build_sft_data(rows, SD.SyntheticLabelSource(rows), prompts, tmp_path / "o1")
    with pytest.raises(SD.SFTDataError, match="not in the table"):
        SD.build_sft_data(sweep["rows"][1:], SD.SyntheticLabelSource(sweep["rows"][1:]), prompts, tmp_path / "o2")


def test_load_table_pins_and_eval_columns(tmp_path, sweep):
    t = tmp_path / "table"
    t.mkdir()
    (t / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sweep["rows"]))
    rows, files = SD.load_table(t, {"proposals.jsonl": SD.sha256_file(t / "proposals.jsonl")})
    assert len(rows) == len(sweep["rows"])
    with pytest.raises(SD.SFTDataError, match="pinned"):
        SD.load_table(t, {"proposals.jsonl": "0" * 64})
    (t / "proposals.jsonl").write_text(json.dumps({**sweep["rows"][0], "y_eval": [0.0]}) + "\n")
    with pytest.raises(SD.SFTDataError, match="evaluation-column"):
        SD.load_table(t)


# ---------------------------------------------------------------------------------------------- labels

def test_soft_targets_follow_r1_soft_sigma(sweep):
    row = next(r for r in sweep["rows"] if not r["noop"] and not r["duplicate"])
    rec = {"proposal_id": row["proposal_id"], "node": NODE, "label_kind": "audit", "delta_label": 0.004,
           "k_label": 5, "sigma_node": SIGMA}
    y = SD.soft_target(rec, row)
    assert np.allclose(y, LB.soft_label(0.004, None, SIGMA, sigma_mode="pooled_node", k_label=5))
    assert y[0] == 0 and abs(y.sum() - 1) < 1e-9
    noop = next(r for r in sweep["rows"] if r["noop"])
    y0 = SD.soft_target({"proposal_id": noop["proposal_id"], "node": NODE, "label_kind": "rule_noop"}, noop)
    assert y0[0] == 1 and y0.sum() == 1
    with pytest.raises(SD.SFTDataError, match="sigma_node"):
        SD.soft_target({**rec, "sigma_node": SIGMA * 2}, row)
    with pytest.raises(SD.SFTDataError, match="inert"):
        SD.soft_target(rec, noop)


def test_label_block_source_never_opens_evaluation_files(sweep, tmp_path, opened):
    block = _label_block(sweep, tmp_path / "audit")
    prompts = _prompts(sweep)
    opened.clear()                      # the fixture's own writes above are not the builder's reads
    src = SD.LabelBlockSource(block)
    out = tmp_path / "data"
    SD.build_sft_data(sweep["rows"], src, prompts, out)
    names = {Path(p).name for p in opened}
    assert "label_block.jsonl" in names and "evidence_completion.json" in names
    assert not names & {"evaluation_block.jsonl", "runs.jsonl", "audits.jsonl"}
    man = json.loads((out / "sft_data.json").read_text())
    assert man["table_matches_audit_table"] is None          # no table record given here
    prov = man["labels"]
    assert prov["kind"] == "label_block" and prov["sweep"] == "sweep1"
    assert prov["completion"]["label_seeds"] == list(SD.LABEL_SEEDS)
    assert "evaluation_block_sha256" not in prov["completion"] and "not run in this process" in \
        prov["full_completion_verification"]
    text = (out / "rows.jsonl").read_text()
    from r1.c3.train.run import EVAL_COLUMNS
    keys = {k for line in text.splitlines() for k in SD._all_keys(json.loads(line))}
    assert "EVIDENCE" not in text and "evaluation" not in text and not any(EVAL_COLUMNS.search(k) for k in keys)


def test_label_block_source_sweep2_plugs_in_with_the_same_format(sweep, tmp_path, monkeypatch):
    d8 = []
    monkeypatch.setattr(SD, "require_d8_confirmation", lambda: d8.append(1))
    block = _label_block(sweep, tmp_path / "audit2", schema="r1.c3_audit_completion/sweep2-1", index_sha256="2" * 64)
    src = SD.LabelBlockSource(block, sweep="sweep2", index_sha256="2" * 64)
    m = SD.build_sft_data(sweep["rows"], src, _prompts(sweep), tmp_path / "data2")
    assert m["labels"]["sweep"] == "sweep2" and m["counts"]["train"] > 0 and d8          # the D8 guard ran


def test_r1_bx_d8_guards_the_new_loaders(sweep, tmp_path, monkeypatch, opened):
    """Review round 1, F1: without R1-BX-D8-CONFIRM, a sweep-2 label block and an unknown-provenance table are
    refused before any label byte is read."""
    from r1.c3 import analysis_guard
    def stop():
        raise RuntimeError("STOP: R1-BX-D8-CONFIRM missing (test)")
    monkeypatch.setattr(SD, "require_d8_confirmation", stop)
    monkeypatch.setattr(analysis_guard, "require_d8_confirmation", stop)
    block = _label_block(sweep, tmp_path / "audit2", index_sha256="2" * 64)
    t = tmp_path / "table"
    t.mkdir()
    (t / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sweep["rows"]))
    opened.clear()
    with pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):
        SD.LabelBlockSource(block, sweep="sweep2").label_records()
    with pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):
        SD.LabelBlockSource(block, sweep="sweep1").label_records()    # a non-sweep-1 index is guarded too
    with pytest.raises(RuntimeError, match="R1-BX-D8-CONFIRM"):
        SD.load_table(t)
    names = {Path(x).name for x in opened}
    assert "label_block.jsonl" not in names and "proposals.jsonl" not in names


def test_sealed_paths_and_sweep_binding_refused(sweep, tmp_path):
    sealed = tmp_path / "r1_sealed" / "a"
    block = _label_block(sweep, sealed)
    with pytest.raises(RuntimeError, match="r1_sealed"):
        SD.LabelBlockSource(block)
    block = _label_block(sweep, tmp_path / "a")
    with pytest.raises(SD.SFTDataError, match="belongs to sweep1, not sweep2"):
        SD.LabelBlockSource(block, sweep="sweep2").label_records()
    with pytest.raises(SD.SFTDataError, match="another sweep index"):
        SD.LabelBlockSource(block, index_sha256="0" * 64).label_records()
    with pytest.raises(SD.SFTDataError, match="another classification"):
        SD.LabelBlockSource(block, classification_sha256="0" * 64).label_records()
    (tmp_path / "a" / "audits.jsonl").write_text("{}\n")
    with pytest.raises(SD.SFTDataError, match="mixed audits.jsonl"):
        SD.LabelBlockSource(block).label_records()
    block = _label_block(sweep, tmp_path / "b", index_sha256="")
    with pytest.raises(SD.SFTDataError, match="no index_sha256"):
        SD.LabelBlockSource(block).label_records()


@pytest.mark.parametrize("case,match", [
    ("eval_path", "never opens"),
    ("wrong_name", "label_block.jsonl"),
    ("stop", "STOP.json"),
    ("seeds", "label seeds"),
    ("sha", "differs from the completion"),
    ("extra_key", "outside the label-block schema"),
    ("eval_seeds_row", "7001-7005"),
    ("soft_eval_key", "evaluation-column names"),
    ("dup", "duplicate proposal id"),
    ("schema", "not an audit completion"),
    ("no_completion", "completion record"),
])
def test_label_block_source_refusals(sweep, tmp_path, case, match):
    a = tmp_path / "audit"
    if case == "eval_path":
        _label_block(sweep, a)
        with pytest.raises(SD.SFTDataError, match=match):
            SD.LabelBlockSource(a / "evaluation_block.jsonl")
        with pytest.raises(SD.SFTDataError, match=match):
            SD.LabelBlockSource(a / "label_block.jsonl", completion=a / "runs.jsonl")
        return
    if case == "wrong_name":
        _label_block(sweep, a)
        (a / "labels.jsonl").write_text((a / "label_block.jsonl").read_text())
        with pytest.raises(SD.SFTDataError, match=match):
            SD.LabelBlockSource(a / "labels.jsonl")
        return
    mutate = {"extra_key": lambda L: L[0].update({"delta_evaluation": 1.0}),
              "eval_seeds_row": lambda L: next(x for x in L if x["label_kind"] == "audit").update(
                  {"seeds": [7006, 7007, 7008, 7009, 7010]}),
              "soft_eval_key": lambda L: next(x for x in L if x["label_kind"] == "audit")["soft_parameters"].update(
                  {"y_eval": 1.0}),
              "dup": lambda L: L.append(dict(L[0]))}.get(case)
    block = _label_block(sweep, a, schema="other/1" if case == "schema" else "r1.c3_audit_completion/3",
                         seeds=(7001, 7002, 7003, 7004, 7006) if case == "seeds" else SD.LABEL_SEEDS, mutate=mutate)
    if case == "stop":
        (a / "STOP.json").write_text("{}")
    if case == "sha":
        block.write_text(block.read_text() + "\n")
    if case == "no_completion":
        (a / "evidence_completion.json").rename(a / "moved_aside.json")
    with pytest.raises(SD.SFTDataError, match=match):
        SD.LabelBlockSource(block).label_records()


def test_label_block_outside_table_refused(sweep, tmp_path):
    block = _label_block(sweep, tmp_path / "a", mutate=lambda L: L.append(
        {"proposal_id": "c3_other:x__s1:t002", "node": NODE, "label_kind": "rule_noop", "delta_label": 0.0,
         "se_label": 0.0, "soft_parameters": {"inert": True}}))
    with pytest.raises(SD.SFTDataError, match="not in the table"):
        SD.build_sft_data(sweep["rows"], SD.LabelBlockSource(block), _prompts(sweep), tmp_path / "o")


# ---------------------------------------------------------------------------------------------- splits & build

def test_assign_splits_per_node_and_deterministic():
    insts = [f"{n}__s{k}" for n in ("digits_mlp", "tabular_mlp") for k in range(18)]
    a, b = SD.assign_splits(insts), SD.assign_splits(list(reversed(insts)))
    assert a == b
    for n in ("digits_mlp", "tabular_mlp"):
        got = [a[i] for i in insts if i.startswith(n)]
        assert got.count("test") == 3 and got.count("val") == 3 and got.count("train") == 12
    lono = SD.assign_splits(insts, {"holdout_nodes": ["tabular_mlp"]})
    assert all(lono[i] == "test" for i in insts if i.startswith("tabular_mlp"))
    assert SD.assign_splits(insts, {"salt": "other"}) != a
    with pytest.raises(SD.SFTDataError, match="instances"):
        SD.assign_splits(insts[:6])
    with pytest.raises(SD.SFTDataError, match="holdout"):
        SD.assign_splits(insts, {"holdout_nodes": ["openml_sonar"]})


def test_split_assignment_is_fixed_by_the_universe_not_the_table():
    """Review round 1, F3: dropping or missing an instance in one table moves no other instance."""
    universe = SD.instance_universe(["digits_mlp", "tabular_mlp"], 18)
    full = SD.assign_splits(universe, universe=universe)
    for drop in universe[:6]:
        part = SD.assign_splits([i for i in universe if i != drop], universe=universe)
        assert all(part[i] == full[i] for i in part)
    with pytest.raises(SD.SFTDataError, match="outside the split universe"):
        SD.assign_splits(["digits_mlp__s999"], universe=universe)
    assert len(universe) == 36 and "digits_mlp__s104" in universe


def test_build_synthetic_data_directory(sweep, tmp_path):
    out = tmp_path / "data"
    m = SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"]), _prompts(sweep), out)
    rows = [json.loads(x) for x in (out / "rows.jsonl").read_text().splitlines()]
    splits = json.loads((out / "splits.json").read_text())["instances"]
    assert len(splits["test"]) == 3 and len(splits["val"]) == 3 and len(splits["train"]) == 3
    assert {r["split"] for r in rows} == {"train", "val"}
    assert not {r["instance"] for r in rows} & set(splits["test"])
    test_keys = {SD.dup_key(r) for r in sweep["rows"] if r["instance"] in splits["test"]}
    val_keys = {r["dup_key"] for r in rows if r["split"] == "val"}
    assert not {r["dup_key"] for r in rows} & test_keys
    assert not {r["dup_key"] for r in rows if r["split"] == "train"} & val_keys
    c = m["counts"]
    assert c["table_rows_without_label"] == sum(r["duplicate"] for r in sweep["rows"]) and m["table_matches_audit_table"] is None
    assert c["labelled_test_proposals"] == c["test_rows_withheld"] and \
        c["labelled_test_seen_in_train_or_val"] <= c["labelled_test_proposals"]
    sp = json.loads((out / "splits.json").read_text())
    assert sp["universe"]["n"] == 9 and "dry run" in sp["universe"]["source"]
    assert c["train"] + c["val"] + c["test_rows_withheld"] + c["dropped_dup_of_test"] + c["dropped_dup_of_val"] \
        == c["labelled"]
    assert c["rule_noop"] > 0 and all(abs(sum(r["y"]) - 1) < 1e-9 for r in rows)
    assert m["prompt_version"] == PROMPT_VERSION and m["featurizer_version"] == F.FEATURIZER_VERSION
    assert m["soft_label_version"] == "soft_label/v2_pooled_node" and "ENGINEERING_ONLY" in m["label_status"]
    train, val, _ = SD.load_sft_data(out)
    assert len(train) == c["train"] and len(val) == c["val"] and train[0]["y"].dtype == torch.float32
    with pytest.raises(SD.SFTDataError, match="not empty"):
        SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"]), _prompts(sweep), out)
    (out / "rows.jsonl").write_text((out / "rows.jsonl").read_text().replace('"val"', '"train"', 1))
    with pytest.raises(SD.SFTDataError, match="sha256"):
        SD.load_sft_data(out)


# ---------------------------------------------------------------------------------------------- Stage S runner

def _data(sweep, tmp_path):
    out = tmp_path / "data"
    SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"], shift_z=1.5), _prompts(sweep), out)
    return SD.load_sft_data(out)


def test_stage_s_dry_run_on_cpu(sweep, tmp_path):
    train, val, _ = _data(sweep, tmp_path)
    model = tiny.build_hashbag(seed=0)
    proto = {**SFT.DEFAULT_PROTOCOL, "micro_batch": 4}
    from r1.c3.train.model import new_head_parameters
    rep = SFT.run_stage_s(model, train, val, tmp_path / "run", proto, lr=1e-4, seed=0,
                          head_params=new_head_parameters(model), max_steps=12, eval_every_steps=3, log=lambda s: None,
                          data_sha256="d" * 64, label_status="synthetic")
    assert rep["protocol_deviation"] == {"max_steps": 12, "eval_every_steps": 3} and rep["data_sha256"] == "d" * 64
    assert rep["train"]["completed"] and rep["n_train"] == len(train)
    assert rep["protocol"]["effective_batch"] == 16 and rep["total_steps"] == min(12, 5 * rep["steps_per_epoch"])
    sel = rep["selected"]
    for k in ("val_rps", "val_rps_skill", "val_nll", "val_ece_all_bins", "val_ece_top1", "val_width_ratio"):
        assert np.isfinite(sel[k])
    assert len(sel["val_pit_histogram"]) == 10
    assert abs(sel["val_rps"] - rep["train"]["best_value"]) < 1e-6        # the best checkpoint, not the last
    assert rep["temperature"] > 0 and (tmp_path / "run" / "best" / "temperature.json").is_file()
    evals = [json.loads(x) for x in (tmp_path / "run" / "metrics.jsonl").read_text().splitlines()
             if json.loads(x)["kind"] == "eval"]
    assert evals[0]["step"] == 0 and len(evals) >= 3
    assert rep["selected_temperature_scaled"]["val_nll"] <= sel["val_nll"] + 1e-6
    assert np.load(tmp_path / "run" / "pred_val_logits.npy").shape == (len(val), 12)


def test_stage_s_refusals(sweep, tmp_path):
    train, val, _ = _data(sweep, tmp_path)
    with pytest.raises(ValueError, match="grid"):
        SFT.run_stage_s(tiny.build_hashbag(), train, val, tmp_path / "r1", {}, lr=2e-4, seed=0)
    with pytest.raises(ValueError, match="divide"):
        SFT.run_stage_s(tiny.build_hashbag(), train, val, tmp_path / "r2", {"micro_batch": 5}, lr=1e-4, seed=0)
    leaky = [{**train[0], "y_eval": train[0]["y"]}] + train[1:]
    with pytest.raises(TrackPStop, match="evaluation-seed columns"):
        SFT.run_stage_s(tiny.build_hashbag(), leaky, val, tmp_path / "r3", {}, lr=1e-4, seed=0, max_steps=1)


def _report(d, lr, seed, v, **more):
    d.mkdir(parents=True)
    (d / "sft_report.json").write_text(json.dumps({"lr": lr, "seed": seed, "train": {"best_value": v},
                                                   "data_sha256": "d",
                                                   "protocol": {"loss": "rps+ce", "lr_grid": [1e-5, 3e-5, 1e-4]},
                                                   "label_status": "ENGINEERING_ONLY", **more}))
    return d


def test_select_lr(tmp_path):
    runs = [_report(tmp_path / f"{lr}_{s}", lr, s, v) for lr, vals in
            ((1e-5, [0.3, 0.32, 0.31]), (3e-5, [0.2, 0.25, 0.24]), (1e-4, [0.22, 0.21, 0.2])) for s, v in enumerate(vals)]
    rep = SFT.select_lr(runs)
    assert rep["selected_lr"] == 1e-4 and rep["label_status"] == "ENGINEERING_ONLY"
    with pytest.raises(ValueError, match="3 distinct seeds"):
        SFT.select_lr(runs[:-1])
    with pytest.raises(ValueError, match="not the whole grid"):
        SFT.select_lr(runs[3:])
    with pytest.raises(ValueError, match="appears twice"):
        SFT.select_lr(runs + [_report(tmp_path / "dup", 1e-4, 0, 0.1)])
    with pytest.raises(ValueError, match="differ in data_sha256"):
        SFT.select_lr(runs[:-1] + [_report(tmp_path / "other", 1e-4, 2, 0.2, data_sha256="e")])
    with pytest.raises(ValueError, match="deviates from the protocol"):
        SFT.select_lr(runs[:-1] + [_report(tmp_path / "dev", 1e-4, 2, 0.2, protocol_deviation={"max_steps": 3})])


def test_ce_only_ablation_and_resume_bound_to_data(sweep, tmp_path):
    train, val, _ = _data(sweep, tmp_path)
    y = torch.stack([r["y"] for r in train[:4]])
    out = {"belief_logits": torch.zeros(4, 12)}
    ce = SFT.stage_s_loss_fn("ce")(out, train[:4])
    assert torch.isclose(ce, -(y * torch.log(torch.full((4, 12), 1 / 12))).sum(-1).mean())
    with pytest.raises(ValueError, match="unknown Stage S loss"):
        SFT.stage_s_loss_fn("hinge")
    run = tmp_path / "run_resume"
    SFT.run_stage_s(tiny.build_hashbag(), train, val, run, {"micro_batch": 4}, lr=1e-4, seed=0, max_steps=2,
                    data_sha256="a" * 64, log=lambda s: None)
    with pytest.raises(RuntimeError, match="different training config"):
        SFT.run_stage_s(tiny.build_hashbag(), train, val, run, {"micro_batch": 4}, lr=1e-4, seed=0, max_steps=2,
                        data_sha256="b" * 64, log=lambda s: None)


# ---------------------------------------------------------------------------------------------- CLI

def test_cli_dry_run_end_to_end(sweep, tmp_path, monkeypatch, capsys):
    import importlib.util
    from r1.harness import REPO
    spec = importlib.util.spec_from_file_location("trackp_cli", REPO / "r1" / "scripts" / "trackp.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(D, "sweep_replay_inputs", lambda *a, **k: sweep["inputs"])
    t = tmp_path / "table"
    t.mkdir()
    (t / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sweep["rows"]))
    data_run = tmp_path / "sft_data"
    rc = cli.main(["sft-data", "--table", str(t), "--table-pin", "none", "--sweep", str(sweep["tmp"] / "index.json"),
                   "--labels", "synthetic", "--tokenizers", "whitespace", "--run-dir", str(data_run)])
    assert rc == 0
    assert json.loads((data_run / "manifest.json").read_text())["evidence_label"] == "ENGINEERING_ONLY"
    capsys.readouterr()

    def stop(argv, text):
        assert cli.main(argv) == 2
        err = capsys.readouterr().err
        assert text in err, err
    # the pinned sweep-1 table refuses this synthetic table
    (tmp_path / "class.json").write_text("{}")
    stop(["sft-data", "--table", str(t), "--sweep", "x", "--labels", "synthetic", "--tokenizers", "pool",
          "--classification", str(tmp_path / "class.json"), "--run-dir", str(tmp_path / "d2")], "!= pinned")
    # a pinned sweep-1 table needs its classification sidecar (the label block is bound to it)
    stop(["sft-data", "--table", str(t), "--sweep", "x", "--labels", "synthetic", "--tokenizers", "pool",
          "--run-dir", str(tmp_path / "d2b")], "pass --classification")
    stop(["spike", "--tiny", "--family", "hashbag", "--allow-placeholders", "--run-dir", str(tmp_path / "sp")],
         "serves sft-dev only")
    # real labels need a pinned table, and the pool tokenizers
    stop(["sft-data", "--table", str(t), "--table-pin", "none", "--sweep", "x", "--labels",
          str(tmp_path / "label_block.jsonl"), "--run-dir", str(tmp_path / "d3")], "unpinned table")
    stop(["sft-data", "--table", str(t), "--sweep", "x", "--labels", str(tmp_path / "label_block.jsonl"),
          "--tokenizers", "whitespace", "--run-dir", str(tmp_path / "d4")], "whitespace is for synthetic")
    stop(["sft-data", "--table", str(t), "--table-pin", "nope", "--sweep", "x", "--labels", "synthetic",
          "--run-dir", str(tmp_path / "d5")], "unknown --table-pin")
    run = tmp_path / "sft_dev"
    rc = cli.main(["sft-dev", "--data", str(data_run / "data"), "--tiny", "--family", "hashbag", "--lr", "1e-4",
                   "--steps", "6", "--eval-every", "3", "--allow-placeholders", "--run-dir", str(run)])
    assert rc == 0
    man = json.loads((run / "manifest.json").read_text())
    rep = json.loads((run / "report.json").read_text())
    assert man["evidence_label"] == "DRYRUN" and man["subcommand"] == "sft-dev"
    assert man["model_files_sha256"]["heads.pt"] and rep["data"]["labels"] == "synthetic"
    assert rep["protocol_deviation"] == {"max_steps": 6, "eval_every_steps": 3}
    # one run is not a grid (3 seeds per lr), and a protocol deviation is refused: STOP, not a traceback
    stop(["sft-select", "--runs", str(run), "--run-dir", str(tmp_path / "sel")], "deviates from the protocol")
    # resuming the run directory with another lr is a STOP, not a traceback
    stop(["sft-dev", "--data", str(data_run / "data"), "--tiny", "--family", "hashbag", "--lr", "3e-5",
          "--steps", "6", "--eval-every", "3", "--allow-placeholders", "--run-dir", str(run)], "different training config")
    # sft-dev is ENGINEERING only: refused before the environment check
    def no_env(cfg):
        raise AssertionError("environment check reached")
    monkeypatch.setattr(cli.R, "check_environment", no_env)
    stop(["sft-dev", "--data", str(data_run / "data"), "--base", "kev-0.8b", "--lr", "1e-4", "--evidence", "EVIDENCE",
          "--run-dir", str(tmp_path / "e2")], "sft-dev is ENGINEERING_ONLY")
    # P.4 `sft` stays "not yet" in this unit, even with an authorization note present
    monkeypatch.setattr(cli.R, "authorization_note", lambda phase: Path("/x/trackp_p4_note.md"))
    stop(["sft", "--data", str(data_run / "data"), "--base", "kev-0.8b", "--lr", "1e-4", "--evidence", "EVIDENCE",
          "--run-dir", str(tmp_path / "p4")], "not enabled in this unit")


def test_htcondor_config_runs_the_qtorch_checks_and_skips_the_portal_schedule(monkeypatch):
    from r1.harness import REPO
    from r1.c3.train import run as R
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_htcondor_v2.json").read_text())
    portal = json.loads((REPO / "r1/scripts/configs/trackp_portal.json").read_text())
    for key in ("spike", "toy_batch", "e0", "e3", "kev_temperature"):
        assert cfg[key] == portal[key]
    assert "TODO_VERIFY_ON_HOST" in cfg["venv"]["causal_conv1d"] and cfg["lease"] == "htcondor_slot"
    assert R.track_x_running("") is False      # the empty schedule the lease receives on an HTCondor slot


def test_manifest_records_whether_the_audit_table_is_this_table(sweep, tmp_path):
    block = _label_block(sweep, tmp_path / "a")
    prompts = _prompts(sweep)
    same = SD.build_sft_data(sweep["rows"], SD.LabelBlockSource(block), prompts, tmp_path / "o1",
                             table_record={"sha256": {"proposals.jsonl": "p" * 64}})
    other = SD.build_sft_data(sweep["rows"], SD.LabelBlockSource(block), prompts, tmp_path / "o2",
                              table_record={"sha256": {"proposals.jsonl": "q" * 64}})
    assert same["table_matches_audit_table"] is True and other["table_matches_audit_table"] is False


def test_exclude_from_heldout_keeps_train_and_cleans_val_and_test(sweep, tmp_path):
    prompts = _prompts(sweep)
    a = SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"]), prompts, tmp_path / "a")
    b = SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"]), prompts, tmp_path / "b",
                          split_cfg={"cross_split_duplicates": "exclude_from_heldout"})
    assert b["counts"]["train"] >= a["counts"]["train"] and b["counts"]["dropped_dup_of_test"] == 0
    rows = [json.loads(x) for x in (tmp_path / "b" / "rows.jsonl").read_text().splitlines()]
    train_keys = {SD.dup_key(r) for r in sweep["rows"] if r["instance"] in
                  json.loads((tmp_path / "b" / "splits.json").read_text())["instances"]["train"]}
    assert not {r["dup_key"] for r in rows if r["split"] == "val"} & train_keys
    sp = json.loads((tmp_path / "b" / "splits.json").read_text())
    assert len(sp["test_proposals_seen_in_train_or_val"]) == b["counts"]["test_rows_seen_in_train_or_val"]
    assert json.loads((tmp_path / "a" / "splits.json").read_text())["test_proposals_seen_in_train_or_val"] is None
    with pytest.raises(SD.SFTDataError, match="policy"):
        SD.build_sft_data(sweep["rows"], SD.SyntheticLabelSource(sweep["rows"]), prompts, tmp_path / "c",
                          split_cfg={"cross_split_duplicates": "merge"})
