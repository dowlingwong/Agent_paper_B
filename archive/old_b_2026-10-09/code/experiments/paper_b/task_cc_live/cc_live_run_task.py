#!/usr/bin/env python3
"""F8: run the live candidate-consistency task on CPU through the real fork path.

The session/workspace fork and tool calls are exercised with the existing toy
adapter's ``MockModelProvider`` (the sanctioned mock-provider mode).  The real
Pi runtime is not built or reachable here; that limitation is recorded, and no
model is called.  Output is ENGINEERING_ONLY.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from causal_branch.control.branch_tree import execute_tree_v2  # noqa: E402
from cc_live_generator import family_law_hash, generate_family  # noqa: E402
from cc_live_task import LiveCandidateTask  # noqa: E402
from cc_live_tools import tool_names  # noqa: E402

ENGINEERING_ONLY = "ENGINEERING_ONLY"
#: The vendored Pi runtime needs a Node build and a model endpoint; neither is
#: available under the offline CPU constraint.  The toy adapter's mock provider
#: is the closest real path and exercises the workspace/session fork.
PI_PATH_NOTE = (
    "real Pi adapter not exercised: it requires the built Node runtime and a "
    "model endpoint (offline CPU constraint); the toy adapter MockModelProvider "
    "path is used instead and no model is called"
)


def run(n_families: int, seed: int) -> dict:
    families = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i in range(n_families):
            family = generate_family(i, seed + i)
            _, tree = execute_tree_v2(
                LiveCandidateTask(family), root_id=f"live-{i}",
                template_family_id=f"live-family-{i}", split="engineering",
                seed=seed + i, branch_root=root / f"fam{i}", repetitions=2,
            )
            families.append({"family_id": i, "dataset": family["dataset"], "tree": tree})
    return {
        "banner": ENGINEERING_ONLY,
        "law_hash": family_law_hash(),
        "tools": tool_names(),
        "pi_path_note": PI_PATH_NOTE,
        "families": families,
        "now_best": sum(1 for f in families
                        if f["tree"]["now"] >= f["tree"]["later"] and f["tree"]["now"] >= f["tree"]["never"]),
        "later_best": sum(1 for f in families
                          if f["tree"]["later"] > f["tree"]["now"] and f["tree"]["later"] >= f["tree"]["never"]),
        "never_best": sum(1 for f in families
                          if f["tree"]["never"] > f["tree"]["now"] and f["tree"]["never"] > f["tree"]["later"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--families", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260927)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refuse overwrite: {output} exists")
    output.mkdir(parents=True)
    report = run(args.families, args.seed)
    (output / "live_task_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "LIVE_TASK_BANNER.txt").write_text(
        f"{ENGINEERING_ONLY}: mock-provider CPU task; no model call.\n", encoding="utf-8")
    print(f"task-cc-live: {ENGINEERING_ONLY} ({len(report['families'])} families)")
    print(f"  now-best={report['now_best']} later-best={report['later_best']} never-best={report['never_best']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
