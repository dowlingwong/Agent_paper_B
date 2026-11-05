"""B1 complete-batch verifier, synthetic files only, no training or server."""
import hashlib
import json
from pathlib import Path
import pytest
from r1.exam import analyze, runtime
from r1.exam.guards import digest_file


def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,sort_keys=True))


def fixture(tmp_path,monkeypatch):
    head='a'*40;rule_sha=digest_file(analyze.RULE_V2)
    specs=[{'id':'a','role':'candidate','family':'fa','thinking_policy':{'mode':'off','switchable':True,'off_switch':True}},
           {'id':'b','role':'candidate','family':'fb','thinking_policy':{'mode':'off','switchable':False}}]
    registry={'candidates':specs,'software_anchors':[]};reg=tmp_path/'registry.yaml';write(reg,registry)
    stage=tmp_path/'stage.json';write(stage,{'rows':[{'candidate':s['id'],'passed':True} for s in specs]})
    amendment=tmp_path/'amendment.json';write(amendment,{'label':'ENGINEERING_ONLY','rows':[]})
    receipt=tmp_path/'receipt';receipt.write_text(digest_file(stage)+'\n'+digest_file(amendment))
    values=tmp_path/'grids';values.write_text('synthetic')
    cfg={'dryrun':False,'registry':str(reg),'value_grids':str(values),'nodes':['digits_mlp'],
         'instance_seeds':[9001,9002], 'stage_a_table':str(stage),'stage_a_table_sha256':digest_file(stage),
         'stage_a_amendment_table':str(amendment),'stage_a_amendment_table_sha256':digest_file(amendment),
         'stage_a_amendment_acceptance':str(receipt),'stage_a_amendment_acceptance_sha256':digest_file(receipt)}
    batch=tmp_path/'batch';batch.mkdir();write(batch/'registry_snapshot.yaml',registry)
    binding=hashlib.sha256(json.dumps({'config':cfg,'registry_sha256':digest_file(reg),'rule_sha256':rule_sha,
                                     'value_grids_sha256':digest_file(values)},sort_keys=True).encode()).hexdigest()
    state={'status':'COMPLETE','phase':'b1','execution_label':'EVIDENCE','binding':binding,'rule_sha256':rule_sha,'completed':{}}
    manifests=[]
    for order,spec in enumerate(specs):
        cid=spec['id'];grid=[('off','digits_mlp',seed) for seed in cfg['instance_seeds']]
        if spec['thinking_policy']['switchable']:grid += [('on','openml_credit_approval',seed) for seed in cfg['instance_seeds']]
        roots=[];paths=[]
        for mode,node,seed in grid:
            root=batch/cid/'b1'/mode/f'{node}__s{seed}';root.mkdir(parents=True)
            job=root/'job.json';write(job,{'authorization_checkout_head':head})
            trials=root/'root_trials.jsonl';trials.write_text('')
            events=root/'root_events.jsonl';events.write_text(json.dumps({'event_type':'llm_call','payload':{'cache_prompt':False}})+'\n')
            configs=root/'audit_configs.json';configs.write_text('{}')
            cache={'cache_prompt':False,'llm_call_events':1,'llm_call_failed_events':0,'trial_llm_call_records':0,'all_false':True}
            hashes={'root_trials.jsonl':digest_file(trials),'root_events.jsonl':digest_file(events),
                    'audit_cache.json':None,'audit_configs.json':digest_file(configs),'a4_observer_requests.jsonl':None}
            data={'status':'COMPLETE','label':'EXAM','execution_label':'EVIDENCE',
                'phase':'b1','candidate':cid,'mode':mode,'node':node,'instance_seed':seed,'job_binding':binding,
                'job_sha256':digest_file(job),'evidence_hashes':hashes,'audited_proposals':[],
                'd28':{'nodes':{node:{'pass':True}}},'cache_prompt':cache,'observer_evidence':{'calls':0,'sha256':None}}
            path=root/'campaign_manifest.json';write(path,data)
            cert=root/'post_check.json';write(cert,{'binding':binding,'manifest_sha256':digest_file(path),'passed':True})
            state['completed'][f'{cid}/b1/{mode}/{node}__s{seed}']={'path':str(path),'sha256':digest_file(path),'post_check_sha256':digest_file(cert)}
            roots.append(data);paths.append(str(path))
        m={'label':'EXAM','phase':'b1','status':'COMPLETE','execution_label':'EVIDENCE','candidate':cid,
           'family':spec['family'],'role':'candidate','registry_order':order,'registry_path':str(batch/'registry_snapshot.yaml'),
           'registry_sha256':digest_file(reg),'rule_sha256':rule_sha,'primary_mode':'off','stage_a_pass':True,
           'd28_pass':True,'audited_proposals':[],'root_manifests':paths,'cache_prompt_by_root':[x['cache_prompt'] for x in roots],
           'authorization_checkout_head':head,'stage_a_table_sha256':cfg['stage_a_table_sha256'],
           'stage_a_amendment_table_sha256':cfg['stage_a_amendment_table_sha256'],
           'stage_a_amendment_acceptance_sha256':cfg['stage_a_amendment_acceptance_sha256']}
        write(batch/cid/'b1_manifest.json',m);manifests.append(m)
    write(batch/'batch_state.json',state);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':manifests})
    monkeypatch.setattr(runtime,'author_gate',lambda *a:head)
    monkeypatch.setattr(runtime,'read_registry',lambda p:registry)
    return batch,cfg,rule_sha,state,manifests


