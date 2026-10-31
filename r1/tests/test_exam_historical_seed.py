import hashlib
import json
from types import SimpleNamespace

import pytest

from r1.exam.stage_a import load_prompts, run_stage_a


def seed(campaign, budget):
    return int.from_bytes(hashlib.sha256(f'{campaign}|{budget}|0|0'.encode()).digest()[:4], 'big')


def test_pinned_harness_known_seed_vector():
    # From the retained 411c harness function and its historical llm_call.
    assert seed('digits_mlp__s104',2)==1023010193


def fixture(tmp_path, mutate=None):
    source=tmp_path/'source.jsonl'
    ledger=tmp_path/'ledger.jsonl'
    text='Synthetic context with no historical outcomes'
    records=[]
    rows=[]
    for i in range(50):
        record={'trial_id':f't{i}', 'node_id':f'n{i%4}', 'campaign_id':f'c{i%4}',
                'budget_index':i, 'memory_mode':'append_only_summary',
                'extra':{'manager':{'context_sha256':hashlib.sha256(text.encode()).hexdigest(),
                                    'llm_call':{'seed':seed(f'c{i%4}',i)}}}}
        records.append(record)
    if mutate: mutate(records)
    ledger.write_text(''.join(json.dumps(record)+'\n' for record in records))
    digest=hashlib.sha256(ledger.read_bytes()).hexdigest()
    for i in range(50):
        rows.append({'trial_id':f't{i}', 'node':f'n{i%4}', 'prompt':text,
                     'active_keys':['X'], 'ledger_path':str(ledger),
                     'ledger_sha256':digest,'memory_mode':'append_only_summary'})
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    return source,hashlib.sha256(source.read_bytes()).hexdigest()


def test_seed_derived_from_pinned_ledger_without_rewriting_candidate(tmp_path):
    source,digest=fixture(tmp_path)
    original=source.read_bytes()
    rows=load_prompts(source,digest,historical_seeds=True)
    assert [row['seed'] for row in rows]==[seed(f'c{i%4}',i) for i in range(50)]
    assert source.read_bytes()==original
    assert all('seed' not in json.loads(line) for line in original.splitlines())


@pytest.mark.parametrize('mutate',[
    lambda records: records[0]['extra']['manager']['llm_call'].pop('seed'),
    lambda records: records[0]['extra']['manager']['llm_call'].__setitem__('seed',1),
    lambda records: records[0].pop('campaign_id'),
    lambda records: records[0].__setitem__('budget_index',True),
    lambda records: records.append(records[0]),
])
def test_missing_invalid_or_ambiguous_historical_seed_stops(tmp_path,mutate):
    source,digest=fixture(tmp_path,mutate)
    with pytest.raises(ValueError):
        load_prompts(source,digest,historical_seeds=True)


def test_source_ledger_change_stops(tmp_path):
    source,digest=fixture(tmp_path)
    row=json.loads(source.read_text().splitlines()[0])
    with open(row['ledger_path'],'w') as out: out.write('changed')
    with pytest.raises(ValueError, match='provenance'):
        load_prompts(source,digest,historical_seeds=True)


def test_relative_ledger_resolves_from_bundle_not_runner_cwd(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle'
    bundle.mkdir()
    source,_=fixture(bundle)
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    for row in rows: row['ledger_path']='ledger.jsonl'
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    runner=tmp_path/'runner'
    runner.mkdir()
    monkeypatch.chdir(runner)
    resolved=load_prompts(source,digest,historical_seeds=True)
    assert len(resolved)==50 and all(type(row['seed']) is int for row in resolved)


@pytest.mark.parametrize('mode',['traversal','outside_absolute','symlink_escape'])
def test_ledger_cannot_escape_prompt_bundle(tmp_path,mode):
    bundle=tmp_path/'bundle'
    bundle.mkdir()
    source,_=fixture(bundle)
    outside=tmp_path/'outside.jsonl'
    outside.write_bytes((bundle/'ledger.jsonl').read_bytes())
    if mode=='traversal': path='../outside.jsonl'
    elif mode=='outside_absolute': path=str(outside)
    else:
        (bundle/'link.jsonl').symlink_to(outside)
        path='link.jsonl'
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    rows[0]['ledger_path']=path
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='traversal|outside'):
        load_prompts(source,digest,historical_seeds=True)


def test_candidate_cannot_override_historical_seed(tmp_path):
    source,_=fixture(tmp_path)
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    rows[0]['seed']=1
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='seed mismatch'):
        load_prompts(source,digest,historical_seeds=True)


def test_history_cannot_be_resolved_in_dryrun_mode(tmp_path):
    source,digest=fixture(tmp_path)
    with pytest.raises(ValueError, match='verified source'):
        load_prompts(source,digest,dryrun=True,historical_seeds=True)


def test_replay_calls_and_records_same_seed(tmp_path,monkeypatch):
    source,digest=fixture(tmp_path)
    rows=load_prompts(source,digest,historical_seeds=True)
    calls=[]
    class Instance:
        ctx_size=4
        def chat(self, prompt, *, seed, **kwargs):
            calls.append((seed, kwargs['extra']['cache_prompt']))
            return {'choices':[{'message':{'content':'{}'}}], 'usage':{}}
        def completion(self, payload):
            return {'tokens_evaluated':3,'tokens_predicted':1}
    def post(instance, route, payload):
        if route=='/tokenize': return {'tokens':[1]}
        if route=='/completion': return {'tokens_evaluated':3,'tokens_predicted':1}
        return {'prompt':'rendered'}
    monkeypatch.setattr('r1.exam.stage_a.require_d3_evidence',lambda:None)
    monkeypatch.setattr('r1.exam.cache_descriptive.true_replay',lambda *args,**kwargs:{'synthetic':True})
    monkeypatch.setattr('r1.exam.stage_a.post',post)
    monkeypatch.setattr('r1.exam.stage_a.parse_proposal',lambda *args:(True,True))
    instance=Instance()
    nongen=SimpleNamespace(post=lambda route,payload:post(instance,route,payload))
    out=run_stage_a(instance,{'id':'fixture','thinking_policy':{'mode':'off'}},rows[:1],
                    gpu_sample=lambda:{'free_mib':2048,'used_mib':128},schema_format={},
                    template_renderer=lambda messages:'rendered',cache_context={'false_recorder':instance,'non_generation_recorder':nongen})
    assert calls==[(rows[0]['seed'],False)]*4
    assert out['cache_prompt_planned'] is False
    assert [item['seed'] for item in out['responses'][0]['responses']]==[rows[0]['seed']]*2
