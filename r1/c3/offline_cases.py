"""Static 16-case identity binding for M3; never schedules or runs a case.

This materializes a deterministic declaration only. It cannot prove that a
configuration has no data-dependent external I/O, that its dependencies are
available, or that the Linux execution boundary is sound. Production STOP
remains until those independent preflight obligations are met.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import PurePosixPath


class CaseStop(RuntimeError): pass


def _digest(data): return hashlib.sha256(data).hexdigest()


def bind_cases(cases,cache_snapshots):
    """Validate 16 selected cases and bind their files and OpenML cache hashes."""
    if not isinstance(cases,list) or len(cases)!=16 or not isinstance(cache_snapshots,dict):
        raise CaseStop('STOP: exactly 16 cases and a cache map are required')
    nodes={};case_ids=set();records=[]
    for case in cases:
        if not isinstance(case,dict):raise CaseStop('STOP: malformed case')
        cid=case.get('case_id');node=case.get('node');budget=case.get('budget_index')
        if (not isinstance(cid,str) or not cid or cid in case_ids or not isinstance(node,str) or not node
                or type(budget) is not int or budget not in (1,2)):
            raise CaseStop('STOP: duplicate or invalid case identity')
        case_ids.add(cid);nodes.setdefault(node,set())
        if budget in nodes[node]:raise CaseStop('STOP: duplicate node budget index')
        nodes[node].add(budget)
        seeds=[case.get(k) for k in ('instance_seed','train_seed','split_seed')]
        if any(type(seed) is not int for seed in seeds) or len(set(seeds))!=1:
            raise CaseStop('STOP: case seeds are missing or inconsistent')
        command=case.get('worker_command')
        if not isinstance(command,str) or not command or command.startswith('NOT CHECKED'):
            raise CaseStop('STOP: pinned worker command unavailable')
        files=case.get('files');expected=case.get('configuration_file_sha256')
        if not isinstance(files,dict) or not files or not isinstance(expected,dict) or set(files)!=set(expected):
            raise CaseStop('STOP: configuration file map not established')
        actual={}
        for name,text in files.items():
            if (not isinstance(name,str) or not name or PurePosixPath(name).is_absolute() or
                    any(part in ('','.','..') for part in name.split('/')) or not isinstance(text,str)):
                raise CaseStop('STOP: invalid configuration path or content')
            digest=_digest(text.encode())
            if expected[name]!=digest:raise CaseStop('STOP: configuration content digest mismatch')
            actual[name]=digest
        cache=None
        if node.startswith('openml_'):
            snap=cache_snapshots.get(node)
            if (not isinstance(snap,dict) or snap.get('node')!=node or
                    snap.get('offline_executability')!='NOT_ESTABLISHED'):
                raise CaseStop('STOP: matching cache identity snapshot required')
            cache=(snap.get('cache') or {}).get('sha256')
            if not isinstance(cache,str) or len(cache)!=64 or any(c not in '0123456789abcdef' for c in cache):
                raise CaseStop('STOP: invalid cache snapshot digest')
        records.append({'case_id':cid,'node':node,'budget_index':budget,'seed':seeds[0],
                        'worker_command':command,'configuration_file_sha256':dict(sorted(actual.items())),
                        'cache_snapshot_sha256':cache})
    if len(nodes)!=8 or any(values!={1,2} for values in nodes.values()):
        raise CaseStop('STOP: exactly two trial indices for each of eight nodes required')
    if set(cache_snapshots)!={n for n in nodes if n.startswith('openml_')}:
        raise CaseStop('STOP: cache map must match selected OpenML nodes exactly')
    records.sort(key=lambda x:x['case_id'])
    payload={'schema':'m3_static_case_binding/v1','cases':records,'offline_executability':'NOT_ESTABLISHED'}
    canonical=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    return {**payload,'binding_sha256':_digest(canonical)}
