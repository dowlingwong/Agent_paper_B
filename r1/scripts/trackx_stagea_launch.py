#!/usr/bin/env python3
"""Build the pinned guardian manifest for ONE new Track X Stage A attempt.

This tool never acquires the GPU lock, never starts a server and never contacts a
model. It only binds the exact reviewed files, a complete explicit environment
and the runner argv into a manifest that the reviewed lease guardian validates
and launches. It refuses an existing output or evidence directory (no resume),
refuses a dirty or mis-pinned checkout, and refuses unresolved configuration.

The lock is acquired by the guardian; the runner re-verifies the inherited
descriptor. Same-UID non-interference is the author's assumption
(R1-EXAM-COOPERATIVE-UID); host-global single-server is NOT_CHECKABLE.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class LaunchStop(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def absolute_new(path: str, what: str) -> Path:
    if not isinstance(path, str) or not path.startswith('/') or '\x00' in path:
        raise LaunchStop(f'STOP: {what} must be an absolute path')
    resolved = Path(path)
    if os.path.lexists(resolved):
        raise LaunchStop(f'STOP: {what} already exists; never resume an existing attempt')
    if not resolved.parent.is_dir():
        raise LaunchStop(f'STOP: {what} parent does not exist')
    return resolved


def existing_regular(path: str, what: str) -> Path:
    if not isinstance(path, str) or not path.startswith('/'):
        raise LaunchStop(f'STOP: {what} must be an absolute path')
    target = Path(path)
    try:
        st = os.lstat(target)
    except OSError as exc:
        raise LaunchStop(f'STOP: {what} is unavailable') from exc
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise LaunchStop(f'STOP: {what} must be a stable regular file')
    return target


def git(repo: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def pinned_files(repo: Path, config: Path, prompts: Path, extra: list[Path]) -> list[dict]:
    files = sorted((repo / 'r1').rglob('*.py')) + sorted((repo / 'r1').rglob('*.yaml'))
    files += [config, prompts, repo / 'r1/scripts/trackx_lease_guardian.py', *extra]
    rows, seen = [], set()
    for path in files:
        resolved = path.resolve(strict=True)
        if resolved in seen:
            continue
        seen.add(resolved)
        rows.append({'path': str(resolved), 'sha256': sha256_file(resolved)})
    if len(rows) < 2:
        raise LaunchStop('STOP: too few pinned files')
    return rows


def environment(repo: Path, cfg: dict, server_binary: Path) -> dict:
    return {
        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'HOME': '/home/dowling',
        'USER': 'dowling',
        'LOGNAME': 'dowling',
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
        'PYTHONPATH': str(repo),
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONUNBUFFERED': '1',
        'OMP_NUM_THREADS': '1',
        'OPENBLAS_NUM_THREADS': '1',
        'MKL_NUM_THREADS': '1',
        'HF_HOME': str(Path(cfg['work_dir']) / 'hf'),
        'AR_HARNESS_ROOT': str(Path(cfg['work_dir']) / 'autoresearch_harness'),
        'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1',
        'HF_HUB_DISABLE_XET': '1',
        'LD_LIBRARY_PATH': str(server_binary.parent),
        'TMPDIR': cfg['work_dir'],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default=str(REPO))
    parser.add_argument('--lock', default='/home/dowling/r1_locks/gpu0.lock')
    parser.add_argument('--config')
    parser.add_argument('--python')
    parser.add_argument('--runner', help='python file the guardian must launch (default: exam_runner.py)')
    parser.add_argument('--runner-arg', action='append', default=[],
                        help='extra argv entry passed to --runner (repeatable; preflight fixture only)')
    parser.add_argument('--evidence-dir', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--expect-commit')
    parser.add_argument('--print-only', action='store_true', help='run every check, write no manifest')
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve(strict=True)
    sys.path.insert(0, str(repo))
    from r1.exam.runtime import load_config, placeholders, read_registry
    from r1.exam.cache_runtime import COOPERATIVE_POLICY
    from r1.scripts.llama_server_instance import build_info

    config = Path(args.config or repo / 'r1/scripts/configs/exam_portal.json').resolve(strict=True)
    cfg = load_config(config)
    lock = existing_regular(args.lock, 'GPU lock')
    evidence = absolute_new(args.evidence_dir, 'evidence directory')
    out = absolute_new(args.out, 'output directory')
    python = Path(args.python).resolve(strict=True)
    if not python.is_file():
        raise LaunchStop('STOP: interpreter is not a file')

    if placeholders({k: cfg[k] for k in ('prompts', 'prompts_sha256')}):
        raise LaunchStop('STOP: Stage A prompt configuration is unresolved')
    if cfg.get('cache_prompt') is not False or cfg.get('d3_policy') != COOPERATIVE_POLICY:
        raise LaunchStop('STOP: cooperative D3 policy / explicit false not configured')
    if not Path(out).is_relative_to(Path(cfg['work_dir'])) or not Path(evidence).is_relative_to(Path(cfg['work_dir'])):
        raise LaunchStop('STOP: output and evidence must be under the approved work directory')
    if not Path(cfg['prompts']).is_relative_to(Path(cfg['work_dir']).parent):
        raise LaunchStop('STOP: frozen prompt bundle must be under the approved exam-x root')

    head = git(repo, 'rev-parse', 'HEAD')
    if args.expect_commit and head != args.expect_commit:
        raise LaunchStop('STOP: checkout does not match the expected commit')
    if git(repo, 'status', '--porcelain'):
        raise LaunchStop('STOP: checkout is dirty; the reviewed bytes must be the committed bytes')
    if cfg['paper_commit'] != head:
        raise LaunchStop('STOP: config paper_commit does not equal the checked-out commit; bind it first')

    prompts = Path(cfg['prompts']).resolve(strict=True)
    if sha256_file(prompts) != cfg['prompts_sha256']:
        raise LaunchStop('STOP: frozen prompt-set digest mismatch')
    from r1.exam.stage_a import load_prompts
    load_prompts(str(prompts), cfg['prompts_sha256'], historical_seeds=True)

    binary = Path(cfg['server']['binary']).resolve(strict=True)
    if sha256_file(binary) != cfg['server']['binary_sha256']:
        raise LaunchStop('STOP: llama-server binary digest mismatch')
    info = build_info(str(binary))
    if info.get('version_line') != cfg['server']['build']:
        raise LaunchStop('STOP: llama-server build line mismatch')

    registry = repo / cfg['registry']
    read_registry(registry)
    for key in ('rule', 'value_grids'):
        if not (repo / cfg[key]).is_file():
            raise LaunchStop(f'STOP: missing pinned {key}')
    for spec in read_registry(registry)['candidates'] + read_registry(registry).get('sensitivities', []):
        model = Path(spec['runtime']['model_path'])
        if not model.is_file() or model.stat().st_size != spec['quant_source']['size_bytes']:
            raise LaunchStop(f'STOP: model file/size mismatch for {spec["id"]}')

    runner = Path(args.runner) if args.runner else repo / 'r1/scripts/exam_runner.py'
    runner = runner.resolve(strict=True)
    if runner.suffix != '.py' or not runner.is_relative_to(repo):
        raise LaunchStop('STOP: runner must be a python file inside the reviewed repository')
    argv = [str(python), str(runner)]
    if args.runner_arg:
        argv += list(args.runner_arg)
    else:
        argv += ['stage-a', '--config', str(config), '--out', str(out)]
    manifest = {
        'version': 'trackx_guardian_manifest/v1',
        'argv': argv,
        'files': pinned_files(repo, config, prompts, [lock]),
        'environment': environment(repo, cfg, binary),
    }
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    digest = hashlib.sha256(raw).hexdigest()
    manifest_path = Path(str(evidence) + '.manifest.json')
    if os.path.lexists(manifest_path):
        raise LaunchStop('STOP: manifest path already exists')
    if not args.print_only:
        fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    guardian = repo / 'r1/scripts/trackx_lease_guardian.py'
    print(json.dumps({
        'manifest': str(manifest_path),
        'manifest_sha256': digest,
        'written': not args.print_only,
        'run_from_working_directory': str(repo),
        'guardian_command': [str(python), str(guardian), '--lock', str(lock),
                             '--manifest', str(manifest_path), '--manifest-sha256', digest,
                             '--evidence-dir', str(evidence),
                             '--expected-runner', str(runner)],
        'pinned_file_count': len(manifest['files']),
        'scope': ('cooperative same-UID flock; same-UID non-interference assumed by the author, '
                  'host-global single-server NOT_CHECKABLE'),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
