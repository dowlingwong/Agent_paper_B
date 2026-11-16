"""Runbook P3: E-SYN worlds, simulator, exact DP and certified oracle (steps 3-6; revised after review round 1)."""
import importlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from paperc import schema as S
from paperc import seeds as SD
from paperc.esyn import dp, extra as X, families as F, policies as P, sim, table as T, worlds as WD
from paperc.esyn.oracle import OracleToleranceError, certify

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "paperC" / "esyn" / "oracle_table_v1.json"
REG = SD.Registry.load()
TRACKS_PIN = "fab88fced839c5fb794ed62a0742b4646cb76ea2"


# ---------------------------------------------------------------- worlds declare their channel as data

def test_worlds_declare_channel_and_sign():
    assert {"strict_null", "budget", "interaction", "shared_error", "eval_allocation"} <= set(X.WORLDS)
    for w in X.WORLDS.values():
        assert w.channel in X.CHANNELS and w.gain_sign in (0, 1)
        assert (w.channel == "none") == (w.gain_sign == 0)
        assert w.reference_gain == 0.5 * w.base.sigma_cmp
        json.dumps(w.to_dict())


def test_world_validation():
    base = WD.make_world("N0")
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="none", gain_sign=1, base=base)
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="budget", gain_sign=1, base=base, epochs=("E1", "E2", "verify"))
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="interaction", gain_sign=1, base=WD.make_world("N0", n_keys=2),
                    interaction=((0.0, 1.0), (0.0, 0.0)))
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="budget", gain_sign=1, base=base, sizes=(1.0,), size_probs=(0.5,))
    with pytest.raises(ValueError):           # no interaction on P1 probe / follow-up keys (review P3 finding 12)
        X.ESynWorld(name="x", channel="interaction", gain_sign=1,
                    base=WD.make_world("P1", variant="diffuse", strength=16.0),
                    interaction=((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0)))


# ---------------------------------------------------------------- records (P1), replay, privileged fields

POLICIES = [P.Static(0.0, 0.0), P.Static(0.001, -0.001), P.EvalAlloc(0.0, -0.001, 1.0, 2, 2, "best"),
            P.InteractionAware(0.0, 0.0, 0.5), P.Dynamic(0.0005, -0.001, 0.1, 0.004, 0.004, 0.01, 0.01),
            P.Schedule((0.0, 0.0015, 0.001, 0.0015, 0.002, 0.003), (0.0, -0.001, 0.001))]


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_campaigns_write_valid_records(name):
    w = X.WORLDS[name]
    pols = POLICIES + ([P.Threshold(dp.solve(w).table)] if not dp.inapplicable_reasons(w) else [])
    epochs = set()
    for pol in pols:
        for i in range(4):
            r = sim.run_campaign(w, pol, i, record=True)
            f = sim.run_campaign(w, pol, i)
            assert r.Y == f.Y and r.decisions == f.decisions        # fast path == recorded path
            v = S.check_campaign(r.rows, registry=REG, behaviour=sim.behaviour_for(pol))
            assert v == [], v[:3]
            assert r.rows[-1]["episode_end"]["reason"] == r.end_reason
            epochs |= {row["identity"]["epoch"] for row in r.rows}
            names = {k for row in r.rows for k in row["state"]["forecasts"]}
            priv = {k for k in names if k.startswith(sim.PRIVILEGED_PREFIX)}
            if getattr(pol, "privileged", False) and w.interaction:
                assert priv == {sim.PRIVILEGED_PREFIX + "interaction"}
            else:
                assert not priv, (pol.name, priv)                    # review P3 finding 4
    assert epochs == set(w.epochs)                                  # every offered epoch occurs


def test_record_regenerates_from_its_instance_seed():
    w = X.WORLDS["eval_allocation"]
    pol = P.EvalAlloc(0.0, -0.001, 1.0, 2, 2, "best")
    r = sim.run_campaign(w, pol, 37, record=True)
    seed = r.rows[0]["seeds"]["instance_seed"]
    assert seed == sim.INSTANCE_BASE + 37
    assert sim.run_campaign(w, pol, seed - sim.INSTANCE_BASE, record=True).rows == r.rows
    with pytest.raises(ValueError):
        sim.run_campaign(w, pol, sim.MAX_RECORDED, record=True)


