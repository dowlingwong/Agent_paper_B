"""The autoresearch-only G.1b spec on TASL-2 (sweep2/t1_tasl/g1b_tasl.py, schema g1b_tasl_ar_job/v1;
R1-G1B-NOTE2-DECISIONS NOTE2-AR A): its validation, the shared cap, the node job, its own assembly and summary, the
third note (strict and draft) and its launch; and the seven-node spec unchanged beside it.

Synthetic only: no GPU, no host, no run (the engine, nvidia-smi and the setup are replaced). AI-assisted.
"""
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
import g1b_tasl as T  # noqa: E402
import g1b_lib as lib  # noqa: E402
from test_t1_tasl_g1b import GATE, _write_part  # noqa: E402

AR_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_ar_spec.json"
AR_SHIPPED = json.loads(AR_PATH.read_text())
SEVEN_PATH = ROOT / "sweep2" / "t1_tasl" / "g1b_tasl_spec.json"
SEVEN = json.loads(SEVEN_PATH.read_text())
SIGNED_SEVEN_SHA = "060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465"   # the first note's spec
SEVEN_SHA = hashlib.sha256(SEVEN_PATH.read_bytes()).hexdigest()
# The launch chain of R1-T1-DATA-MANIFEST re-issues the seven-node spec in (a); the AR spec's re-binding, (d), is a later
# delivery (the TASL-2 host check at the AR pin STOPped). Until then the shipped AR spec binds the first note's spec and
# refuses (test below); the mechanics are tested on the shipped spec re-bound to the checkout's seven-node spec, which
# is the one change of that field (d) makes.
AR_DEFERRED = AR_SHIPPED["seven_node_spec"]["sha256"] == SIGNED_SEVEN_SHA != SEVEN_SHA
# After (d), the second delivery of the chain, the shipped AR spec is final: host-check sha256, paper.commit and the
# environment row filled (TASL-2 host check at 2d09f9a9 PASS; R1-G1B-AR-ENV amended by R1-G1B-AR-PY).
AR_FINAL = not lib._placeholder(AR_SHIPPED["hosts"]["TASL-2"]["isolation_host_check"]["sha256"])
AR = copy.deepcopy(AR_SHIPPED)
AR["seven_node_spec"]["sha256"] = SEVEN_SHA
UUID2 = SEVEN["hosts"]["TASL-2"]["gpu_uuid"]
NOTE_DRAFT = ROOT / "docs" / "r1" / "proposals" / "G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md"
ENV_ROW = "R1-G1B-AR-ENV"


def host_report(verdict="PASS", commit=None) -> str:
    return (f"# host check\nhost_check_host: TASL-2\nhost_check_harness_commit: {commit or AR['harness']['commit']}\n"
            f"host_check_items: 1-7 PASS\nhost_check_verdict: {verdict}\n")


def filled(tmp_path: Path | None = None) -> dict:
    """The shipped AR spec with its three signature-time fields filled; with tmp_path, the host paths moved there."""
    spec = copy.deepcopy(AR)
    spec["paper"]["commit"] = "3" * 40
    spec["env_decision"]["authority"] = f"{ENV_ROW} (AR-ENV A)"
    host = spec["hosts"]["TASL-2"]
    host["isolation_host_check"]["sha256"] = hashlib.sha256(host_report().encode()).hexdigest()
    if tmp_path is not None:
        for key in ("base", "harness_dir", "runs_root", "sealed_root"):
            host[key] = str(tmp_path / key)
        host["data_root"] = host["base"] + "/data"
    return spec


# ============================================================================================ spec
def test_seven_node_spec_is_the_signed_one_and_still_validates():
    """The seven-node spec in the checkout is the first note's (060aac91) or, after chain commit (a), its re-issue: the
    two corrected data manifests of R1-T1-DATA-MANIFEST and paper.commit (tests/test_t1_tasl_chain.py)."""
    if SEVEN_SHA != SIGNED_SEVEN_SHA:
        census = {"mlgym_fmnist": "8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c",
                  "mlgym_cifar10": "c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40"}
        values = {n["node"]: n["data_manifest_sha256"] for n in SEVEN["nodes"]}
        assert all(values[k] != v and re.fullmatch(r"[0-9a-f]{64}", values[k]) for k, v in census.items())
        assert SEVEN["run_id"] == "g1b-tasl-20261121-b"
    loaded = T.validate_spec(copy.deepcopy(SEVEN), launch=True)
    assert set(loaded["projection"]["estimate"]["per_node"]) == set(T.T1_NODES)
    assert "g1b_shared_cap" not in loaded["projection"]


