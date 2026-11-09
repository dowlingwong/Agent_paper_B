"""Exercise the exact source function without importing optional torch dependencies."""
import ast
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def read_metrics():
    source = Path(__file__).parents[1] / 'c3/train/spike.py'
    tree = ast.parse(source.read_text())
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_read_metrics']
    assert len(definitions) == 1
    namespace = {'Path': Path}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['_read_metrics']


def test_sealed_run_refused_before_read(tmp_path, read_metrics):
    with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'): read_metrics(tmp_path / 'r1_sealed' / 'run')


def test_sealed_metrics_file_symlink_refused(tmp_path, read_metrics):
    sealed = tmp_path / 'R1_SEALED'; sealed.mkdir()
    target = sealed / 'metrics'; target.write_text('{"kind": "step", "loss": 1}\n')
    run = tmp_path / 'run'; run.mkdir(); (run / 'metrics.jsonl').symlink_to(target)
    with pytest.raises(RuntimeError, match='r1_sealed'): read_metrics(run)


def test_unsealed_step_filter_unchanged(tmp_path, read_metrics):
    (tmp_path / 'metrics.jsonl').write_text('{"kind": "step", "loss": 1}\n{"kind": "other"}\n')
    assert read_metrics(tmp_path) == [{'kind': 'step', 'loss': 1}]
