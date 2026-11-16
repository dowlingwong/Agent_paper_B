"""Runbook P5: decision-relevance check (revised after review rounds 1 and 2)."""
import json
import math

import numpy as np
import pytest

from paperc import relevance as RV
from paperc import schema as S
from paperc.esyn import extra as X, policies as EP, sim

_step = iter(range(10**9))


def _r(node, epoch, *, v=None, m=None, g=None, sigma=0.01, rule=None, action=None, camp="c1", forced=False,
       branch=(), p_select=None, invalid=False, divergent=False, dhat=None, inst=None):
    action = action or {"E1": "execute", "E2": "keep", "verify": "verify", "reaudit": "reaudit",
                        "final": "select"}[epoch]
    return {"identity": {"node": node, "epoch": epoch, "campaign_id": camp, "instance_id": inst or camp,
                         "step_index": next(_step), "branch_path": list(branch)},
            "state": {"rule_forced": rule is not None, "sigma_node": sigma, "candidate_invalid": invalid,
                      "candidate_divergent": divergent, "candidate_delta_hat": dhat,
                      "forecasts": {"a2u": {"v_star": v, "m_hat": m, "g": g}}},
            "action": {"action": action, "rule": rule or ("fork_arm" if forced else "policy"), "forced": forced},
            "policy": {"policy": "p"}, "env": {"W": 10, "constants": {}},
            "fork": {"p_select": p_select} if p_select else None}


def rel(rows, **kw):
    return RV.relevance(rows, validate=False, **kw)


def test_known_shares_and_counts():
    rows = []
    # E1 distances (V* - g) / sigma = -2, -0.8, -0.4, -0.1, 0.1, 0.3, 0.6, 1.5 in two campaigns (g = 0.001)
    for i, z in enumerate((-2, -0.8, -0.4, -0.1, 0.1, 0.3, 0.6, 1.5)):
        rows.append(_r("n", "E1", v=0.001 + z * 0.01, g=0.001, camp=f"c{i % 3}",
                       action="skip" if z < 0 else "execute"))
    for z in (-0.2, 0.7, 3.0):
        rows.append(_r("n", "E2", m=z * 0.01))
    rows += [_r("n", "E1", rule="rule_duplicate", action="skip"), _r("n", "E1", rule="rule_noop", action="skip")]
    s = rel(rows)["n"]
    e1 = s.e1["g"]
    assert e1.n_eligible == 8 and e1.counts == {0.25: 2, 0.5: 4, 1.0: 6}
    assert e1.shares[1.0] == pytest.approx(6 / 8) and 0 < e1.intervals[1.0][0] < 6 / 8 < e1.intervals[1.0][1]
    assert e1.quantiles[0.0] == pytest.approx(-2) and e1.quantiles[1.0] == pytest.approx(1.5)
    assert s.e2.counts == {0.25: 1, 0.5: 1, 1.0: 2}
    assert s.n_e1_rows == 10 and s.rule_skip_share == pytest.approx(0.2)
    assert s.rule_skips == {"rule_duplicate": 1, "rule_noop": 1}
    assert (s.policy_skips, s.policy_executes) == (4, 4)
    assert s.price == {"g": 0.001} and s.campaigns == 3


