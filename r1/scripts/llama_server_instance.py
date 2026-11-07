"""A dedicated llama.cpp ``llama-server`` per batch (RUNBOOK A.10; PLAN §10 R1-INFER-LLAMACPP, 25 Oct 2026).

The llama.cpp counterpart of ``r1/scripts/ollama_instance.py``.  A batch gets a
server that nothing else shares:

* launched as ``llama-server -m <gguf> --host 127.0.0.1 --port <p> -ngl <n>
  -c <ctx> --alias <alias> -np 1`` (plus configured extra arguments) in its own
  process group.  ``-np 1`` gives the server a single slot, so requests are
  never batched with each other and each request's ``seed`` (D26) drives its
  own sampling; the environment is stripped of every ``LLAMA_ARG_*`` variable
  (llama.cpp reads them as defaults for flags not on the command line) and of
  ``LLAMA_API_KEY``, so the recorded argv is the whole configuration;
* refuses a port anything already listens on;
* ready when ``/health`` answers 200 (llama-server answers 503 while it loads
  the model); identity from ``/v1/models`` (the alias) and ``/props``
  (``model_path`` where the build reports it);
* PID, process group, port, model path, full argv, the server's command line
  as read back from ``/proc``, the build (``llama-server --version``) and times
  recorded in ``<batch>/llama_server_<port>[_r<g>].json``; its log (stdout and
  stderr) in ``llama_server_<port>[_r<g>].log``;
* ``offload_check`` decides full GPU offload by two routes (author's revised
  acceptance, runbook 25 Oct; llama.cpp v0.7.0 on deepthought printed no
  offload line at default verbosity): (i) the log line ``offloaded N/N layers``
  (``N/M`` with M != N is a STOP even if the memory looks fine); else (ii) the
  server pid listed by ``nvidia-smi --query-compute-apps`` on the configured
  GPU uuid with used memory >= the pinned ``footprint_mib`` (refused if unset).
  A CPU-fallback line stops both routes; the route that passed is recorded;
* ``stop()`` signals only the process group it started, after checking the
  PID still leads it.

Restarts and orphans (RUNBOOK A.5 / A.8) as for Ollama: ``generation`` > 0
names the ``_r<g>`` record and log; ``orphan_matches`` / ``stop_orphan`` signal
an earlier instance of the same batch only when its pid is alive, owned by this
user, still leads the recorded process group, and its command line (binary,
``--port``, ``-m`` path and every other argument) equals the recorded argv.
Another user's process is never signalled.

The pins themselves (GGUF sha256, build string) are checked by the runner
before any start (``sha256_file``, ``build_info``).

Fake-able: ``binary`` may be any executable taking these arguments
(the dry run uses ``r1/scripts/c3_fake_llama_server.py`` behind a shebang).

ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from r1.exam.cache_proc import process_start_ticks
from r1.exam.cooperative_lease import LeaseStop
from r1.scripts.ollama_instance import _utc, free_port, pid_alive, port_is_free

OFFLOAD_RE = re.compile(r'offloaded (\d+)/(\d+) layers to GPU')
GPU_BUFFER_RE = re.compile(r'\b(CUDA\d+) model buffer size\s*=\s*([\d.]+) MiB')
KV_BUFFER_RE = re.compile(r'\b(CUDA\d+|CPU) KV buffer size\s*=\s*([\d.]+) MiB')
CPU_FALLBACK_RE = re.compile(r'no usable GPU found|--gpu-layers option will be ignored|ggml_cuda_init: failed|'
                             r'no CUDA-capable device|CUDA driver version is insufficient', re.I)
VERSION_RE = re.compile(r'^version:\s*(\S+)\s*\(([^)]*)\)\s*$', re.M)
STRIPPED_ENV_PREFIX = 'LLAMA_ARG_'
STRIPPED_ENV = ('LLAMA_API_KEY',)
INTERPRETERS = re.compile(r'(python[\d.]*|sh|bash|dash)$')


def thinking_args(policy: dict | None) -> list[str]:
    """Opt-in exam thinking policy; callers verify flags against the pinned build's help."""
    if policy is None:
        return []
    mode = policy.get('mode')
    budget = policy.get('budget', 0)
    if mode not in ('off', 'on', 'always_on'):
        raise ValueError('thinking policy mode must be off, on or always_on')
    if isinstance(budget, bool) or not isinstance(budget, int) or (mode == 'off' and budget != 0) or (mode != 'off' and budget < 1):
        raise ValueError('off has budget 0; thinking-on requires a positive token budget')
    args = []
    if policy.get('off_switch') and mode != 'always_on':
        args += ['--chat-template-kwargs', json.dumps({'enable_thinking': mode == 'on'}, separators=(',', ':'))]
    if mode != 'off':
        args += ['--reasoning-budget', str(budget)]
    return args


