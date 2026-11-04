"""C3 B.1 environment replay driver (ENGINEERING_ONLY). AI-assisted (Claude), M3 of MAC_LOCAL_RUNBOOK_20261104.

Implements the predeclared protocol of
``docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`` ("Predeclared
replay protocol"); reviewed in ``docs/r1/reviews/C3_ENV_REPLAY_DRAFT_REVIEW_20261028.md``
and scoped in ``docs/r1/reviews/C3_B2_REPLAY_LLM_SCOPE_REVIEW_20261031.md``.

* **Cases (fixed without metric values).** For each of the eight authorized nodes, in
  the sweep index's order: the ``append_only_summary`` campaign with the numerically
  smallest instance seed, budget indices 1 (the first recorded kept incumbent) and 2
  (the next proposal): 16 cases. A missing or unsuccessful trial is a STOP; no later
  trial is ever substituted.
* **Configurations** are recovered from the preserved root record's start files and
  the logged structured edits; each recovered patch must reproduce the ledger's
  ``patch_hash`` and the archived ``patch.diff``.
* **Seeds.** Each case reuses its campaign's recorded instance seed as
  ``train_seed = split_seed`` (the ``ccb4712`` collector binding, checked against
  that commit's source). Seeds 7001-7010 are a STOP. Direct per-process seed identity
  is NOT CHECKABLE (all ledger ``training_seed`` fields are null) and is reported so.
* **No manager model.** The driver imports only the harness worker, node registry and
  ``ManagerProposal`` (a no-edit proposal); an LLM client module in ``sys.modules`` is
  a STOP. No GPU is requested.
* **Pass tolerance is exactly zero, declared before execution**: the replayed metric
  token, as emitted in the worker log, must equal the recorded token in the archived
  original ``run.log``. Nothing is re-rounded. Any mismatch, missing/non-finite metric,
  unexpected environment, unverified input or interruption is a STOP; completed and
  partial artifacts are kept and nothing is retried.

``--dry-run`` performs every source check, the case selection and the configuration
recovery, and writes the plan; it runs no worker and skips the host-only environment
checks (reported as ``DEFERRED_TO_HOST``). It never needs the batch or the venv.

The run itself is the operator's (R1-HANDOVER-04NOV), on deepthought CPUs, only after
the author's replay authorization note (packet e1, R1-B2-REPLAY-GO).
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.metadata as import_metadata
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

LABEL = 'ENGINEERING_ONLY'
SCHEMA = 'r1.c3_env_replay/1'
DRAFT = 'docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md'
TOLERANCE = 0  # declared before execution; never changed after results are seen
MEMORY_MODE = 'append_only_summary'
BUDGET_INDICES = (1, 2)
SELECTION_RULE = ('per authorized node: the append_only_summary campaign with the numerically smallest '
                  'instance seed; budget indices 1 (first recorded kept incumbent) and 2 (next proposal); '
                  'no metric value is used; a missing or unsuccessful trial is a STOP')

# Sources: R1-SWEEP1-CLASSIFY, docs/r1/authorizations/C3_B1_CORPUS_FREEZE_20261031.md.
INDEX = 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json'
INDEX_SHA256 = '812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab'
SIDECAR = 'results/r1/evidence/C3_sweep_classification_20261028.json'
SIDECAR_SHA256 = 'bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc'
CORPUS_TREES = {  # Git trees of the frozen B.1 corpus (C3_B1_CORPUS_FREEZE_20261031.md)
    'results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z': '6b1c0c6154a604c391f8b7684a2d4ce34ccddd1a',
    'results/r1/evidence/C3_sweep_none_20261027T224356Z': '468e57ce4871d0d33f08932c6fe13c2cb0d431ce',
}
COLLECTOR_COMMIT = 'ccb47128aad82e331f79df4a893dbc1ee7e42f51'  # paper pin of the sweep (R1-SWEEP1-CLASSIFY)
COLLECTOR_BINDINGS = ('return 100 + 10 * k + (sum(map(ord, node)) % 7)',
                      'LocalWorker(node_root=node_dir, artifact_dir=root / "art", train_seed=seed, split_seed=seed)')
COLLECTOR_THREADS = {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}  # ccb4712 service_env
NO_GPU = {'CUDA_VISIBLE_DEVICES': ''}  # CPU-only replay; sklearn nodes do not read it
PILOT_DATA_CACHE = 'experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache'  # ccb4712 e1b_collect
FORBIDDEN_SEEDS = range(7001, 7011)
CEPH_RESERVE_FILES = 200  # replay writes about 20 files (plan, cases, 16 raw logs, summary); 10x margin

# Host pins: replay draft, environment investigation and DT_PHASE2_RECHECK_20261026 (all 28 Oct or earlier).
HOST = 'deepthought'
HARNESS_COMMIT = '6adf3859de66c4814fcf376eed59880fbd8eeaf7'
BATCH = '/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw'
SHARED_PYTHON = '/ceph/dwong/r1_prepare_20261025/venv/bin/python'
FREEZE = '/ceph/dwong/r1_prepare_20261025/freeze_with_lightgbm.txt'
FREEZE_SHA256 = 'c760b28f2d03cfd31ae491b13b13ec6a348caee603b051349d9f85f9af282406'
UV_LOCK_SHA256 = 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090'
PYTHON_VERSION = (3, 13, 15)
VERSIONS = {'scikit-learn': '1.8.0', 'numpy': '2.4.4', 'pandas': '3.0.3', 'scipy': '1.17.1'}
ALLOWED_ADDITION = {'narwhals': '2.27.1'}
LAUNCH_UTC = datetime(2026, 10, 27, 15, 48, tzinfo=timezone.utc)
OBSERVED_PACKAGE_LIST_SHA256 = 'c09242ac13970394a660452fb1b92dde39edcf390022c40a19327e67e725315f'  # 28 Oct, format unrecorded
LLM_MODULES = ('openai', 'langchain', 'langchain_core', 'langchain_openai', 'langgraph', 'ollama', 'llama_cpp',
               'autoresearch.manager.langgraph_manager', 'autoresearch.manager.llm')
METRIC_LINE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)(?::\s+|=)([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$',
                         re.MULTILINE)  # the pinned harness's _parse_metrics_from_log pattern


class Stop(RuntimeError):
    """A protocol STOP: report, retain everything, never retry automatically."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes())


