import os
import stat
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.scripts import c3_mount_inode_candidate as guard


def test_no_recovered_fixture_or_seccomp_import_entry():
    import importlib.util
    assert importlib.util.find_spec('r1.scripts.c3_cache_offline_fixture') is None
    assert importlib.util.find_spec('r1.scripts.c3_replay_seccomp_candidate') is None


def test_valid_readonly_mount_binds_device_inode_and_mount_id():
    old=SimpleNamespace(st_mode=stat.S_IFDIR, st_dev=4, st_ino=55)
    new=SimpleNamespace(st_mode=stat.S_IFDIR, st_dev=4, st_ino=55)
    info='22 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n'
    proof=guard.verify_binding(old,new,'mnt_id:\t3\n','mnt_id:\t22\n',info,Path('/tmp/source'))
    assert proof['inode']==55 and proof['readonly_mount_id']==22


@pytest.mark.parametrize('kind', ['replaced','same_mount','rw','wrong_path','wrong_id','nested','shared'])
def test_racy_or_unprotected_mount_stops(kind):
    old=SimpleNamespace(st_mode=stat.S_IFDIR, st_dev=4, st_ino=55)
    new=SimpleNamespace(st_mode=stat.S_IFDIR, st_dev=4, st_ino=55 if kind!='replaced' else 56)
    after='3' if kind=='same_mount' else '22'
    path='/tmp/elsewhere' if kind=='wrong_path' else '/tmp/source'
    mount_id='23' if kind=='wrong_id' else '22'
    opts='rw' if kind=='rw' else 'ro'
    optional=' shared:1' if kind=='shared' else ''
    info=f'{mount_id} 2 4:1 / {path} {opts}{optional} - ext4 /dev/x ro\n'
    if kind=='nested': info += '30 22 4:1 / /tmp/source/nested rw - ext4 /dev/x rw\n'
    with pytest.raises(ValueError, match='STOP'):
        guard.verify_binding(old,new,'mnt_id:\t3\n',f'mnt_id:\t{after}\n',info,Path('/tmp/source'))


def test_reads_are_anchored_and_reject_symlink_and_traversal(tmp_path):
    root=tmp_path/'root'; root.mkdir(); (root/'x').write_bytes(b'content')
    (root/'link').symlink_to(root/'x')
    fd=os.open(root,os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert guard.read_relative_nofollow(fd,'x') == b'content'
        with pytest.raises(ValueError,match='STOP'): guard.read_relative_nofollow(fd,'link')
        with pytest.raises(ValueError,match='STOP'): guard.read_relative_nofollow(fd,'../other')
    finally:
        os.close(fd)


@pytest.mark.parametrize('entries', [
    '21 2 4:1 / /tmp/source rw - ext4 /dev/x rw\n22 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n',
    '21 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n22 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n',
    '22 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n22 2 4:1 / /tmp/source ro - ext4 /dev/x ro\n',
])
def test_stacked_or_duplicate_mountpoint_is_ambiguous(entries):
    value=SimpleNamespace(st_mode=stat.S_IFDIR,st_dev=4,st_ino=55)
    with pytest.raises(ValueError,match='ambiguous'):
        guard.verify_binding(value,value,'mnt_id:\t3\n','mnt_id:\t22\n',entries,Path('/tmp/source'))


def test_anchored_tree_read_does_not_follow_replaced_root(tmp_path):
    import hashlib
    root=tmp_path/'source'; root.mkdir(); (root/'nested').mkdir(); (root/'nested'/'x').write_bytes(b'original')
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:
        root.rename(tmp_path/'old-source')
        root.mkdir(); (root/'nested').mkdir(); (root/'nested'/'x').write_bytes(b'replaced')
        actual=guard.manifest_relative_nofollow(fd,'nested')
        assert actual == {'x':hashlib.sha256(b'original').hexdigest()}
    finally:
        os.close(fd)


def test_bind_and_raw_mount_always_stop_before_io(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(guard.os, 'open', lambda *args, **kwargs: calls.append('open'))
    monkeypatch.setattr(guard.os, 'readlink', lambda *args, **kwargs: calls.append('readlink'))
    with pytest.raises(ValueError, match='mounting is disabled'):
        guard.bind_readonly_fd_pinned(tmp_path / 'source', {'child_mount_namespace': 'mnt:[22]'})
    with pytest.raises(ValueError, match='mounting is disabled'):
        guard._raw_mount('/proc/self/fd/3', '/proc/self/fd/3', 4096)
    assert calls == []
