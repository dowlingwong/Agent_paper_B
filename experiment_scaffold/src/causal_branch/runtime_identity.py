"""Digest of the code that determines what a soak / smoke / E0 run executes.

A qualification or smoke result describes the runtime code it ran on. When any
of these files changes, an earlier result does not automatically qualify the
changed code: readiness compares the digest a result recorded with the digest
of the tree about to launch, and a mismatch is a requalification dependency.

The set is deliberately broad (the whole ``causal_branch`` package, the Pi
extension and system prompt, and the producers/launchers); a false
"requalify" costs a run, a false "still qualified" costs the evidence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

RUNTIME_GLOBS = (
    "experiment_scaffold/src/causal_branch/**/*.py",
    "experiment_scaffold/pi_extensions/*.ts",
    "experiment_scaffold/configs/pi_system_prompt.txt",
    "scripts/realistic_soak.py",
    "scripts/run_local_soak.py",
    "scripts/e0_launch.py",
    "scripts/real_pi_local_smoke.py",
    # S1: the smoke/rehearsal serving launcher, and the modules the producers
    # load by path, change what runs as much as the producers themselves.
    "scripts/start_bound_server.py",
    "scripts/round8_run_supervisor.py",
    "scripts/e0_stage_b_progression.py",
    # The vendored Pi agent the arms execute (tracked source and manifests;
    # the built dist is derived from these and verified by verify_vendored_pi).
    "third_party/pi/package.json",
    "third_party/pi/package-lock.json",
    "third_party/pi/packages/agent/package.json",
    "third_party/pi/packages/agent/src/**/*.ts",
    "third_party/pi/packages/ai/package.json",
    "third_party/pi/packages/ai/src/**/*.ts",
    "third_party/pi/packages/ai/src/**/*.json",
    "third_party/pi/packages/coding-agent/package.json",
    "third_party/pi/packages/coding-agent/src/**/*.ts",
)


def runtime_files(repo_root: Path) -> list[Path]:
    repo_root = Path(repo_root)
    found: set[Path] = set()
    for pattern in RUNTIME_GLOBS:
        for path in repo_root.glob(pattern):
            if path.is_file() and "__pycache__" not in path.parts:
                found.add(path)
    return sorted(found)


def runtime_code_identity(repo_root: Path) -> dict[str, Any]:
    repo_root = Path(repo_root)
    listing = []
    for path in runtime_files(repo_root):
        listing.append((path.relative_to(repo_root).as_posix(),
                        hashlib.sha256(path.read_bytes()).hexdigest()))
    digest = hashlib.sha256("\n".join(f"{p} {h}" for p, h in listing).encode("utf-8")).hexdigest()
    return {"schema": "runtime_code_identity/v2", "globs": list(RUNTIME_GLOBS),
            "files": len(listing), "digest": digest}
