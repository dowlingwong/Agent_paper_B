"""B1 model-output checks run before execution: a failing proposal is an invalid trial, not a STOP.

PLAN §10 ``R1-EXAM-B1-MODEL-OUTPUT-INVALID`` (13 Nov 2026). AI-assisted (Claude).

The pinned ``LocalWorker`` executes the change named in the proposal's free-text ``objective``
("change SYMBOL from OLD to NEW"), while the control plane, the ledger and the replay use the structured
edit built from the ``param`` / ``old_value`` / ``new_value`` fields. The B1 worker guard
(``b1_proposal_guard.verify_proposal``) refuses to execute when the two disagree, or when the value
cannot be inserted safely. Before this module, it did so with a STOP (run ``4b31_20261112_c``,
trial 20). These conditions are properties of the model's output. ``check_model_output`` evaluates
them on the proposal, before the control plane decides whether to call the worker. A failing proposal is
then turned into a harness precondition failure: not executed, recorded as an invalid trial
(``PROPOSAL_PRECONDITION_FAILED``), charged to the LLM budget like any proposal call. The worker guard
keeps its STOP: a proposal that reaches it and fails is now an internal inconsistency (a code bug).

The checks, in the guard's order, with a stable code each:

* ``directive_missing`` — the objective holds no "change X from A to B" directive the worker can execute;
* ``directive_symbol_not_editable`` — the directive names a symbol outside the node's editable symbols;
* ``directive_symbol_differs`` / ``directive_old_differs`` / ``directive_new_differs`` — the directive the
  worker would execute is not the structured edit;
* ``replacement_escape`` — the new value contains a backslash (the worker inserts it with ``re.sub``);
* ``python_value_too_long`` / ``python_value_not_literal`` / ``python_value_not_finite_number`` — for a ``.py``
  editable file, the new value is not a bounded, finite ``int`` / ``float`` literal.

A ``.py`` value for which ``ast.literal_eval`` raises ``TypeError`` passes here: the worker guard lets that
exception through to the harness, which records an invalid trial (edit failed), exactly as before.

Not checked here, because the model cannot cause it: the edit path, which the harness fixes to the node's
single editable file (the worker guard still STOPs if it differs).
"""
from __future__ import annotations

import ast
import math

from autoresearch.worker.local_worker import _parse_change_directive

POLICY = 'b1_model_output_invalid/v1'
CHECKS = ('directive_missing', 'directive_symbol_not_editable', 'directive_symbol_differs',
          'directive_old_differs', 'directive_new_differs', 'replacement_escape',
          'python_value_too_long', 'python_value_not_literal', 'python_value_not_finite_number')
PY_VALUE_MAX_CHARS = 256


def check_model_output(objective: str, edit: dict, node_spec) -> dict | None:
    """Return ``{'check': code, 'message': ..., 'directive': [...] | None}`` for the first failing check, else None.

    ``edit`` is the harness structured edit (a dict). The order and the conditions are those of the worker
    guard, so a proposal that passes here passes the guard's model-output conditions."""
    parsed = _parse_change_directive(objective or '')
    if parsed is None:
        return {'check': 'directive_missing', 'directive': None,
                'message': 'objective has no "change X from A to B" directive for the worker'}
    symbol, old, new = parsed
    directive = [symbol, old, new]
    canonical = {s.lower(): s for s in node_spec.editable_symbols}.get(symbol.lower())
    if canonical is None:
        return {'check': 'directive_symbol_not_editable', 'directive': directive,
                'message': f'directive symbol {symbol!r} is not an editable symbol of the node'}
    if canonical != str(edit.get('symbol', '')):
        return {'check': 'directive_symbol_differs', 'directive': directive,
                'message': f'directive symbol {canonical!r} differs from the structured edit symbol {edit.get("symbol")!r}'}
    if old != str(edit.get('old', '')):
        return {'check': 'directive_old_differs', 'directive': directive,
                'message': f'directive old value {old!r} differs from the structured edit old value {edit.get("old")!r}'}
    if new != str(edit.get('new', '')):
        return {'check': 'directive_new_differs', 'directive': directive,
                'message': f'directive new value {new!r} differs from the structured edit new value {edit.get("new")!r}'}
    if '\\' in new:
        return {'check': 'replacement_escape', 'directive': directive,
                'message': 'new value contains a backslash'}
    if str(edit.get('path', '')).endswith('.py'):
        if len(new) > PY_VALUE_MAX_CHARS:
            return {'check': 'python_value_too_long', 'directive': directive,
                    'message': f'Python value longer than {PY_VALUE_MAX_CHARS} characters'}
        try:
            value = ast.literal_eval(new)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            return {'check': 'python_value_not_literal', 'directive': directive,
                    'message': 'Python value is not a literal'}
        except TypeError:
            # The worker guard does not catch TypeError (e.g. ``{[]: 1}``): it propagates as an ordinary
            # exception, which the harness records as an invalid trial after a worker run. Left to that path,
            # so such a proposal is recorded exactly as under run 4b31_20261112_c.
            return None
        if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
            return {'check': 'python_value_not_finite_number', 'directive': directive,
                    'message': 'Python value is not a finite int or float'}
    return None
