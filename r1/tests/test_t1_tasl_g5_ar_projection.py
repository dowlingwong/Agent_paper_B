"""The pre-pilot G.5 projection with and without autoresearch_fixedtokens (sweep2/t1_tasl/g5_ar_projection_tasl.py)
and the figures the G.5 draft (revision 7, §2.6, §2.8, §2.10, §2.11) quotes from it. Synthetic: reads no run output."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g5_ar_projection_tasl as P  # noqa: E402
import g5_projection_tasl as P7  # noqa: E402

DRAFT = ROOT / "docs" / "r1" / "proposals" / "T1_G5_AUTHORIZATION_DRAFT_20261120.md"
TODAY = date(2026, 11, 22)


def _row(rows, **kw):
    hits = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    assert len(hits) == 1, kw
    return hits[0]


def test_seven_node_table_is_the_published_one_and_params_are_unchanged():
    assert P.table(with_ar=False) == P7.table()
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
    assert (k6["gpu_hours"], k6["B7"], k6["within_cap_230"]) == (208.5, "2026-12-11", True)
    hi = _row(rows, nodes=8, K=10, g1b_days=2, case="share 0.8")
    assert hi["gpu_hours"] == 386.0 and hi["gpu_hours"] * 1.10 <= 425        # G5-CAP B with autoresearch
    text = DRAFT.read_text()
    for needle in ("| 10 | share 0.6, LLM 60 s | 305.3 | 12 Dec | 15 Dec | −7 |",
                   "| 6 (K-check PASS row only) | share 0.6, LLM 60 s | 208.5 | 8 Dec | 11 Dec | −3 |",
                   "labels done 5 Dec, B.7 8 Dec, **0 days of slack**", "425 GPU-h"):
        assert needle in text, needle


def test_k6_placeholder_is_not_a_plan_row_name_and_cli_runs(capsys):
    assert not re.search(r"^\| R1-HYPOTHETICAL-K-CHECK ", (ROOT / "docs" / "r1" / "PLAN.md").read_text(), re.M)
    assert P.main(["--today", "2026-11-22"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["basis"].startswith("pre-pilot") and len(out["dates"]) == 24


def test_draft_stays_unsigned():
    text = DRAFT.read_text()
    assert re.search(r"^approved: false$", text, re.M) and not re.search(r"^approved: true", text, re.M)
