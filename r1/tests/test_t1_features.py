"""ARMS-T1FEAT A: T1 features for the G.5 table (sweep2/t1_tasl/g5_features.py), their wiring into the assembly
(g5_assemble.py), the T1 noise input of the gate run (g5_noise.py) and the suite-name mapping. Synthetic only: fake
ledgers, fake G.1b runs and the synthetic G.5 world of test_t1_g5_seal; no sealed data, no real label or value."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random

import pytest

from r1.tests.test_t1_g5_seal import (A, G, NODE, SIGMA, Engine, assemble_world, lock_for, node_git,  # noqa: F401
                                      world)
import g5_features as F  # noqa: E402  (sweep2/t1_tasl is on sys.path through test_t1_g5_seal)
import g5_noise as N  # noqa: E402

from r1.c3 import features as T0F
from r1.c3 import gate
from r1.c3 import gate_input_builder as B

LS = "trackg_v2_diff_campaign_ledger/v1"
NAN_FIELDS = set(F.NO_T1_SOURCE) - set(F.CAT_FEATURES_V3)


def same(a: dict, b: dict) -> bool:
    return list(a) == list(b) and all((isinstance(x, float) and isinstance(y, float) and math.isnan(x)
                                       and math.isnan(y)) or x == y for x, y in zip(a.values(), b.values()))


# =============================================================================================== T0 unchanged
# sha256 over json.dumps(features) + "\n" of the eight proposals below, computed on the base commit 30e2d51a
# (mac-g5-code-main-20261123) before this unit; r1/c3/features.py is not changed by it.
T0_GOLDEN = "ffe94da07cbfb00f79f03baa5104b108269f8ac1fa1af5b23d753ca8ae9c97a1"
T0_CODES = {"digits_mlp": 0, "openml_breast_w": 1, "openml_ionosphere": 2, "tabular_mlp": 3,
            "openml_credit_approval": 4, "openml_wdbc": 5, "openml_credit_g": 6, "openml_sonar": 7,
            "openml_blood_transfusion": 8, "openml_qsar_biodeg": 9, "openml_climate": 10}


def t0_proposals():
    from r1.tests.test_c3_features import START, YAML, ledger, row
    props, _ = T0F.replay_campaign(ledger(), START, "digits_mlp", "digits_mlp__s104", "t", "none", 20, 0.0075)
    led = [row(1, "C", "0.15", "0.3", "kept", 0.99, None, "config.yaml"),
           row(2, "max_depth", "5", "7", "discarded", 0.99, 0.99, "config.yaml"),
           row(3, "model_type", "logistic_regression", "random_forest", "discarded", 0.98, 0.99, "config.yaml"),
           row(4, "C", "0.3", "0.6", "kept", 0.995, 0.99, "config.yaml")]
    p2, _ = T0F.replay_campaign(led, YAML, "openml_breast_w", "openml_breast_w__s105", "t", "append_only_summary",
                                20, 0.0039)
    return props + p2


def test_t0_features_byte_identical_and_t0_tables_untouched():
    props = t0_proposals()
    blob = "".join(json.dumps(p.features) + "\n" for p in props).encode()
    assert len(props) == 8 and hashlib.sha256(blob).hexdigest() == T0_GOLDEN
    assert T0F.FEATURIZER_VERSION == "c3_features/v3"                  # the T0 version string is not bumped
    assert T0F.NODE_CODES == T0_CODES and set(T0F.NODE_INFO) == set(T0_CODES)   # importing g5_features adds nothing
    with pytest.raises(ValueError, match="unknown node"):              # the T0 replay still refuses a T1 node
        T0F.NodeContext(node="mlab_cifar10", start_files={}, sigma_node=0.01, runs_total=20, memory_mode="none")


def test_schema_is_featurizer_v3_and_codes_are_appended():
    assert F.FEATURES_V3 == T0F.FEATURES and F.CAT_FEATURES_V3 == T0F.CAT_FEATURES
    assert F.NUM_FEATURES_V3 == T0F.NUM_FEATURES
    assert set(F.NO_T1_SOURCE) <= set(F.FEATURES_V3) and set(F.RAW_STATE_FIELDS) <= set(F.FEATURES_V3)
    assert not set(F.T1_NODE_CODES.values()) & set(T0F.NODE_CODES.values())
    assert min(F.T1_NODE_CODES.values()) == max(T0F.NODE_CODES.values()) + 1 == F.FIRST_T1_CODE
    assert sorted(F.T1_NODE_CODES.values()) == list(range(11, 19))
    assert {F.tier_of_code(c) for c in T0F.NODE_CODES.values()} == {"T0"}
    assert {F.tier_of_code(c) for c in F.T1_NODE_CODES.values()} == {"T1"}


def test_t1_nodes_are_the_g5_spec_nodes_and_the_split_files_t1_nodes():
    spec = json.loads((A.HERE / "g5_tasl_spec.json").read_text())
    assert [n["node"] for n in spec["nodes"]] == list(F.T1_NODE_INFO)
    split = json.loads((A.HERE.parents[1] / spec["instances"]["split_file"]["path"]).read_text())
    assert sorted(split["t1"]["nodes"]) == sorted(F.T1_NODE_INFO)
    assert not set(F.T1_NODE_INFO) & set(gate.T0_NODES)


# =============================================================================================== suite mapping
def test_suite_mapping_to_gate_suites():
    assert set(F.SUITE_NAMES.values()) == set(gate.SUITES)
    assert set(F.SUITE_NAMES) == {v["suite"] for v in F.T1_NODE_INFO.values()}
    assert F.gate_suite("mlagentbench") == "MLAgentBench" and F.gate_suite("mlgym") == "MLGym"
    assert F.gate_suite("autoresearch") == "autoresearch"
    with pytest.raises(F.FeatureError, match="no gate suite"):
        F.gate_suite("MLAgentBench")                     # gate names are not node-spec names
    got = F.tier1_suites({n: v["suite"] for n, v in F.T1_NODE_INFO.items()})
    assert got == {"mlab_cifar10": "MLAgentBench", "mlab_imdb": "MLAgentBench", "mlab_ogbn_arxiv": "MLAgentBench",
                   "mlgym_cifar10": "MLGym", "mlgym_fmnist": "MLGym", "mlgym_breakout_minatar": "MLGym",
                   "mlgym_houseprice": "MLGym", "autoresearch_fixedtokens": "autoresearch"}
    with pytest.raises(F.FeatureError, match="declares"):
        F.tier1_suites({"mlab_imdb": "mlgym"})
    with pytest.raises(F.FeatureError, match="not a declared T1 node"):
        F.tier1_suites({"openml_wdbc": "mlgym"})
    B.Tier1(suites=got, modes=("history",))             # the frozen builder's Tier1 takes the mapped names


# =============================================================================================== T1 features
def run(state, raw, *, executed=True, diff=True):
    r = {"executed": executed}
    if diff:
        r["diff"] = {"code_state_sha256": state, "code_state_raw_sha256": raw}
    if executed:
        r.update(code_state_sha256=state, code_state_raw_sha256=raw)
    return r


def t1_ledger(direction="maximize"):
    """Steps as the v2-diff engine writes them, with the diff provenance of apply_diff in every run record."""
    up = 1.0 if direction == "maximize" else -1.0
    v = lambda d: round(0.40 + up * d, 6)                                 # noqa: E731
    e = [{"schema": LS, "step": 0, "decision": "baseline", "runs": [run("B", "Br", diff=False)],
          "final_outcome": {"kind": "ok", "value": v(0)}, "best_after": v(0)}]
    steps = [("kept", run("C1", "C1r"), v(0.10), v(0.10)),
             ("discarded", run("C2", "C2r"), v(0.05), v(0.10)),
             ("not_run_inert", run("C1", "C1r_ws", executed=False), None, v(0.10)),    # whitespace-only change
             ("invalid_proposal", None, None, v(0.10)),
             ("not_run_duplicate", run("C2", "C2r", executed=False), None, v(0.10)),
             ("discarded_divergent", run("C3", "C3r"), None, v(0.10)),
             ("not_run_refused", {"executed": False, "diff": {"code_state_sha256": None}}, None, v(0.10)),
             ("kept", run("C4", "C4r"), v(0.15), v(0.15)),
             ("not_run_inert", run("C4", "C4r", executed=False), None, v(0.15)),       # empty diff
             ("infrastructure_failure_final", run("C5", "C5r"), None, v(0.15)),
             ("discarded", run("C5", "C5r"), v(0.12), v(0.15))]                     # infra-final: not registered
    for i, (dec, r, val, best) in enumerate(steps, start=1):
        x = {"schema": LS, "step": i, "decision": dec, "manager_call": {"usage": {}}, "runs": [r] if r else [],
             "best_after": best}
        if val is not None:
            x["final_outcome"] = {"kind": "ok", "value": val}
        if r is not None and dec != "invalid_proposal":
            x["proposal"] = {"diff": f"--- a/train.py\n+++ b/train.py\n@@ step {i}"}
        e.append(x)
    return e


def featurize(entries, *, direction="maximize", w=20, mode="history", node="mlab_imdb", suite="mlagentbench"):
    return F.featurize_ledger(entries, node=node, spec_suite=suite, sign=1.0 if direction == "maximize" else -1.0,
                              sigma_node=0.05, budget_w=w, w_semantics="manager_calls", memory_mode=mode)


def test_t1_fields_from_the_ledger():
    feats, info = featurize(t1_ledger())
    assert sorted(feats) == [1, 2, 3, 5, 6, 8, 9, 10, 11]                  # steps with a candidate code state
    assert info == {"raw_state_missing": 0}
    for f in feats.values():
        assert list(f) == list(F.FEATURES_V3) and f["node_code"] == 12
        assert all(f[k] == -1 for k in ("key_code", "model_type_code", "new_cat_code"))
        assert all(math.isnan(f[k]) for k in NAN_FIELDS) and f["memory_on"] == 1.0
    s1, s2, s3, s5, s6, s8, s9, s11 = (feats[i] for i in (1, 2, 3, 5, 6, 8, 9, 11))
    assert (s1["budget_index"], s1["budget_frac_left"], s1["keeps_so_far"], s1["trials_since_keep"]) == (1.0, 1.0, 0, 1)
    assert s1["recorded_gain_z"] == 0.0 and s1["active_seen_before"] == 0.0 and s1["active_equals_incumbent"] == 0.0
    assert s2["keeps_so_far"] == 1.0 and s2["trials_since_keep"] == 1.0 and s2["budget_frac_left"] == 1 - 1 / 20
    assert s2["recorded_gain_z"] == pytest.approx(0.10 / 0.05)
    # inert, whitespace only: normalised state = incumbent's, raw differs (T0's inactive-key edit has the same shape)
    assert (s3["active_equals_incumbent"], s3["cfg_equals_incumbent"], s3["active_seen_before"]) == (1.0, 0.0, 1.0)
    assert s3["full_seen_before"] == 0.0
    # duplicate of step 2's evaluated state: seen, not equal to the incumbent; the invalid reply of step 4 counted
    assert (s5["active_equals_incumbent"], s5["active_seen_before"], s5["full_seen_before"]) == (0.0, 1.0, 1.0)
    assert s5["invalid_so_far"] == 1.0 and s5["budget_frac_left"] == pytest.approx(1 - 4 / 20)
    assert s6["invalid_so_far"] == 1.0 and s6["active_seen_before"] == 0.0
    assert s8["invalid_so_far"] == 3.0                         # + the divergent run (no metric) and the refused diff
    assert s8["trials_since_keep"] == 7.0 and s8["keeps_so_far"] == 1.0
    assert (s9["active_equals_incumbent"], s9["cfg_equals_incumbent"]) == (1.0, 1.0)  # empty diff: raw equal too
    assert s9["keeps_so_far"] == 2.0 and s9["trials_since_keep"] == 1.0
    assert s9["recorded_gain_z"] == pytest.approx(0.15 / 0.05)
    assert s11["active_seen_before"] == 0.0 and s11["invalid_so_far"] == 4.0   # infra-final: counted, not registered
    assert feats[10]["active_seen_before"] == 0.0


def test_t1_minimised_metric_and_memory_none():
    up, _ = featurize(t1_ledger(), direction="maximize")
    down, _ = featurize(t1_ledger("minimize"), direction="minimize", mode="none")
    for step in up:
        assert down[step]["recorded_gain_z"] == pytest.approx(up[step]["recorded_gain_z"])
        assert down[step]["memory_on"] == 0.0
    assert down[9]["recorded_gain_z"] > 0                      # an improvement is positive in both directions


def test_t1_features_do_not_read_the_own_or_later_outcomes():
    base, _ = featurize(t1_ledger())
    for n in range(1, 12):
        led = t1_ledger()
        for e in led[n:]:                                      # step n's own outcome side and every later line
            if e["step"] == n:                                 # its decision, within what its run record allows
                e["decision"] = "discarded" if F.proposal_side(e) else "not_run_refused"
            else:
                e["decision"] = random.Random(e["step"]).choice(["kept", "discarded", "invalid_proposal",
                                                                 "discarded_divergent"])
                e["runs"] = [run("Z%d" % e["step"], "Zr%d" % e["step"])]
            e["best_after"] = 9.0 + e["step"]
            e["final_outcome"] = {"kind": "ok", "value": -3.0}
        alt, _ = featurize(led)
        for step in base:
            if step <= n and step in alt:
                assert same(base[step], alt[step]), (n, step)


def test_t1_raw_state_missing_gives_nan_and_is_counted():
    led = t1_ledger()
    for e in led:
        for r in e["runs"]:
            r.pop("code_state_raw_sha256", None)
            (r.get("diff") or {}).pop("code_state_raw_sha256", None)
    feats, info = featurize(led)
    assert info["raw_state_missing"] == len(feats)
    assert all(math.isnan(f["cfg_equals_incumbent"]) and math.isnan(f["full_seen_before"]) for f in feats.values())
    assert feats[5]["active_seen_before"] == 1.0               # the normalised fields do not need raw states


def test_t1_featurizer_refusals():
    led = t1_ledger()
    with pytest.raises(F.FeatureError, match="not a declared T1 node"):
        featurize(led, node="digits_mlp")
    with pytest.raises(F.FeatureError, match="declares"):
        featurize(led, suite="mlgym")
    with pytest.raises(F.FeatureError, match="manager calls"):
        F.featurize_ledger(led, node="mlab_imdb", spec_suite="mlagentbench", sign=1.0, sigma_node=0.05, budget_w=20,
                           w_semantics="worker_runs", memory_mode="history")
    with pytest.raises(F.FeatureError, match="sigma_node positive"):
        F.featurize_ledger(led, node="mlab_imdb", spec_suite="mlagentbench", sign=1.0, sigma_node=0.0, budget_w=20,
                           w_semantics="manager_calls", memory_mode="history")
    with pytest.raises(F.FeatureError, match="more than W"):
        featurize(led, w=5)
    gap = t1_ledger()
    del gap[3]
    with pytest.raises(F.FeatureError, match="follows step"):
        featurize(gap)
    with pytest.raises(F.FeatureError, match="baseline"):
        featurize(t1_ledger()[1:])


def test_one_model_over_both_tiers():
    """A T0 row and T1 rows go through the arms' feature matrix together; with LightGBM present, A3 fits on them
    (the -1 categorical values are LightGBM's missing values)."""
    from r1.c3.arms import LGBMPrior, feature_matrix
    t0 = [{"node": p.node, "features": p.features} for p in t0_proposals()]
    t1 = [{"node": "mlab_imdb", "features": f} for f in featurize(t1_ledger())[0].values()]
    X, cols = feature_matrix(t0 + t1)
    assert X.shape == (len(t0) + len(t1), len(F.FEATURES_V3)) and cols == list(F.FEATURES_V3)
    pytest.importorskip("lightgbm")
    rows = []
    for i, r in enumerate((t0 + t1) * 4):
        soft = [0.0] * 12
        soft[1 + (i % 11)] = 1.0
        rows.append({**r, "noop": False, "soft": soft, "weight": 1.0})
    P = LGBMPrior(rounds=5).fit(rows).predict(rows)
    assert P.shape == (len(rows), 12)


# =============================================================================================== the assembly
def test_assembly_rows_carry_features_and_re_derive_byte_identically(world):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6"}, divergent_eval={"S13_7"}))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    raw = (table / "proposals.jsonl").read_bytes()
    rows = [json.loads(x) for x in raw.decode().splitlines()]
    assert rows and all(list(r["features"]) == sorted(F.FEATURES_V3) for r in rows)   # sorted keys in the table
    by = {r["proposal_id"]: r for r in rows}
    first = by[f"g5.history:{NODE}__s5101:t001"]["features"]
    assert first["node_code"] == 12 and first["budget_index"] == 1.0 and first["budget_frac_left"] == 1.0
    assert first["keeps_so_far"] == 0.0 and first["memory_on"] == 1.0 and first["recorded_gain_z"] == 0.0
    assert math.isnan(first["cfg_equals_incumbent"])           # the fixture's records carry no raw code states
    noop = by[f"g5.history:{NODE}__s5101:t008"]["features"]
    assert noop["active_equals_incumbent"] == 1.0 and noop["recorded_gain_z"] == pytest.approx(0.10 / SIGMA)
    build = json.loads((table / "build.json").read_text())
    assert build["featurizer"] == json.loads(json.dumps(F.describe()))
    assert build["nodes"][NODE]["gate_suite"] == "MLAgentBench" and build["nodes"][NODE]["suite"] == "mlagentbench"
    feat = build["nodes"][NODE]["features"]
    # the fixture's duplicate (step 5) repeats the incumbent's state C1: the code-state check counts it
    assert feat["raw_state_missing"] == len(rows) and feat["flag_mismatch"] == 12
    assert F.tier1_suites({n: v["suite"] for n, v in build["nodes"].items()}) == {NODE: "MLAgentBench"}
    # the test stage re-derives the table, features included, byte-identically; a changed feature is refused
    bad = raw.replace(b'"budget_index": 1.0', b'"budget_index": 2.0', 1)
    assert bad != raw
    (table / "proposals.jsonl").write_bytes(bad)
    with pytest.raises(G.Stop, match="proposals.jsonl is not the one"):
        A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    (table / "proposals.jsonl").write_bytes(raw)
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert (table / "proposals.jsonl").read_bytes() == raw


def test_assembly_refuses_a_node_spec_suite_other_than_declared(world, monkeypatch):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s))
    monkeypatch.setitem(F.T1_NODE_INFO, NODE, {"suite": "mlgym", "code": 12})    # the node spec says mlagentbench
    with pytest.raises(G.Stop, match="T1 features cannot be computed.*declares"):
        A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    assert not table.exists()


