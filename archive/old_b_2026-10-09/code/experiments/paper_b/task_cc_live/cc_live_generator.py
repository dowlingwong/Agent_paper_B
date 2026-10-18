"""F8: template/family generator for the live candidate-consistency task.

Uses scikit-learn's **bundled** tabular datasets (no network): the breast-cancer
and wine tables.  Each family is a deterministic subsample with a disjoint
training / dev-1 / dev-2 / hidden split.  The hidden split is returned to the
task object only and is never written into the agent workspace.

This is a realistic CPU task for Devstral; it is not a scientific result.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
from sklearn.datasets import load_breast_cancer, load_wine

DATASETS = {"breast_cancer": load_breast_cancer, "wine": load_wine}


def family_law_hash() -> str:
    payload = json.dumps({"datasets": sorted(DATASETS), "version": "task_cc_live_v1"},
                         sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def generate_family(family_id: int, seed: int, *, n_train: int = 60,
                    n_dev1: int = 30, n_dev2: int = 30, n_hidden: int = 50,
                    label_noise: float = 0.2) -> dict:
    """One template family: 4 disjoint tabular splits and feature names."""

    name = "breast_cancer" if family_id % 2 == 0 else "wine"
    bunch = DATASETS[name]()
    x = np.asarray(bunch.data, dtype=float)
    features = [str(f) for f in bunch.feature_names]
    rng = np.random.default_rng(seed)
    # Repair pass F9: a balanced, harder derived target and label noise, so the
    # task is not trivially solvable and the realism thresholds are meaningful.
    z = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-9)
    separator = rng.normal(size=x.shape[1])
    score = z @ separator
    label = (score > np.median(score)).astype(int)
    label = label ^ (rng.uniform(size=len(label)) < label_noise).astype(int)
    y = label
    order = rng.permutation(len(y))
    need = n_train + n_dev1 + n_dev2 + n_hidden
    if need > len(order):
        raise ValueError(f"{name} has {len(order)} rows but the split needs {need}")
    order = order[:need]
    cuts = np.cumsum([0, n_train, n_dev1, n_dev2, n_hidden])
    parts = [order[cuts[i]:cuts[i + 1]] for i in range(4)]
    return {
        "family_id": family_id,
        "dataset": name,
        "features": features,
        "X_train": x[parts[0]], "y_train": y[parts[0]],
        "X_dev1": x[parts[1]], "y_dev1": y[parts[1]],
        "X_dev2": x[parts[2]], "y_dev2": y[parts[2]],
        "X_hidden": x[parts[3]], "y_hidden": y[parts[3]],
    }
