"""Stage A mechanical probes on a dedicated server. Caller owns host/pin/space gates."""
from __future__ import annotations
import json
import hashlib
import re
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
from r1.exam.guards import digest_file


def post(instance, route, payload, timeout=300):
    with urlopen(Request(instance.url+route,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=timeout) as r:
        return json.load(r)


def load_prompts(path, expected, *, dryrun=False):
    if digest_file(path)!=expected: raise ValueError('frozen prompt-set digest mismatch')
    rows=[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    if len(rows)!=50 or len({r['node'] for r in rows})<4: raise ValueError('50 prompts across >=4 nodes required')
    sources={};seen=set()
    for row in rows:
        if not row.get('prompt') or not row.get('active_keys'): raise ValueError('prompt and active keys required')
        if not dryrun:
            source=Path(row['ledger_path'])
            if row.get('memory_mode')!='append_only_summary' or digest_file(source)!=row['ledger_sha256']:
                raise ValueError('prompt-set source ledger/memory provenance mismatch')
            key=(str(source.resolve()),row['trial_id'])
            if key in seen: raise ValueError('duplicate frozen ledger/trial prompt')
            seen.add(key)
            if source not in sources: sources[source]=[json.loads(s) for s in source.read_text().splitlines() if s.strip()]
            record=next((r for r in sources[source] if r.get('trial_id')==row['trial_id']),None)
            if (record is None or record.get('memory_mode')!='append_only_summary' or record.get('node_id')!=row['node'] or
                ((record.get('extra') or {}).get('manager') or (record.get('extra') or {})).get('context_sha256')!=hashlib.sha256(row['prompt'].encode()).hexdigest()):
                raise ValueError('frozen prompt does not match its recorded memory-on manager context')
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


def run_stage_a(instance, spec, prompts, *, gpu_sample, schema_format, dryrun=False, template_renderer=None):
    result={'candidate':spec['id'],'label':'EXAM','execution_label':'DRYRUN' if dryrun else 'ENGINEERING_ONLY',
            'phase':'stage-a','prompts':len(prompts),'failure_classes':[], 'cpu_pool_only':instance.ctx_size==16384,
            'free_parse_successes':0,'schema_parse_successes':0,'active_key_successes':0,'free_active_key_successes':0,'free_seed_reproducible':True,
            'seed_reproducible':True,'template_checks':[],'grammar_after_thinking':None}
    telemetry=[];stop=threading.Event()
    def sample():
        while not stop.is_set():
            try: telemetry.append(gpu_sample())
            except Exception as exc: telemetry.append({'error':repr(exc)})
            stop.wait(.2)
    thread=threading.Thread(target=sample,daemon=True);thread.start()
    component='offload'
    try:
        # Prefill the full declared context with no generated token.
        tokenized=post(instance,'/tokenize',{'content':'a ','add_special':True})['tokens']
        if not tokenized: raise ValueError('empty tokenisation result')
        target=instance.ctx_size
        tokens=(tokenized*((target+len(tokenized)-1)//len(tokenized)))[:target]
        reply=post(instance,'/completion',{'prompt':tokens,'n_predict':0,'seed':0,'temperature':0.2,'cache_prompt':False})
        if reply.get('tokens_evaluated')!=target: raise ValueError('prefill count does not equal declared context')
        result['prefill_tokens']=target
        samples=[s for s in telemetry if 'error' not in s]
        if not samples: raise ValueError('no VRAM telemetry')
        result['min_free_mib']=min(s['free_mib'] for s in samples)
        result['peak_used_mib']=max(s['used_mib'] for s in samples)
        if any('error' in s for s in telemetry) or result['min_free_mib']<1024:
            raise ValueError('VRAM monitoring unavailable or <1 GiB free during prefill')
        component='template'
        render=template_renderer or (lambda messages:hf_render(spec,messages))
        for i in range(5):
            messages=[{'role':'user','content':f'Fixed template check {i}: JSON, whitespace, Unicode α, newline\nend.'}]
            actual=post(instance,'/apply-template',{'messages':messages,'add_generation_prompt':True,
                        'chat_template_kwargs':{'enable_thinking':spec['thinking_policy']['mode']!='off'}})['prompt']
            expected=render(messages)
            result['template_checks'].append(actual==expected)
        if not all(result['template_checks']): result['failure_classes'].append('template')
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
                reply=instance.chat(row['prompt'],max_tokens=4096,seed=row['seed'],extra={'temperature':.2,**kwargs})
                timings.append(time.monotonic()-t)
                message=reply['choices'][0]['message'];content=message.get('content') or ''
                final=re.sub(r'<think>.*?</think>\s*','',content,flags=re.S).strip()
                ok,key_valid=parse_proposal(final,row,structured)
                if structured: result['schema_parse_successes']+=ok
                else: result['free_parse_successes']+=ok
                if structured and ok: result['active_key_successes']+=key_valid
                if not structured and ok: result['free_active_key_successes']+=key_valid
                repeated=instance.chat(row['prompt'],max_tokens=4096,seed=row['seed'],extra={'temperature':.2,**kwargs})
                repeated_message=repeated['choices'][0]['message']
                if structured: result['seed_reproducible'] &= repeated_message==message
                else: result['free_seed_reproducible'] &= repeated_message==message
                reasoning=(reply.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens')
                token_rows.append({**reply.get('usage',{}),'reasoning_tokens':reasoning})
                pair.append({'structured':structured,'raw_content':content,'reasoning_content':message.get('reasoning_content'),
                             'parse_ok':ok,'repeat_message':repeated_message,'usage':reply.get('usage',{})})
            except Exception as exc:
                failure='timeout' if 'timeout' in str(exc).lower() or 'timed out' in str(exc).lower() else 'parse'
                
                if structured: result['failure_classes'].append(failure)
                pair.append({'structured':structured,'error':repr(exc)})
        responses.append({'prompt_id':row.get('id'),'responses':pair})
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
    result['failure_classes']=sorted(set(result['failure_classes']))
    result['passed']=not result['failure_classes']
    return result


def main(argv=None):
    import argparse
    from r1.harness import import_harness
    import_harness()
    from autoresearch.llm.providers import manager_response_format
    from r1.exam.runtime import gpu_sample
    from r1.exam.campaign import write_json
    from r1.scripts.llama_server_instance import LlamaServerInstance
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
    job=json.loads(Path(a.job).read_text());cfg=job['config'];spec=job['candidate']
    inst=LlamaServerInstance(job['out'],cfg['server']['binary'],model_path=spec['runtime']['model_path'],alias=spec['id'],
                             ctx_size=job['ctx'],port=job['port'])
    prompts=load_prompts(cfg['prompts'],cfg['prompts_sha256'],dryrun=bool(cfg.get('dryrun')))
    render=(lambda ms: ''.join(f"{m['role']}: {m['content']}\n" for m in ms)+'assistant: ') if cfg.get('dryrun') else None
    result=run_stage_a(inst,spec,prompts,gpu_sample=lambda:gpu_sample(cfg),schema_format=manager_response_format(),
                       dryrun=bool(cfg.get('dryrun')),template_renderer=render)
    if spec['thinking_policy'].get('switchable') is True or spec['thinking_policy']['mode']=='always_on':
        try:
            reply=inst.chat(prompts[0]['prompt'],max_tokens=4096,seed=prompts[0]['seed'],extra={
                'temperature':.2,'response_format':manager_response_format(),
                'chat_template_kwargs':{'enable_thinking':True},'reasoning_budget':2048})
            message=reply['choices'][0]['message'];final=re.sub(r'<think>.*?</think>\s*','',message['content'],flags=re.S)
            parsed=json.loads(final);reasoning=(reply.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens')
            grammar=bool(reasoning or message.get('reasoning_content')) and isinstance(parsed,dict) and set(parsed)==set(manager_response_format()['json_schema']['schema']['required'])
            result['thinking_grammar_probe']={'passed':grammar,'message':message,'usage':reply.get('usage')}
            result['thinking_disabled_due_grammar']=not grammar and spec['thinking_policy']['mode']!='always_on'
            if not grammar and spec['thinking_policy']['mode']=='always_on':
                result['failure_classes']=sorted(set(result['failure_classes']+['grammar']));result['passed']=False
        except Exception as exc:
            result['thinking_grammar_probe']={'passed':False,'error':repr(exc)}
            result['thinking_disabled_due_grammar']=spec['thinking_policy']['mode']!='always_on'
            if not result['thinking_disabled_due_grammar']: result['passed']=False;result['failure_classes'].append('grammar')
    if not cfg.get('dryrun'):
        from r1.exam.fit import estimate
        source=Path(spec['runtime']['model_config_path'])
        if digest_file(source)!=spec['runtime']['model_config_sha256']: raise ValueError('source config pin mismatch')
        result['fit_estimate']=estimate(json.loads(source.read_text()),spec['quant_source']['size_bytes'],job['ctx'])
        if not result['fit_estimate']['estimated_admissible']:
            result['failure_classes']=sorted(set(result['failure_classes']+['fit_estimate']));result['passed']=False
    write_json(Path(job['out'])/'stage_a.json',result)

if __name__=='__main__': main()