def sha256_file(path: str | Path, chunk: int = 16 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            digest.update(block)
    return digest.hexdigest()


def parse_version(text: str) -> dict:
    """The ``version: <v> (<build/commit>)`` line, its version and the commit.

    Seen forms: ``version: 6873 (0e4a0cf2)`` and, llama.cpp v0.7.0 on deepthought,
    ``version: 0.7.0-dev (build 1, commit 620d222)``.
    """
    found = VERSION_RE.search(text)
    if not found:
        return {'version_line': None, 'build_number': None, 'commit': None}
    inner = found.group(2)
    commit = re.search(r'commit\s+([0-9a-f]{7,40})', inner) or re.fullmatch(r'\s*([0-9a-f]{7,40})\s*', inner)
    return {'version_line': found.group(0).strip(), 'build_number': found.group(1),
            'commit': commit.group(1) if commit else inner}


def build_info(binary: str, timeout: float = 60.0, capture=None) -> dict:
    """``<binary> --version``: the raw output, the ``version: <n> (<commit>)`` line and its parts.

    llama.cpp prints the version on stderr (CUDA builds may print device lines
    first); both streams are searched.
    """
    done = (capture([str(binary), '--version'], timeout=timeout) if capture is not None else
            subprocess.run([str(binary), '--version'], capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL))
    text = (done.stdout or '') + (done.stderr or '')
    return {'binary': str(binary), 'returncode': done.returncode, 'raw': text.strip()[-2000:], **parse_version(text)}


def offload_report(log_text: str) -> dict:
    """What the server log says about offload.  ``full`` = route (i): an ``offloaded N/N layers`` line with
    N > 0 and no CPU-fallback line (buffer lines are recorded, not required).  ``line`` is ``full``,
    ``partial`` or ``absent``."""
    offloaded = OFFLOAD_RE.findall(log_text)
    buffers = [{'device': d, 'mib': float(m)} for d, m in GPU_BUFFER_RE.findall(log_text)]
    kv = [{'device': d, 'mib': float(m)} for d, m in KV_BUFFER_RE.findall(log_text)]
    fallback = [line.strip() for line in log_text.splitlines() if CPU_FALLBACK_RE.search(line)][-5:]
    n, total = (int(offloaded[-1][0]), int(offloaded[-1][1])) if offloaded else (None, None)
    line = 'absent' if not offloaded else ('full' if total and n == total else 'partial')
    full = line == 'full' and not fallback
    reasons = []
    if line == 'absent':
        reasons.append('no "offloaded N/M layers to GPU" line in the server log')
    elif line == 'partial':
        reasons.append(f'offloaded {n}/{total} layers')
    if fallback:
        reasons.append('CPU fallback reported')
    return {'full': full, 'line': line, 'offloaded_layers': n, 'total_layers': total, 'gpu_model_buffers': buffers,
            'kv_buffers': kv, 'cpu_fallback_lines': fallback, 'reasons': reasons}


def parse_compute_apps(text: str) -> list[dict]:
    """Rows of ``nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader,nounits``."""
    rows = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(',')]
        if len(parts) != 3 or not parts[0].isdigit():
            continue
        rows.append({'pid': int(parts[0]), 'gpu_uuid': parts[1],
                     'used_mib': int(parts[2]) if parts[2].isdigit() else None})
    return rows


def gpu_compute_apps(timeout: float = 60.0, capture=None) -> list[dict] | None:
    """The GPU compute processes now (pid, GPU uuid, MiB), or None when ``nvidia-smi`` cannot be read."""
    try:
        argv=['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader,nounits']
        done = (capture(argv, timeout=timeout) if capture is not None else
                subprocess.run(argv, capture_output=True, text=True, timeout=timeout))
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_compute_apps(done.stdout) if done.returncode == 0 else None