def metric_name(node: str) -> str:
    return 'val_score' if node in ('digits_mlp', 'tabular_mlp') else 'val_auc'


def emitted_metric(log_text: str, name: str) -> str | None:
    """The metric token exactly as the worker emitted it (last matching line), or None."""
    tokens = [v for k, v in METRIC_LINE.findall(log_text) if k.lower() == name]
    return tokens[-1] if tokens else None


def no_llm_modules() -> None:
    loaded = sorted(m for m in sys.modules if any(m == p or m.startswith(p + '.') for p in LLM_MODULES))
    if loaded:
        raise Stop(f'STOP: LLM client modules loaded in the replay process: {loaded}')


# ---------------------------------------------------------------------------- source corpus

def verify_corpus(paper: Path, *, require_git: bool = True) -> dict:
    """Bind the replay to the SHA256-bound index and sidecar and the frozen corpus trees."""
    paper = Path(paper)
    for rel, expected in ((INDEX, INDEX_SHA256), (SIDECAR, SIDECAR_SHA256)):
        path = paper / rel
        if path.is_symlink() or not path.is_file() or file_sha256(path) != expected:
            raise Stop(f'STOP: unverified input {rel}')
    index = json.loads((paper / INDEX).read_text())
    sidecar = json.loads((paper / SIDECAR).read_text())
    if sidecar.get('decision_id') != 'R1-SWEEP1-CLASSIFY' or sidecar.get('label') != 'EVIDENCE' or \
            sidecar.get('index', {}).get('sha256') != INDEX_SHA256:
        raise Stop('STOP: classification sidecar does not bind the sweep index')
    sweeps = {}
    for entry in sidecar['sweeps']:
        manifest = paper / entry['new_dir'] / 'manifest.json'
        if file_sha256(manifest) != entry['manifest_sha256']:
            raise Stop(f'STOP: manifest hash mismatch for {entry["memory_mode"]}')
        sweeps[entry['memory_mode']] = entry
    trees = {}
    if require_git:
        def git(*args):
            return subprocess.check_output(['git', '-C', str(paper), *args], text=True, timeout=60).strip()
        try:
            if git('status', '--porcelain', '--untracked-files=all', '--', INDEX, SIDECAR, *CORPUS_TREES):
                raise Stop('STOP: frozen corpus has uncommitted or untracked changes')
            for rel, tree in CORPUS_TREES.items():
                trees[rel] = git('rev-parse', f'HEAD:{rel}')
                if trees[rel] != tree:
                    raise Stop(f'STOP: frozen corpus tree differs: {rel}')
            from r1.c3.dataset import _verify_original_blobs
            _verify_original_blobs(paper.resolve(), index, sidecar['sweeps'])
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            raise Stop(f'STOP: corpus provenance not verifiable: {exc}') from exc
    return {'index': {'path': INDEX, 'sha256': INDEX_SHA256}, 'sidecar': {'path': SIDECAR, 'sha256': SIDECAR_SHA256},
            'corpus_trees': trees or 'NOT CHECKED (no git)', 'original_blobs_verified': bool(require_git),
            'index_doc': index, 'sweeps': sweeps}


