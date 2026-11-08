"""Only synthetic sealed paths; no model downloads or real sealed material."""
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from r1.c3.train import registry


@pytest.mark.parametrize('function', [registry.sha256_file, registry.git_blob_sha1])
def test_direct_hash_helpers_refuse_synthetic_sealed_before_open(tmp_path, function):
    path = tmp_path / 'r1_sealed' / 'item'
    with patch('builtins.open', side_effect=AssertionError('must not open')):
        with pytest.raises(RuntimeError, match='r1_sealed'): function(path)


def test_case_and_symlink_alias_refused(tmp_path):
    sealed = tmp_path / 'R1_SEALED'; sealed.mkdir()
    item = sealed / 'weights'; item.write_bytes(b'synthetic')
    alias = tmp_path / 'alias'; alias.symlink_to(item)
    for path in (item, alias):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.sha256_file(path)
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.git_blob_sha1(path)


def test_reverify_refuses_sealed_registry_before_read(tmp_path):
    with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.reverify(tmp_path / 'r1_sealed' / 'registry.yaml')


def test_reverify_refuses_indirect_sealed_file(tmp_path):
    reg = tmp_path / 'registry.yaml'
    reg.write_text(yaml.safe_dump({'models': {'synthetic': {'local_path': str(tmp_path / 'r1_sealed'),
                                                            'files': {'weights': {'sha256': 'irrelevant'}}}}}))
    with pytest.raises(RuntimeError, match='r1_sealed'): registry.reverify(reg)


def test_verify_dir_refuses_sealed_before_hub_or_download(tmp_path):
    with patch.object(registry, 'hub_tree', side_effect=AssertionError('no network')):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.verify_dir('kev-0.8b', tmp_path / 'r1_sealed')
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.download('kev-0.8b', tmp_path / 'r1_sealed')


def test_unsealed_reverify_and_hash_semantics_unchanged(tmp_path):
    model = tmp_path / 'model'; model.mkdir(); data = b'synthetic model bytes'
    (model / 'weights').write_bytes(data)
    reg = tmp_path / 'registry.yaml'
    reg.write_text(yaml.safe_dump({'models': {'synthetic': {'local_path': str(model),
                      'files': {'weights': {'sha256': hashlib.sha256(data).hexdigest()}}}}}))
    assert registry.reverify(reg) == []
    assert registry.git_blob_sha1(model / 'weights') == hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def test_cli_refuses_sealed_output_before_read_or_write(tmp_path):
    with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
        with pytest.raises(RuntimeError, match='r1_sealed'):
            registry.main(['--out', str(tmp_path / 'r1_sealed' / 'registry.yaml')])


def test_verify_dir_refuses_pinned_descendant_symlink_before_open(tmp_path):
    target = tmp_path / 'model'; target.mkdir()
    sealed = tmp_path / 'r1_sealed'; sealed.mkdir()
    item = sealed / 'weights'; item.write_bytes(b'synthetic')
    (target / 'weights').symlink_to(item)
    fake_tree = {'weights': {'size': 9, 'lfs_sha256': None, 'oid': None}}
    with patch.object(registry, 'hub_tree', return_value=fake_tree):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.verify_dir('kev-0.8b', target)


def test_verify_dir_retains_normal_fake_hub_behavior(tmp_path):
    target = tmp_path / 'model'; target.mkdir(); data = b'synthetic'
    (target / 'weights').write_bytes(data)
    fake_tree = {'weights': {'size': len(data), 'lfs_sha256': hashlib.sha256(data).hexdigest(), 'oid': None}}
    with patch.object(registry, 'hub_tree', return_value=fake_tree):
        result = registry.verify_dir('kev-0.8b', target)
    assert result['files']['weights']['sha256'] == hashlib.sha256(data).hexdigest()


def _download_target(base):
    repo, rev = registry.PINS['kev-0.8b']
    return base / f"{repo.replace('/', '__')}@{rev[:12]}"


def test_download_refuses_existing_sealed_target_before_network(tmp_path):
    sealed = tmp_path / 'r1_sealed'; sealed.mkdir()
    models = tmp_path / 'models'; models.mkdir()
    _download_target(models).symlink_to(sealed, target_is_directory=True)
    with patch('builtins.__import__', side_effect=AssertionError('network library import must not occur')):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.download('kev-0.8b', models)


def test_download_refuses_existing_sealed_child_before_network(tmp_path):
    sealed = tmp_path / 'r1_sealed'; sealed.mkdir(); (sealed / 'weights').write_bytes(b'synthetic')
    models = tmp_path / 'models'; models.mkdir(); target = _download_target(models); target.mkdir()
    (target / 'weights').symlink_to(sealed / 'weights')
    with patch('builtins.__import__', side_effect=AssertionError('network library import must not occur')):
        with pytest.raises(RuntimeError, match='r1_sealed'): registry.download('kev-0.8b', models)


def test_download_refuses_existing_nonsealed_directory_link(tmp_path):
    models = tmp_path / 'models'; models.mkdir(); target = _download_target(models); target.mkdir()
    other = tmp_path / 'other'; other.mkdir(); (target / 'alias').symlink_to(other, target_is_directory=True)
    with pytest.raises(registry.RegistryError, match='directory symlink'):
        registry.download('kev-0.8b', models)


def test_download_new_unsealed_target_uses_fake_hub(tmp_path):
    import sys
    import types
    models = tmp_path / 'models'
    calls = []
    fake_hub = types.SimpleNamespace(snapshot_download=lambda *args, **kwargs: calls.append((args, kwargs)))
    with patch.dict(sys.modules, {'huggingface_hub': fake_hub}), \
         patch.object(registry, 'check_floor'), patch.object(registry, 'verify_dir', return_value={'ok': True}):
        assert registry.download('kev-0.8b', models) == {'ok': True}
    assert len(calls) == 1 and calls[0][1]['local_dir'] == str(_download_target(models))