def offload_check(log_text: str, *, pid: int | None, gpu_uuid: str | None, footprint_mib, apps) -> dict:
    """Full GPU offload by route (i) (log line N/N) or, when the build prints no such line, route (ii)
    (the server pid on ``gpu_uuid`` with used memory >= ``footprint_mib``).  A partial line or a
    CPU-fallback line is a STOP whatever the memory.  ``route`` names the route that passed (or None)."""
    report = offload_report(log_text)
    rows = [r for r in (apps or []) if r.get('pid') == pid]
    mine = next((r for r in rows if r.get('gpu_uuid') == gpu_uuid), None)
    memory = {'pid': pid, 'gpu_uuid': gpu_uuid, 'footprint_mib': footprint_mib,
              'used_mib': mine.get('used_mib') if mine else None, 'rows_of_pid': rows,
              'compute_apps_read': apps is not None}
    check = {**report, 'route': None, 'gpu_memory': memory}
    if report['cpu_fallback_lines']:
        check['full'] = False
        return check
    if report['line'] == 'full':
        check.update(full=True, route='log_line')
        return check
    if report['line'] == 'partial':
        check['full'] = False
        return check
    reasons = list(report['reasons'])  # route (i) unavailable: the build printed no offload line
    if not isinstance(footprint_mib, (int, float)) or isinstance(footprint_mib, bool) or footprint_mib <= 0:
        reasons.append('route (ii) refused: footprint_mib is not set (measure it with the probe and pin it)')
    elif apps is None:
        reasons.append('route (ii): nvidia-smi --query-compute-apps could not be read')
    elif mine is None:
        reasons.append(f'route (ii): server pid {pid} is not listed on {gpu_uuid} by nvidia-smi '
                       f'(rows of this pid: {rows})')
    elif mine.get('used_mib') is None or mine['used_mib'] < footprint_mib:
        reasons.append(f'route (ii): server pid {pid} uses {mine.get("used_mib")} MiB on {gpu_uuid}, '
                       f'below the pinned footprint {footprint_mib} MiB')
    else:
        check.update(full=True, route='gpu_memory', reasons=[])
        return check
    check.update(full=False, reasons=reasons)
    return check


def _get_json(url: str, timeout: float) -> tuple[int | None, object]:
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b'null')
        except ValueError:
            return exc.code, None
    except (OSError, ValueError):
        return None, None


