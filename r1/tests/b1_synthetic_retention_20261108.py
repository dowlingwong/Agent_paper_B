"""Test-owned DRYRUN file retirement; never install for production."""
import json
import uuid
from pathlib import Path


def retire(path):
    path=Path(path)
    if not path.exists() and not path.is_symlink(): return
    if path.is_symlink() or not path.is_file(): raise RuntimeError('STOP: unsafe synthetic evidence path')
    target_dir=path.parent/'_to_delete'
    target_dir.mkdir(mode=0o700,exist_ok=True)
    dest=target_dir/(path.name+'.'+uuid.uuid4().hex)
    if dest.exists() or dest.is_symlink(): raise RuntimeError('STOP: synthetic evidence collision')
    path.rename(dest)  # test-owned root, unique destination, no concurrent writers


def guarded_json(original):
    def write(path,data):
        path=Path(path)
        tmp=path.with_name(path.name+'.tmp')
        if tmp.exists() or tmp.is_symlink(): raise RuntimeError('STOP: stale synthetic temp')
        retire(path)
        return original(path,data)
    return write


def record_save(instance):
    path=instance.record_path
    retire(path)
    with path.open('x') as f: f.write(json.dumps(instance.record,indent=2)+'\n')
