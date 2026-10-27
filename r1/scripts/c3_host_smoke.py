#!/usr/bin/env python3
"""RUNBOOK A.8 host smoke on deepthought: the **real** llama-server, the real GGUF and the
R1-SCHEMA structured output, under the runner's watchdog (A.8) and its per-root resume (A.5).

The desktop dry runs (``c3_sweep_dryrun.py``) prove the supervision logic against a fake
server.  This script proves it against the real one on this host.  It reuses the dry run's
isolation - temporary clones of both repositories, local bare remotes, an isolated tmux
socket, a marked temporary root under the system temporary directory - but it replaces the
dry run's fake ``llama-server``, fake ``nvidia-smi`` and fake ``ps`` with the real ones:
the ``llamacpp`` block, ``gpu_uuid``, binary and GGUF come from the host launch config, so
the pins, the ``/health`` and ``/props`` checks and the full-offload check all run against
the real server on a real TITAN.

No fault is injected (there is no fake to inject one into).  The two scenarios kill a real
process by the pid the batch itself recorded, after checking that pid, process group and
command line match that record:

* ``watchdog`` - kill the batch's ``llama-server`` with SIGTERM while a request is in
  flight (a ``launch_slot_`` line with no ``release`` yet in the server's own log).  The
  runner's watchdog must record the loss, restart the server and re-run the affected roots
  whole, and the batch must complete.
* ``interrupt`` - kill the runner's process group once one root has completed and another
  is in progress (the dry run's own ``Interrupter``), then restart with ``--start <batch>``.
  Completed roots must be kept byte for byte, the interrupted root re-run whole.

Scale is smoke-scale (two nodes, 2 instances, W = 4, one memory mode), so the outputs are
**ENGINEERING_ONLY and must never be used as labels**.  Run from the paper repository root
with ``AR_HARNESS_ROOT`` and a venv python that has the harness dependencies.

AI-assisted (Claude); ENGINEERING_ONLY.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from r1.scripts import c3_sweep_dryrun as dr  # noqa: E402
from r1.scripts.c3_label_sweep import load_config, placeholders  # noqa: E402

SCHEMA = 'manager_proposal/v1'
LAUNCH = re.compile(r'launch_slot_: id\s+\d+ \| task (\d+)')
RELEASE = re.compile(r'release: id\s+\d+ \| task (\d+)')


def utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def real_bin(root: Path, socket_name: str) -> Path:
    """Only the isolated tmux wrapper; nvidia-smi, ps and llama-server stay the host's."""
    bin_dir = root / 'bin'
    bin_dir.mkdir()
    real_tmux = shutil.which('tmux')
    if not real_tmux:
        raise RuntimeError('STOP: the host smoke needs tmux')
    dr.executable(bin_dir / 'tmux', f'#!/bin/sh\nexec {real_tmux} -L {socket_name} "$@"\n')
    return bin_dir


def smoke_config(base: dict, nodes: list, runs: int, instances: int, workers: int) -> dict:
    """The host launch config at smoke scale; every host value and the schema are kept."""
    config = json.loads(json.dumps(base))
    config.update(nodes=nodes, instances=instances, runs=runs, workers=workers,
                  memory_modes=['append_only_summary'], min_live_nodes=len(nodes),
                  liveness=dict(base['liveness'], instances=1, runs=runs),
                  gpu_wait_seconds=0, max_collect_sessions=3)
    left = placeholders(config)
    if left:
        raise RuntimeError(f'STOP: the base config still has open host values {left}')
    if config['backend'] != 'llamacpp':
        raise RuntimeError('STOP: the host smoke is for the llama.cpp backend')
    if config.get('proposal_schema') != SCHEMA:
        raise RuntimeError(f'STOP: the host smoke requires proposal_schema {SCHEMA} (R1-SCHEMA)')
    return config