# =============================================================================================== T1 noise
def g1b_run(root, node, *, n_edits=3, seeds=6, short_edit=None):
    """A synthetic assembled G.1b run directory (runs.jsonl, edits.json, ASSEMBLY.json) for one node, and the
    verdict fields its summary would carry."""
    d = root / "g1b_run"
    d.mkdir(parents=True)
    rows = []
    for c in ["c0"] + [f"c{k}" for k in range(1, n_edits + 1)]:
        for s in range(seeds if c != short_edit else 2):
            m = 0.8 + 0.01 * int(c[1:]) + random.Random(f"{c}:{s}").gauss(0, 0.003 * (1 + int(c[1:])))
            rows.append({"node": node, "config": c, "condition": "joint", "train_seed": 100 + s, "split_seed": 200 + s,
                         "success": True, "metric": m, "wall_seconds": 1.0})
        rows.append({"node": node, "config": c, "condition": "default", "train_seed": None, "split_seed": None,
                     "success": True, "metric": 0.8, "wall_seconds": 1.0})
    rows.append({"node": node, "config": "c1", "condition": "joint", "train_seed": 999, "split_seed": 999,
                 "success": False, "metric": None, "wall_seconds": 1.0})      # a failed run: not paired
    rows.append({"node": "other_node", "config": "c1", "condition": "joint", "train_seed": 100, "split_seed": 200,
                 "success": True, "metric": 5.0, "wall_seconds": 1.0})       # another node: ignored
    (d / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "edits.json").write_text(json.dumps({node: [{"symbol": f"k{k}", "old": "a", "new": "b"}
                                                     for k in range(1, n_edits + 1)]}))
    (d / "ASSEMBLY.json").write_text(json.dumps({"schema": G.ASSEMBLY_SCHEMA, "run_id": "g1b-tasl-20261121-b",
                                                 "runs_sha256": G.L._sha_file(d / "runs.jsonl")}))
    counts = [2 if short_edit == f"c{k}" else seeds for k in range(1, n_edits + 1)]
    return d, {"n_edits": n_edits, "paired_joint_n": counts, "assembly_sha256": G.L._sha_file(d / "ASSEMBLY.json")}


