"""Pure inspection of supplied synthetic unit history; no execution or authority.

The caller must establish complete, ordered, immutable history and unit
identity separately. A return value is not permission to submit or rerun.
"""


class UnitHistoryError(ValueError):
    pass


def assess_history(unit_id, attempts):
    """Inspect a complete supplied sequence of terminal whole-unit attempts.

    An interrupted attempt is a cut. The second cut always returns STOP.
    Failed/incomplete/unknown histories are refused; they cannot be silently
    interpreted as clean infrastructure failures or an absent prior attempt.
    """
    if not isinstance(unit_id, str) or not unit_id:
        raise UnitHistoryError('unit identity required')
    if not isinstance(attempts, (list, tuple)):
        raise UnitHistoryError('complete attempt history required')
    cuts = 0
    completed = False
    for number, row in enumerate(attempts, start=1):
        if not isinstance(row, dict) or row.get('unit_id') != unit_id:
            raise UnitHistoryError('unit identity mismatch')
        if type(row.get('attempt')) is not int or row['attempt'] != number:
            raise UnitHistoryError('attempt sequence incomplete or duplicate')
        if completed or cuts >= 2:
            raise UnitHistoryError('attempt after terminal state')
        outcome = row.get('outcome')
        if outcome == 'interrupted':
            cuts += 1
        elif outcome == 'complete':
            completed = True
        else:
            raise UnitHistoryError('unknown, failed, or nonterminal attempt')
    state = 'STOP_CUT_TWICE' if cuts >= 2 else ('COMPLETE' if completed else 'FRESH_ATTEMPT_POSSIBLE')
    return {'unit_id': unit_id, 'state': state, 'cuts': cuts, 'attempts': len(attempts)}
