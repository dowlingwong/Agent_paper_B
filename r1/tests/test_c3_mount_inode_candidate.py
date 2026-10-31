import os
import stat
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.scripts import c3_mount_inode_candidate as guard


def test_recovered_fixture_cli_is_explicitly_blocked():
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, '-m', 'r1.scripts.c3_cache_offline_fixture'],
        check=False, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'STOP: recovered fixture is not authorized for execution' in result.stderr


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


def test_bind_pinning_rejects_replaced_directory_and_closes_fds(tmp_path,monkeypatch):
    root=tmp_path/'source'; root.mkdir(); other=tmp_path/'other'; other.mkdir()
    opened=[]; original_read=Path.read_text; real_readlink=os.readlink
    def fake_open(path):
        fd=os.open(root if not opened else other,os.O_RDONLY|os.O_DIRECTORY)
        opened.append(fd)
        return fd
    def fake_text(path,*a,**k):
        if str(path)=='/proc/self/mountinfo': return '1 2 4:1 / / rw - ext4 /dev/x rw\n'
        if str(path).startswith('/proc/self/fdinfo/'): return 'mnt_id:\t3\n'
        return original_read(path,*a,**k)
    def fake_link(path,*a,**k):
        return 'mnt:[22]' if path=='/proc/self/ns/mnt' else real_readlink(path,*a,**k)
    called=[]
    monkeypatch.setattr(guard.os,'getuid',lambda:0)
    monkeypatch.setattr(guard.os,'readlink',fake_link)
    monkeypatch.setattr(Path,'read_text',fake_text)
    monkeypatch.setattr(guard,'open_dir_absolute_nofollow',fake_open)
    monkeypatch.setattr(guard,'_raw_mount',lambda source,target,flags:called.append((source,target,flags)))
    with pytest.raises(ValueError,match='changed'):
        guard.bind_readonly_fd_pinned(root,{'child_mount_namespace':'mnt:[22]'})
    assert len(called)==1
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)


def test_never_remounts_if_reopened_fd_has_original_mount_id(tmp_path,monkeypatch):
    root=tmp_path/'source'; root.mkdir(); opened=[]; original_read=Path.read_text; real_readlink=os.readlink
    def fake_open(path):
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY); opened.append(fd); return fd
    def fake_text(path,*a,**k):
        if str(path)=='/proc/self/mountinfo': return '3 2 4:1 / / rw - ext4 /dev/x rw\n'
        if str(path).startswith('/proc/self/fdinfo/'): return 'mnt_id:\t3\n'
        return original_read(path,*a,**k)
    def fake_link(path,*a,**k):
        return 'mnt:[22]' if path=='/proc/self/ns/mnt' else real_readlink(path,*a,**k)
    called=[]
    monkeypatch.setattr(guard.os,'getuid',lambda:0)
    monkeypatch.setattr(guard.os,'readlink',fake_link)
    monkeypatch.setattr(Path,'read_text',fake_text)
    monkeypatch.setattr(guard,'open_dir_absolute_nofollow',fake_open)
    monkeypatch.setattr(guard,'_raw_mount',lambda source,target,flags:called.append((source,target,flags)))
    with pytest.raises(ValueError,match='distinct mount'):
        guard.bind_readonly_fd_pinned(root,{'child_mount_namespace':'mnt:[22]'})
    assert len(called)==1  # bind attempted; no remount of the wrong FD
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)
