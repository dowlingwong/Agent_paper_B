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
  PID still leads it;
* two-GPU serving (M4 2(e), R1-BX-PROPOSED-CONFIRM REVISIONS (f)): with
  ``gpu_uuids=[u1, u2]`` and ``tensor_split=[a, b]`` the server sees both cards
  (``CUDA_VISIBLE_DEVICES=u1,u2``) and gets ``--split-mode layer --tensor-split
  a,b``; ``offload_check_dual`` requires full offload with model buffers on both
  cards in the last load of this start's log (route (i)) or the server pid on
  both cards at their pinned per-card footprints (route (ii)); uuids must be
  GPU-/MIG- uuids and no extra argument or env may override the split or the
  devices. Without ``gpu_uuids`` the single-GPU argv,
  environment and record are byte-for-byte what they were.

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
import math
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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


def build_info(binary: str, timeout: float = 60.0) -> dict:
    """``<binary> --version``: the raw output, the ``version: <n> (<commit>)`` line and its parts.

    llama.cpp prints the version on stderr (CUDA builds may print device lines
    first); both streams are searched.
    """
    done = subprocess.run([str(binary), '--version'], capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL)
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


def gpu_compute_apps(timeout: float = 60.0) -> list[dict] | None:
    """The GPU compute processes now (pid, GPU uuid, MiB), or None when ``nvidia-smi`` cannot be read."""
    try:
        done = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,used_memory',
                               '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=timeout)
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


UUID_RE = re.compile(r'^(GPU|MIG)-[0-9A-Za-z-]+$')
DUAL_CONFLICTING_FLAGS = ('--tensor-split', '-ts', '--split-mode', '-sm', '--main-gpu', '-mg', '--device', '-dev')


def validate_dual(gpu_uuid, gpu_uuids, tensor_split, *, extra_args=(), env_extra=None):
    """Two-GPU settings: exactly two distinct GPU-/MIG- uuids (exact strings, nothing stripped) and two
    positive finite split weights, not together with the single ``gpu_uuid``, and no ``extra_args`` or
    ``env_extra`` that would override the split or the device selection (llama.cpp's last flag wins,
    and the record would then describe a configuration that is not served).  Returns ``(None, None)``
    for single-GPU serving, whose inputs are not checked here (unchanged behaviour)."""
    if gpu_uuids is None and tensor_split is None:
        return None, None
    if gpu_uuids is None or tensor_split is None:
        raise ValueError('two-GPU serving needs both gpu_uuids and tensor_split')
    if gpu_uuid is not None:
        raise ValueError('use either gpu_uuid (one card) or gpu_uuids (two cards), not both')
    if (not isinstance(gpu_uuids, (list, tuple)) or len(gpu_uuids) != 2
            or any(not isinstance(u, str) or not UUID_RE.match(u) for u in gpu_uuids)
            or gpu_uuids[0] == gpu_uuids[1]):
        raise ValueError('gpu_uuids must be two distinct GPU-/MIG- uuids (no index, no whitespace)')
    if (not isinstance(tensor_split, (list, tuple)) or len(tensor_split) != 2
            or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0
                   for x in tensor_split)):
        raise ValueError('tensor_split must be two positive finite numbers')
    for arg in extra_args or ():
        if str(arg) in DUAL_CONFLICTING_FLAGS or str(arg).split('=', 1)[0] in DUAL_CONFLICTING_FLAGS:
            raise ValueError(f'extra_args may not override the two-GPU split or devices: {arg!r}')
    if env_extra and 'CUDA_VISIBLE_DEVICES' in env_extra:
        raise ValueError('env_extra may not set CUDA_VISIBLE_DEVICES with gpu_uuids')
    return list(gpu_uuids), list(tensor_split)


def tensor_split_arg(tensor_split) -> str:
    """Exact argv text of the split: ``repr`` for floats (round-trip), ``str`` for ints."""
    return ','.join(repr(float(x)) if isinstance(x, float) else str(x) for x in tensor_split)


def dual_args(tensor_split) -> list[str]:
    """``--split-mode layer --tensor-split a,b`` for two-GPU serving; nothing otherwise."""
    if not tensor_split:
        return []
    return ['--split-mode', 'layer', '--tensor-split', tensor_split_arg(tensor_split)]


