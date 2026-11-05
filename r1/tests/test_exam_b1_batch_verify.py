"""B1 complete-batch verifier, synthetic files only, no training or server."""
import hashlib
import json
from pathlib import Path
import pytest
from r1.exam import analyze, runtime
from r1.exam.guards import digest_file
from r1.liveness.check import evaluate_ledger_paths


def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,sort_keys=True))


def fixture(tmp_path,monkeypatch):
    import subprocess
    from r1.harness import harness_root
    from autoresearch.nodes.registry import load_registered_node
    from r1.c3.features import replay_campaign
    from r1.scripts import exam_runner
    head='a'*40;rule_sha=digest_file(analyze.RULE_V2);harness=Path(harness_root())
    harness_sha=subprocess.check_output(['git','-C',str(harness),'rev-parse','HEAD'],text=True).strip()
    anchors=[{'id':'random_valid','role':'anchor','family':'random','kind':'random_valid'},
             {'id':'scripted','role':'anchor','family':'scripted','kind':'scripted'},
             {'id':'qwen25_coder_7b','role':'anchor','family':'qwen','thinking_policy':{'mode':'off','switchable':False}}]
    candidates=[{'id':'a','role':'candidate','family':'fa','thinking_policy':{'mode':'off','switchable':True,'off_switch':True}},
                {'id':'b','role':'candidate','family':'fb','thinking_policy':{'mode':'off','switchable':False}}]
    specs=anchors+candidates;registry={'software_anchors':anchors[:2],'candidates':anchors[2:]+candidates}
    reg=tmp_path/'registry.yaml';write(reg,registry)
    stage=tmp_path/'stage.json';write(stage,{'rows':[{'candidate':s['id'],'passed':True} for s in specs]})
    amendment=tmp_path/'amendment.json';write(amendment,{'label':'ENGINEERING_ONLY','rows':[]})
    receipt=tmp_path/'receipt';receipt.write_text(digest_file(stage)+'\n'+digest_file(amendment))
    reference=tmp_path/'reference.json';write(reference,{'lower':0.1,'upper':0.5})
    values=tmp_path/'grids';values.write_text('synthetic')
    cfg={'dryrun':False,'registry':str(reg),'value_grids':str(values),'nodes':['digits_mlp'],'workers':20,
         'host':'TASL-7','W':2,'llm_call_cap':8,'audit_seeds':[9101,9102,9103,9104],
         'proposal_schema':'manager_proposal/v1','harness_commit':harness_sha,
         'anchor_duplicate_reference':{'source':str(reference),'sha256':digest_file(reference),'lower':0.1,'upper':0.5},
         'instance_seeds':[9001,9002], 'stage_a_table':str(stage),'stage_a_table_sha256':digest_file(stage),
         'stage_a_amendment_table':str(amendment),'stage_a_amendment_table_sha256':digest_file(amendment),
         'stage_a_amendment_acceptance':str(receipt),'stage_a_amendment_acceptance_sha256':digest_file(receipt)}
    batch=tmp_path/'batch';batch.mkdir();write(batch/'registry_snapshot.yaml',registry)
    binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(reg),'rule_sha256':rule_sha,
                                     'value_grids_sha256':digest_file(values)},sort_keys=True).encode()).hexdigest()
    state={'status':'COMPLETE','phase':'b1','execution_label':'EVIDENCE','binding':binding,'rule_sha256':rule_sha,
           'completed':{},'anchor_gate':{'fixture':True}}
    manifests=[]
    for order,spec in enumerate(specs):
        cid=spec['id'];grid=[('off','digits_mlp',seed) for seed in cfg['instance_seeds']]
        if (spec.get('thinking_policy') or {}).get('switchable'):grid += [('on','openml_credit_approval',seed) for seed in cfg['instance_seeds']]
        roots=[];paths=[]
        for mode,node,seed in grid:
            root=batch/cid/'b1'/mode/f'{node}__s{seed}';root.mkdir(parents=True)
            node_spec=load_registered_node(node,repo_root=harness)
            start={p:(harness/'nodes'/node/p).read_text() for p in node_spec.editable_paths}
            source_hashes={p:digest_file(harness/'nodes'/node/p) for p in node_spec.editable_paths}
            job=root/'job.json';write(job,{'authorization_checkout_head':head,'authority_config':cfg,'phase':'b1','node':node,
                'seed':seed,'mode':mode,'dryrun':False,'harness_commit':harness_sha,'node_source_sha256':source_hashes,
                'out':str(root),'binding':binding,'value_grids':str(values),'candidate':spec,
                **{key:cfg[key] for key in ('workers','host','W','llm_call_cap','audit_seeds','proposal_schema')}})
            trials=root/'root_trials.jsonl';trials.write_text(''.join(json.dumps({'node_id':node,'trial_id':f't{i}',
                    'budget_index':i,'decision':'kept','extra':{}})+'\n' for i in (1,2)))
            records=[json.loads(x) for x in trials.read_text().splitlines()]
            _,checks=replay_campaign(records,start,node,f'{node}__s{seed}','EXAM','append_only_summary',cfg['W'],1.)
            software=spec.get('kind') in ('random_valid','scripted')
            budget={'max_worker_runs':2,'max_llm_calls':8,'worker_runs':2,'llm_calls':0 if software else 1}
            event_rows=([{'event_type':'llm_call','payload':{'cache_prompt':False}}] if not software else [])
            event_rows.append({'event_type':'campaign_completed','payload':{'compute_budget':budget}})
            events=root/'root_events.jsonl';events.write_text(''.join(json.dumps(x)+'\n' for x in event_rows))
            configs=root/'audit_configs.json';configs.write_text('{}')
            cache=None if software else {'cache_prompt':False,'llm_call_events':1,'llm_call_failed_events':0,'trial_llm_call_records':0,'all_false':True}
            hashes={'root_trials.jsonl':digest_file(trials),'root_events.jsonl':digest_file(events),
                    'audit_cache.json':None,'audit_configs.json':digest_file(configs),'a4_observer_requests.jsonl':None}
            data={'status':'COMPLETE','label':'EXAM','execution_label':'EVIDENCE',
                'phase':'b1','candidate':cid,'mode':mode,'node':node,'instance_seed':seed,'job_binding':binding,
                'job_sha256':digest_file(job),'evidence_hashes':hashes,'audited_proposals':[],
                'd28':evaluate_ledger_paths([trials],generated_utc='synthetic',manager_kind='scripted' if software else 'langgraph',memory_mode='append_only_summary'),
                'cache_prompt':cache,'observer_evidence':None if software else {'calls':0,'sha256':None},
                'replay_checks':checks,'compute_budget':budget,'termination':'worker_cap',
                'diagnostics':{'trials':2,'evaluated':0,'invalid':0,'duplicates':0,'noops':0,'parse_failed':0,'forecast_queries':0,'forecast_query_failed':0}}
            path=root/'campaign_manifest.json';write(path,data)
            cert=root/'post_check.json';write(cert,{'binding':binding,'manifest_sha256':digest_file(path),'passed':True})
            state['completed'][f'{cid}/b1/{mode}/{node}__s{seed}']={'path':str(path),'sha256':digest_file(path),'post_check_sha256':digest_file(cert)}
            roots.append(data);paths.append(str(path))
        descriptive=[r for r in roots if r['mode']!='off']
        m={'label':'EXAM','phase':'b1','status':'COMPLETE','execution_label':'EVIDENCE','candidate':cid,
           'family':spec['family'],'role':spec['role'],'registry_order':order,'registry_path':str(batch/'registry_snapshot.yaml'),
           'registry_sha256':digest_file(reg),'rule_sha256':rule_sha,'primary_mode':'off','stage_a_pass':True,
           'stage_a_pass_source':'stage_a_table',
           'd28_pass':all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in roots if r['mode']=='off'),
           'thinking_on_d28':{'pass':all(all(n['pass'] for n in r['d28']['nodes'].values()) for r in descriptive),
               'roots':len(descriptive),'role':'descriptive_never_changes_eligibility'} if descriptive else None,
           'diagnostics':{k:sum(r['diagnostics'].get(k,0) for r in roots) for k in ('trials','evaluated','invalid','duplicates','noops','parse_failed','forecast_queries','forecast_query_failed')},
           'audited_proposals':[],'root_manifests':paths,'cache_prompt_by_root':[x['cache_prompt'] for x in roots],
           'authorization_checkout_head':head,'stage_a_table_sha256':cfg['stage_a_table_sha256'],
           'stage_a_amendment_table_sha256':cfg['stage_a_amendment_table_sha256'],
           'stage_a_amendment_acceptance_sha256':cfg['stage_a_amendment_acceptance_sha256']}
        write(batch/cid/'b1_manifest.json',m);manifests.append(m)
    write(batch/'batch_state.json',state);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':manifests})
    monkeypatch.setattr(runtime,'author_gate',lambda *a:head)
    monkeypatch.setattr(runtime,'read_registry',lambda p:registry)
    monkeypatch.setattr(exam_runner,'anchor_gate',lambda manifests,cfg:{'fixture':True})
    return batch,cfg,rule_sha,state,manifests


