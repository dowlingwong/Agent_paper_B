"""Track P on P3 (PRE-SPLIT A) and the P.3b exam set inside P3 train: synthetic records only, no label file."""
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

import pytest

from r1.c3 import p3_split
from r1.c3.train import exam_set as X
from r1.c3.train import sft_data as SD
from r1.harness import REPO

sys.path.insert(0, str(Path(__file__).parent))
import test_gate_input_builder as W  # noqa: E402  (synthetic world: design instances of the eight T0 nodes)

SPLIT_FILE = {"path": "r1/c3/splits/c3_p3_split_v1.json", "sha256": p3_split.P3_SPLIT_SHA256}
ASSIGN = p3_split.assignment(p3_split.load())


@pytest.fixture(scope="module")
def rows():
    return W._world()[0][0].rows


def test_split_file_mode_is_the_p3_assignment():
    insts = sorted(ASSIGN)
    got = SD.assign_splits(insts, {"split_file": SPLIT_FILE})
    assert got == {i: {"dev": "val"}.get(v["split"], v["split"]) for i, v in ASSIGN.items()}
    held = SD.assign_splits(insts, {"split_file": SPLIT_FILE, "holdout_nodes": ["openml_sonar"]})
    assert all(held[i] == "test" for i in insts if i.startswith("openml_sonar__s"))
    assert all(held[i] == got[i] for i in insts if not i.startswith("openml_sonar__s"))


@pytest.mark.parametrize("cfg,universe,match", [
    ({"split_file": SPLIT_FILE, "salt": "trackp_sft/v1"}, None, "excludes"),
    ({"split_file": SPLIT_FILE, "test_instances_per_node": 9}, None, "excludes"),
    ({"split_file": SPLIT_FILE}, ["digits_mlp__s104", "digits_mlp__s9011"], "universe outside the P3 split file"),
    ({"split_file": SPLIT_FILE}, ["openml_breast_w__s125"], "instances outside the given universe"),
    ({"split_file": {**SPLIT_FILE, "sha256": "0" * 64}}, None, "not the signed P3 split file"),
    ({"split_file": {"path": SPLIT_FILE["path"]}}, None, "path, sha256"),
    ({"split_file": SPLIT_FILE, "holdout_nodes": ["nope"]}, None, "holdout nodes not in the split file"),
])
def test_split_file_refusals(cfg, universe, match):
    with pytest.raises(SD.SFTDataError, match=match):
        SD.assign_splits(["digits_mlp__s104"], cfg, universe)


def test_an_instance_outside_the_split_file_and_an_altered_file_are_refused(tmp_path, monkeypatch):
    with pytest.raises(SD.SFTDataError, match="outside the P3 split file"):
        SD.assign_splits(["digits_mlp__s9011"], {"split_file": SPLIT_FILE})
    fake = tmp_path / "repo"
    (fake / "r1/c3/splits").mkdir(parents=True)
    (fake / SPLIT_FILE["path"]).write_bytes((REPO / SPLIT_FILE["path"]).read_bytes().replace(b'"test"', b'"Test"', 1))
    import r1.harness
    monkeypatch.setattr(r1.harness, "REPO", fake)
    with pytest.raises(SD.SFTDataError, match="not the pinned P3 split file"):
        SD.assign_splits(["digits_mlp__s104"], {"split_file": SPLIT_FILE})


def test_the_track_p_config_binds_the_p3_split_file():
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_sft.json").read_text())
    sp = cfg["splits"]
    assert sp["split_file"] == SPLIT_FILE and not ({"salt", "universe", "test_instances_per_node"} & set(sp))
    assert sp["cross_split_duplicates"] == SD.DECIDED_DUPLICATE_POLICY and sp["holdout_nodes"] == []


def test_an_sft_build_on_p3_holds_no_test_instance_row(rows, tmp_path):
    import dataclasses

    @dataclasses.dataclass
    class Prompt:
        text: str
    prompts = {r["proposal_id"]: (Prompt("prompt"), r["features"]) for r in rows}
    man = SD.build_sft_data(rows, SD.SyntheticLabelSource(rows), prompts, tmp_path / "data",
                            split_cfg={"split_file": SPLIT_FILE})
    splits = json.loads((tmp_path / "data" / "splits.json").read_text())
    assert splits["universe"]["source"].startswith("the signed P3 split file")
    assert splits["config"]["split_file"] == SPLIT_FILE
    out = [json.loads(l) for l in (tmp_path / "data" / "rows.jsonl").read_text().splitlines()]
    assert out and all(ASSIGN[r["instance"]]["split"] in ("train", "dev") for r in out)
    assert {r["split"] for r in out} <= {"train", "val", "val_seen"}
    assert all(ASSIGN[r["instance"]]["split"] == ("dev" if r["split"] in ("val", "val_seen") else "train") for r in out)
    assert man["counts"]["test_rows_withheld"] > 0


