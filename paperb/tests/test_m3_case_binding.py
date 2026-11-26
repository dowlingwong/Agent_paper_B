"""Static synthetic case-binding checks; no replay or model execution."""
import copy
import hashlib
import pytest
from r1.c3.offline_cases import bind_cases,CaseStop


def fixtures():
    cases=[];snaps={}
    for n in range(8):
        node=f'openml_{n}' if n<6 else f'other_{n}'
        if n<6:snaps[node]={'node':node,'offline_executability':'NOT_ESTABLISHED','cache':{'sha256':str(n)*64}}
        for budget in (1,2):
            contents=f'case {n} {budget}\n'
            cases.append({'case_id':f'{node}:t{budget:03}','node':node,'budget_index':budget,
                          'instance_seed':100+n,'train_seed':100+n,'split_seed':100+n,
                          'worker_command':'python3 train.py --config config.yaml',
                          'files':{'config.yaml':contents},
                          'configuration_file_sha256':{'config.yaml':hashlib.sha256(contents.encode()).hexdigest()}})
    return cases,snaps


def test_binding_all_cases_is_deterministic_and_never_claims_offline():
    cases,snaps=fixtures();one=bind_cases(cases,snaps);two=bind_cases(list(reversed(cases)),snaps)
    assert one==two and len(one['cases'])==16 and one['offline_executability']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('change,reason',[
    ('missing','16 cases'),('duplicate','duplicate or invalid'),('wrong_budget','duplicate node budget'),
    ('seed','seeds'),('command','worker command'),('hash','digest mismatch'),('path','configuration path'),
    ('cache','cache identity'),('extra_cache','cache map')])
def test_binding_refuses_bad_identity(change,reason):
    cases,snaps=fixtures();cases=copy.deepcopy(cases);snaps=copy.deepcopy(snaps)
    if change=='missing':cases.pop()
    elif change=='duplicate':cases[1]['case_id']=cases[0]['case_id']
    elif change=='wrong_budget':cases[1]['budget_index']=1
    elif change=='seed':cases[0]['split_seed']=1
    elif change=='command':cases[0]['worker_command']='NOT CHECKED (no harness)'
    elif change=='hash':cases[0]['files']['config.yaml']='tampered'
    elif change=='path':
        content=cases[0]['files'].pop('config.yaml');digest=cases[0]['configuration_file_sha256'].pop('config.yaml')
        cases[0]['files']['../config.yaml']=content;cases[0]['configuration_file_sha256']['../config.yaml']=digest
    elif change=='cache':snaps.pop('openml_0')
    else:snaps['openml_unselected']={}
    with pytest.raises(CaseStop,match=reason):bind_cases(cases,snaps)
