"""R1-E1-OPENML-AMEND offline identity mechanism for the six OpenML nodes.

ENGINEERING_ONLY; AI-assisted. Reviewed code for the author's amended identity
criterion (``docs/r1/PLAN.md`` row **R1-E1-OPENML-AMEND**, basis
``e1-openml-20261116`` @ ``5d73550a``). It is the only code allowed to lift the
``c3_env_replay.py`` OpenML hard STOP, and only when every one of the following
holds at the same moment and on the same preserved cache:

* **(i) data id** -- the harness NodeSpecs and the frozen ``dataset.json`` at
  the pinned harness commit, the sweep-1 ``cache_check.json`` record and the
  reviewed audit all give the same OpenML data id (15/59/1510/29/40/1467).
* **(ii) loaded-data fingerprint** -- recomputing the sweep-1 pre-launch
  loaded-data fingerprint (``r1.noise.check_caches.check_node``) on the same
  preserved cache reproduces the values recorded in ``cache_check.json``
  (SHA-256 ``35e76f37...``, mtime ``2026-10-27T15:22:39Z``) exactly, with the
  same library versions. The recomputation runs with the process network
  disabled.
* **(iii) ARFF md5** -- each cache ARFF file's md5 equals the OpenML
  ``md5_checksum`` in the cache's own ``api/v1/json/data/<id>.gz`` metadata.
* **(iv) unchanged bytes** -- every cache file's SHA-256 and the whole cache
  tree digest before and after use equal the values recorded in the reviewed
  audit ``OFFLINE_MECHANISM_AUDIT.json`` (SHA-256 ``9f14c879...``).

Requirement (b), enforced worker network denial, lives in
``r1.c3.e1_offline_network`` and is installed by the driver *before* this
mechanism recomputes (ii), so the fingerprint load itself runs under the
enforced denial.

What this mechanism does NOT establish (stated in the amended report too):
the surviving bytes are not a hash the sweep itself recorded; the sweep-1
anchor is the data id plus the loaded-data fingerprint plus OpenML's own md5
self-consistency, not a sweep-1 file digest. Any mismatch, unreadable input or
unexpected file is a STOP, never a retry. No worker is executed here.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import platform
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TOKEN = 'r1-e1-openml-amend-20261117'  # the explicit reviewed flag/environment value
SCHEMA = 'r1.e1_openml_offline_mechanism/1'
AUDIT_REL = 'docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json'
AUDIT_SHA256 = '9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7'
AUDIT_SCHEMA = 'r1.e1_offline_mechanism_audit/1'
CACHE_CHECK_NAME = 'cache_check.json'
CACHE_CHECK_SHA256 = '35e76f37fcc4925a7896f6cf0bc2ab2bbf8647adfc763729da5a8e93325944f9'
CACHE_CHECK_MTIME_UTC = '2026-10-27T15:22:39Z'

OPENML_IDS = {
    'openml_breast_w': 15,
    'openml_ionosphere': 59,
    'openml_wdbc': 1510,
    'openml_credit_approval': 29,
    'openml_sonar': 40,
    'openml_climate': 1467,
}

# The cache_check.json fingerprint fields compared exactly (float 4dp included).
FINGERPRINT_FIELDS = ('dataset_id', 'cache_source', 'rows', 'features', 'categorical_columns',
                      'missing_values', 'target_name', 'class_counts', 'positive_label', 'minority_share')

FINGERPRINT_LOADER = 'r1.noise.check_caches.check_node'
ALLOWED_DOTFILES = frozenset({'.gitignore', '.gitkeep'})


class MechanismStop(RuntimeError):
    """An R1-E1-OPENML-AMEND identity STOP: report, retain everything, no retry."""


# ---------------------------------------------------------------------------- primitives

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path) -> str:
    return sha256(Path(path).read_bytes())


def tree_digest(root) -> str:
    """The driver's own data-cache tree digest algorithm, byte for byte."""
    root = Path(root)
    digest = hashlib.sha256()
    if root.exists():
        for path in sorted(root.rglob('*')):
            if path.is_file():
                digest.update(str(path.relative_to(root)).encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def _need(mapping, key, what):
    try:
        return mapping[key]
    except (KeyError, TypeError) as exc:
        raise MechanismStop(f'STOP: {what} is missing: {key!r}') from exc


def _regular_file(path, what):
    path = Path(path)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise MechanismStop(f'STOP: {what} is unreadable: {path}') from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise MechanismStop(f'STOP: {what} is not a regular file: {path}')
    return path


def _parse_utc(text) -> datetime:
    try:
        value = datetime.fromisoformat(str(text).replace('Z', '+00:00'))
    except ValueError as exc:
        raise MechanismStop(f'STOP: invalid recorded UTC timestamp {text!r}') from exc
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _git_show(harness: Path, commit: str, rel: str) -> bytes:
    """Exact bytes of one pinned harness file from the commit, not from the worktree."""
    try:
        return subprocess.check_output(['git', '-C', str(harness), 'show', f'{commit}:{rel}'],
                                       stderr=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise MechanismStop(f'STOP: pinned harness file unavailable at {commit}: {rel}') from exc


def verify_harness_head(harness: Path, commit: str) -> None:
    try:
        head = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'],
                                       text=True, stderr=subprocess.DEVNULL, timeout=60).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise MechanismStop(f'STOP: harness checkout unreadable: {harness}') from exc
    if head != commit:
        raise MechanismStop(f'STOP: harness HEAD {head} is not the pinned {commit}')


# ---------------------------------------------------------------------------- (i) data id

def verify_dataset_ids(harness: Path, harness_commit: str, audit: dict, cache_check: dict) -> dict:
    """(i): harness NodeSpecs, frozen dataset.json, sweep-1 record and audit agree."""
    pinned = _need(audit, 'pinned_harness', 'audit section pinned_harness')
    if str(pinned.get('commit')) != harness_commit:
        raise MechanismStop(f'STOP: audit pinned harness commit {pinned.get("commit")!r} '
                            f'is not {harness_commit!r}')
    if Path(str(pinned.get('path'))).resolve() != Path(harness).resolve():
        raise MechanismStop(f'STOP: audit pinned harness path {pinned.get("path")!r} is not {harness}')
    audit_specs = _need(pinned, 'node_specs', 'audit pinned_harness.node_specs')
    batch_record = _need(audit, 'sweep1_batch_records', 'audit sweep1_batch_records')
    audit_cc = _need(_need(batch_record, 'files', 'audit batch files'), CACHE_CHECK_NAME,
                     'audit cache_check record')
    audit_cc_nodes = _need(audit_cc, 'nodes', 'audit cache_check nodes')
    cc_nodes = {row.get('node'): row for row in _need(_need(cache_check, 'doc', 'cache_check'),
                                                      'nodes', 'cache_check nodes')}
    out = {}
    for node, expected in OPENML_IDS.items():
        spec = _need(audit_specs, node, f'audit NodeSpec {node}')
        row = cc_nodes.get(node)
        if row is None:
            raise MechanismStop(f'STOP: {node}: no sweep-1 cache_check record (data id missing)')
        recorded = row.get('dataset_id')
        if recorded is None:
            raise MechanismStop(f'STOP: {node}: sweep-1 cache_check record has no dataset_id')
        audited = _need(_need(audit_cc_nodes, node, f'audit cache_check entry {node}'),
                        'dataset_id', f'audit cache_check dataset_id {node}')
        try:
            config = json.loads(_git_show(harness, harness_commit, f'configs/nodes/{node}.yaml'))
            identity = json.loads(_git_show(harness, harness_commit, f'nodes/{node}/dataset.json'))
        except json.JSONDecodeError as exc:
            raise MechanismStop(f'STOP: {node}: pinned harness NodeSpec is not JSON') from exc
        seen = {'harness_node_spec': (config.get('dataset') or {}).get('dataset_id'),
                'harness_dataset_json': identity.get('dataset_id'),
                'sweep1_cache_check': recorded, 'audit_cache_check': audited,
                'audit_node_spec': spec.get('dataset_id')}
        if any(value != expected for value in seen.values()):
            raise MechanismStop(f'STOP: {node}: OpenML data id mismatch, expected {expected}: {seen}')
        if identity.get('node_name') != node:
            raise MechanismStop(f'STOP: {node}: pinned dataset.json names {identity.get("node_name")!r}')
        if (config.get('dataset') or {}).get('dataset_name') not in (None, spec.get('dataset_name')):
            raise MechanismStop(f'STOP: {node}: pinned dataset_name differs from the audit')
        if (config.get('dataset') or {}).get('target') not in (None, spec.get('target')):
            raise MechanismStop(f'STOP: {node}: pinned target differs from the audit')
        out[node] = {'dataset_id': expected, 'sources': seen,
                     'dataset_name': spec.get('dataset_name'), 'target': spec.get('target')}
    return out


# ---------------------------------------------------------------------------- (iii) ARFF md5

def _cache_relative_paths(audit: dict, node: str, dataset_id: int) -> dict:
    observation = _need(audit, 'current_cache_observation', 'audit current_cache_observation')
    recorded = _need(_need(observation, 'per_file_sha256', 'audit per_file_sha256'), node,
                     f'audit per-file hashes {node}')
    if not isinstance(recorded, dict) or len(recorded) != 4:
        raise MechanismStop(f'STOP: {node}: expected four audited cache files, got {recorded!r}')
    metadata = [rel for rel in recorded if rel == f'openml/openml.org/api/v1/json/data/{dataset_id}.gz']
    features = [rel for rel in recorded if '/api/v1/json/data/features/' in rel]
    qualities = [rel for rel in recorded if '/api/v1/json/data/qualities/' in rel]
    arff = [rel for rel in recorded if '/data/v1/download/' in rel]
    if len(metadata) != 1 or len(features) != 1 or len(qualities) != 1 or len(arff) != 1:
        raise MechanismStop(f'STOP: {node}: audited cache paths are not the four expected files: '
                            f'{sorted(recorded)}')
    return {'metadata': metadata[0], 'features': features[0], 'qualities': qualities[0], 'arff': arff[0]}


def _arff_consistency(cache_root: Path, node: str, dataset_id: int,
                      metadata_rel: str, arff_rel: str) -> dict:
    """The cache ARFF md5 must equal the OpenML md5_checksum in the cache metadata."""
    metadata_path = _regular_file(Path(cache_root) / metadata_rel, f'{node} cache metadata')
    arff_path = _regular_file(Path(cache_root) / arff_rel, f'{node} cache ARFF')
    try:
        metadata = json.loads(gzip.decompress(metadata_path.read_bytes()).decode('utf-8'))
        arff = gzip.decompress(arff_path.read_bytes())
    except (OSError, EOFError, ValueError) as exc:
        raise MechanismStop(f'STOP: {node}: cache metadata/ARFF cannot be read: '
                            f'{type(exc).__name__}: {exc}') from exc
    description = _need(metadata, 'data_set_description', f'{node} cache metadata data_set_description')
    checksum = description.get('md5_checksum')
    if not isinstance(checksum, str) or len(checksum) != 32:
        raise MechanismStop(f'STOP: {node}: cache metadata has no OpenML md5_checksum')
    if str(description.get('id')) != str(dataset_id):
        raise MechanismStop(f'STOP: {node}: cache metadata id {description.get("id")!r} is not {dataset_id}')
    file_id = str(description.get('file_id'))
    if f'/data/v1/download/{file_id}/' not in arff_rel:
        raise MechanismStop(f'STOP: {node}: cache ARFF path does not match metadata file_id {file_id!r}')
    actual = hashlib.md5(arff).hexdigest()
    if actual != checksum:
        raise MechanismStop(f'STOP: {node}: cache ARFF md5 {actual} differs from the OpenML '
                            f'md5_checksum {checksum}')
    return {'metadata': metadata_rel, 'arff': arff_rel, 'file_id': file_id,
            'md5_checksum': checksum, 'arff_md5': actual}


def verify_arff_md5(cache_root: Path, audit: dict, node: str, dataset_id: int, rels: dict) -> dict:
    out = _arff_consistency(Path(cache_root), node, dataset_id, rels['metadata'], rels['arff'])
    self_description = _need(_need(audit, 'current_cache_observation', 'audit observation'),
                             'openml_self_description', 'audit openml_self_description')
    recorded = _need(self_description, node, f'audit OpenML self-description {node}')
    if str(recorded.get('file_id')) != out['file_id']:
        raise MechanismStop(f'STOP: {node}: OpenML file_id differs from the audit')
    recorded_md5 = recorded.get('md5_checksum', recorded.get('openml_md5_checksum'))
    if recorded_md5 != out['md5_checksum']:
        raise MechanismStop(f'STOP: {node}: OpenML md5 self-consistency differs from the audit')
    return out


# ---------------------------------------------------------------------------- (iv) unchanged bytes

def _walk_cache(root: Path, node: str) -> dict:
    root = Path(root)
    try:
        mode = root.lstat().st_mode
    except OSError as exc:
        raise MechanismStop(f'STOP: {node}: cache is unreadable: {root}') from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise MechanismStop(f'STOP: {node}: cache is not a real directory: {root}')
    entries = {}

    def onerror(exc):
        raise MechanismStop(f'STOP: {node}: cannot inspect the whole cache tree: {exc}') from exc

    for current, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        here = Path(current)
        for name in dirs:
            path = here / name
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                raise MechanismStop(f'STOP: {node}: cache directory unreadable: {path}') from exc
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise MechanismStop(f'STOP: {node}: cache contains a symlink or irregular entry: {path}')
        for name in files:
            path = here / name
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                raise MechanismStop(f'STOP: {node}: cache file unreadable: {path}') from exc
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise MechanismStop(f'STOP: {node}: cache contains a symlink or irregular entry: {path}')
            try:
                entries[path.relative_to(root).as_posix()] = file_sha256(path)
            except OSError as exc:
                raise MechanismStop(f'STOP: {node}: cache file unreadable: {path}') from exc
    if not entries:
        raise MechanismStop(f'STOP: {node}: cache is empty')
    return entries


def _is_allowed_dotfile(rel: str) -> bool:
    return '/' not in rel and rel in ALLOWED_DOTFILES


def snapshot_cache(cache_root: Path, audit: dict, node: str) -> dict:
    """(iv) fingerprint the whole cache tree; every file must equal the reviewed audit."""
    entries = _walk_cache(Path(cache_root), node)
    observation = _need(audit, 'current_cache_observation', 'audit observation')
    per_file = _need(_need(observation, 'per_file_sha256', 'audit per_file_sha256'), node,
                     f'audit per-file hashes {node}')
    expected = set(per_file)
    unexpected = sorted(rel for rel in entries if rel not in expected and not _is_allowed_dotfile(rel))
    missing = sorted(rel for rel in expected if rel not in entries)
    if unexpected or missing:
        raise MechanismStop(f'STOP: {node}: cache file set differs from the audit; '
                            f'missing={missing} unexpected={unexpected}')
    for rel, expected_sha in per_file.items():
        if entries[rel] != expected_sha:
            raise MechanismStop(f'STOP: {node}: cache file SHA-256 differs from the audit: {rel}')
    digest = tree_digest(Path(cache_root))
    recorded_digest = _need(_need(observation, 'tree_digest_driver_algorithm', 'audit tree digests'),
                            node, f'audit tree digest {node}')
    if digest != recorded_digest:
        raise MechanismStop(f'STOP: {node}: cache tree digest {digest} differs from the audit '
                            f'{recorded_digest}')
    return {'files': entries, 'tree_digest': digest,
            'dotfiles': sorted(rel for rel in entries if rel not in expected)}


# ---------------------------------------------------------------------------- (ii) fingerprint

def _current_versions() -> dict:
    import importlib.metadata as metadata
    try:
        return {'python': platform.python_version(), 'sklearn': metadata.version('scikit-learn'),
                'numpy': metadata.version('numpy'), 'pandas': metadata.version('pandas')}
    except metadata.PackageNotFoundError as exc:
        raise MechanismStop(f'STOP: cannot read the pinned library versions: {exc}') from exc


def default_fingerprint_loader(harness: Path, node: str) -> dict:
    """Recompute the sweep-1 loaded-data fingerprint on the preserved cache, network disabled."""
    from r1.noise import check_caches as check  # lazy: imports the harness eagerly
    from r1.noise import e1_noise_floor as e1
    check.HARNESS = Path(harness)
    e1.HARNESS = Path(harness)
    check._disable_network()
    with tempfile.TemporaryDirectory(prefix='r1_e1_openml_fp_') as tmp:
        return check.check_node(node, Path(tmp))


def bind_cache_check(batch: Path, audit: dict) -> dict:
    """Bind the sweep-1 pre-launch cache_check.json by hash, mtime and pre-launch position."""
    path = Path(batch) / CACHE_CHECK_NAME
    _regular_file(path, 'sweep-1 cache_check.json')
    batch_record = _need(audit, 'sweep1_batch_records', 'audit sweep1_batch_records')
    if Path(str(_need(batch_record, 'batch', 'audit batch path'))).resolve() != Path(batch).resolve():
        raise MechanismStop(f'STOP: audit batch {batch_record.get("batch")!r} is not {batch}')
    record = _need(_need(batch_record, 'files', 'audit batch files'), CACHE_CHECK_NAME,
                   'audit cache_check record')
    digest = file_sha256(path)
    if digest != record.get('sha256'):
        raise MechanismStop(f'STOP: cache_check.json SHA-256 {digest} differs from the audit '
                            f'{record.get("sha256")}')
    if digest != CACHE_CHECK_SHA256:
        raise MechanismStop(f'STOP: cache_check.json is not the reviewed sweep-1 record '
                            f'({CACHE_CHECK_SHA256})')
    recorded_mtime = _parse_utc(record.get('mtime_utc'))
    if recorded_mtime != _parse_utc(CACHE_CHECK_MTIME_UTC):
        raise MechanismStop(f'STOP: audit records cache_check mtime {record.get("mtime_utc")!r}, '
                            f'expected {CACHE_CHECK_MTIME_UTC}')
    try:
        actual_mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0)
    except OSError as exc:
        raise MechanismStop(f'STOP: cache_check.json is unreadable: {path}') from exc
    if actual_mtime != recorded_mtime:
        raise MechanismStop(f'STOP: cache_check.json mtime {actual_mtime.isoformat()} differs from '
                            f'the recorded {recorded_mtime.isoformat()}')
    launch = _parse_utc(_need(batch_record, 'launch_utc', 'audit launch_utc'))
    if not actual_mtime < launch:
        raise MechanismStop('STOP: cache_check.json is not before the sweep-1 launch')
    try:
        doc = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise MechanismStop('STOP: cache_check.json is not valid JSON') from exc
    return {'path': str(path), 'sha256': digest, 'mtime_utc': actual_mtime.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'launch_utc': launch.strftime('%Y-%m-%dT%H:%M:%SZ'), 'doc': doc}