# ---------------------------------------------------------------------------------------------------- exam set

def _big(rows, campaigns_per_instance=1):
    """More proposals per campaign so that the 400-proposal target is reachable on P3 train."""
    out = []
    for r in rows:
        out.append(r)
        if not (r["noop"] or r["duplicate"]):
            for j in range(3):
                q = dict(r)
                q["proposal_id"] = r["proposal_id"] + f"x{j}"
                q["incumbent_hash"], q["candidate_hash"] = q["proposal_id"] + ":i", q["proposal_id"] + ":c"
                out.append(q)
    return out


def test_exam_set_lies_in_p3_train_and_meets_the_spec(rows):
    big = _big(rows)
    ex = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    assert ex["schema"] == X.SCHEMA and ex["split_file"]["sha256"] == p3_split.P3_SPLIT_SHA256
    assert all(ASSIGN[v["instance"]]["split"] == "train" for v in ex["items"].values())    # never dev or test
    by_pid = {r["proposal_id"]: r for r in big}
    assert not any(by_pid[p]["noop"] or by_pid[p]["duplicate"] for p in ex["items"])        # audited proposals only
    assert X.TARGET_MIN <= ex["counts"]["items"] and len(ex["nodes"]) >= X.MIN_NODES and not ex["below_target"]
    chosen = ex["instances"]["exam_train"] + ex["instances"]["exam_val"]
    assert len(ex["instances"]["exam_train"]) == (7 * len(chosen) + 5) // 10
    # the shortest qualifying prefix of the salted instance order
    eligible = sorted({p3_split.instance_id(r["node"], r["instance_seed"]) for r in big if not (r["noop"] or r["duplicate"])
                       and ASSIGN[p3_split.instance_id(r["node"], r["instance_seed"])]["split"] == "train"},
                      key=lambda i: hashlib.sha256(f"trackp_exam/v1:{i}".encode()).hexdigest())
    assert chosen == eligible[:len(chosen)]
    n_prev = sum(1 for r in big if not (r["noop"] or r["duplicate"])
                 and p3_split.instance_id(r["node"], r["instance_seed"]) in chosen[:-1])
    assert n_prev < X.TARGET_MIN or len({ASSIGN[i]["node"] for i in chosen[:-1]}) < X.MIN_NODES


def test_exam_val_repeats_of_exam_train_are_val_seen(rows):
    big = _big(rows)
    ex = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    tr, va = ex["instances"]["exam_train"][0], ex["instances"]["exam_val"][0]
    big2 = copy.deepcopy(big)
    src = next(r for r in big2 if p3_split.instance_id(r["node"], r["instance_seed"]) == tr)
    dst = next(r for r in big2 if p3_split.instance_id(r["node"], r["instance_seed"]) == va
               and not (r["noop"] or r["duplicate"]) and r["node"] == src["node"]) if \
        ASSIGN[tr]["node"] == ASSIGN[va]["node"] else None
    if dst is None:                                       # pick an exam-val instance of the same node as an exam-train one
        pairs = [(t, v) for t in ex["instances"]["exam_train"] for v in ex["instances"]["exam_val"]
                 if ASSIGN[t]["node"] == ASSIGN[v]["node"]]
        tr, va = pairs[0]
        src = next(r for r in big2 if p3_split.instance_id(r["node"], r["instance_seed"]) == tr)
        dst = next(r for r in big2 if p3_split.instance_id(r["node"], r["instance_seed"]) == va
                   and not (r["noop"] or r["duplicate"]))
    dst["incumbent_hash"], dst["candidate_hash"] = src["incumbent_hash"], src["candidate_hash"]
    ex2 = X.draw(big2, source="sweep1", proposals_sha256="a" * 64)
    assert ex2["items"][dst["proposal_id"]]["exam_split"] == "val_seen"
    assert ex2["counts"]["by_split"]["val_seen"] == ex["counts"]["by_split"]["val_seen"] + 1


