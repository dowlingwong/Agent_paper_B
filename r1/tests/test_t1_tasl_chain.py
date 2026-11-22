"""The TASL launch chain of R1-T1-DATA-MANIFEST and the third G.1b note (docs/r1/reports/tasl_chain_20261122/).

- each re-issued spec differs from the signed one on the chain base only in the fields the row (or the third note)
  changes;
- each run's launch passes ``verify_launch_tasl`` from its own commit and fails from the other chain commits, against a
  local origin whose main is the chain tip (sparse checkouts of this repository);
- each note draft binds its run's spec and passes its check function once signed and its open fields filled;
- the seven-node row assembles across the first note, the amendment and note 2 (decision G1B-JOIN), and the
  autoresearch floor joins it by node.
Synthetic outputs only; no label is read."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT / "sweep2" / "g1b"))
sys.path.insert(0, str(Path(__file__).parent))
import g1b_crosscheck as X  # noqa: E402
import g1b_lib as lib  # noqa: E402
import g1b_tasl as T  # noqa: E402
import g1b_tasl_join as J  # noqa: E402
import g4_tasl as G4  # noqa: E402
from test_t1_tasl_g1b import _attempt, job, launch_spec  # noqa: E402,F401  (job: the fake-host fixture)

TABLE = ROOT / "docs/r1/reports/tasl_chain_20261122/launch_table.json"
PROP = ROOT / "docs/r1/proposals"
SIGNED = {"sweep2/t1_tasl/g1b_tasl_spec.json": "060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465",
          "sweep2/t1_tasl/g1b_crosscheck_spec.json": "2521f7d28f5d0b062d91a55bfaf853c8b6dd04a307c94a9d04f99a049471e5f3",
          "sweep2/t1_tasl/g4_tasl_spec.json": "60607099d99c549b03b9b961d1a1478fe5bcc306c1daf35630677c5ad7313015"}
YES = lambda rel, raw: True  # noqa: E731
CFG = json.loads((ROOT / "docs/r1/reports/tasl_chain_20261122/build_config.json").read_text())
ER = CFG["erratum"]          # the reviewed census erratum record (published on main with the chain)
ER_TEXT = f"{ER['record']} sha256 {ER['sha256']}"
ERRATUM = "docs/r1/reports/x/CENSUS_ERRATUM.md sha256 " + "e" * 64
P4_FILLED = "PASS — docs/r1/reviews/T1_TASL_REVIEW_20261121.md; the census erratum record " + ERRATUM


def _git(repo, *a, check=True):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)
    if check and r.returncode:
        raise AssertionError(f"git {a}: {r.stderr}")
    return r.stdout.strip()


def _table() -> dict:
    if not TABLE.is_file():
        pytest.skip("no launch table in this checkout (the chain's docs commit adds it)")
    t = json.loads(TABLE.read_text())
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", t["runs"][0]["launch_commit"] + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("the chain commits are not in this repository")
    return t


def _show(commit, rel) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"], capture_output=True, check=True).stdout


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ===================================================================================== the specs of the chain
def test_each_reissued_spec_changes_only_the_declared_fields():
    t = _table()
    base = t["base"]
    new = {r["spec"]: r for r in t["runs"]}
    for rel, signed in SIGNED.items():
        old = _show(base, rel)
        assert _sha(old) == signed, f"{rel} on the chain base is not the signed spec"
    g1b_old = json.loads(_show(base, "sweep2/t1_tasl/g1b_tasl_spec.json"))
    g1b_run = new["sweep2/t1_tasl/g1b_tasl_spec.json"]
    g1b_new_raw = _show(g1b_run["launch_commit"], g1b_run["spec"])
    g1b_new = json.loads(g1b_new_raw)
    assert _sha(g1b_new_raw) == g1b_run["spec_sha256"]
    diff = J.spec_difference(g1b_old, g1b_new)
    assert diff["corrected_nodes"] == sorted(J.CORRECTED_NODES) and "paper.commit" in diff["paths"]
    assert g1b_new["paper"]["commit"] == base == g1b_run["paper_commit"]
    by_node = {n["node"]: n["data_manifest_sha256"] for n in g1b_new["nodes"]}
    assert {k: by_node[k] for k in J.CORRECTED_NODES} == t["values"]
    # the cross-check spec: the re-issued G.1b spec, a new run id for the full rerun, paper.commit
    xc_run = new["sweep2/t1_tasl/g1b_crosscheck_spec.json"]
    xc_old = json.loads(_show(base, xc_run["spec"]))
    xc_new = json.loads(_show(xc_run["launch_commit"], xc_run["spec"]))
    assert sorted(".".join(map(str, p)) for p in J._diff(xc_old, xc_new)) == ["comment", "g1b_spec.sha256",
                                                                             "paper.commit", "run_id"]
    assert xc_new["g1b_spec"]["sha256"] == g1b_run["spec_sha256"] and xc_new["paper"]["commit"] == xc_run["paper_commit"]
    assert xc_new["run_id"] != xc_old["run_id"] and xc_new["run_id"].startswith(g1b_new["run_id"] + "-")
    # G.4: the mlgym_fmnist manifest and paper.commit, run id kept (no pilot job ran)
    g4_run = new["sweep2/t1_tasl/g4_tasl_spec.json"]
    g4_old = json.loads(_show(base, g4_run["spec"]))
    g4_new = json.loads(_show(g4_run["launch_commit"], g4_run["spec"]))
    i = [n["node"] for n in g4_new["nodes"]].index("mlgym_fmnist")
    assert sorted(J._diff(g4_old, g4_new)) == sorted([("nodes", i, "data_manifest_sha256"), ("paper", "commit")])
    assert g4_new["nodes"][i]["data_manifest_sha256"] == t["values"]["mlgym_fmnist"]
    # (d) is a later delivery: the AR spec and the third-note draft are main's, the AR spec binding the first note's spec
    assert t["ar"].startswith("deferred") and not any(r["spec"].endswith("g1b_tasl_ar_spec.json") for r in t["runs"])
    tip = _git(ROOT, "rev-parse", "HEAD")
    for rel in ("sweep2/t1_tasl/g1b_tasl_ar_spec.json", "docs/r1/proposals/G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md"):
        assert _show(tip, rel) == _show(base, rel), rel
    assert json.loads(_show(tip, "sweep2/t1_tasl/g1b_tasl_ar_spec.json"))["seven_node_spec"]["sha256"] == SIGNED[
        "sweep2/t1_tasl/g1b_tasl_spec.json"]


def test_each_chain_commit_changes_one_spec_and_names_its_parent():
    t = _table()
    commits = [r["launch_commit"] for r in t["runs"]]
    assert len(set(commits)) == 3                       # (a) G.1b (amendment and note 2), (b) cross-check, (c) G.4
    for c in dict.fromkeys(commits):
        parent = _git(ROOT, "rev-parse", f"{c}^")
        changed = [f for f in _git(ROOT, "diff", "--name-only", parent, c).splitlines() if not f.startswith("docs/")]
        assert len(changed) == 1, (c, changed)
        spec = json.loads(_show(c, changed[0]))
        assert spec["paper"]["commit"] == parent


# ===================================================================================== launches from each commit
def _sparse_clone(tmp_path: Path, tip: str) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", "--shared", str(ROOT), str(origin)], check=True,
                   capture_output=True)
    _git(origin, "update-ref", "refs/heads/main", tip)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(origin), str(work)], check=True,
                   capture_output=True)
    _git(work, "sparse-checkout", "set", "--no-cone", "/sweep2/t1_tasl/", "/docs/r1/PLAN.md")
    return origin, work


def _rows_for(run: str, spec: dict) -> tuple[str, ...]:
    if run.startswith("g1b-ar"):
        return T.AR_PLAN_ROWS + (T.ROW_ID.match(spec["env_decision"]["authority"]).group(0),)
    if run.startswith("g1b"):
        return T.PLAN_ROWS + ("R1-T1-TASL-ENV",)
    if run == "crosscheck":
        return T.PLAN_ROWS + ("R1-T1-TASL-ENV", "R1-G1B-TASL-DECISIONS")
    return G4.PLAN_ROWS


def _docs_child(work: Path, commit: str, name: str) -> str:
    """A docs-only child of ``commit`` (one new file under docs/), made with plumbing (no checkout)."""
    blob = subprocess.run(["git", "-C", str(work), "hash-object", "-w", "--stdin"], input=f"{name}\n", text=True,
                          capture_output=True, check=True).stdout.strip()
    env = dict(os.environ, GIT_INDEX_FILE=str(work / ".git" / f"idx_{name}"))
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a], env=env, capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    run("read-tree", commit)
    run("update-index", "--add", "--cacheinfo", f"100644,{blob},docs/r1/zz_{name}.md")
    tree = run("write-tree")
    return run("-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", tree, "-p", commit, "-m", f"docs {name}")


def _note_check(run: dict, note: Path, checkout: Path):
    """The run's own note check, against the spec file of the checkout (the drafts signed, P-fields filled)."""
    spec_file = checkout / run["spec"]
    if run["run"].startswith("g1b-ar"):
        return T.check_note_ar(note, spec_file, spec=json.loads(spec_file.read_text()), on_main=YES)
    if run["run"].startswith("g1b"):
        return T.check_note(note, spec_file, run["paper_commit"], on_main=YES)
    if run["run"] == "crosscheck":
        xc = json.loads(spec_file.read_text())
        g1b = json.loads((checkout / "sweep2/t1_tasl/g1b_tasl_spec.json").read_text())
        return X.check_xc_note(note, spec_file, xc, g1b, on_main=YES)
    return G4.check_note(note, spec_file, run["paper_commit"], on_main=YES)


