"""Synthetic filesystem/authority fixtures only; no B2 evidence is created."""
import copy
import base64
import hashlib
import json
import subprocess
from pathlib import Path
import pytest

from r1.exam import analyze, b2_verified as verified
from r1.exam import runtime
from r1.exam.analyze import RULE_V2
from r1.exam.guards import digest_file
from r1.scripts import exam_runner

NODES = ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere']
SHA = digest_file(RULE_V2)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True))


def synthetic_campaign(node, seed, W=20, cap=80, rejected=()):
    """Generate the pinned event/observer shape; fake requests, no server."""
    campaign = f'{node}__s{seed}'
    def event(kind, payload, trial=None):
        return {'campaign_id': campaign, 'trial_id': trial, 'event_type': kind, 'payload': payload}
    events = [event('campaign_started', {'budget': cap, 'node_id': node, 'memory_mode': 'append_only_summary',
        'proposal_schema': 'manager_proposal/v1', 'proposal_observer': 'exam_self_forecast/v1'})]
    records, journal = [], []
    request = json.dumps({'cache_prompt': False}, separators=(',', ':'))
    request_sha = hashlib.sha256(request.encode()).hexdigest()
    response = b'{"fixture":true}'; response_sha = hashlib.sha256(response).hexdigest()
    for index, kind in enumerate([*rejected, *(['worker'] * W)], 1):
        trial = f'{campaign}-trial-{index:03d}'
        events.append(event('trial_started', {'budget_index': index}, trial))
        manager = {'cache_prompt': False, 'parse_ok': True}
        events.append(event('llm_call', manager, trial))
        record = {'campaign_id': campaign, 'node_id': node, 'trial_id': trial, 'budget_index': index,
                  'decision': 'skipped' if kind == 'skipped' else ('failed_invalid' if kind == 'invalid' else 'kept'),
                  'extra': {'manager': {'llm_call': manager}, 'worker': {'worker_skipped': True} if kind == 'skipped' else {}}}
        records.append(record)
        if kind == 'skipped': continue
        events.append(event('worker_started', {'worker_mode': 'synthetic'}, trial))
        events.append(event('worker_finished', {'success': kind == 'worker'}, trial))
        if kind == 'invalid': continue  # precondition failure: no charged worker or forecast
        sequence = len(journal) // 4 + 1
        evidence = {'request_body': request, 'request_body_sha256': request_sha, 'response_body_sha256': response_sha}
        forecast = {'cache_prompt': False, 'llm_calls': 1, 'request_evidence': evidence}
        events.append(event('exam_self_forecast', forecast, trial))
        events.append(event('llm_call', {**forecast, 'purpose': 'self_forecast'}, trial))
        events.append(event('edit_novelty', {'active_config_equals_incumbent': False, 'active_config_seen_before': False}, trial))
        journal.extend([
            {'sequence': sequence, 'event': 'request_attempt', 'request_body': request, 'request_body_sha256': request_sha},
            {'sequence': sequence, 'event': 'response_headers', 'http_status': 200},
            {'sequence': sequence, 'event': 'response_chunk', 'chunk_index': 1, 'chunk_bytes': len(response),
             'chunk_sha256': response_sha, 'chunk_b64': base64.b64encode(response).decode()},
            {'sequence': sequence, 'event': 'response_complete', 'response_body_sha256': response_sha},
        ])
    calls = 2 * W + len(rejected)
    budget = {'max_worker_runs': W, 'max_worker_seconds': None, 'max_llm_calls': cap, 'worker_runs': W,
              'worker_seconds': 1., 'llm_calls': calls, 'exhausted': True, 'worker_runs_remaining': 0,
              'worker_seconds_remaining': None, 'llm_calls_remaining': cap - calls, 'worker_runs_used': W,
              'worker_seconds_used': 1., 'llm_calls_used': calls}
    events.append(event('campaign_completed', {'compute_budget': budget, 'records_written': len(records)}))
    diagnostics = {'trials': len(records), 'evaluated': W, 'invalid': list(rejected).count('invalid'),
                   'duplicates': 0, 'noops': 0, 'parse_failed': 0, 'forecast_queries': W, 'forecast_query_failed': 0}
    return records, events, journal, budget, diagnostics


def write_lines(path, rows):
    path.write_text(''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows))


