"""Desktop DRYRUN of the C3 label sweep: real launcher and runner, fake Ollama, real CPU workers.

Modelled on ``rerun2_dryrun.py``.  Everything lives in a marked temporary
directory: a source fixture of this checkout (HEAD plus the working-tree
``r1/``), temporary bare remotes for the paper and the harness, fresh clones
made by the real launcher (``--prepare``; test suites skipped, they run
separately), an isolated tmux socket, fake ``nvidia-smi`` / ``ps`` / ``ollama``
on PATH and the fake model server ``c3_fake_ollama.py``.  Refused on Ada.

Scenarios (fault injection over /api/chat calls of the batch's own server):

* ``retry`` - the server cuts one request off mid-way; the harness's bounded
  transport retry must resend it with the same D26 seed and the batch must
  complete (every phase committed and pushed to the bare remote);
* ``permanent`` - the server process exits mid-request and stays down; the
  failed roots must persist traceback, error class, UTC time and the attempt
  log, and the runner must stop cleanly (STOP recorded, collection files
  written, the dedicated server gone, tmux session ended).

Only ``summary.json`` and copied logs leave the temporary directory (``--out``).
AI-assisted (Claude).  DRYRUN; never evidence.
"""
import argparse
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FAULTS = {
    # Liveness makes about 8 chat calls (2 nodes x 1 instance x W=4); call 14 falls in the first sweep.
    'retry': [{'chat_call': 14, 'mode': 'drop'}],
    'permanent': [{'chat_call': 14, 'mode': 'exit'}],
}


def run(args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT)


def executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def build_fixture(root: Path, harness_source: Path) -> dict:
    source = root / 'source'
    for attempt in range(3):
        # The source repository is shared with other sessions; a concurrent ref
        # or pack lock can make one clone fail transiently.
        done = subprocess.run(['git', 'clone', '-q', '--no-checkout', str(REPO), str(source)],
                              capture_output=True, text=True)
        if done.returncode == 0:
            break
        shutil.rmtree(source, ignore_errors=True)
        time.sleep(2)
    else:
        raise RuntimeError(f'STOP: fixture clone failed: {done.stderr.strip()[-500:]}')
    archive = subprocess.check_output(['git', 'archive', 'HEAD'], cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter='data')
    shutil.copytree(REPO / 'r1', source / 'r1', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    pin = (source / 'r1/scripts/HARNESS_PIN_C3').read_text().strip()
    for key, value in [('user.name', 'DRYRUN fixture'), ('user.email', 'fixture@example.invalid')]:
        run(['git', 'config', key, value], cwd=source)
    run(['git', 'add', '-f', '.'], cwd=source)
    run(['git', 'commit', '-q', '--allow-empty', '-m', 'DRYRUN source fixture'], cwd=source)
    paper_remote, harness_remote = root / 'paper.git', root / 'harness.git'
    run(['git', 'clone', '--bare', '-q', str(source), str(paper_remote)])
    run(['git', 'update-ref', 'refs/heads/main', run(['git', 'rev-parse', 'HEAD'], cwd=source).strip()],
        cwd=paper_remote)
    run(['git', 'symbolic-ref', 'HEAD', 'refs/heads/main'], cwd=paper_remote)
    run(['git', 'clone', '--bare', '-q', str(harness_source), str(harness_remote)])
    run(['git', 'cat-file', '-e', pin + '^{commit}'], cwd=harness_remote)
    run(['git', 'update-ref', 'refs/heads/r1', pin], cwd=harness_remote)
    run(['git', 'symbolic-ref', 'HEAD', 'refs/heads/r1'], cwd=harness_remote)
    return {'source': source, 'paper_remote': paper_remote, 'harness_remote': harness_remote, 'pin': pin}


def fake_bin(root: Path, socket_name: str) -> Path:
    bin_dir = root / 'bin'
    bin_dir.mkdir()
    real_tmux = shutil.which('tmux')
    if not real_tmux:
        raise RuntimeError('STOP: desktop dry run requires tmux')
    executable(bin_dir / 'tmux', f'#!/bin/sh\nexec {real_tmux} -L {socket_name} "$@"\n')
    executable(bin_dir / 'nvidia-smi', '''#!/bin/sh
case "$*" in
  *"--query-gpu"*) echo '0, GPU-DRYRUN, DRYRUN shared card, 40000';;
  *"-x"*) echo '<nvidia_smi_log><gpu><uuid>GPU-DRYRUN</uuid><processes><process_info><pid>99999999</pid><used_memory>100 MiB</used_memory></process_info></processes></gpu></nvidia_smi_log>';;
  *) echo 'DRYRUN GPU census';;
esac
''')
    executable(bin_dir / 'ps', '#!/bin/sh\necho dryrun_co_tenant\n')
    executable(bin_dir / 'ollama', f'#!/bin/sh\nexec {sys.executable} {REPO / "r1/scripts/c3_fake_ollama.py"} "$@"\n')
    executable(bin_dir / 'paper_a_status', '#!/bin/sh\necho \'{"paper_a_live_waiting_for_card": false, '
               '"source": "DRYRUN fixture"}\'\n')
    return bin_dir


def data_cache(rel: Path, sources) -> Path | None:
    """First existing copy of an ignored OpenML cache among the candidate harness checkouts (read only)."""
    for source in sources:
        if (Path(source) / rel).is_dir():
            return Path(source) / rel
    return None


def run_scenario(scenario: str, root: Path, fixture: dict, bin_dir: Path, data_sources,
                 python: str, deadline_s: float) -> dict:
    batches = root / f'batches_{scenario}'
    batches.mkdir()
    config = {'nodes': ['digits_mlp', 'openml_breast_w'], 'instances': 2, 'runs': 6, 'workers': 2,
              'liveness': {'instances': 1, 'runs': 4}, 'min_live_nodes': 2, 'gpu_wait_seconds': 0,
              'max_collect_sessions': 3,
              'paper_a_check': {'command': [str(bin_dir / 'paper_a_status')]},
              'ollama': {'binary': str(bin_dir / 'ollama'), 'start_timeout': 30}}
    config_path = root / f'c3_config_{scenario}.json'
    config_path.write_text(json.dumps(config, indent=2))
    env = {k: v for k, v in os.environ.items()
           if k not in ('R1_BATCH_DIRECTORY', 'R1_PAPER_ROOT', 'AR_HARNESS_ROOT', 'R1_LIVENESS_MANIFEST',
                        'PYTHONPATH', 'C3_FAKE_FAULTS')}
    env.update(R1_DRYRUN='1', R1_DRYRUN_ROOT=str(root), R1_DRYRUN_CHILD='1', R1_FAKE_OLLAMA_ROOT=str(root),
               R1_GIT_NAME='DRYRUN fixture', R1_GIT_EMAIL='fixture@example.invalid',
               R1_C3_BATCH_ROOT=str(batches), R1_C3_PAPER_REMOTE=str(fixture['paper_remote']),
               R1_C3_HARNESS_REMOTE=str(fixture['harness_remote']), R1_C3_VENV_PYTHON=python,
               R1_C3_SKIP_SUITES='1', R1_C3_CONFIG=str(config_path), C3_FAKE_FAULTS=json.dumps(FAULTS[scenario]),
               R1_COAUTHOR='Claude (AI-assisted DRYRUN) <noreply@anthropic.com>',
               PATH=str(bin_dir) + os.pathsep + os.environ['PATH'], PYTHONPATH=str(fixture['source']),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    launcher = fixture['source'] / 'r1/scripts/c3_label_sweep_launch.sh'
    prepare = run(['bash', str(launcher), '--prepare'], cwd=fixture['source'], env=env)
    batch = Path(next(l.split('Batch:')[1].strip() for l in prepare.splitlines() if l.startswith('PREPARED. Batch:')))
    # Existing local OpenML caches (ignored by git, absent from fresh clones); no harness code change.
    for node in config['nodes']:
        rel = Path(f'experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache')
        found = data_cache(rel, data_sources)
        if found is not None:
            shutil.copytree(found, batch / 'autoresearch_harness' / rel)
    launch = run(['bash', str(launcher), '--start', str(batch)], cwd=fixture['source'], env=env)
    deadline = time.monotonic() + deadline_s
    state = {}
    while time.monotonic() < deadline:
        state_file = batch / 'batch_state.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except json.JSONDecodeError:
                state = {}
            if state.get('finished_utc') and (batch / 'c3_sweep_summary.json').exists():
                if subprocess.run(['tmux', 'has-session', '-t', 'r1_c3_sweep'], env=env,
                                  capture_output=True).returncode:
                    break
        time.sleep(1)
    timed_out = time.monotonic() >= deadline
    calls = [json.loads(l) for l in (root / 'fake_calls.jsonl').read_text().splitlines()] \
        if (root / 'fake_calls.jsonl').exists() else []
    return {'batch': batch, 'state': state, 'calls': calls, 'env': env, 'timed_out': timed_out,
            'deadline_s': deadline_s}


def check_retry(result: dict) -> dict:
    assert not result['timed_out'], f"scenario exceeded {result['deadline_s']} s"
    state, batch = result['state'], result['batch']
    assert state['stop_reason'] is None, state['stop_reason']
    for step in ('preconditions', 'liveness', 'sweep_append_only_summary', 'sweep_none', 'index'):
        assert state['steps'][step]['completed'], step
    paper_remote = Path(result['env']['R1_C3_PAPER_REMOTE'])
    for step in ('liveness', 'sweep_append_only_summary', 'sweep_none', 'index'):
        run(['git', 'cat-file', '-e', state['steps'][step]['commit'] + '^{commit}'], cwd=paper_remote)
    chats = [c for c in result['calls'] if c.get('path') == '/api/chat']
    dropped = [c for c in chats if c.get('fault') == 'drop']
    assert len(dropped) == 1, dropped
    resent = [c for c in chats if c['chat_call'] > dropped[0]['chat_call'] and c['seed'] == dropped[0]['seed']]
    assert resent, 'the dropped request was not resent with the same seed'
    retried = sum(state['steps'][s]['checks']['llm_calls_retried'] for s in ('sweep_append_only_summary', 'sweep_none'))
    assert retried == 1, retried
    assert all(isinstance(c['seed'], int) for c in chats)
    ollama = state['ollama']
    assert ollama.get('stopped_utc') and Path(ollama['models_dir']).is_relative_to(batch)
    index = json.loads(Path(state['steps']['index']['path']).read_text())
    assert index['audit']['status'] == 'pending' and len(index['sweeps']) == 2
    for sweep in index['sweeps']:
        manifest = json.loads((batch / 'agent_paper_B' / sweep['manifest']).read_text())
        assert manifest['roots_only'] and manifest['verify_split_policy'] == 'vary'
        assert manifest['action_versions']['verify_failed'] == 'original_stands/v1'
        assert manifest['manager']['transport_max_attempts'] == 3
    paper = batch / 'agent_paper_B'
    restart_env = dict(result['env'], R1_BATCH_DIRECTORY=str(batch), R1_PAPER_ROOT=str(paper),
                       AR_HARNESS_ROOT=str(batch / 'autoresearch_harness'),
                       PYTHONPATH=f"{batch / 'autoresearch_harness/src'}:{paper}")
    restart = subprocess.run([str(batch / 'autoresearch_harness/.venv/bin/python'), 'r1/scripts/c3_label_sweep.py'],
                             cwd=paper, capture_output=True, text=True, env=restart_env)
    assert restart.returncode == 3 and 'already finished' in restart.stdout, restart.stdout + restart.stderr
    return {'dropped_chat_call': dropped[0]['chat_call'], 'resent_with_same_seed': True,
            'llm_calls_retried': retried, 'restart_refused': True, 'eligible_nodes':
            state['steps']['liveness']['eligible_nodes'],
            'roots': {s: state['steps'][s]['checks']['roots'] for s in ('sweep_append_only_summary', 'sweep_none')},
            'commits': {s: v.get('commit') for s, v in state['steps'].items() if v.get('commit')}}


def check_permanent(result: dict) -> dict:
    assert not result['timed_out'], f"scenario exceeded {result['deadline_s']} s"
    state = result['state']
    reason = state['stop_reason'] or ''
    assert 'root campaign failures' in reason, reason
    step = state['steps']['sweep_append_only_summary']
    assert not step['completed']
    out = Path(step['out'])
    failures = [json.loads(p.read_text()) for p in sorted((out / 'failures').glob('root__*.json'))]
    assert failures
    for item in failures:
        assert item['traceback'].startswith('Traceback') and item['error_class'] and item['failed_utc']
        datetime.strptime(item['failed_utc'], '%Y-%m-%dT%H:%M:%S.%fZ')
    with_attempts = [f for f in failures if f.get('transport_attempts')]
    assert with_attempts and all(len(f['transport_attempts']) == 3 for f in with_attempts)
    assert (out / 'collection_failures.json').exists() and (out / 'collection_checks.json').exists()
    ollama = state['ollama']
    assert ollama.get('stopped_utc') is not None
    alive = subprocess.run(['kill', '-0', str(ollama['pid'])], capture_output=True).returncode == 0
    assert not alive, 'dedicated fake server still running'
    exits = [c for c in result['calls'] if c.get('fault') == 'exit']
    assert len(exits) == 1
    return {'stop_reason': reason, 'failed_roots': len(failures),
            'failure_classes': sorted({f['error_class'] for f in failures}),
            'attempt_classes': sorted({a['error_class'] for f in with_attempts for a in f['transport_attempts']}),
            'server_exit_chat_call': exits[0]['chat_call']}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', choices=['retry', 'permanent', 'both'], default='both')
    ap.add_argument('--out', type=Path, default=None)
    ap.add_argument('--python', default=sys.executable, help='interpreter with the harness dependencies')
    ap.add_argument('--deadline', type=float, default=150.0, help='seconds per scenario run')
    ap.add_argument('--keep', action='store_true', help='keep the temporary directories for inspection')
    args = ap.parse_args()
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: desktop DRYRUN is forbidden on Ada')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = args.out or REPO / 'results/r1/engineering' / f'c3_sweep_dryrun_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    harness_source = Path(os.environ.get('AR_HARNESS_ROOT', str(REPO.parent / 'autoresearch_harness'))).resolve()
    data_sources = [Path(p) for p in (os.environ.get('R1_DRYRUN_DATA_HARNESS'), harness_source,
                                      REPO.parent / 'autoresearch_harness', REPO.parents[2] / 'autoresearch_harness')
                    if p]
    scenarios = ['retry', 'permanent'] if args.scenario == 'both' else [args.scenario]
    summary = {'label': 'DRYRUN', 'scenarios': {}, 'started_utc': stamp, 'harness_source': str(harness_source)}
    start = time.monotonic()
    for scenario in scenarios:
        root = Path(tempfile.mkdtemp(prefix=f'r1_c3_dryrun_{scenario}_')).resolve()
        (root / '.dryrun').write_text('DRYRUN\n')
        socket_name = 'r1c3dry_' + root.name
        entry = {'temporary_root': str(root)}
        result = None
        try:
            fixture = build_fixture(root, harness_source)
            entry['pin'] = fixture['pin']
            bin_dir = fake_bin(root, socket_name)
            result = run_scenario(scenario, root, fixture, bin_dir, data_sources, args.python, args.deadline)
            entry['checks'] = (check_retry if scenario == 'retry' else check_permanent)(result)
            entry['passed'] = True
        except Exception as exc:
            entry['passed'] = False
            entry['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            if result:
                entry['stop_reason'] = result['state'].get('stop_reason')
                entry['batch'] = str(result['batch'])
                target = out / scenario
                target.mkdir()
                for path in sorted(result['batch'].glob('*.log')) + sorted(result['batch'].glob('*.json*')):
                    shutil.copy2(path, target / path.name)
                if (root / 'fake_calls.jsonl').exists():
                    shutil.copy2(root / 'fake_calls.jsonl', target / 'fake_calls.jsonl')
            subprocess.run([shutil.which('tmux') or 'tmux', '-L', socket_name, 'kill-server'], capture_output=True)
            if not args.keep:
                shutil.rmtree(root, ignore_errors=True)  # ~250 MB per scenario
                entry['temporary_root_removed'] = True
        summary['scenarios'][scenario] = entry
    summary['elapsed_seconds'] = round(time.monotonic() - start, 1)
    summary['completed'] = all(e.get('passed') for e in summary['scenarios'].values())
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, default=str) + '\n')
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
