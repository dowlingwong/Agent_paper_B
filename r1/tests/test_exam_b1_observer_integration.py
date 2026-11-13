"""Pinned harness + B1 observer CPU integration, loopback stand-in only."""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
DRIVER=ROOT/'r1/tests/exam_b1_observer_driver.py'

@pytest.mark.parametrize('mode',['ok','fail'])
def test_pinned_harness_observer_stop_and_journal(tmp_path,mode):
    harness=os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        if os.environ.get('R1_REQUIRE_B1_HARNESS')=='1': pytest.fail('pinned B1 harness required')
        pytest.skip('set AR_HARNESS_B1_ROOT to pinned harness')
    head=subprocess.check_output(['git','-C',harness,'rev-parse','HEAD'],text=True).strip()
    assert head=='a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
    out=tmp_path/mode
    env={**os.environ,'AR_HARNESS_ROOT':harness,'PYTHONDONTWRITEBYTECODE':'1'}
    proc=subprocess.run([sys.executable,str(DRIVER),str(out),mode],env=env,text=True,capture_output=True,timeout=90)
    assert proc.returncode==0,proc.stderr
    result=json.loads((out/'driver_result.json').read_text())
    obs=[r for r in result['requests'] if r['observer']]
    assert obs and all(r['body'].get('cache_prompt') is False for r in result['requests'])
    if mode=='ok':
        assert result['status']=='complete'
        manifest=json.loads((out/'root/campaign_manifest.json').read_text())
        assert manifest['observer_evidence']['calls']==len(obs)
        assert manifest['evidence_hashes']['a4_observer_requests.jsonl']==manifest['observer_evidence']['sha256']
    else:
        assert result['status']=='observer_stop' and len(obs)==1
        assert not (out/'root/campaign_manifest.json').exists()
        assert result['requests'][-1]['observer']


@pytest.mark.parametrize('delay, status', [(0.3, 'complete'), (2.5, 'observer_stop')])
def test_observer_timeout_threshold_is_the_constant_and_a_timeout_still_stops(tmp_path, delay, status):
    """R1-EXAM-B1-OBSERVER-TIMEOUT: the request uses OBSERVER_TIMEOUT_S (here replaced by 1 s in the driver); a
    slower answer is still a STOP with the journal kept, a faster one completes. Only the threshold changed."""
    harness=os.environ.get('AR_HARNESS_B1_ROOT')
    if not harness:
        if os.environ.get('R1_REQUIRE_B1_HARNESS')=='1': pytest.fail('pinned B1 harness required')
        pytest.skip('set AR_HARNESS_B1_ROOT to pinned harness')
    out=tmp_path/'slow'
    env={**os.environ,'AR_HARNESS_ROOT':harness,'PYTHONDONTWRITEBYTECODE':'1','OBS_DELAY_S':str(delay),'OBS_TIMEOUT_S':'1.0'}
    proc=subprocess.run([sys.executable,str(DRIVER),str(out),'slow'],env=env,text=True,capture_output=True,timeout=120)
    assert proc.returncode==0,proc.stderr
    result=json.loads((out/'driver_result.json').read_text())
    assert result['status']==status
    journal=[json.loads(s) for s in (out/'root/a4_observer_requests.jsonl').read_text().splitlines()]
    if status=='observer_stop':
        assert [r for r in result['requests'] if r['observer']].__len__()==1
        assert journal[-1]['event']=='stop' and 'timed out' in journal[-1]['error']
        assert not (out/'root/campaign_manifest.json').exists()
    else:
        assert not any(r['event']=='stop' for r in journal)