def _signed_draft(run: dict, tmp: Path) -> Path:
    names = {"g1b-amendment": "g1b_t1_tasl_20991230.md", "g1b-note2": "g1b_t1_tasl_20991231.md",
             "crosscheck": "g1b_xc_t1_tasl_20991231.md", "g4-pilot": "g4_t1_tasl_20991231.md"}
    return _signed((ROOT / run["note_draft"]).read_text(), tmp / run["run"], names[run["run"]],
                   census_erratum=ERRATUM, P4="PASS — docs/r1/reviews/X.md and the census erratum record " + ERRATUM)


def test_each_run_launches_from_its_own_commit_and_from_no_other(tmp_path):
    t = _table()
    tip = _git(ROOT, "rev-parse", "HEAD")
    origin, work = _sparse_clone(tmp_path, tip)
    _git(work, "fetch", "-q", "origin")
    # docs-only children of every launch commit, all reachable from main (a merge on top of the tip, tree unchanged)
    children = {r["launch_commit"]: _docs_child(work, r["launch_commit"], r["run"]) for r in t["runs"]}
    merge = subprocess.run(["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", "commit-tree",
                            f"{tip}^{{tree}}", "-p", tip, *sum((["-p", c] for c in children.values()), []), "-m",
                            "merge docs children"], capture_output=True, text=True, check=True).stdout.strip()
    _git(work, "push", "-q", "origin", f"{merge}:refs/heads/main")
    _git(work, "fetch", "-q", "origin")
    candidates = list(dict.fromkeys([t["base"]] + [r["launch_commit"] for r in t["runs"]]))
    seen, refused_by_note = {}, []
    for c in candidates + list(children.values()):
        _git(work, "checkout", "-q", "--detach", c)
        for run in t["runs"]:
            spec_file = work / run["spec"]
            spec = json.loads(_show(run["launch_commit"], run["spec"]))
            launch_spec_dict = {"paper": {"commit": spec["paper"]["commit"]}}     # the repo id is tested elsewhere
            if spec_file.is_file() and _sha(spec_file.read_bytes()) == run["spec_sha256"]:
                try:
                    T.verify_launch_tasl(work, launch_spec_dict, _rows_for(run["run"], spec), spec_path=spec_file)
                    ok = "pass"
                except T.Stop as exc:
                    ok = str(exc)
            else:              # another spec in this checkout: the run's note refuses it on its spec sha256
                with pytest.raises((T.Stop, X.Stop, G4.Stop), match="spec_sha256|paper_commit|env_decision"):
                    _note_check(run, _signed_draft(run, tmp_path / c[:8]), work)
                ok = "refused by the note (spec sha256)"
                refused_by_note.append((run["run"], c))
            seen[(run["run"], c)] = ok
    for run in t["runs"]:
        for c in candidates:
            got = seen[(run["run"], c)]
            assert (got == "pass") == (c == run["launch_commit"]), (run["run"], c, got)
        own_child = children[run["launch_commit"]]
        assert seen[(run["run"], own_child)] == "pass", (run["run"], seen[(run["run"], own_child)])
        for other, child in children.items():          # another run's docs child is not this run's launch commit
            if other != run["launch_commit"]:
                assert seen[(run["run"], child)] != "pass"
    shared = [(r["run"], c) for r in t["runs"] for c in candidates
              if c != r["launch_commit"] and seen[(r["run"], c)].startswith("STOP: the launch checkout differs")]
    assert shared and refused_by_note, "both refusal paths must be exercised"


