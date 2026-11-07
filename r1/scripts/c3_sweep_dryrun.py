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
* ``interrupt`` (RUNBOOK A.5) - once the first sweep has a completed root and a
  root in progress, the runner's whole process group is SIGKILLed (runner,
  collector, workers; the dedicated server survives as an orphan, as after a
  preemption); ``--start`` is run again on the same batch.  The batch must
  finish; completed roots are kept byte for byte and never re-run, the roots in
  progress are re-run whole, the orphaned server is stopped and a new one
  started, and the interruption is logged (batch, step and runner logs, sweep
  directory, committed).
* ``watchdog`` (RUNBOOK A.8) - the watchdog is enabled and the server sends
  itself SIGTERM mid-request (the 14 Oct incident); the runner must record the
  loss (time, SIGTERM, last request), restart its dedicated server and re-run
  the affected roots whole, and the batch must finish.

``both`` runs ``retry`` and ``permanent``; ``all`` runs the four.

``--backend llamacpp`` (RUNBOOK A.10, 25 Oct; PLAN §10 R1-INFER-LLAMACPP) runs
the same scenarios on the llama.cpp path: the fake ``llama-server``
(``r1/scripts/c3_fake_llama_server.py``, OpenAI-compatible ``/v1`` endpoints,
``/health``, a full-offload log line) behind a shebang wrapper on PATH, a
fixture GGUF file whose sha256 and the fake's build line are the pins, and the
harness ``llamacpp`` provider in the collectors.  The checks also verify the
pins, the offload record, the ``llamacpp/<alias>`` manager model, the seed
policy and the request path.  ``--backend ollama`` (default) is the historical
path.

``--fake-offload silent`` (review of batch B, 25 Oct) makes the fake llama-server
log like llama.cpp v0.7.0 on deepthought at default verbosity (no ``offloaded
N/N layers`` line), so the runner must accept full offload by route (ii): the
server pid on the card with at least ``footprint_mib`` in the fake
``nvidia-smi --query-compute-apps``.  ``line`` (default) exercises route (i);
every load and post-collection check must record the expected route.

``--base-config PATH`` (e.g. ``r1/scripts/configs/c3_sweep_ada.json``) starts
from a real launch config instead of the built-in fixture config and overrides
only what a desktop DRYRUN must change: the nodes (its nodes among
``digits_mlp`` / ``openml_breast_w``), scale (2 instances, W = 6, liveness 1 x
W = 4, 2 workers), the GPU wait, the Ollama binary / port / model seeding (fake
server) and the Paper A check, which then runs the real
``r1/scripts/paper_a_status.py`` against a fake finished Paper A run (fake
checkout on ``paper-a-v4-ada``, no tmux session, no GPU process).  Everything
else (memory modes, transport retry, gates, audit seeds, pending nodes, ...)
comes from the base config, and the retry check also verifies the audit seeds
and pending nodes recorded in the sweep index.

