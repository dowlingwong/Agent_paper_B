"""W2 (PLAN R1-SEQ-BUDGET-FIELDS): budget fields from worker runs. ENGINEERING_ONLY; AI-assisted (Claude).

On execute-all campaigns (every row ran the worker once, no verify) the new
``budget_frac_left`` and the serialized budget line must equal the old
trial-indexed values exactly; with control-plane skips, precondition rejections
or verify re-runs they must follow the true worker-run count.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from r1.c3 import features as F
from r1.c3.accounting import campaign_usage
from r1.c3.features import NodeContext, ReplayProposal, ReplayView, featurize_view, row_worker_runs
from r1.c3.train import serialize as S
from r1.scripts import w2_execute_all_identity_check as CHECK

W = 20
CTX = NodeContext(node="digits_mlp", start_files={"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"},
                  sigma_node=0.0075, runs_total=W, memory_mode="none")
EDITS = [("ALPHA", "1e-4", "1e-3"), ("ALPHA", "1e-3", "1e-4"), ("MAX_ITER", "40", "80"), ("MAX_ITER", "80", "40"),
         ("HIDDEN_UNITS", "32", "64"), ("HIDDEN_UNITS", "64", "32")]


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    """As in test_trackp_serialize: stand in for the harness definition when the pin lacks it."""
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def old_frac(b: int) -> float:
    return 1.0 - (b - 1) / W


def old_line(b: int) -> str:
    return f"Budget: trial {b} of {W} ({max(W - (b - 1), 0)} worker runs left before this trial)"


def execute_all(seed: int, n: int = W, worker_mode: str | None = "local", not_kept=(), failed=()) -> list[dict]:
    """A consistent execute-all ledger: each edit is applied to the replayed incumbent (rows in ``not_kept`` never keep)."""
    rng = random.Random(seed)
    cfg = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}
    rows, best = [], None
    for b in range(1, n + 1):
        key = rng.choice(sorted(cfg))
        new = {"HIDDEN_UNITS": ["32", "64", "128"], "ALPHA": ["1e-4", "1e-3", "1e-2"],
               "MAX_ITER": ["40", "80", "160"]}[key]
        new = rng.choice([v for v in new if v != cfg[key]])
        metric = round(0.85 + 0.1 * rng.random(), 4)
        fail = (b - 1) in failed and best is not None   # the worker ran and crashed: no metric, no keep
        kept = (best is None or metric > best) and (b - 1) not in not_kept and not fail
        row = {"budget_index": b, "decision": "failed_invalid" if fail else "kept" if kept else "discarded",
               "parsed_metrics": {} if fail else {"val_score": metric},
               "current_best_before": best, "delta_vs_best": None if (fail or best is None) else metric - best,
               "extra": {"manager": {"structured_edit": {"symbol": key, "old": cfg[key], "new": new, "path": "train.py"}}}}
        if worker_mode is not None:
            row["worker_mode"] = worker_mode
        rows.append(row)
        if kept:
            cfg[key], best = new, metric
    return rows


def view(rows, i):
    edit = rows[i]["extra"]["manager"]["structured_edit"]
    return ReplayView(budget_index=rows[i]["budget_index"], ledger_prefix=tuple(rows[:i]),
                      current_best=rows[i]["current_best_before"], proposal=ReplayProposal(extra={"structured_edit": edit}))


class _FakeTok:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


@pytest.mark.parametrize("worker_mode", ["local", None])
@pytest.mark.parametrize("seed", range(5))
def test_execute_all_features_and_budget_line_are_identical(seed, worker_mode):
    rows = execute_all(seed, worker_mode=worker_mode)
    seen = 0
    for i in range(len(rows)):
        b = rows[i]["budget_index"]
        res = featurize_view(view(rows, i), CTX)
        used = sum(row_worker_runs(r) for r in rows[:i])
        assert used == b - 1
        assert S.budget_line(b, W, used) == old_line(b) == S.budget_line(b, W)
        if res is None:
            continue
        seen += 1
        assert res.features["budget_frac_left"] == old_frac(b)  # exact, not approximate
        prompt = S.serialize_view(view(rows, i), CTX, tokenizers={"fake": _FakeTok()})
        assert old_line(b) in prompt.state.splitlines()
    assert seen >= W - 2


def test_skips_prechecks_and_verify_follow_true_worker_runs():
    rows = execute_all(11, n=8, not_kept={2, 3})
    rows[2] = {**rows[2], "decision": "skipped", "parsed_metrics": {}, "delta_vs_best": None, "worker_mode": "control_plane",
               "extra": {**rows[2]["extra"], "control": {"epoch": "E1", "action": "skip", "reason": "predicted_no_gain"}}}
    rows[3] = {**rows[3], "decision": "failed_invalid", "parsed_metrics": {}, "delta_vs_best": None,
               "worker_mode": "local_precheck"}
    rows[4] = {**rows[4], "extra": {**rows[4]["extra"], "control": {"epoch": "E2", "verify": {"r": 2, "pairs": [1, 2]}}}}
    expected_used = [0, 1, 2, 2, 2, 7, 8, 9]  # row 3: 0, row 4: 0, row 5: 1 + 2*2
    for i, row in enumerate(rows):
        used = sum(row_worker_runs(r) for r in rows[:i])
        assert used == expected_used[i]
        assert S.budget_line(row["budget_index"], W, used).endswith(f"({W - used} worker runs left before this trial)")
    res = featurize_view(view(rows, 7), CTX)
    assert res is not None and res.features["budget_frac_left"] == 1.0 - 9 / W != old_frac(8)


def test_missing_worker_mode_skip_with_control_counts_none():
    assert row_worker_runs({"decision": "skipped", "extra": {"control": {"epoch": "E1", "action": "skip"}}}) == 0
    assert row_worker_runs({"decision": "discarded", "extra": {}}) == 1
    assert row_worker_runs({"decision": "skipped", "extra": {}}) == 1


def test_rule_matches_the_accounting_worker_run_count(tmp_path):
    rows = [{"worker_mode": "local", "extra": {}}, {"worker_mode": "control_plane", "extra": {}},
            {"worker_mode": "local_precheck", "extra": {}}, {"worker_mode": "local", "extra": {"control": {"verify": {"r": 3}}}},
            {"worker_mode": "local", "extra": {"control": {"verify": {"pairs": [1, 2]}}}}]
    rec, ev = tmp_path / "root_trials.jsonl", tmp_path / "root_events.jsonl"
    rec.write_text("".join(json.dumps(r) + "\n" for r in rows)); ev.write_text("")
    usage = campaign_usage(rec, ev, arm="x", instance="i", information_set="s", worker_run_cap=W, llm_call_cap=None,
                           manager_deterministic=True)
    assert usage.worker_runs == sum(row_worker_runs(r) for r in rows) == 1 + 0 + 0 + 7 + 5


def test_identity_check_script_passes_execute_all_and_stops_on_difference(tmp_path):
    good = tmp_path / "a" / "root_trials.jsonl"; good.parent.mkdir()
    good.write_text("".join(json.dumps(r) + "\n" for r in execute_all(3)))
    assert CHECK.main([str(good), "--runs-total", str(W)]) == 0
    bad_rows = execute_all(4)
    bad_rows[5]["worker_mode"] = "control_plane"
    bad = tmp_path / "b" / "root_trials.jsonl"; bad.parent.mkdir()
    bad.write_text("".join(json.dumps(r) + "\n" for r in bad_rows))
    assert CHECK.main([str(good), str(bad), "--runs-total", str(W)]) == 3


GOLDEN = Path(__file__).parent / "data" / "w2_execute_all_golden_a15300ca.json"


def _outputs(rows):
    out = []
    for i in range(len(rows)):
        res = featurize_view(view(rows, i), CTX)
        if res is None:
            out.append(None)
            continue
        p = S.serialize_view(view(rows, i), CTX, tokenizers={"fake": _FakeTok()})
        out.append({"features_hash": F.features_hash(res.features), "budget_frac_left": res.features["budget_frac_left"],
                    "text": S.render_text(p), "meta": json.loads(json.dumps(p.meta, default=str))})
    return out


def test_execute_all_matches_golden_generated_at_base_commit():
    """Feature hash, full prompt text and meta equal what the pre-W2 code (a15300ca) produced on the same ledgers.

    The golden file was generated by running the base checkout's own code on these ledgers (four W = 20
    campaigns, three with failed worker runs); it holds the ledgers and the outputs.
    """
    golden = json.loads(GOLDEN.read_text())
    assert golden["generated_at_commit"] == "a15300ca" and golden["runs_total"] == W
    n = 0
    for camp in golden["campaigns"]:
        got = _outputs(camp["rows"])
        assert got == camp["expected"]
        n += sum(1 for e in got if e)
    assert n >= 70


def test_golden_comparison_detects_a_non_execute_all_row():
    camp = json.loads(GOLDEN.read_text())["campaigns"][0]
    rows = [dict(r) for r in camp["rows"]]
    i = next(k for k, r in enumerate(rows) if r["decision"] == "failed_invalid")
    rows[i]["worker_mode"] = "local_precheck"          # the worker did not run: one run fewer from here on
    got = _outputs(rows)
    assert got[:i + 1] == camp["expected"][:i + 1]
    assert all(g != e for g, e in zip(got[i + 1:], camp["expected"][i + 1:]) if e)


def test_ghost_and_ctrl_only_rows_count_their_debited_run():
    for arm in ("ghost", "ctrl_only"):
        row = {"decision": "skipped", "worker_mode": "control_plane",
               "extra": {"control": {"epoch": "E1", "action": "skip", "arm": arm}}}
        assert row_worker_runs(row) == 1
    assert row_worker_runs({"decision": "skipped", "worker_mode": "control_plane",
                            "extra": {"control": {"epoch": "E1", "action": "skip", "arm": "skip"}}}) == 0


def test_trial_budget_changes_only_the_trial_denominator():
    assert S.budget_line(25, W, 16, trial_budget=40) == "Budget: trial 25 of 40 (4 worker runs left before this trial)"
    assert S.budget_line(5, W, 4, trial_budget=None) == old_line(5)
    assert F.FEATURIZER_VERSION == "c3_features/v3"
    for bad in (0, -1, 2.5, True):
        with pytest.raises(ValueError):
            NodeContext(node="digits_mlp", start_files={}, sigma_node=1.0, runs_total=W, memory_mode="none", trial_budget=bad)


def test_identity_check_reports_row_kinds_reads_gz_and_refuses_sealed(tmp_path):
    import gzip
    rows = execute_all(5)
    rows[3] = {**rows[3], "worker_mode": "local_precheck"}
    p = tmp_path / "x" / "root_trials.jsonl.gz"; p.parent.mkdir()
    p.write_bytes(gzip.compress("".join(json.dumps(r) + "\n" for r in rows).encode()))
    res = CHECK.check_ledger(p, W)
    assert res["differences"] > 0 and res["rows_not_counting_one"] == {"precheck_rejection": 1}
    sealed = tmp_path / "r1_sealed" / "root_trials.jsonl"; sealed.parent.mkdir()
    sealed.write_text("")
    assert CHECK.main([str(sealed), "--runs-total", str(W)]) == 2
