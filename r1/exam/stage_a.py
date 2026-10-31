"""Stage A mechanical probes on a dedicated server. Caller owns host/pin/space gates."""
from __future__ import annotations
import json
import hashlib
import re
import math
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
from r1.exam.guards import digest_file


def post(instance, route, payload, timeout=300):
    require_d3_evidence()
    with urlopen(Request(instance.url+route,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=timeout) as r:
        return json.load(r)


def load_prompts(path, expected, *, dryrun=False, historical_seeds=False):
    # Use the same bytes for digest checking and parsing; never edit the source.
    prompt_path=Path(path).resolve(strict=True)
    bundle_root=prompt_path.parent
    data=prompt_path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected: raise ValueError('frozen prompt-set digest mismatch')
    rows=[json.loads(s) for s in data.decode('utf-8').splitlines() if s.strip()]
    if len(rows)!=50 or len({r['node'] for r in rows})<4: raise ValueError('50 prompts across >=4 nodes required')
    sources={};seen=set()
    for row in rows:
        if not row.get('prompt') or not row.get('active_keys'): raise ValueError('prompt and active keys required')
        if not dryrun:
            ledger_path=Path(row['ledger_path'])
            if '..' in ledger_path.parts:
                raise ValueError('source ledger path traversal forbidden')
            source=(ledger_path if ledger_path.is_absolute() else bundle_root/ledger_path).resolve(strict=True)
            try:
                source.relative_to(bundle_root)
            except ValueError:
                raise ValueError('source ledger outside prompt bundle') from None
            if source not in sources:
                raw=source.read_bytes()
                sha=hashlib.sha256(raw).hexdigest()
                if row.get('memory_mode')!='append_only_summary' or sha!=row['ledger_sha256']:
                    raise ValueError('prompt-set source ledger/memory provenance mismatch')
                sources[source]=(sha,[json.loads(s) for s in raw.decode('utf-8').splitlines() if s.strip()])
            sha, records=sources[source]
            if row.get('memory_mode')!='append_only_summary' or sha!=row['ledger_sha256']:
                raise ValueError('prompt-set source ledger/memory provenance mismatch')
            key=(str(source.resolve()),row['trial_id'])
            if key in seen: raise ValueError('duplicate frozen ledger/trial prompt')
            seen.add(key)
            matches=[r for r in records if r.get('trial_id')==row['trial_id']]
            if len(matches)!=1: raise ValueError('source ledger trial must be unique')
            record=matches[0]
            if (record is None or record.get('memory_mode')!='append_only_summary' or record.get('node_id')!=row['node'] or
                ((record.get('extra') or {}).get('manager') or (record.get('extra') or {})).get('context_sha256')!=hashlib.sha256(row['prompt'].encode()).hexdigest()):
                raise ValueError('frozen prompt does not match its recorded memory-on manager context')
            if historical_seeds:
                # D26: SHA-256(campaign|budget|0|0), first four bytes big-endian.
                # Source records were produced with harness 411c6054; the
                # separately pinned Stage A harness is 897d83c8. Both record
                # the same manager_seed formula; neither pin is replaced here.
                # Require the historical llm_call to agree with the formula.
                campaign=record.get('campaign_id'); budget=record.get('budget_index')
                manager=(record.get('extra') or {}).get('manager') or {}
                call=manager.get('llm_call') or {}
                recorded=call.get('seed')
                if not isinstance(campaign,str) or not campaign or type(budget) is not int or budget<0 or type(recorded) is not int:
                    raise ValueError('missing historical D26 seed inputs')
                payload=f'{campaign}|{budget}|0|0'.encode('utf-8')
                derived=int.from_bytes(hashlib.sha256(payload).digest()[:4],'big')
                if recorded!=derived or ('seed' in row and (type(row['seed']) is not int or row['seed']!=derived)):
                    raise ValueError('historical D26 seed mismatch')
                row['seed']=derived
        elif historical_seeds:
            raise ValueError('historical D26 seeds require verified source ledgers')
    return rows


def hf_render(spec, messages):
    from transformers import AutoTokenizer  # optional host dependency; no model is loaded
    source=spec['chat_template_source']
    tokenizer=AutoTokenizer.from_pretrained(source['repo'],revision=source['revision'],trust_remote_code=False,token=False)
    template=tokenizer.get_chat_template()
    if hashlib.sha256(template.encode()).hexdigest()!=source['template_sha256']: raise ValueError('HF template differs from pinned template bytes')
    return tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,
                                        enable_thinking=spec['thinking_policy']['mode']!='off')


