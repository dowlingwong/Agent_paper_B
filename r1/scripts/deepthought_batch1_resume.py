"""Execute the authorized remote batch, preserving a stopped attempt."""
from datetime import datetime, timezone
import hashlib
import getpass
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import time
from urllib.request import urlopen
from zoneinfo import ZoneInfo
from xml.etree import ElementTree

BATCH = Path(os.environ['R1_BATCH_DIRECTORY'])
PAPER = Path(os.environ.get('R1_PAPER_ROOT', '/ceph/dwong/agent_paper_B'))
HARNESS = Path(os.environ.get('AR_HARNESS_ROOT', '/ceph/dwong/autoresearch_harness'))
PY = str(HARNESS / '.venv/bin/python')
OLLAMA = os.environ.get('R1_OLLAMA_BINARY', str(BATCH / 'ollama_runtime/bin/ollama'))
DIGEST = 'dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364'
MODEL = 'qwen2.5-coder:7b'
# R1-COMPUTE GPU co-tenancy (author, 13 Oct 2026; PLAN §10): a card may be shared with
# other users' processes when its free memory suffices; LLM latency is descriptive only.
MODEL_FOOTPRINT_MIB = 5304  # DT1: size_vram 5560907776 B, model fully offloaded
MARGIN_MIB = 2048
EXECUTOR = os.environ.get('R1_EXECUTOR', 'Codex')
COAUTHOR = os.environ.get('R1_COAUTHOR', 'Codex <noreply@openai.com>')
os.environ.update(AR_HARNESS_ROOT=str(HARNESS), OLLAMA_BASE_URL='http://127.0.0.1:11434',
                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
os.environ['PATH'] = str(HARNESS / '.venv/bin') + ':' + os.environ['PATH']
state = {'label': 'ENGINEERING_ONLY', 'steps': {}, 'batch_logs': str(BATCH), 'execution_host': platform.node(), 'wait_limit_seconds': None}
if (BATCH / 'repairs.json').exists():
    state['steps'].update(json.loads((BATCH / 'repairs.json').read_text()))


def save():
    (BATCH / 'batch_state.json').write_text(json.dumps(state, indent=2) + '\n')


def stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def cmd(argv, cwd=PAPER, log=None):
    print('RUN', argv, flush=True)
    if log:
        with (BATCH / log).open('a') as f:
            subprocess.run(argv, cwd=cwd, check=True, stdout=f, stderr=subprocess.STDOUT)
    else:
        subprocess.run(argv, cwd=cwd, check=True)


def git_output(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()


def commit(repo, message, paths, step):
    cmd(['git', 'add', '-f', '--', *[str(p) for p in paths]], cwd=repo)
    # Preserve raw generated CSV, logs and patch artifacts byte-for-byte.
    cmd(['git', 'diff', '--cached', '--check', '--', '.',
         ':!results/r1/**', ':!experiments/r1/**'], cwd=repo)
    cmd(['git', 'commit', '-m', message, '-m', 'Co-Authored-By: ' + COAUTHOR], cwd=repo)
    branch = 'r1' if repo == HARNESS else 'main'
    cmd(['git', 'push', 'origin', branch], cwd=repo)
    head = git_output(repo, 'rev-parse', 'HEAD')
    remote = git_output(repo, 'ls-remote', 'origin', 'refs/heads/' + branch).split()[0]
    if head != remote:
        raise RuntimeError('STOP: pushed head does not match remote head')
    state['steps'][step]['commit'] = head
    save()


def gpu_rows():
    """All cards, and the cards with enough free memory to load the pinned model (co-tenancy rule)."""
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.free',
                                    '--format=csv,noheader,nounits'], text=True).strip().splitlines()
    need = MODEL_FOOTPRINT_MIB + MARGIN_MIB
    return rows, [r for r in rows if int(r.split(',')[3].strip()) >= need]


def pin():
    with urlopen('http://127.0.0.1:11434/api/tags', timeout=15) as r:
        tags = json.load(r)
    found = next((m for m in tags['models'] if m['name'] == MODEL), None)
    if found is None or found['digest'] != DIGEST:
        raise RuntimeError('STOP: Ollama digest differs from author pin')
    return found


