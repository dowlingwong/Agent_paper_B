"""Synthetic tests for the S2-C5 real-submission switch (disabled by default; no submission)."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c5_switch as sw  # noqa: E402

NOTE = """approved: true\nlabel: EVIDENCE\nrun_id: s2sweep-20261117-a\nimage: {img}\n
layout_request_walltime_s: 8735\nlayout_request_disk_kb: 42460970\nlayout_request_memory_mb: 32000\n
layout_chunks: 16\nlayout_gpu_hours: 25.88
layout_wall_hours: 25.88\nb2_audits: none (this authorization carries no B.2 audits)\nd8_lock: true\n""".format(img=sw.FROZEN_IMAGE)
for i in range(1, 8):
    reference = "R1-S2C3-ACCEPT" if i == 4 else "fixture"
    NOTE += f"P{i}: PASS — {reference}\n"

JDL = ("# reviewed\nuniverse = container\ncontainer_image = docker://%s\nexecutable = job.sh\n"
       "request_memory = 32000\nrequest_disk = 42460970\n+RequestWalltime = 8735\n"
       "periodic_hold = (NumJobStarts > 1)\n"
       "queue 1\n" % sw.FROZEN_IMAGE)


def write_inputs(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    note_dir = repo / "docs" / "r1" / "authorizations"; note_dir.mkdir(parents=True)
    note = note_dir / "c3_sweep2_20261117.md"; note.write_text(NOTE)
    jdl = tmp_path / "job.jdl"
    spec = {"schema": sw.lib.SCHEMA, "run_id": "s2sweep-20261117-a", "image": {"digest": sw.FROZEN_IMAGE},
            "request_walltime_s": 8735, "request_disk_kb": 42460970, "request_memory_mb": 32000,
            "label": "EVIDENCE",
            "label_source": {"authorization": note.name,
                             "authorization_sha256": hashlib.sha256(NOTE.encode()).hexdigest()}}
    text = JDL.replace("queue 1", f"requirements = {sw.render_jdl.requirements(spec)}\nqueue 1")
    jdl.write_text(text)
    spec["reviewed_jdl_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    monkeypatch.setattr(sw, "REPO_ROOT", repo)
    monkeypatch.setattr(sw, "_authorized_note", lambda rel, raw: True)
    return sp, note, jdl


def test_check_accepts_a_matching_note_spec_and_jdl(tmp_path, monkeypatch):
    sp, note, jdl = write_inputs(tmp_path, monkeypatch)
    out = sw.check(sp, note, jdl)
    assert out["run_id"] == "s2sweep-20261117-a" and out["jdl_sha256"]
    assert out["layout"]["layout_chunks"] == "16"


def test_path_and_commit_checks_are_enforced(tmp_path, monkeypatch):
    sp, note, jdl = write_inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(sw, "_authorized_note", lambda rel, raw: False)
    with pytest.raises(sw.Stop, match="not committed"):
        sw.check(sp, note, jdl)
    monkeypatch.setattr(sw, "_authorized_note", lambda rel, raw: True)
    outside = tmp_path / "c3_sweep2_20261117.md"; outside.write_text(NOTE)
    with pytest.raises(sw.Stop, match="authorizations"):
        sw.check(sp, outside, jdl)


def test_check_refuses_mismatches(tmp_path, monkeypatch):
    sp, note, jdl = write_inputs(tmp_path, monkeypatch)
    bad = json.loads(sp.read_text()); bad["run_id"] = "other"; sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="run_id"):
        sw.check(sp, note, jdl)
    bad = json.loads(sp.read_text()); bad["run_id"] = "s2sweep-20261117-a"; bad["request_disk_kb"] = 1
    sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="disk"):
        sw.check(sp, note, jdl)
    bad["request_disk_kb"] = 42460970; bad["reviewed_jdl_sha256"] = "0" * 64; sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="reviewed JDL"):
        sw.check(sp, note, jdl)
    jdl.write_text(JDL)
    bad["reviewed_jdl_sha256"] = hashlib.sha256(JDL.encode()).hexdigest()
    sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="H200 placement"):
        sw.check(sp, note, jdl)
    note.write_text(NOTE.replace("P1: PASS", "P1: NOT PASS"))
    with pytest.raises(sw.Stop, match="PASS"):
        sw.check(sp, note, jdl)
    note.write_text(NOTE.replace("approved: true", "approved: false"))
    with pytest.raises(sw.Stop, match="not approved"):
        sw.check(sp, note, jdl)


def test_note_parser_hardening():
    for change in (NOTE.replace("P1: PASS", "P1: FAIL"), NOTE + "approved: true\n",
                   NOTE.replace("layout_gpu_hours: 25.88", "layout_gpu_hours: nan"),
                   NOTE.replace("layout_wall_hours: 25.88", "layout_wall_hours: 49")):
        with pytest.raises(sw.Stop):
            sw.parse_note(change)


def test_submit_is_disabled_without_both_keys(tmp_path, monkeypatch):
    sp, note, jdl = write_inputs(tmp_path, monkeypatch)
    with pytest.raises(sw.Stop, match="disabled"):
        sw.submit(sp, note, jdl)
    monkeypatch.setenv("S2C5_ENABLE_REAL", "1")
    with pytest.raises(sw.Stop, match="disabled"):
        sw.submit(sp, note, jdl, enable=False)
    calls = []
    class Fake:
        returncode = 0; stdout = "1 job(s) submitted to cluster 1."; stderr = ""
    monkeypatch.setattr(sw.subprocess, "run", lambda argv, **kw: calls.append(argv) or Fake())
    monkeypatch.setattr(sw, "_verify_launch", lambda *args: None)
    out = sw.submit(sp, note, jdl, enable=True)
    assert calls and calls[0][0] == "condor_submit" and out["jdl_sha256"]
    record = (jdl.parent / "S2C5_SUBMISSIONS.jsonl").read_text()
    assert "s2sweep-20261117-a" in record and out["jdl_sha256"] in record
    with pytest.raises(sw.Stop, match="already attempted"):
        sw.submit(sp, note, jdl, enable=True)
    assert len(calls) == 1


# ---------------------------------------------------------------- R1-S2C3B-WDBC declared exception
_WDBC_PLAN = "| R1-S2C3B-WDBC | declared exception |\n"
_WDBC_EXC = {"row": "R1-S2C3B-WDBC", "node": "openml_wdbc", "criterion": "invalid_rate",
             "required": "< 0.3", "max_observed": 0.30, "observed": 0.3}


_NODES = list(sw.lib.LIVENESS_NODES)


def _wdbc_gate(**change):
    nodes = {node: {"pass": True, "failed_criteria": [], "criteria": {}} for node in _NODES}
    nodes["openml_wdbc"] = {"pass": False, "failed_criteria": ["invalid_rate"],
                            "criteria": {"invalid_rate": {"observed": 0.3, "required": "< 0.3"}}}
    gate = {"live_nodes": 7, "failed_nodes": ["openml_wdbc"], "declared_exception": dict(_WDBC_EXC), "nodes": nodes}
    gate.update(change)
    return gate


def test_liveness_nodes_ok_accepts_eight_and_the_declared_seven():
    assert sw.liveness_nodes_ok({"live_nodes": 8, "failed_nodes": []}, "")
    assert sw.liveness_nodes_ok(_wdbc_gate(), _WDBC_PLAN)


def test_liveness_nodes_ok_rechecks_the_recorded_node_entries():
    missing = _wdbc_gate(); missing.pop("nodes")
    assert not sw.liveness_nodes_ok(missing, _WDBC_PLAN)
    other_failed = _wdbc_gate(); other_failed["nodes"]["openml_climate"]["pass"] = False
    assert not sw.liveness_nodes_ok(other_failed, _WDBC_PLAN)
    mismatch = _wdbc_gate(); mismatch["nodes"]["openml_wdbc"]["criteria"]["invalid_rate"]["observed"] = 0.25
    assert not sw.liveness_nodes_ok(mismatch, _WDBC_PLAN)
    two = _wdbc_gate(); two["nodes"]["openml_wdbc"]["failed_criteria"] = ["invalid_rate", "keep_after_trial_1"]
    assert not sw.liveness_nodes_ok(two, _WDBC_PLAN)


@pytest.mark.parametrize("change, plan", [
    ({}, ""),                                                            # row not on published main
    ({"declared_exception": None}, _WDBC_PLAN),                          # no recorded exception
    ({"failed_nodes": ["openml_climate"]}, _WDBC_PLAN),                  # another node failed
    ({"live_nodes": 6, "failed_nodes": ["openml_wdbc", "openml_climate"]}, _WDBC_PLAN),
    ({"declared_exception": dict(_WDBC_EXC, observed=0.4)}, _WDBC_PLAN),  # worse than the boundary
    ({"declared_exception": dict(_WDBC_EXC, criterion="keep_after_trial_1")}, _WDBC_PLAN),
    ({"declared_exception": dict(_WDBC_EXC, row="R1-OTHER")}, _WDBC_PLAN),
    ({"declared_exception": dict(_WDBC_EXC, observed=True)}, _WDBC_PLAN),
])
def test_liveness_nodes_ok_refuses_any_other_shortfall(change, plan):
    gate = _wdbc_gate(**change)
    assert not sw.liveness_nodes_ok(gate, plan)


def test_switch_and_c3b_driver_declare_the_same_exception():
    import s2_c3b_lib as c3b
    assert sw.WDBC_EXCEPTION == c3b.DECLARED_EXCEPTION
