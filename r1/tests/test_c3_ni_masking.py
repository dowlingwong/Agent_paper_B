"""Results-masking test on synthetic fixtures (fixture-only; no tables, no labels). ENGINEERING_ONLY; AI-assisted (Claude)."""
import json

import numpy as np
import pytest

from r1.c3 import ni_masking as NI
from r1.c3.arms import LGBMPrior
from r1.c3.features import FEATURES
from r1.c3.labels import soft_label

NODES = ("nodeA", "nodeB")
SIG = 0.01


def _row(node, i, t, f, delta, dhat, soft, soft_eval, cand="c", inc="i"):
    return {"proposal_id": f"{node}:{i}:{t}", "node": node, "instance": f"{node}__s{i}", "instance_seed": i,
            "features": f, "sigma_node": SIG, "sigma_cmp": SIG, "delta_hat": dhat, "delta_true": delta,
            "weight": 1.0, "eval_weight": 1.0, "soft": soft, "soft_eval": soft_eval,
            "candidate_hash": f"{node}:{cand}", "incumbent_hash": f"{node}:{inc}"}


def synth(outcome: str, n_inst=24, per=20, seed=0):
    """Key 1 harmful, key 2 helpful by a campaign-level latent theta; key 3 no-ops.

    ``outcome``:
    - ``"informative"``: ``last_key_delta_z`` is a noisy copy of theta (earlier results predict increments);
    - ``"noise"``: ``last_key_delta_z`` is independent noise;
    - ``"function"``: every masked feature is a deterministic function of retained features (no extra information).
    Labels and evaluation targets use independent audit noise, as with disjoint seed halves.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for node in NODES:
        for i in range(n_inst):
            theta = rng.normal()
            for t in range(per):
                key = int(rng.integers(1, 4))
                f = {c: 0.0 for c in FEATURES}
                f["key_code"] = key
                f["node_code"] = NODES.index(node)
                f["budget_index"] = float(t)
                inert = key == 3
                f["active_seen_before"] = float(inert)
                f["active_equals_incumbent"] = float(inert)
                if outcome == "informative":
                    f["last_key_delta_z"] = theta + rng.normal(0, 0.3)
                elif outcome == "noise":
                    f["last_key_delta_z"] = rng.normal()
                else:
                    f["last_key_delta_z"] = 0.5 * key - 1.0
                f["keeps_so_far"] = float(t // 4)
                if inert:
                    delta = 0.0
                elif key == 1:
                    delta = -1.5 * SIG + rng.normal(0, 0.1 * SIG)
                else:
                    delta = 1.5 * theta * SIG + rng.normal(0, 0.1 * SIG)
                dhat = 0.0 if inert else delta + rng.normal(0, SIG)
                lab = None if inert else delta + rng.normal(0, 0.1 * SIG)
                evl = None if inert else delta + rng.normal(0, 0.1 * SIG)
                soft = soft_label(lab, 0.1 * SIG, SIG, inert=inert, sigma_mode="se_audit")
                soft_eval = None if inert else soft_label(evl, 0.1 * SIG, SIG, sigma_mode="se_audit")
                rows.append(_row(node, i, t, f, delta, dhat, soft, soft_eval, cand=f"{i}:{t}", inc=f"{i}"))
    return rows


def synth_recurring_pairs(n_inst=24, n_pairs=12, seed=0):
    """Every campaign replays the same (candidate, incumbent) pairs; true increments depend only on the key.

    Each pair's training label carries a pair-specific audit error shared across campaigns (same start
    configuration, same label seeds). ``recorded_gain_z`` (masked) identifies the pair, so the full arm can learn
    that shared label noise. The evaluation half has independent noise: scoring against it must not flag.
    """
    rng = np.random.default_rng(seed)
    pair_key = rng.integers(1, 3, n_pairs)
    pair_noise = rng.normal(0, 1.0 * SIG, n_pairs)
    rows = []
    for node in NODES:
        for i in range(n_inst):
            for p in range(n_pairs):
                key = int(pair_key[p])
                f = {c: 0.0 for c in FEATURES}
                f["key_code"] = key
                f["node_code"] = NODES.index(node)
                f["recorded_gain_z"] = float(p)
                delta = (-0.5 if key == 1 else 0.5) * SIG
                dhat = delta + rng.normal(0, SIG)
                soft = soft_label(delta + pair_noise[p], 0.1 * SIG, SIG, sigma_mode="se_audit")
                soft_eval = soft_label(delta + rng.normal(0, 0.1 * SIG), 0.1 * SIG, SIG, sigma_mode="se_audit")
                rows.append(_row(node, i, p, f, delta, dhat, soft, soft_eval, cand=f"p{p}", inc="start"))
    return rows


def test_feature_lists_exist_are_disjoint_and_are_dropped():
    assert set(NI.DIRECT_OUTCOME_FEATURES) <= set(FEATURES)
    assert not set(NI.DIRECT_OUTCOME_FEATURES) & set(NI.RETAINED_INCUMBENT_DEPENDENT)
    pytest.importorskip("lightgbm")
    rows = synth("informative", n_inst=6, per=10)
    m = NI.ARMS["masked"]().fit(rows)
    assert not set(NI.DIRECT_OUTCOME_FEATURES) & set(m.cols)
    assert set(NI.DIRECT_OUTCOME_FEATURES) <= set(LGBMPrior().fit(rows).cols)


def test_results_add_value_when_results_predict_increments():
    pytest.importorskip("lightgbm")
    res = NI.run_test(synth("informative"), "instance", 3, n_boot=300)
    pooled = res["pooled"]
    assert res["scored_against"] == "soft_eval"
    assert pooled["rps_masked"] > pooled["rps_full"]
    assert pooled["rps_masked_minus_full"]["ci95"][0] > 0 and pooled["results_add_predictive_value"]
    assert pooled["utility_per20_full_minus_masked"]["mean"] > 0
    assert set(res["nodes"]) == set(NODES)


def test_null_rate_when_results_carry_no_information():
    pytest.importorskip("lightgbm")
    flags = [NI.run_test(synth("noise", seed=s), "instance", 3, n_boot=200)["pooled"]["results_add_predictive_value"]
             for s in range(10)]
    assert sum(flags) <= 2


def test_no_flag_when_masked_features_are_functions_of_retained_features():
    pytest.importorskip("lightgbm")
    res = NI.run_test(synth("function"), "instance", 3, n_boot=300)
    assert not res["pooled"]["results_add_predictive_value"]


def test_label_half_scoring_flags_shared_label_noise_and_eval_half_does_not():
    pytest.importorskip("lightgbm")
    rows = synth_recurring_pairs()
    wrong = NI.run_test(rows, "instance", 3, n_boot=300, score_against="label")
    right = NI.run_test(rows, "instance", 3, n_boot=300)
    assert wrong["pooled"]["results_add_predictive_value"]          # the artefact of finding N2
    assert not right["pooled"]["results_add_predictive_value"]      # removed by evaluation-half scoring


def test_pair_grouped_folds_keep_recurring_pairs_in_one_fold():
    rows = synth_recurring_pairs(n_inst=6, n_pairs=3)
    rows[0]["candidate_hash"] = "unique"     # a campaign that shares at least the other pairs stays linked
    fid = NI.pair_grouped_folds(rows, 3)
    by_pair = {}
    for r, f in zip(rows, fid):
        by_pair.setdefault((r["node"], r["candidate_hash"], r["incumbent_hash"]), set()).add(int(f))
    assert all(len(s) == 1 for s in by_pair.values())
    distinct = synth("noise", n_inst=6, per=4)          # no recurring pairs: campaigns spread over all folds
    assert len(set(NI.pair_grouped_folds(distinct, 3).tolist())) == 3


def test_lono_and_pair_grouped_modes_run():
    pytest.importorskip("lightgbm")
    rows = synth("informative", n_inst=8, per=10)
    lono = NI.run_test(rows, "lono", n_boot=100)
    assert lono["mode"] == "lono" and lono["k"] is None and set(lono["nodes"]) == set(NODES)
    pg = NI.run_test(rows, "pair_grouped", 3, n_boot=100)
    assert pg["mode"] == "pair_grouped" and "n_instances" in pg["pooled"]["rps_masked_minus_full"]
    assert pg["fold_diagnostics"]["n_folds"] == 3 and not pg["fold_diagnostics"]["degenerate"]
    linked = synth_recurring_pairs(n_inst=6, n_pairs=3)       # every campaign shares the start pairs
    diag = NI.fold_diagnostics(linked, NI.pair_grouped_folds(linked, 3))
    assert diag["degenerate"] and all(len(v) == 1 for v in diag["folds_per_node"].values())
    assert diag["n_nodes_single_fold"] == len(diag["folds_per_node"])


def test_rejects_unknown_mode_and_missing_eval_labels():
    rows = synth("noise", n_inst=2, per=4)
    with pytest.raises(ValueError):
        NI.run_test(rows, "random")
    for r in rows:
        r.pop("soft_eval")
    with pytest.raises(ValueError):
        NI.run_test(rows, "instance")


def test_with_eval_soft_uses_the_evaluation_half_of_the_seeds():
    row = {"proposal_id": "p", "sigma_node": SIG, "features": {c: 0.0 for c in FEATURES}, "noop": False,
           "duplicate": False}
    audit = {"proposal_id": "p", "seeds": list(range(7001, 7011)), "delta_audit": 0.0, "se": 0.001,
             "candidate_metrics": [1.0] * 5 + [1.015] * 5, "incumbent_metrics": [1.0] * 10}
    out = NI.with_eval_soft([row], {"p": audit}, "se_audit")[0]
    # mean 1.5 sigma from seeds 7006-7010 (inside bin (1, 2]); the label half (7001-7005) has mean 0
    expected = soft_label(0.015, None, SIG, sigma_mode="pooled_node", k_label=5)
    assert np.argmax(out["soft_eval"]) == np.argmax(expected) == 9
    pooled = NI.with_eval_soft([row], {"p": audit}, "pooled_node")[0]["soft_eval"]
    assert np.allclose(pooled, expected)


def test_main_end_to_end(tmp_path, monkeypatch):
    pytest.importorskip("lightgbm")
    rows = synth("noise", n_inst=6, per=8)
    for r in rows:
        r.pop("soft_eval")
    audits = {}
    rng = np.random.default_rng(1)
    for r in rows:
        if r["features"]["key_code"] != 3:
            c = list(1.0 + r["delta_true"] + rng.normal(0, 0.1 * SIG, 10))
            audits[r["proposal_id"]] = {"proposal_id": r["proposal_id"], "seeds": list(range(7001, 7011)),
                                        "delta_audit": float(np.mean(c) - 1.0), "se": 0.001,
                                        "candidate_metrics": c, "incumbent_metrics": [1.0] * 10}
    monkeypatch.setattr(NI.OE, "table_noise", lambda table: None)
    monkeypatch.setattr(NI.OE, "assemble", lambda table, audits_path, seed_split, sigma_mode: rows)
    monkeypatch.setattr(NI, "load_audits", lambda table, audits_path: audits)
    out = tmp_path / "ni.json"
    assert NI.main(["--table", str(tmp_path), "--out", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["sigma_mode"] == "se_audit" and res["sigma_mode_role"] == "primary"
    assert set(NI.MODES) <= set(res) and res["label"] == "ENGINEERING_ONLY"
    assert "results_add_predictive_value" in res["instance"]["pooled"]
    assert "evidence_against_NI" not in json.dumps(res)
