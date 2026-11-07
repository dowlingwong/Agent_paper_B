from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.exam.b1_node_artifacts import B1ArtifactPreservationStop, preserve_node_artifacts


def test_previous_node_outputs_are_retained_across_invocations(tmp_path):
    root = tmp_path / 'node'
    root.mkdir()
    preserve_node_artifacts(root)
    for version in ('first', 'second'):
        artifacts = root / 'artifacts'
        artifacts.mkdir()
        (artifacts / 'metrics.json').write_text(version)
        (artifacts / 'run.log').write_text(version + '-log')
        preserve_node_artifacts(root)
        assert not artifacts.exists()
    archived = sorted((root / '_to_delete').iterdir())
    assert len(archived) == 2
    assert {p.joinpath('metrics.json').read_text() for p in archived} == {'first', 'second'}
    assert {p.joinpath('run.log').read_text() for p in archived} == {'first-log', 'second-log'}


def test_symlink_artifacts_are_never_followed(tmp_path):
    target = tmp_path / 'other'
    target.mkdir()
    (target / 'metrics.json').write_text('outside')
    root = tmp_path / 'node'
    root.mkdir()
    (root / 'artifacts').symlink_to(target, target_is_directory=True)
    with pytest.raises(B1ArtifactPreservationStop):
        preserve_node_artifacts(root)
    assert (target / 'metrics.json').read_text() == 'outside'
    assert (root / 'artifacts').is_symlink()


def test_worker_preserves_before_running_and_refuses_after_failure(tmp_path, monkeypatch):
    from autoresearch.worker.local_worker import LocalWorker
    from r1.exam import b1_node_artifacts, b1_proposal_guard

    observed = []
    monkeypatch.setattr(b1_proposal_guard, 'verify_proposal', lambda *_: observed.append('verify'))
    monkeypatch.setattr(b1_node_artifacts, 'preserve_node_artifacts', lambda *_: observed.append('preserve'))
    monkeypatch.setattr(LocalWorker, 'run_trial', lambda *_: observed.append('run'))
    worker = b1_proposal_guard.B1IntegrityWorker(node_root=tmp_path)
    worker.run_trial(SimpleNamespace(), SimpleNamespace(), 1)
    assert observed == ['verify', 'preserve', 'run']

    def fail(_root):
        raise B1ArtifactPreservationStop('STOP: simulated')
    monkeypatch.setattr(b1_node_artifacts, 'preserve_node_artifacts', fail)
    observed.clear()
    with pytest.raises(B1ArtifactPreservationStop):
        worker.run_trial(SimpleNamespace(), SimpleNamespace(), 2)
    assert observed == ['verify']


def test_b1_audit_keeps_prior_seed_outputs(tmp_path, monkeypatch):
    from r1.c3.audit import run_config
    import r1.harness
    import autoresearch.nodes.registry as registry
    import autoresearch.worker.local_worker as worker_module

    harness = tmp_path / 'harness'
    (harness / 'nodes' / 'openml_demo').mkdir(parents=True)
    work = tmp_path / 'work'
    work.mkdir()
    spec = SimpleNamespace(editable_paths=(), metric_name='score')
    monkeypatch.setattr(r1.harness, 'import_harness', lambda: harness)
    monkeypatch.setattr(registry, 'load_registered_node', lambda *args, **kwargs: spec)

    class FakeWorker:
        def __init__(self, *, node_root, **_kwargs):
            self.root = Path(node_root)

        def run_trial_at_seed(self, _proposal, _spec, _index, *, train_seed, split_seed):
            assert train_seed == split_seed
            output = self.root / 'artifacts'
            output.mkdir(exist_ok=True)
            (output / 'metrics.json').write_text(str(train_seed))
            (output / 'run.log').write_text(f'run {train_seed}')
            return SimpleNamespace(success=True, failure_message=None,
                                   parsed_metrics={'score': train_seed}, changed_files=())

    monkeypatch.setattr(worker_module, 'LocalWorker', FakeWorker)
    rows = run_config('openml_demo', {}, [1, 2, 3], str(work), preserve_node_outputs=True)
    assert [row['metric'] for row in rows] == [1, 2, 3]
    node = next(work.iterdir()) / 'openml_demo'
    assert (node / 'artifacts' / 'metrics.json').read_text() == '3'
    archived = list((node / '_to_delete').iterdir())
    assert {p.joinpath('metrics.json').read_text() for p in archived} == {'1', '2'}
    assert {p.joinpath('run.log').read_text() for p in archived} == {'run 1', 'run 2'}