Only ``summary.json`` and copied logs leave the temporary directory (``--out``).
AI-assisted (Claude).  DRYRUN; never evidence.
"""
import argparse
import io
import json
import os
import platform
import shutil
import signal
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
    'interrupt': [],
    'watchdog': [{'chat_call': 14, 'mode': 'sigterm'}],
}
WATCHDOG_DRYRUN = {'enabled': True, 'poll_seconds': 0.5, 'health_timeout': 2.0, 'unresponsive_checks': 2,
                   'model_checks': 2, 'max_restarts': 2}
SCENARIOS = {'both': ['retry', 'permanent'], 'all': ['retry', 'permanent', 'interrupt', 'watchdog']}


def run(args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT)


def executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def build_fixture(root: Path, harness_source: Path) -> dict:
    source = root / 'source'
    # A failed clone may leave evidence in source; keep it and do not retry.
    done = subprocess.run(['git', 'clone', '-q', '--no-checkout', str(REPO), str(source)],
                          capture_output=True, text=True)
    if done.returncode != 0:
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
  *"--query-compute-apps"*) exec @PY@ -c "import runpy; runpy.run_path('@FAKE@', run_name='fake_nvidia_smi')" "$@";;
  *"--query-gpu"*) echo '0, GPU-DRYRUN, DRYRUN shared card, 40000';;
  *"-x"*) echo '<nvidia_smi_log><gpu><uuid>GPU-DRYRUN</uuid><processes><process_info><pid>99999999</pid><used_memory>100 MiB</used_memory></process_info></processes></gpu></nvidia_smi_log>';;
  *) echo 'DRYRUN GPU census';;
esac
'''.replace('@PY@', sys.executable).replace('@FAKE@', str(REPO / 'r1/scripts/c3_fake_llama_server.py')))
    executable(bin_dir / 'ps', '#!/bin/sh\necho dryrun_co_tenant\n')
    executable(bin_dir / 'ollama', f'#!/bin/sh\nexec {sys.executable} {REPO / "r1/scripts/c3_fake_ollama.py"} "$@"\n')
    # Shebang (not a shell exec): the server's command line is <python> <bin>/llama-server <args>, so the
    # runner's orphan check sees the recorded binary and argv (RUNBOOK A.10).
    executable(bin_dir / 'llama-server', f'#!{sys.executable}\nimport runpy, sys\nsys.argv[0] = __file__\n'
               f'runpy.run_path({str(REPO / "r1/scripts/c3_fake_llama_server.py")!r}, run_name="__main__")\n')
    executable(bin_dir / 'paper_a_status', '#!/bin/sh\necho \'{"paper_a_live_waiting_for_card": false, '
               '"source": "DRYRUN fixture"}\'\n')
    return bin_dir


def data_cache(rel: Path, sources) -> Path | None:
    """First existing copy of an ignored OpenML cache among the candidate harness checkouts (read only)."""
    for source in sources:
        if (Path(source) / rel).is_dir():
            return Path(source) / rel
    return None


DRYRUN_NODES = ('digits_mlp', 'openml_breast_w')


def fake_paper_a(root: Path, bin_dir: Path) -> Path:
    """A fake *finished* Paper A run and a paper_a_status.py config pointing at it (DRYRUN only)."""
    checkout = root / 'paper_a_fake' / 'agent-checkpoint-intervention'
    run_dir = checkout / 'results/paper_a/replay_panel_v4/live_DRYRUN'
    run_dir.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', '-b', 'paper-a-v4-ada', str(checkout)], check=True)
    (run_dir / 'state.json').write_text(json.dumps({'status': 'finished', 'label': 'DRYRUN'}))
    executable(bin_dir / 'paper_a_nvidia_smi', "#!/bin/sh\necho 'No running processes found'\n")
    config = {'comment': 'DRYRUN fake Paper A (finished).', 'expected_host': platform.node().split('.')[0],
              'paper_a_checkout': str(checkout), 'expected_branch': 'paper-a-v4-ada',
              'run_dir': 'results/paper_a/replay_panel_v4/live_DRYRUN', 'state_file': 'state.json',
              'state_key': 'status', 'running_values': ['running'], 'finished_values': ['finished'],
              'waiting_values': ['waiting'], 'finished_markers': [], 'tmux_session': 'paper_a_fake_session',
              'tmux_binary': str(bin_dir / 'tmux'), 'nvidia_smi_binary': str(bin_dir / 'paper_a_nvidia_smi'),
              'ps_binary': str(bin_dir / 'ps'), 'process_patterns': ['live_DRYRUN']}
    path = root / 'paper_a_status_dryrun.json'
    path.write_text(json.dumps(config, indent=2))
    return path


FAKE_BUILD = 'version: 0 (DRYRUN)'  # what c3_fake_llama_server.py --version prints


def fake_gguf(root: Path) -> tuple[Path, str]:
    """A fixture "GGUF" (any bytes: the fake server loads nothing) and its sha256, the DRYRUN model pin."""
    path = root / 'models' / 'r1-manager-DRYRUN-Q4_K_M.gguf'
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b'GGUF' + b'DRYRUN fixture; no tensors\n' * 1000)
    return path, _sha(path)


def llamacpp_fixture(root: Path, bin_dir: Path, base: dict | None = None) -> dict:
    """The ``llamacpp`` block for the fake server; alias, -ngl and -c are kept from *base* when it sets them."""
    model, sha = fake_gguf(root)
    block = {'binary': str(bin_dir / 'llama-server'), 'model_path': str(model), 'model_sha256': sha,
             'model_alias': 'r1-manager', 'build': FAKE_BUILD, 'port': None, 'n_gpu_layers': 999,
             'ctx_size': 8192, 'footprint_mib': 5304, 'extra_args': [], 'start_timeout': 30}
    for key in ('model_alias', 'n_gpu_layers', 'ctx_size'):
        value = (base or {}).get(key)
        if value is not None and not (isinstance(value, str) and value.startswith('TODO_VERIFY')):
            block[key] = value
    return block


def dryrun_config(base: dict, root: Path, bin_dir: Path) -> tuple[dict, list]:
    """The base launch config with only the desktop-DRYRUN keys overridden (documented in the summary).

    A host draft (``TODO_VERIFY*`` values, e.g. ``c3_sweep_deepthought.json``) is accepted: every
    open value is a host value this override replaces, and none may remain afterwards.
    """
    config = json.loads(json.dumps(base))
    nodes = [n for n in base.get('nodes', []) if n in DRYRUN_NODES]
    if len(nodes) < 2:
        raise RuntimeError(f'STOP: base config needs both of {DRYRUN_NODES} for the desktop DRYRUN')
    command = list(base['paper_a_check']['command'])
    if '--config' in command:  # a real Paper A status check: point it at a fake finished Paper A run
        command[command.index('--config') + 1] = str(fake_paper_a(root, bin_dir))
    elif '--not-applicable' not in command:
        raise RuntimeError('STOP: base paper_a_check.command is neither a --config check nor --not-applicable')
    overrides = {'nodes': nodes, 'instances': 2, 'runs': 6, 'workers': 2,
                 'liveness': dict(base.get('liveness', {}), instances=1, runs=4), 'min_live_nodes': 2,
                 'gpu_wait_seconds': 0, 'max_collect_sessions': 3,
                 'paper_a_check': dict(base['paper_a_check'], command=command),
                 'ollama': {'binary': str(bin_dir / 'ollama'), 'start_timeout': 30, 'port': None,
                            'seed_models_from': None}}
    if base.get('backend') == 'llamacpp':
        overrides['llamacpp'] = llamacpp_fixture(root, bin_dir, base.get('llamacpp'))
    # Host values still open in a draft (and only those): the fake card and this desktop.
    if str(base.get('gpu_uuid')).startswith('TODO_VERIFY'):
        overrides['gpu_uuid'] = 'auto'
    if any(str(h).startswith('TODO_VERIFY') for h in base.get('allowed_hosts', [])):
        overrides['allowed_hosts'] = [platform.node().split('.')[0]]
    config.update(overrides)
    sys.path.insert(0, str(REPO))
    from r1.scripts.c3_label_sweep import placeholders
    left = placeholders(config)
    if left:
        raise RuntimeError(f'STOP: DRYRUN overrides leave open host values {left}')
    return config, sorted(overrides)


def _sha(path: Path) -> str | None:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


class Interrupter:
    """``interrupt`` scenario: SIGKILL the runner's process group mid-sweep, then ``--start`` again."""

    STEP = 'sweep_append_only_summary'

    def __init__(self, launcher: Path, cwd: Path, env: dict) -> None:
        self.launcher, self.cwd, self.env, self.info = launcher, cwd, env, {}

    def __call__(self, batch: Path, state: dict) -> None:
        if self.info:
            return
        step = state.get('steps', {}).get(self.STEP) or {}
        if not step.get('out') or step.get('completed') or not state.get('runners'):
            return
        out, work = Path(step['out']), Path(step['work'])
        if not (out / 'roots').is_dir() or not (work / 'roots').is_dir():
            return
        complete = sorted(p.stem for p in (out / 'roots').glob('*.json'))
        partial = sorted(d.name for d in (work / 'roots').iterdir() if d.name not in complete
                         and (d / 'root_trials.jsonl').exists() and (d / 'root_trials.jsonl').read_text().strip())
        if not complete or not partial:
            return
        hashes = {inst: {'root': _sha(out / 'roots' / f'{inst}.json'),
                         'ledger': _sha(work / 'roots' / inst / 'root_trials.jsonl')} for inst in complete}
        runner = int(state['runners'][-1]['pid'])
        os.killpg(os.getpgid(runner), signal.SIGKILL)  # runner, collector and its workers; not the server
        self.info = {'killed_utc': datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'), 'runner_pid': runner,
                     'completed_before_kill': complete, 'partial_at_kill': partial, 'hashes_before': hashes,
                     'ollama_before': state.get(_key(state), {}).get('pid')}
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not subprocess.run(['tmux', 'has-session', '-t', 'r1_c3_sweep'],
                                                                 env=self.env, capture_output=True).returncode:
            time.sleep(0.2)
        self.info['restart_launch'] = run(['bash', str(self.launcher), '--start', str(batch)], cwd=self.cwd,
                                          env=self.env).strip().splitlines()[-1:]