def verify_fingerprints(harness: Path, cache_check: dict, audit: dict,
                        loader=None, versions_probe=None) -> dict:
    """(ii): recompute the loaded-data fingerprint with the same cache and compare exactly."""
    loader = loader or default_fingerprint_loader
    versions = (versions_probe or _current_versions)()
    recorded_versions = cache_check['doc'].get('versions') or {}
    for name, value in recorded_versions.items():
        if versions.get(name) != value:
            raise MechanismStop(f'STOP: library environment differs from the sweep-1 cache_check: '
                                f'{name}={versions.get(name)!r}, recorded {value!r}')
    recorded_harness = cache_check['doc'].get('harness')
    if recorded_harness is not None and Path(str(recorded_harness)).resolve() != Path(harness).resolve():
        raise MechanismStop(f'STOP: the sweep-1 cache_check was produced with a different harness: '
                            f'{recorded_harness!r}')
    cc_nodes = {row.get('node'): row for row in cache_check['doc'].get('nodes') or []}
    audit_cc = _need(_need(_need(audit, 'sweep1_batch_records', 'audit sweep1_batch_records'),
                           'files', 'audit batch files'), CACHE_CHECK_NAME, 'audit cache_check record')
    audit_nodes = _need(audit_cc, 'nodes', 'audit cache_check nodes')
    fingerprints = {}
    for node in OPENML_IDS:
        recorded = cc_nodes.get(node)
        if recorded is None:
            raise MechanismStop(f'STOP: {node}: no sweep-1 loaded-data fingerprint')
        try:
            row = loader(harness, node)
        except MechanismStop:
            raise
        except Exception as exc:  # noqa: BLE001 - any loader failure is a STOP, never skipped
            raise MechanismStop(f'STOP: {node}: fingerprint recomputation failed: '
                                f'{type(exc).__name__}: {exc}') from exc
        fingerprint = {}
        for field in FINGERPRINT_FIELDS:
            if field not in row:
                raise MechanismStop(f'STOP: {node}: recomputed fingerprint lacks {field!r} '
                                    f'(status {row.get("status")!r}, reason {row.get("reason")!r})')
            if row[field] != recorded.get(field):
                raise MechanismStop(f'STOP: {node}: loaded-data fingerprint differs at {field!r}: '
                                    f'recomputed {row[field]!r}, sweep-1 record {recorded.get(field)!r}')
            fingerprint[field] = row[field]
        recorded_path = recorded.get('cache_path')
        expected_path = Path(harness) / 'nodes' / node / 'data_cache'
        if recorded_path is not None and Path(str(recorded_path)).resolve() != expected_path.resolve():
            raise MechanismStop(f'STOP: {node}: the sweep-1 record points at a different cache: '
                                f'{recorded_path!r}')
        audited = _need(_need(audit_nodes, node, f'audit cache_check entry {node}'),
                        'dataset_id', f'audit cache_check dataset_id {node}')
        if audited != fingerprint['dataset_id']:
            raise MechanismStop(f'STOP: {node}: audit cache_check dataset id {audited!r} differs from '
                                f'the recomputed {fingerprint["dataset_id"]!r}')
        fingerprints[node] = fingerprint
    return {'loader': FINGERPRINT_LOADER, 'versions': versions, 'fingerprints': fingerprints}


