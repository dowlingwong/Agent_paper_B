"""Filesystem-only synthetic tests; no model, host or replay."""
import os
from pathlib import Path

import pytest

from r1.c3.offline_cache_copy import copy_cache, CopyStop


def test_copy_is_new_inode_and_byte_identical(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'folder').mkdir()
    (source / 'folder' / 'cache.bin').write_bytes(b'fake cache payload')
    target = tmp_path / 'target'
    result = copy_cache(source, target)
    assert (target / 'folder' / 'cache.bin').read_bytes() == b'fake cache payload'
    assert (source / 'folder' / 'cache.bin').stat().st_ino != (target / 'folder' / 'cache.bin').stat().st_ino
    assert result['files'][0]['path'] == 'folder/cache.bin'
    assert result['offline_executability'] == 'NOT_ESTABLISHED'
    with pytest.raises(CopyStop, match='cache copy failed'):
        copy_cache(source, target)


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'fifo'])
def test_refuses_non_regular_or_hardlinked_source(tmp_path, kind):
    source = tmp_path / 'source'; source.mkdir()
    if kind == 'symlink':
        (source / 'item').symlink_to(tmp_path / 'outside')
    elif kind == 'hardlink':
        (tmp_path / 'outside').write_bytes(b'fake')
        os.link(tmp_path / 'outside', source / 'item')
    else:
        os.mkfifo(source / 'item')
    target = tmp_path / 'target'
    with pytest.raises(CopyStop, match='symlink or special|multiply linked'):
        copy_cache(source, target)
    assert target.is_dir()  # retained for inspection, never deleted


def test_source_symlink_and_destination_inside_source_are_refused(tmp_path):
    source = tmp_path / 'source'; source.mkdir(); (source / 'x').write_text('synthetic')
    (tmp_path / 'alias').symlink_to(source, target_is_directory=True)
    with pytest.raises(CopyStop):
        copy_cache(tmp_path / 'alias', tmp_path / 'copy')
    with pytest.raises(CopyStop, match='overlap'):
        copy_cache(source, source / 'copy')
    assert not (source / 'copy').exists()


def test_change_during_read_stops_and_preserves_destination(tmp_path, monkeypatch):
    import r1.c3.offline_cache_copy as module
    source = tmp_path / 'source'; source.mkdir(); item = source / 'x'; item.write_bytes(b'old')
    original = module.os.read; changed = False
    def read(fd, count):
        nonlocal changed
        data = original(fd, count)
        if data and not changed:
            changed = True
            item.write_bytes(b'new content')
        return data
    monkeypatch.setattr(module.os, 'read', read)
    with pytest.raises(CopyStop, match='source file changed'):
        copy_cache(source, tmp_path / 'target')
    assert (tmp_path / 'target').is_dir()
