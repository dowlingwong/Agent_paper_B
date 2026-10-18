"""Scripted agent backend and task tools for the candidate-consistency task.

References: ``docs/paper_split/B_INFRA_CONSTRUCTION_PLAN_20261006.md`` IP2
and ``docs/paper_split/B_EXECUTION_RUNBOOK_20261008.md`` Stage 4.1.

``CandidateTaskTools`` is the task side of the three agent tools (fit, verify,
submit) plus the checkpoint-2 data arrival and the hidden-test grade; it reuses
the frozen fit and verifier rules of ``cc_live_candidate``.  ``ScriptedCandidateAgent``
is a model-free agent that drives those tools through the executor and writes
real Pi-shaped session JSONL, so every CPU test and dry run exercises the same
fork, session and history path the Devstral backend will.

The scripted agent can never carry a qualifying root (``is_scripted``).
Behaviours exist only to exercise the executor's guards:

``"typical"``  fit, (verify once if offered), submit;
``"greedy"``   asks for a second verification, which the guard refuses;
``"careless"`` never verifies even when offered (the executor rejects the
               branch: a verify branch must execute exactly one verification).

Nothing here is evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from causal_branch.control.executor import TurnResult, append_entries, read_session
from cc_live_candidate import Stump, accuracy, fit_stump, verifier


# --------------------------------------------------------------------------
# Task tools
# --------------------------------------------------------------------------


class CandidateTaskTools:
    """Task-side tool implementations for one template family."""

    def __init__(self, family: dict) -> None:
        self.family = family
        self._hidden = (np.asarray(family["X_hidden"]), np.asarray(family["y_hidden"]))

    # -- workspace helpers ------------------------------------------------
    def _write_csv(self, path: Path, x, y) -> None:
        arr = np.column_stack([np.asarray(x), np.asarray(y)])
        header = ",".join(self.family["features"] + ["label"])
        np.savetxt(path, arr, delimiter=",", header=header, comments="")

    def _visible(self, workspace: Path):
        xs, ys = [], []
        for name in sorted(Path(workspace).glob("dev*.csv")):
            arr = np.loadtxt(name, delimiter=",", skiprows=1)
            xs.append(arr[:, :-1])
            ys.append(arr[:, -1].astype(int))
        return np.vstack(xs), np.concatenate(ys)

    @staticmethod
    def _split(x, y, fit_fraction: float = 0.8):
        cut = int(len(y) * fit_fraction)
        return (x[:cut], y[:cut]), (x[cut:], y[cut:])

    # -- executor hooks ---------------------------------------------------
    def prepare(self, workspace: Path) -> None:
        workspace = Path(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        self._write_csv(workspace / "dev1.csv", self.family["X_dev1"], self.family["y_dev1"])
        (workspace / "features.json").write_text(
            json.dumps(self.family["features"]) + "\n", encoding="utf-8")
        (workspace / "task.md").write_text(
            "Fit a classifier on the visible development data and submit the "
            "candidate with the best development accuracy.\n", encoding="utf-8")

    def fit_candidate(self, workspace: Path) -> dict:
        x, y = self._visible(workspace)
        (fit_x, fit_y), _ = self._split(x, y)
        candidate = fit_stump(fit_x, fit_y)
        return {**json.loads(candidate.to_json()),
                "visible_accuracy": float(accuracy(candidate, fit_x, fit_y))}

    def verify_candidate(self, workspace: Path, candidate: dict) -> dict:
        x, y = self._visible(workspace)
        _, (check_x, check_y) = self._split(x, y)
        current = Stump(int(candidate["feature"]), float(candidate["threshold"]),
                        int(candidate["direction"]))
        repaired = verifier(current, check_x, check_y)
        return {**json.loads(repaired.to_json()), "replaced": repaired != current}

    def submit_candidate(self, workspace: Path, candidate: dict) -> dict:
        stump = Stump(int(candidate["feature"]), float(candidate["threshold"]),
                      int(candidate["direction"]))
        (Path(workspace) / "candidate.json").write_text(stump.to_json() + "\n", encoding="utf-8")
        return {"accepted": True}

    def arrive_checkpoint2(self, workspace: Path) -> bool:
        self._write_csv(Path(workspace) / "dev2.csv", self.family["X_dev2"], self.family["y_dev2"])
        return True

    def grade(self, workspace: Path) -> float:
        path = Path(workspace) / "candidate.json"
        if not path.is_file():
            return 0.0  # no valid candidate: U = 0 with the reason retained by the caller
        data = json.loads(path.read_text())
        candidate = Stump(**data)
        hidden_x, hidden_y = self._hidden
        return float(accuracy(candidate, hidden_x, hidden_y))


# --------------------------------------------------------------------------
# Scripted agent
# --------------------------------------------------------------------------


@dataclass
class ScriptedCandidateAgent:
    """Model-free agent; writes Pi-shaped session entries through the executor."""

    behaviour: str = "typical"
    is_scripted: bool = True

    def _entries(self, session: Path):
        document = read_session(session)
        leaf = document.entries[-1]["id"] if document.entries else None
        counter = len(document.entries)
        made: list[dict] = []

        def emit(kind: str, **fields):
            nonlocal leaf, counter
            entry_id = "e" + hashlib.sha256(f"{session.stem}|{counter}".encode()).hexdigest()[:10]
            entry = {"type": kind, "id": entry_id, "parentId": leaf, **fields}
            made.append(entry)
            leaf = entry_id
            counter += 1
            return entry

        return made, emit

    def run_turn(self, *, workspace: Path, session: Path, tools, prompt: str, stop: str,
                 seed: int) -> TurnResult:
        made, emit = self._entries(session)
        emit("message", message={"role": "user", "content": prompt})
        offered = "verify_candidate" in prompt
        emit("message", message={"role": "assistant",
                                 "content": "Fitting a candidate on the visible development data."})
        emit("tool_call", name="fit_candidate", arguments={})
        fitted = tools.call("fit_candidate", {})
        emit("tool_result", name="fit_candidate", ok=fitted["ok"],
             content=json.dumps(fitted.get("result"), sort_keys=True))
        candidate = {k: fitted["result"][k] for k in ("feature", "threshold", "direction")}
        if offered and self.behaviour != "careless":
            attempts = 2 if self.behaviour == "greedy" else 1
            for _ in range(attempts):
                emit("tool_call", name="verify_candidate", arguments={"candidate": candidate})
                checked = tools.call("verify_candidate", {"candidate": candidate})
                emit("tool_result", name="verify_candidate", ok=checked["ok"],
                     content=json.dumps(checked.get("result") or {"refused": checked.get("reason")},
                                        sort_keys=True))
                if checked["ok"]:
                    candidate = {k: checked["result"][k] for k in ("feature", "threshold", "direction")}
        emit("tool_call", name="submit_candidate", arguments={"candidate": candidate})
        submitted = tools.call("submit_candidate", {"candidate": candidate})
        emit("tool_result", name="submit_candidate", ok=submitted["ok"],
             content=json.dumps(submitted.get("result"), sort_keys=True))
        if stop == "checkpoint1":
            emit("checkpoint", checkpoint_id="c1")
        elif stop == "checkpoint2":
            emit("checkpoint", checkpoint_id="c2")
        else:
            emit("message", message={"role": "assistant", "content": "Submitted the final candidate."})
        append_entries(session, made)
        usage = {"prompt_tokens": 40 * len(made), "completion_tokens": 12 * len(made)}
        return TurnResult(leaf_entry_id=made[-1]["id"], terminal="settled", usage=usage)