def gpu_census():
    """Descriptive census of every card: free memory and the owners of its processes."""
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.free',
                                    '--format=csv,noheader,nounits'], text=True).strip().splitlines()
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    cards = []
    for row in rows:
        index, uuid, name, free = [part.strip() for part in row.split(',')]
        processes = []
        for g in xml.findall('gpu'):
            if g.findtext('uuid') != uuid:
                continue
            for p in g.findall('./processes/process_info'):
                pid = p.findtext('pid')
                try:
                    owner = subprocess.check_output(['ps', '-o', 'user=', '-p', pid], text=True).strip()
                except subprocess.CalledProcessError:
                    owner = None  # exited between nvidia-smi and ps
                processes.append({'pid': pid, 'owner': owner, 'used_memory': p.findtext('used_memory')})
        cards.append({'index': index, 'uuid': uuid, 'name': name, 'free_mib': int(free), 'processes': processes})
    return cards


def check_gpu():
    """Co-tenancy check (PLAN §10, 13 Oct): other users' processes are allowed and only logged.

    STOP only when the selected card's free memory is below the margin: footprint + margin
    before our model is loaded, the margin alone once it is loaded.
    """
    selected_uuid = state['gpu'].split(',')[1].strip()
    cards = gpu_census()
    card = next((c for c in cards if c['uuid'] == selected_uuid), None)
    if card is None:
        raise RuntimeError('STOP: selected GPU is no longer listed by nvidia-smi')
    need = MARGIN_MIB if state.get('model_loaded') else MODEL_FOOTPRINT_MIB + MARGIN_MIB
    me = getpass.getuser()
    record = {'label': 'ENGINEERING_ONLY', 'utc': stamp(), 'selected_uuid': selected_uuid,
              'need_free_mib': need, 'selected_free_mib': card['free_mib'],
              'other_owners_on_selected': sorted({str(p['owner']) for p in card['processes'] if p['owner'] != me}),
              'cards': cards}
    with (BATCH / 'gpu_census.jsonl').open('a') as f:
        f.write(json.dumps(record) + '\n')
    if card['free_mib'] < need:
        raise RuntimeError(f"STOP: selected GPU has {card['free_mib']} MiB free, below the {need} MiB co-tenancy margin")
    return record


def assert_full_offload(loaded, where):
    """The pinned model must sit entirely on the GPU; a partial or CPU load is a STOP."""
    if loaded is None or loaded.get('size_vram', 0) <= 0 or loaded['size_vram'] < loaded.get('size', 0):
        raise RuntimeError(f'STOP: {where}: pinned model is not fully offloaded to the GPU')


def require_liveness(nodes):
    """D28 gate (P5): no LLM-backed collection without a committed liveness pass.

    The manifest is ``$R1_LIVENESS_MANIFEST`` when set, else the newest
    ``results/r1/engineering/liveness_*/liveness.json``.  The manifest must
    come from an LLM-backed liveness run (``manager_kind: langgraph``): a
    scripted smoke pass is not the D28 check (review F5).  A missing, scripted
    or failed node raises ``STOP:``.
    """
    from r1.liveness import load_liveness_manifest, require_live

    explicit = os.environ.get('R1_LIVENESS_MANIFEST')
    if explicit:
        manifest_path = Path(explicit)
    else:
        candidates = sorted((PAPER / 'results/r1/engineering').glob('liveness_*/liveness.json'))
        if not candidates:
            raise RuntimeError('STOP: no D28 liveness manifest; run the liveness check first')
        manifest_path = candidates[-1]
    manifest = load_liveness_manifest(manifest_path)
    if manifest.get('manager_kind') != 'langgraph':
        raise RuntimeError(
            f'STOP: liveness manifest {manifest_path} is not from an LLM-backed run '
            f"(manager_kind={manifest.get('manager_kind')!r}); run `python -m r1.liveness --run "
            "--manager langgraph` first"
        )
    return require_live(list(nodes), manifest)


