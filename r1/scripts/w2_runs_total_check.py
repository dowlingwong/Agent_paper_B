"""W2-3 (author, 14 Nov): every Track P source ledger made exactly W worker runs, before the c3_features/v3 rebuild.

ENGINEERING_ONLY; AI-assisted (Claude). The stop-rule report (``docs/r1/reports/W2_STOP_RULE_20261114.md``) recommends
the worker-run budget feature only under one precondition: every sweep ledger has ``worker_runs_total == 20``. A
campaign that hit the trial cap (2W on sweep 1: ``e1b_collect`` passes ``budget = runs * 2``) with fewer worker runs
would make the worker-runs-left feature show runs it could no longer use. This check reads that number.

**The STOP is proposed, not in force.** Exit 3 marks a ledger that would STOP under the proposed W2-3 rule. Adopting
that rule as a STOP of the rebuild is a separate author decision; until then exit 3 is a report to the author.

Two inputs, either or both, and the expected number of ledgers (``--expect-ledgers``; 288 for sweep 1), so that a
partial set cannot pass:

* ``--summary <file>``: the JSON printed by ``r1.scripts.w2_execute_all_identity_check`` (already produced on the
  cluster for sweep 1; no new data access). Each result's ``rows``, ``runs_total``, ``worker_runs_total``,
  ``differences`` and ``rows_not_counting_one`` are read.
* ledgers (``root_trials.jsonl[.gz]``): recomputed here with the same ``check_ledger`` (it reads only
  ``budget_index``, ``decision``, ``worker_mode`` and ``extra.control``). This path also checks that
  ``budget_index`` runs 1..rows and that no row follows the row that used the W-th worker run.

``r1_sealed`` paths (summaries and ledgers) are refused before opening.

Exit 0 PASS; exit 3 proposed STOP (a ledger differs); exit 2 bad input (including a wrong ledger count).

    python -m r1.scripts.w2_runs_total_check --runs-total 20 --expect-ledgers 288 [--summary identity_check.json] [root_trials.jsonl ...]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _results_from_summary(path: Path, runs_total: int) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("status") not in ("IDENTICAL", "STOP_DIFFERENCE"):
        raise ValueError(f"{path}: not a w2_execute_all_identity_check summary")
    results = data.get("results")
    if not isinstance(results, list) or data.get("ledgers") != len(results) or not results:
        raise ValueError(f"{path}: ledger count differs from its results")
    out = []
    for r in results:
        if not isinstance(r, dict) or not isinstance(r.get("ledger"), str):
            raise ValueError(f"{path}: result without a ledger path")
        for key in ("rows", "runs_total", "worker_runs_total", "differences"):
            if type(r.get(key)) is not int:
                raise ValueError(f"{path}: {r.get('ledger')}: {key} is not an integer")
        if r["runs_total"] != runs_total:
            raise ValueError(f"{path}: {r['ledger']}: the summary was made with runs_total {r['runs_total']}, not {runs_total}")
        if r["differences"] and not r.get("rows_not_counting_one"):
            raise ValueError(f"{path}: {r['ledger']}: differences without rows that count other than one run "
                             "(duplicated or missing budget indices?)")
        out.append({"ledger": os.path.normpath(r["ledger"]), "rows": r["rows"], "worker_runs_total": r["worker_runs_total"],
                    "source": str(path)})
    return out


def _recompute(path: Path, runs_total: int) -> dict:
    from r1.c3.features import row_worker_runs
    from r1.scripts.w2_execute_all_identity_check import _rows, check_ledger
    r = check_ledger(path, runs_total)
    rows = sorted(_rows(path), key=lambda x: int(x["budget_index"]))
    if [int(x["budget_index"]) for x in rows] != list(range(1, len(rows) + 1)):
        raise ValueError(f"{path}: budget_index does not run 1..{len(rows)}")
    used, after_cap = 0, 0
    for x in rows:
        if used >= runs_total:
            after_cap += 1
        used += row_worker_runs(x)
    return {"ledger": str(path.resolve()), "rows": r["rows"], "worker_runs_total": r["worker_runs_total"],
            "rows_after_cap": after_cap, "source": "recomputed"}


def evaluate(results: list[dict], runs_total: int, trial_budget: int) -> dict:
    paths = [r["ledger"] for r in results]
    dup = sorted({p for p in paths if paths.count(p) > 1})
    if dup:
        raise ValueError(f"ledger listed more than once: {dup[:3]}")
    bad = []
    for r in results:
        n, rows = r["worker_runs_total"], r["rows"]
        if rows > trial_budget:
            kind = "rows_over_trial_budget"
        elif n == runs_total and not r.get("rows_after_cap"):
            continue
        elif n == runs_total:
            kind = "rows_after_cap"
        elif n < runs_total:
            kind = "short_at_trial_cap" if rows == trial_budget else "short_before_trial_cap"
        else:
            kind = "over_cap"
        bad.append({**r, "kind": kind})
    kinds = {}
    for b in bad:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    return {"status": "STOP" if bad else "PASS", "stop_rule": "proposed (adoption is a separate author decision)",
            "check": "W2-3 worker_runs_total == runs_total", "runs_total": runs_total, "trial_budget": trial_budget,
            "ledgers": len(results), "ledgers_differing": len(bad), "by_kind": kinds, "differing": bad}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledgers", nargs="*")
    ap.add_argument("--summary", action="append", default=[])
    ap.add_argument("--runs-total", type=int, required=True)
    ap.add_argument("--expect-ledgers", type=int, required=True)
    ap.add_argument("--trial-budget", type=int, default=None, help="trial cap per campaign (default 2 x runs-total, sweep 1)")
    args = ap.parse_args(argv)
    try:
        if args.runs_total < 1 or args.expect_ledgers < 1:
            raise ValueError("runs_total and expect_ledgers must be positive")
        trial_budget = args.trial_budget if args.trial_budget is not None else 2 * args.runs_total
        if not args.ledgers and not args.summary:
            raise ValueError("give --summary and/or ledgers")
        from r1.c3.analysis_guard import refuse_sealed
        refuse_sealed(*[Path(s) for s in args.summary], *[Path(p) for p in args.ledgers])
        results = []
        for s in args.summary:
            results += _results_from_summary(Path(s), args.runs_total)
        for p in [Path(x) for x in args.ledgers]:
            if p.name not in ("root_trials.jsonl", "root_trials.jsonl.gz") or not p.is_file():
                raise ValueError(f"not a root_trials.jsonl file: {p}")
            results.append(_recompute(p, args.runs_total))
        out = evaluate(results, args.runs_total, trial_budget)
        if out["ledgers"] != args.expect_ledgers:
            raise ValueError(f"{out['ledgers']} ledgers given, {args.expect_ledgers} expected: the set is incomplete or too large")
    except (RuntimeError, ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BAD_INPUT", "error": str(exc)}))
        return 2
    print(json.dumps(out, indent=1))
    return 3 if out["status"] == "STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