class LlamaServerInstance:
    MODEL_LOSS_KIND = 'model_missing'
    BACKEND = 'llamacpp'

    def __init__(self, batch_dir: str | Path, binary: str, *, model_path: str | Path, alias: str,
                 port: int | None = None, n_gpu_layers: int = 999, ctx_size: int = 8192,
                 gpu_uuid: str | None = None, label: str = 'ENGINEERING_ONLY', extra_args=(),
                 env_extra: dict[str, str] | None = None, start_timeout: float = 120.0,
                 generation: int = 0, thinking_policy: dict | None = None) -> None:
        self.batch = Path(batch_dir).resolve()
        self.binary = str(binary)
        self.model_path = str(model_path)
        self.alias = str(alias)
        self.port = int(port) if port else free_port()
        self.n_gpu_layers, self.ctx_size = int(n_gpu_layers), int(ctx_size)
        self.gpu_uuid, self.label = gpu_uuid, label
        self.extra_args = [str(a) for a in extra_args]
        self.thinking_policy = dict(thinking_policy) if thinking_policy is not None else None
        self.thinking_argv = thinking_args(self.thinking_policy)
        self.env_extra = dict(env_extra or {})
        self.start_timeout = start_timeout
        self.generation = int(generation)
        self.process: subprocess.Popen | None = None
        suffix = f'_r{self.generation}' if self.generation else ''
        self.record_path = self.batch / f'llama_server_{self.port}{suffix}.json'
        self.log_path = self.batch / f'llama_server_{self.port}{suffix}.log'
        self.record: dict = {}
        self.b1_record_identity = None
        self.dryrun_record_identity = None

    @property
    def url(self) -> str:
        return f'http://127.0.0.1:{self.port}'

    @property
    def openai_base_url(self) -> str:
        return self.url + '/v1'

    @property
    def argv(self) -> list[str]:
        return [self.binary, '-m', self.model_path, '--host', '127.0.0.1', '--port', str(self.port),
                '-ngl', str(self.n_gpu_layers), '-c', str(self.ctx_size), '--alias', self.alias, '-np', '1',
                *self.extra_args, *self.thinking_argv]

    def env(self) -> tuple[dict[str, str], list[str]]:
        env, removed = {}, []
        for key, value in os.environ.items():
            if key.startswith(STRIPPED_ENV_PREFIX) or key in STRIPPED_ENV:
                removed.append(key)
            else:
                env[key] = value
        if self.gpu_uuid:
            env['CUDA_VISIBLE_DEVICES'] = self.gpu_uuid
        env.update(self.env_extra)
        return env, sorted(removed)

    def _save(self) -> None:
        def write():
            if getattr(self, 'b1_containment', None) is not None:
                from r1.exam.b1_state_preserve import publish_server_record
                self.b1_record_identity = publish_server_record(
                    self.record_path, self.record, self.b1_record_identity)
            elif getattr(self, 'label', None) == 'DRYRUN':
                from r1.exam.b1_state_preserve import publish_dryrun_server_record
                self.dryrun_record_identity = publish_dryrun_server_record(
                    self.record_path, self.record, getattr(self, 'dryrun_record_identity', None))
            else:
                self.record_path.write_text(json.dumps(self.record, indent=2) + '\n')
        if getattr(self, 'b1_containment', None) is not None:
            self.b1_containment.write_active(write)
        else:
            write()

    def health(self, timeout: float = 2.0) -> dict | None:
        """``/health`` body when the server is ready (HTTP 200), else None (down, or 503 while loading)."""
        status, body = _get_json(self.url + '/health', timeout)
        return body if status == 200 and isinstance(body, dict) else None

    def models(self, timeout: float = 15.0) -> dict | None:
        status, body = _get_json(self.url + '/v1/models', timeout)
        return body if status == 200 and isinstance(body, dict) else None

    def props(self, timeout: float = 15.0) -> dict | None:
        status, body = _get_json(self.url + '/props', timeout)
        return body if status == 200 and isinstance(body, dict) else None

    def model_ids(self, timeout: float = 15.0) -> list[str] | None:
        models = self.models(timeout)
        if models is None:
            return None
        return [str(m.get('id')) for m in models.get('data') or [] if isinstance(m, dict)]

    def model_loaded(self, timeout: float = 10.0) -> bool | None:
        """True / False: the alias is / is not listed by ``/v1/models``; None: unknown (no answer)."""
        ids = self.model_ids(timeout)
        return None if ids is None else self.alias in ids

    def chat(self, content: str, *, max_tokens: int = 1, seed: int = 0, timeout: float = 600.0,
             extra: dict | None = None) -> dict:
        payload = json.dumps({'model': self.alias, 'messages': [{'role': 'user', 'content': content}],
                              'max_tokens': max_tokens, 'temperature': 0, 'seed': seed, **(extra or {})}).encode()
        with urlopen(Request(self.openai_base_url + '/chat/completions', data=payload,
                             headers={'Content-Type': 'application/json'}), timeout=timeout) as response:
            return json.load(response)

    def log_text(self) -> str:
        return self.log_path.read_text(errors='replace') if self.log_path.exists() else ''

    def offload(self, footprint_mib=None, apps=None) -> dict:
        """``offload_check`` for this server (``apps`` read from nvidia-smi now unless given)."""
        if apps is None:
            apps = gpu_compute_apps()
        pid = (self.record or {}).get('pid') or (self.process.pid if self.process else None)
        return offload_check(self.log_text(), pid=pid, gpu_uuid=self.gpu_uuid, footprint_mib=footprint_mib, apps=apps)

    def start(self, *, build: dict | None = None, model_sha256: str | None = None,
              preserve_on_failure: bool = False, lease_fd: int | None = None,
              b1_lease_fd: int | None = None, b1_containment=None, b1_cancelled=None) -> dict:
        """Start the native server; cooperative Stage A passes the inherited lease FD.

        ``lease_fd`` must be the verified lease descriptor of this process.  When
        it is ``None`` and ``TRACKX_GPU_LEASE_FD`` is present, the environment
        contract is re-verified and that FD is used (the cooperative chain never
        runs a native server without it).  The server must retain the same open
        file description: once it is healthy, ``lease_inheritance`` is proved
        with ancestor->descendant ``kcmp(KCMP_FILE)`` plus /proc FD dev/ino,
        pid/start-ticks/parent-pid identity; any mismatch is a STOP before the
        caller may issue a request.
        """
        if self.process is not None:
            raise RuntimeError('STOP: this instance was already started')
        if lease_fd is not None and (type(lease_fd) is not int or lease_fd < 3):
            raise RuntimeError('STOP: explicit lease FD invalid')
        if b1_lease_fd is not None and (type(b1_lease_fd) is not int or b1_lease_fd < 3 or lease_fd is not None):
            raise RuntimeError('STOP: B1 lease FD invalid or conflicts with Stage A')
        if not port_is_free(self.port):
            raise RuntimeError(f'STOP: port {self.port} is in use; a dedicated instance never shares a server')
        if not Path(self.model_path).is_file():
            raise RuntimeError(f'STOP: GGUF file not found: {self.model_path}')
        self.b1_containment = b1_containment
        def prepare_log():
            self.batch.mkdir(parents=True, exist_ok=True)
            return self.log_path.open('ab')
        log=b1_containment.write_active(prepare_log) if b1_containment is not None else prepare_log()
        env, removed = self.env()
        argv = self.argv
        if lease_fd is None and os.environ.get('TRACKX_GPU_LEASE_FD'):
            if b1_lease_fd is not None: raise RuntimeError('STOP: conflicting Stage A and B1 lease environments')
            from r1.exam.cache_runtime import verified_lease_fd
            lease_fd = verified_lease_fd()
        passed_fd=lease_fd if lease_fd is not None else b1_lease_fd
        try:
            if b1_containment is not None:
                if b1_lease_fd is None or lease_fd is not None:
                    raise RuntimeError('STOP: contained B1 server requires its B1 lease')
                self.b1_containment = b1_containment
                self.process = b1_containment.spawn('server', argv, env=env, stdout=log,
                                                    lease_fd=b1_lease_fd)
            else:
                self.process = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT,
                                                stdin=subprocess.DEVNULL, start_new_session=True,
                                                pass_fds=() if passed_fd is None else (passed_fd,))
        finally:
            log.close()
        try:
            server_ticks = process_start_ticks(self.process.pid)
        except (RuntimeError, ValueError):
            server_ticks = None
        self.record = {'label': self.label, 'backend': self.BACKEND, 'binary': self.binary, 'argv': argv,
                       'pid': self.process.pid, 'pgid': os.getpgid(self.process.pid), 'port': self.port,
                       'start_ticks': server_ticks,
                       'url': self.url, 'openai_base_url': self.openai_base_url, 'model_path': self.model_path,
                       'model_sha256': model_sha256, 'alias': self.alias, 'n_gpu_layers': self.n_gpu_layers,
                       'ctx_size': self.ctx_size, 'parallel_slots': 1, 'gpu_uuid': self.gpu_uuid,
                       'env_removed': removed, 'build': build, 'log': str(self.log_path), 'started_utc': _utc()}
        if self.thinking_policy is not None:
            self.record['thinking_policy'] = self.thinking_policy
        if self.generation:
            self.record['generation'] = self.generation
        try:
            self.record['cmdline'] = proc_cmdline(self.process.pid)
        except OSError:
            self.record['cmdline'] = None
        self._save()
        # Capture the SAME-OFD lease inheritance proof BEFORE the readiness loop:
        # a server can exit before /health (template parser error, 32k OOM, ...) and
        # lease completion requires an inheritance proof on every server record.  The
        # FD is inherited at fork/exec, so ancestor->descendant kcmp and /proc FD
        # dev/ino work while the child is barely alive.  If the child is already gone
        # we cannot prove anything; fall through so the readiness loop records the
        # failed start (the completion then stays fail-closed), and if the child is
        # alive but the proof fails this is a genuine STOP.
        if lease_fd is not None:
            try:
                inheritance = self._verify_lease_inheritance(lease_fd, server_ticks)
            except Exception as exc:  # noqa: BLE001 - classified below
                self.record['lease_inheritance_capture'] = {
                    'captured': False, 'utc': _utc(), 'error': f'{type(exc).__name__}: {exc}'}
                try:
                    self._save()
                except OSError:
                    pass
                if self.process.poll() is None:
                    raise
            else:
                self.record['lease_inheritance'] = inheritance
                self.record['start_ticks'] = inheritance['server_start_ticks']
                server_ticks = inheritance['server_start_ticks']
                self._save()
        deadline = time.monotonic() + self.start_timeout
        last = None
        while time.monotonic() < deadline:
            if b1_cancelled is not None and b1_cancelled():
                raise RuntimeError('STOP: B1 server startup cancelled by monitor')
            if self.process.poll() is not None:
                # A server that exited before readiness is over, so its record must be
                # finalized here (stopped_utc/returncode): lease completion accounting
                # requires every observed server record to name a stop.  The process was
                # never healthy, so no request could have been served.
                self.record.update(exited_early=self.process.returncode, failed_utc=_utc(),
                                   stopped_utc=_utc(), returncode=self.process.returncode,
                                   stopped_before_ready=True,
                                   log_tail=self.log_text().splitlines()[-20:])
                self._save()
                raise RuntimeError(f'STOP: dedicated llama-server exited during start (rc={self.process.returncode})')
            status, body = _get_json(self.url + '/health', 2.0)
            last = {'status': status, 'body': body}
            if status == 200:
                if b1_lease_fd is not None:
                    from r1.exam.b1_lease import verify_server_fd
                    verify_server_fd(b1_lease_fd,self.process.pid)
                    if b1_containment is not None:
                        b1_containment.verify_live_lease(self.process,b1_lease_fd)
                if lease_fd is not None:
                    inheritance = self._verify_lease_inheritance(lease_fd, server_ticks)
                    self.record['lease_inheritance'] = inheritance
                    self.record['start_ticks'] = inheritance['server_start_ticks']
                    server_ticks = inheritance['server_start_ticks']
                try:  # the exec has happened by now: the command line is the server's own
                    self.record['cmdline'] = proc_cmdline(self.process.pid)
                except OSError:
                    pass
                self.record.update(healthy_utc=_utc(), health=body)
                self._save()
                return self.record
            time.sleep(0.2)
        self.record['last_health'] = last
        if not preserve_on_failure:
            self.stop()
        raise RuntimeError(f'STOP: dedicated llama-server did not become healthy (last /health: {last})')

    def _verify_lease_inheritance(self, lease_fd: int, server_ticks):
        """Prove the native server retained the inherited lease OFD, else STOP.

        The direction is the legal ancestor->descendant one: this process (the
        server's parent) kcmp-checks its descendant.  A missing FD, a different
        dev/ino, a different pid/start-ticks/parent or an EPERM kcmp is never
        treated as success.
        """
        from r1.exam.cache_runtime import verify_server_lease_inheritance
        try:
            return verify_server_lease_inheritance(self.process.pid, lease_fd, runner_pid=os.getpid(),
                                                   started_ticks=server_ticks)
        except LeaseStop as exc:
            self.record['lease_inheritance_failure'] = {
                'method': 'proc_fd_dev_ino_and_kcmp_file_ancestor_to_descendant',
                'lease_fd': lease_fd, 'server_pid': self.process.pid,
                'server_start_ticks': server_ticks, 'reason': str(exc), 'utc': _utc(),
                'kcmp_direction': 'ancestor->descendant', 'retry_permitted': False}
            try:
                self._save()
            except OSError:
                pass
            raise

    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self, timeout: float = 20.0) -> dict:
        """Stop only the process group this instance started; record the outcome."""
        if self.process is None:
            return self.record
        if getattr(self, 'b1_containment', None) is not None:
            self.b1_containment.stop_server(self.process)
        elif self.process.poll() is None:
            pgid = self.record.get('pgid')
            if pgid != os.getpgid(self.process.pid):
                raise RuntimeError('STOP: process group changed; refusing to signal')
            os.killpg(pgid, signal.SIGTERM)
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(pgid, signal.SIGKILL)
                self.process.wait(timeout=timeout)
                self.record['killed'] = True
        self.record.update(stopped_utc=_utc(), returncode=self.process.returncode)
        self._save()
        return self.record

    def returncode_info(self) -> dict:
        rc = None if self.process is None else self.process.poll()
        info: dict = {'returncode': rc}
        if rc is not None and rc < 0:
            try:
                info['signal'] = signal.Signals(-rc).name
            except ValueError:
                info['signal'] = f'signal {-rc}'
        return info

    def __enter__(self) -> 'LlamaServerInstance':
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def proc_cmdline(pid: int) -> list[str]:
    raw = Path(f'/proc/{int(pid)}/cmdline').read_bytes()
    return [part.decode(errors='replace') for part in raw.split(b'\0') if part]


