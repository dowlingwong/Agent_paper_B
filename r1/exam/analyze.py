"""Manifest-driven exam analysis; finalists fixed by the byte-pinned X.5 rule before B1."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import yaml
from r1.exam.guards import artifact_label, digest_file, frozen_digest, paired_instance_bootstrap, wilson_interval

RULE=Path(__file__).parent/'rules/x5_rule_v1.yaml'
# x5_rule/v2 (PLAN R1-MAIN-PROPOSER (a), R1-EXAM-ALWAYS-ON-SKIP): thinking-off selection for B1/B2.
# The default stays v1 because Stage A's config (exam_portal.json) binds v1 (MAC runbook M2 step 2,
# a recorded deviation from the draft, which pointed the default at v2).  B1/B2 v2 configs name v2.
RULE_V2=Path(__file__).parent/'rules/x5_rule_v2.yaml'
SUPPORTED_RULES=('x5_rule/v1','x5_rule/v2')


def is_v2(rule):
    return bool(rule) and rule.get('version')=='x5_rule/v2'


def _validate_v2(rule):
    """Fail closed on a v2 rule whose mode fields are not the quoted string 'off' (bare off is YAML False)."""
    modes={'ranking_mode':rule.get('ranking_mode'),'thinking_mode.primary':rule['thinking_mode'].get('primary'),
           'thinking_mode.b2_mode':rule['thinking_mode'].get('b2_mode'),'selection.mode':rule['selection'].get('mode')}
    bad={k:v for k,v in modes.items() if not isinstance(v,str) or v!='off'}
    if bad: raise ValueError(f'x5_rule/v2 mode fields must be the string "off": {bad}')
    # Only 'skip' is implemented and ruled (R1-EXAM-ALWAYS-ON-SKIP); the draft's alternative
    # 'run_descriptive' has no code path, so it is refused rather than half-supported.
    if rule['thinking_mode'].get('always_on_in_b1')!='skip':
        raise ValueError('x5_rule/v2 always_on_in_b1 must be skip (R1-EXAM-ALWAYS-ON-SKIP)')
    sens=rule['thinking_mode'].get('b1_sensitivity') or {}
    if not isinstance(sens.get('node'),str) or not sens['node']: raise ValueError('x5_rule/v2 b1_sensitivity.node required')
    if (sens.get('enabled') is not True or sens.get('mode')!='on' or
            type(sens.get('instances')) is not int or sens['instances']!=4 or
            sens.get('role')!='descriptive_only' or sens['node']!='openml_credit_approval'):
        raise ValueError('x5_rule/v2 requires the four-instance descriptive thinking-on sensitivity')
    if rule['eligibility'].get('d28_scope')!='thinking_off_only':
        raise ValueError('x5_rule/v2 D28 eligibility must use thinking off only')
    if rule['eligibility'].get('exclude_thinking_policy_mode')!='always_on': raise ValueError('x5_rule/v2 must exclude always_on models')
    if rule['selection'].get('ties')!='lower_gpu_hours': raise ValueError('x5_rule/v2 B2 ties must go to lower GPU-h')


def load_rule(path=RULE, expected=None):
    if expected is None: expected=Path(str(path)+'.sha256').read_text().split()[0]
    sha=frozen_digest(path,expected)
    rule=yaml.safe_load(Path(path).read_text())
    if rule['version'] not in SUPPORTED_RULES: raise ValueError('unsupported rule')
    if is_v2(rule): _validate_v2(rule)
    return rule,sha


def thinking_off_capable(policy):
    """R1-MAIN-PROPOSER (a): able to run with thinking off = a non-thinking model or a declared off_switch.

    ``policy`` is the frozen registry ``thinking_policy``.  Always-on models are never capable; a
    switchable model needs its declared ``off_switch``; a missing policy (software anchors) is not a
    candidate and is treated as not capable."""
    if not isinstance(policy,dict): return False
    if policy.get('mode')=='always_on': return False
    if policy.get('mode')!='off': return False
    return policy.get('off_switch') is True or policy.get('switchable') is not True


def finite_mean(values):
    values=[float(v) for v in values]
    if not values or not all(math.isfinite(v) for v in values): raise ValueError('finite nonempty values required')
    return sum(values)/len(values)


def choose_finalists(rows, rule):
    eligible=[r for r in rows if r['role']=='candidate' and r.get('stage_a_pass') and r.get('d28_pass') and r.get('mu_hat') is not None]
    if is_v2(rule):
        # v2 ranks only thinking-off-capable rows, on thinking-off mu_hat (b1_summary computes it so).
        eligible=[r for r in eligible if r.get('thinking_off_eligible') is True and r.get('mu_hat_mode')=='off']
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


def b1_summary(manifests, *, rule_path=RULE, expected=None, synthetic=False):
    rule,sha=load_rule(rule_path,expected);rows=[]
    if is_v2(rule):
        if not synthetic:
            raise ValueError('STOP: B1 finalist analysis requires a verified complete batch and Stage A eligible set')
        if not manifests or any(m.get('execution_label')!='DRYRUN' for m in manifests):
            raise ValueError('STOP: B1 synthetic analysis accepts DRYRUN manifests only')
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
        if is_v2(rule):
            rows.append(_b1_row_v2(m,source,observations,rule));continue
        primary=[r for r in observations if r['mode']==m['primary_mode']]
        if not primary:
            rows.append({'candidate':m['candidate'],'source_label':artifact_label(source),'role':m['role'],'family':m['family'],
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
        rows.append({'candidate':m['candidate'],'source_label':artifact_label(source),'role':m['role'],'family':m['family'],
                     'stage_a_pass':m['stage_a_pass'],'d28_pass':m['d28_pass'],'registry_order':m['registry_order'],
                     'a4_forecast_summary':forecast_summary(primary,m.get('diagnostics',{})),
                     'mu_hat':mean['mean'],'cluster_interval':mean,'b2_thinking_mode':choice,
                     'p_positive':sum(r['delta_audit']>0 for r in primary)/len(primary),
                     'increment_sd':float(np.std([r['delta_audit'] for r in primary],ddof=1)) if len(primary)>1 else None,
                     'a4_log_score':finite_mean(scores) if scores else None,
                     'a4_brier':finite_mean([(float(r['p_delta_positive'])-(r['delta_audit']>0))**2 for r in forecasts]) if forecasts else None,
                     'diagnostics':m.get('diagnostics',{})})
    return {'phase':'b1','label':'DRYRUN' if is_v2(rule) else 'EXAM','rule_sha256':sha,'rows':rows,'finalists':choose_finalists(rows,rule)}


def _b1_row_v2(m, source, observations, rule):
    """x5_rule/v2 B1 row: mu_hat over thinking-off proposals only; thinking-on rows descriptive only."""
    policy=source.get('thinking_policy')
    capable=thinking_off_capable(policy) if m['role']=='candidate' else None
    if m['role']=='candidate' and not capable and rule['thinking_mode']['always_on_in_b1']=='skip':
        raise ValueError('always-thinking model has a B1 manifest although x5_rule/v2 always_on_in_b1 is skip')
    if capable and m.get('primary_mode')!='off': raise ValueError('x5_rule/v2 B1 primary mode must be off')
    primary=[r for r in observations if r['mode']=='off']
    node=rule['thinking_mode']['b1_sensitivity']['node']
    sensitivity={}
    for mode in ('off','on','always_on'):
        values=[r['delta_audit'] for r in observations if r['mode']==mode and r['node']==node]
        if values: sensitivity[mode]=finite_mean(values)
    base={'candidate':m['candidate'],'source_label':artifact_label(source),'role':m['role'],'family':m['family'],
          'stage_a_pass':m['stage_a_pass'],'d28_pass':m['d28_pass'],'registry_order':m['registry_order'],
          'rule_version':'x5_rule/v2','thinking_policy_mode':(policy or {}).get('mode'),
          'thinking_off_eligible':capable,'mu_hat_mode':'off','b2_thinking_mode':'off',
          'thinking_on_sensitivity':{'node':node,'means_by_mode':sensitivity,'role':'descriptive_never_changes_b2_mode'},
          'a4_forecast_summary':forecast_summary(primary,m.get('diagnostics',{})),'diagnostics':m.get('diagnostics',{})}
    if not primary:
        return {**base,'mu_hat':None,'cluster_interval':None,'unrankable_reason':'no_noninert_nonduplicate_thinking_off_audits'}
    mean=bootstrap_mean(primary,field='delta_audit',rule=rule)
    forecasts=[r for r in primary if r.get('p_delta_positive') is not None]
    scores=[math.log(max(1e-12,min(1-1e-12,float(r['p_delta_positive'])))) if r['delta_audit']>0
            else math.log(max(1e-12,1-min(1-1e-12,float(r['p_delta_positive'])))) for r in forecasts]
    return {**base,'mu_hat':mean['mean'],'cluster_interval':mean,
            'p_positive':sum(r['delta_audit']>0 for r in primary)/len(primary),
            'increment_sd':float(np.std([r['delta_audit'] for r in primary],ddof=1)) if len(primary)>1 else None,
            'a4_log_score':finite_mean(scores) if scores else None,
            'a4_brier':finite_mean([(float(r['p_delta_positive'])-(r['delta_audit']>0))**2 for r in forecasts]) if forecasts else None}


def stage_a_summary(manifests):
    return {'phase':'stage-a','label':'ENGINEERING_ONLY','rows':[
        {'candidate':m['candidate'],'source_label':m.get('source_label','source unresolved'),'passed':m['passed'],'failure_classes':m.get('failure_classes',[]),
         'free_parse':wilson_interval(m['free_parse_successes'],m['prompts']) if m.get('prompts') else None,
         'schema_parse':wilson_interval(m['schema_parse_successes'],m['prompts']) if m.get('prompts') else None,
         'cpu_pool_only':m.get('cpu_pool_only',False)} for m in manifests]}


def _v2_sha():
    return Path(str(RULE_V2)+'.sha256').read_text().split()[0]


def b2_summary(manifests, *, rule_path=None, expected=None):
    """B2 summary.

    * With a rule (v1 or v2): every manifest's ``rule_sha256`` must equal the loaded rule's sha;
      under x5_rule/v2 the summary is ``_b2_summary_v2``, under v1 the unchanged v1 ranking.
    * Without a rule: the historical v1 summary, kept only for manifests that carry no v2 stamp.
      A manifest stamped ``rule_version == 'x5_rule/v2'`` or carrying the v2 rule sha is refused,
      so v2 B2 results can never be ranked under v1 semantics by omission.
    """
    if rule_path is not None:
        rule,sha=load_rule(rule_path,expected)
        for m in manifests:
            if m.get('rule_sha256')!=sha:
                raise ValueError(f'B2 manifest {m.get("candidate")!r} rule hash differs from the given rule ({rule["version"]})')
        if is_v2(rule): return _b2_summary_v2(manifests,rule,sha)
    else:
        v2sha=_v2_sha()
        for m in manifests:
            if m.get('rule_version')=='x5_rule/v2' or m.get('rule_sha256')==v2sha:
                raise ValueError('x5_rule/v2 B2 manifest requires the v2 rule (pass --rule x5_rule_v2.yaml with its sha)')
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
        rows.append({'candidate':m['candidate'],'source_label':m['source_label'],'final_y':finite_mean(values),'instances':len(values),
                     'purpose':m.get('purpose','primary'),'schema_mode':m.get('schema_mode','manager_proposal/v1'),'gpu_hours':m['gpu_hours'],'mode':m['mode'],'other_mode_audits':m.get('sensitivity_final_audits',[])})
    return {'phase':'b2','label':'EXAM','rows':sorted([r for r in rows if r['purpose']=='primary'],key=lambda r:(-r['final_y'],r['gpu_hours'] if r['gpu_hours'] is not None else math.inf)),
            'schema_sensitivity_rows':[r for r in rows if r['purpose']=='schema_free_sensitivity'],
            'author_decision_pending':True}


def _b2_final_values(m):
    values=[]
    for r in m['final_audits']:
        if r['seeds']!=list(range(9201,9211)) or len(r['metrics'])!=10: raise ValueError('ten fresh B2 audits required')
        value=finite_mean(r['metrics'])
        if not math.isclose(value,float(r['final_y']),abs_tol=1e-12): raise ValueError('B2 final Y differs from raw audits')
        values.append(value)
    return values


def _b2_summary_v2(manifests, rule, sha):
    """x5_rule/v2: rank only primary thinking-off rows by final audited Y; ties to lower GPU-h.

    A primary manifest in any other mode is refused.  The top-3 thinking-on reruns (the manifest's
    ``sensitivity_final_audits``) and any ``thinking_on_descriptive`` manifest are reported under
    ``thinking_on_descriptive`` and never enter the ranking."""
    primary=[];schema=[];descriptive=[];primary_candidates=set()
    for m in manifests:
        if m.get('label')!='EXAM' or m.get('phase')!='b2' or m.get('status')!='COMPLETE':
            raise ValueError('complete EXAM B2 manifests required')
        if m.get('rule_sha256')!=sha: raise ValueError('B2 manifest rule hash differs from frozen x5_rule/v2 bytes')
        purpose=m.get('purpose','primary')
        if purpose=='thinking_on_descriptive':
            if m.get('mode')=='off': raise ValueError('thinking_on_descriptive manifest must not be thinking-off')
            descriptive.append({'candidate':m['candidate'],'mode':m['mode'],'final_y':finite_mean(_b2_final_values(m)),'source':'manifest'})
            continue
        if purpose=='primary' and m.get('mode')!='off':
            raise ValueError(f'x5_rule/v2 refuses a primary B2 manifest in mode {m.get("mode")!r}; B2 runs thinking off')
        if purpose=='primary':
            candidate=m.get('candidate')
            if candidate in primary_candidates:
                raise ValueError(f'duplicate primary B2 candidate: {candidate!r}')
            primary_candidates.add(candidate)
        values=_b2_final_values(m)
        row={'candidate':m['candidate'],'source_label':m['source_label'],'final_y':finite_mean(values),'instances':len(values),
             'purpose':purpose,'schema_mode':m.get('schema_mode','manager_proposal/v1'),'gpu_hours':m['gpu_hours'],'mode':m['mode'],
             'template_repair':m.get('template_repair')}
        if purpose=='primary': primary.append(row)
        elif purpose=='schema_free_sensitivity': schema.append(row)
        else: raise ValueError(f'unknown B2 purpose {purpose!r}')
        rerun=m.get('sensitivity_final_audits') or []
        if rerun:
            ys=[float(r['final_y']) for r in rerun]
            descriptive.append({'candidate':m['candidate'],'mode':'on','final_y':finite_mean(ys),'instances':len(ys),
                                'source':'top3_thinking_on_rerun','label':m.get('thinking_on_rerun','descriptive')})
    # Until an independently reviewed, author-bound B2 power plan validates the
    # complete unique node/instance grid, no v2 ranking is safe to publish.
    raise ValueError('STOP: B2 node/instance grid has not been verified against the author-bound power plan')
    ranked=sorted(primary,key=lambda r:(-r['final_y'],r['gpu_hours'] if r['gpu_hours'] is not None else math.inf))
    return {'phase':'b2','label':'EXAM','rule_version':'x5_rule/v2','rule_sha256':sha,'rows':ranked,
            'selection':{'quantity':rule['selection']['quantity'],'mode':'off','ties':'lower_gpu_hours',
                         'rule_top':ranked[0]['candidate'] if ranked else None},
            'schema_sensitivity_rows':schema,'thinking_on_descriptive':descriptive,
            'author_decision_pending':True}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['stage-a','b1','b2'])
    p.add_argument('manifests',nargs='+');p.add_argument('--rule',default=str(RULE));p.add_argument('--rule-sha256')
    a=p.parse_args(argv);ms=[json.loads(Path(x).read_text()) for x in a.manifests]
    result=b1_summary(ms,rule_path=a.rule,expected=a.rule_sha256) if a.phase=='b1' else (stage_a_summary(ms) if a.phase=='stage-a' else b2_summary(ms,rule_path=a.rule,expected=a.rule_sha256))
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__': main()
