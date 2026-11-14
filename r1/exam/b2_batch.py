"""Verify a complete authorized B2 batch and its node/instance grid before any x5_rule/v2 B2 ranking.

B2 code unit (14 Nov 2026; AI-assisted, Claude). This is the B2 grid verifier proposed in
``docs/r1/proposals/B2_GRID_VERIFIER_DESIGN_20261104.md``, at the same authority level as the B1 batch verifier
(``r1.exam.b1_batch.verify_batch``, unchanged): the clean committed checkout, the committed author note, the dated
author PLAN rows and the frozen B1 analysis are the process authority (``runtime.author_gate`` for phase ``b2``).
The design's externally authenticated authority snapshot and independent receiving record are *not* implemented
here; like B1, the independent review of the run and of its evidence is the process boundary.

What is verified, fail closed:
* the batch is a completed EVIDENCE ``b2`` batch with the configured binding, registry snapshot and rule;
* the frozen B1 analysis is the digest-bound file and names a non-empty, duplicate-free finalist list of registry
  candidates; exactly one candidate manifest per finalist, in registry order, and no other primary candidate;
* the author-bound grid: the three configured nodes x seeds ``9011 … 9011 + n - 1`` (n = the author-bound
  ``b2_instances_per_node``), for the primary thinking-off mode, and for the descriptive thinking-on rerun of the
  top three finalists that can switch thinking on; every root in that grid exists exactly once and no other root;
* every root as the B1 verifier checks it (receiving check, job authority and parameters, ledger diagnostics,
  budget, cache-false, observer and proposal journals, D28 record, replay, paired audits from the cache), with the
  B2 audit seeds 9201–9210;
* every root has exactly one final-Y audit for its own (node, instance) with the ordered seeds 9201–9210, ten finite
  numeric metrics and ``final_y`` equal to their mean (absolute tolerance 1e-12); the candidate manifest's
  ``final_audits`` / ``sensitivity_final_audits`` are exactly those of its verified primary / rerun roots.
"""
from __future__ import annotations
import hashlib
import json
import math
import subprocess
from pathlib import Path

from r1.exam.analyze import thinking_off_capable
from r1.exam.b1_batch import refuse_sealed
from r1.exam.guards import digest_file

B2_SEED_BASE = 9011
B2_AUDIT_SEEDS = list(range(9201, 9211))
PROTOCOL_NODE_SETS = ({'digits_mlp', 'openml_credit_approval', 'openml_ionosphere'},
                      {'tabular_mlp', 'openml_credit_approval', 'openml_ionosphere'})


def _stop(message):
    raise ValueError('STOP: B2 batch ' + message)


def _read(path):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError) as exc: raise ValueError('STOP: B2 batch file unavailable or malformed') from exc


def _inside(root, path):
    refuse_sealed(root, path)
    if not Path(path).resolve().is_relative_to(Path(root).resolve()):
        _stop('constituent path escapes its batch root')


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def expected_grid(cfg, finalists, specs_by_id, eligible):
    """The author-bound B2 grid: [(candidate, mode, node, seed)] in run order, and the per-finalist modes."""
    n = cfg.get('b2_instances_per_node')
    if type(n) is not int or not 1 <= n <= 89:
        _stop('instance count is not an author-bound integer in 1..89')
    nodes = cfg.get('nodes')
    if not isinstance(nodes, list) or len(nodes) != 3 or len(set(nodes)) != 3 or set(nodes) not in PROTOCOL_NODE_SETS:
        _stop('node list is not the three protocol nodes')
    seeds = list(range(B2_SEED_BASE, B2_SEED_BASE + n))
    if not isinstance(finalists, list) or not finalists or len(set(finalists)) != len(finalists):
        _stop('finalist list empty or duplicated')
    grid, modes_of = [], {}
    for rank, cid in enumerate(finalists):
        spec = specs_by_id.get(cid)
        if spec is None or spec.get('role') != 'candidate' or cid not in eligible:
            _stop(f'finalist {cid!r} is not an eligible registry candidate')
        if not thinking_off_capable(spec.get('thinking_policy')):
            _stop(f'finalist {cid!r} cannot run thinking off')
        modes = ['off']
        if rank < 3 and (spec.get('thinking_policy') or {}).get('switchable') is True and \
                not eligible[cid].get('thinking_disabled_due_grammar'):
            modes.append('on')
        modes_of[cid] = modes
        grid.extend((cid, mode, node, seed) for mode in modes for node in nodes for seed in seeds)
    return grid, modes_of, seeds