def test_the_shipped_ar_spec_binds_the_seven_node_spec_or_refuses():
    """Until (d) re-binds it, the shipped AR spec names the first note's seven-node spec and refuses to validate against
    the re-issued one in the checkout: no AR launch from (a)–(c)."""
    if AR_DEFERRED:
        with pytest.raises(T.Stop, match="differs from the one the AR spec binds"):
            T.validate_spec(copy.deepcopy(AR_SHIPPED))
    else:
        assert AR_SHIPPED["seven_node_spec"]["sha256"] == SEVEN_SHA
        T.validate_spec(copy.deepcopy(AR_SHIPPED))


def test_the_seven_node_spec_refuses_autoresearch():
    spec = copy.deepcopy(SEVEN)
    spec["nodes"].append(copy.deepcopy(AR["nodes"][0]))
    with pytest.raises(T.Stop, match="joins G.1b only under its own spec"):
        T.validate_spec(spec)


def test_shipped_ar_spec_validates_and_refuses_launch_until_filled():
    loaded = T.validate_spec(copy.deepcopy(AR))
    p = loaded["projection"]
    assert loaded["run_id"] == "g1b-ar-tasl-20261122-a" and list(p["estimate"]["per_host_gpu_wall_hours"]) == ["TASL-2"]
    assert p["estimate"]["per_node"]["autoresearch_fixedtokens"]["runs"] == 460
    assert p["estimate"]["total_gpu_hours"] == round((460 * 218.951 + 900) / 3600, 3)        # 28.227
    shared = p["g1b_shared_cap"]
    assert shared["seven_node_spec"] == 28.262 and shared["crosscheck"] == 2.1
    assert shared["total_estimate"] == round(28.227 + 28.262 + 2.1, 3) and shared["sensitivity_within_cap"]
    if AR_FINAL:                                         # (d): launchable, within R1-G1B-CAP
        assert AR_SHIPPED["seven_node_spec"]["sha256"] == SEVEN_SHA and not AR_DEFERRED
        assert T.validate_spec(copy.deepcopy(AR_SHIPPED), launch=True)["projection"]["within_cap"]
        assert AR_SHIPPED["env_decision"]["authority"].startswith(ENV_ROW + " ")
    else:
        with pytest.raises(T.Stop, match="paper.commit"):
            T.validate_spec(copy.deepcopy(AR), launch=True)
    spec = filled()
    spec["env_decision"]["authority"] = "TODO: the PLAN row admitting the AR census environment"
    with pytest.raises(T.Stop, match="env_decision.authority"):
        T.validate_spec(spec, launch=True)
    spec = filled()
    spec["hosts"]["TASL-2"]["isolation_host_check"]["sha256"] = "TODO: x"
    with pytest.raises(T.Stop, match="isolation_host_check.sha256"):
        T.validate_spec(spec, launch=True)
    assert T.validate_spec(filled(), launch=True)["projection"]["within_cap"]


def test_ar_spec_pins_are_the_census_values():
    node = AR["nodes"][0]
    assert node["run_seconds"] == 218.951 and node["slowest_census_seconds"] == 255.916
    assert T.timeout_basis(AR, node) * 3 == pytest.approx(767.748)
    assert node["committed_pin_sha256"].startswith("147f0d35") and node["data_manifest_sha256"].startswith("ab7186d2")
    freeze = ROOT / "sweep2" / "g1b" / AR["envs"]["ar-cond7a"]["freeze"]
    assert lib._sha_file(freeze) == AR["envs"]["ar-cond7a"]["sha256"].lower()
    assert AR["envs"]["ar-cond7a"]["sha256"].startswith("11def6ad") and len(freeze.read_text().splitlines()) == 122


def _set(path, value):
    def edit(s):
        target = s
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
    return edit