def test_track_s_stop4_fixture():
    """Track S STOP 4: every V* - g in 2.6-4.1 sigma, every E1 skip a rule duplicate; E2 margins as in S0.5
    (about 15 % within 0.5 sigma) — E1 has no decision-relevant states, E2 has."""
    rng = np.random.default_rng(4)
    rows = []
    for node, lo, hi in (("digits_mlp", 2.58, 2.61), ("tabular_mlp", 4.04, 4.06)):
        for k, z in enumerate(rng.uniform(lo, hi, 300)):
            rows.append(_r(node, "E1", v=0.00066 + z * 0.0066, sigma=0.0066, g=0.00066, camp=f"{node}{k % 10}"))
        rows += [_r(node, "E1", rule="rule_duplicate", action="skip", sigma=0.0066) for _ in range(400)]
        for k, z in enumerate(np.concatenate([rng.uniform(-0.5, 0.5, 45), rng.uniform(1.0, 6.0, 255)])):
            rows.append(_r(node, "E2", m=z * 0.0066, sigma=0.0066, camp=f"{node}{k % 10}"))
    out = rel(rows)
    md = RV.markdown(out)
    for node in ("digits_mlp", "tabular_mlp"):
        s = out[node]
        assert s.e1["g"].counts[1.0] == 0 and s.e1["g"].status.startswith("no decision-relevant states")
        assert s.rule_skips == {"rule_duplicate": 400} and s.policy_skips == 0
        assert s.e2.counts[0.5] == 45 and not s.e2.status.startswith(("no decision", "not assessed"))
        line = next(ln for ln in md.splitlines() if ln.startswith(f"| {node} | a2u"))
        assert "E1 vs g: no decision-relevant states" in line and "E2 (m_hat - h): no" not in line
    # mutation: move the E1 rows inside the band and the verdict changes
    moved = [dict(r, state=dict(r["state"], forecasts={"a2u": dict(r["state"]["forecasts"]["a2u"],
             v_star=0.00066 + 0.1 * 0.0066)})) if r["identity"]["epoch"] == "E1" and not r["state"]["rule_forced"]
             else r for r in rows]
    assert not rel(moved)["digits_mlp"].e1["g"].status.startswith("no decision")


def test_not_assessed_is_not_the_gate_outcome():
    s = rel([_r("n", "E1", v=0.031, g=0.001)])["n"]          # 3 sigma from the price
    assert s.e2.status.startswith("not assessed") and s.e1["g"].status.startswith("no decision-relevant")


def test_forks_forced_rows_and_other_epochs():
    root = [_r("n", "E1", v=0.0, g=0.0) for _ in range(2)] + [_r("n", "E1", v=0.05, g=0.0) for _ in range(2)]
    forks = [_r("n", "E1", v=0.0, g=0.0, branch=("f1:skip:r1",), forced=True, action="skip", p_select=0.5),
             _r("n", "E1", v=0.0, g=0.0, branch=("f1:skip:r1",), p_select=0.5),
             _r("n", "E1", v=0.0, g=0.0, branch=("f2:skip:r1",), p_select=0.25)]
    other = [_r("n", "verify", m=0.0), _r("n", "reaudit"), _r("n", "final")]
    s = rel(root + forks + other)["n"]                    # root: forks excluded
    assert s.e1["g"].n_eligible == 4 and s.e1["g"].shares[1.0] == 0.5 and s.n_fork_rows_excluded == 3
    w = rel(root + forks + other, forks="weighted")["n"]  # weighted: the forced arm out, others weight 1/p
    assert w.n_forced_rows == 1 and w.e1["g"].n_eligible == 6
    assert w.e1["g"].shares[1.0] == pytest.approx((2 + 2 + 4) / (4 + 2 + 4))
    assert s.e2.n_eligible == 0                           # verify / reaudit / final rows never count


def test_invalid_and_divergent_e2_discards():
    rows = [_r("n", "E2", m=0.001), _r("n", "E2", m=None, invalid=True, action="discard"),
            _r("n", "E2", m=None, divergent=True, action="discard")]
    s = rel(rows)["n"]
    assert s.e2.n_eligible == 1 and s.n_invalid_discards == 2


def test_keep_threshold_and_raw_statistic():
    rows = [_r("a", "E2", m=-0.004, dhat=0.003), _r("b", "E2", m=0.002, dhat=0.02)]
    assert rel(rows)["a"].e2.counts[0.5] == 1                       # |-0.004| / 0.01 = 0.4
    assert rel(rows, h=-0.004)["a"].e2.counts[0.25] == 1              # h moves the margin
    assert rel(rows, h={"a": 0.002, "b": 0.0})["a"].e2.counts[1.0] == 1
    assert rel(rows, h={"a": 0.002, "b": 0.0})["a"].h == 0.002
    raw = rel(rows, e2_stat="delta_hat")
    assert raw["a"].e2.counts[0.25] == 0 and raw["a"].e2.counts[0.5] == 1 and raw["b"].e2.counts[1.0] == 0


