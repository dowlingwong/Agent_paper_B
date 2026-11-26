"""ARMS-T1FEAT A: T1 features for the G.5 table (sweep2/t1_tasl/g5_features.py), their wiring into the assembly
(g5_assemble.py), the T1 noise input of the gate run (g5_noise.py) and the suite-name mapping. Synthetic only: fake
ledgers, fake G.1b runs and the synthetic G.5 world of test_t1_g5_seal; no sealed data, no real label or value."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
import pytest

from r1.tests.test_t1_g5_seal import (A, G, NODE, SIGMA, SIGMA_JOINT, SPEC, Engine, S, assemble_world,  # noqa: F401
                                      lock_for, node_git, world)
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
    assert first["cfg_equals_incumbent"] == 0.0                # the fixture's records carry raw code states
    noop = by[f"g5.history:{NODE}__s5101:t008"]["features"]
    assert noop["active_equals_incumbent"] == 1.0 and noop["recorded_gain_z"] == pytest.approx(0.10 / SIGMA)
    build = json.loads((table / "build.json").read_text())
    assert build["featurizer"] == json.loads(json.dumps(F.describe()))
    assert build["nodes"][NODE]["gate_suite"] == "MLAgentBench" and build["nodes"][NODE]["suite"] == "mlagentbench"
    feat = build["nodes"][NODE]["features"]
    # raw states everywhere and the duplicate (step 5) repeats step 2's evaluated state: both D9 counts are 0
    assert feat == {"raw_state_missing": 0, "flag_mismatch": 0}
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


def realistic_ledger(k, wave, repeat_step=None):
    """Run records as the harness writes them (runner.run, apply_diff, manager_view): the baseline has no diff and its
    own code states; an executed diff has the states in the record and in its ``diff`` provenance; a not-run diff
    (inert, duplicate) has them only in ``diff``. Raw states everywhere. Step 5 is a duplicate of step 2's evaluated,
    discarded (non-incumbent) state; steps 8, 9, ... are inert (normalised state = the incumbent's)."""
    def prov(state, raw, inc, status):
        return {"status": status, "code_state_sha256": state, "code_state_raw_sha256": raw,
                "incumbent_code_state_sha256": inc, "normalised_diff_sha256": f"nd-{state}",
                "inert": status == "inert", "duplicate": status == "duplicate"}

    def executed(state, raw, inc):
        return {"executed": True, "code_state_sha256": state, "code_state_raw_sha256": raw,
                "incumbent_code_state_sha256": inc, "elapsed_seconds_info_only": 10.0,
                "diff": prov(state, raw, inc, "applied")}
    best = 0.40
    lines = [json.dumps({"schema": LS, "step": 0, "decision": "baseline",
                         "final_outcome": {"kind": "ok", "value": best},
                         "runs": [{"executed": True, "diff": None, "code_state_sha256": "B",
                                   "code_state_raw_sha256": "Br", "incumbent_code_state_sha256": "B"}],
                         "best_after": best})]
    parent, parent_raw = "B", "Br"
    call = {"usage": {"prompt_tokens": 1000, "completion_tokens": 300}, "request": {"cache_prompt": False}}
    for st in range(1, 21):
        e = {"schema": LS, "step": st, "manager_call": call}
        if st == 1:
            e.update(decision="kept", proposal={"diff": "d1"}, final_outcome={"kind": "ok", "value": 0.50},
                     runs=[executed("C1", "C1r", "B")])
            best, parent, parent_raw = 0.50, "C1", "C1r"
        elif st in (4, 12):
            e.update(decision="invalid_proposal")
        elif st % 4 in (2, 3):
            cand = f"S{wave}{k}_{2 if st == repeat_step else st}"     # repeat_step: re-runs step 2's state
            e.update(decision="discarded", proposal={"diff": f"diff-{wave}{k}-{st}"},
                     final_outcome={"kind": "ok", "value": 0.45}, runs=[executed(cand, cand + "r", parent)])
        elif st == 5:
            dup = f"S{wave}{k}_2"
            e.update(decision="not_run_duplicate", proposal={"diff": "dup"},
                     runs=[{"executed": False, "outcome": None, "diff": prov(dup, dup + "r", parent, "duplicate")}])
        else:
            e.update(decision="not_run_inert", proposal={"diff": "ws"},
                     runs=[{"executed": False, "outcome": None,
                            "diff": prov(parent, parent_raw, parent, "inert")}])
        e["best_after"] = best
        lines.append(json.dumps(e))
    return lines


class RealisticEngine(Engine):
    repeat_step = None

    def __call__(self, argv, **kw):
        if "--campaign" not in argv:
            return super().__call__(argv, **kw)
        import subprocess
        from pathlib import Path
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True)
        f = json.loads(Path(argv[argv.index("--campaign") + 1]).read_text())
        for inst in f["instances"]:
            d = out / f"instance_{inst['instance']}_{inst['memory_mode']}"
            d.mkdir()
            lines = realistic_ledger(inst["instance"], f["wave"], self.repeat_step)
            (d / "campaign_ledger.jsonl").write_text("\n".join(lines) + "\n")
        (out / "campaign_record.json").write_text(json.dumps({"stop": None}))
        return subprocess.CompletedProcess(argv, 0, "engine ok", "")


