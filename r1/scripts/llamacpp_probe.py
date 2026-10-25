"""One-token GPU load probe of a GGUF on llama.cpp's ``llama-server`` (RUNBOOK A.11; A.10 handoff).

Run on the sweep host from the paper checkout, before any sweep config is
filled in.  It uses the runner's own code (``r1/scripts/llama_server_instance.py``),
so it checks exactly what the runner will check at launch:

1. ``llama-server --version`` (the ``version: <n> (<commit>)`` line = ``llamacpp.build``);
2. the GGUF's sha256 (= ``llamacpp.model_sha256``);
3. a dedicated server on one card (``CUDA_VISIBLE_DEVICES``), ``-ngl``/``-c``
   as in the config, ``/health`` ready, ``/v1/models`` serving the alias,
   ``/props`` reporting the GGUF path;
4. one completion of one token (``max_tokens`` 1, ``seed`` 0);
5. the server log: every layer offloaded to the GPU, a CUDA model buffer, no
   CPU-fallback line; the server's GPU memory from ``nvidia-smi``
   (= ``llamacpp.footprint_mib``);
6. the server is stopped (only its own process group).

Everything goes under ``--out``: ``probe_<UTC>.json`` (the verdict and all
values), ``probe_<UTC>/llama_server_<port>.log`` (the server's own log) and
``.json`` (its record).  Exit 0 only for full GPU offload (and matching pins,
when ``--expect-*`` are given); 1 otherwise; 2 for a usage error.  Starts
nothing else, never touches another process.  Standard library only.

    python3 -m r1.scripts.llamacpp_probe --binary /path/llama-server --model /path/model-Q4_K_M.gguf \\
        --gpu GPU-xxxxxxxx --port 18481 --out /path/to/logs

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from r1.scripts import llama_server_instance as lsi  # noqa: E402
from r1.scripts.ollama_instance import port_is_free  # noqa: E402


def _nvidia(args: list[str]) -> str | None:
    try:
        return subprocess.run(['nvidia-smi', *args], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f'nvidia-smi failed: {exc!r}'


def server_gpu_mib(pid: int) -> int | None:
    """GPU memory (MiB) of the server process, from ``nvidia-smi --query-compute-apps``; None if not listed."""
    out = _nvidia(['--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits']) or ''
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 2 and parts[0] == str(pid) and parts[1].isdigit():
            return int(parts[1])
    return None


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
    ap.add_argument('--expect-sha256', default=None)
    ap.add_argument('--expect-build', default=None, help='the exact "version: <n> (<commit>)" line')
    ap.add_argument('--out', required=True, help='log directory (created)')
    args = ap.parse_args(argv)
    if not Path(args.model).is_absolute() or not Path(args.binary).is_absolute():
        ap.error('--binary and --model must be absolute paths (they are pinned as given)')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    result: dict = {'schema': 'r1.llamacpp_probe/1', 'label': 'ENGINEERING_ONLY', 'ai_assisted': 'AI-assisted (Claude)',
                    'utc': stamp, 'host': platform.node(), 'args': vars(args)}
    path = out / f'probe_{stamp}.json'

    def save():
        path.write_text(json.dumps(result, indent=2, default=str) + '\n')

    def say(message):
        print(message, flush=True)
        result.setdefault('log', []).append(message)
        save()

    if not port_is_free(args.port):
        result['verdict'] = 'refused: port in use'
        say(f'REFUSED: port {args.port} is in use')
        return 1
    result['build'] = lsi.build_info(args.binary)
    say(f'build: {result["build"]["version_line"]}')
    started = time.monotonic()
    result['model_sha256'] = lsi.sha256_file(args.model)
    result['sha256_seconds'] = round(time.monotonic() - started, 1)
    say(f'sha256: {result["model_sha256"]} ({result["sha256_seconds"]} s)')
    result['gpus_before'] = _nvidia(['--query-gpu=index,uuid,name,memory.used,memory.total,driver_version,compute_cap',
                                     '--format=csv'])
    inst = lsi.LlamaServerInstance(out / f'probe_{stamp}', args.binary, model_path=args.model, alias=args.alias,
                                   port=args.port, n_gpu_layers=args.ngl, ctx_size=args.ctx, gpu_uuid=args.gpu,
                                   label='ENGINEERING_ONLY probe', start_timeout=args.start_timeout)
    try:
        try:
            result['server'] = inst.start(build=result['build'], model_sha256=result['model_sha256'])
            say(f'server healthy: pid {inst.record["pid"]}, log {inst.log_path}')
            result['served_models'] = inst.model_ids()
            props = inst.props() or {}
            result['props'] = {k: props.get(k) for k in ('model_path', 'total_slots', 'build_info')}
            started = time.monotonic()
            reply = inst.chat('Reply OK', max_tokens=1, seed=0)
            result['probe'] = {'seconds': round(time.monotonic() - started, 2), 'usage': reply.get('usage'),
                               'content': reply['choices'][0]['message'].get('content')}
            result['server_gpu_mib'] = server_gpu_mib(inst.record['pid'])
            result['gpus_loaded'] = _nvidia(['--query-gpu=index,uuid,memory.used,memory.total', '--format=csv'])
        except Exception as exc:  # noqa: BLE001 - recorded; the verdict below is then not full offload
            result['error'] = f'{type(exc).__name__}: {exc}'
            say(f'ERROR: {result["error"]}')
        result['offload'] = inst.offload()
    finally:
        result['server_stop'] = {k: inst.stop().get(k) for k in ('stopped_utc', 'returncode', 'killed')} \
            if inst.process is not None else None
        result['server_log'] = str(inst.log_path)
    pins = {'build': args.expect_build in (None, result['build']['version_line']),
            'model_sha256': args.expect_sha256 in (None, result['model_sha256'])}
    full = bool(result['offload']['full']) and args.alias in (result.get('served_models') or []) \
        and 'error' not in result
    result['pins_match'] = pins
    result['verdict'] = 'FULL_GPU_OFFLOAD' if full and all(pins.values()) else 'NOT_ACCEPTED'
    say(f'offload: {result["offload"]["offloaded_layers"]}/{result["offload"]["total_layers"]} layers; '
        f'reasons {result["offload"]["reasons"]}; server GPU MiB {result.get("server_gpu_mib")}; '
        f'pins {pins}; VERDICT {result["verdict"]}; record {path}')
    return 0 if result['verdict'] == 'FULL_GPU_OFFLOAD' else 1


if __name__ == '__main__':
    raise SystemExit(main())
