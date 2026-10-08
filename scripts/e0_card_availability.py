#!/usr/bin/env python3
"""Is a candidate pair of cards free? Advisory, and by the SAME enumeration the lease uses.

WHAT THIS IS FOR. Every availability check before a launch -- an operator's
pre-flight, a wait-for-a-window watcher -- must ask the question the production
lease will ask, or it certifies a card the lease then refuses. On 2026-09-12
campaign 20260912a spent its only Stage A attempt doing exactly that: every poll
used `nvidia-smi --query-compute-apps`, which lists COMPUTE contexts only, and
reported card 3 idle while another tenant held three 6 MiB GRAPHICS contexts on
it. The launcher consumed the attempt, `acquire` exited 4 with
`foreign_compute_process:...`, and the attempt was gone.

So this uses `compute_pids_by_uuid` -- the same `nvidia-smi -q -x` enumeration
that `select_lease_devices` blocks on, covering C, G and C+G alike.

WHAT IT IS NOT. It is ADVISORY. Availability is a snapshot, not a reservation:
another tenant may take a card between this check and the lease. The production
lease remains the only authority on whether a card may be used, and Stage B's
progression reads the cards again at its own safe point. A clear result here is
a precondition for trying, never a licence to skip acquisition.

FAILS CLOSED. If the enumeration cannot be read, this refuses (exit 3) rather
than reporting cards free. Unknown is not idle.

Exit codes:
  0  every requested card is free of contexts of every type
  1  at least one requested card carries a context (it names them)
  3  the enumeration could not be read; availability is UNKNOWN
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "experiment_scaffold/src"))

EXIT_FREE = 0
EXIT_BUSY = 1
EXIT_UNKNOWN = 3


def survey(uuids: list[str]) -> dict[str, object]:
    """The production enumeration, per requested card. Raises on unreadable."""
    from causal_branch.round5_titan_stage_a_acquisition import (  # noqa: PLC0415
        GpuProcessQueryFailure, compute_pids_by_uuid,
    )
    try:
        table = compute_pids_by_uuid()
    except GpuProcessQueryFailure as exc:
        raise SystemExit(_unknown(f"the GPU process enumeration failed: {exc}"))

    missing = [u for u in uuids if u not in table]
    if missing:
        raise SystemExit(_unknown(
            f"the enumeration does not list {missing}; a card that cannot be "
            "enumerated is not a card that is known to be free"))

    cards = {u: sorted(int(p) for p in table[u]) for u in uuids}
    busy = {u: p for u, p in cards.items() if p}
    return {
        "schema": "e0-card-availability-1",
        "enumeration": ("causal_branch.round5_titan_stage_a_acquisition."
                        "compute_pids_by_uuid (nvidia-smi -q -x; C, G and C+G)"),
        "advisory": ("availability is a snapshot, not a reservation. The "
                     "production lease is the only authority; acquire and "
                     "verify it before using any card."),
        "requested": list(uuids),
        "contexts_by_uuid": cards,
        "free": not busy,
        "busy": busy,
    }


def _unknown(why: str) -> int:
    print(json.dumps({"schema": "e0-card-availability-1", "free": None,
                      "refused": why,
                      "reading": "UNKNOWN is not idle; this refuses rather "
                                 "than reporting the cards free"},
                     indent=2, sort_keys=True))
    return EXIT_UNKNOWN


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gpu-uuid", action="append", default=[], required=True,
                    metavar="UUID", help="a card to check; repeat per card")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    result = survey(list(dict.fromkeys(args.gpu_uuid)))
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return EXIT_FREE if result["free"] else EXIT_BUSY


if __name__ == "__main__":
    sys.exit(main())
