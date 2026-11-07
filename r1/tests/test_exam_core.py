"""Phase 1 exam guards, estimates and outcome-blind rule regressions. No inference."""
import copy
import hashlib
import json
import uuid
from pathlib import Path
import pytest
import yaml
from r1.exam.fit import estimate
from r1.exam.guards import (MIN_FREE_BYTES, licence_blockers, occupancy_blockers, paired_instance_bootstrap,
                            quantization_blockers, space_check, wilson_interval, frozen_digest)
from r1.exam.namespace import refuse_exam, check_exam_seeds
from r1.exam.analyze import choose_finalists, load_rule, b1_summary
from r1.exam.runtime import DEFAULT_CONFIG, load_config, read_registry, host_check


def _preserve_and_replace_fixture(path, content):
    """Retain a test fixture before its intentional same-path tampering.

    The caller must supply a private, stable test directory. Path.rename does
    not provide atomic no-replace semantics against an uncooperative writer.
    """
    retired_root=path.parent/'_to_delete'
    retired_root.mkdir(mode=0o700,exist_ok=True)
    retired=retired_root/uuid.uuid4().hex
    retired.mkdir(mode=0o700)
    path.rename(retired/path.name)
    with path.open('x',encoding='utf-8') as handle:
        handle.write(content)


def test_attention_fit_hand_calculation():
    r=estimate({'num_hidden_layers':2,'num_key_value_heads':4,'head_dim':64},10*2**30)
    assert r['kv_and_state_bytes']==2*2*4*64*32768==33554432
    assert r['total_bytes']==10*2**30+33554432+int(1.5*2**30)
    assert r['estimated_admissible'] and not r['measured_fit']
    assert r['config_fields']['num_key_value_heads']['field']=='num_key_value_heads'


def test_sliding_fit_hand_calculation():
    c={'num_hidden_layers':4,'num_key_value_heads':2,'head_dim':32,'sliding_window':4096,
       'layer_types':['full_attention','sliding_attention']*2}
    r=estimate(c,100)
    assert r['kv_and_state_bytes']==2*2*32*(2*32768+2*4096)==9437184
    assert r['config_fields']['sliding_window']['value']==4096


def test_hybrid_fit_hand_calculation():
    c={'text_config':{'num_hidden_layers':3,'num_key_value_heads':2,'head_dim':64,
       'layer_types':['full_attention','linear_attention','linear_attention'],
       'linear_num_key_heads':2,'linear_key_head_dim':16,'linear_num_value_heads':4,'linear_value_head_dim':32,'linear_conv_kernel_dim':3}}
    r=estimate(c,100)
    assert r['kv_and_state_bytes']==8388608+2*4*(4*16*32+2*(2*2*16+4*32))==8408064
    assert r['config_fields']['linear_key_head_dim']['field']=='text_config.linear_key_head_dim'
    assert r['layers'][1]['tokens'] is None
    with pytest.raises(ValueError): estimate({'model_type':'mamba','num_hidden_layers':3},100)
    with pytest.raises(ValueError): estimate({'num_hidden_layers':1,'layer_types':['unknown']},100)


def test_fit_boundary_and_fallback():
    c={'num_hidden_layers':1,'num_key_value_heads':8,'head_dim':128}
    kv=2*8*128*32768;buffers=int(1.5*2**30)
    size=int(23.5*2**30)-kv-buffers
    assert estimate(c,size)['estimated_admissible']
    assert not estimate(c,size+1)['estimated_admissible']
    assert estimate(c,size+1,16384)['estimated_admissible']


@pytest.mark.parametrize('payload',[{'label':'EXAM'},{'instance_seed':9001},{'audit_seeds':[9201,9202]}, {'campaign_id':'digits_mlp__s9011-trial-002'}])
def test_c3_namespace_refuses_even_unlabelled_seeds(payload):
    with pytest.raises(ValueError,match='EXAM|exam'): refuse_exam(payload)


