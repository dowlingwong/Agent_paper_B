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