def test_exam_set_is_deterministic_and_refuses_bad_input(rows, tmp_path):
    big = _big(rows)
    a = X.render(X.draw(big, source="sweep1", proposals_sha256="a" * 64))
    shuffled = list(big)
    random.Random(4).shuffle(shuffled)
    assert X.render(X.draw(shuffled, source="sweep1", proposals_sha256="a" * 64)) == a
    small = X.draw(rows[:200], source="sweep1", proposals_sha256="a" * 64)
    assert small["below_target"] is True                  # too few P3 train proposals: flagged, the author decides
    with pytest.raises(X.ExamSetError, match="EX-SOURCE"):
        X.draw(big, source="sweep3", proposals_sha256="a" * 64)
    bad = copy.deepcopy(big[:5])
    bad[0]["instance_seed"] = 9011
    bad[0]["instance"] = f"{bad[0]['node']}__s9011"
    with pytest.raises(X.ExamSetError, match="not in the P3 split file"):
        X.draw(bad, source="sweep1", proposals_sha256="a" * 64)
    with pytest.raises(X.ExamSetError, match="duplicate proposal id"):
        X.draw(big[:3] + big[:1], source="sweep1", proposals_sha256="a" * 64)


def _decision_prompts(rows):
    p = SD.DecisionPrompt(state="state", proposal="proposal", question="question", options=("a", "b"))
    return {r["proposal_id"]: (p, r["features"]) for r in rows}


def _p3_build(rows, out, label_source=None):
    prompts = _decision_prompts(rows)
    return SD.build_sft_data(rows, label_source or SD.SyntheticLabelSource(rows), prompts, out,
                             split_cfg={"split_file": SPLIT_FILE})


def test_p4_recomputation_of_a_p3_build(rows, tmp_path):
    """Review round 1, B1: the P.4 evaluator recomputes the assignment as assign_splits(union, config,
    universe=union) over the recorded instances; a P3 build passes it. m5: the recorded universe is the P3 file's
    instances of the table's nodes (the T0 tier here), not all 240."""
    _p3_build(rows, tmp_path / "data")
    splits = json.loads((tmp_path / "data" / "splits.json").read_text())
    union = sorted(i for s_ in splits["instances"].values() for i in s_)
    nodes = {r["node"] for r in rows}
    assert union == SD.p3_universe(nodes) and splits["universe"]["n"] == len(union) == 18 * len(nodes)
    assert not any(ASSIGN[i]["node"] not in nodes for i in union)
    again = SD.assign_splits(union, splits["config"], universe=union)
    assert all(again[i] == s_ for s_, insts in splits["instances"].items() for i in insts)


class _RealLooking(SD.SyntheticLabelSource):
    def provenance(self):
        return {**super().provenance(), "kind": "label_block"}


def test_real_labels_are_built_and_loaded_only_on_the_signed_split_file(rows, tmp_path):
    """Review round 1, M1: a non-synthetic label source is refused without the signed split_file, at build and at
    load; on P3 it builds and loads."""
    prompts = _decision_prompts(rows)
    for cfg in (None, {"salt": "trackp_sft/v1"}, {"split_file": {**SPLIT_FILE, "sha256": "1" * 64}}):
        with pytest.raises(SD.SFTDataError, match="signed P3 split file|not the signed P3 split file"):
            SD.build_sft_data(rows, _RealLooking(rows), prompts, tmp_path / "x", split_cfg=cfg)
    _p3_build(rows, tmp_path / "p3", _RealLooking(rows))
    assert json.loads((tmp_path / "p3" / "sft_data.json").read_text())["labels"]["kind"] == "label_block"
    pytest.importorskip("torch")
    SD.load_sft_data(tmp_path / "p3")
    # a salt-split directory relabelled as real (the pre-signature trackp_sft/v1 trial's shape) is refused at load
    SD.build_sft_data(rows, SD.SyntheticLabelSource(rows), prompts, tmp_path / "salt",
                      split_cfg={"cross_split_duplicates": SD.DECIDED_DUPLICATE_POLICY})
    man = json.loads((tmp_path / "salt" / "sft_data.json").read_text())
    man["labels"] = {**man["labels"], "kind": "label_block"}
    (tmp_path / "salt" / "sft_data.json").write_text(json.dumps(man))
    with pytest.raises(SD.SFTDataError, match="not built on the signed P3 split file"):
        SD.load_sft_data(tmp_path / "salt")


