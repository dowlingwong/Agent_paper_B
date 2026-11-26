"""Real pinned worker/restore logic with synthetic local files and no node execution."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from autoresearch.control_plane import campaign as harness_campaign
from autoresearch.manager.base import ManagerProposal
from r1.exam.b1_editable_preserve import B1EditablePreservationStop, preserve_pinned_editables
from r1.exam.b1_proposal_guard import B1IntegrityWorker


SPEC=SimpleNamespace(editable_paths=('train.py',),editable_symbols=('HIDDEN_UNITS',),metric_name='val_score')

def proposal():
    return ManagerProposal(manager_mode='langgraph_manager',proposal_summary='synthetic',
        proposal_rationale='synthetic',target_files=('train.py',),
        objective='change HIDDEN_UNITS from 64 to 128',
        extra={'structured_edit':{'path':'train.py','symbol':'HIDDEN_UNITS','old':'64','new':'128'}})


def archived(root):
    return sorted(p.read_bytes() for p in (root/'_to_delete').iterdir() if p.is_file())


def make_worker(tmp_path):
    root=tmp_path/'node';root.mkdir();(root/'train.py').write_text('HIDDEN_UNITS = 64\n')
    return root,B1IntegrityWorker(node_root=root,artifact_dir=tmp_path/'art',train_seed=9,split_seed=9)


def test_actual_pinned_worker_edit_preserves_old_file(tmp_path):
    root,worker=make_worker(tmp_path)
    with preserve_pinned_editables(worker,SPEC), patch.object(worker,'_run_command',return_value=(None,True,None,{'val_score':0.7},None)):
        result=worker.run_trial(proposal(),SPEC,1)
    assert result.success and result.parsed_metrics['val_score']==0.7
    assert (root/'train.py').read_text()=='HIDDEN_UNITS = 128\n'
    assert archived(root)==[b'HIDDEN_UNITS = 64\n']


def test_actual_pinned_worker_failure_restores_and_preserves_both_versions(tmp_path):
    root,worker=make_worker(tmp_path)
    with preserve_pinned_editables(worker,SPEC), patch.object(worker,'_run_command',return_value=(None,False,'synthetic failure',{},None)):
        result=worker.run_trial(proposal(),SPEC,1)
    assert not result.success
    assert (root/'train.py').read_text()=='HIDDEN_UNITS = 64\n'
    assert archived(root)==[b'HIDDEN_UNITS = 128\n',b'HIDDEN_UNITS = 64\n']


def test_actual_campaign_restore_retires_changed_and_absent_files(tmp_path):
    root,worker=make_worker(tmp_path)
    initial=harness_campaign._EditableStateSnapshot(root=root,contents={'train.py':b'HIDDEN_UNITS = 4\n'})
    with preserve_pinned_editables(worker,SPEC):
        harness_campaign._restore_editable_state(initial)
        assert (root/'train.py').read_bytes()==b'HIDDEN_UNITS = 4\n'
        missing=harness_campaign._EditableStateSnapshot(root=root,contents={'train.py':None})
        harness_campaign._restore_editable_state(missing)
    assert not (root/'train.py').exists()
    assert archived(root)==[b'HIDDEN_UNITS = 4\n',b'HIDDEN_UNITS = 64\n']


def test_overlay_restores_module_global_even_on_stop(tmp_path):
    root,worker=make_worker(tmp_path)
    original=harness_campaign._editable_path
    with pytest.raises(B1EditablePreservationStop):
        with preserve_pinned_editables(worker,SPEC), patch('r1.exam.b1_editable_preserve._retire_or_create',side_effect=B1EditablePreservationStop('STOP')):
            harness_campaign._restore_editable_state(harness_campaign._EditableStateSnapshot(root=root,contents={'train.py':b'other'}))
    assert harness_campaign._editable_path is original
    assert (root/'train.py').read_text()=='HIDDEN_UNITS = 64\n'


def test_actual_campaign_discard_restores_prior_edit_without_losing_versions(tmp_path):
    import shutil
    from autoresearch.memory.append_store import TrialAppendStore
    from autoresearch.nodes.registry import load_registered_node
    from r1.harness import import_harness
    harness=import_harness()
    spec=load_registered_node('digits_mlp',repo_root=harness)
    root=tmp_path/'node'
    shutil.copytree(harness/'nodes'/'digits_mlp',root,ignore=shutil.ignore_patterns('__pycache__'))
    worker=B1IntegrityWorker(node_root=root,artifact_dir=tmp_path/'art',train_seed=9,split_seed=9)
    original=(root/'train.py').read_bytes()
    class Manager:
        mode='fixture'
        deterministic=True
        def propose_next_trial(self,status,memory_context,node_spec):
            old=status.current_constants['HIDDEN_UNITS']
            new='64' if status.budget_index==1 else '128'
            return ManagerProposal('fixture','edit','synthetic',('train.py',),
                f'change HIDDEN_UNITS from {old} to {new}',
                {'structured_edit':{'path':'train.py','symbol':'HIDDEN_UNITS','old':old,'new':new}})
    run_command=[(None,True,None,{'val_score':0.7},None),(None,True,None,{'val_score':0.6},None)]
    ledger=tmp_path/'campaign_trials.jsonl'
    with preserve_pinned_editables(worker,spec), patch.object(worker,'_run_command',side_effect=run_command):
        harness_campaign.run_real_campaign(node_spec=spec,campaign_id='fixture',budget=2,
            manager_mode='baseline_manager',memory_mode='append_only_summary',records_path=ledger,
            worker=worker,proposal_backend=Manager())
    rows=TrialAppendStore(ledger).read_all()
    assert [row.decision.value for row in rows]==['kept','discarded']
    assert b'HIDDEN_UNITS = 64' in (root/'train.py').read_bytes()
    versions=archived(root)
    assert original in versions
    assert any(b'HIDDEN_UNITS = 128' in value for value in versions)
    assert any(b'HIDDEN_UNITS = 64' in value for value in versions)


def test_symlink_is_refused_without_touching_target(tmp_path):
    root, worker = make_worker(tmp_path)
    external = tmp_path / 'external'
    external.write_bytes(b'external evidence')
    (root / 'train.py').rename(root / 'prior_train.py')
    (root / 'train.py').symlink_to(external)
    snapshot = harness_campaign._EditableStateSnapshot(root=root, contents={'train.py': b'replacement'})
    with preserve_pinned_editables(worker, SPEC), pytest.raises(B1EditablePreservationStop):
        harness_campaign._restore_editable_state(snapshot)
    assert external.read_bytes() == b'external evidence'
    assert (root / 'train.py').is_symlink()
    assert (root / 'prior_train.py').read_bytes() == b'HIDDEN_UNITS = 64\n'
