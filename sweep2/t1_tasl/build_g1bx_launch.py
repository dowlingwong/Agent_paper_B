"""Build the launch commit of the T1 node-expansion G.1b (R1-T1-NODE-EXPANSION) on its base, reproducibly.
ENGINEERING_ONLY; AI-assisted (Claude); not used by any job.

Usage:
  python sweep2/t1_tasl/build_g1bx_launch.py build <g1bx_build_config.json> --worktree <clean worktree>
  python sweep2/t1_tasl/build_g1bx_launch.py render --worktree <checkout>      # the note's rendered lines (JSON)

The base (``base``) holds the node-expansion kind of ``g1b_tasl.py`` and two templates: the spec
``sweep2/t1_tasl/g1b_tasl_x_spec.json`` with ``paper.commit`` PENDING, and the note draft
``docs/r1/proposals/G1B_X_T1_TASL_NOTE_DRAFT_20261126.md`` with ``paper_commit`` and ``spec_sha256`` PENDING and its
other key lines rendered from the spec (``render``). ``build`` resets the config's branch to the base and writes, as
the xc3 builder does:

1. **the launch commit**: the spec with ``paper.commit`` = the commit's parent (the base), and the note draft with
   ``paper_commit`` and ``spec_sha256`` filled; its rendered lines are rendered again and must not change (a template
   out of step with the spec refuses). Before it commits, with the base's own code: ``g1b_tasl.py validate --launch``
   and ``g1b_tasl.py check-note-x --draft``. The commit changes exactly one file outside ``docs/``, the spec;
2. **the tail**: ``tail_paths`` taken from ``tail_ref`` (this builder and its config, the prep report, the tests of the
   built spec, note and launch commit);
3. **the launch table**: ``g1bx_launch_table.json`` and ``G1BX_LAUNCH_TABLE.md`` beside the chain's tables.

Author and committer dates are pinned from the config, so the same config, base and tail give the same shas, provided
the commits are made with the same signing setup (the repository signs commits with an SSH key; the signature is part
of each commit). **Never build again once a job of the run has started from the launch commit.**

The note's gate lines (``gate_<node>``), P2 and P4 are not rendered: the coordinating chat completes them at
publication (the note says how); the rendered lines do not depend on them.
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

SPEC = "sweep2/t1_tasl/g1b_tasl_x_spec.json"
NOTE = "docs/r1/proposals/G1B_X_T1_TASL_NOTE_DRAFT_20261126.md"
REPORTS = "docs/r1/reports/tasl_chain_20261122/"
TABLE_JSON = REPORTS + "g1bx_launch_table.json"
TABLE_MD = REPORTS + "G1BX_LAUNCH_TABLE.md"
TEMPLATE_PAPER = "PENDING: the launch commit's parent (build_g1bx_launch.py fills it)"
NOTE_PENDING = ("paper_commit", "spec_sha256")


def rendered_keys(spec: dict) -> tuple[str, ...]:
    return ("run_id", "host_TASL2", "envs", *(f"node_{n['node']}" for n in spec["nodes"]), "projection", "cap",
            "cpu_preflight", *(f"determinism_check_{n['node']}" for n in spec["nodes"] if n.get("cpu_replacement")))


def _cpu_list(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def _census_cpus(n: dict) -> str:
    """The CPU set the node's census ran on (g1b_tasl.node_census_cpus)."""
    return (n.get("cpu_replacement") or {}).get("census_cpus") or n["cpus"]


def _disjoint(spec: dict) -> bool:
    sets = [frozenset(_cpu_list(n["cpus"])) for n in spec["nodes"] if n.get("cpus")]
    return all(not (a & b) for i, a in enumerate(sets) for b in sets[i + 1:])


def _where(n: dict) -> str:
    rep = n.get("cpu_replacement")
    if not rep:
        return "its census CPU set"
    return (f"its {rep['authority']} replacement for its census set {rep['census_cpus']}, determinism-checked before "
            "first use")


