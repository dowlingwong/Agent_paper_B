"""Track S analysis tests (r1/tracks/analyze.py). CPU, fast, unittest style. AI-assisted (Claude, 29 Oct 2026)."""
from __future__ import annotations

import copy
import json
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from r1.tracks import analyze as A
from r1.tracks import simulate_controls as S
from r1.tracks.schema import STATE_FEATURES


def pd_fork(B: int = 40, **kw) -> A.Predeclaration:
    nd = A.NodeDecl("planted", "primary", 0.0033, k_n=20.0, sigma_node=0.0066,
                    sizing=A.SizingDecl(0.009, 300), sigma_cmp_vary=0.0066)
    return A.Predeclaration(nodes={"planted": nd}, primary_nodes=["planted"], bootstrap_B=B, fallback_active=True,
                            **kw)


def fork_result(leaves, B: int = 40) -> dict:
    ft = A.build_fork_table("planted", leaves)
    return A.analyze_forks(ft, pd_fork(B).nodes["planted"], pd_fork(B))


# ----------------------------------------------------------------------------------------------- fork level
class ForkLevelTests(unittest.TestCase):
    def test_null_continuation_gives_no_fork_level_gain(self):
        lv = S.planted_forks(n_instances=40, forks_per_instance=12, sigma=0.002, seed=1)
        r = fork_result(lv)
        tq = r["estimates"]["TQ_pi_vs_mtilde"]
        self.assertLess(tq["lb95"], 0.0005)
        self.assertLess(abs(r["estimates"]["hybrid_I_seq"]["est"]), 0.0005)
        self.assertEqual(r["label"], "FIXTURE")

    def test_planted_state_dependent_continuation_is_found(self):
        # executing pays later only while many runs are left (information / budget style), keeping marginal
        # edits pays later (feedback): pi' must beat the value-tuned immediate-only rule m~ on total Q
        lv = S.planted_forks(n_instances=40, forks_per_instance=15, sigma=0.0015, seed=2,
                             info=lambda s: 0.006 * (s["runs_left"] - 5.0) / 4.0,
                             e2_keep=lambda s: 0.004 * (1.0 if s["keeps_so_far"] <= 2 else -1.0))
        r = fork_result(lv)
        self.assertGreater(r["estimates"]["TQ_pi_vs_mtilde"]["lb95"], 0.0)

    def test_no_credit_for_one_step_miscalibration(self):
        # the base controller's immediate forecast is wrong (true immediate = forecast + 0.004 on seen keys),
        # continuation is null: the forecast + continuation score must not credit anything
        lv = S.planted_forks(n_instances=40, forks_per_instance=12, sigma=0.002, seed=3,
                             index_bias=lambda s, ep: 0.004 * s["key_seen"])
        r = fork_result(lv)
        self.assertLess(abs(r["estimates"]["hybrid_I_seq"]["est"]), 0.0005)
        self.assertLess(r["estimates"]["hybrid_I_seq"]["lb95"], 0.0002)

    def test_bad_keep_followed_by_recovery_is_not_credited(self):
        # E2: keeping costs −0.010 immediately and recovers +0.008 later (net −0.002); the forecast m-hat ~ 0.
        # The revision-3 hybrid score (forecast + continuation) credits keeping; total-Q analyses must not.
        lv = S.planted_forks(n_instances=40, forks_per_instance=12, share_e1=0.0, sigma=0.001, seed=4,
                             e2_keep=0.008, index_bias=lambda s, ep: -0.010 - s["index_value"])
        r = fork_result(lv)
        est = r["estimates"]
        self.assertGreater(est["hybrid_I_seq"]["lb95"], 0.002)       # the old score credits a harmful policy
        self.assertLess(est["TQ_pi_vs_mtilde"]["est"], 0.0005)       # total Q does not
        ft = A.build_fork_table("planted", lv)
        pol = A.fit_policies(ft, pd_fork())["pi_prime"]
        acts = [A.policy_act(pol, {k: float(x) for k, x in zip(STATE_FEATURES, ft.X[i])}, "E2") for i in range(50)]
        self.assertLess(np.mean(acts), 0.2)                          # pi' discards
        # campaign level: a policy that keeps these edits loses 0.002 per event; the S3e test must not say A
        rng = np.random.default_rng(0)
        D = -0.002 * rng.poisson(3, 60) + rng.normal(0, 0.008, 60)
        self.assertNotIn(A.campaign_route(A.mean_test(D), 0.0033), ("A", "A-small"))

    def test_ghat_refit_per_fold_and_per_replicate(self):
        lv = S.planted_forks(n_instances=30, forks_per_instance=10, sigma=0.002, seed=5, budget=0.002)
        ft = A.build_fork_table("planted", lv)
        pd = pd_fork()
        fmap = A.assign_folds(ft.instance.tolist(), 5, np.random.default_rng(1))
        fold = np.array([fmap[k] for k in ft.instance])
        _, ghat_row, ghats = A.cross_fit_hybrid(ft.X, ft.e1, ft.index, ft.dbar, ft.w, fold, 5, pd.ridge_alpha,
                                                pd.interactions)
        for k in range(5):
            tr = (fold != k) & ft.e1
            self.assertAlmostEqual(ghats[k], -np.sum(ft.w[tr] * ft.dbar[tr]) / ft.w[tr].sum(), places=12)
        boot = A.refitting_bootstrap(ft, pd)
        self.assertGreater(np.std(boot["draws"]["hybrid_ghat"]), 0.0)
        self.assertGreater(np.std(boot["draws"]["g_tilde"]) + np.std(boot["draws"]["h_tilde"]), 0.0)

    def test_duplicated_clusters_share_a_fold(self):
        keys = np.array(["a", "a", "b", "c", "c", "d", "e", "f"])
        fmap = A.assign_folds(keys.tolist(), 3, np.random.default_rng(0))
        self.assertEqual(len(fmap), 6)

    def test_u_split_unbiased_for_its_estimand_under_null(self):
        rng = np.random.default_rng(7)
        n, reps = 400, 300
        mu = rng.normal(0, 0.002, n)                 # true mean score difference per fork (no continuation)
        idx = mu.copy()
        m_act = idx > 0.0005                         # some fixed comparator
        w = np.ones(n)
        est, truth, hind = [], [], []
        for _ in range(reps):
            d = rng.normal(0, 0.004, (n, 2))         # continuation noise, mean 0 (null)
            u, _ = A.u_split(idx, d, m_act, w)
            est.append(u)
            s1, s2 = idx + d[:, 0], idx + d[:, 1]
            a1, a2 = s1 > 0, s2 > 0
            tv = 0.5 * ((a1 != m_act) * np.where(a1, 1, -1) * mu + (a2 != m_act) * np.where(a2, 1, -1) * mu)
            truth.append(tv.mean())
            hind.append((((s1 > 0) != m_act) * np.where(s1 > 0, 1, -1) * s1).mean())
        se = np.std(np.array(est) - np.array(truth)) / math.sqrt(reps)
        self.assertLess(abs(np.mean(est) - np.mean(truth)), 4 * se + 1e-6)
        self.assertGreater(np.mean(hind), np.mean(truth) + 10 * se)  # the hindsight version is biased upward

    def test_host_mixing_is_refused(self):
        lv = S.planted_forks(n_instances=6, forks_per_instance=3, seed=8)
        lv[0] = replace(lv[0], provenance=replace(lv[0].provenance, host="TASL-7"))
        with self.assertRaises(A.HostMixingError):
            A.build_fork_table("planted", lv)
        r = S.make_campaign_root("planted", "c0", "static:0,0", 0, 0.9, W=10, llm_cap=40, host="TASL-2")
        with self.assertRaises(A.HostMixingError):
            A.check_hosts("planted", S.planted_forks(n_instances=2, forks_per_instance=1, seed=9), [r])

    def test_policy_serialisation_round_trip(self):
        lv = S.planted_forks(n_instances=12, forks_per_instance=6, seed=10, budget=0.001)
        ft = A.build_fork_table("planted", lv)
        pols = A.fit_policies(ft, pd_fork())
        with tempfile.TemporaryDirectory() as d:
            sha = A.write_policy(pols["pi_prime"], Path(d) / "p.json")
            back = A.load_policy(Path(d) / "p.json", sha)
            with self.assertRaises(A.TrackSAnalysisError):
                A.load_policy(Path(d) / "p.json", "0" * 64)
        fast = S.LinearPolicy(back)
        for i in range(20):
            st = {k: float(x) for k, x in zip(STATE_FEATURES, ft.X[i])}
            ep = "E1" if ft.e1[i] else "E2"
            self.assertAlmostEqual(A.policy_score(back, st, ep), fast.score(st, ep), places=12)