def test_c3_build_and_sweep_admission_refuse_exam(tmp_path,monkeypatch):
    from r1.c3 import dataset
    from r1.scripts.c3_label_sweep import load_config as sweep_config
    d=tmp_path/'source';d.mkdir();(d/'manifest.json').write_text('{"label":"EXAM"}')
    monkeypatch.setattr(dataset,'SOURCES',{'exam':{'dir':str(d),'ledgers':'*','runs':20,'memory_mode':'append_only_summary'}})
    monkeypatch.setattr(dataset,'noise_table',lambda:{})
    with pytest.raises(ValueError,match='EXAM'): dataset.build(tmp_path/'table',sources=['exam'])
    with pytest.raises(ValueError,match='EXAM'): dataset.sweep_sources({'label':'EXAM'},tmp_path/'index',tmp_path)
    config=tmp_path/'config.json';config.write_text('{"label":"EXAM"}')
    with pytest.raises(ValueError,match='EXAM'): sweep_config(config)
    refuse_exam({'label':'ENGINEERING_ONLY','instance_seed':100,'audit_seeds':list(range(7001,7011))})


def test_disk_floor_exact_boundary(tmp_path):
    assert space_check(tmp_path,free_bytes=MIN_FREE_BYTES)['floor_bytes']==MIN_FREE_BYTES
    with pytest.raises(RuntimeError,match='100 GB'): space_check(tmp_path,free_bytes=MIN_FREE_BYTES-1)
    with pytest.raises(RuntimeError,match='does not exist'): space_check(tmp_path/'missing')


def test_registry_pool_exclusion_and_source_policy():
    r=read_registry(Path(__file__).parents[1]/'exam/registry.yaml')
    assert sum(x['role']=='candidate' for x in r['candidates'])==20
    assert len(r['software_anchors'])==2
    assert not any(x['id']=='ornith10_31b' for x in r['candidates'])
    assert r['phase2_vendor_first']['ornith10_35b']=='ornith-ai/Ornith-1.0-35B-GGUF'
    good={'id':'x','base_repo':'vendor/model','vendor_q4_available':True,'quant_source':{'kind':'vendor','repo':'vendor/model-GGUF','quantization':'Q4_K_M'}}
    assert not quantization_blockers(good)
    bad=copy.deepcopy(good);bad['quant_source']['quantization']='IQ3_XS';assert quantization_blockers(bad)
    bad=copy.deepcopy(good);bad['quant_source']['repo']='unsloth/model';assert quantization_blockers(bad)
    assert not quantization_blockers({'id':'gpt_oss_20b','quant_source':{'kind':'native_mxfp4','quantization':'MXFP4'}})


def test_ported_wilson_endpoints_and_paired_bootstrap():
    assert wilson_interval(0,30)['lower']==0
    assert wilson_interval(30,30)['upper']==pytest.approx(1)
    assert wilson_interval(15,30)['lower']==pytest.approx(.3315412564)
    a=[{'instance_id':str(i),'value':i+1} for i in range(4)]
    b=[{'instance_id':str(i),'value':i} for i in range(4)]
    r=paired_instance_bootstrap(a,b,resamples=100)
    assert r['difference_point']==r['difference_lower']==r['difference_upper']==1
    assert r['resampling_unit']=='instance_pair'
    with pytest.raises(ValueError): paired_instance_bootstrap(a,b[:-1])
    with pytest.raises(ValueError): paired_instance_bootstrap(a,b,resamples=10)


def test_ported_licence_occupancy_and_frozen_digest(tmp_path):
    assert licence_blockers('x',{})
    policy={'candidates':{'x':{'status':'author_approved_research_and_publication','licence':'MIT','approved_by':'Dowling Wong','approval_ref':'PLAN#R1-EXAM-LICENCES'}}}
    assert not licence_blockers('x',policy)
    sample={'device':0,'compute_pids':[],'memory_used_mib':20,'utilisation_percent':0}
    assert not occupancy_blockers([sample])
    assert occupancy_blockers([{**sample,'compute_pids':[123]}])
    assert not occupancy_blockers([{**sample,'compute_pids':[123],'memory_used_mib':2000}],owned_pids=[123])
    assert occupancy_blockers([])
    p=tmp_path/'rule';p.write_text('frozen');sha=hashlib.sha256(p.read_bytes()).hexdigest();assert frozen_digest(p,sha)==sha
    _preserve_and_replace_fixture(p,'changed')
    with pytest.raises(ValueError): frozen_digest(p,sha)


