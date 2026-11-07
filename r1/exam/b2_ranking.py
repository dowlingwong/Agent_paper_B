"""Synthetic v2 B2 grid/ranking core; it does not authorize evidence analysis.

The caller supplies an explicit synthetic finalist set, node list and instance
count.  Production still STOPs until the B2 author decision, note, received
root evidence and cost provenance have their own reviewed integration.
"""
from __future__ import annotations

import math


def _number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f'B2 {name} must be a finite number')
    return float(value)


def _audit(row):
    if not isinstance(row, dict):
        raise ValueError('B2 audit must be an object')
    seeds = row.get('seeds')
    if not isinstance(seeds, list) or any(type(seed) is not int for seed in seeds) or seeds != list(range(9201, 9211)):
        raise ValueError('B2 audits require ordered seeds 9201–9210')
    metrics = row.get('metrics')
    if not isinstance(metrics, list) or len(metrics) != 10:
        raise ValueError('B2 audit requires ten metrics')
    values = [_number(x, 'metric') for x in metrics]
    mean = sum(values) / len(values)
    if not math.isclose(_number(row.get('final_y'), 'final_y'), mean, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError('B2 final Y differs from raw audits')
    return mean


def synthetic_b2_rank(manifests, *, finalists, nodes, instances_per_node, rule_sha256):
    """Rank DRYRUN fixtures on an explicit complete grid, with no evidence claim."""
    from r1.exam.analyze import RULE_V2, load_rule
    if not isinstance(finalists, list) or not finalists or any(not isinstance(x, str) or not x for x in finalists) or len(set(finalists)) != len(finalists):
        raise ValueError('B2 synthetic finalists must be nonempty and unique')
    if not isinstance(nodes, list) or not nodes or any(not isinstance(x, str) or not x for x in nodes) or len(set(nodes)) != len(nodes):
        raise ValueError('B2 synthetic nodes must be nonempty and unique')
    if type(instances_per_node) is not int or not 1 <= instances_per_node <= 89:
        raise ValueError('B2 synthetic count must fit seeds 9011–9099')
    if not isinstance(rule_sha256, str) or len(rule_sha256) != 64 or any(c not in '0123456789abcdef' for c in rule_sha256):
        raise ValueError('B2 frozen rule SHA required')
    rule, _ = load_rule(RULE_V2, expected=rule_sha256)
    if rule.get('version') != 'x5_rule/v2' or rule.get('selection', {}).get('quantity') != 'b2_final_audited_y':
        raise ValueError('B2 synthetic ranking requires the frozen v2 final-Y rule')
    expected = {(node, f'{node}__s{seed}') for node in nodes for seed in range(9011, 9011 + instances_per_node)}
    if len({instance for _, instance in expected}) != len(expected):
        raise ValueError('B2 canonical instance ID collision')
    if not isinstance(manifests, list):
        raise ValueError('B2 manifests must be a list')
    primary = {}
    for m in manifests:
        if not isinstance(m, dict) or m.get('label') != 'EXAM' or m.get('execution_label') != 'DRYRUN' or m.get('phase') != 'b2' or m.get('status') != 'COMPLETE':
            raise ValueError('B2 synthetic ranking requires complete EXAM DRYRUN manifests')
        if m.get('rule_sha256') != rule_sha256:
            raise ValueError('B2 manifest rule hash mismatch')
        purpose = m.get('purpose', 'primary')
        if purpose not in ('primary', 'schema_free_sensitivity', 'thinking_on_descriptive'):
            raise ValueError('B2 unknown manifest purpose')
        if purpose != 'primary':
            # Sensitivities never fill the primary grid or affect ranking.
            continue
        cid = m.get('candidate')
        if not isinstance(cid, str) or cid not in finalists:
            raise ValueError('B2 extra primary candidate')
        if cid in primary:
            raise ValueError('B2 duplicate primary candidate')
        if m.get('mode') != 'off' or m.get('primary_mode') != 'off':
            raise ValueError('B2 primary mode and primary_mode must both be thinking-off')
        rows = m.get('final_audits')
        if not isinstance(rows, list):
            raise ValueError('B2 final audit grid missing')
        seen = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('B2 audit must be an object')
            if not isinstance(row.get('node'), str) or not isinstance(row.get('instance_id'), str):
                raise ValueError('B2 final audit identity must contain strings')
            key = (row['node'], row['instance_id'])
            if key not in expected or key in seen:
                raise ValueError('B2 final audit grid has unexpected or duplicate instance')
            seen[key] = _audit(row)
        if set(seen) != expected:
            raise ValueError('B2 final audit grid incomplete')
        gpu = _number(m.get('gpu_hours'), 'GPU hours')
        if gpu < 0:
            raise ValueError('B2 GPU hours cannot be negative')
        primary[cid] = {'candidate': cid, 'final_y': sum(seen.values()) / len(seen),
                        'gpu_hours': gpu, 'instances': len(seen), 'mode': 'off'}
    if set(primary) != set(finalists):
        raise ValueError('B2 primary finalists incomplete')
    # The rule does not specify a third tie-break if both numbers are equal.
    ranked = sorted((primary[cid] for cid in finalists), key=lambda row: (-row['final_y'], row['gpu_hours']))
    tied = len(ranked) > 1 and (ranked[0]['final_y'], ranked[0]['gpu_hours']) == (ranked[1]['final_y'], ranked[1]['gpu_hours'])
    return {'label': 'DRYRUN', 'phase': 'b2', 'rule_sha256': rule_sha256, 'rows': ranked,
            'rule_top': None if tied else ranked[0]['candidate'], 'unresolved_exact_tie': tied, 'author_decision_pending': True,
            'provenance': 'synthetic_inputs_not_authority_or_received_evidence'}
