"""Gate-input builder (preregistration §3, PRE-MEM C, PRE-DUP A, PRE-DIV A, P3): synthetic records only; no table,
label or evaluation file is opened. Expected utilities come from ``_hand_u``, which uses ``labels``/``rules``
directly and none of the builder's code."""
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
SEVEN = B.SEVEN_T0


def _row(node, seed, mode, t, kind="audit", src="s2", key=None):
    pid = f"{src}_{mode}:{node}__s{seed}:t{t:03d}"
    rng = random.Random(pid)
    return {"proposal_id": pid, "instance": f"{node}__s{seed}", "instance_seed": seed, "node": node,
            "source": f"{src}_{mode}", "memory_mode": mode, "budget_index": t, "sigma_node": SIG,
            "sigma_cmp": SIG * (1.6 if t % 2 else 1.0),
            "delta_hat": 0.0 if kind == "noop" else rng.gauss(0, SIG), "noop": kind == "noop",
            "duplicate": kind == "dup", "features": {},
            "incumbent_hash": (key or pid) + ":i", "candidate_hash": (key or pid) + ":c"}


def _label(row, k=5, seeds=B.T0_LABEL_SEEDS):
    if row["noop"]:
        return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "rule_noop",
                "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}}
    d = random.Random("L" + row["proposal_id"]).gauss(0.002, SIG)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "label_kind": "audit",
            "seeds": list(seeds), "delta_label": d, "se_label": 0.004,
            "soft_parameters": {"inert": False, "sigma_node": SIG, "k_label": k, "delta_label": d, "se_label": 0.004}}