def test_price_sources_precedence_and_errors():
    rows = [_r("a", "E1", v=0.002), _r("b", "E1", v=0.002, g=0.001)]
    with pytest.raises(RV.RelevanceInputError):
        rel(rows)                                                  # node a has no price anywhere
    out = rel(rows, g=0.002)
    assert out["a"].price == {"g": 0.002} and out["b"].price == {"g": 0.002}   # argument wins over forecast
    out = rel(rows, g={"a": 0.0})                                  # mapping misses b: falls back to its forecast
    assert out["a"].price_source["g"] == {"mapping": 1} and out["b"].price_source["g"] == {"forecast": 1}
    env_row = dict(_r("c", "E1", v=0.002), env={"W": 10, "constants": {"g": 0.002}})
    assert rel([env_row])["c"].price_source["g"] == {"env": 1}
    two = rel(rows[1:], thresholds={"price": 0.001, "static": 0.002})["b"]
    assert set(two.e1) == {"price", "static"} and two.e1["static"].counts[0.25] == 1
    assert rel([_r("a", "E1", v=0.002, g=0.001), _r("a", "E1", v=0.002, g=0.002)])["a"].price == {"g": "varies"}


def test_bad_values_and_inputs():
    with pytest.raises(RV.RelevanceInputError, match="finite"):
        rel([_r("a", "E1", v=0.002, g=0.001, sigma=float("nan"))])
    with pytest.raises(RV.RelevanceInputError, match="finite"):
        rel([_r("a", "E1", v=float("inf"), g=0.001)])
    with pytest.raises(RV.RelevanceInputError, match="malformed"):
        rel([{"identity": {"node": "a", "epoch": "E1", "campaign_id": "x", "step_index": 3}, "state": {}}],
            belief="a2u")
    with pytest.raises(RV.RelevanceInputError):
        rel([])
    with pytest.raises(RV.RelevanceInputError):
        rel([_r("a", "E1", v=0.002, g=0.001)], bands=(0.0, 1.0))
    two_beliefs = _r("a", "E1", v=0.002, g=0.001)
    two_beliefs["state"]["forecasts"]["c3"] = {"v_star": 0.001}
    with pytest.raises(RV.RelevanceInputError, match="beliefs"):
        rel([two_beliefs])
    assert rel([two_beliefs], belief="c3", g=0.001)["a"].belief == "c3"


def test_esyn_records_transitions_and_cli(tmp_path, capsys):
    w = X.WORLDS["budget"]
    pol = EP.Static(0.001, 0.0)
    rows = [row for i in range(20) for row in sim.run_campaign(w, pol, i, record=True).rows]
    out = RV.relevance(rows, g=0.001)                                # validate=True by default
    s = out["esyn_budget"]
    assert s.e1["g"].n_eligible > 0 and s.policy_skips > 0 and set(s.rule_skips) == {"rule_noop"}
    assert RV.relevance([S.from_dict(r) for r in rows], g=0.001)["esyn_budget"].to_dict() == s.to_dict()
    bad = json.loads(json.dumps(rows))
    bad[0]["state"]["runs_used"] = 3
    with pytest.raises(RV.RelevanceInputError, match="schema violations"):
        RV.relevance(bad, g=0.001)
    f = tmp_path / "rows.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    md, js = tmp_path / "sub" / "rel.md", tmp_path / "sub" / "rel.json"
    assert RV.main([str(f), "--out", str(md), "--json", str(js), "--g", "0.001", "--threshold", "static=0.002"]) == 0
    text = md.read_text()
    assert "sha256" in text and "schema validation: on" in text and "E1 vs static" in text
    data = json.loads(js.read_text())
    assert data["inputs"][0]["rows"] == len(rows) and data["nodes"]["esyn_budget"]["E1"]["g"]["n_eligible"] > 0
    with pytest.raises(SystemExit):
        RV.main([str(f), "--out", str(md), "--g", "0.001", "--g-json", "x.json"])     # exclusive
    with pytest.raises(SystemExit):
        RV.main([str(f), "--out", str(md), "--bands", "-1,2"])
    broken = tmp_path / "broken.jsonl"
    broken.write_text(json.dumps(rows[0]) + "\n{not json\n")
    assert RV.main([str(broken), "--out", str(md), "--g", "0.001"]) == 2
    assert "broken.jsonl:2" in capsys.readouterr().err
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    assert RV.main([str(empty), "--out", str(md), "--g", "0.001"]) == 2