def run_scenario(scenario: str, root: Path, fixture: dict, bin_dir: Path, data_sources,
                 python: str, deadline_s: float, base_config: dict | None = None, backend: str = 'ollama',
                 fake_offload: str = 'line') -> dict:
    batches = root / f'batches_{scenario}'
    batches.mkdir()
    overridden = None
    if base_config is not None:
        config, overridden = dryrun_config(base_config, root, bin_dir)
    else:
        config = {'nodes': ['digits_mlp', 'openml_breast_w'], 'instances': 2, 'runs': 6, 'workers': 2,
                  'liveness': {'instances': 1, 'runs': 4}, 'min_live_nodes': 2, 'gpu_wait_seconds': 0,
                  'max_collect_sessions': 3,
                  'paper_a_check': {'command': [str(bin_dir / 'paper_a_status')]},
                  'ollama': {'binary': str(bin_dir / 'ollama'), 'start_timeout': 30}}
        if backend == 'llamacpp':
            config.update(backend='llamacpp', llamacpp=llamacpp_fixture(root, bin_dir))
    if scenario == 'watchdog':
        config['watchdog'] = dict(WATCHDOG_DRYRUN)
        overridden = sorted(set(overridden) | {'watchdog'}) if overridden is not None else None
    if scenario == 'permanent' and (config.get('watchdog') or {}).get('enabled'):
        # 'permanent' checks the clean STOP when the server stays down; with the watchdog on (the host
        # drafts, A.10) the one-shot exit would be recovered instead, which the 'watchdog' scenario checks.
        config['watchdog'] = dict(config['watchdog'], enabled=False)
        overridden = sorted(set(overridden) | {'watchdog'}) if overridden is not None else None
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
               R1_COAUTHOR='Claude (AI-assisted DRYRUN) <noreply@anthropic.com>', C3_FAKE_LLAMA_OFFLOAD=fake_offload,
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
    interrupter = Interrupter(launcher, fixture['source'], env) if scenario == 'interrupt' else None
    deadline = time.monotonic() + deadline_s
    state = {}
    while time.monotonic() < deadline:
        state_file = batch / 'batch_state.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except json.JSONDecodeError:
                state = {}
            if interrupter is not None:
                interrupter(batch, state)
            if state.get('finished_utc') and (batch / 'c3_sweep_summary.json').exists():
                if subprocess.run(['tmux', 'has-session', '-t', 'r1_c3_sweep'], env=env,
                                  capture_output=True).returncode:
                    break
        time.sleep(1)
    timed_out = time.monotonic() >= deadline
    calls = [json.loads(l) for l in (root / 'fake_calls.jsonl').read_text().splitlines()] \
        if (root / 'fake_calls.jsonl').exists() else []
    return {'batch': batch, 'state': state, 'calls': calls, 'env': env, 'timed_out': timed_out,
            'backend': config.get('backend', 'ollama'), 'fake_offload': fake_offload,
            'deadline_s': deadline_s, 'config': config, 'overridden': overridden,
            'interrupt': interrupter.info if interrupter is not None else None}

