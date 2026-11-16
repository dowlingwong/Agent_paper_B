"""Synthetic tests for the S2-C2 sweep-2 HTCondor job wrapper (no job, no network, no GPU)."""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c2_lib as lib  # noqa: E402
import render_jdl  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "spec.example.json").read_text())


def spec(**over):
    s = copy.deepcopy(SPEC)
    s.update(over)
    return s


def test_sample_spec_validates_and_defaults_to_engineering_label():
    v = lib.validate_spec(spec())
    assert v["label"] == "ENGINEERING_ONLY"
    assert str(v["output_root"]).startswith("/ceph/srv/dwong/paperb/sweep2/s2eng-20261116-a")


def test_authorization_note_sets_evidence_label(tmp_path):
    note = tmp_path / "c3_sweep2_20261116.md"
    note.write_text("# auth\nrun: s2eng-20261116-a\napproved: true\nlabel: EVIDENCE\n")
    s = spec(); s["label_source"] = {"authorization": str(note),
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    assert lib.resolve_label(s) == "EVIDENCE"


def test_authorization_must_be_approved_and_named(tmp_path):
    note = tmp_path / "a.md"
    note.write_text("run: s2eng-20261116-a\napproved: false\nlabel: EVIDENCE\n")
    s = spec(); s["label_source"] = {"authorization": str(note),
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    with pytest.raises(lib.Stop, match="not approved"):
        lib.resolve_label(s)
    note.write_text("run: other-run\napproved: true\nlabel: EVIDENCE\n")
    s["label_source"]["authorization_sha256"] = hashlib.sha256(note.read_bytes()).hexdigest()
    with pytest.raises(lib.Stop, match="does not name this run"):
        lib.resolve_label(s)


def test_index_label_may_never_select_the_table_label():
    """R1-SWEEP1-CLASSIFY defect regression: a sweep-index label (PILOT/ENGINEERING_ONLY) is not a table label."""
    s = spec(); s["label_source"] = {"sweep_index_label": "ENGINEERING_ONLY"}
    with pytest.raises(lib.Stop, match="index label may not select"):
        lib.resolve_label(s)
    s = spec(); s["label_source"] = {"index_label": "PILOT"}
    with pytest.raises(lib.Stop, match="index label may not select"):
        lib.resolve_label(s)


def test_output_must_be_sealed_and_not_r1_sealed():
    s = spec(); s["output"] = {"root": "/tmp/out", "sealed": True}
    with pytest.raises(lib.Stop, match="sealed"):
        lib.validate_spec(s)
    s = spec(); s["output"] = {"root": "/ceph/srv/dwong/paperb/sweep2/s2eng-20261116-a/r1_sealed", "sealed": True}
    with pytest.raises(lib.Stop, match="r1_sealed"):
        lib.validate_spec(s)


def test_requirements_pin_l40s_and_nemo2():
    for key, bad in (("gpu_device_name", "NVIDIA H200"), ("cloud_site", "BwForCluster-HoreKa")):
        s = spec(); s["requirements"][key] = bad
        with pytest.raises(lib.Stop):
            lib.validate_spec(s)
    s = spec(); s["requirements"]["machine_regex"] = "(["
    with pytest.raises(lib.Stop, match="does not compile"):
        lib.validate_spec(s)
    s = spec(); s["requirements"]["requires_etp_ceph"] = False
    with pytest.raises(lib.Stop, match="ETP ceph"):
        lib.validate_spec(s)


def test_w20_and_schema_are_enforced():
    s = spec(); s["collector"]["runs"] = 19
    with pytest.raises(lib.Stop, match="W = 20"):
        lib.validate_spec(s)
    s = spec(); s["collector"]["proposal_schema"] = "manager_proposal/v0"
    with pytest.raises(lib.Stop, match="manager_proposal/v1"):
        lib.validate_spec(s)


def test_jdl_pins_container_l40s_cpu_class_and_ceph():
    jdl = render_jdl.render(lib.validate_spec(spec())["spec"], "s2_c2_job")
    assert "universe = container" in jdl
    assert "container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35" in jdl
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"' in jdl
    assert 'TARGET.CloudSite =?= "BwForCluster-Nemo2"' in jdl
    assert 'regexp("^g36[0-9]{2}\\.nemo\\.privat$", TARGET.Machine)' in jdl
    assert "TARGET.ProvidesEtpCeph =?= True" in jdl
    assert "request_GPUs = 1" in jdl and "request_cpus = 16" in jdl
    assert "docker_image" not in jdl and "RequestGPUMemory" not in jdl


def test_collector_argv_uses_llamacpp_and_writes_label():
    v = lib.validate_spec(spec()); s = v["spec"]
    argv = lib.collector_argv(s, Path("/p"), Path("/h"), Path("/o"), Path("/w"), "ENGINEERING_ONLY", False)
    joined = " ".join(argv)
    assert argv[0] == "/opt/r1/envs/harness/bin/python"
    assert "-m r1.headroom.e1b_collect" in joined
    assert "--manager-model llamacpp/gemma4_31b" in joined
    assert "--proposal-schema manager_proposal/v1" in joined
    assert "--label ENGINEERING_ONLY" in joined and "--runs 20" in joined
    assert "--memory-mode append_only_summary" in joined and "--roots-only" in joined
    assert "--analysis" not in joined and "--read" not in joined
    resumed = lib.collector_argv(s, Path("/p"), Path("/h"), Path("/o"), Path("/w"), "EVIDENCE", True)
    assert "--resume" in resumed


def test_server_argv_keeps_exam_flags_and_refuses_managed_duplicates():
    s = spec()["server"]; s = {"server": s, "model": {"alias": "gemma4_31b"}}
    argv = lib.build_server_argv({"server": s["server"], "model": s["model"]}, Path("/m.gguf"))
    joined = " ".join(argv)
    assert "--jinja" in joined and "enable_thinking" in joined
    assert "--cache-type-k" in joined and "q8_0" in joined
    assert "-c 16384" in joined and "-ngl 99" in joined
    bad = spec(); bad["server"]["extra_args"] = bad["server"]["extra_args"] + ["-c", "4096"]
    with pytest.raises(lib.Stop, match="managed flags"):
        lib.build_server_argv(bad, Path("/m.gguf"))


def test_cpu_identity_checks_the_pinned_class(monkeypatch, tmp_path):
    fake = tmp_path / "cpuinfo"
    fake.write_text("processor\t: 0\nmodel name\t: Test CPU Model 123\nprocessor\t: 1\n")
    real_path = __import__("pathlib").Path
    monkeypatch.setattr(lib, "Path", lambda p: fake if str(p) == "/proc/cpuinfo" else real_path(p))
    assert lib.cpu_identity("Test CPU")["logical_cpus"] == 2
    with pytest.raises(lib.Stop, match="does not contain the pinned class"):
        lib.cpu_identity("definitely-not-a-cpu-model")