def test_the_cli_binds_p3_for_a_pinned_table_and_refuses_a_config_without_it(rows, tmp_path, monkeypatch, capsys):
    """m7: a pinned sft-data build passes the signed split_file to build_sft_data (universe None: the P3 file's
    instances of the table's nodes); an SFT config without it is a STOP before any table or label is opened."""
    import importlib.util
    from r1.c3 import dataset as D
    spec = importlib.util.spec_from_file_location("trackp_cli_p3", REPO / "r1" / "scripts" / "trackp.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    table = tmp_path / "table"
    table.mkdir()
    (table / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    sha = hashlib.sha256((table / "proposals.jsonl").read_bytes()).hexdigest()
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_sft.json").read_text())
    cfg["tables"] = {"synth": {"sha256": {"proposals.jsonl": sha}}}
    (tmp_path / "cfg.json").write_text(json.dumps(cfg))
    seen = {}
    monkeypatch.setattr(D, "sweep_replay_inputs", lambda *a, **k: {"index_path": str(tmp_path / "cfg.json")})
    monkeypatch.setattr(SD, "sweep_prompts", lambda *a, **k: {})

    def fake_build(rows_, source, prompts, out, **kw):
        seen.update(kw)
        raise SystemExit(0)
    monkeypatch.setattr(SD, "build_sft_data", fake_build)
    argv = ["sft-data", "--table", str(table), "--table-pin", "synth", "--sft-config", str(tmp_path / "cfg.json"),
            "--sweep", "x", "--labels", "synthetic", "--tokenizers", "whitespace", "--run-dir", str(tmp_path / "r")]
    with pytest.raises(SystemExit):
        cli.main(argv)
    assert seen["split_cfg"]["split_file"] == SPLIT_FILE and seen["universe"] is None
    assert not ({"salt", "universe", "test_instances_per_node"} & set(seen["split_cfg"]))
    del cfg["splits"]["split_file"]
    cfg["splits"]["salt"] = "trackp_sft/v1"
    (tmp_path / "cfg2.json").write_text(json.dumps(cfg))
    seen.clear()
    assert cli.main(argv[:6] + [str(tmp_path / "cfg2.json")] + argv[7:]) == 2
    assert "signed P3 split file" in capsys.readouterr().err and not seen


def _t1_rows(rows):
    """Copies of T0 rows moved onto T1 instances of the P3 file (draw must ignore them)."""
    t1 = sorted(i for i, v in ASSIGN.items() if v["tier"] == "T1")[:4]
    out = []
    for k, inst in enumerate(t1):
        for j, r in enumerate(rows[:30]):
            q = dict(r)
            q["node"], q["instance_seed"] = ASSIGN[inst]["node"], int(inst.rsplit("__s", 1)[1])
            q["instance"] = inst
            q["proposal_id"] = f"t1:{inst}:{j}"
            out.append(q)
    return out


def test_exam_ignores_t1_dev_and_test_rows(rows):
    """m7: T1, dev and test rows never enter or move the exam."""
    big = _big(rows)
    base = X.render(X.draw(big, source="sweep1", proposals_sha256="a" * 64))
    t1 = _t1_rows(rows)
    assert t1 and all(ASSIGN[r["instance"]]["tier"] == "T1" for r in t1)
    assert X.render(X.draw(big + t1, source="sweep1", proposals_sha256="a" * 64)) == base
    train_only = [r for r in big if ASSIGN[p3_split.instance_id(r["node"], r["instance_seed"])]["split"] == "train"]
    assert X.render(X.draw(train_only, source="sweep1", proposals_sha256="a" * 64)) == base


def test_a_rule_skip_exam_train_row_makes_val_seen(rows):
    """m7: the val_seen key set holds every table row of an exam-train instance, rule-skips included."""
    big = copy.deepcopy(_big(rows))
    ex = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    pairs = [(t, v) for t in ex["instances"]["exam_train"] for v in ex["instances"]["exam_val"]
             if ASSIGN[t]["node"] == ASSIGN[v]["node"]]
    tr, va = pairs[0]
    skip = next((r for r in big if p3_split.instance_id(r["node"], r["instance_seed"]) == tr
                 and (r["noop"] or r["duplicate"])), None)
    if skip is None:                         # make one: a duplicate row on the exam-train instance
        skip = dict(next(r for r in big if p3_split.instance_id(r["node"], r["instance_seed"]) == tr))
        skip["proposal_id"] += ":dup"
        skip["duplicate"] = True
        big.append(skip)
    assert skip["proposal_id"] not in X.draw(big, source="sweep1", proposals_sha256="a" * 64)["items"]
    dst = next(r for r in big if p3_split.instance_id(r["node"], r["instance_seed"]) == va
               and not (r["noop"] or r["duplicate"]))
    dst["incumbent_hash"], dst["candidate_hash"] = skip["incumbent_hash"], skip["candidate_hash"]
    ex2 = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    assert ex2["items"][dst["proposal_id"]]["exam_split"] == "val_seen"


def test_the_node_condition_extends_the_prefix_and_above_target_is_flagged(rows, monkeypatch):
    """m7: when the item target is met with too few nodes, the prefix grows; above_target is set past the max."""
    big = _big(rows)
    base = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    monkeypatch.setattr(X, "MIN_NODES", 7)
    ex = X.draw(big, source="sweep1", proposals_sha256="a" * 64)
    chosen = ex["instances"]["exam_train"] + ex["instances"]["exam_val"]
    assert len(ex["nodes"]) >= 7 and len(chosen) >= len(base["instances"]["exam_train"] + base["instances"]["exam_val"])
    n_prev = sum(1 for r in big if not (r["noop"] or r["duplicate"])
                 and p3_split.instance_id(r["node"], r["instance_seed"]) in chosen[:-1])
    assert len({ASSIGN[i]["node"] for i in chosen[:-1]}) < 7 or n_prev < X.TARGET_MIN
    monkeypatch.setattr(X, "TARGET_MAX", 10)
    assert X.draw(big, source="sweep1", proposals_sha256="a" * 64)["above_target"] is True
    assert base["above_target"] is (base["counts"]["items"] > 500)


def test_rounding_is_integer_half_up():
    """m1: (7 n + 5) // 10, not float rounding."""
    assert [(7 * n + 5) // 10 for n in (15, 35, 45, 1, 2)] == [11, 25, 32, 1, 1]


def test_check_labelled_stops_on_a_missing_member(rows):
    ex = X.draw(_big(rows), source="sweep1", proposals_sha256="a" * 64)
    X.check_labelled(ex, list(ex["items"]) + ["other"])
    with pytest.raises(X.ExamSetError, match="no y_train record"):
        X.check_labelled(ex, list(ex["items"])[1:])


def test_exam_cli_write_verify_pin_and_stops(rows, tmp_path, capsys):
    """m2, m3, m7: the CLI pins the table, binds the source to the pin, refuses to overwrite, refuses below target,
    and verify compares bytes."""
    def table(name, rs):
        d = tmp_path / name
        d.mkdir()
        (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs))
        return d, hashlib.sha256((d / "proposals.jsonl").read_bytes()).hexdigest()
    big_t, big_sha = table("big", _big(rows))
    small_t, small_sha = table("small", rows[:200])
    cfg = json.loads((REPO / "r1/scripts/configs/trackp_sft.json").read_text())
    cfg["tables"] = {"sweep1_synth": {"sha256": {"proposals.jsonl": big_sha}},
                     "sweep1_small": {"sha256": {"proposals.jsonl": small_sha}}}
    (tmp_path / "cfg.json").write_text(json.dumps(cfg))
    common = ["--sft-config", str(tmp_path / "cfg.json"), "--source", "sweep1"]
    out = tmp_path / "exam.json"
    assert X.main(["write", "--table", str(big_t), "--table-pin", "sweep1_synth", *common, "--out", str(out)]) == 0
    sha = capsys.readouterr().out.strip()
    assert sha == hashlib.sha256(out.read_bytes()).hexdigest()
    assert json.loads(out.read_text())["table_pin"] == "sweep1_synth"
    assert X.main(["write", "--table", str(big_t), "--table-pin", "sweep1_synth", *common, "--out", str(out)]) == 2
    assert "written once" in capsys.readouterr().err
    assert X.main(["verify", "--table", str(big_t), "--table-pin", "sweep1_synth", *common, "--file", str(out)]) == 0
    assert capsys.readouterr().out.startswith("OK " + sha)
    out.write_bytes(out.read_bytes().replace(b'"val"', b'"val_seen"', 1))
    assert X.main(["verify", "--table", str(big_t), "--table-pin", "sweep1_synth", *common, "--file", str(out)]) == 2
    capsys.readouterr()
    for argv, text in (
            (["--table", str(big_t), "--table-pin", "sweep1_small", *common], "!= pinned"),
            (["--table", str(big_t), "--table-pin", "nope", *common], "unknown table pin"),
            (["--table", str(big_t), "--table-pin", "sweep1_synth", "--sft-config", str(tmp_path / "cfg.json"),
              "--source", "sweep2"], "not the table pin's sweep"),
            (["--table", str(small_t), "--table-pin", "sweep1_small", *common], "below_target=True")):
        assert X.main(["write", *argv, "--out", str(tmp_path / "x.json")]) == 2
        assert text in capsys.readouterr().err
    assert not (tmp_path / "x.json").exists()
