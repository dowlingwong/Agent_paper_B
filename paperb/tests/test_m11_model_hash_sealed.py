"""Execute exact source function in isolation; importing model.py requires torch."""
import ast
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def hash_function():
    source = Path(__file__).parents[1] / 'c3/train/model.py'
    tree = ast.parse(source.read_text())
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'sha256_file']
    assert len(definitions) == 1
    module = ast.Module(body=definitions, type_ignores=[])
    namespace = {'Path': Path, 'hashlib': hashlib}
    exec(compile(module, str(source), 'exec'), namespace)
    return namespace['sha256_file']


def test_direct_sealed_refused_before_open(tmp_path, hash_function):
    with patch('builtins.open', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'):
            hash_function(tmp_path / 'r1_sealed' / 'weights')


def test_case_alias_and_symlink_refused(tmp_path, hash_function):
    sealed = tmp_path / 'R1_SEALED'; sealed.mkdir()
    target = sealed / 'weights'; target.write_bytes(b'synthetic')
    alias = tmp_path / 'alias'; alias.symlink_to(target)
    for path in (target, alias):
        with pytest.raises(RuntimeError, match='r1_sealed'): hash_function(path)


def test_normal_file_hash_unchanged(tmp_path, hash_function):
    data = b'nonsealed synthetic bytes'; path = tmp_path / 'weights'; path.write_bytes(data)
    assert hash_function(path) == hashlib.sha256(data).hexdigest()