def collect(out, work, extra, nodes):
    require_liveness(nodes)
    cmd([PY, '-m', 'r1.headroom.e1b_collect', '--manager', 'langgraph', '--work', str(work),
         '--out', str(out), *extra], log=out.name + '.log')
    for _ in range(12):
        check_gpu()
        cmd([PY, '-m', 'r1.headroom.e1b_collect', '--resume', str(out), '--workers',
             '2' if 'smoke' in out.name else '4'], log=out.name + '.log')
        manifest = json.loads((out / 'manifest.json').read_text())
        if manifest['sessions'][-1]['jobs_before'] == 0:
            break
    else:
        raise RuntimeError('STOP: collector failed to reach a zero-job session')
    leaves = [json.loads(p.read_text()) for p in (out / 'leaves').glob('*.json')]
    if not leaves or {p['action'] for p in leaves} != {'continue', 'verify'}:
        raise RuntimeError('STOP: missing continue or verify leaves')
    failures = [p for p in leaves if p['integrity'] != 'ok' or not p['audit_metrics']
                or any(m is None for m in p['audit_metrics'])]
    if failures:
        raise RuntimeError('STOP: collection failures; no leaf retries permitted')
    if manifest['manager']['kind'] != 'langgraph':
        raise RuntimeError('STOP: manager kind is not langgraph')
    calls, parse_failures, summaries = [], [], []
    for p in work.rglob('*.jsonl'):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('event_type') == 'llm_call':
                calls.append(item)
                if not item['payload'].get('parse_ok', True):
                    parse_failures.append(item)
            if 'proposal_summary' in item:
                summaries.append(item['proposal_summary'])
    if not calls or not summaries or not any(not re.fullmatch(r'\w+\s+\S+\s+->\s+\S+', s) for s in summaries):
        raise RuntimeError('STOP: no demonstrated LLM proposals in branch/root ledgers')
    if len(parse_failures) / len(calls) > 0.20:
        (out / 'parse_failure_examples.json').write_text(json.dumps(parse_failures[:5], indent=2))
        raise RuntimeError('STOP: manager parse failures exceed 20 percent')
    check = {'label': manifest['label'], 'leaves': len(leaves), 'collection_failures': len(failures),
             'manager_kind': manifest['manager']['kind'], 'llm_calls': len(calls),
             'parse_failures': len(parse_failures), 'proposal_examples': summaries[:5]}
    (out / 'collection_checks.json').write_text(json.dumps(check, indent=2) + '\n')
    # Archive ledgers and snapshots so analysis needs only committed inputs.
    archive = out / 'provenance'
    archive.mkdir()
    original_sources = {}
    for p in work.rglob('*.jsonl'):
        target = archive / 'ledgers' / p.relative_to(work)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    for p in (out / 'roots').glob('*.json'):
        root = json.loads(p.read_text())
        original_sources[root['instance']] = root['snapshots']
        new_paths = []
        for old in root['snapshots']:
            target = archive / 'snapshots' / root['instance'] / Path(old).name
            shutil.copytree(old, target)
            new_paths.append(str(target.relative_to(PAPER)))
        root['snapshots'] = new_paths
        p.write_text(json.dumps(root) + '\n')
    for noise in manifest['noise'].values():
        noise['original_source'] = noise['source']
        noise['source'] = str(Path(noise['source']).relative_to(PAPER))
    manifest['archival_paths'] = 'Snapshots and noise sources are repository-relative; original paths preserved in provenance.'
    (archive / 'original_snapshot_paths.json').write_text(json.dumps(original_sources, indent=2) + '\n')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return check


