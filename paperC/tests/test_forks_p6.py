"""Runbook P6: fork design, fork continuations on E-SYN, tau^2, design-weighted means and the N6 value."""
import json
from dataclasses import replace

import numpy as np
import pytest

from paperc import forks as F
from paperc import policies as P
from paperc import schema as S
from paperc.esyn import policies as EP, sim
from paperc.esyn.extra import WORLDS
from paperc.runner import OUT as LADDER

LAD = json.loads(LADDER.read_text())


def n1(world):
    return EP.from_name(LAD["worlds"][world]["rows"]["N1"]["policy"])


def design(world, **kw):
    w, pol = WORLDS[world], n1(world)
    base = dict(q_uniform=0.2, q_oversample=0.6, band_e1=0.25 * w.base.sigma_cmp, band_e2=0.25 * w.base.sigma_cmp,
                g=pol.g, h=pol.h)
    return F.Design(**{**base, **kw})


def dispatcher(*pols):
    by = {p.name: p for p in pols}
    return lambda view: sim.behaviour_for(by[view.policy])(view)


# ---------------------------------------------------------------- simulator

def test_fork_continuation_reproduces_root_and_is_schema_valid():
    w, beh, cont = WORLDS["eval_allocation"], n1("eval_allocation"), P.N0()
    ft = F.collect(w, beh, range(3), design("eval_allocation"), [beh, cont], reps=2, record=True)
    assert len(ft) > 0 and ft.q.shape == (len(ft), 2, 2)
    rows = [S.from_dict(r) for r in ft.rows]
    assert S.check_campaign(rows, behaviour=dispatcher(beh, cont)) == []
    root = {(r.identity.campaign_id, r.identity.step_index): r for r in rows if not r.identity.branch_path}
    firsts = {}
    for r in rows:
        if r.identity.branch_path:
            firsts.setdefault((r.identity.campaign_id, tuple(r.identity.branch_path)), r)
    assert len(firsts) == len(ft) * 2 * 2 * 2                       # forks x arms x continuations x replicates
    for (_, bp), r in firsts.items():
        par = root[(r.identity.campaign_id, r.identity.step_index)]
        assert r.state == par.state and r.action.forced and r.policy.action_prob is None
        assert r.policy.behaviour_action == par.action.action and r.action.rule == "fork_arm"
        fork_id, arm, c, rep = bp[0].split(":")
        assert r.fork.replicate == int(rep[1:]) and r.identity.fork_id == fork_id and r.action.action == arm


def test_fork_randomness_shared_proposals_independent_measurements():
    w, beh = WORLDS["budget"], n1("budget")
    mk = lambda arm, c=0, r=1: sim.ForkSpec(trial=5, epoch="E1", arm=arm, continuation=beh, cont_index=c,
                                            replicate=r)                                  # noqa: E731
    a, b = sim.ForkDraws(w, 7, mk("execute")), sim.ForkDraws(w, 7, mk("skip"))
    assert np.array_equal(a.stream.eta, b.stream.eta) and np.array_equal(a.stream.u_kind, b.stream.u_kind)
    assert not np.array_equal(a.eps, b.eps)
    assert not np.array_equal(sim.ForkDraws(w, 7, mk("execute", r=2)).stream.eta, a.stream.eta)
    assert not np.array_equal(sim.ForkDraws(w, 7, mk("execute", c=1)).stream.eta, a.stream.eta)


def test_fork_errors():
    w, beh = WORLDS["budget"], n1("budget")
    with pytest.raises(ValueError, match="trial >= 2"):
        sim.ForkSpec(trial=1, epoch="E1", arm="skip", continuation=beh)
    with pytest.raises(ValueError, match="not allowed"):
        sim.ForkSpec(trial=3, epoch="E1", arm="keep", continuation=beh)
    with pytest.raises(ValueError, match="deterministic"):
        sim.ForkSpec(trial=3, epoch="E1", arm="skip", continuation=P.RandomExec(0.5, 0.0))
    root = sim.run_campaign(w, beh, 2, record=True)
    rule = next(r for r in root.rows if r["action"]["rule"] == "rule_noop")
    t_rule = int(rule["state"]["proposal_hash"][1:])
    with pytest.raises(ValueError, match="rule-forced"):
        sim.run_campaign(w, beh, 2, fork=sim.ForkSpec(trial=t_rule, epoch="E1", arm="skip", continuation=beh))
    skipped = [int(r["state"]["proposal_hash"][1:]) for r in root.rows
               if r["identity"]["epoch"] == "E1" and r["action"]["action"] == "skip" and not r["state"]["rule_forced"]]
    if skipped:
        with pytest.raises(ValueError, match="not reached"):
            sim.run_campaign(w, beh, 2, fork=sim.ForkSpec(trial=skipped[0], epoch="E2", arm="keep", continuation=beh))


