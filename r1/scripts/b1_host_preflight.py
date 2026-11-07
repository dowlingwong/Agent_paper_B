"""One owned B1 host preflight: committed gate, flock and native server; no inference.

This is not B1 execution. The operator must complete the reviewed O2/site and
no-preemption prerequisites before invoking it. Output is retained on failure.
"""
from __future__ import annotations

import argparse
import copy
import math
import fcntl
import json
import os
import signal
import stat
import sys
from pathlib import Path

from r1.exam.analyze import load_rule, thinking_off_capable
from r1.exam.b1_lease import acquire, verify_server_fd
from r1.exam.guards import space_check
from r1.exam.runtime import (B1_CONFIG_REL, REPO, EXAM_SERVER_ARGS, ExamRunner,
    author_gate, b1_harness_sources, gpu_sample, host_check, load_config,
    read_registry, require_committed_b1_config, require_committed_b1_registry,
    template_repair_args, worker_environment, placeholders)
from r1.scripts.exam_runner import (stage_a_pass_set, verify_anchor_reference,
    refuse_cache_prompt_override, check_template_repairs)
from r1.exam.observer import _authorized_candidate
from r1.scripts import llama_server_instance as lsi
from r1.scripts.llama_server_instance import LlamaServerInstance, gpu_compute_apps


def resolve_stage_a_spec(spec, cfg, registry, eligible):
    """Use B1's PASS-row footprint and independently apply its observer binding."""
    result=copy.deepcopy(spec)
    runtime=result.get('runtime') or {}
    if placeholders(runtime.get('footprint_mib')):
        accepted=eligible.get(result['id']) or {}
        if (accepted.get('model_sha256')!=(result.get('quant_source') or {}).get('sha256') or
                accepted.get('build')!=(cfg.get('server') or {}).get('build')):
            raise RuntimeError('STOP: Stage A model/build mismatch')
        runtime['footprint_mib']=(accepted.get('qualification') or {}).get('footprint_mib')
    value=runtime.get('footprint_mib')
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
        raise RuntimeError('STOP: Stage A footprint is not positive and finite')
    result['runtime']=runtime
    if not _authorized_candidate({'candidate':result},cfg,registry):
        raise RuntimeError('STOP: Stage A footprint does not match authorized candidate')
    return result


def check_b1_protocol(cfg, rows, eligible):
    """Apply production B1's pre-server cache, template and grammar checks."""
    if cfg.get('cache_prompt') is not False:
        raise RuntimeError('STOP: B1 requires cache_prompt explicitly false')
    refuse_cache_prompt_override()
    check_template_repairs(cfg,rows)
    unavailable=[s['id'] for s in rows if s['id'] in eligible and
                 (s.get('thinking_policy') or {}).get('switchable') is True and
                 eligible[s['id']].get('thinking_disabled_due_grammar')]
    if unavailable:
        raise RuntimeError('STOP: required thinking-on sensitivity disabled by Stage A grammar: '+', '.join(unavailable))


