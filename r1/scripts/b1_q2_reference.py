#!/usr/bin/env python3
"""Pre-fixed Q2 campaign-resampling reference; no model or audit values read.

AI-assisted (Codex). The seed, 10,000 draws, per-node draw count, pooling and
quantile interpolation are fixed in this file before examining the reference.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

SEED = 20261107
DRAWS = 10000
SOURCE_HEAD = 'e9641c1dd0ba6ee0f5a0373b2a6716b53fe64e58'
SOURCE_TREE = '6b1c0c6154a604c391f8b7684a2d4ce34ccddd1a'
OLD_HARNESS = '6adf3859de66c4814fcf376eed59880fbd8eeaf7'
NEW_HARNESS = 'a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
MODEL_SHA = '509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c'
INDEX_SHA = '812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab'
MANIFEST_SHA = 'f18f8a8b47ba17dc1da9e875d500831d6d0d03c69aa7d12b216444aeff1af98f'
BASE = 'results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z'
INDEX = 'results/r1/pilot/C3_sweep_index_20261028T033315Z.json'
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
W = 20
PER_NODE = 4


class ReferenceUnavailable(Exception):
    """The specified source cannot be read or has a blocking mismatch."""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    try:
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReferenceUnavailable('git source unavailable: '+repr(exc)) from exc


def blob(repo, revision, path):
    return git(repo, 'show', revision+':'+path)


def novelty_counts(events):
    """The same expressions as exam/campaign.py:191–196, restricted to novelty."""
    novelty = [e['payload'] for e in events if e['event_type'] == 'edit_novelty']
    return {'evaluated': len(novelty),
            'duplicates': sum(bool(p.get('active_config_seen_before')) for p in novelty)}


def linear_quantile(sorted_values, probability):
    pos = (len(sorted_values)-1)*probability
    left = int(pos)
    frac = pos-left
    return sorted_values[left]*(1-frac)+sorted_values[min(left+1,len(sorted_values)-1)]*frac


def source_block(text, start, end):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ReferenceUnavailable('duplicate-definition source markers changed')
    return text.split(start,1)[1].split(end,1)[0]


def function_ast(text, name):
    tree=ast.parse(text)
    found=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(found)!=1: raise ReferenceUnavailable('missing novelty helper '+name)
    return ast.dump(found[0],include_attributes=False)


def compare_definition(harness):
    source='src/autoresearch/control_plane/campaign.py'
    old=blob(harness,OLD_HARNESS,source).decode('utf-8')
    new=blob(harness,NEW_HARNESS,source).decode('utf-8')
    markers=(('    # D27: record-only novelty flags.','    records: list[TrialRecord] = []'),
             ('            # D27: record-only novelty flags on the evaluated trial.',
              '            # Compute cumulative repeated-bad count for this trial'))
    for a,b in markers:
        if source_block(old,a,b)!=source_block(new,a,b):
            raise ReferenceUnavailable('blocking duplicate-definition mismatch in '+a.strip())
    for name in ('_effective_config_at','_project_active_config','_config_sha256'):
        if function_ast(old,name)!=function_ast(new,name):
            raise ReferenceUnavailable('blocking duplicate-definition mismatch in '+name)
    changed=git(harness,'diff','--name-only',OLD_HARNESS,NEW_HARNESS,'--',
                'src/autoresearch/nodes',*[f'nodes/{n}' for n in NODES]).decode().strip()
    if changed: raise ReferenceUnavailable('blocking node-definition mismatch: '+changed)
    return {'result':'match', 'basis':'identical D27 initialization and emission blocks, novelty helper ASTs, and no changes to node/registry paths between pinned harness commits',
            'old_harness':OLD_HARNESS,'new_harness':NEW_HARNESS}


def compute(repo, harness, checkout):
    cfg=json.loads((checkout/'r1/scripts/configs/exam_b1_v2.json').read_text())
    reg=json.loads((checkout/'r1/exam/registry.yaml').read_text())
    anchor=next(x for x in reg['candidates'] if x['id']=='qwen25_coder_7b')
    if (cfg['nodes']!=list(NODES) or cfg['W']!=W or len(cfg['instance_seeds'])!=PER_NODE or
        anchor['base_repo']!='Qwen/Qwen2.5-Coder-7B-Instruct' or
        anchor['quant_source']['quantization']!='Q4_K_M' or anchor['quant_source']['sha256']!=MODEL_SHA):
        raise ReferenceUnavailable('blocking B1 model, quantization, node, W or campaign-count mismatch')
    tree=git(repo,'rev-parse',SOURCE_HEAD+':'+BASE).decode().strip()
    if tree!=SOURCE_TREE: raise ReferenceUnavailable('frozen source corpus tree mismatch')
    ib=blob(repo,SOURCE_HEAD,INDEX); mb=blob(repo,SOURCE_HEAD,BASE+'/manifest.json')
    if sha(ib)!=INDEX_SHA or sha(mb)!=MANIFEST_SHA:
        raise ReferenceUnavailable('frozen index or manifest digest mismatch')
    idx=json.loads(ib); man=json.loads(mb)
    if (idx['runs']!=W or idx['manager']['model_sha256']!=MODEL_SHA or
        man['memory_mode']!='append_only_summary' or man['runs']!=W or
        man['harness']['commit']!=OLD_HARNESS or man['harness']['dirty'] is not False or
        any(node not in idx['nodes'] or node not in man['nodes'] for node in NODES)):
        raise ReferenceUnavailable('blocking source model, memory, nodes or W mismatch')
    definition=compare_definition(harness)
    list_path=BASE+'/provenance/ledgers/roots'
    paths=git(repo,'ls-tree','-r','--name-only',SOURCE_HEAD,'--',list_path).decode().splitlines()
    groups={n:[] for n in NODES}
    for path in sorted(paths):
        parts=Path(path).parts
        if len(parts)<2 or parts[-1]!='root_events.jsonl': continue
        campaign=parts[-2]
        node=next((n for n in NODES if campaign.startswith(n+'__s')),None)
        if node is None: continue
        raw=blob(repo,SOURCE_HEAD,path)
        try:
            events=[json.loads(line) for line in raw.splitlines() if line.strip()]
            novelty=[e for e in events if e.get('event_type')=='edit_novelty']
            if (not novelty or any(e.get('campaign_id')!=campaign or not isinstance(e.get('payload'),dict) or
                    type(e['payload'].get('active_config_seen_before')) is not bool or
                    e['payload'].get('seen_before_resume')=='unknown' for e in novelty)):
                raise ReferenceUnavailable('unreadable or incompatible novelty ledger '+path)
            counts=novelty_counts(events)
        except (ValueError,KeyError,TypeError) as exc:
            raise ReferenceUnavailable('unreadable proposal ledger '+path+': '+repr(exc)) from exc
        groups[node].append({'campaign':campaign,'path':path,'sha256':sha(raw),**counts})
    if any(len(groups[n])!=idx['instances'] for n in NODES):
        raise ReferenceUnavailable('unreadable or missing required node-stratum ledgers')
    generator=random.Random(SEED); samples=[]
    for _ in range(DRAWS):
        selected=[generator.choice(groups[n]) for n in NODES for _ in range(PER_NODE)]
        den=sum(x['evaluated'] for x in selected)
        if den==0: raise ReferenceUnavailable('empty evaluated count in sampled campaigns')
        samples.append(sum(x['duplicates'] for x in selected)/den)
    samples.sort()
    return {'schema':'b1_anchor_duplicate_reference/v1','source':BASE,
        'method':'stratified campaign bootstrap predictive reference; pooled duplicate/evaluated rate',
        'lower':linear_quantile(samples,.005),'upper':linear_quantile(samples,.995),
        'quantile_definition':'linear interpolation at p*(N-1), 0-indexed sorted values',
        'seed':SEED,'draws':DRAWS,'campaigns_per_node_per_draw':PER_NODE,
        'source_commit':SOURCE_HEAD,'source_tree':SOURCE_TREE,'source_index_sha256':INDEX_SHA,
        'source_manifest_sha256':MANIFEST_SHA,'script_sha256':sha(Path(__file__).read_bytes()),
        'python_version':sys.version.split()[0], 'campaigns':groups,
        'comparability':{
            'blocking':{'proposer_and_quantization':{'result':'match','model':'Qwen/Qwen2.5-Coder-7B-Instruct','quantization':'Q4_K_M','gguf_sha256':MODEL_SHA},
                        'memory_mode':{'result':'match','value':'append_only_summary'},
                        'nodes':{'result':'match','value':list(NODES)},'W':{'result':'match','value':W},
                        'duplicate_definition':definition},
            'disclosed':{'host_gpu':'sweep-1 deepthought TITAN; B1 TASL-7 RTX 4090, subject to host check',
                         'llamacpp':'same recorded commit 620d222; different sm_52/sm_89 build and B1 flags',
                         'cache_prompt':'sweep-1 default with actual HTTP bodies not retained; B1 explicit false',
                         'context_length':'sweep-1 8192; B1 32768',
                         'a4_side_query':'B1 charged side query does not enter manager context',
                         'harness_pins':{'sweep1':OLD_HARNESS,'b1':NEW_HARNESS}}},
        'fallback':False, 'interpretation':'99% predictive resampling reference, not a confidence interval for the mean'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-repo',type=Path,required=True)
    p.add_argument('--harness-repo',type=Path,required=True);p.add_argument('--checkout',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:
        result=compute(a.source_repo,a.harness_repo,a.checkout)
    except (ReferenceUnavailable, OSError, ValueError, KeyError, StopIteration, UnicodeError, TypeError) as exc:
        result={'schema':'b1_anchor_duplicate_reference/v1','source':BASE,'lower':0.0,'upper':1.0,
                'fallback':True,'fallback_reason':str(exc),'seed':SEED,'draws':DRAWS,
                'script_sha256':sha(Path(__file__).read_bytes()),
                'interpretation':'descriptive fallback; scripted versus random discrimination remains unchanged'}
    if a.out.exists(): raise SystemExit('STOP: preserve existing reference; choose a fresh path')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'path':str(a.out),'sha256':sha(a.out.read_bytes()),'fallback':result['fallback'],
                      'lower':result['lower'],'upper':result['upper']}))


if __name__=='__main__': main()
