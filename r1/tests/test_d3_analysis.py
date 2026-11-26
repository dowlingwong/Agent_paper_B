# AI-assisted (Claude, chat session, 22 Nov 2026; subagent). Revision 4: AI-assisted (Claude, local worker,
# 27 Nov 2026). DRAFT; not signed.
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


GPU = "NVIDIA H200"


def _row(stage, arm, node, seed, rep, y, rng, gpu=GPU):
    final = START if y == 0 else hashlib.sha256(f"{arm}{node}{seed}{rep}".encode()).hexdigest()
    hpo = stage == "HPO-REF"
    calls = 0 if hpo else int(rng.integers(d3.W, d3.LLM_CALL_CAP + 1))
    return {"campaign_id": d3.campaign_id(stage, arm, node, seed, rep), "stage": stage, "arm": arm, "node": node,
            "instance_id": d3.instance_id(node, seed), "instance_seed": seed, "repetition": rep,
            "memory_mode": d3.HPO_MEMORY_MODE if hpo else d3.MEMORY_MODE, "status": "complete", "y_raw": float(y),
            "worker_runs": d3.W, "llm_calls": calls,
            "ended_on": "worker_runs", "audit_seeds": list(d3.audit_seeds(seed)),
            "start_config_hash": START, "final_config_hash": final,
            # revision 4 fields
            "gpu_model": None if hpo else gpu, "infra_attempts": 1,
            "y_raw_w": {str(w): float(y) if w == d3.W else float(y) * w / d3.W for w in d3.BUDGET_POINTS},
            "proposals": d3.W if hpo else calls, "llm_tokens_prompt": 0 if hpo else 1000 * calls,
            "llm_tokens_completion": 0 if hpo else 100 * calls, "worker_seconds": 40.0,
            "proposer_gpu_seconds": 0.0 if hpo else 300.0, "controller_seconds": 1.5, "wall_seconds": 400.0,
            "duplicates_proposed": 3, "duplicates_executed": 0 if arm in d3.RULE_LAYER_ARMS else 3,
            "rule_skips": 3 if arm in d3.RULE_LAYER_ARMS else 0, "value_skips": 1 if arm in d3.SCREEN_ARMS else 0,
            "keeps": 2, "distinct_configs_executed": 17, "last_keep_run": 12, "last_improving_run": 12 if y > 0 else None}


def _shrink(row, runs, calls, ended):
    """Make a row end below W consistently: counts, Y(w) missing beyond runs, mechanism counts within runs."""
    row.update(worker_runs=runs, llm_calls=calls, proposals=min(row["proposals"], calls), ended_on=ended,
               distinct_configs_executed=min(row["distinct_configs_executed"], runs),
               last_keep_run=min(row["last_keep_run"], runs) if row["last_keep_run"] else None,
               last_improving_run=min(row["last_improving_run"], runs) if row["last_improving_run"] else None)
    row["y_raw_w"] = {k: (v if int(k) <= runs else None) for k, v in row["y_raw_w"].items()}
    return row


def synthetic_table(stage="D.3a", arms=None, reps=1, effects=None, seed=0, sigma=None, gpu_by_node=None):
    """A complete synthetic table: y_raw = sigma_node * (effect[arm] + instance effect + noise)."""
    rng = np.random.default_rng(seed)
    default_arms = {"D.3a": d3.ARMS_D3A, "D.3b": d3.ARMS_D3B, "HPO-REF": d3.ARMS_HPO}[stage]
    arms = list(arms or default_arms)
    a6 = ("A6" in arms) if stage == "D.3b" else None
    effects = effects or {}
    sigma = sigma or {node: 0.001 * (i + 1) for i, node in enumerate(d3.NODES)}
    gpu_by_node = gpu_by_node or {}
    rows = []
    for node in d3.NODES:
        for s in d3.INSTANCE_SEEDS:
            inst = rng.normal(0, 1.0)
            for arm in arms:
                for r in range(reps):
                    y = sigma[node] * (effects.get(arm, 0.0) + inst + rng.normal(0, 0.5))
                    rows.append(_row(stage, arm, node, s, r, y, rng, gpu=gpu_by_node.get(node, GPU)))
    return {"schema": d3.SCHEMA, "stage": stage, "predeclaration_sha256": SHA,
            "noise_source_sha256": d3.NOISE_SOURCE_SHA256, "sigma_node": sigma, "arms": arms, "a6_entered": a6,
            "repetitions": reps, "rows": rows}