def finish(reason):
    if state.get('ollama_started_by_batch'):
        stopped = subprocess.run(['tmux', 'kill-session', '-t', 'r1_ollama_resume_20261012'],
                                 capture_output=True, text=True)
        state['ollama_cleanup'] = {'returncode': stopped.returncode, 'stderr': stopped.stderr}
        (BATCH / 'gpu_after_ollama_stop.txt').write_text(subprocess.check_output(['nvidia-smi'], text=True))
    state['finished_utc'] = stamp()
    state['stop_reason'] = reason
    save()
    day = datetime.now(ZoneInfo('Europe/Berlin')).strftime('%d %B %Y')
    lines = [f'## {day} — Remote batch 1: {"stopped" if reason else "completed"}', '',
             f'AI-assisted execution by {EXECUTOR}. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.', '',
             f'- **Execution host:** `{platform.node()}`. Logs and preserved runtime state: `{BATCH}/`.',
             f'- **Harness:** `{git_output(HARNESS, "rev-parse", "HEAD")}`; manager `{MODEL}`, pinned digest `{DIGEST}`.',
             f'- **GPU / offload:** `{state.get("gpu", "not selected")}`; `{json.dumps(state.get("gpu_offload", {}), sort_keys=True)}`.', '']
    for step, data in state['steps'].items():
        lines.append(f'- **{step}:** `{json.dumps(data, sort_keys=True)}`')
    if reason:
        lines += ['', f'**STOP:** {reason}', '',
                  'DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.']
    lines += ['', '- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.', '']
    status = PAPER / 'docs/r1/STATUS.md'
    old = status.read_text()
    pos = old.index('\n## ')
    status.write_text(old[:pos] + '\n\n' + '\n'.join(lines) + old[pos:])
    state['steps']['STATUS'] = {'completed': True, 'reason': reason}
    commit(PAPER, 'Record remote batch 1 execution status', ['docs/r1/STATUS.md'], 'STATUS')
    print('FINISHED', json.dumps(state), flush=True)


