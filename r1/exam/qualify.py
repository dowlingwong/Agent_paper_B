"""Stage A offload qualification on the exact exam flags; raw telemetry precedes footprint pinning."""
import argparse
import json
import math
import re
from pathlib import Path
from r1.scripts import llamacpp_probe, llama_server_instance as lsi
from r1.scripts.ollama_instance import free_port
from r1.exam.campaign import write_json
from r1.exam.guards import digest_file


def known_load_oom(raw, cfg, out):
    """Distinguish an evidenced allocation failure from missing/unknown telemetry."""
    log=Path(raw.get('server_log',''))
    pins=raw.get('pins_match') or {}
    if (not log.is_file() or not log.resolve().is_relative_to(Path(out).resolve()) or
        raw.get('gpu_uuid')!=cfg['gpu_uuid'] or any(pins.get(k) is not True for k in ('build','model_sha256')) or
        not raw.get('server_stop') or raw['server_stop'].get('returncode') is None): return None
    text=log.read_text(errors='replace')
    if not re.search(r'^ggml_backend_cuda_buffer_type_alloc_buffer:.*cudaMalloc failed: out of memory\s*$',text,re.M): return None
    evidence={'kind':'cuda_allocation_out_of_memory','server_log_sha256':digest_file(log),'healthy_idle_after_stop':False}
    try:
        from r1.exam.runtime import gpu_sample
        apps=lsi.gpu_compute_apps();sample=gpu_sample(cfg)
        evidence.update(compute_apps_after_stop=apps,gpu_after_stop=sample)
        evidence['healthy_idle_after_stop']=apps==[] and sample['free_mib']>=1024
    except Exception as error:evidence['census_error']=repr(error)
    return evidence


def qualify(job):
    # Direct qualification must not bypass Stage A's pending D3 review gate.
    from r1.exam.stage_a import require_d3_evidence
    require_d3_evidence()
    cfg=job['config'];spec=job['candidate'];out=Path(job['out'])
    out.mkdir(parents=True,exist_ok=True)
    if cfg.get('dryrun'):
        result={'status':'PASS','footprint_mib':5560,'label':'DRYRUN','synthetic_telemetry':True,'model_sha256':spec['quant_source']['sha256'],'context':job['ctx']}
    else:
        thinking={**spec['thinking_policy'],'budget':2048 if spec['thinking_policy']['mode']!='off' else 0}
        args=['--binary',cfg['server']['binary'],'--model',spec['runtime']['model_path'],'--gpu',cfg['gpu_uuid'],
              '--port',str(free_port()),'--ctx',str(job['ctx']),'--alias',spec['id'],'--out',str(out),
              '--expect-sha256',spec['quant_source']['sha256'],'--expect-build',cfg['server']['build'],
              '--expect-binary-sha256',cfg['server']['binary_sha256'],
              '--exam-stage-a',
              '--min-gpu-mib',str(math.ceil(.9*spec['quant_source']['size_bytes']/2**20)),
              '--server-extra-args',json.dumps(['--jinja','--cache-type-k','q8_0','--cache-type-v','q8_0']),
              '--thinking-policy',json.dumps(thinking)]
        code=llamacpp_probe.main(args)
        raw_path=max(out.glob('probe_*.json'));raw=json.loads(raw_path.read_text())
        # No footprint can be adopted without loaded-state PID/GPU telemetry.
        footprint=raw.get('footprint_mib_to_pin')
        success=code==0 and isinstance(footprint,(int,float)) and math.isfinite(footprint) and footprint>0
        # A nonzero probe or failed telemetry is an infrastructure STOP unless
        # explicitly classified below from a retained, pinned allocation OOM
        # and a healthy idle post-state. A positive footprint alone is not proof
        # of a completed mechanical failure.
        status='PASS' if success else 'PREPARATION_STOP'
        allocation=known_load_oom(raw,cfg,out) if footprint is None else None
        if allocation and allocation['healthy_idle_after_stop']:status='MECHANICAL_FAILURE'
        result={'status':status,'footprint_mib':footprint,
                'label':'ENGINEERING_ONLY','raw_probe':str(raw_path),'raw_probe_sha256':digest_file(raw_path),
                'model_sha256':spec['quant_source']['sha256'],'context':job['ctx'],'offload_route':raw.get('route'),
                'stop_reasons':raw.get('stop_reasons',[]),'allocation_failure_evidence':allocation}
    write_json(out/'qualification.json',result)
    return result


def qualification_exit_code(result):
    """Only a fully recorded candidate OOM can return normally for fallback."""
    status=result.get('status') if isinstance(result,dict) else None
    if status=='PASS': return 0
    if status=='MECHANICAL_FAILURE':
        evidence=result.get('allocation_failure_evidence') or {}
        if evidence.get('kind')=='cuda_allocation_out_of_memory' and evidence.get('healthy_idle_after_stop') is True:
            return 0
    return 1


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
    job=json.loads(Path(a.job).read_text())
    from r1.exam.cache_runtime import authorize_cooperative_stagea
    authorize_cooperative_stagea(job['config'])
    result=qualify(job);return qualification_exit_code(result)

if __name__=='__main__': raise SystemExit(main())
