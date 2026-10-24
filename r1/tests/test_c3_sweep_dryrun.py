"""Desktop DRYRUN of the C3 label sweep with fault injection (fake Ollama, real CPU workers).

Runs ``r1/scripts/c3_sweep_dryrun.py --scenario both`` (about a minute):
``retry`` — the batch's server drops one request; bounded retry resends it with
the same seed and the batch completes; ``permanent`` — the server exits for
good; failed roots persist traceback / class / UTC time / attempts and the
runner stops cleanly.  Skipped on Ada and inside the fresh-clone suite.
AI-assisted (Claude).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(os.environ.get('R1_DRYRUN_CHILD') == '1' or platform.node().split('.')[0] == 'ucrtasl'
                    or shutil.which('tmux') is None,
                    reason='desktop integration only (not on Ada, not inside a DRYRUN batch, needs tmux)')
def test_c3_sweep_dryrun_retry_and_permanent_failure(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ('R1_DRYRUN', 'PYTHONPATH')}
    out = tmp_path / 'dryrun'
    done = subprocess.run([sys.executable, str(REPO / 'r1/scripts/c3_sweep_dryrun.py'), '--scenario', 'both',
                           '--out', str(out), '--deadline', '75'],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=170)
    summary = json.loads((out / 'summary.json').read_text())
    assert done.returncode == 0, json.dumps(summary, indent=2) + done.stderr[-2000:]
    retry = summary['scenarios']['retry']['checks']
    assert retry['resent_with_same_seed'] and retry['llm_calls_retried'] == 1 and retry['restart_refused']
    assert set(retry['commits']) == {'liveness', 'sweep_append_only_summary', 'sweep_none', 'index'}
    permanent = summary['scenarios']['permanent']['checks']
    assert 'root campaign failures' in permanent['stop_reason'] and permanent['failed_roots'] >= 1


DESKTOP_ONLY = pytest.mark.skipif(os.environ.get('R1_DRYRUN_CHILD') == '1' or platform.node().split('.')[0] == 'ucrtasl'
                                  or shutil.which('tmux') is None,
                                  reason='desktop integration only (not on Ada, not inside a DRYRUN batch, needs tmux)')


def _scenario(tmp_path, name):
    env = {k: v for k, v in os.environ.items() if k not in ('R1_DRYRUN', 'PYTHONPATH')}
    out = tmp_path / 'dryrun'
    done = subprocess.run([sys.executable, str(REPO / 'r1/scripts/c3_sweep_dryrun.py'), '--scenario', name,
                           '--out', str(out), '--deadline', '120'],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=170)
    summary = json.loads((out / 'summary.json').read_text())
    assert done.returncode == 0, json.dumps(summary, indent=2) + done.stderr[-2000:]
    return summary['scenarios'][name]['checks']


@DESKTOP_ONLY
def test_c3_sweep_dryrun_resumes_after_kill_mid_campaign(tmp_path):
    """RUNBOOK A.5: SIGKILL of the runner's process group mid-sweep, then ``--start`` again on the batch."""
    checks = _scenario(tmp_path, 'interrupt')
    assert checks['completed_before_kill'] and checks['roots_rerun_whole']
    assert not set(checks['completed_before_kill']) & set(checks['roots_rerun_whole'])
    assert checks['orphan_server_stopped'] in ('SIGTERM', 'SIGKILL')
    assert checks['table']['n_proposals'] > 0  # A.4: the finished batch directory -> C3 table


@DESKTOP_ONLY
def test_c3_sweep_dryrun_watchdog_restarts_a_killed_runner(tmp_path):
    """RUNBOOK A.8: the dedicated server gets SIGTERM mid-request; the watchdog records it and recovers."""
    checks = _scenario(tmp_path, 'watchdog')
    assert checks['runner_event']['kind'] == 'server_exited' and checks['runner_event']['signal'] == 'SIGTERM'
    assert 'fault=sigterm' in checks['last_server_request'] and checks['restarted_generation'] == 1
    assert checks['roots_rerun_whole'] or checks['root_failures_moved']
