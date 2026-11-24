"""T0 arms freeze (``r1.c3.arms_freeze``): synthetic tables and label rows only; no real table, label block,
evaluation block or receipt is opened. AI-assisted (Claude)."""
import copy
import json
import math
import random
import re

import numpy as np
import pytest

from r1.c3 import arms_freeze as AF
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split, release
from r1.c3.features import FEATURES, NODE_CODES
from r1.c3.labels import INERT, N_BINS
from r1.c3.train import metrics as M

SIG = 0.01
ASSIGN = p3_split.assignment(p3_split.load())
NODES = B.ALL_T0
BASE_COMMIT = "1402f466497c29638c53a3397f44ab9a3e6717ec"


def _features(node, pid):
    rng = random.Random("F" + pid)
    f = {c: rng.random() for c in FEATURES}
    f.update(node_code=NODE_CODES[node], key_code=rng.randrange(5), model_type_code=rng.randrange(3),
             new_cat_code=rng.randrange(4), last_key_delta_z=float("nan"), budget_frac_left=rng.random())
    return f


def _row(node, seed, mode, t, kind="audit", src="s2", key=None):
    pid = f"{src}_{mode}:{node}__s{seed}:t{t:03d}"
    rng = random.Random(pid)
    f = _features(node, pid)
    f["active_equals_incumbent"] = float(kind == "noop")
    return {"proposal_id": pid, "instance": f"{node}__s{seed}", "instance_seed": seed, "node": node,
            "source": f"{src}_{mode}", "memory_mode": mode, "budget_index": t, "sigma_node": SIG,
            "sigma_cmp": SIG * (1.6 if t % 2 else 1.0),
            "delta_hat": 0.0 if kind == "noop" else rng.gauss(0, SIG), "noop": kind == "noop",
            "duplicate": kind == "dup", "features": f,
            "incumbent_hash": (key or pid) + ":i", "candidate_hash": (key or pid) + ":c"}


def _label(row, seeds=B.T0_LABEL_SEEDS, kind="audit"):
    if row["noop"]:
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "rule_noop",
                "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}}
    if kind == "divergent":
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "divergent",
                "seeds": list(seeds)}
    d = SIG * (2.0 * row["features"]["old_num"] - 1.0) + random.Random("L" + row["proposal_id"]).gauss(0, SIG / 2)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "audit",
            "seeds": list(seeds), "delta_label": d, "se_label": 0.004,
            "soft_parameters": {"inert": False, "sigma_node": SIG, "k_label": 5, "delta_label": d, "se_label": 0.004}}


def _evaluation(row):
    return {"proposal_id": row["proposal_id"], "node": row["node"], "seeds": list(B.T0_EVALUATION_SEEDS),
            "delta_evaluation": random.Random("E" + row["proposal_id"]).gauss(0.002, SIG), "se_evaluation": 0.004}


def _world(nodes=NODES):
    """Tables of both sources, train/dev label rows of both, and (for the builder comparison only) the test labels and
    the evaluation rows of sweep 2."""
    s2, s1 = [], []
    for node in nodes:
        for inst, v in sorted(ASSIGN.items()):
            if v["node"] != node:
                continue
            seed = int(inst.rsplit("__s", 1)[1])
            for mode in B.T0_MODES:
                s2 += [_row(node, seed, mode, 2, "noop"), _row(node, seed, mode, 3, "dup")]
                s2 += [_row(node, seed, mode, t) for t in range(4, 9)]
                s1 += [_row(node, seed, mode, 2, "noop", src="s1")]
                s1 += [_row(node, seed, mode, t, src="s1") for t in range(3, 7)]
    div = next(r for r in s2 if not r["noop"] and not r["duplicate"]
               and ASSIGN[r["instance"]]["split"] == "train")["proposal_id"]
    lab2 = {r["proposal_id"]: _label(r, kind="divergent" if r["proposal_id"] == div else "audit")
            for r in s2 if not r["duplicate"]}
    lab1 = {r["proposal_id"]: _label(r) for r in s1 if not r["duplicate"]}
    td = lambda rows, lab: [lab[r["proposal_id"]] for r in rows if r["proposal_id"] in lab  # noqa: E731
                            and ASSIGN[r["instance"]]["split"] != "test"]
    return {"tables": {"sweep2": s2, "sweep1": s1}, "labels": {"sweep2": td(s2, lab2), "sweep1": td(s1, lab1)},
            "all_labels2": list(lab2.values()), "evals2": [_evaluation(r) for r in s2 if not r["noop"]
                                                           and not r["duplicate"]], "divergent": div}


@pytest.fixture(scope="module")
def world():
    return _world()


@pytest.fixture(scope="module")
def trows(world):
    return {s: AF.training_rows(s, world["tables"][s], world["labels"][s], assign=ASSIGN) for s in world["tables"]}


@pytest.fixture(scope="module")
def frozen(world, trows):
    return AF.freeze_a3(world["tables"], trows, calibration="temperature", twin_weight="mode_group")


# ------------------------------------------------------------------------------------------- training rows

def test_training_rows_equal_the_builders_construction(world, trows):
    src = B.Source("sweep2", world["tables"]["sweep2"], world["all_labels2"], world["evals2"])
    prepared, _, _ = B._prepare([src, B.Source("sweep1", world["tables"]["sweep1"])], ASSIGN, None)
    want = {r["row"]["proposal_id"]: r for r in prepared if r["split"] != "test"}
    got = {r["proposal_id"]: r for r in trows["sweep2"]}
    assert set(got) == set(want) and len(got) > 1000
    for pid, r in got.items():
        w = want[pid]
        assert r["split"] == w["split"] and r["instance"] == w["instance"] and r["key"] == w["key"]
        assert r["label_kind"] == w["label_kind"] and r["weight"] == w["weight"] == 1.0
        if w["soft"] is None:
            assert r["soft"] is None
        else:
            assert np.array_equal(r["soft"], w["soft"])
    assert got[world["divergent"]]["soft"] is None and got[world["divergent"]]["label_kind"] == "divergent"
    kinds = {(r["noop"], r["duplicate"], r["soft"] is None) for r in got.values()}
    assert (True, False, False) in kinds and (False, True, True) in kinds and (False, False, False) in kinds
    assert not any(ASSIGN[r["instance"]]["split"] == "test" for r in trows["sweep1"])


def _mut(world, src="sweep2"):
    return copy.deepcopy(world["tables"][src]), copy.deepcopy(world["labels"][src])


def _first(rows, pred):
    return next(r for r in rows if pred(r))


def test_training_rows_refusals(world):
    rows, labs = _mut(world)
    ok = AF.training_rows("sweep2", rows, labs, assign=ASSIGN)
    assert ok
    traindev = lambda r: ASSIGN[r["instance"]]["split"] != "test"  # noqa: E731
    # a non-inert train/dev proposal without its label row
    victim = _first(rows, lambda r: traindev(r) and not r["noop"] and not r["duplicate"])
    with pytest.raises(AF.ArmsFreezeError, match="without its label row"):
        AF.training_rows("sweep2", rows, [l for l in labs if l["proposal_id"] != victim["proposal_id"]], assign=ASSIGN)
    # a duplicate carrying a label row
    dup = _first(rows, lambda r: traindev(r) and r["duplicate"])
    with pytest.raises(AF.ArmsFreezeError, match="duplicate carries a label"):
        AF.training_rows("sweep2", rows, labs + [_label({**dup, "duplicate": False})], assign=ASSIGN)
    # a test label (refused before anything else)
    test_row = _first(rows, lambda r: not traindev(r) and not r["noop"] and not r["duplicate"])
    with pytest.raises(AF.ArmsFreezeError, match="test label"):
        AF.training_rows("sweep2", rows, labs + [_label(test_row)], assign=ASSIGN)
    # evaluation fields or evaluation seeds in a label row
    bad = copy.deepcopy(labs)
    bad[5]["delta_evaluation"] = 0.1
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AF.training_rows("sweep2", rows, bad, assign=ASSIGN)
    bad = copy.deepcopy(labs)
    i = next(k for k, l in enumerate(bad) if l["label_kind"] == "audit")
    bad[i]["seeds"] = list(B.T0_EVALUATION_SEEDS)
    with pytest.raises(AF.ArmsFreezeError, match="evaluation seeds"):
        AF.training_rows("sweep2", rows, bad, assign=ASSIGN)
    # an evaluation row offered as a label row
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AF.training_rows("sweep2", rows, labs + [world["evals2"][0]], assign=ASSIGN)
    # G.5 label rows (g5_assemble.group_label) list their label-seed divergences: admitted only as a subset of the
    # row's own label seeds, on an audit or divergent row
    g5 = copy.deepcopy(labs)
    g5[i]["divergent_seeds"] = [g5[i]["seeds"][0]]
    assert AF.training_rows("sweep2", rows, g5, assign=ASSIGN)
    g5[i]["divergent_seeds"] = []
    assert AF.training_rows("sweep2", rows, g5, assign=ASSIGN)
    for div in ([B.T0_EVALUATION_SEEDS[0]], [9999], "7001", [True]):
        g5[i]["divergent_seeds"] = div
        with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
            AF.training_rows("sweep2", rows, g5, assign=ASSIGN)
    g5[i]["divergent_seeds"] = [g5[i]["seeds"][0]]
    g5[i]["k_evaluation"] = 4
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AF.training_rows("sweep2", rows, g5, assign=ASSIGN)
    noop = next(k for k, l in enumerate(labs) if l["label_kind"] == "rule_noop")
    g5 = copy.deepcopy(labs)
    g5[noop]["divergent_seeds"] = []
    with pytest.raises(AF.ArmsFreezeError, match="evaluation field"):
        AF.training_rows("sweep2", rows, g5, assign=ASSIGN)
    # a table row carrying a label/evaluation value
    bad_rows = copy.deepcopy(rows)
    bad_rows[0]["delta_true"] = 0.0
    with pytest.raises(AF.ArmsFreezeError, match="label/evaluation values"):
        AF.training_rows("sweep2", bad_rows, labs, assign=ASSIGN)
    # a row without the featurizer's full feature set (e.g. a T1 row before a T1 feature view exists)
    bad_rows = copy.deepcopy(rows)
    del bad_rows[0]["features"]["budget_frac_left"]
    with pytest.raises(AF.ArmsFreezeError, match="featurizer"):
        AF.training_rows("sweep2", bad_rows, labs, assign=ASSIGN)
    # label rows for proposals outside the table; label seeds other than the tier's (builder's _label_ok)
    with pytest.raises(AF.ArmsFreezeError, match="outside the table"):
        AF.training_rows("sweep2", [r for r in rows if r["proposal_id"] != victim["proposal_id"]], labs,
                         assign=ASSIGN)
    bad = copy.deepcopy(labs)
    bad[i]["seeds"] = [7001, 7002, 7003]
    with pytest.raises(AF.ArmsFreezeError, match="label seeds"):
        AF.training_rows("sweep2", rows, bad, assign=ASSIGN)
    with pytest.raises(AF.ArmsFreezeError, match="unknown source"):
        AF.training_rows("sweep3", rows, labs, assign=ASSIGN)


def test_input_paths_refused(tmp_path):
    for name in ("label_block.jsonl", "evaluation_block.jsonl", "evaluation_block.all.jsonl",
                 "label_block.test.jsonl", "runs.jsonl"):
        with pytest.raises(AF.ArmsFreezeError):
            AF.refuse_input_path(tmp_path / name)
    with pytest.raises(AF.ArmsFreezeError):
        AF.refuse_input_path(tmp_path / "sweep2" / "test")
    with pytest.raises(AF.ArmsFreezeError):
        AF.refuse_input_path(tmp_path / "sweep2" / "test" / "RECEIPT.json")
    AF.refuse_input_path(tmp_path / "sweep2" / "traindev" / "label_block.traindev.jsonl", tmp_path / "table")


