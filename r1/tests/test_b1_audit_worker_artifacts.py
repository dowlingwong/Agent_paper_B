"""Exercise the pinned worker from the B1 audit entry point without a node run."""
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from r1.c3 import audit
from r1.exam.b1_worker_artifact_guard import B1WorkerArtifactStop, GuardedTrialPath


@pytest.mark.parametrize('preserve', [False, True])
def test_audit_worker_uses_guard_only_for_b1(tmp_path, monkeypatch, preserve):
    import r1.harness
    r1.harness.import_harness()
    import autoresearch.nodes.registry as registry
    from autoresearch.worker.local_worker import LocalWorker

    harness = tmp_path / 'harness'
    (harness / 'nodes' / 'fixture').mkdir(parents=True)
    spec = SimpleNamespace(name='fixture', editable_paths=(), metric_name='score', run_command='unused')
    monkeypatch.setattr(r1.harness, 'import_harness', lambda: harness)
    monkeypatch.setattr(registry, 'load_registered_node', lambda *args, **kwargs: spec)
    paths = []

    def run_trial(worker, proposal, node_spec, index, **kwargs):
        trial = worker._resolve_artifact_dir('trial-001')
        paths.append(trial)
        worker._run_command(node_spec, trial, 'trial-001')
        return SimpleNamespace(success=True, failure_message=None,
                               parsed_metrics={'score': 1.0}, changed_files=())

    monkeypatch.setattr(LocalWorker, 'run_trial_at_seed', run_trial)
    result = SimpleNamespace(stdout='partial log content', stderr='', returncode=0)
    original_open = io.open
    attempts = []

    class PartialWrite:
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
        if str(path).endswith('/run.log') and mode in ('x', 'w'):
            attempts.append(mode)
            if preserve:
                return PartialWrite(original_open(path, mode, *args, **kwargs))
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(io, 'open', failing_open)
    with patch('autoresearch.worker.local_worker.subprocess.run', return_value=result):
        if preserve:
            with pytest.raises(B1WorkerArtifactStop):
                audit.run_config('fixture', {}, [1], str(tmp_path), preserve_node_outputs=True)
            assert isinstance(paths[0], GuardedTrialPath)
            assert (paths[0] / 'run.log').read_text() == 'partial'
            assert attempts == ['x']
        else:
            rows = audit.run_config('fixture', {}, [1], str(tmp_path))
            assert type(paths[0]) is type(Path())
            assert (paths[0] / 'run.log').read_text().startswith('partial log content')
            assert attempts == ['w']
            assert rows[0]['success']
