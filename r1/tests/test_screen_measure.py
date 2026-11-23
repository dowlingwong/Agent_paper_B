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


def _fake_smoke_run(job: dict, _tmp: str, runtime_expected=None) -> dict:
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


class NoteAndHostTest(unittest.TestCase):
    NOTE = "# t\n\nprose: not a field\n\n## Key block\n\n```\napproved: false\nlabel: EVIDENCE\n```\n"

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


if __name__ == "__main__":
    unittest.main()
