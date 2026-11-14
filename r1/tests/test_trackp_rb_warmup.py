"""R-B SFT warm-up rows from demonstration logs (synthetic logs; no API call, no key, no label table)."""
import numpy as np
import pytest

from r1.c3.rb_demos import DEMO_VERSION, build_messages
from r1.c3.train import rb_warmup as W
from r1.c3.train.types import DecisionPrompt


def prompt(pid, split="train"):
    return DecisionPrompt(state=f"state {pid}", proposal=f"edit {pid}", meta={"proposal_id": pid, "split": split})


def record(p, analysis="looks small", **over):
    rec = {"version": DEMO_VERSION, "status": 200, "analysis": analysis, "model_returned": "DeepSeek-V4.1-Flash-1017",
           "prompt_id": p.meta["proposal_id"], "request": {"messages": build_messages(p)}}
    rec.update(over)
    return rec


Y = list(np.full(12, 1 / 12))
count = lambda text: len(text.split())


def test_accepted_rows_carry_the_three_targets():
    ps = [prompt("a"), prompt("b")]
    res = W.warmup_rows([record(ps[0]), record(ps[1], analysis="  ok  ")], ps, {"a": Y, "b": Y},
                        {"a": 0.3, "b": -0.1}, count_tokens=count)
    assert [r["action_target"] for r in res["rows"]] == [1, 0] and res["refused"] == []
    assert res["rows"][1]["analysis"] == "ok" and res["rows"][0]["teacher_model"].startswith("DeepSeek")


@pytest.mark.parametrize("over, prompts, reason", [
    ({"status": 500}, None, "HTTP 200"),
    ({"analysis": ""}, None, "empty"),
    ({"model_returned": None}, None, "returned model"),
    ({"request": {"messages": [{"role": "user", "content": "leaked label: 0.9"}]}}, None, "leak-guarded"),
    ({"analysis": "w " * 257}, None, "longer than 256"),
    ({}, [prompt("a", split="test")], "training partition"),
])
def test_refusals_are_listed_not_dropped(over, prompts, reason):
    ps = prompts or [prompt("a")]
    res = W.warmup_rows([record(prompt("a"), **over)], ps, {"a": Y}, {"a": 1.0}, count_tokens=count)
    assert res["rows"] == [] and reason in res["refused"][0]["reason"]


def test_first_demonstration_per_prompt_is_kept_and_bad_labels_refused():
    p = prompt("a")
    res = W.warmup_rows([record(p, analysis="first"), record(p, analysis="second")], [p], {"a": Y}, {"a": 1.0},
                        count_tokens=count)
    assert [r["analysis"] for r in res["rows"]] == ["first"]
    bad = W.warmup_rows([record(p)], [p], {"a": [1.0] * 12}, {"a": 1.0}, count_tokens=count)
    assert bad["rows"] == [] and "distribution" in bad["refused"][0]["reason"]


def test_format_only_fallback_uses_training_prompts_only():
    rows = W.format_only_rows([prompt("a"), prompt("b", split="val")], {"a": Y, "b": Y}, {"a": -1.0, "b": 1.0})
    assert len(rows) == 1 and rows[0]["analysis"] == W.FORMAT_ONLY_ANALYSIS and rows[0]["action_target"] == 0
