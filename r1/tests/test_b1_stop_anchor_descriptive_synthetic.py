"""Synthetic B1-only fixture, no bootstrap, real audit data or host."""
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mod(monkeypatch):
    path = Path(__file__).parents[2] / 'docs/r1/proposals/B1_STOP_ANCHOR_DESCRIPTIVE_20261108.py'
    spec = importlib.util.spec_from_file_location('b1_stop_descriptive_synthetic', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if not hasattr(module.os, 'O_NOATIME'): monkeypatch.setattr(module.os, 'O_NOATIME', 0, raising=False)
    return module


@pytest.fixture
def fixture_root(tmp_path, mod):
    root = tmp_path / 'b1'; root.mkdir(); completed = {}; binding = 'synthetic-binding'
    for anchor in mod.ALL_ANCHORS:
        for node in mod.NODES:
            for seed in mod.SEEDS:
                key = f'{anchor}/b1/off/{node}__s{seed}'
                expected = str(root / key / 'campaign_manifest.json')
                completed[key] = {'path': expected, 'sha256': 'not-read-qwen'}
                if anchor not in mod.ANCHORS: continue
                directory = root / key; directory.mkdir(parents=True)
                job = {'candidate': {'id': anchor}, 'phase': 'b1', 'node': node, 'seed': seed,
                       'mode': 'off', 'dryrun': False, 'binding': binding, 'authorization_checkout_head': mod.HEAD,
                       'audit_seeds': mod.AUDIT, 'authority_config': {'audit_seeds': mod.AUDIT,
                       'instance_seeds': list(mod.SEEDS), 'rule_sha256': mod.RULE}}
                raw_job = json.dumps(job).encode(); (directory / 'job.json').write_bytes(raw_job)
                proposal = {'proposal_id': f'{node}-{seed}-trial-1', 'instance_id': f'{node}__s{seed}',
                            'node': node, 'mode': 'off', 'audit_seeds': mod.AUDIT,
                            'candidate_metrics': [1, 2, 3, 4], 'incumbent_metrics': [0, 1, 2, 3], 'delta_audit': 1.0}
                manifest = {'job_sha256': hashlib.sha256(raw_job).hexdigest(), 'job_binding': binding,
                            'phase': 'b1', 'execution_label': 'EVIDENCE', 'status': 'COMPLETE',
                            'candidate': anchor, 'node': node, 'instance_seed': seed, 'mode': 'off',
                            'audited_proposals': [proposal], 'diagnostics': dict(trials=20, evaluated=1, invalid=0,
                                                                                duplicates=0, noops=0, parse_failed=0)}
                raw = json.dumps(manifest).encode(); (directory / 'campaign_manifest.json').write_bytes(raw)
                completed[key]['sha256'] = hashlib.sha256(raw).hexdigest()
    (root / 'batch_state.json').write_text(json.dumps({'phase': 'b1', 'status': 'STOPPED',
        'stop_reason': mod.EXPECTED_REASON, 'binding': binding, 'completed': completed}))
    return root


def test_fixed_seed_descriptive_fields_only(mod, fixture_root):
    result = mod.inspect(str(fixture_root))
    assert len(result['rows']) == 24 and result['comparison_or_gate_recomputed'] is False
    assert all(row['mean_delta_audit'] == 1.0 and row['audited_proposals'] == 1 for row in result['rows'])
    assert 'candidate_metrics' not in json.dumps(result) and 'incumbent_metrics' not in json.dumps(result)


def test_wrong_job_seed_refuses_before_manifest_read(mod, fixture_root):
    path = fixture_root / 'random_valid/b1/off/digits_mlp__s9001/job.json'
    data = json.loads(path.read_text()); data['audit_seeds'] = [7006, 7007, 7008, 7009]
    path.write_text(json.dumps(data)); original = mod._read; calls = []
    def read(root, parts):
        calls.append(parts[-1]); return original(root, parts)
    with patch.object(mod, '_read', side_effect=read), pytest.raises(ValueError, match='seed mismatch'):
        mod.inspect(str(fixture_root))
    assert 'campaign_manifest.json' not in calls


def test_manifest_digest_mismatch_stops(mod, fixture_root):
    path = fixture_root / 'random_valid/b1/off/digits_mlp__s9001/campaign_manifest.json'
    path.write_text(path.read_text() + ' ')
    with pytest.raises(ValueError, match='manifest binding'): mod.inspect(str(fixture_root))


def test_wrong_manifest_seed_refuses(mod, fixture_root):
    key = 'random_valid/b1/off/digits_mlp__s9001'; path = fixture_root / key / 'campaign_manifest.json'
    data = json.loads(path.read_text()); data['audited_proposals'][0]['audit_seeds'] = [7006, 7007, 7008, 7009]
    raw = json.dumps(data).encode(); path.write_bytes(raw)
    state_path = fixture_root / 'batch_state.json'; state = json.loads(state_path.read_text())
    state['completed'][key]['sha256'] = hashlib.sha256(raw).hexdigest(); state_path.write_text(json.dumps(state))
    with pytest.raises(ValueError, match='seed or identity mismatch'): mod.inspect(str(fixture_root))
