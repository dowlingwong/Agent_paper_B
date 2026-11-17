"""R1-E1-OPENML-AMEND offline identity mechanism: fixture tests only.

No e1 run, no network, no deepthought, no batch or venv. The fixtures reproduce
the reviewed cache layout (four OpenML cache files per node, metadata md5
self-consistency) and the sweep-1 ``cache_check.json`` / audit record shape.
"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

import pytest

from r1.c3 import e1_openml_offline as M
from r1.scripts import c3_env_replay as R

NODES = {
    'openml_breast_w': (15, 52350, 'breast-w', 'Class'),
    'openml_ionosphere': (59, 59, 'ionosphere', 'class'),
    'openml_wdbc': (1510, 1592318, 'wdbc', 'Class'),
    'openml_credit_approval': (29, 29, 'credit-approval', 'class'),
    'openml_sonar': (40, 40, 'sonar', 'Class'),
    'openml_climate': (1467, 1586232, 'climate-model-simulation-crashes', 'Class'),
}
VERSIONS = {'python': '3.13.15', 'sklearn': '1.8.0', 'numpy': '2.4.4', 'pandas': '3.0.3'}
CACHE_MTIME = datetime(2026, 10, 27, 15, 22, 39, tzinfo=timezone.utc)
LAUNCH = datetime(2026, 10, 27, 15, 48, 34, tzinfo=timezone.utc)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=check)


def _write_gz(path, payload: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(payload))


class Fixture:
    """A synthetic but schema-faithful preserved harness/batch/audit fixture."""

    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.paper = tmp_path / 'paper'
        self.batch = tmp_path / 'batch'
        self.harness = self.batch / 'autoresearch_harness'
        self.cache_check_path = self.batch / 'cache_check.json'
        self.rels, self.fingerprints, self.arff = {}, {}, {}
        for index, (node, (dataset_id, file_id, name, target)) in enumerate(NODES.items()):
            cache = self.harness / 'nodes' / node / 'data_cache'
            rels = {
                'metadata': f'openml/openml.org/api/v1/json/data/{dataset_id}.gz',
                'features': f'openml/openml.org/api/v1/json/data/features/{dataset_id}.gz',
                'qualities': f'openml/openml.org/api/v1/json/data/qualities/{dataset_id}.gz',
                'arff': f'openml/openml.org/data/v1/download/{file_id}/{name}.arff.gz',
            }
            arff = f'@relation {name}\n@attribute a numeric\n@data\n1\n'.encode()
            md5 = hashlib.md5(arff).hexdigest()
            self.arff[node] = {'file_id': str(file_id), 'md5_checksum': md5, 'arff_md5': md5}
            _write_gz(cache / rels['metadata'], json.dumps({'data_set_description': {
                'id': str(dataset_id), 'name': name, 'version': '1', 'file_id': str(file_id),
                'format': 'ARFF', 'md5_checksum': md5}}).encode())
            _write_gz(cache / rels['features'], b'{"features": []}')
            _write_gz(cache / rels['qualities'], b'{"qualities": []}')
            _write_gz(cache / rels['arff'], arff)
            if node in ('openml_sonar', 'openml_climate'):
                (cache / '.gitignore').write_text('openml/\n')
                (cache / '.gitkeep').write_text('')
            self.rels[node] = rels
            self.fingerprints[node] = {
                'dataset_id': dataset_id, 'cache_source': 'node data_cache',
                'rows': 699 - index, 'features': 9 + index, 'categorical_columns': 0,
                'missing_values': index, 'target_name': target,
                'class_counts': {'a': 100 + index, 'b': 200 - index},
                'positive_label': 'b', 'minority_share': round((100 + index) / 300, 4)}
            (self.harness / 'nodes' / node / 'dataset.json').write_text(json.dumps(
                {'node_name': node, 'dataset_id': dataset_id, 'dataset_name': name, 'target': target}))
            (self.harness / 'configs/nodes').mkdir(parents=True, exist_ok=True)
            (self.harness / 'configs/nodes' / f'{node}.yaml').write_text(json.dumps(
                {'name': node, 'metric_name': 'val_auc',
                 'dataset': {'source': 'openml', 'dataset_id': dataset_id,
                             'dataset_name': name, 'target': target}}))
        self.cache_check_path.write_text(json.dumps({
            'harness': str(self.harness), 'versions': dict(VERSIONS),
            'nodes': [{'node': node, **self.fingerprints[node],
                       'cache_path': str(self.harness / 'nodes' / node / 'data_cache'),
                       'problems': [], 'status': 'ok'} for node in NODES]}, indent=2) + '\n')
        stamp = CACHE_MTIME.timestamp()
        os.utime(self.cache_check_path, (stamp, stamp))
        _git(self.harness, 'init', '-q')
        _git(self.harness, 'add', '-A')
        _git(self.harness, '-c', 'user.email=fixture@example.invalid', '-c', 'user.name=fixture',
             'commit', '-qm', 'fixture')
        self.commit = _git(self.harness, 'rev-parse', 'HEAD').stdout.strip()
        self.audit = {
            'schema': M.AUDIT_SCHEMA, 'label': 'ENGINEERING_ONLY',
            'written_utc': '2026-11-16T23:14:00Z',
            'verdict': {'identity': 'UNPROVABLE'},
            'sweep1_batch_records': {
                'batch': str(self.batch),
                'launch_utc': LAUNCH.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'files': {'cache_check.json': {'sha256': _sha(self.cache_check_path.read_bytes()),
                                               'mtime_utc': CACHE_MTIME.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                               'nodes': {node: {'dataset_id': spec['dataset_id'],
                                                                'cache_source': 'node data_cache'}
                                                         for node, spec in self.fingerprints.items()}}}},
            'pinned_harness': {
                'commit': self.commit, 'path': str(self.harness),
                'node_specs': {node: {'dataset_id': spec['dataset_id'],
                                      'dataset_name': NODES[node][2], 'target': NODES[node][3]}
                               for node, spec in self.fingerprints.items()}},
            'current_cache_observation': {
                'per_file_sha256': {}, 'tree_digest_driver_algorithm': {},
                'openml_self_description': {
                    node: {'dataset_version': '1', 'file_id': self.arff[node]['file_id'],
                           'openml_md5_checksum': self.arff[node]['md5_checksum'],
                           'uncompressed_arff_md5': self.arff[node]['md5_checksum']}
                    for node in NODES}},
        }
        self.write_audit()

    def cache(self, node):
        return self.harness / 'nodes' / node / 'data_cache'

    def write_audit(self):
        observation = self.audit['current_cache_observation']
        observation['per_file_sha256'] = {
            node: {rel: M.file_sha256(self.cache(node) / rel) for rel in self.rels[node].values()}
            for node in NODES}
        observation['tree_digest_driver_algorithm'] = {
            node: M.tree_digest(self.cache(node)) for node in NODES}
        path = self.paper / M.AUDIT_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.audit, indent=2, sort_keys=True) + '\n')
        self.audit_path = path
        return path

    def pin(self, monkeypatch):
        self.mp = monkeypatch
        monkeypatch.setattr(M, 'AUDIT_SHA256', M.file_sha256(self.audit_path))
        monkeypatch.setattr(M, 'CACHE_CHECK_SHA256', _sha(self.cache_check_path.read_bytes()))

    def repin(self):
        self.pin(self.mp)

    def rebind_cache_check(self):
        """Rewrite the audit's cache_check hash after a deliberate record mutation, then re-pin."""
        stamp = CACHE_MTIME.timestamp()
        os.utime(self.cache_check_path, (stamp, stamp))  # writing the record must not move its mtime
        self.audit['sweep1_batch_records']['files']['cache_check.json']['sha256'] = _sha(
            self.cache_check_path.read_bytes())
        self.write_audit()
        self.repin()

    def recommit(self):
        _git(self.harness, 'add', '-A')
        _git(self.harness, '-c', 'user.email=fixture@example.invalid', '-c', 'user.name=fixture',
             'commit', '-qm', 'fixture mutation')
        self.commit = _git(self.harness, 'rev-parse', 'HEAD').stdout.strip()
        self.audit['pinned_harness']['commit'] = self.commit
        self.write_audit()
        self.repin()
        return self.commit

    def loader(self, harness, node):
        return dict(self.fingerprints[node], problems=[], status='ok')

    def versions(self):
        return dict(VERSIONS)

    def prepare(self, **kwargs):
        return M.prepare(self.paper, self.harness, self.batch, self.commit,
                         fingerprint_loader=kwargs.pop('fingerprint_loader', self.loader),
                         versions_probe=kwargs.pop('versions_probe', self.versions), **kwargs)


