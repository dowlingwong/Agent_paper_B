"""The T1 node-expansion G.1b (R1-T1-NODE-EXPANSION): the built spec, the note draft and the launch commit
(docs/r1/reports/tasl_chain_20261122/g1bx_launch_table.json, built by sweep2/t1_tasl/build_g1bx_launch.py).

- the launch commit changes exactly the spec outside docs/ (plus the note draft), its spec's paper.commit is its
  parent (the base), and the spec differs from the base's template only in paper.commit; the note draft differs from
  the base's only in paper_commit and spec_sha256 and passes ``check-note-x --draft`` with every gate PENDING;
- it launches (``verify_launch_tasl``) from itself and a docs-only child, not from the tip (the tail adds code);
- at the base the published note would refuse the template spec;
- R1-TASL2-CPU: the table's CPU sets avoid 8-11 and name each replacement set's determinism check record.
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
import build_g1bx_launch as BX  # noqa: E402
import g1b_tasl as G  # noqa: E402

REP = ROOT / "docs/r1/reports/tasl_chain_20261122"
TABLE = REP / "g1bx_launch_table.json"
CFG = json.loads((REP / "g1bx_build_config.json").read_text())
SPEC_PATH = ROOT / BX.SPEC
NOTE = ROOT / BX.NOTE
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
        pytest.skip("no g1bx launch table in this checkout (the builder's last commit adds it)")
    t = json.loads(TABLE.read_text())
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", t["launch_commit"] + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("the g1bx launch commit is not in this repository")
    return t


def _show(commit: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"], capture_output=True, check=True).stdout


def test_built_spec_and_table():
    t = _table()
    spec = G.load_spec(SPEC_PATH)
    loaded = G.validate_spec(spec, launch=True)
    assert spec["paper"]["commit"] == t["paper_commit"] == t["base"] == CFG["base"]
    assert t["spec_sha256"] == G.L._sha_file(SPEC_PATH) and t["run_id"] == spec["run_id"] == "g1b-x-tasl-20261126-a"
    assert t["nodes"] == list(G.X_NODES) and t["harness_commits"] == {n["node"]: n["harness"]["commit"]
                                                                      for n in spec["nodes"]}
    assert t["projection"] == json.loads(json.dumps(loaded["projection"]))
    assert t["note_check_draft"] is True and set(t["gates_draft"].values()) == {"PENDING"}
    # R1-TASL2-CPU: no set contains CPUs 8-11; Titanic and Forest Cover on replacement sets, the four sets disjoint
    assert t["cpus"] == {"mlgym_titanic": "12-15", "mlgym_metamaze": "0-3", "gc7rc_etth1": "16-31",
                         "gc7rc_forestcover": "4-7"}
    assert t["census_cpus"] == {"mlgym_titanic": "8-11", "mlgym_metamaze": "0-3", "gc7rc_etth1": "16-31",
                                "gc7rc_forestcover": "8-11"}
    assert t["determinism_check_records"] == {n["node"]: n["cpu_replacement"]["determinism_check"]["record"]
                                              for n in spec["nodes"] if n.get("cpu_replacement")}
    assert set(t["gate_requires"]["mlgym_titanic"]) >= {"cpu_determinism"} and \
        set(t["gate_requires"]["gc7rc_forestcover"]) >= {"cpu_determinism"}


def test_launch_commit_and_template(tmp_path):
    t = _table()
    spec = G.load_spec(SPEC_PATH)
    lc, base = t["launch_commit"], t["base"]
    assert _git(ROOT, "rev-parse", f"{lc}^") == base == spec["paper"]["commit"]
    assert subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", lc, "HEAD"]).returncode == 0
    assert sorted(_git(ROOT, "diff", "--name-only", base, lc).splitlines()) == sorted([BX.SPEC, BX.NOTE])
    assert _show(lc, BX.SPEC) == SPEC_PATH.read_bytes() and _show(lc, BX.NOTE) == NOTE.read_bytes()
    template = json.loads(_show(base, BX.SPEC))
    fa, fb = _flat(template), _flat(spec)
    assert template["paper"]["commit"] == BX.TEMPLATE_PAPER
    assert sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)) == ["paper.commit"]
    draft_base = G._note_fields(_show(base, BX.NOTE))
    draft = G._note_fields(NOTE.read_bytes())
    assert sorted(k for k in set(draft) | set(draft_base) if draft.get(k) != draft_base.get(k)) == \
        ["paper_commit", "spec_sha256"]
    assert all(draft_base[k].startswith("PENDING") for k in ("paper_commit", "spec_sha256"))
    assert draft["spec_sha256"] == G.L._sha_file(SPEC_PATH) and draft["paper_commit"] == base
    target = tmp_path / "docs/r1/authorizations/g1b_x_t1_tasl_20991231.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(NOTE.read_bytes())
    fields = G.check_note_x(target, SPEC_PATH, spec=spec, draft=True)
    assert [k for k, v in fields.items() if v.upper().startswith("PENDING")] == \
        ["gate_mlgym_titanic", "gate_mlgym_metamaze", "gate_gc7rc_etth1", "gate_gc7rc_forestcover", "P2", "P4"]
    proj = G.validate_spec(G.load_spec(SPEC_PATH), launch=True)["projection"]
    assert {k: fields[k] for k in BX.rendered_keys(spec)} == BX.render(spec, proj)


def _docs_child(work: Path, commit: str) -> str:
    blob = subprocess.run(["git", "-C", str(work), "hash-object", "-w", "--stdin"], input="docs\n", text=True,
                          capture_output=True, check=True).stdout.strip()
    env = dict(os.environ, GIT_INDEX_FILE=str(work / ".git" / "idx_g1bx"))
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a], env=env, capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    run("read-tree", commit)
    run("update-index", "--add", "--cacheinfo", f"100644,{blob},docs/r1/zz_g1bx_child.md")
    return run("-c", "user.name=t", "-c", "user.email=t@t", "commit-tree", run("write-tree"), "-p", commit, "-m", "d")


def test_launches_from_the_launch_commit_only(tmp_path):
    t = _table()
    spec = G.load_spec(SPEC_PATH)
    tip = _git(ROOT, "rev-parse", "HEAD")
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", "--shared", str(ROOT), str(origin)], check=True,
                   capture_output=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", str(origin), str(work)], check=True,
                   capture_output=True)
    _git(work, "sparse-checkout", "set", "--no-cone", "/sweep2/t1_tasl/", "/sweep2/g1b/", "/docs/r1/PLAN.md")
    child = _docs_child(work, t["launch_commit"])
    merge = subprocess.run(["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", "commit-tree",
                            f"{tip}^{{tree}}", "-p", tip, "-p", child, "-m", "merge"], capture_output=True, text=True,
                           check=True).stdout.strip()
    _git(work, "push", "-q", "origin", f"{merge}:refs/heads/main")
    _git(work, "fetch", "-q", "origin")
    rows = G.X_PLAN_ROWS
    plan = (ROOT / "docs/r1/PLAN.md").read_text()
    if not all(re.search(rf"^\| {re.escape(r)} \|", plan, re.M) for r in rows):
        pytest.skip("the PLAN rows are not in this checkout")
    seen = {}
    for c in (t["launch_commit"], child, tip):
        _git(work, "checkout", "-q", "--detach", c)
        try:
            G.verify_launch_tasl(work, {"paper": {"commit": spec["paper"]["commit"]}}, rows,
                                 spec_path=work / BX.SPEC)
            seen[c] = "pass"
        except G.Stop as exc:
            seen[c] = str(exc)
    assert seen[t["launch_commit"]] == "pass" and seen[child] == "pass"
    assert seen[tip].startswith("STOP: the launch checkout differs from the paper commit outside docs/")
    # at the base the binding passes on code (the base is the paper commit), but the spec there is the template: the
    # published note binds the built spec's sha256 and paper commit and refuses it
    _git(work, "checkout", "-q", "--detach", t["base"])
    template = G.load_spec(work / BX.SPEC)
    signed = tmp_path / "docs/r1/authorizations/g1b_x_t1_tasl_20991231.md"
    signed.parent.mkdir(parents=True)
    signed.write_text(NOTE.read_text().replace("\napproved: false\n", "\napproved: true\n"))
    with pytest.raises(G.Stop, match="paper_commit|spec_sha256"):
        G.check_note_x(signed, work / BX.SPEC, spec=template, on_main=YES)
