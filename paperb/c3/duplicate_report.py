"""C1 duplicate-rate report from a C3 proposal table (PLAN §10, "Duplicates (22 Oct)"). AI-assisted (Claude).

Reads ``DIR/proposals.jsonl`` written by ``python -m r1.c3.dataset build`` and
reports, per source x node x memory mode (plus totals per memory mode and
overall):

- ``proposals``: evaluated proposals in the table (trial >= 2 with a parsed
  metric; trial 1 and invalid/skipped trials are not proposals of the table);
- ``noop_inactive_edit``: the edit changes only keys inactive for the node's
  model (Delta = 0);
- ``noop_incumbent_repeat``: the candidate's active configuration equals the
  incumbent's (Delta = 0), including literal no-changes
  (``noop_literal_no_change``, a subset);
- ``duplicate``: repeats an earlier evaluated non-incumbent active
  configuration of the same campaign (result known from the ledger);
- ``other``: everything else;
- fractions of ``proposals``, and the runs the rule-detectable kinds cost under
  the default rule rho, which executes every proposal: one run each, i.e.
  ``wasted_runs_rho`` = no-ops + duplicates, also per campaign.

The no-op kind comes from the table's ``noop_kind`` field (tables built after
22 Oct) or is derived from existing features (``arms.noop_kind``).

Usage:
  python -m r1.c3.duplicate_report --table DIR [--out DIR/duplicate_rate.json] [--md DIR/duplicate_rate.md]

The label (``--label``, default PILOT) is carried into both outputs.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from r1.c3.arms import is_duplicate, is_noop, noop_kind
from r1.c3.dataset import load_table

KINDS = ("noop_inactive_edit", "noop_incumbent_repeat", "duplicate", "other")


def kind(row: dict) -> str:
    if is_noop(row):
        return "noop_" + noop_kind(row)
    if is_duplicate(row):
        return "duplicate"
    return "other"


def _block(rows: list[dict]) -> dict:
    n = len(rows)
    c = defaultdict(int)
    campaigns = set()
    for r in rows:
        c[kind(r)] += 1
        campaigns.add((r["source"], r["instance"]))
        if is_noop(r) and r["features"].get("cfg_equals_incumbent"):
            c["noop_literal_no_change"] += 1
    noops = c["noop_inactive_edit"] + c["noop_incumbent_repeat"]
    wasted = noops + c["duplicate"]
    frac = (lambda x: x / n if n else None)
    return {"proposals": n, "campaigns": len(campaigns),
            **{k: c[k] for k in KINDS}, "noop_literal_no_change": c["noop_literal_no_change"], "noops": noops,
            "fractions": {"noop_inactive_edit": frac(c["noop_inactive_edit"]),
                          "noop_incumbent_repeat": frac(c["noop_incumbent_repeat"]),
                          "noops": frac(noops), "duplicate": frac(c["duplicate"]), "other": frac(c["other"]),
                          "noops_plus_duplicates": frac(wasted)},
            "wasted_runs_rho": wasted,
            "wasted_runs_rho_per_campaign": wasted / len(campaigns) if campaigns else None,
            "wasted_run_fraction_rho": frac(wasted)}


def report(rows: list[dict], label: str = "PILOT") -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["source"], r["node"], r["memory_mode"])].append(r)
    by_mode = defaultdict(list)
    for r in rows:
        by_mode[r["memory_mode"]].append(r)
    return {"label": label, "ai_assisted": "AI-assisted (Claude)",
            "definition": "Kinds per PLAN §10 'Duplicates (22 Oct)'. Under rho every proposal is executed and "
                          "costs one run; wasted runs = no-ops + duplicates (the runs the rule layer A2+ saves).",
            "groups": [{"source": s, "node": n, "memory_mode": m, **_block(g)}
                       for (s, n, m), g in sorted(groups.items())],
            "by_memory_mode": {m: _block(g) for m, g in sorted(by_mode.items())},
            "total": _block(rows)}


def _pct(x):
    return "NA" if x is None else f"{100 * x:.1f} %"


def markdown(rep: dict) -> str:
    lines = [f"| Source | Node | Memory | Campaigns | Proposals | No-op: inactive edit | No-op: incumbent repeat "
             "| Duplicate | Other | No-ops | Duplicates | Wasted runs under ρ (per campaign) |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]

    def row(s, n, m, b):
        f = b["fractions"]
        per = b["wasted_runs_rho_per_campaign"]
        return (f"| {s} | {n} | {m} | {b['campaigns']} | {b['proposals']} | {b['noop_inactive_edit']} "
                f"| {b['noop_incumbent_repeat']} | {b['duplicate']} | {b['other']} | {_pct(f['noops'])} "
                f"| {_pct(f['duplicate'])} | {b['wasted_runs_rho']} = {_pct(b['wasted_run_fraction_rho'])} "
                f"({'NA' if per is None else f'{per:.1f}'}) |")
    for g in rep["groups"]:
        lines.append(row(g["source"], g["node"], g["memory_mode"], g))
    for m, b in rep["by_memory_mode"].items():
        lines.append(row("**all**", "**all**", f"**{m}**", b))
    lines.append(row("**all**", "**all**", "**all**", rep["total"]))
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--md", default=None)
    ap.add_argument("--label", default="PILOT")
    args = ap.parse_args(argv)
    rows = load_table(Path(args.table))
    rep = report(rows, args.label)
    rep["table"] = str(args.table)
    out = Path(args.out) if args.out else Path(args.table) / "duplicate_rate.json"
    md = Path(args.md) if args.md else Path(args.table) / "duplicate_rate.md"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    md.write_text(f"{rep['label']}. AI-assisted (Claude). Table: `{args.table}`.\n\n" + markdown(rep))
    t = rep["total"]
    print(json.dumps({"proposals": t["proposals"], "noops": t["noops"], "duplicate": t["duplicate"],
                      "wasted_run_fraction_rho": t["wasted_run_fraction_rho"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
