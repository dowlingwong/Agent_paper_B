"""Read-only binding of recovered replay cases and supplied cache identities.

This is a planning artifact only. It does not prevent later changes, prove the
cache is complete, enforce network isolation, or authorize any replay.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from r1.c3.offline_config_checks import check_cases, ConfigStop
from r1.c3.offline_preflight import snapshot, SnapshotStop
from r1.scripts.c3_env_replay import Stop, select_cases, verify_collector_binding, verify_corpus


class RecoveryStop(RuntimeError):
    pass


def bind_recovered_cases(paper, harness, cache_sources, cache_copies):
    """Bind frozen recovered cases to six explicitly supplied cache copies.

    The caller supplies paths to candidate copies. Distinct paths and equal
    hashes do not establish independent storage: files can be hard-linked.
    This function performs no writes and is neither a launch gate nor proof
    of isolation, privacy or offline executability.
    """
    paper, harness = Path(paper), Path(harness)
    try:
        corpus = verify_corpus(paper)
        collector = verify_collector_binding(paper)
        cases = select_cases(paper, corpus, harness)
        nodes = {case['node'] for case in cases if case['node'].startswith('openml_')}
        if not isinstance(cache_sources, dict) or not isinstance(cache_copies, dict):
            raise RecoveryStop('STOP: source and copy cache maps required')
        if set(cache_sources) != nodes or set(cache_copies) != nodes or len(nodes) != 6:
            raise RecoveryStop('STOP: exactly the six selected OpenML cache pairs required')
        resolved = []
        for node in sorted(nodes):
            for path in (cache_sources[node], cache_copies[node]):
                p = Path(path)
                if p.is_symlink() or not p.is_dir():
                    raise RecoveryStop('STOP: cache must be a real directory')
                resolved.append(p.resolve(strict=True))
        for index, left in enumerate(resolved):
            for right in resolved[index + 1:]:
                if left == right or left in right.parents or right in left.parents:
                    raise RecoveryStop('STOP: cache directories must be distinct and non-overlapping')
        pairs = {}
        for node in sorted(nodes):
            source = snapshot(harness, node, cache_sources[node])
            copy = snapshot(harness, node, cache_copies[node])
            if source != copy:
                raise RecoveryStop(f'STOP: source and supplied cache differ for {node}')
            pairs[node] = source
        checked = check_cases(cases, pairs, harness)
    except (Stop, SnapshotStop, ConfigStop, OSError, ValueError, TypeError, KeyError) as exc:
        raise RecoveryStop(f'STOP: recovered configuration binding failed: {exc}') from exc
    payload = {
        'schema': 'm3_recovered_case_binding/v1',
        'corpus': {k: v for k, v in corpus.items() if k not in ('index_doc', 'sweeps')},
        'collector': collector,
        'config_checks': checked,
        'cache_pairs': pairs,
        'offline_executability': 'NOT_ESTABLISHED',
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    return {**payload, 'binding_sha256': hashlib.sha256(canonical).hexdigest()}
