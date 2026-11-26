"""The short cross-check xc3 (R1-G5-AUDIT-TWO-CARDS): the built spec, the note draft and the launch commit
(docs/r1/reports/tasl_chain_20261122/xc3_launch_table.json, built by sweep2/t1_tasl/build_xc3_launch.py).

- the built spec validates with the shipped code: the four G.1b TASL-2 nodes, TASL-7 only, the declared G.1b TASL-2
  attempts (their job-record sha256s as recorded on main), the verdict paths the G.5 audit-host gate binds, the
  projection within the cap; its derived TASL-7 specs differ from the G.1b spec only in the declared fields;
- the note draft's rendered lines equal the spec's; it passes ``check-xc-note --draft``, and once signed (approved,
  P4 filled) the strict check;
- the launch commit changes exactly the spec outside docs/, its spec's paper.commit is its parent, and it launches
  (``verify_launch_tasl``) from itself and a docs-only child, not from the tip; at the base the note refuses the
  template spec.
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
import build_xc3_launch as BX  # noqa: E402
import g1b_crosscheck as X  # noqa: E402
import g1b_tasl as G  # noqa: E402
import g1b_tasl_join as J  # noqa: E402

REP = ROOT / "docs/r1/reports/tasl_chain_20261122"
TABLE = REP / "xc3_launch_table.json"
CFG = json.loads((REP / "xc3_build_config.json").read_text())
SPEC_REL = "sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json"
SPEC_PATH = ROOT / SPEC_REL
NOTE_REL = "docs/r1/proposals/G1B_XC3_SHORT_NOTE_DRAFT_20261125.md"
NOTE = ROOT / NOTE_REL
NODES = ["mlab_imdb", "mlab_ogbn_arxiv", "mlgym_fmnist", "mlgym_houseprice"]
VERDICTS = {n: f"docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_{n}_20261125.json" for n in NODES}
ATTEMPTS = {"mlab_imdb": 1, "mlab_ogbn_arxiv": 1, "mlgym_fmnist": 3, "mlgym_houseprice": 1}
# the TASL chain's record on main of the sealed G.1b TASL-2 attempts: "<sha256>  <host path>" lines, taken on TASL-2
# before the autoresearch G.1b run (the four attempts' files, sealed under sealed_g1b/g1b-tasl-20261121-b/)
CAPTURE = REP / "AR_G1B_TASL2_RESULT_20261122_captures/inputs/baseline_initial_state.txt"
PIN_FILES = {"job_record_sha256": "job_record.json", "out_tar_sha256": "out.tar", "sha256sums_sha256": "SHA256SUMS"}


def _captured(node: str, attempt: int, name: str) -> str:
    """The sha256 the capture records for exactly <sealed root>/g1b-tasl-20261121-b/<node>/attempt-N/<name>."""
    tail = f"/g1b-tasl-20261121-b/{node}/attempt-{attempt}/{name}"
    hits = [ln.split() for ln in CAPTURE.read_text().splitlines()
            if re.fullmatch(r"[0-9a-f]{64}  /\S+", ln) and ln.split()[1].endswith(tail)
            and "/sealed_g1b/" in ln.split()[1]]
    assert len(hits) == 1, (node, name, hits)
    return hits[0][0]
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


def _spec() -> dict:
    spec = json.loads(SPEC_PATH.read_text())
    if spec["paper"]["commit"] == BX.TEMPLATE_PAPER:
        pytest.skip("the template spec (the base): the launch commit fills paper.commit")
    return spec


def _table() -> dict:
    if not TABLE.is_file():
        pytest.skip("no xc3 launch table in this checkout (the builder's last commit adds it)")
    t = json.loads(TABLE.read_text())
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", t["launch_commit"] + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("the xc3 launch commit is not in this repository")
    return t


def _show(commit: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"], capture_output=True, check=True).stdout


def test_built_spec_binds_the_four_tasl2_nodes_and_their_g1b_attempts():
    spec = _spec()
    xc, g1b, _ = X.load_xc(SPEC_PATH, ROOT)
    assert X.is_short(xc) and xc["nodes"] == NODES and xc["hosts"] == ["TASL-7"]
    assert xc["run_id"] == "g1b-tasl-20261121-b-xc3-a" and xc["verdicts"] == VERDICTS
    assert sorted(NODES) == sorted(n["node"] for n in g1b["nodes"] if n["host"] == "TASL-2")
    assert xc["g1b_spec"]["sha256"] == G.L._sha_file(ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json")
    for node, attempt in ATTEMPTS.items():
        a = spec["g1b_tasl2_attempts"][node]
        assert a["attempt"] == attempt
        for key, name in PIN_FILES.items():           # each pin is the capture's line for that very file
            assert a[key] == _captured(node, attempt, name), (node, key)
        assert X._sums_sha(a["out_tar_sha256"], a["job_record_sha256"]) == a["sha256sums_sha256"]
        note = G._note_fields((ROOT / a["note"]).read_bytes())
        assert note["approved"] == "true" and note["spec_sha256"] == a["spec_sha256"]
    fm = REP / "G1B_TASL2_FMNIST_AMENDMENT_20261122_captures/sealed"
    assert spec["g1b_tasl2_attempts"]["mlgym_fmnist"]["sha256sums_sha256"] == G.L._sha_file(fm / "SHA256SUMS")
    assert spec["g1b_tasl2_attempts"]["mlgym_fmnist"]["job_record_sha256"] == G.L._sha_file(fm / "job_record.json")
    assert spec["g1b_tasl2_attempts"]["mlgym_fmnist"]["note"] == "docs/r1/authorizations/g1b_t1_tasl_20261122.md"
    assert spec["g1b_tasl2_attempts"]["mlgym_fmnist"]["spec_sha256"] == xc["g1b_spec"]["sha256"]
    proj = X.short_projection(xc, g1b)
    assert (proj["estimate"]["gpu_hours"], proj["sensitivity"]["gpu_hours"]) == (1.039, 1.184)
    assert (proj["estimate"]["cpu_core_hours"], proj["estimate"]["runs"], proj["cap_gpu_hours"]) == (2.112, 40, 2.0)
    for node in NODES:                         # the derived TASL-7 specs change only the declared fields
        d = X.derived_spec(g1b, xc, node, "TASL-7")
        changed = sorted(k for k in set(_flat(d)) | set(_flat(g1b)) if _flat(d).get(k) != _flat(g1b).get(k))
        assert changed == ["crosscheck.crosscheck_run_id", "crosscheck.g1b_spec_sha256", "crosscheck.host",
                           "crosscheck.kind", "crosscheck.node", "crosscheck.rule",
                           "hosts.TASL-7.extra_env.AR_HOUSEPRICE_TRAIN_CSV", "nodes", "paper.commit", "run_id"]
        moved = [(a, b) for a, b in zip(g1b["nodes"], d["nodes"]) if a != b]     # "nodes": the node's host only
        assert len(moved) == 1 and {k for k in moved[0][0] if moved[0][0][k] != moved[0][1][k]} == {"host"}
        assert [n for n in d["nodes"] if n["node"] == node][0]["host"] == "TASL-7"
        assert [n for n in d["nodes"] if n["node"] != node] == [n for n in g1b["nodes"] if n["node"] != node]
    assert d["hosts"]["TASL-7"]["extra_env"]["AR_HOUSEPRICE_TRAIN_CSV"] == \
        g1b["hosts"]["TASL-2"]["extra_env"]["AR_HOUSEPRICE_TRAIN_CSV"]


def test_note_draft_renders_the_spec_and_passes_the_checks(tmp_path):
    spec = _spec()
    xc, g1b, _ = X.load_xc(SPEC_PATH, ROOT)
    text = NOTE.read_text()
    fields = G._note_fields(text.encode())
    assert fields["approved"] == "false" and fields["paper_commit"] == spec["paper"]["commit"]
    assert fields["xc_spec_sha256"] == G.L._sha_file(SPEC_PATH)
    rendered = BX.render(spec, g1b, X.short_projection(xc, g1b))
    assert {k: fields[k] for k in BX.RENDERED} == rendered
    assert [k for k, v in fields.items() if "<FILL" in v or v.upper().startswith("PENDING")] == ["P4"]
    for word in ("XC3-FAIL", "XC3-SIGN", "XC3-CAP", "a cross-host check PASS for that node",
                 "Signing this note with these lines unchanged adopts the recommended options"):
        assert word in text
    assert X.short_decisions(fields, xc) == {"xc3_fail": "A", "xc3_cap": "R1-G1B-CAP", "skip_nodes": []}
    assert "houseprice" in fields and "skip_nodes: mlgym_houseprice" in fields["houseprice"]
    assert "captured_verdict_<node>.json" in fields["publication"] and "SHA256SUMS sha256" in fields["comparison"]
    assert "`mac-xc3-short-crosscheck-20261125c`" in text.splitlines()[2]
    out = X.check_xc_note(NOTE, SPEC_PATH, xc, g1b, on_main=lambda rel, raw: pytest.fail("draft reads no main"),
                          draft=True)
    assert out["run_id"] == xc["run_id"]
    signed = tmp_path / "docs/r1/authorizations/g1b_xc_short_t1_tasl_20991231.md"
    signed.parent.mkdir(parents=True)
    signed.write_text(re.sub(r"^P4: PENDING — (.*)$", "P4: PASS — docs/r1/reviews/XC3_SHORT_CROSSCHECK_REVIEW.md",
                             text.replace("\napproved: false\n", "\napproved: true\n"), flags=re.M))
    assert X.check_xc_note(signed, SPEC_PATH, xc, g1b, on_main=YES)["approved"] == "true"
    # the other options: an edit of the decision lines only, which the checks accept without other change
    alt = signed.with_name("g1b_xc_short_t1_tasl_20991229.md")
    alt.write_text(signed.read_text().replace("\nxc3_fail: A\n", "\nxc3_fail: B\n")
                   .replace("\nxc3_cap: R1-G1B-CAP\n", "\nxc3_cap: G5-CAP\n")
                   .replace("\nskip_nodes: none\n", "\nskip_nodes: mlgym_houseprice\n"))
    got = X.short_decisions(X.check_xc_note(alt, SPEC_PATH, xc, g1b, on_main=YES), xc)
    assert got == {"xc3_fail": "B", "xc3_cap": "G5-CAP", "skip_nodes": ["mlgym_houseprice"]}
    unfilled = signed.with_name("g1b_xc_short_t1_tasl_20991230.md")           # signed without filling P4
    unfilled.write_text(text.replace("\napproved: false\n", "\napproved: true\n"))
    with pytest.raises(X.Stop, match="not filled"):
        X.check_xc_note(unfilled, SPEC_PATH, xc, g1b, on_main=YES)
    assert J.publication_check(signed.read_text()) == []               # the coordinating chat's check
    assert J.publication_check(unfilled.read_text()) != []
    for key, host in (("P2", "TASL-2"), ("P3", "TASL-7")):              # the cited host checks, by path and sha256
        rec = g1b["hosts"][host]["isolation_host_check"]
        assert f"{rec['record']} sha256 {rec['sha256']}" in fields[key]
        assert G.L._sha_file(ROOT / rec["record"]) == rec["sha256"]
    # the TASL-7 nodes' cross-check note cannot launch this spec, nor this note the xc2 spec
    xc2_path = ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc2, g1b2, _ = X.load_xc(xc2_path, ROOT)
    with pytest.raises(X.Stop, match="g1b_xc_t1_tasl_|g1b_xc_short_t1_tasl_"):
        X.check_xc_note(signed, xc2_path, xc2, g1b2, on_main=YES)
    with pytest.raises(X.Stop, match="g1b_xc_short_t1_tasl_"):
        X.check_xc_note(ROOT / "docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md", SPEC_PATH, xc, g1b, on_main=YES)
    status = X.short_verdict_status(SPEC_PATH, read_main={"docs/r1/PLAN.md": b"plan"}.get, repo=ROOT,
                                    list_main=lambda: list(xc["verdicts"].values()))
    assert {n: s["status"] for n, s in status.items()} == {n: "PENDING" for n in NODES}


def test_launch_commit_and_template(tmp_path):
    t = _table()
    spec = _spec()
    lc, base = t["launch_commit"], t["base"]
    assert _git(ROOT, "rev-parse", f"{lc}^") == base == t["paper_commit"] == spec["paper"]["commit"]
    assert subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", lc, "HEAD"]).returncode == 0
    assert sorted(_git(ROOT, "diff", "--name-only", base, lc).splitlines()) == sorted([SPEC_REL, NOTE_REL])
    assert _show(lc, SPEC_REL) == SPEC_PATH.read_bytes() and _show(lc, NOTE_REL) == NOTE.read_bytes()
    assert t["spec_sha256"] == G.L._sha_file(SPEC_PATH) and t["verdicts"] == VERDICTS
    assert t["base"] == CFG["base"]
    template = json.loads(_show(base, SPEC_REL))
    fa, fb = _flat(template), _flat(spec)
    assert template["paper"]["commit"] == BX.TEMPLATE_PAPER
    assert sorted(k for k in fa if fa[k] != fb[k]) == ["paper.commit"]
    draft_base = G._note_fields(_show(base, NOTE_REL))
    draft = G._note_fields(NOTE.read_bytes())
    assert sorted(k for k in draft if draft[k] != draft_base[k]) == ["paper_commit", "xc_spec_sha256"]
    assert all(draft_base[k].startswith("PENDING") for k in ("paper_commit", "xc_spec_sha256"))
    p = tmp_path / "xc3_template_spec.json"                       # the template refuses (no launch before the build)
    p.write_bytes(_show(base, SPEC_REL))
    with pytest.raises(X.Stop, match="full commit"):
        X.load_xc(p, ROOT)


def _docs_child(work: Path, commit: str) -> str:
    blob = subprocess.run(["git", "-C", str(work), "hash-object", "-w", "--stdin"], input="docs\n", text=True,
                          capture_output=True, check=True).stdout.strip()
    env = dict(os.environ, GIT_INDEX_FILE=str(work / ".git" / "idx_xc3"))
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a], env=env, capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    run("read-tree", commit)
    run("update-index", "--add", "--cacheinfo", f"100644,{blob},docs/r1/zz_xc3_child.md")
    return run("-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", run("write-tree"), "-p", commit, "-m", "d")


def test_launches_from_the_launch_commit_only(tmp_path):
    t = _table()
    spec = _spec()
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
    rows = X.launch_rows(spec)
    assert "R1-G5-AUDIT-TWO-CARDS" in rows
    plan = (ROOT / "docs/r1/PLAN.md").read_text()
    if not all(re.search(rf"^\| {re.escape(r)} \|", plan, re.M) for r in rows):
        pytest.skip("the PLAN rows are not in this checkout")
    seen = {}
    for c in (t["launch_commit"], child, tip, t["base"]):
        _git(work, "checkout", "-q", "--detach", c)
        spec_file = work / SPEC_REL
        try:
            G.verify_launch_tasl(work, {"paper": {"commit": spec["paper"]["commit"]}}, rows, spec_path=spec_file)
            seen[c] = "pass"
        except G.Stop as exc:
            seen[c] = str(exc)
    assert seen[t["launch_commit"]] == "pass" and seen[child] == "pass"
    assert seen[tip].startswith("STOP: the launch checkout differs from the paper commit outside docs/")
    # at the base the binding passes on code (the base is the paper commit), but the spec there is the template:
    # the signed note binds the built spec's sha256 and refuses it
    _git(work, "checkout", "-q", "--detach", t["base"])
    xc, g1b, _ = X.load_xc(SPEC_PATH, ROOT)
    signed = tmp_path / "docs/r1/authorizations/g1b_xc_short_t1_tasl_20991231.md"
    signed.parent.mkdir(parents=True)
    signed.write_text(re.sub(r"^P4: PENDING — (.*)$", "P4: PASS — docs/r1/reviews/XC3_REVIEW.md",
                             NOTE.read_text().replace("\napproved: false\n", "\napproved: true\n"), flags=re.M))
    with pytest.raises(X.Stop, match="xc_spec_sha256"):
        X.check_xc_note(signed, work / SPEC_REL, xc, g1b, on_main=YES)


def test_the_xc2_bindings_are_unchanged_by_the_short_kind():
    """The six committed xc2 verdicts (steps 1 and 2) still name exactly the sides the shipped code recomputes from the
    xc2 spec (the derived xc2 specs are byte-identical), and the xc2 spec is the one its signed note binds."""
    xc2_path = ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc, g1b, _ = X.load_xc(xc2_path, ROOT)
    note = G._note_fields((ROOT / "docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md").read_bytes())
    assert note["xc_spec_sha256"] == G.L._sha_file(xc2_path)
    files = sorted(REP.glob("G1B_XC2_STEP*_VERDICT_*.json"))
    assert len(files) == 6
    for f in files:
        v = json.loads(f.read_text())
        want = X.expected_sides(xc, g1b, v["node"], v["mode"])
        assert {h: (v["sides"][h]["run_id"], v["sides"][h]["spec_sha256"]) for h in want} == want, f.name
        assert v["verdict"] == "PASS" and v["mode"] in ("xc", "preassembly")
