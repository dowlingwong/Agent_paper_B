"""Fail-closed start measurement and ledger replay for Paper C measurement (b)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess

from r1.c3 import audit, dataset, d3_analysis, features
from r1.c3.analysis_guard import refuse_sealed
from r1.harness import harness_commit, import_harness

INSTANCE_SEEDS = {"digits_mlp": tuple(range(62_000, 62_006)),
                  "tabular_mlp": tuple(range(62_006, 62_012))}
AUDIT_START = 10_901_000
MEASUREMENT_A_AUDITS = range(10_900_000, 10_900_720)
HARNESS = "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"
AUTHORIZATION = "docs/r1/authorizations/paperc_measure_b_20261127.md"
C1 = "results/r1/noise/D28_REPAIR_20261027/summary.json"


def check_reservations(registry_path: Path) -> dict:
    """Check the proposed reserve without treating it as author approval."""
    return _check_registry(json.loads(registry_path.read_text()))


def _check_registry(registry: dict) -> dict:
    proposed = set().union(*INSTANCE_SEEDS.values())
    audit_seeds = set(range(AUDIT_START, AUDIT_START + 10 * len(proposed)))
    used = set().union(*d3_analysis.declared_d3_seeds().values(), d3_analysis.sweep_instance_seed_universe(),
                       range(20010, 20802))
    for b in registry["paper_b"]:
        if any(b["lo"] <= s < b["hi"] for s in proposed | audit_seeds):
            raise ValueError(f"proposed seeds overlap {b['name']}")
    for b in registry["paper_c"]:
        if b["name"] not in ("paperc_audits", "paperc_guarded_first_instances") and any(
                b["lo"] <= s < b["hi"] for s in proposed | audit_seeds):
            raise ValueError(f"proposed seeds overlap {b['name']}")
    for bounds in d3_analysis.RESERVED_SEED_NAMESPACES.values():
        if bounds is not None and any(bounds[0] <= s <= bounds[1] for s in proposed | audit_seeds):
            raise ValueError("proposed seeds overlap a reserved D.3 namespace")
    block = next(b for b in registry["paper_c"] if b["name"] == "paperc_audits")
    if (proposed | audit_seeds) & used or audit_seeds.intersection(MEASUREMENT_A_AUDITS) or \
            not block["lo"] + 10 * 10_000 <= min(audit_seeds) <= max(audit_seeds) < block["hi"]:
        raise ValueError("proposed seeds overlap an audit or D.3 reservation")
    return {"proposed_instances": {node: list(seeds) for node, seeds in INSTANCE_SEEDS.items()},
            "audit_seed_range": [min(audit_seeds), max(audit_seeds)],
            "instance_extension_published": any(b["name"] == "paperc_guarded_first_instances"
                                               and b["lo"] == min(proposed) and b["hi"] == max(proposed) + 1
                                               for b in registry["paper_c"])}

def metric(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite metric")
    return float(value)


def run_guarded(*, measure_start, run_campaign, **campaign_kwargs):
    """Pass the start score through the harness's initial incumbent API once."""
    if "initial_current_best" in campaign_kwargs:
        raise ValueError("the initial incumbent metric must come from the start measurement")
    start = metric(measure_start(), "start")
    return start, run_campaign(initial_current_best=start, **campaign_kwargs)


def verify_keeps(rows: list[dict], start_metric: float) -> list[int]:
    """Verify every decision against the current incumbent, including trial one."""
    incumbent = metric(start_metric, "start")
    keeps = []
    for expected, row in enumerate(rows, 1):
        if row.get("budget_index") != expected:
            raise ValueError(f"expected trial index {expected}")
        if row.get("current_best_before") != incumbent:
            raise ValueError(f"trial {expected} was compared with another incumbent")
        value = (row.get("parsed_metrics") or {}).get("val_score")
        decision = row.get("decision")
        if decision in ("failed_invalid", "skipped"):
            continue
        value = metric(value, f"trial {expected}")
        if decision != ("kept" if value > incumbent else "discarded"):
            raise ValueError(f"trial {expected} violates strict improvement")
        if decision == "kept":
            keeps.append(expected)
            incumbent = value
    if not rows:
        raise ValueError("empty campaign ledger")
    return keeps


def accounting(rows: list[dict], events: list[dict]) -> dict:
    endings = [e["payload"] for e in events if e["event_type"] == "campaign_completed"]
    if len(endings) != 1 or endings[0]["records_written"] != len(rows):
        raise ValueError("missing, duplicate or inconsistent terminal event")
    runs = sum(features.row_worker_runs(r) for r in rows)
    calls = sum(e["event_type"] == "llm_call" for e in events)
    proposals = sum(e["event_type"] in ("proposal_created", "proposal_revised")
                    or (e["event_type"] == "proposal_rejected_inactive_key" and not e["payload"].get("skipped"))
                    for e in events)
    if calls != proposals or not 1 <= runs <= 20 or not 1 <= calls <= 80:
        raise ValueError("ledger or proposal telemetry is inconsistent with the run/call budget")
    return {"candidate_worker_runs": runs, "start_worker_runs": 1, "llm_calls": calls}


