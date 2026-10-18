"""F8: the live candidate-consistency task executed through the real fork path.

The fit tool uses a fit portion of the visible development data; the verifier
checks a disjoint visible diagnostic portion and replaces the candidate only on
a strict improvement.  Dev batch 2 arrives online at checkpoint 2.  The hidden
evaluation lives in the task object and is never written into the workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from causal_branch.adapters.toy import MockModelProvider

from cc_live_candidate import Stump, accuracy, fit_stump, verifier


class LiveCandidateTask:
    def __init__(self, family: dict):
        self.family = family
        self.provider = MockModelProvider()
        self._hidden = (np.asarray(family["X_hidden"]), np.asarray(family["y_hidden"]))

    # -- workspace helpers ------------------------------------------------
    def _write_csv(self, path: Path, x, y) -> None:
        arr = np.column_stack([np.asarray(x), np.asarray(y)])
        header = ",".join(self.family["features"] + ["label"])
        np.savetxt(path, arr, delimiter=",", header=header, comments="")

    def _visible(self, workspace: Path):
        xs, ys = [], []
        for name in sorted(workspace.glob("dev*.csv")):
            arr = np.loadtxt(name, delimiter=",", skiprows=1)
            xs.append(arr[:, :-1])
            ys.append(arr[:, -1].astype(int))
        return np.vstack(xs), np.concatenate(ys)

    @staticmethod
    def _split(x, y, fit_fraction: float = 0.8):
        cut = int(len(y) * fit_fraction)
        return (x[:cut], y[:cut]), (x[cut:], y[cut:])

    # -- the B5 TreeTask protocol ----------------------------------------
    def prepare(self, workspace: Path, *, template_id: str, root_id: str, seed: int) -> None:
        workspace.mkdir(parents=True, exist_ok=True)
        self._write_csv(workspace / "dev1.csv", self.family["X_dev1"], self.family["y_dev1"])
        (workspace / "features.json").write_text(
            json.dumps(self.family["features"]) + "\n", encoding="utf-8")
        (fit_x, fit_y), _ = self._split(self.family["X_dev1"], self.family["y_dev1"])
        self.provider.complete("fit")  # exercised mock provider
        candidate = fit_stump(fit_x, fit_y)
        (workspace / "candidate.json").write_text(candidate.to_json() + "\n", encoding="utf-8")

    def continue_to_checkpoint2(self, workspace: Path) -> bool:
        self._write_csv(workspace / "dev2.csv", self.family["X_dev2"], self.family["y_dev2"])
        return True

    def verify_and_respond(self, workspace: Path) -> None:
        x, y = self._visible(workspace)
        (fit_x, fit_y), (check_x, check_y) = self._split(x, y)
        self.provider.complete("fit")
        candidate = fit_stump(fit_x, fit_y)
        repaired = verifier(candidate, check_x, check_y)
        (workspace / "candidate.json").write_text(repaired.to_json() + "\n", encoding="utf-8")

    def grade(self, workspace: Path) -> float:
        data = json.loads((workspace / "candidate.json").read_text())
        candidate = Stump(**data)
        hidden_x, hidden_y = self._hidden
        return accuracy(candidate, hidden_x, hidden_y)

    # -- explicit submission path (test hook) -----------------------------
    def submit(self, candidate: Stump) -> Stump:
        """The submission path returns a valid executable candidate or raises."""

        if not isinstance(candidate, Stump):
            raise ValueError("submission must be an executable candidate (Stump)")
        return candidate
