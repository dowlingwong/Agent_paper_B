"""Tests of the R1-SCREEN-MEASURE unit (design, seeds, analysis, runner, power) on synthetic data only.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed. No harness, no host, no real metric.
Run: ``python -m pytest r1/tests/test_screen_measure.py -q -p no:cacheprovider``.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
import uuid
from pathlib import Path
from unittest import mock

import numpy as np

import r1.harness
import r1.noise
from r1.harness import REPO
from r1.noise import screen_analysis as sa
from r1.noise import screen_design as sd
from r1.noise import screen_measure as sm
from r1.noise import screen_power as sp
from r1.noise import screen_seeds as ss

DESIGN = sd.build_design()


def _rows(run_dir: Path) -> list[dict]:
    return [json.loads(x) for x in (run_dir / sa.RUNS_FILE).read_text().splitlines() if x.strip()]


def _write_rows(run_dir: Path, rows: list[dict], update_manifest: bool = True) -> None:
    """Rewrite the run table; by default also refresh the manifest's runs_sha256, so that a test of another refusal is
    not refused by the table/manifest binding (review M2) instead."""
    (run_dir / sa.RUNS_FILE).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    if update_manifest:
        m = _manifest(run_dir)
        m["runs_sha256"] = sd.sha256_file(run_dir / sa.RUNS_FILE)
        _write_manifest(run_dir, m)


# ---- picklable fakes of a harness run (module level, so that ProcessPoolExecutor can send them; no harness) ----

def _fake_run(job: dict, _tmp: str) -> dict:
    """A run of a c0 job driven by extra job keys: sleep, raise ('runtime' or any), fail_condition, repeat_offset."""
    if job.get("sleep"):
        time.sleep(job["sleep"])
    if job.get("raise") == "runtime":
        raise sm.WorkerRuntimeStop("STOP: worker interpreter, versions, or package list mismatch")
    if job.get("raise"):
        raise ValueError("fake run failure")
    fail = job.get("fail_condition") in (job["condition"], "any")
    metric = None if fail else 0.5 + 1e-4 * job["seed"] + (job.get("repeat_offset", 0.0)
                                                            if job["condition"] == "repeat" else 0.0)
    return {"node": job["node"], "config": job["config"], "condition": job["condition"], "seed": job["seed"],
            "metric": metric, "success": not fail, "failure": "fake failure" if fail else None,
            "edit_applied": None, "values_before": {}, "values_after": {}, "wall_seconds": 0.0}


def _fake_smoke_run(job: dict, _tmp: str, runtime_expected=None, data_cache=None, data_trees=None) -> dict:
    """A smoke run with every edit applied as declared; openml_climate c35 returns c3's metric (an inert edit)."""
    node = DESIGN["nodes"][job["node"]]
    base = {e["symbol"]: e["old"] for e in node["edits"]}
    before = {**base, **{e["symbol"]: e["new"] for e in job["edits"][:-1]}}
    after = {**before, **({job["edits"][-1]["symbol"]: job["edits"][-1]["new"]} if job["edits"] else {})}
    cid = "c3" if (job["node"], job["config"]) == ("openml_climate", "c35") else job["config"]
    metric = 0.5 + 0.001 * list(node["configs"]).index(cid) + 0.0001 * sd.T0_NODES.index(job["node"])
    return {"node": job["node"], "config": job["config"], "condition": job["condition"], "seed": job["seed"],
            "metric": metric, "success": True, "failure": None, "edit_applied": True if job["edits"] else None,
            "values_before": before, "values_after": after, "wall_seconds": 0.0}


def _c0_jobs(n_rest: int = 20) -> list[dict]:
    """The first-seed run and the repeat at 3301, then n_rest further seeds, of digits_mlp c0 (no edit)."""
    job = {"node": "digits_mlp", "config": "c0", "edits": []}
    return [{**job, "condition": "seed", "seed": 3301}, {**job, "condition": "repeat", "seed": 3301}] + \
        [{**job, "condition": "seed", "seed": s} for s in range(3302, 3302 + n_rest)]


def _manifest(run_dir: Path) -> dict:
    return json.loads((run_dir / "manifest.json").read_text())


def _write_manifest(run_dir: Path, m: dict) -> None:
    (run_dir / "manifest.json").write_text(json.dumps(m, sort_keys=True))


class DesignTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(DESIGN["n_configs"], 84)
        self.assertEqual(DESIGN["n_seed_runs"], 84 * 120)
        self.assertEqual(DESIGN["n_triples"], 72)
        self.assertEqual(DESIGN["n_primary_triples"], 20)
        self.assertEqual(DESIGN["testable_nodes"], ["digits_mlp", "openml_climate"])
        per = {n: (v["n_configs"], v["n_triples"], v["n_primary_triples"]) for n, v in DESIGN["nodes"].items()}
        self.assertEqual(per["digits_mlp"], (15, 18, 18))
        self.assertEqual(per["tabular_mlp"], (15, 18, 0))
        self.assertEqual(per["openml_climate"], (9, 6, 2))
        for n in ("openml_breast_w", "openml_credit_approval", "openml_ionosphere", "openml_sonar", "openml_wdbc"):
            self.assertEqual(per[n], (9, 6, 0))

    def test_nodes_are_the_t0_nodes(self):
        from r1.c3.p3_split import T0_NODES
        self.assertEqual(tuple(sd.T0_NODES), tuple(T0_NODES))
        self.assertEqual(set(sd.DECISION_NODES), set(T0_NODES))
        self.assertNotIn("openml_wdbc", sd.SEVEN_NODES)

    def test_exclusions_written_before_any_run(self):
        self.assertEqual(DESIGN["nodes"]["digits_mlp"]["excluded_children"], {"c34": "same_symbol"})
        self.assertEqual(DESIGN["nodes"]["tabular_mlp"]["excluded_children"], {"c24": "same_symbol"})
        openml = {"c12": "same_symbol", "c13": "identical_to:c3", "c14": "identical_to:c4", "c23": "identical_to:c3",
                  "c24": "identical_to:c4", "c34": "same_symbol", "c45": "identical_to:c4"}
        for n in sd.T0_NODES:
            if n.startswith("openml_"):
                self.assertEqual(DESIGN["nodes"][n]["excluded_children"], openml, n)

    def test_primary_rule_is_both_links(self):
        for n, v in DESIGN["nodes"].items():
            for t in v["triples"]:
                both = t["link_gp_rho_joint"] < sd.NEAR_DUPLICATE and t["link_pc_rho_joint"] < sd.NEAR_DUPLICATE
                self.assertEqual(t["primary"], both, t["id"])
                self.assertEqual(t["pc_only_rule"], t["link_pc_rho_joint"] < sd.NEAR_DUPLICATE)
                if t["primary"]:
                    self.assertTrue(all(p > sa.THRESHOLD for p in t["reference_partial"].values()), t["id"])

    def test_reference_partial_symmetric_and_calibrated(self):
        for v in DESIGN["nodes"].values():
            by_child = {}
            for t in v["triples"]:
                by_child.setdefault(t["c"], []).append(t["reference_partial"])
            for pair in by_child.values():
                self.assertEqual(pair[0], pair[1])
        # T5 calibration of screening_test: link 0.82 on both sides gives 0.24 and 0.37
        self.assertAlmostEqual(sd.shared_lineage_partial(0.7082, 0.82, 0.82), 0.24, places=2)
        self.assertAlmostEqual(sd.shared_lineage_partial(0.7891, 0.82, 0.82), 0.37, places=2)
        self.assertEqual(sd.shared_lineage_partial(0.0, 0.7, 0.6), 0.0)
        # a near-duplicate link makes the partial small even with a large shared share
        self.assertLess(sd.shared_lineage_partial(0.7082, 0.999, 0.70), 0.03)

    def test_pinned_inputs_refuse_a_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            for rel in [sd.NOISE_SOURCE, *sd.EDIT_SOURCES]:
                (Path(tmp) / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(REPO / rel, Path(tmp) / rel)
            self.assertEqual(sd.design_sha256(sd.build_design(Path(tmp))), sd.design_sha256(DESIGN))
            p = Path(tmp) / sd.NOISE_SOURCE
            p.write_bytes(p.read_bytes() + b" ")
            with self.assertRaises(sd.DesignError):
                sd.build_design(Path(tmp))


class SeedTest(unittest.TestCase):
    def test_block_is_clear(self):
        rep = ss.check_block()
        self.assertEqual(rep["block"], [3301, 3420, 120])

    def test_clashes_refused(self):
        for bad in (range(2990, 3110), range(3961, 4081), range(6151, 6271), range(50, 170)):
            with self.assertRaises(ss.SeedClash):
                ss.check_block(tuple(bad))
        with self.assertRaises(ss.SeedClash):
            ss.check_block(tuple(range(3301, 3420)))           # 119 seeds
        with self.assertRaises(ss.SeedClash):
            ss.check_block((3301,) * 120)

    def test_reserved_copy_equals_d3_blob(self):
        branch, path, blob = ss.D3_SOURCE
        r = subprocess.run(["git", "-C", str(REPO), "cat-file", "-p", blob], capture_output=True)
        if r.returncode:
            self.skipTest(f"blob {blob} of {branch}:{path} not in this repository")
        tree = ast.parse(r.stdout.decode())
        value = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "RESERVED_SEED_NAMESPACES"
                                                     for t in node.targets):
                value = ast.literal_eval(node.value)
        self.assertEqual(value, ss.RESERVED_SEED_NAMESPACES)
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and hasattr(node.targets[0], "id"):
                try:
                    consts[node.targets[0].id] = ast.literal_eval(node.value)
                except ValueError:
                    pass
        self.assertEqual(consts["SMOKE_SEEDS"], ss.D3_SMOKE)
        self.assertEqual((consts["REPLICATE_SEED_BASE"], consts["AUDIT_SEED_BASE"]), (6500, 6700))

    def test_hex_only(self):
        self.assertFalse(ss.hex_only("sha `8f033b81…3413d`", ss.TOKEN))   # 5-character fragment: listed
        self.assertTrue(ss.hex_only("digest abcdef3350fedcba", ss.TOKEN))
        self.assertFalse(ss.hex_only("seeds 3301-3420", ss.TOKEN))
        self.assertFalse(ss.hex_only("x 3350 and deadbeef3360", ss.TOKEN))


