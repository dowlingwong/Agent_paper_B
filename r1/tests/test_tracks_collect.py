"""Track S collector: fork selection probabilities, end-to-end on synthetic nodes, resume, schema round trip,
policy phases (tune / campaign) and the same-repetition placebo, S0.4 + fit_prior.

CPU only, scripted managers (no LLM). ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from r1.tracks import collect as C
from r1.tracks.a2u import A2UPrior, RidgeScore, SCORE_MODEL_SCHEMA
from r1.tracks.schema import STATE_FEATURES, TRACKS_LEAF_SCHEMA, leaf_from_dict, root_from_dict, to_dict


LL = {"mechanism": "loglinear"}


def _run(tmp: Path, *extra: str, node: str = "synthetic_N0", phase: str = "synthetic", out: str = "out") -> Path:
    args = ["--phase", phase, "--node", node, "--llm-cap", "10", "--out", str(tmp / out), "--work", str(tmp / "work"),
            "--label", "FIXTURE", "--host-label", "ci", "--gpu", "none", *extra]
    if phase != "S0.4" and "--W" not in extra:
        args += ["--W", "10"]
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


# ---------------------------------------------------------------------------
# Fork selection
# ---------------------------------------------------------------------------

def test_selection_draw_probabilities_and_determinism():
    n = 6000
    draws = [C.selection_draw(f"r__E1_b{i:05d}", epoch="E1", p_u=0.2, near=(i % 2 == 0), p_near=0.5,
                              aa_fraction=0.1) for i in range(n)]
    near = [d for i, d in enumerate(draws) if i % 2 == 0]
    far = [d for i, d in enumerate(draws) if i % 2 == 1]
    assert sum(d is not None for d in far) / len(far) == pytest.approx(0.2, abs=0.02)
    assert sum(d is not None for d in near) / len(near) == pytest.approx(1 - 0.8 * 0.5, abs=0.025)
    for d in near:
        if d is not None:
            assert d["selection"]["p_select"] == pytest.approx(0.6)
    for d in far:
        if d is not None:
            assert d["selection"]["p_select"] == pytest.approx(0.2) and not d["selection"]["oversample"]
    sel = [d for d in draws if d is not None]
    assert np.mean([d["selection"]["channel_arms"] for d in sel]) == pytest.approx(1 / 3, abs=0.03)
    assert np.mean([d["aa"] for d in sel]) == pytest.approx(0.1, abs=0.02)
    # Deterministic per fork id (a resumed run selects the same forks); E2 forks never get channel arms.
    assert C.selection_draw("r__E1_b00007", epoch="E1", p_u=0.2, near=False, p_near=0.5, aa_fraction=0.1) == draws[7]
    e2 = [C.selection_draw(f"r__E2_b{i:05d}", epoch="E2", p_u=1.0, near=False, p_near=0, aa_fraction=0)
          for i in range(300)]
    assert all(d is not None and not d["selection"]["channel_arms"] for d in e2)


def test_binding_shares():
    roots = [{"status": "ok", "W": 20, "runs_used": r} for r in (7, 9, 10, 12, 20)]
    assert C.binding_shares(roots) == {8: 0.8, 10: 0.6, 12: 0.4, 20: 0.2}
    with pytest.raises(ValueError):
        C.binding_shares([{"status": "ok", "W": 10, "runs_used": 10}])


def test_leaf_arms():
    e1 = {"epoch": "E1", "selection": {"channel_arms": True}, "aa": True}
    assert C.leaf_arms(e1, 2) == [("skip", 1), ("skip", 2), ("execute", 1), ("execute", 2), ("ghost", 1), ("ghost", 2),
                                  ("ctrl_only", 1), ("ctrl_only", 2), ("aa", 0)]
    e2 = {"epoch": "E2", "selection": {"channel_arms": False}, "aa": False}
    assert C.leaf_arms(e2, 2) == [("keep", 1), ("keep", 2), ("discard", 1), ("discard", 2)]


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_collector_end_to_end_resume_and_schema(tmp_path):
    out = _run(tmp_path, "--instances", "2", "--forks", "3", "--aa-fraction", "0.5", "--near-band", "0.001",
               "--p-near", "1.0", node="synthetic_P1")
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == C.MANIFEST_SCHEMA and manifest["phase"] == "synthetic"
    assert manifest["g0"] == manifest["g_declared"] and manifest["e2_verify"] is False
    roots = [root_from_dict(r) for r in C.read_jsonl(out / "roots.jsonl")]
    leaves_raw = C.read_jsonl(out / "leaves.jsonl")
    leaves = [leaf_from_dict(l) for l in leaves_raw]
    forks = C.read_jsonl(out / "forks.jsonl")
    assert len(roots) == 2 and all(r.status == "ok" for r in roots)
    assert forks and leaves and all(l.status == "ok" for l in leaves)
    assert all(to_dict(l) == raw for l, raw in zip(leaves, leaves_raw))  # schema round trip
    assert all(l.schema == TRACKS_LEAF_SCHEMA and tuple(l.state) == STATE_FEATURES for l in leaves)
    expected = Counter((f["fork_id"], arm, rep) for f in forks for arm, rep in C.leaf_arms(f, 2, 1))
    assert Counter((l.fork_id, l.arm, l.rep) for l in leaves) == expected
    for l in leaves:
        assert l.provenance.g0 == manifest["g0"] and l.provenance.label == "FIXTURE"
        seed = int(l.instance_id.rsplit("__s", 1)[1])
        assert len(l.y_terminal_per_seed) == manifest["K"] and \
            l.audit_seeds == list(C.instance_audit_seeds(manifest["phase"], seed, manifest["K"]))
        if l.arm in ("skip", "ghost", "ctrl_only", "discard"):
            assert l.immediate_measured == 0.0
        assert (l.aa_reproduced is True) if l.arm == "aa" else (l.aa_reproduced is None)
        assert l.llm_seed_base == (0 if l.arm == "aa" else C.REP_BASE + l.rep)
        assert 0.0 < l.selection.p_select <= 1.0
    # Ghost / ctrl_only spend the fork trial's run; skip does not.
    by = {(l.fork_id, l.arm, l.rep): l for l in leaves}
    for (fid, arm, rep), l in by.items():
        if arm == "ghost":
            assert l.runs_used >= 1
    # Resume: a second session does nothing; a removed leaf line is recomputed identically.
    adapter = C.make_adapter("synthetic_P1", {}, None)
    assert C.plan(C.Run(C.parse_args(["--phase", "synthetic", "--node", "synthetic_P1", "--out", str(out)]), adapter, out,
                        tmp_path / "work", manifest, None, "", 0.0, 0.0, 0.0, None, None, 0.0))["leaves_todo"] == []
    lines = (out / "leaves.jsonl").read_text().splitlines()
    (out / "leaves.jsonl").write_text("\n".join(lines[:-1]) + "\n")
    _run(tmp_path, "--instances", "2", "--forks", "3", "--aa-fraction", "0.5", "--near-band", "0.001",
         "--p-near", "1.0", node="synthetic_P1")
    again = C.read_jsonl(out / "leaves.jsonl")
    assert len(again) == len(lines)
    strip = lambda d: {k: v for k, v in d.items() if k != "provenance"}  # noqa: E731
    assert strip(again[-1]) == strip(json.loads(lines[-1]))
    assert len(C.read_jsonl(out / "roots.jsonl")) == 2  # roots not re-run
    # Changed parameters are refused on resume.
    with pytest.raises(SystemExit, match="differ"):
        _run(tmp_path, "--instances", "2", "--forks", "3", "--W", "12", node="synthetic_P1")


def test_dry_run_runs_nothing(tmp_path, capsys):
    assert C.main(["--phase", "synthetic", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "10",
                   "--out", str(tmp_path / "o"), "--work", str(tmp_path / "w"), "--instances", "3", "--dry-run"]) == 0
    with pytest.raises(ValueError, match="non-binding"):  # the N0 world runs at W = llm_cap only
        C.main(["--phase", "synthetic", "--node", "synthetic_N0", "--W", "10", "--llm-cap", "40",
                "--out", str(tmp_path / "o"), "--work", str(tmp_path / "w"), "--instances", "3", "--dry-run"])
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["dry_run"] and out["roots_todo"] == 3 and not (tmp_path / "o").exists()


def _ledger(work: Path, root_id: str) -> list[str]:
    rows = C.read_jsonl(work / "roots" / root_id / "root_trials.jsonl")
    out = []
    for r in rows:
        for key in ("timestamp_start", "timestamp_end", "wall_clock_seconds"):
            r.pop(key)
        out.append(json.dumps(r, sort_keys=True))
    return out


def test_campaign_phase_policies_and_same_repetition_placebo(tmp_path):
    model = tmp_path / "model.json"
    model.write_text(json.dumps({"schema": SCORE_MODEL_SCHEMA, "intercept": -0.0005,
                                 "coef": {"index_value": 1.0, "budget_gap": 0.001, "e2": 0.0005}}))
    g0 = 0.0005
    pols = [f"static:{g0},0", f"dynamic:{g0},0,0,0,0", f"dynamic:{g0},0.004,0.5,0,0.001",
            f"static:{g0},0.001", f"pi_prime:{model}"]
    out = _run(tmp_path, "--instances", "2", *sum((["--policy", p] for p in pols), []), "--rep", "3",
               phase="campaign", node="synthetic_P2p")
    roots = [root_from_dict(r) for r in C.read_jsonl(out / "roots.jsonl")]
    assert Counter(r.policy for r in roots) == Counter({p: 2 for p in pols})
    assert all(r.status == "ok" and r.y_terminal is not None and r.y_start is not None for r in roots)
    # Same instance, same seed key: static and dynamic with zero slopes take identical decisions,
    # so their ledgers are byte-identical apart from wall-clock fields (the exact same-repetition placebo).
    for inst in {r.instance_id for r in roots}:
        ids = {r.policy: r.root_id for r in roots if r.instance_id == inst}
        a, b = _ledger(tmp_path / "work", ids[pols[0]]), _ledger(tmp_path / "work", ids[pols[1]])
        assert a and a == b


def test_tune_phase_runs_every_configuration_on_the_same_paired_instances(tmp_path):
    """Rev. 7 D2: 15 statics on 20 paired dev instances; the 4 fixed members (centred at m*'s decision means
    from the static stage's roots) on 40, the first 20 of which are the statics' instances."""
    grid = C.tuning_grid("static", 0.003)
    assert len(grid) == 15 and "static:0.00015,-0.00075" in grid and "static:0.0012,0.00075" in grid
    assert "static:0,0" in grid  # rev. 7 (a)
    assert len(C.tuning_grid("static", 0.003, extend=True)) == 18
    dyn = C.tuning_grid("dynamic", 0.003, "static:0.0003,0", centres={"r1bar": 0.1, "taubar": 0.002, "r2bar": 0.05})
    assert dyn == ["dynamic:0.0003,0.003,0,0,0,0.1,0.002,0.05", "dynamic:0.0003,0,0.5,0,0,0.1,0.002,0.05",
                   "dynamic:0.0003,0,0,0,0.0015,0.1,0.002,0.05", "dynamic:0.0003,0,0,0,-0.0015,0.1,0.002,0.05"]
    st = _run(tmp_path, "--tune-grid", "static", "--sigma-cmp-vary", "0.003", phase="tune", out="static")
    roots = C.read_jsonl(st / "roots.jsonl")
    assert Counter(r["policy"] for r in roots) == Counter({p: C.TUNE_N_STATIC for p in grid})
    m_star = "static:0.0003,0"
    centres = C.centres_from_roots(str(st / "roots.jsonl"), m_star)
    assert centres["n_E1"] > 0 and centres["n_E2"] > 0
    mem = _run(tmp_path, "--tune-grid", "dynamic", "--sigma-cmp-vary", "0.003", "--m-star", m_star,
               "--centres-from", str(st / "roots.jsonl"), phase="tune", out="members")
    mroots = C.read_jsonl(mem / "roots.jsonl")
    members = C.tuning_grid("dynamic", 0.003, m_star, centres=centres)
    assert Counter(r["policy"] for r in mroots) == Counter({p: C.TUNE_N_MEMBERS for p in members})
    assert json.loads((mem / "manifest.json").read_text())["centres"] == centres
    by_policy: dict[str, set] = {}
    for r in roots + mroots:
        by_policy.setdefault(r["policy"], set()).add(r["instance_id"])
    static_ids = {frozenset(by_policy[p]) for p in grid}
    member_ids = {frozenset(by_policy[p]) for p in members}
    assert len(static_ids) == 1 and len(member_ids) == 1  # paired within each stage
    (s_ids,), (m_ids,) = static_ids, member_ids
    assert s_ids < m_ids and sorted(m_ids)[:C.TUNE_N_STATIC] == sorted(s_ids)  # the first 20 are shared
    seeds = {int(i.rsplit("__s", 1)[1]) for i in m_ids}
    lo, hi = C.INSTANCE_SEED_BLOCKS["tune"]
    assert seeds == {lo + k for k in range(C.TUNE_N_MEMBERS)}  # the dev (tuning) block


def test_s04_and_fit_prior(tmp_path):
    out = _run(tmp_path, "--instances", "2", phase="S0.4", node="synthetic_N0")
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["W"] == manifest["llm_cap"]  # non-binding W in S0.4
    rows = C.read_jsonl(out / "s04_rows.jsonl")
    assert rows and all(r["delta_audit"] is not None and r["k"] == C.DEV_K for r in rows)
    assert {r["sign"] for r in rows} <= {"+", "-", "0"}
    assert C.main(["--phase", "fit_prior", "--node", "synthetic_N0", "--out", str(out), "--sigma-node", "0.005"]) == 0
    prior = A2UPrior.load(out / "a2u_prior.json")
    assert prior.node == "digits_mlp" and "local" in prior.kinds
    assert prior.meta["sources"]["s04_rows_sha256"] == C.sha256_file(out / "s04_rows.jsonl")


def test_policy_parsing_and_verify_refusal(tmp_path):
    from r1.tracks.synthetic import synthetic_node
    from r1.c3.features import NodeContext
    from r1.tracks.synthetic import surface_start_files
    node = synthetic_node("synthetic_N0", LL)
    pr = node.prior()
    ctx = NodeContext(node="digits_mlp", start_files=surface_start_files(), sigma_node=pr.sigma_node, runs_total=10,
                      memory_mode="append_only_summary")
    st = C.policy_controller("static:0.001,0.002", pr, ctx, g0=0.0)
    dy = C.policy_controller("dynamic:0.001,0,0,0.002,0", pr, ctx, g0=0.0)
    dc = C.policy_controller("dynamic:0.001,0,0,0.002,0,0.3,0.004,0.2", pr, ctx, g0=0.0)
    assert (st.g, st.h0) == (dy.g, dy.h0) == (dc.g, dc.h0) and st.version == dy.version
    assert st.policy_name == "static:0.001,0.002" and dc.r2_bar == 0.2
    for bad in ("dynamic:b_budget=1", "static:g=0.001,e2off=0", "matched_static:0.001,0.002", "dynamic:1,2"):
        with pytest.raises(ValueError):
            C.policy_controller(bad, pr, ctx, g0=0.0)
    with pytest.raises(ValueError):
        C.policy_controller("budget_dp:table.json", pr, ctx, g0=0.0)
    with pytest.raises(SystemExit, match="verify"):
        C.main(["--phase", "synthetic", "--node", "synthetic_N0", "--W", "10", "--out", str(tmp_path / "o"),
                "--e2-verify"])


def test_s05b_truncated_incumbent_audits(tmp_path):
    out = _run(tmp_path, "--instances", "2", "--forks", "0", "--aa-fraction", "0", "--W", "20", node="synthetic_P0",
               phase="S0.5")
    assert C.main(["--phase", "S0.5b", "--node", "synthetic_P0", "--out", str(out), "--work", str(tmp_path / "work"),
                   "--truncate-W", "3,6,20"]) == 0
    rows = C.read_jsonl(out / "s05b_truncated.jsonl")
    assert len(rows) == 6 and all(len(r["y_terminal_per_seed"]) == 5 for r in rows)
    roots = {r["root_id"]: r for r in C.read_jsonl(out / "roots.jsonl")}
    for r in rows:
        assert r["runs_used"] <= r["W"]
        assert r["binding"] == (r["runs_used"] >= r["W"] and r["trials"] < 10)  # W used while proposals remained
        if r["W"] == 20:  # the full ledger: the root's own terminal audit
            assert r["y_terminal"] == roots[r["root_id"]]["y_terminal"]
    # The truncation equals a campaign actually run at that W (A2-U is budget-blind).
    from r1.tracks import oracle as O
    from r1.tracks.synthetic import synthetic_node
    node = synthetic_node("synthetic_P0", LL)
    for r in rows:
        if r["W"] == 6:
            seed = int(r["instance_id"].rsplit("__s", 1)[1])
            ctl = O.controller_for(node, "a2u", W=6)
            assert O.simulate(node, ctl, seed, W=6, cap=10)["y_terminal"] == r["y_terminal"]
    # Resume: nothing is audited twice.
    assert C.main(["--phase", "S0.5b", "--node", "synthetic_P0", "--out", str(out), "--work", str(tmp_path / "work"),
                   "--truncate-W", "3,6,20"]) == 0
    assert len(C.read_jsonl(out / "s05b_truncated.jsonl")) == 6


def test_truncate_at_W():
    rows = [{"budget_index": i, "decision": d, "worker_mode": "w"} for i, d in
            enumerate(["kept", "skipped", "discarded", "kept", "skipped", "kept"], start=1)]
    prefix, binding = C.truncate_at_W(rows, 2)
    assert [r["budget_index"] for r in prefix] == [1, 2, 3] and binding
    prefix, binding = C.truncate_at_W(rows, 10)
    assert len(prefix) == 6 and not binding
    prefix, binding = C.truncate_at_W(rows, 4)  # the 4th run is the last trial: W did not stop anything
    assert len(prefix) == 6 and not binding
