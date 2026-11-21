"""The G.1b cross-host check (sweep2/t1_tasl/g1b_crosscheck.py): spec validation, derived specs, the default-part job
on both hosts with fake host tools, seal, the comparison and its verdicts, and the launch note. Synthetic only."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT / "sweep2" / "g1b"))
sys.path.insert(0, str(Path(__file__).parent))
import g1b_crosscheck as X  # noqa: E402
import g1b_tasl as T  # noqa: E402
import g1b_lib as lib  # noqa: E402
from test_t1_tasl_g1b import GATE, host_report, job, launch_spec  # noqa: E402,F401  (job: the fake-host fixture)

XC_SHIPPED = json.loads((ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json").read_text())


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture
def repo(job, tmp_path, monkeypatch):
    """A fake repository root holding the job fixture's G.1b spec at the committed path, and a cross-check spec."""
    spec, spec_path, calls, state, engine, smi, setup = job
    root = tmp_path / "repo"
    g1b = root / "sweep2/t1_tasl/g1b_tasl_spec.json"
    g1b.parent.mkdir(parents=True)
    g1b.write_bytes(spec_path.read_bytes())
    xc = copy.deepcopy(XC_SHIPPED)
    xc["g1b_spec"]["sha256"] = _sha(g1b)
    xc["run_id"] = spec["run_id"] + "-xc"
    xc_path = root / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc_path.write_text(json.dumps(xc))
    monkeypatch.setattr(T, "REPO_ROOT", root)
    return {"root": root, "g1b": g1b, "xc": xc, "xc_path": xc_path, "job": job}


