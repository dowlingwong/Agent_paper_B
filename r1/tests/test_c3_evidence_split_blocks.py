import json

import pytest

from r1.c3 import audit, dataset


def test_blocks_keep_seed_roles_separate_and_handle_rules(monkeypatch, tmp_path):
    rows = [
        {'proposal_id': 'audit', 'node': 'n', 'noop': False, 'duplicate': False, 'sigma_node': 0.5},
        {'proposal_id': 'noop', 'node': 'n', 'noop': True, 'duplicate': False, 'sigma_node': 0.5},
        {'proposal_id': 'duplicate', 'node': 'n', 'noop': False, 'duplicate': True, 'sigma_node': 0.5},
    ]
    monkeypatch.setattr(dataset, 'load_table', lambda _: rows)
    results = [{'proposal_id': 'audit', 'node': 'n', 'seeds': list(range(7001, 7011)),
                'candidate_metrics': [float(x) for x in range(10)], 'incumbent_metrics': [0.0] * 10}]
    labels, evaluation = audit.evidence_blocks(tmp_path, results)
    assert [x['proposal_id'] for x in labels] == ['audit', 'noop']
    assert [x['proposal_id'] for x in evaluation] == ['audit']
    assert labels[0]['seeds'] == list(range(7001, 7006))
    assert evaluation[0]['seeds'] == list(range(7006, 7011))
    assert labels[0]['delta_label'] == 2.0 and evaluation[0]['delta_evaluation'] == 7.0
    assert labels[0]['soft_parameters']['k_label'] == 5
    assert labels[1]['label_kind'] == 'rule_noop' and labels[1]['soft_parameters']['inert']
    assert not any(str(s) in json.dumps(labels) for s in range(7006, 7011))
    with pytest.raises(ValueError, match='cover eligible'):
        audit.evidence_blocks(tmp_path, [])
    with pytest.raises(ValueError, match='duplicate proposal ID'):
        audit.evidence_blocks(tmp_path, results + results)


def test_worker_probe_uses_worker_path_and_rejects_mismatch(monkeypatch):
    expected = {'worker_python': '/shared/venv/bin/python3', 'worker_prefix': '/shared/venv',
                'worker_versions': {'scikit-learn': '1.8.0', 'numpy': '2.4.4',
                                    'pandas': '3.0.3', 'scipy': '1.17.1'}, 'package_list_sha256': 'abc'}
    observed = {'worker_python': expected['worker_python'], 'prefix': expected['worker_prefix'],
                'base_prefix': '/system', 'versions': expected['worker_versions'], 'package_list_sha256': 'abc',
                'worker_python_realpath': '/system/python3'}
    seen = []
    monkeypatch.setattr(audit.shutil, 'which', lambda name, path: '/batch/.venv/bin/python3')
    def probe(cmd, **kwargs):
        seen.append((cmd, kwargs['env']))
        return json.dumps(observed)
    monkeypatch.setattr(audit.subprocess, 'check_output', probe)
    env = {'PATH': '/batch/.venv/bin', 'AR_TRAIN_SEED': '7001'}
    result = audit.worker_runtime(expected, 'python3 train.py --config config.yaml', env)
    assert seen[0][0][:2] == ['/batch/.venv/bin/python3', '-B'] and seen[0][1] == env
    assert result['worker_command_python'] == '/batch/.venv/bin/python3'
    observed['worker_python'] = '/anaconda/bin/python3'
    with pytest.raises(ValueError, match='mismatch'):
        audit.worker_runtime(expected, 'python3 train.py', env)
    observed['worker_python'] = expected['worker_python']
    observed['prefix'] = observed['base_prefix']
    with pytest.raises(ValueError, match='mismatch'):
        audit.worker_runtime(expected, 'python3 train.py', env)
    with pytest.raises(ValueError, match='direct python3'):
        audit.worker_runtime(expected, 'python3 train.py; echo bad', env)


def test_each_raw_run_must_carry_matching_venv_and_versions(tmp_path):
    expected = {'worker_python': '/shared/venv/bin/python3', 'worker_prefix': '/shared/venv',
                'worker_versions': {'scikit-learn': '1.8.0', 'numpy': '2.4.4',
                                    'pandas': '3.0.3', 'scipy': '1.17.1'}, 'package_list_sha256': 'abc'}
    runtime = {'worker_python': expected['worker_python'], 'prefix': expected['worker_prefix'],
               'base_prefix': '/system', 'versions': expected['worker_versions'],
               'package_list_sha256': 'abc', 'worker_command_python': '/batch/wrapper/python3',
               'worker_python_realpath': '/system/python3'}
    path = tmp_path / 'runs.jsonl'
    path.write_text(json.dumps({'seed': 7001, 'worker_runtime': runtime}) + '\n')
    audit.validate_worker_records(path, expected)
    path.write_text(json.dumps({'seed': 7001, 'worker_runtime': runtime}) + '\n' +
                    json.dumps({'seed': 7002}) + '\n')
    with pytest.raises(ValueError, match='worker runtime'):
        audit.validate_worker_records(path, expected)
    runtime['versions'] = {**runtime['versions'], 'scikit-learn': '1.5.1'}
    path.write_text(json.dumps({'seed': 7001, 'worker_runtime': runtime}) + '\n')
    with pytest.raises(ValueError, match='worker runtime'):
        audit.validate_worker_records(path, expected)