def test_load_traindev_pins_the_receipt_and_refuses_evaluation_or_test_rows(monkeypatch, world, tmp_path):
    calls = []
    good = {"stage": "traindev", "source": "sweep2", "counts": {"evaluation_rows": 0}}

    def fake(root, source, receipt_sha256=None):
        calls.append((source, receipt_sha256))
        return copy.deepcopy(world["labels"][source]), dict(good, source=source)
    monkeypatch.setattr(release, "traindev_labels", fake)
    sha = "a" * 64
    labs, rec = AF.load_traindev(tmp_path, "sweep2", sha)
    assert calls == [("sweep2", sha)] and len(labs) == len(world["labels"]["sweep2"])
    with pytest.raises(AF.ArmsFreezeError, match="receipt sha256"):
        AF.load_traindev(tmp_path, "sweep2", None)
    monkeypatch.setattr(release, "traindev_labels",
                        lambda *a, **k: ([], {"stage": "traindev", "source": "sweep2",
                                              "counts": {"evaluation_rows": 3}}))
    with pytest.raises(AF.ArmsFreezeError, match="without evaluation rows"):
        AF.load_traindev(tmp_path, "sweep2", sha)
    test_row = _first(world["tables"]["sweep2"], lambda r: ASSIGN[r["instance"]]["split"] == "test" and not r["noop"]
                      and not r["duplicate"])
    monkeypatch.setattr(release, "traindev_labels", lambda *a, **k: ([_label(test_row)], dict(good)))
    with pytest.raises(AF.ArmsFreezeError, match="test label"):
        AF.load_traindev(tmp_path, "sweep2", sha)


# ------------------------------------------------------------------------------------------- PRE-SELECT

def _lab(node, split, soft, src="sweep2", noop=False):
    return {"node": node, "split": split, "soft": np.asarray(soft, float), "source": src, "noop": noop,
            "proposal_id": f"{node}{split}{random.random()}"}


def test_base_rates_and_preselect_score_by_hand():
    a, b = np.eye(N_BINS)[6], np.eye(N_BINS)[8]
    rows = [_lab("n1", "train", a), _lab("n1", "train", b), _lab("n1", "train", a, src="sweep1"),
            _lab("n2", "train", b), _lab("n1", "dev", a)]
    bases = AF.base_rates(rows)
    assert np.allclose(bases["n1"], (a + b) / 2) and np.allclose(bases["n2"], b)   # sweep 1 is not the reference
    dev = [_lab("n1", "dev", a), _lab("n1", "dev", b), _lab("n2", "dev", a), _lab("n3", "dev", a)]
    pred = lambda rs: np.array([np.full(N_BINS, 1 / N_BINS) for _ in rs])  # noqa: E731
    sc = AF.preselect_score(pred, dev, bases)
    y1 = np.array([a, b])
    s1 = 1 - M.mean_rps(pred([0, 0]), y1) / M.mean_rps(np.broadcast_to(bases["n1"], y1.shape), y1)
    y2 = np.array([a])
    s2 = 1 - M.mean_rps(pred([0]), y2) / M.mean_rps(np.broadcast_to(bases["n2"], y2.shape), y2)
    assert math.isclose(sc["per_node"]["n1"], s1) and math.isclose(sc["per_node"]["n2"], s2)
    assert math.isclose(sc["score"], (s1 + s2) / 2)                     # nodes weighted equally
    assert sc["left_out"] == {"n3": "no train base rate"}
    with pytest.raises(AF.ArmsFreezeError):
        AF.preselect_score(pred, [_lab("n3", "dev", a)], bases)


def test_choose_ties_and_the_pooled_choice():
    c = lambda s, pool, base=0.0: {"score": s, "pool": pool, "base_params": base}  # noqa: E731
    assert AF.choose({"sweep2_only": c(0.2, "sweep2_only"), "pooled": c(0.2 + 5e-10, "pooled")}) == "sweep2_only"
    assert AF.choose({"sweep2_only": c(0.2, "sweep2_only"), "pooled": c(0.2 + 5e-9, "pooled")}) == "pooled"
    assert AF.choose({"sweep2_only": c(0.3, "sweep2_only"), "pooled": c(0.2, "pooled")}) == "sweep2_only"
    a5 = {"kev4b/pooled": c(0.4, "pooled", 4e9), "kev08b/pooled": c(0.4, "pooled", 0.8e9),
          "kev4b/sweep2_only": c(0.4 - 1e-10, "sweep2_only", 4e9), "kev08b/sweep2_only": c(0.1, "sweep2_only", 0.8e9)}
    assert AF.choose(a5) == "kev4b/sweep2_only"                          # sweep-2-only first, then the smaller base
    a5["kev08b/sweep2_only"]["score"] = 0.4
    assert AF.choose(a5) == "kev08b/sweep2_only"
    del a5["kev4b/sweep2_only"], a5["kev08b/sweep2_only"]
    assert AF.choose(a5) == "kev08b/pooled"


# ------------------------------------------------------------------------------------------- calibration

def test_temperature_calibration_fit_and_switch():
    rng = np.random.default_rng(0)
    n = 400
    z = rng.normal(size=(n, 11))
    y_cond = np.exp(z) / np.exp(z).sum(1, keepdims=True)
    sharp = np.exp(3 * z) / np.exp(3 * z).sum(1, keepdims=True)        # over-confident forecasts
    P = np.concatenate([np.zeros((n, 1)), sharp], 1)
    Y = np.concatenate([np.zeros((n, 1)), y_cond], 1)
    cal = AF.fit_calibration(P, Y, "temperature")
    assert cal["mode"] == "temperature" and 2.5 < cal["temperature"] < 3.5 and cal["fit_rows"] == n
    rows = [{"noop": i == 0} for i in range(n)]
    P[0] = np.eye(N_BINS)[INERT]
    Q = AF.apply_calibration(P, rows, cal)
    assert np.allclose(Q.sum(1), 1) and np.array_equal(Q[0], np.eye(N_BINS)[INERT]) and np.all(Q[1:, INERT] == 0)
    assert np.allclose(Q[1:, 1:], y_cond[1:], atol=0.05)
    none = AF.fit_calibration(P, Y, "none")
    assert none == {"mode": "none"} and np.array_equal(AF.apply_calibration(P, rows, none), P)
    with pytest.raises(AF.ArmsFreezeError):
        AF.fit_calibration(P, Y, "isotonic")
    with pytest.raises(AF.ArmsFreezeError):
        AF.fit_calibration(np.zeros((0, N_BINS)), np.zeros((0, N_BINS)))


# ------------------------------------------------------------------------------------------- A3 freeze

def test_freeze_a3_selects_calibrates_and_predicts_every_proposal(world, trows, frozen):
    sel = frozen["selection"]
    assert sel["choice"] in AF.VARIANTS and set(sel["candidates"]) == set(AF.VARIANTS)
    assert sel["candidates"]["pooled"]["train_sources"] == ["sweep1", "sweep2"]
    assert sel["candidates"]["sweep2_only"]["train_sources"] == ["sweep2"]
    want = AF.choose({k: {"score": v["score"], "pool": k} for k, v in sel["candidates"].items()})
    assert sel["choice"] == want and sel["held_out"] == [] and sel["trained_nodes"] == sorted(NODES)
    # the scored dev population is the PRE-DUP primary dev population (gate source, labelled rows)
    prim = B.primary_dev_population([B.Source(s, r) for s, r in world["tables"].items()])
    dev = [r for r in trows["sweep2"] if r["split"] == "dev" and r["soft"] is not None and r["proposal_id"] in prim]
    assert sel["dev_rows_scored"] == len(dev) > 0
    assert frozen["calibration"]["mode"] == "temperature" and frozen["calibration"]["temperature"] > 0
    s2 = world["tables"]["sweep2"]
    assert set(frozen["predictions"]) == {r["proposal_id"] for r in s2}           # test proposals included
    P = np.array([frozen["predictions"][r["proposal_id"]] for r in s2])
    assert np.array_equal(B._rule_layer(P, s2), P)
    assert all(frozen["predictions"][r["proposal_id"]][INERT] == 1.0 for r in s2 if r["noop"])
    # the predictions feed the builder (A3 and A5 slots) without refusal
    labels = world["all_labels2"]
    src = B.Source("sweep2", s2, labels, world["evals2"])
    noise = {n: {"sigma_node": SIG, "delta_n": 0.002} for n in NODES}
    gi, _ = B.build([src, B.Source("sweep1", world["tables"]["sweep1"])],
                    {"A3": frozen["predictions"], "A5": frozen["predictions"]}, noise, t0_nodes=B.SEVEN_T0)
    assert len(gi["nodes"]) == 7


def test_calibration_switch_none_and_determinism(world, trows, frozen):
    raw = AF.freeze_a3(world["tables"], trows, calibration="none", twin_weight="mode_group")
    assert raw["calibration"] == {"mode": "none"} and raw["selection"] == frozen["selection"]
    again = AF.freeze_a3(world["tables"], trows, calibration="temperature", twin_weight="mode_group")
    assert again["predictions"] == frozen["predictions"]
    assert again["model"].model.model_to_string() == frozen["model"].model.model_to_string()


def test_fold_arm_holds_out_its_nodes(world, trows):
    plan = AF.fold_plan(B.SEVEN_T0, B.Tier1(suites={"mlgym_fmnist": "MLGym", "mlab_imdb": "MLAgentBench",
                                                     "mlgym_cifar10": "MLGym"}, modes=("none",)))
    assert plan["lono:digits_mlp"] == ["digits_mlp"] and "lono:openml_wdbc" not in plan
    assert plan["loso:MLGym"] == ["mlgym_cifar10", "mlgym_fmnist"] and plan["loso:MLAgentBench"] == ["mlab_imdb"]
    assert len(plan) == 9 and AF.fold_plan(B.SEVEN_T0, None).keys() == {f"lono:{n}" for n in B.SEVEN_T0}
    res = AF.freeze_a3(world["tables"], trows, calibration="temperature", twin_weight="mode_group",
                       held_out=["digits_mlp"])
    assert "digits_mlp" not in res["selection"]["trained_nodes"] and res["selection"]["held_out"] == ["digits_mlp"]
    assert set(res["predictions"]) == {r["proposal_id"] for r in world["tables"]["sweep2"] if r["node"] == "digits_mlp"}
    assert "digits_mlp" not in res["selection"]["candidates"]["pooled"]["per_node"]


def test_write_arm_artefacts_and_entry(tmp_path, frozen):
    e = AF.write_arm(tmp_path / "A3", "A3", frozen, code_commit=BASE_COMMIT, role="primary", inputs={"x": 1})
    for k in ("checkpoint", "calibration", "selection", "predictions"):
        f = tmp_path / e[k]["path"]
        assert f.is_file() and AF._sha_file(f) == e[k]["sha256"]
    assert e["preselect"]["choice"] == frozen["selection"]["choice"] and set(e["preselect"]["dev_values"]) == \
        set(AF.VARIANTS)
    preds = json.loads((tmp_path / e["predictions"]["path"]).read_text())
    assert preds["schema"] == AF.PRED_SCHEMA and preds["predictions"] == frozen["predictions"]
    with pytest.raises(FileExistsError):
        AF.write_arm(tmp_path / "A3", "A3", frozen, code_commit=BASE_COMMIT, role="primary", inputs={})


# ------------------------------------------------------------------------------------------- FEAT-ONE identity

def _tables_v2_v3(world):
    v3 = copy.deepcopy(world["tables"]["sweep1"])
    v2 = copy.deepcopy(v3)
    for r in v2[::7]:
        r["features"]["budget_frac_left"] = r["features"]["budget_frac_left"] / 2
    return v2, v3


