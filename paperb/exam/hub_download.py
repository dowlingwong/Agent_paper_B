"""Pinned HTTPS transport for Phase 2; isolated children, retained partials, full SHA receiving."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import threading
from r1.exam.guards import artifact_label, guarded_download, quantization_blockers, space_check
from urllib.parse import quote

ROOT=Path('/home/dowling/exam-x/models')
WORK=Path('/home/dowling/exam-x/work')


def receive_one(spec, out, *, check_space=space_check, cancel=None):
    def guard(path):
        if cancel is not None and cancel.is_set(): raise InterruptedError('STOP: cohort transport cancelled')
        return check_space(path)
    blockers=quantization_blockers(spec)
    if blockers: raise ValueError(str(blockers))
    source=spec['quant_source'];target=Path(spec['runtime']['model_path'])
    if not target.parent.resolve().is_relative_to(ROOT): raise ValueError('target outside approved models')
    guard(ROOT);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    certificate=out/(spec['id']+'.json')
    if certificate.exists():
        old=json.loads(certificate.read_text())
        if old['source']!=source: raise RuntimeError('STOP: existing receiving source differs')
    target.parent.mkdir(parents=True,exist_ok=True)
    reused=target.exists()
    start=time.time()
    if not reused:
        env={**os.environ,'HF_HOME':str(WORK/'hf'),'HF_HUB_DISABLE_XET':'1',
             'HF_HUB_DISABLE_TELEMETRY':'1','HF_HUB_DISABLE_IMPLICIT_TOKEN':'1'}
        # Standard HTTPS worker sends no HF authorization token.
        with (out/(spec['id']+'.transport.log')).open('ab') as log:
            child=subprocess.Popen([sys.executable,'-m','r1.exam.hub_download','--worker',json.dumps(spec)],
                                   env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while child.poll() is None:
                guard(ROOT);time.sleep(.2)
            if child.returncode: raise RuntimeError(f'STOP: HTTPS transport exited {child.returncode}; inspect retained partial and worker log')
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try: child.wait(timeout=15)
                except subprocess.TimeoutExpired: os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
    # Whole-artifact receiving validation, including reused files. No inference.
    guard(ROOT)
    if target.stat().st_size!=source['size_bytes']: raise RuntimeError('STOP: received artifact size mismatch; preserved')
    sha=__import__('hashlib').sha256()
    with target.open('rb') as f:
        for chunk in iter(lambda:f.read(16<<20),b''):
            guard(ROOT);sha.update(chunk)
    if sha.hexdigest()!=source['sha256']: raise RuntimeError('STOP: received artifact SHA mismatch; preserved')
    result={'candidate':spec['id'],'source_label':artifact_label(spec),'source':source,'target':str(target),
            'transport':'stdlib_https_retained_partial','result':{'reused':reused,'sha256':sha.hexdigest()},'started':start,'finished':time.time(),'space_after':guard(ROOT)}
    tmp=certificate.with_suffix('.json.tmp');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(certificate)
    print(spec['id'],'VERIFIED',flush=True)
    return result


def run_downloads(rows, out, *, check_space=space_check, workers=2):
    if not isinstance(workers,int) or isinstance(workers,bool) or not 1<=workers<=8: raise ValueError('download workers must be 1..8')
    stop=threading.Event();errors=[]
    def run(spec):
        if stop.is_set(): raise InterruptedError('STOP: queued artifact cancelled')
        try: return receive_one(spec,out,check_space=check_space,cancel=stop)
        except BaseException as exc:
            errors.append({'candidate':spec['id'],'error':repr(exc)});stop.set();raise
    def interrupt(signum, frame):
        stop.set();raise InterruptedError(f'STOP: transport controller signal {signum}')
    prior=None
    if threading.current_thread() is threading.main_thread():
        prior=signal.signal(signal.SIGTERM,interrupt)
    pool=ThreadPoolExecutor(max_workers=workers)
    try: return list(pool.map(run,rows))
    except BaseException:
        stop.set()
        if errors:
            Path(out).mkdir(parents=True,exist_ok=True)
            (Path(out)/'transport_stop.json').write_text(json.dumps({'status':'STOPPED','errors':errors},indent=2)+'\n')
        raise
    finally:
        stop.set();pool.shutdown(wait=True,cancel_futures=True)
        if prior is not None: signal.signal(signal.SIGTERM,prior)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registry');p.add_argument('--out');p.add_argument('--worker');p.add_argument('--workers',type=int,default=2)
    a=p.parse_args(argv)
    if platform.node().split('.')[0]!='TASL-2': raise RuntimeError('portal only')
    if a.worker:
        spec=json.loads(a.worker);source=spec['quant_source']
        target=Path(spec['runtime']['model_path'])
        url=f"https://huggingface.co/{source['repo']}/resolve/{source['revision']}/{quote(source['file'])}"
        guarded_download(url,target,sha256=source['sha256'],size_bytes=source['size_bytes'],storage_root=ROOT)
        return
    if not a.registry or not a.out: p.error('--registry and --out required')
    if (Path(a.out)/'transport_stop.json').exists(): raise RuntimeError('STOP: prior transport STOP record must be preserved and explicitly resolved before continuation')
    reg=json.loads(Path(a.registry).read_text());rows=reg['candidates']+reg.get('sensitivities',[])
    # Bounded direct HTTPS artifacts; no library-owned partial-file cleanup.
    run_downloads(rows,a.out,workers=a.workers)

if __name__=='__main__': main()
