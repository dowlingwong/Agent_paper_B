"""L12 tests: forked side query, cap charging, malformed replies (stub LLM; no Ollama)."""
from __future__ import annotations

import copy
import shutil
import tempfile
from pathlib import Path

import pytest

from r1.harness import import_harness
from r1.llm_control import LLMSelfController, build_side_prompt

HARNESS = import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402
from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.control_plane.controller import build_control_view  # noqa: E402
from autoresearch.manager.langgraph_manager import LangGraphManager  # noqa: E402
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402


def _view(epoch="E2"):
    spec = load_registered_node("lr_synthetic", repo_root=HARNESS)
    return build_control_view(epoch=epoch, budget_index=3, current_best=0.9,
                              budget={"llm_calls_remaining": 4, "llm_calls_used": 1}, node=spec)


def test_reply_is_parsed_and_charged():
    ctl = LLMSelfController(lambda p: 'Sure. {"action": "verify", "scores": {"verify": 0.01, "continue": 0}}')
    d = ctl.decide(_view(), {"continue": True, "verify": True})
    assert d.action == "verify" and d.llm_calls == 1 and d.scores["verify"] == 0.01


@pytest.mark.parametrize("reply", ["no json here", '{"action": "teleport"}', '{"action": "skip"}', "{bad json",
                                   '{"action": "verify", "scores": [1, 2]}', '{"action": "verify", "scores": "x"}',
                                   '[1, 2]'])
def test_malformed_or_disallowed_replies_fall_back_to_continue(reply):
    ctl = LLMSelfController(lambda p: reply)
    d = ctl.decide(_view(), {"continue": True, "verify": True, "skip": False})
    assert d.llm_calls == 1
    if ctl.log[-1]["reason"].startswith("parse_failure") or "not_allowed" in ctl.log[-1]["reason"]:
        assert d.action == "continue"
    assert ctl.log[-1]["reason"] != "ok"


def test_no_call_when_cap_exhausted_or_nothing_to_choose():
    calls = []
    ctl = LLMSelfController(lambda p: calls.append(p) or '{"action": "verify"}')
    spec = load_registered_node("lr_synthetic", repo_root=HARNESS)
    view = build_control_view(epoch="E2", budget_index=3, budget={"llm_calls_remaining": 0, "llm_calls_used": 2},
                              node=spec)
    assert ctl.decide(view, {"continue": True, "verify": True}).llm_calls == 0
    assert ctl.decide(_view(), {"continue": True, "verify": False}).llm_calls == 0
    assert calls == []


def test_side_query_leaves_view_and_manager_untouched():
    view = _view()
    before = copy.deepcopy(view.canonical_payload())
    manager = LangGraphManager(llm=lambda *a, **k: "x")
    state = copy.deepcopy(manager.__dict__)
    LLMSelfController(lambda p: '{"action": "continue"}').decide(view, {"continue": True, "verify": True})
    assert view.canonical_payload() == before
    assert manager.__dict__.keys() == state.keys()
    assert all(manager.__dict__[k] is state[k] or manager.__dict__[k] == state[k]
               for k in state if k != "_injected_llm")


def test_prompt_lists_only_allowed_actions():
    p = build_side_prompt(_view(), {"continue": True, "verify": True, "skip": False})
    assert "verify:" in p and "skip:" not in p


def test_side_queries_spend_the_campaign_llm_cap():
    spec = load_registered_node("lr_synthetic", repo_root=HARNESS)
    calls = []
    ctl = LLMSelfController(lambda p: calls.append(1) or '{"action": "continue"}')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copytree(HARNESS / "nodes" / "lr_synthetic", tmp / "node")
        run_real_campaign(node_spec=spec, campaign_id="l12", budget=6, manager_mode="baseline_manager",
                          memory_mode="none", records_path=tmp / "t.jsonl",
                          worker=LocalWorker(node_root=tmp / "node", artifact_dir=tmp / "art"),
                          controller=ctl, compute_budget=ComputeBudget(max_llm_calls=4))
        n_trials = len(TrialAppendStore(tmp / "t.jsonl").read_all())
    assert len(calls) <= 4
    assert n_trials < 6
