"""Synthetic tests for the S2-C2 sweep-2 HTCondor job wrapper/seal/liveness (no job, no network, no GPU)."""
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
    assert v["label"] == "ENGINEERING_ONLY" and v["kind"] == "chunk"


def test_class_constants_are_not_spec_driven():
    for path, bad in ((("requirements", "cloud_site"), "BwForCluster-HoreKa"),
                      (("requirements", "gpu_device_name"), "NVIDIA H200"),
                      (("requirements", "arch"), "AARCH64"), (("requirements", "opsys"), "WINDOWS"),
                      (("requirements", "min_cpus"), 4), (("requirements", "cpu_family"), 25),
                      (("requirements", "cpu_model_number"), 1),
                      (("requirements", "cpu_model_contains"), "AMD EPYC")):
        s = spec(); s[path[0]][path[1]] = bad
        with pytest.raises(lib.Stop):
            lib.validate_spec(s)


def test_b2_harness_pin_is_enforced():
    s = spec(); s["harness"]["commit"] = "897d83c8efa364ec2fdd37288241cc42e01d7274"
    with pytest.raises(lib.Stop, match="B2 harness"):
        lib.validate_spec(s)


def test_noise_source_is_pinned():
    s = spec(); s["noise_source"]["sha256"] = "0" * 64
    with pytest.raises(lib.Stop, match="noise_source"):
        lib.validate_spec(s)
    s = spec(); s["noise_source"]["path"] = "results/r1/noise/other.json"
    with pytest.raises(lib.Stop, match="noise_source"):
        lib.validate_spec(s)
    s = spec(); del s["noise_source"]
    with pytest.raises(lib.Stop, match="noise_source"):
        lib.validate_spec(s)


def test_liveness_block_is_pinned():
    s = spec(); s["liveness"]["min_live_nodes"] = 4
    with pytest.raises(lib.Stop, match="min_live_nodes"):
        lib.validate_spec(s)
    s = spec(); s["liveness"]["nodes"] = s["liveness"]["nodes"][:2]
    with pytest.raises(lib.Stop, match="eight sweep-1 nodes"):
        lib.validate_spec(s)
    s = spec(); s["liveness"]["runs"] = 5
    with pytest.raises(lib.Stop, match="runs=10"):
        lib.validate_spec(s)
    s = spec(); s["liveness"]["max_parse_failure_rate"] = 0.5
    with pytest.raises(lib.Stop, match="max_parse_failure_rate"):
        lib.validate_spec(s)


