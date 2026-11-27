"""Runbook PH: the headroom census reproduces the Track S S0.5 summary and is reproducible from pinned commits."""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pytest

from paperc import census as C

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "paperC" / "census" / "census_v1.json"


def _have(ref):
    return subprocess.run(["git", "-C", str(REPO), "cat-file", "-e", f"{ref}^{{commit}}"],
                          capture_output=True).returncode == 0


needs_pins = pytest.mark.skipif(not (_have(C.TRACKS_PIN) and _have(C.SWEEP_PIN)),
                                reason="census input commits not present (git fetch trackS-ops-20261030 and "
                                       "codex/coordinator-20261031)")


@pytest.fixture(scope="module")
def result():
    return json.loads(json.dumps(C.run(REPO), sort_keys=True))


@needs_pins
def test_committed_census_is_current(result):
    assert json.loads(OUT.read_text()) == result


@needs_pins
def test_reproduces_track_s_s05_summary(result):
    """Numbers of TRACKS_S05_SUMMARY_20261115.md §2 and §4 (mac-tracks-stop4-end-20261115 @ 795e518b)."""
    t = {c["node"]: c for c in result["tracks"]}
    d, tb = t["digits_mlp"], t["tabular_mlp"]
    assert (d["e1"]["margin_min_sigma"], d["e1"]["margin_max_sigma"]) == (2.576, 2.612)      # 2.58-2.61 sigma
    assert (tb["e1"]["margin_min_sigma"], tb["e1"]["margin_max_sigma"]) == (4.038, 4.056)    # 4.04-4.06 sigma
    assert d["e1"]["v_star_range_sigma"] == 0.036 and tb["e1"]["v_star_range_sigma"] == 0.018
    assert d["e1"]["n_eligible"] == 298 and tb["e1"]["n_eligible"] == 330
    assert d["e1"]["near_price_share"] == 0.0 and tb["e1"]["near_price_share"] == 0.0
    assert d["e1"]["skip_reasons"] == {"rule_duplicate": 429} and tb["e1"]["skip_reasons"] == {"rule_duplicate": 399}
    assert round(46 / 298, 3) == d["e2"]["near_zero_share"] and round(38 / 330, 3) == tb["e2"]["near_zero_share"]
    assert d["keep_quality"]["logged_action_mismatches"] == 0 == tb["keep_quality"]["logged_action_mismatches"]
    assert d["e2"]["actions"] == {"keep": 148, "discard": 170, "failed_invalid": 53}
    assert tb["e2"]["actions"] == {"keep": 158, "discard": 192, "failed_invalid": 51}
    assert d["budget"]["binding_share_by_W"] == {"8": 1.0, "10": 1.0, "12": 0.94, "20": 0.04}
    assert tb["budget"]["binding_share_by_W"] == {"8": 1.0, "10": 1.0, "12": 1.0, "20": 0.16}
    assert d["budget"]["llm_cap_reached_share_at_W40"] == 1.0 == tb["budget"]["llm_cap_reached_share_at_W40"]


@needs_pins
def test_sweep_covers_eight_nodes_and_both_modes(result):
    s = {c["node"]: c for c in result["sweep"]}
    assert len(s) == 8
    for c in s.values():
        assert c["n_campaigns"] == 36            # 18 instances x 2 memory modes
        assert c["budget"]["runs_per_campaign"] == 20


def test_v_star_formula():
    tau, sig = 2.0, 1.0
    assert math.isclose(C.v_star(0.0, tau, sig), 0.3989422804 * tau ** 2 / math.sqrt(tau ** 2 + sig ** 2), rel_tol=1e-9)
    assert C.v_star(0.3, 0.0, 1.0) == 0.3 and C.v_star(-0.3, 0.0, 1.0) == 0.0
    assert C.v_star(0.0, 3.0, 1.0) > C.v_star(0.0, 2.0, 1.0)
    # S0.5 summary §4: at mu = 0, 0.399 tau_w^2 / sqrt(tau_w^2 + sigma_cmp^2) = 2.8 sigma_node on digits
    assert round(C.v_star(0.0, 0.0493, 0.0186) / 0.0066, 1) == 2.8