def check_inputs(expected_head, out):
    """Run the same committed B1 gate and pin validation without starting work."""
    cfg=load_config(REPO/B1_CONFIG_REL)
    if cfg.get('dryrun'):
        raise RuntimeError('STOP: preflight requires committed production config')
    head=require_committed_b1_config(REPO/B1_CONFIG_REL,cfg)
    if head != expected_head:
        raise RuntimeError('STOP: reviewed HEAD mismatch')
    registry=read_registry(cfg['registry'])
    require_committed_b1_registry(cfg,head,selected_path=REPO/cfg['registry'],selected_registry=registry)
    rule,rule_sha=load_rule(cfg['rule'],cfg['rule_sha256'])
    if rule.get('version')!='x5_rule/v2' or author_gate(cfg,'b1',rule_sha)!=head:
        raise RuntimeError('STOP: committed B1 gate mismatch')
    verify_anchor_reference(cfg)
    env=worker_environment()
    import numpy, sklearn
    print(json.dumps({'python':sys.executable,'numpy':numpy.__version__,'sklearn':sklearn.__version__,
        'worker_python':str(Path(sys.executable).parent/'python3'),
        'threads':[env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')]}),flush=True)
    for node in cfg['nodes']:
        b1_harness_sources(node,cfg['harness_commit'])
    host_check(cfg,out)
    if Path(out).absolute().parent != Path(cfg['work_dir']).absolute():
        raise RuntimeError('STOP: preflight directory must be a direct child of work_dir')
    for key in ('models_dir','work_dir'):
        space_check(cfg[key])
    rows=registry['candidates']+registry['software_anchors']+registry.get('sensitivities',[])
    eligible=stage_a_pass_set(cfg,{s['id'] for s in rows if s.get('role')=='candidate'},v2=True)
    check_b1_protocol(cfg,rows,eligible)
    matches=[s for s in rows if s['id']=='qwen25_coder_7b' and s.get('role')=='anchor']
    if len(matches)!=1 or 'qwen25_coder_7b' not in eligible:
        raise RuntimeError('STOP: Stage A approved model anchor unavailable')
    # Reuse the production constructor checks, including code and harness pins.
    runner=ExamRunner(cfg,out,b1_config_head=head)
    spec=resolve_stage_a_spec(matches[0],cfg,registry,eligible)
    # Match B1's eligible model selection and its declared always-on skip.
    validated=[]
    for item in rows:
        if item['id'] not in eligible or item.get('kind') in ('random_valid','scripted'):
            continue
        if (item.get('role') in ('candidate','sensitivity') and
                rule['thinking_mode']['always_on_in_b1']=='skip' and
                not thinking_off_capable(item.get('thinking_policy'))):
            continue
        resolved=resolve_stage_a_spec(item,cfg,registry,eligible)
        template_repair_args(resolved)
        runner.validate_spec(resolved)
        validated.append(item['id'])
    if spec['id'] not in validated:
        raise RuntimeError('STOP: model anchor was not validated')
    print(json.dumps({'validated_models':validated}),flush=True)
    build=runner.validate_spec(spec)
    return cfg,spec,build


def idle_gpu(cfg):
    sample=gpu_sample(cfg)
    apps=gpu_compute_apps()
    if apps is None or apps or sample['free_mib']<1024 or sample['utilisation_percent']>5:
        raise RuntimeError('STOP: GPU occupancy, margin or visibility unsuitable')
    return sample


def verify_contender(path, fd):
    flags=os.O_RDWR | os.O_NOFOLLOW
    contender=os.open(path,flags)
    try:
        a=os.fstat(fd); b=os.fstat(contender)
        if not stat.S_ISREG(b.st_mode) or (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino):
            raise RuntimeError('STOP: lock contender inode mismatch')
        try:
            fcntl.flock(contender,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'dev':a.st_dev,'ino':a.st_ino,'contender_refused':True}
        raise RuntimeError('STOP: independent lock contender unexpectedly succeeded')
    finally:
        os.close(contender)



_HANDLED_SIGNALS=(signal.SIGTERM,signal.SIGINT,signal.SIGHUP)


def start_owned_server(inst, *, spawning=None, received=None, **kwargs):
    """Bind the child before acting on a signal delivered during Popen.

    The short single-threaded preflight temporarily wraps only its existing
    server spawn. Signals are deferred in the parent during Popen; no signal
    mask is inherited by the child and no production module changes on disk.
    """
    spawning = spawning if spawning is not None else [False]
    received = received if received is not None else []
    original=lsi.subprocess.Popen
    def tracked_spawn(*args,**spawn_kwargs):
        if inst.process is not None:
            raise RuntimeError('STOP: unexpected second preflight server spawn')
        spawning[0]=True
        try:
            child=original(*args,**spawn_kwargs)
            inst.process=child
        finally:
            spawning[0]=False
        if received:
            raise InterruptedError(f'STOP: preflight interrupted by signal {received[0]}')
        return child
    lsi.subprocess.Popen=tracked_spawn
    try:
        return inst.start(**kwargs)
    finally:
        lsi.subprocess.Popen=original


def stop_owned_server(inst):
    """Stop an owned live child, including before its server record exists."""
    if inst is None or inst.process is None or inst.process.poll() is not None:
        return
    if inst.record.get('pgid') is None:
        # Popen remains our unreaped child here: its PID cannot be reused.
        pid=inst.process.pid
        if os.getpgid(pid)!=pid:
            raise RuntimeError('STOP: owned early server group identity mismatch')
        inst.record['pgid']=pid
    inst.stop()
    if inst.process.poll() is None:
        raise RuntimeError('STOP: owned server did not exit')


def run(expected_head, out):
    cfg,spec,build=check_inputs(expected_head,out)
    out=Path(out)
    idle_gpu(cfg)
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    lock=Path.home()/'r1_locks'/'gpu0.lock'
    if lock.is_symlink() or not lock.is_file():
        raise RuntimeError('STOP: existing lock file unavailable')
    fd=None
    inst=None
    signal_handlers={}
    received=[]
    cleanup_started=[False]
    spawning=[False]
    def interrupted(signum, frame):
        received.append(signum)
        if not cleanup_started[0] and not spawning[0] and len(received)==1:
            raise InterruptedError(f'STOP: preflight interrupted by signal {signum}')
    try:
        for sig in _HANDLED_SIGNALS:
            signal_handlers[sig]=signal.signal(sig,interrupted)
        fd=acquire(lock)
        lock_info=verify_contender(lock,fd)
        before=idle_gpu(cfg)
        inst=LlamaServerInstance(out,cfg['server']['binary'],model_path=spec['runtime']['model_path'],
            alias=spec['id'],ctx_size=cfg['ctx_size'],n_gpu_layers=cfg['n_gpu_layers'],
            gpu_uuid=cfg['gpu_uuid'],extra_args=[*EXAM_SERVER_ARGS,*template_repair_args(spec)],
            thinking_policy={**spec['thinking_policy'],'mode':'off','budget':0},
            label='ENGINEERING_ONLY',start_timeout=cfg['server']['start_timeout'])
        inst.b1_preserve_records=True
        start_owned_server(inst,spawning=spawning,received=received,build=build,
                           model_sha256=spec['quant_source']['sha256'],b1_lease_fd=fd)
        verify_server_fd(fd,inst.process.pid)
        offload=inst.offload(footprint_mib=spec['runtime']['footprint_mib'])
        if not offload['full'] or spec['id'] not in (inst.model_ids() or []):
            raise RuntimeError('STOP: full offload or model alias unavailable')
        if (inst.props() or {}).get('model_path') != spec['runtime']['model_path']:
            raise RuntimeError('STOP: model path identity mismatch')
        sample=gpu_sample(cfg); apps=gpu_compute_apps()
        if (apps is None or any(row['pid']!=inst.process.pid for row in apps)
                or sample['free_mib']<1024):
            raise RuntimeError('STOP: GPU occupancy or margin changed')
        print(json.dumps({'phase':'ENGINEERING_ONLY','head':expected_head,'gpu_before':before,
              'gpu_loaded':sample,'lock':lock_info,'server_pid':inst.process.pid,
              'server_start_ticks':inst.record.get('start_ticks'),'lease_fd':fd,
              'model':spec['id'],'offload':offload},sort_keys=True),flush=True)
    finally:
        original=sys.exc_info()[1]
        cleanup_started[0]=True
        cleanup_error=None
        try:
            stop_owned_server(inst)
        except BaseException as exc:
            cleanup_error=exc
            try: print(f'STOP: owned server shutdown failed: {exc}',file=sys.stderr,flush=True)
            except Exception: pass
        try:
            if fd is not None:
                os.close(fd)
        except BaseException as exc:
            if cleanup_error is None: cleanup_error=exc
            try: print(f'STOP: lease close failed: {exc}',file=sys.stderr,flush=True)
            except Exception: pass
        finally:
            for sig,handler in signal_handlers.items():
                signal.signal(sig,handler)
        if received:
            try: print(f'STOP: preflight received signals {received}',file=sys.stderr,flush=True)
            except Exception: pass
        if cleanup_error is not None and original is None:
            raise cleanup_error
        if received and original is None:
            raise InterruptedError(f'STOP: preflight interrupted by signal {received[0]}')
    print('PREFLIGHT_PASS: owned server exited and own lease descriptor closed',flush=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--head',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    run(args.head,args.out)


if __name__=='__main__':
    main()