LOAD_MARKERS = ('llama_model_loader: loaded meta data', 'load_tensors: offloading')


def last_load(log_text: str) -> str:
    """The part of a log from the last model-load marker on (the whole text if there is none).

    Guards against buffer lines of an earlier load in a reused log.  A later load that prints no
    marker at all cannot be told apart here, which is why ``offload()`` also reads only from the
    log size recorded at ``start()``."""
    meta = log_text.rfind(LOAD_MARKERS[0])
    offl = log_text.rfind(LOAD_MARKERS[1])
    if meta < 0 and offl < 0:
        return log_text
    cut = meta if meta >= 0 else offl   # a load starts at its 'loaded meta data' line
    return log_text[log_text.rfind('\n', 0, cut) + 1:]


def offload_check_dual(log_text: str, *, pid: int | None, gpu_uuids, footprint_mib, apps) -> dict:
    """Full offload across both cards.  Route (i): an ``offloaded N/N layers`` line, no CPU fallback,
    and a non-zero model buffer on two CUDA devices.  Route (ii), when the build prints no offload line:
    the server pid listed by nvidia-smi on **each** uuid with used memory >= that card's pinned
    footprint (``footprint_mib`` = ``[f1, f2]``).  A partial line or CPU fallback is a STOP.  Only the
    last load in ``log_text`` is read (``last_load``).  The server pid's nvidia-smi rows on each card are
    recorded either way; this is *not* the occupancy census of other processes on the two cards (that
    belongs to the runner, M4 2(e), and is not done here)."""
    report = offload_report(last_load(log_text))
    rows = [r for r in (apps or []) if r.get('pid') == pid]
    cards = []
    for i, uuid in enumerate(gpu_uuids):
        mine = next((r for r in rows if r.get('gpu_uuid') == uuid), None)
        cards.append({'gpu_uuid': uuid, 'used_mib': mine.get('used_mib') if mine else None,
                      'listed': mine is not None})
    devices = sorted({b['device'] for b in report['gpu_model_buffers'] if b['mib'] > 0})
    check = {**report, 'route': None, 'cards': cards, 'model_buffer_devices': devices,
             'compute_apps_read': apps is not None, 'pid': pid}
    if report['cpu_fallback_lines'] or report['line'] == 'partial':
        check['full'] = False
        return check
    if report['line'] == 'full':
        if len(devices) >= 2:
            check.update(full=True, route='log_line')
            return check
        check.update(full=False, reasons=[f'offloaded N/N but model buffers on {devices}, not on two cards'])
        return check
    reasons = list(report['reasons'])
    if (not isinstance(footprint_mib, (list, tuple)) or len(footprint_mib) != 2
            or any(isinstance(f, bool) or not isinstance(f, (int, float)) or f <= 0 for f in footprint_mib)):
        reasons.append('route (ii) refused: per-card footprint_mib [f1, f2] is not set')
    elif apps is None:
        reasons.append('route (ii): nvidia-smi --query-compute-apps could not be read')
    else:
        short = [c['gpu_uuid'] for c, f in zip(cards, footprint_mib)
                 if c['used_mib'] is None or c['used_mib'] < f]
        if not short:
            check.update(full=True, route='gpu_memory', reasons=[])
            return check
        reasons.append(f'route (ii): server pid {pid} not at its pinned footprint on {short}')
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
                 generation: int = 0, thinking_policy: dict | None = None,
                 gpu_uuids: list[str] | None = None, tensor_split: list[float] | None = None) -> None:
        self.gpu_uuids, self.tensor_split = validate_dual(gpu_uuid, gpu_uuids, tensor_split,
                                                          extra_args=extra_args, env_extra=env_extra)
        self.log_offset = 0  # size of a reused log before this start (two-GPU offload reads after it)
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
                *dual_args(self.tensor_split), *self.extra_args, *self.thinking_argv]

    def env(self) -> tuple[dict[str, str], list[str]]:
        env, removed = {}, []
        for key, value in os.environ.items():
            if key.startswith(STRIPPED_ENV_PREFIX) or key in STRIPPED_ENV:
                removed.append(key)
            else:
                env[key] = value
        if self.gpu_uuid:
            env['CUDA_VISIBLE_DEVICES'] = self.gpu_uuid
        elif self.gpu_uuids:
            env['CUDA_VISIBLE_DEVICES'] = ','.join(self.gpu_uuids)
        env.update(self.env_extra)
        return env, sorted(removed)

    def _save(self) -> None:
        self.record_path.write_text(json.dumps(self.record, indent=2) + '\n')

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
        if self.gpu_uuids:
            raw = self.log_path.read_bytes() if self.log_path.exists() else b''
            return offload_check_dual(raw[self.log_offset:].decode(errors='replace'), pid=pid,
                                      gpu_uuids=self.gpu_uuids, footprint_mib=footprint_mib, apps=apps)
        return offload_check(self.log_text(), pid=pid, gpu_uuid=self.gpu_uuid, footprint_mib=footprint_mib, apps=apps)

    def start(self, *, build: dict | None = None, model_sha256: str | None = None) -> dict:
        if self.process is not None:
            raise RuntimeError('STOP: this instance was already started')
        if not port_is_free(self.port):
            raise RuntimeError(f'STOP: port {self.port} is in use; a dedicated instance never shares a server')
        if not Path(self.model_path).is_file():
            raise RuntimeError(f'STOP: GGUF file not found: {self.model_path}')
        self.batch.mkdir(parents=True, exist_ok=True)
        env, removed = self.env()
        argv = self.argv
        if self.gpu_uuids:  # the log is opened for appending: read this start's part only
            self.log_offset = self.log_path.stat().st_size if self.log_path.exists() else 0
        log = self.log_path.open('ab')
        self.process = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, start_new_session=True)
        log.close()
        self.record = {'label': self.label, 'backend': self.BACKEND, 'binary': self.binary, 'argv': argv,
                       'pid': self.process.pid, 'pgid': os.getpgid(self.process.pid), 'port': self.port,
                       'url': self.url, 'openai_base_url': self.openai_base_url, 'model_path': self.model_path,
                       'model_sha256': model_sha256, 'alias': self.alias, 'n_gpu_layers': self.n_gpu_layers,
                       'ctx_size': self.ctx_size, 'parallel_slots': 1, 'gpu_uuid': self.gpu_uuid,
                       'env_removed': removed, 'build': build, 'log': str(self.log_path), 'started_utc': _utc()}
        if self.thinking_policy is not None:
            self.record['thinking_policy'] = self.thinking_policy
        if self.gpu_uuids:  # only for two-GPU serving: single-GPU records keep their keys
            self.record.update(gpu_uuids=list(self.gpu_uuids), tensor_split=list(self.tensor_split),
                               tensor_split_arg=tensor_split_arg(self.tensor_split), split_mode='layer',
                               log_offset=self.log_offset)
        if self.generation:
            self.record['generation'] = self.generation
        try:
            self.record['cmdline'] = proc_cmdline(self.process.pid)
        except OSError:
            self.record['cmdline'] = None
        self._save()
        deadline = time.monotonic() + self.start_timeout
        last = None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.record.update(exited_early=self.process.returncode, failed_utc=_utc(),
                                   log_tail=self.log_text().splitlines()[-20:])
                self._save()
                raise RuntimeError(f'STOP: dedicated llama-server exited during start (rc={self.process.returncode})')
            status, body = _get_json(self.url + '/health', 2.0)
            last = {'status': status, 'body': body}
            if status == 200:
                try:  # the exec has happened by now: the command line is the server's own
                    self.record['cmdline'] = proc_cmdline(self.process.pid)
                except OSError:
                    pass
                self.record.update(healthy_utc=_utc(), health=body)
                self._save()
                return self.record
            time.sleep(0.2)
        self.record['last_health'] = last
        self.stop()
        raise RuntimeError(f'STOP: dedicated llama-server did not become healthy (last /health: {last})')

    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self, timeout: float = 20.0) -> dict:
        """Stop only the process group this instance started; record the outcome."""
        if self.process is None:
            return self.record
        if self.process.poll() is None:
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