def test_evidence_requires_authorization_evidence_ready_and_cpu_pin(tmp_path, monkeypatch):
    note = tmp_path / "c3_sweep2_20261116.md"
    note.write_text("run: s2eng-20261116-b\napproved: true\nlabel: EVIDENCE\n")
    monkeypatch.chdir(tmp_path)
    s = spec(); s["label_source"] = {"authorization": "c3_sweep2_20261116.md",
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    with pytest.raises(lib.Stop, match="evidence_ready"):
        lib.validate_spec(s)
    s["paper"]["evidence_ready"] = True
    assert lib.validate_spec(s)["label"] == "EVIDENCE"


def test_authorization_must_be_approved_and_named(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    note = tmp_path / "a.md"
    note.write_text("run: s2eng-20261116-b\napproved: false\nlabel: EVIDENCE\n")
    s = spec(); s["paper"]["evidence_ready"] = True
    s["label_source"] = {"authorization": "a.md",
                         "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    with pytest.raises(lib.Stop, match="not approved"):
        lib.resolve_label(s)
    note.write_text("run: other\napproved: true\nlabel: EVIDENCE\n")
    s["label_source"]["authorization_sha256"] = hashlib.sha256(note.read_bytes()).hexdigest()
    with pytest.raises(lib.Stop, match="does not name this run"):
        lib.resolve_label(s)


def test_index_label_may_never_select_the_table_label():
    for key in ("sweep_index_label", "index_label"):
        s = spec(); s["label_source"] = {key: "ENGINEERING_ONLY"}
        with pytest.raises(lib.Stop, match="index label"):
            lib.resolve_label(s)


def test_requirements_reject_etp_ceph():
    s = spec(); s["requirements"]["requires_etp_ceph"] = True
    with pytest.raises(lib.Stop, match="ProvidesEtpCeph"):
        lib.validate_spec(s)


def test_settings_validators():
    for change in (lambda s: s["collector"].__setitem__("runs", 19),
                   lambda s: s["collector"].__setitem__("workers", 8),
                   lambda s: s["server"].__setitem__("ctx", 16384),
                   lambda s: s["server"].__setitem__("n_gpu_layers", 99),
                   lambda s: s.__setitem__("walltime_s", 60),
                   lambda s: s["collector"].__setitem__("proposal_schema", "manager_proposal/v0")):
        s = spec(); change(s)
        with pytest.raises(lib.Stop):
            lib.validate_spec(s)


def test_layout_fields_are_validated():
    for key, bad in (("request_disk_kb", None), ("request_disk_kb", -5), ("request_disk_kb", "lots"),
                     ("request_memory_mb", 1), ("request_memory_mb", "x")):
        s = spec()
        if bad is None:
            del s[key]
        else:
            s[key] = bad
        with pytest.raises(lib.Stop, match=key):
            lib.validate_spec(s)
    s = spec(); s["server"]["extra_args"][s["server"]["extra_args"].index("--chat-template-kwargs") + 1] = \
        '{"enable_thinking":false, "add_generation_prompt":true}'
    with pytest.raises(lib.Stop, match="byte-identical"):
        lib.validate_spec(s)


def test_settings_are_fail_closed():
    s = spec(); s["server"]["extra_args"] = s["server"]["extra_args"] + ["--threads", "8"]
    with pytest.raises(lib.Stop, match="not part of the exam setting"):
        lib.validate_spec(s)
    s = spec(); k = s["server"]["extra_args"].index("--chat-template-kwargs")
    s["server"]["extra_args"][k + 1] = '{"enable_thinking":true}'
    with pytest.raises(lib.Stop, match="enable_thinking"):
        lib.validate_spec(s)
    s = spec(); k = s["server"]["extra_args"].index("--chat-template-kwargs")
    s["server"]["extra_args"][k + 1] = "not-json"
    with pytest.raises(lib.Stop, match="byte-identical"):
        lib.validate_spec(s)


def test_exam_server_flags_are_required():
    s = spec(); s["server"]["extra_args"] = [a for a in s["server"]["extra_args"] if a != "--jinja"]
    with pytest.raises(lib.Stop, match="--jinja"):
        lib.validate_spec(s)
    s = spec(); s["server"]["extra_args"] = [a for a in s["server"]["extra_args"] if a != "--cache-type-k"]
    with pytest.raises(lib.Stop, match="cache-type-k"):
        lib.validate_spec(s)


def test_server_argv_is_the_exam_setting_and_discloses_non_numeric_diffs():
    s = lib.validate_spec(spec())["spec"]
    argv = lib.build_server_argv(s, Path("model.gguf"))
    joined = " ".join(argv)
    for flag, value in (("-c", "32768"), ("-ngl", "999"), ("-np", "1"), ("-lv", "4")):
        assert flag in argv and argv[argv.index(flag) + 1] == value
    assert "--no-webui" in argv
    assert "--no-webui" in " ".join(lib.NON_NUMERIC_DIFFERENCES)
    assert "-lv 4" in " ".join(lib.NON_NUMERIC_DIFFERENCES)


def test_collector_argv_has_e1_summary_noise_source_and_deadline():
    s = lib.validate_spec(spec())["spec"]
    argv = lib.collector_argv(s, "ENGINEERING_ONLY", False, Path("/tmp/paper"))
    joined = " ".join(argv)
    assert "--e1-summary" in argv and lib.NOISE_PATH in joined
    assert "--deadline" in argv and int(argv[argv.index("--deadline") + 1]) == s["walltime_s"] - 600
    assert "noise_source" in joined and lib.NOISE_SHA in joined
    assert "--audit-seeds 0" in joined and "audit_seeds" not in joined


def test_liveness_argv_uses_all_eight_nodes_and_sweep1_dimensions():
    s = lib.validate_spec(spec())["spec"]
    argv = lib._liveness_argv(s)
    joined = " ".join(argv)
    assert argv[argv.index("--nodes") + 1:argv.index("--nodes") + 9] == list(lib.LIVENESS_NODES)
    assert "--instances 2" in joined and "--runs 10" in joined
    assert "--manager-model llamacpp/gemma4_31b" in joined and "--proposal-schema manager_proposal/v1" in joined
    assert "--deadline" not in argv


def test_liveness_kind_validates():
    s = spec(); s["kind"] = "liveness"
    assert lib.validate_spec(s)["kind"] == "liveness"


def test_collection_gates_mirror_sweep1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"; work = tmp_path / "work"
    (out / "roots").mkdir(parents=True); (work / "roots" / "x").mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "manager": {"kind": "langgraph"},
                                                  "c3_label_sweep": {"memory_mode": "append_only_summary"}}))
    (out / "roots" / "r0.json").write_text("{}")
    (work / "roots" / "x" / "root_events.jsonl").write_text(json.dumps(
        {"event_type": "llm_call", "payload": {"parse_ok": True}}) + "\n")
    (work / "roots" / "x" / "root_trials.jsonl").write_text(json.dumps(
        {"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "success",
         "parsed_metrics": {"val_score": 0.9}}) + "\n")
    with pytest.raises(lib.Stop, match="root failures"):
        lib.collection_gates(out, work, "digits_mlp", 2)
    assert (out / "collection_checks.json").is_file() and (out / "collection_failures.json").is_file()
    (out / "roots" / "r1.json").write_text("{}")
    (work / "roots" / "x" / "root_events.jsonl").write_text("".join(
        json.dumps({"event_type": "llm_call", "payload": {"parse_ok": False}}) + "\n" for _ in range(10)))
    with pytest.raises(lib.Stop, match="parse failure rate"):
        lib.collection_gates(out, work, "digits_mlp", 2)
    assert (out / "parse_failure_examples.json").is_file()
    (work / "roots" / "x" / "root_events.jsonl").write_text(json.dumps(
        {"event_type": "llm_call", "payload": {"parse_ok": True}}) + "\n")
    (work / "roots" / "x" / "root_trials.jsonl").write_text("".join(
        json.dumps({"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "failed",
                    "failure_category": "runtime_error", "parsed_metrics": {}}) + "\n" for _ in range(2)))
    with pytest.raises(lib.Stop, match="zero successful worker runs"):
        lib.collection_gates(out, work, "digits_mlp", 2)
    assert (out / "worker_failure.json").is_file()
    (work / "roots" / "x" / "root_trials.jsonl").write_text("".join(
        json.dumps({"proposal_summary": "raise lr 0.1 -> 0.3",
                    "execution_status": "failed" if i < 9 else "success",
                    "failure_category": "invalid_config", "parsed_metrics": {"val_score": 0.9} if i >= 9 else {}})
        + "\n" for i in range(10)))
    with pytest.raises(lib.Stop, match="worker failure rate"):
        lib.collection_gates(out, work, "digits_mlp", 2)
    (work / "roots" / "x" / "root_trials.jsonl").write_text(
        json.dumps({"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "success",
                    "parsed_metrics": {"val_score": 0.9}}) + "\n" +
        json.dumps({"proposal_summary": "raise lr 0.1 -> 0.4", "execution_status": "failed",
                    "failure_category": "runtime_error", "parsed_metrics": {}}) + "\n")
    with pytest.raises(lib.Stop, match="runtime_error"):
        lib.collection_gates(out, work, "digits_mlp", 2)
    (work / "roots" / "x" / "root_trials.jsonl").write_text(json.dumps(
        {"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "failed",
         "failure_category": "runtime_error", "parsed_metrics": {}}) + "\n")
    with pytest.raises(lib.Stop, match="zero successful"):
        lib.collection_gates(out, work, "digits_mlp", 2)
        lib.collection_gates(out, work, "digits_mlp", 2)
    (work / "roots" / "x" / "root_trials.jsonl").write_text(json.dumps(
        {"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "success",
         "parsed_metrics": {"val_score": 0.9}}) + "\n")
    (work / "roots" / "x" / "root_events.jsonl").write_text(json.dumps(
        {"event_type": "llm_call", "payload": {"parse_ok": True}}) + "\n")
    check = lib.collection_gates(out, work, "digits_mlp", 2)
    assert check["roots"] == 2 and check["llm_calls"] == 1 and check["manager_kind"] == "langgraph"
    assert check["worker"]["successful_with_metrics"] == 1 and check["worker"]["success_rate"] == 1.0


