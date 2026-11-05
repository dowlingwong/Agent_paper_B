"""Verify a complete authorized B1 batch before producing v2 finalists."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from r1.exam.analyze import thinking_off_capable
from r1.exam.guards import digest_file


def _stop(message):
    raise ValueError('STOP: B1 batch '+message)


def _read(path):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError) as exc: raise ValueError('STOP: B1 batch file unavailable or malformed') from exc


def verify_batch(batch, cfg, rule_sha):
    """Return verified candidate manifests; no inference, server, or mutation.

    The clean committed author note and PLAN are the process authority; this
    does not claim cryptographic authorship or resist a malicious same-UID writer.
    """
    from r1.exam.runtime import author_gate, read_registry, verify_campaign, _verify_b1_root_authority
    from r1.scripts.exam_runner import stage_a_pass_set
    from r1.exam.campaign import cache_prompt_evidence, read_rows
    from r1.exam.b1_observer_journal import validate_observer_journal
    if cfg.get('dryrun'): _stop('production verification refuses DRYRUN')
    head=author_gate(cfg,'b1',rule_sha)
    if not isinstance(head,str) or len(head)!=40: _stop('authorized HEAD absent')
    batch=Path(batch).resolve(strict=True)
    state=_read(batch/'batch_state.json')
    if state.get('status')!='COMPLETE' or state.get('phase')!='b1' or state.get('execution_label')!='EVIDENCE':
        _stop('is not a completed evidence batch')
    registry_path=batch/'registry_snapshot.yaml'
    if registry_path.resolve().parent!=batch or digest_file(registry_path)!=digest_file(cfg['registry']):
        _stop('registry snapshot differs from configured registry')
    registry=read_registry(registry_path)
    expected_binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(registry_path),
        'rule_sha256':rule_sha,'value_grids_sha256':digest_file(cfg['value_grids'])},sort_keys=True).encode()).hexdigest()
    if state.get('binding')!=expected_binding or state.get('rule_sha256')!=rule_sha:
        _stop('configuration binding mismatch')
    candidates={r['id'] for r in registry['candidates'] if r.get('role')=='candidate'}
    eligible=stage_a_pass_set(cfg,candidates,v2=True)
    specs=registry['software_anchors']+[r for r in registry['candidates'] if r['role']=='anchor']+\
          [r for r in registry['candidates'] if r['role']=='candidate']+registry.get('sensitivities',[])
    expected=[]
    for spec in specs:
        if spec['id'] not in eligible: continue
        if spec.get('role') in ('candidate','sensitivity') and not thinking_off_capable(spec.get('thinking_policy')): continue
        expected.append(spec)
    ids=[s['id'] for s in expected]
    if not ids or len(set(ids))!=len(ids): _stop('empty or duplicate eligible set')
    data=_read(batch/'b1_manifests.json')
    manifests=data.get('manifests') if isinstance(data,dict) and data.get('label')=='EXAM' else None
    if not isinstance(manifests,list) or [m.get('candidate') for m in manifests]!=ids:
        _stop('candidate set or registry order differs from Stage A passes')
    state_roots=state.get('completed')
    if not isinstance(state_roots,dict): _stop('completed root index missing')
    expected_keys=set()
    for spec,m in zip(expected,manifests):
        cid=spec['id']; candidate_path=batch/cid/'b1_manifest.json'
        if not candidate_path.resolve().is_relative_to(batch) or _read(candidate_path)!=m:
            _stop('candidate manifest differs from aggregate')
        if (m.get('execution_label')!='EVIDENCE' or m.get('authorization_checkout_head')!=head or
            m.get('stage_a_table_sha256')!=cfg['stage_a_table_sha256'] or
            m.get('stage_a_amendment_table_sha256')!=cfg['stage_a_amendment_table_sha256'] or
            m.get('stage_a_amendment_acceptance_sha256')!=cfg['stage_a_amendment_acceptance_sha256']):
            _stop('candidate authority or Stage A inputs differ')
        modes=[(spec.get('thinking_policy') or {}).get('mode','off')]
        if (spec.get('thinking_policy') or {}).get('switchable') is True:
            if eligible[cid].get('thinking_disabled_due_grammar'): _stop('required sensitivity disabled')
            modes.append('on')
        grids=[]
        for index,mode in enumerate(modes):
            nodes=cfg['nodes'] if index==0 else ['openml_credit_approval']
            grids.extend((mode,node,seed) for node in nodes for seed in cfg['instance_seeds'])
        expected_paths=[str(batch/cid/'b1'/mode/f'{node}__s{seed}'/'campaign_manifest.json') for mode,node,seed in grids]
        if m.get('root_manifests')!=expected_paths: _stop('candidate root grid differs from authorized design')
        roots=[]
        for (mode,node,seed),path in zip(grids,expected_paths):
            key=f'{cid}/b1/{mode}/{node}__s{seed}';expected_keys.add(key)
            entry=state_roots.get(key)
            if not Path(path).resolve().is_relative_to(batch): _stop('root path escapes batch')
            if not isinstance(entry,dict) or entry.get('path')!=path or digest_file(path)!=entry.get('sha256'):
                _stop('root missing or changed')
            root=verify_campaign(path,expected_binding);_verify_b1_root_authority(path,head)
            if (root.get('execution_label')!='EVIDENCE' or root.get('phase')!='b1' or root.get('candidate')!=cid or
                root.get('mode')!=mode or root.get('node')!=node or root.get('instance_seed')!=seed):
                _stop('root identity differs from grid')
            names={'root_trials.jsonl','root_events.jsonl','audit_cache.json','audit_configs.json','a4_observer_requests.jsonl'}
            hashes=root.get('evidence_hashes')
            if not isinstance(hashes,dict) or set(hashes)!=names or any(hashes[k] is None for k in ('root_trials.jsonl','root_events.jsonl','audit_configs.json')):
                _stop('root evidence index incomplete')
            if spec.get('kind') not in ('random_valid','scripted'):
                records=read_rows(Path(path).parent/'root_trials.jsonl');events=read_rows(Path(path).parent/'root_events.jsonl')
                if root.get('cache_prompt')!=cache_prompt_evidence(records,events): _stop('cache evidence differs from events')
                if root.get('observer_evidence')!=validate_observer_journal(Path(path).parent/'a4_observer_requests.jsonl',events):
                    _stop('observer evidence differs from journal')
            if digest_file(Path(path).parent/'post_check.json')!=entry.get('post_check_sha256'):
                _stop('root receiving certificate changed')
            if node not in (root.get('d28') or {}).get('nodes',{}): _stop('root D28 node missing')
            roots.append(root)
        if m.get('audited_proposals')!=[p for r in roots for p in r['audited_proposals']]:
            _stop('candidate audits differ from verified roots')
        primary=[r for r in roots if r['mode']==m.get('primary_mode')]
        if not primary or m.get('d28_pass')!=all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in primary):
            _stop('candidate D28 differs from verified primary roots')
        if m.get('cache_prompt_by_root')!=[r.get('cache_prompt') for r in roots]:
            _stop('candidate cache evidence differs from roots')
        if spec.get('kind') not in ('random_valid','scripted') and not all((r.get('cache_prompt') or {}).get('all_false') is True for r in roots):
            _stop('root lacks cache-false evidence')
    if set(state_roots)!=expected_keys: _stop('batch has extra or missing completed roots')
    return manifests, {'batch_state_sha256':digest_file(batch/'batch_state.json'),
                       'batch_manifests_sha256':digest_file(batch/'b1_manifests.json'),
                       'authorization_checkout_head':head,'eligible_candidates':ids}
