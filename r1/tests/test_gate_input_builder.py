"""Gate-input builder (preregistration §3, PRE-MEM C, PRE-DUP A, PRE-DIV A, P3): synthetic records only; no table,
label or evaluation file is opened."""
import copy
import json
import random

import numpy as np
import pytest

from r1.c3 import gate as G
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split, rules
from r1.c3.labels import moments, soft_label

SIG = 0.01
MODES = B.T0_MODES
ASSIGN = p3_split.assignment(p3_split.load())


def _row(node, seed, mode, t, kind="audit", src="s2", key=None):
    pid = f"{src}_{mode}:{node}__s{seed}:t{t:03d}"
    rng = random.Random(pid)
    return {"proposal_id": pid, "instance": f"{node}__s{seed}", "instance_seed": seed, "node": node,
            "source": f"{src}_{mode}", "memory_mode": mode, "budget_index": t, "sigma_node": SIG, "sigma_cmp": SIG,
            "delta_hat": 0.0 if kind == "noop" else rng.gauss(0, SIG), "noop": kind == "noop",
            "duplicate": kind == "dup", "features": {},
            "incumbent_hash": (key or pid) + ":i", "candidate_hash": (key or pid) + ":c"}


def _label(row):
    if row["noop"]:
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "rule_noop",
                "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}}
    d = random.Random("L" + row["proposal_id"]).gauss(0.002, SIG)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "audit",
            "seeds": list(B.T0_LABEL_SEEDS), "delta_label": d, "se_label": 0.004,
            "soft_parameters": {"inert": False, "sigma_node": SIG, "k_label": 5, "delta_label": d, "se_label": 0.004}}


def _evaluation(row):
    d = random.Random("E" + row["proposal_id"]).gauss(0.002, SIG)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "seeds": list(B.T0_EVALUATION_SEEDS),
            "delta_evaluation": d, "se_evaluation": 0.004}


def _world(nodes=G.T0_NODES):
    s2, s1 = [], []
    for node in nodes:
        for inst, v in ASSIGN.items():
            if v["node"] != node:
                continue
            seed = int(inst.rsplit("__s", 1)[1])
            for mode in MODES:
                s2 += [_row(node, seed, mode, 2, "noop"), _row(node, seed, mode, 3, "dup")]
                s2 += [_row(node, seed, mode, t) for t in range(4, 8)]
                s1 += [_row(node, seed, mode, t, src="s1") for t in range(2, 5)]
    labelled = [r for r in s2 if not r["duplicate"]]
    sweep2 = B.Source("sweep2", s2, [_label(r) for r in labelled], [_evaluation(r) for r in labelled if not r["noop"]])
    sweep1 = B.Source("sweep1", s1, gate=False)
    rng = np.random.default_rng(3)
    preds = {a: {r["proposal_id"]: rng.dirichlet(np.ones(12)).tolist() for r in s2} for a in ("A3", "A5")}
    noise = {n: {"sigma_node": SIG, "delta_n": 0.002} for n in nodes}
    return [sweep2, sweep1], preds, noise


def _node(gi, node):
    return next(n for n in gi["nodes"] if n["node"] == node)


def _val(gi, node, split, series, inst):
    b = _node(gi, node)[split]
    return b[series][b["instance_ids"].index(inst)]


def _first(node, split):
    return sorted(i for i, v in ASSIGN.items() if v["node"] == node and v["split"] == split)[0]


@pytest.fixture(scope="module")
def world():
    return _world()


def test_primary_secondary_and_sensitivity_layout(world):
    out = B.runs(*world)
    gi, rep = out["primary"]
    assert gi["schema"] == "r1_d8_gate_input/v3.1" and gi["split"] == G.SPLIT
    assert gi["t0_nodes"] == sorted(B.PRIMARY_T0) and len(gi["nodes"]) == 7
    assert "openml_wdbc" not in {n["node"] for n in gi["nodes"]} and rep["skipped_nodes"] == ["openml_wdbc"]
    assert out["wdbc_sensitivity"][0]["t0_nodes"] == sorted(G.T0_NODES)
    assert len(out["wdbc_sensitivity"][0]["nodes"]) == 8
    for n in gi["nodes"]:
        assert n["suite"] is None and n["tier"] == "T0" and n["delta_n"] == 0.002
        assert [len(n[s]["instance_ids"]) for s in ("train", "dev", "test")] == [6, 3, 9]
        assert set(n["train"]) == {"instance_ids", "A2", "oracle"}
        assert set(n["test"]) == {"instance_ids", "A2", "oracle", "A3", "A5"}
        for s in ("train", "dev", "test"):
            assert all(ASSIGN[i]["split"] == s for i in n[s]["instance_ids"])
    G._validate(gi)