def test_identity_accepts_the_v2_v3_pattern_and_refuses_anything_else(world, tmp_path):
    v2, v3 = _tables_v2_v3(world)
    cfg = b'{"h": {"files": {}}}'
    out = AF.identity_compare(v2, v3, sealed_configs=cfg, arms_configs=cfg)
    assert out["pass"] and out["n_budget_frac_left_differ"] == len(v2[::7]) and out["n_other_differences"] == 0
    assert out["keys_equal"] and out["configs_equal"]                           # NaN features compare equal
    assert AF.identity_compare(v3, v3, sealed_configs=cfg, arms_configs=cfg)["n_budget_frac_left_differ"] == 0
    # a key difference
    out = AF.identity_compare(v2[1:], v3, sealed_configs=cfg, arms_configs=cfg)
    assert not out["pass"] and not out["keys_equal"] and out["keys_only_arms"] == 1
    renamed = copy.deepcopy(v2)
    renamed[0]["node"] = "tabular_mlp" if renamed[0]["node"] != "tabular_mlp" else "digits_mlp"
    assert not AF.identity_compare(renamed, v3, sealed_configs=cfg, arms_configs=cfg)["pass"]
    # a configs difference
    assert not AF.identity_compare(v2, v3, sealed_configs=cfg, arms_configs=cfg + b" ")["pass"]
    # another feature, a top-level field, a missing field, NaN against a number
    for mutate in (lambda r: r["features"].__setitem__("budget_index", 99.0),
                   lambda r: r.__setitem__("candidate_hash", "x"),
                   lambda r: r["features"].pop("keeps_so_far"),
                   lambda r: r["features"].__setitem__("last_key_delta_z", 0.0),
                   lambda r: r.__setitem__("noop", 1)):
        bad = copy.deepcopy(v2)
        mutate(bad[3])
        out = AF.identity_compare(bad, v3, sealed_configs=cfg, arms_configs=cfg)
        assert not out["pass"] and out["n_other_differences"] == 1 and out["other_differences"][0][0] == \
            bad[3]["proposal_id"]
    with pytest.raises(AF.ArmsFreezeError, match="duplicate key"):
        AF.identity_compare(v2 + v2[:1], v3, sealed_configs=cfg, arms_configs=cfg)
    # the file form (tables without build.json pass the D8-confirmed guard on this checkout)
    for name, rows in (("sealed", v2), ("arms", v3)):
        d = tmp_path / name
        d.mkdir()
        (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (d / "configs.json").write_bytes(cfg)
    res = AF.identity_check(tmp_path / "sealed", tmp_path / "arms")
    assert res["pass"] and res["arms_proposals_sha256"] == AF._sha_file(tmp_path / "arms" / "proposals.jsonl")
    assert res["featurizer"] == "c3_features/v3"


# ------------------------------------------------------------------------------------------- arms-frozen record

PLAN = ("# PLAN\n\n## 10. Decisions\n\n### 24 November 2026 — arms freeze (author)\n\n| ID | Decision |\n|---|---|\n"
        "| R1-ARMS-DECISIONS | the arms decisions |\n| R1-ARMS-A5FOLD-OUT | A5 folds not built |\n"
        "| R1-T1-FEAT-DECISIONS | ARMS-T1FEAT A report: D1-D4 A, D7: a T1 prompt form for A5 |\n"
        "| R1-T1-A5-DECISIONS | A5's T1 input: D7-FORM A (`trackp_prompt_t1/1`); D7-DIFF B with fallback A |\n"
        "| R1-POSTFREEZE-READS | the post-freeze reads amendment |\n")         # the row the record's amendments cite


def _pin(path, ch):
    return {"path": path, "sha256": ch * 64}


SRC_SHA = {"sweep1": AF.SWEEP1_SEALED_PROPOSALS_SHA256, "sweep2": "9" * 64, "g5": "c" * 64}      # released tables in the fake record


def _arm(role, a5=False, a3=False):
    e = {"role": role, "code_commit": BASE_COMMIT, "checkpoint": _pin("a/model.txt", "1"),
         "calibration": _pin("a/calibration.json", "2"), "predictions": _pin("a/predictions.json", "3"),
         "preselect": {"choice": "sweep2_only", "dev_values": {"sweep2_only": 0.1, "pooled": 0.05}}}
    if a5:
        e["p4_arm_pin"] = _pin("p4/pin.json", "4")
    if a3:
        e["toolchain"] = {"python": "3.12.3", "numpy": "2.5.4", "lightgbm": "4.7.0"}
        e.update(calibration_mode="temperature", twin_weight="mode_group")
        e["inputs"] = {s: {"receipt_sha256": "8" * 64, "traindev_partition_sha256": "7" * 64,
                           "table_proposals_sha256": AF.SWEEP1_V3_PROPOSALS_SHA256 if s == "sweep1" else SRC_SHA[s]}
                       for s in ("sweep1", "sweep2", "g5")}
    return e


T1_INST = sorted(i for i, v in ASSIGN.items() if v["node"] == "mlgym_fmnist" and v["split"] in ("train", "dev"))


def _record():
    from r1.harness import REPO
    gate, builder = AF._sha_file(REPO / "r1/c3/gate.py"), AF._sha_file(REPO / "r1/c3/gate_input_builder.py")
    ident = {"schema": AF.IDENTITY_SCHEMA, "featurizer": AF.FEATURIZER, "pass": True,
             "sealed_proposals_sha256": SRC_SHA["sweep1"], "arms_proposals_sha256": AF.SWEEP1_V3_PROPOSALS_SHA256,
             "n_budget_frac_left_differ": 116, "configs_sha256": {"sealed": AF.SWEEP1_V3_CONFIGS_SHA256,
                                                                 "arms": AF.SWEEP1_V3_CONFIGS_SHA256}}
    rec = {"schema": AF.RECORD_SCHEMA, "preregistration": {"path": AF.PREREG_PATH, "sha256": AF.PREREG_SHA256},
           "gate": {"path": "r1/c3/gate.py", "sha256": gate},
           "gate_input_builder": {"path": "r1/c3/gate_input_builder.py", "sha256": builder},
           "split_file": {"path": "r1/c3/splits/c3_p3_split_v1.json", "sha256": p3_split.P3_SPLIT_SHA256},
           "noise_source": {"path": AF.NOISE_PATH, "sha256": AF.NOISE_SHA256},
           "g1b_summaries": {"mlgym_fmnist": {"path": "r1/c3/splits/c3_p3_split_v1.json",      # a committed file
                                              "sha256": p3_split.P3_SPLIT_SHA256}},
           "t0_nodes": list(B.SEVEN_T0), "t1": {"suites": {"mlgym_fmnist": "MLGym"}, "modes": ["none"], "d3_k6": False,
                                                "instances": list(T1_INST)},
           "label_tables": {s: {"label_block_sha256": "6" * 64, "traindev_partition_sha256": "7" * 64,
                                "receipt_sha256": "8" * 64, "proposals_sha256": SRC_SHA[s]}
                            for s in ("sweep1", "sweep2", "g5")},
           "feature_tables": {"featurizer": "c3_features/v3",
                              "sweep1": {"sealed_proposals_sha256": SRC_SHA["sweep1"],
                                         "arms_proposals_sha256": AF.SWEEP1_V3_PROPOSALS_SHA256,
                                         "identity_check": ident},
                              "sweep2": {"proposals_sha256": SRC_SHA["sweep2"]}, "g5": {"proposals_sha256": SRC_SHA["g5"]}},
           "fold_arms": {"A3": "built", "A5": "not_built:R1-ARMS-A5FOLD-OUT"},
           "secondary_arms": ["A5-qwen3.5-0.8b-base", "A4"],
           "decisions": {**{d: "R1-ARMS-DECISIONS" for d in AF.REQUIRED_DECISIONS},
                         "ARMS-T1FEAT": "R1-T1-FEAT-DECISIONS"},
           "a3_settings": {"calibration": "temperature", "twin_weight": "mode_group"},
           "disclosures": {"trackp_sft_v1": "Track P SFT runs on trackp_sft/v1 (sweep 1) before the signature",
                           "exam_set": "P.3b exam set drawn from sweep 2's P3 train label block"},
           # post-freeze reads amendment A§9 (the fields unit 2 adds)
           "amendments": [{"path": "docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_20261123.md",
                           "sha256": "e" * 64, "plan_row": "R1-POSTFREEZE-READS"}],
           "rule_arms": {"A0": {"rule": "r1.c3.offline_eval.rho", "constants": None},
                         **{arm: {"vectors": {n: [0.0] + [1.0 / 11] * 11 for n in [*B.ALL_T0, "mlgym_fmnist"]},
                                  "fitter": {"path": "r1/c3/arms_constants.py", "sha256": "5" * 64,
                                             "code_commit": BASE_COMMIT},
                                  "constants": {"path": "rule_constants/C3_RULE_ARM_CONSTANTS.json",
                                                "sha256": "d" * 64},
                                  "receipts": {"sweep2": "8" * 64, "g5": "8" * 64},
                                  "fit_population": "dev label block, full dev population, gate sources",
                                  **({"offline": "no rule layer; no verify offline"} if arm == "A1" else {})}
                            for arm in ("A1", "A2")},
                         "d3_constants": None}}
    arms = {"A3": _arm("primary", a3=True), "A5": _arm("primary", a5=True), "A4": _arm("secondary"),
            "A5-qwen3.5-0.8b-base": _arm("secondary", a5=True)}
    for fold in AF.fold_plan(B.SEVEN_T0, B.Tier1(suites={"mlgym_fmnist": "MLGym"}, modes=("none",))):
        arms[f"A3@{fold}"] = _arm("fold", a3=True)
    rec["arms"] = arms
    return rec


def test_record_checker_accepts_a_complete_record_and_round_trips():
    rec = _record()
    out = AF.check_record(rec, plan_text=PLAN, record_path="docs/r1/arms_frozen/C3_ARMS_FROZEN_20261215.md")
    assert out["pass"] and "A3@loso:MLGym" in out["arms"] and "A3@lono:tabular_mlp" in out["arms"]
    text = AF.render_record(rec)
    assert AF.parse_record(text) == rec
    assert AF.check_record(AF.parse_record(text), plan_text=PLAN, verify_git=True)["code_commits"] == [BASE_COMMIT]
    # the record path is one the test release row can cite
    path = "docs/r1/arms_frozen/C3_ARMS_FROZEN_20261215.md"
    row = release.row_text("T0", "test", prereg="a" * 64, split="b" * 64, commit=BASE_COMMIT, arms_path=path,
                           arms="c" * 64)
    assert re.fullmatch(release.row_pattern("T0", "test"), row)
    with pytest.raises(AF.ArmsFreezeError, match="record path"):
        AF.check_record(rec, plan_text=PLAN, record_path="results/arms.md")
    with pytest.raises(AF.ArmsFreezeError, match="one fenced json block"):
        AF.parse_record(text + "\ntrailing\n")


@pytest.mark.parametrize("key", AF.REQUIRED_TOP)
def test_record_checker_refuses_a_missing_item(key):
    rec = _record()
    del rec[key]
    with pytest.raises(AF.ArmsFreezeError):
        AF.check_record(rec, plan_text=PLAN)


def _refused(mutate, match=None):
    rec = _record()
    mutate(rec)
    with pytest.raises(AF.ArmsFreezeError, match=match):
        AF.check_record(rec, plan_text=PLAN)


def test_record_checker_refuses_wrong_bindings():
    _refused(lambda r: r["gate"].__setitem__("sha256", "0" * 64), "gate")
    _refused(lambda r: r["gate_input_builder"].__setitem__("sha256", "0" * 64), "gate_input_builder")
    _refused(lambda r: r["preregistration"].__setitem__("sha256", "0" * 64), "preregistration")
    _refused(lambda r: r["split_file"].__setitem__("sha256", "0" * 64), "split_file")
    _refused(lambda r: r["noise_source"].__setitem__("sha256", "0" * 64), "noise_source")
    _refused(lambda r: r.__setitem__("t0_nodes", list(B.SEVEN_T0)[:6]), "t0_nodes")
    _refused(lambda r: r["g1b_summaries"].clear(), "g1b")
    _refused(lambda r: r["t1"]["suites"].__setitem__("mlgym_fmnist", "Kaggle"), "suite")
    _refused(lambda r: r["label_tables"].pop("g5"), "label_tables")
    _refused(lambda r: r["label_tables"]["sweep2"].__setitem__("receipt_sha256", "x"), "receipt_sha256")
    _refused(lambda r: r["feature_tables"]["sweep1"]["identity_check"].__setitem__("pass", False), "FEAT-ONE")
    _refused(lambda r: r["feature_tables"].__setitem__("featurizer", "c3_features/v2"), "featurizer")
    _refused(lambda r: r["feature_tables"]["sweep2"].__setitem__("proposals_sha256", "0" * 64), "released table")
    _refused(lambda r: r["decisions"].__setitem__("ARMS-CAL", "R1-NOT-A-ROW"), "ARMS-CAL")
    _refused(lambda r: r["decisions"].pop("FEAT-ONE"), "FEAT-ONE")
    _refused(lambda r: r["disclosures"].__setitem__("exam_set", " "), "disclosures")
    _refused(lambda r: r["fold_arms"].__setitem__("A5", "not_built:R1-NOT-A-ROW"), "absent author row")
    _refused(lambda r: r["arms"].pop("A3@lono:digits_mlp"), "missing")
    _refused(lambda r: r["arms"].pop("A4"), "missing")
    _refused(lambda r: r["arms"].__setitem__("TabPFN-ic", _arm("secondary")), "undeclared")
    _refused(lambda r: r["arms"]["A5"].pop("p4_arm_pin"), "p4_arm_pin")
    _refused(lambda r: r["arms"]["A5-qwen3.5-0.8b-base"].pop("p4_arm_pin"), "p4_arm_pin")
    _refused(lambda r: r["arms"]["A3"].pop("calibration"), "lacks")
    _refused(lambda r: r["arms"]["A3"].__setitem__("code_commit", "abc"), "code_commit")
    _refused(lambda r: r["arms"]["A3"].__setitem__("role", "secondary"), "role")
    _refused(lambda r: r["arms"]["A3"]["preselect"].__setitem__("choice", "other"), "preselect")
    _refused(lambda r: r["arms"]["A3"]["checkpoint"].__setitem__("sha256", "short"), "checkpoint")
    _refused(lambda r: r.__setitem__("schema", "other"), "schema")


def _file(root, rel, data: bytes):
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    return {"path": rel, "sha256": AF._sha(data)}


def _artefacts(rec, root):
    """Real files for every pin; A5-family checkpoints are P.4 best/ trees bound by an arm pin file."""
    for i, (name, e) in enumerate(sorted(rec["arms"].items())):
        e["predictions"] = _file(root, f"art/{i}/predictions.json", f"preds {i}".encode())
        if name.startswith("A5"):
            _file(root, f"p4/{i}/best/adapter/weights.bin", f"weights {i}".encode())
            e["calibration"] = _file(root, f"p4/{i}/best/temperature.json", b'{"temperature": 1.3}')
            e["checkpoint"] = {"path": f"p4/{i}/best", "sha256": AF.tree_sha256(root / f"p4/{i}/best")}
            pin = {"schema": "trackp_p4_arm_pin/v2", "grid": [
                {"run_dir": "other", "best_tree_sha256": "0" * 64, "temperature_sha256": "0" * 64},
                {"run_dir": "lr3e-5_s1", "best_tree_sha256": e["checkpoint"]["sha256"],
                 "temperature_sha256": e["calibration"]["sha256"]}]}
            e["p4_arm_pin"] = _file(root, f"p4/{i}/pin.json", json.dumps(pin).encode())
        else:
            e["checkpoint"] = _file(root, f"art/{i}/model.txt", f"model {i}".encode())
            e["calibration"] = _file(root, f"art/{i}/calibration.json", f"cal {i}".encode())


def test_tree_sha_is_p4_arm_pins_formula(tmp_path):
    _file(tmp_path, "b/x.bin", b"1")
    _file(tmp_path, "b/sub/y.json", b"2")
    lines = "".join(f"{p}\0{AF._sha(d)}\n" for p, d in (("sub/y.json", b"2"), ("x.bin", b"1")))
    assert AF.tree_sha256(tmp_path / "b") == AF._sha(lines.encode())


def test_record_checker_rehashes_artefacts_and_checks_commits(tmp_path):
    rec = _record()
    _artefacts(rec, tmp_path / "a")
    n = sum(len([k for k in ("checkpoint", "calibration", "predictions", "p4_arm_pin") if k in e])
            for e in rec["arms"].values())
    assert AF.check_record(rec, plan_text=PLAN, artefact_root=tmp_path / "a")["artefacts_rehashed"] == n
    (tmp_path / "a" / rec["arms"]["A3"]["checkpoint"]["path"]).write_bytes(b"changed")
    with pytest.raises(AF.ArmsFreezeError, match="differs"):
        AF.check_record(rec, plan_text=PLAN, artefact_root=tmp_path / "a")
    rec = _record()
    _artefacts(rec, tmp_path / "b")
    (tmp_path / "b" / rec["arms"]["A5"]["checkpoint"]["path"] / "extra.bin").write_bytes(b"x")
    with pytest.raises(AF.ArmsFreezeError, match="A5.checkpoint"):
        AF.check_record(rec, plan_text=PLAN, artefact_root=tmp_path / "b")
    rec = _record()
    _artefacts(rec, tmp_path / "c")
    pin = json.loads((tmp_path / "c" / rec["arms"]["A5"]["p4_arm_pin"]["path"]).read_text())
    pin["grid"][1]["temperature_sha256"] = "1" * 64
    rec["arms"]["A5"]["p4_arm_pin"] = _file(tmp_path / "c", rec["arms"]["A5"]["p4_arm_pin"]["path"],
                                            json.dumps(pin).encode())
    with pytest.raises(AF.ArmsFreezeError, match="exactly one run"):
        AF.check_record(rec, plan_text=PLAN, artefact_root=tmp_path / "c")
    rec = _record()
    rec["arms"]["A3"]["code_commit"] = "f" * 40
    with pytest.raises(AF.ArmsFreezeError, match="origin/main"):
        AF.check_record(rec, plan_text=PLAN, verify_git=True)


# ------------------------------------------------------------------------------------------- the train-a3 command

def _table_dir(root, name, rows):
    d = root / name
    d.mkdir()
    (d / "proposals.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "configs.json").write_bytes(b"{}")
    return d


def test_train_command_binds_receipts_and_feat_one(monkeypatch, world, tmp_path):
    v2, v3 = _tables_v2_v3(world)
    sealed = _table_dir(tmp_path, "sealed_v2", v2)
    arms1 = _table_dir(tmp_path, "arms_v3", v3)
    s2 = _table_dir(tmp_path, "sweep2_table", world["tables"]["sweep2"])
    ident = AF.identity_check(sealed, arms1)
    (tmp_path / "identity.json").write_bytes(AF._dump(ident))
    shas = {"sweep1": AF._sha_file(sealed / "proposals.jsonl"), "sweep2": AF._sha_file(s2 / "proposals.jsonl")}
    monkeypatch.setattr(AF, "SWEEP1_V3_PROPOSALS_SHA256", ident["arms_proposals_sha256"])
    monkeypatch.setattr(AF, "SWEEP1_V3_CONFIGS_SHA256", AF._sha(b"{}"))
    monkeypatch.setattr(AF, "SWEEP1_SEALED_PROPOSALS_SHA256", shas["sweep1"])

    def fake(root, source, receipt_sha256=None):
        assert receipt_sha256 == {"sweep1": "1" * 64, "sweep2": "2" * 64}[source]
        assert str(root).endswith({"sweep1": "rel1", "sweep2": "rel2"}[source])
        return copy.deepcopy(world["labels"][source]), {
            "stage": "traindev", "source": source, "counts": {"evaluation_rows": 0},
            "inputs": {"proposals_sha256": shas[source]}, "outputs": {"label_block.traindev.jsonl": "e" * 64}}
    monkeypatch.setattr(release, "traindev_labels", fake)
    monkeypatch.setattr(AF, "_code_commit", lambda: BASE_COMMIT)
    args = ["train-a3", "--release-root", f"sweep1={tmp_path / 'rel1'}", "--release-root", f"sweep2={tmp_path / 'rel2'}",
            "--artefact-root", str(tmp_path), "--table", f"sweep1={arms1}",
            "--table", f"sweep2={s2}", "--receipt", "sweep1=" + "1" * 64, "--receipt", "sweep2=" + "2" * 64,
            "--identity", str(tmp_path / "identity.json"), "--folds", "--calibration", "temperature",
            "--twin-weight", "mode_group"]
    for flag in ("--calibration", "--twin-weight"):                # the author row's choice must be typed in
        i = args.index(flag)
        with pytest.raises(SystemExit):
            AF.main(args[:i] + args[i + 2:] + ["--out", str(tmp_path / "out0")])
    assert not (tmp_path / "out0").exists()
    with pytest.raises(AF.ArmsFreezeError, match="inside --artefact-root"):
        AF.main(args + ["--out", "/tmp/elsewhere_not_under_root"])
    assert AF.main(args + ["--out", str(tmp_path / "out")]) == 0
    entries = json.loads((tmp_path / "out" / "entries.json").read_text())
    assert set(entries) == {"A3"} | {f"A3@lono:{n}" for n in B.SEVEN_T0}
    a3 = entries["A3"]
    assert a3["code_commit"] == BASE_COMMIT and a3["role"] == "primary" and a3["calibration_mode"] == "temperature"
    assert a3["inputs"]["sweep1"]["table_proposals_sha256"] == ident["arms_proposals_sha256"]
    assert a3["n_predictions"] == len(world["tables"]["sweep2"]) and a3["twin_weight"] == "mode_group"
    assert set(a3["toolchain"]) == {"python", "numpy", "lightgbm"}
    assert entries["A3@lono:openml_sonar"]["role"] == "fold"
    for e in entries.values():
        for k in ("checkpoint", "calibration", "predictions"):
            assert e[k]["path"].startswith("out/") and AF._sha_file(tmp_path / e[k]["path"]) == e[k]["sha256"]
    # the sealed table itself (v2) in place of the v3 arms table, or a failing identity check, is refused
    bad = [a if a != f"sweep1={arms1}" else f"sweep1={sealed}" for a in args]
    with pytest.raises(AF.ArmsFreezeError, match="FEAT-ONE"):
        AF.main(bad + ["--out", str(tmp_path / "out2")])
    (tmp_path / "identity.json").write_bytes(AF._dump({**ident, "pass": False}))
    with pytest.raises(AF.ArmsFreezeError, match="FEAT-ONE"):
        AF.main(args + ["--out", str(tmp_path / "out3")])
    # self-identity: the sealed table compared with itself passes identity_compare, but FEAT-ONE refuses it
    self_ident = AF.identity_check(sealed, sealed)
    assert self_ident["pass"] and self_ident["n_budget_frac_left_differ"] == 0
    (tmp_path / "identity.json").write_bytes(AF._dump(self_ident))
    monkeypatch.setattr(AF, "SWEEP1_V3_PROPOSALS_SHA256", shas["sweep1"])
    with pytest.raises(AF.ArmsFreezeError, match="FEAT-ONE"):
        AF.main(bad + ["--out", str(tmp_path / "out5")])
    monkeypatch.setattr(AF, "SWEEP1_V3_PROPOSALS_SHA256", ident["arms_proposals_sha256"])
    (tmp_path / "identity.json").write_bytes(AF._dump({**ident, "schema": "other/v0"}))
    with pytest.raises(AF.ArmsFreezeError, match="FEAT-ONE"):
        AF.main(args + ["--out", str(tmp_path / "out6")])
    (tmp_path / "identity.json").write_bytes(AF._dump(ident))
    shas["sweep2"] = "0" * 64
    with pytest.raises(AF.ArmsFreezeError, match="receipt released"):
        AF.main(args + ["--out", str(tmp_path / "out4")])


def test_feat_one_pin_is_the_trackp_sft_pin():
    from r1.harness import REPO
    pin = json.loads((REPO / "r1/scripts/configs/trackp_sft.json").read_text())["tables"]["sweep1_v3"]
    assert pin["sha256"] == {"proposals.jsonl": AF.SWEEP1_V3_PROPOSALS_SHA256,
                             "configs.json": AF.SWEEP1_V3_CONFIGS_SHA256}
    assert pin["featurizer_version"] == AF.FEATURIZER


def test_record_checker_refuses_self_identity_and_unpinned_arms_tables():
    def same(r):
        idc = r["feature_tables"]["sweep1"]["identity_check"]
        idc.update(arms_proposals_sha256=SRC_SHA["sweep1"], n_budget_frac_left_differ=0)
        r["feature_tables"]["sweep1"]["arms_proposals_sha256"] = SRC_SHA["sweep1"]
    _refused(same, "FEAT-ONE")
    _refused(lambda r: r["feature_tables"]["sweep1"]["identity_check"].__setitem__("n_budget_frac_left_differ", 0),
             "FEAT-ONE")
    def other(r):
        r["feature_tables"]["sweep1"]["arms_proposals_sha256"] = "e" * 64
        r["feature_tables"]["sweep1"]["identity_check"]["arms_proposals_sha256"] = "e" * 64
    _refused(other, "pinned v3")
    _refused(lambda r: r["feature_tables"]["sweep1"]["identity_check"].__setitem__("featurizer", "c3_features/v2"),
             "FEAT-ONE")
    _refused(lambda r: r["feature_tables"]["sweep1"]["identity_check"]["configs_sha256"].__setitem__("arms", "0" * 64),
             "configs")


def test_record_checker_binds_a3_inputs_to_the_record_tables():
    _refused(lambda r: r["arms"]["A3"]["inputs"]["sweep2"].__setitem__("receipt_sha256", "0" * 64), "inputs.sweep2")
    _refused(lambda r: r["arms"]["A3@lono:digits_mlp"]["inputs"]["sweep1"].__setitem__(
        "traindev_partition_sha256", "0" * 64), "inputs.sweep1")
    _refused(lambda r: r["arms"]["A3"]["inputs"]["sweep1"].__setitem__("table_proposals_sha256", SRC_SHA["sweep1"]),
             "inputs.sweep1")                                # trained on the sealed v2 table
    _refused(lambda r: r["arms"]["A3"]["inputs"].pop("g5"), "inputs must name")
    _refused(lambda r: r["arms"]["A3"].pop("toolchain"), "toolchain")


def test_record_checker_t1_instances_and_g1b_against_the_repo():
    _refused(lambda r: r["t1"].pop("instances"), "t1 must be")
    _refused(lambda r: r["t1"].__setitem__("instances", [i for i in T1_INST if ASSIGN[i]["split"] != "dev"]),
             "train and a dev")
    _refused(lambda r: r["t1"]["instances"].append("mlab_imdb__s5101"), "frozen T1 node")
    _refused(lambda r: r["t1"]["instances"].append("mlgym_fmnist__s9999"), "split-file instance")
    _refused(lambda r: r["g1b_summaries"]["mlgym_fmnist"].__setitem__("sha256", "0" * 64), "committed file differs")
    _refused(lambda r: r["g1b_summaries"]["mlgym_fmnist"].__setitem__("path", "results/r1/absent.json"),
             "g1b_summaries")


def test_record_checker_needs_d7_signed_when_t1_is_in_the_read():
    """D7 (A5's T1 input): with a non-empty T1 set, the row ARMS-T1FEAT cites must be one of the two rows recording
    D7 (R1-T1-FEAT-DECISIONS, R1-T1-A5-DECISIONS) and the PLAN's R1-T1-A5-DECISIONS must adopt D7-FORM A; an author
    row that merely mentions a "D7" of another report (R1-D3-MIN's "R1-BX-D7", R1-EXAM-B1-ANCHOR-R4-H2's "D7 PASS")
    no longer passes. A T0-only record needs none of it."""
    _refused(lambda r: r["decisions"].__setitem__("ARMS-T1FEAT", "R1-ARMS-DECISIONS"), "rows recording D7")
    rec = _record()
    rec["decisions"]["ARMS-T1FEAT"] = "R1-T1-A5-DECISIONS"
    assert AF.check_record(rec, plan_text=PLAN)["pass"]
    unrelated = PLAN + ("| R1-D3-MIN | the control arms: A0 (the Karpathy default of R1-BX-D7) |\n"
                        "| R1-EXAM-B1-ANCHOR-R4-H2 | H1 not supported, **D7 PASS** |\n")
    for row in ("R1-D3-MIN", "R1-EXAM-B1-ANCHOR-R4-H2"):          # whole-word D7, but not the D7 of ARMS-T1FEAT A
        rec = _record()
        rec["decisions"]["ARMS-T1FEAT"] = row
        with pytest.raises(AF.ArmsFreezeError, match="rows recording D7"):
            AF.check_record(rec, plan_text=unrelated)
    a5_row = "| R1-T1-A5-DECISIONS | A5's T1 input: D7-FORM A (`trackp_prompt_t1/1`); D7-DIFF B with fallback A |\n"
    for plan in (PLAN.replace(a5_row, ""),                                           # the options row absent
                 PLAN.replace(a5_row, a5_row.replace("D7-FORM A", "D7-FORM C")),    # another D7-FORM option
                 PLAN.replace(a5_row, a5_row.replace("D7-FORM A", "XD7-FORM A"))):
        with pytest.raises(AF.ArmsFreezeError, match="adopting D7-FORM A"):
            AF.check_record(_record(), plan_text=plan)
    # the committed PLAN carries both rows, and R1-T1-A5-DECISIONS adopts D7-FORM A
    from pathlib import Path
    from r1.c3.release import author_rows
    real = dict(author_rows((Path(AF.__file__).resolve().parents[2] / "docs/r1/PLAN.md").read_text(encoding="utf-8")))
    assert set(AF.D7_ROWS) <= set(real) and re.search(r"(?<![\w-])D7-FORM A\b", real[AF.D7_FORM_ROW])
    rec = _record()
    rec["decisions"]["ARMS-T1FEAT"] = "R1-ARMS-DECISIONS"
    rec["t1"] = {"suites": {}, "modes": [], "d3_k6": False, "instances": []}
    rec["g1b_summaries"] = {}
    for k in ("label_tables", "feature_tables"):
        rec[k].pop("g5")
    rec["arms"] = {k: e for k, e in rec["arms"].items() if not k.startswith("A3@loso:")}   # no T1 suite, no LOSO
    for e in rec["arms"].values():
        if "inputs" in e:
            e["inputs"].pop("g5")
    assert AF.check_record(rec, plan_text=PLAN)["pass"]


def test_record_checker_rehashes_receipts_under_release_roots(tmp_path):
    rec = _record()
    roots = {}
    for src in ("sweep1", "sweep2"):
        d = tmp_path / src / src / "traindev"
        d.mkdir(parents=True)
        part = f"partition {src}\n".encode()
        (d / "label_block.traindev.jsonl").write_bytes(part)
        receipt = AF._dump({"source": src, "stage": "traindev",
                            "inputs": {"label_block_sha256": "6" * 64, "proposals_sha256": SRC_SHA[src]},
                            "outputs": {"label_block.traindev.jsonl": AF._sha(part)}})
        (d / "RECEIPT.json").write_bytes(receipt)
        rec["label_tables"][src].update(receipt_sha256=AF._sha(receipt), traindev_partition_sha256=AF._sha(part))
        for e in rec["arms"].values():
            if "inputs" in e:
                e["inputs"][src].update(receipt_sha256=AF._sha(receipt), traindev_partition_sha256=AF._sha(part))
        roots[src] = tmp_path / src
    out = AF.check_record(rec, plan_text=PLAN, release_roots=roots)
    assert out["receipts_rehashed"] == 2
    (roots["sweep2"] / "sweep2" / "traindev" / "label_block.traindev.jsonl").write_bytes(b"changed")
    with pytest.raises(AF.ArmsFreezeError, match="label_tables.sweep2"):
        AF.check_record(rec, plan_text=PLAN, release_roots=roots)
    with pytest.raises(AF.ArmsFreezeError, match="does not"):
        AF.check_record(rec, plan_text=PLAN, release_roots={"g6": tmp_path})


def test_render_creates_the_record_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(AF, "check_record", lambda *a, **k: {"pass": True})
    (tmp_path / "rec.json").write_text(json.dumps(_record()))
    assert AF.main(["render", "--json", str(tmp_path / "rec.json"), "--out", "docs/r1/arms_frozen/X.md"]) == 0
    assert AF.parse_record((tmp_path / "docs/r1/arms_frozen/X.md").read_text()) == _record()


def _tw(rows):
    return AF.twin_weighted([{"source": src, "instance": inst, "memory_mode": mode, "key": key, "weight": 1.0}
                             for src, inst, mode, key in rows])


def _total(out, src=None):
    return sum(r["weight"] for r in out if src is None or r["source"] == src)


def test_twin_weighting_per_mode_keeps_one_sources_total():
    m1, m2 = B.T0_MODES
    s2_both = [("sweep2", "a__s1", m1, "k"), ("sweep2", "a__s1", m2, "k")]
    alone = _tw(s2_both)
    assert _total(alone) == 2.0 and [r["weight"] for r in alone] == [1.0, 1.0]
    one = _tw(s2_both + [("sweep1", "a__s1", m1, "k")])                # sweep 1 in one mode
    assert [r["weight"] for r in one] == [0.5, 1.0, 0.5]
    assert _total(one) == 2.0 and _total(one, "sweep2") == 1.5     # the key keeps sweep 2's total of 2
    two = _tw(s2_both + [("sweep1", "a__s1", m1, "k"), ("sweep1", "a__s1", m2, "k")])
    assert [r["weight"] for r in two] == [0.5] * 4 and _total(two) == 2.0
    # not twins: another instance, a key in one source only, sweep 1 in a mode sweep 2 lacks
    other = _tw([("sweep2", "a__s1", m1, "k"), ("sweep1", "a__s2", m1, "k"), ("sweep1", "a__s1", m2, "k"),
                 ("sweep2", "a__s1", m1, "j")])
    assert [r["weight"] for r in other] == [1.0] * 4
    # a source with two rows in one group (cannot arise from labelled rows, handled anyway): the group keeps T = 2
    odd = _tw([("sweep2", "a__s1", m1, "k"), ("sweep2", "a__s1", m1, "k"), ("sweep1", "a__s1", m1, "k")])
    assert _total(odd) == 2.0 and _total(odd, "sweep2") == 1.0


def test_calibration_uses_only_primary_dev_audit_rows_and_twins_are_downweighted(world):
    tables = copy.deepcopy(world["tables"])
    s1_train = [r for r in tables["sweep1"] if ASSIGN[r["instance"]]["split"] == "train" and not r["noop"]]
    s2_dev = [r for r in tables["sweep2"] if ASSIGN[r["instance"]]["split"] == "dev" and not r["noop"]
              and not r["duplicate"]]
    s2_train = [r for r in tables["sweep2"] if ASSIGN[r["instance"]]["split"] == "train" and not r["noop"]
                and not r["duplicate"]]
    repeated = set()
    for a, b in zip(s1_train[:10], [d for d in s2_dev if d["node"] == s1_train[0]["node"]][:10]):
        a["incumbent_hash"], a["candidate_hash"] = b["incumbent_hash"], b["candidate_hash"]   # dev repeat of a train key
        a["node"] = b["node"]
        repeated.add(b["proposal_id"])
    free = s1_train[10:]
    twins = []
    for t in s2_train:                                                # cross-source twins on the same instance
        a = next((r for r in free if r["instance"] == t["instance"] and r["memory_mode"] == t["memory_mode"]), None)
        if a is None:
            continue
        free.remove(a)
        a["incumbent_hash"], a["candidate_hash"] = t["incumbent_hash"], t["candidate_hash"]
        twins.append(t)
        if len(twins) == 5:
            break
    assert repeated and twins
    trows = {s: AF.training_rows(s, tables[s], world["labels"][s], assign=ASSIGN) for s in tables}
    res = AF.freeze_a3(tables, trows, calibration="temperature", twin_weight="mode_group")
    prim = B.primary_dev_population([B.Source(s, r) for s, r in tables.items()])
    want = sorted(r["proposal_id"] for r in trows["sweep2"] if r["split"] == "dev" and r["label_kind"] == "audit"
                  and not r["noop"] and r["proposal_id"] in prim)
    assert res["selection"]["calibration_rows"] == want and not repeated & set(want)
    assert res["calibration"]["fit_rows"] == len(want)
    assert res["selection"]["candidates"]["pooled"]["twin_rows_downweighted"] >= 2 * len(twins)
    assert res["selection"]["candidates"]["sweep2_only"]["twin_rows_downweighted"] == 0
    none = AF.freeze_a3(tables, trows, calibration="temperature", twin_weight="none")
    assert none["selection"]["candidates"]["pooled"]["twin_rows_downweighted"] == 0
    with pytest.raises(AF.ArmsFreezeError, match="twin_weight"):
        AF.freeze_a3(tables, trows, calibration="temperature", twin_weight="group")
    with pytest.raises(AF.ArmsFreezeError, match="sweep1"):      # m7: a builder refusal surfaces as ArmsFreezeError
        AF.freeze_a3({"sweep2": tables["sweep2"]}, {"sweep2": trows["sweep2"]}, calibration="temperature",
                     twin_weight="none")


def test_record_checker_binds_a3_settings_and_the_sealed_pin():
    _refused(lambda r: r["arms"]["A3@lono:digits_mlp"].__setitem__("twin_weight", "none"), "a3_settings")
    _refused(lambda r: r["arms"]["A3"].__setitem__("calibration_mode", "none"), "a3_settings")
    _refused(lambda r: r["a3_settings"].__setitem__("twin_weight", "group"), "a3_settings")
    def other_sealed(r):
        r["label_tables"]["sweep1"]["proposals_sha256"] = "a" * 64
        r["feature_tables"]["sweep1"]["sealed_proposals_sha256"] = "a" * 64
        r["feature_tables"]["sweep1"]["identity_check"]["sealed_proposals_sha256"] = "a" * 64
    _refused(other_sealed, "sealed B.2 table")


# ------------------------------------------------------------------------------------------- post-freeze reads fields
# Unit 2 of the post-freeze reads amendment (A§8, A§9): amendments and rule_arms. AI-assisted (Claude, subagent,
# 23 Nov 2026). Synthetic constants files and a synthetic signed amendment in a temporary git repository only.

import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

from r1.c3 import arms_constants as AC  # noqa: E402

PLAN_WITHOUT_ROW = PLAN.replace("| R1-POSTFREEZE-READS | the post-freeze reads amendment |\n", "")


def test_postfreeze_amendments_cite_the_plan_row():
    assert "R1-POSTFREEZE-READS" not in PLAN_WITHOUT_ROW
    rec = _record()
    with pytest.raises(AF.ArmsFreezeError, match="author row of PLAN"):          # the row is absent from PLAN
        AF.check_record(rec, plan_text=PLAN_WITHOUT_ROW)
    _refused(lambda r: r["amendments"][0].__setitem__("plan_row", "R1-NOT-A-ROW"), "author row of PLAN")
    _refused(lambda r: r["amendments"][0].__setitem__("plan_row", "R1-ARMS-DECISIONS"), "must cite")
    _refused(lambda r: r["amendments"][0].__setitem__("plan_row", "r1-postfreeze-reads"), "author row of PLAN")
    _refused(lambda r: r["amendments"].append(copy.deepcopy(r["amendments"][0])), "exactly")
    _refused(lambda r: r.__setitem__("amendments", []), "exactly")
    _refused(lambda r: r.__setitem__("amendments", r["amendments"][0]), "exactly")
    _refused(lambda r: r["amendments"][0].pop("sha256"), "entry must be")
    _refused(lambda r: r["amendments"][0].__setitem__("note", "x"), "entry must be")
    _refused(lambda r: r["amendments"][0].__setitem__("sha256", "e" * 63), "sha256")
    _refused(lambda r: r["amendments"][0].__setitem__("path", "docs/r1/reports/AMEND.md"), "path must match")
    _refused(lambda r: r["amendments"][0].__setitem__(                       # N1: the draft's path
        "path", "docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_DRAFT_20261123.md"), "not name a draft")


def test_postfreeze_rule_arms_structure():
    v = [0.0] + [1.0 / 11] * 11
    _refused(lambda r: r["rule_arms"]["A0"].__setitem__("rule", "r1.c3.offline_eval.decisions"), "A0")
    _refused(lambda r: r["rule_arms"]["A0"].__setitem__("constants", {"pi": 0}), "A0")
    _refused(lambda r: r["rule_arms"].pop("d3_constants"), "rule_arms must be")
    _refused(lambda r: r["rule_arms"].__setitem__("A3", {}), "rule_arms must be")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].pop("openml_wdbc"), "eight T0 nodes")    # all eight, always
    _refused(lambda r: r["rule_arms"]["A2"]["vectors"].pop("mlgym_fmnist"), "frozen T1")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].__setitem__("mlab_imdb", list(v)), "frozen T1")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].__setitem__("digits_mlp", v[:-1]), "12 finite")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].__setitem__("digits_mlp", [float("nan")] + v[1:]), "12 finite")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].__setitem__("digits_mlp", [-0.01, 0.01 + v[1]] + v[2:]),
             "12 finite")
    _refused(lambda r: r["rule_arms"]["A1"]["vectors"].__setitem__("digits_mlp", [0.0] + [0.09] * 11), "sum to 1")
    _refused(lambda r: r["rule_arms"]["A2"]["vectors"].__setitem__("digits_mlp", [0.01, v[1] - 0.01] + v[2:]),
             "no-op bin")
    _refused(lambda r: r["rule_arms"]["A1"].pop("offline"), "rule_arms.A1 must be")
    _refused(lambda r: r["rule_arms"]["A1"].__setitem__("offline", "rule layer"), "offline")
    _refused(lambda r: r["rule_arms"]["A2"].__setitem__("offline", AC.A1_OFFLINE), "rule_arms.A2 must be")
    _refused(lambda r: r["rule_arms"]["A2"]["receipts"].__setitem__("sweep2", "9" * 64), "one fit")
    _refused(lambda r: r["rule_arms"]["A2"]["constants"].__setitem__("sha256", "9" * 64), "one fit")
    _refused(lambda r: r["rule_arms"]["A1"]["fitter"].__setitem__("path", "r1/c3/other.py"), "fitter")
    _refused(lambda r: r["rule_arms"]["A1"]["fitter"].__setitem__("code_commit", "abc"), "fitter")
    _refused(lambda r: r["rule_arms"]["A1"]["fitter"].pop("code_commit"), "fitter")
    _refused(lambda r: r["rule_arms"]["A1"]["constants"].__setitem__("path", "/abs/C.json"), "relative")
    _refused(lambda r: r["rule_arms"]["A1"]["constants"].__setitem__("path", "a/../../C.json"), "relative")
    _refused(lambda r: r["rule_arms"]["A1"]["receipts"].pop("g5"), "receipts")              # T1 frozen: G.5 too
    _refused(lambda r: r["rule_arms"]["A1"]["receipts"].__setitem__("sweep1", "8" * 64), "receipts")
    _refused(lambda r: r["rule_arms"]["A1"].__setitem__("fit_population", "train label block"), "fit_population")
    _refused(lambda r: r["rule_arms"].__setitem__("d3_constants", {"path": "d3.json"}), "d3_constants")
    _refused(lambda r: r["rule_arms"].__setitem__("d3_constants", {"path": "../d3.json", "sha256": "1" * 64}),
             "relative")


