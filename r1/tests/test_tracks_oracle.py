"""Track S oracle simulator: exact agreement with the full pipeline on synthetic nodes; speed.

ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import time

import pytest

from r1.tracks import collect as C
from r1.tracks import oracle as O
from r1.tracks.synthetic import synthetic_node

LL = {"mechanism": "loglinear"}  # the rev.-6 log-linear test nodes (not declared controls)
CASES = [
    ("synthetic_P0", 6, {**LL, "sigma_audit": 0.001}),
    ("synthetic_P0", 6, {**LL, "variant": "concentrated"}),
    ("synthetic_P1", 8, {**LL}),
    ("synthetic_P1", 8, {**LL, "variant": "concentrated", "kappa": 0.0}),
    ("synthetic_P2p", 10, {**LL, "variant": "concentrated"}),
    ("synthetic_P2m", 10, {**LL}),
    ("synthetic_N0", 12, {**LL, "variant": "concentrated"}),
    # rev. 7 worlds (``r1.tracks.worlds``): the calibrated controls and the two non-control worlds
    ("synthetic_N0", 12, {}),
    ("synthetic_P2p", 5, {"variant": "diffuse", "strength": 0.012}),
    ("synthetic_P2p", 5, {"variant": "concentrated", "strength": 0.012}),
    ("synthetic_P1", 5, {"variant": "diffuse", "strength": 8.0}),
    ("synthetic_P0", 5, {"variant": "concentrated", "strength": 0.004}),
    ("synthetic_P2m", 5, {"variant": "diffuse", "strength": 0.008}),
]


@pytest.mark.parametrize("node_name,W,params", CASES)
def test_oracle_reproduces_the_pipeline_exactly(tmp_path, node_name, W, params):
    import json
    sigma = synthetic_node(node_name, params).sigma_node
    g0 = 0.1 * sigma
    f = C.fmt_num
    pols = ["a2u", f"static:{f(0.3 * sigma)},{f(0.25 * sigma)}", "static:0,0",
            f"dynamic:{f(g0)},{f(sigma)},0.5,0,{f(-0.5 * sigma)}",
            f"dynamic:{f(g0)},{f(sigma)},0.5,0,{f(0.5 * sigma)},0.1,{f(0.5 * sigma)},-0.05"]
    args = ["--phase", "campaign", "--node", node_name, "--W", str(W), "--llm-cap", "12", "--instances", "3",
            "--out", str(tmp_path / "out"), "--work", str(tmp_path / "work"), "--synthetic-params", json.dumps(params)]
    for pol in pols:
        args += ["--policy", pol]
    assert C.main(args) == 0
    roots = C.read_jsonl(tmp_path / "out" / "roots.jsonl")
    node = synthetic_node(node_name, params)
    checked = 0
    for r in roots:
        seed = int(r["instance_id"].rsplit("__s", 1)[1])
        pol = r["policy"]
        ctl = O.controller_for(node, pol, W=W, g0=g0)
        sim = O.simulate(node, ctl, seed, W=W, cap=12, audit_seeds=C.instance_audit_seeds("campaign", seed, 5))
        assert sim["y_terminal"] == r["y_terminal"], (node_name, pol, seed)
        assert sim["runs_used"] == r["runs_used"]
        pipe = [(d["index"], "skip" if d["action"] == "skip" else d["action"]) for d in r["decisions"]
                if (d["epoch"] == "E1" and d["action"] == "skip") or (d["epoch"] == "E2" and d["action"] in ("keep", "discard"))]
        assert [d for d in sim["decisions"] if d[1] != "precondition_failed"] == pipe
        checked += 1
    assert checked == 3 * len(pols)


def test_oracle_is_fast_enough_for_large_replication():
    node = synthetic_node("synthetic_P2p", {"strength": 0.01}).bind(W=10, llm_cap=40)
    ctl = O.controller_for(node, "a2u", W=10)
    t0 = time.process_time()  # CPU time: robust to parallel test runs
    for i in range(50):
        O.simulate(node, ctl, 36000 + i, W=10, cap=40)
    per = (time.process_time() - t0) / 50
    assert per < 0.05  # 10^4 campaigns per member in well under 10 minutes on one core


def test_evaluate_is_paired_and_reports_gains():
    res = O.evaluate("synthetic_P0", ["a2u", "a2u"], n=20, W=8, cap=20, params={"strength": 0.004})
    assert res["seed_base"] >= O.ORACLE_EVAL_BASE
    assert res["gain_vs_first"]["a2u"]["mean"] == 0.0 and res["n"] == 20
    with pytest.raises(ValueError):
        O.controller_for(synthetic_node("synthetic_P0"), "pi_prime:x.json", W=8)