def bind_summary(world, run_dir, verdict_extra):
    """Rewrite the world's REL-T1-G1B copy with the run's assembly sha256 and the verdict fields, and rebind the spec
    (before the run, as sign_note does)."""
    s, repo, rel = world["spec"], world["repo"], world["rel"]
    summary = {"schema": G.SUMMARY_SCHEMA, "label": G.ENGINEERING_ONLY, "run_id": "g1b-tasl-20261121-b",
               "assembly_sha256": verdict_extra["assembly_sha256"],
               "verdicts": {NODE: {"qualifies_D21": True, "sigma_joint": SIGMA, "n_edits": verdict_extra["n_edits"],
                                   "paired_joint_n": verdict_extra["paired_joint_n"]}}}
    (repo / rel).write_text(json.dumps(summary))
    s["noise_floor"]["seven"].update(sha256=G.L._sha_file(repo / rel))
    world["sp"].write_text(json.dumps(s))
    rec = json.loads(world["srv"].read_text())
    world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    return lock_for(world, "traindev")("traindev")


def test_noise_d18_matches_e1_report_and_is_bound_to_the_copy(world):
    from r1.noise import e1_report
    d, extra = g1b_run(world["tmp"], NODE, n_edits=4, short_edit="c3")
    row = bind_summary(world, d, extra)
    rec = N.derive(world["spec"], row, {NODE: d})
    n = rec["nodes"][NODE]
    pinned = e1_report.summarise(d)["nodes"][NODE]["summary"]["median_sd_joint"]
    assert n["median_paired_sd"] == pinned and n["delta_n"] == max(0.002, 0.25 * pinned)
    assert n["sigma_node"] == SIGMA and n["n_edits"] == 4 and n["n_edits_with_sd"] == 3
    assert n["summary"] == world["rel"] and n["summary_sha256"] == G.L._sha_file(world["repo"] / world["rel"])
    assert n["runs_sha256"] == G.L._sha_file(d / "runs.jsonl") and n["assembly_sha256"] == extra["assembly_sha256"]
    noise = N.builder_noise(rec)
    assert noise == {NODE: {"delta_n": n["delta_n"], "sigma_node": SIGMA}}
    sha = N.write_record(rec, "docs/r1/reports/t1_noise_x/T1_NOISE.json", repo=world["repo"])
    raw = (world["repo"] / "docs/r1/reports/t1_noise_x/T1_NOISE.json").read_bytes()
    assert N.builder_noise({}, sha256=sha, raw=raw) == noise
    with pytest.raises(G.Stop, match="differs from the sha256"):
        N.builder_noise({}, sha256="0" * 64, raw=raw)
    with pytest.raises(FileExistsError):
        N.write_record(rec, "docs/r1/reports/t1_noise_x/T1_NOISE.json", repo=world["repo"])
    # small floors take the D18 floor
    tiny = copy.deepcopy(rec)
    tiny["nodes"][NODE]["delta_n"] = max(N.D18_FLOOR, 0.25 * 1e-6)
    assert N.builder_noise(tiny)[NODE]["delta_n"] == 0.002


