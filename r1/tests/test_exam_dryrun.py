"""Legacy combined dryrun is refused at the current Stage A safety boundary.

The old kill/resume-success assertion conflicts with the preserved STOP policy;
separate synthetic B1 tests cover the reviewed parent/child path. No inference.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from r1.harness import REPO


def test_exam_fake_end_to_end(tmp_path):
    root=tmp_path/'exam';env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(REPO)}
    result=subprocess.run([sys.executable,'-m','r1.scripts.exam_dryrun','--root',str(root)],cwd=REPO,env=env,
                          capture_output=True,text=True,timeout=360)
    assert result.returncode!=0
    log=(root/'stage-a_0.log').read_text()
    assert 'STOP: D3 cold-cache cooperative lease FD absent' in log
    assert not (root/'summary.json').exists()
    assert not (root/'stage-a').exists()
    assert not (root/'fake_calls.jsonl').exists()
