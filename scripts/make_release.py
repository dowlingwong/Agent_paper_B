#!/usr/bin/env python3
"""Build allowlisted reproducibility packages for Paper A and Paper B.

The package is a miniature repository with the same relative layout as the
real one, so its pinned scripts run unchanged inside it.  It is generated from
an explicit allowlist; anything not listed is excluded by construction.  A's
package contains no Paper B data, code or protocol; B's package carries the
research-draft status until the qualification and pilot gates pass.

Usage::

    python3 scripts/make_release.py --paper a
    python3 scripts/make_release.py --paper b
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from release_provenance import git

ROOT = Path(__file__).resolve().parents[1]

BUILD_SUFFIXES = {".aux", ".log", ".fls", ".fdb_latexmk", ".out", ".synctex.gz", ".blg"}

PAPER_A_ALLOWLIST = [
    "papers/paper_a",
    "protocols/paper_a/RELEASE_PIN.yaml",
    "protocols/state_audit_synthetic_v3_20260922.json",
    "protocols/state_audit_workload_v1_20260922.json",
    "evidence/state_audit_corrections_20260922/synthetic_v3",
    "evidence/state_audit_corrections_20260922/summary_v3",
    "evidence/state_audit_corrections_20260922/workload_v1_final",
    "scripts/run_state_audit_upgrade.py",
    "scripts/summarize_state_audit_upgrade.py",
    "scripts/measure_state_audit_workload.py",
    "experiment_scaffold/src/causal_branch/state_audit.py",
    "experiment_scaffold/src/causal_branch/checkpoint.py",
    "experiment_scaffold/src/causal_branch/replay_validity.py",
    "experiment_scaffold/src/causal_branch/finite_repeat_identification.py",
    "experiment_scaffold/src/causal_branch/finite_budget_decisions.py",
    "experiment_scaffold/src/causal_branch/variance_adaptive.py",
    "experiment_scaffold/src/causal_branch/measurement/__init__.py",
    "experiment_scaffold/synthetic/finite_repeat_identification",
    "experiment_scaffold/synthetic/finite_budget_decisions",
    "experiment_scaffold/tests/test_state_audit_upgrade.py",
    "experiment_scaffold/tests/test_state_audit_corrections.py",
    "experiments/paper_a",
    "docs/paper_split/SCOPE.md",
    "docs/paper_split/CLAIMS.yaml",
    "docs/paper_split/PRIOR_DISCLOSURE.md",
    "docs/paper_split/VALIDATION.md",
    # Runners, results and modules the manuscript points to (review F02).
    "scripts/evaluate_replay_validity.py",
    "scripts/evaluate_finite_budget_decisions.py",
    "experiment_scaffold/src/causal_branch/u3_calibration_sensitivity.py",
    "experiment_scaffold/src/causal_branch/replay_discrepancy_simulator.py",
    "experiment_scaffold/synthetic/replay_validity_stage1/results.json",
    "experiment_scaffold/synthetic/replay_validity_stage1/README.md",
    "results/validation_logs/L7-sources.json",
    # Dated A-only validation record for the final source (travels with the
    # package while VALIDATION.md is held by another session).
    "docs/paper_split/A_FINALIZATION_RECORD_20261004.md",
]

#: Evidence produced on the Ada host after this allowlist was written (runbook
#: protocols/paper_a/ADA_RUNBOOK_20261005.md section 5).  A group joins A's
#: allowlist once its evidence file is committed; from then on every entry of
#: the group must resolve, so a partial commit fails the build instead of
#: shipping silently without it.  Entries may use shell globs ("live_*").
PAPER_A_POST_RUN = (
    {"name": "E-R3: Appendix F.1 rerun, 1,000 seeds per cell",
     "evidence": "experiment_scaffold/synthetic/replay_validity_stage2/results.json",
     "entries": ["protocols/paper_a/replay_validity_stage2.yaml", "protocols/paper_a/replay_validity_stage2.sha256",
                 "experiment_scaffold/synthetic/replay_validity_stage2"]},
    {"name": "E-R2: real-replay panel v2 (one live run)",
     "evidence": "results/paper_a/replay_panel_v2/live_*/panel/analysis.json",
     # The endpoint file and task registry are what loading the frozen design checks;
     # the task templates and hidden tables themselves are not shipped.
     "entries": ["protocols/paper_a/replay_panel_v2.yaml", "protocols/paper_a/replay_panel_v2.sha256",
                 "protocols/paper_a/replay_panel_v2_endpoint.json",
                 "protocols/paper_a/replay_panel_v2_tasks/registry.yaml",
                 "protocols/paper_a/replay_panel_v2_authorization.json", "results/paper_a/replay_panel_v2/live_*"]},
)


def match_paths(paths, pattern: str) -> list[str]:
    """Repository-relative prefixes of ``paths`` (an iterable of file paths) that match ``pattern``."""
    depth = pattern.count("/") + 1
    found = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) >= depth:
            prefix = "/".join(parts[:depth])
            if fnmatch.fnmatchcase(prefix, pattern):
                found.add(prefix)
    return sorted(found)


def paper_a_post_run_entries(match) -> list[str]:
    """Allowlist entries of the post-run groups whose evidence ``match(pattern)`` finds.

    ``match`` maps a glob pattern to the matching repository-relative paths
    (tracked files for the release, files on disk for the supplement).  A glob
    entry with no match is returned literally, so the caller's "entry has no
    files" check fails loudly.
    """
    entries: list[str] = []
    for group in PAPER_A_POST_RUN:
        if not match(group["evidence"]):
            continue
        for entry in group["entries"]:
            entries.extend((match(entry) or [entry]) if any(c in entry for c in "*?[") else [entry])
    return entries


#: Tracked files under an A allowlist entry that the package leaves out: style
#: kits the TMLR build does not load, and the deferred Tier-2 replay-panel
#: preparation, whose adapter and protocol are not part of A's evidence
#: (review F02, F19).  ``legacy``/``archive`` paths are excluded separately.
PAPER_A_EXCLUDE = {
    "papers/paper_a/iclr2027_conference.sty",
    "papers/paper_a/iclr2027_conference.bst",
    "papers/paper_a/icml2026.sty",
    "papers/paper_a/icml2026.bst",
    "papers/paper_a/algorithm.sty",
    "papers/paper_a/algorithmic.sty",
    "experiments/paper_a/replay_panel.py",
}

#: Non-TeX files kept from the manuscript directory.
PAPER_A_KEEP_NAMES = {"Makefile", "references.bib", "TEMPLATE.lock", "TERMS.md", "TERMS_BASELINE.tsv"}

PAPER_B_ALLOWLIST = [
    "papers/paper_b",
    "protocols/paper_b",
    "experiments/paper_b",
    "experiment_scaffold/src/causal_branch/control",
    "experiment_scaffold/src/causal_branch/measurement/__init__.py",
    "experiment_scaffold/src/causal_branch/state_audit.py",
    "experiment_scaffold/src/causal_branch/checkpoint.py",
    "experiment_scaffold/src/causal_branch/replay_validity.py",
    "experiment_scaffold/src/causal_branch/finite_repeat_identification.py",
    "experiment_scaffold/src/causal_branch/finite_budget_decisions.py",
    "experiment_scaffold/src/causal_branch/variance_adaptive.py",
    "tests/control",
    "docs/paper_split/SCOPE.md",
    "docs/paper_split/PRIOR_DISCLOSURE.md",
    "docs/paper_split/CLAIMS.yaml",
    "docs/paper_split/VALIDATION.md",
]


def _iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.is_file():
            yield child


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tex_closure(base: Path) -> set[Path]:
    pending, seen = [base / "main.tex"], set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if not path.is_file():
            raise SystemExit(f"missing LaTeX input: {path}")
        seen.add(path)
        text = path.read_text()
        for target in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
            pending.append((base / target).with_suffix('.tex'))
    return seen


def paper_a_member(name: str, a_tex: set[str]) -> bool:
    """Whether a path under an A allowlist entry belongs in A's package.

    ``name`` is repository-relative; ``a_tex`` holds the repository-relative
    paths of the LaTeX files ``main.tex`` reaches.  Shared by the release
    package and the anonymised supplement so the two cannot drift (review F01).
    """
    rel = Path(name)
    if any(part in {'legacy', 'archive', 'tmp', '__pycache__'} for part in rel.parts):
        return False
    if rel.suffix in BUILD_SUFFIXES or rel.suffix in {'.pyc', '.bbl'} or rel.name in {'main.pdf', '.DS_Store'}:
        return False
    if name in PAPER_A_EXCLUDE:
        return False
    if name.startswith('papers/paper_a/'):
        if rel.suffix == '.tex':
            return name in a_tex
        # Worked-example and calculator data are inputs of theory-check and the
        # paper tests, so the whole data/ directory ships (review F01).
        return (rel.suffix in {'.sty', '.bst', '.py', '.sh'} or rel.name in PAPER_A_KEEP_NAMES
                or name.startswith('papers/paper_a/data/'))
    return True


def _copy_allowlisted(entries: list[str], destination: Path) -> list[dict]:
    manifest = []
    tracked = set(git(ROOT, 'ls-files', '-z').decode().split('\0'))
    a_base = ROOT / 'papers/paper_a'
    a_tex = {path.relative_to(ROOT).as_posix() for path in _tex_closure(a_base)}
    for name in sorted(tracked):
        if not name or not any(name == entry or name.startswith(entry + '/') for entry in entries):
            continue
        rel = Path(name)
        if not paper_a_member(name, a_tex):
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


def _a_release_id() -> str:
    """The release id declared by A's committed release pin (new pin, new id)."""
    try:
        pin = git(ROOT, 'show', 'HEAD:protocols/paper_a/RELEASE_PIN.yaml').decode()
    except subprocess.CalledProcessError:
        return "paper_a_v2_integration"
    match = re.search(r"^release_id:\s*(\S+)", pin, re.MULTILINE)
    return match.group(1) if match else "paper_a_v2_integration"