def test_replay_detects_a_different_policy():
    w = X.WORLDS["budget"]
    r = sim.run_campaign(w, P.Static(0.0, 0.0), 1, record=True)
    v = S.check_campaign(r.rows, behaviour=sim.behaviour_for(P.Static(0.003, 0.0)))
    assert v and {x.check for x in v} == {"propensity"}


def test_terminal_and_final_candidates():
    w = X.WORLDS["eval_allocation"]
    r = sim.run_campaign(w, P.EvalAlloc(0.0, 0.0, 1.0, 2, 2, "best"), 7, record=True)
    last = r.rows[-1]
    assert last["identity"]["epoch"] == "final" and last["state"]["candidates"]
    assert all("candidates" not in row["state"] for row in r.rows[:-1])     # forward-compatible rows
    tm = last["terminal"]
    assert len(tm["audit_seeds"]) == w.n_audit and abs(np.mean(tm["y_terminal_per_seed"]) - tm["y_terminal"]) < 1e-12
    assert r.rows[0]["identity"]["campaign_id"].startswith("pc-")
    # a candidate whose record differs from the one it had as the incumbent is caught (review P3 finding 10)
    bad = json.loads(json.dumps(r.rows))
    bad[-1]["state"]["candidates"][0]["obs"] += 1
    assert any("does not carry the record" in v.message for v in S.check_campaign(bad))


def test_rng_root_key_is_claimed():
    claim = [c for c in REG.claims if c["name"] == "esyn_rng_root"]
    assert claim and claim[0]["value"] == sim.RNG_KEY and REG.paper_c_check("eps", sim.RNG_KEY) is None


# ---------------------------------------------------------------- mechanisms, replayed independently

def _replay(w, pol, inst):
    """Recompute every delta_hat, record, comparison sd and Y from the draws and the logged actions."""
    r = sim.run_campaign(w, pol, inst, record=True)
    d = sim.Draws(w, inst)
    props = {p.t: p for p in WD.proposal_sequence(w.base, w.regime, d.tab, d.stream)}
    b, sm, M = w.base, w.sigma_meas, w.interaction
    inc_true, inc_rec, inc_obs, inc_err = b.y0, b.y0, 0, []
    kept, chain, cand, k_r, cur_t = set(), {}, None, 0, None
    for row in r.rows:
        ep, act, st, out = row["identity"]["epoch"], row["action"]["action"], row["state"], row["outcome"]
        assert st["incumbent_recorded"] == pytest.approx(inc_rec, abs=1e-12) and st["incumbent_obs"] == inc_obs
        if ep == "E1" and act == "execute":
            t = int(st["candidate_hash"][1:])
            p = props[t]
            size = sim._size(w, p, d)
            delta = size * (WD.theta(b, w.regime, d.tab, p.key, t, []) - p.off) + b.sigma_eta * d.stream.eta[t]
            kidx = p.key - (w.llm_cap + 2) if b.n_keys > 0 else None
            if M and kidx not in kept:
                delta += sum(M[i][kidx] for i in kept)
            ct = inc_true + delta
            if w.comparison == "config":
                e = [sm * d.stream.eps[t]]
                assert out["delta_hat"] == pytest.approx(ct + e[0] - inc_rec, abs=1e-12)
            else:
                e = []
                assert out["delta_hat"] == pytest.approx(delta + b.sig(p.kind) * d.stream.eps[t], abs=1e-12)
            cand = [t, ct, e, kidx, out["delta_hat"]]
        elif ep == "verify" and act == "verify":
            t, ct, e, kidx, _ = cand
            ne = sm * d.eps_v[t, len(e) - 1]
            assert out["delta_hat"] == pytest.approx(ct + ne - inc_rec, abs=1e-12)
            e.append(ne)
        elif ep == "E2":
            t, ct, e, kidx, dh0 = cand
            exp = ct + np.mean(e) - inc_rec if w.comparison == "config" else dh0
            assert st["candidate_delta_hat"] == pytest.approx(exp, abs=1e-12)
            sc = sm * math.sqrt(1 / len(e) + (1 / inc_obs if inc_obs else 0)) if w.comparison == "config" \
                else b.sig("filler")
            assert st["forecasts"]["a2u"]["sigma"] == pytest.approx(sc, abs=1e-15)
            if act == "keep":
                if kidx is not None:
                    kept.add(kidx)
                inc_true = ct
                if w.comparison == "config":
                    inc_err, inc_rec, inc_obs = list(e), ct + np.mean(e), len(e)
                else:
                    inc_rec, inc_obs = inc_rec + exp, 1
                chain[f"c{t}"] = [ct, list(inc_err)]
            k_r, cur_t = 0, t
        elif ep == "reaudit" and act == "reaudit":
            ne = sm * d.eps_r[cur_t, k_r]
            k_r += 1
            assert out["delta_hat"] == pytest.approx(inc_true + ne - inc_rec, abs=1e-12)
            inc_err.append(ne)
            inc_rec, inc_obs = inc_true + np.mean(inc_err), len(inc_err)
            chain[st["incumbent_hash"]] = [inc_true, list(inc_err)]
        elif ep == "final":
            for c in st["candidates"]:
                v, m = chain[c["hash"]]
                assert c["recorded"] == pytest.approx(v + np.mean(m), abs=1e-12) and c["obs"] == len(m)
            assert r.Y == pytest.approx(chain[row["action"]["selected"]][0] - b.y0, abs=1e-12)
    if "final" not in w.epochs:
        assert r.Y == pytest.approx(inc_true - b.y0, abs=1e-12)
    return r


