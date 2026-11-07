"""Exercise pinned harness artifact writes without running a node."""
import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from r1.exam.b1_proposal_guard import B1IntegrityWorker
from r1.exam.b1_worker_artifact_guard import B1WorkerArtifactStop
from r1.tests.test_b1_editable_preservation import SPEC, make_worker, proposal


def test_partial_run_log_failure_stops_before_harness_exception_rewrite(tmp_path, monkeypatch):
    root, worker = make_worker(tmp_path)
    trial = worker._resolve_artifact_dir('trial-001')
    original_open = io.open
    attempts = []

    class FailingStream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stream.close()
        def write(self, text):
            self.stream.write(text[:7])
            raise OSError('injected partial write')

    def failing_open(path, mode='r', *args, **kwargs):
        if str(path).endswith('/run.log') and mode == 'x':
            attempts.append(str(path))
            return FailingStream(original_open(path, mode, *args, **kwargs))
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(io, 'open', failing_open)
    result = SimpleNamespace(stdout='partial log content', stderr='', returncode=0)
    with patch('autoresearch.worker.local_worker.subprocess.run', return_value=result), pytest.raises(B1WorkerArtifactStop):
        worker._run_command(SimpleNamespace(run_command='unused'), trial, 'trial-001')
    assert (trial / 'run.log').read_text() == 'partial'
    assert len(attempts) == 1


def test_existing_patch_or_log_is_not_overwritten(tmp_path):
    root, worker = make_worker(tmp_path)
    trial = worker._resolve_artifact_dir('trial-001')
    for name in ('patch.diff', 'run.log'):
        path = trial / name
        path.write_text('existing evidence')
        with pytest.raises(B1WorkerArtifactStop):
            path.write_text('replacement')
        assert path.read_text() == 'existing evidence'


def test_successful_worker_writes_patch_and_log(tmp_path):
    root, worker = make_worker(tmp_path)
    result = SimpleNamespace(stdout='val_score: 0.7', stderr='', returncode=0)
    with patch('autoresearch.worker.local_worker.subprocess.run', return_value=result):
        out = worker.run_trial(proposal(), SimpleNamespace(**SPEC.__dict__, run_command='unused'), 1)
    assert out.success
    assert (tmp_path / 'art' / 'trial-001' / 'patch.diff').is_file()
    assert (tmp_path / 'art' / 'trial-001' / 'run.log').read_text().startswith('val_score: 0.7')