@pytest.mark.parametrize("edit, match", [
    (lambda s: s.update(schema="g1b_tasl_job/v2"), "spec must be"),
    (_set(("envs",), {"torch312": SEVEN["envs"]["torch312"]}), "envs must be exactly ar-cond7a"),
    (_set(("envs", "ar-cond7a", "python"), "3.12.16"), "python must be 3.12.15"),
    (_set(("envs", "ar-cond7a", "sha256"), "0" * 64), "committed census freeze"),
    (lambda s: s["hosts"].update({"TASL-7": copy.deepcopy(SEVEN["hosts"]["TASL-7"])}), "hosts must be exactly"),
    (lambda s: s["nodes"].append(copy.deepcopy(SEVEN["nodes"][0])), "measures exactly"),
    (lambda s: s["nodes"][0].update(host="TASL-7"), "host must be one of"),
    (lambda s: s["nodes"][0].update(n_edits=5), "uniform"),
    (_set(("run_id",), SEVEN["run_id"]), "run_id must be the AR spec's own"),
    (_set(("run_id",), SEVEN["run_id"] + "-ar"), "run_id must be the AR spec's own"),
    (_set(("hosts", "TASL-2", "harness_dir"), SEVEN["hosts"]["TASL-2"]["harness_dir"]), "second checkout"),
    (_set(("hosts", "TASL-2", "harness_dir"), SEVEN["hosts"]["TASL-2"]["harness_dir"] + "/ar"), "second checkout"),
    (_set(("hosts", "TASL-2", "harness_dir"), "/home/dowling/r1_tracks"), "second checkout"),
    (_set(("hosts", "TASL-2", "gpu_uuid"), "GPU-11111111-2222-3333-4444-555555555555"), "one card per host"),
    (_set(("hosts", "TASL-2", "hostname"), "TASL-9"), "hostname differs"),
    (_set(("seven_node_spec", "sha256"), "0" * 64), "differs from the one the AR spec binds"),
    (_set(("seven_node_spec", "path"), "sweep2/t1_tasl/g1b_crosscheck_spec.json"), "seven_node_spec.path"),
    (_set(("estimate", "census_gpu_model"), "NVIDIA RTX 6000 Ada Generation"), "census_gpu_model"),
    (_set(("estimate", "ratio_4090_over_ada"), 1.2), "ratio 1.0"),
    (_set(("note_rule",), "R1-G1B-TASL-DECISIONS"), "note_rule must cite"),
    (_set(("caps", "crosscheck_gpu_hours"), 0), "crosscheck_gpu_hours"),
    (_set(("caps", "crosscheck_gpu_hours"), 11), "crosscheck_gpu_hours"),
    (_set(("harness", "repo"), "https://github.com/x/autoresearch_harness.git"), "harness.repo"),
    # review round 1
    (_set(("harness", "commit"), SEVEN["harness"]["commit"]), "harness.commit must be the AR pin"),
    (_set(("harness", "commit"), "4" * 40), "harness.commit must be the AR pin"),
    (_set(("env_decision", "authority"), "R1-T1-TASL-ENV (hosts)"), "already requires"),
    (_set(("env_decision", "authority"), "R1-G1B-CAP"), "already requires"),
    (_set(("seven_node_spec", "run_id"), "g1b-tasl-20261121-a"), "seven_node_spec.run_id"),
    (_set(("note_rule",), "R1-G1B-NOTE2-DECISIONSX"), "note_rule must cite"),
    (_set(("run_id",), "g4-tasl-20261121-a"), "run_id must be the AR spec's own"),
    (_set(("run_id",), "g1b-other-a"), "run_id must be the AR spec's own"),
    (_set(("timeout_decision", "basis"), "census_baseline_x3"), "census_slowest_x3"),
    (lambda s: s["hosts"]["TASL-2"].update(base=SEVEN["hosts"]["TASL-2"]["harness_dir"] + "/x",
                                           data_root=SEVEN["hosts"]["TASL-2"]["harness_dir"] + "/x/data"),
     "base lies inside"),
    (_set(("hosts", "TASL-2", "runs_root"), AR["hosts"]["TASL-2"]["harness_dir"] + "/runs"), "runs_root lies inside"),
    (_set(("hosts", "TASL-2", "sealed_root"), "/home/dowling/r1_tracks"), "lies inside hosts.TASL-2.sealed_root"),
    (_set(("hosts", "TASL-2", "env_python", "ar-cond7a"), SEVEN["hosts"]["TASL-2"]["harness_dir"] + "/v/bin/python"),
     "env_python.ar-cond7a lies inside"),
])
def test_ar_spec_refusals(edit, match):
    spec = filled()
    edit(spec)
    with pytest.raises(T.Stop, match=match):
        T.validate_spec(spec, launch=True)


