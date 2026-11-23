"""The G.1b cross-host check (sweep2/t1_tasl/g1b_crosscheck.py): spec validation, derived specs, the default-part job
on both hosts with fake host tools, seal, the comparison and its verdicts, and the launch note. Synthetic only."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import re
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
    verdict = X.compare(sealed["TASL-7"], sealed["TASL-2"], "mlab_cifar10", mode="xc", xc_path=repo["xc_path"])
    assert verdict["verdict"] == "PASS" and verdict["complete"] and len(verdict["rows"]) == 10
    assert set(verdict["sides"]) == {"TASL-7", "TASL-2"} and verdict["reason"] is None and verdict["mode"] == "xc"
    # the same attempts are not the pre-assembly pair (that needs the G.1b TASL-7 attempt)
    with pytest.raises(X.Stop, match="not the preassembly attempt on TASL-7"):
        X.compare(sealed["TASL-7"], sealed["TASL-2"], "mlab_cifar10", mode="preassembly", xc_path=repo["xc_path"])
    # the CLI writes the verdict once
    out = tmp_path / "verdict.json"
    cli = ["compare", str(repo["xc_path"]), "--mode", "xc", "--a", str(sealed["TASL-2"]), "--b",
           str(sealed["TASL-7"]), "--node", "mlab_cifar10", "--out", str(out)]
    assert X.main(cli) == 0
    assert json.loads(out.read_text())["verdict"] == "PASS"
    assert X.main(cli) == 2
    with pytest.raises(X.Stop, match="other host"):
        X.compare(sealed["TASL-2"], sealed["TASL-2"], "mlab_cifar10", mode="xc", xc_path=repo["xc_path"])
    # the wrapper's queries for t1_tasl_node.sh xc
    for host in X.CROSS_HOSTS:
        assert X.main(["cpus", str(repo["xc_path"]), "--node", "mlab_cifar10", "--host", host]) == 0
        assert X.main(["logdir", str(repo["xc_path"]), "--node", "mlab_cifar10", "--host", host]) == 0
    with pytest.raises(X.Stop, match="not a cross-check job"):
        X.derived_spec(T.load_spec(repo["g1b"]), repo["xc"], "mlab_imdb", "TASL-2")


def _sealed(dirpath: Path, host: str, rows: list[dict], *, run_id: str, spec_sha256: str, harness: str,
            node="mlab_cifar10", stop_class=None, attempt=1) -> Path:
    """A sealed attempt in the g1b_tasl seal layout (<...>/attempt-N/)."""
    dirpath = dirpath / f"attempt-{attempt}"
    dirpath.mkdir(parents=True)
    record = {"label": T.ENGINEERING_ONLY, "node": node, "run_id": run_id, "host": {"host": host},
              "spec_sha256": spec_sha256, "harness_commit": harness, "stop_class": stop_class, "attempt": attempt}
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
                                                           "node": node, "run_id": run_id, "host": host,
                                                           "attempt": attempt}))
    return dirpath


def _rows(metric=lambda k, cond: 0.5 + 0.004 * k, fail=None, node="mlab_cifar10", n=5):
    out = []
    for k in range(n):
        for cond in X.DEFAULT_CONDITIONS:
            failed = fail == (k, cond)
            out.append({"node": node, "config": f"c{k}", "condition": cond, "train_seed": None,
                        "split_seed": None, "metric": None if failed else metric(k, cond), "success": not failed,
                        "failure": "divergent:timeout" if failed else None, "isolation": dict(GATE)})
    return out


def _pair(repo, tmp_path, a_rows, b_rows, mode="xc", node="mlab_cifar10", **over):
    """The two sealed attempts the mode names, with the run ids and spec sha256s it expects."""
    xc, g1b, _ = X.load_xc(repo["xc_path"])
    want = X.expected_sides(xc, g1b, node, mode)
    harness = g1b["harness"]["commit"]
    a = _sealed(tmp_path / "t7", "TASL-7", a_rows, run_id=want["TASL-7"][0], spec_sha256=want["TASL-7"][1],
                harness=harness, node=node, **over.get("TASL-7", {}))
    b = _sealed(tmp_path / "t2", "TASL-2", b_rows, run_id=want["TASL-2"][0], spec_sha256=want["TASL-2"][1],
                harness=harness, node=node, **over.get("TASL-2", {}))
    return a, b


@pytest.mark.parametrize("case,verdict,reason", [
    ("identical", "PASS", None),
    ("last_bit", "STOP", "cross_host_mismatch"),       # a metric differing in its last bit is not identical
    ("failure_both_same", "PASS", None),               # the same failure on both hosts is an identical outcome
    ("failure_one_side", "STOP", "cross_host_mismatch"),
    ("missing_row", "STOP", "incomplete"),
    ("missing_config_both", "STOP", "incomplete"),     # c4 absent on both sides is not "complete"
    ("nondeterministic", "STOP", "nondeterministic:TASL-7,TASL-2"),
])
def test_compare_verdicts(repo, tmp_path, case, verdict, reason):
    a_rows, b_rows = _rows(), _rows()
    if case == "last_bit":                  # both conditions of c1 on TASL-2: deterministic there, not identical
        for i in (2, 3):
            b_rows[i]["metric"] = a_rows[i]["metric"] + 1e-15
    elif case == "failure_both_same":
        a_rows, b_rows = _rows(fail=(2, "default")), _rows(fail=(2, "default"))
        for rows in (a_rows, b_rows):
            rows[5]["metric"], rows[5]["success"], rows[5]["failure"] = None, False, "divergent:timeout"
    elif case == "failure_one_side":
        for i in (4, 5):                    # c2 fails in both conditions on TASL-2 only
            b_rows[i]["metric"], b_rows[i]["success"], b_rows[i]["failure"] = None, False, "divergent:timeout"
    elif case == "missing_row":
        b_rows = b_rows[:-1]
    elif case == "missing_config_both":
        a_rows, b_rows = _rows(n=4), _rows(n=4)
    elif case == "nondeterministic":
        a_rows = _rows(metric=lambda k, c: 0.5 + 0.004 * k + (1e-6 if c == "default_repeat" else 0))
        b_rows = copy.deepcopy(a_rows)
    a, b = _pair(repo, tmp_path, a_rows, b_rows)
    out = X.compare(a, b, "mlab_cifar10", mode="xc", xc_path=repo["xc_path"])
    assert (out["verdict"], out["reason"]) == (verdict, reason), out
    if reason == "cross_host_mismatch":
        assert "re-measured on TASL-2" in out["on_stop"] and "XC-REMEASURE" in out["on_stop"]
    elif reason and reason.startswith("nondeterministic"):
        assert "second draw" in out["on_stop"] and "re-measured" not in out["on_stop"]


def test_compare_refuses_attempts_it_was_not_given(repo, tmp_path):
    """M1: the run ids, spec sha256s and harness the mode names; the receipt's host and attempt; the row node; sums
    listing exactly out.tar and job_record.json; sealed (a receipt) and complete; one regular runs.jsonl in the tar."""
    xc, g1b, _ = X.load_xc(repo["xc_path"])
    want = X.expected_sides(xc, g1b, "mlab_cifar10", "xc")
    harness = g1b["harness"]["commit"]
    good7 = _sealed(tmp_path / "g7", "TASL-7", _rows(), run_id=want["TASL-7"][0], spec_sha256=want["TASL-7"][1],
                    harness=harness)
    cmp = lambda a, b: X.compare(a, b, "mlab_cifar10", mode="xc", xc_path=repo["xc_path"])  # noqa: E731

    def t2(name, **kw):
        args = dict(run_id=want["TASL-2"][0], spec_sha256=want["TASL-2"][1], harness=harness)
        args.update(kw)
        rows = args.pop("rows", _rows())
        return _sealed(tmp_path / name, "TASL-2", rows, **args)
    assert cmp(good7, t2("ok"))["verdict"] == "PASS"
    with pytest.raises(X.Stop, match="not the xc attempt on TASL-2"):
        cmp(good7, t2("rid", run_id="other-TASL-2"))
    with pytest.raises(X.Stop, match="not the xc attempt on TASL-2"):
        cmp(good7, t2("spec", spec_sha256="0" * 64))
    with pytest.raises(X.Stop, match="not the pin"):
        cmp(good7, t2("harness", harness="0" * 40))
    with pytest.raises(X.Stop, match="names node"):
        cmp(good7, t2("node", rows=_rows() + [{**_rows()[0], "node": "mlab_imdb"}]))
    d = t2("receipt_host")
    rec = json.loads((d / "SEAL_RECEIPT.json").read_text())
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({**rec, "host": "TASL-7"}))
    with pytest.raises(X.Stop, match=r"receipt does not bind .*host"):
        cmp(good7, d)
    d = t2("receipt_attempt")
    (d / "SEAL_RECEIPT.json").write_text(json.dumps({**rec, "attempt": 2, "run_id": want["TASL-2"][0]}))
    with pytest.raises(X.Stop, match=r"receipt does not bind .*attempt"):
        cmp(good7, d)
    d = t2("sums")
    (d / "SHA256SUMS").write_text(f"{_sha(d / 'job_record.json')}  job_record.json\n")
    with pytest.raises(X.Stop, match="must list exactly"):
        cmp(good7, d)
    d = t2("nosums")
    (d / "SHA256SUMS").rename(tmp_path / "moved_sums")
    with pytest.raises(X.Stop, match="has no SHA256SUMS"):
        cmp(good7, d)
    d = t2("unsealed")
    (d / "SEAL_RECEIPT.json").rename(tmp_path / "moved_receipt.json")
    with pytest.raises(X.Stop, match="not sealed"):
        cmp(good7, d)
    with pytest.raises(X.Stop, match="not a complete"):
        cmp(good7, t2("infra", stop_class="infrastructure"))
    d = t2("tamper")
    (d / "job_record.json").write_text((d / "job_record.json").read_text().replace('"attempt": 1', '"attempt":  1'))
    with pytest.raises(X.Stop, match="SHA256SUMS"):
        cmp(good7, d)
    d = t2("dup")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for _ in range(2):
            data = b"{}\n"
            info = tarfile.TarInfo("out/default/runs.jsonl")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    (d / "out.tar").write_bytes(buf.getvalue())
    (d / "SHA256SUMS").write_text("".join(f"{_sha(d / n)}  {n}\n" for n in ("out.tar", "job_record.json")))
    with pytest.raises(X.Stop, match="duplicate members"):
        cmp(good7, d)
    (d / "out.tar").write_bytes(b"not a tar")
    (d / "SHA256SUMS").write_text("".join(f"{_sha(d / n)}  {n}\n" for n in ("out.tar", "job_record.json")))
    with pytest.raises(X.Stop, match="cannot be read"):
        cmp(good7, d)
    bad = _rows()
    bad[0]["isolation"] = {**GATE, "effective": False}
    with pytest.raises(lib.Stop, match="not effectively isolated"):
        cmp(good7, t2("gate", rows=bad))


def test_run_xc_restores_the_parts_after_a_stop_and_is_not_reentrant(repo, monkeypatch):
    seen = {}

    def boom(path, node, **kw):
        seen["parts"] = lib.PARTS
        with pytest.raises(X.Stop, match="not re-entrant"):
            X.run_xc(repo["xc_path"], "mlab_cifar10", "TASL-2")
        raise X.Stop("STOP: infrastructure")
    monkeypatch.setattr(T, "run_node_job", boom)
    before = (lib.PARTS, lib.merge_parts)
    with pytest.raises(X.Stop, match="infrastructure"):
        X.run_xc(repo["xc_path"], "mlab_cifar10", "TASL-2")
    assert len(seen["parts"]) == 1 and seen["parts"][0][0] == "default"
    assert (lib.PARTS, lib.merge_parts) == before and X._ACTIVE["run"] is False


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
    """As drafted it STOPs on approved; signed, it passes check_note against the spec in the checkout, and its P7 opens
    the TASL-7 gate. Since R1-T1-DATA-MANIFEST it binds the re-issued spec (paper_commit and spec_sha256 are the
    spec's), with the first note's run_id, harness and host row (test_t1_tasl_chain.py)."""
    draft = (ROOT / "docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md").read_text()
    spec_path = ROOT / "sweep2/t1_tasl/g1b_tasl_spec.json"
    spec = T.load_spec(spec_path)
    first = (ROOT / "docs/r1/authorizations/g1b_t1_tasl_20261121.md").read_text()
    pick = lambda text, k: next(l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith(k + ":"))  # noqa: E731
    for k in ("run_id", "harness_commit", "host_row"):
        assert pick(draft, k) == pick(first, k)
    assert pick(draft, "paper_commit") == spec["paper"]["commit"] and pick(draft, "spec_sha256") == _sha(spec_path)
    if re.search(r"^P4: PENDING", draft, re.M):      # the census erratum record, completed at signature
        draft = re.sub(r"^P4: PENDING — (.*)$", lambda m: "P4: PASS — " + m.group(1).replace("<FILL", "[filled"),
                       draft, flags=re.M)
    yes = lambda rel, raw: True  # noqa: E731
    p = tmp_path / "docs/r1/authorizations/g1b_t1_tasl_20261122.md"
    p.parent.mkdir(parents=True)
    p.write_text(draft)
    with pytest.raises(T.Stop, match="approved"):
        T.check_note(p, spec_path, spec["paper"]["commit"], on_main=yes, spec=spec)
    signed = _signed_copy(draft, tmp_path / "s", "g1b_t1_tasl_20261122.md")
    fields = T.check_note(signed, spec_path, spec["paper"]["commit"], on_main=yes, spec=spec)
    # M2: P7 is PENDING until the cross-check has run, so g1b_tasl.launch refuses the TASL-7 nodes with this draft
    assert fields["P7"].startswith("PENDING — ") and "<FILL" not in "".join(fields.values())
    with pytest.raises(T.Stop, match="P7 PASS"):
        T.launch(spec_path, signed, "mlab_cifar10", enable=True, on_main=yes)


def test_xc_note_draft_parses(tmp_path):
    """The first draft, signed as it was reviewed, binds the cross-check spec it was written for. Since
    R1-T1-DATA-MANIFEST re-issued the specs it no longer matches the checkout's (spec sha256s, run id), so the check
    refuses it; the re-issued note draft is tested in test_t1_tasl_chain.py."""
    draft = (ROOT / "docs/r1/proposals/G1B_XC_NOTE_DRAFT_20261121.md").read_text()
    xc_path = ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    xc, g1b, _ = X.load_xc(xc_path, ROOT)
    yes = lambda rel, raw: True  # noqa: E731
    with pytest.raises(X.Stop, match="not filled"):          # as drafted: unfilled (and unsigned)
        X.check_xc_note(_signed_copy(draft, tmp_path / "a", "g1b_xc_t1_tasl_20991231.md", approved="false"),
                        xc_path, xc, g1b, on_main=yes)
    signed = _signed_copy(draft, tmp_path / "b", "g1b_xc_t1_tasl_20991231.md", paper_commit=xc["paper"]["commit"],
                          xc_spec_sha256=_sha(xc_path), P4="PASS — docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md")
    fields = T._note_fields(signed.read_bytes())
    if fields["g1b_spec_sha256"] == xc["g1b_spec"]["sha256"]:      # before the re-issue
        assert X.check_xc_note(signed, xc_path, xc, g1b, on_main=yes)["run_id"] == xc["run_id"]
    else:
        with pytest.raises(X.Stop, match="g1b_spec_sha256|run_id"):
            X.check_xc_note(signed, xc_path, xc, g1b, on_main=yes)


TASL7_NODES = ("mlab_cifar10", "mlgym_breakout_minatar", "mlgym_cifar10")


def _verdicts(repo, tmp_path, mode, tamper=None):
    """Real compare verdicts for the three TASL-7 nodes, written under docs/r1/reports/ of the fake repository."""
    out, attempts = [], {}
    for node in TASL7_NODES:
        a, b = _pair(repo, tmp_path / mode / node, _rows(node=node), _rows(node=node), mode=mode, node=node)
        v = X.compare(a, b, node, mode=mode, xc_path=repo["xc_path"])
        if tamper:
            tamper(node, v)
        rel = f"docs/r1/reports/g1b_xc/{mode}_{node}.json"
        (repo["root"] / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo["root"] / rel).write_text(json.dumps(v, indent=1, sort_keys=True) + "\n")
        out.append(Path(rel))
        attempts[node] = (a, b)
    main = {p.as_posix(): (repo["root"] / p).read_bytes() for p in out}
    return out, attempts, main


def test_check_note2_requires_the_three_step1_passes(repo, tmp_path):
    from test_t1_tasl_g1b import _note
    spec = T.load_spec(repo["g1b"])
    paths, _, main = _verdicts(repo, tmp_path, "xc")
    xc_note = "docs/r1/authorizations/g1b_xc_t1_tasl_20991231.md"
    main[xc_note] = _xc_note(repo).read_bytes()          # the signed cross-check note, as check_xc_note reads it
    cites = "; ".join(f"{p.as_posix()} sha256 {_sha(repo['root'] / p)}" for p in paths)
    yes = lambda rel, raw: True  # noqa: E731
    p7 = f"PASS — R1-T1-TASL-ENV cross-host check under {xc_note}; step-1 verdicts PASS: {cites}"
    note = _note(tmp_path / "n", repo["g1b"], spec["paper"]["commit"], P7=p7)
    out = X.check_note2(note, repo["xc_path"], paths, on_main=yes, read_main=main.get)
    assert out["p7"] == "PASS" and sorted(out["verdicts"]) == sorted(TASL7_NODES) and out["mode"] == "strict"
    # before signature: --draft on the unsigned note, which is not on main (strict mode refuses it there)
    draft = _note(tmp_path / "dr", repo["g1b"], spec["paper"]["commit"], P7=p7, approved="false")
    assert X.check_note2(draft, repo["xc_path"], paths, draft=True, on_main=lambda rel, raw: False,
                         read_main=main.get)["mode"] == "draft"
    with pytest.raises(X.Stop, match="not committed byte-identically"):
        X.check_note2(draft, repo["xc_path"], paths, on_main=lambda rel, raw: False, read_main=main.get)
    with pytest.raises(X.Stop, match="draft mode is for the unsigned note"):
        X.check_note2(note, repo["xc_path"], paths, draft=True, read_main=main.get)
    with pytest.raises(X.Stop, match="template placeholder"):
        X.check_note2(_note(tmp_path / "ph", repo["g1b"], spec["paper"]["commit"],
                            P7=p7.replace("20991231", "<date>")), repo["xc_path"], paths, on_main=yes,
                      read_main=main.get)
    with pytest.raises(X.Stop, match="signed cross-check note"):
        X.check_note2(note, repo["xc_path"], paths, on_main=yes, read_main={**main, xc_note: None}.get)
    with pytest.raises(X.Stop, match="approved"):           # a cross-check note on main that is not signed
        X.check_note2(note, repo["xc_path"], paths, on_main=yes,
                      read_main={**main, xc_note: _xc_note(repo, approved="false").read_bytes()}.get)
    with pytest.raises(X.Stop, match="P7 must read PASS"):
        X.check_note2(_note(tmp_path / "a", repo["g1b"], spec["paper"]["commit"], P7="PENDING — later"),
                      repo["xc_path"], paths, on_main=yes, read_main=main.get)
    with pytest.raises(X.Stop, match="not filled"):
        X.check_note2(_note(tmp_path / "b", repo["g1b"], spec["paper"]["commit"], P7="PASS — R1-T1-TASL-ENV <FILL>"),
                      repo["xc_path"], paths, on_main=yes, read_main=main.get)
    with pytest.raises(X.Stop, match="must cite"):
        X.check_note2(_note(tmp_path / "c", repo["g1b"], spec["paper"]["commit"],
                            P7=f"PASS — R1-T1-TASL-ENV under {xc_note}"),
                      repo["xc_path"], paths, on_main=yes, read_main=main.get)
    with pytest.raises(X.Stop, match="not committed byte-identically"):
        X.check_note2(note, repo["xc_path"], paths, on_main=yes, read_main={xc_note: main[xc_note]}.get)
    with pytest.raises(X.Stop, match="step-1 verdicts for"):
        X.check_note2(note, repo["xc_path"], paths[:2], on_main=yes, read_main=main.get)
    bad_paths, _, bad_main = _verdicts(repo, tmp_path / "stop", "xc",
                                       tamper=lambda n, v: v.update(verdict="STOP") if n == "mlgym_cifar10" else None)
    bad_cites = "; ".join(f"{p.as_posix()} sha256 {_sha(repo['root'] / p)}" for p in bad_paths)
    bad_note = _note(tmp_path / "d", repo["g1b"], spec["paper"]["commit"],
                     P7=f"PASS — R1-T1-TASL-ENV under {xc_note}; {bad_cites}")
    bad_main[xc_note] = main[xc_note]
    with pytest.raises(X.Stop, match="not a step-1 PASS of mlgym_cifar10"):
        X.check_note2(bad_note, repo["xc_path"], bad_paths, on_main=yes, read_main=bad_main.get)


def test_assemble_requires_the_step2_pass_of_the_attempts_given(repo, tmp_path, monkeypatch):
    """B2: g1b_crosscheck assemble recomputes each TASL-7 node's pre-assembly comparison from the attempts given and
    requires it to equal the committed PASS verdict; only then the signed spec's assembly runs (unchanged)."""
    paths, attempts, main = _verdicts(repo, tmp_path, "preassembly")
    called = {}
    def fake_assemble(dirs, spec, dest, sha):
        called.update(dirs=dirs, sha=sha)
        Path(dest).mkdir(parents=True)
        (Path(dest) / "runs.jsonl").write_text("{}\n")
        (Path(dest) / "ASSEMBLY.json").write_text('{"jobs": []}\n')
        return {"nodes": len(dirs)}
    monkeypatch.setattr(T, "assemble", fake_assemble)
    others = [tmp_path / f"other_{i}" for i in range(4)]
    for i, d in enumerate(others):                  # the four TASL-2 nodes' sealed attempts (passed through)
        d.mkdir()
        (d / "job_record.json").write_text(json.dumps({"node": f"tasl2_node_{i}"}))
    sealed = [attempts[n][0] for n in TASL7_NODES] + others
    t2 = [attempts[n][1] for n in TASL7_NODES]
    out = X.assemble_gated(repo["xc_path"], tmp_path / "dest", sealed, paths, t2, read_main=main.get)
    assert called["sha"] == repo["xc"]["g1b_spec"]["sha256"] and len(called["dirs"]) == 7
    gate = json.loads((tmp_path / "dest" / "crosscheck_gate.json").read_text())
    assert sorted(gate["nodes"]) == sorted(TASL7_NODES) and out["crosscheck_gate"] == gate
    assert gate["runs_jsonl_sha256"] == _sha(tmp_path / "dest" / "runs.jsonl")
    # summarise only a run carrying a matching gate record
    monkeypatch.setattr(T, "summarise", lambda run_dir, spec, root: {"summarised": str(run_dir)})
    assert X.summarise_gated(repo["xc_path"], tmp_path / "dest", tmp_path)["summarised"] == str(tmp_path / "dest")
    (tmp_path / "dest" / "runs.jsonl").write_text("{}\n{}\n")
    with pytest.raises(X.Stop, match="does not bind this assembly"):
        X.summarise_gated(repo["xc_path"], tmp_path / "dest", tmp_path)
    (tmp_path / "plain").mkdir()
    with pytest.raises(X.Stop, match="not assembled through the cross-check gate"):
        X.summarise_gated(repo["xc_path"], tmp_path / "plain", tmp_path)
    called.clear()
    with pytest.raises(X.Stop, match="needs its G.1b TASL-7 attempt"):
        X.assemble_gated(repo["xc_path"], tmp_path / "d2", sealed[1:], paths, t2, read_main=main.get)
    with pytest.raises(X.Stop, match="not committed byte-identically"):
        X.assemble_gated(repo["xc_path"], tmp_path / "d3", sealed, paths, t2, read_main=lambda rel: None)
    xc_paths, _, xc_main = _verdicts(repo, tmp_path / "x", "xc")
    with pytest.raises(X.Stop, match="not a step-2 PASS"):
        X.assemble_gated(repo["xc_path"], tmp_path / "d4", sealed, xc_paths, t2, read_main=xc_main.get)
    # a committed PASS for other attempts than the ones given is not this comparison
    other_paths, other_attempts, other_main = _verdicts(repo, tmp_path / "o", "preassembly",
                                                        tamper=lambda n, v: v["sides"]["TASL-7"].update(
                                                            job_record_sha256="0" * 64))
    with pytest.raises(X.Stop, match="not the comparison of the attempts given"):
        X.assemble_gated(repo["xc_path"], tmp_path / "d5", sealed, other_paths, t2, read_main=other_main.get)
    assert not called


def test_wrapper_starts_the_crosscheck_job_in_the_scope(tmp_path):
    """B1: t1_tasl_node.sh xc queries cpus and logdir with --host and passes run-node ... --host."""
    from test_t1_tasl_g1b import _stub_env
    script = ROOT / "sweep2" / "t1_tasl" / "t1_tasl_node.sh"
    run_root = tmp_path / "runs" / "rid-xc-TASL-2"
    env = _stub_env(tmp_path, run_root, 0)
    res = subprocess.run(["bash", str(script), "xc", "xc.json", "mlgym_breakout_minatar", "xc_note.md", "TASL-2",
                          "--enable"], env=env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    stub = Path(env["STUB_DIR"])
    argv, cgroup, log = (stub / "run_node_argv").read_text().split("\n")
    assert argv == "run-node xc.json --node mlgym_breakout_minatar --note xc_note.md --host TASL-2 --enable"
    assert "--user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0" in (stub / "systemd_run_args").read_text()
    assert cgroup.startswith("/sys/fs/cgroup") and Path(log).parent == run_root / "_logs"
    for bad in (["xc", "xc.json", "mlab_cifar10", "xc_note.md", "--enable"], ["xc", "xc.json", "mlab_cifar10",
                                                                              "xc_note.md", "TASL-9"]):
        r = subprocess.run(["bash", str(script), *bad], env=env, capture_output=True, text=True)
        assert r.returncode == 2 and "host" in r.stderr


def test_wrapper_queries_the_real_crosscheck_cli(repo):
    """The two queries the wrapper makes, answered by g1b_crosscheck.py itself (derived spec, the host's cpus and the
    derived run's log directory)."""
    import contextlib
    import io as _io
    spec = T.load_spec(repo["g1b"])
    for host in X.CROSS_HOSTS:
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert X.main(["logdir", str(repo["xc_path"]), "--node", "mlgym_breakout_minatar", "--host", host]) == 0
        assert buf.getvalue().strip() == str(Path(spec["hosts"][host]["runs_root"]) / f"{repo['xc']['run_id']}-{host}"
                                             / "_logs")
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert X.main(["cpus", str(repo["xc_path"]), "--node", "mlgym_breakout_minatar", "--host", host]) == 0
        assert buf.getvalue().strip() == spec["hosts"][host]["cpus"]


def test_real_launch_binding_with_the_crosscheck_spec(tmp_path):
    """verify_launch_tasl with the cross-check spec as spec_path: the checkout's code must equal the cross-check
    spec's paper commit outside docs/ and that one file, so the signed G.1b spec and the code cannot change after it."""
    from test_t1_tasl_g1b import _git, _publish
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    _git(work, "checkout", "-q", "-b", "main")
    rows = T.PLAN_ROWS + ("R1-T1-TASL-ENV", "R1-G1B-TASL-DECISIONS")
    (work / "docs/r1").mkdir(parents=True)
    (work / "docs/r1/PLAN.md").write_text("".join(f"| {r} | x |\n" for r in rows))
    (work / "sweep2/t1_tasl").mkdir(parents=True)
    (work / "sweep2/t1_tasl/g1b_crosscheck.py").write_text("code = 1\n")
    (work / "sweep2/t1_tasl/g1b_tasl_spec.json").write_text('{"run_id": "g1b"}\n')
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "M (code)")
    m = _git(work, "rev-parse", "HEAD")
    xc_path = work / "sweep2/t1_tasl/g1b_crosscheck_spec.json"
    _publish(work, "L (the cross-check spec naming M, and its note)",
             {"sweep2/t1_tasl/g1b_crosscheck_spec.json": json.dumps({"paper": {"commit": m}}),
              "docs/r1/authorizations/g1b_xc_t1_tasl_20991231.md": f"paper_commit: {m}\n"})
    out = T.verify_launch_tasl(work, {"paper": {"commit": m}}, rows, spec_path=xc_path)
    assert out["paper_commit"] == m
    for rel in ("sweep2/t1_tasl/g1b_tasl_spec.json", "sweep2/t1_tasl/g1b_crosscheck.py"):
        _publish(work, f"change {rel}", {rel: "changed\n"})
        with pytest.raises(T.Stop, match="differs from the paper commit"):
            T.verify_launch_tasl(work, {"paper": {"commit": m}}, rows, spec_path=xc_path)


def test_check_note2_cli_on_the_unsigned_draft(tmp_path, capsys):
    """The CLI's --draft mode runs on the unsigned second-note draft against the signed spec (no main, approved false):
    as drafted it stops on P7 PENDING; strict mode stops earlier (the draft is not on main / not signed)."""
    draft = ROOT / "docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md"
    note = tmp_path / "docs/r1/authorizations/g1b_t1_tasl_20261122.md"
    note.parent.mkdir(parents=True)
    note.write_text(re.sub(r"^P4: PENDING — (.*)$", lambda m: "P4: PASS — " + m.group(1).replace("<FILL", "[filled"),
                           draft.read_text(), flags=re.M))
    xc = str(ROOT / "sweep2/t1_tasl/g1b_crosscheck_spec.json")
    args = ["check-note2", xc, "--note", str(note), "--verdict", "docs/r1/reports/x.json"]
    assert X.main(args + ["--draft"]) == 2
    assert "P7 must read PASS" in capsys.readouterr().err
    assert X.main(args) == 2
    assert "not committed byte-identically" in capsys.readouterr().err
