"""Synthetic B1 harness provenance and pre-worker guard."""
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
from r1.exam import campaign, runtime


def test_clean_harness_source_hashes_and_dirty_rejection(tmp_path,monkeypatch):
    import r1.harness
    import autoresearch.nodes.registry as nodes
    repo=tmp_path/'harness';(repo/'nodes/digits_mlp').mkdir(parents=True)
    source=repo/'nodes/digits_mlp/train.py';source.write_text('synthetic source')
    env={**os.environ,'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid',
         'GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
    subprocess.run(['git','init','-q',str(repo)],env=env,check=True)
    subprocess.run(['git','-C',str(repo),'add','.'],env=env,check=True)
    subprocess.run(['git','-C',str(repo),'commit','-qm','fixture'],env=env,check=True)
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    monkeypatch.setattr(r1.harness,'harness_root',lambda:repo)
    monkeypatch.setattr(nodes,'load_registered_node',lambda *a,**k:SimpleNamespace(editable_paths=['train.py']))
    assert runtime.b1_harness_sources('digits_mlp',head)=={'train.py':runtime.digest_file(source)}
    source.write_text('changed')
    with pytest.raises(runtime.PreparationStop,match='clean and pinned'):
        runtime.b1_harness_sources('digits_mlp',head)


def test_worker_rejects_source_mismatch_before_output(tmp_path,monkeypatch):
    monkeypatch.setattr(campaign,'require_worker_host',lambda job:None)
    monkeypatch.setattr(runtime,'b1_harness_sources',lambda *a:{'train.py':'actual'})
    job={'phase':'b1','out':str(tmp_path/'out'),'dryrun':False,'node':'digits_mlp',
         'harness_commit':'pin','authority_config':{'harness_commit':'pin'},
         'node_source_sha256':{'train.py':'different'}}
    with pytest.raises(RuntimeError,match='initial node sources differ'):
        campaign._collect_b1_review(job)
    assert not (tmp_path/'out').exists()
