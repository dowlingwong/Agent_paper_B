"""Synthetic tests for the S2-C4 timing-pilot helper (no job, no GPU, no labels)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c2_lib as lib  # noqa: E402
import s2_c4_pilot as p4  # noqa: E402


def test_make_specs_writes_two_pilot_specs(tmp_path):
    out = tmp_path / "specs"
    specs = p4.make_specs(ROOT / "sweep2" / "spec.example.json", "s2c4-20261116", out)
    assert set(specs) == set(p4.MODES)
    for mode, path in specs.items():
        s = json.loads(Path(path).read_text())
        assert s["collector"]["memory_mode"] == mode
        assert s["collector"]["instances"] == p4.PILOT_INSTANCES
        assert s["chunk_id"].endswith("-pilot")
        assert s["run_id"] == "s2c4-20261116"


def test_parse_condor_log_queue_and_wall():
    log = """000 (1.000.000) 11/16 01:00:00 Job submitted from host: <x>
001 (1.000.000) 11/16 01:10:00 Job executing on host: <y>
005 (1.000.000) 11/16 01:20:00 Job terminated.
"""
    t = p4.parse_condor_log(log)
    assert t["queue_wait_s"] == 600 and t["wall_s"] == 600
    with pytest.raises(lib.Stop, match="lacks submit/execute/terminated"):
        p4.parse_condor_log("garbage")


def test_parse_condor_log_006_image_and_memory_peaks():
    log = """000 (1.000.000) 11/16 01:00:00 Job submitted
001 (1.000.000) 11/16 01:10:00 Job executing
006 (1.000.000) 11/16 01:11:00 Image size of job updated: 45000000
\tMemoryUsage = 64000
006 (1.000.000) 11/16 01:12:00 Image size of job updated: 51000000
\tMemoryUsage = 96000
005 (1.000.000) 11/16 01:20:00 Job terminated.
"""
    t = p4.parse_condor_log(log)
    assert t["image_size_kb_peak"] == 51000000 and t["memory_usage_mb_peak"] == 96000


def test_layout_extrapolates_to_full_sweep():
    lay = p4.layout([{"wall_s": 600.0}, {"wall_s": 660.0}])
    assert lay["pilot_wall_s"] == 660.0
    assert lay["estimated_full_chunk_wall_s"] == 660.0 * 9
    assert lay["chunks"] == 16
    assert lay["estimated_total_gpu_hours"] == round(660.0 * 9 * 16 / 3600.0, 2)
    assert lay["proposed_request_walltime_s"] == int(__import__("math").ceil(660.0 * 9 * 1.5))
    assert lay["chunk_split_required"] is False


def test_layout_requests_chunk_split_when_walltime_exceeds_a_day():
    lay = p4.layout([{"wall_s": 9000.0}])
    assert lay["chunk_split_required"] is True and lay["proposed_request_walltime_s"] == 86400


def test_parse_llama_log_buffers():
    text = "load_tensors: CUDA0 model buffer size = 4168.09 MiB\nllama_kv_cache: CUDA0 KV buffer size = 952.00 MiB\n"
    out = p4.parse_llama_log(text)
    assert out == {"model_buffer_mib": 4168.09, "kv_buffer_mib": 952.0}
