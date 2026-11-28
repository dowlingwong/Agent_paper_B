# AI-assisted (Claude, local worker, 27 Nov 2026). Synthetic tests only: no harness run, no SMAC3 run.
"""Tests of the D.3 HPO-REF unit (r1/c3/d3_hpo_ref.py; R1-D3-HPO-REF, pre-declaration revision 4 §5.8, §8)."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from unittest import mock

import numpy as np

from r1.c3 import d3_analysis as D3
from r1.c3 import d3_hpo_ref as H

START = {
    "mlp": {"HIDDEN_UNITS": 64, "ALPHA": 1e-4, "LEARNING_RATE_INIT": 1e-3, "BATCH_SIZE": 32, "MAX_ITER": 100},
    "openml": {"model_type": "logistic_regression", "C": 1.0, "class_weight": None, "imputer": "most_frequent",
               "learning_rate": 0.1, "max_depth": 5, "max_iter": 1000, "n_estimators": 100, "scaler": "standard"},
}


def start_of(node):
    return dict(START["mlp" if node.endswith("_mlp") else "openml"])


def metric_of(node, cfg):
    h = hashlib.sha256((node + H.default_config_sha256(cfg)).encode()).digest()
    return 0.5 + 0.5 * int.from_bytes(h[:4], "big") / 2 ** 32


class Evaluator:
    def __init__(self, fail=lambda cfg: False, infra_at=None):
        self.calls, self.fail, self.infra_at = [], fail, infra_at

    def __call__(self, node, cfg, seed):
        self.calls.append((node, H.default_config_sha256(cfg), seed))
        if self.infra_at is not None and len(self.calls) == self.infra_at:
            raise H.InfrastructureFailure("card lost")
        if self.fail(cfg):
            return H.EvalResult(success=False, seconds=0.5)
        return H.EvalResult(success=True, metric=metric_of(node, cfg), seconds=1.0)


class FakeSmac:
    """Stand-in of the SMAC3 backend's three methods: the default first, then seeded random draws; the incumbent is
    the lowest cost among successful trials (first wins ties), as SMAC3's deterministic best-so-far."""

    instances = []

    def __init__(self, space, start, seed):
        self.space, self.rng, self.first = space, np.random.default_rng(seed), True
        self.start, self.told, self.asked = start, [], []
        FakeSmac.instances.append(self)

    def ask(self):
        if self.first:
            self.first = False
            v = {k: self.start[k] for k in self.space.active_keys(self.start)}
        else:
            v = H.draw_configuration(self.space, self.rng)
        self.asked.append(v)
        return dict(v)

    def tell(self, cost, crashed):
        self.told.append((self.asked[len(self.told)], cost, crashed))

    def incumbent(self):
        ok = [(c, i) for i, (v, c, crashed) in enumerate(self.told) if not crashed]
        if not ok:
            return None
        return dict(self.told[min(ok)[1]][0])


def harness_space(node):
    try:
        return H.load_node_space(node)
    except H.HpoRefError as exc:
        raise unittest.SkipTest(f"harness pin not readable here: {exc}")


def synthetic_space(node):
    """The declared space without the harness (the loader's checks are tested on the pinned files below)."""
    params, active, excluded = H.DECLARED_SPACES[node]
    editable = tuple(p.name for p in params) + tuple(excluded)
    return H.NodeSpace(node=node, config_sha256=H.NODE_CONFIG_SHA256[node], metric_direction="maximize",
                       params=params, active_by_model_type=active, dataset_excluded=excluded,
                       editable_symbols=editable)


