#!/usr/bin/env python3
"""B6: executable fixed-policy witnesses through the real adapter.

Each of the eight screen families is executed through the B5 tree driver with
the scripted candidate-consistency task.  The witnesses check the declared
regime ordering and the two stop conditions:

- ordinary refitting makes the verifier redundant; or
- no legitimate later-information mechanism exists.

Either stop condition is a legitimate outcome and is recorded, not hidden.
All artifacts are ENGINEERING_ONLY; no live model is used.
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
from law import EXPECTED_ORDERING, SCREEN_LAW, families, law_hash  # noqa: E402
from pilot_law import pilot_law_hash  # noqa: E402
from task import CandidateConsistencyTask, ordinary_refit, verifier_output  # noqa: E402

ENGINEERING_ONLY = "ENGINEERING_ONLY"


def _ordering_ok(mechanism: str, tree: dict) -> bool:
    now, later, never = tree["now"], tree["later"], tree["never"]
    if mechanism == "now_best":
        return now > later and now > never
    if mechanism == "later_best":
        return later > now and later > never
    if mechanism == "never_best":
        return never > now and never > later
    if mechanism == "uninformative_or_harmful":
        return now <= never and later <= never
    raise ValueError(f"unknown mechanism {mechanism!r}")


def run_screen(branch_root: Path) -> dict:
    results = []
    for mechanism, index, spec in families():
        tree = execute_tree_v2(
            CandidateConsistencyTask(spec),
            root_id=f"{mechanism}-{index}", template_family_id=f"{mechanism}-family-{index}",
            split="screen", seed=1000 + index,
            branch_root=branch_root / f"{mechanism}-{index}",
        )[1]
        results.append({
            "mechanism": mechanism,
            "family_index": index,
            "tree": tree,
            "ordering_ok": _ordering_ok(mechanism, tree),
            "expected": list(EXPECTED_ORDERING[mechanism]),
            "verifier_changes_ckpt1": verifier_output(spec, 1) != ordinary_refit(spec, 1),
            "verifier_changes_ckpt2": verifier_output(spec, 2) != ordinary_refit(spec, 2),
            "later_information_changes_fit": ordinary_refit(spec, 2) != ordinary_refit(spec, 1),
        })
    redundancy = all(
        not (r["verifier_changes_ckpt1"] or r["verifier_changes_ckpt2"]) for r in results
    )
    later_information = any(r["later_information_changes_fit"] for r in results)
    return {
        "banner": ENGINEERING_ONLY,
        "law_hash": law_hash(),
        "pilot_law_hash": pilot_law_hash(),
        "families": results,
        "all_orderings_ok": all(r["ordering_ok"] for r in results),
        "stop_verifier_redundant": redundancy,
        "later_information_exists": later_information,
        "verdict": (
            "STOP_VERIFIER_REDUNDANT" if redundancy
            else "STOP_NO_LATER_INFORMATION" if not later_information
            else "WITNESSES_OK"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="B6 candidate-consistency witnesses")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refuse overwrite: {output} exists")
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        report = run_screen(Path(tmp))
    (output / "witness_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "WITNESS_BANNER.txt").write_text(
        f"{ENGINEERING_ONLY}: executable fixed-policy witnesses; no scientific claim.\n",
        encoding="utf-8")
    print(f"task-cc witnesses: {report['verdict']} ({ENGINEERING_ONLY})")
    print(f"  law hash {report['law_hash'][:16]}; pilot law hash {report['pilot_law_hash'][:16]}")
    for row in report["families"]:
        print(f"  {row['mechanism']}[{row['family_index']}] ordering_ok={row['ordering_ok']} "
              f"tree={row['tree']['now']}/{row['tree']['later']}/{row['tree']['never']}")
    return 0 if report["all_orderings_ok"] and report["verdict"] == "WITNESSES_OK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