# ----------------------------------------------------------------------------------------------- campaign level
class SizingAndGateTests(unittest.TestCase):
    def test_n_helper(self):
        self.assertEqual(A.campaign_n(0.01, 0.0033), math.ceil((2.93 * 0.01 / 0.0033) ** 2))
        u = A.sigma_D_ucl(0.008, 20)
        from scipy.stats import chi2
        self.assertAlmostEqual(u, 0.008 * math.sqrt(19 / chi2.ppf(0.2, 19)), places=12)
        self.assertGreater(u, 0.008)
        sz = A.plan_sizing(A.SizingDecl(0.009, 300), 0.0033, dev_ucl=0.012)
        self.assertEqual(sz["sigma_D_ucl"], 0.012)                      # max of S0.5b and S0.7
        self.assertEqual(sz["n_formula"], A.campaign_n(0.012, 0.0033))    # reported only (rev 7.2)
        self.assertEqual(sz["n_run_target"], 300)                         # n fixed at 300 whatever the formula
        self.assertFalse(sz["below_rev72_n"])
        big = A.plan_sizing(A.SizingDecl(0.03), 0.0033, dev_ucl=None)
        self.assertGreater(big["n_formula"], 300)
        self.assertEqual(big["n_run_target"], 300)
        self.assertTrue(A.plan_sizing(A.SizingDecl(0.03, 100), 0.0033, None)["below_rev72_n"])
        self.assertAlmostEqual(big["mde_at_run"], 2.93 * 0.03 / math.sqrt(300))
        self.assertGreater(big["mde_at_run"], 0.0033)

    def test_fp_gate_count_rule(self):
        self.assertTrue(A.fp_gate(19, 200)["stop"])
        self.assertFalse(A.fp_gate(18, 200)["stop"])
        self.assertAlmostEqual(A.fp_gate(18, 200)["p_binom"], 0.01209, places=4)
        self.assertLess(A.fp_gate(19, 200)["p_binom"], 0.01)
        self.assertTrue(A.fp_gate(9, 50)["stop"] == (A.fp_gate(9, 50)["p_binom"] < 0.01))

    def test_power_report_and_s06_controls(self):
        pr = A.power_report(150, 200)
        self.assertAlmostEqual(pr["power"], 0.75)
        self.assertTrue(pr["ci95"][0] < 0.75 < pr["ci95"][1])
        self.assertNotIn("ok", pr)                                        # reported, never gated
        self.assertEqual({(k, v, m) for k, v, m in A.S06_CONTROLS},
                         {("P2+", "diffuse", 1.0), ("P2+", "concentrated", 1.0), ("P1", "diffuse", 2.0)})
        self.assertEqual(len(A.S06_UNMEASURED), 3)
        self.assertFalse(hasattr(A, "resize_rule"))

    def test_freeze_check(self):
        sz = A.plan_sizing(A.SizingDecl(0.009, 300), 0.0033, None)
        self.assertFalse(A.freeze_check(sz, {"n": sz["n_run_target"]})["rerun_s06"])
        self.assertTrue(A.freeze_check(sz, {"n": sz["n_run_target"] + 5})["rerun_s06"])
        self.assertTrue(A.freeze_check(sz, None)["rerun_s06"])

    def test_holm_by_p_value(self):
        h = A.holm_by_p({"a": 0.03, "b": 0.01}, 0.05)
        self.assertEqual(h["b"]["rank"], 1)
        self.assertAlmostEqual(h["b"]["alpha_level"], 0.025)
        self.assertTrue(h["b"]["rejected"] and h["a"]["rejected"])
        h = A.holm_by_p({"a": 0.03, "b": 0.026}, 0.05)
        self.assertFalse(h["b"]["rejected"] or h["a"]["rejected"])     # step-down stops at the first
        h = A.holm_by_p({"a": 0.06, "b": 0.02}, 0.05)
        self.assertTrue(h["b"]["rejected"])
        self.assertFalse(h["a"]["rejected"])

    def test_mean_test_and_routes(self):
        rng = np.random.default_rng(1)
        t = A.mean_test(0.01 + rng.normal(0, 0.005, 60))
        self.assertGreater(t["lb"], 0)
        self.assertEqual(A.campaign_route(t, 0.0033), "A")
        t = A.mean_test(0.001 + rng.normal(0, 0.0005, 80))
        self.assertEqual(A.campaign_route(t, 0.0033), "A-small")
        t = A.mean_test(rng.normal(0, 0.002, 80))
        self.assertEqual(A.campaign_route(t, 0.0033), "no gain found")