def test_oracle_utility_by_hand(world):
    gi, _ = B.build(*world)
    node, inst = "digits_mlp", _first("digits_mlp", "test")
    sweep2 = world[0][0]
    labels = {l["proposal_id"]: l for l in sweep2.labels}
    evals = {e["proposal_id"]: e for e in sweep2.evaluations}
    per_mode = []
    for mode in MODES:
        rs = []
        for row in [r for r in sweep2.rows if r["instance"] == inst and r["memory_mode"] == mode]:
            if row["duplicate"]:
                rs.append(0.0)
                continue
            lab = labels[row["proposal_id"]]
            p = (soft_label(None, None, SIG, inert=True) if row["noop"] else
                 soft_label(lab["delta_label"], None, SIG, sigma_mode="pooled_node", k_label=5))
            pi, mu, tau = moments(p[None], np.array([SIG]), tau_floor_z=0.15)
            ex, kp = rules.decide(pi, mu, tau, np.array([SIG]), np.array([0.1 * SIG]), np.array([row["delta_hat"]]))
            d = 0.0 if row["noop"] else evals[row["proposal_id"]]["delta_evaluation"]
            rs.append(float(d * kp[0] - 0.1 * SIG * ex[0]))
        per_mode.append(20 * np.mean(rs))
    assert _val(gi, node, "test", "oracle", inst) == pytest.approx(np.mean(per_mode), abs=1e-15)


def test_a2_uses_only_the_dev_label_block_and_delta_true_the_evaluation_block(world):
    base, _ = B.build(*world)
    srcs, preds, noise = copy.deepcopy(world)
    for lab in srcs[0].labels:          # change every train and test label value
        if lab["label_kind"] == "audit" and ASSIGN[lab["proposal_id"].split(":")[1]]["split"] != "dev":
            lab["delta_label"] = lab["soft_parameters"]["delta_label"] = lab["delta_label"] + 0.05
    moved, _ = B.build(srcs, preds, noise)
    for b, m in zip(base["nodes"], moved["nodes"]):
        for s in ("train", "dev", "test"):
            assert b[s]["A2"] == m[s]["A2"]                  # A2 unchanged: fitted on dev only
        assert b["test"]["A3"] == m["test"]["A3"] and b["test"]["A5"] == m["test"]["A5"]
    assert any(b["test"]["oracle"] != m["test"]["oracle"] for b, m in zip(base["nodes"], moved["nodes"]))
    srcs, preds, noise = copy.deepcopy(world)
    for lab in srcs[0].labels:          # change dev labels: A2 moves
        if lab["label_kind"] == "audit" and ASSIGN[lab["proposal_id"].split(":")[1]]["split"] == "dev":
            lab["delta_label"] = lab["soft_parameters"]["delta_label"] = lab["delta_label"] + 0.05
    moved, _ = B.build(srcs, preds, noise)
    assert any(b["test"]["A2"] != m["test"]["A2"] for b, m in zip(base["nodes"], moved["nodes"]))
    srcs, preds, noise = copy.deepcopy(world)
    for ev in srcs[0].evaluations:      # evaluation values move realised values, not decisions
        ev["delta_evaluation"] += 1.0
    moved, _ = B.build(srcs, preds, noise)
    assert any(b["train"]["oracle"] != m["train"]["oracle"] for b, m in zip(base["nodes"], moved["nodes"]))


