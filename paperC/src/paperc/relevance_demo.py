"""Decision-relevance check on E-SYN records (build runbook P5, demonstration): ``python -m paperc.relevance_demo``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY. For every E-SYN world, records ``N`` campaigns of
the world's tuned N1 from the committed ladder table (instances 0 .. N-1), measures E1 against N1's own g and E2
against N1's own h (the decisions N1 actually took), and writes ``paperC/docs/reports/RELEVANCE_ESYN_20261116.md``
through ``paperc.relevance``.
E-SYN results are implementation checks, never evidence about the real loop.
"""
from __future__ import annotations

import json
from pathlib import Path

from paperc import relevance as RV
from paperc.esyn import policies as EP, sim
from paperc.esyn.extra import WORLDS
from paperc.runner import OUT as LADDER

N = 50
REPORT = Path(__file__).resolve().parents[2] / "docs" / "reports" / "RELEVANCE_ESYN_20261116.md"


def main() -> Path:
    lad = json.loads(LADDER.read_text())
    rows, prices, hs = [], {}, {}
    for name, w in WORLDS.items():
        n1 = EP.from_name(lad["worlds"][name]["rows"]["N1"]["policy"])
        prices[f"esyn_{name}"], hs[f"esyn_{name}"] = n1.g, n1.h
        for i in range(N):
            rows += sim.run_campaign(w, n1, i, record=True).rows
    summ = RV.relevance(rows, thresholds={"N1 g": prices}, h=hs, belief="a2u", validate=True)
    md = RV.markdown(summ, title="Decision-relevance check on E-SYN records (N1, 50 campaigns per world)",
                     validated=True)
    md += ("\nSource: `python -m paperc.relevance_demo`: records of each world's tuned N1 from "
           "`esyn/ladder_table_v1.json`, instances 0–49; E1 against N1's own g, E2 against N1's own h. On E-SYN these "
           "are the tuned rule's own thresholds, so the shares measure how many decisions sit near N1's cuts, not near "
           "a real run price. In five worlds (budget, eval_allocation, keep_feedback, shared_error, strict_null) the "
           "95th percentile of (V\\* − g) / sigma_node is at most about 0.45, so almost every E1 decision falls inside "
           "the bands, unlike Track S's 2.6–4.1 sigma at STOP 4. The exceptions are information (95th percentile about "
           "3.4, maximum about 19, from the size-16 follow-ups) and interaction (a tail up to about 3.7). In the four "
           "worlds with g = 0, N1 skips nothing or almost nothing (policy skips column: one skip in interaction), so "
           "its E1 decisions sit at the cut but do not change.\n")
    REPORT.write_text(md)
    return REPORT


if __name__ == "__main__":
    print(main())