def _t0_only(rec):
    """The fixture as a T0-only record (an empty frozen T1 set): no G.5 table, no LOSO fold, no T1 vector."""
    rec["t1"] = {"suites": {}, "modes": [], "d3_k6": False, "instances": []}
    rec["g1b_summaries"] = {}
    for k in ("label_tables", "feature_tables"):
        rec[k].pop("g5")
    rec["arms"].pop("A3@loso:MLGym")
    for e in rec["arms"].values():
        if "inputs" in e:
            e["inputs"].pop("g5")
    for arm in ("A1", "A2"):
        rec["rule_arms"][arm]["vectors"].pop("mlgym_fmnist")
        rec["rule_arms"][arm]["receipts"].pop("g5")
    return rec


def test_postfreeze_t0_only_record_and_arms_unchanged():
    rec = _t0_only(_record())
    out = AF.check_record(rec, plan_text=PLAN)
    assert out["pass"] and "A3@loso:MLGym" not in out["arms"] and out["code_commits"] == [BASE_COMMIT]
    bad = copy.deepcopy(rec)
    bad["rule_arms"]["A1"]["receipts"]["g5"] = "8" * 64                     # no G.5 receipt without T1
    with pytest.raises(AF.ArmsFreezeError, match="receipts"):
        AF.check_record(bad, plan_text=PLAN)
    # A0 and A1 are rule arms of the record, not arms: arms still equals required_arms
    assert not {"A0", "A1", "A2"} & set(AF.required_arms(_record()))
    _refused(lambda r: r["arms"].__setitem__("A1", _arm("secondary")), "undeclared")
    _refused(lambda r: r["arms"].__setitem__("A0", _arm("secondary")), "undeclared")
    # the fitter's commit is a code commit of the record (verify_git checks it like the arms')
    rec = _record()
    for a in ("A1", "A2"):
        rec["rule_arms"][a]["fitter"]["code_commit"] = "f" * 40
    assert "f" * 40 in AF.check_record(rec, plan_text=PLAN)["code_commits"]
    with pytest.raises(AF.ArmsFreezeError, match="origin/main"):
        AF.check_record(rec, plan_text=PLAN, verify_git=True)


