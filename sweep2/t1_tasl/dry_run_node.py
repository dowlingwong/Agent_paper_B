#!/usr/bin/env python3
"""ENGINEERING dry-run: one default part of one G.1b node, no signed note and no EVIDENCE.

This wrapper does not change the reviewed runner. It runs the pinned run_node_job (lease, delegated scope, preflight,
engine invocation) but restricts g1b_lib.PARTS to the default part and merges the partial rows, so a dry-run exercises
lease/scope/preflight/timeout/seal without spending the full 460-run node. It must never be used for a G.1b row.

R1-TASL2-CPU check runs (local/20261126-01): under the derived spec of ``g5_tasl.py cpuset-spec`` (a ``cpuset_check``
block for this node and run id ``tasl2-cpuset-<node>-<YYYYMMDD>``) the check needs ``CHECK_REPEATS`` complete attempts
of the node in that one run, which G.1b's ``next_attempt`` refuses after the first (one attempt per node per run). For
such a spec only, the attempt directory comes from ``check_next_attempt``: a new attempt while fewer than
``CHECK_REPEATS`` complete attempts exist, an infrastructure STOP retried as in G.1b, and a refusal after a node or
timing STOP, a missing job record, any other stop class, or the ``CHECK_REPEATS``-th complete attempt. Every other spec
runs with G.1b's ``next_attempt`` unchanged.
"""
import json
import os
import re
import shutil
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g1b_lib as L  # noqa: E402

# The same values as g5_tasl.TASL2_CPU_ROW, CPUSET_RUN and CPUSET_REPEATS (a test keeps them equal); not imported, so
# the dry run loads nothing beyond the G.1b runner.
CHECK_RULE = "R1-TASL2-CPU"
CHECK_RUN = re.compile(r"^tasl2-cpuset-(?P<node>[a-z0-9_]+)-\d{8}$")
CHECK_REPEATS = 3


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


def is_cpuset_check(spec: dict, node: str) -> bool:
    """True for the derived spec of this node's R1-TASL2-CPU check; False for a spec without a ``cpuset_check`` block.
    A block that does not name this node and the rule, or a run id that is not this node's check run, is refused."""
    if "cpuset_check" not in spec:
        return False
    c = spec["cpuset_check"]
    m = CHECK_RUN.fullmatch(str(spec.get("run_id")))
    if not isinstance(c, dict) or c.get("rule") != CHECK_RULE or c.get("node") != node or not m or \
            m.group("node") != node:
        raise G.Stop(f"STOP: the spec carries a cpuset_check block but is not {node}'s {CHECK_RULE} check spec "
                     f"(rule {CHECK_RULE}, node {node}, run id tasl2-cpuset-{node}-<YYYYMMDD>)")
    return True


def check_next_attempt(node_root: Path) -> tuple[int, Path]:
    """The next attempt directory of a check run, created as G.1b's ``next_attempt`` creates it (``attempt-N`` and its
    ``attempt.json``). Refused when an earlier attempt has no job record, ended in a node or timing STOP or any stop
    class other than None and "infrastructure", or when ``CHECK_REPEATS`` complete attempts (stop_class None) exist."""
    done = G.attempts(node_root)
    complete = 0
    for _n, p in done:
        rec_path = p / "job_record.json"
        if not rec_path.is_file():
            raise G.Stop(f"STOP: {p} has no job record; inspect it before another attempt")
        stop_class = json.loads(rec_path.read_text()).get("stop_class")
        if stop_class is None:
            complete += 1
        elif stop_class != "infrastructure":
            raise G.Stop(f"STOP: {p} ended with stop_class {stop_class!r}; no new attempt of this check "
                         "(only an infrastructure STOP may be retried)")
    if complete >= CHECK_REPEATS:
        raise G.Stop(f"STOP: {node_root} holds {complete} complete attempts, the check's {CHECK_REPEATS}; "
                     "no further attempt")
    n = (done[-1][0] + 1) if done else 1
    path = Path(node_root) / f"attempt-{n}"
    path.mkdir(parents=True, exist_ok=False)
    with (path / "attempt.json").open("x") as fh:     # who owns the attempt, for close-attempt
        fh.write(json.dumps({"attempt": n, "pid": os.getpid(), "hostname": socket.gethostname(),
                             "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
    return n, path


def main() -> int:
    spec_path, node = Path(sys.argv[1]), sys.argv[2]
    if is_cpuset_check(G.load_spec(spec_path), node):
        G.next_attempt = check_next_attempt          # run_node_job looks it up in G's namespace at the call
    L.PARTS = (L.PARTS[0],)          # one default part only (10 rows: default + repeat)
    L.merge_parts = partial_merge
    rec = G.run_node_job(spec_path, node)
    print(json.dumps({"ok": True, "node": node, "runs": rec.get("runs"), "parts": rec.get("parts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