def test_r1_g1b_cap_is_shared_with_the_seven_node_spec_and_the_crosscheck(monkeypatch):
    spec = filled()
    monkeypatch.setattr(T.L, "CAP_TOTAL_GPU_HOURS", 50.0)        # this spec alone (28.2) fits; G.1b together does not
    spec["caps"]["max_total_gpu_hours"] = 50
    with pytest.raises(T.Stop, match="G.1b together .* exceeds the cap 50.0"):
        T.validate_spec(spec)


def test_the_spec_own_cap_bounds_the_shared_total_when_lower():
    spec = filled()
    spec["caps"]["max_total_gpu_hours"] = 40          # 28.2 alone fits; together 58.6 does not
    with pytest.raises(T.Stop, match="exceeds the cap 40.0"):
        T.validate_spec(spec)
    spec["caps"]["max_total_gpu_hours"] = 100
    assert T.validate_spec(spec)["projection"]["g1b_shared_cap"]["cap_total_gpu_hours"] == 100.0


# ============================================================================================ the node job
@pytest.fixture
def job(tmp_path, monkeypatch):
    spec = filled(tmp_path)
    spec_path = tmp_path / "ar_spec.json"
    spec_path.write_text(json.dumps(spec))
    calls = []
    monkeypatch.setattr(T, "host_identity", lambda s, h: {"host": h, "hostname": "TASL-2"})
    monkeypatch.setattr(T, "ptrace_scope", lambda: 1)
    monkeypatch.setattr(T, "scope_cgroup", lambda: {"cgroup_parent": "/sys/fs/cgroup/scope"})
    monkeypatch.setattr(T, "harness_checkout", lambda s, h: {"dir": s["hosts"][h]["harness_dir"],
                                                             "commit": s["harness"]["commit"]})
    monkeypatch.setattr(T, "environment", lambda s, h, n: {"name": n["env"], "python_version": "3.12.15"})
    monkeypatch.setattr(T, "check_affinity", lambda s, n, affinity=None: T.cpu_list(T.node_cpus(s, n)))
    monkeypatch.setattr(os, "environ", dict(os.environ))

    def engine(argv, **kw):
        calls.append((argv, kw))
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        part = next(p for p in lib.PARTS if p[0] == Path(argv[argv.index("--out") + 1]).name)
        _write_part(Path(argv[argv.index("--out") + 1]), chunk["node"], part)
        return subprocess.CompletedProcess(argv, 0, "", "")

    def smi(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUID2}, NVIDIA GeForce RTX 4090, 535.309.01, 24564 MiB\n", "")
    setup = lambda harness, node, base, out: {"data_root": str(base / "data"), "setup": "x"}  # noqa: E731
    return spec, spec_path, calls, engine, smi, setup


def _attempt(spec, n=1):
    return Path(spec["hosts"]["TASL-2"]["runs_root"]) / spec["run_id"] / "autoresearch_fixedtokens" / f"attempt-{n}"


def test_ar_node_job_end_to_end(job):
    spec, spec_path, calls, engine, smi, setup = job
    rec = T.run_node_job(spec_path, "autoresearch_fixedtokens", smi=smi, engine=engine, setup=setup)
    assert rec["runs"]["written"] == 460 and rec["stop"] is None and rec["attempt"] == 1
    assert rec["spec_schema"] == T.AR_SCHEMA and rec["env_decision"].startswith(ENV_ROW)
    assert rec["note_rule"].startswith(T.AR_RULE) and "autoresearch_fixedtokens" in rec["output_use"]
    assert rec["timeout_basis"] == {"decision": "census_slowest_x3", "seconds": 255.916, "timeout_s": 3 * 255.916}
    assert rec["harness_commit"] == AR["harness"]["commit"] and rec["harness"]["dir"].endswith("harness_dir")
    for argv, kw in calls:                    # the engine runs from the AR checkout, in the AR environment
        assert argv[0] == spec["hosts"]["TASL-2"]["env_python"]["ar-cond7a"] and argv[-2:] == ["--gpu-uuid", UUID2]
        assert kw["cwd"] == Path(spec["hosts"]["TASL-2"]["harness_dir"])
        chunk = json.loads(Path(argv[argv.index("--chunk") + 1]).read_text())
        assert chunk["measured_run_seconds"] == 255.916 and chunk["stop_on_timeout"] is True
        assert chunk["chunk_id"].startswith(spec["run_id"] + "-autoresearch_fixedtokens-")