@pytest.mark.parametrize("name,pol", [
    ("eval_allocation", P.EvalAlloc(0.0, -0.001, 1.0, 2, 3, "best")),
    ("eval_allocation", P.EvalAlloc(0.0, 0.0, 2.0, 3, 3, "incumbent")),
    ("shared_error", P.EvalAlloc(0.0, 0.0, 0.0, 1, 3, "incumbent")),
    ("interaction", P.InteractionAware(0.0, 0.0, 0.25)),
    ("interaction", P.Static(0.0, -0.002)),
    ("budget", P.Static(0.0, 0.0))])
def test_measurement_model_replays_exactly(name, pol):
    for i in range(25):
        _replay(X.WORLDS[name], pol, i)


def test_interaction_adds_the_partner_complement():
    w = X.WORLDS["interaction"]
    seen = 0
    for i in range(60):
        tr = []
        sim.run_campaign(w, P.Static(0.0, -0.01), i, trace=tr)     # keeps nearly everything
        for e in tr:
            expect = sum(w.interaction[k][e["kidx"]] for k in e["kept_keys"]) if e["kidx"] not in e["kept_keys"] \
                else 0.0
            assert e["interaction"] == pytest.approx(expect, abs=1e-15)
            seen += e["interaction"] > 0
    assert seen > 20                                                 # partners do meet


# ---------------------------------------------------------------- loop-level equivalence with Track S (step 2)

@pytest.fixture(scope="module")
def tracks_sim(tmp_path_factory):
    root = tmp_path_factory.mktemp("tracks_pin")
    try:
        for f in ("simulate_controls.py", "analyze.py", "schema.py"):
            src = subprocess.run(["git", "-C", str(REPO), "show", f"{TRACKS_PIN}:r1/tracks/{f}"],
                                 capture_output=True, text=True, check=True).stdout
            (root / "r1" / "tracks").mkdir(parents=True, exist_ok=True)
            (root / "r1" / "tracks" / f).write_text(src)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip(f"Track S pin {TRACKS_PIN[:8]} not available (git fetch trackS-ops-20261030)")
    (root / "r1" / "__init__.py").write_text("")
    (root / "r1" / "tracks" / "__init__.py").write_text("")
    saved = {k: v for k, v in sys.modules.items() if k == "r1" or k.startswith("r1.")}
    for k in saved:
        del sys.modules[k]
    sys.path.insert(0, str(root))
    try:
        yield importlib.import_module("r1.tracks.simulate_controls")
    finally:
        sys.path.remove(str(root))
        for k in [k for k in sys.modules if k == "r1" or k.startswith("r1.")]:
            del sys.modules[k]
        sys.modules.update(saved)


