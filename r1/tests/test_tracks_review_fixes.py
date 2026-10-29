"""Track S collector review (COLLECTOR_REVIEW_20261029): one test group per finding.

CPU only, synthetic nodes and scripted managers. ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from r1.tracks import a2u
from r1.tracks import collect as C
from r1.tracks import oracle as O
from r1.tracks.probes import s1_factorial as F
from r1.tracks.schema import leaf_from_dict, root_from_dict
from r1.tracks.synthetic import synthetic_node


LL = {"mechanism": "loglinear"}


def _run(tmp: Path, *extra: str, node: str = "synthetic_N0", phase: str = "synthetic", out: str = "out",
         W: str | None = "10", cap: str = "10") -> Path:
    args = ["--phase", phase, "--node", node, "--llm-cap", cap, "--out", str(tmp / out), "--work", str(tmp / "work"),
            "--label", "FIXTURE", "--host-label", "ci", "--gpu", "none", *extra]
    if W is not None and phase != "S0.4" and "--W" not in extra:
        args += ["--W", W]
    assert C.main(_legacy(args)) == 0
    return tmp / out


def _legacy(args: list[str]) -> list[str]:
    """These tests exercise the collector on the rev.-6 log-linear synthetic nodes (``mechanism=loglinear``);
    the rev.-7 world nodes are tested in test_tracks_worlds.py and test_tracks_oracle.py."""
    if not args[args.index("--node") + 1].startswith("synthetic_"):
        return args
    if "--synthetic-params" in args:
        i = args.index("--synthetic-params") + 1
        params = json.loads(args[i])
        params.setdefault("mechanism", "loglinear")
        return args[:i] + [json.dumps(params)] + args[i + 1:]
    return args + ["--synthetic-params", json.dumps({"mechanism": "loglinear"})]


def _ledger(work: Path, root_id: str) -> list[str]:
    out = []
    for r in C.read_jsonl(work / "roots" / root_id / "root_trials.jsonl"):
        for key in ("timestamp_start", "timestamp_end", "wall_clock_seconds"):
            r.pop(key)
        out.append(json.dumps(r, sort_keys=True))
    return out


# ---------------------------------------------------------------------------
# B1: phase-keyed audit-seed blocks
# ---------------------------------------------------------------------------

def test_b1_audit_blocks_are_disjoint_and_phase_keyed():
    blocks = C.AUDIT_SEED_BLOCKS
    names = list(blocks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not set(blocks[a]) & set(blocks[b]), (a, b)
    # Disjoint from every instance block, the S1.1 block, the selection seed and the oracle blocks.
    all_audit = set().union(*map(set, blocks.values()))
    for lo, hi in C.INSTANCE_SEED_BLOCKS.values():
        assert not all_audit & set(range(lo, hi))
    assert not all_audit & set(F.S11_SEEDS) and C.SELECTION_SEED not in all_audit
    assert min(O.ORACLE_SELECT_BASE, O.ORACLE_EVAL_BASE) > max(all_audit) and O.ORACLE_EVAL_BASE >= \
        O.ORACLE_SELECT_BASE + O.ORACLE_BLOCK_SIZE
    # The S3e block is used by no other phase; S0.7 tuning and S3e never share seeds.
    assert list(C.PHASE_AUDIT_BLOCK.values()).count("campaign") == 1
    assert C.audit_rule("S0.5b", 5)["block"] == "S0.5"
    # Per-instance seeds (final review MAJOR 1): inside the phase's block, disjoint across instances and phases.
    for phase, (lo, hi) in C.INSTANCE_SEED_BLOCKS.items():
        block = C.PHASE_AUDIT_BLOCK[phase]
        per = [C.instance_audit_seeds(phase, s, C.AUDIT_STRIDE) for s in (lo, lo + 1, hi - 1)]
        assert all(set(x) <= set(C.AUDIT_SEED_BLOCKS[block]) for x in per)
        assert not set(per[0]) & set(per[1]) and not set(per[1]) & set(per[2])
    assert C.instance_audit_seeds("campaign", 32000, 5)[:3] == C.instance_audit_seeds("campaign", 32000, 3)
    with pytest.raises(ValueError):
        C.instance_audit_seeds("campaign", 31999, 5)  # an S3 instance seed is not a campaign instance
    instance_ranges = [range(*b) for b in C.INSTANCE_SEED_BLOCKS.values()]
    for i, a in enumerate(instance_ranges):
        for b in instance_ranges[i + 1:]:
            assert not set(a) & set(b)


def test_b1_manifests_and_records_carry_their_own_block(tmp_path):
    tune = _run(tmp_path, "--instances", "1", "--policy", "a2u", phase="tune", out="tune")
    camp = _run(tmp_path, "--instances", "1", "--policy", "a2u", phase="campaign", out="camp")
    mt, mc = (json.loads((d / "manifest.json").read_text()) for d in (tune, camp))
    assert (mt["audit_block"], mc["audit_block"]) == ("tune", "campaign")
    assert (mt["audit_rule"]["base"], mc["audit_rule"]["base"]) == (C.AUDIT_SEED_BASES["tune"],
                                                                     C.AUDIT_SEED_BASES["campaign"])
    assert mc["seed_blocks"]["audits"]["campaign"] == [500000, 599999]
    rows = C.read_jsonl(tmp_path / "camp" / "audit_runs.jsonl")
    assert rows and {r["seed"] for r in rows} <= set(C.instance_audit_seeds("campaign", mc["seed_base"], 5))


# ---------------------------------------------------------------------------
# M1: roots and continuations under m*; E2 band centred at h
# ---------------------------------------------------------------------------

def test_m1_root_policy_runs_roots_rebuilds_and_leaves(tmp_path):
    s = synthetic_node("synthetic_P2p", LL).sigma_node
    h = 0.5 * s
    m_star = C.policy_string("static", (0.0, h))  # executes every non-rule proposal, keeps iff m_hat > h
    h = C.as_dynamic(m_star)[3]
    out = _run(tmp_path, "--instances", "2", "--forks", "6", "--root-policy", m_star, "--near-band", str(0.3 * s),
               "--p-near", "1.0", "--aa-fraction", "1.0", node="synthetic_P2p")
    roots = [root_from_dict(r) for r in C.read_jsonl(out / "roots.jsonl")]
    assert {r.policy for r in roots} == {m_star}
    leaves = [leaf_from_dict(l) for l in C.read_jsonl(out / "leaves.jsonl")]
    assert leaves and {l.policy for l in leaves} == {m_star}
    assert all(l.aa_reproduced for l in leaves if l.arm == "aa")  # continuations rebuilt under m*
    e2 = [d for r in roots for d in r.decisions if d["epoch"] == "E2" and d["eligible"]]
    assert e2
    for d in e2:  # the margin is m_hat - h, not m_hat
        assert d["margin"] == pytest.approx(d["index_value"] - h, abs=1e-12)
    for f in C.read_jsonl(out / "forks.jsonl"):
        assert f["near"] == (abs(f["margin"]) <= 0.3 * s)


# ---------------------------------------------------------------------------
# M2: seed key = (node, instance seed); S0.5 policy and repetition pairs
# ---------------------------------------------------------------------------

def test_m2_seed_key_and_s05_policy_rep_pairs(tmp_path):
    node = synthetic_node("synthetic_P2p", LL)
    g0 = 0.1 * node.sigma_node
    same_rule = C.policy_string("static", (g0, 0.0))  # the same rule as the primary a2u root (g0 to 9 d.p.)
    out = _run(tmp_path, "--instances", "2", "--forks", "0", "--policy", same_rule, "--policy", "a2u",
               "--rep", "0", "--rep", "1", node="synthetic_P2p", phase="S0.5", W="20", cap="12")
    roots = C.read_jsonl(out / "roots.jsonl")
    by_inst: dict[str, list] = {}
    for r in roots:
        by_inst.setdefault(r["instance_id"], []).append(r)
    for inst, rs in by_inst.items():
        # primary (a2u, rep 0) + same_rule x {0, 1} + a2u x {1}  (a2u x 0 is the primary itself)
        assert Counter((r["policy"], r["rep"]) for r in rs) == Counter(
            {("a2u", 0): 1, (same_rule, 0): 1, (same_rule, 1): 1, ("a2u", 1): 1})
        seed = int(inst.rsplit("__s", 1)[1])
        cid = C.seed_key_for("synthetic_P2p", seed)
        for r in rs:
            first = json.loads(_ledger(tmp_path / "work", r["root_id"])[0])
            assert first["campaign_id"] == cid  # no phase or policy tag in the seed key
        prim = [r for r in rs if r["policy"] == "a2u" and r["rep"] == 0][0]
        twin = [r for r in rs if r["policy"] == same_rule and r["rep"] == 0][0]
        assert _ledger(tmp_path / "work", prim["root_id"]) == _ledger(tmp_path / "work", twin["root_id"])
    assert "tracks_synthetic_P2p__s30500" == C.seed_key_for("synthetic_P2p", 30500)


# ---------------------------------------------------------------------------
# M5: resume — dedupe, commit marker, retries, truncated lines
# ---------------------------------------------------------------------------

def _plan(out: Path, work: Path):
    manifest = json.loads((out / "manifest.json").read_text())
    adapter = C.make_adapter(manifest["node"], {}, manifest.get("synthetic_params"))
    run = C.Run(C.parse_args(["--phase", manifest["phase"], "--node", manifest["node"], "--out", str(out)]), adapter,
                out, work, manifest, None, "", 0.0, 0.0, 0.0, None, None, 0.0)
    return C.plan(run)


def test_m5_dedupe_and_root_commit_marker(tmp_path):
    args = ("--instances", "2", "--forks", "3", "--aa-fraction", "0")
    out = _run(tmp_path, *args)
    forks = (out / "forks.jsonl").read_text()
    leaves_n = len(C.read_jsonl(out / "leaves.jsonl"))
    # A crash between the fork appends and the root line: duplicated forks, missing root line.
    (out / "forks.jsonl").write_text(forks + forks)
    roots = (out / "roots.jsonl").read_text().splitlines()
    (out / "roots.jsonl").write_text("\n".join(roots[:-1]) + "\n")
    p = _plan(out, tmp_path / "work")
    assert p["forks_known"] == len(set(f["fork_id"] for f in C.read_jsonl(out / "forks.jsonl")))
    assert len(p["roots_todo"]) == 1 and p["leaves_todo"] == []
    _run(tmp_path, *args)
    assert len(C.read_jsonl(out / "roots.jsonl")) == 2
    assert len(C.read_jsonl(out / "leaves.jsonl")) == leaves_n  # no leaf scheduled twice
    ids = [f["fork_id"] for f in C.read_jsonl(out / "forks.jsonl")]
    assert len(ids) == 2 * len(forks.splitlines())  # the duplicates written above stay; nothing new appended
    assert len(set(ids)) == len(forks.splitlines())


def test_m5_failed_units_are_retried_up_to_the_limit(tmp_path, monkeypatch):
    real = C.run_leaf
    calls = {"n": 0}

    def flaky(run, fork, arm, rep, root_rows):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("llama-server outage")
        return real(run, fork, arm, rep, root_rows)

    monkeypatch.setattr(C, "run_leaf", flaky)
    args = ("--instances", "1", "--forks", "2", "--aa-fraction", "0")
    out = _run(tmp_path, *args)
    failed = C.read_jsonl(out / "failed_units.jsonl")
    assert len(failed) == 1 and failed[0]["error_message"] == "llama-server outage"
    unit = failed[0]["unit"]
    done_units = {C.leaf_unit(l["fork_id"], l["arm"], l["rep"]) for l in C.read_jsonl(out / "leaves.jsonl")}
    assert unit not in done_units  # a failure is never recorded as done
    _run(tmp_path, *args)  # resume retries it
    done_units = {C.leaf_unit(l["fork_id"], l["arm"], l["rep"]) for l in C.read_jsonl(out / "leaves.jsonl")}
    assert unit in done_units


def test_m5_retry_limit_and_exhausted_units(tmp_path, monkeypatch):
    def broken(run, fork, arm, rep, root_rows):
        raise RuntimeError("always")

    monkeypatch.setattr(C, "run_leaf", broken)
    args = ("--instances", "1", "--forks", "1", "--aa-fraction", "0", "--max-retries", "1")
    out = _run(tmp_path, *args)
    n_units = len(C.read_jsonl(out / "failed_units.jsonl"))
    assert n_units >= 1 and not C.read_jsonl(out / "leaves.jsonl")
    _run(tmp_path, *args)  # second attempt (the declared retry)
    assert len(C.read_jsonl(out / "failed_units.jsonl")) == 2 * n_units
    _run(tmp_path, *args)  # exhausted: not attempted again
    assert len(C.read_jsonl(out / "failed_units.jsonl")) == 2 * n_units
    assert len(_plan(out, tmp_path / "work")["exhausted"]) == n_units


def test_m5_truncated_last_line_is_tolerated_and_repaired(tmp_path):
    path = tmp_path / "x.jsonl"
    C.append_jsonl(path, {"a": 1})
    with open(path, "a") as fh:
        fh.write('{"a": 2, "b"')  # a crash mid-write
    assert C.read_jsonl(path) == [{"a": 1}]
    C.append_jsonl(path, {"a": 3})
    assert C.read_jsonl(path) == [{"a": 1}, {"a": 3}]
    assert path.read_text().endswith("\n")
    path.write_text('{"a": 1}\n{"broken\n{"a": 3}\n')
    with pytest.raises(json.JSONDecodeError):
        C.read_jsonl(path)  # corruption before the last line is an error, never skipped


# ---------------------------------------------------------------------------
# M6: S0.5 calibration audits
# ---------------------------------------------------------------------------

def test_m6_s05_calibration_rows(tmp_path):
    out = _run(tmp_path, "--instances", "2", "--forks", "0", node="synthetic_P0", phase="S0.5", W="20", cap="12",
               out="s05")
    manifest = json.loads((out / "manifest.json").read_text())
    rows = C.read_jsonl(out / "s05_calibration.jsonl")
    assert rows and manifest["audit_block"] == "S0.5"
    for r in rows:
        seed = int(r["instance"].rsplit("__s", 1)[1])
        assert r["audit_seeds"] == list(C.instance_audit_seeds("S0.5", seed, manifest["K"]))
        assert r["sd_paired"] is not None and r["k"] == manifest["K"]
        assert r["stratum"] == a2u.n_group_stratum(r["n_group"]) and r["level"] == 0.8
        assert r["delta_audit"] is not None and isinstance(r["covered"], bool)
        assert r["lo"] < r["mu"] < r["hi"]
    assert {r["stratum"] for r in rows} >= {"0"}
    ivs = [dict(r) for r in rows if r["root_id"] == rows[0]["root_id"]]
    cov = a2u.coverage(ivs, {r["budget_index"]: r["delta_audit"] for r in ivs})
    assert cov["n"] == len(ivs) and set(cov["by_stratum"]) == {r["stratum"] for r in ivs}
    assert not C.read_jsonl(out / "s04_rows.jsonl")  # the prior's training rows are never the calibration input


# ---------------------------------------------------------------------------
# M4: oracle certification
# ---------------------------------------------------------------------------

def test_m4_oracle_exact_values_and_certification():
    node = synthetic_node("synthetic_N0", LL)
    noisy = synthetic_node("synthetic_N0", {**LL, "sigma_audit": 0.01})
    ctl = O.controller_for(node, "a2u", W=40)
    seeds = range(O.ORACLE_EVAL_BASE, O.ORACLE_EVAL_BASE + 20)
    # Exact expected Y: audit noise does not enter.
    assert np.array_equal(O.exact_values(node, ctl, seeds, W=40, cap=12),
                          O.exact_values(noisy, O.controller_for(noisy, "a2u", W=40), seeds, W=40, cap=12))
    s = node.sigma_node
    statics = [C.policy_string("static", (0.05 * s, 0)), C.policy_string("static", (0.4 * s, 0))]
    res = O.certify("synthetic_N0", statics, [C.policy_string("dynamic", (0.05 * s, s, 0, 0, 0))], delta_Y=0.01,
                    W=40, cap=12, n_select=50, n_pilot=60, n_max=5000, params=LL)
    assert res["best_static"] in statics and res["pass"]
    assert res["selection"]["seeds"][1] <= res["evaluation"]["seeds"][0]  # independent seeds
    g = next(iter(res["gains"].values()))
    assert g["half_width"] <= 0.05 * 0.01
    s0 = synthetic_node("synthetic_P0", LL).sigma_node
    with pytest.raises(O.OracleToleranceError):  # a member that does differ, with a tolerance n_max cannot reach
        O.certify("synthetic_P0", [C.policy_string("static", (0.05 * s0, 0))],
                  [C.policy_string("dynamic", (0.05 * s0, 2 * s0, 0, 0, 0))], delta_Y=1e-6, W=8, cap=12, n_select=10,
                  n_pilot=30, n_max=40, params=LL)


# ---------------------------------------------------------------------------
# M3: synthetic worlds (mechanics now; final parameters from the rev-7 simulation study)
# ---------------------------------------------------------------------------

def test_m3_p0_values_are_observable_and_p2_trigger_varies():
    node = synthetic_node("synthetic_P0", LL)
    prior = node.prior()
    assert len(prior.groups) == 4
    from r1.c3 import rules
    vs = {k: float(rules.proposal_value(0.0, kp.mu0, (kp.tau0 ** 2 + kp.tau_w ** 2) ** 0.5, kp.sigma_cmp))
          for k, kp in prior.groups.items()}
    means = {k: kp.mu0 for k, kp in prior.groups.items()}
    order = sorted(vs, key=means.get)
    assert all(vs[a] < vs[b] for a, b in zip(order, order[1:]))  # V* strictly increases with the group mean
    assert vs[order[-1]] > 10 * vs[order[0]]
    conc = synthetic_node("synthetic_P0", {**LL, "variant": "concentrated"}).prior()
    assert len(conc.groups) == 3
    p2 = synthetic_node("synthetic_P2p", LL)
    triggers = {p2.trigger_trial(s) for s in range(36000, 36040)}
    assert len(triggers) > 3 and min(triggers) >= 2 and max(triggers) <= 12
    assert synthetic_node("synthetic_P2p", {**LL, "trigger_trial": 5}).trigger_trial(1) == 5
    with pytest.raises(ValueError):
        synthetic_node("synthetic_N0", {**LL, "gain": 0.01})


def _best_member(name: str, W: int, params: dict | None = None, cap: int = 20, n_select: int = 120,
                 n_eval: int = 200) -> tuple[str, dict]:
    """Best static on the selection block, then the four fixed rev.-7 members anchored at it (uncentred for the
    log-linear nodes, centred at its decision means for the world nodes) on the evaluation block."""
    params = LL if params is None else params
    node = synthetic_node(name, params)
    s = node.sigma_node
    statics = C.tuning_grid("static", s)
    best = O.certify(name, statics, [], delta_Y=1.0, W=W, cap=cap, n_select=n_select, n_pilot=2, params=params,
                     strict=False)["best_static"]
    centres = None
    if getattr(node, "synthetic_world", False):
        bound = node.bind(W=W, llm_cap=cap)
        ctl = O.controller_for(bound, best, W=W)
        recs = [d for i in range(100) for d in
                O.simulate(bound, ctl, O.ORACLE_SELECT_BASE + n_select + i, W=W, cap=cap)["records"]]
        centres = C.decision_centres(recs)
    members = C.member_policies(best, s, centres)
    res = O.certify(name, [best], list(members.values()), delta_Y=1.0, W=W, cap=cap, n_select=2, n_pilot=n_eval,
                    n_max=n_eval, params=params, strict=False)
    top = res["best_member"]
    channel = next(n for n, m in members.items() if m == top).split("×")[0]
    return channel, res


def test_m3_p0_best_member_is_the_budget_channel():
    channel, res = _best_member("synthetic_P0", W=8, cap=40, n_eval=800)  # W = 8 of 40 proposals: the budget binds
    assert channel == "budget"
    g = res["gains"][res["best_member"]]
    assert g["gain"] > 2 * g["half_width"]


def test_m3_n0_has_no_gain():
    _, res = _best_member("synthetic_N0", W=20)
    for g in res["gains"].values():
        assert abs(g["gain"]) <= max(g["half_width"], 1e-12)


def test_m3_world_p2p_best_member_is_the_keep_channel():
    """Rev. 7 world P2+ (concentrated, strength 0.012: about 1 delta_Y for keep+ in the analysis study): the best
    centred member is keep+, significantly. (The rev.-6 placeholder P1 / P2 xfail tests are superseded by the
    worlds; P1's planted gain is not an info-member gain, analysis notes 5.1, and P2- is not a control.)"""
    channel, res = _best_member("synthetic_P2p", W=10, params={"variant": "concentrated", "strength": 0.012},
                                cap=40, n_select=120, n_eval=300)
    assert channel == "keep+"
    g = res["gains"][res["best_member"]]
    assert g["gain"] > 2 * g["half_width"]


# ---------------------------------------------------------------------------
# Rev-7 support
# ---------------------------------------------------------------------------

def test_rev7_g0_is_execute_all_non_rule(tmp_path):
    params = json.dumps({"mu_step": -0.02, "spread": 0.002})  # strongly negative values: g > 0 would skip
    out = _run(tmp_path, "--instances", "2", "--policy", "static:0,0", "--policy", "static:0.001,0",
               "--synthetic-params", params, phase="campaign", W="40")
    roots = C.read_jsonl(out / "roots.jsonl")
    for r in roots:
        skips = [d for d in r["decisions"] if d["epoch"] == "E1" and d["action"] == "skip"]
        if r["policy"] == "static:0,0":
            assert not skips
        else:
            assert skips


def test_rev7_fixed_members_and_centring():
    """Rev. 7 D2: no magnitude grids; four fixed members, centred (r1bar, taubar at E1, r2bar at E2)."""
    with pytest.raises(ValueError):
        C.tuning_grid("magnitude", 0.002, "static:0.0002,0")
    grid = C.member_policies("static:0.0002,0", 0.002, {"r1bar": 0.2, "taubar": 0.001, "r2bar": 0.1})
    assert grid == {"budget×1": "dynamic:0.0002,0.002,0,0,0,0.2,0.001,0.1",
                    "info×0.5": "dynamic:0.0002,0,0.5,0,0,0.2,0.001,0.1",
                    "keep+×0.5": "dynamic:0.0002,0,0,0,0.001,0.2,0.001,0.1",
                    "keep-×0.5": "dynamic:0.0002,0,0,0,-0.001,0.2,0.001,0.1"}
    assert C.resolve_m_star("0.1,0", 0.002) == "static:0.0002,0"


def test_rev7_tune_accepts_explicit_jobs(tmp_path):
    jobs = tmp_path / "jobs.json"
    jobs.write_text(json.dumps([{"policy": "static:0,0", "instances": [0, 1, 2]},
                                {"policy": "static:1e-3,0", "instances": [1, 2], "rep": 0}]))
    out = _run(tmp_path, "--jobs", str(jobs), phase="tune")
    roots = C.read_jsonl(out / "roots.jsonl")
    # job policies are recorded in the analysis spelling
    assert Counter(r["policy"] for r in roots) == Counter({"static:0,0": 3, "static:0.001,0": 2})
    lo = C.INSTANCE_SEED_BLOCKS["tune"][0]
    assert {r["instance_id"] for r in roots if r["policy"] == "static:0.001,0"} == \
        {f"synthetic_N0__s{lo + k}" for k in (1, 2)}
    with pytest.raises(SystemExit):
        _run(tmp_path, "--jobs", str(jobs), phase="campaign", out="o2")


# ---------------------------------------------------------------------------
# MINOR
# ---------------------------------------------------------------------------

def test_m1_minor_reps_only_on_the_channel_third():
    ordinary = {"epoch": "E1", "selection": {"channel_arms": False}, "aa": False}
    channel = {"epoch": "E1", "selection": {"channel_arms": True}, "aa": False}
    e2 = {"epoch": "E2", "selection": {"channel_arms": False}, "aa": False}
    assert C.leaf_arms(ordinary, 2, 1) == [("skip", 1), ("execute", 1)]
    assert len(C.leaf_arms(channel, 2, 1)) == 8
    assert C.leaf_arms(e2, 2, 1) == [("keep", 1), ("discard", 1)]


def test_m2_minor_aa_mismatch_is_a_stop(tmp_path):
    out = _run(tmp_path, "--instances", "1", "--forks", "2", "--aa-fraction", "1.0")
    manifest = json.loads((out / "manifest.json").read_text())
    adapter = C.make_adapter("synthetic_N0", {}, None)
    prior = adapter.node.prior()
    args = C.parse_args(["--phase", "synthetic", "--node", "synthetic_N0", "--out", str(out)])
    run = C.Run(args, adapter, out, tmp_path / "work", manifest, prior, prior.sha256, prior.sigma_node,
                manifest["g_declared"], manifest["g0"], root_from_dict(C.read_jsonl(out / "roots.jsonl")[0]).provenance,
                C.AuditCache(out / "audit_runs.jsonl", adapter, tmp_path / "work"), 0.0)
    fork = C.read_jsonl(out / "forks.jsonl")[0]
    root_rows = C.read_jsonl(tmp_path / "work" / "roots" / fork["root_id"] / "root_trials.jsonl")
    tampered = [dict(r, proposal_summary="not the root") if r["budget_index"] > fork["index"] else r for r in root_rows]
    with pytest.raises(C.Stop, match="A/A"):
        C.run_leaf(run, fork, "aa", 0, tampered)


def test_m3_minor_provenance_and_label(tmp_path):
    with pytest.raises(SystemExit, match="provenance"):
        C.main(["--phase", "S0.4", "--node", "digits_mlp", "--out", str(tmp_path / "o"), "--manager", "llamacpp",
                "--manager-model", "llamacpp/r1-manager", "--host-label", "ci"])
    out = _run(tmp_path, "--instances", "1", "--forks", "1", "--aa-fraction", "0")
    for l in C.read_jsonl(out / "leaves.jsonl"):
        assert l["provenance"]["harness_dirty"] is not None and l["provenance"]["paper_dirty"] is not None
    with pytest.raises(SystemExit, match="label"):
        C.main(["--phase", "synthetic", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "10", "--out", str(out),
                "--work", str(tmp_path / "work"), "--instances", "1", "--forks", "1", "--aa-fraction", "0",
                "--label", "EVIDENCE", "--host-label", "ci", "--gpu", "none"])


def test_m4_minor_seed_block_bounds(tmp_path):
    with pytest.raises(SystemExit, match="block"):
        _run(tmp_path, "--seed-base", "31000", phase="synthetic")
    with pytest.raises(SystemExit, match="block"):
        _run(tmp_path, "--instances", "2000", phase="synthetic")


def test_m5_minor_s05b_refuses_budget_reading_roots(tmp_path):
    s = synthetic_node("synthetic_P0", LL).sigma_node
    out = _run(tmp_path, "--instances", "1", "--forks", "0", "--root-policy",
               C.policy_string("dynamic", (0.1 * s, s, 0, 0, 0)),
               node="synthetic_P0", phase="S0.5", W="20", cap="12")
    with pytest.raises(SystemExit, match="reads the budget"):
        C.main(["--phase", "S0.5b", "--node", "synthetic_P0", "--out", str(out), "--work", str(tmp_path / "work"),
                "--truncate-W", "8"])
