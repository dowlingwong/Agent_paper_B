import gzip
import os
import sys
from pathlib import Path

import pytest
from r1.harness import import_harness
HARNESS = import_harness()
from autoresearch.nodes.registry import load_registered_node
from autoresearch.manager.base import ManagerProposal
from autoresearch.worker.local_worker import LocalWorker
from r1.exam.b1_openml_cache_guard import B1OpenMLWorkerMixin, B1OpenMLCacheStop


class Worker(B1OpenMLWorkerMixin, LocalWorker):
    pass

@pytest.mark.parametrize('bad', [False, True])
def test_pinned_worker_real_sklearn_cache_failure_preserves_evidence(tmp_path, monkeypatch, bad):
    node = tmp_path / 'node'; node.mkdir()
    cache = node/'data_cache/openml.org/api/v1/json/data/29.gz'
    cache.parent.mkdir(parents=True)
    cache.write_bytes(gzip.compress(b'{bad json' if bad else b'{"ok": true}'))
    before = cache.read_bytes()
    (node/'neighbour.py').write_text('value = 1\n')
    (node/'train.py').write_text('''import neighbour\nassert neighbour.value == 1\nfrom sklearn.datasets import _openml\nreal = _openml._open_openml_url\ncount = [0]\ndef tracked(*a, **k):\n count[0] += 1\n return real(*a, **k)\n_openml._open_openml_url = tracked\ntry:\n _openml._get_json_content_from_openml_api("https://www.openml.org/api/v1/json/data/29", None, "data_cache")\nfinally:\n print("opens=", count[0], flush=True)\nprint("val_auc: 0.5")\n''')
    artifacts=tmp_path/'art'; artifacts.mkdir()
    monkeypatch.setenv('PATH',str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'])
    spec=load_registered_node('openml_credit_approval',repo_root=HARNESS)
    worker=Worker(node_root=node,artifact_dir=artifacts)
    proposal=ManagerProposal(manager_mode='c3_audit',proposal_summary='audit',proposal_rationale='',target_files=spec.editable_paths,objective='Audit run; no change.')
    if bad:
        with pytest.raises(B1OpenMLCacheStop): worker.run_trial_at_seed(proposal,spec,1,train_seed=123,split_seed=123)
    else:
        result=worker.run_trial_at_seed(proposal,spec,1,train_seed=123,split_seed=123)
        assert result.success is True
    log=(artifacts/'trial-001'/'run.log').read_text()
    assert 'opens= 1' in log
    if bad: assert 'B1_OPENML_CACHE_FAILURE_STOP_20261107' in log
    assert cache.read_bytes()==before