def table_from_sweep(result: dict) -> dict:
    """RUNBOOK A.4 end to end: the finished batch directory -> the C3 table, one command."""
    batch = result['batch']
    paper = batch / 'agent_paper_B'
    table = batch / 'c3_table_check'
    env = dict(result['env'], AR_HARNESS_ROOT=str(batch / 'autoresearch_harness'),
               PYTHONPATH=f"{batch / 'autoresearch_harness/src'}:{paper}")
    out = run([str(batch / 'autoresearch_harness/.venv/bin/python'), '-m', 'r1.c3.dataset', 'build-sweep',
               '--index', str(batch), '--out', str(table)], cwd=paper, env=env)
    summary = json.loads(out.strip().splitlines()[-1])
    build = json.loads((table / 'build.json').read_text())
    assert summary['n_proposals'] > 0 and len(summary['sources']) == 2, summary
    assert build['label'] == 'DRYRUN' and build['sweep_index']['audit']['status'] == 'pending'
    return {'n_proposals': summary['n_proposals'], 'sources': summary['sources']}


def _key(state: dict) -> str:
    """The state key of the batch's model server record (RUNBOOK A.10)."""
    return 'llama_server' if state.get('backend') == 'llamacpp' else 'ollama'


def _record_name(state: dict, port, generation: int) -> str:
    stem = 'llama_server' if state.get('backend') == 'llamacpp' else 'ollama_instance'
    return f'{stem}_{port}' + (f'_r{generation}' if generation else '') + '.json'