class StatisticsTest(unittest.TestCase):
    def test_triple_partial_exclusions(self):
        rng = np.random.default_rng(0)
        g, p, c = rng.normal(size=(3, 50))
        self.assertEqual(sa.triple_partial(g, p, c)[1], "ok")
        self.assertEqual(sa.triple_partial(g, g, c)[1], "identical_members")
        self.assertEqual(sa.triple_partial(np.ones(50), p, c)[1], "zero_spread")
        self.assertEqual(sa.triple_partial(g, g + 1e-6 * p, c)[1], "near_singular")
        self.assertEqual(sa.triple_partial(g[:3], p[:3], c[:3])[1], "too_few_seeds")
        self.assertEqual(sa.triple_partial(np.r_[g[:-1], np.nan], p, c)[1], "non_finite")

    def test_partial_closed_form(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=(3, 20000))
        g = x[0]
        p = 0.8 * g + 0.6 * x[1]
        c = 0.7 * p + math.sqrt(1 - 0.49) * x[2]                 # Markov: partial 0
        self.assertLess(abs(sa.triple_partial(g, p, c)[0]), 0.03)

    def test_bootstrap_equals_loop(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=(5, 120))
        x[1] += x[0]
        x[2] += x[1]
        x[4] += x[3] + x[0]
        idx = np.array([[0, 1, 2], [0, 3, 4], [0, 1, 4]])
        iv, _, _ = sa.seed_bootstrap(x, idx, n_boot=300, seed=11)
        draws = np.random.default_rng(11).integers(0, 120, size=(300, 120))
        means = [np.mean([sa.triple_partial(x[a][d], x[b][d], x[c][d])[0] for a, b, c in idx]) for d in draws]
        lo, hi = np.quantile(means, [0.025, 0.975])
        self.assertAlmostEqual(iv[0.95][0], lo, places=12)
        self.assertAlmostEqual(iv[0.95][1], hi, places=12)

    def test_bootstrap_chunk_does_not_matter(self):
        rng = np.random.default_rng(3)
        x = rng.normal(size=(4, 120))
        idx = np.array([[0, 1, 2], [0, 1, 3]])
        a = sa.seed_bootstrap(x, idx, n_boot=400)
        with mock.patch.object(sa, "BOOT_CHUNK", 7):
            b = sa.seed_bootstrap(x, idx, n_boot=400)
        self.assertEqual(a, b)

    def test_bootstrap_counts_empty_resamples(self):
        """Review N5: a resample in which every eligible triple is undefined is counted and left out of the interval."""
        x = np.random.default_rng(7).normal(size=(3, 6))       # 6 seeds: some resamples are degenerate
        idx = np.array([[0, 1, 2]])
        iv, dropped, empty = sa.seed_bootstrap(x, idx, n_boot=1000, seed=13)
        draws = np.random.default_rng(13).integers(0, 6, size=(1000, 6))
        loop = [sa.triple_partial(x[0][d], x[1][d], x[2][d])[0] for d in draws]
        self.assertEqual(empty, sum(v is None for v in loop))
        self.assertEqual(dropped, empty)                        # one triple: every undefined cell empties a resample
        self.assertGreater(empty, 0)
        means = [v for v in loop if v is not None]
        self.assertAlmostEqual(iv[0.95][0], float(np.quantile(means, 0.025)), places=12)

    def test_identical_configs(self):
        """Review M3: bit-identical vectors over the complete seeds are found, near-identical ones are not."""
        v = {"c0": [0.1, 0.2, 0.3], "c3": [0.4, 0.5, 0.6], "c35": [0.4, 0.5, 0.6], "c5": [0.4, 0.5, 0.6 + 1e-15]}
        self.assertEqual(sa.identical_configs(v), [["c3", "c35"]])
        self.assertEqual(sa.identical_configs({"c0": [1.0], "c1": [2.0]}), [])

    def test_kernel_gives_partial_near_zero(self):
        node = DESIGN["nodes"]["digits_mlp"]
        vals = sp.simulate(node, 0.0, np.random.default_rng(4), k=3000)
        res = sa.node_test(vals, node["triples"], n_boot=200)
        self.assertEqual(res["n_eligible"], 18)
        self.assertLess(abs(res["estimate"]), 0.03)
        self.assertEqual(res["verdict"], "NO_SHARED")
        self.assertAlmostEqual(sp.mean_population_partial(node, 0.0), 0.0, places=12)

    def test_shared_gives_positive_partial_matching_the_model(self):
        node = DESIGN["nodes"]["digits_mlp"]
        s = sd.REFERENCE_SHARES[0]
        vals = sp.simulate(node, s, np.random.default_rng(5), k=4000)
        res = sa.node_test(vals, node["triples"], n_boot=200)
        self.assertGreater(res["estimate"], 0.2)
        self.assertLess(abs(res["estimate"] - sp.mean_population_partial(node, s)), 0.03)
        self.assertEqual(res["verdict"], "SHARED")

    def test_not_tested_by_design(self):
        node = DESIGN["nodes"]["tabular_mlp"]
        vals = sp.simulate(node, 0.7, np.random.default_rng(6))
        res = sa.node_test(vals, node["triples"], n_boot=50)
        self.assertEqual((res["verdict"], res["not_tested_reason"]), ("NOT_TESTED", "no_triple_in_design"))
        self.assertGreater(sa.node_test(vals, node["triples"], n_boot=50, select="all")["n_eligible"], 0)
        with self.assertRaises(sa.AnalysisRefused):
            sa.node_test(vals, node["triples"], select="something_else")

    def test_failure_rule(self):
        tab = {"c0": {s: 0.5 for s in sd.SEED_BLOCK}, "c1": {s: 0.5 for s in sd.SEED_BLOCK},
               "c2": {s: 0.5 for s in sd.SEED_BLOCK}}
        for s in sd.SEED_BLOCK[:7]:
            tab["c2"][s] = None                                    # 7 > 6: c2 dropped
        for s in sd.SEED_BLOCK[10:13]:
            tab["c1"][s] = None                                    # 3 seeds dropped node-wide
        values, rec = sa.complete_values(tab)
        self.assertEqual(set(values), {"c0", "c1"})
        self.assertEqual(rec["n_complete_seeds"], 117)
        self.assertEqual(rec["dropped_configs"], {"c2": 7})
        tab["c0"] = {s: None for s in sd.SEED_BLOCK}
        self.assertEqual(sa.complete_values(tab)[0], {})

    def test_decision(self):
        v = {n: "NO_SHARED" for n in sd.T0_NODES}
        self.assertEqual(sa.decision(v), "R1_THEORY_RHO_2_FINAL")
        v["openml_wdbc"] = "SHARED"
        self.assertEqual(sa.decision(v), "PROPOSE_SEVENTH_D3A_ARM")
        self.assertEqual(sa.decision(v, sd.SEVEN_NODES), "R1_THEORY_RHO_2_FINAL")
        self.assertAlmostEqual(sa.bonferroni_level(DESIGN), 0.975)
        self.assertEqual(sa.decide(0.11, 0.3), "SHARED")
        self.assertEqual(sa.decide(-0.2, 0.09), "NO_SHARED")
        self.assertEqual(sa.decide(0.05, 0.2), "INCONCLUSIVE")
        self.assertEqual(sa.decide(float("nan"), 0.2), "INCONCLUSIVE")


