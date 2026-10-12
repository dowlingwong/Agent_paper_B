"""Wait for the author's Ada GPU 0 and confirmed old-launcher shutdown."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import time
from xml.etree import ElementTree

BATCH = Path(os.environ['R1_BATCH_DIRECTORY'])
UUID = 'GPU-9be33fd1-8eeb-497d-772a-87362d6720be'
if platform.node().split('.')[0] != 'ucrtasl' or os.environ.get('R1_GPU_UUID') != UUID:
    raise SystemExit('STOP: this watcher is restricted to author-approved Ada GPU 0')
claim = BATCH / 'ada_runner_claim'
while True:
    if claim.exists():
        break
    try:
        xml = ElementTree.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x'], text=True))
        cards = xml.findall('gpu')
        card = next(g for g in cards if g.findtext('uuid') == UUID)
        if cards[0].findtext('uuid') != UUID:
            raise RuntimeError('STOP: GPU index 0 no longer matches the author-selected UUID')
        processes = [p.findtext('pid') for p in card.findall('./processes/process_info')]
        old = BATCH / 'deepthought_disabled.json'
        disabled = old.exists() and json.loads(old.read_text()).get('duplicate_launch_prevented') is True
        record = {'label': 'ENGINEERING_ONLY', 'utc': datetime.now(timezone.utc).isoformat(),
                  'gpu_uuid': UUID, 'process_pids': processes, 'duplicate_launch_prevented': disabled}
        with (BATCH / 'ada_wait.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')
        if disabled and not processes:
            try:
                claim.mkdir()
            except FileExistsError:
                break
            (claim / 'owner.json').write_text(json.dumps(record, indent=2) + '\n')
            with (BATCH / 'runner.log').open('a') as stream:
                result = subprocess.run([os.environ['AR_HARNESS_ROOT'] + '/.venv/bin/python',
                    os.environ['R1_PAPER_ROOT'] + '/r1/scripts/deepthought_batch1_resume.py'],
                    stdout=stream, stderr=subprocess.STDOUT)
            (claim / 'runner_exit.json').write_text(json.dumps({'label': 'ENGINEERING_ONLY',
                'utc': datetime.now(timezone.utc).isoformat(), 'returncode': result.returncode}, indent=2) + '\n')
            break
    except (OSError, subprocess.SubprocessError, ElementTree.ParseError, json.JSONDecodeError) as exc:
        with (BATCH / 'ada_wait.jsonl').open('a') as stream:
            stream.write(json.dumps({'label': 'ENGINEERING_ONLY', 'utc': datetime.now(timezone.utc).isoformat(),
                                     'infrastructure_error': repr(exc)}) + '\n')
    time.sleep(60)
