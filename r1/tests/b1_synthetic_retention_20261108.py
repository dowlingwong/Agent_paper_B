"""Test-owned DRYRUN file retirement; never install for production."""
import json
import uuid
from pathlib import Path


class SyntheticRetentionStop(SystemExit):
    pass


def retire(path):
    try:
        path=Path(path)
        if not path.exists() and not path.is_symlink(): return
        if path.is_symlink() or not path.is_file(): raise RuntimeError('unsafe synthetic evidence path')
        target_dir=path.parent/'_to_delete'
        target_dir.mkdir(mode=0o700,exist_ok=True)
        dest=target_dir/(path.name+'.'+uuid.uuid4().hex)
        if dest.exists() or dest.is_symlink(): raise RuntimeError('synthetic evidence collision')
        path.rename(dest)  # test-owned root, unique destination, no concurrent writers
    except Exception as exc:
        raise SyntheticRetentionStop('STOP: cannot retain synthetic evidence') from exc


def guarded_json(original):
    def write(path,data):
        path=Path(path)
        tmp=path.with_name(path.name+'.tmp')
        if tmp.exists() or tmp.is_symlink(): raise SyntheticRetentionStop('STOP: stale synthetic temp')
        retire(path)
        try: return original(path,data)
        except Exception as exc: raise SyntheticRetentionStop('STOP: synthetic JSON write failed') from exc
    return write


def record_save(instance):
    path=instance.record_path
    retire(path)
    try:
        with path.open('x') as f: f.write(json.dumps(instance.record,indent=2)+'\n')
    except Exception as exc: raise SyntheticRetentionStop('STOP: synthetic record write failed') from exc