def test_frozen_finalists_absent_family_anchors_and_order():
    rule,_=load_rule()
    rows=[{'candidate':str(i),'role':'candidate','family':'a' if i<4 else 'b','stage_a_pass':True,'d28_pass':True,'mu_hat':1 if i<4 else .5,'registry_order':i} for i in range(7)]
    rows.append({'candidate':'anchor','role':'anchor','family':'z','stage_a_pass':True,'d28_pass':True,'mu_hat':100,'registry_order':8})
    assert choose_finalists(rows,rule)==['0','1','2','3','4']
    assert choose_finalists(list(reversed(rows)),rule)==['0','1','2','3','4']
    rows[1]['d28_pass']=False
    assert '1' not in choose_finalists(rows,rule)


def test_config_placeholder_check_and_no_mac_inference(tmp_path):
    cfg=load_config(DEFAULT_CONFIG,allow_placeholders=True)
    draft={**cfg,'host':'TODO_VERIFY_ON_HOST'}
    path=tmp_path/'unverified.json';path.write_text(json.dumps(draft))
    with pytest.raises(ValueError,match='placeholders'): load_config(path)
    with pytest.raises(RuntimeError,match='portal'): host_check({**cfg,'host':'wrong'},tmp_path)


def test_b1_recomputes_means_modes_and_refuses_forged_registry(tmp_path):
    from r1.exam.guards import digest_file
    from r1.exam.analyze import b2_summary, stage_a_summary
    rule,sha=load_rule()
    registry=tmp_path/'registry.yaml'
    registry.write_text(json.dumps({'software_anchors':[],'candidates':[{'id':'x','role':'candidate','family':'family'}]}))
    values=[{'instance_id':f'node{i}__s9001','node':'openml_credit_approval','mode':mode,'delta_audit':value,'candidate_metrics':[value]*4,'incumbent_metrics':[0]*4,'audit_seeds':list(range(9101,9105)),'p_delta_positive':.6}
            for i in range(4) for mode,value in [('off',.01),('on',.02)]]
    m={'label':'EXAM','phase':'b1','status':'COMPLETE','candidate':'x','family':'family','role':'candidate','registry_order':0,
       'rule_sha256':sha,'registry_path':str(registry),'registry_sha256':digest_file(registry),'primary_mode':'off',
       'stage_a_pass':True,'d28_pass':True,'audited_proposals':values}
    result=b1_summary([m]);assert result['finalists']==['x']
    forged=copy.deepcopy(m);forged['audited_proposals'][0]['delta_audit']=99
    with pytest.raises(ValueError,match='raw audits'): b1_summary([forged])
    a4=result['rows'][0]['a4_forecast_summary'];assert a4['primary_forecast_coverage']==1 and sum(b['count'] for b in a4['calibration']['bins'])==4
    assert 'pending_author' in a4['p_no_effect_evaluation']
    assert result['rows'][0]['mu_hat']==pytest.approx(.01) and result['rows'][0]['b2_thinking_mode']=='on'
    with pytest.raises(ValueError,match='registry'): b1_summary([{**m,'family':'forged'}])
    with pytest.raises(ValueError,match='rule hash'): b1_summary([{**m,'rule_sha256':'0'*64}])
    s=stage_a_summary([{'candidate':'x','passed':True,'prompts':50,'free_parse_successes':40,'schema_parse_successes':49}])
    assert s['rows'][0]['free_parse']['point']==.8
    b=b2_summary([{'label':'EXAM','phase':'b2','status':'COMPLETE','candidate':'x','source_label':'fixture','final_audits':[{'final_y':v,'metrics':[v]*10,'seeds':list(range(9201,9211))} for v in (.6,.8)],'gpu_hours':1,'mode':'on'}])
    assert b['rows'][0]['final_y']==pytest.approx(.7) and b['author_decision_pending']


