"""Stage R-B SFT warm-up rows from the teacher's demonstration analyses (spec §6.4 warm start, step 2). Code only.

ENGINEERING_ONLY; AI-assisted (Claude). No API call is made here: the demonstrations are written by
``r1/c3/rb_demos.DemoWriter`` (DeepSeek, R1-RB-TEACHER) into ``calls.jsonl``; this module only reads such a log and
joins it with the training prompts.

A warm-up row is ``{"prompt": DecisionPrompt, "analysis": str, "y_train": [12], "action_target": 1[u > 0]}`` (spec:
"SFT targets: the demonstration analysis, y_train (belief) and 1[u > 0] (action)").

Checks, each a refusal of the record (listed in the result, never silently dropped):
* the record is ``rb_demos/v1`` with HTTP 200, a non-empty analysis and a returned model string (logged per §6.4);
* **leak guard**: the logged request's messages equal ``rb_demos.build_messages(prompt)`` for the joined prompt, so
  the teacher saw only the serialised state and proposal;
* the prompt is in the training partition (``meta['split'] == 'train'``); val and test prompts are refused;
* the analysis is at most 256 tokens by the caller's tokenizer (``count_tokens``); longer ones are refused.
A prompt with several accepted demonstrations keeps the first one in log order.

``format_only_rows`` is the spec's fallback (step 3): a short template analysis when no demonstration is usable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from r1.c3.rb_demos import DEMO_VERSION, MAX_ANALYSIS_TOKENS, build_messages
from r1.c3.train.types import DecisionPrompt

FORMAT_ONLY_ANALYSIS = "The edit changes one setting; its effect relative to the noise level is uncertain."


def read_calls(path: Path | str) -> list[dict]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def warmup_rows(calls: Iterable[Mapping], prompts: Sequence[DecisionPrompt], y_train: Mapping[str, Sequence[float]],
                u: Mapping[str, float], *, count_tokens: Callable[[str], int]) -> dict:
    by_id = {p.meta.get("proposal_id"): p for p in prompts}
    rows, refused, seen = [], [], set()
    for i, rec in enumerate(calls):
        pid = rec.get("prompt_id")
        reason = None
        prompt = by_id.get(pid)
        if rec.get("version") != DEMO_VERSION or rec.get("status") != 200:
            reason = "not an rb_demos/v1 HTTP 200 record"
        elif not isinstance(rec.get("analysis"), str) or not rec["analysis"].strip():
            reason = "empty analysis"
        elif not rec.get("model_returned"):
            reason = "no returned model string"
        elif prompt is None:
            reason = "prompt not in the given training prompts"
        elif prompt.meta.get("split") != "train":
            reason = "prompt is not in the training partition"
        elif (rec.get("request") or {}).get("messages") != build_messages(prompt):
            reason = "logged request differs from the leak-guarded messages"
        elif count_tokens(rec["analysis"]) > MAX_ANALYSIS_TOKENS:
            reason = f"analysis longer than {MAX_ANALYSIS_TOKENS} tokens"
        elif pid not in y_train or pid not in u:
            reason = "no training label for this prompt"
        if reason:
            refused.append({"index": i, "prompt_id": pid, "reason": reason})
            continue
        if pid in seen:
            continue
        seen.add(pid)
        y = np.asarray(y_train[pid], dtype=float)
        if y.shape != (12,) or not np.isclose(y.sum(), 1.0) or np.any(y < 0):
            refused.append({"index": i, "prompt_id": pid, "reason": "y_train is not a 12-bin distribution"})
            seen.discard(pid)
            continue
        rows.append({"prompt": prompt, "analysis": rec["analysis"].strip(), "y_train": y.tolist(),
                     "action_target": int(float(u[pid]) > 0), "teacher_model": rec["model_returned"]})
    return {"rows": rows, "refused": refused}


def format_only_rows(prompts: Sequence[DecisionPrompt], y_train: Mapping[str, Sequence[float]],
                     u: Mapping[str, float]) -> list[dict]:
    """Fallback warm-up (spec §6.4 step 3): the fixed template analysis; R-B is then reported "without warm-up"."""
    out = []
    for p in prompts:
        pid = p.meta.get("proposal_id")
        if p.meta.get("split") != "train" or pid not in y_train or pid not in u:
            continue
        out.append({"prompt": p, "analysis": FORMAT_ONLY_ANALYSIS, "y_train": list(map(float, y_train[pid])),
                    "action_target": int(float(u[pid]) > 0), "teacher_model": None})
    return out
