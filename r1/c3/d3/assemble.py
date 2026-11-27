"""Assemble the G7 outcome table directly from G1 and G6 production output.

ENGINEERING code for task ``compute/20261127-23``.  It reads the per-campaign
``summary.json`` records G1 writes (the exact ``SUMMARY_KEYS`` shape) and the six-key
``g7_rows.jsonl`` records G6 writes, then calls G7's reviewed ``build_table``.  No fixture
summary or hand-supplied audit is accepted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from r1.c3 import d3_analysis as D3
from r1.c3 import d3_outcome_table as table


class AssembleStop(RuntimeError):
    """The production records are incomplete or ambiguous; nothing is written."""


def load_summaries(chunk_dirs: Iterable[str | Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for chunk in map(Path, chunk_dirs):
        if not (chunk / "campaigns").is_dir():
            raise AssembleStop(f"{chunk}: no campaigns/ directory")
        for path in sorted((chunk / "campaigns").glob("*/summary.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("schema") != table.SUMMARY_SCHEMA:
                raise AssembleStop(f"{path}: not a {table.SUMMARY_SCHEMA} summary")
            out.append(payload)
    if not out:
        raise AssembleStop("no campaign summaries found")
    return out


def load_audits(audit_dirs: Iterable[str | Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for audit in map(Path, audit_dirs):
        path = audit / "g7_rows.jsonl"
        if not path.is_file():
            raise AssembleStop(f"{path}: no G6 g7_rows.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    if not out:
        raise AssembleStop("no audit rows found")
    return out


def build(stage: str, chunk_dirs: Iterable[str | Path], audit_dirs: Iterable[str | Path], *,
          predeclaration_path: str | Path, d3b_note: str | Path | None = None,
          repetitions: int = D3.REPETITIONS,
          noise_summary_path: str | Path | None = None) -> dict[str, Any]:
    summaries = load_summaries(chunk_dirs)
    audits = load_audits(audit_dirs)
    return table.build_table(stage, summaries, audits, predeclaration_path=predeclaration_path,
                             d3b_note=d3b_note, repetitions=repetitions,
                             noise_summary_path=noise_summary_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D.3 G1/G6 -> G7 outcome table (ENGINEERING)")
    ap.add_argument("--stage", required=True, choices=list(D3.STAGES))
    ap.add_argument("--chunk", action="append", required=True)
    ap.add_argument("--audit", action="append", required=True)
    ap.add_argument("--predeclaration", required=True)
    ap.add_argument("--d3b-note", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    result = build(args.stage, args.chunk, args.audit, predeclaration_path=args.predeclaration,
                   d3b_note=args.d3b_note)
    out = table.write_table(result, args.out)
    print(json.dumps({"out": str(out), "rows": len(result["rows"]), "stage": result["stage"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