class NamespaceTest(unittest.TestCase):
    def test_declared_blocks_are_disjoint_from_every_reserved_namespace(self):
        report = d3.check_namespaces()
        self.assertEqual(report["d3_blocks"]["instance"], [6201, 6218, 18])
        self.assertEqual(report["d3_blocks"]["replicate"], [6501, 6679, 162])
        self.assertEqual(report["d3_blocks"]["audit"], [6701, 6880, 180])
        self.assertEqual(report["d3_blocks"]["smoke"], [6301, 6302, 2])
        self.assertEqual(report["d3_blocks"]["smoke_replicate"], [6311, 6329, 18])
        self.assertEqual(d3.replicate_seeds(6301), tuple(range(6311, 6320)))
        self.assertEqual(d3.replicate_seeds(6302), tuple(range(6321, 6330)))

    def test_reserved_intervals_equal_the_module_constants(self):
        import ast
        from r1.c3.audit import DEFAULT_SEEDS
        from sweep2.s2_c3b_lib import EXAM_SEED_BLOCK, G1B_SEED_BLOCK, PROMPT_MEASUREMENT_SEEDS
        res = {label.split(" (")[0]: iv for label, iv in d3.RESERVED_SEED_NAMESPACES.items()}
        self.assertEqual(res["B.2 audit seeds, label 7001-7005 and evaluation 7006-7010"],
                         (min(DEFAULT_SEEDS), max(DEFAULT_SEEDS)))
        self.assertEqual(res["exam instance and audit seeds"], tuple(EXAM_SEED_BLOCK))
        self.assertEqual(res["G.1b proposed training-seed block"], tuple(G1B_SEED_BLOCK))
        prompt = sorted(PROMPT_MEASUREMENT_SEEDS.values())
        self.assertEqual(res["S2-C3b prompt-measurement seeds"], (prompt[0], prompt[-1]))

        def constant(path, name):   # modules that import the harness are parsed, not imported
            tree = ast.parse((Path(__file__).resolve().parents[2] / path).read_text())
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
                    return ast.literal_eval(node.value)
            raise AssertionError(name)
        base = constant("r1/noise/e1_noise_floor.py", "SEED_BASE")
        self.assertEqual(res["D21 noise floors, train seeds"], (base["train"], base["train"] + 29))
        self.assertEqual(res["D21 noise floors, split seeds"], (base["split"], base["split"] + 29))
        self.assertEqual(res["D21 noise floors, joint seeds"], (base["joint"], base["joint"] + 29))
        self.assertEqual(res["E1b audit seeds"][0], constant("r1/headroom/e1b_collect.py", "AUDIT_SEED_BASE"))
        e2e = (Path(__file__).resolve().parents[2] / "r1/e2e.py").read_text()
        self.assertIn("train_seed=999", e2e)
        self.assertEqual(res["engineering smoke seeds"], (999, 999))

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
        cases = [("instance_seed", 150), ("instance_seed", 6301), ("llm_calls", d3.LLM_CALL_CAP + 1), ("worker_runs", d3.W + 1),
                 ("audit_seeds", list(range(7001, 7011))), ("memory_mode", "none"), ("ended_on", "trial_budget"),
                 ("y_raw", float("nan")), ("repetition", 1), ("node", "openml_wdbc"), ("worker_runs", True)]
        for key, value in cases:
            t = copy.deepcopy(self.table)
            t["rows"][5][key] = value
            self.refused(t)

    def test_ended_on_must_agree_with_the_counts(self):
        t = copy.deepcopy(self.table)
        t["rows"][0]["ended_on"] = "llm_call_cap"                       # but worker_runs = W
        self.refused(t)
        t = copy.deepcopy(self.table)
        row = next(r for r in t["rows"] if r["arm"] == "A0")
        _shrink(row, 17, 30, "no_fundable_candidate")   # A0 never ends this way
        self.refused(t)
        t = copy.deepcopy(self.table)
        row = next(r for r in t["rows"] if r["arm"] == "FIXR3")
        _shrink(row, 18, 8, "no_fundable_candidate")
        d3.validate_table(t, "D.3a")
        _shrink(row, 12, d3.LLM_CALL_CAP, "no_fundable_candidate")
        self.refused(t)
        row.update(ended_on="llm_call_cap")
        d3.validate_table(t, "D.3a")

    def test_refusals_do_not_echo_table_content(self):
        t = copy.deepcopy(self.table)
        t["rows"][2]["node"] = "SECRET_VALUE_42"
        t["rows"][2]["SECRET_KEY_43"] = 1
        for table in (t, {**copy.deepcopy(self.table), "SECRET_KEY_44": 0}):
            with self.assertRaises(d3.D3InputError) as ctx:
                d3.validate_table(table, "D.3a")
            self.assertNotIn("SECRET", str(ctx.exception))

    def test_one_start_configuration_per_node_even_without_d3b(self):
        t = copy.deepcopy(self.table)
        t["rows"][0]["start_config_hash"] = "c" * 64
        t["rows"][0]["final_config_hash"] = "d" * 64
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

    def test_load_table_checks_suffix_before_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "d3a_outcome.txt"
            path.write_text(json.dumps(self.table))
            with self.assertRaises(d3.D3InputError):
                d3.load_table(path, "D.3a")

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
        ys = d3.outcome_matrix(t, 2)
        node, s = d3.NODES[2], d3.INSTANCE_SEEDS[4]
        vals = [r["y_raw"] / t["sigma_node"][node] for r in t["rows"]
                if r["arm"] == "A2" and r["node"] == node and r["instance_seed"] == s]
        self.assertEqual(len(vals), 2)
        self.assertAlmostEqual(ys["A2"][node][4], float(np.mean(vals)), places=12)


