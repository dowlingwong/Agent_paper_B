"""The pre-pilot G.5 projection with and without autoresearch_fixedtokens (sweep2/t1_tasl/g5_ar_projection_tasl.py)
and the figures the G.5 draft (revision 8, §2.4, §2.6, §2.8, §2.9, §2.10, §2.11) quotes from it. Synthetic: reads no run output."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g4_tasl  # noqa: E402
import g5_ar_projection_tasl as P  # noqa: E402
import g5_projection_tasl as P7  # noqa: E402

DRAFT = ROOT / "docs" / "r1" / "proposals" / "T1_G5_AUTHORIZATION_DRAFT_20261120.md"
TODAY = date(2026, 11, 22)


def _row(rows, **kw):
    hits = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    assert len(hits) == 1, kw
    return hits[0]


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if "requested_slot_hours" not in k}
    return obj


def test_seven_node_table_is_the_published_one_and_params_are_unchanged():
    assert P.table(with_ar=False) == _strip(P7.table())                 # review m6: no HTCondor slot-hours
    assert "requested_slot_hours" not in json.dumps(P.table(with_ar=True))
    assert P.PARAMS == json.loads((ROOT / "sweep2" / "t1_tasl" / "g4_tasl_dates_params.json").read_text())
    p = P.params(with_ar=True)
    assert P.AR not in P.PARAMS["t1_nodes"] and P.AR not in P.PARAMS["run_seconds"]      # no mutation
    assert p["t1_nodes"][-1] == P.AR and p["run_seconds"][P.AR] == 218.951


def test_ar_census_time_is_the_u4_census_row():
    census = (ROOT / "docs" / "r1" / "reports" / "trackg_g0_20261117" / "TRACKG_U4_CENSUS_20261120.md").read_text()
    row = next(line for line in census.splitlines() if line.startswith("| autoresearch_fixedtokens |"))
    assert row.split("|")[4].strip() == f"{P.AR_CENSUS_B1_S} s" and "TASL-2 4090" in row


def test_eight_node_table_and_dates_match_the_draft():
    t8 = P.table(with_ar=True)
    assert t8["W=manager_calls MEM=one_mode share=0.6 K=10"]["gpu_hours"] == 305.3
    assert t8["W=manager_calls MEM=one_mode share=0.8 K=10"]["gpu_hours"] == 386.0
    assert t8["W=manager_calls MEM=one_mode share=0.6 K=6"]["gpu_hours"] == 208.5
    assert t8["W=worker_runs MEM=one_mode share=0.6 K=10"]["gpu_hours"] == 489.5
    rows = P.dates_grid(TODAY)
    base7 = _row(rows, nodes=7, K=10, g1b_days=1, case="share 0.6, LLM 60 s")
    assert (base7["labels_done"], base7["B7"], base7["B7_slack_days"]) == ("2026-12-05", "2026-12-08", 0)
    base8 = _row(rows, nodes=8, K=10, g1b_days=2, case="share 0.6, LLM 60 s")
    assert (base8["gpu_hours"], base8["ar_gpu_hours"], base8["B7"], base8["B7_slack_days"]) == \
        (305.3, 138.44, "2026-12-15", -7)
    k6 = _row(rows, nodes=8, K=6, g1b_days=2, case="share 0.6, LLM 60 s")
    assert (k6["gpu_hours"], k6["B7"], k6["within_cap"], k6["cap_gpu_hours"]) == (208.5, "2026-12-11", True, 425)
    assert k6["hypothetical_k_check"] is True and "hypothetical_k_check" not in base8          # review m7
    hi = _row(rows, nodes=8, K=10, g1b_days=2, case="share 0.8")
    assert hi["gpu_hours"] == 386.0 and hi["gpu_hours"] * 1.10 <= 425 == hi["cap_gpu_hours"]  # the cap, R1-G5-DECISIONS
    assert (hi["labels_done"], hi["B7"], hi["B7_slack_days"]) == ("2026-12-16", "2026-12-19", -11)
    llm = _row(rows, nodes=8, K=10, g1b_days=2, case="LLM 120 s")
    assert (llm["gpu_hours"], llm["labels_done"], llm["B7"], llm["B7_slack_days"]) == (337.3, "2026-12-14",
                                                                                     "2026-12-17", -9)
    k6hi = _row(rows, nodes=8, K=6, g1b_days=2, case="share 0.8")
    assert (k6hi["gpu_hours"], k6hi["B7"], k6hi["B7_slack_days"]) == (259.9, "2026-12-13", -5)
    for case in ("share 0.6, LLM 60 s", "share 0.8", "LLM 120 s"):      # one day earlier with 1 day of G.1b
        for k in (10, 6):
            two, one = (_row(rows, nodes=8, K=k, g1b_days=d, case=case) for d in (2, 1))
            assert date.fromisoformat(two["B7"]) - date.fromisoformat(one["B7"]) == date(2026, 1, 2) - date(2026, 1, 1)
    like7 = _row(rows, nodes=7, K=10, g1b_days=2, case="share 0.6, LLM 60 s")   # review m3: B at 2 days
    assert like7["B7"] == "2026-12-09" and (date(2026, 12, 15) - date(2026, 12, 9)).days == 6
    text = DRAFT.read_text()
    for needle in ("| 10 | share 0.6, LLM 60 s | 305.3 | 12 Dec | 15 Dec | −7 |",
                   "| 10 | share 0.8 | 386.0 | 16 Dec | 19 Dec | −11 |",
                   "| 10 | LLM 120 s | 337.3 | 14 Dec | 17 Dec | −9 |",
                   "| 6 (K-check PASS row only) | share 0.6, LLM 60 s | 208.5 | 8 Dec | 11 Dec | −3 |",
                   "| 6 (K-check PASS row only) | share 0.8 | 259.9 | 10 Dec | 13 Dec | −5 |",
                   "labels done 5 Dec, B.7 8 Dec, **0 days of slack**", "425 GPU-h",
                   "B.7 would have been 9 Dec against A's 15 Dec, 6 days earlier"):
        assert needle in text, needle


def test_the_other_figures_the_draft_quotes(monkeypatch):
    """Review m8: §2.4 (parents re-run), §2.9 (campaign hours), autoresearch's breakdown, the eight-node MEM B and W B
    rows, the seven-node table."""
    text = DRAFT.read_text()
    t7, t8 = P.table(with_ar=False), P.table(with_ar=True)
    for t, key, gpu, audited in (
            (t7, "W=manager_calls MEM=one_mode share=0.6 K=10", 166.9, 144),
            (t7, "W=manager_calls MEM=one_mode share=0.8 K=10", 206.2, 192),
            (t7, "W=manager_calls MEM=one_mode share=0.6 K=6", 118.7, 144),
            (t8, "W=manager_calls MEM=both_modes share=0.6 K=10", 610.7, 288),
            (t8, "W=manager_calls MEM=both_modes share=0.8 K=10", 772.1, 384),
            (t8, "W=manager_calls MEM=both_modes share=0.8 K=6", 519.8, 384),
            (t8, "W=worker_runs MEM=one_mode share=0.8 K=10", 475.5, 240),
            (t8, "W=worker_runs MEM=one_mode share=0.6 K=6", 334.9, 240)):
        assert (t[key]["gpu_hours"], t[key]["audited_per_node"]) == (gpu, audited), key
    today = TODAY
    for with_ar, share, total, campaign in ((False, 0.6, 166.9, 39.4), (False, 0.8, 206.2, 43.0),
                                            (True, 0.6, 305.3, 55.1), (True, 0.8, 386.0, 62.3)):
        r = g4_tasl.recompute_dates({}, P.params(with_ar=with_ar, ran_share=share), today=today)
        per_node = r["g5_by_K"]["10"]["per_node"]
        assert round(sum(v["gpu_hours"] for v in per_node.values()), 1) == total
        assert round(sum(v["campaign_gpu_hours"] for v in per_node.values()), 1) == campaign
        reuse = P.params(with_ar=with_ar, ran_share=share)
        reuse["reuse_parent_runs"] = False
        no_reuse = g4_tasl.recompute_dates({}, reuse, today=today)["g5_total_gpu_hours"]
        assert no_reuse == {(False, 0.6): 188.3, (False, 0.8): 235.6, (True, 0.6): 349.5, (True, 0.8): 445.5}[
            (with_ar, share)]
    ar = g4_tasl.recompute_dates({}, P.params(with_ar=True), today=today)["g5_by_K"]["10"]["per_node"][P.AR]
    assert (ar["campaign_gpu_hours"], ar["audit_gpu_hours"], ar["jobs"], ar["audit_chunks"], ar["gpu_hours"]) == \
        (15.68, 118.6, 10, 8, 138.44)
    ar8 = g4_tasl.recompute_dates({}, P.params(with_ar=True, ran_share=0.8), today=today)["g5_by_K"]["10"]["per_node"]
    ar6 = g4_tasl.recompute_dates({}, P.params(with_ar=True, k6=True), today=today)["g5_by_K"]["6"]["per_node"]
    assert (ar8[P.AR]["gpu_hours"], ar6[P.AR]["gpu_hours"]) == (179.83, 89.75)
    for needle in ("188.3 GPU-h for seven nodes and 349.5", "235.6 (above 230) and 445.5 (above 425)",
                   "167 + 39 ≈ 206", "206 + 43 ≈ 249", "305 + 55 ≈ 360", "386 + 62 ≈ 448 at 0.8 (above 425)",
                   "campaigns 15.7, audits 118.6; 10 jobs, 8 of them audit", "179.8 GPU-h at share 0.8 and 89.8",
                   "| A: 20 calls | B: both | 0.8 | 519.8 | 772.1 | 384 |", "3.225×", "67.901 s"):
        assert needle in text, needle


def test_k6_placeholder_is_not_a_plan_row_name_and_cli_runs(capsys):
    assert not re.search(r"^\| R1-HYPOTHETICAL-K-CHECK ", (ROOT / "docs" / "r1" / "PLAN.md").read_text(), re.M)
    assert P.main(["--today", "2026-11-22"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["basis"].startswith("pre-pilot") and len(out["dates"]) == 24
    assert all(r.get("hypothetical_k_check") is (True if r["K"] == 6 else None) for r in out["dates"])


def test_draft_stays_unsigned():
    text = DRAFT.read_text()
    assert re.search(r"^approved: false$", text, re.M) and not re.search(r"^approved: true", text, re.M)