def test_stop_with_evidence_persists_record_and_tars(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir(); (tmp_path / "work").mkdir()
    (tmp_path / "llama-server.log").write_text("log\n")
    rec = tmp_path / "job_record.json"
    with pytest.raises(lib.Stop, match="gate breach"):
        lib._stop_with_evidence({"label": "ENGINEERING_ONLY"}, rec, "gate breach")
    assert json.loads(rec.read_text())["stop"] == "gate breach"
    assert (tmp_path / "out.tar").is_file() and (tmp_path / "work.tar").is_file()
    assert (tmp_path / "SHA256SUMS").is_file()


def test_renderer_pins_class_and_transfers_outputs(tmp_path):
    stage = tmp_path / "stage"; out = tmp_path / "job.jdl"
    render_jdl.main([str(ROOT / "sweep2" / "spec.example.json"), "--out", str(out), "--stage-dir", str(stage)])
    jdl = out.read_text()
    assert "universe = container" in jdl
    assert "container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35" in jdl
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA L40S"' in jdl
    assert "TARGET.CloudSite" not in jdl  # R1-SWEEP-HOST-L40S-SITES: GPU model, not site
    assert f"Cpus >= {lib.MIN_CPUS}" in jdl and 'Arch == "X86_64"' in jdl and 'OpSys == "LINUX"' in jdl
    assert "TARGET.CpuFamily" not in jdl and "TARGET.CpuModelNumber" not in jdl
    assert "periodic_hold = (NumJobStarts > 1)" in jdl
    assert "regexp(" not in jdl
    assert "transfer_output_files = out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log" in jdl
    assert "request_disk = 42460977" in jdl and "request_memory = 32000" in jdl
    assert "ProvidesEtpCeph" not in jdl and "docker_image" not in jdl


def test_renderer_refuses_absolute_authorization_path(tmp_path):
    note = tmp_path / "a.md"; note.write_text("approved: true\nlabel: EVIDENCE\n")
    s = spec(); s["label_source"] = {"authorization": str(note),
                                     "authorization_sha256": hashlib.sha256(note.read_bytes()).hexdigest()}
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(s))
    with pytest.raises(lib.Stop, match="bare basename"):
        render_jdl.main([str(sp), "--out", str(tmp_path / "x.jdl"),
                         "--stage-dir", str(tmp_path / "stage"), "--auth-note", str(note)])


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
    fake_root = tmp_path / "sealed"; fake_root.mkdir()
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


