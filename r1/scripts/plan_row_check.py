"""Check that an integration branch keeps every PLAN §10 row and STATUS entry of its sources.

MAC_LOCAL_RUNBOOK_20261104 M1 step 3. For each source ref:

* every table row of PLAN.md §10 (a line starting with ``|`` between the
  ``## 10.`` and ``## 11.`` headings, table separators excluded) must occur
  byte-identically in the result's §10, at least as many times as in the
  source;
* every other non-blank §10 line (headings, notes, bullets) likewise;
* every STATUS.md entry (a ``## `` section heading or a top-level ``- ``
  bullet together with its indented continuation lines) must occur
  byte-identically in the result's STATUS.md, with multiplicity.

A source row missing from the result is reported as ``MISSING``, unless
another source holds a different version of a row the merge-base also had
(``EDITED-BY:<ref>``): that is a later edit of the same line on another
source, which the three-way merge keeps; or unless a source that descends
from it holds a different version that the result keeps
(``SUPERSEDED-IN:<ref>``; the descendant edited its ancestor's line again).
Both tags show the replacing line's first 160 characters for review.  Rows
present only in the result (in no source) are listed as ``RESULT-ONLY``.

Usage::

    python r1/scripts/plan_row_check.py --result HEAD \
        --source origin/codex/coordinator-20261031 --source 13badb0 ...

Exit status 0 when nothing is MISSING, 1 otherwise.  Reads git objects only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter

PLAN = "docs/r1/PLAN.md"
STATUS = "docs/r1/STATUS.md"


def show(ref: str, path: str) -> str:
    return subprocess.run(["git", "show", f"{ref}:{path}"], check=True,
                          capture_output=True, text=True).stdout


def merge_base(a: str, b: str) -> str | None:
    r = subprocess.run(["git", "merge-base", a, b], capture_output=True, text=True)
    return r.stdout.strip() or None


def is_ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b]).returncode == 0


def plan_rows(text: str) -> list[str]:
    rows, inside = [], False
    for line in text.split("\n"):
        if line.startswith("## 10."):
            inside = True
            continue
        if inside and line.startswith("## 11."):
            break
        if inside and line.startswith("|") and not set(line) <= set("|-: "):
            rows.append(line)
    return rows


def plan_other_lines(text: str) -> list[str]:
    """Non-blank §10 lines that are not table rows: headings, notes, bullets."""
    lines, inside = [], False
    for line in text.split("\n"):
        if line.startswith("## 10."):
            inside = True
            continue
        if inside and line.startswith("## 11."):
            break
        if inside and line.strip() and not line.startswith("|"):
            lines.append(line)
    return lines


def status_entries(text: str) -> list[str]:
    entries, cur = [], None
    for line in text.split("\n"):
        top = line.startswith("## ") or line.startswith("- ")
        if top:
            if cur is not None:
                entries.append("\n".join(cur))
            cur = [line]
        elif cur is not None and line.startswith((" ", "\t", "|")) and cur[0].startswith("- "):
            cur.append(line)
        else:
            if cur is not None:
                entries.append("\n".join(cur))
            cur = None
    if cur is not None:
        entries.append("\n".join(cur))
    return entries


def key(row: str) -> str:
    """First cell of a table row (the decision id), or the first 60 characters of any other line."""
    if row.startswith("|"):
        return row.split("|")[1].strip()
    return row[:60]


def check(result: str, sources: list[str]) -> tuple[list[str], int]:
    out, missing = [], 0
    extract = {"PLAN §10": (PLAN, plan_rows), "PLAN §10 other lines": (PLAN, plan_other_lines),
               "STATUS": (STATUS, status_entries)}
    res = {kind: Counter(fn(show(result, path))) for kind, (path, fn) in extract.items()}
    src_sets = {kind: {} for kind in res}
    for kind, (path, fn) in extract.items():
        for s in sources:
            src_sets[kind][s] = Counter(fn(show(s, path)))
    for kind in res:
        out.append(f"## {kind}")
        union = Counter()
        for s in sources:
            union |= src_sets[kind][s]
            need = src_sets[kind][s]
            lost = need - res[kind]
            n_ok = sum(need.values()) - sum(lost.values())
            out.append(f"{s}: {sum(need.values())} items, {n_ok} present byte-identical")
            for row in sorted(lost):
                mb = merge_base(result, s)
                editors = []
                if mb is not None and kind.startswith("PLAN"):
                    base_rows = set(extract[kind][1](show(mb, PLAN)))
                    if row in base_rows:
                        # another source replaced this line, and its version is what the result holds
                        editors = [o for o in sources if o != s and row not in src_sets[kind][o]
                                   and any(key(r) == key(row) and r in res[kind]
                                           for r in src_sets[kind][o])]
                tag = f"EDITED-BY:{','.join(editors)}" if editors else "MISSING"
                if not editors and kind.startswith("PLAN"):
                    desc = [o for o in sources if o != s and is_ancestor(s, o) and row not in src_sets[kind][o]
                            and any(key(r) == key(row) and r in res[kind] for r in src_sets[kind][o])]
                    if desc:
                        tag = f"SUPERSEDED-IN:{','.join(desc)}"
                if tag == "MISSING":
                    missing += 1
                out.append(f"  {tag} x{lost[row]}: {row[:160]}")
                if tag != "MISSING":
                    for r in sorted(r for r in res[kind] if key(r) == key(row)):
                        out.append(f"    kept in result: {r[:160]}")
        extra = res[kind] - union
        out.append(f"RESULT-ONLY: {sum(extra.values())}")
        for row in sorted(extra):
            out.append(f"  RESULT-ONLY x{extra[row]}: {row[:160]}")
    out.append(f"MISSING total: {missing}")
    return out, missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--result", default="HEAD")
    ap.add_argument("--source", action="append", required=True)
    a = ap.parse_args(argv)
    lines, missing = check(a.result, a.source)
    print("\n".join(lines))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