def test_campaign_budget_allows_skips_and_uncharged_precondition_failures():
    records, events, journal, budget, diagnostics = synthetic_campaign(NODES[0], 9011, rejected=('skipped', 'invalid'))
    root = {'compute_budget': budget, 'termination': 'worker_cap', 'diagnostics': diagnostics}
    verified._campaign_budget(records, events, root, {'W': 20, 'llm_call_cap': 80, 'proposal_schema': 'manager_proposal/v1'}, NODES[0], 9011)
    assert budget['worker_runs'] == 20 and budget['llm_calls'] == 42 and len(records) == 22


def test_zero_workers_requires_a_fully_evidenced_llm_cap():
    records, events, journal, budget, diagnostics = synthetic_campaign(NODES[0], 9011, W=0, rejected=('invalid',) * 80)
    budget.update(max_worker_runs=20, worker_runs_remaining=20, exhausted=True)
    root = {'compute_budget': budget, 'termination': 'llm_cap_or_reserved_observer_pair', 'diagnostics': diagnostics}
    verified._campaign_budget(records, events, root, {'W': 20, 'llm_call_cap': 80, 'proposal_schema': 'manager_proposal/v1'}, NODES[0], 9011)
    assert not journal and budget['worker_runs'] == 0 and budget['llm_calls'] == 80


def test_retained_pinned_harness_synthetic_campaign_shape():
    path = Path(__file__).parent / 'fixtures/b2_pinned_harness_synthetic_20261105'
    records = [json.loads(line) for line in (path / 'root_trials.jsonl').read_text().splitlines()]
    events = [json.loads(line) for line in (path / 'root_events.jsonl').read_text().splitlines()]
    root = json.loads((path / 'campaign_manifest.json').read_text())
    verified._campaign_budget(records, events, root, {'W': 2, 'llm_call_cap': 8, 'proposal_schema': 'manager_proposal/v1'}, 'digits_mlp', 9001)


@pytest.mark.parametrize('mutation', ['empty_trials', 'no_completion', 'duplicate_completion', 'bad_written_count',
    'bad_worker_count', 'bad_call_count', 'no_observer', 'missing_worker_event', 'forecast_call_mismatch',
    'missing_manager_call', 'observer_before_worker', 'wrong_termination', 'early_stop', 'wrong_observer', 'wrong_diagnostics', 'unknown_trial'])
def test_campaign_budget_refuses_missing_or_inconsistent_evidence(mutation):
    records, events, journal, budget, diagnostics = synthetic_campaign(NODES[0], 9011)
    root = {'compute_budget': budget, 'termination': 'worker_cap', 'diagnostics': diagnostics}
    if mutation == 'empty_trials': records.clear()
    if mutation == 'no_completion': events.pop()
    if mutation == 'duplicate_completion': events.append(copy.deepcopy(events[-1]))
    if mutation == 'bad_written_count': events[-1]['payload']['records_written'] = 0
    if mutation == 'bad_worker_count': budget['worker_runs'] = 19
    if mutation == 'bad_call_count': budget['llm_calls'] = 39
    if mutation == 'no_observer': events[:] = [e for e in events if e['event_type'] not in ('exam_self_forecast',) and not (e['event_type'] == 'llm_call' and e['payload'].get('purpose') == 'self_forecast')]
    if mutation == 'missing_worker_event': events.remove(next(e for e in events if e['event_type'] == 'worker_finished'))
    if mutation == 'forecast_call_mismatch': next(e for e in events if e['event_type'] == 'exam_self_forecast')['payload'] = {'cache_prompt': True}
    if mutation == 'missing_manager_call': events.remove(next(e for e in events if e['event_type'] == 'llm_call' and e['payload'].get('purpose') != 'self_forecast'))
    if mutation == 'observer_before_worker':
        forecast = next(e for e in events if e['event_type'] == 'exam_self_forecast')
        events.remove(forecast); events.insert(1, forecast)
    if mutation == 'wrong_termination': root['termination'] = 'llm_cap_or_reserved_observer_pair'
    if mutation == 'early_stop':
        events = [e for e in events if e.get('trial_id') != records[-1]['trial_id']]
        records.pop(); budget.update(worker_runs=19, worker_runs_used=19, worker_runs_remaining=1,
            llm_calls=38, llm_calls_used=38, llm_calls_remaining=42, exhausted=False)
        root['termination'] = 'llm_cap_or_reserved_observer_pair'; events[-1]['payload']['records_written'] = 19
    if mutation == 'wrong_observer': events[0]['payload']['proposal_observer'] = None
    if mutation == 'wrong_diagnostics': root['diagnostics']['trials'] = 0
    if mutation == 'unknown_trial': events[1]['trial_id'] = 'other-trial-001'
    with pytest.raises(ValueError, match='STOP: B2 verification'):
        verified._campaign_budget(records, events, root, {'W': 20, 'llm_call_cap': 80, 'proposal_schema': 'manager_proposal/v1'}, NODES[0], 9011)


