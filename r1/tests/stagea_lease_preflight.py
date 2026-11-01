#!/usr/bin/env python3
"""PREFLIGHT FIXTURE (not production): prove the real native llama-server retains
the reviewed GPU-lease open file description.

Run only by the reviewed lease guardian under the real GPU lock. It loads the
real pinned llama-server with the smallest real GGUF at the exam context, issues
NO generation request, proves the inherited FD/OFD with the reviewed production
checks (ancestor->descendant kcmp(KCMP_FILE), /proc FD dev/ino, FD set, pid/start
ticks/ppid), stops the server, and writes the fail-closed completion evidence so
the guardian may release. It writes its own PREFLIGHT evidence directory only;
it never writes Stage A output, never touches the frozen prompt set, and never
sends a signal to a process it did not create.

Anything unobservable is a STOP. Same-UID non-interference is the author's
assumption and host-global single-server is NOT_CHECKABLE.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from r1.exam.cache_proc import process_start_ticks
from r1.exam.cache_runtime import (authorize_cooperative_stagea, verified_lease_fd,
                                   verify_server_lease_inheritance,
                                   validate_lease_inheritance_record)
from r1.exam.campaign import write_json
from r1.exam.guards import digest_file
from r1.exam.runtime import EXAM_SERVER_ARGS, load_config, read_registry, gpu_sample
from r1.scripts import llama_server_instance as lsi


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--ctx', type=int, default=32768)
    args = parser.parse_args(argv)

    evidence_dir = os.environ.get('TRACKX_LEASE_EVIDENCE_DIR')
    if not evidence_dir or not Path(evidence_dir).is_dir():
        raise RuntimeError('STOP: guardian evidence directory absent')
    if not os.environ.get('TRACKX_GPU_LEASE_FD'):
        raise RuntimeError('STOP: inherited GPU lease FD absent')
    out = Path(args.out)
    if out.exists():
        raise RuntimeError('STOP: preflight output exists; never resume')
    cfg = load_config(args.config)
    if platform.node().split('.')[0] != 'TASL-2' or cfg['host'] != 'TASL-2':
        raise RuntimeError('STOP: preflight runs on TASL-2 only')
    if not out.resolve().is_relative_to(Path(cfg['work_dir'])):
        raise RuntimeError('STOP: preflight output must be under the approved work directory')

    authorized = authorize_cooperative_stagea(cfg)
    registry = read_registry(REPO / cfg['registry'])
    spec = next(s for s in registry['candidates'] + registry['software_anchors'] + registry.get('sensitivities', [])
                if s['id'] == args.candidate)
    model = Path(spec['runtime']['model_path'])
    server = cfg['server']
    if not model.is_file() or model.stat().st_size != spec['quant_source']['size_bytes']:
        raise RuntimeError('STOP: model file/size mismatch')
    if digest_file(server['binary']) != server['binary_sha256']:
        raise RuntimeError('STOP: server binary digest mismatch')
    info = lsi.build_info(server['binary'])
    if info['version_line'] != server['build']:
        raise RuntimeError('STOP: server build mismatch')

    out.mkdir(parents=True)
    before = gpu_sample(cfg)
    apps_before = lsi.gpu_compute_apps()
    if apps_before is None or apps_before or before['free_mib'] < 1024:
        raise RuntimeError('STOP: GPU not quietly available before preflight')
    lease_fd = verified_lease_fd()
    args_list = list(EXAM_SERVER_ARGS)
    inst = lsi.LlamaServerInstance(out / 'server', server['binary'], model_path=str(model), alias=args.candidate,
                                   ctx_size=args.ctx, n_gpu_layers=999, gpu_uuid=cfg['gpu_uuid'],
                                   extra_args=args_list, start_timeout=server['start_timeout'])
    started = time.monotonic()
    record = None
    try:
        inst.start(build=info, model_sha256=spec['quant_source']['sha256'], lease_fd=lease_fd)
        inherited = verify_server_lease_inheritance(
            inst.process.pid, lease_fd, runner_pid=os.getpid(),
            started_ticks=process_start_ticks(inst.process.pid))
        validate_lease_inheritance_record(inherited)
        # Prove the served artifact identity without any generation request.
        served = inst.model_ids()
        props = inst.props() or {}
        if args.candidate not in (served or []):
            raise RuntimeError('STOP: served alias identity mismatch')
        if props.get('model_path') != str(model):
            raise RuntimeError('STOP: served GGUF path mismatch')
        # Free-but-required runtime observations the runner will rely on.
        sample = gpu_sample(cfg)
        apps = lsi.gpu_compute_apps()
        payload = {
            'label': 'PREFLIGHT', 'execution_label': 'ENGINEERING_ONLY',
            'phase': 'stage-a-lease-preflight', 'candidate': args.candidate,
            'ctx_size': args.ctx, 'model_sha256': spec['quant_source']['sha256'],
            'server_binary_sha256': server['binary_sha256'], 'server_build': info['version_line'],
            'gpu_uuid': cfg['gpu_uuid'], 'authorization': authorized,
            'lease_inheritance': inherited, 'server_process': {'pid': inst.process.pid,
                'start_ticks': inherited['server_start_ticks'],
                'ppid': inherited['server_ppid'], 'pgid': os.getpgid(inst.process.pid)},
            'gpu_before': before, 'gpu_after_load': sample, 'compute_apps_after_load': apps,
            'chat_completion_requests_issued': 0, 'generation_requests_issued': 0,
            'scope': ('real native llama-server FD retention under the real GPU flock; '
                      'no generation; same-UID non-interference is an author assumption; '
                      'host-global single-server NOT_CHECKABLE'),
            'started_monotonic_ns': time.monotonic_ns(),
        }
        write_json(out / 'preflight.json', payload)
    finally:
        record = inst.stop()
    stopped_ok = record.get('stopped_utc') and (inst.process.poll() is not None)
    after = gpu_sample(cfg)
    write_json(out / 'preflight_after.json', {
        'stopped': bool(stopped_ok), 'server_record_sha256': digest_file(inst.record_path),
        'server_record': str(inst.record_path), 'gpu_after_stop': after,
        'elapsed_seconds': time.monotonic() - started,
    })
    if not stopped_ok:
        raise RuntimeError('STOP: preflight server did not stop cleanly')
    write_json(out / 'batch_state.json', {
        'schema': 'exam_batch/v1', 'label': 'PREFLIGHT', 'execution_label': 'ENGINEERING_ONLY',
        'phase': 'stage-a-lease-preflight', 'status': 'COMPLETE',
        'servers': [{'pid': record['pid'], 'start_ticks': record['start_ticks']}],
        'scope': 'preflight only; not a Stage A attempt'})
    from r1.exam.cooperative_lease import write_completion
    completion = write_completion(
        evidence_dir, batch_state_path=str(out / 'batch_state.json'),
        servers=[{'pid': record['pid'], 'start_ticks': record['start_ticks'],
                  'stopped_utc': record['stopped_utc'],
                  'record_sha256': digest_file(inst.record_path),
                  'record_path': str(Path(inst.record_path).resolve())}],
        runner_pid=os.getpid(), runner_start_ticks=process_start_ticks(os.getpid()))
    write_json(out / 'preflight_completion_path.json', {'completion': str(completion)})
    print(json.dumps({'ok': True, 'out': str(out), 'lease_fd': lease_fd,
                      'server_pid': record['pid'], 'completion': str(completion)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