@pytest.fixture
def fx(tmp_path, monkeypatch):
    fixture = Fixture(tmp_path)
    fixture.pin(monkeypatch)
    return fixture


# ---------------------------------------------------------------------------- accepted identity

def test_prepare_accepts_the_full_amended_identity_and_records_evidence(fx):
    mechanism = fx.prepare()
    report = mechanism.report
    assert report['schema'] == M.SCHEMA and report['token'] == M.TOKEN
    assert report['identity']['anchor_is_sweep1_file_hash'] is False
    assert set(report['nodes']) == set(NODES)
    for node, (dataset_id, _file_id, _name, _target) in NODES.items():
        record = report['nodes'][node]
        assert record['dataset_id'] == dataset_id
        assert record['cache_tree_digest'] == fx.audit['current_cache_observation'][
            'tree_digest_driver_algorithm'][node]
        for rel, expected_sha in fx.audit['current_cache_observation']['per_file_sha256'][node].items():
            assert record['cache_files'][rel] == expected_sha
        assert record['arff']['md5_checksum'] == record['arff']['arff_md5']
        assert record['loaded_data_fingerprint'] == fx.fingerprints[node]
    assert report['environments'] == VERSIONS
    json.dumps(report)  # must be serialisable into the replay plan


def test_prepare_recomputes_the_sweep1_fingerprint_with_the_supplied_loader(fx):
    seen = []

    def loader(harness, node):
        seen.append((str(harness), node))
        return fx.loader(harness, node)

    fx.prepare(fingerprint_loader=loader)
    assert [node for _harness, node in seen] == list(NODES)


