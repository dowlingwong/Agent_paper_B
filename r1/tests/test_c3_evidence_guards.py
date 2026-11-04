import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from r1.c3 import audit, dataset

FAKE_ENV = {'worker_python': '/venv/bin/python', 'worker_prefix': '/venv',
            'worker_versions': {'scikit-learn': '1.8.0', 'numpy': '2.4.4',
                                'scipy': '1.17.1', 'pandas': '3.0.3'}, 'package_list_sha256': 'hash'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classification_fixture(tmp_path):
    index_rel = 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json'
    auth_rel = 'docs/r1/authorizations/c3_sweep1_20261027.md'
    side_rel = 'docs/r1/reports/classification.json'
    for name in (index_rel, auth_rel, side_rel):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
    pins = {'paper_commit': 'ccb47128aad82e331f79df4a893dbc1ee7e42f51',
            'harness_commit': '6adf3859de66c4814fcf376eed59880fbd8eeaf7',
            'config_sha256': '2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b',
            'model_sha256': '509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c',
            'llamacpp_build': 'version: 0.7.0-dev (build 1, commit 620d222)'}
    (tmp_path / auth_rel).write_text(' '.join(pins.values()))
    sweeps, bindings = [], []
    for mode in ('append_only_summary', 'none'):
        old = f'results/r1/pilot/C3_sweep_{mode}'
        new = f'results/r1/evidence/C3_sweep_{mode}'
        (tmp_path / new).mkdir(parents=True)
        manifest = tmp_path / new / 'manifest.json'
        manifest.write_text(json.dumps({'label': 'PILOT', 'memory_mode': mode, 'launch_provenance': pins}))
        sweeps.append({'memory_mode': mode, 'out': old, 'manifest': old + '/manifest.json',
                       'ledgers': old + '/provenance/ledgers/roots'})
        bindings.append({'memory_mode': mode, 'old_dir': old, 'new_dir': new, 'manifest_sha256': sha(manifest)})
    nodes = ['digits_mlp', 'tabular_mlp', 'openml_breast_w', 'openml_ionosphere', 'openml_wdbc',
             'openml_credit_approval', 'openml_sonar', 'openml_climate']
    (tmp_path / index_rel).write_text(json.dumps({'sweeps': sweeps, 'label': 'ENGINEERING_ONLY',
        'launch_provenance': pins, 'nodes': nodes, 'excluded_nodes': [], 'instances': 18, 'runs': 20,
        'manager': {'proposal_schema': 'manager_proposal/v1'},
        'audit': {'seeds': list(range(7001, 7011)), 'label_seeds': list(range(7001, 7006)),
                  'evaluation_seeds': list(range(7006, 7011))}}))
    side = {'schema': 'r1.c3_classification/1', 'label': 'EVIDENCE', 'decision_id': 'R1-SWEEP1-CLASSIFY',
            'authorization': {'path': auth_rel, 'sha256': sha(tmp_path / auth_rel)},
            'index': {'path': index_rel, 'sha256': sha(tmp_path / index_rel)}, 'sweeps': bindings}
    (tmp_path / side_rel).write_text(json.dumps(side))
    (tmp_path / 'docs/r1/PLAN.md').write_text(
        f'| R1-SWEEP1-CLASSIFY (28 Oct) | EVIDENCE {index_rel} {side["index"]["sha256"]} '
        f'{auth_rel} {side_rel} {sha(tmp_path / side_rel)} |\n')
    return tmp_path / index_rel, tmp_path / side_rel, side


def test_evidence_classification_requires_bound_authority_and_unchanged_files(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, '_verify_published', lambda *args: None)
    monkeypatch.setattr(dataset, '_verify_original_blobs', lambda *args: None)
    index, sidecar, data = classification_fixture(tmp_path)
    assert dataset.evidence_classification(index, tmp_path, sidecar)['label'] == 'EVIDENCE'
    (tmp_path / data['sweeps'][0]['new_dir'] / 'manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='manifest hash'):
        dataset.evidence_classification(index, tmp_path, sidecar)


def test_evidence_classification_rejects_unapproved_or_unsafe_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, '_verify_published', lambda *args: None)
    monkeypatch.setattr(dataset, '_verify_original_blobs', lambda *args: None)
    index, sidecar, data = classification_fixture(tmp_path)
    (tmp_path / 'docs/r1/PLAN.md').write_text('| R1-SWEEP1-CLASSIFY | EVIDENCE |\n')
    with pytest.raises(ValueError, match='PLAN'):
        dataset.evidence_classification(index, tmp_path, sidecar)
    with pytest.raises(ValueError, match='repository-relative'):
        dataset._safe_relative(tmp_path, '../outside')


def test_evidence_audit_rejects_missing_failed_and_nonfinite_seeds(tmp_path):
    plan = [{'proposal_id': 'x', 'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'i'}]
    cache = audit.RunCache(tmp_path / 'runs.jsonl')
    rows = [{'node': 'n', 'config_hash': h, 'seed': s, 'success': True, 'changed_files': False,
             'metric': float(s), 'wall_seconds': 1} for h in ('c', 'i') for s in audit.DEFAULT_SEEDS]
    cache.add(rows[:-1])
    with pytest.raises(ValueError, match='invalid evidence'):
        audit.validate_evidence_results(plan, cache)
    cache.add(rows[-1:])
    assert len(audit.validate_evidence_results(plan, cache)) == 1
    cache.add([{**rows[-1], 'success': False}])
    with pytest.raises(ValueError, match='invalid evidence'):
        audit.validate_evidence_results(plan, cache)


def test_evidence_plan_covers_all_and_rejects_stale_table(tmp_path, monkeypatch):
    index, sidecar, _ = classification_fixture(tmp_path)
    monkeypatch.setattr(dataset, 'evidence_classification', lambda *args: {'label': 'EVIDENCE'})
    monkeypatch.setattr(audit, '_verify_replay', lambda *args: None)
    table = tmp_path / 'table'
    table.mkdir()
    base = {'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'i'}
    rows = [{**base, 'proposal_id': 'a', 'noop': False, 'noop_kind': None, 'duplicate': False,
             'features': {'active_key': True, 'cfg_equals_incumbent': False}},
            {**base, 'proposal_id': 'b', 'noop': False, 'noop_kind': None, 'duplicate': True,
             'features': {'active_key': True, 'cfg_equals_incumbent': False}},
            {**base, 'proposal_id': 'c', 'noop': True, 'noop_kind': 'incumbent_repeat', 'duplicate': False,
             'features': {'active_key': True, 'cfg_equals_incumbent': True}}]
    (table / 'proposals.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    (table / 'configs.json').write_text(json.dumps({'c': {'files': {}}, 'i': {'files': {}}}))
    metadata = {'label': 'EVIDENCE', 'classification': {'sha256': sha(sidecar)},
                'sweep_index': {'sha256': sha(index)},
                'table_sha256': {n: sha(table / n) for n in ('proposals.jsonl', 'configs.json')}}
    (table / 'build.json').write_text(json.dumps(metadata))
    planned, binding = audit.evidence_plan(table, tmp_path, index, sidecar)
    assert [p['proposal_id'] for p in planned] == ['a']
    assert binding['counts'] == {'eligible': 1, 'noops': 1, 'duplicates': 1}
    (table / 'proposals.jsonl').write_text('')
    with pytest.raises(ValueError, match='contents differ'):
        audit.evidence_plan(table, tmp_path, index, sidecar)


def test_evidence_audit_refuses_existing_output_even_without_cache(tmp_path, monkeypatch):
    # Test downstream path protection independently of the real entry STOP.
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: ([{'proposal_id': 'a'}], {}))
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: dict(FAKE_ENV))
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {})
    monkeypatch.setattr(audit, 'evidence_resources', lambda *args: {})
    monkeypatch.setattr(audit, 'monitor_evidence_resources', lambda *args: {})
    existing = tmp_path / 'previous'
    existing.mkdir()
    (existing / 'runs.jsonl').write_text('pilot data\n')
    with pytest.raises(ValueError, match='new dedicated'):
        audit.evidence_run(tmp_path, tmp_path, tmp_path, tmp_path, existing, 1, 30, scratch_root=tmp_path / 'scratch')
    assert (existing / 'runs.jsonl').read_text() == 'pilot data\n'


def test_evidence_output_rejects_symlink_and_overlapping_sweep(tmp_path):
    evidence = tmp_path / 'results/r1/evidence'
    evidence.mkdir(parents=True)
    target = tmp_path / 'old_batch'
    target.mkdir()
    (evidence / 'C3_audit_EVIDENCE_old').symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        audit.evidence_output_path(tmp_path, evidence / 'C3_audit_EVIDENCE_old')
    with pytest.raises(ValueError, match='new dedicated'):
        audit.evidence_output_path(tmp_path, target / 'C3_audit_EVIDENCE_new')


def test_original_sweep_blob_verification_detects_altered_or_added_file(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    old, new = 'results/r1/pilot/sweep', 'results/r1/evidence/sweep'
    source = tmp_path / old
    source.mkdir(parents=True)
    (source / 'root.json').write_text('original')
    subprocess.run(['git', '-C', str(tmp_path), 'add', old], check=True)
    subprocess.run(['git', '-C', str(tmp_path), '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                    'commit', '-qm', 'fixture'], check=True)
    commit = subprocess.check_output(['git', '-C', str(tmp_path), 'rev-parse', 'HEAD'], text=True).strip()
    dest = tmp_path / new
    dest.parent.mkdir(parents=True)
    source.rename(dest)
    index = {'sweeps': [{'memory_mode': 'none', 'commit': commit}]}
    bindings = [{'memory_mode': 'none', 'old_dir': old, 'new_dir': new}]
    dataset._verify_original_blobs(tmp_path, index, bindings)
    (dest / 'root.json').write_text('modified')
    with pytest.raises(ValueError, match='differs from original'):
        dataset._verify_original_blobs(tmp_path, index, bindings)


def test_published_authority_rejects_unpublished_changes(tmp_path, monkeypatch):
    f = tmp_path / 'authority'
    f.write_text('local modified')
    def fake(cmd, **kwargs):
        if 'ls-remote' in cmd:
            return b'abc refs/heads/main\n'
        if 'rev-parse' in cmd:
            return b'abc\n'
        return b'published'
    monkeypatch.setattr(dataset.subprocess, 'check_output', fake)
    with pytest.raises(ValueError, match='published'):
        dataset._verify_published(tmp_path, ['authority'])


def test_first_worker_failure_stops_new_dispatch_and_preserves_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    table = tmp_path / 'table'
    table.mkdir()
    (table / 'configs.json').write_text(json.dumps({h: {'files': {}} for h in ('a', 'b', 'c')}))
    plan = [{'node': 'n', 'candidate_hash': 'a', 'incumbent_hash': 'b'},
            {'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'a'}]
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: dict(FAKE_ENV))
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {'paper_code_commit': 'fixture'})
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: (plan, {'counts': {}}))
    monkeypatch.setattr(audit, 'evidence_resources', lambda *args: {})
    monkeypatch.setattr(audit, 'monitor_evidence_resources', lambda *args: {})
    submitted = []
    class Future:
        def __init__(self, node, h): self.node, self.h = node, h
        def result(self):
            return [{'seed': 7001, 'success': False, 'changed_files': False, 'metric': None, 'wall_seconds': 1}]
    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def submit(self, func, node, files, seeds, scratch, stop, journal, identity):
            submitted.append(node)
            assert identity['node'] == node and identity['config_hash'] in ('a', 'b', 'c')
            Path(journal).write_text('{"seed":7001,"success":false}\n')
            return Future(node, len(submitted))
    monkeypatch.setattr(audit, 'ProcessPoolExecutor', Pool)
    monkeypatch.setattr(audit, 'wait', lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / 'results/r1/evidence/C3_audit_EVIDENCE_test'
    with pytest.raises(ValueError, match='STOP'):
        audit.evidence_run(table, tmp_path, tmp_path, tmp_path, out, 1, 300, scratch_root=tmp_path / 'scratch')
    assert len(submitted) == 1
    assert (out / 'STOP.json').exists() and (out / 'runs.jsonl').exists()
    assert list((out / 'seed_journals').glob('*.jsonl'))
    scratch = Path(json.loads((out / 'scratch.json').read_text())['scratch'])
    assert scratch.is_dir()
    # Synthetic test cleanup only; production retains STOP scratch.
    import shutil
    shutil.rmtree(scratch)
    assert not (out / 'evidence_completion.json').exists()


@pytest.mark.parametrize('failure', ['validation', 'completion_write'])
def test_final_failure_keeps_scratch_and_writes_stop(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    table = tmp_path / 'table'
    table.mkdir()
    (table / 'configs.json').write_text(json.dumps({h: {'files': {}} for h in ('a', 'b')}))
    (table / 'build.json').write_text('{}')
    (table / 'proposals.jsonl').write_text('{}\n')
    auth = tmp_path / 'docs/r1/authorizations/c3_sweep1_20261027.md'
    auth.parent.mkdir(parents=True)
    auth.write_text('auth')
    index, classification = tmp_path / 'index', tmp_path / 'classification'
    index.write_text('index')
    classification.write_text('classification')
    plan = [{'proposal_id': 'p', 'node': 'n', 'candidate_hash': 'a', 'incumbent_hash': 'b'}]
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: dict(FAKE_ENV))
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {'paper_code_commit': 'fixture'})
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: (plan, {'counts': {'eligible': 1}}))
    monkeypatch.setattr(audit, 'evidence_resources', lambda *args: {})
    monkeypatch.setattr(audit, 'monitor_evidence_resources', lambda *args: {})
    class Future:
        def result(self):
            return [{'seed': s, 'success': True, 'changed_files': False, 'metric': float(s), 'wall_seconds': 1}
                    for s in audit.DEFAULT_SEEDS]
    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def submit(self, *args): return Future()
    monkeypatch.setattr(audit, 'ProcessPoolExecutor', Pool)
    monkeypatch.setattr(audit, 'wait', lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    monkeypatch.setattr(audit, 'evidence_blocks', lambda *args: ([{'proposal_id': 'p'}], [{'proposal_id': 'p'}]))
    monkeypatch.setattr(audit, 'validate_worker_records', lambda *args: None)
    if failure == 'validation':
        monkeypatch.setattr(audit, 'evidence_cache', lambda *args: (_ for _ in ()).throw(ValueError('bad cache')))
    else:
        original = Path.write_text
        def write(path, *args, **kwargs):
            if path.name == '.evidence_completion.tmp':
                raise OSError('disk full')
            return original(path, *args, **kwargs)
        monkeypatch.setattr(Path, 'write_text', write)
    out = tmp_path / 'results/r1/evidence/C3_audit_EVIDENCE_test'
    scratch = tmp_path / 'scratch'
    with pytest.raises((ValueError, OSError)):
        audit.evidence_run(table, tmp_path, index, classification, out, 1, 300, scratch_root=scratch)
    assert (out / 'STOP.json').exists() and (scratch / 'STOP.json').exists()
    assert not (out / 'evidence_completion.json').exists()


def test_resource_floor_stops_dispatch_and_drains_inflight(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    table = tmp_path / 'table'
    table.mkdir()
    (table / 'configs.json').write_text(json.dumps({h: {'files': {}} for h in ('a', 'b', 'c')}))
    plan = [{'node': 'n', 'candidate_hash': 'a', 'incumbent_hash': 'b'},
            {'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'a'}]
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: dict(FAKE_ENV))
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {})
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: (plan, {'counts': {}}))
    monkeypatch.setattr(audit, 'evidence_resources', lambda *args: {})
    checks = []
    def monitor(*args):
        checks.append(1)
        if len(checks) > 1:
            raise ValueError('Ceph floor')
        return {}
    monkeypatch.setattr(audit, 'monitor_evidence_resources', monitor)
    import itertools
    clock = itertools.count(0, 31)
    monkeypatch.setattr(audit.time, 'monotonic', lambda: next(clock))
    submitted, completed = [], []
    class Future:
        def result(self):
            completed.append(1)
            return [{'seed': s, 'success': True, 'changed_files': False, 'metric': float(s), 'wall_seconds': 1}
                    for s in audit.DEFAULT_SEEDS]
    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def submit(self, *args):
            submitted.append(1)
            return Future()
    monkeypatch.setattr(audit, 'ProcessPoolExecutor', Pool)
    monkeypatch.setattr(audit, 'wait', lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / 'results/r1/evidence/C3_audit_EVIDENCE_test'
    with pytest.raises(ValueError, match='resource monitoring STOP'):
        audit.evidence_run(table, tmp_path, tmp_path, tmp_path, out, 2, 10000, scratch_root=tmp_path / 'scratch')
    assert len(submitted) == 2 and len(completed) == 2
    assert (out / 'STOP.json').exists() and not (out / 'evidence_completion.json').exists()


def test_stop_falls_back_to_local_scratch_when_output_write_fails(tmp_path, monkeypatch):
    out, scratch = tmp_path / 'out', tmp_path / 'scratch'
    out.mkdir()
    original = Path.write_text
    def write(path, *args, **kwargs):
        if path == out / 'STOP.json':
            raise OSError('Ceph unavailable')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'write_text', write)
    with pytest.raises(ValueError, match='failure'):
        with audit.evidence_scratch(out, scratch, {'paper_code_commit': 'fixture'}):
            raise ValueError('failure')
    assert (scratch / 'STOP.json').is_file()
    assert not (out / 'STOP.json').exists()


def test_replay_detects_deleted_rows_despite_self_signed_table(tmp_path, monkeypatch):
    table = tmp_path / 'source'
    table.mkdir()
    (table / 'proposals.jsonl').write_text('deleted\n')
    (table / 'configs.json').write_text('{}')
    def fake_build(index, out, **kwargs):
        out.mkdir()
        (out / 'proposals.jsonl').write_text('complete\n')
        (out / 'configs.json').write_text('{}')
    monkeypatch.setattr(dataset, 'build_from_sweep', fake_build)
    monkeypatch.setattr(audit, '_local_scratch_mount', lambda p: ['xfs', 'local'])
    with pytest.raises(ValueError, match='full source replay'):
        audit._verify_replay(table, tmp_path, tmp_path, tmp_path)


def test_evidence_environment_rejects_dirty_harness(tmp_path, monkeypatch):
    monkeypatch.setenv('AR_HARNESS_ROOT', str(tmp_path))
    monkeypatch.setattr(audit, 'original_sweep_environment', lambda *a: ({'python': audit.sys.version, 'packages': {}}, 'p', 'h'))
    monkeypatch.setattr(audit.import_metadata, 'distributions', lambda: [])
    def fake(cmd, **kwargs):
        if 'rev-parse' in cmd:
            return '6adf3859de66c4814fcf376eed59880fbd8eeaf7\n'
        return ' M dirty.py\n'
    monkeypatch.setattr(audit.subprocess, 'check_output', fake)
    with pytest.raises(ValueError, match='dirty'):
        audit.evidence_environment(tmp_path, tmp_path)


def test_missing_original_environment_fails_closed(tmp_path):
    with pytest.raises(ValueError, match='original sweep full environment record missing'):
        audit.original_sweep_environment(tmp_path, None)


def test_resource_checks_reject_infinite_deadline_and_too_many_workers(tmp_path):
    with pytest.raises(ValueError, match='finite'):
        audit.evidence_resources([], 1, float('inf'), tmp_path, 1, 1)
    with pytest.raises(ValueError, match='workers'):
        audit.evidence_resources([], 17, 300, tmp_path, 1, 1)


def test_resource_checks_reject_ceph_scratch_mount(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'is_symlink', lambda self: False)
    monkeypatch.setattr(audit.subprocess, 'check_output', lambda *a, **k: 'ceph cephfs\n')
    with pytest.raises(ValueError, match='not verified local'):
        audit.evidence_resources([], 1, 300, Path('/tmp/r1_c3_audit_EVIDENCE_missing'), 1, 20)


def _hide_loaded_harness_modules(monkeypatch):
    # Other tests in the same session may already have imported the real harness;
    # those modules would trip the import check before the condition under test.
    for name in [n for n in audit.sys.modules if n == 'autoresearch' or n.startswith('autoresearch.')]:
        monkeypatch.delitem(audit.sys.modules, name)


def test_evidence_environment_rejects_harness_import_spoof(tmp_path, monkeypatch):
    import types
    from r1 import harness
    monkeypatch.setenv('AR_HARNESS_ROOT', str(tmp_path / 'harness'))
    monkeypatch.setattr(audit, 'original_sweep_environment', lambda *a: ({'python': audit.sys.version, 'packages': {}}, 'p', 'h'))
    monkeypatch.setattr(audit.import_metadata, 'distributions', lambda: [])
    monkeypatch.setattr(audit.subprocess, 'check_output',
        lambda cmd, **kw: '6adf3859de66c4814fcf376eed59880fbd8eeaf7\n' if 'rev-parse' in cmd else '')
    # Patch the module object, and patch importlib.import_module last: audit.importlib is the
    # global importlib, and pytest resolves dotted monkeypatch targets with import_module.
    monkeypatch.setattr(harness, 'import_harness', lambda: tmp_path)
    _hide_loaded_harness_modules(monkeypatch)
    monkeypatch.setattr(audit.importlib, 'import_module', lambda name: None)
    fake = types.ModuleType('autoresearch')
    fake.__file__ = str(tmp_path / 'spoofed.py')
    monkeypatch.setitem(audit.sys.modules, 'autoresearch', fake)
    with pytest.raises(ValueError, match='outside pinned checkout'):
        audit.evidence_environment(tmp_path, tmp_path)


def test_evidence_environment_rejects_wrong_locked_sklearn(tmp_path, monkeypatch):
    monkeypatch.setenv('AR_HARNESS_ROOT', str(tmp_path))
    monkeypatch.setattr(audit, 'original_sweep_environment', lambda *a: ({'python': audit.sys.version, 'packages': {}}, 'p', 'h'))
    monkeypatch.setattr(audit.import_metadata, 'distributions', lambda: [])
    (tmp_path / 'uv.lock').write_text('[[package]]\nname="scikit-learn"\nversion="1.8.0"\n')
    monkeypatch.setattr(audit.subprocess, 'check_output',
        lambda cmd, **kw: '6adf3859de66c4814fcf376eed59880fbd8eeaf7\n' if 'rev-parse' in cmd else '')
    monkeypatch.setattr(audit.import_metadata, 'version', lambda name: '1.7.0')
    # Stub actual harness imports; the version mismatch remains fail-closed.
    from r1 import harness
    monkeypatch.setattr(harness, 'import_harness', lambda: tmp_path)
    _hide_loaded_harness_modules(monkeypatch)
    monkeypatch.setattr(audit.importlib, 'import_module', lambda name: None)
    with pytest.raises(ValueError, match='sklearn'):
        audit.evidence_environment(tmp_path, tmp_path)


def test_evidence_paper_provenance_rejects_wrong_checkout(tmp_path, monkeypatch):
    def fake(cmd, **kwargs):
        if 'ls-remote' in cmd:
            return b'a' * 40 + b' refs/heads/main\n'
        if 'rev-parse' in cmd:
            return b'b' * 40 + b'\n'
        return b''
    monkeypatch.setattr(audit.subprocess, 'check_output', fake)
    with pytest.raises(ValueError, match='HEAD or published'):
        audit.evidence_paper_provenance(tmp_path, 'a' * 40, 'docs/r1/reviews/review.md')


def test_evidence_paper_provenance_rejects_dirty_code(tmp_path, monkeypatch):
    def fake(cmd, **kwargs):
        if 'ls-remote' in cmd:
            return b'a' * 40 + b' refs/heads/main\n'
        if 'rev-parse' in cmd:
            return b'a' * 40 + b'\n'
        if 'status' in cmd:
            return b' M r1/c3/audit.py\n'
        return b''
    monkeypatch.setattr(audit.subprocess, 'check_output', fake)
    monkeypatch.setattr(audit.subprocess, 'run', lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match='tracked or untracked'):
        audit.evidence_paper_provenance(tmp_path, 'a' * 40, 'docs/r1/reviews/review.md')


def test_published_authority_rejects_stale_remote(tmp_path, monkeypatch):
    f = tmp_path / 'authority'
    f.write_text('content')
    def fake(cmd, **kwargs):
        return b'new refs/heads/main\n' if 'ls-remote' in cmd else b'old\n'
    monkeypatch.setattr(dataset.subprocess, 'check_output', fake)
    with pytest.raises(ValueError, match='stale'):
        dataset._verify_published(tmp_path, ['authority'])


def test_evidence_cache_rejects_duplicate_and_unexpected_rows(tmp_path):
    plan = [{'proposal_id': 'x', 'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'i'}]
    path = tmp_path / 'runs.jsonl'
    one = {'node': 'n', 'config_hash': 'c', 'seed': 7001}
    path.write_text(json.dumps(one) + '\n' + json.dumps(one) + '\n')
    with pytest.raises(ValueError, match='duplicate or unexpected'):
        audit.evidence_cache(plan, path)
    path.write_text(json.dumps({**one, 'seed': 7011}) + '\n')
    with pytest.raises(ValueError, match='duplicate or unexpected'):
        audit.evidence_cache(plan, path)


@pytest.mark.parametrize('role', ['label', 'evaluation'])
def test_completion_rejects_rewritten_audit_even_if_digest_recomputed(tmp_path, monkeypatch, role):
    # Exercise downstream digest checks with fixture-only attestation bypassed.
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    table = tmp_path / 'table'
    table.mkdir()
    for name in ('build.json', 'proposals.jsonl', 'configs.json'):
        (table / name).write_text('{}')
    auth = tmp_path / 'docs/r1/authorizations/c3_sweep1_20261027.md'
    auth.parent.mkdir(parents=True)
    auth.write_text('auth')
    index, classification = tmp_path / 'index', tmp_path / 'classification'
    index.write_text('index')
    classification.write_text('classification')
    plan = [{'proposal_id': 'x', 'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'i',
             'reason': 'full_population', 'inclusion_probability': 1.0}]
    counts = {'eligible': 1, 'noops': 0, 'duplicates': 0}
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: (plan, {'counts': counts}))
    out = tmp_path / 'audits'
    out.mkdir()
    (out / 'plan.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in plan))
    cache = audit.RunCache(out / 'runs.jsonl')
    runtime = {'worker_python': FAKE_ENV['worker_python'], 'prefix': FAKE_ENV['worker_prefix'],
               'base_prefix': '/base', 'versions': FAKE_ENV['worker_versions'],
               'package_list_sha256': FAKE_ENV['package_list_sha256'], 'worker_command_python': '/wrapper/python3',
               'worker_python_realpath': '/system/python3'}
    cache.add([{'node': 'n', 'config_hash': h, 'seed': s, 'success': True,
                'changed_files': False, 'metric': float(s), 'wall_seconds': 1, 'worker_runtime': runtime}
               for h in ('c', 'i') for s in audit.DEFAULT_SEEDS])
    result = audit.validate_evidence_results(plan, cache)
    def blocks(_table, values):
        return ([{'proposal_id': 'x', 'delta_label': values[0]['delta_audit']}],
                [{'proposal_id': 'x', 'delta_evaluation': values[0]['delta_audit']}])
    monkeypatch.setattr(audit, 'evidence_blocks', blocks)
    labels, evaluations = blocks(table, result)
    (out / 'label_block.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in labels))
    (out / 'evaluation_block.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in evaluations))
    environment = {'harness_commit': '6adf3859de66c4814fcf376eed59880fbd8eeaf7', 'harness_dirty': False,
                   'scikit_learn': '1.8.0', 'python': '3.13.2', 'uv_lock_sha256': 'locked',
                   'paper_code_clean': True, 'paper_code_commit': 'a' * 40, 'review_path': 'docs/r1/reviews/test.md',
                   'sweep_environment_path': 'docs/r1/reports/env.json', 'sweep_environment_sha256': 'envhash',
                   **FAKE_ENV}
    monkeypatch.setattr(audit, 'original_sweep_environment', lambda *a: ({'python': '3.13.2'}, 'p', 'envhash'))
    review = b'Code-Commit: ' + b'a' * 40 + b'\nVerdict: ACCEPTED\n'
    environment['review_sha256'] = hashlib.sha256(review).hexdigest()
    monkeypatch.setattr(audit.subprocess, 'check_output',
        lambda cmd, **kw: 'published\n' if 'rev-parse' in cmd else review)
    monkeypatch.setattr(audit.subprocess, 'run', lambda *args, **kw: None)
    (out / 'environment.json').write_text(json.dumps(environment))
    (out / 'resources.json').write_text('{}')
    completion = {'schema': 'r1.c3_audit_completion/2', 'label': 'EVIDENCE',
        'authorization_sha256': sha(auth), 'classification_sha256': sha(classification), 'index_sha256': sha(index),
        'build_sha256': sha(table / 'build.json'), 'proposals_sha256': sha(table / 'proposals.jsonl'),
        'configs_sha256': sha(table / 'configs.json'), 'plan_sha256': sha(out / 'plan.jsonl'),
        'label_block_sha256': sha(out / 'label_block.jsonl'),
        'evaluation_block_sha256': sha(out / 'evaluation_block.jsonl'),
        'runs_sha256': sha(out / 'runs.jsonl'), 'per_run_worker_runtime': 'runs.jsonl:worker_runtime',
        'environment_sha256': sha(out / 'environment.json'), 'counts': counts,
        'resources_sha256': sha(out / 'resources.json'),
        'label_seeds': list(range(7001, 7006)), 'evaluation_seeds': list(range(7006, 7011))}
    (out / 'evidence_completion.json').write_text(json.dumps(completion))
    audit.verify_evidence_completion(table, out / 'label_block.jsonl', tmp_path, index, classification)
    target = out / f'{role}_block.jsonl'
    rewritten = labels[0] if role == 'label' else evaluations[0]
    rewritten['delta_label' if role == 'label' else 'delta_evaluation'] = 123
    target.write_text(json.dumps(rewritten) + '\n')
    completion[f'{role}_block_sha256'] = sha(target)
    (out / 'evidence_completion.json').write_text(json.dumps(completion))
    with pytest.raises(ValueError, match='raw seed results'):
        audit.verify_evidence_completion(table, out / 'label_block.jsonl', tmp_path, index, classification)
