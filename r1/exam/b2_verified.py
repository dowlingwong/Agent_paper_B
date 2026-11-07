"""Verify a completed v2 B2 evidence batch before applying the frozen ranking.

Authority is the clean committed checkout plus the author's dated PLAN row and
note. Repository writers can forge those records: the author's instruction and
independent review are the process boundary, not cryptographic authentication.
This reader does not authorize B2 or remove the runner's separate phase STOP.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from r1.harness import REPO
from r1.exam.b1_batch import _inside, refuse_sealed
from r1.exam.b2_ranking import _rank_grid
from r1.exam.guards import digest_file


def _stop(message):
    raise ValueError('STOP: B2 verification ' + message)


def _read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError('STOP: B2 verification missing or malformed JSON') from exc


def _path(path):
    path = Path(path)
    return path if path.is_absolute() else REPO / path


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            _stop('authorization contains duplicate JSON key')
        result[key] = value
    return result


def _repo_bytes(path, head):
    path = Path(path)
    path = path if path.is_absolute() else REPO / path
    refuse_sealed(path)
    try:
        resolved = path.resolve(strict=True)
        rel = resolved.relative_to(REPO.resolve())
        raw = resolved.read_bytes()
        committed = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{head}:{rel.as_posix()}'], stderr=subprocess.DEVNULL)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValueError('STOP: B2 verification committed file unavailable') from exc
    if raw != committed:
        _stop('file bytes differ from committed checkout')
    return raw


def _power_row(plan, note_sha):
    # Reuse the existing strict dated-section/table parser: replace only exact
    # first cells, so neither prose nor another author row can match this test.
    from r1.exam.runtime import _x5_author_row
    original = re.compile(r'^(\s*\|\s*)R1-EXAM-RULE-X5V2(\s*\|)', re.M)
    target = re.compile(r'^(\s*\|\s*)R1-EXAM-B2-POWER-PLAN(\s*\|)', re.M)
    rewritten = original.sub(r'\1R1-EXAM-RULE-X5V2-OTHER\2', plan)
    rewritten = target.sub(r'\1R1-EXAM-RULE-X5V2\2', rewritten)
    if not _x5_author_row(rewritten, note_sha): return False
    lines = plan.splitlines()
    matches = [i for i, line in enumerate(lines) if target.match(line)]
    if len(matches) != 1: return False
    first = matches[0]
    while first and lines[first-1].lstrip().startswith('|'): first -= 1
    header = [x.strip().strip('*` ') for x in lines[first].strip().strip('|').split('|')]
    if len(header) < 2: return False
    return bool(re.fullmatch(r"(?:author(?:'s)?\s+)?decision(?:\s*\([^)]*\))?", header[1], re.I))


def _authority(config_path):
    from r1.exam.runtime import _x5_author_row, load_config
    try:
        head = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', '--verify', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain', '--untracked-files=all'], text=True).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('STOP: B2 verification cannot inspect checkout') from exc
    if not re.fullmatch(r'[0-9a-f]{40}', head) or dirty:
        _stop('requires clean committed checkout')
    config_raw = _repo_bytes(config_path, head)
    config_file = Path(config_path)
    if not config_file.is_absolute(): config_file = REPO / config_file
    cfg = load_config(config_file)
    if cfg.get('dryrun') is True:
        _stop('production verification refuses DRYRUN config')
    note_path = (cfg.get('authorizations') or {}).get('b2')
    if not isinstance(note_path, str) or not note_path or note_path.startswith('TODO_'):
        _stop('author B2 note is absent')
    raw = _repo_bytes(note_path, head)
    try:
        text = raw.decode('utf-8')
        blocks = re.findall(r'```json\s*(.*?)```', text, re.S)
        if len(blocks) > 1: _stop('authorization has multiple JSON blocks')
        note = json.loads(blocks[0] if blocks else text, object_pairs_hook=_pairs)
        plan = _repo_bytes(REPO / 'docs/r1/PLAN.md', head).decode('utf-8')
    except (UnicodeError, ValueError, TypeError) as exc:
        raise ValueError('STOP: B2 verification malformed authorization or PLAN') from exc
    if not isinstance(note, dict): _stop('authorization must be an object')
    rule_sha = cfg.get('rule_sha256')
    if not isinstance(rule_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', rule_sha):
        _stop('configured rule digest is invalid')
    if (note.get('author') != 'Dowling Wong' or note.get('phase') != 'b2' or
        note.get('approved') is not True or note.get('rule_sha256') != rule_sha or
        note.get('config_sha256') != hashlib.sha256(config_raw).hexdigest()):
        _stop('author note does not bind phase, rule and config bytes')
    if not _x5_author_row(plan, rule_sha) or not _power_row(plan, hashlib.sha256(raw).hexdigest()):
        _stop('dated rule or B2 power-plan decision is absent')
    if (note.get('nodes') != cfg.get('nodes') or note.get('instances_per_node') != cfg.get('b2_instances_per_node') or
        type(note.get('instances_per_node')) is not int or not 1 <= note['instances_per_node'] <= 89 or
        note.get('b1_analysis_sha256') != cfg.get('b1_analysis_sha256')):
        _stop('author note does not bind B2 nodes, count and B1 analysis')
    if (not isinstance(cfg.get('nodes'), list) or len(cfg['nodes']) != 3 or any(not isinstance(n, str) for n in cfg['nodes']) or len(set(cfg['nodes'])) != 3 or
        set(cfg['nodes']) not in ({'digits_mlp', 'openml_credit_approval', 'openml_ionosphere'},
                                  {'tabular_mlp', 'openml_credit_approval', 'openml_ionosphere'})):
        _stop('B2 node scope requires the three authorized CPU nodes')
    return cfg, head, hashlib.sha256(raw).hexdigest()


def _match_hash(path, expected, name):
    refuse_sealed(path)
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected) or digest_file(path) != expected:
        _stop(name + ' digest mismatch')


def _hours(state, candidate, recorded):
    intervals = []
    for entry in state.get('server_intervals', []):
        if not isinstance(entry, dict): _stop('malformed server interval')
        if entry.get('candidate') != candidate or entry.get('phase') != 'b2' or entry.get('mode') != 'off': continue
        start, end = entry.get('start'), entry.get('end')
        if (type(start) not in (int, float) or type(end) not in (int, float) or
            not math.isfinite(start) or not math.isfinite(end) or end < start or entry.get('cost_is_upper_bound')):
            _stop('incomplete or invalid server interval')
        intervals.append((start, end))
    intervals.sort()
    if not intervals or any(b[0] < a[1] for a, b in zip(intervals, intervals[1:])):
        _stop('missing or overlapping server intervals')
    value = sum((end - start) / 3600 for start, end in intervals)
    if type(recorded) not in (int, float) or not math.isfinite(recorded) or recorded < 0 or not math.isclose(value, recorded, rel_tol=0.0, abs_tol=1e-12):
        _stop('candidate GPU hours differ from intervals')


def b2_summary_verified(batch, config_path, *, rule_path=None, expected=None):
    """Return a v2 ranking only after committed authority and complete receipt checks."""
    from r1.exam.runtime import read_registry, verify_campaign
    from r1.scripts.exam_runner import check_template_repairs, stage_a_pass_set, template_repair_record
    from r1.exam.analyze import RULE_V2, is_v2, load_rule, thinking_off_capable
    from r1.exam.observer import _authorized_candidate
    from r1.exam.campaign import cache_prompt_evidence, read_rows
    from r1.exam.b1_observer_journal import validate_observer_journal
    cfg, head, note_sha = _authority(config_path)
    rule_sha = cfg['rule_sha256']
    rule, selected_sha = load_rule(rule_path or RULE_V2, expected)
    if not is_v2(rule) or selected_sha != rule_sha: _stop('selected analysis rule differs from authorized v2 rule')
    for path_key, sha_key in (('rule', 'rule_sha256'), ('b1_analysis', 'b1_analysis_sha256'),
                               ('stage_a_table', 'stage_a_table_sha256'),
                               ('stage_a_amendment_table', 'stage_a_amendment_table_sha256'),
                               ('stage_a_amendment_acceptance', 'stage_a_amendment_acceptance_sha256')):
        path = Path(cfg[path_key]); path = path if path.is_absolute() else REPO / path
        _match_hash(path, cfg[sha_key], path_key)
    screen = _read(_path(cfg['b1_analysis']))
    if (not isinstance(screen, dict) or screen.get('phase') != 'b1' or screen.get('label') != 'EXAM' or screen.get('execution_label') != 'EVIDENCE' or
        screen.get('rule_sha256') != rule_sha or not isinstance(screen.get('batch_verification'), dict)):
        _stop('B1 analysis is not a verified v2 evidence summary')
    b1proof = screen['batch_verification']
    if (not re.fullmatch(r'[0-9a-f]{40}', str(b1proof.get('authorization_checkout_head') or '')) or
        any(not re.fullmatch(r'[0-9a-f]{64}', str(b1proof.get(key) or '')) for key in ('batch_state_sha256', 'batch_manifests_sha256')) or
        not isinstance(b1proof.get('eligible_candidates'), list)):
        _stop('B1 verification proof is incomplete')
    finalists = screen.get('finalists')
    if not isinstance(finalists, list) or not finalists or any(not isinstance(x, str) or not x for x in finalists) or len(set(finalists)) != len(finalists):
        _stop('B1 finalists missing or duplicated')
    if any(cid not in b1proof['eligible_candidates'] for cid in finalists): _stop('B1 finalist missing from verified eligible set')
    rows = screen.get('rows')
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows): _stop('B1 rows missing')
    if any(not isinstance(r.get('candidate'), str) for r in rows): _stop('malformed B1 candidate identifier')
    by_candidate = {r.get('candidate'): r for r in rows}
    if len(by_candidate) != len(rows): _stop('duplicate B1 analysis row')
    for cid in finalists:
        r = by_candidate.get(cid) or {}
        if (r.get('role') != 'candidate' or r.get('stage_a_pass') is not True or r.get('d28_pass') is not True or
            r.get('thinking_off_eligible') is not True or r.get('mu_hat_mode') != 'off' or r.get('b2_thinking_mode') != 'off'):
            _stop('B1 finalist lacks v2 eligibility')
    refuse_sealed(batch)
    batch = Path(batch).resolve(strict=True)
    for name in ('batch_state.json', 'b2_manifests.json', 'registry_snapshot.yaml'):
        _inside(batch, batch / name)
    state = _read(batch / 'batch_state.json')
    if not isinstance(state, dict) or state.get('status') != 'COMPLETE' or state.get('phase') != 'b2' or state.get('label') != 'EXAM' or state.get('execution_label') != 'EVIDENCE':
        _stop('batch is not completed B2 evidence')
    registry_path = batch / 'registry_snapshot.yaml'
    if digest_file(registry_path) != digest_file(_path(cfg['registry'])): _stop('registry snapshot mismatch')
    registry = read_registry(registry_path)
    registry_by_id = {x['id']: x for x in registry['candidates']}
    if cfg.get('cache_prompt') is not False: _stop('B2 config must pin cache_prompt false')
    check_template_repairs(cfg, registry['software_anchors'] + registry['candidates'] + registry.get('sensitivities', []))
    stage_cfg = dict(cfg)
    for key in ('stage_a_table', 'stage_a_amendment_table'):
        stage_cfg[key] = str(_path(cfg[key]))
    eligible = stage_a_pass_set(stage_cfg, {x['id'] for x in registry['candidates'] if x['role'] == 'candidate'}, v2=True)
    for cid in finalists:
        spec = registry_by_id.get(cid) or {}
        if spec.get('role') != 'candidate' or not thinking_off_capable(spec.get('thinking_policy')) or cid not in eligible:
            _stop('finalist differs from Stage A or registry')
    binding = hashlib.sha256(json.dumps({'config': cfg, 'registry_sha256': digest_file(registry_path),
        'rule_sha256': rule_sha, 'value_grids_sha256': digest_file(_path(cfg['value_grids']))}, sort_keys=True).encode()).hexdigest()
    if state.get('binding') != binding or state.get('rule_sha256') != rule_sha:
        _stop('batch config/rule binding mismatch')
    aggregate = _read(batch / 'b2_manifests.json')
    if not isinstance(aggregate, dict) or aggregate.get('label') != 'EXAM' or not isinstance(aggregate.get('manifests'), list): _stop('candidate aggregate missing')
    manifests = aggregate['manifests']
    if any(not isinstance(m, dict) or m.get('purpose', 'primary') != 'primary' for m in manifests):
        _stop('primary batch must not contain separate sensitivity manifests')
    ids = [m.get('candidate') for m in manifests]
    if any(not isinstance(cid, str) or not cid for cid in ids): _stop('malformed candidate identifier')
    if len(ids) != len(set(ids)) or set(ids) != set(finalists): _stop('candidate batch differs from B1 finalists')
    state_roots = state.get('completed')
    if not isinstance(state_roots, dict): _stop('completed root index missing')
    expected_off_keys = {f'{cid}/b2/off/{node}__s{seed}' for cid in finalists for node in cfg['nodes']
                         for seed in range(9011, 9011 + cfg['b2_instances_per_node'])}
    if any(not isinstance(key, str) for key in state_roots): _stop('malformed root index key')
    observed_off_keys = {key for key in state_roots if len(key.split('/')) == 4 and key.split('/')[1:3] == ['b2', 'off']}
    if observed_off_keys != expected_off_keys: _stop('primary root index differs from complete grid')
    for m in manifests:
        cid = m['candidate']; candidate_dir = batch / cid
        _inside(batch, candidate_dir / 'b2_manifest.json')
        if _read(candidate_dir / 'b2_manifest.json') != m: _stop('candidate aggregate differs from retained file')
        if (m.get('b1_analysis_sha256') != cfg['b1_analysis_sha256'] or m.get('rule_sha256') != rule_sha or
            m.get('registry_sha256') != digest_file(registry_path) or Path(str(m.get('registry_path') or '')).resolve() != registry_path or
            m.get('gpu_hours_status') != 'recorded_dedicated_intervals' or m.get('role') != 'candidate' or
            m.get('family') != registry_by_id[cid].get('family') or m.get('model_sha256') != (registry_by_id[cid].get('quant_source') or {}).get('sha256') or
            m.get('template_repair') != template_repair_record(registry_by_id[cid]) or m.get('cache_prompt') is not False or
            m.get('stage_a_table_sha256') != cfg['stage_a_table_sha256'] or
            m.get('stage_a_amendment_table_sha256') != cfg['stage_a_amendment_table_sha256'] or
            m.get('stage_a_amendment_acceptance_sha256') != cfg['stage_a_amendment_acceptance_sha256'] or
            m.get('stage_a_pass') is not True or m.get('stage_a_pass_source') != eligible[cid].get('stage_a_pass_source') or
            m.get('harness_commit') != cfg.get('harness_commit') or m.get('authorization_checkout_head') != head):
            _stop('candidate authority, registry or cost status mismatch')
        _hours(state, cid, m.get('gpu_hours'))
        primary_paths = [candidate_dir / 'b2' / 'off' / f'{node}__s{seed}' / 'campaign_manifest.json'
                         for node in cfg['nodes'] for seed in range(9011, 9011 + cfg['b2_instances_per_node'])]
        roots = m.get('root_manifests')
        if not isinstance(roots, list) or any(not isinstance(x, str) for x in roots) or len(roots) != len(set(roots)) or any(str(path) not in roots for path in primary_paths):
            _stop('primary root paths missing or duplicated')
        for raw_root in roots:
            _inside(candidate_dir, Path(raw_root))
            allowed_on = {str(candidate_dir / 'b2' / 'on' / f'{node}__s{seed}' / 'campaign_manifest.json')
                          for node in cfg['nodes'] for seed in range(9011, 9011 + cfg['b2_instances_per_node'])}
            if raw_root not in {str(path) for path in primary_paths} | allowed_on:
                _stop('candidate includes unexpected root path')
        final_audits = []
        for path in primary_paths:
            _inside(batch, path); root_dir = path.parent
            for name in ('job.json', 'post_check.json', 'root_trials.jsonl', 'root_events.jsonl', 'audit_cache.json', 'audit_configs.json', 'a4_observer_requests.jsonl'):
                _inside(root_dir, root_dir / name)
            root = _read(path); node = root.get('node'); seed = root.get('instance_seed')
            key = f'{cid}/b2/off/{node}__s{seed}'; entry = state_roots.get(key)
            if not isinstance(entry, dict) or entry.get('path') != str(path) or entry.get('sha256') != digest_file(path) or entry.get('post_check_sha256') != digest_file(root_dir / 'post_check.json'):
                _stop('root receipt missing or changed')
            hashes = root.get('evidence_hashes')
            if not isinstance(hashes, dict) or set(hashes) != {'root_trials.jsonl', 'root_events.jsonl', 'audit_cache.json', 'audit_configs.json', 'a4_observer_requests.jsonl'}:
                _stop('root evidence index malformed')
            if any(hashes[name] is None for name in ('root_trials.jsonl', 'root_events.jsonl', 'audit_configs.json')):
                _stop('required root evidence is missing')
            root = verify_campaign(path, binding); job = _read(root_dir / 'job.json')
            records = read_rows(root_dir / 'root_trials.jsonl'); events = read_rows(root_dir / 'root_events.jsonl')
            if (root.get('cache_prompt') != cache_prompt_evidence(records, events) or
                root.get('observer_evidence') != validate_observer_journal(root_dir / 'a4_observer_requests.jsonl', events)):
                _stop('root lacks cache-false or bound observer evidence')
            if (root.get('execution_label') != 'EVIDENCE' or root.get('phase') != 'b2' or root.get('candidate') != cid or root.get('mode') != 'off' or
                node not in cfg['nodes'] or type(seed) is not int or not 9011 <= seed < 9011 + cfg['b2_instances_per_node'] or
                path != candidate_dir / 'b2' / 'off' / f'{node}__s{seed}' / 'campaign_manifest.json' or
                job.get('phase') != 'b2' or job.get('mode') != 'off' or job.get('node') != node or job.get('seed') != seed or
                job.get('binding') != binding or job.get('out') != str(root_dir) or job.get('dryrun') is not False or
                (job.get('candidate') or {}).get('id') != cid or job.get('audit_seeds') != list(range(9201, 9211)) or
                any(job.get(field) != cfg.get(field) for field in ('host', 'workers', 'W', 'llm_call_cap', 'value_grids', 'proposal_schema')) or
                not _authorized_candidate(job, stage_cfg, registry)):
                _stop('root identity or job mismatch')
            audits = root.get('final_audits')
            if not isinstance(audits, list) or len(audits) != 1: _stop('root final audit missing')
            if not isinstance(audits[0], dict) or audits[0].get('node') != node or audits[0].get('instance_id') != f'{node}__s{seed}':
                _stop('root final audit identity differs')
            final_audits.extend(audits)
        if m.get('final_audits') != final_audits: _stop('candidate audits differ from roots')
    result = _rank_grid(manifests, finalists=finalists, nodes=cfg['nodes'], instances_per_node=cfg['b2_instances_per_node'],
                        rule_sha256=rule_sha, execution_label='EVIDENCE')
    return {**result, 'label': 'EXAM', 'execution_label': 'EVIDENCE',
            'batch_verification': {'authorization_checkout_head': head, 'authorization_note_sha256': note_sha,
                'batch_state_sha256': digest_file(batch / 'batch_state.json'),
                'batch_manifests_sha256': digest_file(batch / 'b2_manifests.json')}}