def test_dotfile_only_cache_trees_are_covered_by_the_tree_digest(fx):
    report = fx.prepare().report
    assert set(report['nodes']['openml_sonar']['cache_dotfiles']) == {'.gitignore', '.gitkeep'}
    assert report['nodes']['openml_breast_w']['cache_dotfiles'] == []


# ---------------------------------------------------------------------------- (i) data id STOPs

def test_missing_dataset_id_in_the_sweep1_record_is_a_stop(fx):
    doc = json.loads(fx.cache_check_path.read_text())
    for row in doc['nodes']:
        if row['node'] == 'openml_wdbc':
            del row['dataset_id']
    fx.cache_check_path.write_text(json.dumps(doc) + '\n')
    with pytest.raises(M.MechanismStop, match='cache_check.json SHA-256'):
        fx.prepare()


def test_missing_dataset_id_is_a_stop_at_the_identity_comparison(fx):
    cache_check = M.bind_cache_check(fx.batch, fx.audit)
    fx.audit['sweep1_batch_records']['files']['cache_check.json']['nodes']['openml_wdbc'].pop('dataset_id')
    cache_check['doc']['nodes'] = [row for row in cache_check['doc']['nodes']
                                   if row['node'] != 'openml_wdbc'] + [
        {'node': 'openml_wdbc', 'status': 'ok', 'cache_source': 'node data_cache'}]
    with pytest.raises(M.MechanismStop, match='no dataset_id'):
        M.verify_dataset_ids(fx.harness, fx.commit, fx.audit, cache_check)