def test_assembly_on_realistic_records(world):
    """Code states of not-run diffs only in the diff provenance (review M4): the duplicate takes its code state from
    there, every feature is computed with raw states, and the harness verdicts agree with the code-state fields."""
    s = world["spec"]
    table, ev, _ = assemble_world(world, RealisticEngine(s))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    by = {r["proposal_id"]: r for r in rows}
    dup = by[f"g5.history:{NODE}__s5101:t005"]
    assert dup["duplicate"] and dup["candidate_hash"] == "S11_2" and dup["delta_hat"] == 0.0
    f = dup["features"]
    assert (f["active_seen_before"], f["full_seen_before"], f["active_equals_incumbent"]) == (1.0, 1.0, 0.0)
    noop = by[f"g5.history:{NODE}__s5101:t008"]
    assert noop["noop"] and noop["candidate_hash"] == "C1"
    assert (noop["features"]["active_equals_incumbent"], noop["features"]["cfg_equals_incumbent"]) == (1.0, 1.0)
    ran = by[f"g5.history:{NODE}__s5101:t002"]["features"]
    assert (ran["active_equals_incumbent"], ran["active_seen_before"], ran["cfg_equals_incumbent"]) == (0.0, 0.0, 0.0)
    build = json.loads((table / "build.json").read_text())
    assert build["nodes"][NODE]["features"] == {"raw_state_missing": 0, "flag_mismatch": 0}
    assert not any(math.isnan(r["features"][k]) for r in rows for k in F.RAW_STATE_FIELDS)
    raw = (table / "proposals.jsonl").read_bytes()
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert (table / "proposals.jsonl").read_bytes() == raw


def test_d9_b_flag_mismatch_of_an_executed_row_the_fields_call_seen_stops(world):
    """The converse direction (review m5): an executed row whose code state was evaluated before (here step 6 re-runs
    step 2's discarded state, which the harness would have called a duplicate) makes flag_mismatch non-zero, and under
    D9 B (R1-T1-FEAT-DECISIONS) the assembly STOPs with the fixed reason; nothing is written."""
    s = world["spec"]
    eng = RealisticEngine(s)
    eng.repeat_step = 6
    table, ev, _ = assemble_world(world, eng)
    with pytest.raises(G.Stop) as exc:
        A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    assert str(exc.value) == A.D9_STOP.format(node=NODE, counts="flag_mismatch")
    assert not table.exists() and not ev.exists()


@pytest.mark.parametrize("engine_kw, counts", [
    ({"raw": False}, "raw_state_missing"),                      # run records without raw code states
    ({"dup_of_incumbent": True}, "flag_mismatch"),              # a "duplicate" of the incumbent: the harness says inert
    ({"raw": False, "dup_of_incumbent": True}, "raw_state_missing and flag_mismatch"),
])
def test_d9_b_traindev_stage_stops_on_a_non_zero_count(world, engine_kw, counts):
    """D9 B: a non-zero raw_state_missing or flag_mismatch count STOPs the train/dev assembly with a fixed clear-text
    reason that carries the node and the count names, no count and no value; nothing is written."""
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s, **engine_kw))
    with pytest.raises(G.Stop) as exc:
        A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    msg = str(exc.value)
    # the fixed template with the node and the count names only: no count and no value
    assert msg == A.D9_STOP.format(node=NODE, counts=counts) and "D9 B" in msg and "R1-T1-FEAT-DECISIONS" in msg
    assert not table.exists() and not ev.exists()