def test_ar_seal_assemble_summarise_are_its_own(job, tmp_path, monkeypatch):
    spec, spec_path, calls, engine, smi, setup = job
    T.run_node_job(spec_path, "autoresearch_fixedtokens", smi=smi, engine=engine, setup=setup)
    receipt = T.seal(_attempt(spec), spec, "autoresearch_fixedtokens")
    manifest = T.assemble([Path(receipt["sealed_path"])], spec, tmp_path / "run", lib._sha_file(spec_path))
    assert manifest["schema"] == T.AR_ASSEMBLY_SCHEMA and [j["node"] for j in manifest["jobs"]] == \
        ["autoresearch_fixedtokens"]
    monkeypatch.setattr(T.L, "summarise", lambda run_dir, s, root: {"schema": "x", "verdicts": {}})
    summary = T.summarise(tmp_path / "run", spec, ROOT)
    assert summary["schema"] == T.AR_SUMMARY_SCHEMA and summary["hosts"] == {"autoresearch_fixedtokens": "TASL-2"}
    assert summary["env_decision"].startswith(ENV_ROW) and summary["census_gpu_model"] == T.GPU_MODEL
    # an assembly of the other kind is refused (the AR floor joins the table by node, never inside the seven's)
    asm = json.loads((tmp_path / "run" / "ASSEMBLY.json").read_text())
    asm["schema"] = T.ASSEMBLY_SCHEMA
    (tmp_path / "run" / "ASSEMBLY.json").write_text(json.dumps(asm))
    with pytest.raises(T.Stop, match="other spec kind"):
        T.summarise(tmp_path / "run", spec, ROOT)
    with pytest.raises(T.Stop, match="the assembly is of the other spec kind"):    # an AR assembly, seven-node spec
        asm["schema"] = T.AR_ASSEMBLY_SCHEMA
        (tmp_path / "run" / "ASSEMBLY.json").write_text(json.dumps(asm))
        T.summarise(tmp_path / "run", copy.deepcopy(SEVEN), ROOT)


# ============================================================================================ the third note
def note_fields(spec, spec_path, **over) -> dict:
    pin = spec["harness"]["commit"]
    rec = spec["hosts"]["TASL-2"]["isolation_host_check"]["record"]
    fields = {"approved": "true", "label": "ENGINEERING_ONLY", "labels_read": "none",
              "paper_commit": spec["paper"]["commit"], "spec_sha256": lib._sha_file(spec_path),
              "run_id": spec["run_id"], "harness_commit": pin, "note_rule": "R1-G1B-NOTE2-DECISIONS (NOTE2-AR A)",
              "host_row": "R1-T1-TASL-ENV (hosts), with R1-T1-HOST-TASL", "env_row": ENV_ROW,
              "P1": "PASS — R1-TRACKG-AR-U2-TASL2: the AR census row on TASL-2",
              "P2": f"PASS — TASL-2 host check at harness {pin[:8]}: {rec} sha256 x",
              "P3": f"PASS — independent review of harness {pin[:8]}: docs/r1/reviews/AR_HARNESS_REVIEW.md",
              "P4": "PASS — spec support and spec: docs/r1/reviews/G1B_AR_SPEC_REVIEW.md",
              "P5": "PASS — R1-G1B-EDITS: 4 edits", "P6": "PASS — R1-G1B-TIMEOUT: census_slowest_x3",
              "P7": f"PASS — {ENV_ROW}: the AR census environment ar-cond7a", "P8": "PASS — R1-G1B-CAP: 58.6 GPU-h"}
    fields.update(over)
    return fields


