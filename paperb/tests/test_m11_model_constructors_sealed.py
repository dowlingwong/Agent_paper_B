"""Exercise exact constructor sources to pre-loader boundary without torch."""
import ast
import os
import stat
import types
from pathlib import Path

import pytest


class BoundaryReached(Exception):
    pass


class FakeBase:
    def __init__(self, *args, **kwargs):
        raise BoundaryReached


@pytest.fixture
def constructors():
    source = Path(__file__).parents[1] / 'c3/train/model.py'
    tree = ast.parse(source.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_guard_model_input')
    nodes = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), helper]
    for name in ('PointerWrapper', 'LayaWrapper'):
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
        method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        nodes.append(ast.ClassDef(name=name, bases=[ast.Name(id='FakeBase', ctx=ast.Load())],
                                  keywords=[], body=[method], decorator_list=[]))
    namespace = {'Path': Path, 'os': os, 'stat': stat, 'FakeBase': FakeBase,
                 'torch': types.SimpleNamespace(float32='synthetic')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(source), 'exec'), namespace)
    return namespace


def test_direct_kev_base_and_warm_start_fail_before_parent_or_loader(tmp_path, constructors):
    klass = constructors['PointerWrapper']
    for base, init in ((tmp_path / 'r1_sealed' / 'model', None),
                       (tmp_path / 'ordinary', tmp_path / 'R1_SEALED' / 'checkpoint')):
        with pytest.raises(RuntimeError, match='r1_sealed'): klass(base, init_from=init)


def test_direct_laya_encoder_and_weights_fail_before_parent_or_loader(tmp_path, constructors):
    klass = constructors['LayaWrapper']
    for encoder, weights in ((tmp_path / 'r1_sealed' / 'encoder', None),
                             (None, tmp_path / 'R1_SEALED' / 'weights')):
        with pytest.raises(RuntimeError, match='r1_sealed'): klass({}, object(), encoder_config=encoder, weights=weights)


def test_direct_constructor_nested_sealed_alias_refused(tmp_path, constructors):
    root = tmp_path / 'ordinary'; root.mkdir()
    sealed = tmp_path / 'r1_sealed'; sealed.mkdir(); (sealed / 'weights').write_bytes(b'fake')
    (root / 'weights').symlink_to(sealed / 'weights')
    with pytest.raises(RuntimeError, match='r1_sealed'): constructors['PointerWrapper'](root)
    with pytest.raises(RuntimeError, match='r1_sealed'):
        constructors['LayaWrapper']({}, object(), encoder_config=root)


def test_nonsealed_and_nonpath_inputs_reach_original_constructor_boundary(tmp_path, constructors):
    base = tmp_path / 'ordinary'; base.mkdir(); (base / 'config').write_text('{}')
    with pytest.raises(BoundaryReached): constructors['PointerWrapper'](base)
    with pytest.raises(BoundaryReached): constructors['PointerWrapper']('remote-model-id')
    with pytest.raises(BoundaryReached): constructors['LayaWrapper']({}, object(), encoder_config=object())
