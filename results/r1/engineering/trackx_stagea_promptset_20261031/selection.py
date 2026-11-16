"""Preparation only. Predetermine source trials and validate candidate prompt bytes.

This does not reconstruct prompts, execute models, or publish files. The caller
must supply exact per-trial prompt text and active keys reconstructed separately.
"""
from __future__ import annotations
import gzip, hashlib, json
from pathlib import Path

# Fixed before reading metrics or prompt content. Equal near-balanced node weight.
NODES = ('digits_mlp','openml_breast_w','openml_ionosphere','tabular_mlp')
QUOTAS = (13,13,12,12)

def sha(data): return hashlib.sha256(data).hexdigest()

def choose(node_ledgers):
    """Rows ordered by node, root seed, then budget index; trials 2+ only.

    Paths are identified by the exact <node>__s<integer> directory. Selection
    is done before looking at prompt availability, model quality or metrics.
    """
    out=[]
    for node,quota in zip(NODES,QUOTAS):
        roots=[]
        for path in node_ledgers[node]:
            name=Path(path).parent.name; prefix=node+'__s'
            if not name.startswith(prefix) or not name[len(prefix):].isdigit(): raise ValueError('invalid source root '+name)
            roots.append((int(name[len(prefix):]),Path(path)))
        roots.sort(); seen=set(); selected=[]
        for seed,path in roots:
            if seed in seen: raise ValueError('duplicate root seed')
            seen.add(seed); raw=path.read_bytes(); data=gzip.decompress(raw) if path.suffix=='.gz' else raw
            records=[json.loads(x) for x in data.splitlines() if x.strip()]
            indices=[r.get('budget_index') for r in records]
            if any(not isinstance(i,int) for i in indices) or len(indices)!=len(set(indices)): raise ValueError('invalid or duplicate trial index')
            records.sort(key=lambda r:r['budget_index'])
            for record in records:
                if record['budget_index'] < 2: continue
                if record.get('node_id')!=node or record.get('memory_mode')!='append_only_summary': raise ValueError('node/memory mismatch')
                selected.append({'node':node,'seed':seed,'path':str(path),'source_sha256':sha(raw),'ledger_sha256':sha(data),'record':record})
                if len(selected)==quota: break
            if len(selected)==quota: break
        if len(selected)!=quota: raise ValueError('insufficient fixed records for '+node)
        out.extend(selected)
    return out

def validate(selected, candidates):
    """Fail closed on missing rows, duplicate trials and original context SHA.

    Candidate key = (node, seed, trial_id); value has prompt, active_keys.
    Context verification confirms bytes only, not active-key correctness.
    """
    if len(selected)!=50: raise ValueError('not 50 selected')
    seen=set(); checked=[]
    for item in selected:
        r=item['record']; key=(item['node'],item['seed'],r['trial_id'])
        if key in seen: raise ValueError('duplicate trial')
        seen.add(key)
        c=candidates.get(key)
        if not c or not c.get('prompt') or not c.get('active_keys'): raise ValueError('missing prompt/active keys: '+str(key))
        manager=(r.get('extra') or {}).get('manager') or {}
        actual=sha(c['prompt'].encode('utf-8')); expected=manager.get('context_sha256')
        if not expected or actual!=expected: raise ValueError('original context hash mismatch: '+str(key))
        checked.append({**item,'prompt_sha256':actual,'active_keys':c['active_keys']})
    return checked