def determinism_line(spec: dict, n: dict) -> str:
    """The note's key line naming a replacement set's fixed-seed determinism check (R1-TASL2-CPU): record, procedure,
    pass criterion, and the stability record as supporting evidence."""
    rep = n["cpu_replacement"]
    chk = rep["determinism_check"]
    host = spec["hosts"][n["host"]]
    ratio = spec["estimate"]["ratio_sensitivity"]
    bound = f"{ratio * n['run_seconds']:.4f}".rstrip("0").rstrip(".")
    return (
        f"{rep['authority']}: the fixed-seed determinism check of cpus {n['cpus']} (the replacement for the census set "
        f"{rep['census_cpus']}) before the node's first job on it; record {chk['record']} on main, cited in "
        f"gate_{n['node']} as 'determinism check {chk['record']} sha256' followed by the record's sha256; procedure: on "
        f"{host['hostname']}, from the node's G.1b checkout {n['harness']['dir']} at harness {n['harness']['commit']}, "
        f"environment {n['env']}, the census baseline step only (s000_baseline, the reviewed census smoke's first run: "
        f"seeds 8001/8001, the census budget, the node's isolation and limits), run {chk['runs']} times one after "
        f"another, each in its own delegated scope (MemoryMax 8G, MemorySwapMax 0) under taskset -c {n['cpus']} with "
        "CUDA_VISIBLE_DEVICES empty, the set idle before each run (no CPU of it busier than "
        f"{spec['cpu_preflight']['max_busy']:g} over {spec['cpu_preflight']['seconds']:g} s); pass: both runs exit 0 "
        "with isolation effective:true, waivers {} and exceptions [], both result channels have sha256 "
        f"{chk['census_baseline_result_channel_sha256']} (bitwise identical to each other and to the census baseline's), "
        f"and each baseline wall time (elapsed_seconds_info_only) is at most {bound} s (ratio_sensitivity {ratio:g} x "
        f"census B1 {n['run_seconds']:g} s); the record's column-0 lines determinism_check_host, _node, _cpus, "
        "_harness_commit, _runs, _result_channel_sha256, _baseline_seconds and _verdict (PASS) are read by the gate "
        f"(check_determinism_record); supporting evidence, not the check: the TASL-2 CPU stability record "
        f"{rep['stability_record']['path']} sha256 {rep['stability_record']['sha256']} (review ACCEPTED), in which cpus "
        f"{n['cpus']} passed 3 of 3 MetaMaze baselines, bitwise identical, and cpus 8-11 failed 3 of 3")