def _roots(node, pol, ys, rep=0, phase="campaign", suffix="", inst_prefix="c", host=S.SIM_HOST):
    return [S.make_campaign_root(node, f"{inst_prefix}{k:04d}", pol, rep, y, W=10, llm_cap=40, phase=phase,
                                 suffix=suffix, host=host) for k, y in enumerate(ys)]


class PlaceboTests(unittest.TestCase):
    def test_exact_placebo(self):
        r = _roots("n", "static:0.001,0", [0.9, 0.91]) + _roots("n", "static:0.001,0", [0.9, 0.91], suffix="dup")
        self.assertEqual(A.placebo_exact(r, "static:0.001,0")["status"], "pass")
        r[-1] = S.make_campaign_root("n", "c0001", "static:0.001,0", 0, 0.9100001, W=10, llm_cap=40, suffix="dup")
        self.assertEqual(A.placebo_exact(r, "static:0.001,0")["status"], "STOP")
        self.assertEqual(A.placebo_exact(r[:2], "static:0.001,0")["status"], "missing")
        ok = _roots("n", "p", [0.9] * 4) + _roots("n", "p", [0.9] * 4, suffix="dup")
        self.assertEqual(A.placebo_exact(ok, "p", min_groups=10)["status"], "insufficient")

    def test_descriptive_placebo(self):
        rng = np.random.default_rng(2)
        y1 = 0.9 + rng.normal(0, 0.005, 60)
        y2 = 0.9 + rng.normal(0, 0.005, 60)
        r = _roots("n", "p", y1, 0) + _roots("n", "p", y2, 1)   # rep 0 (primary) vs rep 1 (final review MAJOR 2)
        d = A.placebo_descriptive(r, "p")
        self.assertEqual(d["status"], "pass")
        r = _roots("n", "p", y1, 0) + _roots("n", "p", y1 - 0.004, 1)
        self.assertEqual(A.placebo_descriptive(r, "p")["status"], "STOP")
        r = _roots("n", "p", y1, 1) + _roots("n", "p", y2, 2)       # reps 1 and 2 are not the placebo pair
        self.assertEqual(A.placebo_descriptive(r, "p")["status"], "missing")
        r = _roots("n", "p", y1, 0) + _roots("n", "p", y1 - 0.004, 1)
        self.assertEqual(A.placebo_descriptive(r, "p")["status"], "STOP")


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.fam = A.FamilyDecl()
        self.sn = 0.0066
        self.nd = A.NodeDecl("n", "primary", 0.0033, sigma_node=self.sn, sizing=A.SizingDecl(0.009, 300),
                             sigma_cmp_vary=self.sn)
        self.pd = A.Predeclaration(nodes={"n": self.nd}, primary_nodes=["n"], fallback_active=True,
                                   winners_curse_splits=20)

    def _dev(self, means: dict[str, float], n=20, decisions=None):
        rng = np.random.default_rng(3)
        out = []
        base = rng.normal(0, 0.004, n)
        for c, m in means.items():
            rs = _roots("n", c, 0.9 + m + base + rng.normal(0, 1e-4, n), phase="dev_tuning", inst_prefix="d")
            if decisions and c in decisions:
                for r in rs:
                    r.decisions.extend(decisions[c])
            out += rs
        return out

    def test_two_stage_selection_edge_extension_centring_flip_and_matched_static(self):
        stat = self.fam.static_configs(self.sn)
        self.assertEqual(len(stat), 15)
        means = {c: 0.0 for c in stat}
        edge = A.policy_string("static", (0.4 * self.sn, 0.0))
        means[edge] = 0.002                                            # m* on the upper g edge
        m_dec = [{"index": 3, "epoch": "E1", "eligible": True, "index_value": 0.003, "r": 0.2,
                  "tau_pred": 0.004, "action": "execute"},
                 {"index": 4, "epoch": "E1", "eligible": True, "index_value": 0.001, "r": 0.4,
                  "tau_pred": 0.006, "action": "skip"},
                 {"index": 3, "epoch": "E2", "eligible": True, "index_value": 0.001, "r": 0.1,
                  "action": "keep"}]
        dev = self._dev(means)
        sel = A.selection_report(dev, self.pd, self.nd)
        self.assertEqual(sel["status"], "extension_needed")
        self.assertEqual(len(sel["extension_configs"]), 3)
        dev += self._dev({c: 0.001 for c in sel["extension_configs"]})
        dev = [r for r in dev if A.policy_of(r) != edge] + self._dev({edge: 0.002}, decisions={edge: m_dec})
        sel = A.selection_report(dev, self.pd, self.nd)
        self.assertEqual(sel["status"], "members_needed")
        self.assertEqual(sel["m_star"], edge)
        c = sel["centres"]
        self.assertAlmostEqual(c["r1bar"], 0.3)                        # mean r over m*'s E1 decisions
        self.assertAlmostEqual(c["taubar"], 0.005)
        self.assertAlmostEqual(c["r2bar"], 0.1)
        mem = A.FamilyDecl().members(edge, self.sn, c)
        self.assertEqual(set(mem), {"budget×1", "info×0.5", "keep+×0.5", "keep-×0.5"})   # D2 fixed sizes
        self.assertEqual(sel["members"], mem)
        decs = [{"index": 5, "epoch": "E1", "eligible": True, "index_value": 0.0026, "r": 0.5,
                 "tau_pred": 0.004, "action": "execute"},
                {"index": 6, "epoch": "E1", "eligible": True, "index_value": 0.004, "r": 0.3,
                 "tau_pred": 0.004, "action": "execute"},
                {"index": 6, "epoch": "E2", "eligible": True, "index_value": 0.0005, "r": 0.2,
                 "action": "keep"}]
        best = mem["budget×1"]
        dev += self._dev({p: (0.003 if p == best else 0.001) for p in mem.values()}, n=40, decisions={best: decs})
        sel = A.selection_report(dev, self.pd, self.nd)
        self.assertEqual(sel["status"], "ok")
        self.assertEqual(sel["pi_star"], best)
        self.assertEqual(sel["pi_star_member"], "budget×1")
        self.assertEqual(sel["tuning"]["campaigns"], 4 * 40)               # D2: 4 members × 40
        self.assertTrue(sel["paired_dev_instances"])
        self.assertTrue(sel["static_extended"])
        # m* = static(0.4σ, 0) executes V* ≥ 0.00264: flips at the first E1 decision only
        self.assertAlmostEqual(sel["flip"]["flip_rate"], 1 / 3)
        self.assertAlmostEqual(sel["flip"]["flip_rate_E1"], 0.5)
        self.assertEqual(sel["flip"]["flip_rate_E2"], 0.0)
        g0, bb = 0.4 * self.sn, 1.0 * self.sn
        self.assertAlmostEqual(sel["matched_static"]["g_eff"], np.mean([g0 - bb * (0.5 - 0.3), g0 - bb * (0.3 - 0.3)]))

    def test_tuning_procedures(self):
        members = {f"{ch}×{u}": f"dynamic:0.001,{0.001 * k},0,0,0" for k, (ch, u) in
                   enumerate([(c, u) for c in ("budget", "info", "keep+", "keep-") for u in (1, 2, 3)], 1)}
        true = {p: (0.004 if n == "info×2" else 0.0) for n, p in members.items()}
        rng = np.random.default_rng(0)
        noise = {p: rng.normal(0, 0.0005, 200) for p in members.values()}
        get = lambda p, k: true[p] + noise[p][k]  # noqa: E731
        for proc in ({"procedure": "argmax", "n_dev": 20}, {"procedure": "halving", "member_budget": 340},
                     {"procedure": "channel_first", "n1": 20, "n2": 60}):
            t = A.tune_members(get, members, proc)
            self.assertEqual(t["winner"], "info×2", proc)
        sched = A.halving_schedule(12, 340)
        self.assertEqual([m for m, _ in sched], [12, 6, 3, 2])
        self.assertLessEqual(sum(m * (c - (sched[i - 1][1] if i else 0)) for i, (m, c) in enumerate(sched)), 340)
        with self.assertRaises(A.MissingDev):
            A.tune_members(lambda p, k: (_ for _ in ()).throw(KeyError(p)), members, {"procedure": "argmax"})

    def test_ties_go_to_the_simpler_member(self):
        cfgs = [A.policy_string("static", (0.002, 0.001)), A.policy_string("static", (0.001, 0.0))]
        self.assertEqual(A._argmax_simplest(cfgs, np.array([0.5, 0.5])), 1)

    def test_centred_semantics(self):
        s = "dynamic:0.001,0.002,0,0,0,0.1,0,0.1"
        self.assertTrue(A.threshold_act(s, {"r": 0.5, "index_value": 0.0005}, "E1"))    # r > r̄₁: lower threshold
        self.assertFalse(A.threshold_act(s, {"r": 0.1, "index_value": 0.0005}, "E1"))   # r = r̄₁: m*'s threshold
        eff = A.effective_thresholds(s, [{"epoch": "E1", "eligible": True, "r": 0.0},
                                         {"epoch": "E1", "eligible": True, "r": 0.2}])
        self.assertAlmostEqual(eff["g_eff"], 0.001)                     # centred: same mean threshold as m*

    def test_comparison_operators(self):
        # execute uses ≥ (g = 0 with V̂* = 0 executes), keep uses > (m̂ = h does not keep)
        self.assertTrue(A.threshold_act("static:0,0", {"index_value": 0.0}, "E1"))
        self.assertFalse(A.threshold_act("static:0,0", {"index_value": 0.0}, "E2"))
        self.assertTrue(A.threshold_act("dynamic:0,0,0,0,0,0.2,0.004,0.2", {"index_value": 0.0, "r": 0.9}, "E1"))
        self.assertFalse(A.threshold_act("dynamic:0,0,0,0,0,0.2,0.004,0.2", {"index_value": 0.0, "r": 0.9}, "E2"))
        p = S.ThresholdPolicy("static:0,0")
        self.assertTrue(p.e1({"index_value": 0.0, "r": 0.0, "tau_pred": 0.0}))
        self.assertFalse(p.e2({"index_value": 0.0, "r": 0.0}))

    def test_zero_coefficients_reproduce_static(self):
        rng = np.random.default_rng(1)
        for _ in range(200):
            st = {"index_value": rng.normal(0, 0.002), "r": rng.uniform(-0.5, 0.5), "tau_pred": 0.004}
            for ep in ("E1", "E2"):
                self.assertEqual(A.threshold_act("static:0.001,-0.0005", st, ep),
                                 A.threshold_act("dynamic:0.001,0,0,-0.0005,0,0.3,0.004,0.2", st, ep))

    def test_r_definition_and_budget_term_after_a_skip(self):
        # D1′-style check: r = runs_left/W − proposals_left/N_cap; after a skip runs are unchanged and one fewer
        # proposal is left, so r rises and the budget term (b_budget > 0) lowers the execute threshold
        W, cap = 2, 4
        before = A.r_value({"runs_left": 1, "trial_index": 2}, W, cap)      # 1/2 − 3/4
        after_skip = A.r_value({"runs_left": 1, "trial_index": 3}, W, cap)  # 1/2 − 2/4
        self.assertAlmostEqual(before, -0.25)
        self.assertAlmostEqual(after_skip, 0.0)
        s = "dynamic:0.002,0.004,0,0,0,0,0,0"
        x = {"index_value": 0.0019}
        self.assertFalse(A.threshold_act(s, {**x, "r": before}, "E1"))
        self.assertTrue(A.threshold_act(s, {**x, "r": after_skip + 0.1}, "E1"))
        with self.assertRaises(A.TrackSAnalysisError):
            A.threshold_act(s, x, "E1")                                  # r must be supplied

    def test_threshold_semantics(self):
        e2 = {"r": 0.3, "index_value": -0.0005}
        self.assertTrue(A.threshold_act("dynamic:0,0,0,0,0.002", e2, "E2"))            # keep+ (uncentred)
        self.assertFalse(A.threshold_act("dynamic:0,0,0,0,-0.002", {**e2, "index_value": 0.0005}, "E2"))  # keep−
        self.assertTrue(A.threshold_act("dynamic:0.001,0,0.1,0,0", {"index_value": 0.0008}, "E1", tau_pred=0.004))
        with self.assertRaises(A.TrackSAnalysisError):
            A.threshold_act("dynamic:0.001,0,0.1,0,0", {"index_value": 0.0008}, "E1")
        self.assertEqual(A.channel_of("dynamic:0,0,0,0,-0.001"), "keep-")