def test_pre_dup_primary_drops_test_repeats_and_keeps_train_dev(world):
    srcs, preds, noise = copy.deepcopy(world)
    node = "openml_sonar"
    test_inst, train_inst = _first(node, "test"), _first(node, "train")
    seed_tr = int(train_inst.rsplit("__s", 1)[1])
    target = [r for r in srcs[0].rows if r["instance"] == test_inst and r["memory_mode"] == "none"]
    for r in target:                    # every proposal of one mode repeats a sweep-1 train-instance key
        key = r["proposal_id"]
        r["incumbent_hash"], r["candidate_hash"] = key + ":i", key + ":c"
        srcs[1].rows.append(_row(node, seed_tr, "none", 50 + r["budget_index"], src="s1", key=key))
    prim, rep = B.build(srcs, preds, noise, population="primary")
    full, _ = B.build(srcs, preds, noise, population="full")
    only_append, _ = B.build(srcs, preds, noise, population="full", modes=("append_only_summary",))
    assert rep["nodes"][node]["repeats_dropped_test"] == len(target)
    assert rep["nodes"][node]["mode_fallbacks"]["test"] == [f"{test_inst}:none"]
    for s in B.TEST_SERIES:             # fallback: U is the other mode's U
        assert _val(prim, node, "test", s, test_inst) == _val(only_append, node, "test", s, test_inst)
        assert _val(full, node, "test", s, test_inst) != _val(prim, node, "test", s, test_inst)
    for a, b in zip(prim["nodes"], full["nodes"]):
        assert a["train"] == b["train"] and a["dev"] == b["dev"]
    # both modes repeated -> the instance is left out of the primary input and reported
    for r in [r for r in srcs[0].rows if r["instance"] == test_inst and r["memory_mode"] == "append_only_summary"]:
        key = r["proposal_id"]
        r["incumbent_hash"], r["candidate_hash"] = key + ":i", key + ":c"
        srcs[1].rows.append(_row(node, seed_tr, "append_only_summary", 80 + r["budget_index"], src="s1", key=key))
    prim, rep = B.build(srcs, preds, noise)
    assert test_inst not in _node(prim, node)["test"]["instance_ids"]
    assert rep["nodes"][node]["left_out_instances"]["test"] == [test_inst]


