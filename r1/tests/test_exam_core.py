"""Phase 1 exam guards, estimates and outcome-blind rule regressions. No inference."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
import yaml
from r1.exam.fit import estimate
from r1.exam.guards import (MIN_FREE_BYTES, licence_blockers, occupancy_blockers, paired_instance_bootstrap,
                            quantization_blockers, space_check, wilson_interval, frozen_digest)
from r1.exam.namespace import refuse_exam, check_exam_seeds
from r1.exam.analyze import choose_finalists, load_rule, b1_summary
from r1.exam.runtime import DEFAULT_CONFIG, load_config, read_registry, host_check


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
    assert sum(x['role']=='candidate' for x in r['candidates'])==21
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
    p.write_text('changed')
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
    with pytest.raises(ValueError,match='placeholders'): load_config(DEFAULT_CONFIG)
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
    assert result['rows'][0]['mu_hat']==pytest.approx(.01) and result['rows'][0]['b2_thinking_mode']=='on'
    with pytest.raises(ValueError,match='registry'): b1_summary([{**m,'family':'forged'}])
    with pytest.raises(ValueError,match='rule hash'): b1_summary([{**m,'rule_sha256':'0'*64}])
    s=stage_a_summary([{'candidate':'x','passed':True,'prompts':50,'free_parse_successes':40,'schema_parse_successes':49}])
    assert s['rows'][0]['free_parse']['point']==.8
    b=b2_summary([{'label':'EXAM','phase':'b2','status':'COMPLETE','candidate':'x','final_audits':[{'final_y':v,'metrics':[v]*10,'seeds':list(range(9201,9211))} for v in (.6,.8)],'gpu_hours':1,'mode':'on'}])
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
    ledger.write_text('changed')
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
