"""Exact source functions with synthetic fake dependencies; no model load."""
import ast
import os
import stat
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def functions():
    source = Path(__file__).parents[1] / 'c3/train/model.py'
    tree = ast.parse(source.read_text())
    names = {'_guard_model_input', '_laya_core', 'build_model'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {n.name for n in nodes} == names
    ns = {'Path': Path, 'os': os, 'stat': stat, 'FAMILIES': ('kev', 'laya')}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
    return ns


def test_build_refuses_sealed_base_and_kw_before_loader(tmp_path, functions):
    for kw in ({}, {'init_from': tmp_path / 'r1_sealed' / 'checkpoint'},
               {'tokenizer_path': tmp_path / 'R1_SEALED' / 'tokenizer'}):
        base = tmp_path / 'r1_sealed' / 'base' if not kw else tmp_path / 'ordinary'
        functions['PointerWrapper'] = lambda *a, **k: pytest.fail('loader reached')
        with pytest.raises(RuntimeError, match='r1_sealed'): functions['build_model']('kev', base, **kw)


def test_laya_refuses_sealed_weights_or_encoder_before_import(tmp_path, functions):
    for encoder, weights in ((tmp_path / 'r1_sealed' / 'encoder', None),
                             (None, tmp_path / 'R1_SEALED' / 'weights')):
        with patch('builtins.__import__', wraps=__import__) as imported:
            with pytest.raises(RuntimeError, match='r1_sealed'): functions['_laya_core']({}, encoder, weights)
        assert not any(call.args[0] in ('laya', 'transformers') for call in imported.call_args_list)


def test_base_tree_sealed_file_symlink_and_directory_link_refused(tmp_path, functions):
    root = tmp_path / 'base'; root.mkdir(); sealed = tmp_path / 'r1_sealed'; sealed.mkdir()
    target = sealed / 'weights'; target.write_bytes(b'synthetic')
    (root / 'model.safetensors').symlink_to(target)
    with pytest.raises(RuntimeError, match='r1_sealed'): functions['_guard_model_input'](root)
    root2 = tmp_path / 'base2'; root2.mkdir(); ordinary = tmp_path / 'ordinary'; ordinary.mkdir()
    (root2 / 'dirlink').symlink_to(ordinary, target_is_directory=True)
    with pytest.raises(RuntimeError, match='directory symlink'): functions['_guard_model_input'](root2)


def test_nonsealed_paths_and_nonpath_object_preserve_dispatch(tmp_path, functions):
    root = tmp_path / 'base'; root.mkdir(); (root / 'config.json').write_text('{}')
    sentinel = object(); calls = []
    functions['PointerWrapper'] = lambda *a, **k: calls.append((a, k)) or sentinel
    assert functions['build_model']('kev', root) is sentinel
    assert functions['build_model']('kev', 'a-model-id') is sentinel
    assert functions['build_model']('kev', sentinel) is sentinel
    assert len(calls) == 3


def test_laya_object_config_fake_loader_still_dispatches(functions):
    fake_laya = types.ModuleType('laya'); fake_laya.common = types.SimpleNamespace(DecisionModel=lambda *a: ('ok', a))
    fake_transformers = types.ModuleType('transformers')
    fake_transformers.AutoModel = types.SimpleNamespace(from_config=lambda *a, **k: 'fake-encoder')
    with patch.dict(sys.modules, {'laya': fake_laya, 'transformers': fake_transformers}):
        assert functions['_laya_core']({'head_layers': 3}, object(), None)[0] == 'ok'
