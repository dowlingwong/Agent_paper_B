"""Stage A offload qualification on the exact exam flags; raw telemetry precedes footprint pinning."""
import argparse
import json
import math
import re
from pathlib import Path
from r1.scripts import llamacpp_probe, llama_server_instance as lsi
from r1.scripts.ollama_instance import free_port
from r1.exam.campaign import write_json
from r1.exam.runtime import EXAM_SERVER_ARGS, template_repair_args
from r1.exam.guards import digest_file


def known_load_oom(raw, cfg, out, spec):
    """Distinguish an evidenced allocation failure from missing/unknown telemetry.

    Real startup-OOM probes retain top-level gpu_uuid/binary_sha256/model_sha256/build
    and a ``dedicated llama-server exited during start (rc=1)`` stop reason, but leave
    ``server_stop``/``pins_match`` unset (same real shape as the template STOP).  The
    pinned identity therefore comes from those top-level fields, and the recorded exit
    from ``server_stop`` or the stop reason; the *log* must be retained inside the
    attempt directory and contain the cudaMalloc OOM line.  The post-stop census must be
    healthy for the 16k fallback to be allowed.
    """
    log=Path(raw.get('server_log',''))
    try:
        inside=log.is_file() and log.resolve().is_relative_to(Path(out).resolve())
    except OSError:
        inside=False
    if not inside: return None
    if raw.get('verdict')!='STOP' or raw.get('footprint_mib_to_pin') is not None: return None
    if raw.get('gpu_uuid')!=cfg['gpu_uuid']: return None
    if raw.get('binary_sha256')!=cfg['server']['binary_sha256']: return None
    if raw.get('model_sha256')!=(spec.get('quant_source') or {}).get('sha256'): return None
    build=raw.get('build') or {}
    if build.get('version_line')!=cfg['server']['build']: return None
    exits=[str(reason) for reason in (raw.get('stop_reasons') or [])
           if re.search(r'dedicated llama-server exited during start \(rc=\d+\)',str(reason))]
    stopped=(raw.get('server_stop') or {}).get('returncode') if isinstance(raw.get('server_stop'),dict) else None
    if stopped is None and not exits: return None
    text=log.read_text(errors='replace')
    match=re.search(r'ggml_backend_cuda_buffer_type_alloc_buffer:.*cudaMalloc failed: out of memory\s*$',text,re.M)
    if not match: return None
    evidence={'kind':'cuda_allocation_out_of_memory','server_log':str(log.resolve()),
              'server_log_sha256':digest_file(log),'matched_line':match.group(0).strip()[:300],
              'exit_evidence':{'server_stop':raw.get('server_stop'),
                               'stop_reason':exits[0] if exits else None},
              'pins':{'gpu_uuid':raw.get('gpu_uuid'),'binary_sha256':raw.get('binary_sha256'),
                      'model_sha256':raw.get('model_sha256'),'build':build.get('version_line')},
              'healthy_idle_after_stop':False}
    try:
        from r1.exam.runtime import gpu_sample
        apps=lsi.gpu_compute_apps();sample=gpu_sample(cfg)
        evidence.update(compute_apps_after_stop=apps,gpu_after_stop=sample)
        evidence['healthy_idle_after_stop']=apps==[] and sample['free_mib']>=1024
    except Exception as error:evidence['census_error']=repr(error)
    return evidence


def known_template_parse_failure(raw, cfg, out, spec):
    """A pinned-build *chat template* incompatibility is a candidate failure class.

    The runbook keeps template failures apart from offload/parse/timeout failures.
    llama.cpp exits during startup when its automatic parser generator cannot parse
    the model template (e.g. an unguarded ``tools | tojson``); that is a property of
    this candidate under the pinned build, not an infrastructure STOP.  Only retained
    evidence qualifies: a server log inside the attempt directory whose SHA-256 is
    recorded, matching pinned GPU/binary/build/model identities, a recorded startup
    exit (``server_stop.returncode`` or a ``dedicated llama-server exited during
    start (rc=N)`` stop reason), and the explicit template parser error followed by
    the model-loading failure.  Anything else remains PREPARATION_STOP.
    """
    log=Path(raw.get('server_log',''))
    try:
        inside=log.is_file() and log.resolve().is_relative_to(Path(out).resolve())
    except OSError:
        inside=False
    if not inside: return None
    if raw.get('verdict')!='STOP' or raw.get('footprint_mib_to_pin') is not None: return None
    if raw.get('gpu_uuid')!=cfg['gpu_uuid']: return None
    if raw.get('binary_sha256')!=cfg['server']['binary_sha256']: return None
    if raw.get('model_sha256')!=(spec.get('quant_source') or {}).get('sha256'): return None
    build=raw.get('build') or {}
    if build.get('version_line')!=cfg['server']['build']: return None
    exits=[str(reason) for reason in (raw.get('stop_reasons') or [])
           if re.search(r'dedicated llama-server exited during start \(rc=\d+\)',str(reason))]
    stopped=(raw.get('server_stop') or {}).get('returncode') if isinstance(raw.get('server_stop'),dict) else None
    if stopped is None and not exits: return None
    text=log.read_text(errors='replace')
    match=re.search(r'^.*chat template parsing error.*$',text,re.M)
    if not match or 'exiting due to model loading error' not in text: return None
    return {'kind':'chat_template_parse_error','server_log':str(log.resolve()),
            'server_log_sha256':digest_file(log),'matched_line':match.group(0).strip()[:300],
            'exit_evidence':{'server_stop':raw.get('server_stop'),
                             'stop_reason':exits[0] if exits else None},
            'pins':{'gpu_uuid':raw.get('gpu_uuid'),'binary_sha256':raw.get('binary_sha256'),
                    'model_sha256':raw.get('model_sha256'),'build':build.get('version_line')},
            'failure_class':'template','retry_at_16k':False}


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
              '--server-extra-args',json.dumps(list(EXAM_SERVER_ARGS)+template_repair_args(spec)),
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
        allocation=known_load_oom(raw,cfg,out,spec) if footprint is None else None
        template=None
        if allocation and allocation['healthy_idle_after_stop']:status='MECHANICAL_FAILURE'
        elif footprint is None:
            template=known_template_parse_failure(raw,cfg,out,spec)
            if template: status='TEMPLATE_FAILURE'
        result={'status':status,'footprint_mib':footprint,
                'label':'ENGINEERING_ONLY','raw_probe':str(raw_path),'raw_probe_sha256':digest_file(raw_path),
                'model_sha256':spec['quant_source']['sha256'],'context':job['ctx'],'offload_route':raw.get('route'),
                'stop_reasons':raw.get('stop_reasons',[]),'allocation_failure_evidence':allocation,
                'template_failure_evidence':template}
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
    if status=='TEMPLATE_FAILURE':
        evidence=result.get('template_failure_evidence') or {}
        if evidence.get('kind')=='chat_template_parse_error' and evidence.get('failure_class')=='template':
            return 0
    return 1


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
    job=json.loads(Path(a.job).read_text())
    from r1.exam.cache_runtime import authorize_cooperative_stagea
    authorize_cooperative_stagea(job['config'])
    result=qualify(job);return qualification_exit_code(result)

if __name__=='__main__': raise SystemExit(main())