def test_host_identity_rejects_below_class_cpus(monkeypatch):
    monkeypatch.setattr(lib.socket, "gethostname", lambda: "g3612.nemo.privat")
    monkeypatch.setattr(lib.socket, "getfqdn", lambda name: "g3612.nemo.privat")
    monkeypatch.setattr(lib.os, "cpu_count", lambda: 16)
    assert lib.host_identity()["logical_cpus"] == 16
    monkeypatch.setattr(lib.os, "cpu_count", lambda: 8)
    with pytest.raises(lib.Stop, match="below the pinned class"):
        lib.host_identity()


def test_cpu_identity_checks_the_s2_c4_cpu_class(monkeypatch, tmp_path):
    fake = tmp_path / "cpuinfo"
    fake.write_text("processor\t: 0\ncpu family\t: 6\nmodel\t\t: 207\n"
                    "model name\t: INTEL(R) XEON(R) PLATINUM 8562Y+ CPU @ 2.80GHz\n"
                    "processor\t: 1\n")
    real = __import__("pathlib").Path
    monkeypatch.setattr(lib, "Path", lambda x: fake if str(x) == "/proc/cpuinfo" else real(x))
    info = lib.cpu_identity()
    assert info["cpu_family"] == 6 and info["cpu_model_number"] == 207 and info["logical_cpus"] == 2
    fake.write_text("processor\t: 0\ncpu family\t: 25\nmodel\t\t: 1\nmodel name\t: AMD EPYC 9004\n")
    other = lib.cpu_identity()
    assert other["cpu_family"] == 25 and other["model"].startswith("AMD EPYC")


