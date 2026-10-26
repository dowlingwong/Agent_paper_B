"""Manifest-driven exam analysis; finalists fixed by the byte-pinned X.5 rule before B1."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import yaml
from r1.exam.guards import digest_file, frozen_digest, paired_instance_bootstrap, wilson_interval

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
    eligible=[r for r in rows if r['role']=='candidate' and r.get('stage_a_pass') and r.get('d28_pass') and r.get('mu_hat') is not None]
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


def forecast_summary(rows, diagnostics):
    scored=[r for r in rows if r.get('p_delta_positive') is not None]
    for r in scored:
        if not 0<=float(r['p_delta_positive'])<=1: raise ValueError('forecast probability outside [0,1]')
    bins=[]
    for i in range(5):
        members=[r for r in scored if min(4,int(float(r['p_delta_positive'])*5))==i]
        bins.append({'lower':i/5,'upper':(i+1)/5,'count':len(members),
                     'mean_probability':finite_mean([r['p_delta_positive'] for r in members]) if members else None,
                     'observed_positive_rate':finite_mean([r['delta_audit']>0 for r in members]) if members else None})
    return {'audited_primary_proposals':len(rows),'scored_primary_forecasts':len(scored),
            'primary_forecast_coverage':len(scored)/len(rows) if rows else None,
            'query_failures_all_modes':diagnostics.get('forecast_query_failed'),
            'observer_queries_all_modes':diagnostics.get('forecast_queries'),
            'calibration':{'method':'five_fixed_probability_bins_descriptive','bins':bins},
            'p_no_effect_evaluation':'pending_author_outcome_definition; probabilities retained, no threshold invented'}


def b1_summary(manifests, *, rule_path=RULE, expected=None):
    rule,sha=load_rule(rule_path,expected);rows=[]
    for m in manifests:
        if m.get('label')!='EXAM' or m.get('phase')!='b1' or m.get('status')!='COMPLETE':
            raise ValueError('analysis requires complete EXAM B1 manifests')
        if m.get('rule_sha256')!=sha: raise ValueError('manifest rule hash differs from frozen bytes')
        registry_path=Path(m['registry_path'])
        if digest_file(registry_path)!=m['registry_sha256']: raise ValueError('registry snapshot digest mismatch')
        registry=yaml.safe_load(registry_path.read_text())
        all_rows=registry['software_anchors']+[r for r in registry['candidates'] if r['role']=='anchor']+[r for r in registry['candidates'] if r['role']=='candidate']+registry.get('sensitivities',[])
        index=next(i for i,r in enumerate(all_rows) if r['id']==m['candidate'])
        source=all_rows[index]
        if (m['family'],m['role'],m['registry_order'])!=(source['family'],source['role'],index): raise ValueError('family/role/order differs from frozen registry')
        observations=m['audited_proposals']
        for r in observations:
            if r['audit_seeds']!=list(range(9101,9105)): raise ValueError('B1 audit seed mismatch')
            a,b=r['candidate_metrics'],r['incumbent_metrics']
            if len(a)!=4 or len(b)!=4: raise ValueError('four paired B1 audits required')
            delta=finite_mean(a)-finite_mean(b)
            if not math.isclose(delta,float(r['delta_audit']),abs_tol=1e-12): raise ValueError('B1 delta differs from raw audits')
        primary=[r for r in observations if r['mode']==m['primary_mode']]
        if not primary:
            rows.append({'candidate':m['candidate'],'role':m['role'],'family':m['family'],
                         'stage_a_pass':m['stage_a_pass'],'d28_pass':m['d28_pass'],'registry_order':m['registry_order'],
                         'mu_hat':None,'cluster_interval':None,'b2_thinking_mode':m['primary_mode'],
                         'a4_forecast_summary':forecast_summary(primary,m.get('diagnostics',{})),
                         'unrankable_reason':'no_noninert_nonduplicate_primary_audits','diagnostics':m.get('diagnostics',{})})
            continue
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
                     'a4_forecast_summary':forecast_summary(primary,m.get('diagnostics',{})),
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
        values=[]
        for r in m['final_audits']:
            if r['seeds']!=list(range(9201,9211)) or len(r['metrics'])!=10: raise ValueError('ten fresh B2 audits required')
            value=finite_mean(r['metrics'])
            if not math.isclose(value,float(r['final_y']),abs_tol=1e-12): raise ValueError('B2 final Y differs from raw audits')
            values.append(value)
        rows.append({'candidate':m['candidate'],'final_y':finite_mean(values),'instances':len(values),
                     'purpose':m.get('purpose','primary'),'schema_mode':m.get('schema_mode','manager_proposal/v1'),'gpu_hours':m['gpu_hours'],'mode':m['mode'],'other_mode_audits':m.get('sensitivity_final_audits',[])})
    return {'phase':'b2','label':'EXAM','rows':sorted([r for r in rows if r['purpose']=='primary'],key=lambda r:(-r['final_y'],r['gpu_hours'] if r['gpu_hours'] is not None else math.inf)),
            'schema_sensitivity_rows':[r for r in rows if r['purpose']=='schema_free_sensitivity'],
            'author_decision_pending':True}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['stage-a','b1','b2'])
    p.add_argument('manifests',nargs='+');p.add_argument('--rule',default=str(RULE));p.add_argument('--rule-sha256')
    a=p.parse_args(argv);ms=[json.loads(Path(x).read_text()) for x in a.manifests]
    result=b1_summary(ms,rule_path=a.rule,expected=a.rule_sha256) if a.phase=='b1' else (stage_a_summary(ms) if a.phase=='stage-a' else b2_summary(ms))
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__': main()
