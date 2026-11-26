"""The G.4b re-pilot (R1-G5-DIFF-RECOUNT): the built spec, the note draft and the launch commit
(docs/r1/reports/tasl_chain_20261122/g4b_launch_table.json, built by sweep2/t1_tasl/build_g4b_launch.py).

- the built spec is the G.4 spec with only the declared fields changed, on the config's harness commit, and validates
  for launch; the base holds the template (the two PENDING values);
- the launch commit changes exactly the spec outside docs/, its spec's paper.commit is its parent, and it launches
  (``verify_launch_tasl``) from itself and a docs-only child, not from the tip; at the base the note refuses the spec;
- the note draft passes ``check-note --draft``, and once signed the strict check, with the disclosure figures;
- the harness rule passes on the configured harness commit when the harness repository is available.
Synthetic only: no host, no label, no evaluation value."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
import g1b_tasl as G  # noqa: E402
import g1b_tasl_join as J  # noqa: E402
import g4_tasl as T  # noqa: E402

REP = ROOT / "docs/r1/reports/tasl_chain_20261122"
TABLE = REP / "g4b_launch_table.json"
CFG = json.loads((REP / "g4b_build_config.json").read_text())
SPEC_REL = "sweep2/t1_tasl/g4b_tasl_spec.json"
SPEC_PATH = ROOT / SPEC_REL
SPEC = json.loads(SPEC_PATH.read_text())
G4 = json.loads((ROOT / "sweep2/t1_tasl/g4_tasl_spec.json").read_text())
NOTE = ROOT / "docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md"
DECLARED = ["comment", "harness.branch", "harness.commit", "harness.g1b_pin", "harness.pin_rule", "paper.commit",
            "run_id", "third_node_reason", "worker.harness_dir"]
YES = lambda rel, raw: True  # noqa: E731


def _git(repo, *a, check=True):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)
    if check and r.returncode:
        raise AssertionError(f"git {a}: {r.stderr}")
    return r.stdout.strip()


def _flat(d: dict, p: str = "") -> dict:
    out = {}
    for k, v in d.items():
        out.update(_flat(v, f"{p}{k}.") if isinstance(v, dict) else {p + k: v})
    return out


def _table() -> dict:
    if not TABLE.is_file():
        pytest.skip("no G.4b launch table in this checkout (the builder's last commit adds it)")
    t = json.loads(TABLE.read_text())
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", t["launch_commit"] + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("the G.4b launch commit is not in this repository")
    return t


def _show(commit: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"], capture_output=True, check=True).stdout


def test_built_spec_is_the_g4_spec_with_the_declared_changes():
    fa, fb = _flat(G4), _flat(SPEC)
    assert sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)) == DECLARED
    assert T.is_g4b(SPEC) and SPEC["harness"]["commit"] == CFG["harness_commit"]
    assert SPEC["harness"]["g1b_pin"] == G4["harness"]["commit"] and SPEC["harness"]["pin_rule"] == T.RECOUNT_ROW
    assert SPEC["run_id"] == "g4b-tasl-20261124-a" and SPEC["pilot"] == G4["pilot"] and SPEC["nodes"] == G4["nodes"]
    out = T.validate_spec(json.loads(SPEC_PATH.read_text()), launch=True)
    assert out["projection"]["total_gpu_hours"] == 11.077 and out["projection"]["proposals_total"] == 180
    assert T.host_check_commit(SPEC) == G4["harness"]["commit"]
    assert SPEC["worker"]["isolation_host_check"] == G4["worker"]["isolation_host_check"]


def test_launch_commit_and_template():
    t = _table()
    lc, base = t["launch_commit"], t["base"]
    assert _git(ROOT, "rev-parse", f"{lc}^") == base == t["paper_commit"] == SPEC["paper"]["commit"]
    assert subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", lc, "HEAD"]).returncode == 0
    changed = _git(ROOT, "diff", "--name-only", base, lc).splitlines()
    assert sorted(changed) == sorted([SPEC_REL, "docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md"])
    assert _show(lc, SPEC_REL) == SPEC_PATH.read_bytes() and _show(lc, str(NOTE.relative_to(ROOT))) == NOTE.read_bytes()
    assert t["spec_sha256"] == G.L._sha_file(SPEC_PATH) and t["harness_commit"] == CFG["harness_commit"]
    template = json.loads(_show(base, SPEC_REL))
    assert template["harness"]["commit"].startswith("PENDING") and template["paper"]["commit"].startswith("PENDING")
    fa, fb = _flat(template), _flat(SPEC)
    assert sorted(k for k in fa if fa[k] != fb[k]) == ["harness.commit", "paper.commit"]
    draft_base = _show(base, str(NOTE.relative_to(ROOT))).decode()
    assert [k for k in ("paper_commit", "spec_sha256", "harness_commit")
            if re.search(rf"^{k}: PENDING", draft_base, re.M)] == ["paper_commit", "spec_sha256", "harness_commit"]


def _signed(tmp: Path, name: str = "g4_t1_tasl_20991231.md") -> Path:
    p = tmp / "docs/r1/authorizations" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(re.sub(r"^approved: false$", "approved: true", NOTE.read_text(), flags=re.M))
    return p


def test_note_draft_and_signed_note(tmp_path):
    text = NOTE.read_text()
    fields = G._note_fields(text.encode())
    assert not [k for k, v in fields.items() if v.upper().startswith("PENDING") or re.search(r"<[^>]*>", v)]
    assert fields["paper_commit"] == SPEC["paper"]["commit"] and fields["spec_sha256"] == G.L._sha_file(SPEC_PATH)
    assert fields["harness_commit"] == SPEC["harness"]["commit"] and fields["g1b_pin"] == SPEC["harness"]["g1b_pin"]
    for figure in ("155 of its 180 proposals", "122 as malformed_hunk", "33 as malformed_diff"):
        assert figure in fields["g4_strict_liveness"]
    assert "g5_tasl.py dates" in fields["dates"] and "--pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json" in fields["dates"]
    assert "trackg_diff_recount/v1" in fields["measures"]
    out = T.note_check(SPEC_PATH, NOTE, draft=True, on_main=lambda rel, raw: False,
                       read_main=lambda rel: pytest.fail("draft mode reads nothing from main"))
    assert out == {"ok": True, "mode": "draft", "run_id": SPEC["run_id"], "harness_commit": SPEC["harness"]["commit"],
                   "host_check_commit": SPEC["harness"]["g1b_pin"], "g4b": True,
                   "paper_commit": SPEC["paper"]["commit"], "spec_sha256": G.L._sha_file(SPEC_PATH)}
    signed = _signed(tmp_path)
    record = SPEC["worker"]["isolation_host_check"]["record"]
    main = {record: (ROOT / record).read_bytes()} | {r: b"Verdict: ACCEPTED\n" for r in T.REVIEW_PATH.findall(
        fields["P4"])}
    got = T.note_check(SPEC_PATH, signed, draft=False, on_main=YES, read_main=main.get)
    assert got["mode"] == "strict"
    assert J.publication_check(signed.read_text()) == []
    with pytest.raises(T.Stop, match="draft mode is for the unsigned note"):
        T.note_check(SPEC_PATH, signed, draft=True, on_main=YES)
    # a G.4 note cannot launch the G.4b spec, nor the G.4b note the G.4 spec
    with pytest.raises(T.Stop, match="paper_commit|spec_sha256"):
        T.check_note(ROOT / "docs/r1/authorizations/g4_t1_tasl_20261123.md", SPEC_PATH, SPEC["paper"]["commit"],
                     on_main=YES, spec=SPEC)
    with pytest.raises(T.Stop, match="paper_commit|spec_sha256"):
        T.check_note(signed, ROOT / "sweep2/t1_tasl/g4_tasl_spec.json", G4["paper"]["commit"], on_main=YES, spec=G4)


def test_harness_rule_on_the_configured_commit():
    root = os.environ.get("AR_HARNESS_ROOT")
    if not root or any(subprocess.run(["git", "-C", root, "cat-file", "-e", c + "^{commit}"],
                                      capture_output=True).returncode for c in (SPEC["harness"]["commit"],
                                                                                 SPEC["harness"]["g1b_pin"])):
        pytest.skip("the harness repository with the G.4b commit is not available (set AR_HARNESS_ROOT)")
    out = T.harness_rule_check(Path(root), SPEC)
    assert out["commit"] == SPEC["harness"]["commit"] and out["host_check_commit"] == SPEC["harness"]["g1b_pin"]
    assert out["engine_files_in_closure"] == [] and "src/autoresearch/trackg/audit_g5.py" in out["added"]


def _docs_child(work: Path, commit: str) -> str:
    blob = subprocess.run(["git", "-C", str(work), "hash-object", "-w", "--stdin"], input="docs\n", text=True,
                          capture_output=True, check=True).stdout.strip()
    env = dict(os.environ, GIT_INDEX_FILE=str(work / ".git" / "idx_g4b"))
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a], env=env, capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    run("read-tree", commit)
    run("update-index", "--add", "--cacheinfo", f"100644,{blob},docs/r1/zz_g4b_child.md")
    return run("-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", run("write-tree"), "-p", commit, "-m", "d")


def test_launches_from_the_launch_commit_only(tmp_path):
    t = _table()
    tip = _git(ROOT, "rev-parse", "HEAD")
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", "--shared", str(ROOT), str(origin)], check=True,
                   capture_output=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(origin), str(work)], check=True,
                   capture_output=True)
    _git(work, "sparse-checkout", "set", "--no-cone", "/sweep2/t1_tasl/", "/docs/r1/PLAN.md")
    child = _docs_child(work, t["launch_commit"])
    merge = subprocess.run(["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", "commit-tree",
                            f"{tip}^{{tree}}", "-p", tip, "-p", child, "-m", "merge"], capture_output=True, text=True,
                           check=True).stdout.strip()
    _git(work, "push", "-q", "origin", f"{merge}:refs/heads/main")
    _git(work, "fetch", "-q", "origin")
    rows = T.plan_rows(SPEC)
    plan = (ROOT / "docs/r1/PLAN.md").read_text()
    if not all(re.search(rf"^\| {re.escape(r)} \|", plan, re.M) for r in rows):
        pytest.skip("the PLAN rows are not in this checkout")
    seen = {}
    for c in (t["launch_commit"], child, tip, t["base"]):
        _git(work, "checkout", "-q", "--detach", c)
        spec_file = work / SPEC_REL
        try:
            T.G.verify_launch_tasl(work, {"paper": {"commit": SPEC["paper"]["commit"]}}, rows, spec_path=spec_file)
            seen[c] = "pass"
        except T.Stop as exc:
            seen[c] = str(exc)
    assert seen[t["launch_commit"]] == "pass" and seen[child] == "pass"
    assert seen[tip].startswith("STOP: the launch checkout differs from the paper commit outside docs/")
    # at the base the binding passes on code (the base is the paper commit), but the spec there is the template:
    # the signed note binds the built spec's sha256 and refuses it
    _git(work, "checkout", "-q", "--detach", t["base"])
    with pytest.raises(T.Stop, match="spec_sha256"):
        T.check_note(_signed(tmp_path), work / SPEC_REL, SPEC["paper"]["commit"], on_main=YES)