def test_full_authorized_synthetic_batch_passes(tmp_path,monkeypatch):
    batch,cfg,sha,_,_=fixture(tmp_path,monkeypatch)
    result=analyze.b1_summary_verified(batch,cfg,rule_path=analyze.RULE_V2,expected=sha)
    assert result['label']=='EVIDENCE' and result['batch_verification']['eligible_candidates']==['a','b']
    assert result['finalists']==[]


@pytest.mark.parametrize('tamper',['batch_status','missing_candidate','missing_root','extra_root','wrong_head','forged_audits','d28','receipt','cache_event'])
def test_partial_or_tampered_batch_stops(tmp_path,monkeypatch,tamper):
    batch,cfg,sha,state,ms=fixture(tmp_path,monkeypatch)
    if tamper=='batch_status':state['status']='RUNNING';write(batch/'batch_state.json',state)
    elif tamper=='missing_candidate':write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms[:1]})
    elif tamper=='missing_root':state['completed'].pop(next(iter(state['completed'])));write(batch/'batch_state.json',state)
    elif tamper=='extra_root':state['completed']['extra']={};write(batch/'batch_state.json',state)
    elif tamper=='wrong_head':
        path=Path(ms[0]['root_manifests'][0]);job=path.parent/'job.json';write(job,{'authorization_checkout_head':'b'*40})
    elif tamper=='forged_audits':
        ms[0]['audited_proposals']=[{'synthetic':'forged'}];write(batch/'a/b1_manifest.json',ms[0]);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    elif tamper=='d28':
        ms[0]['d28_pass']=False;write(batch/'a/b1_manifest.json',ms[0]);write(batch/'b1_manifests.json',{'label':'EXAM','manifests':ms})
    elif tamper=='receipt': Path(cfg['stage_a_amendment_acceptance']).write_text('changed')
    elif tamper=='cache_event':
        path=Path(ms[0]['root_manifests'][0]);root=json.loads(path.read_text());events=path.parent/'root_events.jsonl'
        events.write_text(json.dumps({'event_type':'llm_call','payload':{'cache_prompt':True}})+'\n')
        root['evidence_hashes']['root_events.jsonl']=digest_file(events);write(path,root)
        cert=path.parent/'post_check.json';write(cert,{'binding':state['binding'],'manifest_sha256':digest_file(path),'passed':True})
        entry=state['completed']['a/b1/off/digits_mlp__s9001'];entry.update(sha256=digest_file(path),post_check_sha256=digest_file(cert))
        write(batch/'batch_state.json',state)
    with pytest.raises((ValueError,RuntimeError,KeyError)):
        analyze.b1_summary_verified(batch,cfg,rule_path=analyze.RULE_V2,expected=sha)