@pytest.mark.parametrize("kind,variant,strength,W", [("N0", None, 0.0, 40), ("P1", "diffuse", 16.0, 10),
                                                     ("P2+", "diffuse", 0.012, 10), ("P0", "diffuse", 0.004, 10)])
def test_campaign_values_equal_track_s(tracks_sim, kind, variant, strength, W):
    """Runbook P3 step 2: Paper C's loop reproduces Track S's campaign values (static rules, noiseless y_true)."""
    TS = tracks_sim
    w = X.ESynWorld(name=f"eq_{kind}_{variant}", channel="budget", gain_sign=1,
                    base=WD.make_world(kind, strength, variant), W=W)
    tw = TS.make_world(kind, strength, variant)
    for g, h in ((0.0, 0.0), (0.001, -0.001), (0.0015, 0.001)):
        tsim = TS.Sim(tw, TS.Regime(W=W, llm_cap=40, p_rule=0.55), 0)
        if kind == "N0":
            tsim.W = W
        pol = TS.ThresholdPolicy(f"static:{g},{h}")
        for inst in range(40):
            d = sim.Draws(w, inst)
            _, seed = sim.campaign_seed(w, inst)
            y_ts = tsim.run_campaign(d.tab, pol, seed, None, noiseless=True) - tw.y0
            assert sim.run_campaign(w, P.Static(g, h), inst).Y == pytest.approx(y_ts, abs=1e-12)


# ---------------------------------------------------------------- exact DP

@pytest.mark.parametrize("name", ["budget", "strict_null"])
def test_dp_matches_simulation(name):
    w = X.WORLDS[name]
    sol = dp.solve(w)
    n = 8000
    inst = range(sim.DECOMP_BASE + 500_000, sim.DECOMP_BASE + 500_000 + n)
    ys = sim.campaign_values(w, P.Threshold(sol.table), inst)
    assert abs(ys.mean() - sol.value) < 4 * ys.std() / math.sqrt(n)
    for g in (0.0, dp.size_law(w).v[1]):
        ys = sim.campaign_values(w, P.Static(g, 0.0), inst)
        assert abs(ys.mean() - dp.static_value(w, g)) < 4 * ys.std() / math.sqrt(n)


def test_dp_dominates_statics_and_null_gain_is_zero():
    for name in ("budget", "strict_null"):
        w = X.WORLDS[name]
        v = dp.solve(w).value
        stat = [dp.static_value(w, g) for g in np.linspace(0, 0.004, 41)] + \
               [dp.static_value(w, g) for g in dp.size_law(w).v]
        assert v >= max(stat) - 1e-15
        if name == "strict_null":
            assert abs(v - max(stat)) < 1e-15          # non-binding W: the DP is the static rule g = 0
        else:
            assert v - max(stat) > 0.001               # binding W: a planted budget gain


def test_dp_not_applicable_elsewhere():
    for name in ("interaction", "shared_error", "eval_allocation", "information", "keep_feedback"):
        assert dp.inapplicable_reasons(X.WORLDS[name])


def test_certify_fails_when_n_max_is_too_small():
    w = X.WORLDS["budget"]
    sol = dp.solve(w)
    with pytest.raises(OracleToleranceError):
        certify(w, delta_Y=0.002, n_select=50, n_pilot=50, n_max=60, statics=[P.Static(0.001, 0.0)],
                members=[P.Threshold(sol.table)])


def test_static_grid_extension():
    g, h, ext = F.extend_static_grid(list(F.G0), list(F.H0), P.Static(0.0, -0.003))
    assert ext and h[0] == -0.005 and g == list(F.G0)              # g = 0 is a natural bound
    assert F.static_interior(g, h, P.Static(0.0, -0.003))
    g, h, ext = F.extend_static_grid(list(F.G0), list(F.H0), P.Static(0.003, 0.001))
    assert ext and g[-1] == 0.005 and h[-1] == 0.003


