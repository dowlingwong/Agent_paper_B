"""Build the launch commit of the short cross-check xc3 (R1-G5-AUDIT-TWO-CARDS) on its base, reproducibly.
ENGINEERING_ONLY; AI-assisted (Claude); not used by any job.

Usage:
  python sweep2/t1_tasl/build_xc3_launch.py build <xc3_build_config.json> --worktree <clean worktree>
  python sweep2/t1_tasl/build_xc3_launch.py render --worktree <checkout>      # the note's rendered lines (JSON)

The base (``base``) holds the short kind of ``g1b_crosscheck.py`` and two templates: the spec
``sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json`` with ``paper.commit`` PENDING, and the note draft
``docs/r1/proposals/G1B_XC3_SHORT_NOTE_DRAFT_20261125.md`` with ``paper_commit`` and ``xc_spec_sha256`` PENDING and its
other key lines rendered from the spec (``render``). ``build`` resets the config's branch to the base and writes, as in
the TASL launch chain:

1. **the launch commit**: the spec with ``paper.commit`` = the commit's parent (the base), and the note draft with
   ``paper_commit`` and ``xc_spec_sha256`` filled; its rendered lines are rendered again and must not change (a
   template out of step with the spec refuses). Before it commits, with the base's own code:
   ``g1b_crosscheck.py validate`` (the short spec, its derived TASL-7 specs and its projection within the cap) and
   ``g1b_crosscheck.py check-xc-note --draft``. The commit changes exactly one file outside ``docs/``, the spec;
2. **the tail**: ``tail_paths`` taken from ``tail_ref`` (this builder and its config, the prep report, the tests of
   the built spec, note and launch commit);
3. **the launch table**: ``xc3_launch_table.json`` and ``XC3_LAUNCH_TABLE.md`` beside the chain's table.

Author and committer dates are pinned from the config, so the same config, base and tail give the same shas, provided
the commits are made with the same signing setup: the repository signs commits (``commit.gpgsign``, an SSH key), and
the signature is part of each commit, so a rebuild with another key, or unsigned, gives other shas. **Never build again
once a job of the run has started from the launch commit.**

The note's decision lines (``xc3_fail``, ``xc3_cap``, ``skip_nodes``) are not rendered: the author may edit them at
signature (the note says how); the rendered lines do not depend on them.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_launch_chain as B  # noqa: E402

SPEC = "sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json"
G1B = "sweep2/t1_tasl/g1b_tasl_spec.json"
NOTE = "docs/r1/proposals/G1B_XC3_SHORT_NOTE_DRAFT_20261125.md"
REPORTS = "docs/r1/reports/tasl_chain_20261122/"
TABLE_JSON = REPORTS + "xc3_launch_table.json"
TABLE_MD = REPORTS + "XC3_LAUNCH_TABLE.md"
TEMPLATE_PAPER = "PENDING: the launch commit's parent (build_xc3_launch.py fills it)"
NOTE_PENDING = ("paper_commit", "xc_spec_sha256")
RENDERED = ("run_id", "g1b_spec_sha256", "harness_commit", "nodes", "tasl2_side", "verdicts", "projection", "cap")


def render(spec: dict, g1b: dict, proj: dict) -> dict:
    """The note's lines that restate the spec (and the G.1b spec it binds), in the note's words."""
    entries = {n["node"]: n for n in g1b["nodes"]}
    sealed_root = g1b["hosts"]["TASL-2"]["sealed_root"]

    def dev(n):
        e = entries[n]
        return f"{n} ({e['device']}{' on its own cpus ' + e['cpus'] if e.get('cpus') else ''}, {e['env']})"
    side = "; ".join(
        f"{n}: {sealed_root}/{g1b['run_id']}/{n}/attempt-{a['attempt']} (job_record.json sha256 "
        f"{a['job_record_sha256']}, out.tar sha256 {a['out_tar_sha256']}, SHA256SUMS sha256 "
        f"{a['sha256sums_sha256']}, spec_sha256 {a['spec_sha256']}, under {a['note']})"
        for n, a in spec["g1b_tasl2_attempts"].items())
    est, sen = proj["estimate"], proj["sensitivity"]
    gpu_nodes = [n for n in spec["nodes"] if entries[n]["device"] == "gpu"]
    cpu_nodes = [n for n in spec["nodes"] if entries[n]["device"] == "cpu"]
    setup = g1b["estimate"]["setup_estimate_s"]
    runs = (lambda n: est["per_node"][n]["runs"])
    gpu_terms = " + ".join(f"{entries[n]['run_seconds']:g}" for n in gpu_nodes)
    cpu_text = "; ".join(
        f"{n} {est['cpu_core_hours']:g} CPU core-hours ({runs(n)} x {entries[n]['run_seconds']:g} s + {setup:g} s of "
        f"setup, on cpus {entries[n].get('cpus')}; sensitivity {sen['cpu_core_hours']:g}), no GPU" for n in cpu_nodes)
    projection = (
        f"about {est['gpu_hours']:g} GPU-h by the G.1b spec's own accounting (estimate ratio "
        f"{g1b['estimate']['ratio_4090_over_ada']:g}): {runs(gpu_nodes[0])} x ({gpu_terms}) s of runs on TASL-7 plus "
        f"{len(gpu_nodes)} x {setup:g} s of setup; at the sensitivity ratio {g1b['estimate']['ratio_sensitivity']:g}, "
        f"{sen['gpu_hours']:g} GPU-h; {cpu_text}; {est['runs']} runs in all, none on TASL-2 (the TASL-2 side is the "
        "sealed G.1b attempt); the derived specs' own projection and deadline_s, as written in each job record, "
        "still count all 460 runs per node (an over-estimate that binds nothing)")
    cap = (f"{spec['caps']['max_gpu_hours']:g} GPU-h for this run (caps.max_gpu_hours): validate checks the projection "
           "against it, and before each GPU job launch_xc refuses unless the GPU lease hours the run has used so far "
           "plus that job's projection stay within it (short_cap_gate); a projection or consumption beyond it is an "
           "author STOP. The budget it counts against is the xc3_cap line: R1-G1B-CAP (G.1b's 100 GPU-h; recorded "
           "consumption on main 7.0612 GPU-h TASL-2 notes 1 and amendment, 6.9858 GPU-h TASL-7 note 2, 29.1178 GPU-h "
           "autoresearch, plus the cross-check jobs) or G5-CAP (the G.5 cap the G.5 note sets)")
    return {"run_id": spec["run_id"], "g1b_spec_sha256": spec["g1b_spec"]["sha256"],
            "harness_commit": g1b["harness"]["commit"], "nodes": ", ".join(dev(n) for n in spec["nodes"]),
            "tasl2_side": side, "verdicts": "; ".join(f"{n}: {p}" for n, p in spec["verdicts"].items()),
            "projection": projection, "cap": cap}


def _x(*args: str, worktree: Path) -> dict:
    """``g1b_crosscheck.py`` of the worktree (the base's code), with no inherited PYTHONPATH; rc 0, JSON returned."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-B", str(worktree / "sweep2/t1_tasl/g1b_crosscheck.py"), *args],
                       capture_output=True, text=True, cwd=worktree, env=env)
    if r.returncode != 0:
        raise SystemExit(f"build-xc3: g1b_crosscheck.py {args[0]} refused: {r.stderr.strip()[:400]}")
    return json.loads(r.stdout)