def test_d9_b_test_stage_and_integrity_check_stop_too(world, monkeypatch):
    """D9 B in the test stage and in the release step's re-derivation: the train/dev stage passes (counts 0); if the
    re-derived counts were non-zero (simulated: the node_rows result patched), the test stage STOPs before the
    evaluation block is written, and verify_evidence STOPs."""
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    real = A.node_rows

    def counted(*a, **kw):
        out = real(*a, **kw)
        out["features"] = dict(out["features"], raw_state_missing=1)
        return out
    monkeypatch.setattr(A, "node_rows", counted)
    with pytest.raises(G.Stop) as exc:
        A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert str(exc.value) == A.D9_STOP.format(node=NODE, counts="raw_state_missing")
    assert not (ev / "evaluation_block.jsonl").exists()
    from r1.c3 import release as R
    with R.integrity_context():
        with pytest.raises(G.Stop, match=r"D9 B"):
            A.verify_evidence(table, ev, test=False, lock=lock_for(world, "traindev"), git=node_git(),
                              spec_path=world["sp"])
    monkeypatch.setattr(A, "node_rows", real)
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    assert (ev / "evaluation_block.jsonl").exists()


def test_assembly_refuses_a_node_spec_suite_other_than_declared(world, monkeypatch):
    s = world["spec"]
    table, ev, _ = assemble_world(world, Engine(s))
    monkeypatch.setitem(F.T1_NODE_INFO, NODE, {"suite": "mlgym", "code": 12})    # the node spec says mlagentbench
    with pytest.raises(G.Stop, match="T1 features cannot be computed.*declares"):
        A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    assert not table.exists()


# =============================================================================================== T1 noise
def g1b_rows(node, *, n_edits=3, seeds=6, short_edit=None, noise=0.003, flat=False):
    """Synthetic G.1b runs.jsonl records for one node at the joint seeds 3001.. (never real values), plus a default
    run per config, a failed run (not paired) and another node's run (ignored). ``flat``: every edit shifts every seed
    by the same amount (sd 0)."""
    rows = []
    for c in ["c0"] + [f"c{k}" for k in range(1, n_edits + 1)]:
        for s in range(seeds if c != short_edit else 2):
            k = int(c[1:])
            if flat:                                    # dyadic: every paired difference is exactly k/64
                m = 0.5 + s / 1024 + k / 64
            else:
                m = 0.8 + 0.01 * k + random.Random(f"{c}:{s}").gauss(0, noise * (1 + k))
            rows.append({"node": node, "config": c, "condition": "joint", "train_seed": 3001 + s,
                         "split_seed": 3001 + s, "success": True, "metric": m, "wall_seconds": 1.0})
        rows.append({"node": node, "config": c, "condition": "default", "train_seed": None, "split_seed": None,
                     "success": True, "metric": 0.8, "wall_seconds": 1.0})
    rows.append({"node": node, "config": "c1", "condition": "joint", "train_seed": 3030, "split_seed": 3030,
                 "success": False, "metric": None, "wall_seconds": 1.0})      # a failed run: not paired
    rows.append({"node": "other_node", "config": "c1", "condition": "joint", "train_seed": 3001, "split_seed": 3001,
                 "success": True, "metric": 5.0, "wall_seconds": 1.0})       # another node: ignored
    return rows


def g1b_run(world, node, *, n_edits=3, seeds=6, short_edit=None, noise=0.003, rows=None, flat=False):
    """A synthetic assembled G.1b run written as the REL-T1-G1B copies beside the world's summary copy (D6 A):
    runs.jsonl and ASSEMBLY.json (and edits.json, which only the e1_report oracle reads), and the verdict fields its
    summary would carry."""
    d = world["repo"] / Path(world["rel"]).parent
    rows = g1b_rows(node, n_edits=n_edits, seeds=seeds, short_edit=short_edit, noise=noise, flat=flat) \
        if rows is None else rows
    (d / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "edits.json").write_text(json.dumps({node: [{"symbol": f"k{k}", "old": "a", "new": "b"}
                                                     for k in range(1, n_edits + 1)]}))
    (d / "ASSEMBLY.json").write_text(json.dumps({"schema": G.ASSEMBLY_SCHEMA, "run_id": "g1b-tasl-20261121-b",
                                                 "runs_sha256": G.L._sha_file(d / "runs.jsonl")}))
    counts = [2 if short_edit == f"c{k}" else seeds for k in range(1, n_edits + 1)]
    return d, {"n_edits": n_edits, "paired_joint_n": counts, "assembly_sha256": G.L._sha_file(d / "ASSEMBLY.json")}