class RunAndRefusalTest(unittest.TestCase):
    """One stub run (s = 0) and one (s = 0.7891), then mutated copies for every refusal."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="smeas_test_"))
        cls.run0 = cls.tmp / "stub0"
        cls.run1 = cls.tmp / "stub1"
        assert sm.main(["run", "--stub", "--stub-shared", "0", "--out", str(cls.run0)]) == 0
        assert sm.main(["run", "--stub", "--stub-shared", "0.7891", "--out", str(cls.run1)]) == 0

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, name: str) -> Path:
        dst = self.tmp / name
        shutil.copytree(self.run0, dst)
        return dst

    def refused(self, run_dir: Path, engineering: bool = True, match: str | None = None, **kw):
        """The analysis refuses; with *match*, for the intended reason (a regex on the message)."""
        ctx = self.assertRaisesRegex(sa.AnalysisRefused, match) if match else self.assertRaises(sa.AnalysisRefused)
        with ctx:
            sa.analyse(run_dir, engineering=engineering, n_boot=kw.pop("n_boot", 100), **kw)

    def evidence_copy(self, name: str) -> Path:
        """A stub table relabelled as a complete evidence launch record (review M2): load_run accepts it."""
        d = self.copy(name)
        m = _manifest(d)
        m.update({"label": "EVIDENCE", "stub": False, "preflight": {"note": "docs/r1/authorizations/x.md"},
                  "harness": {"commit": sa.HARNESS_COMMIT, "branch": "x", "dirty": False},
                  "edit_sets": {n: "equal" for n in sd.T0_NODES}})
        _write_manifest(d, m)
        return d

    def test_plan(self):
        jobs = sm.plan(DESIGN)
        self.assertEqual(len(jobs), 84 * 121)
        self.assertTrue(all(j["seed"] == 3301 for j in jobs[:168]))
        self.assertEqual(sum(j["condition"] == "repeat" for j in jobs), 84)
        self.assertEqual(len(sm.plan(DESIGN, seeds=(sm.SMOKE_SEED,))), 168)
        m = _manifest(self.run0)
        self.assertEqual((m["planned_runs"], m["written_runs"], m["stop"], m["label"]),
                         (10164, 10164, None, "ENGINEERING_ONLY"))
        self.assertEqual(m["runs_sha256"], sd.sha256_file(self.run0 / sa.RUNS_FILE))
        self.assertEqual(m["seeds"], list(sd.SEED_BLOCK))         # review N6: the seeds actually planned

    def test_stub_analysis(self):
        res0 = sa.analyse(self.run0, engineering=True, n_boot=300)
        self.assertNotIn("SHARED", res0["verdicts"].values())
        self.assertEqual(res0["decision"], "R1_THEORY_RHO_2_FINAL")
        res1 = sa.analyse(self.run1, engineering=True, n_boot=300)
        self.assertEqual(res1["verdicts"]["digits_mlp"], "SHARED")
        self.assertEqual(res1["decision"], "PROPOSE_SEVENTH_D3A_ARM")
        for res in (res0, res1):
            for n in sd.T0_NODES:
                if n not in DESIGN["testable_nodes"]:
                    self.assertEqual(res["verdicts"][n], "NOT_TESTED")
            self.assertEqual(res["nodes"]["digits_mlp"]["primary"]["bootstrap_empty_resamples"], 0)

    def test_evidence_mode_refuses_engineering_table(self):
        self.refused(self.run0, engineering=False, n_boot=sa.N_BOOT, match="only an EVIDENCE table")

    def test_evidence_mode_refuses_other_n_boot(self):
        d = self.evidence_copy("nboot")
        self.refused(d, engineering=False, n_boot=500, match="B = 2,000")

    def test_evidence_label_with_stub_refused(self):
        d = self.copy("evstub")
        m = _manifest(d)
        m["label"] = "EVIDENCE"
        _write_manifest(d, m)
        self.refused(d, engineering=False, n_boot=sa.N_BOOT, match="only an EVIDENCE table")
        self.refused(d, engineering=True, match="ENGINEERING_ONLY tables only")

    def test_manifest_refusals(self):
        for key, value, match in (("seeds", list(range(3302, 3422)), "seeds"), ("stop", "deadline", "STOP"),
                                  ("design_sha256", "0" * 64, "design"), ("run_id", "other", "run_id"),
                                  ("schema", "r1_screen_measure_run/v1", "schema")):
            d = self.copy(f"m_{key}")
            m = _manifest(d)
            m[key] = value
            _write_manifest(d, m)
            self.refused(d, match=match)

    def test_table_bound_to_manifest(self):
        """Review M2: the table must be the one whose sha256 the runner wrote into the manifest."""
        d = self.copy("sha_missing")
        m = _manifest(d)
        del m["runs_sha256"]
        _write_manifest(d, m)
        self.refused(d, match="runs_sha256")
        d = self.copy("sha_other")
        m = _manifest(d)
        m["runs_sha256"] = "0" * 64
        _write_manifest(d, m)
        self.refused(d, match="runs_sha256")
        d = self.copy("sha_table_changed")
        rows = _rows(d)
        rows[500]["wall_seconds"] = 1.0                         # a change the other checks would not see
        _write_rows(d, rows, update_manifest=False)
        self.refused(d, match="runs_sha256")
        _write_rows(d, rows)                                    # the same table, bound: accepted
        sa.load_run(d, engineering=True)

    def test_evidence_launch_record_required(self):
        """Review M2: in evidence mode the preflight record, harness 6adf3859 clean and equal edit sets are required."""
        d = self.evidence_copy("ev_ok")
        manifest, rows, _ = sa.load_run(d, engineering=False)   # positive control: a complete record is accepted
        self.assertEqual(len(rows), 10164)
        cases = {
            "no_preflight": lambda m: m.pop("preflight"),
            "empty_preflight": lambda m: m.update(preflight={}),
            "other_harness": lambda m: m["harness"].update(commit="4012897a" + "0" * 32),
            "dirty_harness": lambda m: m["harness"].update(dirty=True),
            "dirty_unknown": lambda m: m["harness"].pop("dirty"),
            "no_harness": lambda m: m.pop("harness"),
            "edit_set_differs": lambda m: m["edit_sets"].update(openml_sonar="differs"),
            "edit_set_missing_node": lambda m: m["edit_sets"].pop("tabular_mlp"),
            "no_edit_sets": lambda m: m.pop("edit_sets"),
        }
        for name, change in cases.items():
            d = self.evidence_copy(f"ev_{name}")
            m = _manifest(d)
            change(m)
            _write_manifest(d, m)
            with self.assertRaisesRegex(sa.AnalysisRefused, "preflight|harness|edit_sets", msg=name):
                sa.load_run(d, engineering=False)

    def test_row_refusals(self):
        rows = _rows(self.run0)
        cases = {
            "extra": (rows + [{**rows[0], "seed": 3421}], "outside the declared design"),
            "duplicate": (rows + [rows[5]], "twice"),
            "missing": (rows[:-1], "misses"),
            "keys": ([{**rows[0], "extra": 1}] + rows[1:], "row keys"),
            "outside": (rows + [{**rows[0], "config": "c99"}], "outside the declared design"),
        }
        for name, (rr, match) in cases.items():
            d = self.copy(f"r_{name}")
            _write_rows(d, rr)
            self.refused(d, match=match)

    def test_determinism_refused(self):
        d = self.copy("det")
        rows = _rows(d)
        for r in rows:
            if r["condition"] == "repeat" and r["config"] == "c1" and r["node"] == "digits_mlp":
                r["metric"] += 1e-9
        _write_rows(d, rows)
        self.refused(d, match="determinism check failed")
        for condition in ("seed", "repeat"):                    # review M1: a failed run at 3301
            d = self.copy(f"det_fail_{condition}")
            rows = _rows(d)
            for r in rows:
                if (r["node"], r["config"], r["condition"], r["seed"]) == ("digits_mlp", "c1", condition, 3301):
                    r.update(metric=None, success=False, failure="fake")
            _write_rows(d, rows)
            self.refused(d, match="determinism unverifiable")

    def test_identical_configurations_refused(self):
        """Review M3: class_weight inert under random_forest would make c35 equal c3 on openml_climate."""
        d = self.copy("ident")
        rows = _rows(d)
        c3 = {(r["condition"], r["seed"]): r["metric"] for r in rows
              if (r["node"], r["config"]) == ("openml_climate", "c3")}
        for r in rows:
            if (r["node"], r["config"]) == ("openml_climate", "c35"):
                r["metric"] = c3[(r["condition"], r["seed"])]
        _write_rows(d, rows)
        self.refused(d, match=r"openml_climate: configurations \[\['c3', 'c35'\]\] have bit-identical")
        d = self.copy("ident_one_seed")                         # identical at one seed only: accepted
        rows = _rows(d)
        for r in rows:
            if (r["node"], r["config"], r["seed"]) == ("openml_climate", "c35", 3350):
                r["metric"] = c3[(r["condition"], r["seed"])]
        _write_rows(d, rows)
        sa.analyse(d, engineering=True, n_boot=20)

    def test_edit_refusals(self):
        for name, match in (("not_applied", "edit not applied"), ("not_verified", "edit not verified")):
            d = self.copy(f"e_{name}")
            rows = _rows(d)
            for r in rows:
                if r["node"] == "digits_mlp" and r["config"] == "c12" and r["seed"] == 3350:
                    if name == "not_applied":
                        r["edit_applied"] = False
                    else:
                        r["values_after"] = dict(r["values_before"])
            _write_rows(d, rows)
            self.refused(d, match=match)

    def test_protected_paths_refused(self):
        sealed = self.tmp / "r1_sealed" / "x"
        sealed.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.run0, sealed)
        self.refused(sealed)
        marked = self.tmp / "marked"
        marked.mkdir()
        (marked / "evidence_completion.json").write_text("{}")
        shutil.copytree(self.run0, marked / "run")
        self.refused(marked / "run")
        for part in ("label_block_x", "test_block_y"):
            p = self.tmp / part / "run"
            shutil.copytree(self.run0, p)
            self.refused(p)

    def test_runner_refusals(self):
        with self.assertRaises(SystemExit):
            sm.main(["run", "--stub", "--out", str(self.run0)])               # exists: never resumed
        with self.assertRaises(SystemExit):
            sm.main(["run", "--evidence", "--out", str(self.tmp / "ev")])      # not under results/r1/screen_measure
        with self.assertRaises(SystemExit):
            sm.main(["run", "--stub", "--workers", "17", "--out", str(self.tmp / "w17")])
        with self.assertRaises(SystemExit):
            sm.main(["run", "--stub", "--out", str(REPO / sm.EVIDENCE_OUT_ROOT / "x")])

    def test_check_row(self):
        job = sm.plan(DESIGN)[0 + 2 * 7]                    # a first-seed run of a child or single
        job = next(j for j in sm.plan(DESIGN) if j["node"] == "digits_mlp" and j["config"] == "c12")
        base = {e["symbol"]: e["old"] for e in DESIGN["nodes"]["digits_mlp"]["edits"]}
        before = {**base, job["edits"][0]["symbol"]: job["edits"][0]["new"]}
        after = {**before, job["edits"][1]["symbol"]: job["edits"][1]["new"]}
        ok = {"node": "digits_mlp", "config": "c12", "seed": 3301, "edit_applied": True,
              "values_before": before, "values_after": after}
        self.assertIsNone(sm.check_row(ok, job))
        self.assertIn("edit_not_applied", sm.check_row({**ok, "edit_applied": False}, job))
        self.assertIn("edit_not_verified", sm.check_row({**ok, "values_after": before}, job))
        other = next(k for k in base if k not in after or after[k] == base[k])
        self.assertIn("undeclared_change", sm.check_row({**ok, "values_after": {**after, other: "7"}}, job))
        c0 = next(j for j in sm.plan(DESIGN) if j["config"] == "c0")
        self.assertIsNone(sm.check_row({"edit_applied": None, "values_before": base, "values_after": base,
                                        "node": "x", "config": "c0", "seed": 1}, c0))


class RunnerStopTest(unittest.TestCase):
    """Review M7: every STOP path of ``execute``, in-process and through the process pool, with fake run functions (no
    harness, no host). Each case checks the STOP reason and that the manifest is written with it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="smeas_stop_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_execute(self, jobs, in_process, deadline=3600.0, monitor=False, workers=2):
        out = self.tmp / f"run_{uuid.uuid4().hex[:8]}"
        out.mkdir()
        res = sm.execute(out, jobs, _fake_run, {}, workers, deadline, str(self.tmp), in_process=in_process,
                         monitor=monitor)
        self.assertEqual(json.loads((out / "manifest.json").read_text())["stop"], res["stop"])
        self.assertEqual(res["runs_sha256"], sd.sha256_file(out / sa.RUNS_FILE))
        return res, out

    def test_clean_run_has_no_stop(self):
        for in_process in (True, False):
            res, _ = self.run_execute(_c0_jobs(), in_process)
            self.assertEqual((res["stop"], res["written_runs"], res["failed_runs"]), (None, 22, 0))

    def test_failure_rate(self):
        for in_process in (True, False):
            jobs = _c0_jobs(298)                                 # 300 planned: STOP above 3 failed runs
            for j in jobs[10:13]:
                j["fail_condition"] = "any"
            res, _ = self.run_execute(jobs, in_process)
            self.assertIsNone(res["stop"], in_process)           # 3 of 300 = 1 %: not above
            self.assertEqual(res["failed_runs"], 3)
            jobs[13]["fail_condition"] = "any"
            res, _ = self.run_execute(jobs, in_process)
            self.assertEqual(res["stop"], "failure_rate 4 of 300 planned runs", in_process)

    def test_run_exception(self):
        for in_process in (True, False):
            jobs = _c0_jobs()
            jobs[5]["raise"] = "value"
            res, _ = self.run_execute(jobs, in_process)
            self.assertTrue(res["stop"].startswith("run_exception digits_mlp c0 3305: fake run failure"), res["stop"])

    def test_worker_runtime_stop_has_its_own_reason(self):
        """Review N2."""
        for in_process in (True, False):
            jobs = _c0_jobs()
            jobs[4]["raise"] = "runtime"
            res, _ = self.run_execute(jobs, in_process)
            self.assertTrue(res["stop"].startswith("worker_runtime digits_mlp c0 3304: STOP: worker interpreter"),
                            res["stop"])

    def test_determinism_mismatch(self):
        for in_process in (True, False):
            jobs = _c0_jobs()
            jobs[1]["repeat_offset"] = 1e-12
            res, _ = self.run_execute(jobs, in_process)
            self.assertEqual(res["stop"], "determinism digits_mlp c0 seed 3301", in_process)

    def test_failed_run_at_the_determinism_seed(self):
        """Review M1: a failed first run or repeat at 3301 is a STOP even though one failure is far below 1 %."""
        for in_process in (True, False):
            for k, condition in ((0, "seed"), (1, "repeat")):
                jobs = _c0_jobs(298)
                jobs[k]["fail_condition"] = condition
                res, _ = self.run_execute(jobs, in_process)
                self.assertEqual(res["stop"], "determinism_unverifiable digits_mlp c0 seed 3301", (in_process, k))
                self.assertEqual(res["failed_runs"], 1)

    def test_deadline(self):
        jobs = _c0_jobs(10)
        for j in jobs:
            j["sleep"] = 0.05
        res, _ = self.run_execute(jobs, True, deadline=0.12)
        self.assertEqual(res["stop"], "deadline")
        self.assertLess(res["written_runs"], 12)
        res, _ = self.run_execute(jobs, False, deadline=0.12, workers=2)
        self.assertEqual(res["stop"], "deadline")
        self.assertLess(res["written_runs"], 12)
        self.assertGreaterEqual(res["written_runs"], 2)          # the runs in flight finish and are written

    def test_cotenancy_breach(self):
        bad = {"utc": "t", "cpus": 40, "load1": 35.0, "our_workers": 0, "free_for_others": 5.0, "ok": False}
        with mock.patch.object(sm, "cotenancy", return_value=bad) as co:
            res, out = self.run_execute(_c0_jobs(), False, monitor=True)
        self.assertEqual(res["stop"], "cotenancy 5.0 cores left to other users")
        self.assertEqual(res["written_runs"], 0)                 # sampled before the first submission
        self.assertEqual(json.loads((out / "cotenancy.log").read_text().splitlines()[0])["ok"], False)
        co.assert_called_with(0)
        good = {**bad, "free_for_others": 26.0, "ok": True}
        with mock.patch.object(sm, "cotenancy", return_value=good):
            res, out = self.run_execute(_c0_jobs(), False, monitor=True)
        self.assertIsNone(res["stop"])
        self.assertTrue((out / "cotenancy.log").read_text().strip())

    def test_identity_flags(self):
        """Review M3: the smoke flags a configuration whose seed-999 metric equals c0's or a single-edit parent's."""
        node = DESIGN["nodes"]["openml_climate"]
        rows = [{"node": "openml_climate", "config": c, "condition": "seed", "seed": 999, "success": True,
                 "metric": 0.5 + 0.01 * k} for k, c in enumerate(node["configs"])]
        self.assertEqual(sm.identity_flags(rows, DESIGN), [])
        m = {r["config"]: r for r in rows}
        m["c35"]["metric"] = m["c3"]["metric"]                   # inert class_weight under random_forest
        m["c2"]["metric"] = m["c0"]["metric"]                    # inert C
        rows.append({**m["c1"], "condition": "repeat", "metric": m["c0"]["metric"]})   # repeats are not compared
        flags = sm.identity_flags(rows, DESIGN)
        self.assertEqual([(f["config"], f["identical_to"]) for f in flags], [("c2", "c0"), ("c35", "c3")])
        m["c15"]["metric"] = m["c25"]["metric"]                  # two children: not a parent pair, not flagged
        self.assertEqual(len(sm.identity_flags(rows, DESIGN)), 2)


