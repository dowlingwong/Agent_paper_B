"""Runbook P5: decision-relevance check."""
import json

import numpy as np
import pytest

from paperc import relevance as RV
from paperc.esyn import extra as X, policies as EP, sim


def _r(node, epoch, *, v=None, m=None, g=None, sigma=0.01, rule=None, action="execute"):
    forced = rule is not None
    return {"identity": {"node": node, "epoch": epoch},
            "state": {"rule_forced": forced, "sigma_node": sigma,
                      "forecasts": {"a2u": {"v_star": v, "m_hat": m, "g": g}}},
            "action": {"action": action, "rule": rule or "policy"}, "env": {"constants": {}}}


def test_known_shares():
    rows = []
    # E1: distances (V* - g) / sigma = -2, -0.8, -0.4, -0.1, 0.1, 0.3, 0.6, 1.5   (g = 0.001, sigma = 0.01)
    for z in (-2, -0.8, -0.4, -0.1, 0.1, 0.3, 0.6, 1.5):
        rows.append(_r("n", "E1", v=0.001 + z * 0.01, g=0.001))
    # E2: m_hat / sigma = -0.2, 0.7, 3.0
    for z in (-0.2, 0.7, 3.0):
        rows.append(_r("n", "E2", m=z * 0.01))
    rows += [_r("n", "E1", rule="rule_duplicate", action="skip"), _r("n", "E1", rule="rule_noop", action="skip")]
    s = RV.relevance(rows)["n"]
    assert s.e1.n_eligible == 8 and s.e1.counts == {0.25: 2, 0.5: 4, 1.0: 6}
    assert s.e1.shares[1.0] == pytest.approx(6 / 8)
    assert s.e1.quantiles[0.0] == pytest.approx(-2) and s.e1.quantiles[1.0] == pytest.approx(1.5)
    assert s.e2.counts == {0.25: 1, 0.5: 1, 1.0: 2}
    assert s.n_e1_rows == 10 and s.rule_skip_share == pytest.approx(0.2)
    assert s.rule_skips == {"rule_duplicate": 1, "rule_noop": 1}
    assert s.e1.relevant and s.e2.relevant and s.price == 0.001


def test_track_s_stop4_fixture_has_no_decision_relevant_states():
    """Track S STOP 4: every V* - g in 2.6-4.1 sigma, every E1 skip a rule duplicate."""
    rng = np.random.default_rng(4)
    rows = []
    for node, lo, hi in (("digits_mlp", 2.58, 2.61), ("tabular_mlp", 4.04, 4.06)):
        for z in rng.uniform(lo, hi, 300):
            rows.append(_r(node, "E1", v=0.00066 + z * 0.0066, sigma=0.0066, g=0.00066))
        rows += [_r(node, "E1", rule="rule_duplicate", action="skip", sigma=0.0066) for _ in range(400)]
    out = RV.relevance(rows)
    for node in ("digits_mlp", "tabular_mlp"):
        s = out[node]
        assert not s.e1.relevant and s.e1.counts[1.0] == 0
        assert s.rule_skips == {"rule_duplicate": 400}
        assert s.verdict()[0].startswith("E1: no decision-relevant states")
    md = RV.markdown(out, belief="a2u", h=0.0)
    assert md.count("no decision-relevant states") >= 2


def test_price_sources_and_errors():
    rows = [_r("a", "E1", v=0.002)]
    with pytest.raises(RV.RelevanceInputError):
        RV.relevance(rows)                                      # no price anywhere
    assert RV.relevance(rows, g=0.002)["a"].e1.counts[0.25] == 1
    assert RV.relevance(rows, g={"a": 0.0})["a"].e1.counts[0.25] == 1   # 0.002 / 0.01 = 0.2 sigma
    rows2 = [dict(_r("a", "E1", v=0.002), env={"constants": {"g": 0.002}})]
    assert RV.relevance(rows2)["a"].price == 0.002
    with pytest.raises(RV.RelevanceInputError):
        RV.relevance([_r("a", "E1", v=None, g=0.001)])
    varies = [_r("a", "E1", v=0.002, g=0.001), _r("a", "E1", v=0.002, g=0.002)]
    assert RV.relevance(varies)["a"].price == "varies"


def test_on_esyn_records_and_cli(tmp_path):
    w = X.WORLDS["budget"]
    pol = EP.Static(0.001, 0.0)
    rows = [row for i in range(20) for row in sim.run_campaign(w, pol, i, record=True).rows]
    out = RV.relevance(rows, g=0.001, validate=True)
    s = out["esyn_budget"]
    assert s.e1.n_eligible > 0 and 0.0 <= s.e1.shares[1.0] <= 1.0
    assert s.rule_skips and set(s.rule_skips) == {"rule_noop"}
    f = tmp_path / "rows.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    md, js = tmp_path / "rel.md", tmp_path / "rel.json"
    assert RV.main([str(f), "--out", str(md), "--json", str(js), "--g", "0.001"]) == 0
    assert "esyn_budget" in md.read_text() and json.loads(js.read_text())["esyn_budget"]["E1"]["n_eligible"] > 0
    bad = [dict(r) for r in rows]
    bad[0] = json.loads(json.dumps(bad[0]))
    bad[0]["state"]["runs_used"] = 3                              # breaks the budget chain
    with pytest.raises(RV.RelevanceInputError):
        RV.relevance(bad, g=0.001, validate=True)
