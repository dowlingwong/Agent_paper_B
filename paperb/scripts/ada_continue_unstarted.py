"""Continue only unstarted DT2–DT4 after a successful DT1 artifact commit."""
import ast
import json
import os
import platform
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, urlopen

assert platform.node().split('.')[0] == 'ucrtasl', 'STOP: Ada-only continuation'
assert os.environ['R1_GPU_UUID'] == 'auto' or os.environ['R1_GPU_UUID'].startswith('GPU-'), 'STOP: invalid GPU selector'
previous = Path(os.environ['R1_PREVIOUS_BATCH'])
prior = json.loads((previous / 'batch_state.json').read_text())
assert prior['steps']['DT1']['completed']
assert not any(k in prior['steps'] for k in ['DT2', 'DT3', 'DT4'])
assert "git', 'diff', '--cached', '--check" in prior['stop_reason']
source_path = Path(__file__).with_name('deepthought_batch1_resume.py')
source = source_path.read_text()
tree = ast.parse(source)
assert isinstance(tree.body[-1], ast.Try)
tree.body.pop()  # Load helpers without invoking the original claimed runner.
exec(compile(tree, str(source_path), 'exec'), globals())
state['previous_stopped_attempt'] = str(previous)
state['steps']['DT1'] = dict(prior['steps']['DT1'])
state['steps']['DT1']['commit'] = git_output(HARNESS, 'rev-parse', 'HEAD')
marker = "    commit(HARNESS, 'Record PILOT Deepthought manager pin and ten-call latency', [out], 'DT1')"
a = source.index(marker) + len(marker) + 1
b = source.rindex('\n\ntry:\n    main()')
exec(compile('def remaining():\n' + source[a:b], str(source_path), 'exec'), globals())

try:
    assert json.loads((BATCH / 'deepthought_disabled.json').read_text())['duplicate_launch_prevented']
    assert not json.loads((BATCH / 'postfix_comparison.json').read_text())['new_failures']
    save()
    while True:
        rows, free = gpu_rows()
        chosen = free if os.environ['R1_GPU_UUID'] == 'auto' else [
            r for r in free if r.split(',')[1].strip() == os.environ['R1_GPU_UUID']]
        with (BATCH / 'gpu_wait.jsonl').open('a') as f:
            f.write(json.dumps({'label': 'ENGINEERING_ONLY', 'utc': stamp(), 'free_selected_gpu': bool(chosen)}) + '\n')
        if chosen:
            break
        time.sleep(60)
    (BATCH / 'continuation_claim').mkdir()  # Never clear or reuse this claim.
    state['gpu'] = chosen[0]
    os.environ['R1_GPU_UUID'] = state['gpu'].split(',')[1].strip()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 11434))
    command = (f'CUDA_VISIBLE_DEVICES={os.environ["R1_GPU_UUID"]} OLLAMA_VULKAN=0 '
               f'OLLAMA_HOST=127.0.0.1:11434 OLLAMA_MODELS={previous}/ollama_models '
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
        raise RuntimeError('STOP: dedicated model server did not start')
    model = pin()
    check_gpu()
    payload = json.dumps({'model': MODEL, 'prompt': 'Reply OK', 'stream': False,
                          'keep_alive': '30m', 'options': {'num_predict': 1}}).encode()
    with urlopen(Request('http://127.0.0.1:11434/api/generate', data=payload,
                         headers={'Content-Type': 'application/json'}), timeout=300) as r:
        probe_result = json.load(r)
    with urlopen('http://127.0.0.1:11434/api/ps', timeout=15) as r:
        offload = json.load(r)
    (BATCH / 'gpu_offload_probe.json').write_text(json.dumps(
        {'label': 'ENGINEERING_ONLY', 'response': probe_result, 'processes': offload}, indent=2) + '\n')
    loaded = next(m for m in offload['models'] if m.get('name', m.get('model')) == MODEL)
    assert loaded['digest'] == DIGEST and loaded['size_vram'] > 0, 'STOP: pin/offload check failed'
    check_gpu()
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    selected = next(g for g in xml.findall('gpu') if g.findtext('uuid') == os.environ['R1_GPU_UUID'])
    assert selected.findall('./processes/process_info'), 'STOP: no process on selected GPU'
    state['gpu_offload'] = {'size_vram': loaded['size_vram'], 'verified_before_DT2': True,
                           'probe_tokens_max': 1, 'host': platform.node()}
    meta = {'harness_commit': git_output(HARNESS, 'rev-parse', 'HEAD')}
    save()
    remaining()
except Exception as exc:
    finish(f'{type(exc).__name__}: {exc}')
else:
    finish(None)
