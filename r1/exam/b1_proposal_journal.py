"""Validate the B1 proposal journal against the root's ledger and events (R1-EXAM-B1-MODEL-OUTPUT-INVALID).

AI-assisted (Claude). The journal (``b1_proposals.jsonl``) is written by ``B1CappedLangGraphManager`` before
each proposal is returned, so before any execution. This check runs after the campaign: once in the worker
(the result goes into the root manifest), and again in ``b1_batch`` verification. Any disagreement is a STOP,
because it would be an internal inconsistency, not a model output.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SCHEMA = 'b1_proposal_journal/v1'
OUTCOMES = ('not_applicable', 'd25_inactive_key', 'harness_precondition', 'passed', 'rejected')


def _stop(message):
    raise RuntimeError(f'STOP: B1 proposal journal {message}')


def validate_proposal_journal(path, records, events) -> dict:
    path = Path(path)
    if not path.is_file():
        _stop('missing')
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            _stop('has an unreadable line')
        if not isinstance(row, dict) or row.get('schema') != SCHEMA or row.get('check') not in OUTCOMES:
            _stop('row has an unknown schema or outcome')
        if (row['check'] == 'rejected') != (row.get('rejection') is not None):
            _stop('rejection and outcome disagree')
        rows.append(row)
    calls = [e for e in events if e.get('event_type') == 'llm_call' and 'purpose' not in (e.get('payload') or {})]
    if len(calls) != len(rows):
        _stop(f'has {len(rows)} rows for {len(calls)} proposer calls')
    for event, row in zip(calls, rows):
        payload = event.get('payload') or {}
        if event.get('trial_id') != row.get('trial_id') or bool(payload.get('truncated')) != row.get('truncated'):
            _stop(f'row for {row.get("trial_id")} does not match its proposer call event')
    last = {}
    for row in rows:
        if row['trial_id'] in last and last[row['trial_id']]['check'] == 'rejected':
            _stop(f'a rejected proposal of {row["trial_id"]} was followed by another call (rejections are final)')
        last[row['trial_id']] = row
    for record in records:
        manager = (record.get('extra') or {}).get('manager') or {}
        sha = manager.get('raw_proposal_sha256')
        if sha is None:
            continue
        row = last.get(record.get('trial_id'))
        if row is None or row.get('raw_proposal_sha256') != sha:
            _stop(f'last row for {record.get("trial_id")} is not the recorded proposal')
        rejected = manager.get('b1_model_output_rejected')
        if (row['check'] == 'rejected') != (rejected is not None):
            _stop(f'rejection of {record.get("trial_id")} differs between journal and ledger')
        if rejected is not None and (rejected.get('check') != row['rejection'].get('check') or
                                     rejected.get('structured_edit') != row.get('structured_edit') or
                                     record.get('decision') != 'failed_invalid'):
            _stop(f'rejected proposal {record.get("trial_id")} is not an invalid trial with the journalled edit')
        if rejected is None and manager.get('structured_edit') != row.get('final_structured_edit'):
            _stop(f'structured edit of {record.get("trial_id")} differs from the journal')
    by_check = Counter(r['rejection']['check'] for r in rows if r['check'] == 'rejected')
    return {'schema': SCHEMA, 'rows': len(rows), 'trials': len(last),
            'outcomes': {k: sum(r['check'] == k for r in rows) for k in OUTCOMES},
            'rejected_by_check': dict(sorted(by_check.items()))}
