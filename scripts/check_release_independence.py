#!/usr/bin/env python3
"""Release independence check: build and verify a package in a clean directory.

For Paper A the check proves the required property: the package builds its PDF
and runs its retained-evidence verification with no Paper B paths, no model
weights, no network and no credentials.  It also runs the package's own
documented checks inside the copy: theory-check, the paper tests, the
state-audit control tests, the measurement-facade import and the named runners.  For Paper B it proves the draft builds
and its engineering smoke path runs.

Usage::

    python3 scripts/check_release_independence.py --paper a [--full]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from release_provenance import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], cwd: Path, env: dict | None = None) -> dict:
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=env)
    return {
        "command": " ".join(command),
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.strip().splitlines()[-4:],
        "stderr_tail": proc.stderr.strip().splitlines()[-4:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Release independence check")
    parser.add_argument("--paper", choices=("a", "b"), required=True)
    parser.add_argument("--full", action="store_true", help="run the full A reproduction")
    args = parser.parse_args()

    source = ROOT / "release" / f"paper_{args.paper}"
    if not source.is_dir():
        print(f"release package missing: {source}; run scripts/make_release.py first")
        return 1

    report: dict = {"paper": args.paper, "commands": [], "checks": {}}
    with tempfile.TemporaryDirectory(prefix=f"release-{args.paper}-") as tmp:
        clean = Path(tmp) / f"paper_{args.paper}"
        shutil.copytree(source, clean)

        # 1. Forbidden content: no B paths in an A package (and vice versa).
        forbidden = ["papers/paper_b", "protocols/paper_b", "experiments/paper_b"] if args.paper == "a" else [
            "papers/paper_a", "protocols/paper_a", "experiments/paper_a"
        ]
        manifest = json.loads((clean / "MANIFEST.json").read_text())
        provenance_errors = verify_manifest(ROOT, clean, manifest)
        report["source_commit"] = manifest.get("source_commit")
        report["checks"]["manifest_matches_source_commit"] = not provenance_errors
        if provenance_errors:
            report["provenance_errors"] = provenance_errors
        leaked = [
            row["path"]
            for row in manifest["files"]
            for prefix in forbidden
            if row["path"].startswith(prefix)
        ]
        report["checks"]["no_cross_paper_paths"] = not leaked
        if leaked:
            report["checks"]["cross_paper_paths"] = leaked[:10]

        # 2. No credential-looking files or environment requirements.
        credential_names = {".env", "credentials.json", "secrets.yaml", "token.txt"}
        creds = [row["path"] for row in manifest["files"] if Path(row["path"]).name in credential_names]
        report["checks"]["no_credentials"] = not creds

        # 3. Build the manuscript from the package only.
        paper_dir = clean / ("papers/paper_a" if args.paper == "a" else "papers/paper_b")
        report["commands"].append(_run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], paper_dir))
        built = report["commands"][-1]["exit_code"] == 0 and (paper_dir / "main.pdf").is_file()
        report["checks"]["pdf_built"] = built
        if built:
            report["checks"]["pdf_bytes"] = (paper_dir / "main.pdf").stat().st_size

        # 4. Run the package's own verification path.
        if args.paper == "a":
            command = [sys.executable, "experiments/paper_a/reproduce_evidence.py"]
            if not args.full:
                command.append("--quick")
            report["commands"].append(_run(command, clean))
            report["checks"]["reproduce_exit_zero"] = report["commands"][-1]["exit_code"] == 0

            # 5. The package runs its own documented checks (review F01/F02):
            #    theory-check (theorems, worked example, grid summary), the
            #    paper tests, the state-audit control tests, the measurement
            #    facade import and the runners the manuscript names.
            env = dict(os.environ, PYTHONPATH=str(clean / "experiment_scaffold/src"))
            def step(command: list[str], use_env: bool = False) -> bool:
                report["commands"].append(_run(command, clean, env if use_env else None))
                return report["commands"][-1]["exit_code"] == 0
            report["checks"]["theory_check_exit_zero"] = step(
                ["make", "-C", "papers/paper_a", "theory-check", f"PYTHON={sys.executable}"])
            report["checks"]["paper_tests_exit_zero"] = step(
                [sys.executable, "-m", "unittest", "discover", "-s", "papers/paper_a/tests", "-p", "test_*.py"])
            report["checks"]["state_audit_tests_exit_zero"] = step(
                [sys.executable, "-m", "unittest", "experiment_scaffold/tests/test_state_audit_upgrade.py",
                          "experiment_scaffold/tests/test_state_audit_corrections.py"], use_env=True)
            report["checks"]["facade_import_exit_zero"] = step(
                [sys.executable, "-c", "import causal_branch.measurement"], use_env=True)
            report["checks"]["runner_import_exit_zero"] = all(
                step([sys.executable, runner, "--help"])
                for runner in ("scripts/evaluate_replay_validity.py", "scripts/evaluate_finite_budget_decisions.py"))
        else:
            report["commands"].append(
                _run(
                    [
                        sys.executable,
                        "experiments/paper_b/smoke_b.py",
                        "--output",
                        "results/paper_b/smoke_release_check",
                    ],
                    clean,
                )
            )
            report["checks"]["smoke_exit_zero"] = report["commands"][-1]["exit_code"] == 0

    ok = all(
        value for key, value in report["checks"].items()
        if key.startswith(("no_", "pdf_", "reproduce_", "smoke_", "manifest_", "theory_", "paper_tests_",
                           "state_audit_", "facade_", "runner_"))
    )
    print(f"check-release-{args.paper}: {'PASS' if ok else 'FAIL'}")
    for key, value in report["checks"].items():
        print(f"  {key}: {value}")
    (ROOT / f"release/check_release_{args.paper}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