# --- the constants files (constants_root)

def _constants_doc(rec, seed=0):
    """A constants file of unit 1's schema consistent with ``rec``'s label_tables and t1 (synthetic vectors)."""
    rng = np.random.default_rng(seed)
    nodes = {}
    for n in [*B.ALL_T0, *rec["t1"]["suites"]]:
        a1 = rng.dirichlet(np.ones(N_BINS))
        a2 = a1.copy()
        a2[INERT] = 0.0
        a2 = a2 / a2.sum()
        nodes[n] = {"tier": "T1" if n in rec["t1"]["suites"] else "T0",
                    "source": "g5" if n in rec["t1"]["suites"] else "sweep2",
                    "A1": [float(x) for x in a1], "A2": [float(x) for x in a2], "sigma_node": SIG,
                    "dev_instances": sorted(i for i, v in ASSIGN.items() if v["node"] == n and v["split"] == "dev"),
                    "rows": {"dev": 30, "A1": 28, "A2": 24}}
    lt = rec["label_tables"]
    return {"schema": AC.SCHEMA, "written_by": "test", "fit_population": AC.FIT_POPULATION, "rules": AC.RULES,
            "fitter": {"path": AC.FITTER_PATH, "sha256": "5" * 64, "code_commit": BASE_COMMIT},
            "row_order": "proposal_id", "split_file": {"path": AC.SPLIT_PATH, "sha256": p3_split.P3_SPLIT_SHA256},
            "gate_input_builder": {"path": AC.BUILDER_PATH, "sha256": rec["gate_input_builder"]["sha256"]},
            "toolchain": {"python": "3.13.15", "numpy": "2.4.4", "scipy": "1.17.1",
                          "interpreter": "/work/dwong/arms_t0_20261123/venv/bin/python3"},
            "sources": {s: {**{k: lt[s][k] for k in ("receipt_sha256", "traindev_partition_sha256",
                                                     "label_block_sha256", "proposals_sha256")},
                            "configs_sha256": None} for s in lt if s in B.GATE_SOURCES},
            "t1": {k: rec["t1"][k] for k in ("suites", "modes", "d3_k6")},
            "t0_nodes": list(B.ALL_T0), "d3_nodes": list(AC.D3_NODES), "nodes": nodes}


