"""Track S A2-U controller: update maths, predictive variance, (key, sign) groups, policies, rebuild, fit.

ENGINEERING_ONLY; AI-assisted (Claude, 29 Oct 2026). CPU fixtures, no LLM.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from r1.c3 import rules
from r1.c3.features import ReplayProposal, ReplayView, featurize_view
from r1.tests.c3_campaign_fixtures import NODE, SequenceBackend, node_context, run_campaign
from r1.tracks import a2u
from r1.tracks.schema import STATE_FEATURES

SIGMA = 0.005


def prior(mu0=0.001, tau0=0.004, sigma=SIGMA, tau_w=0.002) -> a2u.A2UPrior:
    return a2u.A2UPrior(node=NODE, sigma_node=SIGMA, kinds={"local": a2u.KindPrior(mu0, tau0, sigma, tau_w)})


def test_group_posterior_closed_form():
    kp = a2u.KindPrior(mu0=0.001, tau0=0.004, sigma_cmp=0.005, tau_w=0.002)
    assert a2u.group_posterior(kp, []) == (0.001, 0.004)
    d = [0.003, -0.001, 0.006]
    obs_var = 0.005 ** 2 + 0.002 ** 2
    prec = 1 / 0.004 ** 2 + 3 / obs_var
    mu, tau = a2u.group_posterior(kp, d)
    assert tau == pytest.approx(math.sqrt(1 / prec))
    assert mu == pytest.approx((0.001 / 0.004 ** 2 + sum(d) / obs_var) / prec)
    # Inflation lambda scales the observation variance only.
    mu2, tau2 = a2u.group_posterior(kp, d, obs_inflation=2.0)
    prec2 = 1 / 0.004 ** 2 + 3 / (2 * obs_var)
    assert tau2 == pytest.approx(math.sqrt(1 / prec2)) and tau2 > tau
    assert mu2 == pytest.approx((0.001 / 0.004 ** 2 + sum(d) / (2 * obs_var)) / prec2)


def test_posterior_mean_and_bayes_threshold_agree():
    mu, tau, sigma = 0.001, 0.003, 0.005
    t = float(rules.bayes_threshold(mu, tau, sigma))
    assert a2u.posterior_mean(t, mu, tau, sigma) == pytest.approx(0.0, abs=1e-15)
    for d in np.linspace(-0.02, 0.02, 41):
        assert (a2u.posterior_mean(d, mu, tau, sigma) > 0) == (d > t)


def test_sign_of():
    assert [a2u.sign_of(x) for x in (1.0, -1.0, 0.0, math.nan, None, "x")] == ["+", "-", "0", "0", "0", "0"]


STEPS = [("ALPHA", 2.0), ("ALPHA", 2.0), ("ALPHA", 0.5), ("LEARNING_RATE_INIT", 2.0), ("ALPHA", 4.0),
         ("ALPHA", 2.0), ("ALPHA", 2.0), ("ALPHA", 0.5), ("MAX_ITER", 2.0), ("ALPHA", 0.25)]


class StatusBackend:
    """Multiplies one key per trial, reading the current value from the status (never stale)."""

    mode, deterministic = "status_backend", True

    def __init__(self, steps=STEPS) -> None:
        self.steps, self.n = list(steps), 0

    def propose_next_trial(self, status, memory_context, node_spec):
        from autoresearch.manager.base import ManagerProposal
        key, factor = self.steps[self.n % len(self.steps)]
        self.n += 1
        old = status.current_constants[key]
        new = str(int(float(old) * factor)) if key == "MAX_ITER" else repr(float(old) * factor)
        return ManagerProposal(manager_mode=self.mode, proposal_summary=f"{key} {old} -> {new}", proposal_rationale="",
                               target_files=tuple(node_spec.editable_paths), objective=f"Change {key}.",
                               extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                                          "symbol": key, "old": old, "new": new}})


def _ledger(tmp_path, controller=None, budget=10):
    """A scripted campaign on digits_mlp; with the default controller every proposal is executed."""
    from autoresearch.control_plane.action_versions import KEEP_RULE_BAYES, ActionVersions
    kwargs = {}
    if controller is not None:
        kwargs = controller.campaign_kwargs(W=20, llm_cap=budget)
    else:
        from autoresearch.control_plane.budget import ComputeBudget
        kwargs = {"budget": budget, "compute_budget": ComputeBudget(max_worker_runs=20)}
    records, events, rows, worker = run_campaign(tmp_path, StatusBackend(), scale=0.01, **kwargs)
    return records, events, rows


def _view(rows, i):
    row = rows[i]
    return ReplayView(budget_index=row["budget_index"], ledger_prefix=tuple(rows[:i]),
                      current_best=row.get("current_best_before"),
                      proposal=ReplayProposal(extra={"structured_edit": row["extra"]["manager"]["structured_edit"]}))


def test_groups_are_key_and_sign_and_forecast_is_predictive(tmp_path):
    _, _, rows = _ledger(tmp_path)
    ctl = a2u.A2UController(prior(), node_context(SIGMA))
    for i in range(1, len(rows)):
        fc = ctl.forecast(_view(rows, i))
        rep = fc["rep"]
        # Expected group observations from an independent replay with featurize_view.
        expected = []
        for j in range(1, i):
            res = featurize_view(_view(rows, j), node_context(SIGMA))
            edit = rows[j]["extra"]["manager"]["structured_edit"]
            if (res is not None and not res.noop and not res.duplicate and rows[j]["decision"] != "skipped"
                    and edit["symbol"] == fc["key"] and a2u.sign_of(res.features["direction"]) == fc["sign"]):
                expected.append(rows[j]["delta_vs_best"])
        assert rep.deltas.get((fc["key"], fc["sign"]), []) == expected
        mu, tau_n = a2u.group_posterior(ctl.prior.kind("local"), expected)
        assert fc["mu"] == pytest.approx(mu)
        assert fc["tau"] == pytest.approx(math.sqrt(tau_n ** 2 + 0.002 ** 2))  # predictive, not tau_n alone
        assert fc["v_star"] == pytest.approx(float(rules.proposal_value(0.0, mu, fc["tau"], SIGMA)))
        res = featurize_view(_view(rows, i), node_context(SIGMA))
        assert (fc["noop"], fc["duplicate"]) == (res.noop, res.duplicate)  # A2's rule semantics


def test_a2u_campaign_decisions_follow_the_rule_and_rebuild_from_views(tmp_path):
    ctl = a2u.A2UController(prior(mu0=0.0005, tau0=0.003), node_context(SIGMA), g=0.0004)
    records, events, rows = _ledger(tmp_path, ctl)
    decisions = [e for e in events if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"]
    assert decisions
    rebuilt = a2u.A2UController(prior(mu0=0.0005, tau0=0.003), node_context(SIGMA), g=0.0004)
    for e in decisions:
        d = e["payload"]["detail"]
        if d.get("reason") == "no_features":
            continue
        if d["noop"] or d["duplicate"]:
            assert d["skip_reason"] in ("rule_noop", "rule_duplicate")
            continue
        assert d["execute"] == (d["v_star"] >= 0.0004)
        assert e["payload"]["action"] == ("continue" if d["execute"] else "skip")
    # Stateless: a fresh controller gives the same forecast on every executed row's view.
    for i in range(1, len(rows)):
        if rows[i]["decision"] == "skipped":
            continue
        a, b = ctl.forecast(_view(rows, i)), rebuilt.forecast(_view(rows, i))
        assert (a["mu"], a["tau"], a["v_star"]) == (b["mu"], b["tau"], b["v_star"])
    # Bayes keep with the updated predictive law.
    for e in events:
        if e["event_type"] == "decision_made" and (e["payload"].get("keep_rule") or {}).get("applied"):
            kr = e["payload"]["keep_rule"]
            assert kr["decision"] == ("kept" if kr["delta_hat"] > kr["threshold"] else "discarded")


def _e2_view(rows, i, used=3, left=7):
    from types import SimpleNamespace
    row = rows[i]
    v = _view(rows, i)
    return SimpleNamespace(epoch="E2", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                           current_best=v.current_best, proposal=v.proposal,
                           provisional=SimpleNamespace(delta_vs_best=row["delta_vs_best"]),
                           budget={"worker_runs_used": used, "worker_runs_remaining": left,
                                   "trials_remaining": 30, "trials_total": 40})


def test_policy_keep_rules_are_served_exactly_as_thresholds(tmp_path):
    _, _, rows = _ledger(tmp_path)
    ctx = node_context(SIGMA)
    view = _e2_view(rows, 4)
    base = a2u.A2UController(prior(), ctx)
    fc = base.forecast(view)
    mu, tau, sigma = fc["mu"], fc["tau"], fc["sigma"]
    kp = base.keep_prior(view)
    assert (kp.mu, kp.tau, kp.sigma) == (mu, tau, sigma)  # default: the plain Bayes threshold

    def keeps(ctl, d):
        return d > ctl.keep_prior(view).threshold

    static = a2u.A2UController.static_price(prior(), ctx, 0.001, e2_offset=0.002)
    c_hat = a2u.A2UController(prior(), ctx, c_hat=lambda s: -0.001 + 0.1 * s["index_value"] + 0.0001 * s["runs_left"])
    model = a2u.RidgeScore(intercept=-0.0005, coef={"index_value": 2.0, "runs_left": 0.0001, "e2": 0.0003})
    score = a2u.A2UController(prior(), ctx, score_fn=model)
    for d in np.linspace(-0.03, 0.03, 61):
        m = a2u.posterior_mean(d, mu, tau, sigma)
        assert keeps(static, d) == (m > 0.002)
        assert keeps(c_hat, d) == (m - 0.001 + 0.1 * m + 0.0001 * 7 > 0)
        assert keeps(score, d) == (-0.0005 + 2.0 * m + 0.0001 * 7 + 0.0003 > 0)
    bad = a2u.A2UController(prior(), ctx, score_fn=a2u.RidgeScore(0.0, {"index_value": -1.0}))
    with pytest.raises(ValueError, match="does not increase"):
        bad.keep_prior(view)
    nonlinear = a2u.A2UController(prior(), ctx, score_fn=lambda s: s["index_value"] ** 3)
    with pytest.raises(ValueError, match="not affine"):
        nonlinear.keep_prior(view)


def test_dynamic_family_reduces_exactly_to_static_and_uses_worker_run_budget(tmp_path):
    from types import SimpleNamespace
    _, _, rows = _ledger(tmp_path)
    ctx = node_context(SIGMA)
    budget = {"worker_runs_used": 4, "worker_runs_remaining": 6, "trials_remaining": 30, "trials_total": 40,
              "llm_calls_remaining": 32, "llm_calls_used": 8}
    static = a2u.A2UController.static_price(prior(), ctx, 0.0003, e2_offset=0.0005)
    zero = a2u.A2UController.dynamic(prior(), ctx, g0=0.0003, h0=0.0005)
    assert zero.version == static.version
    dyn = a2u.A2UController.dynamic(prior(), ctx, g0=0.0003, b_budget=0.002, b_info=0.5, h0=0.0005, h_budget=0.001)
    gap = 6 / 10 - 30 / 40  # runs_left / W - proposals_left / N_cap
    for i in range(1, len(rows)):
        v = _view(rows, i)
        e1 = SimpleNamespace(epoch="E1", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                             current_best=v.current_best, proposal=v.proposal, provisional=None, budget=budget,
                             input_hash=lambda: "h")
        e2 = SimpleNamespace(**{**vars(e1), "epoch": "E2",
                                "provisional": SimpleNamespace(delta_vs_best=rows[i]["delta_vs_best"])})
        a, b = static.decide(e1, {"continue": True, "skip": True}), zero.decide(e1, {"continue": True, "skip": True})
        assert (a.action, a.detail) == (b.action, b.detail)
        assert static.keep_prior(e2) == zero.keep_prior(e2)
        fc = dyn.forecast(e1)
        if fc is None or fc["noop"] or fc["duplicate"]:
            continue
        bonus = 0.5 * fc["tau"]  # rev. 6: b_info multiplies tau_pred directly (no new-group indicator)
        d = dyn.decide(e1, {"continue": True, "skip": True})
        assert d.detail["budget_gap"] == pytest.approx(gap)
        assert d.detail["execute"] == (fc["v_star"] + bonus >= 0.0003 - 0.002 * gap)
        thr = dyn.keep_prior(e2).threshold
        for delta in np.linspace(-0.02, 0.02, 21):
            m = a2u.posterior_mean(delta, fc["mu"], fc["tau"], fc["sigma"])
            assert (delta > thr) == (m > 0.0005 - 0.001 * gap)
    # h_budget takes both signs.
    neg = a2u.A2UController.dynamic(prior(), ctx, g0=0.0003, h0=0.0005, h_budget=-0.001)
    v = _view(rows, 4)
    e2 = SimpleNamespace(epoch="E2", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                         current_best=v.current_best, proposal=v.proposal, budget=budget,
                         provisional=SimpleNamespace(delta_vs_best=rows[4]["delta_vs_best"]))
    fc = neg.forecast(e2)
    for delta in np.linspace(-0.02, 0.02, 21):
        m = a2u.posterior_mean(delta, fc["mu"], fc["tau"], fc["sigma"])
        assert (delta > neg.keep_prior(e2).threshold) == (m > 0.0005 + 0.001 * gap)


def test_budget_member_lowers_the_threshold_when_runs_are_plentiful():
    """Runbook D1' example: N = 2 proposals, K = 1 run, V* in {1, 3}. After a skip at trial 1 the run is
    still available for the last proposal: r = 1/1 - 1/2 > 0, so b_budget > 0 lowers the trial-2 threshold."""
    from types import SimpleNamespace
    # rev. 6.1 convention: proposals_left includes the current proposal; r is evaluated before the decision.
    # Proposal 1 (its manager call charged, trial not yet consumed): r = 1/1 - 2/2 = 0.
    first = {"worker_runs_used": 0, "worker_runs_remaining": 1, "trials_remaining": 2, "trials_total": 2,
             "llm_calls_remaining": 1, "llm_calls_used": 1}
    assert a2u.budget_gap(SimpleNamespace(budget=first)) == 0.0
    # The same with a scripted manager (no LLM call counted): the trial budget counts the proposals.
    scripted = {**first, "llm_calls_remaining": 2, "llm_calls_used": 0}
    assert a2u.budget_gap(SimpleNamespace(budget=scripted)) == 0.0
    # Proposal 2 after a skip at proposal 1: r = 1/1 - 1/2 = +0.5.
    budget = {"worker_runs_used": 0, "worker_runs_remaining": 1, "trials_remaining": 1, "trials_total": 2,
              "llm_calls_remaining": 0, "llm_calls_used": 2}
    view = SimpleNamespace(budget=budget)
    r = a2u.budget_gap(view)
    assert r == 0.5
    g0, b = 2.0, 2.0
    assert g0 - b * r < g0  # the budget member's threshold is below the static one
    # V* = 1 is skipped by the static rule at g0 = 2 but executed by the budget member (threshold 1),
    # which is optimal here: the only remaining run is otherwise wasted.
    assert not (1.0 >= g0) and (1.0 >= g0 - b * r)
    # Scarce runs: the same member raises the threshold (r < 0).
    scarce = {"worker_runs_used": 1, "worker_runs_remaining": 0, "trials_remaining": 1, "trials_total": 2,
              "llm_calls_remaining": 0, "llm_calls_used": 2}
    assert a2u.budget_gap(SimpleNamespace(budget=scarce)) < 0


def test_e1_score_policies_and_worker_run_state(tmp_path):
    from types import SimpleNamespace
    _, _, rows = _ledger(tmp_path)
    v = _view(rows, 5)
    view = SimpleNamespace(epoch="E1", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                           current_best=v.current_best, proposal=v.proposal, provisional=None,
                           budget={"worker_runs_used": 4, "worker_runs_remaining": 6, "trials_remaining": 30,
                                   "trials_total": 40},
                           input_hash=lambda: "h")
    seen = []
    ctl = a2u.A2UController(prior(), node_context(SIGMA), c_hat=lambda s: seen.append(s) or 1.0)
    dec = ctl.decide(view, {"continue": True, "skip": True})
    assert dec.action == "continue" and dec.detail["score"] == pytest.approx(dec.detail["v_star"] + 1.0)
    state = seen[0]
    assert tuple(k for k in state if k not in ("epoch",) + a2u.POLICY_EXTRA_FEATURES) == STATE_FEATURES
    assert state["epoch"] == "E1"
    assert state["runs_left"] == 6.0 and state["budget_fraction"] == pytest.approx(0.4)  # worker runs, not trials
    neg = a2u.A2UController(prior(), node_context(SIGMA), score_fn=a2u.RidgeScore(-1.0, {}))
    dec = neg.decide(view, {"continue": True, "skip": True})
    assert dec.action == "skip" and dec.detail["skip_reason"] == "prior_no_gain"


def test_no_update_is_a2(tmp_path):
    _, _, rows = _ledger(tmp_path)
    a2 = a2u.A2UController(prior(), node_context(SIGMA), update=False)
    vals = {round(a2.forecast(_view(rows, i))["v_star"], 15) for i in range(1, len(rows))}
    assert len(vals) == 1  # one constant per (node, kind)


def test_prior_file_roundtrip_and_sha(tmp_path):
    p = prior()
    sha = p.save(tmp_path / "prior.json")
    assert sha == p.sha256
    import hashlib
    assert hashlib.sha256((tmp_path / "prior.json").read_bytes()).hexdigest() == sha
    q = a2u.A2UPrior.load(tmp_path / "prior.json", expect_sha256=sha)
    assert q == p
    with pytest.raises(ValueError):
        a2u.A2UPrior.load(tmp_path / "prior.json", expect_sha256="0" * 64)
    (tmp_path / "bad.json").write_text(json.dumps(p.to_payload()))  # not canonical
    with pytest.raises(ValueError, match="canonical"):
        a2u.A2UPrior.load(tmp_path / "bad.json")


def test_fit_prior_recovers_simulated_moments():
    rng = np.random.default_rng(7)
    rows = []
    for inst in range(30):
        for key in ("ALPHA", "MAX_ITER"):
            for sign in "+-":
                m = rng.normal(0.001, 0.003)
                for _ in range(3):
                    delta = rng.normal(m, 0.002)
                    rows.append({"instance": f"i{inst}", "key": key, "sign": sign, "kind": "local",
                                 "delta_audit": delta + rng.normal(0, 0.0005), "se": 0.0005,
                                 "delta_hat": delta + rng.normal(0, 0.005)})
    fit = a2u.fit_prior(rows, NODE, 0.005, k_label=5)
    kp = fit.kinds["local"]
    assert kp.sigma_cmp == pytest.approx(0.005, rel=0.15)
    assert kp.tau_w == pytest.approx(0.002, rel=0.25)
    assert kp.mu0 == pytest.approx(0.001, abs=0.0015)
    # Before any observation the predictive sd equals A2's node prior sd.
    assert math.hypot(kp.tau0, kp.tau_w) == pytest.approx(fit.meta["stats"]["local"]["tau_a2"], rel=1e-9)
    none = a2u.fit_prior(rows, NODE, 0.005, k_label=5, within_key="none")
    assert none.kinds["local"].tau_w == 0.0
    with pytest.raises(ValueError):
        a2u.fit_prior(rows[:3], NODE, 0.005, k_label=5)


def test_predictive_intervals_and_coverage(tmp_path):
    _, _, rows = _ledger(tmp_path)
    ctl = a2u.A2UController(prior(), node_context(SIGMA))
    ivs = a2u.predictive_intervals(rows, ctl, level=0.8, audit_se={r["budget_index"]: 0.001 for r in rows})
    assert ivs and all(iv["lo"] < iv["mu"] < iv["hi"] for iv in ivs)
    for iv in ivs:
        fc = ctl.forecast(_view(rows, [r["budget_index"] for r in rows].index(iv["budget_index"])))
        sd = math.sqrt(fc["tau"] ** 2 + 0.001 ** 2)
        assert iv["hi"] - iv["mu"] == pytest.approx(1.2815515655446004 * sd)
    audited = {iv["budget_index"]: iv["mu"] for iv in ivs}
    assert a2u.coverage(ivs, audited)["coverage"] == 1.0
    audited = {iv["budget_index"]: iv["hi"] + 1 for iv in ivs}
    assert a2u.coverage(ivs, audited)["coverage"] == 0.0


def test_d1_prime_controller_decision_and_centred_terms(tmp_path):
    """Review m9: the D1' instance through ``A2UController.decide``. N = 2 proposals, K = 1 run: at proposal 1
    r = 0 and the budget member decides as static; at proposal 2 after a skip r = +0.5 and the budget member
    executes a proposal that static (at the same g0, just above its V*) skips. Rev. 7 (b): centring at
    r1bar = 0.5 restores the static decision there."""
    from types import SimpleNamespace
    _, _, rows = _ledger(tmp_path)
    ctx = node_context(SIGMA)
    v = _view(rows, 3)
    proposal_1 = {"worker_runs_used": 0, "worker_runs_remaining": 1, "trials_remaining": 2, "trials_total": 2,
                  "llm_calls_remaining": 1, "llm_calls_used": 1}
    proposal_2 = {"worker_runs_used": 0, "worker_runs_remaining": 1, "trials_remaining": 1, "trials_total": 2,
                  "llm_calls_remaining": 0, "llm_calls_used": 2}

    def view(budget):
        return SimpleNamespace(epoch="E1", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                               current_best=v.current_best, proposal=v.proposal, provisional=None, budget=budget,
                               input_hash=lambda: "h")

    fc = a2u.A2UController(prior(), ctx).forecast(view(proposal_1))
    assert not fc["noop"] and not fc["duplicate"]
    g0 = fc["v_star"] + 1e-5  # static skips this proposal
    static = a2u.A2UController.static_price(prior(), ctx, g0)
    budget = a2u.A2UController.dynamic(prior(), ctx, g0=g0, b_budget=1e-3)
    centred = a2u.A2UController.dynamic(prior(), ctx, g0=g0, b_budget=1e-3, r1_bar=0.5)
    mask = {"continue": True, "skip": True}
    d1 = budget.decide(view(proposal_1), mask)
    assert d1.detail["budget_gap"] == 0.0 and d1.action == static.decide(view(proposal_1), mask).action == "skip"
    d2 = budget.decide(view(proposal_2), mask)
    assert d2.detail["budget_gap"] == 0.5 and d2.detail["e1_threshold"] == pytest.approx(g0 - 0.5e-3)
    assert static.decide(view(proposal_2), mask).action == "skip" and d2.action == "continue"
    c2 = centred.decide(view(proposal_2), mask)
    assert c2.detail["e1_threshold"] == pytest.approx(g0) and c2.action == "skip"
    # tau_bar centres the information bonus: b_info (tau - tau_bar) = 0 at tau_bar = tau.
    info = a2u.A2UController.dynamic(prior(), ctx, g0=g0, b_info=1.0, tau_bar=fc["tau"])
    assert info.decide(view(proposal_1), mask).detail["info_bonus"] == pytest.approx(0.0, abs=1e-15)
    assert a2u.A2UController.dynamic(prior(), ctx, g0=g0, b_info=1.0).decide(view(proposal_1), mask).action == "continue"


def test_predictive_intervals_carry_n_group_strata(tmp_path):
    _, _, rows = _ledger(tmp_path)
    ivs = a2u.predictive_intervals(rows, a2u.A2UController(prior(), node_context(SIGMA)))
    assert {"n_group", "stratum"} <= set(ivs[0])
    assert all(iv["stratum"] == a2u.n_group_stratum(iv["n_group"]) for iv in ivs)
    assert [a2u.n_group_stratum(n) for n in (0, 1, 2, 3, 7)] == ["0", "1-2", "1-2", ">=3", ">=3"]
    cov = a2u.coverage(ivs, {iv["budget_index"]: iv["mu"] for iv in ivs})
    assert cov["coverage"] == 1.0 and all(v["coverage"] == 1.0 for v in cov["by_stratum"].values())


def test_per_group_priors_override_the_kind_prior(tmp_path):
    _, _, rows = _ledger(tmp_path)
    base = prior()
    special = a2u.KindPrior(mu0=0.01, tau0=1e-6, sigma_cmp=SIGMA, tau_w=0.001)
    grouped = a2u.A2UPrior(node=NODE, sigma_node=SIGMA, kinds=base.kinds, groups={"ALPHA|+": special})
    ctl, plain = a2u.A2UController(grouped, node_context(SIGMA)), a2u.A2UController(base, node_context(SIGMA))
    for i in range(1, len(rows)):
        fa, fb = ctl.forecast(_view(rows, i)), plain.forecast(_view(rows, i))
        if fa["key"] == "ALPHA" and fa["sign"] == "+" and fa["n_group"] == 0:
            assert fa["mu"] == pytest.approx(0.01) and fb["mu"] == pytest.approx(0.001)
        elif fa["key"] != "ALPHA":
            assert fa["mu"] == fb["mu"]
    q = a2u.A2UPrior.from_payload(json.loads(grouped.canonical_bytes()))
    assert q == grouped and "groups" in grouped.to_payload() and "groups" not in base.to_payload()


def test_operators_execute_ge_keep_gt_and_g0_executes_zero_index(tmp_path):
    """Rev. 7.1 m9: execute uses >= and keep uses > in every policy (static, dynamic, the matched static, A2-U);
    ``static:0,h`` executes a proposal whose V* is exactly 0."""
    from types import SimpleNamespace
    from r1.tracks import collect as C
    _, _, rows = _ledger(tmp_path)
    ctx = node_context(SIGMA)
    v = _view(rows, 3)
    budget = {"worker_runs_used": 1, "worker_runs_remaining": 9, "trials_remaining": 38, "trials_total": 40,
              "llm_calls_remaining": 37, "llm_calls_used": 3}
    view = SimpleNamespace(epoch="E1", budget_index=v.budget_index, ledger_prefix=v.ledger_prefix,
                           current_best=v.current_best, proposal=v.proposal, provisional=None, budget=budget,
                           input_hash=lambda: "h")
    mask = {"continue": True, "skip": True}
    base = a2u.A2UController(prior(), ctx).forecast(view)
    assert not base["noop"] and not base["duplicate"]
    zero = {**base, "mu": -1.0, "tau": 1e-9, "tau_n": 0.0, "sigma": SIGMA, "v_star": 0.0}
    assert float(a2u.rules.proposal_value(0.0, -1.0, 1e-9, SIGMA)) == 0.0  # V* underflows to exactly 0

    def ctl(policy):
        c = C.policy_controller(policy, prior(), ctx, g0=0.0, W=10)
        return c

    for pol in ("static:0,0", "static:0,0.00165", "dynamic:0,0,0,0,0", "dynamic:0,0,0,0,0,0.3,0.004,0.2", "a2u"):
        c = ctl(pol)
        c.forecast = lambda _view, fc=zero: fc
        assert c.decide(view, mask).action == "continue", pol  # V* = 0 >= g = 0: executed
    # ">=" at a tie for the dynamic rule: V* + b_info (tau - taubar) == g0 - b_budget (r - r1bar)
    r = a2u.budget_gap(view, 10)
    vs = base["v_star"]
    exact = a2u.A2UController.dynamic(prior(), ctx, g0=vs, b_budget=0.002, r1_bar=r, W=10)
    assert exact.decide(view, mask).action == "continue"          # equality executes
    above = a2u.A2UController.dynamic(prior(), ctx, g0=vs + 1e-12, b_budget=0.002, r1_bar=r, W=10)
    assert above.decide(view, mask).action == "skip"
    st = a2u.A2UController.static_price(prior(), ctx, vs)
    assert st.decide(view, mask).action == "continue"              # static: V* >= g at equality
    # keep ">": delta_hat exactly at the threshold is discarded, every policy's keep prior
    from autoresearch.control_plane.action_versions import bayes_keep as bayes_keep_decision
    for pol in ("static:0,0", "static:0,0.00165", "dynamic:0,0,0,0.00165,0.0033,0.3,0.004,0.2", "a2u"):
        kp = C.policy_controller(pol, prior(), ctx, g0=0.0, W=10).keep_prior(
            SimpleNamespace(**{**vars(view), "epoch": "E2"}))
        assert not bayes_keep_decision(kp.threshold, kp) and bayes_keep_decision(kp.threshold + 1e-12, kp), pol
