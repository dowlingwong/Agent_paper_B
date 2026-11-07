"""Synthetic-only bootstrap around the real Stage A worker entrypoint.

Explicitly substitutes cache/lease identity, journal validation, transport and
telemetry in this child. Never import in production or use on a real server.
"""
import json
import os
import sys
from pathlib import Path

from r1.exam import cache_descriptive, cache_runtime, cache_order, cache_proc, cache_false, cache_nongen, stage_a, runtime
from r1.scripts import llama_server_instance
from r1.scripts.c3_fake_ollama import proposal_for


def render(messages):
    return ''.join(f"{m['role']}: {m['content']}\n" for m in messages)+'assistant: '


class Instance:
    def __init__(self, _out, _binary, *, model_path, alias, ctx_size, port):
        self.url='http://127.0.0.1:1'; self.alias=alias; self.ctx_size=ctx_size


class FalseRecorder:
    def __init__(self, _url, _alias, *, census, identity, journal_path):
        with Path(journal_path).open('x') as f: f.write('{}\n')
    def close(self): pass
    def completion(self,payload):
        return {'tokens_evaluated':len(payload['prompt']),'tokens_predicted':1}
    def chat(self,prompt,*,seed,**kwargs):
        return {'choices':[{'message':{'content':json.dumps(proposal_for(prompt,seed)),
                                        'reasoning_content':'DRYRUN'}}],
                'usage':{'completion_tokens_details':{'reasoning_tokens':1}}}


class NonGeneration:
    def __init__(self, _url, *, census, identity, journal_path):
        with Path(journal_path).open('x') as f: f.write('{}\n')
    def close(self): pass
    def post(self,route,payload):
        if route=='/tokenize': return {'tokens':[1]}
        if route=='/apply-template': return {'prompt':render(payload['messages'])}
        raise AssertionError(route)


def fake_true_replay(_instance,_prompts,_schema,**kwargs):
    with Path(kwargs['journal_path']).open('x') as f: f.write('{}\n')
    return {'synthetic':True}


def main():
    stage_a.require_d3_evidence=lambda:None
    cache_runtime.authorize_cooperative_stagea=lambda cfg:None
    cache_runtime.reject_unverified_cold=lambda identity:None
    cache_runtime.validate_worker_binding=lambda identity,job:None
    cache_descriptive.true_replay=fake_true_replay
    cache_order.validate_local_order=lambda *args,**kwargs:{'synthetic':True}
    cache_proc.sample_llama_server_processes=lambda identity:[]
    cache_false.FalseCallRecorder=FalseRecorder
    cache_nongen.NonGenerationRecorder=NonGeneration
    runtime.gpu_sample=lambda cfg:{'free_mib':20000,'used_mib':1000}
    llama_server_instance.LlamaServerInstance=Instance
    print(f'SYNTHETIC_STAGE_A_WORKER pid={os.getpid()} parent={os.getppid()}',flush=True)
    stage_a.main(sys.argv[1:])


if __name__=='__main__': main()
