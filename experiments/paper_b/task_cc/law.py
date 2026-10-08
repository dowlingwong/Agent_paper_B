"""B6: the frozen development-screen law for the candidate-consistency task.

Four mechanism classes, two fresh template families each, eight families total.
This is an artificial *diagnostic* law, not natural deployment prevalence.  The
law is frozen and hashed before any live screen; the pilot law is a separate
artifact (:mod:`pilot_law`), frozen before pilot outcomes.

Each family is a parameterised candidate-consistency instance: the fit tool and
verifier are the fixed rules of :mod:`task`; only the visible development data
and the hidden true parameter differ.  The expected regime ordering is declared
here and checked by the executable witnesses.
"""

from __future__ import annotations

import hashlib
import json

#: Expected regime ordering under the declared accuracy endpoint and costs.
EXPECTED_ORDERING = {
    "now_best": ("now", "later", "never"),
    "later_best": ("later", "now", "never"),
    "never_best": ("never", "now", "later"),
    "uninformative_or_harmful": ("never", "now", "later"),
}

SCREEN_LAW = {
    "now_best": [
        {"true_param": 1, "fit_dev1": [0, 0, 1], "check_dev1": [1, 1, 0],
         "fit_dev2": [0, 0], "check_dev2": [0, 0]},
        {"true_param": 2, "fit_dev1": [1, 1, 2], "check_dev1": [2, 2, 1],
         "fit_dev2": [1, 1], "check_dev2": [1, 1]},
    ],
    "later_best": [
        {"true_param": 1, "fit_dev1": [0, 0], "check_dev1": [0, 0],
         "fit_dev2": [1, 1, 1], "check_dev2": [1, 1, 1]},
        {"true_param": 2, "fit_dev1": [1, 1], "check_dev1": [1, 1],
         "fit_dev2": [2, 2, 2], "check_dev2": [2, 2, 2]},
    ],
    "never_best": [
        {"true_param": 1, "fit_dev1": [1, 1, 0], "check_dev1": [0, 0, 1],
         "fit_dev2": [0, 0], "check_dev2": [0, 0]},
        {"true_param": 2, "fit_dev1": [2, 2, 1], "check_dev1": [1, 1, 2],
         "fit_dev2": [1, 1], "check_dev2": [1, 1]},
    ],
    "uninformative_or_harmful": [
        {"true_param": 1, "fit_dev1": [1, 1, 1], "check_dev1": [1, 1, 0],
         "fit_dev2": [1, 1, 1], "check_dev2": [1, 1, 0]},
        {"true_param": 2, "fit_dev1": [2, 2, 2], "check_dev1": [2, 2, 1],
         "fit_dev2": [2, 2, 2], "check_dev2": [2, 2, 1]},
    ],
}


def law_hash(law: dict | None = None) -> str:
    payload = json.dumps(law if law is not None else SCREEN_LAW,
                         sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def families():
    """Yield ``(mechanism_class, family_index, spec)`` for every screen family."""

    for mechanism, specs in SCREEN_LAW.items():
        for index, spec in enumerate(specs):
            yield mechanism, index, spec