def check_llamacpp(result: dict) -> dict:
    """RUNBOOK A.10 checks common to every llama.cpp scenario that got past preconditions."""
    state, batch, config = result['state'], result['batch'], result['config']
    spec = config['llamacpp']
    server = state['llama_server']
    pins = state['llamacpp_pin_checks']
    assert pins and all(p['verdict'] == 'pinned' for p in pins), pins
    assert {p['model_sha256'] for p in pins} == {spec['model_sha256']}
    assert {p['build']['version_line'] for p in pins} == {spec['build']}
    assert server['model_sha256'] == spec['model_sha256'] and server['model_path'] == spec['model_path']
    assert server['argv'][0] == spec['binary'] and server['argv'][server['argv'].index('--port') + 1] == str(server['port'])
    assert server['cmdline'][1:] == server['argv'] or server['cmdline'] == server['argv'], server['cmdline']
    offload = json.loads((batch / 'gpu_offload_load_probe.json').read_text())
    assert offload['backend'] == 'llamacpp' and offload['offload']['full'], offload
    expected_route = 'gpu_memory' if result.get('fake_offload') == 'silent' else 'log_line'
    routes = state.get('offload_routes') or []
    assert routes and {r['route'] for r in routes} == {expected_route}, routes  # load and every collection
    if expected_route == 'gpu_memory':
        assert offload['offload']['line'] == 'absent' and offload['offload']['gpu_memory']['used_mib'] >= spec['footprint_mib']
    assert offload['models'] == [spec['model_alias']] and offload['props_model_path'] == spec['model_path']
    probes = [c for c in result['calls'] if c.get('probe')]
    assert probes, 'no one-token load probe'
    chats = [c for c in result['calls'] if 'chat_call' in c and 'path' in c]  # not the fault event lines
    assert chats and {c['path'] for c in chats} == {'/v1/chat/completions'}
    assert {c.get('model') for c in chats} == {spec['model_alias']}
    assert all(isinstance(c['seed'], int) for c in chats)
    assert not any(c.get('env_llama_arg') for c in result['calls'] if c.get('event') == 'serve')
    census = (batch / 'gpu_census.jsonl').read_text().splitlines()
    assert census and json.loads(census[-1])['need_free_mib'] in (2048, spec['footprint_mib'] + 2048)
    return {'model_sha256': server['model_sha256'], 'build': pins[-1]['build']['version_line'],
            'offloaded_layers': f"{offload['offload']['offloaded_layers']}/{offload['offload']['total_layers']}",
            'offload_routes': sorted({r['where'] + ':' + r['route'] for r in routes}),
            'chat_path': '/v1/chat/completions', 'served_alias': offload['models']}


def check_llamacpp_manifests(result: dict) -> dict:
    state, config = result['state'], result['config']
    model = 'llamacpp/' + config['llamacpp']['model_alias']
    out = {}
    for step in ('sweep_append_only_summary', 'sweep_none'):
        manifest = json.loads((Path(state['steps'][step]['out']) / 'manifest.json').read_text())
        assert manifest['manager']['model'] == model, manifest['manager']
        assert manifest['seed_policy']['kind'] == 'llamacpp_seed', manifest['seed_policy']
        block = manifest['c3_label_sweep']
        assert block['backend'] == 'llamacpp' and block['llama_server']['model_sha256'] == config['llamacpp']['model_sha256']
        assert block['llamacpp_build'] == config['llamacpp']['build'] and 'ollama' not in block
        out[step] = manifest['manager']['model']
    live = json.loads((Path(state['steps']['liveness']['out']) / 'manifest.json').read_text())
    assert live['manager']['model'] == model and live['seed_policy']['kind'] == 'llamacpp_seed'
    index = json.loads(Path(state['steps']['index']['path']).read_text())
    assert index['manager'] == {'backend': 'llamacpp', 'model': model,
                                'model_sha256': config['llamacpp']['model_sha256'],
                                'llamacpp_build': config['llamacpp']['build']}, index.get('manager')
    return {'manager_model': model, 'index_manager': index['manager']}