def _render_worktree(worktree: Path, spec_rel: str) -> dict:
    """Validate the spec with the worktree's code and render the note's lines. A template spec (paper.commit PENDING)
    is validated as a copy with a dummy full commit: nothing rendered depends on the paper commit."""
    spec = json.loads((worktree / spec_rel).read_text())
    if spec["paper"]["commit"] == TEMPLATE_PAPER:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="xc3_render_") as tmp:
            copy = Path(tmp) / "spec.json"
            copy.write_text(json.dumps({**spec, "paper": {**spec["paper"], "commit": "0" * 40}}))
            validated = _x("validate", str(copy), worktree=worktree)
    else:
        validated = _x("validate", spec_rel, worktree=worktree)
    g1b = json.loads((worktree / G1B).read_text())
    return render(spec, g1b, validated["projection"]) | {"_validated": validated}


def main() -> dict:
    cfg, W = B.CFG, B.W
    if B.git("status", "--porcelain"):
        raise SystemExit("build-xc3: the worktree must be clean (it resets the branch)")
    B.git("checkout", "-q", "-f", "-B", cfg["branch"], cfg["base"])
    parent = B.git("rev-parse", "HEAD")
    template = json.loads(B.read(SPEC))
    if template["paper"]["commit"] != TEMPLATE_PAPER:
        raise SystemExit("build-xc3: the base must hold the template spec (paper.commit PENDING)")
    note = B.read(NOTE)
    for key in NOTE_PENDING:
        if not re.search(rf"^{key}: PENDING", note, re.M):
            raise SystemExit(f"build-xc3: the base's note draft must have {key} PENDING")

    # ------------------------------------------------------------------ 1. the launch commit
    B.write(SPEC, B.sub1(B.read(SPEC), json.dumps(TEMPLATE_PAPER), json.dumps(parent), "paper.commit"))
    lines = _render_worktree(W, SPEC)
    validated = lines.pop("_validated")
    spec_sha = B.sha(SPEC)
    filled = B.fields_replace(note, {"paper_commit": parent, "xc_spec_sha256": spec_sha, **lines}, "note")
    old = _fields(note)
    new = _fields(filled)
    moved = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    if moved != sorted(NOTE_PENDING):
        raise SystemExit(f"build-xc3: the note template is out of step with the spec (lines {moved} would change)")
    B.write(NOTE, filled)
    note_check = _x("check-xc-note", SPEC, "--note", NOTE, "--draft", worktree=W)
    launch, changed = B.commit(
        "xc3 launch commit: short cross-check spec of the four G.1b TASL-2 nodes on TASL-7 (R1-G5-AUDIT-TWO-CARDS); "
        "note draft bound",
        [SPEC, NOTE], ["T1-Launch-Run: xc3-short", f"T1-Launch-Spec: {SPEC} {spec_sha}", f"T1-Paper-Commit: {parent}"])
    if changed != [SPEC]:
        raise SystemExit(f"build-xc3: the launch commit changes {changed} outside docs/")

    # ------------------------------------------------------------------ 2. the tail
    if cfg.get("tail_ref"):
        B.git("checkout", cfg["tail_ref"], "--", *cfg["tail_paths"])
        B.commit(cfg["tail_message"], cfg["tail_paths"], [])

    # ------------------------------------------------------------------ 3. the launch table
    spec = json.loads(B.read(SPEC))
    table = {"schema": "t1_tasl_xc3_launch/1", "base": parent, "run": "xc3-short", "nodes": spec["nodes"],
             "hosts": spec["hosts"], "run_id": spec["run_id"], "derived_run_id": f"{spec['run_id']}-TASL-7",
             "spec": SPEC, "spec_sha256": spec_sha, "paper_commit": parent, "launch_commit": launch,
             "note_draft": NOTE, "note_name": "docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md",
             "g1b_spec_sha256": spec["g1b_spec"]["sha256"], "harness_commit": lines["harness_commit"],
             "g1b_tasl2_attempts": spec["g1b_tasl2_attempts"], "verdicts": spec["verdicts"],
             "projection": validated["projection"], "note_check_draft": note_check["ok"]}
    B.write(TABLE_JSON, json.dumps(table, indent=1) + "\n")
    rows = "\n".join(f"| {n} | `{spec['g1b_tasl2_attempts'][n]['attempt']}` | "
                     f"`{spec['g1b_tasl2_attempts'][n]['job_record_sha256']}` | `{spec['verdicts'][n]}` |"
                     for n in spec["nodes"])
    B.write(TABLE_MD, "\n".join([
        "# Short cross-check xc3 — launch table (generated by build_xc3_launch.py)",
        "",
        f"Base `{parent}` (the short kind of `g1b_crosscheck.py` and the templates). The launch commit changes exactly "
        "the spec (plus `docs/`), and the spec's `paper.commit` is its parent. A docs-only descendant of the launch "
        "commit may also launch (`verify_launch_tasl`). Publish by merge, never squash or rebase: the launch commit "
        "must stay an ancestor of `main` with this sha.",
        "",
        "| run | nodes | run_id (TASL-7 jobs) | launch commit | paper_commit | spec | spec sha256 | note draft |",
        "|---|---|---|---|---|---|---|---|",
        f"| xc3-short | {', '.join(spec['nodes'])} | `{spec['run_id']}` (`{table['derived_run_id']}`) | `{launch}` | "
        f"`{parent}` | `{SPEC}` | `{spec_sha}` | `{NOTE}` |",
        "",
        f"G.1b spec `{spec['g1b_spec']['sha256']}`, harness `{lines['harness_commit']}` on both sides. Projection "
        f"{validated['projection']['estimate']['gpu_hours']} GPU-h (sensitivity "
        f"{validated['projection']['sensitivity']['gpu_hours']}), {validated['projection']['estimate']['cpu_core_hours']}"
        f" CPU core-hours, cap {spec['caps']['max_gpu_hours']} GPU-h.",
        "",
        "| node | G.1b TASL-2 attempt | its job_record.json sha256 | verdict path (bound by the spec) |",
        "|---|---|---|---|",
        rows,
        ""]))
    B.commit("docs(r1): xc3 launch table (generated)", [TABLE_JSON, TABLE_MD], [])
    table["tip"] = B.git("rev-parse", "HEAD")
    return table


def _fields(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("build", "render"))
    ap.add_argument("config", nargs="?")
    ap.add_argument("--worktree", required=True)
    a = ap.parse_args(argv)
    if a.mode == "render":
        out = _render_worktree(Path(a.worktree), SPEC)
        out.pop("_validated")
        print(json.dumps(out, indent=1))
        return 0
    B.CFG = json.loads(Path(a.config).read_text())
    B.W = Path(a.worktree)
    print(json.dumps(main(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