def test_power_row_requires_real_author_decision_table():
    sha = 'a' * 64
    head = '## 10. Author decisions\n### 7 November 2026 (author)\n'
    row = f'| R1-EXAM-B2-POWER-PLAN | approved {sha} |\n'
    assert verified._power_row(head + '| ID | Decision |\n|---|---|\n' + row, sha)
    assert not verified._power_row(head + '| Artifact | SHA256 |\n|---|---|\n' + row, sha)
    assert not verified._power_row(head + '```\n| ID | Decision |\n|---|---|\n' + row + '```\n', sha)
    assert not verified._power_row(head + f'Prose mentions R1-EXAM-B2-POWER-PLAN {sha}', sha)
    assert not verified._power_row(head.replace('7 November', '40 November') + '| ID | Decision |\n|---|---|\n' + row, sha)
    assert not verified._power_row(head + '| ID | Decision |\n|---|---|\n' + row + row, sha)


def test_authority_requires_committed_clean_note_and_exact_bindings(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'; repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 'Synthetic fixture'], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 'fixture@example.invalid'], check=True)
    cfg = {'rule_sha256': SHA, 'nodes': NODES, 'b2_instances_per_node': 2,
           'b1_analysis_sha256': 'b' * 64, 'authorizations': {'b2': 'note.json'}}
    write(repo / 'config.json', cfg)
    note = {'author': 'Dowling Wong', 'phase': 'b2', 'approved': True, 'rule_sha256': SHA,
            'config_sha256': digest_file(repo / 'config.json'), 'nodes': NODES,
            'instances_per_node': 2, 'b1_analysis_sha256': 'b' * 64}
    write(repo / 'note.json', note)
    note_sha = digest_file(repo / 'note.json')
    plan = ('## 10. Author decisions\n### 7 November 2026 (author)\n| ID | Decision |\n|---|---|\n'
            f'| R1-EXAM-RULE-X5V2 | synthetic {SHA} |\n'
            f'| R1-EXAM-B2-POWER-PLAN | synthetic {note_sha} |\n')
    (repo / 'docs/r1').mkdir(parents=True)
    (repo / 'docs/r1/PLAN.md').write_text(plan)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'synthetic authority fixture'], check=True)
    monkeypatch.setattr(verified, 'REPO', repo)
    monkeypatch.setattr(runtime, 'load_config', lambda path: json.loads(Path(path).read_text()))
    actual, head, actual_note_sha = verified._authority(repo / 'config.json')
    assert actual == cfg and len(head) == 40 and actual_note_sha == note_sha
    (repo / 'untracked.txt').write_text('dirty')
    with pytest.raises(ValueError, match='clean committed checkout'):
        verified._authority(repo / 'config.json')


@pytest.mark.parametrize('field,value', [
    ('author', 'someone else'), ('phase', 'b1'), ('approved', False), ('rule_sha256', 'c' * 64),
    ('config_sha256', 'c' * 64), ('nodes', ['digits_mlp']), ('instances_per_node', 3),
    ('instances_per_node', True), ('b1_analysis_sha256', 'c' * 64),
])
def test_committed_authority_must_bind_exact_values(tmp_path, monkeypatch, field, value):
    repo = tmp_path / 'repo'; repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 'Synthetic fixture'], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 'fixture@example.invalid'], check=True)
    cfg = {'rule_sha256': SHA, 'nodes': NODES, 'b2_instances_per_node': 2,
           'b1_analysis_sha256': 'b' * 64, 'authorizations': {'b2': 'note.json'}}
    write(repo / 'config.json', cfg)
    note = {'author': 'Dowling Wong', 'phase': 'b2', 'approved': True, 'rule_sha256': SHA,
            'config_sha256': digest_file(repo / 'config.json'), 'nodes': NODES,
            'instances_per_node': 2, 'b1_analysis_sha256': 'b' * 64}
    note[field] = value; write(repo / 'note.json', note)
    (repo / 'docs/r1').mkdir(parents=True)
    (repo / 'docs/r1/PLAN.md').write_text('## 10. Author decisions\n### 7 November 2026 (author)\n| ID | Decision |\n|---|---|\n'
        f'| R1-EXAM-RULE-X5V2 | synthetic {SHA} |\n| R1-EXAM-B2-POWER-PLAN | synthetic {digest_file(repo / "note.json")} |\n')
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'synthetic authority fixture'], check=True)
    monkeypatch.setattr(verified, 'REPO', repo)
    monkeypatch.setattr(runtime, 'load_config', lambda path: json.loads(Path(path).read_text()))
    with pytest.raises(ValueError, match='STOP: B2 verification'):
        verified._authority(repo / 'config.json')