# ----------------------------------------------------------------------------------------------- decision rule
def fake_campaign(mean, lb, ub, p, *, flip=0.05, exact="pass", z=0.1, n=70, share=None, channel="budget",
                  capped=False):
    return {"label": "FIXTURE", "pi_star": "dynamic:0.001,0.0066,0,0,0,0.1,0.004,0.1", "pi_star_channel": channel,
            "m_star": "static:0.001,0", "delta_Y": 0.0033,
            "test": {"mean": mean, "lb": lb, "ub": ub, "p_one_sided": p, "n": n},
            "placebo_exact": {"status": exact, "n_mismatch": 0 if exact == "pass" else 1, "n_groups": 10,
                              "min_groups": 10},
            "placebo_descriptive": {"status": "STOP" if abs(z) > 3.5 else "pass", "z": z, "n": 15},
            "sizing": {"n_formula": 400 if capped else n, "n_run_target": n, "n_fixed": True,
                       "mde_at_run": 0.004 if capped else 0.002},
            "flip_S3e": {"flip_rate": flip},
            "underpowered_vs_plan": False,
            "selection": {"flip": {"flip_rate": flip}, "paired_dev_instances": True, "n_dev_instances": 20,
                          "pi_star_member": f"{channel}×1"},
            "matched_static": {"policy": "static:0.0005,0", "recovers_share": share}}


