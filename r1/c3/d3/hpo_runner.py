"""CPU HPO-REF campaign and terminal audit entry points for a signed stage launcher.

The launcher supplies the matched G1 start hash and admits the host under the stage note. Campaigns
preserve rendered editable files and a G6-compatible snapshot archive. The audit uses the G6 runner
and shared per-seed cache. This module does not submit jobs.
"""
from __future__ import annotations

import ast
from dataclasses import asdict
import hashlib
from itertools import count
import json
import math
from pathlib import Path
from platform import python_version
import time

import yaml

from r1.c3 import analysis_guard, d3_analysis as D3, d3_hpo_ref as hpo, d3_outcome_table as outcome
from r1.c3.features import apply_edit
from r1.c3.d3 import audit as g6
from r1.c3.d3.adapter import prepare_node_dir
from r1.c3.d3.campaign_chunk import sha256sums
from r1.c3.d3.snapshots import config_sha256
from r1.harness import harness_commit, import_harness

from autoresearch.manager.base import ManagerProposal
from autoresearch.manager.hyperparam_edits import parse_train_constants
from autoresearch.nodes.registry import load_registered_node
from autoresearch.worker.local_worker import LocalWorker


def _pinned_harness() -> Path:
    root = import_harness()
    observed = harness_commit(root)
    if observed["commit"] != hpo.HARNESS_PIN or observed["dirty"]:
        raise hpo.HpoRefError("HPO-REF needs the clean D.3 harness at its reviewed pin")
    return root


