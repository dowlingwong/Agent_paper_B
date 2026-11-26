"""Run exact model source methods in isolation using synthetic fake dependencies."""
import ast
import hashlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def load_wrapper():
    source = Path(__file__).parents[1] / 'c3/train/model.py'
    tree = ast.parse(source.read_text())
    model = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == '_Wrapper')
    load = next(n for n in model.body if isinstance(n, ast.FunctionDef) and n.name == 'load')
    sha = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'sha256_file')
    ns = dict(Path=Path, json=json, hashlib=hashlib, MANIFEST='manifest.json',
              ADAPTER_FILE='adapter/adapter_model.safetensors', HEADS_FILE='heads.safetensors',
              IntegrityError=RuntimeError)
    exec(compile(ast.Module(body=[sha, load], type_ignores=[]), str(source), 'exec'), ns)
    return ns['load']


def test_sealed_root_refused_before_optional_import_or_read(tmp_path, load_wrapper):
    with patch('builtins.__import__', wraps=__import__) as imported, \
         patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'):
            load_wrapper(object(), tmp_path / 'r1_sealed' / 'model')
    assert not any(call.args[0] in ('peft', 'safetensors.torch') for call in imported.call_args_list)


def test_sealed_manifest_symlink_refused_before_read(tmp_path, load_wrapper):
    sealed = tmp_path / 'R1_SEALED'; sealed.mkdir(); target = sealed / 'manifest'; target.write_text('{}')
    model = tmp_path / 'model'; model.mkdir(); (model / 'manifest.json').symlink_to(target)
    with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'): load_wrapper(object(), model)


def test_unsealed_synthetic_load_uses_verified_files(tmp_path, load_wrapper):
    model = tmp_path / 'model'; (model / 'adapter').mkdir(parents=True)
    files = {'adapter/adapter_model.safetensors': b'fake adapter', 'heads.safetensors': b'fake heads'}
    for name, content in files.items(): (model / name).write_bytes(content)
    record = {'family': 'synthetic', 'head_form': 'synthetic', 'action_head': False,
              'files': {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}}
    (model / 'manifest.json').write_text(json.dumps(record))
    loaded = []
    fake_peft = types.ModuleType('peft')
    fake_peft.get_peft_model_state_dict = lambda obj: {'adapter-key': 1}
    fake_peft.set_peft_model_state_dict = lambda obj, state: types.SimpleNamespace(unexpected_keys=[])
    fake_safetensors = types.ModuleType('safetensors')
    fake_torch = types.ModuleType('safetensors.torch')
    fake_torch.load_file = lambda path: loaded.append(path) or {'adapter-key': 1}
    dummy = types.SimpleNamespace(describe=lambda: dict(family='synthetic', head_form='synthetic', action_head=False),
                                  _peft=lambda: object(), heads=types.SimpleNamespace(load_state_dict=lambda *a, **k: None))
    with patch.dict(sys.modules, {'peft': fake_peft, 'safetensors': fake_safetensors, 'safetensors.torch': fake_torch}):
        assert load_wrapper(dummy, model) == record
    assert len(loaded) == 2


def test_unsealed_manifest_cannot_pin_sealed_adapter(tmp_path, load_wrapper):
    model = tmp_path / 'model'; (model / 'adapter').mkdir(parents=True)
    sealed = tmp_path / 'r1_sealed'; sealed.mkdir(); target = sealed / 'adapter'; target.write_bytes(b'fake')
    (model / 'adapter/adapter_model.safetensors').symlink_to(target)
    (model / 'heads.safetensors').write_bytes(b'fake')
    record = {'family': 'synthetic', 'head_form': 'synthetic', 'action_head': False,
              'files': {'adapter/adapter_model.safetensors': 'ignored', 'heads.safetensors': 'ignored'}}
    (model / 'manifest.json').write_text(json.dumps(record))
    fake_peft = types.ModuleType('peft'); fake_peft.get_peft_model_state_dict = lambda obj: {}
    fake_peft.set_peft_model_state_dict = lambda obj, state: None
    fake_safetensors = types.ModuleType('safetensors'); fake_torch = types.ModuleType('safetensors.torch')
    fake_torch.load_file = lambda path: (_ for _ in ()).throw(AssertionError('must not load'))
    dummy = types.SimpleNamespace(describe=lambda: dict(family='synthetic', head_form='synthetic', action_head=False))
    with patch.dict(sys.modules, {'peft': fake_peft, 'safetensors': fake_safetensors, 'safetensors.torch': fake_torch}):
        with pytest.raises(RuntimeError, match='r1_sealed'): load_wrapper(dummy, model)