def test_full_authorized_synthetic_batch_passes(tmp_path,monkeypatch):
    batch,cfg,sha,_,_=fixture(tmp_path,monkeypatch)
    result=analyze.b1_summary_verified(batch,cfg,rule_path=analyze.RULE_V2,expected=sha)
    assert result['label']=='EXAM' and result['execution_label']=='EVIDENCE'
    assert result['batch_verification']['eligible_candidates']==['random_valid','scripted','qwen25_coder_7b','a','b']
    assert result['finalists']==[]


@pytest.mark.parametrize('tamper',['batch_status','missing_candidate','missing_anchor','missing_root','extra_root','wrong_head',
    'forged_audits','forged_root_audit','d28','receipt','cache_event','forged_registry','stage_pass','anchor_gate','budget','node_source','root_d28','diagnostics','root_diagnostics','on_d28'])
def test_partial_or_tampered_batch_stops(tmp_path,monkeypatch,tamper):
    batch,cfg,sha,state,ms=fixture(tmp_path,monkeypatch)
    selected=next(m for m in ms if m['candidate']=='a')
    def save_candidate():
        write(batch/'a/b1_manifest.json',selected);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    def rebind_root(path,root):
        write(path,root);cert=path.parent/'post_check.json'
        write(cert,{'binding':state['binding'],'manifest_sha256':digest_file(path),'passed':True})
        entry=state['completed']['a/b1/off/digits_mlp__s9001']
        entry.update(sha256=digest_file(path),post_check_sha256=digest_file(cert));write(batch/'batch_state.json',state)
    if tamper=='batch_status':state['status']='RUNNING';write(batch/'batch_state.json',state)
    elif tamper=='missing_candidate':write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms[:1]})
    elif tamper=='missing_anchor':write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms[1:]})
    elif tamper=='missing_root':state['completed'].pop(next(iter(state['completed'])));write(batch/'batch_state.json',state)
    elif tamper=='extra_root':state['completed']['extra']={};write(batch/'batch_state.json',state)
    elif tamper=='wrong_head':
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text());job=path.parent/'job.json';data=json.loads(job.read_text())
        data['authorization_checkout_head']='b'*40;write(job,data);root['job_sha256']=digest_file(job);rebind_root(path,root)
    elif tamper=='forged_audits':
        selected['audited_proposals']=[{'synthetic':'forged'}];write(batch/'a/b1_manifest.json',selected);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    elif tamper=='d28':
        selected['d28_pass']=not selected['d28_pass'];write(batch/'a/b1_manifest.json',selected);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    elif tamper=='receipt': Path(cfg['stage_a_amendment_acceptance']).write_text('changed')
    elif tamper=='stage_pass': selected['stage_a_pass']=False;save_candidate()
    elif tamper=='anchor_gate': state['anchor_gate']={'fixture':False};write(batch/'batch_state.json',state)
    elif tamper=='diagnostics': selected['diagnostics']['trials']=99;save_candidate()
    elif tamper=='root_diagnostics':
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text());root['diagnostics']['trials']=99
        selected['diagnostics']['trials']+=97;save_candidate();rebind_root(path,root)
    elif tamper=='forged_root_audit':
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text())
        root['audited_proposals']=[{'delta_audit':0.9,'candidate_metrics':[0.9]*4,'incumbent_metrics':[0.0]*4}]
        selected['audited_proposals']=root['audited_proposals'];save_candidate();rebind_root(path,root)
    elif tamper=='on_d28': selected['thinking_on_d28']['pass']=not selected['thinking_on_d28']['pass'];save_candidate()
    elif tamper in ('budget','node_source'):
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text());job=path.parent/'job.json';data=json.loads(job.read_text())
        if tamper=='budget': data['llm_call_cap']=999
        else: data['node_source_sha256']={'forged':'0'*64}
        write(job,data);root['job_sha256']=digest_file(job);rebind_root(path,root)
    elif tamper=='root_d28':
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text());verdict=root['d28']['nodes']['digits_mlp']
        verdict['pass']=not verdict['pass'];rebind_root(path,root)
    elif tamper=='forged_registry':
        fake=tmp_path/'forged_registry.yaml';write(fake,{'software_anchors':[],'candidates':[{'id':'a','role':'candidate','family':'wrong'}]})
        selected['registry_path']=str(fake);selected['registry_sha256']=digest_file(fake)
        write(batch/'a/b1_manifest.json',selected);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    elif tamper=='cache_event':
        path=Path(selected['root_manifests'][0]);root=json.loads(path.read_text());events=path.parent/'root_events.jsonl'
        event_rows=[json.loads(x) for x in events.read_text().splitlines()]
        event_rows[0]['payload']['cache_prompt']=True;events.write_text(''.join(json.dumps(x)+'\n' for x in event_rows))
        root['evidence_hashes']['root_events.jsonl']=digest_file(events);write(path,root)
        rebind_root(path,root)
    with pytest.raises((ValueError,RuntimeError,KeyError)):
        analyze.b1_summary_verified(batch,cfg,rule_path=analyze.RULE_V2,expected=sha)


@pytest.mark.parametrize('name',['batch_state.json','b1_manifests.json','job.json','post_check.json',
                                'root_events.jsonl','a4_observer_requests.jsonl'])
def test_batch_constituents_cannot_escape_via_symlink(tmp_path,monkeypatch,name):
    batch,cfg,sha,_,ms=fixture(tmp_path,monkeypatch)
    selected=next(m for m in ms if m['candidate']=='a')
    root=Path(selected['root_manifests'][0]).parent
    path=batch/name if name in ('batch_state.json','b1_manifests.json') else root/name
    outside=tmp_path/('outside_'+name);outside.write_text(path.read_text() if path.exists() else 'synthetic')
    if path.exists():
        saved=path.parent/'_to_delete';saved.mkdir(exist_ok=True);path.rename(saved/name)
    path.symlink_to(outside)
    with pytest.raises(ValueError,match='escapes'):
        analyze.b1_summary_verified(batch,cfg,rule_path=analyze.RULE_V2,expected=sha)
