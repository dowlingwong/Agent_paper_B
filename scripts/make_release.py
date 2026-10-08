#!/usr/bin/env python3
"""Build the Paper B reproducibility package.

The package is a miniature repository with the same relative layout as the
real one, so its pinned scripts run unchanged inside it.  It is generated from
an explicit allowlist; anything not listed is excluded by construction.  B's
package carries the research-draft status until the qualification and pilot
gates pass.

Usage::

    python3 scripts/make_release.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from release_provenance import git

ROOT = Path(__file__).resolve().parents[1]

BUILD_SUFFIXES = {".aux", ".log", ".fls", ".fdb_latexmk", ".out", ".synctex.gz", ".blg"}

#: The complete import closure of B's code at snapshot S, plus B's own trees.
#: The measurement core is deliberately absent: B does not import it, and the
#: package must not ship Paper A's code.
PAPER_B_ALLOWLIST = [
    "papers/paper_b",
    "protocols/paper_b",
    "experiments/paper_b",
    "experiment_scaffold/src/causal_branch/control",
    "experiment_scaffold/src/causal_branch/__init__.py",
    "experiment_scaffold/src/causal_branch/types.py",
    "experiment_scaffold/src/causal_branch/branching.py",
    "experiment_scaffold/src/causal_branch/checkpoint.py",
    "experiment_scaffold/src/causal_branch/pi_fork.py",
    "experiment_scaffold/src/causal_branch/adapters/__init__.py",
    "experiment_scaffold/src/causal_branch/adapters/toy.py",
    "tests/control",
    "docs/paper_split/SCOPE.md",
    "docs/paper_split/PRIOR_DISCLOSURE.md",
    "docs/paper_split/CLAIMS.yaml",
    "docs/paper_split/VALIDATION.md",
]


def paper_b_member(name: str) -> bool:
    """Whether a path under a B allowlist entry belongs in B's package."""
    rel = Path(name)
    if any(part in {'legacy', 'archive', 'tmp', '__pycache__'} for part in rel.parts):
        return False
    if rel.suffix in BUILD_SUFFIXES or rel.suffix in {'.pyc', '.bbl'} or rel.name in {'main.pdf', '.DS_Store'}:
        return False
    return True


def _copy_allowlisted(entries: list[str], destination: Path) -> list[dict]:
    manifest = []
    tracked = set(git(ROOT, 'ls-files', '-z').decode().split('\0'))
    for name in sorted(tracked):
        if not name or not any(name == entry or name.startswith(entry + '/') for entry in entries):
            continue
        rel = Path(name)
        if not paper_b_member(name):
            continue
        data = git(ROOT, 'show', 'HEAD:' + name)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    for entry in entries:
        if not any(row['path'] == entry or row['path'].startswith(entry + '/') for row in manifest):
            raise SystemExit(f'allowlist entry has no committed release files: {entry}')
    return manifest


def _git_commit() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


README = """# Paper B research-draft package

**Status: research draft.**  No real-agent experimental result exists in this
package.  Every performance number in the manuscript is marked planned, and the
figure slots refuse to fabricate data.

## Build

```sh
cd papers/paper_b
make pdf
make verify
```

## Engineering smoke path (ENGINEERING_ONLY)

```sh
python3 experiments/paper_b/smoke_b.py --output results/paper_b/smoke_local
python3 -m unittest discover -s tests/control -p 'test_*.py'
```

The smoke path exercises the branch schema, the matched learners, the
allocator, the paired evaluator and the conservative selection rule on a
closed synthetic workload.  It is an engineering check, never a pilot and never
a real-agent result.

## Contract

`protocols/paper_b/contract_v3.yaml` is the active prospective contract; v2 and
v1 are historical.  The launch validator rejects missing required fields:

```sh
python3 protocols/paper_b/launch_validator.py --for-launch   # exits 1 while draft
```

## Requirements

- Python 3.11+, NumPy, PyYAML
- TeX Live with latexmk and the ICML development style kit
"""


def build(paper: str = "b") -> Path:
    if paper != "b":
        raise SystemExit("this repository ships only Paper B")
    if git(ROOT, "status", "--porcelain", "--untracked-files=normal").strip():
        raise SystemExit("release requires a clean committed tree")
    allowlist = PAPER_B_ALLOWLIST
    title = "Paper B release (budgeted intervention control)"
    destination = ROOT / "release" / "paper_b"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    manifest = _copy_allowlisted(allowlist, destination)
    (destination / "README.md").write_text(README, encoding="utf-8")
    release_manifest = {
        "release": "paper_b_v2_integration",
        "title": title,
        "source_commit": _git_commit(),
        "source_commit_dirty": False,
        "generated_files": ["README.md", "MANIFEST.json"],
        "built_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "files": manifest,
        "file_count": len(manifest),
    }
    (destination / "MANIFEST.json").write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"release paper_b: {len(manifest)} files -> {destination.relative_to(ROOT)}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Paper B release package")
    parser.add_argument("--paper", choices=("b",), default="b")
    args = parser.parse_args()
    build(args.paper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