def test_schedule_nests_static_rules():
    w = X.WORLDS["keep_feedback"]
    s, sch = P.Static(0.001, -0.002), P.Schedule((0.001,) * 6, (-0.002,) * 3)
    assert all(sim.run_campaign(w, s, i).Y == sim.run_campaign(w, sch, i).Y for i in range(30))


# ---------------------------------------------------------------- certified oracle (committed table)

@pytest.fixture(scope="module")
def table():
    return json.loads(TABLE.read_text())


CHANNEL_WORLDS = ["budget", "interaction", "shared_error", "eval_allocation", "keep_feedback", "information"]


def test_table_is_current(table):
    assert table["code_sha256"] == T.code_sha256(), "E-SYN code changed: rebuild with python -m paperc.esyn.table"
    assert set(table["worlds"]) == set(X.WORLDS)
    for name, rec in table["worlds"].items():
        assert rec["world"] == json.loads(json.dumps(X.WORLDS[name].to_dict())), f"{name}: table is stale"


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_selected_policies_are_interior(table, name):
    """Review P3 findings 1 and 8: no selected static or member parameter sits on a non-natural grid edge."""
    sel = table["worlds"][name]["oracle"]["selection"]
    assert sel["static_interior"]
    ms = sel["member_search"]
    assert ms["param_interior"] and ms["gh_interior"]


def test_null_distinct_member_does_not_beat_static(table):
    o = table["worlds"]["strict_null"]["oracle"]
    assert o["selection"]["best_member"] != o["selection"]["best_static"]
    assert o["pass"] and o["reference_source"].startswith("declared")
    assert o["gain"] + o["half_width"] <= o["tolerance"]           # no member beats the static rule
    fam = table["worlds"]["strict_null"]["null_family_eval"]       # each family's best, on the evaluation block
    assert set(fam) == {"dynamic_null", "schedule"}
    for r in fam.values():
        assert r["diff"] + r["half_width"] <= o["tolerance"], r
    assert max(r["share_differing"] for r in fam.values()) >= 0.10  # at least one decides differently often


@pytest.mark.parametrize("name", CHANNEL_WORLDS)
def test_channel_gain_is_positive(table, name):
    o = table["worlds"][name]["oracle"]
    assert X.WORLDS[name].gain_sign == 1
    assert o["gain"] - o["half_width"] > 0                          # the sign is as declared


UNCERTIFIED: dict[str, str] = {}


@pytest.mark.parametrize("name", [pytest.param(n, marks=pytest.mark.xfail(strict=True, reason=UNCERTIFIED[n]))
                                  if n in UNCERTIFIED else n for n in CHANNEL_WORLDS])
def test_channel_gain_is_certified(table, name):
    o = table["worlds"][name]["oracle"]
    assert o["reference_source"].startswith("declared")
    assert o["pass"] and o["half_width"] <= o["tolerance"]


def test_dp_and_oracle_agree_on_budget(table):
    rec = table["worlds"]["budget"]
    o = rec["oracle"]
    exact = rec["dp_gain_over_selected_static"]
    assert exact is not None and o["reference_gain"] == rec["dp_gain_over_best_static"]
    assert abs(o["gain"] - exact) <= o["half_width"] + o["tolerance"]
    ev = o["evaluation"]
    assert abs(ev["member_value"] - rec["dp_value"]) < 4 * ev["member_sd"] / math.sqrt(ev["n"])
    assert abs(ev["static_value"] - rec["dp_selected_static_exact"]) < 4 * ev["static_sd"] / math.sqrt(ev["n"])


def test_decomposition_and_calibration_present(table):
    dc = table["decomposition"]
    assert set(dc["vs_best_static"]) == {"verify_only", "reaudit_only", "both_final_incumbent", "both_final_best"}
    assert "final_best_minus_incumbent" in dc["W40"] and "final_best_minus_incumbent" in dc["W60"]
    assert {(c["world"], c["W"]) for c in table["calibration"]} == set(T.CALIBRATION)
    assert all(c["block"][0] == sim.SELECT_BASE for c in table["calibration"])