def test_round2_interval_quantiles_and_clusters():
    # hand-computed: 3 clusters, rows in / out of the band c0 [1, 0], c1 [1, 1], c2 [0, 0, 0, 1]; p = 0.5,
    # cluster residuals 0, 1, -1, se = sqrt(2 * 3/2) / 8 = 0.2165064, n_eff = 0.25 / se^2 = 5.333,
    # t(0.975, 2) = 4.302653, Wilson interval 0.5 -+ 0.440554
    rows = []
    for c, ins in (("c0", (1, 0)), ("c1", (1, 1)), ("c2", (0, 0, 0, 1))):
        rows += [_r("n", "E1", v=0.001 + (0.0 if i else 0.05), g=0.001, camp=c) for i in ins]
    e1 = rel(rows)["n"].e1["g"]
    assert e1.shares[1.0] == 0.5 and e1.se[1.0] == pytest.approx(0.21650635, abs=1e-7)
    assert e1.intervals[1.0] == pytest.approx((0.5 - 0.440554, 0.5 + 0.440554), abs=1e-5)
    assert RV.wilson_cluster(0.3, 0.05, 100, 1) is None                      # one cluster: no interval
    lo, hi = RV.wilson_cluster(0.0, 0.0, 300, 10)                             # boundary: n_eff = k, not degenerate
    assert lo == 0.0 and 0.2 < hi < 0.5
    one = rel([_r("n", "E1", v=0.001, g=0.001), _r("n", "E1", v=0.06, g=0.001)])["n"]
    assert one.e1["g"].intervals[1.0] is None and "[—]" in RV.markdown({"n": one})
    # weighted quantile = numpy inverted-CDF quantile on the integer-weight expansion
    rng = np.random.default_rng(3)
    z, w = rng.normal(size=40), rng.integers(1, 5, 40).astype(float)
    for q in RV.QUANTILES:
        assert RV._wquantile(z, w, q) == pytest.approx(np.quantile(np.repeat(z, w.astype(int)), q,
                                                                   method="inverted_cdf"))
    # cluster key: two policies' campaigns on the same three instances
    shared = [_r("n", "E1", v=0.001 + 0.003 * k, g=0.001, camp=f"{pol}{i}", inst=f"i{i}")
              for pol in ("A", "B") for i in range(3) for k in range(4)]
    assert rel(shared)["n"].e1["g"].clusters == 3 and rel(shared, cluster="campaign_id")["n"].e1["g"].clusters == 6
    assert rel(shared)["n"].cluster == "instance_id"
    no_inst = _r("n", "E1", v=0.001, g=0.001)
    del no_inst["identity"]["instance_id"]
    with pytest.raises(RV.RelevanceInputError, match="instance_id"):
        rel([no_inst])