def _completed_ok(result: dict) -> tuple[dict, Path]:
    assert not result['timed_out'], f"scenario exceeded {result['deadline_s']} s"
    state, batch = result['state'], result['batch']
    assert state['stop_reason'] is None, state['stop_reason']
    for step in ('preconditions', 'liveness', 'sweep_append_only_summary', 'sweep_none', 'index'):
        assert state['steps'][step]['completed'], step
    return state, batch


def _committed_paths(result: dict, commit: str) -> list:
    paper_remote = Path(result['env']['R1_C3_PAPER_REMOTE'])
    return run(['git', 'ls-tree', '-r', '--name-only', commit], cwd=paper_remote).splitlines()


def _records(batch: Path) -> list:
    return [json.loads(line) for line in (batch / 'interruptions.jsonl').read_text().splitlines()]


def check_interrupt(result: dict) -> dict:
    state, batch = _completed_ok(result)
    info = result['interrupt']
    assert info, 'the runner was never interrupted (no completed root with another in progress)'
    step = state['steps']['sweep_append_only_summary']
    out, work = Path(step['out']), Path(step['work'])
    records = _records(batch)
    assert len(records) == 1, records
    record = records[0]
    assert record['kind'] == 'process_restart' and record['phase'] == 'sweep_append_only_summary', record
    assert (out / 'interruptions.jsonl').read_text().strip() == json.dumps(record, default=str)
    assert 'INTERRUPTION' in (batch / 'sweep_append_only_summary.log').read_text()
    runner_log = (batch / 'runner.log').read_text()
    assert 'INTERRUPTION' in runner_log and runner_log.count("'r1.liveness'") == 1  # appended, not truncated
    completed, rerun = info['completed_before_kill'], record['roots_rerun_whole']
    assert rerun and not set(rerun) & set(completed), (rerun, completed)
    for inst, before in info['hashes_before'].items():  # kept byte for byte, never re-run
        assert _sha(out / 'roots' / f'{inst}.json') == before['root'], inst
        assert _sha(work / 'roots' / inst / 'root_trials.jsonl') == before['ledger'], inst
    manifest = json.loads((out / 'manifest.json').read_text())
    expected = len(state['steps']['liveness']['eligible_nodes']) * result['config']['instances']
    assert manifest['sessions'][0]['jobs_before'] == expected - record['roots_completed_kept'], manifest['sessions']
    runs = result['config']['runs']
    for inst in rerun:  # re-run whole; the partial attempt archived, never merged
        partial = out / 'provenance/ledgers/interrupted/01/roots' / inst / 'root_trials.jsonl'
        final = [json.loads(line) for line in (out / 'provenance/ledgers/roots' / inst / 'root_trials.jsonl')
                 .read_text().splitlines() if line.strip()]
        assert (work / 'interrupted/01/roots' / inst).is_dir(), inst
        # A root killed before its first trial was logged has no partial ledger to archive (it may start
        # between the Interrupter's snapshot and the kill); one with logged trials at the kill must have it.
        assert partial.exists() or inst not in info['partial_at_kill'], (inst, info['partial_at_kill'])
        budget = [r['budget_index'] for r in final]  # a fresh campaign from trial 1, contiguous
        assert budget == list(range(1, len(budget) + 1)) and len(budget) >= runs, (inst, budget)
    restart = state['service_restarts'][0]
    assert restart['reason'] == 'process_restart' and restart['previous_instance']['action'] == 'SIGTERM', restart
    key = _key(state)
    assert restart['previous_instance']['pid'] == info['ollama_before'] != restart[key]['pid']
    assert record['service_restart']['generation'] == 1
    assert (batch / _record_name(state, restart[key]['port'], 1)).exists()
    assert 'results/r1/pilot/' + out.name + '/interruptions.jsonl' in _committed_paths(result, step['commit'])
    checks = step['checks']
    assert checks['roots'] == expected and checks['interrupted_attempts']['root_attempts'] == len(rerun)
    extra = {}
    if result.get('backend') == 'llamacpp':  # both generations pinned and fully offloaded
        assert json.loads((batch / 'gpu_offload_load_probe_r1.json').read_text())['offload']['full']
        extra = {'llamacpp': check_llamacpp(result), 'manifests': check_llamacpp_manifests(result),
                 'orphan_check': restart['previous_instance']['check']}
    return {**extra, 'killed_utc': info['killed_utc'], 'completed_before_kill': completed, 'roots_rerun_whole': rerun,
            'roots_completed_kept': record['roots_completed_kept'],
            'resumed_jobs_before': manifest['sessions'][0]['jobs_before'],
            'orphan_server_stopped': restart['previous_instance']['action'], 'table': table_from_sweep(result)}


