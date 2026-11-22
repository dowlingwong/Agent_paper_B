# AI-assisted (Claude, chat session, 22 Nov 2026; subagent). DRAFT; not signed; not reviewed.
"""Tests of the D.3 closed-loop analysis on synthetic outcome tables only (no label, test or evaluation data).

AI-assisted (Claude, chat session, 22 Nov 2026; written by a subagent). DRAFT; not signed; not reviewed.
"""
import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy import stats

from r1.c3 import d3_analysis as d3

SHA = "a" * 64
START = "b" * 64


def _row(stage, arm, node, seed, rep, y, rng):
    final = START if y == 0 else hashlib.sha256(f"{arm}{node}{seed}{rep}".encode()).hexdigest()
    return {"campaign_id": d3.campaign_id(stage, arm, node, seed, rep), "stage": stage, "arm": arm, "node": node,
            "instance_id": d3.instance_id(node, seed), "instance_seed": seed, "repetition": rep,
            "memory_mode": d3.MEMORY_MODE, "status": "complete", "y_raw": float(y),
            "worker_runs": int(rng.integers(0, d3.W + 1)), "llm_calls": int(rng.integers(1, d3.LLM_CALL_CAP + 1)),
            "ended_on": "worker_runs", "audit_seeds": list(d3.audit_seeds(seed)),
            "start_config_hash": START, "final_config_hash": final}


def synthetic_table(stage="D.3a", arms=None, reps=1, effects=None, seed=0, sigma=None):
    """A complete synthetic table: y_raw = sigma_node * (effect[arm] + instance effect + noise)."""
    rng = np.random.default_rng(seed)
    arms = list(arms or (d3.ARMS_D3A if stage == "D.3a" else d3.ARMS_D3B))
    effects = effects or {}
    sigma = sigma or {node: 0.001 * (i + 1) for i, node in enumerate(d3.NODES)}
    rows = []
    for node in d3.NODES:
        for s in d3.INSTANCE_SEEDS:
            inst = rng.normal(0, 1.0)
            for arm in arms:
                for r in range(reps):
                    y = sigma[node] * (effects.get(arm, 0.0) + inst + rng.normal(0, 0.5))
                    rows.append(_row(stage, arm, node, s, r, y, rng))
    return {"schema": d3.SCHEMA, "stage": stage, "predeclaration_sha256": SHA,
            "noise_source_sha256": d3.NOISE_SOURCE_SHA256, "sigma_node": sigma, "arms": arms,
            "repetitions": reps, "rows": rows}