def proc_uid(pid: int) -> int:
    for line in Path(f'/proc/{int(pid)}/status').read_text().splitlines():
        if line.startswith('Uid:'):
            return int(line.split()[1])  # real uid
    raise OSError(f'no Uid line for pid {pid}')


def _flag(args: list[str], name: str) -> str | None:
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None


def cmdline_matches(cmdline: list[str], argv: list[str]) -> tuple[bool, str]:
    """The live command line is the recorded argv: same binary (directly, or as the script of an
    interpreter's shebang), same ``--port``, same ``-m`` path and every other argument identical."""
    if not cmdline or not argv:
        return False, 'no command line'
    binary = argv[0]
    if cmdline[0] == binary:
        rest = cmdline[1:]
    elif len(cmdline) > 1 and cmdline[1] == binary and INTERPRETERS.search(os.path.basename(cmdline[0])):
        rest = cmdline[2:]
    else:
        return False, 'binary differs'
    if _flag(rest, '--port') != _flag(argv[1:], '--port'):
        return False, 'port differs'
    if _flag(rest, '-m') != _flag(argv[1:], '-m'):
        return False, 'model path differs'
    if rest != argv[1:]:
        return False, 'arguments differ'
    return True, 'command line matches'


def orphan_matches(record: dict) -> tuple[bool, str]:
    """Is the process in an earlier instance *record* still alive, and provably that instance?

    Ours means: same pid, owned by this user, still the leader's process group
    recorded at start, and its command line equals the recorded argv (binary,
    ``--port``, ``-m`` path, all other arguments).  A live pid that fails any
    check is not ours and is never signalled.
    """
    pid, pgid = record.get('pid'), record.get('pgid')
    if not pid or record.get('stopped_utc'):
        return False, 'no live process recorded'
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False, 'not running'
    except PermissionError:
        return False, 'pid belongs to another user'
    if not pid_alive(int(pid)):
        return False, 'not running (zombie)'
    try:
        if proc_uid(int(pid)) != os.getuid():
            return False, 'pid belongs to another user'
        if os.getpgid(int(pid)) != pgid:
            return False, 'process group differs (pid reused)'
        cmdline = proc_cmdline(int(pid))
    except (OSError, ValueError) as exc:
        return False, f'cannot inspect pid: {exc!r}'
    ok, reason = cmdline_matches(cmdline, record.get('argv') or [])
    if not ok:
        return False, f'{reason} (not this batch\'s instance)'
    return True, 'alive; pid, owner, process group and command line (binary, --port, -m) match'


def stop_orphan(record: dict, timeout: float = 20.0) -> dict:
    """Stop an earlier instance of this batch left running by a killed runner (after ``orphan_matches``)."""
    ours, reason = orphan_matches(record)
    result = {'pid': record.get('pid'), 'pgid': record.get('pgid'), 'port': record.get('port'), 'check': reason,
              'utc': _utc()}
    if not ours:
        result['action'] = 'none'
        return result
    pgid = int(record['pgid'])
    os.killpg(pgid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(int(record['pid'])):
            result['action'] = 'SIGTERM'
            return result
        time.sleep(0.2)
    os.killpg(pgid, signal.SIGKILL)
    result['action'] = 'SIGKILL'
    return result
