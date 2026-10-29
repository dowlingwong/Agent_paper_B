"""Track S rev. 7: the collector's synthetic worlds and policy strings agree with the analysis branch.

ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026). The analysis modules are this repository's
``r1/tracks/analyze.py`` and ``simulate_controls.py`` (merged), so the round trip also checks the schema the
collector writes.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from r1.tracks import collect as C
from r1.tracks import oracle as O
from r1.tracks import worlds as WD
from r1.tracks.synthetic import synthetic_node

WS = 20261029  # world seed (the WorldNode default)


@pytest.fixture(scope="module")
def AS():
    """The in-repo analysis modules (final review MINOR 5: no outside path, no silent skip)."""
    from r1.tracks import analyze, simulate_controls
    return analyze, simulate_controls


# ---------------------------------------------------------------------------- policy strings
def test_policy_strings_and_tuning_declaration_match_the_analysis(AS):
    A, _ = AS
    sigma = 0.0066
    fam = A.FamilyDecl()
    assert C.static_grid(sigma) == fam.static_configs(sigma) and len(C.static_grid(sigma)) == 15
    assert C.static_grid(sigma, extend=True) == fam.static_configs(sigma, extended=True)
    m_star = fam.static_configs(sigma)[7]
    centres = {"r1bar": 0.0312, "taubar": 0.00451, "r2bar": -0.0125}
    assert C.member_policies(m_star, sigma, centres) == fam.members(m_star, sigma, centres)
    for s in ["static:0,0", "static:0.00066,-0.00165", "dynamic:0.00066,0.0066,0,0,0",
              "dynamic:0.00033,0,0.5,0.00165,0,0.0312,0.00451,-0.0125"]:
        assert C.canonical_policy(s) == A.policy_string(*A.parse_policy(s))
        assert C.as_dynamic(s) == A.as_dynamic(s)
    assert C.canonical_policy("static:6.6e-4,0") == "static:0.00066,0"
    for bad in ("static:g=0,e2off=0", "matched_static:0,0", "dynamic:1,2,3"):
        with pytest.raises(ValueError):
            C.parse_policy(bad)
    decs = [{"epoch": "E1", "eligible": True, "r": 0.1, "tau_pred": 0.004},
            {"epoch": "E1", "eligible": True, "r": -0.2, "tau_pred": 0.006},
            {"epoch": "E1", "eligible": False, "r": 0.9, "tau_pred": 9.0},
            {"epoch": "E2", "eligible": True, "r": 0.05}]
    assert C.decision_centres(decs) == A.decision_centres(decs)


# ---------------------------------------------------------------------------- world mechanism
def _variants():
    out = [("N0", None, 0.0), ("P1", None, 8.0)]
    return out + [(k, v, 0.01) for (k, v) in WD.VARIANTS]


def test_world_components_match_the_simulator(AS):
    _, S = AS
    assert set(WD.VARIANTS) == set(S.VARIANTS)
    for kind, variant, strength in _variants():
        mine, theirs = WD.make_world(kind, strength, variant), S.make_world(kind, strength, variant)
        assert mine.to_dict() == dataclasses.asdict(theirs), (kind, variant)
        rg_m, rg_s = WD.Regime(llm_cap=40, p_rule=0.55), S.Regime(W=10, llm_cap=40, p_rule=0.55)
        for inst in (0, 7, 32001):
            assert np.array_equal(WD.theta_table(mine, rg_m, WS, inst), S.theta_table(theirs, rg_s, WS, inst))
        for bf in (0.0, 0.2, 0.5, 0.9):
            sim = S.Sim(theirs, rg_s, WS)
            assert WD.fb_scale(mine, bf) == sim.fb_scale(bf)
    a, b = WD.Stream([1, 2, 3], 40), S.Stream(np.random.default_rng([1, 2, 3]), 40)
    for f in ("u_rule", "u_kind", "lag", "eta", "eps", "z_size"):
        assert np.array_equal(getattr(a, f), getattr(b, f))
    for args in ((0.001, 2e-5, 0.0066), (-0.003, 1e-5, 0.0005), (0.0, 4e-6, 0.05)):
        assert WD.v_star(*args) == S.v_star(*args)
        # the controller's index (r1.c3.rules) is the same quantity
        from r1.c3 import rules
        assert float(rules.proposal_value(0.0, args[0], np.sqrt(args[1]), args[2])) == pytest.approx(
            S.v_star(*args), rel=1e-9, abs=1e-15)


def _qualifying(world, rg, n, start=0):
    """Instances whose simulator stream has a non-rule trial 1 (where "trial 1 is executed and kept" holds in
    both; see worlds.proposal_sequence)."""
    out, inst = [], start
    while len(out) < n:
        tab = WD.theta_table(world, rg, WS, inst)
        if WD.Stream([WS, inst, 7000, 0], rg.llm_cap).u_rule[1] >= tab[-2]:
            out.append(inst)
        inst += 1
    return out


NODE_OF = {"N0": "synthetic_N0", "P0": "synthetic_P0", "P1": "synthetic_P1", "P2+": "synthetic_P2p",
           "P2-": "synthetic_P2m"}
WORLD_CASES = [("N0", None, 0.0, 40), ("P2+", "diffuse", 0.012, 10), ("P2+", "concentrated", 0.012, 10),
               ("P1", "diffuse", 8.0, 10), ("P0", "concentrated", 0.004, 10), ("P2-", "diffuse", 0.008, 10)]


def _sim_decisions(dec):
    out = []
    for d in dec:
        if d["epoch"] == "E1" and d["action"] == "skip":
            out.append((d["index"], "skip"))
        elif d["epoch"] == "E2":
            out.append((d["index"], d["action"]))
    return out


@pytest.mark.parametrize("kind,variant,strength,W", WORLD_CASES)
def test_oracle_agrees_with_the_analysis_simulator(AS, kind, variant, strength, W):
    """Same world, instance and stream: the oracle (= the pipeline, test_tracks_oracle) and the analysis
    simulator give the same terminal value and the same decisions under statics and centred members."""
    A, S = AS
    cap, sigma = 40, 0.0066
    theirs = S.make_world(kind, strength, variant)
    rg_s = S.Regime(W=W, llm_cap=cap, p_rule=0.55)
    sim = S.Sim(theirs, rg_s, WS)
    params = {"strength": strength, **({"variant": variant} if variant else {})}
    node = synthetic_node(NODE_OF[kind], params).bind(W=W, llm_cap=cap)
    m_star = "static:0.00066,0.00165"
    pols = ["static:0,0", m_star, "static:0.00264,-0.00165"] + \
        list(C.member_policies(m_star, sigma, {"r1bar": 0.05, "taubar": 0.005, "r2bar": 0.02}).values())
    insts = _qualifying(WD.make_world(kind, strength, variant), WD.Regime(llm_cap=cap), 12)
    for pol in pols:
        ctl = O.controller_for(node, pol, W=W)
        for inst in insts:
            dec: list = []
            y_s = sim.run_campaign(S.theta_table(theirs, rg_s, WS, inst), S.ThresholdPolicy(pol), [WS, inst, 7000, 0],
                                   None, noiseless=True, decisions=dec)
            mine = O.simulate(node, ctl, inst, W=W, cap=cap)
            assert mine["y_true_terminal"] == pytest.approx(y_s, abs=1e-12), (pol, inst)
            got = [d for d in mine["decisions"] if d[0] >= 2 and d[1] != "precondition_failed"]
            assert got == _sim_decisions(dec), (pol, inst)


def test_collector_roots_round_trip_through_the_analysis_loader(AS, tmp_path):
    """Review request (rev. 7.1): RootRecord policy / rep / llm_seed_base and per-decision epoch, action,
    index_value, eligible, r, tau_pred; loaded by ``analyze.load_roots``; ``analyze.threshold_act`` reproduces
    every recorded eligible action; r and tau_pred equal the simulator's at the same state."""
    A, S = AS
    W, cap, sigma = 10, 40, 0.0066
    world = WD.make_world("P2+", 0.012, "diffuse")
    lo = C.INSTANCE_SEED_BLOCKS["campaign"][0]
    insts = _qualifying(world, WD.Regime(llm_cap=cap), 40, start=lo)
    base = next(i for i in insts if i + 1 in insts)
    member = C.member_policies("static:0.00066,0.00165", sigma, {"r1bar": 0.05, "taubar": 0.005, "r2bar": 0.02})
    pols = ["static:0.00066,0.00165", member["budget×1"], member["keep+×0.5"], member["info×0.5"]]
    args = ["--phase", "campaign", "--node", "synthetic_P2p", "--W", str(W), "--llm-cap", str(cap),
            "--instances", "2", "--seed-base", str(base), "--rep", "0", "--rep", "1",
            "--out", str(tmp_path / "out"), "--work", str(tmp_path / "work"),
            "--synthetic-params", json.dumps({"strength": 0.012, "variant": "diffuse"})]
    for p in pols:
        args += ["--policy", p]
    assert C.main(args) == 0
    roots = A.load_roots(tmp_path / "out" / "roots.jsonl")
    assert len(roots) == 2 * len(pols) * 2
    assert {A.policy_of(r) for r in roots} == set(pols)
    by_key: dict = {}
    for r in roots:
        assert r.rep in (0, 1) and isinstance(r.llm_seed_base, int)
        by_key.setdefault((r.instance_id, r.rep), set()).add(r.llm_seed_base)
        elig = [d for d in r.decisions if d["eligible"]]
        assert elig, r.root_id
        for d in elig:
            assert {"epoch", "action", "index_value", "eligible", "r", "tau_pred"} <= set(d)
            acted = d["action"] in ("execute", "keep")
            assert A.threshold_act(r.policy, d, d["epoch"]) == acted, (r.policy, d)
    # one seed base per (instance, repetition), shared by all policies; different across repetitions
    assert all(len(v) == 1 for v in by_key.values())
    assert len({next(iter(v)) for v in by_key.values()}) == len(by_key)
    # r / tau_pred / index values equal the simulator's (repetition 0)
    sim = S.Sim(S.make_world("P2+", 0.012, "diffuse"), S.Regime(W=W, llm_cap=cap, p_rule=0.55), WS)
    for r in roots:
        if r.rep != 0:
            continue
        inst = int(r.instance_id.rsplit("__s", 1)[1])
        dec: list = []
        sim.run_campaign(S.theta_table(sim.w, sim.r, WS, inst), S.ThresholdPolicy(r.policy), [WS, inst, 7000, 0],
                         None, noiseless=True, decisions=dec)
        mine = [(d["index"], d["epoch"], d["action"]) for d in r.decisions if d["eligible"]]
        assert mine == [(d["index"], d["epoch"], d["action"]) for d in dec], r.policy
        for a, b in zip([d for d in r.decisions if d["eligible"]], dec):
            assert a["r"] == pytest.approx(b["r"], abs=1e-12)
            assert a["index_value"] == pytest.approx(b["index_value"], rel=1e-9, abs=1e-15)
            if a["epoch"] == "E1":
                assert a["tau_pred"] == pytest.approx(b["tau_pred"], rel=1e-9)


