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
from r1.exam.b1_proposal_guard import B1IntegrityWorker


class Worker(B1OpenMLWorkerMixin, LocalWorker):
    pass

@pytest.mark.parametrize('bad', [False, True, 'missing'])
@pytest.mark.parametrize('worker_type', [Worker, B1IntegrityWorker])
@pytest.mark.parametrize('node_name', ['openml_credit_approval', 'openml_ionosphere'])
def test_pinned_worker_real_sklearn_cache_failure_preserves_evidence(tmp_path, monkeypatch, bad, worker_type, node_name):
    node = tmp_path / 'node'; node.mkdir()
    cache = node/'data_cache/openml.org/api/v1/json/data/29.gz'
    cache.parent.mkdir(parents=True)
    if bad != 'missing': cache.write_bytes(gzip.compress(b'{bad json' if bad else b'{"ok": true}'))
    before = cache.read_bytes() if cache.exists() else None
    (node/'neighbour.py').write_text('value = 1\n')
    (node/'train.py').write_text('''import socket\ndef forbidden(*a, **k):\n print("NETWORK_ATTEMPT", flush=True)\n raise RuntimeError("network attempted")\nsocket.socket.connect = forbidden\nsocket.getaddrinfo = forbidden\nimport neighbour\nassert neighbour.value == 1\nfrom sklearn.datasets import _openml\nreal = _openml._open_openml_url\ncount = [0]\ndef tracked(*a, **k):\n count[0] += 1\n return real(*a, **k)\n_openml._open_openml_url = tracked\ntry:\n _openml._get_json_content_from_openml_api("https://www.openml.org/api/v1/json/data/29", None, "data_cache")\nfinally:\n print("opens=", count[0], flush=True)\nprint("val_auc: 0.5")\n''')
    artifacts=tmp_path/'art'; artifacts.mkdir()
    monkeypatch.setenv('PATH',str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'])
    spec=load_registered_node(node_name,repo_root=HARNESS)
    worker=worker_type(node_root=node,artifact_dir=artifacts)
    proposal=ManagerProposal(manager_mode='c3_audit',proposal_summary='audit',proposal_rationale='',target_files=spec.editable_paths,objective='Run the restored configuration unchanged; make no edit.')
    if bad:
        with pytest.raises(B1OpenMLCacheStop): worker.run_trial_at_seed(proposal,spec,1,train_seed=123,split_seed=123)
    else:
        result=worker.run_trial_at_seed(proposal,spec,1,train_seed=123,split_seed=123)
        assert result.success is True
    log=(artifacts/'trial-001'/'run.log').read_text()
    assert 'opens= 1' in log
    assert 'NETWORK_ATTEMPT' not in log
    if bad: assert 'B1_OPENML_CACHE_FAILURE_STOP_20261107' in log
    assert (cache.read_bytes() if cache.exists() else None)==before
    assert sorted(p.name for p in cache.parent.iterdir()) == ([] if bad == 'missing' else ['29.gz'])


def test_initialization_failure_is_explicit_stop(monkeypatch, capsys):
    from r1.exam import b1_openml_cache_guard as guard
    def fail(_):
        raise ImportError('synthetic missing dependency')
    monkeypatch.setattr(guard, 'install', fail)
    with pytest.raises(SystemExit) as exc:
        guard.main()
    assert exc.value.code == guard.EXIT
    assert guard.MARKER in capsys.readouterr().err