# ---------------------------------------------------------------- design

def test_selection_rule_and_design_weights():
    w, beh = WORLDS["keep_feedback"], n1("keep_feedback")
    d = design("keep_feedback")
    root = sim.run_campaign(w, beh, 4, record=True)
    pts = F.select_forks(w, 4, root.rows, d)
    elig = F.eligible_rows(root.rows)
    assert pts and len(pts) < len(elig)
    for fp in pts:
        u = F.selection_uniforms(w, 4, fp.trial, fp.epoch)
        near = abs(fp.margin) <= d.band_e1
        assert fp.design.near_threshold == near
        assert fp.design.uniform == (u[0] < d.q_uniform) and fp.design.oversample == (near and u[1] < d.q_oversample)
        assert fp.design.p_select == pytest.approx(1 - (1 - d.q_uniform) * (1 - d.q_oversample * near))
    assert pts == F.select_forks(w, 4, root.rows, d)                               # deterministic
    assert len(F.select_forks(w, 4, root.rows, d, select_all=True)) == len(elig)


def test_horvitz_thompson_mean_is_design_unbiased():
    """Over redrawn selections of fixed roots, the HT mean of any state quantity equals its population mean; the
    unweighted mean is biased by the near-threshold oversample (here: the quantity is |margin| itself)."""
    w, beh = WORLDS["budget"], n1("budget")
    roots = [sim.run_campaign(w, beh, i, record=True).rows for i in range(30)]
    full = [fp for i, r in enumerate(roots) for fp in F.select_forks(w, i, r, design("budget"), select_all=True)]
    pop = np.mean([abs(fp.margin) for fp in full])
    ht, unw = [], []
    for rep in range(300):
        d = design("budget", q_uniform=0.1, q_oversample=0.8, design_rep=rep)
        pts = [fp for i, r in enumerate(roots) for fp in F.select_forks(w, i, r, d)]
        x, wt = np.array([abs(fp.margin) for fp in pts]), np.array([1 / fp.design.p_select for fp in pts])
        ht.append((wt * x).sum() / len(full))
        unw.append(x.mean())
    se = np.std(ht) / np.sqrt(len(ht))
    assert abs(np.mean(ht) - pop) < 4 * se
    assert np.mean(unw) < pop - 10 * np.std(unw) / np.sqrt(len(unw))


# ---------------------------------------------------------------- statistics on synthetic tables

def synthetic(n_roots=60, per_root=8, tau=0.0, noise=1.0, C=2, R=2, seed=0, q_slope=0.0):
    rng = np.random.default_rng(seed)
    n = n_roots * per_root
    inst = np.repeat(np.arange(n_roots), per_root)
    x = rng.normal(size=n)
    theta = tau * rng.normal(size=n) + q_slope * x
    cells = theta[:, None, None] + noise * rng.normal(size=(n, C, R))
    ps = np.where(rng.random(n) < 0.5, 0.25, 1.0)
    feats = [{k: (x[i] if k in ("v_star", "m_hat") else 0.0) for k in F.FEATURES["E1"] + F.FEATURES["E2"]}
             for i in range(n)]
    return F.ForkTable(world="syn", behaviour="b", continuations=["c"] * C, reps=R, fork_id=[f"f{i}" for i in range(n)],
                       instance=inst, trial=np.arange(n), e1=np.ones(n, bool), index=x, margin=x, near=ps < 1,
                       p_select=ps, b_act=np.ones(n, bool), features=feats, q=cells, d=cells.copy(),
                       n_eligible={int(i): per_root for i in range(n_roots)}), theta


def test_fork_diffs_hand_computed():
    ft, _ = synthetic(n_roots=2, per_root=1)
    ft.d[0] = [[1.0, 3.0], [0.0, 4.0]]          # policy 0: mean 2, var 2; policy 1: mean 2, var 8
    dbar, se2 = F.fork_diffs(ft, "d")
    assert dbar[0] == pytest.approx(2.0) and se2[0] == pytest.approx((2 + 8) / (2 * 4))
    d0, s0 = F.fork_diffs(ft, "d", cont=1)
    assert d0[0] == pytest.approx(2.0) and s0[0] == pytest.approx(8 / 2)
    with pytest.raises(F.ForkError):
        F.fork_diffs(replace(ft, d=ft.d[:, :, :1], reps=1), "d")


@pytest.mark.parametrize("tau", [0.0, 0.8])
def test_tau2_unbiased_on_synthetic_tables(tau):
    est = [F.tau2_point(*F.fork_diffs(synthetic(tau=tau, seed=s)[0], "d"), synthetic(tau=tau, seed=s)[0].w)["tau2"]
           for s in range(300)]
    assert abs(np.mean(est) - tau ** 2) < 4 * np.std(est) / np.sqrt(len(est))