def test_shipped_spec_binds_the_signed_g1b_spec():
    xc, g1b, path = X.load_xc(ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json", ROOT)
    assert xc["g1b_spec"]["sha256"] == _sha(ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json")
    assert sorted(xc["nodes"]) == sorted(n["node"] for n in g1b["nodes"] if n["host"] == "TASL-7")
    for node in xc["nodes"]:
        for host in X.CROSS_HOSTS:
            d = X.derived_spec(g1b, xc, node, host)
            assert d["run_id"] == f"{xc['run_id']}-{host}" and T.node_entry(d, node)["host"] == host
            others = [n for n in d["nodes"] if n["node"] != node]
            assert others == [n for n in g1b["nodes"] if n["node"] != node]           # nothing else changes
            assert d["harness"] == g1b["harness"] and d["envs"] == g1b["envs"]
    breakout = X.derived_spec(g1b, xc, "mlgym_breakout_minatar", "TASL-2")
    assert breakout["hosts"]["TASL-2"]["env_python"]["jax312"].endswith("envs/jax312/bin/python")


@pytest.mark.parametrize("edit,match", [
    (lambda x: x.update(label="EVIDENCE"), "ENGINEERING_ONLY"),
    (lambda x: x["g1b_spec"].update(sha256="0" * 64), "signed spec"),
    (lambda x: x.update(run_id="other-xc"), "safe"),
    (lambda x: x.update(nodes=["mlab_cifar10"]), "TASL-7 nodes"),
    (lambda x: x.update(hosts=["TASL-2", "TASL-7"]), "hosts must be"),
    (lambda x: x["env_python_additions"]["TASL-2"].update(torch312="/x/python"), "override"),
    (lambda x: x["env_python_additions"]["TASL-2"].update(nope="/x/python"), "declared env"),
    (lambda x: x.update(rule="none"), "R1-T1-TASL-ENV"),
    (lambda x: x["paper"].update(commit="abc"), "full commit"),
])
def test_spec_refusals(repo, edit, match):
    xc = copy.deepcopy(repo["xc"])
    edit(xc)
    repo["xc_path"].write_text(json.dumps(xc))
    with pytest.raises(X.Stop, match=match):
        X.load_xc(repo["xc_path"], repo["root"])


def test_breakout_on_tasl2_needs_the_env_addition(repo):
    xc = copy.deepcopy(repo["xc"])
    xc["env_python_additions"] = {}
    g1b = T.load_spec(repo["g1b"])
    with pytest.raises(X.Stop, match="needs jax312 on TASL-2"):
        X.derived_spec(g1b, xc, "mlgym_breakout_minatar", "TASL-2")
    assert X.derived_spec(g1b, xc, "mlgym_breakout_minatar", "TASL-7")


def test_default_part_on_both_hosts_seal_and_compare(repo, tmp_path):
    spec, spec_path, calls, state, engine, smi, setup = repo["job"]
    sealed = {}
    for host in X.CROSS_HOSTS:
        calls.clear()
        rec = X.run_xc(repo["xc_path"], "mlab_cifar10", host, smi=smi, engine=engine, setup=setup)
        assert rec["stop"] is None and rec["runs"] == {"expected": 10, "written": 10, "successful": 10,
                                                       "divergent": 0, "crosscheck_default_part": True}
        assert [c[c.index("--out") + 1].rsplit("/", 1)[1] for c in calls] == ["default"]   # default part only
        assert rec["host"]["host"] == host and rec["run_id"] == f"{repo['xc']['run_id']}-{host}"
        d = json.loads((Path(spec["hosts"][host]["runs_root"]) / rec["run_id"] / "_specs/mlab_cifar10.json").read_text())
        assert rec["spec_sha256"] == hashlib.sha256((json.dumps(d, indent=1, sort_keys=True) + "\n").encode()).hexdigest()
        job_dir = Path(spec["hosts"][host]["runs_root"]) / rec["run_id"] / "mlab_cifar10" / "attempt-1"
        receipt = T.seal(job_dir, d, "mlab_cifar10")
        sealed[host] = Path(receipt["sealed_path"])
    assert lib.PARTS[0][0] == "default" and len(lib.PARTS) == 4          # the parts are restored after the job
    verdict = X.compare(sealed["TASL-7"], sealed["TASL-2"], "mlab_cifar10")
    assert verdict["verdict"] == "PASS" and verdict["complete"] and len(verdict["rows"]) == 10
    assert set(verdict["sides"]) == {"TASL-7", "TASL-2"}
    # the CLI writes the verdict once
    out = tmp_path / "verdict.json"
    assert X.main(["compare", "--a", str(sealed["TASL-2"]), "--b", str(sealed["TASL-7"]), "--node", "mlab_cifar10",
                   "--out", str(out)]) == 0
    assert json.loads(out.read_text())["verdict"] == "PASS"
    assert X.main(["compare", "--a", str(sealed["TASL-2"]), "--b", str(sealed["TASL-7"]), "--node", "mlab_cifar10",
                   "--out", str(out)]) == 2
    with pytest.raises(X.Stop, match="other host"):
        X.compare(sealed["TASL-2"], sealed["TASL-2"], "mlab_cifar10")
    with pytest.raises(X.Stop, match="not a cross-check job"):
        X.derived_spec(T.load_spec(repo["g1b"]), repo["xc"], "mlab_imdb", "TASL-2")


def _sealed(dirpath: Path, host: str, rows: list[dict], *, node="mlab_cifar10", stop_class=None) -> Path:
    """A sealed attempt in the g1b_tasl seal layout."""
    dirpath.mkdir(parents=True)
    record = {"label": T.ENGINEERING_ONLY, "node": node, "run_id": f"r-{host}", "host": {"host": host},
              "spec_sha256": "s", "harness_commit": "h", "stop_class": stop_class, "attempt": 1}
    (dirpath / "job_record.json").write_text(json.dumps(record))
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        data = "".join(json.dumps(r) + "\n" for r in rows).encode()
        info = tarfile.TarInfo("out/default/runs.jsonl")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    (dirpath / "out.tar").write_bytes(buf.getvalue())
    (dirpath / "SHA256SUMS").write_text("".join(f"{_sha(dirpath / n)}  {n}\n" for n in ("out.tar", "job_record.json")))
    (dirpath / "SEAL_RECEIPT.json").write_text(json.dumps({"job_record_sha256": _sha(dirpath / "job_record.json"),
                                                           "node": node, "run_id": f"r-{host}"}))
    return dirpath


def _rows(metric=lambda k, cond: 0.5 + 0.004 * k, fail=None):
    out = []
    for k in range(5):
        for cond in X.DEFAULT_CONDITIONS:
            failed = fail == (k, cond)
            out.append({"node": "mlab_cifar10", "config": f"c{k}", "condition": cond, "train_seed": None,
                        "split_seed": None, "metric": None if failed else metric(k, cond), "success": not failed,
                        "failure": "divergent:timeout" if failed else None, "isolation": dict(GATE)})
    return out


@pytest.mark.parametrize("case,verdict", [
    ("identical", "PASS"),
    ("last_bit", "STOP"),               # a metric differing in its last bit is not identical
    ("failure_both_same", "PASS"),      # the same failure on both hosts is an identical outcome
    ("failure_one_side", "STOP"),
    ("missing_row", "STOP"),
    ("nondeterministic", "STOP"),
])
def test_compare_verdicts(tmp_path, case, verdict):
    a_rows, b_rows = _rows(), _rows()
    if case == "last_bit":
        b_rows[3]["metric"] = a_rows[3]["metric"] + 1e-15
    elif case == "failure_both_same":
        a_rows, b_rows = _rows(fail=(2, "default")), _rows(fail=(2, "default"))
        for rows in (a_rows, b_rows):
            rows[5]["metric"], rows[5]["success"], rows[5]["failure"] = None, False, "divergent:timeout"
    elif case == "failure_one_side":
        b_rows = _rows(fail=(2, "default"))
    elif case == "missing_row":
        b_rows = b_rows[:-1]
    elif case == "nondeterministic":
        a_rows = _rows(metric=lambda k, c: 0.5 + 0.004 * k + (1e-6 if c == "default_repeat" else 0))
        b_rows = copy.deepcopy(a_rows)
    a = _sealed(tmp_path / "a", "TASL-7", a_rows)
    b = _sealed(tmp_path / "b", "TASL-2", b_rows)
    out = X.compare(a, b, "mlab_cifar10")
    assert out["verdict"] == verdict, out
    if verdict == "STOP":
        assert "re-measured on TASL-2" in out["on_stop"]


def test_compare_refuses_unsealed_or_infrastructure_attempts(tmp_path):
    a = _sealed(tmp_path / "a", "TASL-7", _rows())
    b = _sealed(tmp_path / "b", "TASL-2", _rows(), stop_class="infrastructure")
    with pytest.raises(X.Stop, match="not a complete"):
        X.compare(a, b, "mlab_cifar10")
    c = _sealed(tmp_path / "c", "TASL-2", _rows())
    (c / "job_record.json").write_text((c / "job_record.json").read_text().replace('"h"', '"g"'))
    with pytest.raises(X.Stop, match="SHA256SUMS"):
        X.compare(a, c, "mlab_cifar10")
    bad = _rows()
    bad[0]["isolation"] = {**GATE, "effective": False}
    d = _sealed(tmp_path / "d", "TASL-2", bad)
    with pytest.raises(lib.Stop, match="not effectively isolated"):
        X.compare(a, d, "mlab_cifar10")


def _xc_note(repo, **over):
    g1b = T.load_spec(repo["g1b"])
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none",
              "paper_commit": repo["xc"]["paper"]["commit"], "xc_spec_sha256": _sha(repo["xc_path"]),
              "g1b_spec_sha256": repo["xc"]["g1b_spec"]["sha256"], "run_id": repo["xc"]["run_id"],
              "harness_commit": g1b["harness"]["commit"], "host_row": "R1-T1-TASL-ENV",
              "P1": "PASS — R1-T1-TASL-ENV cross-host check",
              "P2": f"PASS — {g1b['hosts']['TASL-2']['isolation_host_check']['record']}",
              "P3": f"PASS — {g1b['hosts']['TASL-7']['isolation_host_check']['record']}",
              "P4": "PASS — docs/r1/reviews/G1B_XC_REVIEW.md"}
    fields.update(over)
    p = repo["root"] / "docs/r1/authorizations/g1b_xc_t1_tasl_20991231.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    return p


def test_launch_needs_the_note_keys_host_records_and_binding(repo, monkeypatch):
    g1b = T.load_spec(repo["g1b"])
    reports = {f"docs/r1/reports/{h}_check.md": host_report(h).encode() for h in T.HOSTS}
    seen = []
    kw = dict(enable=True, on_main=lambda rel, raw: True, read_main=reports.get,
              launch_binding=lambda r, s, rows: seen.append((s, rows)) or {"bound": True},
              runner=lambda xc, node, host: {"node": node, "host": host})
    note = _xc_note(repo)
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    with pytest.raises(X.Stop, match="disabled"):
        X.launch_xc(repo["xc_path"], note, "mlab_cifar10", "TASL-2", **kw)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    out = X.launch_xc(repo["xc_path"], note, "mlab_cifar10", "TASL-2", **kw)
    assert out == {"node": "mlab_cifar10", "host": "TASL-2", "launch": {"bound": True}}
    assert seen[0][0] == {"paper": repo["xc"]["paper"]} and "R1-G1B-TASL-DECISIONS" in seen[0][1]
    with pytest.raises(X.Stop, match="not committed"):
        X.launch_xc(repo["xc_path"], note, "mlab_cifar10", "TASL-2", **{**kw, "on_main": lambda rel, raw: False})
    with pytest.raises(X.Stop, match="not on published main"):
        X.launch_xc(repo["xc_path"], note, "mlab_cifar10", "TASL-2", **{**kw, "read_main": lambda rel: None})
    for key, value, match in (("xc_spec_sha256", "0" * 64, "xc_spec_sha256"), ("g1b_spec_sha256", "1" * 64, "g1b_spec"),
                              ("run_id", "x", "run_id"), ("approved", "false", "approved"),
                              ("P2", "PASS — the TASL-2 check", "P2 must read PASS"),
                              ("harness_commit", g1b["harness"]["commit"][:8], "harness_commit")):
        bad = _xc_note(repo, **{key: value})
        with pytest.raises(X.Stop, match=match):
            X.launch_xc(repo["xc_path"], bad, "mlab_cifar10", "TASL-2", **kw)
    wrong = repo["root"] / "docs/r1/authorizations/g1b_t1_tasl_20991231.md"
    wrong.write_bytes(note.read_bytes())
    with pytest.raises(X.Stop, match="g1b_xc_t1_tasl_"):
        X.launch_xc(repo["xc_path"], wrong, "mlab_cifar10", "TASL-2", **kw)


def _signed_copy(text: str, tmp: Path, name: str, **fills) -> Path:
    """The draft as signed: approved true (unless given) and the named fields filled."""
    fills = {"approved": "true", **fills}
    out = []
    for line in text.splitlines(keepends=True):
        key = line.split(":", 1)[0]
        out.append(f"{key}: {fills[key]}\n" if key in fills else line)
    p = tmp / "docs/r1/authorizations" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(out))
    return p


