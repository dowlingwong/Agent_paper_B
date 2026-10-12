"""Monitor one authorized host; elect one batch runner on the shared Ceph filesystem."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from xml.etree import ElementTree

batch = Path(os.environ['R1_BATCH_DIRECTORY'])
host = platform.node().split('.')[0]
if host not in {'deepthought', 'deepthought2'}:
    raise SystemExit('STOP: unauthorized execution host')
claim = batch / 'runner_claim'
log = batch / ('gpu_wait_' + host + '.jsonl')

def census():
    xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
    cards = []
    for gpu in xml.findall('gpu'):
        processes = []
        for process in gpu.findall('./processes/process_info'):
            pid = process.findtext('pid')
            owner = subprocess.run(['ps', '-o', 'user=', '-p', pid], capture_output=True, text=True)
            processes.append({'pid': pid, 'owner': owner.stdout.strip(), 'type': process.findtext('type')})
        cards.append({'uuid': gpu.findtext('uuid'), 'name': gpu.findtext('product_name'),
                      'processes': processes, 'free_mib': gpu.findtext('./fb_memory_usage/free')})
    return {'label': 'ENGINEERING_ONLY', 'utc': datetime.now(timezone.utc).isoformat(),
            'host': host, 'cards': cards, 'free_gpu_uuids': [g['uuid'] for g in cards if not g['processes']]}

while True:
    if claim.exists():
        print('A runner has claimed this batch; this watcher exits without launching.', flush=True)
        break
    try:
        sample = census()
        with log.open('a') as stream:
            stream.write(json.dumps(sample) + '\n')
        if '--census-only' in sys.argv:
            print(json.dumps(sample), flush=True)
            break
        if sample['free_gpu_uuids']:
            try:
                claim.mkdir()
            except FileExistsError:
                break
            (claim / 'owner.json').write_text(json.dumps(sample, indent=2) + '\n')
            # Revalidate immediately; an occupied GPU never reaches the runner.
            confirmed = census()
            (claim / 'confirmation.json').write_text(json.dumps(confirmed, indent=2) + '\n')
            if not confirmed['free_gpu_uuids']:
                (claim / 'STOP.json').write_text(json.dumps({'label': 'ENGINEERING_ONLY',
                    'reason': 'GPU became occupied between election and launch; no model started'}, indent=2) + '\n')
                break
            with (batch / 'runner.log').open('a') as stream:
                result = subprocess.run(['/ceph/dwong/autoresearch_harness/.venv/bin/python',
                    '/ceph/dwong/agent_paper_B/r1/scripts/deepthought_batch1_resume.py'],
                    stdout=stream, stderr=subprocess.STDOUT)
            (claim / 'runner_exit.json').write_text(json.dumps({'label': 'ENGINEERING_ONLY',
                'host': host, 'returncode': result.returncode,
                'utc': datetime.now(timezone.utc).isoformat()}, indent=2) + '\n')
            break
    except (subprocess.SubprocessError, OSError, ElementTree.ParseError) as exc:
        with log.open('a') as stream:
            stream.write(json.dumps({'label': 'ENGINEERING_ONLY', 'host': host,
                'utc': datetime.now(timezone.utc).isoformat(), 'census_error': repr(exc)}) + '\n')
    time.sleep(60)
