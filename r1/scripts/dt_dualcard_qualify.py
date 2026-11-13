#!/usr/bin/env python3
"""DTQ — dual-card qualification of one GGUF on two named GPUs (MAC_LOCAL_RUNBOOK M4 step 4; OPERATOR O5).

ENGINEERING_ONLY. AI-assisted (Claude). The result is informational: it never feeds the Track X selection
(R1-EXAM-RULE-X5V2 is frozen before any DTQ number exists) and it authorizes nothing.

For one GGUF the tool
1. checks that neither card has another process on it (a co-tenant at the start or during the run is a STOP);
2. serves the GGUF with one dedicated ``llama-server`` across the two cards (``LlamaServerInstance`` with
   ``gpu_uuids`` and ``tensor_split``; ``--split-mode layer``) at the B.1b settings: context 16,384, q8_0 KV cache,
   ``--jinja``, thinking off through the registry-style policy (``--chat-template-kwargs {"enable_thinking":false}``),
   ``-np 1``, and ``cache_prompt: false`` on every request;
3. proves offload with ``offload_check_dual`` (route (i): ``offloaded N/N`` plus model buffers on two CUDA devices;
   the pinned build 620d222 prints that line only at ``-lv 4`` (R1-EXAM-OFFLOAD-ROUTE), so ``-lv 4`` is passed by
   default; route (ii) needs ``--footprint-mib f1 f2``);
4. replays N = 50 sweep-shaped prompts x 3 repeats with their D26 seeds, reusing the Track S probe
   (``r1/tracks/probes/determinism.py`` at paper ``d10b05b7``: the harness request body ``chat_payload``, the
   interleaved ``schedule``, ``identity_rate``, ``latency_stats``);
5. reports within-server identity, latency mean and p95, completion tokens per call, peak memory per card of the
   server process, and the sweep-2 projection; and evaluates the DTQ pass criterion of PLAN R1-BX-PROPOSED-CONFIRM:
   full offload to both cards, within-server identity 1.000 at ``cache_prompt: false``, sweep-2 T0 projection
   <= 4 days.

A server that cannot start (for example an out-of-memory exit) or does not offload fully is a **recorded result**
(``status`` ``server_start_failed`` / ``offload_not_full``), not a tool failure (O5: "an OOM is a recorded result").

Prompts: ``--prompts`` is a JSONL file, one ``{"prompt", "seed", "source"}`` per line, drawn by the operator from
sweep-1 contexts. Every ``--exclude-prompts`` file (the exam's frozen prompt sets) is read and any prompt text in
common is refused, so the replay set is disjoint from the exam (O5). ``--dry-run`` runs against the fake server
(``r1/scripts/c3_fake_llama_server.py``) and labels everything DRYRUN.

Projection (LLM time only, a lower bound): ``campaigns x calls_per_campaign x mean latency`` with one server
serving one call at a time. Worker time between calls is not included; ``--calls-per-campaign`` has no default
because it is a property of the sweep-2 design that the operator states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from r1.scripts import llama_server_instance as lsi  # noqa: E402
from r1.tracks.probes import determinism as probe  # noqa: E402

SCHEMA = 'dtq_report/v1'
CTX_SIZE = 16384
KV_ARGS = ['--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0']
THINKING_OFF = {'mode': 'off', 'budget': 0, 'off_switch': True}
PROPOSAL_SCHEMA = 'manager_proposal/v1'
N_PROMPTS, REPEATS = 50, 3
PASS_IDENTITY, PASS_PROJECTION_DAYS = 1.0, 4.0
DEFAULT_CAMPAIGNS = 288   # sweep-1 shape reused by sweep 2 (R1-MAIN-PROPOSER (b)): 8 nodes x 18 instances x 2 memory modes


def _norm(text: str) -> str:
    return hashlib.sha256(' '.join(str(text).split()).encode()).hexdigest()


def _texts(row: dict) -> list[str]:
    if 'prompt' in row:
        return [str(row['prompt'])]
    if isinstance(row.get('messages'), list):
        return ['\n'.join(str(m.get('content', '')) for m in row['messages'] if isinstance(m, dict))]
    return []


def load_prompts(path: str, n: int, exclude: list[str]) -> tuple[list[dict], dict]:
    """The first ``n`` rows of ``path``; each needs ``prompt`` (str), ``seed`` (int) and ``source`` (str).
    Refuses duplicates and any prompt whose whitespace-normalised text occurs in an ``exclude`` file."""
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if len(rows) < n:
        raise SystemExit(f'STOP: {path} has {len(rows)} prompts; {n} are needed')
    rows = rows[:n]
    for i, r in enumerate(rows):
        if not isinstance(r.get('prompt'), str) or not r['prompt'].strip():
            raise SystemExit(f'STOP: prompt row {i} has no prompt text')
        if isinstance(r.get('seed'), bool) or not isinstance(r.get('seed'), int):
            raise SystemExit(f'STOP: prompt row {i} has no integer D26 seed')
        if not isinstance(r.get('source'), str) or not r['source'].strip():
            raise SystemExit(f'STOP: prompt row {i} has no source (the sweep-1 context it was drawn from)')
    keys = [_norm(r['prompt']) for r in rows]
    if len(set(keys)) != len(keys):
        raise SystemExit('STOP: duplicate prompts in the replay set')
    excluded: set[str] = set()
    files = []
    for ex in exclude:
        raw = Path(ex).read_bytes()
        n_rows = 0
        for line in raw.decode().splitlines():
            if line.strip():
                n_rows += 1
                excluded.update(_norm(t) for t in _texts(json.loads(line)))
        files.append({'path': str(ex), 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': n_rows})
    overlap = [i for i, k in enumerate(keys) if k in excluded]
    if overlap:
        raise SystemExit(f'STOP: replay prompts {overlap} occur in an excluded (exam) prompt set')
    return rows, {'prompts_file': str(path), 'prompts_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                  'n': n, 'excluded_files': files, 'excluded_texts': len(excluded), 'overlap': 0}


def co_tenants(apps: list[dict] | None, uuids: list[str], own_pid: int | None) -> list[dict] | None:
    """nvidia-smi rows on either card that do not belong to ``own_pid``; None when nvidia-smi cannot be read."""
    if apps is None:
        return None
    return [r for r in apps if r.get('gpu_uuid') in uuids and r.get('pid') != own_pid]


class MemorySampler(threading.Thread):
    """Polls nvidia-smi: peak used MiB of the server pid per card, and any co-tenant on the two cards."""

    def __init__(self, uuids: list[str], pid: int, interval: float = 1.0, apps_fn=lsi.gpu_compute_apps):
        super().__init__(daemon=True)
        self.uuids, self.pid, self.interval, self.apps_fn = list(uuids), pid, interval, apps_fn
        self.peak = {u: None for u in uuids}
        self.samples = 0
        self.unread = 0
        self.intruders: list[dict] = []
        self._halt = threading.Event()

    def sample(self) -> None:
        apps = self.apps_fn()
        if apps is None:
            self.unread += 1
            return
        self.samples += 1
        for r in apps:
            if r.get('pid') == self.pid and r.get('gpu_uuid') in self.peak and r.get('used_mib') is not None:
                old = self.peak[r['gpu_uuid']]
                self.peak[r['gpu_uuid']] = r['used_mib'] if old is None else max(old, r['used_mib'])
        self.intruders.extend(co_tenants(apps, self.uuids, self.pid) or [])

    def run(self) -> None:
        while not self._halt.is_set():
            self.sample()
            self._halt.wait(self.interval)

    def stop(self) -> None:
        self._halt.set()
        self.join(timeout=10 * self.interval + 30)
        self.sample()


def post(url: str, payload: dict, timeout: float) -> tuple[str, float, int | None]:
    """The probe's POST, keeping ``usage.completion_tokens`` as well."""
    req = urllib.request.Request(url.rstrip('/') + '/chat/completions', data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - local dedicated server
        body = json.loads(resp.read())
    dt = time.perf_counter() - t0
    tokens = (body.get('usage') or {}).get('completion_tokens')
    return body['choices'][0]['message']['content'], dt, tokens if isinstance(tokens, int) else None


def replay(url: str, model: str, prompts: list[dict], repeats: int, order_seed: int, timeout: float) -> dict:
    """One serial client: every (prompt, repeat) once in the probe's interleaved order; failures counted, never
    retried (an errored repeat makes its prompt not identical)."""
    payloads = [probe.chat_payload(p['prompt'], p['seed'], model, proposal_schema=PROPOSAL_SCHEMA) for p in prompts]
    bad = [i for i, b in enumerate(payloads) if b.get('cache_prompt') is not False]
    if bad:
        raise SystemExit(f'STOP: harness request body lacks explicit cache_prompt false (prompts {bad[:5]})')
    order = probe.schedule(len(prompts), repeats, order_seed, 0, 0)
    contents: dict[int, list] = {i: [] for i in range(len(prompts))}
    lat: list[float] = []
    tokens: list[int] = []
    errors = 0
    for i, _r in order:
        try:
            text, dt, n = post(url, payloads[i], timeout)
        except Exception:  # noqa: BLE001 - counted, not retried
            errors += 1
            contents[i].append(None)
            continue
        contents[i].append(text)
        lat.append(dt)
        if n is not None:
            tokens.append(n)
    tok = probe.latency_stats([float(t) for t in tokens])
    return {'calls': len(order), 'errors': errors, 'identity_rate': probe.identity_rate(contents, repeats),
            'non_identical_prompts': [i for i, v in contents.items() if len(v) != repeats or None in v
                                      or len(set(v)) != 1],
            'latency': probe.latency_stats(lat),
            'completion_tokens': {'n': tok['n'], 'mean': tok['mean_s'], 'p95': tok['p95_s']},
            'order': {'seed': order_seed, 'rule': 'probe.schedule(url_index=0, client=0)', 'head': order[:5]},
            'request_example': payloads[0] if payloads else None}


def projection_days(mean_latency_s: float | None, campaigns: int, calls_per_campaign: int) -> float | None:
    if mean_latency_s is None or not math.isfinite(mean_latency_s):
        return None
    return campaigns * calls_per_campaign * mean_latency_s / 86400.0


def evaluate(offload: dict | None, identity: float | None, days: float | None) -> dict:
    full = bool(offload and offload.get('full'))
    ident = identity is not None and identity >= PASS_IDENTITY
    proj = days is not None and days <= PASS_PROJECTION_DAYS
    return {'criterion': 'R1-BX-PROPOSED-CONFIRM: full offload to both cards; within-server identity 1.000 at '
                         'cache_prompt false; sweep-2 T0 projection <= 4 days',
            'full_offload_both_cards': full, 'identity_1': ident, 'projection_le_4_days': proj,
            'pass': full and ident and proj, 'applied_by': 'tool (informational); the host decision is the author\'s'}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--gguf', required=True)
    ap.add_argument('--gguf-sha256', required=True, help='the registry sha256; the file is hashed and must match')
    ap.add_argument('--llama-server-bin', required=True)
    ap.add_argument('--gpu-uuid', action='append', required=True, help='exactly two, GPU-/MIG- uuids')
    ap.add_argument('--tensor-split', default='1,1')
    ap.add_argument('--footprint-mib', type=float, nargs=2, default=None, help='route (ii) per-card floors')
    ap.add_argument('--no-verbose-load', action='store_true', help='do not pass -lv 4 (route (i) needs the line)')
    ap.add_argument('--model', default='r1-manager', help='server alias')
    ap.add_argument('--port', type=int, default=None)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--exclude-prompts', action='append', default=[])
    ap.add_argument('--n', type=int, default=N_PROMPTS)
    ap.add_argument('--repeats', type=int, default=REPEATS)
    ap.add_argument('--order-seed', type=int, default=20261104)
    ap.add_argument('--campaigns', type=int, default=DEFAULT_CAMPAIGNS)
    ap.add_argument('--calls-per-campaign', type=int, required=True)
    ap.add_argument('--timeout', type=float, default=600.0)
    ap.add_argument('--start-timeout', type=float, default=900.0)
    ap.add_argument('--sample-seconds', type=float, default=1.0)
    ap.add_argument('--host-label', required=True)
    ap.add_argument('--out-dir', required=True, help='new directory (must not exist)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    if len(a.gpu_uuid) != 2:
        ap.error('exactly two --gpu-uuid')
    if a.n < 1 or a.repeats < 2 or a.campaigns < 1 or a.calls_per_campaign < 1:
        ap.error('--n >= 1, --repeats >= 2, --campaigns >= 1 and --calls-per-campaign >= 1')
    if not a.dry_run and not a.exclude_prompts:
        ap.error('--exclude-prompts (the exam frozen prompt sets) is required outside --dry-run')
    out = Path(a.out_dir)
    if out.exists():
        raise SystemExit(f'STOP: --out-dir {out} exists; DTQ writes a fresh directory')
    split = [int(float(x)) if float(x).is_integer() else float(x) for x in a.tensor_split.split(',')]
    prompts, prompt_record = load_prompts(a.prompts, a.n, a.exclude_prompts)
    sha = lsi.sha256_file(a.gguf)
    if sha != a.gguf_sha256:
        raise SystemExit(f'STOP: GGUF sha256 {sha} differs from the registry value {a.gguf_sha256}')
    out.mkdir(parents=True)
    label = 'DRYRUN' if a.dry_run else 'ENGINEERING_ONLY'
    report: dict = {'schema': SCHEMA, 'label': label, 'informational': True, 'host': a.host_label,
                    'gguf': a.gguf, 'gguf_sha256': sha, 'gpu_uuids': a.gpu_uuid, 'tensor_split': split,
                    'settings': {'ctx_size': CTX_SIZE, 'kv': 'q8_0', 'jinja': True, 'thinking_policy': THINKING_OFF,
                                 'parallel_slots': 1, 'cache_prompt': False, 'proposal_schema': PROPOSAL_SCHEMA,
                                 'temperature': 0.2, 'verbose_load': not a.no_verbose_load},
                    'prompts': prompt_record, 'repeats': a.repeats,
                    'probe': {'module': 'r1.tracks.probes.determinism', 'schema': probe.PROBE_SCHEMA,
                              'source_commit': 'd10b05b7'},
                    'projection_inputs': {'campaigns': a.campaigns, 'calls_per_campaign': a.calls_per_campaign,
                                          'basis': 'LLM time only, one call at a time (lower bound)'}}

    inst = None

    def finish(status: str, code: int = 0) -> int:
        if inst is not None and inst.alive():  # stop the server first, so the report records it
            rec = inst.stop() or {}
            report['server_stop'] = {'stopped': not inst.alive(),
                                     **{k: v for k, v in rec.items() if k.startswith('stop') or k == 'returncode'}}
        report['status'] = status
        (out / 'dtq_report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': status, 'pass': (report.get('dtq') or {}).get('pass')}))
        return code

    before = lsi.gpu_compute_apps()
    report['census_before'] = before
    others = co_tenants(before, a.gpu_uuid, None)
    if others is None and not a.dry_run:
        return finish('STOP_nvidia_smi_unreadable', 2)
    if others:
        report['co_tenants'] = others
        return finish('STOP_co_tenant_at_start', 2)
    report['build'] = lsi.build_info(a.llama_server_bin)
    extra = ['--jinja', *KV_ARGS, *([] if a.no_verbose_load else ['-lv', '4'])]
    inst = lsi.LlamaServerInstance(out / 'server', a.llama_server_bin, model_path=a.gguf, alias=a.model, port=a.port,
                                   ctx_size=CTX_SIZE, label=label, extra_args=extra, start_timeout=a.start_timeout,
                                   thinking_policy=THINKING_OFF, gpu_uuids=a.gpu_uuid, tensor_split=split)
    try:
        try:
            report['server'] = inst.start(build=report['build'], model_sha256=sha)
        except RuntimeError as exc:
            report['server'] = inst.record
            report['server_error'] = str(exc)
            report['server_log_tail'] = inst.log_text().splitlines()[-40:]
            report['dtq'] = evaluate(None, None, None)
            return finish('server_start_failed')
        offload = inst.offload(footprint_mib=a.footprint_mib)
        report['offload'] = offload
        if not offload.get('full'):
            report['dtq'] = evaluate(offload, None, None)
            return finish('offload_not_full')
        report['server_props'] = inst.props()
        sampler = MemorySampler(a.gpu_uuid, inst.record['pid'], a.sample_seconds)
        sampler.start()
        try:
            result = replay(inst.openai_base_url, a.model, prompts, a.repeats, a.order_seed, a.timeout)
        finally:
            sampler.stop()
        report['replay'] = result
        report['peak_mib_per_card'] = sampler.peak
        report['memory_samples'] = {'read': sampler.samples, 'unreadable': sampler.unread}
        days = projection_days(result['latency']['mean_s'], a.campaigns, a.calls_per_campaign)
        report['projection_days'] = days
        report['cache_prompt'] = (result.get('request_example') or {}).get('cache_prompt')
        report['dtq'] = evaluate(offload, result['identity_rate'], days)
        if sampler.intruders:
            report['co_tenants'] = sampler.intruders
            return finish('STOP_co_tenant_during_run', 2)
        return finish('complete')
    finally:  # an unexpected exception: never leave the dedicated server running
        if inst.alive():
            inst.stop()


if __name__ == '__main__':
    raise SystemExit(main())
