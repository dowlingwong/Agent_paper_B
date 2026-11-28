"""D.3 G1 -> G6 -> G7 integration on the seven synthetic cases (task compute/20261127-23).

The campaigns are synthetic (scripted proposals, synthetic worker/audit metrics), but every
record passes through the production G1 chunk, the production G1 summary, the production G6
audit and the production G7 table builder.  No fixture summary and no hand-supplied audit is
used for the seven case checks; the full 882-row table repeats the seven production cases
across the declared design only to satisfy G7's coverage check.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace

import pytest

from r1.c3 import d3_analysis as D3
from r1.c3 import d3_outcome_table as table
from r1.c3.d3 import assemble, audit
from r1.c3.d3.campaign_chunk import ChunkSpec, run_chunk
from r1.c3.d3.replicate_campaign import ReplicateUnit
from r1.c3.d3.snapshots import ParityBudget, config_sha256, sha256_json, wrap
from r1.c3.d3.summary import SUMMARY_SCHEMA
from r1.c3.d3_replicate import EgateEngine, Fixr3Engine
from r1.tests.test_d3_g1_snapshots import (
    HARNESS,
    ConfigMetricWorker,
    ToggleBackend,
    VerifyOnce,
    _node_copy,
    load_registered_node,
)
from autoresearch.control_plane.controller import ControlDecision

NODE = "digits_mlp"
SEED = 6201
INSTANCE = f"{NODE}__s{SEED}"
SOURCE = {"sha256": "0" * 64}
MANIFEST = {
    "campaign_model": "synthetic GPU",
    "proposer_model": "scripted",
    "campaign_model_source_sha256": sha256_json(SOURCE),
}
OBSERVED = {
    "model": "synthetic GPU",
    "proposer_model": "scripted",
    "memory_check": "pass",
    "lease": True,
}
PREDECLARATION = "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md"


class ScriptedManager(ToggleBackend):
    deterministic = False


class SyntheticWorker(ConfigMetricWorker):
    def __init__(self, root, *, final_keep):
        super().__init__(root)
        self.final_keep = final_keep
        self.configs = {}

    def run_trial(self, proposal, node_spec, budget_index):
        result = super().run_trial(proposal, node_spec, budget_index)
        self.configs[budget_index] = {"train.py": (self.node_root / "train.py").read_text()}
        value = 0.50 + 0.01 * self.runs
        if self.runs == 20 and not self.final_keep:
            value = 0.40
        return replace(result, parsed_metrics={"val_score": value})


class SyntheticDecision(VerifyOnce):
    def __init__(self, *, early):
        super().__init__(at=99)
        self.early = early

    def decide(self, view, mask):
        if self.early and view.epoch == "E1" and 7 <= view.budget_index < 80:
            assert mask.get("skip")
            return ControlDecision("skip", {}, self.version, view.input_hash())
        return super().decide(view, mask)


def _spec(arm):
    return ChunkSpec("a", arm, NODE, 0, (SEED,), 20, 80, "direct", "synthetic", SOURCE)


def fake_audit(node, files, seeds):
    text = files["train.py"]
    if text.startswith("X = "):
        level = 0.1 * (1 + int(text.split("=")[1]))
    else:
        match = re.search(r"^LEARNING_RATE_INIT\s*=\s*([0-9.e+-]+)", text, re.MULTILINE)
        level = 50 * float(match[1])
    return [audit.Run(seed, 0.05 + level + 1e-5 * seed,
                      hashlib.sha256(f"{node}:{seed}:{text}".encode()).hexdigest())
            for seed in seeds]


def _audit_case(cdir, out):
    result = audit.audit_campaign(cdir, out, sigma_node=1.0, runner=fake_audit, cache=audit.Cache())
    rows = audit.g7_rows(result)
    cid = D3.campaign_id("D.3a", json.loads((cdir / "summary.json").read_text())["arm"],
                         NODE, SEED, 0)
    return result, table._audits_by_campaign(rows).get(cid, {"keep": []})


def harness_case(root, *, early=False, final_keep=True, expect=None, stop=False):
    node = _node_copy(root)
    worker = SyntheticWorker(node, final_keep=final_keep)
    ended_on = "stop" if stop else ("llm_call_cap" if early else "worker_runs")

    def factory(spec, seed, cdir, recorder):
        return wrap({
            "node_spec": load_registered_node(NODE, repo_root=HARNESS),
            "campaign_id": recorder.instance_id,
            "budget": 80,
            "manager_mode": "baseline_manager",
            "memory_mode": "append_only_summary",
            "records_path": cdir / "fixture-records.jsonl",
            "worker": worker,
            "proposal_backend": ScriptedManager(),
            "controller": SyntheticDecision(early=early),
            "compute_budget": ParityBudget(max_worker_runs=20, max_llm_calls=80, recorder=recorder),
            "verify_runs": 2,
            "verify_split_policy": "vary",
        }, recorder), ended_on

    chunk = root / "chunk"
    run_chunk(_spec("A0"), chunk, factory, manifest=MANIFEST, observed=OBSERVED)
    cdir = chunk / "campaigns" / INSTANCE
    summary = json.loads((cdir / "summary.json").read_text())
    assert summary["schema"] == SUMMARY_SCHEMA and summary["stage"] == "D.3a"
    assert set(summary) == table.SUMMARY_KEYS
    assert len(list((cdir / "keeps").glob("keep-*.json"))) == summary["keeps"]
    if expect is not None:
        assert (summary["worker_runs"], summary["last_keep_run"], summary["keeps"]) == expect
    _, audits = _audit_case(cdir, root / "g6")
    row = None if stop else table.build_row("D.3a", summary, audits)
    return summary, audits, row, chunk, root / "g6"


def replicate_case(root, arm, *, final_keep=True, expect=None):
    def validate(proposal):
        files = {"train.py": f"X = {proposal}\n"}
        return files, config_sha256(files)

    def run_trial(proposal, files, seed, j, budget_index):
        x = int(files["train.py"].split("=")[1])
        if (arm == "FIXR3" and budget_index == 2) or (arm == "EGATE" and 2 <= budget_index <= 7):
            return False, None, 0.01
        if not final_keep and x == (6 if arm == "FIXR3" else 7):
            x = -2
        return True, 0.20 + 0.08 * (x + 1) + 0.0002 * j, 0.01

    def factory(spec, seed, cdir, recorder):
        engine = Fixr3Engine(seed) if arm == "FIXR3" else EgateEngine(seed)
        return ReplicateUnit(engine, lambda step, _inc, _calls: step, validate, run_trial,
                             {"train.py": "X = -1\n"})

    chunk = root / "chunk"
    run_chunk(_spec(arm), chunk, replicate_factory=factory, manifest=MANIFEST, observed=OBSERVED)
    cdir = chunk / "campaigns" / INSTANCE
    summary = json.loads((cdir / "summary.json").read_text())
    assert summary["schema"] == SUMMARY_SCHEMA and summary["stage"] == "D.3a"
    if expect is not None:
        assert (summary["worker_runs"], summary["last_keep_run"], summary["keeps"]) == expect
    _, audits = _audit_case(cdir, root / "g6")
    row = table.build_row("D.3a", summary, audits)
    return summary, audits, row, chunk, root / "g6"


def _clone(summary, audits, *, arm, node, seed, repetition=0):
    s = dict(summary)
    s.update({"stage": "D.3a", "arm": arm, "node": node, "instance_seed": seed,
              "repetition": repetition,
              "start_config_hash": hashlib.sha256(f"start:{node}".encode()).hexdigest()})
    cid = D3.campaign_id("D.3a", arm, node, seed, repetition)
    a = []
    for row in audits["keep"]:
        a.append({**row, "campaign_id": cid})
    for point in ("final", "5", "10", "15", "20"):
        if point in audits:
            a.append({**audits[point], "campaign_id": cid})
    return s, a


def test_seven_production_cases_pass_g7():
    import tempfile
    from pathlib import Path

    root = Path(tempfile.mkdtemp(prefix="d3-integration-"))
    cases = [
        harness_case(root / "hk", early=False, final_keep=True, expect=(20, 20, 20)),
        harness_case(root / "hd", early=False, final_keep=False, expect=(20, 19, 19)),
        harness_case(root / "he", early=True, final_keep=True, expect=(7, 7, 7)),
        replicate_case(root / "fk", "FIXR3", final_keep=True, expect=(20, 20, 6)),
        replicate_case(root / "fd", "FIXR3", final_keep=False, expect=(20, 17, 5)),
        replicate_case(root / "ek", "EGATE", final_keep=True, expect=(20, 20, 2)),
        replicate_case(root / "ed", "EGATE", final_keep=False, expect=(20, 1, 1)),
    ]
    assert len(cases) == 7
    for summary, audits, row, chunk, audit_dir in cases:
        assert row["campaign_id"] == D3.campaign_id(
            "D.3a", summary["arm"], summary["node"], summary["instance_seed"], summary["repetition"])
        assert row["status"] == "complete"
        assert row["y_raw"] == audits["final"]["y_raw"]
        assert row["final_config_hash"] == audits["final"]["config_sha256"]
        if audits["keep"]:
            assert row["last_keep_run"] == audits["keep"][-1]["keep_run"]
            assert row["y_raw"] == audits["keep"][-1]["y_raw"]
        # The production disk boundary: the G1 summary and the G6 g7 rows load from disk.
        assert assemble.load_summaries([chunk]) == [summary]
        assert len(assemble.load_audits([audit_dir])) == len(
            [1] + [1 for point in ("5", "10", "15", "20") if point in audits]
            + [1 for _ in audits["keep"]])

    # A zero-run campaign: G7 forbids any audit row, and the descriptive Y_final row remains.
    row = _zero_run_case(root / "z")
    assert row["worker_runs"] == 0 and row["y_raw"] == 0.0

    # A stopped campaign is written as "stopped" and G7 refuses it (no table row).
    summary, audits, _, _, _ = harness_case(root / "st", early=False, final_keep=True, stop=True)
    assert summary["status"] == "stopped"
    with pytest.raises(table.OutcomeTableError):
        table.build_row("D.3a", summary, audits)


class _NoRunEngine:
    arm = "EGATE"
    version = "no-run/v1"
    instance_seed = SEED
    steps = 0
    incumbent = None
    seeds = ()
    zero_variance_cases = 0

    def step(self, candidate_sha, run_one, counter):
        from types import SimpleNamespace
        return SimpleNamespace(runs_charged=0, decision="discarded", replicates=[],
                               display_metric=None, detail={})


def _zero_run_case(root):
    from r1.c3.d3.replicate_campaign import ReplicateUnit

    def validate(proposal):
        files = {"train.py": f"X = {proposal}\n"}
        return files, config_sha256(files)

    def factory(spec, seed, cdir, recorder):
        return ReplicateUnit(_NoRunEngine(), lambda step, _inc, _calls: step, validate,
                             lambda *a, **k: (_ for _ in ()).throw(AssertionError("no run expected")),
                             {"train.py": "X = -1\n"})

    chunk = root / "chunk"
    run_chunk(_spec("EGATE"), chunk, replicate_factory=factory, manifest=MANIFEST, observed=OBSERVED)
    cdir = chunk / "campaigns" / INSTANCE
    summary = json.loads((cdir / "summary.json").read_text())
    assert summary["worker_runs"] == 0 and summary["last_keep_run"] is None and summary["keeps"] == 0
    result, audits = _audit_case(cdir, root / "g6")
    rows = audit.g7_rows(result)
    assert not [r for r in rows if r["point"] == "final"]
    return table.build_row("D.3a", summary, None)


def test_full_design_assembly_accepts_g7_and_analysis():
    import tempfile
    from pathlib import Path

    root = Path(tempfile.mkdtemp(prefix="d3-assemble-"))
    # One production template per arm family.  The full design repeats them only to satisfy
    # G7's coverage check; the seven case checks above use the production records directly.
    harness = harness_case(root / "h", early=False, final_keep=False)
    fixr3 = replicate_case(root / "f", "FIXR3", final_keep=False)
    egate = replicate_case(root / "e", "EGATE", final_keep=False)
    templates = {"A0": harness, "A0R": harness, "A1": harness, "A2": harness,
                 "LADDER": harness, "FIXR3": fixr3, "EGATE": egate}
    chunk_dirs, audits = [], []
    for arm in D3.ARMS_D3A:
        chunk = root / "chunks" / f"arm-{arm}"
        chunk_dirs.append(chunk)
        for node in D3.NODES:
            for seed in D3.INSTANCE_SEEDS:
                s, a = _clone(templates[arm][0], templates[arm][1], arm=arm, node=node, seed=seed)
                inst = D3.instance_id(node, seed)
                cdir = chunk / "campaigns" / inst
                cdir.mkdir(parents=True, exist_ok=True)
                (cdir / "summary.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n",
                                                   encoding="utf-8")
                audits.extend(a)
    audit_root = root / "audit"
    audit_root.mkdir()
    (audit_root / "g7_rows.jsonl").write_text(
        "".join(json.dumps(a, sort_keys=True) + "\n" for a in audits), encoding="utf-8")
    result = assemble.build("D.3a", chunk_dirs, [audit_root], predeclaration_path=PREDECLARATION)
    assert len(result["rows"]) == len(D3.ARMS_D3A) * len(D3.NODES) * len(D3.INSTANCE_SEEDS)
    out = table.write_table(result, root / "table.json")
    loaded = D3.load_table(out, "D.3a")
    report = D3.analyse(loaded, d3b_not_run="not_started")
    assert report["schema"] == D3.REPORT_SCHEMA
    assert report["families"]["D.3a"]["family"] == "D.3a"


def test_rule_arm_without_e1_events_is_a_stop():
    from r1.c3.d3 import summary as S

    records = [{"budget_index": 1, "worker_mode": "ran", "decision": "keep",
                "trial_id": "t1", "extra": {}}]
    with pytest.raises(S.SummaryStop):
        S.mechanism_counts(records, [], config_by_trial={1: {"config_sha256": "a" * 64}},
                           arm="A2")
    # A0 / FIXR3 / EGATE have no rule layer; the same record is accepted.
    S.mechanism_counts(records, [], config_by_trial={1: {"config_sha256": "a" * 64}}, arm="A0")