# ===================================================================================== the note drafts
def _signed(text: str, tmp: Path, name: str, **fills) -> Path:
    fills.setdefault("approved", "true")
    out = []
    for line in text.splitlines(keepends=True):
        key = line.split(":", 1)[0]
        out.append(f"{key}: {fills[key]}\n" if key in fills and re.match(rf"^{re.escape(key)}: ", line) else line)
    p = tmp / "docs/r1/authorizations" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(out))
    return p


def _open_fields(text: str) -> list[str]:
    return sorted(k for k, v in T._note_fields(text.encode()).items() if "<FILL" in v
                  or v.upper().startswith("PENDING"))




def test_amendment_note_binds_the_reissued_spec_and_launches_only_tasl2(tmp_path):
    spec_path = ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json"
    spec = T.load_spec(spec_path)
    text = (PROP / "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md").read_text()
    f = T._note_fields(text.encode())
    assert f["approved"] == "false" and f["run_id"] == spec["run_id"] == "g1b-tasl-20261121-b"
    assert f["paper_commit"] == spec["paper"]["commit"] and f["spec_sha256"] == lib._sha_file(spec_path)
    assert _open_fields(text) == ["P7"]             # P7: the TASL-7 nodes are note 2's
    assert f"census erratum record {ER_TEXT} (review {ER['review']})" in f["P4"] and f["P4"].startswith("PASS — ")
    assert "docs/r1/reviews/T1_TASL_REVIEW_20261121.md" in f["P4"] and "docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md" in f["P4"]
    for node in J.CORRECTED_NODES:
        assert T.node_entry(spec, node)["data_manifest_sha256"] in f[f"node_{node}"]
        assert T.node_entry(spec, node)["data_manifest_sha256"] == CFG["values"][node]
    unfilled = _signed(text, tmp_path / "u", "g1b_t1_tasl_20261122.md", P4="PENDING — " + f["P4"][len("PASS — "):])
    with pytest.raises(T.Stop, match="P4 is not PASS"):           # review round 1, M2: no launch without P4 PASS
        T.launch(spec_path, unfilled, "mlgym_fmnist", enable=True, on_main=YES)
    note = _signed(text, tmp_path, "g1b_t1_tasl_20261122.md")
    fields = T.check_note(note, spec_path, spec["paper"]["commit"], on_main=YES, spec=spec)
    assert fields["amends"].startswith("docs/r1/authorizations/g1b_t1_tasl_20261121.md")
    with pytest.raises(T.Stop, match="P7 PASS"):
        T.launch(spec_path, note, "mlab_cifar10", enable=True, on_main=YES)
    first = ROOT / "docs/r1/authorizations/g1b_t1_tasl_20261121.md"
    with pytest.raises(T.Stop, match="paper_commit|spec_sha256"):   # the first note cannot launch the re-issued spec
        T.check_note(first, spec_path, spec["paper"]["commit"], on_main=YES, spec=spec)