@pytest.fixture
def batch_fixture(tmp_path, monkeypatch):
    """Synthetic files use EVIDENCE field values to test the verifier, not real evidence."""
    cfg = {'rule': str(RULE_V2), 'rule_sha256': SHA, 'nodes': NODES, 'b2_instances_per_node': 2,
           'host': 'TASL-7', 'workers': 2, 'W': 20, 'llm_call_cap': 80, 'proposal_schema': 'manager_proposal/v1',
           'cache_prompt': False, 'template_repairs': {}, 'harness_commit': '3' * 40,
           'stage_a_table': str(tmp_path / 'stage.json'), 'stage_a_amendment_table': str(tmp_path / 'amend.json'),
           'stage_a_amendment_acceptance': str(tmp_path / 'accept.txt'), 'registry': str(tmp_path / 'registry.yaml'),
           'value_grids': str(tmp_path / 'grids.yaml'), 'b1_analysis': str(tmp_path / 'b1.json')}
    for key in ('stage_a_table', 'stage_a_amendment_table', 'stage_a_amendment_acceptance', 'registry', 'value_grids'):
        Path(cfg[key]).write_text('synthetic ' + key)
    for key in ('stage_a_table', 'stage_a_amendment_table', 'stage_a_amendment_acceptance'):
        cfg[key + '_sha256'] = digest_file(cfg[key])
    specs = [{'id': cid, 'role': 'candidate', 'family': cid, 'thinking_policy': {'mode': 'off'},
              'quant_source': {'sha256': ('a' if cid == 'a' else 'b') * 64}} for cid in ('a', 'b')]
    b1 = {'phase': 'b1', 'label': 'EXAM', 'execution_label': 'EVIDENCE', 'rule_sha256': SHA,
          'batch_verification': {'authorization_checkout_head': '4' * 40, 'batch_state_sha256': '5' * 64,
                                 'batch_manifests_sha256': '6' * 64, 'eligible_candidates': ['a', 'b']}, 'finalists': ['a', 'b'],
          'rows': [{'candidate': cid, 'role': 'candidate', 'stage_a_pass': True, 'd28_pass': True,
                    'thinking_off_eligible': True, 'mu_hat_mode': 'off', 'b2_thinking_mode': 'off'} for cid in ('a', 'b')]}
    write(Path(cfg['b1_analysis']), b1); cfg['b1_analysis_sha256'] = digest_file(cfg['b1_analysis'])
    batch = tmp_path / 'batch'; batch.mkdir(); (batch / 'registry_snapshot.yaml').write_text(Path(cfg['registry']).read_text())
    binding = hashlib.sha256(json.dumps({'config': cfg, 'registry_sha256': digest_file(batch / 'registry_snapshot.yaml'),
        'rule_sha256': SHA, 'value_grids_sha256': digest_file(cfg['value_grids'])}, sort_keys=True).encode()).hexdigest()
    state = {'label': 'EXAM', 'execution_label': 'EVIDENCE', 'status': 'COMPLETE', 'phase': 'b2',
             'rule_sha256': SHA, 'binding': binding, 'completed': {}, 'server_intervals': []}
    manifests = []
    for ix, spec in enumerate(specs):
        cid = spec['id']; audit_rows = []; paths = []; y = .6 + ix * .1
        state['server_intervals'].append({'candidate': cid, 'phase': 'b2', 'mode': 'off', 'start': ix * 10000, 'end': ix * 10000 + 3600})
        for node in NODES:
            for seed in (9011, 9012):
                root = batch / cid / 'b2' / 'off' / f'{node}__s{seed}'; root.mkdir(parents=True)
                job = {'phase': 'b2', 'mode': 'off', 'node': node, 'seed': seed, 'binding': binding,
                       'out': str(root), 'dryrun': False, 'candidate': spec, 'audit_seeds': list(range(9201, 9211)),
                       **{key: cfg[key] for key in ('host', 'workers', 'W', 'llm_call_cap', 'value_grids', 'proposal_schema')}}
                write(root / 'job.json', job)
                evidence = {}
                records, events, journal, budget, diagnostics = synthetic_campaign(node, seed)
                write_lines(root / 'root_trials.jsonl', records)
                write_lines(root / 'root_events.jsonl', events)
                write_lines(root / 'a4_observer_requests.jsonl', journal)
                (root / 'audit_configs.json').write_text('{}')
                for name in ('root_trials.jsonl', 'root_events.jsonl', 'audit_configs.json', 'a4_observer_requests.jsonl'):
                    evidence[name] = digest_file(root / name)
                evidence['audit_cache.json'] = None
                final = {'node': node, 'instance_id': f'{node}__s{seed}', 'seeds': list(range(9201, 9211)),
                         'metrics': [y] * 10, 'final_y': y}
                record = {'status': 'COMPLETE', 'label': 'EXAM', 'execution_label': 'EVIDENCE', 'job_binding': binding,
                          'job_sha256': digest_file(root / 'job.json'), 'evidence_hashes': evidence, 'candidate': cid,
                          'phase': 'b2', 'node': node, 'instance_seed': seed, 'mode': 'off', 'final_audits': [final],
                          'cache_prompt': {'cache_prompt': False, 'llm_call_events': 40, 'llm_call_failed_events': 0,
                                           'trial_llm_call_records': 20, 'all_false': True},
                          'observer_evidence': {'calls': 20, 'sha256': evidence['a4_observer_requests.jsonl']},
                          'compute_budget': budget, 'termination': 'worker_cap', 'diagnostics': diagnostics}
                path = root / 'campaign_manifest.json'; write(path, record)
                write(root / 'post_check.json', {'binding': binding, 'manifest_sha256': digest_file(path), 'passed': True})
                key = f'{cid}/b2/off/{node}__s{seed}'
                state['completed'][key] = {'path': str(path), 'sha256': digest_file(path), 'post_check_sha256': digest_file(root / 'post_check.json')}
                paths.append(str(path)); audit_rows.append(final)
        m = {'label': 'EXAM', 'execution_label': 'EVIDENCE', 'status': 'COMPLETE', 'phase': 'b2', 'candidate': cid,
             'family': cid, 'role': 'candidate', 'model_sha256': spec['quant_source']['sha256'], 'mode': 'off', 'primary_mode': 'off',
             'template_repair': None, 'cache_prompt': False,
             'stage_a_pass': True, 'stage_a_pass_source': None, 'harness_commit': cfg['harness_commit'],
             'authorization_checkout_head': '1' * 40,
             'rule_sha256': SHA, 'b1_analysis_sha256': cfg['b1_analysis_sha256'], 'registry_sha256': digest_file(batch / 'registry_snapshot.yaml'),
             'registry_path': str(batch / 'registry_snapshot.yaml'), 'stage_a_table_sha256': cfg['stage_a_table_sha256'],
             'stage_a_amendment_table_sha256': cfg['stage_a_amendment_table_sha256'],
             'stage_a_amendment_acceptance_sha256': cfg['stage_a_amendment_acceptance_sha256'],
             'gpu_hours': 1., 'gpu_hours_status': 'recorded_dedicated_intervals', 'root_manifests': paths, 'final_audits': audit_rows}
        write(batch / cid / 'b2_manifest.json', m); manifests.append(m)
    write(batch / 'batch_state.json', state); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': manifests})
    monkeypatch.setattr(verified, '_authority', lambda path: (cfg, '1' * 40, '2' * 64))
    monkeypatch.setattr(runtime, 'read_registry', lambda path: {'candidates': specs, 'software_anchors': []})
    monkeypatch.setattr(exam_runner, 'stage_a_pass_set', lambda cfg, candidates, v2: {'a': {}, 'b': {}})
    return batch, cfg, state, manifests


