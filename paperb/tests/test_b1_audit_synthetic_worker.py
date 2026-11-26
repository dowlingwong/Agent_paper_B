"""B1 audit seed plumbing with a synthetic worker; no model or GPU execution.

This does not replace the real LocalWorker determinism test on a qualified host.
"""
from types import SimpleNamespace
from r1.c3 import audit


def test_audit_run_config_binds_joint_seeds_to_worker(tmp_path, monkeypatch):
    import r1.harness
    r1.harness.import_harness()  # expose the pinned local module; no worker is run
    import autoresearch.nodes.registry as registry
    import autoresearch.worker.local_worker as local_worker
    harness=tmp_path/'synthetic_harness'; node=harness/'nodes'/'fixture'; node.mkdir(parents=True)
    (node/'train.py').write_text('synthetic only\n')
    spec=SimpleNamespace(editable_paths=('train.py',),metric_name='score')
    seen=[]
    class SyntheticWorker:
        def __init__(self, **kwargs):
            assert (kwargs['node_root']/'train.py').read_text()=='synthetic edit\n'
        def run_trial_at_seed(self, proposal, node_spec, budget_index, *, train_seed, split_seed):
            seen.append((budget_index,train_seed,split_seed))
            return SimpleNamespace(success=True, failure_message=None, parsed_metrics={'score':train_seed/10000},changed_files=())
    monkeypatch.setattr(r1.harness,'import_harness',lambda:harness)
    monkeypatch.setattr(registry,'load_registered_node',lambda node,repo_root:spec)
    monkeypatch.setattr(local_worker,'LocalWorker',SyntheticWorker)
    # Preserve artifacts rather than deleting any test-created directory.
    monkeypatch.setattr(audit.shutil,'rmtree',lambda *args,**kwargs:None)
    rows=audit.run_config('fixture',{'train.py':'synthetic edit\n'},[9101,9102],str(tmp_path))
    assert seen==[(1,9101,9101),(2,9102,9102)]
    assert [r['seed'] for r in rows]==[9101,9102]
    assert [r['metric'] for r in rows]==[0.9101,0.9102]
    assert all(r['success'] and not r['changed_files'] for r in rows)
