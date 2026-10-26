"""Manifest-driven exam analysis; finalists fixed by the byte-pinned X.5 rule before B1."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import yaml
from r1.exam.guards import frozen_digest, paired_instance_bootstrap, wilson_interval

RULE=Path(__file__).parent/'rules/x5_rule_v1.yaml'


def load_rule(path=RULE, expected=None):
    if expected is None: expected=Path(str(path)+'.sha256').read_text().split()[0]
    sha=frozen_digest(path,expected)
    rule=yaml.safe_load(Path(path).read_text())
    if rule['version']!='x5_rule/v1': raise ValueError('unsupported rule')
    return rule,sha


def finite_mean(values):
    values=[float(v) for v in values]
    if not values or not all(math.isfinite(v) for v in values): raise ValueError('finite nonempty values required')
    return sum(values)/len(values)


def choose_finalists(rows, rule):
    eligible=[r for r in rows if r['role']=='candidate' and r.get('stage_a_pass') and r.get('d28_pass')]
    ids=[r['candidate'] for r in rows]
    if len(set(ids))!=len(ids): raise ValueError('duplicate candidate analysis rows')
    order={r['candidate']:r['registry_order'] for r in rows}
    ranked=sorted(eligible,key=lambda r:(-float(r['mu_hat']), order[r['candidate']]))
    selected=ranked[:rule['finalists']['top_by_mean']]
    families={r['family'] for r in selected}
    missing=[r for r in ranked[len(selected):] if r['family'] not in families]
    if missing: selected+=missing[:rule['finalists']['absent_family_extra']]
    return [r['candidate'] for r in selected][:rule['finalists']['maximum']]


def bootstrap_mean(rows, *, field, rule):
    groups={}
    for r in rows: groups.setdefault(str(r['instance_id']),[]).append(float(r[field]))
    if not groups: raise ValueError('no clusters')
    clusters=list(groups.values());rng=np.random.default_rng(rule['bootstrap']['seed'])
    draws=[]
    for _ in range(rule['bootstrap']['resamples']):
        sample=[clusters[i] for i in rng.integers(0,len(clusters),len(clusters))]
        draws.append(finite_mean([v for cluster in sample for v in cluster]))
    lo,hi=np.quantile(draws,[.025,.975])
    return {'mean':finite_mean([v for cluster in clusters for v in cluster]),'lower':float(lo),'upper':float(hi),
            'unit':'node_instance_cluster','clusters':len(groups)}


def b1_summary(manifests, *, rule_path=RULE, expected=None):
    rule,sha=load_rule(rule_path,expected);rows=[]
    for m in manifests:
        if m.get('label')!='EXAM' or m.get('phase')!='b1' or m.get('status')!='COMPLETE':
            raise ValueError('analysis requires complete EXAM B1 manifests')
        if m.get('rule_sha256')!=sha: raise ValueError('manifest rule hash differs from frozen bytes')
        observations=m['audited_proposals']
        primary=[r for r in observations if r['mode']==m['primary_mode']]
        if not primary: raise ValueError('no primary audited increments')
        mean=bootstrap_mean(primary,field='delta_audit',rule=rule)
        modes={}
        for mode in ('off','on','always_on'):
            values=[r['delta_audit'] for r in observations if r['mode']==mode and r['node']==rule['thinking_mode']['sensitivity_node']]
            if values: modes[mode]=finite_mean(values)
        choice=max(modes,key=lambda k:(modes[k],k=='off')) if modes else m['primary_mode']
        forecasts=[r for r in primary if r.get('p_delta_positive') is not None]
        scores=[math.log(max(1e-12,min(1-1e-12,float(r['p_delta_positive'])))) if r['delta_audit']>0
                else math.log(max(1e-12,1-min(1-1e-12,float(r['p_delta_positive'])))) for r in forecasts]
        rows.append({'candidate':m['candidate'],'role':m['role'],'family':m['family'],
                     'stage_a_pass':m['stage_a_pass'],'d28_pass':m['d28_pass'],'registry_order':m['registry_order'],
                     'mu_hat':mean['mean'],'cluster_interval':mean,'b2_thinking_mode':choice,
                     'p_positive':sum(r['delta_audit']>0 for r in primary)/len(primary),
                     'increment_sd':float(np.std([r['delta_audit'] for r in primary],ddof=1)) if len(primary)>1 else None,
                     'a4_log_score':finite_mean(scores) if scores else None,
                     'a4_brier':finite_mean([(float(r['p_delta_positive'])-(r['delta_audit']>0))**2 for r in forecasts]) if forecasts else None,
                     'diagnostics':m.get('diagnostics',{})})
    return {'phase':'b1','label':'EXAM','rule_sha256':sha,'rows':rows,'finalists':choose_finalists(rows,rule)}


def stage_a_summary(manifests):
    return {'phase':'stage-a','label':'ENGINEERING_ONLY','rows':[
        {'candidate':m['candidate'],'passed':m['passed'],'failure_classes':m.get('failure_classes',[]),
         'free_parse':wilson_interval(m['free_parse_successes'],m['prompts']) if m.get('prompts') else None,
         'schema_parse':wilson_interval(m['schema_parse_successes'],m['prompts']) if m.get('prompts') else None,
         'cpu_pool_only':m.get('cpu_pool_only',False)} for m in manifests]}


def b2_summary(manifests):
    rows=[]
    for m in manifests:
        if m.get('label')!='EXAM' or m.get('phase')!='b2' or m.get('status')!='COMPLETE':
            raise ValueError('complete EXAM B2 manifests required')
        values=[r['final_y'] for r in m['final_audits']]
        rows.append({'candidate':m['candidate'],'final_y':finite_mean(values),'instances':len(values),
                     'gpu_hours':m['gpu_hours'],'mode':m['mode']})
    return {'phase':'b2','label':'EXAM','rows':sorted(rows,key=lambda r:(-r['final_y'],r['gpu_hours'])),
            'author_decision_pending':True}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['stage-a','b1','b2'])
    p.add_argument('manifests',nargs='+');p.add_argument('--rule',default=str(RULE));p.add_argument('--rule-sha256')
    a=p.parse_args(argv);ms=[json.loads(Path(x).read_text()) for x in a.manifests]
    result=b1_summary(ms,rule_path=a.rule,expected=a.rule_sha256) if a.phase=='b1' else (stage_a_summary(ms) if a.phase=='stage-a' else b2_summary(ms))
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__': main()
