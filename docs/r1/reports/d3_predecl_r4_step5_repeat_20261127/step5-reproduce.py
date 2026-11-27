"""Repeat D.3 step (5) on the pinned source using synthetic campaigns only."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import tempfile

from r1.c3 import d3_analysis as analysis
from r1.c3 import d3_outcome_table as table
from r1.c3.d3 import audit
from r1.c3.d3.campaign_chunk import ChunkSpec, run_chunk
from r1.c3.d3.replicate_campaign import ReplicateUnit
from r1.c3.d3.snapshots import ParityBudget, config_sha256, sha256_json, wrap
from r1.c3.d3_replicate import EgateEngine, Fixr3Engine
from r1.tests.test_d3_g1_snapshots import (
    HARNESS,
    ConfigMetricWorker,
    ToggleBackend,
    VerifyOnce,
    _node_copy,
    load_registered_node,
)
from r1.tests.test_d3_outcome_table import _design, _summary
from autoresearch.control_plane.controller import ControlDecision

NODE = "digits_mlp"
SEED = 6201
INSTANCE = f"{NODE}__s{SEED}"
STAGE = "D.3a"
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
DECLARATION = Path("docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md")


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
        # Spend 80 LLM calls and exactly seven worker runs in the early case.
        # The 80th proposal is the seventh worked proposal and produces a keep.
        if self.early and view.epoch == "E1" and 7 <= view.budget_index < 80:
            assert mask.get("skip")
            return ControlDecision("skip", {}, self.version, view.input_hash())
        return super().decide(view, mask)


def load(path):
    return json.loads(path.read_text())


def ledger(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def chunk_spec(arm):
    # One declared-seed synthetic instance. Never build a full launch spec.
    return ChunkSpec("a", arm, NODE, 0, (SEED,), 20, 80, "direct", "synthetic", SOURCE)


def harness_case(root, *, early=False, final_keep=True):
    node = _node_copy(root)
    worker = SyntheticWorker(node, final_keep=final_keep)
    ended_on = "llm_call_cap" if early else "worker_runs"

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
    run_chunk(chunk_spec("A0"), chunk, factory, manifest=MANIFEST, observed=OBSERVED)
    cdir = chunk / "campaigns" / INSTANCE
    rows = ledger(cdir / "ledger.jsonl")
    kept = [
        (charged, worker.configs[row["budget_index"]])
        for charged, row in enumerate(
            (row for row in rows if row["budget_index"] in worker.configs), start=1
        )
        if row["decision"] in {"keep", "kept"}
    ]
    expected = 7 if early else 20 if final_keep else 19
    assert kept[-1][0] == expected
    final = load(cdir / "snapshots" / "final.json")
    last_trial = next(row["budget_index"] for row in reversed(rows) if row["decision"] in {"keep", "kept"})
    assert final["last_kept_trial_index"] == last_trial == (80 if early else expected)
    assert final["w"] == (7 if early else 20)
    assert final["config_sha256"] == config_sha256({"train.py": (node / "train.py").read_text()})
    return cdir, kept


def replicate_case(root, arm, *, final_keep=True):
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
    run_chunk(chunk_spec(arm), chunk, replicate_factory=factory, manifest=MANIFEST, observed=OBSERVED)
    cdir = chunk / "campaigns" / INSTANCE
    trial_rows = ledger(cdir / "ledger.jsonl")
    attempts = [row["record"] for row in ledger(cdir / "runs.jsonl")]
    kept_steps = {row["budget_index"] for row in trial_rows if row["decision"] == "kept"}
    kept = {}
    for charged, attempt in enumerate(attempts, start=1):
        step = attempt["step"]
        if step in kept_steps:
            kept[step] = (charged, validate(step)[0])
    final = load(cdir / "snapshots" / "final.json")
    assert final["w"] == len(attempts) == 20
    assert final["last_kept_trial_index"] == max(kept_steps)
    assert (kept[max(kept_steps)][0] == 20) == final_keep
    return cdir, list(kept.values())


def fake_audit(node, files, seeds):
    text = files["train.py"]
    if text.startswith("X = "):
        level = 0.1 * (1 + int(text.split("=")[1]))
    else:
        match = re.search(r"^LEARNING_RATE_INIT\s*=\s*([0-9.e+-]+)", text, re.MULTILINE)
        level = 50 * float(match[1])
    return [
        audit.Run(seed, 0.05 + level + 1e-5 * seed,
                  hashlib.sha256(f"{node}:{seed}:{text}".encode()).hexdigest())
        for seed in seeds
    ]


def g7_row(arm, audit_row, *, point, keep_run=None):
    return {
        "schema": table.AUDIT_ROW_SCHEMA,
        "campaign_id": analysis.campaign_id(STAGE, arm, NODE, SEED, 0),
        "point": point,
        "keep_run": keep_run,
        "config_sha256": audit_row["config_sha256"],
        "y_raw": audit_row["y_raw"],
    }


def require_refusal(operation, message):
    try:
        operation()
    except table.OutcomeTableError as exc:
        assert message in str(exc), str(exc)
        return str(exc)
    raise AssertionError(f"G7 should refuse: {message}")


def probe(root, cdir, kept, label):
    snapshots = cdir / "snapshots"
    final = load(snapshots / "final.json")
    arm, runs = final["arm"], final["w"]
    assert final["config_sha256"] == config_sha256(kept[-1][1])
    raw_summary = load(cdir / "summary.json")
    sigma = table.sigma_from_noise_source()[NODE]
    cache = audit.Cache()
    audit_result = audit.audit_campaign(cdir, root / "g6", sigma_node=sigma, runner=fake_audit, cache=cache)
    assert set(audit_result) == {"w", "final"}
    primary = audit_result["final"]
    assert primary["seeds"] == list(range(6701, 6711))
    assert not (root / "g6" / "Y_keep.jsonl").exists()
    reached = {str(row["w"]): row for row in audit_result["w"] if not row.get("missing_w")}
    audit_rows = [g7_row(arm, primary, point="final"), *(
        g7_row(arm, row, point=point) for point, row in reached.items()
    )]
    pre_differs = None
    if runs == 20:
        pre = load(snapshots / "w20_pre.json")
        assert pre["pre_decision"]
        pre_differs = pre["config_sha256"] != primary["config_sha256"]
        assert pre_differs == (kept[-1][0] == 20)
        assert primary["alias_of_w"] == 20
        assert primary["config_sha256"] == reached["20"]["config_sha256"]
        assert primary["y_raw"] == reached["20"]["y_raw"]
    else:
        assert "20" not in reached
        assert primary["w"] == 7 and primary.get("alias_of_w") is None

    # A published G1 summary reaches G7 with the same schema tag but incompatible fields.
    summary_refusal = require_refusal(
        lambda: table.build_row(STAGE, raw_summary, None), "a campaign summary must hold exactly"
    )

    # Adapt the stage/point fields and provide a synthetic accounting summary. This
    # reproduces the remaining real interface failure without conflating the two.
    summary = _summary(
        STAGE, arm, NODE, SEED, worker_runs=runs, llm_calls=raw_summary["llm_calls"],
        proposals=raw_summary["llm_calls"], start_config_hash=primary["start_config_sha256"],
        final_config_hash=primary["config_sha256"], last_keep_run=kept[-1][0], keeps=len(kept),
        distinct_configs_executed=min(runs, len(kept) + 1),
    )
    by_campaign = table._audits_by_campaign(audit_rows)
    cid = analysis.campaign_id(STAGE, arm, NODE, SEED, 0)
    keep_refusal = require_refusal(
        lambda: table.build_row(STAGE, summary, by_campaign[cid]), "one keep audit per keep is required"
    )

    # Supply all missing keep audits explicitly through the audit primitive only
    # to isolate verification of the canonical terminal G1 repair.
    for keep_run, files in kept:
        snap = {
            **final, "w": keep_run, "worker_runs": keep_run, "w_actual": keep_run,
            "incumbent_config": files, "config_sha256": config_sha256(files),
        }
        keep_row = audit.audit_snapshot(snap, sigma_node=sigma, runner=fake_audit, cache=cache)
        audit_rows.append(g7_row(arm, keep_row, point="keep", keep_run=keep_run))
    summaries, audits = _design()
    summaries = [row for row in summaries if table._check_summary(row, STAGE) != cid] + [summary]
    for fixture_summary in summaries:
        if fixture_summary["node"] == NODE:
            fixture_summary["start_config_hash"] = summary["start_config_hash"]
    audits = [row for row in audits if row["campaign_id"] != cid] + audit_rows
    complete = table.build_table(STAGE, summaries, audits, predeclaration_path=DECLARATION)
    target = next(row for row in complete["rows"] if row["campaign_id"] == cid)
    table_path = table.write_table(complete, root / "d3a_outcome.json")
    analysis_path = root / "d3a_report.json"
    assert analysis.main([
        "analyse", "--d3a", str(table_path), "--d3b-not-run", "not_started",
        "--predeclaration", str(DECLARATION), "--out", str(analysis_path),
    ]) == 0
    assert target["y_raw"] == primary["y_raw"]
    assert target["y_raw_w"]["20"] == (primary["y_raw"] if runs == 20 else None)
    assert target["last_keep_run"] == kept[-1][0]
    return {
        "case": label,
        "w_final": runs,
        "llm_calls": raw_summary["llm_calls"],
        "last_kept_trial": final["last_kept_trial_index"],
        "last_keep_run": target["last_keep_run"],
        "keeps": len(kept),
        "canonical_final_config_sha256": primary["config_sha256"],
        "pre_decision_config_differs_at_w20": pre_differs,
        "y_raw": round(target["y_raw"], 8),
        "y_raw_w20": None if target["y_raw_w"]["20"] is None else round(target["y_raw_w"]["20"], 8),
        "audit_seeds": primary["seeds"],
        "production_summary_refusal": summary_refusal,
        "production_g6_keep_refusal": keep_refusal,
        "analysis_with_fixture_bridge_pass": True,
    }


if __name__ == "__main__":
    for label, make in [
        ("harness_worker_cap_keep", lambda root: harness_case(root)),
        ("harness_worker_cap_discard", lambda root: harness_case(root, final_keep=False)),
        ("harness_call_cap_keep", lambda root: harness_case(root, early=True)),
        ("FIXR3_worker_cap_keep", lambda root: replicate_case(root, "FIXR3")),
        ("FIXR3_worker_cap_discard", lambda root: replicate_case(root, "FIXR3", final_keep=False)),
        ("EGATE_worker_cap_keep", lambda root: replicate_case(root, "EGATE")),
        ("EGATE_worker_cap_discard", lambda root: replicate_case(root, "EGATE", final_keep=False)),
    ]:
        root = Path(tempfile.mkdtemp(prefix="d3-step5-repeat-"))
        print(json.dumps(probe(root, *make(root), label), sort_keys=True), flush=True)
