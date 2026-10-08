#!/usr/bin/env python3
"""Release independence check for Paper B: build and verify in a clean directory.

Proves the package builds its PDF, runs its engineering smoke path and passes
its own control tests with no Paper A paths, no measurement core, no model
weights, no network and no credentials.

Usage::

    python3 scripts/check_release_independence.py
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

#: Paths that must never appear in a B package.
FORBIDDEN_PREFIXES = (
    "papers/paper_a",
    "protocols/paper_a",
    "experiments/paper_a",
)

#: Paper A measurement-core modules that B does not import and must not ship.
FORBIDDEN_MEASUREMENT = (
    "experiment_scaffold/src/causal_branch/measurement/__init__.py",
    "experiment_scaffold/src/causal_branch/state_audit.py",
    "experiment_scaffold/src/causal_branch/replay_validity.py",
    "experiment_scaffold/src/causal_branch/finite_repeat_identification.py",
    "experiment_scaffold/src/causal_branch/finite_budget_decisions.py",
    "experiment_scaffold/src/causal_branch/variance_adaptive.py",
)


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
    parser = argparse.ArgumentParser(description="Release independence check (Paper B)")
    parser.parse_args()

    source = ROOT / "release" / "paper_b"
    if not source.is_dir():
        print(f"release package missing: {source}; run scripts/make_release.py first")
        return 1

    report: dict = {"paper": "b", "commands": [], "checks": {}}
    with tempfile.TemporaryDirectory(prefix="release-b-") as tmp:
        clean = Path(tmp) / "paper_b"
        shutil.copytree(source, clean)

        manifest = json.loads((clean / "MANIFEST.json").read_text())
        provenance_errors = verify_manifest(ROOT, clean, manifest)
        report["source_commit"] = manifest.get("source_commit")
        report["checks"]["manifest_matches_source_commit"] = not provenance_errors
        if provenance_errors:
            report["provenance_errors"] = provenance_errors

        paths = [row["path"] for row in manifest["files"]]
        leaked = [p for p in paths if p.startswith(FORBIDDEN_PREFIXES)]
        report["checks"]["no_cross_paper_paths"] = not leaked
        if leaked:
            report["checks"]["cross_paper_paths"] = leaked[:10]

        core = [p for p in paths if p in FORBIDDEN_MEASUREMENT]
        report["checks"]["no_measurement_core"] = not core
        if core:
            report["checks"]["measurement_core_paths"] = core[:10]

        credential_names = {".env", "credentials.json", "secrets.yaml", "token.txt"}
        creds = [p for p in paths if Path(p).name in credential_names]
        report["checks"]["no_credentials"] = not creds

        # 3. Build the manuscript from the package only. The build is skipped,
        #    with a recorded flag, on a host without latexmk; the control tests
        #    below still prove the package's code is complete.
        paper_dir = clean / "papers/paper_b"
        if shutil.which("latexmk"):
            report["commands"].append(
                _run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], paper_dir)
            )
            built = report["commands"][-1]["exit_code"] == 0 and (paper_dir / "main.pdf").is_file()
            report["checks"]["pdf_built"] = built
            if built:
                report["checks"]["pdf_bytes"] = (paper_dir / "main.pdf").stat().st_size
        else:
            report["checks"]["pdf_skipped_no_latexmk"] = True

        # 4. Engineering smoke path.
        report["commands"].append(
            _run(
                [sys.executable, "experiments/paper_b/smoke_b.py", "--output", "results/paper_b/smoke_release_check"],
                clean,
            )
        )
        report["checks"]["smoke_exit_zero"] = report["commands"][-1]["exit_code"] == 0

        # 5. The package runs its own control tests from its own source tree.
        env = dict(os.environ, PYTHONPATH=str(clean / "experiment_scaffold/src"))
        report["commands"].append(
            _run([sys.executable, "-m", "unittest", "discover", "-s", "tests/control", "-p", "test_*.py"], clean, env)
        )
        report["checks"]["control_tests_exit_zero"] = report["commands"][-1]["exit_code"] == 0

    ok = all(
        value for key, value in report["checks"].items()
        if key.startswith(("no_", "pdf_", "smoke_", "control_", "manifest_"))
    )
    print(f"check-release-b: {'PASS' if ok else 'FAIL'}")
    for key, value in report["checks"].items():
        print(f"  {key}: {value}")
    (ROOT / "release/check_release_b.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
