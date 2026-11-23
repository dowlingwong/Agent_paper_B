#!/usr/bin/env python3
"""Seed-namespace check of the R1-SCREEN-MEASURE block 3301-3420 (tier E). Extends ``check_namespaces`` of
``r1/c3/d3_analysis.py`` (branch ``mac-d3-predecl-20261122``, blob ``b20cf020``) to this block.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.

Two parts:
* ``check_block`` (static; run by the runner before an evidence run): the block must be 120 distinct integers and
  meet none of (a) the reserved namespaces of ``d3_analysis.RESERVED_SEED_NAMESPACES`` (copied below; a test
  compares the copy with the blob when the branch is present), (b) the D.3 seed blocks declared in that module
  (instances, smoke, replicates, audits), (c) the sweep instance universe (``p3_split.t0_instance_seed``), (d) the
  namespaces the all-refs scan found that the D.3 list does not carry (``ADDITIONAL_NAMESPACES``).
* ``scan`` (run once; output committed): every distinct tree of every ref (heads, remotes, tags) of the repository is
  searched with ``git grep`` for any token 3301-3420, and for any line mentioning "seed" that holds an integer in
  3031-3420 (a range or base that could reach the block), in code, documents, configurations and manifest-like JSON.
  Protected paths are excluded by pathspec and never read: sweep evidence (``results/r1/evidence``), the B.2 audit
  directories (``docs/r1/reports/b2_audit_*``, ``docs/r1/reports/sweep2_*/s2_b2_audit_*``), and any path holding
  ``r1_sealed``, ``label_block``, ``evaluation_block`` or ``test_block``. This unit's own files are excluded too, so
  that a re-run after they are committed gives the same record. Every E1-style manifest (``seed_bases`` +
  ``seeds_per_condition``) found on any ref is also expanded to its seed spans. A hit whose matching numbers all lie
  inside a hexadecimal run of seven or more characters (a digest or commit fragment) is counted, not listed.

Run: ``python -m r1.noise.screen_seeds scan --repo <git repo> --out <json>``; ``python -m r1.noise.screen_seeds check``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from r1.harness import REPO

BLOCK = tuple(range(3301, 3421))
D3_SOURCE = ("mac-d3-predecl-20261122", "r1/c3/d3_analysis.py", "b20cf020050edd79fd48f233f310850ac20cd297")
# Copy of d3_analysis.RESERVED_SEED_NAMESPACES at the blob above (closed intervals; None = the sweep universe).
RESERVED_SEED_NAMESPACES = {
    "sweep 1 and sweep 2 instance seeds = P3 T0 split universe (e1b_collect._instance_seed, k = 0..17)": None,
    "T1 G.5 instance seeds = P3 T1 split universe (r1/c3/p3_split.py T1_SEEDS)": (5101, 5112),
    "B.2 audit seeds, label 7001-7005 and evaluation 7006-7010 (r1/c3/audit.py DEFAULT_SEEDS)": (7001, 7010),
    "exam instance and audit seeds (r1/exam/namespace.py; sweep2/s2_c3b_lib.py EXAM_SEED_BLOCK 9001-9303)": (9001, 9303),
    "G.1b proposed training-seed block (RUNBOOK G.1b; sweep2/s2_c3b_lib.py G1B_SEED_BLOCK)": (8001, 8010),
    "D21 noise floors, train seeds (r1/noise/e1_noise_floor.py SEED_BASE; g1b note: 30 seeds)": (1001, 1030),
    "D21 noise floors, split seeds": (2001, 2030),
    "D21 noise floors, joint seeds": (3001, 3030),
    "G.4 pilot instance seeds (authorizations/g4_t1_tasl_20261122.md)": (4001, 4003),
    "E1b audit seeds (r1/headroom/e1b_collect.py AUDIT_SEED_BASE; R1-E1B-RERUN2)": (5001, 5006),
    "S2-C3b prompt-measurement seeds (sweep2/s2_c3b_lib.py PROMPT_MEASUREMENT_SEEDS)": (6101, 6108),
    "Track S instance blocks (r1/tracks/collect.py INSTANCE_SEED_BLOCKS on trackS-ops-20261030)": (30000, 39999),
    "Track S audit blocks (r1/tracks/collect.py AUDIT_SEED_BASES)": (100000, 799999),
    "engineering smoke seeds (r1/e2e.py 999)": (999, 999),
}
# Found by the all-refs scan of 23 Nov 2026 and not in the D.3 list (closed intervals).
ADDITIONAL_NAMESPACES = {
    "G.4 pilot seed allow-list (sweep2/g4/g4_lib.py; sweep2/t1_tasl/g4_tasl.py: 4001-4099)": (4001, 4099),
}
# The D.3 blocks declared in the same module (INSTANCE_SEEDS, SMOKE_SEEDS and the replicate / audit laws).
D3_INSTANCE = tuple(range(6201, 6219))
D3_SMOKE = (6301, 6302)
D3_BLOCKS = {
    "D.3 instance seeds": set(D3_INSTANCE),
    "D.3 smoke seeds": set(D3_SMOKE),
    "D.3 smoke replicate seeds (6300 + 10 (s - 6300) + j)": {6300 + 10 * (s - 6300) + j for s in D3_SMOKE
                                                             for j in range(1, 10)},
    "D.3 replicate seeds (6500 + 10 i + j)": {6500 + 10 * i + j for i in range(len(D3_INSTANCE)) for j in range(1, 10)},
    "D.3 audit seeds (6700 + 10 i + k)": {6700 + 10 * i + k for i in range(len(D3_INSTANCE)) for k in range(1, 11)},
}
TOKEN = r"(^|[^0-9.])(330[1-9]|33[1-9][0-9]|34[01][0-9]|3420)([^0-9.]|$)"
REACH = r"(^|[^0-9.])(30[3-9][0-9]|3[1-3][0-9]{2}|34[01][0-9]|3420)([^0-9.]|$)"
INCLUDE = ("*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.sh", "*.sub", "*.cfg", "*.txt",
           "*manifest*.json", "*spec*.json", "*seed*.json", "*design*.json", "*plan*.json")
EXCLUDE = ("results/r1/evidence/**", "docs/r1/reports/b2_audit_*/**", "docs/r1/reports/sweep2_*/s2_b2_audit_*/**",
           "**/r1_sealed/**", "**/*label_block*", "**/*evaluation_block*", "**/*test_block*",
           "**/C3_audit_EVIDENCE*/**",
           # this unit's own files (a re-run after they are committed must give the same record)
           "r1/noise/screen_*.py", "r1/tests/test_screen_measure.py", "docs/r1/authorizations/SCREEN_MEASURE_*",
           "results/r1/engineering/screen_measure_*/**")
HEX_RUN = re.compile(r"[0-9a-fA-F]{7,}")


class SeedClash(ValueError):
    pass


def sweep_universe() -> set[int]:
    from r1.c3.p3_split import T0_INSTANCES_PER_NODE, T0_NODES, t0_instance_seed
    return {t0_instance_seed(n, k) for n in T0_NODES for k in range(T0_INSTANCES_PER_NODE)}


def check_block(block=BLOCK) -> dict:
    """Raise SeedClash if the block meets any reserved namespace or D.3 block; else a report of what was checked."""
    block = list(block)
    if len(block) != 120 or len(set(block)) != 120 or any(not isinstance(s, int) or s < 0 for s in block):
        raise SeedClash("the block must be 120 distinct non-negative integers")
    b = set(block)
    report = {"block": [min(b), max(b), len(b)], "reserved": {}, "d3": {}}
    for label, interval in RESERVED_SEED_NAMESPACES.items():
        used = sweep_universe() if interval is None else set(range(interval[0], interval[1] + 1))
        if b & used:
            raise SeedClash(f"block meets reserved namespace {label!r}: {sorted(b & used)[:5]}")
        report["reserved"][label] = [min(used), max(used), len(used)]
    for label, used in D3_BLOCKS.items():
        if b & used:
            raise SeedClash(f"block meets {label}: {sorted(b & used)[:5]}")
        report["d3"][label] = [min(used), max(used), len(used)]
    report["additional"] = {}
    for label, (lo, hi) in ADDITIONAL_NAMESPACES.items():
        used = set(range(lo, hi + 1))
        if b & used:
            raise SeedClash(f"block meets {label}: {sorted(b & used)[:5]}")
        report["additional"][label] = [lo, hi, len(used)]
    return report


def hex_only(text: str, pattern: str) -> bool:
    """True if every match of *pattern*'s number group lies inside a hexadecimal run of >= 7 characters."""
    runs = [(m.start(), m.end()) for m in HEX_RUN.finditer(text)]
    found = [m.span(2) for m in re.finditer(pattern, text)]
    return bool(found) and all(any(a <= s0 and e0 <= b for a, b in runs) for s0, e0 in found)