def test_round2_forks_h_thresholds_and_not_assessed():
    root = [_r("n", "E1", v=0.0, g=0.0)]
    with pytest.raises(RV.RelevanceInputError, match="single-level"):
        rel(root + [_r("n", "E1", v=0.0, g=0.0, branch=("f1:skip:r1", "f2:execute:r1"), p_select=0.5)],
            forks="weighted")
    for bad in (-0.5, 2.0):
        with pytest.raises(RV.RelevanceInputError, match=r"outside \(0, 1\]"):
            rel(root + [_r("n", "E1", v=0.0, g=0.0, branch=("f1:skip:r1",), p_select=bad)], forks="weighted")
    zero = _r("n", "E1", v=0.0, g=0.0, branch=("f1:skip:r1",))
    zero["fork"] = {"p_select": 0.0}
    with pytest.raises(RV.RelevanceInputError, match="outside"):
        rel(root + [zero], forks="weighted")
    e2 = [_r("a", "E2", m=0.001), _r("b", "E1", v=0.0, g=0.0)]
    for h in (float("nan"), float("inf"), {"a": float("nan")}, True):
        with pytest.raises(RV.RelevanceInputError, match="finite"):
            rel(e2, h=h)
    out = rel(e2, h={"a": 0.0})                         # b has no eligible E2 rows: its missing h is harmless
    assert (out["a"].h, out["a"].h_source) == (0.0, "mapping") and (out["b"].h, out["b"].h_source) == (None, "missing")
    assert rel(e2)["a"].h_source == "default" and rel(e2, h=0.0)["a"].h_source == "argument"
    with pytest.raises(RV.RelevanceInputError, match="h mapping"):
        rel(e2, h={"b": 0.0})
    two = [_r("a", "E1", v=0.002, g=0.001), _r("b", "E1", v=0.002, g=0.001)]
    with pytest.raises(RV.RelevanceInputError, match="only g falls back"):
        rel(two, thresholds={"static": {"a": 0.002}})    # an extra threshold never falls back to the price
    with pytest.raises(RV.RelevanceInputError, match="give it once"):
        rel(two, g=0.001, thresholds={"g": 0.002})
    assert set(rel(two, g=0.001, thresholds={"static": 0.002})["a"].e1) == {"g", "static"}
    na = rel([_r("n", "E1", v=0.031, g=0.001)])["n"].to_dict()["E2"]
    assert na["shares"] == {"0.25": None, "0.5": None, "1.0": None} and na["intervals"]["1.0"] is None
    line = next(ln for ln in RV.markdown(rel([_r("n", "E1", v=0.031, g=0.001)])).splitlines() if "E2: m_hat" in ln)
    assert "0.0%" not in line and "| — | — | — |" in line
    bad = _r("n", "E1", v=0.0, g=0.0)
    bad["action"] = "execute"
    with pytest.raises(RV.RelevanceInputError, match="malformed"):
        rel([bad])


def test_round2_cli_errors(tmp_path, capsys):
    w = X.WORLDS["budget"]
    rows = [row for i in range(5) for row in sim.run_campaign(w, EP.Static(0.001, 0.0), i, record=True).rows]
    f = tmp_path / "rows.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    md = tmp_path / "rel.md"
    with pytest.raises(SystemExit):
        RV.main([str(f), "--out", str(md), "--g", "0.001", "--threshold", "g=0.5"])
    hj = tmp_path / "h.json"
    hj.write_text('{"esyn_budget": NaN}')
    assert RV.main([str(f), "--out", str(md), "--g", "0.001", "--h-json", str(hj)]) == 2 and not md.exists()
    assert RV.main([str(f), "--out", str(md), "--g", "0.001", "--h", "nan", "--json", str(tmp_path / "x.json")]) == 2
    assert not md.exists()
    gj = tmp_path / "g.json"
    gj.write_text("{oops")
    assert RV.main([str(f), "--out", str(md), "--g-json", str(gj)]) == 2
    assert "--g-json" in capsys.readouterr().err
    binary = tmp_path / "bin.jsonl"
    binary.write_bytes(b"\xff\xfe\x00garbage")
    assert RV.main([str(binary), "--out", str(md), "--g", "0.001"]) == 2
    assert "not UTF-8" in capsys.readouterr().err
    assert RV.main([str(f), "--out", str(tmp_path), "--g", "0.001"]) == 2      # --out names a directory
    assert RV.main([str(f), "--out", str(md), "--g", "0.001", "--cluster", "campaign_id"]) == 0
    assert "clustered by `campaign_id`" in md.read_text()