def _git_commit() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def build(paper: str) -> Path:
    if git(ROOT, "status", "--porcelain", "--untracked-files=normal").strip():
        raise SystemExit("release requires a clean committed tree")
    if paper == "a":
        allowlist, title = PAPER_A_ALLOWLIST, "Paper A release (measurement / identification)"
        readme = """# Paper A reproducibility package

This package is self-contained for the TMLR manuscript *Branching Is Not Yet
Measurement* and its retained evidence.  It contains no Paper B code, data,
model weights or credentials.

## Build

```sh
cd papers/paper_a
make pdf          # latexmk build
make verify       # no undefined references, errors or duplicate labels
make theory-check # theorem checks, worked example and grid summary (NumPy, PyYAML)
```

## Tests

```sh
python3 -m unittest discover -s papers/paper_a/tests -p 'test_*.py'
PYTHONPATH=experiment_scaffold/src python3 -m unittest \\
    experiment_scaffold/tests/test_state_audit_upgrade.py \\
    experiment_scaffold/tests/test_state_audit_corrections.py
```

## Reproduce the retained evidence

```sh
python3 experiments/paper_a/reproduce_evidence.py            # full
python3 experiments/paper_a/reproduce_evidence.py --quick    # verify scripts only
```

Both modes also re-check the evidence produced on the Ada host when it is
present (`experiments/paper_a/post_run.py er3-check` and `er2-check`): the
E-R3 summaries and Table F.1 are recomputed from the committed per-seed rows,
and the E-R2 analysis from the committed panel rows.  Neither reruns a GPU job.

Full reproduction reruns the synthetic grid (1,890 rows), the workload
measurement (300 records, timings vary by host) and the summary tables into
`results/paper_a/reproduction_<UTC>/`, comparing them with the frozen
`evidence/state_audit_corrections_20260922/` records.  The retained ratios of
median complete audit cost to median best-reference cost are 1.347 / 1.311 /
1.309 with zero audit-cheaper observations at each size: the negative result is
kept, not tuned.

## Requirements

- Python 3.11+, NumPy, PyYAML
- TeX Live with latexmk and the TMLR class kit (recorded in
  `papers/paper_a/TEMPLATE.lock`)
"""
    else:
        allowlist, title = PAPER_B_ALLOWLIST, "Paper B release (budgeted intervention control)"
        readme = """# Paper B research-draft package

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

`protocols/paper_b/contract_v2.yaml` is the active prospective b_v2 contract; v1 is historical.  The
launch validator rejects missing required fields:

```sh
python3 protocols/paper_b/launch_validator.py --for-launch   # exits 1 while draft
```

## Requirements

- Python 3.11+, NumPy, PyYAML
- TeX Live with latexmk and the ICML development style kit
"""
    destination = ROOT / "release" / f"paper_{paper}"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    if paper == "a":
        tracked = [name for name in git(ROOT, "ls-files", "-z").decode().split("\0") if name]
        allowlist = allowlist + paper_a_post_run_entries(lambda pattern: match_paths(tracked, pattern))
    manifest = _copy_allowlisted(allowlist, destination)
    (destination / "README.md").write_text(readme, encoding="utf-8")
    release_manifest = {
        "release": _a_release_id() if paper == "a" else f"paper_{paper}_v2_integration",
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
    print(f"release paper_{paper}: {len(manifest)} files -> {destination.relative_to(ROOT)}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a paper release package")
    parser.add_argument("--paper", choices=("a", "b"), required=True)
    args = parser.parse_args()
    build(args.paper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