def verify_collector_binding(paper: Path) -> dict:
    """The frozen collector's seed rule and LocalWorker binding, read from its commit."""
    try:
        source = subprocess.check_output(['git', '-C', str(paper), 'show',
                                          f'{COLLECTOR_COMMIT}:r1/headroom/e1b_collect.py'], text=True, timeout=60)
    except (subprocess.SubprocessError, OSError) as exc:
        raise Stop(f'STOP: collector source at {COLLECTOR_COMMIT} unavailable') from exc
    missing = [b for b in COLLECTOR_BINDINGS if b not in source]
    if missing:
        raise Stop(f'STOP: collector seed binding not found at {COLLECTOR_COMMIT}: {missing}')
    return {'commit': COLLECTOR_COMMIT, 'path': 'r1/headroom/e1b_collect.py', 'blob_sha256': sha256(source.encode()),
            'bindings': list(COLLECTOR_BINDINGS)}


class Archive:
    """The preserved local-work archive of one sweep, verified against its manifest."""

    def __init__(self, sweep_dir: Path):
        manifest = json.loads((sweep_dir / 'manifest.json').read_text())
        record = manifest.get('local_work_archive') or {}
        self.path, self.index_path = sweep_dir / record.get('path', ''), sweep_dir / record.get('index', '')
        if not self.path.is_file() or file_sha256(self.path) != record.get('sha256') or \
                not self.index_path.is_file() or file_sha256(self.index_path) != record.get('index_sha256'):
            raise Stop(f'STOP: local work archive or its index differs from the manifest in {sweep_dir}')
        index = json.loads(self.index_path.read_text())
        self.refs = {r['original_ref']: r for r in index['references']}
        self.record = {'path': str(self.path), 'sha256': record['sha256'], 'index_sha256': record['index_sha256']}

    def member(self, original_ref: str) -> tuple[bytes, dict]:
        ref = self.refs.get(original_ref)
        if ref is None:
            raise Stop(f'STOP: no archived member for {original_ref}')
        with tarfile.open(self.path) as tar:
            handle = tar.extractfile(ref['member'])
            data = handle.read() if handle else None
        if data is None or sha256(data) != ref['sha256']:
            raise Stop(f'STOP: archived member differs from its index: {ref["member"]}')
        return data, ref


def node_spec(harness: Path, node: str) -> dict:
    """The pinned NodeSpec file (JSON content) read from the harness commit, not the working tree."""
    try:
        raw = subprocess.check_output(['git', '-C', str(harness), 'show', f'{HARNESS_COMMIT}:configs/nodes/{node}.yaml'],
                                      timeout=60)
        return json.loads(raw)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise Stop(f'STOP: pinned NodeSpec for {node} unavailable at {HARNESS_COMMIT}') from exc