# ---------------------------------------------------------------------------- the mechanism

class OpenMLOfflineMechanism:
    """A verified identity report; the only object allowed to admit an OpenML case."""

    def __init__(self, report: dict):
        self.report = report

    @property
    def nodes(self) -> tuple:
        return tuple(self.report['nodes'])

    def verify_source_caches(self, harness: Path) -> dict:
        """(iv) re-verify every source cache after the last case; STOP on any change."""
        out = {}
        for node, record in self.report['nodes'].items():
            cache_root = Path(harness) / 'nodes' / node / 'data_cache'
            entries = _walk_cache(cache_root, node)
            if entries != record['cache_files']:
                changed = sorted(rel for rel in set(entries) | set(record['cache_files'])
                                 if entries.get(rel) != record['cache_files'].get(rel))
                raise MechanismStop(f'STOP: {node}: source cache changed during the replay: {changed}')
            digest = tree_digest(cache_root)
            if digest != record['cache_tree_digest']:
                raise MechanismStop(f'STOP: {node}: source cache tree digest changed during the replay')
            out[node] = digest
        return out

    def verify_case_cache(self, node: str, cache_root: Path, phase: str) -> dict:
        """(iii)+(iv) before/after use: the per-case copy must still be the audited bytes."""
        if node not in self.report['nodes']:
            raise MechanismStop(f'STOP: {node}: not part of the verified OpenML identity')
        record = self.report['nodes'][node]
        entries = _walk_cache(Path(cache_root), node)
        if entries != record['cache_files']:
            changed = sorted(rel for rel in set(entries) | set(record['cache_files'])
                             if entries.get(rel) != record['cache_files'].get(rel))
            raise MechanismStop(f'STOP: {node}: {phase}-use cache copy differs from the audited '
                                f'identity: {changed}')
        digest = tree_digest(Path(cache_root))
        if digest != record['cache_tree_digest']:
            raise MechanismStop(f'STOP: {node}: {phase}-use cache copy tree digest differs from the audit')
        arff = _arff_consistency(Path(cache_root), node, record['dataset_id'],
                                record['arff']['metadata'], record['arff']['arff'])
        if arff['md5_checksum'] != record['arff']['md5_checksum'] or \
                arff['arff_md5'] != record['arff']['arff_md5']:
            raise MechanismStop(f'STOP: {node}: {phase}-use cache ARFF md5 differs from the audit')
        return {'phase': phase, 'node': node, 'tree_digest': digest, 'files': len(entries),
                'arff_md5': arff['arff_md5']}


