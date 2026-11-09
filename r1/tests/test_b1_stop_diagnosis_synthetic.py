"""Synthetic B1 STOP diagnosis fixtures with known answers; no host, real data or model."""
import hashlib
import importlib.util
import json
import random
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).parents[2]


@pytest.fixture
def mod(monkeypatch):
    path = REPO / 'docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py'
    spec = importlib.util.spec_from_file_location('b1_stop_diagnosis_synthetic', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # Mac has no O_NOATIME; substitute only in this synthetic fixture.
    if not hasattr(module.os, 'O_NOATIME'): monkeypatch.setattr(module.os, 'O_NOATIME', 0, raising=False)
    return module


def _delta(anchor, node, seed, b):
    # Known answers: scripted +0.001 everywhere; random_valid +0.002 in the first half, 0.0 in the second
    # (mean 0.001 over b = 2..20 is not exact, so the instance means are computed in the test).
    if anchor == 'scripted': return 0.001
    if anchor == 'random_valid': return 0.002 if b <= 10 else 0.0
    return 0.003


def build(root, mod, *, qwen_dup=10, qwen_eval=20, budgets=range(2, 21)):
    root.mkdir(); completed = {}; binding = 'synthetic-binding'
    for anchor in mod.ANCHORS:
        for node in mod.NODES:
            for seed in mod.SEEDS:
                key = f'{anchor}/b1/off/{node}__s{seed}'; directory = root / key; directory.mkdir(parents=True)
                job = {'candidate': {'id': anchor}, 'phase': 'b1', 'node': node, 'seed': seed, 'W': mod.W,
                       'mode': 'off', 'dryrun': False, 'binding': binding, 'authorization_checkout_head': mod.HEAD,
                       'audit_seeds': mod.AUDIT, 'authority_config': {'audit_seeds': mod.AUDIT,
                       'instance_seeds': list(mod.SEEDS), 'rule_sha256': mod.RULE}}
                raw_job = json.dumps(job).encode(); (directory / 'job.json').write_bytes(raw_job)
                props = []
                for b in budgets:
                    d = _delta(anchor, node, seed, b)
                    props.append({'proposal_id': f'EXAM:{node}__s{seed}:t{b:03d}', 'instance_id': f'{node}__s{seed}',
                                  'node': node, 'mode': 'off', 'audit_seeds': mod.AUDIT, 'k': 4, 'delta_audit': d,
                                  'candidate_metrics': [0.5 + d] * 4, 'incumbent_metrics': [0.5] * 4})
                metric = mod.METRIC[node]
                trials = [{'budget_index': 1, 'node_id': node, 'decision': 'kept', 'parsed_metrics': {metric: 0.5}},
                          {'budget_index': 2, 'node_id': node, 'decision': 'kept', 'parsed_metrics': {metric: 0.52}},
                          {'budget_index': 3, 'node_id': node, 'decision': 'discarded', 'parsed_metrics': {metric: 0.49}}]
                raw_trials = ('\n'.join(json.dumps(t) for t in trials) + '\n').encode()
                (directory / 'root_trials.jsonl').write_bytes(raw_trials)
                dup, ev = (qwen_dup, qwen_eval) if anchor == 'qwen25_coder_7b' else (0, len(props))
                manifest = {'job_sha256': hashlib.sha256(raw_job).hexdigest(), 'job_binding': binding,
                            'phase': 'b1', 'execution_label': 'EVIDENCE', 'status': 'COMPLETE', 'termination': 'worker_cap',
                            'candidate': anchor, 'node': node, 'instance_seed': seed, 'mode': 'off',
                            'compute_budget': {'worker_runs': 20, 'llm_calls': 0},
                            'evidence_hashes': {'root_trials.jsonl': hashlib.sha256(raw_trials).hexdigest()},
                            'audited_proposals': props, 'diagnostics': dict(trials=20, evaluated=ev, invalid=0,
                                                                            duplicates=dup, noops=0, parse_failed=0)}
                raw = json.dumps(manifest).encode(); (directory / 'campaign_manifest.json').write_bytes(raw)
                completed[key] = {'path': str(root / key / 'campaign_manifest.json'), 'sha256': hashlib.sha256(raw).hexdigest()}
    (root / 'batch_state.json').write_text(json.dumps({'phase': 'b1', 'status': 'STOPPED',
        'stop_reason': mod.EXPECTED_REASON, 'binding': binding, 'completed': completed}))
    return root


def test_known_answers_reproduce_stop_and_d2_d7(mod, tmp_path):
    result = mod.inspect(str(build(tmp_path / 'b1', mod)))
    s = result['summary']
    # random_valid instance mean = (9 x 0.002 + 10 x 0.0) / 19; scripted = 0.001; difference = 0.001 - 0.018/19 > 0.
    expected = 0.001 - 0.018 / 19
    assert s['D1_gate_recomputed']['difference_point'] == pytest.approx(expected)
    assert s['D1_gate_recomputed']['difference_lower'] == pytest.approx(expected)  # identical pairs: degenerate interval
    assert s['D1_reproduces_stop'] is False
    assert s['D7'] == {'duplicates': 120, 'evaluated': 240, 'rate': 0.5, 'reference': [0.4239, 0.58], 'inside': True}
    d2 = s['D2']['random_valid/digits_mlp']
    assert d2['audited'] == 76 and d2['keeps_including_first'] == 8 and d2['mean_gain_after_first_keep'] == pytest.approx(0.02)
    assert d2['d0'] == {'k_not_4': 0, 'none_in_vectors': 0, 'delta_mismatch': 0}
    d4 = s['D4']['random_valid/openml_ionosphere']
    assert d4['budget_index_le_10']['mean'] == pytest.approx(0.002) and d4['budget_index_gt_10']['mean'] == pytest.approx(0.0)
    # 19 audited proposals per root (b = 2..20): first half b = 2..11 holds nine 0.002 and one 0.0.
    assert d4['first_half_of_audited']['mean'] == pytest.approx(0.0018) and d4['second_half_of_audited']['mean'] == pytest.approx(0.0)
    d3 = s['D3']['scripted/openml_ionosphere']
    assert d3['mean_over_sigma_joint'] == pytest.approx(0.001 / 0.0410) and d3['share_harmful'] == 0
    assert 'qwen25_coder_7b/digits_mlp' in s['D8_information_only'] and not any(k.startswith('qwen') for k in s['D3'])
    text = json.dumps(result)
    assert 'candidate_metrics' not in text and 'incumbent_metrics' not in text and result['stop_changed'] is False


def test_negative_difference_reproduces_stop(mod, tmp_path, monkeypatch):
    monkeypatch.setitem(globals(), '_delta', lambda a, n, s, b: 0.0 if a == 'scripted' else (0.004 if a == 'random_valid' else 0.003))
    s = mod.inspect(str(build(tmp_path / 'b1', mod)))['summary']
    assert s['D1_gate_recomputed']['difference_point'] == pytest.approx(-0.004) and s['D1_reproduces_stop'] is True


def test_duplicate_rate_outside_reference(mod, tmp_path):
    s = mod.inspect(str(build(tmp_path / 'b1', mod, qwen_dup=2, qwen_eval=20)))['summary']
    assert s['D7']['rate'] == pytest.approx(0.1) and s['D7']['inside'] is False


def test_bootstrap_port_equals_frozen_guard(mod):
    from r1.exam.guards import paired_instance_bootstrap as frozen
    rng = random.Random(7)
    for _ in range(5):
        a = [{'instance_id': f'i{k % 12}', 'value': rng.gauss(0, 0.01)} for k in range(60)]
        b = [{'instance_id': f'i{k % 12}', 'value': rng.gauss(0, 0.01)} for k in range(50)]
        assert mod.paired_instance_bootstrap(a, b) == frozen(a, b)


def test_wrong_job_seed_refuses_before_manifest_read(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    path = root / 'qwen25_coder_7b/b1/off/openml_ionosphere__s9004/job.json'
    data = json.loads(path.read_text()); data['audit_seeds'] = [7006, 7007, 7008, 7009]; path.write_text(json.dumps(data))
    original = mod._read_bytes; calls = []
    def read(r, parts):
        calls.append('/'.join(parts)); return original(r, parts)
    with patch.object(mod, '_read_bytes', side_effect=read), pytest.raises(ValueError, match='seed mismatch'):
        mod.inspect(str(root))
    assert 'qwen25_coder_7b/b1/off/openml_ionosphere__s9004/campaign_manifest.json' not in calls


def test_trials_hash_mismatch_refuses(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    p = root / 'scripted/b1/off/digits_mlp__s9002/root_trials.jsonl'; p.write_bytes(p.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='root_trials hash'): mod.inspect(str(root))


def test_inconsistent_delta_is_counted_not_hidden(mod, tmp_path):
    root = build(tmp_path / 'b1', mod); key = 'random_valid/b1/off/digits_mlp__s9001'
    path = root / key / 'campaign_manifest.json'; data = json.loads(path.read_text())
    data['audited_proposals'][0]['delta_audit'] = 0.5; raw = json.dumps(data).encode(); path.write_bytes(raw)
    sp = root / 'batch_state.json'; st = json.loads(sp.read_text())
    st['completed'][key]['sha256'] = hashlib.sha256(raw).hexdigest(); sp.write_text(json.dumps(st))
    s = mod.inspect(str(root))['summary']
    assert s['D2']['random_valid/digits_mlp']['d0']['delta_mismatch'] == 1


def test_local_mode_from_descriptive_capture(mod, tmp_path):
    rows = []
    for anchor, v in (('random_valid', 0.002), ('scripted', 0.001)):
        for node in mod.NODES:
            for seed in mod.SEEDS:
                rows.append({'anchor': anchor, 'node': node, 'instance_seed': seed, 'audited_proposals': 5,
                             'mean_delta_audit': v, 'diagnostics': {}, 'job_sha256': 'x', 'manifest_sha256': 'y'})
    cap = tmp_path / 'ssh.log'
    cap.write_text('PRIVATE_CAPTURE=x\n' + json.dumps({'rows': rows}) + '\nDESCRIPTIVE_CAPTURE_COMPLETE\n\nSSH_EXIT=0\n')
    out = mod.from_descriptive_capture(str(cap))
    assert out['D1_gate_recomputed']['difference_point'] == pytest.approx(-0.001) and out['D1_reproduces_stop'] is True
    assert out['D3_means_by_node']['scripted/openml_credit_approval']['over_sigma_joint'] == pytest.approx(0.001 / 0.0279)
    rows.pop(); cap.write_text(json.dumps({'rows': rows}) + '\nDESCRIPTIVE_CAPTURE_COMPLETE\n')
    with pytest.raises(ValueError, match='24 expected rows'): mod.from_descriptive_capture(str(cap))