def check_watchdog(result: dict) -> dict:
    state, batch = _completed_ok(result)
    step = state['steps']['sweep_append_only_summary']
    out = Path(step['out'])
    records = _records(batch)
    assert len(records) == 1 and records[0]['kind'] == 'runner_lost', records
    record = records[0]
    event = record['runner_event']
    assert event['kind'] == 'server_exited' and event['signal'] == 'SIGTERM' and event['returncode'] == -15, event
    assert event['detected_utc'] and event['last_healthy_utc'] <= event['detected_utc']
    recent = event['last_request'].get('last_server_requests') or []
    assert any('fault=sigterm' in line for line in recent), event['last_request']
    assert record['roots_rerun_whole'] or record['root_failures_moved'], record
    restart = state['service_restarts'][0]
    assert restart['reason'] == 'runner_lost' and restart['generation'] == 1
    key = _key(state)
    assert restart[key]['pid'] != restart['previous_' + key]['pid']
    serves = [c for c in result['calls'] if c.get('event') == 'serve']
    assert len(serves) == 2, serves  # the original and the restarted server
    assert len([c for c in result['calls'] if c.get('fault') == 'sigterm']) == 1
    checks = step['checks']
    expected = len(state['steps']['liveness']['eligible_nodes']) * result['config']['instances']
    assert checks['roots'] == expected and checks['root_failures'] == 0
    assert 'results/r1/pilot/' + out.name + '/interruptions.jsonl' in _committed_paths(result, step['commit'])
    extra = {}
    if result.get('backend') == 'llamacpp':
        assert json.loads((batch / 'gpu_offload_load_probe_r1.json').read_text())['offload']['full']
        extra = {'llamacpp': check_llamacpp(result), 'manifests': check_llamacpp_manifests(result)}
    return {**extra, 'runner_event': {k: event[k] for k in ('kind', 'signal', 'returncode', 'detected_utc')},
            'last_server_request': next(line for line in recent if 'fault=sigterm' in line),
            'roots_rerun_whole': record['roots_rerun_whole'], 'root_failures_moved': record['root_failures_moved'],
            'restarted_generation': restart['generation'], 'table': table_from_sweep(result)}



