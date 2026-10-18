"""B6: the candidate-consistency task (B-only, CPU, scripted).

A *fit tool* returns the exact executable candidate it evaluated.  A verifier
checks consistency against **visible** development diagnostics and the frozen
response rule replaces the candidate only on a strict visible improvement; ties
leave it unchanged.  The hidden evaluation is separate and is never written into
the workspace, so neither the agent nor the verifier can read it.  Checkpoint 2
arises online after a second visible development batch arrives (legitimate new
information, not future leakage).

The task executes files through the B5 driver; no outcome is a supplied
constant.  Nothing here is scientific evidence.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

CANDIDATES = (0, 1, 2, 3)


def fit_tool(observations) -> int:
    """Return the exact executable candidate the fit tool evaluated.

    The candidate is the modal observation (ties resolve to the smallest); this
    is the candidate the tool scored, not a later re-derivation.
    """

    if not observations:
        raise ValueError("the fit tool needs at least one visible observation")
    counts = Counter(int(v) for v in observations)
    best = max(counts.values())
    return min(v for v, c in counts.items() if c == best)


def _score(candidate: int, observations) -> float:
    if not observations:
        return 0.0
    return sum(1 for v in observations if int(v) == int(candidate)) / len(observations)


def verifier(candidate: int, check_observations) -> int:
    """Frozen response rule.

    The verifier checks the candidate against a separate visible development
    diagnostic (``check_observations``) and replaces it only when the diagnostic
    consistency candidate is *strictly* better on that diagnostic.  Ties leave
    the candidate unchanged.
    """

    diagnostic_candidate = fit_tool(check_observations)
    if _score(diagnostic_candidate, check_observations) > _score(candidate, check_observations):
        return diagnostic_candidate
    return candidate


class CandidateConsistencyTask:
    """A task adapter for the B5 tree driver."""

    def __init__(self, spec: dict):
        self.spec = spec
        self.true_param = int(spec["true_param"])
        self._candidate_path = "candidate.json"

    # -- visible development surface ------------------------------------
    def _visible(self, workspace: Path):
        fit_obs, check_obs = [], []
        for name in sorted(workspace.glob("fit_dev*.json")):
            fit_obs.extend(json.loads(name.read_text())["observations"])
        for name in sorted(workspace.glob("check_dev*.json")):
            check_obs.extend(json.loads(name.read_text())["observations"])
        return fit_obs, check_obs

    def prepare(self, workspace: Path, *, template_id: str, root_id: str, seed: int) -> None:
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "fit_dev1.json").write_text(
            json.dumps({"observations": self.spec["fit_dev1"]}) + "\n", encoding="utf-8")
        (workspace / "check_dev1.json").write_text(
            json.dumps({"observations": self.spec["check_dev1"]}) + "\n", encoding="utf-8")
        (workspace / "task.json").write_text(
            json.dumps({"template_id": template_id, "root_id": root_id, "seed": seed}) + "\n",
            encoding="utf-8")
        candidate = fit_tool(self.spec["fit_dev1"])
        self._write_candidate(workspace, candidate)

    def continue_to_checkpoint2(self, workspace: Path) -> bool:
        # Legitimate new visible information: a second development batch.
        (workspace / "fit_dev2.json").write_text(
            json.dumps({"observations": self.spec["fit_dev2"]}) + "\n", encoding="utf-8")
        (workspace / "check_dev2.json").write_text(
            json.dumps({"observations": self.spec["check_dev2"]}) + "\n", encoding="utf-8")
        return True

    def verify_and_respond(self, workspace: Path) -> None:
        fit_obs, check_obs = self._visible(workspace)
        evaluated = fit_tool(fit_obs)
        repaired = verifier(evaluated, check_obs)
        self._write_candidate(workspace, repaired)

    def grade(self, workspace: Path) -> float:
        # Hidden evaluation: the true parameter is never written to the workspace.
        candidate = json.loads((workspace / self._candidate_path).read_text())["threshold"]
        return 1.0 if int(candidate) == self.true_param else 0.0

    def _write_candidate(self, workspace: Path, candidate: int) -> None:
        (workspace / self._candidate_path).write_text(
            json.dumps({"threshold": int(candidate)}) + "\n", encoding="utf-8")


def ordinary_refit(spec: dict, checkpoint: int) -> int:
    """Ordinary refitting on the visible fit data (the redundancy check)."""

    obs = list(spec["fit_dev1"])
    if checkpoint == 2:
        obs += list(spec["fit_dev2"])
    return fit_tool(obs)


def verifier_output(spec: dict, checkpoint: int) -> int:
    fit_obs = list(spec["fit_dev1"]) + (list(spec["fit_dev2"]) if checkpoint == 2 else [])
    check_obs = list(spec["check_dev1"]) + (list(spec["check_dev2"]) if checkpoint == 2 else [])
    return verifier(fit_tool(fit_obs), check_obs)
