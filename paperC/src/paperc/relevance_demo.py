"""Decision-relevance check on E-SYN records (build runbook P5, demonstration): ``python -m paperc.relevance_demo``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY. For every E-SYN world, records ``N`` campaigns of
the world's tuned N1 from the committed ladder table (instances 0 .. N-1), takes N1's g as the run price and h = 0
(the Bayes keep margin), and writes ``paperC/docs/reports/RELEVANCE_ESYN_20261116.md`` through ``paperc.relevance``.
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
    rows, prices = [], {}
    for name, w in WORLDS.items():
        n1 = EP.from_name(lad["worlds"][name]["rows"]["N1"]["policy"])
        prices[f"esyn_{name}"] = n1.g
        for i in range(N):
            rows += sim.run_campaign(w, n1, i, record=True).rows
    summ = RV.relevance(rows, g=prices, validate=True)
    md = RV.markdown(summ, belief="a2u", h=0.0, title="Decision-relevance check on E-SYN records (N1, 50 campaigns per world)")
    md += ("\nSource: `python -m paperc.relevance_demo` (records of each world's tuned N1 from "
           "`esyn/ladder_table_v1.json`, instances 0–49; price g = N1's g; E2 margin against h = 0). On E-SYN the price "
           "is the tuned rule's own threshold, so E1 shares measure how many proposals sit near N1's cut, not a real run "
           "price. The E-SYN worlds were built with V* small next to sigma_node (about 0.05-0.4 sigma), unlike Track S's "
           "2.6-4.1 sigma at STOP 4, so most E1 decisions fall inside the bands: in sigma_node units these worlds are "
           "the opposite of the STOP 4 situation.\n")
    REPORT.write_text(md)
    return REPORT


if __name__ == "__main__":
    print(main())
