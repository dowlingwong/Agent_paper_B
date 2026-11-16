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
layout_chunks: 16\nlayout_gpu_hours: 41.72\nb2_audits: none\nd8_lock: true\n""".format(img=sw.FROZEN_IMAGE)
for i in range(1, 8):
    NOTE += f"P{i}: PASS\n"


def write_inputs(tmp_path):
    note = tmp_path / "c3_sweep2_20261117.md"; note.write_text(NOTE)
    spec = {"run_id": "s2sweep-20261117-a", "image": {"digest": sw.FROZEN_IMAGE},
            "request_walltime_s": 12203, "request_disk_kb": 42460977, "request_memory_mb": 32000,
            "label": "EVIDENCE",
            "label_source": {"authorization": note.name,
                             "authorization_sha256": hashlib.sha256(NOTE.encode()).hexdigest()}}
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    return sp, note


def test_check_accepts_a_matching_note_and_spec(tmp_path):
    sp, note = write_inputs(tmp_path)
    out = sw.check(sp, note)
    assert out["run_id"] == "s2sweep-20261117-a" and out["layout"]["layout_chunks"] == "16"


def test_check_refuses_mismatches_and_missing_fields(tmp_path):
    sp, note = write_inputs(tmp_path)
    bad = json.loads(sp.read_text()); bad["run_id"] = "other"; sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="run_id"):
        sw.check(sp, note)
    bad = json.loads(sp.read_text()); bad["run_id"] = "s2sweep-20261117-a"; bad["request_disk_kb"] = 1
    sp.write_text(json.dumps(bad))
    with pytest.raises(sw.Stop, match="disk"):
        sw.check(sp, note)
    note.write_text(NOTE.replace("approved: true", "approved: false"))
    with pytest.raises(sw.Stop, match="not approved"):
        sw.check(sp, note)


def test_submit_is_disabled_without_both_keys(tmp_path, monkeypatch):
    sp, note = write_inputs(tmp_path)
    with pytest.raises(sw.Stop, match="disabled"):
        sw.submit(sp, note, tmp_path / "x.jdl")
    monkeypatch.setenv("S2C5_ENABLE_REAL", "1")
    with pytest.raises(sw.Stop, match="disabled"):
        sw.submit(sp, note, tmp_path / "x.jdl", enable=False)
    with pytest.raises(sw.Stop, match="JDL"):
        sw.submit(sp, note, tmp_path / "x.jdl", enable=True)
