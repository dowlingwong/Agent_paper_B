"""Build the C3 proposal table from root ledgers (C3_DESIGN §3-4). ENGINEERING_ONLY; AI-assisted (Claude).

Sources (roots only; no branch ledgers):
- ``dt4``      results/r1/pilot/E1b_20261013T151857Z            (memory none, W = 20)
- ``rerun2A``  results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014 (memory on, W = 20; PARTIAL)
- ``liveness`` results/r1/engineering/liveness_llm_20261014T140742Z    (memory on, W = 10)

Usage:
  python -m r1.c3.dataset build --out DIR
  python -m r1.c3.dataset build-sweep --index SWEEP --out DIR [--paper-root DIR] [--e1-summary FILE]
  python -m r1.c3.dataset plan  --table DIR [--quota rerun2A:tabular_mlp:70 ...] [--di]

``build-sweep`` (RUNBOOK A.4) builds the same table from a completed C3 label
sweep: SWEEP is the sweep index ``results/r1/pilot/C3_sweep_index_<UTC>.json``
(schema ``r1.c3_sweep_index/1``, written by ``r1/scripts/c3_label_sweep.py``) or
the sweep's batch directory (its ``batch_state.json`` names the index; the paper
clone is ``<batch>/agent_paper_B``). One source per memory mode, named
``c3_<index UTC>_<memory mode>`` unless ``--source-name MODE=NAME`` is given;
rows are produced by the same replay and ``row_of`` as ``build``.

``build`` writes DIR/proposals.jsonl (features, logged Delta_hat, decision, inert
flag, instance, node, memory mode, config hashes), DIR/configs.json (file texts
by hash) and DIR/build.json (sources, replay checks, noise table). ``plan``
writes DIR/plan.jsonl: a seeded random audit sample of non-inert proposals per
(source, node) stratum, plus (``--di``) the DI-changed candidates.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from r1.c3.analysis_guard import refuse_sealed

from r1.c3.features import (NODE_INFO, Proposal, configuration, files_hash, normalise_files, read_jsonl,
                            replay_campaign)
from r1.harness import REPO, harness_root
from r1.exam.namespace import refuse_exam

LEGACY_LIVENESS_HARNESS = "411c6054c8505f93a6429e2f9eed526952793882"
E1_SUMMARY = "results/r1/pilot/E1_20261022T214606Z/summary.json"  # common 30-seed run, the C1 noise-floor table (PLAN §10, 22 Oct); was E1_20261012T145353Z
SOURCES = {
    "dt4": {"dir": "results/r1/pilot/E1b_20261013T151857Z", "ledgers": "provenance/ledgers/roots/*/root_trials.jsonl*",
            "runs": 20, "memory_mode": "none"},
    "rerun2A": {"dir": "results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014",
                "ledgers": "provenance/ledgers/roots/*/root_trials.jsonl*", "runs": 20,
                "memory_mode": "append_only_summary"},
    "liveness": {"dir": "results/r1/engineering/liveness_llm_20261014T140742Z", "ledgers": "ledgers/*/root_trials.jsonl",
                 "runs": 10, "memory_mode": "append_only_summary"},
}
# Decision-changed E2 points of the DI analyses (docs/r1/reports/
# DI_TEST_MEMORY_ON_PARTIAL_20261019_tables.md, "Decision audit"): the root trial
# at budget index b is the candidate; it was compared against the E2 incumbent.
DI_CHANGED = {
    "rerun2A": [("tabular_mlp__s102", 12, "promotion"), ("tabular_mlp__s112", 8, "promotion"),
                ("tabular_mlp__s112", 12, "promotion"), ("tabular_mlp__s122", 12, "demotion"),
                ("tabular_mlp__s132", 8, "promotion"), ("tabular_mlp__s152", 8, "promotion"),
                ("tabular_mlp__s152", 12, "promotion"), ("tabular_mlp__s182", 4, "demotion"),
                ("tabular_mlp__s182", 8, "promotion"), ("tabular_mlp__s202", 4, "demotion"),
                ("tabular_mlp__s232", 4, "demotion"), ("tabular_mlp__s252", 8, "promotion"),
                ("tabular_mlp__s252", 12, "promotion")],
    "dt4": [("digits_mlp__s104", 8, "promotion"), ("digits_mlp__s104", 12, "promotion"),
            ("digits_mlp__s114", 8, "promotion"), ("digits_mlp__s134", 8, "promotion"),
            ("digits_mlp__s144", 4, "promotion"), ("digits_mlp__s144", 8, "promotion")],
}
DEFAULT_QUOTA = {("rerun2A", "tabular_mlp"): 70, ("rerun2A", "openml_breast_w"): 54, ("dt4", "digits_mlp"): 26}
PLAN_SEED = 20261019


def noise_table(summary_path: Path | str = REPO / E1_SUMMARY) -> dict:
    """Per-node noise constants from the E1 summary.

    sigma_node: median sd_joint over material edits (the e1b ``sigma_d`` definition);
    used to standardise z = Delta / sigma_node.
    sigma_local / sigma_structural: median sd_joint over local / model_type edits
    (comparison noise per edit kind, T4 (A2)); MLP nodes have only local edits and
    use sigma_node.
    delta_n (D18): max(0.002, 0.25 x median paired sd over all E1 edits).

    Nodes in NODE_INFO that the summary does not cover (e.g. the 22 Oct pool
    extension before its E1 run) get no entry, so any later use of them fails
    loudly with a KeyError instead of being given invented constants.
    """
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(summary_path)
    s = json.loads(Path(summary_path).read_text())
    out = {}
    for node in (n for n in NODE_INFO if n in s["nodes"]):
        edits = [e for e in s["nodes"][node]["edits"] if "sd_joint" in e]
        mats = [e for e in edits if e.get("material")] or edits
        sig = float(np.median([e["sd_joint"] for e in mats]))
        struct = [e["sd_joint"] for e in edits if e["edit"].startswith("model_type")]
        local = [e["sd_joint"] for e in edits if not e["edit"].startswith("model_type")]
        med_all = float(np.median([e["sd_joint"] for e in edits]))
        fam = NODE_INFO[node]["family"]
        out[node] = {"sigma_node": sig,
                     "sigma_local": float(np.median(local)) if fam == "openml" and local else sig,
                     "sigma_structural": float(np.median(struct)) if fam == "openml" and struct else sig,
                     "median_sd_all": med_all, "delta_n": max(0.002, 0.25 * med_all)}
    return out


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _start_files(src_dir: Path, inst: str, node: str, strict: bool = False) -> dict:
    rj = src_dir / "roots" / f"{inst}.json"
    refuse_sealed(rj)
    if rj.exists():
        return json.loads(rj.read_text())["start_files"]
    if strict:  # sweep outputs always record start files; never fall back to today's node files
        raise ValueError(f"{rj}: root record with start files missing")
    # Historical liveness has no captured start files. Use its recorded clean harness commit,
    # not the current checkout, which may have a different start configuration.
    if src_dir.resolve() != (REPO / SOURCES["liveness"]["dir"]).resolve():
        raise ValueError(f"{src_dir}: no authorized historical start-file fallback")
    manifest_path = src_dir / "manifest.json"
    refuse_sealed(manifest_path)
    if not manifest_path.is_file():
        raise ValueError(f"{src_dir}: missing historical manifest for start files")
    harness = json.loads(manifest_path.read_text()).get("harness") or {}
    revision = harness.get("commit")
    if revision != LEGACY_LIVENESS_HARNESS or harness.get("dirty") is not False:
        raise ValueError(f"{src_dir}: historical start files require the recorded clean liveness harness commit")
    path = "train.py" if NODE_INFO[node]["family"] == "mlp" else "config.yaml"
    result = subprocess.run(["git", "-C", str(harness_root()), "show", f"{revision}:nodes/{node}/{path}"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"{src_dir}: historical harness object {revision}:nodes/{node}/{path} unavailable")
    return {path: result.stdout}


def _replay_sources(specs: dict, noise: dict, strict_start_files: bool = False) -> tuple[list, dict, dict]:
    """Replay every root ledger of ``specs`` ({name: (spec, source dir)}), in order; rows, configs, checks."""
    rows, configs, checks = [], {}, {}
    for name, (src, d) in specs.items():
        refuse_sealed(d, d / 'manifest.json')
        refuse_exam(src, context=f'C3 source {name}')
        if (d / 'manifest.json').exists():
            refuse_exam(json.loads((d / 'manifest.json').read_text()), context=f'C3 manifest {d}')
        for f in sorted(glob.glob(str(d / src["ledgers"]))):
            inst = Path(f).parent.name
            node = inst.split("__s")[0]
            records = read_jsonl(Path(f))
            refuse_exam(records, context=f'C3 ledger {f}')
            refuse_exam(inst, context=f'C3 ledger {f}')
            props, ch = replay_campaign(records, _start_files(d, inst, node, strict_start_files), node,
                                        inst, name, src["memory_mode"], src["runs"], noise[node]["sigma_node"])
            checks[f"{name}:{inst}"] = ch
            for p in props:
                configs[p.candidate_hash] = {"node": node, "files": p.candidate_files}
                configs[p.incumbent_hash] = {"node": node, "files": p.incumbent_files}
                rows.append(row_of(p, noise))
    return rows, configs, checks


def _write_table(out: Path, rows: list, configs: dict, checks: dict, head: dict, noise: dict) -> dict:
    with open(out / "proposals.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    (out / "configs.json").write_text(json.dumps(configs))
    tot = {k: sum(c[k] for c in checks.values()) for k in next(iter(checks.values()))}
    meta = {**head, "noise": noise, "replay_checks_total": tot,
            "replay_checks": checks, "n_proposals": len(rows), "n_configs": len(configs)}
    if head.get('label') == 'EVIDENCE':
        meta['table_sha256'] = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                for name in ('proposals.jsonl', 'configs.json')}
    (out / "build.json").write_text(json.dumps(meta, indent=1))
    return meta


def build(out: Path, sources=tuple(SOURCES), e1_summary: Path | str | None = None) -> dict:
    """The historical pilot table.  ``e1_summary`` (default ``E1_SUMMARY``) picks the noise source,
    e.g. the 12 Oct E1 for an exact rebuild of the 19 Oct pilot table."""
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(out,e1_summary)
    noise = noise_table() if e1_summary is None else noise_table(e1_summary)
    out.mkdir(parents=True, exist_ok=True)
    rows, configs, checks = _replay_sources({name: (SOURCES[name], REPO / SOURCES[name]["dir"]) for name in sources},
                                            noise)
    head = {"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)", "commit": git_head(),
            "sources": {k: SOURCES[k] for k in sources}}
    return _write_table(out, rows, configs, checks, head, noise)


# ---------------------------------------------------------------------------
# Sweep index -> table (RUNBOOK A.4)
# ---------------------------------------------------------------------------

SWEEP_INDEX_SCHEMA = "r1.c3_sweep_index/1"
SWEEP_LEDGERS = "*/root_trials.jsonl*"  # under the index's per-sweep ``ledgers`` directory
SOURCE_NAME = re.compile(r"[A-Za-z0-9_]+")  # no ':' (proposal ids and --quota use it as separator)


def _sha256(path: Path) -> str:
    refuse_sealed(path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _safe_relative(root: Path, value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or not rel.parts or '..' in rel.parts:
        raise ValueError('classification paths must be repository-relative')
    result = (root / rel).resolve()
    refuse_sealed(root / rel, result)
    if not result.is_relative_to(root.resolve()):
        raise ValueError('classification path escapes repository')
    return result


def _verify_published(root: Path, paths: list[str]) -> None:
    """Require exact authority bytes from the current, remotely published main."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, timeout=30)
    remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
    if git('rev-parse', 'refs/remotes/origin/main').decode().strip() != remote:
        raise ValueError('origin/main is stale or missing; fetch before evidence use')
    for rel in paths:
        if git('show', f'{remote}:{rel}') != _safe_relative(root, rel).read_bytes():
            raise ValueError(f'published origin/main differs from evidence authority: {rel}')


