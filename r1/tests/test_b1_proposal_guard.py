"""Pure mocked guard tests: no model, worker command, subprocess or temp file."""
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from autoresearch.manager.base import ManagerProposal
from autoresearch.worker.local_worker import LocalWorker
from r1.exam.b1_proposal_guard import B1IntegrityWorker, B1ProposalIntegrityStop

SPEC = SimpleNamespace(editable_paths=('train.py',), editable_symbols=('HIDDEN_UNITS',))

def proposal(mode='langgraph_manager', *, objective='change HIDDEN_UNITS from 64 to 128',
             new='128', structured=True, path='train.py'):
    edit = {'type': 'python_constant', 'path': path, 'symbol': 'HIDDEN_UNITS',
            'old': '64', 'new': new}
    return ManagerProposal(manager_mode=mode, proposal_summary='synthetic',
        proposal_rationale='synthetic', target_files=(path,), objective=objective,
        extra={'structured_edit': edit} if structured else {})

def fake_worker():
    return B1IntegrityWorker.__new__(B1IntegrityWorker)

@pytest.mark.parametrize('mode', ['langgraph_manager', 'scripted_random', 'random_valid'])
def test_matching_proposals_delegate_unchanged(mode):
    p = proposal(mode); before = asdict(p); sentinel = object()
    with patch.object(LocalWorker, 'run_trial', return_value=sentinel) as delegate:
        assert fake_worker().run_trial(p, SPEC, 1) is sentinel
    delegate.assert_called_once_with(p, SPEC, 1)
    assert asdict(p) == before


def test_noedit_internal_verify_delegates():
    p = proposal(objective='Run the restored configuration unchanged; make no edit.', structured=False)
    with patch.object(LocalWorker, 'run_trial', return_value='noedit') as delegate:
        assert fake_worker().run_trial(p, SPEC, 3) == 'noedit'
    delegate.assert_called_once_with(p, SPEC, 3)

@pytest.mark.parametrize('p', [
    proposal(objective='change HIDDEN_UNITS from 64 to 129'),
    proposal(objective='change HIDDEN_UNITS from 64 to 128', structured=False),
    proposal(objective='unparseable', structured=True),
    proposal(objective="change HIDDEN_UNITS from 64 to __import__('os').setsid()", new="__import__('os').setsid()"),
    proposal(objective='change HIDDEN_UNITS from 64 to 1e309', new='1e309'),
    proposal(path='elsewhere.py'),
])
def test_unsafe_or_inconsistent_proposals_stop_before_worker(p):
    delegate = Mock()
    with patch.object(LocalWorker, 'run_trial', delegate):
        with pytest.raises(B1ProposalIntegrityStop, match='STOP:'):
            try:
                fake_worker().run_trial(p, SPEC, 1)
            except Exception:
                pytest.fail('STOP must bypass the pinned Exception-to-invalid conversion')
    delegate.assert_not_called()


def test_case_insensitive_symbol_matches_pinned_worker():
    p = proposal(objective='change hidden_units from 64 to 128')
    with patch.object(LocalWorker, 'run_trial', return_value='ok'):
        assert fake_worker().run_trial(p, SPEC, 1) == 'ok'


def test_actual_random_and_scripted_anchor_proposals_pass_unchanged():
    from autoresearch.manager.base import ManagerStatus
    from autoresearch.manager.random_valid import RandomValidManager
    from autoresearch.nodes.registry import load_registered_node
    from r1.harness import import_harness
    from r1.headroom.scripted_manager import ScriptedRandomManager
    spec = load_registered_node('digits_mlp', repo_root=import_harness())
    constants = {'HIDDEN_UNITS': '32', 'ALPHA': '0.0001',
                 'LEARNING_RATE_INIT': '0.001', 'BATCH_SIZE': '64', 'MAX_ITER': '100'}
    status = ManagerStatus('synthetic', 1, None, 'val_score', 'maximize',
                           current_constants=constants, effective_config=constants)
    grid = {key: [value, '128' if key in ('HIDDEN_UNITS', 'BATCH_SIZE', 'MAX_ITER') else '0.01']
            for key, value in constants.items()}
    managers = [RandomValidManager(grid), ScriptedRandomManager('digits_mlp', seed=17, repetition=0)]
    with patch.object(LocalWorker, 'run_trial', return_value='ok'):
        for manager in managers:
            p = manager.propose_next_trial(status, None, spec)
            before = asdict(p)
            assert fake_worker().run_trial(p, spec, 1) == 'ok'
            assert asdict(p) == before
