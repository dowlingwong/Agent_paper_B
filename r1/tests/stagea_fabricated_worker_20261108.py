"""Synthetic-only bootstrap around the real Stage A worker entrypoint.

Explicitly substitutes cache/lease identity, journal validation, transport and
telemetry in this child. Never import in production or use on a real server.
"""
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from r1.exam import cache_descriptive, cache_runtime, cache_order, cache_proc, cache_false, cache_nongen, stage_a, runtime
from r1.scripts import llama_server_instance


def render(messages):
    return ''.join(f"{m['role']}: {m['content']}\n" for m in messages)+'assistant: '


def post(url, route, payload):
    if not url.startswith('http://127.0.0.1:'): raise RuntimeError('synthetic localhost only')
    request=Request(url+route, data=json.dumps(payload).encode(),
                    headers={'Content-Type':'application/json'},method='POST')
    with urlopen(request,timeout=10) as response: return json.load(response)


class Instance:
    def __init__(self, _out, _binary, *, model_path, alias, ctx_size, port):
        self.url=f'http://127.0.0.1:{port}'; self.alias=alias; self.ctx_size=ctx_size


class FalseRecorder:
    def __init__(self, url, alias, *, census, identity, journal_path):
        self.url=url;self.alias=alias
        with Path(journal_path).open('x') as f: f.write('{}\n')
    def close(self): pass
    def completion(self,payload): return post(self.url,'/completion',payload)
    def chat(self,prompt,*,seed,**kwargs):
        payload={'model':self.alias,'messages':[{'role':'user','content':prompt}],
                 'seed':seed,'max_tokens':kwargs.get('max_tokens',4096)}
        payload.update(kwargs.get('extra') or {})
        return post(self.url,'/v1/chat/completions',payload)


class NonGeneration:
    def __init__(self, url, *, census, identity, journal_path):
        self.url=url
        with Path(journal_path).open('x') as f: f.write('{}\n')
    def close(self): pass
    def post(self,route,payload): return post(self.url,route,payload)

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
    lease_fd=int(os.environ['SYNTHETIC_LEASE_FD'])
    os.fstat(lease_fd)
    print(f'SYNTHETIC_STAGE_A_WORKER pid={os.getpid()} parent={os.getppid()} lease_fd_open=True',flush=True)
    stage_a.main(sys.argv[1:])


if __name__=='__main__': main()
