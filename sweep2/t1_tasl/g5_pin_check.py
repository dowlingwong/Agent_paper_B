"""The G5-PIN B check (R1-G5-DECISIONS): two G.5 harness commits carry byte-identical G.5 code. ENGINEERING_ONLY.

G5-PIN B runs each T1 node's G.5 jobs on the harness commit of its own G.1b noise floor: ``G5-7`` on the seven nodes' pin
``c025f89a`` and ``G5-AR`` on autoresearch's pin ``2d09f9a9`` (which descends from ``c025f89a``). The G.5 code must be the
same in both. This check makes that exact, for the whole tree rather than a list of G.5 files:

1. ``G5-7`` descends from (or is) the seven nodes' pin, ``G5-AR`` from autoresearch's pin, and autoresearch's pin from the
   seven nodes' pin;
2. the paths that differ between ``G5-7`` and ``G5-AR`` are exactly the paths that differ between the two pins (the pin
   delta), and
3. on each of those paths ``G5-7`` holds the seven nodes' pin's tree entry and ``G5-AR`` autoresearch's pin's (mode, type
   and object, as ``git ls-tree`` lists them; absent where the pin has no such path).

Diffs run with ``--ignore-submodules=none``, so a gitlink change is never hidden by a user setting, and paths are compared
as git records them (a mode or type change is a change).

So every file outside the pin delta, everything G.5 adds or changes included, is byte-identical between the two G.5
commits, and G.5 changes no file of the pin delta in either family. The per-family measurement-path identity of P5
(each G.5 commit against its own G.1b pin) is a separate check of the G.5 code unit.

Usage: python sweep2/t1_tasl/g5_pin_check.py <harness repo> <G5-7 commit> <G5-AR commit>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PIN_SEVEN = "c025f89aeafc2199bf3487b4bcaa16678273c702"     # the seven nodes' G.1b harness pin (G.1b first note)
PIN_AR = "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"        # autoresearch's G.1b harness pin (third note)


class Stop(RuntimeError):
    pass


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check)


def _commit(repo: Path, ref: str) -> str:
    res = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
    if res.returncode != 0:
        raise Stop(f"STOP: {ref} is not a commit in {repo}")
    return res.stdout.strip()


def _descends(repo: Path, ancestor: str, commit: str) -> bool:
    return _git(repo, "merge-base", "--is-ancestor", ancestor, commit, check=False).returncode == 0


def _changed(repo: Path, a: str, b: str) -> list[str]:
    out = _git(repo, "-c", "diff.ignoreSubmodules=none", "diff", "--ignore-submodules=none", "--no-renames",
               "--no-ext-diff", "--name-only", "-z", a, b).stdout
    return sorted(p for p in out.split("\0") if p)


def _entry(repo: Path, commit: str, path: str) -> str | None:
    """The tree entry of ``path`` at ``commit``: mode, type and object id (None if absent)."""
    out = _git(repo, "ls-tree", "-z", "--full-tree", commit, "--", path).stdout
    entries = [e for e in out.split("\0") if e and e.split("\t", 1)[-1] == path]
    return entries[0].split("\t", 1)[0] if entries else None


def check(repo: Path, g5_seven: str, g5_ar: str, *, pin_seven: str = PIN_SEVEN, pin_ar: str = PIN_AR) -> dict:
    """Raise Stop unless ``g5_seven`` and ``g5_ar`` carry byte-identical G.5 code over their two G.1b pins."""
    repo = Path(repo)
    p7, par = _commit(repo, pin_seven), _commit(repo, pin_ar)
    g7, gar = _commit(repo, g5_seven), _commit(repo, g5_ar)
    if not _descends(repo, p7, par):
        raise Stop(f"STOP: autoresearch's pin {par[:8]} does not descend from the seven nodes' pin {p7[:8]}")
    if not _descends(repo, p7, g7):
        raise Stop(f"STOP: G5-7 {g7[:8]} does not descend from the seven nodes' G.1b pin {p7[:8]}")
    if not _descends(repo, par, gar):
        raise Stop(f"STOP: G5-AR {gar[:8]} does not descend from autoresearch's G.1b pin {par[:8]}")
    delta = _changed(repo, p7, par)
    between = _changed(repo, g7, gar)
    if between != delta:
        extra = sorted(set(between) - set(delta))
        missing = sorted(set(delta) - set(between))
        raise Stop("STOP: the G.5 commits differ outside the pin delta (G.5 code not byte-identical): "
                   f"{extra[:10]}" + (f"; pin-delta paths made equal: {missing[:10]}" if missing else ""))
    for path in delta:
        if _entry(repo, g7, path) != _entry(repo, p7, path) or _entry(repo, gar, path) != _entry(repo, par, path):
            raise Stop(f"STOP: G.5 changes {path}, a file of the pin delta {p7[:8]}..{par[:8]}")
    return {"schema": "g5_pin_check/1", "pin_seven": p7, "pin_ar": par, "g5_seven": g7, "g5_ar": gar,
            "pin_delta": delta, "g5_changes": _changed(repo, p7, g7)}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    try:
        out = check(Path(args[0]), args[1], args[2])
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
