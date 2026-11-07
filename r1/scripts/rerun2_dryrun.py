"""Run the real rerun-2 entrypoint/launcher on CPU against isolated fake services.

AI-assisted. All generated repositories and pushes remain in a marked temporary
directory; only the DRYRUN summary and logs are exported to the paper repository.
"""
import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]


def run(args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT)


def commit_source_fixture(source):
    """Record the extracted fixture tree, even when it matches its parent."""
    run(['git', 'add', '-f', '.'], cwd=source)
    run(['git', 'commit', '--allow-empty', '-qm', 'DRYRUN source fixture'], cwd=source)


def executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before-fixes', action='store_true')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: desktop DRYRUN is forbidden on Ada')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = args.out or REPO / 'results/r1/engineering' / f'rerun2_dryrun_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='r1_rerun2_dryrun_')).resolve()
    (root / '.dryrun').write_text('DRYRUN\n')
    harness_source = Path(os.environ.get('AR_HARNESS_ROOT', str(REPO.parent / 'autoresearch_harness'))).resolve()
    pin = (REPO / 'r1/scripts/HARNESS_PIN_RERUN2').read_text().strip()
    source = root / 'source'
    run(['git', 'clone', '-q', '--no-checkout', str(REPO), str(source)])
    archive = subprocess.check_output(['git', 'archive', '69b2bbd' if args.before_fixes else 'HEAD'], cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter='data')
    if not args.before_fixes:
        shutil.copytree(REPO / 'r1', source / 'r1', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    for key, value in [('user.name', 'DRYRUN fixture'), ('user.email', 'fixture@example.invalid')]:
        run(['git', 'config', key, value], cwd=source)
    commit_source_fixture(source)
    paper_remote, harness_remote = root / 'paper.git', root / 'harness.git'
    run(['git', 'clone', '--bare', '-q', str(source), str(paper_remote)])
    run(['git', 'clone', '--bare', '-q', str(harness_source), str(harness_remote)])
    run(['git', 'update-ref', 'refs/heads/r1', pin], cwd=harness_remote)
    run(['git', 'symbolic-ref', 'HEAD', 'refs/heads/r1'], cwd=harness_remote)
    bin_dir = root / 'bin'
    bin_dir.mkdir()
    real_tmux = shutil.which('tmux')
    if not real_tmux:
        raise RuntimeError('STOP: desktop dry run requires tmux')
    socket_name = 'r1dry_' + root.name
    executable(bin_dir / 'tmux', f'#!/bin/sh\nexec {real_tmux} -L {socket_name} "$@"\n')
    executable(bin_dir / 'nvidia-smi', '''#!/bin/sh
case "$*" in
  *"--query-gpu"*) echo '0, GPU-DRYRUN, DRYRUN shared card, 40000';;
  *"-x"*) echo '<nvidia_smi_log><gpu><uuid>GPU-DRYRUN</uuid><processes><process_info><pid>99999999</pid><used_memory>100 MiB</used_memory></process_info></processes></gpu></nvidia_smi_log>';;
  *) echo 'DRYRUN GPU census';;
esac
''')
    executable(bin_dir / 'ps', '#!/bin/sh\necho dryrun_co_tenant\n')
    executable(bin_dir / 'ollama', f'#!/bin/sh\nexec {sys.executable} {REPO / "r1/scripts/rerun2_fake_ollama.py"}\n')
    models_parent = root / 'pinned'
    (models_parent / 'ollama_models').mkdir(parents=True)
    batches = root / 'batches'
    batches.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ('R1_BATCH_DIRECTORY', 'R1_PAPER_ROOT', 'R1_LIVENESS_MANIFEST')}
    env.update(R1_DRYRUN='1', R1_DRYRUN_PORT=str(port), R1_DRYRUN_ROOT=str(root), R1_DRYRUN_CHILD='1',
               R1_GIT_NAME='DRYRUN fixture', R1_GIT_EMAIL='fixture@example.invalid',
               AR_HARNESS_ROOT=str(harness_source), R1_RERUN2_BATCH_ROOT=str(batches),
               R1_RERUN2_PINNED_BATCH=str(models_parent), R1_RERUN2_OLLAMA_BINARY=str(bin_dir / 'ollama'),
               R1_RERUN2_PAPER_REMOTE=str(paper_remote), R1_RERUN2_HARNESS_REMOTE=str(harness_remote),
               R1_EXECUTOR='Codex (AI-assisted DRYRUN)', PATH=str(bin_dir) + os.pathsep + os.environ['PATH'],
               PYTHONPATH=str(source), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    env.pop('AR_HARNESS_ROOT')  # launcher sets the fresh checkout, never the source
    start = time.monotonic()
    summary = {'label': 'DRYRUN', 'before_fixes': args.before_fixes, 'temporary_root': str(root), 'pin': pin}
    batch = None
    try:
        if args.before_fixes:
            batch = batches / 'before'
            batch.mkdir()
            paper, harness = batch / 'agent_paper_B', batch / 'autoresearch_harness'
            run(['git', 'clone', '-q', str(paper_remote), str(paper)])
            run(['git', 'clone', '-q', str(harness_remote), str(harness)])
            for repo in (paper, harness):
                run(['git', 'config', 'user.name', 'DRYRUN fixture'], cwd=repo)
                run(['git', 'config', 'user.email', 'fixture@example.invalid'], cwd=repo)
            env.update(R1_BATCH_DIRECTORY=str(batch), R1_PAPER_ROOT=str(paper), AR_HARNESS_ROOT=str(harness),
                       R1_OLLAMA_MODELS=str(models_parent / 'ollama_models'), R1_OLLAMA_BINARY=str(bin_dir / 'ollama'))
            env.pop('R1_DRYRUN')  # old runner has no mode: local fake host solely to reproduce pre-inference defect
            wrapper = "import platform,runpy,socket; from unittest.mock import MagicMock; platform.node=lambda:'ucrtasl'; socket.socket=MagicMock(); runpy.run_path('r1/scripts/ada_e1b_rerun2.py',run_name='__main__')"
            result = subprocess.run([sys.executable, '-c', wrapper], cwd=paper, env=env, capture_output=True, text=True)
            (batch / 'runner.log').write_text(result.stdout + result.stderr)
        else:
            prepare = run(['bash', str(source / 'r1/scripts/ada_e1b_rerun2_launch.sh'), '--prepare'], cwd=source, env=env)
            (out / 'prepare.log').write_text(prepare)
            batch = Path(next(line.split('Batch:')[1].strip() for line in prepare.splitlines() if line.startswith('PREPARED. Batch:')))
            payload = json.loads((batch / 'prepare.json').read_text())
            if not payload['ok']:
                raise RuntimeError('STOP: DRYRUN preparation tests failed: ' + str(payload['harness_tests']['unexpected']))
            # Use the existing local OpenML cache; no synthetic data or harness-code modification.
            cache_rel = Path('experiments/r1/pilot/L8_20261009T152916Z/nodes/openml_breast_w/data_cache')
            cache = harness_source / cache_rel
            if not cache.is_dir():
                raise RuntimeError('STOP: desktop OpenML fixture cache is missing')
            shutil.copytree(cache, batch / 'autoresearch_harness' / cache_rel)
            launch = run(['bash', str(source / 'r1/scripts/ada_e1b_rerun2_launch.sh'), '--start', str(batch)], cwd=source, env=env)
            (out / 'launch.log').write_text(launch)
            deadline = time.monotonic() + 850
            while time.monotonic() < deadline:
                state_file = batch / 'batch_state.json'
                if state_file.exists():
                    try:
                        state = json.loads(state_file.read_text())
                    except json.JSONDecodeError:
                        time.sleep(1)
                        continue
                    if state.get('finished_utc'):
                        # finish saves state before its final push; wait until session exits.
                        if subprocess.run(['tmux', 'has-session', '-t', 'r1_e1b_rerun2'], env=env, capture_output=True).returncode:
                            break
                time.sleep(1)
            else:
                raise RuntimeError('STOP: desktop DRYRUN exceeded 15-minute bound')
        state = json.loads((batch / 'batch_state.json').read_text())
        summary['state'] = state
        summary['batch'] = str(batch)
        if args.before_fixes:
            assert state['stop_reason'] == "NameError: name 'MODELS' is not defined", state
            summary['expected_failure_observed'] = True
        else:
            assert state['stop_reason'] is None, state['stop_reason']
            for phase in ('preconditions', 'liveness', 'arm_A', 'arm_B', 'arm_C', 'comparison', 'STATUS'):
                assert state['steps'][phase]['completed'], phase
                if phase != 'preconditions':
                    commit = state['steps'][phase]['commit']
                    run(['git', 'cat-file', '-e', commit + '^{commit}'], cwd=paper_remote)
            liveness = json.loads((Path(state['steps']['liveness']['out']) / 'liveness.json').read_text())
            summary['inactive_key_rejections'] = {node: data['inactive_key_rejections'] for node, data in liveness['nodes'].items()}
            assert sum(summary['inactive_key_rejections'].values()) > 0
            for arm in ('A', 'B', 'C'):
                item = state['steps']['arm_' + arm]
                assert item['committed_analysis_sha256'] == item['regenerated_analysis_sha256']
            assert run(['git', 'rev-parse', 'HEAD'], cwd=batch / 'agent_paper_B').strip() == run(['git', 'rev-parse', 'refs/heads/main'], cwd=paper_remote).strip()
            calls = [json.loads(line) for line in (root / 'fake_calls.jsonl').read_text().splitlines()]
            chats = [item for item in calls if item['path'] == '/api/chat']
            assert chats and all(isinstance(item['seed'], int) for item in chats)
            summary['seeded_fake_chat_calls'] = len(chats)
            py = batch / 'autoresearch_harness/.venv/bin/python'
            restart_env = dict(env, R1_BATCH_DIRECTORY=str(batch), R1_PAPER_ROOT=str(batch / 'agent_paper_B'), AR_HARNESS_ROOT=str(batch / 'autoresearch_harness'))
            restart = subprocess.run([str(py), 'r1/scripts/ada_e1b_rerun2.py'], cwd=batch / 'agent_paper_B', env=restart_env, capture_output=True, text=True)
            assert restart.returncode and 'already finished' in restart.stdout + restart.stderr
            summary['restart_refused'] = True
            summary['completed'] = True
            summary['fixture'] = {'nodes': 2, 'instances_per_node': 2, 'runs': 6, 'points': [2], 'repetitions': 1, 'audit_seeds': 1,
                                  'deviations': '2 instances required by unchanged cross-fitting; W=6 required by unchanged paired verify cost 2*r=4; isolated loopback port because 11434 is occupied'}
    except Exception as exc:
        summary['error'] = str(exc)
        raise
    finally:
        summary['elapsed_seconds'] = round(time.monotonic() - start, 2)
        if batch:
            for name in sorted({p.name for p in batch.glob('*.log')} | {'prepare.json', 'batch_state.json', 'gpu_census.jsonl'}):
                if (batch / name).exists():
                    shutil.copy2(batch / name, out / name)
        if (root / 'fake_calls.jsonl').exists():
            shutil.copy2(root / 'fake_calls.jsonl', out / 'fake_calls.jsonl')
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        subprocess.run([real_tmux, '-L', socket_name, 'kill-server'], capture_output=True)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
