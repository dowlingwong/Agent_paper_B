"""Synthetic-cache tests for the actual pinned OpenML loader, never replay.

Requires AR_M3_PINNED_HARNESS at the exact pinned Git checkout and sklearn
1.8.0. The fixture is sklearn's local iris test data relabelled with the pinned
node's numeric ID; it is synthetic test data, not real ionosphere evidence.
The monkeypatch detects Python urlopen attempts only, not network syscalls or
other processes. The production OpenML replay STOP is deliberately unchanged.
"""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import uuid

import pytest

from r1.c3.offline_preflight import HARNESS_COMMIT, SnapshotStop, cache_snapshot, snapshot


def pinned_harness():
    value=os.environ.get('AR_M3_PINNED_HARNESS')
    if not value:
        if os.environ.get('R1_REQUIRE_M3_HARNESS')=='1': pytest.fail('AR_M3_PINNED_HARNESS required')
        pytest.skip('set AR_M3_PINNED_HARNESS to the exact pinned checkout')
    path=Path(value)
    assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==HARNESS_COMMIT
    return path


def fixture_cache(cache, damage=None):
    import sklearn
    assert sklearn.__version__=='1.8.0'
    import sklearn.datasets.tests.data.openml.id_61 as fixture
    fixture_dir=Path(fixture.__file__).parent
    description=json.loads(gzip.decompress((fixture_dir/'api-v1-jd-61.json.gz').read_bytes()))
    description['data_set_description']['id']='59'
    base=cache/'openml'/'openml.org'
    files={
        base/'api/v1/json/data/59.gz':gzip.compress(json.dumps(description).encode()),
        base/'api/v1/json/data/features/59.gz':(fixture_dir/'api-v1-jdf-61.json.gz').read_bytes(),
        base/'api/v1/json/data/qualities/59.gz':(fixture_dir/'api-v1-jdq-61.json.gz').read_bytes(),
        base/'data/v1/download/61/iris.arff.gz':(fixture_dir/'data-v1-dl-61.arff.gz').read_bytes(),
    }
    for index,(path,data) in enumerate(files.items()):
        if damage=='missing' or (damage=='partial' and index==1):
            continue
        if damage=='corrupt' and index==0:
            data=b'not gzip'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return list(files)


def pinned_loader(tmp_path, harness):
    node=tmp_path/'openml_ionosphere';node.mkdir()
    for name in ('benchmark.py','dataset.json'):
        shutil.copyfile(harness/'nodes/openml_ionosphere'/name,node/name)
    spec=importlib.util.spec_from_file_location('m3_fixture_'+uuid.uuid4().hex,node/'benchmark.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.DATA_ID==59 and module.NODE_NAME=='openml_ionosphere'
    return module


def deny_network(monkeypatch):
    import sklearn.datasets._openml as openml
    attempts=[]
    def deny(request,*args,**kwargs):
        attempts.append(request.full_url);raise RuntimeError('fixture intercepted urlopen attempt')
    def deny_socket(*args,**kwargs): raise RuntimeError('fixture denies socket creation')
    def deny_unlink(*args,**kwargs): raise RuntimeError('fixture preserves cache files')
    monkeypatch.setattr(openml,'urlopen',deny)
    monkeypatch.setattr(socket,'socket',deny_socket)
    monkeypatch.setattr(openml.os,'unlink',deny_unlink)
    return attempts


def test_actual_pinned_loader_reads_complete_synthetic_cache_without_download(tmp_path,monkeypatch):
    harness=pinned_harness();module=pinned_loader(tmp_path,harness)
    fixture_cache(module.CACHE_DIR)
    before=cache_snapshot(module.CACHE_DIR)
    attempts=deny_network(monkeypatch)
    x,y=module._load_frame()
    assert len(x)==len(y)>0 and attempts==[]
    assert cache_snapshot(module.CACHE_DIR)==before
    result=snapshot(harness,'openml_ionosphere',module.CACHE_DIR)
    assert result['dataset_id']==59 and result['offline_executability']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('damage',['missing','partial','corrupt','wrong_id'])
def test_actual_pinned_loader_refuses_bad_synthetic_cache(tmp_path,monkeypatch,damage):
    harness=pinned_harness();module=pinned_loader(tmp_path,harness)
    fixture_cache(module.CACHE_DIR,damage)
    if damage=='wrong_id':
        module.DATA_ID=60
    attempts=deny_network(monkeypatch)
    if damage=='corrupt':
        with pytest.raises(gzip.BadGzipFile): module._load_frame()
    else:
        with pytest.raises(RuntimeError,match='fixture (intercepted urlopen attempt|preserves cache files)'):
            module._load_frame()
    if damage in ('missing','partial','wrong_id'): assert attempts


def test_snapshot_refuses_wrong_pin_or_symlink_cache(tmp_path,monkeypatch):
    harness=pinned_harness();cache=tmp_path/'cache';fixture_cache(cache)
    first=snapshot(harness,'openml_ionosphere',cache)
    assert first['cache']==cache_snapshot(cache)
    (cache/'link').symlink_to(cache/'openml',target_is_directory=True)
    with pytest.raises(SnapshotStop,match='symlink'): snapshot(harness,'openml_ionosphere',cache)
    import r1.c3.offline_preflight as module
    monkeypatch.setattr(module,'HARNESS_COMMIT','0'*40)
    with pytest.raises(SnapshotStop,match='wrong harness commit'): snapshot(harness,'openml_ionosphere',cache)


def test_snapshot_detects_cache_mutation_and_pinned_source_mismatch(tmp_path,monkeypatch):
    harness=pinned_harness();cache=tmp_path/'cache';fixture_cache(cache)
    before=snapshot(harness,'openml_ionosphere',cache)
    extra=cache/'unrelated.txt';extra.write_text('changed cache')
    after=snapshot(harness,'openml_ionosphere',cache)
    assert before['cache']['sha256']!=after['cache']['sha256']
    import r1.c3.offline_preflight as module
    real=module.subprocess.check_output
    def different_commit(*args,**kwargs):
        result=real(*args,**kwargs)
        if any('nodes/openml_ionosphere/benchmark.py' in str(x) for x in args[0]):
            return result+b'changed'
        return result
    monkeypatch.setattr(module.subprocess,'check_output',different_commit)
    with pytest.raises(SnapshotStop,match='differs from pinned commit'):
        snapshot(harness,'openml_ionosphere',cache)
