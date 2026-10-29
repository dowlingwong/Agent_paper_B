"""Track S end to end, collector -> assemble -> analysis (final review; from /tmp/trackS_e2e/e2e.sh).

CPU only, synthetic world nodes, scripted managers, fixed seeds, small sizes (the declared design is 15 x 20
statics, 4 x 40 members and n = 300; here 15 x STATIC_N, 4 x MEMBER_N and FRESH_N). ENGINEERING_ONLY;
AI-assisted (Claude, 29 Oct 2026).

Pipeline (one call each, as an operator would run them):
  collect tune --tune-grid static            -> analyze select (m*; extension if needed)
  collect tune --tune-grid dynamic           -> analyze select (pi*, matched static)
  collect campaign (pi*, m*, matched static, a2u; exact placebo first; descriptive placebo at rep 1)
  collect assemble -> analyze analyze
P2+ concentrated (planted keep feedback) must give route A with pi* = keep+; N0 must give "no gain found".
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from r1.tracks import analyze as A
from r1.tracks import collect as C

SIGMA = 0.0066
STATIC_N, MEMBER_N, FRESH_N = 8, 16, 40
EXACT_N, DESC_N = 10, 15


def _collect(*args: str) -> None:
    assert C.main(list(args)) == 0


def _predeclaration(path: Path, node: str) -> Path:
    path.write_text(json.dumps({
        "schema": A.PREDECLARATION_SCHEMA, "primary_nodes": [node], "fallback_active": True, "bootstrap_B": 20,
        "winners_curse_splits": 20, "tuning": {"procedure": "argmax", "n_dev": MEMBER_N},
        "nodes": {node: {"role": "primary", "sigma_node": SIGMA, "delta_Y": 0.0033, "sigma_cmp_vary": SIGMA,
                         "g_declared": 0.1 * SIGMA, "sizing": {"sigma_D_ucl_s05b": 0.0093, "n": FRESH_N}}}}))
    return path


def _select(pd: Path, node: str, node_dir: Path) -> dict:
    sel = A.public(A.selection_report(A.load_roots(node_dir / "dev_roots.jsonl"),
                                      A.parse_predeclaration(json.loads(pd.read_text())),
                                      A.parse_predeclaration(json.loads(pd.read_text())).nodes[node]))
    return sel


def run_e2e(tmp: Path, node: str, W: int, params: dict, cap: int = 40) -> dict:
    common = ["--node", node, "--W", str(W), "--llm-cap", str(cap), "--synthetic-params", json.dumps(params),
              "--host-label", "ci", "--label", "FIXTURE"]
    pd = _predeclaration(tmp / "pd.json", node)
    nd = tmp / "node"
    dev = [tmp / "static"]
    _collect("--phase", "tune", "--tune-grid", "static", "--sigma-cmp-vary", str(SIGMA), "--instances", str(STATIC_N),
             "--out", str(dev[0]), "--work", str(tmp / "w"), *common)
    C.assemble(node, nd, dev=dev)
    sel = _select(pd, node, nd)
    if sel["status"] == "extension_needed":
        dev.append(tmp / "ext")
        _collect("--phase", "tune", "--tune-grid", "static", "--tune-g-extension", "--sigma-cmp-vary", str(SIGMA),
                 "--instances", str(STATIC_N), "--out", str(dev[-1]), "--work", str(tmp / "w"), *common)
        C.assemble(node, nd, dev=dev)
        sel = _select(pd, node, nd)
    m_star = sel["m_star"]
    static_roots = tmp / "static_roots.jsonl"
    static_roots.write_text((nd / "dev_roots.jsonl").read_text())
    dev.append(tmp / "members")
    _collect("--phase", "tune", "--tune-grid", "dynamic", "--sigma-cmp-vary", str(SIGMA), "--m-star", m_star,
             "--centres-from", str(static_roots), "--instances", str(MEMBER_N), "--out", str(dev[-1]),
             "--work", str(tmp / "w"), *common)
    C.assemble(node, nd, dev=dev)
    sel = _select(pd, node, nd)
    assert sel["status"] == "ok"
    pols = list(dict.fromkeys([sel["pi_star"], m_star, sel["matched_static"]["policy"], "a2u"]))
    camp = tmp / "campaign"
    _collect("--phase", "campaign", *sum((["--policy", p] for p in pols), []), "--instances", str(FRESH_N),
             "--placebo-policy", m_star, "--exact-placebo-n", str(EXACT_N), "--descriptive-placebo-n", str(DESC_N),
             "--out", str(camp), "--work", str(tmp / "w"), *common)
    rep = C.assemble(node, nd, dev=dev, campaign=[camp])
    ctl = {"label": "FIXTURE", "nodes": {node: {"n": FRESH_N, "N0": {"R": 200, "k_A": 2},
                                               "P2+": {"diffuse": {"calibrated": False},
                                                       "concentrated": {"R": 200, "k_A": 172, "target_gain": 0.0033,
                                                                        "achieved_oracle_gain": 0.0033,
                                                                        "p_correct_selection": 0.9}},
                                               "P1": {"diffuse": {"calibrated": False}}}}}
    res = A.run_analysis({node: nd}, A.parse_predeclaration(json.loads(pd.read_text())), controls=ctl)
    return {"result": res, "selection": sel, "assemble": rep, "campaign_dir": camp}


def _check_common(out: dict, node: str) -> dict:
    res = out["result"]
    c = res["nodes"][node]["campaign"]
    assert c["placebo_exact"]["status"] == "pass" and c["placebo_exact"]["n_groups"] == EXACT_N
    assert c["placebo_descriptive"]["status"] == "pass" and c["placebo_descriptive"]["n"] == DESC_N
    assert c["test"]["n"] == FRESH_N and c["rep"] == 0                         # primary repetition only
    assert c["label"] == "FIXTURE" and c["dev_label"] == "FIXTURE"
    assert c["flip_S3e"]["n"] > 0                                              # on fresh S3e states
    assert isinstance(c["m_star_vs_a2u"], dict) and c["m_star_vs_a2u"]["a2u_policy"] == "a2u"
    assert c["sizing"]["n_run_target"] == FRESH_N and c["sizing"]["n_fixed"]
    # The exact placebo ran first in the campaign phase.
    roots = C.read_jsonl(out["campaign_dir"] / "roots.jsonl")
    head = [(r["policy"], r["rep"], r["root_id"].endswith("_dup")) for r in roots[:2 * EXACT_N]]
    assert all(p == out["selection"]["m_star"] and rp == 0 for p, rp, _ in head)
    assert sum(d for *_, d in head) == EXACT_N
    assert set(out["assemble"]["outputs"]) == {"dev_roots.jsonl", "campaign_roots.jsonl"}
    return c


def test_e2e_p2_plus_concentrated_gives_route_A(tmp_path):
    node = "synthetic_P2p"
    out = run_e2e(tmp_path, node, 10, {"variant": "concentrated", "strength": 0.03})
    c = _check_common(out, node)
    assert out["selection"]["pi_star_channel"] == "keep+"
    assert out["result"]["decision"]["route"] == "A", (c["test"], out["result"]["decision"].get("warnings"))


def test_e2e_n0_gives_no_gain_found(tmp_path):
    node = "synthetic_N0"
    out = run_e2e(tmp_path, node, 20, {}, cap=20)  # N0 runs at the non-binding W = cap
    _check_common(out, node)
    assert out["result"]["decision"]["route"] == "no gain found"
