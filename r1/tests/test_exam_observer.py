"""The A4 exam observer must not feed decisions, memory or immutable trial records."""
import copy
from unittest.mock import patch
from r1.tests.c3_campaign_fixtures import SequenceBackend, run_campaign
from r1.exam.observer import SelfForecastObserver
from r1.scripts.llama_server_instance import LlamaServerInstance, thinking_args
from autoresearch.control_plane.budget import ComputeBudget
from autoresearch.manager.base import ManagerProposal

class DynamicBackend:
    deterministic=True
    mode='fixture'
    def propose_next_trial(self,status,memory_context,node_spec):
        old=status.current_constants['MAX_ITER'];new=str(int(old)+status.budget_index+1)
        return ManagerProposal(self.mode,'edit','fixture',node_spec.editable_paths,'change MAX_ITER',
            {'structured_edit':{'type':'python_constant','path':'train.py','symbol':'MAX_ITER','old':old,'new':new}})


def test_observer_changes_only_answers_and_llm_accounting(tmp_path):
    def backend(): return DynamicBackend()
    queries=[]
    observer=SelfForecastObserver(llm=lambda p:queries.append(p) or '{"p_no_effect":0.2,"p_positive":0.75,"size":"small"}')
    with patch('autoresearch.control_plane.campaign._iso_now',return_value='2026-10-26T00:00:00Z'):
        _,ev_a,a,_=run_campaign(tmp_path/'a',backend(),budget=3,compute_budget=ComputeBudget(max_llm_calls=10))
        _,ev_b,b,_=run_campaign(tmp_path/'b',backend(),budget=3,compute_budget=ComputeBudget(max_llm_calls=10),proposal_observer=observer)
    assert a==b
    answers=[e['payload'] for e in ev_b if e['event_type']=='exam_self_forecast']
    calls=[e for e in ev_b if e['event_type']=='llm_call']
    assert len(queries)==len(answers)==len(calls)==3
    assert all(abs(r['p_delta_positive']-.6)<1e-12 for r in answers)
    assert not any(e['event_type']=='exam_self_forecast' for e in ev_a)
    assert all('No metric outcome is supplied' in p for p in queries)


def test_observer_cap_and_failed_query_are_recorded_without_decision_input(tmp_path):
    observer=SelfForecastObserver(llm=lambda p:(_ for _ in ()).throw(ValueError('bad fixture answer')))
    _,events,rows,_=run_campaign(tmp_path,DynamicBackend(),budget=2,
                                compute_budget=ComputeBudget(max_llm_calls=1),proposal_observer=observer)
    calls=[e for e in events if e['event_type']=='llm_call']
    assert len(calls)==1 and calls[0]['payload']['status']=='query_failed'
    assert len(rows)==1  # observer call exhausts the declared cap; it never exceeds it


def test_thinking_policy_is_opt_in_and_budgeted(tmp_path):
    kwargs={'batch_dir':tmp_path,'binary':'/fixture/server','model_path':'/fixture/model','alias':'fixture','port':12345}
    old=LlamaServerInstance(**kwargs)
    off=LlamaServerInstance(**kwargs,thinking_policy={'mode':'off','budget':0,'off_switch':True})
    on=LlamaServerInstance(**kwargs,thinking_policy={'mode':'on','budget':2048,'off_switch':True})
    always=LlamaServerInstance(**kwargs,thinking_policy={'mode':'always_on','budget':2048,'off_switch':False})
    assert old.argv==['/fixture/server','-m','/fixture/model','--host','127.0.0.1','--port','12345','-ngl','999','-c','8192','--alias','fixture','-np','1']
    assert off.argv[-2:]==['--chat-template-kwargs','{"enable_thinking":false}']
    assert on.argv[-2:]==['--reasoning-budget','2048']
    assert '--chat-template-kwargs' not in always.argv
    import pytest
    with pytest.raises(ValueError): thinking_args({'mode':'on','budget':0})


def test_observer_reserves_call_before_non_deterministic_proposal(tmp_path):
    class CalledManager(DynamicBackend): deterministic=False
    observer=SelfForecastObserver(llm=lambda p:'{"p_no_effect":0.1,"p_positive":0.5,"size":"small"}')
    _,events,rows,_=run_campaign(tmp_path,CalledManager(),budget=4,compute_budget=ComputeBudget(max_llm_calls=3),proposal_observer=observer)
    assert len(rows)==1
    assert any(e['event_type']=='exam_observer_call_pair_unavailable' for e in events)
    completed=next(e for e in events if e['event_type']=='campaign_completed')
    assert completed['payload']['compute_budget']['llm_calls']==2


def test_schema_parse_failure_is_counted_without_worker_or_fallback(tmp_path):
    class ParseFailed:
        mode='schema_fixture';deterministic=False;schema_version='manager_proposal/v1'
        def propose_next_trial(self,status,memory_context,node_spec):
            return ManagerProposal(self.mode,'parse_failed','failure',node_spec.editable_paths,'',
                                   {'parse_failed':True,'schema_version':self.schema_version,
                                    'llm_call':{'schema_version':self.schema_version,'parse_failed':True,'parse_ok':False}})
    _,events,rows,worker=run_campaign(tmp_path,ParseFailed(),budget=3,compute_budget=ComputeBudget(max_llm_calls=3))
    assert len(rows)==3 and worker.runs==0
    assert all(r['decision']=='failed_invalid' and r['extra']['manager']['parse_failed'] for r in rows)
    assert len([e for e in events if e['event_type']=='llm_call'])==3