def server_record(batch: Path, state: dict) -> dict | None:
    rec = state.get('llama_server') or {}
    return rec if rec.get('pid') and not rec.get('stopped_utc') else None


def in_flight(log: Path) -> bool:
    if not log.exists():
        return False
    text = log.read_text(errors='replace')
    launched = {m.group(1) for m in LAUNCH.finditer(text)}
    released = {m.group(1) for m in RELEASE.finditer(text)}
    return bool(launched - released)


def owned(record: dict) -> bool:
    """Signal only a process whose pid, process group and command line match the record."""
    pid = int(record['pid'])
    try:
        if os.getpgid(pid) != int(record['pgid']):
            return False
        cmdline = Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\x00')[:-1]
    except (ProcessLookupError, PermissionError, FileNotFoundError):
        return False
    return cmdline == [str(a) for a in record['cmdline']]


class ServerKiller:
    """Kill the batch's own llama-server once a request is in flight during collection."""

    def __init__(self) -> None:
        self.info: dict | None = None

    def __call__(self, batch: Path, state: dict) -> None:
        if self.info is not None:
            return
        step = (state.get('steps') or {}).get('sweep_append_only_summary') or {}
        if step.get('completed') or not step:
            return
        record = server_record(batch, state)
        if not record or not in_flight(Path(record['log'])):
            return
        if not owned(record):
            raise RuntimeError(f'STOP: the recorded server pid {record["pid"]} does not match its record')
        os.kill(int(record['pid']), signal.SIGTERM)
        self.info = {'killed_utc': utc(), 'pid': int(record['pid']), 'pgid': int(record['pgid']),
                     'port': record.get('port'), 'signal': 'SIGTERM', 'in_flight_request': True,
                     'server_log': record['log']}