def test_note2_binds_the_reissued_spec_and_waits_for_the_crosscheck(tmp_path, capsys):
    spec_path = ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json"
    spec = T.load_spec(spec_path)
    text = (PROP / "G1B_T1_TASL_NOTE2_DRAFT_20261121.md").read_text()
    f = T._note_fields(text.encode())
    first = T._note_fields((ROOT / "docs/r1/authorizations/g1b_t1_tasl_20261121.md").read_bytes())
    for k in ("run_id", "harness_commit", "host_row"):
        assert f[k] == first[k]
    assert f["paper_commit"] == spec["paper"]["commit"] and f["spec_sha256"] == lib._sha_file(spec_path)
    assert f["spec_sha256"] != first["spec_sha256"]
    amend = T._note_fields((PROP / "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md").read_bytes())
    assert (f["paper_commit"], f["spec_sha256"]) == (amend["paper_commit"], amend["spec_sha256"])
    assert _open_fields(text) == ["P7"]
    assert f["P4"] == amend["P4"]
    with pytest.raises(T.Stop, match="P4 is not PASS"):
        T.check_note(_signed(text, tmp_path / "u", "g1b_t1_tasl_20261123.md", P4="PENDING — x"), spec_path,
                     spec["paper"]["commit"], on_main=YES, spec=spec)
    note = _signed(text, tmp_path, "g1b_t1_tasl_20261123.md")
    T.check_note(note, spec_path, spec["paper"]["commit"], on_main=YES, spec=spec)
    draft = _signed(text, tmp_path / "d", "g1b_t1_tasl_20261123.md", approved="false")
    xc = str(ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json")
    assert X.main(["check-note2", xc, "--note", str(draft), "--verdict", "docs/r1/reports/x.json", "--draft"]) == 2
    assert "P7 must read PASS" in capsys.readouterr().err


def test_reissued_crosscheck_note_binds_the_reissued_specs(tmp_path):
    xc_path = ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc, g1b, _ = X.load_xc(xc_path, ROOT)
    text = (PROP / "G1B_XC_NOTE_REISSUE_DRAFT_20261122.md").read_text()
    assert _open_fields(text) == []
    f = T._note_fields(text.encode())
    assert f["census_erratum"] == ER_TEXT
    with pytest.raises(X.Stop, match="census_erratum"):
        X.check_xc_note(_signed(text, tmp_path / "e", "g1b_xc_t1_tasl_20261123.md", census_erratum="<FILL x>"),
                        xc_path, xc, g1b, on_main=YES)
    assert f["run_id"] == xc["run_id"] != "g1b-tasl-20261121-b-xc" and f["approved"] == "false"
    assert f"{xc['run_id']}-TASL-7" in f["jobs"] and "g1b-tasl-20261121-b-xc-TASL" not in f["jobs"]
    with pytest.raises(X.Stop, match="not filled|approved"):
        X.check_xc_note(_signed(text, tmp_path / "u", "g1b_xc_t1_tasl_20261123.md", approved="false"), xc_path, xc,
                        g1b, on_main=YES)
    fields = X.check_xc_note(_signed(text, tmp_path, "g1b_xc_t1_tasl_20261123.md"), xc_path,
                             xc, g1b, on_main=YES)
    assert fields["g1b_spec_sha256"] == lib._sha_file(ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json")
    with pytest.raises(X.Stop, match="paper_commit|spec_sha256|run_id"):            # the first cross-check note
        X.check_xc_note(_signed((ROOT / "docs/r1/authorizations/g1b_xc_t1_tasl_20261122.md").read_text(),
                                tmp_path / "old", "g1b_xc_t1_tasl_20261122.md"), xc_path, xc, g1b, on_main=YES)


def test_reissued_g4_note_binds_the_reissued_spec(tmp_path):
    spec_path = ROOT / "sweep2/t1_tasl/g4_tasl_spec.json"
    spec = G4.load_spec(spec_path)
    G4.validate_spec(copy.deepcopy(spec))                          # node pins equal the re-issued G.1b spec's
    text = (PROP / "G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md").read_text()
    assert _open_fields(text) == [] and T._note_fields(text.encode())["census_erratum"] == ER_TEXT
    with pytest.raises(G4.Stop, match="not filled"):
        G4.check_note(_signed(text, tmp_path / "u", "g4_t1_tasl_20261123.md", census_erratum="<FILL x>"), spec_path,
                      spec["paper"]["commit"], on_main=YES, spec=spec)
    fields = G4.check_note(_signed(text, tmp_path, "g4_t1_tasl_20261123.md"), spec_path,
                           spec["paper"]["commit"], on_main=YES, spec=spec)
    assert fields["run_id"] == "g4-tasl-20261121-a" and T.node_entry(
        T.load_spec(ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json"), "mlgym_fmnist")["data_manifest_sha256"] in fields["nodes"]
    with pytest.raises(G4.Stop, match="spec_sha256|paper_commit"):
        G4.check_note(ROOT / "docs/r1/authorizations/g4_t1_tasl_20261122.md", spec_path, spec["paper"]["commit"],
                      on_main=YES, spec=spec)


# ===================================================================================== the joined seven-node row
def _amend(spec: dict) -> dict:
    new = copy.deepcopy(spec)
    new["paper"]["commit"] = "4" * 40
    for n in new["nodes"]:
        if n["node"] in J.CORRECTED_NODES:
            n["data_manifest_sha256"] = hashlib.sha256(n["node"].encode()).hexdigest()
    return new


def _main_with(rows=(J.JOIN_ROW,), first: bytes | None = None) -> callable:
    text = "".join(f"| {r} | x |\n" for r in rows).encode()
    return lambda rel: text if rel == "docs/r1/PLAN.md" else first if rel == J.FIRST_NOTE else None


def _first_note_for(spec_path: Path, spec: dict) -> bytes:
    return (f"approved: true\nspec_sha256: {lib._sha_file(spec_path)}\npaper_commit: {spec['paper']['commit']}\n"
            ).encode()


def test_spec_difference_admits_only_the_row_fields(job):
    spec = job[0]
    diff = J.spec_difference(spec, _amend(spec))
    assert diff["corrected_nodes"] == sorted(J.CORRECTED_NODES) and len(diff["paths"]) == 3
    for edit, match in ((lambda s: s.update(run_id="other"), "run id"),
                        (lambda s: s["nodes"][0].update(run_seconds=1.0), "outside R1-T1-DATA-MANIFEST"),
                        (lambda s: s["nodes"].reverse(), "same order"),
                        (lambda s: s["harness"].update(commit="5" * 40), "outside")):
        bad = _amend(spec)
        edit(bad)
        with pytest.raises(J.Stop, match=match):
            J.spec_difference(spec, bad)
    other = _amend(spec)
    for n in other["nodes"]:
        if n["node"] == "mlab_imdb":
            n["data_manifest_sha256"] = "f" * 64          # not a corrected node
    with pytest.raises(J.Stop, match="outside"):
        J.spec_difference(spec, other)


def test_the_seven_node_row_assembles_across_the_three_notes(job, tmp_path, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    amended = _amend(spec)
    amended_path = tmp_path / "amended_spec.json"
    amended_path.write_text(json.dumps(amended))
    first_note = ("mlab_ogbn_arxiv", "mlab_imdb", "mlgym_houseprice")
    sealed = {}
    for name, path in [(n, spec_path) for n in first_note] + \
            [(n["node"], amended_path) for n in spec["nodes"] if n["node"] not in first_note]:
        s = T.load_spec(path)
        node = T.node_entry(s, name)
        log = Path(s["hosts"][node["host"]]["runs_root"]) / s["run_id"] / "_logs" / f"{name}-x.node.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("NODE_EXIT=0\n")
        T.run_node_job(path, name, smi=smi, engine=engine, setup=setup, node_log=str(log))
        sealed[name] = Path(T.seal(_attempt(s, name), s, name)["sealed_path"])
    dirs = list(sealed.values())
    monkeypatch.setattr(J, "_code_diff", lambda old, new, repo: ["sweep2/t1_tasl/g1b_tasl.py"])
    first = _first_note_for(spec_path, spec)
    kw = dict(expected_amended_sha256=lib._sha_file(amended_path), read_main=_main_with(first=first))
    with pytest.raises(T.Stop, match="does not match the table"):          # the unchanged rule: one spec sha256
        T.assemble(dirs, amended, tmp_path / "plain", lib._sha_file(amended_path))
    with pytest.raises(J.Stop, match=J.JOIN_ROW):                           # not without the author row
        J.assemble_join(dirs, amended_path, spec_path, tmp_path / "norow",
                        **{**kw, "read_main": _main_with((), first)})
    # review round 1, M1: a predecessor that differs from the signed first note's spec (here only in paper.commit) or
    # a re-issued spec other than the expected one is refused
    variant = copy.deepcopy(spec)
    variant["paper"]["commit"] = "5" * 40
    variant_path = tmp_path / "variant_spec.json"
    variant_path.write_text(json.dumps(variant))
    with pytest.raises(J.Stop, match="signed first note"):
        J.assemble_join(dirs, amended_path, variant_path, tmp_path / "v", **kw)
    with pytest.raises(J.Stop, match="not the one expected"):
        J.assemble_join(dirs, amended_path, spec_path, tmp_path / "w", **{**kw, "expected_amended_sha256": "0" * 64})
    unsealed = _fake_record(tmp_path / "runs_fmnist_1", "mlgym_fmnist", lib._sha_file(spec_path))
    rec = json.loads((unsealed / "job_record.json").read_text())
    (unsealed / "job_record.json").write_text(json.dumps({**rec, "stop_class": "infrastructure", "attempt": 1,
                                                          "stop": "STOP: data manifest"}))
    man = J.assemble_join(dirs, amended_path, spec_path, tmp_path / "run", unsealed=[unsealed], **kw)
    assert man["join"]["paper_commits"] == {"predecessor": spec["paper"]["commit"], "spec": "4" * 40}
    assert man["join"]["job_code_files_differing"] == ["sweep2/t1_tasl/g1b_tasl.py"]
    assert man["join"]["unsealed_attempts_not_used"][0]["node"] == "mlgym_fmnist"
    assert man["join"]["nodes_under_predecessor"] == sorted(first_note)
    assert sorted(man["join"]["nodes_under_spec"]) == sorted(set(sealed) - set(first_note))
    assert {j["node"] for j in man["jobs"]} == {n["node"] for n in spec["nodes"]}
    assert {j["spec_sha256"] for j in man["jobs"]} == {lib._sha_file(spec_path), lib._sha_file(amended_path)}
    def coverage_only(run_dir, s, root):         # g1b_lib.summarise's own checks on the assembly, before e1_report
        a = json.loads((Path(run_dir) / "ASSEMBLY.json").read_text())
        assert a["runs_sha256"] == lib._sha_file(Path(run_dir) / "runs.jsonl")
        assert a["spec_json_sha256"] == hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
        rows = lib._rows(Path(run_dir) / "runs.jsonl")
        want = {(n["node"], r["config"], r["condition"], r["train_seed"], r["split_seed"]) for n in s["nodes"]
                for part in lib.PARTS for r in lib.expected_runs(4, part[1], part[2])}
        assert {(r["node"], r["config"], r["condition"], r["train_seed"], r["split_seed"]) for r in rows} == want
        assert len(rows) == len(want)
        return {"verdicts": {n["node"]: {} for n in s["nodes"]}}
    monkeypatch.setattr(T.L, "summarise", coverage_only)
    summary = T.summarise(tmp_path / "run", amended, ROOT)        # exact coverage of all seven nodes, one table
    assert summary["schema"] == T.SUMMARY_SCHEMA and set(summary["verdicts"]) == {n["node"] for n in spec["nodes"]}
    assert summary["hosts"]["mlab_cifar10"] == "TASL-7" and summary["hosts"]["mlab_imdb"] == "TASL-2"
    # a corrected node's attempt under the first spec is refused; so is an attempt of a third spec
    with pytest.raises(J.Stop, match="corrected data manifest"):
        J.assemble_join(dirs[:3] + [_fake_record(tmp_path / "f", "mlgym_fmnist", lib._sha_file(spec_path))] + dirs[4:],
                        amended_path, spec_path, tmp_path / "r2", **kw)
    with pytest.raises(J.Stop, match="neither the predecessor"):
        J.assemble_join(dirs[:-1] + [_fake_record(tmp_path / "g", "mlgym_cifar10", "9" * 64)], amended_path,
                        spec_path, tmp_path / "r3", **kw)
    with pytest.raises(J.Stop, match="same file"):
        J.assemble_join(dirs, spec_path, spec_path, tmp_path / "r4", **kw)


def test_the_job_code_difference_of_the_two_paper_commits():
    """The joined row's two code versions: between the first note's paper commit and the chain base, the job path
    changes only in the autoresearch-only branches of g1b_tasl.py, the cross-check kind of t1_tasl_node.sh and the
    AR environment's freeze file (g1b_lib.py and r1/noise unchanged)."""
    t = _table()
    first = T._note_fields((ROOT / J.FIRST_NOTE).read_bytes())
    files = J._code_diff(first["paper_commit"], t["base"], ROOT)
    assert set(files) <= {"sweep2/t1_tasl/g1b_tasl.py", "sweep2/t1_tasl/t1_tasl_node.sh",
                          "sweep2/g1b/env/ar-cond7a.freeze.txt"}, files
    assert "sweep2/g1b/g1b_lib.py" not in files and not any(f.startswith("r1/noise") for f in files)


def _fake_record(d: Path, node: str, sha: str) -> Path:
    d.mkdir(parents=True)
    (d / "job_record.json").write_text(json.dumps({"node": node, "spec_sha256": sha}))
    return d


def test_gated_join_runs_the_crosscheck_gate_first(job, tmp_path, monkeypatch):
    """The R1-T1-TASL-ENV gate of g1b_crosscheck.assemble_gated, unchanged, in front of the joined assembly."""
    import test_t1_tasl_crosscheck as XT
    spec, spec_path = job[0], job[1]
    root = tmp_path / "repo"
    g1b = root / "sweep2/t1_tasl/g1b_tasl_spec.json"
    g1b.parent.mkdir(parents=True)
    g1b.write_text(json.dumps(_amend(spec)))
    xc = copy.deepcopy(XT.XC_SHIPPED)
    xc["g1b_spec"]["sha256"] = lib._sha_file(g1b)
    xc["run_id"] = spec["run_id"] + "-xc2"
    xc_path = root / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc_path.write_text(json.dumps(xc))
    monkeypatch.setattr(T, "REPO_ROOT", root)
    repo = {"root": root, "g1b": g1b, "xc": xc, "xc_path": xc_path, "job": job}
    paths, attempts, main = XT._verdicts(repo, tmp_path, "preassembly")
    called = {}

    def fake_join(dirs, amended_path, predecessor_path, dest, *, expected_amended_sha256, unsealed, read_main):
        called.update(dirs=dirs, amended=Path(amended_path), predecessor=Path(predecessor_path),
                      expected=expected_amended_sha256)
        Path(dest).mkdir(parents=True)
        (Path(dest) / "runs.jsonl").write_text("{}\n")
        (Path(dest) / "ASSEMBLY.json").write_text('{"jobs": []}\n')
        return {"jobs": []}
    monkeypatch.setattr(J, "assemble_join", fake_join)
    sealed = [attempts[n][0] for n in XT.TASL7_NODES]
    t2 = [attempts[n][1] for n in XT.TASL7_NODES]
    out = J.assemble_gated_join(xc_path, tmp_path / "dest", sealed, paths, t2, spec_path, read_main=main.get)
    assert called["amended"] == g1b and called["predecessor"] == spec_path
    assert called["expected"] == xc["g1b_spec"]["sha256"]
    gate = json.loads((tmp_path / "dest" / "crosscheck_gate.json").read_text())
    assert gate == out["crosscheck_gate"] and gate["g1b_spec_sha256"] == xc["g1b_spec"]["sha256"]
    monkeypatch.setattr(T, "summarise", lambda run_dir, s, r: {"ok": True})
    assert X.summarise_gated(xc_path, tmp_path / "dest", tmp_path) == {"ok": True}
    xc_paths, _, xc_main = XT._verdicts(repo, tmp_path / "x", "xc")
    called.clear()
    with pytest.raises(J.Stop, match="not a step-2 PASS"):
        J.assemble_gated_join(xc_path, tmp_path / "d2", sealed, xc_paths, t2, spec_path, read_main=xc_main.get)
    with pytest.raises(J.Stop, match="needs its G.1b TASL-7 attempt"):
        J.assemble_gated_join(xc_path, tmp_path / "d3", sealed[1:], paths, t2, spec_path, read_main=main.get)
    assert not called


def _summary(path: Path, schema: str, run_id: str, nodes, gate=True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": schema, "label": T.ENGINEERING_ONLY, "run_id": run_id,
                                "assembly_sha256": "a" * 64,
                                "verdicts": {n: {"qualifies_D21": True} for n in nodes}}))
    if gate:
        (path.parent / "crosscheck_gate.json").write_text(json.dumps({"schema": X.GATE_SCHEMA,
                                                                       "assembly_json_sha256": "a" * 64}))
    return path


def test_the_autoresearch_floor_joins_by_node(tmp_path):
    split = ROOT / J.SPLIT_REL
    eight = sorted(json.loads(split.read_text())["t1"]["nodes"])
    seven = [n for n in eight if n != "autoresearch_fixedtokens"]
    s7 = _summary(tmp_path / "seven" / "summary.json", T.SUMMARY_SCHEMA, "g1b-tasl-20261121-b", seven)
    sar = _summary(tmp_path / "ar" / "summary.json", T.AR_SUMMARY_SCHEMA, "g1b-ar-tasl-20261122-a",
                   ["autoresearch_fixedtokens"], gate=False)
    out = J.noise_floor_by_node(s7, sar, split)
    assert sorted(out["nodes"]) == eight and out["nodes"]["autoresearch_fixedtokens"]["run_id"] == "g1b-ar-tasl-20261122-a"
    assert {out["nodes"][n]["run_id"] for n in seven} == {"g1b-tasl-20261121-b"}
    with pytest.raises(J.Stop, match="both"):
        J.noise_floor_by_node(s7, _summary(tmp_path / "x" / "s.json", T.AR_SUMMARY_SCHEMA, J.AR_RUN_ID, ["mlab_imdb"]),
                              split)
    with pytest.raises(J.Stop, match="split file"):
        J.noise_floor_by_node(_summary(tmp_path / "s6" / "s.json", T.SUMMARY_SCHEMA, J.SEVEN_RUN_ID, seven[1:]), sar,
                              split)
    with pytest.raises(J.Stop, match="summary of run"):            # review round 1, m6: the expected run ids
        J.noise_floor_by_node(_summary(tmp_path / "o" / "s.json", T.SUMMARY_SCHEMA, "g1b-tasl-other", seven), sar,
                              split)
    with pytest.raises(J.Stop, match="cross-check gate"):          # the seven-node row came through the gate
        J.noise_floor_by_node(_summary(tmp_path / "ng" / "s.json", T.SUMMARY_SCHEMA, J.SEVEN_RUN_ID, seven,
                                       gate=False), sar, split)
    with pytest.raises(J.Stop, match="is not a"):
        J.noise_floor_by_node(sar, s7, split)                         # kinds swapped
    assert J.main(["floor-by-node", str(s7), str(sar), "--split", str(split)]) == 0


# ===================================================================================== the builder's guards
def test_builder_refuses_a_dirty_worktree(tmp_path):
    """Round-2 m4: ``build`` refuses a dirty worktree before it resets the branch."""
    import build_launch_chain as B
    tip = _git(ROOT, "rev-parse", "HEAD")
    origin, work = _sparse_clone(tmp_path, tip)
    _git(work, "checkout", "-q", "main")
    (work / "sweep2/t1_tasl/zz_local.txt").write_text("x\n")
    cfg = ROOT / "docs/r1/reports/tasl_chain_20261122/build_config.json"
    with pytest.raises(SystemExit, match="must be clean"):
        B.cli(["build", str(cfg), "--worktree", str(work)])
    assert _git(work, "rev-parse", "HEAD") == tip


def test_publication_check_passes_the_filled_notes_and_refuses_a_fill_left_in(tmp_path, monkeypatch):
    """Chain review round 2 m1 / confirmation C1: the field-scoped scan passes every draft once its open fields are
    filled (the amendment's PENDING P7 and the drafts' prose included) and refuses a P4 signed as PASS with the
    erratum's <FILL> left in, a P4 without the erratum clause, and an unfilled census_erratum. Since the reviewed erratum
    record is cited, the drafts pass as shipped once signed."""
    monkeypatch.setattr(J, "_fetch_origin", lambda: True)              # the CLI's origin/main: the record published
    monkeypatch.setattr(J, "_main_erratum", lambda: ER)
    monkeypatch.setattr(J, "_main_sha256", lambda rel: ER["sha256"] if rel == ER["record"] else None)
    amend = (PROP / "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md").read_text()
    note2 = (PROP / "G1B_T1_TASL_NOTE2_DRAFT_20261121.md").read_text()
    for name, text in (("a", amend), ("n", note2)):
        assert "PENDING" in text                                # a plain grep would always refuse these
        ok = _signed(text, tmp_path / name, "g1b_t1_tasl_20261123.md").read_text()
        assert J.publication_check(ok, p4=True) == []
        assert J.publication_check(_signed(text, tmp_path / (name + "f"), "g1b_t1_tasl_20261123.md", P4=P4_FILLED)
                                   .read_text(), p4=True) == []
        assert J.publication_check(_signed(text, tmp_path / (name + "u"), "g1b_t1_tasl_20261123.md",
                                           P4="PENDING — census erratum record <FILL: path>").read_text(), p4=True)
        left = _signed(text, tmp_path / (name + "l"), "g1b_t1_tasl_20261123.md",
                       P4="PASS — docs/r1/reviews/T1_TASL_REVIEW_20261121.md; census erratum record <FILL: path>")
        assert any("field still to fill: P4:" in b for b in J.publication_check(left.read_text(), p4=True))
        assert J.main(["publication-check", str(left), "--p4"]) == 2
        gone = _signed(text, tmp_path / (name + "g"), "g1b_t1_tasl_20261123.md",       # the erratum clause deleted
                       P4="PASS — docs/r1/reviews/T1_TASL_REVIEW_20261121.md")
        assert J.publication_check(gone.read_text(), p4=True) == [
            "P4 must cite 'census erratum record docs/r1/… sha256 <64 hex>'"]
        spaced = ok.replace("\nP4: PASS", "\nP4 : PASS").replace("P4 : PASS", "P4 : PASS <FILL x>", 1)
        assert any("P4 :" in b for b in J.publication_check(spaced))        # key\s*: as the parser reads it
        signed = _signed(text, tmp_path / (name + "m"), "g1b_t1_tasl_20261123.md")
        assert J.main(["publication-check", str(signed), "--p4"]) == 0
    for draft, name in (("G1B_XC_NOTE_REISSUE_DRAFT_20261122.md", "g1b_xc_t1_tasl_20261123.md"),
                        ("G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md", "g4_t1_tasl_20261123.md")):
        text = (PROP / draft).read_text()
        assert J.main(["publication-check", str(_signed(text, tmp_path / draft, name))]) == 0
        assert J.publication_check(text, main_sha256=lambda rel: ER["sha256"]) == []
        unfilled = _signed(text, tmp_path / (draft + "u"), name, census_erratum="<FILL: the record>").read_text()
        assert J.publication_check(unfilled) and "census_erratum" in J.publication_check(unfilled)[0]


def test_publication_check_requires_the_cited_record_bytes_on_main(tmp_path, monkeypatch):
    """Chain review round 3, M1/m2: the erratum record cited in P4 or census_erratum must be on origin/main with the
    cited sha256 (the bytes its review fixes); a missing record or other bytes refuse publication."""
    amend = _signed((PROP / "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md").read_text(), tmp_path / "a",
                    "g1b_t1_tasl_20261123.md")
    g4 = _signed((PROP / "G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md").read_text(), tmp_path / "g",
                 "g4_t1_tasl_20261123.md")
    assert J.publication_check(amend.read_text(), p4=True, main_sha256=lambda rel: ER["sha256"]) == []
    gone = J.publication_check(amend.read_text(), p4=True, main_sha256=lambda rel: None)
    assert gone == [f"P4 cites {ER['record']}, which is not on origin/main"]
    other = J.publication_check(g4.read_text(), main_sha256=lambda rel: "f" * 64)
    assert other == [f"census_erratum cites {ER['record']} sha256 {ER['sha256'][:12]}…, origin/main has ffffffffffff…"]
    monkeypatch.setattr(J, "_fetch_origin", lambda: True)
    monkeypatch.setattr(J, "_main_erratum", lambda: ER)
    monkeypatch.setattr(J, "_main_sha256", lambda rel: "f" * 64)
    assert J.main(["publication-check", str(g4)]) == 2
    # chain review round 4, m2: a sha256 edited to match changed bytes on main is still not the reviewed one
    edited = _signed(g4.read_text(), tmp_path / "e", "g4_t1_tasl_20261123.md",
                     census_erratum=f"{ER['record']} sha256 " + "f" * 64)
    assert J.main(["publication-check", str(edited)]) == 2
    assert J.publication_check(edited.read_text(), main_sha256=lambda rel: "f" * 64, erratum=ER) == [
        f"census_erratum cites {ER['record']} sha256 ffffffffffff…, not the reviewed {ER['sha256'][:12]}… the chain names"]
    assert J.publication_check(edited.read_text(), main_sha256=lambda rel: "f" * 64) == []   # without the chain's
    monkeypatch.setattr(J, "_main_erratum", lambda: None)              # the chain not yet published
    assert J.main(["publication-check", str(g4)]) == 2
    monkeypatch.setattr(J, "_main_erratum", lambda: ER)
    monkeypatch.setattr(J, "_fetch_origin", lambda: False)             # round 4, m1: a failed fetch refuses
    monkeypatch.setattr(J, "_main_sha256", lambda rel: ER["sha256"])
    assert J.main(["publication-check", str(g4)]) == 2
    assert J._CITED.findall("see docs/r1/reviews/X.md and docs/r1/reports/y/R.md sha256 " + "a" * 64) == [
        ("docs/r1/reports/y/R.md", "a" * 64)]