def select_cases(paper: Path, corpus: dict, harness: Path | None) -> list[dict]:
    """The 16 fixed cases with recovered configurations and their recorded values."""
    from r1.c3.features import apply_edit, normalise_files, read_jsonl, files_hash
    index = corpus['index_doc']
    entry = corpus['sweeps'][MEMORY_MODE]
    sweep_dir = paper / entry['new_dir']
    indexed = next(s for s in index['sweeps'] if s['memory_mode'] == MEMORY_MODE)
    ledgers = sweep_dir / Path(indexed['ledgers']).relative_to(indexed['out'])
    archive = Archive(sweep_dir)
    cases = []
    for node in index['nodes']:
        seeds = sorted(int(p.name.rsplit('__s', 1)[1]) for p in ledgers.glob(f'{node}__s*') if p.is_dir())
        if len(seeds) != index['instances']:
            raise Stop(f'STOP: {node}: {len(seeds)} campaigns, expected {index["instances"]}')
        seed = seeds[0]
        campaign = f'{node}__s{seed}'
        expected_seeds = {100 + 10 * k + (sum(map(ord, node)) % 7) for k in range(index['instances'])}
        root_path = sweep_dir / 'roots' / f'{campaign}.json'
        root = json.loads(root_path.read_text())
        if root.get('instance') != campaign or root.get('node') != node or root.get('seed') != seed or \
                seed not in expected_seeds or seed in FORBIDDEN_SEEDS:
            raise Stop(f'STOP: instance seed of {campaign} not established by the root record and collector rule')
        ledger_path = ledgers / campaign / 'root_trials.jsonl'
        events_path = ledgers / campaign / 'root_events.jsonl'
        rows = {int(r['budget_index']): r for r in read_jsonl(ledger_path)}
        events = read_jsonl(events_path)
        files = normalise_files(root['start_files'])
        name = metric_name(node)
        spec = node_spec(harness, node) if harness is not None else None
        if spec is not None and (spec.get('metric_name') != name or set(spec['editable_paths']) != set(files)):
            raise Stop(f'STOP: pinned NodeSpec of {node} differs from the recorded metric or editable files')
        recorded_before = None
        for b in BUDGET_INDICES:
            row = rows.get(b)
            if row is None or row.get('execution_status') != 'success' or row.get('validity_status') != 'valid' or \
                    row.get('campaign_id') != campaign or row.get('memory_mode') != MEMORY_MODE:
                raise Stop(f'STOP: {campaign} trial {b} missing or unsuccessful; no later trial is selected')
            value = (row.get('parsed_metrics') or {}).get(name)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise Stop(f'STOP: {campaign} trial {b} lacks a finite {name}')
            if row.get('training_seed') not in (None, seed):
                raise Stop(f'STOP: {campaign} trial {b} records a different training seed')
            trial_events = {e['event_type'] for e in events if e.get('trial_id') == row['trial_id']}
            if any('verify' in t for t in trial_events):
                raise Stop(f'STOP: {campaign} trial {b} has verify events; its seed derivation differs')
            edit = ((row.get('extra') or {}).get('manager') or {}).get('structured_edit')
            if not edit:
                raise Stop(f'STOP: {campaign} trial {b} has no structured edit to recover its configuration')
            candidate = apply_edit(files, edit)
            path = edit['path']
            diff = ''.join(difflib.unified_diff(files[path].splitlines(keepends=True),
                                                candidate[path].splitlines(keepends=True),
                                                fromfile=f'a/{Path(path).name}', tofile=f'b/{Path(path).name}'))
            patch, patch_ref = archive.member(row['patch_ref'])
            if sha256(diff.encode()) != row.get('patch_hash') or patch != diff.encode():
                raise Stop(f'STOP: recovered configuration of {campaign} trial {b} differs from the recorded patch')
            log, log_ref = archive.member(row['raw_log_ref'])
            token = emitted_metric(log.decode('utf-8', 'replace'), name)
            if token is None or float(token) != float(value):
                raise Stop(f'STOP: archived log of {campaign} trial {b} does not carry the recorded {name}')
            if b == 1 and row.get('decision') != 'kept':
                raise Stop(f'STOP: {campaign} trial 1 is not a recorded kept incumbent')
            if b == 2 and row.get('current_best_before') != recorded_before:
                raise Stop(f'STOP: {campaign} trial 2 does not continue from the trial-1 incumbent')
            cases.append({
                'case_id': f'{campaign}:t{b:03d}', 'node': node, 'memory_mode': MEMORY_MODE, 'campaign_id': campaign,
                'budget_index': b, 'trial_id': row['trial_id'], 'decision': row['decision'],
                'source_commit': indexed.get('commit'), 'original_dir': indexed['out'], 'relocated_dir': entry['new_dir'],
                'ledger': {'path': str(ledger_path.relative_to(paper)), 'sha256': file_sha256(ledger_path)},
                'events': {'path': str(events_path.relative_to(paper)), 'sha256': file_sha256(events_path)},
                'root_record': {'path': str(root_path.relative_to(paper)), 'sha256': file_sha256(root_path)},
                'archive': {**archive.record, 'patch_member': patch_ref['member'], 'patch_sha256': patch_ref['sha256'],
                            'log_member': log_ref['member'], 'log_sha256': log_ref['sha256']},
                'structured_edit': edit, 'patch_hash': row['patch_hash'],
                'incumbent_files_hash': files_hash(files), 'configuration_hash': files_hash(candidate),
                'configuration_file_sha256': {p: sha256(t.encode()) for p, t in sorted(candidate.items())},
                'files': candidate,
                'instance_seed': seed, 'train_seed': seed, 'split_seed': seed,
                'seed_provenance': {'root_record_seed': seed, 'collector_rule': 'instance seed = 100 + 10k + sum(ord(node)) % 7',
                                    'ledger_training_seed': row.get('training_seed'),
                                    'per_process_identity': 'NOT CHECKABLE (ledger training_seed null; no process snapshot)'},
                'worker_command': spec['run_command'] if spec else 'NOT CHECKED (no harness)',
                'metric_key': name, 'recorded_value': value, 'recorded_token': token,
                'recorded_precision': len(token.split('.', 1)[1]) if '.' in token and 'e' not in token.lower() else None,
            })
            recorded_before = value
            if row['decision'] == 'kept':
                files = candidate
    return cases