def test_harness_node_spec_dataset_id_mismatch_is_a_stop(fx):
    path = fx.harness / 'configs/nodes/openml_sonar.yaml'
    doc = json.loads(path.read_text())
    doc['dataset']['dataset_id'] = 41
    path.write_text(json.dumps(doc))
    fx.recommit()
    with pytest.raises(M.MechanismStop, match='data id mismatch'):
        fx.prepare()


def test_dataset_id_mismatch_is_a_stop(fx):
    # Keep the pinned audit in step so the id comparison (not the audit pin) fires.
    path = fx.harness / 'configs/nodes/openml_sonar.yaml'
    doc = json.loads(path.read_text())
    doc['dataset']['dataset_id'] = 41
    path.write_text(json.dumps(doc))
    fx.recommit()
    with pytest.raises(M.MechanismStop, match='data id mismatch'):
        fx.prepare()


def test_dataset_json_missing_id_is_a_stop(fx):
    path = fx.harness / 'nodes/openml_sonar/dataset.json'
    doc = json.loads(path.read_text())
    del doc['dataset_id']
    path.write_text(json.dumps(doc))
    fx.recommit()
    with pytest.raises(M.MechanismStop, match='data id mismatch'):
        fx.prepare()


# ---------------------------------------------------------------------------- (ii) fingerprint STOPs

def test_fingerprint_difference_is_a_stop(fx):
    def loader(harness, node):
        row = fx.loader(harness, node)
        if node == 'openml_ionosphere':
            row['rows'] += 1
        return row

    with pytest.raises(M.MechanismStop, match="loaded-data fingerprint differs at 'rows'"):
        fx.prepare(fingerprint_loader=loader)


def test_fingerprint_class_counts_difference_is_a_stop(fx):
    def loader(harness, node):
        row = fx.loader(harness, node)
        row['class_counts'] = dict(row['class_counts'])
        row['class_counts']['a'] += 1
        return row

    with pytest.raises(M.MechanismStop, match='class_counts'):
        fx.prepare(fingerprint_loader=loader)


def test_fingerprint_loader_failure_is_a_stop(fx):
    def loader(_harness, _node):
        raise RuntimeError('cache not loadable offline')

    with pytest.raises(M.MechanismStop, match='recomputation failed'):
        fx.prepare(fingerprint_loader=loader)


def test_library_version_difference_is_a_stop(fx):
    def versions():
        return {**VERSIONS, 'numpy': '2.4.5'}

    with pytest.raises(M.MechanismStop, match='library environment differs'):
        fx.prepare(versions_probe=versions)


def test_cache_path_difference_is_a_stop(fx):
    doc = json.loads(fx.cache_check_path.read_text())
    for row in doc['nodes']:
        if row['node'] == 'openml_wdbc':
            row['cache_path'] = '/elsewhere/data_cache'
    fx.cache_check_path.write_text(json.dumps(doc) + '\n')
    fx.rebind_cache_check()
    with pytest.raises(M.MechanismStop, match='different cache'):
        fx.prepare()


def test_cache_check_harness_difference_is_a_stop(fx):
    doc = json.loads(fx.cache_check_path.read_text())
    doc['harness'] = '/elsewhere/autoresearch_harness'
    fx.cache_check_path.write_text(json.dumps(doc) + '\n')
    fx.rebind_cache_check()
    with pytest.raises(M.MechanismStop, match='different harness'):
        fx.prepare()


def test_missing_loaded_data_fingerprint_is_a_stop(fx):
    cache_check = M.bind_cache_check(fx.batch, fx.audit)
    cache_check['doc']['nodes'] = [row for row in cache_check['doc']['nodes']
                                   if row['node'] != 'openml_sonar']
    with pytest.raises(M.MechanismStop, match='no sweep-1 loaded-data fingerprint'):
        M.verify_fingerprints(fx.harness, cache_check, fx.audit, loader=fx.loader,
                              versions_probe=fx.versions)


# ---------------------------------------------------------------------------- (iii) ARFF md5 STOPs

