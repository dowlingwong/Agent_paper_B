"""B1 observer guard and journal checks on synthetic data only."""
import base64
import hashlib
import json
from pathlib import Path
import pytest
from r1.exam import observer
from r1.exam.b1_observer_journal import validate_observer_journal


def test_unmarked_dryrun_context_is_refused(tmp_path):
    job={'phase':'b1','dryrun':True,'out':str(tmp_path/'root'),
         'authority_config':{'dryrun':True,'dryrun_root':str(tmp_path),'rule_sha256':'fixture'}}
    with pytest.raises(RuntimeError,match='marked temporary root'):
        with observer.authorized_b1_observer(job): pass


def test_production_host_must_match_authorized_host(monkeypatch):
    monkeypatch.setattr('r1.exam.campaign.require_worker_host',lambda job:None)
    job={'phase':'b1','dryrun':False,'host':'TASL-2','node':'digits_mlp',
         'authority_config':{'host':'TASL-7','nodes':['digits_mlp'],'cache_prompt':False}}
    with pytest.raises(observer.D3EvidenceStop,match='host/node'):
        with observer.authorized_b1_observer(job): pass


@pytest.mark.parametrize('hostname',['TASL-7.example','tasl-7.example','TASL-2','tasl-2.example'])
def test_marked_dryrun_is_refused_on_exam_hosts(tmp_path,monkeypatch,hostname):
    (tmp_path/'.dryrun').write_text('synthetic')
    monkeypatch.setattr('platform.node',lambda:hostname)
    job={'phase':'b1','dryrun':True,'out':str(tmp_path/'root'),
         'authority_config':{'dryrun':True,'dryrun_root':str(tmp_path),'rule_sha256':'fixture'}}
    with pytest.raises(observer.D3EvidenceStop,match='forbidden on exam hosts'):
        with observer.authorized_b1_observer(job): pass


@pytest.mark.parametrize('hostname',['TASL-7.example','tasl-7.example','TASL-2','tasl-2.example','ucrtasl.example'])
def test_dryrun_parent_refuses_exam_hosts_before_output(tmp_path,monkeypatch,hostname):
    from r1.exam.runtime import host_check
    from r1.scripts import exam_dryrun
    (tmp_path/'.dryrun').write_text('fixture')
    monkeypatch.setattr('platform.node',lambda:hostname)
    monkeypatch.setattr(exam_dryrun,'prepare',lambda *a:pytest.fail('must refuse before preparing'))
    with pytest.raises(RuntimeError,match='development host'): host_check({'dryrun':True,'dryrun_root':str(tmp_path)},tmp_path/'out')
    with pytest.raises(RuntimeError,match='development host'): exam_dryrun.run(tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_reordered_journal_is_refused(tmp_path):
    body=json.dumps({'cache_prompt':False}); raw=b'{"answer":"fixture"}'
    digest=hashlib.sha256(raw).hexdigest(); request_sha=hashlib.sha256(body.encode()).hexdigest()
    events=[{'event_type':'llm_call','payload':{'purpose':'self_forecast','cache_prompt':False,
             'request_evidence':{'request_body':body,'request_body_sha256':request_sha,'response_body_sha256':digest}}}]
    entries=[{'event':'request_attempt','sequence':1,'request_body':body,'request_body_sha256':request_sha},
             {'event':'response_headers','sequence':1,'http_status':200},
             {'event':'response_chunk','sequence':1,'chunk_index':1,'chunk_bytes':len(raw),'chunk_sha256':digest,'chunk_b64':base64.b64encode(raw).decode()},
             {'event':'response_complete','sequence':1,'response_body_sha256':digest}]
    path=tmp_path/'journal.jsonl'
    path.write_text(''.join(json.dumps(x)+'\n' for x in entries))
    assert validate_observer_journal(path,events)['calls']==1
    path.write_text(''.join(json.dumps(x)+'\n' for x in [entries[3],*entries[:3]]))
    with pytest.raises(RuntimeError,match='order'):
        validate_observer_journal(path,events)


def test_interleaved_journal_sequences_are_refused(tmp_path):
    path=tmp_path/'journal.jsonl'
    path.write_text(''.join(json.dumps({'event':'request_attempt','sequence':x})+'\n' for x in [1,2,1]))
    events=[{'event_type':'llm_call','payload':{'purpose':'self_forecast'}}]*2
    with pytest.raises(RuntimeError,match='not serial'):
        validate_observer_journal(path,events)


@pytest.mark.parametrize('key,bad',[('workers',99),('W',999),('llm_call_cap',1000),('audit_seeds',[1]),('proposal_schema','free')])
def test_child_cannot_change_authorized_b1_settings(monkeypatch,key,bad):
    monkeypatch.setattr('r1.exam.campaign.require_worker_host',lambda job:None)
    cfg={'dryrun':False,'host':'TASL-7','nodes':['digits_mlp'],'instance_seeds':[9001],
         'workers':20,'W':20,'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
         'proposal_schema':'manager_proposal/v1','cache_prompt':False}
    job={'phase':'b1','dryrun':False,'host':'TASL-7','node':'digits_mlp','seed':9001,'mode':'off',
         'workers':20,'W':20,'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
         'proposal_schema':'manager_proposal/v1','authority_config':cfg}
    job[key]=bad
    with pytest.raises(observer.D3EvidenceStop,match='differs|mismatch'):
        with observer.authorized_b1_observer(job): pass


def test_child_rejects_nonfalse_cache_setting(monkeypatch):
    monkeypatch.setattr('r1.exam.campaign.require_worker_host',lambda job:None)
    cfg={'dryrun':False,'host':'TASL-7','nodes':['digits_mlp'],'instance_seeds':[9001],
         'workers':20,'W':20,'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
         'proposal_schema':'manager_proposal/v1','cache_prompt':True}
    job={'phase':'b1','dryrun':False,'host':'TASL-7','node':'digits_mlp','seed':9001,'mode':'off',
         'workers':20,'W':20,'llm_call_cap':80,'audit_seeds':[9101,9102,9103,9104],
         'proposal_schema':'manager_proposal/v1','authority_config':cfg}
    with pytest.raises(observer.D3EvidenceStop,match='schema/cache'):
        with observer.authorized_b1_observer(job): pass


def test_child_accepts_only_stage_a_bound_footprint(monkeypatch):
    import copy
    from r1.scripts import exam_runner
    row={'id':'model','role':'candidate','runtime':{'footprint_mib':'TODO_VERIFY_ON_HOST'},
         'quant_source':{'sha256':'modelsha'},'thinking_policy':{'mode':'off'}}
    registry={'candidates':[row],'software_anchors':[]}
    cfg={'server':{'build':'build'}}
    accepted={'candidate':'model','model_sha256':'modelsha','build':'build',
              'qualification':{'footprint_mib':1234}}
    monkeypatch.setattr(exam_runner,'stage_a_pass_set',lambda *a,**k:{'model':accepted})
    candidate=copy.deepcopy(row);candidate['runtime']['footprint_mib']=1234
    assert observer._authorized_candidate({'candidate':candidate},cfg,registry)
    for edit in ({'runtime':{'footprint_mib':1235}},{'quant_source':{'sha256':'other'}}):
        assert not observer._authorized_candidate({'candidate':{**candidate,**edit}},cfg,registry)
    accepted['model_sha256']='other'
    assert not observer._authorized_candidate({'candidate':candidate},cfg,registry)
