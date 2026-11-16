"""Synthetic filesystem checks; no harness trial or model is run."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.c3 import audit


def test_run_plan_preserves_caller_tmp(tmp_path):
    supplied = tmp_path / 'caller'
    supplied.mkdir()
    (supplied / 'keep').write_text('caller data')
    result = audit.run_plan([], {}, tmp_path / 'out', seeds=(1, 2), workers=1, tmp=str(supplied))
    assert result['configs_run_this_call'] == 0
    assert (supplied / 'keep').read_text() == 'caller data'


def test_run_plan_preserves_owned_tmp_in_place(tmp_path, monkeypatch):
    original = audit.tempfile.mkdtemp
    created = []
    def create(*, prefix):
        path = Path(original(prefix=prefix, dir=tmp_path))
        (path / 'evidence').write_bytes(b'keep')
        created.append(path)
        return str(path)
    monkeypatch.setattr(audit.tempfile, 'mkdtemp', create)
    audit.run_plan([], {}, tmp_path / 'out', seeds=(1, 2), workers=1)
    assert len(created) == 1
    assert (created[0] / 'evidence').read_bytes() == b'keep'


@pytest.mark.parametrize('fail', [False, True])
def test_run_config_preserves_worker_files_in_place(tmp_path, monkeypatch, fail):
    from r1 import harness
    harness_root = tmp_path / 'harness'
    (harness_root / 'nodes' / 'node').mkdir(parents=True)
    (harness_root / 'nodes' / 'node' / 'code.py').write_text('original')
    monkeypatch.setattr(harness, 'import_harness', lambda: harness_root)
    import autoresearch.nodes.registry as registry
    import autoresearch.worker.local_worker as local_worker
    monkeypatch.setattr(registry, 'load_registered_node', lambda *a, **k: SimpleNamespace(editable_paths=['code.py'], metric_name='m'))
    class FakeWorker:
        def __init__(self, node_root, artifact_dir, **kwargs):
            Path(artifact_dir).mkdir()
            (Path(artifact_dir) / 'partial').write_text('evidence')
        def run_trial_at_seed(self, *args, **kwargs):
            if fail:
                raise ValueError('synthetic failure')
            return SimpleNamespace(success=True, failure_message=None, parsed_metrics={'m': 1}, changed_files=[])
    monkeypatch.setattr(local_worker, 'LocalWorker', FakeWorker)
    work_parent = tmp_path / 'work_parent'
    work_parent.mkdir()
    if fail:
        with pytest.raises(ValueError, match='synthetic failure'):
            audit.run_config('node', {'code.py': 'changed'}, [1], str(work_parent))
    else:
        assert audit.run_config('node', {'code.py': 'changed'}, [1], str(work_parent))[0]['metric'] == 1
    work = list(work_parent.iterdir())
    assert len(work) == 1 and work[0].name.startswith('c3a_node_')
    assert (work[0] / 'node' / 'code.py').read_text() == 'changed'
    assert (work[0] / 'art' / 'partial').read_text() == 'evidence'
