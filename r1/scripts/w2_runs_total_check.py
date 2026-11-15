"""W2-3 (author, 14 Nov): every Track P source ledger made exactly W worker runs, before the c3_features/v3 rebuild.

ENGINEERING_ONLY; AI-assisted (Claude). The stop-rule report (``docs/r1/reports/W2_STOP_RULE_20261114.md``) recommends
the worker-run budget feature only under one precondition: every sweep ledger has ``worker_runs_total == 20``. A
campaign that hit the 2W trial cap with fewer worker runs would make the worker-runs-left feature show runs it could
no longer use. This check reads that number and STOPs on any ledger that differs.

Two inputs, either or both:

* ``--summary <file>``: the JSON printed by ``r1.scripts.w2_execute_all_identity_check`` (already produced on the
  cluster for sweep 1; no new data access). Each result's ``worker_runs_total`` and ``runs_total`` are read.
* ledgers (``root_trials.jsonl[.gz]``): recomputed here with the same ``check_ledger`` (it reads only
  ``budget_index``, ``decision``, ``worker_mode`` and ``extra.control``; sealed paths are refused before opening).

Exit 0 PASS (every ledger has exactly W worker runs); exit 3 STOP (a ledger differs; report it to the author, do not
rebuild that table); exit 2 bad input.

    python -m r1.scripts.w2_runs_total_check --runs-total 20 [--summary identity_check.json] [root_trials.jsonl ...]
"""
from __future__ import annotations

import argparse
import json
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
        for key in ("rows", "runs_total", "worker_runs_total"):
            if type(r.get(key)) is not int:
                raise ValueError(f"{path}: {r.get('ledger')}: {key} is not an integer")
        if r["runs_total"] != runs_total:
            raise ValueError(f"{path}: {r['ledger']}: the summary was made with runs_total {r['runs_total']}, not {runs_total}")
        out.append({"ledger": r["ledger"], "rows": r["rows"], "worker_runs_total": r["worker_runs_total"], "source": str(path)})
    return out


def evaluate(results: list[dict], runs_total: int) -> dict:
    paths = [r["ledger"] for r in results]
    dup = sorted({p for p in paths if paths.count(p) > 1})
    if dup:
        raise ValueError(f"ledger listed more than once: {dup[:3]}")
    bad = []
    for r in results:
        n, rows = r["worker_runs_total"], r["rows"]
        if n == runs_total:
            continue
        if n < runs_total:
            kind = "short_at_trial_cap" if rows >= 2 * runs_total else "short_before_trial_cap"
        else:
            kind = "over_cap"
        bad.append({**r, "kind": kind})
    kinds = {}
    for b in bad:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    return {"status": "STOP" if bad else "PASS", "check": "W2-3 worker_runs_total == runs_total",
            "runs_total": runs_total, "ledgers": len(results), "ledgers_differing": len(bad), "by_kind": kinds,
            "differing": bad}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledgers", nargs="*")
    ap.add_argument("--summary", action="append", default=[])
    ap.add_argument("--runs-total", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        if args.runs_total < 1:
            raise ValueError("runs_total must be positive")
        if not args.ledgers and not args.summary:
            raise ValueError("give --summary and/or ledgers")
        results = []
        for s in args.summary:
            results += _results_from_summary(Path(s), args.runs_total)
        if args.ledgers:
            from r1.c3.analysis_guard import refuse_sealed
            from r1.scripts.w2_execute_all_identity_check import check_ledger
            paths = [Path(p) for p in args.ledgers]
            refuse_sealed(*paths)
            for p in paths:
                if p.name not in ("root_trials.jsonl", "root_trials.jsonl.gz") or not p.is_file():
                    raise ValueError(f"not a root_trials.jsonl file: {p}")
            for p in paths:
                r = check_ledger(p, args.runs_total)
                results.append({"ledger": r["ledger"], "rows": r["rows"], "worker_runs_total": r["worker_runs_total"],
                                "source": "recomputed"})
        out = evaluate(results, args.runs_total)
    except (RuntimeError, ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BAD_INPUT", "error": str(exc)}))
        return 2
    print(json.dumps(out, indent=1))
    return 3 if out["status"] == "STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
