"""Required two-candidate/three-anchor Stage A + B1 kill/resume integration; no inference."""
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
    assert result.returncode==0,result.stdout+result.stderr+'\n'+'\n'.join(p.read_text()[-2500:] for p in root.glob('*.log'))
    summary=json.loads((root/'summary.json').read_text())
    assert summary['pass'] and all(summary['checks'].values())