def _write(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _start_config(node_dir: Path, spec, space: hpo.NodeSpace):
    files = {rel: (node_dir / rel).read_text(encoding="utf-8") for rel in spec.editable_paths}
    symbols = set(spec.editable_symbols)
    sites = {}
    start = {}
    for rel in files:
        is_yaml = Path(rel).suffix in (".yaml", ".yml")
        for symbol, raw in parse_train_constants(node_dir / rel).items():
            if symbol not in symbols:
                continue
            if symbol in sites:
                raise hpo.HpoRefError(f"{symbol}: more than one editable assignment")
            sites[symbol] = (rel, raw, is_yaml)
            start[symbol] = yaml.safe_load(raw) if is_yaml else ast.literal_eval(raw)
    return files, sites, hpo.check_start_config(space, start)


def _render(files: dict, sites: dict, start: dict, config: dict) -> dict:
    rendered = dict(files)
    for symbol, value in config.items():
        if value == start[symbol]:
            continue
        rel, raw, is_yaml = sites[symbol]
        if is_yaml:
            literal = format(value, ".17e") if type(value) is float else json.dumps(value)
        else:
            literal = repr(value)
        rendered = apply_edit(rendered, {"path": rel, "symbol": symbol, "old": raw, "new": literal})
    return rendered


def _evaluator(node_dir: Path, attempt: Path, spec, renderer, worker_factory):
    worker = worker_factory(node_root=node_dir, artifact_dir=attempt / "worker", timeout_seconds=600)
    proposal = ManagerProposal(manager_mode="d3_hpo_ref", proposal_summary="HPO-REF trial",
                               proposal_rationale="Render the sampled configuration", target_files=spec.editable_paths,
                               objective="Run the rendered configuration.")
    trial_index = count(1)

    def evaluate(node, config, seed):
        files = renderer(config)
        for rel, source in files.items():
            (node_dir / rel).write_text(source, encoding="utf-8")
        started = time.perf_counter()
        result = worker.run_trial_at_seed(proposal, spec, next(trial_index), train_seed=seed, split_seed=seed)
        if result.changed_files or any((node_dir / rel).read_text(encoding="utf-8") != text
                                       for rel, text in files.items()):
            raise hpo.HpoRefError(f"{node}: worker changed the rendered configuration")
        metric = (result.parsed_metrics or {}).get(spec.metric_name) if result.success else None
        ok = type(metric) in (int, float) and math.isfinite(metric) and 0.0 <= metric <= 1.0
        return hpo.EvalResult(ok, metric if ok else None, time.perf_counter() - started)

    return evaluate


def _seal(c: hpo.Campaign, render, root: Path) -> Path:
    instance = D3.instance_id(c.node, c.instance_seed)
    campaign = root / "campaigns" / instance
    snapshots = campaign / "snapshots"
    snapshots.mkdir(parents=True, exist_ok=False)
    start = render(c.start_config)

    def payload(w, config, final=False):
        files = render(config)
        return {"schema": g6.SNAPSHOT_SCHEMA, "stage": hpo.STAGE, "arm": c.arm, "node": c.node,
                "repetition": c.repetition, "instance_id": instance, "w": w, "worker_runs": w,
                "w_actual": w, "incumbent_config": files, "start_config": start, "config_sha256": config_sha256(files),
                "final": final, "ended_on": c.ended_on if final else None}

    for w, config in c.snapshots.items():
        _write(snapshots / f"w{w}.json", payload(w, config))
    keeps = snapshots / "keeps"
    keeps.mkdir()
    for w, config in c.keeps:
        _write(keeps / f"w{w:02d}.json", payload(w, config))
    _write(snapshots / "final.json", payload(c.worker_runs, c.final_config, final=True))
    _write(campaign / "summary.json", hpo.campaign_summary(c))
    _write(campaign / "charged_runs.json", [asdict(run) for run in c.counter.runs])
    _write(campaign / "runtime.json", {"harness_commit": hpo.HARNESS_PIN, "python": python_version(),
                                       "smac_distributions": hpo.SMAC_PINS if c.arm == "SMAC3" else None})
    sha256sums(campaign)
    return campaign


def run_cpu_campaign(arm: str, node: str, seed: int, repetition: int, output_root: Path, *,
                     expected_start_sha256: str, data_cache_root: str | None = None,
                     worker_factory=LocalWorker) -> Path:
    """Run one CPU reference campaign from the byte-identical G1 start, in a fresh attempt tree."""
    if arm not in hpo.ARMS or node not in D3.NODES or type(seed) is not int or seed not in D3.INSTANCE_SEEDS:
        raise hpo.HpoRefError("invalid HPO-REF arm, node or instance seed")
    if type(repetition) is not int or not 0 <= repetition < D3.REPETITIONS:
        raise hpo.HpoRefError("invalid HPO-REF repetition")
    root = _pinned_harness()
    space = hpo.load_node_space(node, harness_root=root)
    spec = load_registered_node(node, repo_root=root)
    files, sites, start = _start_config(root / "nodes" / node, spec, space)
    if config_sha256(files) != expected_start_sha256:
        raise hpo.HpoRefError(f"{node}: rendered start differs from the matched G1 start hash")
    if arm == "SMAC3":
        hpo.require_smac()

    def render(config):
        return _render(files, sites, start, config)

    def digest(config):
        return config_sha256(render(config))

    output_root = Path(output_root)
    analysis_guard.refuse_sealed(output_root, data_cache_root)
    output_root.mkdir(parents=True, exist_ok=False)
    attempts = count(1)

    def attempt():
        directory = output_root / f"attempt-{next(attempts):03d}"
        directory.mkdir()
        node_dir = prepare_node_dir(node, directory / "node", spec=spec, harness=root, data_cache_root=data_cache_root)
        if {rel: (node_dir / rel).read_text(encoding="utf-8") for rel in files} != files:
            raise hpo.HpoRefError(f"{node}: prepared worker files differ from the G1 start")
        evaluate = _evaluator(node_dir, directory, spec, render, worker_factory)
        args = (space, start, seed, repetition, evaluate, digest, time.perf_counter)

        def backend(space, start, seed):
            return hpo.Smac3Backend(space, start, seed, output_directory=directory / "smac")

        try:
            if arm == "RS":
                return hpo._run_rs_attempt(*args)
            return hpo._run_smac_attempt(*args, backend)
        except hpo.InfrastructureFailure as exc:
            _write(directory / "infrastructure.json", {"failure": str(exc)})
            raise

    campaign = hpo.run_attempts(attempt)
    return _seal(campaign, render, output_root)


def _verify_seal(root: Path) -> None:
    manifest = root / "SHA256SUMS"
    if root.is_symlink():
        raise hpo.HpoRefError(f"{root}: the sealed campaign root is a symlink")
    entries = {}
    for path in sorted(root.rglob("*")):
        analysis_guard.refuse_sealed(path)
        if path.is_symlink():
            raise hpo.HpoRefError(f"{path}: a sealed campaign cannot contain symlinks")
        if path.is_file() and path != manifest:
            entries[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = "".join(f"{sha}  {name}\n" for name, sha in sorted(entries.items()))
    if manifest.read_text(encoding="utf-8") != expected:
        raise hpo.HpoRefError("campaign seal does not match its snapshot archive")


def audit_cpu_campaign(campaign_dir: Path, output_root: Path, *, sigma_node: float, scratch: Path,
                       cache: g6.Cache, runner: g6.Runner | None = None) -> dict:
    """Audit a sealed CPU campaign with G6 and produce the validated G7 outcome row."""
    campaign_dir, output_root, scratch = Path(campaign_dir), Path(output_root), Path(scratch)
    analysis_guard.refuse_sealed(campaign_dir, output_root, scratch)
    _verify_seal(campaign_dir)
    summary = json.loads((campaign_dir / "summary.json").read_bytes())
    cid = outcome._check_summary(summary, hpo.STAGE)
    identity = {key: summary[key] for key in ("stage", "arm", "node", "repetition")}
    identity["instance_id"] = D3.instance_id(summary["node"], summary["instance_seed"])
    snapshots = campaign_dir / "snapshots"
    final = g6.load_snapshot(snapshots / "final.json", **identity)
    final_w = summary["worker_runs"]
    ended_on = hpo.hpo_ended_on(arm=summary["arm"], worker_runs=final_w, proposals=summary["proposals"])
    if (campaign_dir.name != identity["instance_id"] or final["w"] != final_w or final["ended_on"] != ended_on
            or final["config_sha256"] != summary["final_config_hash"]
            or config_sha256(final["start_config"]) != summary["start_config_hash"]):
        raise hpo.HpoRefError("final snapshot differs from the HPO-REF campaign summary")
    for w in D3.BUDGET_POINTS:
        path = snapshots / f"w{w}.json"
        if path.is_file() != (w <= final_w):
            raise hpo.HpoRefError(f"w{w}: snapshot presence differs from the actual charged-run count")
        if w <= final_w:
            snap = g6.load_snapshot(path, **identity)
            if (snap["w"] != w or config_sha256(snap["start_config"]) != summary["start_config_hash"]
                    or w == D3.W and snap["config_sha256"] != final["config_sha256"]):
                raise hpo.HpoRefError(f"w{w}: snapshot differs from the HPO-REF campaign summary")
    keep_paths = sorted((snapshots / "keeps").glob("*.json"))
    keeps = [g6.load_snapshot(path, **identity) for path in keep_paths]
    keep_indexes = [snap["w"] for snap in keeps]
    if (len(keeps) != summary["keeps"] or keep_indexes != sorted(set(keep_indexes))
            or any(not 1 <= snap["w"] <= final_w
            or config_sha256(snap["start_config"]) != summary["start_config_hash"] for snap in keeps)):
        raise hpo.HpoRefError("kept snapshots differ from the HPO-REF campaign summary")
    if keeps and (keeps[-1]["w"] != summary["last_keep_run"]
                  or keeps[-1]["config_sha256"] != summary["final_config_hash"]):
        raise hpo.HpoRefError("last keep differs from the HPO-REF terminal incumbent")
    if cache is None:
        raise hpo.HpoRefError("HPO-REF requires the shared G6 audit cache")
    if runner is None:
        _pinned_harness()
        scratch.mkdir(parents=True, exist_ok=True)
        runner = g6.harness_runner(scratch)
    output_root.mkdir(parents=True, exist_ok=False)
    results = g6.audit_campaign(campaign_dir, output_root, sigma_node=sigma_node, runner=runner, cache=cache)

    def row(point, data, w=None):
        return {"schema": outcome.AUDIT_ROW_SCHEMA, "campaign_id": cid, "point": point, "keep_run": w,
                "config_sha256": data["config_sha256"], "y_raw": data["y_raw"]}

    audit = {"final": row("final", results["final"]), "keep": []}
    audit.update({str(record["w"]): row(str(record["w"]), record) for record in results["w"]
                  if not record.get("missing_w")})
    kept = output_root / "keeps"
    kept.mkdir()
    for snap in keeps:
        audited = g6.audit_snapshot(snap, sigma_node=sigma_node, runner=runner, cache=cache)
        _write(kept / f"w{snap['w']:02d}.json", audited)
        audit["keep"].append(row("keep", audited, snap["w"]))
    result = outcome.build_row(hpo.STAGE, summary, audit)
    _write(output_root / "g7_audit.json", audit)
    _write(output_root / "outcome_row.json", result)
    sha256sums(output_root)
    return result