# ---------------------------------------------------------------------------- environment (host only)

PROBE = r'''import importlib.metadata as m, json, os, re, sys
packages, newest = {}, 0.0
for d in m.distributions():
    name = re.sub(r"[-_.]+", "-", (d.metadata.get("Name") or "")).lower()
    if not name or name in packages: raise SystemExit("missing or duplicate distribution " + name)
    packages[name] = d.version
    base = getattr(d, "_path", None)
    if base is not None and os.path.isdir(base):
        newest = max([newest, os.stat(base).st_mtime] + [os.stat(os.path.join(base, f)).st_mtime for f in os.listdir(base)])
print(json.dumps({"executable": sys.executable, "realpath": os.path.realpath(sys.executable), "prefix": sys.prefix,
 "base_prefix": sys.base_prefix, "version": list(sys.version_info[:3]), "build": sys.version,
 "versions": {n: m.version(n) for n in ("scikit-learn", "numpy", "pandas", "scipy")},
 "packages": packages, "newest_dist_info_mtime": newest}))'''


def probe(python: str) -> dict:
    try:
        out = subprocess.check_output([python, '-B', '-c', PROBE], text=True, timeout=120,
                                      env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        return json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise Stop(f'STOP: interpreter probe failed: {python}: {exc}') from exc


def canonical_packages(packages: dict) -> tuple[str, str]:
    text = ''.join(f'{n}=={v}\n' for n, v in sorted(packages.items()))
    return text, sha256(text.encode())


def parse_freeze(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '==' not in line:
            raise Stop(f'STOP: freeze line not pinned: {line!r}')
        name, version = line.split('==', 1)
        out[re.sub(r'[-_.]+', '-', name).lower()] = version.strip()
    return out


def wrapper_target(path: Path) -> str:
    text = path.read_text()
    m = re.fullmatch(r"#!/bin/sh\nexec (\S+) \"\$@\"\n", text)
    if not m:
        raise Stop(f'STOP: {path} is not the recorded exec wrapper')
    return m.group(1).strip("'")


def check_environment(batch: Path, harness: Path) -> dict:
    """Numerical and orchestration uses of the actual batch venv, checked separately (draft, first bullet)."""
    wrappers = {n: batch / 'autoresearch_harness/.venv/bin' / n for n in ('python', 'python3')}
    targets = {n: wrapper_target(p) for n, p in wrappers.items()}
    if set(targets.values()) != {SHARED_PYTHON}:
        raise Stop(f'STOP: batch wrappers do not exec the recorded shared venv: {targets}')
    observed = {n: probe(str(p)) for n, p in wrappers.items()}
    first = observed['python']
    if any(o['realpath'] != first['realpath'] or o['prefix'] != first['prefix'] or o['packages'] != first['packages']
           for o in observed.values()):
        raise Stop('STOP: python and python3 wrappers resolve to different environments')
    if first['prefix'] == first['base_prefix']:
        raise Stop('STOP: batch interpreter is not a virtual environment')
    if tuple(first['version']) != PYTHON_VERSION or first['versions'] != VERSIONS:
        raise Stop(f'STOP: Python or library versions differ: {first["version"]} {first["versions"]}')
    lock = harness / 'uv.lock'
    if file_sha256(lock) != UV_LOCK_SHA256:
        raise Stop('STOP: batch harness uv.lock differs from the recorded lock')
    newest = datetime.fromtimestamp(first['newest_dist_info_mtime'], tz=timezone.utc)
    if newest >= LAUNCH_UTC:
        raise Stop(f'STOP: dist-info modified at or after launch: {newest.isoformat()}')
    freeze = Path(FREEZE)
    if file_sha256(freeze) != FREEZE_SHA256:
        raise Stop('STOP: 25 October freeze file differs')
    frozen = parse_freeze(freeze.read_text())
    current = first['packages']
    added = {k: v for k, v in current.items() if k not in frozen}
    removed = sorted(k for k in frozen if k not in current)
    changed = {k: (frozen[k], current[k]) for k in frozen if k in current and frozen[k] != current[k]}
    if added != ALLOWED_ADDITION or removed or changed:
        raise Stop(f'STOP: package list differs from the 25 Oct freeze beyond narwhals: '
                   f'added={added} removed={removed} changed={changed}')
    worker_path = os.pathsep.join([str(wrappers['python3'].parent), os.environ.get('PATH', '')])
    if shutil.which('python3', path=worker_path) != str(wrappers['python3']):
        raise Stop('STOP: worker python3 on the replay PATH is not the batch wrapper')
    if Path(sys.prefix).resolve() != Path(first['prefix']).resolve():
        raise Stop('STOP: the driver does not run in the batch venv (orchestration use)')
    text, digest = canonical_packages(current)
    return {'host': platform.node(), 'wrappers': {n: str(p) for n, p in wrappers.items()}, 'wrapper_target': SHARED_PYTHON,
            'interpreter': first['realpath'], 'prefix': first['prefix'], 'build': first['build'],
            'versions': first['versions'], 'uv_lock_sha256': UV_LOCK_SHA256,
            'newest_dist_info_mtime_utc': newest.isoformat(), 'freeze': {'path': FREEZE, 'sha256': FREEZE_SHA256},
            'difference_from_freeze': {'added': added, 'removed': removed, 'changed': changed},
            'current_package_list': text, 'current_package_list_sha256': digest,
            'package_list_sha256_28oct_observation': OBSERVED_PACKAGE_LIST_SHA256,
            'observation_note': 'current-state observation, not a launch-bound snapshot', 'worker_path': worker_path}


def check_harness(harness: Path, nodes: list[str]) -> dict:
    def git(*args):
        return subprocess.check_output(['git', '-C', str(harness), *args], text=True, timeout=60).strip()
    try:
        head = git('rev-parse', 'HEAD')
        dirty = git('status', '--porcelain', '--untracked-files=no')
    except (subprocess.SubprocessError, OSError) as exc:
        raise Stop('STOP: harness checkout unreadable') from exc
    if head != HARNESS_COMMIT or dirty:
        raise Stop('STOP: harness is not the clean pinned commit')
    caches = {}
    for node in nodes:
        if not node.startswith('openml_'):
            continue
        cache = harness / 'nodes' / node / 'data_cache'
        source = cache if cache.exists() else harness / PILOT_DATA_CACHE.format(node=node)
        if not has_cache_files(source):
            raise Stop(f'STOP: {node} has no local OpenML data cache; the replay would download')
        caches[node] = tree_digest(source)
    return {'harness': str(harness), 'commit': head, 'tracked_clean': True, 'data_caches_sha256': caches}


def has_cache_files(root: Path) -> bool:
    return Path(root).is_dir() and any(p.is_file() and p.name not in ('.gitignore', '.gitkeep')
                                       for p in Path(root).rglob('*'))


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    if root.exists():
        for p in sorted(root.rglob('*')):
            if p.is_file():
                h.update(str(p.relative_to(root)).encode() + b'\0' + p.read_bytes() + b'\0')
    return h.hexdigest()


def check_resources(out: Path, scratch: Path, min_free_bytes: int) -> dict:
    from r1.c3.audit import _local_scratch_mount
    if out.exists() or scratch.exists():
        raise Stop('STOP: output and scratch must be new')
    if scratch.parent.resolve() != Path('/tmp').resolve() or not scratch.name.startswith('r1_c3_env_replay_'):
        raise Stop('STOP: scratch must be a new r1_c3_env_replay_* directory directly under /tmp')
    try:
        mount = _local_scratch_mount(scratch.parent)
    except (ValueError, subprocess.SubprocessError, OSError) as exc:
        raise Stop(f'STOP: scratch is not on a verified local disk: {exc}') from exc
    free = {str(p): shutil.disk_usage(p).free for p in (scratch.parent, out.parent)}
    if min_free_bytes <= 0 or min(free.values()) < min_free_bytes:
        raise Stop('STOP: disk headroom below the operator estimate')
    ceph = None
    if out.resolve().is_relative_to('/ceph'):
        # Authorization floor (c3_sweep1_20261027.md / runbook §2): 50 GiB free; plus file-count headroom.
        def attr(name):
            return int(subprocess.check_output(['getfattr', '-n', name, '--only-values', '/ceph/dwong'],
                                               text=True, timeout=20).strip())
        try:
            used, maximum = attr('ceph.dir.rfiles'), attr('ceph.quota.max_files')
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise Stop('STOP: Ceph file-count headroom not measurable') from exc
        if shutil.disk_usage('/ceph/dwong').free < 50 * 1024**3 or maximum <= 0 or maximum - used < CEPH_RESERVE_FILES:
            raise Stop('STOP: Ceph free space or file-count headroom below the floor')
        ceph = {'files_used': used, 'files_max': maximum, 'reserve_files': CEPH_RESERVE_FILES}
    return {'scratch': str(scratch), 'scratch_mount': mount, 'free_bytes': free, 'min_free_bytes': min_free_bytes,
            'ceph': ceph}


# ---------------------------------------------------------------------------- execution

def execute_case(case: dict, node_source: Path, scratch: Path, env_overrides: dict) -> dict:
    """Run one recovered configuration once at its recorded seed through the pinned LocalWorker."""
    from r1.harness import import_harness
    harness = import_harness()
    from autoresearch.manager.base import ManagerProposal
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker
    no_llm_modules()
    spec = load_registered_node(case['node'], repo_root=node_source)
    work = Path(tempfile.mkdtemp(prefix=f"case_{case['node']}_", dir=scratch))
    node_dir = work / 'node'
    shutil.copytree(Path(node_source) / 'nodes' / case['node'], node_dir,
                    ignore=shutil.ignore_patterns('__pycache__', '.autoresearch_artifacts'))
    if case['node'].startswith('openml_'):
        if not (node_dir / 'data_cache').exists():  # exactly the ccb4712 collector's _node_copy rule
            cache = Path(node_source) / PILOT_DATA_CACHE.format(node=case['node'])
            if cache.exists():
                shutil.copytree(cache, node_dir / 'data_cache')
        if not has_cache_files(node_dir / 'data_cache'):
            raise Stop(f"STOP: {case['node']} has no local OpenML data cache; the replay would download")
    before = tree_digest(node_dir / 'data_cache')
    for rel, text in case['files'].items():
        if rel not in spec.editable_paths:
            raise Stop(f'STOP: {rel} is not editable on {case["node"]}')
        (node_dir / rel).write_text(text, encoding='utf-8')
    worker = LocalWorker(node_root=node_dir, artifact_dir=work / 'art',
                         train_seed=case['train_seed'], split_seed=case['split_seed'])
    noedit = ManagerProposal(manager_mode='c3_env_replay', proposal_summary='replay', proposal_rationale='',
                             target_files=spec.editable_paths, objective='Environment replay; no change.')
    saved = {k: os.environ.get(k) for k in env_overrides}
    os.environ.update(env_overrides)
    try:
        t0 = time.perf_counter()
        result = worker.run_trial(noedit, spec, case['budget_index'])
        wall = time.perf_counter() - t0
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    no_llm_modules()
    log = Path(result.raw_log_ref).read_text(encoding='utf-8', errors='replace') if result.raw_log_ref else ''
    token = emitted_metric(log, case['metric_key'])
    return {'case_id': case['case_id'], 'success': bool(result.success), 'changed_files': list(result.changed_files),
            'failure': result.failure_message, 'replay_token': token, 'recorded_token': case['recorded_token'],
            'replay_value': result.parsed_metrics.get(case['metric_key']) if result.success else None,
            'recorded_value': case['recorded_value'], 'wall_seconds': round(wall, 3),
            'data_cache_unchanged': tree_digest(node_dir / 'data_cache') == before,
            'log_text': log, 'work_dir': str(work), 'harness_code_root': str(harness)}


def case_passes(r: dict) -> bool:
    return (r['success'] and not r['changed_files'] and r['data_cache_unchanged'] and r['replay_token'] is not None
            and math.isfinite(float(r['replay_token'])) and r['replay_token'] == r['recorded_token']
            and float(r['replay_token']) == float(r['recorded_value']))


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def run(paper: Path, out: Path, *, dry_run: bool, harness: Path | None = None, batch: Path | None = None,
        scratch: Path | None = None, min_free_bytes: int = 0, execute=execute_case) -> dict:
    sys.dont_write_bytecode = True
    paper = Path(paper).resolve()
    out = Path(out)
    if out.exists():
        raise Stop('STOP: output location must be new')
    if any(out.resolve().is_relative_to((paper / rel).resolve()) for rel in CORPUS_TREES) or \
            (batch is not None and out.resolve().is_relative_to(Path(batch).resolve())):
        raise Stop('STOP: output inside the preserved batch or corpus')
    no_llm_modules()
    corpus = verify_corpus(paper)
    collector = verify_collector_binding(paper)
    cases = select_cases(paper, corpus, harness)
    if len(cases) != 2 * len(corpus['index_doc']['nodes']) or len(cases) != 16:
        raise Stop(f'STOP: {len(cases)} cases, expected 16')
    plan = {'schema': SCHEMA, 'label': 'DRYRUN' if dry_run else LABEL, 'ai_assisted': 'AI-assisted (Claude)',
            'protocol': DRAFT, 'tolerance': TOLERANCE, 'comparison': 'emitted metric token, exact; no re-rounding',
            'selection_rule': SELECTION_RULE, 'collector_binding': collector,
            'corpus': {k: v for k, v in corpus.items() if k not in ('index_doc', 'sweeps')},
            'harness_commit': HARNESS_COMMIT, 'thread_environment': COLLECTOR_THREADS,
            'llm_requests': 'none (no manager; LLM client modules are a STOP)',
            'cases': [{k: v for k, v in c.items() if k != 'files'} for c in cases],
            'written_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    if dry_run:
        plan['environment'] = 'DEFERRED_TO_HOST'
        out.mkdir(parents=True)
        write_json(out / 'replay_plan.json', plan)
        return {'label': 'DRYRUN', 'cases': len(cases), 'out': str(out),
                'nodes': sorted({c['node'] for c in cases})}
    if platform.node().split('.')[0] != HOST:
        raise Stop(f'STOP: the replay runs on {HOST} only')
    if harness is None or batch is None or scratch is None:
        raise Stop('STOP: --harness, --batch and --scratch are required')
    harness, batch, scratch = Path(harness), Path(batch), Path(scratch)
    if harness.resolve() != (batch / 'autoresearch_harness').resolve() or \
            Path(os.environ.get('AR_HARNESS_ROOT', '')).resolve() != harness.resolve():
        raise Stop('STOP: harness must be the batch checkout and AR_HARNESS_ROOT')
    if os.environ.get('PYTHONDONTWRITEBYTECODE') != '1':
        raise Stop('STOP: PYTHONDONTWRITEBYTECODE=1 is required (the historical environment stays unchanged)')
    environment = check_environment(batch, harness)
    environment['harness'] = check_harness(harness, corpus['index_doc']['nodes'])
    environment['resources'] = check_resources(out, scratch, min_free_bytes)
    out.mkdir(parents=True)
    scratch.mkdir()
    plan['environment'] = environment
    write_json(out / 'replay_plan.json', plan)  # declared before the first execution
    (out / 'raw').mkdir()
    env_overrides = {**COLLECTOR_THREADS, **NO_GPU, 'PATH': environment['worker_path'], 'PYTHONDONTWRITEBYTECODE': '1'}
    results, stop = [], None
    try:
        for case in cases:
            r = execute(case, harness, scratch, env_overrides)
            (out / 'raw' / f"{case['case_id'].replace(':', '_')}.log").write_text(r.pop('log_text'))
            r['pass'] = case_passes(r)
            results.append(r)
            with (out / 'cases.jsonl').open('a') as fh:
                fh.write(json.dumps(r, sort_keys=True) + '\n')
                fh.flush()
                os.fsync(fh.fileno())
            if not r['pass']:
                stop = f"STOP: case {case['case_id']} does not reproduce at zero tolerance"
                break
        else:
            caches = check_harness(harness, corpus['index_doc']['nodes'])['data_caches_sha256']
            if caches != environment['harness']['data_caches_sha256']:
                stop = 'STOP: harness data caches changed during the replay'
    except BaseException as exc:  # interruption is a STOP; retain everything
        stop = f'STOP: interrupted: {type(exc).__name__}: {exc}'
    summary = {'label': LABEL, 'cases_planned': len(cases), 'cases_run': len(results),
               'cases_passed': sum(r['pass'] for r in results), 'stop': stop, 'tolerance': TOLERANCE,
               'scratch_retained': str(scratch), 'replay_plan_sha256': file_sha256(out / 'replay_plan.json'),
               'cases_sha256': file_sha256(out / 'cases.jsonl') if (out / 'cases.jsonl').exists() else None,
               'verdict': 'PASS' if stop is None and len(results) == 16 else 'STOP'}
    write_json(out / ('STOP.json' if summary['verdict'] == 'STOP' else 'summary.json'), summary)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--paper-root', default='.', help='paper checkout at the reviewed commit')
    ap.add_argument('--out', required=True, help='new output directory (never inside the batch or corpus)')
    ap.add_argument('--dry-run', action='store_true', help='source checks, case selection and recovery only')
    ap.add_argument('--harness', default=None, help='batch harness checkout (pinned 6adf385)')
    ap.add_argument('--batch', default=None, help=f'preserved sweep batch, e.g. {BATCH}')
    ap.add_argument('--scratch', default=None, help='new /tmp/r1_c3_env_replay_* directory')
    ap.add_argument('--min-free-bytes', type=int, default=0, help='operator disk-headroom estimate')
    args = ap.parse_args(argv)
    try:
        result = run(Path(args.paper_root), Path(args.out), dry_run=args.dry_run,
                     harness=Path(args.harness) if args.harness else None,
                     batch=Path(args.batch) if args.batch else None,
                     scratch=Path(args.scratch) if args.scratch else None, min_free_bytes=args.min_free_bytes)
    except Stop as exc:
        print(json.dumps({'verdict': 'STOP', 'reason': str(exc)}))
        return 2
    print(json.dumps(result))
    return 0 if result.get('verdict', 'PASS') == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
