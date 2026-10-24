"""C3 label sweep runner (PLAN §10: R1-E1B-RERUN2 revision and R1-C3, 18 Oct 2026; C3_DESIGN §4).

Root campaigns only (no branching) with the pinned LLM manager, under two
memory modes (``append_only_summary`` primary, ``none`` contrast), the
``"vary"`` verify split and the PLAN new-campaign action versions, W = 20 worker
runs, D26 seeds, nodes from a config file (default: the D21 nodes) and a
configurable number of instances per node (default 18).  Proposal labels come
later from fresh-seed audits (``r1/c3/audit.py``, a separate stage); this runner
writes ``C3_sweep_index_<UTC>.json`` as that stage's input contract and runs no
audit.

Phases, checkpointed in ``batch_state.json``; a completed phase is never redone
and an interrupted phase is a STOP (never retried automatically), except the
sweep phases (below, RUNBOOK A.5):

1. ``preconditions`` — PLAN rows; paper checkout at its remote head and the
   harness at ``r1/scripts/HARNESS_PIN_C3``; the **Paper A coordination check**
   (PLAN §10, 19 Oct: a configurable command must report that no Paper A live
   campaign is waiting for a card, else the launch refuses); GPU card
   selection under the co-tenancy rule (13 Oct; helpers reused from
   ``deepthought_batch1_resume.py``); a **dedicated Ollama instance** for this
   batch (own port, models directory and process group;
   ``r1/scripts/ollama_instance.py``); digest pin, load probe, full offload.
2. ``liveness`` — the D28 check first (memory on, LLM, 2 instances, W = 10);
   fewer than ``min_live_nodes`` passing nodes is a STOP; failing nodes are
   excluded and recorded.
3. ``sweep_<memory mode>`` — the D28 gate (``none`` is the declared contrast
   and reuses the memory-on verdict), roots-only collection with failure
   records, gates that write ``collection_checks.json`` /
   ``collection_failures.json`` **before** raising, the after-collection
   offload check, archive of ledgers and events, commit.
4. ``index`` — the sweep index for the audit stage, commit.

Resume per campaign root (RUNBOOK A.5, 24 Oct; config ``resume``).  Restarting
the runner on a batch whose sweep phase was interrupted (``--start <batch>``
again) resumes that phase: completed roots are kept and never re-run; a root
that had started but not completed is re-run whole, never patched (its partial
work is moved to ``<work>/interrupted/<n>/`` and archived with the run); the
interruption is logged in ``<batch>/interruptions.jsonl``, the step log, the
runner log and ``<sweep>/interruptions.jsonl``.  Before resuming, the runner
refuses while a process of an earlier runner of this batch is still alive,
stops this batch's orphaned Ollama (pid, process group and environment must
match its record), re-checks the checkout heads, re-runs the Paper A check and
card selection and starts a new dedicated instance (``_r<n>`` records).  An
interrupted liveness, preconditions or index phase stays a STOP.

Runner watchdog (RUNBOOK A.8, 24 Oct; config ``watchdog``, opt-in).  During
collection the runner polls its dedicated instance: process exit (exit status
or signal), ``/api/version`` unresponsive for ``unresponsive_checks`` polls, or
the pinned model missing from ``/api/ps`` for ``model_checks`` polls.  On a
loss it stops the collector's process tree, records the loss (time, exit
status / signal, the server log's last request and signal lines, the last LLM
event), stops and restarts the dedicated instance and resumes per the A.5 rule;
root failure records with transport-class errors written during that session
are moved aside so those roots are re-run whole.  At most ``max_restarts``.

The batch's Ollama instance is stopped in ``finish``; it never touches another
server.  This runner writes no STATUS.md entry (the operator records STATUS);
``batch_state.json`` and ``c3_sweep_summary.json`` hold the outcome.

DRYRUN (``R1_DRYRUN=1``; ``r1/scripts/dryrun_guard.py``): refused on Ada; fake
Ollama / nvidia-smi through PATH; pushes only to local bare remotes
(``r1/scripts/c3_sweep_dryrun.py``).

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import ast
import getpass
import json
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from r1.scripts.dryrun_guard import validate_dryrun  # noqa: E402
from r1.scripts.ollama_instance import OllamaInstance, pid_alive, stop_orphan  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
MODEL = 'qwen2.5-coder:7b'
DIGEST = 'dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364'
ROWS = ('R1-E1B-RERUN2 (revision)', 'R1-C3 (18 Oct)', 'D21', 'Verify split policy',
        'D28 (revised criterion 2)', 'R1-COMPUTE (GPU co-tenancy, 13 Oct)',
        'R1-COMPUTE (Paper A coordination, 19 Oct)', 'D4 amendment')
D21_NODES = ['digits_mlp', 'tabular_mlp', 'openml_breast_w', 'openml_ionosphere', 'openml_wdbc', 'openml_credit_approval', 'openml_sonar', 'openml_blood_transfusion']  # noise-node pool after the 22 Oct common 30-seed run (PLAN §10, D21 rows, 22 Oct)
DEFAULTS = {
    'nodes': D21_NODES,
    'instances': 18,
    'runs': 20,
    'memory_modes': ['append_only_summary', 'none'],
    'workers': 4,
    'transport_max_attempts': 3,
    'liveness': {'instances': 2, 'runs': 10, 'memory_mode': 'append_only_summary'},
    'min_live_nodes': 2,
    'max_parse_failure_rate': 0.20,
    'max_collect_sessions': 12,
    'paper_a_check': {'command': None, 'timeout': 120},
    'gpu_uuid': 'auto',
    'gpu_wait_seconds': 6 * 3600,
    'ollama': {'binary': '/usr/local/bin/ollama', 'seed_models_from': None, 'port': None, 'start_timeout': 120},
    'allowed_hosts': ['ucrtasl', 'deepthought', 'deepthought2'],
    # Fresh-seed audit design recorded for the audit stage (r1/c3/audit.py; C3_DESIGN §4):
    # K = 10 common joint seeds, first half for labels, second half for offline evaluation.
    'audit': {'seeds': list(range(7001, 7011)), 'label_seeds': 5, 'evaluation_seeds': 5},
    # Candidate nodes that are NOT run: recorded only, moved into 'nodes' by a later
    # config once they qualify (e.g. the 22 Oct node-pool re-measurement).
    'nodes_pending': [],
    # RUNBOOK A.5 (24 Oct): a restarted runner resumes an interrupted sweep phase from its last
    # completed campaign root (interrupted roots re-run whole); at most max_restarts per batch.
    'resume': {'sweeps': True, 'max_restarts': 5},
    # RUNBOOK A.8 (24 Oct): watchdog of the batch's dedicated Ollama during collection (opt-in).
    'watchdog': {'enabled': False, 'poll_seconds': 5.0, 'health_timeout': 10.0, 'unresponsive_checks': 3,
                 'model_checks': 3, 'max_restarts': 3},
}
PHASES_FIXED = ('preconditions', 'liveness')
INTERRUPTION_SCHEMA = 'r1.c3_sweep_interruption/1'
GPU_HELPERS = {'gpu_rows', 'gpu_census', 'check_gpu', 'assert_full_offload'}
GPU_CONSTANTS = {'MODEL_FOOTPRINT_MIB', 'MARGIN_MIB'}


class Stop(RuntimeError):
    """A STOP for the author; the batch never retries automatically."""


class PhaseInterrupted(Stop):
    pass


def stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def load_config(path=None) -> dict:
    """Defaults (PLAN D21 nodes, 18 instances, W = 20) overlaid by a JSON config file."""
    config = json.loads(json.dumps(DEFAULTS))
    if path:
        user = json.loads(Path(path).read_text())
        unknown = set(user) - set(DEFAULTS) - {'comment'}
        if unknown:
            raise Stop(f'STOP: unknown config keys {sorted(unknown)}')
        for key, value in user.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    if config['runs'] != 20 and not validate_dryrun():
        raise Stop('STOP: W = 20 worker runs outside DRYRUN (C3_DESIGN §4)')
    if not config['memory_modes'] or not set(config['memory_modes']) <= {'append_only_summary', 'none'}:
        raise Stop('STOP: memory modes are append_only_summary and/or none (D24)')
    validate_audit(config['audit'])
    if set(config['nodes_pending']) & set(config['nodes']):
        raise Stop('STOP: a node is both in nodes and nodes_pending')
    if len(set(config['nodes'])) != len(config['nodes']):
        raise Stop('STOP: duplicate node in nodes')
    validate_resume(config['resume'], config['watchdog'])
    return config


def validate_resume(resume: dict, watchdog: dict) -> None:
    """RUNBOOK A.5 / A.8 settings: known keys and sane values only."""
    if set(resume) != {'sweeps', 'max_restarts'} or not isinstance(resume['sweeps'], bool) \
            or not isinstance(resume['max_restarts'], int) or resume['max_restarts'] < 0:
        raise Stop(f'STOP: resume must be {{"sweeps": bool, "max_restarts": int >= 0}}, got {resume}')
    keys = {'enabled', 'poll_seconds', 'health_timeout', 'unresponsive_checks', 'model_checks', 'max_restarts'}
    if set(watchdog) != keys or not isinstance(watchdog['enabled'], bool):
        raise Stop(f'STOP: watchdog keys must be {sorted(keys)} with a boolean "enabled", got {watchdog}')
    for key in keys - {'enabled'}:
        value = watchdog[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise Stop(f'STOP: watchdog.{key} must be a number >= 0, got {value!r}')
    if watchdog['poll_seconds'] <= 0 or watchdog['health_timeout'] <= 0 or watchdog['unresponsive_checks'] < 1:
        raise Stop('STOP: watchdog poll_seconds and health_timeout > 0, unresponsive_checks >= 1')


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def proc_table() -> dict:
    """{pid: (ppid, cmdline)} from /proc (Linux); empty where /proc is unavailable."""
    table = {}
    for entry in Path('/proc').glob('[0-9]*'):
        try:
            stat = (entry / 'stat').read_text()
            ppid = int(stat.rsplit(')', 1)[1].split()[1])
            cmdline = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').strip()
        except (OSError, ValueError, IndexError):
            continue
        table[int(entry.name)] = (ppid, cmdline)
    return table


def descendants(pid: int, table: dict | None = None) -> list:
    table = proc_table() if table is None else table
    children, frontier = [], [pid]
    while frontier:
        parent = frontier.pop()
        for child, (ppid, _) in table.items():
            if ppid == parent and child not in children:
                children.append(child)
                frontier.append(child)
    return children


def stop_tree(pid: int, timeout: float = 20.0) -> dict:
    """SIGTERM a process and all its descendants (collected first), then SIGKILL what is left."""
    pids = [pid, *descendants(pid)]
    for target in pids:
        try:
            os.kill(target, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and any(pid_alive(t) for t in pids):
        time.sleep(0.2)
    killed = [t for t in pids if pid_alive(t)]
    for target in killed:
        try:
            os.kill(target, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return {'pids': pids, 'sigkill': killed}


class RunnerWatchdog:
    """Detects a dead or unresponsive dedicated Ollama during collection (RUNBOOK A.8).

    ``check()`` returns None while healthy, else a loss record: ``server_exited``
    (the instance process ended; exit status or signal), ``unresponsive``
    (``/api/version`` failed ``unresponsive_checks`` consecutive polls) or
    ``model_unloaded`` (the pinned model absent from ``/api/ps`` for
    ``model_checks`` consecutive polls: the model runner is gone; 0 disables).
    """

    def __init__(self, instance, spec: dict, model: str = MODEL) -> None:
        self.instance, self.spec, self.model = instance, spec, model
        self.health_misses = self.model_misses = 0
        self.last_healthy_utc = utc_iso()
        self.started_utc = self.last_healthy_utc

    def model_loaded(self):
        try:
            with urlopen(self.instance.url + '/api/ps', timeout=float(self.spec['health_timeout'])) as response:
                models = json.load(response).get('models') or []
        except (OSError, ValueError):
            return None  # unknown; the health check decides about responsiveness
        return any(m.get('name', m.get('model')) == self.model for m in models)

    def check(self) -> dict | None:
        inst = self.instance
        if not inst.alive():
            return self.event('server_exited', **inst.returncode_info())
        if inst.health(timeout=float(self.spec['health_timeout'])) is None:
            self.health_misses += 1
            if self.health_misses >= int(self.spec['unresponsive_checks']):
                return self.event('unresponsive', consecutive_failed_health_checks=self.health_misses)
            return None
        self.health_misses = 0
        if int(self.spec.get('model_checks', 0)) > 0:
            loaded = self.model_loaded()
            if loaded is False:
                self.model_misses += 1
                if self.model_misses >= int(self.spec['model_checks']):
                    return self.event('model_unloaded', consecutive_checks_without_model=self.model_misses)
                return None
            if loaded:
                self.model_misses = 0
        self.last_healthy_utc = utc_iso()
        return None

    def event(self, kind: str, **info) -> dict:
        record = getattr(self.instance, 'record', {}) or {}
        return {'kind': kind, 'detected_utc': utc_iso(), 'last_healthy_utc': self.last_healthy_utc,
                'watch_started_utc': self.started_utc,
                'instance': {k: record.get(k) for k in ('pid', 'pgid', 'port', 'generation', 'started_utc', 'log')},
                **info}


def validate_audit(audit: dict) -> None:
    """K fresh joint seeds, distinct, split first half label / second half evaluation (C3_DESIGN §4)."""
    seeds = audit.get('seeds') or []
    k = len(seeds)
    if k < 2 or k % 2 or len(set(seeds)) != k or not all(isinstance(x, int) for x in seeds):
        raise Stop(f'STOP: audit.seeds must be an even number (>= 2) of distinct integers, got {seeds}')
    if audit.get('label_seeds') != k // 2 or audit.get('evaluation_seeds') != k // 2:
        raise Stop('STOP: audit label/evaluation split must be first half / second half of audit.seeds')


def load_gpu_helpers(namespace: dict) -> dict:
    """Reuse the co-tenancy helpers of ``deepthought_batch1_resume.py`` without its side effects."""
    source = SCRIPTS / 'deepthought_batch1_resume.py'
    tree = ast.parse(source.read_text())
    body = [n for n in tree.body
            if (isinstance(n, ast.FunctionDef) and n.name in GPU_HELPERS)
            or (isinstance(n, ast.Assign) and {getattr(t, 'id', None) for t in n.targets} & GPU_CONSTANTS)]
    exec(compile(ast.Module(body=body, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def paper_a_check(spec: dict, host: str) -> dict:
    """PLAN §10 (19 Oct): refuse unless no Paper A live campaign is waiting for a card.

    ``spec['command']`` (argv list or shell-quoted string) must exit 0 and print,
    as its last non-empty stdout line, a JSON object with
    ``"paper_a_live_waiting_for_card": false``.  Anything else refuses; the
    record is attached to the exception (``exc.args[1]``) and to the state.
    """
    command = spec.get('command')
    if not command:
        raise Stop('STOP: no Paper A coordination command configured (paper_a_check.command); '
                   'PLAN §10 requires the check before any Paper B GPU launch',
                   {'utc': stamp(), 'verdict': 'refused: no command', 'host': host})
    argv = command if isinstance(command, list) else shlex.split(command)
    record = {'utc': stamp(), 'command': argv, 'host': host}
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=int(spec.get('timeout', 120)))
    except (OSError, subprocess.TimeoutExpired) as exc:
        record['verdict'] = f'refused: could not run ({exc!r})'
        raise Stop(f'STOP: Paper A coordination check could not run: {exc!r}', record) from exc
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    record.update(returncode=done.returncode, stdout_tail=lines[-5:], stderr_tail=done.stderr.splitlines()[-5:])
    if done.returncode != 0 or not lines:
        record['verdict'] = 'refused: check failed'
        raise Stop(f'STOP: Paper A coordination check failed (rc={done.returncode}); launch refused', record)
    try:
        report = json.loads(lines[-1])
    except json.JSONDecodeError:
        record['verdict'] = 'refused: unparseable'
        raise Stop('STOP: Paper A coordination check printed no JSON verdict; launch refused', record)
    record['report'] = report
    if not isinstance(report, dict) or report.get('paper_a_live_waiting_for_card') is not False:
        record['verdict'] = 'refused: Paper A waiting or unknown'
        raise Stop('STOP: a Paper A live campaign is waiting for a card (or the check is inconclusive); '
                   'launch refused - wait, or run on Deepthought (PLAN §10, 19 Oct)', record)
    record['verdict'] = 'clear'
    return record


class SweepRunner:
    def __init__(self, config: dict, *, batch: Path, paper: Path, harness: Path, python: str) -> None:
        self.config = config
        self.dryrun = validate_dryrun()
        self.label = 'DRYRUN' if self.dryrun else 'ENGINEERING_ONLY'
        self.batch, self.paper, self.harness, self.py = batch, paper, harness, python
        self.remote = 'dryrun' if self.dryrun else 'origin'
        self.host = platform.node().split('.')[0]
        self.state: dict = {'label': self.label, 'steps': {}, 'batch': str(batch), 'host': platform.node(),
                            'config': config}
        self.ollama: OllamaInstance | None = None
        self.pending_restart: dict | None = None  # service restart record awaiting its sweep's interruption entry
        self.gpu = load_gpu_helpers({
            'subprocess': subprocess, 'ElementTree': ElementTree, 'getpass': getpass, 'json': json,
            'BATCH': batch, 'state': self.state, 'stamp': stamp,
        })

    # -- bookkeeping ---------------------------------------------------------
    def save(self) -> None:
        (self.batch / 'batch_state.json').write_text(json.dumps(self.state, indent=2, default=str) + '\n')

    def load_previous_state(self) -> None:
        path = self.batch / 'batch_state.json'
        if path.exists():
            previous = json.loads(path.read_text())
            steps = previous.pop('steps', {})
            previous.pop('config', None)
            self.state.update(previous)
            self.state['steps'].update(steps)

    def phase(self, name, fn) -> None:
        entry = self.state['steps'].get(name)
        if entry and entry.get('completed'):
            print(f'PHASE {name}: completed; skipping', flush=True)
            return
        if entry:
            if not self.resumable(name):
                raise PhaseInterrupted(f'STOP: phase {name} was interrupted at {entry.get("started_utc")}; '
                                       'author decision required (no automatic retry)')
            # RUNBOOK A.5: the sweep resumes from its last completed campaign root (see ``sweep``).
            entry.setdefault('resumed_utc', []).append(stamp())
            self.save()
            print(f'PHASE {name}: interrupted at {entry.get("started_utc")}; resuming per campaign root', flush=True)
            fn()
            self.state['steps'][name].update(completed=True, completed_utc=stamp())
            self.save()
            return
        self.state['steps'][name] = {'completed': False, 'started_utc': stamp()}
        self.save()
        fn()
        self.state['steps'][name].update(completed=True, completed_utc=stamp())
        self.save()

    def cmd(self, argv, *, cwd=None, log=None, env=None) -> None:
        print('RUN', argv, flush=True)
        run_env = dict(os.environ, **(env or {}))
        if log:
            with (self.batch / log).open('a') as f:
                subprocess.run(argv, cwd=cwd or self.paper, check=True, stdout=f, stderr=subprocess.STDOUT,
                               env=run_env)
        else:
            subprocess.run(argv, cwd=cwd or self.paper, check=True, env=run_env)

    def git(self, repo, *args) -> str:
        return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()

    def commit(self, message: str, paths, step: str) -> None:
        if self.dryrun:
            message = 'DRYRUN: ' + message
        coauthor = os.environ.get('R1_COAUTHOR', 'AI-assisted <noreply@example.com>')
        self.cmd(['git', 'add', '-f', '--', *[str(p) for p in paths]])
        self.cmd(['git', 'diff', '--cached', '--check', '--', '.', ':!results/r1/**'])
        self.cmd(['git', 'commit', '-m', message, '-m', 'Co-Authored-By: ' + coauthor])
        self.cmd(['git', 'push', self.remote, 'HEAD:refs/heads/main'])
        head = self.git(self.paper, 'rev-parse', 'HEAD')
        remote = self.git(self.paper, 'ls-remote', self.remote, 'refs/heads/main').split()[0]
        if head != remote:
            raise Stop('STOP: pushed head does not match remote head')
        self.state['steps'][step]['commit'] = head
        self.save()

    # -- interruptions (RUNBOOK A.5 / A.8) -------------------------------------
    def resumable(self, name: str) -> bool:
        return name.startswith('sweep_') and bool(self.config['resume']['sweeps'])

    def watchdog_on(self) -> bool:
        return bool(self.config['watchdog']['enabled'])

    def log_event(self, record: dict, out: Path | None, step: str | None) -> dict:
        """One interruption record: batch run log, step log, runner log and the sweep directory (committed)."""
        record = {'schema': INTERRUPTION_SCHEMA, 'n': len(self.state.get('interruptions', [])) + 1,
                  'label': self.label, **record}
        line = json.dumps(record, default=str)
        with (self.batch / 'interruptions.jsonl').open('a') as f:
            f.write(line + '\n')
        if out is not None and out.is_dir():
            with (out / 'interruptions.jsonl').open('a') as f:
                f.write(line + '\n')
        if step:
            with (self.batch / f'{step}.log').open('a') as f:
                f.write('INTERRUPTION ' + line + '\n')
        print('INTERRUPTION', line, flush=True)
        self.state.setdefault('interruptions', []).append(
            {k: record.get(k) for k in ('n', 'kind', 'phase', 'detected_utc')})
        self.save()
        return record

    def earlier_processes(self) -> list:
        """Live processes of an earlier runner of this batch (runner, collector, liveness), never ourselves.

        Called when a restarted runner starts, before it has children of its own.
        """
        table = proc_table()
        mine, pid = {os.getpid()}, os.getpid()
        while pid in table:  # our ancestors (the launcher's shell names the batch too)
            pid = table[pid][0]
            mine.add(pid)
        batch = str(self.batch)
        return [{'pid': p, 'cmdline': c[:300]} for p, (_, c) in sorted(table.items())
                if p not in mine and batch in c and ('c3_label_sweep' in c or 'r1.headroom.e1b_collect' in c
                                                     or 'r1.liveness' in c)]

    def restart_service(self, reason: str, phase: str) -> dict:
        """Stop the lost (or orphaned) dedicated instance and start a new one after the launch checks."""
        restarts = self.state.setdefault('service_restarts', [])
        key = 'resume' if reason == 'process_restart' else 'watchdog'
        limit = int(self.config[key]['max_restarts'])
        used = sum(1 for r in restarts if r['reason'] == reason)
        if used >= limit:
            raise Stop(f'STOP: {reason}: {used} service restarts already (config {key}.max_restarts = {limit}); '
                       'the author decides')
        record = {'reason': reason, 'phase': phase, 'utc': stamp(), 'generation': len(restarts) + 1,
                  'previous_ollama': {k: (self.state.get('ollama') or {}).get(k)
                                      for k in ('pid', 'pgid', 'port', 'generation', 'started_utc', 'log')}}
        restarts.append(record)
        self.save()
        if reason == 'process_restart':
            earlier = self.earlier_processes()
            if earlier:
                record['refused'] = earlier
                self.save()
                raise Stop(f'STOP: processes of an earlier runner of this batch are still alive: {earlier}; '
                           'never resumed alongside them')
            record['previous_instance'] = stop_orphan(self.state.get('ollama') or {})
            self.check_heads()
        elif self.ollama is not None:
            record['previous_instance'] = self.ollama.stop()
        self.ollama = None
        self.state['model_loaded'] = False  # the new instance has not loaded the model yet (co-tenancy margin)
        self.save()
        self.start_service(generation=record['generation'])
        record.update(ollama={k: self.state['ollama'].get(k) for k in
                              ('pid', 'pgid', 'port', 'generation', 'models_seeded', 'started_utc', 'healthy_utc')},
                      gpu=self.state.get('gpu'), paper_a_check=self.state.get('paper_a_check', {}).get('verdict'),
                      completed_utc=stamp())
        self.save()
        return record

    def resume_interrupted(self, out: Path, work: Path, step: str, kind: str, *, restart: dict | None = None,
                           event: dict | None = None, session_started: float | None = None) -> dict:
        """RUNBOOK A.5: keep completed roots; move partial attempts aside so the collector re-runs them whole."""
        n = len(self.state.get('interruptions', [])) + 1
        out_moved, work_moved = out / 'interrupted' / f'{n:02d}', work / 'interrupted' / f'{n:02d}'
        complete, unparseable, failures_moved, rerun = [], [], [], []
        for path in sorted((out / 'roots').glob('*.json')):
            try:
                json.loads(path.read_text())
                complete.append(path.stem)
            except ValueError:  # killed while the collector wrote it
                (out_moved / 'roots').mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(out_moved / 'roots' / path.name))
                unparseable.append(path.stem)
        if kind == 'runner_lost' and session_started is not None:
            for path in sorted((out / 'failures').glob('root__*.json')):
                if path.stat().st_mtime < session_started:
                    continue
                attempts = json.loads(path.read_text()).get('transport_attempts') or []
                if attempts and attempts[-1].get('error_class') not in (None, 'non_retryable'):
                    (out_moved / 'failures').mkdir(parents=True, exist_ok=True)
                    shutil.move(str(path), str(out_moved / 'failures' / path.name))
                    failures_moved.append(path.name[len('root__'):-len('.json')])
        failed = {p.name[len('root__'):-len('.json')] for p in (out / 'failures').glob('root__*.json')}
        if (work / 'roots').is_dir():
            for root in sorted((work / 'roots').iterdir()):
                if root.name in complete or root.name in failed:
                    continue
                (work_moved / 'roots').mkdir(parents=True, exist_ok=True)
                shutil.move(str(root), str(work_moved / 'roots' / root.name))
                rerun.append(root.name)
        entry = self.state['steps'][step]
        return self.log_event({
            'kind': kind, 'phase': step, 'phase_started_utc': entry.get('started_utc'), 'detected_utc': stamp(),
            'rule': 'RUNBOOK A.5: resume from the last completed campaign root; an interrupted root is re-run '
                    'whole, never patched',
            'roots_completed_kept': len(complete), 'roots_rerun_whole': rerun,
            'root_records_unparseable_moved': unparseable, 'root_failures_moved': failures_moved,
            'moved_to': {'out': str(out_moved.relative_to(self.paper)) if out_moved.exists() else None,
                         'work': str(work_moved) if work_moved.exists() else None},
            'service_restart': restart, 'runner_event': event}, out, step)

    def last_request(self, work: Path) -> dict:
        """What the lost server was doing: its log's last request and signal lines, the last LLM event."""
        info: dict = {}
        try:
            log = Path((self.state.get('ollama') or {}).get('log') or '')
            if log.is_file():
                lines = log.read_text(errors='replace').splitlines()
                requests = [line for line in lines if '[GIN]' in line or 'POST "/api/' in line]
                info.update(server_log=str(log), server_log_tail=lines[-20:],
                            last_server_request=requests[-1] if requests else None,
                            last_server_requests=requests[-5:],  # concurrent workers: the fatal one may not be last
                            server_log_signal_lines=[line for line in lines[-500:] if re.search(
                                r'signal|terminated|exit status|killed|no longer running', line, re.I)][-10:])
            events = sorted((work / 'roots').rglob('root_events.jsonl'), key=lambda q: q.stat().st_mtime)
            for path in reversed(events):
                calls = [json.loads(line) for line in path.read_text().splitlines()
                         if line.strip() and '"llm_call' in line]
                if calls:
                    last = calls[-1]
                    info['last_llm_event'] = {'file': str(path), 'event_type': last.get('event_type'),
                                              'trial_id': last.get('trial_id'),
                                              **{k: (last.get('payload') or {}).get(k)
                                                 for k in ('seed', 'llm_seed', 'parse_ok', 'transport_attempts')}}
                    break
        except Exception as exc:  # noqa: BLE001 - diagnostics never mask the loss itself
            info['error'] = repr(exc)
        return info

    def runner_lost(self, event: dict, out: Path, work: Path, step: str, session_started: float | None = None):
        """RUNBOOK A.8: record the loss, restart the dedicated instance, re-run affected roots whole (A.5)."""
        event['last_request'] = self.last_request(work)
        try:
            restart = self.restart_service('runner_lost', step)
        except Stop as exc:
            self.log_event({'kind': 'runner_lost', 'phase': step, 'detected_utc': stamp(), 'runner_event': event,
                            'restart_failed': str(exc.args[0])}, out, step)
            raise
        event['stopped_instance'] = {k: (restart.get('previous_instance') or {}).get(k)
                                     for k in ('returncode', 'stopped_utc', 'killed')}
        return self.resume_interrupted(out, work, step, 'runner_lost', restart=restart, event=event,
                                       session_started=session_started)

    def collect(self, argv, step: str, out: Path, work: Path, resume) -> None:
        """One collector session; with the watchdog on, a runner loss restarts the service and resumes."""
        if not self.watchdog_on():
            self.cmd(argv, log=f'{step}.log', env=self.ollama_env())
            return
        while True:
            started = time.time()
            event = self.watched_cmd(argv, log=f'{step}.log')
            if event is None:
                return
            self.runner_lost(event, out, work, step, session_started=started)
            argv = resume

    def watched_cmd(self, argv, *, log: str) -> dict | None:
        """Run the collector while polling the dedicated instance; None, or the loss record."""
        print('RUN', argv, '(watched)', flush=True)
        spec = self.config['watchdog']
        watchdog = RunnerWatchdog(self.ollama, spec)
        with (self.batch / log).open('a') as f:
            proc = subprocess.Popen(argv, cwd=self.paper, stdout=f, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, **self.ollama_env()))
        event = None
        try:
            while proc.poll() is None:
                event = watchdog.check()
                if event is not None:
                    break
                time.sleep(float(spec['poll_seconds']))
        finally:
            if proc.poll() is None:
                stopped = stop_tree(proc.pid)
                proc.wait()
                if event is not None:
                    event['collector'] = {'pid': proc.pid, 'stopped': stopped, 'returncode': proc.returncode}
        if event is None and proc.returncode != 0:
            event = watchdog.check()  # a collector that failed because the server died near the end
            if event is None:
                raise subprocess.CalledProcessError(proc.returncode, argv)
            event['collector'] = {'pid': proc.pid, 'returncode': proc.returncode}
        return event

    # -- model service -------------------------------------------------------
    def ollama_env(self) -> dict:
        return {'OLLAMA_BASE_URL': self.state['ollama']['url'], 'OMP_NUM_THREADS': '1',
                'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'AR_HARNESS_ROOT': str(self.harness)}

    def ollama_alive(self) -> bool:
        return self.ollama is not None and self.ollama.alive() and self.ollama.health() is not None

    def model_ps(self) -> dict:
        with urlopen(self.state['ollama']['url'] + '/api/ps', timeout=15) as response:
            return json.load(response)

    def check_offload(self, where: str) -> None:
        processes = self.model_ps()
        (self.batch / f'gpu_offload_{where}.json').write_text(json.dumps(
            {'label': self.label, 'utc': stamp(), 'processes': processes}, indent=2) + '\n')
        loaded = next((m for m in processes['models'] if m.get('name', m.get('model')) == MODEL), None)
        self.gpu['assert_full_offload'](loaded, where)
        if loaded.get('digest') != DIGEST:
            raise Stop(f'STOP: {where}: loaded model digest differs from the author pin')
        self.gpu['check_gpu']()

    def select_card(self) -> str:
        wanted = self.config.get('gpu_uuid', 'auto')
        deadline = time.monotonic() + float(self.config.get('gpu_wait_seconds', 0))
        while True:
            rows, eligible = self.gpu['gpu_rows']()
            if wanted != 'auto':
                eligible = [r for r in eligible if r.split(',')[1].strip() == wanted]
            with (self.batch / 'gpu_wait.jsonl').open('a') as f:
                f.write(json.dumps({'label': self.label, 'utc': stamp(), 'rows': rows, 'eligible': eligible}) + '\n')
            if eligible:
                return max(eligible, key=lambda r: int(r.split(',')[3].strip()))
            if time.monotonic() > deadline:
                raise Stop('STOP: no card with enough free memory (co-tenancy margin) within the wait limit')
            time.sleep(60)

    # -- phases --------------------------------------------------------------
    def check_heads(self) -> tuple[str, str]:
        paper_head = self.git(self.paper, 'rev-parse', 'HEAD')
        if paper_head != self.git(self.paper, 'ls-remote', self.remote, 'refs/heads/main').split()[0]:
            raise Stop('STOP: paper checkout is not at the remote main head')
        harness_head = self.git(self.harness, 'rev-parse', 'HEAD')
        pin_file = self.paper / 'r1/scripts/HARNESS_PIN_C3'
        if not pin_file.exists() or pin_file.read_text().strip() != harness_head:
            raise Stop(f'STOP: harness head {harness_head} differs from r1/scripts/HARNESS_PIN_C3')
        return paper_head, harness_head

    def preconditions(self) -> None:
        plan = (self.paper / 'docs/r1/PLAN.md').read_text()
        missing = [row for row in ROWS if row not in plan]
        if missing:
            raise Stop(f'STOP: PLAN §10 lacks the author rows {missing}')
        paper_head, harness_head = self.check_heads()
        self.state.update(paper_head_at_launch=paper_head, harness_head_at_launch=harness_head)
        self.save()
        self.start_service()

    def start_service(self, generation: int = 0) -> None:
        """Paper A check, card, dedicated Ollama, digest, load probe, offload (generation > 0: a restart)."""
        # PLAN §10 (19 Oct): Paper A coordination before any Paper B GPU launch.
        try:
            self.state['paper_a_check'] = paper_a_check(self.config['paper_a_check'], self.host)
        except Stop as exc:
            if len(exc.args) > 1:
                self.state['paper_a_check'] = exc.args[1]
            self.save()
            raise
        self.save()
        self.state['gpu'] = self.select_card()
        uuid = self.state['gpu'].split(',')[1].strip()
        self.gpu['check_gpu']()
        spec = self.config['ollama']
        restart = {'generation': generation, 'reuse_models': True} if generation else {}
        port, models_dir = spec.get('port'), None
        if generation:  # a restart reuses the batch's port and models directory
            previous = self.state.get('ollama') or {}
            port, models_dir = port or previous.get('port'), previous.get('models_dir')
        self.ollama = OllamaInstance(self.batch, spec['binary'], port=port, models_dir=models_dir,
                                     seed_models_from=spec.get('seed_models_from'), gpu_uuid=uuid,
                                     label=self.label, start_timeout=float(spec.get('start_timeout', 120)), **restart)
        self.state['ollama'] = self.ollama.start()
        self.save()
        if not spec.get('seed_models_from') and self.state['ollama'].get('models_seeded') != 'reused':
            self.ollama.pull(MODEL)
        with urlopen(self.ollama.url + '/api/tags', timeout=15) as response:
            tags = json.load(response)
        found = next((m for m in tags['models'] if m['name'] == MODEL), None)
        if found is None or found['digest'] != DIGEST:
            raise Stop('STOP: Ollama digest differs from the author pin')
        payload = json.dumps({'model': MODEL, 'prompt': 'Reply OK', 'stream': False, 'keep_alive': -1,
                              'options': {'num_predict': 1}}).encode()
        with urlopen(Request(self.ollama.url + '/api/generate', data=payload,
                             headers={'Content-Type': 'application/json'}), timeout=300) as response:
            json.load(response)
        xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
        selected = next((g for g in xml.findall('gpu') if g.findtext('uuid') == uuid), None)
        if selected is None or not selected.findall('./processes/process_info'):
            raise Stop('STOP: no process on the selected GPU after loading')
        self.state['model_loaded'] = True
        self.check_offload('load_probe' if not generation else f'load_probe_r{generation}')
        self.save()

    def liveness(self) -> None:
        live = self.config['liveness']
        out = self.paper / 'results/r1/engineering' / f'liveness_c3_{stamp()}'
        self.cmd([self.py, '-m', 'r1.liveness', '--run', '--manager', 'langgraph',
                  '--memory-mode', live['memory_mode'], '--nodes', *self.config['nodes'],
                  '--instances', str(live['instances']), '--runs', str(live['runs']),
                  '--transport-max-attempts', str(self.config['transport_max_attempts']),
                  '--out', str(out), '--work', str(self.batch / 'liveness_work')],
                 log='liveness.log', env=self.ollama_env())
        report = json.loads((out / 'liveness.json').read_text())
        nodes = self.config['nodes']
        eligible = [n for n in nodes if report['nodes'].get(n, {}).get('pass')]
        self.state['steps']['liveness'].update(
            out=str(out), eligible_nodes=eligible, excluded_nodes=[n for n in nodes if n not in eligible],
            verdicts={n: report['nodes'][n].get('criteria') for n in nodes if n in report['nodes']})
        self.save()
        self.commit('Record C3 label sweep D28 liveness (memory on)', [out], 'liveness')
        if len(eligible) < int(self.config['min_live_nodes']):
            raise Stop(f'STOP: only {len(eligible)} nodes passed D28 liveness '
                       f'(< {self.config["min_live_nodes"]}); the author decides')

    def require_liveness(self, nodes, memory_mode) -> None:
        from r1.liveness import load_liveness_manifest, require_live
        manifest = load_liveness_manifest(Path(self.state['steps']['liveness']['out']) / 'liveness.json')
        arm_role = 'contrast' if memory_mode == 'none' else 'primary'
        require_live(list(nodes), manifest, memory_mode=memory_mode, arm_role=arm_role)

    def sweep(self, memory_mode: str) -> None:
        step = f'sweep_{memory_mode}'
        entry = self.state['steps'][step]
        eligible = self.state['steps']['liveness']['eligible_nodes']
        self.require_liveness(eligible, memory_mode)  # D28 gate first
        base = [self.py, '-m', 'r1.headroom.e1b_collect']
        previous = Path(entry['out']) if entry.get('out') else None
        if previous is not None and (previous / 'manifest.json').exists():
            # RUNBOOK A.5: resume an interrupted sweep from its last completed campaign root.
            out, work = previous, Path(entry['work'])
            resume = [*base, '--resume', str(out), '--workers', str(self.config['workers'])]
            self.resume_interrupted(out, work, step, 'process_restart', restart=self.pending_restart)
            self.pending_restart = None
            self.collect_sessions(out, work, step, resume, eligible, memory_mode)
            return
        if previous is not None and previous.exists():
            if any(previous.iterdir()):
                raise Stop(f'STOP: {previous} exists without a collector manifest and is not empty; '
                           'author decision required')
            previous.rmdir()  # created by this batch's collector, which died before writing anything
            self.log_event({'kind': 'process_restart', 'phase': step, 'detected_utc': stamp(),
                            'note': f'collector never started: empty {previous} removed; the sweep starts fresh',
                            'service_restart': self.pending_restart}, None, step)
            self.pending_restart = None
        if self.pending_restart is not None:  # restarted before this sweep had started any collector
            self.log_event({'kind': 'process_restart', 'phase': step, 'detected_utc': stamp(),
                            'note': 'restart before the sweep started', 'service_restart': self.pending_restart},
                           None, step)
            self.pending_restart = None
        out = self.paper / 'results/r1/pilot' / f'C3_sweep_{memory_mode}_{stamp()}'
        work = self.batch / f'c3_{memory_mode}_work'
        if out.exists():
            raise Stop('STOP: sweep destination already exists; no overwrite')
        self.state['steps'][step].update(out=str(out), work=str(work))
        self.save()
        extra = {'c3_label_sweep': {
            'schema': 'r1.c3_label_sweep/1', 'memory_mode': memory_mode,
            'arm_role': 'contrast' if memory_mode == 'none' else 'primary', 'batch': str(self.batch),
            'liveness': self.state['steps']['liveness']['out'],
            'paper_a_check': self.state.get('paper_a_check', {}).get('verdict'),
            'ollama': {k: self.state['ollama'].get(k) for k in ('port', 'pid', 'models_dir')},
            'gpu': self.state.get('gpu'), 'audit': 'pending (r1/c3/audit.py)',
            'audit_seeds': self.config['audit']['seeds'], 'nodes_pending': self.config['nodes_pending']}}
        label_args = ['--label', 'DRYRUN', '--split', 'engineering'] if self.dryrun else \
            ['--label', 'PILOT', '--split', 'c3_labels']
        resume = [*base, '--resume', str(out), '--workers', str(self.config['workers'])]
        self.collect([*base, '--manager', 'langgraph', '--roots-only', '--points', '--reps', '0',
                      '--audit-seeds', '0', '--nodes', *eligible, '--instances', str(self.config['instances']),
                      '--runs', str(self.config['runs']), '--verify-split-policy', 'vary', '--new-campaign-versions',
                      '--memory-mode', memory_mode,
                      '--transport-max-attempts', str(self.config['transport_max_attempts']),
                      '--root-failures', 'record', '--extra-manifest', json.dumps(extra),
                      '--workers', str(self.config['workers']), '--out', str(out), '--work', str(work), *label_args],
                     step, out, work, resume)
        self.collect_sessions(out, work, step, resume, eligible, memory_mode)

    def collect_sessions(self, out: Path, work: Path, step: str, resume: list, eligible, memory_mode) -> None:
        """Resume sessions until one finds no job; then gates, offload check, archive, commit."""
        for _ in range(int(self.config['max_collect_sessions'])):
            manifest = json.loads((out / 'manifest.json').read_text())
            if manifest['sessions'] and manifest['sessions'][-1]['jobs_before'] == 0:
                break
            if not self.ollama_alive():
                if not self.watchdog_on():
                    break  # a dead model service: the gates below record it and stop
                loss = RunnerWatchdog(self.ollama, self.config['watchdog']).check() or \
                    {'kind': 'unhealthy_between_sessions', 'detected_utc': utc_iso()}
                self.runner_lost(loss, out, work, step)
            self.gpu['check_gpu']()
            self.collect(resume, step, out, work, resume)
        else:
            raise Stop('STOP: collector failed to reach a zero-job session')
        checks = self.collection_gates(out, work, eligible, memory_mode)
        self.check_offload(f'{memory_mode}_collection')
        self.archive(out, work)
        self.state['steps'][step]['checks'] = checks
        self.save()
        self.commit(f'Record C3 label sweep roots ({memory_mode})', [out], step)

    def collection_gates(self, out: Path, work: Path, nodes, memory_mode) -> dict:
        """Gates of one sweep; every outcome is written to disk before any STOP is raised."""
        manifest = json.loads((out / 'manifest.json').read_text())
        expected = len(nodes) * int(self.config['instances'])
        roots = sorted((out / 'roots').glob('*.json'))
        failure_dir = out / 'failures'
        failures = [json.loads(p.read_text()) for p in sorted(failure_dir.glob('*.json'))] \
            if failure_dir.exists() else []
        calls, failed_calls, parse_failures, summaries, retried = [], [], [], [], []
        for path in sorted((work / 'roots').rglob('root_events.jsonl')):  # final roots, not interrupted attempts
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get('event_type') == 'llm_call':
                    calls.append(item)
                    if not item['payload'].get('parse_ok', True):
                        parse_failures.append(item)
                    if len(item['payload'].get('transport_attempts', [])) > 1:
                        retried.append({'trial_id': item.get('trial_id'),
                                        'attempts': item['payload']['transport_attempts']})
                elif item.get('event_type') == 'llm_call_failed':
                    failed_calls.append({'trial_id': item.get('trial_id'), **item['payload']})
        for path in sorted((work / 'roots').rglob('root_trials.jsonl')):
            for line in path.read_text().splitlines():
                if line.strip():
                    summaries.append(json.loads(line).get('proposal_summary') or '')
        check = {'label': manifest['label'], 'memory_mode': memory_mode, 'expected_roots': expected,
                 'roots': len(roots), 'root_failures': len(failures), 'llm_calls': len(calls),
                 'llm_calls_failed': len(failed_calls), 'llm_calls_retried': len(retried),
                 'retried_calls': retried[:20], 'parse_failures': len(parse_failures),
                 'proposal_examples': summaries[:5], 'manager_kind': manifest['manager']['kind'],
                 'transport_max_attempts': manifest['manager'].get('transport_max_attempts', 1),
                 'verify_split_policy': manifest.get('verify_split_policy'),
                 'action_versions': manifest.get('action_versions'), 'written_utc': stamp()}
        if (work / 'interrupted').exists():  # RUNBOOK A.5: calls spent on attempts that were re-run whole
            check['interrupted_attempts'] = {
                'root_attempts': len([d for d in (work / 'interrupted').glob('*/roots/*') if d.is_dir()]),
                'llm_calls': sum(1 for path in (work / 'interrupted').rglob('root_events.jsonl')
                                 for line in path.read_text().splitlines()
                                 if line.strip() and json.loads(line).get('event_type') == 'llm_call'),
                'interruptions': len(self.state.get('interruptions', []))}
        (out / 'collection_checks.json').write_text(json.dumps(check, indent=2) + '\n')
        if failures or len(roots) != expected:
            payload = {'label': self.label, 'written_utc': stamp(), 'n_failures': len(failures),
                       'missing_roots': expected - len(roots) - len(failures), 'failures': failures,
                       'llm_calls_failed': failed_calls}
            (out / 'collection_failures.json').write_text(json.dumps(payload, indent=2) + '\n')
            raise Stop(f'STOP: {len(failures)} root campaign failures, {len(roots)}/{expected} roots complete; '
                       f'records in {out}/failures and collection_failures.json (no automatic retry)')
        if manifest['manager']['kind'] != 'langgraph':
            raise Stop('STOP: sweep manifest is not LLM-backed')
        if not calls or not any(not re.fullmatch(r'\w+\s+\S+\s+->\s+\S+', s) for s in summaries):
            raise Stop('STOP: no demonstrated LLM proposals in the root ledgers')
        if len(parse_failures) / len(calls) > float(self.config['max_parse_failure_rate']):
            (out / 'parse_failure_examples.json').write_text(json.dumps(parse_failures[:5], indent=2) + '\n')
            raise Stop('STOP: manager parse failures exceed the configured rate')
        return {k: v for k, v in check.items() if k not in ('retried_calls', 'proposal_examples')}

    def archive(self, out: Path, work: Path) -> None:
        """Copy root ledgers and events into the run; the audit stage then needs only committed inputs."""
        archive = out / 'provenance' / 'ledgers'
        paths = sorted((work / 'roots').rglob('*.jsonl'))
        if (work / 'interrupted').exists():  # RUNBOOK A.5: partial attempts of re-run roots, kept as provenance
            paths += sorted((work / 'interrupted').rglob('*.jsonl'))
        for path in paths:
            target = archive / path.relative_to(work)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        manifest = json.loads((out / 'manifest.json').read_text())
        for noise in manifest['noise'].values():
            source = Path(noise['source'])
            if source.is_absolute() and source.is_relative_to(self.paper):
                noise['original_source'] = noise['source']
                noise['source'] = str(source.relative_to(self.paper))
        manifest['archival_paths'] = 'Root ledgers/events under provenance/ledgers; noise sources repository-relative.'
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    def index(self) -> None:
        """The sweep index: the input contract of the audit stage (``r1/c3/audit.py``)."""
        sweeps = []
        for mode in self.config['memory_modes']:
            entry = self.state['steps'][f'sweep_{mode}']
            out = Path(entry['out'])
            sweeps.append({'memory_mode': mode, 'arm_role': 'contrast' if mode == 'none' else 'primary',
                           'out': str(out.relative_to(self.paper)),
                           'manifest': str((out / 'manifest.json').relative_to(self.paper)),
                           'ledgers': str((out / 'provenance/ledgers/roots').relative_to(self.paper)),
                           'commit': entry.get('commit')})
        live = self.state['steps']['liveness']
        index = {'schema': 'r1.c3_sweep_index/1', 'label': self.label, 'written_utc': stamp(),
                 'nodes': live['eligible_nodes'], 'excluded_nodes': live['excluded_nodes'],
                 'instances': self.config['instances'], 'runs': self.config['runs'],
                 'liveness': str(Path(live['out']).relative_to(self.paper)),
                 'harness_commit': self.state.get('harness_head_at_launch'), 'sweeps': sweeps,
                 'nodes_pending': self.config['nodes_pending'],
                 'audit': {'status': 'pending', 'seeds': self.config['audit']['seeds'],
                           'label_seeds': self.config['audit']['seeds'][:self.config['audit']['label_seeds']],
                           'evaluation_seeds': self.config['audit']['seeds'][self.config['audit']['label_seeds']:],
                           'stage': f'r1/c3/audit.py (separate stage; C3_DESIGN §4: K = '
                                    f'{len(self.config["audit"]["seeds"])} common fresh joint seeds per '
                                    'non-inert evaluated proposal; first half label, second half evaluation)'}}
        path = self.paper / 'results/r1/pilot' / f'C3_sweep_index_{stamp()}.json'
        path.write_text(json.dumps(index, indent=2) + '\n')
        self.state['steps']['index']['path'] = str(path)
        self.save()
        self.commit('Record C3 label sweep index (audit pending)', [path], 'index')

    def phases(self) -> list:
        return [*PHASES_FIXED, *[f'sweep_{m}' for m in self.config['memory_modes']], 'index']

    def pending_phase(self) -> str | None:
        return next((p for p in self.phases() if not self.state['steps'].get(p, {}).get('completed')), None)

    def main(self) -> None:
        self.load_previous_state()
        if self.state.get('finished_utc'):
            raise Stop('STOP: this C3 sweep batch already finished; start a new batch')
        if not self.dryrun and self.host not in set(self.config['allowed_hosts']):
            raise Stop(f'STOP: unauthorized execution host {self.host}')
        self.state.setdefault('runners', []).append({'pid': os.getpid(), 'started_utc': stamp()})
        self.save()
        self.phase('preconditions', self.preconditions)
        if self.ollama is None:
            pending = self.pending_phase()
            started = pending in self.state['steps']
            if pending is None or (pending == 'index' and not started):
                pass  # nothing left that needs the model service
            elif self.config['resume']['sweeps'] and (self.resumable(pending) or not started):
                # RUNBOOK A.5: a restarted runner resumes; its sweep phase logs the interruption.
                self.pending_restart = self.restart_service('process_restart', pending)
                if not self.resumable(pending):
                    self.log_event({'kind': 'process_restart', 'phase': pending, 'detected_utc': stamp(),
                                    'note': 'restart before the phase started', 'service_restart': self.pending_restart},
                                   None, None)
                    self.pending_restart = None
            else:
                raise Stop('STOP: the batch Ollama instance belongs to an earlier process; a restart after '
                           'preconditions is an author decision (start a new batch)')
        self.phase('liveness', self.liveness)
        for mode in self.config['memory_modes']:
            self.phase(f'sweep_{mode}', lambda mode=mode: self.sweep(mode))
        self.phase('index', self.index)

    def finish(self, reason) -> dict:
        if self.ollama is not None:
            try:
                self.state['ollama'] = self.ollama.stop()
            except Exception as exc:  # noqa: BLE001 - recorded; never masks the stop reason
                self.state['ollama_stop_error'] = repr(exc)
        if not self.state.get('finished_utc'):
            self.state['finished_utc'] = stamp()
            self.state['stop_reason'] = reason
        self.save()
        summary = {'label': self.label, 'stop_reason': self.state.get('stop_reason'),
                   'finished_utc': self.state['finished_utc'],
                   'steps': {k: {kk: v.get(kk) for kk in ('completed', 'commit', 'out', 'checks')}
                             for k, v in self.state['steps'].items()}}
        (self.batch / 'c3_sweep_summary.json').write_text(json.dumps(summary, indent=2, default=str) + '\n')
        print('FINISHED', json.dumps(summary, default=str), flush=True)
        return summary


def build_runner(config_path=None) -> SweepRunner:
    batch = Path(os.environ['R1_BATCH_DIRECTORY'])
    paper = Path(os.environ.get('R1_PAPER_ROOT', str(Path(__file__).resolve().parents[2])))
    harness = Path(os.environ['AR_HARNESS_ROOT'])
    python = os.environ.get('R1_C3_PY', str(harness / '.venv/bin/python'))
    config = load_config(config_path or os.environ.get('R1_C3_CONFIG'))
    return SweepRunner(config, batch=batch, paper=paper, harness=harness, python=python)


def entrypoint(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=None, help='JSON config (nodes, instances, paper_a_check, ollama, ...)')
    ap.add_argument('--check-config', action='store_true',
                    help='validate the config (defaults overlaid), print it and exit; starts nothing')
    args = ap.parse_args(argv)
    if args.check_config:
        try:
            config = load_config(args.config or os.environ.get('R1_C3_CONFIG'))
        except Stop as exc:
            print(exc.args[0], flush=True)
            return 2
        print(json.dumps(config, indent=2), flush=True)
        return 0
    runner = build_runner(args.config)
    try:
        runner.main()
    except Stop as exc:
        if 'already finished' in str(exc.args[0]):
            print(exc.args[0], flush=True)
            return 3
        runner.finish(str(exc.args[0]))
        return 2
    except Exception as exc:  # noqa: BLE001 - every stop is recorded with its class
        runner.finish(f'{type(exc).__name__}: {exc}')
        return 1
    runner.finish(None)
    return 0


if __name__ == '__main__':
    raise SystemExit(entrypoint())
