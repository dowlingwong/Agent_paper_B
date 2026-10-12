"""A seeded random bounded-edit proposer: the E1b stand-in for the LLM manager.

It is used only because the Linux VM that runs the pilot cannot reach the
Mac's Ollama.  Proposals are local multiplicative edits of one editable
numeric symbol (factor log-uniform in [1/3, 3], clipped to the node's allowed
range).  On OpenML nodes there is also a 30 % chance of a categorical switch
(model_type, class_weight or scaler).

The proposal law is not an LLM's, so headroom measured with it is headroom
*for this proposer*.  The Mac command in the E1b report reruns the pilot with
the pinned qwen2.5-coder:7b.

``deterministic = True``: no LLM call is made or counted, and revise stays
masked (the proposer takes no revision feedback).  The RNG is keyed by
(instance seed, repetition, budget index).  So sibling branches with the same
repetition draw the same proposal at the same budget index whenever their
incumbents agree (common random numbers across siblings).
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.manager.base import ManagerProposal  # noqa: E402

OPENML_ACTIVE = {
    "logistic_regression": ("C", "max_iter"),
    "random_forest": ("n_estimators", "max_depth"),
    "gradient_boosting": ("n_estimators", "max_depth", "learning_rate"),
}
CATEGORICAL = ("model_type", "class_weight", "scaler")


def _is_int(text: str) -> bool:
    return re.fullmatch(r"[-+]?\d+", text.strip()) is not None


class ScriptedRandomManager:
    mode = "scripted_random"
    deterministic = True

    def __init__(self, node: str, *, seed: int, repetition: int, factor_range: float = 3.0,
                 categorical_prob: float = 0.3) -> None:
        self.node = node
        self.seed = int(seed)
        self.repetition = int(repetition)
        self.factor_range = float(factor_range)
        self.categorical_prob = float(categorical_prob)
        raw = json.loads((HARNESS / "configs" / "nodes" / f"{node}.yaml").read_text())
        self.ranges = raw.get("allowed_ranges", {})
        self.values = raw.get("allowed_values", {})
        self.symbols = tuple(raw.get("editable_symbols", ()))

    def _rng(self, budget_index: int) -> np.random.Generator:
        return np.random.default_rng([self.seed, self.repetition, int(budget_index)])

    def propose_next_trial(self, status, memory_context, node_spec) -> ManagerProposal:
        rng = self._rng(status.budget_index)
        consts = {k: v for k, v in (status.current_constants or {}).items() if k in self.symbols}
        edit = None
        if self.node.startswith("openml_") and rng.random() < self.categorical_prob:
            key = CATEGORICAL[int(rng.integers(len(CATEGORICAL)))]
            options = ["null" if o is None else str(o) for o in self.values.get(key, [])]
            options = [o for o in options if o != consts.get(key)]
            if key in consts and options:
                edit = (key, consts[key], options[int(rng.integers(len(options)))])
        if edit is None:
            if self.node.startswith("openml_"):
                numeric = [s for s in OPENML_ACTIVE.get(consts.get("model_type", ""), ()) if s in consts]
            else:
                numeric = [s for s in self.symbols if s in consts]
            for _ in range(20):
                sym = numeric[int(rng.integers(len(numeric)))]
                old = consts[sym]
                factor = math.exp(rng.uniform(-math.log(self.factor_range), math.log(self.factor_range)))
                new_val = float(old) * factor
                lo_hi = self.ranges.get(sym)
                if lo_hi:
                    new_val = min(max(new_val, float(lo_hi[0])), float(lo_hi[1]))
                new = str(int(round(new_val))) if _is_int(old) else f"{new_val:.4g}"
                if float(new) != float(old):
                    edit = (sym, old, new)
                    break
        if edit is None:
            raise RuntimeError("scripted proposer found no non-trivial edit")
        sym, old, new = edit
        path = node_spec.editable_paths[0]
        return ManagerProposal(
            manager_mode=self.mode,
            proposal_summary=f"{sym} {old} -> {new}",
            proposal_rationale="Seeded random bounded edit (E1b PILOT stand-in for the LLM manager).",
            target_files=tuple(node_spec.editable_paths),
            objective=f"Change {sym} from {old} to {new} in {path} and keep all other hyperparameters unchanged.",
            extra={"structured_edit": {"type": "config_value" if path.endswith((".yaml", ".yml")) else "python_constant",
                                       "path": path, "symbol": sym, "old": old, "new": new},
                   "scripted": {"seed": self.seed, "repetition": self.repetition}},
        )
