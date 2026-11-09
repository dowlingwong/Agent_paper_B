"""Synthetic B1 STOP diagnosis fixtures with known answers; no host, real data or model."""
import hashlib
import importlib.util
import json
import os
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


def repin(root, mod):
    """Synthetic stand-in for the accepted capture's state SHA (the real pin is a module constant)."""
    mod.EXPECTED_STATE_SHA = hashlib.sha256((root / 'batch_state.json').read_bytes()).hexdigest()


def rehash_manifest(root, mod, key, edit):
    path = root / key / 'campaign_manifest.json'; data = json.loads(path.read_text()); edit(data)
    raw = json.dumps(data).encode(); path.write_bytes(raw)
    sp = root / 'batch_state.json'; st = json.loads(sp.read_text())
    st['completed'][key]['sha256'] = hashlib.sha256(raw).hexdigest(); sp.write_text(json.dumps(st)); repin(root, mod)


def build(root, mod, *, qwen_dup=10, qwen_eval=20, budgets=range(2, 21), invalid=0, worker_runs=None):
    """``budgets`` is a range or a callable (anchor, node, seed) -> budget indices of the audited
    proposals; ``worker_runs`` an optional callable (anchor, node, seed) -> (worker_runs, termination).
    Scripted roots on OpenML nodes carry one skipped ledger row (an inactive categorical draw)."""
    root.mkdir(); completed = {}; binding = 'synthetic-binding'
    for anchor in mod.ANCHORS:
        for node in mod.NODES:
            for seed in mod.SEEDS:
                key = f'{anchor}/b1/off/{node}__s{seed}'; directory = root / key; directory.mkdir(parents=True)
                job = {'candidate': {'id': anchor}, 'phase': 'b1', 'node': node, 'seed': seed, 'W': mod.W,
                       'mode': 'off', 'dryrun': False, 'binding': binding, 'authorization_checkout_head': mod.HEAD,
                       'audit_seeds': mod.AUDIT, 'authority_config': {'audit_seeds': mod.AUDIT,
                       'instance_seeds': list(mod.SEEDS), 'rule_sha256': mod.RULE,
                       'anchor_duplicate_reference': dict(mod.DUP_REF_PINNED)}}
                raw_job = json.dumps(job).encode(); (directory / 'job.json').write_bytes(raw_job)
                props = []
                for b in (budgets(anchor, node, seed) if callable(budgets) else budgets):
                    d = _delta(anchor, node, seed, b)
                    props.append({'proposal_id': f'EXAM:{node}__s{seed}:t{b:03d}', 'instance_id': f'{node}__s{seed}',
                                  'node': node, 'mode': 'off', 'audit_seeds': mod.AUDIT, 'k': 4, 'delta_audit': d,
                                  'candidate_metrics': [0.5 + d] * 4, 'incumbent_metrics': [0.5] * 4})
                metric = mod.METRIC[node]
                trials = [{'budget_index': 1, 'node_id': node, 'decision': 'kept', 'parsed_metrics': {metric: 0.5}},
                          {'budget_index': 2, 'node_id': node, 'decision': 'kept', 'parsed_metrics': {metric: 0.52}},
                          {'budget_index': 3, 'node_id': node, 'decision': 'discarded', 'parsed_metrics': {metric: 0.49}}]
                if anchor == 'scripted' and node.startswith('openml_'):
                    trials.append({'budget_index': 4, 'node_id': node, 'decision': 'skipped', 'parsed_metrics': {}})
                raw_trials = ('\n'.join(json.dumps(t) for t in trials) + '\n').encode()
                (directory / 'root_trials.jsonl').write_bytes(raw_trials)
                dup, ev = (qwen_dup, qwen_eval) if anchor == 'qwen25_coder_7b' else (0, len(props))
                runs, term = worker_runs(anchor, node, seed) if worker_runs else (20, 'worker_cap')
                manifest = {'job_sha256': hashlib.sha256(raw_job).hexdigest(), 'job_binding': binding,
                            'phase': 'b1', 'execution_label': 'EVIDENCE', 'status': 'COMPLETE', 'termination': term,
                            'candidate': anchor, 'node': node, 'instance_seed': seed, 'mode': 'off',
                            'compute_budget': {'worker_runs': runs, 'llm_calls': 0},
                            'evidence_hashes': {'root_trials.jsonl': hashlib.sha256(raw_trials).hexdigest()},
                            'audited_proposals': props, 'diagnostics': dict(trials=20, evaluated=ev, invalid=invalid,
                                                                            duplicates=dup, noops=0, parse_failed=0)}
                raw = json.dumps(manifest).encode(); (directory / 'campaign_manifest.json').write_bytes(raw)
                completed[key] = {'path': str(root / key / 'campaign_manifest.json'), 'sha256': hashlib.sha256(raw).hexdigest()}
    (root / 'batch_state.json').write_text(json.dumps({'phase': 'b1', 'status': 'STOPPED',
        'stop_reason': mod.EXPECTED_REASON, 'binding': binding, 'completed': completed}))
    repin(root, mod)
    return root


