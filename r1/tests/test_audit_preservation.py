"""Synthetic filesystem checks; no harness trial or model is run."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.c3 import audit


def test_retire_preserves_contents(tmp_path):
    work = tmp_path / 'work'
    work.mkdir()
    (work / 'evidence').write_bytes(b'keep')
    retired = audit._retire_owned_work(work, audit._identity(work))
    assert not work.exists()
    assert retired.parent == tmp_path / '_to_delete'
    assert (retired / 'evidence').read_bytes() == b'keep'


def test_collision_stops_without_overwriting(tmp_path, monkeypatch):
    work = tmp_path / 'work'
    work.mkdir()
    (work / 'source').write_text('source')
    target = tmp_path / '_to_delete' / 'work-fixed'
    target.mkdir(parents=True)
    (target / 'existing').write_text('existing')
    monkeypatch.setattr(audit.uuid, 'uuid4', lambda: SimpleNamespace(hex='fixed'))
    with pytest.raises(RuntimeError, match='STOP'):
        audit._retire_owned_work(work, audit._identity(work))
    assert (work / 'source').read_text() == 'source'
    assert (target / 'existing').read_text() == 'existing'


def test_unsafe_retirement_root_stops(tmp_path):
    work = tmp_path / 'work'
    work.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (tmp_path / '_to_delete').symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match='STOP'):
        audit._retire_owned_work(work, audit._identity(work))
    assert work.is_dir()
    assert list(outside.iterdir()) == []


def test_changed_identity_stops(tmp_path):
    work = tmp_path / 'work'
    work.mkdir()
    with pytest.raises(RuntimeError, match='identity changed'):
        audit._retire_owned_work(work, (-1, -1))
    assert work.is_dir()


def test_run_plan_preserves_caller_tmp(tmp_path):
    supplied = tmp_path / 'caller'
    supplied.mkdir()
    (supplied / 'keep').write_text('caller data')
    result = audit.run_plan([], {}, tmp_path / 'out', seeds=(1, 2), workers=1, tmp=str(supplied))
    assert result['configs_run_this_call'] == 0
    assert (supplied / 'keep').read_text() == 'caller data'
    assert not (tmp_path / '_to_delete').exists()


def test_run_plan_retires_owned_tmp(tmp_path, monkeypatch):
    original = audit.tempfile.mkdtemp
    def create(*, prefix):
        return original(prefix=prefix, dir=tmp_path)
    monkeypatch.setattr(audit.tempfile, 'mkdtemp', create)
    audit.run_plan([], {}, tmp_path / 'out', seeds=(1, 2), workers=1)
    entries = list((tmp_path / '_to_delete').iterdir())
    assert len(entries) == 1
    assert entries[0].name.startswith('c3_audit_tmp_')


def test_run_config_preserves_worker_files_on_failure(tmp_path, monkeypatch):
    from r1 import harness
    harness_root = tmp_path / 'harness'
    (harness_root / 'nodes' / 'node').mkdir(parents=True)
    (harness_root / 'nodes' / 'node' / 'code.py').write_text('original')
    monkeypatch.setattr(harness, 'import_harness', lambda: harness_root)
    import autoresearch.nodes.registry as registry
    import autoresearch.worker.local_worker as local_worker
    monkeypatch.setattr(registry, 'load_registered_node', lambda *a, **k: SimpleNamespace(editable_paths=['code.py']))
    class FakeWorker:
        def __init__(self, node_root, artifact_dir, **kwargs):
            Path(artifact_dir).mkdir()
            (Path(artifact_dir) / 'partial').write_text('partial evidence')
        def run_trial_at_seed(self, *args, **kwargs):
            raise ValueError('synthetic failure')
    monkeypatch.setattr(local_worker, 'LocalWorker', FakeWorker)
    work_parent = tmp_path / 'work_parent'
    work_parent.mkdir()
    with pytest.raises(ValueError, match='synthetic failure'):
        audit.run_config('node', {'code.py': 'changed'}, [1], str(work_parent))
    retired = list((work_parent / '_to_delete').iterdir())
    assert len(retired) == 1
    assert (retired[0] / 'node' / 'code.py').read_text() == 'changed'
    assert (retired[0] / 'art' / 'partial').read_text() == 'partial evidence'