def _authorized(paper: Path, spec_bytes: bytes) -> dict:
    def git(*args):
        return subprocess.check_output(["git", "-C", str(paper), *args], text=True, timeout=30).strip()

    root = paper.resolve()
    if Path(__file__).resolve().parents[3] != root or Path(audit.__file__).resolve().parents[2] != root:
        raise ValueError("executing code is outside the reviewed checkout")
    head = git("rev-parse", "HEAD")
    text = audit._published_bytes(root, AUTHORIZATION)
    note = audit._key_block(text.decode())
    expected = {"task": "local/20261127-19b", "approved": "true", "paper_commit": head,
                "spec_sha256": hashlib.sha256(spec_bytes).hexdigest()}
    if any(note.get(k) != v for k, v in expected.items()):
        raise ValueError("the exact guarded-first spec and code have not been authorized")
    plan = audit._published_bytes(root, "docs/r1/PLAN.md").decode()
    note_sha = hashlib.sha256(text).hexdigest()
    if not any(line.startswith("| R1-PAPERC-MEASURE-B-LAUNCH |") and note_sha in line for line in plan.splitlines()):
        raise ValueError("PLAN does not bind this guarded-first authorization")
    review_path = note.get("review_path", "")
    if not re.fullmatch(r"docs/r1/reviews/[A-Z0-9_]+\.md", review_path):
        raise ValueError("the note must bind the independent review")
    review = audit._published_bytes(root, review_path)
    if (hashlib.sha256(review).hexdigest() != note.get("review_sha256")
            or not {f"Code-Commit: {head}", "Verdict: ACCEPTED"} <= set(review.decode().splitlines())):
        raise ValueError("independent review did not accept the exact code commit")
    git("merge-base", "--is-ancestor", head, "origin/main")
    if git("status", "--porcelain") or socket.gethostname().split(".")[0] != "deepthought":
        raise ValueError("the clean paper pin must run on deepthought")
    return note