def check_final_audit(root, node, seed):
    """Exactly one final-Y audit for this root's own (node, instance), ten finite metrics, final_y = their mean."""
    final = root.get('final_audits')
    if not isinstance(final, list) or len(final) != 1 or not isinstance(final[0], dict):
        _stop('root does not have exactly one final-Y audit')
    record = final[0]
    if set(record) != {'instance_id', 'node', 'seeds', 'metrics', 'final_y'}:
        _stop('final-Y audit fields differ')
    if record['instance_id'] != f'{node}__s{seed}' or record['node'] != node:
        _stop('final-Y audit belongs to another node or instance')
    seeds = record['seeds']
    if not isinstance(seeds, list) or [type(s) for s in seeds] != [int] * 10 or seeds != B2_AUDIT_SEEDS:
        _stop('final-Y audit seeds are not exactly 9201–9210')
    metrics = record['metrics']
    if not isinstance(metrics, list) or len(metrics) != 10 or not all(_number(v) for v in metrics):
        _stop('final-Y audit needs ten finite numeric metrics')
    if not _number(record['final_y']) or not math.isclose(record['final_y'], sum(metrics) / 10, rel_tol=0.0, abs_tol=1e-12):
        _stop('final_y differs from the mean of its ten audits')
    return record


def verify_b2_batch(batch, cfg, rule_sha):
    """Return (verified candidate manifests, proof with the verified grid); no inference, server, or mutation."""
    from r1.exam.runtime import author_gate, read_registry, verify_campaign, _verify_b1_root_authority, b1_harness_sources
    from r1.scripts.exam_runner import stage_a_pass_set
    from r1.exam.campaign import cache_prompt_evidence, read_rows
    from r1.exam.b1_observer_journal import validate_observer_journal
    from r1.exam.b1_proposal_journal import validate_proposal_journal
    from r1.liveness.check import evaluate_ledger_paths
    from r1.harness import harness_root
    from autoresearch.nodes.registry import load_registered_node
    from r1.c3.features import replay_campaign, files_hash
    from r1.c3.audit import paired
    from r1.exam.observer import _authorized_candidate
    refuse_sealed(batch, cfg.get('registry'), cfg.get('rule'), cfg.get('value_grids'), cfg.get('b1_analysis'),
                  cfg.get('stage_a_table'), cfg.get('stage_a_amendment_table'), cfg.get('stage_a_amendment_acceptance'),
                  (cfg.get('authorizations') or {}).get('b2'))
    if cfg.get('dryrun'): _stop('production verification refuses DRYRUN')
    head = author_gate(cfg, 'b2', rule_sha)
    if not isinstance(head, str) or len(head) != 40: _stop('authorized HEAD absent')
    harness = Path(harness_root()).resolve()
    try:
        pinned = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
        changed = subprocess.check_output(['git', '-C', str(harness), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    except (OSError, subprocess.SubprocessError) as exc: raise ValueError('STOP: B2 harness pin unavailable') from exc
    if pinned != cfg.get('harness_commit') or changed: _stop('harness differs from the clean pin')
    node_sources = {node: b1_harness_sources(node, cfg['harness_commit']) for node in cfg['nodes']}
    batch = Path(batch).resolve(strict=True)
    _inside(batch, batch / 'batch_state.json'); _inside(batch, batch / 'b2_manifests.json')
    state = _read(batch / 'batch_state.json')
    if state.get('status') != 'COMPLETE' or state.get('phase') != 'b2' or state.get('execution_label') != 'EVIDENCE':
        _stop('is not a completed evidence batch')
    registry_path = batch / 'registry_snapshot.yaml'
    if registry_path.resolve().parent != batch or digest_file(registry_path) != digest_file(cfg['registry']):
        _stop('registry snapshot differs from configured registry')
    registry = read_registry(registry_path)
    expected_binding = hashlib.sha256(json.dumps({'config': cfg, 'registry_sha256': digest_file(registry_path),
        'rule_sha256': rule_sha, 'value_grids_sha256': digest_file(cfg['value_grids'])}, sort_keys=True).encode()).hexdigest()
    if state.get('binding') != expected_binding or state.get('rule_sha256') != rule_sha:
        _stop('configuration binding mismatch')
    if digest_file(cfg['b1_analysis']) != cfg['b1_analysis_sha256']: _stop('B1 analysis digest mismatch')
    screen = _read(cfg['b1_analysis'])
    if screen.get('phase') != 'b1' or screen.get('rule_sha256') != rule_sha or screen.get('execution_label') != 'EVIDENCE':
        _stop('B1 analysis is not the verified x5_rule/v2 evidence analysis')
    candidates = {r['id'] for r in registry['candidates'] if r.get('role') == 'candidate'}
    eligible = stage_a_pass_set(cfg, candidates, v2=True)
    specs = registry['software_anchors'] + [r for r in registry['candidates'] if r['role'] == 'anchor'] + \
        [r for r in registry['candidates'] if r['role'] == 'candidate'] + registry.get('sensitivities', [])
    specs_by_id = {s['id']: s for s in specs}
    order = [s['id'] for s in specs]
    finalists = screen.get('finalists')
    grid, modes_of, seeds = expected_grid(cfg, finalists, specs_by_id, eligible)
    ids = [cid for cid in order if cid in set(finalists)]
    data = _read(batch / 'b2_manifests.json')
    manifests = data.get('manifests') if isinstance(data, dict) and data.get('label') == 'EXAM' else None
    if not isinstance(manifests, list) or [m.get('candidate') for m in manifests] != ids:
        _stop('candidate set or registry order differs from the frozen finalists')
    state_roots = state.get('completed')
    if not isinstance(state_roots, dict): _stop('completed root index missing')
    expected_keys = set()
    for m in manifests:
        cid = m['candidate']; spec = specs_by_id[cid]
        candidate_path = batch / cid / 'b2_manifest.json'
        _inside(batch, batch / cid)
        if not candidate_path.resolve().is_relative_to(batch) or _read(candidate_path) != m:
            _stop('candidate manifest differs from aggregate')
        if (m.get('label') != 'EXAM' or m.get('phase') != 'b2' or m.get('status') != 'COMPLETE' or
                m.get('execution_label') != 'EVIDENCE' or m.get('authorization_checkout_head') != head or
                m.get('rule_sha256') != rule_sha or m.get('rule_version') != 'x5_rule/v2' or
                m.get('b1_analysis_sha256') != cfg['b1_analysis_sha256'] or
                m.get('purpose') != 'primary' or m.get('mode') != 'off' or m.get('primary_mode') != 'off' or
                m.get('stage_a_table_sha256') != cfg['stage_a_table_sha256'] or
                m.get('stage_a_amendment_table_sha256') != cfg['stage_a_amendment_table_sha256'] or
                m.get('stage_a_amendment_acceptance_sha256') != cfg['stage_a_amendment_acceptance_sha256'] or
                m.get('cache_prompt') is not False or m.get('harness_commit') != cfg['harness_commit']):
            _stop('candidate identity, authority or inputs differ')
        if (Path(str(m.get('registry_path') or '')).resolve() != registry_path.resolve() or
                m.get('registry_sha256') != digest_file(registry_path)):
            _stop('candidate registry does not bind the verified batch snapshot')
        cells = [(mode, node, seed) for (c, mode, node, seed) in grid if c == cid]
        expected_paths = [str(batch / cid / 'b2' / mode / f'{node}__s{seed}' / 'campaign_manifest.json') for mode, node, seed in cells]
        if m.get('root_manifests') != expected_paths: _stop('candidate root grid differs from the author-bound grid')
        if (m.get('thinking_on_rerun') == 'descriptive') != (len(modes_of[cid]) > 1):
            _stop('thinking-on rerun label differs from the grid')
        roots = []
        for (mode, node, seed), path in zip(cells, expected_paths):
            key = f'{cid}/b2/{mode}/{node}__s{seed}'; expected_keys.add(key)
            entry = state_roots.get(key)
            if not Path(path).resolve().is_relative_to(batch): _stop('root path escapes batch')
            root_dir = Path(path).parent
            _inside(batch, root_dir)
            names = ('root_trials.jsonl', 'root_events.jsonl', 'audit_cache.json', 'audit_configs.json',
                     'a4_observer_requests.jsonl', 'b1_proposals.jsonl')
            for name in ('job.json', 'post_check.json') + names:
                _inside(root_dir, root_dir / name)
            if not isinstance(entry, dict) or entry.get('path') != path or digest_file(path) != entry.get('sha256'):
                _stop('root missing or changed')
            preliminary = _read(path)
            hashes = preliminary.get('evidence_hashes') if isinstance(preliminary, dict) else None
            if not isinstance(hashes, dict) or set(hashes) != set(names) or any(hashes[k] is None for k in ('root_trials.jsonl', 'root_events.jsonl', 'audit_configs.json')):
                _stop('root evidence index incomplete')
            root = verify_campaign(path, expected_binding); _verify_b1_root_authority(path, head)
            job = _read(root_dir / 'job.json')
            for field in ('workers', 'host', 'W', 'llm_call_cap', 'proposal_schema'):
                if job.get(field) != cfg.get(field): _stop('root job parameters differ from authorization')
            if job.get('audit_seeds') != B2_AUDIT_SEEDS: _stop('root job audit seeds are not 9201–9210')
            if (job.get('authority_config') != cfg or job.get('phase') != 'b2' or job.get('node') != node or
                    job.get('seed') != seed or job.get('mode') != mode or job.get('dryrun') is not False or
                    job.get('harness_commit') != cfg['harness_commit'] or job.get('node_source_sha256') != node_sources[node] or
                    job.get('out') != str(root_dir) or job.get('binding') != expected_binding or
                    job.get('value_grids') != cfg['value_grids'] or not _authorized_candidate(job, cfg, registry)):
                _stop('root job authority, candidate or source binding differs')
            if (root.get('execution_label') != 'EVIDENCE' or root.get('phase') != 'b2' or root.get('candidate') != cid or
                    root.get('mode') != mode or root.get('node') != node or root.get('instance_seed') != seed):
                _stop('root identity differs from grid')
            records = read_rows(root_dir / 'root_trials.jsonl'); events = read_rows(root_dir / 'root_events.jsonl')
            novelty = [e['payload'] for e in events if e.get('event_type') == 'edit_novelty']
            forecasts = {e['trial_id']: e['payload'] for e in events if e.get('event_type') == 'exam_self_forecast'}
            diagnostics = {'trials': len(records), 'evaluated': len(novelty),
                'invalid': sum(r['decision'] == 'failed_invalid' for r in records),
                'duplicates': sum(bool(p.get('active_config_seen_before')) for p in novelty),
                'noops': sum(bool(p.get('active_config_equals_incumbent')) for p in novelty),
                'parse_failed': sum(bool(((r.get('extra') or {}).get('manager') or {}).get('parse_failed')) or
                    ((((r.get('extra') or {}).get('manager') or {}).get('llm_call')) or {}).get('parse_ok') is False for r in records),
                'forecast_queries': len(forecasts), 'forecast_query_failed': sum(r.get('status') == 'query_failed' for r in forecasts.values())}
            if root.get('diagnostics') != diagnostics: _stop('root diagnostics differ from ledger and events')
            completed = [e.get('payload') or {} for e in events if e.get('event_type') == 'campaign_completed']
            if len(completed) != 1: _stop('root completion event missing or duplicated')
            worker_count = sum(not ((r.get('extra') or {}).get('worker') or {}).get('worker_skipped', False) and r.get('decision') != 'skipped' for r in records)
            budget = completed[0].get('compute_budget')
            if not isinstance(budget, dict) or root.get('compute_budget') != budget:
                _stop('root budget differs from completion event')
            if (budget.get('max_worker_runs') != cfg['W'] or budget.get('max_llm_calls') != cfg['llm_call_cap'] or
                    type(budget.get('worker_runs')) is not int or not 0 <= budget['worker_runs'] <= cfg['W'] or
                    type(budget.get('llm_calls')) is not int or not 0 <= budget['llm_calls'] <= cfg['llm_call_cap']):
                _stop('root budget exceeds or differs from authorized caps')
            if budget['worker_runs'] != worker_count: _stop('worker count differs from trial ledger')
            call_events = [e.get('payload') or {} for e in events if e.get('event_type') in ('llm_call', 'llm_call_failed')]
            if any(type(e.get('llm_calls', 1)) is not int or e.get('llm_calls', 1) < 1 for e in call_events) or \
                    budget['llm_calls'] != sum(e.get('llm_calls', 1) for e in call_events):
                _stop('LLM call count differs from events')
            if root.get('termination') != ('worker_cap' if budget['worker_runs'] >= cfg['W'] else 'llm_cap_or_reserved_observer_pair'):
                _stop('termination label differs from budget')
            if root.get('cache_prompt') != cache_prompt_evidence(records, events): _stop('cache evidence differs from events')
            if (root.get('cache_prompt') or {}).get('all_false') is not True: _stop('root lacks cache-false evidence')
            if root.get('observer_evidence') != validate_observer_journal(root_dir / 'a4_observer_requests.jsonl', events):
                _stop('observer evidence differs from journal')
            if root.get('proposal_journal') != validate_proposal_journal(root_dir / 'b1_proposals.jsonl', records, events):
                _stop('proposal journal evidence differs from journal')
            if digest_file(root_dir / 'post_check.json') != entry.get('post_check_sha256'):
                _stop('root receiving certificate changed')
            recorded = root.get('d28') or {}
            recomputed = evaluate_ledger_paths([root_dir / 'root_trials.jsonl'], generated_utc=recorded.get('generated_utc'),
                                               manager_kind='langgraph', memory_mode='append_only_summary')
            if recorded != recomputed or node not in recomputed['nodes']:
                _stop('root D28 differs from verified ledger')
            node_spec = load_registered_node(node, repo_root=harness)
            start = {p: (harness / 'nodes' / node / p).read_text() for p in node_spec.editable_paths}
            proposals, checks = replay_campaign(records, start, node, f'{node}__s{seed}', 'EXAM', 'append_only_summary', cfg['W'], 1.)
            if root.get('replay_checks') != checks: _stop('root replay checks differ')
            audited = [p for p in proposals if not p.features.get('active_equals_incumbent') and not p.features.get('active_seen_before')]
            expected_configs = {}
            for proposal in audited:
                for files in (proposal.candidate_files, proposal.incumbent_files):
                    expected_configs[files_hash(files)] = {'node': node, 'files': files}
            if _read(root_dir / 'audit_configs.json') != expected_configs: _stop('audit configs differ from replay')
            cache_path = root_dir / 'audit_cache.json'
            cache = _read(cache_path) if cache_path.exists() else {}
            if set(cache) != set(expected_configs): _stop('audit cache keys differ from replay')
            reconstructed = []
            for proposal in audited:
                arrays = [cache[files_hash(files)] for files in (proposal.candidate_files, proposal.incumbent_files)]
                result = paired(*arrays)
                if result['k'] != len(B2_AUDIT_SEEDS): _stop('audit cache has incomplete paired seeds')
                trial = f'{node}__s{seed}-trial-{proposal.budget_index:03d}'
                reconstructed.append({'proposal_id': proposal.proposal_id, 'instance_id': f'{node}__s{seed}',
                    'node': node, 'mode': mode, 'audit_seeds': B2_AUDIT_SEEDS, 'candidate_hash': proposal.candidate_hash,
                    'incumbent_hash': proposal.incumbent_hash, 'candidate_metrics': arrays[0], 'incumbent_metrics': arrays[1],
                    **result, **{k: v for k, v in forecasts.get(trial, {}).items() if k in ('p_delta_positive', 'p_no_effect')}})
            if root.get('audited_proposals') != reconstructed: _stop('root audits differ from replay and cache')
            check_final_audit(root, node, seed)
            roots.append(root)
        if m.get('audited_proposals') != [p for r in roots for p in r['audited_proposals']]:
            _stop('candidate audits differ from verified roots')
        primary = [r for r in roots if r['mode'] == 'off']; rerun = [r for r in roots if r['mode'] != 'off']
        if m.get('final_audits') != [r['final_audits'][0] for r in primary]:
            _stop('candidate final-Y audits differ from its verified primary roots')
        if m.get('sensitivity_final_audits') != [r['final_audits'][0] for r in rerun]:
            _stop('candidate rerun final-Y audits differ from its verified rerun roots')
        pairs = [(a['node'], a['instance_id']) for a in m['final_audits']]
        if len(set(pairs)) != len(pairs) or set(pairs) != {(n, f'{n}__s{s}') for n in cfg['nodes'] for s in seeds}:
            _stop('primary final-Y audits do not cover exactly the author-bound grid')
        if m.get('cache_prompt_by_root') != [r.get('cache_prompt') for r in roots]:
            _stop('candidate cache evidence differs from roots')
        diagnostic_keys = ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed', 'forecast_queries', 'forecast_query_failed')
        if m.get('diagnostics') != {k: sum(r['diagnostics'].get(k, 0) for r in roots) for k in diagnostic_keys}:
            _stop('candidate diagnostics differ from verified roots')
    if set(state_roots) != expected_keys: _stop('batch has extra or missing completed roots')
    return manifests, {'batch_state_sha256': digest_file(batch / 'batch_state.json'),
                       'batch_manifests_sha256': digest_file(batch / 'b2_manifests.json'),
                       'authorization_checkout_head': head, 'b1_analysis_sha256': cfg['b1_analysis_sha256'],
                       'grid': {'verified': True, 'finalists': ids, 'nodes': list(cfg['nodes']), 'seeds': seeds,
                                'instances_per_node': len(seeds), 'audit_seeds': B2_AUDIT_SEEDS,
                                'modes': {cid: modes_of[cid] for cid in ids}}}