def test_tau2_interval_covers_zero_under_the_null():
    cover = []
    for s in range(60):
        ft, _ = synthetic(tau=0.0, seed=1000 + s)
        lo, hi = F.tau2(ft, "d", B=200, seed=s)["ci"]
        cover.append(lo <= 0.0 <= hi)
    assert np.mean(cover) >= 0.85


def test_n6_value_detects_learnable_sign_changes_and_not_noise():
    ft, _ = synthetic(q_slope=1.0, noise=0.5, seed=3)               # q = x + noise: act iff x > 0 is the gain
    v = F.n6_value(ft, B=100, seed=1)
    assert v["per_decision"] > 0.2 and v["ci_per_decision"][0] > 0 and 0.3 < v["flip_rate"] < 0.7
    ft0, _ = synthetic(q_slope=0.0, tau=0.0, noise=0.5, seed=4)
    ft0.q += 1.0                                                    # acting is always right: behaviour optimal
    v0 = F.n6_value(ft0, B=100, seed=1)
    assert v0["per_decision"] <= 1e-12 and v0["flip_rate"] < 0.05
    few = ft.subset(np.arange(len(ft)) < 40)                        # 5 roots: too few training forks per fold
    assert F.n6_value(few, B=0, min_train=50)["fallback_forks"] == len(few)


def test_bootstrap_copies_are_separate_clusters():
    rng = np.random.default_rng(0)
    inst = np.repeat(np.arange(5), 3)
    idx, cl = F._boot_index(inst, rng)
    assert len(idx) == 15 and len(np.unique(cl)) == 5
    for c in np.unique(cl):                                         # one drawn copy = one instance, 3 rows
        assert len(set(inst[idx[cl == c]])) == 1 and (cl == c).sum() == 3


# ---------------------------------------------------------------- E-SYN null world

def test_null_world_continuation_difference_has_no_heterogeneity():
    w, beh = WORLDS["strict_null"], n1("strict_null")
    ft = F.collect(w, beh, range(30), design("strict_null"), [beh, P.N0()], reps=2)
    t_d, t_q = F.tau2(ft, "d", B=200), F.tau2(ft, "q", B=200)
    assert t_d["ci"][0] <= 0.0 <= t_d["ci"][1]
    assert t_q["ci"][0] > 0                                         # the one-step value still varies
    dbar, se2 = F.fork_diffs(ft, "d")
    assert abs(F.fork_means(ft, "d")["hajek"]) < 4 * np.sqrt(se2.mean() / len(ft) * 4)


def test_n6_cross_fitting_never_uses_held_out_outcomes():
    """Exact: changing the outcomes of the forks in one fold leaves that fold's decisions unchanged (and changes
    other folds' decisions in general, since they train on it)."""
    ft, _ = synthetic(q_slope=1.0, noise=0.5, seed=5)
    rows = np.arange(len(ft))
    qbar = ft.q.mean(axis=(1, 2))
    fold = F._assign_folds(ft.instance, 5, np.random.default_rng([F.ANALYSIS_KEY, 2, 0]))
    base = F.n6_point(ft, rows, ft.instance, folds=5, alpha=1.0, min_train=10,
                      rng=np.random.default_rng([F.ANALYSIS_KEY, 2, 0]), qbar=qbar)
    for k in range(5):
        q2 = qbar.copy()
        q2[fold == k] = -100.0 * q2[fold == k] + 3.0
        alt = F.n6_point(ft, rows, ft.instance, folds=5, alpha=1.0, min_train=10,
                         rng=np.random.default_rng([F.ANALYSIS_KEY, 2, 0]), qbar=q2)
        assert np.array_equal(alt["act"][fold == k], base["act"][fold == k])
        assert not np.array_equal(alt["act"][fold != k], base["act"][fold != k])


def test_forks_from_a_stochastic_root():
    """A randomised behaviour policy (SPT-2 mixture component): the replay up to the fork point reproduces the
    root's draws, so every fork's first row equals the root's row, and both propensity replays pass."""
    w, beh, cont = WORLDS["budget"], P.RandomExec(0.6, 0.0), n1("budget")
    d = F.Design(q_uniform=0.3, q_oversample=0.0, band_e1=0.0, band_e2=0.0, g=0.0, h=0.0)
    ft = F.collect(w, beh, range(4), d, [cont], reps=2, record=True)
    assert len(ft) > 0
    rows = [S.from_dict(r) for r in ft.rows]
    assert S.check_campaign(rows, behaviour=dispatcher(beh, cont)) == []
    root = {(r.identity.campaign_id, r.identity.step_index): r for r in rows if not r.identity.branch_path}
    for r in rows:
        if r.identity.branch_path and r.action.forced:
            par = root[(r.identity.campaign_id, r.identity.step_index)]
            assert r.state == par.state and r.policy.behaviour_action == par.action.action
            assert r.policy.behaviour_prob == pytest.approx(par.policy.action_prob)