def drive(scenario: str, root: Path, fixture: dict, bin_dir: Path, config: dict, python: str,
          deadline_s: float, data_sources: list) -> dict:
    batches = root / f'batches_{scenario}'
    batches.mkdir()
    config_path = root / f'c3_config_{scenario}.json'
    config_path.write_text(json.dumps(config, indent=2))
    env = {k: v for k, v in os.environ.items()
           if k not in ('R1_BATCH_DIRECTORY', 'R1_PAPER_ROOT', 'AR_HARNESS_ROOT', 'R1_LIVENESS_MANIFEST',
                        'PYTHONPATH', 'C3_FAKE_FAULTS')}
    env.update(R1_DRYRUN='1', R1_DRYRUN_ROOT=str(root), R1_DRYRUN_CHILD='1',
               R1_GIT_NAME='HOST SMOKE', R1_GIT_EMAIL='smoke@example.invalid',
               R1_C3_BATCH_ROOT=str(batches), R1_C3_PAPER_REMOTE=str(fixture['paper_remote']),
               R1_C3_HARNESS_REMOTE=str(fixture['harness_remote']), R1_C3_VENV_PYTHON=python,
               R1_C3_SKIP_SUITES='1', R1_C3_CONFIG=str(config_path),
               R1_COAUTHOR='Claude (AI-assisted ENGINEERING_ONLY host smoke) <noreply@anthropic.com>',
               PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
    launcher = fixture['source'] / 'r1/scripts/c3_label_sweep_launch.sh'
    prepare = dr.run(['bash', str(launcher), '--prepare'], cwd=fixture['source'], env=env)
    batch = Path(next(l.split('Batch:')[1].strip() for l in prepare.splitlines()
                      if l.startswith('PREPARED. Batch:')))
    for node in config['nodes']:  # local OpenML caches: git-ignored, absent from a fresh clone
        rel = Path(f'experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache')
        found = dr.data_cache(rel, data_sources)
        if found is not None:
            shutil.copytree(found, batch / 'autoresearch_harness' / rel)
    launch = dr.run(['bash', str(launcher), '--start', str(batch)], cwd=fixture['source'], env=env)
    hook = {'watchdog': ServerKiller(),
            'interrupt': dr.Interrupter(launcher, fixture['source'], env)}[scenario]
    deadline = time.monotonic() + deadline_s
    state: dict = {}
    while time.monotonic() < deadline:
        state_file = batch / 'batch_state.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except json.JSONDecodeError:
                state = {}
            hook(batch, state)
            if state.get('finished_utc') and (batch / 'c3_sweep_summary.json').exists():
                if subprocess.run(['tmux', 'has-session', '-t', 'r1_c3_sweep'], env=env,
                                  capture_output=True).returncode:
                    break
        time.sleep(1)
    return {'batch': batch, 'state': state, 'env': env, 'config': config, 'launch': launch.strip(),
            'timed_out': time.monotonic() >= deadline, 'deadline_s': deadline_s,
            'hook': hook.info, 'scenario': scenario}


# -- checks (real server; the dry run's fake-server assertions do not apply) ----------------

def _completed(result: dict) -> tuple[dict, Path]:
    assert not result['timed_out'], f'scenario exceeded {result["deadline_s"]} s'
    state, batch = result['state'], result['batch']
    assert state.get('stop_reason') is None, state.get('stop_reason')
    for step in ('preconditions', 'liveness', 'sweep_append_only_summary', 'index'):
        assert state['steps'][step]['completed'], step
    return state, batch


def _records(batch: Path) -> list:
    path = batch / 'interruptions.jsonl'
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []


def schema_evidence(result: dict, state: dict, batch: Path) -> dict:
    """R1-SCHEMA: the manifest records the schema, and parse failures are counted, not defaulted."""
    step = state['steps']['sweep_append_only_summary']
    manifest = json.loads((Path(step['out']) / 'manifest.json').read_text())
    manager = manifest['manager']
    assert manager.get('proposal_schema') == SCHEMA, manager
    checks = step['checks']
    index = json.loads(Path(state['steps']['index']['path']).read_text())
    assert (index.get('manager') or {}).get('proposal_schema') == SCHEMA, index.get('manager')
    calls, failures = checks.get('llm_calls'), checks.get('parse_failures')
    return {'manifest_proposal_schema': manager['proposal_schema'],
            'index_proposal_schema': index['manager']['proposal_schema'],
            'manager_kind': manager.get('kind'), 'manager_model': index['manager'].get('model'),
            'llm_calls': calls, 'parse_failures': failures,
            'parse_failure_rate': round(failures / calls, 4) if calls else None,
            'max_parse_failure_rate': result['config']['max_parse_failure_rate'],
            'roots': checks.get('roots'), 'root_failures': checks.get('root_failures')}


def offload_evidence(batch: Path) -> dict:
    out = {}
    for path in sorted(batch.glob('gpu_offload_*.json')):
        report = json.loads(path.read_text())
        out[path.name] = {'full': report['offload']['full'], 'route': report['offload'].get('route')}
        assert report['offload']['full'], path.name
    assert out, 'no offload report was written'
    return out


def check_watchdog(result: dict) -> dict:
    state, batch = _completed(result)
    assert result['hook'], 'the server was never killed (no in-flight request during collection)'
    records = _records(batch)
    lost = [r for r in records if r['kind'] == 'runner_lost']
    assert len(lost) == 1, records
    event = lost[0]['runner_event']
    # The REAL llama-server handles SIGTERM itself ("cleaning up before exit...", cancelling the
    # in-flight task) and then exits on its own, so the watchdog usually sees the loss as
    # `unresponsive` (consecutive failed /health checks) rather than as the fake server's
    # `server_exited` with signal SIGTERM and returncode -15.  Either classification is a correctly
    # recorded loss; which one happened is reported, never asserted away.
    assert event['kind'] in ('server_exited', 'unresponsive', 'model_missing'), event
    assert event['detected_utc'] and event['last_healthy_utc'] <= event['detected_utc']
    assert event.get('instance', {}).get('pid') == result['hook']['pid'], event.get('instance')
    assert (event.get('last_request') or {}).get('server_log_tail'), event.get('last_request')
    stopped = event.get('stopped_instance') or {}
    assert stopped.get('stopped_utc'), stopped
    assert lost[0]['roots_rerun_whole'] or lost[0]['root_failures_moved'], lost[0]
    restart = state['service_restarts'][0]
    assert restart['reason'] == 'runner_lost' and restart['generation'] == 1, restart
    assert restart['llama_server']['pid'] != restart['previous_llama_server']['pid']
    assert restart['previous_llama_server']['pid'] == result['hook']['pid']
    step = state['steps']['sweep_append_only_summary']
    expected = len(state['steps']['liveness']['eligible_nodes']) * result['config']['instances']
    assert step['checks']['roots'] == expected and step['checks']['root_failures'] == 0, step['checks']
    return {'killed': result['hook'],
            'runner_event': {k: event.get(k) for k in
                             ('kind', 'signal', 'returncode', 'detected_utc', 'last_healthy_utc',
                              'consecutive_failed_health_checks')},
            'stopped_instance': {k: stopped.get(k) for k in ('returncode', 'stopped_utc', 'killed')},
            'server_log_tail_lines': len(event['last_request']['server_log_tail']),
            'roots_rerun_whole': lost[0]['roots_rerun_whole'],
            'root_failures_moved': lost[0]['root_failures_moved'],
            'restarted_generation': restart['generation'],
            'server_pids': [restart['previous_llama_server']['pid'], restart['llama_server']['pid']],
            'offload': offload_evidence(batch), 'schema': schema_evidence(result, state, batch)}


def check_interrupt(result: dict) -> dict:
    state, batch = _completed(result)
    info = result['hook']
    assert info, 'the runner was never interrupted'
    step = state['steps']['sweep_append_only_summary']
    out, work = Path(step['out']), Path(step['work'])
    records = [r for r in _records(batch) if r['kind'] == 'process_restart']
    assert len(records) == 1, records
    record = records[0]
    assert (out / 'interruptions.jsonl').exists()
    assert 'INTERRUPTION' in (batch / 'sweep_append_only_summary.log').read_text()
    completed, rerun = info['completed_before_kill'], record['roots_rerun_whole']
    assert rerun and not set(rerun) & set(completed), (rerun, completed)
    for inst, before in info['hashes_before'].items():  # kept byte for byte, never re-run
        assert dr._sha(out / 'roots' / f'{inst}.json') == before['root'], inst
        assert dr._sha(work / 'roots' / inst / 'root_trials.jsonl') == before['ledger'], inst
    runs = result['config']['runs']
    for inst in rerun:
        partial = out / 'provenance/ledgers/interrupted/01/roots' / inst / 'root_trials.jsonl'
        final = [json.loads(l) for l in (out / 'provenance/ledgers/roots' / inst / 'root_trials.jsonl')
                 .read_text().splitlines() if l.strip()]
        assert (work / 'interrupted/01/roots' / inst).is_dir(), inst
        assert partial.exists() or inst not in info['partial_at_kill'], (inst, info['partial_at_kill'])
        budget = [r['budget_index'] for r in final]
        assert budget == list(range(1, len(budget) + 1)) and len(budget) >= runs, (inst, budget)
    restart = state['service_restarts'][0]
    assert restart['reason'] == 'process_restart' and restart['previous_instance']['action'] == 'SIGTERM', restart
    return {'killed_utc': info['killed_utc'], 'completed_before_kill': completed,
            'roots_rerun_whole': rerun, 'roots_completed_kept': record['roots_completed_kept'],
            'orphan_server_stopped': restart['previous_instance']['action'],
            'orphan_check': restart['previous_instance'].get('check'),
            'offload': offload_evidence(batch), 'schema': schema_evidence(result, state, batch)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', choices=['watchdog', 'interrupt', 'both'], default='both')
    ap.add_argument('--config', required=True, help='the completed host launch config')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--python', required=True, help='interpreter with the harness dependencies')
    ap.add_argument('--deadline', type=float, default=3600.0, help='seconds per scenario')
    ap.add_argument('--nodes', nargs='+', default=['digits_mlp', 'openml_breast_w'])
    ap.add_argument('--runs', type=int, default=4)
    ap.add_argument('--instances', type=int, default=2)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--keep', action='store_true', help='keep the temporary roots for inspection')
    args = ap.parse_args()
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: forbidden on Ada')
    args.out.mkdir(parents=True, exist_ok=False)
    harness = Path(os.environ.get('AR_HARNESS_ROOT', str(REPO.parent / 'autoresearch_harness'))).resolve()
    data_sources = [p for p in [Path(os.environ['R1_DRYRUN_DATA_HARNESS'])
                                if os.environ.get('R1_DRYRUN_DATA_HARNESS') else None, harness] if p]
    base = load_config(args.config)  # the runner's own validation; placeholders are refused
    config = smoke_config(base, args.nodes, args.runs, args.instances, args.workers)
    scenarios = ['watchdog', 'interrupt'] if args.scenario == 'both' else [args.scenario]
    summary = {'label': 'ENGINEERING_ONLY', 'ai_assisted': 'AI-assisted (Claude)', 'host': platform.node(),
               'started_utc': utc(), 'config_path': str(args.config), 'harness_source': str(harness),
               'backend': base['backend'], 'proposal_schema': base.get('proposal_schema'),
               'llamacpp': {k: base['llamacpp'][k] for k in
                            ('binary', 'model_path', 'model_sha256', 'build', 'footprint_mib', 'ctx_size')},
               'gpu_uuid': base['gpu_uuid'], 'smoke_scale': {'nodes': args.nodes, 'instances': args.instances,
                                                             'runs': args.runs, 'workers': args.workers,
                                                             'memory_modes': config['memory_modes']},
               'scenarios': {}}
    start = time.monotonic()
    for scenario in scenarios:
        root = Path(tempfile.mkdtemp(prefix=f'r1_c3_smoke_{scenario}_')).resolve()
        (root / '.dryrun').write_text('ENGINEERING_ONLY host smoke\n')
        socket_name = 'r1c3smoke_' + root.name
        entry = {'temporary_root': str(root), 'started_utc': utc()}
        result = None
        began = time.monotonic()
        try:
            fixture = dr.build_fixture(root, harness)
            entry['pin'] = fixture['pin']
            result = drive(scenario, root, fixture, real_bin(root, socket_name), config,
                           args.python, args.deadline, data_sources)
            entry['checks'] = {'watchdog': check_watchdog, 'interrupt': check_interrupt}[scenario](result)
            entry['passed'] = True
        except Exception as exc:
            entry['passed'] = False
            entry['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            entry['elapsed_seconds'] = round(time.monotonic() - began, 1)
            if result:
                entry['stop_reason'] = result['state'].get('stop_reason')
                entry['batch'] = str(result['batch'])
                target = args.out / scenario
                target.mkdir()
                for path in sorted(result['batch'].glob('*.log')) + sorted(result['batch'].glob('*.json*')):
                    shutil.copy2(path, target / path.name)
            subprocess.run([shutil.which('tmux') or 'tmux', '-L', socket_name, 'kill-server'],
                           capture_output=True)
            if not args.keep and result:
                shutil.rmtree(root, ignore_errors=True)
                entry['temporary_root_removed'] = True
        summary['scenarios'][scenario] = entry
    summary['elapsed_seconds'] = round(time.monotonic() - start, 1)
    summary['completed'] = all(e.get('passed') for e in summary['scenarios'].values())
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2, default=str) + '\n')
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