def render(spec: dict, proj: dict) -> dict:
    """The note's lines that restate the spec, in the note's words."""
    host = spec["hosts"]["TASL-2"]
    est, sen = proj["estimate"], proj["sensitivity"]
    disjoint = _disjoint(spec)
    out = {"run_id": spec["run_id"],
           "host_TASL2": (f"hostname {host['hostname']}; every node CPU-only on its CPU set, its census set or its "
                          "R1-TASL2-CPU replacement, never one containing CPUs 8-11 (no GPU card, no GPU "
                          f"lease; the card {host['gpu_uuid']} stays free for other jobs); a CPU-set lease per node ("
                          + ", ".join(sorted({f"~/r1_locks/cpus-{n['cpus']}.lock" for n in spec["nodes"]}))
                          + ("); the sets are disjoint, so the nodes can run at the same time; base " if disjoint else
                             "), so nodes on one set run one after another; base ")
                          + f"{host['base']}, runs {host['runs_root']}, sealed {host['sealed_root']}"),
           "envs": "; ".join(f"{name} (freeze {env['freeze']}, sha256 {env['sha256']}, Python {env['python']}, "
                             f"compared with {'python -m pip freeze' if env['freeze_tool'] == 'pip' else 'uv pip freeze'}"
                             f" at every job start; interpreter {host['env_python'][name]})"
                             for name, env in spec["envs"].items())}
    for n in spec["nodes"]:
        t = n["census_seconds"]
        out[f"node_{n['node']}"] = (
            f"host TASL-2; cpu (cpus {n['cpus']}, {_where(n)}; engine admission {n['cpu_only']}); env {n['env']}; "
            f"harness {n['harness']['commit']} (branch {n['harness']['branch']}, checkout {n['harness']['dir']}); "
            f"node_spec_sha256 {n['node_spec_sha256']}; committed_pin_sha256 {n['committed_pin_sha256']}; "
            f"edits_manifest_sha256 {n['edits_manifest_sha256']}; data_manifest_sha256 {n['data_manifest_sha256']}; "
            f"census_record {n['census_record']} sha256 {n['census_record_sha256']}; census records B1 {t['B1']:g}, "
            f"B2 {t['B2']:g}, E1 {t['E1']:g}, E2 {t['E2']:g}, E3 {t['E3']:g}, E4 {t['E4']:g} s; slowest "
            f"{n['slowest_census_seconds']:g} s; timeout {3 * n['slowest_census_seconds']:.3f} s (3 x slowest, "
            f"R1-G1B-TIMEOUT); runs 460; projected {est['per_node'][n['node']]['hours_by_record']:g} h by record "
            f"({sen['per_node'][n['node']]['hours_by_record']:g} h at ratio {spec['estimate']['ratio_sensitivity']:g}); "
            f"kit {n['kit_record']['path']} (review {n['kit_review']['path']})")
    by_set: dict[str, float] = {}
    by_set_sen: dict[str, float] = {}
    for n in spec["nodes"]:
        by_set[n["cpus"]] = by_set.get(n["cpus"], 0.0) + est["per_node"][n["node"]]["hours_by_record"]
        by_set_sen[n["cpus"]] = by_set_sen.get(n["cpus"], 0.0) + sen["per_node"][n["node"]]["hours_by_record"]
    sets = "; ".join(f"cpus {s}: {by_set[s]:.3f} h ({by_set_sen[s]:.3f} h)" for s in by_set)
    longest = max(by_set, key=lambda s: by_set_sen[s])
    out["projection"] = (
        f"{est['total_gpu_hours']:g} GPU-h (all four nodes CPU-only); CPU wall by census record {est['cpu_node_hours_by_record']:g} h "
        f"for the four nodes one after another ({sen['cpu_node_hours_by_record']:g} h at ratio "
        f"{spec['estimate']['ratio_sensitivity']:g}); per CPU set: {sets}; "
        + (f"the sets are disjoint, so with all four running at once the wall is the longest set's, cpus {longest}: "
           f"{by_set[longest]:.3f} h ({by_set_sen[longest]:.3f} h); " if disjoint else "")
        + f"by the spec's B1 accounting {est['cpu_node_hours']:g} h, {est['cpu_core_hours']:g} CPU core-hours; "
        f"{len(spec['nodes']) * 460} runs in all")
    pre = spec["cpu_preflight"]
    out["cpu_preflight"] = (
        f"before the attempt and before each part, every job samples /proc/stat for {pre['seconds']:g} s and refuses if "
        f"any CPU of its CPU set was busier than {pre['max_busy']:g} (fraction of the interval); before the attempt "
        "the refusal goes to _refusals/ and uses up nothing, before a later part it is an infrastructure STOP (a new "
        "attempt may follow); the readings are in the job record (cpu_preflight)")
    for n in spec["nodes"]:
        if n.get("cpu_replacement"):
            out[f"determinism_check_{n['node']}"] = determinism_line(spec, n)
    out["cap"] = (f"{spec['caps']['max_total_gpu_hours']:g} GPU-h for the G.1b expansion ({spec['caps']['authority']}); "
                  f"projected {est['total_gpu_hours']:g} GPU-h, margin {spec['caps']['max_total_gpu_hours']:g} GPU-h; a "
                  "projection or consumption beyond it is an author STOP")
    return out