def test_second_note_draft_parses_with_the_first_notes_binding(tmp_path):
    """As drafted it STOPs on approved; signed, it passes check_note against the signed spec with the first note's
    paper_commit, and its P7 opens the TASL-7 gate."""
    draft = (ROOT / "docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md").read_text()
    spec_path = ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json"
    spec = T.load_spec(spec_path)
    first = (ROOT / "docs/r1/authorizations/g1b_t1_tasl_20261121.md").read_text()
    pick = lambda text, k: next(l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith(k + ":"))  # noqa: E731
    for k in ("run_id", "paper_commit", "spec_sha256", "harness_commit", "host_row"):
        assert pick(draft, k) == pick(first, k)
    yes = lambda rel, raw: True  # noqa: E731
    p = tmp_path / "docs/r1/authorizations/g1b_t1_tasl_20261122.md"
    p.parent.mkdir(parents=True)
    p.write_text(draft)
    with pytest.raises(T.Stop, match="approved"):
        T.check_note(p, spec_path, spec["paper"]["commit"], on_main=yes, spec=spec)
    signed = _signed_copy(draft, tmp_path / "s", "g1b_t1_tasl_20261122.md")
    fields = T.check_note(signed, spec_path, spec["paper"]["commit"], on_main=yes, spec=spec)
    assert fields["P7"].startswith("PASS — ") and "R1-T1-TASL-ENV" in fields["P7"]


def test_xc_note_draft_parses(tmp_path):
    draft = (ROOT / "docs/r1/proposals/G1B_XC_NOTE_DRAFT_20261121.md").read_text()
    xc_path = ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc, g1b, _ = X.load_xc(xc_path, ROOT)
    yes = lambda rel, raw: True  # noqa: E731
    with pytest.raises(X.Stop, match="approved"):
        X.check_xc_note(_signed_copy(draft, tmp_path / "a", "g1b_xc_t1_tasl_20991231.md", approved="false"),
                        xc_path, xc, g1b, on_main=yes)
    signed = _signed_copy(draft, tmp_path / "b", "g1b_xc_t1_tasl_20991231.md", paper_commit=xc["paper"]["commit"],
                          xc_spec_sha256=_sha(xc_path), P4="PASS — docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md")
    fields = X.check_xc_note(signed, xc_path, xc, g1b, on_main=yes)
    assert fields["run_id"] == xc["run_id"] and fields["g1b_spec_sha256"] == xc["g1b_spec"]["sha256"]
