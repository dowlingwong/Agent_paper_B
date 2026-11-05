"""Pure private mount construction tests; the real mount syscall is mocked."""
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.c3 import offline_mounts as mounts


def test_readonly_file_closure_mount_and_digest(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir(mode=0o700)
    source=tmp_path/'binary';source.write_bytes(b'fixture executable')
    digest=hashlib.sha256(source.read_bytes()).hexdigest();calls=[]
    def fake_mount(src,dst,kind,flags,data):
        calls.append((src,str(dst),kind,flags,data))
        if flags==mounts.MS_BIND:
            os.chmod(dst,0o600);Path(dst).write_bytes(Path(src).read_bytes())
    monkeypatch.setattr(mounts,'_mount',fake_mount)
    monkeypatch.setattr(os,'statvfs',lambda _:SimpleNamespace(f_flag=os.ST_RDONLY))
    mounts.create_root(root,1048576)
    mounts.mount_closure(root,[{'source':str(source),'target':'/runtime/bin/python','sha256':digest}])
    assert (root/'runtime/bin/python').read_bytes()==source.read_bytes()
    assert calls[0][2]=='tmpfs' and calls[1][3]==mounts.MS_BIND
    assert calls[2][3]&mounts.MS_RDONLY


@pytest.mark.parametrize('target',['/proc/a','/dev/a','/work/a','/out/a','../outside','/a/../b','//a'])
def test_reserved_or_nonabsolute_targets_rejected(tmp_path,target):
    with pytest.raises(mounts.MountStop): mounts._target(tmp_path,target)


def test_source_mismatch_and_target_symlink_stop_before_bind(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();source=tmp_path/'source';source.write_bytes(b'expected')
    (root/'runtime').symlink_to(tmp_path,target_is_directory=True)
    calls=[];monkeypatch.setattr(mounts,'_mount',lambda *a:calls.append(a))
    bad={'source':str(source),'target':'/runtime/bin','sha256':'0'*64}
    with pytest.raises(mounts.MountStop,match='hash mismatch'):mounts.mount_closure(root,[bad])
    good={**bad,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    with pytest.raises(mounts.MountStop,match='non-directory target parent'):mounts.mount_closure(root,[good])
    assert calls==[]


def test_private_root_refuses_nonempty_and_insecure_directory(tmp_path,monkeypatch):
    calls=[];monkeypatch.setattr(mounts,'_mount',lambda *a:calls.append(a))
    insecure=tmp_path/'insecure';insecure.mkdir(mode=0o755);os.chmod(insecure,0o755)
    with pytest.raises(mounts.MountStop,match='owner-only'):mounts.create_root(insecure,1048576)
    occupied=tmp_path/'occupied';occupied.mkdir(mode=0o700);(occupied/'keep').write_text('keep')
    with pytest.raises(mounts.MountStop,match='not empty'):mounts.create_root(occupied,1048576)
    assert calls==[] and (occupied/'keep').read_text()=='keep'


def test_work_file_copy_checks_digest_and_never_overwrites(tmp_path):
    root=tmp_path/'root';(root/'work').mkdir(parents=True)
    source=tmp_path/'src';source.write_bytes(b'configuration')
    item={'source':str(source),'target':'/work/node/config.yaml',
          'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    mounts.populate_work(root,[item])
    assert (root/'work/node/config.yaml').read_bytes()==b'configuration'
    with pytest.raises(FileExistsError):mounts.populate_work(root,[item])
    with pytest.raises(mounts.MountStop,match='invalid working-file target'):
        mounts.populate_work(root,[{**item,'target':'/work/../outside'}])
    with pytest.raises(mounts.MountStop,match='hash mismatch'):
        mounts.populate_work(root,[{**item,'target':'/work/other','sha256':'0'*64}])