def test_driver_regex_reads_the_version(monkeypatch, tmp_path):
    p = tmp_path / "version"
    p.write_text("NVRM version: NVIDIA UNIX Open Kernel Module for x86_64  615.71.10  Release Build\n")
    real = __import__("pathlib").Path
    monkeypatch.setattr(lib, "Path", lambda x: p if str(x) == "/proc/driver/nvidia/version" else real(x))
    assert lib._driver_version() == "615.71.10"


def test_job_entry_precreates_the_transferred_outputs():
    text = (ROOT / "sweep2" / "s2_c2_job.sh").read_text()
    for name in ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert name in text
    assert "--scratch" not in text


def test_worker_env_prepends_the_harness_venv(tmp_path, monkeypatch):
    class FakePath(type(__import__("pathlib").Path())):
        pass
    real = __import__("pathlib").Path
    def fake(x):
        p = real(x)
        if str(p) == "/opt/r1/envs/harness/bin":
            return tmp_path / "venvbin"
        return p
    (tmp_path / "venvbin").mkdir()
    (tmp_path / "venvbin" / "python3").write_text("#!/bin/sh\n")
    monkeypatch.setattr(lib, "Path", fake)
    env = lib._worker_env(tmp_path / "paper", tmp_path / "harness")
    assert env["PATH"].startswith(str(tmp_path / "venvbin")) and "LLAMACACHE_PROMPT" not in env


def test_worker_skipped_nested_schema_is_excluded_from_the_gate(tmp_path, monkeypatch):
    # sweep-1 records worker_skipped inside extra.worker (not top-level); a healthy digits/append chunk has 38 skips
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"; work = tmp_path / "work"
    (out / "roots").mkdir(parents=True); (work / "roots" / "x").mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"label": "ENGINEERING_ONLY", "manager": {"kind": "langgraph"},
                                                  "c3_label_sweep": {"memory_mode": "append_only_summary"}}))
    for i in range(2):
        (out / "roots" / f"r{i}.json").write_text("{}")
    (work / "roots" / "x" / "root_events.jsonl").write_text(json.dumps(
        {"event_type": "llm_call", "payload": {"parse_ok": True}}) + "\n")
    trials = [json.dumps({"proposal_summary": "raise lr 0.1 -> 0.3", "execution_status": "success",
                          "parsed_metrics": {"val_score": 0.9}}) for _ in range(8)]
    trials += [json.dumps({"proposal_summary": "skip", "execution_status": "failed",
                           "failure_category": "proposal_precondition_failed",
                           "extra": {"worker": {"worker_skipped": True}}}) for _ in range(2)]
    (work / "roots" / "x" / "root_trials.jsonl").write_text("\n".join(trials) + "\n")
    check = lib.collection_gates(out, work, "digits_mlp", 2)
    assert check["worker"]["skipped"] == 2 and check["worker"]["trials"] == 8
    assert check["worker"]["failure_rate"] == 0.0


def test_no_resume_path_refuses_a_prior_chunk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "manifest.json").write_text("{}")
    (tmp_path / "job_record.json").write_text('{"schema": "s2_c2_job_record/1"}')
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec()))
    with pytest.raises(lib.Stop, match="no resume path"):
        lib.run_job(sp)
    assert not (tmp_path / "out.tar").exists()


def test_walltime_must_be_one_and_a_half_the_measured_chunk():
    s = spec(); s["layout_measured_chunk_s"] = 8000; s["walltime_s"] = 12000
    assert lib.validate_spec(s)["label"] == "ENGINEERING_ONLY"
    s["walltime_s"] = 12203
    with pytest.raises(lib.Stop, match="1.5x"):
        lib.validate_spec(s)
    s = spec(); s["layout_measured_chunk_s"] = -1
    with pytest.raises(lib.Stop, match="positive"):
        lib.validate_spec(s)