def test_complete_received_fixture_ranks_and_binds_hashes(batch_fixture):
    batch, cfg, state, manifests = batch_fixture
    result = verified.b2_summary_verified(batch, 'unused')
    assert result['rule_top'] == 'b' and result['execution_label'] == 'EVIDENCE'
    assert result['batch_verification']['batch_state_sha256'] == digest_file(batch / 'batch_state.json')


def test_cli_requires_v2_rule_and_verified_batch(batch_fixture, capsys):
    batch, cfg, state, manifests = batch_fixture
    analyze.main(['b2', '--batch', str(batch), '--config', 'unused', '--rule', str(RULE_V2), '--rule-sha256', SHA])
    assert json.loads(capsys.readouterr().out)['rule_top'] == 'b'
    with pytest.raises(ValueError, match='selected analysis rule'):
        analyze.main(['b2', '--batch', str(batch), '--config', 'unused'])


def test_swapped_root_audits_are_refused_even_if_receipts_are_rehashed(batch_fixture):
    batch, cfg, state, manifests = batch_fixture
    paths = [Path(p) for p in manifests[0]['root_manifests'][:2]]
    records = [json.loads(p.read_text()) for p in paths]
    records[0]['final_audits'], records[1]['final_audits'] = records[1]['final_audits'], records[0]['final_audits']
    manifests[0]['final_audits'][:2] = [r['final_audits'][0] for r in records]
    for path, record in zip(paths, records):
        write(path, record)
        check_path = path.parent / 'post_check.json'
        check = json.loads(check_path.read_text()); check['manifest_sha256'] = digest_file(path); write(check_path, check)
        key = f"a/b2/off/{record['node']}__s{record['instance_seed']}"
        state['completed'][key]['sha256'] = digest_file(path)
        state['completed'][key]['post_check_sha256'] = digest_file(check_path)
    write(batch / 'a/b2_manifest.json', manifests[0]); write(batch / 'batch_state.json', state)
    write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': manifests})
    with pytest.raises(ValueError, match='root final audit identity differs'):
        verified.b2_summary_verified(batch, 'unused')