def test_noise_refusals(world):
    d, extra = g1b_run(world["tmp"], NODE)
    row = bind_summary(world, d, extra)
    with pytest.raises(G.Stop, match="run directories are given"):
        N.derive(world["spec"], row, {NODE: d, "mlab_cifar10": d})
    good = (d / "runs.jsonl").read_bytes()
    (d / "runs.jsonl").write_bytes(good + b"\n")                 # not the run the copy binds
    with pytest.raises(G.Stop, match="not the run of the summary copy"):
        N.derive(world["spec"], row, {NODE: d})
    (d / "runs.jsonl").write_bytes(good)
    bad = dict(extra, paired_joint_n=[6, 6, 5])
    row = bind_summary(world, d, bad)
    with pytest.raises(G.Stop, match="paired-seed counts"):
        N.derive(world["spec"], row, {NODE: d})
    row = bind_summary(world, d, dict(extra, n_edits=None))
    with pytest.raises(G.Stop, match="n_edits"):
        N.derive(world["spec"], row, {NODE: d})
    with pytest.raises(G.Stop, match="T0 and a T1"):
        N.merge_noise({NODE: {"delta_n": 0.002, "sigma_node": 0.01}}, {NODE: {"delta_n": 0.003, "sigma_node": 0.01}})


def test_t0_plus_t1_gate_input_with_the_frozen_builder(world):
    """The assembled T1 table (features filled), the T1 noise record and the mapped suites go into the frozen
    builder beside a synthetic T0 world; the T1 node comes out with its gate suite and the derived δ_n."""
    from r1.tests import test_gate_input_builder as TB
    s = world["spec"]
    d, extra = g1b_run(world["tmp"], NODE)
    row = bind_summary(world, d, extra)
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6"}, divergent_eval={"S13_7"}))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()]
    evals = [json.loads(x) for x in (ev / "evaluation_block.jsonl").read_text().splitlines()]
    build = json.loads((table / "build.json").read_text())
    t1_noise = N.builder_noise(N.derive(s, row, {NODE: d}))
    assert t1_noise[NODE]["sigma_node"] == build["nodes"][NODE]["sigma_node"] == rows[0]["sigma_node"]
    (sweep2, sweep1), preds, t0_noise = TB._world()
    for r in rows:
        if not r["noop"]:
            for a in ("A3", "A5"):
                preds[a][r["proposal_id"]] = [1 / 12] * 12
    t1 = B.Tier1(suites=F.tier1_suites({n: v["suite"] for n, v in build["nodes"].items()}), modes=("history",))
    gi, rep = B.build([sweep2, sweep1, B.Source("g5", rows, labels, evals)], preds,
                      N.merge_noise(t0_noise, t1_noise), t0_nodes=B.SEVEN_T0, t1=t1)
    node = next(n for n in gi["nodes"] if n["node"] == NODE)
    assert node["tier"] == "T1" and node["suite"] == "MLAgentBench" and node["delta_n"] == t1_noise[NODE]["delta_n"]
    assert {n["node"] for n in gi["nodes"] if n["tier"] == "T0"} == set(B.SEVEN_T0)
    assert rep["t1_not_supplied"] == {}
    with pytest.raises(B.BuilderError, match="positive δ_n"):  # without the T1 noise the builder refuses the node
        B.build([sweep2, sweep1, B.Source("g5", rows, labels, evals)], preds, t0_noise, t0_nodes=B.SEVEN_T0, t1=t1)