def run(paper: Path, spec_bytes: bytes, node: str, seed: int, out: Path, scratch: Path) -> None:
    note = _authorized(paper, spec_bytes)
    spec = json.loads(spec_bytes)
    if node not in INSTANCE_SEEDS or seed not in INSTANCE_SEEDS[node] or [node, seed] not in spec["roots"]:
        raise ValueError("root is outside the guarded-first pre-declaration")
    signed_registry = audit._published_bytes(paper, "paperC/seeds/registry_v1.json")
    if (hashlib.sha256(signed_registry).hexdigest() != spec["registry_sha256"]
            or not _check_registry(json.loads(signed_registry))["instance_extension_published"]):
        raise ValueError("published registry does not bind the author-approved worker extension")
    proposer = spec["proposer"]
    if (proposer["thinking"] is not False or note.get("proposer") != proposer["model"]
            or os.environ.get("LLAMACPP_BASE_URL") != proposer["base_url"]):
        raise ValueError("proposer environment differs from the signed identity")
    h = import_harness()
    pin = harness_commit(h)
    if pin["dirty"] or pin["commit"] != HARNESS:
        raise ValueError("Paper C harness checkout differs from the reviewed pin")
    from autoresearch.control_plane.budget import ComputeBudget
    from autoresearch.control_plane.campaign import run_real_campaign
    from autoresearch.memory.event_store import CampaignEventStore
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker
    from autoresearch.worker.seeds import seed_environment
    from r1.headroom.e1b_collect import make_manager

    node_spec = load_registered_node(node, repo_root=h)
    source = h / "nodes" / node
    start_files = {name: (source / name).read_text() for name in node_spec.editable_paths}
    out.mkdir()
    scratch.mkdir()
    work = scratch / "node"
    shutil.copytree(source, work, ignore=shutil.ignore_patterns(".autoresearch_artifacts", "__pycache__"))
    (out / "spec.json").write_bytes(spec_bytes)
    events, ledger = out / "events.jsonl", out / "ledger.jsonl"

    def measure(label, config, seeds):
        rows = audit.run_config(node, config, seeds, str(scratch), stop_on_invalid=True, stop_on_failure=True,
                                journal=str(out / f"{label}.jsonl"),
                                journal_identity={"expected_worker": spec["expected_worker"]})
        if [row["seed"] for row in rows] != seeds or any(not row["success"] or row["changed_files"] for row in rows):
            raise ValueError(f"incomplete CPU measurement: {label}")
        return [metric(row["metric"], label) for row in rows]

    try:
        campaign = f"pc-guarded-first-{node}__s{seed}"
        worker_runtime = audit.worker_runtime(spec["expected_worker"], node_spec.run_command, seed_environment(seed, seed))
        (out / "worker_runtime.json").write_text(json.dumps(worker_runtime, indent=2, sort_keys=True) + "\n")
        worker = LocalWorker(node_root=work, artifact_dir=scratch / "art", train_seed=seed, split_seed=seed)
        start, _ = run_guarded(measure_start=lambda: measure("start", start_files, [seed])[0],
                               run_campaign=run_real_campaign, node_spec=node_spec, campaign_id=campaign,
                               worker=worker, budget=40, records_path=ledger, manager_mode="langgraph_manager",
                               memory_mode="append_only_summary", proposal_backend=make_manager(
                                   node, seed, 0, {"kind": "langgraph", "model": proposer["model"],
                                                   "temperature": proposer["temperature"],
                                                   "proposal_schema": proposer["proposal_schema"]}),
                               event_store=CampaignEventStore(events),
                               compute_budget=ComputeBudget(max_worker_runs=20, max_llm_calls=80))
        rows = features.read_jsonl(ledger)
        kept = set(verify_keeps(rows, start))
        counts = accounting(rows, features.read_jsonl(events))
        seeds = list(range(AUDIT_START + 10 * (seed - 62_000), AUDIT_START + 10 * (seed - 62_000) + 10))
        current, audited = start_files, {}

        def fresh(config):
            key = features.files_hash(config)
            if key not in audited:
                audited[key] = measure(key, config, seeds)
            return audited[key]

        previous = start_audit = fresh(start_files)
        deltas = []
        for row in rows:
            if row["budget_index"] in kept:
                edit = features._row_edit(row)
                if not edit:
                    raise ValueError("a kept guarded-first row has no replayable edit")
                current = features.apply_edit(current, edit)
                candidate = fresh(current)
                deltas.append({"trial": row["budget_index"], "config": features.files_hash(current),
                               **audit.paired(candidate, previous)})
                previous = candidate
        if any((work / name).read_text() != text for name, text in current.items()):
            raise ValueError("replayed terminal configuration differs from the harness workspace")
        c1 = json.loads((paper / C1).read_bytes())
        sigma = dataset.noise_table(paper / C1)[node]["sigma_node"]
        result = {"node": node, "seed": seed, "start_metric": start, "trial_one": rows[0]["decision"],
                  "paper_commit": note["paper_commit"], "spec_sha256": note["spec_sha256"],
                  "start_config": features.files_hash(start_files),
                  "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
                  "audit_seeds": seeds, "counts": counts, "kept": deltas, "sigma_d": sigma,
                  "c1_sha256": hashlib.sha256((paper / C1).read_bytes()).hexdigest(),
                  "c1_regrets": [e["decision_regret"] for e in c1["nodes"][node]["edits"]
                                 if e.get("decision_regret") is not None],
                  "terminal": {"config": features.files_hash(current), **audit.paired(previous, start_audit)}}
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except Exception as exc:
        (out / "STOP.json").write_text(json.dumps({"class": type(exc).__name__, "message": str(exc)}) + "\n")
        raise


def summarise(records: list[dict]) -> list[dict]:
    """Evaluate the signed stake criteria across all six root pairs per node."""
    keys = {(r["node"], r["seed"]) for r in records}
    expected = {(node, seed) for node, seeds in INSTANCE_SEEDS.items() for seed in seeds}
    if keys != expected or len(records) != len(keys):
        raise ValueError("guarded-first receipts do not cover the exact roster")
    if len({(root["paper_commit"], root["spec_sha256"]) for root in records}) != 1:
        raise ValueError("guarded-first receipts differ in spec or code pin")
    for root in records:
        first_seed = AUDIT_START + 10 * (root["seed"] - 62_000)
        if root["audit_seeds"] != list(range(first_seed, first_seed + 10)):
            raise ValueError("guarded-first receipt differs from the bound audit seed block")
    out = []
    for node in INSTANCE_SEEDS:
        roots = [r for r in records if r["node"] == node]
        first = roots[0]
        same = ("sigma_d", "c1_sha256", "c1_regrets")
        if any(any(root[k] != first[k] for k in same) for root in roots):
            raise ValueError(f"{node}: frozen C1 basis differs across roots")
        sigma = first["sigma_d"]
        regret = statistics.median(first["c1_regrets"]) / sigma
        increments = [keep["delta_audit"] / sigma for r in roots for keep in r["kept"]]
        median = statistics.median(increments) if increments else None
        out.append({"node": node, "retained": len(increments), "median_increment_sigma_d": median,
                    "decision_regret_sigma_d": regret,
                    "stakes_floor": regret >= .1 or (median is not None and median >= .5),
                    "trial_one_kept": sum(r["trial_one"] == "kept" for r in roots),
                    "terminal_gain_median": statistics.median(r["terminal"]["delta_audit"] for r in roots)})
    return out


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--node", choices=INSTANCE_SEEDS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args(argv)
    refuse_sealed(args.paper, args.spec, args.out, args.scratch)
    run(args.paper, args.spec.read_bytes(), args.node, args.seed, args.out, args.scratch)


if __name__ == "__main__":
    main()