def write_note(tmp_path, fields, name="g1b_ar_t1_tasl_20991231.md") -> Path:
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))
    return p


def test_check_note_ar_strict_and_draft(job, tmp_path):
    spec, spec_path, *_ = job
    yes = lambda rel, raw: True  # noqa: E731
    note = write_note(tmp_path, note_fields(spec, spec_path))
    assert T.check_note_ar(note, spec_path, spec=spec, on_main=yes)["env_row"] == ENV_ROW
    with pytest.raises(T.Stop, match="not committed byte-identically"):
        T.check_note_ar(note, spec_path, spec=spec, on_main=lambda rel, raw: False)
    with pytest.raises(T.Stop, match="draft mode is for the unsigned note"):
        T.check_note_ar(note, spec_path, spec=spec, draft=True)
    draft = write_note(tmp_path, note_fields(spec, spec_path, approved="false"))
    assert T.check_note_ar(draft, spec_path, spec=spec, draft=True)["approved"] == "false"   # not on main: fine
    with pytest.raises(T.Stop, match="note field approved"):
        T.check_note_ar(draft, spec_path, spec=spec, on_main=yes)
    with pytest.raises(T.Stop, match="third note binds an autoresearch-only spec"):
        T.check_note_ar(note, SEVEN_PATH, spec=SEVEN, on_main=yes)
    with pytest.raises(T.Stop, match="third note \\(check_note_ar\\)"):
        T.check_note(note, spec_path, spec["paper"]["commit"], on_main=yes, spec=spec)


@pytest.mark.parametrize("over, match", [
    ({"spec_sha256": "0" * 64}, "spec_sha256"),
    ({"run_id": SEVEN["run_id"]}, "run_id"),
    ({"harness_commit": AR["harness"]["commit"][:8]}, "harness_commit"),
    ({"paper_commit": "4" * 40}, "paper_commit"),
    ({"env_row": "R1-OTHER"}, "env_row"),
    ({"labels_read": "some"}, "labels_read"),
    ({"note_rule": "R1-G1B-TASL-DECISIONS"}, "note_rule must cite"),
    ({"host_row": "R1-OTHER"}, "host_row must cite"),
    ({"P7": "PENDING — the env row"}, "PENDING"),
    ({"P3": "PASS — review <path>"}, "placeholder"),
    ({"P5": "FAIL — x"}, "P5 is not PASS"),
    ({"P1": "PASS — the census"}, "P1 must cite 'R1-TRACKG-AR-U2-TASL2'"),
    ({"P2": "PASS — TASL-2 host check, see the report"}, "P2 must cite"),
    ({"P3": "PASS — docs/r1/reviews/AR_HARNESS_REVIEW.md"}, "P3 must cite"),
    ({"P4": "PASS — reviewed"}, "P4 must cite"),
    ({"P7": "PASS — the environment row"}, "P7 must cite"),
    ({"P8": "PASS — within the cap"}, "P8 must cite"),
])
def test_check_note_ar_refusals(job, tmp_path, over, match):
    spec, spec_path, *_ = job
    note = write_note(tmp_path, note_fields(spec, spec_path, **over))
    with pytest.raises(T.Stop, match=match):
        T.check_note_ar(note, spec_path, spec=spec, on_main=lambda rel, raw: True)


def test_check_note_ar_needs_its_name_and_one_approved_line(job, tmp_path):
    spec, spec_path, *_ = job
    note = write_note(tmp_path, note_fields(spec, spec_path), name="g1b_t1_tasl_20991231.md")
    with pytest.raises(T.Stop, match="g1b_ar_t1_tasl_<YYYYMMDD>.md"):
        T.check_note_ar(note, spec_path, spec=spec, on_main=lambda rel, raw: True)
    note = write_note(tmp_path, note_fields(spec, spec_path, approved="false"))
    note.write_text(note.read_text() + "approved: false\n")
    with pytest.raises(T.Stop, match="draft mode is for the unsigned note"):
        T.check_note_ar(note, spec_path, spec=spec, draft=True)