def test_synthetic_evidence_audit_writes_distinct_hashed_blocks(tmp_path, monkeypatch):
    # Fixture verifies block semantics only; real EVIDENCE is still blocked.
    monkeypatch.setattr(audit, '_require_task_native_runtime_attestation', lambda: None)
    table = tmp_path / 'table'
    table.mkdir()
    for name, data in [('build.json', '{}'), ('proposals.jsonl', '{}\n'),
                       ('configs.json', json.dumps({'c': {'files': {}}, 'i': {'files': {}}}))]:
        (table / name).write_text(data)
    auth = tmp_path / 'docs/r1/authorizations/c3_sweep1_20261027.md'
    auth.parent.mkdir(parents=True)
    auth.write_text('test authorization')
    index, classification = tmp_path / 'index', tmp_path / 'classification'
    index.write_text('index')
    classification.write_text('classification')
    rows = [{'proposal_id': 'p', 'node': 'n', 'noop': False, 'duplicate': False, 'sigma_node': 0.5}]
    monkeypatch.setattr(dataset, 'load_table', lambda _: rows)
    plan = [{'proposal_id': 'p', 'node': 'n', 'candidate_hash': 'c', 'incumbent_hash': 'i'}]
    env = {'worker_python': '/venv/bin/python3', 'worker_prefix': '/venv',
           'worker_versions': {'scikit-learn': '1.8.0', 'numpy': '2.4.4',
                               'pandas': '3.0.3', 'scipy': '1.17.1'}, 'package_list_sha256': 'abc'}
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: dict(env))
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {})
    monkeypatch.setattr(audit, 'evidence_plan', lambda *args: (plan, {'counts': {'eligible': 1, 'noops': 0, 'duplicates': 0}}))
    monkeypatch.setattr(audit, 'evidence_resources', lambda *args: {})
    monkeypatch.setattr(audit, 'monitor_evidence_resources', lambda *args: {})
    class Future:
        def __init__(self, key): self.key = key
        def result(self):
            runtime = {'worker_python': env['worker_python'], 'prefix': env['worker_prefix'],
                       'base_prefix': '/system', 'versions': env['worker_versions'],
                       'package_list_sha256': env['package_list_sha256'], 'worker_command_python': '/wrapper/python3',
                       'worker_python_realpath': '/system/python3'}
            return [{'seed': s, 'success': True, 'changed_files': False,
                     'metric': float(s) + (1.0 if self.key == 'c' else 0.0),
                     'wall_seconds': 1.0, 'worker_runtime': runtime} for s in audit.DEFAULT_SEEDS]
    class Pool:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def submit(self, function, node, files, seeds, scratch, stop, journal, identity):
            return Future(identity['config_hash'])
    monkeypatch.setattr(audit, 'ProcessPoolExecutor', Pool)
    monkeypatch.setattr(audit, 'wait', lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / 'results/r1/evidence/C3_audit_EVIDENCE_fake'
    scratch = tmp_path / 'scratch'
    audit.evidence_run(table, tmp_path, index, classification, out, 1, 300, scratch_root=scratch)
    label = json.loads((out / 'label_block.jsonl').read_text())
    evaluation = json.loads((out / 'evaluation_block.jsonl').read_text())
    completion = json.loads((out / 'evidence_completion.json').read_text())
    assert label['seeds'] == list(range(7001, 7006))
    assert evaluation['seeds'] == list(range(7006, 7011))
    assert completion['label_block_sha256'] == audit._digest(out / 'label_block.jsonl')
    assert completion['evaluation_block_sha256'] == audit._digest(out / 'evaluation_block.jsonl')
    assert completion['per_run_worker_runtime'] == 'runs.jsonl:worker_runtime'
    assert (out / 'runs.jsonl').is_file() and not (out / 'audits.jsonl').exists()
    # Local test fixture only: production retains stopped scratch and never reruns it.
    import shutil
    shutil.rmtree(scratch)
