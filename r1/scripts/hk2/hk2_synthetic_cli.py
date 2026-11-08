"""Offline synthetic-only CLI for the reviewed HK6 pure helpers.

JSON via stdin/stdout only. A synthetic label is a caller assertion, not
proof of provenance. Never submit jobs, access site resources or create files.
This is not the production audit CLI or an authorizing EVIDENCE path.
"""
import argparse
import hashlib
import json
import sys

from r1.scripts.hk2.hk2_audit_shards import merge_shards, select_shard
from r1.scripts.hk2.hk2_unit_history import assess_history

LABEL = 'SYNTHETIC_ONLY'
MAX_INPUT = 2 * 1024 * 1024


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out


def _invalid_constant(_value):
    raise ValueError('non-finite JSON number')


def _plan_id(plan, seeds, count):
    # select_shard validates pair identities, seeds and count before binding.
    select_shard(plan, seeds, count, 0)
    raw = json.dumps({'plan': plan, 'seeds': seeds, 'count': count},
                     sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def evaluate(action, obj):
    if not isinstance(obj, dict) or obj.get('label') != LABEL:
        raise ValueError('explicit synthetic label required')
    if action == 'history':
        if set(obj) != {'label', 'unit_id', 'attempts'}:
            raise ValueError('invalid history input')
        result = assess_history(obj['unit_id'], obj['attempts'])
    elif action in ('select', 'merge'):
        expected = {'label', 'plan', 'seeds', 'count', 'index' if action == 'select' else 'shards'}
        if set(obj) != expected:
            raise ValueError('invalid shard input')
        plan, seeds, count = obj['plan'], obj['seeds'], obj['count']
        identity = _plan_id(plan, seeds, count)
        if action == 'select':
            result = {'plan_sha256': identity, 'index': obj['index'],
                      'pairs': select_shard(plan, seeds, count, obj['index'])}
        else:
            shards = obj['shards']
            if not isinstance(shards, list):
                raise ValueError('shards must be a list')
            mapping = {}
            for shard in shards:
                if (not isinstance(shard, dict) or set(shard) != {'index', 'plan_sha256', 'rows'} or
                        type(shard['index']) is not int or shard['index'] in mapping or
                        shard['plan_sha256'] != identity):
                    raise ValueError('invalid shard identity or duplicate index')
                mapping[shard['index']] = shard['rows']
            result = {'plan_sha256': identity, 'rows': merge_shards(plan, seeds, count, mapping)}
    else:
        raise ValueError('unsupported action')
    return {'label': LABEL, 'execution_authorized': False, 'result': result}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('select', 'merge', 'history'))
    args = ap.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError('synthetic input exceeds size limit')
        obj = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
        answer = evaluate(args.action, obj)
        sys.stdout.write(json.dumps(answer, sort_keys=True, allow_nan=False) + '\n')
        if args.action == 'history' and answer['result']['state'] == 'STOP_CUT_TWICE':
            print('STOP: synthetic unit cut twice', file=sys.stderr)
            return 2
    except (ValueError, TypeError, UnicodeError, KeyError) as exc:
        print('STOP: synthetic input rejected: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