class AnalyseTest(unittest.TestCase):
    def test_d3a_only_reports_d3b_not_run(self):
        t = synthetic_table(effects={"A2": 1.0})
        with self.assertRaises(d3.D3InputError):      # R1-D3B-UNCONDITIONAL: no longer a reason
            d3.analyse(t, d3b_not_run="gate_not_passed")
        rep = d3.analyse(t, d3b_not_run="not_started")
        fam = rep["families"]["D.3a"]
        self.assertEqual([c["contrast"] for c in fam["contrasts"]],
                         ["A0R - A0", "A2 - A0R", "A1 - A0", "A2 - A0", "FIXR3 - A0", "EGATE - A0", "LADDER - A0",
                          "LADDER - A2"])
        self.assertIn("8 contrasts", fam["multiplicity"])
        a2 = fam["contrasts"][3]
        self.assertTrue(a2["reject_holm"])
        self.assertEqual(a2["holm_direction"], "favourable")
        self.assertGreater(a2["estimate"], 0.7)
        self.assertEqual(rep["families"]["D.3b"]["status"], "not_run")
        self.assertEqual(rep["families"]["D.3b"]["reason"], "not_started")
        self.assertEqual(rep["readings"]["learned_gain"], "not_run")
        self.assertEqual(rep["reference_rows"]["status"], "not_run")

    def test_reason_is_required_without_d3b(self):
        with self.assertRaises(d3.D3InputError):
            d3.analyse(synthetic_table())

    def test_d3b_pairs_with_d3a_and_adds_a6_contrast(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", arms=d3.ARMS_D3B_WITH_A6, seed=2)
        rep = d3.analyse(a, b, a6_declared=True)
        names = [c["contrast"] for c in rep["families"]["D.3b"]["contrasts"]]
        self.assertEqual(names, ["A3 - A2", "A5 - A2", "A3 - A0", "A5 - A0", "A5 - A3", "A6 - A5"])
        self.assertTrue(rep["families"]["D.3b"]["a6_entered"])
        b2 = synthetic_table(stage="D.3b", seed=2)
        names = [c["contrast"] for c in d3.analyse(a, b2, a6_declared=False)["families"]["D.3b"]["contrasts"]]
        self.assertNotIn("A6 - A5", names)

    def test_d3b_with_a_different_predeclaration_or_sigma_is_refused(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", seed=2)
        b["predeclaration_sha256"] = "d" * 64
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, b, a6_declared=False)
        b = synthetic_table(stage="D.3b", seed=2, sigma={n: 1.0 for n in d3.NODES})
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, b, a6_declared=False)

    def test_a6_entry_is_bound_by_the_note(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", arms=d3.ARMS_D3B_WITH_A6, seed=2)
        with self.assertRaises(d3.D3InputError):   # the note says A6 did not enter
            d3.analyse(a, b, a6_declared=False)
        with self.assertRaises(d3.D3InputError):   # no declaration at all
            d3.analyse(a, b)
        b["a6_entered"] = False                      # arms no longer follow the header
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(b, "D.3b")
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "d3b_note.md"
            note.write_text("x\napproved: true\na6_entered: true\n")
            self.assertTrue(d3.read_a6_declaration(note))
            for bad in ("approved: true\na6_entered: true\na6_entered: false\n",   # two declarations
                        "approved: false\na6_entered: true\n",                       # not signed
                        "a6_entered: true\n"):                                         # no approval line
                note.write_text(bad)
                with self.assertRaises(d3.D3InputError):
                    d3.read_a6_declaration(note)
            note.write_bytes(b"approved: true\n\xff\xfe")
            with self.assertRaises(d3.D3InputError):                                    # not UTF-8: refused, no traceback
                d3.read_a6_declaration(note)
            with self.assertRaises(d3.D3InputError):
                d3.read_a6_declaration(Path(tmp) / "missing.md")

    def test_repetitions_are_bound_to_the_declared_count(self):
        self.assertEqual(d3.REPETITIONS, 1)
        t = synthetic_table(reps=2, seed=7, effects={"A2": 1.0})
        rep = d3.analyse(t, d3b_not_run="not_started")
        self.assertIn("D.3a_all_repetitions", rep["families"])
        self.assertNotIn("reject_holm", rep["families"]["D.3a_all_repetitions"]["contrasts"][0])
        ys0 = d3.outcome_matrix(t, 1)
        node = d3.NODES[0]
        rep0 = [r["y_raw"] / t["sigma_node"][node] for r in t["rows"]
                if r["arm"] == "A2" and r["node"] == node and r["instance_seed"] == 6201 and r["repetition"] == 0]
        self.assertAlmostEqual(ys0["A2"][node][0], rep0[0], places=12)
        t0 = synthetic_table(seed=7)
        t0["repetitions"] = 0
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(t0, "D.3a")

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

    def test_cli_writes_once_and_never_overwrites(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            predecl = tdir / "predecl.md"
            predecl.write_text("synthetic pre-declaration\n")
            table = synthetic_table()
            table["predeclaration_sha256"] = hashlib.sha256(predecl.read_bytes()).hexdigest()
            (tdir / "d3a.json").write_text(json.dumps(table))
            args = ["analyse", "--d3a", str(tdir / "d3a.json"), "--d3b-not-run", "not_started",
                    "--predeclaration", str(predecl), "--out", str(tdir / "report.json")]
            with mock.patch.object(d3, "verify_sigma_against_noise_source", return_value=None):
                self.assertEqual(d3.main(args), 0)
                first = (tdir / "report.json").read_text()
                self.assertEqual(json.loads(first)["families"]["D.3b"]["status"], "not_run")
                self.assertEqual(d3.main(args), 2)
                self.assertEqual((tdir / "report.json").read_text(), first)
                d3b_args = ["analyse", "--d3a", str(tdir / "d3a.json"), "--d3b", str(tdir / "d3a.json"),
                            "--predeclaration", str(predecl), "--out", str(tdir / "r2.json")]
                self.assertEqual(d3.main(d3b_args), 2)       # --d3b without --d3b-note


def _fam(name, directions):
    """A synthetic analysed family: contrast name -> holm_direction."""
    return {"family": name, "status": "analysed",
            "contrasts": [{"contrast": c, "holm_direction": d} for c, d in directions.items()]}


D3A_NONE = {"A0R - A0": "none", "A2 - A0R": "none", "A1 - A0": "none", "A2 - A0": "none", "FIXR3 - A0": "none",
            "EGATE - A0": "none", "LADDER - A0": "none", "LADDER - A2": "none"}
D3B_NONE = {"A3 - A2": "none", "A5 - A2": "none", "A3 - A0": "none", "A5 - A0": "none", "A5 - A3": "none"}


class Revision4FamiliesTest(unittest.TestCase):
    """R1-D3-DECOMP, R1-D3B-UNCONDITIONAL: the two families and their multiplicity."""

    def test_declared_families_and_arms(self):
        self.assertEqual(d3.ARMS_D3A, ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER"))
        self.assertEqual(d3.CONTRASTS_D3A, (("A0R", "A0"), ("A2", "A0R"), ("A1", "A0"), ("A2", "A0"),
                                            ("FIXR3", "A0"), ("EGATE", "A0"), ("LADDER", "A0"), ("LADDER", "A2")))
        self.assertEqual(d3.CONTRASTS_D3B, (("A3", "A2"), ("A5", "A2"), ("A3", "A0"), ("A5", "A0"), ("A5", "A3")))
        self.assertEqual(d3.CONTRAST_A6, ("A6", "A5"))
        for arm in ("FIXR3", "EGATE", "LADDER", "A0", "A1"):      # rule layer off (pre-declaration §5)
            self.assertNotIn(arm, d3.RULE_LAYER_ARMS)
        self.assertIn("A0R", d3.RULE_LAYER_ARMS)
        self.assertNotIn("A0R", d3.SCREEN_ARMS)

    def test_d3b_family_has_five_contrasts_holm_over_five(self):
        a = synthetic_table(seed=1)
        b = synthetic_table(stage="D.3b", seed=2, effects={"A5": 1.5})
        rep = d3.analyse(a, b, a6_declared=False)
        fam = rep["families"]["D.3b"]
        self.assertEqual(len(fam["contrasts"]), 5)
        raw = [c["p_two_sided"] for c in fam["contrasts"]]
        adj, _ = d3.holm(raw)
        self.assertEqual([c["p_holm"] for c in fam["contrasts"]], adj)
        self.assertEqual(rep["design"]["D.3b"]["contrasts"], 5)
        self.assertEqual(rep["design"]["D.3a"]["contrasts"], 8)

    def test_rule_layer_and_screen_counts_follow_the_arm(self):
        t = synthetic_table()
        row = next(r for r in t["rows"] if r["arm"] == "FIXR3")
        row["rule_skips"] = 1
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(t, "D.3a")
        t = synthetic_table()
        row = next(r for r in t["rows"] if r["arm"] == "A0R")
        row["value_skips"] = 1                                 # A0R has no screen
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(t, "D.3a")
        t = synthetic_table()
        row = next(r for r in t["rows"] if r["arm"] == "A0R")
        row["rule_skips"] = 9                                  # allowed for A0R
        d3.validate_table(t, "D.3a")


class Revision4SchemaTest(unittest.TestCase):
    """Schema r1_d3_outcome/v2: GPU model, attempts, Y(w), compute and mechanism fields."""

    def setUp(self):
        self.table = synthetic_table()

    def refused(self, table, stage="D.3a"):
        with self.assertRaises(d3.D3InputError):
            d3.validate_table(table, stage)

    def test_v1_tables_are_refused(self):
        t = copy.deepcopy(self.table)
        t["schema"] = "r1_d3_outcome/v1"
        self.refused(t)
        t = copy.deepcopy(self.table)
        for row in t["rows"]:
            for key in d3.ROW_KEYS - d3.ROW_KEYS_V1:
                del row[key]
        self.refused(t)

    def test_one_gpu_model_per_instance(self):
        t = synthetic_table(gpu_by_node={d3.NODES[0]: "NVIDIA A100", d3.NODES[1]: "NVIDIA L40S"})
        d3.validate_table(t, "D.3a")                           # different models on different instances: allowed
        row = next(r for r in t["rows"] if r["arm"] == "A2" and r["node"] == d3.NODES[2])
        row["gpu_model"] = "NVIDIA A100"                       # one arm of an instance on another model
        self.refused(t)
        for bad in (None, "", " ", 5, "x" * 129):
            t = copy.deepcopy(self.table)
            t["rows"][0]["gpu_model"] = bad
            self.refused(t)

    def test_d3b_instances_keep_their_d3a_gpu_model(self):
        a = synthetic_table(seed=1, gpu_by_node={d3.NODES[3]: "NVIDIA A100"})
        b = synthetic_table(stage="D.3b", seed=2, gpu_by_node={d3.NODES[3]: "NVIDIA A100"})
        d3.analyse(a, b, a6_declared=False)
        b = synthetic_table(stage="D.3b", seed=2)
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, b, a6_declared=False)

    def test_budget_curve_fields(self):
        t = copy.deepcopy(self.table)
        row = next(r for r in t["rows"] if r["arm"] == "A2")
        _shrink(row, 12, d3.LLM_CALL_CAP, "llm_call_cap")
        d3.validate_table(t, "D.3a")
        row["y_raw_w"]["15"] = 0.0                             # w beyond the runs must be missing (null)
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["rows"][0]["y_raw_w"]["5"] = None                    # w reached must be present
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["rows"][0]["y_raw_w"]["20"] = t["rows"][0]["y_raw"] + 1.0   # Y(20) is the primary Y at w_final = 20
        self.refused(t)
        t = copy.deepcopy(self.table)
        t["rows"][0]["y_raw_w"] = {"5": 0.0, "10": 0.0, "15": 0.0}
        self.refused(t)

    def test_compute_and_mechanism_fields(self):
        cases = [("infra_attempts", 0), ("infra_attempts", 1.0), ("worker_seconds", -1.0),
                 ("wall_seconds", float("inf")), ("keeps", d3.W + 1), ("distinct_configs_executed", d3.W + 1),
                 ("duplicates_executed", 4), ("rule_skips", -1), ("proposals", d3.LLM_CALL_CAP + 1),
                 ("last_keep_run", 0), ("last_keep_run", None), ("last_improving_run", 13), ("llm_tokens_prompt", 1.5)]
        for key, value in cases:
            t = copy.deepcopy(self.table)
            row = next(r for r in t["rows"] if r["arm"] == "A2" and r["y_raw"] > 0)
            row[key] = value
            with self.subTest(key=key, value=value):
                self.refused(t)
        t = copy.deepcopy(self.table)
        row = next(r for r in t["rows"] if r["arm"] == "A0")
        row.update(keeps=0, last_keep_run=None, last_improving_run=None, infra_attempts=3)
        d3.validate_table(t, "D.3a")                           # repeated attempts are recorded, never an outcome


class Revision4HpoRefTest(unittest.TestCase):
    """R1-D3-HPO-REF: RS and SMAC3, descriptive, outside the Holm families."""

    def test_reference_rows_are_descriptive(self):
        a = synthetic_table(seed=1)
        h = synthetic_table(stage="HPO-REF", seed=3, effects={"SMAC3": 0.5})
        rep = d3.analyse(a, d3b_not_run="not_started", hpo=h)
        ref = rep["reference_rows"]
        self.assertEqual([c["contrast"] for c in ref["contrasts"]], ["RS - A0", "SMAC3 - A0", "RS - A2", "SMAC3 - A2"])
        for c in ref["contrasts"]:
            self.assertNotIn("p_two_sided", c)
            self.assertNotIn("reject_holm", c)
            self.assertIn("ci95_t", c)
        self.assertIn("outside the Holm families", ref["status"])
        self.assertEqual(len(rep["families"]["D.3a"]["contrasts"]), 8)   # the D.3a family is unchanged by HPO-REF
        self.assertIn("RS", rep["secondary"]["runs_to_match"])

    def test_reference_rows_schema(self):
        h = synthetic_table(stage="HPO-REF", seed=3)
        d3.validate_table(h, "HPO-REF")
        cases = [("llm_calls", 5), ("gpu_model", GPU), ("memory_mode", d3.MEMORY_MODE), ("proposer_gpu_seconds", 1.0),
                 ("ended_on", "llm_call_cap")]
        for key, value in cases:
            t = copy.deepcopy(h)
            t["rows"][0][key] = value
            with self.subTest(key=key), self.assertRaises(d3.D3InputError):
                d3.validate_table(t, "HPO-REF")
        t = copy.deepcopy(h)
        rs = next(r for r in t["rows"] if r["arm"] == "RS")
        _shrink(rs, 15, 0, "proposal_cap")
        rs["proposals"] = d3.HPO_PROPOSAL_CAP
        d3.validate_table(t, "HPO-REF")
        smac = next(r for r in t["rows"] if r["arm"] == "SMAC3")
        _shrink(smac, 15, 0, "proposal_cap")
        smac["proposals"] = d3.HPO_PROPOSAL_CAP
        with self.assertRaises(d3.D3InputError):              # the proposal cap ends only RS
            d3.validate_table(t, "HPO-REF")

    def test_reference_rows_pair_with_d3a(self):
        a = synthetic_table(seed=1)
        h = synthetic_table(stage="HPO-REF", seed=3)
        h["predeclaration_sha256"] = "d" * 64
        with self.assertRaises(d3.D3InputError):
            d3.analyse(a, d3b_not_run="not_started", hpo=h)


class Revision4ReadingsTest(unittest.TestCase):
    """Task local/20261126-16 points 2 and 3: the declared readings, set by rule."""

    def readings(self, d3a=None, d3b=None):
        fams = {"D.3a": _fam("D.3a", {**D3A_NONE, **(d3a or {})})}
        fams["D.3b"] = _fam("D.3b", {**D3B_NONE, **d3b}) if d3b is not None else {"status": "not_run"}
        return d3.declared_readings(fams)

    def test_no_rule_gain_is_row_five(self):
        r = self.readings(d3b={"A5 - A2": "favourable"})
        self.assertEqual(r["rule_gain"], "none")
        self.assertEqual({g: v["row"] for g, v in r["headline_by_gate_verdict"].items()},
                         {"pass": 5, "fail": 5, "stop": 5})
        r = self.readings({"A2 - A0": "unfavourable"}, {})
        self.assertEqual(r["rule_gain"], "harm")
        self.assertEqual(r["headline_by_gate_verdict"]["pass"]["row"], 5)
        self.assertTrue(r["notes"])

    def test_rule_and_learned_gain(self):
        r = self.readings({"A2 - A0": "favourable", "A2 - A0R": "favourable"}, {"A3 - A2": "favourable"})
        self.assertEqual((r["rule_gain"], r["learned_gain"], r["gain_source"]), ("gain", "gain", "one_step_rule_adds"))
        self.assertEqual(r["headline_by_gate_verdict"]["pass"]["row"], 1)
        self.assertEqual(r["headline_by_gate_verdict"]["fail"]["row"], 2)
        r = self.readings({"A2 - A0": "favourable"}, {"A3 - A2": "unfavourable", "A5 - A0": "favourable"})
        self.assertEqual(r["learned_gain"], "harm")                  # A5 - A0 does not count for "A3 or A5 > A2"
        self.assertEqual(r["headline_by_gate_verdict"]["pass"]["row"], 3)
        self.assertEqual(r["headline_by_gate_verdict"]["fail"]["row"], 4)
        self.assertIsNone(r["headline_by_gate_verdict"]["stop"]["row"])

    def test_rule_layer_alone_is_not_credited_to_the_one_step_rule(self):
        r = self.readings({"A2 - A0": "favourable", "A0R - A0": "favourable", "A2 - A0R": "none"}, {})
        self.assertEqual(r["gain_source"], "rule_layer_alone")
        self.assertEqual(r["qualifier"], d3.RULE_LAYER_ALONE_TEXT)
        for gate in ("pass", "fail"):
            self.assertEqual(r["headline_by_gate_verdict"][gate]["headline"], d3.RULE_LAYER_ALONE_TEXT)
        r = self.readings({"A2 - A0": "favourable", "A0R - A0": "favourable", "A2 - A0R": "unfavourable"}, {})
        self.assertEqual(r["gain_source"], "rule_layer_alone")
        r = self.readings({"A2 - A0": "favourable"}, {})
        self.assertEqual(r["gain_source"], "not_separated")
        self.assertIsNone(r["qualifier"])

    def test_learned_not_run_leaves_rows_one_to_four_open(self):
        r = self.readings({"A2 - A0": "favourable"})
        self.assertEqual(r["learned_gain"], "not_run")
        self.assertIsNone(r["headline_by_gate_verdict"]["pass"]["row"])

    def test_readings_end_to_end_on_synthetic_effects(self):
        a = synthetic_table(seed=11, effects={"A0R": 1.5, "A2": 1.5})
        b = synthetic_table(stage="D.3b", seed=12)
        rep = d3.analyse(a, b, a6_declared=False)
        self.assertEqual(rep["readings"]["rule_gain"], "gain")
        self.assertEqual(rep["readings"]["gain_source"], "rule_layer_alone")


class Revision4SecondaryTest(unittest.TestCase):
    """R1-D3-OUTCOMES2 (a)-(e) and the detectable difference (task local/20261126-16 point 6)."""

    def test_detectable_difference_by_hand(self):
        dd = d3.detectable_difference(8)
        z = (stats.norm.ppf(1 - 0.05 / 16) + stats.norm.ppf(0.8)) / math.sqrt(126)
        self.assertAlmostEqual(dd["mde_first_step_sd_units_normal"], z, places=12)
        self.assertAlmostEqual(dd["mde_first_step_sd_units_normal"], 0.3186, places=4)
        self.assertAlmostEqual(dd["mde_first_step_sd_units_t"], 0.3233, places=4)
        self.assertAlmostEqual(d3.detectable_difference(5)["mde_first_step_sd_units_normal"], 0.3045, places=4)
        # revision 3's figure for six contrasts is reproduced
        self.assertAlmostEqual(d3.detectable_difference(6)["mde_first_step_sd_units_normal"], 0.310, places=3)
        self.assertAlmostEqual(dd["mde_last_step_sd_units_normal"], 0.2496, places=4)

    def test_budget_curve_missing_w_and_runs_to_match(self):
        t = synthetic_table(seed=21, effects={"A2": 2.0})
        node = d3.NODES[0]
        rows = [r for r in t["rows"] if r["arm"] == "A1" and r["node"] == node][:3]
        for r in rows:
            _shrink(r, 7, d3.LLM_CALL_CAP, "llm_call_cap")
        d3.validate_table(t, "D.3a")
        curve = d3.budget_curve(t)
        self.assertEqual(curve["A1"][node]["5"]["n"], 18)
        self.assertEqual(curve["A1"][node]["10"]["missing_w"], 3)
        self.assertEqual(curve["A1"][node]["10"]["n"], 15)
        vals = [r["y_raw_w"]["10"] / t["sigma_node"][node] for r in t["rows"]
                if r["arm"] == "A1" and r["node"] == node and r["y_raw_w"]["10"] is not None]
        self.assertAlmostEqual(curve["A1"][node]["10"]["mean"], float(np.mean(vals)), places=12)
        rtm = d3.runs_to_match(curve)
        self.assertIn("complete", rtm["A1"][node])
        for n in d3.NODES:                                     # a large effect reaches A0's Y(20) within the budget
            self.assertIsNotNone(rtm["A2"][n]["w"])

    def test_runs_to_match_by_hand(self):
        cell = lambda m: {"mean": m, "n": 18, "missing_w": 0}   # noqa: E731
        curves = {"A0": {n: {"5": cell(0.1), "10": cell(0.2), "15": cell(0.3), "20": cell(0.4)} for n in d3.NODES},
                  "A2": {n: {"5": cell(0.1), "10": cell(0.45), "15": cell(0.5), "20": cell(0.6)} for n in d3.NODES}}
        rtm = d3.runs_to_match(curves)
        self.assertEqual(rtm["A2"][d3.NODES[0]]["w"], 10)
        self.assertEqual(rtm["A0"][d3.NODES[0]]["w"], 20)
        self.assertTrue(rtm["A2"][d3.NODES[0]]["complete"])
        curves["A2"][d3.NODES[1]]["5"] = {"mean": 0.0, "n": 15, "missing_w": 3}   # a mean used rests on fewer
        self.assertFalse(d3.runs_to_match(curves)["A2"][d3.NODES[1]]["complete"])
        curves["A0"][d3.NODES[0]]["20"] = {"mean": None, "n": 0, "missing_w": 18}
        self.assertIsNone(d3.runs_to_match(curves)["A2"][d3.NODES[0]]["w"])

    def test_compute_and_mechanisms(self):
        t = synthetic_table(seed=22)
        out = d3.compute_and_mechanisms(t)
        self.assertEqual(out["A0R"]["mean_rule_skips"], 3.0)
        self.assertEqual(out["A0"]["mean_duplicates_executed"], 3.0)
        self.assertEqual(out["A2"]["campaigns"], 126)
        self.assertEqual(out["A2"]["mean_last_keep_run"], 12.0)

    def test_offline_online_agreement(self):
        off = {"A2": {n: 0.0 for n in d3.NODES}, "A3": {n: 1.0 for n in d3.NODES}, "A5": {n: 2.0 for n in d3.NODES}}
        on = {"A2": {n: 0.1 for n in d3.NODES}, "A3": {n: 0.2 for n in d3.NODES}, "A5": {n: 0.3 for n in d3.NODES}}
        out = d3.offline_online_agreement(off, on)
        self.assertEqual(out["mean_kendall_tau"], 1.0)
        on["A5"] = {n: 0.0 for n in d3.NODES}
        self.assertAlmostEqual(d3.offline_online_agreement(off, on)["mean_kendall_tau"], -1 / 3, places=12)
        flat = {a: {n: 0.0 for n in d3.NODES} for a in ("A2", "A3", "A5")}
        out = d3.offline_online_agreement(flat, on)
        self.assertIsNone(out["mean_kendall_tau"])
        self.assertEqual(out["nodes_with_tau"], 0)

    def test_cli_design_and_hpo_ref(self):
        from unittest import mock
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(d3.main(["design"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["with_A6"]["D.3b"]["contrasts"], 6)
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            predecl = tdir / "predecl.md"
            predecl.write_text("synthetic pre-declaration\n")
            sha = hashlib.sha256(predecl.read_bytes()).hexdigest()
            a, h = synthetic_table(), synthetic_table(stage="HPO-REF", seed=4)
            a["predeclaration_sha256"] = h["predeclaration_sha256"] = sha
            (tdir / "d3a.json").write_text(json.dumps(a))
            (tdir / "hpo.json").write_text(json.dumps(h))
            args = ["analyse", "--d3a", str(tdir / "d3a.json"), "--d3b-not-run", "not_started",
                    "--hpo-ref", str(tdir / "hpo.json"), "--predeclaration", str(predecl),
                    "--out", str(tdir / "report.json")]
            with mock.patch.object(d3, "verify_sigma_against_noise_source", return_value=None):
                self.assertEqual(d3.main(args), 0)
            rep = json.loads((tdir / "report.json").read_text())
            self.assertEqual(rep["inputs"]["hpo_ref_sha256"],
                             hashlib.sha256((tdir / "hpo.json").read_bytes()).hexdigest())
            self.assertEqual(rep["schema"], d3.REPORT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
