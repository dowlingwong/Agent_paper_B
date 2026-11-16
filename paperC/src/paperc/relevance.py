"""Decision-relevance check on ``spt_transition/v1`` records (build runbook P5; BUILD_LIST B10; plan addendum §B.3).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

Paper B's Track S stopped at STOP 4 because no E1 decision was near its threshold: V* - g lay 2.6-4.1 sigma above
the price everywhere, so every eligible proposal was executed and every E1 skip was a rule duplicate. Before any
sequential-policy collection, this module measures, per node, how many logged decisions are close enough to their
threshold for a different policy to change them:

* **E1** (eligible rows: epoch E1, not rule-forced): the share of rows with |V* - g| <= b sigma_node for the declared
  bands b (default 0.25, 0.5, 1.0), and the distribution of (V* - g) / sigma_node;
* **E2** (eligible rows: epoch E2, not rule-forced): the same for the keep margin |m_hat - h| (h = 0 by default, the
  Bayes keep);
* the **rule-skip share** of E1 rows (rule-forced skips over all E1 rows) and its breakdown by rule.

An epoch is reported as having **no decision-relevant states** when none of its eligible rows lies within the widest
band (or it has no eligible rows). The share that would gate SPT-2 is **not** set here: it is a proposal for the
author (runbook P5).

Inputs per row (dicts as written by ``schema.to_dict``, or ``Transition`` objects): ``identity.node``,
``identity.epoch``, ``state.rule_forced``, ``state.sigma_node``, ``state.forecasts[<belief>].v_star`` / ``m_hat`` /
``g``, ``action.rule``. The price g is taken, in this order, from the ``g`` argument (a number, or a mapping
node -> number), the forecast's ``g`` field, or ``env.constants["g"]``; a node with E1 rows and no price is an error.
``validate=True`` first runs ``schema.check_campaign`` on the rows and refuses invalid input.

CLI: ``python -m paperc.relevance rows.jsonl [more.jsonl ...] --out report.md [--g 0.001 | --g-json prices.json]
[--belief a2u] [--h 0] [--bands 0.25,0.5,1.0] [--no-validate]``.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from paperc import schema as S

BANDS = (0.25, 0.5, 1.0)
QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)


class RelevanceInputError(ValueError):
    pass


def _row(r) -> dict:
    return S.to_dict(r) if isinstance(r, S.Transition) else r


@dataclass
class EpochSummary:
    n_eligible: int = 0
    shares: dict = field(default_factory=dict)        # band -> share within the band
    counts: dict = field(default_factory=dict)        # band -> count within the band
    quantiles: dict = field(default_factory=dict)     # quantile -> standardised distance (signed)
    relevant: bool = False

    def to_dict(self) -> dict:
        return {"n_eligible": self.n_eligible, "shares": {str(k): v for k, v in self.shares.items()},
                "counts": {str(k): v for k, v in self.counts.items()},
                "quantiles": {str(k): v for k, v in self.quantiles.items()}, "relevant": self.relevant}


@dataclass
class NodeSummary:
    node: str
    price: float | str | None
    e1: EpochSummary
    e2: EpochSummary
    n_e1_rows: int
    rule_skip_share: float | None
    rule_skips: dict

    def verdict(self) -> list[str]:
        out = []
        for name, ep in (("E1", self.e1), ("E2", self.e2)):
            if not ep.relevant:
                out.append(f"{name}: no decision-relevant states ({ep.counts.get(max(ep.counts, default=1.0), 0)} "
                           f"of {ep.n_eligible} eligible rows within the widest band)")
            else:
                widest = max(ep.shares)
                out.append(f"{name}: {ep.shares[widest]:.1%} of {ep.n_eligible} eligible rows within {widest} sigma")
        return out

    def to_dict(self) -> dict:
        return {"node": self.node, "price": self.price, "E1": self.e1.to_dict(), "E2": self.e2.to_dict(),
                "n_e1_rows": self.n_e1_rows, "rule_skip_share": self.rule_skip_share, "rule_skips": self.rule_skips,
                "verdict": self.verdict()}


def _summarise(z: np.ndarray, bands) -> EpochSummary:
    s = EpochSummary(n_eligible=int(len(z)))
    for b in bands:
        c = int(np.sum(np.abs(z) <= b)) if len(z) else 0
        s.counts[b] = c
        s.shares[b] = c / len(z) if len(z) else 0.0
    if len(z):
        s.quantiles = {q: float(np.quantile(z, q)) for q in QUANTILES}
    s.relevant = bool(len(z)) and s.counts[max(bands)] > 0
    return s


def relevance(rows: Iterable, *, g: float | Mapping[str, float] | None = None, belief: str = "a2u", h: float = 0.0,
              bands=BANDS, validate: bool = False) -> dict[str, NodeSummary]:
    rows = [_row(r) for r in rows]
    if validate:
        v = S.check_campaign(rows)
        if v:
            raise RelevanceInputError(f"{len(v)} schema violations, first: {v[0]}")
    bands = tuple(sorted(float(b) for b in bands))
    by_node: dict[str, list] = defaultdict(list)
    for r in rows:
        by_node[r["identity"]["node"]].append(r)
    out = {}
    for node, rs in sorted(by_node.items()):
        arg = g.get(node) if isinstance(g, Mapping) else g
        z1, z2, skips, n_e1, prices = [], [], Counter(), 0, set()
        for r in rs:
            ep, st = r["identity"]["epoch"], r["state"]
            if ep == "E1":
                n_e1 += 1
            if st["rule_forced"]:
                if ep == "E1" and r["action"]["action"] == "skip":
                    skips[r["action"]["rule"]] += 1
                continue
            sig = st.get("sigma_node")
            f = (st.get("forecasts") or {}).get(belief)
            if ep not in ("E1", "E2"):
                continue
            if f is None or not sig or sig <= 0:
                raise RelevanceInputError(f"{node}: an eligible {ep} row lacks the '{belief}' forecast or sigma_node")
            if ep == "E1":
                p = arg if arg is not None else f.get("g")
                if p is None:
                    p = (r.get("env") or {}).get("constants", {}).get("g")
                if p is None:
                    raise RelevanceInputError(f"{node}: no price g for E1 rows (argument, forecast or env constant)")
                prices.add(float(p))
                if f.get("v_star") is None:
                    raise RelevanceInputError(f"{node}: an eligible E1 row has no v_star")
                z1.append((f["v_star"] - float(p)) / sig)
            else:
                if f.get("m_hat") is None:
                    raise RelevanceInputError(f"{node}: an eligible E2 row has no m_hat")
                z2.append((f["m_hat"] - h) / sig)
        price = next(iter(prices)) if len(prices) == 1 else (None if not prices else "varies")
        out[node] = NodeSummary(node=node, price=price, e1=_summarise(np.array(z1), bands),
                                e2=_summarise(np.array(z2), bands), n_e1_rows=n_e1,
                                rule_skip_share=(sum(skips.values()) / n_e1) if n_e1 else None,
                                rule_skips=dict(skips))
    return out


def markdown(summary: dict[str, NodeSummary], *, belief: str, h: float, bands=BANDS, title: str | None = None) -> str:
    bands = tuple(sorted(bands))
    lines = [f"# {title or 'Decision-relevance check'}", "",
             f"ENGINEERING_ONLY. Generated by `paperc.relevance` (build runbook P5). Belief `{belief}`; E2 margin "
             f"m_hat - {h:g}; distances in sigma_node. The share that would gate SPT-2 is not set here.", ""]
    head = "| Node | Epoch | Eligible rows | " + " | ".join(f"within {b} σ" for b in bands) + \
        " | min | 5 % | median | 95 % | max |"
    lines += [head, "|" + "---|" * (head.count("|") - 1)]
    for node, s in summary.items():
        for name, ep in (("E1 (V\\* − g)", s.e1), ("E2 (m̂ − h)", s.e2)):
            qs = [ep.quantiles.get(q) for q in (0.0, 0.05, 0.5, 0.95, 1.0)]
            qtxt = " | ".join("—" if q is None else f"{q:+.2f}" for q in qs)
            share = " | ".join(f"{ep.shares[b]:.1%} ({ep.counts[b]})" for b in bands)
            lines.append(f"| {node} | {name} | {ep.n_eligible} | {share} | {qtxt} |")
    lines += ["", "| Node | Price g | E1 rows | Rule-skip share | Rule skips by rule | Verdict |", "|---|---|---|---|---|---|"]
    for node, s in summary.items():
        rs = "—" if s.rule_skip_share is None else f"{s.rule_skip_share:.1%}"
        lines.append(f"| {node} | {s.price if s.price is not None else '—'} | {s.n_e1_rows} | {rs} | "
                     f"{', '.join(f'{k}: {v}' for k, v in sorted(s.rule_skips.items())) or '—'} | "
                     f"{'; '.join(s.verdict())} |")
    return "\n".join(lines) + "\n"


def _read(paths) -> list[dict]:
    rows = []
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Decision-relevance check on spt_transition/v1 records (P5).")
    ap.add_argument("rows", nargs="+", help="JSONL files of spt_transition/v1 rows")
    ap.add_argument("--out", required=True, help="markdown report to write")
    ap.add_argument("--json", help="also write the summary as JSON")
    ap.add_argument("--g", type=float, help="run price g (raw units) for every node")
    ap.add_argument("--g-json", help="JSON file mapping node -> price g")
    ap.add_argument("--belief", default="a2u")
    ap.add_argument("--h", type=float, default=0.0, help="E2 keep threshold for the margin (default 0)")
    ap.add_argument("--bands", default=",".join(map(str, BANDS)))
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--title")
    a = ap.parse_args(argv)
    g = json.loads(Path(a.g_json).read_text()) if a.g_json else a.g
    bands = tuple(float(x) for x in a.bands.split(","))
    summ = relevance(_read(a.rows), g=g, belief=a.belief, h=a.h, bands=bands, validate=not a.no_validate)
    Path(a.out).write_text(markdown(summ, belief=a.belief, h=a.h, bands=bands, title=a.title))
    if a.json:
        Path(a.json).write_text(json.dumps({k: v.to_dict() for k, v in summ.items()}, indent=1) + "\n")
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
