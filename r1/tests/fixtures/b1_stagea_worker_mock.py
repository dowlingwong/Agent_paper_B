"""Run the real Stage A worker with explicit, test-only synthetic boundaries.

This is NOT an operator entrypoint. It refuses non-DRYRUN jobs and anything
outside a marked temporary root. No network, model, GPU or Linux lease is used.
"""
import hashlib
import io
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path


def main():
    if len(sys.argv)!=2:
        raise SystemExit('synthetic fixture requires one job path')
    job_path=Path(sys.argv[1]).resolve(strict=True)
    job=json.loads(job_path.read_text());cfg=job['config'];root=Path(cfg['dryrun_root']).resolve(strict=True)
    temp_roots={Path(tempfile.gettempdir()).resolve(),Path('/tmp').resolve()}
    from r1.exam.runtime import APPROVED_EXAM_HOSTS
    forbidden={name.casefold() for name in APPROVED_EXAM_HOSTS}|{'ucrtasl','deepthought'}
    if (platform.node().split('.')[0].casefold() in forbidden or
            not any(root!=temp and root.is_relative_to(temp) for temp in temp_roots) or not (root/'.dryrun').is_file() or
            cfg.get('dryrun') is not True or not job_path.is_relative_to(root) or
            not Path(job['out']).resolve().is_relative_to(root) or
            not Path(cfg['prompts']).resolve().is_relative_to(root) or
            not Path(cfg['server']['binary']).resolve().is_relative_to(root)):
        raise SystemExit('STOP: synthetic Stage A fixture cannot run outside marked temporary DRYRUN')
    receipt=Path(job['out'])/'SYNTHETIC_stage_a_worker_identity.json'
    with receipt.open('x') as fh:
        json.dump({'label':'SYNTHETIC_ONLY','pid':os.getpid(),'parent_pid':os.getppid(),
                   'job':str(job_path),'transport':'in-memory fake; no socket'},fh)
    from r1.exam import stage_a, cache_runtime, cache_proc, cache_descriptive, cache_false, cache_nongen, runtime
    from r1.scripts.c3_fake_ollama import proposal_for

    # Explicit test-only stubs: never claim a real lease, coldness or census.
    stage_a.require_d3_evidence=lambda:None
    cache_runtime.authorize_cooperative_stagea=lambda *a,**k:None
    cache_runtime.reject_unverified_lease=lambda *a,**k:None
    cache_runtime.reject_unverified_cold=lambda *a,**k:None
    cache_runtime.validate_worker_binding=lambda *a,**k:None
    runtime.gpu_sample=lambda *a,**k:{'free_mib':20000,'used_mib':1000}

    def frozen_fixture(prompts,binding):
        path=Path(binding['path']).resolve(strict=True)
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=binding['sha256']:
            raise RuntimeError('STOP: synthetic prompt fixture binding mismatch')
        if stage_a.load_prompts(path,binding['sha256'],dryrun=True)!=prompts:
            raise RuntimeError('STOP: synthetic prompt fixture changed')
    cache_descriptive.verify_frozen_binding=frozen_fixture

    def synthetic_census(identity):
        observed={'pid':identity['pid'],'process_start_ticks':identity['process_start_ticks'],'executable':identity['binary']}
        sample={'method':cache_proc.CENSUS_METHOD,'scope':cache_proc.CENSUS_SCOPE,'count':1,
                'pid':identity['pid'],'process_start_ticks':identity['process_start_ticks'],
                'observed':[observed],'monotonic_ns':time.monotonic_ns(),
                'inaccessible_executable_links':0,'missing_executable_links':0,'unreadable_executable_links':0,
                'unreadable_executable_errnos':[],'unreadable_executable_samples':[],
                'unobserved_same_uid_calls':'assumed absent by author decision, not measured',
                'host_global_single_server':'NOT_CHECKABLE'}
        sample['snapshot_sha256']=cache_proc.census_digest(sample)
        return sample
    cache_proc.sample_llama_server_processes=synthetic_census

    class Response(io.BytesIO):
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): self.close()
    def fake_urlopen(request,timeout=None):
        prefix='http://127.0.0.1:'+str(job['port'])
        if not request.full_url.startswith(prefix+'/'):
            raise RuntimeError('STOP: synthetic transport refuses other destinations')
        route=request.full_url[len(prefix):];body=json.loads(request.data)
        if route=='/tokenize': value={'tokens':[1,2]}
        elif route=='/apply-template':
            value={'prompt':''.join(f"{m['role']}: {m['content']}\n" for m in body['messages'])+'assistant: '}
        elif route=='/completion':
            n=len(body['prompt']);value={'tokens_evaluated':n,'tokens_predicted':1,'timings':{'prompt_n':n,'cache_n':0}}
        elif route=='/v1/chat/completions':
            prompt=body['messages'][0]['content'];seed=body['seed']
            value={'choices':[{'message':{'content':json.dumps(proposal_for(prompt,seed)),'reasoning_content':'SYNTHETIC'}}],
                   'timings':{'prompt_n':10,'cache_n':0},
                   'usage':{'prompt_tokens':10,'prompt_tokens_details':{'cached_tokens':0},
                            'completion_tokens_details':{'reasoning_tokens':1}}}
        else: raise RuntimeError('STOP: unsupported synthetic route '+route)
        return Response(json.dumps(value).encode())
    cache_descriptive.urlopen=fake_urlopen;cache_false.urlopen=fake_urlopen;cache_nongen.urlopen=fake_urlopen
    os.environ['TRACKX_GPU_LEASE_FD']='3'  # marker only; actual lease operations are stubbed above
    stage_a.main(['--job',str(job_path)])


if __name__=='__main__':main()
