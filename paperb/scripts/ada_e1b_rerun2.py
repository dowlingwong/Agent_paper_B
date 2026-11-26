"""E1b rerun-2 on Ada (R1-E1B-RERUN2, PLAN §10 row of 14 Oct 2026; PILOT).

Phases, each checkpointed in ``batch_state.json``:

1. preconditions: PLAN rows, both checkouts at their origin heads, the model
   digest pin, one co-tenancy GPU card, Ollama with ``OLLAMA_KEEP_ALIVE=-1``
   and the pinned model fully offloaded with telemetry;
2. LLM liveness (memory on, seeded): the four rerun nodes, 2 instances, W = 10,
   committed under ``results/r1/engineering/liveness_llm_<UTC>/``; fewer than
   two passing nodes is a STOP;
3. arm A: LLM, ``append_only_summary``, through the D28 gate;
4. arm B: LLM, ``none`` (declared contrast; gate-exempt, eligibility from the
   memory-on check);
5. arm C: scripted stand-in (CPU; no gate);
6. for each arm: collection checks, ``e1b_analyze`` tables, commit and the
   committed-data regeneration check;
7. comparison: ``r1.headroom.e1b_compare`` over the three committed runs;
8. finish: STATUS entry and push.

A completed phase is never redone; an interrupted phase is a STOP for the
author and is never retried automatically.  Reuses the helpers of
``deepthought_batch1_resume.py`` (pin, co-tenancy card selection, ``check_gpu``,
``assert_full_offload``, ``commit`` with the whitespace check, push
verification and ``finish``) loaded without running its DT4 ``main()``.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from r1.scripts.dryrun_guard import validate_dryrun

DRYRUN = validate_dryrun()
if not DRYRUN and platform.node().split('.')[0] != 'ucrtasl':
    raise SystemExit('STOP: Ada-only E1b rerun-2')

# Load the shared helpers (constants, census, collect, finish) without running main().
source_path = Path(__file__).with_name('deepthought_batch1_resume.py')
tree = ast.parse(source_path.read_text())
assert isinstance(tree.body[-1], ast.If), 'unexpected deepthought_batch1_resume.py tail'
tree.body.pop()  # drop the __main__ guard
exec(compile(tree, str(source_path), 'exec'), globals())

ROWS = ('R1-E1B-RERUN2', 'D28 (revised criterion 2)', 'R1-COMPUTE (GPU co-tenancy, 13 Oct)')
NODES = ['digits_mlp', 'tabular_mlp', 'openml_ionosphere', 'openml_breast_w']
INSTANCES = 18
RUNS = 20
POINTS = [4, 8, 12]
REPS = 2
AUDIT_SEEDS = 6
WORKERS = 4
if DRYRUN:
    NODES = ['digits_mlp', 'openml_breast_w']
    INSTANCES, RUNS, POINTS, REPS, AUDIT_SEEDS, WORKERS = 2, 6, [2], 1, 1, 1
OLLAMA_SESSION = 'r1_ollama_e1b_rerun2'
PHASES = ('preconditions', 'liveness', 'arm_A', 'arm_B', 'arm_C', 'comparison')
ARMS = {
    'A': ('append_only_summary', 'primary', 'langgraph'),
    'B': ('none', 'contrast', 'langgraph'),
    'C': ('none', 'reference', 'scripted'),
}


class PhaseInterrupted(RuntimeError):
    """A phase started but did not complete; the author must decide (never retried)."""


def load_previous_state():
    """Resume the phase checkpoints written by an earlier process."""
    path = BATCH / 'batch_state.json'
    if not path.exists():
        return
    previous = json.loads(path.read_text())
    steps = previous.pop('steps', {})
    state.update(previous)
    state.setdefault('steps', {}).update(steps)


def phase(name, fn):
    entry = state['steps'].get(name)
    if entry and entry.get('completed'):
        print(f'PHASE {name}: completed; skipping', flush=True)
        return
    if entry:
        raise PhaseInterrupted(
            f'phase {name} was interrupted at {entry.get("started_utc")}'
        )
    state['steps'][name] = {'completed': False, 'started_utc': stamp()}
    save()
    fn()
    state['steps'][name]['completed'] = True
    state['steps'][name]['completed_utc'] = stamp()
    save()


def select_card():
    """Wait for a card whose free memory covers footprint + margin; take the emptiest."""
    while True:
        rows, eligible = gpu_rows()
        wanted = os.environ.get('R1_GPU_UUID', 'auto')
        if wanted != 'auto':
            eligible = [r for r in eligible if r.split(',')[1].strip() == wanted]
        with (BATCH / 'gpu_wait.jsonl').open('a') as f:
            f.write(json.dumps({'label': 'DRYRUN' if DRYRUN else 'ENGINEERING_ONLY', 'utc': stamp(), 'rows': rows,
                                'eligible': eligible}) + '\n')
        if eligible:
            return max(eligible, key=lambda r: int(r.split(',')[3].strip()))
        time.sleep(60)


def model_ps():
    with urlopen(OLLAMA_URL + '/api/ps', timeout=15) as response:
        return json.load(response)


def check_after_collection(where):
    """The pinned model must be fully offloaded after every LLM phase."""
    processes = model_ps()
    (BATCH / f'gpu_offload_{where}.json').write_text(json.dumps(
        {'label': 'DRYRUN' if DRYRUN else 'ENGINEERING_ONLY', 'utc': stamp(), 'processes': processes}, indent=2) + '\n')
    loaded = next((m for m in processes['models'] if m.get('name', m.get('model')) == MODEL), None)
    assert_full_offload(loaded, where)
    check_gpu()


def preconditions():
    plan = (PAPER / 'docs/r1/PLAN.md').read_text()
    for row in ROWS:
        if row not in plan:
            raise RuntimeError(f'STOP: PLAN §10 lacks the author row {row}')
    models_value = os.environ.get('R1_OLLAMA_MODELS')
    if not models_value:
        raise RuntimeError('STOP: R1_OLLAMA_MODELS is required')
    models = Path(models_value)
    if not models.is_dir():
        raise RuntimeError(f'STOP: R1_OLLAMA_MODELS directory is missing: {models}')
    remote = 'dryrun' if DRYRUN else 'origin'
    paper_head = git_output(PAPER, 'rev-parse', 'HEAD')
    if paper_head != git_output(PAPER, 'ls-remote', remote, 'refs/heads/main').split()[0]:
        raise RuntimeError('STOP: paper checkout is not at origin/main')
    harness_head = git_output(HARNESS, 'rev-parse', 'HEAD')
    if harness_head != git_output(HARNESS, 'ls-remote', remote, 'refs/heads/r1').split()[0]:
        raise RuntimeError('STOP: harness checkout is not at origin/r1')
    pin_file = PAPER / 'r1/scripts/HARNESS_PIN_RERUN2'
    if pin_file.exists():
        pinned = pin_file.read_text().strip()
        if harness_head != pinned:
            raise RuntimeError(f'STOP: harness head {harness_head} differs from HARNESS_PIN_RERUN2 {pinned}')
    state['paper_head_at_launch'] = paper_head
    state['harness_head_at_launch'] = harness_head
    state['authorization'] = 'PLAN §10 rows: ' + ', '.join(ROWS)
    save()
    with socket.socket() as port_probe:
        port_probe.bind(('127.0.0.1', OLLAMA_PORT))  # refuses if anything already listens
    if subprocess.run(['tmux', 'has-session', '-t', OLLAMA_SESSION], capture_output=True).returncode == 0:
        raise RuntimeError(f'STOP: a tmux session {OLLAMA_SESSION} already exists')
    state['gpu'] = select_card()
    uuid = state['gpu'].split(',')[1].strip()
    check_gpu()
    command = (f'CUDA_VISIBLE_DEVICES={uuid} OLLAMA_VULKAN=0 OLLAMA_HOST=127.0.0.1:{OLLAMA_PORT} '
               f'OLLAMA_MODELS={models} OLLAMA_NUM_PARALLEL=1 OLLAMA_KEEP_ALIVE=-1 '
               f'{OLLAMA} serve > {BATCH}/ollama_serve.log 2>&1')
    cmd(['tmux', 'new-session', '-d', '-s', OLLAMA_SESSION, command])
    state['ollama_started_by_batch'] = True
    save()
    for _ in range(60):
        try:
            with urlopen(OLLAMA_URL + '/api/version', timeout=2) as r:
                version = json.load(r)
            break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('STOP: dedicated Ollama server did not start')
    pin()
    payload = json.dumps({'model': MODEL, 'prompt': 'Reply OK', 'stream': False,
                          'keep_alive': -1, 'options': {'num_predict': 1}}).encode()
    with urlopen(Request(OLLAMA_URL + '/api/generate', data=payload,
                         headers={'Content-Type': 'application/json'}), timeout=300) as r:
        probe_result = json.load(r)
    offload = model_ps()
    (BATCH / 'gpu_offload_probe.json').write_text(json.dumps(
        {'label': 'DRYRUN' if DRYRUN else 'ENGINEERING_ONLY', 'response': probe_result, 'processes': offload}, indent=2) + '\n')
    loaded = next((m for m in offload['models'] if m.get('name', m.get('model')) == MODEL), None)
    assert_full_offload(loaded, 'load probe')
    if loaded['digest'] != DIGEST:
        raise RuntimeError('STOP: loaded model digest differs from author pin')
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    selected = next(g for g in xml.findall('gpu') if g.findtext('uuid') == uuid)
    if not selected.findall('./processes/process_info'):
        raise RuntimeError('STOP: no process on the selected GPU after loading')
    state['model_loaded'] = True
    state['ollama_version'] = version
    check_gpu()
    state['gpu_offload'] = {'size': loaded['size'], 'size_vram': loaded['size_vram'], 'full_offload': True,
                            'probe_tokens_max': 1, 'keep_alive': -1, 'host': platform.node()}
    save()


def print_estimate():
    """Print leaves and expected LLM calls per arm before anything runs (PLAN constants)."""
    roots = len(NODES) * INSTANCES
    leaves = roots * len(POINTS) * 2 * REPS  # continue + verify, both repetitions
    avg_remaining = RUNS - sum(POINTS) / len(POINTS)
    calls = roots * RUNS + leaves * avg_remaining
    label = 'DRYRUN' if DRYRUN else 'ENGINEERING_ONLY'
    repetitions_text = 'one repetition' if DRYRUN else 'two repetitions'
    print(f'ESTIMATE ({label}): {len(NODES)} nodes x {INSTANCES} instances = {roots} roots; '
          f'{leaves} leaves per arm (assumes every E2 point yields both actions and {repetitions_text}); '
          f'expected LLM calls per LLM arm ~ {roots * RUNS} (roots, W={RUNS}) + '
          f'{int(leaves * avg_remaining)} (branches, mean remaining budget {avg_remaining:.0f}) '
          f'= ~{int(calls)}', flush=True)


def liveness_phase():
    out = PAPER / 'results/r1/engineering' / f'liveness_llm_{stamp()}'
    cmd([PY, '-m', 'r1.liveness', '--run', '--manager', 'langgraph',
         '--memory-mode', 'append_only_summary', '--nodes', *NODES,
         '--instances', '1' if DRYRUN else '2', '--runs', '4' if DRYRUN else '10',
         '--out', str(out), '--work', str(BATCH / 'liveness_work')], log='liveness.log')
    report = json.loads((out / 'liveness.json').read_text())
    eligible = [n for n in NODES if report['nodes'].get(n, {}).get('pass')]
    entry = state['steps']['liveness']
    entry.update({'out': str(out), 'eligible_nodes': eligible,
                  'excluded_nodes': [n for n in NODES if n not in eligible],
                  'verdicts': {n: report['nodes'][n]['criteria'] for n in NODES if n in report['nodes']}})
    save()
    commit(PAPER, 'Record ENGINEERING_ONLY E1b rerun-2 LLM liveness (memory on)', [out], 'liveness')
    if len(eligible) < 2:
        raise RuntimeError(f'STOP: only {len(eligible)} nodes passed D28 liveness (< 2); '
                           'the author decides how to proceed')


def arm(label):
    memory_mode, arm_role, manager = ARMS[label]
    out = PAPER / 'results/r1/pilot' / f'E1b_rerun2_{label}_{stamp()}'
    work = BATCH / f'r1_e1b_rerun2_{label}_work'
    eligible = state['steps']['liveness']['eligible_nodes']
    tables = PAPER / 'docs/r1/reports' / (
        f'HEADROOM_RERUN2_{label}_{datetime.now(timezone.utc).strftime("%Y%m%d")}_tables.md'
    )
    if out.exists() or tables.exists():
        raise RuntimeError('STOP: arm destination already exists; no overwrite')
    checks = collect(
        out, work,
        ['--nodes', *eligible, '--instances', str(INSTANCES), '--runs', str(RUNS),
         '--points', *[str(p) for p in POINTS], '--reps', str(REPS),
         '--audit-seeds', str(AUDIT_SEEDS), '--workers', str(WORKERS),
         '--memory-mode', memory_mode, '--arm', label, '--arm-role', arm_role],
        eligible, manager=manager, memory_mode=memory_mode, arm_role=arm_role,
    )
    if manager == 'langgraph':
        check_after_collection(f'{label.lower()}_collection')
    cmd([PY, '-m', 'r1.headroom.e1b_analyze', str(out), '--md', str(tables)],
        log=f'arm_{label}_analysis.log')
    state['steps'][f'arm_{label}'].update({'out': str(out), 'tables': str(tables), 'checks': checks})
    save()
    commit(PAPER, f'Record PILOT E1b rerun-2 arm {label} ({memory_mode}, {arm_role})', [out, tables],
           f'arm_{label}')
    regeneration_check(out, label)


def regeneration_check(out, label):
    """Re-run e1b_analyze from committed inputs; analysis.json must be byte-identical."""
    archive = BATCH / f'committed_analysis_{label}.tar'
    manifest = json.loads((out / 'manifest.json').read_text())
    sources = sorted({info['source'] for info in manifest['noise'].values()})
    with archive.open('wb') as f:
        subprocess.run(['git', 'archive', 'HEAD', 'r1', str(out.relative_to(PAPER)), *sources],
                       cwd=PAPER, stdout=f, check=True)
    regen = BATCH / f'analysis_regeneration_{label}'
    if regen.exists():
        shutil.rmtree(regen)
    regen.mkdir()
    cmd(['tar', '-xf', str(archive), '-C', str(regen)])
    expected = hashlib.sha256((out / 'analysis.json').read_bytes()).hexdigest()
    regen_out = regen / out.relative_to(PAPER)
    cmd([PY, '-m', 'r1.headroom.e1b_analyze', str(regen_out)], cwd=regen,
        log=f'arm_{label}_regeneration.log')
    observed = hashlib.sha256((regen_out / 'analysis.json').read_bytes()).hexdigest()
    state['steps'][f'arm_{label}']['committed_analysis_sha256'] = expected
    state['steps'][f'arm_{label}']['regenerated_analysis_sha256'] = observed
    save()
    if expected != observed:
        raise RuntimeError('STOP: analysis differs when regenerated from committed inputs')


def comparison():
    dirs = [state['steps'][f'arm_{label}']['out'] for label in ('A', 'B', 'C')]
    report = PAPER / 'docs/r1/reports' / f'HEADROOM_RERUN2_{stamp()}_comparison.md'
    payload = report.with_suffix('.json')
    if report.exists() or payload.exists():
        raise RuntimeError('STOP: comparison destination already exists; no overwrite')
    cmd([PY, '-m', 'r1.headroom.e1b_compare', *dirs, '--md', str(report), '--json', str(payload)],
        log='comparison.log')
    state['steps']['comparison'].update({'report': str(report), 'json': str(payload)})
    save()
    commit(PAPER, 'Record PILOT E1b rerun-2 cross-arm comparison', [report, payload], 'comparison')


def main():
    load_previous_state()
    state['status_title'] = 'R1-E1B-RERUN2 (DRYRUN)' if DRYRUN else 'R1-E1B-RERUN2 (PILOT)'
    state['status_commit_message'] = 'Record R1-E1B-RERUN2 execution status'
    state['status_accept_note'] = (
        'E1b rerun-2 phases are accepted only where the phase entry explicitly records '
        'completion. Partial outputs are preserved; no completed phase was re-run and no '
        'interrupted phase was retried.'
    )
    state['ollama_session'] = OLLAMA_SESSION
    liveness_out = state['steps'].get('liveness', {}).get('out')
    if liveness_out:
        os.environ['R1_LIVENESS_MANIFEST'] = str(Path(liveness_out) / 'liveness.json')
    save()
    phase('preconditions', preconditions)
    print_estimate()
    phase('liveness', liveness_phase)
    os.environ['R1_LIVENESS_MANIFEST'] = str(Path(state['steps']['liveness']['out']) / 'liveness.json')
    for label in ('A', 'B', 'C'):
        phase(f'arm_{label}', lambda label=label: arm(label))
    phase('comparison', comparison)


def _already_finished() -> bool:
    """True when every phase completed and the STATUS entry was written."""
    steps = state.get('steps', {})
    return (
        all(steps.get(name, {}).get('completed') for name in PHASES)
        and steps.get('STATUS', {}).get('completed') is True
    )


def _entrypoint():
    load_previous_state()
    if _already_finished():
        # Review F10: finish is the last phase; a restart of a completed batch
        # must not append and push a second STATUS entry.
        raise SystemExit('STOP: this rerun-2 batch already finished; nothing to do')
    try:
        main()
    except PhaseInterrupted as exc:
        finish(f'STOP: {exc}; author decision required (no automatic retry)')
    except Exception as exc:
        finish(f'{type(exc).__name__}: {exc}')
    else:
        finish(None)


if __name__ == '__main__':
    _entrypoint()