def controls(nodes=("a", "b"), k0=5, n=70):
    def v(mult, k):
        return {"R": 200, "k_A": k, "target_gain": mult * 0.0033, "achieved_oracle_gain": mult * 0.0033 * 0.98,
                "p_correct_selection": 0.9}
    per = {"n": n, "N0": {"R": 200, "k_A": k0}, "P2+": {"diffuse": v(1, 150), "concentrated": v(1, 154)},
           "P1": {"diffuse": v(2, 126)}}
    return {"label": "FIXTURE", "nodes": {nd: copy.deepcopy(per) for nd in nodes}}


class DecisionTests(unittest.TestCase):
    def setUp(self):
        nd = {x: A.NodeDecl(x, "primary", 0.0033, sigma_node=0.0066, sizing=A.SizingDecl(0.009, 300),
                            sigma_cmp_vary=0.0066) for x in ("a", "b")}
        self.pd = A.Predeclaration(nodes=nd, primary_nodes=["a", "b"])

    def res(self, ca, cb):
        return {"a": {"role": "primary", "campaign": ca, "fork": None, "label": "FIXTURE"},
                "b": {"role": "primary", "campaign": cb, "fork": None, "label": "FIXTURE"}}

    def test_route_A_with_holm_and_budget_wording(self):
        d = A.decide(self.res(fake_campaign(0.006, 0.002, 0.01, 0.004), fake_campaign(0.0, -0.002, 0.002, 0.5)),
                     controls(), self.pd)
        self.assertEqual(d["route"], "A")
        self.assertEqual(d["rejected_nodes"], ["a"])
        self.assertIn("≥ δ_Y", d["wording"])
        self.assertIn("a dynamic-knapsack threshold, explained by known OR theory", d["wording"])

    def test_threshold_level_shift_wording(self):
        d = A.decide(self.res(fake_campaign(0.006, 0.002, 0.01, 0.004, share=0.6),
                              fake_campaign(0.0, -0.002, 0.002, 0.5)), controls(), self.pd)
        self.assertIn("a threshold-level shift found by the dynamic tuning", d["wording"])

    def test_route_A_small(self):
        d = A.decide(self.res(fake_campaign(0.0015, 0.0004, 0.0026, 0.01), fake_campaign(0.0, -0.002, 0.002, 0.5)),
                     controls(), self.pd)
        self.assertEqual(d["route"], "A-small")
        self.assertIn("not worded as ≥ δ_Y", d["wording"])

    def test_no_gain_found_per_node_wording(self):
        d = A.decide(self.res(fake_campaign(0.0, -0.002, 0.0021, 0.5, flip=0.07),
                              fake_campaign(0.001, -0.001, 0.004, 0.2, capped=True)), controls(), self.pd)
        self.assertEqual(d["route"], "no gain found")
        w = d["wording"]
        self.assertIn("a: the selected dynamic member π* did not beat the tuned static rule m*; its mean gain is "
                      "below UB₉₅ = 0.0021.", w)
        self.assertIn("power 0.75", w)                                     # this node's S0.6 keep-feedback power
        self.assertIn("information-world gain of 2 δ_Y with power 0.63", w)
        self.assertIn("The budget channel, negative keep feedback and the information member itself are unprobed.", w)
        self.assertIn("It bounds π* only, not the four-member family.", w)
        self.assertIn("UB₉₅ < δ_Y is not an equivalence or negligibility result", w)
        self.assertIn("This is not evidence that the loop is one-step.", w)
        self.assertIn("minimum detectable effect", w)                      # the MDE at the fixed n is reported
        row = d["per_node"]["a"]
        self.assertEqual((row["UB95"], row["flip_rate_S3e"], row["flip_rate_dev"]), (0.0021, 0.07, 0.07))
        self.assertEqual(row["S06_P_correct_member"]["P2+-diffuse"], 0.9)

    def test_track_s_not_run(self):
        pd = A.parse_predeclaration({"schema": A.PREDECLARATION_SCHEMA, "primary_nodes": [], "nodes": {},
                                     "not_run_reason": "both nodes exceed 4 days (S0.5b fallback)"})
        d = A.decide({}, None, pd)
        self.assertEqual(d["route"], "Track S not run")
        self.assertIn("4 days", d["wording"])
        with self.assertRaises(A.TrackSAnalysisError):
            A.parse_predeclaration({"schema": A.PREDECLARATION_SCHEMA, "primary_nodes": [], "nodes": {}})

    def test_stops(self):
        good = dict(mean=0.0, lb=-0.002, ub=0.002, p=0.5)
        self.assertEqual(A.decide(self.res(fake_campaign(**good), fake_campaign(**good)), controls(k0=19),
                                  self.pd)["route"], "VOID_STOP")
        self.assertEqual(A.decide(self.res(fake_campaign(**good), fake_campaign(**good)), controls(k0=18),
                                  self.pd)["route"], "no gain found")
        self.assertEqual(A.decide(self.res(fake_campaign(**good, exact="STOP"), fake_campaign(**good)), controls(),
                                  self.pd)["route"], "VOID_STOP")
        self.assertEqual(A.decide(self.res(fake_campaign(**good, z=3.6), fake_campaign(**good)), controls(),
                                  self.pd)["route"], "VOID_STOP")
        d = A.decide(self.res(fake_campaign(**good, exact="insufficient"), fake_campaign(**good)), None, self.pd)
        self.assertEqual(d["route"], "no gain found")                        # missing controls warn, never gate
        self.assertTrue(any("exact placebo insufficient" in w for w in d["warnings"]))

    def test_only_declared_outcomes_can_be_output(self):
        rng = np.random.default_rng(11)
        seen = set()
        for _ in range(400):
            cs = []
            for _ in range(2):
                m = rng.normal(0.0, 0.004)
                se = abs(rng.normal(0.0015, 0.0007)) + 1e-5
                cs.append(fake_campaign(m, m - 1.7 * se, m + 1.7 * se, float(rng.uniform(0, 1)),
                                        flip=float(rng.uniform(0, 0.3)), share=rng.choice([None, 0.2, 0.7]),
                                        channel=str(rng.choice(A.CHANNEL_MEMBERS)), capped=bool(rng.random() < 0.3),
                                        z=float(rng.normal(0, 1.5)), exact=str(rng.choice(["pass", "pass", "STOP",
                                                                                             "missing"]))))
            ctl = controls(k0=int(rng.integers(0, 30))) if rng.random() < 0.8 else None
            d = A.decide(self.res(*cs), ctl, self.pd)
            self.assertIn(d["route"], A.OUTCOMES + ("VOID_STOP",))
            seen.add(d["route"])
        self.assertTrue({"A", "A-small", "no gain found", "VOID_STOP"} <= seen)
        self.assertNotIn("B", seen)
        self.assertNotIn("inconclusive", seen)

    def test_labels(self):
        self.assertEqual(A.combine_labels(["EVIDENCE", "EVIDENCE"]), "EVIDENCE")
        self.assertEqual(A.combine_labels(["EVIDENCE", "PILOT", "ENGINEERING_ONLY"]), "ENGINEERING_ONLY")
        with self.assertRaises(A.TrackSAnalysisError):
            A.combine_labels(["EVIDENCE", "evidence"])


