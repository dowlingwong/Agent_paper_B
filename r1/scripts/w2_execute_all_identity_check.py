"""W2 identity check (PLAN R1-SEQ-BUDGET-FIELDS): on execute-all ledgers the worker-run budget equals the trial index.

ENGINEERING_ONLY; AI-assisted (Claude). For each given ``root_trials.jsonl`` the
check recomputes, for every trial b, the worker runs consumed by rows 1..b-1
under ``r1.c3.features.row_worker_runs`` and compares it with b - 1, which is
what ``budget_frac_left`` and the serialized budget line used before W2. It
reads only ``budget_index``, ``decision``, ``worker_mode`` and ``extra.control``
of each row (no metric, delta, edit or label), refuses sealed paths before
opening, and prints one JSON summary.

Exit 0: identical on every ledger. Exit 3: a difference (STOP per W2: report it,
do not adopt the new fields on that table without the author); the summary names
the kinds of rows that do not count one run. Exit 2: bad input, including a
refused sealed path.

    python -m r1.scripts.w2_execute_all_identity_check <root_trials.jsonl[.gz]> [...] --runs-total W
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

FIELDS = ("budget_index", "decision", "worker_mode", "extra")


def _text(path: Path) -> str:
    return gzip.decompress(path.read_bytes()).decode() if path.name.endswith(".gz") else path.read_text()


def _kind(row: dict) -> str:
    mode = str(row.get("worker_mode"))
    control = row["extra"]["control"]
    if control.get("verify"):
        return "verify"
    if mode == "control_plane":
        return f"control_plane_skip({control.get('reason') or control.get('arm') or control.get('action')})"
    if mode.endswith("_precheck"):
        return "precheck_rejection"
    if row.get("worker_mode") is None:
        return "missing_worker_mode"
    return "worker_run"


def _rows(path: Path) -> list[dict]:
    out = []
    for line in _text(path).splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        extra = row.get("extra") or {}
        out.append({"budget_index": row.get("budget_index"), "decision": row.get("decision"),
                    "worker_mode": row.get("worker_mode"), "extra": {"control": extra.get("control") or {}}})
    return out


def check_ledger(path: Path, runs_total: int) -> dict:
    from r1.c3.features import row_worker_runs
    rows = sorted(_rows(path), key=lambda r: int(r["budget_index"]))
    used, diffs, kinds = 0, [], {}
    for r in rows:
        b = int(r["budget_index"])
        if used != b - 1:
            diffs.append({"budget_index": b, "trial_indexed_used": b - 1, "worker_runs_used": used})
        n = row_worker_runs(r)
        if n != 1:
            kinds[_kind(r)] = kinds.get(_kind(r), 0) + 1
        used += n
    return {"ledger": str(path), "rows": len(rows), "runs_total": runs_total, "differences": len(diffs),
            "first_difference": diffs[0] if diffs else None, "rows_not_counting_one": kinds,
            "worker_runs_total": used, "worker_runs_over_cap": used > runs_total}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledgers", nargs="+")
    ap.add_argument("--runs-total", type=int, required=True)
    args = ap.parse_args(argv)
    from r1.c3.analysis_guard import refuse_sealed
    paths = [Path(p) for p in args.ledgers]
    try:
        refuse_sealed(*paths)
        for p in paths:
            if p.name not in ("root_trials.jsonl", "root_trials.jsonl.gz") or not p.is_file():
                raise ValueError(f"not a root_trials.jsonl file: {p}")
        results = [check_ledger(p, args.runs_total) for p in paths]
    except (RuntimeError, ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BAD_INPUT", "error": str(exc)}))
        return 2
    bad = [r for r in results if r["differences"]]
    print(json.dumps({"status": "STOP_DIFFERENCE" if bad else "IDENTICAL", "ledgers": len(results),
                      "ledgers_with_differences": len(bad), "results": results}, indent=1))
    return 3 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