def _evaluation(row, seeds=B.T0_EVALUATION_SEEDS):
    d = random.Random("E" + row["proposal_id"]).gauss(0.002, SIG)
    return {"proposal_id": row["proposal_id"], "node": row["node"], "seeds": list(seeds),
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
    sweep1 = B.Source("sweep1", s1)
    rng = np.random.default_rng(3)
    preds = {a: {r["proposal_id"]: rng.dirichlet(np.ones(12)).tolist() for r in s2} for a in ("A3", "A5")}
    noise = {n: {"sigma_node": SIG, "delta_n": 0.002} for n in nodes}
    return [sweep2, sweep1], preds, noise


def _hand_u(src, inst, mode, series, preds=None, g_units=0.1, exclude=()):
    """20 x mean r over one campaign, computed with labels/rules only (oracle or a supplied arm)."""
    labels = {l["proposal_id"]: l for l in src.labels}
    evals = {e["proposal_id"]: e for e in src.evaluations}
    rs = []
    for row in [r for r in src.rows if r["instance"] == inst and r["memory_mode"] == mode
                and r["proposal_id"] not in exclude]:
        if row["duplicate"]:
            rs.append(0.0)
            continue
        lab = labels[row["proposal_id"]]
        if row["noop"]:
            p = soft_label(None, None, SIG, inert=True)
        elif series == "oracle":
            if lab["label_kind"] == "divergent":
                rs.append(0.0)
                continue
            p = soft_label(lab["delta_label"], None, SIG, sigma_mode="pooled_node",
                           k_label=lab["soft_parameters"]["k_label"])
        else:
            p = np.array(preds[series][row["proposal_id"]])
        pi, mu, tau = moments(p[None], np.array([SIG]), tau_floor_z=0.15)
        g = g_units * SIG
        ex, kp = rules.decide(pi, mu, tau, np.array([row["sigma_cmp"]]), np.array([g]), np.array([row["delta_hat"]]))
        ev = evals.get(row["proposal_id"])
        if ev is not None and len(ev.get("divergent_seeds", [])) > len(ev["seeds"]) / 2:
            rs.append(float(-g * ex[0]))
            continue
        d = 0.0 if row["noop"] else ev["delta_evaluation"]
        rs.append(float(d * kp[0] - g * ex[0]))
    return 20 * float(np.mean(rs))


def _node(gi, node):
    return next(n for n in gi["nodes"] if n["node"] == node)


def _val(gi, node, split, series, inst):
    b = _node(gi, node)[split]
    return b[series][b["instance_ids"].index(inst)]


def _first(node, split):
    return sorted(i for i, v in ASSIGN.items() if v["node"] == node and v["split"] == split)[0]


def _drop(src, pids):
    src.rows = [r for r in src.rows if r["proposal_id"] not in pids]
    src.labels = [x for x in src.labels if x["proposal_id"] not in pids]
    src.evaluations = [x for x in src.evaluations if x["proposal_id"] not in pids]


@pytest.fixture(scope="module")
def world():
    return _world()


def build(w, **kw):
    kw.setdefault("t0_nodes", SEVEN)
    return B.build(*w, **kw)


def test_primary_secondary_and_sensitivity_layout(world):
    out = B.runs(*world, primary_t0=SEVEN)
    gi, rep = out["primary"]
    assert gi["schema"] == "r1_d8_gate_input/v3.1" and gi["split"] == G.SPLIT
    assert gi["t0_nodes"] == sorted(SEVEN) and len(gi["nodes"]) == 7
    assert "openml_wdbc" not in {n["node"] for n in gi["nodes"]} and rep["skipped_nodes"] == ["openml_wdbc"]
    sens = out["wdbc_sensitivity"]
    assert sens[0]["t0_nodes"] == sorted(G.T0_NODES) and len(sens[0]["nodes"]) == 8
    assert sens[1]["equals_primary"] is False
    assert rep["repeat_key_sources"]["sweep1"] > 0 and rep["repeat_key_sources"]["sweep2"] > 0
    for n in gi["nodes"]:
        assert n["suite"] is None and n["tier"] == "T0" and n["delta_n"] == 0.002
        assert [len(n[s]["instance_ids"]) for s in ("train", "dev", "test")] == [6, 3, 9]
        assert set(n["train"]) == {"instance_ids", "A2", "oracle"}
        assert set(n["test"]) == {"instance_ids", "A2", "oracle", "A3", "A5"}
        for s in ("train", "dev", "test"):
            assert all(ASSIGN[i]["split"] == s for i in n[s]["instance_ids"])
    G._validate(gi)
    eight = B.runs(*world, primary_t0=G.T0_NODES)
    assert len(eight["primary"][0]["nodes"]) == 8 and eight["wdbc_sensitivity"][1]["equals_primary"] is True
    with pytest.raises(B.BuilderError, match="primary_t0"):
        B.runs(*world, primary_t0=SEVEN[:6])


@pytest.mark.parametrize("series", ["oracle", "A3", "A5"])
@pytest.mark.parametrize("g_units", [0.1, 0.05, 0.2])
def test_utility_by_hand(world, series, g_units):
    gi, _ = build(world, g_units=g_units)
    for node, split in (("digits_mlp", "test"), ("openml_sonar", "train")):
        inst = _first(node, split)
        if series != "oracle" and split != "test":
            continue
        want = np.mean([_hand_u(world[0][0], inst, m, series, world[1], g_units) for m in MODES])
        assert _val(gi, node, split, series, inst) == pytest.approx(want, abs=1e-15)


def test_a2_uses_only_the_dev_label_block_and_delta_true_the_evaluation_block(world):
    base, _ = build(world)
    srcs, preds, noise = copy.deepcopy(world)
    for lab in srcs[0].labels:          # change every train and test label value
        if lab["label_kind"] == "audit" and ASSIGN[lab["proposal_id"].split(":")[1]]["split"] != "dev":
            lab["delta_label"] = lab["soft_parameters"]["delta_label"] = lab["delta_label"] + 0.05
    moved, _ = build((srcs, preds, noise))
    for b, m in zip(base["nodes"], moved["nodes"]):
        for s in ("train", "dev", "test"):
            assert b[s]["A2"] == m[s]["A2"]                  # A2 unchanged: fitted on dev only
        assert b["test"]["A3"] == m["test"]["A3"] and b["test"]["A5"] == m["test"]["A5"]
    assert any(b["test"]["oracle"] != m["test"]["oracle"] for b, m in zip(base["nodes"], moved["nodes"]))
    srcs, preds, noise = copy.deepcopy(world)
    for lab in srcs[0].labels:          # change dev labels: A2 moves
        if lab["label_kind"] == "audit" and ASSIGN[lab["proposal_id"].split(":")[1]]["split"] == "dev":
            lab["delta_label"] = lab["soft_parameters"]["delta_label"] = lab["delta_label"] + 0.05
    moved, _ = build((srcs, preds, noise))
    assert any(b["test"]["A2"] != m["test"]["A2"] for b, m in zip(base["nodes"], moved["nodes"]))


def test_a2_by_hand(world):
    """A2 = per node, the mean of the dev instances' non-inert soft labels with the inert bin zeroed (PRE-A2 C), then
    the rule layer and ``rules.decide``; computed here without the builder or ``arms``."""
    gi, _ = build(world)
    src = world[0][0]
    labels = {l["proposal_id"]: l for l in src.labels}
    for node, split in (("digits_mlp", "test"), ("openml_credit_approval", "train"), ("tabular_mlp", "dev")):
        dev = [soft_label(labels[r["proposal_id"]]["delta_label"], None, SIG, sigma_mode="pooled_node", k_label=5)
               for r in src.rows if r["node"] == node and ASSIGN[r["instance"]]["split"] == "dev"
               and not (r["noop"] or r["duplicate"])]
        a1 = np.mean(dev, axis=0)
        a1[0] = 0.0
        a1 = a1 / a1.sum()
        inst = _first(node, split)
        per_mode = []
        for mode in MODES:
            rs = []
            for row in [r for r in src.rows if r["instance"] == inst and r["memory_mode"] == mode]:
                if row["duplicate"]:
                    rs.append(0.0)
                    continue
                p = soft_label(None, None, SIG, inert=True) if row["noop"] else a1
                pi, mu, tau = moments(p[None], np.array([SIG]), tau_floor_z=0.15)
                ex, kp = rules.decide(pi, mu, tau, np.array([row["sigma_cmp"]]), np.array([0.1 * SIG]),
                                      np.array([row["delta_hat"]]))
                d = 0.0 if row["noop"] else next(e for e in src.evaluations
                                                 if e["proposal_id"] == row["proposal_id"])["delta_evaluation"]
                rs.append(float(d * kp[0] - 0.1 * SIG * ex[0]))
            per_mode.append(20 * np.mean(rs))
        assert _val(gi, node, split, "A2", inst) == pytest.approx(np.mean(per_mode), abs=1e-15)


def test_evaluation_values_move_realised_values_not_decisions(world):
    c = 1.0
    srcs, preds, noise = copy.deepcopy(world)
    for ev in srcs[0].evaluations:
        ev["delta_evaluation"] += c
    for mode in MODES:
        a, _ = build(world, modes=(mode,), population="full")
        b, _ = build((srcs, preds, noise), modes=(mode,), population="full")
        for na, nb in zip(a["nodes"], b["nodes"]):
            for split in ("train", "dev", "test"):
                for s in B.TEST_SERIES if split == "test" else B.TRAIN_DEV_SERIES:
                    for ua, ub in zip(na[split][s], nb[split][s]):
                        kept = (ub - ua) * 6 / (20 * c)        # 6 proposals per campaign: an integer keep count
                        assert abs(kept - round(kept)) < 1e-9 and 0 <= round(kept) <= 4


def test_pre_dup_primary_drops_test_repeats_and_falls_back(world):
    srcs, preds, noise = copy.deepcopy(world)
    node = "openml_sonar"
    test_inst, train_inst = _first(node, "test"), _first(node, "train")
    seed_tr = int(train_inst.rsplit("__s", 1)[1])
    target = [r for r in srcs[0].rows if r["instance"] == test_inst and r["memory_mode"] == "none"]
    for r in target:                    # every proposal of one mode repeats a sweep-1 train-instance key
        srcs[1].rows.append(_row(node, seed_tr, "none", 50 + r["budget_index"], src="s1", key=r["proposal_id"]))
    prim, rep = build((srcs, preds, noise), population="primary")
    full, _ = build((srcs, preds, noise), population="full")
    assert rep["nodes"][node]["repeats_dropped_test"] == len(target)
    assert rep["nodes"][node]["mode_fallbacks"]["test"] == [f"{test_inst}:none"]
    for s in ("oracle", "A3", "A5"):    # fallback: U is the other mode's U
        assert _val(prim, node, "test", s, test_inst) == pytest.approx(
            _hand_u(srcs[0], test_inst, "append_only_summary", s, preds), abs=1e-15)
        assert _val(full, node, "test", s, test_inst) == pytest.approx(
            np.mean([_hand_u(srcs[0], test_inst, m, s, preds) for m in MODES]), abs=1e-15)
    for a, b in zip(prim["nodes"], full["nodes"]):
        assert a["train"] == b["train"] and a["dev"] == b["dev"]
    for r in [r for r in srcs[0].rows if r["instance"] == test_inst and r["memory_mode"] == "append_only_summary"]:
        srcs[1].rows.append(_row(node, seed_tr, "append_only_summary", 80 + r["budget_index"], src="s1",
                                 key=r["proposal_id"]))
    prim, rep = build((srcs, preds, noise))
    assert test_inst not in _node(prim, node)["test"]["instance_ids"]
    assert rep["nodes"][node]["left_out_instances"]["test"] == [test_inst]


def test_pre_dup_keeps_and_renormalises_the_remaining_weights(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "tabular_mlp", _first("tabular_mlp", "test")
    dev_row = next(r for r in srcs[0].rows if r["instance"] == _first(node, "dev") and r["budget_index"] == 5
                   and r["memory_mode"] == "none")
    victim = next(r for r in srcs[0].rows if r["instance"] == inst and r["budget_index"] == 4
                  and r["memory_mode"] == "none")
    victim["incumbent_hash"], victim["candidate_hash"] = dev_row["incumbent_hash"], dev_row["candidate_hash"]
    prim, rep = build((srcs, preds, noise))
    assert rep["nodes"][node]["repeats_dropped_test"] == 1
    for s in ("oracle", "A3", "A5"):    # the none-mode U averages over the 5 remaining proposals
        want = np.mean([_hand_u(srcs[0], inst, "append_only_summary", s, preds),
                        _hand_u(srcs[0], inst, "none", s, preds, exclude={victim["proposal_id"]})])
        assert _val(prim, node, "test", s, inst) == pytest.approx(want, abs=1e-15)


def test_pre_div_partial_and_divergent(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "openml_climate", _first("openml_climate", "test")
    rows = [r for r in srcs[0].rows if r["instance"] == inst and not (r["noop"] or r["duplicate"])]
    ev = {e["proposal_id"]: e for e in srcs[0].evaluations}
    ev[rows[0]["proposal_id"]].update(divergent_seeds=[7006, 7009], k_evaluation=3)                  # partial
    ev[rows[1]["proposal_id"]].update(divergent_seeds=[7006, 7007, 7008], k_evaluation=2, delta_evaluation=None)
    div, rep = build((srcs, preds, noise))
    assert rep["nodes"][node]["evaluation_partial"] == 1 and rep["nodes"][node]["evaluation_divergent"] == 1
    for s in ("oracle", "A3", "A5"):
        assert _val(div, node, "test", s, inst) == pytest.approx(
            np.mean([_hand_u(srcs[0], inst, m, s, preds) for m in MODES]), abs=1e-15)
    row = rows[1]                       # the divergent row's executions, counted per series, by hand
    lab = {l["proposal_id"]: l for l in srcs[0].labels}[row["proposal_id"]]
    beliefs = {"oracle": soft_label(lab["delta_label"], None, SIG, sigma_mode="pooled_node", k_label=5),
               "A3": np.array(preds["A3"][row["proposal_id"]]), "A5": np.array(preds["A5"][row["proposal_id"]])}
    for s, p in beliefs.items():
        pi, mu, tau = moments(p[None], np.array([SIG]), tau_floor_z=0.15)
        ex, _ = rules.decide(pi, mu, tau, np.array([row["sigma_cmp"]]), np.array([0.1 * SIG]),
                             np.array([row["delta_hat"]]))
        assert rep["nodes"][node]["divergent_executed"][s] == int(ex[0])
    for bad, match in (({"delta_evaluation": 0.1}, "divergent proposal carries"),
                       ({"k_evaluation": 3}, "k_evaluation does not match")):
        b = copy.deepcopy(srcs)
        {e["proposal_id"]: e for e in b[0].evaluations}[row["proposal_id"]].update(bad)
        with pytest.raises(B.BuilderError, match=match):
            build((b, preds, noise))
    b = copy.deepcopy(srcs)
    {e["proposal_id"]: e for e in b[0].evaluations}[row["proposal_id"]].pop("k_evaluation")
    with pytest.raises(B.BuilderError, match="come together"):
        build((b, preds, noise))


def test_partial_and_divergent_labels(world):
    srcs, preds, noise = copy.deepcopy(world)
    node, inst = "openml_ionosphere", _first("openml_ionosphere", "test")
    rows = [r for r in srcs[0].rows if r["instance"] == inst and not (r["noop"] or r["duplicate"])]
    labs = {l["proposal_id"]: l for l in srcs[0].labels}
    labs[rows[0]["proposal_id"]].update(label_kind="divergent", delta_label=None, soft_parameters={"inert": False})
    labs[rows[1]["proposal_id"]]["soft_parameters"]["k_label"] = 3             # partial: s = sigma / sqrt(3)
    gi, rep = build((srcs, preds, noise))
    assert rep["nodes"][node]["label_divergent"] == 1 and rep["nodes"][node]["label_partial"] == 1
    assert _val(gi, node, "test", "oracle", inst) == pytest.approx(
        np.mean([_hand_u(srcs[0], inst, m, "oracle", preds) for m in MODES]), abs=1e-15)
    labs[rows[1]["proposal_id"]]["soft_parameters"]["k_label"] = 2             # 3 of 5 diverged: not a label
    with pytest.raises(B.BuilderError, match="k_label"):
        build((srcs, preds, noise))


def test_input_order_does_not_change_the_output(world):
    a = json.dumps(build(world), sort_keys=True)
    srcs, preds, noise = copy.deepcopy(world)
    for s in srcs:
        random.Random(1).shuffle(s.rows)
        random.Random(2).shuffle(s.labels)
        random.Random(3).shuffle(s.evaluations)
    assert json.dumps(build((srcs[::-1], preds, noise)), sort_keys=True) == a


@pytest.mark.parametrize("mutate,match", [
    (lambda s, p: s[0].rows.append(_row("digits_mlp", 9011, "none", 2)), "not in the P3 split file"),
    (lambda s, p: s[0].labels[1].__setitem__("seeds", [7001, 7002, 7003, 7004, 7006]), "label seeds"),
    (lambda s, p: s[0].evaluations[0].__setitem__("seeds", [7001, 7002, 7003, 7004, 7005]), "seeds differ"),
    (lambda s, p: p["A5"].pop(s[0].evaluations[0]["proposal_id"]), "A5: no prediction"),
    (lambda s, p: p["A3"].__setitem__(s[0].evaluations[0]["proposal_id"], [0.5] * 12), "12-bin distributions"),
    (lambda s, p: s[0].labels.append({**s[0].labels[1], "proposal_id": next(
        r["proposal_id"] for r in s[0].rows if r["duplicate"])}), "within-campaign duplicate"),
    (lambda s, p: s[0].rows.append(dict(s[0].rows[0])), "duplicate proposal id"),
    (lambda s, p: s[0].rows[0].__setitem__("instance", "digits_mlp__s999"), "is not"),
    (lambda s, p: s[1].labels.append(s[0].labels[0]), "repeat-key source"),
    # B1: a complete population; a missing label or evaluation row is refused, never dropped
    (lambda s, p: s[0].evaluations.pop(0), "without its evaluation row"),
    (lambda s, p: s[0].labels.remove(next(l for l in s[0].labels if l["label_kind"] == "audit")),
     "without its label row"),
    (lambda s, p: s[0].labels.append({**s[0].labels[1], "proposal_id": "sweep2:none:digits_mlp__s104:t099"}),
     "outside the table"),
    (lambda s, p: s[0].labels[1].__setitem__("audit_reason", "di_changed"), "audit_reason"),
    (lambda s, p: next(l for l in s[0].labels if l["label_kind"] == "audit")["soft_parameters"].__setitem__(
        "sigma_node", 0.02), "sigma_node differs"),
    (lambda s, p: s[0].evaluations.append({**s[0].evaluations[0], "proposal_id": next(
        r["proposal_id"] for r in s[0].rows if r["noop"])}), "no-op carries an evaluation row"),
    (lambda s, p: (s[0].rows.append(_row("digits_mlp", 104, "full_history", 9, "noop")),
                   s[0].labels.append(_label(s[0].rows[-1]))), "undeclared memory modes"),
    (lambda s, p: s.__setitem__(1, B.Source("sweep3", s[1].rows)), "distinct members"),
    (lambda s, p: s.pop(1), "sweep1 repeat-key source"),
    (lambda s, p: s[0].rows.append(_row("mlab_cifar10", 5101, "none", 2, "noop")), "not a T0 node"),
])
def test_refusals(world, mutate, match):
    srcs, preds, noise = copy.deepcopy(world)
    mutate(srcs, preds)
    with pytest.raises(B.BuilderError, match=match):
        build((srcs, preds, noise))


def test_missing_test_block_is_refused_not_zeroed(world):
    """B1: removing a node's test label and evaluation rows must be an input refusal, not a zero series."""
    srcs, preds, noise = copy.deepcopy(world)
    test_pids = {r["proposal_id"] for r in srcs[0].rows if r["node"] == "digits_mlp"
                 and ASSIGN[r["instance"]]["split"] == "test" and not (r["noop"] or r["duplicate"])}
    srcs[0].labels = [x for x in srcs[0].labels if x["proposal_id"] not in test_pids]
    srcs[0].evaluations = [x for x in srcs[0].evaluations if x["proposal_id"] not in test_pids]
    with pytest.raises(B.BuilderError, match="complete population"):
        build((srcs, preds, noise))


def test_t0_node_set_noise_mode_and_a2_refusals(world):
    srcs, preds, noise = world
    with pytest.raises(B.BuilderError, match="t0_nodes"):
        build(world, t0_nodes=["mlab_cifar10"])
    with pytest.raises(TypeError):
        B.build(srcs, preds, noise)                                   # t0_nodes is required
    with pytest.raises(B.BuilderError, match="δ_n"):
        build((srcs, preds, {k: v for k, v in noise.items() if k != "digits_mlp"}))
    with pytest.raises(B.BuilderError, match="sigma_node differs"):
        build((srcs, preds, {**noise, "digits_mlp": {"sigma_node": 0.02, "delta_n": 0.002}}))
    few = copy.deepcopy(world)                                        # a T0 node without dev rows
    _drop(few[0][0], {r["proposal_id"] for r in few[0][0].rows
                      if r["node"] == "openml_sonar" and ASSIGN[r["instance"]]["split"] == "dev"})
    with pytest.raises(B.BuilderError, match="openml_sonar"):
        build(few)
    nomode = copy.deepcopy(world)                                     # a train campaign without rows
    inst = _first("openml_breast_w", "train")
    _drop(nomode[0][0], {r["proposal_id"] for r in nomode[0][0].rows
                         if r["instance"] == inst and r["memory_mode"] == "none"})
    with pytest.raises(B.BuilderError, match="fallback applies only"):
        build(nomode)
    noa2 = copy.deepcopy(world)                                       # dev of one node: only inert proposals
    _drop(noa2[0][0], {r["proposal_id"] for r in noa2[0][0].rows if r["node"] == "openml_climate"
                       and ASSIGN[r["instance"]]["split"] == "dev" and not (r["noop"] or r["duplicate"])})
    with pytest.raises(B.BuilderError, match="no A1 constant"):
        build(noa2)


def test_t1_nodes_suites_modes_and_k6_seeds(world):
    srcs, preds, noise = copy.deepcopy(world)
    rows, labels, evals = [], [], []
    for node in ("mlab_cifar10", "mlgym_fmnist"):
        for inst, v in ASSIGN.items():
            if v["node"] != node or (node == "mlgym_fmnist" and v["split"] == "dev"):
                continue
            seed = int(inst.rsplit("__s", 1)[1])
            rows += [_row(node, seed, "none", t, src="g5") for t in range(2, 6)]
    for r in rows:
        labels.append(_label(r, k=3, seeds=B.D3_LABEL_SEEDS))
        evals.append(_evaluation(r, seeds=B.D3_EVALUATION_SEEDS))
        for a in ("A3", "A5"):
            preds[a][r["proposal_id"]] = [1 / 12] * 12
    srcs.append(B.Source("g5", rows, labels, evals))
    noise.update({n: {"sigma_node": SIG, "delta_n": 0.003} for n in ("mlab_cifar10", "mlgym_fmnist")})
    with pytest.raises(B.BuilderError, match="frozen T1 setting"):
        build((srcs, preds, noise))
    with pytest.raises(B.BuilderError, match="frozen suite"):
        build((srcs, preds, noise), t1=B.Tier1(suites={"mlab_cifar10": "MLAgentBench"}, modes=("none",), d3_k6=True))
    suites = {"mlab_cifar10": "MLAgentBench", "mlgym_fmnist": "MLGym", "autoresearch_fixedtokens": "autoresearch"}
    t1 = B.Tier1(suites=suites, modes=("none",), d3_k6=True)
    gi, rep = build((srcs, preds, noise), t1=t1)
    n = _node(gi, "mlab_cifar10")
    assert n["tier"] == "T1" and n["suite"] == "MLAgentBench" and n["delta_n"] == 0.003
    assert [len(n[s]["instance_ids"]) for s in ("train", "dev", "test")] == [4, 2, 6]
    assert rep["t1_not_supplied"] == {"mlgym_fmnist": ["dev"], "autoresearch_fixedtokens": ["no rows"]}
    with pytest.raises(B.BuilderError, match="label seeds"):
        build((srcs, preds, noise), t1=B.Tier1(suites=suites, modes=("none",), d3_k6=False))


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
    with pytest.raises(B.BuilderError, match="sweep1 repeat-key source"):
        B.primary_dev_population(srcs[:1])
    bad = copy.deepcopy(srcs)
    bad[1].rows.append(_row("mlab_cifar10", 5101, "none", 2, src="s1"))
    with pytest.raises(B.BuilderError, match="not a T0 node"):
        B.primary_dev_population(bad)
