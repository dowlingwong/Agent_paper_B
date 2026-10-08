"""The registered D7 commands, in ONE place.

`task.json` declares three commands -- fit_baseline, fit_candidate,
compute_dev_accuracy -- and the agent reaches them only through
`run_registered_command`. Without these handlers installed on the ToolBridge,
every such call raises "unregistered command", the agent cannot evaluate
anything on dev.csv, and the measured yield is a property of the crippled
harness rather than of the model.

That is not hypothetical. The Round-5 TITAN Stage-B path constructed its
ToolBridge WITHOUT handlers while the WP3 qualification runner constructed its
bridge WITH them -- two call sites, one drifted. This module exists so there is
exactly one implementation left to drift. The WP3 runner and Stage B both
import from here.

Scope guarantee: every handler reads only the workspace's own `dev.csv`. The
hidden evaluation table lives under a sibling `_hidden` root that no workspace
path reaches, and nothing here takes a path argument.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _read_table(path: Path) -> tuple[list[tuple[float, float]], list[int]]:
    features, labels = [], []
    with path.open(encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            if not row:
                continue
            features.append((float(row[0]), float(row[1])))
            labels.append(int(row[2]))
    return features, labels


def d7_command_handlers(workspace: Path) -> dict[str, Any]:
    """Handlers bound to ONE workspace. Frozen semantics; not tunable."""

    def _accuracy(lam: float) -> float:
        features, labels = _read_table(workspace / "dev.csv")
        correct = sum(1 for (x1, x2), y in zip(features, labels)
                      if (1 if (lam * x1 + (1 - lam) * x2) > 0.5 else 0) == y)
        return correct / len(labels) if labels else 0.0

    def fit_baseline(**_: Any) -> dict[str, Any]:
        return {"lam": 0.5, "dev_accuracy": _accuracy(0.5),
                "note": "frozen baseline from baseline.py"}

    def compute_dev_accuracy(lam: float = 0.5, **_: Any) -> dict[str, Any]:
        return {"lam": float(lam), "dev_accuracy": _accuracy(float(lam))}

    def fit_candidate(**_: Any) -> dict[str, Any]:
        grid = [i / 20.0 for i in range(21)]
        scored = sorted(((_accuracy(l), l) for l in grid), reverse=True)
        best_acc, best_lam = scored[0]
        return {"best_lam": best_lam, "dev_accuracy": best_acc,
                "searched": len(grid)}

    return {"fit_baseline": fit_baseline,
            "compute_dev_accuracy": compute_dev_accuracy,
            "fit_candidate": fit_candidate}
