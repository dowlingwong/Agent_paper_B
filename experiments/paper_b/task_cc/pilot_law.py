"""B6: the pilot law — a *separate* artifact, frozen before pilot outcomes.

This file is deliberately not executed by the screen witnesses.  It gives the
pilot generator and law distinct template families and true parameters so the
screen and pilot are disjoint, and it must be frozen (hashed) before any pilot
outcome is collected.  No pilot is run in this work item.
"""

from __future__ import annotations

import hashlib
import json

PILOT_LAW = {
    "now_best": [
        {"true_param": 3, "fit_dev1": [2, 2, 3], "check_dev1": [3, 3, 2],
         "fit_dev2": [2, 2], "check_dev2": [2, 2]},
    ],
    "later_best": [
        {"true_param": 3, "fit_dev1": [2, 2], "check_dev1": [2, 2],
         "fit_dev2": [3, 3, 3], "check_dev2": [3, 3, 3]},
    ],
    "never_best": [
        {"true_param": 3, "fit_dev1": [3, 3, 2], "check_dev1": [2, 2, 3],
         "fit_dev2": [2, 2], "check_dev2": [2, 2]},
    ],
    "uninformative_or_harmful": [
        {"true_param": 3, "fit_dev1": [3, 3, 3], "check_dev1": [3, 3, 2],
         "fit_dev2": [3, 3, 3], "check_dev2": [3, 3, 2]},
    ],
}


def pilot_law_hash() -> str:
    payload = json.dumps(PILOT_LAW, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
