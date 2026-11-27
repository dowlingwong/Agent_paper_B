"""Tests for the D.3 G1 launchers (design revision 6b) — synthetic, CPU only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from r1.c3.d3 import launch as L
from r1.c3.d3 import launch_htcondor as H
from r1.c3.d3 import launch_ssh as S
from r1.c3.d3 import probe as P
from r1.c3.d3.campaign_chunk import ChunkSpec, check_hardware, sha256_json

SOURCE = {"path": "docs/r1/authorizations/example.md",
          "sha256": "a" * 64, "model": "NVIDIA RTX 4090"}


def _record(**kw):
    base = {
        "schema": L.LAUNCH_SCHEMA, "stage": "a", "arm": "A2", "node": "digits_mlp",
        "repetition": 0, "instance_seeds": list(range(6201, 6219)), "W": 20, "llm_cap": 80,
        "launcher": "ssh", "host": "TASL-2", "campaign_model_source": dict(SOURCE),
        "hardware": {"required_memory_mib": 20000},
        "manifest": {"path": "manifest.json", "sha256": "b" * 64},
        "observed": {"path": "observed.json", "sha256": "c" * 64},
    }
    base.update(kw)
    return base


def _write(path: Path, payload) -> str:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n" if not isinstance(payload, str) else payload,
                    encoding="utf-8")
    return L.sha256_file(path)


def _staged(tmp_path: Path):
    repo = tmp_path / "repo.tar"
    repo.write_bytes(b"synthetic repo tarball")
    manifest = tmp_path / "manifest.json"
    observed = tmp_path / "observed.json"
    _write(manifest, {"schema": "r1_d3_campaign_manifest/v1"})
    _write(observed, {"schema": L.OBSERVED_SCHEMA, "memory_check": "pass", "lease": True,
                      "lease_path": "/tmp/gpu0.lock"})
    launch_path = tmp_path / "launch.json"
    record = _record(launcher="htcondor", staging={"repo_tarball": {
        "path": str(repo), "sha256": L.sha256_file(repo)}})
    record["manifest"]["sha256"] = L.sha256_file(manifest)
    record["observed"]["sha256"] = L.sha256_file(observed)
    L.write_launch(launch_path, record)
    return launch_path, manifest, observed, repo


def test_launch_record_requires_signed_values():
    good = _record()
    L.validate_launch(good)
    with pytest.raises(L.LaunchStop):
        L.validate_launch({k: v for k, v in good.items() if k != "manifest"})
    with pytest.raises(L.LaunchStop):
        L.validate_launch({**good, "W": 19})
    with pytest.raises(L.LaunchStop):
        L.validate_launch({**good, "instance_seeds": [6201, 6202]})
    with pytest.raises(L.LaunchStop):
        L.validate_launch({**good, "launcher": "magic"})


def test_both_launchers_pass_the_same_chunk_argv(tmp_path):
    launch_path, manifest, observed, repo = _staged(tmp_path)
    record = L.read_json(launch_path)
    submit = H.render_submit(record, submit_dir=tmp_path / "submit")
    argv = L.chunk_argv("launch.json", "out", manifest_path="manifest.json",
                        observed_path="observed.json", python="python3")
    args_line = [line for line in submit.splitlines() if line.startswith("arguments = ")][0]
    assert args_line[len("arguments = "):] == L.shell_join(argv[1:])
    ssh_record = {**record, "launcher": "ssh", "lease_path": "/tmp/gpu0.lock"}
    script = S.render_remote_script(
        ssh_record, launch_text="{}", manifest_text="{}", observed_text="{}",
        out_dir="out", lease_path="/tmp/gpu0.lock")
    assert L.shell_join(argv) in script
    assert "flock -n 9" in script


def test_htcondor_request_is_never_edited(tmp_path):
    launch_path, _, _, _ = _staged(tmp_path)
    record = L.read_json(launch_path)
    with pytest.raises(L.LaunchStop):
        H.render_submit(record, submit_dir=tmp_path, request={**L.D3_REQUEST, "request_memory_mb": 60000})
    with pytest.raises(L.LaunchStop):
        H.render_submit(record, submit_dir=tmp_path,
                        request={k: v for k, v in L.D3_REQUEST.items() if k != "request_cpus"})
    text = H.render_submit(record, submit_dir=tmp_path)
    assert "request_memory = 131072" in text and "request_cpus = 8" in text
    assert "request_GPUs = 1" in text and "+RequestWalltime = 3600" in text


def test_htcondor_requires_a_pinned_repo_tarball(tmp_path):
    launch_path, _, _, repo = _staged(tmp_path)
    record = L.read_json(launch_path)
    record["staging"]["repo_tarball"]["sha256"] = "0" * 64
    with pytest.raises(L.LaunchStop):
        H.render_submit(record, submit_dir=tmp_path)


def test_other_processes_record_count_and_memory_only():
    text = "GPU-abc, 1234, 512\nGPU-def, 5678, 1024\n"
    got = L.parse_other_processes(text)
    assert got == {"count": 2, "used_memory_mib": 1536, "unknown_memory_count": 0}
    assert "1234" not in json.dumps(got) and "GPU-" not in json.dumps(got)


def test_other_processes_accepts_real_nvidia_smi_units():
    text = "GPU-abc, 1234, 512 MiB\nGPU-abc, 5678, N/A\nGPU-def, 9012, 1024 MiB\n"
    got = L.parse_other_processes(text, gpu_uuid="GPU-abc")
    assert got == {"count": 2, "used_memory_mib": 512, "unknown_memory_count": 1}


def test_probe_reads_the_card_and_records_count_memory_only():
    class Proc:
        def __init__(self, stdout):
            self.returncode, self.stdout, self.stderr = 0, stdout, ""

    def runner(argv, **kw):
        if "name,uuid,driver_version,memory.total,memory.free" in " ".join(argv):
            return Proc("NVIDIA RTX 4090, GPU-abc, 535.113, 24564, 24000\n")
        return Proc("GPU-abc, 1234, 512 MiB\nGPU-def, 5678, 1024 MiB\n")

    record = P.probe(gpu_index=0, required_memory_mib=20000, proposer_model="gemma4_31b",
                     host="TASL-2", lease=True, lease_path="/tmp/gpu0.lock", runner=runner)
    assert record["model"] == "NVIDIA RTX 4090" and record["gpu_uuid"] == "GPU-abc"
    assert record["memory_check"] == "pass"
    assert record["other_processes_start"] == {"count": 1, "used_memory_mib": 512,
                                               "unknown_memory_count": 0}
    assert "1234" not in json.dumps(record["other_processes_start"])


def test_check_hardware_refuses_a_host_mismatch():
    spec = ChunkSpec.from_launch(_record())
    manifest = {"campaign_model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b"}
    good = {"host": "TASL-2", "model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b",
            "memory_check": "pass", "lease": True}
    check_hardware(spec, good, manifest)
    with pytest.raises(Exception):
        check_hardware(spec, {**good, "host": "TASL-7"}, manifest)
    # HTCondor chooses the worker: the actual host is recorded, not compared.
    condor = ChunkSpec.from_launch(_record(launcher="htcondor"))
    check_hardware(condor, {**good, "host": "worker-17.etp.kit.edu"}, manifest)


def test_memory_fit_and_lease_helpers(tmp_path):
    assert L.memory_fit(46000, 48000) == "pass"
    assert L.memory_fit(46000, 40000) == "fail"
    with pytest.raises(L.LaunchStop):
        L.memory_fit(0, 1)
    # A released lease can be taken; a missing directory is a refusal.
    lease = tmp_path / "gpu0.lock"
    lease.write_text("")
    assert L.lease_held(lease) is True
    with pytest.raises(L.LaunchStop):
        L.lease_held(tmp_path / "missing" / "gpu0.lock")


def test_ssh_refuses_a_bad_observed_record(tmp_path):
    observed = {"memory_check": "fail", "lease": True, "lease_path": "/tmp/gpu0.lock"}
    with pytest.raises(L.LaunchStop):
        S.check_observed(observed, lease_path="/tmp/gpu0.lock")
    with pytest.raises(L.LaunchStop):
        S.check_observed({**observed, "memory_check": "pass", "lease": False},
                         lease_path="/tmp/gpu0.lock")
    with pytest.raises(L.LaunchStop):
        S.check_observed({**observed, "memory_check": "pass", "lease_path": "/tmp/other.lock"},
                         lease_path="/tmp/gpu0.lock")


def test_ssh_dry_run_writes_the_same_launch_fields(tmp_path):
    launch_path, manifest, observed, _ = _staged(tmp_path)
    record = L.read_json(launch_path)
    record["launcher"] = "ssh"
    record["lease_path"] = "/tmp/gpu0.lock"
    L.write_launch(launch_path, record)
    out = tmp_path / "chunk"
    got = S.launch(launch_path, out, manifest_path=manifest, observed_path=observed,
                   lease_path="/tmp/gpu0.lock", dry_run=True)
    assert got["launcher"] == "ssh" and got["request"] is None
    assert "launch.json" in got["script"] and "manifest.json" in got["script"]
    assert "flock -n 9" in got["script"]
    saved = json.loads((tmp_path / "launch.json").read_text())
    assert saved["launcher"] == "ssh" and saved["lease_path"] == "/tmp/gpu0.lock"
    assert saved["request"] is None


def test_ssh_refuses_a_missing_lease(tmp_path):
    launch_path, manifest, observed, _ = _staged(tmp_path)
    record = L.read_json(launch_path)
    record["launcher"] = "ssh"
    L.write_launch(launch_path, record)
    with pytest.raises(L.LaunchStop):
        S.launch(launch_path, tmp_path / "chunk", manifest_path=manifest,
                 observed_path=observed, lease_path=None, dry_run=True)


def test_condor_submit_parses_a_cluster_id():
    assert H.parse_cluster_id("1 job(s) submitted to cluster 760148.\n") == "760148"
    with pytest.raises(L.LaunchStop):
        H.parse_cluster_id("nothing here")


def test_htcondor_job_probes_the_assigned_card(tmp_path):
    launch_path, manifest, observed, repo = _staged(tmp_path)
    record = L.read_json(launch_path)
    record["observed"] = {"path": "observed.json", "probe": True}
    L.write_launch(launch_path, record)
    got = H.submit(launch_path, tmp_path / "chunk", submit_dir=tmp_path / "submit",
                   manifest_path=manifest, dry_run=True)
    submit = (tmp_path / "submit" / H.SUBMIT_NAME).read_text()
    assert "observed.json" not in [p.strip() for p in
                                   submit.split("transfer_input_files = ")[1].splitlines()[0].split(",")]
    wrapper = (tmp_path / "submit" / H.WRAPPER_NAME).read_text()
    assert "r1.c3.d3.probe" in wrapper and "--out observed.json" in wrapper
    assert not (tmp_path / "submit" / "observed.json").exists()
    assert got["launcher"] == "htcondor" and got["dry_run"] is True


def test_gpu_index_is_read_from_the_lease():
    assert P.gpu_index_from_lease("/home/x/r1_locks/gpu0.lock") == 0
    assert P.gpu_index_from_lease("/home/x/r1_locks/gpu3.lock") == 3
    assert P.gpu_index_from_lease(None) == 0
    assert P.gpu_index_from_lease("/home/x/r1_locks/other.lock") == 0


def test_probe_from_records_uses_the_actual_host_and_lease_card(monkeypatch):
    class Proc:
        def __init__(self, stdout):
            self.returncode, self.stdout, self.stderr = 0, stdout, ""

    seen = []

    def runner(argv, **kw):
        seen.append(argv)
        if "name,uuid,driver_version,memory.total,memory.free" in " ".join(argv):
            return Proc("NVIDIA RTX 4090, GPU-card3, 535.113, 24564, 24000\n")
        return Proc("GPU-card3, 1234, 512 MiB\n")

    monkeypatch.setattr(P.socket, "gethostname", lambda: "TASL-2.actual")
    launch = _record(launcher="ssh")
    launch["hardware"] = {"required_memory_mib": 20000}
    record = P.probe_from_records(launch, {"proposer_model": "gemma4_31b"},
                                  lease_path="/home/x/r1_locks/gpu3.lock", runner=runner)
    assert record["host"] == "TASL-2.actual"
    assert record["gpu_uuid"] == "GPU-card3"
    assert ["-i", "3"] == seen[0][1:3]


def test_probe_requires_a_declared_memory_requirement():
    launch = _record(launcher="ssh")
    launch.pop("hardware")
    with pytest.raises(L.LaunchStop):
        P.probe_from_records(launch, {"proposer_model": "gemma4_31b"}, runner=lambda *a, **k: None)