def _t(*args: str, worktree: Path) -> dict:
    """``g1b_tasl.py`` of the worktree (the base's code), with no inherited PYTHONPATH; rc 0, JSON returned."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-B", str(worktree / "sweep2/t1_tasl/g1b_tasl.py"), *args],
                       capture_output=True, text=True, cwd=worktree, env=env)
    if r.returncode != 0:
        raise SystemExit(f"build-g1bx: g1b_tasl.py {args[0]} refused: {r.stderr.strip()[:400]}")
    return json.loads(r.stdout)


def _render_worktree(worktree: Path, spec_rel: str) -> dict:
    """Validate the spec with the worktree's code and render the note's lines. A template spec (paper.commit PENDING)
    is validated as a copy with a dummy full commit: nothing rendered depends on the paper commit."""
    spec = json.loads((worktree / spec_rel).read_text())
    if spec["paper"]["commit"] == TEMPLATE_PAPER:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="g1bx_render_") as tmp:
            copy = Path(tmp) / "spec.json"
            copy.write_text(json.dumps({**spec, "paper": {**spec["paper"], "commit": "0" * 40}}))
            validated = _t("validate", str(copy), "--launch", worktree=worktree)
    else:
        validated = _t("validate", spec_rel, "--launch", worktree=worktree)
    return render(spec, validated["projection"]) | {"_validated": validated}


def main() -> dict:
    cfg, W = B.CFG, B.W
    if B.git("status", "--porcelain"):
        raise SystemExit("build-g1bx: the worktree must be clean (it resets the branch)")
    B.git("checkout", "-q", "-f", "-B", cfg["branch"], cfg["base"])
    parent = B.git("rev-parse", "HEAD")
    template = json.loads(B.read(SPEC))
    if template["paper"]["commit"] != TEMPLATE_PAPER:
        raise SystemExit("build-g1bx: the base must hold the template spec (paper.commit PENDING)")
    note = B.read(NOTE)
    for key in NOTE_PENDING:
        if not re.search(rf"^{key}: PENDING", note, re.M):
            raise SystemExit(f"build-g1bx: the base's note draft must have {key} PENDING")

    # ------------------------------------------------------------------ 1. the launch commit
    B.write(SPEC, B.sub1(B.read(SPEC), json.dumps(TEMPLATE_PAPER), json.dumps(parent), "paper.commit"))
    lines = _render_worktree(W, SPEC)
    validated = lines.pop("_validated")
    spec_sha = B.sha(SPEC)
    filled = B.fields_replace(note, {"paper_commit": parent, "spec_sha256": spec_sha, **lines}, "note")
    old, new = _fields(note), _fields(filled)
    moved = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    if moved != sorted(NOTE_PENDING):
        raise SystemExit(f"build-g1bx: the note template is out of step with the spec (lines {moved} would change)")
    B.write(NOTE, filled)
    note_check = _note_check_draft(W)
    launch, changed = B.commit(
        "g1bx launch commit: G.1b spec of the four T1 node-expansion candidates on TASL-2 (R1-T1-NODE-EXPANSION); "
        "note draft bound",
        [SPEC, NOTE], ["T1-Launch-Run: g1b-expansion", f"T1-Launch-Spec: {SPEC} {spec_sha}", f"T1-Paper-Commit: {parent}"])
    if changed != [SPEC]:
        raise SystemExit(f"build-g1bx: the launch commit changes {changed} outside docs/")

    # ------------------------------------------------------------------ 2. the tail
    if cfg.get("tail_ref"):
        B.git("checkout", cfg["tail_ref"], "--", *cfg["tail_paths"])
        B.commit(cfg["tail_message"], cfg["tail_paths"], [])

    # ------------------------------------------------------------------ 3. the launch table
    spec = json.loads(B.read(SPEC))
    proj = validated["projection"]
    table = {"schema": "t1_tasl_g1bx_launch/1", "base": parent, "run": "g1b-expansion", "run_id": spec["run_id"],
             "nodes": [n["node"] for n in spec["nodes"]], "spec": SPEC, "spec_sha256": spec_sha,
             "paper_commit": parent, "launch_commit": launch, "note_draft": NOTE,
             "note_name": "docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md",
             "harness_commits": {n["node"]: n["harness"]["commit"] for n in spec["nodes"]},
             "cpus": {n["node"]: n["cpus"] for n in spec["nodes"]},
             "census_cpus": {n["node"]: _census_cpus(n) for n in spec["nodes"]},
             "determinism_check_records": {n["node"]: n["cpu_replacement"]["determinism_check"]["record"]
                                           for n in spec["nodes"] if n.get("cpu_replacement")},
             "gate_requires": {n["node"]: n["gate_requires"] for n in spec["nodes"]},
             "projection": proj, "note_check_draft": note_check["ok"], "gates_draft": note_check["gates"]}
    B.write(TABLE_JSON, json.dumps(table, indent=1) + "\n")
    rows = "\n".join(
        f"| {n['node']} | `{n['harness']['commit']}` | {n['cpus']} | {_census_cpus(n)} | {n['env']} | "
        f"{n['slowest_census_seconds']:g} s | "
        f"{proj['estimate']['per_node'][n['node']]['hours_by_record']:g} h | {', '.join(n['gate_requires'])} | "
        f"{note_check['gates'][n['node']]} |" for n in spec["nodes"])
    B.write(TABLE_MD, "\n".join([
        "# T1 node-expansion G.1b — launch table (generated by build_g1bx_launch.py)",
        "",
        f"Base `{parent}` (the node-expansion kind of `g1b_tasl.py` and the templates). The launch commit changes "
        "exactly the spec (plus `docs/`), and the spec's `paper.commit` is its parent. A docs-only descendant of the "
        "launch commit may also launch (`verify_launch_tasl`). Publish by merge, never squash or rebase: the launch "
        "commit must stay an ancestor of `main` with this sha.",
        "",
        "| run | run_id | launch commit | paper_commit | spec | spec sha256 | note draft |",
        "|---|---|---|---|---|---|---|",
        f"| g1b-expansion | `{spec['run_id']}` | `{launch}` | `{parent}` | `{SPEC}` | `{spec_sha}` | `{NOTE}` |",
        "",
        f"Projection {proj['estimate']['total_gpu_hours']} GPU-h (cap {spec['caps']['max_total_gpu_hours']} GPU-h); CPU "
        f"wall by census record {proj['estimate']['cpu_node_hours_by_record']} h for the four nodes one after another "
        f"({proj['sensitivity']['cpu_node_hours_by_record']} h at ratio {spec['estimate']['ratio_sensitivity']}); the "
        "four CPU sets are disjoint and none contains CPUs 8-11 (R1-TASL2-CPU), so the four nodes can run at the same "
        "time.",
        "",
        "| node | harness pin | cpus | census cpus | env | slowest census record | projected (by record) | gate "
        "requires | gate in the draft |",
        "|---|---|---|---|---|---|---|---|---|",
        rows,
        ""]))
    B.commit("docs(r1): g1bx launch table (generated)", [TABLE_JSON, TABLE_MD], [])
    table["tip"] = B.git("rev-parse", "HEAD")
    return table


def _note_check_draft(worktree: Path) -> dict:
    """``check-note-x --draft`` on a copy of the note under its final name in a scratch docs/r1/authorizations/."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory(prefix="g1bx_note_") as tmp:
        d = Path(tmp) / "docs/r1/authorizations"
        d.mkdir(parents=True)
        target = d / "g1b_x_t1_tasl_20261126.md"
        shutil.copy2(worktree / NOTE, target)
        return _t("check-note-x", SPEC, "--note", str(target), "--draft", worktree=worktree)


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