class SpaceTest(unittest.TestCase):
    def test_table_prefixes_match_full_digests(self):
        for n in D3.NODES:
            self.assertTrue(H.NODE_CONFIG_SHA256[n].startswith(H.TABLE_SHA256_PREFIX[n]), n)
        self.assertEqual(set(H.NODE_CONFIG_SHA256), set(D3.NODES))

    def test_pinned_configs_load_and_match_the_table(self):
        for n in D3.NODES:
            s = harness_space(n)
            self.assertEqual(s.config_sha256, H.NODE_CONFIG_SHA256[n])
            if n.endswith("_mlp"):
                self.assertIsNone(s.active_by_model_type)
                self.assertEqual(len(s.params), 5)
            else:
                self.assertEqual(s.dataset_excluded, () if n == "openml_credit_approval" else ("imputer",))
                self.assertEqual("imputer" in s.keys, n == "openml_credit_approval")
                self.assertEqual(s.active_keys({"model_type": "gradient_boosting"})[:4],
                                 ("model_type", "n_estimators", "max_depth", "learning_rate"))
        self.assertTrue(harness_space("openml_sonar").param("C").log)
        self.assertFalse(harness_space("digits_mlp").param("BATCH_SIZE").log)

    def _raw(self, node):
        try:
            return json.loads(H.read_pinned_node_config(node))
        except H.HpoRefError as exc:
            raise unittest.SkipTest(str(exc))

    def _refuses(self, node, cfg, pattern):
        raw = json.dumps(cfg).encode()
        with mock.patch.dict(H.NODE_CONFIG_SHA256, {node: hashlib.sha256(raw).hexdigest()}):
            with self.assertRaisesRegex(H.HpoRefError, pattern):
                H.load_node_space(node, raw)

    def test_tampered_bytes_refused_by_sha256(self):
        self._raw("digits_mlp")
        raw = H.read_pinned_node_config("digits_mlp")
        with self.assertRaisesRegex(H.HpoRefError, "sha256"):
            H.load_node_space("digits_mlp", raw + b" ")

    def test_space_differences_refused(self):
        base = self._raw("openml_climate")
        cases = []
        c = copy.deepcopy(base); c["allowed_ranges"]["C"] = [0.001, 10.0]; cases.append((c, "allowed_ranges of C"))
        c = copy.deepcopy(base); c["allowed_ranges"]["max_depth"] = [2.0, 30.0]; cases.append((c, "integer type"))
        c = copy.deepcopy(base); c["allowed_values"]["scaler"] = ["none", "standard"]; cases.append((c, "scaler"))
        c = copy.deepcopy(base); c["active_keys"]["dataset_excluded"] = []; cases.append((c, "editable_symbols|"
                                                                                          "dataset_excluded"))
        c = copy.deepcopy(base); c["active_keys"]["by_model_type"]["random_forest"].remove("max_depth")
        cases.append((c, "random_forest"))
        c = copy.deepcopy(base); c["editable_symbols"].append("tol"); cases.append((c, "editable_symbols"))
        c = copy.deepcopy(base); c["metric_direction"] = "minimize"; cases.append((c, "metric_direction"))
        for cfg, pattern in cases:
            self._refuses("openml_climate", cfg, pattern)
        m = self._raw("tabular_mlp")
        m["allowed_ranges"]["ALPHA"] = [1e-5, 1.0]
        self._refuses("tabular_mlp", m, "ALPHA")

    def test_start_config_checked(self):
        s = synthetic_space("openml_sonar")
        H.check_start_config(s, start_of("openml_sonar"))
        bad = start_of("openml_sonar"); bad["C"] = 1000.0
        with self.assertRaisesRegex(H.HpoRefError, "start value of C"):
            H.check_start_config(s, bad)
        bad = start_of("openml_sonar"); del bad["imputer"]
        with self.assertRaisesRegex(H.HpoRefError, "editable symbols"):
            H.check_start_config(s, bad)