def test_pre_dup_renormalises_kept_weights(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "tabular_mlp", _first("tabular_mlp", "test")
    dev_inst = _first(node, "dev")
    victim = next(r for r in srcs[0].rows if r["instance"] == inst and r["budget_index"] == 4
                  and r["memory_mode"] == "none")
    dev_row = next(r for r in srcs[0].rows if r["instance"] == dev_inst and r["budget_index"] == 5
                   and r["memory_mode"] == "none")
    victim["incumbent_hash"], victim["candidate_hash"] = dev_row["incumbent_hash"], dev_row["candidate_hash"]
    prim, rep = B.build(srcs, preds, noise)
    assert rep["nodes"][node]["repeats_dropped_test"] == 1
    srcs2 = copy.deepcopy(srcs)          # same instance with the repeat removed outright: identical U
    srcs2[0].rows = [r for r in srcs2[0].rows if r["proposal_id"] != victim["proposal_id"]]
    srcs2[0].labels = [x for x in srcs2[0].labels if x["proposal_id"] != victim["proposal_id"]]
    srcs2[0].evaluations = [x for x in srcs2[0].evaluations if x["proposal_id"] != victim["proposal_id"]]
    gone, _ = B.build(srcs2, preds, noise, population="full")
    for s in B.TEST_SERIES:
        assert _val(prim, node, "test", s, inst) == pytest.approx(_val(gone, node, "test", s, inst), abs=1e-15)


def test_pre_div_partial_and_divergent(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "openml_climate", _first("openml_climate", "test")
    rows = [r for r in srcs[0].rows if r["instance"] == inst and not (r["noop"] or r["duplicate"])]
    ev = {e["proposal_id"]: e for e in srcs[0].evaluations}
    ev[rows[0]["proposal_id"]]["divergent_seeds"] = [7006, 7009]                 # partial
    ev[rows[1]["proposal_id"]].update(divergent_seeds=[7006, 7007, 7008], delta_evaluation=None)
    div, rep = B.build(srcs, preds, noise)
    assert rep["nodes"][node]["partial"] == 1 and rep["nodes"][node]["divergent"] == 1
    assert set(rep["nodes"][node]["divergent_executed"]) == set(B.TRAIN_DEV_SERIES) | set(B.TEST_SERIES)
    # divergent: r = -g * execute, i.e. the same as a proposal with Delta_true = 0
    srcs0 = copy.deepcopy(srcs)
    e0 = {e["proposal_id"]: e for e in srcs0[0].evaluations}[rows[1]["proposal_id"]]
    e0.pop("divergent_seeds")
    e0["delta_evaluation"] = 0.0
    zero, _ = B.build(srcs0, preds, noise)
    for s in B.TEST_SERIES:
        assert _val(div, node, "test", s, inst) == pytest.approx(_val(zero, node, "test", s, inst), abs=1e-15)
    with pytest.raises(B.BuilderError, match="divergent proposal carries"):
        bad = copy.deepcopy(srcs)
        {e["proposal_id"]: e for e in bad[0].evaluations}[rows[1]["proposal_id"]]["delta_evaluation"] = 0.1
        B.build(bad, preds, noise)


def test_divergent_label_is_never_executed_by_the_oracle(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "openml_ionosphere", _first("openml_ionosphere", "test")
    rows = [r for r in srcs[0].rows if r["instance"] == inst and not (r["noop"] or r["duplicate"])]
    lab = {l["proposal_id"]: l for l in srcs[0].labels}[rows[0]["proposal_id"]]
    lab.update(label_kind="divergent", delta_label=None, soft_parameters={"inert": False})
    ev = {e["proposal_id"]: e for e in srcs[0].evaluations}[rows[0]["proposal_id"]]
    ev["delta_evaluation"] = 0.0
    a, _ = B.build(srcs, preds, noise)
    srcs[0].rows = [r for r in srcs[0].rows if r["proposal_id"] != rows[0]["proposal_id"]]
    srcs[0].labels = [x for x in srcs[0].labels if x["proposal_id"] != rows[0]["proposal_id"]]
    srcs[0].evaluations = [x for x in srcs[0].evaluations if x["proposal_id"] != rows[0]["proposal_id"]]
    # oracle skips it (r = 0, weight 1), so its U is 5/6 of the U without it on that mode
    b, _ = B.build(srcs, preds, noise)
    mode = rows[0]["memory_mode"]
    other = [m for m in MODES if m != mode][0]
    only_other, _ = B.build(srcs, preds, noise, modes=(other,))
    only_mode, _ = B.build(srcs, preds, noise, modes=(mode,))
    u_mode_with = 2 * _val(a, node, "test", "oracle", inst) - _val(only_other, node, "test", "oracle", inst)
    assert u_mode_with == pytest.approx(_val(only_mode, node, "test", "oracle", inst) * 5 / 6, abs=1e-12)
    assert _val(b, node, "test", "oracle", inst) is not None


def test_input_order_does_not_change_the_output(world):
    a = json.dumps(B.build(*world), sort_keys=True)
    srcs, preds, noise = copy.deepcopy(world)
    for s in srcs:
        random.Random(1).shuffle(s.rows)
        random.Random(2).shuffle(s.labels)
        random.Random(3).shuffle(s.evaluations)
    assert json.dumps(B.build(srcs, preds, noise), sort_keys=True) == a


@pytest.mark.parametrize("mutate,match", [
    (lambda s, p: s[0].rows.append(_row("digits_mlp", 9011, "none", 2)), "not in the P3 split file"),
    (lambda s, p: s[0].labels[1].__setitem__("seeds", [7001, 7002, 7003, 7004, 7006]), "label seeds"),
    (lambda s, p: s[0].evaluations[0].__setitem__("seeds", [7001, 7002, 7003, 7004, 7005]), "seeds differ"),
    (lambda s, p: p["A5"].pop(s[0].evaluations[0]["proposal_id"]), "A5: no prediction"),
    (lambda s, p: s[0].labels.append({**s[0].labels[1], "proposal_id": next(
        r["proposal_id"] for r in s[0].rows if r["duplicate"])}), "within-campaign duplicate"),
    (lambda s, p: s[0].rows.append(dict(s[0].rows[0])), "duplicate proposal id"),
    (lambda s, p: s[0].rows[0].__setitem__("instance", "digits_mlp__s999"), "is not"),
    (lambda s, p: s[1].labels.append(s[0].labels[0]), "repeat-key source"),
    (lambda s, p: s[0].evaluations.pop(0), "without an evaluation row"),
])
def test_refusals(world, mutate, match):
    srcs, preds, noise = copy.deepcopy(world)
    mutate(srcs, preds)
    with pytest.raises(B.BuilderError, match=match):
        B.build(srcs, preds, noise)


def test_t0_node_set_and_noise_refusals(world):
    srcs, preds, noise = world
    with pytest.raises(B.BuilderError, match="t0_nodes"):
        B.build(srcs, preds, noise, t0_nodes=["mlab_cifar10"])
    with pytest.raises(B.BuilderError, match="δ_n"):
        B.build(srcs, preds, {k: v for k, v in noise.items() if k != "digits_mlp"})
    with pytest.raises(B.BuilderError, match="sigma_node differs"):
        B.build(srcs, preds, {**noise, "digits_mlp": {"sigma_node": 0.02, "delta_n": 0.002}})
    few = copy.deepcopy(world)
    few[0][0].rows = [r for r in few[0][0].rows if not (r["node"] == "openml_sonar" and
                                                         ASSIGN[r["instance"]]["split"] == "dev")]
    keep = {r["proposal_id"] for r in few[0][0].rows}
    few[0][0].labels = [x for x in few[0][0].labels if x["proposal_id"] in keep]
    few[0][0].evaluations = [x for x in few[0][0].evaluations if x["proposal_id"] in keep]
    with pytest.raises(B.BuilderError, match="declared T0 node openml_sonar has no instance"):
        B.build(*few)


def test_t1_nodes_suites_modes_and_k6_seeds(world):
    srcs, preds, noise = copy.deepcopy(world)
    t1rows = []
    for node in ("mlab_cifar10", "mlgym_fmnist"):
        for inst, v in ASSIGN.items():
            if v["node"] != node or (node == "mlgym_fmnist" and v["split"] == "dev"):
                continue
            seed = int(inst.rsplit("__s", 1)[1])
            t1rows += [_row(node, seed, "none", t, src="g5") for t in range(2, 6)]
    for r in t1rows:
        lab = _label(r)
        lab["seeds"] = list(B.D3_LABEL_SEEDS)
        lab["soft_parameters"]["k_label"] = 3
        ev = _evaluation(r)
        ev["seeds"] = list(B.D3_EVALUATION_SEEDS)
        srcs.append(B.Source("g5", [r], [lab], [ev]))
        for a in ("A3", "A5"):
            preds[a][r["proposal_id"]] = [1 / 12] * 12
    noise.update({n: {"sigma_node": SIG, "delta_n": 0.003} for n in ("mlab_cifar10", "mlgym_fmnist")})
    with pytest.raises(B.BuilderError, match="frozen T1 setting"):
        B.build(srcs, preds, noise)
    with pytest.raises(B.BuilderError, match="frozen suite"):
        B.build(srcs, preds, noise, t1=B.Tier1(suites={"mlab_cifar10": "MLAgentBench"}, modes=("none",), d3_k6=True))
    t1 = B.Tier1(suites={"mlab_cifar10": "MLAgentBench", "mlgym_fmnist": "MLGym"}, modes=("none",), d3_k6=True)
    gi, rep = B.build(srcs, preds, noise, t1=t1)
    n = _node(gi, "mlab_cifar10")
    assert n["tier"] == "T1" and n["suite"] == "MLAgentBench" and n["delta_n"] == 0.003
    assert [len(n[s]["instance_ids"]) for s in ("train", "dev", "test")] == [4, 2, 6]
    assert rep["t1_not_supplied"] == {"mlgym_fmnist": ["dev"]}
    with pytest.raises(B.BuilderError, match="label seeds"):
        B.build(srcs, preds, noise, t1=B.Tier1(suites=t1.suites, modes=("none",), d3_k6=False))


def test_repeat_key_equals_sft_dup_key_and_primary_dev_population(world):
    from r1.c3.train import sft_data
    r = world[0][0].rows[5]
    assert B.repeat_key(r) == sft_data.dup_key(r)
    srcs = copy.deepcopy(world[0])
    node = "openml_breast_w"
    dev_row = next(r for r in srcs[0].rows if r["node"] == node and ASSIGN[r["instance"]]["split"] == "dev")
    train_seed = int(_first(node, "train").rsplit("__s", 1)[1])
    srcs[1].rows.append(_row(node, train_seed, "none", 90, src="s1", key="shared"))
    dev_row["incumbent_hash"], dev_row["candidate_hash"] = "shared:i", "shared:c"
    pop = B.primary_dev_population(srcs)
    all_dev = {r["proposal_id"] for r in srcs[0].rows if ASSIGN[r["instance"]]["split"] == "dev"}
    assert pop == all_dev - {dev_row["proposal_id"]}