def check_retry(result: dict) -> dict:
    assert not result['timed_out'], f"scenario exceeded {result['deadline_s']} s"
    state, batch = result['state'], result['batch']
    assert state['stop_reason'] is None, state['stop_reason']
    for step in ('preconditions', 'liveness', 'sweep_append_only_summary', 'sweep_none', 'index'):
        assert state['steps'][step]['completed'], step
    paper_remote = Path(result['env']['R1_C3_PAPER_REMOTE'])
    for step in ('liveness', 'sweep_append_only_summary', 'sweep_none', 'index'):
        run(['git', 'cat-file', '-e', state['steps'][step]['commit'] + '^{commit}'], cwd=paper_remote)
    chats = [c for c in result['calls'] if c.get('path') in ('/api/chat', '/v1/chat/completions') and 'chat_call' in c]
    dropped = [c for c in chats if c.get('fault') == 'drop']
    assert len(dropped) == 1, dropped
    resent = [c for c in chats if c['chat_call'] > dropped[0]['chat_call'] and c['seed'] == dropped[0]['seed']]
    assert resent, 'the dropped request was not resent with the same seed'
    retried = sum(state['steps'][s]['checks']['llm_calls_retried'] for s in ('sweep_append_only_summary', 'sweep_none'))
    assert retried == 1, retried
    assert all(isinstance(c['seed'], int) for c in chats)
    ollama = state[_key(state)]
    assert ollama.get('stopped_utc')
    if result.get('backend') == 'llamacpp':
        extra_llama = {'llamacpp': check_llamacpp(result), 'manifests': check_llamacpp_manifests(result)}
        collection = json.loads((batch / 'gpu_offload_append_only_summary_collection.json').read_text())
        assert collection['offload']['full']  # checked again after collection
    else:
        assert Path(ollama['models_dir']).is_relative_to(batch)
        extra_llama = {}
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
    extra = {}
    if result.get('overridden') is not None:
        config = result['config']
        audit = config['audit']
        assert index['audit']['seeds'] == audit['seeds'], index['audit']
        assert index['audit']['label_seeds'] == audit['seeds'][:audit['label_seeds']]
        assert index['audit']['evaluation_seeds'] == audit['seeds'][audit['label_seeds']:]
        assert index['nodes_pending'] == config['nodes_pending']
        check = state['paper_a_check']
        expected = 'not_applicable' if '--not-applicable' in check['command'] else 'clear_finished'
        assert check['verdict'] == 'clear' and check['report']['verdict'] == expected, check
        assert 'paper_a_status.py' in ' '.join(check['command'])
        extra = {'base_config_overridden_keys': result['overridden'], 'index_audit_seeds': index['audit']['seeds'],
                 'index_nodes_pending': index['nodes_pending'], 'paper_a_status_verdict': check['report']['verdict']}
    return {**extra, **extra_llama, 'dropped_chat_call': dropped[0]['chat_call'], 'resent_with_same_seed': True,
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
    ollama = state[_key(state)]
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
    ap.add_argument('--scenario', choices=['retry', 'permanent', 'interrupt', 'watchdog', 'both', 'all'],
                    default='both')
    ap.add_argument('--out', type=Path, default=None)
    ap.add_argument('--python', default=sys.executable, help='interpreter with the harness dependencies')
    ap.add_argument('--deadline', type=float, default=150.0, help='seconds per scenario run')
    ap.add_argument('--keep', action='store_true', help='compatibility flag; temporary directories are always kept')
    ap.add_argument('--base-config', type=Path, default=None,
                    help='start from this launch config (e.g. r1/scripts/configs/c3_sweep_ada.json); a host '
                         'draft with TODO_VERIFY values is accepted, its host values are overridden')
    ap.add_argument('--fake-offload', choices=['line', 'silent'], default='line',
                    help='llama.cpp fake: log the offload line (route i) or not, like v0.7.0 (route ii)')
    ap.add_argument('--backend', choices=['ollama', 'llamacpp'], default=None,
                    help='fixture config backend (default ollama); with --base-config the base decides')
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
    scenarios = SCENARIOS.get(args.scenario, [args.scenario])
    base_config = None
    if args.base_config:
        sys.path.insert(0, str(REPO))
        from r1.scripts.c3_label_sweep import load_config
        base_config = load_config(args.base_config, allow_placeholders=True)  # the runner's own validation first
        if args.backend and args.backend != base_config['backend']:
            raise SystemExit(f'STOP: --backend {args.backend} contradicts the base config ({base_config["backend"]})')
    summary = {'label': 'DRYRUN', 'scenarios': {}, 'started_utc': stamp, 'harness_source': str(harness_source),
               'base_config': str(args.base_config) if args.base_config else None,
               'backend': base_config['backend'] if base_config else (args.backend or 'ollama')}
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
            result = run_scenario(scenario, root, fixture, bin_dir, data_sources, args.python, args.deadline,
                                  base_config, backend=args.backend or 'ollama',
                                  fake_offload=args.fake_offload)
            entry['checks'] = {'retry': check_retry, 'permanent': check_permanent, 'interrupt': check_interrupt,
                               'watchdog': check_watchdog}[scenario](result)
            entry['passed'] = True
        except Exception as exc:
            entry['passed'] = False
            entry['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            if result and entry.get('passed'):
                entry['stop_reason'] = result['state'].get('stop_reason')
                entry['batch'] = str(result['batch'])
                target = out / scenario
                target.mkdir()
                for path in sorted(result['batch'].glob('*.log')) + sorted(result['batch'].glob('*.json*')):
                    shutil.copy2(path, target / path.name)
                if (root / 'fake_calls.jsonl').exists():
                    shutil.copy2(root / 'fake_calls.jsonl', target / 'fake_calls.jsonl')
            if entry.get('passed'):
                subprocess.run([shutil.which('tmux') or 'tmux', '-L', socket_name, 'kill-server'], capture_output=True)
            entry['temporary_root_removed'] = False
        summary['scenarios'][scenario] = entry
        if not entry.get('passed'):
            break
    summary['elapsed_seconds'] = round(time.monotonic() - start, 1)
    summary['completed'] = all(e.get('passed') for e in summary['scenarios'].values())
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, default=str) + '\n')
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