def run_dt4(meta, version):
    """DT4: E1b with the pinned LLM manager, analysis and committed regeneration."""
    pin()
    check_gpu()
    out = PAPER / 'results/r1/pilot' / ('E1b_' + stamp())
    work = BATCH / 'r1_e1b_llm_work'
    checks = collect(out, work, ['--nodes', 'digits_mlp', 'openml_ionosphere', '--instances', '6',
                               '--runs', '20', '--points', '4', '8', '12', '--reps', '2',
                               '--audit-seeds', '6', '--workers', '4'],
                     ['digits_mlp', 'openml_ionosphere'])
    with urlopen('http://127.0.0.1:11434/api/ps', timeout=15) as response:
        processes_after = json.load(response)
    (BATCH / 'gpu_offload_after_collection.json').write_text(json.dumps(
        {'label': 'ENGINEERING_ONLY', 'utc': stamp(), 'processes': processes_after}, indent=2) + '\n')
    after = next((m for m in processes_after['models'] if m.get('name', m.get('model')) == MODEL), None)
    assert_full_offload(after, 'after DT4 collection')
    check_gpu()
    report_stamp = datetime.now(timezone.utc).strftime('%Y%m%d')
    tables = PAPER / f'docs/r1/reports/HEADROOM_PILOT_{report_stamp}_llm_tables.md'
    report = PAPER / f'docs/r1/reports/HEADROOM_PILOT_{report_stamp}_llm.md'
    if report.exists() or tables.exists():
        raise RuntimeError('STOP: report destination already exists; no overwrite')
    cmd([PY, '-m', 'r1.headroom.e1b_analyze', str(out), '--md', str(tables)], log='DT4_analysis.log')
    current = json.loads((out / 'analysis.json').read_text())
    scripted = json.loads((PAPER / 'results/r1/pilot/E1b_20261012T161034Z/analysis.json').read_text())
    text = [f'# E1b LLM pilot headroom pre-check — {report_stamp}', '',
            f'**PILOT. AI-assisted execution and report by {EXECUTOR}. Not evidence; no human review.**', '',
            '## What ran', '',
            f'Run `{out.relative_to(PAPER)}` on `{platform.node()}`; harness `{meta["harness_commit"]}`; manager LangGraph/Ollama `{MODEL}`, digest `{DIGEST}`; GPU `{state["gpu"]}`; Ollama `{version}`.', '',
            'Six instances per node, digits_mlp and openml_ionosphere; W=20 worker runs; E2 points 4, 8, 12; continue and verify, r=2, two repetitions; six common fresh joint audit seeds 5001–5006. Verify split policy fixed. Every branch continues under the default rule at matched worker budget.', '',
            f'Collection checks: `{json.dumps(checks)}`.', '',
            '## Headroom bracket and scripted comparison', '',
            'Naive oracle is biased upward; its upper confidence bound is a conservative ceiling. Leaf-split oracle is biased downward with two repetitions. These are pilot inputs for this proposal law, nodes and budget.', '',
            '| Node | Proposer | Best simple | Naive headroom (95% CI) | Leaf-split headroom (95% CI) |',
            '|---|---|---|---|---|']
    for node in ['digits_mlp', 'openml_ionosphere', 'ALL']:
        for name, data in [('LLM', current), ('scripted', scripted)]:
            row = data['per_node'][node]
            base = row['best_simple']
            naive = row['contrast_ci']['oracle_naive - ' + base]
            leaf = row['contrast_ci']['oracle_leafsplit - ' + base]
            text.append(f'| {node} | {name} | {base} | {row["headroom_naive"]:+.4f} [{naive[0]:+.4f}, {naive[1]:+.4f}] | {row["headroom_leafsplit"]:+.4f} [{leaf[0]:+.4f}, {leaf[1]:+.4f}] |')
    text += ['', '## Deviations', '',
             f'The initial named host Deepthought2 has two L40S cards, while the author-approved fallback Deepthought has four TITAN X cards. The execution host was {platform.node()}; one card was used. Under the author’s 13 Oct co-tenancy decision (PLAN §10) the card could be shared with other users’ processes when its free memory was at least the model footprint plus 2 GiB; the per-step GPU census is in the batch log `gpu_census.jsonl`, and latency is descriptive only. Scratch paths are unique under the batch log directory to preserve pre-existing directories. No second Ollama instance was started; Ollama serializes inference, and OMP/OpenBLAS/MKL are capped at one thread per worker. Archived snapshot/noise paths were made repository-relative, with original paths recorded; proposal ledgers and snapshot bytes are included for regeneration. As in the scripted pilot, only E2 continue/verify is branched; E1 skip/revise and run-free rules are not evaluated, PACE is not scored, and this is not a stronger-manager deployment check.', '',
             '## What this changes for the E2 STOP', '',
             'The table adds headroom under the pinned LLM proposal law alongside the scripted proposal law. It is input to the author’s E2 STOP, not a go/no-go decision: D18, D21, D23, the D4 amendment and any split-policy revision remain open. The two-repetition oracle bracket is noisy and the pilot does not establish a learning gain. L11 remains unbuilt.', '']
    report.write_text('\n'.join(text))
    state['steps']['DT4'] = {'completed': False, 'out': str(out), 'checks': checks, 'report': str(report),
                             'headroom': {n: {k: r[k] for k in ['best_simple', 'headroom_naive', 'headroom_leafsplit', 'contrast_ci']}
                                          for n, r in current['per_node'].items()}}
    commit(PAPER, 'Record PILOT E1b LLM headroom bracket and scripted comparison', [out, tables, report], 'DT4')
    # Reproduce analysis from a fresh archive containing only committed inputs.
    archive = BATCH / 'committed_analysis.tar'
    e1_source = json.loads((out / 'manifest.json').read_text())['noise']['digits_mlp']['source']
    with archive.open('wb') as f:
        subprocess.run(['git', 'archive', 'HEAD', 'r1', str(out.relative_to(PAPER)), e1_source], cwd=PAPER, stdout=f, check=True)
    regen = BATCH / 'analysis_regeneration'
    regen.mkdir()
    cmd(['tar', '-xf', str(archive), '-C', str(regen)])
    expected = hashlib.sha256((out / 'analysis.json').read_bytes()).hexdigest()
    regen_out = regen / out.relative_to(PAPER)
    cmd([PY, '-m', 'r1.headroom.e1b_analyze', str(regen_out)], cwd=regen, log='DT4_regeneration.log')
    observed = hashlib.sha256((regen_out / 'analysis.json').read_bytes()).hexdigest()
    state['steps']['DT4']['committed_analysis_sha256'] = expected
    state['steps']['DT4']['regenerated_analysis_sha256'] = observed
    save()
    if expected != observed:
        raise RuntimeError('STOP: analysis differs when regenerated from committed inputs')
    state['steps']['DT4']['completed'] = True
    save()


