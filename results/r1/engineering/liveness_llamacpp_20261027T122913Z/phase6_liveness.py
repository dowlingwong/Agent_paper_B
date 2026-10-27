"""Phase 6 (RUNBOOK A.7): D28 LLM liveness on the eight D21 nodes under llama.cpp, memory on,
R1-SCHEMA structured output. Starts the batch's own llama-server with the pinned config values,
verifies the pins and full GPU offload before and after, runs the runner's own liveness command,
and stops only the server it started. ENGINEERING_ONLY; AI-assisted (Claude).
"""
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

PAPER = Path(os.environ['PAPER_ROOT'])
sys.path.insert(0, str(PAPER))
from r1.scripts import llama_server_instance as lsi

def utc():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

cfg = json.loads((PAPER / 'r1/scripts/configs/c3_sweep_deepthought.json').read_text())
cfg['nodes'] = ['openml_breast_w', 'openml_sonar', 'openml_wdbc', 'openml_climate']  # D21-qualified nodes only
spec, live = cfg['llamacpp'], cfg['liveness']
stamp = utc()
out = PAPER / 'results/r1/engineering' / f'liveness_llamacpp_{stamp}'
work = Path(os.environ['WORK']) / f'liveness_work_{stamp}'
batch = Path(os.environ['WORK']) / f'liveness_batch_{stamp}'
for d in (out, work, batch):
    d.mkdir(parents=True, exist_ok=True)

record = {'label': 'ENGINEERING_ONLY', 'ai_assisted': 'AI-assisted (Claude)', 'utc': stamp,
          'host': os.uname().nodename, 'config': str(PAPER / 'r1/scripts/configs/c3_sweep_deepthought.json'),
          'nodes': cfg['nodes'], 'liveness': live, 'proposal_schema': cfg['proposal_schema'],
          'gpu_uuid': cfg['gpu_uuid'], 'out': str(out), 'work': str(work)}

build = lsi.build_info(spec['binary'])
record['build'] = build['version_line']
if build['version_line'] != spec['build']:
    sys.exit(f"STOP: build {build['version_line']!r} != pin {spec['build']!r}")
t0 = time.monotonic()
sha = lsi.sha256_file(spec['model_path'])
record['model_sha256'] = sha
record['sha256_seconds'] = round(time.monotonic() - t0, 1)
if sha != spec['model_sha256']:
    sys.exit(f'STOP: GGUF sha256 {sha} != pin {spec["model_sha256"]}')

inst = lsi.LlamaServerInstance(batch, spec['binary'], model_path=spec['model_path'],
                               alias=spec['model_alias'], port=spec['port'],
                               n_gpu_layers=spec['n_gpu_layers'], ctx_size=spec['ctx_size'],
                               gpu_uuid=cfg['gpu_uuid'], label='ENGINEERING_ONLY liveness',
                               start_timeout=float(spec['start_timeout']))
rec = inst.start(build=build, model_sha256=sha)
record['server'] = {k: rec.get(k) for k in ('pid', 'pgid', 'port', 'started_utc', 'healthy_utc', 'log')}
rc = None
try:
    record['served_models'] = inst.model_ids()
    record['props'] = inst.props()
    probe = inst.chat('ping', max_tokens=1, seed=1)
    record['one_token'] = {'completion_tokens': (probe.get('usage') or {}).get('completion_tokens')}
    if spec['model_alias'] not in (record['served_models'] or []):
        sys.exit(f"STOP: /v1/models does not list {spec['model_alias']!r}: {record['served_models']}")
    before = inst.offload(footprint_mib=spec['footprint_mib'])
    record['offload_before'] = {'full': before['full'], 'route': before.get('route'),
                                'gpu_memory': before.get('gpu_memory'), 'reasons': before.get('reasons')}
    if not before['full']:
        sys.exit(f'STOP: full offload not proven before the run: {before}')
    cmd = [sys.executable, '-m', 'r1.liveness', '--run', '--manager', 'langgraph',
           '--memory-mode', live['memory_mode'], '--nodes', *cfg['nodes'],
           '--instances', str(live['instances']), '--runs', str(live['runs']),
           '--transport-max-attempts', str(cfg['transport_max_attempts']),
           '--manager-model', 'llamacpp/' + spec['model_alias'],
           '--proposal-schema', cfg['proposal_schema'],
           '--out', str(out), '--work', str(work)]
    record['command'] = cmd
    env = {**os.environ, 'LLAMACPP_BASE_URL': rec['openai_base_url'], 'OMP_NUM_THREADS': '1',
           'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
           'PYTHONPATH': f"{os.environ['AR_HARNESS_ROOT']}/src:{PAPER}"}
    started = time.monotonic()
    with (Path(os.environ['WORK']) / 'logs' / f'liveness_{stamp}.log').open('w') as log:
        rc = subprocess.run(cmd, cwd=PAPER, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    record['liveness_returncode'] = rc
    record['liveness_seconds'] = round(time.monotonic() - started, 1)
    after = inst.offload(footprint_mib=spec['footprint_mib'])
    record['offload_after'] = {'full': after['full'], 'route': after.get('route'),
                               'gpu_memory': after.get('gpu_memory'), 'reasons': after.get('reasons')}
finally:
    record['server_stop'] = inst.stop()
    (out / 'liveness_run_record.json').write_text(json.dumps(record, indent=1, default=str) + '\n')
    (out / 'phase6_liveness.py').write_text(Path(__file__).read_text())

verdict = json.loads((out / 'liveness.json').read_text()) if (out / 'liveness.json').exists() else {}
print(json.dumps({'returncode': rc, 'out': str(out),
                  'offload_before': record.get('offload_before', {}).get('full'),
                  'offload_after': record.get('offload_after', {}).get('full'),
                  'verdicts': {n: {'pass': v['pass'], 'failed': v['failed_criteria']}
                               for n, v in (verdict.get('nodes') or {}).items()}}, indent=1))