def test_arff_md5_tamper_is_a_stop_even_with_audit_hashes_in_step(fx):
    cache = fx.cache('openml_ionosphere')
    arff_rel = fx.rels['openml_ionosphere']['arff']
    (cache / arff_rel).write_bytes(gzip.compress(b'tampered ARFF payload'))
    fx.write_audit()  # (iv) stays consistent; only OpenML's own md5 can catch this
    fx.repin()
    with pytest.raises(M.MechanismStop, match='cache ARFF md5'):
        fx.prepare()


def test_metadata_md5_self_inconsistency_is_a_stop(fx):
    cache = fx.cache('openml_sonar')
    rel = fx.rels['openml_sonar']['metadata']
    doc = json.loads(gzip.decompress((cache / rel).read_bytes()))
    doc['data_set_description']['md5_checksum'] = '0' * 32
    _write_gz(cache / rel, json.dumps(doc).encode())
    fx.write_audit()
    fx.repin()
    with pytest.raises(M.MechanismStop, match='cache ARFF md5'):
        fx.prepare()


def test_metadata_dataset_id_mismatch_is_a_stop(fx):
    cache = fx.cache('openml_wdbc')
    rel = fx.rels['openml_wdbc']['metadata']
    doc = json.loads(gzip.decompress((cache / rel).read_bytes()))
    doc['data_set_description']['id'] = '1511'
    _write_gz(cache / rel, json.dumps(doc).encode())
    fx.write_audit()
    fx.repin()
    with pytest.raises(M.MechanismStop, match='cache metadata id'):
        fx.prepare()


# ---------------------------------------------------------------------------- (iv) unchanged bytes

def test_tampered_cache_file_is_a_stop(fx):
    (fx.cache('openml_breast_w') / fx.rels['openml_breast_w']['features']).write_bytes(b'changed')
    with pytest.raises(M.MechanismStop, match='cache file SHA-256 differs'):
        fx.prepare()


def test_missing_cache_file_is_a_stop(fx):
    (fx.cache('openml_wdbc') / fx.rels['openml_wdbc']['qualities']).unlink()
    with pytest.raises(M.MechanismStop, match='cache file set differs'):
        fx.prepare()


def test_unexpected_cache_file_is_a_stop(fx):
    (fx.cache('openml_breast_w') / 'openml/extra.bin').write_bytes(b'x')
    with pytest.raises(M.MechanismStop, match='cache file set differs'):
        fx.prepare()


def test_tree_digest_tamper_with_unchanged_per_file_set_is_a_stop(fx):
    # A permitted dotfile is outside the per-file map but inside the tree digest.
    (fx.cache('openml_breast_w') / '.gitignore').write_text('openml/\n')
    with pytest.raises(M.MechanismStop, match='cache tree digest'):
        fx.prepare()


def test_cache_symlink_is_a_stop(fx):
    target = fx.cache('openml_breast_w') / fx.rels['openml_breast_w']['features']
    real = target.read_bytes()
    target.unlink()
    (fx.cache('openml_breast_w') / 'elsewhere.gz').write_bytes(real)
    target.symlink_to(fx.cache('openml_breast_w') / 'elsewhere.gz')
    with pytest.raises(M.MechanismStop, match='symlink or irregular'):
        fx.prepare()


def test_tree_digest_matches_the_driver_algorithm(fx):
    for node in NODES:
        assert M.tree_digest(fx.cache(node)) == R.tree_digest(fx.cache(node))


# ---------------------------------------------------------------------------- sweep-1 record pin

def test_audit_pin_mismatch_is_a_stop(fx, monkeypatch):
    monkeypatch.setattr(M, 'AUDIT_SHA256', '0' * 64)
    with pytest.raises(M.MechanismStop, match='is not the reviewed'):
        M.load_audit(fx.paper)


def test_missing_audit_is_a_stop(fx):
    fx.audit_path.unlink()
    with pytest.raises(M.MechanismStop, match='unreadable'):
        M.load_audit(fx.paper)


def test_cache_check_mtime_after_launch_is_a_stop(fx):
    stamp = datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp()
    os.utime(fx.cache_check_path, (stamp, stamp))
    with pytest.raises(M.MechanismStop, match='mtime'):
        fx.prepare()