def bind_summary(world, run_dir, verdict_extra):
    """Rewrite the world's REL-T1-G1B copy with the run's assembly sha256 and the verdict fields, and rebind the spec's
    noise_floor.seven (summary, ASSEMBLY.json and runs.jsonl sha256s; before the run, as sign_note does)."""
    s, repo, rel = world["spec"], world["repo"], world["rel"]
    summary = {"schema": G.SUMMARY_SCHEMA, "label": G.ENGINEERING_ONLY, "run_id": "g1b-tasl-20261121-b",
               "assembly_sha256": verdict_extra["assembly_sha256"],
               "verdicts": {NODE: {"qualifies_D21": True, "sigma_joint": SIGMA_JOINT,
                                   "determinism": {"deterministic": True},       # g1b_lib.summarise's shape
                                   "n_edits": verdict_extra["n_edits"],
                                   "paired_joint_n": verdict_extra["paired_joint_n"]}}}
    (repo / rel).write_text(json.dumps(summary))
    s["noise_floor"]["seven"].update(sha256=G.L._sha_file(repo / rel),
                                     assembly_sha256=G.L._sha_file(run_dir / "ASSEMBLY.json"),
                                     runs_sha256=G.L._sha_file(run_dir / "runs.jsonl"))
    world["sp"].write_text(json.dumps(s))
    rec = json.loads(world["srv"].read_text())
    world["srv"].write_text(json.dumps(rec | {"spec_sha256": G.L._sha_file(world["sp"])}))
    return lock_for(world, "traindev")("traindev")


def t0_rule(run_dir, node):
    """dataset.noise_table's σ_node rule applied to e1_report's edits of the run (the oracle)."""
    from r1.noise import e1_report
    edits = [e for e in e1_report.summarise(run_dir)["nodes"][node]["edits"] if "sd_joint" in e]
    return float(np.median([e["sd_joint"] for e in edits if e.get("material")] or [e["sd_joint"] for e in edits])), \
        sum(bool(e.get("material")) for e in edits)


def test_noise_d18_and_t0_sigma_match_e1_report_and_are_bound_to_the_copy(world):
    """D6 A and D6-σ B: σ_node is dataset.noise_table's rule on e1_report's edits of the copied run, δ_n is D18 on
    e1_report's median; the record's σ_node is the table's (noise_by_node) by construction, not sigma_joint."""
    from r1.noise import e1_report
    d, extra = g1b_run(world, NODE, n_edits=4, short_edit="c3")
    row = bind_summary(world, d, extra)
    rec = N.derive(world["spec"], row)
    assert rec["schema"] == "g5_t1_noise/2" and rec["t1_sigma_node"] == "t0_definition"
    n = rec["nodes"][NODE]
    pinned = e1_report.summarise(d)["nodes"][NODE]["summary"]["median_sd_joint"]
    assert n["median_paired_sd"] == pinned and n["delta_n"] == max(0.002, 0.25 * pinned)
    want, n_mat = t0_rule(d, NODE)
    assert n["sigma_node"] == n["sigma_node_t0_definition"] == want and n["n_material_edits"] == n_mat
    assert n["sigma_node"] != SIGMA_JOINT and n["sigma_joint"] == SIGMA_JOINT
    assert n["sigma_node_rule"] == "t0_definition"
    assert A.noise_by_node(world["spec"], row)[NODE]["sigma_node"] == n["sigma_node"]     # the table's σ_node
    assert n["n_edits"] == 4 and n["n_edits_with_sd"] == 3
    assert n["summary"] == world["rel"] and n["summary_sha256"] == G.L._sha_file(world["repo"] / world["rel"])
    assert n["runs_sha256"] == G.L._sha_file(d / "runs.jsonl") and n["assembly_sha256"] == extra["assembly_sha256"]
    assert n["runs_copy"] == str(Path(world["rel"]).parent / "runs.jsonl")
    assert not any(isinstance(v, str) and v.startswith("/") for v in n.values())          # no absolute path
    assert N.derive(world["spec"], row, {NODE: d}) == rec                                  # the copy directory itself
    noise = N.builder_noise(rec)
    assert noise == {NODE: {"delta_n": n["delta_n"], "sigma_node": want}}
    sha = N.write_record(rec, "docs/r1/reports/t1_noise_x/T1_NOISE.json", repo=world["repo"])
    raw = (world["repo"] / "docs/r1/reports/t1_noise_x/T1_NOISE.json").read_bytes()
    assert N.builder_noise({}, sha256=sha, raw=raw) == noise
    with pytest.raises(G.Stop, match="differs from the sha256"):
        N.builder_noise({}, sha256="0" * 64, raw=raw)
    with pytest.raises(FileExistsError):
        N.write_record(rec, "docs/r1/reports/t1_noise_x/T1_NOISE.json", repo=world["repo"])
    with pytest.raises(G.Stop, match="not a g5_t1_noise/2 record"):
        N.builder_noise(dict(rec, schema="g5_t1_noise/1"))


