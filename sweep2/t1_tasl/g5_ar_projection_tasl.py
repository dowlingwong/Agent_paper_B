"""Pre-pilot G.5 projection and dates on the TASL pair with and without ``autoresearch_fixedtokens`` (G.5 draft §2.8,
§2.10 and §2.11, revision 8). ENGINEERING_ONLY: it reads no run output, no label and no evaluation value.

The seven-node inputs are ``g4_tasl_dates_params.json`` unchanged (census run times on the RTX 6000 Ada, ratio 1.0,
LLM 60 s per call, ran share 0.6, keep share 0.2). The eighth node adds ``autoresearch_fixedtokens`` at its census B1
time, 218.951 s, measured on TASL-2's RTX 4090 (``docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md``,
census table). The formulas are ``g4_lib.g5_node`` and, for the dates, the TASL wrapper ``g4_tasl.recompute_dates``
(one worker slot, the RTX 4090 declared; it drops the HTCondor ``requested_slot_hours``, which the TASL pair does not
have). The tables drop ``requested_slot_hours`` too. The cap of the eight-node rows is 425 GPU-h (R1-G5-DECISIONS).

Pre-pilot only: with no pilot summary the 4090/census ratio is 1.0, so autoresearch's 4090 time is not rescaled.
After the pilot ``recompute_dates`` would multiply every non-pilot node's census time by the measured ratio,
autoresearch's included, which is wrong for a node censused on the 4090 (G.5 draft §8, §9). This script therefore
refuses pilot summaries; it has no such input.

K = 6 is shown only as the hypothetical K-check PASS case (``k_check_row`` here is a placeholder name, not a PLAN row;
the dates CLI checks a real row on origin/main); its date rows carry ``"hypothetical_k_check": true``.

Usage: python sweep2/t1_tasl/g5_ar_projection_tasl.py --today YYYY-MM-DD
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "g4"))
sys.path.insert(0, str(HERE.parent / "g1b"))
import g4_lib  # noqa: E402,F401  (the formulas; used through g4_tasl and g5_projection)
import g4_tasl  # noqa: E402
import g5_projection  # noqa: E402

PARAMS = json.loads((HERE / "g4_tasl_dates_params.json").read_text())
AR = "autoresearch_fixedtokens"
AR_CENSUS_B1_S = 218.951        # TRACKG_U4_CENSUS_20261120.md, census table: B1 on TASL-2 (RTX 4090)
K6_PLACEHOLDER_ROW = "R1-HYPOTHETICAL-K-CHECK"
CAP_SEVEN, CAP_EIGHT = 230, 425                # G5-CAP B; with autoresearch, R1-G5-DECISIONS


def params(*, with_ar: bool, g1b_days: float = None, ran_share: float = None, llm_s: float = None,
           k6: bool = False) -> dict:
    p = copy.deepcopy(PARAMS)
    if with_ar:
        p["t1_nodes"] = p["t1_nodes"] + [AR]
        p["run_seconds"] = {**p["run_seconds"], AR: AR_CENSUS_B1_S}
        p["g5_cap_gpu_hours"] = CAP_EIGHT
    if g1b_days is not None:
        p["g1b_days"] = g1b_days
    if ran_share is not None:
        p["ran_share_fallback"] = ran_share
    if llm_s is not None:
        p["llm_seconds_fallback"] = llm_s
    if k6:
        p["k_check_passed"], p["k_check_row"] = True, K6_PLACEHOLDER_ROW
    return p


def _drop_slot_hours(obj):
    """Remove the HTCondor walltime-request quantities: direct host runs on the TASL pair request no slot-hours."""
    if isinstance(obj, dict):
        return {k: _drop_slot_hours(v) for k, v in obj.items() if "requested_slot_hours" not in k}
    if isinstance(obj, list):
        return [_drop_slot_hours(v) for v in obj]
    return obj


def table(*, with_ar: bool) -> dict:
    """The §2.8 table (W x MEM x ran share x K) for seven or eight nodes."""
    saved = g5_projection.PARAMS
    try:
        g5_projection.PARAMS = params(with_ar=with_ar)
        return _drop_slot_hours(g5_projection.table())
    finally:
        g5_projection.PARAMS = saved


def dates_grid(today: date) -> list[dict]:
    rows = []
    for with_ar in (False, True):
        for k6 in (False, True):
            for g1b_days in (1, 2):
                for label, kw in (("share 0.6, LLM 60 s", {}), ("share 0.8", {"ran_share": 0.8}),
                                  ("LLM 120 s", {"llm_s": 120})):
                    r = g4_tasl.recompute_dates({}, params(with_ar=with_ar, g1b_days=g1b_days, k6=k6, **kw),
                                                today=today)
                    per_node = r["g5_by_K"][str(r["binding_K"])]["per_node"]
                    rows.append({"nodes": 8 if with_ar else 7, "K": r["binding_K"], "g1b_days": g1b_days,
                                 "case": label, "gpu_hours": r["g5_total_gpu_hours"],
                                 "longest_node_gpu_hours": r["longest_node_gpu_hours"],
                                 "ar_gpu_hours": per_node[AR]["gpu_hours"] if with_ar else None,
                                 "labels_done": r["labels_done"], "B7": r["B7"], "B7_slack_days": r["slack_days"]["B7"],
                                 "cap_gpu_hours": CAP_EIGHT if with_ar else CAP_SEVEN,
                                 "within_cap": r["g5_within_cap"],
                                 **({"hypothetical_k_check": True} if k6 else {})})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--today", required=True)
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today)
    print(json.dumps({"basis": "pre-pilot fallbacks; ENGINEERING_ONLY", "today": today.isoformat(),
                      "ar_census_b1_s": AR_CENSUS_B1_S, "table_seven_nodes": table(with_ar=False),
                      "table_eight_nodes": table(with_ar=True), "dates": dates_grid(today)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