class RsTest(unittest.TestCase):
    def test_draws_stay_in_space_and_on_active_keys(self):
        for n in D3.NODES:
            s = synthetic_space(n)
            rng = H.rs_generator(6201, 0)
            for _ in range(200):
                v = H.draw_configuration(s, rng)
                self.assertEqual(set(v), set(s.active_keys(v)))
                for k, x in v.items():
                    self.assertTrue(H._in_param(s.param(k), x), (n, k, x))
                    if s.param(k).kind == "int":
                        self.assertIsInstance(x, int)

    def test_seeded_and_reproducible(self):
        s = synthetic_space("openml_ionosphere")
        a = H.run_rs(s, start_of(s.node), 6205, 0, Evaluator())
        b = H.run_rs(s, start_of(s.node), 6205, 0, Evaluator())
        c = H.run_rs(s, start_of(s.node), 6205, 1, Evaluator())
        self.assertEqual(a.executed, b.executed)
        self.assertNotEqual(a.executed, c.executed)
        self.assertEqual(a.worker_runs, H.W)
        self.assertEqual(a.ended_on, "worker_runs")
        self.assertEqual(a.executed[0], start_of(s.node))          # charged run 1: the start configuration
        # the PCG64 seed of §4.1
        g = np.random.Generator(np.random.PCG64(6205 + 1_000_000))
        self.assertEqual(H.rs_generator(6205, 1).random(), g.random())

    def test_duplicates_skipped_uncharged_and_proposal_cap(self):
        # A tiny categorical space on an OpenML node: duplicates are frequent and the 80-draw cap binds.
        params = (H.Param("model_type", "cat", choices=("logistic_regression", "random_forest")),
                  H.Param("scaler", "cat", choices=("none", "standard", "minmax")))
        active = {"logistic_regression": ("model_type", "scaler"), "random_forest": ("model_type", "scaler")}
        s = H.NodeSpace("openml_sonar", "x", "maximize", params, active, (),
                        tuple(start_of("openml_sonar")))
        ev = Evaluator()
        c = H.run_rs(s, start_of(s.node), 6201, 0, ev)
        self.assertEqual(c.ended_on, "proposal_cap")
        self.assertEqual(c.proposals, H.HPO_PROPOSAL_CAP)
        self.assertEqual(c.worker_runs, 6)                         # the 6 distinct configurations, each once
        self.assertEqual(len(ev.calls), len({x[1] for x in ev.calls}))
        self.assertEqual(c.rule_skips, H.HPO_PROPOSAL_CAP - (c.worker_runs - 1))
        self.assertLessEqual(c.duplicates_proposed, c.rule_skips)
        self.assertEqual(c.duplicates_executed, 0)
        row = H.build_row(c, lambda cfg: 0.1)
        self.assertEqual(row["ended_on"], "proposal_cap")
        self.assertEqual(row["y_raw_w"], {"5": row["y_raw_w"]["5"], "10": None, "15": None, "20": None})
        self.assertIsNotNone(row["y_raw_w"]["5"])

    def test_keep_rule_strict_improvement(self):
        s = synthetic_space("digits_mlp")
        c = H.run_rs(s, start_of(s.node), 6210, 0, Evaluator())
        best = None
        kept = [w for w, _ in c.keeps]
        for run in c.counter.runs:
            if run.success and (best is None or run.metric > best):
                best = run.metric
                self.assertIn(run.w, kept)
            else:
                self.assertNotIn(run.w, kept)
        self.assertEqual(c.keeps[0][0], 1)                         # the start run is the first keep
        self.assertEqual(c.final_config, c.keeps[-1][1])

    def test_failed_runs_charged_not_kept_start_failure(self):
        s = synthetic_space("openml_credit_approval")
        st = start_of(s.node)
        fail = lambda cfg: cfg == st or cfg.get("model_type") == "random_forest"
        c = H.run_rs(s, st, 6211, 0, Evaluator(fail=fail))
        self.assertEqual(c.worker_runs, H.W)
        self.assertFalse(c.counter.runs[0].success)
        self.assertTrue(all(cfg.get("model_type") != "random_forest" for _, cfg in c.keeps))
        first_ok = next(r.w for r in c.counter.runs if r.success)
        self.assertEqual(c.keeps[0][0], first_ok)

    def test_infrastructure_failure_reruns_whole_attempt(self):
        s = synthetic_space("openml_breast_w")
        clean = H.run_rs(s, start_of(s.node), 6212, 0, Evaluator())
        ev = Evaluator(infra_at=7)
        c = H.run_rs(s, start_of(s.node), 6212, 0, ev)
        self.assertEqual(c.infra_attempts, 2)
        self.assertEqual(c.executed, clean.executed)
        self.assertEqual(c.worker_runs, H.W)
        self.assertEqual(clean.infra_attempts, 1)

    def test_counter_refuses_beyond_w(self):
        k = H.HpoRunCounter(2)
        for _ in range(2):
            k.charge(kind="trial", role="candidate", seed=1, config_sha256="a", success=False)
        with self.assertRaises(H.OverBudget):
            k.charge(kind="trial", role="candidate", seed=1, config_sha256="a", success=False)
        with self.assertRaises(ValueError):
            H.HpoRunCounter(2).charge(kind="trial", role="candidate", seed=1, config_sha256="a", success=True)

    def test_ended_on_rule(self):
        self.assertEqual(H.hpo_ended_on(arm="RS", worker_runs=20, proposals=80), "worker_runs")
        self.assertEqual(H.hpo_ended_on(arm="RS", worker_runs=19, proposals=80), "proposal_cap")
        with self.assertRaises(H.HpoRefError):
            H.hpo_ended_on(arm="SMAC3", worker_runs=19, proposals=80)
        with self.assertRaises(H.HpoRefError):
            H.hpo_ended_on(arm="RS", worker_runs=19, proposals=79)
        with self.assertRaises(H.OverBudget):
            H.hpo_ended_on(arm="RS", worker_runs=21, proposals=21)


