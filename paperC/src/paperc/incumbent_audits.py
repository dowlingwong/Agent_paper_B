"""R1-PAPERC-MEASURE-FIRST (a), using the classified Sweep 1 replay and CPU audit worker."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

from r1.c3 import audit, dataset, d3_analysis, features
from r1.c3.analysis_guard import SWEEP1_INDEX_PATH, refuse_sealed
from r1.harness import harness_root

NODES = ("digits_mlp", "openml_credit_approval", "openml_ionosphere", "tabular_mlp")
CLASSIFICATION = "results/r1/evidence/C3_sweep_classification_20261028.json"
REGISTRY = "paperC/seeds/registry_v1.json"
C1 = "results/r1/noise/D28_REPAIR_20261027/summary.json"
AUTHORIZATION = "docs/r1/authorizations/paperc_measure_a_20261127.md"
HARNESS = "6adf3859de66c4814fcf376eed59880fbd8eeaf7"
AUDIT_START = 10_900_000
K = 10


def check_seeds(path: Path, count: int) -> None:
    """Verify the proposed audit sub-block against the registered and newer R1 ranges."""
    registry = json.loads(path.read_text())
    block = next(b for b in registry["paper_c"] if b["name"] == "paperc_audits")
    end = AUDIT_START + count * K
    if count != len(NODES) * 18 or not block["lo"] <= AUDIT_START < end <= block["hi"]:
        raise ValueError("audit population or Paper C audit namespace differs from the pre-declaration")
    for b in registry["paper_b"] + [b for b in registry["paper_c"] if b != block]:
        if b["lo"] < end and AUDIT_START < b["hi"]:
            raise ValueError(f"audit block overlaps {b['name']}")
    recorded = next(c for c in registry["paper_c_claims"] if c["name"] == "esyn_rng_root")
    # The named E-SYN recorded roster uses disjoint nominal audit labels.
    if block["lo"] + K * recorded["index_ranges"]["recorded"][1] > AUDIT_START:
        raise ValueError("audit block overlaps the nominal E-SYN audit labels")
    for bounds in d3_analysis.RESERVED_SEED_NAMESPACES.values():
        if bounds is not None and bounds[0] < end and AUDIT_START <= bounds[1]:
            raise ValueError("audit block overlaps a reserved D.3 namespace")
    seeds = set().union(*d3_analysis.declared_d3_seeds().values(), d3_analysis.sweep_instance_seed_universe(),
                        range(20010, 20802))
    if any(AUDIT_START <= seed < end for seed in seeds):
        raise ValueError("audit block intersects a D.3, verify or historical sweep seed")


def replay_retained(rows: list[dict], start_files: dict, node: str, instance: str, mode: str) -> dict:
    """Replay the actual keeps, including the first valid outcome excluded by the proposal featurizer."""
    if [r["budget_index"] for r in rows] != list(range(1, 21)):
        raise ValueError(f"{instance}: expected exactly 20 charged Sweep 1 trials")
    current = features.normalise_files(start_files)
    configs = {features.files_hash(current): current}
    start = next(iter(configs))
    kept = []
    for row in rows:
        if row["decision"] != "kept":
            continue
        previous = features.files_hash(current)
        edit = features._row_edit(row)
        current = features.apply_edit(current, edit) if edit else current
        candidate = features.files_hash(current)
        configs[candidate] = current
        kept.append({"trial": row["budget_index"], "previous": previous, "candidate": candidate,
                     "recorded_delta": row.get("delta_vs_best")})
    return {"node": node, "instance": instance, "mode": mode, "start": start,
            "terminal": features.files_hash(current), "retained": kept, "configs": configs}


def prepare(paper: Path) -> dict:
    replay = dataset.sweep_replay_inputs(paper / SWEEP1_INDEX_PATH, paper_root=paper,
                                        classification=paper / CLASSIFICATION)
    if replay["index"]["harness_commit"] != HARNESS or len(replay["specs"]) != 2:
        raise ValueError("unexpected Sweep 1 code pin or memory-mode population")
    roots = []
    for spec, source in replay["specs"].values():
        for ledger in sorted(source.glob(spec["ledgers"])):
            instance = ledger.parent.name
            node = instance.split("__s")[0]
            if node in NODES:
                roots.append(replay_retained(features.read_jsonl(ledger),
                                              dataset._start_files(source, instance, node, strict=True),
                                              node, instance, spec["memory_mode"]))
    roster = sorted({(r["node"], int(r["instance"].rsplit("__s", 1)[1])) for r in roots})
    check_seeds(paper / REGISTRY, len(roster))
    if len(roots) != 2 * len(roster) or len({(r["instance"], r["mode"]) for r in roots}) != len(roots):
        raise ValueError("expected two distinct Sweep 1 memory-mode roots per node and seed")
    seed_at = {key: AUDIT_START + i * K for i, key in enumerate(roster)}
    for r in roots:
        first = seed_at[r["node"], int(r["instance"].rsplit("__s", 1)[1])]
        r["audit_seeds"] = list(range(first, first + K))
    return {"schema": "paperc_incumbent_audits/1", "harness": HARNESS,
            "c1_sha256": hashlib.sha256((paper / C1).read_bytes()).hexdigest(), "roots": roots}


def _audit_config(task: tuple) -> tuple[tuple, list[dict]]:
    key, files, scratch = task
    node, seeds, _ = key
    rows = audit.run_config(node, files, list(seeds), scratch, stop_on_invalid=True,
                            preserve_node_outputs=True)
    if [r["seed"] for r in rows] != list(seeds) or any(not r["success"] or r["changed_files"] or
                                                      not math.isfinite(r["metric"]) for r in rows):
        raise ValueError(f"invalid or incomplete audit for {key}")
    return key, rows


def summarise(roots: list[dict], results: dict, noise: dict, c1: dict) -> list[dict]:
    def pair(root, candidate, previous):
        prefix = (root["node"], tuple(root["audit_seeds"]))
        return statistics.mean(c["metric"] - p["metric"] for c, p in
                               zip(results[(*prefix, candidate)], results[(*prefix, previous)], strict=True))

    tables = []
    for node, mode in sorted({(r["node"], r["mode"]) for r in roots}):
        group = [r for r in roots if (r["node"], r["mode"]) == (node, mode)]
        first, subsequent, terminal, excess = [], [], [], []
        for root in group:
            terminal.append(pair(root, root["terminal"], root["start"]))
            for keep in root["retained"]:
                delta = pair(root, keep["candidate"], keep["previous"])
                recorded = keep["recorded_delta"]
                if recorded is None:
                    first.append(delta)
                else:
                    subsequent.append(delta)
                    excess.append(recorded - delta)
        sigma = noise[node]["sigma_node"]
        regret = statistics.median(e["decision_regret"] for e in c1["nodes"][node]["edits"]
                                   if e.get("decision_regret") is not None) / sigma
        increments = statistics.median(subsequent) / sigma if subsequent else None
        tables.append({"node": node, "mode": mode, "roots": len(group), "first_keeps": len(first),
                       "first_keep_median": statistics.median(first) if first else None,
                       "subsequent_keeps": len(subsequent),
                       "false_keeps": sum(d <= 0 for d in subsequent),
                       "terminal_gain_median": statistics.median(terminal),
                       "winner_curse_median": statistics.median(excess) if excess else None,
                       "kept_increment_sigma_d": increments, "decision_regret_sigma_d": regret,
                       "stakes_floor": regret >= .1 or (increments is not None and increments >= .5)})
    return tables


def run(paper: Path, plan_bytes: bytes, scratch: Path, out: Path) -> None:
    def git(repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True, timeout=30).strip()

    note = audit._key_block(audit._published_bytes(paper, AUTHORIZATION).decode())
    paper_commit = git(paper, "rev-parse", "HEAD")
    expected = {"task": "local/20261127-19a", "approved": "true", "paper_commit": paper_commit,
                "plan_sha256": hashlib.sha256(plan_bytes).hexdigest()}
    signer = note.get("signed_by", "").strip()
    if any(note.get(k) != v for k, v in expected.items()) or not signer or signer.startswith("TODO"):
        raise ValueError("published authorization does not bind this code and exact plan")
    git(paper, "merge-base", "--is-ancestor", paper_commit, "origin/main")
    harness = harness_root()
    if git(paper, "status", "--porcelain") or git(harness, "status", "--porcelain", "--untracked-files=no") or \
            git(harness, "rev-parse", "HEAD") != HARNESS:
        raise ValueError("paper or Sweep 1 harness checkout differs from the launch pin")
    workers = int(note.get("workers", 0))
    if not 1 <= workers <= 16:
        raise ValueError("signed worker count must be between 1 and 16")
    plan = json.loads(plan_bytes)
    if plan != prepare(paper):
        raise ValueError("signed audit plan no longer reproduces from the published Sweep 1 inputs")
    scratch.mkdir()
    out.mkdir()
    (out / "plan.json").write_bytes(plan_bytes)
    jobs = {(r["node"], tuple(r["audit_seeds"]), key): value for r in plan["roots"]
            for key, value in r["configs"].items()}
    results = {}
    with (out / "runs.jsonl").open("x") as stream, ProcessPoolExecutor(max_workers=workers) as pool:
        for key, rows in pool.map(_audit_config, ((key, cfg, str(scratch)) for key, cfg in jobs.items())):
            results[key] = rows
            stream.write(json.dumps({"node": key[0], "config": key[2], "rows": rows}, sort_keys=True) + "\n")
            stream.flush()
    table = summarise(plan["roots"], results, dataset.noise_table(paper / C1), json.loads((paper / C1).read_bytes()))
    (out / "summary.json").write_text(json.dumps(table, indent=2, sort_keys=True) + "\n")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "run"):
        p = sub.add_parser(command)
        p.add_argument("--paper", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
        if command == "run":
            p.add_argument("--scratch", type=Path, required=True)
            p.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    refuse_sealed(args.paper, args.out)
    if args.command == "prepare":
        with args.out.open("x") as out:
            json.dump(prepare(args.paper), out, indent=2, sort_keys=True)
            out.write("\n")
    else:
        refuse_sealed(args.plan, args.scratch)
        run(args.paper, args.plan.read_bytes(), args.scratch, args.out)


if __name__ == "__main__":
    main()