def test_t0_sigma_equals_dataset_noise_table_on_a_t0_node(tmp_path):
    """g5_noise's σ_node and δ_n equal dataset.noise_table's own values, computed by noise_table from e1_report's
    summary of the same synthetic run (the run labelled with a T0 node so that noise_table covers it), with and
    without a material edit."""
    from r1.c3 import dataset
    from r1.noise import e1_report
    for name, kw in (("noisy", {"noise": 0.003}), ("quiet", {"noise": 0.03, "n_edits": 2}),
                     ("flat", {"flat": True})):
        d = tmp_path / name
        d.mkdir()
        rows = g1b_rows("digits_mlp", **kw)
        (d / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        n_edits = kw.get("n_edits", 3)
        (d / "edits.json").write_text(json.dumps({"digits_mlp": [{"symbol": f"k{k}", "old": "a", "new": "b"}
                                                                 for k in range(1, n_edits + 1)]}))
        (d / "ASSEMBLY.json").write_text(json.dumps({"runs_sha256": G.L._sha_file(d / "runs.jsonl")}))
        summary = json.dumps({"assembly_sha256": G.L._sha_file(d / "ASSEMBLY.json"), "verdicts": {"digits_mlp": {
            "n_edits": n_edits, "paired_joint_n": [6] * n_edits}}}).encode()
        got = N.node_delta("digits_mlp", summary, d)
        (d / "e1_summary.json").write_text(json.dumps(e1_report.summarise(d)))
        table = dataset.noise_table(d / "e1_summary.json")["digits_mlp"]
        assert got["sigma_node_t0_definition"] == table["sigma_node"], name
        assert got["delta_n"] == table["delta_n"] and got["median_paired_sd"] == table["median_sd_all"], name
    assert got["n_material_edits"] == 3                     # the flat run: every edit material, sd = 0 ...
    assert got["sigma_node_t0_definition"] == 0.0           # ... which noise_by_node refuses (no positive σ_node)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_noise_refuses_non_finite_paired_sds(world, bad):
    """Review m7: a non-finite metric gives a non-finite paired sd (or median): node_delta STOPs, in derive and in
    noise_by_node; finite inputs give the same values as before (the other noise tests)."""
    rows = g1b_rows(NODE)
    rows[1] = dict(rows[1], metric=bad)                         # c0 at one joint seed: every edit's sd is affected
    d, extra = g1b_run(world, NODE, rows=rows)
    row = bind_summary(world, d, extra)
    with pytest.raises(G.Stop, match="non-finite paired sd or median"):
        N.derive(world["spec"], row)
    with pytest.raises(G.Stop, match="non-finite paired sd or median"):
        A.noise_by_node(world["spec"], row)


def test_noise_d18_floor_through_derive(world):
    """A low-noise G.1b run: 0.25 x the median paired sd is below 0.002, so δ_n is D18's floor."""
    from r1.noise import e1_report
    d, extra = g1b_run(world, NODE, noise=1e-6)
    rec = N.derive(world["spec"], bind_summary(world, d, extra))
    n = rec["nodes"][NODE]
    assert 0 < n["median_paired_sd"] < 0.008 and n["delta_n"] == N.D18_FLOOR == 0.002
    assert n["median_paired_sd"] == e1_report.summarise(d)["nodes"][NODE]["summary"]["median_sd_joint"]
    assert N.builder_noise(rec)[NODE]["delta_n"] == 0.002


def test_noise_refusals(world, tmp_path):
    s = world["spec"]
    d, extra = g1b_run(world, NODE)
    row = bind_summary(world, d, extra)
    with pytest.raises(G.Stop, match="run directories are given"):
        N.derive(s, row, {NODE: d, "mlab_cifar10": d})
    with pytest.raises(G.Stop, match="under D6 A"):                 # only the copy beside the summary is read
        N.derive(s, row, {NODE: tmp_path})
    for value in (None, "sigma_joint", "t0"):                        # D6-σ B: the old sigma_joint path is removed
        other = json.loads(json.dumps(s))
        other["noise_floor"]["t1_sigma_node"] = value
        with pytest.raises(G.Stop, match="t1_sigma_node must be 't0_definition'"):
            N.derive(other, row)
    other = json.loads(json.dumps(s))
    other["noise_floor"]["seven"]["runs_sha256"] = "0" * 64          # the spec names other copies
    with pytest.raises(G.Stop, match="differ from the sha256s the REL-T1-G1B copy names"):
        N.derive(other, row)
    other["noise_floor"]["seven"]["runs_copy"] = "docs/r1/reports/elsewhere/runs.jsonl"
    with pytest.raises(G.Stop, match="not the ones the REL-T1-G1B copy names"):
        N.derive(other, row)
    good = (d / "runs.jsonl").read_bytes()
    (d / "runs.jsonl").write_bytes(good + b"\n")                 # not the run the copy binds
    with pytest.raises(G.Stop, match="not the run of the summary copy"):
        N.derive(s, row)
    (d / "runs.jsonl").write_bytes(good)
    (d / "ASSEMBLY.json").rename(d / "ASSEMBLY.moved")             # a copy missing
    with pytest.raises(G.Stop, match="not an assembled G.1b run directory"):
        N.derive(s, row)
    (d / "ASSEMBLY.moved").rename(d / "ASSEMBLY.json")
    bad = dict(extra, paired_joint_n=[6, 6, 5])
    row = bind_summary(world, d, bad)
    with pytest.raises(G.Stop, match="paired-seed counts"):
        N.derive(s, row)
    row = bind_summary(world, d, dict(extra, n_edits=None))
    with pytest.raises(G.Stop, match="n_edits"):
        N.derive(s, row)
    d, extra = g1b_run(world, NODE, flat=True)                      # sd 0 on every edit: no positive σ_node
    row = bind_summary(world, d, extra)
    with pytest.raises(G.Stop, match="no positive σ_node by T0's definition"):
        N.derive(s, row)
    with pytest.raises(G.Stop, match="T0 and a T1"):
        N.merge_noise({NODE: {"delta_n": 0.002, "sigma_node": 0.01}}, {NODE: {"delta_n": 0.003, "sigma_node": 0.01}})


@pytest.mark.parametrize("key, seed", [("train_seed", 7001), ("split_seed", 7005), ("seed", 7006),
                                       ("audit_seed", 7010)])
def test_noise_refuses_a_g1b_run_with_an_audit_seed(world, key, seed):
    """D6 A: a G.1b runs.jsonl holds noise-floor runs at the G.1b seeds only; a record at a seed in 7001-7010 (the G.5
    label and evaluation seeds), even of another node or a failed run, is a STOP; seeds just outside the block pass."""
    rows = g1b_rows(NODE)
    rows.append({"node": "other_node", "config": "c0", "condition": "joint", key: seed, "success": False,
                 "metric": None})
    d, extra = g1b_run(world, NODE, rows=rows)
    row = bind_summary(world, d, extra)
    with pytest.raises(G.Stop, match="seed in the audit block 7001-7010"):
        N.derive(world["spec"], row)
    with pytest.raises(G.Stop, match="seed in the audit block 7001-7010"):
        A.noise_by_node(world["spec"], row)
    rows[-1][key] = 7000 if seed == 7001 else 7011
    d, extra = g1b_run(world, NODE, rows=rows)
    N.derive(world["spec"], bind_summary(world, d, extra))


def test_noise_refuses_an_r1_sealed_copy(world, tmp_path, monkeypatch):
    """g5_noise refuses an ``r1_sealed`` path before reading it (as dataset.noise_table does): here the repository
    the copies are read from is reached through an ``r1_sealed`` path. Its copied check refuses exactly the paths
    ``analysis_guard.refuse_sealed`` refuses."""
    from r1.c3.analysis_guard import refuse_sealed
    d, extra = g1b_run(world, NODE)
    row = bind_summary(world, d, extra)
    sealed = tmp_path / "x" / "r1_sealed"
    sealed.parent.mkdir()
    sealed.symlink_to(world["repo"])
    monkeypatch.setattr(N.S, "REPO_ROOT", sealed)
    opened = []
    real = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda self: opened.append(self) or real(self))
    with pytest.raises(RuntimeError, match="r1_sealed paths are not analysis inputs"):
        N.derive(world["spec"], row)
    assert not any("r1_sealed" in str(x) for x in opened)
    monkeypatch.undo()
    real_seal = tmp_path / "y" / "r1_sealed"
    real_seal.mkdir(parents=True)
    link = tmp_path / "plain"
    link.symlink_to(real_seal)                                      # a symlink into the seal is refused by both
    for path in (sealed, sealed / "runs.jsonl", real_seal, link, link / "runs.jsonl", tmp_path / "R1_SEALED" / "x",
                 tmp_path / "ok"):
        got = []
        for fn in (refuse_sealed, N._refuse_sealed):
            try:
                fn(path)
                got.append(False)
            except RuntimeError:
                got.append(True)
        assert got[0] == got[1], path
        assert got[0] == (path.name != "ok"), path