class SmacTest(unittest.TestCase):
    def test_refuses_without_smac(self):
        with mock.patch.dict(sys.modules, {"smac": None}), mock.patch.object(H, "version", H.SMAC_PINS.__getitem__):
            with self.assertRaisesRegex(H.SmacUnavailable, "cannot import from its pinned"):
                H.require_smac()
            with self.assertRaisesRegex(H.SmacUnavailable, "cannot import from its pinned"):
                H.run_smac3(synthetic_space("openml_sonar"), start_of("openml_sonar"), 6201, 0, Evaluator())

    def test_refuses_other_installed_smac_version(self):
        wrong = H.SMAC_PINS | {"smac": "2.4.1"}
        with mock.patch.object(H, "version", wrong.__getitem__):
            with self.assertRaisesRegex(H.SmacUnavailable, "distribution versions differ.*2.4.1"):
                H.require_smac()

    def test_every_ask_evaluated_and_charged_until_w(self):
        s = synthetic_space("openml_climate")
        st = start_of(s.node)
        FakeSmac.instances.clear()
        ev = Evaluator(fail=lambda cfg: cfg.get("model_type") == "gradient_boosting")
        c = H.run_smac3(s, st, 6203, 1, ev, backend_factory=FakeSmac)
        fake = FakeSmac.instances[-1]
        self.assertEqual(len(fake.asked), H.W)
        self.assertEqual(len(ev.calls), H.W)
        self.assertEqual((c.worker_runs, c.proposals, c.ended_on), (H.W, H.W, "worker_runs"))
        for (v, cost, crashed), run in zip(fake.told, c.counter.runs):
            self.assertEqual(crashed, not run.success)
            self.assertEqual(cost, H.WORST_COST if crashed else -run.metric)
        self.assertEqual(c.final_config, H.full_config(s, st, fake.incumbent()))
        self.assertEqual(c.rule_skips, 0)

    def test_smac_seed(self):
        self.assertEqual(H.smac_seed(6201, 0), 6201)
        self.assertEqual(H.smac_seed(6201, 1), 6202)

    def test_configspace_builder(self):
        try:
            import ConfigSpace  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("ConfigSpace not installed")
        s = synthetic_space("openml_climate")
        cs = H.build_configspace(s, start_of(s.node), 1)
        self.assertEqual(set(cs.keys()), set(s.keys))


def synthetic_table_from_runs():
    rows = []
    for arm in H.ARMS:
        for node in D3.NODES:
            s = synthetic_space(node)
            st = start_of(node)
            for seed in D3.INSTANCE_SEEDS:
                ev = Evaluator(fail=lambda cfg: cfg.get("MAX_ITER") == 5)
                c = (H.run_rs(s, st, seed, 0, ev) if arm == "RS"
                     else H.run_smac3(s, st, seed, 0, ev, backend_factory=FakeSmac))
                rows.append(H.build_row(c, lambda cfg, n=node, st=st: metric_of(n, cfg) - metric_of(n, st)))
    return H.build_table(rows, predeclaration_sha256=H.PREDECLARATION_SHA256, sigma_node={n: 0.01 for n in D3.NODES})


class EndToEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = synthetic_table_from_runs()

    def test_full_design_validates(self):
        t = self.table
        self.assertEqual(len(t["rows"]), 2 * 7 * 18)
        D3.validate_table(copy.deepcopy(t), "HPO-REF")
        for r in t["rows"]:
            self.assertEqual((r["llm_calls"], r["proposer_gpu_seconds"], r["gpu_model"]), (0, 0, None))
            if r["arm"] == "SMAC3":
                self.assertEqual((r["worker_runs"], r["proposals"], r["ended_on"]), (20, 20, "worker_runs"))
            self.assertEqual(r["y_raw_w"]["20"], r["y_raw"])
            if r["keeps"]:
                self.assertIsNotNone(r["last_keep_run"])

    def test_proposal_cap_row_validates_in_the_table(self):
        params = (H.Param("model_type", "cat", choices=("logistic_regression", "random_forest")),
                  H.Param("scaler", "cat", choices=("none", "standard", "minmax")))
        active = {"logistic_regression": ("model_type", "scaler"), "random_forest": ("model_type", "scaler")}
        s = H.NodeSpace("openml_sonar", "x", "maximize", params, active, (), tuple(start_of("openml_sonar")))
        c = H.run_rs(s, start_of(s.node), 6201, 0, Evaluator())
        row = H.build_row(c, lambda cfg: 0.1)
        t = copy.deepcopy(self.table)
        i = next(i for i, r in enumerate(t["rows"]) if r["campaign_id"] == row["campaign_id"])
        t["rows"][i] = row
        D3.validate_table(t, "HPO-REF")
        self.assertEqual(row["ended_on"], "proposal_cap")

    def test_tampered_rows_refused_by_the_analysis(self):
        t = copy.deepcopy(self.table)
        smac = next(r for r in t["rows"] if r["arm"] == "SMAC3")
        smac["ended_on"] = "proposal_cap"
        with self.assertRaises(D3.D3InputError):
            D3.validate_table(t, "HPO-REF")
        t = copy.deepcopy(self.table)
        t["rows"][0]["llm_calls"] = 1
        with self.assertRaises(D3.D3InputError):
            D3.validate_table(t, "HPO-REF")

    def test_summary_is_the_g7_contract_shape(self):
        s = synthetic_space("openml_sonar")
        c = H.run_rs(s, start_of(s.node), 6201, 0, Evaluator())
        summ = H.campaign_summary(c)
        expected = {"schema", "stage", "arm", "node", "instance_seed", "repetition", "status", "gpu_model",
                    "infra_attempts", "worker_runs", "llm_calls", "unfundable", "start_config_hash",
                    "final_config_hash", "last_keep_run", *D3.COMPUTE_INT_KEYS, *D3.COMPUTE_SECONDS_KEYS,
                    *D3.MECHANISM_KEYS}
        self.assertEqual(set(summ), expected)
        req = H.audit_requests(c)
        self.assertEqual(req[0]["point"], "final")
        self.assertEqual(sum(1 for r in req if r["point"] == "keep"), len(c.keeps))
        self.assertEqual({r["point"] for r in req if r["point"] not in ("final", "keep")}, {"5", "10", "15", "20"})

    def test_audit_not_called_for_the_start(self):
        s = synthetic_space("digits_mlp")
        st = start_of(s.node)
        c = H.run_rs(s, st, 6201, 0, Evaluator(fail=lambda cfg: cfg != st))   # only the start succeeds
        called = []
        row = H.build_row(c, lambda cfg: called.append(cfg) or 1.0)
        self.assertEqual(called, [])
        self.assertEqual((row["y_raw"], row["keeps"], row["last_keep_run"]), (0.0, 1, 1))
        self.assertEqual(row["final_config_hash"], row["start_config_hash"])


if __name__ == "__main__":
    unittest.main()