@pytest.mark.parametrize('mutation', ['empty_trials', 'no_completion', 'no_forecast'])
def test_rehashed_broken_campaign_is_refused(batch_fixture, mutation):
    batch, cfg, state, manifests = batch_fixture
    path = Path(manifests[0]['root_manifests'][0]); root = path.parent
    record = json.loads(path.read_text())
    if mutation == 'empty_trials': (root / 'root_trials.jsonl').write_text('')
    else:
        events = [json.loads(line) for line in (root / 'root_events.jsonl').read_text().splitlines()]
        if mutation == 'no_completion': events = [e for e in events if e['event_type'] != 'campaign_completed']
        if mutation == 'no_forecast': events = [e for e in events if e['event_type'] != 'exam_self_forecast']
        write_lines(root / 'root_events.jsonl', events)
    for name in ('root_trials.jsonl', 'root_events.jsonl'):
        record['evidence_hashes'][name] = digest_file(root / name)
    write(path, record)
    check = json.loads((root / 'post_check.json').read_text()); check['manifest_sha256'] = digest_file(path)
    write(root / 'post_check.json', check)
    key = next(k for k, v in state['completed'].items() if v['path'] == str(path))
    state['completed'][key].update(sha256=digest_file(path), post_check_sha256=digest_file(root / 'post_check.json'))
    write(batch / 'batch_state.json', state)
    with pytest.raises(ValueError, match='STOP: B2 verification'):
        verified.b2_summary_verified(batch, 'unused')


@pytest.mark.parametrize('case', ['missing_root', 'extra_root', 'extra_candidate', 'tampered_audit', 'bad_receipt', 'open_interval', 'wrong_gpu_hours', 'dirty_mode', 'changed_job'])
def test_received_fixture_refuses_missing_or_altered_evidence(batch_fixture, case):
    batch, cfg, state, manifests = batch_fixture
    if case == 'missing_root': state['completed'].pop(next(iter(state['completed'])))
    if case == 'extra_root': state['completed']['a/b2/off/digits_mlp__s9099'] = {}
    if case == 'extra_candidate': manifests.append(copy.deepcopy(manifests[0])); manifests[-1]['candidate'] = 'extra'
    if case == 'tampered_audit': manifests[0]['final_audits'][0]['final_y'] += 1
    if case == 'bad_receipt': state['completed'][next(iter(state['completed']))]['post_check_sha256'] = '0' * 64
    if case == 'open_interval': state['server_intervals'][0]['end'] = None
    if case == 'wrong_gpu_hours': manifests[0]['gpu_hours'] = .5
    if case == 'dirty_mode': manifests[0]['primary_mode'] = 'on'
    if case == 'changed_job':
        path = Path(next(iter(state['completed'].values()))['path']); (path.parent / 'job.json').write_text('{}')
    if case in ('tampered_audit', 'wrong_gpu_hours', 'dirty_mode'):
        write(batch / manifests[0]['candidate'] / 'b2_manifest.json', manifests[0])
    write(batch / 'batch_state.json', state); write(batch / 'b2_manifests.json', {'label': 'EXAM', 'manifests': manifests})
    with pytest.raises((ValueError, runtime.PreparationStop)):
        verified.b2_summary_verified(batch, 'unused')
