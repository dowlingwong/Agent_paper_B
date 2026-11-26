"""16 pinned-harness config checks, no model or numerical replay."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import pytest
from r1.c3.offline_config_checks import check_cases,ConfigStop
from r1.c3.offline_preflight import HARNESS_COMMIT


def fixtures():
    path=os.environ.get('AR_M3_PINNED_HARNESS')
    if not path:
        if os.environ.get('R1_REQUIRE_M3_HARNESS')=='1':pytest.fail('AR_M3_PINNED_HARNESS required')
        pytest.skip('set AR_M3_PINNED_HARNESS')
    harness=Path(path)
    assert subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip()==HARNESS_COMMIT
    index=json.loads((Path(__file__).resolve().parents[2]/'results/r1/pilot/C3_sweep_index_20261028T033315Z.json').read_text())
    cases=[];snapshots={}
    for index,node in enumerate(index['nodes']):
        schema=json.loads((harness/f'configs/nodes/{node}.yaml').read_text())
        if node.startswith('openml_'):
            snapshots[node]={'node':node,'offline_executability':'NOT_ESTABLISHED','cache':{'sha256':str(index)*64}}
        for budget in (1,2):
            files={p:(harness/f'nodes/{node}'/p).read_text() for p in schema['editable_paths']}
            campaign=f'{node}__s{100+index}'
            cases.append({'case_id':f'{campaign}:t{budget:03}','campaign_id':campaign,'node':node,'budget_index':budget,
                          'instance_seed':100+index,'train_seed':100+index,'split_seed':100+index,
                          'worker_command':schema['run_command'],'files':files,
                          'configuration_file_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}})
    return cases,snapshots,harness


def rehash(case):
    case['configuration_file_sha256']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in case['files'].items()}


def test_checks_all_16_pinned_node_configs_without_running_models():
    cases,snaps,harness=fixtures();result=check_cases(cases,snaps,harness)
    assert len(result['checks'])==16 and result['offline_executability']=='NOT_ESTABLISHED'
    assert all(c['configuration_shape']=='PASS' for c in result['checks'])


@pytest.mark.parametrize('change,reason',[('range','out-of-range'),('value','invalid configuration value'),
                                          ('source','non-editable MLP code changed'),('command','worker command mismatch')])
def test_one_invalid_case_stops_entire_preflight(change,reason):
    cases,snaps,harness=fixtures();cases=copy.deepcopy(cases)
    if change=='range':
        case=next(c for c in cases if c['node'].startswith('openml_'))
        case['files']['config.yaml']=re.sub(r'^max_iter:.*$', 'max_iter: 999999',case['files']['config.yaml'],flags=re.M)
    elif change=='value':
        case=next(c for c in cases if c['node'].startswith('openml_'))
        case['files']['config.yaml']=case['files']['config.yaml'].replace('model_type: logistic_regression','model_type: unsafe')
    elif change=='source':
        case=next(c for c in cases if c['node']=='digits_mlp')
        case['files']['train.py']+='\nprint("unexpected")\n'
    else:
        case=cases[0];case['worker_command']='python3 different.py'
    rehash(case)
    with pytest.raises(ConfigStop,match=reason):check_cases(cases,snaps,harness)