def parse_proposal(content, row, structured):
    """Use the actual harness parser; free-generation heuristics remain descriptive."""
    from r1.harness import import_harness
    harness=import_harness()
    from autoresearch.manager.base import ManagerStatus
    from autoresearch.manager.langgraph_manager import _validate_proposal
    from autoresearch.nodes.registry import load_registered_node
    spec=load_registered_node(row['node'],repo_root=harness)
    constants=dict(re.findall(r'^  ([A-Za-z_][A-Za-z0-9_]*) = (.+)$',row['prompt'],re.M))
    status=ManagerStatus('exam_replay',1,None,spec.metric_name,spec.metric_direction,constants)
    result=_validate_proposal({'raw_proposal':content,'status':status,'node_spec':spec,
                              'context_text':row['prompt'],'proposal_schema':'manager_proposal/v1' if structured else None})['proposal']
    key=(result.extra.get('structured_edit') or {}).get('symbol') or result.extra.get('named_param')
    valid_key=key is not None and key.lower() in {str(k).lower() for k in row['active_keys']}
    return result.extra['llm_call']['parse_ok'],valid_key


def require_d3_evidence():
    from r1.exam.cache_runtime import require_authorized_stagea
    require_authorized_stagea()


def prefill_metadata(context):
    return {'declared_context_tokens':context,'prefill_requested_tokens':context-1,
            'prefill_tokens':None,'prefill_requested_generated_tokens':1,'prefill_generated_tokens':None,
            'native_api_reserve_tokens':1,'prefill_author_ref':'R1-EXAM-PREFILL-RESERVE'}


