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
    reference = tmp_path / 'reference.json'; write(reference, {'lower': 0.1, 'upper': 0.5})
    b1 = tmp_path / 'b1_analysis.json'
    write(b1, {'phase': 'b1', 'label': 'EXAM', 'rule_sha256': rule_sha, 'finalists': list(finalists), 'rows': [],
               'execution_label': 'EVIDENCE', 'batch_verification': {'synthetic': True}})
    cfg = {'dryrun': False, 'registry': str(reg), 'value_grids': str(values), 'nodes': list(NODES), 'workers': 20,
           'host': 'TASL-7', 'W': 2, 'llm_call_cap': 8, 'audit_seeds': [9101, 9102, 9103, 9104],
           'instance_seeds': [9001, 9002, 9003, 9004], 'b2_instances_per_node': len(SEEDS),
           'proposal_schema': 'manager_proposal/v1', 'harness_commit': harness_sha, 'authorizations': {'b2': 'note.md'},
           'anchor_duplicate_reference': {'source': str(reference), 'sha256': digest_file(reference), 'lower': 0.1, 'upper': 0.5},
           'b1_analysis': str(b1), 'b1_analysis_sha256': digest_file(b1),
           'stage_a_table': str(stage), 'stage_a_table_sha256': digest_file(stage),
           'stage_a_amendment_table': str(amendment), 'stage_a_amendment_table_sha256': digest_file(amendment),
           'stage_a_amendment_acceptance': str(receipt), 'stage_a_amendment_acceptance_sha256': digest_file(receipt)}
    batch = tmp_path / 'batch'; batch.mkdir(); write(batch / 'registry_snapshot.yaml', registry)
    binding = hashlib.sha256(json.dumps({'config': cfg, 'registry_sha256': digest_file(reg), 'rule_sha256': rule_sha,
                                         'value_grids_sha256': digest_file(values)}, sort_keys=True).encode()).hexdigest()
    state = {'status': 'COMPLETE', 'phase': 'b2', 'execution_label': 'EVIDENCE', 'binding': binding, 'rule_sha256': rule_sha,
             'completed': {}, 'server_intervals': []}
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
        state['server_intervals'] += [{'candidate': cid, 'phase': 'b2', 'mode': 'off', 'context': 32768, 'start': 1000.0, 'end': 4600.0},
                                      {'candidate': cid, 'phase': 'b2', 'mode': 'off', 'context': 32768, 'start': 5000.0, 'end': 6800.0}]
        if len(modes) > 1:
            state['server_intervals'].append({'candidate': cid, 'phase': 'b2', 'mode': 'on', 'context': 32768, 'start': 7000.0, 'end': 9000.0})
        d28 = lambda rs: all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in rs)
        primary_roots = [r for r in roots if r['mode'] == 'off']; rerun_roots = [r for r in roots if r['mode'] != 'off']
        m = {'label': 'EXAM', 'phase': 'b2', 'status': 'COMPLETE', 'execution_label': 'EVIDENCE', 'candidate': cid,
             'stage_a_pass_source': 'stage_a_table', 'd28_scope': 'thinking_off_roots_only', 'd28_pass': d28(primary_roots),
             'thinking_on_d28': {'pass': d28(rerun_roots), 'roots': len(rerun_roots), 'role': 'descriptive_never_changes_eligibility'} if rerun_roots else None,
             'gpu_hours_status': 'recorded_dedicated_intervals',
             'family': spec['family'], 'role': spec['role'], 'registry_order': order.index(cid),
             'registry_path': str(batch / 'registry_snapshot.yaml'), 'registry_sha256': digest_file(reg), 'rule_sha256': rule_sha,
             'rule_version': 'x5_rule/v2', 'primary_mode': 'off', 'mode': 'off', 'purpose': 'primary', 'stage_a_pass': True,
             'b1_analysis_sha256': cfg['b1_analysis_sha256'], 'cache_prompt': False, 'harness_commit': harness_sha,
             'diagnostics': {k: sum(r['diagnostics'].get(k, 0) for r in roots) for k in
                             ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed', 'forecast_queries', 'forecast_query_failed')},
             'audited_proposals': [], 'root_manifests': paths, 'cache_prompt_by_root': [x['cache_prompt'] for x in roots],
             'final_audits': [r['final_audits'][0] for r in roots if r['mode'] == 'off'],
             'sensitivity_final_audits': [r['final_audits'][0] for r in roots if r['mode'] != 'off'],
             'gpu_hours': 1.5, 'source_label': 'fixture', 'authorization_checkout_head': head,
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


TAMPER = {
    'batch_phase': 'not a completed evidence batch', 'missing_root': 'root missing or changed',
    'extra_root': 'extra or missing completed roots', 'dropped_rerun_root': 'root grid differs',
    'final_y': 'final_y differs from the mean', 'final_y_tolerance': 'final_y differs from the mean',
    'final_seed': 'seeds are not exactly 9201', 'final_instance': 'another node or instance',
    'manifest_finals': 'final-Y audits differ from its verified primary roots',
    'manifest_rerun_finals': 'rerun final-Y audits differ', 'rerun_label': 'rerun label differs',
    'count': 'configuration binding mismatch', 'nodes': 'configuration binding mismatch',
    'b1_sha': 'configuration binding mismatch', 'finalists': 'configuration binding mismatch',
    'wrong_head': 'authorization HEAD mismatch', 'job_audit_seeds': 'audit seeds are not 9201',
    'job_seed': 'job authority, candidate or source binding', 'mode': 'job authority, candidate or source binding',
    'extra_candidate': 'candidate set or registry order', 'cache_event': 'cache_prompt not explicitly false',
    'manifest_b1_sha': 'candidate identity, authority or inputs differ', 'registry_snapshot': 'registry snapshot differs',
    'post_check': 'receiving certificate changed', 'root_d28': 'D28 differs from verified ledger',
    'candidate_d28': 'candidate D28 differs', 'rerun_d28': 'descriptive D28 differs',
    'stage_pass_source': 'Stage A pass provenance', 'diagnostics': 'candidate diagnostics differ',
    'root_diagnostics': 'root diagnostics differ', 'candidate_audits': 'candidate audits differ',
    'replay': 'replay checks differ', 'budget': 'budget differs from completion event',
    'journal': 'proposal journal evidence differs', 'observer': 'observer evidence differs',
    'all_false': 'cache evidence differs from events', 'screen': 'B1 analysis is not the verified',
    'gpu_hours': 'GPU-h of', 'gpu_upper_bound': 'only an upper bound', 'gpu_open': 'no closed server intervals',
    'gpu_status': 'GPU-h of', 'anchor': 'invalid anchor duplicate reference', 'cap': 'author cap of 10',
}


@pytest.mark.parametrize('tamper', sorted(TAMPER))
def test_partial_or_tampered_b2_batch_stops(tmp_path, monkeypatch, tamper):
    batch, cfg, sha, state, ms = fixture(tmp_path, monkeypatch)
    m = ms[0]
    def save():
        write(batch / 'a/b2_manifest.json', m); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': ms})
    first = Path(m['root_manifests'][0]); root = json.loads(first.read_text())
    def root_and_candidate(change):
        change(root); _rebind(batch, state, first, root)
    if tamper == 'batch_phase': state['phase'] = 'b1'; write(batch / 'batch_state.json', state)
    elif tamper == 'missing_root': state['completed'].pop(next(iter(state['completed']))); write(batch / 'batch_state.json', state)
    elif tamper == 'extra_root': state['completed']['a/b2/off/digits_mlp__s9013'] = {}; write(batch / 'batch_state.json', state)
    elif tamper == 'dropped_rerun_root':
        m['root_manifests'] = [p for p in m['root_manifests'] if '/b2/on/' not in p]; save()
    elif tamper in ('final_y', 'final_y_tolerance', 'final_seed', 'final_instance'):
        # the root and the candidate aggregate both carry the tampered record, so only the final-Y check can catch it
        rec = root['final_audits'][0]
        if tamper == 'final_y': rec['final_y'] += 1e-6
        elif tamper == 'final_y_tolerance': rec['final_y'] += 1e-11       # inside any relative tolerance, outside abs 1e-12
        elif tamper == 'final_seed': rec['seeds'][0] = 9101
        else: rec['instance_id'] = 'digits_mlp__s9012'
        _rebind(batch, state, first, root); m['final_audits'][0] = rec; save()
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
    elif tamper == 'all_false':
        root['cache_prompt'] = {**root['cache_prompt'], 'all_false': False}; _rebind(batch, state, first, root)
    elif tamper == 'cache_event':
        events = first.parent / 'root_events.jsonl'; rows = [json.loads(x) for x in events.read_text().splitlines()]
        rows[0]['payload']['cache_prompt'] = True
        events.write_text(''.join(json.dumps(x) + '\n' for x in rows))
        root['evidence_hashes']['root_events.jsonl'] = digest_file(events); _rebind(batch, state, first, root)
    elif tamper == 'manifest_b1_sha': m['b1_analysis_sha256'] = '0' * 64; save()
    elif tamper == 'registry_snapshot': write(batch / 'registry_snapshot.yaml', {'software_anchors': [], 'candidates': []})
    elif tamper == 'post_check':
        cert = first.parent / 'post_check.json'; data = json.loads(cert.read_text()); data['note'] = 'x'; write(cert, data)
    elif tamper == 'root_d28':
        root['d28']['nodes']['digits_mlp']['pass'] = not root['d28']['nodes']['digits_mlp']['pass']; _rebind(batch, state, first, root)
    elif tamper == 'candidate_d28': m['d28_pass'] = not m['d28_pass']; save()
    elif tamper == 'rerun_d28': m['thinking_on_d28']['pass'] = not m['thinking_on_d28']['pass']; save()
    elif tamper == 'stage_pass_source': m['stage_a_pass_source'] = 'a1_amendment_measurement'; save()
    elif tamper == 'diagnostics': m['diagnostics']['trials'] = 99; save()
    elif tamper == 'root_diagnostics':
        root['diagnostics']['trials'] = 99; m['diagnostics']['trials'] += 97; save(); _rebind(batch, state, first, root)
    elif tamper == 'candidate_audits': m['audited_proposals'] = [{'forged': True}]; save()
    elif tamper == 'replay': root['replay_checks'] = {'forged': True}; _rebind(batch, state, first, root)
    elif tamper == 'budget': root['compute_budget'] = {**root['compute_budget'], 'llm_calls': 7}; _rebind(batch, state, first, root)
    elif tamper == 'journal': root['proposal_journal'] = {**root['proposal_journal'], 'rows': 9}; _rebind(batch, state, first, root)
    elif tamper == 'observer': root['observer_evidence'] = {'calls': 3}; _rebind(batch, state, first, root)
    elif tamper == 'screen':
        b1 = Path(cfg['b1_analysis']); data = json.loads(b1.read_text()); data['execution_label'] = 'DRYRUN'
        b1.write_text(json.dumps(data))
        monkeypatch.setattr('r1.exam.b2_batch.digest_file', lambda p, _d=digest_file: cfg['b1_analysis_sha256'] if str(p) == str(b1) else _d(p))
    elif tamper == 'gpu_hours': m['gpu_hours'] = 1.6; save()
    elif tamper == 'gpu_status': m['gpu_hours_status'] = 'upper_bound_after_interruption'; save()
    elif tamper == 'gpu_upper_bound':
        state['server_intervals'][0]['cost_is_upper_bound'] = True; write(batch / 'batch_state.json', state)
    elif tamper == 'gpu_open':
        for x in state['server_intervals']:
            if x['mode'] == 'off': x['end'] = None
        write(batch / 'batch_state.json', state)
    elif tamper == 'anchor': Path(cfg['anchor_duplicate_reference']['source']).write_text('{"lower":0.1,"upper":0.6}')
    elif tamper == 'cap': pass
    if tamper == 'cap':
        from r1.exam.b2_batch import expected_grid
        with pytest.raises(ValueError, match=TAMPER[tamper]):
            expected_grid({'b2_instances_per_node': 11, 'nodes': list(NODES)}, ['a'],
                          {'a': {'id': 'a', 'role': 'candidate', 'thinking_policy': {'mode': 'off', 'switchable': False}}}, {'a': {}})
        return
    with pytest.raises((ValueError, RuntimeError, KeyError), match=TAMPER[tamper]):
        analyze.b2_summary_verified(batch, cfg, rule_path=analyze.RULE_V2, expected=sha)


def test_ranking_uses_only_the_verified_gpu_hours(tmp_path, monkeypatch):
    from r1.exam.analyze import _b2_summary_v2, load_rule
    rule, sha = load_rule(analyze.RULE_V2, digest_file(analyze.RULE_V2))
    batch, cfg, _, _, ms = fixture(tmp_path, monkeypatch)
    m = {**ms[0], 'rule_sha256': sha}
    grid = {'verified': True, 'finalists': ['a'], 'nodes': list(NODES), 'instances_per_node': 2, 'gpu_hours': {'a': 1.5}}
    assert _b2_summary_v2([m], rule, sha, grid=grid)['rows'][0]['gpu_hours'] == 1.5
    for bad in ({'a': 1.4}, {}, {'a': None}):
        with pytest.raises(ValueError, match='GPU-h tie-break input'):
            _b2_summary_v2([m], rule, sha, grid={**grid, 'gpu_hours': bad})
    with pytest.raises(ValueError, match='GPU-h tie-break input'):
        _b2_summary_v2([{**m, 'gpu_hours': None}], rule, sha, grid=grid)


def test_b2_cli_verified_mode_requires_batch_and_config(capsys):
    with pytest.raises(SystemExit):
        analyze.main(['b2', '--batch', '/tmp/x'])