# ---------------------------------------------------------------------------------------------------- all-refs scan

def _git(repo: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)   # bytes: no newline translation
    if check and r.returncode not in (0, 1):
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8", "replace")


def _pathspecs() -> list[str]:
    return [f":(glob)**/{g}" for g in INCLUDE] + [f":(exclude,glob){g}" for g in EXCLUDE]


def scan(repo: Path) -> dict:
    refs = [line.split() for line in _git(repo, "for-each-ref", "--format=%(objectname) %(refname)",
                                          "refs/heads", "refs/remotes", "refs/tags").splitlines()]
    trees = defaultdict(list)
    for sha, ref in refs:
        trees[_git(repo, "rev-parse", f"{sha}^{{tree}}").strip()].append(ref)
    token_hits, reach_hits, manifests = {}, {}, {}
    for tree, tree_refs in sorted(trees.items()):
        for pattern, store, need_seed in ((TOKEN, token_hits, False), (REACH, reach_hits, True)):
            out = _git(repo, "grep", "-I", "-n", "--null", "-E", pattern, tree, "--", *_pathspecs())
            for line in out.split("\n"):
                if not line:
                    continue
                head, lineno, text = line.split("\0", 2)       # "<tree>:<path>\0<line>\0<text>"
                path = head.split(":", 1)[1]
                if need_seed and "seed" not in text.lower():
                    continue
                key = (path, text.strip()[:240])
                if key not in store:
                    ctx = [text[max(0, m.start(2) - 40):m.end(2) + 40].strip() for m in re.finditer(pattern, text)]
                    store[key] = {"path": path, "line": int(lineno), "text": text.strip()[:240], "contexts": ctx,
                                  "hex_only": hex_only(text, pattern), "refs": set()}
                store[key]["refs"].update(tree_refs)
        names = _git(repo, "ls-tree", "-r", "--name-only", tree).splitlines()
        for path in names:
            if not path.endswith("manifest.json") or not path.startswith(("results/r1/noise/", "results/r1/pilot/")):
                continue
            if path in manifests:
                continue
            try:
                m = json.loads(_git(repo, "show", f"{tree}:{path}"))
            except (json.JSONDecodeError, RuntimeError):
                continue
            if isinstance(m, dict) and "seed_bases" in m and "seeds_per_condition" in m:
                n = int(m["seeds_per_condition"])
                manifests[path] = {k: [int(v), int(v) + n - 1] for k, v in m["seed_bases"].items()}
    block = set(BLOCK)
    manifest_clash = {p: s for p, s in manifests.items() if any(block & set(range(a, b + 1)) for a, b in s.values())}

    def finish(store, pattern):
        rows = sorted(({**v, "refs": len(v["refs"])} for v in store.values()), key=lambda h: (h["path"], h["line"]))
        hexed = [h for h in rows if h["hex_only"]]                 # classified on the full line
        listed = [h for h in rows if not h["hex_only"]]
        by_path = defaultdict(int)
        for h in hexed:
            by_path[h["path"]] += 1
        return listed, {"count": len(hexed), "by_path": dict(sorted(by_path.items()))}
    token_listed, token_hex = finish(token_hits, TOKEN)
    reach_listed, reach_hex = finish(reach_hits, REACH)
    ref_list = sorted(f"{sha} {ref}" for sha, ref in refs)
    return {"repo_head_count": len(refs), "distinct_trees": len(trees),
            "refs_sha256": hashlib.sha256("\n".join(ref_list).encode()).hexdigest(),
            "include": list(INCLUDE), "exclude": list(EXCLUDE), "token_pattern": TOKEN, "reach_pattern": REACH,
            "hex_run_pattern": HEX_RUN.pattern,
            "token_hits": token_listed, "token_hits_hex_only": token_hex,
            "seed_reach_hits": reach_listed, "seed_reach_hits_hex_only": reach_hex,
            "e1_manifests": manifests, "e1_manifest_spans_meeting_block": manifest_clash,
            "static_check": check_block()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("scan")
    s.add_argument("--repo", default=str(REPO))
    s.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "check":
        print(json.dumps(check_block(), indent=1))
        return 0
    res = scan(Path(args.repo))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"distinct_trees": res["distinct_trees"], "refs": res["repo_head_count"],
                      "token_hits_listed": len(res["token_hits"]),
                      "token_hits_hex_only": res["token_hits_hex_only"]["count"],
                      "seed_reach_hits_listed": len(res["seed_reach_hits"]),
                      "seed_reach_hits_hex_only": res["seed_reach_hits_hex_only"]["count"],
                      "e1_manifests": len(res["e1_manifests"]),
                      "manifest_spans_meeting_block": res["e1_manifest_spans_meeting_block"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
