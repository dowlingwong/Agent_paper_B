"""Pure audit-row sharding checks; no filesystem, scheduler, or authorization.

Input is an already determined ordered audit plan and explicit seed list. The
caller must independently bind those inputs and validate the produced audit
values and provenance. This module is not a runnable HK6 workflow.
"""
import math


class ShardError(ValueError):
    pass


_FIELDS = ('proposal_id', 'node', 'candidate_hash', 'incumbent_hash')


def _validated(plan, seeds, count):
    if type(count) is not int or count < 1:
        raise ShardError('invalid shard count')
    if not isinstance(plan, (list, tuple)) or not plan:
        raise ShardError('empty or invalid plan')
    if (not isinstance(seeds, (list, tuple)) or not seeds or
            any(type(seed) is not int or seed < 0 for seed in seeds) or len(set(seeds)) != len(seeds)):
        raise ShardError('invalid seed list')
    entries = []
    seen = set()
    for row in plan:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k] for k in _FIELDS):
            raise ShardError('invalid audit pair')
        if row['proposal_id'] in seen:
            raise ShardError('duplicate proposal id')
        seen.add(row['proposal_id'])
        entries.append({k: row[k] for k in _FIELDS})
    return entries, list(seeds)


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def select_shard(plan, seeds, count, index):
    """Return a deterministic ordered subset; count/index are zero-based."""
    entries, _ = _validated(plan, seeds, count)
    if type(index) is not int or not 0 <= index < count:
        raise ShardError('invalid shard index')
    return [entry for n, entry in enumerate(entries) if n % count == index]


def merge_shards(plan, seeds, count, shards):
    """Verify one audit result per authorized pair and return plan-order rows.

    ``shards`` must contain each numeric shard index exactly once. This checks
    structural completeness only, not file identity, metrics' scientific
    provenance, result correctness, or authorization.
    """
    entries, expected_seeds = _validated(plan, seeds, count)
    if not isinstance(shards, dict) or any(type(k) is not int for k in shards) or set(shards) != set(range(count)):
        raise ShardError('missing or invalid shard indices')
    by_id = {}
    for index in range(count):
        rows = shards[index]
        if not isinstance(rows, (list, tuple)):
            raise ShardError('invalid shard rows')
        expected = {row['proposal_id']: row for row in select_shard(entries, expected_seeds, count, index)}
        for row in rows:
            if not isinstance(row, dict):
                raise ShardError('invalid result row')
            pid = row.get('proposal_id')
            if not isinstance(pid, str) or pid not in expected or pid in by_id:
                raise ShardError('unexpected or duplicate result')
            if any(row.get(k) != expected[pid][k] for k in _FIELDS):
                raise ShardError('audit pair identity mismatch')
            if (not isinstance(row.get('seeds'), list) or
                any(type(seed) is not int for seed in row['seeds']) or row['seeds'] != expected_seeds):
                raise ShardError('wrong seeds or ordering')
            for field in ('candidate_metrics', 'incumbent_metrics'):
                values = row.get(field)
                if (not isinstance(values, list) or len(values) != len(expected_seeds) or
                    any(not _finite_number(v) for v in values)):
                    raise ShardError('invalid paired measurements')
            by_id[pid] = row
        if {row['proposal_id'] for row in rows} != set(expected):
            raise ShardError('missing audit pair')
    return [by_id[entry['proposal_id']] for entry in entries]
