"""Track S simulator tests (r1/tracks/simulate_controls.py). CPU, fast, unittest style. AI-assisted (Claude, 29 Oct 2026)."""
from __future__ import annotations

import json
import unittest
from dataclasses import replace

import numpy as np

from r1.tracks import analyze as A
from r1.tracks import simulate_controls as S
from r1.tracks.schema import STATE_FEATURES, TRACKS_LEAF_SCHEMA, leaf_from_dict, to_dict

SMALL = S.Regime(n_instances=8, forks_per_instance=6)


class RecordTests(unittest.TestCase):
    def test_leaf_and_root_round_trip(self):
        lv, rt = S.simulate(S.make_world("P2", 0.004), SMALL, seed=3)
        self.assertTrue(lv and rt)
        for lf in lv[:50]:
            self.assertEqual(lf.schema, TRACKS_LEAF_SCHEMA)
            self.assertEqual(list(lf.state), list(STATE_FEATURES))
            back = leaf_from_dict(json.loads(json.dumps(to_dict(lf))))
            self.assertEqual(back, lf)
            self.assertEqual(lf.provenance.label, "FIXTURE")
        r = S.make_campaign_root("n", "c0001", "static:0.001,0", 2, 0.91, W=10, llm_cap=40)
        back = A.root_from_dict(json.loads(json.dumps(A.record_to_dict(r))))
        self.assertEqual((A.policy_of(back), A.rep_of(back), back.y_terminal), ("static:0.001,0", 2, 0.91))

    def test_deterministic(self):
        a, _ = S.simulate(S.make_world("P1", 6.0), SMALL, seed=4)
        b, _ = S.simulate(S.make_world("P1", 6.0), SMALL, seed=4)
        self.assertEqual([to_dict(x) for x in a], [to_dict(x) for x in b])
        x = S.run_s3e(S.make_world("N0"), SMALL, S.Plan(n_campaign=6, n_dev=6), seed=1)["result"]["test"]["mean"]
        y = S.run_s3e(S.make_world("N0"), SMALL, S.Plan(n_campaign=6, n_dev=6), seed=1)["result"]["test"]["mean"]
        self.assertEqual(x, y)

    def test_every_arm_present_and_channel_third(self):
        lv, _ = S.simulate(S.make_world("B0"), SMALL, seed=5)
        ft = A.build_fork_table("synthetic_B0", lv)
        self.assertEqual(ft.counts["forks_no_complete_rep"], 0)
        chan = np.mean([f.selection.channel_arms for f in lv if f.epoch == "E1" and f.arm == "skip"])
        self.assertTrue(0.1 < chan < 0.6)


class PolicyTests(unittest.TestCase):
    def test_threshold_policy_matches_analyze(self):
        rng = np.random.default_rng(0)
        for s in ("static:0.001,-0.001", "dynamic:0.001,0.002,0,0,0", "dynamic:0.001,0,0.3,0,0",
                  "dynamic:0.0005,0,0,0,0.004", "dynamic:0.0005,0,0,0.001,-0.004",
                  "dynamic:0.001,0.002,0,0,0,0.6,0.004,0.5", "dynamic:0.001,0,0.5,0,0,0.6,0.004,0.5",
                  "dynamic:0.001,0,0,0.0005,-0.003,0.6,0.004,0.5"):
            p = S.ThresholdPolicy(s)
            for _ in range(50):
                f = {"budget_fraction": rng.random(), "r": rng.uniform(-0.5, 0.5),
                     "index_value": rng.normal(0, 0.002), "tau_pred": abs(rng.normal(0.004, 0.001))}
                self.assertEqual(p.e1(f), A.threshold_act(s, f, "E1", f["tau_pred"]))
                self.assertEqual(p.e2(f), A.threshold_act(s, f, "E2"))