def test_t0_plus_t1_gate_input_with_the_frozen_builder(world):
    """The assembled T1 table (features filled), the T1 noise record and the mapped suites go into the frozen
    builder beside a synthetic T0 world; the T1 node comes out with its gate suite and the derived δ_n. Under D6-σ B
    the table's σ_node (rows, soft labels, build.json) and the record's are T0's definition on the copied G.1b run, so
    the builder's "table sigma_node differs from the noise source" refusal passes; a record carrying the summary's
    sigma_joint instead is refused."""
    from r1.tests import test_gate_input_builder as TB
    s = world["spec"]
    d, extra = g1b_run(world, NODE)
    row = bind_summary(world, d, extra)
    want, _ = t0_rule(d, NODE)
    table, ev, _ = assemble_world(world, Engine(s, divergent_label={"S12_6"}, divergent_eval={"S13_7"}))
    A.assemble(world["sp"], "traindev", table, ev, lock=lock_for(world, "traindev"), git=node_git())
    A.assemble(world["sp"], "test", table, ev, lock=lock_for(world, "traindev", "test"), git=node_git())
    rows = [json.loads(x) for x in (table / "proposals.jsonl").read_text().splitlines()]
    labels = [json.loads(x) for x in (ev / "label_block.jsonl").read_text().splitlines()]
    evals = [json.loads(x) for x in (ev / "evaluation_block.jsonl").read_text().splitlines()]
    build = json.loads((table / "build.json").read_text())
    t1_noise = N.builder_noise(N.derive(s, row))
    assert t1_noise[NODE]["sigma_node"] == build["nodes"][NODE]["sigma_node"] == rows[0]["sigma_node"] == want
    bn = build["nodes"][NODE]
    assert bn["sigma_node_rule"] == "t0_definition" and bn["sigma_joint"] == SIGMA_JOINT
    assert all(r["sigma_node"] == r["sigma_cmp"] == want for r in rows)
    assert all(lab["soft_parameters"]["sigma_node"] == want for lab in labels if lab["label_kind"] == "audit")
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
    joint = {NODE: dict(t1_noise[NODE], sigma_node=SIGMA_JOINT)}    # the removed D6-σ A value: refused
    with pytest.raises(B.BuilderError, match="table sigma_node differs from the noise source"):
        B.build([sweep2, sweep1, B.Source("g5", rows, labels, evals)], preds, N.merge_noise(t0_noise, joint),
                t0_nodes=B.SEVEN_T0, t1=t1)
