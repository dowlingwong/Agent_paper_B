#!/usr/bin/env python3
"""Resolve the pinned Node for Pi exactly as a qualifying launch will (S6).

    python3 scripts/resolve_pinned_node.py [--candidate /path/to/node-or-its-dir]

Uses the adapter's own ``require_pinned_node`` (R5_PI_NODE / NODE_BIN, or the
registered ``~/.local/node-v22.19.0/bin/node``; never a PATH fallback; the
registered version only). ``--candidate`` is tried as R5_PI_NODE. Prints JSON
with the executable to record as the handoff input ``node_exe``.

Exit 0 = a pinned executable resolves; 3 = expected diagnostic refusal (absent,
PATH-only, or the wrong version) -- record it and stop before any Pi command.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "experiment_scaffold/src"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", default=None, help="a Node executable or its directory, tried as R5_PI_NODE")
    args = ap.parse_args(argv)
    from causal_branch.adapters.pi_agent import (  # noqa: PLC0415
        PINNED_NODE, PINNED_NODE_VERSION, node_provenance, require_pinned_node,
    )
    if args.candidate:
        os.environ["R5_PI_NODE"] = args.candidate
    report = {"registered_path": str(PINNED_NODE), "registered_version": PINNED_NODE_VERSION,
              "R5_PI_NODE": os.environ.get("R5_PI_NODE"), "NODE_BIN": os.environ.get("NODE_BIN")}
    try:
        node = require_pinned_node()
    except RuntimeError as exc:
        report.update(resolved=False, refusal=str(exc))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 3
    report.update(resolved=True, node_exe=os.path.realpath(node), provenance=node_provenance(node))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
