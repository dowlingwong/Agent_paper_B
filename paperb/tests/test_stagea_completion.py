"""Runner-side release evidence: every native-server record under the run root is
covered, and an unstopped or still-live server blocks completion. No GPU/model."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.scripts import exam_runner


def _record(path: Path, *, pid: int, start_ticks: int, stopped='2026-10-31T00:00:00Z'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'pid': pid, 'start_ticks': start_ticks, 'stopped_utc': stopped}) + '\n')
    return path


def _runner(out: Path):
    (out / 'batch_state.json').write_text(json.dumps({'status': 'COMPLETE'}) + '\n')
    return SimpleNamespace(out=out)


def test_completion_covers_nested_qualification_and_server_records(tmp_path, monkeypatch):
    out = tmp_path / 'out'
    probe = _record(out / 'cand/stage-a/32768/qualification/probe_x/llama_server_9010.json',
                    pid=555000, start_ticks=777)
    served = _record(out / 'servers/cand/llama_server_9000.json', pid=555001, start_ticks=888)
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(evidence))
    monkeypatch.setattr('r1.exam.cache_proc.process_start_ticks', lambda pid: 424242)
    path = exam_runner._write_lease_completion(_runner(out))
    data = json.loads(Path(path).read_text())
    assert {row['record_path'] for row in data['servers']} == {str(probe.resolve()), str(served.resolve())}
    assert data['servers'][0]['record_sha256'] and data['servers'][1]['record_sha256']
    assert data['runner_pid'] == os.getpid() and data['runner_start_ticks'] == 424242


def test_completion_refuses_unstopped_and_live_records(tmp_path, monkeypatch):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(evidence))
    monkeypatch.setattr('r1.exam.cache_proc.process_start_ticks', lambda pid: 424242)
    out = tmp_path / 'out'
    _record(out / 'servers/cand/llama_server_9000.json', pid=555001, start_ticks=888, stopped=None)
    with pytest.raises(exam_runner.PreparationStop, match='incomplete for lease completion'):
        exam_runner._write_lease_completion(_runner(out))
    out = tmp_path / 'live'
    _record(out / 'servers/cand/llama_server_9000.json', pid=os.getpid(), start_ticks=424242)
    with pytest.raises(exam_runner.PreparationStop, match='still alive'):
        exam_runner._write_lease_completion(_runner(out))


def test_completion_refuses_without_evidence_dir(tmp_path, monkeypatch):
    monkeypatch.delenv('TRACKX_LEASE_EVIDENCE_DIR', raising=False)
    monkeypatch.setattr('r1.exam.cache_proc.process_start_ticks', lambda pid: 424242)
    out = tmp_path / 'out'
    _record(out / 'servers/cand/llama_server_9000.json', pid=555001, start_ticks=888)
    with pytest.raises(exam_runner.PreparationStop, match='evidence directory absent'):
        exam_runner._write_lease_completion(_runner(out))
