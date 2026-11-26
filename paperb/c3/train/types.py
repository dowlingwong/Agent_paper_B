"""Shared Track P types: the neutral decision prompt and the DecisionModel contract (spec §2).

Every wrapper in ``model.py`` takes a list of ``DecisionPrompt`` (built by
``serialize.py`` from the leak-guarded view, or by ``exam_synthetic.py``) and
renders it in its family's native format itself. Bins come from
``r1.c3.labels`` (bin 0 = inert/no-op, bins 1..11 over z = Delta / sigma_node);
the order of ``BIN_OPTIONS`` is fixed and is the order of every 12-vector.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Protocol, Sequence

from r1.c3.labels import BIN_NAMES, EDGES, N_BINS

# Fixed option texts and order of the 12-option decision question (spec §2.2: "fixed bin names and order").
BIN_OPTIONS: tuple[str, ...] = (
    "no effect: the edit leaves the active configuration unchanged",
    *(f"standardised change z in {name}" for name in BIN_NAMES[1:]),
)
assert len(BIN_OPTIONS) == N_BINS

QUESTION = ("How much will this proposed edit change the validation metric, in units of the node's noise level "
            "(z = change / sigma_node; positive is better)?")

PROMPT_VERSION = "trackp_prompt/v2"   # v2 (author, 14 Nov): budget line by worker runs used (W2)
T1_PROMPT_VERSION = "trackp_prompt_t1/1"   # T1 (G.5) rows: serialize_t1.py (D7 of the ARMS-T1FEAT A report)
MAX_TOKENS = 1024  # spec §2.2: the whole serialised prompt, every tokenizer in the pool (Laya's limit)


@dataclass(frozen=True)
class DecisionPrompt:
    """One proposal as the decision models see it.

    ``state``: the loop state text (node, budget, incumbent, recent history), shared by all proposals on one state;
    ``proposal``: the proposed edit text (the branch); ``question``/``options``: the 12-option decision question.
    ``group``: state id (tree packing groups branches of one state, never across splits); ``meta``: bookkeeping that
    never reaches a model (proposal id, split, truncation record).
    """

    state: str
    proposal: str
    question: str = QUESTION
    options: tuple[str, ...] = BIN_OPTIONS
    group: str = ""
    meta: dict = field(default_factory=dict, compare=False)


class DecisionModel(Protocol):
    """Spec §2.5. ``forward`` returns ``{"belief_logits": [N, 12], "action_logit": [N] | None}`` (torch tensors)."""

    family: str

    def forward(self, batch: Sequence[DecisionPrompt]) -> dict: ...

    def trainable_parameters(self) -> Iterator: ...

    def save(self, path) -> dict: ...  # adapter + heads only; returns {"files": {name: sha256}}

    def load(self, path) -> dict: ...  # verifies the recorded sha256; returns the same record


__all__ = ["BIN_OPTIONS", "DecisionModel", "DecisionPrompt", "EDGES", "MAX_TOKENS", "N_BINS", "PROMPT_VERSION",
           "QUESTION", "T1_PROMPT_VERSION"]