def test_guarded_download_stops_mid_stream_and_preserves_partial(tmp_path):
    import io
    from r1.exam.guards import guarded_download
    payload=b'abcdefgh';calls=[]
    def space(path):
        calls.append(1)
        if len(calls)==3: raise RuntimeError('STOP: below 100 GB')
        return {'available_bytes':MIN_FREE_BYTES+100}
    target=tmp_path/'weights.gguf'
    with pytest.raises(RuntimeError,match='100 GB'):
        guarded_download('https://huggingface.co/fixture',target,sha256=hashlib.sha256(payload).hexdigest(),size_bytes=len(payload),
                         storage_root=tmp_path,opener=lambda *a,**k:io.BytesIO(payload),check_space=space,chunk_bytes=4)
    assert not target.exists() and (tmp_path/'weights.gguf.partial').read_bytes()==b'abcd'
    with pytest.raises(RuntimeError,match='preserve earlier'):
        guarded_download('https://huggingface.co/fixture',target,sha256=hashlib.sha256(payload).hexdigest(),size_bytes=len(payload),storage_root=tmp_path)


def test_prompt_freeze_checks_real_source_and_never_overwrites(tmp_path):
    from r1.exam.freeze_prompts import freeze
    from r1.exam.guards import digest_file
    ledger=tmp_path/'ledger'
    prompt='prior trial memory fixture'
    records=[{'trial_id':f'trial{i}','node_id':str(i%4),'memory_mode':'append_only_summary','extra':{'manager':{'context_sha256':hashlib.sha256(prompt.encode()).hexdigest()}}} for i in range(50)]
    ledger.write_text(''.join(json.dumps(r)+'\n' for r in records))
    rows=[{'id':i,'trial_id':f'trial{i}','node':str(i%4),'prompt':prompt,'active_keys':['C'],'seed':i,
           'ledger_path':str(ledger),'ledger_sha256':digest_file(ledger),'memory_mode':'append_only_summary'} for i in range(50)]
    source=tmp_path/'source.jsonl';source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    target=tmp_path/'frozen.jsonl';sha=freeze(source,target)
    assert digest_file(target)==sha
    with pytest.raises(ValueError,match='preserve'): freeze(source,target)
    _preserve_and_replace_fixture(ledger,'changed')
    with pytest.raises(ValueError,match='provenance'): freeze(source,tmp_path/'bad.jsonl')


def test_schema_option_reaches_collector_and_liveness_without_changing_defaults(tmp_path,monkeypatch):
    from r1.headroom.e1b_collect import make_manager
    from r1.scripts.c3_label_sweep import SweepRunner
    import r1.liveness.__main__ as live
    from types import SimpleNamespace
    cfg={'kind':'langgraph','model':'llamacpp/fixture','temperature':.2}
    assert make_manager('digits_mlp',9001,0,cfg).schema_version is None
    assert make_manager('digits_mlp',9001,0,{**cfg,'proposal_schema':'manager_proposal/v1'}).schema_version=='manager_proposal/v1'
    runner=SweepRunner.__new__(SweepRunner);runner.backend='llamacpp'
    runner.config={'llamacpp':{'model_alias':'fixture'},'proposal_schema':'manager_proposal/v1'}
    assert runner.manager_model_args()==['--manager-model','llamacpp/fixture','--proposal-schema','manager_proposal/v1']
    capture=[]
    def root(**kwargs): capture.append(kwargs['manager']);raise RuntimeError('fixture stop before any campaign')
    from r1.headroom import e1b_collect as collector
    monkeypatch.setattr(collector,'run_root',root)
    args=SimpleNamespace(manager='langgraph',manager_model='llamacpp/fixture',proposal_schema='manager_proposal/v1',
                         memory_mode='append_only_summary',transport_max_attempts=None,nodes=['digits_mlp'],instances=1,runs=10,
                         out=str(tmp_path/'out'),work=str(tmp_path/'work'))
    with pytest.raises(RuntimeError,match='fixture stop'): live.run_campaigns(args)
    assert capture[0]['proposal_schema']=='manager_proposal/v1'