class PredeclarationAndCliTests(unittest.TestCase):
    def decl(self, **over):
        d = {"schema": A.PREDECLARATION_SCHEMA, "primary_nodes": ["synthetic_N0"], "fallback_active": True,
             "bootstrap_B": 20, "winners_curse_splits": 20,
             "nodes": {"synthetic_N0": {"role": "primary", "sigma_node": 0.0066, "delta_Y": 0.0033,
                                        "sigma_cmp_vary": 0.0066,
                                        "sizing": {"sigma_D_ucl_s05b": 0.0093, "n_max": 300}}}}
        d.update(over)
        return d

    def test_parse(self):
        pd = A.parse_predeclaration(self.decl())
        self.assertEqual(len(pd.families.static_configs(0.0066)), 15)
        self.assertEqual(len(pd.families.members("static:0.001,0", 0.0066)), 4)     # D2
        self.assertEqual(pd.tuning, {"procedure": "argmax", "n_dev": 40})
        bad = self.decl()
        bad["nodes"]["synthetic_N0"]["delta_Y"] = 0.004
        with self.assertRaises(A.TrackSAnalysisError):
            A.parse_predeclaration(bad)
        bad = self.decl()
        del bad["nodes"]["synthetic_N0"]["sizing"]
        with self.assertRaises(A.TrackSAnalysisError):
            A.parse_predeclaration(bad)
        with self.assertRaises(A.TrackSAnalysisError):
            A.parse_predeclaration(self.decl(primary_nodes=["synthetic_N0", "x"], fallback_active=True))
        with self.assertRaises(A.TrackSAnalysisError):
            A.parse_predeclaration(self.decl(families={"g_units": [0.05, 0.1, 0.2, 0.4], "h_units": [-1, 0, 1],
                                                       "g_ext_units": 0.8}))   # g = 0 missing

    def test_end_to_end_cli_on_simulated_records(self):
        plan = S.Plan(n_campaign=30)
        reg = replace(S.Regime(n_instances=8, forks_per_instance=6), sigma_campaign=0.005)
        ex = S.run_s3e(S.make_world("N0"), reg, plan, seed=5)
        lv, rt = S.simulate(S.make_world("B0"), reg, seed=5, node="synthetic_N0")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            S.write_node(d / "synthetic_N0", lv, rt, ex["dev_roots"], ex["fresh_roots"])
            (d / "pd.json").write_text(json.dumps(self.decl()))
            ctl = controls(nodes=("synthetic_N0",), n=30)
            (d / "ctl.json").write_text(json.dumps(ctl))
            rc = A.main(["select", "--predeclaration", str(d / "pd.json"), "--node", f"synthetic_N0={d / 'synthetic_N0'}",
                         "--out", str(d / "sel.json")])
            self.assertEqual(rc, 0)
            sel = json.loads((d / "sel.json").read_text())
            self.assertEqual(sel["status"], "ok")
            rc = A.main(["analyze", "--predeclaration", str(d / "pd.json"), "--node",
                         f"synthetic_N0={d / 'synthetic_N0'}", "--controls", str(d / "ctl.json"),
                         "--out-json", str(d / "r.json"), "--out-md", str(d / "r.md"),
                         "--policy-out", str(d / "pol")])
            self.assertEqual(rc, 0)
            res = json.loads((d / "r.json").read_text())
            self.assertEqual(res["decision"]["label"], "FIXTURE")
            self.assertNotIn("EVIDENCE", (d / "r.md").read_text().replace("never EVIDENCE", "").replace(
                "EVIDENCE unless", ""))
            self.assertEqual(res["nodes"]["synthetic_N0"]["campaign"]["placebo_exact"]["status"], "pass")
            self.assertTrue((d / "pol" / "synthetic_N0.pi_prime.json").exists())


if __name__ == "__main__":
    unittest.main()