def thinking_grammar_probe(recorder, row, schema_format):
    """Use the same false wire recorder as primary calls; preserve evidence STOPs."""
    from r1.exam.cache_false import D3EvidenceStop
    controls={'temperature':.2,'cache_prompt':False,'response_format':schema_format,
              'chat_template_kwargs':{'enable_thinking':True},'reasoning_budget_tokens':2048}
    try:
        reply=recorder.chat(row['prompt'],max_tokens=4096,seed=row['seed'],extra=controls)
        message=reply['choices'][0]['message']
        final=re.sub(r'<think>.*?</think>\s*','',message['content'],flags=re.S)
        parsed=json.loads(final)
        reasoning=(reply.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens')
        grammar=bool(reasoning or message.get('reasoning_content')) and isinstance(parsed,dict) and set(parsed)==set(schema_format['json_schema']['schema']['required'])
        return {'passed':grammar,'seed':row['seed'],'message':message,'usage':reply.get('usage'),'request_controls':controls}
    except D3EvidenceStop:
        raise
    except Exception as exc:
        return {'passed':False,'seed':row['seed'],'error':repr(exc),'request_controls':controls}


def fit_prefill(instance, recorder=None, non_generation=None):
    """Author-approved native API reserve; cache allocation remains the declared ctx."""
    require_d3_evidence()
    if recorder is None: raise RuntimeError('STOP: D3 false-call recorder required')
    if non_generation is None: raise RuntimeError('STOP: D3 non-generation recorder required')
    context=instance.ctx_size
    target=context-1
    tokenized=non_generation.post('/tokenize',{'content':'a ','add_special':True})['tokens']
    if not tokenized: raise ValueError('empty tokenisation result')
    tokens=(tokenized*((target+len(tokenized)-1)//len(tokenized)))[:target]
    reply=recorder.completion({'prompt':tokens,'n_predict':1,'seed':0,'temperature':0.2,'cache_prompt':False})
    evidence={'declared_context_tokens':context,'prefill_requested_tokens':target,
              'prefill_tokens':reply.get('tokens_evaluated'),'prefill_requested_generated_tokens':1,
              'prefill_generated_tokens':reply.get('tokens_predicted'),'native_api_reserve_tokens':1,
              'prefill_author_ref':'R1-EXAM-PREFILL-RESERVE'}
    return evidence


def run_stage_a(instance, spec, prompts, *, gpu_sample, schema_format, dryrun=False, template_renderer=None, cache_context=None):
    require_d3_evidence()
    if not isinstance(cache_context,dict):
        raise RuntimeError('STOP: descriptive cache context is absent')
    from r1.exam.cache_descriptive import true_replay
    from r1.exam.cache_false import D3EvidenceStop
    recorder=cache_context.get('false_recorder')
    non_generation=cache_context.get('non_generation_recorder')
    if recorder is None:
        raise RuntimeError('STOP: D3 false-call recorder required')
    if non_generation is None:
        raise RuntimeError('STOP: D3 non-generation recorder required')
    true_context={k:v for k,v in cache_context.items() if k not in ('false_recorder','non_generation_recorder')}
    descriptive=true_replay(instance,prompts,schema_format,**true_context)
    result={'candidate':spec['id'],'label':'EXAM','execution_label':'DRYRUN' if dryrun else 'ENGINEERING_ONLY',
            'phase':'stage-a','cache_prompt_planned':False,'descriptive_cache_true':descriptive,'prompts':len(prompts),'failure_classes':[], 'cpu_pool_only':instance.ctx_size==16384,
            'free_parse_successes':0,'schema_parse_successes':0,'active_key_successes':0,'free_active_key_successes':0,'free_seed_reproducible':True,
            'seed_reproducible':True,'template_checks':[],'grammar_after_thinking':None,
            **prefill_metadata(instance.ctx_size)}
    telemetry=[];stop=threading.Event()
    def sample():
        while not stop.is_set():
            try: telemetry.append(gpu_sample())
            except Exception as exc: telemetry.append({'error':repr(exc)})
            stop.wait(.2)
    thread=threading.Thread(target=sample,daemon=True);thread.start()
    component='offload'
    try:
        result.update(fit_prefill(instance,recorder,non_generation))
        if result['prefill_tokens']!=instance.ctx_size-1:
            raise ValueError('prefill count does not equal approved context minus one')
        if result['prefill_generated_tokens']!=1:
            raise ValueError('native probe did not report exactly one generated token')
        if any(not isinstance(s,dict) or 'error' in s for s in telemetry):
            raise D3EvidenceStop('STOP: VRAM monitoring unavailable or malformed')
        samples=list(telemetry)
        if not samples: raise D3EvidenceStop('STOP: no VRAM telemetry')
        for sample in samples:
            for key in ('free_mib','used_mib'):
                value=sample.get(key)
                if type(value) not in (int,float) or not math.isfinite(value) or value<0:
                    raise D3EvidenceStop(f'STOP: VRAM telemetry {key} missing or invalid')
        result['min_free_mib']=min(s['free_mib'] for s in samples)
        result['peak_used_mib']=max(s['used_mib'] for s in samples)
        if result['min_free_mib']<1024:
            raise D3EvidenceStop('STOP: VRAM monitoring unavailable or <1 GiB free during prefill')
        component='template'
        render=template_renderer or (lambda messages:hf_render(spec,messages))
        for i in range(5):
            messages=[{'role':'user','content':f'Fixed template check {i}: JSON, whitespace, Unicode α, newline\nend.'}]
            actual=non_generation.post('/apply-template',{'messages':messages,'add_generation_prompt':True,
                        'chat_template_kwargs':{'enable_thinking':spec['thinking_policy']['mode']!='off'}})['prompt']
            expected=render(messages)
            result['template_checks'].append(actual==expected)
        if not all(result['template_checks']): result['failure_classes'].append('template')
    except D3EvidenceStop:
        raise
    except Exception as exc:
        result['probe_error']=f'{type(exc).__name__}: {exc}'
        result['failure_classes'].append(component)
    finally:
        stop.set();thread.join(timeout=2)
    if 'offload' in result['failure_classes']:
        result.update(requested_prompts=len(prompts),prompts=0,passed=False,gpu_samples=telemetry)
        return result
    timings=[];token_rows=[];responses=[]
    for row in prompts:
        pair=[]
        for structured in (False,True):
            repeated_message=None
            kwargs={'response_format':schema_format} if structured else {}
            try:
                t=time.monotonic()
                reply=recorder.chat(row['prompt'],max_tokens=4096,seed=row['seed'],extra={'temperature':.2,'cache_prompt':False,**kwargs})
                timings.append(time.monotonic()-t)
                message=reply['choices'][0]['message'];content=message.get('content') or ''
                final=re.sub(r'<think>.*?</think>\s*','',content,flags=re.S).strip()
                ok,key_valid=parse_proposal(final,row,structured)
                if structured: result['schema_parse_successes']+=ok
                else: result['free_parse_successes']+=ok
                if structured and ok: result['active_key_successes']+=key_valid
                if not structured and ok: result['free_active_key_successes']+=key_valid
                repeated=recorder.chat(row['prompt'],max_tokens=4096,seed=row['seed'],extra={'temperature':.2,'cache_prompt':False,**kwargs})
                repeated_message=repeated['choices'][0]['message']
                if structured: result['seed_reproducible'] &= repeated_message==message
                else: result['free_seed_reproducible'] &= repeated_message==message
                reasoning=(reply.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens')
                token_rows.append({**reply.get('usage',{}),'reasoning_tokens':reasoning})
                pair.append({'structured':structured,'seed':row['seed'],'raw_content':content,'reasoning_content':message.get('reasoning_content'),
                             'parse_ok':ok,'repeat_message':repeated_message,'usage':reply.get('usage',{})})
            except D3EvidenceStop:
                raise
            except Exception as exc:
                failure='timeout' if 'timeout' in str(exc).lower() or 'timed out' in str(exc).lower() else 'parse'

                if structured: result['failure_classes'].append(failure)
                pair.append({'structured':structured,'seed':row['seed'],'error':repr(exc)})
        responses.append({'prompt_id':row.get('trial_id'),'responses':pair})
    result.update(responses=responses,token_counts=token_rows,
                  latency_p50=float(np.quantile(timings,.5)) if timings else None,
                  latency_p95=float(np.quantile(timings,.95)) if timings else None,
                  gpu_samples=telemetry)
    # Thinking/grammar evidence is required before a thinking-on row can qualify.
    if spec['thinking_policy']['mode']!='off':
        result['grammar_after_thinking']=any((r.get('reasoning_tokens') or 0)>0 for r in token_rows) and result['schema_parse_successes']==len(prompts)
        if not result['grammar_after_thinking']: result['failure_classes'].append('grammar')
    if result['schema_parse_successes']/len(prompts)<.95: result['failure_classes'].append('parse')
    if not result['seed_reproducible']: result['failure_classes'].append('seed_reproducibility')
    if spec['thinking_policy'].get('switchable') is True or spec['thinking_policy']['mode']=='always_on':
        grammar=thinking_grammar_probe(recorder,prompts[0],schema_format)
        result['thinking_grammar_probe']=grammar
        result['thinking_disabled_due_grammar']=not grammar['passed'] and spec['thinking_policy']['mode']!='always_on'
        if not grammar['passed'] and spec['thinking_policy']['mode']=='always_on':
            result['failure_classes'].append('grammar')
    result['failure_classes']=sorted(set(result['failure_classes']))
    result['passed']=not result['failure_classes']
    return result


def main(argv=None):
    import os
    if not os.environ.get('TRACKX_GPU_LEASE_FD'):
        require_d3_evidence()
    import argparse
    from r1.harness import import_harness
    import_harness()
    from autoresearch.llm.providers import manager_response_format
    from r1.exam.runtime import gpu_sample
    from r1.exam.campaign import write_json
    from r1.scripts.llama_server_instance import LlamaServerInstance
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
    job=json.loads(Path(a.job).read_text());cfg=job['config'];spec=job['candidate']
    from r1.exam.cache_runtime import authorize_cooperative_stagea
    authorize_cooperative_stagea(cfg)
    from r1.exam.cache_runtime import reject_unverified_cold, validate_worker_binding
    # Do not construct any request recorder or contact the service until a
    # reviewed cold identity proof exists. The current checker always STOPs.
    reject_unverified_cold(job.get('cache_identity'))
    identity=job['cache_identity']
    validate_worker_binding(identity,job)
    inst=LlamaServerInstance(job['out'],cfg['server']['binary'],model_path=spec['runtime']['model_path'],alias=spec['id'],
                             ctx_size=job['ctx'],port=job['port'])
    prompts=load_prompts(cfg['prompts'],cfg['prompts_sha256'],dryrun=bool(cfg.get('dryrun')),
                         historical_seeds=not bool(cfg.get('dryrun')))
    render=(lambda ms: ''.join(f"{m['role']}: {m['content']}\n" for m in ms)+'assistant: ') if cfg.get('dryrun') else None
    from contextlib import ExitStack
    from r1.exam.cache_proc import sample_llama_server_processes
    from r1.exam.cache_false import FalseCallRecorder
    from r1.exam.cache_nongen import NonGenerationRecorder
    output=Path(job['out'])
    census=lambda:sample_llama_server_processes(identity)
    with ExitStack() as stack:
        false= FalseCallRecorder(inst.url,inst.alias,census=census,identity=identity,
                                 journal_path=output/'d3_false_calls.jsonl')
        stack.callback(false.close)
        nongen=NonGenerationRecorder(inst.url,census=census,identity=identity,
                                     journal_path=output/'d3_non_generation_calls.jsonl')
        stack.callback(nongen.close)
        context={'census':census,'identity':identity,'journal_path':output/'d3_true_calls.jsonl',
                 'frozen_binding':{'path':cfg['prompts'],'sha256':cfg['prompts_sha256']},
                 'false_recorder':false,'non_generation_recorder':nongen}
        schema_format=manager_response_format()
        result=run_stage_a(inst,spec,prompts,gpu_sample=lambda:gpu_sample(cfg),schema_format=schema_format,
                           dryrun=bool(cfg.get('dryrun')),template_renderer=render,cache_context=context)
    result['d3_observation_scope']={
        'policy':'author_same_uid_cooperative_20261031',
        'same_uid_external_noninterference':'assumed by author, not independently measured',
        'host_global_single_server':'NOT_CHECKABLE',
        'census':'visible /proc snapshots only; inaccessible processes and between-sample gaps unobserved',
        'coldness':'new owned server; first true response cache counts must indicate zero cached tokens',
    }
    from r1.exam.cache_order import validate_local_order
    def journal_rows(path):
        return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    result['d3_local_journal_order']=validate_local_order(
        journal_rows(output/'d3_true_calls.jsonl'),journal_rows(output/'d3_false_calls.jsonl'),
        journal_rows(output/'d3_non_generation_calls.jsonl'),prompts,alias=spec['id'],ctx_size=job['ctx'],
        schema_format=schema_format,expect_grammar=bool(spec['thinking_policy'].get('switchable') is True or spec['thinking_policy']['mode']=='always_on'),
        thinking_enabled=spec['thinking_policy']['mode']!='off',identity=identity)
    if not cfg.get('dryrun'):
        from r1.exam.fit import estimate
        source=Path(spec['runtime']['model_config_path'])
        if digest_file(source)!=spec['runtime']['model_config_sha256']: raise ValueError('source config pin mismatch')
        result['fit_estimate']=estimate(json.loads(source.read_text()),spec['quant_source']['size_bytes'],job['ctx'])
        if not result['fit_estimate']['estimated_admissible']:
            result['failure_classes']=sorted(set(result['failure_classes']+['fit_estimate']));result['passed']=False
    write_json(Path(job['out'])/'stage_a.json',result)

if __name__=='__main__': main()