def _with_constants(root, rec=None, doc=None, d3_doc=None, rel="rc/C3_RULE_ARM_CONSTANTS.json"):
    rec = rec or _record()
    doc = doc or _constants_doc(rec)
    data = AF._dump(doc)
    _file(root, rel, data)
    d3 = None
    if d3_doc is not None:
        d3 = ("rc/D3_CONSTANTS.json", AF._dump(d3_doc))
        _file(root, d3[0], d3[1])
    fields = AF.postfreeze_fields(data, constants_path=rel, amendment_path=rec["amendments"][0]["path"],
                                  amendment_sha256=rec["amendments"][0]["sha256"], d3=d3)
    rec.update(fields)
    return rec, doc


def test_postfreeze_fields_writer_and_the_constants_file_check(tmp_path):
    rec, doc = _with_constants(tmp_path)
    assert rec["rule_arms"]["A0"] == {"rule": "r1.c3.offline_eval.rho", "constants": None}
    assert rec["rule_arms"]["A1"]["offline"] == "no rule layer; no verify offline"
    assert rec["rule_arms"]["A1"]["receipts"] == {"sweep2": "8" * 64, "g5": "8" * 64}
    assert rec["rule_arms"]["d3_constants"] is None and rec["amendments"][0]["plan_row"] == "R1-POSTFREEZE-READS"
    for arm in ("A1", "A2"):
        assert all(AC.same_bits(rec["rule_arms"][arm]["vectors"][n], doc["nodes"][n][arm]) for n in doc["nodes"])
    rendered = AF.parse_record(AF.render_record(rec))                    # the record's JSON keeps every bit
    out = AF.check_record(rendered, plan_text=PLAN, constants_root=tmp_path)
    assert out["pass"] and out["constants_files_rehashed"] == 1 and out["amendments_rehashed"] == 0
    assert AF.check_record(rendered, plan_text=PLAN)["constants_files_rehashed"] == 0      # structure only

    def refused(mutate, match, root=tmp_path):
        r = copy.deepcopy(rec)
        mutate(r)
        with pytest.raises(AF.ArmsFreezeError, match=match):
            AF.check_record(r, plan_text=PLAN, constants_root=root)

    # a wrong constants sha256; a missing file; a file changed after it was pinned
    refused(lambda r: [r["rule_arms"][a]["constants"].__setitem__("sha256", "0" * 64) for a in ("A1", "A2")],
            "differs from its sha256")
    refused(lambda r: None, "is missing", root=tmp_path / "elsewhere")
    # vectors differing from the constants file by one ulp, in one bin of one node
    def ulp(r, arm="A2", node="openml_sonar"):
        v = r["rule_arms"][arm]["vectors"][node]
        v[3] = float(np.nextafter(v[3], 1.0))
    refused(ulp, "A2: the vectors differ")
    refused(lambda r: ulp(r, "A1", "mlgym_fmnist"), "A1: the vectors differ")
    # the fit's receipts, partitions or tables are not the record's label_tables; the fitter or T1 setting differ
    refused(lambda r: r["label_tables"]["sweep2"].__setitem__("label_block_sha256", "0" * 64),
            "other than label_tables.sweep2")
    refused(lambda r: [r["rule_arms"][a]["receipts"].__setitem__("g5", "0" * 64) for a in ("A1", "A2")],
            "receipts differ")
    refused(lambda r: [r["rule_arms"][a]["fitter"].__setitem__("sha256", "0" * 64) for a in ("A1", "A2")],
            "fitter differs")
    other = copy.deepcopy(doc)                                    # N2: fitted with another builder than the record's
    other["gate_input_builder"]["sha256"] = "0" * 64
    r2, _ = _with_constants(tmp_path / "builder", doc=other)
    with pytest.raises(AF.ArmsFreezeError, match="constants file's gate_input_builder is not the record's"):
        AF.check_record(r2, plan_text=PLAN, constants_root=tmp_path / "builder")
    refused(lambda r: r["t1"].__setitem__("modes", ["history"]), "T1 setting")
    dev = [i for i in T1_INST if ASSIGN[i]["split"] == "dev"]
    refused(lambda r: r["t1"]["instances"].remove(dev[0]), "dev instances")