def test_known_answers_reproduce_stop_and_d2_d7(mod, tmp_path):
    result = mod.inspect(str(build(tmp_path / 'b1', mod)))
    s = result['summary']
    # random_valid instance mean = (9 x 0.002 + 10 x 0.0) / 19; scripted = 0.001; difference = 0.001 - 0.018/19 > 0.
    expected = 0.001 - 0.018 / 19
    assert s['D1_gate_recomputed']['difference_point'] == pytest.approx(expected)
    assert s['D1_gate_recomputed']['difference_lower'] == pytest.approx(expected)  # identical pairs: degenerate interval
    assert s['D1_reproduces_stop'] is False
    d7 = s['D7']
    assert (d7['duplicates'], d7['evaluated'], d7['rate'], d7['inside'], d7['passes_next_gate']) == (120, 240, 0.5, True, True)
    assert d7['reference']['lower'] == 0.42386590667728663 and d7['reference']['upper'] == 0.5800007633587785
    assert result['state_sha256'] == mod.EXPECTED_STATE_SHA
    d2 = s['D2']['random_valid/digits_mlp']
    assert d2['audited'] == 76 and d2['keeps_including_first'] == 8 and d2['mean_gain_after_first_keep'] == pytest.approx(0.02)
    assert d2['skipped'] == 0 and d2['roots_with_gain_after_first_keep'] == 4 and d2['decisions'] == {'discarded': 4, 'kept': 8}
    assert s['D2']['scripted/openml_credit_approval']['skipped'] == 4 and s['D2']['scripted/digits_mlp']['skipped'] == 0
    assert d2['d0'] == {'k_not_4': 0, 'none_in_vectors': 0, 'delta_mismatch': 0}
    d4 = s['D4']['random_valid/openml_ionosphere']
    assert d4['budget_index_le_10']['mean'] == pytest.approx(0.002) and d4['budget_index_gt_10']['mean'] == pytest.approx(0.0)
    # 19 audited proposals per root (b = 2..20): first half b = 2..11 holds nine 0.002 and one 0.0.
    assert d4['first_half_of_audited']['mean'] == pytest.approx(0.0018) and d4['second_half_of_audited']['mean'] == pytest.approx(0.0)
    d3 = s['D3']['scripted/openml_ionosphere']
    assert d3['mean_over_sigma_joint'] == pytest.approx(0.001 / 0.0410) and d3['share_harmful'] == 0
    assert d3['median_over_sigma_joint'] == pytest.approx(0.001 / 0.0410)
    assert s['D3']['random_valid/digits_mlp']['median_over_sigma_joint'] == pytest.approx(0.0)  # 9 x 0.002, 10 x 0.0
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
    st['completed'][key]['sha256'] = hashlib.sha256(raw).hexdigest(); sp.write_text(json.dumps(st)); repin(root, mod)
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


def _tracking(mod):
    original = mod._read_bytes; calls = []
    def read(r, parts):
        calls.append('/'.join(parts)); return original(r, parts)
    return calls, read


