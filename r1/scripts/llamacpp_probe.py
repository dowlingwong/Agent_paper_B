"""GPU load probe of a GGUF on llama.cpp's ``llama-server`` (RUNBOOK A.11; batch B handoff and review).

Run on the sweep host from the paper checkout, before a sweep config is filled
in.  It uses the runner's own code (``r1/scripts/llama_server_instance.py``):

1. ``llama-server --version`` (the ``version: ...`` line = ``llamacpp.build``);
2. the GGUF's sha256 (= ``llamacpp.model_sha256``);
3. a dedicated server on one card (``CUDA_VISIBLE_DEVICES``), ``-ngl``/``-c`` as
   in the config, ``/health`` ready, ``/v1/models`` serving the alias, ``/props``;
4. a one-token completion, then a generation run of ``--gen-tokens`` tokens
   (``ignore_eos``) whose tokens/s come from llama-server's ``timings``;
5. **loaded-state telemetry recorded before any assertion**: ``nvidia-smi``
   compute apps and cards, the server's own MiB on the target card;
6. full-offload acceptance by the runner's two routes (author's revised
   acceptance, 25 Oct): (i) the log line ``offloaded N/N layers`` (a partial
   N/M is a STOP); else (ii) the server pid on the target GPU uuid with at least
   ``--expect-footprint-mib`` (a pin being checked) or ``--min-gpu-mib``
   (default 90 % of the GGUF size), **plus a CPU control run** (``-ngl 0``, same
   request) at least ``--min-speedup`` (2x) slower in generation tokens/s;
7. every server it started is stopped (only its own process groups).

The server's measured MiB is reported as ``footprint_mib_to_pin``.  Everything
goes under ``--out``: ``probe_<UTC>.json`` and ``probe_<UTC>/llama_server_<port>
[_r1].{log,json}`` (``_r1`` = the CPU control).  Exit 0 only for
``FULL_GPU_OFFLOAD``; 1 for ``STOP`` (also on any error); 2 for usage errors.
Standard library only.

    python3 -m r1.scripts.llamacpp_probe --binary /path/llama-server --model /path/model-Q4_K_M.gguf \\
        --gpu GPU-xxxxxxxx --port 18481 --out /path/to/logs

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from r1.scripts import llama_server_instance as lsi  # noqa: E402
from r1.scripts.ollama_instance import port_is_free  # noqa: E402

GEN_PROMPT = 'Write a Python function that returns the first twenty prime numbers, with a docstring.'


def _utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _nvidia(args: list[str]) -> str | None:
    try:
        return subprocess.run(['nvidia-smi', *args], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f'nvidia-smi failed: {exc!r}'


def resolve_gpu_uuid(gpu: str) -> str | None:
    """The UUID of ``--gpu`` (given as a UUID, or as an index resolved through nvidia-smi)."""
    if gpu.startswith('GPU-'):
        return gpu
    for line in (_nvidia(['--query-gpu=index,uuid', '--format=csv,noheader']) or '').splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 2 and parts[0] == gpu:
            return parts[1]
    return None


def tokens_per_second(reply: dict, seconds: float) -> tuple[float | None, str]:
    timings = reply.get('timings') or {}
    if isinstance(timings.get('predicted_per_second'), (int, float)) and timings['predicted_per_second'] > 0:
        return float(timings['predicted_per_second']), 'timings.predicted_per_second'
    tokens = (reply.get('usage') or {}).get('completion_tokens')
    if tokens and seconds > 0:
        return tokens / seconds, 'usage.completion_tokens / wall seconds'
    return None, 'unavailable'


def generation(inst, tokens: int, *, exam_stage_a=False) -> dict:
    started = time.monotonic()
    extra={'ignore_eos': True}
    if exam_stage_a: extra['cache_prompt']=False
    reply = inst.chat(GEN_PROMPT, max_tokens=tokens, seed=0, extra=extra)
    seconds = time.monotonic() - started
    tps, source = tokens_per_second(reply, seconds)
    return {'tokens_per_second': tps, 'source': source, 'wall_seconds': round(seconds, 3),
            'usage': reply.get('usage'), 'timings': reply.get('timings')}


def qualification_recorder(inst, args, path):
    """One identity-bound false-request journal; cold proof is not implied."""
    from r1.exam.cache_runtime import capture_parent_identity
    from r1.exam.cache_proc import sample_llama_server_processes
    from r1.exam.cache_false import FalseCallRecorder
    if not args.expect_binary_sha256 or not args.expect_sha256:
        raise RuntimeError('STOP: qualification recorder binary/model pins required')
    identity=capture_parent_identity(inst,binary_sha256=args.expect_binary_sha256,
                                     model_sha256=args.expect_sha256)
    census=lambda:sample_llama_server_processes(identity)
    recorder=FalseCallRecorder(inst.url,inst.alias,census=census,identity=identity,journal_path=path)
    return recorder,identity


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--binary', required=True)
    ap.add_argument('--model', required=True, help='GGUF file (absolute path)')
    ap.add_argument('--gpu', required=True, help='CUDA_VISIBLE_DEVICES value: one GPU UUID (or index)')
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--ctx', type=int, default=8192)
    ap.add_argument('--ngl', type=int, default=999)
    ap.add_argument('--alias', default='r1-manager')
    ap.add_argument('--start-timeout', type=float, default=600.0)
    ap.add_argument('--gen-tokens', type=int, default=64, help='tokens of the throughput run (GPU and CPU control)')
    ap.add_argument('--min-speedup', type=float, default=2.0, help='route (ii): GPU / CPU-control tokens/s')
    ap.add_argument('--min-gpu-mib', type=int, default=None,
                    help='route (ii) memory floor when no footprint is pinned yet (default: 90%% of the GGUF size)')
    ap.add_argument('--expect-footprint-mib', type=int, default=None, help='route (ii) against a pinned footprint')
    ap.add_argument('--expect-sha256', default=None)
    ap.add_argument('--expect-binary-sha256',default=None)
    ap.add_argument('--expect-build', default=None, help='the exact "version: ..." line')
    ap.add_argument('--server-extra-args', default=None, help='JSON list of flags for exact exam-path qualification')
    ap.add_argument('--thinking-policy', default=None, help='JSON exam thinking policy')
    ap.add_argument('--exam-stage-a',action='store_true',help='Stage A isolation, cache, and STOP preservation')
    ap.add_argument('--out', required=True, help='log directory (created)')
    args = ap.parse_args(argv)
    if args.exam_stage_a:
        # This direct entry point cannot bypass the Stage A D3 gate.
        from r1.exam.stage_a import require_d3_evidence
        require_d3_evidence()
    server_options = {}
    if args.server_extra_args is not None:
        flags = json.loads(args.server_extra_args)
        if not isinstance(flags, list) or not all(isinstance(x, str) for x in flags):
            ap.error('--server-extra-args must encode a list of strings')
        server_options['extra_args'] = flags
    if args.thinking_policy is not None:
        server_options['thinking_policy'] = json.loads(args.thinking_policy)
    if not Path(args.model).is_absolute() or not Path(args.binary).is_absolute():
        ap.error('--binary and --model must be absolute paths (they are pinned as given)')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    result: dict = {'schema': 'r1.llamacpp_probe/2', 'label': 'ENGINEERING_ONLY', 'ai_assisted': 'AI-assisted (Claude)',
                    'utc': stamp, 'host': platform.node(),
                    'args': {k: v for k, v in vars(args).items() if k not in ('server_extra_args', 'thinking_policy') or v is not None},
                    'route': None, 'cpu_control': None,
                    'footprint_mib_to_pin': None, 'stop_reasons': [], 'verdict': 'RUNNING'}
    path = out / f'probe_{stamp}.json'

    def save():
        path.write_text(json.dumps(result, indent=2, default=str) + '\n')

    def say(message):
        print(message, flush=True)
        result.setdefault('log', []).append(message)
        save()

    def stop(reason):
        result['stop_reasons'].append(reason)
        say(f'STOP: {reason}')

    if not port_is_free(args.port):
        stop(f'port {args.port} is in use')
        result['verdict'] = 'STOP'
        save()
        return 1
    result['build'] = lsi.build_info(args.binary)
    say(f'build: {result["build"]["version_line"]}')
    started = time.monotonic()
    result['model_sha256'] = lsi.sha256_file(args.model)
    result['sha256_seconds'] = round(time.monotonic() - started, 1)
    say(f'sha256: {result["model_sha256"]} ({result["sha256_seconds"]} s)')
    if args.exam_stage_a:
        # Pin failures must be discovered before starting any qualification
        # process, so failure never causes a later cleanup signal.
        binary_sha=lsi.sha256_file(args.binary)
        result['binary_sha256']=binary_sha
        if (not args.expect_binary_sha256 or not args.expect_sha256 or not args.expect_build or
            binary_sha!=args.expect_binary_sha256 or result['model_sha256']!=args.expect_sha256 or
            result['build']['version_line']!=args.expect_build):
            stop('Stage A qualification binary/model/build pin mismatch')
            result['verdict']='STOP';save();return 1
    gguf_mib = Path(args.model).stat().st_size / 2 ** 20
    floor = args.expect_footprint_mib or args.min_gpu_mib or math.ceil(0.9 * gguf_mib)
    uuid = resolve_gpu_uuid(args.gpu)
    result.update(gguf_mib=round(gguf_mib, 1), route_ii_floor_mib=floor, gpu_uuid=uuid,
                  gpus_before=_nvidia(['--query-gpu=index,uuid,name,memory.used,memory.total,driver_version,'
                                       'compute_cap', '--format=csv']))
    save()
    probe_dir = out / f'probe_{stamp}'
    inst = lsi.LlamaServerInstance(probe_dir, args.binary, model_path=args.model, alias=args.alias,
                                   port=args.port, n_gpu_layers=args.ngl, ctx_size=args.ctx, gpu_uuid=args.gpu,
                                   label='ENGINEERING_ONLY probe', start_timeout=args.start_timeout)
    if server_options:
        inst = lsi.LlamaServerInstance(probe_dir, args.binary, model_path=args.model, alias=args.alias,
                                      port=args.port, n_gpu_layers=args.ngl, ctx_size=args.ctx, gpu_uuid=args.gpu,
                                      label='ENGINEERING_ONLY probe', start_timeout=args.start_timeout, **server_options)
    offload = None
    gpu_recorder=None
    try:
        result['server'] = inst.start(build=result['build'], model_sha256=result['model_sha256'],
                                      preserve_on_failure=args.exam_stage_a)
        say(f'server healthy: pid {inst.record["pid"]}, log {inst.log_path}')
        # Cooperative Stage A: this worker's native server must be proved to hold
        # the SAME inherited lease open file description before any request is
        # issued (the start already verified ancestor->descendant kcmp + /proc).
        result['lease_inheritance'] = (result['server'] or {}).get('lease_inheritance')
        if os.environ.get('TRACKX_GPU_LEASE_FD'):
            from r1.exam.cache_runtime import validate_lease_inheritance_record
            try:
                validate_lease_inheritance_record(result['lease_inheritance'])
            except RuntimeError as exc:
                raise RuntimeError(f'STOP: qualification server lease inheritance unproved: {exc}') from exc
            if (result['server'] or {}).get('start_ticks') != result['lease_inheritance']['server_start_ticks']:
                raise RuntimeError('STOP: qualification server lease inheritance start ticks mismatch')
        result['served_models'] = inst.model_ids()
        props = inst.props() or {}
        result['props'] = {k: props.get(k) for k in ('model_path', 'total_slots', 'build_info')}
        target=inst
        if args.exam_stage_a:
            journal=probe_dir/'d3_qualification_gpu.jsonl'
            gpu_recorder,identity=qualification_recorder(inst,args,journal)
            result['qualification_gpu_identity']=identity
            result['qualification_gpu_journal']=str(journal)
            target=gpu_recorder
        one_extra={'cache_prompt':False} if args.exam_stage_a else None
        result['one_token'] = target.chat('Reply OK', max_tokens=1, seed=0,extra=one_extra).get('usage')
        result['gpu_generation'] = generation(target, args.gen_tokens,exam_stage_a=args.exam_stage_a)
        # Loaded-state telemetry before any assertion (deepthought 25 Oct: it was missing when the probe stopped).
        apps = lsi.gpu_compute_apps()
        mine = [r for r in (apps or []) if r['pid'] == inst.record['pid']]
        result['loaded'] = {'utc': _utc(), 'compute_apps': apps, 'server_rows': mine,
                            'gpus': _nvidia(['--query-gpu=index,uuid,memory.used,memory.total', '--format=csv'])}
        on_card = next((r for r in mine if r['gpu_uuid'] == uuid), None)
        result['footprint_mib_to_pin'] = on_card['used_mib'] if on_card else None
        save()
        offload = lsi.offload_check(inst.log_text(), pid=inst.record['pid'], gpu_uuid=uuid, footprint_mib=floor,
                                    apps=apps)
        if args.exam_stage_a and (args.alias not in (result.get('served_models') or []) or not offload['full']):
            stop('Stage A qualification did not establish alias and full offload')
    except Exception as exc:  # noqa: BLE001 - recorded; the verdict is then STOP
        stop(f'{type(exc).__name__}: {exc}')
    finally:
        if gpu_recorder is not None: gpu_recorder.close()
        if args.exam_stage_a and result['stop_reasons']:
            result['server_stop']=None
            result['server_preserved_on_stop']=inst.process is not None
        else:
            result['server_stop'] = {k: inst.stop().get(k) for k in ('stopped_utc', 'returncode', 'killed')} \
                if inst.process is not None else None
        result['server_log'] = str(inst.log_path)
        save()
    if args.exam_stage_a and result['stop_reasons']:
        result['verdict']='STOP';save();return 1
    if offload is None:
        offload = lsi.offload_report(inst.log_text())
        offload['full'] = False
    result['offload'] = offload
    if args.alias not in (result.get('served_models') or []):
        stop(f'alias {args.alias!r} not served (/v1/models: {result.get("served_models")})')
    if not offload['full']:
        for reason in offload['reasons'] or ['full offload not shown']:
            stop(reason)
    elif offload.get('route') == 'gpu_memory' and not result['stop_reasons']:
        # Route (ii) needs the CPU control: same request with -ngl 0, at least min_speedup x slower.
        control = lsi.LlamaServerInstance(probe_dir, args.binary, model_path=args.model, alias=args.alias,
                                          port=args.port, n_gpu_layers=0, ctx_size=args.ctx, gpu_uuid=args.gpu,
                                          label='ENGINEERING_ONLY probe CPU control', start_timeout=args.start_timeout,
                                          generation=1)
        if server_options:
            control = lsi.LlamaServerInstance(probe_dir, args.binary, model_path=args.model, alias=args.alias,
                                             port=args.port, n_gpu_layers=0, ctx_size=args.ctx, gpu_uuid=args.gpu,
                                             label='ENGINEERING_ONLY probe CPU control', start_timeout=args.start_timeout,
                                             generation=1, **server_options)
        info = {'argv_ngl': '0', 'log': str(control.log_path)}
        result['cpu_control'] = info
        cpu_recorder=None
        try:
            control.start(build=result['build'], model_sha256=result['model_sha256'],preserve_on_failure=args.exam_stage_a)
            target=control
            if args.exam_stage_a:
                journal=probe_dir/'d3_qualification_cpu.jsonl'
                cpu_recorder,identity=qualification_recorder(control,args,journal)
                info['identity']=identity;info['journal']=str(journal);target=cpu_recorder
            info['generation'] = generation(target, args.gen_tokens,exam_stage_a=args.exam_stage_a)
            if args.exam_stage_a:
                gpu_tps=(result.get('gpu_generation') or {}).get('tokens_per_second')
                cpu_tps=(info.get('generation') or {}).get('tokens_per_second')
                info['speedup']=round(gpu_tps/cpu_tps,3) if gpu_tps and cpu_tps else None
                info['passed']=info['speedup'] is not None and info['speedup']>=args.min_speedup
                if not info['passed']:
                    info['error']='Stage A CPU control speedup missing or below threshold'
        except Exception as exc:  # noqa: BLE001
            info['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            if cpu_recorder is not None: cpu_recorder.close()
            if control.process is not None and not (args.exam_stage_a and 'error' in info):
                info['server_stop'] = {k: control.stop().get(k) for k in ('stopped_utc', 'returncode', 'killed')}
            elif args.exam_stage_a and 'error' in info:
                info['server_preserved_on_stop']=control.process is not None
        if args.exam_stage_a and 'error' in info:
            stop('Stage A CPU control failed; process preserved');result['verdict']='STOP';save();return 1
        gpu_tps = (result.get('gpu_generation') or {}).get('tokens_per_second')
        cpu_tps = (info.get('generation') or {}).get('tokens_per_second')
        info['speedup'] = round(gpu_tps / cpu_tps, 3) if gpu_tps and cpu_tps else None
        info['passed'] = info['speedup'] is not None and info['speedup'] >= args.min_speedup
        save()
        if not info['passed']:
            stop(f'route (ii): CPU control speedup {info["speedup"]} < {args.min_speedup} '
                 f'(GPU {gpu_tps} tok/s, CPU {cpu_tps} tok/s; {info.get("error", "")})')
    if offload['full'] and not result['stop_reasons']:
        result['route'] = offload['route']
    pins = {'build': args.expect_build in (None, result['build']['version_line']),
            'model_sha256': args.expect_sha256 in (None, result['model_sha256'])}
    result['pins_match'] = pins
    for name, ok in pins.items():
        if not ok:
            stop(f'{name} differs from the expected pin')
    result['verdict'] = 'FULL_GPU_OFFLOAD' if not result['stop_reasons'] and result['route'] else 'STOP'
    if result['verdict'] == 'STOP':
        result['route'] = None
    say(f'route {result["route"]}; offload line {offload.get("line")}; server MiB on card '
        f'{result["footprint_mib_to_pin"]}; CPU control {result["cpu_control"] and result["cpu_control"].get("speedup")}; '
        f'VERDICT {result["verdict"]}; footprint_mib to pin: {result["footprint_mib_to_pin"]}; record {path}')
    return 0 if result['verdict'] == 'FULL_GPU_OFFLOAD' else 1


if __name__ == '__main__':
    raise SystemExit(main())
