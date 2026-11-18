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
layout_request_walltime_s: 12203\nlayout_request_disk_kb: 42460977\nlayout_request_memory_mb: 32000\n
layout_chunks: 16\nlayout_gpu_hours: 41.72\nb2_audits: none (this authorization carries no B.2 audits)\nd8_lock: true\n""".format(img=sw.FROZEN_IMAGE)
for i in range(1, 8):
    NOTE += f"P{i}: PASS\n"

JDL = ("# reviewed\nuniverse = container\ncontainer_image = docker://%s\nexecutable = job.sh\n"
       "request_memory = 32000\nrequest_disk = 42460977\n+RequestWalltime = 12203\nqueue 1\n" % sw.FROZEN_IMAGE)


def write_inputs(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    note_dir = repo / "docs" / "r1" / "authorizations"; note_dir.mkdir(parents=True)
    note = note_dir / "c3_sweep2_20261117.md"; note.write_text(NOTE)
    jdl = tmp_path / "job.jdl"; jdl.write_text(JDL)
    spec = {"run_id": "s2sweep-20261117-a", "image": {"digest": sw.FROZEN_IMAGE},
            "request_walltime_s": 12203, "request_disk_kb": 42460977, "request_memory_mb": 32000,
            "label": "EVIDENCE", "reviewed_jdl_sha256": hashlib.sha256(JDL.encode()).hexdigest(),
            "label_source": {"authorization": note.name,
                             "authorization_sha256": hashlib.sha256(NOTE.encode()).hexdigest()}}
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
    bad["request_disk_kb"] = 42460977; bad["reviewed_jdl_sha256"] = "0" * 64; sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="reviewed JDL"):
        sw.check(sp, note, jdl)
    note.write_text(NOTE.replace("P1: PASS", "P1: NOT PASS"))
    with pytest.raises(sw.Stop, match="PASS"):
        sw.check(sp, note, jdl)
    note.write_text(NOTE.replace("approved: true", "approved: false"))
    with pytest.raises(sw.Stop, match="not approved"):
        sw.check(sp, note, jdl)


def test_note_parser_hardening():
    for change in (NOTE.replace("P1: PASS", "P1: FAIL"), NOTE + "approved: true\n",
                   NOTE.replace("layout_gpu_hours: 41.72", "layout_gpu_hours: nan")):
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
    out = sw.submit(sp, note, jdl, enable=True)
    assert calls and calls[0][0] == "condor_submit" and out["jdl_sha256"]
    record = (jdl.parent / "S2C5_SUBMISSIONS.jsonl").read_text()
    assert "s2sweep-20261117-a" in record and out["jdl_sha256"] in record
