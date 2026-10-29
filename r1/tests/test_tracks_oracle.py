"""Track S oracle simulator: exact agreement with the full pipeline on synthetic nodes; speed.

ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import time

import pytest

from r1.tracks import collect as C
from r1.tracks import oracle as O
from r1.tracks.synthetic import synthetic_node

CASES = [
    ("synthetic_P0", 6, {"sigma_audit": 0.001}),
    ("synthetic_P0", 6, {"variant": "concentrated"}),
    ("synthetic_P1", 8, {}),
    ("synthetic_P1", 8, {"variant": "concentrated", "kappa": 0.0}),
    ("synthetic_P2p", 10, {"variant": "concentrated"}),
    ("synthetic_P2m", 10, {}),
    ("synthetic_N0", 12, {"variant": "concentrated"}),
]


@pytest.mark.parametrize("node_name,W,params", CASES)
def test_oracle_reproduces_the_pipeline_exactly(tmp_path, node_name, W, params):
    import json
    sigma = synthetic_node(node_name, params).sigma_node
    g0 = 0.1 * sigma
    pols = ["a2u", f"static:g={0.3 * sigma:.6g},e2off={0.25 * sigma:.6g}", "static:g=0,e2off=0",
            f"dynamic:g0={g0:.6g},b_budget={sigma:.6g},b_info=0.5,h0=0,h_budget={-0.5 * sigma:.6g}",
            f"dynamic:g0={g0:.6g},b_budget={sigma:.6g},b_info=0.5,h_budget={0.5 * sigma:.6g},r_bar=0.1,"
            f"tau_bar={0.5 * sigma:.6g}"]
    args = ["--phase", "campaign", "--node", node_name, "--W", str(W), "--llm-cap", "12", "--instances", "3",
            "--out", str(tmp_path / "out"), "--work", str(tmp_path / "work"), "--synthetic-params", json.dumps(params)]
    for pol in pols:
        args += ["--policy", pol]
    assert C.main(args) == 0
    roots = C.read_jsonl(tmp_path / "out" / "roots.jsonl")
    seeds = json.loads((tmp_path / "out" / "manifest.json").read_text())["audit_seeds"]
    node = synthetic_node(node_name, params)
    checked = 0
    for r in roots:
        seed = int(r["instance_id"].rsplit("__s", 1)[1])
        pol = r["policy"]
        ctl = O.controller_for(node, pol, W=W, g0=g0)
        sim = O.simulate(node, ctl, seed, W=W, cap=12, audit_seeds=seeds)
        assert sim["y_terminal"] == r["y_terminal"], (node_name, pol, seed)
        assert sim["runs_used"] == r["runs_used"]
        pipe = [(d["index"], "skip" if d["action"] == "skip" else d["action"]) for d in r["decisions"]
                if (d["epoch"] == "E1" and d["action"] == "skip") or d["epoch"] == "E2"]
        assert [d for d in sim["decisions"] if d[1] != "precondition_failed"] == pipe
        checked += 1
    assert checked == 3 * len(pols)


def test_oracle_is_fast_enough_for_large_replication():
    node = synthetic_node("synthetic_P0")
    ctl = O.controller_for(node, "a2u", W=10)
    t0 = time.perf_counter()
    for i in range(50):
        O.simulate(node, ctl, 36000 + i, W=10, cap=40)
    per = (time.perf_counter() - t0) / 50
    assert per < 0.05  # 10^4 campaigns per member in well under 10 minutes on one core


def test_evaluate_is_paired_and_reports_gains():
    res = O.evaluate("synthetic_P0", ["a2u", "a2u"], n=20, W=8, cap=20)
    assert res["seed_base"] >= O.ORACLE_EVAL_BASE
    assert res["gain_vs_first"]["a2u"]["mean"] == 0.0 and res["n"] == 20
    with pytest.raises(ValueError):
        O.controller_for(synthetic_node("synthetic_P0"), "pi_prime:x.json", W=8)