def test_postfreeze_d3_constants_file(tmp_path):
    rec0 = _record()
    doc = _constants_doc(rec0)
    rec, _ = _with_constants(tmp_path / "same", rec=copy.deepcopy(rec0), doc=doc, d3_doc=doc)
    out = AF.check_record(rec, plan_text=PLAN, constants_root=tmp_path / "same")
    assert out["constants_files_rehashed"] == 2 and rec["rule_arms"]["d3_constants"]["path"] == "rc/D3_CONSTANTS.json"
    # a D.3 file of the same schema family carrying only the seven D.3 nodes (and other fields, e.g. LADDER)
    d3 = {"schema": "r1_c3_rule_arm_constants/v2-d3", "nodes": {n: {**doc["nodes"][n], "ladder_eta": 0.0}
                                                                for n in AC.D3_NODES}}
    rec, _ = _with_constants(tmp_path / "seven", rec=copy.deepcopy(rec0), doc=doc, d3_doc=d3)
    assert AF.check_record(rec, plan_text=PLAN, constants_root=tmp_path / "seven")["pass"]
    # openml_wdbc is not a D.3 node: a difference there is not compared
    other = copy.deepcopy(doc)
    other["nodes"]["openml_wdbc"]["A1"][2] = float(np.nextafter(other["nodes"]["openml_wdbc"]["A1"][2], 1.0))
    rec, _ = _with_constants(tmp_path / "wdbc", rec=copy.deepcopy(rec0), doc=doc, d3_doc=other)
    assert AF.check_record(rec, plan_text=PLAN, constants_root=tmp_path / "wdbc")["pass"]
    # a D.3 node differing by one ulp, or missing, is refused: by the writer, and by the checker
    bad = copy.deepcopy(doc)
    bad["nodes"]["openml_climate"]["A2"][5] = float(np.nextafter(bad["nodes"]["openml_climate"]["A2"][5], 1.0))
    with pytest.raises(AF.ArmsFreezeError, match="D.3 nodes"):
        _with_constants(tmp_path / "w1", rec=copy.deepcopy(rec0), doc=doc, d3_doc=bad)
    rec, _ = _with_constants(tmp_path / "c1", rec=copy.deepcopy(rec0), doc=doc, d3_doc=doc)
    _file(tmp_path / "c1", "rc/D3_CONSTANTS.json", AF._dump(bad))
    rec["rule_arms"]["d3_constants"]["sha256"] = AF._sha(AF._dump(bad))
    with pytest.raises(AF.ArmsFreezeError, match=r"A2: the D.3 nodes \['openml_climate'\] differ"):
        AF.check_record(rec, plan_text=PLAN, constants_root=tmp_path / "c1")
    lack = copy.deepcopy(doc)
    lack["nodes"].pop("openml_sonar")
    with pytest.raises(AF.ArmsFreezeError, match="lacks the D.3 nodes"):
        _with_constants(tmp_path / "w2", rec=copy.deepcopy(rec0), doc=doc, d3_doc=lack)
    # a D.3 pin whose file changed
    rec, _ = _with_constants(tmp_path / "c2", rec=copy.deepcopy(rec0), doc=doc, d3_doc=doc)
    rec["rule_arms"]["d3_constants"]["sha256"] = "0" * 64
    with pytest.raises(AF.ArmsFreezeError, match="d3_constants.*differs from its sha256"):
        AF.check_record(rec, plan_text=PLAN, constants_root=tmp_path / "c2")


def test_postfreeze_constants_from_the_fitter_round_trip(tmp_path):
    """A constants file written by unit 1's document builder (synthetic fit) enters the record unchanged."""
    rec = _t0_only(_record())
    rows = []
    for node in B.ALL_T0:
        for inst, v in sorted(ASSIGN.items()):
            if v["node"] == node and v["split"] == "dev":
                seed = int(inst.rsplit("__s", 1)[1])
                rows += [_row(node, seed, m, t, "noop" if t == 2 else "audit") for m in B.T0_MODES for t in (2, 4, 5)]
    labels = [_label(r) for r in rows]
    fitted, items = AC.fit_sources({"sweep2": (rows, labels)}, t1=None, assign=ASSIGN)
    lt = rec["label_tables"]["sweep2"]
    doc = AC.document(fitted, items, sources_meta={"sweep2": {**{k: lt[k] for k in (
        "receipt_sha256", "traindev_partition_sha256", "label_block_sha256", "proposals_sha256")},
        "configs_sha256": "c" * 64}}, t1=None,
        fitter={"path": AC.FITTER_PATH, "sha256": "5" * 64, "code_commit": BASE_COMMIT},
        builder_sha256=rec["gate_input_builder"]["sha256"])
    assert set(doc["toolchain"]) == {"python", "numpy", "scipy", "interpreter"}      # the running interpreter's
    rec, _ = _with_constants(tmp_path, rec=rec, doc=doc)
    out = AF.check_record(AF.parse_record(AF.render_record(rec)), plan_text=PLAN, constants_root=tmp_path)
    assert out["pass"] and out["constants_files_rehashed"] == 1
    assert all(AC.same_bits(rec["rule_arms"]["A2"]["vectors"][n], fitted[n]["A2"]) for n in B.ALL_T0)


# --- the signed amendment as a committed file (verify_committed)

def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", *args], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


AMEND_PATH = "docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_20261123.md"


def _amendment_text(**over):
    from r1.harness import REPO
    block = {"amends": f"{AF.PREREG_PATH} sha256 {AF.PREREG_SHA256}", "plan_row": "R1-POSTFREEZE-READS",
             "status": "SIGNED", "frozen": "true", "constants_fitter_sha256": "5" * 64,
             "arms_freeze_sha256": AF._sha_file(REPO / "r1/c3/arms_freeze.py"),
             "descriptive_rows_sha256": "1" * 64, "dispersion_estimate_sha256": "2" * 64, "c1_rates_sha256": "3" * 64,
             "open_items": "1-24 settled as recommended",
             "signed_by": "author, in chat, 24 November 2026", "signed_utc": "2026-11-24T09:00:00Z",
             "frozen_utc": "2026-11-24T10:00:00Z"}                    # the key names of the sign-ready A§13
    block.update(over)
    body = "\n".join(f"{k}: {v}" for k, v in block.items() if v is not None)
    return f"# Amendment (synthetic)\n\nText.\n\n```\n{body}\n```\n"


