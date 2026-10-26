"""One prompt template for every decision model (RUNBOOK Track P 1.2; spec §2.2). ENGINEERING_ONLY; AI-assisted (Claude).

``serialize_view(view, node_ctx)`` turns the leak-guarded E1 view into a
``DecisionPrompt``. It reads exactly what ``r1.c3.features.featurize_view``
reads (``view.budget_index``, ``view.ledger_prefix``, ``view.current_best``,
``view.proposal``'s structured edit) plus the ``NodeContext`` constants; from a
prefix row it reads only ``budget_index``, ``decision``, ``parsed_metrics``,
``delta_vs_best``, ``current_best_before`` and the structured edit
(``ROW_FIELDS``). No audit, sibling or future field can enter: the featurizer
refuses prefix rows at or after the current trial (``FeatureLeakError``).

Template (``PROMPT_VERSION``), fixed field order:

    state    = node description, budget, incumbent configuration and metric, history (oldest first)
    proposal = the edit (key, old -> new) and the featurizer's rule flags
    question + the 12 options in ``BIN_OPTIONS`` order

Length rule (declared; tested per tokenizer): ``render_text(prompt)`` must fit
``MAX_TOKENS - FRAMING_RESERVE`` tokens under every tokenizer in ``POOL`` (the
reserve is left for each family's own framing: Kev's delimiters, StartLux's
chat template, Laya's head). If it does not, the **oldest history lines are
dropped first** until it does; the node description, budget, incumbent, the
proposal, the question and the options are never cut. ``meta`` records the
history line count and how many lines were dropped. A prompt that does not fit
with no history left raises ``PromptTooLong``.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from typing import Mapping, Sequence

from r1.c3.features import NODE_INFO, NodeContext, active_projection, configuration, featurize_view, parsed_metric
from r1.c3.train.types import BIN_OPTIONS, MAX_TOKENS, PROMPT_VERSION, QUESTION, DecisionPrompt

FRAMING_RESERVE = 128   # tokens left to each family's framing within MAX_TOKENS
ROW_FIELDS = ("budget_index", "decision", "parsed_metrics", "delta_vs_best", "current_best_before", "extra")

# Tokenizers that must accept every prompt (spec §2.2): repo, pinned revision, subfolder. Kev uses its base's tokenizer.
POOL = {
    "qwen3.5-0.8b-base": ("Qwen/Qwen3.5-0.8B-Base", "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68", None),
    "qwen3.5-4b-base": ("Qwen/Qwen3.5-4B-Base", "1001bb4d826a52d1f399e183466143f4da7b741b", None),
    "laya-typed-decisions": ("convaiinnovations/laya-typed-decisions", "e929ae5cf69bc34259cd2f95c9e91145b818b1f0",
                             "tokenizer"),
    "startlux-0.8b-instant": ("startlux-models/StartLux-Decision-v1.1-0.8B-Instant",
                              "6496ae641cc71b149ce9dad69bd97f2a44e7bf11", None),
    "startlux-2b-instant": ("startlux-models/StartLux-Decision-v1.1-2B-Instant",
                            "f1e6cd147dda82c9ffa3e8e725d5c1f175566fb1", None),
    "startlux-4b-instant": ("startlux-models/StartLux-Decision-v1.1-4B-Instant",
                            "416088f77cfce09633906a3675c7cd2e5dabcf10", None),
}


class PromptTooLong(ValueError):
    """The prompt exceeds the token budget even with every history line dropped."""


TOKENIZER_FILES = ["tokenizer*", "*/tokenizer*", "vocab.json", "merges.txt", "special_tokens_map.json",
                   "added_tokens.json", "chat_template.jinja", "config.json"]


@lru_cache(maxsize=None)
def load_tokenizer(name: str):
    """A pool tokenizer at its pinned revision (tokenizer files only; the local snapshot when already cached)."""
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    repo, rev, sub = POOL[name]
    path = snapshot_download(repo, revision=rev, allow_patterns=TOKENIZER_FILES)
    return AutoTokenizer.from_pretrained(f"{path}/{sub}" if sub else path)


def pool_tokenizers() -> dict:
    return {name: load_tokenizer(name) for name in POOL}


def count_tokens(tok, text: str) -> int:
    return len(tok(text, add_special_tokens=False)["input_ids"])


# ---------------------------------------------------------------- template pieces (shared with exam_synthetic)

def fmt(v) -> str:
    if isinstance(v, float):
        return "nan" if math.isnan(v) else f"{v:.6g}"
    return str(v)


def node_lines(node: str, sigma_node: float, memory_mode: str) -> list[str]:
    info = NODE_INFO[node]
    return [f"Node: {node} ({info['family']} family; {info['rows']} rows, {info['features']} features, "
            f"{info['classes']} classes, minority share {info['minority']:.3f})",
            f"Metric: {info['metric']} (higher is better); noise level sigma_node = {fmt(float(sigma_node))}",
            f"Memory: {memory_mode}"]


def budget_line(b: int, runs_total: int) -> str:
    return f"Budget: trial {b} of {runs_total} ({max(runs_total - (b - 1), 0)} worker runs left before this trial)"


def incumbent_lines(config: Mapping, current_best, first_metric, sigma_node: float) -> list[str]:
    cfg = ", ".join(f"{k}={fmt(config[k])}" for k in sorted(config))
    gain = ("n/a" if first_metric is None or current_best is None
            else f"{(current_best - first_metric) / sigma_node:+.2f}")
    return [f"Incumbent configuration (active keys): {cfg}",
            f"Incumbent metric: {fmt(current_best)}; recorded gain since the first valid trial: z = {gain}"]


def edit_text(edit: Mapping | None) -> str:
    if not edit:
        return "(no structured edit)"
    return f"{edit['symbol']}: {edit['old']} -> {edit['new']} (file {edit['path']})"


def history_line(b: int, edit: Mapping | None, decision: str, delta_z: float | None) -> str:
    """One compact history line (the file is omitted; the proposal names it)."""
    if delta_z is None:
        outcome = "skipped" if decision == "skipped" else "no valid metric"
    else:
        outcome = f"{decision}, z {delta_z:+.2f}"
    what = f"{edit['symbol']} {edit['old']} -> {edit['new']}" if edit else "(no edit)"
    return f"t{b}: {what}; {outcome}"


def state_text(head: Sequence[str], history: Sequence[str]) -> str:
    lines = list(head) + ["History (oldest first):"] + (list(history) if history else ["(none)"])
    return "\n".join(lines)


def render_text(prompt: DecisionPrompt) -> str:
    """The neutral rendering the length rule is checked on (families render their own framing around it)."""
    opts = "\n".join(f"{k}. {o}" for k, o in enumerate(prompt.options))
    return f"{prompt.state}\n\nProposal:\n{prompt.proposal}\n\nQuestion: {prompt.question}\nOptions:\n{opts}"


def fit_history(make, history: Sequence[str], tokenizers: Mapping, budget: int) -> tuple[DecisionPrompt, int]:
    """Largest suffix of ``history`` (most recent lines) for which ``make(kept)`` fits ``budget`` under every
    tokenizer. Returns (prompt, number of dropped lines). Token counts grow with the kept lines, so the boundary is
    found by bisection."""
    def fits(k: int) -> bool:
        text = render_text(make(history[len(history) - k:] if k else []))
        return all(count_tokens(t, text) <= budget for t in tokenizers.values())

    n = len(history)
    if fits(n):
        return make(list(history)), 0
    if not fits(0):
        raise PromptTooLong(f"prompt exceeds {budget} tokens with no history")
    lo, hi = 0, n            # fits(lo), not fits(hi)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if fits(mid) else (lo, mid)
    return make(list(history[n - lo:]) if lo else []), n - lo


# ---------------------------------------------------------------- the view

def _allowed(record) -> dict:
    """The fields of a prefix row that the template may read (``ROW_FIELDS``)."""
    row = record if isinstance(record, dict) else record.to_dict()
    return {k: row.get(k) for k in ROW_FIELDS}


def _row_edit(row: Mapping):
    return ((row.get("extra") or {}).get("manager") or {}).get("structured_edit")


def serialize_view(view, node_ctx: NodeContext, *, tokenizers: Mapping | None = None, max_tokens: int = MAX_TOKENS,
                   group: str = "", meta: Mapping | None = None) -> DecisionPrompt | None:
    """``DecisionPrompt`` of the proposal in ``view`` (None when the trial has no features, as in the table)."""
    res = featurize_view(view, node_ctx)          # refuses future rows; replays the incumbent
    if res is None:
        return None
    b = int(view.budget_index)
    sigma = float(node_ctx.sigma_node)
    rows = [_allowed(r) for r in view.ledger_prefix]
    history, first_metric = [], None
    for row in rows:
        metric = parsed_metric(row)
        if metric is not None and first_metric is None:
            first_metric = metric
        d = row.get("delta_vs_best")
        dz = None if metric is None or row.get("decision") == "skipped" or d is None else float(d) / sigma
        history.append(history_line(int(row["budget_index"]), _row_edit(row), row.get("decision") or "", dz))
    incumbent = json.loads(active_projection(configuration(res.incumbent_files), node_ctx.node))
    head = (node_lines(node_ctx.node, sigma, node_ctx.memory_mode) + [budget_line(b, node_ctx.runs_total)]
            + incumbent_lines(incumbent, view.current_best, first_metric, sigma))
    f = res.features
    flags = [f"Edited key is {'active' if f['active_key'] else 'inactive'} for this node's model; "
             f"{'structural' if f['structural'] else 'numeric'} key",
             f"Active configuration equals the incumbent: {'yes' if res.noop else 'no'}; "
             f"evaluated before in this campaign: {'yes' if res.duplicate else 'no'}",
             f"Times this key was edited before: {int(f['key_edit_count'])}; same edit before: "
             f"{int(f['same_edit_count'])}; reverses the last edit of this key: "
             f"{'yes' if f['reverse_of_last_key_edit'] else 'no'}"]
    proposal = "\n".join([f"Edit: {edit_text(res.edit or None)}"] + flags)

    def make(kept):
        return DecisionPrompt(state=state_text(head, kept), proposal=proposal, question=QUESTION, options=BIN_OPTIONS,
                              group=group)

    toks = pool_tokenizers() if tokenizers is None else tokenizers
    prompt, dropped = fit_history(make, history, toks, max_tokens - FRAMING_RESERVE)
    info = {"prompt_version": PROMPT_VERSION, "budget_index": b, "history_total": len(history),
            "history_dropped": dropped, "token_budget": max_tokens - FRAMING_RESERVE,
            "tokenizers": sorted(toks), **(dict(meta) if meta else {})}
    return DecisionPrompt(state=prompt.state, proposal=prompt.proposal, question=prompt.question,
                          options=prompt.options, group=group, meta=info)
