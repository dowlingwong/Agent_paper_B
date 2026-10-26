"""RUNBOOK Track P 1.2: one prompt template from the leak-guarded view; <= 1,024 tokens for every pool tokenizer.

Leak tests follow Track H's (``test_c3_featurizer_online.py``) on the ReplayView path, so they run without the
harness hooks. ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import dataclasses
import glob
import math
from pathlib import Path

import pytest

from r1.c3 import dataset as D
from r1.c3 import features as F
from r1.c3.features import FeatureLeakError, NodeContext, ReplayProposal, ReplayView, read_jsonl
from r1.c3.train import serialize as S
from r1.c3.train.types import BIN_OPTIONS, MAX_TOKENS, PROMPT_VERSION, QUESTION
from r1.harness import REPO


@pytest.fixture(scope="module")
def pool():
    try:
        return S.pool_tokenizers()
    except Exception as exc:  # pragma: no cover - only without network and cache
        pytest.skip(f"pool tokenizers unavailable: {exc}")


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    """Harness pin 6afdb0e (``is_control_plane_skip``) is not on GitHub; stand in with its definition when absent."""
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def _row(b, key, old, new, decision, metric, best, **more):
    return {"budget_index": b, "decision": decision, "parsed_metrics": {"val_score": metric},
            "current_best_before": best, "delta_vs_best": None if best is None else metric - best,
            "extra": {"manager": {"structured_edit": {"symbol": key, "old": old, "new": new, "path": "train.py"}}},
            **more}


def _ledger():
    return [_row(1, "HIDDEN_UNITS", "32", "64", "kept", 0.90, None),
            _row(2, "ALPHA", "1e-4", "1e-3", "discarded", 0.89, 0.90),
            _row(3, "MAX_ITER", "40", "80", "kept", 0.93, 0.90),
            _row(4, "ALPHA", "1e-4", "1e-3", "discarded", 0.91, 0.93)]


CTX = NodeContext(node="digits_mlp", start_files={"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"},
                  sigma_node=0.0075, runs_total=20, memory_mode="none")


def _view(rows, i):
    edit = rows[i]["extra"]["manager"]["structured_edit"]
    return ReplayView(budget_index=rows[i]["budget_index"], ledger_prefix=tuple(rows[:i]),
                      current_best=rows[i]["current_best_before"], proposal=ReplayProposal(extra={"structured_edit": edit}))


class _Spy:
    def __init__(self, view):
        object.__setattr__(self, "_view", view)
        object.__setattr__(self, "read", set())

    def __getattr__(self, name):
        self.read.add(name)
        return getattr(self._view, name)


class _RecordingRow(dict):
    """A ledger row that records which top-level fields are read."""

    def __init__(self, *a, log, **k):
        super().__init__(*a, **k)
        self.log = log

    def get(self, key, default=None):
        self.log.add(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.log.add(key)
        return super().__getitem__(key)


def test_template_fields_version_and_fixed_options(pool):
    p = S.serialize_view(_view(_ledger(), 3), CTX, tokenizers=pool)
    assert p.question == QUESTION and p.options == BIN_OPTIONS and len(p.options) == 12
    assert p.meta["prompt_version"] == PROMPT_VERSION and p.meta["history_dropped"] == 0
    text = S.render_text(p)
    assert "Node: digits_mlp" in p.state and "Budget: trial 4 of 20" in p.state
    assert "Incumbent configuration (active keys): ALPHA=0.0001, HIDDEN_UNITS=64, MAX_ITER=80" in p.state
    assert p.proposal.startswith("Edit: ALPHA: 1e-4 -> 1e-3 (file train.py)")
    # the same edit ran at t2, but on a different incumbent (MAX_ITER was kept at t3): not a duplicate
    assert "evaluated before in this campaign: no" in p.proposal and "same edit before: 1" in p.proposal
    assert [ln.split(":")[0] for ln in p.state.split("History (oldest first):\n")[1].splitlines()] == ["t1", "t2", "t3"]
    assert text.index(p.state) < text.index(p.proposal) < text.index(QUESTION)
    assert [ln.split(". ", 1)[1] for ln in text.split("Options:\n")[1].splitlines()] == list(BIN_OPTIONS)


def test_reads_only_the_featurizer_inputs(pool):
    rows = _ledger()
    log: set = set()
    spy_rows = [_RecordingRow(r, log=log) for r in rows]
    spy = _Spy(_view(spy_rows, 3))
    S.serialize_view(spy, CTX, tokenizers=pool)
    assert spy.read == {"budget_index", "ledger_prefix", "current_best", "proposal"}
    assert log <= set(S.ROW_FIELDS)


def test_future_own_outcome_and_non_view_fields_are_unreachable(pool):
    rows = _ledger()
    base = S.serialize_view(_view(rows, 3), CTX, tokenizers=pool)
    with pytest.raises(FeatureLeakError):   # a record at or after the current trial
        S.serialize_view(ReplayView(budget_index=3, ledger_prefix=tuple(rows), current_best=0.93,
                                    proposal=ReplayProposal(extra={})), CTX, tokenizers=pool)
    alt = [dict(r) for r in rows]
    alt[3] = {**alt[3], "decision": "kept", "parsed_metrics": {"val_score": 0.99}, "delta_vs_best": 0.06}
    alt.append({**alt[1], "budget_index": 5})
    for r in alt[:3]:     # audit, sibling and free-text fields on prefix rows never reach the prompt
        r.update({"audit": {"delta_audit": 9.9}, "sibling_outcomes": [0.1], "proposal_rationale": "LEAK",
                  "proposal_summary": "LEAK"})
        r["extra"] = {**r["extra"], "audit": {"z": 9.9},
                      "manager": {**r["extra"]["manager"], "worker_memory_context_text": "LEAK"}}
    same = S.serialize_view(_view(alt, 3), CTX, tokenizers=pool)
    assert S.render_text(same) == S.render_text(base) and "LEAK" not in S.render_text(same)


def test_first_trial_and_missing_incumbent_have_no_prompt(pool):
    rows = _ledger()
    assert S.serialize_view(_view(rows, 0), CTX, tokenizers=pool) is None
    assert S.serialize_view(dataclasses.replace(_view(rows, 1), current_best=None), CTX, tokenizers=pool) is None


def _long_ledger(n, value_len=1):
    """n discarded ALPHA trials after one kept trial, then the proposal; values long with ``value_len``."""
    rows, best = [], None
    for b in range(1, n + 2):
        new = f"0.{b}" + "123456789" * value_len
        m = 0.90 + 0.001 * (b % 7)
        rows.append({"budget_index": b, "decision": "discarded" if best is not None else "kept",
                     "parsed_metrics": {"val_score": m}, "current_best_before": best,
                     "delta_vs_best": None if best is None else m - best,
                     "extra": {"manager": {"structured_edit": {
                         "symbol": "HIDDEN_UNITS" if b == 1 else "ALPHA", "old": "32" if b == 1 else "1e-4",
                         "new": "64" if b == 1 else new, "path": "train.py"}}}})
        best = best or m
    return rows


def test_truncation_drops_the_oldest_history_lines_first(pool):
    rows = _long_ledger(300)
    ctx = dataclasses.replace(CTX, runs_total=400)
    p = S.serialize_view(_view(rows, 300), ctx, tokenizers=pool)
    budget = MAX_TOKENS - S.FRAMING_RESERVE
    text = S.render_text(p)
    assert max(S.count_tokens(t, text) for t in pool.values()) <= budget
    hist = p.state.split("History (oldest first):\n")[1].splitlines()
    assert p.meta["history_total"] == 300 and p.meta["history_dropped"] == 300 - len(hist) > 0
    assert hist[-1].startswith("t300:") and hist[0] == f"t{300 - len(hist) + 1}:" + hist[0].split(":", 1)[1]
    # one more line would not fit under at least one tokenizer (the kept suffix is maximal)
    full = S.serialize_view(_view(rows, 300), ctx, tokenizers=pool, max_tokens=10 ** 6)
    all_lines = full.state.split("History (oldest first):\n")[1].splitlines()
    head = p.state.split("History (oldest first):\n")[0]
    longer = dataclasses.replace(p, state=head + "History (oldest first):\n" + "\n".join(all_lines[-len(hist) - 1:]))
    assert max(S.count_tokens(t, S.render_text(longer)) for t in pool.values()) > budget
    # the proposal, question and options are never cut
    assert p.proposal == full.proposal and p.options == BIN_OPTIONS and p.question == QUESTION


def test_prompt_too_long_without_history_is_refused(pool):
    with pytest.raises(S.PromptTooLong):
        S.serialize_view(_view(_ledger(), 3), CTX, tokenizers=pool, max_tokens=S.FRAMING_RESERVE + 100)


@pytest.mark.parametrize("name", list(S.POOL))
def test_worst_case_long_history_and_long_values_fit_each_tokenizer(pool, name):
    rows = _long_ledger(200, value_len=12)
    ctx = dataclasses.replace(CTX, runs_total=400)
    p = S.serialize_view(_view(rows, 200), ctx, tokenizers={name: pool[name]})
    assert S.count_tokens(pool[name], S.render_text(p)) <= MAX_TOKENS - S.FRAMING_RESERVE
    assert p.meta["history_dropped"] > 0


PILOT = [s for s in D.SOURCES if (REPO / D.SOURCES[s]["dir"]).exists()]


@pytest.mark.skipif(len(PILOT) < 3, reason="pilot ledgers not present")
def test_every_pilot_proposal_fits_every_pool_tokenizer(pool):
    noise = D.noise_table()
    n, worst = 0, {k: 0 for k in pool}
    for name in PILOT:
        src, d = D.SOURCES[name], REPO / D.SOURCES[name]["dir"]
        for f in sorted(glob.glob(str(d / src["ledgers"]))):
            inst = Path(f).parent.name
            node = inst.split("__s")[0]
            ctx = NodeContext(node=node, start_files=D._start_files(d, inst, node),
                              sigma_node=noise[node]["sigma_node"], runs_total=src["runs"],
                              memory_mode=src["memory_mode"])
            rows = read_jsonl(Path(f))
            for i, row in enumerate(rows):
                edit = ((row.get("extra") or {}).get("manager") or {}).get("structured_edit")
                v = ReplayView(budget_index=int(row["budget_index"]), ledger_prefix=tuple(rows[:i]),
                               current_best=row.get("current_best_before"),
                               proposal=ReplayProposal(extra={"structured_edit": edit}))
                p = S.serialize_view(v, ctx, tokenizers=pool)
                if p is None:
                    continue
                text = S.render_text(p)
                for k, t in pool.items():
                    worst[k] = max(worst[k], S.count_tokens(t, text))
                n += 1
    assert n > 1000
    assert all(v <= MAX_TOKENS - S.FRAMING_RESERVE for v in worst.values()), worst
    assert not any(math.isnan(v) for v in worst.values())