@pytest.fixture()
def amend_repo(tmp_path):
    """A git checkout holding the files check_record reads from ``repo`` (copies) and a synthetic amendment."""
    from r1.harness import REPO
    repo = tmp_path / "repo"
    for rel in (AF.PREREG_PATH, "r1/c3/gate.py", "r1/c3/gate_input_builder.py", "r1/c3/arms_freeze.py",
                "r1/c3/arms_constants.py", "r1/c3/splits/c3_p3_split_v1.json"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, repo / rel)
    (repo / "docs/r1/PLAN.md").write_text(PLAN)
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    fitter = {"path": AC.FITTER_PATH, "sha256": AF._sha_file(repo / AC.FITTER_PATH),       # the fitter's commit
              "code_commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).decode().strip()}

    def commit(text):
        (repo / AMEND_PATH).parent.mkdir(parents=True, exist_ok=True)
        (repo / AMEND_PATH).write_text(text)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "x", "--allow-empty")
        return AF._sha(text.encode())
    return repo, commit, fitter


def _bound(rec, fitter):
    """``rec`` with the temporary checkout's committed fitter as rule_arms' fitter."""
    for a in ("A1", "A2"):
        rec["rule_arms"][a]["fitter"] = dict(fitter)
    return rec


def test_postfreeze_amendment_checked_as_a_committed_signed_file(amend_repo):
    repo, commit, fitter = amend_repo
    rec = _bound(_record(), fitter)

    def text(**over):                                # A§13 binding the checkout's fitter unless overridden
        return _amendment_text(**{"constants_fitter_sha256": fitter["sha256"], **over})
    rec["amendments"][0].update(path=AMEND_PATH, sha256=commit(text()))
    out = AF.check_record(rec, repo=repo, plan_text=PLAN, verify_committed=True)
    assert out["pass"] and out["amendments_rehashed"] == 1
    assert AF.check_record(rec, repo=repo, plan_text=PLAN)["amendments_rehashed"] == 0
    cases = [({"frozen": "false"}, "frozen"),                                    # the draft
             ({"plan_row": "R1-POSTFREEZE-READS-CHOICES"}, "plan_row"),
             ({"amends": f"{AF.PREREG_PATH} sha256 {'0' * 64}"}, "amends"),
             ({"constants_fitter_sha256": "<pending: unit 1>"}, "constants_fitter_sha256"),   # unit 1 not bound
             ({"arms_freeze_sha256": "0" * 64}, "arms_freeze_sha256"),                     # unit 2 not bound
             ({"signed_by": "<pending>"}, "not signed"),
             ({"frozen_utc": "<pending>"}, "not signed"),
             # M1: signed_utc in the frozen_utc form, no later than frozen_utc (sign-ready A§13 placeholder refused)
             ({"signed_utc": "<filled when published on main>"}, "not signed"),
             ({"signed_utc": None}, "not signed"),
             ({"signed_utc": "yesterday"}, "not signed"),
             ({"signed_utc": "2026-11-24T10:00:01Z"}, "not signed"),           # later than frozen_utc
             ({"signed_utc": "2026-11-24T09:00:00+00:00"}, "not signed"),      # an offset, not Z
             ({"frozen_utc": "2026-11-24T10:00:00.5Z"}, "not signed"),         # a fraction
             ({"frozen_utc": "2026-13-24T10:00:00Z"}, "not signed"),           # not a date
             ({"frozen": "true (frozen when the record pins it)"}, "frozen"),  # nothing may follow true
             ({"frozen": None}, "no final fenced block")]
    for over, match in cases:
        rec["amendments"][0]["sha256"] = commit(text(**over))
        with pytest.raises(AF.ArmsFreezeError, match=match):
            AF.check_record(rec, repo=repo, plan_text=PLAN, verify_committed=True)
    for ok in ({"signed_utc": "2026-11-24T10:00:00Z"}, {"signed_utc": "2026-11-24T09:59Z"}):   # equal; no seconds
        rec["amendments"][0]["sha256"] = commit(text(**ok))
        assert AF.check_record(rec, repo=repo, plan_text=PLAN, verify_committed=True)["amendments_rehashed"] == 1
    rec["amendments"][0]["sha256"] = commit(text())
    # N4: A§13's arms_freeze_sha256 is compared with the committed arms_freeze.py, not a changed working file
    real = (repo / "r1/c3/arms_freeze.py").read_bytes()
    (repo / "r1/c3/arms_freeze.py").write_bytes(real + b"\n")
    with pytest.raises(AF.ArmsFreezeError, match="arms_freeze.py differs from committed HEAD"):
        AF.check_record(rec, repo=repo, plan_text=PLAN, verify_committed=True)
    (repo / "r1/c3/arms_freeze.py").write_bytes(real)
    # the record's sha256 is not the committed file's; the working file differs from HEAD; an uncommitted path
    bad = copy.deepcopy(rec)
    bad["amendments"][0]["sha256"] = "0" * 64
    with pytest.raises(AF.ArmsFreezeError, match="differs from its sha256"):
        AF.check_record(bad, repo=repo, plan_text=PLAN, verify_committed=True)
    (repo / AMEND_PATH).write_text(text() + "\n")
    with pytest.raises(AF.ArmsFreezeError, match="differs from committed HEAD"):
        AF.check_record(rec, repo=repo, plan_text=PLAN, verify_committed=True)
    (repo / AMEND_PATH).write_text(text())
    other = "docs/r1/authorizations/UNCOMMITTED.md"
    (repo / other).write_text(text())
    bad["amendments"][0].update(path=other, sha256=AF._sha(text().encode()))
    with pytest.raises(AF.ArmsFreezeError, match="not a regular committed file"):
        AF.check_record(bad, repo=repo, plan_text=PLAN, verify_committed=True)
    # N3: the fitter's sha256 is that of r1/c3/arms_constants.py at its code commit
    bad = copy.deepcopy(rec)
    for a in ("A1", "A2"):
        bad["rule_arms"][a]["fitter"]["sha256"] = "5" * 64
    bad["amendments"][0]["sha256"] = commit(text(constants_fitter_sha256="5" * 64))
    with pytest.raises(AF.ArmsFreezeError, match="at its code commit"):
        AF.check_record(bad, repo=repo, plan_text=PLAN, verify_committed=True)
    bad = copy.deepcopy(rec)
    for a in ("A1", "A2"):
        bad["rule_arms"][a]["fitter"]["code_commit"] = "f" * 40
    with pytest.raises(AF.ArmsFreezeError, match="not in the fitter's code commit"):
        AF.check_record(bad, repo=repo, plan_text=PLAN, verify_committed=True)


def test_postfreeze_fields_cli_and_the_full_check(amend_repo, monkeypatch, tmp_path, capsys):
    repo, commit, fitter = amend_repo
    import r1.harness
    monkeypatch.setattr(r1.harness, "REPO", repo)
    rec = _record()
    root = tmp_path / "A"
    doc = _constants_doc(rec)
    doc["fitter"] = dict(fitter)
    _file(root, "rc/C.json", AF._dump(doc))
    _file(root, "rc/D3.json", AF._dump(doc))
    sha = commit(_amendment_text(constants_fitter_sha256=fitter["sha256"]))
    args = ["postfreeze-fields", "--constants", "rc/C.json", "--constants-root", str(root), "--amendment", AMEND_PATH,
            "--d3-constants", "rc/D3.json"]
    assert AF.main(args + ["--out", str(tmp_path / "fields.json")]) == 0
    printed = json.loads(capsys.readouterr().out)
    fields = json.loads((tmp_path / "fields.json").read_text())
    assert printed["amendment_sha256"] == sha == fields["amendments"][0]["sha256"]
    assert fields["rule_arms"]["d3_constants"] == {"path": "rc/D3.json", "sha256": AF._sha(AF._dump(doc))}
    rec.update(fields)
    out = AF.check_record(rec, repo=repo, plan_text=PLAN, constants_root=root, verify_committed=True)
    assert out["constants_files_rehashed"] == 2 and out["amendments_rehashed"] == 1
    with pytest.raises(AF.ArmsFreezeError, match="written once"):
        AF.main(args + ["--out", str(tmp_path / "fields.json")])
    commit(_amendment_text(frozen="false", constants_fitter_sha256=fitter["sha256"]))     # an unfrozen amendment
    with pytest.raises(AF.ArmsFreezeError, match="frozen"):
        AF.main(args + ["--out", str(tmp_path / "f2.json")])
    commit(_amendment_text(constants_fitter_sha256=fitter["sha256"]))
    (repo / "docs/r1/PLAN.md").write_text(PLAN_WITHOUT_ROW)                      # the row is not on PLAN
    with pytest.raises(AF.ArmsFreezeError, match="author row of PLAN"):
        AF.main(args + ["--out", str(tmp_path / "f3.json")])
    assert not (tmp_path / "f2.json").exists() and not (tmp_path / "f3.json").exists()


def test_cli_check_and_render_pass_the_new_options(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(AF, "check_record", lambda *a, **k: seen.append(k) or {"pass": True})
    monkeypatch.chdir(tmp_path)
    (tmp_path / "rec.json").write_text(json.dumps(_record()))
    AF.main(["render", "--json", str(tmp_path / "rec.json"), "--out", "docs/r1/arms_frozen/X.md"])
    assert seen[-1]["verify_committed"] is True and seen[-1]["constants_root"] is None
    assert seen[-1]["require_file_checks"] is True
    AF.main(["check", "--record", "docs/r1/arms_frozen/X.md", "--artefact-root", "/A"])
    assert seen[-1]["constants_root"] == "/A" and seen[-1]["verify_committed"] is True
    assert seen[-1]["require_file_checks"] is True
    AF.main(["check", "--record", "docs/r1/arms_frozen/X.md", "--artefact-root", "/A", "--constants-root", "/C",
             "--no-git"])                     # M2: --no-git skips commit ancestry only, not the committed amendment
    assert seen[-1]["constants_root"] == "/C" and seen[-1]["verify_committed"] is True
    assert seen[-1]["verify_git"] is False and seen[-1]["require_file_checks"] is True


def test_cli_refuses_a_pass_without_the_file_checks(tmp_path, monkeypatch):
    """M2: for a record with amendments/rule_arms, check without a constants root and render without
    --constants-root are refused; nothing is written. The Python API keeps its opt-in (default off)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "rec.json").write_text(json.dumps(_record()))
    with pytest.raises(AF.ArmsFreezeError, match="need both file checks"):
        AF.main(["render", "--json", str(tmp_path / "rec.json"), "--out", "docs/r1/arms_frozen/X.md"])
    assert not (tmp_path / "docs/r1/arms_frozen/X.md").exists()
    rec_md = tmp_path / "docs/r1/arms_frozen/Y.md"
    rec_md.parent.mkdir(parents=True)
    rec_md.write_text(AF.render_record(_record()))
    for extra in ([], ["--no-git"], ["--release-root", f"sweep2={tmp_path}"]):
        with pytest.raises(AF.ArmsFreezeError, match="need both file checks"):
            AF.main(["check", "--record", "docs/r1/arms_frozen/Y.md", *extra])
    with pytest.raises(AF.ArmsFreezeError, match="need both file checks"):
        AF.check_record(_record(), plan_text=PLAN, constants_root=tmp_path, require_file_checks=True)
    assert AF.check_record(_record(), plan_text=PLAN)["pass"]