def test_robust_sd():
    x = np.random.default_rng(0).normal(0, 2.0, 20000)
    assert abs(C.robust_sd(x) - 2.0) < 0.05


# ---------------------------------------------------------------- adapter fixtures (always run)

def _trial(i, *, patch, valid=True, decision="discarded", before=None, delta=None):
    return {"budget_index": i, "patch_hash": patch, "validity_status": "valid" if valid else "invalid",
            "decision": decision, "current_best_before": before, "delta_vs_best": delta}


def test_parse_sweep_campaign():
    trials = [_trial(1, patch="a", decision="kept"),                                  # trial 1: kept, no delta
              _trial(2, patch="b", before=0.90, delta=-0.01),
              _trial(3, patch="b", before=0.90, delta=-0.01),                          # duplicate patch
              _trial(4, patch="c", valid=False),                                       # invalid
              _trial(5, patch="d", decision="kept", before=0.90, delta=0.02),
              _trial(6, patch="e", before=0.92, delta=0.0)]
    cp = C.parse_sweep_campaign(trials)
    assert cp["duplicates"] == 1 and cp["invalid"] == 1
    assert cp["comparisons"] == [-0.01, 0.02, 0.0] and cp["kept"] == [0.02] and cp["keeps_after_trial1"] == 1
    assert cp["trial1_metric"] == 0.90 and math.isclose(cp["final_best"], 0.92)


def test_join_keeps_and_logged_actions():
    roots = [{"status": "ok", "instance_id": "n__s1", "y_terminal": 1.0, "y_after_trial1": 0.5,
              "decisions": [{"epoch": "E2", "action": "keep", "index": 1},
                            {"epoch": "E2", "action": "keep", "index": 2},
                            {"epoch": "E2", "action": "discard", "index": 3},
                            {"epoch": "E2", "action": "keep", "index": 4}]}]
    rows = [{"instance": "tracks_n__s1", "budget_index": 2, "delta_hat": 0.3, "delta_audit": 0.2},
            {"instance": "tracks_n__s1", "budget_index": 3, "delta_hat": 0.1, "delta_audit": -0.1}]
    j = C.join_keeps(roots, rows)
    assert j == [{"instance": "n__s1", "keeps": [(0.3, 0.2)], "missing": 1, "audited_gain": 0.5}]
    assert C.logged_action_mismatches(roots, rows) == 1     # index 3 discarded although delta_hat > 0


def test_c1_paired_and_node_level_v_star():
    rec = {"default_metric": 0.9, "sigma_joint": 0.05, "edits": [
        {"sd_joint": 0.01, "rho_joint": 0.995, "flip_emp": 0.2, "campaign_wrong": True, "decision_regret": 0.001,
         "material": False},
        {"sd_joint": 0.02, "rho_joint": 0.98, "flip_emp": 0.4, "campaign_wrong": False, "decision_regret": 0.003,
         "material": True}]}
    p = C.c1_paired(rec)
    # sd_joint already is the sd of the paired difference: used as is, never rescaled by rho_joint
    assert math.isclose(p["paired_sd"], 0.015) and math.isclose(p["paired_sd_material"], 0.02)
    assert (p["paired_sd_min"], p["paired_sd_max"], p["start_seed_sd"]) == (0.01, 0.02, 0.05)
    assert math.isclose(p["flip_emp_mean"], 0.3) and p["campaign_wrong_share"] == 0.5
    small = np.random.default_rng(1).normal(0, 0.5, 200)
    assert C.node_level_v_star(small, 1.0)["status"].startswith("misspecified")
    ok = C.node_level_v_star(small, 0.1)
    assert ok["status"] == "ok" and ok["price_over_v_star"] != "inf"
    assert C._r(float("inf")) == "inf" and C._r(float("nan")) is None


@needs_pins
def test_sigma_d_is_the_material_edit_median_of_sd_joint(result):
    """The sweep's sigma_d is C1's median paired sd over material edits (review PH R2-1)."""
    for c in result["sweep"]:
        assert math.isclose(c["keep_quality"]["c1_paired_sd_material_edits_sigma_d"], 1.0, abs_tol=1e-4), c["node"]
