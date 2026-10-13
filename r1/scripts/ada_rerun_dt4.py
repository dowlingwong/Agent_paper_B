"""Fresh DT4 attempt on Ada under the author's GPU co-tenancy decision (PLAN §10, 13 Oct 2026).

DT1–DT3 are complete and are never repeated. The interrupted DT4 attempt of 13 Oct
(results/r1/pilot/E1b_20261013T090510Z) stays preserved and unanalysed; this is a new
collection with a new timestamp and the same design. Other users' processes on the
selected card are allowed and logged; a STOP happens only on insufficient free memory,
a partial or CPU load of the pinned model, or the existing collection rules.
"""
import ast
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import time
from urllib.request import Request, urlopen
from xml.etree import ElementTree

if platform.node().split('.')[0] != 'ucrtasl':
    raise SystemExit('STOP: Ada-only DT4 rerun')
previous = Path(os.environ['R1_PREVIOUS_BATCH'])
prior = json.loads((previous / 'batch_state.json').read_text())
for step in ('DT1', 'DT2', 'DT3'):
    if not prior['steps'].get(step, {}).get('completed'):
        raise SystemExit(f'STOP: {step} is not completed in the previous batch')
if prior['steps'].get('DT4', {}).get('completed') or not prior.get('partial_DT4_preserved'):
    raise SystemExit('STOP: previous batch is not the interrupted, preserved DT4 attempt')
if json.loads((previous / 'deepthought_disabled.json').read_text()).get('duplicate_launch_prevented') is not True:
    raise SystemExit('STOP: the Deepthought duplicate-launch hold is not confirmed')
MODELS = Path(os.environ['R1_OLLAMA_MODELS'])

# Load the shared helpers (constants, census, collect, run_dt4, finish) without running main().
source_path = Path(__file__).with_name('deepthought_batch1_resume.py')
tree = ast.parse(source_path.read_text())
assert isinstance(tree.body[-1], ast.Try)
tree.body.pop()
exec(compile(tree, str(source_path), 'exec'), globals())

plan = (PAPER / 'docs/r1/PLAN.md').read_text()
for row in ('R1-COMPUTE (GPU co-tenancy, 13 Oct)', 'R1-COMPUTE (DT4 rerun, 13 Oct)'):
    if row not in plan:
        raise SystemExit(f'STOP: PLAN §10 lacks the author row {row}')
head = git_output(PAPER, 'rev-parse', 'HEAD')
if head != git_output(PAPER, 'ls-remote', 'origin', 'refs/heads/main').split()[0]:
    raise SystemExit('STOP: paper checkout is not at origin/main')
if subprocess.run(['tmux', 'has-session', '-t', 'r1_ollama_resume_20261012'], capture_output=True).returncode == 0:
    raise SystemExit('STOP: a tmux session r1_ollama_resume_20261012 already exists')
(BATCH / 'dt4_rerun_claim').mkdir()  # Never cleared or reused; a second launch in this batch fails here.

state['previous_stopped_attempt'] = str(previous)
for step in ('DT1', 'DT2', 'DT3'):
    state['steps'][step] = dict(prior['steps'][step])
state['dt4_rerun'] = {'authorization': 'PLAN §10 R1-COMPUTE (DT4 rerun, 13 Oct) and (GPU co-tenancy, 13 Oct)',
                      'interrupted_attempt_preserved': 'results/r1/pilot/E1b_20261013T090510Z',
                      'paper_head_at_launch': head}


def select_card():
    """Wait for a card whose free memory covers the footprint plus margin; take the emptiest."""
    while True:
        rows, eligible = gpu_rows()
        wanted = os.environ.get('R1_GPU_UUID', 'auto')
        if wanted != 'auto':
            eligible = [r for r in eligible if r.split(',')[1].strip() == wanted]
        with (BATCH / 'gpu_wait.jsonl').open('a') as f:
            f.write(json.dumps({'label': 'ENGINEERING_ONLY', 'utc': stamp(), 'rows': rows,
                                'eligible': eligible}) + '\n')
        if eligible:
            return max(eligible, key=lambda r: int(r.split(',')[3].strip()))
        time.sleep(60)


try:
    save()
    state['gpu'] = select_card()
    uuid = state['gpu'].split(',')[1].strip()
    check_gpu()
    with socket.socket() as port_probe:
        port_probe.bind(('127.0.0.1', 11434))
    command = (f'CUDA_VISIBLE_DEVICES={uuid} OLLAMA_VULKAN=0 OLLAMA_HOST=127.0.0.1:11434 '
               f'OLLAMA_MODELS={MODELS} OLLAMA_NUM_PARALLEL=1 OLLAMA_KEEP_ALIVE=-1 '
               f'{OLLAMA} serve > {BATCH}/ollama_serve.log 2>&1')
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
        raise RuntimeError('STOP: dedicated model server did not start')
    pin()
    payload = json.dumps({'model': MODEL, 'prompt': 'Reply OK', 'stream': False,
                          'keep_alive': -1, 'options': {'num_predict': 1}}).encode()
    with urlopen(Request('http://127.0.0.1:11434/api/generate', data=payload,
                         headers={'Content-Type': 'application/json'}), timeout=300) as r:
        probe_result = json.load(r)
    with urlopen('http://127.0.0.1:11434/api/ps', timeout=15) as r:
        offload = json.load(r)
    (BATCH / 'gpu_offload_probe.json').write_text(json.dumps(
        {'label': 'ENGINEERING_ONLY', 'response': probe_result, 'processes': offload}, indent=2) + '\n')
    loaded = next((m for m in offload['models'] if m.get('name', m.get('model')) == MODEL), None)
    assert_full_offload(loaded, 'load probe')
    if loaded['digest'] != DIGEST:
        raise RuntimeError('STOP: loaded model digest differs from author pin')
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    selected = next(g for g in xml.findall('gpu') if g.findtext('uuid') == uuid)
    if not selected.findall('./processes/process_info'):
        raise RuntimeError('STOP: no process on the selected GPU after loading')
    state['model_loaded'] = True
    check_gpu()
    state['gpu_offload'] = {'size': loaded['size'], 'size_vram': loaded['size_vram'], 'full_offload': True,
                            'probe_tokens_max': 1, 'keep_alive': -1, 'host': platform.node()}
    meta = {'harness_commit': git_output(HARNESS, 'rev-parse', 'HEAD')}
    save()
    run_dt4(meta, version)
except Exception as exc:
    finish(f'{type(exc).__name__}: {exc}')
else:
    finish(None)