def test_state_sha_differs_from_accepted_capture_refuses_before_any_job(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    mod.EXPECTED_STATE_SHA = 'cfe74fafdbbff6f10648f7e015b3df52f0438c435d45caf76e9e8c116d0b5794'  # the real pin
    calls, read = _tracking(mod)
    with patch.object(mod, '_read_bytes', side_effect=read), pytest.raises(ValueError, match='accepted descriptive capture'):
        mod.inspect(str(root))
    assert calls == ['batch_state.json']


def test_pinned_constants():
    text = (REPO / 'docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py').read_text()
    assert "EXPECTED_STATE_SHA = 'cfe74fafdbbff6f10648f7e015b3df52f0438c435d45caf76e9e8c116d0b5794'" in text


def test_rounded_duplicate_reference_in_job_refuses_before_manifest(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    path = root / 'qwen25_coder_7b/b1/off/digits_mlp__s9001/job.json'; data = json.loads(path.read_text())
    data['authority_config']['anchor_duplicate_reference'].update(lower=0.4239, upper=0.58); path.write_text(json.dumps(data))
    calls, read = _tracking(mod)
    with patch.object(mod, '_read_bytes', side_effect=read), pytest.raises(ValueError, match='pinned interval'):
        mod.inspect(str(root))
    assert 'qwen25_coder_7b/b1/off/digits_mlp__s9001/campaign_manifest.json' not in calls


def test_d7_uses_exact_pinned_bounds(mod, tmp_path):
    # 12 qwen roots x 42387 / (12 x 100000) = 0.42387: inside the gate's exact interval [0.4238659..., 0.5800007...]
    # but below the rounded 0.4239, so a rounded D7 would wrongly report it outside.
    s = mod.inspect(str(build(tmp_path / 'b1', mod, qwen_dup=42387, qwen_eval=100000)))['summary']
    assert s['D7']['rate'] == pytest.approx(0.42387) and s['D7']['rate'] < 0.4239
    assert s['D7']['inside'] is True and s['D7']['passes_next_gate'] is True


@pytest.mark.parametrize('field,value', [('status', 'RUNNING'), ('execution_label', 'DRYRUN')])
def test_manifest_status_or_label_mismatch_refuses(mod, tmp_path, field, value):
    root = build(tmp_path / 'b1', mod)
    rehash_manifest(root, mod, 'random_valid/b1/off/openml_ionosphere__s9001', lambda d: d.update({field: value}))
    with pytest.raises(ValueError, match='manifest binding or identity'): mod.inspect(str(root))


def test_symlinked_file_refuses(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    target = root / 'scripted/b1/off/digits_mlp__s9001/job.json'; copy = tmp_path / 'job_copy.json'
    copy.write_bytes(target.read_bytes()); target.rename(tmp_path / 'job_orig.json'); os.symlink(copy, target)
    with pytest.raises(OSError): mod.inspect(str(root))


def test_symlinked_directory_component_refuses(mod, tmp_path):
    root = build(tmp_path / 'b1', mod)
    d = root / 'scripted/b1/off/digits_mlp__s9001'; moved = tmp_path / 'moved_root'
    d.rename(moved); os.symlink(moved, d)
    with pytest.raises(OSError): mod.inspect(str(root))


def test_file_not_owned_refuses(mod, tmp_path, monkeypatch):
    root = build(tmp_path / 'b1', mod); uid = os.getuid()
    monkeypatch.setattr(mod.os, 'getuid', lambda: uid + 1)
    with pytest.raises(ValueError, match='owned regular file'): mod.inspect(str(root))


def test_file_changed_during_read_refuses(mod, tmp_path, monkeypatch):
    root = build(tmp_path / 'b1', mod); real_read = os.read; state = root / 'batch_state.json'; done = []
    def read(fd, n):
        chunk = real_read(fd, n)
        if chunk and not done:
            done.append(1)
            with open(state, 'ab') as f: f.write(b' ')
        return chunk
    monkeypatch.setattr(mod.os, 'read', read)
    with pytest.raises(ValueError, match='changed during read'): mod.inspect(str(root))


def test_main_prints_nothing_on_stdout_when_refusing(mod, tmp_path, monkeypatch, capsys):
    root = build(tmp_path / 'b1', mod)
    p = root / 'scripted/b1/off/digits_mlp__s9002/root_trials.jsonl'; p.write_bytes(p.read_bytes() + b'\n')
    monkeypatch.setattr(mod, 'ROOT', str(root))
    assert mod.main(['-c']) == 1
    out = capsys.readouterr()
    assert out.out == '' and out.err.startswith('STOP: diagnosis refused: ValueError: root_trials hash')
    monkeypatch.setattr(mod, 'ROOT', str(build(tmp_path / 'ok', mod)))
    assert mod.main(['-c']) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2 and lines[1] == 'DIAGNOSIS_CAPTURE_COMPLETE' and json.loads(lines[0])['stop_changed'] is False