def _verify_original_blobs(root: Path, index: dict, entries: list[dict]) -> None:
    """Every moved file must be byte-identical to its original sweep commit."""
    if subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-object-format']).decode().strip() != 'sha1':
        raise ValueError('unsupported git object format')
    for sweep in index['sweeps']:
        entry = next(e for e in entries if e['memory_mode'] == sweep['memory_mode'])
        old, new = Path(entry['old_dir']), _safe_relative(root, entry['new_dir'])
        raw = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '-z',
                                       sweep['commit'], '--', str(old)])
        expected = {}
        for line in raw.split(b'\0'):
            if not line:
                continue
            header, path = line.split(b'\t', 1)
            mode, kind, digest = header.decode().split()
            relative = Path(path.decode()).relative_to(old)
            if kind != 'blob' or mode not in ('100644', '100755'):
                raise ValueError('sweep contains unsupported git object')
            expected[str(relative)] = digest
        if not expected:
            raise ValueError('no original sweep blobs found')
        actual = {}
        for path in new.rglob('*'):
            refuse_sealed(path)
            if path.is_symlink():
                raise ValueError('symlinks forbidden in classified sweep')
            if path.is_file():
                data = path.read_bytes()
                actual[str(path.relative_to(new))] = hashlib.sha1(
                    b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != expected:
            raise ValueError('moved sweep differs from original commit blobs')


def evidence_classification(index_path: Path, paper_root: Path, sidecar_path: Path) -> dict:
    """Resolve the author's exact immutable classification, never rewrite native records."""
    refuse_sealed(index_path, paper_root, sidecar_path)
    root = Path(paper_root).resolve()
    sidecar = Path(sidecar_path).resolve()
    index_path = Path(index_path).resolve()
    if not sidecar.is_relative_to(root) or not index_path.is_relative_to(root):
        raise ValueError('classification and index must be inside repository')
    decision = json.loads(sidecar.read_text())
    if decision.get('schema') != 'r1.c3_classification/1' or decision.get('label') != 'EVIDENCE' or decision.get('decision_id') != 'R1-SWEEP1-CLASSIFY':
        raise ValueError('invalid evidence classification')
    auth = decision['authorization']
    source = decision['index']
    if auth['path'] != 'docs/r1/authorizations/c3_sweep1_20261027.md' or _sha256(_safe_relative(root, auth['path'])) != auth['sha256']:
        raise ValueError('authorization missing or hash mismatch')
    if source['path'] != 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json' or _safe_relative(root, source['path']) != index_path or _sha256(index_path) != source['sha256']:
        raise ValueError('index path or hash mismatch')
    side_rel = str(sidecar.relative_to(root))
    required = ('R1-SWEEP1-CLASSIFY', 'EVIDENCE', auth['path'], source['path'], source['sha256'], side_rel, _sha256(sidecar))
    refuse_sealed(root / 'docs/r1/PLAN.md')
    rows = (root / 'docs/r1/PLAN.md').read_text().splitlines()
    if not any(line.startswith('| R1-SWEEP1-CLASSIFY ') and all(x in line for x in required) for line in rows):
        raise ValueError('matching author PLAN classification row missing')
    _verify_published(root, ['docs/r1/PLAN.md', auth['path'], source['path'], side_rel])
    index = json.loads(index_path.read_text())
    provenance = index.get('launch_provenance') or {}
    expected_pins = {
        'paper_commit': 'ccb47128aad82e331f79df4a893dbc1ee7e42f51',
        'harness_commit': '6adf3859de66c4814fcf376eed59880fbd8eeaf7',
        'config_sha256': '2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b',
        'model_sha256': '509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c',
        'llamacpp_build': 'version: 0.7.0-dev (build 1, commit 620d222)',
    }
    note = _safe_relative(root, auth['path']).read_text()
    if provenance != expected_pins or any(v not in note for k, v in expected_pins.items() if k != 'paper_commit'):
        raise ValueError('classification launch pins do not match authorization')
    nodes = ['digits_mlp', 'tabular_mlp', 'openml_breast_w', 'openml_ionosphere', 'openml_wdbc',
             'openml_credit_approval', 'openml_sonar', 'openml_climate']
    if index.get('nodes') != nodes or index.get('excluded_nodes') != [] or index.get('instances') != 18 or index.get('runs') != 20 or \
            index.get('manager', {}).get('proposal_schema') != 'manager_proposal/v1':
        raise ValueError('classified sweep design differs from authorization')
    audit = index.get('audit') or {}
    if audit.get('seeds') != list(range(7001, 7011)) or audit.get('label_seeds') != list(range(7001, 7006)) or \
            audit.get('evaluation_seeds') != list(range(7006, 7011)):
        raise ValueError('classified sweep audit seeds differ from authorization')
    entries = decision['sweeps']
    if len(entries) != 2 or {e['memory_mode'] for e in entries} != {'none', 'append_only_summary'}:
        raise ValueError('classification must bind both memory modes')
    indexed = {s['memory_mode']: s for s in index['sweeps']}
    if set(indexed) != {e['memory_mode'] for e in entries}:
        raise ValueError('classification does not bind exact index modes')
    for entry in entries:
        recorded = indexed[entry['memory_mode']]
        old = Path(recorded['out'])
        if str(old) != entry['old_dir'] or old.parts[:3] != ('results', 'r1', 'pilot'):
            raise ValueError('classification old directory differs from index')
        expected_new = Path('results/r1/evidence') / old.name
        if str(expected_new) != entry['new_dir'] or recorded['manifest'] != str(old / 'manifest.json') or not Path(recorded['ledgers']).is_relative_to(old):
            raise ValueError('classification path mapping differs from index')
        manifest = _safe_relative(root, str(expected_new / 'manifest.json'))
        if _sha256(manifest) != entry['manifest_sha256']:
            raise ValueError('classified manifest hash mismatch')
        if json.loads(manifest.read_text()).get('launch_provenance') != provenance:
            raise ValueError('classified manifest launch pins differ from index')
    _verify_original_blobs(root, index, entries)
    return decision


def resolve_sweep(sweep: Path | str, paper_root: Path | str | None = None) -> tuple[Path, Path]:
    """(index file, paper root) from an index file or a completed sweep batch directory."""
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(sweep,paper_root)
    sweep = Path(sweep)
    if sweep.is_dir():
        state_path = sweep / "batch_state.json"
        refuse_sealed(state_path)
        if not state_path.exists():
            raise ValueError(f"{sweep}: not a sweep batch directory (no batch_state.json)")
        step = json.loads(state_path.read_text()).get("steps", {}).get("index") or {}
        if not step.get("completed") or not step.get("path"):
            raise ValueError(f"{sweep}: the sweep's index phase is not completed; no table from an unfinished sweep")
        root = Path(paper_root) if paper_root else sweep / "agent_paper_B"
        recorded = Path(step["path"])
        local = root / "results/r1/pilot" / recorded.name
        index = local if paper_root and local.exists() else recorded if recorded.exists() else local
        return index, root
    if paper_root:
        return sweep, Path(paper_root)
    parts = sweep.resolve().parts
    if len(parts) >= 5 and parts[-4:-1] == ("results", "r1", "pilot"):
        return sweep, sweep.resolve().parents[3]
    raise ValueError(f"{sweep}: index outside <paper>/results/r1/pilot; pass paper_root")


def sweep_sources(index: dict, index_path: Path, paper_root: Path, source_names: dict | None = None,
                  classification: dict | None = None) -> dict:
    """Validated per-memory-mode sources of a sweep index: {name: (spec, sweep dir)}.

    Refuses (ValueError) a wrong schema, a sweep with recorded root failures, a
    manifest that disagrees with the index (memory mode, W, instances; for real
    sweep manifests also the node list), or a ledger count other than
    nodes x instances.  Sources are named ``c3_<index UTC>_<memory mode>``
    unless ``source_names`` maps a memory mode to a name.
    """
    refuse_exam(index, context='C3 sweep index')
    if index.get("schema") != SWEEP_INDEX_SCHEMA:
        raise ValueError(f"{index_path}: schema {index.get('schema')!r}, expected {SWEEP_INDEX_SCHEMA!r}")
    tag = re.sub(r"[^0-9A-Za-z]", "", str(index.get("written_utc", "")))
    names = dict(source_names or {})
    specs = {}
    for sweep in index["sweeps"]:
        sweep = dict(sweep)
        if classification is not None:
            binding = next(e for e in classification['sweeps'] if e['memory_mode'] == sweep['memory_mode'])
            old, new = Path(binding['old_dir']), Path(binding['new_dir'])
            for key in ('out', 'manifest', 'ledgers'):
                sweep[key] = str(new / Path(sweep[key]).relative_to(old))
        mode = sweep["memory_mode"]
        name = names.pop(mode, f"c3_{tag}_{mode}")
        if not SOURCE_NAME.fullmatch(name) or name in specs:
            raise ValueError(f"invalid or duplicate source name {name!r}")
        d = paper_root / sweep["out"]
        manifest_path = paper_root / sweep["manifest"]
        refuse_sealed(d, manifest_path, paper_root / sweep['ledgers'])
        manifest = json.loads(manifest_path.read_text())
        refuse_exam(manifest, context=f'C3 manifest {manifest_path}')
        if manifest.get("launch_provenance") != index.get("launch_provenance"):
            raise ValueError(f"{manifest_path}: launch provenance differs from sweep index")
        noise_source = index.get("noise_source")
        if noise_source is not None:
            if (manifest.get("c3_label_sweep") or {}).get("noise_source") != noise_source:
                raise ValueError(f"{manifest_path}: noise source differs from sweep index")
            if set(manifest.get("noise", {})) != set(manifest["nodes"]):
                raise ValueError(f"{manifest_path}: noise-node set differs from manifest nodes")
            pinned = (paper_root / noise_source["path"]).resolve()
            refuse_sealed(paper_root / noise_source['path'], pinned)
            if not pinned.is_relative_to(paper_root.resolve()) or not pinned.is_file() or _sha256(pinned) != noise_source["sha256"]:
                raise ValueError(f"{manifest_path}: pinned noise source missing or sha256 mismatch")
            from r1.headroom.e1b_collect import node_noise
            for node, entry in manifest["noise"].items():
                source_path = Path(entry.get("source", ""))
                if not source_path.is_absolute():
                    source_path = paper_root / source_path
                if source_path.resolve() != pinned:
                    raise ValueError(f"{manifest_path}: noise path differs from sweep index")
                expected = node_noise(pinned, node)
                if any(entry.get(key) != expected[key] for key in ("sigma_t", "sigma_s", "sigma_d", "definition")):
                    raise ValueError(f"{manifest_path}: noise values differ from pinned source for {node}")
        ledgers = paper_root / sweep["ledgers"]
        if (d / "collection_failures.json").exists() or any((d / "failures").glob("*.json")):
            raise ValueError(f"{d}: the sweep recorded failures; no table from an incomplete sweep")
        if (manifest.get("memory_mode") or "none") != mode:
            raise ValueError(f"{manifest_path}: memory mode {manifest.get('memory_mode')!r} != index {mode!r}")
        if int(manifest["runs"]) != int(index["runs"]) or int(manifest["instances"]) != int(index["instances"]):
            raise ValueError(f"{manifest_path}: runs/instances differ from the index")
        if "c3_label_sweep" in manifest and list(manifest["nodes"]) != list(index["nodes"]):
            raise ValueError(f"{manifest_path}: nodes {manifest['nodes']} != index nodes {index['nodes']}")
        files = sorted(glob.glob(str(ledgers / SWEEP_LEDGERS)))
        expected = len(manifest["nodes"]) * int(manifest["instances"])
        if len(files) != expected:
            raise ValueError(f"{ledgers}: {len(files)} root ledgers, expected {expected} (nodes x instances)")
        unknown = {Path(f).parent.name.split("__s")[0] for f in files} - set(manifest["nodes"])
        if unknown:
            raise ValueError(f"{ledgers}: ledgers of nodes outside the manifest: {sorted(unknown)}")
        rel = Path(sweep["ledgers"]).relative_to(sweep["out"]) if Path(sweep["ledgers"]).is_relative_to(sweep["out"]) \
            else None
        if rel is None:
            raise ValueError(f"{sweep['ledgers']}: ledgers must lie inside the sweep directory {sweep['out']}")
        spec = {"dir": sweep["out"], "ledgers": str(rel / SWEEP_LEDGERS), "runs": int(index["runs"]),
                "memory_mode": mode, "manifest": sweep["manifest"], "manifest_sha256": _sha256(manifest_path),
                "commit": sweep.get("commit"), "label": manifest.get("label"),
                "noise_source_at_collection": {n: v.get("source") for n, v in (manifest.get("noise") or {}).items()}}
        specs[name] = (spec, d)
    if names:
        raise ValueError(f"source names for memory modes not in the index: {sorted(names)}")
    return specs


def sweep_replay_inputs(sweep: Path | str, *, paper_root: Path | str | None = None,
                        e1_summary: Path | str | None = None, source_names: dict | None = None,
                        classification: Path | str | None = None) -> dict:
    """The validated replay inputs of a completed C3 label sweep (index, classification, sources, noise).

    Shared by ``build_from_sweep`` and the Track P SFT prompt builder (``r1.c3.train.sft_data``), so both replay
    exactly the same ledgers under exactly the same checks.  Returns ``{"index_path", "root", "index", "decision",
    "specs", "source", "e1_summary", "noise"}``.
    """
    from r1.c3.analysis_guard import refuse_sealed, require_d8_confirmation, SWEEP1_INDEX_SHA, SWEEP1_INDEX_PATH
    refuse_sealed(sweep,paper_root,e1_summary,classification)
    index_path, root = resolve_sweep(sweep, paper_root)
    refuse_sealed(index_path, root)
    if (Path(index_path).resolve() != (Path(root)/SWEEP1_INDEX_PATH).resolve()
            or _sha256(Path(index_path)) != SWEEP1_INDEX_SHA):
        require_d8_confirmation()
    index = json.loads(Path(index_path).read_text())
    decision = evidence_classification(index_path, Path(root), Path(classification)) if classification else None
    specs = sweep_sources(index, Path(index_path), Path(root), source_names, decision)
    source = index.get("noise_source")
    if source is not None:
        if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
            raise ValueError("sweep index has malformed noise source")
        rel = Path(source["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("sweep noise source must be repository-relative")
        pinned = (Path(root) / rel).resolve()
        refuse_sealed(Path(root) / rel, pinned)
        if not pinned.is_relative_to(Path(root).resolve()) or not pinned.is_file():
            raise ValueError("sweep noise source missing or outside paper root")
        if _sha256(pinned) != source["sha256"]:
            raise ValueError("sweep noise source sha256 mismatch")
        if e1_summary is not None and Path(e1_summary).resolve() != pinned:
            raise ValueError("explicit E1 summary differs from pinned sweep noise source")
        e1_summary = pinned
    noise = noise_table() if e1_summary is None else noise_table(e1_summary)
    return {"index_path": index_path, "root": root, "index": index, "decision": decision, "specs": specs,
            "source": source, "e1_summary": e1_summary, "noise": noise}


def build_from_sweep(sweep: Path | str, out: Path, *, paper_root: Path | str | None = None,
                     e1_summary: Path | str | None = None, source_names: dict | None = None,
                     classification: Path | str | None = None) -> dict:
    """A completed C3 label sweep -> the C3 proposal table (same files and row format as ``build``)."""
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(sweep,out,paper_root,e1_summary,classification)
    inputs = sweep_replay_inputs(sweep, paper_root=paper_root, e1_summary=e1_summary, source_names=source_names,
                                 classification=classification)
    index_path, index, decision, specs = inputs["index_path"], inputs["index"], inputs["decision"], inputs["specs"]
    source, e1_summary, noise = inputs["source"], inputs["e1_summary"], inputs["noise"]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=decision is None)
    rows, configs, checks = _replay_sources(specs, noise, strict_start_files=True)
    if not checks:
        raise ValueError(f"{index_path}: no root ledgers")
    head = {"label": decision['label'] if decision else index.get("label"), "ai_assisted": "AI-assisted (Claude)", "commit": git_head(),
            **({'classification': {'path': str(Path(classification).resolve()), 'sha256': _sha256(Path(classification)), 'native_index_label': index.get('label')}} if decision else {}),
            "sources": {k: v[0] for k, v in specs.items()},
            "sweep_index": {"path": str(index_path), "sha256": _sha256(index_path), "label": index.get("label"),
                            "nodes": index.get("nodes"), "excluded_nodes": index.get("excluded_nodes"),
                            "instances": index.get("instances"), "runs": index.get("runs"),
                            "harness_commit": index.get("harness_commit"), "audit": index.get("audit")},
            "e1_summary": source["path"] if source is not None else (str(e1_summary) if e1_summary is not None else E1_SUMMARY),
            **({"noise_source": source} if source is not None else {})}
    return _write_table(out, rows, configs, checks, head, noise)


def row_of(p: Proposal, noise: dict) -> dict:
    key = p.edit.get("symbol")
    kind = "structural" if key == "model_type" else "local"
    sigma = noise[p.node]["sigma_structural" if kind == "structural" else "sigma_local"]
    return {"proposal_id": p.proposal_id, "instance": p.instance, "instance_seed": p.instance_seed,
            "node": p.node, "source": p.source, "memory_mode": p.memory_mode, "budget_index": p.budget_index,
            "edit": p.edit, "edit_kind": kind, "sigma_node": noise[p.node]["sigma_node"], "sigma_cmp": sigma,
            "features": p.features, **p.outcome,
            "candidate_hash": p.candidate_hash, "incumbent_hash": p.incumbent_hash}


def load_table(table_dir: Path) -> list[dict]:
    from r1.c3.analysis_guard import guard_table
    guard_table(table_dir, Path(table_dir) / 'proposals.jsonl')
    return [json.loads(x) for x in (Path(table_dir) / "proposals.jsonl").read_text().splitlines() if x.strip()]


def di_candidates(rows: list[dict]) -> list[dict]:
    """Locate the DI-changed candidates and check them against the E2 snapshots."""
    by_id = {r["proposal_id"]: r for r in rows}
    found = []
    for source, pts in DI_CHANGED.items():
        sdir = REPO / SOURCES[source]["dir"]
        for inst, b, direction in pts:
            pid = f"{source}:{inst}:t{b:03d}"
            r = by_id[pid]
            want = "discarded" if direction == "promotion" else "kept"
            if r["decision"] != want:
                raise ValueError(f"{pid}: root decision {r['decision']} inconsistent with {direction}")
            snap = sdir / "provenance" / "snapshots" / inst / f"E2_b{b:03d}"
            refuse_sealed(snap, snap / 'manifest.json')
            man = json.loads((snap / "manifest.json").read_text())
            for p in man['editable_paths']:
                refuse_sealed(snap / 'incumbent' / p)
            snap_inc = configuration(normalise_files({p: (snap / "incumbent" / p).read_text() for p in man["editable_paths"]}))
            found.append({**r, "di_direction": direction, "snapshot_incumbent_config": snap_inc})
    return found


def plan(table_dir: Path, quota: dict, include_di: bool, seed: int = PLAN_SEED) -> list[dict]:
    rows = load_table(table_dir)
    refuse_sealed(Path(table_dir) / 'configs.json')
    configs = json.loads((Path(table_dir) / "configs.json").read_text())
    rng = np.random.default_rng(seed)
    chosen: dict[str, dict] = {}
    for (source, node), n in quota.items():
        pool = sorted([r for r in rows if r["source"] == source and r["node"] == node and not r.get("rule_skip", r["inert"])],
                      key=lambda r: r["proposal_id"])
        idx = rng.permutation(len(pool))[:n]
        for i in sorted(idx):
            r = pool[i]
            chosen[r["proposal_id"]] = {"proposal_id": r["proposal_id"], "node": node, "reason": "random",
                                        "candidate_hash": r["candidate_hash"], "incumbent_hash": r["incumbent_hash"]}
    if include_di:
        for r in di_candidates(rows):
            inc_cfg = configuration(configs[r["incumbent_hash"]]["files"])
            if inc_cfg != r["snapshot_incumbent_config"]:
                raise ValueError(f"{r['proposal_id']}: replayed incumbent differs from E2 snapshot")
            if r["proposal_id"] in chosen:
                chosen[r["proposal_id"]]["reason"] = "random+di"
            else:
                chosen[r["proposal_id"]] = {"proposal_id": r["proposal_id"], "node": r["node"], "reason": "di",
                                            "candidate_hash": r["candidate_hash"], "incumbent_hash": r["incumbent_hash"]}
            chosen[r["proposal_id"]]["di_direction"] = r["di_direction"]
            chosen[r["proposal_id"]]["di_inert"] = r["inert"]
            chosen[r["proposal_id"]]["di_duplicate"] = r.get("duplicate")
    return list(chosen.values())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--sources", nargs="+", default=list(SOURCES))
    w = sub.add_parser("build-sweep", help="table from a completed C3 label sweep (index file or batch directory)")
    w.add_argument("--index", required=True, help="C3_sweep_index_<UTC>.json or the sweep batch directory")
    w.add_argument("--out", required=True)
    w.add_argument("--paper-root", default=None, help="paper checkout the index paths are relative to")
    w.add_argument("--e1-summary", default=None, help=f"noise source (default {E1_SUMMARY})")
    w.add_argument("--source-name", nargs="*", default=[], help="MODE=NAME source names (default c3_<UTC>_<mode>)")
    w.add_argument("--classification", default=None, help="author classification sidecar (validated before evidence use)")
    p = sub.add_parser("plan")
    p.add_argument("--table", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--quota", nargs="*", default=None, help="source:node:n entries")
    p.add_argument("--di", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "build":
        meta = build(Path(args.out), tuple(args.sources))
        print(json.dumps({"n_proposals": meta["n_proposals"], "checks": meta["replay_checks_total"]}))
    elif args.cmd == "build-sweep":
        names = dict(item.split("=", 1) for item in args.source_name)
        meta = build_from_sweep(Path(args.index), Path(args.out), paper_root=args.paper_root,
                                e1_summary=args.e1_summary, source_names=names, classification=args.classification)
        print(json.dumps({"n_proposals": meta["n_proposals"], "sources": list(meta["sources"]),
                          "checks": meta["replay_checks_total"]}))
    else:
        quota = DEFAULT_QUOTA if args.quota is None else {
            (q.split(":")[0], q.split(":")[1]): int(q.split(":")[2]) for q in args.quota}
        rows = plan(Path(args.table), quota, args.di)
        out = Path(args.out) if args.out else Path(args.table) / "plan.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(json.dumps({"planned": len(rows), "di": sum("di" in r["reason"] for r in rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
