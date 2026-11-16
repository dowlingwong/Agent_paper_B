"""Synthetic tests for the S2-C2 sweep-2 HTCondor job wrapper/seal step (no job, no network, no GPU)."""
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
    s = copy.deepcopy(SPEC); s.update(over); return s


def test_sample_spec_is_engineering_and_validates():
    v = lib.validate_spec(spec())
    assert v["label"] == "ENGINEERING_ONLY"


def test_class_constants_are_not_spec_driven():
    for path, bad in ((("requirements", "cloud_site"), "BwForCluster-HoreKa"),
                      (("requirements", "gpu_device_name"), "NVIDIA H200"),
                      (("requirements", "machine_regex"), ".*"), (("requirements", "min_cpus"), 4)):
        s = spec(); s[path[0]][path[1]] = bad
        with pytest.raises(lib.Stop):
            lib.validate_spec(s)


def test_b2_harness_pin_is_enforced():
    s = spec(); s["harness"]["commit"] = "897d83c8efa364ec2fdd37288241cc42e01d7274"
    with pytest.raises(lib.Stop, match="B2 harness"):
        lib.validate_spec(s)


def test_evidence_requires_authorization_and_evidence_ready(tmp_path, monkeypatch):
    note = tmp_path / "c3_sweep2_20261116.md"
    note.write_text("run: s2eng-20261116-a\napproved: true\nlabel: EVIDENCE\n")
    monkeypatch.chdir(tmp_path)
    s = spec(); s["label_source"] = {"authorization": "c3_sweep2_20261116.md",
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    with pytest.raises(lib.Stop, match="evidence_ready"):
        lib.validate_spec(s)
    s["paper"]["evidence_ready"] = True
    s["requirements"]["cpu_model_contains"] = "Test CPU"
    assert lib.validate_spec(s)["label"] == "EVIDENCE"


def test_authorization_must_be_approved_and_named(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    note = tmp_path / "a.md"
    note.write_text("run: s2eng-20261116-a\napproved: false\nlabel: EVIDENCE\n")
    s = spec(); s["label_source"] = {"authorization": "a.md",
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    s["paper"]["evidence_ready"] = True
    with pytest.raises(lib.Stop, match="not approved"):
        lib.resolve_label(s)
    note.write_text("run: other\napproved: true\nlabel: EVIDENCE\n")
    s["label_source"]["authorization_sha256"] = hashlib.sha256(note.read_bytes()).hexdigest()
    with pytest.raises(lib.Stop, match="does not name this run"):
        lib.resolve_label(s)


def test_index_label_may_never_select_the_table_label():
    """Scoped to this wrapper's path: a sweep-index label cannot become the table label (R1-SWEEP1-CLASSIFY)."""
    for key in ("sweep_index_label", "index_label"):
        s = spec(); s["label_source"] = {key: "ENGINEERING_ONLY"}
        with pytest.raises(lib.Stop, match="index label"):
            lib.resolve_label(s)


def test_requirements_reject_etp_ceph():
    s = spec(); s["requirements"]["requires_etp_ceph"] = True
    with pytest.raises(lib.Stop, match="ProvidesEtpCeph"):
        lib.validate_spec(s)


def test_w20_workers_schema_ctx_and_walltime_are_enforced():
    for change in (lambda s: s["collector"].__setitem__("runs", 19),
                   lambda s: s["collector"].__setitem__("workers", 8),
                   lambda s: s["server"].__setitem__("ctx", 8192),
                   lambda s: s.__setitem__("walltime_s", 60),
                   lambda s: s["collector"].__setitem__("proposal_schema", "manager_proposal/v0")):
        s = spec(); change(s)
        with pytest.raises(lib.Stop):
            lib.validate_spec(s)


def test_exam_server_flags_are_required():
    s = spec(); s["server"]["extra_args"] = [a for a in s["server"]["extra_args"] if a != "--jinja"]
    with pytest.raises(lib.Stop, match="--jinja"):
        lib.validate_spec(s)
    s = spec(); s["server"]["extra_args"] = [a for a in s["server"]["extra_args"] if a != "--cache-type-k"]
    with pytest.raises(lib.Stop, match="cache-type-k"):
        lib.validate_spec(s)


def test_renderer_pins_container_l40s_cpu_class_and_transfers_outputs(tmp_path):
    stage = tmp_path / "stage"
    out = tmp_path / "job.jdl"
    render_jdl.main([str(ROOT / "sweep2" / "spec.example.json"), "--out", str(out), "--stage-dir", str(stage)])
    jdl = out.read_text()
    assert "universe = container" in jdl
    assert "container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35" in jdl
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"' in jdl
    assert 'TARGET.CloudSite =?= "BwForCluster-Nemo2"' in jdl
    assert f"Cpus >= {lib.MIN_CPUS}" in jdl and 'Arch == "X86_64"' in jdl and 'OpSys == "LINUX"' in jdl
    assert 'regexp("^g36[0-9]{2}\\.nemo\\.privat$", TARGET.Machine)' in jdl
    assert "transfer_output_files = out,work,job_record.json,SHA256SUMS,llama-server.log" in jdl
    assert "request_disk = 50000000" in jdl and "request_memory = 128000" in jdl
    assert "ProvidesEtpCeph" not in jdl and "docker_image" not in jdl
    assert (stage / "s2_c2_spec.json").is_file() and (stage / "s2_c2_lib.py").is_file()


def test_renderer_stages_authorization_note_for_evidence(tmp_path, monkeypatch):
    note = tmp_path / "c3_sweep2_20261116.md"
    note.write_text("run: s2eng-20261116-a\napproved: true\nlabel: EVIDENCE\n")
    s = spec(); s["paper"]["evidence_ready"] = True
    s["requirements"]["cpu_model_contains"] = "Test CPU"
    s["label_source"] = {"authorization": "c3_sweep2_20261116.md",
                         "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    spec_path = tmp_path / "spec.json"; spec_path.write_text(json.dumps(s))
    stage = tmp_path / "stage"; out = tmp_path / "job.jdl"
    render_jdl.main([str(spec_path), "--out", str(out), "--stage-dir", str(stage), "--auth-note", str(note)])
    jdl = out.read_text()
    assert "c3_sweep2_20261116.md" in jdl
    assert (stage / "c3_sweep2_20261116.md").is_file()


def test_sealed_target_rejects_traversal_and_symlinks(tmp_path, monkeypatch):
    real = Path("/ceph/srv/dwong/paperb/sweep2")
    monkeypatch.setattr(lib, "SEALED_ROOT", real)
    assert str(lib._sealed_target("r1", "c1")) == "/ceph/srv/dwong/paperb/sweep2/r1/c1"
    for bad in ("..", "a/b"):
        with pytest.raises(lib.Stop):
            lib._sealed_target(bad, "c1")
    monkeypatch.setattr(lib, "SEALED_ROOT", Path("/ceph/../sealed"))
    with pytest.raises(lib.Stop):
        lib._sealed_target("r1", "c1")
    fake_root = tmp_path / "sealed"
    fake_root.mkdir()
    (fake_root / "run").symlink_to(tmp_path)
    monkeypatch.setattr(lib, "SEALED_ROOT", fake_root)
    with pytest.raises(lib.Stop, match="outside|symlink"):
        lib._sealed_target("run", "c1")


def test_offload_check_accepts_full_offload_and_rejects_partial_or_missing():
    log = "load_tensors: offloaded 29/29 layers to GPU\nCUDA0 model buffer size = 4168.09 MiB\n"
    assert lib.offload_check(log)["offloaded_layers"] == 29
    with pytest.raises(lib.Stop, match="not fully offloaded"):
        lib.offload_check("load_tensors: offloaded 0/29 layers to GPU\n")
    with pytest.raises(lib.Stop, match="no offload counts"):
        lib.offload_check("CUDA0 model buffer size = 4168.09 MiB\n")


def test_host_identity_rejects_off_class_landing(monkeypatch):
    monkeypatch.setattr(lib.socket, "gethostname", lambda: "g3612.nemo.privat")
    monkeypatch.setattr(lib.socket, "getfqdn", lambda name: "g3612.nemo.privat")
    monkeypatch.setattr(lib.os, "cpu_count", lambda: 16)
    assert lib.host_identity()["logical_cpus"] == 16
    monkeypatch.setattr(lib.socket, "gethostname", lambda: "mdm1.etp.kit.edu")
    monkeypatch.setattr(lib.socket, "getfqdn", lambda name: "mdm1.etp.kit.edu")
    with pytest.raises(lib.Stop, match="outside the pinned CPU-class"):
        lib.host_identity()
    monkeypatch.setattr(lib.socket, "gethostname", lambda: "g3612.nemo.privat")
    monkeypatch.setattr(lib.socket, "getfqdn", lambda name: "g3612.nemo.privat")
    monkeypatch.setattr(lib.os, "cpu_count", lambda: 8)
    with pytest.raises(lib.Stop, match="below the pinned class"):
        lib.host_identity()


def test_driver_regex_reads_only_the_version(monkeypatch, tmp_path):
    p = tmp_path / "version"
    p.write_text("NVRM version: NVIDIA UNIX x86_64 Kernel Module  535.104.05  Sun Aug 20 2023\n")
    real = __import__("pathlib").Path
    monkeypatch.setattr(lib, "Path", lambda x: p if str(x) == "/proc/driver/nvidia/version" else real(x))
    assert lib._driver_version() == "535.104.05"


def test_cpu_identity_checks_the_pinned_class(monkeypatch, tmp_path):
    fake = tmp_path / "cpuinfo"
    fake.write_text("processor\t: 0\nmodel name\t: Test CPU Model 123\nprocessor\t: 1\n")
    real = __import__("pathlib").Path
    monkeypatch.setattr(lib, "Path", lambda x: fake if str(x) == "/proc/cpuinfo" else real(x))
    assert lib.cpu_identity("Test CPU")["logical_cpus"] == 2
    with pytest.raises(lib.Stop, match="does not contain the pinned class"):
        lib.cpu_identity("definitely-not-a-cpu-model")


def test_collector_argv_and_resume():
    s = lib.validate_spec(spec())["spec"]
    argv = lib.collector_argv(s, "ENGINEERING_ONLY", False)
    joined = " ".join(argv)
    assert argv[0] == "/opt/r1/envs/harness/bin/python" and "-m r1.headroom.e1b_collect" in joined
    assert "--manager-model llamacpp/gemma4_31b" in joined and "--proposal-schema manager_proposal/v1" in joined
    assert "--label ENGINEERING_ONLY" in joined and "--runs 20" in joined and "--roots-only" in joined
    assert "--analysis" not in joined and "--read" not in joined
    assert "--resume" in lib.collector_argv(s, "ENGINEERING_ONLY", True)


def test_resume_pin_mismatch_is_a_stop(tmp_path):
    s = lib.validate_spec(spec())["spec"]
    record = tmp_path / "job_record.json"
    record.write_text(json.dumps({"label": "ENGINEERING_ONLY", "image_digest": "ghcr.io/other@sha256:" + "0" * 64,
                                  "model_sha256": s["model"]["sha256"], "paper_commit": s["paper"]["commit"],
                                  "harness_commit": s["harness"]["commit"]}))
    with pytest.raises(lib.Stop, match="resume pin mismatch"):
        lib._check_resume_record(s, record, "ENGINEERING_ONLY")


def test_evidence_requires_the_cpu_model_pin(tmp_path, monkeypatch):
    note = tmp_path / "a.md"
    note.write_text("run: s2eng-20261116-a\napproved: true\nlabel: EVIDENCE\n")
    monkeypatch.chdir(tmp_path)
    s = spec(); s["paper"]["evidence_ready"] = True
    s["requirements"]["cpu_model_contains"] = None
    s["label_source"] = {"authorization": "a.md",
                         "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    with pytest.raises(lib.Stop, match="cpu_model_contains"):
        lib.validate_spec(s)
    s["requirements"]["cpu_model_contains"] = "AMD EPYC"
    assert lib.validate_spec(s)["label"] == "EVIDENCE"


def test_collector_passes_the_walltime_deadline():
    s = lib.validate_spec(spec())["spec"]
    argv = lib.collector_argv(s, "ENGINEERING_ONLY", False)
    assert "--deadline" in argv
    assert int(argv[argv.index("--deadline") + 1]) == s["walltime_s"] - 600


def test_renderer_refuses_absolute_authorization_path(tmp_path):
    note = tmp_path / "a.md"; note.write_text("approved: true\nlabel: EVIDENCE\n")
    s = spec(); s["label_source"] = {"authorization": str(note),
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(s))
    with pytest.raises(lib.Stop, match="bare basename"):
        render_jdl.main([str(sp), "--out", str(tmp_path / "x.jdl"),
                         "--stage-dir", str(tmp_path / "stage"), "--auth-note", str(note)])


def test_seal_verifies_transferred_sums_before_copy(tmp_path, monkeypatch):
    src = tmp_path / "jobout"; (src / "out").mkdir(parents=True)
    (src / "out" / "x.txt").write_text("hello")
    (src / "job_record.json").write_text(json.dumps({"run_id": "r1", "chunk_id": "c1", "label": "ENGINEERING_ONLY",
                                                     "image_digest": "ghcr.io/x@sha256:" + "0" * 64,
                                                     "model_sha256": "1" * 64, "host": {"fqdn": "g3612.nemo.privat"}}))
    (src / "SHA256SUMS").write_text("0" * 64 + "  out/x.txt\n")
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "sealed")
    with pytest.raises(lib.Stop, match="SHA256SUMS verification failed"):
        lib.seal(src, "r1", "c1")


def test_job_entry_precreates_the_transferred_outputs():
    text = (ROOT / "sweep2" / "s2_c2_job.sh").read_text()
    for name in ("out", "work", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert name in text
