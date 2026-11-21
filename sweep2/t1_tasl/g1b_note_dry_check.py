"""Dry launch check of the G.1b TASL authorization note: shows that a note draft parses as ``check_note`` reads it and
that the whole launch gate of ``g1b_tasl.launch`` passes up to (not including) the node job, in a scratch repository.

ENGINEERING_ONLY; AI-assisted (Claude). Runs nothing on a host, opens no label, evaluation or sealed file, and never
writes to the repository it is given: the scratch "origin" and clone borrow its objects read-only (git alternates)
and live under a fresh temporary directory.

Steps (each reported in the JSON output):

1. **As drafted.** The draft is copied to ``docs/r1/authorizations/g1b_t1_tasl_<date>.md`` in a temp dir and given to
   ``check_note`` (``on_main`` stubbed true): it must STOP on ``approved`` (the draft is unsigned). Its parsed fields are
   listed, and duplicate keys would STOP here.
2. **As signed, in a scratch repository.** ``origin/main`` is set to ``--main-commit`` (the commit that carries the
   launch binding; in reality this unit merged to main). On a clone, the launch commit is made: the spec with the
   note's ``run_id`` and ``paper.commit = --main-commit``, and the note with ``approved: true``, ``paper_commit`` and
   ``spec_sha256`` filled, at its authorization path. It is pushed to the scratch origin and fetched.
3. **The launch gate**, for one TASL-2 node and one TASL-7 node: ``g1b_tasl.launch`` with ``REPO_ROOT`` set to the
   clone, both keys set, and the real ``check_note`` / ``check_host_record`` / ``verify_launch_tasl`` against the scratch
   origin; the node job (``runner``) is replaced by a stub that records it was reached. A TASL-7 node is expected to
   STOP on P7 while the draft's P7 reads PENDING.
4. **The S2-C5 binding** (``g1b_lib.verify_launch``) on the same launch checkout, for comparison: it STOPs.
5. **Main moves on** (decision XC A): an unrelated code commit and a second note for the same run (same paper commit
   and spec; P7 PASS, a hypothetical labelled as such) are published. The checkout stays at the launch commit, with the
   second note copied from ``origin/main`` into its authorizations directory (an untracked docs file): the TASL-2 node
   still passes, the TASL-7 node passes with the second note, and a checkout at the new main STOPs (its code differs).

The clone's ``origin`` URL is the spec's repository URL, rewritten to the scratch origin by ``url.<path>.insteadOf``,
with ``pushurl`` set to the scratch origin; the script refuses to run unless git resolves both to the scratch path.

``python sweep2/t1_tasl/g1b_note_dry_check.py --draft docs/r1/proposals/G1B_T1_TASL_NOTE_DRAFT_20261121.md
--main-commit <sha>`` prints the JSON report; the exit code is 0 when every step gives its expected outcome.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "g1b"))
import g1b_tasl as T  # noqa: E402
import g1b_lib as L  # noqa: E402

SPEC_REL = "sweep2/t1_tasl/g1b_tasl_spec.json"
NOTE_REL = "docs/r1/authorizations/g1b_t1_tasl_20261121.md"
NOTE2_REL = "docs/r1/authorizations/g1b_t1_tasl_20261122.md"
SPARSE = ("docs/r1/PLAN.md", "docs/r1/authorizations/", "docs/r1/reports/trackg_g0_20261117/", "sweep2/")
P7_HYPOTHETICAL = ("P7: PASS — R1-T1-TASL-ENV cross-host check (HYPOTHETICAL, for this dry check only: no crosscheck "
                   "job exists)")


def _git(cwd, *args, check=True):
    env = {**os.environ, "GIT_AUTHOR_NAME": "dry-check", "GIT_AUTHOR_EMAIL": "dry@check",
           "GIT_COMMITTER_NAME": "dry-check", "GIT_COMMITTER_EMAIL": "dry@check"}
    res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env)
    if check and res.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout.strip()


def _fill(draft: str, *, paper_commit: str, spec_sha256: str, p7: str | None = None) -> str:
    out = []
    for line in draft.splitlines(keepends=True):
        if line.startswith("approved:"):
            line = "approved: true\n"
        elif line.startswith("paper_commit:"):
            line = f"paper_commit: {paper_commit}\n"
        elif line.startswith("spec_sha256:"):
            line = f"spec_sha256: {spec_sha256}\n"
        elif line.startswith("P7:") and p7 is not None:
            line = p7 + "\n"
        out.append(line)
    return "".join(out)


def _fields(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line))]


def _outcome(fn):
    try:
        return {"result": "PASS", "value": fn()}
    except (T.Stop, L.Stop) as exc:
        return {"result": "STOP", "message": str(exc)}


@contextlib.contextmanager
def _patched(repo: Path):
    saved_root, saved_env = T.REPO_ROOT, os.environ.get(T.ENABLE_ENV)
    T.REPO_ROOT = repo
    os.environ[T.ENABLE_ENV] = "1"
    try:
        yield
    finally:
        T.REPO_ROOT = saved_root
        if saved_env is None:
            os.environ.pop(T.ENABLE_ENV, None)
        else:
            os.environ[T.ENABLE_ENV] = saved_env


def run(draft_path: Path, main_commit: str, repo: Path, work: Path) -> dict:
    draft = draft_path.read_text()
    report = {"draft": str(draft_path), "draft_sha256": hashlib.sha256(draft.encode()).hexdigest(),
              "main_commit": main_commit, "fields": _fields(draft)}
    dup = sorted({k for k in report["fields"] if report["fields"].count(k) > 1})
    report["duplicate_fields"] = dup
    run_id = next(line.split(":", 1)[1].strip() for line in draft.splitlines() if line.startswith("run_id:"))

    # 1. as drafted
    d1 = work / "as_drafted" / NOTE_REL
    d1.parent.mkdir(parents=True)
    d1.write_text(draft)
    shipped = json.loads(_git(repo, "show", f"{main_commit}:{SPEC_REL}"))
    sp1 = work / "as_drafted" / "spec.json"
    sp1.write_text(json.dumps(shipped))
    report["as_drafted"] = _outcome(lambda: sorted(T.check_note(d1, sp1, shipped["paper"]["commit"],
                                                                on_main=lambda rel, raw: True, spec=shipped)))

    # 2. scratch origin and clone (objects borrowed read-only through alternates)
    objects = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "objects"
    origin = work / "origin.git"
    _git(work, "init", "-q", "--bare", "-b", "main", str(origin))
    (origin / "objects" / "info" / "alternates").write_text(f"{objects}\n")
    _git(origin, "update-ref", "refs/heads/main", main_commit)
    clone = work / "clone"
    subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(origin), str(clone)], check=True,
                   capture_output=True)
    repo_url = shipped["paper"]["repo"]
    _git(clone, "config", "remote.origin.url", repo_url)
    _git(clone, "config", f"url.{origin}.insteadOf", repo_url)
    _git(clone, "config", "remote.origin.pushurl", str(origin))
    if _git(clone, "remote", "get-url", "origin") != str(origin) or \
            _git(clone, "remote", "get-url", "--push", "origin") != str(origin):
        raise RuntimeError("the scratch clone's origin does not resolve to the scratch origin; refusing to continue")
    _git(clone, "sparse-checkout", "set", "--no-cone", *SPARSE)
    _git(clone, "checkout", "-q", "main")
    spec = json.loads((clone / SPEC_REL).read_text())
    spec["run_id"] = run_id
    spec["paper"]["commit"] = main_commit
    (clone / SPEC_REL).write_text(json.dumps(spec, indent=1) + "\n")
    spec_sha = hashlib.sha256((clone / SPEC_REL).read_bytes()).hexdigest()
    note = clone / NOTE_REL
    note.write_text(_fill(draft, paper_commit=main_commit, spec_sha256=spec_sha))
    _git(clone, "add", SPEC_REL, NOTE_REL)
    _git(clone, "commit", "-q", "-m", "dry check: launch commit (spec run_id and paper.commit; signed note)")
    _git(clone, "push", "-q", "origin", "main")
    _git(clone, "fetch", "-q", "origin")
    launch_main = _git(clone, "rev-parse", "HEAD")
    report["scratch"] = {"launch_main": launch_main, "spec_sha256": spec_sha, "run_id": run_id,
                         "spec_diff_vs_shipped": sorted(k for k in spec if spec[k] != shipped.get(k))}

    # 3. the launch gate up to the node job
    reached = []
    runner = lambda sp, node: reached.append(node) or {"runner": "stub (not run)", "node": node}  # noqa: E731
    by_host = {h: next(n["node"] for n in spec["nodes"] if n["host"] == h) for h in T.HOSTS}
    gate = {}
    with _patched(clone):
        for h, node in by_host.items():
            gate[f"{h}:{node}"] = _outcome(lambda: T.launch(clone / SPEC_REL, note, node, enable=True, runner=runner))
        report["s2c5_verify_launch"] = _outcome(
            lambda: L.verify_launch(clone, spec, T.PLAN_ROWS + ("R1-T1-TASL-ENV",)))
        # 5. main moves on: unrelated code and a second note (P7 PASS, hypothetical) for the same run
        m2 = launch_main
        note2_text = _fill(draft, paper_commit=main_commit, spec_sha256=spec_sha, p7=P7_HYPOTHETICAL)
        _git(clone, "checkout", "-q", "-b", "later", m2)
        (clone / "sweep2" / "t1_tasl" / "unrelated_later_code.py").write_text("x = 1\n")
        (clone / NOTE2_REL).write_text(note2_text)
        _git(clone, "add", "-A")
        _git(clone, "commit", "-q", "-m", "dry check: unrelated code and a second note")
        _git(clone, "push", "-q", "origin", "HEAD:main")
        _git(clone, "fetch", "-q", "origin")
        moved = _git(clone, "rev-parse", "origin/main")
        gate["new main checkout (code differs)"] = _outcome(
            lambda: T.launch(clone / SPEC_REL, clone / NOTE2_REL, by_host["TASL-7"], enable=True, runner=runner))
        _git(clone, "checkout", "-q", m2)               # the hosts stay on the signed launch commit
        note2 = clone / NOTE2_REL
        note2.write_bytes(subprocess.run(["git", "-C", str(clone), "show", f"origin/main:{NOTE2_REL}"],
                                         capture_output=True, check=True).stdout)
        node7 = by_host["TASL-7"]
        gate[f"after main moved, launch checkout, TASL-2:{by_host['TASL-2']} (first note)"] = _outcome(
            lambda: T.launch(clone / SPEC_REL, note, by_host["TASL-2"], enable=True, runner=runner))
        gate[f"after main moved, launch checkout, TASL-7:{node7} (second note, P7 PASS hypothetical)"] = _outcome(
            lambda: T.launch(clone / SPEC_REL, note2, node7, enable=True, runner=runner))
        report["scratch"]["main_after_move"] = moved
    report["launch_gate"] = gate
    report["runner_reached_for"] = reached

    n2, n7 = f"TASL-2:{by_host['TASL-2']}", f"TASL-7:{by_host['TASL-7']}"
    expect = {
        "no duplicate fields": not dup,
        "as drafted STOPs on approved": report["as_drafted"]["result"] == "STOP"
        and "approved" in report["as_drafted"]["message"],
        "TASL-2 node passes the gate": gate[n2]["result"] == "PASS",
        "TASL-7 node STOPs on P7 (PENDING)": gate[n7]["result"] == "STOP" and "P7" in gate[n7]["message"],
        "S2-C5 binding STOPs": report["s2c5_verify_launch"]["result"] == "STOP",
        "a checkout at the moved main STOPs": gate["new main checkout (code differs)"]["result"] == "STOP"
        and "differs from the paper commit" in gate["new main checkout (code differs)"]["message"],
        "after main moved, the TASL-2 node passes from the launch checkout":
            gate[f"after main moved, launch checkout, {n2} (first note)"]["result"] == "PASS",
        "after main moved, the TASL-7 node passes with the second note": gate[
            f"after main moved, launch checkout, {n7} (second note, P7 PASS hypothetical)"]["result"] == "PASS",
    }
    report["expected"] = expect
    report["ok"] = all(expect.values())
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draft", required=True)
    ap.add_argument("--main-commit", required=True, help="the commit standing in for the main that carries the code")
    ap.add_argument("--repo", default=str(T.REPO_ROOT))
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="g1b_note_dry_") as tmp:
        report = run(Path(a.draft), a.main_commit, Path(a.repo), Path(tmp))
    print(json.dumps(report, indent=1, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