def prepare(paper: Path, harness: Path, batch: Path, harness_commit: str, *,
            fingerprint_loader=None, versions_probe=None) -> OpenMLOfflineMechanism:
    """Prove (i)-(iv) before any case may be scheduled; STOP on any failure."""
    try:
        audit = load_audit(paper)
        verify_harness_head(harness, harness_commit)
        cache_check = bind_cache_check(batch, audit)
        data_ids = verify_dataset_ids(harness, harness_commit, audit, cache_check)
        nodes = {}
        for node, dataset_id in OPENML_IDS.items():
            rels = _cache_relative_paths(audit, node, dataset_id)
            cache_root = Path(harness) / 'nodes' / node / 'data_cache'
            snapshot = snapshot_cache(cache_root, audit, node)
            arff = verify_arff_md5(cache_root, audit, node, dataset_id, rels)
            nodes[node] = {'dataset_id': dataset_id, 'cache_path': str(cache_root),
                           'dataset_identity': data_ids[node], 'cache_files': snapshot['files'],
                           'cache_tree_digest': snapshot['tree_digest'],
                           'cache_dotfiles': snapshot['dotfiles'], 'arff': arff}
        fingerprint = verify_fingerprints(harness, cache_check, audit, loader=fingerprint_loader,
                                          versions_probe=versions_probe)
        for node in nodes:
            nodes[node]['loaded_data_fingerprint'] = fingerprint['fingerprints'][node]
        return OpenMLOfflineMechanism({
            'schema': SCHEMA, 'token': TOKEN, 'label': 'ENGINEERING_ONLY',
            'written_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'authority': {
                'row': 'R1-E1-OPENML-AMEND',
                'basis': 'e1-openml-20261116 @ 5d73550a (audit + accepted independent review)',
                'audit': {'path': AUDIT_REL, 'sha256': AUDIT_SHA256},
                'sweep1_record': {'path': str(Path(batch) / CACHE_CHECK_NAME),
                                  'sha256': CACHE_CHECK_SHA256, 'mtime_utc': CACHE_CHECK_MTIME_UTC},
                'harness_commit': harness_commit,
                'fingerprint_loader': FINGERPRINT_LOADER,
            },
            'identity': {'criterion': '(i) data id, (ii) loaded-data fingerprint, (iii) ARFF md5, '
                                      '(iv) unchanged audited bytes; plus (b) enforced worker '
                                      'network denial',
                         'anchor_is_sweep1_file_hash': False,
                         'note': 'identity rests on the sweep-1 data id and loaded-data fingerprint, '
                                 'not on a file hash recorded by sweep 1'},
            'environments': fingerprint['versions'],
            'nodes': nodes,
        })
    except MechanismStop:
        raise
    except Exception as exc:  # noqa: BLE001 - fail closed: never admit a case on an unexpected error
        raise MechanismStop(f'STOP: fingerprint/identity verification failed: '
                            f'{type(exc).__name__}: {exc}') from exc


def load_audit(paper: Path) -> dict:
    """Load the pinned reviewed audit; its own SHA-256 is the trust anchor."""
    path = Path(paper) / AUDIT_REL
    _regular_file(path, 'reviewed audit')
    digest = file_sha256(path)
    if digest != AUDIT_SHA256:
        raise MechanismStop(f'STOP: {AUDIT_REL} SHA-256 {digest} is not the reviewed {AUDIT_SHA256}')
    try:
        audit = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise MechanismStop(f'STOP: {AUDIT_REL} is not valid JSON') from exc
    if audit.get('schema') != AUDIT_SCHEMA:
        raise MechanismStop(f'STOP: {AUDIT_REL} schema {audit.get("schema")!r} is not {AUDIT_SCHEMA!r}')
    return audit
