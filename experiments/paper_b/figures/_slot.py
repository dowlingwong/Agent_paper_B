"""Shared guard for Paper B figure slots.

Every figure in the B experimental plan is a *slot*: it names the generating
script and the dataset it requires.  Until a qualified dataset exists, a slot
refuses to run.  This is deliberate: a plausible-looking curve generated from
an unqualified workload would be fabricated evidence.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def require_dataset(script: str) -> int:
    parser = argparse.ArgumentParser(description=f"Paper B figure slot: {script}")
    parser.add_argument("--dataset", required=True, help="qualified B branch dataset directory")
    args = parser.parse_args()
    dataset = Path(args.dataset)
    if not dataset.is_dir():
        print(f"{script}: BLOCKED - no qualified dataset at {dataset}")
        print("This slot is PLANNED; it refuses to fabricate data. See the B contract.")
        return 2
    print(f"{script}: dataset {dataset} present; generation is not implemented in the draft.")
    print("Implement only against a qualified dataset with the frozen split manifest.")
    return 3
