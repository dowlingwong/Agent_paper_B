"""Replay B1 proposer calls with their fixed prompt, read-only, and report what the worker guard would do.

ENGINEERING_ONLY; AI-assisted (Claude). For R1-EXAM-B1-MODEL-OUTPUT-INVALID, item (1): why run
``4b31_20261112_c`` recorded trials 018/019 as invalid and stopped at trial 020.

Input: a **copy** of one B1 root directory (``root_trials.jsonl``, ``root_events.jsonl``, ``node/``). The
original is never opened for writing. Also needed: a llama-server serving the candidate with the run's exact
argv (taken from the run's retained server record), reachable at ``--base-url``. For each requested trial
``b`` the script rebuilds what the harness gave the proposer at that trial, with the harness's own
functions:
* the ledger prefix (rows before ``b``) read back through the harness's ``TrialAppendStore``;
* the memory context (``append_only_summary``, the campaign defaults);
* the incumbent files (start files plus the kept edits);
* the manager status, from those files;
* the incumbent metric.

It then calls the B1 proposer once (``B1CappedLangGraphManager``, same seed rule, no revision). No worker
runs and nothing is executed.

Reproduction checks against the run:
* ``context_sha256`` and ``raw_proposal_sha256`` against the trial's ledger record (trials that have one);
* ``seed``, ``prompt_tokens``, ``completion_tokens`` and ``response_chars`` against the trial's
  ``llm_call`` event (all trials, including one that stopped before its record was written).

Reported per trial:
* the six reply fields and the objective;
* the directive the worker would parse, and the structured edit;
* the verdict of the run's worker guard (``verify_proposal``: STOP text or pass);
* the verdict of the new pre-check (``check_model_output``).

    python -m r1.scripts.b1_proposal_replay --root-copy DIR --candidate olmo31_32b \\
        --node openml_credit_approval --seed 9002 --trials 18,19,20 --base-url http://127.0.0.1:PORT/v1 --out NEW_DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def _rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def replay(root_copy: Path, candidate: str, node: str, seed: int, trials: list[int], out: Path) -> dict:
    from r1.harness import import_harness, harness_commit
    harness = import_harness()
    from autoresearch.control_plane.campaign import _current_best, _manager_status
    from autoresearch.memory.append_store import TrialAppendStore as Store
    from autoresearch.memory.summarizer import MemoryMode, build_memory_context
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import _parse_change_directive
    from r1.c3.features import apply_edit
    from r1.exam.b1_llm_truncation import B1CappedLangGraphManager
    from r1.exam.b1_proposal_guard import B1ProposalIntegrityStop, verify_proposal
    from r1.exam.b1_proposal_precheck import check_model_output

    spec = load_registered_node(node, repo_root=harness)
    campaign_id = f'{node}__s{seed}'
    records = _rows(root_copy / 'root_trials.jsonl')
    events = _rows(root_copy / 'root_events.jsonl')
    start = {p: (harness / 'nodes' / node / p).read_text() for p in spec.editable_paths}
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for b in trials:
        prefix = [r for r in records if int(r['budget_index']) < b]
        if [int(r['budget_index']) for r in prefix] != list(range(1, b)):
            raise ValueError(f'ledger prefix of trial {b} is not trials 1..{b - 1}')
        work = out / f'trial-{b:03d}'
        node_root = work / 'node'
        shutil.copytree(harness / 'nodes' / node, node_root, ignore=shutil.ignore_patterns('__pycache__', '.autoresearch_artifacts'))
        files = dict(start)
        for r in prefix:
            if r.get('decision') == 'kept':
                edit = ((r.get('extra') or {}).get('manager') or {}).get('structured_edit')
                if edit:
                    files = apply_edit(files, edit)
        for p, text in files.items():
            (node_root / p).write_text(text)
        prefix_path = work / 'prefix_trials.jsonl'
        prefix_path.write_text(''.join(json.dumps(r) + '\n' for r in prefix))
        prefix_records = Store(prefix_path).read_all()
        memory = build_memory_context(prefix_records, MemoryMode('append_only_summary'), spec, b)
        worker = type('ReplayRoot', (), {'node_root': node_root})()
        best = _current_best(prefix_records, spec.metric_name, spec.metric_direction)
        status = _manager_status(campaign_id=campaign_id, budget_index=b, current_best=best, node_spec=spec, worker=worker)
        manager = B1CappedLangGraphManager(model='llamacpp/' + candidate, proposal_schema='manager_proposal/v1',
                                           transport_retry=None, journal_path=work / 'b1_proposals.jsonl')
        manager.b1_worker = worker
        proposal = manager.propose_next_trial(status, memory, spec, revision_feedback=None, revision_attempt=0)
        journal = _rows(work / 'b1_proposals.jsonl')[-1]
        edit = journal['structured_edit']
        call = proposal.extra['llm_call']
        record = next((r for r in records if int(r['budget_index']) == b), None)
        tid = f'{campaign_id}-trial-{b:03d}'
        run_calls = [e['payload'] for e in events if e.get('event_type') == 'llm_call' and e.get('trial_id') == tid
                     and 'purpose' not in (e.get('payload') or {})]
        guard = 'pass'
        try:
            # the run's guard semantics: the proposal as the harness built it, before the new pre-check
            probe = type(proposal)(manager_mode=proposal.manager_mode, proposal_summary=proposal.proposal_summary,
                                   proposal_rationale=proposal.proposal_rationale, target_files=proposal.target_files,
                                   objective=proposal.objective,
                                   extra={**proposal.extra, **({'structured_edit': edit} if edit else {})})
            verify_proposal(probe, spec)
        except B1ProposalIntegrityStop as exc:
            guard = str(exc.code)
        try:
            fields = json.loads(journal['raw_reply'] or '')
        except (TypeError, json.JSONDecodeError):
            fields = None
        manager_rec = ((record or {}).get('extra') or {}).get('manager') or {}
        results.append({
            'trial': b, 'trial_id': tid,
            'run_record_present': record is not None, 'run_decision': (record or {}).get('decision'),
            'run_llm_calls_for_trial': len(run_calls),
            'reproduced': {
                'context_sha256': (manager_rec.get('context_sha256') == proposal.extra.get('context_sha256')) if record else None,
                'raw_proposal_sha256': (manager_rec.get('raw_proposal_sha256') == proposal.extra.get('raw_proposal_sha256')) if record else None,
                'llm_call_event': ({k: (run_calls[0].get(k), call.get(k)) for k in
                                    ('seed', 'prompt_tokens', 'completion_tokens', 'response_chars')} if run_calls else None),
                'incumbent_metric_matches_record': (record.get('current_best_before') == best) if record else None,
            },
            'reply_fields': fields, 'objective': proposal.objective,
            'directive': list(_parse_change_directive(proposal.objective or '') or []) or None,
            'structured_edit': edit,
            'run_guard_verdict': guard,
            'new_precheck': (check_model_output(proposal.objective, edit, spec) if isinstance(edit, dict) else None),
            'new_precheck_outcome': journal['check'],
        })
    report = {'schema': 'b1_proposal_replay/v1', 'harness': harness_commit(), 'candidate': candidate, 'node': node,
              'seed': seed, 'campaign_id': campaign_id, 'base_url': os.environ.get('LLAMACPP_BASE_URL'),
              'trials': results}
    (out / 'replay.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root-copy', required=True, type=Path)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--node', required=True)
    ap.add_argument('--seed', required=True, type=int)
    ap.add_argument('--trials', required=True)
    ap.add_argument('--base-url', required=True)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args(argv)
    os.environ['LLAMACPP_BASE_URL'] = a.base_url
    for key in ('LLAMACPP_CACHE_PROMPT', 'LLAMACPP_API_KEY'):
        os.environ.pop(key, None)
    try:
        report = replay(a.root_copy, a.candidate, a.node, a.seed, [int(x) for x in a.trials.split(',')], a.out)
    except (ValueError, OSError) as exc:
        print(f'b1_proposal_replay: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