def test_ported_numerics_match_archived_machinery_on_shared_inputs():
    import ast, math, random
    from typing import Any, Sequence, Mapping
    source=Path(__file__).parents[2]/'archive/old_b_2026-10-09/code/experiment_scaffold/src/causal_branch/round5_titan_exam.py'
    tree=ast.parse(source.read_text())
    selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('wilson_interval','paired_template_bootstrap')]
    ns={'math':math,'random':random,'Any':Any,'Sequence':Sequence,'Mapping':Mapping,'Round5GuardFailure':ValueError,'WILSON_Z_95':1.959963984540054}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),ns)
    for k,n in [(0,30),(12,30),(30,30)]: assert wilson_interval(k,n)==ns['wilson_interval'](k,n)
    a=[{'template_id':str(i),'success':bool(i%2)} for i in range(8)]
    b=[{'template_id':str(i),'success':bool(i%3)} for i in range(8)]
    archived=ns['paired_template_bootstrap'](a,b,resamples=200,seed=42)
    current=paired_instance_bootstrap([{'instance_id':r['template_id'],'value':float(r['success'])} for r in a],
                                      [{'instance_id':r['template_id'],'value':float(r['success'])} for r in b],resamples=200,seed=42)
    for key in ('difference_point','difference_lower','difference_upper','median'): assert current[key]==pytest.approx(archived[key])


def test_pool_cannot_replace_a_removed_model_while_preserving_count(tmp_path):
    registry=Path(__file__).parents[1]/'exam/registry.yaml';data=yaml.safe_load(registry.read_text())
    data['candidates'][0]['id']='unapproved_substitute'
    p=tmp_path/'registry.yaml';p.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='author pool'): read_registry(p)


def test_resume_certificate_and_evidence_tamper_refusal(tmp_path):
    from r1.exam.runtime import verify_campaign, PreparationStop
    from r1.exam.guards import digest_file
    from r1.exam.campaign import write_json
    write_json(tmp_path/'job.json',{'binding':'frozen'})
    (tmp_path/'ledger.jsonl').write_text('original')
    m={'status':'COMPLETE','label':'EXAM','job_binding':'frozen','job_sha256':digest_file(tmp_path/'job.json'),
       'evidence_hashes':{'ledger.jsonl':digest_file(tmp_path/'ledger.jsonl')}}
    manifest=tmp_path/'campaign_manifest.json';write_json(manifest,m)
    with pytest.raises(PreparationStop,match='receiving check'): verify_campaign(manifest,'frozen')
    write_json(tmp_path/'post_check.json',{'binding':'frozen','manifest_sha256':digest_file(manifest),'passed':True})
    assert verify_campaign(manifest,'frozen')==m
    _preserve_and_replace_fixture(tmp_path/'ledger.jsonl','changed')
    with pytest.raises(PreparationStop,match='evidence changed'): verify_campaign(manifest,'frozen')


def test_no_audited_increments_retains_candidate_diagnostics(tmp_path):
    from r1.exam.guards import digest_file
    registry=tmp_path/'registry.yaml'
    registry.write_text(json.dumps({'software_anchors':[],'candidates':[{'id':'x','role':'candidate','family':'family'}]}))
    _,sha=load_rule()
    m={'label':'EXAM','phase':'b1','status':'COMPLETE','candidate':'x','family':'family','role':'candidate','registry_order':0,
       'rule_sha256':sha,'registry_path':str(registry),'registry_sha256':digest_file(registry),'primary_mode':'off',
       'stage_a_pass':True,'d28_pass':True,'audited_proposals':[],'diagnostics':{'invalid':20}}
    r=b1_summary([m]);assert r['finalists']==[]
    assert r['rows'][0]['mu_hat'] is None and r['rows'][0]['diagnostics']['invalid']==20


def test_evidence_refuses_changed_stage_a_and_b1_inputs(tmp_path):
    from types import SimpleNamespace
    from r1.scripts.exam_runner import _evidence_unreviewed
    from r1.exam.runtime import PreparationStop
    from r1.exam.guards import digest_file
    source=tmp_path/'stage.json';source.write_text('{}')
    cfg={'stage_a_table':str(source),'stage_a_table_sha256':digest_file(source)}
    runner=SimpleNamespace(cfg=cfg)
    _preserve_and_replace_fixture(source,'{"changed": true}')
    with pytest.raises(PreparationStop,match='Stage A table digest'): _evidence_unreviewed(runner,'b1',None,False)
    cfg['stage_a_table_sha256']=digest_file(source)
    cfg.update(b1_analysis=str(source),b1_analysis_sha256='0'*64)
    with pytest.raises(PreparationStop,match='B1 analysis digest'): _evidence_unreviewed(runner,'b2',None,False)