def test_ar_launch_needs_the_third_note_both_keys_and_the_tasl2_record(job, tmp_path, monkeypatch):
    spec, spec_path, *_ = job
    yes = lambda rel, raw: True  # noqa: E731
    note = write_note(tmp_path, note_fields(spec, spec_path))
    plan = (f"| R1-OTHER | x |\n| {ENV_ROW} | autoresearch_fixedtokens runs in its census environment ar-cond7a "
            "(Python 3.12.15) |\n").encode()
    reports = {spec["hosts"]["TASL-2"]["isolation_host_check"]["record"]: host_report().encode(),
               "docs/r1/PLAN.md": plan}
    monkeypatch.delenv(T.ENABLE_ENV, raising=False)
    with pytest.raises(T.Stop, match="disabled"):
        T.launch(spec_path, note, "autoresearch_fixedtokens", enable=True, on_main=yes, read_main=reports.get)
    monkeypatch.setenv(T.ENABLE_ENV, "1")
    seen = []
    out = T.launch(spec_path, note, "autoresearch_fixedtokens", enable=True, on_main=yes, read_main=reports.get,
                   launch_binding=lambda repo, s, rows: seen.append(rows) or {"bound": True},
                   runner=lambda sp, n: {"runs": {"written": 460}})
    assert out["launch"] == {"bound": True}
    assert set(T.AR_PLAN_ROWS) <= set(seen[0]) and ENV_ROW in seen[0] and "R1-G1B-NOTE2-DECISIONS" in seen[0]
    # a host check at the old pin, with the spec binding that very report: refused on the pin, not the sha256
    stale_report = host_report(commit=SEVEN["harness"]["commit"]).encode()
    stale_spec = copy.deepcopy(spec)
    stale_spec["hosts"]["TASL-2"]["isolation_host_check"]["sha256"] = hashlib.sha256(stale_report).hexdigest()
    stale_path = tmp_path / "stale_spec.json"
    stale_path.write_text(json.dumps(stale_spec))
    stale_note = write_note(tmp_path, note_fields(stale_spec, stale_path), name="g1b_ar_t1_tasl_20991230.md")
    stale = {**reports, spec["hosts"]["TASL-2"]["isolation_host_check"]["record"]: stale_report}
    with pytest.raises(T.Stop, match="does not show a PASS for this host and pin.*host_check_harness_commit"):
        T.launch(stale_path, stale_note, "autoresearch_fixedtokens", enable=True, on_main=yes, read_main=stale.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    for text in (b"", f"| {ENV_ROW} | torch312 only |\n".encode(),
                 f"| {ENV_ROW} | ar-cond7a |\n| {ENV_ROW} | ar-cond7a |\n".encode()):
        with pytest.raises(T.Stop, match="must exist once and name ar-cond7a"):    # decision AR-ENV on main
            T.launch(spec_path, note, "autoresearch_fixedtokens", enable=True, on_main=yes,
                     read_main={**reports, "docs/r1/PLAN.md": text}.get,
                     launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    with pytest.raises(T.Stop, match="not in the spec"):
        T.launch(spec_path, note, "mlab_imdb", enable=True, on_main=yes, read_main=reports.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})
    seven_note = write_note(tmp_path, note_fields(spec, spec_path), name="g1b_t1_tasl_20991231.md")
    with pytest.raises(T.Stop, match="g1b_ar_t1_tasl_"):           # the seven-node notes cannot launch it
        T.launch(spec_path, seven_note, "autoresearch_fixedtokens", enable=True, on_main=yes, read_main=reports.get,
                 launch_binding=lambda *a: {}, runner=lambda sp, n: {})


def test_cli_check_note_ar(job, tmp_path, capsys):
    spec, spec_path, *_ = job
    draft = write_note(tmp_path, note_fields(spec, spec_path, approved="false"))
    assert T.main(["check-note-ar", str(spec_path), "--note", str(draft), "--draft"]) == 0
    assert T.main(["check-note-ar", str(spec_path), "--note", str(draft)]) == 2         # not on main / approved
    assert "not committed byte-identically on origin/main" in capsys.readouterr().err
    assert T.main(["check-note-ar", str(AR_PATH), "--note", str(draft), "--draft"]) == 2   # shipped spec: TODOs


def test_the_shipped_draft_binds_the_ar_spec_and_is_not_signable_yet(tmp_path):
    """The third-note draft names the AR spec's run id and harness pin and reads approved: false. Before (d) its open
    fields (paper commit, spec sha256, env row, P2, P3, P4, P7) keep check_note_ar --draft from passing; after (d) it
    has none and passes check_note_ar --draft against the shipped spec as it stands."""
    fields = T._note_fields(NOTE_DRAFT.read_bytes())
    assert fields["approved"] == "false" and fields["run_id"] == AR["run_id"]
    assert fields["harness_commit"] == AR["harness"]["commit"] and fields["note_rule"].startswith(T.AR_RULE)
    pending = [k for k in ("P2", "P3", "P4", "P7") if fields[k].upper().startswith("PENDING")]
    if not AR_FINAL:
        assert pending == ["P2", "P3", "P4", "P7"]
        assert all(fields[k].upper().startswith("PASS") for k in ("P1", "P5", "P6", "P8"))
        assert re.search(r"<[^>]*>", fields["paper_commit"]) and re.search(r"<[^>]*>", fields["spec_sha256"])
        return
    assert pending == [] and all(fields[f"P{i}"].upper().startswith("PASS") for i in range(1, 9))
    assert fields["paper_commit"] == AR_SHIPPED["paper"]["commit"] and fields["env_row"] == ENV_ROW
    assert fields["spec_sha256"] == hashlib.sha256(AR_PATH.read_bytes()).hexdigest()
    rec = AR_SHIPPED["hosts"]["TASL-2"]["isolation_host_check"]
    assert f"{rec['record']} sha256 {rec['sha256']}" in fields["P2"] and "R1-G1B-AR-PY" in fields["P7"]
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True)
    note = d / "g1b_ar_t1_tasl_20991231.md"
    note.write_bytes(NOTE_DRAFT.read_bytes())
    assert T.check_note_ar(note, AR_PATH, spec=copy.deepcopy(AR_SHIPPED), draft=True)["run_id"] == AR["run_id"]