class NamespaceTest(unittest.TestCase):
    def test_declared_blocks_are_disjoint_from_every_reserved_namespace(self):
        report = d3.check_namespaces()
        self.assertEqual(report["d3_blocks"]["instance"], [6201, 6218, 18])
        self.assertEqual(report["d3_blocks"]["replicate"], [6501, 6679, 162])
        self.assertEqual(report["d3_blocks"]["audit"], [6701, 6880, 180])

    def test_sweep_universe_is_the_split_files_t0_universe_law(self):
        universe = d3.sweep_instance_seed_universe()
        self.assertEqual(min(universe), 100)
        self.assertLessEqual(max(universe), 276)
        self.assertFalse(universe & set(d3.INSTANCE_SEEDS))

    def test_exam_and_audit_modules_agree_with_the_reserved_list(self):
        from r1.c3.p3_split import T1_SEEDS
        from r1.exam.namespace import EXAM_SEEDS
        blocks = d3.declared_d3_seeds()
        for block in blocks.values():
            self.assertFalse(block & set(T1_SEEDS))
            self.assertFalse(block & EXAM_SEEDS)
            self.assertFalse(block & set(range(7001, 7011)))

    def test_seed_helpers(self):
        self.assertEqual(d3.audit_seeds(6201), tuple(range(6701, 6711)))
        self.assertEqual(d3.audit_seeds(6218), tuple(range(6871, 6881)))
        self.assertEqual(d3.replicate_seeds(6202)[:2], (6511, 6512))
        with self.assertRaises(d3.D3InputError):
            d3.audit_seeds(150)


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.table = synthetic_table()

    def refused(self, table, stage="D.3a"):
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(table, stage)

    def test_valid_table_passes(self):
        d3.validate_table(self.table, "D.3a")

    def test_unknown_or_missing_keys_are_refused(self):
        t = copy.deepcopy(self.table)
        t["rows"][0]["delta_true"] = 0.1
        self.refused(t)
        t = copy.deepcopy(self.table)
        del t["rows"][0]["y_raw"]
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["labels"] = []
        self.refused(t)

    def test_wrong_schema_stage_arms_or_noise_are_refused(self):
        for key, value in (("schema", "r1_d3_outcome/v0"), ("stage", "D.3b"), ("arms", ["A0", "A1"]),
                           ("noise_source_sha256", "c" * 64), ("repetitions", 3)):
            t = copy.deepcopy(self.table)
            t[key] = value
            self.refused(t)
        self.refused(self.table, stage="D.3b")

    def test_incomplete_design_or_status_is_refused(self):
        t = copy.deepcopy(self.table)
        t["rows"].pop()
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["rows"][3]["status"] = "stopped"
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["rows"].append(copy.deepcopy(t["rows"][0]))
        self.refused(t)

    def test_seed_caps_and_audit_seeds_are_checked(self):
        cases = [("instance_seed", 150), ("llm_calls", d3.LLM_CALL_CAP + 1), ("worker_runs", d3.W + 1),
                 ("audit_seeds", list(range(7001, 7011))), ("memory_mode", "none"), ("ended_on", "trial_budget"),
                 ("y_raw", float("nan")), ("repetition", 1), ("node", "openml_wdbc"), ("worker_runs", True)]
        for key, value in cases:
            t = copy.deepcopy(self.table)
            t["rows"][5][key] = value
            self.refused(t)

    def test_unchanged_final_configuration_must_have_zero_outcome(self):
        t = copy.deepcopy(self.table)
        row = next(r for r in t["rows"] if r["y_raw"] != 0)
        row["final_config_hash"] = START
        self.refused(t)

    def test_forbidden_input_paths_are_refused_before_opening(self):
        for name in ("label_block.jsonl", "evaluation_block.jsonl", "runs.jsonl", "c3_p3_split_v1.json",
                     "proposals.jsonl"):
            with self.assertRaises(d3.D3InputError):
                d3.refuse_input_path(Path("/nonexistent") / name)
        with self.assertRaises(d3.D3InputError):
            d3.refuse_input_path(Path("/nonexistent/r1_sealed/d3a.json"))

    def test_load_table_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "d3a_outcome.json"
            path.write_text(json.dumps(self.table))
            self.assertEqual(d3.load_table(path, "D.3a")["stage"], "D.3a")


class StatisticsTest(unittest.TestCase):
    def test_holm_matches_hand_computation(self):
        adj, rej = d3.holm([0.01, 0.04, 0.03, 0.005], alpha=0.05)
        self.assertEqual([round(x, 10) for x in adj], [0.03, 0.06, 0.06, 0.02])
        self.assertEqual(rej, [True, False, False, True])

    def test_contrast_estimate_se_and_p_by_hand(self):
        rng = np.random.default_rng(3)
        ya = {n: rng.normal(0.3, 1, 18) for n in d3.NODES}
        yb = {n: rng.normal(0.0, 1, 18) for n in d3.NODES}
        out = d3.paired_contrast(ya, yb, boot=200)
        diffs = [ya[n] - yb[n] for n in d3.NODES]
        est = np.mean([d.mean() for d in diffs])
        se = math.sqrt(sum(d.var(ddof=1) / 18 for d in diffs)) / len(d3.NODES)
        self.assertAlmostEqual(out["estimate"], est, places=12)
        self.assertAlmostEqual(out["se"], se, places=12)
        self.assertEqual(out["df"], 7 * 17)
        self.assertAlmostEqual(out["p_two_sided"], 2 * stats.t.sf(abs(est / se), 119), places=12)
        self.assertLess(out["ci95_t"][0], est)
        self.assertGreater(out["ci95_t"][1], est)

    def test_bootstrap_is_reproducible(self):
        rng = np.random.default_rng(4)
        ya = {n: rng.normal(0, 1, 18) for n in d3.NODES}
        yb = {n: rng.normal(0, 1, 18) for n in d3.NODES}
        a = d3.paired_contrast(ya, yb, boot=300)
        b = d3.paired_contrast(ya, yb, boot=300)
        self.assertEqual(a["ci95_bootstrap"], b["ci95_bootstrap"])

    def test_degenerate_identical_arms(self):
        y = {n: np.zeros(18) for n in d3.NODES}
        out = d3.paired_contrast(y, y, boot=50)
        self.assertEqual(out["p_two_sided"], 1.0)
        self.assertTrue(out["degenerate_se"])

    def test_outcome_is_in_sigma_units_and_averages_repetitions(self):
        t = synthetic_table(reps=2, seed=5)
        ys = d3.outcome_matrix(t)
        node, s = d3.NODES[2], d3.INSTANCE_SEEDS[4]
        vals = [r["y_raw"] / t["sigma_node"][node] for r in t["rows"]
                if r["arm"] == "A2" and r["node"] == node and r["instance_seed"] == s]
        self.assertEqual(len(vals), 2)
        self.assertAlmostEqual(ys["A2"][node][4], float(np.mean(vals)), places=12)