class PipelineTests(unittest.TestCase):
    def test_s3e_pipeline_selection_placebos_and_matched_static(self):
        plan = S.Plan(n_campaign=16, n_dev=8, n_dev_members=12)
        reg = replace(SMALL, sigma_campaign=0.004)
        out = S.run_s3e(S.make_world("P2", 0.008, fb_shape="r_linear", fb_len=6), reg, plan, seed=2)
        res = out["result"]
        self.assertEqual(res["placebo_exact"]["status"], "pass")         # same rep, same policy: D = 0 exactly
        self.assertEqual(res["placebo_exact"]["n_groups"], 10)
        self.assertIn(res["placebo_descriptive"]["status"], ("pass", "STOP"))
        self.assertEqual(res["placebo_descriptive"]["n"], 15)
        self.assertEqual(res["selection"]["tuning"]["campaigns"], 4 * 12)
        self.assertIsInstance(res["other_members_vs_m_star"], dict)
        self.assertEqual(len(res["other_members_vs_m_star"]), 3)
        self.assertIn(res["route_single_node"], ("A", "A-small", "no gain found"))
        self.assertIn(res["pi_star_channel"], A.CHANNEL_MEMBERS)
        self.assertEqual(res["selection"]["n_dev_instances"], 8)
        self.assertTrue(res["selection"]["paired_dev_instances"])
        self.assertIsNotNone(res["selection"]["flip"]["flip_rate"])
        dev_i = {r.instance_id for r in out["dev_roots"]}
        self.assertFalse(dev_i & {r.instance_id for r in out["fresh_roots"]})
        ms = res["selection"]["matched_static"]["policy"]
        if ms not in (res["pi_star"], res["m_star"]):
            self.assertEqual(res["matched_static_runs"]["n_instances"], 16)  # matched static on all n instances

    def test_oracle_and_calibration_machinery(self):
        plan = S.Plan()
        g = S.oracle_gain(S.make_world("N0"), SMALL, plan, n_oracle=40)
        self.assertIn(g["member_oracle"].split("×")[0], A.CHANNEL_MEMBERS)
        self.assertGreater(g["centres"]["r1bar"], 0.0)
        cal = S.calibrate_strength("P2+", "diffuse", SMALL, plan, grid=(0.004, 0.012, 0.02), n_cal=40, n_oracle=60,
                                   iters=2, refine=1)
        self.assertTrue(cal["trace"])
        if cal["strength"] is not None:
            self.assertIn("within_tolerance", cal)

    def test_replicate_reports_rates_with_binomial_cis(self):
        plan = S.Plan(n_campaign=8, n_dev=6)
        reg = replace(SMALL, sigma_campaign=0.004)
        oracle = {"gain": 0.0, "member_oracle": "budget×1", "m_oracle": "static:0.00033,0"}
        r = S.replicate(S.make_world("N0"), reg, plan, 3, oracle=oracle)
        self.assertEqual(r["R"], 3)
        lo, hi = r["route_A_or_A_small"]["ci95_clopper_pearson"]
        self.assertTrue(0.0 <= lo <= r["route_A_or_A_small"]["rate"] <= hi <= 1.0)
        self.assertIn("p_correct_member", r)
        self.assertEqual(r["exact_placebo_not_pass"], 3)          # n = 8 < the 10 declared exact-placebo instances

    def test_design_study_replicate_and_schedule_oracle(self):
        plan = S.Plan(n_campaign=10)
        reg = replace(SMALL, sigma_campaign=0.005)
        r = S.study_replicate(S.make_world("P2+", 0.008, "diffuse"), reg, plan, 3, S.DESIGNS)
        self.assertEqual(set(r["designs"]), set(S.DESIGNS))
        for d in r["designs"].values():
            self.assertLessEqual(d["campaigns"], 640 + 60)
            self.assertIn(d["winner"].split("×")[0], A.CHANNEL_MEMBERS)
        self.assertEqual(r["designs"]["D1 fixed-4, argmax n=20"]["campaigns"], r["static_campaigns"] + 4 * 20)
        o = S.schedule_oracle(S.make_world("N0"), SMALL, plan, n_search=8, n_verify=8, sweeps=1)
        self.assertGreaterEqual(o["gain"], -1e-12)              # the schedule nests the best static rule

    def test_rev7_worlds(self):
        for kind, variant, st in (("P0", "diffuse", 0.004), ("P0", "concentrated", 0.004),
                                  ("P2-", "diffuse", 0.004), ("P2-", "concentrated", 0.004)):
            w = S.make_world(kind, st, variant)
            y = S.Sim(w, SMALL, 1).run_campaign(S.theta_table(w, SMALL, 1, 0), S.ThresholdPolicy("static:0,0"),
                                                [1, 0, 1], None, noiseless=True)
            self.assertTrue(np.isfinite(y))

    def test_trial_one_is_never_rule_detectable_and_kept(self):
        reg = replace(SMALL, p_rule=0.95)
        sim = S.Sim(S.make_world("N0"), reg, 3)
        for inst in range(30):
            st, log = sim.run_root(inst, S.theta_table(S.make_world("N0"), reg, 3, inst))
            self.assertFalse(log[0]["rule"])
            self.assertTrue(log[0].get("executed") and log[0].get("kept"))
            self.assertFalse(log[0].get("e1_eligible"))

    def test_noise_matching(self):
        reg, rec = S.match_noise(S.Regime(), S.Plan(), sigma_D=0.01)
        self.assertAlmostEqual(reg.sigma_campaign, S.sigma_campaign_for(0.01, S.Regime()))
        small = replace(SMALL, llm_cap=20)
        reg3, rec3 = S.match_noise(small, S.Plan(), between_policy_sd=0.012)   # first S0.6 run (pilot)
        self.assertEqual(rec3["matched_to"], "S0.5 pilot between-policy sd")
        got = S.pilot_between_policy_sd(S.make_world("N0"), reg3, S.Plan())
        self.assertAlmostEqual(got, 0.012, delta=0.002)
        reg4, rec4 = S.match_noise(small, S.Plan(), between_policy_sd=0.012, dev_between_sd=0.01)  # post-S0.7 re-run
        self.assertEqual(rec4["matched_to"], "dev between-configuration sd (post-S0.7 re-run)")
        reg2, rec2 = S.match_noise(S.Regime(), S.Plan(), pilot_D=list(np.random.default_rng(0).normal(0, 0.01, 25)))
        self.assertEqual(rec2["m_pairs"], 25)

    def test_planted_generator_channels(self):
        lv = S.planted_forks(n_instances=30, forks_per_instance=10, sigma=0.0005, budget=0.002, info=0.001,
                             feedback=0.0015, seed=1)
        ft = A.build_fork_table("planted", lv)
        est = A.channel_means(ft, np.arange(len(ft)))
        self.assertAlmostEqual(est["delta_B"], 0.002, delta=0.0006)
        self.assertAlmostEqual(est["delta_I"], 0.001, delta=0.0006)
        self.assertAlmostEqual(est["delta_F"], 0.0015, delta=0.0006)


if __name__ == "__main__":
    unittest.main()
