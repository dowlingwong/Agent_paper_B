"""String-only reproducer; no file edits, eval, worker execution, model or host."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from r1.harness import import_harness
root = import_harness()
from autoresearch.control_plane import campaign
from autoresearch.manager.base import ManagerStatus
from autoresearch.manager.langgraph_manager import _validate_proposal
from autoresearch.nodes.registry import load_registered_node
from autoresearch.worker.local_worker import _parse_change_directive

spec = load_registered_node('digits_mlp', repo_root=root)
status = ManagerStatus('synthetic', 1, None, 'val_score', 'maximize',
                       current_constants={'HIDDEN_UNITS': '64'})
for value in ['129', "__import__('os').setsid()"]:
    raw = {'summary': 'synthetic', 'rationale': 'synthetic',
           'objective': f'change HIDDEN_UNITS from 64 to {value}',
           'param': 'HIDDEN_UNITS', 'old_value': '64', 'new_value': '128'}
    state = {'raw_proposal': json.dumps(raw), 'status': status, 'node_spec': spec,
             'context_text': 'synthetic', 'proposal_schema': 'manager_proposal/v1'}
    proposal = _validate_proposal(state)['proposal']
    with patch.object(campaign, 'parse_train_constants', return_value={'HIDDEN_UNITS': '64'}):
        failure = campaign._precondition_failure_result(
            proposal, spec, SimpleNamespace(node_root=Path('/synthetic')))
    edit = _parse_change_directive(proposal.objective)
    ast.parse(f'{edit[0]} = {edit[2]}')  # syntax analysis only; do not execute
    print(json.dumps({'parse_ok': proposal.extra['llm_call']['parse_ok'],
                      'precondition_failed': failure is not None,
                      'structured_new': proposal.extra['structured_edit']['new'],
                      'worker_objective_new': edit[2],
                      'assignment_syntax_valid': True}, sort_keys=True))