def test_cache_check_is_not_the_reviewed_record_is_a_stop(fx, monkeypatch):
    monkeypatch.setattr(M, 'CACHE_CHECK_SHA256', '0' * 64)
    with pytest.raises(M.MechanismStop, match='not the reviewed sweep-1 record'):
        fx.prepare()


def test_wrong_batch_path_is_a_stop(fx, tmp_path):
    other = tmp_path / 'other_batch'
    shutil.copytree(fx.batch, other)
    with pytest.raises(M.MechanismStop, match='audit batch'):
        M.prepare(fx.paper, fx.harness, other, fx.commit, fingerprint_loader=fx.loader,
                  versions_probe=fx.versions)


# ---------------------------------------------------------------------------- before/after use

def test_before_and_after_checks_pass_on_unchanged_bytes(fx, tmp_path):
    mechanism = fx.prepare()
    assert set(mechanism.verify_source_caches(fx.harness)) == set(NODES)
    copy = tmp_path / 'case_copy'
    shutil.copytree(fx.cache('openml_climate'), copy)
    before = mechanism.verify_case_cache('openml_climate', copy, 'before')
    after = mechanism.verify_case_cache('openml_climate', copy, 'after')
    assert before['phase'] == 'before' and after['phase'] == 'after'
    assert before['tree_digest'] == mechanism.report['nodes']['openml_climate']['cache_tree_digest']
    assert before['arff_md5'] == fx.arff['openml_climate']['md5_checksum']


def test_tamper_after_use_of_the_case_copy_is_a_stop(fx, tmp_path):
    mechanism = fx.prepare()
    copy = tmp_path / 'case_copy'
    shutil.copytree(fx.cache('openml_sonar'), copy)
    mechanism.verify_case_cache('openml_sonar', copy, 'before')
    (copy / fx.rels['openml_sonar']['features']).write_bytes(b'changed during the worker run')
    with pytest.raises(M.MechanismStop, match='after-use cache copy differs'):
        mechanism.verify_case_cache('openml_sonar', copy, 'after')


def test_tampered_source_cache_after_the_replay_is_a_stop(fx):
    mechanism = fx.prepare()
    (fx.cache('openml_wdbc') / fx.rels['openml_wdbc']['features']).write_bytes(b'changed')
    with pytest.raises(M.MechanismStop, match='source cache changed during the replay'):
        mechanism.verify_source_caches(fx.harness)


def test_unverified_node_is_refused_by_the_case_check(fx, tmp_path):
    mechanism = fx.prepare()
    with pytest.raises(M.MechanismStop, match='not part of the verified'):
        mechanism.verify_case_cache('openml_other', tmp_path, 'before')


# ---------------------------------------------------------------------------- the real reviewed audit

def test_the_committed_audit_is_the_reviewed_one():
    repo = R.Path(R.__file__).resolve().parents[2]
    path = repo / M.AUDIT_REL
    if not path.is_file():
        pytest.skip('reviewed audit is not in this checkout')
    assert M.file_sha256(path) == M.AUDIT_SHA256
    audit = M.load_audit(repo)
    assert audit['pinned_harness']['commit'] == R.HARNESS_COMMIT
    assert audit['sweep1_batch_records']['files']['cache_check.json']['sha256'] == M.CACHE_CHECK_SHA256
    assert audit['sweep1_batch_records']['files']['cache_check.json']['mtime_utc'] == M.CACHE_CHECK_MTIME_UTC
    assert set(audit['current_cache_observation']['per_file_sha256']) == set(M.OPENML_IDS)
    for node, dataset_id in M.OPENML_IDS.items():
        assert audit['pinned_harness']['node_specs'][node]['dataset_id'] == dataset_id
        description = audit['current_cache_observation']['openml_self_description'][node]
        assert description['openml_md5_checksum'] == description['uncompressed_arff_md5']
        assert len(description['openml_md5_checksum']) == 32