class PreflightTest(unittest.TestCase):
    """Review M7: ``preflight_evidence`` with the published-main reader, the provenance, environment and harness checks
    and the co-tenancy probe replaced by stubs (no host, no harness, no network)."""

    PRE_PATH = "docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_20990101.md"
    PLAN_ROW = "| R1-SCREEN-MEASURE | runs on deepthought CPUs under the conditions of R1-SWEEP2-B2-GO |"
    GOOD_CO = {"utc": "t", "cpus": 40, "load1": 2.0, "our_workers": 0, "free_for_others": 38.0, "ok": True}

    def setUp(self):
        self.audit = importlib.import_module("r1.c3.audit")
        self.args = argparse.Namespace(
            paper_root=str(REPO), note="docs/r1/authorizations/screen_measure_20990101.md", code_commit="a" * 40,
            code_review="docs/r1/reviews/SCREEN_MEASURE_REVIEW_20990101.md", workers=16,
            tmp=f"/tmp/{sm.EVIDENCE_TMP_PREFIX}unittest_{uuid.uuid4().hex}", data_cache_sha256="d" * 64)
        self.pre = b"the signed pre-declaration (stand-in bytes)"
        self.fields = {**sm.expected_note(self.args, DESIGN, Path(REPO).resolve()), "workers": "16",
                       "predeclaration": f"{self.PRE_PATH} sha256 {hashlib.sha256(self.pre).hexdigest()}"}
        self.plan = f"# PLAN\n\n{self.PLAN_ROW}\n"
        self.calls = []
        for name, value in (("evidence_paper_provenance", {"provenance": "ok"}),
                            ("evidence_environment", {"environment": "ok"}),
                            ("sweep2_harness_equivalence", {"equivalence": "ok"})):
            patcher = mock.patch.object(self.audit, name, side_effect=lambda *a, _n=name, _v=value:
                                        (self.calls.append(_n), _v)[1])
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in (mock.patch.object(self.audit, "_published_bytes", side_effect=self.published),
                        mock.patch.object(sm, "cotenancy", side_effect=lambda n: dict(self.GOOD_CO)),
                        mock.patch.dict(os.environ, {"AR_HARNESS_ROOT": "/nonexistent/harness"})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def published(self, root, rel):
        files = {self.args.note: self.note_text().encode(), "docs/r1/PLAN.md": self.plan.encode(),
                 self.PRE_PATH: self.pre}
        if rel not in files:
            raise ValueError(f"{rel} is not on the published main")
        return files[rel]

    def note_text(self) -> str:
        body = "".join(f"{k}: {v}\n" for k, v in self.fields.items())
        return f"# note\n\nprose: not a field\n\n## Key block\n\n```\n{body}```\n"

    def stops(self, match: str):
        with self.assertRaisesRegex(sm.RunStop, match):
            sm.preflight_evidence(self.args, DESIGN)

    def test_complete_note_passes(self):
        res = sm.preflight_evidence(self.args, DESIGN)
        self.assertEqual(res["predeclaration_sha256"], hashlib.sha256(self.pre).hexdigest())
        self.assertEqual(res["note_sha256"], hashlib.sha256(self.note_text().encode()).hexdigest())
        self.assertEqual((res["provenance"], res["environment"], res["harness_equivalence"]),
                         ({"provenance": "ok"}, {"environment": "ok"}, {"equivalence": "ok"}))
        self.assertEqual(res["seed_check"]["block"], [3301, 3420, 120])
        self.assertEqual(sorted(self.calls), ["evidence_environment", "evidence_paper_provenance",
                                              "sweep2_harness_equivalence"])

    def test_placeholder(self):
        self.fields["code_review"] = "<docs/r1/reviews/SCREEN_MEASURE_REVIEW_<date>.md>"
        self.stops("placeholder")

    def test_field_mismatch(self):
        for key, value in (("approved", "false"), ("design_sha256", "0" * 64), ("sha256_screen_analysis", "0" * 64),
                           ("harness_commit", "4012897a" + "0" * 32),
                           ("labels_read", "label_block")):
            saved = self.fields[key]
            self.fields[key] = value
            self.stops(rf"note fields differ from the run: \['{key}'\]")
            self.fields[key] = saved
        del self.fields["run_id"]
        self.stops(r"note fields differ from the run: \['run_id'\]")

    def test_workers_bound(self):
        for args_workers, note_workers, match in ((17, "16", "workers 17 not within"), (16, "8", "workers 16 not"),
                                                  (0, "16", "workers 0 not"), (16, "17", "workers 16 not"),
                                                  (16, "x", "missing or not an integer")):
            self.args.workers, self.fields["workers"] = args_workers, note_workers
            self.stops(match)
        del self.fields["workers"]
        self.args.workers = 16
        self.stops("missing or not an integer")

    def test_predeclaration_sha256(self):
        self.pre = b"a different pre-declaration"
        self.stops("pre-declaration's sha256 differs")
        self.fields["predeclaration"] = "docs/r1/authorizations/OTHER.md sha256 " + "0" * 64
        self.stops("pre-declaration: .* not on the published main")

    def test_plan_row_count(self):
        for plan in ("# PLAN\n", f"# PLAN\n{self.PLAN_ROW}\n{self.PLAN_ROW}\n",
                     "| R1-SCREEN-MEASURE | on the Mac under R1-SWEEP2-B2-GO |\n",
                     "| R1-SCREEN-MEASURE | on deepthought |\n"):
            self.plan = plan
            self.stops("exactly one R1-SCREEN-MEASURE row")

    def test_note_path_and_publication(self):
        for note in ("/abs/docs/r1/authorizations/n.md", "docs/r1/authorizations/../../PLAN.md", "docs/r1/n.md", None):
            self.args.note = note
            self.stops("--note must be")
        self.args.note = "docs/r1/authorizations/unpublished.md"
        self.fields = {}
        with mock.patch.object(self.audit, "_published_bytes", side_effect=ValueError("not on the published main")):
            self.stops("not on the published main")

    def test_scratch_directory(self):
        existing = tempfile.mkdtemp(prefix=sm.EVIDENCE_TMP_PREFIX, dir="/tmp")
        self.addCleanup(shutil.rmtree, existing, True)
        for tmp in (existing, "/var/tmp/" + sm.EVIDENCE_TMP_PREFIX + "x", "/tmp/r1_smeas_other_x"):
            self.args.tmp = tmp
            self.stops("--tmp must be a new directory")

    def test_cotenancy_at_start(self):
        with mock.patch.object(sm, "cotenancy", return_value={**self.GOOD_CO, "free_for_others": 9.0, "ok": False}):
            self.stops("co-tenancy before launch")


class SmokeModeTest(unittest.TestCase):
    """The engineering-smoke path of ``main`` with the harness replaced by stubs (no harness, no host): the manifest
    records seed 999 as its seeds (review N6) and the identity flags (review M3); the analysis refuses the table."""

    def test_smoke_manifest(self):
        tmp = Path(tempfile.mkdtemp(prefix="smeas_smoke_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        fake_e1 = types.SimpleNamespace(HARNESS=Path("/nonexistent/harness"), library_versions=lambda: {"fake": "1"})
        runtime = {"worker_python": "/batch/venv/bin/python3", "worker_prefix": "/batch/venv",
                   "worker_versions": {"scikit-learn": "1.8.0"}, "package_list_sha256": "a" * 64}

        good = {"utc": "t", "cpus": 40, "load1": 2.0, "our_workers": 0, "free_for_others": 38.0, "ok": True}
        with mock.patch.object(r1.noise, "e1_noise_floor", fake_e1, create=True), \
                mock.patch.object(r1.harness, "harness_commit",
                                  return_value={"commit": sm.HARNESS_COMMIT, "branch": "x", "dirty": False}), \
                mock.patch.object(sm, "check_edit_sets", return_value={n: "equal" for n in sd.T0_NODES}), \
                mock.patch("r1.c3.audit.evidence_environment", return_value=runtime) as checked, \
                mock.patch.object(sm, "_run_with_runtime", _fake_smoke_run), \
                mock.patch.object(sm, "read_data_cache", return_value={"tree_sha256": "d" * 64, "nodes": {}}), \
                mock.patch.object(sm, "cotenancy", return_value=good), \
                mock.patch.object(sm, "execute", wraps=sm.execute) as execute:
            with self.assertRaisesRegex(SystemExit, "--data-cache is required"):
                sm.main(["run", "--engineering-smoke", "--out", str(tmp / "smoke"), "--tmp", str(tmp / "scratch"),
                         "--workers", "2"])
            rc = sm.main(["run", "--engineering-smoke", "--out", str(tmp / "smoke"), "--tmp", str(tmp / "scratch"),
                          "--workers", "2", "--data-cache", str(tmp / "cache")])
            checked.assert_called_once_with(sm.REPO)
            self.assertEqual(execute.call_args.args[2].keywords["runtime_expected"], runtime)
            checked.side_effect = ValueError("runtime mismatch")
            with self.assertRaisesRegex(SystemExit, "engineering smoke requires the evidence runtime"):
                sm.main(["run", "--engineering-smoke", "--out", str(tmp / "bad"), "--tmp", str(tmp / "scratch"),
                         "--workers", "2", "--data-cache", str(tmp / "cache")])
            self.assertFalse((tmp / "bad").exists())
        self.assertEqual(rc, 0)
        m = _manifest(tmp / "smoke")
        self.assertEqual((m["label"], m["seeds"], m["planned_runs"], m["written_runs"], m["stop"]),
                         ("ENGINEERING_ONLY", [999], 168, 168, None))
        self.assertNotIn("seeds_smoke", m)
        self.assertEqual(m["data_cache"]["tree_sha256"], "d" * 64)
        self.assertEqual(m["worker_runtime_expected"], runtime)
        self.assertEqual(m["identity_flags"], [{"node": "openml_climate", "config": "c35", "identical_to": "c3",
                                                "seed": 999, "metric": _fake_smoke_run(
                                                    {"node": "openml_climate", "config": "c3", "condition": "seed",
                                                     "seed": 999, "edits": []}, "")["metric"]}])
        self.assertEqual(m["runs_sha256"], sd.sha256_file(tmp / "smoke" / sa.RUNS_FILE))
        with self.assertRaisesRegex(sa.AnalysisRefused, "seeds"):
            sa.analyse(tmp / "smoke", engineering=True, n_boot=10)


class NoteAndHostTest(unittest.TestCase):
    NOTE ="# t\n\nprose: not a field\n\n## Key block\n\n```\napproved: false\nlabel: EVIDENCE\n```\n"

    def test_key_block(self):
        self.assertEqual(sm.key_block(self.NOTE), {"approved": "false", "label": "EVIDENCE"})
        with self.assertRaises(sm.RunStop):
            sm.key_block(self.NOTE.replace("label: EVIDENCE", "label: EVIDENCE\nlabel: x"))
        with self.assertRaises(sm.RunStop):
            sm.key_block(self.NOTE.replace("label: EVIDENCE", "- label EVIDENCE"))
        with self.assertRaises(sm.RunStop):
            sm.key_block(self.NOTE.replace("## Key block", "## Keys"))

    def test_authorization_draft_parses_and_is_unsigned(self):
        drafts = sorted((REPO / "docs/r1/authorizations").glob("SCREEN_MEASURE_AUTHORIZATION_DRAFT_*.md"))
        if not drafts:
            self.skipTest("no authorization draft yet")
        fields = sm.key_block(drafts[-1].read_text())
        self.assertEqual(fields["approved"], "false")
        self.assertEqual(fields["design_sha256"], sd.design_sha256(DESIGN))
        self.assertEqual(fields["run_id"], sd.RUN_ID)
        self.assertEqual(fields["seed_block"], "3301-3420")
        self.assertEqual(fields["harness_commit"], sm.HARNESS_COMMIT)
        for rel in sm.CODE_FILES:
            self.assertIn(f"sha256_{Path(rel).stem}", fields)

    def test_cotenancy_convention(self):
        with mock.patch("os.getloadavg", return_value=(30.0, 0, 0)), \
                mock.patch("os.sched_getaffinity", return_value=set(range(40)), create=True):
            self.assertTrue(sm.cotenancy(16)["ok"])               # 40 - (30 - 16) = 26 >= 10
            self.assertTrue(sm.cotenancy(0)["ok"])                # 40 - 30 = 10: at the floor, allowed
            self.assertEqual(sm.cotenancy(0)["free_for_others"], 10.0)
        with mock.patch("os.getloadavg", return_value=(31.0, 0, 0)), \
                mock.patch("os.sched_getaffinity", return_value=set(range(40)), create=True):
            self.assertFalse(sm.cotenancy(0)["ok"])


class PowerTest(unittest.TestCase):
    def test_model_matches_design_reference_partials(self):
        for n in DESIGN["testable_nodes"]:
            node = DESIGN["nodes"][n]
            for s in sd.REFERENCE_SHARES:
                pp = sp.population_partials(node, s)
                for t in node["triples"]:
                    if t["primary"]:
                        self.assertAlmostEqual(pp[t["id"]], t["reference_partial"][f"{s:.4f}"], places=5)

    def test_covariance_positive_definite(self):
        for v in DESIGN["nodes"].values():
            for s in (0.0, 0.3, 0.7082, 0.95):
                _, cov = sp.lineage_covariance(v, s)
                self.assertGreater(np.linalg.eigvalsh(cov).min(), -1e-10)

    def test_solve_share(self):
        node = DESIGN["nodes"]["digits_mlp"]
        s = sp.solve_share(node, 0.10)
        self.assertGreaterEqual(sp.mean_population_partial(node, s), 0.10)
        self.assertLess(sp.mean_population_partial(node, s - 0.0001), 0.10)

    def test_closed_form_of_the_both_links_argument(self):
        """Review M5: under u + product kernel, partial = [s/(1-s)] sqrt(t_gp t_pc), t = (1-rho)/(1+rho), with rho the
        link's model correlation max(rho_E1, s); it matches the design's reference_partial on all 72 triples."""
        def closed(s, a, b):
            t = lambda r: (1 - r) / (1 + r)
            return s / (1 - s) * math.sqrt(t(max(a, s)) * t(max(b, s)))
        n = 0
        for v in DESIGN["nodes"].values():
            for t in v["triples"]:
                a, b = t["link_gp_rho_joint"], t["link_pc_rho_joint"]
                for s in sd.REFERENCE_SHARES:
                    self.assertAlmostEqual(closed(s, a, b), t["reference_partial"][f"{s:.4f}"], delta=1e-6)
                    n += 1
                for s in (0.1, 0.5, 0.9):
                    self.assertAlmostEqual(closed(s, a, b), sd.shared_lineage_partial(s, a, b), places=12)
        self.assertEqual(n, 144)
        # a near-duplicate link with the share below it: small; the share at the link itself: not small
        self.assertLess(sd.shared_lineage_partial(0.7082, 0.9991, 0.70), 0.03)
        self.assertGreater(sd.shared_lineage_partial(0.9991, 0.9994, 0.9991), 0.4)

    def test_all_triples_option(self):
        """Review M4: the all-triples selection of the power code (the row's test, an option for the author)."""
        with self.assertRaises(ValueError):
            sp.selected(DESIGN["nodes"]["digits_mlp"], "pc_only_rule")
        digits = DESIGN["nodes"]["digits_mlp"]
        self.assertEqual(sp.population_partials(digits, 0.7082, "all"), sp.population_partials(digits, 0.7082))
        tab = DESIGN["nodes"]["tabular_mlp"]
        self.assertEqual(len(sp.selected(tab, "all")), 18)
        self.assertEqual(sp.selected(tab, "primary"), [])
        self.assertAlmostEqual(sp.consistent_share(tab, "all"), 0.8783, places=4)
        # the review's bounds at the largest E1-consistent share: <= 0.052 on tabular_mlp, ~0.013 on the OpenML five
        self.assertLess(sp.mean_population_partial(tab, sp.consistent_share(tab, "all"), "all"), 0.052)
        for n in ("openml_breast_w", "openml_credit_approval", "openml_ionosphere", "openml_sonar", "openml_wdbc"):
            node = DESIGN["nodes"][n]
            self.assertLess(sp.mean_population_partial(node, sp.consistent_share(node, "all"), "all"), 0.0135, n)



# ---------------------------------------------------------------------------------------------------- data cache
# local/20261126-02: the 26 Nov smoke downloaded every OpenML dataset per run (no committed cache, the pilot fallback
# absent from a fresh harness worktree). The runs now use a declared, hashed cache and must leave it unchanged.

def _write_cache(root: Path, node: str, arff: bytes, *, extra: dict | None = None) -> None:
    import gzip
    d = root / node / "data_cache" / "openml" / "openml.org"
    (d / "data" / "v1" / "download" / "1").mkdir(parents=True)
    (d / "data" / "v1" / "download" / "1" / f"{node}.arff.gz").write_bytes(gzip.compress(arff, mtime=0))
    (d / "api" / "v1" / "json" / "data").mkdir(parents=True)
    (d / "api" / "v1" / "json" / "data" / "1.gz").write_bytes(gzip.compress(b"{}", mtime=0))
    for rel, data in (extra or {}).items():
        (root / node / "data_cache" / rel).write_bytes(data)


def _write_cache_manifest(root: Path, nodes: list[str]) -> dict:
    man = {"schema": sm.DATA_CACHE_SCHEMA, "nodes": {}}
    for n in nodes:
        files = sm.cache_tree(root / n / "data_cache")
        man["nodes"][n] = {"files": files, "tree_sha256": sm.tree_sha256(files)}
    man["tree_sha256"] = sm.tree_sha256({n: v["tree_sha256"] for n, v in man["nodes"].items()})
    (root / sm.DATA_CACHE_MANIFEST).write_text(json.dumps(man))
    return man


class DataCacheTest(unittest.TestCase):
    NODES = ["openml_climate", "openml_sonar"]           # no pilot cache: no pilot reference

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="smeas_cache_test_"))
        self.addCleanup(shutil.rmtree, self.root, True)
        for n in self.NODES:
            _write_cache(self.root, n, f"@relation {n}".encode())
        self.man = _write_cache_manifest(self.root, self.NODES)

    def test_manifest_checked_against_the_files(self):
        got = sm.read_data_cache(self.root, self.NODES)
        self.assertEqual(got["tree_sha256"], self.man["tree_sha256"])
        self.assertEqual(sorted(got["nodes"]), self.NODES)
        with self.assertRaisesRegex(sm.RunStop, "exactly the nodes"):
            sm.read_data_cache(self.root, self.NODES + ["openml_wdbc"])
        (self.root / "openml_sonar" / "data_cache" / "new.json").write_bytes(b"x")     # a file the manifest lacks
        with self.assertRaisesRegex(sm.RunStop, "differ from the data-cache manifest"):
            sm.read_data_cache(self.root, self.NODES)

    def test_tampered_total_and_stray_entries(self):
        self.man["tree_sha256"] = "0" * 64
        (self.root / sm.DATA_CACHE_MANIFEST).write_text(json.dumps(self.man))
        with self.assertRaisesRegex(sm.RunStop, "total tree_sha256"):
            sm.read_data_cache(self.root, self.NODES)
        _write_cache_manifest(self.root, self.NODES)
        (self.root / "stray").mkdir()
        with self.assertRaisesRegex(sm.RunStop, "unexpected entries"):
            sm.read_data_cache(self.root, self.NODES)

    def test_content_sha_ignores_the_gzip_header(self):
        import gzip
        a, b = self.root / "a.gz", self.root / "b.gz"
        a.write_bytes(gzip.compress(b"same", mtime=1))
        b.write_bytes(gzip.compress(b"same", mtime=2))
        self.assertNotEqual(sm._file_sha(a), sm._file_sha(b))
        self.assertEqual(sm._content_sha(a), sm._content_sha(b))
        bad = self.root / "bad.gz"
        bad.write_bytes(b"not gzip")
        with self.assertRaisesRegex(sm.RunStop, "not a gzip file"):
            sm._content_sha(bad)

    def test_pilot_reference(self):
        root = Path(tempfile.mkdtemp(prefix="smeas_pilot_"))
        self.addCleanup(shutil.rmtree, root, True)
        _write_cache(root, "openml_wdbc", b"@relation not the pilot's data")
        _write_cache_manifest(root, ["openml_wdbc"])
        with self.assertRaisesRegex(sm.RunStop, "differs from the E1 pilot"):
            sm.read_data_cache(root, ["openml_wdbc"])
        with mock.patch.dict(sm.PILOT_ARFF_SHA256, {"openml_wdbc": hashlib.sha256(b"@relation not the pilot's data").hexdigest()}):
            sm.read_data_cache(root, ["openml_wdbc"])
        two = Path(tempfile.mkdtemp(prefix="smeas_two_"))
        self.addCleanup(shutil.rmtree, two, True)
        _write_cache(two, "openml_sonar", b"@relation x", extra={"second.arff": b"% comment\n@RELATION y"})
        _write_cache_manifest(two, ["openml_sonar"])
        with self.assertRaisesRegex(sm.RunStop, "2 ARFF files"):
            sm.read_data_cache(two, ["openml_sonar"])

    def test_pilot_pins_are_the_four_pilot_nodes(self):
        self.assertEqual(sorted(sm.PILOT_ARFF_SHA256), ["openml_breast_w", "openml_credit_approval",
                                                         "openml_ionosphere", "openml_wdbc"])
        self.assertTrue(set(sm.PILOT_ARFF_SHA256) <= set(DESIGN["nodes"]))


class _FakeResult:
    def __init__(self, success, log, extra=None):
        self.success, self.raw_log_ref, self.extra = success, str(log), extra or {}
        self.changed_files, self.parsed_metrics = (), ({"val_auc": 0.9} if success else {})
        self.failure_message = None if success else "exit code 1"


class LineageDataCacheTest(unittest.TestCase):
    """``run_one_lineage`` with the harness replaced by a fake: the node copy gets the declared cache in place of the
    fallback copy, a run that downloads into the cache is the ``data_cache`` STOP, and a failed run's log tail is kept."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="smeas_lineage_"))
        self.addCleanup(shutil.rmtree, self.root, True)
        _write_cache(self.root / "cache", "openml_sonar", b"@relation sonar")
        self.seen = {}

    def fake_e1(self, *, download=False, success=True):
        test = self

        def prepare(node, work):
            d = work / node
            (d / "data_cache").mkdir(parents=True)
            (d / "data_cache" / "fallback.gz").write_bytes(b"pilot fallback copy")
            return d

        class Worker:
            def __init__(self, node_root, artifact_dir, timeout_seconds):
                self.root, self.art = node_root, artifact_dir

            def run_trial_at_seed(self, proposal, spec, i, train_seed, split_seed):
                test.seen["cache"] = sorted(p.name for p in (self.root / "data_cache").rglob("*") if p.is_file())
                if download:
                    (self.root / "data_cache" / "downloaded.json").write_bytes(b"from openml.org")
                self.art.mkdir(parents=True, exist_ok=True)
                (self.art / "run.log").write_text("Traceback ...\nURLError: temporary failure in name resolution\n")
                return _FakeResult(success, self.art / "run.log", {"failure_category": "data"} if not success else {})
        spec = types.SimpleNamespace(metric_name="val_auc")
        return types.SimpleNamespace(load_registered_node=lambda n, repo_root=None: spec, HARNESS=Path("/x"),
                                     _prepare_node=prepare, current_values=lambda d, s: {},
                                     LocalWorker=Worker, _edit_proposal=lambda s, e: None)

    def run_job(self, e1):
        job = {"node": "openml_sonar", "config": "c0", "condition": "seed", "seed": 999, "edits": []}
        with mock.patch.object(r1.noise, "e1_noise_floor", e1, create=True):
            trees = {"openml_sonar": sm.tree_sha256(sm.cache_tree(self.root / "cache" / "openml_sonar" / "data_cache"))}
            return sm.run_one_lineage(job, str(self.root), None, str(self.root / "cache"), trees)

    def test_declared_cache_replaces_the_fallback(self):
        row = self.run_job(self.fake_e1())
        self.assertEqual(self.seen["cache"], ["1.gz", "openml_sonar.arff.gz"])
        self.assertTrue(row["success"])
        self.assertNotIn("_failure_log", row)

    def test_download_during_the_run_is_a_stop_and_keeps_the_log(self):
        with self.assertRaisesRegex(sm.DataCacheStop, "cache changed during the run") as cm:
            self.run_job(self.fake_e1(download=True))
        self.assertIn("URLError", cm.exception.log_tail)                     # review M2

    def test_cache_changed_since_launch_is_a_stop(self):                        # review M1
        job = {"node": "openml_sonar", "config": "c0", "condition": "seed", "seed": 999, "edits": []}
        with mock.patch.object(r1.noise, "e1_noise_floor", self.fake_e1(), create=True):
            with self.assertRaisesRegex(sm.DataCacheStop, "changed since launch"):
                sm.run_one_lineage(job, str(self.root), None, str(self.root / "cache"), {"openml_sonar": "0" * 64})
            with self.assertRaisesRegex(sm.DataCacheStop, "missing"):
                sm.run_one_lineage({**job, "node": "openml_sonar"}, str(self.root), None, str(self.root / "nocache"),
                                   {"openml_sonar": "0" * 64})

    def test_data_cache_stop_survives_pickling(self):
        import pickle
        e = pickle.loads(pickle.dumps(sm.DataCacheStop("msg", "tail")))
        self.assertEqual((str(e), e.log_tail), ("msg", "tail"))

    def test_failed_run_keeps_its_log(self):
        row = self.run_job(self.fake_e1(success=False))
        self.assertFalse(row["success"])
        self.assertEqual(row["_failure_log"]["failure_category"], "data")
        self.assertIn("URLError", row["_failure_log"]["log_tail"])

    def test_failure_log_written_beside_the_runs_and_not_in_the_row(self):
        out = self.root / "out"
        out.mkdir()
        job = {"node": "openml_sonar", "config": "c0", "condition": "seed", "seed": 999, "edits": []}

        def run_fn(j, tmp):
            return {"node": j["node"], "config": j["config"], "condition": j["condition"], "seed": j["seed"],
                    "metric": None, "success": False, "failure": "exit code 1", "edit_applied": None,
                    "values_before": {}, "values_after": {}, "wall_seconds": 1.0,
                    "_failure_log": {"failure_category": None, "log_tail": "boom"}}
        man = sm.execute(out, [job], run_fn, {}, 1, 100.0, str(self.root), in_process=True)
        self.assertEqual(man["failed_runs"], 1)
        row = json.loads((out / sa.RUNS_FILE).read_text())
        self.assertNotIn("_failure_log", row)
        fail = json.loads((out / sm.FAILED_RUNS_FILE).read_text())
        self.assertEqual((fail["node"], fail["log_tail"], fail["failure"]), ("openml_sonar", "boom", "exit code 1"))


class BuildDataCacheTest(unittest.TestCase):
    """Build and verify each node's cache in order, then publish the manifest."""

    def test_build_then_read(self):
        import gzip
        root = Path(tempfile.mkdtemp(prefix="smeas_build_"))
        self.addCleanup(shutil.rmtree, root, True)
        harness = root / "harness"
        for n in ("openml_climate", "openml_sonar"):
            (harness / "nodes" / n).mkdir(parents=True)
            (harness / "nodes" / n / "dataset.json").write_text("{}")
        order, mutate = [], set()

        def prepare(node, work):
            d = work / node
            (d / "data_cache").mkdir(parents=True)
            (d / "data_cache" / ".gitkeep").write_text("")
            return d

        def load(node_dir, *, offline):
            node, cache = node_dir.name, node_dir / "data_cache"
            download = cache / "openml" / "openml.org" / "data" / "v1" / "download" / "52350"
            order.append((node, offline))
            if offline:
                self.assertTrue((download / f"{node}.arff.gz").is_file())
                if node in mutate:
                    (download / "unexpected.json").write_text("{}")
                return
            self.assertEqual(list(cache.iterdir()), [])
            download.mkdir(parents=True)
            (download / f"{node}.arff.gz").write_bytes(gzip.compress(b"@relation " + node.encode(), mtime=0))

        e1 = types.SimpleNamespace(HARNESS=harness, library_versions=lambda: {"scikit-learn": "1.8.0"},
                                   _prepare_node=prepare)
        hc = {"commit": sm.HARNESS_COMMIT, "branch": "x", "dirty": False}
        with mock.patch.object(r1.noise, "e1_noise_floor", e1, create=True), \
                mock.patch.object(r1.harness, "harness_commit", return_value=hc), \
                mock.patch.object(sm, "_load_openml_cache", load):
            got = sm.build_data_cache(DESIGN, root / "cache", str(root))
            self.assertEqual(got["nodes"], ["openml_climate", "openml_sonar"])
            self.assertEqual(order, [(n, offline) for n in got["nodes"] for offline in (False, True)])
            self.assertEqual(sm.read_data_cache(root / "cache", got["nodes"])["tree_sha256"], got["tree_sha256"])
            with self.assertRaisesRegex(sm.RunStop, "exists"):
                sm.build_data_cache(DESIGN, root / "cache", str(root))
            mutate.add("openml_sonar")
            with self.assertRaisesRegex(sm.RunStop, "openml_sonar: the offline load changed"):
                sm.build_data_cache(DESIGN, root / "cache2", str(root))
            self.assertFalse((root / "cache2" / sm.DATA_CACHE_MANIFEST).exists())

    @unittest.skipUnless(importlib.util.find_spec("sklearn") and importlib.util.find_spec("pandas"),
                         "requires the OpenML loader")
    def test_offline_loader_uses_url_path(self):
        import gzip

        with tempfile.TemporaryDirectory(prefix="smeas_openml_") as tmp:
            node = Path(tmp)
            (node / "benchmark.py").write_text(
                "from sklearn.datasets import fetch_openml\n"
                "def _load_frame():\n"
                "    return fetch_openml(data_id=15, data_home='data_cache', as_frame=True, parser='auto')\n"
            )
            cache = node / "data_cache"
            openml = cache / "openml" / "openml.org"
            arff = b"@relation synthetic\n@attribute x numeric\n@attribute y {a,b}\n@data\n0,a\n1,b\n"
            description = {"status": "active", "format": "ARFF", "description": "synthetic regression fixture",
                           "url": "https://openml.org/data/v1/download/52350/example.arff",
                           "md5_checksum": hashlib.md5(arff).hexdigest()}
            features = [{"name": name, "index": str(i), "data_type": dtype, "is_target": target,
                         "is_ignore": "false", "is_row_identifier": "false", "number_of_missing_values": "0"}
                        for i, (name, dtype, target) in enumerate([("x", "numeric", "false"), ("y", "nominal", "true")])]
            metadata = {"data/15.gz": {"data_set_description": description},
                        "data/features/15.gz": {"data_features": {"feature": features}},
                        "data/qualities/15.gz": {"data_qualities": {"quality": [
                            {"name": "NumberOfInstances", "value": "2"}]}}}
            for rel, value in metadata.items():
                p = openml / "api" / "v1" / "json" / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(gzip.compress(json.dumps(value).encode()))
            download = openml / "data" / "v1" / "download"
            download.mkdir(parents=True)
            legacy = download / "52350.gz"
            legacy.write_bytes(gzip.compress(arff))
            before = sm.cache_tree(cache)
            fake_seeds = types.SimpleNamespace(seed_environment=lambda *_: dict(os.environ))
            path = os.pathsep.join((str(Path(sys.executable).parent), os.environ["PATH"]))
            with mock.patch.dict("sys.modules", {"autoresearch.worker.seeds": fake_seeds}), \
                    mock.patch.dict(os.environ, PATH=path):
                with self.assertRaisesRegex(sm.RunStop, "unexpected OpenML download: .*52350/example.arff"):
                    sm._load_openml_cache(node, offline=True)
                self.assertEqual(sm.cache_tree(cache), before)

                actual = download / "52350" / "example.arff.gz"
                actual.parent.mkdir(exist_ok=True)
                legacy.rename(actual)
                before = sm.cache_tree(cache)
                sm._load_openml_cache(node, offline=True)
                self.assertEqual(sm.cache_tree(cache), before)


def _cache_stop_run(job, tmp):
    raise sm.DataCacheStop(f"{job['node']}'s dataset cache changed during the run", "the log tail")


class DataCacheStopExecuteTest(unittest.TestCase):
    """Review M3: the ``data_cache`` STOP through ``execute``, in-process and through the process pool, with the run's
    log tail in failed_runs.jsonl (review M2)."""

    def test_in_process_and_pool(self):
        job = {"node": "openml_sonar", "config": "c0", "condition": "seed", "seed": 999, "edits": []}
        for in_process in (True, False):
            out = Path(tempfile.mkdtemp(prefix="smeas_dcstop_"))
            self.addCleanup(shutil.rmtree, out, True)
            with mock.patch.object(sm, "cotenancy", return_value={"ok": True, "free_for_others": 30}):
                man = sm.execute(out, [job], _cache_stop_run, {}, 1, 100.0, str(out), in_process=in_process)
            self.assertTrue(man["stop"].startswith("data_cache openml_sonar c0 999: "), man["stop"])
            fail = json.loads((out / sm.FAILED_RUNS_FILE).read_text())
            self.assertEqual((fail["log_tail"], fail["condition"]), ("the log tail", "seed"))

    def test_data_cache_refused_with_stub(self):
        tmp = Path(tempfile.mkdtemp(prefix="smeas_stubdc_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        with self.assertRaisesRegex(SystemExit, "not --stub"):
            sm.main(["run", "--stub", "--out", str(tmp / "o"), "--data-cache", str(tmp)])



class NoDeadlineTest(unittest.TestCase):
    """R1-NO-TIMEOUT (1): the measurement has no deadline option; the note carries no deadline field."""

    def test_no_deadline(self):
        self.assertFalse(hasattr(sm, "DEFAULT_DEADLINE"))
        with self.assertRaises(SystemExit):
            sm.main(["run", "--stub", "--out", "/nonexistent/x", "--deadline", "10800"])
        args = argparse.Namespace(code_commit="a" * 40, code_review="r", data_cache_sha256="d" * 64)
        self.assertNotIn("deadline_seconds", sm.expected_note(args, DESIGN, Path(REPO).resolve()))



class ArffByContentTest(unittest.TestCase):
    """local/20261127-05 (compute's STOP): scikit-learn 1.8.0 stores the ARFF as ``data/v1/download/<id>.gz``; the ARFF
    is found by content, exactly one per node, and the pilot's pinned decompressed sha256 still applies."""

    def setUp(self):
        import gzip
        self.gzip = gzip
        self.root = Path(tempfile.mkdtemp(prefix="smeas_arff_"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def write_skl18(self, node: str, arff: bytes) -> Path:
        d = self.root / node / "data_cache" / "openml" / "openml.org"
        (d / "data" / "v1" / "download").mkdir(parents=True)
        (d / "data" / "v1" / "download" / "52350.gz").write_bytes(self.gzip.compress(arff, mtime=1))
        for sub in ("data", "data/features", "data/qualities"):
            (d / "api" / "v1" / "json" / sub).mkdir(parents=True, exist_ok=True)
            (d / "api" / "v1" / "json" / sub / "15.gz").write_bytes(self.gzip.compress(b'{"data_set_description": {}}', mtime=1))
        return self.root / node / "data_cache"

    def test_is_arff(self):
        self.assertTrue(sm.is_arff(b"% a comment\n\n@RELATION breast-w\n@attribute x numeric\n"))
        self.assertTrue(sm.is_arff(b"@relation r"))
        self.assertFalse(sm.is_arff(b'{"data_set_description": {}}'))
        self.assertFalse(sm.is_arff(b"% only comments\n"))
        self.assertFalse(sm.is_arff(b""))

    def test_id_gz_layout_counts_as_the_one_arff(self):
        cache = self.write_skl18("openml_sonar", b"% c\n@relation sonar\n@data\n1\n")
        files = sm.cache_tree(cache)
        self.assertEqual([k for k, v in files.items() if v["arff"]], ["openml/openml.org/data/v1/download/52350.gz"])
        sm.check_pilot("openml_sonar", files)                                  # no pilot pin for sonar: only the count
        _write_cache_manifest(self.root, ["openml_sonar"])
        sm.read_data_cache(self.root, ["openml_sonar"])

    def test_pilot_pin_applies_to_the_id_gz_file(self):
        data = b"@relation breast-w\n@data\n"
        files = sm.cache_tree(self.write_skl18("openml_breast_w", data))
        with self.assertRaisesRegex(sm.RunStop, "differs from the E1 pilot"):
            sm.check_pilot("openml_breast_w", files)
        with mock.patch.dict(sm.PILOT_ARFF_SHA256, {"openml_breast_w": hashlib.sha256(data).hexdigest()}):
            sm.check_pilot("openml_breast_w", files)

    def test_no_arff_or_two_arffs_refused(self):
        files = sm.cache_tree(self.write_skl18("openml_climate", b'{"not": "arff"}'))
        with self.assertRaisesRegex(sm.RunStop, "0 ARFF files"):
            sm.check_pilot("openml_climate", files)
        cache = self.write_skl18("openml_wdbc", b"@relation wdbc")
        (cache / "openml" / "openml.org" / "data" / "v1" / "download" / "99.gz").write_bytes(
            self.gzip.compress(b"@relation other", mtime=1))
        with self.assertRaisesRegex(sm.RunStop, "2 ARFF files"):
            sm.check_pilot("openml_wdbc", sm.cache_tree(cache))


if __name__ == "__main__":
    unittest.main()
