"""Bounded test-only preservation checks; never run B1 or a model."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]
HARNESS=Path(os.environ.get('AR_HARNESS_ROOT','/nonexistent'))


def run_child(code, root):
    env={**os.environ,'PYTHONPATH':str(ROOT)+os.pathsep+str(HARNESS/'src'),
         'AR_HARNESS_ROOT':str(HARNESS),'PYTHONDONTWRITEBYTECODE':'1',
         'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    result=subprocess.run([sys.executable,'-B','-c',code,str(root)],cwd=ROOT,env=env,
                          capture_output=True,text=True,timeout=40)
    assert result.returncode==0,result.stdout+'\n'+result.stderr


def test_actual_pinned_controller_does_not_convert_collision_to_invalid(tmp_path):
    if not (HARNESS/'src').is_dir(): pytest.skip('requires pinned harness')
    assert subprocess.check_output(['git','-C',str(HARNESS),'rev-parse','HEAD'],text=True).strip()=='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    run_child(r'''
import os, shutil, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autoresearch.control_plane.campaign import run_real_campaign
from autoresearch.nodes.registry import load_registered_node
from autoresearch.manager.base import ManagerProposal
from r1.exam.campaign import FixtureWorker
from r1.tests import b1_synthetic_campaign_20261108 as adapter
from r1.tests.b1_synthetic_retention_20261108 import SyntheticRetentionStop
root=Path(sys.argv[1]);node=root/'node';harness=Path(os.environ['AR_HARNESS_ROOT'])
shutil.copytree(harness/'nodes/digits_mlp',node,ignore=shutil.ignore_patterns('__pycache__'))
spec=load_registered_node('digits_mlp',repo_root=harness)
editable=node/'train.py';before=editable.read_bytes()
archive=node/'_to_delete';archive.mkdir(mode=0o700)
collision=archive/'train.py.fixed';collision.write_bytes(b'protected-collision')
class Manager:
 mode='fixture';deterministic=True
 def propose_next_trial(self,status,memory_context,node_spec):
  old=status.current_constants['HIDDEN_UNITS']
  return ManagerProposal('fixture','edit','test',('train.py',),
    f'change HIDDEN_UNITS from {old} to 128',
    {'structured_edit':{'path':'train.py','symbol':'HIDDEN_UNITS','old':old,'new':'128'}})
ledger=root/'trials.jsonl'
try:
 with patch('r1.tests.b1_synthetic_retention_20261108.uuid.uuid4',return_value=SimpleNamespace(hex='fixed')):
  run_real_campaign(node_spec=spec,campaign_id='synthetic',budget=1,
   manager_mode='baseline_manager',memory_mode='append_only_summary',records_path=ledger,
   worker=FixtureWorker(node,9),proposal_backend=Manager())
except SyntheticRetentionStop:
 pass
else:
 raise AssertionError('pinned controller swallowed preservation STOP')
assert editable.read_bytes()==before
assert collision.read_bytes()==b'protected-collision'
assert not ledger.exists() or ledger.stat().st_size==0
print('ACTUAL_PINNED_CONTROLLER_STOP_PROPAGATED')
''',tmp_path)


def test_synthetic_lock_lifecycle_preserves_bytes_and_stop_order(tmp_path):
    if not (HARNESS/'src').is_dir(): pytest.skip('requires pinned harness')
    run_child(r'''
import json, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from r1.tests import b1_synthetic_trace_runner_20261108 as trace
root=Path(sys.argv[1]); lock=root/'runner.lock'; lock.write_text('{"pid":12345}')
old=lock.read_bytes(); events=[]
fake=SimpleNamespace(lock=lock, state={'phase':'b1'},cfg={'dryrun':True},b1_lease_fd=None,
                     stop_service=lambda:events.append('stop'))
trace.retained_close(fake,preserve_running=True)
assert lock.read_bytes()==old and events==[]
def failure(): raise RuntimeError('server-stop-failed')
fake.stop_service=failure
try: trace.retained_close(fake)
except RuntimeError: pass
else: raise AssertionError('stop failure lost')
assert lock.read_bytes()==old
fake.stop_service=lambda:events.append('stop')
trace.retained_close(fake)
assert not lock.exists() and events==['stop']
assert [p.read_bytes() for p in (root/'_to_delete').glob('runner.lock.*')]==[old]
lock.write_bytes(old)
with patch.object(trace.os,'kill',side_effect=ProcessLookupError):
 new=trace.retained_claim(root)
assert new==lock and lock.exists()
assert len(list((root/'_to_delete').glob('runner.lock.*')))==2
assert all(p.read_bytes()==old for p in (root/'_to_delete').glob('runner.lock.*'))
print('SYNTHETIC_LOCK_LIFECYCLE_PASS')
''',tmp_path)