def main():
    save()
    host = platform.node().split('.')[0]
    if host not in {'deepthought', 'deepthought2', 'ucrtasl'}:
        raise RuntimeError('STOP: unauthorized execution host')
    if host == 'ucrtasl':
        if os.environ.get('R1_GPU_UUID') != 'GPU-9be33fd1-8eeb-497d-772a-87362d6720be':
            raise RuntimeError('STOP: Ada batch is restricted to the author-selected GPU 0')
        authorization = json.loads((BATCH / 'deepthought_disabled.json').read_text())
        if authorization.get('duplicate_launch_prevented') is not True:
            raise RuntimeError('STOP: prior Deepthought launch claim is not disabled')
    comparison = json.loads((BATCH / 'postfix_comparison.json').read_text())
    if comparison['new_failures']:
        raise RuntimeError('STOP: tests that passed before now fail: ' + repr(comparison['new_failures']))
    rows, free = gpu_rows()
    required_uuid = os.environ.get('R1_GPU_UUID')
    if required_uuid:
        free = [row for row in free if row.split(',')[1].strip() == required_uuid]
    if not free:
        raise RuntimeError('STOP: no selected card has enough free memory for the pinned model (co-tenancy margin)')
    gpu = free[0].split(',')[0].strip()
    gpu_uuid = free[0].split(',')[1].strip()
    state['gpu'] = free[0]
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 11434))
    models = BATCH / 'ollama_models'
    models.mkdir()
    command = (f'CUDA_VISIBLE_DEVICES={gpu_uuid} OLLAMA_VULKAN=0 OLLAMA_HOST=127.0.0.1:11434 OLLAMA_MODELS={models} '
               f'OLLAMA_NUM_PARALLEL=1 {OLLAMA} serve > {BATCH}/ollama_serve.log 2>&1')
    cmd(['tmux', 'new-session', '-d', '-s', 'r1_ollama_resume_20261012', command])
    state['ollama_started_by_batch'] = True
    save()
    for _ in range(60):
        try:
            with urlopen('http://127.0.0.1:11434/api/version', timeout=2) as r:
                version = json.load(r)
            break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('STOP: dedicated Ollama server did not start')
    env = dict(os.environ, OLLAMA_HOST='127.0.0.1:11434')
    with (BATCH / 'model_pull.log').open('w') as f:
        subprocess.run([OLLAMA, 'pull', MODEL], env=env, check=True, stdout=f, stderr=subprocess.STDOUT)
    model = pin()
    check_gpu()
    # Load one token, then prove actual CUDA offload before latency or campaigns.
    from urllib.request import Request
    payload = json.dumps({'model': MODEL, 'prompt': 'Reply OK', 'stream': False,
                          'keep_alive': '30m', 'options': {'num_predict': 1}}).encode()
    with urlopen(Request('http://127.0.0.1:11434/api/generate', data=payload,
                         headers={'Content-Type': 'application/json'}), timeout=300) as response:
        probe_result = json.load(response)
    with urlopen('http://127.0.0.1:11434/api/ps', timeout=15) as response:
        offload = json.load(response)
    (BATCH / 'gpu_offload_probe.json').write_text(json.dumps(
        {'label': 'ENGINEERING_ONLY', 'response': probe_result, 'processes': offload}, indent=2) + '\n')
    loaded = next((m for m in offload['models'] if m.get('name', m.get('model')) == MODEL), None)
    if loaded is None or loaded.get('size_vram', 0) <= 0:
        raise RuntimeError('STOP: load probe demonstrated no GPU offload; no DT1 latency or later campaigns started')
    check_gpu()
    selected_uuid = state['gpu'].split(',')[1].strip()
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    selected = next(g for g in xml.findall('gpu') if g.findtext('uuid') == selected_uuid)
    if not selected.findall('./processes/process_info'):
        raise RuntimeError('STOP: GPU offload API lacks a process on the selected card')
    state['gpu_offload'] = {'size_vram': loaded['size_vram'], 'probe_tokens_max': 1,
                           'verified_before_DT1': True, 'host': platform.node()}
    state['model_loaded'] = True
    save()
    out = HARNESS / 'experiments/r1/pilot' / ('L4dt_' + stamp())
    cmd([PY, str(BATCH / 'dt1_latency.py'), str(out)], cwd=HARNESS, log='DT1.log')
    cmd([PY, 'scripts/r1_llm_latency.py', '--events', str(out / 'events.jsonl'), '--out', str(out)], cwd=HARNESS, log='DT1.log')
    meta = {'label': 'PILOT', 'model': model, 'gpu': state['gpu'], 'ollama_version': version,
            'harness_commit': git_output(HARNESS, 'rev-parse', 'HEAD'),
            'execution_host': platform.node(), 'gpu_inventory': subprocess.check_output(['nvidia-smi'], text=True),
            'gpu_selection': {'CUDA_VISIBLE_DEVICES': gpu_uuid, 'OLLAMA_VULKAN': '0'}}
    (out / 'provenance.json').write_text(json.dumps(meta, indent=2) + '\n')
    latency = json.loads((out / 'llm_latency.json').read_text())
    state['steps']['DT1'] = {'completed': False, 'out': str(out), 'latency': latency}
    save()
    if latency['n_calls'] != 10:
        raise RuntimeError('STOP: L4-dt did not produce ten calls')
    with urlopen('http://127.0.0.1:11434/api/ps', timeout=15) as response:
        processes = json.load(response)
    (out / 'ollama_processes.json').write_text(json.dumps(processes, indent=2) + '\n')
    loaded = next((m for m in processes['models'] if m.get('name', m.get('model')) == MODEL), None)
    if loaded is None or loaded.get('size_vram', 0) <= 0:
        raise RuntimeError('STOP: Ollama did not demonstrate GPU offload; CPU fallback is not accepted as GPU latency')
    state['steps']['DT1']['completed'] = True
    state['steps']['DT1']['size_vram'] = loaded['size_vram']
    commit(HARNESS, 'Record PILOT Deepthought manager pin and ten-call latency', [out], 'DT1')
    pin()
    check_gpu()
    out = PAPER / 'results/r1/engineering' / ('L12_live_' + stamp())
    cmd([PY, 'r1/scripts/l12_live_smoke.py', '--out', str(out)], log='DT2.log')
    state['steps']['DT2'] = {'completed': True, 'out': str(out), 'summary': json.loads((out / 'summary.json').read_text())}
    commit(PAPER, 'Record ENGINEERING_ONLY L12 live accounting smoke', ['r1/scripts/l12_live_smoke.py', out], 'DT2')
    pin()
    check_gpu()
    out = PAPER / 'results/r1/engineering' / ('E1b_llm_smoke_' + stamp())
    work = BATCH / 'r1_e1b_smoke_work'
    checks = collect(out, work, ['--nodes', 'digits_mlp', '--instances', '1', '--runs', '10',
                               '--points', '4', '--reps', '1', '--audit-seeds', '2', '--workers', '2',
                               '--label', 'ENGINEERING_ONLY', '--split', 'engineering'],
                     ['digits_mlp'])
    state['steps']['DT3'] = {'completed': True, 'out': str(out), 'checks': checks}
    commit(PAPER, 'Record ENGINEERING_ONLY E1b smoke with pinned LLM manager', [out], 'DT3')
    run_dt4(meta, version)


def _entrypoint():
    try:
        main()
    except Exception as exc:
        finish(f'{type(exc).__name__}: {exc}')
    else:
        finish(None)


if __name__ == '__main__':
    _entrypoint()
