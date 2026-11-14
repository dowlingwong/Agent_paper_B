"""B2 complete-batch / grid verifier (B2 code unit, 14 Nov 2026), synthetic files only, no training or server.

Built like ``test_exam_b1_batch_verify.fixture``: one finalist ``a`` (switchable, so its descriptive thinking-on rerun
is part of the grid), the three protocol nodes, n = 2 instances (9011, 9012), final-Y audits on 9201–9210.
"""
import hashlib
import json
from pathlib import Path

import pytest

from r1.exam import analyze, runtime
from r1.exam.guards import digest_file
from r1.liveness.check import evaluate_ledger_paths

NODES = ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere']
SEEDS = [9011, 9012]
AUDIT = list(range(9201, 9211))


def write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, sort_keys=True))


def fixture(tmp_path, monkeypatch, finalists=('a',)):
    import subprocess
    from r1.harness import harness_root
    from autoresearch.nodes.registry import load_registered_node
    from r1.c3.features import replay_campaign
    from r1.exam.b1_proposal_journal import validate_proposal_journal
    head = 'a' * 40; rule_sha = digest_file(analyze.RULE_V2); harness = Path(harness_root())
    harness_sha = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
    anchors = [{'id': 'random_valid', 'role': 'anchor', 'family': 'random', 'kind': 'random_valid'},
               {'id': 'scripted', 'role': 'anchor', 'family': 'scripted', 'kind': 'scripted'},
               {'id': 'qwen25_coder_7b', 'role': 'anchor', 'family': 'qwen', 'thinking_policy': {'mode': 'off', 'switchable': False}}]
    candidates = [{'id': 'a', 'role': 'candidate', 'family': 'fa', 'thinking_policy': {'mode': 'off', 'switchable': True, 'off_switch': True}},
                  {'id': 'b', 'role': 'candidate', 'family': 'fb', 'thinking_policy': {'mode': 'off', 'switchable': False}}]
    specs = anchors + candidates; registry = {'software_anchors': anchors[:2], 'candidates': anchors[2:] + candidates}
    reg = tmp_path / 'registry.yaml'; write(reg, registry)
    stage = tmp_path / 'stage.json'; write(stage, {'rows': [{'candidate': s['id'], 'passed': True} for s in specs]})
    amendment = tmp_path / 'amendment.json'; write(amendment, {'label': 'ENGINEERING_ONLY', 'rows': []})
    receipt = tmp_path / 'receipt'; receipt.write_text(digest_file(stage) + '\n' + digest_file(amendment))
    values = tmp_path / 'grids'; values.write_text('synthetic')
    b1 = tmp_path / 'b1_analysis.json'
    write(b1, {'phase': 'b1', 'label': 'EXAM', 'rule_sha256': rule_sha, 'finalists': list(finalists), 'rows': [],
               'execution_label': 'EVIDENCE', 'batch_verification': {'synthetic': True}})
    cfg = {'dryrun': False, 'registry': str(reg), 'value_grids': str(values), 'nodes': list(NODES), 'workers': 20,
           'host': 'TASL-7', 'W': 2, 'llm_call_cap': 8, 'audit_seeds': [9101, 9102, 9103, 9104],
           'instance_seeds': [9001, 9002, 9003, 9004], 'b2_instances_per_node': len(SEEDS),
           'proposal_schema': 'manager_proposal/v1', 'harness_commit': harness_sha, 'authorizations': {'b2': 'note.md'},
           'b1_analysis': str(b1), 'b1_analysis_sha256': digest_file(b1),
           'stage_a_table': str(stage), 'stage_a_table_sha256': digest_file(stage),
           'stage_a_amendment_table': str(amendment), 'stage_a_amendment_table_sha256': digest_file(amendment),
           'stage_a_amendment_acceptance': str(receipt), 'stage_a_amendment_acceptance_sha256': digest_file(receipt)}
    batch = tmp_path / 'batch'; batch.mkdir(); write(batch / 'registry_snapshot.yaml', registry)
    binding = hashlib.sha256(json.dumps({'config': cfg, 'registry_sha256': digest_file(reg), 'rule_sha256': rule_sha,
                                         'value_grids_sha256': digest_file(values)}, sort_keys=True).encode()).hexdigest()
    state = {'status': 'COMPLETE', 'phase': 'b2', 'execution_label': 'EVIDENCE', 'binding': binding, 'rule_sha256': rule_sha,
             'completed': {}}
    order = [s['id'] for s in specs]
    manifests = []
    for cid in [c for c in order if c in finalists]:
        spec = next(s for s in specs if s['id'] == cid)
        modes = ['off', 'on'] if spec['thinking_policy'].get('switchable') else ['off']
        grid = [(mode, node, seed) for mode in modes for node in NODES for seed in SEEDS]
        roots, paths = [], []
        for i, (mode, node, seed) in enumerate(grid):
            root = batch / cid / 'b2' / mode / f'{node}__s{seed}'; root.mkdir(parents=True)
            node_spec = load_registered_node(node, repo_root=harness)
            start = {p: (harness / 'nodes' / node / p).read_text() for p in node_spec.editable_paths}
            source_hashes = {p: digest_file(harness / 'nodes' / node / p) for p in node_spec.editable_paths}
            job = root / 'job.json'
            write(job, {'authorization_checkout_head': head, 'authority_config': cfg, 'phase': 'b2', 'node': node, 'seed': seed,
                        'mode': mode, 'dryrun': False, 'harness_commit': harness_sha, 'node_source_sha256': source_hashes,
                        'out': str(root), 'binding': binding, 'value_grids': str(values), 'candidate': spec,
                        'audit_seeds': AUDIT, **{k: cfg[k] for k in ('workers', 'host', 'W', 'llm_call_cap', 'proposal_schema')}})
            trials = root / 'root_trials.jsonl'
            trials.write_text(''.join(json.dumps({'node_id': node, 'trial_id': f't{j}', 'budget_index': j, 'decision': 'kept',
                                                  'extra': {}}) + '\n' for j in (1, 2)))
            records = [json.loads(x) for x in trials.read_text().splitlines()]
            _, checks = replay_campaign(records, start, node, f'{node}__s{seed}', 'EXAM', 'append_only_summary', cfg['W'], 1.)
            budget = {'max_worker_runs': 2, 'max_llm_calls': 8, 'worker_runs': 2, 'llm_calls': 1}
            event_rows = [{'event_type': 'llm_call', 'payload': {'cache_prompt': False}},
                          {'event_type': 'campaign_completed', 'payload': {'compute_budget': budget}}]
            events = root / 'root_events.jsonl'; events.write_text(''.join(json.dumps(x) + '\n' for x in event_rows))
            configs = root / 'audit_configs.json'; configs.write_text('{}')
            journal_path = root / 'b1_proposals.jsonl'
            journal_path.write_text(json.dumps({'schema': 'b1_proposal_journal/v1', 'trial_id': None, 'truncated': False,
                                                'check': 'not_applicable', 'rejection': None}) + '\n')
            journal = validate_proposal_journal(journal_path, records, event_rows)
            observer = root / 'a4_observer_requests.jsonl'
            from r1.exam.b1_observer_journal import validate_observer_journal
            hashes = {'root_trials.jsonl': digest_file(trials), 'root_events.jsonl': digest_file(events), 'audit_cache.json': None,
                      'audit_configs.json': digest_file(configs), 'a4_observer_requests.jsonl': None,
                      'b1_proposals.jsonl': digest_file(journal_path)}
            metrics = [0.6 + (i + k) / 1000 for k in range(10)]
            final = [{'instance_id': f'{node}__s{seed}', 'node': node, 'seeds': AUDIT, 'metrics': metrics, 'final_y': sum(metrics) / 10}]
            data = {'status': 'COMPLETE', 'label': 'EXAM', 'execution_label': 'EVIDENCE', 'phase': 'b2', 'candidate': cid,
                    'mode': mode, 'node': node, 'instance_seed': seed, 'job_binding': binding, 'job_sha256': digest_file(job),
                    'evidence_hashes': hashes, 'audited_proposals': [],
                    'd28': evaluate_ledger_paths([trials], generated_utc='synthetic', manager_kind='langgraph', memory_mode='append_only_summary'),
                    'cache_prompt': {'cache_prompt': False, 'llm_call_events': 1, 'llm_call_failed_events': 0,
                                     'trial_llm_call_records': 0, 'all_false': True},
                    'observer_evidence': validate_observer_journal(observer, event_rows), 'proposal_journal': journal,
                    'replay_checks': checks, 'compute_budget': budget, 'termination': 'worker_cap',
                    'diagnostics': {'trials': 2, 'evaluated': 0, 'invalid': 0, 'duplicates': 0, 'noops': 0, 'parse_failed': 0,
                                    'forecast_queries': 0, 'forecast_query_failed': 0},
                    'final_audits': final}
            path = root / 'campaign_manifest.json'; write(path, data)
            cert = root / 'post_check.json'; write(cert, {'binding': binding, 'manifest_sha256': digest_file(path), 'passed': True})
            state['completed'][f'{cid}/b2/{mode}/{node}__s{seed}'] = {'path': str(path), 'sha256': digest_file(path),
                                                                       'post_check_sha256': digest_file(cert)}
            roots.append(data); paths.append(str(path))
        m = {'label': 'EXAM', 'phase': 'b2', 'status': 'COMPLETE', 'execution_label': 'EVIDENCE', 'candidate': cid,
             'family': spec['family'], 'role': spec['role'], 'registry_order': order.index(cid),
             'registry_path': str(batch / 'registry_snapshot.yaml'), 'registry_sha256': digest_file(reg), 'rule_sha256': rule_sha,
             'rule_version': 'x5_rule/v2', 'primary_mode': 'off', 'mode': 'off', 'purpose': 'primary', 'stage_a_pass': True,
             'b1_analysis_sha256': cfg['b1_analysis_sha256'], 'cache_prompt': False, 'harness_commit': harness_sha,
             'diagnostics': {k: sum(r['diagnostics'].get(k, 0) for r in roots) for k in
                             ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed', 'forecast_queries', 'forecast_query_failed')},
             'audited_proposals': [], 'root_manifests': paths, 'cache_prompt_by_root': [x['cache_prompt'] for x in roots],
             'final_audits': [r['final_audits'][0] for r in roots if r['mode'] == 'off'],
             'sensitivity_final_audits': [r['final_audits'][0] for r in roots if r['mode'] != 'off'],
             'gpu_hours': 1.0, 'source_label': 'fixture', 'authorization_checkout_head': head,
             'stage_a_table_sha256': cfg['stage_a_table_sha256'], 'stage_a_amendment_table_sha256': cfg['stage_a_amendment_table_sha256'],
             'stage_a_amendment_acceptance_sha256': cfg['stage_a_amendment_acceptance_sha256']}
        if len(modes) > 1: m['thinking_on_rerun'] = 'descriptive'
        write(batch / cid / 'b2_manifest.json', m); manifests.append(m)
    write(batch / 'batch_state.json', state); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': manifests})
    monkeypatch.setattr(runtime, 'author_gate', lambda *a: head)
    monkeypatch.setattr(runtime, 'read_registry', lambda p: registry)
    return batch, cfg, rule_sha, state, manifests


def test_full_authorized_synthetic_b2_batch_ranks(tmp_path, monkeypatch):
    batch, cfg, sha, _, _ = fixture(tmp_path, monkeypatch)
    result = analyze.b2_summary_verified(batch, cfg, rule_path=analyze.RULE_V2, expected=sha)
    grid = result['batch_verification']['grid']
    assert grid['verified'] is True and grid['finalists'] == ['a'] and grid['seeds'] == SEEDS
    assert grid['modes'] == {'a': ['off', 'on']} and grid['audit_seeds'] == AUDIT
    assert result['selection']['rule_top'] == 'a' and result['rows'][0]['instances'] == 6
    assert result['thinking_on_descriptive'][0]['source'] == 'top3_thinking_on_rerun'


def _rebind(batch, state, path, root):
    write(path, root); cert = path.parent / 'post_check.json'
    write(cert, {'binding': state['binding'], 'manifest_sha256': digest_file(path), 'passed': True})
    for entry in state['completed'].values():
        if entry['path'] == str(path): entry.update(sha256=digest_file(path), post_check_sha256=digest_file(cert))
    write(batch / 'batch_state.json', state)


@pytest.mark.parametrize('tamper', ['batch_phase', 'missing_root', 'extra_root', 'dropped_rerun_root', 'final_y', 'final_seed',
                                    'final_instance', 'manifest_finals', 'manifest_rerun_finals', 'rerun_label', 'count',
                                    'nodes', 'b1_sha', 'finalists', 'wrong_head', 'job_audit_seeds', 'job_seed',
                                    'mode', 'extra_candidate', 'cache_event'])
def test_partial_or_tampered_b2_batch_stops(tmp_path, monkeypatch, tamper):
    batch, cfg, sha, state, ms = fixture(tmp_path, monkeypatch)
    m = ms[0]
    def save():
        write(batch / 'a/b2_manifest.json', m); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': ms})
    first = Path(m['root_manifests'][0]); root = json.loads(first.read_text())
    if tamper == 'batch_phase': state['phase'] = 'b1'; write(batch / 'batch_state.json', state)
    elif tamper == 'missing_root': state['completed'].pop(next(iter(state['completed']))); write(batch / 'batch_state.json', state)
    elif tamper == 'extra_root': state['completed']['a/b2/off/digits_mlp__s9013'] = {}; write(batch / 'batch_state.json', state)
    elif tamper == 'dropped_rerun_root':
        m['root_manifests'] = [p for p in m['root_manifests'] if '/b2/on/' not in p]; save()
    elif tamper == 'final_y': root['final_audits'][0]['final_y'] += 1e-6; _rebind(batch, state, first, root)
    elif tamper == 'final_seed': root['final_audits'][0]['seeds'][0] = 9101; _rebind(batch, state, first, root)
    elif tamper == 'final_instance': root['final_audits'][0]['instance_id'] = 'digits_mlp__s9012'; _rebind(batch, state, first, root)
    elif tamper == 'manifest_finals': m['final_audits'] = m['final_audits'][:-1]; save()
    elif tamper == 'manifest_rerun_finals': m['sensitivity_final_audits'] = []; save()
    elif tamper == 'rerun_label': m.pop('thinking_on_rerun'); save()
    elif tamper == 'count': cfg['b2_instances_per_node'] = 3
    elif tamper == 'nodes': cfg['nodes'] = NODES[:2] + ['tabular_mlp']
    elif tamper == 'b1_sha': cfg['b1_analysis_sha256'] = '0' * 64
    elif tamper == 'finalists':
        b1 = Path(cfg['b1_analysis']); data = json.loads(b1.read_text()); data['finalists'] = ['a', 'b']
        b1.write_text(json.dumps(data)); cfg['b1_analysis_sha256'] = digest_file(b1)
    elif tamper in ('wrong_head', 'job_audit_seeds', 'job_seed', 'mode'):
        job = first.parent / 'job.json'; data = json.loads(job.read_text())
        if tamper == 'wrong_head': data['authorization_checkout_head'] = 'b' * 40
        elif tamper == 'job_audit_seeds': data['audit_seeds'] = [9101, 9102, 9103, 9104]
        elif tamper == 'job_seed': data['seed'] = 9001
        else: data['mode'] = 'on'
        write(job, data); root['job_sha256'] = digest_file(job); _rebind(batch, state, first, root)
    elif tamper == 'extra_candidate':
        ms.append({**m, 'candidate': 'b'}); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': ms})
    elif tamper == 'cache_event':
        events = first.parent / 'root_events.jsonl'; rows = [json.loads(x) for x in events.read_text().splitlines()]
        rows[0]['payload']['cache_prompt'] = True; events.write_text(''.join(json.dumps(x) + '\n' for x in rows))
        root['evidence_hashes']['root_events.jsonl'] = digest_file(events); _rebind(batch, state, first, root)
    with pytest.raises((ValueError, RuntimeError, KeyError)):
        analyze.b2_summary_verified(batch, cfg, rule_path=analyze.RULE_V2, expected=sha)


def test_b2_cli_verified_mode_requires_batch_and_config(capsys):
    with pytest.raises(SystemExit):
        analyze.main(['b2', '--batch', '/tmp/x'])
