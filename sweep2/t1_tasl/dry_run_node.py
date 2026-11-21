#!/usr/bin/env python3
"""ENGINEERING dry-run: one default part of one G.1b node, no signed note and no EVIDENCE.

This wrapper does not change the reviewed runner. It runs the pinned run_node_job (lease, delegated scope, preflight,
engine invocation) but restricts g1b_lib.PARTS to the default part and merges the partial rows, so a dry-run exercises
lease/scope/preflight/timeout/seal without spending the full 460-run node. It must never be used for a G.1b row.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g1b_lib as L  # noqa: E402


def partial_merge(out: Path, node: dict) -> dict:
    rows = [r for p in L.PARTS for r in L._rows(out / p[0] / "runs.jsonl")]
    for row in rows:
        L.check_row_gate(row)
    with (out / "runs.jsonl").open("x") as fh:
        fh.writelines(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    shutil.copy2(out / "default" / "edits.json", out / "edits.json")
    return {"expected": len(rows), "written": len(rows),
            "successful": sum(1 for r in rows if r["success"]),
            "divergent": sum(1 for r in rows if not r["success"]),
            "dry_run_partial": True}


def main() -> int:
    spec_path, node = Path(sys.argv[1]), sys.argv[2]
    L.PARTS = (L.PARTS[0],)          # one default part only (10 rows: default + repeat)
    L.merge_parts = partial_merge
    rec = G.run_node_job(spec_path, node)
    print(json.dumps({"ok": True, "node": node, "runs": rec.get("runs"), "parts": rec.get("parts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
