"""Fail-closed boundaries for identifiable C3 sweep EVIDENCE rows.

These checks do not authenticate provenance and cannot identify a row whose
origin markers have been removed. Callers must validate source artifacts and
preserve provenance before relying on them.
"""
from collections.abc import Mapping


def is_identifiable_sweep_evidence(value, depth=0):
    if depth > 6:
        return False
    if isinstance(value, Mapping):
        if (value.get('_evidence_seed_split') is True or value.get('decision_id') == 'R1-SWEEP1-CLASSIFY'
                or value.get('label') == 'EVIDENCE'):
            return True
        return any(is_identifiable_sweep_evidence(v, depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(is_identifiable_sweep_evidence(v, depth + 1) for v in value)
    if hasattr(value, 'meta') and isinstance(value.meta, Mapping):
        return is_identifiable_sweep_evidence(value.meta, depth + 1)
    return False


def refuse_unverified_sweep_rows(rows, context):
    if any(is_identifiable_sweep_evidence(row) for row in rows):
        raise ValueError(f'{context}: identifiable C3 sweep EVIDENCE rows need a verified label-only boundary')