def test_world_forks_continue_from_the_root_plan_and_aa_reproduces(tmp_path):
    """Leaves of a world node: the continuation manager proposes as the root up to the fork trial (incl. the P1
    follow-up plan) and from its own repetition's stream after it; A/A leaves reproduce the root."""
    node = synthetic_node("synthetic_P1", {"variant": "diffuse", "strength": 8.0}).bind(W=10, llm_cap=20)
    root = node.manager(36000, 0)
    leaf = node.manager(36000, 101, fork_trial=7)
    assert leaf.sequence[:7] == root.sequence[:7] and leaf.sequence != root.sequence
    assert node.manager(36000, 0, fork_trial=7).sequence == root.sequence
    out = tmp_path / "out"
    assert C.main(["--phase", "synthetic", "--node", "synthetic_P1", "--W", "10", "--llm-cap", "20",
                   "--instances", "2", "--forks", "3", "--aa-fraction", "1.0", "--reps", "1",
                   "--root-policy", "static:0.00066,0", "--out", str(out), "--work", str(tmp_path / "work"),
                   "--synthetic-params", json.dumps({"variant": "diffuse", "strength": 8.0})]) == 0
    leaves = C.read_jsonl(out / "leaves.jsonl")
    aa = [l for l in leaves if l["arm"] == "aa"]
    assert aa and all(l["aa_reproduced"] for l in aa)
    assert not (out / "failed_units.jsonl").exists() or not C.read_jsonl(out / "failed_units.jsonl")
