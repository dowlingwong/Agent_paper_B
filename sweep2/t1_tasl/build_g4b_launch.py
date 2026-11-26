"""Build the G.4b launch commit (R1-G5-DIFF-RECOUNT) on its base, reproducibly. ENGINEERING_ONLY; not used by any job.

Usage:
  python sweep2/t1_tasl/build_g4b_launch.py build <g4b_build_config.json> --worktree <clean worktree>

The base (``base``) holds the G.4b pin rule in ``g4_tasl.py`` and two templates: ``sweep2/t1_tasl/g4b_tasl_spec.json``
with ``harness.commit`` and ``paper.commit`` PENDING, and the note draft
``docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md`` with ``paper_commit``, ``spec_sha256`` and
``harness_commit`` PENDING. ``build`` resets the config's branch to the base and writes, as in the TASL launch chain:

1. **the launch commit**: the spec with ``harness.commit`` = the config's ``harness_commit`` (the one value that
   depends on the recount unit's review) and ``paper.commit`` = the commit's parent (the base), and the note draft with
   its three binding fields filled; nothing else. Before it commits, with the base's own code: ``g4_tasl.py validate
   --launch``, ``g4_tasl.py harness-check`` on ``harness_repo`` (the harness rule must pass on that commit) and
   ``g4_tasl.py check-note --draft``. The commit changes exactly one file outside ``docs/``, the spec;
2. **the tail**: ``tail_paths`` taken from ``tail_ref`` (the report, this builder and its config, the tests that read
   the built spec);
3. **the launch table**: ``g4b_launch_table.json`` and ``G4B_LAUNCH_TABLE.md`` beside the chain's table.

Author and committer dates are pinned from the config, so the same config, base and tail give the same shas. To move
to the final reviewed tip, change ``harness_commit`` in the config and build again. **Never build again once a G.4b
job or server has started from the launch commit.**
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_launch_chain as B  # noqa: E402

SPEC = "sweep2/t1_tasl/g4b_tasl_spec.json"
NOTE = "docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md"
REPORTS = "docs/r1/reports/tasl_chain_20261122/"
TABLE_JSON = REPORTS + "g4b_launch_table.json"
TABLE_MD = REPORTS + "G4B_LAUNCH_TABLE.md"
TEMPLATE_HARNESS = ("PENDING: final reviewed G5-7 recount tip (R1-G5-DIFF-RECOUNT; build_g4b_launch.py fills it from "
                    "g4b_build_config.json harness_commit)")
TEMPLATE_PAPER = "PENDING: the launch commit's parent (build_g4b_launch.py fills it)"
NOTE_PENDING = ("paper_commit", "spec_sha256", "harness_commit")


def _g4(*args: str) -> dict:
    """``g4_tasl.py`` of the worktree (the base's code), with no inherited PYTHONPATH; rc 0 required, JSON returned."""
    env = {k: v for k, v in __import__("os").environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-B", str(B.W / "sweep2/t1_tasl/g4_tasl.py"), *args], capture_output=True,
                       text=True, cwd=B.W, env=env)
    if r.returncode != 0:
        raise SystemExit(f"build-g4b: g4_tasl.py {args[0]} refused: {r.stderr.strip()[:400]}")
    return json.loads(r.stdout)


def main() -> dict:
    cfg = B.CFG
    tip = cfg["harness_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", str(tip)):
        raise SystemExit("build-g4b: harness_commit must be a full 40-hex commit")
    if B.git("status", "--porcelain"):
        raise SystemExit("build-g4b: the worktree must be clean (it resets the branch)")
    B.git("checkout", "-q", "-f", "-B", cfg["branch"], cfg["base"])
    parent = B.git("rev-parse", "HEAD")
    template = json.loads(B.read(SPEC))
    if template["harness"]["commit"] != TEMPLATE_HARNESS or template["paper"]["commit"] != TEMPLATE_PAPER:
        raise SystemExit("build-g4b: the base must hold the template spec (harness.commit and paper.commit PENDING)")
    note = B.read(NOTE)
    for key in NOTE_PENDING:
        if not re.search(rf"^{key}: PENDING", note, re.M):
            raise SystemExit(f"build-g4b: the base's note draft must have {key} PENDING")

    # ------------------------------------------------------------------ 1. the launch commit
    text = B.read(SPEC)
    text = B.sub1(text, json.dumps(TEMPLATE_HARNESS), json.dumps(tip), "harness.commit")
    text = B.sub1(text, json.dumps(TEMPLATE_PAPER), json.dumps(parent), "paper.commit")
    B.write(SPEC, text)
    validated = _g4("validate", SPEC, "--launch")
    rule = _g4("harness-check", SPEC, "--repo", cfg["harness_repo"])
    spec_sha = B.sha(SPEC)
    B.write(NOTE, B.fields_replace(note, {"paper_commit": parent, "spec_sha256": spec_sha, "harness_commit": tip},
                                   "note"))
    note_check = _g4("check-note", SPEC, "--note", NOTE, "--draft")
    spec = json.loads(B.read(SPEC))
    launch, changed = B.commit(
        f"g4b launch commit: G.4b spec on harness {tip[:8]} (R1-G5-DIFF-RECOUNT); note draft bound",
        [SPEC, NOTE], ["T1-Launch-Run: g4b-repilot", f"T1-Launch-Spec: {SPEC} {spec_sha}", f"T1-Paper-Commit: {parent}",
                       f"T1-Harness-Commit: {tip}"])
    if changed != [SPEC]:
        raise SystemExit(f"build-g4b: the launch commit changes {changed} outside docs/")

    # ------------------------------------------------------------------ 2. the tail
    if cfg.get("tail_ref"):
        B.git("checkout", cfg["tail_ref"], "--", *cfg["tail_paths"])
        B.commit(cfg["tail_message"], cfg["tail_paths"], [])

    # ------------------------------------------------------------------ 3. the launch table
    table = {"schema": "t1_tasl_g4b_launch/1", "base": parent, "run": "g4b-repilot",
             "nodes": [n["node"] for n in spec["nodes"]], "run_id": spec["run_id"], "spec": SPEC,
             "spec_sha256": spec_sha, "paper_commit": parent, "launch_commit": launch, "note_draft": NOTE,
             "harness_commit": tip, "harness_commit_status": cfg["harness_commit_status"],
             "harness_branch": spec["harness"]["branch"], "g1b_pin": spec["harness"]["g1b_pin"],
             "host_check": spec["worker"]["isolation_host_check"], "host_check_commit": rule["host_check_commit"],
             "harness_rule": {k: rule[k] for k in ("measurement_path_files", "added", "engine_files_in_closure",
                                                   "pilot_engine_unchanged", "recount_engine")} | {
                                 "closure_files": len(rule["closure"]), "repo_at_build": cfg["harness_repo"]},
             "projection_total_gpu_hours": validated["projection"]["total_gpu_hours"],
             "note_check_draft": note_check["ok"]}
    B.write(TABLE_JSON, json.dumps(table, indent=1) + "\n")
    B.write(TABLE_MD, "\n".join([
        "# G.4b re-pilot — launch table (generated by build_g4b_launch.py)",
        "",
        f"Base `{parent}` (the G.4b pin rule and the templates). The launch commit changes exactly the spec (plus "
        "`docs/`), and the spec's `paper.commit` is its parent. A docs-only descendant of the launch commit may also "
        "launch (`verify_launch_tasl`). Publish by merge, never squash or rebase: the launch commit must stay an "
        "ancestor of `main` with this sha.",
        "",
        "| run | nodes | run_id | launch commit | paper_commit | spec | spec sha256 | harness commit | note draft |",
        "|---|---|---|---|---|---|---|---|---|",
        f"| g4b-repilot | {', '.join(table['nodes'])} | `{spec['run_id']}` | `{launch}` | `{parent}` | `{SPEC}` | "
        f"`{spec_sha}` | `{tip}` | `{NOTE}` |",
        "",
        f"**Harness commit status:** {cfg['harness_commit_status']}",
        "",
        f"G.1b pin `{spec['harness']['g1b_pin']}`; TASL-2's host check `{spec['worker']['isolation_host_check']['record']}`"
        f" is compared with that pin. Harness rule at build (repository `{cfg['harness_repo']}`): "
        f"{rule['measurement_path_files']} measurement-path files unchanged, noise_floor closure "
        f"{len(rule['closure'])} files, added {rule['added']}, pilot driver and prompt at the pin, recount rule in "
        f"`{rule['recount_engine']}`.",
        ""]))
    B.commit("docs(r1): G.4b launch table (generated)", [TABLE_JSON, TABLE_MD], [])
    table["tip"] = B.git("rev-parse", "HEAD")
    return table


def cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("build",))
    ap.add_argument("config")
    ap.add_argument("--worktree", required=True)
    a = ap.parse_args(argv)
    B.CFG = json.loads(Path(a.config).read_text())
    B.W = Path(a.worktree)
    print(json.dumps(main(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