def test_the_shipped_draft_completed_in_its_open_fields_passes_check_note_ar_draft(tmp_path):
    """Review round 1, M1: fill only the fields the draft declares open (paper_commit, spec_sha256, env_row, P2, P3, P4,
    P7) and the copy passes check_note_ar --draft against the filled spec; no other line holds a placeholder."""
    spec = filled()
    spec_path = tmp_path / "ar_spec.json"
    spec_path.write_text(json.dumps(spec))
    pin = spec["harness"]["commit"]
    rec = spec["hosts"]["TASL-2"]["isolation_host_check"]["record"]
    fills = {"paper_commit": spec["paper"]["commit"], "spec_sha256": lib._sha_file(spec_path), "env_row": ENV_ROW,
             "P2": f"PASS — TASL-2 host check at harness {pin[:8]}: {rec} sha256 x",
             "P3": f"PASS — independent review of harness {pin[:8]}: docs/r1/reviews/X.md",
             "P4": "PASS — docs/r1/reviews/G1B_AR_SPEC_SUPPORT_REVIEW.md",
             "P7": f"PASS — {ENV_ROW}: ar-cond7a"}
    lines = []
    for line in NOTE_DRAFT.read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:", line)
        lines.append(f"{m.group(1)}: {fills[m.group(1)]}" if m and m.group(1) in fills else line)
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True)
    note = d / "g1b_ar_t1_tasl_20991231.md"
    note.write_text("\n".join(lines) + "\n")
    assert T.check_note_ar(note, spec_path, spec=spec, draft=True)["run_id"] == AR["run_id"]


def test_the_procedure_file_cannot_pass_as_a_host_check_record():
    """Review round 2, N1: the procedure shows the record's key lines behind a prefix, so pointing the spec at the
    procedure (with its own sha256) is refused."""
    rel = "docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md"
    raw = (ROOT / rel).read_bytes()
    host = {"hostname": "TASL-2", "isolation_host_check": {"record": rel, "sha256": hashlib.sha256(raw).hexdigest()}}
    with pytest.raises(T.Stop, match="does not show a PASS"):
        T.check_host_record(host, AR["harness"]["commit"], lambda r: raw if r == rel else None)
