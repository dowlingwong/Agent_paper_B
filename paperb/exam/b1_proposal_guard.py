"""B1 pre-execution integrity STOP for the pinned LocalWorker proposal path.

The guard does not classify a proposal as invalid or rewrite it. It terminates
this B1 campaign before the worker changes any files if the advertised edit
and the objective actually parsed by the pinned worker do not agree. STOP is
not a completed trial and must never be automatically resumed.

R1-EXAM-B1-MODEL-OUTPUT-INVALID (13 Nov 2026): this file is unchanged in
behaviour. The same model-output conditions are now checked on the proposal
before the control plane calls the worker (``r1.exam.b1_proposal_precheck``),
where a failing proposal becomes an invalid trial. A proposal that still fails
here has bypassed that check, which is an internal inconsistency, so the STOP
stays.
"""
from __future__ import annotations

import ast
import math

from autoresearch.worker.local_worker import LocalWorker, _parse_change_directive
from r1.exam.b1_openml_cache_guard import B1OpenMLWorkerMixin

_NO_EDIT = 'Run the restored configuration unchanged; make no edit.'


class B1ProposalIntegrityStop(SystemExit):
    """Escape the pinned harness's Exception-to-invalid conversion."""


def verify_proposal(proposal, node_spec):
    """Check actual worker parsing without executing the proposed assignment."""
    edit = proposal.extra.get('structured_edit')
    parsed = _parse_change_directive(proposal.objective)
    if edit is None and parsed is None and proposal.objective == _NO_EDIT:
        return  # pinned harness's internal verify rerun of an existing config
    if not isinstance(edit, dict) or parsed is None:
        raise B1ProposalIntegrityStop('STOP: B1 structured edit or worker directive missing')
    symbol, old, new = parsed
    # The pinned worker resolves objective symbols case-insensitively.
    canonical = {s.lower(): s for s in node_spec.editable_symbols}.get(symbol.lower())
    if (canonical != str(edit.get('symbol', '')) or old != str(edit.get('old', '')) or
            new != str(edit.get('new', ''))):
        raise B1ProposalIntegrityStop('STOP: B1 worker directive and structured edit differ')
    path = edit.get('path')
    # All three B1 nodes have exactly one editable file; the worker otherwise
    # chooses the first target containing the symbol rather than edit['path'].
    if (tuple(node_spec.editable_paths) != (path,) or
            tuple(proposal.target_files) != (path,)):
        raise B1ProposalIntegrityStop('STOP: B1 edit path differs from worker target')
    # The pinned worker passes new into re.sub's replacement string while
    # replay inserts it literally. Backslashes can be interpreted as escapes
    # or group references, so reject rather than rewrite or execute them.
    if '\\' in new:
        raise B1ProposalIntegrityStop('STOP: B1 replacement has regex escape syntax')
    if str(path).endswith('.py'):
        # ast.literal_eval never evaluates function calls. Bound work before parsing.
        if len(new) > 256:
            raise B1ProposalIntegrityStop('STOP: B1 Python value is not a bounded numeric literal')
        try:
            value = ast.literal_eval(new)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            raise B1ProposalIntegrityStop('STOP: B1 Python value is not a numeric literal')
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            raise B1ProposalIntegrityStop('STOP: B1 Python value is not a finite numeric literal')


class B1IntegrityWorker(B1OpenMLWorkerMixin, LocalWorker):
    """Run the pinned worker after integrity checking, with an I/O overlay."""
    def _resolve_artifact_dir(self, trial_label):
        from r1.exam.b1_worker_artifact_guard import GuardedTrialPath
        return GuardedTrialPath(super()._resolve_artifact_dir(trial_label))

    def _locate_target_file(self, param, proposal, node_spec):
        path=super()._locate_target_file(param,proposal,node_spec)
        guarded=getattr(self,'_b1_editable_path_type',None)
        if path is not None and guarded is not None:
            path=guarded(path)
            path._check()
        return path

    def run_trial(self, proposal, node_spec, budget_index):
        verify_proposal(proposal, node_spec)
        from r1.exam.b1_node_artifacts import preserve_node_artifacts
        preserve_node_artifacts(self._node_root)
        return super().run_trial(proposal, node_spec, budget_index)