def test_b2_respects_stage_a_thinking_disable(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    from r1.exam.guards import digest_file
    from r1.exam.campaign import write_json
    from r1.exam.runtime import PreparationStop
    _,sha=load_rule();stages=tmp_path/'stage.json';screen=tmp_path/'b1.json';registry=tmp_path/'registry.json'
    registry.write_text('{}')
    write_json(stages,{'rows':[{'candidate':'x','passed':True,'thinking_disabled_due_grammar':True}]})
    write_json(screen,{'rule_sha256':sha,'finalists':['x'],'rows':[{'candidate':'x','b2_thinking_mode':'off'}]})
    spec={'id':'x','role':'candidate','family':'f','thinking_policy':{'mode':'off','switchable':True}}
    class Fake:
        def __init__(self):
            self.cfg={'stage_a_table':str(stages),'stage_a_table_sha256':digest_file(stages),'b1_analysis':str(screen),
                      'b1_analysis_sha256':digest_file(screen),'nodes':['digits_mlp'],'b2_instances_per_node':1,'instance_seeds':[9001],
                      'server':{'build':'fake'},'dryrun':True}
            self.state={'completed':{}};self.rule_sha=sha;self.calls=[];self.service=None;self.out=tmp_path;self.registry_path=registry
        def spec_order(self,*args): return [copy.deepcopy(spec)]
        def server(self,spec,mode,ctx): self.calls.append(mode)
        def root(self,spec,phase,node,seed,mode,**kwargs):
            return {'mode':mode,'node':node,'instance_seed':seed,'audited_proposals':[],
                    'diagnostics':dict.fromkeys(('trials','evaluated','invalid','duplicates','noops','parse_failed'),0),
                    'd28':{'nodes':{'digits_mlp':{'pass':True}}},'final_audits':[]}
    runner=Fake();_evidence_unreviewed(runner,'b2',None,False)
    assert runner.calls==['off']
    data=json.loads(screen.read_text());data['rows'][0]['b2_thinking_mode']='on';_preserve_and_replace_fixture(screen,json.dumps(data,indent=2,allow_nan=False)+'\n')
    runner=Fake()
    with pytest.raises(PreparationStop,match='disabled by Stage A'): _evidence_unreviewed(runner,'b2',None,False)
    assert runner.calls==[]


def test_phase2_real_architecture_cache_shapes():
    root=Path(__file__).parents[2]/'docs/r1/reports/exam_phase2_20261026'
    c=json.loads((root/'nemotron35_30b_a3b_config.json').read_text())
    result=estimate(c,100)
    mamba=4*(64*64*128+3*(64*64+2*8*128))
    assert result['kv_and_state_bytes']==c['layers_block_type'].count('mamba')*mamba+c['layers_block_type'].count('attention')*2*2*128*32768
    assert all(r['bytes']==0 for r in result['layers'] if r['kind']=='moe')
    c=json.loads((root/'lfm25_24b_a2b_config.json').read_text());result=estimate(c,100)
    assert result['kv_and_state_bytes']==c['layer_types'].count('conv')*4*2048*2+c['layer_types'].count('full_attention')*2*8*64*32768
    c=json.loads((root/'glm47_flash_config.json').read_text());result=estimate(c,100)
    assert result['kv_and_state_bytes']==47*(512+64)*32768
    assert all(r['kind']=='compressed_mla' for r in result['layers'])


def test_gemma_global_and_local_cache_dimensions():
    root=Path(__file__).parents[2]/'docs/r1/reports/exam_phase2_20261026'
    expected={'gemma4_31b':50*2*16*256*1024+10*2*4*512*32768,
              'gemma4_26b_a4b':25*2*8*256*1024+5*2*2*512*32768,
              'gemma4_12b':40*2*8*256*1024+8*2*1*512*32768}
    for name,value in expected.items():
        c=json.loads((root/(name+'_config.json')).read_text());r=estimate(c,100)
        assert r['kv_and_state_bytes']==value
        assert r['config_fields']['global_head_dim']['value']==512
        assert 'num_global_key_value_heads' in r['config_fields']
    # Equal K/V projection weights do not eliminate the two runtime caches.
    assert expected['gemma4_31b']==1761607680


def test_author_unsloth_exception_is_exact_and_labelled():
    r=read_registry(Path(__file__).parents[1]/'exam/registry.yaml')
    s=next(s for s in r['candidates'] if s['id']=='qwen3_coder_30b_a3b')
    assert not quantization_blockers(s)
    assert s['source_label']=='source exception (unsloth)'
    for change in ({'id':'another_candidate'}, {'source_label':'ordinary quant'}):
        bad=copy.deepcopy(s);bad.update(change);assert quantization_blockers(bad)
    for name in ('UD-Q4_K_M.gguf','Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_M.gguf'):
        bad=copy.deepcopy(s);bad['quant_source']['file']=name;assert quantization_blockers(bad)
    assert any(x['id']=='qwopus36_27b_v4' for x in r['excluded'])


def test_fake_matches_pinned_reasoning_budget_request_fields(monkeypatch):
    from r1.scripts import c3_fake_llama_server as fake
    monkeypatch.setattr(fake,'ARGS',{'-ngl':'999','--reasoning-budget':'0','--chat-template-kwargs':'{"enable_thinking":false}'})
    request={'chat_template_kwargs':{'enable_thinking':True},'reasoning_budget':2048}
    assert 'reasoning_content' not in fake.Handler.completion(None,request,'{}')['choices'][0]['message']
    request.pop('reasoning_budget');request['reasoning_budget_tokens']=2048
    reply=fake.Handler.completion(None,request,'{}')
    assert reply['usage']['completion_tokens_details']['reasoning_tokens']==1
    request['chat_template_kwargs']['enable_thinking']=False
    assert 'reasoning_content' not in fake.Handler.completion(None,request,'{}')['choices'][0]['message']


def test_rico_uses_standalone_vendor_template_and_native_thinking_policy():
    r=read_registry(Path(__file__).parents[1]/'exam/registry.yaml')
    s=next(s for s in r['candidates'] if s['id']=='rico03_qwen36_27b')
    template=(Path(__file__).parents[2]/'docs/r1/reports/exam_phase2_20261026/rico_vendor_chat_template.jinja').read_bytes()
    assert hashlib.sha256(template).hexdigest()==s['chat_template_source']['template_sha256']
    assert s['chat_template_source']['file']=='chat_template.jinja'
    assert b'enable_thinking' not in template and b'<think>' in template
    assert s['thinking_policy']['mode']=='always_on' and s['thinking_policy']['budget']==2048
    assert not s['thinking_policy']['switchable'] and not s['thinking_policy']['off_switch']


def test_evidence_entry_refuses_b2_and_unreviewed_b1_rule():
    from types import SimpleNamespace
    from r1.scripts.exam_runner import evidence
    from r1.exam.runtime import PreparationStop
    for phase in ('b1','b2'):
        with pytest.raises(PreparationStop,match='only x5_rule/v2 B1 evidence'):
            evidence(SimpleNamespace(cfg={}),phase,None,False)


def test_host_check_allows_the_two_approved_portals_and_pins_config_host(tmp_path,monkeypatch):
    from r1.exam import runtime
    (tmp_path/'models').mkdir();(tmp_path/'work').mkdir()
    monkeypatch.setattr(runtime,'EXAM_X_ROOT',tmp_path)
    cfg={'host':'TASL-7','models_dir':str(tmp_path/'models'),
         'work_dir':str(tmp_path/'work')}
    monkeypatch.setattr(runtime.platform,'node',lambda:'TASL-7')
    monkeypatch.setattr(runtime,'space_check',lambda path:None)
    out=tmp_path/'work'/'out'
    runtime.host_check(cfg,out)  # accepted on the approved host with matching cfg.host
    with pytest.raises(RuntimeError,match='approved portal host'):
        runtime.host_check({**cfg,'host':'TASL-2'},out)
    monkeypatch.setattr(runtime.platform,'node',lambda:'Dowlings-MacBook-Pro-2')
    with pytest.raises(RuntimeError,match='approved portal host'):
        runtime.host_check({**cfg},out)