class AnalyseTest(unittest.TestCase):
    def test_d3a_only_reports_d3b_not_run(self):
        t = synthetic_table(effects={"A2": 1.0})
        rep = d3.analyse(t, d3b_not_run="gate_not_passed")
        fam = rep["families"]["D.3a"]
        self.assertEqual([c["contrast"] for c in fam["contrasts"]],
                         ["A1 - A0", "A2 - A0", "FIXR3 - A0", "EGATE - A0", "LADDER - A0", "LADDER - A2"])
        a2 = fam["contrasts"][1]
        self.assertTrue(a2["reject_holm"])
        self.assertGreater(a2["estimate"], 0.7)
        self.assertEqual(rep["families"]["D.3b"]["status"], "not_run")
        self.assertEqual(rep["families"]["D.3b"]["reason"], "gate_not_passed")

    def test_reason_is_required_without_d3b(self):
        with self.assertRaises(d3.D3InputError):
            d3.analyse(synthetic_table())

    def test_d3b_pairs_with_d3a_and_adds_a6_contrast(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", arms=d3.ARMS_D3B_WITH_A6, seed=2)
        rep = d3.analyse(a, b)
        names = [c["contrast"] for c in rep["families"]["D.3b"]["contrasts"]]
        self.assertEqual(names, ["A3 - A2", "A5 - A2", "A3 - A0", "A5 - A0", "A6 - A5"])
        self.assertTrue(rep["families"]["D.3b"]["a6_entered"])
        b2 = synthetic_table(stage="D.3b", seed=2)
        names = [c["contrast"] for c in d3.analyse(a, b2)["families"]["D.3b"]["contrasts"]]
        self.assertNotIn("A6 - A5", names)

    def test_d3b_with_a_different_predeclaration_or_sigma_is_refused(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", seed=2)
        b["predeclaration_sha256"] = "d" * 64
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, b)
        b = synthetic_table(stage="D.3b", seed=2, sigma={n: 1.0 for n in d3.NODES})
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, b)

    def test_sigma_check_against_a_synthetic_noise_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps({"nodes": {}}))
            with self.assertRaises(d3.D3InputError):   # sha differs from the pin
                d3.verify_sigma_against_noise_source({n: 1.0 for n in d3.NODES}, path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(d3.D3InputError):   # nodes absent from the summary
                d3.verify_sigma_against_noise_source({n: 1.0 for n in d3.NODES}, path, expected_sha256=sha)

    def test_cli_refuses_a_predeclaration_hash_mismatch_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            (tdir / "d3a.json").write_text(json.dumps(synthetic_table()))
            (tdir / "predecl.md").write_text("not the declared file\n")
            rc = d3.main(["analyse", "--d3a", str(tdir / "d3a.json"), "--d3b-not-run", "not_started",
                          "--predeclaration", str(tdir / "predecl.md"), "--out", str(tdir / "report.json")])
            self.assertEqual(rc, 2)
            self.assertFalse((tdir / "report.json").exists())
            (tdir / "report.json").write_text("{}")
            rc = d3.main(["analyse", "--d3a", str(tdir / "d3a.json"), "--d3b-not-run", "not_started",
                          "--predeclaration", str(tdir / "predecl.md"), "--out", str(tdir / "report.json")])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
